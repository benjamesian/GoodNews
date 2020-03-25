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


def post_articles(articles):
    """Post articles to api endpoint so that can be added to db."""
    with requests.Session() as session:
        LOGGER.debug('grabbing csrf token from %s', URL_LOGIN)

        session.get(URL_LOGIN)
        session.headers.update({
            'content-type': 'application/json',
            'X-CSRFToken': session.cookies.get('csrftoken')
        })

        data = articles

        # only staff members can post content to the site
        data['username'] = USERNAME
        data['password'] = PASSWORD

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
    """
    Tag articles with sentiments and format resulting data so it can be posted
    to the site.
    """
    article_text = ('\n'.join((
        '<h1>', article.get('title', ''), '</h1>', article.get('body', '')
    )) for article in articles)
    raw_sentiments = get_batch_sentiments(article_text)
    raw_sentiments = [
        sent.get('document_tone', {}).get('tones', [])
        for sent in raw_sentiments
    ]

    iter1, iter2 = tee(zip(articles, raw_sentiments))
    with_sentiments = filter(lambda x: x[1], iter1)
    without_sentiments = filterfalse(lambda x: x[1], iter2)

    article_keys = {'url', 'title', 'author', 'created_at', 'picture_url'}
    processed_articles = {
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

    return {
        'processed': processed_articles,
        'without_sentiments': without_sentiments
    }


def handle_processed_articles(data):
    """Post articles that have been tagged with sentiments to the site.

    Warn about articles that were'nt tagged with sentiments or if no articles
    will be posted.
    """
    try:
        if data['processed'].get('articles'):
            post_articles(data['processed'])
        else:
            LOGGER.warning('None of the articles had sentiments!')
    except KeyError:
        LOGGER.warning('Data has no key "processed"')

    try:
        for article in data['without_sentiments']:
            LOGGER.debug('article had no sentiments: %s', article)
    except KeyError:
        LOGGER.info('Data has no key "without_sentiments"')


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


def get_data(conn: socket.socket, length: int, chunksize: int = 4096) -> bytes:
    '''get data from a message with a length header'''
    data = b''
    while length > chunksize:
        data += conn.recv(chunksize)
        length -= chunksize
    data += conn.recv(length)

    return data


def handle_connection(connection: socket.socket):
    '''communicate with a scraper'''
    while True:
        received_filename = b''
        response = b'MSG'
        try:
            length = consume_length_header(connection)
            received_filename = get_data(connection, length, 4096)
        except ValueError as ex:
            response += '-EHEADER'
            LOGGER.exception('Bad value, likely length header %s', ex)
        except (ConnectionError, OSError) as err:
            response += b'-ERECV'
            LOGGER.exception('recv error: %s', err)
        else:
            try:
                with open(received_filename, 'r') as istream:
                    received_filename = process_articles(json.load(istream))
                    handle_processed_articles(received_filename)
                response += b'-OK'
            except json.JSONDecodeError:
                response += b'-EJSON'
                LOGGER.warning('Bad JSON')
            except FileNotFoundError:
                response += b'-EFILE'
                LOGGER.error('No such file: %s', received_filename.decode())
            except PermissionError:
                response += b'-EPERM'
                LOGGER.error('Permission denied: %s', received_filename.decode())
            except (ConnectionError, OSError) as err:
                response += b'-EUNKNOWN'
                LOGGER.error('Error: %s', err)

        response += b'-DONE'
        connection.sendall(add_length_header(response))
        retry = connection.recv(4)

        if not retry:
            LOGGER.warning('Client closed unexpectedly. data=\n%s', received_filename)
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

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(server_address)
        server.listen(1)

        while True:
            connection, client_address = server.accept()
            LOGGER.debug("accepted connection from %s", client_address)
            handle_connection(connection)


if __name__ == "__main__":
    LOGGER.info('start language processing service')
    main()
    LOGGER.warning('language processing service finished')
