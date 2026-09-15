"""self-test: feed synthetic collector rows through run_forward matching, verify anchors/fills/gates."""
import json, os, datetime, importlib.util
ROOT=r"D:\wk-probes"; TMP=os.path.join(ROOT,"testcollected")
os.makedirs(TMP, exist_ok=True)
# monkeypatch: point samples_for at TMP by writing files there and patching glob
import engine
orig_glob = engine.glob.glob
engine.glob.glob = lambda pat: orig_glob(os.path.join(TMP,"*.jsonl"))

def s(utc, bid, ask, bsz, asz):
    return {"utc":utc,"sym":"SPYUSDT","bid":bid,"ask":ask,"mid":(bid+ask)/2,
            "spread_bps":(ask-bid)/((bid+ask)/2)*1e4,"bid_sz":bsz,"ask_sz":asz}
rows=[
  s("2026-09-18T21:00:10+00:00", 660.10, 660.14, 5, 5),   # Fri 21 anchor (within 10min)
  s("2026-09-18T21:15:00+00:00", 660.20, 660.24, 5, 5),   # too far? 15min -> ignore
  s("2026-09-20T16:00:05+00:00", 666.00, 666.50, 3, 0.1), # Sun 16: mid up -> LONG, entry ask 666.50; depth ask 0.1*666.5=66.65<100 gate? 66>100 false
  s("2026-09-21T20:00:20+00:00", 667.00, 667.20, 5, 5),   # Mon 20 exit bid 667.00
]
with open(os.path.join(TMP,"2026-09-18.jsonl"),"w") as f:
    for r in rows: f.write(json.dumps(r)+"\n")

tr = engine.run_forward()
print("\n=== CHECKS ===")
t=tr[0]
assert t["w_pct"]>0 and t["position"]==1, "direction"
assert "16:00" in t["entry"]["ts"], "entry anchor must be Sun 16:00"
assert "20:00" in t["exit"]["ts"], "exit anchor must be Mon 20:00"
assert t["entry"]["gate"]=="FAIL" and t["status"]=="FAILURE: entry not executable", f"66usd ask depth must fail gate, got {t}"
print("ALL CHECKS PASS")
print("entry:",t["entry"]["ts"],t["entry"]["gate"],"| status:",t["status"])
