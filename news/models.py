from django.db import models
from django.contrib.postgres.fields import ArrayField


class NewsArticle(models.Model):
    SENTIMENT_CHOICES = [
        ('POSITIVE', 'Positive'),
        ('NEGATIVE', 'Negative'),
        ('NEUTRAL', 'Neutral'),
    ]
    
    id = models.BigIntegerField(primary_key=True)
    published_on = models.DateTimeField()
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000)
    source_id = models.IntegerField()
    body = models.TextField()
    
    keywords = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list
    )
    
    sentiment = models.CharField(
        max_length=10,
        choices=SENTIMENT_CHOICES,
        default='NEUTRAL'
    )
    
    categories = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-published_on']
        indexes = [
            models.Index(fields=['-published_on']),
            models.Index(fields=['source_id']),
            models.Index(fields=['sentiment']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.id})"