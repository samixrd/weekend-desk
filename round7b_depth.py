"""ROUND 7b: venue history depth + weekend coverage + first lead-lag probe."""
import json, urllib.request, datetime, math

def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=25))

def binance_1h(sym, days=90):
    end = int(datetime.datetime(2026,9,15).timestamp()*1000)
    start = end - days*86400000
    out=[]; cur=start
    while cur < end:
        u=f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=1h&startTime={cur}&limit=1500"
        rows=get(u)
        if not isinstance(rows,list) or not rows: break
        out += rows
        cur = rows[-1][0]+3600000
        if len(rows)<1500: break
    return out  # [openTime, o,h,l,c,v,...]

def bybit_1h(sym, days=90):
    end = int(datetime.datetime(2026,9,15).timestamp()*1000)
    u=f"https://api.bybit.com/v5/market/kline?category=linear&symbol={sym}&interval=60&end={end}&limit=1000"
    rows=get(u).get("result",{}).get("list",[])
    out=[]; cur_end=end
    while rows:
        out+=rows
        oldest=int(rows[-1][0])
        u=f"https://api.bybit.com/v5/market/kline?category=linear&symbol={sym}&interval=60&end={oldest-1}&limit=1000"
        rows=get(u).get("result",{}).get("list",[])
        if oldest < end-days*86400000: break
    return out  # [start,o,h,l,c,v,turnover]

for sym in ["SPYUSDT","AAPLUSDT","TSLAUSDT"]:
    b = binance_1h(sym, days=120)
    y = bybit_1h(sym, days=40)
    bo = datetime.datetime.utcfromtimestamp(b[0][0]/1000) if b else None
    yo = datetime.datetime.utcfromtimestamp(int(y[-1][0])/1000) if y else None
    # weekend bars? count Sat/Sun bars with vol>0 in Binance set
    wkn = sum(1 for r in b if datetime.datetime.utcfromtimestamp(r[0]/1000).weekday()>=5 and float(r[7])>0)
    print("%-9s BINANCE bars=%d oldest=%s weekend-vol-bars=%d | BYBIT bars=%d oldest=%s" % (sym, len(b), bo, wkn, len(y), yo))
