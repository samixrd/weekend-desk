# Walk-forward folds (MID-PRICE DAILY PROXY — DESCRIPTIVE ONLY per §6c)

Folds fit earliest 8..k weekends, test weekend k+1; OOS calendar span: 2026-08-15 -> 2026-09-05 (21 days).

| OOS weekend | fit_rule | OOS ret % | frozen sign(w) % | always-long % |
|---|---|---|---|---|
| 2026-08-15 | continuation | +0.94 | +0.94 | -0.94 |
| 2026-08-22 | continuation | -0.15 | -0.15 | +0.15 |
| 2026-08-29 | continuation | +0.14 | +0.14 | -0.14 |
| 2026-09-05 | continuation | +0.08 | +0.08 | -0.08 |

**Aggregate OOS (walk-forward fitted rules): avg +0.25%/wk, ann IR 3.79, n=4 weekends**
**Frozen sign(w) rule on same OOS rows:       avg +0.25%/wk, ann IR 3.79**
**Always-long baseline same rows:            avg -0.25%/wk**

Honesty clause: 22 calendar days / ~4 independent weekend events; weekend-event inference remains sample-limited.
Forward executable folds (Layer C/D) replace this proxy as weekends land; first sealed forward event: 2026-09-21.