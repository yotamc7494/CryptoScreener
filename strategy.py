from config import BUY_BP, BUY_RSI, BUY_STOCH, SELL_RSI, SELL_BP, SELL_STOCH

def get_signal(row):
    # BUY Logic
    if (
        row["rsi"] < BUY_RSI
        and row["stoch_k"] < BUY_STOCH
        and row["bollinger_position"] < BUY_BP
        and row['trend_touch'] == 1
    ):
        return "BUY"

    # SELL Logic
    elif (
        (
            row["rsi"] > SELL_RSI
            and row["stoch_k"] > SELL_STOCH
            and row["bollinger_position"] > SELL_BP
            and row["volume_change"] > 0
        )
        or row['trend_touch'] == -1
    ):
        return "SELL"

    else:
        return "NEUTRAL"


def apply_strategy(df):
    df = df.copy()
    df["signal"] = df.apply(get_signal, axis=1)
    return df
