from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import logging
from decimal import Decimal

from .models import DemoConfig, DemoPosition
from asset.models import Asset

logger = logging.getLogger(__name__)
from .utils import send_telegram_message


@csrf_exempt
def place_fake_order(request):
    if request.method != 'POST':
        send_telegram_message("❌ POST method required for /api/demo/place-order/")
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        side = data.get('side')
        entry_price = data.get('entry_price')
        take_profit = data.get('tp')
        stop_loss = data.get('sl')

        if not all([symbol, quantity, side, entry_price, take_profit, stop_loss]):
            msg = "❌ Missing fields in order request"
            send_telegram_message(msg)
            return JsonResponse({'error': 'All fields (symbol, quantity, side, entry_price, tp, sl) are required.'}, status=400)

        config = DemoConfig.objects.first()
        if not config:
            msg = "❌ Demo configuration not found"
            send_telegram_message(msg)
            return JsonResponse({'error': 'Demo configuration not found.'}, status=500)

        # Check max open positions
        open_positions_count = DemoPosition.objects.filter(status__in=['PENDING', 'OPEN']).count()
        if open_positions_count >= config.max_open_positions:
            msg = f"❌ Max open positions reached ({config.max_open_positions}). Cannot place new order."
            send_telegram_message(msg)
            return JsonResponse({'error': msg}, status=400)

        # Check available balance
        required_margin = float(quantity) * float(entry_price)
        if required_margin > float(config.available_balance):
            msg = f"❌ Not enough balance. Required: {required_margin}, Available: {config.available_balance}"
            send_telegram_message(msg)
            return JsonResponse({'error': msg}, status=400)

        # Find asset
        asset = Asset.objects.filter(symbol=symbol.upper()).first()
        if not asset:
            msg = f"❌ Asset {symbol} not found"
            send_telegram_message(msg)
            return JsonResponse({'error': msg}, status=404)

        # Create position
        position = DemoPosition.objects.create(
            asset=asset,
            side=side.upper(),
            quantity=quantity,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            margin_balance=required_margin
        )

        # Update available balance
        config.available_balance -= Decimal(required_margin)
        config.save()

        msg = f"💰 New Order:\n*Position ID:* {position.id}\n*Symbol:* {symbol.upper()}\n*Side:* {side.upper()}\n*Quantity:* {quantity}\n*Margin:* {required_margin}\n*Available Balance: *{config.available_balance}\n"
        send_telegram_message(msg)
        logger.info(msg)

        return JsonResponse({
            'success': True,
            'position_id': position.id,
            'symbol': symbol.upper(),
            'quantity': quantity,
            'side': side.upper(),
            'margin_used': required_margin
        })

    except Exception as e:
        msg = f"❌ Error placing fake order: {str(e)}"
        send_telegram_message(msg)
        logger.exception(msg)
        return JsonResponse({'error': str(e)}, status=500)
