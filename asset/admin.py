from django.contrib import admin
from asset.models import Asset
from ohlc.utils.init_candles import initialize_candles


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'enable', 'updated', 'last_price')
    list_editable = ('enable',)
    search_fields = ('symbol',)
    actions = ('refill_asset',)
    read_only_fields = ('last_price',)

    def save_model(self, request, obj: Asset, form, change):
        obj.symbol = obj.symbol.upper()
        obj.save()
        initialize_candles(obj)

    @admin.action(description="Refill asset")
    def refill_asset(self, request, queryset):
        for asset in queryset:
            initialize_candles(asset)
