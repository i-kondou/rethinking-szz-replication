#!/usr/bin/env python3
"""Rebuild archived AlarmClock classes and replay all 105 tests; no downloads."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from common import ROOT,load,save,require,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    out=args.output.resolve()
    require(out.is_relative_to(ROOT/'outputs') and not out.exists(),'Use a fresh directory under outputs/')
    java,javac=shutil.which('java'),shutil.which('javac')
    require(java and javac,'A Java JDK is required')
    archive=ROOT/'analysis/rq3/tests/313'
    manifest=load(archive/'run/manifest.json')
    expected=load(archive/'run/records.json')
    out.mkdir(parents=True)
    observed=[]
    for point,details in manifest['points'].items():
        dest=out/point;classes=dest/'classes';classes.mkdir(parents=True)
        sources=[]
        for name,record in details['sources'].items():
            path=archive/'run'/point/name
            require(sha(path)==record['sha256'],'Changed source '+name)
            sources.append(path)
        sources+=sorted((archive/'support').rglob('*.java'))
        command=[javac,'-encoding','UTF-8','-d',str(classes),*map(str,sources)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=60)
        save(dest/'compile.json',dict(command=command,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
        require(result.returncode==0,'Compile failed for '+point)
        for row in (r for r in expected if r['point']==point):
            command=[java,'-Duser.timezone=UTC','-cp',str(classes),'com.better.alarm.model.Replay',row['scenario']]
            result=subprocess.run(command,capture_output=True,text=True,timeout=30)
            require(result.returncode==0 and f"RESULT outcome={row['outcome']}" in result.stdout,'Behavior differs: '+point+'/'+row['scenario'])
            record=dict(point=point,scenario=row['scenario'],replicate=row['replicate'],
                        command=command,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
            save(dest/f"{row['scenario']}-r{row['replicate']}.json",record)
            observed.append(dict(point=point,scenario=row['scenario'],repeat=row['replicate'],outcome=row['outcome']))
    require(len(observed)==105,'Incomplete replay')
    save(out/'summary.json',dict(model_calls=0,tests=observed))
    print('Recompiled and matched all 105 archived outcomes.')


if __name__=='__main__':main()
