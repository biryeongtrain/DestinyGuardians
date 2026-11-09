#!/usr/bin/env python3
"""W325 Red War white/green/blue weapons: shared production kit (generalised W302 Khvostov/Stubborn Oak method).

Each weapon is an authored low-element model (design.py) laid over the catalog row with the same D2 frame (the skin
"base"), textured by projecting the read-only rip from six calibrated orthographic views.  Registry: art/weapons/w325/
registry.json (id, Drive file id, base catalog id, tier).  Python 3 + Pillow; Blender for extract/render.

  python3 scripts/art/w325/kit.py fetch   ID      download + unpack the Drive rip to /tmp/w325-rips/ID (read-only source)
  python3 scripts/art/w325/kit.py extract ID      headless Blender -> art/weapons/w325/ID/proj_cache (6 views albedo+depth)
  python3 scripts/art/w325/kit.py build   ID      design.py -> atlas, skin json (parts with UVs), HUD icon, manifest
  python3 scripts/art/w325/kit.py render  ID      review renders of the built model -> art/weapons/w325/ID/review/*.png
  python3 scripts/art/w325/kit.py adscheck ID     ADS occlusion check vs the base top profile (must report OK)
  python3 scripts/art/w325/kit.py contract BASE   print the base weapon's body/magazine geometry bounds (layout contract)

design.py (art/weapons/w325/ID/design.py) defines:
  elements()                -> list of {"name","from","to"[,"rotation":{"origin":[..],"x":..,"y":..,"z":..}]} in model px
                               (vanilla item px, gun along z, muzzle -z, up +y, centred x=8; same frame as the base)
  model2world(name, p)      -> rip world point (metres, Blender coords) the model point p should sample
  is_magazine(name)         -> bool (default: name starts with 'mag_'); magazine elements become parts.magazine
  optional: STYLE ('pixel' default: Minecraft hand-painted look = weapon palette quantisation + majority cleanup +
           crisp 1-texel bevel lines; 'projection' = legacy smooth bake), PALETTE (colours, default 14), T (texels per px, default 16), ATLAS (default 512), grade(rgb), special(e, fn, s, t) -> rgba | None,
            clear(e, fn) -> bool (face painted alpha 0, e.g. sight glass), NO_OVERLAY (bool), FALLBACK rgba.
"""
import hashlib, importlib.util, json, math, os, re, subprocess, sys, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
REG = ROOT / 'art/weapons/w325/registry.json'
ASSETS = ROOT / 'src/main/resources/assets/destiny'
RIPS = Path('/tmp/w325-rips')
BLENDER = os.environ.get('BLENDER', '/Applications/Blender.app/Contents/MacOS/Blender')
HERE = Path(__file__).resolve().parent


def reg(wid):
    for r in json.loads(REG.read_text()):
        if r['id'] == wid: return r
    raise SystemExit(f'unknown weapon {wid}')


def art(wid): return ROOT / 'art/weapons/w325' / wid
def atlas_path(wid): return ASSETS / f'textures/item/weapon/w325/{wid}.png'
def hud_path(wid): return ASSETS / f'textures/item/hud/w325/ammo_{wid}.png'
def skin_path(wid): return ROOT / f'src/main/resources/destiny/weapon_skins/{wid}.json'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()

# ------------------------------------------------------------------------------------------------ fetch / extract
def fetch(wid):
    r = reg(wid); d = RIPS / wid; d.mkdir(parents=True, exist_ok=True)
    arc = d / 'source.archive'
    if not arc.exists() or arc.stat().st_size < 1000:
        url = f'https://drive.usercontent.google.com/download?id={r["drive_file_id"]}&export=download&confirm=t'
        arc.write_bytes(urllib.request.urlopen(url, timeout=600).read())
    out = d / 'src'
    if not out.exists():
        out.mkdir()
        subprocess.run(['bsdtar', '-xf', str(arc), '-C', str(out)], check=True)
    blends = sorted(out.rglob('*.blend'))
    print('archive sha256', sha(arc)); print('blend files:', *blends, sep='\n  ')
    return blends


def blend_of(wid):
    b = sorted((RIPS / wid / 'src').rglob('*.blend'))
    if not b: b = fetch(wid)
    if not b: raise SystemExit('no .blend in rip (fbx-only rips need a manual import step)')
    return b[0]


def extract(wid, ppm=800):
    cache = art(wid) / 'proj_cache'
    subprocess.run([BLENDER, '-b', str(blend_of(wid)), '--python', str(HERE / 'extract_projection_cache.py'), '--',
                    str(cache), str(ppm)], check=True)

# ------------------------------------------------------------------------------------------------ geometry helpers
FACE_AXES = {'north': (2, 0, 0, False, 1, False), 'south': (2, 1, 0, True, 1, False),
             'east': (0, 1, 2, False, 1, False), 'west': (0, 0, 2, True, 1, False),
             'up': (1, 1, 0, True, 2, True), 'down': (1, 0, 0, True, 2, False)}
NORMALS = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0), 'up': (0, 1, 0), 'down': (0, -1, 0)}


def rot_of(e):
    r = e.get('rotation')
    if not r: return None
    if 'axis' in r: return (r['origin'], [(r['axis'], r['angle'])])
    return (r['origin'], [(a, r.get(a, 0)) for a in ('x', 'y', 'z') if r.get(a, 0)])


def rotate(p, rot, inverse=False):
    """Native 26.3 order: Rx then Ry then Rz (matches CuboidRotation / native_triangle_elements_w115)."""
    if not rot: return p
    o, rs = rot
    x, y, z = p[0] - o[0], p[1] - o[1], p[2] - o[2]
    for ax, ang in (list(reversed(rs)) if inverse else rs):
        a = math.radians(-ang if inverse else ang); c, s = math.cos(a), math.sin(a)
        if ax == 'x': y, z = y * c - z * s, y * s + z * c
        elif ax == 'y': x, z = x * c + z * s, -x * s + z * c
        else: x, y = x * c - y * s, x * s + y * c
    return (x + o[0], y + o[1], z + o[2])


def rotate_vec(v, rot): return rotate(v, ((0, 0, 0), rot[1])) if rot else v


def inside(e, p, eps=0.002):
    q = rotate(p, rot_of(e), inverse=True); f, t = e['from'], e['to']
    return all(min(f[i], t[i]) + eps < q[i] < max(f[i], t[i]) - eps for i in range(3))


def face_frame(e, fn):
    f, t = e['from'], e['to']; pa, side, ua, ufwd, va, vfwd = FACE_AXES[fn]
    o = [0.0] * 3; o[pa] = t[pa] if side else f[pa]; o[ua] = f[ua] if ufwd else t[ua]; o[va] = f[va] if vfwd else t[va]
    u = [0.0] * 3; v = [0.0] * 3
    u[ua] = (t[ua] - f[ua]) * (1 if ufwd else -1); v[va] = (t[va] - f[va]) * (1 if vfwd else -1)
    return o, u, v


def face_point(e, fn, s, t_, push=0.0):
    o, u, v = face_frame(e, fn); n = NORMALS[fn]
    return rotate(tuple(o[i] + u[i] * s + v[i] * t_ + n[i] * push for i in range(3)), rot_of(e))

# ------------------------------------------------------------------------------------------------ projection
class View:
    def __init__(self, cache, name, man):
        v = man['views'][name]; self.ppm = man['ppm']
        self.c, self.R, self.U, self.d = v['centre'], v['right'], v['up'], v['dir']
        self.dmin, self.dmax = v['dmin'], v['dmax']
        al = Image.open(cache / f'{name}_albedo.png').convert('RGBA'); self.W, self.H = al.size; self.alb = al.load()
        self.dep = Image.open(cache / f'{name}_depth.png').load()

    def project(self, w):
        q = [w[i] - self.c[i] for i in range(3)]
        return (self.W / 2 + sum(q[i] * self.R[i] for i in range(3)) * self.ppm,
                self.H / 2 - sum(q[i] * self.U[i] for i in range(3)) * self.ppm)

    def depth_at(self, x, y):
        xi, yi = int(x), int(y)
        if not (0 <= xi < self.W and 0 <= yi < self.H): return None
        val = self.dep[xi, yi]
        if isinstance(val, tuple): val = val[0]
        if val == 0: return None
        return self.dmin + (val / 65535 - 0.02) / 0.98 * (self.dmax - self.dmin)

    def sample(self, x, y):
        x -= 0.5; y -= 0.5; x0, y0 = math.floor(x), math.floor(y); fx, fy = x - x0, y - y0
        acc = [0.0] * 3; aw = 0.0
        for dx, dy, wg in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            xi, yi = x0 + dx, y0 + dy
            if 0 <= xi < self.W and 0 <= yi < self.H and wg > 0:
                r, g, b, a = self.alb[xi, yi]; k = wg * a / 255
                acc[0] += r * k; acc[1] += g * k; acc[2] += b * k; aw += k
        return None if aw < 0.5 else (acc[0] / aw, acc[1] / aw, acc[2] / aw)


def default_grade(rgb):
    r, g, b = rgb; yv = 0.299 * r + 0.587 * g + 0.114 * b; y2 = 80 + (yv - 70) * 1.15
    return tuple(max(0, min(255, int(round(y2 + (c - yv) * 0.95)))) for c in (r, g, b))


def lighten(c, f):
    return tuple(max(0, min(255, int(round(ch + (255 - ch) * f if f > 0 else ch * (1 + f))))) for ch in c[:3])


def load_design(wid):
    p = art(wid) / 'design.py'
    sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(f'w325_{wid}', p); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m


SEAM, RIDGE, WEAR_DL, GRAIN = 30.0, 30.0, 46.0, float(os.environ.get('W325_GRAIN', '.45'))


class Baker:
    def __init__(self, wid):
        self.wid = wid; self.D = load_design(wid); D = self.D
        self.T = getattr(D, 'T', 16); self.A = getattr(D, 'ATLAS', 512)
        self.grade = getattr(D, 'grade', default_grade); self.special = getattr(D, 'special', lambda e, fn, s, t: None)
        self.clear = getattr(D, 'clear', lambda e, fn: False)
        self.is_mag = getattr(D, 'is_magazine', lambda n: n.startswith('mag_'))
        self.fallback = tuple(getattr(D, 'FALLBACK', (78, 78, 80, 255)))
        cache = art(wid) / 'proj_cache'; man = json.loads((cache / 'manifest.json').read_text())
        self.views = {k: View(cache, k, man) for k in man['views']}
        ext = max(man['hi'][i] - man['lo'][i] for i in range(3))
        self.occ = getattr(D, 'OCC_TOL', ext * 0.012)

    def pick(self, e, fn, p_model, nm):
        """View whose direction best matches the face normal mapped into rip space."""
        a = self.D.model2world(e['name'], p_model)
        b = self.D.model2world(e['name'], tuple(p_model[i] + nm[i] * 0.25 for i in range(3)))
        wn = [b[i] - a[i] for i in range(3)]; i = max(range(3), key=lambda k: abs(wn[k]))
        return self.views[('p' if wn[i] > 0 else 'n') + 'xyz'[i]]

    def hidden(self, e, fn, others):
        o, u, v = face_frame(e, fn)
        lu = math.dist((0, 0, 0), u); lv = math.dist((0, 0, 0), v)
        nu = max(3, math.ceil(lu / 0.1)); nv = max(3, math.ceil(lv / 0.1))
        for i in range(nu):
            for j in range(nv):
                p = face_point(e, fn, (i + .5) / nu, (j + .5) / nv, push=0.02)
                if not any(inside(x, p) for x in others): return False
        return True

    def face(self, e, fn):
        o, u, v = face_frame(e, fn)
        w = max(1, int(round(math.dist((0, 0, 0), u) * self.T))); h = max(1, int(round(math.dist((0, 0, 0), v) * self.T)))
        nm = rotate_vec(NORMALS[fn], rot_of(e)); view = self.pick(e, fn, face_point(e, fn, .5, .5), nm)
        img = Image.new('RGBA', (w, h)); px = img.load(); valid = [[False] * h for _ in range(w)]
        self._painted = painted = [[False] * h for _ in range(w)]
        if self.clear(e, fn):
            return img, [[True] * h for _ in range(w)], True
        for i in range(w):
            for j in range(h):
                sp = self.special(e, fn, (i + .5) / w, (j + .5) / h)
                if sp is not None:
                    px[i, j] = tuple(sp); valid[i][j] = True; painted[i][j] = True; continue
                acc = [0.0] * 3; n = 0
                for a in range(2):
                    for b in range(2):
                        wp = self.D.model2world(e['name'], face_point(e, fn, (i + (a + .5) / 2) / w, (j + (b + .5) / 2) / h))
                        x, y = view.project(wp); ds = view.depth_at(x, y)
                        if ds is None or ds > sum(wp[k] * view.d[k] for k in range(3)) + self.occ: continue
                        c = view.sample(x, y)
                        if c is None: continue
                        acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]; n += 1
                if n >= 2:
                    px[i, j] = tuple(self.grade((acc[0] / n, acc[1] / n, acc[2] / n))) + (255,); valid[i][j] = True
        return img, valid, False

    @staticmethod
    def inpaint(img, valid, fb):
        w, h = img.size; px = img.load(); todo = [(i, j) for i in range(w) for j in range(h) if not valid[i][j]]
        if len(todo) == w * h:
            for i, j in todo: px[i, j] = fb
            return
        while todo:
            nxt, upd = [], []
            for i, j in todo:
                acc = [0, 0, 0]; n = 0
                for di in (-1, 0, 1):
                    for dj in (-1, 0, 1):
                        a, b = i + di, j + dj
                        if (di or dj) and 0 <= a < w and 0 <= b < h and valid[a][b]:
                            c = px[a, b]; acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]; n += 1
                if n: upd.append((i, j, tuple(x // n for x in acc) + (255,)))
                else: nxt.append((i, j))
            if not upd:
                for i, j in nxt: px[i, j] = fb
                break
            for i, j, c in upd: px[i, j] = c; valid[i][j] = True
            todo = nxt

    def edges(self, img, e, fn, others):
        w, h = img.size; px = img.load()
        if w < 3 or h < 3: return
        flags = []
        o, u, v = face_frame(e, fn); lu = math.dist((0, 0, 0), u) or 1; lv = math.dist((0, 0, 0), v) or 1
        for s, t_ in ((-0.004, .5), (1.004, .5), (.5, -0.004), (.5, 1.004)):
            ss = .5 + (s - .5) * (1 + .06 / lu) if s != .5 else .5; tt = .5 + (t_ - .5) * (1 + .06 / lv) if t_ != .5 else .5
            flags.append(not any(inside(x, face_point(e, fn, ss, tt, push=-0.015)) for x in others))
        side = fn in ('north', 'south', 'east', 'west')
        def tint(i, j, f):
            c = px[i, j]
            if c[3] == 255: px[i, j] = lighten(c, f) + (255,)
        if flags[2]:
            for i in range(w): tint(i, 0, .14 if side else .08)
        if flags[3]:
            for i in range(w): tint(i, h - 1, -.16 if side else .06)
        if flags[0]:
            for j in range(h): tint(0, j, .06)
        if flags[1]:
            for j in range(h): tint(w - 1, j, .06)

    def pixelate(self, faces):
        """Minecraft weapon look (W30 Gnawing Hunger / Blast Furnace / Recluse): a small shared palette, flat colour
        blocks with no projection noise, and crisp 1-texel light/dark bevel lines on exposed edges."""
        k = int(getattr(self.D, 'PALETTE', 20))
        opaque = [img for n, f, img, clear, e, o, pm in faces if not clear]
        if not opaque: return
        # palette from all opaque texels (special()-painted colours included), median cut in RGB
        sw = sum(i.size[0] for i in opaque); sh = max(i.size[1] for i in opaque)
        strip = Image.new('RGB', (sw, sh)); x = 0
        mask = Image.new('L', (sw, sh), 0)
        for i in opaque:
            strip.paste(i.convert('RGB'), (x, 0)); mask.paste(i.getchannel('A'), (x, 0)); x += i.size[0]
        px = [c for c, a in zip(strip.getdata(), mask.getdata()) if a > 0]
        sample = Image.new('RGB', (len(px), 1)); sample.putdata(px)
        pal = sample.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        extra = getattr(self.D, 'PALETTE_KEEP', [])   # exact accent colours a design wants preserved
        for idx, (n, f, img, clear, e, others, pm) in enumerate(faces):
            if clear: continue
            a = img.getchannel('A')
            q = img.convert('RGB').quantize(palette=pal, dither=Image.Dither.NONE)
            w, h = q.size
            # Flat panels: grime/camo noise within a small contrast of the face's dominant colour collapses into it;
            # only strong features (decals, slots, colour-blocked panels) survive as their own palette colour.
            rgb = q.convert('RGB'); hist = rgb.getcolors(w * h) or []
            if hist:
                dom = max(hist)[1]; ld = 0.299 * dom[0] + 0.587 * dom[1] + 0.114 * dom[2]
                tol = float(getattr(self.D, 'FLAT_TOL', 26))
                rp = rgb.load()
                for i in range(w):
                    for j in range(h):
                        c = rp[i, j]; lc = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
                        chroma = max(abs((c[t] - lc) - (dom[t] - ld)) for t in range(3))
                        if abs(lc - ld) < tol and chroma < tol * .9: rp[i, j] = dom
            if w >= 3 and h >= 3:   # majority cleanup: isolated texels join their neighbourhood
                rgb = rgb.filter(ImageFilter.ModeFilter(3))
            out = rgb.convert('RGBA'); out.putalpha(a)
            if extra:   # specials keep their exact colour where they were painted
                op = out.load(); ip = img.load()
                for i in range(w):
                    for j in range(h):
                        c = ip[i, j][:3]
                        if any(sum(abs(c[t] - ex[t]) for t in range(3)) < 24 for ex in extra): op[i, j] = tuple(c) + (ip[i, j][3],)
            # Hand-painted texels (special()) are authored detail: panel lines, lettering, decals. They bypass the
            # palette, flattening and majority filter (which would erase 1-texel lines) and keep their exact colour.
            op = out.load(); ip = img.load()
            for i in range(w):
                for j in range(h):
                    if pm[i][j]: op[i, j] = ip[i, j]
            self.bevel(out, e, f, others)
            faces[idx] = (n, f, out, clear, e, others, pm)

    # ------------------------------------------------------------------ material style (W123 parity)
    KINDS = {
        # field: soft cosine shading across the face; grain: deterministic material texture; detail: weight of the rip's
        # high-pass luminance (panel seams, vents, engraving, logos) carried onto the clean material colour.
        'metal':   dict(field=.06, grain='brushed', amp=7, detail=1.0, rim=.20),
        'steel':   dict(field=.05, grain='brushed', amp=9, detail=1.0, rim=.26),
        'gold':    dict(field=.08, grain='brushed', amp=6, detail=.8, rim=.30, border=True),
        'paint':   dict(field=.05, grain='fine', amp=3, detail=1.1, rim=.16),
        'polymer': dict(field=.04, grain='stipple', amp=6, detail=.9, rim=.10),
        'rubber':  dict(field=.03, grain='cross', amp=7, detail=.6, rim=.05),
        'cloth':   dict(field=.03, grain='weave', amp=10, detail=.7, rim=.04),
        'wood':    dict(field=.05, grain='wood', amp=12, detail=.8, rim=.10),
        'glow':    dict(field=.00, grain=None, amp=0, detail=.3, rim=.0),
        'lens':    dict(field=.10, grain=None, amp=0, detail=.0, rim=.35),
        'dark':    dict(field=.03, grain='fine', amp=2, detail=.6, rim=.06),
    }

    def material_of(self, e, fn):
        f = getattr(self.D, 'material', None)
        if f: return f(e['name'], fn)
        return None

    def materialize(self, faces):
        """W123-style surface: every part gets a clean material base (palette colour + shading + grain) and keeps the
        rip's own surface detail as luminance relief, so the result reads as the original gun, not flat blocks."""
        mats = dict(getattr(self.D, 'MATERIALS', {}))
        # auto palette fallback: the weapon's dominant rip colours (median cut), kind guessed from chroma/brightness
        opaque = [img for n, f, img, clear, e, o, pm in faces if not clear]
        if not opaque: return
        sw = sum(i.size[0] for i in opaque); sh = max(i.size[1] for i in opaque)
        strip = Image.new('RGB', (sw, sh)); x = 0
        for i in opaque: strip.paste(i.convert('RGB'), (x, 0)); x += i.size[0]
        auto = strip.quantize(colors=int(getattr(self.D, 'PALETTE', 8)), method=Image.Quantize.MEDIANCUT,
                              dither=Image.Dither.NONE).getpalette()[:3 * int(getattr(self.D, 'PALETTE', 8))]
        auto = [tuple(auto[i:i + 3]) for i in range(0, len(auto), 3)]
        for idx, (n, f, img, clear, e, others, pm) in enumerate(faces):
            if clear: continue
            w, h = img.size
            rgb = img.convert('RGB')
            L = rgb.convert('L')
            r = max(1, int(round(self.T * .12)))
            blur = L.filter(ImageFilter.GaussianBlur(r * 1.6))
            lp = L.load(); bp = blur.load()
            m = self.material_of(e, f)
            if isinstance(m, str): m = mats.get(m, {'kind': m})
            if m is None or 'color' not in (m or {}):
                mean = rgb.resize((1, 1), Image.BOX).getpixel((0, 0))
                col = min(auto, key=lambda c: sum((c[t] - mean[t]) ** 2 for t in range(3)))
                lum = .299 * col[0] + .587 * col[1] + .114 * col[2]; chroma = max(col) - min(col)
                kind = (m or {}).get('kind') or ('dark' if lum < 45 else 'paint' if chroma > 28 else 'metal' if lum > 110 else 'polymer')
                m = dict(color=col, kind=kind, **{k: v for k, v in (m or {}).items() if k not in ('color', 'kind')})
            k = dict(self.KINDS.get(m.get('kind', 'paint'), self.KINDS['paint'])); k.update({a: m[a] for a in m if a in k})
            base = m['color']; out = Image.new('RGBA', (w, h)); op = out.load(); ip = img.load()
            # thin-line seam mask: a rip texel counts as a panel seam only when it is clearly darker than its
            # surroundings AND part of a 1-2 texel wide continuous line (grime blotches and speckle are rejected)
            raw = [[(lp[i, j] - bp[i, j]) < -SEAM for j in range(h)] for i in range(w)]
            seam = [[False] * h for _ in range(w)]
            for i in range(w):
                for j in range(h):
                    if not raw[i][j]: continue
                    nb = sum(raw[a][b] for a in range(max(0, i - 1), min(w, i + 2)) for b in range(max(0, j - 1), min(h, j + 2))) - 1
                    big = sum(raw[a][b] for a in range(max(0, i - 2), min(w, i + 3)) for b in range(max(0, j - 2), min(h, j + 3)))
                    seam[i][j] = 2 <= nb <= 4 and big <= 11
            seed = sum(ord(c) for c in n + f) % 97
            blum = .299 * base[0] + .587 * base[1] + .114 * base[2]; bchroma = max(base) - min(base)
            wear = m.get('wear')
            if wear is None and m.get('kind', 'paint') == 'paint' and m.get('wear', True) is not False:
                wear = (188, 178, 156) if blum < 150 else tuple(int(c * .45) for c in base)
            if wear is False: wear = None
            long_u = w >= h
            for i in range(w):
                for j in range(h):
                    if pm[i][j] and not os.environ.get('W325_IGNORE_SPECIAL'): op[i, j] = ip[i, j]; continue
                    v = (j + .5) / h
                    fld = 1 + k['field'] * math.cos(v * math.pi)
                    hp = (lp[i, j] - bp[i, j]) * k['detail']
                    # W123 language: relief is authored lines, not soft noise. Strong rip seams become a crisp dark
                    # texel, strong ridges a crisp light texel; weak relief is kept faint so plates stay clean.
                    if seam[i][j] and k['detail'] > 0: d = -.34
                    else: d = max(-.05, min(.05, hp * .25 / 255.0))
                    g = 0.0; a = k['amp']
                    if k['grain'] == 'brushed':
                        t = j if long_u else i
                        g = (((t * 37 + seed) % 11) - 5) / 5 * a * (.6 + .4 * (((t * 13 + seed) % 3) == 0))
                    elif k['grain'] == 'stipple':
                        g = ((((i * 73) ^ (j * 151) + seed) % 7) - 3) / 3 * a
                    elif k['grain'] == 'fine':
                        g = (((i * 17 + j * 29 + seed) % 23) - 11) / 11 * a
                    elif k['grain'] == 'cross':
                        g = (-a if ((i + j) % 3 == 0 or (i - j) % 3 == 0) else a * .4)
                    elif k['grain'] == 'weave':
                        g = (a if ((i // 2 + j // 2) % 2) else -a)
                    elif k['grain'] == 'wood':
                        t = (i if long_u else j) * .0 + (j if long_u else i)
                        g = math.sin((t + 3 * math.sin((i if long_u else j) * .07 + seed)) * .9) * a
                    c = tuple(max(0, min(255, int(round(base[t] * fld * (1 + d * 1.35) + g * GRAIN)))) for t in range(3))
                    if wear is not None and not seam[i][j]:
                        rc = ip[i, j]; rl = .299 * rc[0] + .587 * rc[1] + .114 * rc[2]
                        # paint chipped to the substrate: the rip shows bare metal / primer where it is much lighter
                        # (or darker, on light paint) than the coat; keep those texels as crisp wear marks.
                        if (rl - blum > WEAR_DL and (max(rc) - min(rc)) < bchroma + 30) or (blum > 150 and blum - rl > WEAR_DL * 1.4):
                            c = tuple(int(wear[t] * (.92 + .08 * fld)) for t in range(3))
                    op[i, j] = c + (255,)
            # material motifs readable at play distance (W123 receiver/grip/rail motifs)
            kind = m.get('kind', 'paint'); side = f in ('east', 'west', 'north', 'south')
            def shade(i, j, fac):
                if not pm[i][j]: op[i, j] = lighten(op[i, j][:3], fac) + (255,)
            if kind in ('metal', 'steel') and side and h >= 5:
                band = max(1, h // 7)
                for i in range(w):
                    for j in range(1, 1 + band): shade(i, j, .16 if kind == 'steel' else .11)
                    shade(i, h - 2, -.12)
            if kind == 'rubber' and w >= 4 and h >= 4:
                for i in range(w):
                    for j in range(h):
                        if (i % 3 == 0) and (j % 3 == 0): shade(i, j, -.22)
                        elif ((i + 1) % 3 == 0) and ((j + 1) % 3 == 0): shade(i, j, .07)
            if kind == 'polymer' and w >= 4 and h >= 4:
                for i in range(w):
                    for j in range(h):
                        if ((i * 7 + j * 13 + seed) % 9) == 0: shade(i, j, .10)
            if kind == 'gold' and side and h >= 4:
                for i in range(w): shade(i, 1, .22)
            # machined plate edge (W123 col[edge]=base+10): every panel reads as a separate part, not one slab
            if k.get('plate', True) and w >= 4 and h >= 4 and m.get('kind') not in ('rubber', 'dark', 'glow', 'lens', 'cloth'):
                for i in range(w):
                    for j in range(h):
                        if (i in (0, w - 1) or j in (0, h - 1)) and not pm[i][j]:
                            op[i, j] = tuple(min(255, c + 10) for c in op[i, j][:3]) + (255,)
            if k.get('border') and w >= 6 and h >= 6:
                for i in range(1, w - 1):
                    for j in (1, h - 2): op[i, j] = tuple(max(0, int(c * .72)) for c in op[i, j][:3]) + (255,)
                for j in range(1, h - 1):
                    for i in (1, w - 2): op[i, j] = tuple(max(0, int(c * .72)) for c in op[i, j][:3]) + (255,)
            if k['rim'] > 0: self.rim(out, e, f, others, k['rim'])
            faces[idx] = (n, f, out, clear, e, others, pm)

    def rim(self, img, e, fn, others, s):
        """1-texel lit top edge and dark lower seam on exposed edges (Ace/W123 edge language)."""
        w, h = img.size; px = img.load()
        if w < 3 or h < 3: return
        o, u, v = face_frame(e, fn); lu = math.dist((0, 0, 0), u) or 1; lv = math.dist((0, 0, 0), v) or 1
        flags = []
        for s_, t_ in ((-0.004, .5), (1.004, .5), (.5, -0.004), (.5, 1.004)):
            ss = .5 + (s_ - .5) * (1 + .06 / lu) if s_ != .5 else .5; tt = .5 + (t_ - .5) * (1 + .06 / lv) if t_ != .5 else .5
            flags.append(not any(inside(x, face_point(e, fn, ss, tt, push=-0.015)) for x in others))
        def tint(i, j, f):
            c = px[i, j]
            if c[3] == 255: px[i, j] = lighten(c, f) + (255,)
        if flags[2]:
            for i in range(w): tint(i, 0, s)
        if flags[3]:
            for i in range(w): tint(i, h - 1, -s * 1.2)
        if flags[0]:
            for j in range(h): tint(0, j, s * .5)
        if flags[1]:
            for j in range(h): tint(w - 1, j, -s * .6)

    def bevel(self, img, e, fn, others):
        """Crisp 1-texel edge lines: top/left light, bottom/right dark on side faces; light rim on top faces."""
        w, h = img.size; px = img.load()
        if w < 2 or h < 2: return
        o, u, v = face_frame(e, fn); lu = math.dist((0, 0, 0), u) or 1; lv = math.dist((0, 0, 0), v) or 1
        flags = []
        for s, t_ in ((-0.004, .5), (1.004, .5), (.5, -0.004), (.5, 1.004)):
            ss = .5 + (s - .5) * (1 + .06 / lu) if s != .5 else .5; tt = .5 + (t_ - .5) * (1 + .06 / lv) if t_ != .5 else .5
            flags.append(not any(inside(x, face_point(e, fn, ss, tt, push=-0.015)) for x in others))
        side = fn in ('north', 'south', 'east', 'west')
        def tint(i, j, f):
            c = px[i, j]
            if c[3] == 255: px[i, j] = lighten(c, f) + (255,)
        hi, lo = (.22, -.28) if side else (.16, -.12)
        if flags[2]:
            for i in range(w): tint(i, 0, hi)
        if flags[3]:
            for i in range(w): tint(i, h - 1, lo)
        if flags[0]:
            for j in range(1, h - 1): tint(0, j, hi * .6)
        if flags[1]:
            for j in range(1, h - 1): tint(w - 1, j, lo * .6)

    def build(self):
        els = [dict(e) for e in self.D.elements()]
        names = [e['name'] for e in els]
        if len(names) != len(set(names)): raise SystemExit('duplicate element names')
        for e in els:
            for v in e['from'] + e['to']:
                if not -16 <= v <= 32: raise SystemExit(f'{e["name"]} outside -16..32')
        faces, hidden = [], []
        style = os.environ.get('W325_STYLE') or getattr(self.D, 'STYLE', 'pixel')
        for e in els:
            others = [o for o in els if o is not e and self.is_mag(o['name']) == self.is_mag(e['name'])]
            for fn in FACE_AXES:
                if self.hidden(e, fn, others): hidden.append((e['name'], fn)); continue
                img, valid, clear = self.face(e, fn)
                if not clear:
                    self.inpaint(img, valid, self.fallback)
                    if style == 'projection':
                        if img.size[0] >= 3 and img.size[1] >= 3:
                            img = Image.blend(img, img.filter(ImageFilter.MedianFilter(3)), .5)
                        self.edges(img, e, fn, others)
                faces.append((e['name'], fn, img, clear, e, others, self._painted))
        if style == 'pixel': self.pixelate(faces)
        if style == 'material': self.materialize(faces)
        faces = [(n, f, img) for n, f, img, *_ in faces]
        order = sorted([((n, f), img.size[0] + 2, img.size[1] + 2) for n, f, img in faces] + [(('_h', '_'), 4, 4)],
                       key=lambda r: (-r[2], -r[1], r[0]))
        pos = {}; x = y = shelf = 0
        for key, w, h in order:
            if x + w > self.A: y += shelf; x = 0; shelf = 0
            pos[key] = (x, y); x += w; shelf = max(shelf, h)
        used = y + shelf
        if used > self.A: raise SystemExit(f'atlas overflow {used}>{self.A}: lower T or simplify')
        atlas = Image.new('RGBA', (self.A, self.A), (0, 0, 0, 0)); k = 16.0 / self.A; uv = {}
        for n, f, img in faces:
            x0, y0 = pos[(n, f)]; w, h = img.size
            g = Image.new('RGBA', (w + 2, h + 2)); g.paste(img.resize((w + 2, h + 2), Image.NEAREST)); g.paste(img, (1, 1))
            atlas.paste(g, (x0, y0))
            uv.setdefault(n, {})[f] = [round((x0 + 1) * k, 6), round((y0 + 1) * k, 6), round((x0 + 1 + w) * k, 6), round((y0 + 1 + h) * k, 6)]
        hx, hy = pos[('_h', '_')]; atlas.paste(Image.new('RGBA', (4, 4), (40, 40, 42, 255)), (hx, hy))
        huv = [round((hx + 1) * k, 6), round((hy + 1) * k, 6), round((hx + 3) * k, 6), round((hy + 3) * k, 6)]
        for n, f in hidden: uv.setdefault(n, {})[f] = huv
        # crop unused atlas rows to a power of two (texture memory / pack size)
        H = 16
        while H < used: H *= 2
        if H < self.A:
            atlas = atlas.crop((0, 0, self.A, H)); kv = self.A / H
            for n in uv:
                for f in uv[n]: a = uv[n][f]; uv[n][f] = [a[0], round(a[1] * kv, 6), a[2], round(a[3] * kv, 6)]
        parts = {'body': [], 'magazine': []}
        for e in els:
            out = {'name': e['name'], 'from': [round(v, 5) for v in e['from']], 'to': [round(v, 5) for v in e['to']]}
            r = rot_of(e)
            if r:
                rr = {'origin': [round(v, 5) for v in r[0]], 'x': 0, 'y': 0, 'z': 0}
                for ax, ang in r[1]: rr[ax] = round(ang, 5)
                out['rotation'] = rr
            for key in ('shade', 'light_emission'):
                if key in e: out[key] = e[key]
            out['faces'] = {fn: {'uv': uv[e['name']][fn], 'texture': '#0'} for fn in ('north', 'east', 'south', 'west', 'up', 'down')}
            parts['magazine' if self.is_mag(e['name']) else 'body'].append(out)
        doc = {'texture_size': [atlas.size[0], atlas.size[1]], 'parts': parts}
        if getattr(self.D, 'NO_OVERLAY', False): doc['no_overlay'] = True
        for p in (atlas_path(self.wid), hud_path(self.wid), skin_path(self.wid)): p.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(atlas_path(self.wid), optimize=True)
        skin_path(self.wid).write_text(json.dumps(doc, separators=(',', ':')))
        hud_icon(els, hud_path(self.wid), getattr(self.D, 'HUD_SKIP', lambda n: False))
        r = reg(self.wid)
        m = {'batch': 'W325', 'id': self.wid, 'name': r['name'], 'tier': r['tier'], 'base': r['base'],
             'drive_file_id': r['drive_file_id'], 'elements': {k: len(v) for k, v in parts.items()},
             'element_total': sum(len(v) for v in parts.values()), 'texels_per_px': self.T, 'atlas': list(atlas.size),
             'hidden_faces': len(hidden), 'rip_archive_sha256': sha(RIPS / self.wid / 'source.archive') if (RIPS / self.wid / 'source.archive').exists() else None,
             'outputs_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (atlas_path(self.wid), hud_path(self.wid), skin_path(self.wid))}}
        (art(self.wid) / 'manifest.json').write_text(json.dumps(m, indent=1, sort_keys=True) + '\n')
        print(f'build {self.wid}: body {len(parts["body"])} + magazine {len(parts["magazine"])} elements, '
              f'{len(faces)} faces ({len(hidden)} hidden), atlas {atlas.size}')


def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3: return pts
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def hud_icon(els, path, skip):
    """160x64 white side silhouette, muzzle left (same convention as the W112/W302 ammo icons)."""
    polys = []
    for e in els:
        if skip(e['name']): continue
        f, t = e['from'], e['to']; rot = rot_of(e)
        pts = [rotate((x, y, z), rot) for x in (f[0], t[0]) for y in (f[1], t[1]) for z in (f[2], t[2])]
        polys.append(hull([(p[2], p[1]) for p in pts]))
    zs = [p[0] for pl in polys for p in pl]; ys = [p[1] for pl in polys for p in pl]
    z0, z1, y0, y1 = min(zs), max(zs), min(ys), max(ys); bw, bh = 152, 53
    sc = min(bw / (z1 - z0), bh / (y1 - y0)); ox = 4 + (bw - (z1 - z0) * sc) / 2; oy = 5 + (bh - (y1 - y0) * sc) / 2; up = 8
    m = Image.new('L', (160 * up, 64 * up), 0); d = ImageDraw.Draw(m)
    for pl in polys: d.polygon([((ox + (z - z0) * sc) * up, (oy + (y1 - y) * sc) * up) for z, y in pl], fill=255)
    a = m.resize((160, 64), Image.BOX).point(lambda v: min(252, (v + 2) // 4 * 4) if v < 250 else 255)
    icon = Image.new('RGBA', (160, 64), (255, 255, 255, 0)); icon.putalpha(a); icon.save(path, optimize=True)

# ------------------------------------------------------------------------------------------------ contract / render
def contract(base):
    """Donor geometry bounds for presentation reference, not target exterior proportions.
    Keep the original weapon's proportions and adapt grip, moving-part pivots and sight framing separately.
    """
    md = ASSETS / 'models'
    hits = sorted(p for p in md.rglob(f'*{base}*.json') if re.search(rf'(?<![a-z0-9]){re.escape(base)}(?![a-z0-9])', p.name))
    seen = set()
    for p in hits:
        d = json.loads(p.read_text()); els = d.get('elements', [])
        if not els or 'gui' in p.parts: continue
        key = (p.parent.name, len(els))
        if key in seen: continue
        seen.add(key)
        if len(seen) > 16: break
        lo = [min(min(e['from'][i], e['to'][i]) for e in els) for i in range(3)]
        hi = [max(max(e['from'][i], e['to'][i]) for e in els) for i in range(3)]
        print(p.relative_to(ROOT), len(els), 'elements  lo', [round(v, 2) for v in lo], 'hi', [round(v, 2) for v in hi])
    print(f'({len(hits)} files mention {base}; W302 contract examples: art/weapons/w302/*/manifest.json)')


def _corners(e):
    f, t = e['from'], e['to']; rot = rot_of(e)
    return [rotate((x, y, z), rot) for x in (f[0], t[0]) for y in (f[1], t[1]) for z in (f[2], t[2])]


def adscheck(wid):
    """Conservative donor-framing conflict hint, not a visibility or exterior-quality gate.
    Compare rear-section element bounds with the donor's top profile. Bounds do not account for
    cutout alpha or the weapon's own sight line. Preserve source geometry; resolve framing separately
    and verify the actual ADS framebuffer instead of deforming an exterior to pass this comparison.
    """
    r = reg(wid); base = r['base']; md = ASSETS / 'models'
    cands = [md / f'weapon_sight_w151/{base}_body.json'] + sorted(md.glob(f'weapon_reload_w*_{base}/{base}_body.json')) \
        + sorted(md.glob(f'weapon/*/{base}.json'))
    src = next((p for p in cands if p.exists() and json.loads(p.read_text()).get('elements')), None)
    if src is None: raise SystemExit(f'no base body model for {base}')
    base_els = json.loads(src.read_text())['elements']
    skin = json.loads(skin_path(wid).read_text())['parts']['body']
    def top(els, z0, z1, band=(6.6, 9.4)):
        best = None
        for e in els:
            c = _corners(e)
            if max(p[2] for p in c) < z0 or min(p[2] for p in c) > z1: continue
            if max(p[0] for p in c) < band[0] or min(p[0] for p in c) > band[1]: continue
            if any(f.get('texture') not in ('#0', None) for f in e.get('faces', {}).values()) and 'aim' in e.get('name', ''): continue
            y = max(p[1] for p in c); best = y if best is None or y > best else best
        return best
    zs = [p[2] for e in base_els for p in _corners(e)]
    zmin, zmax = min(zs), max(zs); start = zmin + (zmax - zmin) / 3
    bad = []; z = start
    while z < zmax:
        b = top(base_els, z, z + .25); k = top(skin, z, z + .25)
        if k is not None and (b is None or k > b + .15): bad.append((round(z, 2), round(k, 2), None if b is None else round(b, 2)))
        z += .25
    print(f'adscheck {wid} vs {src.relative_to(ROOT)}: z {start:.2f}..{zmax:.2f}')
    if not bad: print('  OK: skin never rises above the base top profile behind the front third'); return
    print('  DONOR FRAMING CONFLICT (z, skin top, base top) — preserve source shape; review own sight framing and native ADS:')
    for row in bad: print('   ', row)


def render(wid, views='west,east,top,q,front'):
    out = art(wid) / 'review'; out.mkdir(parents=True, exist_ok=True)
    subprocess.run([BLENDER, '-b', '--python', str(HERE / 'render_model.py'), '--', str(out / wid), str(skin_path(wid)),
                    str(atlas_path(wid)), views], check=True)


if __name__ == '__main__':
    if len(sys.argv) < 3: raise SystemExit(__doc__)
    cmd, arg = sys.argv[1], sys.argv[2]
    {'fetch': fetch, 'extract': extract, 'build': lambda w: Baker(w).build(), 'render': render, 'contract': contract, 'adscheck': adscheck}[cmd](arg)
