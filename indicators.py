import numpy as np
from config import TREND_TOLERANCE, SWINGS_LOOK_BACK, SWING_RANGE, ATR_MULT
import pandas as pd
from scipy.signal import argrelextrema


def add_indicators(df):
    df = df.copy()
    df = add_rsi(df)
    df = add_atr(df)
    df = add_short_rsi_indicator(df)
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

