'''call language processing service and post results to site'''
import json
import logging
from multiprocessing import Pool
import os
import socket
import requests
from language_processing.ibmcloud.ibmcloud import get_sentiments

# ips = {
#     '801-web-01': '35.196.167.155',
#     '801-web-02': '34.73.252.236'
# }


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
        LOGGER.debug('posting %s', articles)
        session.post(URL_ENDPOINT, data=json.dumps(articles))


def get_batch_sentiments(articles):
    """Process articles in parallel."""
    with Pool() as pool:
        return pool.map(get_sentiments, articles)


def process_articles(articles):
    '''perform processing on multiple articles and get results'''
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
    '''add header indicating message length'''
    length = str(len(data)).encode()
    header = (b'<length ' + length + b'>').ljust(32)
    return header + data


def consume_length_header(connection: socket.socket) -> int:
    '''consume a length header and return length value'''
    raw_header = connection.recv(32)
    content_length = raw_header.strip(b'<length> ')
    if content_length.isdigit():
        return int(content_length)
    raise ValueError('bad header', raw_header)


def get_data(connection: socket.socket, length: int, chunksize: int = 4096) -> bytes:
    '''get data from a message with a length header'''
    data = b''
    while length > chunksize:
        data += connection.recv(chunksize)
        length -= chunksize
    data += connection.recv(length)

    return data


def handle_connection(connection: socket.socket):
    '''communicate with a scraper'''
    while True:
        data = b''
        resp = b'MSG'
        try:
            length = consume_length_header(connection)
            data = get_data(connection, length, 4096)
        except ValueError as ex:
            resp += '-EHEADER'
            LOGGER.exception('Bad value, likely length header %s', ex)
        except (ConnectionError, OSError) as err:
            resp += b'-ERECV'
            LOGGER.exception('recv error: %s', err)
        else:
            try:
                process_articles(json.loads(data.decode('utf-8')))
                resp += b'-OK'
            except json.JSONDecodeError:
                resp += b'-EJSON'
                LOGGER.warning('bad json')
            except (ConnectionError, OSError) as err:
                resp += b'-EUNKNOWN'
                LOGGER.error('unknown error: %s', err)

        resp += b'-DONE'
        connection.sendall(add_length_header(resp))
        retry = connection.recv(4)

        if not retry:
            LOGGER.warning('Client closed unexpectedly. data=\n%s', data)
        elif retry == b'DONE':
            LOGGER.debug('Client done sending messages.')
        elif retry in {b'NEXT', b'REDO'}:
            continue
        else:
            LOGGER.warning('Client send unexpected reply: %s', retry)
        break
    connection.close()


def main():
    '''listen for input from a socket'''
    server_address = './uds_socket'

    try:
        os.unlink(server_address)
    except OSError:
        if os.path.exists(server_address):
            raise

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.bind(server_address)
        sock.listen(1)

        while True:
            connection, client_address = sock.accept()
            LOGGER.debug("accepted connection from %s", client_address)
            handle_connection(connection)


if __name__ == "__main__":
    LOGGER = logging.getLogger(__name__)
    LOGGER.setLevel(10)
    LOGGER.debug('start language processing service')
    URL_ENDPOINT = '{}://{}'.format(
        os.getenv('GOOD_NEWS_API_SCHEMA', 'http'),
        os.getenv('GOOD_NEWS_API_HOST', 'localhost')
    )
    URL_LOGIN = '{}/admin'.format(URL_ENDPOINT)
    USERNAME = os.getenv('GOOD_NEWS_USERNAME')
    PASSWORD = os.getenv('GOOD_NEWS_PASSWORD')
    main()
    LOGGER.debug('lannguage processing service finished')
