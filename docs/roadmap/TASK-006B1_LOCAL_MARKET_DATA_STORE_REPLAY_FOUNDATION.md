# TASK-006B1 — Local Market Data Store & Replay Foundation

Status: **PLANNED TASK NODE — DESIGN / TASK CONTRACT REQUIRED**

Placement: **after TASK-006B acceptance and real-structure checkpoint, before TASK-006C approval**

Repository: `ahhhhzzz/ai-infra-quant`

Authoritative roadmap branch: `roadmap/no-live-trading`

## Purpose

Introduce a small local research data store so completed canonical market-data observations that the application has legitimately obtained are not lost when the provider's bounded history window moves forward.

The main reason for this task is long-horizon PAQS research and replay, especially M30/Event work that ultimately depends on completed 1-minute history.

This task is infrastructure for research reproducibility. It is not a return to the earlier broad backtest/platform scope.

## Initial intended scope

The later Task Contract should evaluate and, if approved, implement the smallest durable design for:

- canonical completed D1 observations;
- canonical completed 1-minute observations;
- Security identity / market / timeframe / interval identity;
- Decimal OHLCV;
- provider/provenance;
- retrieval timestamp;
- adjustment basis and relevant source-quality/coverage facts;
- observation/version semantics sufficient to avoid silently losing the historical version actually seen by PAQS when provider-adjusted history later changes;
- deterministic local reads suitable for historical structure/event replay;
- incremental ingestion/deduplication without fabricating missing bars.

The preferred architectural direction is to persist primary completed market-data facts and continue deriving W1 and regular-session M30 deterministically, rather than treating W1/M30 as independent authoritative market facts.

## Explicit non-goals unless a later Task Contract separately approves them

Do not infer approval for:

- tick persistence;
- order-book / Level-2 storage;
- raw Futu DataFrame persistence;
- provider-native SDK objects in core/database models;
- institutional time-series infrastructure;
- Kafka, distributed workers, data lake/lakehouse architecture;
- general-purpose market-data warehouse;
- full point-in-time backtesting platform;
- strategy P&L/Alpha claims;
- broker account, positions, orders or fills;
- broker-write capability.

## Important design issue to resolve before implementation

Current Futu history is labelled `PROVIDER_QFQ_CURRENT` and is explicitly not claimed to be strict point-in-time historical replay data. The later design discussion must decide how local observations/versioning behave when the provider returns changed adjusted historical bars after corporate actions.

A simple overwrite policy must not silently destroy the ability to determine what data version PAQS had actually observed at an earlier calculation time.

## Governance

This file records a future task node only. It is **not an implementation contract**.

Before implementation:

1. TASK-006B must pass independent review and the mandatory real-market structure checkpoint.
2. The user and reviewer must discuss the exact persistence/version/replay requirements.
3. A separate explicit TASK-006B1 Task Contract must be approved.
4. TASK-006C must not be treated as approved merely because this task node exists.

The permanent read-only/no-live-trading product boundary remains unchanged.
