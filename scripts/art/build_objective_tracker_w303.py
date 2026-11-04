"""W303: Destiny 2 style campaign objective tracker sprites (destiny:gui/hud/<name>, tinted via custom_model_data).

  ot_bg        left-anchored dark glass, fades out to the right and at top/bottom (untinted)
  ot_box       objective checkbox outline (white, tinted)
  ot_box_fill  completed checkbox: filled square with an inset check (white, tinted)
  ot_bar       solid bar for progress track/fill (white, tinted)
  ot_icon      story mission sigil: diamond in a broken ring (white, tinted)
  ot_rule      separator line fading out to the right (white, tinted)
  ot_key       keycap plate for button prompts (white, tinted)
  ot_header    story mission header bar: blue, bright top edge, fades out to the right (untinted)
  ot_shield    story mission shield emblem with the Traveler mark (untinted)
Run: python scripts/art/build_objective_tracker_w303.py   (Pillow >= 10)
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src", "main", "resources", "assets", "destiny")
TEX = os.path.join(ROOT, "textures", "item", "hud")
MODELS = os.path.join(ROOT, "models", "gui", "hud")
ITEMS = os.path.join(ROOT, "items", "gui", "hud")
SS = 4


def white(alpha):
    out = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
    out.putalpha(alpha)
    return out


def bg(w=512, h=128):
    out = Image.new("RGBA", (w, h))
    px = out.load()
    for y in range(h):
        v = min(1.0, min(y, h - 1 - y) / (h * 0.22)) ** 1.2
        for x in range(w):
            u = x / (w - 1)
            a = (1 - u) ** 1.35 * 0.62 + max(0.0, 0.12 - u) * 0.6
            px[x, y] = (6, 9, 13, int(255 * min(1, a) * v))
    return out


def box(fill=False, size=64):
    S = size * SS
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    t = S * 0.11
    d.rectangle([0, 0, S - 1, S - 1], fill=255)
    if not fill:
        d.rectangle([t, t, S - 1 - t, S - 1 - t], fill=0)
    else:
        # inset check mark cut out of the filled square
        pts = [(S * .24, S * .52), (S * .42, S * .70), (S * .78, S * .30)]
        d.line(pts, fill=0, width=int(S * .12), joint="curve")
    return white(m.resize((size, size), Image.LANCZOS))


def bar():
    return white(Image.new("L", (16, 16), 255))


def icon(size=128):
    S = size * SS
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    c = S / 2
    r = S * .46
    for k in range(4):
        a0 = 45 + k * 90 + 14
        d.arc([c - r, c - r, c + r, c + r], a0, a0 + 62, fill=255, width=int(S * .06))
    q = S * .27
    d.polygon([(c, c - q), (c + q, c), (c, c + q), (c - q, c)], fill=255)
    q2 = S * .12
    d.polygon([(c, c - q2), (c + q2, c), (c, c + q2), (c - q2, c)], fill=0)
    return white(m.resize((size, size), Image.LANCZOS))


def rule(w=512, h=8):
    out = Image.new("RGBA", (w, h))
    px = out.load()
    for x in range(w):
        a = (1 - x / (w - 1)) ** 1.1
        for y in range(h):
            px[x, y] = (255, 255, 255, int(255 * a))
    return out


def key(w=192, h=64):
    S = SS
    m = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=10 * S, fill=110)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=10 * S, outline=255, width=3 * S)
    return white(m.resize((w, h), Image.LANCZOS))


def header(w=768, h=64):
    out = Image.new("RGBA", (w, h))
    px = out.load()
    for x in range(w):
        u = x / (w - 1)
        fade = 1.0 if u < .55 else max(0.0, 1 - (u - .55) / .45) ** 1.4
        for y in range(h):
            t = y / (h - 1)
            edge = 1.0 if y < 2 or y > h - 3 else 0.0
            r, g, b = (40 + 30 * (1 - t), 70 + 40 * (1 - t), 150 + 45 * (1 - t))
            if edge: r, g, b = 150, 185, 245
            a = (0.92 if not edge else 0.95) * fade
            px[x, y] = (int(r), int(g), int(b), int(255 * a))
    return out


def shield(size=128):
    S = size * SS
    m = Image.new("L", (S, S), 0)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    c = S / 2
    outline = [(S * .08, S * .06), (S * .92, S * .06), (S * .92, S * .58), (c, S * .96), (S * .08, S * .58)]
    d.polygon(outline, fill=(236, 240, 248, 255))
    inner = [(S * .15, S * .13), (S * .85, S * .13), (S * .85, S * .55), (c, S * .87), (S * .15, S * .55)]
    d.polygon(inner, fill=(36, 70, 156, 255))
    # Traveler-style mark: sphere over a Y of three blades
    w = (238, 242, 250, 255)
    d.ellipse([c - S * .09, S * .22, c + S * .09, S * .40], fill=w)
    d.polygon([(S * .27, S * .30), (S * .37, S * .30), (c - S * .02, S * .55), (c - S * .07, S * .55)], fill=w)
    d.polygon([(S * .73, S * .30), (S * .63, S * .30), (c + S * .02, S * .55), (c + S * .07, S * .55)], fill=w)
    d.polygon([(c - S * .05, S * .50), (c + S * .05, S * .50), (c + S * .03, S * .76), (c - S * .03, S * .76)], fill=w)
    return out.resize((size, size), Image.LANCZOS)


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
    save("ot_bg", bg())
    save("ot_box", box(False))
    save("ot_box_fill", box(True))
    save("ot_bar", bar())
    save("ot_icon", icon())
    save("ot_rule", rule())
    save("ot_key", key())
    save("ot_header", header())
    save("ot_shield", shield())


if __name__ == "__main__":
    main()
