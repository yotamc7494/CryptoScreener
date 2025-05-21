import pandas as pd

def add_ll_indicators(df):
    df = df.copy()
    df = add_rsi(df)
    df = add_macd(df)
    df = add_macd_hist(df)
    df = add_stochastic(df)
    df = add_bollinger_bands(df)
    df = add_bollinger_position(df)
    df = add_volume_change(df)
    df = normalize_indicators(df)
    return df

def normalize_indicators(df):
    df = df.copy()

    # Normalize bounded indicators
    for col in ["rsi", "stoch_k", "stoch_d", "bollinger_position"]:
        if col in df.columns:
            df.loc[:, col] = df[col] / 100.0

    # Normalize unbounded using z-score
    for col in ["macd", "macd_signal", "macd_hist", "bollinger_band_width", "volume_change"]:
        if col in df.columns:
            mean = df[col].mean()
            std = df[col].std()
            df.loc[:, col] = (df[col] - mean) / (std + 1e-8)

    return df

def add_rsi(df, period=14):
    df = df.copy()
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df.loc[:, "rsi"] = 100 - (100 / (1 + rs))
    return df

def add_macd(df):
    df = df.copy()
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df.loc[:, "macd"] = ema12 - ema26
    df.loc[:, "macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    return df

def add_macd_hist(df):
    df = df.copy()
    if "macd" not in df or "macd_signal" not in df:
        df = add_macd(df)
    df.loc[:, "macd_hist"] = df["macd"] - df["macd_signal"]
    return df

def add_stochastic(df, k_period=14, d_period=3):
    df = df.copy()
    low_min = df["low"].rolling(window=k_period).min()
    high_max = df["high"].rolling(window=k_period).max()
    df.loc[:, "stoch_k"] = 100 * (df["close"] - low_min) / (high_max - low_min)
    df.loc[:, "stoch_d"] = df["stoch_k"].rolling(window=d_period).mean()
    return df

def add_bollinger_bands(df, period=20, num_std=2):
    df = df.copy()
    ma = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    df.loc[:, "bb_upper"] = ma + num_std * std
    df.loc[:, "bb_lower"] = ma - num_std * std
    df.loc[:, "bollinger_band_width"] = (df["bb_upper"] - df["bb_lower"]) / ma
    return df

def add_bollinger_position(df):
    df = df.copy()
    # Ensure required columns exist
    if not all(col in df for col in ["close", "bb_upper", "bb_lower"]):
        df = add_bollinger_bands(df)
    spread = df["bb_upper"] - df["bb_lower"]
    df.loc[:, "bollinger_position"] = (df["close"] - df["bb_lower"]) / (spread + 1e-8)
    return df

def add_volume_change(df):
    df = df.copy()
    df.loc[:, "volume_change"] = df["volume"].pct_change().fillna(0)
    return df


