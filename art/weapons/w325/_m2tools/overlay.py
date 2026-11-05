"""Review helper (W325 worker m2): warp a rip projection view into model px space through design.model2world and
overlay the authored elements (and optionally the base contract leaves) with a model-px grid.
usage: overlay.py ID [side|top] [K px per model px] [base json rel to models/ ...]"""
import importlib.util, json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/art/w325'))
import kit
wid = sys.argv[1]; mode = sys.argv[2] if len(sys.argv) > 2 else 'side'; K = int(sys.argv[3]) if len(sys.argv) > 3 else 24
bases = sys.argv[4:]
D = kit.load_design(wid)
cache = kit.art(wid) / 'proj_cache'; man = json.loads((cache / 'manifest.json').read_text())
Z0, Z1 = -11.5, 18.5
if mode == 'side':
    Y0, Y1 = 3.0, 15.0; view = kit.View(cache, getattr(D, 'SIDE_VIEW', 'nx'), man)
else:
    Y0, Y1 = 5.5, 10.5; view = kit.View(cache, getattr(D, 'TOP_VIEW', 'nz'), man)
W, H = int((Z1 - Z0) * K), int((Y1 - Y0) * K)
img = Image.new('RGBA', (W, H), (110, 130, 160, 255)); px = img.load()
probe = getattr(D, 'PROBE', 'body')
for j in range(H):
    for i in range(W):
        z = Z0 + (i + .5) / K; v = Y1 - (j + .5) / K
        p = (8.0, v, z) if mode == 'side' else (v, 11.0, z)
        x, y = view.project(D.model2world(probe, p)); c = view.sample(x, y)
        if c: px[i, j] = tuple(int(a) for a in c) + (255,)
d = ImageDraw.Draw(img)
def M(z, v): return ((z - Z0) * K, (Y1 - v) * K)
for g in range(int(Z0), int(Z1) + 1):
    d.line([M(g, Y0), M(g, Y1)], fill=(255, 255, 255, 60) if g % 5 else (255, 255, 0, 110))
for g in range(int(Y0), int(Y1) + 1):
    d.line([M(Z0, g), M(Z1, g)], fill=(255, 255, 255, 60) if g % 5 else (255, 255, 0, 110))
for g in range(int(Z0), int(Z1) + 1, 2): d.text(M(g + .05, Y1 - .05), str(g), fill=(255, 255, 0))
for g in range(int(Y0), int(Y1) + 1): d.text(M(Z0 + .05, g + .45), str(g), fill=(255, 255, 0))
def outline(e, col):
    f, t = e['from'], e['to']; r = kit.rot_of(e)
    pts = [kit.rotate((x, y, z), r) for x in (f[0], t[0]) for y in (f[1], t[1]) for z in (f[2], t[2])]
    hp = kit.hull([(p[2], p[1]) if mode == 'side' else (p[2], p[0]) for p in pts])
    if len(hp) >= 2: d.line([M(*q) for q in hp + hp[:1]], fill=col, width=1)
for b in bases:
    for e in json.loads((kit.ASSETS / 'models' / b).read_text())['elements']: outline(e, (255, 60, 255, 255))
if not getattr(D, '_NO_ELEMENTS', False):
    for e in D.elements(): outline(e, (60, 255, 60, 255) if not D.is_magazine(e['name']) else (255, 140, 0, 255)) if hasattr(D, 'is_magazine') else outline(e, (60, 255, 60, 255))
out = kit.art(wid) / 'review' / f'_overlay_{mode}.png'; out.parent.mkdir(exist_ok=True, parents=True); img.save(out); print(out)
