import logging
from binance.client import Client
from binance.enums import *
from decouple import config

logger = logging.getLogger(__name__)

api_key = config('BINANCE_API_KEY')
secret_key = config('BINANCE_SECRET_KEY')
client = Client(api_key=api_key, api_secret=secret_key)


#TODO: integrate sl and tp together, if one of them is triggered, the other should be cancelled.

def futures_order(symbol, quantity, side, leverage=1, order_type=ORDER_TYPE_MARKET, tp=None, sl=None):
    """
    Places a futures order on Binance.

    Args:
        symbol (str): The trading pair (e.g., 'BTCUSDT').
        quantity (float): The amount of the asset to trade.
        side (str): 'BUY' or 'SELL'.
        position_side (str): 'LONG' or 'SHORT'. **Crucial for Hedge Mode.**
        leverage (int): The leverage to use for the position.
        order_type (str): The type of order (e.g., 'MARKET', 'LIMIT').
        tp (float, optional): Take Profit price. Defaults to None.
        sl (float, optional): Stop Loss price. Defaults to None.

    Returns:
        tuple: A tuple containing the main order, take profit order, and stop loss order.
    """
    order, tp_order, sl_order = None, None, None

    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        
        binance_side = SIDE_BUY if side.lower() == 'buy' else SIDE_SELL
        binance_position_side = 'LONG' if side.lower() == 'buy' else 'SHORT'

        order_params = {
            'symbol': symbol,
            'side': binance_side,
            'positionSide': binance_position_side, 
            'type': order_type,
            'quantity': quantity
        }

        order = client.futures_create_order(**order_params)


        if tp is not None:
            tp_side = SIDE_SELL if side.lower() == 'buy' else SIDE_BUY
            
            tp_order = client.futures_create_order(
                symbol=symbol,
                side=tp_side,
                positionSide=binance_position_side, 
                type="TAKE_PROFIT_MARKET",
                stopPrice=tp,
                quantity=quantity,
                closePosition=False
            )
        
        if sl is not None:
            sl_side = SIDE_SELL if side.lower() == 'buy' else SIDE_BUY
            
            sl_order = client.futures_create_order(
                symbol=symbol,
                side=sl_side,
                positionSide=binance_position_side,
                type="STOP_MARKET",
                stopPrice=sl,
                quantity=quantity,
                closePosition=False
            )
        
    except Exception as e:
        logger.exception(f"Error placing futures order: {e}")

    return order, tp_order, sl_order


def get_positions():
    positions = client.futures_position_information()
    return positions