from django.contrib.auth.models import User
from django.db import models


# https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#extending-the-existing-user-model
class Profile(models.Model):
    """Definition of a User Profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture = models.ImageField(max_length=254)


class Sentiment(models.Model):
    """Representation of a sentiment"""
    name = models.CharField(max_length=30, null=False, primary_key=True)


class Corpus(models.Model):
    """Base class for representations of text with sentiment data"""
    sentiments = models.ManyToManyField(Sentiment, through='SentimentTag')

    class Meta:
        """Define Corpus as an abstract class"""
        abstract = True


class Article(Corpus):
    """Representation of an article"""
    url = models.URLField(max_length=254)
    author = models.CharField(max_length=254)
    created_at = models.DateTimeField(default=None)


class Comment(Corpus):
    """Definition of a sentiment tag"""
    content = models.CharField(max_length=510)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, editable=True)
    user = models.ForeignKey(
        User, models.SET_NULL, blank=True, null=True)
    article = models.ForeignKey(
        Article, models.SET_NULL, blank=True, null=True)
    parent = models.ForeignKey(
        'self', models.PROTECT, blank=True, null=True, related_name='replies')


class SentimentTag(models.Model):
    """Intermediate model for relating corpora to sentiments"""
    magnitude = models.FloatField()
    sentiment = models.ForeignKey(Sentiment, on_delete=models.CASCADE)
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE)
