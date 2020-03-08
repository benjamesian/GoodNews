#!/usr/bin/env python3
"""
Provides a client to request articles from the Guardian API
"""
from datetime import datetime
import json
import pathlib
import requests
from scraping import theguardian


class Client:  # pylint: disable=too-few-public-methods
    """
    Definition of a class to retrieve news from The Guardian
    """
    auth_file = pathlib.Path(__file__).parent.joinpath('auth.json')
    resp_file = pathlib.Path(__file__).parent.joinpath('resp.json')

    def __init__(self, auth_file=None, resp_file=None):
        """
        Instantiate a Guardian API client with credentials
        """
        if auth_file:
            self.auth_file = auth_file
        if resp_file:
            self.resp_file = resp_file
        try:
            with open(self.auth_file) as istream:
                self.auth = json.load(istream)
        except OSError:
            self.auth = {}
        try:
            with open(self.resp_file) as istream:
                self.resp = json.load(istream)
        except OSError:
            self.resp = {}

    def serialize(self):
        """
        Format the most recent response
        """

    def request(self, endpoint='search'):
        """
        Request articles from The Guardian API
        """
        params = {
            'format': 'json',
            'show-fields': 'headline,standfirst,thumbnail,body',
            'api-key': self.auth.get('api-key'),
            'from-date': self.resp.get('timestamp')
        }
        url = '/'.join([theguardian.API, endpoint])
        resp = requests.get(url, params=params)
        self.resp = {**resp.json(), 'timestamp': datetime.utcnow().isoformat()}
        with open(self.resp_file, 'w') as ostream:
            json.dump(self.resp, ostream)
        return resp.status_code


if __name__ == '__main__':
    print(json.dumps(Client().request()))
