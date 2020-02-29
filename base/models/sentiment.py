#!/usr/bin/env python3
"""Provides a Sentiment model"""
from django.db import models


class Sentiment(models.Model):
    """Representation of a sentiment"""
    name = models.CharField(max_length=30, null=False, primary_key=True)
