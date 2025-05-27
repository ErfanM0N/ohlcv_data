from django.db import models
from django.contrib.postgres.indexes import BrinIndex
from decimal import Decimal
from asset.models import Asset


class Candle15M(models.Model):
    """Base model for 15-minute OHLC candles"""
    symbol = models.ForeignKey(Asset, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        unique_together = ('symbol', 'timestamp')
        indexes = [
            models.Index(fields=['symbol']),
            BrinIndex(fields=['timestamp'], pages_per_range=128),
        ]


class Candle1H(models.Model):
    """Model for 1-hour OHLC candles"""
    symbol = models.ForeignKey(Asset, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        unique_together = ('symbol', 'timestamp')
        indexes = [
            models.Index(fields=['symbol']),
            BrinIndex(fields=['timestamp'], pages_per_range=128),
        ]


class Candle4H(models.Model):
    """Model for 4-hour OHLC candles"""
    symbol = models.ForeignKey(Asset, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        unique_together = ('symbol', 'timestamp')
        indexes = [
            models.Index(fields=['symbol']),
            BrinIndex(fields=['timestamp'], pages_per_range=128),
        ]


class Candle1D(models.Model):
    """Model for 1-day OHLC candles"""
    symbol = models.ForeignKey(Asset, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        unique_together = ('symbol', 'timestamp')
        indexes = [
            models.Index(fields=['symbol']),
            BrinIndex(fields=['timestamp'], pages_per_range=128),
        ]