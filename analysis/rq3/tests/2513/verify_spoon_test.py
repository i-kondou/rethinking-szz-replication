"""Recompile original BFC test source and compare used bytecode with cached test."""
import hashlib,json,os,re,subprocess
from pathlib import Path
from run_spoon import OUT,B,jdk,deps,testclasses,case,digest,command

def main():
    dest=OUT/'test-source-check';assert not dest.exists();dest.mkdir()
    path='src/test/java/spoon/test/variable/AccessFullyQualifiedFieldTest.java'
    source=subprocess.check_output(['git','-C',case['repo'],'show',case['revisions']['F']+':'+path])
    original=dest/'AccessFullyQualifiedFieldTest.java';original.write_bytes(source)
    classes=dest/'classes';classes.mkdir()
    mainclasses=B/'work/java-causal-expansion-20260912/expansion-fp-01/2513/F/classes'
    cp=os.pathsep.join(map(str,[mainclasses,testclasses]+deps))
    rr=command([jdk/'bin/javac','-proc:none','-cp',cp,'-d',classes,original],dest,dest/'compile.json');assert rr['returncode']==0
    outputs=[]
    for p,label in [(testclasses,'cached'),(classes,'recompiled')]:
        rr=command([jdk/'bin/javap','-c','-p','-classpath',p,'spoon.test.variable.AccessFullyQualifiedFieldTest'],dest,dest/(label+'.json'));assert rr['returncode']==0;outputs.append(rr['stdout'])
    matches={}
    for name in ['testPrivateStaticImportShouldNotBeImportedInSameClass','buildResourceAndReturnResult']:
        blocks=[]
        for text in outputs:
            start=re.search(r'^  (?:public|private).* '+name+r'\(',text,re.M).start()
            end=text.find('\n\n',start);block=text[start:end if end>=0 else len(text)]
            # Constant-pool indexes can differ without instruction differences.
            blocks.append(re.sub(r'#\d+', '#CP', block))
        matches[name]=blocks[0]==blocks[1]
    record={'original_BFC':case['revisions']['F'],'source_path':path,'source_sha256':digest(original),'cached_class_sha256':digest(testclasses/'spoon/test/variable/AccessFullyQualifiedFieldTest.class'),'method_bytecode_matches_original_source':matches,'comparison':'javap instruction sequence and symbolic constants; normalize constant-pool indices only'}
    (dest/'verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2));assert all(matches.values())
if __name__=='__main__':main()
