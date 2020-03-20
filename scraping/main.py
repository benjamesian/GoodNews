#!/usr/bin/env python3
"""
Get articles from the web
"""
import json
import os
import socket
import sys
import tempfile
from scraping import API_CLIENTS, SOCKET_PATH
from scraping.filters import CONTENT_FILTERS


def accept_status(status: bytes) -> bool:
    """
    Check if the server status is OK
    """
    if status == b'MSG-OK-DONE':
        return True

    if not status:
        raise InterruptedError('Server closed unexpectedly')

    if not status.startswith(b'MSG-'):
        print(f'Unexpected response start: {status}', sys.stderr)
    elif not status.endswith(b'-DONE'):
        print(f'Unexpected response finish: {status}', file=sys.stderr)
    else:
        print(f'Problematic response {status}', file=sys.stderr)

    return False


# def recvall(connection: socket.socket, chunksize: int) -> bytes:
#     data = b''
#     while True:
#         recv_data = connection.recv(chunksize)
#         if not recv_data:
#             break
#         data += recv_data
#     return data


def add_length_header(data: bytes) -> bytes:
    """
    Add padding to a packet
    """
    length = str(len(data)).encode()
    header = (b'<length ' + length + b'>').ljust(32)
    return header + data


def consume_length_header(connection: socket.socket) -> int:
    """
    Ingest a packet
    """
    raw_header = connection.recv(32)
    content_length = raw_header.strip(b'<length> ')
    return int(content_length)


def main():
    """
    Run the program
    """
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(SOCKET_PATH)
        for i, client in enumerate(cls() for cls in API_CLIENTS):
            if 200 <= client.request() < 300:
                filedesc, filename = tempfile.mkstemp(prefix=b'GoodNews')
                articles = client.results(filedesc)
                json.dump(articles, sys.stderr)
                try:
                    os.close(filedesc)
                except OSError:
                    pass

                # send_json = b''
                # try:
                #     send_json = json.dumps(articles).encode()
                # except json.JSONDecodeError:
                #     print(f'Got bad json from {client.name}\n{send_json}',
                #           file=sys.stderr)
                #     continue
                # send_data = add_length_header(send_json)
                send_data = add_length_header(filename)

                retries = 3
                while True:
                    sock.sendall(send_data)
                    status_length = consume_length_header(sock)
                    status = sock.recv(status_length)
                    retries -= 1
                    if accept_status(status) or retries <= 0:
                        break
                    sock.sendall(b'REDO')
                if retries == 0:
                    print(f'Max retries reached: data={filename}',
                          file=sys.stderr)
                if i < len(API_CLIENTS) - 1:
                    sock.sendall(b'NEXT')
                try:
                    os.remove(filename)
                except OSError:
                    pass
        sock.sendall(b'DONE')


if __name__ == '__main__':
    sys.exit(main())
