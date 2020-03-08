#!/usr/bin/env python3
"""
Provides a base class for scrapers and API clients to inherit from
"""
from abc import ABC, abstractmethod
from datetime import datetime


class Client(ABC):  # pylint: disable=too-few-public-methods
    """
    Definition of a class to retrieve news from The Guardian
    """
    @abstractmethod
    def results(self):
        """
        Format the most recent response
        """

    @abstractmethod
    def request(self):
        """
        Submit a query to the specified endpoint
        """

    @staticmethod
    def timestamp():
        """
        Get an ISO-8601 timestamp
        """
        return datetime.utcnow().isoformat()
