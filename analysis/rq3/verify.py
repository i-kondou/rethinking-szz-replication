"""Check classification and the saved reproduction evidence supporting RQ3."""
from collections import Counter
from itertools import product
import re
from common import ROOT,data,load,require,sha
from rq3.checks import check_bookkeeper,check_vividus,check_candidate_tests

HERE=ROOT/'analysis/rq3'


def validate():
    source=load(HERE/'classification.json')
    require(dict(Counter(r['category'] for r in source['cases']))==source['counts'],'RQ3 categories differ')
    disagreement={r['sample_id'] for r in data('rq1')['rows'] if r['method']=='Claude Code' and (r['fp'] or r['fn'])}
    require({r['case_id'] for r in source['cases']}==disagreement and len(disagreement)==22,'RQ3 cohort differs')
    for path in (HERE/'tests/history/runs').rglob('source-manifest.json'):
        for row in load(path):
            blob=path.parent/'sources'/row['path']
            require(sha(blob)==row['sha256'],'Changed source snapshot: '+str(blob))
    for sid in ('907','1121','1381','1728','2557','2911','3530'):
        patches=load(HERE/'patches'/f'{sid}.json')['records']
        require(len(patches)>=3 and all(not r.get('unavailable') for r in patches),'Incomplete patch evidence '+sid)

    alarm=HERE/'tests/313/run'
    rows=load(alarm/'records.json')
    expected=set(product(('candidate','split_parent','split','oracle_parent','oracle','fix_parent','fix'),
                         ('past_two_disabled','future_two_disabled','past_two_enabled','past_one_disabled','zero_two_disabled'),(1,2,3)))
    require(len(rows)==105 and {(r['point'],r['scenario'],r['replicate']) for r in rows}==expected,'Incomplete AlarmClock matrix')
    for row in rows:
        raw=(alarm/row['stdout']).read_text()
        require(row['exit_code']==0 and f"RESULT outcome={row['outcome']}" in raw,'AlarmClock result differs')
        if row['scenario']=='past_two_disabled':
            failure=row['point'] in ('oracle','fix_parent')
            require(row['outcome']==('java.util.ConcurrentModificationException' if failure else 'normal'),'AlarmClock boundary differs')

    for sid,name in [('399','defaultPortWithAuth'),('717','addbootcpWithDefaultBase')]:
        for point,repeat in product(('I_parent','I','F'),(1,2,3)):
            group='usage-fp-01' if point=='F' else 'usage-history-01'
            raw=load(HERE/f'tests/history/runs/claude-candidates-usage-20260912/{group}/{sid}/{point}/test-{repeat}.json')
            require(not raw['timeout'] and raw['returncode'] in (0,1) and 'MEASURE tests=' in raw['stdout'],'Incomplete JUnit test')
            require((f'FAILURE_TEST={name}(' in raw['stdout'])==(point=='I'),'Trigger boundary differs: '+sid)

    spoon=HERE/'tests/2513/original-test'
    rows=load(spoon/'summary.json')
    require(len(rows)==16 and {(r['point'],r['repeat']) for r in rows}==set(product(('F','P','C1_parent','C1','I_parent','I','C2_parent','C2'),(1,2))),'Incomplete Spoon matrix')
    for row in rows:
        raw=load(spoon/row['point']/f"r{row['repeat']}"/'execution.json')
        failure=row['point'] in ('P','C2')
        require(not raw['timeout'] and raw['returncode'] in (0,1),'Spoon did not complete')
        require(f"RESULT runs=1 failures={int(failure)} ignored=0" in raw['stdout'],'Spoon boundary differs')
        require(row['status']==('target_self_import_failure' if failure else 'pass'),'Spoon status differs')
        for generated in row['generated']:
            require(sha(spoon/generated['path'])==generated['sha256'],'Spoon output changed')
    proof=load(HERE/'tests/2513/source-check/verification.json')
    require(all(proof['method_bytecode_matches_original_source'].values()),'Original Spoon test not verified')
    return dict(classification=source['counts'],alarmclock_tests=105,spoon_tests=16,
                trigger_boundary_processes=18,bookkeeper=check_bookkeeper(),
                vividus=check_vividus(),oracle_boundary_tests=check_candidate_tests())
