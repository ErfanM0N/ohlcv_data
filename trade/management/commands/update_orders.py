from django.core.management.base import BaseCommand
from binance import Client, ThreadedWebsocketManager
from asgiref.sync import sync_to_async
from trade.models import Position, Order
from asset.models import Asset
import asyncio
from decouple import config
from django.utils import timezone
import logging
from trade.utils import send_bot_message

logger = logging.getLogger(__name__)


api_key = config('BINANCE_API_KEY')
secret_key = config('BINANCE_SECRET_KEY')
client = Client(api_key=api_key, api_secret=secret_key)


class Command(BaseCommand):
    help = 'Start Binance Futures WebSocket to track order updates'

    def handle(self, *args, **kwargs):
        loop = asyncio.get_event_loop()

        async def process_msg(msg):
            if msg['e'] == 'ORDER_TRADE_UPDATE':
                order = msg['o']
                order_id = order['i']
                symbol = order['s']
                status = order['X']
                logger.info(f"{order_id} for {symbol} status: {status}")
                if status == 'FILLED':
                    await update_order(symbol, order_id)

        @sync_to_async
        def update_order(symbol, order_id):
            try:
                asset = Asset.objects.get(symbol=symbol.upper(), enable=True)
                open_positions = list(Position.objects.filter(asset=asset, status='OPEN'))

                for position in open_positions:
                    for order in position.orders.filter(status='PENDING'):
                        if str(order.order_id) == str(order_id):
                            msg = f'Order {order_id} filled.\n'
                            logger.info(f"Order {order_id} for {symbol} filled")

                            # Update order status
                            order.status = 'FILLED'
                            order.save(update_fields=['status'])

                            # Update position status and PnL
                            position.status = 'CLOSED'
                            position.exit_price = order.price
                            position.exit_time = timezone.now()

                            if position.side == 'BUY':
                                position.pnl = (order.price - position.entry_price) * position.quantity
                            else:
                                position.pnl = (position.entry_price - order.price) * position.quantity
                            position.save(update_fields=['status', 'exit_price', 'exit_time', 'pnl'])
                            logger.info(f"Closed position for {asset.symbol}, order {position.order_id}")
                            msg = f"💵💵Position {position.order_id} closed with PnL: {position.pnl}\n" + msg

                            # Cancel the reverse order (TP or SL)
                            if order.order_type == 'TP':
                                reverse_order = position.orders.filter(order_type='SL').first()
                            else:
                                reverse_order = position.orders.filter(order_type='TP').first()
                            
                            reverse_order.status = 'CANCELED'
                            reverse_order.save(update_fields=['status'])
                            client.futures_cancel_order(symbol=symbol, orderId=reverse_order.order_id)
                            msg += f"Reverse order {reverse_order.order_id} canceled.\n\n"
                            msg += f"✅Position closed successfully."
                            logger.info(f"Canceled reverse order {reverse_order.order_id} for {asset.symbol}")

                            if position.telegram_message_id:
                                send_bot_message(
                                    msg,
                                    reply_msg_id=position.telegram_message_id
                                )
                            else:
                                send_bot_message(msg)
                            return

            except Exception as e:
                msg += f"❗️❗️❗️Error closing position {order_id} for {symbol}: {e}, please check manually"
                if position.telegram_message_id:
                    send_bot_message(
                        msg,
                        reply_msg_id=position.telegram_message_id
                    )
                else:
                    send_bot_message(msg)
                logger.error(f"Error closing position {order_id}: ({e}) for {symbol}")

        def handle_socket_message(msg):
            asyncio.run_coroutine_threadsafe(process_msg(msg), loop)


        twm = ThreadedWebsocketManager(api_key=api_key, api_secret=secret_key)
        twm.start()
        twm.start_futures_user_socket(callback=process_msg)

        self.stdout.write(self.style.SUCCESS("WebSocket running... Press Ctrl+C to stop."))
        twm.join()
       
