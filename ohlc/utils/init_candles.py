import logging
from ohlc.models import Candle15M, Candle1H, Candle4H, Candle1D
from binance import Client
from decouple import config
from datetime import datetime, timezone
from django.db import transaction
from asset.models import Asset
from decimal import Decimal

logger = logging.getLogger(__name__)


def initialize_candles(asset: Asset):
    api_key = config('BINANCE_API_KEY')
    secret_key = config('BINANCE_SECRET_KEY')

    client = Client(api_key=api_key, api_secret=secret_key)

    try:
        with transaction.atomic():
            init_15m_candles(client=client, asset=asset)

            init_1h_candles(client=client, asset=asset)

            init_4h_candles(client=client, asset=asset)

            init_1d_candles(client=client, asset=asset)

    except Exception as e:
        logger.exception(f"An error occurred while fill asset {asset.symbol}: {e}")


def init_15m_candles(client: Client, asset: Asset, from_year: int = 2025, from_month: int = 12, from_day: int = 10):
    start_time = int(datetime(from_year, from_month, from_day, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)

    # 15 min candles, 1000 as limit, 60 to convert min to sec and 1000 to convert sec to msec
    converter_coef = 15 * 1000 * 60 * 1000

    end_time = start_time + converter_coef

    now = int(datetime.now(timezone.utc).timestamp() * 1000)

    while start_time < now:
        data = client.get_klines(
            symbol=asset.symbol.upper(),
            interval=Client.KLINE_INTERVAL_15MINUTE,
            startTime=start_time,
            endTime=end_time,
            limit=1000
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

        start_time = end_time
        end_time += converter_coef


def init_1h_candles(client: Client, asset: Asset, from_year: int = 2025, from_month: int = 12, from_day: int = 10):
    start_time = int(datetime(from_year, from_month, from_day, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)

    # 60 min candles, 1000 as limit, 60 to convert min to sec and 1000 to convert sec to msec
    converter_coef = 60 * 1000 * 60 * 1000

    end_time = start_time + converter_coef

    now = int(datetime.now(timezone.utc).timestamp() * 1000)

    while start_time < now:
        data = client.get_klines(
            symbol=asset.symbol.upper(),
            interval=Client.KLINE_INTERVAL_1HOUR,
            startTime=start_time,
            endTime=end_time,
            limit=1000
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


        start_time = end_time
        end_time += converter_coef


def init_4h_candles(client: Client, asset: Asset, from_year: int = 2025, from_month: int = 12, from_day: int = 10):
    start_time = int(datetime(from_year, from_month, from_day, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)

    # 4 * 60 min candles, 1000 as limit, 60 to convert min to sec and 1000 to convert sec to msec
    converter_coef = 4 * 60 * 1000 * 60 * 1000

    end_time = start_time + converter_coef

    now = int(datetime.now(timezone.utc).timestamp() * 1000)

    while start_time < now:
        data = client.get_klines(
            symbol=asset.symbol.upper(),
            interval=Client.KLINE_INTERVAL_4HOUR,
            startTime=start_time,
            endTime=end_time,
            limit=1000
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

        start_time = end_time
        end_time += converter_coef


def init_1d_candles(client: Client, asset: Asset, from_year: int = 2025, from_month: int = 12, from_day: int = 10):
    start_time = int(datetime(from_year, from_month, from_day, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)

    # 24 * 60 min candles, 1000 as limit, 60 to convert min to sec and 1000 to convert sec to msec
    converter_coef = 24 * 60 * 1000 * 60 * 1000

    end_time = start_time + converter_coef

    now = int(datetime.now(timezone.utc).timestamp() * 1000)

    while start_time < now:
        data = client.get_klines(
            symbol=asset.symbol.upper(),
            interval=Client.KLINE_INTERVAL_1DAY,
            startTime=start_time,
            endTime=end_time,
            limit=1000
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

        start_time = end_time
        end_time += converter_coef
