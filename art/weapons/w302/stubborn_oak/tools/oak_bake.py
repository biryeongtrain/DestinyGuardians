"""W302 Stubborn Oak: face culling, world-projected texel grid, edge/AO classes,
atlas packing and native element export (stdlib + PIL)."""
import math
from PIL import Image
from oak_math import FACES, add, sub, mul, dot, cross, length, norm

D = 32            # texels per model px (uniform -> coplanar seams line up)
ATLAS = 1024
UVU = ATLAS / 16  # texels per native UV unit
PAD = 2
EPS = 0.004


def candidates(solids, s, pad=0.25):
    lo, hi = s.aabb
    out = []
    for o in solids:
        a, b = o.aabb
        if all(a[i] <= hi[i] + pad and b[i] >= lo[i] - pad for i in range(3)):
            out.append(o)
    return out


def inside_any(p, cands, skip=None):
    for o in cands:
        if o is not skip and o.contains(p):
            return True
    return False


def face_hidden(s, face, cands, step=0.08):
    """Hidden only if every sample (<= step px apart, inset 0.02) is inside another solid."""
    q = s.face_quad(face)
    n = s.normal(face)
    eu, ev = sub(q[1], q[0]), sub(q[3], q[0])
    lu, lv = length(eu), length(ev)
    nu, nv = max(2, math.ceil(lu / step) + 1), max(2, math.ceil(lv / step) + 1)
    others = [o for o in cands if o is not s]
    for a in range(nu):
        ta = min(max(a / (nu - 1), 0.02 / lu), 1 - 0.02 / lu)
        for b in range(nv):
            tb = min(max(b / (nv - 1), 0.02 / lv), 1 - 0.02 / lv)
            p = add(add(q[0], mul(eu, ta)), mul(ev, tb))
            if not inside_any(add(p, mul(n, EPS * 2)), others):
                return False
    return True


def axis_of(v):
    for i in range(3):
        if abs(abs(v[i]) - 1) < 1e-6:
            return i, (1 if v[i] > 0 else -1)
    return None, 0


class Face:
    def __init__(self, s, face, cands):
        self.s, self.face, self.cands = s, face, cands
        self.q = s.face_quad(face)
        self.n = s.normal(face)
        self.eu = sub(self.q[1], self.q[0])
        self.ev = sub(self.q[3], self.q[0])
        self.lu, self.lv = length(self.eu), length(self.ev)
        self.tu, self.tv = norm(self.eu), norm(self.ev)
        self.ou, self.wu = self._grid(self.q[0], self.tu, self.lu)
        self.ov, self.wv = self._grid(self.q[0], self.tv, self.lv)

    def _grid(self, p0, t, L):
        """(fractional start offset in texels, rect size) aligned to world 1/D grid."""
        ax, sg = axis_of(t)
        if ax is None:
            return 0.0, max(1, math.ceil(L * D - 1e-6))
        w0 = p0[ax] * D
        g = math.floor(w0 + 1e-6) if sg > 0 else math.ceil(w0 - 1e-6)
        off = abs(w0 - g)
        if off > 1 - 1e-6:
            off = 0.0
        return off, max(1, math.ceil(off + L * D - 1e-6))

    def point(self, i, j):
        su = min(max((i + 0.5 - self.ou) / D, 0.0), self.lu)
        sv = min(max((j + 0.5 - self.ov) / D, 0.0), self.lv)
        return add(add(self.q[0], mul(self.tu, su)), mul(self.tv, sv)), su, sv

    def edge_info(self, p, su, sv):
        """(convex, concave) strengths 0..1 for world point p on this face."""
        convex = concave = 0.0
        n = self.n
        near = min(su, self.lu - su, sv, self.lv - sv) < 0.17
        others = [o for o in self.cands if o is not self.s and
                  all(o.aabb[0][k] - 0.2 <= p[k] <= o.aabb[1][k] + 0.2 for k in range(3))]
        if not near and not others:
            return 0.0, 0.0
        for t in (self.tu, self.tv, mul(self.tu, -1), mul(self.tv, -1)):
            for d, w in ((0.05, 1.0), (0.1, 0.5), (0.16, 0.22)):
                lat = add(p, mul(t, d))
                if near and convex < w and not inside_any(add(lat, mul(n, -EPS)), self.cands):
                    convex = max(convex, w)
                if others and concave < w and inside_any(add(lat, mul(n, EPS)), others):
                    concave = max(concave, w)
        return convex, concave


def collect(solids):
    faces = []
    for s in solids:
        cands = candidates(solids, s)
        for f in FACES:
            if not face_hidden(s, f, cands):
                faces.append(Face(s, f, cands))
    return faces


def pack(faces):
    order = sorted(faces, key=lambda f: (-(f.wv + 2 * PAD), -(f.wu + 2 * PAD), f.s.name, f.face))
    x = y = 0
    shelf = 0
    for f in order:
        w, h = f.wu + 2 * PAD, f.wv + 2 * PAD
        if x + w > ATLAS:
            x, y = 0, y + shelf
            shelf = 0
        if y + h > ATLAS:
            raise ValueError('atlas overflow at ' + f.s.name)
        f.ax, f.ay = x + PAD, y + PAD
        x += w
        shelf = max(shelf, h)
    return y + shelf


def bake(faces, paint):
    img = Image.new('RGBA', (ATLAS, ATLAS), (0, 0, 0, 0))
    px = img.load()
    for f in faces:
        rows = []
        for j in range(f.wv):
            row = []
            for i in range(f.wu):
                p, su, sv = f.point(i, j)
                row.append(paint(f, p, su, sv))
            rows.append(row)
        for j in range(-PAD, f.wv + PAD):
            jj = min(max(j, 0), f.wv - 1)
            for i in range(-PAD, f.wu + PAD):
                ii = min(max(i, 0), f.wu - 1)
                r, g, b = rows[jj][ii]
                px[f.ax + i, f.ay + j] = (r, g, b, 255)
    return img


def uv(f):
    a = (f.ax + f.ou) / UVU
    b = (f.ay + f.ov) / UVU
    c = (f.ax + f.ou + f.lu * D) / UVU
    d = (f.ay + f.ov + f.lv * D) / UVU
    return [round(v, 6) for v in (a, b, c, d)]


def elements(solids, faces):
    by = {}
    for f in faces:
        by.setdefault(id(f.s), {})[f.face] = {'uv': uv(f), 'texture': '#0'}
    out = {}
    for s in solids:
        fs = by.get(id(s))
        if not fs:
            continue
        e = {'name': s.name, 'from': s.lo, 'to': s.hi}
        r = s.element_rotation()
        if r:
            e['rotation'] = r
        e['faces'] = {k: fs[k] for k in ('north', 'east', 'south', 'west', 'up', 'down') if k in fs}
        out.setdefault(s.part, []).append(e)
    return out
