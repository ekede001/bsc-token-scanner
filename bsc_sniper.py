# bsc_sniper.py
import time
import requests
from web3 import Web3

# =========================
# CONFIGURATION
# =========================
BSC_RPC = "https://bsc-dataseed.binance.org/"
BSCSCAN_API = "YOUR_BSCSCAN_API_KEY"

TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

MIN_LIQUIDITY_USD = 1000
MIN_MARKETCAP_USD = 30000
MAX_DEV_HOLDING = 10  # percent

# Key base tokens
WBNB = Web3.to_checksum_address("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
USDT = Web3.to_checksum_address("0x55d398326f99059fF775485246999027B3197955")

# PancakeSwap V2 Factory
FACTORY = Web3.to_checksum_address("0xca143ce32fe78f1f7019d7d551a6402fc5350c73")
w3 = Web3(Web3.HTTPProvider(BSC_RPC))

# Minimal Factory ABI to detect new pairs
FACTORY_ABI = [{
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "token0", "type": "address"},
        {"indexed": True, "name": "token1", "type": "address"},
        {"indexed": False, "name": "pair", "type": "address"},
        {"indexed": False, "name": "", "type": "uint256"}
    ],
    "name": "PairCreated",
    "type": "event"
}]
factory = w3.eth.contract(address=FACTORY, abi=FACTORY_ABI)

# =========================
# Helper Functions
# =========================
def get_token_info(token):
    return {"name": "TEST", "symbol": "TST", "totalSupply": 1000000}

def get_liquidity(pair):
    return 10000  # mock liquidity

def get_price_and_marketcap(pair, token):
    price = 0.00001
    marketcap = 100000
    return price, marketcap

def get_dev_wallet(token):
    return "0xDevWalletMock", 5

def check_contract_renounced(token):
    return True

def check_liquidity_lock(pair):
    return True, 100

def detect_bundle_buy(token):
    return 2

def check_honeypot_and_tax(token):
    return False, 5, 5

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram send error:", e)

# =========================
# Main Scanner
# =========================
def scan(simulation=False):
    print("🚀 BSC Ultra-Fast Sniper Scanner Started")
    
    if simulation:
        # Test mode: fake events for both WBNB and USDT
        print("🔹 Running in SIMULATION mode 🔹")
        event_list = [
            {"args":{"token0": "0xTokenMock0", "token1": WBNB, "pair":"0xPairMockWBNB"}},
            {"args":{"token0": "0xTokenMock1", "token1": USDT, "pair":"0xPairMockUSDT"}}
        ]
    else:
        event_filter = factory.events.PairCreated.create_filter(fromBlock='latest')

    while True:
        events = event_list if simulation else event_filter.get_new_entries()
        for event in events:
            token0 = event["args"]["token0"]
            token1 = event["args"]["token1"]
            pair = event["args"]["pair"]

            # Determine base token: WBNB or USDT
            if token0 == WBNB or token1 == WBNB:
                token = token0 if token1 == WBNB else token1
                base = "WBNB"
            elif token0 == USDT or token1 == USDT:
                token = token0 if token1 == USDT else token1
                base = "USDT"
            else:
                continue  # ignore other pairs

            liquidity = get_liquidity(pair)
            if liquidity < MIN_LIQUIDITY_USD:
                continue

            price, marketcap = get_price_and_marketcap(pair, token)
            if marketcap < MIN_MARKETCAP_USD:
                continue

            dev_wallet, dev_percent = get_dev_wallet(token)
            if dev_percent > MAX_DEV_HOLDING:
                continue

            ownership = "Renounced ✅" if check_contract_renounced(token) else "Not Renounced ❌"
            lock_status, lock_percent = check_liquidity_lock(pair)
            honeypot, buy_tax, sell_tax = check_honeypot_and_tax(token)
            bundle_count = detect_bundle_buy(token)

            message = f"""
🚀 <b>NEW BSC TOKEN DETECTED</b>

Token: {token}
Pair: {pair} ({base})

💰 Liquidity: ${liquidity}
💵 Price: ${price}
📊 Market Cap: ${marketcap}

👤 Dev Wallet: {dev_wallet}
📊 Dev Holding: {dev_percent:.2f}%
🔑 Ownership: {ownership}
🔒 Liquidity Lock: {lock_percent}% Locked

🍯 Honeypot: {"YES ❌" if honeypot else "NO ✅"}
💸 Buy Tax: {buy_tax}%
💸 Sell Tax: {sell_tax}%
📦 Bundle Buys: {bundle_count} wallets

📈 Chart: https://dexscreener.com/bsc/{pair}
💰 Buy Link: https://pancakeswap.finance/swap?outputCurrency={token}
"""
            print(message)
            send_telegram(message)

        time.sleep(5)
        if simulation:
            break  # run once in simulation mode

if __name__ == "__main__":
    # Set simulation=True to immediately test Telegram + logs
    scan(simulation=True) 
