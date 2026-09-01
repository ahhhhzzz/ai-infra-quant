# Composite Quant Score Research Specification

Status: **PROPOSED / RESEARCH_UNVALIDATED**; not approved and not implemented

Future authority: `docs/ROADMAP.md` decision `MTF-001`

## 1. Governance and supersession

This document records only the approved high-level dual-timeframe architecture and research
questions. It does not approve a concrete strategy.

The former completed-daily-only `AIInfraStrategy v1` formula proposal—including its weights, thresholds,
bands, gates, state machine, sizing candidates, and golden cases—is withdrawn as implementation
authority. It may be recovered from Git history for research context, but must not be implemented
under this specification.

A later explicit strategy Task Contract must approve the complete model before implementation.
That approval must specify formulae, weights, thresholds, normalization, score range/bands, missing
data behavior, validation fixtures, and any paper-sizing policy. Phase 1 acceptance and `MTF-001`
do not supply that approval.

No formula or example in this document is a profitability or predictive-validity claim.

## 2. Product and safety boundary

The strategy is read-only decision support for the configurable tracked set beginning with:

```text
US.AVGO
US.VRT
HK.09698
```

It consumes provider-agnostic canonical market data, produces explainable research output, and may
rank tracked securities. It has no provider SDK object, brokerage-account fact, external order,
or execution capability. Whether the user trades in the broker's official client is outside the
strategy and outside application state.

Missing, delayed, stale, unavailable, or invalid inputs remain explicit. No market, valuation,
fundamental, or risk value is fabricated.

## 3. Approved high-level architecture

```text
Composite Quant Score
    =
Daily Base Score
    +
Intraday Minute Adjustment
```

Only this decomposition is approved.

### 3.1 Daily Base Score research role

The daily component represents medium-term structure. A later strategy task may evaluate factors
such as:

- trend;
- absolute momentum;
- relative momentum;
- volatility;
- drawdown;
- medium-term risk.

Daily bars remain a supported input and the baseline for historical backtesting.

### 3.2 Intraday Minute Adjustment research role

The minute component represents current-session strength and risk using only completed 1-minute
bars. A later strategy task may evaluate:

- 5-minute, 15-minute, or 30-minute momentum;
- price versus session open;
- price versus previous close;
- short-term moving averages;
- VWAP;
- minute volume;
- intraday volatility/risk adjustment.

These are candidate factor families, not approved calculations.

## 4. Time and data semantics

Strategy input and output distinguish:

```text
latest_quote_at
latest_completed_minute_bar_at
latest_completed_daily_session
score_calculated_at
```

Only completed 1-minute bars may enter the minute adjustment. An unfinished bar is excluded. A
latest/intraday price is not a final daily close. Provider latency is independent from the
approximately 60-second dashboard polling/recalculation cadence.

All instants are aware UTC, with market-local session/calendar metadata where required. Decimal is
used for financial calculations. Point-in-time historical research uses only data legitimately
available at the calculation cutoff.

## 5. Missing-data and refresh behavior

The future strategy contract must define deterministic behavior when daily or minute inputs are
missing, delayed, stale, partial, or erroneous. It must expose component coverage and timestamps.
It must never silently substitute zero, reuse an unfinished minute bar, or invent a price.

During an active visible dashboard session, the approved model will eventually recalculate
approximately every 60 seconds and on manual refresh. Automatic refresh pauses while hidden and
runs immediately after the page becomes visible. This cadence does not authorize background
processing after the page closes.

## 6. Decisions required before implementation

The later strategy Task Contract must explicitly approve:

1. Daily Base Score factors, lookbacks, transformations, and normalization.
2. Intraday Minute Adjustment factors, lookbacks, normalization, and maximum influence.
3. Combined score scale, arithmetic, weights, bounds, thresholds, and bands.
4. Treatment of differing US/HK sessions and market status.
5. Freshness/delay/staleness rules for quotes, daily bars, and minute bars.
6. Missing/partial/error coverage behavior and risk/reference states.
7. Cross-sectional ranking method and tie behavior.
8. Decimal context, rounding, persistence, and deterministic replay.
9. Point-in-time backtest behavior and transaction-cost assumptions.
10. Synthetic golden fixtures and anti-look-ahead tests.
11. Any simulated-paper interpretation or sizing rule.

No default, recommendation, or earlier proposal silently resolves these decisions.

## 7. Validation requirements for the future approved model

At minimum, future tests must prove:

- daily-only baseline behavior and daily-bar support;
- completed-minute filtering and exclusion of unfinished bars;
- correct separation of latest price and final daily close;
- deterministic combined-score arithmetic with Decimal;
- explicit missing/delayed/stale/error states;
- independent polling cadence and provider-latency metadata;
- US/HK session/calendar correctness;
- reproducible ranking and risk/reference state;
- point-in-time safety and future-record injection resistance;
- no provider-native, brokerage-account, or execution dependency;
- no profitability claim from passing tests or backtests.

Synthetic fixtures must be clearly labelled and must not be presented as real market data.

## 8. Current implementation statement

No Daily Base Score, Intraday Minute Adjustment, combined Composite Quant Score, ranking, or
minute-data strategy behavior is implemented by this documentation task. Phase 2 has not begun.
