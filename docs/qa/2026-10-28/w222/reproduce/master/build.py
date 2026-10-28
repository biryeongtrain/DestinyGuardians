from pathlib import Path
import subprocess,os,json,hashlib,zipfile,xml.etree.ElementTree as ET,shutil,sys
repo=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=repo/'docs/qa/2026-10-28/w222'
phase=sys.argv[1] if len(sys.argv)>1 else 'pass1'
env=dict(os.environ,JAVA_HOME='/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home')
names=['FirstPersonHandsW201Test','SkinArmsW204Test','ReloadPresentationW212Test','ReloadRoutingW114Test','InsertRoutingW179Test']
cmd=['rtk','proxy','./gradlew','--offline','--no-daemon','--max-workers=2','--console=plain','--init-script','/private/tmp/destiny-w222-pass1-native/test-heap.init.gradle','test']
for name in names:cmd+=['--tests','kim.biryeong.destiny.weapon.'+name]
cmd+=['assemble']
with (q/('build-'+phase+'.log')).open('w') as log:result=subprocess.run(cmd,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0,result.returncode
rows=[];out=q/('junit-'+phase);out.mkdir(exist_ok=True)
for name in names:
 path=repo/'build/test-results/test'/('TEST-kim.biryeong.destiny.weapon.'+name+'.xml');e=ET.parse(path).getroot();row={k:int(e.get(k,0)) for k in ['tests','failures','errors']};row['name']=e.get('name');rows.append(row);shutil.copy2(path,out/path.name)
assert not any(x['failures'] or x['errors'] for x in rows)
jar=repo/'build/libs/destiny-guardians-0.1.0+26.3.jar'
with zipfile.ZipFile(jar) as z:assert z.testzip() is None
report=dict(tests=sum(x['tests'] for x in rows),failed=0,rows=rows,jar=str(jar),sha256=hashlib.sha256(jar.read_bytes()).hexdigest(),bytes=jar.stat().st_size,command=cmd)
(q/('build-'+phase+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
