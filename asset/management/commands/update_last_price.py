from django.core.management.base import BaseCommand
from binance import ThreadedWebsocketManager
from asgiref.sync import sync_to_async
from asset.models import Asset
import asyncio


class Command(BaseCommand):
    help = 'Start Binance WebSocket and update Asset prices'

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()

        async def process_msg(msg):
            symbol = msg['s'].lower()
            price = float(msg['c'])

            await update_asset_price(symbol, price)
            await asyncio.sleep(30)

        @sync_to_async
        def update_asset_price(symbol, price):
            try:
                asset = Asset.objects.get(symbol=symbol.upper(), enable=True)
                asset.last_price = price
                asset.save(update_fields=['last_price', 'updated'])
                print(f"Updated {asset.symbol} last price to {price}")
            except Asset.DoesNotExist:
                pass

        def handle_socket_message(msg):
            asyncio.run_coroutine_threadsafe(process_msg(msg), loop)


        twm = ThreadedWebsocketManager()
        twm.start()

        symbols = [a.symbol.upper() for a in Asset.objects.filter(enable=True)]
        for symbol in symbols:
            twm.start_symbol_ticker_socket(callback=handle_socket_message, symbol=symbol)

        self.stdout.write(self.style.SUCCESS("WebSocket started for: " + ", ".join(symbols)))
        twm.join()
