import logging
from binance.client import Client
from binance.enums import *
from decouple import config
from asset.models import Asset


logger = logging.getLogger(__name__)

api_key = config('BINANCE_API_KEY')
secret_key = config('BINANCE_SECRET_KEY')
client = Client(api_key=api_key, api_secret=secret_key)


#TODO: integrate sl and tp together, if one of them is triggered, the other should be cancelled.

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

    Returns:
        tuple: A tuple containing the main order, take profit order, and stop loss order.
    """

    side = SIDE_BUY if side.lower() == 'buy' else SIDE_SELL
    position_side = 'LONG' if side.lower() == 'buy' else 'SHORT'

    asset = Asset.objects.filter(symbol=symbol).first()
    if asset is None:
        logger.error(f"Asset {symbol} not found.")
        return {"error": f"Asset {symbol} not found."}

    last_price = float(asset.last_price)
    price_precision = len(str(last_price).split('.')[-1])
    if side == SIDE_BUY:
        tp = round(last_price * (1 + tp / 100), price_precision)
        sl = round(last_price * (1 - sl / 100), price_precision)
    else:
        tp = round(last_price * (1 - tp / 100), price_precision)
        sl = round(last_price * (1 + sl / 100), price_precision)


    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        
        order_params = {
            'symbol': symbol,
            'side': side,
            'positionSide': position_side,
            'type': order_type,
            'quantity': quantity
        }

        order = client.futures_create_order(**order_params)

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

        return {"data": {
            "order": order,
            "tp_order": tp_order,
            "sl_order": sl_order
        }}

    except Exception as e:
        logger.exception(f"Error placing futures order: {e}")
        return {"error": f"Failed to place futures order. {str(e)}"}


def get_positions():
    try:
        positions = client.futures_position_information()
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