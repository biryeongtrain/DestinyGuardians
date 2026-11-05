"""W325 m8: Minecraft-style flat painter (W30 look) for the kit's special() hook.

Every face is painted from a per-element *region* function instead of the smeared projection: flat material colours,
2-3 colour camo as large world-space blobs, 1-texel panel/vent lines and small decals.  A region may return 'proj' to
keep the rip projection (logos that project cleanly); the kit pixel style then quantises it.
"""
import hashlib, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts/art/w325'))
import kit  # noqa: E402


def _h(ix, iy, iz, seed):
    return int(hashlib.md5(f'{ix},{iy},{iz},{seed}'.encode()).hexdigest()[:6], 16) / 0xFFFFFF


def vnoise(p, cell, seed=0):
    x, y, z = p[0] / cell, p[1] / cell, p[2] / cell
    x0, y0, z0 = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - x0, y - y0, z - z0
    sm = lambda t: t * t * (3 - 2 * t)
    fx, fy, fz = sm(fx), sm(fy), sm(fz)
    acc = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                acc += w * _h(x0 + dx, y0 + dy, z0 + dz, seed)
    return acc


def camo(p, cols, cell=1.6, seed=1, cuts=(0.42, 0.62)):
    """Large 2-3 colour blobs: cols[0] base, cols[1] mid blobs, cols[2] small highlight blobs."""
    v = 0.7 * vnoise(p, cell, seed) + 0.3 * vnoise(p, cell / 2.3, seed + 7)
    if len(cols) > 2 and v > cuts[1]:
        return cols[2]
    if v > cuts[0]:
        return cols[1]
    return cols[0]


SHADE = {'up': 1.0, 'down': 0.82, 'north': 0.93, 'south': 0.93, 'east': 0.97, 'west': 0.97}


def painter(region, shade=False):
    """region(name, fn, p, s, t, e) -> rgb | rgba | 'proj' | None(=proj).  Returns a kit special()."""
    def special(e, fn, s, t):
        p = kit.face_point(e, fn, s, t)
        c = region(e['name'], fn, p, s, t, e)
        if c is None or c == 'proj':
            return None
        if len(c) == 4:
            return tuple(c)
        k = SHADE[fn] if shade else 1.0
        return tuple(max(0, min(255, int(round(ch * k)))) for ch in c) + (255,)
    return special


def line(v, at, w=0.07):
    return abs(v - at) < w


def every(v, start, step, w=0.06):
    return ((v - start) % step) < w and v >= start


def disc(p, cx, cy, r):
    return math.hypot(p[0] - cx, p[1] - cy) < r


FONT = {  # 3x5 pixel glyphs, rows top->bottom
    'S': ['111', '100', '111', '001', '111'], 'U': ['101', '101', '101', '101', '111'],
    'R': ['110', '101', '110', '101', '101'], 'O': ['111', '101', '101', '101', '111'],
    'H': ['101', '101', '111', '101', '101'], 'A': ['010', '101', '111', '101', '101'],
    'K': ['101', '110', '100', '110', '101'], 'E': ['111', '100', '110', '100', '111'],
}


def text_hit(u, v, text, u0, v0, cell, flip=False):
    """True if (u, v) (u along text, v downward) falls on a lit glyph pixel of text starting at (u0, v0)."""
    i = math.floor((u - u0) / cell); j = math.floor((v - v0) / cell)
    if j < 0 or j > 4 or i < 0:
        return False
    k, r = divmod(i, 4)
    if k >= len(text) or r == 3:
        return False
    if flip:
        k = len(text) - 1 - k; r = 2 - r
    g = FONT.get(text[k])
    return bool(g) and g[j][r] == '1'
