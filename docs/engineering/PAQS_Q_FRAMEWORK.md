# PAQS-Q F1 framework

Status: **FOCUSED REVIEW PASS / USER-ACCEPTED LIMITATION / CLOSED / INTEGRATED**.
The corrected implementation has matching actual Linux/Windows vectors (F1-02 PASS).
F1-12: **USER-ACCEPTED LIMITED EXCEPTION（用户接受的限定例外）**.
The recorded Linux mobile layout FAIL remains unchanged and no longer blocks integration;
Windows is the owner's primary acceptance platform. This is not an all-platform PASS.
External ChatGPT focused review closed F01/F02/F03 with no new findings; it did not re-review
the entire history. See the [F1 closeout decision](../decisions/TASK_006C_Q_F1_CLOSEOUT_2026_09_21.md).
See the [minimal closeout report](../evidence/TASK_006C_Q_F1/closeout-01/REPORT.md).
The obsolete global Q-path prohibition is replaced by product-isolation checks under the
[remediation contract](../../prompts/tasks/TASK-006C-Q-F1_REMEDIATION_01.md).
See the [remediation report](../evidence/TASK_006C_Q_F1/remediation-01/REPORT.md);
the [original report](../reports/TASK_006C_Q_F1_IMPLEMENTATION_REPORT.md) remains historical evidence.

The implementation follows exact handoff `857823a0dc39b4c10a1986c575bcbcd9dda11c85`.
The [frozen contract](../../prompts/tasks/TASK-006C-Q-F1_VERSIONED_QUANT_EVENT_FRAMEWORK_FOUNDATION.md)
remains byte-identical. No existing product implementation is edited.

Planned additive files (repository-relative):

```text
src/ai_infra_quant/core/domain/paqs_q/__init__.py
src/ai_infra_quant/core/domain/paqs_q/canonical.py
src/ai_infra_quant/core/domain/paqs_q/inputs.py
src/ai_infra_quant/core/domain/paqs_q/results.py
src/ai_infra_quant/core/ports/paqs_q.py
src/ai_infra_quant/core/strategy/paqs_q/__init__.py
src/ai_infra_quant/core/strategy/paqs_q/calendar.py
src/ai_infra_quant/core/strategy/paqs_q/qualification.py
src/ai_infra_quant/core/strategy/paqs_q/local.py
src/ai_infra_quant/core/strategy/paqs_q/plugins.py
src/ai_infra_quant/core/strategy/paqs_q/registry.py
src/ai_infra_quant/application/paqs_q_artifacts.py
src/ai_infra_quant/resources/paqs_q/b0.json
src/ai_infra_quant/resources/paqs_q/a1.json
tests/paqs_q/__init__.py
tests/paqs_q/support.py
tests/paqs_q/freeze_golden.py
tests/paqs_q/golden/README.md
tests/paqs_q/golden/r05.json
tests/paqs_q/golden/synthetic.json
tests/paqs_q/golden/canonical.json
tests/paqs_q/test_canonical.py
tests/paqs_q/test_parity.py
tests/paqs_q/test_registry.py
tests/paqs_q/test_boundaries.py
tools/validation/paqs_q_f1.py
docs/engineering/PAQS_Q_FRAMEWORK.md
docs/reports/TASK_006C_Q_F1_IMPLEMENTATION_REPORT.md
```

Current documentation updates: `docs/ROADMAP.md`, `docs/MASTER_SPEC.md`,
`docs/ARCHITECTURE.md`, `docs/STRATEGY_SPEC.md`, `docs/REQUIREMENTS_MATRIX.md`,
and `docs/engineering/PAQS_ENGINEERING_GUIDE.md`. Historical research, contracts,
tests and evidence remain unchanged. Validation receipts are added only under
`docs/evidence/TASK_006C_Q_F1/`.

## Module and identity boundaries

`QInput`, `Bar` and `Fact` are frozen dataclasses. Caller bar/calendar/segment containers are
copied into ordered tuples. `FrozenJSON` stores canonical immutable bytes; `document()` always
returns a detached copy, so a caller cannot mutate stored evidence. Constructors reject malformed
primitive types, unsupported schema/mode and financial floats. A supplied selected input with
duplicate identities, unfinished bars or known future evidence produces INVALID before evaluation;
failure envelopes contain hashes/reason codes, no success payload or future values.

`QInput.security` is the canonical market-prefixed security code (for example `US.AVGO`), with
explicit market/currency/IANA timezone. It does not acquire or modify a persisted Security row.
Optional `snapshot_identity` preserves a supplied SHA-256 exactly. No new Snapshot hash algorithm
or live Snapshot adapter is introduced. All supplied facts, quality and provenance enter `input_hash`.

`bounded_prefix(source, cutoff)` is an optional pure preparer for already supplied larger streams.
It filters unavailable future observations before selecting versions and rejects conflicting ties
or unknown version order. Plugins receive selected canonical inputs; they never silently filter
a malformed canonical input into an apparently successful result. No preparer obtains data.

`Descriptor` freezes ID, semantic version, capabilities/status, supported schemas and lineage.
`Config` binds its schema and fully resolved values; B0/A1 permit only the frozen coefficient and
W/A/N profile, materializing defaults. `Record` separates hashed semantic identity from derived
display fields. `QResult` validates the envelope schema/hash and stores immutable Structure/Event
bytes. Every result binds input, snapshot, explicit cutoff, mode, plugin/config/artifact and status.
Event results additionally bind the exact upstream structure result and plugin binding.

All selected bars must match the input security and timeframe, including rows older than the
calculation window. A mismatch returns INVALID / BAR_IDENTITY_CONFLICT before evaluation.
Record constructors, factories and result decoders share validation of required named fields,
field types and canonical Decimal/instant strings. Named price/calendar support schemas are
closed and version references are verified. Record IDs and ordering are checked when decoding.
`legacy`, Event `evidence`, result `evidence`/`lineage` and `display` are explicitly plugin-owned
canonical objects; their internal semantics are supplied by each plugin's versioned contract,
not inferred as a new production strategy by this framework.

Event invocation checks the supplied Structure's input/as_of/mode/snapshot, original registered
ID/version/code/capability/status/lineage, record integrity and time bounds before plugin code.
It uses the recorded config hash without guessing defaults or rerunning Structure. Missing old
implementations raise the typed selection failure UPSTREAM_IMPLEMENTATION_UNAVAILABLE; they
never fall back to a current implementation. Hash validation establishes identity/integrity,
not authenticity against a malicious party capable of rebuilding all hashes.

The public stage protocols live in `core/ports/paqs_q.py`; the registry imports no concrete strategy.
The existing package initializers import retained domain/port definitions, which are included in
the artifact closure without changing or invoking their PAQS-E/broker behavior. The concrete
B0/A1 adapter is pure. Artifact filesystem verification is confined to the new application loader.

## Explicit use

```python
from pathlib import Path
from ai_infra_quant.application.paqs_q_artifacts import load_registry

# q_input is an explicitly constructed, immutable QInput. Default mode is AS_OF.
registry = load_registry(Path("/path/to/verified/source-tree"))
b0 = registry.structure(q_input)
event_status = registry.event(q_input, b0)
# event_status: UNAVAILABLE / EVENT_PLUGIN_NOT_CONFIGURED

experimental = load_registry(Path("/path/to/verified/source-tree"), include_experimental=True)
a1 = experimental.structure(
    q_input, "paqs-q-structure-a1", "0.1.0", allow_experimental=True
)
```

The default registry has only B0 `1.0.0`; its Event registry is empty. Adding A1 to an explicit
inventory does not authorize execution. Both exact ID/version and per-call experimental permission
are required, with rejection before plugin invocation. Permission does not mutate the registry or
contaminate later B0 calls. Unknown, duplicate, conflicting, disabled and incompatible bindings fail
with typed `SelectionError` codes. No latest-version resolution or automatic promotion exists.

`historical_binding_status` returns UNAVAILABLE if the exact implementation is not loaded, including
when a descriptor merely exists in an allowlist. Old canonical results remain unchanged. F1 provides
no persistent history store or automatic migration/reinterpretation of old results.

## Canonical bytes and artifact verification

The contract's `C` and `H(tag, value)` are implemented literally: sorted ASCII schema keys;
compact UTF-8 JSON with ASCII escapes and no BOM/final newline; finite exact Decimal strings;
six-digit UTC instants; ordered arrays and sorted set-like fields. Float and duplicate JSON keys
are rejected. Decimal spelling/ambient precision and host dictionary order do not affect identity.
Snapshot identity is passed through; legacy digests use their original Unicode policy only for
research lineage. New framework hashes always use `paqs-q-canonical-v1` and the prescribed domains.

The two checked-in artifact manifests have the exact `artifact_schema_version/entrypoint/files`
schema. Each of 34 explicitly listed files has a repo-relative POSIX path, `utf8-lf` encoding and
SHA-256. Source text normalizes CRLF/CR to LF without discarding other whitespace; binary hashing
is exact. Both manifests cover the full implementation/import closure, including unchanged parent
initializers and their retained pure domain/port imports. Manifest files exclude themselves.
The entrypoint distinguishes the B0/A1 artifact hashes.

Loading verifies schema, inventory, every content hash, path containment, no symlinks and the active
package's source identity. A different verified tree cannot label the currently imported code as
an old version. Absolute filesystem locations are verification locations only, never hash inputs.
The loader also supports an explicitly supplied unpacked package root via `wheel=True` (logical
`src/` paths map to the package root). Tests actually pack/unpack a portable source ZIP in that
layout, including CRLF manifests. No wheel build or distribution installation is claimed.

After an authorized implementation change, regenerate manifests explicitly:

```text
python tools/validation/paqs_q_f1.py --write-artifacts
```

Never regenerate historical artifact bindings as a way to relabel old results. Release/registration
changes require a new explicit semantic version when semantics change; duplicate same-version
content conflicts are rejected. The current reference plugin versions are frozen by the F1 contract.

## B0/A1 parity and qualification

The port extracts only price/window qualification, calendar certificates, raw inequalities, local
acceptance and per-window costs from pinned R04/R05. It does not import research modules or include
study orchestration, scoring, ATR, smoothing, market selection or parameter optimization. The sole
arm condition is whether prior raw veto applies; both preserve the j-2..j+1 quartet and next-bar
confirmation. Arithmetic uses local precision 50/HALF_EVEN and the inherited 18-place quantization.

The [golden freeze](../../tests/paqs_q/golden/README.md) predates the port. All legacy events,
census rows, rejections, support/calendar hashes and declared per-window costs match. New record
IDs intentionally differ from legacy event IDs and retain those IDs as lineage. Empty valid output
is distinguished from insufficient data. No complete active calendar support yields INSUFFICIENT;
this explicit framework gate never turns missing support into a successful empty event set.

AS_OF is default and never falls back automatically. Current QFQ, unknown required price/calendar
availability or insufficient strict completeness cannot certify historical structure. Explicit
OBSERVATIONAL retains quality, unknown availability and `strict_confirmation=false`. Retrieval
time is transport provenance, not historical availability. W1 nominal interval end remains geometry;
factual completion and known availability are cutoff-bounded. HK lunch/overnight boundaries,
missing sessions/buckets, early closes and DST follow the frozen calendar rules.

## Adding a later Event plugin

A separately approved versioned contract first defines that plugin's semantics, config/evidence
schema, exact descriptor, capabilities and implementation artifact. Implement the Event protocol,
declare compatible Structure schema/capabilities, then explicitly allowlist/register that immutable
binding. Generic orchestration needs no B0/A1-specific branch. Results bind their upstream hash and
are checked for binding/record integrity and known future evidence. New schemas need new versions.

F1 Event fixtures live only in tests and require a test-only registry; default production rejects
their `TEST_ONLY` capability. They prove replacement and upstream binding, not a production strategy.
Formal Breakout/Failed Break/Retest/Transition/Trigger/Follow-through remain unimplemented.
`Event != Setup != Advisory`; no Entry/Hold/Exit, position, PnL, backtest, account or order semantics
are added. There is no Dashboard/API/Analyze/PAQS-E/database integration.

## Reproducing validation

Use Python 3.12 and the repository's existing pinned dependencies. Set `PYTHONPATH` to `src` and
the repository root; Windows separates entries with `;`, Linux with `:`. The report gives exact
test commands and omissions. No command targets the user's database.

```text
python -m pytest tests/paqs_q -ra
python tools/validation/paqs_q_f1.py --vectors <new-output-path>
```

The vector digest covers 28 B0/A1 outputs (12 frozen inputs plus 2 synthetic inputs), canonical
bytes hashes, record IDs, result hashes and input identities. Compare `vectors`, `code_hashes` and
`vector_digest` across actual OS executions; platform labels are operational receipt metadata.
An actual run is required on both operating systems; `mypy --platform win32` is not Windows
execution. The minimal closeout report records the corrected artifact's fresh Windows run and
matching Linux vectors. Pre-remediation receipts remain historical; they did not close this gate.
The recorded Linux mobile browser failure is a user-accepted limited F1-12 exception;
its historical FAIL is preserved and is not an all-platform test PASS.
Both original protection tools remain unchanged historical evidence. To reproduce remediation
protection and its Windows comparison, check out `8a87150685c123bcf9e67288d81ac50a0697a54b` and run
`python docs/evidence/TASK_006C_Q_F1/remediation-01/verify.py --windows <new-output-path>`.
That verifier's closed scope predates the closeout files; it is not a validator for this later
documentation-only addition. The closeout report links the separate document/object checks.
