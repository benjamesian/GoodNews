#!/usr/bin/env python3
"""
Provides a base class for scrapers and API clients to inherit from
"""
from abc import ABC, abstractmethod
from datetime import datetime
from io import IOBase as IO
import json
import os
import sys
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
    def dump(data, file: Union[bytes, int, str, IO]) -> None:
        """
        Dump JSON to a file
        """
        if file is None:
            ostream = sys.stdout
        elif isinstance(file, (bytes, str)):
            ostream = open(file, 'w')
        elif isinstance(file, int):
            ostream = os.fdopen(file, 'w')
        elif isinstance(file, IO):
            ostream = os.fdopen(file.fileno, 'w')
        else:
            raise TypeError("'file' must be 'bytes', 'str', 'int' or 'IOBase'")
        try:
            scraping.LOGGER.info('Writing JSON dump to %s', ostream.name)
            json.dump(data, ostream)
        finally:
            ostream.close()

    @staticmethod
    def timestamp() -> str:
        """
        Get an ISO-8601 timestamp
        """
        return datetime.utcnow().isoformat()
