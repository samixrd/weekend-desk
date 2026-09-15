"""
AUTO-SETTLEMENT — runs Monday 21:30 UTC (Sep 21) via scheduled task.
Mechanical only: executes engine.py forward, renders sealed prediction result,
commits + pushes. No judgment, no editing of rules. If engine fails, the
failure itself is committed (no silence).
"""
import subprocess, datetime, os, json, sys

ROOT = r"D:\wk-probes"
os.chdir(ROOT)

def sh(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")

# 1. forward rows
rc, out = sh(f'python "{os.path.join(ROOT,"engine.py")}" forward')
if rc != 0:
    # honest failure path
    with open(os.path.join(ROOT,"results","FORWARD_RESULT.md"),"w",encoding="utf-8") as f:
        f.write("# Forward settlement FAILED to execute\n\n```\n"+out[-4000:]+"\n```\n")
    sh('git add -A && git -c user.email=samixrd@local -c user.name="samixrd" commit -m "auto-settle: engine failure recorded verbatim" && git push -q origin master')
    sys.exit(0)

rows = json.load(open(os.path.join(ROOT,"results","forward_rows.json")))

# 2. render against PREDICTION_SEALED.md failure conditions
lines = ["# Forward test result — sealed rule, settled %s UTC" % datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"), ""]
for t in rows:
    lines.append("## Weekend feeding Monday %s" % t.get("monday"))
    if "status" not in t: continue
    if t.get("position") in (None,) or "anchors" in str(t.get("status","")):
        lines.append("- **MISSING ANCHORS** — collector did not cover an anchor: %s" % t); continue
    lines.append("- signal w (Sun16/Fri21 mid): **%+.3f%%** → position: %s" % (t["w_pct"], {1:"LONG",0:"NO POSITION (recorded, kept in denominator)","-1":"SHORT"}.get(t["position"])))
    e=t["entry"]; x=t["exit"]
    lines.append("- entry gate: %s (spread %.1f bps, depth $%.0f) | exit gate: %s (spread %.1f bps, depth $%.0f)" % (e["gate"], e["spread_bps"] or -1, e["depth_usd"] or -1, x["gate"], x["spread_bps"] or -1, x["depth_usd"] or -1))
    if "net_pct" in t:
        lines.append("- gross %+.3f%% → fee %.2f%% → funding %s → slippage %.3f%% → impact %.2f%% → **NET %+.3f%%**" % (
            t["gross_pct"], t["fee_pct"], t["funding_pct"], t["slip_pct"], t["impact_pct"], t["net_pct"]))
    lines.append("- status: **%s**" % t["status"])
    lines.append("")
lines.append("_No rescue clause in effect: whatever this page says is the result._")
open(os.path.join(ROOT,"results","FORWARD_RESULT.md"),"w",encoding="utf-8").write("\n".join(lines))

# 3. publish
sh('git add -A && git -c user.email=samixrd@local -c user.name="samixrd" commit -m "FORWARD SETTLEMENT: sealed prediction result published unedited" && git push -q origin master')
print("settled + pushed")
print("\n".join(lines))
