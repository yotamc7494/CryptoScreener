import json
settings = None
SETTINGS_PATH = "settings.json"
LAYER1_COINS = None
BINANCE_URL = None
BINANCE_TRADE_URL = None
BINANCE_KEY = None
BINANCE_SECRET = None
SLACK_WEBHOOK_URL = None
SEND_SLACK = None
AUTO_TRADE = None

WHITE = None
GRAY = None
LIGHT_GRAY = None
BLACK = None
GREEN = None

WIDTH = None
HEIGHT = None
BAR_WIDTH = None
BAR_HEIGHT = None
BAR_X = None
BAR_Y = None

BACKTEST_RANGE = None
SWINGS_LOOK_BACK = None
SWING_RANGE = None
TREND_TOLERANCE = None
BUY_RSI = None
ATR_MULT = None
SELL_RSI = None
BUY_STOCH = None
SELL_STOCH = None
BUY_BP = None
SELL_BP = None
RISK_MANAGEMENT = None

def load_settings():
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)

def save_settings(new_settings):
    # Write to settings.json
    with open(SETTINGS_PATH, "w") as f:
        json.dump(new_settings, f, indent=4)
    # Reload globals
    load(new_settings)

def load(s=None):
    global settings, LAYER1_COINS, BINANCE_URL, BINANCE_TRADE_URL
    global BINANCE_KEY, BINANCE_SECRET, SLACK_WEBHOOK_URL
    global SEND_SLACK, AUTO_TRADE
    global WHITE, GRAY, LIGHT_GRAY, BLACK, GREEN
    global WIDTH, HEIGHT, BAR_WIDTH, BAR_HEIGHT, BAR_X, BAR_Y
    global BACKTEST_RANGE, SWINGS_LOOK_BACK, SWING_RANGE, TREND_TOLERANCE
    global BUY_RSI, SELL_RSI, BUY_STOCH, SELL_STOCH, BUY_BP, SELL_BP, RISK_MANAGEMENT

    settings = s if s else load_settings()

    LAYER1_COINS = settings['coins']
    BINANCE_URL = settings["urls"]["binance"]
    BINANCE_TRADE_URL = settings["urls"]["binance trade"]
    BINANCE_KEY = settings["keys and secrets"]["binance key"]
    BINANCE_SECRET = settings["keys and secrets"]["binance secret"]
    SLACK_WEBHOOK_URL = settings["keys and secrets"]['slack key']
    SEND_SLACK = settings["conditions"]["send slack"]
    AUTO_TRADE = settings["conditions"]["auto trade"]

    WHITE = (255, 255, 255)
    GRAY = (200, 200, 200)
    LIGHT_GRAY = (220, 220, 220)
    BLACK = (0, 0, 0)
    GREEN = (50, 200, 100)

    WIDTH = settings['sizes']['width']
    HEIGHT = settings['sizes']['height']
    BAR_WIDTH = WIDTH - 100
    BAR_HEIGHT = 30
    BAR_X = 50
    BAR_Y = HEIGHT - 100

    BACKTEST_RANGE = settings['strategy']["backtest range"]
    SWINGS_LOOK_BACK = settings['strategy']["swing look back"]
    SWING_RANGE = settings['strategy']["swing range"]
    TREND_TOLERANCE = settings['strategy']["trend tolerance"]
    BUY_RSI = settings['strategy']["buy rsi"]
    SELL_RSI = settings['strategy']["sell rsi"]
    BUY_STOCH = settings['strategy']["but stoch"]
    SELL_STOCH = settings['strategy']["sell stoch"]
    BUY_BP = settings['strategy']["buy bp"]
    ATR_MULT = settings['strategy']["atr mult"]
    SELL_BP = settings['strategy']["sell bp"]
    RISK_MANAGEMENT = settings['strategy']["risk management"]

def reload():
    global settings
    global BUY_RSI, SELL_RSI, BUY_STOCH, SELL_STOCH, BUY_BP, SELL_BP, RISK_MANAGEMENT
    global AUTO_TRADE, SEND_SLACK, BACKTEST_RANGE
    global WIDTH, HEIGHT, BAR_WIDTH, BAR_HEIGHT, BAR_X, BAR_Y
    # ... add all other globals you want to update

    with open("settings.json", "r") as f:
        settings = json.load(f)

    # Re-bind variables
    BUY_RSI = settings['strategy']["buy rsi"]
    SELL_RSI = settings['strategy']["sell rsi"]
    BUY_STOCH = settings['strategy']["but stoch"]
    SELL_STOCH = settings['strategy']["sell stoch"]
    BUY_BP = settings['strategy']["buy bp"]
    SELL_BP = settings['strategy']["sell bp"]
    RISK_MANAGEMENT = settings['strategy']["risk management"]
    AUTO_TRADE = settings["conditions"]["auto trade"]
    SEND_SLACK = settings["conditions"]["send slack"]
    BACKTEST_RANGE = settings['strategy']["backtest range"]
    WIDTH, HEIGHT = settings['sizes']['width'], settings['sizes']['height']
    ATR_MULT = settings['strategy']["atr mult"]
    BAR_WIDTH = WIDTH - 100
    BAR_HEIGHT = 30
    BAR_X = 50
    BAR_Y = HEIGHT - 100


# Initial load
load()
