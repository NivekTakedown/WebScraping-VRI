import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Tuple, Optional
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
from wordcloud import WordCloud
import aiohttp
import asyncio
import markdown2
from PIL import Image
from bs4 import BeautifulSoup
import json
import os

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

STOPWORDS_ESPANOL = set(stopwords.words('spanish'))
STOPWORDS_INGLES = set(stopwords.words('english'))
STOPWORDS_ADICIONALES_URL = 'https://gist.githubusercontent.com/cr0wg4n/78554c5d0afa9944d2fa3a4435d83a57/raw/df59fb916108f2a58bf1a3d8c62818b44231586d/spanish-stop-words.txt'
STOPWORDS_ADICIONALES = [
    'más', 'invitar', 'uno', 'enlace', 'vicerrectorio', 'invitar', 'también',
    'sólo', 'aquí', 'ahora', 'https', 'http', 'com', 'co', 'www',
    'viceinvestigacion', 'unal', 'edu', 'col', 'html', 'p', 'div', 'class',
    'img', 'src'
]
STOPWORDS_BOLETIN = [
    'boletin', 'siun', 'atencion', 'legal', 'control', 'interno', 'vicerrectoria',
    'enlaces', 'ma', 'hora', 'consultar', 'interes', 'linea', 'preguntas',
    'invitamos', 'usuario', 'estadisticas', 'regimen', 'quejas', 'reclamos',
    'notificaciones', 'judiciales', 'glosario', 'contratacion', 'rendicion',
    'cuentas', 'nota', 'acerca', 'distinta', 'cierre', 'mailto', 'fecha', 'area',
    'web', 'pagina', 'registro', 'time', 'modalidad', 'formulario', 'trave',
    'application', 'persona', 'mar', 'ma'
]
STOPWORDS_FECHAS_ESPANOL = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
    'septiembre', 'octubre', 'noviembre', 'diciembre', 'lunes', 'martes',
    'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'
]
STOPWORDS_FECHAS_INGLES = [
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december', 'monday', 'tuesday',
    'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
]
STOPWORDS_REDES_SOCIALES = [
    'twitter', 'instagram', 'youtube', 'facebook', 'whatsapp', 'linkedin',
    'telegram', 'tiktok', 'snapchat', 'pinterest', 'reddit', 'tumblr', 'flickr',
    'quora', 'twitch', 'spotify', 'soundcloud', 'redes', 'sociales'
]
STOPWORDS_LUGARES = [
    'bogota', 'medellin', 'cali', 'barranquilla', 'cartagena', 'cucuta', 'bucaramanga',
    'pereira', 'manizales', 'ibague', 'villavicencio', 'neiva', 'pasto', 'tunja',
    'popayan', 'quibdo', 'monteria', 'santa marta', 'villavicencio', 'valledupar',
    'arauca', 'yopal', 'leticia', 'puerto inirida', 'san jose del guaviare', 'mitu',
    'puerto carreño', 'quibdo', 'san andres', 'providencia', 'bogotá', 'medellín',
    'cali', 'barranquilla', 'cartagena', 'cúcuta', 'colombia', 'universidad', 'nacional'
]


def get_tag(item):
    return item['id'], item['label'].lower()


def get_tags():
    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/tags-posts?populate=custom,10,id&pagination[pageSize]=100'
    response = requests.get(url)
    data = response.json()['customData']

    # Usa map para aplicar get_tag a cada elemento en data
    tags = set(map(get_tag, data))
    return tags


async def download_images(noticias):
    link_to_filename = {}
    json_objects = []
    async with aiohttp.ClientSession() as session:
        for noticia in noticias:
            if noticia['enlaces_imagenes']:
                for i, url in enumerate(noticia['enlaces_imagenes']):
                    filename = f'{noticia["enlace"]}_{i}.'
                    filename = await download_image(session, url, filename)
                    link_to_filename[url] = filename

                    # Obtener atributos de la imagen
                    size, width, height = get_image_attributes(filename)
                    # Crear objeto JSON
                    json_object = {
                        "name": "-aOBQB84e4LlZj-NeQMzIU1wiR0gj5hPL_JAVQKS_LkJQ9EZMMM7PjvNLvdwkWaI_fbxbCtidcy7qjk4yZoOjE-LEP9LfHOUPqA5zYdzOf1iO-qKJNWnsKpL_OgFIC5qXA=w1280",
                        "size": size,
                        "width": width,
                        "height": height,
                        "filename": filename,
                        "url": url
                    }
                    json_objects.append(json_object)

                    await asyncio.sleep(0.1)
    return json_objects


def get_image_attributes(filename):
    with Image.open(filename) as img:
        size = os.path.getsize(filename)
        width, height = img.size
    return size, width, height


async def download_image(session, url, filename):
    async with session.get(url) as response:
        filename = 'imagenes/' + filename + response.headers['Content-Type'].split('/')[-1]
        with open(filename, 'wb') as f:
            f.write(await response.read())
    return filename


def markdown_to_json_blocks(markdown_content: str,images_info) -> dict:
    # Convertir Markdown a HTML
    html_content = markdown2.markdown(markdown_content)
    print(html_content)
    # Analizar el HTML y convertirlo a bloques JSON
    soup = BeautifulSoup(html_content, 'html.parser')
    post_description = convert_html_to_json_blocks(soup,images_info)
    return {"postDescription": post_description}


def convert_html_to_json_blocks(soup,images_info):
    def convert_node_to_block(node):
        if node.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(node.name[1])
            return {
                "type": "heading",
                "children": [{"text": node.get_text(), "type": "text"}],
                "level": level,
                "size": f"h{level}"
            }
        elif node.name == 'p':
            children = []
            for child in node:
                if child.name == 'b':
                    children.append({"bold": True, "text": child.get_text(), "type": "text"})
                elif child.name == 'i':
                    children.append({"italic": True, "text": child.get_text(), "type": "text"})
                elif child.name == 'a':
                    children.append({
                        "url": child.get('href'),
                        "type": "link",
                        "children": [{"text": child.get_text(), "type": "text"}]
                    })
                elif child.name == 'img':
                    children.append(create_image_block(child,images_info))
                else:
                    children.append({"text": child.string or "", "type": "text"})
            return {"type": "paragraph", "children": children}
        elif node.name in ['ul', 'ol']:
            list_type = "unordered" if node.name == 'ul' else "ordered"
            children = []
            for li in node.find_all('li', recursive=False):
                li_children = []
                for child in li:
                    block = convert_node_to_block(child)
                    if block:
                        li_children.append(block)
                children.append({"type": "list-item", "children": li_children})
            return {
                "type": "list",
                "format": list_type,
                "children": children
            }
        elif node.name == 'img':
            return create_image_block(node, images_info)
        
        elif node.name == 'a':
            return {
                "url": node.get('href'),
                "type": "link",
                "children": [convert_node_to_block(child) for child in node.contents]
            }
        return None

    def create_image_block(img_node, images_info):
        src = img_node.get('src', '')
        image_info = next((img for img in images_info if img['url'] == src), None)
        
        if image_info:
            return {
                "type": "image",
                "image": {
                    "ext": image_info['filename'].split('.')[-1],
                    "url": image_info['filename'],  # Cambiado a nombre del archivo
                    "hash": image_info['filename'].split('/')[-1].split('.')[0],
                    "mime": f"image/{image_info['filename'].split('.')[-1]}",
                    "name": image_info['filename'].split('/')[-1],
                    "size": image_info['size'],
                    "width": image_info['width'],
                    "height": image_info['height'],
                    "caption": img_node.get('alt'),
                    "formats": {},
                    "provider": "local",
                    "createdAt": datetime.now().isoformat(),
                    "updatedAt": datetime.now().isoformat(),
                    "previewUrl": None,
                    "alternativeText": img_node.get('alt'),
                    "provider_metadata": None
                },
                "children": [{"text": "", "type": "text"}]
            }
        else:
            # Fallback si no se encuentra la información de la imagen
            return {
                "type": "image",
                "image": {
                    "ext": src.split('.')[-1] if '.' in src else '',
                    "url": src,
                    "hash": src.split('/')[-1].split('.')[0] if '/' in src else '',
                    "mime": f"image/{src.split('.')[-1]}" if '.' in src else '',
                    "name": src.split('/')[-1] if '/' in src else '',
                    "size": 0,
                    "width": img_node.get('width'),
                    "height": img_node.get('height'),
                    "caption": img_node.get('alt'),
                    "formats": {},
                    "provider": "local",
                    "createdAt": datetime.now().isoformat(),
                    "updatedAt": datetime.now().isoformat(),
                    "previewUrl": None,
                    "alternativeText": img_node.get('alt'),
                    "provider_metadata": None
                },
                "children": [{"text": "", "type": "text"}]
            }
            

    blocks = []
    for node in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'img']):
        block = convert_node_to_block(node)
        if block:
            blocks.append(block)

    return blocks


class NoticiasExtractor:
    def __init__(self, session):
        self.session = session

    async def filtrar_enlaces(self) -> List[str]:
        website = f'{BASE_WEBSITE}/investigación'
        try:
            async with self.session.get(website) as response:
                response.raise_for_status()
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'lxml')
                enlaces = soup.find_all('a', class_='aJHbb hDrhEe HlqNPb')
                enlaces_filtrados = [
                    enlace['href'] for enlace in enlaces
                    if '/investigación/apoyo-a-la-investigación/boletín-siun' in enlace['href']
                       and len(enlace['href']) > 56
                ]
                return enlaces_filtrados
        except aiohttp.ClientError as e:
            print(f"Error al obtener la página web: {e}")
            return []
        except Exception as e:
            print(f"Un error ocurrió: {e}")
            return []

    def extraer_enlaces(self, soup: BeautifulSoup, clase: str) -> Tuple[List[str], List[str]]:
        elementos = soup.find_all("div", class_=clase)
        enlaces_imagenes = [img['src'] for elemento in elementos for img in elemento.find_all('img')]
        enlaces_otros = [a['href'] for elemento in elementos for a in elemento.find_all('a') if 'http' in a['href']]
        print(f"Enlaces de imágenes: {enlaces_imagenes} \n")
        # print(f"Enlaces de otros: {enlaces_otros} \n")
        return enlaces_imagenes, enlaces_otros

    async def bajar_texto_noticias(self, enlaces: List[str]) -> List[dict]:
        noticias_lista = []
        enlaces = enlaces[:3]  # Limitar la cantidad de enlaces para pruebas
        async with aiohttp.ClientSession() as session:
            for enlace in enlaces:
                print(f"Enlace: {enlace}")
                website = f"{BASE_WEBSITE}{enlace}"
                noticias_info = {}
                try:
                    async with session.get(website) as response:
                        response.raise_for_status()
                        soup = BeautifulSoup(await response.text(), 'lxml')

                    def agregar_info(clase: str) -> str:
                        elementos = soup.find_all("div", class_=clase)
                        if elementos:
                            texto = ' '.join(str(elemento) for elemento in elementos)
                            return texto
                        return None

                    def buscar_substring(texto: str, subcadena: str) -> bool:
                        return texto.startswith(subcadena)

                    def getContent():
                        main_content = soup.find(id="content")
                        if not main_content:
                            main_content = soup.body
                        if main_content:
                            for header in main_content.find_all(['header', 'nav']):
                                header.decompose()
                            for footer in main_content.find_all('footer'):
                                footer.decompose()
                        return str(main_content)

                    texto_completo = agregar_info("tyJCtd mGzaTb Depvyb baZpAe")
                    if texto_completo:
                        texto_completo_md = md(getContent()).split('\n\n', 2)
                        titulo = texto_completo_md[1]
                        
                        texto_completo_md = \
                            texto_completo_md[2].split('\n\n Te invitamos a consultar nuestras redes sociales')[
                                0].split(
                                "Investigación, UNAL\n\n")[1]
                        fecha_actualizacion = None

                        if buscar_substring(texto_completo_md, "Nota actualizada el "):
                            texto_completo_md = texto_completo_md.split('\n\n', 1)
                            fecha_actualizacion = texto_completo_md[0]
                            texto_completo_md = texto_completo_md[1]
                        fecha_cierre = None
                        if buscar_substring(texto_completo_md, " Cierre: "):
                            texto_completo_md = texto_completo_md.split('\n\n', 1)
                            fecha_cierre = texto_completo_md[0]
                            texto_completo_md = texto_completo_md[1]
                        fecha_evento = None
                        
                        
                        texto_completo_md = texto_completo_md.rsplit('\n\n', 1)
                        fecha_evento = texto_completo_md[1]
                        texto_completo_md = texto_completo_md[0]
                        noticias_info['texto_contenido'] = texto_completo_md

                        noticias_info['shortDescription'] = texto_completo_md[:150]
                        noticias_info['title'] = titulo
                        noticias_info['fecha'] = md(texto_completo).split('\n\n', 2)[1]
                        noticias_info['fecha_cierre'] = fecha_cierre if fecha_cierre else None
                        noticias_info[
                            'fecha_actualizacion'] = f"Nota actualizada el {fecha_actualizacion}" if fecha_actualizacion else None
                        noticias_info['fecha_del_evento'] = fecha_evento if fecha_evento else None
                        noticias_info['enlace'] = enlace.rsplit('/', 1)[1].capitalize()
                        noticias_info['subtitle'] = enlace.rsplit('/', 1)[1].replace('-', ' ').capitalize()
                        # noticias_info['texto_contenido'] = noticias_info['texto_contenido'].replace('\n','&nbsp')
                        
                        # noticias_info['shortDescription'] = noticias_info['shortDescription'].replace('\n','&nbsp')
                    else:
                        noticias_info['texto_contenido'] = None
                        noticias_info['titulo'] = None
                        noticias_info['fecha'] = None
                        noticias_info['fecha_actualizacion'] = None
                        noticias_info['fecha_del_evento'] = None
                        noticias_info['enlace'] = enlace
                    enlaces_imagenes, enlaces_otros = self.extraer_enlaces(soup, "tyJCtd baZpAe")
                    noticias_info['enlaces_imagenes'] = list(
                        set(enlace for enlace in enlaces_imagenes if enlace not in ENLACES_EXCLUIR))
                    noticias_info['images'] = await download_images([noticias_info])
                    if 'images' in noticias_info and isinstance(noticias_info['images'], list) and len(noticias_info['images']) > 0:
                        first_image = noticias_info['images'][0].get('url')
                        if first_image and f'{first_image})' in texto_completo_md:
                            texto_completo_md = texto_completo_md.split(f'{first_image})', 2)[1]
                    noticias_info['texto_contenido_blocks'] = markdown_to_json_blocks(texto_completo_md, noticias_info['images'])
                    noticias_lista.append(noticias_info)
                    await asyncio.sleep(0.1)

                except aiohttp.ClientError as e:
                    print(f"Error al obtener la página web: {e}")
                except Exception as e:
                    print(f"Un error ocurrió: {e}")

        return noticias_lista


class JSONHandler:
    @staticmethod
    def guardar_noticias_json(noticias_lista: List[dict]):
        with open('noticias.json', 'w', encoding='utf-8') as f:
            json.dump(noticias_lista, f, ensure_ascii=False, indent=4)

    @staticmethod
    def cargar_noticias_json() -> List[dict]:
        with open('noticias.json', 'r', encoding='utf-8') as f:
            noticias = json.load(f)
        return noticias

    @staticmethod
    def guardar_palabras_frecuentes_json(palabras_frecuentes: List[Tuple[str, int]]):
        with open('palabras_frecuentes.json', 'w', encoding='utf-8') as f:
            json.dump(palabras_frecuentes, f, ensure_ascii=False, indent=4)

    @staticmethod
    def cargar_palabras_frecuentes_json() -> List[Tuple[str, int]]:
        with open('palabras_frecuentes.json', 'r', encoding='utf-8') as f:
            palabras_frecuentes = json.load(f)
        return palabras_frecuentes


class AnalizadorTextos:
    @staticmethod
    def extraer_palabras_importantes(textos: List[str]) -> Tuple[WordCloud, List[Tuple[str, int]]]:
        stop_words = STOPWORDS_ESPANOL.union(STOPWORDS_INGLES)

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
            palabras = [token.lemma_ for token in doc if
                        token.is_alpha and token.lemma_ not in stop_words and len(token.lemma_) > 3]
            palabras_importantes.extend(palabras)

        wordcloud = WordCloud(width=800, height=800, background_color='white', stopwords=stop_words,
                              min_font_size=10).generate(' '.join(palabras_importantes))

        palabras_frecuentes = Counter(palabras_importantes).most_common(100)
        JSONHandler.guardar_palabras_frecuentes_json(palabras_frecuentes)
        return wordcloud, palabras_frecuentes

    @staticmethod
    def categorizar_noticias(noticias: List[dict], palabras_frecuentes: List[Tuple[str, int]]) -> List[dict]:
        top_palabras = [palabra.lower() for palabra, _ in palabras_frecuentes]

        for noticia in noticias:
            texto = unidecode.unidecode(noticia['texto_contenido'].lower())
            doc = nlp(texto)
            palabras = [token.lemma_ for token in doc if token.is_alpha]
            categorias = [palabra for palabra in top_palabras if palabra in palabras]
            noticia['tags'] = list(set(categorias))[:3]
        return noticias


async def main():
    async with aiohttp.ClientSession() as session:
        extractor = NoticiasExtractor(session)
        enlaces = await extractor.filtrar_enlaces()  # Añade 'await' aquí

        num_coroutines = 5
        enlaces_divididos = np.array_split(enlaces, num_coroutines)

        tareas = [extractor.bajar_texto_noticias(enlaces_parte) for enlaces_parte in enlaces_divididos]
        resultados = await asyncio.gather(*tareas)

        noticias_lista = [noticia for resultado in resultados for noticia in resultado]

        JSONHandler.guardar_noticias_json(noticias_lista)

    noticias = JSONHandler.cargar_noticias_json()
    all_texts = [noticia['texto_contenido'] for noticia in noticias]

    palabras_frecuentes = list(map(lambda x: [x[1], x[0]], get_tags()))
    noticias_categorizadas = AnalizadorTextos.categorizar_noticias(noticias, palabras_frecuentes)

    with open('noticias_categorizadas.json', 'w', encoding='utf-8') as f:
        json.dump(noticias_categorizadas, f, ensure_ascii=False, indent=4)

    print(palabras_frecuentes)


if __name__ == '__main__':
    asyncio.run(main())