"""
Popular technical indicator calculation functions.
Each function accepts candles_data (list of dicts) and optional parameters.
"""


def sma(candles_data, period=14):
    """
    Simple Moving Average
    
    Args:
        candles_data: List of candle dicts with 'close' field
        period: Number of periods for the average
    
    Returns:
        List of SMA values
    """
    if len(candles_data) < period:
        return {'error': f'Insufficient data. Need at least {period} candles'}
    
    sma_values = []
    closes = [float(candle['close']) for candle in candles_data]
    
    for i in range(period - 1, len(closes)):
        sma = sum(closes[i - period + 1:i + 1]) / period
        sma_values.append({
            'timestamp': candles_data[i]['timestamp'],
            'value': round(sma, 8)
        })
    
    return sma_values


def ema(candles_data, period=14):
    """
    Exponential Moving Average
    
    Args:
        candles_data: List of candle dicts with 'close' field
        period: Number of periods for the average
    
    Returns:
        List of EMA values
    """
    if len(candles_data) < period:
        return {'error': f'Insufficient data. Need at least {period} candles'}
    
    closes = [float(candle['close']) for candle in candles_data]
    multiplier = 2 / (period + 1)
    
    # Calculate initial SMA
    ema_value = sum(closes[:period]) / period
    ema_values = [{
        'timestamp': candles_data[period - 1]['timestamp'],
        'value': round(ema_value, 8)
    }]
    
    # Calculate EMA for remaining values
    for i in range(period, len(closes)):
        ema_value = (closes[i] - ema_value) * multiplier + ema_value
        ema_values.append({
            'timestamp': candles_data[i]['timestamp'],
            'value': round(ema_value, 8)
        })
    
    return ema_values


def rsi(candles_data, period=14):
    """
    Relative Strength Index
    
    Args:
        candles_data: List of candle dicts with 'close' field
        period: Number of periods for RSI calculation
    
    Returns:
        List of RSI values (0-100)
    """
    if len(candles_data) < period + 1:
        return {'error': f'Insufficient data. Need at least {period + 1} candles'}
    
    closes = [float(candle['close']) for candle in candles_data]
    
    # Calculate price changes
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]
    
    # Calculate initial averages
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    rsi_values = []
    
    for i in range(period, len(deltas)):
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append({
            'timestamp': candles_data[i + 1]['timestamp'],
            'value': round(rsi, 2)
        })
        
        # Update averages
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    return rsi_values


def macd(candles_data, period=12):
    """
    MACD (Moving Average Convergence Divergence)
    Uses fast=12, slow=26, signal=9 by default
    
    Args:
        candles_data: List of candle dicts with 'close' field
        period: Not used, kept for consistency (uses standard 12/26/9)
    
    Returns:
        List of dicts with macd, signal, and histogram values
    """
    fast_period = 12
    slow_period = 26
    signal_period = 9
    
    if len(candles_data) < slow_period + signal_period:
        return {'error': f'Insufficient data. Need at least {slow_period + signal_period} candles'}
    
    closes = [float(candle['close']) for candle in candles_data]
    
    # Calculate fast EMA
    fast_multiplier = 2 / (fast_period + 1)
    fast_ema = sum(closes[:fast_period]) / fast_period
    fast_emas = [fast_ema]
    
    for i in range(fast_period, len(closes)):
        fast_ema = (closes[i] - fast_ema) * fast_multiplier + fast_ema
        fast_emas.append(fast_ema)
    
    # Calculate slow EMA
    slow_multiplier = 2 / (slow_period + 1)
    slow_ema = sum(closes[:slow_period]) / slow_period
    slow_emas = [slow_ema]
    
    for i in range(slow_period, len(closes)):
        slow_ema = (closes[i] - slow_ema) * slow_multiplier + slow_ema
        slow_emas.append(slow_ema)
    
    # Calculate MACD line
    macd_line = []
    start_idx = slow_period - fast_period
    for i in range(len(slow_emas)):
        macd_val = fast_emas[start_idx + i] - slow_emas[i]
        macd_line.append(macd_val)
    
    # Calculate signal line (EMA of MACD)
    signal_multiplier = 2 / (signal_period + 1)
    signal_ema = sum(macd_line[:signal_period]) / signal_period
    
    macd_values = []
    for i in range(signal_period - 1, len(macd_line)):
        if i == signal_period - 1:
            signal_val = signal_ema
        else:
            signal_ema = (macd_line[i] - signal_ema) * signal_multiplier + signal_ema
            signal_val = signal_ema
        
        histogram = macd_line[i] - signal_val
        
        macd_values.append({
            'timestamp': candles_data[slow_period + i]['timestamp'],
            'macd': round(macd_line[i], 8),
            'signal': round(signal_val, 8),
            'histogram': round(histogram, 8)
        })
    
    return macd_values


def bollinger_bands(candles_data, period=20):
    """
    Bollinger Bands (uses 2 standard deviations)
    
    Args:
        candles_data: List of candle dicts with 'close' field
        period: Number of periods for the moving average
    
    Returns:
        List of dicts with upper, middle, and lower band values
    """
    if len(candles_data) < period:
        return {'error': f'Insufficient data. Need at least {period} candles'}
    
    closes = [float(candle['close']) for candle in candles_data]
    bb_values = []
    std_dev = 2
    
    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1:i + 1]
        sma = sum(window) / period
        
        # Calculate standard deviation
        variance = sum((x - sma) ** 2 for x in window) / period
        std = variance ** 0.5
        
        bb_values.append({
            'timestamp': candles_data[i]['timestamp'],
            'upper': round(sma + (std_dev * std), 8),
            'middle': round(sma, 8),
            'lower': round(sma - (std_dev * std), 8)
        })
    
    return bb_values


def stochastic(candles_data, period=14):
    """
    Stochastic Oscillator (%K and %D)
    
    Args:
        candles_data: List of candle dicts with 'high', 'low', 'close' fields
        period: Number of periods (default 14)
    
    Returns:
        List of dicts with %K and %D values
    """
    if len(candles_data) < period + 3:
        return {'error': f'Insufficient data. Need at least {period + 3} candles'}
    
    stoch_values = []
    k_values = []
    
    for i in range(period - 1, len(candles_data)):
        window = candles_data[i - period + 1:i + 1]
        
        highest_high = max(float(candle['high']) for candle in window)
        lowest_low = min(float(candle['low']) for candle in window)
        current_close = float(candles_data[i]['close'])
        
        if highest_high == lowest_low:
            k = 50
        else:
            k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        k_values.append(k)
        
        # Calculate %D (3-period SMA of %K)
        if len(k_values) >= 3:
            d = sum(k_values[-3:]) / 3
            stoch_values.append({
                'timestamp': candles_data[i]['timestamp'],
                'k': round(k, 2),
                'd': round(d, 2)
            })
    
    return stoch_values


def atr(candles_data, period=14):
    """
    Average True Range
    
    Args:
        candles_data: List of candle dicts with 'high', 'low', 'close' fields
        period: Number of periods
    
    Returns:
        List of ATR values
    """
    if len(candles_data) < period + 1:
        return {'error': f'Insufficient data. Need at least {period + 1} candles'}
    
    true_ranges = []
    
    for i in range(1, len(candles_data)):
        high = float(candles_data[i]['high'])
        low = float(candles_data[i]['low'])
        prev_close = float(candles_data[i - 1]['close'])
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    # Calculate initial ATR (simple average)
    atr_value = sum(true_ranges[:period]) / period
    atr_values = [{
        'timestamp': candles_data[period]['timestamp'],
        'value': round(atr_value, 8)
    }]
    
    # Calculate smoothed ATR
    for i in range(period, len(true_ranges)):
        atr_value = (atr_value * (period - 1) + true_ranges[i]) / period
        atr_values.append({
            'timestamp': candles_data[i + 1]['timestamp'],
            'value': round(atr_value, 8)
        })
    
    return atr_values


def obv(candles_data, period=1):
    """
    On-Balance Volume
    
    Args:
        candles_data: List of candle dicts with 'close' and 'volume' fields
        period: Not used, kept for consistency
    
    Returns:
        List of OBV values
    """
    if len(candles_data) < 2:
        return {'error': 'Insufficient data. Need at least 2 candles'}
    
    obv_value = 0
    obv_values = []
    
    for i in range(len(candles_data)):
        if i == 0:
            obv_value = float(candles_data[i]['volume'])
        else:
            current_close = float(candles_data[i]['close'])
            prev_close = float(candles_data[i - 1]['close'])
            volume = float(candles_data[i]['volume'])
            
            if current_close > prev_close:
                obv_value += volume
            elif current_close < prev_close:
                obv_value -= volume
        
        obv_values.append({
            'timestamp': candles_data[i]['timestamp'],
            'value': round(obv_value, 2)
        })
    
    return obv_values


def adx(candles_data, period=14):
    """
    Average Directional Index
    
    Args:
        candles_data: List of candle dicts with 'high', 'low', 'close' fields
        period: Number of periods
    
    Returns:
        List of dicts with ADX, +DI, and -DI values
    """
    if len(candles_data) < period * 2:
        return {'error': f'Insufficient data. Need at least {period * 2} candles'}
    
    # Calculate True Range and Directional Movement
    tr_list = []
    plus_dm_list = []
    minus_dm_list = []
    
    for i in range(1, len(candles_data)):
        high = float(candles_data[i]['high'])
        low = float(candles_data[i]['low'])
        prev_high = float(candles_data[i - 1]['high'])
        prev_low = float(candles_data[i - 1]['low'])
        prev_close = float(candles_data[i - 1]['close'])
        
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_list.append(tr)
        
        plus_dm = high - prev_high if high - prev_high > prev_low - low and high - prev_high > 0 else 0
        minus_dm = prev_low - low if prev_low - low > high - prev_high and prev_low - low > 0 else 0
        
        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)
    
    # Calculate smoothed values
    atr_value = sum(tr_list[:period]) / period
    plus_di_value = sum(plus_dm_list[:period]) / period
    minus_di_value = sum(minus_dm_list[:period]) / period
    
    adx_values = []
    dx_values = []
    
    for i in range(period, len(tr_list)):
        atr_value = (atr_value * (period - 1) + tr_list[i]) / period
        plus_di_value = (plus_di_value * (period - 1) + plus_dm_list[i]) / period
        minus_di_value = (minus_di_value * (period - 1) + minus_dm_list[i]) / period
        
        plus_di = (plus_di_value / atr_value) * 100 if atr_value != 0 else 0
        minus_di = (minus_di_value / atr_value) * 100 if atr_value != 0 else 0
        
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100 if (plus_di + minus_di) != 0 else 0
        dx_values.append(dx)
        
        if len(dx_values) >= period:
            adx = sum(dx_values[-period:]) / period
            adx_values.append({
                'timestamp': candles_data[i + 1]['timestamp'],
                'adx': round(adx, 2),
                'plus_di': round(plus_di, 2),
                'minus_di': round(minus_di, 2)
            })
    
    return adx_values


def cci(candles_data, period=20):
    """
    Commodity Channel Index
    
    Args:
        candles_data: List of candle dicts with 'high', 'low', 'close' fields
        period: Number of periods
    
    Returns:
        List of CCI values
    """
    if len(candles_data) < period:
        return {'error': f'Insufficient data. Need at least {period} candles'}
    
    cci_values = []
    
    for i in range(period - 1, len(candles_data)):
        window = candles_data[i - period + 1:i + 1]
        
        # Calculate Typical Price
        typical_prices = [
            (float(c['high']) + float(c['low']) + float(c['close'])) / 3
            for c in window
        ]
        
        sma_tp = sum(typical_prices) / period
        current_tp = typical_prices[-1]
        
        # Calculate Mean Deviation
        mean_deviation = sum(abs(tp - sma_tp) for tp in typical_prices) / period
        
        if mean_deviation == 0:
            cci = 0
        else:
            cci = (current_tp - sma_tp) / (0.015 * mean_deviation)
        
        cci_values.append({
            'timestamp': candles_data[i]['timestamp'],
            'value': round(cci, 2)
        })
    
    return cci_values


def vwap(candles_data, period=1):
    """
    Volume Weighted Average Price
    Calculates cumulative VWAP from the start of the data
    
    Args:
        candles_data: List of candle dicts with 'high', 'low', 'close', 'volume' fields
        period: Not used, kept for consistency
    
    Returns:
        List of VWAP values
    """
    if len(candles_data) < 1:
        return {'error': 'Insufficient data. Need at least 1 candle'}
    
    cumulative_tp_volume = 0
    cumulative_volume = 0
    vwap_values = []
    
    for candle in candles_data:
        typical_price = (float(candle['high']) + float(candle['low']) + float(candle['close'])) / 3
        volume = float(candle['volume'])
        
        cumulative_tp_volume += typical_price * volume
        cumulative_volume += volume
        
        if cumulative_volume == 0:
            vwap = typical_price
        else:
            vwap = cumulative_tp_volume / cumulative_volume
        
        vwap_values.append({
            'timestamp': candle['timestamp'],
            'value': round(vwap, 8)
        })
    
    return vwap_values