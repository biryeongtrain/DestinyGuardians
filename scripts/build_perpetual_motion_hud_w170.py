#!/usr/bin/env python3
"""Generate the original PERPETUAL MOTION label with the W108 codec/W110 model pattern.

Uses the SHA-pinned system font, Pillow 12.3.0 and FreeType 2.14.3.
--verify compares all five outputs without creating files or repairing differences.
"""
import argparse
import hashlib
import importlib.util
import io
from pathlib import Path
import sys

# Read-only verification must not emit an imported codec's __pycache__ either.
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "w108_label_codec", ROOT / "scripts/build_feeding_frenzy_hud_w108.py")
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)

NAME = "perk_perpetual_motion_w170"
LABEL = "PERPETUAL MOTION"
BASE = Path("src/main/resources/assets/destiny")
ART = Path("art/hud/w170")
TEXTURE = BASE / f"textures/item/hud/{NAME}.png"
MODEL = BASE / f"models/gui/hud/{NAME}.json"
ITEM = BASE / f"items/gui/hud/{NAME}.json"
SOURCE = ART / "perpetual-motion.svg"
MANIFEST = ART / "manifest.json"
PACK = (TEXTURE, MODEL, ITEM)


def raster_label(font_bytes):
    # Keep W169's 22px letter height; condense the long name rather than reducing
    # cap height to the 14px needed by an uncondensed face in the same label slot.
    size = 22
    font = codec.ImageFont.truetype(io.BytesIO(font_bytes), size * codec.SCALE,
                                    layout_engine=codec.ImageFont.Layout.BASIC)
    left, top, right, bottom = font.getbbox(LABEL)
    ink = codec.Image.new("L", (right - left, bottom - top))
    codec.ImageDraw.Draw(ink).text((-left, -top), LABEL, font=font, fill=255)
    target_width = min(ink.width, (codec.SIZE[0] - 2 * codec.PADDING) * codec.SCALE)
    horizontal_scale = target_width / ink.width
    ink = ink.resize((target_width, ink.height), codec.Image.Resampling.LANCZOS)
    mask = codec.Image.new("L", (codec.SIZE[0] * codec.SCALE, codec.SIZE[1] * codec.SCALE))
    mask.paste(ink, ((mask.width - ink.width) // 2, (mask.height - ink.height) // 2))
    mask = mask.resize(codec.SIZE, codec.Image.Resampling.LANCZOS)
    bounds = mask.getbbox()
    if not bounds or bounds[0] <= 0 or bounds[1] <= 0 or bounds[2] >= 118 or bounds[3] >= 24:
        raise ValueError("Full compact label must fit without clipping")
    image = codec.Image.new("RGBA", codec.SIZE, (255, 255, 255, 0))
    image.putalpha(mask)
    return image, size, bounds, horizontal_scale


def outputs():
    if codec.PILLOW_VERSION != "12.3.0" or codec.features.version("freetype2") != "2.14.3":
        raise ValueError("Reproducibility requires Pillow 12.3.0 / FreeType 2.14.3")
    font = codec.FONT.read_bytes()
    if hashlib.sha256(font).hexdigest() != codec.FONT_SHA256:
        raise ValueError("Pinned system font changed")
    codec.LABEL = LABEL
    image, size, bounds, horizontal_scale = raster_label(font)
    result = {
        TEXTURE: codec.png(image),
        MODEL: codec.encode({
            "ambientocclusion": False, "gui_light": "front",
            "textures": {"0": f"destiny:item/hud/{NAME}", "particle": "#0"},
            "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "shade": False,
                          "faces": {face: {"texture": "#0", "uv": [0, 0, 16, 16], "tintindex": 0}
                                    for face in ("north", "south")}}]}),
        ITEM: codec.encode({"model": {
            "type": "minecraft:model", "model": f"destiny:gui/hud/{NAME}",
            "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}}),
        SOURCE: codec.source_svg(image).replace(b"W108", b"W170"),
    }
    pack_bytes = sum(len(result[path]) for path in PACK)
    if pack_bytes > 16384:
        raise ValueError("Three-file pack exceeds 16KiB")
    result[MANIFEST] = codec.encode({
        "stage": "W170", "label": LABEL, "size": list(codec.SIZE),
        "font_family": "Arial Narrow Bold", "font_sha256": codec.FONT_SHA256,
        "font_size_px": size, "horizontal_scale": horizontal_scale, "alpha_bounds_px": list(bounds),
        "pillow_version": codec.PILLOW_VERSION,
        "freetype_version": codec.features.version("freetype2"),
        "layout_engine": "BASIC", "supersampling": codec.SCALE,
        "provenance": "Original generated system-font label, not an official Destiny sprite; "
                      "no ripped asset or bundled font",
        "runtime_contract": {
            "icon_id": f"destiny:gui/hud/{NAME}", "layout": "COUNT",
            "stacks": [1, 2], "remaining_ticks": "None: no buff duration, countdown or cached deadline",
            "priority": "Reload/utility, after RAPID_HIT and FEEDING_FRENZY",
            "max_rows": 4,
            "node_suffixes": ["marker", "label", "x", "count"],
            "marker": "Green utility buff; master must reserve gold for Memento Mori / Honed Edge",
            "visibility": "Held weapon only; stowed progression belongs to master runtime",
            "layout_limits": "Classic bounded four-row feed; 118x24 label, 32-unit row pitch; "
                             "preempted by all earlier kinds; no modern full-HUD fidelity claim",
            "native_validation": "Not run in this worker; no game launch, GUI or Vision",
            "integration": "Master owns WeaponPerkHud runtime adapter and shared registration"},
        "pack_bytes": pack_bytes, "pack_byte_budget": 16384,
        "pack_files": {str(path): hashlib.sha256(result[path]).hexdigest() for path in PACK},
        "source_files": {str(SOURCE): hashlib.sha256(result[SOURCE]).hexdigest()},
        "generated_paths": [str(path) for path in (*result, MANIFEST)],
    })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        generated = outputs()
        if args.verify:
            different = [str(path) for path, data in generated.items()
                         if not (args.output_root / path).is_file()
                         or (args.output_root / path).read_bytes() != data]
            if different:
                parser.exit(1, "W170 output differs (no writes):\n" + "\n".join(different) + "\n")
        else:
            for path, data in generated.items():
                target = args.output_root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    except (OSError, ValueError) as error:
        parser.exit(1, f"W170: {error}\n")
    print(f"{'verified (read-only)' if args.verify else 'generated'} 5 W170 files; "
          "1 original label / 3 pack assets; 118x24 RGBA")


if __name__ == "__main__":
    main()
