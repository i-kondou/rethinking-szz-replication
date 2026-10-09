"""Saved-study paired tests and candidate/overlap extraction."""
from collections import defaultdict
from fractions import Fraction
AGENT_METHODS=("LLM4SZZ","AgentSZZ","SZZ-Agent","Simple-SZZ-Agent")

def f1(row):
    denominator = 2 * row["tp"] + row["fp"] + row["fn"]
    return Fraction(2 * row["tp"], denominator) if denominator else Fraction(0)

def case_scores(rows, ids):
    groups = defaultdict(list)
    for row in rows:
        groups[row["sample_id"]].append(row)
    assert set(groups) == set(ids)
    reps = 3 if rows[0]["method"] in (*AGENT_METHODS, "Claude Code") else 1
    for group in groups.values():
        assert len(group) == reps
        assert {r["replicate"] for r in group} == set(range(1, reps + 1))
    return {sid: sum(map(f1, group), Fraction(0)) / reps for sid, group in groups.items()}

def paired_test(claude, baseline):
    import scipy
    from scipy.stats import wilcoxon
    assert claude.keys() == baseline.keys()
    ids = sorted(claude, key=int)
    differences = [claude[sid] - baseline[sid] for sid in ids]
    ds = list(map(float, differences))
    result = wilcoxon(ds, alternative="two-sided", zero_method="wilcox", method="approx",
                      correction=False) if any(ds) else None
    return dict(cases=len(ids), nonzero_cases=sum(d != 0 for d in ds),
                statistic=float(result.statistic) if result else 0.0,
                p_value=float(result.pvalue) if result else 1.0,
                positive_cases=sum(d > 0 for d in ds), negative_cases=sum(d < 0 for d in ds),
                method="approx", zero_method="wilcox", alternative="two-sided",
                continuity_correction=False, multiple_comparison_correction=None,
                scipy_version=scipy.__version__, direction="Claude Code minus baseline",
                paired_scores=[dict(sample_id=sid, claude_f1=str(claude[sid]),
                                    baseline_f1=str(baseline[sid]), difference=str(d))
                               for sid, d in zip(ids, differences)])

def holm(values):
    adjusted, previous = [0.0] * len(values), 0.0
    for rank, i in enumerate(sorted(range(len(values)), key=values.__getitem__)):
        previous = max(previous, (len(values) - rank) * values[i])
        adjusted[i] = min(1.0, previous)
    return adjusted

def candidate_evidence(log):
    """Union of actual saved statement/candidate fields, not hash mentions.

    Stage-one raw candidates need not reach stage two. The upstream log also
    contains a ranking prompt not actually sent; never infer an API request
    from that prompt. The original wrong-variable behavior is retained.
    """
    stages = defaultdict(set)
    assessed = []
    for item in log:
        if isinstance(item, str):
            if item.startswith("begin to deal cand_cid "):
                assessed.append(item.rsplit(" ", 1)[1])
        elif "role" not in item:
            stages["s2_cand_cids"].update(item.get("s2_cand_cids", []))
            for key in ("s1_raw_stmts_infos", "s1_ranked_stmts_infos", "s2_cand_stmts"):
                stages[key].update(x["induce_cid"] for x in item.get(key, []) if x.get("induce_cid"))
    return {k: sorted(v - {""}) for k, v in stages.items()}, assessed

def overlap(rows, ids):
    found = {method: {r["sample_id"] for r in rows if r["method"] == method and r["tp"] > 0}
             for method in (*AGENT_METHODS, "Claude Code")}
    cc, universe = found["Claude Code"], set(ids)
    pairs = []
    for method in AGENT_METHODS:
        base = found[method]
        regions = dict(baseline_only=base - cc, both=base & cc, claude_only=cc - base,
                       neither=universe - (base | cc))
        pairs.append(dict(baseline=method, counts={k: len(v) for k, v in regions.items()},
                          case_ids={k: sorted(v, key=int) for k, v in regions.items()}))
    return dict(sample_count=len(ids), definition="At least one of three runs contains an oracle BIC; not exact match.",
                comparisons=pairs)
