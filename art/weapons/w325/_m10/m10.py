"""Shared helpers for the w325_m10 designs (rocket / grenade launchers, swords).

RipMap: uniform scale; rip point (x, a, h) with a = rip axis along the gun (muzzle at -a or +a), h = rip up.
model X = 8 + sx*(x - x0)*s, model Z = Z0 + sz*(a - a0)*s, model Y = Y0 + (h - h0)*s.
"""
import math


class RipMap:
    def __init__(self, s, rip_anchor, model_anchor, along='y', up='z', muzzle='-', x0=0.0, proper=True):
        self.s = s; self.a0, self.h0 = rip_anchor; self.Z0, self.Y0 = model_anchor
        self.ai = 'xyz'.index(along); self.hi = 'xyz'.index(up)
        self.xi = ({0, 1, 2} - {self.ai, self.hi}).pop()
        self.sz = 1 if muzzle == '-' else -1   # muzzle at -a -> model -Z
        # proper=True: a rotation (no mirror; decals read correctly, W302 Khvostov convention).  For a rip with
        # along=y, up=z this gives model X = -x when the muzzle is at -y.  proper=False keeps X = +x (W123 [X,Z,Y]).
        self.sx = -self.sz if proper else 1
        self.x0 = x0

    def m(self, x, a, h):
        return (8 + self.sx * (x - self.x0) * self.s, self.Y0 + (h - self.h0) * self.s, self.Z0 + self.sz * (a - self.a0) * self.s)

    def w(self, p):
        X, Y, Z = p
        out = [0.0, 0.0, 0.0]
        out[self.xi] = self.x0 + self.sx * (X - 8) / self.s
        out[self.ai] = self.a0 + self.sz * (Z - self.Z0) / self.s
        out[self.hi] = self.h0 + (Y - self.Y0) / self.s
        return tuple(out)

    def rb(self, name, xr, ar, hr, **kw):
        """box from rip ranges (metres); xr may be a half width (float) -> symmetric about x0."""
        if not isinstance(xr, (tuple, list)): xr = (self.x0 - xr, self.x0 + xr)
        p = self.m(xr[0], ar[0], hr[0]); q = self.m(xr[1], ar[1], hr[1])
        return box(name, p, q, **kw)


def box(name, a, b, rot=None, **kw):
    lo = [min(a[i], b[i]) for i in range(3)]; hi = [max(a[i], b[i]) for i in range(3)]
    e = {'name': name, 'from': [round(v, 4) for v in lo], 'to': [round(v, 4) for v in hi]}
    if rot: e['rotation'] = rot
    e.update(kw)
    return e


def bar(name, x0, x1, p0, p1, thick, side='below', ext=(0.0, 0.0)):
    """Box whose top (side='below') or bottom (side='above') face lies on the (z,y) line p0->p1."""
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dz, dy); ux, uy = dz / L, dy / L
    theta = math.degrees(math.atan2(-uy, ux))
    ny, nz = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    mz, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    sh = (ext[1] - ext[0]) / 2; mz, my = mz + ux * sh, my + uy * sh
    sg = -1 if side == 'below' else 1
    cy, cz = my + sg * ny * thick / 2, mz + sg * nz * thick / 2
    half = (L + ext[0] + ext[1]) / 2
    return box(name, (x0, cy - thick / 2, cz - half), (x1, cy + thick / 2, cz + half),
               rot={'origin': [round((x0 + x1) / 2, 4), round(cy, 4), round(cz, 4)], 'x': round(theta, 4)})


def post(name, x0, x1, p0, p1, thick, ext=(0.0, 0.0)):
    """Box centred on the (z,y) segment p0->p1 with square-ish section thick (y/z) and x0..x1."""
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dz, dy); ux, uy = dz / L, dy / L
    theta = math.degrees(math.atan2(-uy, ux))
    mz, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    sh = (ext[1] - ext[0]) / 2; mz, my = mz + ux * sh, my + uy * sh
    half = (L + ext[0] + ext[1]) / 2
    return box(name, (x0, my - thick / 2, mz - half), (x1, my + thick / 2, mz + half),
               rot={'origin': [round((x0 + x1) / 2, 4), round(my, 4), round(mz, 4)], 'x': round(theta, 4)})


def rot_zy(p, pivot, deg):
    """rotate model point p about an x-parallel axis through pivot (y,z) by deg (same sense as element x rotation)."""
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    y, z = p[1] - pivot[0], p[2] - pivot[1]
    return (p[0], pivot[0] + y * c - z * s, pivot[1] + y * s + z * c)


def disc(s, t, cx, cy, w, h, r):
    """True if face coords (s,t in 0..1, face size w x h px) are within r px of (cx,cy) given in px."""
    return (s * w - cx) ** 2 + (t * h - cy) ** 2 < r * r


def side_part(M, sight_x, rip_x):
    """Return f(p)->rip world for a part authored around model x sight_x that should sample the rip feature at rip x
    rip_x lying on the opposite model side (mirror across the part centre)."""
    xr = 8 + M.sx * (rip_x - M.x0) * M.s
    def f(p, dy=0.0, dz=0.0):
        return M.w((xr - (p[0] - sight_x), p[1] - dy, p[2] - dz))
    return f


def slant_tip(M, name, hw, A, B, base, t_px=0.6, steps=3):
    """Sword tip in rip (y, z): spine corner A, point B (B.y > A.y, B.z > A.z), filled down to rip z `base` between
    A.y and B.y.  A strip whose top face is the A->B slant (shortened at B so it never pokes past the edge) plus
    stepped boxes under it."""
    out = []
    ya, za = A; yb, zb = B
    L = math.hypot(yb - ya, zb - za); uy, uz = (yb - ya) / L, (zb - za) / L
    t = t_px / M.s
    e = t * uy / uz            # shorten at B so the strip's lower-B corner stays at y <= yb
    p0 = M.m(0, ya, za); p1 = M.m(0, yb, zb)
    out.append(bar(name + '_slant', 8 - hw * M.s, 8 + hw * M.s, (p1[2], p1[1]), (p0[2], p0[1]), t_px,
                   ext=(-e * M.s, 0.03)))
    for i in range(steps):
        y0 = ya + (yb - ya) * i / steps; y1 = ya + (yb - ya) * (i + 1) / steps
        ztop = za + (zb - za) * (i / steps)          # flush with the slant at the step's spine end
        out.append(M.rb(f'{name}_step{i}', hw, (y0, y1), (base, ztop)))
    return out


def cbox(name, lo, hi, c, top=True, bottom=False, axis='z'):
    """Box running along `axis` (z or y) with its long edges chamfered by c px on the top (+y / +z for axis y) and/or
    bottom side.  Built as a core box, a narrower cap box per chamfered side and two 45 deg diamond strips whose outer
    face is the bevel.  Element names: name, name_cap_t/b, name_ch_tl/tr/bl/br."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    out = []
    s = c * math.sqrt(2)
    if axis == 'z':
        ya = y0 + (c if bottom else 0); yb = y1 - (c if top else 0)
        out.append(box(name, (x0, ya, z0), (x1, yb, z1)))
        for side, on, yc, yy in (('t', top, y1 - c, (y1 - c, y1)), ('b', bottom, y0 + c, (y0, y0 + c))):
            if not on: continue
            out.append(box(f'{name}_cap_{side}', (x0 + c, yy[0], z0), (x1 - c, yy[1], z1)))
            for lr, xc in (('l', x0 + c), ('r', x1 - c)):
                out.append(box(f'{name}_ch_{side}{lr}', (xc - s / 2, yc - s / 2, z0), (xc + s / 2, yc + s / 2, z1),
                               rot={'origin': [round(xc, 4), round(yc, 4), round((z0 + z1) / 2, 4)], 'z': 45}))
    else:  # axis y: vertical post, chamfer the edges at +z (top) / -z (bottom) faces
        za = z0 + (c if bottom else 0); zb = z1 - (c if top else 0)
        out.append(box(name, (x0, y0, za), (x1, y1, zb)))
        for side, on, zc, zz in (('t', top, z1 - c, (z1 - c, z1)), ('b', bottom, z0 + c, (z0, z0 + c))):
            if not on: continue
            out.append(box(f'{name}_cap_{side}', (x0 + c, y0, zz[0]), (x1 - c, y1, zz[1])))
            for lr, xc in (('l', x0 + c), ('r', x1 - c)):
                out.append(box(f'{name}_ch_{side}{lr}', (xc - s / 2, y0, zc - s / 2), (xc + s / 2, y1, zc + s / 2),
                               rot={'origin': [round(xc, 4), round((y0 + y1) / 2, 4), round(zc, 4)], 'y': 45}))
    return out


def tube8(name, cx, cy, r, z0, z1):
    """Octagonal tube along z: wide box + tall box + two 45 deg boxes (4 elements), apothem r."""
    a = r * math.tan(math.pi / 8)          # half side of the octagon
    out = [box(name, (cx - r, cy - a, z0), (cx + r, cy + a, z1)),
           box(f'{name}_v', (cx - a, cy - r, z0), (cx + a, cy + r, z1))]
    for k, ang in (('d1', 45), ('d2', -45)):
        out.append(box(f'{name}_{k}', (cx - r, cy - a, z0), (cx + r, cy + a, z1),
                       rot={'origin': [round(cx, 4), round(cy, 4), round((z0 + z1) / 2, 4)], 'z': ang}))
    return out


def rgbn(c, s, t, amp=6, seed=0):
    """Flat colour with a faint deterministic grain (keeps big flat faces from looking plastic)."""
    h = (int(s * 997) * 73856093 ^ int(t * 991) * 19349663 ^ seed * 83492791) & 0xffff
    d = (h % (2 * amp + 1)) - amp
    return tuple(max(0, min(255, v + d)) for v in c[:3]) + (255,)


def face_xyz(e, fn, s, t):
    """Model point of face coords (s, t) (kit face frame), for specials that paint by position."""
    import importlib, sys as _s
    from pathlib import Path as _P
    kp = str(_P(__file__).resolve().parents[4] / 'scripts/art/w325')
    if kp not in _s.path: _s.path.insert(0, kp)
    import kit
    return kit.face_point(e, fn, s, t)


def rc(M, name, hw, yr, zr, c, top=True, bottom=True, axis='z'):
    """M.rb box (rip ranges) with chamfered long edges (see cbox)."""
    b = M.rb('_', hw, yr, zr)
    return cbox(name, b['from'], b['to'], c, top=top, bottom=bottom, axis=axis)


class PwMap(RipMap):
    """RipMap whose along-gun axis is piecewise linear: beyond rip a = a_cut (toward the butt) the rip is compressed
    by factor k, so long rear tubes end before the first-person ADS camera (which sits ~13 px behind the sight)."""
    def __init__(self, *a, a_cut=0.1, k=1.0, **kw):
        super().__init__(*a, **kw); self.a_cut = a_cut; self.k = k

    def _az(self, a):
        d = a - self.a0
        if self.sz * (a - self.a_cut) > 0:
            d = (self.a_cut - self.a0) + (a - self.a_cut) * self.k
        return self.Z0 + self.sz * d * self.s

    def m(self, x, a, h):
        return (8 + self.sx * (x - self.x0) * self.s, self.Y0 + (h - self.h0) * self.s, self._az(a))

    def w(self, p):
        X, Y, Z = p
        zc = self._az(self.a_cut); d = self.sz * (Z - self.Z0) / self.s
        if self.sz * (Z - zc) > 0:
            a = self.a_cut + (self.sz * (Z - zc) / self.s) / self.k
        else:
            a = self.a0 + d
        out = [0.0, 0.0, 0.0]
        out[self.xi] = self.x0 + self.sx * (X - 8) / self.s; out[self.ai] = a; out[self.hi] = self.h0 + (Y - self.Y0) / self.s
        return tuple(out)


def camo(p, cell=1.3, seed=0, levels=(0.62,)):
    """Large-blob camo index at model point p: smooth value noise on a coarse grid, thresholded (0 = base colour)."""
    def h(i, j, k):
        n = (i * 73856093) ^ (j * 19349663) ^ (k * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177 & 0xffffffff
        return (n & 0xffff) / 65535.0
    x, y, z = p[0] / cell, p[1] / cell, p[2] / (cell * 1.6)
    i, j, k = math.floor(x), math.floor(y), math.floor(z); fx, fy, fz = x - i, y - j, z - k
    sm = lambda t: t * t * (3 - 2 * t)
    fx, fy, fz = sm(fx), sm(fy), sm(fz); v = 0.0
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                w = (fx if a else 1 - fx) * (fy if b else 1 - fy) * (fz if c else 1 - fz)
                v += w * h(i + a, j + b, k + c)
    return sum(1 for L in levels if v > L)


def seg(name, lo, hi, cuts, groove=0.06, gw=0.12, axis=2):
    """Split a box along `axis` at the given coordinates; each cut becomes a narrow groove inset by `groove` on the
    four side faces (machined panel joint).  Returns elements name_0..name_n and name_g0..; grooves are full-length
    inset boxes so the silhouette stays closed."""
    out = []; edges = [lo[axis]] + sorted(cuts) + [hi[axis]]
    for i in range(len(edges) - 1):
        a = edges[i] + (gw / 2 if i > 0 else 0); b = edges[i + 1] - (gw / 2 if i < len(edges) - 2 else 0)
        l = list(lo); h = list(hi); l[axis] = a; h[axis] = b
        out.append(box(f'{name}_{i}', l, h))
    for i, c in enumerate(sorted(cuts)):
        l = [v + groove for v in lo]; h = [v - groove for v in hi]
        l[axis] = c - gw / 2; h[axis] = c + gw / 2
        out.append(box(f'{name}_g{i}', l, h))
    return out
