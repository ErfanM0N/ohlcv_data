from django.db import 
from asset.models import Asset

class position(models.Model):
    SIDES = (('BUY', 'Buy'), ('SELL', 'Sell'))
    STATUS = (('OPEN', 'Open'), ('CLOSED', 'Closed'))

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=SIDES)
    quantity = models.FloatField()
    entry_price = models.FloatField()
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=6, choices=STATUS, default='OPEN')

    def __str__(self):
        return f"{self.asset.symbol} - {self.side} - {self.quantity} @ {self.entry_price}"


class order(models.Model):
    TYPES = (('TP', 'Take Profit'), ('SL', 'Stop Loss'))
    STATUS = (('PENDING', 'Pending'), ('FILLED', 'Filled'), ('CANCELED', 'Canceled'))

    position = models.ForeignKey('position', on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=2, choices=TYPES)
    price = models.FloatField()
    order_id = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=8, choices=STATUS, default='PENDING')
