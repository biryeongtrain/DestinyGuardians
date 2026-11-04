#!/usr/bin/env python3
"""Archive-aware read-only gate summary (writes only the requested stage summary)."""
from pathlib import Path
import json,re,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[2];QA=ROOT/'docs/qa/2026-10-25/w84'
def suites(folder):
    c=dict(tests=0,failures=0,errors=0,skipped=0);ids=set()
    for p in folder.glob('TEST-*.xml'):
        d=E.parse(p).getroot()
        for k in c:c[k]+=int(d.attrib[k])
        for t in d.findall('testcase'):ids.add((t.attrib['classname'],t.attrib['name']))
    return c,ids
old,oldIds=suites(ROOT/'docs/qa/2026-10-25/w83/gate-5-xml');assert old['tests']==624
rows=[]
for log in sorted(QA.glob('gate-[0-9]*.log'),key=lambda p:int(p.stem.split('-')[1])):
    n=int(log.stem.split('-')[1]);t=log.read_text();c,ids=suites(QA/f'gate-{n}-xml')
    passed=re.search(r'All (\d+) required tests passed',t);failed=re.search(r'(\d+) required tests failed',t);total=re.search(r'(\d+) GAME TESTS COMPLETE',t)
    rows.append(dict(gate=n,returncode=json.loads((QA/f'gate-{n}-exit.json').read_text())['returncode'],junit=c,
        previousJUnitIdentitiesPreserved=len(oldIds&ids),newJUnit=len(ids-oldIds),gameTestsTotal=int(total[1]) if total else None,
        requiredPassed=int(passed[1]) if passed else None,requiredFailed=int(failed[1]) if failed else None,
        jarSha256=(QA/f'gate-{n}-jar.sha256').read_text().strip() if (QA/f'gate-{n}-jar.sha256').exists() else None,
        forcedAllTasks='20 actionable tasks: 20 executed' in t))
final=rows[-2:];assert len(final)==2
for r in final:
    assert r['returncode']==0 and r['forcedAllTasks'] and r['previousJUnitIdentitiesPreserved']==624,r
    assert r['junit']['tests']>=638 and all(r['junit'][k]==0 for k in ('failures','errors','skipped')),r
    assert r['requiredPassed'] and r['requiredPassed']==r['gameTestsTotal'] and r['requiredPassed']>717,r
assert final[0]['jarSha256']==final[1]['jarSha256'] and final[0]['junit']==final[1]['junit'] and final[0]['requiredPassed']==final[1]['requiredPassed']
out=dict(gates=rows,finalPassingGates=[r['gate'] for r in final],jarSha256=final[-1]['jarSha256'],previousGameTests=717,
    newGameTests=final[-1]['requiredPassed']-717,previousJUnit=624,newJUnit=final[-1]['newJUnit'],
    evidenceBoundary='Raw forced GT logs and archived JUnit XML. Intentional catalog expansion changes separately audited. No native framebuffer/acoustic certification.')
(QA/'gate-summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
