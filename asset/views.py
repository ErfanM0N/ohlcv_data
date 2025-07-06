from django.http import JsonResponse
from .models import Asset


def get_symbols_view(request):
    coins = list(Asset.objects.filter(enable=True).values_list('symbol', flat=True))
    return JsonResponse({'coins': coins})


def get_last_price_view(request):
    symbol = request.GET.get('symbol')
    if not symbol:
        return JsonResponse({'error': 'Symbol parameter is required'}, status=400)

    try:
        asset = Asset.objects.get(symbol=symbol, enable=True)
        last_price = asset.last_price
        updated = asset.updated.strftime('%Y-%m-%d %H:%M:%S') if asset.updated else None
        return JsonResponse({'symbol': symbol, 'last_price': last_price, 'updated': updated})
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found or disabled'}, status=404)
