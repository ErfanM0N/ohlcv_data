from django.contrib import admin
from django.utils.html import format_html
from .models import NewsArticle


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title_short',
        'source_id',
        'sentiment_colored',
        'published_on',
        'category_count',
        'keyword_count',
    )
    
    list_filter = (
        'sentiment',
        'source_id',
        'published_on',
        'created_at',
    )
    
    search_fields = (
        'title',
        'body',
        'keywords',
        'categories',
    )
    
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'url', 'source_id')
        }),
        ('Content', {
            'fields': ('body', 'published_on')
        }),
        ('Classification', {
            'fields': ('sentiment', 'keywords', 'categories')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'published_on'
    list_per_page = 100
    ordering = ('-published_on',)
    
    def title_short(self, obj):
        """Display shortened title"""
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    def category_count(self, obj):
        """Display number of categories"""
        return len(obj.categories) if obj.categories else 0
    category_count.short_description = 'Categories'
    
    def keyword_count(self, obj):
        """Display number of keywords"""
        return len(obj.keywords) if obj.keywords else 0
    keyword_count.short_description = 'Keywords'
    
    def sentiment_colored(self, obj):
        """Display sentiment with color coding"""
        colors = {
            'POSITIVE': 'green',
            'NEGATIVE': 'red',
            'NEUTRAL': 'gray',
        }
        color = colors.get(obj.sentiment, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.sentiment
        )
    sentiment_colored.short_description = 'Sentiment'