# F1 golden freeze, before the production port

`r05.json` is a self-contained extraction from exact R05
`7487cf57161a834d9100f983bab9d8534a1c0488`. Expected values come only from committed
frame/census/event/cost catalogs. All 14 committed case crops were checked against their
full selected frames. Twelve vectors cover both qualification modes and a retained M30
insufficient cutoff. No production evaluator existed when these expectations were frozen.

Price values are from the existing offline exports whose exact SHA-256 values are pinned
in the committed source manifest; no database or provider was accessed. Calendar values
are from the committed calendar catalog. Each source blob SHA-256 is retained in the fixture.
Retrieval timestamps remain transport provenance, never historical availability.

Golden projection: complete event/census records, reasons/status/strict qualification,
window/calendar hashes and all declared per-window costs. Legacy identities remain lineage;
new framework envelope hashes are tested separately. The historical total-source unknown
availability count and run recognition metadata are not outputs of the bounded new input.

`synthetic.json` freezes a labelled, hand-calculated M30 flat/three-center chain and safety
expectations. Its reversal scale is the previous bar range, coefficient 1. All three centers
are within one session. B0 vetoes the second and third raw centers; A1 retains all three.

Reproduction (requires the original verified offline exports; not needed to run tests):

```text
python tests/paqs_q/freeze_golden.py --root . --frozen-prices <frozen-export-directory>
```

The extractor creates its output exclusively and never rewrites an existing freeze.
