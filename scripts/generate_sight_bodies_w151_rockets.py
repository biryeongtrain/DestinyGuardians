#!/usr/bin/env python3
"""Open the two existing offset rocket optics in ADS only; original artwork stays intact."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'src/main/resources/assets/destiny'
CONFIG = {
    'bad_omens': ([9.72, 12.18, 8.225], ['optic_bellows_core', 'optic_bellows_bevel_a', 'optic_rear_socket', 'right_recessed_glass']),
    'code_duello': ([9.55, 12., 6.85], ['Optic_recessed_lens', 'Optic_rear_termination']),
}

def enc(v):
    return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def generate():
    outputs, rows = {}, []
    for id, (center, removed) in CONFIG.items():
        source = A / f'models/weapon_surface_w123/{id}.json'
        m = json.loads(source.read_bytes())
        assert set(removed) <= {e['name'] for e in m['elements']}
        m.pop('display', None)
        m['elements'] = [e for e in m['elements'] if e['name'] not in removed]
        m['textures']['sight'] = 'destiny:item/weapon/w148/sights'
        x, y, z = center
        # The original tube walls/lips/UV stay; replace the opaque rear bellows
        # and lens with genuinely open rear rim and a small luminous front post.
        # This is a functional no-refraction game proxy, not a ripped D2 lens.
        def box(name, lo, hi, uv=(0, 0, 1, 1), rotation=None):
            element=dict(name='w151_' + name, **{'from': lo, 'to': hi},
                faces={f: dict(uv=list(uv), texture='#sight') for f in ('north','south','east','west','up','down')})
            if rotation: element['rotation']=rotation
            m['elements'].append(element)
        if id == 'bad_omens':
            radius, thick = .46, .10
            width = 2*(radius+thick/2)*math.tan(math.pi/8)
            for n in range(8):
                angle=n*math.pi/4
                cx,cy=x-radius*math.sin(angle),y+radius*math.cos(angle)
                box('rear_rim_'+str(n), [cx-width/2,cy-thick/2,z-.36],
                    [cx+width/2,cy+thick/2,z], rotation=dict(origin=[cx,cy,z-.18],z=n*45))
        front = 3.45 if id == 'bad_omens' else 3.95
        box('optic_front_post', [x-.028,y-.24,front-.035], [x+.028,y-.022,front+.035], (6,0,7,1))
        # A crosshair shoulder makes the low-pixel-count physical post readable
        # without filling the actual center ray or painting a screen-space dot.
        box('optic_front_shoulder', [x-.13,y-.10,front-.035], [x+.13,y-.073,front+.035], (6,0,7,1))
        body = f'weapon_sight_w151/{id}_body'
        outputs[A / f'models/{body}.json'] = enc(m)
        rows.append(dict(id=id, family='rocket_launcher', body=body, sightCenter=center,
            forwardPoint=[x,y,z-2], style='offset_open_tube', eyeSide='+Z', plane='XY',
            scale=.9, eyeToSightMeters=.65, removedSightNames=removed, elementCount=len(m['elements']),
            source=str(source.relative_to(ROOT)), sourceSha256=sha(source.read_bytes()),
            reference=dict(photo=f'/tmp/destiny-weapons-w31/references/{id}.jpg',
                note='Default Bungie photo and existing W130/W132 semantic model: right-offset tube, original tube/lip UV retained. Only ADS removes opaque bellows/lens; no optical magnification/refraction claim.')))
    outputs[ROOT / 'art/weapons/w151/rockets-sights.json'] = enc(dict(weapons=rows))
    return outputs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    for p, b in generate().items():
        if args.verify:
            assert p.read_bytes() == b, p
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b)
    print('W151 rocket sight bodies', 'verified' if args.verify else 'generated')
