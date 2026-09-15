"""
WEEKEND DESK ENGINE — executes PROTOCOL.md v1.1 mechanically. No judgment, no tuning.

Modes:
  python engine.py historical   -> Layer A/B daily-proxy rows (descriptive, mid-price)
  python engine.py forward      -> Layer C/D executable rows from collector JSONL (the test)

Reads (read-only):
  collected/*.jsonl                       Layer C snapshots (UTC ISO, hourly weekend)
  (live) Bitget history-fund-rate         Layer D settlements
  (live) Bitget history-candles 1D        Layer A
  (live) Yahoo SPY raw quote O/C          Layer B target

Writes:
  results/historical_rows.json, forward_rows.json, report.md
"""
import json, urllib.request, datetime, math, os, sys, glob

ROOT = r"D:\wk-probes"
OUT  = os.path.join(ROOT, "results"); os.makedirs(OUT, exist_ok=True)

# ---------- frozen constants (mirror PROTOCOL.md — any divergence = bug) ----------
SYM        = "SPYUSDT"
NOTIONAL   = 1000.0
FEE_BPS    = 6.0           # 0.06% per side
SPREAD_GATE_BPS = 30.0     # capacity/operational gate (both anchors)
DEPTH_MULT = 2.0           # impact haircut if depth < 2x notional
IMPACT_BPS = 10.0
MATCH_TOL_MIN = 10
ANCHOR_IN   = (4, 21)      # (dow Fri=4, hour UTC)
ANCHOR_OUT  = (6, 16)      # Sun 16:00
ANCHOR_EXIT = (0, 20)      # Mon 20:00
# ---------------------------------------------------------------------------

def get(u):
    req = urllib.request.Request(u, headers={"User-Agent":"Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=20))

def parse_ts(s): return datetime.datetime.fromisoformat(s)

def samples_for(sym):
    rows=[]
    for f in sorted(glob.glob(os.path.join(ROOT,"collected","*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            r=json.loads(line)
            if r["sym"]==sym: rows.append(r)
    return sorted(rows, key=lambda r: r["utc"])

def match(samples, target):
    """§6c deterministic: nearest sample <=10min, ties->earlier. returns sample or None."""
    best=None
    for s in samples:
        dt=abs((parse_ts(s["utc"])-target).total_seconds())/60.0
        if dt<=MATCH_TOL_MIN:
            if best is None or dt < best[0]:
                best=(dt,s)
    return best[1] if best else None

def funding_between(entry, exit_):
    """Layer D actual settlements in (entry, exit]."""
    try:
        d=get(f"https://api.bitget.com/api/v2/mix/market/history-fund-rate?symbol={SYM}&productType=usdt-futures&pageSize=200")
        tot=0.0; n=0; ok=True
        for r in d.get('data') or []:
            t=datetime.datetime.utcfromtimestamp(int(r['fundingTime'])/1000).replace(tzinfo=datetime.timezone.utc)
            if entry < t <= exit_:
                tot += float(r['fundingRate']); n+=1
        return tot, n, ok
    except Exception:
        return None, 0, False

def gate(smp):
    """symmetric liquidity gates; returns (pass, spread_bps, depth_usd)."""
    if smp is None: return False, None, None
    sp = smp.get("spread_bps")
    side = smp.get("bid_sz",0)*smp.get("bid",0) if smp.get("bid") else 0
    side += 0  # entry-side depth = displayed size on traded side (direction-agnostic worst)
    askd = (smp.get("ask_sz") or 0)*(smp.get("ask") or 0)
    depth = min(side, askd) if smp.get("bid") and smp.get("ask") else None
    passed = (sp is not None and sp <= SPREAD_GATE_BPS and depth is not None and depth >= 100)
    return passed, sp, depth

# ---------- FORWARD (executable, Layer C+D) ----------
def run_forward():
    samples = samples_for(SYM)
    # group by weekend: Fri 00Z -> Mon 21Z
    weekends={}
    for s in samples:
        dt=parse_ts(s["utc"]); key=None
        d=dt.date(); wd=dt.weekday()
        # weekend id = the Monday it feeds
        if wd==4: key=d+datetime.timedelta(days=3)
        elif wd in (5,6): key=(d+datetime.timedelta(days=(7-d.weekday())%7 or 1)) if wd==5 else d+datetime.timedelta(days=1)
        elif wd==0: key=d
        weekends.setdefault(key, []).append(s)
    trades=[]
    for mon in sorted(weekends):
        g=weekends[mon]
        # anchors derived from the Monday it feeds (mon = Monday date, 00:00 UTC base)
        mon_dt=datetime.datetime(mon.year,mon.month,mon.day,tzinfo=datetime.timezone.utc)
        a_in  = mon_dt - datetime.timedelta(days=2, hours=3)   # Fri 21:00 UTC
        a_out = mon_dt - datetime.timedelta(hours=8)           # Sun 16:00 UTC
        a_exi = mon_dt + datetime.timedelta(hours=20)          # Mon 20:00 UTC
        s_in = match(g, a_in) or match(samples, a_in)
        s_out= match(g, a_out) or match(samples, a_out)
        s_exi= match(g, a_exi) or match(samples, a_exi)
        if not (s_in and s_out and s_exi):
            trades.append({"monday":str(mon),"status":"missing anchors",
                           "have_in":bool(s_in),"have_out":bool(s_out),"have_exit":bool(s_exi)})
            continue
        w = s_out["mid"]/s_in["mid"] - 1
        pos = 1 if w>0 else (-1 if w<0 else 0)
        # gates: ENTRY anchor = s_out (Sun 16:00, where fills happen), EXIT = s_exi
        gp_en,sp_en,dp_en = gate(s_out); gp_ex,sp_ex,dp_ex = gate(s_exi)
        row={"monday":str(mon),"w_pct":round(w*100,3),"position":pos,
             "signal_in":{"ts":s_in["utc"],"mid":s_in["mid"]},
             "entry":{"ts":s_out["utc"],"bid":s_out["bid"],"ask":s_out["ask"],"spread_bps":sp_en,"depth_usd":round(dp_en or 0,1),"gate":"PASS" if gp_en else "FAIL"},
             "exit":{"ts":s_exi["utc"],"bid":s_exi["bid"],"ask":s_exi["ask"],"spread_bps":sp_ex,"depth_usd":round(dp_ex or 0,1),"gate":"PASS" if gp_ex else "FAIL"}}
        if pos==0:
            row["status"]="NO_POSITION (w==0; counted in denominator)"; trades.append(row); continue
        if not gp_en:
            row["status"]="FAILURE: entry not executable"; trades.append(row); continue
        # fills
        if pos==1:
            entry_px, exit_px = s_out["ask"], s_exi["bid"]
        else:
            entry_px, exit_px = s_out["bid"], s_exi["ask"]
        gross = (exit_px/entry_px - 1)*pos*100
        costs = FEE_BPS*2/100  # bps->pct: fee both sides (0.06%*2 = 0.12)
        slip  = ((sp_en or 0)/2 + (sp_ex or 0)/2)/1e4*100
        imp   = (IMPACT_BPS*2/1e4*100) if (not gp_ex or (dp_en or 9e9)<DEPTH_MULT*NOTIONAL or (dp_ex or 9e9)<DEPTH_MULT*NOTIONAL) else 0.0
        fsum, fn, fok = funding_between(parse_ts(s_out["utc"]), parse_ts(s_exi["utc"]))
        fund_pct = (-pos*fsum*100) if fok else None   # long pays positive rates
        net = gross - costs - slip - imp + (fund_pct or 0)
        row.update({"gross_pct":round(gross,3),"fee_pct":costs,"slip_pct":round(slip,3),
                    "impact_pct":imp,"funding_pct":round(fund_pct,3) if fund_pct is not None else "NOT RECONSTRUCTABLE",
                    "net_pct":round(net,3),
                    "status":"OK" if gp_ex else "FAILURE: exit not executable (marked at mid, kept)"})
        trades.append(row)
    json.dump(trades, open(os.path.join(OUT,"forward_rows.json"),"w"), indent=1)
    print(json.dumps(trades, indent=1))
    return trades

# ---------- HISTORICAL (Layer A proxy, descriptive only) ----------
def run_historical():
    d=json.load(open(r"D:\wk-probes\weekend_pairs.json"))
    rows=d[SYM]
    stats={"n":len(rows),
           "always_long_avg_pct":round(sum(r[2] for r in rows)/len(rows)*100,3),
           "cont_avg_pct":round(sum((1 if r[1]>0 else -1)*r[2] for r in rows)/len(rows)*100,3),
           "excess_over_baseline_pct":round(sum((1 if r[1]>0 else -1)*r[2]-sum(x[2] for x in rows)/len(rows) for r in rows)/len(rows)*100,3),
           "label":"MID-PRICE DAILY PROXY — DESCRIPTIVE ONLY, not executable (Round-4 §6c)"}
    print(json.dumps(stats,indent=1))
    json.dump(stats, open(os.path.join(OUT,"historical_rows.json"),"w"), indent=1)

if __name__=="__main__":
    if "forward" in sys.argv: run_forward()
    else: run_historical()
