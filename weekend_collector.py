"""
WEEKEND DESK COLLECTOR — Bitget 24/7 stock perps
Frozen protocol: timestamps, symbols, fields are NOT to be changed after first run.
Runs every weekend. Writes append-only JSONL to D:\wk-probes\collected\

Schedule (Windows Task Scheduler or manual before Friday):
  python weekend_collector.py            # daemon: sleeps until Fri 00:00 UTC, samples all weekend
  python weekend_collector.py --now      # immediate single sample pass (for testing)
"""
import json, urllib.request, datetime, time, os, sys, socket

# ============ FROZEN PARAMETERS — DO NOT EDIT ============
SYMBOLS = [
    # primary basket (predefined before any further OS inspection)
    "AAPLUSDT","TSLAUSDT","NVDAUSDT","MSFTUSDT","GOOGLUSDT","AMZNUSDT","METAUSDT",
    # index perps
    "SPYUSDT","QQQUSDT",
    # controls
    "BTCUSDT","ETHUSDT",
]
# sample times: hourly 7x24 during the weekend window, PLUS mandatory anchors:
#   Fri 21:00 UTC (post US close), Sun 16:00 UTC (signal print), Mon 13:30 UTC (underlying open+), Mon 20:00 UTC (US close)
FREQ_SEC = 3600
MANDATORY = [("FRI",21),("SAT",0),("SAT",16),("SUN",0),("SUN",16),("MON",13),("MON",14),("MON",15),("MON",20)]
# window: Fri 00:00 UTC -> Mon 21:00 UTC
WINDOW_START = ("FRI", 0)
WINDOW_END = ("MON", 21)
# =========================================================

OUTDIR = r"D:\wk-probes\collected"
os.makedirs(OUTDIR, exist_ok=True)
API = "https://api.bitget.com/api/v2/mix/market/tickers?productType=usdt-futures"
FIELDS = ["lastPr","askPr","bidPr","bidSz","askSz","baseVolume","quoteVolume",
          "usdtVolume","ts","change24h","fundingRate","holdingAmount","indexPrice","markPrice","openUtc"]

def log(*a):
    print(datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S"), *a, flush=True)

def sample_once():
    try:
        req = urllib.request.Request(API, headers={"User-Agent":"Mozilla/5.0"})
        d = json.load(urllib.request.urlopen(req, timeout=20))
    except Exception as e:
        log("FETCH FAIL", e); return 0
    now = datetime.datetime.now(datetime.timezone.utc)
    # per-symbol file, one JSONL line per symbol
    fname = os.path.join(OUTDIR, now.strftime("%Y-%m-%d") + ".jsonl")
    n = 0
    bymap = {t["symbol"]: t for t in (d.get("data") or [])}
    with open(fname, "a", encoding="utf-8") as f:
        for sym in SYMBOLS:
            t = bymap.get(sym)
            if not t: continue
            rec = {
                "utc": now.isoformat(timespec="seconds"),
                "dow": now.weekday(), "hour": now.hour,
                "sym": sym,
                "bid": float(t["bidPr"]) if t.get("bidPr") else None,
                "ask": float(t["askPr"]) if t.get("askPr") else None,
                "bid_sz": float(t["bidSz"]) if t.get("bidSz") else None,
                "ask_sz": float(t["askSz"]) if t.get("askSz") else None,
                "last": float(t["lastPr"]) if t.get("lastPr") else None,
                "mid": None,
                "spread_bps": None,
                "base_vol": float(t["baseVolume"]) if t.get("baseVolume") else None,
                "oi": float(t["holdingAmount"]) if t.get("holdingAmount") else None,
                "funding": float(t["fundingRate"]) if t.get("fundingRate") else None,
                "index": float(t["indexPrice"]) if t.get("indexPrice") else None,
                "mark": float(t["markPrice"]) if t.get("markPrice") else None,
                "ts_exchange": int(t["ts"]) if t.get("ts") else None,
            }
            if rec["bid"] and rec["ask"]:
                rec["mid"] = (rec["bid"]+rec["ask"])/2
                rec["spread_bps"] = (rec["ask"]-rec["bid"])/rec["mid"]*1e4
            f.write(json.dumps(rec)+"\n"); n += 1
    return n

def in_window(dt):
    wd = dt.weekday()  # 4=Fri 5=Sat 6=Sun 0=Mon
    h = dt.hour
    if wd == 4: return h >= WINDOW_START[1]
    if wd in (5, 6): return True
    if wd == 0: return h <= WINDOW_END[1]
    return False

def next_slot(dt):
    # next full hour
    return (dt + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

def run_daemon():
    log("collector daemon up; window Fri%02d -> Mon%02d UTC" % (WINDOW_START[1], WINDOW_END[1]))
    while True:
        now = datetime.datetime.now(datetime.timezone.utc)
        if in_window(now):
            n = sample_once()
            log("sampled", n, "symbols")
        nxt = next_slot(now)
        sleep = (nxt - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        # idle heartbeat every 10 min
        end = time.time() + sleep
        while time.time() < end:
            time.sleep(min(600, end - time.time()))
            if in_window(datetime.datetime.now(datetime.timezone.utc)) and time.time() >= end:
                break
        # retry fetch robustness: loop continues
        if not in_window(datetime.datetime.now(datetime.timezone.utc)):
            log("outside window, waiting for next weekend...")

def watchdog_check():
    """alert if no samples for >2h during a weekend window (run from cron/monitor)"""
    now = datetime.datetime.now(datetime.timezone.utc)
    if not in_window(now): return
    latest = 0
    for f in os.listdir(OUTDIR):
        p = os.path.join(OUTDIR, f)
        latest = max(latest, os.path.getmtime(p)) if os.path.exists(p) else latest
    if latest and time.time() - latest > 7200:
        log("!! WATCHDOG: stale collection, restart collector")

if __name__ == "__main__":
    if "--now" in sys.argv:
        n = sample_once(); log("one-shot:", n, "records")
    else:
        run_daemon()
