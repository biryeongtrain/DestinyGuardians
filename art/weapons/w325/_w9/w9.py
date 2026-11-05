"""W325 worker-9 shared helpers: authored solids + affine rip mapping + quick 2D overlay previews (no Blender).

Imported by art/weapons/w325/<id>/design.py (deterministic). Preview: python3 w9.py preview <id> [base_json ...]
"""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/art/w325'))


def box(name, lo, hi, rot=None, **kw):
    e = {'name': name, 'from': [float(v) for v in lo], 'to': [float(v) for v in hi]}
    if rot:
        ax, ang, org = rot
        e['rotation'] = {'origin': list(org), 'x': 0, 'y': 0, 'z': 0}; e['rotation'][ax] = ang
    e.update(kw)
    return e


def bar(name, x0, x1, p0, p1, thick, side='center', ext=(0.0, 0.0)):
    """Box spanning x0..x1 along the (z,y) segment p0->p1 (thickness `thick`, centred on / below / above the line),
    rotated about x through its own centre. Kept within +-45 deg by the caller."""
    if p1[0] < p0[0]: p0, p1 = p1, p0; ext = (ext[1], ext[0])
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dz, dy); ux, uy = dz / L, dy / L
    a = math.degrees(math.atan2(-uy, ux))
    off = {'center': 0.0, 'below': -thick / 2, 'above': thick / 2}[side]
    mz = (p0[0] + p1[0]) / 2 + ux * (ext[1] - ext[0]) / 2 - uy * off
    my = (p0[1] + p1[1]) / 2 + uy * (ext[1] - ext[0]) / 2 + ux * off
    half = (L + ext[0] + ext[1]) / 2
    return box(name, (x0, my - thick / 2, mz - half), (x1, my + thick / 2, mz + half),
               ('x', round(a, 4), [round((x0 + x1) / 2, 5), round(my, 5), round(mz, 5)]))


class RipMap:
    """Affine model px -> rip world (metres). Rip: barrel along world Y, up world Z.
    muzzle: '-y' or '+y' rip direction of the muzzle. anchors: model (y,z) point that equals rip (Z,Y) point."""
    def __init__(self, scale, model_anchor, rip_anchor, muzzle='-y', xc=0.0, sx=None):
        self.S = scale; self.ma = model_anchor; self.ra = rip_anchor; self.sg = 1 if muzzle == '-y' else -1
        self.xc = xc; self.sx = sx if sx is not None else scale

    def __call__(self, p):
        x, y, z = p
        wx = self.xc - self.sg * (x - 8) / self.sx
        wy = self.ra[1] + self.sg * (z - self.ma[1]) / self.S
        wz = self.ra[0] + (y - self.ma[0]) / self.S
        return (wx, wy, wz)


# ---------------------------------------------------------------------------------------------- preview
def _rot(e):
    import kit
    return kit.rot_of(e)


def corners(e):
    import kit
    f, t = e['from'], e['to']; r = kit.rot_of(e)
    return [kit.rotate((x, y, z), r) for x in (f[0], t[0]) for y in (f[1], t[1]) for z in (f[2], t[2])]


def preview(wid, base_jsons=(), out=None, K=50, mapfn=None, zr=None):
    import kit
    from PIL import Image, ImageDraw
    D = kit.load_design(wid); els = D.elements()
    cache = kit.art(wid) / 'proj_cache'; man = json.loads((cache / 'manifest.json').read_text())
    bases = []
    for b in base_jsons:
        bases += json.loads(Path(b).read_text()).get('elements', [])
    allp = [c for e in els + bases for c in corners(e)]
    import numpy as np
    f0 = np.array(D.model2world(els[0]['name'], (0, 0, 0)))
    A = np.array([np.array(D.model2world(els[0]['name'], tuple(1.0 if j == i else 0.0 for j in range(3)))) - f0 for i in range(3)]).T
    Ai = np.linalg.inv(A)
    for cx in (man['lo'][0], man['hi'][0]):
        for cy in (man['lo'][1], man['hi'][1]):
            for cz in (man['lo'][2], man['hi'][2]):
                allp.append(tuple(Ai @ (np.array((cx, cy, cz)) - f0)))
    z0 = min(p[2] for p in allp) - 1; z1 = max(p[2] for p in allp) + 1
    y0 = min(p[1] for p in allp) - 1; y1 = max(p[1] for p in allp) + 1
    x0 = min(p[0] for p in allp) - .5; x1 = max(p[0] for p in allp) + .5
    if zr: z0, z1 = zr
    W = int((z1 - z0) * K); H = int((y1 - y0) * K); HT = int((x1 - x0) * K)
    m2w = lambda p: D.model2world(els[0]['name'], p)
    panels = []
    for vname, axes in (('nx', 'side'), ('pz', 'top')):
        v = kit.View(cache, vname, man); src = Image.open(cache / f'{vname}_albedo.png').convert('RGBA')
        if axes == 'side':
            f = lambda u, w: m2w((8, y1 - w / K, z0 + u / K)); size = (W, H)
        else:
            f = lambda u, w: m2w((x0 + w / K, 10, z0 + u / K)); size = (W, HT)
        o = v.project(f(0, 0)); a = v.project(f(1, 0)); b = v.project(f(0, 1))
        coef = (a[0] - o[0], b[0] - o[0], o[0], a[1] - o[1], b[1] - o[1], o[1])
        bg = Image.new('RGBA', size, (60, 60, 64, 255))
        im = src.transform(size, Image.AFFINE, coef, Image.BILINEAR)
        bg.alpha_composite(im)
        gl = Image.new('RGBA', size, (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
        for zz in range(math.ceil(z0 * 2), int(z1 * 2) + 1):
            gd.line([((zz / 2 - z0) * K, 0), ((zz / 2 - z0) * K, size[1])], fill=(255, 255, 255, 70 if zz % 2 == 0 else 30))
        lo_, hi_ = (y0, y1) if axes == 'side' else (x0, x1)
        for yy in range(math.ceil(lo_ * 2), int(hi_ * 2) + 1):
            yp = (y1 - yy / 2) * K if axes == 'side' else (yy / 2 - x0) * K
            gd.line([(0, yp), (size[0], yp)], fill=(255, 255, 255, 70 if yy % 2 == 0 else 30))
        bg.alpha_composite(gl); d = ImageDraw.Draw(bg)
        def pt(p):
            return ((p[2] - z0) * K, (y1 - p[1]) * K) if axes == 'side' else ((p[2] - z0) * K, (p[0] - x0) * K)
        for col, group in (((0, 255, 255, 255), bases), ((255, 230, 0, 255), els)):
            for e in group:
                h = kit.hull([tuple(round(c, 4) for c in pt(p)) for p in corners(e)])
                if len(h) > 2: d.polygon(h, outline=col)
        for zz in range(math.ceil(z0), int(z1) + 1):
            d.line([((zz - z0) * K, 0), ((zz - z0) * K, 6)], fill=(255, 255, 255, 255))
            if zz % 2 == 0: d.text(((zz - z0) * K + 2, 6), str(zz), fill=(255, 255, 255, 255))
        if axes == 'side':
            for yy in range(math.ceil(y0), int(y1) + 1):
                d.line([(0, (y1 - yy) * K), (6, (y1 - yy) * K)], fill=(255, 255, 255, 255)); d.text((8, (y1 - yy) * K - 6), str(yy), fill=(255, 255, 255, 255))
        panels.append(bg)
    out = out or (kit.art(wid) / 'proj_cache' / 'w9_preview.png')
    full = Image.new('RGBA', (W, H + HT + 10), (0, 0, 0, 255)); full.paste(panels[0], (0, 0)); full.paste(panels[1], (0, H + 10))
    full.save(out); print(out, len(els), 'elements')


def measure(wid, step=0.5, vside='nx', vtop='pz'):
    """Print, per model z, the alpha runs of the rip side view (model y) and top view (model x)."""
    import kit
    from PIL import Image
    D = kit.load_design(wid); n = D.elements()[0]['name']
    cache = kit.art(wid) / 'proj_cache'; man = json.loads((cache / 'manifest.json').read_text())
    res = {}
    for vn in (vside, vtop):
        v = kit.View(cache, vn, man); a = Image.open(cache / f'{vn}_albedo.png').convert('RGBA').getchannel('A').load()
        res[vn] = (v, a)
    import numpy as np
    f0 = np.array(D.model2world(n, (0, 0, 0)))
    A = np.array([np.array(D.model2world(n, tuple(1.0 if j == i else 0.0 for j in range(3)))) - f0 for i in range(3)]).T
    Ai = np.linalg.inv(A)
    zs = [(Ai @ (np.array(c) - f0))[2] for c in ((0, man['lo'][1], 0), (0, man['hi'][1], 0))]
    z = math.floor(min(zs) * 2) / 2
    while z <= max(zs):
        out = []
        for vn, rng, fn in ((vside, (1, 16), lambda q: (8, q, z)), (vtop, (5, 11), lambda q: (q, 11, z))):
            v, a = res[vn]; runs = []; cur = None; q = rng[0]
            while q <= rng[1]:
                x, y = v.project(D.model2world(n, fn(q)))
                on = 0 <= int(x) < v.W and 0 <= int(y) < v.H and a[int(x), int(y)] > 128
                if on and cur is None: cur = q
                if not on and cur is not None: runs.append((round(cur, 2), round(q - .05, 2))); cur = None
                q += .05
            if cur is not None: runs.append((round(cur, 2), round(q, 2)))
            out.append(runs)
        print(f'z {z:6.1f}  y {out[0]}   x {out[1]}')
        z += step


def post(name, x0, x1, top, bottom, thick, ext=(0.0, 0.0)):
    """Near-vertical box (long axis y) from `top` (z,y) to `bottom` (z,y), thickness along its own z,
    rotated about x through its centre (grips, magazines, raked posts)."""
    dz, dy = top[0] - bottom[0], top[1] - bottom[1]; L = math.hypot(dz, dy); uz, uy = dz / L, dy / L
    a = math.degrees(math.asin(uz))
    mz = (top[0] + bottom[0]) / 2 + uz * (ext[0] - ext[1]) / 2; my = (top[1] + bottom[1]) / 2 + uy * (ext[0] - ext[1]) / 2
    half = (L + ext[0] + ext[1]) / 2
    return box(name, (x0, my - half, mz - thick / 2), (x1, my + half, mz + thick / 2),
               ('x', round(a, 4), [round((x0 + x1) / 2, 5), round(my, 5), round(mz, 5)]))


def disc(cx, cy, r, s_t_to_xy):
    """helper for specials: returns True if face point lies inside circle."""
    x, y = s_t_to_xy
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def compare(wid):
    """<id>_compare.png: rip side view (proj_cache nx_albedo) above the kit west render, same width."""
    import kit
    from PIL import Image, ImageDraw
    rip = Image.open(kit.art(wid) / 'proj_cache/nx_albedo.png').convert('RGBA')
    ren = Image.open(kit.art(wid) / f'review/{wid}_west.png').convert('RGBA')
    bb = ren.convert('RGB').point(lambda v: 0 if abs(v - 115) < 6 else 255).getbbox()
    a = ren.getchannel('R').point(lambda v: 255).getbbox()
    W = 1100
    # crop render to non-background
    px = ren.load(); bg = px[2, 2]; xs = []; ys = []
    for x in range(0, ren.size[0], 2):
        for y in range(0, ren.size[1], 2):
            p = px[x, y]
            if max(abs(p[i] - bg[i]) for i in range(3)) > 12: xs.append(x); ys.append(y)
    ren = ren.crop((min(xs) - 4, min(ys) - 4, max(xs) + 4, max(ys) + 4))
    rip = rip.resize((W, int(rip.size[1] * W / rip.size[0])), Image.LANCZOS)
    ren = ren.resize((W, int(ren.size[1] * W / ren.size[0])), Image.LANCZOS)
    out = Image.new('RGBA', (W, rip.size[1] + ren.size[1] + 50), (150, 152, 156, 255))
    out.alpha_composite(rip, (0, 20)); out.alpha_composite(ren, (0, rip.size[1] + 45))
    d = ImageDraw.Draw(out); d.text((6, 4), f'{wid}: rip (nx albedo)', fill=(0, 0, 0, 255))
    d.text((6, rip.size[1] + 28), 'W325 model (kit render west)', fill=(0, 0, 0, 255))
    p = kit.art(wid) / f'review/{wid}_compare.png'; out.convert('RGB').save(p); print(p)


def face_xy(e, fn, s, t):
    """Model point of face sample (s,t) (kit face frame, unrotated element)."""
    import kit
    o, u, v = kit.face_frame(e, fn)
    return tuple(o[i] + u[i] * s + v[i] * t for i in range(3))


def lens(e, fn, s, t, want_fn, centre, r, rim=0.08, glass=(28, 44, 58), rimc=(18, 18, 20)):
    """Round lens/bore special on face want_fn, centre (a,b) in that face's in-plane model coords."""
    if fn != want_fn: return None
    p = face_xy(e, fn, s, t)
    if fn in ('north', 'south'): a, b = p[0], p[1]
    elif fn in ('east', 'west'): a, b = p[2], p[1]
    else: a, b = p[0], p[2]
    d = math.hypot(a - centre[0], b - centre[1])
    if d < r - rim:
        k = 1 - 0.35 * d / r
        return tuple(int(c * k) for c in glass) + (255,)
    if d < r: return rimc + (255,)
    return None


def base_body_src(wid):
    import kit
    base = kit.reg(wid)['base']; md = kit.ASSETS / 'models'
    cands = [md / f'weapon_sight_w151/{base}_body.json'] + sorted(md.glob(f'weapon_reload_w*_{base}/{base}_body.json')) \
        + sorted(md.glob(f'weapon/*/{base}.json'))
    return next(p for p in cands if p.exists() and json.loads(p.read_text()).get('elements'))


def top_profile(els, z0, z1, band=(6.6, 9.4), skip_overlay=False):
    best = None
    for e in els:
        c = corners(e)
        if max(p[2] for p in c) < z0 or min(p[2] for p in c) > z1: continue
        if max(p[0] for p in c) < band[0] or min(p[0] for p in c) > band[1]: continue
        if skip_overlay and any(f.get('texture') not in ('#0', None) for f in e.get('faces', {}).values()) and 'aim' in e.get('name', ''): continue
        y = max(p[1] for p in c); best = y if best is None or y > best else best
    return best


def profile(wid, use_design=True):
    """Per 0.25 z slice (whole length): base top vs skin top (design elements), '!!' where skin > base + 0.15."""
    import kit
    src = base_body_src(wid); be = json.loads(src.read_text())['elements']
    els = kit.load_design(wid).elements() if use_design else json.loads(kit.skin_path(wid).read_text())['parts']['body']
    mag = getattr(kit.load_design(wid), 'is_magazine', lambda n: n.startswith('mag_'))
    els = [e for e in els if not mag(e['name'])]
    zs = [p[2] for e in be for p in corners(e)]; zmin, zmax = min(zs), max(zs); start = zmin + (zmax - zmin) / 3
    z = math.floor(zmin * 4) / 4; print(src.name, 'check from z', round(start, 2))
    while z < zmax:
        b = top_profile(be, z, z + .25, skip_overlay=True); k = top_profile(els, z, z + .25)
        flag = '!!' if z >= start and k is not None and (b is None or k > b + .15) else ''
        who = ''
        if flag:
            who = ','.join(e['name'] for e in els if top_profile([e], z, z + .25) is not None and top_profile([e], z, z + .25) > (b or 0) + .15)
        print(f'z {z:6.2f} base {b if b is None else round(b, 2)!s:>6} skin {k if k is None else round(k, 2)!s:>6} {flag} {who}')
        z += .25


def palette(wid, k=8, views=('nx', 'px', 'pz')):
    """Deterministic k-colour palette of the rip albedo (median cut over the opaque pixels of the side/top views)."""
    import kit
    from PIL import Image
    cache = kit.art(wid) / 'proj_cache'; px = []
    for v in views:
        im = Image.open(cache / f'{v}_albedo.png').convert('RGBA')
        px += [p[:3] for p in im.getdata() if p[3] > 200]
    strip = Image.new('RGB', (len(px), 1)); strip.putdata(px)
    q = strip.quantize(colors=k, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[:3 * k]
    return [tuple(pal[i:i + 3]) for i in range(0, 3 * k, 3)]


def snapper(pal, keep=0.0):
    """grade() factory: snap a projected colour to the nearest palette entry (kills smear/bleed into flat panels);
    keep (0..1) mixes back some of the original value for subtle wear."""
    import kit
    def g(rgb):
        best = min(pal, key=lambda c: (c[0] - rgb[0]) ** 2 * .3 + (c[1] - rgb[1]) ** 2 * .59 + (c[2] - rgb[2]) ** 2 * .11)
        mix = tuple(best[i] * (1 - keep) + rgb[i] * keep for i in range(3))
        return kit.default_grade(mix)
    return g


def chamfer_box(name, lo, hi, r, top=True, bottom=False, rt=None, rb=None):
    """Box with 45-degree chamfers on its long top (and/or bottom) x edges: core + inset cap(s) + 45-deg z-rotated
    square slabs whose outer diagonal is the chamfer face. Never rises above hi[1] / below lo[1]."""
    rt = r if rt is None else rt; rb = r if rb is None else rb
    x0, y0, z0 = lo; x1, y1, z1 = hi
    out = []; cy0 = y0 + (rb if bottom else 0); cy1 = y1 - (rt if top else 0)
    out.append(box(name, (x0, cy0, z0), (x1, cy1, z1)))
    for on, rr, yy, sg, tag in ((top, rt, y1, -1, 't'), (bottom, rb, y0, 1, 'b')):
        if not on: continue
        if tag == 't': out.append(box(f'{name}_cap{tag}', (x0 + rr, cy1, z0), (x1 - rr, y1, z1)))
        else: out.append(box(f'{name}_cap{tag}', (x0 + rr, y0, z0), (x1 - rr, cy0, z1)))
        s = rr * math.sqrt(2) / 2
        for side, cx in (('l', x0 + rr), ('r', x1 - rr)):
            cy = yy + sg * rr
            out.append(box(f'{name}_ch{tag}{side}', (cx - s, cy - s, z0), (cx + s, cy + s, z1), ('z', 45, [round(cx, 5), round(cy, 5), 0])))
    return out


def segbar(name, p0, p1, thick, n, x0, x1, side='below'):
    """Sloped bar split into n pieces (keeps each piece's bounding top close to the line for the ADS check)."""
    out = []
    for i in range(n):
        a = (p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n)
        b = (p0[0] + (p1[0] - p0[0]) * (i + 1) / n, p0[1] + (p1[1] - p0[1]) * (i + 1) / n)
        out.append(bar(f'{name}_{i}', x0, x1, a, b, thick, side, ext=(0.02 if i else 0, 0.02)))
    return out


def zwarp(pairs):
    """Piecewise-linear z map (model z -> rip-frame z) from sorted (model_z, rip_z) pairs; clamps/extrapolates ends."""
    def f(z):
        for (a0, b0), (a1, b1) in zip(pairs, pairs[1:]):
            if z <= a1 or (a1, b1) == pairs[-1]:
                return b0 + (z - a0) * (b1 - b0) / (a1 - a0)
        return z
    return f


# ------------------------------------------------------------------------------------------------ pixel-style paint
def model_pt(e, fn, s, t):
    """Model point of a face sample, element rotation applied."""
    import kit
    return kit.face_point(e, fn, s, t)


def _hash(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 144665) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(p, scale, seed=0):
    """Smooth 3D value noise in model px (deterministic): large blobs for painted camo."""
    x, y, z = p[0] / scale, p[1] / scale, p[2] / scale
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z); fx, fy, fz = x - ix, y - iy, z - iz
    sm = lambda u: u * u * (3 - 2 * u); fx, fy, fz = sm(fx), sm(fy), sm(fz)
    acc = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                acc += w * _hash(ix + dx, iy + dy, iz + dz, seed)
    return acc


def camo(e, fn, s, t, base, blobs, scale=1.6, seed=1, quant=0.25):
    """Painted camo: base colour + 1-3 blob colours from thresholded value noise, snapped to a quant px grid so blob
    edges are blocky (Minecraft texels) and continuous across faces. blobs = [(threshold, rgb), ...] ascending."""
    p = model_pt(e, fn, s, t); p = tuple(round(c / quant) * quant for c in p)
    v = vnoise(p, scale, seed) * .7 + vnoise(p, scale * .45, seed + 7) * .3
    col = base
    for th, c in blobs:
        if v > th: col = c
    return tuple(col[:3]) + (255,)


def flat(rgb): return tuple(rgb[:3]) + (255,)


def stripe_rows(t, rows, n_px, col):
    """Dark 1-texel slot lines: rows = list of t-centres (0..1) on a face of n_px texels tall."""
    for r in rows:
        if abs(t - r) < 0.5 / max(n_px, 1): return flat(col)
    return None


def material(name, mats):
    """First matching (prefix tuple, rgb) in mats -> rgb or None."""
    for pre, rgb in mats:
        if name.startswith(pre): return rgb
    return None


def chamfer_box(name, lo, hi, r, top=True, bottom=False, rt=None, rb=None, segs=1, gap=0.1):
    """r3 (Dead Man Walking style, overrides the 45-deg version above): machined block from unrotated parts — a core
    plus a separate inset top (and/or bottom) plate one step (r) narrower, i.e. a 1-step chamfer on the long edges.
    segs>1 splits the plate(s) along z into segments separated by `gap` grooves, so long slabs read as panels.
    Never rises above hi[1] / below lo[1]."""
    rt = r if rt is None else rt; rb = r if rb is None else rb
    x0, y0, z0 = lo; x1, y1, z1 = hi
    cy0 = y0 + (rb if bottom and rb > 0 else 0); cy1 = y1 - (rt if top and rt > 0 else 0)
    out = [box(name, (x0, cy0, z0), (x1, cy1, z1))]
    L = (z1 - z0 - gap * (segs - 1)) / segs
    for on, rr, tag in ((top, rt, 't'), (bottom, rb, 'b')):
        if not on or rr <= 0: continue
        for k in range(segs):
            za = z0 + k * (L + gap); zb = za + L
            nm = f'{name}_cap{tag}' + (f'{k}' if segs > 1 else '')
            if tag == 't': out.append(box(nm, (x0 + rr, cy1, za), (x1 - rr, y1, zb)))
            else: out.append(box(nm, (x0 + rr, y0, za), (x1 - rr, cy0, zb)))
    return out


def edge_strips(name, lo, hi, r, z_ends=True):
    """End caps: thin rims one step proud on the x/y outline at both z ends of a block (DMW end-cap look)."""
    x0, y0, z0 = lo; x1, y1, z1 = hi; out = []
    for tag, (za, zb) in (('f', (z0, z0 + r)), ('r', (z1 - r, z1))):
        out.append(box(f'{name}_rim{tag}', (x0 - r * .5, y0 - r * .5, za), (x1 + r * .5, y1 - r, zb)))
    return out


def lint(wid):
    """Chattering-Bone check: small-angle rotations, coplanar overlapping faces (z-fight) between unrotated boxes."""
    import kit
    els = kit.load_design(wid).elements()
    small = []
    for e in els:
        r = e.get('rotation')
        if r:
            ang = max(abs(r.get(a, 0)) for a in 'xyz')
            if 0 < ang < 20: small.append((e['name'], round(ang, 1)))
    zf = [(a['name'], b['name'], 'xyz'[ax], 'hi' if hi else 'lo') for a, b, ax, hi in coplanar_pairs(els)]
    rot = [e for e in els if e.get('rotation')]
    def ang(e): r = e['rotation']; return max((r.get(a, 0) for a in 'xyz'), key=abs)
    def bb(e):
        c = corners(e); return [min(p[i] for p in c) for i in range(3)], [max(p[i] for p in c) for i in range(3)]
    near = []
    for i, a in enumerate(rot):
        for b in rot[i + 1:]:
            d = abs(ang(a) - ang(b))
            if 0.3 < d < 8:
                (la, ha), (lb, hb) = bb(a), bb(b)
                if all(min(ha[k], hb[k]) - max(la[k], lb[k]) > 0.02 for k in range(3)): near.append((a['name'], b['name'], round(d, 1)))
    print(wid, 'small-rot', len(small), small)
    print(wid, 'near-parallel overlapping rotated', len(near), near)
    print(wid, 'coplanar-same-dir', len(zf), zf[:40])


_FN = {(0, False): 'west', (0, True): 'east', (1, False): 'down', (1, True): 'up', (2, False): 'north', (2, True): 'south'}


def _face_visible(e, ax, hi, others):
    import kit
    fn = _FN[(ax, hi)]
    for s in (.2, .5, .8):
        for t in (.2, .5, .8):
            p = kit.face_point(e, fn, s, t, push=0.02)
            if not any(kit.inside(o, p) for o in others): return True
    return False


def coplanar_pairs(els, is_mag=lambda n: n.startswith('mag_')):
    out = []
    ur = [e for e in els if not e.get('rotation')]
    for i, a in enumerate(ur):
        for b in ur[i + 1:]:
            if is_mag(a['name']) != is_mag(b['name']): continue
            for ax in range(3):
                for hi in (False, True):
                    sa = a['to' if hi else 'from'][ax]; sb = b['to' if hi else 'from'][ax]
                    if abs(sa - sb) > 1e-4: continue
                    o = [k for k in range(3) if k != ax]
                    if not all(min(a['to'][k], b['to'][k]) - max(a['from'][k], b['from'][k]) > 0.02 for k in o): continue
                    rest = [x for x in els if x is not a and x is not b]
                    if _face_visible(a, ax, hi, rest + [b]) or _face_visible(b, ax, hi, rest + [a]):
                        out.append((a, b, ax, hi))
    return out


def tidy(els, d=0.03, is_mag=lambda n: n.startswith('mag_')):
    """Resolve visible coplanar same-direction overlaps (z-fighting): the smaller element's face is recessed by d,
    so detail inlays read as clean recessed panels instead of flickering co-planar faces."""
    vol = lambda e: abs((e['to'][0] - e['from'][0]) * (e['to'][1] - e['from'][1]) * (e['to'][2] - e['from'][2]))
    for _ in range(3):
        pairs = coplanar_pairs(els, is_mag)
        if not pairs: break
        for a, b, ax, hi in pairs:
            s = a if vol(a) <= vol(b) else b
            thick = s['to'][ax] - s['from'][ax]
            dd = min(d, thick * 0.4)
            if hi: s['to'][ax] = round(s['to'][ax] - dd, 5)
            else: s['from'][ax] = round(s['from'][ax] + dd, 5)
    return els


if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        a = [x for x in sys.argv[3:] if not x.startswith('--')]; o = [x for x in sys.argv[3:] if x.startswith('--')]
        kw = {}
        for x in o:
            k, v = x[2:].split('=')
            if k == 'zr': kw['zr'] = tuple(float(t) for t in v.split(','))
            if k == 'K': kw['K'] = int(v)
            if k == 'out': kw['out'] = v
        preview(sys.argv[2], a, **kw)


if __name__ == '__main__' and sys.argv[1] == 'measure':
    measure(sys.argv[2])


if __name__ == '__main__' and sys.argv[1] == 'compare':
    compare(sys.argv[2])


if __name__ == '__main__' and sys.argv[1] == 'profile':
    profile(sys.argv[2])


if __name__ == '__main__' and sys.argv[1] == 'lint':
    lint(sys.argv[2])

