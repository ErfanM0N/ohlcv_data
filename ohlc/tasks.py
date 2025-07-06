import logging
from celery import shared_task
from binance import Client
from decouple import config
from ohlc.models import Candle15M, Candle1H, Candle4H, Candle1D
from datetime import datetime, timezone
from asset.models import Asset
from decimal import Decimal

logger = logging.getLogger(__name__)


@shared_task
def update_15minute_ohlc(limit=5):
    api_key = config('BINANCE_API_KEY')
    secret_key = config('BINANCE_SECRET_KEY')


    client = Client(api_key=api_key, api_secret=secret_key)

    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_time = now - (limit * 15 * 60 * 1000)

    assets = Asset.objects.filter(enable=True)

    for asset in assets:
        try:
            data = client.get_klines(
            symbol=asset.symbol.upper(),
            interval=Client.KLINE_INTERVAL_15MINUTE,
            startTime=start_time,
            endTime=now,
            limit=limit
            )

            candles = []
            for d in data:
                timestamp = datetime.fromtimestamp(d[0] / 1000, tz=timezone.utc)
                candles.append(Candle15M(
                    symbol=asset,
                    timestamp=timestamp,
                    open=Decimal(d[1]),
                    high=Decimal(d[2]),
                    low=Decimal(d[3]),
                    close=Decimal(d[4]),
                    volume=Decimal(d[5])
                ))

            Candle15M.objects.bulk_create(
                candles,
                update_conflicts=True,
                update_fields=['open', 'high', 'low', 'close', 'volume'],
                unique_fields=['symbol', 'timestamp']
            )

        except Exception as e:
            logger.exception(f"An error occurred while updating 15m candles for {asset.symbol}: {e}")
    

@shared_task
def update_1hour_ohlc(limit=5):
    api_key = config('BINANCE_API_KEY')
    secret_key = config('BINANCE_SECRET_KEY')

    client = Client(api_key=api_key, api_secret=secret_key)

    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_time = now - (limit * 60 * 60 * 1000)

    assets = Asset.objects.filter(enable=True)

    for asset in assets:
        try:
            data = client.get_klines(
            symbol=asset.symbol.upper(),
            interval=Client.KLINE_INTERVAL_1HOUR,
            startTime=start_time,
            endTime=now,
            limit=limit
            )

            candles = []
            for d in data:
                timestamp = datetime.fromtimestamp(d[0] / 1000, tz=timezone.utc)
                candles.append(Candle1H(
                    symbol=asset,
                    timestamp=timestamp,
                    open=Decimal(d[1]),
                    high=Decimal(d[2]),
                    low=Decimal(d[3]),
                    close=Decimal(d[4]),
                    volume=Decimal(d[5])
                ))

            Candle1H.objects.bulk_create(
                candles,
                update_conflicts=True,
                update_fields=['open', 'high', 'low', 'close', 'volume'],
                unique_fields=['symbol', 'timestamp']
            )

        except Exception as e:
            logger.exception(f"An error occurred while updating 1h candles for {asset.symbol}: {e}")
    


@shared_task
def update_4hour_ohlc(limit=5):
    api_key = config('BINANCE_API_KEY')
    secret_key = config('BINANCE_SECRET_KEY')

    client = Client(api_key=api_key, api_secret=secret_key)

    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_time = now - (limit * 4 * 60 * 60 * 1000)

    assets = Asset.objects.filter(enable=True)

    for asset in assets:
        try:
            data = client.get_klines(
            symbol=asset.symbol.upper(),
            interval=Client.KLINE_INTERVAL_4HOUR,
            startTime=start_time,
            endTime=now,
            limit=limit
            )

            candles = []
            for d in data:
                timestamp = datetime.fromtimestamp(d[0] / 1000, tz=timezone.utc)
                candles.append(Candle4H(
                    symbol=asset,
                    timestamp=timestamp,
                    open=Decimal(d[1]),
                    high=Decimal(d[2]),
                    low=Decimal(d[3]),
                    close=Decimal(d[4]),
                    volume=Decimal(d[5])
                ))

            Candle4H.objects.bulk_create(
                candles,
                update_conflicts=True,
                update_fields=['open', 'high', 'low', 'close', 'volume'],
                unique_fields=['symbol', 'timestamp']
            )
            

        except Exception as e:
            logger.exception(f"An error occurred while updating 4h candles for {asset.symbol}: {e}")
    

@shared_task
def update_1day_ohlc(limit=5):
    api_key = config('BINANCE_API_KEY')
    secret_key = config('BINANCE_SECRET_KEY')

    client = Client(api_key=api_key, api_secret=secret_key)

    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_time = now - (limit * 24 * 60 * 60 * 1000)

    assets = Asset.objects.filter(enable=True)

    for asset in assets:
        try:
            data = client.get_klines(
            symbol=asset.symbol.upper(),
            interval=Client.KLINE_INTERVAL_1DAY,
            startTime=start_time,
            endTime=now,
            limit=limit
            )

            candles = []
            for d in data:
                timestamp = datetime.fromtimestamp(d[0] / 1000, tz=timezone.utc)
                candles.append(Candle1D(
                    symbol=asset,
                    timestamp=timestamp,
                    open=Decimal(d[1]),
                    high=Decimal(d[2]),
                    low=Decimal(d[3]),
                    close=Decimal(d[4]),
                    volume=Decimal(d[5])
                ))

            Candle1D.objects.bulk_create(
                candles,
                update_conflicts=True,
                update_fields=['open', 'high', 'low', 'close', 'volume'],
                unique_fields=['symbol', 'timestamp']
            )

        except Exception as e:
            logger.exception(f"An error occurred while updating 1d candles for {asset.symbol}: {e}")
    