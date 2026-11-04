#!/usr/bin/env python3
"""Verify the pinned W43 extraction against an explicitly supplied Oracle source file.
No implicit downloads; original source/license/provenance in art/weapons/w43/extraction.json.
"""
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args()
m=json.loads((ROOT/'art/weapons/w43/extraction.json').read_text());raw=a.source.read_bytes()
assert hashlib.sha256(raw).hexdigest()==m['sourceSha256'],'Unexpected source snapshot'
source=json.loads(raw);actual=json.loads((ROOT/'src/main/resources/destiny/weapons/w43-ballistics.json').read_text())
expected=[]
for e in m['entries']:
    if 'policy' in e:
        row=dict(id=e['id'],offsetStart=999,vppStart=0,offsetEnd=999.9,vppEnd=0,floor=1,precision=1)
    else:
        family=source[e['family']];r=family['cat'][e['category']]['range'];s=family['subFam'][e['subfamily']]
        assert s['pve_crit_mult']==e['encodedPveCrit']
        row=dict(id=e['id'],offsetStart=r['offset_start'],vppStart=r['vpp_start'],offsetEnd=r['offset_end'],vppEnd=r['vpp_end'],floor=r.get('pve_floor_percent',r['floor_percent']),precision=s['pve_crit_mult']/51+1.5)
    expected.append(row)
assert expected==actual and len(actual)==63
assert hashlib.sha256((ROOT/'src/main/resources/destiny/weapons/w43-ballistics.json').read_bytes()).hexdigest()==m['runtimeSha256']
print('63/63 ballistics profiles exactly match pinned extraction; not proof of current sandbox balance')
