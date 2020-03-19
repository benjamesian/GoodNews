#!/usr/bin/env python3
"""
Provides a base class for scrapers and API clients to inherit from
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


class Client(ABC):  # pylint: disable=too-few-public-methods
    """
    Definition of a class to retrieve news from a news source
    """
    name: str = None
    url: str = None

    @abstractmethod
    def results(self, filename: str = None) -> List[dict]:
        """
        Format the most recent response
        """

    @abstractmethod
    def request(self, endpoint: str = None) -> int:
        """
        Submit a query to the specified endpoint
        """

    @staticmethod
    def timestamp() -> str:
        """
        Get an ISO-8601 timestamp
        """
        return datetime.utcnow().isoformat()
