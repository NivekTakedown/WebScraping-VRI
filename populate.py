from typing import List
import requests
import json


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
        print(response.text)


def upload_image(filename):
    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/upload'
    filename = filename
    files = {
        "files": open(filename, 'rb')
    }
    response = requests.post(url, files=files)
    return response.json()

def upload_images(filenames):
    return list(map(lambda x: upload_image(x)[0]['id'], filenames))[0]

def upload_publication(publication):
    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/publications?locale=es'
    # tranformar json de publicacion
    tags = get_tags_ids(publication['tags'], get_tags())
    headers = {'Content-Type': 'application/json'}
    images_ids = upload_images(publication['images']) if publication['images'] else None
    
    print(publication)
    
    data = {
        "data": {
            "Publication": {
                "type": "Publicaciones VRI",
                "outstanding": False,
                "tags_posts": {
                    "connect": tags
                },
                "image": images_ids,
                "title": publication['title'],
                "shortDescription": publication['shortDescription'],
                "subtitle": publication['subtitle'],
                "fullDescription": publication['texto_contenido']
            }
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()

def populate_publications(publications):
    return list(map(lambda x: upload_publication(x), publications))
    


def cargar_noticias_json() -> List[dict]:
    with open('noticias_categorizadas.json', 'r', encoding='utf-8') as f:
        noticias = json.load(f)
    return noticias


def get_tag(item):
    return item['id'],item['attributes']['label'].lower()


def get_tags():
    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/tags-posts'
    response = requests.get(url)
    data = response.json()['data']

    # Usa map para aplicar get_tag a cada elemento en data
    tags = set(map(get_tag, data))
    return tags


def get_tags_ids(tags_labels, tags):
    return list(map(lambda x: {"id": x[0]}, filter(lambda x: x[1] in tags_labels, tags)))


if __name__ == '__main__':
    filename = 'palabras_frecuentes.json'
    #download_image('https://lh6.googleusercontent.com/0SZk1KAWMAi2Ck8KKb7OQLLD6e1eAVV9VIJaNE5ZyTbb85vHEZVdAdNbs9aKjfyZPrLXLkNDRK1M0wnWJG2iANTUUmCKgkHocTzDXn2a_BfbCbjHoU2-IOPdjwOcmzUUog=w1280')
    #populate_tags(filename)
    noticias = cargar_noticias_json()
    #download_images(noticias)
    tags = get_tags()
    print(get_tags_ids(['presencial', 'investigacion', 'informacion'], tags))
    print(populate_publications(noticias))