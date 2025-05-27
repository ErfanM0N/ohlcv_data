from django.http import JsonResponse
import logging
from .utils import get_positions, futures_order
import json
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def get_positions_view(request):
    try:
        positions = get_positions()
        return JsonResponse({'positions': positions})
    except Exception as e:
        logger.exception("Error fetching positions")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def place_futures_order_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)

        symbol = data['symbol']
        quantity = float(data['quantity'])
        side = data['side']
        leverage = int(data.get('leverage', 1))
        order_type = data.get('order_type')
        tp = data.get('tp')
        sl = data.get('sl')

        order, tp_order, sl_order = futures_order(
            symbol=symbol,
            quantity=quantity,
            side=side,
            leverage=leverage,
            order_type=order_type,
            tp=tp,
            sl=sl
        )

        return JsonResponse({
            'order': order,
            'tp_order': tp_order,
            'sl_order': sl_order
        })

    except Exception as e:
        logger.exception("Error in place_futures_order_view")
        return JsonResponse({'error': str(e)}, status=400)
