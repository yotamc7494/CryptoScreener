def get_signal(row):
    # BUY Logic
    if (
        row["rsi"] < 35
        and row["stoch_k"] < 20
        and row["bollinger_position"] < 0.25
        #and row["volume_change"] > 0  # avoid weak moves
        and row['trend_touch'] == 1
    ):
        return "BUY"

    # SELL Logic
    elif (
        (
            row["rsi"] > 65
            and row["stoch_k"] > 80
            and row["bollinger_position"] > 0.7
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
