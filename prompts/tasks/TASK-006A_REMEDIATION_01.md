# TASK-006A — Focused Remediation 01

Status: **APPROVED FOCUSED REMEDIATION — TASK-006A ONLY**

Repository: `ahhhhzzz/ai-infra-quant`

Task branch: `task/006a-dynamic-us-hk-paqs-input-foundation`

Authoritative base branch: `roadmap/no-live-trading`

Authoritative base SHA: `2702750dddb9c076d0850ff0ed152964dde3d3f2`

Independently reviewed implementation HEAD: `355d51fdb92b585a7148579005180e103bc72c3b`

Parent Task Contract: `prompts/tasks/TASK-006A_DYNAMIC_US_HK_PAQS_INPUT_FOUNDATION.md`

This remediation is limited to two independently confirmed defects. It does not authorize redesign, refactoring for preference, or any TASK-006B behavior.

## 1. Confirmed defect A — provider validation does not prove EQUITY classification

### Problem

TASK-006A permits the dynamic-add flow only for:

```text
US listed EQUITY
HK listed EQUITY
```

The reviewed implementation validates that a requested canonical symbol returns an available matching quote, but then creates/reuses the local flow as `InstrumentType.EQUITY` without requiring provider-confirmed equity classification.

Futu `get_market_snapshot()` exposes `equity_valid`, documented as whether the security is a stock/equity. The reviewed Futu adapter does not propagate or enforce that fact.

Therefore a quoteable ETF or other non-equity can be falsely admitted to the TASK-006A equity-only workflow.

### Required remediation

Before any Security/Watchlist mutation, the normal dynamic-add flow must require an **explicit provider-confirmed equity classification**.

Provider-specific classification must remain inside `integrations/`; application/core consume a provider-neutral validation result.

The smallest acceptable design may use a dedicated provider-neutral security-validation result or an equivalent narrowly-scoped field, but it must satisfy all of the following:

- exact canonical symbol match remains required;
- currency match remains required;
- provider must explicitly report that the instrument is an equity/stock;
- Futu maps this from `equity_valid` or an equally authoritative provider-native security-type field;
- `equity_valid == False` is rejection;
- missing/unparseable/contradictory classification is rejection, not assumed equity;
- rejection returns a structured validation failure;
- rejection occurs before mutation;
- no new Security row is created;
- no Watchlist membership is created/reactivated;
- market-data validation still does **not** mark brokerage tradability/verification as VERIFIED;
- ETFs, options, warrants, futures, crypto or other non-equities remain outside TASK-006A.

Do not implement general multi-instrument discovery.

### Required regression tests

Add deterministic tests proving at minimum:

1. supported US equity succeeds;
2. supported HK equity succeeds;
3. US ETF / provider `equity_valid=False` is rejected with no database mutation;
4. HK non-equity / provider `equity_valid=False` is rejected with no database mutation;
5. missing or invalid equity classification is rejected with no database mutation;
6. existing duplicate/idempotent equity-add behavior remains valid.

Adapter tests must prove Futu provider-native classification is mapped truthfully and not inferred from price availability.

## 2. Confirmed defect B — left-truncated earliest D1 week can be emitted as completed W1

### Problem

The reviewed implementation starts the trading-calendar request at the earliest currently available source date. If the bounded D1 history starts midweek, earlier scheduled trading days in that ISO week are outside the calendar query.

`derive_weekly_bars()` then compares source dates only with the truncated calendar rows it was given. A Wednesday-Friday source window can therefore appear to have complete coverage and be emitted as a completed W1 even though Monday/Tuesday were never checked.

This violates truthful coverage and completed-W1 semantics.

### Required remediation

The PAQS input path must ensure the earliest weekly bucket cannot be declared complete unless the calendar coverage includes the complete relevant ISO week.

Preferred smallest remediation:

- when D1 data exists, align the calendar query start to the ISO Monday containing the earliest D1 `session_date`;
- retain existing market-local timezone/calendar semantics;
- if the provider/calendar path cannot establish the complete week, mark/exclude the earliest weekly bucket rather than assuming completeness.

The resulting W1 logic must satisfy:

- a history whose first D1 begins midweek cannot emit that truncated first week as completed when earlier scheduled sessions existed;
- that bucket is `PARTIAL`/otherwise non-completed and excluded from `completed_w1_bars`;
- a legitimate holiday-shortened week still completes correctly when the calendar establishes the true first/final scheduled sessions;
- current partial-week behavior remains correct;
- no future bar is consulted to repair historical coverage.

Do not expand into historical real-market backtesting.

### Required regression tests

Add deterministic tests proving at minimum:

1. first available D1 begins Wednesday while Monday/Tuesday are scheduled -> first W1 is not completed;
2. next fully covered week remains completed;
3. legitimate holiday-shortened week behavior is unchanged;
4. current partial week remains excluded;
5. no-lookahead/future-week finalization behavior remains unchanged.

## 3. Scope and protected boundaries

This remediation must not introduce or alter:

```text
ATR
Pivot
Swing
Key Level
Zone
Range
Base Regime
Breakout / Failed Breakout
Retest
Trigger
Follow-through
Setup
Invalidation
Target
RR
Entry Advisory
Holder Advisory
Quality / Composite Score
Ranking
Paper Portfolio
Backtest
broker account access
broker write capability
```

Do not add a migration.

Do not modify:

- `docs/phases/PHASE_1_PLAN.md`
- `docs/reviews/PHASE_1_INDEPENDENT_REVIEW.md`
- `docs/reviews/PHASE_1_POST_REMEDIATION_REVIEW.md`
- `src/ai_infra_quant/database/migrations/versions/0001_phase1_foundation.py`

If `phase1_remediation_commit.txt` exists locally, leave it untracked, untouched, unstaged and uncommitted.

Do not modify `roadmap/no-live-trading`.

## 4. Validation

Run the full TASK-006A validation required by the parent Task Contract after the focused fixes, including at minimum:

```text
pytest
ruff check
ruff format --check
mypy
application startup / health
```

Also run focused tests for:

- equity classification acceptance/rejection and no-mutation behavior;
- Futu classification mapping;
- left-truncated W1 coverage;
- existing W1 holiday/current-week/no-lookahead cases.

Live OpenD smoke remains environmental evidence and must be reported separately from deterministic tests. A blocked live smoke is not permission to fabricate evidence.

## 5. Completion report and stop condition

Commit and push remediation to the **same TASK-006A task branch**.

Final report must include:

- remediation starting/reviewed HEAD: `355d51fdb92b585a7148579005180e103bc72c3b`;
- final task-branch HEAD SHA;
- authoritative base SHA `2702750dddb9c076d0850ff0ed152964dde3d3f2`;
- exact changed-file list for remediation;
- how defect A was fixed;
- how defect B was fixed;
- exact test/lint/type-check/startup results;
- live/environmental evidence separately identified;
- confirmation that no TASK-006B or broker-write behavior was introduced.

Do not merge.
Do not start TASK-006B.
Stop after pushing TASK-006A remediation.
