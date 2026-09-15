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

Three-venue hourly bid/ask/depth/OI/funding collector (same tape format,
separate file, frozen cutoffs) — if built, it must never touch the WD
collector or root schedule. ~5 weekends of executable cross-venue tape =
the minimum honest basis for an executable-arbitrage entry later.
