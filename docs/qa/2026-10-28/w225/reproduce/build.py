from pathlib import Path
import subprocess,os,json,hashlib,xml.etree.ElementTree as ET,shutil
repo=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=repo/'docs/qa/2026-10-28/w225'
names=['FirstPersonHandsW201Test','SkinArmsW204Test','ReloadPresentationW212Test','ReloadRoutingW114Test','InsertRoutingW179Test','SwapPresentationW113Test','SwapPresentationW91Test','WeaponSwapCycleTest']
cmd=['rtk','proxy','./gradlew','--offline','--no-daemon','--max-workers=2','--console=plain','--init-script','/private/tmp/destiny-w225-after-native/test-heap.init.gradle','test']
for name in names:cmd+=['--tests','kim.biryeong.destiny.weapon.'+name]
cmd+=['assemble']
env=dict(os.environ,JAVA_HOME='/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home')
with (q/'build.log').open('x') as log:p=subprocess.run(cmd,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0,p.returncode
rows=[];out=q/'junit';out.mkdir(exist_ok=True)
for name in names:
 path=repo/'build/test-results/test'/('TEST-kim.biryeong.destiny.weapon.'+name+'.xml');e=ET.parse(path).getroot();row={k:int(e.get(k,0)) for k in ['tests','failures','errors']};row['name']=e.get('name');rows.append(row);shutil.copy2(path,out/path.name)
assert not any(x['failures'] or x['errors'] for x in rows)
jar=repo/'build/libs/destiny-guardians-0.1.0+26.3.jar'
report={'tests':sum(x['tests'] for x in rows),'failed':0,'rows':rows,'jar':str(jar),'sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),'bytes':jar.stat().st_size,'command':cmd}
(q/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
