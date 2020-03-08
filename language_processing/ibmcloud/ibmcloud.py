#!/usr/bin/env python3
"""
Provides an app to collect news articles from the web
"""
import os
import io
import requests

TEST_DATA = 'Do not be alarmed. This is only a test.'

API = 'https://api.us-south.tone-analyzer.watson.cloud.ibm.com'
RES = '/instances/0a8e6873-8e98-4aa7-a559-90114da2c819/v3/tone'
URL = '/'.join([CLOUDAPI, RESOURCE])


if __name__ == "__main__":
    KEY = os.getenv('GOOD_NEWS_IBM_CLOUD_API_KEY',
                    'apGNtpjJ5RonxaYWwbKjcpoRbIFBkSNmSkQVKpuOByTG')
    SRC = os.getenv('GOOD_NEWS_ARTICLE_URI', io.StringIO(TEST_DATA)

    PARAMS = {'version': '2017-09-21'}
    HEADERS = {"Content-Type": "application/json"}

    with open(TONESRC, 'r') as source:
        RESPONSE = requests.post(
            CLOUDURL,
            headers=HEADERS,
            data=source.read(),
            auth=('apikey', CLOUDKEY))
        print(RESPONSE.json())
