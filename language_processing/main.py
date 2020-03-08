import json
from language_processing.ibmcloud import get_sentiments
from multiprocessing import Pool
import os
import requests


URL_LOGIN = 'http://localhost:8000/admin/'
URL_ENDPOINT = 'http://localhost:8000/'
DATA_FILE = 'articles.json'

USERNAME = os.getenv('GOOD_NEWS_USERNAME')
PASSWORD = os.getenv('GOOD_NEWS_PASSWORD')


def add_articles(articles, username, password):
    """Post articles to api endpoint so that can be added to db."""
    with requests.Session() as session:
        session.get(URL_LOGIN)
        session.headers.update({
            'X-CSRFToken': session.cookies.get('csrftoken')
        })

        login_data = dict(username=username,
                          password=password,
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


def application(environ, start_response):
    """WSGI server application"""
    content = json.load(environ['wsgi.input'])
    articles = get_batch_sentiments(content.get('data'))
    add_articles(articles, USERNAME, PASSWORD)

    body = {'message': 'data posted'}
    status = '200 OK'
    headers = [('Content-Type', 'application/json'),
               ('Content-Length', str(len(body)))]
    start_response(status, headers)
    return json.dumps(body)
