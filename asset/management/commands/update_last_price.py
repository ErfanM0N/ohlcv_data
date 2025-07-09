import json
import threading
import websocket
from django.core.management.base import BaseCommand
from asset.models import Asset
from logging import getLogger
from trade.utils import send_health_check_message
import time

logger = getLogger(__name__)


class Command(BaseCommand):
    help = 'Start Binance multi-stream WebSocket and print last prices'

    def handle(self, *args, **options):
        symbols = [a.symbol.lower() for a in Asset.objects.filter(enable=True)]
        last_update_dict = {a.symbol.upper(): 0 for a in Asset.objects.filter(enable=True)}

        stream_query = '/'.join([f"{symbol}@ticker" for symbol in symbols])
        ws_url = f"wss://stream.binance.com:9443/stream?streams={stream_query}"

        def on_message(ws, message):
            data = json.loads(message)
            stream = data['stream']  # e.g., btcusdt@ticker
            payload = data['data']
            symbol = payload['s'].lower()
            last_price = payload['c']
            last_update_dict[symbol.upper()] += 1
            if last_update_dict[symbol.upper()] == 10:
                last_update_dict[symbol.upper()] = 0
                update_asset_price(symbol, last_price) 

        def update_asset_price(symbol, price):
            try:
                asset = Asset.objects.get(symbol=symbol.upper(), enable=True)
                asset.last_price = price
                asset.save(update_fields=['last_price', 'updated'])
                logger.info(f"Updated {asset.symbol} last price to {price}")
            except Exception as e:
                logger.error(f"Error updating asset {symbol}: {e}")

        def on_error(ws, error):
            send_health_check_message(f"WebSocket error: {error}")
            logger.error(f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            send_health_check_message("WebSocket connection closed")
            logger.info("WebSocket closed")
            time.sleep(5)  # Wait before trying to reconnect
            run_ws()

        def on_open(ws):
            send_health_check_message("WebSocket connection opened")
            logger.info("WebSocket connection opened.")

        def run_ws():
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open,
            )

            # Run WebSocket in a background thread so Django command doesn't block
            wst = threading.Thread(target=ws.run_forever, daemon=True)
            wst.start()

        run_ws()

