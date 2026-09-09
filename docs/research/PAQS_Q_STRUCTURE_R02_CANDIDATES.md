# PAQS-Q R02 — admissible candidate initialization

Research hypothesis **H1 / QSTR-R02-ELIGIBLE-SEED-1**, frozen after Phase A and before market
comparison. One candidate only. No production authority or return/prediction claim.
[Plan](../evidence/TASK_006B_Q/research-02/EXPERIMENT_PLAN.md).

## Mechanism and full transition definition

Retain the baseline input/quality/version selection and exactly N=W+A legitimate observations;
W1 26+104, D1 60+252, M30 40+160. ATR remains EMA_TR_14 with first TR=H0-L0, arithmetic mean at
index13, alpha=2/15 thereafter. Every ATR step/TR is quantized to 1e-18 using independent
Decimal Context(50, ROUND_HALF_EVEN). All baseline financial/profile parameters remain unchanged.

State is (UNSEEDED/SEEK_HIGH/SEEK_LOW, high-index-or-null, low-index-or-null, previous confirmed
extreme-index-or-null). Start UNSEEDED and all null. Process completed observations in order,
ignoring pivot updates until positive ATR. Equal extremes retain earliest index. Let s be prior
confirmed extreme; **admissible(i) = s is null OR i-s>=2**. In SEEK states only admissible bars may
initialize or improve the sought candidate. UNSEEDED retains the original running high and low.

Update permitted candidate before testing reversal. At i, T=lambda*ATR_i (context-50 product,
no quantum rounding at this comparison). down=(h exists AND h<i AND H_h-C_i>=T),
up=(l exists AND l<i AND C_i-L_l>=T). UNSEEDED emits HIGH on down XOR up when down, LOW when up;
dual or neither emits nothing. SEEK_HIGH emits HIGH on down AND h-s>=2; SEEK_LOW symmetrically.
At most one pivot per bar; emitting sets s=extreme, flips SEEK state and clears the newly sought
candidate. Initialize it from the confirmation bar only if confirmation_index-s>=2. Otherwise
leave null until a later admissible bar. The old candidate of the opposite type is irrelevant.
No output is rewritten after confirmation within this evaluation.

Extremes and confirmations must both be active to enter decision geometry. Warm output can seed
state but cannot supply eligible directional comparisons. Preserve baseline latest-two-high and
latest-two-low label gate, .25 ATR equality, latest-close invalidation and D1 range precedence.
Reuse unchanged zone/range calculations, caps and expiry. There is no threshold relaxation, forced
pivot, vote, retry, persistent history, hysteresis or additional model.

## Semantic cost and evidence

Baseline hands the opposite candidate the confirmation bar even if it is only one bar after the
prior extreme. A lower low there can remain selected forever while failing the separation gate.
H1 instead defines the candidate extremum over the *admissible* post-pivot domain. A lower low or
higher high at s+1 is omitted from that domain. This is an explicit candidate semantic revision,
not a correction to source prices, an assertion that the omitted price did not happen, or relabelling
baseline Regime. The output includes source-backed exact candidate extrema; no fabricated prices.

Hand oracle with constant diagnostic ATR=1 and lambda=1: high110 at i0, close108/low90 at i1
confirms HIGH0. Low90 at i1 is ineligible relative to extreme0. At i2 low95/close96 initializes
eligible low2 (cannot confirm same-bar). At i3 close97 confirms LOW2, distance2>=1, separation2.
Baseline remains locked on LOW1 and emits no LOW. Constant ATR is a pivot-unit oracle, not a
replacement ATR convention in normal calculations. Mirrored price case must be symmetric.

Flat zero ATR emits no pivot and remains UNCERTAIN. Monotone sequences need not provide two-sided
history and remain UNCERTAIN. Alternating input must still respect separation and confirmation;
equalities keep earliest admissible extreme. Gaps cannot bypass same-bar confirmation or infer
intrabar order. A wide initial bar making both predicates true stays UNSEEDED; H1 does not decide
which extreme came first. Incomplete and unavailable bars are excluded before prices are interpreted.
Missing/invalid quality fails or stays conservative under accepted F01 policy.

## Identity, boundedness and failure modes

Normal evaluation consumes only the selected last N, no external close/seed. Thus arbitrary older
valid observations cannot affect candidate state or financial results. Parsing cost may depend on
supplied history; calculation memory is O(N). Pivot processing is O(N); unchanged bounded D1 zone
clustering/range comparison cost is separately counted. Identical bounded observations/config/cutoff
produce identical bytes across processes and surrounding Decimal contexts.

Candidate result rule is QSTR-R02-ELIGIBLE-SEED-1; config identity hashes that version, unchanged
parameter record and W/A. Pivot identity likewise includes the candidate version/config and actual
kind/price/extreme/confirmation refs. Canonical decimal/UTC/null/array representation and semantic
hash method remain the baseline wire contract. Source provenance stays outside decision identity.
Evidence records exact threshold and minimum separation; algorithm-version hashes are never used
as a proxy for structural disagreement.

Finite memory still moves the ATR seed and initial UNSEEDED domain. H1 does not promise rolling
repaint immunity. Reject robustness if repeatable recent eligible structure loss remains solely
from seed reconstruction, or material effects cannot be explained. Also reject if it manufactures
evidence under flat/ambiguous/insufficient input. Treat improved label coverage only as an observed
consequence. Recommendation is recorded after execution in the separate R02 report; this frozen
hypothesis must not be tuned against held-out inputs.
