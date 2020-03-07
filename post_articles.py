#!/usr/bin/env python3
from datetime import datetime
import json
import requests
from sys import argv

LOGIN_DATA = {
    'username': argv[1],
    'password': argv[2]
}
URL_LOGIN = 'http://localhost:8000/admin/'
URL_ENDPOINT = 'http://localhost:8000/post_articles/'
DATA_FILE = 'articles.json'


def add_articles(articles, login=LOGIN_DATA):
    with requests.Session() as s:
        s.get(URL_LOGIN)
        s.headers.update({'X-CSRFToken': s.cookies.get('csrftoken')})

        login_data = dict(username=login.get('username'),
                          password=login.get('password'),
                          next='/')
        r = s.post(URL_LOGIN, data=login_data,
                   headers=dict(Referer=URL_LOGIN))
        s.headers.update({
            'content-type': 'application/json',
            'X-CSRFToken': s.cookies.get('csrftoken')
        })

        r = s.post(
            URL_ENDPOINT,
            data=json.dumps(articles)
        )


if __name__ == '__main__':
    with open(DATA_FILE, 'r') as f:
        articles = json.load(f)
        add_articles(articles)
