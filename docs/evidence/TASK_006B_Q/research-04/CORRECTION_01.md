# Additive correction 01 — canonical partial-day enum

The freeze commit and price/calendar policies are unchanged. The first execution is retained
in study-01, audit-01.json and charts-01; those outputs are preliminary, not the final comparison.
The initial Capture adapter recognized `FULL` and an incorrect `HALF` literal. The protected
domain enum actually defines `FULL`, `MORNING_ONLY`, `AFTERNOON_ONLY`, `UNKNOWN`. All12 captured
early-close rows use `MORNING_ONLY` with explicit09:30–13:00 segments. Treating them as UNKNOWN
was conservative but violated the already frozen instruction to use evidenced actual segments.

The correction recognizes the three documented positive day types without altering their
segments, completeness or availability. UNKNOWN/undocumented types remain ineligible.
No calendar facts are inferred from price presence. Six dedicated schema regressions include
US13:00 close, hypothetical afternoon-only and rejection of undocumented `HALF`.

This is an adapter defect correction, not a second candidate, calendar-policy relaxation or
post-result threshold change. Both executions use exactly the same original source hashes,
scheduled cutoffs, frozen quartet rule and fixed horizons. Final outputs use fresh study-02,
audit-02.json and charts-02 paths; the report gives same-input numerical differences.
