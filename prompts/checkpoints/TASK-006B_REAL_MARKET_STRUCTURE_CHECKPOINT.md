# TASK-006B — Real-Market Structure Checkpoint

Status: **APPROVED VALIDATION CHECKPOINT — NO PRODUCT IMPLEMENTATION**

Repository: `ahhhhzzz/ai-infra-quant`

Validation branch: `validation/006b-real-market-structure-checkpoint`

Authoritative implementation branch: `roadmap/no-live-trading`

Authoritative TASK-006B accepted SHA: `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`

This checkpoint exists because deterministic tests prove implementation consistency, not that Pivot / Zone / Range / Base Regime are semantically useful on real market data.

## 1. Objective

Stress-test the accepted TASK-006B Structure Engine on real read-only US/HK market data before any TASK-006C approval.

This is **not** a profitability, Alpha, signal, entry, or P&L backtest.

The checkpoint evaluates whether the structure layer behaves plausibly and robustly under real historical and current price paths:

```text
ATR
Micro/Major Pivot
Swing labels
Key Levels
Zones
Range
Base Regime
```

## 2. Hard scope boundary

Do not modify product behavior.

Forbidden in this checkpoint:

- any change under `src/`;
- any migration/database schema change;
- any PAQS production parameter change;
- any TASK-006C Event logic;
- Breakout / Breakdown / Failed Breakout / Retest / Role Flip / Transition / Trigger / Follow-through;
- Setup / Invalidation / Target / RR;
- Entry / Holder Advisory;
- Quality / Score / Ranking;
- paper portfolio or backtest P&L;
- broker/account/write behavior.

Allowed changes are validation-only and should be limited to paths such as:

```text
tools/validation/
docs/reviews/
```

Do not commit large raw market-data dumps. Commit compact reproducible summaries and only the minimum selected bar excerpts needed to audit examples.

`phase1_remediation_commit.txt`, if present locally, remains untracked, untouched, unstaged and uncommitted.

## 3. Data / replay truthfulness

Use the existing read-only provider path and accepted TASK-006A/TASK-006B code.

Current Futu adjusted history remains:

```text
PROVIDER_QFQ_CURRENT
historical_replay_safe = false
```

Therefore historical replay in this checkpoint means:

> Re-run the deterministic structure engine on prefixes of the historical bars currently supplied by the provider.

It does **not** prove strict point-in-time corporate-action-safe historical reconstruction.

Never describe this checkpoint as a strict historical trading backtest.

## 4. Securities

Attempt at minimum:

```text
US.AVGO
US.VRT
HK.09698
US.NVDA
HK.00700
```

The first three are historical project symbols. NVDA and HK.00700 provide additional US/HK real-market diversity and must use the normal TASK-006A supported-equity path if a temporary local Security is needed.

Prefer a temporary validation database or otherwise avoid mutating the user's normal local watchlist/database state.

If one symbol is unavailable/not entitled, report it truthfully and continue with the remaining symbols. Do not fabricate substitute data.

## 5. Current live structure smoke

When OpenD is available, collect a current structure snapshot for each available security.

Record, separately for W1 / D1 / M30:

- `as_of_timestamp` and `calculated_at`;
- input quality / warnings / adjustment basis;
- legitimate bar count;
- ATR readiness / latest ATR;
- Micro Pivot count;
- Major Pivot count;
- latest confirmed Major High and Major Low, including extreme and confirmation refs;
- latest comparable Major Swing labels;
- current confirmed support/resistance Zones with geometry and touch count;
- active Range if any;
- Base Regime and explanation.

No market state should be hard-coded into tests.

## 6. D1 historical prefix replay

For each available security, use a sufficiently long completed D1 history from the provider.

Target at least the most recent **500 completed D1 sessions** when available. If fewer are available, use all legitimate available sessions and report the count.

After ATR warm-up, replay the Structure Engine on sequential prefixes:

```text
bars[0:t]
```

for each completed D1 cutoff `t` in the selected replay window.

At every cutoff record compact state sufficient to analyze:

- latest ATR;
- Micro/Major Pivot counts;
- latest Major Pivot IDs/refs;
- latest Swing labels;
- confirmed Zone IDs / geometry;
- active Range ID / geometry;
- Base Regime.

Do not persist every raw bar set to GitHub. A compact CSV/JSON state timeline is acceptable.

## 7. M30 historical prefix replay

Use completed regular-session M30 bars derived from the recent completed 1-minute provider window.

Replay every available M30 cutoff after warm-up for each security where data is available.

HK lunch must remain unbridged; US extended-session data must remain excluded from PAQS M30.

Report the exact available M30 date span and bar count. Do not imply coverage beyond the provider's available recent minute window.

## 8. No-lookahead / immutability replay audit

For real D1 and M30 data, independently verify prefix invariance at many cutoffs.

For a sample of at least 50 cutoffs per available timeframe/security when enough data exists:

1. compute structure on prefix `[0:t]`;
2. recompute on a later prefix `[0:t+k]`;
3. compare all already-confirmed Pivot facts whose confirmation ref is `<= t`;
4. compare stable IDs/provenance of already-confirmed structure that is contractually immutable.

Any past confirmed Pivot extreme, confirmation ref, type, hierarchy, price, ATR-at-confirmation or ID changing after future bars arrive is a HIGH-severity checkpoint failure.

## 9. Boundary and stress-case mining from real data

Automatically identify real-data examples where available for:

- largest positive and negative close-to-close moves;
- largest opening gaps;
- highest ATR / volatility spikes;
- lowest ATR / volatility compression;
- dense Micro Pivot sequences;
- sparse Major Pivot sequences;
- near-equal highs/lows;
- repeated reactions near a Zone;
- candidate one-touch Zones;
- confirmed multi-touch Zones;
- periods with no active Range;
- active Range periods;
- transitions between RANGE / BULL_TREND / BEAR_TREND / UNCERTAIN states **as observations only** (do not implement TASK-006C transition semantics).

For selected examples provide the surrounding bar references and structure output needed for human review.

## 10. Stability metrics

For each security/timeframe summarize:

- Micro Pivots per 100 bars;
- Major Pivots per 100 bars;
- median bars between Major Pivots;
- confirmed Zone count and median touch count;
- fraction of replay cutoffs in each Base Regime;
- number of Base Regime state changes per 100 bars;
- active-Range fraction;
- median active-Range lifetime when measurable;
- count of prefix-invariance violations (must be zero).

These are diagnostic metrics, not optimization targets.

Do not declare a parameter good merely because it produces a desired trend or fewer state changes.

## 11. Small-perturbation sensitivity check

Without changing production defaults, run a validation-only one-at-a-time sensitivity comparison for a representative D1 subset.

At minimum compare defaults against:

```text
major_pivot_atr_lambda: 1.7 / 1.8 / 1.9
zone_cluster_epsilon_atr: 0.45 / 0.50 / 0.55
range_inside_ratio: 0.65 / 0.70 / 0.75
```

Use supported immutable config construction only; do not patch production constants.

Report how many cutoffs change:

- latest Major Pivot identity;
- Zone set/geometry materially;
- active Range state;
- Base Regime.

The purpose is to identify pathological parameter brittleness, not to choose the historically most profitable parameter.

No parameter optimization is authorized.

## 12. Human-review sample selection

Produce a compact human-review set rather than cherry-picking only successful-looking cases.

For each available security, select at least:

1. one clean/trending-looking period if one exists;
2. one range/choppy-looking period if one exists;
3. one volatility shock/gap period if one exists;
4. one ambiguous/UNCERTAIN period if one exists.

Selection criteria must be stated. Include counterexamples where the engine output appears questionable.

For each sample provide:

- security;
- timeframe;
- cutoff;
- preceding bar window/reference range;
- latest price/close at cutoff;
- ATR;
- recent Major/Micro Pivots;
- Swing labels;
- Zones;
- active Range;
- Base Regime and explanation;
- concise reviewer question such as `Does this Major Pivot look too dense?` or `Does this Zone correspond to repeated visible reactions?`.

Do not label the sample `correct` before human review.

## 13. Validation-only tooling

A small reproducible validation harness may be added under `tools/validation/` to:

- retrieve current allowed provider data;
- reuse existing application/core services;
- replay prefixes;
- compute diagnostic summaries;
- produce compact JSON/CSV/Markdown evidence.

It must not fork/copy the PAQS algorithm or introduce a second implementation of structure rules.

The harness must import and execute the accepted production Structure Engine so that evidence tests the real implementation.

## 14. Required evidence document

Create:

```text
docs/reviews/TASK_006B_REAL_MARKET_STRUCTURE_CHECKPOINT.md
```

The report must separate:

- deterministic validation evidence;
- live/current environmental evidence;
- historical current-QFQ replay evidence;
- sensitivity evidence;
- human-review samples;
- blockers/limitations.

It must explicitly state:

```text
historical_replay_safe = false
```

for current provider-QFQ historical evidence.

## 15. Checkpoint verdict

The validation harness itself does not approve TASK-006C.

Final status should be one of:

```text
READY_FOR_HUMAN_REVIEW
BLOCKED_REAL_DATA
STRUCTURE_CONCERNS_FOUND
```

Use `STRUCTURE_CONCERNS_FOUND` if deterministic behavior remains valid but real structure shows materially questionable density, geometry, instability, or regime behavior requiring research/remediation.

Use `BLOCKED_REAL_DATA` if OpenD/data entitlement prevents sufficient real evidence.

Use `READY_FOR_HUMAN_REVIEW` only when sufficient evidence and samples were generated for the user/project manager to inspect.

Only the later human/project review may mark the mandatory checkpoint satisfied.

## 16. Stop

Commit/push only validation artifacts on:

```text
validation/006b-real-market-structure-checkpoint
```

Do not modify or merge `roadmap/no-live-trading`.

Do not modify `task/006b-paqs-structure-engine`.

Do not start TASK-006B1 implementation.

Do not start TASK-006C.

Stop after the validation evidence is pushed.