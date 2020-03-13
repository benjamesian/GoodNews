"""Provide App Models"""
from django.contrib.auth.models import User
from django.db import models


# https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#extending-the-existing-user-model
class Profile(models.Model):
    """Definition of a User Profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=100, null=True, blank=True)
    picture = models.ImageField(upload_to='uploads/', max_length=254)


class Sentiment(models.Model):
    """Representation of a sentiment"""
    name = models.CharField(max_length=30, null=False, primary_key=True)
    picture = models.ImageField(upload_to='icons/', blank=True, max_length=254)

    def __str__(self):
        """Return a string representing a sentiment"""
        return f"{self.name}"


class ArticleSentimentTag(models.Model):
    """Intermediate model for relating corpora to sentiments"""
    corpus = models.ForeignKey(
        'Article', on_delete=models.CASCADE,
        related_name='sentiment_tags',
        related_query_name='sentiment_tag'
    )
    sentiment = models.ForeignKey(
        Sentiment, on_delete=models.CASCADE,
        related_name='article_tags',
        related_query_name='article_tag'
    )
    magnitude = models.FloatField()

    def __str__(self):
        """Return a string representing a sentiment tag"""
        # return (f"A{self.corpus.id}-{self.sentiment.name}"
        #         f"-{self.magnitude} ({self.id})")


class Article(models.Model):
    """Representation of an article"""
    url = models.URLField(max_length=254, null=False, primary_key=True)
    title = models.CharField(default='(untitled)', max_length=254)
    author = models.CharField(max_length=254)
    created_at = models.DateTimeField(default=None)
    picture_url = models.URLField(blank=True)
    sentiments = models.ManyToManyField(Sentiment, through=ArticleSentimentTag)

    def __str__(self):
        """Return a string representing an article"""
        # return f"{self.title[:12]}... ({self.id})"


class CommentSentimentTag(models.Model):
    """Intermediate model for relating corpora to sentiments"""
    corpus = models.ForeignKey(
        'Comment', on_delete=models.CASCADE,
        related_name='sentiment_tags',
        related_query_name='sentiment_tag'
    )
    sentiment = models.ForeignKey(
        Sentiment, on_delete=models.CASCADE,
        related_name='comment_tags',
        related_query_name='comment_tag'
    )
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
