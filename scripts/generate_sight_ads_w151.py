#!/usr/bin/env python3
"""W151: sight-anchored ADS for 20 weapons; preserve original HIP/third/reload graphs."""
import argparse
import copy
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'src/main/resources/assets/destiny'
KEY = 'weapon_sight_w151'
GROUPS = ('handguns', 'rifles', 'pulse', 'rockets')
FP = ('firstperson_righthand', 'firstperson_lefthand')

def enc(v):
    return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def remap(v, mapping):
    if isinstance(v, dict):
        if v.get('type') == 'minecraft:model' and v.get('model') in mapping:
            return dict(v, model=mapping[v['model']])
        return {k: remap(x, mapping) for k,x in v.items()}
    if isinstance(v, list):
        return [remap(x, mapping) for x in v]
    return v

def generate():
    outputs, inputs, rows = {}, {}, []
    two_hand = runpy.run_path(str(ROOT/'scripts/build_weapons_w30.py'))['two_hand_display']
    def read(p):
        inputs[str(p.relative_to(ROOT))] = sha(p.read_bytes())
        return json.loads(p.read_bytes())
    specs = [r for g in GROUPS for r in read(ROOT/f'art/weapons/w151/{g}-sights.json')['weapons']]
    assert len(specs) == len({r['id'] for r in specs}) == 20
    for row in specs:
        id, family = row['id'], row['family']
        hip = read(A / f'models/weapon/{family}/{id}.json')['display']
        body = read(A / f'models/{row["body"]}.json')
        assert len(body['elements']) == row['elementCount'] <= 1000
        assembled_body = row['body']
        if row.get('companionModel'):
            companion = read(ROOT / row['companionModel'])
            assert inputs[row['companionModel']] == row['companionSha256']
            # Some remodels expose body+magazine instead of a static full assembly.
            # ADS is not a reload: keep the seated magazine, once, in the same frame.
            full = copy.deepcopy(body)
            for slot, texture in companion['textures'].items():
                assert slot not in full['textures'] or full['textures'][slot] == texture, (id,slot)
                full['textures'][slot] = texture
            full['elements'].extend(copy.deepcopy(companion['elements']))
            assert len(full['elements']) == row['assemblyElementCount'] <= 1000
            assembled_body += '_assembled'
            outputs[A/f'models/{assembled_body}.json'] = enc(full)
        center, s, distance = row['sightCenter'], row['scale'], row['eyeToSightMeters']
        assert row['eyeSide'] == '+Z' and row['plane'] == 'XY'
        assert all(abs(a-b)<1e-6 for a,b in zip(row['forwardPoint'], [center[0],center[1],center[2]-2]))
        assert sha((ROOT/row['source']).read_bytes()) == row['sourceSha256']
        inputs[row['source']] = row['sourceSha256']
        ads = copy.deepcopy(hip)
        for context in FP:
            ads[context] = dict(rotation=[0,0,0], scale=[s]*3, translation=[
                round(-8.96-s*(center[0]-8),6), round(8.32-s*(center[1]-8),6),
                round(16*(.72-distance)-s*(center[2]-8),6)])
        mapping = {}
        for f in range(21):
            display = copy.deepcopy(hip)
            for context in FP:
                for k in ('rotation','translation','scale'):
                    display[context][k] = [round(a+(b-a)*f/20,6) for a,b in zip(hip[context][k], ads[context][k])]
            for style in ('native', 'twohand'):
                key = f'{KEY}/{id}_{f:02}_{style}'
                parent = f'weapon/{family}/{id}' if f == 0 else assembled_body
                outputs[A/f'models/{key}.json'] = enc(dict(parent='destiny:'+parent,
                    display=display if style=='native' else two_hand(display,family)))
                mapping[f'destiny:weapon_aim_w70/{id}_{f:02}_{style}'] = 'destiny:'+key
        graph = read(A/f'items/weapon_aim_w70/{id}.json')
        outputs[A/f'items/{KEY}/{id}.json'] = enc(remap(graph,mapping))
        rows.append(dict(id=id, family=family, body=assembled_body, sight=row, hip=hip, ads=ads,
            scale=s, eyeToSightMeters=distance, frames=21))
    for p in (Path(__file__).resolve(), ROOT/'scripts/build_weapons_w30.py', A/'textures/item/weapon/w148/sights.png'):
        inputs[str(p.relative_to(ROOT))] = sha(p.read_bytes())
    outputs[ROOT/'art/weapons/w151/ads-manifest.json'] = enc(dict(stage='W151', weapons=rows,
        inputSha256=inputs, outputs={str(p.relative_to(ROOT)):sha(v) for p,v in outputs.items()},
        policy='Twenty independent authored ADS proxies. Original HIP/third/reload preserved. Physical rear aperture/front post, no optical refraction or exact ripped optic claim.'))
    return outputs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    out = generate()
    for p,b in out.items():
        if args.verify:
            assert p.read_bytes()==b,p
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(b)
    print('W151 sight ADS',len(out),'verified' if args.verify else 'generated')
