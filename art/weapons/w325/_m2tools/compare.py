"""<id>_compare.png: rip side view (proj_cache nx_albedo) over the kit west render, rip quarter vs kit q render."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[4]
wid = sys.argv[1]; ripq = sys.argv[2] if len(sys.argv) > 2 else None
A = ROOT / 'art/weapons/w325' / wid
def crop(im):
    bb = im.convert('RGB').point(lambda v: 0 if abs(v - 0) < 0 else v)
    return im
rip = Image.open(A / 'proj_cache/nx_albedo.png').convert('RGBA'); bg = Image.new('RGBA', rip.size, (153, 155, 160, 255)); bg.alpha_composite(rip)
W = 1200; rip = bg.resize((int(W * .9), int(bg.height * W * .9 / bg.width)), Image.LANCZOS)
west = Image.open(A / f'review/{wid}_west.png').convert('RGBA')
rows = [('rip side (proj_cache nx_albedo)', rip), ('model west render', west)]
if ripq:
    q = Image.open(A / f'review/{wid}_q.png').convert('RGBA'); rq = Image.open(ripq).convert('RGBA').resize(q.size)
    pair = Image.new('RGBA', (W, q.height // 2), (153, 155, 160, 255))
    pair.paste(rq.resize((W // 2, q.height // 2)), (0, 0)); pair.paste(q.resize((W // 2, q.height // 2)), (W // 2, 0))
    rows.append(('rip quarter | model quarter', pair))
H = sum(r.height + 24 for _, r in rows)
out = Image.new('RGBA', (W, H), (153, 155, 160, 255)); d = ImageDraw.Draw(out); y = 0
for t, r in rows:
    d.text((8, y + 6), t, fill=(0, 0, 0)); y += 24; out.paste(r, ((W - r.width) // 2, y)); y += r.height
out.convert('RGB').save(A / f'review/{wid}_compare.png', optimize=True); print(A / f'review/{wid}_compare.png')
