#!/usr/bin/env python3
"""Generate W190's base trait resource and compact source proof; --verify writes nothing.

Offline pinned inputs only. No test harness, downloads, shared registries or runtime edits.
"""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/build_under_pressure_w190.py"
TARGET = "src/main/resources/destiny/weapons/w190-under-pressure.json"
SOURCE = "art/weapons/w190/under-pressure/source.json"
BASE, ENHANCED, TRAIT = 1645158859, 3755250867, 4241085061
VERSION = "245114.26.10.13.2000-1-bnet.66137"
PREFIX = "src/main/resources/destiny/weapons/"
PINS = {
    PREFIX + "w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    PREFIX + "w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    PREFIX + "w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    PREFIX + "w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugsets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "inventory_provenance": "c7e198462980f93a9ebc709d06021b0a3ed636969ef73a7a4440146341229be1",
    "ddc": "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437",
}
# Frozen catalog expectation; admission is independently derived from official randomized pools.
EXPECTED = [
    ("bygones", 2712244741, 4, 3060320121),
    ("chattering_bone", 568515759, 4, 423791138),
    ("patron_of_lost_causes", 2723241847, 4, 120674550),
    ("long_arm", 8293111, 3, 3056706286),
    ("dead_man_walking_xx7463", 3751622019, 3, 3268663985),
    ("hollow_words", 607191995, 3, 637298592),
    ("dream_breaker", 2931957300, 3, 3785896921),
    ("coriolis_force", 3512349612, 3, 2568674372),
    ("line_in_the_sand", 946443267, 3, 1503774254),
    ("fixed_odds", 2194955522, 3, 4227334000),
]
PERK = {
    "id": "under_pressure", "hash": BASE,
    "thresholdRatioExclusive": 0.5,
    "accuracyConeReductionAtHalf": 0.125,
    "accuracyConeReductionAtEmpty": 0.25,
    "originalAccuracyVerified": True,
    "originalStabilityText": "up to +30?",
    "originalStabilityVerified": False,
    "temporaryServerStabilityCap": 30,
    "temporaryServerStabilityCurve": "floor(30 * (1 - 2 * rounds / baseCapacity)) below half; otherwise 0",
    "source": "art/weapons/w190/under-pressure/source.json",
}
POLICIES = {
    "ammo": "READ_ONLY_TRUE_LOADED_ROUNDS_CANONICAL_BASE_CAPACITY_NO_RESERVES",
    "condition": "STRICTLY_BELOW_HALF_LINEAR_TO_EMPTY",
    "unsupported": "BONUS_ZERO_SCALAR_ONE_INCLUDING_INVALID_RESOURCE_OR_AMMO",
    "accuracy": "CONE_SIZE_ONLY_NOT_CONE_GROWTH_OR_AIM_ASSIST",
    "stability": "TEMPORARY_SERVER_LINEAR_0_TO_30_FLOOR_ORIGINAL_UNVERIFIED",
    "enhanced": "EXCLUDED",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def roll(weapon, item_hash, socket, pool):
    return dict(id=weapon, hash=item_hash, socket=socket, perkHash=BASE, plugSetHash=pool)


def generate(args):
    paths = {key: args.root / key for key in PINS if key.startswith(PREFIX)}
    paths.update({key: getattr(args, key) for key in PINS if not key.startswith(PREFIX)})
    data, pins = {}, {}
    for key, path in paths.items():
        raw = path.read_bytes()
        require(digest(raw) == PINS[key], "Pinned source changed: " + key)
        pins[key] = {"sha256": digest(raw), "bytes": len(raw)}
        data[key] = raw.decode() if key == "ddc" else json.loads(raw)

    manifest = data["manifest"]["Response"]
    require(manifest["version"] == VERSION, "Manifest version")
    components = manifest["jsonWorldComponentContentPaths"]["en"]
    for component in ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition"):
        require(components[component] == "/common/destiny2_content/json/en/" + component
                + "-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json", "Manifest component path")
    require(data["inventory_provenance"] == {
        "version": VERSION, "path": components["DestinyInventoryItemDefinition"]
    }, "W30 inventory and W60 plugsets share manifest version")
    catalog = list(data[PREFIX + "w30.json"])
    characteristics = list(data[PREFIX + "w40-characteristics.json"])
    for name in ("w83-exotics.json", "w84-exotics.json"):
        catalog.extend(row["catalog"] for row in data[PREFIX + name])
        characteristics.extend(row["characteristics"] for row in data[PREFIX + name])
    require(len(catalog) == len(characteristics) == 65
            and len({w["bungieHash"] for w in characteristics}) == 65
            and {w["id"] for w in catalog} == {w["id"] for w in characteristics}
            and len({w["id"] for w in catalog}) == 65, "Complete current catalog")
    inv, pools = data["inventory"], data["plugsets"]
    for item_hash, kind in ((BASE, "Trait"), (ENHANCED, "Enhanced Trait")):
        definition = inv[str(item_hash)]
        require(definition["hash"] == item_hash and definition["itemType"] == 19
                and definition["displayProperties"]["name"] == "Under Pressure"
                and definition["itemTypeDisplayName"] == kind
                and not definition["redacted"] and not definition["blacklisted"]
                and definition["plug"]["isDummyPlug"] is False, "Official trait identity")

    rows, scans, proofs = [], [], []
    for weapon in characteristics:
        definition = inv[str(weapon["bungieHash"])]
        require(definition["hash"] == weapon["bungieHash"] and definition["itemType"] == 3
                and not definition["redacted"] and not definition["blacklisted"]
                and (definition["inventory"]["tierType"] == 6) == weapon["exotic"], "Official weapon identity")
        legendary = definition["inventory"]["tierType"] == 5 and not weapon["exotic"]
        sockets = definition.get("sockets", {})
        traits = {i for c in sockets.get("socketCategories", [])
                  if c["socketCategoryHash"] == TRAIT for i in c["socketIndexes"]}
        scan = {"id": weapon["id"], "hash": definition["hash"], "legendary": legendary,
                "traitSockets": sorted(traits), "randomizedTraitPools": [], "references": []}
        for index, socket in enumerate(sockets.get("socketEntries", [])):
            if index in traits and socket.get("randomizedPlugSetHash"):
                scan["randomizedTraitPools"].append({"socket": index, "plugSetHash": socket["randomizedPlugSetHash"]})
            # Reusable/crafting/fixed references are recorded but cannot authorize a roll.
            direct = [socket.get("singleInitialItemHash")] + [x["plugItemHash"] for x in socket.get("reusablePlugItems", [])]
            if any(h in (BASE, ENHANCED) for h in direct):
                scan["references"].append({"socket": index, "field": "fixed/reusablePlugItems",
                                           "hashes": [h for h in direct if h in (BASE, ENHANCED)], "admitted": False})
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                pool_hash = socket.get(field)
                if not pool_hash:
                    continue
                pool = pools[str(pool_hash)]
                require(pool["hash"] == pool_hash, "Official pool identity")
                for match in pool["reusablePlugItems"]:
                    if match["plugItemHash"] not in (BASE, ENHANCED):
                        continue
                    admitted = (legendary and index in traits and field == "randomizedPlugSetHash"
                                and pool["isFakePlugSet"] is False and match["plugItemHash"] == BASE
                                and match.get("currentlyCanRoll") is True)
                    scan["references"].append({"socket": index, "field": field, "plugSetHash": pool_hash,
                        "isFakePlugSet": pool["isFakePlugSet"], "matchingEntry": match, "admitted": admitted})
                    if admitted:
                        entry = roll(weapon["id"], definition["hash"], index, pool_hash)
                        require(entry not in rows, "Unique exact roll")
                        rows.append(entry)
                        proofs.append({"roll": entry, "socketCategoryHash": TRAIT,
                            "socketCategories": sockets["socketCategories"], "socketEntry": socket,
                            "matchingEntry": match, "officialPool": pool})
        scans.append(scan)
    require(rows == [roll(*entry) for entry in EXPECTED], "Exact ten base randomized trait sockets")

    ddc_rows = [row for row in re.findall(r"<tr\b[^>]*>.*?</tr>", data["ddc"], re.S) if "Under Pressure" in row]
    require(len(ddc_rows) == 1 and 'id="1662574278R238"' in ddc_rows[0], "DDC gid1662574278 row239")
    row_html = ddc_rows[0]
    row_text = html.unescape(re.sub(r"<[^>]+>", " ", row_html.replace("<br>", "\n"))).strip()
    require(all(text in row_text for text in ("below 50%", "0%", "Linearly grants -12.5% to -25%",
                "↑-30%?", "up to +30?", "↑+?")), "DDC base values, uncertainty and enhanced exclusion")
    resource = {"stage": "W190", "perk": PERK, "policies": POLICIES, "weapons": rows}
    source = {
        "stage": "W190", "generator": SCRIPT, "generatorSha256": digest((args.root / SCRIPT).read_bytes()),
        "sourcePins": pins, "manifestVersion": VERSION,
        "officialUrls": {component: "https://www.bungie.net" + components[component]
                         for component in ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
        "baseDefinition": inv[str(BASE)], "enhancedDefinitionExcluded": inv[str(ENHANCED)],
        "catalogCount": 65, "exactBaseRollCount": len(rows), "rolls": rows,
        "admission": "Legendary, actual trait category4241085061, randomizedPlugSetHash, nonfake pool, base1645158859 currentlyCanRoll=true; all required",
        "catalogScan": scans, "exactPoolProofs": proofs,
        "ddc": {"url": "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278",
            "tab": "Weapon Perks", "gid": 1662574278, "row": 239, "fetchedDate": "2026-10-27",
            "wholeSha256": PINS["ddc"], "rowSha256": digest(row_html.encode()),
            "rowHtml": row_html, "rowText": row_text,
            "pvePvp": "No mode or weapon-family split stated in this base row; no separate values invented.",
            "confidence": {"originalAccuracyVerified": True, "originalStabilityVerified": False},
            "enhancedExcluded": {"hash": ENHANCED, "accuracyText": "↑-30%?", "stabilityText": "↑+?"}},
        "implementation": PERK, "policies": POLICIES,
        "integration": "Master registers under_pressure and exact rolls in WeaponPerks. Add raw stability bonus before existing stat clamp/curve; multiply direction cone size by accuracyScalar once. Default uses authoritative live rounds at query time, including after paid ammo save: Minecraft timing adaptation, not original timing verified by DDC239. Optional explicit-round overloads accept caller-owned rounds/canonical capacity; if choosing pre-payment timing, snapshot local rounds before consume and pass those values consistently. No cached shot lifecycle/tokens; no cone-size scalar on growth.",
        "validation": "Pinned source and output generation only; no tests, builds, game, CU, HUD, animations or shared file edits.",
        "resourceSha256": digest(encode(resource)),
    }
    return {TARGET: resource, SOURCE: source}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    defaults = {
        "inventory": "/tmp/destiny-weapons-w30/bungie-items.json",
        "plugsets": "/tmp/destiny-weapons-w60/bungie-plugsets.json",
        "manifest": "/tmp/destiny-weapons-w60/manifest.json",
        "inventory_provenance": "/tmp/destiny-weapons-w30/manifest-provenance.json",
        "ddc": "/private/tmp/destiny-w190/ddc-perks.html",
    }
    for key, value in defaults.items():
        parser.add_argument("--" + key.replace("_", "-"), type=Path, default=Path(value))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    for name, value in generate(args).items():
        path, raw = args.root / name, encode(value)
        if args.verify:
            require(path.read_bytes() == raw, "Generated output drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print("W190: exact10 / catalog65 / DDC239; " + ("VERIFIED" if args.verify else "GENERATED"))


if __name__ == "__main__":
    main()
