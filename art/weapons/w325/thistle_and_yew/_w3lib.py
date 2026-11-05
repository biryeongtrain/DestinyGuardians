"""Shared helpers for the W325 worker-3 scout designs (identical copy in every weapon folder; deterministic).

base_top(base)            -> function (z0, z1) giving the base body's top y over the ADS centre band (x 6.6..9.4)
clamp_tops(els, base)     -> lower unrotated elements that rise above the base top profile in the rear two thirds
                             (same rule as kit.py adscheck); names starting with an open-sight prefix are skipped
bevel(e, c, top=True, bottom=False) -> [core, cap(s), 45-degree edge rods] replacing one box with chamfered long edges
flat paint                -> flat_faces.json (written by the worker's smear audit) = {"name/face": [r,g,b]}; FlatPainter
                             returns the flat colour with a 1 texel light top/left edge and dark bottom/right edge
"""
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MODELS = ROOT / 'src/main/resources/assets/destiny/models'


def _rot(p, r, inverse=False):
    if not r: return p
    o = r['origin']; x, y, z = p[0] - o[0], p[1] - o[1], p[2] - o[2]
    seq = [(a, r.get(a, 0)) for a in ('x', 'y', 'z') if r.get(a, 0)]
    if inverse: seq = [(a, -g) for a, g in reversed(seq)]
    for ax, ang in seq:
        a = math.radians(ang); c, s = math.cos(a), math.sin(a)
        if ax == 'x': y, z = y * c - z * s, y * s + z * c
        elif ax == 'y': x, z = x * c + z * s, -x * s + z * c
        else: x, y = x * c - y * s, x * s + y * c
    return (x + o[0], y + o[1], z + o[2])


def corners(e):
    f, t = e['from'], e['to']
    return [_rot((x, y, z), e.get('rotation')) for x in (f[0], t[0]) for y in (f[1], t[1]) for z in (f[2], t[2])]


def _base_elements(base):
    cands = [MODELS / f'weapon_sight_w151/{base}_body.json'] + sorted(MODELS.glob(f'weapon_reload_w*_{base}/{base}_body.json'))
    for p in cands:
        if p.exists():
            els = json.loads(p.read_text()).get('elements')
            if els: return els
    raise SystemExit(f'no base body for {base}')


def base_top(base):
    els = _base_elements(base); cs = [(e, corners(e)) for e in els]
    zs = [p[2] for _, c in cs for p in c]; zmin, zmax = min(zs), max(zs)

    def top(z0, z1):
        best = None
        for e, c in cs:
            if max(p[2] for p in c) < z0 or min(p[2] for p in c) > z1: continue
            if max(p[0] for p in c) < 6.6 or min(p[0] for p in c) > 9.4: continue
            if 'aim' in e.get('name', '') and any(f.get('texture') not in ('#0', None) for f in e.get('faces', {}).values()): continue
            y = max(p[1] for p in c); best = y if best is None or y > best else best
        return best
    top.start = zmin + (zmax - zmin) / 3; top.zmax = zmax
    return top


def limit_over(top, z0, z1, margin=0.12):
    """Lowest allowed top over z0..z1 sampled on the adscheck 0.25 grid."""
    lim = None; z = top.start
    while z < top.zmax:
        if z + .25 >= z0 and z <= z1:
            b = top(z, z + .25)
            v = -1e9 if b is None else b + margin
            lim = v if lim is None or v < lim else lim
        z += .25
    return lim


def clamp_tops(els, base, skip=('sight', 'peep', 'sc_'), margin=0.12):
    top = base_top(base); out = []
    for e in els:
        if e['name'].startswith(skip) or e['name'].startswith('mag_'):
            out.append(e); continue
        c = corners(e); z0, z1 = min(p[2] for p in c), max(p[2] for p in c)
        x0, x1 = min(p[0] for p in c), max(p[0] for p in c)
        lim = limit_over(top, z0, z1, margin) if x1 >= 6.6 and x0 <= 9.4 else None
        ytop = max(p[1] for p in c)
        if lim is None or ytop <= lim:
            out.append(e); continue
        if e.get('rotation'):
            raise SystemExit(f'rotated element {e["name"]} rises {ytop:.2f} above base limit {lim:.2f}: fix by hand')
        if lim <= e['from'][1] + 0.04:
            continue                         # whole element above the allowed profile: drop it
        e = dict(e); e['to'] = [e['to'][0], lim, e['to'][2]]; out.append(e)
    return out


def bevel(e, c, top=True, bottom=False):
    """Chamfer the long (z-direction) top and/or bottom edges of an unrotated box by c (model px)."""
    f, t = list(e['from']), list(e['to']); n = e['name']
    core_f, core_t = list(f), list(t)
    if top: core_t[1] -= c
    if bottom: core_f[1] += c
    out = [dict(e, **{'from': core_f, 'to': core_t})]
    s = c * math.sqrt(2) / 2
    for flag, yb, tag in ((top, t[1] - c, 'bt'), (bottom, f[1] + c, 'bb')):
        if not flag: continue
        y0, y1 = (yb, t[1]) if tag == 'bt' else (f[1], yb)
        out.append({'name': f'{n}_{tag}cap', 'from': [f[0] + c, y0, f[2]], 'to': [t[0] - c, y1, t[2]]})
        for side, xc in (('l', f[0] + c), ('r', t[0] - c)):
            o = [xc, yb, (f[2] + t[2]) / 2]
            out.append({'name': f'{n}_{tag}{side}', 'from': [xc - s, yb - s, f[2] + 0.012], 'to': [xc + s, yb + s, t[2] - 0.012],
                        'rotation': {'origin': o, 'x': 0, 'y': 0, 'z': 45}})
    return out


class FlatPainter:
    def __init__(self, here, g):
        p = Path(here) / 'flat_faces.json'
        self.flat = json.loads(p.read_text()) if p.exists() else {}
        self.g = g                     # design module globals (T is read at bake time)

    def __call__(self, e, fn, s, t):
        c = self.flat.get(f"{e['name']}/{fn}")
        if c is None and '_seg' in e['name']: c = self.flat.get(f"{e['name'].split('_seg')[0]}/{fn}")
        if c is None: return None
        f, to = e['from'], e['to']
        ax = {'north': (0, 1), 'south': (0, 1), 'east': (2, 1), 'west': (2, 1), 'up': (0, 2), 'down': (0, 2)}[fn]
        T = self.g.get('T', 16)
        w = max(1, round(abs(to[ax[0]] - f[ax[0]]) * T)); h = max(1, round(abs(to[ax[1]] - f[ax[1]]) * T))
        i, j = int(s * w), int(t * h)
        k = 0                          # kit pixel style draws the bevel lines itself
        return tuple(max(0, min(255, v + k)) for v in c) + (255,)


_TOPS = {}


def fit(e, base, margin=0.12):
    """Lower one unrotated box so it stays under the base top profile (use before bevel())."""
    top = _TOPS.get(base) or _TOPS.setdefault(base, base_top(base))
    f, t = e['from'], e['to']
    if t[0] < 6.6 or f[0] > 9.4: return e
    lim = limit_over(top, f[2], t[2], margin)
    if lim is None or t[1] <= lim: return e
    return dict(e, to=[t[0], max(lim, f[1] + 0.05), t[2]])


_FA = {'north': (2, 0, 0, False, 1, False), 'south': (2, 1, 0, True, 1, False),
       'east': (0, 1, 2, False, 1, False), 'west': (0, 0, 2, True, 1, False),
       'up': (1, 1, 0, True, 2, True), 'down': (1, 0, 0, True, 2, False)}


def face_pt(e, fn, s, t):
    """Model point of face (s, t) (same frame as kit.face_point)."""
    f, to = e['from'], e['to']; pa, side, ua, ufwd, va, vfwd = _FA[fn]
    p = [0.0] * 3; p[pa] = to[pa] if side else f[pa]
    p[ua] = f[ua] + (to[ua] - f[ua]) * (s if ufwd else 1 - s)
    p[va] = f[va] + (to[va] - f[va]) * (t if vfwd else 1 - t)
    return _rot(tuple(p), e.get('rotation'))


def blob(p, scale=1.0, seed=0.0):
    """Smooth deterministic field in about -1..1 for painted camo (2-3 big blobs per few px)."""
    x, y, z = p[0] / scale, p[1] / scale, p[2] / scale
    return (math.sin(z * 1.1 + y * 1.9 + seed) + math.sin(z * 0.53 - y * 1.3 + x * 2.0 + seed * 1.7)
            + 0.6 * math.sin(z * 2.3 + y * 0.4 - seed)) / 2.6


def step_chamfer(e, c=0.1):
    """DMW-style unrotated step chamfer on the top long edges: core lowered by c + top plate inset c in x."""
    f, t = e['from'], e['to']
    if t[0] - f[0] < 4 * c or t[1] - f[1] < 3 * c: return [e]
    core = dict(e, to=[t[0], t[1] - c, t[2]])
    plate = {'name': e['name'] + '_tp', 'from': [f[0] + c, t[1] - c, f[2]], 'to': [t[0] - c, t[1], t[2]]}
    return [core, plate]


def machine(els, target=150, maxlen=3.0, inset=0.05, gap=0.05, skip=('sight', 'peep', 'sc_', 'mag_', 'trigger', 'barrel',
            'supp', 'muzzle', 'spike', 'rail_t', 'fil_', 'teeth')):
    """Dead Man Walking style split of long unrotated slabs: equal flush segments (all faces on the same planes)
    separated by `gap` wide recessed grooves, over a full-length core inset by `inset` on every side so each groove
    reads as a machined seam.  Largest slabs first, stopping before the element total passes `target`."""
    els = list(els)
    def cand():
        out = []
        for i, e in enumerate(els):
            if e.get('rotation') or e['name'].startswith(skip) or '_seg' in e['name'] or e['name'].endswith(('_tp', 'cap')) or '_core' in e['name']: continue
            f, t = e['from'], e['to']; L = t[2] - f[2]
            if L > maxlen and t[0] - f[0] > 0.3 and t[1] - f[1] > 0.3: out.append((L * (t[1] - f[1]), i))
        return sorted(out, reverse=True)
    while True:
        c = cand()
        if not c: break
        _, i = c[0]; e = els[i]; f, t = e['from'], e['to']; L = t[2] - f[2]
        n = max(2, math.ceil(L / maxlen))
        if len(els) + 2 * n - 2 > target: break
        keep = {kk: vv for kk, vv in e.items() if kk in ('shade', 'light_emission')}
        new = []
        for k in range(1, n):          # groove floor: a short inset plug under each seam (small faces, cheap atlas)
            zg = f[2] + L * k / n
            new.append({'name': f"{e['name']}_core{k}", 'from': [f[0] + inset, f[1] + inset, zg - gap], 'to': [t[0] - inset, t[1] - inset, zg + gap], **keep})
        for k in range(n):
            z0 = f[2] + L * k / n + (gap / 2 if k else 0); z1 = f[2] + L * (k + 1) / n - (gap / 2 if k < n - 1 else 0)
            new.append({'name': f"{e['name']}_seg{k}", 'from': [f[0], f[1], z0], 'to': [t[0], t[1], z1], **keep})
        els[i:i + 1] = new
    return els


def sub(p, name, hw, y0f, y1f, z0f, z1f):
    """Panel on a rotated part: same rotation and origin as the parent, box given as fractions of the parent's
    local y/z extent, so the panel stays parallel and flush with its parent (no near-parallel slabs)."""
    f, t = p['from'], p['to']; xc = (f[0] + t[0]) / 2
    return {'name': name, 'from': [xc - hw, f[1] + (t[1] - f[1]) * y0f, f[2] + (t[2] - f[2]) * z0f],
            'to': [xc + hw, f[1] + (t[1] - f[1]) * y1f, f[2] + (t[2] - f[2]) * z1f], 'rotation': dict(p['rotation'])}


def tidy(els, step=0.012):
    """Remove coplanar overlaps (z-fighting): where two unrotated boxes share a face plane on the same side with
    overlapping area, pull the smaller box's face inward by `step`.  Also keep x-rotated rods/fillets 0.012 inside
    the x faces of the slab they sit in."""
    els = [dict(e, **{'from': list(e['from']), 'to': list(e['to'])}) for e in els]
    vol = lambda e: (e['to'][0] - e['from'][0]) * (e['to'][1] - e['from'][1]) * (e['to'][2] - e['from'][2])
    for _ in range(4):
        changed = False
        ur = [e for e in els if not e.get('rotation')]
        for ia in range(len(ur)):
            for ib in range(ia + 1, len(ur)):
                a, b = ur[ia], ur[ib]
                for ax in range(3):
                    for side, key in ((0, 'from'), (1, 'to')):
                        if abs(a[key][ax] - b[key][ax]) > 0.004: continue
                        ov = 1
                        for j in range(3):
                            if j == ax: continue
                            ov *= max(0, min(a['to'][j], b['to'][j]) - max(a['from'][j], b['from'][j]))
                        if ov <= 0.002: continue
                        s_ = a if vol(a) < vol(b) else b
                        if s_['to'][ax] - s_['from'][ax] <= 3 * step: s_ = b if s_ is a else a
                        s_[key][ax] += step if side == 0 else -step; changed = True
        if not changed: break
    for e in els:
        r = e.get('rotation')
        if r and r.get('x') and not r.get('y') and not r.get('z') and e['to'][0] - e['from'][0] > 0.5:
            for o in els:
                if o is e or o.get('rotation'): continue
                for k, j in (('from', 0), ('to', 0)):
                    if abs(o[k][j] - e[k][j]) < 0.004: e[k][j] += 0.012 if k == 'from' else -0.012
    return els

def zslice(e, step):
    """Split an unrotated box along z into ~step-long pieces (so clamp_tops can follow a curved base profile)."""
    f, t = e['from'], e['to']; L = t[2] - f[2]; n = max(1, round(L / step))
    if n == 1: return [e]
    return [dict(e, name=f"{e['name']}_z{k}", **{'from': [f[0], f[1], f[2] + L * k / n], 'to': [t[0], t[1], f[2] + L * (k + 1) / n]})
            for k in range(n)]


def adopt(els, child, parent, hw, y0f, y1f, z0f, z1f):
    """Replace element `child` with a sub() panel of `parent` (same rotation/origin, flush and parallel)."""
    p = next(e for e in els if e['name'] == parent)
    return [sub(p, child, hw, y0f, y1f, z0f, z1f) if e['name'] == child else e for e in els]


def _section(poly, z):
    """y range of a convex (z, y) polygon at z."""
    ys = []
    n = len(poly)
    for i in range(n):
        (z0, y0), (z1, y1) = poly[i], poly[(i + 1) % n]
        if (z0 - z) * (z1 - z) <= 0 and z0 != z1:
            ys.append(y0 + (y1 - y0) * (z - z0) / (z1 - z0))
        elif z0 == z == z1: ys += [y0, y1]
    return (min(ys), max(ys)) if ys else None


def stairify(e, n, quant=0.0):
    """Replace an x-rotated slab by n axis-aligned steps (Dead Man Walking style): neighbours share z planes and
    exact x faces, each step covers the slab's section at its strip centre.  quant snaps y to a grid if > 0."""
    c = corners(e)
    pts = sorted({(round(p[2], 5), round(p[1], 5)) for p in c})
    # convex hull in (z, y)
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    poly = lo[:-1] + up[:-1]
    z0, z1 = min(p[0] for p in poly), max(p[0] for p in poly)
    x0, x1 = e['from'][0], e['to'][0]; out = []
    for k in range(n):
        za, zb = z0 + (z1 - z0) * k / n, z0 + (z1 - z0) * (k + 1) / n
        s = _section(poly, (za + zb) / 2)
        if not s or s[1] - s[0] < 0.08: continue
        ya, yb = s
        if quant: ya, yb = round(ya / quant) * quant, round(yb / quant) * quant
        out.append({'name': f"{e['name']}_st{k}", 'from': [x0, ya, za], 'to': [x1, yb, zb],
                    **{kk: vv for kk, vv in e.items() if kk in ('shade', 'light_emission')}})
    return out


def stairs_for(els, names, n):
    out = []
    for e in els:
        out += stairify(e, n) if e['name'] in names else [e]
    return out
