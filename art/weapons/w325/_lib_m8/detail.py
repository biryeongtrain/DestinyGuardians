"""W325 worker-8 shared authoring helpers (detail pass): element constructors with chamfered sections and a
flat-material face painter for the kit bake.  Imported by art/weapons/w325/<id>/design.py of the m8 weapons.

Coordinates: model px, gun along z (muzzle -z), up +y, centre x=8.  Rotations use the kit/native 26.3 convention
(Rx then Ry then Rz about one origin; +z turns +x toward +y).
"""
import hashlib, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/art/w325'))
import kit  # noqa: E402  (View / face_point / default_grade only; kit is not modified)

R2 = math.sqrt(2.0)
EPS = 0.01


def box(name, lo, hi, rot=None, **kw):
    e = {'name': name, 'from': [round(v, 4) for v in lo], 'to': [round(v, 4) for v in hi]}
    if rot:
        e['rotation'] = {k: ([round(x, 4) for x in v] if k == 'origin' else round(v, 4)) for k, v in rot.items()}
    e.update(kw)
    return e


def rx(name, lo, hi, ang, origin=None):
    o = origin or [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2]
    return box(name, lo, hi, {'origin': o, 'x': ang})


def strut(name, p0, p1, thick, x0, x1, ext=0.0):
    """Box centred on the (z,y) segment p0->p1 (rotated about x)."""
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dz, dy) + 2 * ext
    th = math.degrees(math.atan2(-dy, dz))
    cz, cy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    return box(name, (x0, cy - thick / 2, cz - L / 2), (x1, cy + thick / 2, cz + L / 2),
               {'origin': [(x0 + x1) / 2, cy, cz], 'x': th})


def slope(name, p0, p1, thick, x0, x1, side='below', ext=(0.0, 0.0)):
    """Box whose top (side='below') or bottom (side='above') face lies on the (z,y) line p0->p1."""
    if p1[0] < p0[0]:
        p0, p1, ext = p1, p0, (ext[1], ext[0])
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dz, dy); ux, uy = dz / L, dy / L
    th = math.degrees(math.atan2(-uy, ux)); ny, nz = math.cos(math.radians(th)), math.sin(math.radians(th))
    mz = (p0[0] + p1[0]) / 2 + ux * (ext[1] - ext[0]) / 2
    my = (p0[1] + p1[1]) / 2 + uy * (ext[1] - ext[0]) / 2
    sg = -1 if side == 'below' else 1
    cy, cz = my + sg * ny * thick / 2, mz + sg * nz * thick / 2
    h = (L + ext[0] + ext[1]) / 2
    return box(name, (x0, cy - thick / 2, cz - h), (x1, cy + thick / 2, cz + h),
               {'origin': [(x0 + x1) / 2, cy, cz], 'x': th})


def cham(name, x0, x1, y0, y1, z0, z1, r, corners='tltrblbr', rb=None):
    """Section along z with 45-degree chamfers of size r on the chosen x-y corners (tl tr bl br).
    Core box (inset where chamfered) + one 45-degree strip per corner whose outer face is the chamfer plane.
    rb: separate chamfer size for the bottom corners."""
    rb = r if rb is None else rb
    t = 'tl' in corners or 'tr' in corners
    b = 'bl' in corners or 'br' in corners
    out = []
    rt, rbb = (r if t else 0), (rb if b else 0)
    # full-width middle band and narrower top/bottom caps
    out.append(box(name, (x0, y0 + rbb, z0), (x1, y1 - rt, z1)))
    if t:
        out.append(box(name + '_capt', (x0 + (r if 'tl' in corners else 0), y1 - rt, z0),
                       (x1 - (r if 'tr' in corners else 0), y1, z1)))
    if b:
        out.append(box(name + '_capb', (x0 + (rb if 'bl' in corners else 0), y0, z0),
                       (x1 - (rb if 'br' in corners else 0), y0 + rbb, z1)))
    for c in ('tl', 'tr', 'bl', 'br'):
        if c not in corners:
            continue
        rr = r if c[0] == 't' else rb
        L = rr * R2; d = rr / R2
        mx = x0 + rr / 2 if c[1] == 'l' else x1 - rr / 2
        my = y1 - rr / 2 if c[0] == 't' else y0 + rr / 2
        ang = 45 if c in ('tl', 'br') else -45
        ylo, yhi = (my - d, my) if c[0] == 't' else (my, my + d)
        # strip ends recessed 0.01 px so the core/cap end faces own the end plane (no coplanar z-fighting)
        out.append(box(f'{name}_ch{c}', (mx - L / 2, ylo, z0 + EPS), (mx + L / 2, yhi, z1 - EPS),
                       {'origin': [mx, my, (z0 + z1) / 2], 'z': ang}))
    return out


def ring(name, cx, cy, z0, z1, r_out, wall, n=8):
    """n-sided tube (barrel / muzzle) around (cx, cy) along z, wall thickness wall."""
    out = []
    side = 2 * r_out * math.tan(math.pi / n)
    for i in range(n):
        a = 360.0 * i / n
        rm = r_out - wall / 2
        out.append(box(f'{name}_{i}', (cx - side / 2, cy + rm - wall / 2, z0), (cx + side / 2, cy + rm + wall / 2, z1),
                       {'origin': [cx, cy, (z0 + z1) / 2], 'z': -a}))
    return out


# ------------------------------------------------------------------------------------------- flat material paint
def _hash(*v):
    return int(hashlib.md5(repr(v).encode()).hexdigest()[:6], 16) / 0xFFFFFF


class Flat:
    """Element/face policy -> flat material colour with subtle texel noise (replaces smeared projection).

    colours: {name_prefix: rgb}   explicit material colours (prefix match, longest wins)
    sample:  colour of other flat elements is the graded median of the rip seen from the side (cached).
    policy(e, fn) -> bool decides which faces are flat."""

    def __init__(self, wid, D, policy, colours=None, noise=4.0):
        self.wid, self.D, self.policy = wid, D, policy
        self.colours = dict(colours or {})
        self.noise = noise
        self.cache = {}
        self._views = None

    def views(self):
        if self._views is None:
            c = kit.art(self.wid) / 'proj_cache'
            man = json.loads((c / 'manifest.json').read_text())
            self._views = {k: kit.View(c, k, man) for k in man['views']}
        return self._views

    def colour(self, e):
        n = e['name']
        best = None
        for k, v in self.colours.items():
            if n.startswith(k) and (best is None or len(k) > len(best)):
                best = k
        if best is not None:
            return self.colours[best]
        key = n
        if key in self.cache:
            return self.cache[key]
        V = self.views(); acc = []
        grade = getattr(self.D, 'grade', kit.default_grade)
        for fn, vn in (('west', 'nx'), ('east', 'px'), ('up', 'pz')):
            v = V[vn]
            for i in range(5):
                for j in range(5):
                    p = kit.face_point(e, fn, (i + .5) / 5, (j + .5) / 5)
                    w = self.D.model2world(n, p)
                    c = v.sample(*v.project(w))
                    if c is not None:
                        acc.append(c)
            if len(acc) >= 8:
                break
        if not acc:
            col = (78, 78, 80)
        else:
            acc.sort(key=lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
            mid = acc[len(acc) // 4: max(len(acc) // 4 + 1, 3 * len(acc) // 4)]
            col = tuple(sum(c[k] for c in mid) / len(mid) for k in range(3))
            col = tuple(grade(col))
        self.cache[key] = col
        return col

    def __call__(self, e, fn, s, t):
        if not self.policy(e, fn):
            return None
        c = self.colour(e)
        k = (_hash(e['name'], fn, int(s * 40), int(t * 40)) - .5) * 2 * self.noise
        shade = {'up': 1.06, 'down': 0.86, 'north': 0.95, 'south': 0.95}.get(fn, 1.0)
        return tuple(max(0, min(255, int(round(ch * shade + k)))) for ch in c[:3]) + (255,)


def bore_disc(e, fn, s, t, centre, r_hole, r_lip=None, hole=(12, 12, 13), lip=None):
    """North-face bore painting for elements crossing the bore axis."""
    if fn != 'north':
        return None
    f, to = e['from'], e['to']
    if e.get('rotation'):
        return None
    x, y = to[0] - s * (to[0] - f[0]), to[1] - t * (to[1] - f[1])
    r = math.hypot(x - centre[0], y - centre[1])
    if r < r_hole:
        return hole + (255,)
    if r_lip and lip and r < r_lip:
        return tuple(lip) + (255,)
    return None


def chamy(name, x0, x1, y0, y1, z0, z1, r, corners='fbFB'):
    """Vertical section (long axis y) with 45-degree chamfers on x-z corners: f/b = front(-z)/back(+z) on the left
    (-x) side, F/B on the right (+x) side."""
    out = [box(name, (x0, y0, z0 + (r if ('f' in corners or 'F' in corners) else 0)),
               (x1, y1, z1 - (r if ('b' in corners or 'B' in corners) else 0)))]
    if 'f' in corners or 'F' in corners:
        out.append(box(name + '_capf', (x0 + (r if 'f' in corners else 0), y0, z0),
                       (x1 - (r if 'F' in corners else 0), y1, z0 + r)))
    if 'b' in corners or 'B' in corners:
        out.append(box(name + '_capb', (x0 + (r if 'b' in corners else 0), y0, z1 - r),
                       (x1 - (r if 'B' in corners else 0), y1, z1)))
    L = r * R2; d = r / R2
    for c in 'fbFB':
        if c not in corners:
            continue
        mx = x0 + r / 2 if c in 'fb' else x1 - r / 2
        mz = z0 + r / 2 if c in 'fF' else z1 - r / 2
        # strip long along the chamfer line in x-z; Ry(+a) turns +z toward +x
        ang = {'f': 45, 'B': 45, 'b': -45, 'F': -45}[c]
        zlo, zhi = (mz - d, mz) if c in 'bB' else (mz, mz + d)
        out.append(box(f'{name}_ch{c}', (mx - L / 2, y0 + EPS, zlo), (mx + L / 2, y1 - EPS, zhi),
                       {'origin': [mx, (y0 + y1) / 2, mz], 'y': ang}))
    return out


def zsplit(name, x0, x1, y0, y1, cuts, r=0.0, corners='', groove=0.07, inset=0.06, gtop=True, gbot=False):
    """DMW-style long mass: segments between cuts (z list incl. both ends), each a chamfered section, separated by
    recessed groove rings (inset on the sides, and on top/bottom if gtop/gbot)."""
    out = []
    for i in range(len(cuts) - 1):
        za = cuts[i] + (groove if i > 0 else 0)
        zb = cuts[i + 1] - (groove if i < len(cuts) - 2 else 0)
        nm = f'{name}{i}'
        if r > 0 and corners:
            out += cham(nm, x0, x1, y0, y1, za, zb, r, corners)
        else:
            out.append(box(nm, (x0, y0, za), (x1, y1, zb)))
        if i < len(cuts) - 2:
            out.append(box(f'{name}_groove{i}', (x0 + inset, y0 + (inset if gbot else 0), zb),
                           (x1 - inset, y1 - (inset if gtop else 0), zb + 2 * groove)))
    return out


# ------------------------------------------------------------------------------------------- coplanar cleanup
_FA = {'north': (2, 0), 'south': (2, 1), 'west': (0, 0), 'east': (0, 1), 'down': (1, 0), 'up': (1, 1)}


def _quad(e, fn):
    f, t = e['from'], e['to']; ax, side = _FA[fn]; r = kit.rot_of(e)
    o = [a for a in range(3) if a != ax]; pts = []
    for a_ in (f[o[0]], t[o[0]]):
        for b_ in (f[o[1]], t[o[1]]):
            p = [0, 0, 0]; p[ax] = t[ax] if side else f[ax]; p[o[0]] = a_; p[o[1]] = b_
            pts.append(kit.rotate(tuple(p), r))
    return pts, kit.rotate_vec(kit.NORMALS[fn], r)


def _plane2d(pts, n):
    a = (1, 0, 0) if abs(n[0]) < 0.9 else (0, 1, 0)
    u = [a[1] * n[2] - a[2] * n[1], a[2] * n[0] - a[0] * n[2], a[0] * n[1] - a[1] * n[0]]
    L = math.sqrt(sum(c * c for c in u)); u = [c / L for c in u]
    v = [n[1] * u[2] - n[2] * u[1], n[2] * u[0] - n[0] * u[2], n[0] * u[1] - n[1] * u[0]]
    return [(sum(p[i] * u[i] for i in range(3)), sum(p[i] * v[i] for i in range(3))) for p in pts]


def _inside(h, pt):
    s = None
    for i in range(len(h)):
        a, b = h[i], h[(i + 1) % len(h)]
        c = (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0])
        if abs(c) < 1e-9: continue
        if s is None: s = c > 0
        elif s != (c > 0): return False
    return True


def _overlap(A, B):
    hA, hB = kit.hull(A), kit.hull(B)
    xs = [p[0] for p in A]; ys = [p[1] for p in A]; n = hit = 0
    for i in range(6):
        for j in range(6):
            pt = (min(xs) + (max(xs) - min(xs)) * (i + .5) / 6, min(ys) + (max(ys) - min(ys)) * (j + .5) / 6)
            if _inside(hA, pt):
                n += 1; hit += _inside(hB, pt)
    return hit / max(n, 1)


def _vol(e):
    return abs((e['to'][0] - e['from'][0]) * (e['to'][1] - e['from'][1]) * (e['to'][2] - e['from'][2]))


def separate(E, inset=0.012, rounds=4):
    """Remove coplanar same-facing overlaps (z-fighting): the smaller element's face is pulled inward by `inset`
    along its own local axis.  Keeps every part where it was (sub-texel change)."""
    for _ in range(rounds):
        moved = False; done = set()
        Q = [(e, fn) + _quad(e, fn) for e in E for fn in _FA]
        for i in range(len(Q)):
            ea, fa, pa, na = Q[i]; da = sum(pa[0][k] * na[k] for k in range(3))
            for j in range(i + 1, len(Q)):
                eb, fb, pb, nb = Q[j]
                if ea is eb or sum(na[k] * nb[k] for k in range(3)) < 0.999: continue
                if abs(da - sum(pb[0][k] * nb[k] for k in range(3))) > 0.004: continue
                if max(_overlap(_plane2d(pa, na), _plane2d(pb, na)), _overlap(_plane2d(pb, na), _plane2d(pa, na))) < 0.02:
                    continue
                e, fn = (ea, fa) if _vol(ea) <= _vol(eb) else (eb, fb)
                ax, side = _FA[fn]
                if abs(e['to'][ax] - e['from'][ax]) <= 3 * inset: continue
                key = 'to' if side else 'from'
                if (id(e), fn) in done: continue
                e[key][ax] = round(e[key][ax] + (-inset if side else inset), 4)
                done.add((id(e), fn)); moved = True
        if not moved:
            break
    return E
