# Weekend Desk

**Does the weekend repricing of a 24/7 US-stock perpetual carry predictive directional information about the next native-equity open?**

A frozen-rule quant strategy + falsification apparatus built for the
**Bitget AI Base Camp Hackathon S2** — Track: 🟦 Alpha Factory,
Sub-theme: **After-Hours Information Pricing**.

US equities close Friday 20:00 ET. [Bitget's SPY perpetual](https://www.bitget.com/futures/usdt/SPYUSDT)
keeps trading through the weekend. This project measures what that market
knows — and, more importantly, whether you can actually trade it after
real Sunday-morning spreads, funding settlements, and depth.

---

## Built on Bitget (data spine — every claim re-checkable)

| Bitget resource | Role here |
|---|---|
| **24/7 US-stock perps (SPYUSDT)** | The market under study — the whole thesis exists because this product exists |
| **Public Market Data API** — `tickers`, `history-candles` | Weekend volume/movement facts; 90 daily bars since listing (2026-06-16) |
| **`history-fund-rate` settlements** | Actual funding accounting for every trade, not snapshot approximations |
| **Ticker bid/ask/depth/OI/index/mark** | Frozen hourly microstructure collector (first public weekend tape for these products) |
| Bitget Playbook | Strategy cross-check path (Alpha Factory toolkit) |

No API key was needed for any of it — judges can rerun every number.

## The strategy (zero free parameters, frozen 2026-09-14/15, hash-locked)

```
SIGNAL   w = SPY perp mid(Sun 16:00 UTC) / mid(Fri 21:00 UTC) − 1
DECIDE   w > 0 → LONG 1,000 USDT | w < 0 → SHORT | w == 0 → recorded no-position
ENTER    ask (long) / bid (short) at the Sun 16:00 collector sample
EXIT     Mon 20:00 UTC, bid/ask symmetric
COSTS    fee 0.06%/side + actual settlement funding + spread slippage + depth impact
```

Discovery evidence vs the **native-equity Monday open** (ground-truth target):
r = +0.55 (n = 9 weekends). Crypto-beta purge: mega-cap weekend moves are
**uncorrelated with BTC** (r ≈ 0.05) — this is not crypto noise. Placebo
mid-week windows flip sign (SPY r = −0.68) — the weekend window is
specific. All labeled exploratory; the claim rests only on the sealed
forward test and walk-forward folds.

## Repository map

| File | What it is |
|---|---|
| `PROTOCOL.md` | The frozen research protocol v1.2 — rules, gates, immutables, no-rescue clause |
| `PROTOCOL_HASH.txt` | sha256 lock of protocol + collector + prediction + engine |
| `PREDICTION_SEALED.md` | Pre-registered forward prediction + declared failure conditions |
| `weekend_collector.py` | Hourly microstructure recorder (frozen schedule, UTC JSONL, append-only) |
| `engine.py` | Deterministic strategy executor: forward (executable) + historical (descriptive) modes |
| `walk_forward.py` | Walk-forward fold runner (§5 of protocol) |
| `weekend_probes.py`, `attack_round3.py`, `baseline_probe.py`, `spy_decomp.py` | The exploratory evidence battery |
| `collected/` | Raw weekend JSONL tape |
| `results/` | Engine outputs, walk-forward tables, validation report |
| `SUBMISSION.md` | The six-part hackathon project description |

## Reproduce

```bash
python weekend_collector.py --now      # one-shot live snapshot
python engine.py historical            # exploratory descriptive stats
python engine.py forward               # sealed-executable rows from collector tape
python walk_forward.py                 # fold table + report
```

## Claims discipline

Every number in this repo is labeled **OBSERVED** / **ESTIMATED** /
**TARGETED**. Failure observations (entry gate trips, exit illiquidity,
funding not reconstructable) stay in every denominator. If the forward
test fails, this README gets updated with the negative result — that is
pre-committed in `PREDICTION_SEALED.md`, not a slogan.

*Weekend Desk — humans sleep; the tape doesn't. We measured what it knows.*
