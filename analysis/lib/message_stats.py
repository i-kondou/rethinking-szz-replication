"""Paired message-ablation tests; no model calls."""
from fractions import Fraction
from collections import Counter,defaultdict
from statistics import mean,median
from scipy.stats import rankdata,wilcoxon
METRICS=("f1","bash_calls","elapsed_seconds","common_cost_usd")

def require(ok, message):
    if not ok:
        raise ValueError(message)

def f1_fraction(row):
    denom = 2 * row['tp'] + row['fp'] + row['fn']
    return Fraction(2 * row['tp'], denom) if denom else Fraction(0)

def holm(pvalues):
    require(all(0 <= p <= 1 for p in pvalues), 'invalid p value')
    result, running = [0.] * len(pvalues), 0.
    for order, idx in enumerate(sorted(range(len(pvalues)), key=lambda i: pvalues[i])):
        running = max(running, min(1., (len(pvalues) - order) * pvalues[idx]))
        result[idx] = running
    return result

def signed_rank(diffs):
    """RQ1-compatible approximation plus exact conditional sign distribution."""
    d = [float(x) for x in diffs]
    nz = [x for x in d if x != 0]
    positive, negative = sum(x > 0 for x in d), sum(x < 0 for x in d)
    if not nz:
        return dict(n=len(d), positive=0, negative=0, zero=len(d), statistic=0.,
                    p_raw=1., p_exact=1., rank_biserial=0., w_plus=0., w_minus=0.,
                    tied_absolute_groups=0)
    ranks = rankdata([abs(x) for x in nz], method='average')
    doubled = [int(round(2 * x)) for x in ranks]
    observed = sum(r for r, x in zip(doubled, nz) if x > 0)
    total = sum(doubled)
    # Counts of subset rank sums across all 2**n equally likely sign assignments.
    ways = [0] * (total + 1)
    ways[0] = 1
    reachable = 0
    for r in doubled:
        for s in range(reachable, -1, -1):
            ways[s + r] += ways[s]
        reachable += r
    tail = sum(ways[:min(observed, total-observed) + 1])
    p_exact = min(1., float(Fraction(2 * tail, 2 ** len(nz))))
    approx = wilcoxon(d, alternative='two-sided', zero_method='wilcox',
                      correction=False, method='approx')
    return dict(n=len(d), positive=positive, negative=negative, zero=len(d)-len(nz),
                statistic=float(approx.statistic), p_raw=float(approx.pvalue),
                p_exact=p_exact, w_plus=observed/2, w_minus=(total-observed)/2,
                rank_biserial=(2*observed-total)/total,
                tied_absolute_groups=sum(n > 1 for n in Counter(abs(x) for x in nz).values()))

def case_means(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r['condition'], r['sample_id'])].append(r)
    ids = sorted({r['sample_id'] for r in rows}, key=int)
    result = []
    for sid in ids:
        record = {'sample_id': sid}
        require(len({r['repository'] for cond in ('present', 'free') for r in groups[(cond, sid)]}) == 1,
                f'cross-condition repository mismatch: {sid}')
        for cond in ('present', 'free'):
            group = groups[(cond, sid)]
            require(len(group) == 3 and {r['repeat'] for r in group} == {1, 2, 3}, f'coverage: {sid}/{cond}')
            require(len({r['repository'] for r in group}) == 1, 'repository mismatch')
            record['repository'] = group[0]['repository']
            record[cond] = {k: sum((f1_fraction(r) if k == 'f1' else Fraction(str(r[k]))
                                    for r in group), Fraction(0)) / 3
                            for k in (*METRICS, 'cli_seconds', 'written_commands')}
        result.append(record)
    return result

def test_family(cases, time_key='elapsed_seconds'):
    tests = {}
    for metric in METRICS:
        key = time_key if metric == 'elapsed_seconds' else metric
        diffs = [r['free'][key]-r['present'][key] for r in cases]
        tests[metric] = dict(signed_rank(diffs),
                            mean_present=float(mean(r['present'][key] for r in cases)),
                            mean_free=float(mean(r['free'][key] for r in cases)),
                            mean_difference=float(mean(diffs)), median_difference=float(median(diffs)))
    for metric, padj, pexact in zip(METRICS, holm([tests[k]['p_raw'] for k in METRICS]),
                                  holm([tests[k]['p_exact'] for k in METRICS])):
        tests[metric].update(p_holm=padj, p_exact_holm=pexact,
                             significant_005=padj < .05, significant_001=padj < .01)
    return tests

def descriptive(rows):
    tp, fp, fn = (sum(r[k] for r in rows) for k in ('tp', 'fp', 'fn'))
    return dict(runs=len(rows), cases=len({r['sample_id'] for r in rows}), tp=tp, fp=fp, fn=fn,
                precision=tp/(tp+fp), recall=tp/(tp+fn), pooled_f1=2*tp/(2*tp+fp+fn),
                exact=sum(r['fp'] == r['fn'] == 0 for r in rows),
                resources={k: dict(mean=mean(r[k] for r in rows), median=median(r[k] for r in rows),
                                   total=sum(r[k] for r in rows))
                           for k in (*METRICS[1:], 'cli_seconds', 'reported_cost_usd', 'written_commands')})
