"""Worktree copy of the master's kit.py adscheck (this worktree's kit.py predates it and must not be edited).
Logic identical to /Users/qf/IdeaProjects/DestinyGuardians/scripts/art/w325/kit.py adscheck; additionally lists the
skin elements that reach the offending top and whether they are named 'sight' (allowed hollow sight frame)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/art/w325'))
import kit
from kit import rotate, rot_of, reg, ASSETS, skin_path


def _corners(e):
    f, t = e['from'], e['to']; rot = rot_of(e)
    return [rotate((x, y, z), rot) for x in (f[0], t[0]) for y in (f[1], t[1]) for z in (f[2], t[2])]


def adscheck(wid):
    r = reg(wid); base = r['base']; md = ASSETS / 'models'
    cands = [md / f'weapon_sight_w151/{base}_body.json'] + sorted(md.glob(f'weapon_reload_w*_{base}/{base}_body.json')) \
        + sorted(md.glob(f'weapon/*/{base}.json'))
    src = next((p for p in cands if p.exists() and json.loads(p.read_text()).get('elements')), None)
    base_els = json.loads(src.read_text())['elements']
    skin = json.loads(skin_path(wid).read_text())['parts']['body']
    def top(els, z0, z1, band=(6.6, 9.4), who=False):
        best = None; names = []
        for e in els:
            c = _corners(e)
            if max(p[2] for p in c) < z0 or min(p[2] for p in c) > z1: continue
            if max(p[0] for p in c) < band[0] or min(p[0] for p in c) > band[1]: continue
            if any(f.get('texture') not in ('#0', None) for f in e.get('faces', {}).values()) and 'aim' in e.get('name', ''): continue
            y = max(p[1] for p in c); names.append((y, e['name']))
            best = y if best is None or y > best else best
        return (best, names) if who else best
    zs = [p[2] for e in base_els for p in _corners(e)]
    zmin, zmax = min(zs), max(zs); start = zmin + (zmax - zmin) / 3
    bad = []; z = start; nonsight = 0
    while z < zmax:
        b = top(base_els, z, z + .25); k, names = top(skin, z, z + .25, who=True)
        if k is not None and (b is None or k > b + .15):
            over = sorted({n for y, n in names if y > (b or -99) + .15})
            if any('sight' not in n for n in over): nonsight += 1
            bad.append((round(z, 2), round(k, 2), None if b is None else round(b, 2), over))
        z += .25
    print(f'adscheck {wid} vs {src.relative_to(ROOT)}: z {start:.2f}..{zmax:.2f}')
    if not bad: print('  OK: skin never rises above the base top profile behind the front third'); return
    print(f'  ABOVE BASE: {len(bad)} slices, {nonsight} with non-sight elements')
    for row in bad: print('   ', row)


adscheck(sys.argv[1])
