import random

from config import BUY_BP, BUY_RSI, BUY_STOCH, SELL_RSI, SELL_BP, SELL_STOCH


def get_signal(row):
    if row["rsi_signal_buy"]:
        return "BUY"
    elif row["rsi_signal_sell"]:
        return "SELL"
    return "NEUTRAL"


def apply_strategy(df):
    df = df.copy()
    if "signal" not in df.columns:
        df["signal"] = "NEUTRAL"
    df.at[df.index[-1], "signal"] = get_signal(df.iloc[-1])
    return df
