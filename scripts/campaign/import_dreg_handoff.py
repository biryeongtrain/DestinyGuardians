"""W300: import the Dreg-Light handoff (dreg_combat.bbmodel, 19 bones, 13 retargeted D2 clips) as rg_dreg.

Source (read-only): ~/Downloads/Dreg-Light-Handoff/Dreg-Light/dreg_combat.bbmodel
sha256 96afa5f0e97f5478b4fb769b71ae45fde0e76e4a53b494f820b8bdd5944e3510

Changes made on top of the handoff (geometry/texture/clips otherwise untouched):
  * name -> rg_dreg, provenance block 'w300'.
  * eyes_glow bone under head: 4 emissive eye quads just in front of the (black, unlit-material) eye sockets,
    textured from a cyan patch painted into an unused, fully transparent atlas cell (light_emission 15).
  * clip aliases required by FallenModels/RisingServices.INFANTRY_CLIPS: shoot<-fire, hit<-hurt,
    stagger<-hurt, spawn<-surprise_front, run<-walk (time-scaled x0.72). Original 14 clips are kept.
Usage: python3 import_dreg_handoff.py <handoff.bbmodel> <out rg_dreg.bbmodel>
"""
import base64, copy, hashlib, io, json, sys, uuid
from PIL import Image

NS = uuid.UUID('6f1b8d9e-3c1d-4f4e-9a57-5d0c2b9a3001')
def uid(*p): return str(uuid.uuid5(NS, '/'.join(p)))

src, out = sys.argv[1], sys.argv[2]
raw = open(src, 'rb').read()
d = json.loads(raw)
tex = d['textures'][0]
atlas = Image.open(io.BytesIO(base64.b64decode(tex['source'].split(',', 1)[1]))).convert('RGBA')
W = atlas.width

# ---- owners / groups
owner = {}
groups = {}
def walk(g):
    groups[g['name']] = g
    for c in g['children']:
        if isinstance(c, str): owner[c] = g['name']
        else: walk(c)
for g in d['outliner']: walk(g)
els = {e['uuid']: e for e in d['elements']}

# ---- House of Dusk palette (Bungie Dusk Dreg render, Destinypedia "Render of a Dreg belonging to the House of Dusk").
# data/dreg_material_map.png labels each atlas texel with the nearest source D2 material (dreg_material_map.py);
# each material is re-dyed keeping the source texel value detail (value / material median) x target colour.
import os
import numpy as np
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
mats = json.load(open(os.path.join(DATA, 'dreg_material_map.json')))
M = np.asarray(Image.open(os.path.join(DATA, 'dreg_material_map.png'))).copy()
A = np.asarray(atlas).astype(np.float32)
CLOTH = [mats.index('80E12DD0'), mats.index('80E12F18')]
SKIN = mats.index('80E1D357'); HANDSKIN = len(mats)
for e in d['elements']:
    f = next(v for v in e['faces'].values() if v.get('texture') is not None)
    u0, v0, u1, v1 = [int(x) for x in f['uv']]
    sl = (slice(min(v0, v1), max(v0, v1)), slice(min(u0, u1), max(u0, u1)))
    sub = M[sl]; vis = A[sl][..., 3] > 0
    if not vis.any(): continue
    for c in CLOTH:   # quads that are mostly cloth are all cloth (removes plate/strap speckle on the cowl)
        if (sub[vis] == c).mean() > 0.5: sub[vis] = c
    o = owner.get(e['uuid'], ''); cy = (e['from'][1] + e['to'][1]) / 2
    if o.startswith(('hand_', 'foot_')) or (o.startswith('lower_forearm') and cy < 17.0): sub[vis & (sub == SKIN)] = HANDSKIN
PAL = {'80E12DD0': (0.38, 0.26, 0.45), '80E12F18': (0.38, 0.26, 0.45),   # Dusk violet cowl + tabard
       '80E1D0A6': (0.40, 0.28, 0.21),                                   # leather straps / wraps
       '80E1D0AD': (0.58, 0.56, 0.55), '80E1D1BF': (0.46, 0.44, 0.44),   # worn steel helmet, pauldron, knee, bracers
       '80E1D357': (0.27, 0.25, 0.27),                                   # dark hide (torso / limbs)
       'HAND': (0.46, 0.33, 0.42), '80E1D1A7': (0.48, 0.35, 0.43),       # mauve hands / feet
       '80E12DBD': (0.33, 0.21, 0.40), '80E1D621': (0.84, 0.78, 0.62)}   # violet crest, bone spikes
rgb = A[..., :3] / 255; lum = rgb @ np.array([.299, .587, .114]); vis = A[..., 3] > 0; dyed = rgb.copy()
for name, col in PAL.items():
    m = (M == (HANDSKIN if name == 'HAND' else mats.index(name))) & vis
    if not m.any(): continue
    r = np.clip(lum / np.median(lum[m]), 0.2, 1.9)[..., None]
    dyed[m] = np.clip(np.array(col) * r, 0, 1)[m] * 0.9 + rgb[m] * 0.1
A[..., :3] = dyed * 255
atlas = Image.fromarray(A.astype(np.uint8), 'RGBA').copy()

# ---- find a free transparent 16x16 cell not referenced by any UV
used = set()
for e in d['elements']:
    for f in e['faces'].values():
        if f.get('texture') is None: continue
        u0, v0, u1, v1 = f['uv']
        for cx in range(int(min(u0, u1)) // 16, int(max(u0, u1) - 1e-6) // 16 + 1):
            for cy in range(int(min(v0, v1)) // 16, int(max(v0, v1) - 1e-6) // 16 + 1):
                used.add((cx, cy))
px = atlas.load()
cell = None
for cy in range(W // 16 - 1, -1, -1):
    for cx in range(W // 16 - 1, -1, -1):
        if (cx, cy) in used: continue
        if all(px[cx * 16 + i, cy * 16 + j][3] == 0 for i in range(16) for j in range(16)):
            cell = (cx * 16, cy * 16); break
    if cell: break
assert cell, 'no free atlas cell'

# eye patch: 16x8 radial cyan, opaque (cutout atlas keeps alpha binary)
ex, ey = cell
for i in range(16):
    for j in range(8):
        dx = (i + .5 - 8) / 8; dy = (j + .5 - 4) / 4
        t = max(0.0, 1 - (dx * dx + dy * dy) ** .5)
        r = int(60 + 170 * t ** 1.6); g = int(190 + 65 * t); b = 255
        px[ex + i, ey + j] = (r, min(255, g), b, 255)
patch = [ex, ey, ex + 16, ey + 8]

# ---- eye socket depth from the black head-front texels
def socket_front(x0, x1, y0, y1):
    best = None
    for e in d['elements']:
        if owner.get(e['uuid']) != 'head': continue
        f = e['faces']['north']
        if f.get('texture') is None: continue
        if e['to'][0] <= x0 or e['from'][0] >= x1 or e['to'][1] <= y0 or e['from'][1] >= y1: continue
        z = e['from'][2]
        best = z if best is None else min(best, z)
    return best
head = groups['head']
eyes = [('eye_ul', -1.12, -0.60, 26.78, 27.12), ('eye_ur', 0.60, 1.12, 26.78, 27.12),
        ('eye_ll', -0.66, -0.36, 26.32, 26.58), ('eye_lr', 0.36, 0.66, 26.32, 26.58)]
# mirrored pairs share the frontmost socket depth so the face stays symmetric
pair_z = {}
for n, x0, x1, y0, y1 in eyes:
    k = n[-2]; z = socket_front(x0, x1, y0, y1)
    pair_z[k] = z if k not in pair_z else min(pair_z[k], z)
glow_children = []
for name, x0, x1, y0, y1 in eyes:
    z = pair_z[name[-2]] - 0.03
    e = {'type': 'cube', 'name': name, 'uuid': uid('eye', name), 'origin': list(head['origin']), 'rotation': [0, 0, 0],
         'from': [x0, y0, z], 'to': [x1, y1, z], 'box_uv': False, 'light_emission': 15,
         'faces': {k: ({'uv': patch, 'texture': 0} if k == 'north' else {'uv': [0, 0, 0, 0], 'texture': None})
                   for k in ('north', 'south', 'east', 'west', 'up', 'down')}}
    d['elements'].append(e); glow_children.append(e['uuid'])
head['children'].append({'uuid': uid('bone', 'eyes_glow'), 'name': 'eyes_glow', 'origin': list(head['origin']),
                         'export': True, 'visibility': True, 'children': glow_children})

buf = io.BytesIO(); atlas.save(buf, 'PNG', optimize=True)
tex['source'] = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

# ---- clip aliases
clips = {a['name']: a for a in d['animations']}
def alias(new, old, scale=1.0):
    a = copy.deepcopy(clips[old]); a['name'] = new; a['uuid'] = uid('clip', new)
    a['length'] = round(a['length'] * scale, 6)
    for anim in a['animators'].values():
        for k in anim.get('keyframes', []):
            k['time'] = round(k['time'] * scale, 6); k['uuid'] = uid('kf', new, k['uuid'])
    d['animations'].append(a)
alias('shoot', 'fire'); alias('hit', 'hurt'); alias('stagger', 'hurt'); alias('spawn', 'surprise_front')
alias('run', 'walk', 0.72)

d['name'] = 'rg_dreg'
d['w300'] = {'source': 'Dreg-Light-Handoff/dreg_combat.bbmodel', 'source_sha256': hashlib.sha256(raw).hexdigest(),
             'generator': 'scripts/campaign/import_dreg_handoff.py',
             'added': ['house_of_dusk_palette', 'eyes_glow', 'shoot', 'hit', 'stagger', 'spawn', 'run']}
json.dump(d, open(out, 'w'), separators=(',', ':'))
print('cell', cell, 'elements', len(d['elements']), 'clips', [a['name'] for a in d['animations']])
