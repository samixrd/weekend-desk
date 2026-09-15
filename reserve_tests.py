"""
RESEARCH RESERVE tests (do NOT touch WD frozen rule):
T1 — non-overlapping episodes: recompute |z|>2 convergence with cooldown = horizon
     (fixes CTO's n_rows != n_bets critique).
T2 — CONTROL: WD weekend signal vs native gap after partialling out
     Binance/Bybit weekend moves. Strengthening-evidence only.
"""
import json, urllib.request, datetime, math

def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"}), timeout=25))

def binance_1h(sym, days=120):
    end=int(datetime.datetime(2026,9,15).timestamp()*1000); start=end-days*86400000
    out={}; cur=start
    while cur<end:
        rows=get(f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=1h&startTime={cur}&limit=1500")
        if not isinstance(rows,list) or not rows: break
        for r in rows: out[r[0]]=float(r[4])
        cur=rows[-1][0]+3600000
        if len(rows)<1500: break
    return out

def bybit_1h(sym, days=40):
    end=int(datetime.datetime(2026,9,15).timestamp()*1000)
    out={}; cur=end
    while True:
        rows=get(f"https://api.bybit.com/v5/market/kline?category=linear&symbol={sym}&interval=60&end={cur}&limit=1000").get("result",{}).get("list",[])
        if not rows: break
        for r in rows: out[int(r[0])]=float(r[4])
        oldest=min(int(r[0]) for r in rows)
        if oldest < end-days*86400000: break
        cur=oldest-1
    return out

H=3600000
# ---------- T1 non-overlapping episodes ----------
print("=== T1: convergence with episode cooldown (no overlapping bets) ===")
for sym in ["TSLAUSDT","AAPLUSDT","SPYUSDT"]:
    A={k//H*H:v for k,v in binance_1h(sym).items()}; B=None
    # BG history
    out={}; end=None
    stop=int((datetime.datetime(2026,9,15)-datetime.timedelta(days=100)).timestamp()*1000)
    for _ in range(60):
        u=f"https://api.bitget.com/api/v2/mix/market/history-candles?symbol={sym}&productType=usdt-futures&granularity=1H&limit=200"
        if end: u+=f"&endTime={end}"
        rows=get(u).get('data') or []
        if not rows: break
        for r in rows: out[int(r[0])//H*H]=float(r[2])
        oldest=min(int(r[0]) for r in rows)
        if oldest<stop or len(rows)<200: break
        end=oldest-1
    X=out; Y=A
    ks=sorted(set(X)&set(Y))
    D={k: math.log(X[k]/Y[k]) for k in ks if X[k]>0 and Y[k]>0}
    sk=sorted(D); vals=[D[k] for k in sk]
    h=6  # conservative horizon
    episodes=[]; last_fire=None
    for i,k in enumerate(sk):
        win=[D[j] for j in sk[max(0,i-24):i]]
        if len(win)<12: continue
        mu=sum(win)/len(win); sg=math.sqrt(sum((x-mu)**2 for x in win)/len(win)) or 1e-9
        z=(D[k]-mu)/sg
        k2=k+h*H
        if k2 not in D: continue
        if abs(z)>=2.0 and (last_fire is None or (k-last_fire)//H >= h):
            pnl = -z/abs(z)*(D[k2]-D[k])*1e4
            episodes.append(pnl); last_fire=k
    if episodes:
        m=sum(episodes)/len(episodes)
        sd=math.sqrt(sum((x-m)**2 for x in episodes)/max(1,len(episodes)-1))
        t=m/sd*math.sqrt(len(episodes)) if sd else 0
        print("%-9s NON-OVERLAPPING: n=%d  avg %+.1f bps  sd %.1f  t=%+.1f  win%%=%.0f" % (sym,len(episodes),m,sd,t,100*sum(1 for e in episodes if e>0)/len(episodes)))

# ---------- T2 control regression: w_BG on gap, partialling out w_BN, w_BY ----------
def yahoo(sym):
    end=int(datetime.datetime(2026,9,15).timestamp())
    r=get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={end-110*86400}&period2={end}&interval=1d")['chart']['result'][0]
    q=r['indicators']['quote'][0]
    return {datetime.datetime.utcfromtimestamp(t).date():(o,c) for t,o,c in zip(r['timestamp'],q['open'],q['close']) if t and o and c}

def wk_from_hourly(bars, satstr):
    sat=datetime.date.fromisoformat(satstr)
    sat_dt=datetime.datetime(sat.year,sat.month,sat.day,tzinfo=datetime.timezone.utc)
    fri21=int((sat_dt-datetime.timedelta(days=1,hours=3)).timestamp()*1000)
    sun16=int((sat_dt-datetime.timedelta(hours=8)).timestamp()*1000)
    ks=sorted(bars)
    def near(t):
        c=[k for k in ks if abs(k-t)<=2*H]
        return bars[min(c,key=lambda k:abs(k-t))] if c else None
    a=near(fri21+H); b=near(sun16+H)   # closes of those hours
    return (b/a-1) if a and b else None

d=json.load(open(r"D:\wk-probes\weekend_pairs.json"))
def ols3(ys, xs3):  # gap = a + b1*wBG + b2*wBN + b3*wBY
    n=len(ys); X=[[1]+r for r in xs3]
    def matT(A): return [[A[i][j] for i in range(len(A))] for j in range(len(A[0]))]
    Xt=matT(X)
    XX=[[sum(Xt[i][k]*X[k][j] for k in range(n)) for j in range(4)] for i in range(4)]
    XY=[sum(Xt[i][k]*ys[k] for k in range(n)) for i in range(4)]
    # invert 4x4 gauss
    M=[XX[i][:]+[1.0 if i==j else 0.0 for j in range(4)] for i in range(4)]
    for c in range(4):
        p=max(range(c,4),key=lambda r:abs(M[r][c])); M[c],M[p]=M[p],M[c]
        pv=M[c][c]
        if abs(pv)<1e-15: return None
        M[c]=[v/pv for v in M[c]]
        for r in range(4):
            if r!=c:
                f=M[r][c]; M[r]=[M[r][j]-f*M[c][j] for j in range(8)]
    Inv=[[M[i][4+j] for j in range(4)] for i in range(4)]
    beta=[sum(Inv[i][j]*XY[j] for j in range(4)) for i in range(4)]
    resid=[ys[t]-sum(beta[i]*X[t][i] for i in range(4)) for t in range(n)]
    s2=sum(r*r for r in resid)/max(1,n-4)
    se=[math.sqrt(s2*Inv[i][i]) for i in range(4)]
    return beta, [beta[i]/se[i] if se[i] else 0 for i in range(4)], n

print("\n=== T2: gap ~ a + b1*BG + b2*BN + b3*BY (weekend moves, n small — coefficients, not gospel) ===")
for psym,usym in [("SPYUSDT","SPY"),("AAPLUSDT","AAPL"),("TSLAUSDT","TSLA")]:
    BN=binance_1h(psym); BY=bybit_1h(psym); U=yahoo(usym)
    ys=[];xs=[]
    for r in d[psym]:
        wbg=r[1]; wbn=wk_from_hourly(BN,r[0]); wby=wk_from_hourly(BY,r[0])
        if wby is None: continue
        sat=datetime.date.fromisoformat(r[0]); fri=sat-datetime.timedelta(days=1); mon=sat+datetime.timedelta(days=2)
        if wbn is None or (fri not in U or mon not in U): continue
        ys.append(U[mon][0]/U[fri][1]-1); xs.append([wbg,wbn,wby])
    out=ols3(ys,xs)
    if out:
        beta,tv,n=out
        print("%-5s n=%2d  const %+.3f | BG b=%+.2f t=%+.1f | BN b=%+.2f t=%+.1f | BY b=%+.2f t=%+.1f" %
              (usym,n,beta[0]*100,beta[1],tv[1],beta[2],tv[2],beta[3],tv[3]))
    else: print(usym,"singular (collinear venues) — report pairwise instead")
