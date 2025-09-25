from django.contrib import admin
from .models import Position, Order, BalanceRecord, OneWayPosition


class OrderInline(admin.TabularInline):  
    model = Order
    extra = 0
    readonly_fields = ('order_id',)
    fields = ('order_type', 'price', 'order_id', 'status', 'commission')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('id', 'asset', 'side', 'quantity', 'order_id', 'entry_price', 'entry_time', 'exit_price', 'exit_time', 'leverage',
                     'pnl', 'status', 'probability', 'trading_model', 'commission', 'order_commission', 'telegram_message_id')
    search_fields = ('asset__symbol', 'order_id')
    list_filter = ('side', 'status', 'asset__symbol', 'trading_model')
    ordering = ('-entry_time',)
    inlines = [OrderInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('position', 'order_type', 'price', 'order_id', 'status', 'commission')
    search_fields = ('position__asset__symbol', 'order_id')
    list_filter = ('order_type', 'status')
    ordering = ('-position__entry_time',)


@admin.register(BalanceRecord)
class BalanceRecordAdmin(admin.ModelAdmin):
    list_display = ('total_balance', 'trade_pocket_balance', 'unrealized_pnl', 'unrealized_trade_balance', 'timestamp')
    search_fields = ('total_balance', 'trade_pocket_balance')
    ordering = ('-timestamp',)
    readonly_fields = ('total_balance', 'trade_pocket_balance', 'unrealized_pnl', 'unrealized_trade_balance')


@admin.register(OneWayPosition)
class OneWayPositionAdmin(admin.ModelAdmin):
    list_display = ('id', 'asset', 'side', 'quantity', 'order_id', 'entry_price', 'entry_time', 'leverage', 'trading_model', 'probability', 'telegram_message_id')
    search_fields = ('asset__symbol', 'order_id')
    list_filter = ('side', 'asset__symbol', 'trading_model')
    ordering = ('-entry_time',)
    readonly_fields = ('order_id',)
