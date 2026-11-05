"""W325 hand-cannon authoring helpers (identical copy in each w325-6 hand-cannon folder; deterministic, stdlib only).

Parts are authored in the rip's -x side image (proj_cache/nx_albedo.png, 800 px/m) coordinates and converted to model px
by one calibration: the rip cylinder centre (image px) lands on the base cylinder centre (model z,y), uniform scale S
model px per metre along the gun, SX laterally.  Moved/resized parts carry a per-prefix warp (model -> rip-equivalent
model point) so the projection still samples the matching rip surface.
"""
import json, math
from pathlib import Path


class Cal:
    def __init__(self, cache, img_c, model_c, S, SX, muzzle_neg_y=True, front=None):
        man = json.loads((Path(cache) / 'manifest.json').read_text())
        v = man['views']['nx']; self.ppm = man['ppm']; W, H = v['res']
        cy, cz = v['centre'][1], v['centre'][2]
        self.xic, self.yic = img_c; self.zc, self.yc = model_c; self.S, self.SX = S, SX
        self.f = 1 if muzzle_neg_y else -1
        self.ywc = cy - (self.xic - W / 2) / self.ppm; self.zwc = cz + (H / 2 - self.yic) / self.ppm
        self.k = S / self.ppm
        self.warps = []          # (prefix, fn(model p) -> rip-equivalent model p)
        self.front = front       # (break xi, scale): stretch the gun ahead of the break (short barrels -> base muzzle)
        if front: self.zb = self.zc - self.f * (front[0] - self.xic) * self.k

    def z(self, xi):
        z = self.zc - self.f * (xi - self.xic) * self.k
        if self.front and z < self.zb: z = self.zb + (z - self.zb) * self.front[1]
        return z
    def y(self, yi): return self.yc + (self.yic - yi) * self.k

    def to_world(self, p):
        x, y, z = p
        if self.front and z < self.zb: z = self.zb + (z - self.zb) / self.front[1]
        return (-self.f * (x - 8) / self.SX, self.ywc + self.f * (z - self.zc) / self.S, self.zwc + (y - self.yc) / self.S)

    def model2world(self, name, p):
        for pre, fn in self.warps:
            if name.startswith(pre):
                p = fn(p); break
        return self.to_world(p)

    def img(self, name, p):
        """Model point -> rip nx image (xi, yi) after the part warps (inverse of z()/y())."""
        for pre, fn in self.warps:
            if name.startswith(pre): p = fn(p); break
        x, y, z = p
        if self.front and z < self.zb: z = self.zb + (z - self.zb) / self.front[1]
        return (self.xic - (z - self.zc) / (self.f * self.k), self.yic - (y - self.yc) / self.k)

    # ---- authoring
    def R(self, name, xi0, yi0, xi1, yi1, x0, x1, **kw):
        za, zb = sorted((self.z(xi0), self.z(xi1))); ya, yb = sorted((self.y(yi0), self.y(yi1)))
        e = dict(name=name, **{'from': [x0, ya, za], 'to': [x1, yb, zb]}); e.update(kw); return e


def box(name, lo, hi, **kw):
    e = {'name': name, 'from': list(lo), 'to': list(hi)}; e.update(kw); return e


def tilt_box(name, p0, L, Wd, x0, x1, t):
    """Box hanging from top-front point p0=(z,y): length L downward, width Wd toward the back, down axis leaning t deg
    toward +z (grips).  Rotation about x at p0."""
    z0, y0 = p0
    return {'name': name, 'from': [x0, y0 - L, z0], 'to': [x1, y0, z0 + Wd],
            'rotation': {'origin': [8.0, y0, z0], 'x': -t, 'y': 0, 'z': 0}}


def perp_warp(p0, t, k):
    """Undo a squeeze by k of the distance behind the line through p0 (z,y) leaning t deg (grip thickness)."""
    a = math.radians(t); nz, ny = math.cos(a), math.sin(a)
    def fn(p):
        x, y, z = p; u = (z - p0[0]) * nz + (y - p0[1]) * ny; d = u / k - u
        return (x, y + ny * d, z + nz * d)
    return fn


def lin_warp(axis, m0, m1, r0, r1):
    i = {'x': 0, 'y': 1, 'z': 2}[axis]
    def fn(p):
        q = list(p); q[i] = r0 + (p[i] - m0) * (r1 - r0) / (m1 - m0); return tuple(q)
    return fn


def octo(name, c, r, x_half, z0, z1, n=2, **kw):
    """Round-ish prism along z: n boxes rotated about z (0, 90/n ...)."""
    out = []
    for i in range(n):
        out.append({'name': f'{name}_{i}', 'from': [c[0] - x_half, c[1] - r, z0], 'to': [c[0] + x_half, c[1] + r, z1],
                    'rotation': {'origin': [c[0], c[1], (z0 + z1) / 2], 'x': 0, 'y': 0, 'z': 180 / n * i}, **kw})
    return out


def hwarp(p0, t, k):
    """Undo a horizontal squeeze by k of everything behind the line through p0 (z,y) leaning t deg (grip thickness)."""
    tn = math.tan(math.radians(t))
    def fn(p):
        x, y, z = p; zf = p0[0] + (p0[1] - y) * tn
        return (x, y, zf + (z - zf) / k) if z > zf else p
    return fn


def hsq(p0, t, k, z, y):
    """Forward squeeze (authoring): rip-uniform (z,y) -> squeezed model (z,y)."""
    zf = p0[0] + (p0[1] - y) * math.tan(math.radians(t))
    return (zf + (z - zf) * k if z > zf else z, y)


def tb_from(name, top_front, bottom_front, back_dist, x0, x1):
    """Tilted box from its front edge (two (z,y) points, top first) and its horizontal-at-top width toward +z."""
    (z0, y0), (z1, y1) = top_front, bottom_front
    L = math.hypot(z1 - z0, y1 - y0); t = math.degrees(math.atan2(z1 - z0, y0 - y1))
    return tilt_box(name, top_front, L, back_dist * math.cos(math.radians(t)), x0, x1, t)


# ================================================================== W325 detail pass helpers
S2 = math.sqrt(2.0)
ROOT = Path(__file__).resolve().parents[4]


def _rot(e):
    r = e.get('rotation')
    if not r: return None
    return (r['origin'], [(a, r.get(a, 0)) for a in ('x', 'y', 'z') if r.get(a, 0)])


def _rotate(p, rot):
    """kit.rotate (native 26.3 order Rx, Ry, Rz)."""
    if not rot: return p
    o, rs = rot; x, y, z = p[0] - o[0], p[1] - o[1], p[2] - o[2]
    for ax, ang in rs:
        a = math.radians(ang); c, s = math.cos(a), math.sin(a)
        if ax == 'x': y, z = y * c - z * s, y * s + z * c
        elif ax == 'y': x, z = x * c + z * s, -x * s + z * c
        else: x, y = x * c - y * s, x * s + y * c
    return (x + o[0], y + o[1], z + o[2])


def corners(e):
    f, t = e['from'], e['to']; r = _rot(e)
    return [_rotate((x, y, z), r) for x in (f[0], t[0]) for y in (f[1], t[1]) for z in (f[2], t[2])]


def bev_z(name, x0, x1, y0, y1, z0, z1, c, top=True, bottom=False, cb=None):
    """Long part along z with 45-degree chamfered long edges (top and/or bottom): core + caps + one rotated square
    prism per chamfered edge (its diagonal face is the chamfer)."""
    cb = c if cb is None else cb
    E = [box(f'{name}', [x0, y0 + (cb if bottom else 0), z0], [x1, y1 - (c if top else 0), z1])]
    for on, cc, yy, tag in ((top, c, y1, 'top'), (bottom, cb, y0, 'bot')):
        if not on: continue
        sg = -1 if tag == 'top' else 1
        E.append(box(f'{name}_{tag}cap', [x0 + cc, min(yy, yy + sg * cc), z0], [x1 - cc, max(yy, yy + sg * cc), z1]))
        h = cc / S2
        for side, xc in (('l', x0 + cc), ('r', x1 - cc)):
            yc = yy + sg * cc
            E.append({'name': f'{name}_{tag}bev_{side}', 'from': [xc - h, yc - h, z0], 'to': [xc + h, yc + h, z1],
                      'rotation': {'origin': [xc, yc, (z0 + z1) / 2], 'x': 0, 'y': 0, 'z': 45}})
    return E


def bev_x(name, x0, x1, y, z, c, z_dir):
    """Rotated square prism along x giving a 45-degree chamfer on the edge (y top, z end); z_dir +1 rear end, -1 front."""
    h = c / S2; zc = z - z_dir * c; yc = y - c
    return {'name': name, 'from': [x0, yc - h, zc - h], 'to': [x1, yc + h, zc + h],
            'rotation': {'origin': [(x0 + x1) / 2, yc, zc], 'x': 45, 'y': 0, 'z': 0}}


def drum(prefix, c, r, z0, z1, n=4, band=None):
    """Octagonal (n=4 -> 8 sides) prism along z: n flattened boxes rotated 180/n apart; optional end bands."""
    E = []; w = r * math.tan(math.pi / (2 * n)) * 1.02
    def ring(tag, rr, za, zb):
        ww = rr * math.tan(math.pi / (2 * n)) * 1.02
        for i in range(n):
            E.append({'name': f'{prefix}{tag}_{i}', 'from': [c[0] - rr, c[1] - ww, za], 'to': [c[0] + rr, c[1] + ww, zb],
                      'rotation': {'origin': [c[0], c[1], (za + zb) / 2], 'x': 0, 'y': 0, 'z': 180 / n * i}})
    if band:
        bw, br = band
        ring('', r, z0 + bw, z1 - bw)
        ring('_fband', r + br, z0, z0 + bw); ring('_rband', r + br, z1 - bw, z1)
    else:
        ring('', r, z0, z1)
    return E


def bolt(name, z, y, x_face, side, s=.22, proud=.05):
    """Small screw/pin head proud of a side face (side -1 = west/-x face at x_face, +1 = east)."""
    xa, xb = (x_face - proud, x_face + .01) if side < 0 else (x_face - .01, x_face + proud)
    return box(name, [xa, y - s / 2, z - s / 2], [xb, y + s / 2, z + s / 2])


def muzzle_ring(prefix, cx, cy, ro, ri, z0, z1, depth=.35):
    """Square muzzle crown with a real bore: four walls around the hole + dark plug recessed `depth`."""
    return [box(f'{prefix}_t', [cx - ro, cy + ri, z0], [cx + ro, cy + ro, z1]),
            box(f'{prefix}_b', [cx - ro, cy - ro, z0], [cx + ro, cy - ri, z1]),
            box(f'{prefix}_l', [cx - ro, cy - ri, z0], [cx - ri, cy + ri, z1]),
            box(f'{prefix}_r', [cx + ri, cy - ri, z0], [cx + ro, cy + ri, z1]),
            box(f'{prefix}_bore', [cx - ri, cy - ri, z0 + depth], [cx + ri, cy + ri, z0 + depth + .04])]


# ------------------------------------------------------------------ ADS profile clip (mirrors kit.py adscheck)
def base_profile(base):
    md = ROOT / 'src/main/resources/assets/destiny/models'
    els = json.loads((md / f'weapon_sight_w151/{base}_body.json').read_text())['elements']
    cs = [corners(e) for e in els]
    zs = [p[2] for c in cs for p in c]; zmin, zmax = min(zs), max(zs); start = zmin + (zmax - zmin) / 3
    sl = []; z = start
    while z < zmax:
        best = None
        for c in cs:
            if max(p[2] for p in c) < z or min(p[2] for p in c) > z + .25: continue
            if max(p[0] for p in c) < 6.6 or min(p[0] for p in c) > 9.4: continue
            y = max(p[1] for p in c); best = y if best is None or y > best else best
        sl.append((z, best)); z += .25
    return sl


def _limit(sl, c, margin):
    za, zb = min(p[2] for p in c), max(p[2] for p in c)
    if max(p[0] for p in c) < 6.6 or min(p[0] for p in c) > 9.4: return None
    lim = None
    for z, b in sl:
        if zb < z or za > z + .25: continue
        v = -99 if b is None else b + margin
        lim = v if lim is None else min(lim, v)
    return lim


def ads_clip(E, base, skip=lambda n: n.startswith('mag_') or 'sight_ring' in n, margin=.1, log=None):
    """Make every body element satisfy kit adscheck: element max-y <= base top (+margin) over every 0.25 slice it touches.
    Axis-aligned parts are split at slice boundaries and their tops clipped; rotated parts are split adaptively along
    their local y/z and the offending cells' local tops lowered (cells that vanish are dropped)."""
    sl = base_profile(base); out = []; changed = []
    def ok(e):
        lim = _limit(sl, corners(e), margin)
        return lim is None or max(p[1] for p in corners(e)) <= lim + 1e-6
    def fit_rot(e, depth=0):
        """Rotated part: narrow it from its local +z (back) side first (grips rake back, the back edge is what rises
        over the base backstrap), then shorten it from its local top; never fragment it."""
        g = dict(e, **{'from': list(e['from']), 'to': list(e['to'])}); w0 = g['to'][2] - g['from'][2]
        while not ok(g) and g['to'][2] - g['from'][2] > .45 * w0: g['to'][2] -= .02
        while not ok(g) and g['to'][1] - g['from'][1] > .1: g['to'][1] -= .02
        return [g] if ok(g) else []
    for e in E:
        if skip(e['name']) or ok(e): out.append(e); continue
        changed.append(e['name'])
        if e.get('rotation') and any(e['rotation'].get(a, 0) for a in 'xyz'):
            out += fit_rot(e); continue
        f, t = e['from'], e['to']; za, zb = f[2], t[2]
        cuts = [za] + [z for z, _ in sl if za < z < zb] + [zb]
        segs = []
        for i in range(len(cuts) - 1):
            a, b = cuts[i] + (.001 if i else 0), cuts[i + 1] - (.001 if i < len(cuts) - 2 else 0)
            lim = _limit(sl, [(f[0], 0, a), (t[0], 0, b)], margin)
            top = t[1] if lim is None else min(t[1], lim)
            if segs and abs(segs[-1][3] - top) < 1e-6: segs[-1][2] = b
            else: segs.append([i, a, b, top])
        for k, (i, a, b, top) in enumerate(segs):
            if top - f[1] < .04: continue
            out.append(dict(e, **{'name': e['name'] + (f'~{k}' if len(segs) > 1 else ''),
                                  'from': [f[0], f[1], a], 'to': [t[0], top, b]}))
    if log is not None: log.extend(changed)
    return out


# ------------------------------------------------------------------ flat paint (clean faces instead of smeared bake)
_IMG = {}


def grade(rgb):
    r, g, b = rgb; yv = 0.299 * r + 0.587 * g + 0.114 * b; y2 = 80 + (yv - 70) * 1.15
    return tuple(max(0, min(255, int(round(y2 + (c - yv) * 0.95)))) for c in (r, g, b))


def rip_colour(cache, xi, yi, rad=2, view='nx'):
    """Median colour of the rip side view around image px (xi, yi), graded like the kit bake."""
    from PIL import Image
    key = (str(cache), view)
    if key not in _IMG: _IMG[key] = Image.open(Path(cache) / f'{view}_albedo.png').convert('RGBA').load()
    px = _IMG[key]; vals = []
    for dx in range(-rad, rad + 1):
        for dy in range(-rad, rad + 1):
            c = px[int(xi) + dx, int(yi) + dy]
            if c[3] > 200: vals.append(c[:3])
    if not vals: return (80, 80, 82, 255)
    med = tuple(sorted(v[i] for v in vals)[len(vals) // 2] for i in range(3))
    return grade(med) + (255,)


def stack(name, top_front, bottom_front, back_top, back_bottom, x0, x1, n):
    """Grip as n tilted segments stacked along its front edge (top first).  Segment widths interpolate back_top ->
    back_bottom (measured horizontally from the front edge); short segments let ads_clip narrow only the upper back."""
    (za, ya), (zb, yb) = top_front, bottom_front; out = []
    for i in range(n):
        f0, f1 = i / n, (i + 1) / n
        p0 = (za + (zb - za) * f0, ya + (yb - ya) * f0); p1 = (za + (zb - za) * f1, ya + (yb - ya) * f1)
        w = back_top + (back_bottom - back_top) * (f0 + f1) / 2
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        t = math.degrees(math.atan2(p1[0] - p0[0], p0[1] - p1[1]))
        out.append(tilt_box(f'{name}_{i}', p0, L, w * math.cos(math.radians(t)), x0, x1, t))
    return out


# ------------------------------------------------------------------ W30-style flat paint (Minecraft look)
_FA = {'north': (2, 0, 0, False, 1, False), 'south': (2, 1, 0, True, 1, False),
       'east': (0, 1, 2, False, 1, False), 'west': (0, 0, 2, True, 1, False),
       'up': (1, 1, 0, True, 2, True), 'down': (1, 0, 0, True, 2, False)}


def fpoint(e, fn, s, t):
    """Model point of face fn at (s, t) (same convention as kit.face_point)."""
    f, to = e['from'], e['to']; pa, side, ua, ufwd, va, vfwd = _FA[fn]
    o = [0.0] * 3; o[pa] = to[pa] if side else f[pa]; o[ua] = f[ua] if ufwd else to[ua]; o[va] = f[va] if vfwd else to[va]
    p = list(o); p[ua] += (to[ua] - f[ua]) * (1 if ufwd else -1) * s; p[va] += (to[va] - f[va]) * (1 if vfwd else -1) * t
    return _rotate(tuple(p), _rot(e))


class Painter:
    """Flat colour blocks.  parts: [(name prefix, rgba)] first match wins (None = leave to the projection bake);
    side: [(prefixes, z0, z1, y0, y1, rgba)] decals on west/east faces in model (z, y);
    top: [(prefixes, z0, z1, x0, x1, rgba)] decals on up faces in model (z, x); end: rgba for north/south faces
    of matching prefixes [(prefixes, rgba)].  A prefixes tuple of () matches every part."""
    def __init__(self, parts, side=(), top=(), end=(), poly=(), cal=None):
        """poly: [(prefixes, [(z, y), ...], rgba)] model-space side polygons (checked before side boxes)."""
        self.parts, self.side, self.top, self.end, self.poly = parts, side, top, end, poly
        self.cal = cal       # if given: side/poly decals are in rip nx image px (xi, yi) instead of model (z, y)

    @staticmethod
    def _m(n, pre): return not pre or any(n.startswith(p) for p in pre)

    def __call__(self, e, fn, s, t):
        n = e['name']; base = None
        hit = False
        for pre, c in self.parts:
            if n.startswith(pre): base = c; hit = True; break
        if base is None: return None
        p = fpoint(e, fn, s, t)
        if fn in ('west', 'east'):
            a, b = self.cal.img(n, p) if self.cal else (p[2], p[1])
            for pre, pg, c in self.poly:
                if self._m(n, pre) and inpoly(a, b, pg): return c
            for pre, z0, z1, y0, y1, c in self.side:
                if self._m(n, pre) and min(z0, z1) <= a <= max(z0, z1) and min(y0, y1) <= b <= max(y0, y1): return c
        elif fn == 'up':
            for pre, z0, z1, x0, x1, c in self.top:
                if self._m(n, pre) and z0 <= p[2] <= z1 and x0 <= p[0] <= x1: return c
        else:
            for pre, c in self.end:
                if self._m(n, pre): return c
        return base


def inpoly(x, y, pg):
    k = False; j = len(pg) - 1
    for i in range(len(pg)):
        (xi, yi), (xj, yj) = pg[i], pg[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: k = not k
        j = i
    return k


def slab(name, x0, x1, y0, y1, z0, z1, c=.14, cuts=(), gap=.06, top=True, bottom=True, inset=.05):
    """DMW-style machined slab from unrotated cubes: split along z at `cuts` into segments separated by a recessed
    groove; each segment = core (full height, inset c in x) + two side plates (full width x, height reduced by c at the
    chamfered top/bottom), giving a 1-step chamfer on the long edges."""
    zs = [z0] + sorted(c_ for c_ in cuts if z0 < c_ < z1) + [z1]; E = []
    ya = y0 + (c if bottom else 0); yb = y1 - (c if top else 0)
    for i in range(len(zs) - 1):
        a = zs[i] + (gap / 2 if i else 0); b = zs[i + 1] - (gap / 2 if i < len(zs) - 2 else 0)
        E.append(box(f'{name}_s{i}', [x0 + c, y0, a], [x1 - c, y1, b]))
        E.append(box(f'{name}_s{i}l', [x0, ya, a], [x0 + c, yb, b]))
        E.append(box(f'{name}_s{i}r', [x1 - c, ya, a], [x1, yb, b]))
        if i:
            E.append(box(f'{name}_g{i}', [x0 + inset, y0 + inset, zs[i] - gap / 2], [x1 - inset, y1 - inset, zs[i] + gap / 2]))
    return E


def along(tf, bf, f0, f1, shift=0.0):
    """Sub-segment f0..f1 of the front line tf->bf, shifted horizontally (+z) by `shift`: same rake as the line."""
    p = lambda f: (tf[0] + (bf[0] - tf[0]) * f + shift, tf[1] + (bf[1] - tf[1]) * f)
    return p(f0), p(f1)


def grip_stack(name, tf, bf, wt, wb, x0, x1, n, heel=None, panels=None):
    """Whole grip on ONE rake line (no near-parallel slabs): core stack of n segments sharing exact planes; optional
    heel = (name, depth, width, x0, x1) continuing the same line below the core; optional panels =
    (name_w, name_e, f0, f1, inset, back_top, back_bot, thick) side plates flush on the core sides, same rake."""
    E = stack(name, tf, bf, wt, wb, x0, x1, n)
    if heel:
        hn, d, wh, hx0, hx1 = heel
        L = math.hypot(bf[0] - tf[0], bf[1] - tf[1]); f = 1 + d / L
        a, b = along(tf, bf, 1.0, f)
        E += stack(hn, a, b, wh, wh, hx0, hx1, 1)
    if panels:
        nw, ne, f0, f1, inset, pt, pb, th = panels
        a, b = along(tf, bf, f0, f1, inset)
        n2 = max(1, n - 1)
        E += stack(nw, a, b, pt, pb, x0 - th, x0, n2)
        E += stack(ne, a, b, pt, pb, x1, x1 + th, n2)
    return E


def deconflict(E, eps=.016):
    """Remove coplanar overlapping faces (z-fighting / flicker): for every pair of unrotated elements whose same-facing
    faces lie on one plane and overlap in area, pull the smaller element's face inward by eps."""
    def rotd(e): r = e.get('rotation'); return r and any(abs(r.get(a, 0)) > 1e-6 for a in 'xyz')
    un = [e for e in E if not rotd(e)]
    vol = lambda e: (e['to'][0] - e['from'][0]) * (e['to'][1] - e['from'][1]) * (e['to'][2] - e['from'][2])
    changed = True; guard = 0
    while changed and guard < 6:
        changed = False; guard += 1
        for i, a in enumerate(un):
            for b in un[i + 1:]:
                for ax in range(3):
                    o = [k for k in range(3) if k != ax]
                    if not all(min(a['to'][k], b['to'][k]) - max(a['from'][k], b['from'][k]) > 1e-3 for k in o): continue
                    for side, sg in (('from', 1), ('to', -1)):
                        if abs(a[side][ax] - b[side][ax]) > 1e-3: continue
                        for sm in sorted((a, b), key=vol):
                            if sm['to'][ax] - sm['from'][ax] > 3 * eps:
                                sm[side] = list(sm[side]); sm[side][ax] += sg * eps; changed = True; break
    return E


def carve_bores(E):
    """Subtract muzzle cavity boxes from intersecting static housings, retaining recessed black plugs."""
    plugs=[e for e in E if e['name'].endswith('_bore')]
    if any(e['name']=='muzzle_tube_core' for e in E):
        e=next(e for e in E if e['name']=='muzzle_tube_core')
        cy=(e['from'][1]+e['to'][1])/2;zf=e['from'][2]
        E.remove(e)
        e=box('muzzle_tube_inner_bore',[7.78,cy-.22,zf+.3],[8.22,cy+.22,zf+.34])
        E.append(e);plugs.append(e)
    for plug in plugs:
        prefix=plug['name'][:-5]
        if prefix=='muzzle_tube_inner': prefix='muzzle_tube'
        front=min(e['from'][2] for e in E if e['name'].startswith(prefix))
        if prefix=='muzzle_tube':front-=.3
        lo=[plug['from'][0],plug['from'][1],front-.001];hi=[plug['to'][0],plug['to'][1],plug['from'][2]]
        out=[]
        for e in E:
            if e is plug or e['name'].startswith('mag_') or any(abs(e.get('rotation',{}).get(a,0))>1e-6 for a in 'xyz'):
                out.append(e);continue
            a=list(e['from']);b=list(e['to']);il=[max(a[k],lo[k]) for k in range(3)];ih=[min(b[k],hi[k]) for k in range(3)]
            if any(ih[k]-il[k]<1e-5 for k in range(3)):
                out.append(e);continue
            for k in range(3):
                if il[k]-a[k]>1e-5:
                    q=b.copy();q[k]=il[k];out.append(dict(e,name=e['name']+f'_c{k}a',**{'from':a.copy(),'to':q}));a[k]=il[k]
                if b[k]-ih[k]>1e-5:
                    q=a.copy();q[k]=ih[k];out.append(dict(e,name=e['name']+f'_c{k}b',**{'from':q,'to':b.copy()}));b[k]=ih[k]
        E=out
    return deconflict(E)
