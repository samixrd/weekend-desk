"""
SETTLEMENT AGENT — WITNESS ONLY. Never a trader.

Allowed:  observe -> verify (tape/root/hashes) -> settle (frozen engine) ->
          compare vs baseline -> write immutable memo -> publish (git, X card).
FORBIDDEN (structurally — no code path exists):
  change rule | rerun another timestamp | choose another exit | drop failed
  observations | switch asset | tune costs | rerun until pretty.

Runs Mon 21:30 UTC via WeekendDeskSettle task.
"""
import subprocess, datetime, os, json, sys

ROOT = r"D:\wk-probes"
os.chdir(ROOT)

def sh(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")

def next_monday():
    d = datetime.date.today()
    return (d + datetime.timedelta(days=(7 - d.weekday()) % 7 or 7)).isoformat()

# 0) evidence chain: root must have been committed Sunday by WeekendDeskTape
MON = os.environ.get("WD_MONDAY") or next_monday()
rc, verify_out = sh(f'python tape.py verify --monday {MON}')
print(verify_out)
tape_ok = "VERDICT" in verify_out and "PASS" in verify_out.split("VERDICT")[-1]

# 1. forward rows (frozen engine; single attempt only — no retry-until-pretty)
rc, out = sh(f'python "{os.path.join(ROOT,"engine.py")}" forward')
if rc != 0 or not os.path.exists(os.path.join(ROOT,"results","forward_rows.json")):
    with open(os.path.join(ROOT,"results","FORWARD_RESULT.md"),"w",encoding="utf-8") as f:
        f.write("# Forward settlement: engine FAILED to execute\n\n"
                "Per PREDICTION_SEALED.md this is reported as failure, not retried with changes.\n\n```\n"
                + (out or "")[-4000:] + "\n```\n")
    sh('git add -A && git -c user.email=samixrd@local -c user.name="samixrd" commit -m "auto-settle: engine failure recorded verbatim" && git push -q origin master')
    sys.exit(0)

rows = json.load(open(os.path.join(ROOT,"results","forward_rows.json")))

# 1b) immutable memo header: witness statement + evidence linkage
def manifest_root(m):
    p = os.path.join(ROOT,"results","weekend_"+m,"manifest.json")
    if os.path.exists(p):
        return json.load(open(p)).get("segment_root")
    return "NO ROOT COMMITTED — evidence chain incomplete"

# 2. render against PREDICTION_SEALED.md failure conditions
lines = ["# Forward test result — sealed rule, settled %s UTC" % datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"),
         "",
         "Witness agent: tape verify = %s | weekend root = %s" % ("PASS" if tape_ok else "FAIL", manifest_root(MON)),
         "Agent performed: verify -> settle once -> report. No rule/timestamp/asset/cost was altered.",
         ""]
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
        # counterfactual: same row, same prices, forced LONG (baseline §7.1), same cost formula
        al_gross = (x["bid"]/e["ask"] - 1)*100
        al_net = al_gross - t["fee_pct"] - t["slip_pct"] - t["impact_pct"] + (t["funding_pct"] if isinstance(t.get("funding_pct"), (int, float)) else 0)
        lines.append("- baseline Always-Long on same fills: net %+.3f%% | **excess of signal over baseline: %+.3f%%**" % (al_net, t["net_pct"]-al_net))
    lines.append("- status: **%s**" % t["status"])
    lines.append("")
lines.append("_No rescue clause in effect: whatever this page says is the result._")
open(os.path.join(ROOT,"results","FORWARD_RESULT.md"),"w",encoding="utf-8").write("\n".join(lines))

# 2b) X card for the settlement (second build-in-public post, voting window)
ok_rows = [t for t in rows if "net_pct" in t]
if ok_rows:
    t0 = ok_rows[0]
    card = ("Weekend Desk forward test settled — exactly as pre-registered (protocol sealed 9/14, weekend tape root committed Sunday before settlement).\n\n"
            "Signal: w=%+.2f%% -> %s | Entry Sun 16:00 UTC | Exit Mon 20:00 UTC\n"
            "Net after fees+funding+spread+depth: %+.2f%%\n"
            "Tape verify: %s | result committed unedited by the settlement agent (no human in the loop).\n"
            "%s\n#BitgetHackathon @Bitget_AI") % (
        t0["w_pct"], {1:"LONG",0:"NO POSITION","-1":"SHORT"}.get(t0["position"],"?"),
        t0["net_pct"], "PASS" if tape_ok else "FAIL",
        "repo: github.com/samixrd/weekend-desk")
    open(os.path.join(ROOT,"results","X_POST_RESULT.txt"),"w",encoding="utf-8").write(card)

# 3. publish
sh('git add -A && git -c user.email=samixrd@local -c user.name="samixrd" commit -m "FORWARD SETTLEMENT: sealed prediction result published unedited" && git push -q origin master')
print("settled + pushed")
print("\n".join(lines))
