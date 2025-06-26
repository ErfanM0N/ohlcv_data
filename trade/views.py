from django.http import JsonResponse
import logging
from .utils import get_positions, futures_order, get_balance
import json
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def get_positions_view(request):
    positions = get_positions()
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

        if not all([symbol, quantity, side, tp, sl]):
            return JsonResponse({'error': 'All fields (symbol, quantity, side, tp, sl) are required.'}, status=400)

        quantity = float(quantity)
        tp = float(tp)
        sl = float(sl)

        json_response = futures_order(
            symbol=symbol,
            quantity=quantity,
            side=side,
            tp=tp,
            sl=sl,
            leverage=leverage
        )

        return JsonResponse({
            'data': json_response.get('data', {}),
            'error': json_response.get('error', None)
        },
        status=200 if 'data' in json_response else 400
        )

    except Exception as e:
        logger.exception("Error in place_futures_order_view")
        return JsonResponse({'error': str(e)}, status=400)
