#!/usr/bin/env python3
"""W302 Khvostov 7G-02 (skin id khvostov_7g_02) — deterministic texture/UV builder and Blockbench export converter.

Geometry is authored in Blockbench (project art/weapons/w302/khvostov_7g_02/khvostov_7g_02.bbmodel, Java Block/Item);
this script only produces texture/UV data from the read-only rip and converts the Blockbench export into the game parts.
Standard library + Pillow only.  Byte-identical PNGs need the encoder the committed atlas was written with: Pillow 13.0.0
on zlib-ng 1.3.1 (DestinyGuardians-wortrees/w300-evidence/models/venv/bin/python); other Pillow/zlib builds give the same
pixels with different PNG bytes.

  extract              headless Blender on the source .blend -> art/.../proj_cache (6 ortho views: albedo RGBA8 + depth 16-bit)
  bake EXPORT.json     Blockbench java_block export -> per-face UV layout (uv_layout.json), atlas PNG, HUD icon
  reticle              idempotent post-bake on the current atlas only (clear the holo glass, paint the reticle swatch)
  convert EXPORT.json  Blockbench export with the atlas UVs applied -> parts.json + src/main/resources/destiny/weapon_skins json

Model space: vanilla item px, gun along z (muzzle -z), up +y, centred at x=8.  The source is mapped to model space by a
piecewise station map along the length (barrel/handguard, receiver, buffer, stock) plus per-part frames for the parts that
were moved to fit the gnawing_hunger layout contract (sight raised, magazine/grip shifted and re-raked).
"""
import hashlib, json, math, os, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SKIN = 'khvostov_7g_02'
ART = ROOT / 'art/weapons/w302' / SKIN
CACHE = ART / 'proj_cache'
SRC_DIR = Path.home() / 'Downloads/tutorial-weapons/Khvostov 7G-02/Khvostov 7G-02'
SRC_FILES = ['Khvostov 7G-02.blend', 'Khvostov 7G-02.fbx',
             'a638eb80_Diffuse.png', 'a738eb80_Normal.png', 'a838eb80_GStack.png',
             'c237eb80_Diffuse.png', 'c337eb80_Normal.png', 'c437eb80_GStack.png',
             'f8e4ea80_Diffuse.png', 'f9e4ea80_Normal.png', 'fae4ea80_GStack.png']
ATLAS = ROOT / 'src/main/resources/assets/destiny/textures/item/weapon/w302' / f'{SKIN}.png'
HUD = ROOT / 'src/main/resources/assets/destiny/textures/item/hud/w302' / f'ammo_{SKIN}.png'
PARTS = ART / 'parts.json'
SKIN_JSON = ROOT / 'src/main/resources/destiny/weapon_skins' / f'{SKIN}.json'
UVLAYOUT = ART / 'uv_layout.json'
BLENDER = '/Applications/Blender.app/Contents/MacOS/Blender'

T = 20            # texels per model px
ATLAS_SIZE = 512
SS = 2            # supersamples per texel axis

# ---------------------------------------------------------------- ADS holo reticle (W303, user-selected "master r1")
# Item rendering is cutout, so the holo glass is fully clear and the reticle is geometry: two short red hairline dashes
# either side of the window centre plus a small red centre dot just below it, on the plane z 2.78..2.80 where the W148
# aim tip of the base layout sits (the ADS eye looks down -z through the glass at z 4.56..4.6).  The skin json sets
# "no_overlay" so the white W148 dot is not drawn.  All three quads sample the centre of a 2x2 opaque red swatch.
# shade:false + light_emission 15 keep the red legible in dark areas (geometry/UV identical to r1).
RETICLE_RGBA = (225, 40, 36, 255)
RETICLE_SWATCH = (500, 500, 502, 502)          # atlas px box painted with RETICLE_RGBA (free atlas tail)
RETICLE_UV = [15.640625, 15.640625, 15.671875, 15.671875]   # texel-centre half of the swatch (500.5..501.5 px)
RETICLE_BOXES = {                               # name: (from, to)
    'reticle_l': ([7.66, 12.773, 2.78], [7.8, 12.797, 2.8]),
    'reticle_r': ([8.2, 12.773, 2.78], [8.34, 12.797, 2.8]),
    'reticle_tick': ([7.988, 12.7, 2.78], [8.012, 12.745, 2.8]),     # centre dot
}


def reticle_elements():
    return [{'name': n, 'from': list(f), 'to': list(t), 'shade': False, 'light_emission': 15,
             'faces': {fn: {'uv': list(RETICLE_UV), 'texture': '#0'} for fn in ('north', 'south')}}
            for n, (f, t) in RETICLE_BOXES.items()]


def is_reticle(name):
    return name.startswith('reticle_')

# ---------------------------------------------------------------- source -> model station map
S0 = 24.87 / 0.95562          # model px per metre
Y0, Z0, DY = -0.69116, 0.11645, 0.21
BP = [(-9.43, -9.54), (2.6, 1.79), (9.3, 8.49), (10.6, 10.62), (15.43, 15.45)]   # (uniform-map z, model z)


def znew2old(zn):
    for i in range(len(BP) - 1):
        (o0, n0), (o1, n1) = BP[i], BP[i + 1]
        if zn <= n1 or i == len(BP) - 2:
            if zn < BP[0][1]:
                (o0, n0), (o1, n1) = BP[0], BP[1]
            return o0 + (zn - n0) * (o1 - o0) / (n1 - n0)


def model2world(p):
    x, y, z = p
    zo = znew2old(z)
    return (-(x - 8.0) / S0, (zo + 9.43) / S0 + Y0, (y - DY - 10.66) / S0 + Z0)


def _frame_map(p, mine, src):
    """Map a point between two 2D (z,y) frames: (centre, tilt deg from vertical, top leaning +z; axial/lateral scale)."""
    x, y, z = p
    (mz, my), mt = mine
    (sz, sy), st, ka, kt = src
    a = math.radians(mt); ax = (math.sin(a), math.cos(a)); lat = (math.cos(a), -math.sin(a))
    dz, dy = z - mz, y - my
    u = dz * ax[0] + dy * ax[1]; v = dz * lat[0] + dy * lat[1]
    b = math.radians(st); bx = (math.sin(b), math.cos(b)); bl = (math.cos(b), -math.sin(b))
    u *= ka; v *= kt
    return (x, sy + u * bx[1] + v * bl[1], sz + u * bx[0] + v * bl[0])


def part_transform(name, p):
    """Model point of a moved part -> the equivalent point of the unmoved (station-mapped) source part."""
    x, y, z = p
    if name.startswith('sight_'):
        return (x, y - 0.235, z)
    if name.startswith('mag_'):
        # magazine moved to the contract box (gnawing_hunger magazine) - source body axis 16.1 deg, ours 15.4 deg
        return _frame_map(p, ((3.474, 6.725), 15.4), ((4.166, 7.085), 16.1, 1.0, 1.05))
    if name.startswith('buttpad_'):
        # rubber pad shifted 0.1 back so the butt ends exactly at the contract z 15.45
        return (x, y, 14.85 + (z - 14.95) * 0.8)
    if name.startswith('grip_'):
        # grip re-raked into the contract grip box; shear back to the source rake
        return (x, 9.9 - (9.9 - y) * 0.947, z + (9.9 - y) * 0.2)
    return p

# ---------------------------------------------------------------- geometry helpers
FACE_AXES = {   # (plane axis, plane at 'from'/'to', u axis, u from->to?, v axis, v from->to?)  Blockbench default UV orientation
    'north': (2, 0, 0, False, 1, False), 'south': (2, 1, 0, True, 1, False),
    'east': (0, 1, 2, False, 1, False), 'west': (0, 0, 2, True, 1, False),
    'up': (1, 1, 0, True, 2, True), 'down': (1, 0, 0, True, 2, False),
}
NORMALS = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0), 'up': (0, 1, 0), 'down': (0, -1, 0)}


def rot_of(e):
    r = e.get('rotation')
    if not r:
        return None
    if 'axis' in r:
        return (r['origin'], [(r['axis'], r['angle'])])
    return (r['origin'], [(a, r.get(a, 0)) for a in ('x', 'y', 'z') if r.get(a, 0)])


def rotate(p, rot, inverse=False):
    if not rot:
        return p
    o, rs = rot
    x, y, z = p[0] - o[0], p[1] - o[1], p[2] - o[2]
    seq = list(reversed(rs)) if inverse else rs
    for ax, ang in seq:
        a = math.radians(-ang if inverse else ang); c, s = math.cos(a), math.sin(a)
        if ax == 'x':
            y, z = y * c - z * s, y * s + z * c
        elif ax == 'y':
            x, z = x * c + z * s, -x * s + z * c
        else:
            x, y = x * c - y * s, x * s + y * c
    return (x + o[0], y + o[1], z + o[2])


def rotate_vec(v, rot):
    if not rot:
        return v
    q = rotate(v, ((0, 0, 0), rot[1]))
    return q


def inside(e, p, eps=0.002):
    q = rotate(p, rot_of(e), inverse=True)
    f, t = e['from'], e['to']
    return all(min(f[i], t[i]) + eps < q[i] < max(f[i], t[i]) - eps for i in range(3))


def face_frame(e, fn):
    """Origin, u vector, v vector (local, unrotated) for the Blockbench default UV orientation of a face."""
    f, t = e['from'], e['to']
    pa, side, ua, ufwd, va, vfwd = FACE_AXES[fn]
    o = [0.0, 0.0, 0.0]
    o[pa] = t[pa] if side else f[pa]
    o[ua] = f[ua] if ufwd else t[ua]
    o[va] = f[va] if vfwd else t[va]
    u = [0.0, 0.0, 0.0]; v = [0.0, 0.0, 0.0]
    u[ua] = (t[ua] - f[ua]) * (1 if ufwd else -1)
    v[va] = (t[va] - f[va]) * (1 if vfwd else -1)
    return o, u, v


def face_point(e, fn, s, t_, push=0.0):
    o, u, v = face_frame(e, fn)
    n = NORMALS[fn]
    p = tuple(o[i] + u[i] * s + v[i] * t_ + n[i] * push for i in range(3))
    return rotate(p, rot_of(e))

# ---------------------------------------------------------------- projection cache
class View:
    def __init__(self, name, man):
        v = man['views'][name]
        self.name = name; self.ppm = man['ppm']
        self.c, self.R, self.U, self.d = v['centre'], v['right'], v['up'], v['dir']
        self.dmin, self.dmax = v['dmin'], v['dmax']
        al = Image.open(CACHE / f'{name}_albedo.png').convert('RGBA')
        self.W, self.H = al.size
        self.alb = al.load()
        self.dep = Image.open(CACHE / f'{name}_depth.png').load()

    def project(self, w):
        q = [w[i] - self.c[i] for i in range(3)]
        return (self.W / 2 + sum(q[i] * self.R[i] for i in range(3)) * self.ppm,
                self.H / 2 - sum(q[i] * self.U[i] for i in range(3)) * self.ppm)

    def depth_at(self, x, y):
        xi, yi = int(x), int(y)
        if not (0 <= xi < self.W and 0 <= yi < self.H):
            return None
        val = self.dep[xi, yi]
        if val == 0:
            return None
        return self.dmin + (val / 65535 - 0.02) / 0.98 * (self.dmax - self.dmin)

    def sample(self, x, y):
        x -= 0.5; y -= 0.5
        x0, y0 = math.floor(x), math.floor(y); fx, fy = x - x0, y - y0
        acc = [0.0, 0.0, 0.0]; aw = 0.0
        for dx, dy, wgt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            xi, yi = x0 + dx, y0 + dy
            if 0 <= xi < self.W and 0 <= yi < self.H and wgt > 0:
                r, g, b, a = self.alb[xi, yi]
                k = wgt * a / 255
                acc[0] += r * k; acc[1] += g * k; acc[2] += b * k; aw += k
        if aw < 0.5:
            return None
        return (acc[0] / aw, acc[1] / aw, acc[2] / aw)


def pick_view(views, nm):
    # model normal -> world normal: x flips, model z ~ world +y, model y = world z
    wn = (-nm[0], nm[2], nm[1])
    i = max(range(3), key=lambda k: abs(wn[k]))
    key = ('p' if wn[i] > 0 else 'n') + 'xyz'[i]
    return views[key]

OCC_TOL = 0.30 / S0     # source surface more than 0.3 model px in front of our face = occluder

# ---------------------------------------------------------------- colour
def grade(rgb):
    """Weathered gunmetal: neutral greys are slightly desaturated, warm (rust) texels keep/boost their chroma."""
    r, g, b = rgb
    yv = 0.299 * r + 0.587 * g + 0.114 * b
    y2 = 80 + (yv - 70) * 1.22
    warm = max(0.0, min(1.0, ((r - b) - 4.0) / 14.0))
    k = 0.72 + 0.68 * warm
    out = [y2 + (c - yv) * k for c in (r, g, b)]
    return tuple(max(0, min(255, int(round(c)))) for c in out)


def lighten(c, f):
    return tuple(max(0, min(255, int(round(ch + (255 - ch) * f if f > 0 else ch * (1 + f))))) for ch in c[:3])

# ---------------------------------------------------------------- bake
def load_export(path):
    d = json.loads(Path(path).read_text())
    return d['elements']


def hidden_face(e, fn, others):
    """A face is hidden only if every sample of a <=0.08 px grid (just outside it) lies inside another element."""
    o, u, v = face_frame(e, fn)
    lu = math.sqrt(sum(a * a for a in u)); lv = math.sqrt(sum(a * a for a in v))
    nu = max(3, math.ceil(lu / 0.08)); nv = max(3, math.ceil(lv / 0.08))
    for i in range(nu):
        for j in range(nv):
            p = face_point(e, fn, (i + 0.5) / nu, (j + 0.5) / nv, push=0.02)
            if not any(inside(x, p) for x in others):
                return False
    return True


def edge_flags(e, fn, others):
    """For the 4 face edges (u0,u1,v0,v1): True if convex (surface does not continue across it)."""
    flags = []
    for (s, t_) in ((-0.004, 0.5), (1.004, 0.5), (0.5, -0.004), (0.5, 1.004)):
        o, u, v = face_frame(e, fn)
        lu = math.sqrt(sum(a * a for a in u)) or 1; lv = math.sqrt(sum(a * a for a in v)) or 1
        ss = 0.5 + (s - 0.5) * (1 + 0.06 / lu) if s not in (0.5,) else 0.5
        tt = 0.5 + (t_ - 0.5) * (1 + 0.06 / lv) if t_ not in (0.5,) else 0.5
        p = face_point(e, fn, ss, tt, push=-0.015)
        flags.append(not any(inside(x, p) for x in others))
    return flags


def special(e, fn, s, t_, base):
    """Hand-painted overrides; return (rgba) or None."""
    n = e['name']
    if n == 'muzzle_bore_backstop':
        return (18, 18, 20, 255)
    if n.startswith('muzzle_slat_'):
        c = face_point(e, fn, 0.5, 0.5); nm = rotate_vec(NORMALS[fn], rot_of(e))
        radial = (c[0] - 8.0, c[1] - 10.87)
        if nm[0] * radial[0] + nm[1] * radial[1] < -0.01:      # faces the bore
            return (30, 30, 33, 255)
    if n == 'sight_glass':
        # Item rendering is cutout: any partial alpha draws opaque, so the glass is clear (W302 r2 Vision); the reticle
        # is separate geometry (reticle_elements), not glass texels.
        return (0, 0, 0, 0)
    if n.startswith('sight_frame') and fn in ('north', 'south'):
        return None
    if n.startswith('sight_frame'):
        nm = rotate_vec(NORMALS[fn], rot_of(e)); c = face_point(e, fn, 0.5, 0.5)
        if nm[0] * (8.0 - c[0]) + nm[1] * (12.785 - c[1]) > 0.01:   # faces into the window
            return (34, 34, 37, 255)
    if n == 'light_head_h' and fn == 'north' or n == 'light_head_v' and fn == 'north':
        p = face_point(e, fn, s, t_)
        r = math.hypot(p[0] - 6.83, p[1] - 10.92)
        if r < 0.27:
            return (int(225 - r * 120), int(228 - r * 110), int(214 - r * 120), 255)
        if r < 0.33:
            return (60, 60, 62, 255)
    return None


def bake_face(e, fn, views, others_occ):
    o, u, v = face_frame(e, fn)
    lu = math.sqrt(sum(a * a for a in u)); lv = math.sqrt(sum(a * a for a in v))
    w = max(1, int(round(lu * T))); h = max(1, int(round(lv * T)))
    nm = rotate_vec(NORMALS[fn], rot_of(e))
    view = pick_view(views, nm)
    img = Image.new('RGBA', (w, h)); px = img.load()
    valid = [[False] * h for _ in range(w)]
    name = e['name']
    for i in range(w):
        for j in range(h):
            sp = special(e, fn, (i + 0.5) / w, (j + 0.5) / h, None)
            if sp is not None:
                px[i, j] = sp; valid[i][j] = True; SPECIAL_PIX.setdefault((name, fn), set()).add((i, j)); continue
            acc = [0.0, 0.0, 0.0]; n = 0
            for a in range(SS):
                for b in range(SS):
                    s = (i + (a + 0.5) / SS) / w; t_ = (j + (b + 0.5) / SS) / h
                    p = face_point(e, fn, s, t_)
                    q = part_transform(name, p)
                    wp = model2world(q)
                    x, y = view.project(wp)
                    dsrc = view.depth_at(x, y)
                    if dsrc is None:
                        continue
                    dmine = sum(wp[k] * view.d[k] for k in range(3))
                    if dsrc > dmine + OCC_TOL:
                        continue
                    c = view.sample(x, y)
                    if c is None:
                        continue
                    acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]; n += 1
            if n * 2 >= SS * SS:
                px[i, j] = grade((acc[0] / n, acc[1] / n, acc[2] / n)) + (255,); valid[i][j] = True
    return img, valid


SPECIAL_PIX = {}     # (element, face) -> hand-painted texels, excluded from the speckle filter


def despeckle(img, keep):
    """Half-strength 3x3 median: removes single-texel reprojection speckle, keeps rivets/edges (>=3 texels)."""
    w, h = img.size
    if w < 3 or h < 3:
        return img
    med = img.filter(ImageFilter.MedianFilter(3))
    out = Image.blend(img, med, 0.5)
    if keep:
        src = img.load(); dst = out.load()
        for (i, j) in keep:
            dst[i, j] = src[i, j]
    return out


def inpaint(img, valid, fallback):
    w, h = img.size; px = img.load()
    if not any(any(col) for col in valid):
        for i in range(w):
            for j in range(h):
                px[i, j] = fallback
        return
    todo = [(i, j) for i in range(w) for j in range(h) if not valid[i][j]]
    while todo:
        nxt = []; upd = []
        for (i, j) in todo:
            acc = [0, 0, 0]; n = 0
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    a, b = i + di, j + dj
                    if (di or dj) and 0 <= a < w and 0 <= b < h and valid[a][b]:
                        c = px[a, b]; acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]; n += 1
            if n:
                upd.append((i, j, (acc[0] // n, acc[1] // n, acc[2] // n, 255)))
            else:
                nxt.append((i, j))
        if not upd:
            for (i, j) in nxt:
                px[i, j] = fallback
            break
        for i, j, c in upd:
            px[i, j] = c; valid[i][j] = True
        todo = nxt


def apply_edges(img, flags, fn):
    """1-texel bevel highlight on convex edges; slightly darker on lower edges of side faces."""
    w, h = img.size; px = img.load()
    if w < 3 or h < 3:
        return
    u0, u1, v0, v1 = flags
    side = fn in ('north', 'south', 'east', 'west')
    def tint(i, j, f):
        c = px[i, j]
        if c[3] < 255:
            return
        px[i, j] = lighten(c, f) + (255,)
    if v0:   # top edge of side faces (v runs downward)
        for i in range(w): tint(i, 0, 0.16 if side else 0.10)
    if v1:
        for i in range(w): tint(i, h - 1, -0.18 if side else 0.08)
    if u0:
        for j in range(h): tint(0, j, 0.08)
    if u1:
        for j in range(h): tint(w - 1, j, 0.08)


def pack(rects, width):
    """Shelf packer; rects: list of (key, w, h). Returns {key:(x,y)} and used height."""
    order = sorted(rects, key=lambda r: (-r[2], -r[1], r[0]))
    pos = {}; x = y = shelf = 0
    for key, w, h in order:
        if x + w > width:
            y += shelf; x = 0; shelf = 0
        pos[key] = (x, y); x += w; shelf = max(shelf, h)
    return pos, y + shelf


def is_magazine(name):
    return name.startswith('mag_')


def bake(export_path):
    els = [e for e in load_export(export_path) if not is_reticle(e['name'])]   # reticle uses the fixed swatch
    man = json.loads((CACHE / 'manifest.json').read_text())
    views = {k: View(k, man) for k in man['views']}
    faces = []      # (elem, fn, img)
    hidden = []
    for e in els:
        mag = is_magazine(e['name'])
        others = [o for o in els if o is not e and is_magazine(o['name']) == mag]
        for fn in FACE_AXES:
            if hidden_face(e, fn, others):
                hidden.append((e['name'], fn)); continue
            img, valid = bake_face(e, fn, views, others)
            fb = (78, 78, 80, 255)
            inpaint(img, valid, fb)
            img = despeckle(img, SPECIAL_PIX.get((e['name'], fn)))
            apply_edges(img, edge_flags(e, fn, others), fn)
            faces.append((e['name'], fn, img))
    pad = 1
    rects = [((n, f), img.size[0] + 2 * pad, img.size[1] + 2 * pad) for n, f, img in faces]
    rects.append((('_hidden', '_'), 4, 4))
    pos, used = pack(rects, ATLAS_SIZE)
    if used > ATLAS_SIZE:
        raise SystemExit(f'atlas overflow: {used}px > {ATLAS_SIZE}; lower T')
    atlas = Image.new('RGBA', (ATLAS_SIZE, ATLAS_SIZE), (0, 0, 0, 0))
    layout = {}
    k = 16.0 / ATLAS_SIZE
    for n, f, img in faces:
        x, y = pos[(n, f)]
        w, h = img.size
        # gutter: edge-extend 1 texel
        g = img.resize((w + 2, h + 2), Image.NEAREST)
        g.paste(img, (1, 1))
        for i in range(w + 2):
            g.putpixel((i, 0), img.getpixel((min(max(i - 1, 0), w - 1), 0)))
            g.putpixel((i, h + 1), img.getpixel((min(max(i - 1, 0), w - 1), h - 1)))
        for j in range(h + 2):
            g.putpixel((0, j), img.getpixel((0, min(max(j - 1, 0), h - 1))))
            g.putpixel((w + 1, j), img.getpixel((w - 1, min(max(j - 1, 0), h - 1))))
        atlas.paste(g, (x, y))
        layout.setdefault(n, {})[f] = [round((x + pad) * k, 6), round((y + pad) * k, 6),
                                       round((x + pad + w) * k, 6), round((y + pad + h) * k, 6)]
    hx, hy = pos[('_hidden', '_')]
    atlas.paste(Image.new('RGBA', (4, 4), (40, 40, 42, 255)), (hx, hy))
    huv = [round((hx + 1) * k, 6), round((hy + 1) * k, 6), round((hx + 3) * k, 6), round((hy + 3) * k, 6)]
    for n, f in hidden:
        layout.setdefault(n, {})[f] = huv
    ATLAS.parent.mkdir(parents=True, exist_ok=True)
    if used > RETICLE_SWATCH[1] - 1:
        raise SystemExit(f'atlas rows {used} reach the reticle swatch')
    post_bake(atlas, layout)
    atlas.save(ATLAS, optimize=True)
    UVLAYOUT.write_text(json.dumps({'texture_size': [ATLAS_SIZE, ATLAS_SIZE], 'texels_per_px': T,
                                    'atlas_rows_used': used, 'hidden_faces': len(hidden),
                                    'faces': layout}, indent=1, sort_keys=True))
    hud_icon(els)
    print(f'bake: {len(els)} elements, {len(faces)} painted faces, {len(hidden)} hidden faces, atlas rows {used}/{ATLAS_SIZE}')


def post_bake(atlas, layout):
    """Clear the holo glass faces (alpha 0, gutter included) and paint the opaque reticle swatch; idempotent."""
    k = ATLAS_SIZE / 16.0
    for fn in ('north', 'south'):
        x0, y0, x1, y1 = (round(v * k) for v in layout['sight_glass'][fn])
        for y in range(min(y0, y1) - 1, max(y0, y1) + 1):
            for x in range(min(x0, x1) - 1, max(x0, x1) + 1):
                atlas.putpixel((x, y), (0, 0, 0, 0))
    x0, y0, x1, y1 = RETICLE_SWATCH
    for y in range(y0 - 1, y1 + 1):
        for x in range(x0 - 1, x1 + 1):
            atlas.putpixel((x, y), (0, 0, 0, 0))
    atlas.paste(Image.new('RGBA', (x1 - x0, y1 - y0), RETICLE_RGBA), (x0, y0))


def reticle():
    lay = json.loads(UVLAYOUT.read_text())
    if lay['atlas_rows_used'] > RETICLE_SWATCH[1] - 1:
        raise SystemExit('atlas rows reach the reticle swatch')
    atlas = Image.open(ATLAS).convert('RGBA')
    post_bake(atlas, lay['faces'])
    atlas.save(ATLAS, optimize=True)
    print('reticle: glass cleared, swatch', RETICLE_SWATCH)
    for e in reticle_elements():
        print(' ', e['name'], e['from'], e['to'], 'uv', e['faces']['north']['uv'])

# ---------------------------------------------------------------- HUD icon
def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def hud_icon(els):
    """160x64 flat white side silhouette, muzzle left, soft alpha (multiples of 4), inside x4..155 y5..57 like the base icons."""
    polys = []
    for e in els:
        if e['name'] == 'sight_glass' or is_reticle(e['name']):
            continue
        f, t = e['from'], e['to']; rot = rot_of(e)
        pts = [rotate((x, y, z), rot) for x in (f[0], t[0]) for y in (f[1], t[1]) for z in (f[2], t[2])]
        polys.append(hull([(p[2], p[1]) for p in pts]))
    zs = [p[0] for pl in polys for p in pl]; ys = [p[1] for pl in polys for p in pl]
    z0, z1, y0, y1 = min(zs), max(zs), min(ys), max(ys)
    bw, bh = 152, 53
    sc = min(bw / (z1 - z0), bh / (y1 - y0))
    ox = 4 + (bw - (z1 - z0) * sc) / 2; oy = 5 + (bh - (y1 - y0) * sc) / 2
    up = 8
    m = Image.new('L', (160 * up, 64 * up), 0); d = ImageDraw.Draw(m)
    for pl in polys:
        d.polygon([((ox + (z - z0) * sc) * up, (oy + (y1 - y) * sc) * up) for z, y in pl], fill=255)
    a = m.resize((160, 64), Image.BOX)
    a = a.point(lambda v: min(252, (v + 2) // 4 * 4) if v < 250 else 255)
    icon = Image.new('RGBA', (160, 64), (255, 255, 255, 0))
    icon.putalpha(a)
    HUD.parent.mkdir(parents=True, exist_ok=True)
    icon.save(HUD, optimize=True)

# ---------------------------------------------------------------- convert
def convert(export_path):
    d = json.loads(Path(export_path).read_text())
    lay = json.loads(UVLAYOUT.read_text())
    parts = {'body': [], 'magazine': []}
    want_ret = {e['name']: e for e in reticle_elements()}
    reticles = []
    for e in d['elements']:
        if is_reticle(e['name']):
            # Authored in Blockbench from reticle_elements(); must match the spec (north/south only, swatch UV).
            w = want_ret.pop(e['name'], None)
            if w is None:
                raise SystemExit(f'unexpected reticle element {e["name"]}')
            if any(abs(a - b) > 1e-4 for a, b in zip(e['from'] + e['to'], w['from'] + w['to'])):
                raise SystemExit(f'{e["name"]} {e["from"]}..{e["to"]} != spec {w["from"]}..{w["to"]}')
            got = {fn: f for fn, f in e['faces'].items() if f.get('texture') is not None}
            if set(got) != {'north', 'south'} or any(abs(a - b) > 1e-4 for f in got.values() for a, b in zip(f['uv'], RETICLE_UV)):
                raise SystemExit(f'{e["name"]} faces {got} != north/south swatch {RETICLE_UV}')
            reticles.append(w)      # kept last in body (r1 element order)
            continue
        out = {'name': e['name'], 'from': [round(v, 6) for v in e['from']], 'to': [round(v, 6) for v in e['to']]}
        for v in out['from'] + out['to']:
            if not -16 <= v <= 32:
                raise SystemExit(f'{e["name"]} outside -16..32')
        r = rot_of(e)
        if r:
            rr = {'origin': [round(v, 6) for v in r[0]], 'x': 0, 'y': 0, 'z': 0}
            for ax, ang in r[1]:
                rr[ax] = round(ang, 6)
            out['rotation'] = rr
        faces = {}
        for fn in ('north', 'east', 'south', 'west', 'up', 'down'):
            fc = e['faces'].get(fn)
            want = lay['faces'][e['name']][fn]
            if not fc or 'uv' not in fc:
                raise SystemExit(f'{e["name"]}.{fn} has no uv')
            if any(abs(a - b) > 1e-4 for a, b in zip(fc['uv'], want)):
                raise SystemExit(f'{e["name"]}.{fn} uv {fc["uv"]} != layout {want}')
            faces[fn] = {'uv': [round(v, 6) for v in fc['uv']], 'texture': '#0'}
            if fc.get('rotation'):
                faces[fn]['rotation'] = fc['rotation']
        out['faces'] = faces
        parts['magazine' if is_magazine(e['name']) else 'body'].append(out)
    if want_ret:
        raise SystemExit(f'Blockbench export lacks reticle elements {sorted(want_ret)}')
    parts['body'].extend(sorted(reticles, key=lambda e: list(RETICLE_BOXES).index(e['name'])))
    doc = {'texture_size': lay['texture_size'], 'parts': parts, 'no_overlay': True}   # drop the white W148 dot
    text = json.dumps(doc, separators=(',', ':'))     # parts.json and the skin json are byte-identical
    PARTS.write_text(text)
    SKIN_JSON.parent.mkdir(parents=True, exist_ok=True)
    SKIN_JSON.write_text(text)
    print(f'convert: body {len(parts["body"])} + magazine {len(parts["magazine"])} elements')
    manifest(export_path, parts)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def manifest(export_path, parts):
    m = {'batch': 'W302', 'skin': SKIN, 'layout_contract': 'destiny:weapon_reload_w208_gnawing_hunger (+ weapon_sight_w151)',
         'elements': {k: len(v) for k, v in parts.items()}, 'element_total': sum(len(v) for v in parts.values()),
         'texels_per_px': T, 'atlas': [ATLAS_SIZE, ATLAS_SIZE],
         'sources_sha256': {f: sha(SRC_DIR / f) for f in SRC_FILES if (SRC_DIR / f).exists()},
         'projection_cache_sha256': ({p.name: sha(p) for p in sorted(CACHE.iterdir()) if p.is_file()} if CACHE.is_dir()
                                     else json.loads((ART / 'manifest.json').read_text()).get('projection_cache_sha256')),
         'reticle': {'elements': [e['name'] for e in reticle_elements()], 'swatch_px': list(RETICLE_SWATCH),
                     'rgba': list(RETICLE_RGBA), 'uv': RETICLE_UV,
                     'boxes': {k: [list(f), list(t)] for k, (f, t) in RETICLE_BOXES.items()},
                     'shade': False, 'light_emission': 15, 'no_overlay': True, 'variant': 'master r1 (user-selected)'},
         'blockbench_export': Path(export_path).name, 'blockbench_export_sha256': sha(export_path),
         'outputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (ATLAS, HUD, PARTS, SKIN_JSON) if p.exists()}}
    (ART / 'manifest.json').write_text(json.dumps(m, indent=1, sort_keys=True) + '\n')


def extract():
    tool = ART / 'tools/extract_projection_cache.py'
    subprocess.run([BLENDER, '-b', str(SRC_DIR / SRC_FILES[0]), '--python', str(tool), '--', str(CACHE), '800'], check=True)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == 'extract':
        extract()
    elif cmd == 'bake':
        bake(sys.argv[2])
    elif cmd == 'reticle':
        reticle()
    elif cmd == 'convert':
        convert(sys.argv[2])
    else:
        raise SystemExit(__doc__)
