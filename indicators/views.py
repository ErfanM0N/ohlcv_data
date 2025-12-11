from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from datetime import timedelta
from asset.models import Asset
from ohlc.models import Candle15M, Candle1H, Candle4H, Candle1D
from indicators import utils
import inspect


TIMEFRAME_MODEL_MAP = {
    '15m': Candle15M,
    '1h': Candle1H,
    '4h': Candle4H,
    '1d': Candle1D,
}

TIMEFRAME_DELTA_MAP = {
    '15m': timedelta(minutes=15),
    '1h': timedelta(hours=1),
    '4h': timedelta(hours=4),
    '1d': timedelta(days=1),
}

INDICATOR_DEFAULTS = {
    'sma': 14,
    'ema': 14,
    'rsi': 14,
    'macd': 34,           # Special: needs 26 + 9 - 1
    'bollinger_bands': 20,
    'stochastic': 14,  # Special: needs %K period + %D period - 1
    'atr': 14,
    'obv': 1,
    'adx': 14,
    'cci': 20,
    'vwap': 1,
}


@api_view(['GET'])
def calculate_indicator(request):
    """
    GET endpoint to calculate technical indicators
    
    Query Parameters:
    - symbol: Asset symbol (required)
    - start: Start timestamp (required, ISO format)
    - end: End timestamp (optional, defaults to now)
    - indicator: Indicator name (required)
    - timeframe: Timeframe - 15m, 1h, 4h, or 1d (required)
    - period: Number used in indicator calculation (optional, default varies by indicator)
    """
    
    # Get and validate query parameters
    symbol = request.query_params.get('symbol')
    start = request.query_params.get('start')
    end = request.query_params.get('end')
    indicator_name = request.query_params.get('indicator')
    timeframe = request.query_params.get('timeframe')
    period = request.query_params.get('period', '-1')  # Default to -1 to use indicator default
    
    # Validate required parameters
    if not all([symbol, start, indicator_name, timeframe]):
        return Response(
            {'error': 'Missing required parameters: symbol, start, indicator, timeframe'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate timeframe
    if timeframe not in TIMEFRAME_MODEL_MAP:
        return Response(
            {'error': f'Invalid timeframe. Must be one of: {", ".join(TIMEFRAME_MODEL_MAP.keys())}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Parse timestamps
    try:
        start_dt = parse_datetime(start)
        if not start_dt:
            raise ValueError("Invalid start datetime format")
        
        # If end not provided, use current time
        if end:
            end_dt = parse_datetime(end)
            if not end_dt:
                raise ValueError("Invalid end datetime format")
        else:
            end_dt = timezone.now()
            
    except Exception as e:
        return Response(
            {'error': f'Invalid timestamp format. Use ISO format (e.g., 2024-01-01T00:00:00Z): {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get period value for calculating lookback
    try:
        period_int = int(period) if period != '-1' else int(INDICATOR_DEFAULTS.get(indicator_name, 14))  # default period
    except ValueError:
        return Response(
            {'error': 'Period must be a valid integer'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if indicator_name == 'macd':
        # MACD needs a longer lookback: 26 + 9 - 1 = 34
        period_int = max(period_int, 34)
    
    # Calculate adjusted start time (period units before start)
    timeframe_delta = TIMEFRAME_DELTA_MAP[timeframe]
    adjusted_start = start_dt - (timeframe_delta * period_int)

    if indicator_name == 'stochastic':
        # Stochastic needs an additional period for %D
        adjusted_start -= timeframe_delta * (3 - 1)  # assuming %D period is 3
    elif indicator_name == 'adx':
        # ADX needs double the period
        adjusted_start -= timeframe_delta * (period_int) # additional period
    
    # Calculate adjusted end time (one unit before end)
    adjusted_end = end_dt - timeframe_delta
    
    # Check if indicator function exists in utils
    if not hasattr(utils, indicator_name):
        return Response(
            {'error': f'No indicator with name: {indicator_name}'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    indicator_func = getattr(utils, indicator_name)
    
    # Verify it's actually a function
    if not callable(indicator_func):
        return Response(
            {'error': f'{indicator_name} is not a valid indicator function'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get the asset
    try:
        asset = Asset.objects.get(symbol=symbol)
    except Asset.DoesNotExist:
        return Response(
            {'error': f'Asset with symbol {symbol} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get candles based on timeframe
    CandleModel = TIMEFRAME_MODEL_MAP[timeframe]
    candles = CandleModel.objects.filter(
        symbol=asset,
        timestamp__gte=adjusted_start,
        timestamp__lte=adjusted_end
    ).order_by('timestamp')
    
    if not candles.exists():
        return Response(
            {'error': 'No candles found for the specified time range'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Convert candles to list of dicts for easier processing
    candles_data = list(candles.values(
        'timestamp', 'open', 'high', 'low', 'close', 'volume'
    ))
    
    # Call the indicator function
    try:
        # Check if the function accepts a period parameter
        sig = inspect.signature(indicator_func)
        if 'period' in sig.parameters and int(period) != 0:
            result = indicator_func(candles_data, period=period_int)
        else:
            result = indicator_func(candles_data)
            
    except Exception as e:
        return Response(
            {'error': f'Error calculating indicator: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({
        'symbol': symbol,
        'timeframe': timeframe,
        'indicator': indicator_name,
        'start': start,
        'end': end if end else end_dt.isoformat(),
        'period': period_int,
        'candles_fetched': len(candles_data),
        'result': result
    }, status=status.HTTP_200_OK)