import pygame
from fetcher import load_backtest_data
from config import LAYER1_COINS, LIGHT_GRAY
from indicators import add_ll_indicators
from random_forest import RandomForestSignalClassifier, CONFIDENCE_THRESHOLD

WIDTH, HEIGHT = 600, 400
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
BAR_WIDTH = WIDTH - 100
BAR_HEIGHT = 30
BAR_X = 50
BAR_Y = HEIGHT - 100


def run_backtest(screen):
    switch_trades = True
    backtest_range = 5000
    pygame.display.set_caption("Backtester")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 22)

    coin_data = load_backtest_data()
    clf = RandomForestSignalClassifier()
    clf.load_model("main_rf.pkl")

    all_signals = {}
    aligned_index = None

    # Step 1: Preprocess and batch predict
    idx = 0
    for name, symbol in LAYER1_COINS.items():
        screen.fill(WHITE)
        header = font.render("Running Backtest", True, BLACK)
        width = header.get_width()
        screen.blit(header, ((screen.get_width() - width) / 2, 50))
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

        df = add_ll_indicators(df)
        all_signals[symbol] = clf.predict_all(df)
        aligned_index = df.index if aligned_index is None else aligned_index.intersection(df.index)

    # Step 2: Run backtest logic using precomputed predictions
    capital = 1.0
    equity = [1.0]
    trades = []
    in_position = False
    holding_symbol = None
    entry_price = 0

    idx = 0
    for ts in aligned_index[-backtest_range:]:
        screen.fill(WHITE)
        header = font.render("Running Backtest", True, BLACK)
        width = header.get_width()
        screen.blit(header, ((screen.get_width() - width) / 2, 50))
        progress = idx / backtest_range
        idx += 1
        pygame.draw.rect(screen, (100, 100, 100), (BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT))
        pygame.draw.rect(screen, GREEN, (BAR_X, BAR_Y, int(BAR_WIDTH * progress), BAR_HEIGHT))
        percent_text = font.render(f"{int(progress * 100)}%", True, BLACK)
        screen.blit(percent_text, (BAR_X + BAR_WIDTH // 2 - 20, BAR_Y + 5))
        pygame.display.flip()

        signals = []
        for symbol, df in all_signals.items():
            if ts not in df.index:
                continue
            row = df.loc[ts]
            signal = row["rf_prediction"]
            volatility = row["high"] - row["low"]
            close = row["close"]
            conf = row['rf_confidence']
            signals.append((symbol, signal, volatility, close, conf))

        # Exit logic
        if in_position:
            switched = False
            if switch_trades:
                buy_candidates = [(sym, vol, price, conf) for sym, sig, vol, price, conf in signals if sig == "BUY"]
                current_symbol, current_signal, current_price, current_conf = [(sym, sig, price, vol) for sym, sig, vol, price, conf in signals if sym == holding_symbol][0]
                if buy_candidates:
                    best = max(buy_candidates, key=lambda x: x[1])
                    symbol, _, price, conf = best
                    if conf > current_conf and symbol != current_symbol:
                        gain = (current_price - entry_price) / entry_price
                        capital *= (1 + gain)
                        equity.append(capital)
                        trades.append(gain)
                        holding_symbol = symbol
                        entry_price = price
                        switched = True
            if not switched:
                for sym, sig, _, price, _ in signals:
                    if sym == holding_symbol and sig == "SELL":
                        gain = (price - entry_price) / entry_price
                        capital *= (1 + gain)
                        equity.append(capital)
                        trades.append(gain)
                        in_position = False
                        holding_symbol = None
                        entry_price = 0
                        break
        if not in_position:
            buy_candidates = [(sym, vol, price) for sym, sig, vol, price, conf in signals if sig == "BUY"]
            if buy_candidates:
                best = max(buy_candidates, key=lambda x: x[1])
                symbol, _, price = best
                in_position = True
                holding_symbol = symbol
                entry_price = price

    # Final results
    total = len(trades)
    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]

    winrate = round(len(wins) / total * 100, 2) if total else 0
    avg_trade = round(sum(trades) / total * 100, 2) if total else 0
    avg_win = round(sum(wins) / len(wins) * 100, 2) if wins else 0
    avg_loss = round(sum(losses) / len(losses) * 100, 2) if losses else 0
    total_gain = round((capital - 1.0) * 100, 2)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        screen.fill(WHITE)
        chart_height = 170
        chart_top = 30
        chart_left = 30
        chart_width = WIDTH - chart_left - 20
        max_capital = max(equity)
        min_capital = min(equity)
        capital_range = max_capital - min_capital or 1

        pygame.draw.rect(screen, LIGHT_GRAY, pygame.Rect(10, 10, 580, 210))
        for i in range(1, len(equity)):
            x1 = chart_left + int((i - 1) / len(equity) * chart_width)
            x2 = chart_left + int(i / len(equity) * chart_width)
            y1 = chart_top + int(chart_height - ((equity[i - 1] - min_capital) / capital_range) * chart_height)
            y2 = chart_top + int(chart_height - ((equity[i] - min_capital) / capital_range) * chart_height)
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
            stat_surf = font.render(stat, True, BLACK)
            screen.blit(stat_surf, (30, 230 + i * 24))

        pygame.display.flip()
        clock.tick(30)

