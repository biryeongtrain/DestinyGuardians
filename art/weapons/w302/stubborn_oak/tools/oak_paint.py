"""W302 Stubborn Oak hand-authored paint, sampled in WORLD space so coplanar
neighbouring faces share one continuous surface.  Palette re-derived from the
.blend 'Stubborn Oak_Shader Preset' (ivory worn dye 0.61 lin, dark slots
0.03-0.05, olive 0.084/0.080/0.034, warm orange emission) and the EEVEE review."""
import math

PALETTE = {
    'ivory': (221, 215, 198), 'steel': (176, 179, 178), 'dark': (52, 53, 54),
    'knurl': (150, 152, 150), 'pump': (112, 108, 74), 'collar': (74, 72, 54),
    'grip': (64, 64, 60), 'rubber': (38, 39, 40), 'bore': (16, 16, 18),
}
CHECKER = (38, 38, 36)
BORE = (16, 16, 18)


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def scale(c, k):
    return tuple(x * k for x in c)


def hsh(*v):
    h = 2166136261
    for x in v:
        h = ((h ^ (int(x) & 0xffffffff)) * 16777619) & 0xffffffff
    return (h & 0xffff) / 65535.0


def noise(p, cell=0.35):
    """Smooth value noise in model px (deterministic)."""
    g = [c / cell for c in p]
    i = [math.floor(c) for c in g]
    f = [c - k for c, k in zip(g, i)]
    f = [t * t * (3 - 2 * t) for t in f]
    acc = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[0] if dx else 1 - f[0]) * (f[1] if dy else 1 - f[1]) * (f[2] if dz else 1 - f[2])
                acc += w * hsh(i[0] + dx, i[1] + dy, i[2] + dz)
    return acc


def base(mat, p, n):
    c = PALETTE[mat]
    if mat == 'grip':
        c = scale(c, 0.96 + 0.08 * noise(p, 0.6))
    elif mat == 'ivory':
        k = 0.97 + 0.06 * noise(p, 0.9) + 0.02 * noise(p, 0.18)
        c = scale(c, k)
    elif mat in ('steel', 'knurl'):
        c = scale(c, 0.95 + 0.07 * noise(p, 0.5))
    elif mat == 'rubber':
        c = scale(c, 0.92 + 0.12 * noise(p, 0.08))
    return c


def finish(c, mat, convex, concave, n):
    if convex:
        hi = (246, 243, 234) if mat == 'ivory' else scale(c, 1.45)
        c = mix(c, hi, 0.55 * convex if n[1] > -0.5 else 0.25 * convex)
    if concave:
        c = scale(c, 1 - 0.32 * concave)
    if n[1] < -0.5:
        c = scale(c, 0.9)
    return tuple(max(0, min(255, int(round(v)))) for v in c)


def paint_flat(f, p, su, sv):
    mat = f.s.mat
    c = base(mat, p, f.n)
    convex, concave = f.edge_info(p, su, sv)
    return finish(c, mat, convex, concave, f.n)


# ---------------- decals (world space; positions from the registered rip renders) ----------
DARK = (24, 24, 26)
HOLE_WALL = (96, 93, 84)


def clamp01(v):
    return max(0.0, min(1.0, v))


def shield_holes():
    hs = []
    for sx in (-1, 1):
        for z in (-5.6, -4.9, -4.2, -3.5, -2.8, -2.1, 0.05, 0.75):
            hs.append(((8 + sx * 0.48, 12.32, z), 0.13))      # top-edge row (on bevel)
        for z in (-5.25, -4.55, -3.85, -3.15, -2.45, 0.4, 1.0):
            hs.append(((8 + sx * 0.6, 11.72, z), 0.16))       # side row
    return hs


HOLES = shield_holes()
SLOTS = [(-5.8, -4.55), (-4.15, -2.9), (-2.5, -1.75), (-0.1, 1.05)]   # shield lower slots (z)


def rrect(z, y, z0, z1, y0, y1, r):
    """signed-ish distance test for a rounded rect in (z,y); <=0 inside."""
    cz, cy = min(max(z, z0 + r), z1 - r), min(max(y, y0 + r), y1 - r)
    return math.hypot(z - cz, y - cy) - r


def recess(c, d, depth_dir):
    """Painted recess: flat dark core, soft shadowed rim (no lit wall -> clean shape)."""
    if d <= -0.035:
        return DARK
    if d <= 0:
        return mix(DARK, (70, 68, 62), 0.6)
    if d < 0.035:
        return scale(c, 0.82)
    return None


def decal(f, p):
    g, n = f.s.group, f.n
    x, y, z = p
    side = abs(n[0]) > 0.6
    top = n[1] > 0.6
    if g == 'shield':
        for (cx, cy, cz), r in HOLES:
            d = math.dist(p, (cx, cy, cz)) - r
            if d < 0.06:
                return 'recess', d, (cy - y) / r
        if side:
            for z0, z1 in SLOTS:
                d = rrect(z, y, z0, z1, 11.18, 11.36, .09)
                if d < 0.06:
                    return 'recess', d, (11.27 - y) / .09
        if top and abs(x - 8) < 0.04 and -5.9 < z < 1.2:
            return 'line', None, None
    if g == 'recv' and side:
        for args, cy, r in (((6.9, 8.9, 11.6, 11.9), 11.75, .15), ((5.9, 8.0, 10.66, 10.8), 10.73, .07),
                            ((1.7, 3.0, 11.45, 11.62), 11.53, .08)):
            d = rrect(z, y, *args, r)
            if d < 0.06:
                return 'recess', d, (cy - y) / r
        for sz, sy in ((4.1, 11.1), (6.35, 11.12), (2.2, 10.75)):
            if math.hypot(z - sz, y - sy) < 0.1:
                return 'screw', math.hypot(z - sz, y - sy), (z - sz, y - sy)
        if abs(y - 11.33) < 0.022 and 1.4 < z < 9.1:
            return 'line', None, None
        if 1.6 < z < 5.4 and abs((y - 10.55) - (z - 1.6) * 0.18) < 0.032:
            return 'line', None, None
    if g == 'rail' and top and (z - 2.2) % 0.3 < 0.11:
        return 'groove', None, None
    if g == 'rsight' and top and abs(x - 8) < 0.07 and z > 5.75:
        return 'groove', None, None
    if g == 'grip' and side:
        A = (10.45, 7.3)
        t = (A[0] - y) * 0.906 + (z - A[1]) * 0.423
        w = (z - A[1]) * 0.906 - (A[0] - y) * 0.423
        if 0.75 < t < 3.45 and abs(w) < 0.5:
            if t < 0.8 or t > 3.4 or abs(w) > 0.45:
                return 'border', None, None
            u, v = (t + w) / 0.16, (t - w) / 0.16
            return 'checker', (u % 1 < 0.5) ^ (v % 1 < 0.5), None
    if g == 'tube' and f.s.mat == 'knurl':
        if (z * 12 % 1 < 0.4) or ((x + y) * 12 % 1 < 0.35):
            return 'groove', None, None
    if g == 'pad' and side and (y - 8.7) % 0.32 < 0.07:
        return 'groove', None, None
    return None


CHIP = (118, 116, 108)


def paint(f, p, su, sv):
    mat = f.s.mat
    n = f.n
    c = base(mat, p, n)
    convex, concave = f.edge_info(p, su, sv)
    hit = decal(f, p)
    if hit:
        kind, a, b = hit
        if kind == 'recess':
            r = recess(c, a, b)
            if r is not None:
                return finish(r, 'dark', 0, 0, n)
        elif kind == 'line':
            c = scale(c, 0.72)
        elif kind == 'groove':
            c = scale(c, 0.55)
        elif kind == 'screw':
            dz, dy = b
            c = (60, 60, 60) if abs(dz - dy) < 0.025 else mix((150, 150, 145), (230, 228, 220), clamp01(0.5 + dy * 6))
            return finish(c, 'steel', 0, 0, n)
        elif kind == 'border':
            c = scale(c, 0.8)
        elif kind == 'checker':
            c = CHECKER if a else (84, 84, 79)
            return finish(c, 'dark', 0, concave, n)
    # sparse edge wear on the ivory dye (rip GStack wear shows darker metal on edges)
    if mat == 'ivory' and convex >= 1.0 and noise(p, 0.3) > 0.8 and noise(p, 0.07) > 0.45:
        c = mix(c, CHIP, 0.75)
        convex = 0
    return finish(c, mat, convex, concave, n)
