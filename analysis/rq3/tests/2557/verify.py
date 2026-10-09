#!/usr/bin/env python3
"""Independent readback of recorded outcomes and original-source provenance."""
import hashlib, json, re, subprocess, argparse, zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]/'experiments/repos/vividus-framework/vividus'

def main():
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
 run=HERE/'attempt04';sources=json.loads((run/'source-manifest.json').read_text())
 for s in sources:
  blob=subprocess.check_output(['git','-C',str(REPO),'show',s['revision']+':'+s['path']])
  assert hashlib.sha256(blob).hexdigest()==s['sha256']
  assert (run/s['point']/'sources'/s['path']).read_bytes()==blob
 for d in json.loads((run/'dependencies.json').read_text()):
  assert hashlib.sha256(Path(d['path']).read_bytes()).hexdigest()==d['sha256']
 for manifest in ['acquisition.json','acquisition-exact.json']:
  for r in json.loads((HERE/manifest).read_text()):
   if 'sha256' in r: assert hashlib.sha256((HERE/r['file']).read_bytes()).hexdigest()==r['sha256']
 fork=HERE/'fork-source/jbehave-core/src/main/java'
 with zipfile.ZipFile(HERE/'dependencies/jbehave-alpha2-source.zip') as archive:
  archived_java={}
  for name in archive.namelist():
   relative='/'.join(name.split('/')[1:])
   if relative.startswith('jbehave-core/src/main/java/') and relative.endswith('.java'):
    archived_java[relative]=archive.read(name)
  extracted_java={str(path.relative_to(HERE/'fork-source')):path.read_bytes() for path in fork.rglob('*.java')}
  assert extracted_java==archived_java
 compile_fork=json.loads((run/'compile-fork.json').read_text())
 assert compile_fork['exit']==0
 assert set(map(str,fork.rglob('*.java'))).issubset(set(compile_fork['command']))
 points=sorted({s['point'] for s in sources});assert len(points)==7
 matrix=[]
 for point in points:
  assert json.loads((run/(point+'-compile.json')).read_text())['exit']==0
  for mode in ['plain','parameter','examples']:
   for init in ['false','true']:
    for rep in [1,2]:
     name=f'{point}-{mode}-init{init}-r{rep}'
     data=json.loads((run/(name+'.json')).read_text());text=data['stdout']
     assert data['exit']==0 and not data.get('timeout')
     expect_error=mode=='examples' and init=='false' and point not in ['variables_parent','bfc']
     assert ('DESCRIPTION_ERROR' in text)==expect_error
     assert ('DESCRIPTION_OK' in text)!=expect_error
     counts=re.search(r'COUNTS beforeStory=(\d+) conversions=(\d+) stepExecutions=(\d+)',text)
     assert counts and counts.group(1)=='0' and counts.group(3)=='0'
     assert int(counts.group(2))==(1 if mode=='examples' else 0)
     if expect_error:
      for token in ['this.runningBatchKey','BddRunContext.getRunningBatchKey','VariablesFactory.createVariables','ParameterAdaptor.convert','PerformableTree.performableScenario','JUnitReportingRunner.createPerformableTree']:
       assert token in text
     matrix.append(dict(point=point,mode=mode,initialized=init=='true',repeat=rep,outcome='NPE' if expect_error else 'description_created'))
 for point in ['oracle_parent','bfc']:
  for rep in [1,2]:
   d=json.loads((run/f'{point}-execution-control-r{rep}.json').read_text())
   assert d['exit']==0 and 'EXECUTION_CONTROL_OK' in d['stdout']
   assert 'COUNTS beforeStory=3 conversions=1 stepExecutions=1' in d['stdout']
 summary=dict(passed=True,original_source_files_verified=len(sources),fork_java_sources_compiled=len(list(fork.rglob('*.java'))),matrix_executions=len(matrix),observed_target_npe=sum(r['outcome']=='NPE' for r in matrix),positive_control_executions=4)
 if a.record:
  assert not (HERE/'verification.json').exists()
  (HERE/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
  (HERE/'results.json').write_text(json.dumps(matrix,indent=2)+'\n')
 print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
