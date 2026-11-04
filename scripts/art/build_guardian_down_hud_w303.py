"""W303: global Guardian Down (death / Ghost revive) HUD art, Destiny 2 style.

Flat tinted HUD quads (destiny:gui/hud/<name>), same format as the W301 class cards:
  gd_ring_bg          dim full revive ring (white, tinted)
  gd_ring_00..gd_ring_24  revive progress arcs, 24 segments with gaps (white, tinted)
  gd_ghost            Ghost shell emblem for the ring centre (white, tinted)
  gd_card             killer card plate: dark glass, cut corner, crimson edge baked in
  gd_icon_fallen      Fallen house sigil (white, tinted)
  gd_icon_hostile     hostile combatant skull mark (white, tinted)
  gd_icon_hazard      environmental warning triangle (white, tinted)
  gd_vignette         full-screen crimson-black vignette (untinted)
  gd_glow             soft round glow behind the ring (white, tinted)
Run: python scripts/art/build_guardian_down_hud_w303.py   (Pillow >= 10)
"""
import json
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src", "main", "resources", "assets", "destiny")
TEX = os.path.join(ROOT, "textures", "item", "hud")
MODELS = os.path.join(ROOT, "models", "gui", "hud")
ITEMS = os.path.join(ROOT, "items", "gui", "hud")
SS = 4
SEGMENTS = 24


def white(alpha):
    out = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
    out.putalpha(alpha)
    return out


def down(big, size):
    return big.resize(size, Image.LANCZOS)


def ring(size, outer, inner, start_deg=None, end_deg=None, gap_deg=0.0, segments=None, filled=None):
    """Alpha mask of a ring (fractions of half-size). With segments: draw the first `filled` arcs."""
    S = size * SS
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    c = S / 2
    ro, ri = outer * c, inner * c
    box = [c - ro, c - ro, c + ro, c + ro]
    if segments is None:
        d.ellipse(box, fill=255)
    else:
        step = 360 / segments
        for i in range(filled):
            a0 = -90 + i * step + gap_deg / 2
            d.pieslice(box, a0, a0 + step - gap_deg, fill=255)
    hole = Image.new("L", (S, S), 0)
    ImageDraw.Draw(hole).ellipse([c - ri, c - ri, c + ri, c + ri], fill=255)
    return down(ImageChops.subtract(m, hole), (size, size))


def ghost_emblem(size=256):
    """Generalist Shell read from the front: four petals around a lens, with a thin ring."""
    S = size * SS
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    c = S / 2
    for k in range(4):
        a = math.radians(45 + 90 * k)
        tip = (c + math.cos(a) * S * .46, c + math.sin(a) * S * .46)
        left = (c + math.cos(a - .55) * S * .19, c + math.sin(a - .55) * S * .19)
        right = (c + math.cos(a + .55) * S * .19, c + math.sin(a + .55) * S * .19)
        mid = (c + math.cos(a) * S * .24, c + math.sin(a) * S * .24)
        d.polygon([left, tip, right, mid], fill=255)
    d.ellipse([c - S * .13, c - S * .13, c + S * .13, c + S * .13], fill=255)
    cut = Image.new("L", (S, S), 0)
    ImageDraw.Draw(cut).ellipse([c - S * .085, c - S * .085, c + S * .085, c + S * .085], fill=255)
    m = ImageChops.subtract(m, cut)
    ImageDraw.Draw(m).ellipse([c - S * .045, c - S * .045, c + S * .045, c + S * .045], fill=255)
    return white(down(m, (size, size)))


def card(w=512, h=128):
    """Killer card: dark glass gradient, cut top-right corner, crimson left edge and hairline."""
    S = SS
    m = Image.new("L", (w * S, h * S), 0)
    cut = 26 * S
    ImageDraw.Draw(m).polygon([(0, 0), (w * S - cut, 0), (w * S, cut), (w * S, h * S), (0, h * S)], fill=255)
    m = down(m, (w, h))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = out.load()
    ma = m.load()
    for y in range(h):
        for x in range(w):
            a = ma[x, y]
            if not a:
                continue
            f = x / w
            base = (14, 10, 12)
            alpha = int(a * (0.86 - 0.62 * f ** 1.4))
            if x < 7:
                base, alpha = (196, 44, 52), a
            elif y < 2 and f < .75:
                base, alpha = (205, 70, 78), int(a * (1 - f / .75) * .9)
            px[x, y] = (*base, max(0, alpha))
    return out


def fallen_sigil(size=256):
    """Fallen house banner sigil: crescent horns over a diamond eye with two stacked bars (abstract)."""
    S = size * SS
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    c = S / 2
    d.ellipse([c - S * .42, c - S * .44, c + S * .42, c + S * .40], fill=255)
    d.ellipse([c - S * .34, c - S * .50, c + S * .34, c + S * .18], fill=0)
    d.polygon([(c, c - S * .12), (c + S * .17, c + S * .08), (c, c + S * .28), (c - S * .17, c + S * .08)], fill=255)
    d.polygon([(c, c - S * .02), (c + S * .07, c + S * .08), (c, c + S * .18), (c - S * .07, c + S * .08)], fill=0)
    for k in (-1, 1):
        d.polygon([(c + k * S * .30, c - S * .40), (c + k * S * .40, c - S * .46), (c + k * S * .38, c - S * .30)], fill=255)
    return white(down(m, (size, size)))


def hostile(size=256):
    """Hostile combatant mark: angular horned skull (Destiny enemy-kill feed style)."""
    S = size * SS
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    c = S / 2
    u = S / 100
    d.polygon([(c - 30 * u, c - 22 * u), (c - 44 * u, c - 44 * u), (c - 16 * u, c - 34 * u)], fill=255)
    d.polygon([(c + 30 * u, c - 22 * u), (c + 44 * u, c - 44 * u), (c + 16 * u, c - 34 * u)], fill=255)
    d.polygon([(c - 30 * u, c - 30 * u), (c + 30 * u, c - 30 * u), (c + 34 * u, c + 6 * u), (c + 18 * u, c + 22 * u),
               (c + 18 * u, c + 40 * u), (c - 18 * u, c + 40 * u), (c - 18 * u, c + 22 * u), (c - 34 * u, c + 6 * u)], fill=255)
    d.polygon([(c - 24 * u, c - 8 * u), (c - 6 * u, c - 2 * u), (c - 10 * u, c + 10 * u), (c - 22 * u, c + 6 * u)], fill=0)
    d.polygon([(c + 24 * u, c - 8 * u), (c + 6 * u, c - 2 * u), (c + 10 * u, c + 10 * u), (c + 22 * u, c + 6 * u)], fill=0)
    d.polygon([(c, c + 12 * u), (c - 4 * u, c + 20 * u), (c + 4 * u, c + 20 * u)], fill=0)
    for k in (-10, 0, 10):
        d.rectangle([c + (k - 2.5) * u, c + 28 * u, c + (k + 2.5) * u, c + 40 * u], fill=0)
    return white(down(m, (size, size)))


def hazard(size=256):
    """Environmental hazard: warning triangle with exclamation."""
    S = size * SS
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    c = S / 2
    d.polygon([(c, c - S * .44), (c + S * .40, c + S * .30), (c - S * .40, c + S * .30)], fill=255)
    d.polygon([(c, c - S * .26), (c + S * .25, c + S * .20), (c - S * .25, c + S * .20)], fill=0)
    d.rectangle([c - S * .035, c - S * .12, c + S * .035, c + S * .07], fill=255)
    d.ellipse([c - S * .04, c + S * .10, c + S * .04, c + S * .18], fill=255)
    return white(down(m, (size, size)))


def vignette(w=480, h=270):
    out = Image.new("RGBA", (w, h))
    px = out.load()
    for y in range(h):
        for x in range(w):
            dx, dy = (x - w / 2) / (w / 2), (y - h / 2) / (h / 2)
            d = math.hypot(dx, dy * .9)
            e = max(0.0, min(1.0, (d - .45) / .75)) ** 1.6
            bottom = max(0.0, (y / h - .62) / .38) ** 2 * .55
            a = min(1.0, e * .78 + bottom)
            px[x, y] = (int(40 * (1 - bottom)), 4, 8, int(255 * a))
    return out.filter(ImageFilter.GaussianBlur(1.2))


def glow(size=256):
    out = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    px = out.load()
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - size / 2, y - size / 2) / (size / 2)
            px[x, y] = (255, 255, 255, int(255 * max(0.0, 1 - d) ** 2.4 * .9))
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
    save("gd_ring_bg", white(ring(256, .96, .84)))
    for i in range(SEGMENTS + 1):
        save(f"gd_ring_{i:02d}", white(ring(256, .96, .84, gap_deg=3.2, segments=SEGMENTS, filled=i)))
    save("gd_ghost", ghost_emblem())
    save("gd_card", card())
    save("gd_icon_fallen", fallen_sigil())
    save("gd_icon_hostile", hostile())
    save("gd_icon_hazard", hazard())
    save("gd_vignette", vignette())
    save("gd_glow", glow())


if __name__ == "__main__":
    main()
