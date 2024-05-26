import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

import matplotlib.pyplot as plt
import nltk
import numpy as np
import requests
import spacy
import unidecode
from bs4 import BeautifulSoup
from collections import Counter
from markdownify import markdownify as md
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from wordcloud import WordCloud

# Descargar recursos de NLTK
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Cargar el modelo de lenguaje en español de spaCy
nlp = spacy.load('es_core_news_md')

BASE_WEBSITE = 'https://viceinvestigacion.unal.edu.co'
ENLACES_EXCLUIR = [
    "https://ssl.gstatic.com/atari/images/sociallinks/twitter_white_44dp.png",
    "https://ssl.gstatic.com/atari/images/sociallinks/instagram_white_44dp.png",
    "https://ssl.gstatic.com/atari/images/sociallinks/youtube_white_44dp.png",
    "https://ssl.gstatic.com/atari/images/sociallinks/facebook_white_44dp.png"
]

BASE_WEBSITE = 'https://viceinvestigacion.unal.edu.co'
ENLACES_EXCLUIR = [
    "https://ssl.gstatic.com/atari/images/sociallinks/twitter_white_44dp.png",
    "https://ssl.gstatic.com/atari/images/sociallinks/instagram_white_44dp.png",
    "https://ssl.gstatic.com/atari/images/sociallinks/youtube_white_44dp.png",
    "https://ssl.gstatic.com/atari/images/sociallinks/facebook_white_44dp.png"
]
STOPWORDS_ESPANOL = set(stopwords.words('spanish'))
STOPWORDS_INGLES = set(stopwords.words('english'))
STOPWORDS_ADICIONALES_URL = 'https://gist.githubusercontent.com/cr0wg4n/78554c5d0afa9944d2fa3a4435d83a57/raw/df59fb916108f2a58bf1a3d8c62818b44231586d/spanish-stop-words.txt'
STOPWORDS_ADICIONALES = ['más', 'invitar', 'uno', 'enlace', 'vicerrectorio', 'invitar', 'también', 'sólo', 'aquí', 'ahora', 'https', 'http', 'com', 'co', 'www', 'viceinvestigacion', 'unal', 'edu', 'col', 'html', 'p', 'div', 'class', 'img', 'src']
STOPWORDS_BOLETIN = ['boletin', 'siun', 'atencion', 'legal', 'control', 'interno', 'vicerrectoria', 'enlaces', 'ma', 'hora', 'consultar', 'interes', 'linea', 'preguntas', 'invitamos', 'usuario', 'estadisticas', 'regimen', 'quejas', 'reclamos', 'notificaciones', 'judiciales', 'glosario', 'contratacion', 'rendicion', 'cuentas', 'nota', 'acerca', 'distinta', 'cierre', 'mailto', 'fecha', 'area', 'web', 'pagina', 'registro', 'time', 'modalidad', 'formulario', 'trave', 'application', 'persona', 'mar', 'ma']
STOPWORDS_FECHAS_ESPANOL = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
STOPWORDS_FECHAS_INGLES = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
STOPWORDS_REDES_SOCIALES = ['twitter', 'instagram', 'youtube', 'facebook', 'whatsapp', 'linkedin', 'telegram', 'tiktok', 'snapchat', 'pinterest', 'reddit', 'tumblr', 'flickr', 'quora', 'twitch', 'spotify', 'soundcloud', 'redes', 'sociales']
STOPWORDS_LUGARES = ['bogota', 'medellin', 'cali', 'barranquilla', 'cartagena', 'cucuta', 'bucaramanga', 'pereira', 'manizales', 'ibague', 'villavicencio', 'neiva', 'pasto', 'tunja', 'popayan', 'quibdo', 'monteria', 'santa marta', 'villavicencio', 'valledupar', 'arauca', 'yopal', 'leticia', 'puerto inirida', 'san jose del guaviare', 'mitu', 'puerto carreño', 'quibdo', 'san andres', 'providencia', 'bogotá', 'medellín', 'cali', 'barranquilla', 'cartagena', 'cúcuta', 'colombia', 'universidad', 'nacional']


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
        #enlaces = enlaces[:5]  # Limitar la cantidad de enlaces para pruebas
        enlaces = enlaces[:1]  # Limitar la cantidad de enlaces para pruebas
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

                def extraer_fecha(texto: str, patron_fecha: str) -> str:
                    fechas = re.findall(patron_fecha, texto)
                    return fechas[0] if fechas else None
                # crea un metodo para ver si un substring esta en el texto y si esta lo retorna true
                def buscar_substring(texto: str, subcadena: str) -> bool:
                    return texto.startswith(subcadena)
     
                texto_completo = agregar_info("tyJCtd mGzaTb Depvyb baZpAe")
                if texto_completo:
                    fecha_evento = extraer_fecha(texto_completo, r"\[Boletín SIUN \d+, (\d{1,2}/\d{1,2} de \w+ de \d{4})\]")
                    texto_completo_md = md(texto_completo).split('\n\n',1)
                    titulo = texto_completo_md[0]
                    texto_completo_md = texto_completo_md[1].split('\n\n Te invitamos a consultar nuestras redes sociales')[0].split("Investigación, UNAL\n\n")[1]
                    fecha_actualizacion = None
                    # si empieza con: Nota actualizada... se sivide enn dos y se toma el segundo elemento
                    if buscar_substring(texto_completo_md, " Nota actualizada el "):
                        texto_completo_md = texto_completo_md.split('\n\n',1)
                        fecha_actualizacion = texto_completo_md[0]
                        texto_completo_md = texto_completo_md[1]
                    noticias_info['texto_contenido'] = texto_completo_md
                    noticias_info['titulo'] = titulo
                    noticias_info['fecha'] = md(texto_completo).split('\n\n',2)[1]
                    noticias_info['fecha_actualizacion'] = f"Nota actualizada el {fecha_actualizacion}" if fecha_actualizacion else None
                    noticias_info['fecha_del_evento'] = f"[Boletín SIUN {fecha_evento}]" if fecha_evento else None
                else:
                    noticias_info['texto_contenido'] = None
                    noticias_info['titulo'] = None
                    noticias_info['fecha'] = None
                    noticias_info['fecha_actualizacion'] = None
                    noticias_info['fecha_del_evento'] = None

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

def extraer_palabras_importantes(textos: list) -> tuple:
    # Cargar stopwords
    stop_words = STOPWORDS_ESPANOL.union(STOPWORDS_INGLES)

    # Cargar stopwords adicionales desde una URL
    response = requests.get(STOPWORDS_ADICIONALES_URL)
    stop_words_ = response.text.split('\n')
    stop_words.update(STOPWORDS_ADICIONALES)
    stop_words.update(STOPWORDS_BOLETIN)
    stop_words.update(STOPWORDS_FECHAS_ESPANOL)
    stop_words.update(STOPWORDS_FECHAS_INGLES)
    stop_words.update(STOPWORDS_REDES_SOCIALES)
    stop_words.update(STOPWORDS_LUGARES)
    stop_words.update(stop_words_)

    palabras_importantes = []
    for texto in textos:
        texto = unidecode.unidecode(texto.lower())
        doc = nlp(texto)
        palabras = [token.lemma_ for token in doc if token.is_alpha and token.lemma_ not in stop_words and len(token.lemma_) > 3]
        palabras_importantes.extend(palabras)

    wordcloud = WordCloud(width=800, height=800, background_color='white', stopwords=stop_words, min_font_size=10).generate(' '.join(palabras_importantes))

    palabras_frecuentes = Counter(palabras_importantes).most_common(100)
    with open('palabras_frecuentes.json', 'w', encoding='utf-8') as f:
        json.dump(palabras_frecuentes, f, ensure_ascii=False, indent=4)
    return wordcloud, palabras_frecuentes


def categorizar_noticias(noticias: List[dict], palabras_frecuentes: List[Tuple[str, int]]) -> List[dict]:
    top_palabras = [palabra for palabra, _ in palabras_frecuentes]

    for noticia in noticias:
        texto = unidecode.unidecode(noticia['texto_contenido'].lower())
        doc = nlp(texto)#q? qu hace esta linea de codigo: esta linea de codigo lo que hace es tokenizar el texto y lematizarlo 
        palabras = [token.lemma_ for token in doc if token.is_alpha]
        # sacar las categorias contando las palabras que se encuentran en el texto y que estan en la lista de palabras mas frecuentes, asigna las 3 que mas aparecen
        categorias = [palabra for palabra in top_palabras if palabra in palabras]
        # asignar las categorias a la noticia las que mas se repiten sin que se repitan y por orden de cantidad de aparicion de mayor a menor
        noticia['categorias'] = list(set(categorias))[:3]
    return noticias

# cargar palabras importantes
def cargar_palabras_frecuentes_json():
    with open('palabras_frecuentes.json', 'r', encoding='utf-8') as f:
        palabras_frecuentes = json.load(f)
    return palabras_frecuentes

# Ejecución principal
if __name__ == '__main__':
    guardar_noticias_json()
    noticias = cargar_noticias_json()  # Asegúrate de tener esta función definida
    all_texts = [noticia['texto_contenido'] for noticia in noticias]
    #wordcloud, palabras_frecuentes = extraer_palabras_importantes(all_texts)
    palabras_frecuentes= cargar_palabras_frecuentes_json()
    # Categorizar noticias
    noticias_categorizadas = categorizar_noticias(noticias, palabras_frecuentes)

    # Guardar noticias categorizadas en un nuevo archivo JSON
    with open('noticias_categorizadas.json', 'w', encoding='utf-8') as f:
        json.dump(noticias_categorizadas, f, ensure_ascii=False, indent=4)

    # Imprimir las 100 palabras más frecuentes
    print(palabras_frecuentes)