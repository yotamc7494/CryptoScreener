import random

from config import BUY_BP, BUY_RSI, BUY_STOCH, SELL_RSI, SELL_BP, SELL_STOCH


def get_signal(row):
    if row["rsi_signal_buy"]:
        return "BUY"
    elif row["rsi_signal_sell"]:
        return "SELL"
    return "NEUTRAL"
    # BUY Logic: Only act if swing low confirmed
    if (
            row["rsi"] < BUY_RSI
            and row["stoch_k"] < BUY_STOCH
            and row["bollinger_position"] < BUY_BP
            and row["macd_histogram"] > 0  # Momentum confirmation
            and row["volume_change"] > 0.05  # Rising volume
    ):
        return "BUY"

    # SELL Logic: Only act if swing high confirmed
    elif (
            row["rsi"] > SELL_RSI
            and row["stoch_k"] > SELL_STOCH
            and row["bollinger_position"] > SELL_BP
            and row["volume_change"] > 0):
        return "SELL"

    return "NEUTRAL"


def apply_strategy(df):
    df = df.copy()
    if "signal" not in df.columns:
        df["signal"] = "NEUTRAL"
    df.at[df.index[-1], "signal"] = get_signal(df.iloc[-1])
    return df
