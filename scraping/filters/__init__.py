#!/usr/bin/env python3
"""
Provide filters to block bad news
"""
from . import covid19

CONTENT_FILTERS = [covid19.content_filter]
