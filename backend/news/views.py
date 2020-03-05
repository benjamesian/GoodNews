"""Connect data and routes to relevant views."""
from django.views import generic
from .models import Article, User


class IndexView(generic.ListView):
    """Index view with recent Articles."""
    template_name = 'news/index.html'
    context_object_name = 'ranked_news_list'
    model = Article

    def get_queryset(self):
        """Return ranked articles for a user."""
        articles = super().get_queryset().order_by('-created_at')[:10]
        return articles
        # return articles.annotate(
        #     sentiment_tags=[article.sentiments.through.objects.filter(corpus__id=article.id)
        #                     for article in articles])


class ProfileView(generic.DetailView):
    """View of a User's Profile."""
    model = User
    template_name = 'news/profile.html'
    context_object_name = 'user_profile'
