#!/usr/bin/env python3
"""Acquire pinned fork source and bounded compile dependencies, without a full build."""
import hashlib, json, urllib.request, zipfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
REV = '02d52f582e054685dbaec3c1735128f91cc6a4b8'
COORDS = [
 ('junit','junit','4.13'), ('org.hamcrest','hamcrest','2.2'),
 ('commons-io','commons-io','2.6'), ('org.apache.commons','commons-lang3','3.9'),
 ('org.apache.commons','commons-text','1.8'), ('org.codehaus.plexus','plexus-utils','3.1.0'),
 ('org.freemarker','freemarker','2.3.28'), ('com.thoughtworks.paranamer','paranamer','2.8'),
 ('com.thoughtworks.xstream','xstream','1.4.9'), ('com.google.code.gson','gson','2.8.5'),
 ('com.google.guava','guava','28.2-jre'), ('org.codehaus.groovy','groovy','2.5.8'),
 ('javax.inject','javax.inject','1'), ('org.reflections','reflections','0.9.11'),
 ('org.slf4j','slf4j-api','2.0.0-alpha1')]

def main():
 rows=[]
 def get(url, path):
  path.parent.mkdir(parents=True,exist_ok=True)
  if not path.exists():
   with urllib.request.urlopen(url,timeout=30) as r: data=r.read()
   path.write_bytes(data)
  data=path.read_bytes()
  rows.append(dict(url=url,file=str(path.relative_to(HERE)),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
  print(path.name,len(data),flush=True)
  return data
 archive=HERE/'dependencies'/'jbehave-alpha2-source.zip'
 get(f'https://codeload.github.com/vividus-framework/jbehave-core/zip/{REV}',archive)
 out=HERE/'fork-source'
 with zipfile.ZipFile(archive) as z:
  for m in z.infolist():
   rest='/'.join(m.filename.split('/')[1:])
   if m.is_dir() or not (rest.startswith('jbehave-core/src/main/') or rest in ['pom.xml','jbehave-core/pom.xml']): continue
   p=out/rest
   assert p.resolve().is_relative_to(out.resolve())
   p.parent.mkdir(parents=True,exist_ok=True)
   content=z.read(m)
   if p.exists(): assert p.read_bytes()==content
   else: p.write_bytes(content)
 for g,a,v in COORDS:
  name=f'{a}-{v}.jar'
  get(f'https://repo.maven.apache.org/maven2/{g.replace(".","/")}/{a}/{v}/{name}', HERE/'dependencies'/name)
 for name,url in [('fix-pr.json','https://api.github.com/repos/vividus-framework/vividus/pulls/297'),('fork-tag.json','https://api.github.com/repos/vividus-framework/jbehave-core/git/tags/832607fe2ecfcef2e1171422d8e4f68f19baacf1')]:
  get(url,HERE/'upstream'/name)
 manifest=HERE/'acquisition-exact.json'
 if manifest.exists(): assert json.loads(manifest.read_text())==rows
 else: manifest.write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__': main()
