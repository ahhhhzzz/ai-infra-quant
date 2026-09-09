"""Complete-link geometry adapted from the cited 006B base, with active-only input.

No old Pivot detector is called. Median/independence/merge rules follow candidate section 7.
"""

from decimal import Decimal, localcontext

from .types import CONTEXT, RULE, Bar, Box, Evidence, Parameters, Pivot, Zone, digest, q


def median(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("EMPTY_MEDIAN")
    ordered = sorted(values)
    index = len(ordered) // 2
    with localcontext(CONTEXT):
        return q(ordered[index] if len(ordered) % 2 else (ordered[index - 1] + ordered[index]) / 2)


def independent(items: tuple[Pivot, ...]) -> tuple[Pivot, ...]:
    ordered = sorted(
        {p.identity: p for p in items}.values(),
        key=lambda p: (p.extreme, p.extreme_ref, p.confirmed_ref, p.identity),
    )
    accepted: list[Pivot] = []
    for item in ordered:
        if not accepted or item.extreme - accepted[-1].extreme >= 5:
            accepted.append(item)
    return tuple(accepted)


def geometry(items: tuple[Pivot, ...], role: str, params: Parameters) -> Zone:
    with localcontext(CONTEXT):
        if not items or any(p.atr <= 0 for p in items):
            raise ValueError("INVALID_ZONE_TOUCHES")
        center = median(tuple(p.price for p in items))
        atr = median(tuple(p.atr for p in items))
        mad = median(tuple(abs(p.price - center) for p in items))
        minimum, maximum = q(Decimal("0.15") * atr), q(Decimal("0.75") * atr)
        width = min(max(mad, minimum), maximum)
        refs = tuple(p.identity for p in items)
        identity = digest("qstr-zone", (RULE, params.config_hash, role, tuple(sorted(refs))))
        evidence = (
            Evidence(
                "QSTR-006",
                (
                    ("center", center),
                    ("median_atr", atr),
                    ("mad", mad),
                    ("independent_count", len(items)),
                ),
                "halfwidth=clamp(MAD,min,max); count>=2",
                (minimum, maximum, 2),
                refs,
            ),
        )
        return Zone(
            role,
            center,
            atr,
            mad,
            width,
            q(center - width),
            q(center + width),
            items,
            identity,
            evidence,
        )


def iou(left: Zone, right: Zone) -> Decimal:
    with localcontext(CONTEXT):
        intersection = max(Decimal(0), min(left.upper, right.upper) - max(left.lower, right.lower))
        union = max(left.upper, right.upper) - min(left.lower, right.lower)
        return q(intersection / union) if union > 0 else Decimal(0)


def build_zones(
    items: tuple[Pivot, ...], params: Parameters, counts: dict[str, int]
) -> tuple[Zone, ...]:
    if params.timeframe != "D1":
        return ()
    with localcontext(CONTEXT):
        result: list[Zone] = []
        for kind, role in (("LOW", "SUPPORT"), ("HIGH", "RESISTANCE")):
            clusters: list[list[Pivot]] = []
            ordered = sorted(
                {p.identity: p for p in items if p.kind == kind}.values(),
                key=lambda p: (p.price, p.extreme, p.confirmed, p.identity),
            )
            for item in ordered:
                eligible = []
                for cluster in clusters:
                    distances = []
                    for member in cluster:
                        counts["pair_distance"] = counts.get("pair_distance", 0) + 1
                        distances.append(
                            q(abs(item.price - member.price) / median((item.atr, member.atr)))
                        )
                    if all(d <= params.zone_epsilon for d in distances):
                        center = median(tuple(p.price for p in cluster))
                        denominator = median((item.atr, median(tuple(p.atr for p in cluster))))
                        distance = q(abs(item.price - center) / denominator)
                        eligible.append(
                            (
                                distance,
                                digest("qstr-cluster", tuple(p.identity for p in cluster)),
                                cluster,
                            )
                        )
                if eligible:
                    min(eligible, key=lambda choice: choice[:2])[2].append(item)
                else:
                    clusters.append([item])
            result.extend(
                geometry(independent(tuple(cluster)), role, params) for cluster in clusters
            )
        while True:
            merges = []
            for i, left in enumerate(result):
                for j in range(i + 1, len(result)):
                    right = result[j]
                    if left.role != right.role or min(len(left.touches), len(right.touches)) < 2:
                        continue
                    counts["merge_iou"] = counts.get("merge_iou", 0) + 1
                    overlap = iou(left, right)
                    if overlap >= Decimal("0.5"):
                        merges.append(
                            (
                                -overlap,
                                min(left.lower, right.lower),
                                tuple(sorted((left.identity, right.identity))),
                                i,
                                j,
                            )
                        )
            if not merges:
                break
            *_, i, j = min(merges)
            left, right = result[i], result[j]
            merged = geometry(independent(left.touches + right.touches), left.role, params)
            result = [z for index, z in enumerate(result) if index not in (i, j)] + [merged]
        return tuple(sorted(result, key=lambda z: (z.role, z.lower, z.identity)))


def select_zones(
    zones: tuple[Zone, ...], terminal: int, close: Decimal, params: Parameters
) -> tuple[tuple[Zone, ...], tuple[Zone, ...]]:
    with localcontext(CONTEXT):
        eligible = tuple(
            z
            for z in zones
            if len(z.touches) >= 2
            and terminal - max(p.extreme for p in z.touches) <= params.zone_age
            and (z.lower <= close if z.role == "SUPPORT" else z.upper >= close)
        )
        selected = []
        for role in ("SUPPORT", "RESISTANCE"):
            ranked = sorted(
                (z for z in eligible if z.role == role),
                key=lambda z: (
                    max(z.lower - close, close - z.upper, Decimal(0)),
                    -max(p.extreme for p in z.touches),
                    z.lower,
                    z.identity,
                ),
            )
            selected.extend(ranked[:2])
        return eligible, tuple(selected)


def ranges(
    bars: tuple[Bar, ...],
    atrs: tuple[Decimal | None, ...],
    zones: tuple[Zone, ...],
    params: Parameters,
    counts: dict[str, int],
) -> tuple[Box, ...]:
    length = params.range_length
    if params.timeframe != "D1" or len(bars) < length or any(a is None for a in atrs[-length:]):
        return ()
    with localcontext(CONTEXT):
        recent_atr = median(tuple(a for a in atrs[-length:] if a is not None))
        if recent_atr <= 0:
            return ()
        first = len(bars) - length
        valid = []
        for support in (z for z in zones if z.role == "SUPPORT"):
            for resistance in (z for z in zones if z.role == "RESISTANCE"):
                counts["range_pairs"] = counts.get("range_pairs", 0) + 1
                if support.upper >= resistance.lower:
                    continue
                st = tuple(
                    p for p in support.touches if p.extreme >= first and p.confirmed >= first
                )
                rt = tuple(
                    p for p in resistance.touches if p.extreme >= first and p.confirmed >= first
                )
                if min(len(st), len(rt)) < 2:
                    continue
                by_index: dict[int, set[str]] = {}
                for role, touches in (("L", st), ("H", rt)):
                    for p in touches:
                        by_index.setdefault(p.extreme, set()).add(role)
                if any(len(v) != 1 for v in by_index.values()):
                    continue
                sequence: list[str] = []
                for index in sorted(by_index):
                    role = next(iter(by_index[index]))
                    if not sequence or sequence[-1] != role:
                        sequence.append(role)
                if len(sequence) < 4:
                    continue
                inside = sum(support.lower <= b.close <= resistance.upper for b in bars[-length:])
                ratio = q(Decimal(inside) / length)
                width = q((resistance.center - support.center) / recent_atr)
                if ratio < Decimal("0.7") or not Decimal(2) <= width <= Decimal(12):
                    continue
                if not support.lower <= bars[-1].close <= resistance.upper:
                    continue
                refs = tuple(p.identity for p in st + rt)
                identity = digest(
                    "qstr-range",
                    (
                        RULE,
                        params.config_hash,
                        support.identity,
                        resistance.identity,
                        refs,
                        tuple(b.ref for b in bars[-length:]),
                    ),
                )
                proofs = (
                    Evidence(
                        "QSTR-007",
                        (("inside_count", inside), ("lookback", length), ("inside_ratio", ratio)),
                        ">=",
                        Decimal("0.7"),
                        tuple(b.ref for b in bars[-length:]),
                    ),
                    Evidence(
                        "QSTR-007",
                        (("width_atr", width), ("median_atr", recent_atr)),
                        "inclusive between",
                        (Decimal(2), Decimal(12)),
                        refs,
                    ),
                    Evidence(
                        "QSTR-007",
                        (
                            ("support_reactions", len(st)),
                            ("resistance_reactions", len(rt)),
                            ("alternating", tuple(sequence)),
                        ),
                        ">=2 per side AND >=4 alternating",
                        4,
                        refs,
                    ),
                )
                valid.append(
                    Box(
                        support.lower,
                        resistance.upper,
                        ratio,
                        width,
                        len(st) + len(rt),
                        identity,
                        support.identity,
                        resistance.identity,
                        proofs,
                    )
                )
        return tuple(
            sorted(
                valid,
                key=lambda b: (
                    -b.recent_touches,
                    -b.inside_ratio,
                    b.width_atr,
                    digest("qstr-pair", (b.support, b.resistance)),
                ),
            )
        )
