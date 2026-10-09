"""Validate DIO-V and rescore the unchanged saved answers."""
from common import ROOT,data,load,require,score


def validate():
    original={r['id']:r for r in load(ROOT/'dataset/metadata/cases.json')['cases']}
    verified={r['sample_id']:r for r in load(ROOT/'dataset/dio-verified/dataset.json')['cases']}
    classification=load(ROOT/'analysis/rq3/classification.json')
    ambiguous={r['case_id'] for r in classification['cases'] if r['category']=='Ambiguous or incomplete BIC'}
    excluded=ambiguous|{'1121','2557','2911'}
    require(set(verified)==set(original)-excluded and len(verified)==67,'DIO-V cohort changed')
    changed=set()
    for sid,row in verified.items():
        old=original[sid]
        require(row['repository']==old['repository'] and row['original_bfc_hash']==old['bfc'] and
                row['original_oracle_bic_hash']==old['oracle_bics'][0] and row['synthetic_bfc_hash']==old['synthetic_bfc'],
                'DIO-V source differs: '+sid)
        if row['revised_oracle_bic_hash']!=row['original_oracle_bic_hash']: changed.add(sid)
    require(changed=={'907','1381','1728','3530'},'DIO-V correction changed')
    sources={(r['method'],r['slot_id']):r for r in data('resources')['rows']}
    rows=data('dio')['rows']
    require(len(rows)==1005 and len({(r['method'],r['slot_id']) for r in rows})==1005,'Incomplete DIO-V grid')
    for row in rows:
        ref=sources.get((row['method'],row['slot_id']))
        predictions=ref['predictions'] if ref else []
        require(set(predictions)==set(row['predictions']),'DIO-V changed a saved answer')
        label=verified[row['sample_id']]['revised_oracle_bic_hash']
        require(score(predictions,[label])==row['revised'],'DIO-V score drift')
    return dict(cases=67,repositories=len({r['repository'] for r in verified.values()}),
                corrected=sorted(changed,key=int),excluded=sorted(excluded,key=int),rescored_answers=len(rows))


if __name__=='__main__':
    import json
    print(json.dumps(validate(),indent=2))
