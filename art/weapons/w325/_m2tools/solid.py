"""W325 worker m2 shared authoring helpers for design.py files (pure Python, deterministic).

B()        plain cube (optional single-axis rotation)
bar()      z-long bar with 45 deg chamfered long edges (top/bottom), built as a core + narrow cap + rotated edge prisms
vbar()     y-long (vertical) bar with chamfered vertical edges (front/back), prisms rotated about y
Flat       flat-colour face painter for design.special: base colour + slight vertical shade; kit adds the 1px edge
           highlight/shadow afterwards.  Colours are sampled from the rip projection (graded like the kit bake).
"""
import json, math, sys
from pathlib import Path
R2 = math.sqrt(2.0)
ROOT = Path(__file__).resolve().parents[4]


def B(name, lo, hi, rot=None, origin=None, **kw):
    e = {'name': name, 'from': [round(v, 4) for v in lo], 'to': [round(v, 4) for v in hi]}
    if rot:
        e['rotation'] = {'origin': [round(v, 4) for v in origin], 'x': 0, 'y': 0, 'z': 0}
        e['rotation'][rot[0]] = rot[1]
    e.update(kw)
    return e


def bar(name, x0, x1, y0, y1, z0, z1, c=0.15, top=True, bottom=False, seg=None, at=None):
    """z-long box with chamfered long edges. top only: 4 elements; top+bottom: 6 elements.
    seg=L (or at=[z cuts]): Dead Man Walking style - split into machined blocks <= L px long, each with its own
    chamfers, joined by a recessed 0.08 px groove core (1 extra element per joint)."""
    if seg or at:
        cuts = list(at) if at else [z0 + (z1 - z0) * k / max(1, round((z1 - z0) / seg + .49)) for k in range(1, max(1, round((z1 - z0) / seg + .49)))]
        zs = [z0] + cuts + [z1]; out = []
        for k in range(len(zs) - 1):
            a0 = zs[k] + (.04 if k else 0); a1 = zs[k + 1] - (.04 if k < len(zs) - 2 else 0)
            out += bar(f'{name}_{k}' if k else name, x0, x1, y0, y1, a0, a1, c, top, bottom)
            if k:
                g = .07
                out.append(B(f'{name}_joint_{k}', (x0 + g, y0 + (g if bottom else 0) + (0 if bottom else E2), zs[k] - .04), (x1 - g, y1 - (g if top else 0) - (0 if top else E2), zs[k] + .04)))
        return out
    out = []
    ya = y0 + (c if bottom else 0); yb = y1 - (c if top else 0)
    out.append(B(name, (x0, ya, z0), (x1, yb, z1)))
    if top and bottom:
        out.append(B(name + '_mid', (x0 + c, y0, z0 + E), (x1 - c, y1, z1 - E)))
    elif top:
        out.append(B(name + '_cap', (x0 + c, yb, z0), (x1 - c, y1, z1)))
    elif bottom:
        out.append(B(name + '_cap', (x0 + c, y0, z0), (x1 - c, ya, z1)))
    s = c / R2
    zc = (z0 + z1) / 2
    corners = []
    if top: corners += [('tl', x0 + c, y1 - c), ('tr', x1 - c, y1 - c)]
    if bottom: corners += [('bl', x0 + c, y0 + c), ('br', x1 - c, y0 + c)]
    for tag, cx, cy in corners:
        out.append(B(f'{name}_ch_{tag}', (cx - s, cy - s, z0 + E), (cx + s, cy + s, z1 - E), ('z', 45), (cx, cy, zc)))
    return out


def vbar(name, x0, x1, y0, y1, z0, z1, c=0.15, front=True, back=True):
    """y-long box with chamfered vertical edges at the front (-z) and/or back (+z)."""
    out = []
    za = z0 + (c if front else 0); zb = z1 - (c if back else 0)
    out.append(B(name, (x0, y0, za), (x1, y1, zb)))
    out.append(B(name + '_mid', (x0 + c, y0 + E, z0), (x1 - c, y1 - E, z1)))
    s = c / R2; yc = (y0 + y1) / 2
    corners = []
    if front: corners += [('fl', x0 + c, z0 + c), ('fr', x1 - c, z0 + c)]
    if back: corners += [('bl', x0 + c, z1 - c), ('br', x1 - c, z1 - c)]
    for tag, cx, cz in corners:
        out.append(B(f'{name}_ch_{tag}', (cx - s, y0 + E, cz - s), (cx + s, y1 - E, cz + s), ('y', 45), (cx, yc, cz)))
    return out


def octo(name, cx, cy, r, z0, z1, axis='z'):
    """Exact regular octagon tube (apothem r) as the union of 4 inscribed face-to-face strips: two axis-aligned and two
    rotated 45 deg.  No spikes past the faces (the old box + 45 deg twin made an 8-point star).  Secondary strips are
    recessed 0.006..0.018 px at the ends so the end faces do not z-fight.  axis='x': tube along x (cx = z, cy = y)."""
    k = r * math.tan(math.pi / 8)
    def box(n, a, b, d, rot):
        lo, hi = (cx - a, cy - b, z0 + d), (cx + a, cy + b, z1 - d)
        if axis == 'x':
            lo, hi = (lo[2], lo[1], lo[0]), (hi[2], hi[1], hi[0])
            org = ((z0 + z1) / 2, cy, cx)
        else:
            org = (cx, cy, (z0 + z1) / 2)
        return B(n, lo, hi, (axis, 45) if rot else None, org if rot else None)
    return [box(name, r, k, 0, False), box(name + '_oct', k, r, .006, False),
            box(name + '_d1', r, k, .012, True), box(name + '_d2', k, r, .018, True)]


E = 0.008       # recess of secondary pieces on planes they share with the main block (no coplanar z-fighting)
E2 = 0.008


def clean(els, eps=0.004, rec=0.01):
    """Remove coplanar same-facing overlaps between unrotated (or identically rotated) elements: the larger face is
    recessed 0.01 px so the smaller (accent) face wins.  Returns the list (modified in place)."""
    def rk(e):
        r = e.get('rotation'); return None if not r else (tuple(r['origin']), r.get('x', 0), r.get('y', 0), r.get('z', 0))
    def area(e, ax):
        o = [k for k in range(3) if k != ax]; return abs(e['to'][o[0]] - e['from'][o[0]]) * abs(e['to'][o[1]] - e['from'][o[1]])
    for _ in range(3):
        changed = False
        for i, a in enumerate(els):
            for b in els[i + 1:]:
                if rk(a) != rk(b) or a['name'].startswith('mag_') != b['name'].startswith('mag_'): continue
                for ax in range(3):
                    o = [k for k in range(3) if k != ax]
                    for side in (0, 1):
                        ka = 'from' if (a['from'][ax] <= a['to'][ax]) == (side == 0) else 'to'
                        kb = 'from' if (b['from'][ax] <= b['to'][ax]) == (side == 0) else 'to'
                        if abs(a[ka][ax] - b[kb][ax]) > eps: continue
                        ov = 1
                        for k in o:
                            lo = max(min(a['from'][k], a['to'][k]), min(b['from'][k], b['to'][k]))
                            hi = min(max(a['from'][k], a['to'][k]), max(b['from'][k], b['to'][k]))
                            ov *= max(0, hi - lo)
                        if ov <= 1e-4: continue
                        big, kk = (a, ka) if area(a, ax) >= area(b, ax) else (b, kb)
                        big[kk][ax] = round(big[kk][ax] + (rec if side == 0 else -rec), 4); changed = True
        if not changed: break
    return els


class Flat:
    """Flat-colour painter. rules: list of (predicate(name, face) -> bool, rgb).  shade: vertical gradient strength."""
    def __init__(self, rules, shade=0.06):
        self.rules = rules; self.shade = shade

    def __call__(self, e, fn, s, t):
        for pred, rgb in self.rules:
            if pred(e['name'], fn):
                k = 1.0 + self.shade * (0.5 - t) if fn not in ('up', 'down') else 1.0
                return tuple(max(0, min(255, int(round(c * k)))) for c in rgb) + (255,)
        return None


def rip_colour(wid, model2world, pts, view='nx'):
    """Median graded rip colour around model points (x,y,z) seen from one cached view (for flat paint colours)."""
    sys.path.insert(0, str(ROOT / 'scripts/art/w325'))
    import kit
    cache = kit.art(wid) / 'proj_cache'; man = json.loads((cache / 'manifest.json').read_text())
    v = kit.View(cache, view, man); cs = []
    for p in pts:
        for dy in (-.1, 0, .1):
            for dz in (-.1, 0, .1):
                q = (p[0], p[1] + dy, p[2] + dz); x, y = v.project(model2world('probe', q)); c = v.sample(x, y)
                if c: cs.append(kit.default_grade(c))
    cs.sort(key=lambda c: sum(c))
    return tuple(int(v) for v in cs[len(cs) // 2]) if cs else (70, 70, 72)
