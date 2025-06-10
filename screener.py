# screener.py
import pygame
import datetime
from fetcher import fetch_binance_ohlc, batch_fetch
from config import LAYER1_COINS, BAR_HEIGHT, BAR_X, BAR_Y, BAR_WIDTH, WHITE, GREEN, BLACK
from indicators import add_indicators
from slack_api import send_slack_alert
from trader import exit_trade, enter_trade, get_balance, sell_all_non_usdt
from strategy import apply_strategy
import time

def run_screener(screen):
    pygame.display.set_caption("Crypto Screener")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24)
    starting_balance = get_balance()
    last_run = None
    next_run = None
    in_position = False
    holding_symbol = None
    entry_price = 0
    sell_all_non_usdt()

    def fetch_and_process(screen_obj):
        nonlocal in_position, holding_symbol, entry_price
        last_run = datetime.datetime.now()
        next_run = (last_run + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        if next_run <= last_run:
            next_run += datetime.timedelta(hours=1)

        candidate_entries = []
        fetched_data = batch_fetch(list(LAYER1_COINS.values()))
        idx = 0
        for name, symbol in LAYER1_COINS.items():
            df = fetched_data[idx]
            idx += 1
            if df is None or len(df) < 50:
                continue
            df = add_indicators(df)
            df = apply_strategy(df)
            screen_obj.fill(WHITE)
            draw_candlestick_chart(screen_obj, df, symbol)
            pygame.display.flip()

            signal = df["signal"].iloc[-1]
            price = df["close"].iloc[-1]
            volatility = df["high"].iloc[-1] - df["low"].iloc[-1]

            if in_position:
                if symbol == holding_symbol and signal == "SELL":
                    exit_trade(symbol)
                    send_slack_alert(f"🔻 SELL: {symbol} at {price}")
                    in_position = False
                    holding_symbol = None
                    entry_price = 0
                    temp_balance = get_balance()
                    temp_change = (temp_balance - starting_balance) / starting_balance
                    print(f"Current P/L: {int(temp_change * 10000) / 100}%")
            else:
                if signal == "BUY":
                    candidate_entries.append((symbol, volatility, price))

        if not in_position and candidate_entries:
            best = max(candidate_entries, key=lambda x: x[1])
            symbol, vol, price = best
            enter_trade(symbol)
            send_slack_alert(f"💡 BUY: {symbol} at {price} (volatility: {vol:.2f})")
            in_position = True
            holding_symbol = symbol
            entry_price = price
        return last_run, next_run

    last_run, next_run = fetch_and_process(screen)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        now = datetime.datetime.now()
        if now >= next_run:
            last_run, next_run = fetch_and_process(screen)
            last_run = now
            next_run = last_run.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)

        total_seconds = (next_run - last_run).total_seconds()
        progress_ratio = 1 - min(max(total_seconds / 3600, 0), 1)
        screen.fill(WHITE)
        pygame.draw.rect(screen, (100, 100, 100), (BAR_X, BAR_Y, BAR_WIDTH, BAR_HEIGHT))
        pygame.draw.rect(screen, GREEN, (BAR_X, BAR_Y, int(BAR_WIDTH * progress_ratio), BAR_HEIGHT))

        remaining_time = next_run - now
        countdown_text = f"Next update in: {str(remaining_time).split('.')[0]}"
        msg_surface = font.render(countdown_text, True, BLACK)
        screen.blit(msg_surface, (BAR_X, BAR_Y - 30))
        try:
            current_balance = get_balance()
            change = (current_balance - starting_balance) / starting_balance
            profit_msg = f"Current P/L: {int(change*10000)/100}%"
            profit_msg_surface = font.render(profit_msg, True, BLACK)
            screen.blit(profit_msg_surface, (BAR_X, BAR_Y - 90))
        except Exception as e:
            print(e)

        pygame.display.flip()
        clock.tick(30)


def draw_candlestick_chart(screen, data, ticker):
    if data is None or len(data) == 0:
        return

    font = pygame.font.SysFont("arial", 24)
    msg_surface = font.render(ticker, True, BLACK)
    screen.blit(msg_surface, (10, 10))

    offset = 50
    offset_x = offset
    height = screen.get_height() - offset * 2
    top = offset
    visible_candles = min(100, len(data))
    screen_width = screen.get_width()
    chart_width = screen_width - offset_x * 2
    candle_width = chart_width / visible_candles
    candles = data[-visible_candles:].copy()

    max_price = candles["high"].max()
    min_price = candles["low"].min()
    price_range = max(max_price - min_price, 1e-6)

    def scale(price):
        return top + height - ((price - min_price) / price_range) * height

    # --- Draw Candles ---
    for i, (ts, row) in enumerate(candles.iterrows()):
        o, h, l, c = row["open"], row["high"], row["low"], row["close"]
        x = int(i * candle_width + offset_x)

        open_y = int(scale(o))
        close_y = int(scale(c))
        high_y = int(scale(h))
        low_y = int(scale(l))

        color = (0, 200, 0) if c >= o else (200, 0, 0)

        pygame.draw.line(screen, color, (x + candle_width // 2, high_y), (x + candle_width // 2, low_y), 1)
        body_top = min(open_y, close_y)
        body_height = max(1, abs(close_y - open_y))
        pygame.draw.rect(screen, color, pygame.Rect(x, body_top, candle_width - 2, body_height))








