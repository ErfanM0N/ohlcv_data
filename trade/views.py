from django.http import JsonResponse
import logging
from .utils import get_positions, futures_order, get_balance, cancel_orders, save_orders, get_history
import json
from django.views.decorators.csrf import csrf_exempt

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

        if not all([symbol, quantity, side, tp, sl]):
            return JsonResponse({'error': 'All fields (symbol, quantity, side, tp, sl) are required.'}, status=400)

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
                response.get('data', {}).get('sl_order')
            )
        elif response.get('code') == 200:
            save_orders(
                response.get('data', {}).get('order'),
                response.get('data', {}).get('tp_order'),
                response.get('data', {}).get('sl_order'),
                leverage=leverage,
                trading_model=trading_model
            )

        return JsonResponse({
            'data': response.get('data', {}),
            'error': response.get('error', None)
        },
        status=200 if 'data' in response else response.get('code', 400)
        )

    except Exception as e:
        logger.exception("Error in place_futures_order_view")
        return JsonResponse({'error': str(e)}, status=400)
