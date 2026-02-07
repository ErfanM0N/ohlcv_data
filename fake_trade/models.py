from django.db import models
from asset.models import Asset


class DemoConfig(models.Model):
    balance = models.DecimalField(
        max_digits=20, decimal_places=2, default=10000.00,
        help_text="Starting balance for demo account"
    )
    available_balance = models.DecimalField(
        max_digits=20, decimal_places=2, default=10000.00,
        help_text="Balance available for opening new positions"
    )
    max_open_positions = models.PositiveIntegerField(
        default=5,
        help_text="Maximum number of open trades allowed"
    )
    leverage = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.0,
        help_text="Leverage multiplier for trades"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Demo Configuration"
        verbose_name_plural = "Demo Configurations"

    def __str__(self):
        return f"DemoConfig (Balance: {self.balance}, Leverage: {self.leverage}x)"


class DemoPosition(models.Model):
    SIDE_CHOICES = (
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        verbose_name="Asset",
        help_text="The financial asset being traded"
    )
    side = models.CharField(
        max_length=4,
        choices=SIDE_CHOICES,
        verbose_name="Trade Side",
        help_text="Whether this position is a Buy or Sell"
    )
    quantity = models.FloatField(
        verbose_name="Quantity",
        help_text="Number of units in the position"
    )
    entry_price = models.FloatField(
        verbose_name="Entry Price",
        help_text="Price at which the position was opened"
    )
    stop_loss = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Stop Loss",
        help_text="Price at which the position will be automatically closed to limit loss"
    )
    take_profit = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Take Profit",
        help_text="Price at which the position will be automatically closed to secure profit"
    )
    margin_balance = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0,
        verbose_name="Margin Balance",
        help_text="Amount of balance allocated for this position"
    )
    pnl = models.FloatField(
        default=0.0,
        verbose_name="Profit/Loss",
        help_text="Current profit or loss of this position"
    )
    status = models.CharField(
        max_length=8,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Status",
        help_text="Current status of the position"
    )
    telegram_message_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Telegram Message ID",
        help_text="Reference ID if this position was sent to Telegram"
    )
    commission = models.FloatField(
        default=0,
        verbose_name="Commission",
        help_text="Commission cost for this trade"
    )
    create_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Create Time"
    )
    entry_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Entry Time"
    )
    exit_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Exit Time"
    )
    exit_price = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Exit Price",
        help_text="Price at which the position was closed"
    )

    class Meta:
        verbose_name = "Demo Position"
        verbose_name_plural = "Demo Positions"
        ordering = ['-entry_time']

    def __str__(self):
        return f"{self.asset.symbol} ({self.side}) - Qty: {self.quantity} - Status: {self.status}"
