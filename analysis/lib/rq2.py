"""Reapply the 20 saved manual classifications and aggregate RQ2."""
import copy,csv,re,statistics
from collections import Counter,defaultdict
import blocks
from common import ROOT, data
EXPECTED = [['B', 'C'], ['C'], *[['A'] for _ in range(6)], ['A', 'B', 'C'], ['A'], ['C'], ['C'], *[['B'] for _ in range(5)], ['C'], ['A', 'B', 'C'], ['C']]

def read_inputs():
    return {k:data(k) for k in ("machine","evidence","census","outcomes")}


def read_manual_labels():
    with (ROOT / 'results/inputs/rq2-manual-labels.csv').open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == ['case_id', 'run', 'bash_call', 'activities']
        rows = list(reader)
    for row in rows:
        assert set(row) == set(reader.fieldnames) and all(row.values())
        assert re.fullmatch(r'[1-9][0-9]*', row['case_id'])
        assert re.fullmatch(r'r0[123]', row['run'])
        assert re.fullmatch(r'[1-9][0-9]*', row['bash_call'])
        acts = row['activities'].split('+')
        assert acts == sorted(set(acts)) and set(acts) <= {'A', 'B', 'C'}
    rows.sort(key=lambda row: (int(row['case_id']), row['run'], int(row['bash_call'])))
    return [dict(number=i, call_key=f"{row['case_id']}:{row['run']}#{row['bash_call']}",
                 activities=row['activities'].split('+')) for i, row in enumerate(rows, 1)]

def activity_set(call):
    return sorted({o['activity'] for o in call['operations'] if o['activity'] in {'A', 'B', 'C'}})

def overlay_call(call, decision=None):
    result = copy.deepcopy(call)
    result['label_source'] = 'machine_v5'
    result['machine_activity_complete'] = call['activity_complete']
    if decision is None:
        return result
    assert not call['activity_complete']
    assert decision['call_key'] == call['key']
    acts = decision['activities']
    assert acts == sorted(set(acts)) and acts and set(acts) <= {'A', 'B', 'C'}
    assert set(activity_set(call)) <= set(acts)
    result.update(label_source='user', decision_number=decision['number'],
                  machine_operations=copy.deepcopy(call['operations']),
                  machine_structure_hold=call['structure_hold'],
                  machine_targets_complete=call['targets_complete'],
                  activity_complete=True, structure_hold=len(acts) > 1,
                  internal_order_unknown=len(acts) > 1, targets_complete=False)
    # These are activity-set members, NOT counted internal operations.
    result['operations'] = [dict(id=f"{call['key']}/user-set-{a}", activity=a,
        target='unknown', rule='explicit_user_activity_set', reasons=[],
        unit='unordered_activity_set_member', command_fragment=call['command']) for a in acts]
    return result

def set_projection(groups):
    result = []
    for group in groups:
        acts = sorted({a for lane in group['lanes'] for a in lane['activities'] if a in {'A', 'B', 'C'}})
        if acts and (not result or result[-1] != acts):
            result.append(acts)
    return result

def patterns(projection):
    segments = projection.split('?')
    return dict(starts_AB=projection.startswith('AB'), has_ABA=any('ABA' in s for s in segments),
                has_four_AB=any(re.search(r'ABAB|BABA', s) for s in segments))

def describe(values):
    q = statistics.quantiles(values, method='inclusive') if len(values) > 1 else values * 3
    return dict(mean=statistics.mean(values), median=statistics.median(values), q1=q[0], q3=q[2],
                minimum=min(values), maximum=max(values))

def normalized_prediction(prediction, resolved):
    values = [resolved.get(p) or p for p in prediction]
    assert all(re.fullmatch('[0-9a-f]{40}', p) for p in values)
    return sorted(set(values))

def ranking(calls):
    counts, runs, callsets = Counter(), defaultdict(set), defaultdict(set)
    for c in calls:
        gs = iter(c['git'])
        for item in c['invocations']:
            name = 'git ' + str(next(gs)['subcommand']) if item['executable'] == 'git' else item['executable']
            counts[name] += 1
            runs[name].add(c['slot_id'])
            callsets[name].add((c['slot_id'], c['call_index']))
        assert next(gs, None) is None
    return [dict(command=k, occurrences=n, calls=len(callsets[k]), runs=len(runs[k]))
            for k, n in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]

def flag_value(args, flag):
    for i, arg in enumerate(args):
        if arg == flag:
            return args[i + 1] if i + 1 < len(args) else ''
        if arg.startswith(flag) and arg != flag:
            return arg[len(flag):].lstrip('=')
    return None

def range_kind(args):
    value = flag_value(args, '-L')
    if value is None:
        return 'no_L'
    match = re.match(r'^(\d+),(\+?\d+)(?::|$)', value)
    if not match:
        return 'symbolic_or_function_range'
    start, end = match.groups()
    single = end == '+1' or not end.startswith('+') and int(start) == int(end)
    return 'one_line' if single else 'numeric_multiline'

def log_format(args):
    patch = any(a in {'-p', '--patch', '-u'} for a in args) or flag_value(args, '-L') is not None
    return ('oneline' if '--oneline' in args else 'standard') + ('_with_patch' if patch else '_without_patch')

def query_kinds(args):
    result = []
    for flag in ['-L', '-S', '-G']:
        if flag_value(args, flag) is not None:
            result.append(flag)
    return result

def one_commit_limit(args):
    for i, arg in enumerate(args):
        if arg == '--':
            break
        if arg in {'-1', '-n1', '--max-count=1'}:
            return True
        if arg in {'-n', '--max-count'} and i + 1 < len(args) and args[i+1] == '1':
            return True
    return False

def evidence_audit(census, evidence, outcomes):
    raw = {f"{r['slot_id']}#{c['index']}": c for r in evidence['runs'] for c in r['calls']}
    firsts, provenance = [], []
    seen = set()
    for c in census['calls']:
        key = f"{c['slot_id']}#{c['call_index']}"
        for j, g in enumerate(c['git'], 1):
            sub, args = g['subcommand'], g['arguments']
            row = dict(call_key=key, slot_id=c['slot_id'], sample_id=c['sample_id'], call_index=c['call_index'],
                       git_index_in_call=j, exact=outcomes[c['slot_id']]['exact_set_match'],
                       subcommand=sub, arguments=args, tool_error=c['is_error'])
            if c['slot_id'] not in seen:
                seen.add(c['slot_id'])
                row = dict(row, command=c['command'], format=log_format(args) if sub == 'log' else None,
                           query_kinds=query_kinds(args) if sub == 'log' else [],
                           one_commit_limit=one_commit_limit(args) if sub == 'log' else False,
                           oneline_subject_lines=sum(bool(re.match(r'^[0-9a-f]{7,40}\s+\S', line)) for line in raw[key]['output'].splitlines()))
                firsts.append(row)
            if sub == 'blame' or sub == 'log' and query_kinds(args):
                provenance.append(dict(row, range_kind=range_kind(args), query_kinds=query_kinds(args),
                    command=c['command'], output_excerpt=raw[key]['output'][:800],
                    first_explicit_git=(firsts[-1]['call_key'] == key and firsts[-1]['git_index_in_call'] == j)))
    return dict(first_git=firsts, provenance_requests=provenance)

def build():
    inp = read_inputs()
    original = inp['machine']['runs']
    decisions = read_manual_labels()
    assert len(decisions) == 20 and [d['number'] for d in decisions] == list(range(1, 21))
    assert [d['activities'] for d in decisions] == EXPECTED
    dm = {d['call_key']: d for d in decisions}
    assert len(dm) == len(decisions)
    assert set(dm) == {c['key'] for r in original for c in r['calls'] if not c['activity_complete']}
    evidence = {r['slot_id']: r for r in inp['evidence']['runs']}
    census = {r['slot_id']: r for r in inp['census']['runs']}
    outcomes = {r['slot_id']: r for r in inp['outcomes']['rows']}
    assert set(evidence) == set(census) == set(outcomes) == {r['slot_id'] for r in original}
    census_calls = {f"{c['slot_id']}#{c['call_index']}": c for c in inp['census']['calls']}
    runs, changes = [], []
    for old in original:
        sid = old['slot_id']; e = evidence[sid]; outcome = outcomes[sid]
        assert old['exact'] == e['exact'] == census[sid]['exact'] == outcome['exact_set_match']
        assert outcome['prediction_bic_hashes'] == e['prediction']
        prediction = normalized_prediction(outcome['prediction_bic_hashes'], e['resolved_hashes'])
        assert len(old['calls']) == len(e['calls']) == census[sid]['bash_calls']
        calls = []
        for c, raw in zip(old['calls'], e['calls']):
            cc = census_calls[c['key']]
            assert c['command'] == raw['command'] == cc['command']
            assert c['tool_use_id'] == raw['tool_use_id'] == cc['tool_use_id']
            assert c['tool_error'] == raw['tool_error'] == cc['is_error']
            calls.append(overlay_call(c, dm.get(c['key'])))
        view = blocks.make_blocks(calls)
        assert [g['call_keys'] for g in view['groups']] == [g['call_keys'] for g in old['groups']]
        r = dict(slot_id=sid, sample_id=old['sample_id'], exact=old['exact'],
                 repository=e['repository'], prediction=prediction,
                 original_prediction=outcome['prediction_bic_hashes'], transcript_path=old['transcript_path'],
                 bash_calls=len(calls), command_occurrences=census[sid]['commands'],
                 first_git=census[sid]['first_git'], calls=calls, **view)
        r['set_projection'] = set_projection(view['groups'])
        r['fully_serial'] = view['complete'] and all(n['kind'] == 'activity' for n in view['nodes'])
        r['patterns'] = patterns(view['serial_projection'])
        r['activities'] = sorted({a for c in calls for a in activity_set(c)})
        runs.append(r)
        if any(c['key'] in dm for c in calls):
            changes.append(dict(slot_id=sid, old_trace=old['trace'], new_trace=view['trace'],
                old_complete=old['complete'], new_complete=view['complete'],
                decision_numbers=[dm[c['key']]['number'] for c in calls if c['key'] in dm]))
    audit = evidence_audit(inp['census'], inp['evidence'], outcomes)
    cases = []
    for sample in sorted({r['sample_id'] for r in runs}, key=int):
        rs = [r for r in runs if r['sample_id'] == sample]
        olds = [r for r in original if r['sample_id'] == sample]
        assert len(rs) == 3
        exacts = sum(r['exact'] for r in rs)
        cases.append(dict(sample_id=sample, outcome_group='success' if exacts == 3 else 'failure' if exacts == 0 else 'mixed',
            same_prediction=len({tuple(r['prediction']) for r in rs}) == 1,
            empty_prediction=all(not r['prediction'] for r in rs),
            old_block_comparison=blocks.compare([(r['complete'], r['signature']) for r in olds]),
            block_comparison=blocks.compare([(r['complete'], r['signature']) for r in rs]),
            set_comparison=blocks.compare([(True, r['set_projection']) for r in rs]),
            serial_comparison=blocks.compare([(r['fully_serial'], r['serial_projection']) for r in rs])))
    groups = {}
    for name, flag in [('all', None), ('success', True), ('failure', False)]:
        rs = [r for r in runs if flag is None or r['exact'] == flag]
        ids = {r['slot_id'] for r in rs}; cs = [c for r in rs for c in r['calls']]
        command_calls = [c for c in inp['census']['calls'] if c['slot_id'] in ids]
        firsts = [f for f in audit['first_git'] if f['slot_id'] in ids]
        prov = [p for p in audit['provenance_requests'] if p['slot_id'] in ids]
        blame = [p for p in prov if p['subcommand'] == 'blame']
        logs = [p for p in prov if p['subcommand'] == 'log']
        samecases = [c for c in cases if c['same_prediction'] and (name == 'all' or c['outcome_group'] == name)]
        groups[name] = dict(runs=len(rs), calls=len(cs), machine_labeled_calls=sum(c['label_source'] == 'machine_v5' for c in cs),
            user_labeled_calls=sum(c['label_source'] == 'user' for c in cs),
            activity_unknown_calls=sum(not c['activity_complete'] for c in cs),
            order_hold_calls=sum(c['internal_order_unknown'] for c in cs),
            order_hold_runs=sum(any(c['internal_order_unknown'] for c in r['calls']) for r in rs),
            mixed_overlap_runs=sum(any(g['mixed_overlap'] for g in r['groups']) for r in rs),
            complete_block_runs=sum(r['complete'] for r in rs), fully_serial_runs=sum(r['fully_serial'] for r in rs),
            bash_per_run=describe([r['bash_calls'] for r in rs]), command_occurrences=sum(r['command_occurrences'] for r in rs),
            commands_per_run=describe([r['command_occurrences'] for r in rs]),
            git_occurrences=sum(c['git_commands'] for c in command_calls),
            non_git_occurrences=sum(c['non_git_commands'] for c in command_calls),
            tool_error_calls=sum(c['tool_error'] for c in cs), ranking=ranking(command_calls),
            activity_calls={a: sum(a in activity_set(c) for c in cs) for a in 'ABC'},
            activity_runs={a: sum(a in r['activities'] for r in rs) for a in 'ABC'},
            first_activity= dict(Counter(r['nodes'][0]['label'] for r in rs)),
            patterns={k: sum(r['patterns'][k] for r in rs) for k in ['starts_AB', 'has_ABA', 'has_four_AB']},
            full_serial_ranking=dict(Counter(r['serial_projection'] for r in rs if r['fully_serial']).most_common()),
            first_git=dict(Counter(f['subcommand'] for f in firsts)),
            first_log_formats=dict(Counter(f['format'] for f in firsts if f['subcommand'] == 'log')),
            first_log_query_kinds={q: sum(q in f.get('query_kinds', []) for f in firsts) for q in ['-L', '-S', '-G']},
            first_log_options={q: sum(q in f['arguments'] for f in firsts if f['subcommand'] == 'log') for q in ['--follow', '--all', '--reverse', '--']},
            first_oneline_no_patch_non_single=sum(f['format'] == 'oneline_without_patch' and not f['one_commit_limit'] for f in firsts),
            first_oneline_no_patch_single=sum(f['format'] == 'oneline_without_patch' and f['one_commit_limit'] for f in firsts),
            first_oneline_with_subject_return=sum(f['subcommand'] == 'log' and f['format'].startswith('oneline') and f['oneline_subject_lines'] > 0 for f in firsts),
            blame=dict(occurrences=len(blame), calls=len({p['call_key'] for p in blame}), runs=len({p['slot_id'] for p in blame}),
                one_line_calls=len({p['call_key'] for p in blame if p['range_kind']=='one_line'}),
                one_line_runs=len({p['slot_id'] for p in blame if p['range_kind']=='one_line'}),
                scope_counts=dict(Counter(p['range_kind'] for p in blame)), first_git=sum(p['first_explicit_git'] for p in blame)),
            log_provenance={q: dict(occurrences=sum(q in p['query_kinds'] for p in logs),
                runs=len({p['slot_id'] for p in logs if q in p['query_kinds']}),
                one_line=sum(q in p['query_kinds'] and p['range_kind'] == 'one_line' for p in logs),
                first_git=sum(q in p['query_kinds'] and p['first_explicit_git'] for p in logs)) for q in ['-L', '-S', '-G']},
            same_answer_cases=len(samecases), same_answer_empty_cases=sum(c['empty_prediction'] for c in samecases),
            same_answer_comparisons={k: dict(Counter(c[k] for c in samecases)) for k in ['old_block_comparison', 'block_comparison', 'set_comparison', 'serial_comparison']})
    assert len(runs) == 237 and len(cases) == 79 and groups['all']['calls'] == 1612
    assert sum(r['exact'] for r in runs) == 180 and groups['all']['activity_unknown_calls'] == 0
    assert groups['all']['command_occurrences'] == inp['census']['summary']['commands']
    baseline = dict(activity_unknown_calls=inp['machine']['summary']['activity_unknown_calls'],
        complete_block_runs=inp['machine']['summary']['block_complete_runs'],
        patterns={k: sum(patterns(r['serial_projection'])[k] for r in original) for k in ['starts_AB','has_ABA','has_four_AB']},
        activity_runs={a:sum(any(a in activity_set(c) for c in r['calls']) for r in original) for a in 'ABC'})
    return dict(version='rq2-user-adjudicated-20260916', groups=groups, cases=cases, runs=runs,
        changes=changes, audit=audit, machine_baseline=baseline, 
        boundary='Machine v5 plus explicit user call-level decisions. Unordered sets, overlap and errors retained. No hidden-reasoning, causal, independent-coding or execution-count claims.')
