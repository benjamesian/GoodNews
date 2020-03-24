"""Specify routes for all app views."""
from django.urls import path

from . import views

app_name = 'news'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('about/', views.about, name='about'),
    path('post_articles/', views.post_articles, name='post_articles'),
    path('<int:pk>/', views.ProfileView.as_view(), name='profile'),
]
