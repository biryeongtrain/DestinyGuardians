"""Read-only coincident texel audit for axis-aligned Dreg-Light models.

Coordinates are rounded to 0.001 model pixels to absorb five-decimal export
rounding. This measures coincident texel centers, not arbitrary intersections,
camera visibility, animation deformation or GPU depth precision.
"""
import argparse
import base64
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

# depth, horizontal, vertical axes and texture directions from the baker.
FACES = {'north': (2, 0, 1, -1, -1), 'south': (2, 0, 1, 1, -1),
         'east': (0, 2, 1, -1, -1), 'west': (0, 2, 1, 1, -1),
         'up': (1, 0, 2, 1, 1), 'down': (1, 0, 2, 1, -1)}


def audit(model):
    owners = {}
    def walk(nodes, owner=None):
        for node in nodes:
            if isinstance(node, str):
                owners[node] = owner
            else:
                if any(node.get('rotation', [0, 0, 0])):
                    raise ValueError('Rotated groups require evaluated world transforms')
                walk(node.get('children', []), node['uuid'])
    walk(model['outliner'])
    textures = [np.asarray(Image.open(io.BytesIO(base64.b64decode(t['source'].split(',', 1)[1]))).convert('RGBA'))
                for t in model['textures']]
    reports = {}
    for direction, (da, ua, va, us, vs) in FACES.items():
        coords, colors, bones = [], [], []
        owner_ids = {}
        for element in model['elements']:
            if any(element.get('rotation', [0, 0, 0])):
                raise ValueError('Rotated elements require evaluated world transforms')
            face = element['faces'].get(direction)
            if not face or face.get('texture') is None:
                continue
            low, high = np.array(element['from']), np.array(element['to'])
            if low[da] != high[da]:
                raise ValueError('Expected zero-thickness slices')
            uv = face['uv']
            if any(v != int(v) for v in uv):
                raise ValueError('Expected integral texel rectangles')
            x0, y0, x1, y1 = map(int, uv)
            tile = textures[int(face['texture'])][y0:y1, x0:x1]
            rows, cols = np.nonzero(tile[..., 3] > 25)
            if not len(rows):
                continue
            u, v = (cols + .5)/(x1-x0), (rows + .5)/(y1-y0)
            if us < 0: u = 1-u
            if vs < 0: v = 1-v
            xyz = np.zeros((len(rows), 3))
            xyz[:, da] = low[da]
            xyz[:, ua] = low[ua] + u*(high[ua]-low[ua])
            xyz[:, va] = low[va] + v*(high[va]-low[va])
            coords.append(np.rint(xyz*1000).astype(np.int64))
            colors.append(tile[rows, cols, :3])
            owner = owners[element['uuid']]
            owner_ids.setdefault(owner, len(owner_ids))
            bones.append(np.full(len(rows), owner_ids[owner], np.int32))
        if not coords:
            reports[direction] = {'supported': 0, 'coincident_excess': 0}
            continue
        xyz, rgb, bone = np.concatenate(coords), np.concatenate(colors), np.concatenate(bones)
        order = np.lexsort((xyz[:, 2], xyz[:, 1], xyz[:, 0]))
        xyz, rgb, bone = xyz[order], rgb[order], bone[order]
        equal = np.all(xyz[1:] == xyz[:-1], axis=1)
        cross = equal & (bone[1:] != bone[:-1])
        difference = np.max(np.abs(rgb[1:].astype(int)-rgb[:-1].astype(int)), axis=1)
        reports[direction] = dict(supported=len(xyz), coincident_excess=int(equal.sum()),
                                  cross_bone_adjacent=int(cross.sum()),
                                  color_difference_gt16=int((equal & (difference > 16)).sum()))
    return dict(coordinate_tolerance_model_pixels=.001, directions=reports,
                limitation='Same-facing coincident texel centers only; not visibility or arbitrary overlap')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.model.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
