#!/usr/bin/env python3
"""Import Fireteam Finder art from the live Bungie manifest: activity PGCR banners and activity/mode icons.

Writes textures/item/hud/fireteam/<key>.png with item/model definitions (same quad template as the other HUD
sprites) and src/main/resources/destiny/fireteam/art.json. Banners are downscaled to 640x360, icons to 96x96.
Cache directory (default /tmp/dg-loot) is shared with scripts/gear/fetch_manifest.py.
"""
import io, json, sys, urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/dg-loot")
ASSETS = ROOT / "src/main/resources/assets/destiny"
TEX, ITEMS, MODELS = ASSETS / "textures/item/hud/fireteam", ASSETS / "items/gui/hud/fireteam", ASSETS / "models/gui/hud/fireteam"
BUNGIE = "https://www.bungie.net"


def fetch(url, path):
    if not path.exists():
        path.write_bytes(urllib.request.urlopen(url, timeout=300).read())
    return path


CACHE.mkdir(parents=True, exist_ok=True)
manifest = json.load(open(fetch(BUNGIE + "/Platform/Destiny2/Manifest/", CACHE / "manifest.json")))["Response"]
paths = manifest["jsonWorldComponentContentPaths"]["en"]
acts = json.load(open(fetch(BUNGIE + paths["DestinyActivityDefinition"], CACHE / "DestinyActivityDefinition.json")))
modes = json.load(open(fetch(BUNGIE + paths["DestinyActivityModeDefinition"], CACHE / "DestinyActivityModeDefinition.json")))

GUARDIAN_RISES, DEVILS_LAIR = "3906017155", "1917776943"
STRIKES, STORY = "2394616003", "1686739444"
assert acts[DEVILS_LAIR]["displayProperties"]["name"] == "The Devils' Lair"
assert acts[GUARDIAN_RISES]["displayProperties"]["name"] == "A Guardian Rises"

# key -> (url, size, source hash)
wanted = {
    "banner_devils_lair": (acts[DEVILS_LAIR]["pgcrImage"], (640, 360), DEVILS_LAIR),
    "banner_guardian_rises": (acts[GUARDIAN_RISES]["pgcrImage"], (640, 360), GUARDIAN_RISES),
    "banner_strikes": (modes[STRIKES]["pgcrImage"], (640, 360), STRIKES),
    "banner_story": (modes[STORY]["pgcrImage"], (640, 360), STORY),
    "icon_devils_lair": (acts[DEVILS_LAIR]["displayProperties"]["icon"], (96, 96), DEVILS_LAIR),
    "mode_strikes": (modes[STRIKES]["displayProperties"]["icon"], (96, 96), STRIKES),
    "mode_story": (modes[STORY]["displayProperties"]["icon"], (96, 96), STORY),
}

for d in (TEX, ITEMS, MODELS): d.mkdir(parents=True, exist_ok=True)
template = json.load(open(ASSETS / "models/gui/hud/gear_cursor.json"))
index = {}
for key, (url, size, h) in wanted.items():
    raw = fetch(BUNGIE + url, CACHE / f"fireteam_{key}{Path(url).suffix}").read_bytes()
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    if size[0] != size[1]:  # banner: centre crop to 16:9 first
        w, h2 = im.size; tw = min(w, h2 * 16 // 9); th = tw * 9 // 16
        im = im.crop(((w - tw) // 2, (h2 - th) // 2, (w + tw) // 2, (h2 + th) // 2))
    im = im.resize(size, Image.LANCZOS)
    if size[0] != size[1]: im.convert("RGB").save(TEX / f"{key}.png", optimize=True)
    else: im.save(TEX / f"{key}.png", optimize=True)
    m = dict(template); m["textures"] = {"layer0": f"destiny:item/hud/fireteam/{key}"}
    json.dump(m, open(MODELS / f"{key}.json", "w"), indent=2)
    json.dump({"model": {"type": "minecraft:model", "model": f"destiny:gui/hud/fireteam/{key}",
                         "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}},
              open(ITEMS / f"{key}.json", "w"), indent=2)
    index[key] = {"icon": "fireteam/" + key, "source": BUNGIE + url, "hash": int(h)}
out = ROOT / "src/main/resources/destiny/fireteam/art.json"
out.parent.mkdir(parents=True, exist_ok=True)
json.dump({"manifest": manifest["version"], "art": index}, open(out, "w"), indent=1, sort_keys=True)
print("fireteam art", list(wanted), manifest["version"])
