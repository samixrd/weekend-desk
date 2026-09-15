"""FUNDING-CLOCK FEASIBILITY PROBE — does Bitget stock-perp funding even exist?"""
import json, urllib.request, datetime, math
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=20))
SYMS=["SPYUSDT","QQQUSDT","AAPLUSDT","TSLAUSDT","NVDAUSDT","MSFTUSDT","GOOGLUSDT","AMZNUSDT","METAUSDT","COINUSDT","MSTRUSDT","HOODUSDT","CRCLUSDT","BTCUSDT","ETHUSDT","SOLUSDT"]
print("%-10s %5s %8s %8s %8s %8s %8s" % ("sym","n","mean_bps","std_bps","max_bps","min_bps","pct_nonzero"))
for s in SYMS:
    try:
        d=get(f"https://api.bitget.com/api/v2/mix/market/history-fund-rate?symbol={s}&productType=usdt-futures&pageSize=200")
        rows=d.get('data') or []
        r=[float(x['fundingRate'])*1e4 for x in rows]  # bps per 8h
        if not r: print(s,"no data"); continue
        m=sum(r)/len(r); sd=math.sqrt(sum((x-m)**2 for x in r)/max(1,len(r)-1))
        nz=sum(1 for x in r if abs(x)>0.01)/len(r)*100
        print("%-10s %5d %8.2f %8.2f %8.2f %8.2f %8.1f" % (s,len(r),m,sd,max(r),min(r),nz))
    except Exception as e: print(s,"ERR",e)
# annualized carry implication: mean bps/8h * 3*365
print("\nannualized carry (mean 8h-bps x 1095):")
for s in ["SPYUSDT","AAPLUSDT","TSLAUSDT","BTCUSDT"]:
    try:
        d=get(f"https://api.bitget.com/api/v2/mix/market/history-fund-rate?symbol={s}&productType=usdt-futures&pageSize=200")
        r=[float(x['fundingRate'])*1e4 for x in (d.get('data') or [])]
        print(" %-8s %+.1f%%/yr" % (s, sum(r)/len(r)*1095/1e4*100))
    except Exception as e: print(s,e)
