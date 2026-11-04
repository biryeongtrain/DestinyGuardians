"""W302 Stubborn Oak: stdlib vector/rotation helpers.

Native 26.3 element rotation = Rz*Ry*Rx about origin (EulerXYZ, see
scripts/build_weapon_hud_w112.py rotate()).  Corner index bit0=x,bit1=y,bit2=z.
Face vertex order per face maps to uv (a,b),(c,b),(c,d),(a,d).
"""
import math

FACES = {'north': (3, 2, 0, 1), 'south': (6, 7, 5, 4), 'west': (2, 6, 4, 0),
         'east': (7, 3, 1, 5), 'up': (2, 3, 7, 6), 'down': (4, 5, 1, 0)}
NORMALS = {'north': (0, 0, -1), 'south': (0, 0, 1), 'west': (-1, 0, 0),
           'east': (1, 0, 0), 'up': (0, 1, 0), 'down': (0, -1, 0)}


def add(a, b): return [x + y for x, y in zip(a, b)]
def sub(a, b): return [x - y for x, y in zip(a, b)]
def mul(a, s): return [x * s for x in a]
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def length(a): return math.sqrt(dot(a, a))
def norm(a):
    n = length(a)
    return [x / n for x in a]
def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def matvec(M, v):
    return [sum(M[i][k] * v[k] for k in range(3)) for i in range(3)]


def transpose(M):
    return [[M[j][i] for j in range(3)] for i in range(3)]


def rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def ry(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def euler_matrix(x, y, z):
    return matmul(rz(z), matmul(ry(y), rx(x)))


def matrix_euler(M):
    """Inverse of euler_matrix (Rz Ry Rx)."""
    y = math.asin(max(-1.0, min(1.0, -M[2][0])))
    x = math.atan2(M[2][1], M[2][2])
    z = math.atan2(M[1][0], M[0][0])
    return [round(math.degrees(v), 6) + 0.0 for v in (x, y, z)]


class Solid:
    """One cuboid element in model px; from/to are pre-rotation bounds."""

    def __init__(self, name, lo, hi, mat, rot=None, origin=None, part='body', group=None):
        self.name, self.mat, self.part = name, mat, part
        self.group = group or name.split('_')[0]
        self.lo = [round(v, 6) for v in lo]
        self.hi = [round(v, 6) for v in hi]
        assert all(a < b for a, b in zip(self.lo, self.hi)), name
        self.rot = [round(v, 6) for v in rot] if rot and any(abs(v) > 1e-9 for v in rot) else None
        self.origin = [round(v, 6) for v in (origin or [(a + b) / 2 for a, b in zip(self.lo, self.hi)])]
        self.M = euler_matrix(*self.rot) if self.rot else [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        self.Mt = transpose(self.M)
        self.corners = [self.world([self.hi[a] if m >> a & 1 else self.lo[a] for a in range(3)])
                        for m in range(8)]
        self.aabb = ([min(c[i] for c in self.corners) for i in range(3)],
                     [max(c[i] for c in self.corners) for i in range(3)])

    def world(self, p):
        return add(matvec(self.M, sub(p, self.origin)), self.origin)

    def contains(self, p, eps=1e-5):
        lo, hi = self.aabb
        if any(p[i] < lo[i] - eps or p[i] > hi[i] + eps for i in range(3)):
            return False
        q = add(matvec(self.Mt, sub(p, self.origin)), self.origin)
        return all(self.lo[i] - eps < q[i] < self.hi[i] + eps for i in range(3))

    def face_quad(self, face):
        return [self.corners[i] for i in FACES[face]]

    def normal(self, face):
        return matvec(self.M, list(NORMALS[face]))

    def element_rotation(self):
        if not self.rot:
            return None
        return {'origin': self.origin, 'x': self.rot[0], 'y': self.rot[1], 'z': self.rot[2]}


def chamfer_section(name, x0, x1, y0, y1, z0, z1, r, mat, top=True, bottom=False,
                    pitch=0.0, pivot=None, group=None):
    """Long box with 45-degree chamfered long edges: core + side slab + corner prisms.

    Corner prisms are inset 0.004 px at both ends so their end caps sit just
    behind the slab caps (no coplanar end-cap overlap).
    """
    out = []
    g = group or name
    piv = pivot
    R = rx(pitch)
    ya = y0 + (r if bottom else 0)
    yb = y1 - (r if top else 0)
    out.append(dict(name=name + '_core', lo=[x0 + r, y0, z0], hi=[x1 - r, y1, z1], mat=mat, group=g))
    out.append(dict(name=name + '_side', lo=[x0, ya, z0], hi=[x1, yb, z1], mat=mat, group=g))
    s = r * math.sqrt(2)
    corners = []
    if top:
        corners += [('tl', x0 + r, y1 - r), ('tr', x1 - r, y1 - r)]
    if bottom:
        corners += [('bl', x0 + r, y0 + r), ('br', x1 - r, y0 + r)]
    for tag, cx, cy in corners:
        out.append(dict(name=f'{name}_bevel_{tag}', lo=[cx - s / 2, cy - s / 2, z0 + 0.004],
                        hi=[cx + s / 2, cy + s / 2, z1 - 0.004], mat=mat, group=g,
                        local_z45=True))
    for d in out:
        d['pitch'] = pitch
        d['pivot'] = piv
    return out


def realize(spec):
    """Turn a spec dict (optional pitch/pivot/local_z45) into a Solid."""
    lo, hi = spec['lo'], spec['hi']
    pitch = spec.get('pitch', 0.0) or 0.0
    rot = spec.get('rot')
    if spec.get('local_z45') or pitch:
        c = [(a + b) / 2 for a, b in zip(lo, hi)]
        L = rz(45) if spec.get('local_z45') else [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        P = rx(pitch)
        piv = spec.get('pivot') or c
        # place the box about its own centre: centre moves by pitch about pivot
        wc = add(matvec(P, sub(c, piv)), piv)
        half = [(b - a) / 2 for a, b in zip(lo, hi)]
        lo2, hi2 = sub(wc, half), add(wc, half)
        eul = matrix_euler(matmul(P, L))
        return Solid(spec['name'], lo2, hi2, spec['mat'], eul, wc, spec.get('part', 'body'),
                     spec.get('group'))
    return Solid(spec['name'], lo, hi, spec['mat'], rot, spec.get('origin'),
                 spec.get('part', 'body'), spec.get('group'))
