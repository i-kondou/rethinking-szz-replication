"""Validate saved selections, scores, and command counts against raw logs."""
from collections import Counter
from pathlib import Path
from common import ROOT, data, load, require, sha, score, equivalent, relocated
import answers
import trace
import commands


def normalized(raw, saved):
    raw,saved=set(raw),set(saved)
    require(len(raw)==len(saved) and
            all(sum(full.startswith(short) for full in saved)==1 for short in raw) and
            all(sum(full.startswith(short) for short in raw)==1 for full in saved),
            'Recorded full-hash resolution does not match raw answer')
    return sorted(saved)


def audit():
    from run_llm_baseline_subject import parse_szz_agent_prediction
    from run_pyszz import validate_official_output
    current=data('rq1')
    resources={(r['method'],r['slot_id']):r for r in data('resources')['rows']}
    cases=load(ROOT/'dataset/metadata/cases.json')['cases']
    oracles={r['id']:r['oracle_bics'] for r in cases}
    checked=Counter()
    missing=[]
    for row in current['rows']:
        method,slot=row['method'],row['slot_id']
        if method not in ('Claude Code','LLM4SZZ','AgentSZZ','SZZ-Agent','Simple-SZZ-Agent'):
            continue
        ref=resources.get((method,slot))
        if ref is None:
            require(row['scoring_rule']=='unresolved_as_empty_prediction','Unexpected missing run')
            predicted=[]
            missing.append(dict(method=method,slot_id=slot))
        else:
            directory=relocated(ref['run_dir'])
            if method=='Claude Code':
                result=answers.load_result_entry(directory/'transcript.jsonl')
                raw=answers.extract_bic_hashes(result['result'])
            elif method=='AgentSZZ':
                run=load(directory/'engine/run.json')
                require(run['state']=='completed' and not run['test_stub'],'Non-scientific run')
                raw=run['predicted_bics']
                selected=load(directory/'engine/upstream-output/case/result.json')
                require(raw==([selected['bic']] if selected.get('bic') else []),'AgentSZZ selection changed')
            elif method=='LLM4SZZ':
                prediction=load(directory/'prediction.json')
                raw=prediction['predicted_bics']
                require(sha(relocated(prediction['raw_result']))==prediction['raw_result_sha256'],'Changed candidate log')
            else:
                run=load(directory/'run.json')
                require(run['state']=='completed' and not run['test_stub'],'Non-scientific run')
                raw_path=relocated(run['prediction']['raw_result_path'])
                require(sha(raw_path)==run['prediction']['raw_result_sha256'],'Upstream result changed')
                if method=='Simple-SZZ-Agent':
                    raw=load(raw_path)['results'][0]['predicted_bics']
                else:
                    raw,_=parse_szz_agent_prediction(directory/'runtime',raw_path,
                        raw_path if run['szz_agent_flow']['stage2_executed'] else None)
                require(set(raw)==set(run['prediction']['predicted_bics']),'Raw selection differs')
            predicted=normalized(raw,ref['predictions'])
            checked[method]+=1
        require(score(predicted,oracles[row['sample_id']])=={k:row[k] for k in ('tp','fp','fn')},'Score drift: '+method+'/'+slot)
    require(sum(checked.values())+len(missing)==1185,'Incomplete RQ1 slot grid')

    rule_checked={}
    for record in data('rules')['runs']:
        raw=load(relocated(record['path']))
        by_id={str(r['id']):r for r in raw}
        require(len(raw)==len(by_id)==80,'Historical rule-based case grid changed')
        rows={r['sample_id']:r for r in current['rows'] if r['method']==record['method']}
        require(set(rows)==set(oracles),'Historical rule-based cohort differs')
        for sid,row in rows.items():
            raw_case=by_id[sid]
            case=next(c for c in cases if c['id']==sid)
            require(raw_case['fix_commit_hash']==case['bfc'],'Historical BFC differs')
            counts=score(raw_case['inducing_commit_hash'],oracles[sid])
            require(counts=={k:row[k] for k in counts},'Historical score drift: '+record['method']+'/'+sid)
        rule_checked[record['method']]=len(rows)

    ra=load(ROOT/'results/raw/ra-szz-star/extended-timeout/summary.json')
    ra_rows={r['sample_id']:r for r in current['rows'] if r['method']=='RA-SZZ*'}
    for entry in ra['rows']:
        sid=entry['sample_id']
        selected=Path(entry['selected_attempt']).with_name('result.json')
        path=relocated(selected)
        match=[a for a in entry['attempts'] if Path(a['path'])==selected]
        require(len(match)==1 and sha(path)==match[0]['sha256'],'RA-SZZ source differs')
        result=load(path)
        if entry['status']=='success':
            files=[relocated(p) for p in result['artifacts'] if '/out/' in p and p.endswith('.json')]
            require(len(files)==1,'RA-SZZ output missing')
            _,pred=validate_official_output(load(files[0]),repository=result['repository'],fix_hash=result['fix_commit_hash'])
            require(pred==entry['predictions'],'RA-SZZ selection changed')
        else:
            pred=[]
        require(score(pred,oracles[sid])=={k:ra_rows[sid][k] for k in ('tp','fp','fn')},'RA-SZZ score differs')

    census_calls={(r['slot_id'],r['call_index']):r for r in data('census')['calls']}
    bash=0
    for r in data('rq2')['runs']:
        calls=trace.extract_tool_calls(trace.transcript_events(relocated(r['transcript_path'])))
        require(len(calls)==len(r['calls']),'Missing RQ2 call')
        for index,(raw,selected) in enumerate(zip(calls,r['calls']),1):
            require(raw['tool_name']=='Bash' and raw['tool_use_id']==selected['tool_use_id'] and raw['input']['command']==selected['command'],'RQ2 command drift')
            items,_=commands.split_commands(raw['input']['command'],r['slot_id'],raw['tool_use_id'])
            equivalent(items,census_calls[(r['slot_id'],index)]['invocations'],'shell-extraction')
        bash+=len(calls)

    free={(r['sample_id'],r['repeat']):r['score'] for r in data('free-scores')['rows']}
    for r in data('messages')['rows']:
        events=trace.transcript_events(relocated(r['run_dir'])/'transcript.jsonl')
        end=trace.final_result_event(events)
        calls=trace.extract_tool_calls(events)
        require(len(calls)==r['bash_calls'],'Ablation call count drift')
        written=sum(len(commands.split_commands(c['input']['command'],r['slot_id'] if r['condition']=='present' else '',c['tool_use_id'])[0]) for c in calls)
        require(written==r['written_commands'],'Ablation command count drift')
        for key in ('input_tokens','output_tokens','cache_read_input_tokens'):
            require(end['usage'][key]==r['usage'][key],'Token count drift')
        if r['condition']=='free':
            s=free[(r['sample_id'],r['repeat'])]
            require(not s['unresolved'],'Unresolved hash mapping')
            normalized(answers.extract_bic_hashes(end['result']),s['predicted_new'])
            counts=score(s['predicted_original'],oracles[r['sample_id']])
            require(counts=={k:r[k] for k in counts},'Ablation score drift')
    return dict(validated_saved_answers=dict(checked),unresolved_scored_empty=missing,
                rq2_runs=237,rq2_bash_calls=bash,ablation_transcripts=474,
                ra_szz_saved_successes=ra['success'],ra_szz_saved_failures=ra['selected_failed'],
                historical_rule_based_answers=rule_checked,
                boundaries='Full hashes use saved resolution records. Manual labels are reapplied, not independently re-reviewed.')
