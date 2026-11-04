#!/usr/bin/env python3
from pathlib import Path
import json,re,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[2];QA=ROOT/'docs/qa/2026-10-25/w82'
def suites(folder):
 counts=dict(tests=0,failures=0,errors=0,skipped=0);ids=set()
 for p in folder.glob('TEST-*.xml'):
  d=E.parse(p).getroot()
  for k in counts:counts[k]+=int(d.attrib[k])
  for c in d.findall('testcase'):ids.add((c.attrib['classname'],c.attrib['name']))
 return counts,ids
old,oldIds=suites(ROOT/'docs/qa/2026-10-24/w81/gate-5-xml');assert old['tests']==604
rows=[]
for n in range(1,5):
 t=(QA/f'gate-{n}.log').read_text();c,ids=suites(QA/f'gate-{n}-xml')
 assert oldIds<=ids and c==dict(tests=613,failures=0,errors=0,skipped=0)
 passed=re.search(r'All (\d+) required tests passed',t);failed=re.search(r'(\d+) required tests failed',t)
 total=re.search(r'(\d+) GAME TESTS COMPLETE',t)
 if n>=3:assert passed and int(passed[1])==705 and 'BUILD SUCCESSFUL' in t and '20 actionable tasks: 20 executed' in t
 rows.append(dict(gate=n,junit=c,previousJUnitIdentitiesPreserved=len(oldIds),newJUnit=len(ids-oldIds),
  gameTestsTotal=int(total[1]) if total else None,requiredPassed=int(passed[1]) if passed else None,
  requiredFailed=int(failed[1]) if failed else None,crashed=n==2,
  jarSha256=(QA/f'gate-{n}-jar.sha256').read_text().split()[0]))
assert rows[2]['jarSha256']==rows[3]['jarSha256']
out=dict(gates=rows,finalPassingGates=[3,4],jarSha256=rows[3]['jarSha256'],previousGameTests=693,newGameTests=12,
 intentionallyUpdatedExistingTest='WeaponWaveW78GameTests.ordinarySalvagersSalvoStillExplodesRadially',
 evidenceBoundary='GT raw Minecraft logs; archived XML JUnit only; no native rendering claim.')
(QA/'gate-summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
