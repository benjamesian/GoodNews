"""Specify routes for all app views."""
from django.urls import path

from . import views

# pylint: disable=invalid-name
app_name = 'news'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('about/', views.about, name='about'),
    path('search/', views.search, name='search'),
    path('post_articles/', views.post_articles, name='post_articles'),
    path('<int:pk>/', views.ProfileView.as_view(), name='profile'),
]
