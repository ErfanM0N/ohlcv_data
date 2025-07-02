from django.contrib import admin
from .models import Position, Order


class OrderInline(admin.TabularInline):  
    model = Order
    extra = 0  
    readonly_fields = ('order_id',)  
    fields = ('order_type', 'price', 'order_id', 'status')  


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('asset', 'side', 'quantity', 'order_id', 'entry_price', 'entry_time', 'exit_price', 'exit_time', 'leverage', 'pnl', 'status', 'trading_model')
    search_fields = ('asset__symbol', 'order_id')
    list_filter = ('side', 'status', 'asset__symbol', 'trading_model')
    ordering = ('-entry_time',)
    readonly_fields = ('pnl',)
    inlines = [OrderInline]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('position', 'order_type', 'price', 'order_id', 'status')
    search_fields = ('position__asset__symbol', 'order_id')
    list_filter = ('order_type', 'status')
    ordering = ('-position__entry_time',)

