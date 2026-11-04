#!/usr/bin/env python3
"""Generate two original font labels; --verify checks without rewriting any output.

Reuses the deterministic W108 raster/PNG codec, not its assets or historical QA.
Run with the bundled Pillow Python. No downloaded sprites or bundled fonts.
"""
import argparse
import importlib.util
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("w108_label_codec", ROOT / "scripts/build_feeding_frenzy_hud_w108.py")
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)

def outputs():
    font = codec.FONT.read_bytes()
    if hashlib.sha256(font).hexdigest() != codec.FONT_SHA256:
        raise ValueError("Pinned font changed")
    result = {}
    for trait, label in (("one_for_all", "ONE FOR ALL"), ("surrounded", "SURROUNDED")):
        name = f"perk_{trait}_w109"
        codec.LABEL = label
        image, size, bounds = codec.raster_label(font)
        base = "src/main/resources/assets/destiny/"
        texture = base + f"textures/item/hud/{name}.png"
        model = base + f"models/gui/hud/{name}.json"
        item = base + f"items/gui/hud/{name}.json"
        result[texture] = codec.png(image)
        result[model] = codec.encode({
            "ambientocclusion": False, "gui_light": "front",
            "textures": {"0": f"destiny:item/hud/{name}", "particle": "#0"},
            "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "shade": False,
                          "faces": {f: {"texture": "#0", "uv": [0, 0, 16, 16], "tintindex": 0}
                                    for f in ("north", "south")}}]})
        result[item] = codec.encode({"model": {
            "type": "minecraft:model", "model": f"destiny:gui/hud/{name}",
            "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}})
        art = f"art/weapons/w109/hud/{trait}/"
        result[art + "label-source.svg"] = codec.source_svg(image).replace(b"W108", b"W109")
        result[art + "manifest.json"] = codec.encode({
            "stage": "W109", "label": label, "font_sha256": codec.FONT_SHA256,
            "font_size_px": size, "alpha_bounds_px": bounds, "size": [118, 24],
            "provenance": "Original generated system-font label, not an official Destiny sprite",
            "pack_files": {p: hashlib.sha256(result[p]).hexdigest() for p in (texture, model, item)}})
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    generated = outputs()
    for relative, data in generated.items():
        path = ROOT / relative
        if args.verify:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit("Output differs: " + relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(json.dumps({"verified": args.verify, "files": len(generated)}))
