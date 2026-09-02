# PAQS v0.3.1 — Review Amendment A

**Status:** RESEARCH DEFINITION LOCK AMENDMENT; **not an implementation contract**  
**Applies to:** `PAQS_V0.3.1_COMPLETENESS_LOCK.md`  
**Purpose:** resolves two deterministic ambiguities found during independent post-draft review. Where this amendment is more specific than the base v0.3.1 document, this amendment governs the v0.3.1 research definition.

---

# A1. Hard Invalidation uses an explicit close/buffer inequality

The phrase `decisive close` is not itself an algorithm. For v0.3.1, hard invalidation must be represented by an explicit boundary, timeframe and ATR buffer.

For a Long thesis with snapshotted invalidation boundary `B`:

\[
C_t < B - k_{inv}\cdot ATR_t
\]

where:

```text
C_t       = completed close on invalidation_timeframe
B         = immutable snapshotted invalidation boundary
k_inv     = declared invalidation buffer parameter
ATR_t     = ATR legitimately available at completed bar t
```

Only after the completed close satisfies that inequality is the hard invalidation confirmed.

A wick/low through the boundary without the required close is not, by itself, `HARD_INVALIDATION`; it may be recorded as a warning/event feature.

Setup-family bindings are therefore interpreted as follows.

## A1.1 Trend Pullback Long

```text
B = snapshotted STF structural-support lower_bound
k_inv = invalidation_buffer_atr
```

Hard invalidation:

\[
C^{STF}_t < B - k_{inv}ATR^{STF}_t
\]

The farther HTF context boundary remains diagnostic context and cannot retroactively widen the snapshotted trade invalidation.

## A1.2 Range Failed Breakdown Long

```text
B = failed_break_extreme
k_inv = failed_break_stop_buffer_atr
```

Hard invalidation:

\[
C_t < B - k_{inv}ATR_t
\]

## A1.3 Right-Side Breakout Long — Follow-through variant

```text
B = immutable breakout-source resistance lower_bound
k_inv = invalidation_buffer_atr
```

Hard invalidation:

\[
C^{STF}_t < B - k_{inv}ATR^{STF}_t
\]

## A1.4 Right-Side Breakout Long — Retest variant

The hard invalidation uses the immutable Retest Failure boundary derived from the breakout-source snapshot:

```text
B = old breakout-source zone lower_bound
k_inv = retest_failure_buffer_atr
```

Hard invalidation:

\[
C^{STF}_t < B - k_{inv}ATR^{STF}_t
\]

No implementation may substitute a farther level merely because it improves historical survival or RR.

---

# A2. Deterministic W1 finalization

The phrase `week is known complete` must not depend on hindsight.

## A2.1 Weekly bucket

W1 uses the market-local ISO week containing each completed D1 session.

A candidate weekly bar aggregates only D1 bars legitimately available in that same market-local ISO week.

## A2.2 Historical/as-of finalization

A W1 bucket may be emitted as `completed = true` only when one of the following is legitimately known at the evaluation cutoff:

```text
A. the official market calendar establishes that the final trading session of that ISO week has completed; or
B. a completed D1 bar from a later market-local ISO week has become available; or
C. for current live evaluation, market-local time has moved beyond the end of that ISO week.
```

If none is true:

```text
weekly_bar_status = PARTIAL
```

and the bar is excluded from PAQS HTF structure.

This rule handles holiday-shortened weeks without assuming that Friday must exist.

## A2.3 No future completion

During historical replay, a later-week bar may prove that the prior week is complete only when the historical clock actually reaches that later bar. It may not be consulted while evaluating an earlier cutoff.

## A2.4 HTF behavior during the current week

Until the current W1 becomes completed under A2.2:

```text
PAQS HTF uses the latest prior completed W1
```

The partial current W1 may be displayed separately as non-authoritative context but must not enter confirmed Pivot/Regime/Setup calculations.

---

# A3. Additional tests

## CA1 — Wick through invalidation is not hard exit

A Long support boundary is 100, buffer is 0.10 ATR, bar low trades below the buffered boundary but the completed close returns above it.

Expected:

```text
hard_invalidation = false
holder_advisory != EXIT_IF_HELD
```

## CA2 — Close confirms hard invalidation

The completed close satisfies:

```text
close < boundary - buffer * ATR
```

Expected:

```text
hard_invalidation = true
holder_advisory = EXIT_IF_HELD
```

## CA3 — Holiday-shortened week

The official market calendar establishes Thursday as the final trading session of the week and that session has completed.

Expected:

```text
W1 completed after Thursday close
```

No nonexistent Friday bar is required.

## CA4 — Historical week cannot be finalized from the future

At historical Thursday cutoff, the engine has no legitimate knowledge that the week is complete.

Expected:

```text
current W1 = PARTIAL
```

A later-week D1 bar may finalize the prior W1 only after the historical clock reaches that later bar.

---

**End — PAQS v0.3.1 Review Amendment A**
