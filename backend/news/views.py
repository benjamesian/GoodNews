from django.shortcuts import render
from django.views import generic
# Create your views here.


class IndexView(generic.ListView):
    template_name = 'news/index.html'
    context_object_name = 'ranked_news_list'

    def get_queryset(self):
        """Return ranked articles for a user."""
        return []
