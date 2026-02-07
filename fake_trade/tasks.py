from celery import shared_task
import logging
from django.utils import timezone
from .models import DemoConfig, DemoPosition
from .utils import send_telegram_message, fetch_last_prices
from decimal import Decimal

logger = logging.getLogger(__name__)

@shared_task
def fill_pending_positions():
    """
    Fill all pending DemoPositions using the latest price from Binance API.
    Updates positions to OPEN and sends formatted Telegram message.
    """
    try:
        # 1. Fetch Prices
        prices = fetch_last_prices()
        if not prices:
            # fetch_last_prices handles the Telegram alert internally
            return

        # 2. Get Config
        config = DemoConfig.objects.first()
        if not config:
            msg = "❌ *Configuration Error*\nDemoConfig object not found in database."
            logger.error("DemoConfig not found.")
            send_telegram_message(msg)
            return

        # 3. Get Pending Positions
        pending_positions = DemoPosition.objects.filter(status='PENDING')

        for position in pending_positions:
            symbol = position.asset.symbol.upper()
            
            # Escape underscore for Telegram Markdown (e.g. 1000_SHIB -> 1000\_SHIB)
            safe_symbol = symbol.replace('_', '\\_')
            
            last_price = prices.get(symbol)

            if last_price is None:
                # Optional: Alert if a specific symbol is missing from API
                logger.warning(f"Price for {symbol} not found in API response.")
                continue


            should_fill = False
            if position.side == "BUY" and last_price <= float(position.entry_price):
                should_fill = True
            elif position.side == "SELL" and last_price >= float(position.entry_price):
                should_fill = True

            # 5. Execute Fill
            if should_fill:
                position.status = 'OPEN'
                position.entry_time = timezone.now()
                position.save()

                side_icon = "🟢" if position.side == "BUY" else "🔴"
                
                msg = (
                    f"{side_icon} *Position Filled*\n"
                    f"*Position ID:* `{position.id}`\n"
                    f"*Symbol:* {safe_symbol}\n"
                    f"*Side:* {position.side.upper()}\n"
                    f"*Quantity:* {position.quantity}\n"
                    f"*Fill Price:* {position.entry_price}\n"
                    f"*Margin:* {position.margin_balance}\n"
                    f"*Available Balance:* {config.available_balance}"
                )
                    
                logger.info(f"Filled position {position.id} for {symbol}")
                send_telegram_message(msg)

    except Exception as e:
        # Catch unexpected crashes in the loop or DB logic
        error_msg = f"⚠️ *TASK CRASHED*\nError in `fill_pending_positions`:\n`{str(e)}`"
        logger.error(error_msg)
        send_telegram_message(error_msg)


@shared_task
def close_open_positions():
    """
    Check all OPEN positions. 
    If price hits Stop Loss (SL) or Take Profit (TP):
    1. Close the position.
    2. Calculate Commission (0.05% entry + 0.05% exit).
    3. Calculate PnL.
    4. Update User Balance.
    5. Send Telegram Alert.
    """
    try:
        # 1. Fetch Latest Prices
        prices = fetch_last_prices()
        if not prices:
            # fetch_last_prices handles the specific Telegram alert
            return

        # 2. Get Config (Needed for balance updates)
        config = DemoConfig.objects.first()
        if not config:
            msg = "❌ *Configuration Error*\nDemoConfig object not found. Cannot close positions."
            logger.error(msg)
            send_telegram_message(msg)
            return

        # 3. Get Open Positions
        open_positions = DemoPosition.objects.filter(status='OPEN')

        for position in open_positions:
            symbol = position.asset.symbol.upper()
            safe_symbol = symbol.replace('_', '\\_') # Escape for Telegram
            
            current_price = prices.get(symbol)

            if current_price is None:
                continue

            # --- Logic to Determine Exit ---
            exit_triggered = False
            exit_reason = "" # "TP" or "SL"
            
            # Convert DB floats to native python types for comparison
            entry_price = float(position.entry_price)
            tp = float(position.take_profit)
            sl = float(position.stop_loss)
            qty = float(position.quantity)

            if position.side == "BUY":
                # Long: Profit if price goes UP, Loss if price goes DOWN
                if current_price >= tp:
                    exit_triggered = True
                    exit_reason = "TP"
                elif current_price <= sl:
                    exit_triggered = True
                    exit_reason = "SL"
            
            elif position.side == "SELL":
                # Short: Profit if price goes DOWN, Loss if price goes UP
                if current_price <= tp:
                    exit_triggered = True
                    exit_reason = "TP"
                elif current_price >= sl:
                    exit_triggered = True
                    exit_reason = "SL"

            # --- Execute Closing Logic ---
            if exit_triggered:
                # 1. Calculate Values
                entry_value = qty * entry_price

                if exit_reason == "TP":
                    exit_price = tp
                else:
                    exit_price = sl

                exit_value = qty * exit_price

                # 2. Calculate Commission (0.05% per side)
                # 0.05% = 0.0005
                commission_rate = 0.0005
                entry_comm = entry_value * commission_rate
                exit_comm = exit_value * commission_rate
                total_commission = entry_comm + exit_comm

                # 3. Calculate Gross PnL
                gross_pnl = exit_value - entry_value
                
                # 4. Net PnL (Gross - Commission)
                net_pnl = gross_pnl - total_commission

                # 5. Update Position Model
                position.status = 'CLOSED'
                position.exit_price = exit_price
                position.exit_time = timezone.now()
                position.commission = total_commission
                position.pnl = net_pnl
                position.save()

                # 6. Update User Balance
                # Logic: We return the locked margin, then add the Net PnL.
                # (If PnL is negative, it subtracts from the total).
                
                # Convert to Decimal for financial math with Django models
                margin_release = Decimal(position.margin_balance)
                pnl_decimal = Decimal(f"{net_pnl:.2f}")

                config.available_balance += margin_release + pnl_decimal
                config.balance += pnl_decimal # Total equity changes by PnL
                config.save()

                # 7. Send Telegram Message
                
                # Pick Emoji
                if exit_reason == "TP":
                    header_icon = "🚀 *Take Profit Hit*"
                else:
                    header_icon = "🛑 *Stop Loss Hit*"

                # PnL Icon
                pnl_icon = "🤑" if net_pnl > 0 else "🔻"

                msg = (
                    f"{header_icon}\n"
                    f"*Position ID:* `{position.id}`\n"
                    f"*Symbol:* {safe_symbol}\n"
                    f"*Side:* {position.side}\n"
                    f"*Entry:* {entry_price}\n"
                    f"*Exit:* {exit_price}\n"
                    f"*Gross PnL:* {gross_pnl:.2f}\n"
                    f"*Comm (0.1%):* -{total_commission:.2f}\n"
                    f"-----------------------------\n"
                    f"{pnl_icon} *Net PnL:* {net_pnl:.2f}\n"
                    f"-----------------------------\n"
                    f"*New Balance:* {config.available_balance}"
                )
                
                logger.info(f"Closed position {position.id} ({exit_reason}) for {symbol}. PnL: {net_pnl}")
                send_telegram_message(msg)

    except Exception as e:
        error_msg = f"⚠️ *TASK CRASHED*\nError in `check_and_close_positions`:\n`{str(e)}`"
        logger.error(error_msg)
        send_telegram_message(error_msg)