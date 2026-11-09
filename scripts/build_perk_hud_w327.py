#!/usr/bin/env python3
"""Generate thirteen original W327 HUD label triplets and embedded provenance.

Uses the unchanged W200 raster and W108 PNG codec, pinned system font,
Pillow 13.0.0 / FreeType 2.14.3. --verify compares bytes without writing.
"""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("w200_labels", ROOT / "scripts/build_perk_hud_w200.py")
w200 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w200)
codec = w200.codec
BASE = Path("src/main/resources/assets/destiny")
SOURCE = Path("art/weapons/w327/hud/source.json")
LABELS = (('precision_instrument', 'PRECISION INSTRUMENT', 'COUNT_TIMER', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('desperate_measures', 'DESPERATE MEASURES', 'COUNT_TIMER', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('successful_warm_up', 'SUCCESSFUL WARM-UP', 'TIMER', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('keep_away', 'KEEP AWAY', 'FLAG', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('lone_wolf', 'LONE WOLF', 'FLAG', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('enlightened_action', 'ENLIGHTENED ACTION', 'DECIMAL_COUNT_TIMER', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('eddy_current', 'EDDY CURRENT', 'TIMER', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('perfect_float', 'PERFECT FLOAT', 'TIMER', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('offhand_strike', 'OFFHAND STRIKE', 'TIMER', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('loose_change', 'LOOSE CHANGE', 'TIMER', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('heal_clip', 'HEAL CLIP', 'TIMER', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('permeability', 'PERMEABILITY', 'FLAG', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'), ('repulsor_brace', 'REPULSOR BRACE', 'TIMER', 400, 'PerkExpansion*.buffs', 'Observed source state only; -1 means untimed'))


def paths(key):
    name = f"perk_{key}_w327"
    return (BASE / f"textures/item/hud/{name}.png",
            BASE / f"models/gui/hud/{name}.json",
            BASE / f"items/gui/hud/{name}.json")


def outputs():
    if codec.PILLOW_VERSION != "13.0.0" or codec.features.version("freetype2") != "2.14.3":
        raise ValueError("Reproducibility requires Pillow 13.0.0 / FreeType 2.14.3")
    font = codec.FONT.read_bytes()
    if hashlib.sha256(font).hexdigest() != codec.FONT_SHA256:
        raise ValueError("Pinned system font changed")
    result, labels = {}, []
    for key, label, layout, max_ticks, observer, visibility in LABELS:
        name = f"perk_{key}_w327"
        texture, model, item = paths(key)
        size = (94 if layout == "TIMER" else 118, 24)
        image, bounds, scale = w200.raster_label(font, label, size)
        result[texture] = codec.png(image)
        result[model] = codec.encode({
            "ambientocclusion": False, "gui_light": "front",
            "textures": {"0": f"destiny:item/hud/{name}", "particle": "#0"},
            "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "shade": False,
                          "faces": {face: {"texture": "#0", "uv": [0, 0, 16, 16], "tintindex": 0}
                                    for face in ("north", "south")}}]})
        result[item] = codec.encode({"model": {
            "type": "minecraft:model", "model": f"destiny:gui/hud/{name}",
            "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}})
        labels.append({
            "key": key, "label": label, "icon_id": f"destiny:gui/hud/{name}",
            "layout": layout, "size": list(size), "alpha_bounds_px": list(bounds),
            "horizontal_scale": scale, "valid_ticks": [1, max_ticks],
            "observer": observer, "visibility": visibility,
            "timer": "None; short window uses label and marker only" if layout == "FLAG"
                     else "ceil(observed remaining ticks / 20); never infer or restart duration",
        })
    result[SOURCE] = codec.encode({
        "stage": "W327", "font_family": "Arial Narrow Bold", "font_size_px": 22,
        "font_sha256": codec.FONT_SHA256, "layout_engine": "BASIC",
        "supersampling": codec.SCALE, "padding_px": codec.PADDING,
        "pillow_version": codec.PILLOW_VERSION, "freetype_version": codec.features.version("freetype2"),
        "provenance": "Original generated system-font labels; no official sprite, ripped asset or bundled font",
        "recipe": "W200 raster_label: 0.9 horizontal scale capped to padded width, centered LANCZOS coverage; W108 canonical RGBA8 PNG",
        "recipe_sources": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                           for path in ("scripts/build_perk_hud_w200.py", "scripts/build_feeding_frenzy_hud_w108.py")},
        "max_rows": 4, "labels": labels,
        "priority": "Legacy enum order preserved; new damage rows follow exotic rows, utility follows existing rows",
        "source_policy": "Server-runtime observations only; no equipment inference or gameplay values authored by HUD",
        "native_validation": "Pending master pack/model parser, server and native QA; generation is offline evidence",
        "pack_bytes": sum(map(len, result.values())),
        "pack_files": {str(path): hashlib.sha256(data).hexdigest() for path, data in result.items()},
        "generated_paths": [str(path) for path in (*result, SOURCE)],
    })
    validate(result)
    return result


def validate(generated):
    """Basic image/JSON parsing and reference checks for only these six assets."""
    for key, _, layout, *_ in LABELS:
        texture, model, item = paths(key)
        image = codec.Image.open(io.BytesIO(generated[texture]))
        image.load()
        if image.mode != "RGBA" or image.size != (94 if layout == "TIMER" else 118, 24):
            raise ValueError(f"Invalid label PNG: {texture}")
        graph, mesh = json.loads(generated[item])["model"], json.loads(generated[model])
        if BASE / ("models/" + graph["model"].split(":")[1] + ".json") != model:
            raise ValueError(f"Invalid item reference: {item}")
        if BASE / ("textures/" + mesh["textures"]["0"].split(":")[1] + ".png") != texture:
            raise ValueError(f"Invalid texture reference: {model}")
    json.loads(generated[SOURCE])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        generated = outputs()
        if args.verify:
            different = w200.differences(ROOT, generated)
            if different:
                parser.exit(1, "W327 output differs (no writes):\n" + "\n".join(different) + "\n")
        else:
            for path, data in generated.items():
                target = ROOT / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    except (OSError, ValueError) as error:
        parser.exit(1, f"W327: {error}\n")
    print(f"{'verified (read-only)' if args.verify else 'generated'} 40 W327 files; 13 original labels / 39 pack assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
