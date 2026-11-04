#!/usr/bin/env python3
"""Draw original W44 reticles and vanilla flat-quad models; no downloaded/extracted art.

Run with a Python containing Pillow. --verify compares all outputs without writing.
The contact sheet is a design reference, not an in-game screenshot or pixel-exact claim.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/hud/w44-reticle"
ASSETS = ROOT / "src/main/resources/assets/destiny"
SIZE = 128
SUPERSAMPLE = 4
FAMILIES = (
    "hand_cannon", "sidearm", "auto_rifle", "pulse_rifle", "submachine_gun", "machine_gun",
    "scout_rifle", "sniper_rifle", "linear_fusion_rifle", "shotgun", "shotgun_slug",
    "fusion_rifle", "trace_rifle", "bow", "grenade_launcher", "heavy_grenade_launcher",
    "rocket_launcher",
)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def png(image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def texture(name):
    """Draw in normalized 128px coordinates with a transparent, unobstructed centre."""
    ink = Image.new("L", (SIZE * SUPERSAMPLE, SIZE * SUPERSAMPLE))
    draw = ImageDraw.Draw(ink)

    def points(values):
        return [(round(x * SUPERSAMPLE), round(y * SUPERSAMPLE)) for x, y in values]

    def line(values, width=2):
        draw.line(points(values), fill=255, width=round(width * SUPERSAMPLE), joint="curve")

    def ellipse(box, width=2, filled=False):
        box = tuple(round(v * SUPERSAMPLE) for v in box)
        draw.ellipse(box, fill=255 if filled else None, outline=255, width=round(width * SUPERSAMPLE))

    def arc(start, end, radius=43, width=2):
        box = tuple(round(v * SUPERSAMPLE) for v in (64-radius, 64-radius, 64+radius, 64+radius))
        draw.arc(box, start=start, end=end, fill=255, width=round(width * SUPERSAMPLE))

    def cross(gap=32, edge=49, width=2):
        for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            line([(64+x*gap, 64+y*gap), (64+x*edge, 64+y*edge)], width)

    def brackets(radius=43, arm=14, width=2):
        for x, y in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            line([(64+x*(radius-arm), 64+y*radius), (64+x*radius, 64+y*radius),
                  (64+x*radius, 64+y*(radius-arm))], width)

    if name == "dot":
        ellipse((24, 24, 104, 104), filled=True)
    elif name == "hand_cannon":
        ellipse((21, 21, 107, 107), 2.4)
    elif name == "sidearm":
        ellipse((25, 25, 103, 103), 2.5)
        line([(64, 17), (64, 22)], 2)
        line([(64, 106), (64, 111)], 2)
    elif name in ("auto_rifle", "pulse_rifle", "submachine_gun", "machine_gun"):
        if name == "auto_rifle":
            for angle in range(0, 360, 90):
                arc(angle+13, angle+77, width=2.6)
        elif name == "pulse_rifle":
            for angle in range(0, 360, 90):
                arc(angle+16, angle+38, width=2.6)
                arc(angle+52, angle+74, width=2.6)
        elif name == "submachine_gun":
            cross(31, 49, 2.6)
            for angle in range(0, 360, 90):
                arc(angle+30, angle+60, radius=40, width=2)
        else:
            brackets(43, 21, 2.8)
            cross(35, 45, 2)
    elif name == "scout_rifle":
        cross(26, 47, 2.4)
        ellipse((51, 51, 77, 77), 1.7)
    elif name == "sniper_rifle":
        cross(25, 54, 2.3)
        # The central opening stays clear when ADS contracts the precision frame.
        line([(55, 83), (64, 74), (73, 83)], 1.8)
    elif name == "linear_fusion_rifle":
        line([(64, 23), (105, 64), (64, 105), (23, 64), (64, 23)], 2.3)
        cross(47, 55, 2)
    elif name == "shotgun":
        ellipse((17, 17, 111, 111), 1.8)
        cross(43, 51, 2)
    elif name == "shotgun_slug":
        ellipse((28, 28, 100, 100), 2.4)
        line([(64, 14), (75, 25), (64, 36), (53, 25), (64, 14)], 2)
    elif name == "fusion_rifle":
        line([(32, 24), (18, 24), (18, 104), (32, 104)], 2.6)
        line([(96, 24), (110, 24), (110, 104), (96, 104)], 2.6)
        for y in (44, 64, 84):
            line([(31, y), (40, y)], 2)
            line([(88, y), (97, y)], 2)
    elif name == "trace_rifle":
        ellipse((35, 35, 93, 93), 2.3)
        cross(37, 52, 2.3)
    elif name == "bow":
        line([(21, 49), (21, 32), (38, 32)], 2.4)
        line([(107, 49), (107, 32), (90, 32)], 2.4)
        line([(37, 95), (64, 77), (91, 95)], 2.4)
        line([(64, 96), (64, 106)], 2)
    elif name in ("grenade_launcher", "heavy_grenade_launcher"):
        # Open upper arc and short drop ladder suggest a lobbed projectile without a ballistic promise.
        arc(198, 342, radius=43, width=2.5)
        line([(64, 81), (64, 110)], 2.3)
        line([(53, 91), (75, 91)], 2.3)
        line([(57, 105), (71, 105)], 2.3)
        if name == "heavy_grenade_launcher":
            line([(18, 65), (18, 82), (29, 82)], 2.5)
            line([(110, 65), (110, 82), (99, 82)], 2.5)
    elif name == "rocket_launcher":
        brackets(45, 17, 2.6)
        ellipse((43, 43, 85, 85), 2)
    else:
        raise ValueError(name)

    # An original dark keyline improves readability on light surfaces using the same two quads.
    outline = ink.filter(ImageFilter.MaxFilter(9))
    image = Image.new("RGBA", ink.size)
    image.paste((0, 0, 0, 200), (0, 0), outline)
    image.paste((255, 255, 255, 255), (0, 0), ink)
    return image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def generate():
    output = {}
    images = {}
    for shape in (*FAMILIES, "dot"):
        name = "reticle_w44_" + shape
        key = "gui/hud/" + name
        images[shape] = texture(shape)
        output[ASSETS / f"textures/item/hud/{name}.png"] = png(images[shape])
        output[ASSETS / f"models/{key}.json"] = encode({
            "gui_light": "front", "textures": {"0": f"destiny:item/hud/{name}"},
            "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "faces": {
                face: {"texture": "#0", "uv": [0, 0, 16, 16], "tintindex": 0}
                for face in ("north", "south")}}],
        })
        output[ASSETS / f"items/{key}.json"] = encode({"model": {
            "type": "minecraft:model", "model": "destiny:" + key,
            "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}],
        }})

    # Large atlas for inspection; textures themselves contain no labels or icon silhouettes.
    sheet = Image.new("RGBA", (5 * 240, 4 * 220), (22, 29, 39, 255))
    labels = ImageDraw.Draw(sheet)
    for i, shape in enumerate(FAMILIES):
        x, y = (i % 5) * 240, (i // 5) * 220
        sheet.alpha_composite(images[shape], (x+56, y+28))
        sheet.alpha_composite(images["dot"].resize((9, 9), Image.Resampling.LANCZOS), (x+116, y+88))
        labels.text((x+12, y+176), shape.replace("_", " "), fill=(230, 235, 243))
    labels.text((12, 848), "W44 original procedural reticles | style study, not pixel-exact | sword/glaive excluded", fill=(180, 193, 211))
    output[ART / "contact-sheet.png"] = png(sheet)
    output[ART / "manifest.json"] = encode({
        "originalArtwork": True,
        "provenance": "Original procedural geometry. No Bungie or other third-party sprites, screenshots or icons used.",
        "style": "Destiny-inspired family readability; no pixel-exact reproduction claim.",
        "generator": "scripts/generate_weapon_reticle_w44.py",
        "textureSize": [SIZE, SIZE],
        "maxHudNodes": 2,
        "shapes": list(FAMILIES) + ["dot"],
        "excludedFamilies": ["sword", "glaive"],
        "sha256": {str(path.relative_to(ROOT)): hashlib.sha256(data).hexdigest()
                   for path, data in output.items()},
    })
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = generate()
    for path, data in result.items():
        if args.verify:
            if not path.exists() or path.read_bytes() != data:
                raise SystemExit(f"W44 asset differs or is missing: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f"{'Verified' if args.verify else 'Generated'} {len(result)} W44 reticle files ({len(FAMILIES)+1} original textures)")
