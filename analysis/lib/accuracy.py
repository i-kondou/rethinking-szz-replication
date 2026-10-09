"""Repetition-mean scoring used in the manuscript."""
from fractions import Fraction
COUNTS=("tp","fp","fn")
METRICS=("precision","recall","f1")

def metrics(tp, fp, fn):
    if any(type(v) is not int or v < 0 for v in (tp, fp, fn)):
        raise ValueError("Counts must be nonnegative integers")
    def ratio(a, b):
        return Fraction(a, b) if b else Fraction(0)
    return dict(precision=ratio(tp, tp + fp), recall=ratio(tp, tp + fn),
                f1=ratio(2 * tp, 2 * tp + fp + fn))

def summarize(rows, case_ids, repetitions):
    """Pool cases within each repetition, then average repetition-level scores."""
    expected = {(sid, rep) for sid in case_ids for rep in repetitions}
    observed = [(r["sample_id"], r["replicate"]) for r in rows]
    if len(observed) != len(set(observed)) or set(observed) != expected:
        raise ValueError("Missing, duplicate, or unexpected case/repetition slots")
    per_rep = {}
    for rep in repetitions:
        group = [r for r in rows if r["replicate"] == rep]
        for row in group:
            metrics(*(row[k] for k in COUNTS))
        totals = {k: sum(r[k] for r in group) for k in COUNTS}
        per_rep[str(rep)] = dict(totals, **metrics(**totals))
    means = {k: sum((Fraction(v[k]) for v in per_rep.values()), Fraction(0))
             / len(repetitions) for k in COUNTS + METRICS}
    totals = {k: sum(r[k] for r in rows) for k in COUNTS}
    pooled = dict(totals, **metrics(**totals))
    return {
        "cases": len(case_ids), "runs": len(rows), "repetitions": list(repetitions),
        "per_repetition": {rep: {k: float(v) if isinstance(v, Fraction) else v
                                 for k, v in scores.items()}
                           for rep, scores in per_rep.items()},
        "mean": {k: float(v) for k, v in means.items()},
        "previous_pooled": {k: float(v) if isinstance(v, Fraction) else v
                            for k, v in pooled.items()},
        "rounded_metric_changes": {
            k: {"before": f"{float(pooled[k]):.3f}", "after": f"{float(means[k]):.3f}"}
            for k in METRICS if f"{float(pooled[k]):.3f}" != f"{float(means[k]):.3f}"
        },
    }
