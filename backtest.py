import numpy as np
import pygame
from config import LAYER1_COINS, LIGHT_GRAY, WIDTH, HEIGHT
from fetcher import load_backtest_data
from indicators import add_indicators
from strategy import apply_strategy


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
    idx = 0
    for symbol in LAYER1_COINS.values():
        screen.fill(WHITE)
        header = font.render("Formatting Data", True, BLACK)
        width = header.get_width()
        screen.blit(header, ((screen.get_size()[0] / 2) - (width / 2), 50))
        progress = idx / len(list(LAYER1_COINS.items()))
        idx += 1
        pygame.draw.rect(screen, (100, 100, 100), (BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT))
        pygame.draw.rect(screen, GREEN, (BAR_X, BAR_Y, int(BAR_WIDTH * progress), BAR_HEIGHT))

        percent_text = font.render(f"{int(progress * 100)}%", True, BLACK)
        screen.blit(percent_text, (BAR_X + BAR_WIDTH // 2 - 20, BAR_Y + 5))

        pygame.display.flip()
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
        if i % 50 == 0:
            screen.fill(WHITE)
            draw_chart(screen, equity, i)
            progress = int((i/n_steps)*10000)/100
            header = font.render(f"{progress}%", True, BLACK)
            width = header.get_width()
            screen.blit(header, ((screen.get_size()[0] / 2) - (width / 2), screen.get_size()[1]-50))
            pygame.display.flip()
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

    # Max Drawdown
    peak = equity[0]
    max_drawdown = 0
    for val in equity:
        if val > peak:
            peak = val
        drawdown = (peak - val) / peak
        max_drawdown = max(max_drawdown, drawdown)
    max_drawdown = round(max_drawdown * 100, 2)

    # Expectancy
    expectancy = round((winrate / 100 * avg_win) + ((1 - winrate / 100) * avg_loss), 2)

    # Profit Factor
    profit_factor = round(sum(wins) / abs(sum(losses)), 2) if losses else float('inf')

    # Sharpe Ratio (hourly, assuming 0 risk-free rate)
    returns = np.diff(equity) / equity[:-1]
    sharpe_ratio = round((np.mean(returns) / np.std(returns)) * np.sqrt(1), 2) if np.std(returns) else 0

    # Avg time in trade (approx, assuming equally spaced trades)
    avg_time_in_trade = round(len(equity) / total, 2) if total else 0

    # Show results in Pygame
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        screen.fill(WHITE)
        draw_chart(screen, equity, n_steps)

        stats = [
            f"Total Trades: {total}",
            f"Win Rate: {winrate}%",
            f"Avg Trade: {avg_trade}%",
            f"Avg Win: {avg_win}%",
            f"Avg Loss: {avg_loss}%",
            f"Total Gain: {total_gain}%"
        ]
        stats2 = [
            f"Max Drawdown: {max_drawdown}%",
            f"Expectancy: {expectancy}%",
            f"Profit Factor: {profit_factor}",
            f"Sharpe Ratio: {sharpe_ratio}",
            f"Avg Time in Trade: {avg_time_in_trade}h"
        ]

        for i, stat in enumerate(stats):
            screen.blit(font.render(stat, True, BLACK), (30, 230 + i * 24))
        for i, stat in enumerate(stats2):
            screen.blit(font.render(stat, True, BLACK), (300, 230 + i * 24))

        pygame.display.flip()
        clock.tick(30)

def draw_chart(screen, equity, steps):
    equity = equity[:steps]
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