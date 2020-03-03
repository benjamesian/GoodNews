from django.shortcuts import render
from django.views import generic

from .models import Article, User


class IndexView(generic.ListView):
    template_name = 'news/index.html'
    context_object_name = 'ranked_news_list'

    def get_queryset(self):
        """Return ranked articles for a user."""
        return Article.objects.order_by('-created_at')[:10]


class ProfileView(generic.DetailView):
    model = User
    template_name = 'news/profile.html'
    context_object_name = 'user_profile'
