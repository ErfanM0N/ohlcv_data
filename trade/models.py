from django.db import models
from asset.models import Asset

class Position(models.Model):
    SIDES = (('BUY', 'Buy'), ('SELL', 'Sell'))
    STATUSS = (('OPEN', 'Open'), ('CLOSED', 'Closed'))

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=SIDES)
    quantity = models.FloatField()
    order_id = models.CharField(max_length=32, unique=True)
    entry_price = models.FloatField()
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    exit_price = models.FloatField(null=True, blank=True)
    leverage = models.IntegerField(default=1)
    pnl = models.FloatField(default=0.0)
    status = models.CharField(max_length=6, choices=STATUSS, default='OPEN')
    trading_model = models.CharField(max_length=50, null=True, blank=True)
    telegram_message_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.asset.symbol} - {self.side} - {self.quantity} @ {self.order_id}"


class Order(models.Model):
    TYPES = (('TP', 'Take Profit'), ('SL', 'Stop Loss'))
    STATUSS = (('PENDING', 'Pending'), ('FILLED', 'Filled'), ('CANCELED', 'Canceled'))

    position = models.ForeignKey('position', on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=2, choices=TYPES)
    price = models.FloatField()
    order_id = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=8, choices=STATUSS, default='PENDING')

    def __str__(self):
        return f"{self.order_id}"
