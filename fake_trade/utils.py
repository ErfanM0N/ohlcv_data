import requests
import logging
from decouple import config

logger = logging.getLogger(__name__)

# Load config once
TELEGRAM_BOT_TOKEN = config("BOT_TOKEN")
TELEGRAM_CHAT_ID = '-1003520692428' # or config("TELEGRAM_CHAT_ID")
BINANCE_API_KEY = config("BINANCE_API_KEY")

def send_telegram_message(message: str):
    """
    Send a message to the Telegram channel via bot.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # We use a try/except here to prevent an infinite loop 
    # if the internet is down.
    try:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown" 
        }
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Just log this one, don't try to send a telegram message about failing to send a telegram message
        logger.error(f"Failed to send Telegram message: {e}")


def fetch_last_prices():
    """
    Fetch the last price for all symbols.
    Returns a Dictionary: {'BTCUSDT': 65000.00, ...}
    If it fails, it sends an alert to Telegram and returns None.
    """
    try:
        headers = {'X-MBX-APIKEY': BINANCE_API_KEY}
        
        # Fetch all ticker prices
        response = requests.get(
            'https://fapi.binance.com/fapi/v1/ticker/price',
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        prices_data = response.json()

        # Create dictionary
        prices_dict = {item['symbol']: float(item['price']) for item in prices_data}
        return prices_dict

    except requests.exceptions.RequestException as e:
        msg = f"⚠️ *CRITICAL API ERROR*\nFailed to fetch Binance prices.\nError: `{str(e)}`"
        logger.error(msg)
        send_telegram_message(msg)
        return None
    except Exception as e:
        msg = f"⚠️ *SYSTEM ERROR*\nUnexpected error in price fetch.\nError: `{str(e)}`"
        logger.error(msg)
        send_telegram_message(msg)
        return None