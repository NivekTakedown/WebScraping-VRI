from bs4 import BeautifulSoup
from markdownify import markdownify as md
import requests
import json
import re

def filtrar_enlaces():
    website = 'https://viceinvestigacion.unal.edu.co/investigación'
    try:
        result = requests.get(website)
        result.raise_for_status()
        content = result.text
        soup = BeautifulSoup(content, 'lxml')
        enlaces = soup.find_all('a', class_='aJHbb hDrhEe HlqNPb')
        enlaces_filtrados = [enlace['href'] for enlace in enlaces if '/investigación/apoyo-a-la-investigación/boletín-siun' in enlace['href'] and len(enlace['href']) > 56]
        return enlaces_filtrados[:10]
    except requests.RequestException as e:
        print(f"Error al obtener la página web: {e}")
        return []

def extraer_enlaces(soup,clase):
    elementos = soup.find_all("div", class_=clase)
    enlaces_imagenes = []
    enlaces_otros = []
    for elemento in elementos:
        imagenes = elemento.find_all('img')
        enlaces_imagenes.extend([img['src'] for img in imagenes])
        enlaces = elemento.find_all('a')
        enlaces_otros.extend([a['href'] for a in enlaces if 'http' in a['href']])
    return enlaces_imagenes, enlaces_otros
def bajar_texto_noticias(enlace):
    base_website = 'https://viceinvestigacion.unal.edu.co'
    website = f"{base_website}{enlace}"
    noticias_info = {}
    try:
        result = requests.get(website)
        result.raise_for_status()
        content = result.text
        soup = BeautifulSoup(content, 'lxml')

        def agregar_info(clase):
            elementos = soup.find_all("div", class_=clase)
            if elementos:
                texto = ' '.join(str(elemento) for elemento in elementos)
                return texto
            return None

        def agregar_info_text(clase):
            elementos = soup.find_all("div", class_=clase)
            if elementos:
                texto = ' '.join(elemento.get_text(separator=' ', strip=True) for elemento in elementos)
                return texto
            return None

        def extraer_fecha(texto, patron_fecha):
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
        noticias_info['enlaces_imagenes'], noticias_info['enlaces_otros'] = extraer_enlaces(soup.find("section",class_="yaqOZd LB7kq gk8rDe"),"tyJCtd baZpAe")
        return noticias_info
    except requests.RequestException as e:
        print(f"Error al obtener la página web: {e}")
    except Exception as e:
        print(f"Un error ocurrió: {e}")
    return {}

def guardar_noticias_json():
    enlaces = filtrar_enlaces()
    noticias_lista = [bajar_texto_noticias(enlace) for enlace in enlaces]
    with open('noticias.json', 'w', encoding='utf-8') as f:
        json.dump(noticias_lista, f, ensure_ascii=False, indent=4)

# Ejecutar la función para guardar las noticias en un archivo JSON
guardar_noticias_json()