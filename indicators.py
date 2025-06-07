import numpy as np
from config import TREND_TOLERANCE, SWINGS_LOOK_BACK, SWING_RANGE, ATR_MULT
import pandas as pd
from scipy.signal import argrelextrema


def add_indicators(df):
    df = df.copy()
    df = add_rsi(df)
    df = add_stochastic(df)
    df = add_bollinger_bands(df)
    df = add_bollinger_position(df)
    df = add_volume_change(df)
    df = add_macd(df)
    df = add_atr(df)
    df = add_short_rsi_indicator(df)
    df = add_rsi_confirmations(df)
    return df


def normalize_indicators(df):
    # Bounded indicators
    for col in ["rsi", "stoch_k", "stoch_d", "bollinger_position"]:
        df[col] = df[col] / 100.0

    # Unbounded indicators
    for col in ["macd", "macd_signal", "bollinger_width", "volume_change"]:
        mean, std = df[col].mean(), df[col].std()
        df[col] = (df[col] - mean) / (std + 1e-8)

    return df

def add_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["macd_histogram"] = df["macd"] - df["macd_signal"]
    return df



def add_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = -delta.clip(upper=0).rolling(window=period).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    return df


def add_short_rsi_indicator(df, period=5):
    df = df.copy()

    # Calculate 5-day RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = -delta.clip(upper=0).rolling(window=period).mean()
    rs = gain / loss
    df["rsi_5"] = 100 - (100 / (1 + rs))

    # 20-day moving average
    df["ma_20"] = df["close"].rolling(20).mean()

    # RSI decreasing 3 days in a row
    df["rsi_down_3"] = (
        (df["rsi_5"] < df["rsi_5"].shift(1)) &
        (df["rsi_5"].shift(1) < df["rsi_5"].shift(2)) &
        (df["rsi_5"].shift(2) < df["rsi_5"].shift(3))
    )

    # RSI below 60 for at least 3 days
    rsi_below_60 = df["rsi_5"] < 60
    df["rsi_below_60_3d"] = rsi_below_60.rolling(3).sum() >= 3

    # Signal conditions
    df["rsi_signal_buy"] = (
        (df["rsi_5"] < 30) &
        (df["rsi_down_3"]) &
        (df["rsi_below_60_3d"]) &
        (df["close"] > df["ma_20"])
    )

    df["rsi_signal_sell"] = df["rsi_5"] > 50

    return df


def add_rsi_confirmations(df, delta=-0.0001, lag=3):
    df = df.copy()

    past_close = df["close"].shift(lag)
    past_signal = df["rsi_signal_buy"].shift(lag)

    price_change = (df["close"] - past_close) / past_close

    df["rsi_confirm_buy"] = (past_signal == True) & (price_change > delta)

    return df


def add_stochastic(df, k_period=14, d_period=3):
    low_min = df["low"].rolling(window=k_period).min()
    high_max = df["high"].rolling(window=k_period).max()
    df["stoch_k"] = 100 * (df["close"] - low_min) / (high_max - low_min)
    df["stoch_d"] = df["stoch_k"].rolling(window=d_period).mean()
    return df


def add_bollinger_bands(df, period=20, std_dev=2):
    ma = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    df["bb_upper"] = ma + std_dev * std
    df["bb_lower"] = ma - std_dev * std
    df["bollinger_width"] = (df["bb_upper"] - df["bb_lower"]) / ma
    return df


def add_bollinger_position(df):
    df["bollinger_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
    return df


def add_volume_change(df):
    df["volume_change"] = df["volume"].pct_change().fillna(0)
    return df


def add_atr(df, period=14):
    df = df.copy()
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr"] = tr.rolling(window=period).mean()

    return df


def add_swing_points(df, order=SWING_RANGE, atr_multiplier=1, confirmation_window=SWING_RANGE):
    df = df.copy()
    df["swing"] = 0
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    atr = df["atr"]
    idx = df.index
    center = len(df) - order - confirmation_window
    if center < order or center + confirmation_window >= len(df):
        return df  # not enough data
    # Swing high
    left_highs = highs[center - order:center]
    right_highs = highs[center + 1:center + 1 + order]
    swing_high = highs[center]

    if swing_high > max(left_highs) and swing_high > max(right_highs):
        swing_atr = atr.iloc[center]
        if swing_atr and (swing_high - max(max(left_highs), max(right_highs)) > atr_multiplier * swing_atr):
            # Confirmation: close < low of swing high within next N candles
            confirm = any(closes[center + 1 + i] < lows[center] for i in range(confirmation_window))
            if confirm:
                df.loc[idx[-1], "swing"] = 1

    # Swing low
    left_lows = lows[center - order:center]
    right_lows = lows[center + 1:center + 1 + order]
    swing_low = lows[center]

    if swing_low < min(left_lows) and swing_low < min(right_lows):
        swing_atr = atr.iloc[center]
        if swing_atr and (min(min(left_lows), min(right_lows)) - swing_low > atr_multiplier * swing_atr):
            # Confirmation: close > high of swing low within next N candles
            confirm = any(closes[center + 1 + i] > highs[center] for i in range(confirmation_window))
            if confirm:
                df.loc[idx[-1], "swing"] = -1

    return df

