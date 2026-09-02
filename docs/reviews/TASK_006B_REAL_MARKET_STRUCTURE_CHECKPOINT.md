# TASK-006B Real-Market Structure Checkpoint

Checkpoint status: **STRUCTURE_CONCERNS_FOUND**

This is a validation checkpoint, not a human PASS, a profitability study, or a
strict point-in-time backtest. The deterministic implementation remains internally
consistent, but the real-data observations below show material history-origin,
Pivot-density, and parameter-sensitivity questions that require human/project review
before TASK-006C is considered.

## Authority and scope

- Repository: `ahhhhzzz/ai-infra-quant`
- Validation branch: `validation/006b-real-market-structure-checkpoint`
- Starting branch HEAD and checkpoint-contract commit:
  `4352e40c2bdb5fdb596f7378a488b203482ca6da`
- Accepted TASK-006B SHA and verified `roadmap/no-live-trading` HEAD:
  `96747041ef0ff8c00937c5dd5e80cb4c5c28c17c`
- The validation branch was verified to descend from the accepted SHA. Before validation,
  its only delta from that SHA was the checkpoint contract under `prompts/checkpoints/`.
- The work added only this report and
  `tools/validation/task006b_real_market_checkpoint.py`. No product code, migration,
  production default, or normal local database/watchlist was changed.
- `phase1_remediation_commit.txt` remained untracked, untouched, unstaged, and uncommitted.

The validation harness imports the accepted `PaqsInputQueries` path and
`build_structure_snapshot`; it does not copy or reimplement ATR, Pivot, Swing, Zone,
Range, or Base-Regime rules. It uses a fresh temporary SQLite database, applies the
existing migration, and adds NVDA/HK.00700 only to that temporary watchlist.

Reproduce the real-data run from the repository root with:

```powershell
.venv\Scripts\python.exe tools\validation\task006b_real_market_checkpoint.py
```

The harness emits full-precision JSON to stdout. Raw bar dumps are intentionally not
committed.

## Deterministic evidence

Validation performed on 2026-09-02:

| Check | Result |
|---|---|
| Full pytest | `250 passed, 1 skipped in 100.38s` |
| Focused TASK-006B tests | `42 passed in 4.55s` (`test_paqs_structure`, structure API, architecture boundary) |
| Ruff check | `All checks passed!` |
| Ruff format | `128 files already formatted` |
| mypy | `Success: no issues found in 125 source files` |
| Validation-harness mypy (`MYPYPATH=src`) | `Success: no issues found in 1 source file` |
| Fresh migration/startup/health/OpenAPI group | `16 passed in 13.72s` |
| Real D1/M30 no-lookahead audit | 500 sampled cutoffs, **0 violations** |

The no-lookahead audit sampled 50 cutoffs for each of D1 and M30 for every security.
For each cutoff, the engine was rerun with five additional future bars. All earlier
confirmed Micro/Major Pivot IDs, hierarchy, type, price, extreme and confirmation refs,
ATR-at-confirmation, lambda, confirmed flag, and associated Swing labels remained
unchanged.

## Current/live environmental evidence

OpenD was running and reachable at `127.0.0.1:11111`. All five requested equities were
quote-available through the existing Futu quote-only path. The final evidence collection ran from
`2026-09-02T22:47:30.309545+08:00` through
`2026-09-02T22:48:32.519305+08:00`. No trade context, account context, or write API was
created.

Every bundle was labelled:

```text
adjustment_basis = PROVIDER_QFQ_CURRENT
historical_replay_safe = false
```

Every bundle was `PARTIAL` solely because elapsed M30 buckets lacked complete minute
coverage; only `DerivedCoverage.COMPLETE` M30/W1 bars entered structure calculations.

| Security | Live quote | as_of_timestamp | calculated_at | Source coverage: D1 / W1 complete+partial / minute / M30 complete+partial |
|---|---:|---|---|---|
| HK.00700 | 438.2 | 2026-09-02T22:48:22.942226+08:00 | 2026-09-02T22:48:23.014858+08:00 | 1500 / 317+2 / 7282 / 220+33 |
| HK.09698 | 30.24 | 2026-09-02T22:47:59.829524+08:00 | 2026-09-02T22:47:59.911623+08:00 | 1435 / 304+1 / 7282 / 220+33 |
| US.AVGO | 368.725 | 2026-09-02T22:47:36.501839+08:00 | 2026-09-02T22:47:36.569833+08:00 | 1500 / 311+2 / 31679 / 285+3 |
| US.NVDA | 223.67 | 2026-09-02T22:48:13.754986+08:00 | 2026-09-02T22:48:13.845372+08:00 | 1500 / 311+2 / 31679 / 285+3 |
| US.VRT | 257.255 | 2026-09-02T22:47:50.281204+08:00 | 2026-09-02T22:47:50.341001+08:00 | 1500 / 311+2 / 31679 / 285+3 |

All five provenance invariants had `calculated_at >= as_of_timestamp`.

### Current W1/D1/M30 structure smoke

`High`/`Low` show `extreme@price -> confirmation`. `S/R` are confirmed Support and
Resistance Zone counts. All ATRs were ready. The Regime reason is the accepted engine's
explanation, shortened only by omitting stable IDs where the corresponding ref is shown.

| Security / TF | Bars | ATR | Micro / Major | Latest Major High | Latest Major Low | Latest labels | S / R | Active Range (lower..upper; inside) | Base Regime |
|---|---:|---:|---:|---|---|---|---:|---|---|
| HK.00700 W1 | 317 | 35.500615712339993036 | 18 / 25 | 2025-09-28@677.7 -> 2025-10-12 | 2025-04-06@409.2 -> 2025-04-27 | HL,HH,HL,HH | 2 / 4 | none | BULL_TREND (HH/HL; close not below HL) |
| HK.00700 D1 | 1500 | 11.181133575920882213 | 60 / 154 | 2026-08-05@497.8 -> 2026-08-11 | 2026-07-24@432.0 -> 2026-07-29 | LL,HH,HL,EH | 24 / 22 | 391.884715440000000000..475.575873973679418183; 0.80 | RANGE (active-range precedence) |
| HK.00700 M30 | 220 | 1.915632037235505839 | 4 / 20 | 2026-08-31T07:30Z@454.6 -> 2026-09-01T01:30Z | 2026-09-02T02:30Z@435.0 -> 06:00Z | HH,HL,LH,LL | 4 / 2 | none | BEAR_TREND (LH/LL; close not above LH) |
| HK.09698 W1 | 304 | 3.690204631325151088 | 36 / 21 | 2026-05-10@46.34 -> 2026-05-17 | 2026-03-01@35.5 -> 2026-04-19 | HL,HH,HL,EH | 1 / 2 | 16.650312477015713743..47.634200560194792425; 1.00 | RANGE |
| HK.09698 D1 | 1435 | 1.404738940452498570 | 80 / 145 | 2026-03-11@44.32 -> 2026-03-17 | 2026-03-17@39.8 -> 2026-03-18 | EH,LL,LH,HL | 20 / 24 | 25.291182336569467630..36.499184988735627395; 1.00 | RANGE |
| HK.09698 M30 | 220 | 0.215930434821483606 | 15 / 22 | 2026-08-31T07:30Z@32.28 -> 2026-09-01T01:30Z | 2026-09-02T02:00Z@29.92 -> 07:00Z | HH,LL,LH,LL | 3 / 2 | 29.883821537075236096..32.620000000000000000; 0.75 | RANGE |
| US.AVGO W1 | 311 | 39.149042258369331111 | 20 / 10 | 2023-05-29@88.441074928 -> 2023-06-05 | 2022-10-10@39.212359931 -> 2022-11-07 | LL,LH,LL,HH | 1 / 0 | none | UNCERTAIN (HH/LL conflict) |
| US.AVGO D1 | 1500 | 11.581064503720229453 | 5 / 4 | 2020-11-09@35.006304924 -> 2020-11-10 | 2020-10-30@30.609742674 -> 2020-11-04 | LL,HH | 0 / 0 | none | UNCERTAIN (HH/LL conflict) |
| US.AVGO M30 | 285 | 2.576505072189829276 | 15 / 11 | 2026-08-12T13:30Z@426.56 -> 15:00Z | 2026-08-13T13:30Z@411.41 -> 14:00Z | LH,LL,EH,LL | 1 / 1 | none | UNCERTAIN (EH/LL conflict) |
| US.NVDA W1 | 311 | 17.311880861907853243 | 22 / 27 | 2026-05-11@236.264633141 -> 2026-06-01 | 2026-06-29@189.8 -> 2026-08-03 | HH,HL,HH,HL | 3 / 2 | none | BULL_TREND |
| US.NVDA D1 | 1500 | 7.652853440599707939 | 39 / 95 | 2026-08-17@227.92 -> 2026-08-20 | 2026-08-24@207.25 -> 2026-08-27 | LH,EL,HH,HL | 14 / 11 | none | BULL_TREND |
| US.NVDA M30 | 285 | 1.706233317105534185 | 38 / 18 | 2026-08-31T19:30Z@220.825 -> 2026-09-01T13:30Z | 2026-08-31T13:30Z@216.21 -> 14:00Z | LL,HH,HL,LH | 1 / 2 | none | UNCERTAIN (LH/HL conflict) |
| US.VRT W1 | 311 | 41.858833641068592399 | 47 / 24 | 2026-05-11@379.856596613 -> 2026-06-01 | 2025-11-17@148.988885551 -> 2025-12-01 | HL,HH,HL,HH | 3 / 3 | none | BULL_TREND |
| US.VRT D1 | 1500 | 12.463726234653276029 | 90 / 112 | 2026-08-17@300.3 -> 2026-08-19 | 2026-07-29@220.92 -> 2026-08-04 | EL,LH,LL,LH | 13 / 11 | none | BEAR_TREND |
| US.VRT M30 | 285 | 3.252133632006008134 | 32 / 26 | 2026-08-31T19:00Z@259.44 -> 2026-09-01T13:30Z | 2026-09-01T14:00Z@248.75 -> 16:00Z | HH,EL,LH,LL | 3 / 2 | 254.617751230015479283..276.372424472068012114; 0.825 | RANGE |

### Current confirmed Zone geometry

`R` = resistance, `S` = support, and `xN` = independent touch count. These are all
confirmed Zones from the final current snapshots, with full Decimal bounds.

<details>
<summary>All current confirmed Zones</summary>

```text
HK.00700 W1 (6): R[368.574233466785171518,377.595619653214828482]x2; R[390.400000000000000000,401.000000000000000000]x2; R[446.372213760000000000,457.635885560000000000]x2; R[677.700000000000000000,696.304248620000000000]x2; S[262.698010686051171610,271.666528673948828390]x2; S[354.125135416284041102,363.744015023715958898]x2
HK.00700 D1 (46): R[278.800000000000000000,282.630417600000000000]x2; R[303.057292557737026883,305.742707442262973117]x4; R[319.239026320859523158,321.960973679140476842]x2; R[334.200000000000000000,339.237210240000000000]x2; R[349.373860598236196818,353.220513161763803182]x4; R[359.200000000000000000,366.210916800000000000]x2; R[370.769853120000000000,375.800000000000000000]x2; R[379.951108274884719757,383.648891725115280243]x4; R[387.400000000000000000,390.400000000000000000]x2; R[415.046166080000000000,419.471072000000000000]x2; R[421.200000000000000000,426.200000000000000000]x4; R[446.372213760000000000,452.104753160000000000]x2; R[469.624126026320581817,475.575873973679418183]x3; R[495.245745431585418944,500.043074408414581056]x3; R[507.705894169010610460,512.657392550989389540]x3; R[515.700000000000000000,521.200000000000000000]x2; R[520.485717892981226209,523.914282107018773791]x3; R[534.626215295512028087,539.857976824487971913]x4; R[569.196336728729930366,574.435577491270069634]x4; R[615.950000000000000000,619.950000000000000000]x4; R[653.989339116438008383,659.410660883561991617]x3; R[677.700000000000000000,688.929405420000000000]x2; S[228.812712806444754322,232.352409752555245678]x2; S[246.813808262577868517,250.586191737422131483]x2; S[252.211950635441541762,255.188049364558458238]x2; S[258.885957600000000000,264.964539360000000000]x3; S[283.335712906646920959,285.864287093353079041]x3; S[292.274145120000000000,296.833081440000000000]x4; S[305.982241766307563700,309.217758233692436300]x3; S[313.136622479624996307,317.915950480375003693]x2; S[351.000000000000000000,355.000000000000000000]x3; S[354.096462675315400925,356.503537324684599075]x2; S[368.455547699921871258,374.429263620078128742]x2; S[378.356321160000000000,382.200000000000000000]x2; S[391.884715440000000000,397.715284560000000000]x5; S[400.849592920000000000,409.200000000000000000]x2; S[441.593107641438826506,445.838630398561173494]x3; S[452.565680860000000000,459.848338520000000000]x2; S[463.400000000000000000,470.700000000000000000]x2; S[484.300000000000000000,487.700000000000000000]x2; S[486.498381789186748812,492.301618210813251188]x5; S[500.037418103875558840,504.009028036124441160]x2; S[523.046021758611455945,528.571267061388544055]x2; S[537.284192120000000000,546.502746120000000000]x2; S[586.859240028559104879,590.540759971440895121]x5; S[605.114860249983540513,611.774053070016459487]x2
HK.00700 M30 (6): R[456.503118928449125490,457.496881071550874510]x2; R[483.212709965804988270,484.187290034195011730]x2; S[435.000000000000000000,436.000000000000000000]x2; S[437.554055314817689208,438.445944685182310792]x3; S[445.000000000000000000,446.000000000000000000]x2; S[475.400000000000000000,476.400000000000000000]x2
HK.09698 W1 (3): R[41.582373327693910065,43.347626672306089935]x2; R[46.045799439805207575,47.634200560194792425]x3; S[16.650312477015713743,18.149687522984286257]x3
HK.09698 D1 (44): R[7.180000000000000000,7.360000000000000000]x2; R[8.610180101021893188,8.799819898978106812]x2; R[9.034060869478216908,9.155939130521783092]x2; R[10.934303231560119615,11.085696768439880385]x2; R[11.340000000000000000,11.500000000000000000]x2; R[12.073405788832689027,12.246594211167310973]x3; R[13.400000000000000000,13.680000000000000000]x2; R[16.600000000000000000,17.080000000000000000]x2; R[20.850000000000000000,21.400000000000000000]x2; R[23.471363786827647703,23.928636213172352297]x2; R[25.847347814429478362,26.352652185570521638]x3; R[28.155816794344968922,28.644183205655031078]x3; R[29.196985524905934105,29.703014475094065895]x4; R[33.563591958902839034,34.386408041097160966]x2; R[36.000815011264372605,36.499184988735627395]x2; R[37.320095218526515176,37.859904781473484824]x2; R[38.750000000000000000,39.750000000000000000]x2; R[42.041751830548915576,42.888248169451084424]x2; R[43.764083077707827150,44.335916922292172850]x2; R[45.150000000000000000,45.850000000000000000]x3; R[46.196328517314763582,46.803671482685236418]x3; R[47.550000000000000000,48.900000000000000000]x2; R[62.106800289182924284,62.993199710817075716]x2; R[74.450000000000000000,75.500000000000000000]x2; S[5.229409519391150600,5.410590480608849400]x2; S[5.707649830454958319,5.852350169545041681]x2; S[7.225114094978253995,7.374885905021746005]x3; S[9.202608892339943320,9.377391107660056680]x2; S[9.563286794049878164,9.736713205950121836]x5; S[10.252595381769086053,10.527404618230913947]x2; S[16.768406302034415556,17.231593697965584444]x3; S[18.355469351968490016,18.864530648031509984]x4; S[19.201357399219962223,19.638642600780037777]x2; S[21.300000000000000000,21.950000000000000000]x2; S[23.100000000000000000,23.750000000000000000]x2; S[24.050000000000000000,25.000000000000000000]x2; S[25.291182336569467630,25.808817663430532370]x4; S[29.469774450698569662,30.360225549301430338]x2; S[34.777436116019878360,35.422563883980121640]x3; S[36.764587212736353218,37.405412787263646782]x2; S[39.564957448620028157,40.335042551379971843]x3; S[46.550000000000000000,47.650000000000000000]x3; S[65.788076234063636346,66.811923765936363654]x3; S[97.137079295805473003,98.312920704194526997]x2
HK.09698 M30 (5): R[32.460000000000000000,32.620000000000000000]x3; R[33.131517516086376042,33.248482483913623958]x2; S[29.883821537075236096,29.996178462924763904]x2; S[30.911419362217690203,31.088580637782309797]x3; S[31.956228986993788167,32.063771013006211833]x2
US.AVGO W1 (1): S[37.861412461000000000,39.212359931000000000]x2
US.AVGO D1 (0): none
US.AVGO M30 (2): R[426.579565451964864321,427.570434548035135679]x4; S[420.160000000000000000,421.070000000000000000]x2
US.NVDA W1 (5): R[18.688488316194192131,19.280490179805807869]x2; R[47.994501058000000000,49.829925436000000000]x2; S[13.646780932043217004,14.222524034956782996]x2; S[39.066201693340605170,40.323380609659394830]x2; S[86.319525094753428983,90.720016149246571017]x2
US.NVDA D1 (25): R[13.857260196336086469,13.990720152663913531]x2; R[20.649493350643902290,20.815082623356097710]x2; R[47.035970623790359552,47.522740860209640448]x2; R[50.126134943490716924,50.560873504509283076]x3; R[119.962273235000000000,122.718013970000000000]x2; R[140.528375337000000000,143.226083624000000000]x2; R[144.194686603000000000,146.321460501000000000]x2; R[148.161614440622476540,150.122562056377523460]x2; R[151.846520541037013159,153.706584430962986841]x2; R[182.891722294409311558,184.389091748590688442]x2; R[211.919608261000000000,214.390000000000000000]x2; S[12.535414852000000000,12.742329871000000000]x2; S[12.792377908000000000,12.994707382000000000]x2; S[13.289940741690708134,13.455278044309291866]x2; S[39.894708463241530632,40.359946016758469368]x2; S[43.954371706000000000,44.800722914000000000]x2; S[86.498774270000000000,90.540766974000000000]x2; S[100.508829044604558180,102.646322258395441820]x2; S[112.841464796000000000,114.960367092000000000]x2; S[126.670809876000000000,129.316857851000000000]x2; S[131.045563898314910551,132.453302312685089449]x2; S[167.604610799168916413,169.167336042831083587]x2; S[176.534839576000000000,178.682100863000000000]x2; S[188.772829701898179757,191.037170298101820243]x2; S[206.714328489358796249,209.072621316641203751]x2
US.NVDA M30 (3): R[223.630000000000000000,224.150000000000000000]x2; R[227.148820369687459084,227.571179630312540916]x2; S[216.205000000000000000,216.765000000000000000]x4
US.VRT W1 (6): R[15.128885992000000000,15.995100590000000000]x2; R[27.837586467000000000,28.663657142000000000]x2; R[151.937297733921602840,156.947365174078397160]x2; S[9.147997035838628105,9.839028688161371895]x2; S[11.849875297487007186,12.313057040512992814]x2; S[112.022592001000000000,118.570601450000000000]x2
US.VRT D1 (24): R[13.301870145000000000,13.620477813000000000]x3; R[14.866430948000000000,15.128885992000000000]x2; R[15.334743451000000000,15.671514677000000000]x2; R[15.982509349029576363,16.245697569970423637]x2; R[21.329485085394455372,21.556521380605544628]x2; R[22.999491045000000000,23.368842698000000000]x2; R[26.805900344496370090,27.049398588503629910]x2; R[27.661438918301836423,27.854491476698163577]x2; R[115.665764237821102239,116.948309290178897761]x2; R[152.282032166168803023,154.383297615831196977]x3; R[199.667939756008460565,202.923967086991539435]x2; S[9.408432527398157668,9.688114582601842332]x3; S[10.952138593000000000,11.240876792000000000]x2; S[11.907094492000000000,12.255837846000000000]x2; S[12.649419630000000000,12.968327743000000000]x2; S[13.580651855000000000,13.851089585000000000]x2; S[19.129125713912865581,19.427474206087134419]x3; S[22.906039991059339071,23.123922508940660929]x2; S[24.532790448000000000,24.999916387000000000]x2; S[34.475771502000000000,35.362576029000000000]x2; S[53.197767468459849362,55.158603391540150638]x2; S[117.541076422268338001,119.600126477731661999]x3; S[146.789938476779485176,149.953552540220514824]x2; S[271.368363111269593794,276.684850743730406206]x2
US.VRT M30 (5): R[265.580000000000000000,267.045000000000000000]x2; R[275.367575527931987886,276.372424472068012114]x2; S[254.617751230015479283,255.442248769984520717]x3; S[267.520000000000000000,269.190000000000000000]x2; S[285.127211732224580567,286.133788267775419433]x2
```

</details>

The large cumulative D1 Zone sets—46 for HK.00700 and 44 for HK.09698—are themselves
included for human geometry/usability review; the checkpoint does not assert that this
density is desirable.

## Historical current-QFQ prefix replay

This section is **historical current-QFQ replay**, not strict point-in-time reconstruction:

```text
adjustment_basis = PROVIDER_QFQ_CURRENT
historical_replay_safe = false
```

The D1 replay used exactly the most recent 500 completed sessions for every security.
The M30 replay used every legitimate `DerivedCoverage.COMPLETE` regular-session bar in
the current provider minute window. HK lunch was not bridged, incomplete elapsed buckets
were excluded, and US extended-session minutes were not admitted by the accepted input
builder.

Regime fractions are ordered BULL / BEAR / RANGE / UNCERTAIN. All rates and fractions
are descriptive diagnostics, not optimization targets.

| Security / TF | Exact coverage | Bars / replay cutoffs | Micro / Major per 100 | Median Major spacing | Confirmed Zones / median touches | Regime fractions | Changes/100 | Range fraction / median life | No-lookahead |
|---|---|---:|---:|---:|---:|---|---:|---|---:|
| HK.00700 D1 | 2024-08-20..2026-09-02 | 500 / 487 | 12.80 / 9.60 | 8.00 | 14 / 2.00 | .1335/.1725/.2156/.4784 | 7.60 | .2156 / 3.00 | 0/50 |
| HK.00700 M30 | 2026-08-04T01:30Z..2026-09-02T07:30Z | 220 / 207 | 1.82 / 9.09 | 8.00 | 6 / 2.00 | .0676/.0386/.0193/.8744 | 5.80 | .0193 / 4.00 | 0/50 |
| HK.09698 D1 | 2024-08-20..2026-09-02 | 500 / 487 | 10.00 / 8.20 | 7.50 | 12 / 2.00 | .1520/.0719/.4661/.3101 | 9.86 | .4661 / 9.00 | 0/50 |
| HK.09698 M30 | 2026-08-04T01:30Z..2026-09-02T07:30Z | 220 / 207 | 6.82 / 10.00 | 9.00 | 5 / 2.00 | .1449/.1546/.1594/.5411 | 5.80 | .1594 / 4.00 | 0/50 |
| US.AVGO D1 | 2024-09-04..2026-09-01 | 500 / 487 | 4.80 / 3.40 | 7.50 | 4 / 2.50 | .6674/.0062/.0493/.2772 | 2.26 | .0493 / 12.00 | 0/50 |
| US.AVGO M30 | 2026-08-03T15:00Z..2026-09-02T14:00Z | 285 / 272 | 5.26 / 3.86 | 8.50 | 2 / 3.00 | .0919/.0478/.0000/.8603 | 1.47 | .0000 / n/a | 0/50 |
| US.NVDA D1 | 2024-09-04..2026-09-01 | 500 / 487 | 4.80 / 8.00 | 7.00 | 12 / 2.00 | .3368/.1191/.1458/.3984 | 11.91 | .1458 / 2.00 | 0/50 |
| US.NVDA M30 | 2026-08-03T15:00Z..2026-09-02T14:00Z | 285 / 272 | 13.33 / 6.32 | 10.00 | 3 / 2.00 | .0846/.2463/.0515/.6176 | 4.41 | .0515 / 7.00 | 0/50 |
| US.VRT D1 | 2024-09-04..2026-09-01 | 500 / 487 | 6.40 / 7.60 | 10.00 | 7 / 2.00 | .4148/.1602/.0903/.3347 | 4.52 | .0903 / 2.50 | 0/50 |
| US.VRT M30 | 2026-08-03T15:00Z..2026-09-02T14:00Z | 285 / 272 | 11.23 / 9.12 | 9.00 | 5 / 2.00 | .2831/.0993/.0478/.5699 | 6.99 | .0478 / 5.00 | 0/50 |

Total sequential prefix builds were 3,665: 2,435 D1 and 1,230 M30. The 500
no-lookahead comparisons are a sampled independent audit over those timelines.

### Real-data structure concerns

1. **History-origin semantic divergence (AVGO D1).** The same current-QFQ endpoint bar
   produced sharply different terminal structure depending on the available leading
   history. With all 1,500 D1 bars, the latest Major High/Low remained at
   2020-11-09/2020-10-30 and Base Regime was `UNCERTAIN`. With the latest 500 bars, the
   latest Major High/Low were 2025-07-31/2025-06-09 and the terminal regime was
   `BULL_TREND`. This does not violate prefix invariance, because the initial history is
   different, but it is a material operational stability concern.

2. **Major density exceeds Micro density.** On the latest-500/recent-window replays this
   occurred for HK.00700 M30 (4 Micro vs 20 Major), HK.09698 M30 (15 vs 22), NVDA D1
   (24 vs 40), and VRT D1 (32 vs 38). The engines are intentionally independent, so this
   is not asserted to breach the deterministic contract. It is nevertheless contrary to
   the intuitive hierarchy implied by 1.0 ATR Micro versus 1.8 ATR Major and requires
   semantic review.

3. **Stale lower-threshold sequences.** The latest-500 AVGO terminal D1 state at
   2026-09-01 still had its last Micro High at 2025-06-30 and last Major High at
   2025-07-31. VRT human samples in 2026 retained their last three Micro Pivots from
   May 2025 while Major Pivots continued into 2026. This is consistent with the density
   inversion and suggests a directional-change engine can remain path-locked for long
   periods.

4. **Regime churn and short Range lifetimes.** NVDA D1 changed Base Regime 11.91 times
   per 100 replay cutoffs with a median active-Range lifetime of two bars. HK.09698 D1
   changed 9.86 times per 100 cutoffs. These are observations, not TASK-006C transition
   events, but human reviewers should decide whether the stability is usable.

5. **Cumulative Zone load.** Full current D1 snapshots contained 46 confirmed Zones for
   HK.00700 and 44 for HK.09698 across very broad price spans. The complete geometry is
   recorded above so reviewers can assess whether these are useful historical levels or
   excessive structural clutter.

### Stress and boundary mining

| Security | Largest + close move | Largest - close move | Largest opening gap | Highest / lowest ready ATR | Dense Micro cutoff | First near-equal | First candidate / confirmed Zone / active Range | Cutoffs without Range |
|---|---|---|---|---|---|---|---|---:|
| HK.00700 | 2026-06-02 +45.6 | 2025-04-07 -62.4 | 2025-04-07 -56.0 | 2025-03-06 22.557649 / 2024-09-13 6.569879 | 2025-08-27 (40 total) | 2025-01-03 EH | 2024-09-16 / 2024-12-11 / 2025-01-03 | 382 |
| HK.09698 | 2025-02-14 +6.30 | 2025-04-07 -6.51 | 2025-02-21 +4.5 | 2025-03-05 4.441616 / 2024-12-24 .710660 | 2025-07-03 (28) | 2026-02-26 EH | 2024-09-19 / 2024-10-18 / 2024-11-18 | 260 |
| US.AVGO | 2024-12-13 +43.467689 | 2026-06-04 -60.224685 | 2026-06-04 -70.129009 | 2026-06-09 27.870023 / 2024-11-26 4.467249 | 2024-11-11 (10) | 2025-01-27 EH | 2024-10-01 / 2024-11-06 / 2024-12-02 | 463 |
| US.NVDA | 2026-08-27 +18.32 | 2025-01-27 -24.163910 | 2025-01-27 -17.793424 | 2025-04-10 10.104821 / 2025-06-23 3.350077 | 2025-01-15 (9) | 2025-08-29 EH | 2024-10-01 / 2024-12-03 / 2025-01-08 | 416 |
| US.VRT | 2026-02-11 +48.868371 | 2026-07-29 -46.52 | 2026-02-11 +33.615122 | 2026-07-07 24.702878 / 2024-10-14 3.611557 | 2025-01-29 (19) | 2025-12-22 EL | 2024-10-03 / 2025-02-05 / 2025-06-16 | 443 |

## Validation-only small-perturbation sensitivity

For each security, the representative subset was its latest 250 D1 bars; each variant
was compared at 237 cutoffs after warm-up. Defaults were reconstructed immutably and
were not patched. Columns are changed cutoffs for latest Major identity / Zone set or
geometry / active Range / Base Regime.

| Security | Parameter variant | Changed cutoffs (Major / Zone / Range / Regime), out of 237 |
|---|---|---:|
| HK.00700 | major lambda 1.7 | 23 / 235 / 10 / 32 |
| HK.00700 | major lambda 1.9 | 47 / 202 / 0 / 2 |
| HK.00700 | zone epsilon .45 / .55 | 0/0/0/0 / 0/55/43/43 |
| HK.00700 | range ratio .65 / .75 | 0/0/0/0 / 0/0/0/0 |
| HK.09698 | major lambda 1.7 | 24 / 177 / 0 / 6 |
| HK.09698 | major lambda 1.9 | 17 / 206 / 0 / 2 |
| HK.09698 | zone epsilon .45 / .55 | 0/0/0/0 / 0/114/32/3 |
| HK.09698 | range ratio .65 / .75 | 0/0/0/0 / 0/0/0/0 |
| US.AVGO | major lambda 1.7 | 62 / 226 / 35 / 14 |
| US.AVGO | major lambda 1.9 | 51 / 208 / 30 / 15 |
| US.AVGO | zone epsilon .45 / .55 | 0/0/0/0 / 0/132/5/5 |
| US.AVGO | range ratio .65 / .75 | 0/0/2/2 / 0/0/3/3 |
| US.NVDA | major lambda 1.7 | 7 / 10 / 1 / 1 |
| US.NVDA | major lambda 1.9 | 28 / 214 / 0 / 1 |
| US.NVDA | zone epsilon .45 / .55 | 0/0/0/0 / 0/63/2/2 |
| US.NVDA | range ratio .65 / .75 | 0/0/3/3 / 0/0/0/0 |
| US.VRT | major lambda 1.7 | 119 / 235 / 0 / 9 |
| US.VRT | major lambda 1.9 | 79 / 174 / 0 / 2 |
| US.VRT | zone epsilon .45 / .55 | 0/0/0/0 / 0/0/0/0 |
| US.VRT | range ratio .65 / .75 | 0/0/0/0 / 0/0/0/0 |

Across all 1,185 comparisons per variant, major lambda 1.7 changed 235 latest Major
identities, 883 Zone states/geometries, 46 active Ranges, and 62 Base Regimes. Major
lambda 1.9 changed 222/1004/30/22 respectively. Zone epsilon .55 changed 364 Zone
states/geometries, 82 Ranges, and 53 Regimes; epsilon .45 changed none. Range-ratio
changes affected only 5 (.65) and 3 (.75) Range/Regime cutoffs. The asymmetric and high
Zone sensitivity to small Major-lambda changes is another human-review concern; it is
not a parameter recommendation.

## Human-review samples

Selection was deterministic: the end of the longest observed trend run, the end of the
longest active-Range run, the largest absolute close move/opening gap, and the end of the
longest `UNCERTAIN` run. No sample is labelled correct. Values in this section are
rounded only for readability; the harness emits full Decimal values and stable IDs.

Legend: `H/L:extreme@price>confirmation`; `SC/RC` = support/resistance candidate,
`SF/RF` = support/resistance confirmed; Zone suffix `xN` is touch count. Four nearest
Zones are shown. Reviewer questions are, respectively: Does the Major sequence support
the trend? Do Zones/reactions support the Range? Is confirmation plausible around the
shock? Is `UNCERTAIN` conservative or missing structure?

### HK.00700

```text
trend | window 2025-09-26..10-13 | cutoff 10-13 | close/ATR 633.7/17.7688
  micro H:08-25@615.7>08-27,L:08-28@584.7>09-01,H:09-03@607.7>09-04
  major H:09-18@659.2>09-23,L:09-23@621.7>09-29,H:10-02@677.7>10-10 | labels HL,HH,HL,HH
  zones SC[619.3248,624.0752]x1, RC[613.7627,617.6373]x1, RC[657.0595,661.3405]x1, RC[675.2939,680.1061]x1 | no range | BULL_TREND
range/choppy | window 2026-08-20..09-02 | cutoff 09-02 | 438.2/11.1811
  micro H:08-20@457.4>08-24,L:08-25@438>08-28,H:08-28@462.2>09-01
  major H:07-16@494.8>07-22,L:07-24@432>07-29,H:08-05@497.8>08-11 | labels LL,HH,HL,EH
  zones SC[429.3739,434.6261]x1, RF[419.6238,422.7762]x3, SC[417.7413,423.0587]x1, SF[407.2546,412.9454]x2 | range [407.2546,513.1116]/1.0 | RANGE
shock | window 2025-03-24..04-07 | cutoff 04-07 | 425.6/21.5789
  micro H:03-07@537.2>03-10,L:03-13@489.4>03-14,H:03-19@535.2>03-20
  major H:03-07@537.2>03-13,L:03-13@489.4>03-18,H:03-19@535.2>03-25 | labels HL,HH,HL,EH
  zones RF[419.6238,422.7762]x3, SF[391.4074,394.9926]x2, SC[460.0164,466.7836]x1, SC[380.9129,383.4871]x1 | no range | UNCERTAIN
ambiguous | window 2024-11-22..12-05 | cutoff 12-05 | 395.4/8.4238
  micro L:11-13@386.2>11-20,H:11-20@404>11-22,L:11-27@382.2>12-03
  major H:10-07@472.6>10-08,L:10-31@394.8>11-05,H:11-08@426.2>11-12 | labels HL,LH
  zones SC[392.9062,396.6938]x1, RC[424.2484,428.1516]x1, SC[354.1979,356.2021]x1, RC[469.6269,475.5731]x1 | no range | UNCERTAIN
```

### HK.09698

```text
trend | window 2025-02-27..03-12 | cutoff 03-12 | close/ATR 35.65/3.6761
  micro H:01-20@22.95>01-23,L:01-23@19.46>01-27,H:01-27@23.6>01-28
  major L:01-23@19.46>01-27,H:02-21@48.9>02-26,L:03-04@29.75>03-06 | labels HH,HL,HH,HL
  zones SC[29.1136,30.3864]x1, RC[28.2832,28.9168]x1, RF[23.4707,23.9293]x2, RC[22.6309,22.9691]x1 | no range | BULL_TREND
range/choppy | window 2025-11-05..11-18 | cutoff 11-18 | 28.6/1.3175
  micro H:06-27@30.1>07-02,L:07-02@28.1>07-03,H:07-04@33.7>07-07
  major H:09-26@42.28>10-08,L:10-17@31.18>10-27,H:10-30@37.38>10-31 | labels HL,HH,LL,LH
  zones RF[28.2077,28.7423]x2, RC[29.088,29.612]x1, SF[29.4698,30.3602]x2, SC[30.9472,31.4128]x1 | range [16.961,39.75]/.875 | RANGE
shock | window 2025-03-24..04-07 | cutoff 04-07 | 18.84/2.5975
  micro H:01-20@22.95>01-23,L:01-23@19.46>01-27,H:01-27@23.6>01-28
  major H:02-21@48.9>02-26,L:03-04@29.75>03-06,H:03-06@39.75>03-13 | labels HL,HH,HL,LH
  zones SF[18.4355,18.7845]x2, SF[19.2013,19.6387]x2, SF[17.4,18.04]x2, RF[21.295,21.605]x2 | no range | UNCERTAIN
ambiguous | window 2025-04-03..04-17 | cutoff 04-17 | 20/2.2974
  micro L:01-23@19.46>01-27,H:01-27@23.6>01-28,L:04-09@17>04-10
  major H:02-21@48.9>02-26,L:03-04@29.75>03-06,H:03-06@39.75>03-13 | labels HL,HH,HL,LH
  zones SF[19.2013,19.6387]x2, SF[18.4355,18.7845]x2, RF[21.295,21.605]x2, SF[17.4,18.04]x2 | no range | UNCERTAIN
```

### US.AVGO

```text
trend | window 2026-08-19..09-01 | cutoff 09-01 | close/ATR 369.68/11.5811
  micro H:2025-06-12@255.413>06-13,L:06-20@242.3939>06-23,H:06-30@275.685>07-01
  major H:2025-06-04@262.8806>06-06,L:06-09@238.7942>06-12,H:07-31@304.7163>08-01 | labels HL,HH,HL,HH
  zones RC[303.3472,306.0854]x1, RC[261.628,264.1331]x1, RF[244.456,248.438]x3, SC[237.5694,240.019]x1 | no range | BULL_TREND
range/choppy | window 2025-02-07..02-21 | cutoff 02-21 | 215.9065/8.7047
  micro H:2024-11-08@182.2314>11-11,L:11-27@155.1405>12-02,H:12-04@172.7186>12-05
  major H:12-26@244.1661>2025-01-10,L:01-13@216.7458>01-17,H:01-24@246.447>01-27 | labels HL,LH,HL,EH
  zones SF[213.8762,217.1355]x2, RF[244.456,248.438]x3, RF[182.0944,183.7176]x2, RC[176.5701,178.439]x1 | range [213.8762,248.438]/.9 | RANGE
shock | window 2026-05-21..06-04 | cutoff 06-04 | 418.2481/26.9864
  micro/major/labels are unchanged from the 2026-09-01 trend sample above
  same four nearest zones | no range | BULL_TREND
ambiguous | window 2025-04-04..04-17 | cutoff 04-17 | 169.3477/11.718
  micro H:04-02@171.7642>04-03,L:04-07@136.7736>04-08,H:04-09@185.5307>04-16
  major L:01-13@216.7458>01-17,H:01-24@246.447>01-27,L:04-07@136.7736>04-09 | labels LH,HL,EH,LL
  zones SF[163.2011,164.9041]x2, RC[176.5701,178.439]x1, RF[182.0944,183.7176]x2, SC[154.412,155.8689]x1 | no range | UNCERTAIN
```

The shock sample retaining Pivot facts from 2025 is a counterexample, not a successful
looking example; it is central to the history/path-lock concern.

### US.NVDA

```text
trend | window 2026-05-19..06-02 | cutoff 06-02 | close/ATR 222.5606/8.344
  micro H:2025-05-21@137.2077>05-22,L:05-23@128.9792>05-27,H:05-29@143.2892>05-30
  major L:2026-05-04@194.5133>05-06,H:05-14@236.2646>05-19,L:05-27@208.5369>06-01 | labels HH,HL,HH,HL
  zones RC[215.518,217.6271]x1, RC[210.8488,212.9904]x1, RC[234.9889,237.5403]x1, SC[207.3447,209.7292]x1 | no range | BULL_TREND
range/choppy | window 2025-02-20..03-05 | cutoff 03-05 | 117.1251/7.6661
  micro H:02-18@143.2261>02-21,L:02-25@124.2544>02-26,H:02-27@134.8087>02-28
  major H:01-24@148.7478>01-27,L:02-03@112.8415>02-06,H:02-18@143.2261>02-24 | labels HL,LH,LL,LH
  zones SF[112.8415,114.9604]x2, RC[126.6933,128.2384]x1, SF[126.6708,129.3169]x2, SF[131.0453,132.4536]x2 | range [112.8415,144.495]/.925 | RANGE
shock | window 2025-01-13..01-27 | cutoff 01-27 | 118.2434/8.4894
  micro H:01-07@152.9016>01-08,L:01-13@129.3169>01-15,H:01-24@148.7478>01-27
  major H:01-07@152.9016>01-08,L:01-13@129.3169>01-21,H:01-24@148.7478>01-27 | labels LL,HH,HL,LH
  zones SC[114.2344,115.6863]x1, RC[126.6933,128.2384]x1, SF[126.6708,129.3169]x2, SF[131.0453,132.4536]x2 | no range | UNCERTAIN
ambiguous | window 2024-10-23..11-05 | cutoff 11-05 | 139.6917/4.4089
  micro H:09-26@127.4658>09-27,L:10-02@114.9604>10-03,H:10-14@139.3822>10-15
  major H:09-26@127.4658>10-01,L:10-02@114.9604>10-04,H:10-22@144.1947>10-31 | labels HH
  zones RC[143.5108,144.8786]x1, RC[126.6933,128.2384]x1, SC[114.2344,115.6863]x1 | no range | UNCERTAIN
```

### US.VRT

```text
trend | window 2026-06-09..06-23 | cutoff 06-23 | close/ATR 318.32/23.3539
  micro H:2025-05-14@109.793>05-21,L:05-23@100.8558>05-27,H:05-29@114.1768>05-30
  major L:2026-03-30@231.6522>04-07,H:05-14@379.8566>05-18,L:06-10@275.1232>06-15 | labels HH,HL,HH,HL
  zones RC[279.6204,284.3632]x1, SC[272.3789,277.8675]x1, RC[376.7249,382.9883]x1, SC[229.447,233.8574]x1 | no range | BULL_TREND
range/choppy | window 2025-09-17..09-30 | cutoff 09-30 | 150.7375/6.8833
  micro H:05-14@109.793>05-21,L:05-23@100.8558>05-27,H:05-29@114.1768>05-30
  major L:09-05@118.5706>09-10,H:09-22@152.3262>09-26,L:09-26@136.9687>09-30 | labels LH,LL,HH,HL
  zones RF[152.282,154.3833]x3, RC[144.2548,146.461]x1, SC[135.9362,138.0012]x1, RC[133.9061,135.6647]x1 | range [117.5411,154.3833]/1.0 | RANGE
shock | window 2026-01-29..02-11 | cutoff 02-11 | 248.4001/17.0791
  micro H:2025-05-14@109.793>05-21,L:05-23@100.8558>05-27,H:05-29@114.1768>05-30
  major L:2026-01-08@158.6998>01-16,H:01-30@200.3063>02-05,L:02-05@172.2738>02-06 | labels LH,HL,HH,HL
  zones RF[199.6679,202.924]x2, RC[187.8886,191.2635]x1, RC[181.8084,184.5294]x1, SC[170.419,174.1285]x1 | no range | BULL_TREND
ambiguous | window 2024-10-31..11-13 | cutoff 11-13 | 124.2632/5.0398
  micro H:10-28@114.9432>10-31,L:11-04@104.3559>11-05,H:11-11@130.0208>11-12
  major L:09-23@94.8164>10-03,H:10-23@116.1606>11-01,L:11-04@104.3559>11-05 | labels HL
  zones RC[115.5466,116.7745]x1, SC[103.7189,104.9929]x1, SC[94.181,95.4518]x1 | no range | UNCERTAIN
```

The VRT 2026 samples preserve May-2025 Micro Pivots while Major structure advances,
which is a deliberately retained counterexample for reviewer inspection.

## Limitations and blockers

- The run was not blocked: all five securities had quote/history entitlement and OpenD
  was reachable. Evidence is environmental and may change with provider availability,
  entitlement, the current clock, and the rolling minute window.
- Provider history is current QFQ. Corporate-action adjustments may rewrite past values;
  therefore `historical_replay_safe = false`. No claim of strict point-in-time historical
  reconstruction, P&L, alpha, or profitability is made.
- US M30 coverage is only 285 completed bars from 2026-08-03T15:00Z through
  2026-09-02T14:00Z. HK M30 coverage is only 220 completed bars from
  2026-08-04T01:30Z through 2026-09-02T07:30Z. No longer intraday history is implied.
- Prefix invariance proves that already-confirmed facts do not change when future bars
  are appended to the same origin. It does not prove independence from the chosen
  leading-history boundary; AVGO demonstrates that distinction.
- Sensitivity counts are diagnostic. No parameter optimization, alternate production
  default, or recommendation is authorized by this checkpoint.
- Human visual review of the selected periods remains mandatory. This document does not
  call the checkpoint PASS and does not approve TASK-006C.

## Scope confirmation

No file under `src/` was modified. No migration, TASK-006B1 behavior, TASK-006C event,
advisory, score/composite score, ranking, paper portfolio, backtesting, broker account,
trade context, or broker-write behavior was added or changed.

Final checkpoint status: **STRUCTURE_CONCERNS_FOUND**
