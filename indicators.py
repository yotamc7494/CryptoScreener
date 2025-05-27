import numpy as np
def add_indicators(df):
    df = df.copy()
    df = add_rsi(df)
    df = add_stochastic(df)
    df = add_bollinger_bands(df)
    df = add_bollinger_position(df)
    df = add_volume_change(df)
    df = add_swing_points(df)
    df = add_trend_support_resistance(df)
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

def add_swing_points(df, lookback=3):
    highs = df["high"]
    lows = df["low"]
    swing = [0] * len(df)

    for i in range(lookback, len(df) - lookback):
        prev_highs = highs.iloc[i - lookback:i]
        next_highs = highs.iloc[i + 1:i + 1 + lookback]
        prev_lows = lows.iloc[i - lookback:i]
        next_lows = lows.iloc[i + 1:i + 1 + lookback]

        if highs.iloc[i] > max(prev_highs) and highs.iloc[i] > max(next_highs):
            swing[i] = 1  # Swing High
        elif lows.iloc[i] < min(prev_lows) and lows.iloc[i] < min(next_lows):
            swing[i] = -1  # Swing Low

    df["swing"] = swing
    return df


def add_trend_support_resistance(df, tolerance_pct=0.005, lookback=100):
    df = df.copy()

    n = len(df)
    idx_range = np.arange(n)
    lows = df["low"].values
    highs = df["high"].values
    swings = df["swing"].values

    support_scores = np.zeros(n)
    support_lines = np.full(n, np.nan)
    resistance_scores = np.zeros(n)
    resistance_lines = np.full(n, np.nan)

    swing_low_pos = idx_range[swings == -1]
    swing_high_pos = idx_range[swings == 1]

    support_trend = None
    resistance_trend = None

    for i in range(lookback, n):
        # SUPPORT
        if swings[i] == -1:
            current_price = lows[i]

            if support_trend:
                expected = support_trend["slope"] * i + support_trend["intercept"]
                tolerance = expected * tolerance_pct
                if abs(current_price - expected) <= tolerance:
                    support_trend["score"] += 1
                else:
                    support_trend["score"] -= 1

                if support_trend["score"] <= 0:
                    support_trend = None
                else:
                    support_scores[i] = support_trend["score"]
                    support_lines[i] = expected
                    continue

            recent = swing_low_pos[swing_low_pos < i][-lookback:]
            if len(recent) >= 2:
                for j in range(len(recent) - 1):
                    p1, p2 = recent[j], recent[j + 1]
                    if p2 - p1 == 0:
                        continue
                    price1 = lows[p1]
                    price2 = lows[p2]
                    slope = (price2 - price1) / (p2 - p1)
                    intercept = price2 - slope * p2
                    expected = slope * i + intercept
                    tolerance = expected * tolerance_pct
                    if abs(current_price - expected) <= tolerance:
                        support_trend = {"slope": slope, "intercept": intercept, "score": 2}
                        support_scores[i] = 2
                        support_lines[i] = expected
                        break

        # RESISTANCE
        if swings[i] == 1:
            current_price = highs[i]

            if resistance_trend:
                expected = resistance_trend["slope"] * i + resistance_trend["intercept"]
                tolerance = expected * tolerance_pct
                if abs(current_price - expected) <= tolerance:
                    resistance_trend["score"] += 1
                else:
                    resistance_trend["score"] -= 1

                if resistance_trend["score"] <= 0:
                    resistance_trend = None
                else:
                    resistance_scores[i] = resistance_trend["score"]
                    resistance_lines[i] = expected
                    continue

            recent = swing_high_pos[swing_high_pos < i][-lookback:]
            if len(recent) >= 2:
                for j in range(len(recent) - 1):
                    p1, p2 = recent[j], recent[j + 1]
                    if p2 - p1 == 0:
                        continue
                    price1 = highs[p1]
                    price2 = highs[p2]
                    slope = (price2 - price1) / (p2 - p1)
                    intercept = price2 - slope * p2
                    expected = slope * i + intercept
                    tolerance = expected * tolerance_pct
                    if abs(current_price - expected) <= tolerance:
                        resistance_trend = {"slope": slope, "intercept": intercept, "score": 2}
                        resistance_scores[i] = 2
                        resistance_lines[i] = expected
                        break

    df["trend_support_score"] = support_scores
    df["trend_support_line"] = support_lines
    df["trend_resistance_score"] = resistance_scores
    df["trend_resistance_line"] = resistance_lines

    # Vectorized trend_touch detection
    support_touch = np.where(
        np.abs(lows - support_lines) <= support_lines * tolerance_pct, 1, 0
    )
    resistance_touch = np.where(
        np.abs(highs - resistance_lines) <= resistance_lines * tolerance_pct, -1, 0
    )
    df["trend_touch"] = support_touch + resistance_touch

    return df




