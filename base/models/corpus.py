#!/usr/bin/env python3
"""Provides a Corpus abstract model from which other classes should derive"""
from django.db import models
from base.models.sentiment import Sentiment


class Corpus(models.Model):
    """Base class for representations of text with sentiment data"""
    sentiments = models.ManyToManyField(Sentiment, through='SentimentTag')

    class Meta:
        """Define Corpus as an abstract class"""
        abstract = True


class SentimentTag(models.Model):
    """Intermediate model for relating corpora to sentiments"""
    magnitude = models.FloatField()
    sentiment = models.ForeignKey(Sentiment, on_delete=models.CASCADE)
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE)
