# WEEKEND DESK — Frozen Research Protocol v1.1
**v1.0 frozen 2026-09-14 18:00 UTC · v1.1 amendments applied 2026-09-14 before first
forward weekend — these edits are pre-declaration (no new outcomes observed since
hashing), so folds remain clean. Change log at bottom.**
Track: Bitget AI Hackathon S2 — Alpha Factory → After-Hours Information Pricing

**Timezone note (reproducibility):** all protocol timestamps are **UTC**.
Local machine time is America/Sao_Paulo (UTC−3) in this environment; the
Windows task trigger "Thu 21:45 local" exists only to wake the daemon
early — the daemon itself sleeps until the **Fri 00:00 UTC** window and
every stored record carries UTC ISO timestamps. No protocol claim depends
on local time. (Correction: an earlier message wrongly stated
"Thu 21:45 BDT = Fri 00:00 UTC"; BDT is UTC+6. The equivalence is
Thu 00:00 UTC = Thu 06:00 BDT; irrelevant to the protocol, fixed for the
record.)

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
| B. Underlying daily prints | Yahoo chart API **raw `quote` Open/Close only — never `adjclose`/adjusted series**. Corporate actions, if any, are recorded as flags beside the row, never handled by manual removal after seeing results. | collected |
| C. Live hourly weekend snapshots: bid, ask, size, mid, spread_bps, OI, funding, index, mark, volume | `weekend_collector.py` → `D:\wk-probes\collected\*.jsonl` | **FROZEN schedule, runs Thu 21:45 local (= Fri 00:00 UTC window start), samples all weekend** |
| D. Funding settlements | Bitget `history-fund-rate` endpoint (verified available for SPYUSDT: rows at 00/08/16 UTC) | fetched per-trade by engine |

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
- **Funding:** engine uses **actual settlement records** from
  `GET /api/v2/mix/market/history-fund-rate` (rows with `fundingTime`),
  accruing `−sign(position) × Σ rate × notional` over settlements with
  `fundingTime ∈ (entry, exit]` (8h cycle: 00/08/16 UTC). The ticker
  `fundingRate` snapshot is a diagnostic, NOT the accounting source.
  If settlement rows are missing/unreconstructable for an interval, the
  observation is reported as "funding not reconstructable" and funding is
  excluded from that row's net PnL with a visible flag — never invented
  from the snapshot.
- **Strategy notional (FROZEN):** 1,000 USDT per position. All depth and
  impact tests are evaluated against exactly this size. Book capital is
  defined relative to it (§4 sizing = 1× notional = 1,000 USDT, no
  leverage beyond 1×, no pyramiding).
- **Slippage:** 50% of spread at entry + 50% at exit (top-of-book snapshot).
- **Symmetric liquidity gates (entry AND exit):** the spread/depth checks
  apply at BOTH anchors — Sun 16:00 entry and Mon 20:00 exit. Each trade
  row reports `entry execution quality` and `exit execution quality`
  separately (spread_bps, depth, gate pass/fail). An exit-side gate failure
  is a **FAILURE: exit not executable** observation — kept in all
  denominators with the entry fill counted (you cannot unwind a real
  position for free in a simulation that pretends the exit was clean; for
  reporting, the position is marked at the Mon 20:00 mid with the failure
  flagged). Never discarded.
- **Impact haircut:** +10 bps per side if displayed top-of-book depth on the
  traded side < 2× strategy notional (i.e. < 2,000 USDT) at that anchor.
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
DECISION: w > 0 -> LONG; w < 0 -> SHORT; w == 0 (exact, within stored
          precision) -> NO POSITION. The no-position case is recorded and
          stays in the denominator of every statistic. It is a specified
          outcome, not an omission.
ENTRY:    §4 executable prices at Sun 16:00 collector sample.
EXIT:     §4 executable prices at Mon 20:00 UTC collector sample
          (fallback Mon 20:00 daily-bar close print).
SIZE:     1,000 USDT notional, 1x, no leverage, no pyramiding.
CLAIM SCOPE: the tested hypothesis is DIRECTIONAL information — the sign
          of weekend repricing. Magnitude prediction is NOT claimed and
          is not what sign(w) tests.
NO threshold X. No spread filter Y. No persistence filter. No regime switch.
```

**Why no thresholds (Attack 1 answer):** with n=12 weekends, ANY tuned
threshold is in-sample fabrication; the 12/12 trade rule has zero free
parameters, so there is no selection bias to disclose — the rule was
specified as *maximal simplicity* before forward testing. Descriptive
IS statistics (+0.30%/wk, IR 0.41, t=1.43, long leg +0.41% n=5, short leg
+0.22% n=7) are labeled **IN-SAMPLE DESCRIPTIVE — not a performance claim.**

**Selection-bias admission (mandatory sentence):**
> "The frozen `sign(w)` direction was selected during exploratory discovery;
> therefore all pre-freeze performance is descriptive and not claimed as
> unbiased alpha. The strategy's first confirmatory evidence is the locked
> forward/walk-forward evaluation, with no parameter, asset, timestamp, or
> execution-rule changes permitted after sealing."

**Baseline decomposition (SPY perp Monday session, n=12, descriptive only):**
```
E[Mon]       = +0.04%/wk   (always-long baseline)
E[Mon | w>0] = +0.41% (n=5)   E[Mon | w<0] = −0.22% (n=7)
Long-leg excess over baseline = +0.37% | Short-leg excess = +0.18%
Strategy minus always-long    = +0.26%/wk, IR 0.35, t = +1.22
```
The short leg profits because post-down-weekend Mondays are *negative*,
not because baseline drift carries it; but t=1.22 confirms the IS evidence
is weak and the forward test is the real judge.
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

## 6c. Round-4 clarifications (constraints, not rule changes)

- **Untradeable ≠ no trade.** If the sealed failure gates trip (spread,
  depth), the observation is recorded as **FAILURE: not executable** and
  counted in the denominator of every hit-rate/PnL statistic. It is never
  silently dropped — dropping is a post-hoc filter.
- **30 bps / $1,000 notional are CAPACITY/OPERATIONAL constraints, not
  alpha parameters.** They alter no directional prediction; they only
  determine whether the predicted trade could physically be executed at
  retail size. Chosen from exchange-tier conventions, not from searching
  weekend outcomes.
- **Two distinct metrics, never conflated:**
  - *Research target:* native-equity Monday opening gap (Yahoo print) →
    establishes predictive content only.
  - *Trading outcome:* Sun 16:00 executable perp entry → Mon 20:00
    executable perp exit, net of §4 → establishes tradeability only.
  A positive research result with a negative trading outcome is a valid,
  reportable conclusion ("predictive but not capturable").
- **Deterministic timestamp matching (reproducibility):** anchor = the
  collector sample with smallest |ts − target_utc| and tolerance ≤ 10 min;
  ties → earlier sample; if none within tolerance, fallback is the daily
  bar print in fixed precedence (Sat-open bar for Fri anchor; Mon-bar-open
  for Sun-16 anchor; Mon-bar values for Mon exit). No manual candle
  selection, ever. Raw collector files + this rule must let any judge
  reconstruct every anchor.
- **OI / funding / spread / index / mark are diagnostics and execution
  controls ONLY.** They are not alpha inputs. Any future filter built on
  them requires a NEW declared research fold with fresh forward data —
  not the current sealed one.
- **No-rescue clause (pre-committed):** if Sep 21 net PnL is negative or
  baseline-adjusted forward return < 0, the submission reports **"forward
  validation failed"** with the full machinery. No timestamp swaps, no
  asset swaps (SPY→QQQ), no OI filters, no weekend deletions. A failed
  falsification test executed cleanly is still a stronger entry than a
  rescued number.

## 6d. Competitive positioning (moat statement)

"We trade SPY on weekends" is the obvious reading of the named sub-theme and
is copyable in an afternoon. Our claimed contribution is the **falsification
apparatus**: executable bid/ask accounting, funding sign conventions,
baseline decomposition, placebo windows, crypto-beta purge, sealed
pre-registration, and a live forward test — i.e., *whether the obvious
strategy survives contact with real weekend microstructure*. The strategy
is a test vehicle for the methodology.

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

**Hero section (submission front page) = FORWARD/WALK-FORWARD ONLY:**
```
Forward OOS net return | Sharpe | Sortino | MDD | Turnover |
Baseline excess | n weekend events
— each printed with "35 calendar days / ~4 independent weekend events"
```
Historical exploratory figures (t=1.43, IR 0.35 etc.) live in a clearly
labeled **"Pre-registration context / exploratory"** section — never the
hero, because they are easy to misread as alpha evidence.

Judging-sheet fields: Sharpe, Sortino, max drawdown, turnover,
OOS-vs-IS Sharpe decay ratio, rolling 30-day Sharpe, OOS weekend count n
stated everywhere. Label every figure **OBSERVED** (computed from data
here) / **ESTIMATED** (cost models) / **TARGETED** (projection). No
unlabeled numbers.

## 10. Change log discipline

This file is hashed on write; any edit after 2026-09-14 18:00 UTC gets a
dated changelog entry explaining what changed and why, with the affected
validation fold clearly flagged as no longer clean.

### Change log
- **2026-09-14 (pre-freeze):** v1.0 → v1.1 — SPY-primary, sign-only rule,
  walk-forward design. No outcomes observed after edits; folds clean.
- **2026-09-15 (Round 4):** §6 selection-bias admission + baseline
  decomposition; §6c constraints; §6d moat. Documentation only, strategy
  untouched.
- **2026-09-15 (Round 5):** timezone wording fix; funding accounting →
  actual settlement records (endpoint verified live); notional frozen at
  1,000 USDT; symmetric entry/exit liquidity gates; w==0 case specified;
  raw-price lock; directional claim scope; exploratory stats moved out of
  hero section. **All edits precede the first forward weekend (Sep 18-20)
  and touch no prediction rule, timestamp, or direction — folds remain
  clean.** After the Fri 00:00 UTC window start (Sep 18), this file is
  immutable.
