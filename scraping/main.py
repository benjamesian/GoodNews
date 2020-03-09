#!/usr/bin/env python3
"""
Get articles from the web
"""
import json
import socket
import sys
import scraping


def main():
    """
    Run the program
    """
    for client in (cls() for cls in scraping.API_CLIENTS):
        if 200 <= client.request() < 300:
            articles = client.results()
            print(articles, file=sys.stderr)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(scraping.SOCKET_PATH)
                sock.sendall(json.dumps(articles).encode())


if __name__ == '__main__':
    sys.exit(main())
