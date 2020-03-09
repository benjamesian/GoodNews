import json
from language_processing.ibmcloud.ibmcloud import get_sentiments
from multiprocessing import Pool
import os
import requests
import socket
from threading import Thread


URL_LOGIN = 'http://localhost:8000/admin/'
URL_ENDPOINT = 'http://localhost:8000/'

USERNAME = os.getenv('GOOD_NEWS_USERNAME')
PASSWORD = os.getenv('GOOD_NEWS_PASSWORD')


def add_articles(articles):
    """Post articles to api endpoint so that can be added to db."""
    with requests.Session() as session:
        session.get(URL_LOGIN)
        session.headers.update({
            'X-CSRFToken': session.cookies.get('csrftoken')
        })

        login_data = dict(username=USERNAME,
                          password=PASSWORD,
                          next='/')
        session.post(URL_LOGIN, data=login_data,
                     headers=dict(Referer=URL_LOGIN))
        session.headers.update({
            'content-type': 'application/json',
            'X-CSRFToken': session.cookies.get('csrftoken')
        })

        session.post(URL_ENDPOINT, data=json.dumps(articles))


def get_batch_sentiments(articles):
    """Process articles in parallel."""
    with Pool() as pool:
        return pool.map(get_sentiments, articles)


def process_articles(articles):
    article_titles = map(lambda x: x.get('title', ''), articles)
    raw_sentiments = get_batch_sentiments(article_titles)
    raw_sentiments = [
        sent.get('document_tone', {}).get('tones', [])
        for sent in raw_sentiments
    ]
    articles_data = {
        'articles': [
            {
                'article_data': article,
                'sentiments': [
                    {
                        'name': sentiment.get('tone_id'),
                        'magnitude': sentiment.get('score')
                    }
                    for sentiment in sentiments
                ]
            }
            for article, sentiments in zip(articles, raw_sentiments)]
    }
    add_articles(articles_data)

# old wsgi when considering gunicorn
# def application(environ, start_response):
#     """WSGI server application"""
#     content = json.load(environ['wsgi.input'])
#     articles = get_batch_sentiments(content.get('data'))
#     add_articles(articles, USERNAME, PASSWORD)

#     body = {'message': 'data posted'}
#     status = '200 OK'
#     headers = [('Content-Type', 'application/json'),
#                ('Content-Length', str(len(body)))]
#     start_response(status, headers)
#     return [json.dumps(body)]


def handle_connection(connection):
    data = b''
    with connection:
        while True:
            new_data = connection.recv(1024)
            data += new_data
            if not new_data:
                break
    try:
        process_articles(json.load(data))
    except json.JSONDecodeError:
        pass


if __name__ == "__main__":
    server_address = './uds_socket'

    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.bind(server_address)
        sock.listen(1)

        while True:
            connection, client_address = sock.accept()
            ct = Thread(target=handle_connection, args=(connection,))
            ct.start()
