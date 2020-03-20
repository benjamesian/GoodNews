"""Connect data and routes to relevant views."""
import json
from django.contrib.auth import authenticate
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.views import generic
from .models import Article, ArticleSentimentTag, Sentiment, User


class IndexView(generic.ListView):
    """Index view with recent Articles."""
    template_name = 'news/index.html'
    context_object_name = 'ranked_news_list'
    model = Article
    paginate_by = 25

    def get_queryset(self):
        """Return ranked articles for a user.

        articles are tagged with anger, fear, joy, sadness, analytical, confident, and tentative
        """
        sentiment = self.request.GET.get('q', 'all')
        articles = super().get_queryset().order_by('-created_at')
        if sentiment == 'all':
            negative_sentiments = Sentiment.objects.filter(name__in=['anger', 'fear', 'sadness'])
            ok_sentiments = Sentiment.objects.filter(name__in=['joy', 'analytical', 'confident', 'tentative'])
            articles = articles.filter(sentiments__in=ok_sentiments).exclude(sentiments__in=negative_sentiments)
        else:
            articles = articles.filter(sentiments__in=Sentiment.objects.filter(name=sentiment))
        return articles


def about(request: HttpRequest):
    '''landing page'''
    return render(request, 'news/about.html', {})


def search(request: HttpRequest):
    '''basic search functionality'''
    query: str = request.GET.get('q')
    query = query.lower()
    sentiments = {'anger', 'fear', 'joy', 'sadness', 'analytical', 'confident',
                  'tentative'}

    if query not in sentiments:
        return redirect('/')
    return Http404('bad search')


def post_articles(request: HttpRequest):
    """Post articles to the database."""
    try:
        with open('/data/current/backend/news/views.log', 'a') as ostream:
            print(request.META, file=ostream)
    except OSError:
        pass
    try:
        data = json.loads(request.body.decode('utf-8'))
        username = data['username']
        password = data['password']
        user = authenticate(request, username=username, password=password)
        if user is None or not user.is_staff:
            return JsonResponse({'message': 'only staff can add content'})
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
