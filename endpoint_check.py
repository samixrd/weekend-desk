import json, urllib.request
def get(u):
    req=urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=15))

# tickers (one call, all symbols: bid/ask)
d=get("https://api.bitget.com/api/v2/mix/market/tickers?productType=usdt-futures")
row=[x for x in d['data'] if x['symbol']=='AAPLUSDT'][0]
print("ticker fields:", {k:row[k] for k in ['symbol','bidPr','askPr','bestBid','bestAsk'] if k in row})
print("full keys:", list(row.keys()))

# order book
d=get("https://api.bitget.com/api/v2/mix/market/order-book?symbol=AAPLUSDT&productType=usdt-futures&limit=5")
print("\nbook keys:", list(d.keys()), "bids0:", d['data']['bids'][:2], "asks0:", d['data']['asks'][:2])

# open interest
try:
    d=get("https://api.bitget.com/api/v2/mix/market/open-interest?symbol=AAPLUSDT&productType=usdt-futures")
    print("\nOI:", d['data'])
except Exception as e:
    print("OI err", e)

# funding rate
try:
    d=get("https://api.bitget.com/api/v2/mix/market/current-fund-rate?symbol=AAPLUSDT&productType=usdt-futures")
    print("funding:", d['data'])
except Exception as e:
    print("fund err", e)
