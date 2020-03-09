#!/usr/bin/env python3
"""
Get articles from the web
"""
import sys
from scraping.main import main  # pylint: disable=import-self

if __name__ == '__main__':
    sys.exit(main())
