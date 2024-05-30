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
    return list(map(lambda x: upload_image(x), filenames))


def upload_publication(publication):
    url = 'https://web.unal.edu.co/vicerrectoria/investigacion-cms/api/publications?_locale=ES'
    # tranformar json de publicacion
    tags = get_tags_ids(publication['tags'], get_tags())
    headers = {'Content-Type': 'application/json'}
    if publication['images']:
        images_ids = upload_images(publication['images'])
        if len(images_ids) > 1:
            image = images_ids.pop()[0]['id']

        else:
            image = images_ids[0][0]['id']
    else:
        image = None
    if len(publication['images'])>1:
        publication['texto_contenido'] = replace_images(publication['texto_contenido'], images_ids)
    # xocatenar texto_contenido con fecha actualizacion
    publication['texto_contenido'] = publication['texto_contenido'] + f'\n\n  **{publication["fecha_actualizacion"]}**' if publication['fecha_actualizacion'] else publication['texto_contenido']
    data = {
        "data": {
            "Publication": {
                "type": "Publicaciones VRI",
                "outstanding": False,
                "tags_posts": {
                    "connect": tags
                },
                "image": image,
                "title": publication['title'],
                "shortDescription": publication['shortDescription'],
                "subtitle": publication['subtitle'],
                "fullDescription": publication['texto_contenido']
            },
            "locale": "es"
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
    return item['id'],item['label'].lower()


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


def replace_image(texto_contenido, image):
    pattern = r'\(foto: \[.*?\]\(.*?\)\)'
    new_replacement = f'<p align="center">\n    <img src="https://web.unal.edu.co/vicerrectoria/investigacion-cms/{image[0]["url"]}" alt="{image[0]["name"]}" />\n</p>'
    matches = is_patterm_in_text(texto_contenido, pattern)
    if matches:
        return texto_contenido.replace(matches[0], new_replacement)
    return texto_contenido


def replace_images(texto_contenido, images):
    for image in images:
        texto_contenido = replace_image(texto_contenido, image)
    return texto_contenido


if __name__ == '__main__':
    filename = 'palabras_frecuentes.json'
    # populate_tags(filename)
    noticias = cargar_noticias_json()
    # download_images(noticias)
    tags = get_tags()
    print(is_patterm_in_text('Esta es la primera vez que se reedita la versión de 1924 de La Vorágine, aseguraron los editores de la publicación (foto: [Facultad de Ciencias Humanas de la UNAL sede Bogotá en Twitter](https://twitter.com/humanasunal/status/1782904490703679910))\n\n Tres principales características hacen única a esta edición, que tuvo gran acogida en la FILBo el pasado 23 de abril, durante el [evento de lanzamiento de este clásico de la literatura y en el marco del centenario de su primera publicación](https://www.youtube.com/watch?v=uOvugwbF7nc). Luego de un siglo, en el año La Vorágine, esta novela sigue hablando de Colombia, del pasado, pero también del presente. \n\n Por Diana González\n\n Así lo aseguró el profesor Carlos Páramo, decano de la Facultad de Ciencias Humanas de la Universidad Nacional de Colombia (UNAL) y coeditor de la publicación, durante el [evento de presentación de esta edición crítica en la Feria Internacional del Libro de Bogotá](https://www.youtube.com/watch?v=uOvugwbF7nc) (FILBo). \n\nLa Facultad de Ciencias Humanas, en cabeza del profesor Carlos Páramo, lideró, preparó y ejecutó la iniciativa, que recoge la versión original de la novela, la de 1924, con el fin de magnificar su esplendor y mostrar la estética y estilística que le impregnó en esa época José Eustasio Rivera, egresado de la Facultad de Derecho de la UNAL.\n\nDurante la presentación del libro, sus editores comentaron al auditorio que esta edición crítica de La Vorágine se suma a las más de 140 ediciones que se han hecho de esta novela. Sin embargo, fueron radicales al enfatizar en que de esa cifra esta es la única edición que es fiel a la de 1924 y que eso implica que respeta incondicionalmente las particularidades e idiosincrasias de la primera versión, incluso aquellas que son susceptibles de interpretarse como errores de impresión.\n\nDe ahí que en el prefacio se le sugiera al lector cómo y por qué leer esta edición, que, en efecto, se presenta como una obra única, por cuanto introduce otras características que la diferencian de las numerosas versiones publicadas, empezando porque estas últimas dan cuenta de la versión de la obra de José Eustasio Rivera de 1928, que difiere en muchos aspectos de la original.\n\nPrecisamente, la presentación de la versión original es una de las tres principales características de esta publicación de la Facultad de Ciencias Humanas, que trae al presente la prosa poética y osada de la versión original de 1924, que fue criticada por entonces por el exceso de cadencia rítmica de su prosa.\n\n  \n Grabación del [evento de lanzamiento de la primera edición (1924) de La Vorágine](https://www.youtube.com/watch?v=uOvugwbF7nc), realizado el 19 de abril de 2024 en la FILBo 2024, evento organizado por la Facultad de Ciencias Humanas de la sede Bogotá y la Editorial Universidad Nacional de Colombia\n\n [[Consulte la programación de la UNAL en la FILBo 2024](https://editorial.unal.edu.co/editorial-unal/filbo-2024)]\n\n Tres características hacen única a esta publicación que será distribuida de manera gratuita entre la comunidad universitaria de la Sede Bogotá. Foto: Juan Camilo Ayala, Centro Editorial de la Facultad de Ciencias Humanas de la UNAL sede Bogotá.\n\n «Es la primera vez en la historia que se reedita la primera edición de La Vorágine, que es la de 1924, porque habitualmente la que ha experimentado miles de reediciones es la edición de 1928, que fue la última autorizada por Rivera. Pero la del 24 —que sigue siendo exactamente la misma historia con el mismo orden de párrafos, etcétera— tiene mucha más cadencia poética, es mucho más atrevida», aclaró el profesor Carlos Páramo en entrevista para la Maestría en Museología y Gestión del Patrimonio (MMGP) de la Universidad Nacional de Colombia. \n\nLa segunda característica que la hace única es el uso de las fotografías que ilustraron la primera versión, pues hasta el momento actual ninguna edición de la obra había incluido dichos recursos, que sí se evidencian en la edición crítica de la UNAL, la cual respeta su sentido original y les da la importancia que merecen en cuanto son partes orgánicas de la narración. \n\n«La Vorágine fue una de las primeras novelas, en la literatura universal, que tuvo la osadía de difuminar la frontera entre la “realidad” y la “ficción” de la narración al incluir testimonios visuales que demostraran la presumible factualidad de las situaciones descritas», mencionan los editores en el texto de introducción de la obra crítica de La Vorágine. \n\nAl respecto, el profesor Carlos Páramo explicó que «Rivera fue enormemente osado en incluir fotografías. Tal fue el impacto que causó este recurso y, en cierta manera, tan poco entendido en su momento que al final Rivera terminó sustituyendo las fotografías por mapas. Es un gesto vanguardista a todas luces y en esa medida retomar las fotografías como texto tenía todo el sentido. Pero, esta es la primera edición que lo hace y que además medita sobre el talante de estas fotografías».\n\nEl tercer elemento innovador de esta edición de la UNAL es que presenta un apartado de notas que coteja por primera vez los manuscritos que están en la Biblioteca Nacional de Colombia con la edición original de La Vorágine y que no solo revelan las variantes más significativas entre estas versiones —especialmente las referidas a los nombres de los personajes y a versiones alternas de las situaciones—, sino que aportan nuevas luces sobre las bases históricas y las intenciones narrativas de José Eustasio Rivera.\n\n Cien años después, La Vorágine continúa teniendo vigencia (foto: [Facultad de Ciencias Humanas de la UNAL sede Bogotá en Twitter](https://twitter.com/humanasunal/status/1782904475876815298))\n\n Así mismo, y como valor agregado, esta edición crítica incluye en su interior una última sección denominada «Para hundirse en la vorágine», que presenta quince artículos de diversos autores que, además de demostrar que esta obra sigue vigente aún cien años después, propician un diálogo entre la novela y las distintas disciplinas académicas sociales y humanas que convergen en ella. \n\n«Estos quince ensayos, a guisa de sendas invitaciones desde muy distintos campos disciplinares, buscan leer La Vorágine desde la museografía o museología, desde la antropología, desde la geografía, desde los estudios de género del psicoanálisis, desde la realización audiovisual, desde los estudios literarios, etc.», concluyó el profesor Páramo durante su conversación con la MMGP.\n\nEl equipo editor de esta versión crítica son, además del profesor Carlos Páramo, Carmen Elisa Acosta, profesora  de la Facultad de Ciencias Humanas y actual directora del Instituto Caro y Cuero; Ángela Zárate, antropóloga; y Jineth Ardila Ariza, directora del Centro Editorial de la Facultad de Ciencias Humanas, además de Norma Donato Rodríguez, miembro del comité curatorial de esta edición y quien fungió como asesora de curaduría del texto de la novela.\n\nUna novela vigente en pleno siglo XXI\n-------------------------------------\n\nDe acuerdo con el profesor Carlos Páramo, el tema de la novela sigue tan vigente como en el mismo momento de su publicación. Así lo aseguró al momento de indagársele por la relevancia y carácter trascendental al tiempo y el espacio de esta obra magistral.\n\n«Irónicamente, es tanto más vigente hoy en día que en la época en la que apareció; denunciaba situaciones cruentas atroces en las fronteras de Colombia en torno a una economía extractiva como el caucho. Hoy en día nos damos cuenta de todos los demás asuntos que complejizan y vuelven incómoda la relación con la naturaleza. El problema de las economías extractivas es que ya no solo es el caucho, sino que puede ser cualquier otro, la relación entre lo humano y no humano, es decir, hay múltiples situaciones», recalcó.\n\nPor su parte, Jineth Ardila mencionó durante su intervención que esta edición permite pensar y reflexionar en que esta novela aún tiene mucho por decir. Por eso, invitó a creer, a no perder la fe en que hay cosas nuevas por decir y descubrir. \n\nDistribución gratuita a la comunidad UNAL\n-----------------------------------------\n\nEl profesor Carlos Páramo reveló, durante la entrevista, que, gracias a la Dirección Académica de la Sede Bogotá de la Universidad Nacional de Colombia, se pudo financiar un amplio número de ejemplares de esta edición crítica de La Vorágine que serán distribuidos de manera gratuita entre los diversos miembros de la comunidad de la Sede, después del mes de mayo próximo. \n\n«Contamos con una generosa financiación que permitió adelantar un tiraje de diez mil ejemplares que serán distribuidos gratuitamente entre estudiantes, administrativas y administrativos, y docentes de la Sede Bogotá. Evidentemente, apelando a ciertos mecanismos de selección, porque diez mil es una cifra que es muy grande y muy pequeña a la vez para la Sede, pero que permite una cobertura generosa», concluyó.\n\n[Diana González, Maestría en Museología y Gestión del Patrimonio UNAL]', r'\(foto: \[.*?\]\(.*?\)\)'))
    publications = populate_publications(noticias)
    
