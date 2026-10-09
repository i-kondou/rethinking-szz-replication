#!/usr/bin/env python3
"""Compile immutable historical sources and run a bounded recording harness."""
import argparse, hashlib, json, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
IMPL=HERE.parents[2]
REPO=IMPL/'experiments/repos/apache/bookkeeper'
CACHE=IMPL.parents[1]/'bic-redefinition/implementation/cache/m2'
DEPS=[CACHE/'com/google/guava/guava/20.0/guava-20.0.jar',
      CACHE/'commons-lang/commons-lang/2.6/commons-lang-2.6.jar',
      CACHE/'org/slf4j/slf4j-api/1.7.25/slf4j-api-1.7.25.jar']
POINTS={'c1':'6cfecea6c3','c2_parent':'25c113f62a^','c2':'25c113f62a',
        'oracle_parent':'e33ec10aa4^','oracle':'e33ec10aa4',
        'bfc_parent':'477ff2b594^','bfc':'477ff2b594'}

def git(*args):
    return subprocess.check_output(['git','-C',str(REPO),*args])
def sha(data): return hashlib.sha256(data).hexdigest()
def save(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def command(argv,cwd,record,timeout):
    try:
        p=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=timeout)
        data=dict(command=argv,cwd=str(cwd),exit=p.returncode,stdout=p.stdout,stderr=p.stderr,timeout=False)
    except subprocess.TimeoutExpired as exc:
        data=dict(command=argv,cwd=str(cwd),exit=None,stdout=str(exc.stdout),stderr=str(exc.stderr),timeout=True)
    save(record,data)
    if data['exit']!=0: raise RuntimeError('diagnostic failed; inspect '+str(record))
    return data

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args()
    if Path(a.output).name!=a.output: raise ValueError('use one new directory name')
    for d in DEPS: assert d.is_file(),d
    out=HERE/a.output;out.mkdir(exist_ok=False)
    save(out/'dependencies.json',[dict(path=str(d),sha256=sha(d.read_bytes())) for d in DEPS])
    save(out/'driver-inputs.json',[dict(path=str(p),sha256=sha(p.read_bytes())) for p in [Path(__file__),HERE/'Probe.java.in',HERE/'PLAN.md']])
    command(['/usr/bin/java','-version'],out,out/'java-version.json',10)
    command(['/usr/bin/javac','-version'],out,out/'javac-version.json',10)
    cp=':'.join(map(str,DEPS));manifest=[];rows=[]
    for point,ref in POINTS.items():
        revision=git('rev-parse',ref).decode().strip()
        paths=git('ls-tree','-r','--name-only',revision).decode().splitlines()
        newer=point.startswith('bfc')
        pkg='org.apache.bookkeeper.common.util' if newer else 'org.apache.bookkeeper.util'
        base='bookkeeper-common/src/main/java/' if newer else 'bookkeeper-server/src/main/java/'
        name='OrderedScheduler' if newer else 'OrderedSafeExecutor'
        selected=[base+pkg.replace('.','/')+'/'+n+'.java' for n in [name,'SafeRunnable','MathUtils']]
        if newer: selected.append(base+pkg.replace('.','/')+'/BoundedScheduledExecutorService.java')
        stats=['StatsLogger','OpStatsLogger','OpStatsData','Counter','Gauge','NullStatsLogger']
        selected.extend(next(p for p in paths if p.endswith('/stats/'+n+'.java')) for n in stats)
        root=out/point;src=root/'sources';classes=root/'classes';classes.mkdir(parents=True)
        files=[]
        for path in selected:
            blob=git('show',revision+':'+path);target=src/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(blob)
            manifest.append(dict(point=point,revision=revision,path=path,sha256=sha(blob),snapshot=str(target.relative_to(out))))
            files.append(str(target))
        if not newer:
            callback=src/'diagnostic/org/apache/bookkeeper/proto/BookkeeperInternalCallbacks.java'
            callback.parent.mkdir(parents=True,exist_ok=True)
            callback.write_text('package org.apache.bookkeeper.proto; public final class BookkeeperInternalCallbacks { public interface GenericCallback<T> { void operationComplete(int rc, T result); } }\n')
            files.append(str(callback))
        driver=src/'diagnostic/Probe.java';driver.parent.mkdir(parents=True,exist_ok=True)
        driver.write_text((HERE/'Probe.java.in').read_text().replace('@PKG@',pkg).replace('@EXEC@',name).replace('@BUILDER@','newSchedulerBuilder' if newer else 'newBuilder'));files.append(str(driver))
        save(out/'source-manifest.json',manifest)
        command(['/usr/bin/javac','--release','8','-proc:none','-cp',cp,'-d',str(classes),*files],root,out/(point+'-compile.json'),60)
        for mode in ['object','long','int']:
            for trace in [True,False]:
                for repeat in [1,2]:
                    label=f'{point}-{mode}-trace{str(trace).lower()}-r{repeat}'
                    raw=command(['/usr/bin/java','-Xmx128m','-cp',str(classes)+':'+cp,'Probe',mode,str(trace).lower()],root,out/(label+'.json'),10)
                    observed=json.loads(raw['stdout'].strip());assert observed['task_count']==1
                    rows.append(dict(point=point,revision=revision,repeat=repeat,raw=label+'.json',**observed))
                    save(out/'observations.json',rows)
        print(point,'completed',flush=True)
    print(json.dumps(dict(points=len(POINTS),executions=len(rows))))

if __name__=='__main__': main()
