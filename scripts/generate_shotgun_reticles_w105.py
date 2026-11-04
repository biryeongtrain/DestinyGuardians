#!/usr/bin/env python3
"""Generate W105 historical S19 image-informed shotgun HUD adaptations with Pillow.

Requires Pillow 12.3.0 for the published PNG bytes. No network, runtime or build.
--output-root DIR creates the same relative paths in an independent output tree.
--verify renders in memory and compares every expected file without writing.
The contact sheet is a design reference, never native or in-game evidence.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import math

from PIL import Image, ImageDraw, ImageFont, __version__ as PILLOW_VERSION

ROOT = Path(__file__).resolve().parents[1]
ART = Path("art/hud/w105-shotgun")
ASSETS = Path("src/main/resources/assets/destiny")
SIZE = 128
SUPERSAMPLE = 8
STROKE = 1.75
OUTER_STROKE = 1.25
OUTER_ALPHA = 190
FRAMES = ("aggressive", "precision", "lightweight", "rapid_fire")
SOURCE = "https://www.bungie.net/7/en/News/article/51999"
SOURCE_CONTRACT = "art/weapons/w105/references/CONTRACT.md"
# Motifs visually informed by the official S19 PNGs; dimensions are authored,
# approximately normalized from the illustrations, not extracted pixel contours.
GEOMETRY = {
    "aggressive": {"outline": "seven_separated_bent_segments", "radii": [51, 51],
                   "centerCircleRadius": 16.5, "cornerCount": 7, "edgeFraction": 0.21},
    "precision": {"outline": "four_separated_oval_arcs", "radii": [31, 46],
                  "centerCircleRadius": 14.5,
                  "arcDegrees": [[-120, -60], [-15, 15], [60, 120], [165, 195]]},
    "lightweight": {"outline": "four_separated_diamond_corners", "radii": [43, 39],
                    "centerCircleRadius": 18, "edgeFraction": 0.28},
    "rapid_fire": {"outline": "four_separated_square_brackets", "radii": [26, 26],
                   "centerCircleRadius": 16, "bracketArm": 14},
}
REFERENCE_IMAGES = {
    "aggressive": ("ShotgunSpreadAggressive.png", "af97f626d2652043263750561ce300b133f41814921c9d9b2ce7c835a71d79fe"),
    "precision": ("ShotgunSpreadPrecision.png", "27882f386298fa0e6624309550e304bb9b0ae0894c2e0d6102207da34cb7c157"),
    "lightweight": ("ShotgunSpreadLightweight.png", "fc15943e99e082e0ed6c4c14986359fdb2d0f5c8597ce2d689d518f99304e60a"),
    "rapid_fire": ("ShotgunSpreadsRapidFire.png", "e31a992ecadba08dbe2407bc6a18f1038cf0844b897a4bfc5dc93058f62f8f47"),
}
HISTORICAL_PATTERNS = {
    "aggressive": "fixed evenly distributed cone; reticle circles and segments are not pellet marks",
    "precision": "vertical oval",
    "lightweight": "diamond",
    "rapid_fire": "square",
}


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def png(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=False, compress_level=9)
    return buffer.getvalue()


def texture(frame):
    """White vector strokes with alpha coverage, redrawn from observed motifs.

    All frames have a central circle and disconnected outer strokes. Reference
    impact marks/backgrounds are omitted; the existing aim-point node owns the
    empty center. Reference files are provenance, not generator dependencies.
    """
    geometry = GEOMETRY[frame]
    rx, ry = geometry["radii"]
    side = SIZE * SUPERSAMPLE
    ink = Image.new("L", (side, side))
    draw = ImageDraw.Draw(ink)

    def line(points):
        draw.line([(round(x * SUPERSAMPLE - 0.5), round(y * SUPERSAMPLE - 0.5))
                   for x, y in points], fill=OUTER_ALPHA,
                  width=round(OUTER_STROKE * SUPERSAMPLE), joint="curve")

    def separated_corners(vertices, fraction):
        for i, vertex in enumerate(vertices):
            previous, following = vertices[i - 1], vertices[(i + 1) % len(vertices)]
            arms = [(vertex[0] + (other[0] - vertex[0]) * fraction,
                     vertex[1] + (other[1] - vertex[1]) * fraction)
                    for other in (previous, following)]
            line([arms[0], vertex, arms[1]])

    if frame == "aggressive":
        vertices = [(64 + rx * math.cos(-math.pi / 2 + i * math.tau / 7),
                     64 + ry * math.sin(-math.pi / 2 + i * math.tau / 7))
                    for i in range(geometry["cornerCount"])]
        separated_corners(vertices, geometry["edgeFraction"])
    elif frame == "precision":
        for start, end in geometry["arcDegrees"]:
            line([(64 + rx * math.cos(math.radians(angle / 4)),
                   64 + ry * math.sin(math.radians(angle / 4)))
                  for angle in range(start * 4, end * 4 + 1)])
    elif frame == "lightweight":
        separated_corners([(64, 64 - ry), (64 + rx, 64),
                           (64, 64 + ry), (64 - rx, 64)], geometry["edgeFraction"])
    elif frame == "rapid_fire":
        arm = geometry["bracketArm"]
        for sx in (-1, 1):
            for sy in (-1, 1):
                line([(64 + sx * (rx - arm), 64 + sy * ry),
                      (64 + sx * rx, 64 + sy * ry),
                      (64 + sx * rx, 64 + sy * (ry - arm))])
    else:
        raise ValueError(frame)

    # Analytic annulus at pixel centers avoids a baked central dot and keeps the
    # small central circle centered about (64,64), independently of outer motifs.
    radius = geometry["centerCircleRadius"]
    coords = [(i + 0.5) / SUPERSAMPLE - SIZE / 2 for i in range(side)]
    ring = bytearray(side * side)
    for y, dy in enumerate(coords):
        for x, dx in enumerate(coords):
            if (radius - STROKE) ** 2 <= dx * dx + dy * dy <= radius ** 2:
                ring[y * side + x] = 255
    ink.paste(255, (0, 0, side, side), Image.frombytes("L", (side, side), bytes(ring)))
    alpha = ink.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    image = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 0))
    image.putalpha(alpha)
    return image


def model(name):
    # W44 contract: one zero-depth element, north/south faces, tint index zero.
    return {
        "gui_light": "front",
        "textures": {"0": f"destiny:item/hud/{name}"},
        "elements": [{
            "from": [0, 0, 8], "to": [16, 16, 8],
            "faces": {face: {"texture": "#0", "uv": [0, 0, 16, 16], "tintindex": 0}
                      for face in ("north", "south")},
        }],
    }


def item(name):
    return {"model": {
        "type": "minecraft:model", "model": f"destiny:gui/hud/{name}",
        "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}],
    }}


def contact_sheet(images):
    """Show native texture pixels and a small white/tinted readability study."""
    sheet = Image.new("RGB", (960, 400), (20, 27, 37))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((20, 15), "W105 SHOTGUN | OFFICIAL S19 IMAGE-INFORMED ADAPTATIONS", font=font, fill="white")
    draw.text((20, 36), "DESIGN REFERENCE - NOT NATIVE / NOT IN-GAME / NOT PIXEL-EXACT", font=font, fill=(190, 202, 217))
    for i, frame in enumerate(FRAMES):
        x = i * 240
        draw.rounded_rectangle((x + 12, 68, x + 227, 349), radius=8, fill=(30, 39, 51))
        sheet.paste(images[frame], (x + 56, 82), images[frame])
        draw.text((x + 22, 220), frame.replace("_", " ").upper(), font=font, fill="white")
        draw.text((x + 22, 240), {"aggressive": "circle + 7 bent segments", "precision": "circle + 4 oval arcs", "lightweight": "circle + diamond corners", "rapid_fire": "circle + square brackets"}[frame], font=font, fill=(190, 202, 217))
        for j, tint in enumerate(((255, 255, 255), (246, 214, 107), (232, 92, 80))):
            preview = Image.new("RGBA", (48, 48), (*tint, 0))
            preview.putalpha(images[frame].getchannel("A").resize((48, 48), Image.Resampling.LANCZOS))
            sheet.paste(preview, (x + 24 + j * 61, 277), preview)
    draw.text((20, 365), "Official historical reticle motifs redrawn procedurally. Dimensions authored; impact marks and center dot omitted.", font=font, fill=(190, 202, 217))
    draw.text((20, 382), "128px textures above; 48px tint studies below. Existing separate aim-point node is omitted from this sheet.", font=font, fill=(190, 202, 217))
    return sheet


def generate():
    """Return relative paths and deterministic bytes without accessing disk."""
    output, images, entries = {}, {}, {}
    for frame in FRAMES:
        name = "reticle_w105_shotgun_" + frame
        paths = {
            "texture": ASSETS / f"textures/item/hud/{name}.png",
            "item": ASSETS / f"items/gui/hud/{name}.json",
            "model": ASSETS / f"models/gui/hud/{name}.json",
        }
        images[frame] = texture(frame)
        output[paths["texture"]] = png(images[frame])
        output[paths["item"]] = encode(item(name))
        output[paths["model"]] = encode(model(name))
        entries[frame] = {
            "image": name, "modelId": f"destiny:gui/hud/{name}",
            "paths": {key: path.as_posix() for key, path in paths.items()},
            "historicalPelletPattern": HISTORICAL_PATTERNS[frame],
            "authoredGeometry": {**GEOMETRY[frame], "center": [64, 64], "circleStrokePixels": STROKE,
                                 "outerStrokePixels": OUTER_STROKE, "outerAlpha": OUTER_ALPHA},
        }
    # Exactly the twelve pack files, each with a literal SHA-256 in the manifest.
    asset_hashes = {path.as_posix(): hashlib.sha256(data).hexdigest()
                    for path, data in sorted(output.items())}
    sheet = png(contact_sheet(images))
    output[ART / "contact-sheet.png"] = sheet
    output[ART / "manifest.json"] = encode({
        "schemaVersion": 2,
        "generator": "scripts/generate_shotgun_reticles_w105.py",
        "originalArtwork": False,
        "proceduralRedraw": True,
        "style": "Historical S19 image-informed procedural adaptation; not pixel-exact or current-2026-exact.",
        "provenance": {
            "sourceContract": SOURCE_CONTRACT,
            "primarySource": SOURCE, "primarySourceDate": "2022-12-01",
            "sourceScope": "Historical S19 reticle motifs visually inspected in four official Bungie illustrations.",
            "referenceImagesUsed": [
                {"frame": frame, "path": f"run/private-sources/w105/{frame}.png",
                 "url": f"https://www.bungie.net/pubassets/pkgs/172/172233/{REFERENCE_IMAGES[frame][0]}?av=1243294923&cv=3983621215",
                 "sha256": REFERENCE_IMAGES[frame][1], "size": [250, 250],
                 "use": "Visual motif reference only; source pixels are not copied into outputs."}
                for frame in FRAMES
            ],
            "referenceLimit": "Official historical PNGs inspected. Authored stroke dimensions, spacing and alpha; no pixel-exact reproduction or unchanged-2026 claim.",
            "unchanged2026BehaviorProven": False,
            "aggressiveBoundary": "Central circle with seven separated outer bent segments follows the historical reticle motif; it does not imply a hollow pellet distribution.",
            "authoredNotMeasured": ["normalized motif dimensions", "arc spans and gaps", "stroke", "alpha", "antialiasing", "HUD screen size"],
            "unknowns": ["unchanged current-2026 reticle appearance", "physical pellet coordinates", "spread angles", "universal ADS scalar"],
        },
        "renderer": {"library": "Pillow", "version": PILLOW_VERSION, "supersample": SUPERSAMPLE, "downsample": "LANCZOS"},
        "textureSize": [SIZE, SIZE], "frames": entries,
        "hudContract": {
            "maxHudNodes": 2, "additionalHudNodes": 0,
            "frameNodes": 1, "existingSeparateCenterNodes": 1,
            "centerOpening": "Transparent central 12x12 pixels inside the circle; no baked aim point or pellet dots.",
            "color": "Pure white RGB with alpha coverage; custom_model_data tint index 0.",
            "quad": "W44 one zero-depth 0,0,8 to 16,16,8 element; north and south faces.",
            "integration": "Assets only; caller owns model selection and any runtime size feedback.",
            "ballistics": "No physical pellet coordinates or ADS calibration encoded in these textures.",
            "slug": "Existing W44 pinpoint-slug assets unchanged and not regenerated.",
        },
        "maxHudNodes": 2,
        "assetCount": 12, "sha256": asset_hashes,
        "designReference": {
            "path": (ART / "contact-sheet.png").as_posix(),
            "sha256": hashlib.sha256(sheet).hexdigest(),
            "nativeEvidence": False, "inGameScreenshot": False,
        },
    })
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT,
                        help="Independent destination root; same relative output paths as the repository.")
    parser.add_argument("--verify", action="store_true", help="Compare in memory; do not write or repair any file.")
    args = parser.parse_args()
    root = args.output_root.resolve()
    result = generate()
    if args.verify:
        errors = []
        for relative, data in result.items():
            path = root / relative
            if not path.is_file() or path.read_bytes() != data:
                errors.append(f"Missing or different: {relative}")
        for directory, extension in (("textures/item/hud", "png"), ("items/gui/hud", "json"), ("models/gui/hud", "json")):
            for path in (root / ASSETS / directory).glob(f"reticle_w105_shotgun_*.{extension}"):
                if path.relative_to(root) not in result:
                    errors.append(f"Unexpected W105 asset: {path.relative_to(root)}")
        if errors:
            raise SystemExit("\n".join(errors))
    else:
        for relative, data in result.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f"{'Verified read-only' if args.verify else 'Generated'} 12 W105 pack assets + manifest + design contact sheet in {root}")


if __name__ == "__main__":
    main()
