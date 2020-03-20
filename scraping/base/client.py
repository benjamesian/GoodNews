#!/usr/bin/env python3
"""
Provides a base class for scrapers and API clients to inherit from
"""
from abc import ABC, abstractmethod
from datetime import datetime
from io import IOBase as IO
from json import dump
from os import fdopen
from typing import List, Union
import scraping


class Client(ABC):  # pylint: disable=too-few-public-methods
    """
    Definition of a class to retrieve news from a news source
    """
    name: str = None
    url: str = None

    @abstractmethod
    def request(self, endpoint: str = None) -> int:
        """
        Submit a query to the specified endpoint
        """

    @abstractmethod
    def results(self, file: Union[bytes, int, str, IO] = None) -> List[dict]:
        """
        Get the results of the most recent request
        """

    @staticmethod
    def dump(data, file: Union[bytes, int, str, IO] = None) -> None:
        """
        Dump JSON to a file
        """
        if isinstance(file, (bytes, str)):
            with open(file, 'w') as ostream:
                scraping.LOGGER.info('Writing JSON to %s', ostream.name)
                dump(data, ostream)
        elif isinstance(file, int):
            with fdopen(file, 'w') as ostream:
                scraping.LOGGER.info('Writing JSON to %s', ostream.name)
                dump(data, ostream)
        elif isinstance(file, IO):
            with fdopen(file.fileno, 'w') as ostream:
                scraping.LOGGER.info('Writing JSON to %s', ostream.name)
                dump(data, ostream)
        else:
            raise TypeError(f"'file' must be of type 'str', 'int' or 'IOBase'")

    @staticmethod
    def timestamp() -> str:
        """
        Get an ISO-8601 timestamp
        """
        return datetime.utcnow().isoformat()
