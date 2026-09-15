"""ROUND 7 FEASIBILITY: do Binance/Bybit list US-stock perps with public candle history + weekend bars?"""
import json, urllib.request, datetime

def get(u):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=20))
    except Exception as e:
        return {"_err": str(e)}

print("=== BINANCE USDT-M futures: any stock perp symbols? ===")
d = get("https://fapi.binance.com/fapi/v1/exchangeInfo")
if "_err" in d: print(d["_err"])
else:
    syms = [s["symbol"] for s in d.get("symbols", [])]
    hits = [s for s in syms if any(k in s for k in ["AAPL","TSLA","NVDA","MSFT","META","AMZN","GOOGL","SPY","QQQ","COIN","MSTR","HOOD","CRCL"])]
    print(len(syms), "symbols; stock-like:", hits[:40])

print("\n=== BYBIT linear: symbols ===")
d = get("https://api.bybit.com/v5/market/instruments-info?category=linear&limit=1000")
if "_err" in d: print(d["_err"])
else:
    lst = d.get("result",{}).get("list",[])
    syms = [x["symbol"] for x in lst]
    hits = [s for s in syms if any(k in s for k in ["AAPL","TSLA","NVDA","MSFT","META","AMZN","GOOGL","SPY","QQQ","COIN","MSTR","HOOD","CRCL"])]
    print(len(syms), "symbols; stock-like:", hits[:40])

print("\n=== direct kline probes (whatever names) ===")
tests = [
    ("BINANCE 1h AAPLUSDT", "https://fapi.binance.com/fapi/v1/klines?symbol=AAPLUSDT&interval=1h&limit=10"),
    ("BINANCE 1h TSLAUSDT", "https://fapi.binance.com/fapi/v1/klines?symbol=TSLAUSDT&interval=1h&limit=10"),
    ("BYBIT 1h AAPLUSDT",   "https://api.bybit.com/v5/market/kline?category=linear&symbol=AAPLUSDT&interval=60&limit=10"),
    ("BYBIT 1h TSLAUSDT",   "https://api.bybit.com/v5/market/kline?category=linear&symbol=TSLAUSDT&interval=60&limit=10"),
    ("BYBIT 1h AAPLXUSDT",  "https://api.bybit.com/v5/market/kline?category=linear&symbol=AAPLXUSDT&interval=60&limit=10"),
    ("OKX 1h AAPL-USDT-SWAP","https://www.okx.com/api/v5/market/candles?instId=AAPL-USDT-SWAP&bar=1H&limit=10"),
    ("Gate 1h AAPL_USDT",   "https://api.gateio.ws/api/v4/futures/usdt/candlesticks?contract=AAPL_USDT&interval=1h&limit=10"),
    ("Hyperliquid AAPL",    "https://api.hyperliquid.xyz/info"),
]
for name,u in tests:
    if name.startswith("Hyperliquid"): continue
    d = get(u)
    ok = "_err" not in d and d and (d.get("code") in (None,"0") or "result" in d or isinstance(d,list))
    print("%-22s %s %s" % (name, "OK" if ok else "FAIL", str(d)[:120]))
