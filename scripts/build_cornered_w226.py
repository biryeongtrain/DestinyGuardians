#!/usr/bin/env python3
"""Reproduce exact BASIC Cornered sockets and bounded DDC proof; --check never writes."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons/"
RESOURCE = PREFIX + "w226-cornered.json"
SOURCE = "art/weapons/w226/cornered/source.json"
DOC = "art/weapons/w226/cornered/SOURCE.md"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
BASE, ENHANCED, TRAITS, BACKUP_PLAN = 1799762209, 1008128453, 4241085061, 1600092898
EXPECTED = [{"id": "dream_breaker", "hash": 2931957300, "socket": 4,
             "perkHash": BASE, "plugSetHash": 1206254527}]
PINS = {
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugsets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "ddc": "6430f2f552832b903efb85be59adf4a1791d956d30fee4e4fe79c8ad2c53bc15",
}
URL = ("https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4"
       "/htmlview/sheet?gid=1662574278")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def generate(args):
    pins = {}

    def read(path, key, text=False):
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        pins[key] = {"sha256": digest, "bytes": len(raw)}
        if key in PINS:
            require(digest == PINS[key], "pinned input changed: " + key)
        return raw.decode() if text else json.loads(raw)

    manifest = read(args.manifest, "manifest")["Response"]
    require(manifest["version"] == VERSION, "manifest version")
    inventory = read(args.inventory, "inventory")
    pools = read(args.plugsets, "plugsets")
    require({i["hash"] for i in inventory.values()
             if i.get("displayProperties", {}).get("name") == "Cornered"} == {BASE, ENHANCED},
            "exact basic/enhanced definitions")
    basic, enhanced = inventory[str(BASE)], inventory[str(ENHANCED)]
    require(basic["itemTypeDisplayName"] == "Trait"
            and enhanced["itemTypeDisplayName"] == "Enhanced Trait"
            and basic["plug"]["isDummyPlug"] is False
            and basic["redacted"] is False and basic["blacklisted"] is False, "real basic trait")
    ddc = read(args.ddc, "ddc", text=True)
    rows = [r for r in re.findall(r"<tr\b[^>]*>.*?</tr>", ddc, re.S)
            if any(html.unescape(re.sub(r"<[^>]+>", "", c)).strip() == "Cornered"
                   for c in re.findall(r"<td\b[^>]*>(.*?)</td>", r, re.S))]
    require(len(rows) == 1, "unique exact Cornered row")
    raw_row = rows[0]
    row_text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw_row)).split())
    require('id="1662574278R56"' in raw_row and row_text.startswith("57 Cornered")
            and all(s in row_text for s in ("15 metres", "2 enemies", "0.85x Charge/Draw Time Multiplier",
                    "Buff lingers for 1.5 seconds", "↑and +10 Stability.", "↑Passively grants +5 Stability.")),
            "DDC57 basic values and enhanced-only exclusions")
    selected = read(args.root / PREFIX / "w40-characteristics.json", "w40-characteristics.json")
    catalog = read(args.root / PREFIX / "w30.json", "w30.json")
    for filename in ("w83-exotics.json", "w84-exotics.json"):
        extra = read(args.root / PREFIX / filename, filename)
        selected += [r["characteristics"] for r in extra]
        catalog += [r["catalog"] for r in extra]
    require(len(selected) == len({w["bungieHash"] for w in selected}) == 65, "canonical catalog65")
    require({w["id"] for w in catalog} == {w["id"] for w in selected}, "catalog identity coverage")
    by_id = {w["id"]: w for w in catalog}

    def sockets(item):
        return sorted({n for c in item["sockets"]["socketCategories"]
                       if c["socketCategoryHash"] == TRAITS for n in c["socketIndexes"]})

    def legal(w, n, perk):
        item = inventory[str(w["bungieHash"])]
        entry = item["sockets"]["socketEntries"][n]
        ph = entry.get("randomizedPlugSetHash")
        pool = pools.get(str(ph), {})
        definition = inventory[str(perk)]
        if (w["exotic"] or n not in sockets(item) or item.get("redacted") or item.get("blacklisted")
                or pool.get("isFakePlugSet") is not False
                or definition.get("itemTypeDisplayName") != "Trait"
                or definition.get("plug", {}).get("isDummyPlug") is not False
                or definition.get("redacted") or definition.get("blacklisted")
                or not any(p.get("currentlyCanRoll") is True and p["plugItemHash"] == perk
                           for p in pool.get("reusablePlugItems", []))):
            return None
        return {"id": w["id"], "hash": w["bungieHash"], "socket": n,
                "perkHash": perk, "plugSetHash": ph}

    found, scan = [], []
    for w in selected:
        item = inventory[str(w["bungieHash"])]
        matches = [r for n in sockets(item) if (r := legal(w, n, BASE))]
        found += matches
        scan.append({"id": w["id"], "hash": w["bungieHash"], "traitSockets": sockets(item), "matches": matches})
    require(found == EXPECTED, "exact one current BASIC canonical socket, no fallback")
    require(by_id["dream_breaker"]["family"] == "fusion_rifle", "supported family")
    w = next(w for w in selected if w["id"] == "dream_breaker")
    item = inventory[str(w["bungieHash"])]
    backup = [r for n in sockets(item) if (r := legal(w, n, BACKUP_PLAN))]
    require(backup == [{**EXPECTED[0], "perkHash": BACKUP_PLAN}], "Backup Plan same socket, never co-select")
    entry = item["sockets"]["socketEntries"][4]
    resource = {"stage": "W226", "perk": {"id": "cornered", "hash": BASE,
                "enemiesRequired": 2, "radiusMetres": 15, "chargeTimeMultiplier": .85, "lingerTicks": 30},
                "weapons": found}
    resource_raw = encode(resource)
    components = manifest["jsonWorldComponentContentPaths"]["en"]
    evidence = {"stage": "W226", "version": VERSION,
                "manifestComponents": {k: components[k] for k in
                    ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
                "inputs": pins, "ddc": {"url": URL, "tab": "Weapon Perks", "gid": 1662574278,
                    "row": 57, "htmlRowId": "1662574278R56", "rawRow": raw_row, "rowText": row_text},
                "basicDefinition": basic, "enhancedExcludedHash": ENHANCED,
                "enhancedExcluded": ["+10 Stability while active", "+5 passive Stability"],
                "canonicalWeaponCount": 65, "ownedRealWeaponCount": 1, "catalogScan": scan,
                "socketProof": {"id": w["id"], "hash": w["bungieHash"],
                    "socketCategories": item["sockets"]["socketCategories"], "socket": 4,
                    "entry": entry, "plugSet": pools["1206254527"]},
                "backupPlan": {"rolls": backup, "sameSocket": True, "coSelectable": False},
                "localPolicy": {"metresToBlocks": 1, "distance": "inclusive 3D footpoint radius",
                    "enemyPolicy": "WeaponThreatDetector: loaded living PvE enemies; exclude players, armor stands, tames, allies",
                    "chargeTicks": "ceil(acceptedBase.chargeTicks * 0.85); preserve every other field",
                    "linger": "30 ticks from first below-threshold observation; stow or identity invalidation revokes"},
                "resourceSHA256": hashlib.sha256(resource_raw).hexdigest()}
    pin_lines = "\n".join(f"- `{k}`: SHA-256 `{v['sha256']}` ({v['bytes']} bytes)." for k, v in pins.items())
    doc = f"""# W226 Cornered — BASIC only

[Destiny Data Compendium, Weapon Perks gid1662574278, row57]({URL}), HTML row `1662574278R56`:

> {row_text}

Apply only 2 enemies within 15 metres, charge/draw time ×0.85, linger 1.5 seconds = 30 ticks.
Enhanced hash `{ENHANCED}` and its active +10/passive +5 Stability are explicitly excluded.
Manifest `{VERSION}`; current official inventory and plugset component URLs are retained in source.json.

## Exact socket proof

Scan all 65 canonical identities; exactly **1 owned real weapon** matches: `dream_breaker` hash2931957300,
canonical trait socket4, randomized pool1206254527, BASIC perk1799762209, `currentlyCanRoll=true`,
`isFakePlugSet=false`, non-dummy/non-redacted/non-blacklisted Trait. No fabricated/fallback rolls.
`source.json` contains the complete bounded DDC row, definition, socket/pool and catalog scan.
Backup Plan1600092898 is also socket4/pool1206254527: the two perks cannot co-select and no stacking is added.

## Local application and integration contract

1 metre = 1 block, inclusive 3D footpoint radius. Match WeaponThreatDetector's loaded living PvE enemy
policy (exclude players, armor stands, tames, allies); no line-of-sight invention or chunk loading.
`WeaponCornered.update(p)` is the only entity-scanning/binding path. Master calls it on player ticks
and immediately before both accepted fusion-charge starts, then freezes the full result of
`WeaponCornered.charge(p, entry, base)`. Active charge ticks are `ceil(base.chargeTicks() * .85)`;
every other WeaponProfile field survives. Pure getters neither bind nor refresh linger.
The session pins owner/world/data/runtime/class/loadout mode, original held object/slot, identity and roll.
Actual stow, edits or invalidation revoke linger; first negative observation starts its exclusive deadline.
Master owns registration, shared runtime/handling/aim/shot-trait/command/GameTest wiring.

## Input pins

{pin_lines}

Resource SHA-256: `{evidence['resourceSHA256']}`.

Reproduce: `python3 scripts/build_cornered_w226.py --root X --check` (read-only).
Omit `--check` to write only the three generated resource/proof files. Source paths default to the
user-pinned /tmp inventory, plugsets and manifest plus /private/tmp/destiny-w226/ddc-perks-live.html;
explicit source flags are supported and must match the exact pins above.
"""
    return {RESOURCE: resource_raw, SOURCE: encode(evidence), DOC: doc.encode()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    p.add_argument("--plugsets", type=Path, default=Path("/tmp/destiny-weapons-w60/bungie-plugsets.json"))
    p.add_argument("--manifest", type=Path, default=Path("/tmp/destiny-weapons-w60/manifest.json"))
    p.add_argument("--ddc", type=Path, default=Path("/private/tmp/destiny-w226/ddc-perks-live.html"))
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    for name, raw in generate(args).items():
        path = args.root / name
        if args.check:
            require(path.read_bytes() == raw, "generated output differs: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        print(("verified " if args.check else "wrote ") + name)


if __name__ == "__main__":
    main()
