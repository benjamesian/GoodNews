#!/usr/bin/env python3
"""This is a module docstring."""
import json
import os
import requests

API_KEY = os.getenv('GOOD_NEWS_IBM_CLOUD_API_KEY')
if not API_KEY:
    path = os.path.join(os.path.dirname(__file__), os.pardir,
                        'private/GOOD_NEWS_IBM_CLOUD_API_KEY.txt')
    with open(path, 'r') as f:
        API_KEY = f.read()
URL = ("https://api.us-south.tone-analyzer.watson.cloud.ibm.com"
       "/instances/0a8e6873-8e98-4aa7-a559-90114da2c819"
       "/v3/tone")
HEADERS = {
    "Content-Type": "application/json"
}
PARAMS = {
    'version': '2017-09-21'
}


def get_sentiments(text: str):
    """Run text through IBM tone analysis."""
    data = {'text': text}
    response = requests.post(URL, headers=HEADERS, data=json.dumps(data),
                             auth=('apikey', API_KEY), params=PARAMS)
    return response.json()


if __name__ == '__main__':
    from sys import argv
    print(get_sentiments(argv[1]))
