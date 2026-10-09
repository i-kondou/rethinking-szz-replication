"""Run an unchanged cached developer test on existing full-source Spoon builds."""
import hashlib,json,os,subprocess,time
from pathlib import Path
B=Path('/Users/user-01/research/workspaces/bic-redefinition/implementation')
OUT=Path(__file__).resolve().parent
M=B/'config/java-causal-expansion-20260912/matrix-v1.json'
cfg=json.loads(M.read_text());case=cfg['cases'][0]
deps=[B/d['path'] for d in cfg['common_dependencies']+case['dependencies']]
jdk=Path(cfg['java_home']);testclasses=B/'work/candidate16-2513-F-03/repo/target/test-classes'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(p):return {str(x.relative_to(p)):digest(x) for x in sorted(p.rglob('*')) if x.is_file()}
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def command(argv,cwd,dest):
    t=time.monotonic()
    try:
        p=subprocess.run([str(v) for v in argv],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
        row={'argv':[str(v) for v in argv],'cwd':str(cwd),'returncode':p.returncode,'timeout':False,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace')}
    except subprocess.TimeoutExpired as e:
        row={'argv':[str(v) for v in argv],'cwd':str(cwd),'returncode':None,'timeout':True,'stdout':(e.stdout or b'').decode(errors='replace'),'stderr':(e.stderr or b'').decode(errors='replace')}
    row['seconds']=time.monotonic()-t;dump(dest,row);return row
def main():
    run=OUT/'spoon-original-test-01';assert not run.exists();run.mkdir()
    assert case['id']==2513
    for dep,path in zip(cfg['common_dependencies']+case['dependencies'],deps):assert digest(path)==dep['sha256']
    tc=inventory(testclasses);assert 'spoon/test/variable/AccessFullyQualifiedFieldTest.class' in tc
    driver=run/'driver';driver.mkdir()
    cc=command([jdk/'bin/javac','-proc:none','-cp',os.pathsep.join(map(str,deps)),'-d',driver,OUT/'OneMethod.java'],run,run/'compile-driver.json');assert cc['returncode']==0
    dump(run/'provenance.json',{'matrix':str(M),'matrix_sha256':digest(M),'protocol_sha256':digest(OUT/'protocol.md'),'script_sha256':digest(Path(__file__)),'driver_sha256':digest(OUT/'OneMethod.java'),'testclasses_root':str(testclasses),'testclasses':tc,'dependencies':[{'path':str(p),'sha256':digest(p)} for p in deps],'java_sha256':digest(jdk/'bin/java'),'no_network_or_model':True})
    rows=[]
    for point in ['F','P','C1_parent','C1','I_parent','I','C2_parent','C2']:
        baseid='expansion-fp-01' if point in ['F','P'] else 'expansion-history-01'
        base=B/'runs/java-causal-expansion-20260912'/baseid/'2513'/point
        meta=json.loads((base/'outcome.json').read_text());assert meta['revision']==case['revisions'][point] and meta['compile_status']=='pass'
        classes=B/'work/java-causal-expansion-20260912'/baseid/'2513'/point/'classes'
        inv=inventory(classes);assert inv
        pointdir=run/point;pointdir.mkdir();dump(pointdir/'binary-inputs.json',{'revision':meta['revision'],'main_classes':inv,'origin':str(base),'origin_outcome_sha256':digest(base/'outcome.json'),'origin_source_manifest_sha256':digest(base/'source-manifest.json')})
        cp=os.pathsep.join(map(str,[driver,classes,testclasses]+deps))
        for repeat in [1,2]:
            cwd=pointdir/('r%d'%repeat);cwd.mkdir();(cwd/'tmp').mkdir();(cwd/'home').mkdir()
            fixtures=cwd/'src/test/java/spoon/test/variable/testclasses/digest';fixtures.mkdir(parents=True)
            for name in ['DigestUtil.java','MessageDigest.java']:
                path='src/test/java/spoon/test/variable/testclasses/digest/'+name
                raw=subprocess.check_output(['git','-C',case['repo'],'show',case['revisions']['F']+':'+path]);(fixtures/name).write_bytes(raw)
            rr=command([jdk/'bin/java','-Xmx512m','-ea','-Djava.awt.headless=true','-Duser.language=en','-Duser.country=US','-Duser.timezone=UTC','-Duser.home='+str(cwd/'home'),'-Djava.io.tmpdir='+str(cwd/'tmp'),'-cp',cp,'OneMethod'],cwd,cwd/'execution.json')
            status='unknown'
            if rr['returncode']==0 and 'RESULT runs=1 failures=0 ignored=0' in rr['stdout']:status='pass'
            elif 'java.lang.AssertionError: The result should not contain a static import for STREAM_BUFFER_LENGTH' in rr['stdout'] and 'RESULT runs=1 failures=1 ignored=0' in rr['stdout']:status='target_self_import_failure'
            generated=[{'path':str(p.relative_to(run)),'sha256':digest(p),'has_forbidden_import':'import static spoon.test.variable.testclasses.digest.DigestUtil.STREAM_BUFFER_LENGTH;' in p.read_text()} for p in cwd.rglob('target/**/DigestUtil.java')]
            rows.append({'point':point,'revision':meta['revision'],'repeat':repeat,'status':status,'log':str((cwd/'execution.json').relative_to(OUT)),'generated':generated});dump(run/'summary.json',rows);print(point,repeat,status,flush=True)
            if point in ['F','P'] and status!=('pass' if point=='F' else 'target_self_import_failure'):
                dump(run/'stopped.json',{'reason':'F/P control not satisfied','point':point,'repeat':repeat});assert inv==inventory(classes) and tc==inventory(testclasses);return
        assert inv==inventory(classes)
    assert tc==inventory(testclasses);dump(run/'verified.json',{'binary_inputs_unchanged':True,'tests_selected':len(rows)})
if __name__=='__main__':main()
