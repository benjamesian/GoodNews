from django.contrib.auth.models import User
from django.db import models


# https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#extending-the-existing-user-model
class Profile(models.Model):
    """Definition of a User Profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    picture = models.ImageField(upload_to='uploads/', max_length=254)


class Sentiment(models.Model):
    """Representation of a sentiment"""
    name = models.CharField(max_length=30, null=False, primary_key=True)


class ArticleSentimentTag(models.Model):
    """Intermediate model for relating corpora to sentiments"""
    corpus = models.ForeignKey('Article', on_delete=models.CASCADE)
    sentiment = models.ForeignKey(Sentiment, on_delete=models.CASCADE)
    magnitude = models.FloatField()


class Article(models.Model):
    """Representation of an article"""
    url = models.URLField(max_length=254)
    title = models.CharField(default='Article Title', max_length=254)
    author = models.CharField(max_length=254)
    created_at = models.DateTimeField(default=None)
    picture = models.ImageField(null=True, upload_to='articles_images/', max_length=254)
    sentiments = models.ManyToManyField(Sentiment, through=ArticleSentimentTag)


class CommentSentimentTag(models.Model):
    """Intermediate model for relating corpora to sentiments"""
    corpus = models.ForeignKey('Comment', on_delete=models.CASCADE)
    sentiment = models.ForeignKey(Sentiment, on_delete=models.CASCADE)
    magnitude = models.FloatField()


class Comment(models.Model):
    """Representation of a comment"""
    content = models.CharField(max_length=510)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, editable=True)
    user = models.ForeignKey(
        User, models.SET_NULL, blank=True, null=True)
    article = models.ForeignKey(
        Article, models.SET_NULL, blank=True, null=True)
    parent = models.ForeignKey(
        'self', models.PROTECT, blank=True, null=True, related_name='replies')
    sentiments = models.ManyToManyField(Sentiment, through=CommentSentimentTag)
