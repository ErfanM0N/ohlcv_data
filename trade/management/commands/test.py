from django.core.management.base import BaseCommand
from binance.client import Client
from decouple import config


class Command(BaseCommand):
    help = 'Get the status of a Binance order by symbol and order ID'

    def add_arguments(self, parser):
        parser.add_argument('symbol', type=str, help='Binance symbol, e.g. BTCUSDT')
        parser.add_argument('order_id', type=int, help='Binance order ID')

    def handle(self, *args, **options):
        symbol = options['symbol'].upper()
        order_id = options['order_id']

        # Load API credentials from environment (or replace with settings)
        api_key = config('BINANCE_API_KEY')
        api_secret = config('BINANCE_SECRET_KEY')

        if not api_key or not api_secret:
            self.stderr.write("❌ Binance API key/secret not set in environment variables.")
            return

        # Connect to Binance API
        client = Client(api_key, api_secret)

        try:
            order = client.futures_get_order(symbol=symbol, orderId=order_id)
            self.stdout.write(self.style.SUCCESS(f"✅ Order status: {order['status']}"))
            self.stdout.write(str(order))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error fetching order status: {str(e)}"))
