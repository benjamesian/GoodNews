#!/usr/bin/env python3
"""Provides a User model"""
from django.db import models


class User(models.Model):
    """Definition of a User"""
    username = models.CharField(max_length=254, primary_key=True)
    password = models.CharField(max_length=254)
    email = models.EmailField(max_length=254)
    picture = models.ImageField(max_length=254)
