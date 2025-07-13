from django.core.management.base import BaseCommand
from binance import ThreadedWebsocketManager
from asgiref.sync import sync_to_async
from asset.models import Asset
import asyncio
from trade.utils import send_health_check_message


class Command(BaseCommand):
    help = 'Start Binance WebSocket and update Asset prices'

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()

        async def process_msg(msg):
            try:
                symbol = msg['s'].lower()
                price = float(msg['c'])
                await update_asset_price(symbol, price)
            except Exception as e:
                print(f"Error processing message: {e}")


        @sync_to_async
        def update_asset_price(symbol, price):
            try:
                asset = Asset.objects.get(symbol=symbol.upper(), enable=True)
                asset.last_price = price
                asset.save(update_fields=['last_price', 'updated'])
                print(f"Updated {asset.symbol} last price to {price}")
            except Exception as e:
                print(f"Error updating asset {symbol}: {e}")

        def handle_socket_message(msg):
            try:
                asyncio.run_coroutine_threadsafe(process_msg(msg), loop)
            except Exception as e:
                print(f"Exception while handling message: {e}")


        def start_ws():
            try:
                twm = ThreadedWebsocketManager()
                twm.start()

                symbols = [a.symbol.upper() for a in Asset.objects.filter(enable=True)]
                for symbol in symbols:
                    twm.start_symbol_ticker_socket(callback=handle_socket_message, symbol=symbol)

                self.stdout.write(self.style.SUCCESS("WebSocket started for: " + ", ".join(symbols)))
                twm.join()
            except Exception as e:
                print(f"WebSocket error: {e}. Restarting in 5 seconds...")
                time.sleep(5)
                start_ws()

        start_ws()