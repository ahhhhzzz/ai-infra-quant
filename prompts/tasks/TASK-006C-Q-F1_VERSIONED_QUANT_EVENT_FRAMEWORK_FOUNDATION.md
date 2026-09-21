# TASK-006C-Q-F1 — Versioned Quant/Event Framework Foundation

Contract status: **OWNER-APPROVED / READY FOR IMPLEMENTATION**.

Delivery status at freeze: **AUTHORIZED / CONTRACT FROZEN / IMPLEMENTATION NOT STARTED**.
Owner authorization: explicit 2026-09-21 R05 independent closeout and framework handoff request.
Repository: `ahhhhzzz/ai-infra-quant`.

## 1. Authority, exact starting record and objective

Read AGENTS, ROADMAP, MASTER_SPEC, ARCHITECTURE, STRATEGY_SPEC, engineering guide,
the [R05 independent review](../../docs/reviews/TASK_006B_Q_R05_INDEPENDENT_REVIEW.md) and
[Owner closeout decision](../../docs/decisions/TASK_006B_Q_CLOSEOUT_AND_006C_Q_HANDOFF_2026_09_21.md).
Research anchors are exact:

| Anchor | SHA |
|---|---|
| Product authority roadmap/no-live-trading | `8bf55f1ea5e7b3e9e65517ca9b5a505086bb761f` |
| Reviewed R05 | `7487cf57161a834d9100f983bab9d8534a1c0488` |
| R05 frozen implementation/PLAN | `b10e87cbb324442d1fc744d5fa94522802f870c1` |
| R05 contract | `0d8ca48b046325c4d03a1716c806d42a333153ec` |
| Corrected R04 / B0 study-03 | `c4e21a0204cf6cdd7bb139584b02f01792a49f13` |

The later implementation run starts from the exact final handoff SHA supplied by the verified
delivery of `integration/006b-q-closeout-006c-q-f1-handoff`, including this frozen contract and
the PASS review. Fetch and verify that exact SHA, its ancestry and contract blob; do not substitute
a moving branch head or an inferred future commit. Use a new isolated F1 task branch/worktree.
This contract does not authorize implementation during the closeout run, integration into the
authority branch, force-push or modification of any historical branch/evidence.

Objective: create a replaceable, versioned, deterministic, traceable PAQS-Q engineering foundation.
Do not attempt to finish the final Event strategy in one task. 006B-Q is **REVIEWED / CLOSED AS
REFERENCE RESEARCH**. Do not reopen R06 because cross-equity validation is incomplete. Keep
`RECOMMEND_CROSS_SAMPLE_ONLY` as an optional future research recommendation; strict historical
confirmation and broad market applicability remain **INCOMPLETE**. F1 needs no profitability
proof, parameter search, full-market validation or final strategy definition.

## 2. Frozen architecture

```text
Canonical PAQS Input / Snapshot Identity
        ↓
Versioned Structure Plugin
        ↓
Immutable Structure Result
        ↓
Versioned Event Plugin
        ↓
Immutable Event Result + Evidence
```

Use pure typed protocols and immutable domain values in the existing modular monolith. An
optional `PaqsQStrategyPlugin` composition layer may select and bind the two stages. It must not
embed B0/A1 special cases in generic orchestration or make a concrete strategy the framework core.
Dependency direction is caller → registry/protocol → concrete pure plugin; each plugin consumes
canonical facts. Production core must not import `tools/research/...`, providers, databases,
network clients, OpenD, LLMs or provider SDKs, or read environment variables. Artifact loading and
verification belong outside the pure evaluation core and pass immutable verified values inward.
There is no dynamic module discovery, arbitrary import path, eval or network plugin installation.

## 3. Immutable contracts and explicit statuses

Input must carry schema version, canonical Security/market/currency/timezone, timeframe, exact
`as_of`, qualification mode, completed bar versions, calendar/session facts and versions, quality,
coverage, adjustment and availability provenance. Bind both an existing snapshot identity when
provided and the canonical Q-input content hash. Preserve the existing Snapshot hash algorithm;
never reinterpret or recompute it with the new Q serializer. The Q-input hash covers every fact
consumed by a plugin, including qualification/calendar/negative support evidence and ordering.
Explicit supplied input is supported without live Snapshot acquisition or database reads.

Structure and Event results must be recursively immutable: frozen records with tuples/immutable
values, no mutable nested dict/list aliases. Constructors validate and defensively freeze caller
inputs. Evidence contains source/version references, ordered support, extreme/confirmation and
availability times, reason codes and lineage. Result envelopes bind:

- `schema_version`, `strategy_id`, `strategy_version`, `config_hash`, `code_hash`;
- input/snapshot identity, `as_of`, qualification mode;
- plugin capability and plugin status, including experimental/reference designation;
- result status, sorted reason codes, payload/evidence and `canonical_result_hash`.

Event results additionally bind the exact upstream structure canonical result hash and structure
plugin binding. Optional composition identity must include both bindings; changing either must
not appear to be the same strategy execution. Event plugins declare compatible input/result
schema versions and required capabilities; unsupported combinations fail closed before evaluation.

Separate plugin status (`REFERENCE`, `EXPERIMENTAL`, `DISABLED`) from result status
(`AVAILABLE`, `INSUFFICIENT`, `UNAVAILABLE`, `INVALID`) and qualification mode. Insufficient bars
or unknown required availability → `INSUFFICIENT`; absent/disabled required capability →
`UNAVAILABLE`; malformed/conflicting input, mismatched identity or forbidden future evidence →
`INVALID`. Return explicit stable reason codes and no success payload for these states. A genuine
valid zero-event result may be `AVAILABLE` with an empty tuple only after eligibility checks pass;
it cannot stand for missing data. Registry selection errors are typed failures, not fabricated results.

## 4. Canonical serialization and SHA-256 preimages (paqs-q-canonical-v1)

This section is normative; no Python repr, object address, wall clock, random value, OS path,
unordered iteration, float conversion or unstable source introspection may affect identity.

`C(x)` is exactly the UTF-8 encoding of canonical JSON, with no BOM, whitespace padding or final
newline. Object keys are unique ASCII schema keys sorted lexicographically by code point. Values
are null, Boolean, signed base-10 integers, strings, arrays or objects. No JSON floating number,
NaN or Infinity is allowed. Strings preserve code points (no implicit Unicode normalization),
reject unpaired surrogates, escape quote/backslash and controls according to JSON, use the short
escapes for backspace/formfeed/newline/carriage-return/tab, and lowercase `\uXXXX` for remaining
controls and every non-ASCII code point (surrogate pairs for supplementary characters). Slash is
not escaped. This corresponds to validated `json.dumps(..., ensure_ascii=True, sort_keys=True,
separators=(",", ":"), allow_nan=False).encode("utf-8")`; validation rejects float before dumping.
Integers use no leading plus/zeros; zero is `0`. Booleans are not accepted as integer fields.

Schema-governed conversions before C:

| Domain value | Canonical form |
|---|---|
| Decimal financial/config value | JSON string in fixed notation, all exact digits retained, no exponent/leading plus, remove fractional trailing zeros and then redundant decimal point; any signed zero → `"0"`. Do not call context-sensitive normalization or round while serializing. Reject non-finite values and float input. |
| Instant | Require aware datetime; convert instant to UTC and emit exactly `YYYY-MM-DDTHH:MM:SS.ffffffZ` (six fractional digits). Reject naive datetime. |
| Market date | `YYYY-MM-DD`, distinct from an instant |
| Timezone / enum | Explicit IANA name / frozen enum value string; never repr |
| Hash | Exactly 64 lowercase hex characters for SHA-256 |
| Ordered facts/support | Array preserving explicitly defined semantic order |
| Set-like reasons/capabilities | Deduplicate, lexicographically sort canonical strings, then array |

Bars are ordered by `(security_id, timeframe, start_utc, completed_at, version_ref)`; version
selection occurs before this order, and duplicate/conflicting logical selected bar identities are
rejected, never arbitrarily resolved by sorting. Calendar facts sort by market/date/version ref;
session segments retain chronological order. Structure records sort by
`(extreme_time, confirmation_time, kind, extreme_ref, confirmation_ref, record_id)`.
Event records sort by `(effective_at, event_type, record_id)`. Every protocol must freeze these
named fields; explicit nulls are retained for nullable fields, required missing fields rejected,
unknown fields rejected under v1. Optional future schemas require new versions, not silent omission.
Stable IDs must be computable before the final tie-break order; no index or container order enters IDs.

Define `H(tag, x) = lowerhex(SHA256(ASCII(tag) || 0x00 || C(x)))`. Tags contain no NUL.
Preimages are exactly:

- `config_hash = H("paqs-q/config/v1", {"config_schema_version": v, "values": fully_resolved_config})`.
  Explicit defaults are materialized; Decimal-equivalent spellings share a hash. A changed effective
  config must change this hash. Unknown keys and unsupported values fail closed.
- `input_hash = H("paqs-q/input/v1", canonical_input_payload)` covering the complete normalized
  input above, excluding only its own `input_hash`. Snapshot identity is included if supplied.
- `code_hash = H("paqs-q/implementation/v1", artifact_manifest)` as defined below.
- `binding_hash = H("paqs-q/binding/v1", {"strategy_id": id, "strategy_version": version,
  "config_hash": config_hash, "code_hash": code_hash, "capabilities": capabilities,
  "plugin_status": status})`.
- `record_id = H("paqs-q/record/v1", {"record_schema_version": v, "binding_hash": binding_hash,
  "input_hash": input_hash, "as_of": as_of, "record": identity_payload})`. Identity payload
  includes record type, semantic endpoints and ordered support refs/values, excluding `record_id`
  and derived sequence/display fields. Event identity payload also includes upstream structure hash.
- `canonical_result_hash = H("paqs-q/result/v1", result_payload)`. The payload includes all
  envelope, input, plugin, status/reason, payload/evidence and upstream fields specified above,
  excluding only its own `canonical_result_hash`. Final output bytes are `C(result_envelope)`
  with that hash inserted. Failure envelopes use the same deterministic rules.

No recursive self-hash: item IDs precede result hashing; Event binds an already finalized Structure
hash. Operational timestamps, runtime duration, host paths and log IDs belong to an external run
log, never the canonical result. `as_of` is explicit input, not an execution-clock default.

Implementation artifact manifest schema is
`{"artifact_schema_version":"paqs-q-implementation-v1","entrypoint":logical_name,"files":[...]}`.
Each file entry is exactly `{"path":repo_relative_posix_path,"encoding":encoding,"sha256":content_sha256}`;
`encoding` is explicitly `utf8-lf` or `binary`, fixed by the versioned artifact inventory; file array
sorts by path, with no duplicate, absolute path, drive, backslash, traversal or symlink. Text content
is UTF-8 without BOM, with CRLF and CR normalized to LF before plain SHA-256; all other bytes,
including final newline and trailing spaces, remain meaningful. Binary resources hash exact bytes.
Do not infer encoding from the host or heuristics. The closed explicit inventory covers the
concrete plugin and all project-owned transitive pure
algorithm/qualification/serialization helpers and resources that can affect its result. It excludes
the manifest itself to avoid recursion. Tests must verify inventory closure and content hashes from
a packaged artifact; editing an included implementation byte invalidates verification or produces a
new code hash. A bare Git HEAD, a handwritten version string or `inspect.getsource()` is insufficient.
Dependency/runtime requirements are pinned and reported in validation; OS-specific paths/bytecode
and `.pyc` files never enter this portable source-artifact identity. No new dependency is required.

Changing effective config changes config/binding/result hashes. Changing strategy version changes
binding/result hashes; changing an implementation artifact changes code/binding/result hashes.
It need not change the independent input hash. Test exact fixed expected preimages and digests,
Unicode/escaping, signed zeros, Decimal context independence and LF/CRLF equivalence on both OSes.

## 5. B0 / A1 adoption and compatibility

Initial structure plugin bindings are explicit, with no latest-version resolution:

| Plugin | strategy_id | strategy_version | Capability/status | Default |
|---|---|---|---|---|
| B0 | `paqs-q-structure-b0` | `1.0.0` | `LOCAL_STRUCTURE_CERTIFICATE` / `REFERENCE` | Enabled |
| A1 | `paqs-q-structure-a1` | `0.1.0` | `LOCAL_STRUCTURE_CERTIFICATE` / `EXPERIMENTAL` | Disabled |

B0 lineage is corrected R04 `PROPOSED_SEMANTICS:R04-CALENDAR-LOCAL-1` at the pinned baseline;
A1 lineage is `PROPOSED_SEMANTICS:R05-NO-PRIOR-RAW-VETO-4SUPPORT-1` at the pinned freeze, reviewed
at the exact R05 head. Descriptors retain these research rule IDs, SHAs and golden-vector origins.
The new framework semantic versions identify adaptations; they do not relabel the original evidence.
B0 is a stable reference plugin, not the unique/final correct market definition. A1 is never
automatically preferred because it produces more events.

Use the exact four-observation j-2..j+1 domain, R04 calendar/quality/availability policy, strict
neighbor D/U and XOR, next-bar confirmation, coefficient 1, and W/A/N 26/104/130, 60/252/312,
40/160/200. B0 retains prior-raw veto; A1 removes only that conjunct, preserving the quartet.
No ATR, smoothing, alternation, spacing, parameter tuning or three-support candidate is authorized.
Financial arithmetic retains the inherited local Decimal context (precision 50, HALF_EVEN,
18-place quantization where the source semantics quantize); serialization never rounds further.

Port the smallest pure algorithm/support slice with tests or use a clear production-owned pure
adapter. Production must not import research modules; existing research files remain untouched.
Freeze explicit golden vectors before implementing the port: use committed R05 case JSON plus
their pinned full-frame rows/support catalogs for self-contained price/calendar facts, and
labelled synthetic edge cases. Do not access the user database or fetch new prices to build them.
Golden expectations must be derived from the pinned evidence, not from the new port itself.
Compare all semantic fields: statuses/reasons, exact prices/endpoints, support/calendar identity,
rejections and declared metrics. Preserve legacy endpoint/support/event identifiers as lineage
fields for exact comparison; new envelope IDs/hashes intentionally follow section 4 and must not
be falsely equated to the legacy envelope. Test B0 parity and A1's sole permitted veto difference.

Plugin versions follow explicit immutable semantic versions. A semantic change requires a new
version; changed code at the same registered `(strategy_id, strategy_version)` conflicts and is
rejected. Never overwrite a registry binding or reinterpret old results. Old result verification
uses its original schema/version/artifact; unavailable old implementation produces UNAVAILABLE,
not fallback to the current plugin. No historical result is rewritten by an upgrade.

## 6. Registry and Event interface scope

The default production registry can select only B0 structure v1.0.0; it contains no selectable
production Event strategy. A1 requires both explicit ID/version selection and
`allow_experimental=True` on that call. Missing either fails closed before invocation. Registry
construction must not enable experimental selection globally as a side effect of another call.
Unknown ID/version, duplicate registration (even identical), disabled entry, version/content
conflict and capability/schema incompatibility are rejected with deterministic typed reason codes.

Deliver an Event plugin protocol consuming immutable canonical input plus the immutable Structure
result and explicit descriptor/config binding, returning immutable Event result/evidence.
Use test-only fixture event plugins to prove registration, swap and upstream binding. They live
only in tests, carry `TEST_ONLY` capability, and cannot enter the default production registry.
Without a production Event plugin, report `UNAVAILABLE / EVENT_PLUGIN_NOT_CONFIGURED` when that
stage is explicitly requested. Do not pretend an empty available event engine exists.

F1 does not require production Breakout, Failed Break, Retest, Transition, Trigger or Follow-through.
Their formal semantics must come through subsequent independent versioned plugin contracts, using
the protocol instead of changing the framework core. `Event != Setup != Advisory`.

## 7. Time and deterministic safety

Only completed bars are eligible; quotes and unfinished candles cannot confirm structure/events.
The explicit `as_of` bounds completed_at, confirmation and every known price/calendar availability
time. Future evidence in a supplied canonical input is rejected as INVALID before it can enter
result evidence. Temporal error results identify reason codes without embedding future values.
If an external pure preparer filters a larger source stream, tests must show its selected prefix
is unchanged by post-cutoff injection; the plugin always receives that already bounded input.
Do not assert identical result hashes for different snapshot/input identities.

Default qualification mode is strict `AS_OF`. Unknown required historical availability, current-QFQ
or insufficient completeness cannot become strict confirmation. The explicit `OBSERVATIONAL`
research mode may reproduce frozen evidence but must retain `strict_confirmation=false`, quality,
adjustment and unknown availability; it is never an automatic fallback from AS_OF. Mode is hashed.
Aware UTC instants coexist with explicit IANA market timezone/session dates. Preserve factual W1
completion separately from future nominal interval geometry; a nominal week end is not evidence
that a future price was consumed. HK lunch, overnight, DST and early closes retain frozen policy.

Same canonical input, plugin binding, version, resolved config and as_of must produce byte-identical
canonical results/IDs/hashes regardless of repetition, host OS, hash seed, dict insertion order
or ambient Decimal context. No hidden mutable plugin state, clock, RNG, provider/DB/network I/O,
environment read or current-working-directory dependency is allowed in evaluation.

No Entry/Hold/Exit, position sizing, PnL, win rate, orders or execution semantics. Read-only and
no-broker/no-live/no-automatic-trading are permanent boundaries.

## 8. Permitted future implementation and exclusions

F1 includes plugin protocols, explicit allowlist registry, immutable input/output/evidence models,
canonical serialization/hashing/artifact verification, B0 reference plugin, gated A1 experimental
plugin, Event interface, necessary focused tests, developer documentation and implementation report.
Prefer additive dedicated `paqs_q` modules beneath existing core/domain, core/ports and
core/strategy, with build-time artifact resources under a separate `resources/paqs_q` area and
focused tests. State the exact planned file set before implementation. Do not modify the accepted
legacy `paqs_structure.py` runtime, research sources or historical evidence to simplify the port.

Explicitly excluded: Dashboard/API wiring, database/migrations/persistence, PAQS-E resources or
semantics, Narrative/Analyze, 007D, Setup/Risk/Advisory, Paper, parameter optimization, return
backtesting, market ranking, user database access, new stocks, R06 and any live/account/trading
capability. The registry is an internal pure foundation, not user-uploaded executable strategies.

## 9. Required acceptance and validation

| Gate | Required observable evidence |
|---|---|
| F1-01 | Repeated execution has identical canonical bytes, stable IDs and hashes; independent fixed expected hash vectors, not only self-comparison. |
| F1-02 | Actual Linux and Windows executions produce the same canonical vector hashes; report both runs. A mypy platform switch alone does not satisfy this gate. |
| F1-03 | B0 exactly matches the frozen semantic golden projection, including failures/support; A1 matches the approved sole intervention with separate lineage. |
| F1-04 | Default registry selects B0 only. No selectable production Event fixture or A1 exists by default. |
| F1-05 | A1 fails closed if either explicit ID/version selection or experimental permission is missing; plugin is not called. |
| F1-06 | Explicitly permitted A1 carries its own binding and does not mutate/contaminate B0 inputs, registry or results. |
| F1-07 | Unknown/duplicate/disabled/version-conflict/schema-incompatible registrations or selections are rejected. |
| F1-08 | Config/version/artifact mutations alter the corresponding hashes; artifact tampering or incomplete dependency inventory is detected. Old results retain original bindings. |
| F1-09 | Post-cutoff data cannot enter evidence; prefix preparation, future price/calendar revisions, unknown availability, unfinished bars and W1 geometry boundaries are tested. |
| F1-10 | Insufficient/unavailable/invalid input yields explicit status/reason codes, distinct from valid zero events. |
| F1-11 | AST/import and executable boundary tests establish no provider, DB, network, environment, clock or RNG dependence in core evaluation. |
| F1-12 | PAQS-E, 006B1, database/migrations and Dashboard regressions remain unchanged; product/protected blob checks and appropriate retained regression suites pass. |

Also prove Event fixture swapping through only the protocol, upstream-hash mismatch rejection,
recursive immutability, no alias mutation, stable input ordering and Decimal/UTC/Unicode canonical
edge cases. Keep original 268 research/input tests unchanged and passing. Run new focused tests,
appropriate retained PAQS-E/006B1/database/Dashboard regression suites against isolated synthetic
temporary resources only, Ruff check/format, native and win32 strict mypy, diff/link/protection
checks. Do not run migrations or tests against the user's database. Record exact commands,
versions, counts, warnings, tested SHA, OS evidence and omissions; do not claim unexecuted gates.

Document the immutable schema, registry use, artifact inventory, B0/A1 lineage, golden projection,
status/time rules and how to add a later plugin without editing the core. The implementation report
must distinguish framework completion from event-strategy or market validation and list every
changed path and protected runtime identity. No new Mermaid diagram is required.

## 10. Stop conditions

Freeze this contract as documentation only in the present handoff. A future F1 implementer must
stop after its bounded implementation/report/validation for independent review. Missing input or
an implementation-affecting contract conflict must be reported, never solved by silently loosening
time/quality/canonical gates or expanding strategy scope. Failure to obtain market validation is
not authority to reopen R06 and does not change this foundation's approved objective.

No automatic strategy upgrade, source-history rewrite, merge into roadmap/no-live-trading, Setup,
Risk, Advisory, Paper, backtest or live work is authorized by an F1 PASS. Further production event
plugins and product integration each require their own approved bounded contract.
