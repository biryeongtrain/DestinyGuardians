#!/usr/bin/env python3
"""New W123 replacements for W50 rigid bow bodies; retain every dynamic state.

Canonical rest bow replacements are insufficient: runtime uses a composite of
body_hip + separately sampled string/arrow. No historical W50 file is written.
"""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import generate_bow_models_w50 as bow

ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'src/main/resources'
IDS=('biting_winds','whispering_slab')
def read(path):return json.loads(path.read_bytes())
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()

def normalized(e,textures):
    e=copy.deepcopy(e);e.pop('name',None)
    for f in e['faces'].values():
        key=f['texture']
        while key.startswith('#'):key=textures[key[1:]]
        f['texture']=key
    return json.dumps(e,sort_keys=True,separators=(',',':'))

def generate():
    output={};records=[];historical=read(ROOT/'art/weapons/w50/manifest.json')['sha256']
    for id in IDS:
        source=f'assets/destiny/models/weapon_bow_w50/{id}_body_hip.json'
        design=read(ROOT/f'art/weapons/w123/{id}/design.json')
        full=read(RES/f'assets/destiny/models/weapon_surface_w123/{id}.json')
        original=read(RES/f'assets/destiny/models/weapon/bow/{id}.json')
        names=design['moving_element_names'];assert names and len(names)==len(set(names))
        moving=[e for e in full['elements'] if e['name'] in names]
        body=[e for e in full['elements'] if e['name'] not in names]
        assert body and len(moving)==len(names)
        _,expected=bow.parts(original,bow.CONFIG[id])
        assert collections.Counter(normalized(e,full['textures']) for e in moving)==collections.Counter(normalized(e,original['textures']) for e in expected),id+' rest string/arrow drift'
        max_motion=0;retained={}
        for path,digest in historical.items():
            if f'weapon_bow_w50/{id}_' in path or path.endswith(f'items/weapon_bow_w50/{id}.json'):
                assert sha((ROOT/path).read_bytes())==digest,path
                retained[path]=digest
                if path.endswith('_hip.json') and not path.endswith('_body_hip.json'):
                    max_motion=max(max_motion,len(read(ROOT/path)['elements']))
        assert len(body)+max_motion<=1000
        before=read(RES/source);replacement=copy.deepcopy(full)
        replacement['elements']=body;replacement['display']=before['display']
        replacement['credit']='W147 semantic rigid body / existing W50 dynamic string+arrow stays separate'
        path=f'src/main/resources/assets/destiny/models/weapon_surface_w123/{id}_body_hip.json'
        output[path]=encode(replacement)
        records.append(dict(id=id,source=source,sourceSha256=sha((RES/source).read_bytes()),replacement=path,
            bodyElements=len(body),restMovingElements=len(moving),maxDynamicMovingElements=max_motion,maxAssembledElements=len(body)+max_motion,
            movingElementNames=names,retainedDynamicAndGraphSha256=retained,displayExact=True))
    output['art/weapons/w147/bow-body-integration.json']=encode(dict(stage='W147',bows=records,outputSha256={p:sha(b) for p,b in output.items()},policy='New migration bodies only; no W50 historical graph/state overwrites, no baked static duplicate string in runtime body.'))
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
    for path,data in generate().items():
        target=ROOT/path
        if a.verify:assert target.read_bytes()==data,path
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    print('W147 dynamic bow body replacements: verified' if a.verify else 'W147 dynamic bow body replacements: generated')
