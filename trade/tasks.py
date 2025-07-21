from celery import shared_task
from trade.utils import send_bot_message, get_balance, get_spot_balance, get_position_history_from_binance
from trade.models import Position, Order
import logging

logger = logging.getLogger(__name__)


@shared_task
def balance_report():
    """
    Task to send a balance report message.
    """
    try:
        futures_balance = get_balance()
        spot_balance = get_spot_balance()
        total_balance = futures_balance['balance'] + spot_balance['balance']
        trade_pocket_balance = futures_balance['balance']
        unrealized_pnl = futures_balance['crossUnPnl']
        
        send_bot_message(f"🤑Balance Report:\n\n💳Total balance: {total_balance:.2f}$\n💰Balance in trade: {trade_pocket_balance:.2f}$\n📈Unrealized PNL: {unrealized_pnl:.2f}$")
    except Exception as e:
        logger.error(f"Error sending balance report: {e}")
        print(f"Error sending balance report: {e}")


@shared_task
def save_balance_record():
    """
    Task to save a balance record.
    """
    try:
        futures_balance = get_balance()
        spot_balance = get_spot_balance()
        total_balance = futures_balance['balance'] + spot_balance['balance']
        trade_pocket_balance = futures_balance['balance']
        unrealized_pnl = futures_balance['crossUnPnl']
        unrealized_balance = trade_pocket_balance + unrealized_pnl
        
        from trade.models import BalanceRecord
        BalanceRecord.objects.create(
            total_balance=total_balance,
            trade_pocket_balance=trade_pocket_balance,
            unrealized_pnl=unrealized_pnl,
            unrealized_trade_balance=unrealized_balance
        )
        logger.info("Balance record saved successfully.")
    except Exception as e:
        logger.error(f"Error saving balance record: {e}")
        print(f"Error saving balance record: {e}")

@shared_task
def update_order_commission():
    """
    Task to update the commission of an order.
    """
    try:
        positions = get_position_history_from_binance()['data']
    except Exception as e:
        logger.error(f"Error fetching position history: {e}")
        return
    
    db_positions = Position.objects.filter(order_commission=-1)
    for position in db_positions:
        sum_commission = 0
        for p in positions:
            if p['orderId'] == position.order_id:
                sum_commission += float(p['commission'])
        if sum_commission > 0:
            position.order_commission = sum_commission
        else:
            position.order_commission = -0.1  # Default value if no commission found
        position.save()
        logger.info(f"Updated order commission for position {position.order_id} to {position.order_commission}")

    db_orders = Order.objects.filter(status='FILLED', commission=-1)
    for order in db_orders:
        sum_commission = 0
        for p in positions:
            if p['orderId'] == order.order_id:
                sum_commission += float(p['commission'])
        if sum_commission > 0:
            order.commission = sum_commission
        else:
            order.commission = -0.1  # Default value if no commission found
        order.save()
        logger.info(f"Updated commission for order {order.order_id} to {order.commission}")

    positions = Position.objects.filter(status='CLOSED',commission=-1)
    for position in positions:
        if position.order_commission > 0:
            closed_order = position.orders.filter(status='FILLED').first()
            position.commission = closed_order.commission + position.order_commission
        else:
            position.commission = -0.1
        position.save()
        logger.info(f"Updated commission for position {position.order_id} to {position.commission}")
