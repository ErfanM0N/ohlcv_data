from django.contrib import admin
from .models import DemoConfig, DemoPosition

@admin.register(DemoConfig)
class DemoConfigAdmin(admin.ModelAdmin):
    list_display = ('balance', 'available_balance','leverage', 'max_open_positions', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    search_fields = ('balance',)

@admin.register(DemoPosition)
class DemoPositionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'asset', 'side', 'quantity', 'entry_price', 'stop_loss', 'take_profit',
        'margin_balance', 'pnl', 'status', 'create_time', 'entry_time', 'exit_price', 'exit_time'
    )
    list_filter = ('side', 'status', 'asset')
    search_fields = ('asset__symbol', 'entry_price', 'exit_price')
    readonly_fields = ('create_time', 'entry_time', 'exit_time', 'pnl')
    ordering = ('-create_time',)
