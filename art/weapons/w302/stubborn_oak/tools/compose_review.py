"""Compose review sheets from registered Blender renders (same camera per view)."""
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

RAW = Path(sys.argv[1])
OUT = Path(sys.argv[2])
TAG = sys.argv[3]          # e.g. 'bo' (blockout) or 'final'
PX, Z0, Y1 = 50, -11.0, 15.0
F = ImageFont.load_default(size=20)


def mask(im):
    bg = im.getpixel((2, 2))
    d = ImageChops.difference(im.convert('RGB'), Image.new('RGB', im.size, bg[:3])).convert('L')
    return d.point(lambda v: 255 if v > 6 else 0)


def label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 14 + 11 * len(text), 30), fill=(20, 24, 30))
    d.text((7, 4), text, font=F, fill=(255, 255, 255))
    return im


def grid(im, top=Y1):
    d = ImageDraw.Draw(im, 'RGBA')
    for k in range(int(im.width / PX) + 1):
        z = Z0 + k
        d.line([(k * PX, 0), (k * PX, im.height)], fill=(0, 0, 0, 40 if z % 5 else 90))
    for k in range(int(im.height / PX) + 1):
        d.line([(0, k * PX), (im.width, k * PX)], fill=(0, 0, 0, 40 if (top - k) % 5 else 90))
    return im


def stack(paths, labels):
    ims = [label(Image.open(p).convert('RGB'), t) for p, t in zip(paths, labels)]
    w = max(i.width for i in ims)
    sheet = Image.new('RGB', (w, sum(i.height for i in ims)), (20, 24, 30))
    y = 0
    for i in ims:
        sheet.paste(i, (0, y))
        y += i.height
    return sheet


def overlay(mine, contract, extra=None):
    a = Image.open(mine).convert('RGB')
    m = mask(Image.open(contract))
    edge = m.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 0 else 0)
    tint = Image.new('RGB', a.size, (40, 120, 255))
    out = Image.composite(Image.blend(a, tint, 0.35), a, m)
    out.paste((255, 0, 200), mask=edge)
    if extra:
        e = mask(Image.open(extra)).filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v else 0)
        out.paste((255, 230, 0), mask=e)
    return grid(out)


OUT.mkdir(parents=True, exist_ok=True)
stack([RAW / 'src_west.png', RAW / f'{TAG}_west.png'],
      ['SOURCE rip (D2 shader, EEVEE)', f'W302 {TAG} (Blockbench export, same camera)']
      ).save(OUT / f'{TAG}_vs_source_side.png')
stack([RAW / f'{TAG}_q.png', RAW / f'{TAG}_top.png', RAW / f'{TAG}_east.png'],
      [f'{TAG} three-quarter', f'{TAG} top', f'{TAG} side2 (right)']).save(OUT / f'{TAG}_views.png')
label(overlay(RAW / f'{TAG}_west.png', RAW / 'con_west.png', RAW / 'sight_west.png'),
      'magenta = mindbender contract outline, yellow = W148 sight overlay, 1px grid'
      ).save(OUT / f'{TAG}_contract_overlay_side.png')
