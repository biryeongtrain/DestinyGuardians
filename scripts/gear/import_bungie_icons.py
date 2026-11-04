#!/usr/bin/env python3
"""Import Bungie manifest icons (weapons, weapon traits, engrams) as Destiny HUD sprites.

Inputs: a manifest cache directory with manifest.json, items.json, pools.json and icons/ (see
scripts/gear/fetch_manifest.py). Writes textures/item/hud/bungie/*.png, matching item/model
definitions and src/main/resources/destiny/gear/bungie-icons.json (provenance + id map).
"""
import json, sys, os
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/dg-loot")
ASSETS = ROOT / "src/main/resources/assets/destiny"
TEX, ITEMS, MODELS = ASSETS / "textures/item/hud/bungie", ASSETS / "items/gui/hud/bungie", ASSETS / "models/gui/hud/bungie"
for d in (TEX, ITEMS, MODELS): d.mkdir(parents=True, exist_ok=True)
index = json.load(open(CACHE / "icons/index.json"))
version = json.load(open(CACHE / "manifest.json"))["Response"]["version"]
model_template = json.load(open(ASSETS / "models/gui/hud/gear_cursor.json"))
out = {"manifestVersion": version, "weapons": {}, "perks": {}, "engrams": {}}
for key, url in sorted(index.items()):
    im = Image.open(CACHE / "icons" / f"{key}.png").convert("RGBA")
    if im.size != (96, 96): im = im.resize((96, 96), Image.LANCZOS)
    im.save(TEX / f"{key}.png", optimize=True)
    m = dict(model_template); m["textures"] = {"layer0": f"destiny:item/hud/bungie/{key}"}
    json.dump(m, open(MODELS / f"{key}.json", "w"), indent=2)
    json.dump({"model": {"type": "minecraft:model", "model": f"destiny:gui/hud/bungie/{key}",
               "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}},
              open(ITEMS / f"{key}.json", "w"), indent=2)
    kind, _, name = key.partition("_")
    out[{"weapon": "weapons", "perk": "perks", "engram": "engrams"}[kind]][name] = {"icon": "bungie/" + key, "source": "https://www.bungie.net" + url}
dest = ROOT / "src/main/resources/destiny/gear/bungie-icons.json"
dest.parent.mkdir(parents=True, exist_ok=True)
json.dump(out, open(dest, "w"), indent=1, sort_keys=True)
print(len(index), "icons", version)
