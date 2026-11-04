#!/usr/bin/env python3
from pathlib import Path
import json,re,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[2];QA=ROOT/'docs/qa/2026-10-24/w81'
def suites(folder):
 counts=dict(tests=0,failures=0,errors=0,skipped=0);identities=set()
 for p in folder.glob('TEST-*.xml'):
  d=E.parse(p).getroot()
  for k in counts:counts[k]+=int(d.attrib.get(k,0))
  for c in d.findall('testcase'):identities.add((c.attrib['classname'],c.attrib['name']))
 return counts,identities
old,oldIds=suites(ROOT/'docs/qa/2026-10-24/w80/gate-3-xml');assert old['tests']==589
rows=[]
for n in range(1,6):
 text=(QA/f'gate-{n}.log').read_text();counts,ids=suites(QA/f'gate-{n}-xml')
 assert oldIds<=ids,'Old test identities missing'
 passed=re.search(r'All (\d+) required tests passed',text)
 failed=re.search(r'(\d+) required tests failed',text)
 total=re.search(r'(\d+) GAME TESTS COMPLETE',text)
 assert counts==dict(tests=601 if n<=3 else 604,failures=0,errors=0,skipped=0)
 assert total and int(total[1])==(692 if n<=3 else 693)
 if n>0:assert passed and int(passed[1])==(692 if n<=3 else 693) and 'BUILD SUCCESSFUL' in text and '20 actionable tasks: 20 executed' in text
 rows.append(dict(gate=n,junit=counts,previousJUnitIdentitiesPreserved=len(oldIds),addedJUnit=len(ids-oldIds),
  totalGameTests=int(total[1]),passedRequiredGameTests=int(passed[1]) if passed else None,
  failedRequiredGameTests=int(failed[1]) if failed else 0,forcedTasks=20,
  jarSha256=(QA/f'gate-{n}-jar.sha256').read_text().split()[0],
  gameTestEvidence='Raw Minecraft logs; no GT XML emitted. Archived XML is JUnit only.'))
assert rows[3]['jarSha256']==rows[4]['jarSha256']
out=dict(gates=rows,finalSameJar=True,jarSha256=rows[4]['jarSha256'],finalGates=[4,5],previousGameTests=682,newGameTests=11)
(QA/'gate-summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
