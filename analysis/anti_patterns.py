"""Recompute candidate availability in the reviewed DIO-V difference sets."""
from collections import defaultdict
from common import ROOT,data,load,require,relocated
from stats import candidate_evidence


def validate():
    dio=data('dio')
    labels={r['sample_id']:r['revised_oracle_bic_hash'] for r in load(ROOT/'dataset/dio-verified/dataset.json')['cases']}
    only={r['baseline']:r['case_ids']['claude_only'] for r in dio['comparisons']}
    llm=[]
    seen=defaultdict(list)
    for row in data('resources')['rows']:
        if row['method']!='LLM4SZZ' or row['sample_id'] not in only['LLM4SZZ']:continue
        raw=load(relocated(row['run_dir'])/'prediction.json')
        stages,assessed=candidate_evidence(load(relocated(raw['raw_result'])))
        candidates=set().union(*map(set,stages.values()))
        present=labels[row['sample_id']] in candidates
        seen[row['sample_id']].append(present)
        llm.append(dict(case=row['sample_id'],slot_id=row['slot_id'],candidates=sorted(candidates),
                        oracle_present=present,assessed=assessed))
    require(set(seen)==set(only['LLM4SZZ']) and all(len(v)==3 for v in seen.values()),'Missing LLM4SZZ review')
    absent=sorted((sid for sid,v in seen.items() if not any(v)),key=int)
    require(absent==dio['llm4szz_candidates']['absent_all_three'],'LLM4SZZ candidate availability changed')

    review=load(ROOT/'analysis/anti-patterns/review.json')
    simple_absent=[]
    for row in review['candidate_reviews']:
        sid=row['case']
        require(sid in only[row['method']],'Review outside current overlap')
        if row['method']=='Simple-SZZ-Agent':
            if all(labels[sid] not in r['history_candidates'] for r in row['runs']):simple_absent.append(sid)
            for r in row['runs']:
                record=load(relocated(r['raw_result_path']))
                raw=record['results'][0]
                details=(record.get('details') or record.get('stage2_details') or [{}])[0]
                require(set(raw['predicted_bics'])==set(r['prediction']),'Simple-SZZ saved answer differs')
                require(details['total_candidates']==len(r['history_candidates']),'Simple-SZZ history size differs')
                original_present=bool(set(details['ground_truth_bics']) & set(r['history_candidates']))
                require(details['gt_in_candidates']==original_present,'Simple-SZZ candidate membership differs')
        if row['method']=='SZZ-Agent' and sid in ('1991','2529','3459'):
            require(len(row['runs'])==3 and all(not r['stage2_executed'] and labels[sid] not in r['stage1']['szz_candidates'] for r in row['runs']),
                    'SZZ-Agent stopping observation differs')
    require(set(simple_absent)=={'624','1656','3459'},'Simple-SZZ missing candidate set differs')
    return dict(llm4szz=dict(claude_only_cases=len(only['LLM4SZZ']),absent_all_three=absent,runs=llm),
                simple_szz_agent=dict(claude_only_cases=len(only['Simple-SZZ-Agent']),absent_all_three=sorted(simple_absent,key=int)),
                szz_agent_stage1_stopping_cases=['1991','2529','3459'],
                agent_szz_review_cases=['1656','1991','2529'])
