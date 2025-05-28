import requests
import pandas as pd
import time
import pygame
import os
import pickle
from config import LAYER1_COINS, WHITE, BLACK, GREEN, BINANCE_URL, BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT


def fetch_binance_ohlc(symbol, interval="1h", limit=1000):
    pair = symbol + "USDT"
    params = {
        "symbol": pair,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(BINANCE_URL, params=params)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch {pair}: {response.text}")
    raw = response.json()
    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df = df[["open_time", "open", "high", "low", "close", "volume"]]
    df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df.astype(float)
    return df


def fetch_all_binance_coins():
    data = {}
    for name, symbol in LAYER1_COINS.items():
        try:
            df = fetch_binance_ohlc(symbol)
            data[symbol] = df
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")
    return data


def fetch_binance_ohlc_range(symbol, interval="1h", start_time=None, end_time=None, limit=1000):
    pair = symbol + "USDT"
    params = {
        "symbol": pair,
        "interval": interval,
        "limit": limit
    }
    if start_time:
        params["startTime"] = int(start_time)
    if end_time:
        params["endTime"] = int(end_time)

    response = requests.get(BINANCE_URL, params=params)
    if response.status_code != 200:
        print(f"Error fetching {symbol} from {start_time} to {end_time}")
        return []

    raw = response.json()
    if not raw:
        return []

    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df = df[["open_time", "open", "high", "low", "close", "volume"]]
    df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df.astype(float)

    return df.reset_index().to_dict("records")


def generate_backtest_data(screen, total_candles_per_coin):
    pygame.display.set_caption("Generating Backtest Data")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 22)

    total_batches = 0
    batch_counts = {}
    for symbol in LAYER1_COINS.values():
        batch_count = (total_candles_per_coin + 999) // 1000
        batch_counts[symbol] = batch_count
        total_batches += batch_count

    completed_batches = 0
    coin_data = {}

    for coin_name, symbol in LAYER1_COINS.items():
        batch_count = batch_counts[symbol]
        coin_batches = []

        end_time = int(time.time() * 1000)  # current time in ms
        for batch in range(batch_count):
            # Draw progress
            screen.fill(WHITE)
            header = font.render("Fetching Data", True, BLACK)
            width = header.get_width()
            screen.blit(header, ((screen.get_size()[0] / 2) - (width / 2), 50))
            progress = completed_batches / total_batches
            pygame.draw.rect(screen, (100, 100, 100), (BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT))
            pygame.draw.rect(screen, GREEN, (BAR_X, BAR_Y, int(BAR_WIDTH * progress), BAR_HEIGHT))

            status_text = f"{symbol} [{batch + 1}/{batch_count}]"
            msg_surface = font.render(status_text, True, BLACK)
            screen.blit(msg_surface, (BAR_X, BAR_Y - 40))

            percent_text = font.render(f"{int(progress * 100)}%", True, BLACK)
            screen.blit(percent_text, (BAR_X + BAR_WIDTH // 2 - 20, BAR_Y + 5))

            pygame.display.flip()
            start_time = end_time - 1000 * 60 * 60 * 1000  # 1000 hours earlier in ms
            data = fetch_binance_ohlc_range(symbol, interval='1h', start_time=start_time, end_time=end_time, limit=1000)

            if not data or len(data) < 10:
                print(f"{symbol} has no more data beyond batch {batch + 1}")
                break  # reached historical limit

            coin_batches = data + coin_batches  # prepend to maintain order
            end_time = start_time
            completed_batches += 1
            clock.tick(30)
        coin_data[symbol] = coin_batches
    save_backtest_data(coin_data)


def save_backtest_data(data, filename="backtest_data.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(data, f)
    print(f"✅ Data saved to {filename}")


def load_backtest_data(filename="backtest_data.pkl"):
    if not os.path.exists(filename):
        print("❌ No saved backtest data found.")
        return None

    with open(filename, "rb") as f:
        raw_data = pickle.load(f)

    formatted_data = {}
    for symbol, candles in raw_data.items():
        if not candles:
            continue
        df = pd.DataFrame(candles)
        df.set_index("timestamp", inplace=True)
        df = df.astype(float)
        formatted_data[symbol] = df

    print(f"✅ Loaded and parsed backtest data from {filename}")
    return formatted_data
