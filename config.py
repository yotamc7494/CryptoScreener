LAYER1_COINS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "avalanche-2": "AVAX",
    "polkadot": "DOT",
    "cardano": "ADA",
    "binancecoin": "BNB",
    "cosmos": "ATOM",
    "near": "NEAR",
    "algorand": "ALGO",
    "harmony": "ONE",
    "elrond-erd-2": "EGLD",
    "aptos": "APT",
    "tezos": "XTZ",
    "fantom": "FTM",
    "hedera-hashgraph": "HBAR",
    "flow": "FLOW",
    "kava": "KAVA",
    "thorchain": "RUNE",
    "mina-protocol": "MINA"
}
BINANCE_URL = "https://api.binance.com/api/v3/klines"
BINANCE_TRADE_URL = 'https://testnet.binance.vision/api'
BINANCE_KEY = "8ETWjaWSIyMOydI3lGmql9fj9QlPTYV3ZDcqcLtLiDdSPWwkNz1UWgV9PXW1FuVK"
BINANCE_SECRET = "JKnCRJzUZCCvpkkc8crKrUzTPHeY3GuCFGohglJZY71BuSyr1QwLShznMDu0OIes"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"
SEND_SLACK = False
AUTO_TRADE = True

#colors
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
LIGHT_GRAY = (220, 220, 220)
BLACK = (0, 0, 0)
GREEN = (50, 200, 100)

#positions and sizes
WIDTH, HEIGHT = 600, 400
BAR_WIDTH = WIDTH - 100
BAR_HEIGHT = 30
BAR_X = 50
BAR_Y = HEIGHT - 100

#strategy
SWINGS_LOOK_BACK = 100
SWING_RANGE = 3
TREND_TOLERANCE = 0.005
BUY_RSI = 35
SELL_RSI = 65
BUY_STOCH = 20
SELL_STOCH = 80
BUY_BP = 0.25
SELL_BP = 0.75
RISK_MANAGEMENT = 0.5
