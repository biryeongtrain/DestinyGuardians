#!/usr/bin/env python3
"""Ordinary-bow string/arrow poses, preserving original body, UV and display transforms.

Server-owned float2 selects these sampled poses, not vanilla using_item predicates.
Two rigid limbs/cams stay unchanged: this is authored bow-string/arrow animation,
not a ripped Destiny animation, hand IK, limb deformation or Shadowshot model.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
STEPS = 20
CONFIG = {
    'biting_winds': dict(string=128, arrow=[86, 87, 88, 89, 90, 156, 157, 158, 159, 160,
        161, 162, 163, 164, 165, 166, 203, 204, 220, 221], shaft=161,
        bridges=[[6.378126, 8.803671]], pull=4.8),
    'whispering_slab': dict(string=114, arrow=[67, 68, 70, 139, 140, 141, 142, 180, 181], shaft=140,
        bridges=[[2.486954, 2.944633], [3.173472, 4.775347]], pull=3.4),
}
HELD = ['firstperson_righthand', 'firstperson_lefthand', 'thirdperson_righthand', 'thirdperson_lefthand']


def encode(value): return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def rnd(values): return [round(v, 6) for v in values]


def string_segment(source, start_y, end_y, start_z, end_z):
    """Local +Y cuboid rotated around X, keeping exact centerline endpoint contact."""
    x = (source['from'][0] + source['to'][0]) / 2
    depth = source['to'][2] - source['from'][2]
    dy, dz = end_y - start_y, end_z - start_z
    result = copy.deepcopy(source)
    result['from'] = rnd([source['from'][0], start_y, start_z - depth / 2])
    result['to'] = rnd([source['to'][0], start_y + math.hypot(dy, dz), start_z + depth / 2])
    result['rotation'] = dict(origin=rnd([x, start_y, start_z]), axis='x',
                              angle=round(math.degrees(math.atan2(dz, dy)), 6), rescale=False)
    # Each half keeps its corresponding longitudinal source texture, not two copies of the whole string.
    height = source['to'][1] - source['from'][1]
    a, b = (start_y - source['from'][1]) / height, (end_y - source['from'][1]) / height
    for face in ('north', 'south', 'west', 'east'):
        uv = result['faces'][face]['uv']
        v0, v1 = uv[1], uv[3]
        uv[1], uv[3] = round(v0 + (v1 - v0) * a, 6), round(v0 + (v1 - v0) * b, 6)
    return result


def parts(original, cfg, draw=0., nock=None, empty=False):
    elements = original['elements']
    body = [copy.deepcopy(e) for i, e in enumerate(elements) if i not in cfg['arrow'] and i != cfg['string']]
    string = elements[cfg['string']]
    shaft = elements[cfg['shaft']]
    nock_y = (shaft['from'][1] + shaft['to'][1]) / 2
    z = (string['from'][2] + string['to'][2]) / 2
    pull = cfg['pull'] * draw
    moving = [string_segment(string, string['from'][1], nock_y, z, z + pull),
              string_segment(string, nock_y, string['to'][1], z + pull, z)]
    arrow = [copy.deepcopy(elements[i]) for i in cfg['arrow']]
    # Ripped geometry occluded by the static riser has shaft gaps. Fill only those gaps
    # before translating the arrow; otherwise a full draw reveals a detached arrowhead/fletching.
    for lo, hi in cfg['bridges']:
        bridge = copy.deepcopy(shaft)
        bridge['from'][2], bridge['to'][2] = lo, hi
        arrow.append(bridge)
    offset = [0, 0, pull]
    if nock is not None:
        # First 30% has no arrow. Then bring the original arrow up to the rest.
        # These timings/offsets are authored, not measured Destiny motion curves.
        empty = empty or nock < .3
        t = max(0, min(1, (nock - .3) / .5))
        t = t * t * (3 - 2 * t)
        offset = [.8 * (1 - t), -5 * (1 - t), 1.5 * (1 - t)]
    if not empty:
        for e in arrow:
            e['from'] = rnd([a + b for a, b in zip(e['from'], offset)])
            e['to'] = rnd([a + b for a, b in zip(e['to'], offset)])
        moving += arrow
    return body, moving


def model_node(key): return dict(type='minecraft:model', model='destiny:' + key)


def generate():
    output, sources, bows = {}, {}, {}
    for id, cfg in CONFIG.items():
        key = 'weapon_bow_w50/' + id
        source = ASSETS / f'models/weapon/bow/{id}.json'
        item = ASSETS / f'items/weapon/{id}.json'
        original = json.loads(source.read_bytes())
        original_item = json.loads(item.read_bytes())
        displays = {'hip': original['display']}
        for pose in ('ads', 'inspect'):
            path = ASSETS / f'models/weapon/bow/{id}_{pose}.json'
            child = json.loads(path.read_bytes())
            displays[pose] = copy.deepcopy(original['display']) | child.get('display', {})
            sources[str(path.relative_to(ROOT))] = sha(path.read_bytes())
        for path in (source, item, ROOT/f'art/blockbench/weapons/w30/{id}.bbmodel',
                     ASSETS/f'textures/item/weapon/w30/{id}.png'):
            sources[str(path.relative_to(ROOT))] = sha(path.read_bytes())
        body, _ = parts(original, cfg)
        metadata = {k: copy.deepcopy(v) for k, v in original.items() if k not in ('elements', 'display')}
        def write_geometry(name, elements):
            for pose, display in displays.items():
                path = ASSETS / f'models/{key}_{name}_{pose}.json'
                if pose == 'hip':
                    value = metadata | dict(elements=elements, display=display)
                else:
                    value = dict(parent=f'destiny:{key}_{name}_hip', display=display)
                output[path] = encode(value)
        write_geometry('body', body)
        states = [(0, 'empty', dict(empty=True)), (1, 'loaded', {})]
        states += [(2 + frame, f'draw_{frame:02}', dict(draw=frame/STEPS)) for frame in range(STEPS + 1)]
        states += [(32 + frame, f'nock_{frame:02}', dict(nock=frame/STEPS)) for frame in range(STEPS + 1)]
        for _, name, kwargs in states:
            _, moving = parts(original, cfg, **kwargs)
            assert len(body) + len(moving) <= 256
            write_geometry(name, moving)
        def frames(pose):
            return dict(type='minecraft:range_dispatch', property='minecraft:custom_model_data', index=2,
                        fallback=copy.deepcopy(original_item['model']), entries=[dict(threshold=selector,
                model=dict(type='minecraft:composite', models=[model_node(f'{key}_body_{pose}'),
                                                              model_node(f'{key}_{name}_{pose}')]))
                for selector, name, _ in states])
        pose_select = dict(type='minecraft:select', property='minecraft:custom_model_data', index=0,
                           cases=[dict(when=p, model=frames(p)) for p in ('ads', 'inspect')], fallback=frames('hip'))
        wrapper = copy.deepcopy(original_item)
        wrapper['model'] = dict(type='minecraft:select', property='minecraft:display_context',
            cases=[dict(when=HELD, model=pose_select)], fallback=copy.deepcopy(original_item['model']))
        output[ASSETS / f'items/{key}.json'] = encode(wrapper)
        bows[id] = dict(sourceCubes=len(original['elements']), bodyCubes=len(body),
                        maxCubes=len(body)+len(parts(original,cfg)[1]), stringIndex=cfg['string'],
                        arrowIndices=cfg['arrow'], shaftIndex=cfg['shaft'], shaftBridges=cfg['bridges'],
                        authoredFullDrawPull=cfg['pull'], states=[dict(selector=s,name=n) for s,n,_ in states])
    output[ROOT/'art/weapons/w50/manifest.json'] = encode(dict(
        generator='scripts/generate_bow_models_w50.py', steps=STEPS, selectorFloatIndex=2,
        heldContexts=HELD, originalsUnchanged=True, bows=bows, sourceSha256=sources,
        limitations='Authored rigid-limb string/arrow poses only. No hand IK, limb/cam rig, ripped animation or Shadowshot changes. Native client unverified.',
        sha256={str(path.relative_to(ROOT)): sha(raw) for path,raw in output.items()}))
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    outputs = generate()
    for path, raw in outputs.items():
        if args.verify:
            if not path.is_file() or path.read_bytes() != raw:
                raise SystemExit(f'W50 generated asset differs: {path.relative_to(ROOT)}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(f'{"Verified" if args.verify else "Generated"} {len(outputs)} W50 files')
