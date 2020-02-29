#!/usr/bin/env python3
"""Provides a Comment model"""
from django.db import models
from base.models.corpus import Corpus


class Comment(Corpus):
    """Definition of a sentiment tag"""
    content = models.CharField(max_length=510)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, editable=True)
    user = models.ForeignKey(
        'news.User', models.SET_NULL, blank=True, null=True)
    article = models.ForeignKey(
        'news.Article', models.SET_NULL, blank=True, null=True)
    parent = models.ForeignKey(
        'self', models.PROTECT, blank=True, null=True, related_name='replies')
