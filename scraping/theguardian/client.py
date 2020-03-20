#!/usr/bin/env python3
"""
Provides a client to request articles from the Guardian API
"""
import json
import string
import requests
import scraping
from scraping.base.client import Client as BaseClient
from scraping.theguardian import URL, AUTH_FILE, DATA_FILE


class Client(BaseClient):  # pylint: disable=too-few-public-methods
    """
    Definition of a class to retrieve news from The Guardian
    """
    name = 'TheGuardian'
    url = URL
    auth_file = AUTH_FILE
    data_file = DATA_FILE

    # pylint: disable=super-init-not-called
    def __init__(self, auth_file: str = None, data_file: str = None):
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

    def results(self, filename: str = None):
        """
        Format the most recent response
        """
        scraping.LOGGER.info('Preparing results from The Guardian...')
        articles = [{
            'url': item.get('webUrl'),
            'title': item.get('webTitle'),
            'created_at': item.get('webPublicationDate'),
            'author': item.get('fields', {}).get('byline'),
            'picture_url': item.get('fields', {}).get('thumbnail'),
            'body': ''.join(filter(
                lambda c: 32 <= ord(c) < 127,
                item.get('fields', {}).get('bodyText', [])
            ))
        } for item in self.data.get('response', {}).get('results', [])]
        if filename is not None:
            scraping.LOGGER.debug(json.dumps(articles))
            scraping.LOGGER.info('Writing article JSON to %s', filename)
            with open(filename, 'w') as ostream:
                json.dump(articles, ostream)
        return articles

    def request(self, endpoint: str = 'search'):
        """
        Request articles from The Guardian API
        """
        scraping.LOGGER.info('Requesting articles from The Guardian...')
        params = {
            'format': 'json',
            'show-fields': 'byline,headline,standfirst,thumbnail,bodyText',
            'api-key': self.auth.get('api-key'),
            'from-date': self.data.get('timestamp'),
        }
        url = self.url if endpoint is None else '/'.join((self.url, endpoint))
        scraping.LOGGER.debug('Sending request to %s', url)
        resp = requests.get(url, params=params)
        if 200 <= resp.status_code < 300:
            scraping.LOGGER.info('Response status %d', resp.status_code)
            self.data = resp.json()
            self.data['timestamp'] = self.timestamp()
            scraping.LOGGER.info('Writing response JSON to %s', self.data_file)
            with open(self.data_file, 'w') as ostream:
                json.dump(self.data, ostream)
        else:
            scraping.LOGGER.warning('Response status %d', resp.status_code)
        return resp.status_code
