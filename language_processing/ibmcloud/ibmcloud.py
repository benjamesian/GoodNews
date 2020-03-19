#!/usr/bin/env python3
"""This is a module docstring."""
import os
import requests

API_KEY = os.getenv('NATURAL_LANGUAGE_UNDERSTANDING_APIKEY3')
BASE_URL = 'https://api.us-south.tone-analyzer.watson.cloud.ibm.com'
API_INSTANCE = os.getenv('NATURAL_LANGUAGE_UNDERSTANDING_INSTANCE3')
URL = f'{BASE_URL}/instances/{API_INSTANCE}/v3/tone'
HEADERS = {
    "Content-Type": "text/html"
}
PARAMS = {
    'version': '2017-09-21'
}


def get_sentiments(html_string: str):
    """Run text through IBM tone analysis."""
    response = requests.post(URL, headers=HEADERS, data=html_string,
                             auth=('apikey', API_KEY), params=PARAMS)
    return response.json()


if __name__ == '__main__':
    from sys import argv
    print(get_sentiments(argv[1]))
