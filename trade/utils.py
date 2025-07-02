import logging
from binance.client import Client
from binance.enums import *
from decouple import config
from asset.models import Asset
from trade.models import Position, Order
from django.db.models import F

logger = logging.getLogger(__name__)

api_key = config('BINANCE_API_KEY')
secret_key = config('BINANCE_SECRET_KEY')
client = Client(api_key=api_key, api_secret=secret_key)


def futures_order(symbol, quantity, side, tp, sl, leverage=1, order_type=ORDER_TYPE_MARKET):
    """
    Places a futures order on Binance.

    Args:
        symbol (str): The trading pair (e.g., 'BTCUSDT').
        quantity (float): The amount of the asset to trade.
        side (str): 'BUY' or 'SELL'.
        tp (float, optional): Take Profit price. 
        sl (float, optional): Stop Loss price. 
        leverage (int): The leverage to use for the position.
        order_type (str): The type of order (e.g., 'MARKET', 'LIMIT').
    """

    order, tp_order, sl_order = {}, {}, {}

    side = SIDE_BUY if side.lower() == 'buy' else SIDE_SELL
    position_side = 'LONG' if side.lower() == 'buy' else 'SHORT'

    asset = Asset.objects.filter(symbol=symbol).first()
    if asset is None:
        logger.error(f"Asset {symbol} not found.")
        return {"error": f"Asset {symbol} not found.", "code": 404}

    last_price = float(asset.last_price)
    price_precision = len(str(last_price).split('.')[-1])
    if side == SIDE_BUY:
        tp = round(last_price * (1 + tp / 100), price_precision)
        sl = round(last_price * (1 - sl / 100), price_precision)
    else:
        tp = round(last_price * (1 - tp / 100), price_precision)
        sl = round(last_price * (1 + sl / 100), price_precision)


    try:
        if asset.leverage != leverage:
            logger.info(f"Changing leverage for {symbol} from {asset.leverage} to {leverage}.")
            client.futures_change_leverage(symbol=symbol, leverage=leverage)
            asset.leverage = leverage
            asset.save()
    except Exception as e:
        logger.exception(f"Error changing leverage for {symbol}: {e}")
        return {"error": f"Failed to change leverage for {symbol}. ({str(e)})", "code": 500}
    
    try:
        order_params = {
            'symbol': symbol,
            'side': side,
            'positionSide': position_side,
            'type': order_type,
            'quantity': quantity
        }

        order = client.futures_create_order(**order_params)
        logger.info(f"Placed futures order: {order.get('orderId')} for {symbol} at {last_price} with leverage {leverage}")
        
    except Exception as e:
        logger.exception(f"Error opening futures position: {e}, symbol: {symbol}")
        return {"error": f"Failed to open futures position. ({str(e)})", "code": 400}

    try:
        side = SIDE_SELL if side.lower() == 'buy' else SIDE_BUY
        tp_order = client.futures_create_order(
            symbol=symbol,
            side=side,
            positionSide=position_side, 
            type="TAKE_PROFIT_MARKET",
            stopPrice=tp,
            quantity=quantity,
            closePosition=False
        )
        
        sl_order = client.futures_create_order(
            symbol=symbol,
            side=side,
            positionSide=position_side,
            type="STOP_MARKET",
            stopPrice=sl,
            quantity=quantity,
            closePosition=False
        )
        logger.info(f"Placed TP order: {tp_order.get('orderId')}, SL order: {sl_order.get('orderId')}, symbol: {symbol}")

        return {"data": {
            "order": order,
            "tp_order": tp_order,
            "sl_order": sl_order
        }, "code": 200}

    except Exception as e:
        logger.exception(f"Error placing futures orders: {e}, symbol: {symbol}")
        return {"data": {
            "order": order,
            "tp_order": tp_order,
            "sl_order": sl_order
        },"error": f"Failed to place futures orders. ({str(e)})", "code": 401}


def cancel_orders(order, tp_order, sl_order):
    try:
        if order:
            side = SIDE_SELL if order['side'].lower() == 'buy' else SIDE_BUY
            position_side = order['positionSide']
            quantity = float(order['origQty'])
            symbol = order['symbol']

            client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity,
                positionSide=position_side
            )
            logger.info(f"Closed position: {order['orderId']}, symbol: {symbol}")
        if tp_order:
            client.futures_cancel_order(symbol=tp_order['symbol'], orderId=tp_order['orderId'])
            logger.info(f"Cancelled TP order: {tp_order['orderId']}, symbol: {tp_order['symbol']}")
        if sl_order:
            client.futures_cancel_order(symbol=sl_order['symbol'], orderId=sl_order['orderId'])
            logger.info(f"Cancelled SL order: {sl_order['orderId']}, symbol: {sl_order['symbol']}")

    except Exception as e:
        logger.exception(f"Error cancelling orders: {e}")


def save_orders(order, tp_order, sl_order, leverage=1):
    order = client.futures_get_order(symbol=order['symbol'], orderId=order['orderId'])
    position = Position.objects.create(
        asset=Asset.objects.get(symbol=order['symbol']),
        side='BUY' if order['side'] == SIDE_BUY else 'SELL',
        quantity=float(order['origQty']),
        order_id=order['orderId'],
        entry_price=float(order['avgPrice']),
        leverage=leverage,
        status='OPEN'
    )
    logger.info(f"Saved position: {position.order_id} for {position.asset.symbol} at {position.entry_price}")

    Order.objects.create(
        position=position,
        order_type='TP',
        price=float(tp_order['stopPrice']),
        order_id=tp_order['orderId'],
        status='PENDING'
    )
    logger.info(f"Saved TP order: {tp_order['orderId']} for position: {position.order_id}")

    Order.objects.create(
        position=position,
        order_type='SL',
        price=float(sl_order['stopPrice']),
        order_id=sl_order['orderId'],
        status='PENDING'
    )
    logger.info(f"Saved SL order: {sl_order['orderId']} for position: {position.order_id}")


def get_positions():
    try:
        positions = list(Position.objects.filter(status='OPEN').values(
            'id', 'asset__symbol', 'side', 'quantity', 'order_id', 
            'entry_price', 'entry_time', 'leverage'
        ))

        for p in positions:
            p['symbol'] = p.pop('asset__symbol')

        return positions
    except Exception as e:
        logger.exception(f"Error fetching futures positions: {e}")
        return {"error": f"Failed to fetch futures positions. ({str(e)})", "code": 500}


def get_history():
    try:
        positions = list(Position.objects.filter(status='CLOSED').values(
            'id', 'asset__symbol', 'side', 'quantity', 'order_id', 
            'entry_price', 'entry_time', 'leverage', 'exit_price', 'exit_time', 'pnl'
        ))

        for p in positions:
            p['symbol'] = p.pop('asset__symbol')
            
        return positions
    except Exception as e:
        logger.exception(f"Error fetching futures positions: {e}")
        return {"error": f"Failed to fetch futures positions. ({str(e)})", "code": 500}


def get_balance():
    try:
        balances = client.futures_account_balance()
        balance = next((item for item in balances if item['asset'] == 'USDT'), None)
        
        if balance is None:
            logger.error("USDT balance not found in futures account.")
            return {"error": "USDT balance not found in futures account.", "code": 400}

        balance = {
            "balance": float(balance['balance']),
            "availableBalance": float(balance['availableBalance']),
            "crossUnPnl": float(balance['crossUnPnl'])
        }
        return balance

    except Exception as e:
        logger.exception(f"Error fetching futures account balance: {e}")
        return {"error": f"Failed to fetch futures account balance. ({str(e)})", "code": 500}