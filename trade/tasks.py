from celery import shared_task
from trade.utils import send_bot_message, get_balance, get_spot_balance
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