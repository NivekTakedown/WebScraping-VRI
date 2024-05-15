import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

import numpy as np
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

BASE_WEBSITE = 'https://viceinvestigacion.unal.edu.co'
ENLACES_EXCLUIR = [
    "https://ssl.gstatic.com/atari/images/sociallinks/twitter_white_44dp.png",
    "https://ssl.gstatic.com/atari/images/sociallinks/instagram_white_44dp.png",
    "https://ssl.gstatic.com/atari/images/sociallinks/youtube_white_44dp.png",
    "https://ssl.gstatic.com/atari/images/sociallinks/facebook_white_44dp.png"
]

class NoticiasExtractor:
    def __init__(self, session):
        self.session = session

    def filtrar_enlaces(self) -> List[str]:
        website = f'{BASE_WEBSITE}/investigación'
        try:
            response = self.session.get(website)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            enlaces = soup.find_all('a', class_='aJHbb hDrhEe HlqNPb')
            enlaces_filtrados = [
                enlace['href'] for enlace in enlaces
                if '/investigación/apoyo-a-la-investigación/boletín-siun' in enlace['href']
                and len(enlace['href']) > 56
            ]
            return enlaces_filtrados
        except requests.RequestException as e:
            print(f"Error al obtener la página web: {e}")
            return []

    def extraer_enlaces(self, soup: BeautifulSoup, clase: str) -> Tuple[List[str], List[str]]:
        elementos = soup.find_all("div", class_=clase)
        enlaces_imagenes = []
        enlaces_otros = []
        for elemento in elementos:
            imagenes = elemento.find_all('img')
            enlaces_imagenes.extend([img['src'] for img in imagenes])
            enlaces = elemento.find_all('a')
            enlaces_otros.extend([a['href'] for a in enlaces if 'http' in a['href']])
        return enlaces_imagenes, enlaces_otros

    def bajar_texto_noticias(self, enlaces: List[str]) -> List[dict]:
        noticias_lista = []
        for enlace in enlaces:
            print(f"Enlace: {enlace}")
            website = f"{BASE_WEBSITE}{enlace}"
            noticias_info = {}
            try:
                response = self.session.get(website)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'lxml')

                def agregar_info(clase: str) -> str:
                    elementos = soup.find_all("div", class_=clase)
                    if elementos:
                        texto = ' '.join(str(elemento) for elemento in elementos)
                        return texto
                    return None

                def agregar_info_text(clase: str) -> str:
                    elementos = soup.find_all("div", class_=clase)
                    if elementos:
                        texto = ' '.join(elemento.get_text(separator=' ', strip=True) for elemento in elementos)
                        return texto
                    return None

                def extraer_fecha(texto: str, patron_fecha: str) -> str:
                    fechas = re.findall(patron_fecha, texto)
                    return fechas[0] if fechas else None

                texto_completo = agregar_info("tyJCtd mGzaTb Depvyb baZpAe")
                noticias_info['texto_contenido'] = md(texto_completo)
                noticias_info['titulo'] = agregar_info_text("tyJCtd mGzaTb Depvyb baZpAe lkHyyc")
                noticias_info['fecha'] = extraer_fecha(texto_completo, r"\d{4}/\d{2}/\d{2}")
                fecha_actualizacion = extraer_fecha(texto_completo, r"Nota actualizada el (\d{1,2} \w{3}\. \d{4})")
                noticias_info['fecha_actualizacion'] = f"Nota actualizada el {fecha_actualizacion}" if fecha_actualizacion else None
                fecha_evento = extraer_fecha(texto_completo, r"\[Boletín SIUN \d+, (\d{1,2}/\d{1,2} de \w+ de \d{4})\]")
                noticias_info['fecha_del_evento'] = f"[Boletín SIUN {fecha_evento}" if fecha_evento else None

                # Filtrar los enlaces
                enlaces_imagenes, enlaces_otros = self.extraer_enlaces(soup, "tyJCtd baZpAe")
                noticias_info['enlaces_imagenes'] = list(set(enlace for enlace in enlaces_imagenes if enlace not in ENLACES_EXCLUIR))

                noticias_lista.append(noticias_info)

                # Agregar un retraso antes de la siguiente solicitud
                time.sleep(0.1)  # Ajusta el valor según sea necesario

            except requests.RequestException as e:
                print(f"Error al obtener la página web: {e}")
            except Exception as e:
                print(f"Un error ocurrió: {e}")

        return noticias_lista

def guardar_noticias_json():
    with requests.Session() as session:
        extractor = NoticiasExtractor(session)
        enlaces = extractor.filtrar_enlaces()

        num_hilos = 5  # Número de hilos a utilizar

        # Dividir la lista de enlaces en partes iguales según el número de hilos
        enlaces_divididos = np.array_split(enlaces, num_hilos)

        with ThreadPoolExecutor(max_workers=num_hilos) as executor:
            futures = [executor.submit(extractor.bajar_texto_noticias, enlaces_parte) for enlaces_parte in enlaces_divididos]
            resultados = []
            for future in futures:
                resultados.append(future.result())

        noticias_lista = []
        for resultado in resultados:
            noticias_lista.extend(resultado)

        with open('noticias.json', 'w', encoding='utf-8') as f:
            json.dump(noticias_lista, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    guardar_noticias_json()