#!/usr/bin/env python3
"""Function for posting articles to site."""
import json
import requests

URL_LOGIN = 'http://localhost:8000/admin/'
URL_ENDPOINT = 'http://localhost:8000/post_articles/'
DATA_FILE = 'articles.json'


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


if __name__ == '__main__':
    with open(DATA_FILE, 'r') as f:
        add_articles(json.load(f), 'some_user', 'some_pass')
