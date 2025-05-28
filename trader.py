from config import BINANCE_KEY, BINANCE_SECRET, LAYER1_COINS
from binance.client import Client
import os
client = Client(BINANCE_KEY, BINANCE_SECRET)
client.API_URL = 'https://testnet.binance.vision/api'  # <--- use testnet endpoint
SYMBOL_PAIRS = {v: f"{v}USDT" for v in LAYER1_COINS.values()}
def sell_all_non_usdt():
    account = client.get_account()
    all_balances = account["balances"]
    symbols_info = client.get_exchange_info()["symbols"]
    all_pairs = {s["symbol"] for s in symbols_info}

    for asset in all_balances:
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
def enter_trade(symbol, percantage=50):
    current_balance = get_balance()
    usdt_amount = int(percantage*current_balance)
    pair = SYMBOL_PAIRS.get(symbol)
    if not pair:
        print(f"Symbol {symbol} not found.")
        return

    # Get price to calculate quantity
    ticker = client.get_symbol_ticker(symbol=pair)
    price = float(ticker["price"])
    quantity = round(usdt_amount / price, 6)  # rounded to 6 decimal precision

    try:
        order = client.order_market_buy(symbol=pair, quantity=quantity)
        print(f"✅ BUY {symbol}: {quantity} at {price}")
        return order
    except Exception as e:
        print(f"[ERROR] Failed to buy {symbol}: {e}")
        return None

def get_balance():
    return client.get_asset_balance(asset='USDT')

def exit_trade(symbol):
    pair = SYMBOL_PAIRS.get(symbol)
    if not pair:
        print(f"Symbol {symbol} not found.")
        return

    try:
        balance = client.get_asset_balance(asset=symbol)
        quantity = float(balance["free"])
        if quantity <= 0:
            print(f"No {symbol} available to sell.")
            return

        order = client.order_market_sell(symbol=pair, quantity=round(quantity, 6))
        print(f"✅ SELL {symbol}: {quantity}")
        return order
    except Exception as e:
        print(f"[ERROR] Failed to sell {symbol}: {e}")
        return None