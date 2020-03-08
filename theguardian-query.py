#!/usr/bin/env python3
"""Request articles from the guardian API"""
import json
import requests

def theguardian_search(**kwargs):
    """Request articles from the guardian API"""
    response = requests.get('https://content.guardianapis.com/search',
    params={'api-key': '0af0f6db-d7c2-42ad-aae3-1a7dd85f3fc6'})
print(json.dumps(RESPONSE.json()))

if __name__ == '__main__':
    RESPONSE = requests.get(
        'https://content.guardianapis.com/search',
        params={'api-key': '0af0f6db-d7c2-42ad-aae3-1a7dd85f3fc6'})
    print(json.dumps(RESPONSE.json()))
