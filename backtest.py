import numpy as np
import pygame
import pandas as pd
from config import LAYER1_COINS, LIGHT_GRAY
from fetcher import load_backtest_data
from indicators import add_indicators
from strategy import apply_strategy

WIDTH, HEIGHT = 600, 400
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
BAR_WIDTH = WIDTH - 100
BAR_HEIGHT = 30
BAR_X = 50
BAR_Y = HEIGHT - 100

def run_backtest(screen):
    backtest_range = 1000
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 22)
    pygame.display.set_caption("Backtester")

    coin_data = load_backtest_data()
    signals_map, prices_map = {}, {}
    aligned_index = None
    for symbol in LAYER1_COINS.values():
        df = coin_data.get(symbol)
        if df is None or len(df) < backtest_range:
            continue
        df = df.tail(backtest_range).copy()
        df = add_indicators(df)
        df = apply_strategy(df)
        signals_map[symbol] = df["signal"]
        prices_map[symbol] = df["close"]
        aligned_index = df.index if aligned_index is None else aligned_index.intersection(df.index)
    aligned_index = aligned_index[-backtest_range:]
    n_steps = len(aligned_index)
    capital = 1.0
    equity = np.zeros(n_steps)
    equity[0] = capital
    trades = []

    in_position = False
    holding_symbol = None
    entry_price = 0

    symbols = list(signals_map.keys())
    signal_arr = {s: signals_map[s].reindex(aligned_index).values for s in symbols}
    price_arr = {s: prices_map[s].reindex(aligned_index).values for s in symbols}

    for i in range(1, n_steps):
        if in_position:
            signal = signal_arr[holding_symbol][i]
            price = price_arr[holding_symbol][i]
            if signal == "SELL":
                gain = (price - entry_price) / entry_price
                capital *= (1 + gain)
                equity[i] = capital
                trades.append(gain)
                in_position = False
                holding_symbol = None
                entry_price = 0
            else:
                equity[i] = equity[i - 1]
        else:
            for s in symbols:
                if signal_arr[s][i] == "BUY":
                    in_position = True
                    holding_symbol = s
                    entry_price = price_arr[s][i]
                    break
            if holding_symbol:
                price = price_arr[holding_symbol][i]
                gain = (price - entry_price) / entry_price
                temp_capital = capital * (1 + gain)
                equity[i] = temp_capital
            else:
                equity[i] = equity[i - 1]

    # Calculate stats
    total = len(trades)
    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]
    winrate = round(len(wins) / total * 100, 2) if total else 0
    avg_trade = round(sum(trades) / total * 100, 2) if total else 0
    avg_win = round(sum(wins) / len(wins) * 100, 2) if wins else 0
    avg_loss = round(sum(losses) / len(losses) * 100, 2) if losses else 0
    total_gain = round((capital - 1.0) * 100, 2)

    # Show results in Pygame
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        screen.fill(WHITE)
        chart_height = 170
        chart_top = 30
        chart_left = 30
        chart_width = WIDTH - chart_left - 20
        max_cap = max(equity)
        min_cap = min(equity)
        cap_range = max_cap - min_cap or 1

        pygame.draw.rect(screen, LIGHT_GRAY, pygame.Rect(10, 10, 580, 210))
        for i in range(1, len(equity)):
            x1 = chart_left + int((i - 1) / len(equity) * chart_width)
            x2 = chart_left + int(i / len(equity) * chart_width)
            y1 = chart_top + int(chart_height - ((equity[i - 1] - min_cap) / cap_range) * chart_height)
            y2 = chart_top + int(chart_height - ((equity[i] - min_cap) / cap_range) * chart_height)
            pygame.draw.line(screen, GREEN, (x1, y1), (x2, y2), 2)

        stats = [
            f"Total Trades: {total}",
            f"Win Rate: {winrate}%",
            f"Avg Trade: {avg_trade}%",
            f"Avg Win: {avg_win}%",
            f"Avg Loss: {avg_loss}%",
            f"Total Gain: {total_gain}%"
        ]
        for i, stat in enumerate(stats):
            screen.blit(font.render(stat, True, BLACK), (30, 230 + i * 24))

        pygame.display.flip()
        clock.tick(30)
