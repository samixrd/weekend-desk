# RESEARCH RESERVE — Cross-Venue Price Leadership (NOT submitted S2)

Status: frozen research asset for S3 / post-hackathon. Evidence collected
2026-09-15/16 via public APIs only. Does not touch Weekend Desk's sealed
protocol; WD's `sign(w)` rule and collector are untouched and hash-locked.

## The observation (two-part, genuinely weird)

1. **Hourly lead-lag (2,847 bars, ~100 days, 1h closes):** Binance leads
   Bitget by ~1 hour on the same underlying — corr(ΔBN_t, ΔBG_{t+1h}) ≈
   **+0.54** vs ≈0.0 on the flipped side (both SPY/AAPL, all hours).
   Bybit shows the same pattern vs Bitget (+0.52).
2. **Oracle reversal in the closure window:** weekend move (Fri 21:00 →
   Sun 16:00 UTC) → native Monday open gap (Yahoo raw prints, n=9):
   - **Bitget: SPY r=+0.55 / AAPL r=+0.57** (positive, consistent)
   - Binance: SPY r=−0.47 / AAPL r=+0.22 (unstable)

   > Binance leads tick-for-tick; **Bitget leads to the native open.**
   During equity-market closure, the venue whose repricing maps onto the
   eventual native print is Bitget. Venue leadership is regime-dependent.

## Convergence measurement (T1, non-overlapping episodes)

D_t = ln(P_Bitget/P_Binance); z-score vs trailing 24h; trade reversion of
|z|>2 divergences; **cooldown = horizon (6h) so episodes never overlap**;
BG-vs-Bybit pairs replicate at ~75-80% of the size.

| sym | n episodes | avg gross reversion | t-stat | hit rate |
|---|---|---|---|---|
| TSLA | 118 | **+77.9 bps** | +8.7 | 92% |
| AAPL | 113 | +55.7 bps | +8.9 | 92% |
| SPY  | 110 | +20.9 bps | +7.5 | 92% |

**Label: MID-PRICE GROSS. Not alpha.** Cost floor for the 4-sided
market-neutral leg is 24 bps taker+taker both venues; spreads, adverse
selection, latency, and cross-venue funding are **historically
unobservable** (no venue stores tick-level bid/ask history). The +74 bps
TSLA row is *sizable relative to* those costs, not net of them.

## Why this is NOT an S2 entry

- Executable evidence currently exists for **zero** historical intervals.
- n_rows ≠ n_bets handled (cooldown), but 118 episodes across ~100 days
  still share one regime — no OOS split exists that wasn't seen.
- Submitting mid-price convergence as flagship would repeat exactly the
  error the WD protocol was built to prevent. **Submit the result you can
  defend, not the result you wish you had.**

## What we steal for WD (robustness, not alpha)

Three-venue control regression (gap ~ BG + BN + BY weekend moves) is
**unidentifiable at n=4–9** (coefficients numerically meaningless —
verified, discarded honestly). Usable version for the submission report:
venue-venue weekend-move correlations + per-venue r vs native gap
(the oracle table above), presented as *"the weekend signal is not merely
a venue-wide effect"* — descriptive, rule unchanged.

## Forward plan (S3 asset)

Three-venue hourly bid/ask/depth/OI/funding collector: **BUILT**
(`weekend_collector_v2.py`, scheduled `WeekendDeskV2`, separate tape
`collected_v2/`, own hash-chain — WD collector untouched and hash-locked).

### Frozen conventions (2026-09-16, per CTO review)
- **Universe = all 13 common stock-perp symbols**, pre-declared.
  TSLA/NVDA/AAPL = *exploratory strong-effect subset*; SPY = *exploratory
  negative control*. Selection is never collapsed into the claimed universe.
- **Sampling:** weekday hourly at HH:00:00 UTC (historically compatible
  with the 1h backtest); weekend window every 5 min — the hourly grid is
  always contained in the finer tape. Forward and backtest horizons are
  comparable by construction.
- **Formula (frozen for this experiment):**
  `F_t = ⅓ Σ_v log P_{v,t}` → `D_{v,t} = log P_v − F` →
  `D̃ = D − Σ carry(fund_A − fund_B)` using **actual settlement timestamps
  and signed cash-flow convention** (report prints gross / −fees /
  −BG funding / +BN funding / = net, line by line) →
  `z = D̃ / EWMA_σ(ΔD̃, λ=.97)` → **pre-specified research trigger |z| ≥ 2**
  (a trigger, not an "optimal threshold"), 6h hold, non-overlapping.
  Half-life is reported descriptively, never as a knob.

### Cluster-robust inference (round9) — the effect survives
Day-clustered episode means (removes volatility clustering, same-day
simultaneity, venue-level bursts):

| sym | episodes | naive t | day-clusters | **cluster t** |
|---|---|---|---|---|
| TSLA | 41 | +6.3 | 29 | **+7.0** |
| NVDA | 45 | +8.1 | 31 | **+9.5** |
| AAPL | 41 | +5.9 | 30 | **+7.6** |
| SPY  | 63 | +7.1 | 37 | **+8.1** |

(Cluster t exceeding naive t = episodes are NOT stacking on shared shock
days — the dependence the CTO worried about is measurably absent in this
sample. SPY's fee-adjusted weakness still stands: +7 bps gross < 24 bps
fees — negative control behaves as declared.)
