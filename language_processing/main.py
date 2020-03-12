import json
from language_processing.ibmcloud.ibmcloud import get_sentiments
import logging
from multiprocessing import Pool
import os
import requests
import socket
from threading import Thread


URL_LOGIN = 'https://34.73.94.209/admin/'
URL_ENDPOINT = 'https://34.73.94.209/'

USERNAME = os.getenv('GOOD_NEWS_USERNAME')
PASSWORD = os.getenv('GOOD_NEWS_PASSWORD')


def add_articles(articles):
    """Post articles to api endpoint so that can be added to db."""
    with requests.Session() as session:
        session.get(URL_LOGIN)
        session.headers.update({
            'X-CSRFToken': session.cookies.get('csrftoken')
        })

        login_data = dict(username=USERNAME,
                          password=PASSWORD,
                          next='/')
        session.post(URL_LOGIN, data=login_data,
                     headers=dict(Referer=URL_LOGIN))
        session.headers.update({
            'content-type': 'application/json',
            'X-CSRFToken': session.cookies.get('csrftoken')
        })

        session.post(URL_ENDPOINT, data=json.dumps(articles))


def get_batch_sentiments(articles):
    """Process articles in parallel."""
    with Pool() as pool:
        return pool.map(get_sentiments, articles)


def process_articles(articles):
    article_titles = map(lambda x: x.get('title', ''), articles)
    raw_sentiments = get_batch_sentiments(article_titles)
    raw_sentiments = [
        sent.get('document_tone', {}).get('tones', [])
        for sent in raw_sentiments
    ]
    articles_data = {
        'articles': [
            {
                'article_data': article,
                'sentiments': [
                    {
                        'name': sentiment.get('tone_id'),
                        'magnitude': sentiment.get('score')
                    }
                    for sentiment in sentiments
                ]
            }
            for article, sentiments in zip(articles, raw_sentiments)]
    }
    add_articles(articles_data)

# old wsgi when considering gunicorn
# def application(environ, start_response):
#     """WSGI server application"""
#     content = json.load(environ['wsgi.input'])
#     articles = get_batch_sentiments(content.get('data'))
#     add_articles(articles, USERNAME, PASSWORD)

#     body = {'message': 'data posted'}
#     status = '200 OK'
#     headers = [('Content-Type', 'application/json'),
#                ('Content-Length', str(len(body)))]
#     start_response(status, headers)
#     return [json.dumps(body)]


# def recvall(connection: socket.socket, chunksize: int, json=False) -> bytes:
#     data = b''
#     while True:
#         recv_data = connection.recv(chunksize)
#         if not recv_data:
#             break
#         data += recv_data
#     return data

def add_length_header(data: bytes) -> bytes:
    length = str(len(data)).encode()
    header = (b'<length ' + length + b'>').ljust(32)
    return header + data


def consume_length_header(connection: socket.socket) -> int:
    raw_header = connection.recv(32)
    content_length = raw_header.strip(b'<length> ')
    return int(content_length)


def get_data(connection: socket.socket, chunksize: int = 4096) -> bytes:
    bytes_remaining = consume_length_header(connection)

    data = b''
    while bytes_remaining > chunksize:
        data += connection.recv(chunksize)
        bytes_remaining -= chunksize
    data += connection.recv(bytes_remaining)

    return data


def handle_connection(connection: socket.socket):
    data = b''
    resp = b'MSG'
    while True:
        try:
            data = get_data(connection, 4096)
        except Exception:
            resp += b'-ERECV'
            logging.exception('recv error', e)
        else:
            try:
                process_articles(json.loads(data.decode('utf-8')))
                resp += b'-OK'
            except json.JSONDecodeError:
                resp += b'-EJSON'
                logging.warning('bad json')
            except Exception as e:
                resp += b'-EUNKNOWN'
                logging.error('unknown error', e)
        finally:
            resp += b'-DONE'
            connection.sendall(add_length_header(resp))
            retry = connection.recv(4)
            if not retry:
                logging.warning('Client closed unexpectedly. data=\n{data}')
            elif retry == b'DONE':
                logging.debug('Client done sending messages.')
            elif retry == b'NEXT':
                continue
            else:
                logging.warning(f'Client send unexpected reply: {retry}')
            break
    connection.close()


if __name__ == "__main__":
    server_address = './uds_socket'

    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.bind(server_address)
        sock.listen(1)

        # while True:
        connection, client_address = sock.accept()
        print(f"accepted connection from {client_address}")
        handle_connection(connection)
        # ct = Thread(target=handle_connection, args=(connection,))
        # ct.start()
