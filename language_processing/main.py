'''call language processing service and post results to site'''
from itertools import tee, filterfalse
import json
import logging
import logging.handlers
from multiprocessing import Pool
import os
import socket
import requests
from language_processing.ibmcloud.ibmcloud import get_sentiments

# ips = {
#     '801-web-01': '35.196.167.155',
#     '801-web-02': '34.73.252.236'
# }

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
HANDLER = logging.handlers.SysLogHandler(address='/dev/log')
HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(HANDLER)
# HANDLER = logging.FileHandler('lang.log')
# HANDLER.setLevel(logging.DEBUG)
# LOGGER.addHandler(HANDLER)

URL_BASE = '{}://{}'.format(
    os.getenv('GOOD_NEWS_API_SCHEMA', 'http'),
    os.getenv('GOOD_NEWS_API_HOST', 'localhost')
)
URL_ENDPOINT = '{}/post_articles/'.format(URL_BASE)
URL_LOGIN = '{}/admin/'.format(URL_BASE)
USERNAME = os.getenv('GOOD_NEWS_USERNAME')
PASSWORD = os.getenv('GOOD_NEWS_PASSWORD')


def add_articles(articles):
    """Post articles to api endpoint so that can be added to db."""
    with requests.Session() as session:
        LOGGER.debug('grabbing csrf token from %s', URL_LOGIN)
        session.get(URL_LOGIN)

        # params = dict(username=USERNAME, password=PASSWORD)
        # LOGGER.debug('posting login data to %s', URL_LOGIN)
        # session.post(URL_LOGIN, params=params,
        #              headers=dict(Referer=URL_LOGIN))

        data = articles
        data['username'] = USERNAME
        data['password'] = PASSWORD

        session.headers.update({
            'content-type': 'application/json',
            'X-CSRFToken': session.cookies.get('csrftoken')
        })
        LOGGER.debug('posting articles: %s to: %s', data, URL_ENDPOINT)
        resp = session.post(URL_ENDPOINT, data=json.dumps(data))
        LOGGER.info('server responded with: %s', resp.status_code)
        LOGGER.debug('response headers: {%s}',
                     ', '.join(map(': '.join, resp.headers.items())))


def get_batch_sentiments(articles):
    """Process articles in parallel."""
    with Pool() as pool:
        return pool.map(get_sentiments, articles)


def process_articles(articles):
    '''perform processing on multiple articles and get results'''
    article_text = (
        f"<h1>{article.get('title', '')}</h1>{article.get('body', '')}"
        for article in articles)
    raw_sentiments = get_batch_sentiments(article_text)
    raw_sentiments = [
        sent.get('document_tone', {}).get('tones', [])
        for sent in raw_sentiments
    ]
    iter1, iter2 = tee(zip(articles, raw_sentiments))
    with_sentiments = filter(lambda x: x[1], iter1)
    without_sentiments = filterfalse(lambda x: x[1], iter2)
    article_keys = {'url', 'title', 'author', 'created_at', 'picture_url'}
    articles_data = {
        'articles': [
            {
                'article_data': {
                    k: v for k, v in article.items() if k in article_keys
                },
                'sentiments': [
                    {
                        'name': sentiment.get('tone_id'),
                        'magnitude': sentiment.get('score')
                    }
                    for sentiment in sentiments
                ]
            }
            for article, sentiments in with_sentiments]
    }
    if articles_data['articles']:
        add_articles(articles_data)
    else:
        LOGGER.warning('None of the articles had sentiments!')

    for art in without_sentiments:
        LOGGER.debug('article had no sentiments: %s', art)


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
                LOGGER.warning('bad json %s', data.decode())
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
    LOGGER.info('start language processing service')
    main()
    LOGGER.warning('language processing service finished')
