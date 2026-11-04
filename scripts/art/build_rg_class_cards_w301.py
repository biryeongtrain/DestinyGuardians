"""W301: class-choice cards for the A Guardian Rises opening (augment-style picker).

Generates flat HUD quads (destiny:gui/hud/<name>) in the same tinted-paper format as tile/diamond:
  rg_class_card_{titan,hunter,warlock}  baked panel (class wash, watermark, icon ring, divider)
  rg_class_glow       selection halo (white, tinted with the class colour at runtime)
  rg_class_dim        dark veil for unselected cards
  rg_class_flash      confirm flash
  rg_class_backdrop   full-screen vignette
  rg_class_icon_*     smooth 256px class emblems (white; tinted)
  rg_key / rg_key_wide keycaps
  rg_line             fading header rule
Run with any Pillow >= 10:  python scripts/art/build_rg_class_cards_w301.py
"""
import json
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src", "main", "resources", "assets", "destiny")
TEX = os.path.join(ROOT, "textures", "item", "hud")
MODELS = os.path.join(ROOT, "models", "gui", "hud")
ITEMS = os.path.join(ROOT, "items", "gui", "hud")
SS = 4  # supersampling

W, H = 256, 352
CUT = 22  # Destiny-style cut corners (top-right, bottom-left)
CLASSES = {
    "titan": (0xE5, 0x75, 0x75),
    "hunter": (0x79, 0xB9, 0xDF),
    "warlock": (0xED, 0xCE, 0x79),
}
ICON_Y = 0.29  # icon centre (fraction of height); must match ClassCardHud
DIVIDER_Y = 0.665


def card_mask(w, h, cut, inset=0.0):
    m = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(m)
    i = inset * SS
    c = cut * SS
    pts = [(i, i), (w * SS - c - i * 0.6, i), (w * SS - i, c + i * 0.6), (w * SS - i, h * SS - i),
           (c + i * 0.6, h * SS - i), (i, h * SS - c - i * 0.6)]
    d.polygon(pts, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def border(w, h, cut, width):
    return ImageChops.subtract(card_mask(w, h, cut), card_mask(w, h, cut, inset=width))


def icon(name, size=256):
    src = Image.open(os.path.join(TEX, f"class_{name}_w248.png")).convert("RGBA")
    a = src.getchannel("A").resize((size, size), Image.LANCZOS).filter(ImageFilter.GaussianBlur(size / 220))
    a = a.point(lambda v: max(0, min(255, int((v - 128) * 3.2 + 128))))
    out = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    out.putalpha(a)
    return out


def tinted(mask, rgb, scale):
    layer = Image.new("RGBA", mask.size, rgb + (0,))
    layer.putalpha(mask.point(lambda v: v * scale // 255))
    return layer


def card(name, rgb):
    r, g, b = rgb
    img = Image.new("RGBA", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        base = (20 - 8 * t, 22 - 9 * t, 29 - 11 * t)
        for x in range(W):
            dx = (x - W / 2) / (W * 0.62)
            dy = (y - H * 1.02) / (H * 0.55)
            wash = max(0.0, 1 - math.hypot(dx, dy)) ** 1.5 * 0.58
            top = max(0.0, 1 - y / 90) ** 2 * 0.38
            k = wash + top
            px[x, y] = (int(base[0] + (r - base[0]) * k), int(base[1] + (g - base[1]) * k),
                        int(base[2] + (b - base[2]) * k), 238)
    wm = icon(name, 230).getchannel("A")
    layer = Image.new("L", (W, H), 0)
    layer.paste(wm, ((W - 230) // 2, int(H * 0.42) - 115))
    img.alpha_composite(tinted(layer, (r, g, b), 26))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - CUT, 3], fill=(r, g, b, 255))
    cx, cy = W / 2, H * ICON_Y
    disc = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(disc).ellipse([(cx - 50) * SS, (cy - 50) * SS, (cx + 50) * SS, (cy + 50) * SS], fill=255)
    disc = disc.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(7))
    img.alpha_composite(tinted(disc, (r // 3, g // 3, b // 3), 150))
    ring = Image.new("L", (W * SS, H * SS), 0)
    rd = ImageDraw.Draw(ring)
    rad = 52 * SS
    rd.ellipse([cx * SS - rad, cy * SS - rad, cx * SS + rad, cy * SS + rad], outline=255, width=int(1.6 * SS))
    for k in range(4):
        ang = math.pi / 4 + k * math.pi / 2
        r0, r1 = 58 * SS, 66 * SS
        rd.line([cx * SS + math.cos(ang) * r0, cy * SS + math.sin(ang) * r0,
                 cx * SS + math.cos(ang) * r1, cy * SS + math.sin(ang) * r1], fill=255, width=int(2 * SS))
    img.alpha_composite(tinted(ring.resize((W, H), Image.LANCZOS), (r, g, b), 160))
    dy = int(H * DIVIDER_Y)
    for x in range(30, W - 30):
        f = 1 - abs((x - W / 2) / (W / 2 - 30)) ** 2
        img.putpixel((x, dy), (r, g, b, int(200 * f)))
    img.alpha_composite(tinted(border(W, H, CUT, 1.8), (r, g, b), 120))
    d = ImageDraw.Draw(img)
    d.line([(W - 2, H - 28), (W - 2, H - 2), (W - 28, H - 2)], fill=(r, g, b, 230), width=2)
    d.line([(1, 28), (1, 1), (28, 1)], fill=(r, g, b, 230), width=2)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), card_mask(W, H, CUT)))
    return img


GLOW_MARGIN = 20


def glow():
    m = GLOW_MARGIN
    w, h = W + m * 2, H + m * 2
    shape = Image.new("L", (w, h), 0)
    shape.paste(card_mask(W, H, CUT), (m, m))
    halo = shape.filter(ImageFilter.GaussianBlur(9)).point(lambda v: min(255, v * 2))
    halo = ImageChops.subtract(halo, shape)
    edge = Image.new("L", (w, h), 0)
    edge.paste(border(W, H, CUT, 2.4), (m, m))
    a = ImageChops.lighter(halo.point(lambda v: v * 170 // 255), edge)
    out = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    out.putalpha(a)
    return out


def veil(alpha):
    return tinted(card_mask(W, H, CUT), (0, 0, 0), alpha)


def flash():
    a = Image.new("L", (W, H))
    pa = a.load()
    for y in range(H):
        for x in range(W):
            e = min(x, y, W - 1 - x, H - 1 - y) / 40
            pa[x, y] = int(255 * (0.5 + 0.5 * max(0.0, 1 - e)))
    return tinted(ImageChops.multiply(a, card_mask(W, H, CUT)), (255, 255, 255), 255)


def backdrop():
    w, h = 320, 180
    out = Image.new("RGBA", (w, h))
    p = out.load()
    for y in range(h):
        for x in range(w):
            d = math.hypot((x - w / 2) / (w / 2), (y - h * 0.5) / (h / 2))
            p[x, y] = (2, 4, 8, int(min(250, 170 + 80 * d ** 1.5)))
    return out


def key(w, h):
    big = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(big).rounded_rectangle([SS, SS, w * SS - SS, h * SS - SS], radius=12 * SS, fill=255)
    fill = big.resize((w, h), Image.LANCZOS)
    small = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(small).rounded_rectangle([5 * SS, 5 * SS, w * SS - 5 * SS, h * SS - 5 * SS], radius=8 * SS, fill=255)
    inner = small.resize((w, h), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(tinted(inner, (18, 22, 28), 210))
    out.alpha_composite(tinted(ImageChops.subtract(fill, inner), (225, 232, 240), 235))
    return out


def line():
    w, h = 512, 8
    out = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    for x in range(w):
        f = 1 - abs((x - w / 2) / (w / 2)) ** 1.5
        for y in (3, 4):
            out.putpixel((x, y), (255, 255, 255, int(220 * f)))
    return out


def write_model(name):
    model = {"gui_light": "front", "textures": {"layer0": f"destiny:item/hud/{name}"}, "elements": [{
        "from": [0, 0, 8], "to": [16, 16, 8], "faces": {
            f: {"texture": "#layer0", "uv": [0, 0, 16, 16], "tintindex": 0} for f in ("north", "south")}}]}
    item = {"model": {"type": "minecraft:model", "model": f"destiny:gui/hud/{name}",
                      "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}}
    with open(os.path.join(MODELS, name + ".json"), "w") as f:
        json.dump(model, f, indent=2)
    with open(os.path.join(ITEMS, name + ".json"), "w") as f:
        json.dump(item, f, indent=2)


def save(name, img):
    img.save(os.path.join(TEX, name + ".png"), optimize=True)
    write_model(name)


def main():
    for name, rgb in CLASSES.items():
        save(f"rg_class_card_{name}", card(name, rgb))
        save(f"rg_class_icon_{name}", icon(name))
    save("rg_class_glow", glow())
    save("rg_class_dim", veil(70))
    save("rg_class_flash", flash())
    save("rg_class_backdrop", backdrop())
    save("rg_key", key(64, 64))
    save("rg_key_wide", key(192, 64))
    save("rg_line", line())


if __name__ == "__main__":
    main()
