from typing import List
import requests
import json
import re


def populate_tags(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        names = json.load(f)

    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/tags-posts?locale=es'
    for i, name in enumerate(names):
        name = name[0].capitalize()
        data = {
            "icon": {
                "disconnect": [],
                "connect": [
                    {
                        "id": i,
                        "position": {
                            "end": True
                        }
                    }
                ]
            },
            "label": name
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)


def upload_image(filename):
    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/upload'
    filename = filename['path']
    files = {
        "files": open(filename, 'rb')
    }
    response = requests.post(url, files=files)
    return response.json()


def upload_images(filenames):
    return list(map(lambda x: upload_image(x), filenames))


def upload_publication(publication):
    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/publications'
    # tranformar json de publicacion
    tags = get_tags_ids(publication['tags'], get_tags())
    headers = {'Content-Type': 'application/json'}
    if len(publication['images']) > 0:
        images = publication['images']
        image = images[0]['id']  # Suponiendo que 'id' es 'hash' en tu estructura de datos
    else:
        image = None
    # xocatenar texto_contenido con fecha actualizacion
    publication['texto_contenido_blocks'] = publication['texto_contenido_blocks'] 
    postDescription = publication['texto_contenido_blocks']['postDescription']
    data = {
        "data": {
            "Publication": {
                "type": "Boletín SIUN",
                "outstanding": False,
                "tags_posts": {
                    "connect": tags
                },
                "image": image,
                "title": publication['title'],
                "shortDescription": publication['shortDescription'],
                "subtitle": publication['subtitle'],
                "postDescription": postDescription
            }
        }
    }
    #print(json.dumps(data, indent=4))
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response)
    return response.json()


def populate_publications(publications):
    return list(map(lambda x: upload_publication(x), publications))


def cargar_noticias_json() -> List[dict]:
    with open('noticias_categorizadas.json', 'r', encoding='utf-8') as f:
        noticias = json.load(f)
    return noticias


def get_tag(item):
    return item['id'], item['label'].lower()


def get_tags():
    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/tags-posts?populate=custom,10,id&pagination[pageSize]=100'
    response = requests.get(url)
    data = response.json()['customData']

    # Usa map para aplicar get_tag a cada elemento en data
    tags = set(map(get_tag, data))
    return tags


def get_tags_ids(tags_labels, tags):
    return list(map(lambda x: {"id": x[0]}, filter(lambda x: x[1] in tags_labels, tags)))


def is_patterm_in_text(text, pattern):
    return re.findall(pattern, text)




if __name__ == '__main__':
    filename = 'palabras_frecuentes.json'
    # populate_tags(filename)
    noticias = cargar_noticias_json()
    # download_images(noticias)
    tags = get_tags()
    publications = populate_publications(noticias)
    
