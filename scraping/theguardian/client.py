#!/usr/bin/env python3
"""
Provides a client to request articles from the Guardian API
"""
import json
import requests
import scraping
from scraping.base.client import Client as BaseClient
from scraping.theguardian import API_URL, ARTICLE_KEY_MAP, AUTH_FILE, DATA_FILE


class Client(BaseClient):  # pylint: disable=too-few-public-methods
    """
    Definition of a class to retrieve news from The Guardian
    """
    api_url = '/'.join([API_URL, 'search'])
    auth_file = AUTH_FILE
    data_file = DATA_FILE
    name = 'TheGuardian'

    # pylint: disable=super-init-not-called
    def __init__(self, auth_file=None, data_file=None):
        """
        Instantiate a Guardian API client with credentials
        """
        if auth_file:
            self.auth_file = auth_file
        if data_file:
            self.data_file = data_file
        try:
            with open(self.auth_file) as istream:
                self.auth = json.load(istream)
        except OSError:
            self.auth = {}
        try:
            with open(self.data_file) as istream:
                self.data = json.load(istream)
        except OSError:
            self.data = {}

    def results(self):
        """
        Format the most recent response
        """
        scraping.LOGGER.info('Preparing results from The Guardian API...')
        articles = [
            {k: item.get(v) for k, v in ARTICLE_KEY_MAP.items()}
            for item in self.data.get('response').get('results')
        ]
        scraping.LOGGER.info('articles: %s', json.dumps(articles))
        return articles

    def request(self):
        """
        Request articles from The Guardian API
        """
        scraping.LOGGER.info('Requesting news from The Guardian...')
        params = {
            'format': 'json',
            'show-fields': 'byline,headline,standfirst,thumbnail,bodyText',
            'api-key': self.auth.get('api-key'),
            'from-date': self.data.get('timestamp'),
        }
        scraping.LOGGER.debug('Sending request to %s', self.api_url)
        resp = requests.get(self.api_url, params=params)
        scraping.LOGGER.info('Response status %d', resp.status_code)
        if 200 <= resp.status_code < 300:
            self.data = resp.json()
            self.data['timestamp'] = self.timestamp()
            with open(self.data_file, 'w') as ostream:
                json.dump(self.data, ostream)
            scraping.LOGGER.info('Wrote json to %s', self.data_file)
        return resp.status_code


if __name__ == '__main__':
    print(json.dumps(Client().request()))
