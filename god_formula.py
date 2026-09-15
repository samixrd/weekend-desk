"""
GOD-VIEW FORMULA STACK — runs on venue_index.json (3 venues, 1h, ~42d).
No mid-price illusions: every leg labeled with what it is and which cost
layer is historically observable.

F1  COMMON FACTOR      F_t   = (1/V) Σ_v log P_{i,v,t}          [latent price proxy]
F2  VENUE DISLOCATION  D_t   = log P_BG − log P_BN (pairwise 3 ways)
F3  NET-OF-CARRY BASIS Bn_t  = D_t − Σ_future(fund_A − fund_B)·τ   [NEW: needs both venues' funding]
F4  NORMALIZATION      z_t   = Bn_t / EWMA_σ(ΔBn, λ=0.97)        [shock units, not %]
F5  OU HALF-LIFE       κ from AR(1) on D: ΔD_t = −κ D_{t−1} dt; HL = ln2/κ
F6  LEAD-LAG GATE      only fire when leader (lagged corr > .4) has already moved:
                       use ΔF_t (common factor move) as the "information" leg
SIGNAL                 trade z: short rich venue leg / long cheap venue leg
                       exit at zero-crossing OR 6h stop-clock
STATS                  non-overlap episodes; t; hit%; gross bps; net-vs-fee-floor (24bps)
                       PLUS regime split: weekend vs weekday, market-open vs closed
PLACEBOS               (a) same rule on BTC/ETH-style synthetic: shuffle venue labels
                       (b) |z|>2 at random non-signal hours
"""
import json, math, datetime, os

IDX = json.load(open(r"D:\wk-probes\venue_index.json"))
H = 3600000
def dt(ms): return datetime.datetime(1970,1,1)+datetime.timedelta(milliseconds=ms)

def aligned(sym):
    """hour keys present in all 3 venues (bars are open-time keyed closes)"""
    v1=IDX[sym]["bitget"]["bars"]; v2=IDX[sym]["binance"]["bars"]; v3=IDX[sym]["bybit"]["bars"]
    ks=sorted(set(map(int,v1))&set(map(int,v2))&set(map(int,v3)))
    return [(k, math.log(float(v1[str(k)])), math.log(float(v2[str(k)])), math.log(float(v3[str(k)]))) for k in ks if k%3600000==0]

def funding_rate(idx, sym, v, ts):
    f=IDX[sym][v]["fund"]
    ks=sorted(map(int,f))
    prev=[k for k in ks if k<=ts]
    return float(f[str(prev[-1])]) if prev else 0.0

def ewma_vol(x, lam=0.97):
    v=0.0; out=[]
    for a in x:
        v = lam*v + (1-lam)*(a*a if a==a else 0)
        out.append(math.sqrt(v) if v>0 else 1e-9)
    return out

def run(sym, A="bitget", B="binance"):
    al=aligned(sym)
    if len(al)<500: print(sym,"insufficient",len(al)); return
    # F1 common factor; F2 dislocation = A vs 3-venue consensus
    D=[]
    for k,la,lb,lc in al:
        D.append(la-((la+lb+lc)/3))  # A vs consensus (uses all 3 venues — F1)
    # F3 net of carry: subtract expected funding differential A-B over next 6h
    ts=[k for k,_,_,_ in al]
    dn=[]
    for i,(k,la,lb,lc) in enumerate(al):
        fut=0.0
        for j in range(6):
            if i+j>=len(al): break
            fut += (funding_rate(IDX,sym,A,ts[i+j])-funding_rate(IDX,sym,B,ts[i+j]))
        dn.append(D[i]-fut)   # net-of-carry dislocation
    # F4 normalize on changes
    dD=[dn[i]-dn[i-1] for i in range(1,len(dn))]
    sd=ewma_vol(dD)
    z=[dn[i]/sd[i-1] if i>0 else 0 for i in range(len(dn))]
    # F5 OU half-life on raw D
    x=[D[i-1] for i in range(1,len(D))]; y=[D[i]-D[i-1] for i in range(1,len(D))]
    n=len(x); mx=sum(x)/n; my=sum(y)/n
    sxx=sum((v-mx)**2 for v in x); sxy=sum((a-mx)*(b-my) for a,b in zip(x,y))
    kappa=-sxy/sxx; hl=math.log(2)/kappa if kappa>0 else float("nan")
    # SIGNAL backtest: |z|>2 -> fade D (short A-leg vs consensus), 6h hold, non-overlap
    trades=[]; last=-99
    weekend=lambda k:(dt(k).weekday()>=5 or (dt(k).weekday()==4 and dt(k).hour>=21) or (dt(k).weekday()==0 and dt(k).hour<4))
    for i in range(len(z)):
        if abs(z[i])>=2.0 and i-last>=6:
            j=min(i+6,len(z)-1)
            pnl=-(D[j]-D[i])*1e4*(1 if z[i]>0 else -1)
            trades.append((ts[i],pnl,weekend(ts[i])))
            last=i
    if not trades: print(sym,"no episodes"); return
    allp=[t[1] for t in trades]; w=[t for t in trades if t[2]]; e=[t for t in trades if not t[2]]
    def st(g):
        if not g: return "n=0"
        p=[x[1] for x in g]; m=sum(p)/len(p)
        sd=math.sqrt(sum((x-m)**2 for x in p)/max(1,len(p)-1))
        return "n=%d avg %+.1f bps sd %.0f t=%+.1f hit %.0f%%" % (len(p),m,sd,(m/sd*math.sqrt(len(p)) if sd else 0),100*sum(1 for x in p if x>0)/len(p))
    print("== %s  (%s vs consensus) ==" % (sym,A))
    print("   OU half-life: %.1f h | episodes: ALL %s" % (hl, st(trades)))
    print("   weekend: %s" % st(w));  print("   weekday: %s" % st(e))

if __name__=="__main__":
    for s in ["TSLAUSDT","AAPLUSDT","SPYUSDT","NVDAUSDT"]:
        try: run(s)
        except Exception as ex: print(s,"ERR",ex)
