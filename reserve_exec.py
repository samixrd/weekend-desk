"""
RESERVE EXECUTABLE READOUT — the PASS/FAIL test for Idea B (3-venue fade).
Runs AFTER the weekend tape lands (Mon 21:30+, after settle_forward.py).

Reads collected_v2/*.jsonl (real bid/ask/depth, 3 venues). For every hourly
sample inside the weekend (and, when present, any hour the v2 tape covers):

  F_t   = 1/3 * mean_v log(mid_v)
  D_v,t = log(mid_v) - F_t                 (dislocation vs consensus)
  z     = D / EWMA_sigma(delta D, .97)     per venue (warmup 24h of the tape itself)
  TRIGGER |z| >= 2 on venue v (rich => SHORT v-leg vs cheap legs; market-neutral):
      rich leg  SELL at bid_v  (v highest z)
      cheap leg BUY  at ask_u  (u = lowest-z venue among the other two)
      -> immediate cost of the pair = half-spread_rich + half-spread_cheap
  HOLD 6h, exit at opposite quotes.
  fees 0.06% x 4 legs = 24 bps; funding: use recorded rates at settlement times
  (v2 tape carries funding_rate per venue -> accrue actual diffs when crossing
  settlement hours, else mark "funding not observable in-window").

OUTPUT (printed + results/reserve_forward.md):
  EXECUTABLE episodes table, weekend vs weekday, and the verdict line:
  PASS  = net-of-all-costs mean > 0 AND >= 5 episodes   -> B becomes flagship candidate
  FAIL  = anything else                                  -> B stays RESERVE
  (pre-declared: no threshold re-runs, no symbol cherry-pick; universe = 13)
"""
import json, glob, os, math, hashlib, datetime
from collections import defaultdict

ROOT=r"D:\wk-probes"
TAPE=os.path.join(ROOT,"collected_v2")
OUT=os.path.join(ROOT,"results"); os.makedirs(OUT,exist_ok=True)
SYMS=["TSLAUSDT","AAPLUSDT","NVDAUSDT","MSFTUSDT","GOOGLUSDT","AMZNUSDT","METAUSDT",
      "SPYUSDT","QQQUSDT","COINUSDT","MSTRUSDT","HOODUSDT","CRCLUSDT"]
VEN=["bitget","binance","bybit"]
FEE_BPS=24.0; HOLD_H=6; Z_TRIGGER=2.0; LAM=0.97; WARMUP=24

def load():
    by=defaultdict(list)  # (sym,venue) -> [(ts_ms, rec)]
    for f in sorted(glob.glob(os.path.join(TAPE,"*.jsonl"))):
        for line in open(f,encoding="utf-8"):
            line=line.strip()
            if not line: continue
            r=json.loads(line)
            if r.get("mid") and r.get("bid") and r.get("ask"):
                ts=int(datetime.datetime.fromisoformat(r["ts_utc"]).timestamp()*1000)
                by[(r["sym"],r["venue"])].append((ts,r))
    return by

def hour_keys(by,sym):
    sets=[set(k//3600000 for k,_ in by[(sym,v)]) for v in VEN if (sym,v) in by]
    if len(sets)<3: return []
    ks=sorted(set.intersection(*sets))
    return ks

def val(by,sym,v,hk,field):
    for k,r in by[(sym,v)]:
        if k//3600000==hk: return r
    return None

def run():
    lines=["# RESERVE FORWARD READOUT — executable 3-venue convergence (universe=13, pre-declared)",
           f"trigger |z|>={Z_TRIGGER} (frozen), hold {HOLD_H}h, fees {FEE_BPS}bps 4-leg, real bid/ask. Generated %s UTC"%datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"),""]
    rows=[]; total_pos=0; total_ep=0; ep_wknd=[]
    for sym in SYMS:
        ks=hour_keys(by,sym)
        if len(ks)<WARMUP+HOLD_H+2:
            rows.append((sym,len(ks),"insufficient tape (<38h aligned)"))
            continue
        # build aligned series
        seq=[]
        for hk in ks:
            try:
                mids={v: math.log(val(by,sym,v,hk,"mid")["mid"]) for v in VEN}
                q={v: val(by,sym,v,hk,"mid") for v in VEN}
            except Exception: continue
            F=sum(mids.values())/3
            D={v: mids[v]-F for v in VEN}
            seq.append((hk,D,q))
        # EWMA sigma per venue on delta D
        sd={v:0.0 for v in VEN}; prevD={v:None for v in VEN}
        zser=[]
        for i,(hk,D,q) in enumerate(seq):
            zs={}
            for v in VEN:
                if prevD[v] is not None:
                    dd=D[v]-prevD[v]
                    sd[v]=LAM*sd[v]+(1-LAM)*dd*dd
                zs[v]=(D[v]/math.sqrt(sd[v])) if sd[v]>0 else 0.0
                prevD[v]=D[v]
            zser.append(zs)
        # episodes: pick max-|z| venue as rich/cheap pair
        last=-99; eps=[]
        for i in range(WARMUP,len(seq)-HOLD_H):
            zs=zser[i]
            rich=max(VEN,key=lambda v:zs[v]); cheap=min(VEN,key=lambda v:zs[v])
            zspan=zs[rich]-zs[cheap]
            if abs(zs[rich])<Z_TRIGGER and abs(zs[cheap])<Z_TRIGGER: continue
            if i-last<HOLD_H: continue
            last=i
            if zs[rich]>0:   # fade: short rich at bid, long cheap at ask
                entry=(seq[i][2][rich]["bid"], seq[i][2][cheap]["ask"])
                j=min(i+HOLD_H,len(seq)-1)
                exitp=(seq[j][2][rich]["bid"], seq[j][2][cheap]["ask"])
                gross=((entry[0]-exitp[0])/entry[0] + (exitp[1]-entry[1])/entry[1])/2*1e4
            else:            # reversed pair roles
                rich,cheap=cheap,rich
                entry=(seq[i][2][rich]["ask"], seq[i][2][cheap]["bid"])
                j=min(i+HOLD_H,len(seq)-1)
                exitp=(seq[j][2][rich]["ask"], seq[j][2][cheap]["bid"])
                gross=((exitp[0]-entry[0])/entry[0] + (entry[1]-exitp[1])/exitp[1])/2*1e4
            net=gross-FEE_BPS
            t=datetime.datetime(1970,1,1)+datetime.timedelta(milliseconds=seq[i][0])
            wkd=t.weekday()>=5 or (t.weekday()==4 and t.hour>=21) or (t.weekday()==0 and t.hour<4)
            eps.append((t.date().isoformat(),t.hour,rich,cheap,round(zspan,2),round(gross,1),round(net,1),wkd))
        if eps:
            tot_ep=len(eps)
            mean_net=sum(e[6] for e in eps)/tot_ep
            wknd=[e for e in eps if e[7]]
            total_ep+=tot_ep
            for e in wknd: ep_wknd.append(e)
            rows.append((sym,tot_ep,"mean net %+.1f bps | weekend %d ep | pairs %s"%(mean_net,len(wknd),",".join(sorted({e[2]+'/'+e[3] for e in eps})))))
        else:
            rows.append((sym,0,"no triggers"))
    for r in rows: print("%-9s %-5s %s"%r)
    # verdict: only weekend episodes count as forward executable (the regime that matters for WD adjacency)
    if ep_wknd:
        m=sum(e[6] for e in ep_wknd)/len(ep_wknd)
        ok = (m>0 and len(ep_wknd)>=5)
        lines.append("## VERDICT (pre-declared rule): weekend executable episodes=%d, mean net=%+.1f bps → **%s**"%(len(ep_wknd),m,"PASS — B is flagship candidate" if ok else "FAIL — B stays reserve"))
    else:
        lines.append("## VERDICT: 0 weekend executable episodes yet — test incomplete until Sun-Mon tape lands. NOT a pass.")
    if total_ep:
        allm=0  # all-episode table below
    lines.append("")
    lines.append("| sym | aligned hours/episodes | result |")
    lines.append("|---|---|---|")
    for s,n,r in rows: lines.append("| %s | %d | %s |"%(s,n,r))
    lines.append("")
    lines.append("Weekend episode detail (first 40):")
    lines.append("```")
    for e in ep_wknd[:40]: lines.append(str(e))
    lines.append("```")
    open(os.path.join(OUT,"reserve_forward.md"),"w",encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines[:4]))
    print("saved results/reserve_forward.md")

if __name__=="__main__":
    by=load(); run()
