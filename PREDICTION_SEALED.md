# PRE-REGISTERED FORWARD PREDICTION — sealed 2026-09-14 (hash below)

Strategy: Weekend Desk v1.1 (SPY perp only), per PROTOCOL.md §6.

Prediction is a RULE, not a direction:
- Observe w = mid(Sun 2026-09-20 16:00 UTC) / mid(Fri 2026-09-18 21:00 UTC) − 1
- Take sign(w) position at §4 executable prices
- Exit Mon 2026-09-21 20:00 UTC at §4 executable prices
- Report net PnL after fee+funding+slippage+impact exactly per §4.

I predict the rule fires and the walk-forward machinery records it; I do NOT
predict its sign (predicting sign after seeing 12 IS continuations would be
the exact selection bias we froze out). The forward weekend's ONLY job is to
test whether the frozen executable machinery survives real Sunday spreads.

Failure conditions I am declaring in advance (any = honest negative report):
1. Sun-16:00 spread > 30 bps → strategy dead at retail size; report it.
2. Top-of-book depth cannot absorb 1000 USDT notional without >10bps impact
   → report as untradeable.
3. Net PnL negative → report as negative. No rescue re-runs.

sha256(this file) appended to PROTOCOL_HASH.txt at freeze time.
