import numpy as np
import pygame
from config import LAYER1_COINS, LIGHT_GRAY, WIDTH, HEIGHT, WHITE, BLACK, GREEN, BAR_WIDTH, BAR_X, BAR_Y, BAR_HEIGHT, BACKTEST_RANGE, SWING_RANGE
from fetcher import load_backtest_data
from indicators import add_indicators
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
    mouse_pos = (0, 0)
    equity = np.zeros(n_steps)
    equity[0] = capital
    trades = []
    in_position = False
    holding_symbol = None
    entry_price = 0
    coins_with_indicators = {}
    signals = {}
    trades_graph = {
        "win": {
            "data": [0]*100,
            "total": 0
        },
        "loss": {
            "data": [0]*100,
            "total": 0
        }
    }
    stop_loss = 100
    take_profit = 100
    cooldown_time = 12
    cooldown = 0
    current_trade_graph = []
    for symbol in symbols:
        df = coin_data[symbol].copy()
        df = add_indicators(df)
        df["signal"] = df.apply(get_signal, axis=1)

        # Store full df and signal list
        coins_with_indicators[symbol] = df
        signals[symbol] = df.loc[aligned_index, "signal"].tolist()

    for i in range(1, n_steps):
        current_index = aligned_index[i]

        if i % 150 == 0:
            screen.fill(WHITE)
            draw_chart(screen, equity, i, trades_graph, mouse_pos)
            progress = int((i / n_steps) * 10000) / 100
            header = font.render(f"{progress}%", True, BLACK)
            screen.blit(header, ((screen.get_size()[0] / 2) - (header.get_width() / 2), screen.get_size()[1] - 50))
            pygame.display.flip()
            pygame.event.pump()
            pygame.display.update()

        if in_position:
            df = coins_with_indicators.get(holding_symbol)
            if df is not None and current_index in df.index :
                price = df.loc[current_index, "close"]
                signal = signals[holding_symbol][i]
                gain = (price - entry_price) / entry_price
                current_trade_graph.append(gain)
                if signal == "SELL" or -stop_loss > gain or take_profit < gain:
                    if -stop_loss > gain:
                        cooldown += cooldown_time
                    capital *= (1 + gain)
                    equity[i] = capital
                    trades.append(gain)
                    in_position = False
                    holding_symbol = None
                    entry_price = 0
                    trade_ratio = len(current_trade_graph)/100
                    trade_result = "win" if current_trade_graph[-1] > 0 else "loss"
                    trades_graph[trade_result]['total'] += 1
                    for idx in range(100):
                        trade_idx = int(trade_ratio * idx)
                        gain = current_trade_graph[trade_idx]
                        trades_graph[trade_result]['data'][idx] += gain
                    current_trade_graph = []
                else:
                    equity[i] = equity[i - 1]
            else:
                equity[i] = equity[i - 1]
        else:
            cooldown = max(0, cooldown-1)
            for symbol in symbols:
                if signals[symbol][i] == "BUY" and cooldown == 0:
                    df = coins_with_indicators[symbol]
                    if current_index in df.index:
                        take_profit = df.loc[current_index, "atr"] * 2.5
                        stop_loss = df.loc[current_index, "atr"] * 3
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
    start_value = equity[0]
    end_value = equity[-1]
    total_hours = len(equity)
    years = total_hours / (24 * 365)
    cagr = (end_value / start_value) ** (1 / years) - 1

    # Show results in Pygame
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == 1024:
                mouse_pos = event.pos

        screen.fill(WHITE)
        draw_chart(screen, equity, n_steps, trades_graph, mouse_pos)

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
            f"Avg Time in Trade: {avg_time_in_trade}h",
            f"CAGR: {int(cagr*10000)/100}%"
        ]

        for i, stat in enumerate(stats):
            screen.blit(font.render(stat, True, BLACK), (30, 230 + i * 24))
        for i, stat in enumerate(stats2):
            screen.blit(font.render(stat, True, BLACK), (300, 230 + i * 24))

        pygame.display.flip()
        clock.tick(30)

def draw_chart(screen, equity, steps, trades_graph, mouse_pos):
    offset = 20
    chart_height = 170
    chart_top = offset * 2
    chart_left = offset * 2
    chart_width = 400 - chart_left - offset
    draw_graph(screen, equity[:steps], chart_height, chart_top, chart_left, chart_width, offset, mouse_pos)
    chart_left += chart_width + offset*3
    chart_width = WIDTH-chart_left - offset*2
    chart_height = 55
    if trades_graph['win']['total'] > 0:
        new_list = [a / trades_graph['win']['total'] for a in trades_graph['win']['data']]
        draw_graph(screen, new_list, chart_height, chart_top, chart_left, chart_width, offset, mouse_pos)
    chart_top += chart_height + offset * 3
    if trades_graph['loss']['total'] > 0:
        new_list = [a / trades_graph['loss']['total'] for a in trades_graph['loss']['data']]
        draw_graph(screen, new_list, chart_height, chart_top, chart_left, chart_width, offset, mouse_pos)



def draw_graph(screen, data_list, chart_height, chart_top, chart_left, chart_width, offset, mouse_pos):
    max_cap = max(data_list)
    min_cap = min(data_list)
    cap_range = max_cap - min_cap or 1
    border = pygame.Rect(
        chart_left-offset,
        chart_top-offset,
        chart_width+offset*2,
        chart_height+offset*2
    )
    pygame.draw.rect(screen, LIGHT_GRAY, border, 2)
    idx = 0
    if border.collidepoint(mouse_pos):
        x_range = (mouse_pos[0] - chart_left)/chart_width
        idx = int(x_range*len(data_list))
    for i in range(1, len(data_list)):
        x1 = chart_left + int((i - 1) / len(data_list) * chart_width)
        if idx == i:
            graph_font = pygame.font.SysFont("arial", 12)
            pygame.draw.line(screen, GREEN, (x1, chart_top-offset), (x1, chart_top+chart_height+offset), 2)
            gain = f"{int(data_list[i]*10000)/100}%"
            txt_surface = graph_font.render(gain, True, BLACK)
            screen.blit(txt_surface, (x1, chart_top-offset))

        x2 = chart_left + int(i / len(data_list) * chart_width)
        #print(chart_height, data_list[i - 1], min_cap, cap_range, chart_height)
        y1 = chart_top + int(chart_height - ((data_list[i - 1] - min_cap) / cap_range) * chart_height)
        y2 = chart_top + int(chart_height - ((data_list[i] - min_cap) / cap_range) * chart_height)
        pygame.draw.line(screen, GREEN, (x1, y1), (x2, y2), 2)