"""W325 worker-5 authoring helpers (copied verbatim into each weapon folder so every design.py is self-contained).

Model space: vanilla item px, muzzle -z, up +y, gun right +x, centred x=8.  Rotations are native 26.3 element
rotations (single axis here, any angle)."""
import math


def box(name, lo, hi, rx=None, origin=None, ry=None, rz=None, **extra):
    """Axis box; optional rotation about x (pitch, + tilts the top toward +z) / y / z around origin (default centre)."""
    lo = [float(v) for v in lo]; hi = [float(v) for v in hi]
    e = {'name': name, 'from': [min(lo[i], hi[i]) for i in range(3)], 'to': [max(lo[i], hi[i]) for i in range(3)]}
    if rx or ry or rz:
        o = origin or [(lo[i] + hi[i]) / 2 for i in range(3)]
        e['rotation'] = {'origin': [float(v) for v in o], 'x': float(rx or 0), 'y': float(ry or 0), 'z': float(rz or 0)}
    e.update(extra)
    return e


def xs(half, cx=8.0):
    return (cx - half, cx + half)


def bx(name, half, y0, y1, z0, z1, **kw):
    """Box symmetric about x=8 with half width `half`."""
    a, b = xs(half)
    return box(name, (a, y0, z0), (b, y1, z1), **kw)


def bar(name, half, p0, p1, thick, side='centre'):
    """Bar in the (z,y) plane from p0=(z,y) to p1 (length axis), `thick` across.  side: 'centre' (line is the
    centreline), 'below' (line is the top face), 'above' (line is the bottom face).  Rotation about x."""
    (z0, y0), (z1, y1) = p0, p1
    L = math.hypot(z1 - z0, y1 - y0); uz, uy = (z1 - z0) / L, (y1 - y0) / L
    nz, ny = -uy, uz                                   # left normal of the direction in (z,y)
    if ny < 0: nz, ny = -nz, -ny                       # normal pointing up
    off = {'centre': 0.0, 'below': -thick / 2, 'above': thick / 2}[side]
    cz, cy = (z0 + z1) / 2 + nz * off, (y0 + y1) / 2 + ny * off
    # unrotated box is a z-aligned bar; rotation about x by angle a maps +z axis to (z=cos a, y=sin a)
    ang = -math.degrees(math.atan2(uy, uz))       # Rx(a) maps +z to (cos a, -sin a)
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    a, b = xs(half)
    return box(name, (a, cy - thick / 2, cz - L / 2), (b, cy + thick / 2, cz + L / 2), rx=ang, origin=[8.0, cy, cz])


def vbar(name, half, top, bottom, thick):
    """Upright bar (grip / magazine style) whose centreline runs from top=(z,y) to bottom=(z,y)."""
    (zt, yt), (zb, yb) = top, bottom
    L = math.hypot(zt - zb, yt - yb); cz, cy = (zt + zb) / 2, (yt + yb) / 2
    ang = math.degrees(math.atan2(zt - zb, yt - yb))  # lean of the top toward +z
    a, b = xs(half)
    return box(name, (a, cy - L / 2, cz - thick / 2), (b, cy + L / 2, cz + thick / 2), rx=ang, origin=[8.0, cy, cz])


def bar3(name, p0, p1, thick, thick_x=None):
    """Bar between two 3D model points (x,y,z) with a square-ish section; native Rx then Ry rotation.
    Rx(a)Ry(b) maps +z to (cos a sin b, -sin a, cos a cos b)."""
    d = [p1[i] - p0[i] for i in range(3)]; L = math.sqrt(sum(v * v for v in d)); d = [v / L for v in d]
    a = math.degrees(math.asin(-d[1])); b = math.degrees(math.atan2(d[0], d[2]))
    c = [(p0[i] + p1[i]) / 2 for i in range(3)]; tx = (thick_x or thick) / 2; ty = thick / 2
    return box(name, (c[0] - tx, c[1] - ty, c[2] - L / 2), (c[0] + tx, c[1] + ty, c[2] + L / 2), rx=a, ry=b, origin=c)


def ring(prefix, cy, z0, z1, outer, wall, cx=8.0, corners=True):
    """Hollow square tube (+45 deg corner fills) along z; aperture centred on (cx, cy)."""
    o, i = outer, outer - wall
    S = [box(prefix + 'top', (cx - o, cy + i, z0), (cx + o, cy + o, z1)),
         box(prefix + 'bottom', (cx - o, cy - o, z0), (cx + o, cy - i, z1)),
         box(prefix + 'left', (cx - o, cy - i, z0), (cx - i, cy + i, z1)),
         box(prefix + 'right', (cx + i, cy - i, z0), (cx + o, cy + i, z1))]
    if corners:
        r = (o + i) / 2 * 0.86; w = wall * 0.75; L = (o - i) * 1.6
        for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
            ccx, ccy = cx + sx * r * 0.7071, cy + sy * r * 0.7071
            S.append(box(f'{prefix}c{k}', (ccx - L / 2, ccy - w / 2, z0), (ccx + L / 2, ccy + w / 2, z1),
                         rz=(-45 if sx * sy > 0 else 45), origin=[ccx, ccy, (z0 + z1) / 2]))
    return S


class Uniform:
    """Uniform rip map: rip world Y (gun length, muzzle -Y) / Z (up) / X (left) <- model z / y / x.
    zb,yb: model point that maps to rip (Yw0, Zw0); s: px per metre along the length; sy: px per metre across
    (height/width, default s); kx: extra lateral widening of the model."""
    def __init__(self, s, zb, Yw0, yb, Zw0, Xc, kx=1.0, sy=None):
        self.s, self.zb, self.Y0, self.yb, self.Z0, self.Xc, self.kx = s, zb, Yw0, yb, Zw0, Xc, kx
        self.sy = sy or s

    def __call__(self, p):
        x, y, z = p
        return (self.Xc - (x - 8.0) / (self.sy * self.kx), self.Y0 + (z - self.zb) / self.s, self.Z0 + (y - self.yb) / self.sy)


def chbox(name, half, y0, y1, z0, z1, c=0.18, top=True, bottom=False, cx=8.0):
    """Box along z with 45 deg chamfered long edges (top and/or bottom): core + narrower cap + two rotated fill slabs
    whose outer faces lie on the chamfer planes (W325 detail pass: clean bevels instead of stair steps)."""
    a, b = cx - half, cx + half
    yc0 = y0 + (c if bottom else 0); yc1 = y1 - (c if top else 0)
    S = [box(name, (a, yc0, z0), (b, yc1, z1))]
    L = c * math.sqrt(2); t = c / math.sqrt(2)
    for tag, on, ys, sgn in (('top', top, y1, 1), ('bot', bottom, y0, -1)):
        if not on: continue
        S.append(box(f'{name}_{tag}cap', (a + c, ys - sgn * c if sgn > 0 else ys, z0), (b - c, ys if sgn > 0 else ys + c, z1)))
        for side, ex in (('l', a), ('r', b)):
            sx = 1 if side == 'l' else -1
            # chamfer hypotenuse midpoint, inward normal points to (+sx, -sgn) / sqrt2
            mx, my = ex + sx * c / 2, ys - sgn * c / 2
            cxm, cym = mx + sx * t / 2 * 0.7071, my - sgn * t / 2 * 0.7071
            ang = 45 if sx * sgn > 0 else -45
            S.append(box(f'{name}_{tag}ch_{side}', (cxm - L / 2, cym - t / 2, z0), (cxm + L / 2, cym + t / 2, z1),
                         rz=ang, origin=[cxm, cym, (z0 + z1) / 2]))
    return S


class Painter:
    """design.py special() helper: faces whose projection is poor (few rip texels land on them -> smeared inpaint) or
    that are listed in `flat` are painted one clean colour (dominant graded rip colour of the face, or the given rgb);
    kit.edges() then adds the 1 px edge highlight/shadow.  Good faces keep the projection (decals, panel lines)."""
    def __init__(self, design_file, model2world, flat=None, thresh=0.55, grade=None, extra=None):
        import json, sys
        from pathlib import Path
        root = Path(design_file).resolve().parents[4]
        sys.path.insert(0, str(root / 'scripts/art/w325'))
        import kit
        self.kit = kit; self.m2w = model2world; self.flat = flat or {}; self.thresh = thresh
        self.grade = grade or kit.default_grade; self.extra = extra
        cache = Path(design_file).resolve().parent / 'proj_cache'
        man = json.loads((cache / 'manifest.json').read_text())
        self.views = {k: kit.View(cache, k, man) for k in man['views']}
        ext = max(man['hi'][i] - man['lo'][i] for i in range(3)); self.occ = ext * 0.012
        self.memo = {}

    def _view(self, e, fn):
        k = self.kit; p = k.face_point(e, fn, .5, .5); nm = k.rotate_vec(k.NORMALS[fn], k.rot_of(e))
        a = self.m2w(e['name'], p); b = self.m2w(e['name'], tuple(p[i] + nm[i] * .25 for i in range(3)))
        wn = [b[i] - a[i] for i in range(3)]; i = max(range(3), key=lambda q: abs(wn[q]))
        return self.views[('p' if wn[i] > 0 else 'n') + 'xyz'[i]]

    def analyse(self, e, fn):
        n = e['name']
        for pre, col in self.flat.items():
            if n.startswith(pre) and (not isinstance(col, dict) or fn in col):
                c = col[fn] if isinstance(col, dict) else col
                if c is not None: return tuple(c)
        k = self.kit; v = self._view(e, fn); cols = []; tot = 0
        for i in range(8):
            for j in range(8):
                tot += 1; wp = self.m2w(n, k.face_point(e, fn, (i + .5) / 8, (j + .5) / 8))
                x, y = v.project(wp); ds = v.depth_at(x, y)
                if ds is None or ds > sum(wp[q] * v.d[q] for q in range(3)) + self.occ: continue
                c = v.sample(x, y)
                if c is not None: cols.append(self.grade(c))
        if len(cols) >= tot * self.thresh: return None
        if not cols: return tuple(self.flat.get('_fallback', (70, 72, 74)))
        buckets = {}
        for c in cols: buckets.setdefault(tuple(int(ch) // 24 for ch in c), []).append(c)
        best = max(buckets.values(), key=len)
        return tuple(int(sum(c[q] for c in best) / len(best)) for q in range(3))

    def __call__(self, e, fn, s, t):
        if self.extra:
            r = self.extra(e, fn, s, t)
            if r is not None: return r
        key = (e['name'], fn)
        if key not in self.memo: self.memo[key] = self.analyse(e, fn)
        c = self.memo[key]
        if c is None: return None
        g = 1.0 + (0.035 if fn in ('north', 'south', 'east', 'west') and t < .5 else 0)   # faint top-lit gradient
        return tuple(max(0, min(255, int(ch * g))) for ch in c[:3]) + (255,)


_PARTSUF = ('_topcap', '_botcap', '_topch_l', '_topch_r', '_botch_l', '_botch_r')


def machined(els, seg=3.6, min_len=4.6, min_sec=0.55, skip=('mag_', 'sight_', 'grip_', 'trigger', 'loop', 'guard')):
    """Dead Man Walking style break-up (W325 detail pass): long slabs (z length > min_len, cross-section >= min_sec in
    x and y) become several machined segments with a recessed joint groove between them instead of one 8-px plank.
    Only unrotated or z-rotated elements are split (z extents are exact).  The core of each chbox family gets an inset
    filler in each groove (0.1 px long, inset 0.07 on the sides / top / bottom) so the groove reads as an engraved seam
    without opening a see-through slit; cap/chamfer strips simply stop at the groove (notched bevel ring).
    Insets only lower the top, so the ADS profile never rises."""
    out = []
    for e in els:
        n = e['name']; f, t = e['from'], e['to']; r = e.get('rotation')
        L = t[2] - f[2]
        rotok = not r or (abs(r.get('x', 0)) < 1e-9 and abs(r.get('y', 0)) < 1e-9)
        core = n
        for sfx in _PARTSUF:
            if n.endswith(sfx): core = n[:-len(sfx)]
        fam_big = L > min_len
        if not rotok or not fam_big or n.startswith(skip) or (core == n and (t[0] - f[0] < min_sec or t[1] - f[1] < min_sec)):
            out.append(e); continue
        k = max(2, int(round(L / seg)))
        joints = [f[2] + L * i / k for i in range(1, k)]
        cuts = [f[2]] + joints + [t[2]]
        for i in range(k):
            a = cuts[i] + (0.05 if i > 0 else 0); b = cuts[i + 1] - (0.05 if i < k - 1 else 0)
            s = {**e, 'name': f'{n}_s{i}', 'from': [f[0], f[1], a], 'to': [t[0], t[1], b]}
            if r: s['rotation'] = {**r, 'origin': [r['origin'][0], r['origin'][1], (a + b) / 2]}
            out.append(s)
        if core == n:
            for i, z in enumerate(joints):
                dx = min(.07, (t[0] - f[0]) / 4); dy = min(.07, (t[1] - f[1]) / 4)
                g = {**e, 'name': f'{n}_g{i}', 'from': [f[0] + dx, f[1] + dy, z - .05], 'to': [t[0] - dx, t[1] - dy, z + .05]}
                if r: g['rotation'] = {**r, 'origin': [r['origin'][0], r['origin'][1], z]}
                out.append(g)
    return out


def along(name, half, top, bottom, thick, a=0.0, b=1.0, off=0.0, cx=8.0):
    """Clean-joint helper (W325 cleanup pass): a slab on EXACTLY the same axis/rotation as the vbar(top, bottom)
    it belongs to (grip panel, backstrap, foot, magazine band...), covering the axial fraction a..b and shifted `off`
    px along the slab's own thickness direction (+ = toward +z of the unrotated slab).  Same angle -> no crossing
    seams or 1-3 deg mismatched panels."""
    (zt, yt), (zb, yb) = top, bottom
    L = math.hypot(zt - zb, yt - yb); ang = math.degrees(math.atan2(zt - zb, yt - yb))
    cz, cy = (zt + zb) / 2, (yt + yb) / 2                       # rotation origin = parent centre
    y0 = cy - L / 2 + L * (1 - b); y1 = cy - L / 2 + L * (1 - a)  # a=0 is the top end
    lo, hi = xs(half, cx)
    return box(name, (lo, y0, cz + off - thick / 2), (hi, y1, cz + off + thick / 2), rx=ang, origin=[cx, cy, cz])


def bar_on(name, half, p0, p1, thick, a=0.0, b=1.0, off=0.0, cx=8.0):
    """Same as along() for a bar(p0, p1) (side='centre'): exact parent axis, fraction a..b, normal offset `off`
    (+ = the bar's up side)."""
    (z0, y0), (z1, y1) = p0, p1
    L = math.hypot(z1 - z0, y1 - y0)
    ang = -math.degrees(math.atan2(y1 - y0, z1 - z0))
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    cz, cy = (z0 + z1) / 2, (y0 + y1) / 2
    lo, hi = xs(half, cx)
    zs, ze = cz - L / 2 + L * a, cz - L / 2 + L * b
    return box(name, (lo, cy + off - thick / 2, zs), (hi, cy + off + thick / 2, ze), rx=ang, origin=[cx, cy, cz])


def steps(prefix, half, z0, z1, ytop, ybot0, ybot1, n, cx=8.0):
    """Axis-aligned step sequence for a sloped underside (Dead Man Walking style): n blocks sharing exact edges,
    each from its stepped bottom up to ytop; bottoms interpolate ybot0 -> ybot1 along z."""
    S = []
    for i in range(n):
        za = z0 + (z1 - z0) * i / n; zb = z0 + (z1 - z0) * (i + 1) / n
        yb = ybot0 + (ybot1 - ybot0) * (i + .5) / n
        S.append(bx(f'{prefix}{i}', half, yb, ytop, za, zb, cx=cx) if False else box(f'{prefix}{i}', (cx - half, yb, za), (cx + half, ytop, zb)))
    return S


def dezfight(els, eps=0.012):
    """Remove coplanar overlapping faces (z-fighting slivers): for two elements with the same rotation (or none) whose
    same-facing faces lie on one plane and overlap, the smaller face is pulled `eps` inward so the bigger part's face
    wins cleanly.  Only shrinks elements (never raises the ADS profile).  Applied separately to body and magazine."""
    def key(e):
        r = e.get('rotation')
        if not r: return None
        return (round(r.get('x', 0), 4), round(r.get('y', 0), 4), round(r.get('z', 0), 4), tuple(round(v, 4) for v in r['origin']))
    for i, a in enumerate(els):
        for b in els[i + 1:]:
            if key(a) != key(b) or a['name'].startswith('mag_') != b['name'].startswith('mag_'): continue
            for ax in range(3):
                o = [k for k in range(3) if k != ax]
                if not all(min(a['to'][k], b['to'][k]) - max(a['from'][k], b['from'][k]) > .02 for k in o): continue
                for side in ('from', 'to'):
                    if abs(a[side][ax] - b[side][ax]) > .004: continue
                    area = lambda e: (e['to'][o[0]] - e['from'][o[0]]) * (e['to'][o[1]] - e['from'][o[1]])
                    s = a if area(a) <= area(b) else b
                    if s['to'][ax] - s['from'][ax] <= 3 * eps: continue
                    s[side] = list(s[side]); s[side][ax] += eps if side == 'from' else -eps
    return els
