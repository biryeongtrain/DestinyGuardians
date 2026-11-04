#!/usr/bin/env python3
"""One forced build/test gate with immediate report/JAR preservation, even on failure."""
from pathlib import Path
import subprocess,os,sys,shutil,hashlib,json
ROOT=Path(__file__).resolve().parents[2];QA=ROOT/'docs/qa/2026-10-25/w82'
n=int(sys.argv[1]); log=QA/f'gate-{n}.log'
if log.exists():raise SystemExit('Refusing to overwrite a gate')
env=dict(os.environ,JAVA_HOME='/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home')
with log.open('w') as f:r=subprocess.run(['./gradlew','test','build','--rerun-tasks','--console=plain'],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
shutil.copytree(ROOT/'build/test-results/test',QA/f'gate-{n}-xml')
jar=ROOT/'build/libs/destiny-guardians-0.1.0+26.3.jar'
if jar.exists():(QA/f'gate-{n}-jar.sha256').write_text(hashlib.sha256(jar.read_bytes()).hexdigest()+'\n')
(QA/f'gate-{n}-exit.json').write_text(json.dumps(dict(returncode=r.returncode))+'\n')
print(json.dumps(dict(gate=n,returncode=r.returncode,log=str(log))))
sys.exit(r.returncode)
