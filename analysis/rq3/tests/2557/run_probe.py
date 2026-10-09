#!/usr/bin/env python3
"""Compile unmodified fork/VIVIDUS source, run bounded isolated JUnit construction."""
import argparse, hashlib, json, subprocess, time, shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]/'experiments/repos/vividus-framework/vividus'
POINTS={'variables_parent':'abfb232^','oracle_parent':'e083434^','oracle':'e083434','claude_parent':'024c71c^','claude':'024c71c','bfc_parent':'ebef05e999^','bfc':'ebef05e999'}
BDD='vividus-bdd-engine/src/main/java/org/vividus/bdd/'
FILES=[BDD+p+'.java' for p in ['context/BddRunContext','context/IBddRunContext','context/BddVariableContext','context/IBddVariableContext','model/RunningStory','model/RunningScenario','BatchedEmbedder','BatchedPerformableTree','ExtendedEmbedder','EmbedderControlsProvider','IEmbedderControlsProvider','IBatchStorage','resource/ResourceBatch','batch/BatchStorage','batch/BatchResourceConfiguration','batch/BatchExecutionConfiguration','variable/VariablesFactory','variable/IVariablesFactory','variable/Variables','variable/VariableScope','variable/DynamicVariable','steps/ParameterAdaptor','steps/ParameterConvertersDecorator','steps/ExpressionAdaptor','steps/SubSteps','steps/ISubStepsListener','expression/IExpressionProcessor']]
FILES += ['vividus-test-context/src/main/java/org/vividus/testcontext/'+p+'.java' for p in ['TestContext','SimpleTestContext']]
FILES += ['vividus-util/src/main/java/org/vividus/util/property/'+p+'.java' for p in ['IPropertyMapper','IPropertyParser']]

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--compile-only',action='store_true');args=p.parse_args()
 out=HERE/args.output
 assert out.resolve().is_relative_to(HERE.resolve())
 out.mkdir(exist_ok=False)
 shutil.copy2(__file__,out/'runner-snapshot.py');shutil.copy2(HERE/'Probe.java',out/'Probe.java')
 records=[]
 def run(cmd,name,timeout=60):
  start=time.monotonic()
  try:
   r=subprocess.run([str(x) for x in cmd],cwd=out,text=True,capture_output=True,timeout=timeout)
   row=dict(command=[str(x) for x in cmd],exit=r.returncode,stdout=r.stdout,stderr=r.stderr,seconds=time.monotonic()-start)
  except subprocess.TimeoutExpired as e:
   row=dict(command=[str(x) for x in cmd],exit=None,stdout=str(e.stdout),stderr=str(e.stderr),timeout=True)
  (out/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n');records.append(dict(name=name,**row))
  print(name,row['exit'],row['stdout'][-250:],row['stderr'][-1500:] if row['exit'] else '',flush=True)
  return row
 jars=sorted(p for p in (HERE/'dependencies').glob('*.jar') if 'sources' not in p.name and not p.name.startswith('jbehave-core'))
 cp=':'.join(str(p) for p in jars if p.name!='guava-20.0.jar');fork=HERE/'fork-source/jbehave-core/src/main/java'
 forkcp=':'.join(str(p) for p in jars if p.name!='guava-28.2-jre.jar')
 (out/'dependencies.json').write_text(json.dumps([{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in jars],indent=2)+'\n')
 classes=out/'fork-classes';classes.mkdir()
 sourcepaths=sorted(fork.rglob('*.java'))
 row=run(['javac','--release','11','-proc:none','-cp',forkcp,'-d',classes,*sourcepaths],'compile-fork')
 if row['exit']!=0: return
 resources=HERE/'fork-source/jbehave-core/src/main/resources'
 cp=f'{classes}:{resources}:{cp}'
 files=[]
 for label,ref in POINTS.items():
  sha=subprocess.check_output(['git','-C',str(REPO),'rev-parse',ref],text=True).strip()
  work=out/label;work.mkdir();dest=work/'classes';dest.mkdir()
  paths=[]
  for rel in FILES:
   r=subprocess.run(['git','-C',str(REPO),'show',f'{sha}:{rel}'],capture_output=True)
   if r.returncode: continue
   path=work/'sources'/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(r.stdout);paths.append(path)
   files.append(dict(point=label,revision=sha,path=rel,sha256=hashlib.sha256(r.stdout).hexdigest()))
  row=run(['javac','--release','11','-proc:none','-cp',cp,'-d',dest,*paths,HERE/'Probe.java'],label+'-compile')
  if row['exit']!=0: continue
  if not args.compile_only:
   for mode in ['plain','parameter','examples']:
    for init in ['false','true']:
     for repeat in [1,2]: run(['java','-cp',f'{dest}:{cp}','Probe',mode,init],f'{label}-{mode}-init{init}-r{repeat}')
   if label in ['oracle_parent','bfc']:
    for repeat in [1,2]: run(['java','-cp',f'{dest}:{cp}','Probe','plain','false','execute-control'],f'{label}-execution-control-r{repeat}')
 (out/'source-manifest.json').write_text(json.dumps(files,indent=2)+'\n')
 (out/'summary.json').write_text(json.dumps([{'name':r['name'],'exit':r['exit'],'ok':'DESCRIPTION_OK' in r['stdout'],'error':'DESCRIPTION_ERROR' in r['stdout'],'counts':[l for l in r['stdout'].splitlines() if l.startswith('COUNTS')]} for r in records],indent=2)+'\n')
if __name__=='__main__': main()
