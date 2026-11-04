#!/usr/bin/env python3
"""Build exact flattened W50 composites for isolated Blockbench inspection, not game frames."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT/'src/main/resources/assets/destiny'


def make(id, state):
    bb = json.loads((ROOT/f'art/blockbench/weapons/w30/{id}.bbmodel').read_text())
    body = json.loads((ASSETS/f'models/weapon_bow_w50/{id}_body_hip.json').read_text())
    moving = json.loads((ASSETS/f'models/weapon_bow_w50/{id}_{state}_hip.json').read_text())
    bb['name'] = f'W50 {id} {state}'
    bb['elements'] = []
    for i, e in enumerate(body['elements'] + moving['elements']):
        element = copy.deepcopy(e)
        element.update(type='cube', name=f'{"body" if i<len(body["elements"]) else "moving"}_{i:03}',
                       uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, f'destiny:w50/{id}/{state}/{i}')), box_uv=False)
        rotation = element.pop('rotation', None)
        element['origin'] = rotation['origin'] if rotation else [8, 8, 8]
        if rotation:
            element['rotation'] = [rotation['angle'] if axis == rotation['axis'] else 0 for axis in 'xyz']
        for face in element['faces'].values():
            face['texture'] = 0
        bb['elements'].append(element)
    bb['outliner'] = [e['uuid'] for e in bb['elements']]
    bb['display'] = body['display']
    bb['destiny_w50'] = dict(state=state, sourceModels=[f'{id}_body_hip', f'{id}_{state}_hip'],
                            cubes=len(bb['elements']), evidence='Exact runtime composite flattened; not a Minecraft framebuffer')
    return (json.dumps(bb, ensure_ascii=False, indent=2)+'\n').encode()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    for id in ('biting_winds', 'whispering_slab'):
        for state in ('loaded', 'draw_20', 'empty', 'nock_10'):
            # Only the two full-draw editable projects are deliverables. Intermediates are private QA fixtures.
            folder = ROOT/('art/blockbench/weapons/w50' if state == 'draw_20' else 'run/private-sources/w50/previews')
            path = folder/f'{id}_{state}.bbmodel'
            raw = make(id, state)
            if args.verify:
                assert path.read_bytes() == raw, path
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            print(path.relative_to(ROOT), len(raw), hashlib.sha256(raw).hexdigest())
