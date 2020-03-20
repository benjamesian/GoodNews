#!/usr/bin/env python3
"""
Provides a client to request articles from the Guardian API
"""
import json
import os
import string
import requests
import scraping
from scraping import base
from scraping.filters import CONTENT_FILTERS


class Client(base.Client):  # pylint: disable=too-few-public-methods
    """
    Definition of a class to retrieve news from The Guardian
    """
    name = 'TheGuardian'
    url = 'https://content.guardianapis.com'
    auth_file = os.getenv(
        'GOOD_NEWS_THE_GUARDIAN_AUTH_FILE',
        os.path.join(os.path.dirname(__file__), 'auth.json')
    )
    data_file = os.getenv(
        'GOOD_NEWS_THE_GUARDIAN_AUTH_FILE',
        os.path.join(os.path.dirname(__file__), 'data.json')
    )

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

    def results(self, file=None):
        """
        Format the most recent response
        """
        scraping.LOGGER.info('Formatting results from The Guardian...')
        articles = [{
            'url': item.get('webUrl'),
            'title': item.get('webTitle'),
            'created_at': item.get('webPublicationDate'),
            'author': item.get('fields', {}).get('byline'),
            'picture_url': item.get('fields', {}).get('thumbnail'),
            'body': ''.join(filter(
                lambda c: c in string.printable,
                item.get('fields', {}).get('bodyText', [])
            ))
        } for item in self.data.get('response', {}).get('results', [])]
        for content_filter in CONTENT_FILTERS:
            articles = content_filter(articles)
        self.dump(articles, file)
        return articles
