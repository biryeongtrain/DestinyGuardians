"""Print the base body top profile (centre band x 6.6..9.4) per 0.5 px z, as used by adscheck."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/art/w325')); sys.path.insert(0, str(Path(__file__).parent))
import kit
base = sys.argv[1]
els = json.loads((kit.ASSETS / f'models/weapon_sight_w151/{base}_body.json').read_text())['elements']
def corners(e):
    f, t = e['from'], e['to']; r = kit.rot_of(e)
    return [kit.rotate((x, y, z), r) for x in (f[0], t[0]) for y in (f[1], t[1]) for z in (f[2], t[2])]
z = -10.0
while z < 17:
    ys = [max(p[1] for p in c) for c in map(corners, els) if not (max(p[2] for p in c) < z or min(p[2] for p in c) > z + .25)
          and not (max(p[0] for p in c) < 6.6 or min(p[0] for p in c) > 9.4)]
    print(f'{z:6.2f} {max(ys) if ys else None}')
    z += .5
