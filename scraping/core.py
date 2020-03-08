#!/usr/bin/env python3
"""
Get articles from the web
"""
import json
import socket
import scraping


def main():
    """
    Run the program
    """
    # set up sockets
    for client in map(lambda cls: cls(), scraping.CLIENTS):
        if 200 <= client.request() < 300:
            data = client.serialize()
            # write to socket
