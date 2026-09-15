# WEEKEND DESK — Frozen Research Protocol v1.1
**v1.0 frozen 2026-09-14 18:00 UTC · v1.1 amendments applied 2026-09-14 before first
forward weekend — these edits are pre-declaration (no new outcomes observed since
hashing), so folds remain clean. Change log at bottom.**
Track: Bitget AI Hackathon S2 — Alpha Factory → After-Hours Information Pricing

---

## 0. Research question (final wording — tone-limited by design)

> When traditional equity markets are closed, do continuously traded stock
> perpetuals contain **predictive information** about the subsequent
> underlying-market open, after controlling for crypto-market moves,
> liquidity frictions, and unconditional day-of-week drift?

We do **NOT** claim to prove price discovery. We test whether predictive
content is *consistent with information flow* rather than liquidity noise
or common-factor effects. Possible outcomes H1 (continuation), H2 (null),
H3 (reversal) are all reportable results.

## 1. Data

| Layer | Source | Status |
|---|---|---|
| A. Historical daily perp bars | Bitget public API, 2026-06-16 → | collected (90 bars, 12 weekends) |
| B. Underlying daily prints (open/close) | Yahoo Finance chart API, aligned US sessions | collected |
| C. Live hourly weekend snapshots: bid, ask, size, mid, spread_bps, OI, funding, index, mark, volume | `weekend_collector.py` → `D:\wk-probes\collected\*.jsonl` | **FROZEN schedule, runs Thu 21:45 BDT weekly (Task Scheduler `WeekendDeskCollector`)** |

Collector frozen fields/timestamps must never be edited after a weekend has
been observed. No "discovering" a better sample time.

## 2. Instrument universe (fixed)

- **PRIMARY STRATEGY = SPY perp ONLY.** SPY is a real economic object with the
  best weekend evidence (discovery r=+0.55 vs true gap; continuation both
  legs positive). All headline metrics (Sharpe, Sortino, MDD, turnover,
  OOS decay) are computed on the SPY-only strategy.
- **Robustness arm (research, not the strategy):** predefined 7-stock
  basket — AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN, META (perps) equal weight,
  reported as cross-sectional aggregation evidence only.
- **Secondary / exploratory:** QQQ and any single-name cross-sectional
  finding (e.g. GOOGL r=+0.89) — labeled
  **"exploratory cross-sectional evidence"**, never the strategy.
- **Excluded:** COIN, MSTR, CRCL, HOOD (crypto-beta contaminated: r 0.44–0.75
  vs BTC weekend), TQQQ/SQQQ (path dependency).
- **Controls:** BTC, ETH perps; **Bitget indexPrice/markPrice = FEATURE/CONTROL
  ONLY** (see §2b).

## 2b. Target vs control separation (hard-coded; attacks source contamination)

- **Ground-truth target** for the discovery test = **native-equity print**
  (Yahoo chart API: SPY Mon open / Fri close). This remains the target
  even though Bitget provides `indexPrice`.
- **Rationale:** Bitget's perp index is constructed from underlying
  references that update around Monday open; using a post-open Bitget index
  value as target would make the measurement partially self-derived
  (perp-measures-perp). Native print keeps T1 independent of the exchange
  whose product we are studying.
- `indexPrice`/`markPrice` appear ONLY as features/controls (basis,
  premium/discount diagnostics). Any report table using them as a target
  must be flagged "perp-derived" and excluded from discovery claims.

## 3. Signal definition (frozen — SPY only)

- **Signal window:** **Fri 21:00 UTC → Sun 16:00 UTC** (immutable; Fri 21:00
  = 1h after US cash close, avoids close-auction prints; Sun 16:00 = 30min
  before US pre-market opens, frozen before any forward observation).
- **Anchor-in:** Layer C collector sample at/nearest Fri 21:00 UTC (fallback:
  Saturday-bar open from daily API).
- **Anchor-out / decision timestamp:** **Sun 16:00 UTC collector sample —
  frozen decision time; no re-selection, no "discovering" a better stamp.**
- **Weekend return (SPY):** w = P(Sun16) / P(Fri21) − 1, mid-price for signal
  math only; execution uses §4 prices.
- **Robustness basket w:** mean of the 7 stock-perp weekend returns (same
  anchors), diagnostic only.
- **Target 1 (discovery test):** underlying SPY Monday open gap
  g = Mon_open / Fri_close − 1 (Yahoo print).
- **Target 2 (tradable test):** SPY perp Monday session, §4 accounting.

## 4. Executable accounting (mandatory; mid-price results are diagnostics only)

- LONG entry = **ask** at Sun 16:00 collector sample; exit = **bid** at exit.
- SHORT entry = **bid** at Sun 16:00; exit = **ask** at exit.
- **Fee:** taker 0.06% per side (Bitget futures USDT-perp tier-0 rate; if
  actual account tier differs at submission, recompute with the real rate —
  the number, never the method, is fixed).
- **Funding (sign convention frozen):** funding paid LONG→SHORT when rate >0.
  Strategy accrues `−sign(position) × Σ fundingRate × notional` over all
  funding settlements whose timestamp falls in (entry, exit]. Rates from
  Layer C `funding` field. Weekend holds typically cross 8–16 settlements;
  no "computed later."
- **Slippage:** 50% of spread at entry + 50% at exit (top-of-book snapshot).
- **Impact haircut:** +10 bps per side if assumed position notional > 2×
  displayed top-of-book depth at Sun 16:00.
- **Position sizing (frozen):** 1× of allocated book capital per signal
  (no pyramiding, no vol-scaling — vol-scaling is a post-hoc knob).
- Every headline number ships as `gross → net` pair with each deduction
  itemized.

## 5. Validation design (walk-forward; replaces any "Sep 1 = OOS" claim)

Single split is invalid (post-hoc boundary + already inspected). Instead:

```
Weekend series (12 historical + forwards as they arrive)
  fold i: fit on weekends 1..k, test on weekends k+1..k+4 (4-week block)
  k starts at 8 -> blocks: [9-12] test on [1..8] fit
  roll forward: each new observed weekend extends the series;
  parameters always refit using ONLY strictly-earlier weekends.
```

- Cumulative out-of-sample window covered: **Aug 17 → Sep 20 = 35 calendar
  days ≥ 30-day requirement** (block boundaries at weekend events).
- Parameters (direction rule, threshold X, filters Y/Z, hold time): fit
  **inside the IS portion of each fold only**. Never chosen after seeing
  the fold's OOS outcomes.
- **True untouched forward test:** weekend of Sep 19–20 (Layer C data,
  protocol frozen before observation). Results reported separately as
  forward test.

### Honesty clause (printed **beside every headline metric**, not in an appendix)
> "OOS: +X%; Sharpe Y — evaluated over 35 calendar days / **~4 independent
> weekend events**. The 30-day OOS window satisfies the hackathon validation
> requirement; weekend-event inference remains sample-limited. We report
> confidence intervals and failure cases rather than point claims of
> long-run alpha."

## 6. Trading rule — FROZEN SPECIFICATION v1.1 (this is the whole strategy)

```
SIGNAL:   w = SPY perp mid(Sun 16:00 UTC) / mid(Fri 21:00 UTC) − 1
DECISION: if w > 0 -> LONG SPY perp; if w < 0 -> SHORT; if w == 0 -> no trade.
ENTRY:    §4 executable prices at Sun 16:00 collector sample.
EXIT:     §4 executable prices at Mon 20:00 UTC collector sample
          (fallback Mon 20:00 daily-bar close print).
SIZE:     1x book capital, no leverage beyond 1x, no pyramiding.
NO threshold X. No spread filter Y. No persistence filter. No regime switch.
```

**Why no thresholds (Attack 1 answer):** with n=12 weekends, ANY tuned
threshold is in-sample fabrication; the 12/12 trade rule has zero free
parameters, so there is no selection bias to disclose — the rule was
specified as *maximal simplicity* before forward testing. Descriptive
IS statistics (+0.30%/wk, IR 0.41, t=1.43, long leg +0.41% n=5, short leg
+0.22% n=7) are labeled **IN-SAMPLE DESCRIPTIVE — not a performance claim.**
The claim rests only on: (a) walk-forward blocks (§5) and (b) the frozen
forward weekend Sep 19–20 with pre-registered prediction.

**Pre-registered forward prediction (sealed before Mon Sep 21):** SPY signal
w on Sep 19–20 weekend → position sign(w) entered Sun 16:00 → PnL net of
§4 costs at Mon 20:00. Reported whatever it is.

The richer template (threshold X, spread cap Y, persistence, z-normalization,
baseline-adjusted direction) is **demoted to research-diagnostics section** —
per-fold IS-fitted variants may be reported as exploratory, never headline.

## 6b. Ten immutables (violation of any = protocol broken, say so publicly)

1. Signal window: Fri 21:00 → Sun 16:00 UTC — fixed
2. Decision timestamp: Sun 16:00 UTC — fixed
3. Entry: BUY=ask / SELL=bid at that sample — fixed
4. Exit: Mon 20:00 UTC — fixed
5. Sizing: 1x, no vol-scaling — fixed
6. Fees/funding: §4 method + sign convention — fixed
7. No threshold changes — rule has none
8. No asset deletion/addition (SPY-only primary)
9. No basket re-weighting (basket is diagnostic anyway)
10. **No looking at Sunday outcome then touching the Monday rule.**
   Collector samples are written append-only; strategy code reads them
   mechanically. Any rule edit after a weekend starts is a protocol break.

## 7. Baselines that must be beaten (report table)

1. **Always-Long Monday** (same instrument, same hold window).
2. **Unconditional Monday gap mean** per asset (drift benchmark).
3. Signal strategy minus baseline-1 = the only number we are allowed to
   call "alpha."
4. Placebo window (Tue 20:00 ET anchor, same 48h→session structure) —
   historical probe: SPY flips to r=−0.68 mid-week; any strategy must show
   the weekend window is materially different.

## 8. Mechanism diagnostics (research, not parameters)

BTC-purge residuals · vol-normalized shocks · spread/depth conditioning ·
basket-vs-single aggregation · placebo windows. Any "why" narrative in the
report must cite these tables.

## 9. Reporting metrics (Alpha Factory judging sheet)

Sharpe, Sortino, max drawdown, turnover, OOS-vs-IS Sharpe decay ratio,
rolling 30-day Sharpe, OOS weekend count n stated everywhere. Label every
figure **OBSERVED** (computed from data here) / **ESTIMATED** (cost models)
/ **TARGETED** (projection). No unlabeled numbers.

## 10. Change log discipline

This file is hashed on write; any edit after 2026-09-14 18:00 UTC gets a
dated changelog entry explaining what changed and why, with the affected
validation fold clearly flagged as no longer clean.
