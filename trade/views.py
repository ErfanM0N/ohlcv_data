from django.http import JsonResponse
import logging
from .utils import get_positions, futures_order, get_balance, cancel_orders, save_orders, get_history, open_position, get_position_history, get_open_positions
import json
from django.views.decorators.csrf import csrf_exempt
from trade.models import Position, OneWayPosition, BalanceRecord
from datetime import datetime, timedelta
from asset.models import Asset
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder


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


def get_balance_history_view(request):
    """
    Handles HTTP GET requests to retrieve a list of balance history records, optionally filtered by a start timestamp.

    Args:
        request (HttpRequest): The HTTP request object, which may include a 'start' query parameter representing a Unix timestamp.

    Returns:
        JsonResponse: A JSON response containing a list of balance history records, each with the following fields:
            - total_balance: The total balance at the record's timestamp.
            - trade_pocket_balance: The trade pocket balance at the record's timestamp.
            - unrealized_pnl: The unrealized profit and loss at the record's timestamp.
            - unrealized_trade_balance: The unrealized trade balance at the record's timestamp.
            - timestamp: The ISO-formatted timestamp of the record.

    Notes:
        - If the 'start' query parameter is provided and valid, only records with a timestamp greater than or equal to 'start' are returned.
        - If 'start' is invalid or not provided, all records are returned.
        - The records are ordered by timestamp in descending order.
    """
    balance_history = BalanceRecord.objects.all().order_by('-timestamp')
    start = request.GET.get('start')
    if start:
        try:
            start_dt = datetime.fromtimestamp(float(start))
            balance_history = balance_history.filter(timestamp__gte=start_dt)
        except Exception:
            pass
    data = [
        {
            'total_balance': record.total_balance,
            'trade_pocket_balance': record.trade_pocket_balance,
            'unrealized_pnl': record.unrealized_pnl,
            'unrealized_trade_balance': record.unrealized_trade_balance,
            'timestamp': record.timestamp.isoformat()
        }
        for record in balance_history
    ]
    return JsonResponse({'data': data}, status=200)




def get_balance_history_without_start():
    records = list(BalanceRecord.objects.all().order_by('-timestamp'))
    return records


def get_trade_history_without_start():
    records = list(Position.objects.filter(status='CLOSED').order_by('-entry_time'))
    return records


def balance_history_view(request):
    """View for displaying balance history with date filtering"""
    records = get_balance_history_without_start()
    
    # Prepare data for JavaScript
    records_data = [
        {
            'timestamp': record.timestamp.isoformat(),
            'total_balance': record.total_balance,
            'trade_pocket_balance': record.trade_pocket_balance,
            'unrealized_pnl': record.unrealized_pnl,
            'unrealized_trade_balance': record.unrealized_trade_balance,
        }
        for record in records
    ]
    
    # Calculate default date range (last week)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    context = {
        'records_json': json.dumps(records_data),
        'default_start_date': start_date.strftime('%Y-%m-%d'),
        'default_end_date': end_date.strftime('%Y-%m-%d'),
    }

    trades = get_trade_history_without_start()
    trades_json = json.dumps([{
        'side': t.side,
        'entry_time': t.entry_time.isoformat(),
        'exit_time': t.exit_time.isoformat() if t.exit_time else None,
        'pnl': float(t.pnl),
        'symbol': t.asset.symbol,
        'quantity': float(t.quantity),
        'order_id': t.order_id,
        'entry_price': float(t.entry_price),
        'exit_price': float(t.exit_price) if t.exit_price else None,
        'leverage': t.leverage,
        'probability': float(t.probability)
    } for t in trades], cls=DjangoJSONEncoder)

    context['trades_json'] = trades_json
    
    return render(request, 'monitor.html', context)