#!/usr/bin/env python3
"""Offline W77 exact-base Dragonfly socket extraction and bounded source evidence.

No downloads, builds, cache repair, or runtime integration. Eight literal data
pins bind the W40 selection/catalog to official cached manifest components and a
small research summary. --verify and --inspect-source are strictly read only.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/extract_dragonfly_w77.py"
PROFILE = "src/main/java/kim/biryeong/destiny/weapon/DragonflyProfile.java"
REF = "art/weapons/w77/references/"
NOTES = "art/weapons/w77/reference-notes.md"
TARGET = "src/main/resources/destiny/weapons/w77-dragonfly.json"
BASE, ENHANCED, OTHER = 2848615171, 169755979, 3865257976
TRAIT_CATEGORY = 4241085061
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
BUNGIE = "https://www.bungie.net"
OFFICIAL_URL = BUNGIE + "/7/en/News/Article/twid_07_03_2025"
COMMUNITY_URL = "https://www.light.gg/db/items/2848615171/dragonfly/"
DAMAGE_TYPES = {1: "KINETIC", 2: "ARC", 3: "SOLAR", 4: "VOID", 6: "STASIS", 7: "STRAND"}
SUPPORTED_ELEMENTS = {"ARC", "SOLAR", "VOID"}
PINS = {
    "selected": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "w40Provenance": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "catalog": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    "characteristics": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "research": "ca514c058c0461d8f445489bc9e6b3ccb0c1e96c3564003329181635db57ed66",
}
# Regression oracle only; the independent full scan below never filters by it.
EXPECTED_ROLLS = {
    ("brass_attacks", 2121785039, 4, 3403850295),
    ("distant_relation", 2034817450, 4, 3824767299),
    ("line_in_the_sand", 946443267, 4, 3257645194),
    ("long_arm", 8293111, 4, 619833418),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    if isinstance(value, str):
        return value.encode("utf-8")
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def row_key(row):
    return row["id"], row["hash"], row["socket"], row["plugSetHash"]


def extract(args):
    root = args.root.resolve()
    sources_dir = (args.sources_dir or root / "run/private-sources/w73").resolve()
    paths = {
        "selected": root / "art/weapons/w40/definitions.json",
        "w40Provenance": root / "art/weapons/w40/provenance.json",
        "catalog": root / "src/main/resources/destiny/weapons/w30.json",
        "characteristics": root / "src/main/resources/destiny/weapons/w40-characteristics.json",
        "inventory": args.inventory or sources_dir / "bungie-items.json",
        "plugSets": sources_dir / "bungie-plugsets.json",
        "manifest": sources_dir / "manifest.json",
        "research": root / (REF + "research.json"),
    }
    require(paths.keys() == PINS.keys(), "Every data input requires a literal SHA256 pin")
    sources, pins = {}, {}
    for key, path in paths.items():
        raw = path.read_bytes()
        require(digest(raw) == PINS[key], "Source SHA256 mismatch: " + key)
        sources[key] = json.loads(raw)
        resolved = path.resolve()
        pins[key] = {"path": str(resolved.relative_to(root)) if resolved.is_relative_to(root) else str(resolved),
                     "sha256": PINS[key], "bytes": len(raw)}

    response = sources["manifest"]
    require(response["ErrorCode"] == 1, "Cached manifest API response failed")
    manifest = response["Response"]
    inventory_path = "/common/destiny2_content/json/en/DestinyInventoryItemDefinition-" + SUFFIX
    plugsets_path = inventory_path.replace("DestinyInventoryItemDefinition-", "DestinyPlugSetDefinition-")
    components = manifest["jsonWorldComponentContentPaths"]["en"]
    require(manifest["version"] == VERSION
            and components["DestinyInventoryItemDefinition"] == inventory_path
            and components["DestinyPlugSetDefinition"] == plugsets_path,
            "Official components must belong to the exact pinned manifest")
    w40 = sources["w40Provenance"]
    require(w40["manifest"] == {"version": VERSION, "path": inventory_path}
            and w40["cachedInventorySha256"] == PINS["inventory"]
            and w40["source"] == BUNGIE + inventory_path, "W40 official lineage mismatch")
    selected, inventory, plugsets = sources["selected"], sources["inventory"], sources["plugSets"]
    ids = {w["id"] for w in selected}
    catalog = {w["id"]: w for w in sources["catalog"]}
    require(len(selected) == len(ids) == len({w["bungieHash"] for w in selected}) == 63,
            "Expected 63 unique exact selected weapons")
    require(len(catalog) == len(sources["catalog"]) == 63 and set(catalog) == ids
            and sources["characteristics"] == selected, "W30/W40 runtime catalog binding changed")
    definitions = []
    same_name = {v["hash"] for v in inventory.values() if v.get("displayProperties", {}).get("name") == "Dragonfly"}
    require(same_name == {BASE, ENHANCED, OTHER}, "New same-name Dragonfly identity requires explicit review")
    for h, kind, disposition in ((BASE, "Trait", "supported exact base only"),
                                 (ENHANCED, "Enhanced Trait", "excluded enhanced"),
                                 (OTHER, "Trait", "excluded different same-name hash")):
        perk = inventory[str(h)]
        require(perk["hash"] == h and perk["displayProperties"]["name"] == "Dragonfly"
                and perk["itemTypeDisplayName"] == kind and perk["itemType"] == 19
                and not perk["redacted"] and not perk["blacklisted"] and not perk["plug"]["isDummyPlug"],
                "Invalid official Dragonfly identity: " + str(h))
        definitions.append({"hash": h, "name": "Dragonfly", "itemTypeDisplayName": kind,
                            "disposition": disposition})
    require(inventory[str(BASE)]["displayProperties"]["description"] ==
            "Precision kills create an elemental damage explosion.", "Base trigger description changed")

    research = sources["research"]
    official, community = research["official"], research["community"]
    require(research["stage"] == "W77" and official["url"] == OFFICIAL_URL
            and official["authority"] == "official" and official["publicationDate"] == "2025-07-03"
            and official["weaponArchetypeScaling"] is False
            and community["url"] == COMMUNITY_URL and community["authority"] == "community"
            and community["apiId"] == BASE and community["radiusMeters"] == 4.5
            and community["lastUpdatedReported"] == "2025-12-27", "Research evidence boundary changed")

    rolls, proofs, direct, excluded, other_base, audit = [], [], [], [], [], []
    socket_total = set_total = 0
    # All 63 hashes, ALL socket categories, all direct defaults/reusable items,
    # and BOTH plug-set fields. Neither names nor families select candidates.
    for weapon in sorted(selected, key=lambda w: (w["id"], w["bungieHash"])):
        wid = weapon["id"]
        item = inventory[str(weapon["bungieHash"])]
        require(item["hash"] == weapon["bungieHash"] and item["itemType"] == 3
                and not item["redacted"] and not item["blacklisted"]
                and (item["inventory"]["tierType"] == 6) == weapon["exotic"]
                and DAMAGE_TYPES[item["defaultDamageType"]] == weapon["damage"],
                "Invalid exact weapon/damage binding: " + wid)
        sockets = item.get("sockets", {})
        entries = sockets.get("socketEntries", [])
        trait_indexes = {i for c in sockets.get("socketCategories", [])
                         if c["socketCategoryHash"] == TRAIT_CATEGORY for i in c["socketIndexes"]}
        require(all(0 <= i < len(entries) for i in trait_indexes), "Invalid trait socket indexes: " + wid)
        before = len(rolls)
        socket_audit = []
        for index, socket in enumerate(entries):
            socket_total += 1
            identity = {"id": wid, "hash": item["hash"], "socket": index}
            direct_hashes = {socket["singleInitialItemHash"],
                             *[p["plugItemHash"] for p in socket.get("reusablePlugItems", [])]}
            for h in (BASE, ENHANCED, OTHER):
                if h not in direct_hashes:
                    continue
                if h == BASE:
                    require(weapon["damage"] in SUPPORTED_ELEMENTS,
                            "Unsupported Dragonfly element found (not filtered): " + wid + " " + weapon["damage"])
                option = {**identity, "perkHash": h, "source": "direct",
                          "initialPerk": socket["singleInitialItemHash"] == h,
                          "traitCategory": index in trait_indexes}
                (direct if h == BASE else excluded).append(option)
            reviewed = []
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                set_hash = socket.get(field)
                if not set_hash:
                    continue
                set_total += 1
                pool = plugsets[str(set_hash)]
                require(pool["hash"] == set_hash and not pool["redacted"] and not pool["blacklisted"],
                        "Invalid referenced plug set: " + str(set_hash))
                pool_items = pool.get("reusablePlugItems", [])
                reviewed.append({"field": field, "hash": set_hash, "isFakePlugSet": pool["isFakePlugSet"],
                                 "entryCount": len(pool_items)})
                for h in (BASE, ENHANCED, OTHER):
                    matches = [{"index": n, "item": p} for n, p in enumerate(pool_items) if p["plugItemHash"] == h]
                    if not matches:
                        continue
                    option = {**identity, "perkHash": h, "plugSetHash": set_hash, "plugSetField": field,
                              "isFakePlugSet": pool["isFakePlugSet"], "traitCategory": index in trait_indexes,
                              "matchingEntries": matches}
                    if h != BASE:
                        excluded.append(option)
                        continue
                    # Report ANY unsupported elemental occurrence, even in a non-runtime pool.
                    require(weapon["damage"] in SUPPORTED_ELEMENTS,
                            "Unsupported Dragonfly element found (not filtered): " + wid + " " + weapon["damage"])
                    rollable = [m for m in matches if m["item"].get("currentlyCanRoll") is True]
                    if (field != "randomizedPlugSetHash" or index not in trait_indexes
                            or pool["isFakePlugSet"] is not False or not rollable or weapon["exotic"]):
                        other_base.append(option)
                        continue
                    require(len(matches) == len(rollable) == 1, "Duplicate/unrollable base entries need explicit audit")
                    require(catalog[wid]["family"] in {"scout_rifle", "sidearm", "linear_fusion_rifle"},
                            "Unsupported eligible weapon family found (not filtered): " + wid)
                    row = {**identity, "perkHash": BASE, "plugSetHash": set_hash}
                    rolls.append(row)
                    proofs.append({**row, "damage": weapon["damage"], "family": catalog[wid]["family"],
                                   "officialDamageType": item["defaultDamageType"],
                                   "socketCategoryHash": TRAIT_CATEGORY, "plugSetField": field,
                                   "isFakePlugSet": False, "matchingEntries": matches})
            socket_audit.append({"socket": index, "traitCategory": index in trait_indexes,
                                 "singleInitialItemHash": socket["singleInitialItemHash"],
                                 "directReusableCount": len(socket.get("reusablePlugItems", [])),
                                 "reviewedPlugSets": reviewed})
        audit.append({"id": wid, "hash": item["hash"], "damage": weapon["damage"],
                      "family": catalog[wid]["family"], "exotic": weapon["exotic"], "socketCount": len(entries),
                      "traitSocketIndexes": sorted(trait_indexes), "baseRandomizedRows": len(rolls) - before,
                      "sockets": socket_audit})

    # Regression checks follow the full independent discovery, never seed it.
    require((len(audit), socket_total, set_total) == (63, 678, 627), "Full selected scan coverage changed")
    require({row_key(r) for r in rolls} == EXPECTED_ROLLS and len(rolls) == 4
            and len({r["id"] for r in rolls}) == 4, "Exact Dragonfly tuples differ from four-row regression oracle")
    require(not direct and not excluded and not other_base,
            "New direct/enhanced/other-hash/non-runtime occurrence requires explicit review")
    require(not any(w["exotic"] for w in selected), "Selected exotic/catalyst coverage changed")
    rolls.sort(key=row_key)
    proofs.sort(key=row_key)
    radius_source = {k: community[k] for k in ("authority", "url", "sourceSha256")}
    official_source = {k: official[k] for k in ("authority", "url", "sourceSha256")}
    damage_policy = {
        "authority": "local_authored_pve", "units": "Minecraft HP", "scaling": "fixed_perk_damage",
        "description": "Authored PvE center damage of 10 Minecraft HP for every eligible weapon. No conversion from Destiny damage and no multiplication by weapon damage, archetype, ammo, critical, range, or active weapon damage buffs.",
    }
    falloff_policy = {
        "authority": "local_authored_pve", "units": "damage fraction", "scaling": "linear_floor",
        "description": "For finite distance d >= 0: inside inclusive radius r, fraction=max(0.3,1-d/r); outside r, fraction=0. Thus center damage is 10 HP and boundary damage is 3 HP. One sourced meter maps to one Minecraft block. Curve, 0.3 floor, boundary inclusion, and unit mapping are local choices, not sourced Destiny mechanics.",
    }
    resource = {"stage": "W77", "perk": {"id": "dragonfly", "hash": BASE, "radiusMeters": 4.5,
                "damageHp": 10.0, "falloffFloor": 0.3, "radiusSource": radius_source,
                "officialChange": official_source, "damagePolicy": damage_policy, "falloffPolicy": falloff_policy},
                "weapons": rolls}
    pools = {
        "stage": "W77", "selectedCount": 63, "socketCount": socket_total,
        "plugSetReferencesReviewed": set_total, "runtimeRollCount": len(rolls), "perkDefinitions": definitions,
        "policy": "Require exact base 2848615171, exact selected item hash, trait category, nonfake randomized pool and currentlyCanRoll=true. Zero weights do not override the explicit rollability flag. Direct defaults/reusable plugs and reusable plug sets are audited separately; none add a row. Never infer pools from names/families. Unsupported elements cause failure and are never silently filtered.",
        "runtimeRolls": rolls, "weapons": proofs, "directSocketOptions": direct,
        "enhancedAndOtherHashOccurrencesExcluded": excluded, "otherBasePoolOccurrencesNotSelected": other_base,
        "unsupportedBaseElementOccurrences": [], "supportedElements": sorted(SUPPORTED_ELEMENTS),
        "noOfficialBaseRandomizedRollIds": sorted(ids - {r["id"] for r in rolls}),
        "exoticCatalystScope": "No selected weapon is exotic. Selected-63 coverage only; no global catalyst census or global availability claim.",
        "selectionAudit": audit,
    }
    mechanics = {
        "stage": "W77", "baseHash": BASE, "enhancedHashExcluded": ENHANCED, "otherSameNameHashExcluded": OTHER,
        "officialIdentity": definitions, "trigger": "precision weapon final blow",
        "officialPrimary": official, "communityRadius": community,
        "serverPolicy": {"damageHp": 10.0, "radiusBlocks": 4.5, "falloffFloor": 0.3,
                         "damage": damage_policy, "falloff": falloff_policy,
                         "elements": "Match triggering weapon ARC/SOLAR/VOID. No subclass debuff or elemental verb is implied.",
                         "selection": "An eligible optional socket roll must actually be selected on the triggering weapon copy.",
                         "runtimeOwnership": "The parent worker owns event ordering, PvE target validation, friendly/self protection, line of sight, proc recursion prevention, VFX, and existing sound aliases."},
        "sourceBoundary": "Official manifest supplies identity, exact sockets, explicit rollability and weapon elements. Bungie July 3, 2025 announces normalized combatant explosion scaling replacing archetype scaling. light.gg supplies community 4.5 m radius and matching element. Fixed 10 Minecraft HP, linear 0.3 floor and meter/block mapping are local authored PvE policy. No original damage formula, enhanced behavior, or fresh gameplay measurement is claimed.",
        "researchRepresentation": research["boundary"],
    }
    outputs = {TARGET: resource, REF + "socket-pools.json": pools,
               REF + "mechanics.json": mechanics, NOTES: make_notes(rolls, proofs)}
    profile_raw = (root / PROFILE).read_bytes()
    outputs[REF + "provenance.json"] = {
        "stage": "W77", "manifestVersion": VERSION, "inventoryUrl": BUNGIE + inventory_path,
        "plugSetsUrl": BUNGIE + plugsets_path, "sourceHashes": pins,
        "generator": SCRIPT, "generatorSha256": digest(Path(__file__).resolve().read_bytes()),
        "profile": PROFILE, "profileSha256": digest(profile_raw),
        "outputHashes": {name: digest(encoded(value)) for name, value in outputs.items()},
        "capturedDate": research["capturedDate"], "sourceBoundary": mechanics["sourceBoundary"],
        "researchRepresentation": research["boundary"],
        "reproduce": "rtk proxy python3 scripts/extract_dragonfly_w77.py --verify",
        "inspect": "rtk proxy python3 scripts/extract_dragonfly_w77.py --inspect-source",
        "verification": "Eight literal data SHA256 pins; exact comparison of all five generated files including notes/provenance. Generator and hand-authored profile hashes are recorded without a self-hash cycle. Inspection and verification do not write files, create directories, fetch, build, or repair caches. Cache overrides retain identical required content hashes. The profile itself is not generated or compiled by this script.",
    }
    require(len(outputs) == 5, "Expected five generated outputs")
    return outputs, paths


def make_notes(rolls, proofs):
    elements = {r["id"]: r["damage"] for r in proofs}
    rows = "\n".join(f'| {r["id"]} | {r["hash"]} | {r["socket"]} | {r["plugSetHash"]} | {elements[r["id"]]} |' for r in rolls)
    return f'''# W77 Dragonfly source pipeline

The pinned official manifest yields **four** exact base **2848615171** rolls after
an independent traversal of all **63** selected hashes, **678 sockets**, and
**627 plug-set references**. Socket indexes are zero based.

| ID | Weapon hash | Socket | Randomized plug set | Element |
|---|---:|---:|---:|---|
{rows}

All four pools are nonfake randomized trait sets in category **4241085061**;
their exact base entries have `currentlyCanRoll=true`. Both weight fields are
zero and do not negate that flag. No base direct defaults/reusable items,
enhanced **169755979**, different same-name **3865257976**, or non-runtime base
pool occurrences were found. All four are ARC/SOLAR/VOID. No Kinetic, Stasis or
Strand occurrence was filtered: encountering any unsupported base element
fails explicitly. The 59 negative IDs and every inspected socket/reference are
recorded in `references/socket-pools.json`. The selected inventory has no
exotics; this is not a global catalyst or global drop-availability census.

## Integration API

`DragonflyProfile.ID = "dragonfly"`, `HASH = 2848615171L`.

* `rolls(): List<WeaponPerks.Roll>`: the four exact tuples above; each perk hash is 2848615171.
* `radius(): double`: **4.5**, community meters mapped to Minecraft blocks.
* `damage(): float`: **10f**, fixed authored Minecraft PvE center damage.
* `falloffFloor(): float`: **.3f**, authored minimum fraction inside the radius.
* `perk(): Perk`: typed runtime data with separate radius provenance and local policies.

The profile validates stage, trait identity/hash, finite exact tuning values,
source authorities/URLs/hash shape, policy labels, complete exact socket tuples,
catalog membership, W40 item hash, nonexotic status, supported families and
ARC/SOLAR/VOID elements. It exposes immutable rolls. Proven eligible rolls must
still be selected on the weapon copy; runtime integration belongs to the parent.

## Sources and authored policy

[Bungie's July 3, 2025 TWID]({OFFICIAL_URL}), under **Chain Reaction, Dragonfly,
Firefly**, announces that The Edge of Fate replaces combatant weapon-archetype
explosion scaling with more normalized perk scaling. It does not establish a
Minecraft HP conversion, universal damage number, radius or falloff curve.
The announcement concerns the July 15 expansion changes.

The exact-base [light.gg Community Research]({COMMUNITY_URL}) reports a **4.5 m**
weapon-element blast on precision kills, with reported update **2025-12-27**.
This is community evidence. The bounded English search result explicitly
identified Basic / Trait and API ID 2848615171; direct opens returned HTTP 402.
The stale **3 m** summary and weapon-archetype multipliers are not used.

**10 Minecraft HP is locally authored PvE tuning**, shared by all four eligible
weapons. It is not original Destiny damage and does not scale with weapon shot
damage, archetype, ammo, critical/range modifiers or active damage perks.
For finite nonnegative distance `d`, use `max(0.3, 1-d/4.5)` inside the inclusive
4.5-block radius and zero outside. Thus the center receives 10 HP and the edge
3 HP. The curve, floor, boundary inclusion and one-meter/one-block mapping are
project policy. Radius provenance is independent of the local damage policy.

`references/research.json` is a small pinned input with paraphrased claims,
URLs, dates, retrieval limitations and SHA256 identifiers for the exact
URL-bound web-tool result representations. No article/page payload is stored.
Those hashes are not original HTML hashes; offline verification cannot recover
or revalidate the discarded responses. `references/mechanics.json` preserves
this distinction. No enhanced behavior or fresh gameplay measurement is claimed.

## Offline reproduction

```sh
rtk proxy python3 scripts/extract_dragonfly_w77.py
rtk proxy python3 scripts/extract_dragonfly_w77.py --verify
rtk proxy python3 scripts/extract_dragonfly_w77.py --inspect-source
```

The default cache is the existing `run/private-sources/w73` official component
cache. Eight literal SHA256 pins bind W40 definitions/provenance, W30 catalog,
W40 runtime characteristics, inventory, plug sets, manifest and research summary.
The manifest version is `{VERSION}`. No older stage or cache is rewritten.

`--root` chooses the input checkout; `--sources-dir`/`--inventory` relocate
byte-identical caches; `--output-root` writes a separate reproduction tree.
Generation writes only the runtime JSON, socket/mechanics/provenance JSON and
these notes. `research.json` and Java are authored inputs, not generated files.
Provenance records the generator/profile hashes and four other output hashes.
`--verify` compares all five generated files byte for byte. `--inspect-source`
checks the pins and full extraction and prints input hashes plus eligible tuples.
Both modes are offline and read only, including failure paths: no downloads,
directory creation, cache repair, builds, Java/native launches or audio creation.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify", action="store_true", help="Offline read-only byte-exact check of all generated files")
    modes.add_argument("--inspect-source", action="store_true", help="Offline read-only source hashes and exact eligible tuples")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--sources-dir", type=Path, help="Official cache; default run/private-sources/w73")
    parser.add_argument("--inventory", type=Path, help="Override official inventory cache without relaxing its pin")
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    try:
        outputs, inputs = extract(args)
        output_root = (args.output_root or args.root).resolve()
        input_paths = {p.resolve() for p in inputs.values()} | {
            Path(__file__).resolve(), (args.root / SCRIPT).resolve(), (args.root / PROFILE).resolve()}
        resolved = [(output_root / name).resolve() for name in outputs]
        require(len(set(resolved)) == len(outputs), "Output paths alias each other")
        for name, path in zip(outputs, resolved):
            require(path.is_relative_to(output_root) and path not in input_paths,
                    "Output escapes root or aliases an input: " + name)
        if args.inspect_source:
            for key, pin in outputs[REF + "provenance.json"]["sourceHashes"].items():
                print(key + " " + pin["sha256"] + " " + pin["path"])
        elif args.verify:
            failures = []
            for (name, value), path in zip(outputs.items(), resolved):
                try:
                    if path.read_bytes() != encoded(value):
                        failures.append("Generated bytes differ: " + name)
                except OSError as error:
                    failures.append("Unreadable output " + name + ": " + str(error))
            require(not failures, "\n".join(failures))
        else:
            for (_, value), path in zip(outputs.items(), resolved):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(encoded(value))
        mode = "INSPECTED" if args.inspect_source else "VERIFIED" if args.verify else "GENERATED"
        print(mode + ": W77; 63 selected; 678 sockets; 627 plug-set references; four exact-base rolls.")
        proofs = outputs[REF + "socket-pools.json"]["weapons"]
        for row in proofs:
            print(f'{row["id"]} {row["hash"]} socket {row["socket"]} perk {BASE} set {row["plugSetHash"]} {row["damage"]}')
        print("radius()=4.5 community meters; damage()=10f authored Minecraft PvE HP; falloffFloor()=.3f local.")
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print("W77 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
