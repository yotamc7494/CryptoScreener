# screener.py
import time

import pygame
import datetime
from fetcher import fetch_binance_ohlc
from config import LAYER1_COINS
from indicators import add_indicators
from slack_api import send_slack_alert
from strategy import apply_strategy

WIDTH, HEIGHT = 600, 400
WHITE = (255, 255, 255)
GREEN = (50, 200, 100)
BLACK = (0, 0, 0)

def run_screener(screen):
    pygame.display.set_caption("Crypto Screener")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24)

    last_run = None
    next_run = None
    in_position = False
    holding_symbol = None
    entry_price = 0

    def fetch_and_process(screen_obj):
        nonlocal in_position, holding_symbol, entry_price

        last_run = datetime.datetime.now()
        next_run = (last_run + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        if next_run <= last_run:
            next_run += datetime.timedelta(hours=1)

        candidate_entries = []

        for name, symbol in LAYER1_COINS.items():
            try:
                df = fetch_binance_ohlc(symbol)
                if df is None or len(df) < 50:
                    continue

                screen_obj.fill(WHITE)
                draw_candlestick_chart(screen_obj, df, symbol)
                pygame.display.flip()

                df = add_indicators(df)
                df = apply_strategy(df)

                signal = df["signal"].iloc[-1]
                price = df["close"].iloc[-1]
                volatility = df["high"].iloc[-1] - df["low"].iloc[-1]

                if in_position:
                    if symbol == holding_symbol and signal == "SELL":
                        send_slack_alert(f"🔻 SELL: {symbol} at {price}")
                        in_position = False
                        holding_symbol = None
                        entry_price = 0
                else:
                    if signal == "BUY":
                        candidate_entries.append((symbol, volatility, price))

            except Exception as e:
                print(f"[ERROR] {symbol}: {e}")

        if not in_position and candidate_entries:
            best = max(candidate_entries, key=lambda x: x[1])
            symbol, vol, price = best
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

        bar_width = WIDTH - 100
        bar_height = 20
        bar_x = 50
        bar_y = HEIGHT - 40
        screen.fill(WHITE)
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * progress_ratio), bar_height))

        remaining_time = next_run - now
        countdown_text = f"Next update in: {str(remaining_time).split('.')[0]}"
        msg_surface = font.render(countdown_text, True, BLACK)
        screen.blit(msg_surface, (bar_x, bar_y - 30))

        pygame.display.flip()
        clock.tick(30)


def draw_candlestick_chart(screen, data, ticker):
    if data is None or len(data) == 0:
        return
    font = pygame.font.SysFont("arial", 24)
    msg_surface = font.render(ticker, True, BLACK)
    screen.blit(msg_surface, (10, 10))
    offset = 50  # X offset in pixels from the left
    offset_x = offset
    height = screen.get_height() - offset*2
    top = offset
    visible_candles = min(100, len(data))
    screen_width = screen.get_width()
    chart_width = screen_width - offset_x*2
    candle_width = chart_width / visible_candles
    candles = data[-visible_candles:]

    max_price = candles["high"].max()
    min_price = candles["low"].min()
    price_range = max(max_price - min_price, 1e-6)

    def scale(price):
        return top + height - ((price - min_price) / price_range) * height
    for i, (ts, row) in enumerate(candles.iterrows()):
        o, h, l, c = row["open"], row["high"], row["low"], row["close"]
        x = int(i * candle_width + offset_x)

        open_y = int(scale(o))
        close_y = int(scale(c))
        high_y = int(scale(h))
        low_y = int(scale(l))

        color = (0, 200, 0) if c >= o else (200, 0, 0)

        # Wick

        pygame.draw.line(screen, color, (x + candle_width // 2, high_y), (x + candle_width // 2, low_y), 1)

        # Body
        body_top = min(open_y, close_y)
        body_height = max(1, abs(close_y - open_y))
        pygame.draw.rect(screen, color, pygame.Rect(x, body_top, candle_width - 2, body_height))




