import os
import requests
from dotenv import load_dotenv
import random
import logging


def check_vk_error(response):
    if response.get('error'):
        raise requests.exceptions.HTTPError


def download_image(file_path, url):
    response = requests.get(url)
    response.raise_for_status()
    with open(file_path, "wb") as file:
        file.write(response.content)


def download_comic():
    url = 'https://xkcd.com/info.0.json'
    file_path = 'comics.jpg'
    response = requests.get(url)
    response.raise_for_status()
    number_of_comics = response.json()['num']
    random_number = random.randint(1, number_of_comics)
    comic_url = f'https://xkcd.com/{random_number}/info.0.json'
    comic_response = requests.get(comic_url)
    comic_response.raise_for_status()
    response = comic_response.json()
    comment = response['alt']
    comic_url = response['img']
    download_image(file_path, comic_url)
    return comment


def get_upload_url(access_token, group_id):
    payload = {
        'v': 5.131,
        'extended': 1,
        'access_token': access_token,
        'group_id': group_id
    }
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    upload_url_response = requests.get(url, params=payload)
    upload_url_response.raise_for_status()
    response = upload_url_response.json()
    check_vk_error(response)
    return response['response']['upload_url']


def upload_photo(upload_url):
    with open('comics.jpg', 'rb') as file:
        files = {
            'photo': file,
            }
        upload_photo_response = requests.post(upload_url, files=files)
    upload_photo_response.raise_for_status()
    response = upload_photo_response.json()
    check_vk_error(response)
    return response


def save_wall_photo(photo_server, photo, photo_hash, group_id, access_token):
    payload = {
            'server': photo_server,
            'photo': photo,
            'hash': photo_hash,
            'group_id': group_id,
            'access_token': access_token,
            'v': 5.131
    }

    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    save_wall_photo_response = requests.post(url, params=payload)
    save_wall_photo_response.raise_for_status()
    response = save_wall_photo_response.json()
    check_vk_error(response)
    return response


def post_photo(from_group, attachments, message, group_id, access_token):
    payload = {
        'v': 5.131,
        'owner_id':  f'-{group_id}',
        'from_group': from_group,
        'attachments': attachments,
        'message': message,
        'access_token': access_token
        }
    url = 'https://api.vk.com/method/wall.post'
    post_photo_response = requests.post(url, params=payload)
    post_photo_response.raise_for_status()
    response = post_photo_response.json()
    check_vk_error(response)
    return response


if __name__ == "__main__":
    load_dotenv()
    group_id = os.environ['ID_GROUP']
    access_token = os.environ['VK_TOKEN']
    try:
        message = download_comic()
        upload_url = get_upload_url(access_token, group_id)
        response = upload_photo(upload_url)
        v = 5.131
        photo_server = response['server']
        photo = response['photo']
        photo_hash = response['hash']
        album_response = save_wall_photo(photo_server, photo, photo_hash, group_id, access_token)
        owner_id = album_response['response'][0]['owner_id']
        media_id = album_response['response'][0]['id']
        attachments = f'photo{owner_id}_{media_id}'
        from_group = 1
        post_photo(from_group, attachments, message, group_id, access_token)
    except requests.exceptions.HTTPError:
        logging.exception('Ошибка в запросе к "vk.com" или "xkcd.com" ')
    finally:
        os.remove('comics.jpg')
