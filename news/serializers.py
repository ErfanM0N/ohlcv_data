from rest_framework import serializers
from .models import NewsArticle


class NewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = [
            'id',
            'published_on',
            'title',
            'url',
            'source_id',
            'body',
            'keywords',
            'sentiment',
            'categories',
            'created_at',
        ]