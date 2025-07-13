from django.http import JsonResponse
import logging
from .utils import get_positions, futures_order, get_balance, cancel_orders, save_orders, get_history, open_position, get_position_history, get_open_positions
import json
from django.views.decorators.csrf import csrf_exempt
from trade.models import Position, OneWayPosition
from datetime import datetime
from asset.models import Asset


logger = logging.getLogger(__name__)


def get_positions_view(request):
    positions = get_positions()
    if 'error' in positions:
        return JsonResponse({'error': positions['error'], 'data': {}}, status=positions.get('code', 500))
    return JsonResponse({'data': positions}, status=200)

def get_trade_history_view(request):
    positions = get_history()
    if 'error' in positions:
        return JsonResponse({'error': positions['error'], 'data': {}}, status=positions.get('code', 500))
    return JsonResponse({'data': positions}, status=200)


def get_balance_view(request):
    balance = get_balance()
    if 'error' in balance:
        return JsonResponse({'error': balance['error'], 'data': {}}, status=balance.get('code', 500))
    return JsonResponse({'data': balance}, status=200)


@csrf_exempt
def place_futures_order_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        side = data.get('side')
        tp = data.get('tp')
        sl = data.get('sl')
        leverage = int(data.get('leverage', 1))
        trading_model = data.get('trading_model')
        probability = float(data.get('probability', -1))

        asset = Asset.objects.filter(symbol=symbol.upper()).first()
        if asset:
            OneWayPosition.objects.create(
                asset=asset,
                order_id=int(datetime.now().timestamp()),
                quantity=quantity,
                entry_price=asset.last_price,
                side=side.upper(),
                leverage=leverage,
                probability=probability
            )

        logger.info(f"OneWayPosition created: {symbol} - {quantity} - {side} - {leverage}") 

        if not all([symbol, quantity, side, tp, sl]):
            return JsonResponse({'error': 'All fields (symbol, quantity, side, tp, sl) are required.'}, status=400)

        # Handle with MastMali
        open_positions_count = Position.objects.filter(status='OPEN').count()
        if open_positions_count >= 5:
            return JsonResponse({'error': 'max position limit reached'}, status=400)
        #######################
        
        quantity = float(quantity)
        tp = float(tp)
        sl = float(sl)

        response = futures_order(
            symbol=symbol,
            quantity=quantity,
            side=side,
            tp=tp,
            sl=sl,
            leverage=leverage,
            trading_model=trading_model
        )

        if response.get('code') == 401:
            cancel_orders(
                response.get('data', {}).get('order'),
                response.get('data', {}).get('tp_order'),
                response.get('data', {}).get('sl_order'),
                symbol=symbol
            )
        elif response.get('code') == 200:
            save_orders(
                response.get('data', {}).get('order'),
                response.get('data', {}).get('tp_order'),
                response.get('data', {}).get('sl_order'),
                leverage=leverage,
                trading_model=trading_model,
                probability=probability
            )

        return JsonResponse({
            'data': response.get('data', {}),
            'error': response.get('error', None)
        },
        status=response.get('code', 400)
        )

    except Exception as e:
        logger.exception("Error in place_futures_order_view")
        return JsonResponse({'error': str(e)}, status=400)
    

@csrf_exempt
def open_position_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        side = data.get('side')
        leverage = int(data.get('leverage', 1))
        trading_model = data.get('trading_model')
        probability = float(data.get('probability', -1))

        if not all([symbol, quantity, side]):
            return JsonResponse({'error': 'All fields (symbol, quantity, side) are required.'}, status=400)

        quantity = float(quantity)

        response = open_position(
            symbol=symbol,
            quantity=quantity,
            side=side,
            leverage=leverage,
            trading_model=trading_model,
            probability=probability
        )

        return JsonResponse({
            'data': response.get('data', {}),
            'error': response.get('error', None)
        },
        status=response.get('code', 400)
        )

    except Exception as e:
        logger.error("Error in Open Position View")
        return JsonResponse({'error': str(e)}, status=400)

def get_position_history_view(request):
    symbol = request.GET.get('symbol')
    start_time = request.GET.get('start_time')
    positions = get_position_history(start_time=start_time, symbol=symbol)
    return JsonResponse({'data': positions}, status=200)


def get_open_positions_view(request):
    positions = get_open_positions()
    if 'error' in positions:
        return JsonResponse({'error': positions['error'], 'data': {}}, status=positions.get('code', 500))
    return JsonResponse({'data': positions.get('data', [])}, status=200)