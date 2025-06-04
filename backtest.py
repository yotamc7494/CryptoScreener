import numpy as np
import pygame
from config import LAYER1_COINS, LIGHT_GRAY, WIDTH, HEIGHT, WHITE, BLACK, GREEN, BAR_WIDTH, BAR_X, BAR_Y, BAR_HEIGHT, BACKTEST_RANGE, SWING_RANGE
from fetcher import load_backtest_data
from indicators import add_indicators, add_swing_points
from strategy import get_signal


def run_backtest(screen):
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 22)
    pygame.display.set_caption("Backtester")

    coin_data = load_backtest_data()
    symbols = list(LAYER1_COINS.values())
    aligned_index = None

    for symbol in symbols:
        df = coin_data.get(symbol)
        if df is not None and len(df) >= BACKTEST_RANGE:
            aligned_index = df.tail(BACKTEST_RANGE).index if aligned_index is None else aligned_index.intersection(df.index)
    aligned_index = aligned_index[-BACKTEST_RANGE:]
    n_steps = len(aligned_index)

    capital = 1.0
    equity = np.zeros(n_steps)
    equity[0] = capital
    trades = []
    in_position = False
    holding_symbol = None
    entry_price = 0
    coins_with_indicators = {}
    signals = {}

    for symbol in symbols:
        df = coin_data[symbol].copy()
        df = add_indicators(df)
        coins_with_indicators[symbol] = df
        signals[symbol] = []

    for i in range(1, n_steps):
        current_index = aligned_index[i]
        df_now_map = {}

        for symbol in symbols:
            df = coins_with_indicators[symbol]
            if current_index not in df.index:
                signals[symbol].append("NEUTRAL")
                continue
            """
            current_loc = df.index.get_loc(current_index)
            left = max(current_loc - SWING_RANGE * 3, 0)
            right = current_loc + 1  # include current row, but not future
            swing_window = df.iloc[left:right].copy()

            swing_window = add_swing_points(swing_window)
            df.at[current_index, "swing"] = 0
            swing_series = swing_window["swing"]

            if (swing_series == 1).any():
                df.at[current_index, "swing"] = 1
            elif (swing_series == -1).any():
                df.at[current_index, "swing"] = -1
            """
            row = df.loc[current_index]
            signal = get_signal(row)
            signals[symbol].append(signal)
            df_now_map[symbol] = df

        if i % 15 == 0:
            screen.fill(WHITE)
            draw_chart(screen, equity, i)
            progress = int((i / n_steps) * 10000) / 100
            header = font.render(f"{progress}%", True, BLACK)
            screen.blit(header, ((screen.get_size()[0] / 2) - (header.get_width() / 2), screen.get_size()[1] - 50))
            pygame.display.flip()
            if i % 10 == 0:
                pygame.event.pump()
                pygame.display.update()

        if in_position:
            df = df_now_map.get(holding_symbol)
            if df is not None and current_index in df.index:
                signal = signals[holding_symbol][-1]
                price = df.loc[current_index, "close"]
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
                equity[i] = equity[i - 1]
        else:
            for symbol in symbols:
                if signals[symbol][-1] == "BUY":
                    df = coins_with_indicators[symbol]
                    if current_index in df.index:
                        in_position = True
                        holding_symbol = symbol
                        entry_price = df.loc[current_index, "close"]
                        break
            equity[i] = capital if in_position else equity[i - 1]

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