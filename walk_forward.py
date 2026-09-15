"""
WALK-FORWARD RUNNER — PROTOCOL.md §5 folds over the weekend event series.

Design (frozen):
  - Event = one weekend (Sat anchor dates from Layer A daily bars; the only
    series long enough to build folds).
  - fold k: FIT on weekends 1..k, TEST on weekend k+1 (expanding window,
    one event per OOS block — blocks-of-4 need more events than exist yet).
  - FIT means: from weekends 1..k choose direction rule {continuation,
    reversal} by max mean PnL (that's the only degree of freedom; the
    frozen headline rule sign(w) is always reported too).
  - All numbers MID-PRICE daily proxy => labeled DESCRIPTIVE until Layer C
    forward weekends accumulate executable folds.

Output: results/walk_forward.md + .json
"""
import json, os, math, datetime

ROOT = r"D:\wk-probes"
OUT  = os.path.join(ROOT, "results"); os.makedirs(OUT, exist_ok=True)
BASK = ["AAPLUSDT","TSLAUSDT","NVDAUSDT","MSFTUSDT","GOOGLUSDT","AMZNUSDT","METAUSDT"]

d = json.load(open(os.path.join(ROOT, "weekend_pairs.json")))
SPY = d["SPYUSDT"]
n = len(SPY)
rows = [(r[1], r[2]) for r in SPY]  # (weekend mid move, next Mon perp session)

def mean(x): return sum(x)/len(x) if x else 0.0
def stddev(x):
    if len(x) < 2: return 0.0
    m = mean(x); return math.sqrt(sum((v-m)**2 for v in x)/(len(x)-1))

folds = []
for k in range(8, n):  # earliest fit window = 8 weekends
    fit = rows[:k]; test = rows[k]
    pnl_cont = [ (1 if w>0 else -1)*mo for w, mo in fit ]
    pnl_rev  = [ -(1 if w>0 else -1)*mo for w, mo in fit ]
    best = "continuation" if mean(pnl_cont) >= mean(pnl_rev) else "reversal"
    sgn = 1 if best == "continuation" else -1
    oos = sgn*(1 if test[0]>0 else -1)*test[1]*100
    frozen = (1 if test[0]>0 else -1)*test[1]*100
    folds.append({"fold_oos_weekend": test[0] and str(SPY[k][0]),
                  "fit_n": k, "fit_rule": best,
                  "oos_ret_pct": round(oos,3),
                  "frozen_sign_rule_ret_pct": round(frozen,3),
                  "always_long_ret_pct": round(test[1]*100,3)})

oos = [f["oos_ret_pct"] for f in folds]
fr = [f["frozen_sign_rule_ret_pct"] for f in folds]
al = [f["always_long_ret_pct"] for f in folds]
def series_stats(x):
    m, s = mean(x), stddev(x)
    return {"n": len(x), "avg_pct_wk": round(m,3), "ir": round(m/s*math.sqrt(52)/math.sqrt(len(x))*math.sqrt(len(x)/52*52/len(x)),2) if s else None}

def ir_ann(x):
    m, s = mean(x), stddev(x)
    return round(m/s*math.sqrt(52),2) if s else None

lines = ["# Walk-forward folds (MID-PRICE DAILY PROXY — DESCRIPTIVE ONLY per §6c)",
         "",
         "Folds fit earliest 8..k weekends, test weekend k+1; OOS calendar span: %s -> %s (%d days)." % (
             SPY[8][0], SPY[-1][0], (datetime.date.fromisoformat(SPY[-1][0])-datetime.date.fromisoformat(SPY[8][0])).days),
         "",
         "| OOS weekend | fit_rule | OOS ret % | frozen sign(w) % | always-long % |",
         "|---|---|---|---|---|"]
for f in folds:
    lines.append("| %s | %s | %+.2f | %+.2f | %+.2f |" % (f["fold_oos_weekend"], f["fit_rule"], f["oos_ret_pct"], f["frozen_sign_rule_ret_pct"], f["always_long_ret_pct"]))
lines += ["",
          "**Aggregate OOS (walk-forward fitted rules): avg %+.2f%%/wk, ann IR %s, n=%d weekends**" % (mean(oos), ir_ann(oos), len(oos)),
          "**Frozen sign(w) rule on same OOS rows:       avg %+.2f%%/wk, ann IR %s**" % (mean(fr), ir_ann(fr)),
          "**Always-long baseline same rows:            avg %+.2f%%/wk**" % mean(al),
          "",
          "Honesty clause: %d calendar days / ~%d independent weekend events; weekend-event inference remains sample-limited." % (
              (datetime.date.fromisoformat(SPY[-1][0])-datetime.date.fromisoformat(SPY[8][0])).days+1, len(folds)),
          "Forward executable folds (Layer C/D) replace this proxy as weekends land; first sealed forward event: 2026-09-21."]

json.dump(folds, open(os.path.join(OUT,"walk_forward.json"),"w"), indent=1)
open(os.path.join(OUT,"walk_forward.md"),"w", encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
