#!/usr/bin/env python3
"""
Provide a filter to block articles related to COVID-19
"""
import re
from typing import List


def content_filter(articles: List[dict]) -> List[dict]:
    """
    Filters out articles relating to coronavirus
    """
    pat = re.compile(r'\b(corona.?virus|covid.?19)\b', flags=re.IGNORECASE)
    return list(filter(
        lambda article:
        dict(filter(
            any(lambda item: pat.search(item[0]) or pat.search(item[1])),
            article.items()
        )), articles
    ))
