from config import BINANCE_KEY, BINANCE_SECRET, LAYER1_COINS, BINANCE_TRADE_URL, RISK_MANAGEMENT, LAYER1_COINS
from binance.client import Client
import math
from datetime import datetime
client = Client(BINANCE_KEY, BINANCE_SECRET)
client.API_URL = BINANCE_TRADE_URL  # <--- use testnet endpoint
SYMBOL_PAIRS = {v: f"{v}USDT" for v in LAYER1_COINS.values()}

def sell_all_non_usdt():
    account = client.get_account()
    all_balances = account["balances"]
    flatten_coins = [LAYER1_COINS[v] for (s, v) in enumerate(LAYER1_COINS)]
    my_symbols = []
    for s in all_balances:
        if s['asset'] in flatten_coins:
            my_symbols.append(s)
    symbols_info = client.get_exchange_info()["symbols"]
    all_pairs = {s["symbol"] for s in symbols_info}

    for asset in my_symbols:
        coin = asset["asset"]
        free = float(asset["free"])

        if coin in ["USDT"] or free == 0:
            continue

        symbol = f"{coin}USDT"
        if symbol not in all_pairs:
            print(f"❌ No USDT pair for {coin}, skipping")
            continue

        try:
            qty = round(free, 6)
            print(f"🔻 Selling {qty} of {coin}...")
            order = client.order_market_sell(symbol=symbol, quantity=qty)
            print(f"✅ Sold {coin} at market price")
        except Exception as e:
            print(f"⚠️ Could not sell {coin}: {e}")

def enter_trade(symbol, percentage=RISK_MANAGEMENT):
    current_balance = get_balance()
    usdt_amount = int(percentage*current_balance)
    pair = SYMBOL_PAIRS.get(symbol)
    if not pair:
        print(f"Symbol {symbol} not found.")
        return

    # Get price to calculate quantity
    ticker = client.get_symbol_ticker(symbol=pair)
    price = float(ticker["price"])
    quantity = round(usdt_amount / price, 6)
    step = get_lot_size(pair)
    quantity = round_step_size(quantity, step)

    try:
        order = client.order_market_buy(symbol=pair, quantity=quantity)
        now = datetime.now()
        print(f"{now} - ✅ BUY {symbol}: {quantity} at {price}")
        return order
    except Exception as e:
        print(f"[ERROR] Failed to buy {symbol}: {e}")
        return None


def get_lot_size(symbol):
    exchange_info = client.get_exchange_info()
    for s in exchange_info['symbols']:
        if s['symbol'] == symbol:
            for f in s['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    return f['stepSize']
    return None

def round_step_size(quantity, step_size):
    precision = int(round(-math.log(float(step_size), 10), 0))
    return round(quantity - (quantity % float(step_size)), precision)


def get_balance():
    return float(client.get_asset_balance(asset='USDT')['free'])
def exit_trade(symbol):
    pair = SYMBOL_PAIRS.get(symbol)
    if not pair:
        print(f"Symbol {symbol} not found.")
        return

    try:
        balance = client.get_asset_balance(asset=symbol)
        ticker = client.get_symbol_ticker(symbol=pair)
        price = float(ticker['price'])
        quantity = float(balance["free"])
        if quantity <= 0:
            print(f"No {symbol} available to sell.")
            return

        order = client.order_market_sell(symbol=pair, quantity=round(quantity, 6))
        now = datetime.now()
        print(f"{now} - ✅ SELL {symbol}: {quantity} at {price}")
        return order
    except Exception as e:
        print(f"[ERROR] Failed to sell {symbol}: {e}")
        return None