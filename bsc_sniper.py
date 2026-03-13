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

# =========================
# BSC CONNECTION
# =========================

w3 = Web3(Web3.HTTPProvider(BSC_RPC))

WBNB = Web3.to_checksum_address("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c")
USDT = Web3.to_checksum_address("0x55d398326f99059fF775485246999027B3197955")

FACTORY = Web3.to_checksum_address("0xca143ce32fe78f1f7019d7d551a6402fc5350c73")

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
# TOKEN ABI
# =========================

TOKEN_ABI = [
    {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"}
]

# =========================
# HELPER FUNCTIONS
# =========================

def get_token_info(token):

    try:
        contract = w3.eth.contract(address=token, abi=TOKEN_ABI)

        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        supply = contract.functions.totalSupply().call()

        return name, symbol, supply

    except:
        return "Unknown", "UNK", 0


def get_dex_data(pair):

    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/bsc/{pair}"
        r = requests.get(url).json()

        pair_data = r["pair"]

        liquidity = float(pair_data["liquidity"]["usd"])
        price = float(pair_data["priceUsd"])
        marketcap = float(pair_data["fdv"])

        return liquidity, price, marketcap

    except:
        return 0, 0, 0


def get_dev_wallet(token):

    try:
        url = f"https://api.bscscan.com/api?module=token&action=tokenholderlist&contractaddress={token}&page=1&offset=10&apikey={BSCSCAN_API}"

        data = requests.get(url).json()

        dev_wallet = data["result"][0]["HolderAddress"]
        dev_balance = float(data["result"][0]["TokenHolderQuantity"])

        return dev_wallet, dev_balance

    except:
        return "Unknown", 0


def send_telegram(message):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, data=data)
    except:
        pass


# =========================
# MAIN SCANNER
# =========================

def scan():

    print("🚀 BSC Token Scanner Started")

    event_filter = factory.events.PairCreated.create_filter(fromBlock='latest')

    while True:

        events = event_filter.get_new_entries()

        for event in events:

            token0 = event["args"]["token0"]
            token1 = event["args"]["token1"]
            pair = event["args"]["pair"]

            if token0 == WBNB or token1 == WBNB:

                token = token0 if token1 == WBNB else token1
                base = "WBNB"

            elif token0 == USDT or token1 == USDT:

                token = token0 if token1 == USDT else token1
                base = "USDT"

            else:
                continue

            name, symbol, supply = get_token_info(token)

            liquidity, price, marketcap = get_dex_data(pair)

            if liquidity < MIN_LIQUIDITY_USD:
                continue

            if marketcap < MIN_MARKETCAP_USD:
                continue

            dev_wallet, dev_balance = get_dev_wallet(token)

            message = f"""
🚀 <b>NEW BSC TOKEN DETECTED</b>

Token: {name} ({symbol})

📄 Contract:
{token}

💰 Liquidity: ${liquidity:,.0f}
💵 Price: ${price}
📊 Market Cap: ${marketcap:,.0f}

👤 Dev Wallet:
{dev_wallet}

📈 Chart
https://dexscreener.com/bsc/{pair}

💰 Buy
https://pancakeswap.finance/swap?outputCurrency={token}

🔎 BscScan
https://bscscan.com/token/{token}
"""

            print(message)
            send_telegram(message)

        time.sleep(2)


if __name__ == "__main__":
    scan()
