#!/usr/bin/env python3
"""Read-only gate summary; archive status before writing this report."""
from pathlib import Path
import json,re,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[2];QA=ROOT/'docs/qa/2026-10-25/w83'
def suites(folder):
 c=dict(tests=0,failures=0,errors=0,skipped=0);ids=set()
 for p in folder.glob('TEST-*.xml'):
  d=E.parse(p).getroot()
  for k in c:c[k]+=int(d.attrib[k])
  for t in d.findall('testcase'):ids.add((t.attrib['classname'],t.attrib['name']))
 return c,ids
old,oldIds=suites(ROOT/'docs/qa/2026-10-25/w82/gate-4-xml');assert old['tests']==613
rows=[]
for log in sorted(QA.glob('gate-[0-9]*.log')):
 n=int(log.stem.split('-')[1]);t=log.read_text();c,ids=suites(QA/f'gate-{n}-xml')
 passed=re.search(r'All (\d+) required tests passed',t);failed=re.search(r'(\d+) required tests failed',t);total=re.search(r'(\d+) GAME TESTS COMPLETE',t)
 exit=json.loads((QA/f'gate-{n}-exit.json').read_text())['returncode']
 rows.append(dict(gate=n,returncode=exit,junit=c,previousJUnitIdentitiesPreserved=len(oldIds&ids),newJUnit=len(ids-oldIds),gameTestsTotal=int(total[1]) if total else None,requiredPassed=int(passed[1]) if passed else None,requiredFailed=int(failed[1]) if failed else None,jarSha256=(QA/f'gate-{n}-jar.sha256').read_text().strip() if (QA/f'gate-{n}-jar.sha256').exists() else None,forcedAllTasks='20 actionable tasks: 20 executed' in t))
final=rows[-2:];assert len(final)==2 and all(r['returncode']==0 and r['requiredPassed']==717 and r['junit']==dict(tests=624,failures=0,errors=0,skipped=0) and r['previousJUnitIdentitiesPreserved']==613 and r['forcedAllTasks'] for r in final),rows
assert final[0]['jarSha256']==final[1]['jarSha256']
out=dict(gates=rows,finalPassingGates=[r['gate'] for r in final],jarSha256=final[-1]['jarSha256'],previousGameTests=705,newGameTests=12,previousJUnit=613,newJUnit=11,evidenceBoundary='Raw GT logs and archived JUnit XML; historical catalog-expansion tests intentionally adapted and separately audited. No framebuffer proof.')
(QA/'gate-summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
