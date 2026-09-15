"""
TAMPER-EVIDENT TAPE — Module 1 of Weekend Desk verification machine.

Does NOT touch the frozen collector: reads collected/*.jsonl, derives a
deterministic hash-chain + per-weekend Merkle root (computed fresh each
run; the chain is a pure function of source bytes, so any edit to any
past record changes every downstream hash and the published root).

Frozen segmentation:
  weekend segment  = records with ts in (Fri 00:00 UTC .. root_cutoff]
  ROOT_CUTOFF      = Sunday 17:00 UTC, covering the Sun-16:00 entry anchor
                     plus its +-10min match tolerance. Monday records are
                     always EXCLUDED from the pre-settlement root.
No retroactive rebuilding: roots are emitted by schedule and locked in
manifests; a later `build` may recompute for verification, but the
COMMITTED root in the manifest is the claim.

Wording (per protocol review): the root is a cryptographic commitment
publicly timestamped before settlement; later alteration produces a root
mismatch. It is NOT marketed as "mathematical proof of existence".

CLI:
  python tape.py build                     # chain integrity + counts
  python tape.py root --monday 2026-09-21  # emit manifest + tweet card
  python tape.py verify [--monday ...]     # PASS/FAIL table
"""
import json, hashlib, os, sys, glob, datetime, argparse, subprocess

ROOT = r"D:\wk-probes"
RESULTS = os.path.join(ROOT, "results"); os.makedirs(RESULTS, exist_ok=True)
CUTOFF_HOUR_UTC = 17            # Sun 17:00 UTC — FROZEN, see TAPE.md

def load_records():
    recs = []
    for f in sorted(glob.glob(os.path.join(ROOT, "collected", "*.jsonl"))):
        with open(f, encoding="utf-8") as fh:
            for ln, line in enumerate(fh):
                line = line.strip()
                if not line: continue
                r = json.loads(line)
                r["_file"] = os.path.basename(f); r["_line"] = ln
                recs.append(r)
    recs.sort(key=lambda r: (r["utc"], r["_file"], r["_line"]))
    return recs

def sha(b): return hashlib.sha256(b).hexdigest()
def canon(r):
    d = {k: r[k] for k in sorted(r) if not k.startswith("_")}
    return json.dumps(d, sort_keys=True, separators=(",", ":"))

def build_chain(recs):
    prev = "GENESIS"
    for r in recs:
        h = sha((prev + canon(r)).encode())
        r["_rec_hash"] = sha(canon(r).encode())
        r["_chain"] = h; prev = h
    return recs, prev

def merkle_root(leaves):
    if not leaves: return "EMPTY"
    level = list(leaves)
    while len(level) > 1:
        if len(level) % 2: level.append(level[-1])
        level = [sha((level[i] + level[i+1]).encode()) for i in range(0, len(level), 2)]
    return level[0]

def monday_of(r):
    dt = datetime.datetime.fromisoformat(r["utc"])
    d = dt.date(); wd = d.weekday()
    if wd <= 0: return d + datetime.timedelta(days=(0-wd) % 7 or (0 if wd==0 else 7))
    return d + datetime.timedelta(days=7 - wd)   # Fri/Sat/Sun -> following Monday

def seg_root(recs, monday):
    """records for weekend feeding `monday`, up to cutoff; returns (root, count, chain_tip)"""
    m = datetime.date.fromisoformat(monday)
    fri0 = datetime.datetime(m.year,m.month,m.day,tzinfo=datetime.timezone.utc) - datetime.timedelta(days=3)
    cut = datetime.datetime(m.year,m.month,m.day,tzinfo=datetime.timezone.utc) - datetime.timedelta(hours=24-CUTOFF_HOUR_UTC)  # Sun 17:00 UTC
    seg = [r for r in recs if fri0 <= datetime.datetime.fromisoformat(r["utc"]) <= cut]
    leaves = [r["_rec_hash"] for r in seg]
    # chain restricted segment continuity: recompute chain over seg only, from GENESIS
    prev = "GENESIS"
    for r in seg:
        prev = sha((prev + canon(r)).encode())
    return merkle_root(leaves), len(seg), prev

def hashes_files():
    out = {}
    p = os.path.join(ROOT, "PROTOCOL_HASH.txt")
    if os.path.exists(p):
        for line in open(p):
            parts = line.split()
            if len(parts) >= 2: out[parts[1].lstrip("*")] = parts[0]
    return out

def git_head():
    try:
        return subprocess.run(["git","-C",ROOT,"rev-parse","HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception: return "?"

def cmd_root(monday):
    recs, _ = build_chain(load_records())
    root, cnt, tip = seg_root(recs, monday)
    h = hashes_files()
    man = {"protocol_hash": h.get("PROTOCOL.md"), "prediction_hash": h.get("PREDICTION_SEALED.md"),
           "collector_hash": h.get("weekend_collector.py"), "engine_hash": h.get("engine.py"),
           "collector_commit": git_head(),
           "root_cutoff_utc": (datetime.date.fromisoformat(monday)-datetime.timedelta(days=1)).isoformat()+"T17:00:00+00:00",
           "segment_root": root, "chain_tip": tip, "record_count": cnt,
           "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    d = os.path.join(RESULTS, "weekend_" + monday); os.makedirs(d, exist_ok=True)
    mpath = os.path.join(d, "manifest.json")
    if os.path.exists(mpath):
        old = json.load(open(mpath))
        if old.get("segment_root") != root:
            print("!! ROOT MISMATCH vs committed manifest — do not overwrite; investigate")
            return 1
        print("root already committed, unchanged:", root)
        return 0
    json.dump(man, open(mpath, "w"), indent=1)
    card = ("Weekend Desk tape commit — weekend feeding %s\n"
            "Merkle root (all %d microstructure records up to Sun 17:00 UTC, "
            "before any settlement):\n%s\n"
            "Protocol+prediction sealed beforehand (hashes in repo).\n"
            "Result publishes automatically Mon 21:30 UTC. Win or lose, unedited.\n"
            "#BitgetHackathon @Bitget_AI") % (monday, cnt, root)
    open(os.path.join(d, "X_POST_ROOT.txt"), "w", encoding="utf-8").write(card)
    print("manifest:", mpath); print("root:", root, "records:", cnt)
    print(card)
    return 0

def cmd_verify(monday=None):
    recs, tip = build_chain(load_records())
    ok_files = True
    h = hashes_files()
    p = os.path.join(ROOT, "PROTOCOL_HASH.txt")
    for f, want in h.items():
        fp = os.path.join(ROOT, f)
        got = sha(open(fp, "rb").read()) if os.path.exists(fp) else "MISSING"
        if got != want: ok_files = False; print("FILE MISMATCH", f)
    mondays = [monday] if monday else sorted({str(monday_of(r)) for r in recs})
    any_root = True
    for m in mondays:
        mpath = os.path.join(RESULTS, "weekend_" + m, "manifest.json")
        if not os.path.exists(mpath): continue
        man = json.load(open(mpath))
        root, cnt, _ = seg_root(recs, m)
        passed = (root == man["segment_root"]) and (cnt == man["record_count"])
        any_root &= passed
        print("MERKLE %s  %s  root=%s  records=%d%s" % ("PASS" if passed else "FAIL", m, root[:16], cnt, "" if passed else "  <-- TAPED DATA ALTERED"))
    print("PROTOCOL/PREDICTION FILES   %s" % ("PASS" if ok_files else "FAIL"))
    print("FULL-TAPE CHAIN TIP         %s" % tip[:32])
    print("RECORD COUNT                %d" % len(recs))
    print("VERDICT                     %s" % ("PASS" if (ok_files and any_root) else "FAIL"))
    return 0 if (ok_files and any_root) else 1

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["build","root","verify"])
    ap.add_argument("--monday")
    a = ap.parse_args()
    if a.mode == "build":
        recs, tip = build_chain(load_records())
        from collections import Counter
        per = Counter(str(monday_of(r)) for r in recs)
        print("records:", len(recs), "chain tip:", tip[:24], "per-segment:", dict(per))
    elif a.mode == "root":
        sys.exit(cmd_root(a.monday or "2026-09-21"))
    else:
        sys.exit(cmd_verify(a.monday))
