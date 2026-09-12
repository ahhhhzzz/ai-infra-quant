# R05 frozen controlled-ablation plan

This file is committed and normally pushed with the complete implementation/tests and
[mathematical specification](../../../research/PAQS_Q_PRIOR_RAW_VETO_ABLATION_R05.md)
before any real AVGO A1 calculation. After GitHub readback, create an additive freeze receipt.
No post-result candidate/metric/cutoff/selection/calculation edits are authorized. If any hard
invariant fails, preserve failure.json and all produced files, mark INVALID and stop.

## Lineage and fixed input

Contract: `0d8ca48b046325c4d03a1716c806d42a333153ec`, direct child of corrected R04
`c4e21a0204cf6cdd7bb139584b02f01792a49f13`. Product authority remains
`8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f`. Substantive R04-F01 PASS:
`2094118f270e209b5b037162813815886678fdbd`; current review head
`56020173b223dcf277ef8f125eeeaaa3fa135bcc` adds formatting only. No review history enters R05.

Use only the three normalized AVGO exports in `D:/AI_Infra_Quant_Codex_v1/task006b-q-data`
and `D:/AI_Infra_Quant_Codex_v1/task006b-q-r04-source/capture-calendar.json`. Verify their
R04 freeze hashes and the exact study-03 source manifest. No DB, OpenD, price service, web research,
LLM, provider, credential or account request. GitHub Git/ref/document operations are delivery
provenance, not research-data acquisition. All research request budgets and actual targets are zero.

The same 100 cutoffs per timeframe in both modes produce 600 scheduled evaluations per arm.
W/A/N and all calendar/quality policies are unchanged. AVGO remains development/current-QFQ/PARTIAL
with unknown historical availability. Keep the fixed40 universe and the missing39; no extra cohort.
The freeze manifest copies all exact cutoff values and enumerates all600 coordinates.

## Execution order and reproducibility

1. Complete and test implementation on synthetic US.TEST/HK.00005 data only. Retained B0 tests
   may read existing AVGO evidence; no A1 AVGO before the push/readback receipt.
2. Freeze exact B0/A1 definitions, mathematical proof, metrics, case rubric, enumeration and code.
   freeze.json contains all new implementation/test/spec/PLAN canonical-LF SHA256 values (excluding
   its own self-hash); the Git commit additionally freezes every mode/type/blob including freeze.json.
3. Re-run unchanged R04 study into fresh baseline-study; compare all21 files with study-03.
   Ignore only actual recognized_at and summary started_at/finished_at/runtime/derived output bytes;
   enumerate every ignored path. All other fields, controls and case content must match exactly.
4. Only after B0 reconciliation, calculate the paired study with the unchanged frozen inputs.
   Each B0 cutoff is again compared against study-03's full census/events/costs and scalar metadata.
   Assert inclusion, exact veto bijection, unchanged non-veto classification, shared endpoint
   components, time bounds and all3 segment conservation equations for both arms.
5. Store full census through explicit catalogs, calendar views, price refs, all event records,
   endpoint mappings, omits/references, dependencies and transitions in six frame files.
   Catalog index is position in census_ids; active begins at active_start. Inventory arrays sort
   POSIX strings explicitly. Writes are exclusive; no old output path is reused.
6. Run the fixed40,000-input synthetic enumeration and render/inspect every selected real case.
   Apply the decision table, preserving qualitative trade-offs and market limitations.

B0 integrity targets: VALID100/100/74, other326 insufficient; W1 segment centers
10400=8479+1921; active PRIOR_RAW_VETO172/939/108. These are reproduction checks, never A1
optimization targets. Zero losses alone and event-count growth do not count as success.

## Deterministic case rubric (maximum15 real cases)

For each available timeframe, among OBSERVATIONAL valid cutoffs only:

1. First added endpoint: smallest (cutoff, extreme index).
2. Most-extreme B0 omission restored by A1: largest absolute price difference from that occurrence's
   latest earlier accepted B0 same-kind reference. Tie: earliest cutoff, then extreme index.
   This is the retained more-extreme comparator, not an outcome or global ground truth.
3. Longest maximal unit-gap alternating chain containing at least one addition: most events,
   then earliest cutoff and first extreme index.
4. First A1-created consecutive same-kind pair: absent from B0 pair-key set, earliest cutoff,
   then first and last extreme indices. A hard invariant anomaly instead makes the run INVALID.
5. One triple-only non-event diagnostic: prefer active over warm, then earliest cutoff/index.

Record zero for absent categories. Deduplicate equal (timeframe,cutoff,focus-first,focus-last),
combine category labels, order stable case IDs. Each image spans focus-first-5 through
focus-last+6, clipped to the selected window: at most312 candles, never after cutoff. Show B0/A1,
extreme and next-bar confirmation separately, prior raw D/U, quartet span, unavailable support
and segment boundaries. UTC ordinal axis does not fill gaps. All used candles and rejected rows
remain in case JSON. Prices are Decimal until drawing. Inspect every selected PNG and record
favorable, ambiguous and noisy structural interpretations, without future-direction labels.

## Decision table and stop

- Integrity violation: INVALID and stop, with all failures retained. No research disposition.
- REJECT_NO_VETO if the valid experiment increases consecutive same-kind rate in any observed
  timeframe, or complete qualitative case review establishes a clear structural failure.
- RECOMMEND_CROSS_SAMPLE_ONLY if all integrity/proof checks pass, every valid timeframe has at
  least one unique restored more-extreme endpoint, no timeframe's same-kind rate increases,
  all added unit-gap chains are disclosed and there are no unexplained/non-veto additions.
  Complete case inspection remains required; a structural-failure finding takes priority.
- Otherwise INCONCLUSIVE. Undefined pair denominators cannot establish non-increase; however
  an observed increase in another timeframe still satisfies the rejection condition.

Qualitative review must cite a selected case and actual baseline/current raw/omission context;
it cannot introduce a new numeric acceptance threshold or claim future outcomes. A repeated-kind
pair or a dense alternating chain is disclosed evidence to assess, not automatically a formal
Swing failure. No-veto does not imply a new alternation promise. Mixed interpretation is reported
as such; event growth alone cannot resolve it.

Strict historical confirmation and broad market applicability remain INCOMPLETE under every
disposition. No product adoption or extra symbol/triple-only experiment follows.

## Validation and preservation

Run retained234 plus at least12 new tests, Ruff, format and native/win32 strict mypy on R05 only;
diff, relative links, 612 original objects and frozen R05 objects. Use an isolated worktree and
keep all old evidence, database and worktrees intact. Old protection scripts remain unchanged.
Matplotlib is reused from the existing separate R04 plot environment without dependency changes.
Use Agg plus a temporary writable cache. No browser/Uvicorn/DB/full-product run is required.
Final report is Chinese, distinguishes implementation validity, structural interpretation,
market applicability and adoption, and reports exact freeze/final lineage. Push R05 only and stop.
