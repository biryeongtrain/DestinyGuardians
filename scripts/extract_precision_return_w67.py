#!/usr/bin/env python3
"""Offline W67 exact-base precision-return rolls and measured mechanics.

All consumed inputs are SHA256 pinned. --verify reads and compares all five
outputs without creating directories, repairing caches, writing or networking.
Raw web captures remain private. No third research capture is consumed.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/extract_precision_return_w67.py"
REF = "art/weapons/w67/references/"
NOTES = "art/weapons/w67/reference-notes.md"
TARGET = "src/main/resources/destiny/weapons/w67-precision-return.json"
TRAIT_CATEGORY = 4241085061
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
BUNGIE = "https://www.bungie.net"
PERKS = (
    ("triple_tap", 3400784728, "Triple Tap", 3, 1, 573122728,
     "research2.json", "https://www.light.gg/db/items/3400784728/triple-tap/?_=879"),
    ("fourth_times_the_charm", 1354429876, "Fourth Time's the Charm", 4, 2, 848860060,
     "research1.json", "https://www.light.gg/db/items/1354429876/fourth-times-the-charm/?_=935"),
)
BASES = {p[1] for p in PERKS}
ENHANCED = {p[5] for p in PERKS}
PINS = {
    "selected": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "w40Provenance": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "research1.json": "86da1adbcf1aa29681aaf94a99f97778f05e46b1b0cdb7cb2c276e4e35fed629",
    "research2.json": "bd6d0ebccf0c5e0cf4d9307c630909759d970eaacdafac55ffc47b65aa2963ef",
}
# Added AFTER independently scanning every selected socket. Regression only;
# never used to select weapons, infer roll eligibility, or drive enumeration.
# id, exact weapon hash, zero-based socket, exact perk hash, randomized set hash.
EXPECTED_RANDOM = {
    ("aishas_embrace", 2638190703, 3, 3400784728, 7997267),
    ("ammit_ar2", 2119346509, 3, 3400784728, 1723759242),
    ("austringer", 3055790362, 3, 3400784728, 2750499928),
    ("distant_relation", 2034817450, 3, 3400784728, 1131958073),
    ("duke_mk_44", 2112909414, 2, 3400784728, 3744182842),
    ("aishas_embrace", 2638190703, 4, 1354429876, 4211351701),
    ("beloved", 3107853529, 3, 1354429876, 1196545279),
    ("retrofit_escapade", 3103325054, 3, 1354429876, 3756086698),
    ("seventh_seraph_officer_revolver", 3037520408, 3, 1354429876, 903350103),
}
EXPECTED_DIRECT = {
    ("distant_relation", 2034817450, 3, 3400784728),
    ("aishas_embrace", 2638190703, 3, 3400784728),
    ("retrofit_escapade", 3103325054, 3, 1354429876),
}
EXPECTED_ENHANCED = {
    ("austringer", 3055790362, 3, 573122728, 2750499928),
    ("ammit_ar2", 2119346509, 3, 573122728, 1723759242),
    ("beloved", 3107853529, 3, 848860060, 1196545279),
    ("retrofit_escapade", 3103325054, 3, 848860060, 3756086698),
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
    return tuple(row[k] for k in ("id", "hash", "socket", "perkHash", "plugSetHash"))


def option_key(option):
    return (option["id"], option["hash"], option["socket"], option["perkHash"],
            option.get("plugSetField", ""), option.get("plugSetHash", 0))


def measured_section(capture, url, perk_hash, hits, rounds):
    """Bind measurements to ONE exact base URL and its own community section."""
    require(capture.get("isError") is False, "Failed research capture: " + url)
    text = "\n".join(c.get("text", "") for c in capture["content"])
    blocks = [block for block in text.split("--------------------------------------------------------------------------------")
              if "(" + url + ")" in block]
    require(len(blocks) == 1, "Missing or ambiguous exact-base URL: " + url)
    block = blocks[0]
    require("API ID: " + str(perk_hash) in block and "Basic / Trait" in block,
            "Research identity is not the exact base trait: " + url)
    require(block.count("#### Community Research") == 1 and "#### Details" in block,
            "Missing bounded community section: " + url)
    section = block.split("#### Community Research", 1)[1].split("#### Details", 1)[0]
    match = re.search(r"Scoring\s+(\d+)\s+Precision\s+Hits\s+within\s+(\d+)\s+seconds.*?refills\s+(\d+)\s+Ammo", section)
    require(match is not None and tuple(map(int, match.groups())) == (hits, 2, rounds),
            "Base hit threshold, interval or return measurement changed: " + url)
    for phrase in ("of each", "from thin air", "base capacity", "persists through stow", "2024-07-30"):
        require(phrase in section, "Missing base measurement " + phrase + ": " + url)
    # Return no captured prose: generated public evidence is paraphrased.


def extract(args):
    root = args.root.resolve()
    paths = {
        "selected": root / "art/weapons/w40/definitions.json",
        "w40Provenance": root / "art/weapons/w40/provenance.json",
        "inventory": args.inventory,
        "plugSets": args.shared_sources_dir / "bungie-plugsets.json",
        "manifest": args.shared_sources_dir / "manifest.json",
        "research1.json": args.sources_dir / "research1.json",
        "research2.json": args.sources_dir / "research2.json",
    }
    require(paths.keys() == PINS.keys(), "Every consumed input must have a hardcoded SHA256 pin")
    sources, pins = {}, {}
    for key, path in paths.items():
        raw = path.read_bytes()
        require(digest(raw) == PINS[key], "Source SHA256 mismatch: " + key)
        sources[key] = json.loads(raw)
        path = path.resolve()
        pins[key] = {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                     "sha256": PINS[key], "bytes": len(raw)}
    require(sources["manifest"]["ErrorCode"] == 1, "Manifest API response failed")
    manifest = sources["manifest"]["Response"]
    inventory_path = "/common/destiny2_content/json/en/DestinyInventoryItemDefinition-" + SUFFIX
    plugsets_path = inventory_path.replace("DestinyInventoryItemDefinition-", "DestinyPlugSetDefinition-")
    components = manifest["jsonWorldComponentContentPaths"]["en"]
    require(manifest["version"] == VERSION
            and components["DestinyInventoryItemDefinition"] == inventory_path
            and components["DestinyPlugSetDefinition"] == plugsets_path,
            "Inventory and plug sets must belong to the exact pinned manifest")
    w40 = sources["w40Provenance"]
    require(w40["manifest"] == {"version": VERSION, "path": inventory_path}
            and w40["cachedInventorySha256"] == PINS["inventory"]
            and w40["source"] == BUNGIE + inventory_path, "W40 source lineage mismatch")
    selected, inventory, plugsets = sources["selected"], sources["inventory"], sources["plugSets"]
    require(len(selected) == len({w["id"] for w in selected})
            == len({w["bungieHash"] for w in selected}) == 63, "Expected 63 unique selected weapons")
    definitions = []
    for _, base, name, hits, rounds, enhanced, capture_name, url in PERKS:
        for h, kind in ((base, "Trait"), (enhanced, "Enhanced Trait")):
            perk = inventory[str(h)]
            require(perk["hash"] == h and perk["displayProperties"]["name"] == name
                    and perk["itemTypeDisplayName"] == kind and perk["itemType"] == 19
                    and not perk["redacted"] and not perk["blacklisted"]
                    and not perk["plug"]["isDummyPlug"], "Invalid precision-return definition: " + str(h))
            description = perk["displayProperties"]["description"].lower()
            require("precision hits" in description and "magazine" in description,
                    "Official trigger/return description changed: " + str(h))
            definitions.append({"hash": h, "name": name, "itemTypeDisplayName": kind,
                                "itemType": 19, "disposition": "supported exact base" if h == base else "excluded enhanced"})
        measured_section(sources[capture_name], url, base, hits, rounds)

    rows, proofs, direct, enhanced_options, other_base, exotic_options, audit = [], [], [], [], [], [], []
    # Enumeration is intentionally independent of EXPECTED_* and covers ALL
    # selected items, ALL sockets and BOTH referenced plug-set fields.
    for weapon in sorted(selected, key=lambda w: (w["id"], w["bungieHash"])):
        item = inventory[str(weapon["bungieHash"])]
        require(item["hash"] == weapon["bungieHash"] and item["itemType"] == 3
                and not item["redacted"] and not item["blacklisted"]
                and (item["inventory"]["tierType"] == 6) == weapon["exotic"],
                "Invalid exact selected weapon: " + weapon["id"])
        sockets = item.get("sockets", {})
        entries = sockets.get("socketEntries", [])
        trait_indexes = {i for c in sockets.get("socketCategories", [])
                         if c["socketCategoryHash"] == TRAIT_CATEGORY for i in c["socketIndexes"]}
        require(all(0 <= i < len(entries) for i in trait_indexes), "Invalid trait indexes: " + weapon["id"])
        socket_audit = []
        before = len(rows)
        for index, socket in enumerate(entries):
            identity = {"id": weapon["id"], "hash": item["hash"], "socket": index}
            category = TRAIT_CATEGORY if index in trait_indexes else None
            direct_hashes = {socket["singleInitialItemHash"],
                             *[p["plugItemHash"] for p in socket.get("reusablePlugItems", [])]}
            for h in sorted(BASES | ENHANCED):
                if h not in direct_hashes:
                    continue
                option = {**identity, "perkHash": h, "source": "direct",
                          "initialPerk": socket["singleInitialItemHash"] == h,
                          "reusablePlugItems": [p for p in socket.get("reusablePlugItems", []) if p["plugItemHash"] == h],
                          "socketCategoryHash": category}
                (enhanced_options if h in ENHANCED else exotic_options if weapon["exotic"] else direct).append(option)
            reviewed_sets = []
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                set_hash = socket.get(field)
                if not set_hash:
                    continue
                pool = plugsets[str(set_hash)]
                require(pool["hash"] == set_hash and not pool["redacted"] and not pool["blacklisted"],
                        "Missing or invalid referenced plug set: " + str(set_hash))
                pool_items = pool.get("reusablePlugItems", [])
                reviewed_sets.append({"field": field, "hash": set_hash, "isFakePlugSet": pool["isFakePlugSet"],
                                      "entryCount": len(pool_items)})
                for h in sorted(BASES | ENHANCED):
                    matches = [{"index": n, "item": p} for n, p in enumerate(pool_items) if p["plugItemHash"] == h]
                    if not matches:
                        continue
                    option = {**identity, "perkHash": h, "plugSetHash": set_hash, "plugSetField": field,
                              "isFakePlugSet": pool["isFakePlugSet"], "socketCategoryHash": category,
                              "matchingEntries": matches}
                    if h in ENHANCED:
                        enhanced_options.append(option)
                        continue
                    if weapon["exotic"]:
                        exotic_options.append(option)
                        continue
                    eligible = [m for m in matches if m["item"].get("currentlyCanRoll") is True]
                    if (field != "randomizedPlugSetHash" or not eligible or category != TRAIT_CATEGORY
                            or pool["isFakePlugSet"] is not False or item["itemTypeDisplayName"] in ("Sword", "Glaive")):
                        other_base.append(option)
                        continue
                    require(len(matches) == len(eligible) == 1,
                            "Duplicate/unrollable base entries require explicit audit: " + weapon["id"])
                    row = {**identity, "perkHash": h, "plugSetHash": set_hash}
                    rows.append(row)
                    proofs.append({**row, "selection": "randomized", "socketCategoryHash": TRAIT_CATEGORY,
                                   "weaponType": item["itemTypeDisplayName"], "socketEntry": socket,
                                   "plugSetField": field, "isFakePlugSet": False, "matchingEntries": eligible})
            socket_audit.append({"socket": index, "traitCategory": index in trait_indexes,
                                 "singleInitialItemHash": socket["singleInitialItemHash"],
                                 "directReusableCount": len(socket.get("reusablePlugItems", [])),
                                 "reviewedPlugSets": reviewed_sets})
        audit.append({"id": weapon["id"], "hash": item["hash"], "weaponType": item["itemTypeDisplayName"],
                      "exotic": weapon["exotic"], "socketCount": len(entries),
                      "traitSocketIndexes": sorted(trait_indexes), "randomizedBaseRows": len(rows) - before,
                      "sockets": socket_audit})

    # The literal oracle is checked only after enumeration completes.
    require({row_key(r) for r in rows} == EXPECTED_RANDOM and len(rows) == 9,
            "Independent enumeration differs from the nine-row regression set")
    require({tuple(r[k] for k in ("id", "hash", "socket", "perkHash")) for r in direct} == EXPECTED_DIRECT
            and len(direct) == 3, "Direct occurrence regression changed")
    row_sockets = {row_key(r)[:4] for r in rows}
    for option in direct:
        require(tuple(option[k] for k in ("id", "hash", "socket", "perkHash")) in row_sockets,
                "Direct option does not overlap its own exact randomized perk row")
        option.update(alsoProvenRandomized=True, addsRuntimeRow=False)
    require({row_key(e) for e in enhanced_options} == EXPECTED_ENHANCED and len(enhanced_options) == 4
            and all(e.get("plugSetField") == "randomizedPlugSetHash" for e in enhanced_options),
            "Enhanced occurrence regression changed")
    require(not other_base, "Additional noneligible base evidence requires explicit audit")
    selected_exotics = [w["id"] for w in selected if w["exotic"]]
    require(not selected_exotics and not exotic_options, "Exotic/catalyst selected coverage changed")
    rows.sort(key=row_key)
    proofs.sort(key=row_key)
    direct.sort(key=option_key)
    enhanced_options.sort(key=option_key)
    resource = {"stage": "W67", "perks": [
        {"id": perk_id, "hash": base, "hits": hits, "returnRounds": rounds, "windowTicks": 40,
         "weapons": [r for r in rows if r["perkHash"] == base]}
        for perk_id, base, _, hits, rounds, _, _, _ in PERKS]}
    coverage = {r["id"] for r in rows}
    pools = {
        "stage": "W67", "selectedCount": 63, "supportedCount": len(coverage), "poolRows": len(rows),
        "randomizedPoolRows": len(rows), "fixedDirectRows": 0,
        "perkDefinitions": definitions, "provenBaseHashes": sorted(BASES),
        "rowsByPerk": {perk_id: sum(r["perkHash"] == base for r in rows)
                       for perk_id, base, *_ in PERKS},
        "policy": "Scan all 63 selected exact hashes and all sockets, direct options and both plug-set fields. Emit only exact base hashes from their own real randomized trait pools with currentlyCanRoll=true. Exclude fake sets, exotics, catalysts, swords, glaives and enhanced hashes. Socket indexes are zero based. Zero weight does not override currentlyCanRoll. Direct defaults add no runtime rows.",
        "weapons": proofs, "directSocketOptions": direct,
        "otherBasePoolOccurrencesNotSelected": other_base,
        "enhancedSelectedOptionsExcluded": enhanced_options,
        "exoticBaseOccurrencesExcluded": exotic_options,
        "exoticCatalystExclusion": {
            "selectedExoticCount": 0, "selectedExoticIds": [],
            "policy": "An exotic or catalyst cannot qualify through a matching name, description, catalyst-granted trait or secondary weapon page. Only the selected nonexotic weapon's exact base randomized trait pool can qualify.",
            "secondaryCatalystResultsUsedAsEligibility": False,
            "scope": "No exotics occur among these 63 selected definitions. This is not a global scan of every catalyst in the manifest.",
        },
        "selectionAudit": audit,
        "unsupportedSelectedIds": sorted(w["id"] for w in selected if w["id"] not in coverage),
    }
    mechanics = {
        "stage": "W67", "ticksPerSecond": 20, "baseWindowSeconds": 2, "windowTicks": 40,
        "windowMeaning": "Maximum elapsed time between successive qualifying precision hits; not a deadline for the entire group of three or four.",
        "perks": [
            {"id": perk_id, "baseHash": base, "enhancedHashExcluded": enhanced,
             "hits": hits, "returnRounds": rounds,
             "officialDescriptionSupports": "Precision impacts quickly repeated can refill the magazine; the official description specifies the returned round count.",
             "secondaryMeasurements": {
                 "url": url, "publisher": "light.gg", "primary": False,
                 "section": "Community Research", "exactPerkHash": base, "privateCapture": capture,
                 "lastUpdatedReported": "2024-07-30", "hits": hits, "returnRounds": rounds,
                 "secondsBetweenPrecisionHits": 2, "persistsThroughStow": True,
                 "consumesReserves": False, "maximumMagazine": "base capacity",
                 "retrieval": "Pinned search capture bound to this exact base URL and its own community section. Community documentation, not a fresh gameplay measurement or Bungie assertion.",
             }} for perk_id, base, _, hits, rounds, enhanced, capture, url in PERKS],
        "sourceAudit": {
            "official": "Pinned Bungie inventory and plug sets establish exact hashes, official descriptions and eligible selected rolls. They do not establish numeric hit thresholds, timing, reserve generation, magazine cap, stow persistence or reset rules.",
            "measuredSecondary": "Each exact-base light.gg section independently states its hit threshold, two-second inter-hit interval, return count, ammunition generation, base-cap limit and stow persistence.",
            "reloadReset": "Unresolved: neither consumed exact-base section states whether reload resets accumulated hits or its timer.",
            "bodyOrMissReset": "Unresolved: neither consumed exact-base section explicitly states whether a body hit or miss resets accumulated hits. Nonprecision hits do not satisfy the precision requirement.",
            "unresolved": ["Reload reset semantics", "Body-hit/miss reset semantics",
                           "Exact equality at the interval boundary and event ordering",
                           "In-flight projectile attribution, multihit grouping and ownership/copy identity",
                           "Independent live confirmation of the captured community measurements"],
            "excludedEvidence": "research3.json is not consumed. Adjacent Focused Fury reload/stow reset statements and Jade Rabbit/Cranial Spike body-shot discussions cannot establish Triple Tap or Fourth Time's the Charm behavior. Enhanced and catalyst search sections do not supply base eligibility.",
        },
        "projectIntegrationPolicy": {
            "verifiedDestinyInternals": False,
            "timing": "Expire accumulated progress when now minus the last qualifying precision-hit tick is at least 40, before crediting the new hit. A qualifying hit restarts the interval; the entire hit group may span more than 40 ticks.",
            "nonprecision": "A body hit or miss neither advances the hit count nor updates the precision-hit clock. No additional body/miss reset is introduced without evidence.",
            "reload": "Do not add an explicit reload reset or reload notifier without evidence. Elapsed-time expiration still applies during reloading.",
            "stow": "Keep accumulated progress while stowed; stowing grants no additional time.",
            "ammunition": "Generate the appropriate returned rounds into the actual magazine without deducting reserves; limit the result to the weapon's base magazine capacity.",
            "hud": "Existing HUD reflects the actual returned magazine ammunition. No separate precision-perk countdown row is introduced.",
            "boundary": "These are the main implementation's supplied integration rules. Equality, body/miss handling, reload handling and HUD decisions are project policy, not proof of Destiny internals. This sidecar implements no runtime API or behavior.",
        },
        "limitations": ["No live Destiny test, tick-level certification or later-patch audit.",
                        "A pool entry grants optional eligibility; it does not activate the perk on every copy.",
                        "Aisha's Embrace has both base perks in different sockets; each perk retains its own eligibility row.",
                        "Only the exact pinned selected weapon hashes qualify; no same-name reissue inference.",
                        "No enhanced or exotic catalyst support is inferred from shared mechanics text."],
    }
    notes = """# W67 precision-return source and data sidecar

Independent enumeration of all 63 selected official weapon definitions yields **9 real randomized exact-base rows across 8 weapons**: five Triple Tap rows and four Fourth Time's the Charm rows. The runtime resource has exactly `stage` and `perks`; each perk has `id`, `hash`, `hits`, `returnRounds`, `windowTicks` and `weapons`. Every weapon row has exactly `id`, `hash`, `socket`, `perkHash` and `plugSetHash`.

## Exact eligible rows

All sockets below are zero based. Triple Tap is base hash **3400784728**; Fourth Time's the Charm is base hash **1354429876**.

| Perk | Selected ID | Weapon hash | Socket | Randomized plug set |
|---|---|---:|---:|---:|
| Triple Tap | aishas_embrace | 2638190703 | 3 | 7997267 |
| Triple Tap | ammit_ar2 | 2119346509 | 3 | 1723759242 |
| Triple Tap | austringer | 3055790362 | 3 | 2750499928 |
| Triple Tap | distant_relation | 2034817450 | 3 | 1131958073 |
| Triple Tap | duke_mk_44 | 2112909414 | 2 | 3744182842 |
| Fourth Time's the Charm | aishas_embrace | 2638190703 | 4 | 4211351701 |
| Fourth Time's the Charm | beloved | 3107853529 | 3 | 1196545279 |
| Fourth Time's the Charm | retrofit_escapade | 3103325054 | 3 | 3756086698 |
| Fourth Time's the Charm | seventh_seraph_officer_revolver | 3037520408 | 3 | 903350103 |

## Enumeration and exclusions

`references/socket-pools.json` preserves each eligible socket entry, trait category 4241085061, exact randomized plug-set hash, `isFakePlugSet=false`, original matching-entry index and full `currentlyCanRoll=true` record. Every selected item's sockets and referenced randomized/reusable set counts are audited, including negatives. Zero weights are preserved and do not negate rollability. The literal expected-tuple regression set was added after the independent scan; it never chooses eligible weapons or filters enumeration. Rows and audits are deterministically sorted.

Three direct defaults overlap their own exact randomized rows: Distant Relation and Aisha's Embrace for Triple Tap, and Retrofit Escapade for Fourth Time's the Charm. They add zero rows. Enhanced Triple Tap 573122728 occurs in Austringer and Ammit AR2; enhanced Fourth Time's the Charm 848860060 occurs in Beloved and Retrofit Escapade. All four enhanced entries are preserved as exclusion proof. There are no additional base occurrences outside the eligible randomized pools. None of the 63 selected definitions is exotic. All exotic catalysts remain excluded; catalyst-page text does not grant an unselected or exotic weapon a base randomized roll. This is selected-weapon proof, not a global census of catalysts.

## Source boundary and mechanics

Official pinned Bungie inventory and plug sets prove exact definitions, descriptions and eligible rolls. The descriptions establish rapid precision impacts and the returned round amounts. They do not establish the three/four-hit thresholds, numeric timing, reserve behavior, base-cap limit, stow behavior or reset rules.

Each exact-base light.gg Community Research section supplies its threshold and **2 seconds between successive precision hits**, rather than a two-second limit for the entire sequence. At 20 project ticks per second this is 40 ticks. Triple Tap generates one round after three hits; Fourth Time's the Charm generates two after four. The community measurements describe reserve-independent generation, a limit at the base magazine capacity and progress retained through stowing. Both sections report a July 30, 2024 research update. These are captured secondary measurements, not primary Bungie mechanics documentation or fresh gameplay tests. Enhanced timing and catalyst-granted variants are excluded.

The two consumed sections do not explicitly settle whether reloading, body hits or misses reset accumulated progress. Those points remain unresolved. The optional third capture is not consumed: neighboring Focused Fury reset text and Jade Rabbit/Cranial Spike body-shot discussion establish no reset rule for these two perks.

Sources: [Triple Tap exact base](https://www.light.gg/db/items/3400784728/triple-tap/?_=879), [Fourth Time's the Charm exact base](https://www.light.gg/db/items/1354429876/fourth-times-the-charm/?_=935). Official component URLs and SHA256 lineage are recorded in `references/provenance.json`. Full captures stay private in `/tmp/destiny-weapons-w67/research1.json` and `research2.json`; public evidence is paraphrased, without full article/search dumps or extended quotations.

## Main runtime's supplied policy

Expire progress at **at least 40 ticks since the last precision hit**, before counting a new hit. Each qualifying hit restarts that interval. Body hits and misses do not advance progress or update its clock, and no extra reset on reload is added without proof. No reload notifier is introduced. Stowing preserves progress but does not pause time. Returned rounds update the actual magazine without consuming reserves and are capped at base capacity. The existing HUD shows that real magazine; there is no invented precision-perk countdown row. Exact tick equality, reset handling and HUD choices are project integration policy, not independently proven Destiny internals. This sidecar neither implements nor verifies concurrent runtime changes.

## Offline reproduction

```sh
rtk proxy python3 scripts/extract_precision_return_w67.py
rtk proxy python3 scripts/extract_precision_return_w67.py --verify
```

`--root` selects the input checkout and defaults to the script's repository. `--output-root` selects a separate destination tree while keeping inputs at `--root`; it does not change output bytes. `--inventory`, `--shared-sources-dir` and `--sources-dir` override source-cache locations. Defaults are `/tmp/destiny-weapons-w30/bungie-items.json`, `/tmp/destiny-weapons-w60/{manifest,bungie-plugsets}.json` and `/tmp/destiny-weapons-w67/research{1,2}.json`. W40 selection and provenance come from the input checkout. Source locations are recorded; changing an input location changes provenance metadata, but never changes its required content hash.

All seven consumed source files have hardcoded SHA256 pins. The generator hashes itself in provenance and records the other four generated output hashes. Missing or changed sources fail before any output write. `--verify` compares all five generated outputs byte for byte, including this Markdown file, collects mismatches and performs no writes, directory creation, fetch, cache repair or network access. Missing outputs fail without repair. No Gradle, native app, git mutation or runtime edit is part of this work.
"""
    outputs = {TARGET: resource, REF + "socket-pools.json": pools, REF + "mechanics.json": mechanics, NOTES: notes}
    provenance = {
        "stage": "W67", "manifestVersion": VERSION,
        "inventoryUrl": BUNGIE + inventory_path, "plugSetsUrl": BUNGIE + plugsets_path,
        "sourceHashes": pins, "generator": SCRIPT,
        "generatorSha256": digest(Path(__file__).resolve().read_bytes()),
        "runtimeSha256": digest(encoded(resource)),
        "outputHashes": {name: digest(encoded(value)) for name, value in outputs.items()},
        "retrievedAtDate": "2026-10-24",
        "sourceBoundary": "Official manifest proves descriptions and selected rolls. Exact-base light.gg community measurements supply thresholds, the inter-hit interval, generated rounds, base-cap limit and stow persistence. Reload/body/miss resets remain unresolved; runtime boundary and HUD choices are supplied project policy.",
        "privateSources": "Inventory, plug sets, manifest and both raw search captures remain outside the repository. No third research file is consumed. Public findings are bounded paraphrases, never full captures or credentials.",
        "reproduce": "rtk proxy python3 scripts/extract_precision_return_w67.py --verify",
        "verification": "Every consumed input has an explicit SHA256 pin; all five generated outputs are compared byte for byte. No write, network, fetch or cache repair in verify mode. Generator SHA and four non-provenance output hashes are recorded; provenance deliberately does not hash itself.",
    }
    outputs[REF + "provenance.json"] = provenance
    require(len(outputs) == 5, "Expected exactly five generated outputs")
    return outputs, paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Read-only byte-exact check of all five outputs")
    parser.add_argument("--root", type=Path, default=ROOT, help="Input checkout containing W40 selection/provenance")
    parser.add_argument("--output-root", type=Path, help="Separate output tree; inputs remain at --root")
    parser.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    parser.add_argument("--shared-sources-dir", type=Path, default=Path("/tmp/destiny-weapons-w60"))
    parser.add_argument("--sources-dir", type=Path, default=Path("/tmp/destiny-weapons-w67"))
    args = parser.parse_args()
    try:
        outputs, inputs = extract(args)
        output_root = (args.output_root or args.root).resolve()
        input_paths = {p.resolve() for p in inputs.values()} | {Path(__file__).resolve(), (args.root / SCRIPT).resolve()}
        resolved = [(output_root / name).resolve() for name in outputs]
        require(len(set(resolved)) == len(outputs), "Output paths alias each other")
        for name, path in zip(outputs, resolved):
            require(path.is_relative_to(output_root) and path not in input_paths,
                    "Output escapes output root or aliases an input: " + name)
        if args.verify:
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
        print(("VERIFIED" if args.verify else "GENERATED") +
              ": W67; 63 selected; 9 exact-base randomized rows / 8 weapons; Triple Tap 5; Fourth Time's the Charm 4.")
        print("3 direct overlaps add 0 rows; 4 enhanced entries excluded; 0 selected exotics. Both bases: 40-tick inter-hit window; reload/body/miss reset evidence unresolved.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("W67 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
