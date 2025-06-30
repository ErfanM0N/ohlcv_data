from django.db import models


class Asset(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    enable = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    last_price = models.FloatField(default=0.0)

    def __str__(self):
        return self.symbol
