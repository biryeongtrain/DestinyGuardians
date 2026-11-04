#!/usr/bin/env python3
"""Generate the original RAPID HIT label with the W108 codec/W110 model pattern.

Uses the SHA-pinned system font, Pillow 12.3.0 and FreeType 2.14.3.
--verify compares all five outputs without creating files or repairing differences.
"""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys

# Read-only verification must not emit an imported codec's __pycache__ either.
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "w108_label_codec", ROOT / "scripts/build_feeding_frenzy_hud_w108.py")
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)

NAME = "perk_rapid_hit_w169"
LABEL = "RAPID HIT"
BASE = Path("src/main/resources/assets/destiny")
ART = Path("art/hud/w169")
TEXTURE = BASE / f"textures/item/hud/{NAME}.png"
MODEL = BASE / f"models/gui/hud/{NAME}.json"
ITEM = BASE / f"items/gui/hud/{NAME}.json"
SOURCE = ART / "rapid-hit.svg"
MANIFEST = ART / "manifest.json"
PACK = (TEXTURE, MODEL, ITEM)


def outputs():
    if codec.PILLOW_VERSION != "12.3.0" or codec.features.version("freetype2") != "2.14.3":
        raise ValueError("Reproducibility requires Pillow 12.3.0 / FreeType 2.14.3")
    font = codec.FONT.read_bytes()
    if hashlib.sha256(font).hexdigest() != codec.FONT_SHA256:
        raise ValueError("Pinned system font changed")
    codec.LABEL = LABEL
    image, size, bounds = codec.raster_label(font)
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
        SOURCE: codec.source_svg(image).replace(b"W108", b"W169"),
    }
    pack_bytes = sum(len(result[path]) for path in PACK)
    if pack_bytes > 16384:
        raise ValueError("Three-file pack exceeds 16KiB")
    result[MANIFEST] = codec.encode({
        "stage": "W169", "label": LABEL, "size": list(codec.SIZE),
        "font_family": "Arial Narrow Bold", "font_sha256": codec.FONT_SHA256,
        "font_size_px": size, "alpha_bounds_px": list(bounds),
        "pillow_version": codec.PILLOW_VERSION,
        "freetype_version": codec.features.version("freetype2"),
        "layout_engine": "BASIC", "supersampling": codec.SCALE,
        "provenance": "Original generated system-font label, not an official Destiny sprite; "
                      "no ripped asset or bundled font",
        "runtime_contract": {
            "icon_id": f"destiny:gui/hud/{NAME}", "layout": "STACKED_TIMER",
            "stacks": [1, 2, 3, 4, 5], "remaining_ticks": "Actual observed positive ticks; no cached deadline",
            "priority": "Reload/utility, immediately before FEEDING_FRENZY",
            "max_rows": 4,
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
                parser.exit(1, "W169 output differs (no writes):\n" + "\n".join(different) + "\n")
        else:
            for path, data in generated.items():
                target = args.output_root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    except (OSError, ValueError) as error:
        parser.exit(1, f"W169: {error}\n")
    print(f"{'verified (read-only)' if args.verify else 'generated'} 5 W169 files; "
          "1 original label / 3 pack assets; 118x24 RGBA")


if __name__ == "__main__":
    main()
