#!/usr/bin/env python3
"""
Provides tools to collect news articles from the web
"""
import os
import logging
import logging.handlers
from scraping import theguardian

LOGGER = logging.getLogger(__name__)
SYSLOG_HANDLER = logging.handlers.SysLogHandler(address='/dev/log')
SYSLOG_HANDLER.setLevel(logging.INFO)

API_CLIENTS = [theguardian.client.Client]
SOCKET_PATH = './uds_socket'
