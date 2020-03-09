#!/usr/bin/env python3
"""
Provides a module to collect news from The Guardian
"""
import os
import pathlib

API = 'https://content.guardianapis.com'
AUTH_FILE = os.getenv(
    'GOOD_NEWS_THE_GUARDIAN_AUTH_FILE',
    str(pathlib.Path(__file__).parent.joinpath('auth.json'))
)
DATA_FILE = os.getenv(
    'GOOD_NEWS_THE_GUARDIAN_AUTH_FILE',
    str(pathlib.Path(__file__).parent.joinpath('data.json'))
)
