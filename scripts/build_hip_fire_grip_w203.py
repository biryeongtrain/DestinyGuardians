#!/usr/bin/env python3
"""Generate exact base Hip-Fire Grip sockets and bounded DDC evidence; --check writes nothing."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

BASE = 1866048759
TRAIT_CATEGORY = 4241085061
EXPECTED = [
    ("duke_mk_44", 2112909414, 4, 3815727680),
    ("first_in_last_out", 3616586446, 3, 267999755),
    ("long_arm", 8293111, 3, 3056706286),
    ("whispering_slab", 211938782, 3, 1885424927),
]
INPUTS = {
    "items": Path("/tmp/destiny-weapons-w30/bungie-items.json"),
    "plugsets": Path("/tmp/destiny-weapons-w60/bungie-plugsets.json"),
    "manifest": Path("/tmp/destiny-weapons-w60/manifest.json"),
    "ddc": Path("/private/tmp/destiny-w190/ddc-perks.html"),
}
PERK = {
    "id": "hip_fire_grip", "hash": BASE,
    "stabilityBonus": 25, "accuracyScalar": 0.7, "falloffScalar": 1.2,
    "falloffExcludedFamilies": ["shotgun", "sniper_rifle", "fusion_rifle"],
    "falloffExcludedIds": ["the_last_word"],
    "unsimulated": {
        "aimAssistBonus": 15, "precisionAngleThresholdDegreesBonus": 2.7,
        "aimAssistFalloffDistanceScalar": 1.2, "reticleStickinessFalloffDistanceScalar": 1.2,
    },
}


def load(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def generate(root):
    inventory, pools = load(INPUTS["items"]), load(INPUTS["plugsets"])
    definition = inventory[str(BASE)]
    require(definition["hash"] == BASE and definition["displayProperties"]["name"] == "Hip-Fire Grip",
            "Exact base trait definition required")
    catalog_path = root / "src/main/resources/destiny/weapons/w40-characteristics.json"
    canonical_path = root / "src/main/resources/destiny/weapons/w30.json"
    catalog = load(catalog_path)
    rolls, proofs = [], []
    for weapon in catalog:
        item = inventory[str(weapon["bungieHash"])]
        if item["inventory"]["tierType"] != 5 or weapon["exotic"]:
            continue
        sockets = item.get("sockets", {})
        indexes = sorted({n for c in sockets.get("socketCategories", [])
                          if c["socketCategoryHash"] == TRAIT_CATEGORY for n in c["socketIndexes"]})
        for index in indexes:
            socket = sockets["socketEntries"][index]
            pool = pools.get(str(socket.get("randomizedPlugSetHash")), {})
            if pool.get("isFakePlugSet") is not False:
                continue
            for plug in pool.get("reusablePlugItems", []):
                if plug.get("plugItemHash") != BASE or plug.get("currentlyCanRoll") is not True:
                    continue
                roll = {"id": weapon["id"], "hash": weapon["bungieHash"], "socket": index,
                        "perkHash": BASE, "plugSetHash": socket["randomizedPlugSetHash"]}
                require(item["hash"] == roll["hash"], "Exact official legendary item hash required")
                rolls.append(roll)
                proofs.append({"roll": roll, "itemHash": item["hash"], "itemName": item["displayProperties"]["name"],
                               "tierType": item["inventory"]["tierType"], "traitCategory": TRAIT_CATEGORY,
                               "socket": socket, "isFakePlugSet": pool["isFakePlugSet"], "matchingPlug": plug})
    rolls.sort(key=lambda r: r["id"])
    proofs.sort(key=lambda p: p["roll"]["id"])
    require([(r["id"], r["hash"], r["socket"], r["plugSetHash"]) for r in rolls] == EXPECTED,
            "Official sockets differ from the four pinned base sources")
    ids = {r["id"] for r in rolls}
    canonical = [w for w in load(canonical_path) if w["id"] in ids]
    require(len(canonical) == len(ids), "Complete unique canonical entries required")
    # Bound the retained evidence to the one sheet row; never print the full HTML document.
    rows = [m.group() for m in re.finditer(r'<tr\b[^>]*>.*?</tr>', INPUTS["ddc"].read_text(), re.S)
            if 'id="1662574278R119"' in m.group()]
    require(len(rows) == 1 and len(rows[0]) < 20000, "One bounded DDC row120 required")
    row = rows[0]
    text = " ".join(html.unescape(re.sub(r'<[^>]+>', ' ', row)).split())
    for fragment in ("120", "Hip-Fire Grip", "While hipfiring:", "20% Increased Aim Assist Falloff Distance",
                     "Reticle Stickiness Falloff Distance, and Damage Falloff Distance.", "+15 Aim Assist",
                     "+2.7° Precision Angle Threshold", "-30% Accuracy Cone Size and +25 Stability.",
                     "Shotguns", "Sniper Rifles", "Fusion Rifles, and The Last Word",
                     "do not benefit from Damage Falloff Increases.",
                     "cannot exceed regular Aim Assist Cone Size."):
        require(fragment in text, "Missing DDC base evidence: " + fragment)
    resource = {"stage": "W203", "perk": PERK, "weapons": rolls}
    files = dict(INPUTS, characteristics=catalog_path, canonical=canonical_path)
    source = {
        "date": "2026-10-27", "perkDefinition": definition,
        "officialManifest": load(INPUTS["manifest"])["Response"]["version"],
        "inputs": {name: {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for name, path in files.items()},
        "socketProofs": proofs, "canonicalEntries": sorted(canonical, key=lambda w: w["id"]),
        "ddc": {"url": "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278",
                "tabGid": 1662574278, "row": 120, "htmlRowId": "1662574278R119", "text": text, "html": row,
                "scope": "Base trait, while hipfiring; row has no separate PvE/PvP values. Enhanced effect excluded."},
        "baseValuesVerifiedFromDDC": True, "enhancedExcluded": True,
        "implementedModifiers": {k: v for k, v in PERK.items() if k != "unsimulated"},
        "unsimulated": PERK["unsimulated"],
        "limitations": [
            "No aim-assist, reticle-stickiness or precision-angle engine path is implemented by this worker.",
            "Precision angle does not prefer precision hits when body/precision cones overlap; capped by AA cone in source only.",
            "Falloff scalar scales distance thresholds, never damage or range-stat points; existing meters-to-blocks mapping retained.",
            "Registry, recoil/flinch, cone and falloff integration belong to the master coordinator.",
        ],
    }
    return {"src/main/resources/destiny/weapons/w203-hip-fire-grip.json": resource,
            "art/weapons/w203/hip-fire-grip/source.json": source}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    outputs = generate(root)
    for name, obj in outputs.items():
        dest = root / name
        content = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            require(dest.is_file() and dest.read_text() == content, "Generated output differs: " + name)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
    print("Hip-Fire Grip: four exact legendary base sockets; DDC row120; "
          + ("outputs match (--check)." if args.check else "resource/source generated."))


if __name__ == "__main__":
    main()
