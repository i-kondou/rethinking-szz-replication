#!/usr/bin/env python3
"""Verify saved observations and immutable sources without rerunning tasks."""
import argparse, hashlib, itertools, json, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]/'experiments/repos/apache/bookkeeper'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',default='attempt002');ap.add_argument('--output',required=True);args=ap.parse_args()
    assert Path(args.attempt).name==args.attempt and Path(args.output).name==args.output
    root=HERE/args.attempt;out=HERE/args.output;out.mkdir(exist_ok=False)
    rows=read(root/'observations.json')
    points=['c1','c2_parent','c2','oracle_parent','oracle','bfc_parent','bfc']
    keys={(r['point'],r['mode'],r['trace'],r['repeat']) for r in rows}
    assert len(rows)==len(keys)==84
    assert keys==set(itertools.product(points,['object','long','int'],[True,False],[1,2]))
    manifest=read(root/'source-manifest.json')
    for item in manifest:
        snapshot=root/item['snapshot'];assert sha(snapshot)==item['sha256']
        original=subprocess.check_output(['git','-C',str(REPO),'show',item['revision']+':'+item['path']])
        assert hashlib.sha256(original).hexdigest()==item['sha256']
    for item in read(root/'dependencies.json')+read(root/'driver-inputs.json'):
        assert sha(Path(item['path']))==item['sha256']
    for r in rows:
        raw=read(root/r['raw']);assert raw['exit']==0 and not raw['timeout']
        parsed=json.loads(raw['stdout'])
        assert all(r[k]==v for k,v in parsed.items())
        assert r['task_count']==1 and r['elapsed_nanos']>0
        wrapped=r['trace'] and (r['point'] in ['c1','c2_parent','bfc'] or r['mode']=='object')
        assert len(r['queued_nanos'])==len(r['execution_nanos'])==int(wrapped)
        if wrapped:
            assert r['execution_nanos'][0]>=0
            assert r['queued_within_elapsed']==(r['point']=='bfc')
            if r['point']=='bfc': assert 0<=r['queued_nanos'][0]<=r['elapsed_nanos']
            else: assert r['queued_nanos'][0]>r['elapsed_nanos']
    for point in points:
        compile=read(root/(point+'-compile.json'));assert compile['exit']==0 and not compile['timeout']
        argv=['/usr/bin/javap','-c','-classpath',str(root/point/'classes'),'Probe']
        p=subprocess.run(argv,capture_output=True,text=True,check=True)
        save(out/(point+'-driver-bytecode.json'),dict(argv=argv,stdout=p.stdout,stderr=p.stderr,exit=p.returncode))
        calls=[line.strip() for line in p.stdout.splitlines() if '// Method' in line and '.submitOrdered:' in line]
        assert len(calls)==3
        save(out/(point+'-submit-calls.json'),calls)
        if point in ['c1','c2_parent']:
            assert all('(Ljava/lang/Object;' in line for line in calls)
        else:
            assert '(Ljava/lang/Object;' in calls[0] and '(J' in calls[1] and '(I' in calls[2]
    old='bookkeeper-server/src/main/java/org/apache/bookkeeper/util/OrderedSafeExecutor.java'
    new='bookkeeper-common/src/main/java/org/apache/bookkeeper/common/util/OrderedScheduler.java'
    evidence={
        'c1.patch':['show','--format=fuller','6cfecea6c3','--',old],
        'c2.patch':['show','--format=fuller','25c113f62a','--',old],
        'oracle.patch':['show','--format=fuller','e33ec10aa4','--',old],
        'bfc.patch':['show','--format=fuller','477ff2b594','--',new],
        'c1-parent.java.txt':['show','6cfecea6c3^:'+old],
        'bfc-developer-test.java.txt':['show','477ff2b594:bookkeeper-server/src/test/java/org/apache/bookkeeper/test/OpStatTest.java']}
    for name,argv in evidence.items():
        (out/name).write_bytes(subprocess.check_output(['git','-C',str(REPO),*argv]))
    c1parent=(out/'c1-parent.java.txt').read_text()
    assert 'TimedRunnable' not in c1parent and 'taskPendingStats' not in c1parent
    checks={'attempt':args.attempt,'executions':len(rows),'trace_true':sum(r['trace'] for r in rows),
        'trace_false':sum(not r['trace'] for r in rows),'source_snapshots':len(manifest),
        'source_sha_match':True,'raw_summary_match':True,'one_task_each':True,
        'expected_measurement_counts':True,'expected_queue_bound':True,'overload_bytecode_match':True,
        'c1_parent_no_timing_feature':True,
        'observations_sha256':sha(root/'observations.json'),'verifier_sha256':sha(Path(__file__)),
        'evidence_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()}}
    save(out/'verification.json',checks);print(json.dumps(checks,ensure_ascii=False))

if __name__=='__main__': main()
