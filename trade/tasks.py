from celery import shared_task
from trade.utils import send_bot_message, get_balance, get_spot_balance, get_position_history_from_binance, create_daily_balance_chart, send_bot_photo, create_weekly_balance_chart
from trade.models import Position, Order
import logging
from django.utils import timezone
from datetime import datetime, timedelta
from .models import BalanceRecord


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


def format_change(change):
    """Format balance change with appropriate emoji and formatting"""
    if change > 0:
        return f"+${abs(change):,.2f}"
    elif change < 0:
        return f"-${abs(change):,.2f}"
    else:
        return f"${change:,.2f}"
    

@shared_task
def send_daily_balance_report():
    """
    Send daily unrealized trade balance report via Telegram at midnight.
    Shows changes from the previous midnight to current midnight.
    """
    try:

        now = timezone.now()
        today_midnight = now
        yesterday_midnight = today_midnight - timedelta(days=1, minutes=30)
        
        records = BalanceRecord.objects.filter(
            timestamp__gte=yesterday_midnight,
            timestamp__lte=today_midnight
        ).order_by('timestamp')
        
        if not records.exists():
            message = "📊 Daily Unrealized Trade Balance Report\n\n"
            message += "❌ No data available for the past 24 hours."
            send_bot_message(message)
            return
        
        first_record = records.first()
        last_record = records.last()
        
        
        unrealized_trade_change = last_record.unrealized_trade_balance - first_record.unrealized_trade_balance
        
        message = "📊 Daily Change Balance Report\n\n"
        
        message += f"💰 Current: ${last_record.unrealized_trade_balance:,.2f}\n"
        change_percent = (unrealized_trade_change / first_record.unrealized_trade_balance) * 100 if first_record.unrealized_trade_balance != 0 else 0

        if unrealized_trade_change > 0:
            trend_emoji = "📈"
        elif unrealized_trade_change < 0:
            trend_emoji = "📉"
        else:   
            trend_emoji = "➡️"

        message += f"{trend_emoji} 24h Change: {format_change(unrealized_trade_change)} ({change_percent:+.2f}%)\n\n"


        chart_buffer = create_daily_balance_chart(records, yesterday_midnight, now)
        if chart_buffer:

            send_bot_photo(chart_buffer, caption=message)
            logger.info(f"Daily unrealized trade balance report with chart sent successfully at {now}")
        else:

            send_bot_message(message)
            logger.warning(f"Chart creation failed, sent text-only report at {now}")

    except Exception as e:
        error_message = f"❌ Error generating daily report: {str(e)}"
        logger.error(error_message)
        try:
            send_bot_message(error_message)
        except:
            pass


@shared_task
def send_weekly_balance_report():
    """
    Send weekly unrealized trade balance report via Telegram at midnight.
    Shows changes from the previous midnight to current midnight.
    """
    try:

        now = timezone.now()
        today_midnight = now
        last_week_midnight = today_midnight - timedelta(days=7, minutes=30)

        records = BalanceRecord.objects.filter(
            timestamp__gte=last_week_midnight,
            timestamp__lte=today_midnight
        ).order_by('timestamp')
        
        if not records.exists():
            message = "📊 Weekly Unrealized Trade Balance Report\n\n"
            message += "❌ No data available for the past week."
            send_bot_message(message)
            return
        
        first_record = records.first()
        last_record = records.last()
        
        
        unrealized_trade_change = last_record.unrealized_trade_balance - first_record.unrealized_trade_balance
        
        message = "📊 Weekly Change Balance Report\n\n"
        
        message += f"💰 Current: ${last_record.unrealized_trade_balance:,.2f}\n"
        change_percent = (unrealized_trade_change / first_record.unrealized_trade_balance) * 100 if first_record.unrealized_trade_balance != 0 else 0

        if unrealized_trade_change > 0:
            trend_emoji = "📈"
        elif unrealized_trade_change < 0:
            trend_emoji = "📉"
        else:   
            trend_emoji = "➡️"

        message += f"{trend_emoji} 7d Change: {format_change(unrealized_trade_change)} ({change_percent:+.2f}%)\n\n"


        chart_buffer = create_weekly_balance_chart(records, last_week_midnight, now)
        if chart_buffer:

            send_bot_photo(chart_buffer, caption=message)
            logger.info(f"Weekly unrealized trade balance report with chart sent successfully at {now}")
        else:

            send_bot_message(message)
            logger.warning(f"Chart creation failed, sent text-only report at {now}")

    except Exception as e:
        error_message = f"❌ Error generating daily report: {str(e)}"
        logger.error(error_message)
        try:
            send_bot_message(error_message)
        except:
            pass
