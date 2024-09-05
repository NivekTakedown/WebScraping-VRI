import requests
import json


def get_tag(item):
    return item['id'], item['label'].lower()


def get_tags():
    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/tags-posts?populate=custom,10,id&pagination[pageSize]=100'
    response = requests.get(url)
    data = response.json()['customData']

    # Use map to apply get_tag to each element in data
    tags = set(map(get_tag, data))

    # Save the tags into a JSON file
    with open('tags.json', 'w') as file:
        json.dump(list(tags), file)

    return tags


def populate_tags(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        names = json.load(f)

    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/tags-posts?locale=ES'
    headers = {'Content-Type': 'application/json'}

    for i in enumerate(names):
        payload = {
            "data": {
                "icon": {
                    "disconnect": [],
                    "connect": [
                        {
                            "id": 37,
                            "position": {
                                "end": True
                            }
                        }
                    ]
                },
                "label": i[1][1]
            }
        }
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        print(response.text)


#get_tags()
populate_tags('tags.json')
