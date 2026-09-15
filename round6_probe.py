"""
PROBE #2: Consensus failure + #3 basis feasibility checks.
(a) can we get basis HISTORY (index/mark candles)? -> endpoint probe
(b) cross-sectional residual test on weekend moves:
    C_t = mean weekend return of 13 stock perps (common equity shock)
    resid_i = w_i - beta_i*C_t (beta=1 simple version first)
    does resid sign predict per-stock Monday session beyond the common part?
"""
import json, urllib.request, datetime, math
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=20))

# (a) basis history availability
for name,u in [("index-candles","https://api.bitget.com/api/v2/mix/market/index-candles?symbol=SPYUSDT&productType=usdt-futures&granularity=1D&limit=5"),
               ("mark-price","https://api.bitget.com/api/v2/mix/market/mark-price-candles?symbol=SPYUSDT&productType=usdt-futures&granularity=1D&limit=5"),
               ("history-mark","https://api.bitget.com/api/v2/mix/market/history-mark-price?symbol=SPYUSDT&productType=usdt-futures&limit=5")]:
    try:
        d=get(u); print("(a) %-12s OK: %s" % (name, str(d.get('data'))[:100]))
    except Exception as e: print("(a) %-12s %s" % (name, e))

# (b) consensus residual test using daily candles (rebuild weekend pairs incl. more names)
STOCKS=["AAPLUSDT","TSLAUSDT","NVDAUSDT","MSFTUSDT","GOOGLUSDT","AMZNUSDT","METAUSDT","SPYUSDT","QQQUSDT","COINUSDT","MSTRUSDT","HOODUSDT","CRCLUSDT"]
def daily(sym):
    out={}; end=None
    for _ in range(6):
        u=f"https://api.bitget.com/api/v2/mix/market/history-candles?symbol={sym}&productType=usdt-futures&granularity=1D&limit=200"
        if end: u+=f"&endTime={end}"
        d=get(u); rows=d.get('data') or []
        if not rows: break
        for r in rows: out[int(r[0])]=(float(r[1]),float(r[2]))
        if len(rows)<200: break
        end=min(int(r[0]) for r in rows)-1
    return out
P={s:daily(s) for s in STOCKS}
common=sorted(set.intersection(*[set(v) for v in P.values()]))
def dow(ts): return datetime.datetime.utcfromtimestamp(ts/1000).weekday()

events=[]
for ts in common:
    if dow(ts)!=5: continue
    t2, t3 = ts+2*86400000, ts+3*86400000
    if t2 not in common or t3 not in common: continue
    row={}
    for s in STOCKS:
        w=P[s][t2][0]/P[s][ts][0]-1      # weekend move (Fri close print -> Sun16)
        mo=P[s][t3][0]/P[s][t2][0]-1     # Monday session
        row[s]=(w,mo)
    events.append(row)
n=len(events); print("\n(b) weekends:", n)

# common shock = mean weekend move of the 7 mega stocks (excl crypto-linked)
MEGA=["AAPLUSDT","TSLAUSDT","NVDAUSDT","MSFTUSDT","GOOGLUSDT","AMZNUSDT","METAUSDT"]
def corr(a,b):
    k=len(a); ma=sum(a)/k; mb=sum(b)/k
    sxx=sum((x-ma)**2 for x in a); syy=sum((y-mb)**2 for y in b); sxy=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    if sxx==0 or syy==0: return 0,0,0
    r=sxy/math.sqrt(sxx*syy); t=r*math.sqrt((k-2)/(1-r*r)) if abs(r)<1 and k>2 else 0
    return r,sxy/sxx,t

print("\nConsensus C_t (mega mean weekend) -> mega mean Monday session:")
rc,bc,tc = corr([sum(e[s][0] for s in MEGA)/7*100 for e in events], [sum(e[s][1] for s in MEGA)/7*100 for e in events])
print("   r=%+.2f beta=%+.2f t=%+.1f" % (rc, bc, tc))
for s in STOCKS:
    C=[sum(e[x][0] for x in MEGA)/7 for e in events]
    w=[e[s][0] for e in events]; mo=[e[s][1] for e in events]
    resid=[x-c for x,c in zip(w,C)]   # beta=1 version
    r_c,b_c,t_c = corr([c*100 for c in C],[m*100 for m in mo])
    r_r,b_r,t_r = corr([x*100 for x in resid],[m*100 for m in mo])
    print("%-10s consensus: r=%+.2f t=%+.1f | residual: r=%+.2f t=%+.1f" % (s, r_c,t_c, r_r,t_r))
# H4 test: does TOTAL dispersion (stdev of weekend moves) predict Monday reversal magnitude?
disp=[max(e[s][0] for s in MEGA)-min(e[s][0] for s in MEGA) for e in events]
mo_mega=[sum(e[s][1] for s in MEGA)/7*100 for e in mo and events]
r,b,t=corr([x*100 for x in disp],mo_mega)
print("\ndispersion -> Monday: r=%+.2f t=%+.1f" % (r,t))
