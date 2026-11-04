"""W301: Generalist Shell default is white (user); the inner core stays grey.

Re-tints only the texels used by the outershell_* faces of the tutorial Ghost (UV rectangles read from the
models); innercore_* and eye_lens texels keep the original grey/cyan. Idempotent: light texels are skipped.
Run from the original atlas (git HEAD) for an exact result:
    git show HEAD:src/main/resources/assets/destiny/textures/item/tutorial/ghost.png > ghost.png (then run)
"""
import glob
import json
import os
from PIL import Image

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src", "main", "resources", "assets", "destiny")
PATH = os.path.join(ASSETS, "textures", "item", "tutorial", "ghost.png")
MODELS = os.path.join(ASSETS, "models", "tutorial", "ghost")


def rects(prefix, size):
    k = size / 16.0
    out = []
    for f in glob.glob(os.path.join(MODELS, prefix + "*.json")):
        for e in json.load(open(f)).get("elements", []):
            for face in e["faces"].values():
                u0, v0, u1, v1 = face["uv"]
                out.append((int(round(min(u0, u1) * k)), int(round(min(v0, v1) * k)),
                            int(round(max(u0, u1) * k)), int(round(max(v0, v1) * k))))
    return out


def main():
    im = Image.open(PATH).convert("RGBA")
    w, _ = im.size
    shell = Image.new("1", im.size, 0)
    keep = Image.new("1", im.size, 0)
    for r in rects("outershell_", w):
        shell.paste(1, r)
    for r in rects("innercore_", w) + rects("eye_", w):
        keep.paste(1, r)
    px, sm, km = im.load(), shell.load(), keep.load()
    for y in range(im.size[1]):
        for x in range(w):
            if not sm[x, y] or km[x, y]:
                continue
            r, g, b, a = px[x, y]
            if a == 0 or (b > 180 and g > 150 and r < 120) or max(r, g, b) > 150:
                continue
            k = 2.85
            px[x, y] = (min(246, int(r * k)), min(246, int(g * k)), min(248, int(b * k + 4)), a)
    im.save(PATH, optimize=True)


if __name__ == "__main__":
    main()
