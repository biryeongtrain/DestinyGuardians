#!/usr/bin/env python3
"""Original W45 scope artwork informed by reviewed gameplay, not extracted Bungie sprites.

Requires Pillow. --verify is read-only. Private reference videos are not packed or redistributed.
Sniper frame quad is 3840 square: a large black extension covers through 32:9 while
the aperture stays undistorted. LFR optics are open, NOT black circular sniper masks.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import math
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
ART = ROOT / "art/hud/w45-scope"
IDS = ("bite_of_the_fox", "beloved", "apostate", "line_in_the_sand", "stormchaser")


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def png(image):
    b = io.BytesIO()
    image.save(b, format="PNG")
    return b.getvalue()


def frame(weapon):
    im = Image.new("RGBA", (1024, 1024))
    d = ImageDraw.Draw(im)
    if weapon in IDS[:3]:
        im.paste((0, 0, 0, 255), (0, 0, 1024, 1024))
        if weapon == "beloved":
            # Large circular glass, green etched concentric rings; never a solid opaque lens.
            d.ellipse((296, 296, 728, 728), fill=(20, 34, 28, 255))
            d.ellipse((299, 299, 725, 725), fill=(0, 0, 0, 0), outline=(119, 161, 138, 200), width=1)
            for r in (208, 211):
                d.ellipse((512-r, 512-r, 512+r, 512+r), outline=(101, 155, 131, 90), width=1)
            for a in range(0, 360, 15):
                rad = math.radians(a)
                d.line([(512+math.cos(rad)*202, 512+math.sin(rad)*202),
                        (512+math.cos(rad)*207, 512+math.sin(rad)*207)], fill=(145, 180, 155, 140), width=1)
        elif weapon == "apostate":
            # Hive scope: clipped-corner wide aperture, not the Beloved circular mask.
            outer = [(310, 390), (714, 390), (738, 416), (738, 608), (714, 634),
                     (310, 634), (286, 608), (286, 416)]
            inner = [(312, 394), (712, 394), (733, 418), (733, 606), (712, 630),
                     (312, 630), (291, 606), (291, 418)]
            d.polygon(outer, fill=(64, 83, 43, 255))
            d.polygon(inner, fill=(0, 0, 0, 0))
            d.line(outer+[outer[0]], fill=(139, 160, 91, 255), width=1)
            for sign in (-1, 1):
                x = 512 + sign*158
                d.line([(x, 451), (x+sign*4, 455), (x+sign*4, 569), (x, 573)], fill=(124, 147, 114, 130), width=1)
        else:
            # Iron Banner footage has a wide rounded-rectangle view, not a generic circular tube.
            d.rounded_rectangle((287, 386, 737, 638), radius=25, fill=(12, 15, 14, 255))
            d.rounded_rectangle((293, 392, 731, 632), radius=21, fill=(0, 0, 0, 0),
                                outline=(120, 132, 115, 170), width=1)
            for sign in (-1, 1):
                x = 512 + sign*199
                for y in (470, 488, 512, 536, 554):
                    d.line([(x, y), (x-sign*5, y)], fill=(148, 153, 135, 150), width=1)
    else:
        raise ValueError("LFR optics are real 3D models, not HUD frames")
    return im


def reticle(weapon):
    # High-resolution red/orange sight; all aim marks resolve to virtual960,540.
    # The chevron's TIP, not its bounding-box centre, is the actual aiming point.
    im = Image.new("RGBA", (512, 512))
    d = ImageDraw.Draw(im)
    color = (239, 92, 79, 255)
    if weapon == "bite_of_the_fox":
        color = (245, 151, 91, 255)
        d.line([(184, 334), (256, 256), (328, 334)], fill=color, width=15, joint="curve")
    elif weapon in ("beloved", "apostate"):
        d.ellipse((222, 222, 290, 290), outline=color, width=12)
        if weapon == "apostate":
            for x in (-1, 1):
                d.line([(256+x*98, 256), (256+x*185, 256)], fill=(157, 179, 151, 230), width=6)
    elif weapon == "line_in_the_sand":
        color = (235, 128, 158, 255)
        d.ellipse((235, 235, 277, 277), outline=color, width=10)
        for x in (-1, 1):
            d.line([(256+x*80, 275), (256+x*118, 275)], fill=color, width=6)
    else:
        color = (243, 164, 89, 255)
        d.ellipse((246, 246, 266, 266), fill=color)
        for x in (-1, 1):
            d.line([(256+x*78, 278), (256+x*117, 278)], fill=color, width=8)
    # Thin dark keyline, original-authored; no solid centre for hollow-ring optics.
    alpha = im.getchannel("A")
    outlined = Image.new("RGBA", im.size, (0, 0, 0, 0))
    outlined.paste((6, 9, 10, 170), (0, 0), alpha.filter(ImageFilter.MaxFilter(9)))
    outlined.alpha_composite(im)
    return outlined.resize((128, 128), Image.Resampling.LANCZOS)


def generate():
    output = {}
    # Vanilla 26.3 sprite dimensions, checked against the local client JAR. Hide only the
    # sprite cross/attack cooldown, not world rendering, inventory or user GUI settings.
    for name, size in {"crosshair": (15, 15), "crosshair_attack_indicator_background": (16, 4),
                       "crosshair_attack_indicator_full": (16, 16),
                       "crosshair_attack_indicator_progress": (16, 4)}.items():
        path = ROOT / f"src/main/resources/assets/minecraft/textures/gui/sprites/hud/{name}.png"
        output[path] = png(Image.new("RGBA", size))
    sheet = Image.new("RGB", (1000, 300*5), (58, 63, 68))
    for row, weapon in enumerate(IDS):
        sniper = weapon in IDS[:3]
        mask, sight = frame(weapon) if sniper else None, reticle(weapon)
        view = Image.new("RGBA", (960, 540), (108, 120, 115, 255))
        if sniper:
            size = 1920
            preview = mask.resize((size, size), Image.Resampling.LANCZOS)
            view.alpha_composite(preview, (480-size//2, 270-size//2))
        else:
            ImageDraw.Draw(view).text((100, 400), "3D held optic - inspect actual gameplay PNG, not this flat design sheet", fill="white")
        view.alpha_composite(sight.resize((40, 40)), (460, 250))
        sheet.paste(view.convert("RGB").resize((480, 270)), (0, row*300))
        ImageDraw.Draw(sheet).text((500, row*300+35), weapon, fill="white")
        for part, texture in (("frame", mask), ("reticle", sight)):
            if texture is None:
                continue
            name = f"scope_w45_{weapon}_{part}"
            key = "gui/hud/"+name
            output[ASSETS/f"textures/item/hud/{name}.png"] = png(texture)
            output[ASSETS/f"models/{key}.json"] = encode({
                "gui_light": "front", "textures": {"0": "destiny:item/hud/"+name,
                                                        "particle": "destiny:item/hud/"+name},
                "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "faces": {
                    face: {"texture": "#0", "uv": [0, 0, 16, 16], "tintindex": 0}
                    for face in ("north", "south")}}]})
            output[ASSETS/f"items/{key}.json"] = encode({"model": {
                "type": "minecraft:model", "model": "destiny:"+key,
                "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}})
    contact = io.BytesIO()
    sheet.save(contact, "JPEG", quality=92)
    output[ART/"design-contact.jpg"] = contact.getvalue()
    output[ART/"manifest.json"] = encode({
        "generator": "scripts/generate_scope_hud_w45.py", "ids": list(IDS),
        "artwork": "Original redraw; gameplay-informed approximation, not extracted/pixel-exact official sprites",
        "aimPoint": [960, 540], "sniperFrameSize": 3840, "linearFrame": "Real 3D held optics; no HUD receiver",
        "layers": "Frame normal depth0, reticle aboveHand depth6; existing ammo/vitals above mask",
        "perspectiveLimitation": "Vanilla server cannot observe F5; HUD follows ADS in all perspectives",
        "vanillaCrosshair": "Transparent cross and attack-indicator sprites; ordinary tools/hands/supers keep FallbackAimHud dot",
        "sha256": {str(path.relative_to(ROOT)): hashlib.sha256(data).hexdigest() for path, data in output.items()},
    })
    return output


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    for path, data in generate().items():
        if args.verify:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit("W45 output differs: "+str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print("Verified W45 scope HUD" if args.verify else "Generated W45 scope HUD")
