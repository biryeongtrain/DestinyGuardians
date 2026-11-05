"""Find coplanar same-facing overlapping faces (z-fighting) between elements of a built skin (unrotated or identical rotation)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
wid = sys.argv[1]
d = json.loads((ROOT / f'src/main/resources/destiny/weapon_skins/{wid}.json').read_text())
for part in ('body', 'magazine'):
    els = d['parts'][part]
    def rk(e):
        r = e.get('rotation'); return None if not r else (tuple(r['origin']), r.get('x', 0), r.get('y', 0), r.get('z', 0))
    out = []
    for i, a in enumerate(els):
        for b in els[i + 1:]:
            if rk(a) != rk(b): continue
            for ax in range(3):
                o = [k for k in range(3) if k != ax]
                for side in (0, 1):
                    pa = (a['from'], a['to'])[side][ax]; pb = (b['from'], b['to'])[side][ax]
                    if abs(pa - pb) > 0.004: continue
                    ov = 1
                    for k in o:
                        lo = max(min(a['from'][k], a['to'][k]), min(b['from'][k], b['to'][k]))
                        hi = min(max(a['from'][k], a['to'][k]), max(b['from'][k], b['to'][k]))
                        ov *= max(0, hi - lo)
                    if ov > 0.01: out.append((round(ov, 3), a['name'], b['name'], 'xyz'[ax] + ('-' if side == 0 else '+')))
    for r in sorted(out, reverse=True): print(part, r)
