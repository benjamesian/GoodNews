#!/usr/bin/env python3
"""
Provides tools to collect news articles from the web
"""
from scraping.theguardian.client import Client as TheGuardianClient
from scraping.core.main import main

API_CLIENTS = [TheGuardianClient]
SOCKET_PATH = './uds_socket'
