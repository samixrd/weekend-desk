# WEEKEND DESK — Submission Copy (Google Form: Project Description)
Track: Alpha Factory · Sub-theme: After-Hours Information Pricing
Status: FINAL PENDING NUMBERS — {{placeholders}} filled only from engine output after Sep 21 settlement. No invented metrics anywhere.

---

## Part 1 · Thesis

**Headline claim (locked wording):** Weekend stock-perp returns contain predictive directional information about the next native-equity open. We do not claim to have proven price discovery; we test predictive content and report falsification.

US equities close on Friday at 20:00 ET — but Bitget's 24/7 SPY perpetual keeps trading through the weekend. When macro and geopolitical events land during the closure window, the perp is the only venue where that information can be priced. Our core hypothesis: **the sign of the weekend repricing of the SPY perp (Fri 21:00 UTC → Sun 16:00 UTC) carries directional information about the Monday native-equity open gap.**

Signal sources: (1) Bitget 24/7 US-stock perpetual futures (SPYUSDT primary) — daily bars since product listing (2026-06-16, 90 bars / 12 weekends) plus a purpose-built hourly microstructure collector (bid/ask/depth/spread/OI/funding/index/mark); (2) native-equity daily prints (raw Yahoo quote Open/Close) as the independent ground-truth target; (3) BTC/ETH perps as crypto-beta controls.

Decision logic: fully deterministic, zero free parameters — `position = sign(weekend return)`, entered at the Sunday 16:00 UTC executable quote (ask if long, bid if short), exited Monday 20:00 UTC (bid/ask symmetric), 1,000 USDT fixed notional.

Risk controls: spread and depth gates applied at BOTH entry and exit anchors; funding accrued from actual settlement records; failure to execute is recorded as a failed observation and kept in every denominator — never quietly skipped. The research protocol was frozen and hash-sealed on 2026-09-14/15, before the first forward weekend was observed, with a pre-registered prediction file (PREDICTION_SEALED.md, sha256-committed).

Why existing solutions fall short: "trade the weekend gap" is the obvious reading of this sub-theme, but every version of it dies on one question — **can you actually get in and out at Sunday-morning liquidity?** Nobody answering it has the data, because Bitget's stock perps are ~3 months old and no one records their weekend microstructure. We built the recorder, froze the rules before the tape ran, and let the data judge.

## Part 2 · Target user and product value

**Segment:** discretionary and systematic retail prosumers (capital ≈ $1k–$50k, weekly to daily horizon) in Bitget's non-US markets — LatAm/SEA/MENA crypto-native traders who already hold stablecoin collateral on Bitget futures and want S&P 500 directional exposure outside US market hours without touching brokerage rails. (Persona basis: OBSERVED — weekend sessions show 15.1% of total SPY perp 24/7 volume; Sunday candles move up to ±1.5%.)

Their problem: information arrives Saturday; their only expression venue has unknown, potentially brutal transaction costs; and every "weekend alpha" YouTube/Telegram idea silently assumes mid prices. This product gives them a signal whose **whole net-cost ledger is itemized** — fee, funding, spread, impact — plus explicit failure reporting ("this weekend was not tradeable"), which is more honest than any strategy shop's smoothed equity curve.

Value delivered: (a) a reproducible after-hours directional tool with a 10-line rule anyone can audit; (b) the first public weekend-microstructure dataset for 24/7 equity perps; (c) a validation apparatus (walk-forward + sealed forward test + baselines + placebo) they can reuse before trusting any weekend strategy — including competitors'.

## Part 3 · Validation data and key metrics

> ⚠️ PLACEHOLDERS — fill from `results/forward_rows.json` + walk-forward runner output after Sep 21, 20:00 UTC settlement. Report OBSERVED/ESTIMATED/TARGETED labels. Never fill a placeholder with a projection dressed as a result.

**Primary (hero) — frozen forward test + walk-forward, executable accounting:**
- Forward weekend Sep 18–20: signal w = {{W_FWD}}% → position {{SIDE_FWD}} → entry ask/bid {{ENTRY_FWD}}, exit {{EXIT_FWD}} → **gross {{GROSS_FWD}}% → net {{NET_FWD}}%** after fee {{FEE_FWD}}% + funding {{FUND_FWD}}% + slippage {{SLIP_FWD}}% + impact {{IMP_FWD}}% {{ENTRY_GATE}}/{{EXIT_GATE}}.
- Walk-forward OOS (folds fit on strictly-earlier weekends): net {{OOS_NET}}%/weekend; Sharpe {{OOS_SHARPE}}; Sortino {{OOS_SORTINO}}; MDD {{OOS_MDD}}; turnover {{TURNOVER}}; baseline excess (vs Always-Long Monday) {{BASELINE_EXCESS}}.
- Sample statement beside every metric: **"{{OOS_CAL_DAYS}} calendar days / {{OOS_WEEKENDS}} independent weekend events"** — the ≥30-day OOS window satisfies the hackathon validation requirement; weekend-event inference remains sample-limited. We report confidence intervals and failure cases rather than point claims of long-run alpha.
- OOS-vs-IS Sharpe decay ratio: {{DECAY_RATIO}}. Rolling window stability reported with event counts, not smoothed.

**Pre-registration context / exploratory (NOT claimed as alpha):** over the 12 historical weekends, a mid-price daily-bar proxy showed +0.30%/wk continuation vs +0.04%/wk always-long (excess +0.26%/wk, IR 0.35, t=1.22) — in-sample descriptive only, direction chosen during discovery. Discovery evidence vs the native print: weekend SPY perp return correlates with the true Monday open gap at r=+0.55 (n=9, exploratory), while placebo mid-week windows flip sign (SPY r=−0.68) and crypto-beta correlation on mega-cap weekend moves is ≈0 (r=+0.05 basket vs BTC) — the weekend effect is window-specific and not crypto noise. These numbers motivated the freeze; the freeze's result is the claim.

**Effectiveness proof plan (post-hackathon):** dataset + engine are the product surface; distribution path is Bitget Playbook listing of the frozen rule with the collector running as a live execution-quality monitor, reporting each weekend's trade-or-failure publicly.

## Part 4 · Progress

**Built (all verified, repo linked in materials):**
1. Data discovery from public Bitget APIs: 90 bars × 17 stock/crypto perps; weekend volume share (15.1%); weekend-vs-weekday spread capture (live).
2. Exploratory battery: lead-lag (perp→perp and perp→native gap), crypto-beta purge, placebo windows, volatility normalization, baseline decomposition — scripts committed.
3. Hourly microstructure collector (frozen symbol set + frozen anchor stamps) running on a scheduled task since 2026-09-14; appends UTC ISO JSONL; one-shot self-verified (11 symbols, mid/spread computed at write).
4. Frozen protocol v1.1/v1.2: signal window Fri 21:00→Sun 16:00 UTC, sign-only rule, 1,000 USDT notional, symmetric liquidity gates, settlement-record funding accounting (Bitget `history-fund-rate` verified), raw-price-only target, deterministic ≤10-min anchor matching, ten immutables, no-rescue clause. sha256-locked before first forward weekend.
5. Sealed pre-registered prediction (PREDICTION_SEALED.md) with self-declared failure conditions.
6. Deterministic engine (`engine.py`): forward + historical modes, gross→net itemization; synthetic-weekend self-test passes all assertions (anchor matching, gate failure kept in denominator, fill direction on ask/bid).
7. Walk-forward runner folds defined; executed on whatever weekend blocks exist by 9/21.

**Not built / known limits (stated up front):** n=12 historical weekends (product age; irreducible); executable entry/exit evidence exists only for weekends after collector start (Sep 18–20 = first, and the only clean forward event pre-deadline); native-gap correlation rests on n=9; strategy capacity unproven above ~$1k notional.

**Stack:** Python 3.11 (stdlib only — no dependencies, fully reproducible), Bitget public REST (tickers/candles/history-fund-rate), Yahoo chart API, Windows Task Scheduler. LLM-assisted development (Part 6).

## Part 5 · Deliverables (Submission Materials Link contents)

- GitHub repo (public): `weekend_collector.py`, `engine.py`, `PROTOCOL.md` (+ `PROTOCOL_HASH.txt`), `PREDICTION_SEALED.md`, probe scripts (`weekend_probes.py`, `attack_round3.py`, `baseline_probe.py`, `spy_decomp.py`), raw JSONL weekend data, `results/` engine outputs.
- Validation report: walk-forward + forward tables with OBSERVED/ESTIMATED labels, failure rows included.
- Demo: 3–5 min video walking one weekend end-to-end — collector tape → Sun 16:00 signal print → sealed rule fires → executable fill → Mon 20:00 net PnL, **including the deliberate failure-case segment** (gate trip recorded, kept in denominator).
- Backtest record: ≥60-day total window (product history 2026-06-16→), walk-forward OOS ≥30 calendar days, event counts stated.

## Part 6 · Role of the LLM (honest)

The LLM was used as a development and research-assistance tool: code generation and review (collector, engine, probes), statistical methodology critique, adversarial review of the research protocol across five rounds (selection bias, baseline decomposition, funding accounting, timestamp reproducibility), and drafting. **The submitted trading decision path is deterministic and contains no LLM at execution time: `sign(weekend return)` evaluated from timestamped market data.** Qwen (via the hackathon endpoint) was used where applicable for development assistance; it does not generate the final trade direction. In the protocol-freeze process, LLM output was treated as a challenger of claims, never an authority for numbers — every figure in this submission is tool-computed and re-checkable from the committed scripts.

---
**Form fields outside the description:**
- Track/sub-theme: Alpha Factory → After-Hours Information Pricing
- X post: must include #BitgetHackathon + @Bitget_AI (draft = next artifact)
- University Name: {{fill full university name — unlocks the 10×500USDT pool; free prize tier, leave no blank}}
- Demo Day: Yes
- K3 subsidy: Yes
