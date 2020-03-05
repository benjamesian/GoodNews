"""Register models to be viewed on the admin site."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Article, ArticleSentimentTag, Comment, Profile, Sentiment


class ProfileInline(admin.StackedInline):
    """Expose Profile attributes for admin view."""
    model = Profile


class UserAdmin(BaseUserAdmin):
    """Add Profile attributes to associated User admin view."""
    inlines = (ProfileInline,)


admin.site.register(Article)
admin.site.register(ArticleSentimentTag)
admin.site.register(Comment)
admin.site.register(Sentiment)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
