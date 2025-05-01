from django.contrib import admin
from ohlc.models import *


@admin.register(Candle15M)
class ModelNameAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume',)
    list_filter = ('symbol',)
    ordering = ('-timestamp',)

@admin.register(Candle1H)
class ModelNameAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume',)
    list_filter = ('symbol',)
    ordering = ('-timestamp',)

@admin.register(Candle4H)
class ModelNameAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume',)
    list_filter = ('symbol',)
    ordering = ('-timestamp',)
