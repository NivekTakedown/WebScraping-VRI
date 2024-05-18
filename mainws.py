import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

import numpy as np
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import spacy

# Cargar el modelo de lenguaje en español de spacy
nlp = spacy.load('es_core_news_md')

import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from wordcloud import WordCloud
from collections import Counter

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
    # return json
        return noticias_lista

# cargar el archivo
def cargar_noticias_json():
    with open('noticias.json', 'r', encoding='utf-8') as f:
        noticias = json.load(f)
    return noticias
import matplotlib.pyplot as plt


import unidecode
from nltk.stem import WordNetLemmatizer

def extraer_palabras_importantes(textos: list) -> tuple:
    # Cargar stopwords
    stop_words = set(stopwords.words('spanish'))
    stop_words.update(stopwords.words('english'))

    # Cargar stopwords adicionales desde una URL
    response = requests.get('https://gist.githubusercontent.com/cr0wg4n/78554c5d0afa9944d2fa3a4435d83a57/raw/df59fb916108f2a58bf1a3d8c62818b44231586d/spanish-stop-words.txt')
    stop_words_ = response.text.split('\n')
    stop_words.update(['más','invitar', 'uno','enlace','vicerrectorio','invitar', 'también', 'sólo', 'aquí', 'ahora', 'https','http', 'com', 'co', 'www', 'viceinvestigacion', 'unal', 'edu', 'col', 'html', 'p', 'div', 'class', 'img', 'src'])
    stop_words.update(['boletin', 'siun', 'atencion', 'legal', 'control', 'interno', 'vicerrectoria', 'enlaces', 'ma', 'hora', 'consultar', 'interes', 'linea', 'preguntas', 'invitamos', 'usuario', 'estadisticas', 'regimen', 'quejas', 'reclamos', 'notificaciones', 'judiciales', 'glosario', 'contratacion', 'rendicion', 'cuentas', 'nota', 'acerca', 'distinta', 'cierre', 'mailto', 'fecha', 'area', 'web', 'pagina', 'registro', 'time', 'modalidad', 'formulario', 'trave', 'application', 'persona', 'mar', 'ma'])
    # Stop words fechas
    stop_words.update(['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'])
    # En inglés
    stop_words.update(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'])
    # Asociado a redes sociales y páginas
    stop_words.update(['twitter', 'instagram', 'youtube', 'facebook', 'whatsapp', 'linkedin', 'telegram', 'tiktok', 'snapchat', 'pinterest', 'reddit', 'tumblr', 'flickr', 'quora', 'twitch', 'spotify', 'soundcloud','redes','sociales'])
    # Lugares
    stop_words.update(['bogota', 'medellin', 'cali', 'barranquilla', 'cartagena', 'cucuta', 'bucaramanga', 'pereira', 'manizales', 'ibague', 'villavicencio', 'neiva', 'pasto', 'tunja', 'popayan', 'quibdo', 'monteria', 'santa marta', 'villavicencio', 'valledupar', 'arauca', 'yopal', 'leticia', 'puerto inirida', 'san jose del guaviare', 'mitu', 'puerto carreño', 'quibdo', 'san andres', 'providencia', 'bogotá', 'medellín', 'cali', 'barranquilla', 'cartagena', 'cúcuta','colombia','universidad','nacional'])
    stop_words.update(stop_words_)

    palabras_importantes = []
    for texto in textos:
        texto = unidecode.unidecode(texto.lower())
        doc = nlp(texto)
        palabras = [token.lemma_ for token in doc if token.is_alpha and token.lemma_ not in stop_words and len(token.lemma_) > 3]
        palabras_importantes.extend(palabras)

    wordcloud = WordCloud(width=800, height=800, background_color='white', stopwords=stop_words, min_font_size=10).generate(' '.join(palabras_importantes))

    palabras_frecuentes = Counter(palabras_importantes).most_common(100)

    return wordcloud, palabras_frecuentes

if __name__ == '__main__':
    noticias = cargar_noticias_json()  # Asegúrate de tener esta función definida
    all_texts = [noticia['texto_contenido'] for noticia in noticias]
    wordcloud, palabras_frecuentes = extraer_palabras_importantes(all_texts)
    # Mostrar la nube de palabras
    plt.figure(figsize=(8, 8), facecolor=None)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.show()

    # Imprimir las 100 palabras más frecuentes
    print(palabras_frecuentes)