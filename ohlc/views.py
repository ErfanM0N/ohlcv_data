from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from .models import Candle1D, Candle4H, Candle1H, Candle15M, Asset


def get_1d_view(request):
    symbol_name = request.GET.get('symbol')
    min_timestamp = request.GET.get('timestamp')  # ISO format expected, e.g. '2025-05-01T00:00:00Z'

    if not symbol_name or not min_timestamp:
        return JsonResponse({'error': 'symbol and timestamp are required.'}, status=400)

    try:
        symbol = Asset.objects.get(symbol=symbol_name)
        parsed_timestamp = parse_datetime(min_timestamp)
        if parsed_timestamp is None:
            raise ValueError
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Symbol not found.'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid timestamp format.'}, status=400)

    candles = Candle1D.objects.filter(symbol=symbol, timestamp__gte=parsed_timestamp).order_by('timestamp')

    data = [
        {
            'timestamp': candle.timestamp.isoformat(),
            'open': str(candle.open),
            'high': str(candle.high),
            'low': str(candle.low),
            'close': str(candle.close),
            'volume': str(candle.volume)
        }
        for candle in candles
    ]

    return JsonResponse({'candles': data})


def get_4h_view(request):
    symbol_name = request.GET.get('symbol')
    min_timestamp = request.GET.get('timestamp')  # ISO format expected, e.g. '2025-05-01T00:00:00Z'

    if not symbol_name or not min_timestamp:
        return JsonResponse({'error': 'symbol and timestamp are required.'}, status=400)

    try:
        symbol = Asset.objects.get(symbol=symbol_name)
        parsed_timestamp = parse_datetime(min_timestamp)
        if parsed_timestamp is None:
            raise ValueError
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Symbol not found.'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid timestamp format.'}, status=400)

    candles = Candle4H.objects.filter(symbol=symbol, timestamp__gte=parsed_timestamp).order_by('timestamp')

    data = [
        {
            'timestamp': candle.timestamp.isoformat(),
            'open': str(candle.open),
            'high': str(candle.high),
            'low': str(candle.low),
            'close': str(candle.close),
            'volume': str(candle.volume)
        }
        for candle in candles
    ]

    return JsonResponse({'candles': data})



def get_1h_view(request):
    symbol_name = request.GET.get('symbol')
    min_timestamp = request.GET.get('timestamp')  # ISO format expected, e.g. '2025-05-01T00:00:00Z'

    if not symbol_name or not min_timestamp:
        return JsonResponse({'error': 'symbol and timestamp are required.'}, status=400)

    try:
        symbol = Asset.objects.get(symbol=symbol_name)
        parsed_timestamp = parse_datetime(min_timestamp)
        if parsed_timestamp is None:
            raise ValueError
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Symbol not found.'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid timestamp format.'}, status=400)

    candles = Candle1H.objects.filter(symbol=symbol, timestamp__gte=parsed_timestamp).order_by('timestamp')

    data = [
        {
            'timestamp': candle.timestamp.isoformat(),
            'open': str(candle.open),
            'high': str(candle.high),
            'low': str(candle.low),
            'close': str(candle.close),
            'volume': str(candle.volume)
        }
        for candle in candles
    ]

    return JsonResponse({'candles': data})



def get_15m_view(request):
    symbol_name = request.GET.get('symbol')
    min_timestamp = request.GET.get('timestamp')  # ISO format expected, e.g. '2025-05-01T00:00:00Z'

    if not symbol_name or not min_timestamp:
        return JsonResponse({'error': 'symbol and timestamp are required.'}, status=400)

    try:
        symbol = Asset.objects.get(symbol=symbol_name)
        parsed_timestamp = parse_datetime(min_timestamp)
        if parsed_timestamp is None:
            raise ValueError
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Symbol not found.'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Invalid timestamp format.'}, status=400)

    candles = Candle15M.objects.filter(symbol=symbol, timestamp__gte=parsed_timestamp).order_by('timestamp')

    data = [
        {
            'timestamp': candle.timestamp.isoformat(),
            'open': str(candle.open),
            'high': str(candle.high),
            'low': str(candle.low),
            'close': str(candle.close),
            'volume': str(candle.volume)
        }
        for candle in candles
    ]

    return JsonResponse({'candles': data})
