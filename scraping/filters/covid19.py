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
    return [a for a in articles if not any(
        map(pat.search, filter(bool, a.values()))
    )]
