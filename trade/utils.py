import logging
from binance.client import Client
from binance.enums import *
from decouple import config
from asset.models import Asset
from trade.models import BalanceRecord, Position, Order, OneWayPosition
import requests
import json 
from time import sleep
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import pandas as pd

logger = logging.getLogger(__name__)

api_key = config('BINANCE_API_KEY')
secret_key = config('BINANCE_SECRET_KEY')
client = Client(api_key=api_key, api_secret=secret_key)

BOT_TOKEN = config("BOT_TOKEN")
CHANNEL_ID = config("CHANNEL_ID")
HEALTH_CHECK_ID = config("HEALTH_CHECK_ID")



def send_health_check_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": HEALTH_CHECK_ID,
        "text": text,
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() 
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Telegram message: {e}")
        return None


def send_bot_message(text, reply_msg_id=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
    }
    
    if reply_msg_id:
        payload["reply_to_message_id"] = reply_msg_id

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() 
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Telegram message: {e}")
        return None


def send_bot_photo(photo, caption=None, reply_msg_id=None):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    data = {
        "chat_id": CHANNEL_ID,
        "parse_mode": "HTML"  # Optional: allows HTML formatting in caption
    }
    
    if caption:
        data["caption"] = caption
        
    if reply_msg_id:
        data["reply_to_message_id"] = reply_msg_id

    try:
        if isinstance(photo, str):
            if photo.startswith('http'):
         
                data["photo"] = photo
                response = requests.post(url, data=data)
            else:
                
                with open(photo, 'rb') as photo_file:
                    files = {"photo": photo_file}
                    response = requests.post(url, data=data, files=files)
        else:
            files = {"photo": photo}
            response = requests.post(url, data=data, files=files)
            
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Telegram photo: {e}")
        return None
    except FileNotFoundError as e:
        logger.error(f"Photo file not found: {e}")
        return None


def open_position(symbol, quantity, side, leverage=1, trading_model=None, probability=-1):
    """
    Opens a new position on Binance.
    """

    side = SIDE_BUY if side.lower() == 'buy' else SIDE_SELL

    # Get asset
    asset = Asset.objects.filter(symbol=symbol).first()
    if asset is None:
        logger.error(f"Asset {symbol} not found.")
        send_bot_message(f"❌❌Failed to place futures order, Asset {symbol} not found.")
        return {"error": f"Asset {symbol} not found.", "code": 404}

    # Get last price
    last_price = float(asset.last_price)


    # Change leverage if needed
    try:
        if asset.leverage != leverage:
            logger.info(f"Changing leverage for {symbol} from {asset.leverage} to {leverage}.")
            client.futures_change_leverage(symbol=symbol, leverage=leverage)
            asset.leverage = leverage
            asset.save()
    except Exception as e:
        logger.error(f"Error changing leverage for {symbol}: {e}")
        send_bot_message(f"❌❌Failed to place futures order, Leverage change failed for {symbol}")
        return {"error": f"Failed to change leverage for {symbol}. ({str(e)})", "code": 500}


    # Open position
    try:
        order_params = {
            'symbol': symbol,
            'side': side,
            'type': ORDER_TYPE_MARKET,
            'quantity': quantity
        }

        order = client.futures_create_order(**order_params)
        logger.info(f"Placed futures order: {order.get('orderId')} for {symbol} at {last_price} with leverage {leverage}")
        save_position(order, leverage=leverage, trading_model=trading_model, probability=probability)

        return {"data": {
            "order": order
        }, "code": 200}

    except Exception as e:
        logger.error(f"Error opening futures position: {e}, symbol: {symbol}")
        send_bot_message(f"❌❌Failed to place futures order, Error opening position for {symbol} ({str(e)})")
        return {"error": f"Failed to open futures position. ({str(e)})", "code": 400}
    

def save_position(order, leverage=1, trading_model=None, probability=-1):
    order = client.futures_get_order(symbol=order['symbol'], orderId=order['orderId'])

    position = OneWayPosition.objects.create(
        asset=Asset.objects.get(symbol=order['symbol']),
        side='BUY' if order['side'] == SIDE_BUY else 'SELL',
        quantity=float(order['origQty']),
        order_id=order['orderId'],
        entry_price=float(order['avgPrice']),
        leverage=leverage,
        trading_model=trading_model,
        probability=probability
    )

    notional = float(order['avgPrice']) * float(order['origQty'])
    msg = f"❗️New Position:\nSymbol: {order['symbol']} \nOrder ID: {order['orderId']} \nSide: {order['side']}\nEntry Price: {order['avgPrice']} \nQuantity: {order['origQty']} \nLeverage: {leverage} \nNominal: {notional:.2f}$"
    rsp = send_bot_message(msg)

    msg_id = rsp.get('result', {}).get('message_id')
    if msg_id:
        position.telegram_message_id = msg_id
        position.save()
        logger.info(f"Telegram message sent: {msg_id}")
    logger.info(msg)


def get_open_positions():
    """
    Retrieves the currently open position on Binance.
    """
    try:
        positions_raw = client.futures_position_information()
        positions = [
            {
            "symbol": p["symbol"],
            "positionAmt": p["positionAmt"],
            "unRealizedProfit": p["unRealizedProfit"],
            "notional": p["notional"],
            "entryPrice": p["breakEvenPrice"],
            }
            for p in positions_raw
        ]
        return {"data": positions, "code": 200}

    except Exception as e:
        logger.exception(f"Error fetching open position: {e}")
        return {"error": f"Failed to fetch open position. ({str(e)})", "code": 500}


def get_position_history_from_binance():
    """
    Retrieves the position history from Binance.
    """
    try:
        positions_raw = client.futures_account_trades()

        positions = [
            {
                "symbol": p["symbol"],
                "orderId": str(p["orderId"]),
                "qty": p["qty"],
                "commission": p["commission"],
                "time": p["time"]
            }
            for p in positions_raw
        ]
        return {"data": positions, "code": 200}

    except Exception as e:
        logger.exception(f"Error fetching position history: {e}")
        return {"error": f"Failed to fetch position history. ({str(e)})", "code": 500, "data": []}


def get_position_history(start_time=None, symbol=None):
    """
    Retrieves the position history from Binance.
    """
    positions = OneWayPosition.objects.all()
    if start_time:
        positions = positions.filter(entry_time__gte=start_time)
    if symbol:
        positions = positions.filter(asset__symbol=symbol)

    result = list(positions.values(
        'id', 'asset__symbol', 'side', 'quantity', 'order_id',
        'entry_price', 'entry_time', 'leverage', 'trading_model', 
        'probability', 'telegram_message_id'
    ))
    for item in result:
        item['symbol'] = item.pop('asset__symbol')
    return result


def futures_order(symbol, quantity, side, tp, sl, leverage=1, order_type=ORDER_TYPE_MARKET, trading_model=None):
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
        trading_model (str, optional): The trading model to use.
    """

    order, tp_order, sl_order = {}, {}, {}

    side = SIDE_BUY if side.lower() == 'buy' else SIDE_SELL
    position_side = 'LONG' if side.lower() == 'buy' else 'SHORT'

    usdc_symbol = symbol.replace('USDT', 'USDC')

    asset = Asset.objects.filter(symbol=symbol, enable=True).first()
    if asset is None:
        logger.error(f"Asset {symbol} not found.")
        send_bot_message(f"❌❌Failed to place futures order, Asset {symbol} not found.")
        return {"error": f"Asset {symbol} not found.", "code": 404}

    try:
        if asset.leverage != leverage:
            logger.info(f"Changing leverage for {symbol} from {asset.leverage} to {leverage}.")
            client.futures_change_leverage(symbol=usdc_symbol, leverage=leverage)
            asset.leverage = leverage
            asset.save()
    except Exception as e:
        logger.exception(f"Error changing leverage for {symbol}: {e}")
        send_bot_message(f"❌❌Failed to place futures order, Leverage change failed for {symbol}")
        return {"error": f"Failed to change leverage for {symbol}. ({str(e)})", "code": 500}
    
    try:
        order_params = {
            'symbol': usdc_symbol,
            'side': side,
            'positionSide': position_side,
            'type': order_type,
            'quantity': quantity
        }

        order = client.futures_create_order(**order_params)
        logger.info(f"Placed futures order: {order.get('orderId')} for {symbol} with leverage {leverage}")
        
    except Exception as e:
        logger.exception(f"Error opening futures position: {e}, symbol: {symbol}")
        send_bot_message(f"❌❌Failed to place futures order, Error opening position for {symbol} ({str(e)})")
        return {"error": f"Failed to open futures position. ({str(e)})", "code": 400}

    try:
        sleep(0.2)

        last_price = float(client.futures_get_order(symbol=order['symbol'], orderId=order['orderId'])['avgPrice'])
        price_precision = 2
        if side == SIDE_BUY:
            tp = round(last_price * (1 + tp / 100), price_precision)
            sl = round(last_price * (1 - sl / 100), price_precision)
        else:
            tp = round(last_price * (1 - tp / 100), price_precision)
            sl = round(last_price * (1 + sl / 100), price_precision)

        side = SIDE_SELL if side.lower() == 'buy' else SIDE_BUY
        tp_order = client.futures_create_order(
            symbol=usdc_symbol,
            side=side,
            positionSide=position_side, 
            type="TAKE_PROFIT_MARKET",
            stopPrice=tp,
            quantity=quantity,
            closePosition=False
        )
        
        sl_order = client.futures_create_order(
            symbol=usdc_symbol,
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
        logger.exception(f"Error placing futures orders: {e}, symbol: {symbol}, order: {order}")
        return {"data": {
            "order": order,
            "tp_order": tp_order,
            "sl_order": sl_order
        },"error": f"Failed to place futures orders. ({str(e)})", "code": 401}


def cancel_orders(order, tp_order, sl_order, symbol):
    msg = f"❌❌Failed to place futures order, Error opening TP/SL Orders for {symbol}\n"
    try:
        if order:
            side = SIDE_SELL if order['side'].lower() == 'buy' else SIDE_BUY
            position_side = order['positionSide']
            quantity = float(order['origQty'])
            usdc_symbol = order['symbol']

            client.futures_create_order(
                symbol=usdc_symbol,
                side=side,
                type='MARKET',
                quantity=quantity,
                positionSide=position_side
            )
            logger.info(f"Closed position: {order['orderId']}, symbol: {symbol}")
            msg += f"Closed position because of failed TP/SL Orders: {order['orderId']}, symbol: {symbol}\n"
        if tp_order:
            client.futures_cancel_order(symbol=tp_order['symbol'], orderId=tp_order['orderId'])
            logger.info(f"Cancelled TP order: {tp_order['orderId']}, symbol: {symbol}")
            msg += f"Cancelled TP order: {tp_order['orderId']}, symbol: {symbol}\n"
        if sl_order:
            client.futures_cancel_order(symbol=sl_order['symbol'], orderId=sl_order['orderId'])
            logger.info(f"Cancelled SL order: {sl_order['orderId']}, symbol: {symbol}")

        send_bot_message(msg + "✅Orders cancelled successfully.")

    except Exception as e:
        send_bot_message(msg + f"Error cancelling orders: {str(e)}")
        logger.exception(f"❗️❗️❗️Error cancelling orders: {e}\n close the position manually if needed.")


def save_orders(order, tp_order, sl_order, leverage=1, trading_model=None, probability=-1):
    symbol = order['symbol'].replace('USDC', 'USDT')
    msg = f"Position opened: {order['orderId']} for {symbol} at {order['avgPrice']} with leverage {leverage}\n"
    order = client.futures_get_order(symbol=order['symbol'], orderId=order['orderId'])
   
    position = Position.objects.create(
        asset=Asset.objects.get(symbol=symbol),
        side='BUY' if order['side'] == SIDE_BUY else 'SELL',
        quantity=float(order['origQty']),
        order_id=order['orderId'],
        entry_price=float(order['avgPrice']),
        leverage=leverage,
        status='OPEN',
        trading_model=trading_model,
        probability=probability
    )
    msg = f"❗️New Position:\n {symbol} \n{order['orderId']} \n{order['side']}\n at {order['avgPrice']} \nquantity: {order['origQty']}\nwith probability: {probability:.4f}\n\n"
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

    rsp = send_bot_message(msg + f"✅TP Price: {tp_order['stopPrice']}\n❌SL Price: {sl_order['stopPrice']}")
    msg_id = rsp.get('result', {}).get('message_id')
    if msg_id:
        position.telegram_message_id = msg_id
        position.save()


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
            'entry_price', 'entry_time', 'leverage', 'exit_price', 'exit_time', 'pnl', 'probability'
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
        balance = next((item for item in balances if item['asset'] == 'USDC'), None)
        
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


def get_spot_balance():
    try:
        account_info = client.get_account()
        balances = account_info['balances']
        usdt_balance = next((item for item in balances if item['asset'] == 'USDC'), None)
        
        if usdt_balance is None:
            logger.error("USDT balance not found in spot account.")
            return {"error": "USDT balance not found in spot account.", "code": 400}

        balance = {
            "balance": float(usdt_balance['free']),
            "availableBalance": float(usdt_balance['free']),
            "crossUnPnl": 0.0
        }
        return balance

    except Exception as e:
        logger.exception(f"Error fetching spot account balance: {e}")
        return {"error": f"Failed to fetch spot account balance. ({str(e)})", "code": 500}


def get_orders():
    open_orders = client.futures_get_open_orders(symbol="LTCUSDT")
    print(open_orders)


def cancel_orders():
    symbol = "LTCUSDT"
    try:
        result = client.futures_cancel_all_open_orders(symbol=symbol)
        print("Cancelled Orders:", result)
    except Exception as e:
        print("Error:", e)


def create_daily_balance_chart(records, start_time, end_time):
    """
    Create a line chart of unrealized trade balance over time
    Returns BytesIO buffer containing the chart image
    """
    try:
        timestamps = [record.timestamp for record in records]
        balances = [record.unrealized_trade_balance for record in records]
        
        plt.style.use('dark_background')  # Dark theme for better Telegram appearance
        fig, ax = plt.subplots(figsize=(12, 6))


        # --- SCALING MODIFICATION START ---
        if balances:
            min_balance = min(balances)
            max_balance = max(balances)

            if min_balance != max_balance:
                # Calculate buffer based on 10% of the range
                balance_range = max_balance - min_balance
                total_buffer = balance_range * 0.10
                
                # To move the data visually towards the top,
                bottom_buffer = total_buffer * 0.6 
                top_buffer = total_buffer * 0.4    
                
                y_min = min_balance - bottom_buffer
                y_max = max_balance + top_buffer
                
                # Apply the new y-axis limits to scale and position the plot
                ax.set_ylim(y_min, y_max)
            else:

                buffer_size = 1.0 
                ax.set_ylim(min_balance - buffer_size, max_balance + buffer_size)
        # --- SCALING MODIFICATION END ---
        
        ax.plot(timestamps, balances, linewidth=2, color='#00ff41', markersize=3)
        
        ax.set_title('Unrealized Trade Balance - Last 24 Hours', 
                    fontsize=16, fontweight='bold', color='white', pad=20)
        ax.set_xlabel('Time', fontsize=12, color='white')
        ax.set_ylabel('Balance ($)', fontsize=12, color='white')
        
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        
        plt.xticks(rotation=45)
        ax.grid(True, alpha=0.3, color='gray')
        
        fill_color = 'gray'
        alpha = 0.1
            
        ax.fill_between(timestamps, balances, alpha=alpha, color=fill_color)
        

        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
                   facecolor='#0f1419', edgecolor='none')
        img_buffer.seek(0)
        
        plt.close(fig)
        
        return img_buffer
        
    except Exception as e:
        logger.error(f"Error creating balance chart: {e}")
        return None


def create_weekly_balance_chart(records, start_time, end_time):
    """
    Create a line chart of unrealized trade balance over time for a week,
    showing only the day on the x-axis.
    Returns BytesIO buffer containing the chart image
    """
    # NOTE: This assumes 'mdates' and 'BytesIO' are imported,
    # and 'logger' is defined for error handling, and 'plt' is imported.

    try:
        timestamps = [record.timestamp for record in records]
        balances = [record.unrealized_trade_balance for record in records]
        
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 6))

        # --- SCALING MODIFICATION (Keep as is) ---
        if balances:
            min_balance = min(balances)
            max_balance = max(balances)

            if min_balance != max_balance:
                balance_range = max_balance - min_balance
                total_buffer = balance_range * 0.10
                bottom_buffer = total_buffer * 0.6 
                top_buffer = total_buffer * 0.4    
                y_min = min_balance - bottom_buffer
                y_max = max_balance + top_buffer
                ax.set_ylim(y_min, y_max)
            else:
                buffer_size = 1.0 
                ax.set_ylim(min_balance - buffer_size, max_balance + buffer_size)
        # --- SCALING MODIFICATION END ---
        
        ax.plot(timestamps, balances, linewidth=2, color='#00ff41', markersize=3)
        
        ax.set_title('Unrealized Trade Balance - Last 7 Days', 
                     fontsize=16, fontweight='bold', color='white', pad=20)
        ax.set_xlabel('Day', fontsize=12, color='white') # Updated x-label
        ax.set_ylabel('Balance ($)', fontsize=12, color='white')
        
        # Y-axis formatter (Keep as is)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # 1. Update X-axis Formatter to only show the abbreviated Day of the week
        # '%a' gives 'Mon', 'Tue', etc.
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%a')) 
        
        # 2. Update X-axis Locator for Ticks at the start of each Day
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1)) 
        
        # Optional: Set a minor locator for better grid lines, e.g., every 6 hours
        ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 6)))
        ax.grid(True, which='major', alpha=0.5, color='gray')
        ax.grid(True, which='minor', alpha=0.1, color='gray') # Lighter grid lines for minor ticks

        plt.xticks(rotation=0, ha='center') # Reduced rotation and centered labels for short day names
        
        fill_color = 'gray'
        alpha = 0.1
            
        ax.fill_between(timestamps, balances, alpha=alpha, color=fill_color)
        

        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight',
                    facecolor='#0f1419', edgecolor='none')
        img_buffer.seek(0)
        
        plt.close(fig)
        
        return img_buffer
        
    except Exception as e:
        logger.error(f"Error creating weekly balance chart: {e}") 
        return None


def get_balance_history_without_start():
    records = list(BalanceRecord.objects.all().order_by('-timestamp'))
    return records


