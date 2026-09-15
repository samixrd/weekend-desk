"""
PROBE #4 — CONSENSUS FAILURE vs NATIVE TARGET (the clean object).
Kill the perp-vs-perp mechanical suspicion: per-stock weekend residual
(w_i - C_t, C = mega-basket weekend move) -> that stock's NATIVE Monday
open gap (Yahoo raw quote Open / prior Close).
Also: does consensus C_t predict the mean native gap (benchmark)?
"""
import json, urllib.request, datetime, math

def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=25))

MEGA = {"AAPLUSDT":"AAPL","TSLAUSDT":"TSLA","NVDAUSDT":"NVDA","MSFTUSDT":"MSFT","GOOGLUSDT":"GOOGL","AMZNUSDT":"AMZN","METAUSDT":"META"}
d = json.load(open(r"D:\wk-probes\weekend_pairs.json"))

def yahoo(sym):
    end = int(datetime.datetime(2026,9,15).timestamp())
    u = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={end-100*86400}&period2={end}&interval=1d"
    r = get(u)['chart']['result'][0]
    ts = r['timestamp']; q = r['indicators']['quote'][0]
    return {datetime.datetime.utcfromtimestamp(t).date(): (o,c) for t,o,c in zip(ts,q['open'],q['close']) if t and o and c}
U = {v: yahoo(v) for v in MEGA.values()}

def corr(a,b):
    k=len(a)
    if k<3: return 0,0,0
    ma=sum(a)/k; mb=sum(b)/k
    sxx=sum((x-ma)**2 for x in a); syy=sum((y-mb)**2 for y in b); sxy=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    if sxx==0 or syy==0: return 0,0,0
    r=sxy/math.sqrt(sxx*syy); t=r*math.sqrt((k-2)/(1-r*r)) if abs(r)<1 and k>2 else 0
    return r,sxy/sxx,t

events=[]
for i in range(len(d["AAPLUSDT"])):
    sat = d["AAPLUSDT"][i][0]  # Saturday date of bar
    fri = (datetime.date.fromisoformat(sat) - datetime.timedelta(days=1))
    mon = (datetime.date.fromisoformat(sat) + datetime.timedelta(days=2))
    row = {}
    for p, us in MEGA.items():
        w = d[p][i][1]
        if fri in U[us] and mon in U[us]:
            fc = U[us][fri][1]; mo = U[us][mon][0]
            row[p] = (w, mo/fc-1)
    if len(row)==7:
        events.append(row)
n=len(events); print("weekends with full native alignment:", n)
C = [sum(e[p][0] for p in MEGA)/7 for e in events]

print("\nBENCHMARK: consensus C_t -> mean native gap")
gaps=[sum(e[p][1] for p in MEGA)/7 for e in events]
r,b,t=corr([x*100 for x in C],[x*100 for x in gaps]); print("   r=%+.2f beta=%+.2f t=%+.1f" % (r,b,t))

print("\nRESIDUAL w_i - C_t -> native gap_i:")
neg=0
for p, us in MEGA.items():
    res=[e[p][0]-sum(e[q][0] for q in MEGA)/7 for e in events]
    g=[e[p][1] for e in events]
    r,b,t=corr([x*100 for x in res],[x*100 for x in g])
    rr,bb,tt=corr([x*100 for x in [e[p][0] for e in events]],[x*100 for x in g])
    print("  %-5s own w->gap r=%+.2f t=%+.1f | residual r=%+.2f t=%+.1f %s" % (us,rr,tt,r,t,"** negative" if r<-0.2 else ""))
    neg += r<-0.2
# pooled panel (sign-only test): all 7x n residual->gap pairs, mean next-move by sign
pool_pos=[e[p][1]*100 for e in events for p in MEGA if (e[p][0]-sum(e[q][0] for q in MEGA)/7)>0]
pool_neg=[e[p][1]*100 for e in events for p in MEGA if (e[p][0]-sum(e[q][0] for q in MEGA)/7)<0]
print("\npooled native gap | resid>0: avg %+.3f%% (n=%d) | resid<0: avg %+.3f%% (n=%d)" % (sum(pool_pos)/max(1,len(pool_pos)),len(pool_pos),sum(pool_neg)/max(1,len(pool_neg)),len(pool_neg)))
# placebo: mid-week residual (Tue->Thu vs basket) predicting native Fri gap? need daily bars; skip if complex
# dispersion sanity
print("\nH4 aggregate: trade basket-direction on C_t, fade per-name residual -> per-stock net edge = |resid effect|")
