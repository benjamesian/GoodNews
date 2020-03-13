"""Connect data and routes to relevant views."""
from django.http import HttpRequest, JsonResponse
from django.views import generic
import json
from .models import Article, ArticleSentimentTag, Sentiment, User


class IndexView(generic.ListView):
    """Index view with recent Articles."""
    template_name = 'news/index.html'
    context_object_name = 'ranked_news_list'
    model = Article

    def get_queryset(self):
        """Return ranked articles for a user."""
        articles = super().get_queryset().order_by('-created_at')[:10]
        return articles

    def post(self, request, *args, **kwargs):
        """Post articles to the database."""
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            return JsonResponse({'error': 'bad json'}, 400)
        articles = data.get('articles', [])
        for article in articles:
            new_article = Article(**article.get('article_data', {}))
            new_article.save()
            sentiments = article.get('sentiments', [])
            for sentiment_data in sentiments:
                sentiment = Sentiment(name=sentiment_data.get('name'))
                sentiment.save()
                tag = ArticleSentimentTag(
                    corpus=new_article,
                    sentiment=sentiment,
                    magnitude=sentiment_data.get('magnitude')
                )
                tag.save()
        return JsonResponse({'message': 'added content to db'})


class ProfileView(generic.DetailView):
    """View of a User's Profile."""
    model = User
    template_name = 'news/profile.html'
    context_object_name = 'user_profile'
