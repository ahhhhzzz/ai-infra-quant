# TASK-006B Structure Stability Review

Status: **RESEARCH REVIEW — DECISION REQUIRED BEFORE ANY IMPLEMENTATION**

Repository: `ahhhhzzz/ai-infra-quant`

Accepted TASK-006B authoritative SHA: `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`

Validation evidence branch: `validation/006b-real-market-structure-checkpoint`

Validation evidence HEAD: `b23d1c196eda957ab04dc0f79c477e2ee1a6e471`

Primary evidence:

- `docs/reviews/TASK_006B_REAL_MARKET_STRUCTURE_CHECKPOINT.md`
- `tools/validation/task006b_real_market_checkpoint.py`

This document records research conclusions and open design decisions only. It is **not** an implementation contract and does not authorize changes to production defaults, product code, TASK-006B1, or TASK-006C.

## 1. Executive conclusion

TASK-006B passed deterministic implementation review, remediation, no-lookahead checks, and integration. The real-market checkpoint then found structure-stability concerns that are material enough to block semantic acceptance of the Structure Engine for use as the foundation of TASK-006C.

The checkpoint verified:

- 250 passed / 1 skipped deterministic tests;
- 0 no-lookahead violations across 500 sampled real-data audits;
- valid current W1/D1/M30 reads for AVGO, VRT, HK.09698, NVDA and HK.00700;
- truthful `PROVIDER_QFQ_CURRENT` / `historical_replay_safe = false` metadata;
- no product code change in the validation branch.

Therefore the current concern is **not** future leakage, arithmetic nondeterminism, provider-boundary failure, or broker-safety failure.

The concern is that the accepted deterministic semantics can produce operationally unstable or stale current structure on real history.

## 2. Finding A — unbounded history-origin dependence / Pivot path-lock

Severity for research: **HIGH**

Observed AVGO D1 endpoint at the same current-QFQ terminal bar:

- using all 1,500 D1 bars, the latest Major High/Low remained in November/October 2020 and Base Regime was `UNCERTAIN`;
- using the latest 500 D1 bars, latest Major High/Low moved to July/June 2025 and terminal Base Regime was `BULL_TREND`.

This is not a prefix-invariance violation because the leading-history boundary differs. It exposes a missing semantic contract: current structure is presently initialized from whatever earliest bar the provider happens to return.

The current Pivot engine is a finite directional-change state machine with an `UNSEEDED` start. Once seeded, every later turn depends on that historical path. With no explicit structural horizon or warm-start/reseed rule, the output can depend materially on an arbitrary provider history origin.

For a current decision terminal, the provider's maximum available history must not silently define the semantic state of today's Pivot chain.

### Design decision required

Define a deterministic **structure analysis horizon / warm-start contract** that separates:

1. data available from the provider/store;
2. bars used only to warm ATR / initialize state;
3. bars whose confirmed Pivot/Zone/Range facts are eligible to define current structure.

Candidate approaches to investigate before approval:

- fixed rolling structure horizon with an explicit hidden warm-up/seed buffer;
- a deterministic common structural anchor followed by a bounded current-analysis horizon;
- another bounded initialization scheme that demonstrates convergence and low origin sensitivity.

Do not choose a window length by maximizing historical returns.

Required acceptance evidence for any proposal:

- same terminal bar under materially longer available leading history should produce semantically convergent current Major structure once the required warm-start history is satisfied;
- old provider history must not be able to lock the current Pivot chain for years without an explicit stale/insufficient result;
- no-lookahead/prefix invariance must remain intact within the declared horizon semantics.

## 3. Finding B — Micro/Major hierarchy inversion and stale lower-threshold sequence

Severity for research: **HIGH / linked to Finding A**

The latest-500/recent-window checkpoint observed Major Pivot density greater than Micro Pivot density in multiple security/timeframe combinations, including HK.00700 M30, HK.09698 M30, NVDA D1 and VRT D1.

The accepted research history intentionally runs Micro and Major as independent directional-change instances and prohibits retrospective Micro-to-Major promotion. That rule alone does not mathematically guarantee `Micro count >= Major count`.

However the observed behavior is semantically concerning because:

- Micro uses the lower threshold (1.0 ATR) and is intended to describe finer structure;
- Major uses the higher threshold (1.8 ATR) and is intended to describe coarser Regime/Range structure;
- VRT 2026 samples retained last Micro Pivots from May 2025 while Major Pivots continued into 2026;
- AVGO terminal D1 Micro/Major facts could remain stale for extended periods.

This suggests independent engines can seed into different phases and remain path-locked.

### Design decision required

Research must decide whether PAQS requires a stronger hierarchy invariant.

Possible directions to evaluate without yet approving implementation:

- shared deterministic initialization/anchor for Micro and Major while retaining independent post-seed engines;
- explicit recency/staleness rules that suppress a hierarchy whose latest confirmed facts are too old to describe current structure;
- a true nested hierarchy design in which Major structure is constructed from or constrained by lower-level confirmed structure.

A true nested hierarchy would change the v0.2 research semantics and therefore requires explicit amendment rather than an implementation shortcut.

Do **not** impose `Micro count >= Major count` as a blind code assertion until the intended hierarchy semantics are proven.

## 4. Finding C — old Zones never expire in TASK-006B

Severity for research: **HIGH-MEDIUM**

Full current D1 snapshots contained 46 confirmed Zones for HK.00700 and 44 for HK.09698 across broad historical price spans.

The current TASK-006B implementation builds Zones from all eligible Major Pivots in the normalized history. It has no Zone age/decay filter.

This is notable because the earlier PAQS v0.2 research lock explicitly stated:

```text
old zone should not remain valid forever
zone_max_age_bars default = 250 STF bars
range = [100, 500]
age resets when a new valid reaction uses the zone
```

TASK-006B adopted several v0.2 Zone parameters but did not adopt Zone decay.

This omission can create cumulative structural clutter and can feed old Zone touches into current Range construction.

### Design decision required

Revisit Zone recency as an explicit deterministic semantic rather than a UI filter.

The later implementation contract should decide:

- whether to restore a Zone maximum age rule;
- whether age is measured from latest accepted reaction/touch;
- whether W1/D1/M30 require distinct horizons;
- whether expired Zones remain available as diagnostic history while being excluded from active structure;
- how Zone age interacts with future TASK-006C role flip/retest semantics.

No value is approved by this review merely because v0.2 proposed 250 STF bars.

## 5. Finding D — Range recency and identity metrics need separation

Severity for research: **MEDIUM**

Range construction currently:

- uses the last 40 closes for inside ratio;
- but derives alternating support/resistance reactions from the full touch history of the selected Zones;
- can therefore combine recent closes with much older boundary reactions when old Zones remain eligible.

This should be reviewed together with Zone decay/recency.

The checkpoint also reported short median active-Range lifetimes (for example NVDA D1 median two bars). That metric must **not** be interpreted literally as semantic Range duration without refinement.

Reason: `range_id` contains support/resistance `zone_id`; Zone IDs are versioned by their source Pivot/touch set. A new accepted touch or Zone merge can change the Range ID even when substantially similar geometry remains active.

Therefore future validation must report at least two separate concepts:

1. **Regime continuity** — consecutive bars whose Base Regime remains `RANGE`;
2. **Range version continuity** — consecutive bars retaining the exact same versioned Range ID.

Only the first measures semantic Range-state persistence. The second is useful audit/version information.

## 6. Finding E — Regime churn is real but not yet a standalone bug

Severity for research: **MEDIUM**

The replay observed Base Regime changes of roughly:

- NVDA D1: 11.91 changes per 100 replay cutoffs;
- HK.09698 D1: 9.86 changes per 100 replay cutoffs.

Unlike the Range-ID lifetime metric, this is an actual state-change measure and is not explained by version IDs.

However it is premature to add hysteresis/debouncing directly to Base Regime because:

- current churn may be downstream of history-origin path-lock;
- current churn may be downstream of old Zone/Range eligibility;
- TASK-006C later owns explicit Event/Transition semantics.

First stabilize Pivot horizon/hierarchy and Zone/Range recency, then rerun the same diagnostics. Only residual excessive Base-Regime churn should trigger a separate Base-Regime semantic amendment.

## 7. Finding F — parameter sensitivity is a real diagnostic, not a direct tuning instruction

Severity for research: **MEDIUM**

The checkpoint's sensitivity comparison is semantically constructed: Zone comparisons use role/status/center/bounds/source-touch references rather than `zone_id`, so the high changed-cutoff counts are not merely caused by `config_hash` changing IDs.

Across 1,185 comparisons:

- Major lambda 1.7 changed Zone state/geometry at 883 cutoffs;
- Major lambda 1.9 changed Zone state/geometry at 1,004 cutoffs;
- corresponding Base Regime changes were much smaller (62 and 22).

This means Zone geometry is sensitive to modest Major Pivot threshold changes, while the downstream Base Regime is more stable than the raw Zone layer.

Do not optimize lambda to reduce these counts or improve returns.

After horizon/hierarchy/Zone-recency semantics are stabilized, repeat the same perturbation audit. Acceptance should emphasize:

- core Major structural conclusions;
- current/relevant Zone geometry;
- current Range/Regime stability;

rather than requiring every historical Zone version to be invariant under parameter perturbation.

## 8. Findings that remain healthy

The checkpoint supports retaining these accepted properties:

- completed-data-only eligibility;
- explicit W1 COMPLETE coverage requirement;
- Decimal arithmetic;
- deterministic IDs/hashes within one config;
- no-lookahead / prefix invariance under a fixed origin;
- distinct extreme and confirmation references;
- current QFQ replay-unsafety metadata;
- provider-neutral core boundary;
- no brokerage/account/write behavior.

Any stabilization work must preserve them.

## 9. Required next research step before code

Before another production code change, prepare a bounded Structure Stability Amendment that explicitly decides:

1. current-structure analysis horizon and initialization/warm-start semantics;
2. Micro/Major initialization relationship and intended hierarchy invariant;
3. Pivot staleness behavior;
4. Zone decay/recency semantics;
5. Range boundary reaction recency semantics;
6. corrected validation metrics for Range semantic continuity vs version continuity.

Then rerun the existing real-market checkpoint, plus explicit origin-sensitivity comparisons, before accepting TASK-006B semantically.

## 10. Acceptance gates for stabilized 006B

A future remediation must not be considered complete only because unit tests pass.

At minimum require:

- deterministic tests remain green;
- 0 no-lookahead violations;
- current structure no longer materially depends on arbitrary extra ancient leading history after the declared warm-start requirement is met;
- current Micro/Major outputs satisfy the explicitly approved hierarchy semantics;
- no multi-month/year stale Pivot chain can silently define current structure unless that behavior is explicitly justified and surfaced;
- active/relevant Zone set obeys approved recency semantics;
- Range semantics use appropriately recent/eligible boundary reactions;
- Range semantic continuity is measured separately from version-ID continuity;
- regime churn is rerun after upstream stabilization;
- parameter sensitivity is rerun without optimizing to P&L;
- real human semantic sanity review is repeated;
- no TASK-006C/B1/advisory/broker behavior is introduced.

## 11. Task sequencing impact

Until this research issue is resolved:

```text
TASK-006B deterministic implementation: PASS / integrated
TASK-006B semantic real-market acceptance: NOT YET PASSED
TASK-006B1 Local Market Data Store: PLANNED, DO NOT START YET
TASK-006C Event Engine: NOT APPROVED
```

The project remains intentionally stopped at the Structure Engine stabilization checkpoint.

**End — TASK-006B Structure Stability Research Review**