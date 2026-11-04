#!/usr/bin/env python3
"""Generate W45 scope wrappers and source-cloned LFR optics; --verify never writes.

Only the live Polymer model getter should select these wrappers for pose 'scope'.
Requires Pillow. Real ITEM_MODEL stays original. All non-first-person contexts reuse the exact
original ADS subtree, including the independent boolean-index-0 grip condition.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
IDS = ("bite_of_the_fox", "beloved", "apostate", "line_in_the_sand", "stormchaser")
FIRST_PERSON = ("firstperson_righthand", "firstperson_lefthand")
LFRS = ("line_in_the_sand", "stormchaser")
CLIP_Y = 11.2
OPTIC_CENTER = (8, 12.7)
VIOLET_TINT = 0xB777FF
BRONZE_TINT = 0xE8C08A


def texture_samples(path, weapon_id):
    """Use opaque original texels only, with sub-texel UVs to avoid atlas bleed."""
    with Image.open(path) as source:
        image = source.convert("RGBA")
    colors = [color for count, color in image.getcolors(image.width * image.height) if color[3] == 255]
    # Original textures are nearly monochrome. Tint only the new inner trim via
    # vanilla per-face tinting; original body faces and original textures stay untouched.
    targets = {"pale": (216, 212, 210), "violet": (216, 212, 210), "metal": (115, 115, 123)}
    if weapon_id == "stormchaser":
        targets.pop("violet")
        targets["bronze"] = (184, 166, 141)
    chosen = {name: min(colors, key=lambda color: (sum((color[i] - target[i]) ** 2 for i in range(3)), color))
              for name, target in targets.items()}
    locations = {}
    pixels = image.load()
    for index in range(image.width * image.height):
        color = pixels[index % image.width, index // image.width]
        if color in chosen.values() and color not in locations:
            locations[color] = (index % image.width, index // image.width)
        if len(locations) == len(set(chosen.values())):
            break
    samples = {}
    for name, color in chosen.items():
        x, y = locations[color]
        samples[name] = {"rgba": list(color), "pixel": [x, y], "uv": [
            (x + .25) * 16 / image.width, (y + .25) * 16 / image.height,
            (x + .75) * 16 / image.width, (y + .75) * 16 / image.height]}
        if name == "violet":
            samples[name]["tintRgb"] = VIOLET_TINT
        elif weapon_id == "stormchaser" and name in ("bronze", "pale"):
            samples[name]["tintRgb"] = BRONZE_TINT
    return samples


def optic_parts(weapon_id, samples):
    pieces = []

    def box(name, low, high, material):
        tint = {"tintindex": 0} if "tintRgb" in samples[material] else {}
        pieces.append({"name": "w45_" + name, "from": low, "to": high,
                       "faces": {face: {"uv": samples[material]["uv"], "texture": "#0", **tint}
                                 for face in ("north", "south", "east", "west", "up", "down")}})

    def segment(name, start, end, width, z0, z1, material):
        """One smooth rectangular beam; 26.3 accepts arbitrary single-axis angles.

        Rotation is around the beam midpoint, without rescale. Tiny endpoint overlap
        closes adjacent short-curve joins without stair-step axis-aligned blocks.
        """
        cx, cy = ((start[i] + end[i]) / 2 for i in (0, 1))
        dx, dy = (end[i] - start[i] for i in (0, 1))
        length = math.hypot(dx, dy) + .02
        box(name, [round(cx - width / 2, 6), round(cy - length / 2, 6), z0],
            [round(cx + width / 2, 6), round(cy + length / 2, 6), z1], material)
        pieces[-1]["rotation"] = {"origin": [round(cx, 6), round(cy, 6), round((z0 + z1) / 2, 6)],
                                  "axis": "z", "angle": round(-math.degrees(math.atan2(dx, dy)), 6),
                                  "rescale": False}

    # The pedestal reaches into the existing stock, below the clear sight line.
    box("mount", [7.6, 10.6, 12.35], [8.4, 11.6, 13.35], "metal")
    if weapon_id == "line_in_the_sand":
        # Thin continuous trapezoid, narrow at top. Its purple inlay is also a
        # continuous angled beam, never an axis-aligned stair or a filled lens.
        box("outer_bottom", [6.34, 11.44, 12.65], [9.66, 11.56, 13.15], "pale")
        box("outer_top", [6.94, 13.94, 12.65], [9.06, 14.06, 13.15], "pale")
        for side in (0, 1):
            reflect = lambda x: x if side == 0 else 16 - x
            segment(f"outer_{side}", [reflect(6.4), 11.5], [reflect(7.0), 14.0], .12, 12.65, 13.15, "pale")
            segment(f"inner_{side}", [reflect(6.5252), 11.605], [reflect(7.0772), 13.905],
                    .05, 13.16, 13.21, "violet")
        box("inner_bottom", [6.5252, 11.58, 13.16], [9.4748, 11.63, 13.21], "violet")
        box("inner_top", [7.0772, 13.88, 13.16], [8.9228, 13.93, 13.21], "violet")
    else:
        # Reference U/horns: inward at the base, flare out at the middle, curl
        # inward again at the tips. Eight short rotated segments per side, plus
        # fine warm highlights. No top bridge, glass or violet material.
        box("u_bottom", [7.18, 11.43, 12.65], [8.82, 11.57, 13.15], "bronze")
        box("u_lower_trim", [7.25, 11.56, 13.16], [8.75, 11.60, 13.21], "pale")
        points = [(7.25, 11.5), (6.85, 11.65), (6.5, 11.95), (6.38, 12.3),
                  (6.46, 12.65), (6.67, 13.0), (6.82, 13.35), (6.88, 13.68), (7.0, 14.0)]
        widths = [.18, .17, .16, .15, .14, .13, .11, .08]
        for side in (0, 1):
            reflect = lambda point: (point[0] if side == 0 else 16 - point[0], point[1])
            for index, (start, end, width) in enumerate(zip(points, points[1:], widths)):
                segment(f"horn_{side}_{index}", reflect(start), reflect(end), width, 12.65, 13.15, "bronze")
                # Offset the fine highlight toward the aperture, along the beam normal.
                dx, dy = end[0] - start[0], end[1] - start[1]
                length = math.hypot(dx, dy)
                nx, ny = dy / length * width * .23, -dx / length * width * .23
                highlight_start = (start[0] + nx, start[1] + ny)
                highlight_end = (end[0] + nx, end[1] + ny)
                segment(f"horn_highlight_{side}_{index}", reflect(highlight_start), reflect(highlight_end),
                        .035, 13.16, 13.21, "pale")
    return pieces


def lfr_models(weapon_id, output, sources):
    source = ASSETS / f"models/weapon/linear_fusion_rifle/{weapon_id}.json"
    ads = source.with_name(weapon_id + "_ads.json")
    texture = ASSETS / f"textures/item/weapon/w30/{weapon_id}.png"
    transform_source = ROOT / "scripts/build_weapons_w30.py"
    for path in (source, ads, texture, transform_source):
        sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    model = json.loads(source.read_bytes())
    body = []
    clipped = removed = 0
    for original in model["elements"]:
        element = copy.deepcopy(original)
        if element["to"][1] > CLIP_Y:
            element["to"][1] = CLIP_Y
            if element["from"][1] < CLIP_Y:
                clipped += 1
        if any(element["from"][axis] >= element["to"][axis] for axis in range(3)):
            removed += 1
        else:
            body.append(element)
    samples = texture_samples(texture, weapon_id)
    optics = optic_parts(weapon_id, samples)
    geometry = copy.deepcopy(model)
    geometry["elements"] = body + optics
    assert len(geometry["elements"]) <= 256
    key = f"weapon_scope_w45/{weapon_id}"
    output[ASSETS / f"models/{key}_geometry.json"] = encode(geometry)
    display = copy.deepcopy(json.loads(ads.read_bytes())["display"])
    for context in FIRST_PERSON:
        display[context]["translation"][1] = round(8.32 - (OPTIC_CENTER[1] - 8) * .95, 6)
    two_hand_display = runpy.run_path(str(transform_source))["two_hand_display"]
    output[ASSETS / f"models/{key}_native.json"] = encode({"parent": f"destiny:{key}_geometry", "display": display})
    output[ASSETS / f"models/{key}_twohand.json"] = encode({
        "parent": f"destiny:{key}_geometry", "display": two_hand_display(display, "linear_fusion_rifle")})
    return {
        "sourceCubes": len(model["elements"]), "bodyCubes": len(body), "clippedCubes": clipped,
        "removedCubes": removed, "opticCubes": len(optics), "totalCubes": len(body) + len(optics),
        "clipY": CLIP_Y, "opticCenter": list(OPTIC_CENTER), "paletteSamples": samples,
        "geometry": f"destiny:{key}_geometry", "native": f"destiny:{key}_native", "twohand": f"destiny:{key}_twohand",
        "shape": "open_trapezoid" if weapon_id == "line_in_the_sand" else "open_u_no_top_bridge",
        "opticTintRgb": VIOLET_TINT if weapon_id == "line_in_the_sand" else BRONZE_TINT,
        "rotationSchema": "26.3 CuboidModelElement.Deserializer accepts arbitrary axis/angle floats; rescale=false",
    }


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def generate():
    output = {}
    originals = {}
    sources = {}
    lfr = {}
    for weapon_id in IDS:
        source = ASSETS / f"items/weapon/{weapon_id}.json"
        originals[str(source.relative_to(ROOT))] = hashlib.sha256(source.read_bytes()).hexdigest()
        sources[str(source.relative_to(ROOT))] = originals[str(source.relative_to(ROOT))]
        item = json.loads(source.read_bytes())
        select = item["model"]
        assert select["type"] == "minecraft:select"
        assert select["property"] == "minecraft:custom_model_data" and select["index"] == 0
        ads = [case["model"] for case in select["cases"] if case["when"] == "ads"]
        assert len(ads) == 1, f"Expected exactly one ADS case: {weapon_id}"
        fallback = ads[0]
        assert fallback["type"] == "minecraft:condition"
        assert fallback["property"] == "minecraft:custom_model_data" and fallback["index"] == 0
        # Preserve every other item-definition option, e.g. hand_animation_on_swap.
        wrapper = copy.deepcopy(item)
        firstperson = {"type": "minecraft:empty"}
        if weapon_id in LFRS:
            lfr[weapon_id] = lfr_models(weapon_id, output, sources)
            firstperson = {"type": "minecraft:condition", "property": "minecraft:custom_model_data", "index": 0,
                           "on_true": {"type": "minecraft:model", "model": lfr[weapon_id]["twohand"],
                                       "tints": [{"type": "minecraft:constant", "value": lfr[weapon_id]["opticTintRgb"]}]},
                           "on_false": {"type": "minecraft:model", "model": lfr[weapon_id]["native"],
                                        "tints": [{"type": "minecraft:constant", "value": lfr[weapon_id]["opticTintRgb"]}]}}
        wrapper["model"] = {
            "type": "minecraft:select",
            "property": "minecraft:display_context",
            "cases": [{"when": list(FIRST_PERSON), "model": firstperson}],
            "fallback": copy.deepcopy(fallback),
        }
        output[ASSETS / f"items/weapon_scope_w45/{weapon_id}.json"] = encode(wrapper)

    output[ROOT / "art/weapons/w45-models/manifest.json"] = encode({
        "generator": "scripts/generate_scope_models_w45.py",
        "minecraftVersion": "26.3",
        "ids": list(IDS),
        "pose": "scope",
        "firstPersonContexts": list(FIRST_PERSON),
        "fallback": "Exact original ADS case, including custom_model_data boolean index 0 grip",
        "routing": "Live Polymer model getter only; real stack ITEM_MODEL remains original",
        "schemaEvidence": {
            "vanillaAsset": "assets/minecraft/items/spyglass.json",
            "enum": "net.minecraft.world.item.ItemDisplayContext#getSerializedName",
            "selectProperty": "net.minecraft.client.renderer.item.properties.select.DisplayContext",
            "validation": "26.3 local merged JAR assets and javap -c -p",
        },
        "originalItemSha256": originals,
        "sourceSha256": sources,
        "lfr": lfr,
        "sha256": {str(path.relative_to(ROOT)): hashlib.sha256(data).hexdigest()
                   for path, data in output.items()},
    })
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    for path, data in generate().items():
        if args.verify:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit(f"W45 asset differs or is missing: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f"{'Verified' if args.verify else 'Generated'} 5 W45 wrappers, 6 LFR 3D models and manifest")
