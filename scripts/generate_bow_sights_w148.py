#!/usr/bin/env python3
"""ADS-only open bow sights in the unchanged W123 native geometry frame.

Writes only two rigid bodies and their integration metadata. No display, parent,
static string/arrow, texture output, historical resource edit, or runtime route.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = 'src/main/resources/assets/destiny/'
META = 'art/weapons/w148/bow-sights.json'
BASELINE = 'a04af75a85bc645741663ef5ee25b53abb6c1310b7fc018398f5600b7b575a3e'
IDS = ('biting_winds', 'whispering_slab')
# Intentional input pins: regenerate against this latest dirty-seeded product,
# rather than silently accepting an older W123 reconstruction or changed atlas.
INPUT_PINS = {
    ASSET+'models/weapon_surface_w123/biting_winds_body_hip.json': 'bd29dd9cf6778d1e57c3097871797d16390d94cb636ed30fcc2b60c372007ca5',
    ASSET+'models/weapon_surface_w123/whispering_slab_body_hip.json': '52e3bceccc2ccaa17eeb0fa9933e28702777e338b31e14ff1d2ac4794f6233af',
    ASSET+'models/weapon_surface_w123/biting_winds.json': 'e40ebb431b1ffa765faca806b42018f0d3ee63582ad3339c4d98304fc452f860',
    ASSET+'models/weapon_surface_w123/whispering_slab.json': '18284e41754af64fffce0c326d72acf6c9a3c31f81951be8cca38e21c4eddd1d',
    ASSET+'textures/item/weapon/w123/biting_winds.png': '4cb177110761d0f9168950db584046923b0daecbf9d733c644a1d4907dd75553',
    ASSET+'textures/item/weapon/w123/whispering_slab.png': '700fc65bd8a9443225135d18c8658d777c4be39cb41cd6f4ee6bc1c1f28e16ca',
    'art/weapons/w123/biting_winds/design.json': '23f70e5d5df94f51b68cc83b5cc12bceb23450d96f761c8cfa7e1476dbf98fda',
    'art/weapons/w123/whispering_slab/design.json': '7b91360fd734465ef78d089dacde658c9824fd41d04e5317839b24dc276b2808',
    'art/weapons/w50/manifest.json': 'aaf0e0c4a18ddab37f134f7d9aabbf01c7c0383b0806194328a5e6c2c33c82a2',
}
CONFIG = {
    'biting_winds': {
        'center': [6.2, 11.85, 5.55],
        'removed': ['sight_vertical', 'sight_crown', 'sight_heel', 'sight_front_post'],
        'halfWidth': .64, 'halfHeight': .88, 'corner': .22,
        'rail': .14, 'depth': .46,
        'palette': {'blue': [215, 3], 'black': [175, 3],
                    'steel': [3, 3], 'yellow': [7, 284]},
        'ringMaterial': 'blue', 'frontMaterial': 'blue', 'pinMaterial': 'yellow',
        'mountFrom': [6.80, 12.13, 5.43], 'mountTo': [7.25, 12.39, 6.14],
        'mountAnchor': 'sight_mount', 'mountMaterial': 'blue',
        'reason': 'Angular blue open sight beside the red riser; replaces the tall occluding blades. Original mount, adjustment drum and draw counter retained.',
    },
    'whispering_slab': {
        # Original x=6.382 lies in the W50 string's x=[6.181671,6.551712].
        # Keep the ring's original Y/Z, move only the new optic right of that ray.
        'center': [6.8, 18.8958083, 2.349],
        'removed': ['sight_ring_'+str(i) for i in range(8)],
        'halfWidth': .58, 'halfHeight': .58, 'corner': .3397561,
        'rail': .12, 'depth': .42,
        'palette': {'black': [497, 11], 'steel': [711, 6], 'brass': [157, 439]},
        'ringMaterial': 'black', 'frontMaterial': 'brass', 'pinMaterial': 'brass',
        'mountFrom': [5.70, 18.8058083, 2.20], 'mountTo': [6.25, 18.9858083, 3.20],
        'mountAnchor': 'sight_side_foot', 'mountMaterial': 'black',
        'reason': 'Black ring with brass eye-facing rim and pin. New center is +0.4178435 X from the old optic to clear the retained string; original cage, side foot, teal inlay and riser retained.',
    },
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def read(relative):
    return json.loads((ROOT/relative).read_bytes())


def verify_inputs():
    for relative, digest in INPUT_PINS.items():
        if sha((ROOT/relative).read_bytes()) != digest:
            raise ValueError('Input pin drift: '+relative)


def palette_uv(pixel):
    # A sub-texel interior of an existing opaque, flat palette pixel; no new PNG.
    x, y = pixel
    return [(x+.125)/64, (y+.125)/64, (x+.875)/64, (y+.875)/64]


def cube(name, lo, hi, cfg, material, front=None):
    faces = {face: {'uv': palette_uv(cfg['palette'][material]), 'texture': '#0'}
             for face in ('north', 'south', 'east', 'west', 'up', 'down')}
    if front:
        # Eye is on +Z looking along -Z, so south is the eye-facing surface.
        faces['south']['uv'] = palette_uv(cfg['palette'][front])
    return {'name': name, 'from': [round(v, 7) for v in lo],
            'to': [round(v, 7) for v in hi], 'faces': faces}


def sight_geometry(cfg):
    cx, cy, cz = cfg['center']
    w, h, c = cfg['halfWidth'], cfg['halfHeight'], cfg['corner']
    outline = [(-w+c, h), (w-c, h), (w, h-c), (w, -h+c),
               (w-c, -h), (-w+c, -h), (-w, -h+c), (-w, h-c)]
    elements = []
    for i, (a, b) in enumerate(zip(outline, outline[1:]+outline[:1])):
        x, y = cx+(a[0]+b[0])/2, cy+(a[1]+b[1])/2
        length = math.dist(a, b)+.012  # Small joined corners, no perimeter gaps.
        e = cube('w148_sight_frame_'+str(i),
                 [x-length/2, y-cfg['rail']/2, cz-cfg['depth']/2],
                 [x+length/2, y+cfg['rail']/2, cz+cfg['depth']/2],
                 cfg, cfg['ringMaterial'], cfg['frontMaterial'])
        e['rotation'] = {'origin': [round(x, 7), round(y, 7), cz], 'axis': 'z',
                         'angle': round(math.degrees(math.atan2(b[1]-a[1], b[0]-a[0])), 7),
                         'rescale': False}
        elements.append(e)
    elements.append(cube('w148_sight_mount_bridge', cfg['mountFrom'], cfg['mountTo'],
                         cfg, cfg['mountMaterial']))
    # A narrow physical lower pin. Its top is 0.07 below the center ray, leaving
    # the aiming ray itself clear, rather than hiding the target with a blade.
    elements.append(cube('w148_sight_pin_stem',
                         [cx-.03, cy-h+.01, cz-.02], [cx+.03, cy-.15, cz+.12],
                         cfg, 'steel'))
    elements.append(cube('w148_sight_pin_tip',
                         [cx-.055, cy-.17, cz+.05], [cx+.055, cy-.07, cz+.21],
                         cfg, cfg['pinMaterial']))
    return elements


def historical_resources(id, manifest):
    retained, states = {}, []
    for path, digest in sorted(manifest['sha256'].items()):
        if f'models/weapon_bow_w50/{id}_' not in path and not path.endswith(f'items/weapon_bow_w50/{id}.json'):
            continue
        if sha((ROOT/path).read_bytes()) != digest:
            raise ValueError('Historical W50 drift: '+path)
        retained[path] = digest
        if path.endswith('_hip.json') and not path.endswith('_body_hip.json'):
            states.append({'path': path, 'elements': len(read(path)['elements'])})
    assert len(states) == 44, (id, 'incomplete W50 states')
    return retained, states


def generate():
    verify_inputs()
    outputs, records = {}, []
    historical = read('art/weapons/w50/manifest.json')
    for id in IDS:
        cfg = CONFIG[id]
        source = ASSET+f'models/weapon_surface_w123/{id}_body_hip.json'
        original = read(source)
        design = read(f'art/weapons/w123/{id}/design.json')
        names = [e['name'] for e in original['elements']]
        assert all(name in names for name in cfg['removed'])
        retained_body = [copy.deepcopy(e) for e in original['elements'] if e['name'] not in cfg['removed']]
        added = sight_geometry(cfg)
        body = {'credit': 'W148 ADS-only open sight / unchanged W123 mainbody frame / separate retained W50 motion',
                'textures': copy.deepcopy(original['textures']), 'elements': retained_body+added}
        path = ASSET+f'models/weapon_sight_w148/{id}_body.json'
        outputs[path] = encode(body)
        retained, states = historical_resources(id, historical)
        max_moving = max(s['elements'] for s in states)
        assert len(body['elements'])+max_moving <= 1000
        cx, cy, cz = cfg['center']
        references = {p: digest for p, digest in design['raw_input_sha256'].items()
                      if p.endswith(('.jpg', '.blend', '.fbx'))}
        records.append({
            'id': id, 'model': f'destiny:weapon_sight_w148/{id}_body',
            'bodyModelPath': path, 'sourceBodyModelPath': source,
            'sourceInputSha256': INPUT_PINS[source],
            'sightCenter': [cx, cy, cz], 'forwardPoint': [cx, cy, round(cz-2, 7)],
            'forwardAxis': [0, 0, -1], 'aperturePlane': 'XY', 'eyeSide': '+Z',
            'sightDepth': cfg['depth'], 'pinTop': [cx, round(cy-.07, 7), round(cz+.21, 7)],
            'pinTopBelowAxis': .07, 'clearCenterCorridorRadius': .04,
            'apertureHalfWidth': cfg['halfWidth']-cfg['rail']/2,
            'apertureHalfHeight': cfg['halfHeight']-cfg['rail']/2,
            'removedNames': cfg['removed'], 'addedNames': [e['name'] for e in added],
            'retainedBodyElements': len(retained_body), 'bodyElements': len(body['elements']),
            'maxRetainedW50MovingElements': max_moving,
            'maxAssembledElements': len(body['elements'])+max_moving,
            'elementLimit': 1000, 'mountAnchorName': cfg['mountAnchor'],
            'paletteUV': {m: palette_uv(p) for m, p in cfg['palette'].items()},
            'designIntent': cfg['reason'], 'nativeFrame': design['source'],
            'referenceInputSha256': references,
            'retainedDynamicAndGraphSha256': retained, 'retainedMovingStates': states,
            'outputSha256': sha(outputs[path]), 'displayIncluded': False,
        })
    outputs[META] = encode({
        'stage': 'W148', 'baselineSha256': BASELINE,
        'generator': 'scripts/generate_bow_sights_w148.py',
        'generatorSha256': sha(Path(__file__).read_bytes()),
        'inputSha256': INPUT_PINS, 'bows': records,
        'policy': 'ADS-only full rigid geometry. Preserve every retained element/face/UV/rotation and native origin; master supplies display and sampled graphs. Real open apertures and small lower pins; no optical card or screenspace crosshair.',
        'nativeAccepted': False,
        'limitations': ['Disk geometry and targeted Python checks only; native parser, eye alignment, both hands, draw/nock visibility, pixel readability and display load acceptance belong to master.',
                        'Fixed palette UV samples reuse the current default-dye atlas; no optical shader, emissive pin or original PBR.',
                        'Pin top is 0.07 native units below the clear center ray. Aperture center is the endpoint alignment anchor, not the body bounding box.'],
    })
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    outputs = generate()
    batch = read('docs/qa/2026-10-26/w148/batch.json')
    owned = next(f['owned_paths'] for f in batch['features'] if f['name'] == 'w148-bow-sights')
    assert set(outputs) <= set(owned)
    for path, raw in outputs.items():
        target = ROOT/path
        if args.verify:
            assert target.read_bytes() == raw, 'Regeneration differs: '+path
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    meta = json.loads(outputs[META])
    print(('Verified' if args.verify else 'Generated')+' W148 bow sights: '+
          ', '.join(f"{r['id']} {r['bodyElements']} rigid + {r['maxRetainedW50MovingElements']} moving = {r['maxAssembledElements']}" for r in meta['bows']))


if __name__ == '__main__':
    main()
