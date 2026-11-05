#!/usr/bin/env python3
"""Import the economy's Bungie manifest icons (Glimmer currency, Vault and Postmaster vendors) as HUD sprites.

Resolves the icons from the live Bungie manifest (DestinyInventoryItemDefinition / DestinyVendorDefinition) using a
cache directory (default /tmp/dg-loot, shared with scripts/gear/fetch_manifest.py), writes
textures/item/hud/bungie/<key>.png plus item/model definitions, and merges "currencies"/"vendors" sections into
src/main/resources/destiny/gear/bungie-icons.json without touching the other sections.
"""
import io, json, os, sys, urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/dg-loot")
ASSETS = ROOT / "src/main/resources/assets/destiny"
TEX, ITEMS, MODELS = ASSETS / "textures/item/hud/bungie", ASSETS / "items/gui/hud/bungie", ASSETS / "models/gui/hud/bungie"
BUNGIE = "https://www.bungie.net"


def fetch(url, path):
    if not path.exists():
        path.write_bytes(urllib.request.urlopen(url, timeout=120).read())
    return path


CACHE.mkdir(parents=True, exist_ok=True)
manifest = json.load(open(fetch(BUNGIE + "/Platform/Destiny2/Manifest/", CACHE / "manifest.json")))["Response"]
paths = manifest["jsonWorldComponentContentPaths"]["en"]
items = json.load(open(fetch(BUNGIE + paths["DestinyInventoryItemDefinition"], CACHE / "items.json")))
vendors = json.load(open(fetch(BUNGIE + paths["DestinyVendorDefinition"], CACHE / "vendors.json")))

# key -> (section, definition, field)
GLIMMER = "3159615086"   # Glimmer; maxStackSize 500000 is the in-game balance cap
VAULT = "1037843411"
POSTMASTER = "3161908920"  # Kadi 55-30, the Tower postmaster
wanted = {
    "currency_glimmer": ("currencies", "glimmer", items[GLIMMER]["displayProperties"]["icon"], GLIMMER),
    "vendor_vault": ("vendors", "vault", vendors[VAULT]["displayProperties"]["icon"], VAULT),
    "vendor_postmaster": ("vendors", "postmaster", vendors[POSTMASTER]["displayProperties"]["icon"], POSTMASTER),
}
assert items[GLIMMER]["displayProperties"]["name"] == "Glimmer"
assert items[GLIMMER]["inventory"]["maxStackSize"] == 500000

for d in (TEX, ITEMS, MODELS): d.mkdir(parents=True, exist_ok=True)
template = json.load(open(ASSETS / "models/gui/hud/gear_cursor.json"))
dest = ROOT / "src/main/resources/destiny/gear/bungie-icons.json"
index = json.load(open(dest))
for key, (section, name, icon, h) in wanted.items():
    raw = fetch(BUNGIE + icon, CACHE / f"{key}{Path(icon).suffix}").read_bytes()
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    if im.size != (96, 96): im = im.resize((96, 96), Image.LANCZOS)
    im.save(TEX / f"{key}.png", optimize=True)
    m = dict(template); m["textures"] = {"layer0": f"destiny:item/hud/bungie/{key}"}
    json.dump(m, open(MODELS / f"{key}.json", "w"), indent=2)
    json.dump({"model": {"type": "minecraft:model", "model": f"destiny:gui/hud/bungie/{key}",
                         "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}},
              open(ITEMS / f"{key}.json", "w"), indent=2)
    index.setdefault(section, {})[name] = {"icon": "bungie/" + key, "source": BUNGIE + icon, "hash": int(h)}
json.dump(index, open(dest, "w"), indent=1, sort_keys=True)
print("economy icons", list(wanted), manifest["version"])
