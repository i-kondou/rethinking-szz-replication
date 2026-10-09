#!/usr/bin/env python3
"""Offline, whole-class JVM replay; Android services are explicit test doubles."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SUBJECT = REPO / 'experiments/repos/yuriykulikov/AlarmClock'
POINTS = [('candidate','54a35c3'),('split_parent','52d8630^'),('split','52d8630'),
          ('oracle_parent','49d5841^'),('oracle','49d5841'),('fix_parent','fc1d53f^'),('fix','fc1d53f')]
INPUTS = ['past_two_disabled','future_two_disabled','past_two_enabled','past_one_disabled','zero_two_disabled']

def sha(b): return hashlib.sha256(b).hexdigest()
def git(*args): return subprocess.check_output(['git','-C',str(SUBJECT),*args])
def snapshot(): return {'head':git('rev-parse','HEAD').decode().strip(),'status':git('status','--porcelain=v1').decode()}
def command(args, cwd, prefix):
    try:
        p=subprocess.run(args,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
        record={'command':list(map(str,args)),'returncode':p.returncode}
        prefix.with_suffix('.stdout').write_bytes(p.stdout)
        prefix.with_suffix('.stderr').write_bytes(p.stderr)
    except subprocess.TimeoutExpired as e:
        prefix.with_suffix('.stdout').write_bytes(e.stdout or b'')
        prefix.with_suffix('.stderr').write_bytes(e.stderr or b'')
        record={'command':list(map(str,args)),'returncode':None,'timeout':True}
    prefix.with_suffix('.command.json').write_text(json.dumps(record,indent=2)+'\n')
    return record

def main():
    p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);args=p.parse_args()
    if not re.fullmatch(r'attempt[0-9]{3}',args.attempt):p.error('use attemptNNN')
    out=HERE/'runs'/args.attempt;out.mkdir(parents=True,exist_ok=False)
    before=snapshot();(out/'subject-before.json').write_text(json.dumps(before,indent=2)+'\n')
    command(['/usr/bin/java','-version'],out,out/'java-version')
    command(['/usr/bin/javac','-version'],out,out/'javac-version')
    manifest={'points':{},'inputs':INPUTS,'repeats':3,'source_policy':'unmodified full Git blobs',
              'support':{str(f.relative_to(HERE)):sha(f.read_bytes()) for f in [HERE/'run.py',HERE/'README.md',*sorted((HERE/'support').rglob('*.java'))]}}
    records=[]
    try:
        for label,ref in POINTS:
            rev=git('rev-parse',ref).decode().strip();work=out/label;work.mkdir()
            paths=git('ls-tree','-r','--name-only',rev,'src/com/better/alarm/model').decode().splitlines()
            names=['Alarm.java','IAlarmsManager.java','Intents.java','IAlarmsScheduler.java']
            names.append('Alarms.java' if any(x.endswith('/Alarms.java') for x in paths) else 'AlarmsManager.java')
            sources={}
            for path in paths:
                if Path(path).name not in names:continue
                blob=git('show',rev+':'+path);dest=work/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob)
                sources[path]={'git_blob':git('rev-parse',rev+':'+path).decode().strip(),'sha256':sha(blob)}
            manifest['points'][label]={'commit':rev,'sources':sources}
            classes=work/'classes';classes.mkdir()
            source_files=sorted((work/'src').rglob('*.java'))+sorted((HERE/'support').rglob('*.java'))
            c=command(['/usr/bin/javac','-encoding','UTF-8','-d',str(classes),*map(str,source_files)],work,work/'compile')
            if c['returncode']!=0:raise RuntimeError('compile failed: '+label+'; inspect '+str(work/'compile.stderr'))
            for scenario in INPUTS:
                for replicate in range(1,4):
                    prefix=work/f'{scenario}-r{replicate:02d}'
                    r=command(['/usr/bin/java','-Duser.timezone=UTC','-cp',str(classes),'com.better.alarm.model.Replay',scenario],work,prefix)
                    data={}
                    for line in prefix.with_suffix('.stdout').read_text().splitlines():
                        if line.startswith('RESULT '):
                            k,v=line[7:].split('=',1);data[k]=v
                    record={'point':label,'scenario':scenario,'replicate':replicate,'exit_code':r['returncode'],**data,
                            'stdout':str(prefix.with_suffix('.stdout').relative_to(out)),'stderr':str(prefix.with_suffix('.stderr').relative_to(out))}
                    records.append(record)
                    if r['returncode']!=0 or data.get('outcome') not in ['normal','java.util.ConcurrentModificationException']:
                        raise RuntimeError('unexpected replay failure: '+str(record))
            print(label,rev[:10],[(s,next(x['outcome'] for x in records if x['point']==label and x['scenario']==s)) for s in INPUTS],flush=True)
    finally:
        after=snapshot();manifest['subject_before']=before;manifest['subject_after']=after
        (out/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
        manifest['artifacts']={str(f.relative_to(out)):sha(f.read_bytes()) for f in sorted(out.rglob('*')) if f.is_file() and 'classes' not in f.parts}
        (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        if before!=after:raise RuntimeError('subject checkout changed')
    assert len(records)==105
    print('Completed 105 fresh-JVM replays; classify observed outcomes separately from interpretation.')

if __name__=='__main__':main()
