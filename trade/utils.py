import logging
from binance.client import Client
from binance.enums import *
from decouple import config

logger = logging.getLogger(__name__)


api_key = config('BINANCE_API_KEY')
secret_key = config('BINANCE_SECRET_KEY')
client = Client(api_key=api_key, api_secret=secret_key)


def futures_order(symbol, quantity, side, leverage=1, order_type=ORDER_TYPE_MARKET, tp=None, sl=None):
    order, tp_order, sl_order = None, None, None

    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        
        order_params = {
            'symbol': symbol,
            'side': SIDE_BUY if side.lower() == 'buy' else SIDE_SELL,
            'type': order_type,
            'quantity': quantity
        }

        order = client.futures_create_order(**order_params)

        if tp is not None:
            tp_side = SIDE_SELL if side.lower() == 'buy' else SIDE_BUY

            tp_order = client.futures_create_order(
                symbol=symbol,
                side=tp_side,
                type="TAKE_PROFIT_MARKET",
                stopPrice=tp,
                closePosition=True
            )
        

        if sl is not None:
            sl_side = SIDE_SELL if side.lower() == 'buy' else SIDE_BUY

            sl_order = client.futures_create_order(
                symbol=symbol,
                side=sl_side,
                type="STOP_MARKET",
                stopPrice=sl,
                closePosition=True
            )
        
    except Exception as e:
        logger.exception("Error placing futures order:", e)
    
    return order, tp_order, sl_order


def get_positions():
    positions = client.futures_position_information()
    return positions

