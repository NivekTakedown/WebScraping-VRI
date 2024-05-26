import requests
import json


def get_next_id():
    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/tags-posts'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza una excepción si la respuesta contiene un código de estado HTTP de error
        tags = response.json()
    except requests.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return None
    except Exception as err:
        print(f'Other error occurred: {err}')
        return None

    tags.sort(key=lambda x: x['id'])
    last_id = tags[-1]['id']
    next_id = last_id + 1
    return next_id


def populate_tags(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        names = json.load(f)

    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/tags-posts'
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


if __name__ == '__main__':
    filename = 'palabras_frecuentes.json'
    populate_tags(filename)