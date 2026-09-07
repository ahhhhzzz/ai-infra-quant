# PAQS Engineering Guide — TASK-007B Analyze/Decision Ledger pending independent review

## Authority and boundary

Implementation authority flows from `AGENTS.md`, `docs/ROADMAP.md`, `docs/MASTER_SPEC.md`, and the
approved TASK-006A, TASK-006B, and TASK-006B2 contracts plus TASK-006B2 Amendment 01. The PAQS
v0.3.1 research lock and Review Amendment A provide adopted semantics where a contract says so.
TASK-006B stops after ATR, Pivot, Swing, Key Level, Zone, Range, and four-state Base Regime. It
contains no later Event, setup, advisory, target/risk-reward, score, or ranking behavior.

TASK-007A separately adopts the accepted PAQS-E Master Spec as a runtime Markdown strategy and
governs only the internal structured-reasoning runtime and first provider adapter. It does not
change the legacy TASK-006B structure engine or authorize a public Analyze workflow.

TASK-007B separately authorizes the current Analyze API and immutable analysis evidence described
below. Its implementation remains pending independent review. Phase 1 migration and review
evidence remain immutable. Calendar/W1/D1/M30 facts are preserved only inside each formed
reasoning request's evidence capsule; no standalone market-data store or replay service is added.

## Data flow and module boundaries

```text
stored canonical Security UUID
  -> dynamic US/HK equity market contract
  -> read-only Market Data Provider port
  -> canonical quote / completed D1 / completed 1m / trading days
  -> provider-agnostic PAQS input preparation
  -> immutable Snapshot-on-Demand factual market snapshot
  -> canonical serialization and SHA-256 snapshot hash
```

Futu SDK enums, DataFrames, and quote contexts stop inside `integrations/futu_quote/`. Core domain
types contain only Python dates/times, aware UTC datetimes, IANA timezone names, Decimal OHLCV, and
canonical enums. The composition root is the only place that selects provider mode.

## Dynamic Security mapping and validation

The market contract is:

| Market | Currency | Timezone | Initial regular session |
|---|---|---|---|
| US | USD | `America/New_York` | 09:30–16:00 |
| HK | HKD | `Asia/Hong_Kong` | 09:30–12:00, 13:00–16:00 |

Canonical provider code equals canonical display symbol (`US.NVDA`, `HK.00700`). This mapping is a
request, not proof of provider support. `POST /api/v1/watchlist/supported-securities` first requires
an AVAILABLE quote whose returned canonical symbol/currency exactly match and whose provider-neutral
classification explicitly confirms equity. Futu maps this from `equity_valid`; false, missing, or
invalid classification fails closed. Only after validation does one unit of work create/reuse the
Security and add/reactivate the default Watchlist membership.

New identities remain `USER_SUPPLIED`, `USER_SUPPLIED_UNVERIFIED`, and tradability `UNVERIFIED`.
Research eligibility requires an enabled US/HK equity, matching market currency, and legitimate
market data. It deliberately does not call `strategy_and_orders_allowed` or require brokerage
tradability verification. A stored currency/timezone conflict fails explicitly.

## Trading-calendar port

The provider-neutral operation is `get_trading_days(market, start_date, end_date)`. A canonical row
retains market date, IANA timezone, canonical and raw provider day type, known session segments,
provider, and retrieval time. Futu `WHOLE`, `MORNING`, and `AFTERNOON` are mapped inside the adapter.
Unknown types keep their raw label and have no guessed segments. The Futu calendar excludes regular
weekends/holidays but may not reflect temporary closure anomalies; actual completed-bar coverage is
therefore measured separately.

## W1 finalization

Completed D1 bars are grouped by market-local ISO week and aggregated with first open, maximum
high, minimum low, last close, and Decimal volume sum. A candidate is finalized only when evidence
available at the cutoff shows one of:

1. the final scheduled calendar session ended;
2. a legitimately available D1 exists in a later ISO week; or
3. live market-local time passed the end of the ISO week.

Calendar source dates are compared with D1 source dates. Missing sessions make coverage PARTIAL
and keep the bar out of `completed_w1_bars`. A holiday-shortened week uses its actual last scheduled
session and does not wait for a fictional Friday. Source rows with retrieval times after the cutoff
are excluded, preventing future-bar injection.

## M30 regular-session aggregation

M30 is derived only from canonical completed 1-minute bars. Buckets are anchored independently at
each canonical session-segment start. US extended-session observations are ignored. Hong Kong lunch
is never crossed. IANA timezone conversion supplies DST behavior.

Every normal bucket expects exactly 30 distinct one-minute intervals with correct one-minute ends.
OHLCV uses first open, maximum high, minimum low, last close, and Decimal volume sum. A missing
minute produces PARTIAL coverage and cannot enter `completed_30m_bars`. Zero-fill, forward-fill,
and interpolation are forbidden. Calendar short sessions produce only buckets that fit wholly in
their mapped segment; unknown schedules produce none. Buckets whose end is after the cutoff are not
evaluated as completed.

## Adjustment, quality, and errors

The Futu path labels both source histories `PROVIDER_QFQ_CURRENT`, sets adjustment time to the
calculation cutoff, and sets `historical_replay_safe = false`. No point-in-time corporate-action
claim is inferred.

The input bundle carries source counts, complete/partial derived counts, calendar status, warnings,
and COMPLETE/PARTIAL/INVALID quality. Provider unavailable, error, entitlement, invalid response,
unknown calendar type, currency conflict, and missing bucket coverage remain distinct. Missing
prices are never represented as zero.

The diagnostic endpoint returns only counts, latest completed timestamps, adjustment/calendar
metadata, quality, and warnings. It accepts no public historical `as_of` parameter and emits no
strategy conclusion.

## TASK-006B2 Snapshot-on-Demand factual contract

`PaqsMarketSnapshotQueries` retrieves one current PAQS input acquisition and one current market
state, then freezes them into the provider-neutral `PaqsMarketSnapshot`. The read-only endpoint is
`GET /api/v1/paqs/securities/{security_id}/market-snapshot`; it has no public query parameters and
does not persist the response. A later request builds a new snapshot, while an already returned
frozen domain object cannot change.

The initial schema is `paqs-market-snapshot-v1`. It includes the latest 156 completed COMPLETE W1
bars, 500 completed D1 bars, and 200 completed COMPLETE REGULAR-session M30 bars. Inputs are sorted
chronologically, duplicate canonical bar identities are rejected, and all OHLCV values remain
`Decimal` in the domain and canonical decimal strings in JSON. W1 PARTIAL and UNKNOWN bars are not
authoritative payload bars.

The machine-readable `timeframe_evidence_status` block has explicit `W1`, `D1`, and `M30` entries.
Each retains its upstream provider-neutral `source_status` and authoritative included count. W1
also reports excluded PARTIAL and UNKNOWN counts; M30 reports the existing missing elapsed-bucket
count. The original source coverage, calendar result status/reason, data quality, warnings, and
adjustment truth are retained separately.

`current_price_reference` and `market_state_reference` are always marked `reference_only`. Missing
or failed quote/state results retain their exact status, provider, retrieval time, and reason
without fabricating a price or closed state. Quote `provider_delay_seconds` is preserved when
reported and remains null when absent; the snapshot applies no freshness or executable-price
policy.

The snapshot hash is lowercase SHA-256 over compact sorted-key UTF-8 JSON. The canonical payload
includes schema version, final aware-UTC `as_of_timestamp`, every model-visible factual value, and
all model-visible source/provenance fields. It excludes only `snapshot_hash` and transient
`created_at`, so a creation-clock change alone does not alter factual identity. Component retrieval
finishes before the creation clock is read, and `created_at` is clamped to be no earlier than the
final as-of boundary.

This shared snapshot is factual infrastructure. It contains no legacy Structure output, objective
indicator package, branch conclusion, provider model call, database record, dashboard workflow, or
broker capability.

## TASK-007A PAQS-E runtime contract

`PaqsEReasoningRequestV1` binds `paqs-e-reasoning-request-v1` to the exact immutable snapshot hash,
security/market/instrument/As-Of identity, `paqs-e-runtime-config-v1`, the selected explicit model,
the selected strategy ID and exact-byte SHA-256, the runtime prompt version/hash, and
`paqs-e-reasoning-result-v1`. W1/D1/M30 bars, current quote and market state, calendar,
adjustment, quality, coverage, provider delay, warnings, and evidence provenance travel inside the
request. Legacy PAQS-Q structure conclusions do not.

Auxiliary context is an ordered frozen tuple. Every item declares its ID, extensible category,
source label/timestamp, optional provenance, As-Of compatibility, and content. TASK-007A retrieves
none of it and has no hidden previous result or provider conversation. `CURRENT_ANALYSIS` rejects
every explicitly As-Of-incompatible item before provider dispatch, while compatible items retain
their declared order and must not have a source timestamp after the snapshot cutoff.

The lightweight registry maps `paqs-e-master` to
`docs/research/PAQS_E_CONTEXT_FREE_MASTER_SPEC_ZH.md`. The loader accepts registered repository-
relative UTF-8 Markdown only, blocks traversal/absolute paths, and hashes the exact bytes. The
separate `paqs-e-runtime-prompt-v1` resource supplies compact transport/guardrail instructions; it
does not duplicate the strategy.

The provider-neutral port returns either a parsed result or one of `CONFIGURATION_ERROR`,
`PROVIDER_UNAVAILABLE`, `PROVIDER_REFUSAL`, or `INVALID_STRUCTURED_OUTPUT`. The OpenAI adapter uses
`responses.parse` with the strict Pydantic result schema, the exact caller model ID, and
`store=false`. It attaches no tool, conversation, previous response, or background state. Missing
`OPENAI_API_KEY` is a truthful configuration failure; secret values never enter domain objects or
error text.

Post-validation is `paqs-e-validator-v1`. It preserves the model judgment and either returns it
unchanged with safe provider response identity or rejects contract violations. RR inputs are
canonical Decimal strings. Risk and reward use Decimal only; ratios use local precision 60 and
`ROUND_HALF_EVEN` quantization to scale 18. An actionable state requires a regular-session eligible
entry reference, structural invalidation and nearest structural T1 with separate numeric
calculation references, valid direction/target ordering, and exact recomputed RR. This is contract
validation, not a deterministic replacement PAQS-E strategy. V1 machine-enforces the exact
`SNAPSHOT_QUOTE_REGULAR_OPEN_REQUIRED` and `UPSTREAM_AVAILABLE_REQUIRED` policy identities.
`SUPPORTED + COMPLETE` outputs, and every READY output, require one to four Key Levels. A
configured minimum RR is an actionable-state consistency gate: it rejects a below-threshold READY
judgment but does not invalidate or rewrite an otherwise valid non-action judgment that reports the
same final RR.

## TASK-007B current Analyze and Decision Ledger

`application/paqs_e_analysis.py` composes the existing snapshot query and TASK-007A runtime through
core-facing boundaries. Public POST input is only Security UUID, unchanged explicit model ID and
registered strategy ID. Runtime config and prompt are server-controlled, and public v1 always
sets `auxiliary_context=()`. Each POST acquires exactly one new current immutable snapshot and
makes exactly one reasoning attempt, even for a repeated snapshot/model/strategy selection.
Dashboard polling never calls this service and previous Decisions are never implicit context.

Before runtime dispatch, canonicalize the complete `PaqsEReasoningRequestV1` and hash its UTF-8
bytes. This captures bounded W1/D1/M30 bars, quote/state references, calendar/session/adjustment,
quality/coverage/provider provenance, runtime identities, selected model/strategy and empty
auxiliary context. Store the canonical JSON text itself as byte authority; do not reconstruct
old evidence from a later cache or a database JSON serializer.

The dedicated Decision Ledger port lives under `core/ports/`; entities and evidence invariants
live under `core/domain/`. SQLAlchemy models/repository implement persistence under `database/`.
No database write transaction spans the provider call. Once TASK-007A returns, one transaction
resolves immutable strategy/prompt artifacts and inserts a terminal Analysis Run. A validated
success also inserts its Decision before the transaction commits. The API may return success
only afterward. Insert/commit failure rolls back artifacts, run and Decision together.

Run statuses are `SUCCEEDED`, `PROVIDER_FAILED`, and `VALIDATION_FAILED`. Provider failures keep
the exact safe TASK-007A kind/reason; validation failures keep validator version and exact issues.
Both failure types commit one run with no Decision before returning a truthful non-2xx response.
A Security/snapshot precondition failure before a request exists creates no invented run.

The new migration file is `0002_task007b_paqs_e_decision_ledger.py`, with revision
`0002_task007b_paqs_e_ledger` and
`down_revision="0001_phase1_foundation"`. It uses the current `DATABASE_URL` and creates only:

- `paqs_e_runtime_artifacts`: immutable exact strategy/prompt content, verified SHA-256 and
  deduplication by `(artifact_kind, artifact_key, content_sha256)`;
- `paqs_e_analysis_runs`: immutable complete canonical request/hash, terminal outcome, identities
  and timestamps;
- `paqs_e_decisions`: immutable validated canonical result/hash, direct query-friendly summary
  copies and revision lineage.

SQLite UPDATE/DELETE triggers protect all three tables. Repositories expose no mutation/delete
operation. Canonical payload hashes and artifact hashes are verified on readback; mismatches and
summary disagreements fail truthfully. `rr_t1` stays Decimal and uses the accepted exact
dialect-aware persistence type. Database artifact content is evidence only; the registry and
versioned prompt resource retain runtime authority.

Canonical Decimal rendering and bounds checks are independent of the ambient arithmetic precision:
all accepted digits survive evidence hashing, while existing scale-insensitive forms stay unchanged.

Revision identity is `(security_id, strategy_id)`. Revision 1 has no predecessor; each success
appends the next revision and supersedes the immediately previous Decision. Model or content-hash
changes continue that series, while a new strategy ID starts a separate series. Unique run and
series/revision constraints plus transaction logic prevent duplicate revision claims, without
silently deduplicating explicit Analyze attempts.

Read endpoints expose a run by ID, a Decision by ID and newest-first Security history with an
optional strategy filter and `limit` 1..100 (default 20). They preserve hashes, exact Decimal text,
UTC instants and safe audit identities. No key/header/environment/exception dump is part of an
API schema or evidence row. TASK-007C UI, replay storage, PAQS-Q, paper state, background work and
broker/account/order capabilities remain outside this task.

## TASK-006B normalized structure input

`core/strategy/paqs_structure.py` consumes only the provider-neutral `PaqsInputBundle`. It converts
completed W1, D1, and complete-coverage M30 inputs into one immutable `StructureBar` shape. D1 keeps
its session date; W1/M30 keep their actual interval references. No exchange-close timestamp is
invented. Partial/unfinished inputs cannot enter confirmed structure.

The three engines run independently:

```text
W1  -> CONTEXT
D1  -> SETUP
M30 -> TRIGGER
```

Input quality `INVALID` suppresses all structure calculation. Insufficient per-timeframe history
keeps ATR unavailable and Base Regime `UNCERTAIN`.

## Parameter registry and deterministic arithmetic

`PaqsStructureConfig` is frozen. Defaults are: ATR period 14; Micro/Major Pivot lambda 1.0/1.8;
minimum Pivot separation 2; equal-Swing tolerance 0.25 ATR; Zone cluster epsilon 0.50 ATR; touch
separation 5 bars; Zone halfwidth clamp 0.15–0.75 ATR; Zone merge IoU 0.50; Range lookback 40;
inside ratio 0.70; Range width 2.0–12.0 ATR. Constructor validation enforces the contract's research
ranges and rejects binary float parameters. ATR period is fixed at 14 because this task adopts no
research range for that value. A zero ATR remains an explicit zero-volatility fact, but cannot act
as a Pivot reversal threshold or Range-normalization divisor.

The `config_hash` is SHA-256 over sorted compact JSON. Decimal values use scale-insensitive
canonical strings, so `1.0` and `1.00` hash identically. Structure IDs hash explicit type,
timeframe, config and sorted source IDs/references. All boundary arithmetic uses `Decimal` inside a
local precision-50 `ROUND_HALF_EVEN` context. Exposed and recursively reused values are quantized
to 18 places; the process-global Decimal context is never mutated.

## ATR

True Range uses High minus Low on the first bar. Later bars use the maximum of High–Low,
`abs(High-previous Close)`, and `abs(Low-previous Close)`. ATR is `None` for the first 13 values.
The fourteenth is the arithmetic mean of the first 14 TR values. Later values use
`alpha = 2/(14+1)` and `ATR[t] = alpha*TR[t] + (1-alpha)*ATR[t-1]`. ATR supplies scale only.

## Independent Pivot and Swing engines

Micro and Major are separate directional-change runs; neither promotes or rewrites the other.
After ATR becomes ready, `UNSEEDED` maintains both High and Low candidates. Exactly one
close-reversal direction must meet its lambda and have an earlier extreme. If both directions
qualify on one bar, neither confirms. `SEEK_HIGH` tracks the greatest High and confirms only when a
later completed Close is at least lambda×current ATR below it; `SEEK_LOW` is symmetric. A new
extreme must be at least `pivot_min_bars` from the prior Pivot extreme. Each Pivot keeps both source
references, confirmation ATR/lambda, a stable ID, and explanation.

Labels compare confirmed Pivots of the same hierarchy and type. Current confirmation ATR times
0.25 is epsilon. Highs become HH/LH/EH and lows become HL/LL/EL using strict outside-tolerance
comparisons. Prefix tests recompute with future bars and require all earlier confirmed records to
remain byte-for-byte equivalent.

## Key Levels and Zones

Each confirmed Major Low/High creates a point SUPPORT/RESISTANCE `MAJOR_SWING` Key Level. High and
Low observations are clustered separately. Inputs are sorted by price, extreme key, confirmation
key and Pivot ID. Complete-link admission requires compatibility with every cluster member; an
eligible-cluster tie uses normalized median-center distance then stable ID.

Touches are selected chronologically and must be five source bars apart by default. One produces a
`CANDIDATE`; two produce `CONFIRMED`. Center and reference ATR are simple medians. Width uses median
absolute deviation, clamped to 0.15–0.75 reference ATR. Same-role confirmed Zones repeatedly merge
at the configured IoU, selecting highest IoU, lower bound and stable IDs in that order. The merged
geometry is recomputed from the union of accepted source observations. Candidate Zones never force
a merge. Confirmed Zone geometry also appears as `PIVOT_CLUSTER` Key Levels.

## Range and Base Regime

Range pairs require separated confirmed support/resistance Zones and at least two independent
touches per side. Chronological touches map to L/H; same-side runs compress and at least four
alternating groups are required. The latest 40 completed bars must all have ready ATR. At least
70% of closes must lie inside `[support.lower_bound, resistance.upper_bound]`; center width divided
by median lookback ATR must be 2.0–12.0. A valid Range is active only if the latest close is inside.
Multiple active candidates select by total touches, inside ratio, narrower width, then stable ID.
Range-boundary Key Levels reference geometry without mutating Zones.

Base Regime precedence is invalid/insufficient -> `UNCERTAIN`, active Range -> `RANGE`, then coherent
Major HH+HL -> `BULL_TREND` or LH+LL -> `BEAR_TREND`; everything else is `UNCERTAIN`. Bull coherence
also requires the latest close not below the latest labelled HL, and Bear coherence requires it not
above the latest labelled LH. Micro structure cannot set Base Regime.

## Structure snapshot and API

`PaqsStructureQueries` composes the current 006A bundle and immutable default config. The read-only
`GET /api/v1/strategies/paqs/securities/{security_id}/structure` endpoint has no replay/config
parameter. Its snapshot carries versions/hash, input and adjustment metadata, calculation/as-of
times, per-timeframe ATR/Pivots/labels/levels/Zones/Ranges/Regime, source references, explanations,
and warnings. Decimal values serialize as strings. Nothing is persisted.

Synthetic fixtures S01–S15 cover bull, bear, Range, insufficient history, delayed and ambiguous
Pivot confirmation, equal labels, candidate/confirmed/merged Zones, invalid/multiple Ranges,
prefix invariance, and completed M30 filtering. They are deterministic semantics tests, not market
or profitability evidence.

## Future extension points

TASK-006C–006E may add events, setup/risk, and advisory/dashboard behavior only after separate
approval and the required human review of real structure. They must not change input or structure
facts based on desirable later outcomes. Broader historical replay requires a separate
point-in-time adjustment/data contract.

## Common misinterpretations

| Misinterpretation | Correct meaning |
|---|---|
| Provider quote validation = brokerage tradability verification | It proves only an exact read-only quote response. |
| User-added Security = real broker instrument/account state | It is a local canonical identity with no account link. |
| Latest quote = final D1 close | Intraday/latest and completed Daily facts are separate. |
| 30m = provider-native 30m requirement | M30 is deterministically derived from completed 1m. |
| US `Session.ALL` = PAQS M30 structural session | Initial PAQS M30 filters to 09:30–16:00 regular time. |
| QFQ = automatically point-in-time-safe historical replay | Current QFQ is explicitly marked replay-unsafe. |
| PAQS input endpoint = trading recommendation | It exposes input health only and has no advisory output. |
