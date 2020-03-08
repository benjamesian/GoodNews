#!/usr/bin/env python3
"""
Provides tools to collect news articles from the web
"""
from scraping import theguardian

CLIENTS = {
    theguardian.client.Client
}
