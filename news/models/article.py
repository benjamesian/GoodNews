#!/usr/bin/env python3
"""Provides an Article model"""
from django.db import models
from base.models.corpus import Corpus


class Article(Corpus):
    """Representation of an article"""
    url = models.URLField(max_length=254)
    author = models.CharField(max_length=254)
    created_at = models.DateTimeField(default=None)
