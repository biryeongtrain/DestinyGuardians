#!/usr/bin/env python3
"""Pinned, offline W73 source/data extraction. --verify never writes or fetches.

Enumerate all 63 exact selected definitions before checking literal regressions.
Writes only W73 notes, reference JSONs, and the W73 runtime resource.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/extract_archers_tempo_w73.py"
REF = "art/weapons/w73/references/"
NOTES = "art/weapons/w73/reference-notes.md"
TARGET = "src/main/resources/destiny/weapons/w73-archers-tempo.json"
BASE, ENHANCED = 201365942, 3523746922
TRAIT_CATEGORY = 4241085061
DRAW_STAT = "447667954"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
BUNGIE = "https://www.bungie.net"
PATCH_URL = BUNGIE + "/7/en/News/article/51380"
COMMUNITY_URL = "https://www.light.gg/db/items/201365942/archers-tempo/"
CAPTURED_COMMUNITY_URL = COMMUNITY_URL + "?_=727"
TIMING_SOURCE = "Bungie Update 4.1.0 standard 0.75; light.gg exact-base Community Research 2024-07-16 (3s, stow removal); W46 raw drawMillis scaled before 20-TPS ceil"
PINS = {
    "selected": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "w40Provenance": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "research": "834d52e16659dcc997d24052b3c907663972c158aa887ab848eecd03911919cd",
    "w46Extraction": "be0a670f4db11adca87383344f13d1e3588f18f58bf22b1454b4652653c87cc8",
    "w46Runtime": "e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07",
}
# Recorded after the independent full 63-weapon / 678-socket / 627-set scan.
# These constants are only post-enumeration assertions, never scan filters.
EXPECTED_ROLLS = {("whispering_slab", 211938782, 3, BASE, 1885424927)}
EXPECTED_TIMINGS = {("biting_winds", 667, 14, 11), ("whispering_slab", 567, 12, 9)}


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


def capture_block(text, url):
    blocks = [b for b in text.split("--------------------------------------------------------------------------------")
              if "(" + url + ")" in b]
    require(len(blocks) == 1, "Missing or ambiguous exact research URL: " + url)
    return blocks[0]


def verify_research(capture):
    require(capture.get("isError") is False, "Research capture failed")
    text = "\n".join(c.get("text", "") for c in capture["content"])
    official = capture_block(text, PATCH_URL)
    require("Destiny 2 Update 4.1.0" in official, "Wrong official patch")
    require("L309:   * Leviathan's Breath:" in official
            and "L310:     * The Archer's Tempo perk from the catalyst" in official,
            "Official scalar must retain its exotic-catalyst context")
    scalar_line = next((line for line in official.splitlines() if line.startswith("L311:")), "")
    require("standard draw time scalar for Archer's Tempo is 0.75x" in scalar_line
            and "0.5625x on Leviathan's Breath" in scalar_line,
            "Standard and catalyst-specific scalars must be distinguished")
    community = capture_block(text, CAPTURED_COMMUNITY_URL)
    require("Basic / Trait" in community and "API ID: " + str(BASE) in community,
            "Community block is not the exact base trait")
    require(community.count("\n#### Community Research\n") == 1
            and "\n#### Details\n" in community, "Unbounded community section")
    section = community.split("\n#### Community Research\n", 1)[1].split("\n#### Details\n", 1)[0]
    require("Precision Hits decrease Draw Time by 25% for 3 seconds." in section
            and "Buff is removed on stow." in section
            and "Last Updated 2024-07-16" in section,
            "Exact base community mechanics/date changed")


def extract(args):
    root, cache = args.root.resolve(), args.sources_dir.resolve()
    paths = {
        "selected": root / "art/weapons/w40/definitions.json",
        "w40Provenance": root / "art/weapons/w40/provenance.json",
        "inventory": cache / "bungie-items.json",
        "plugSets": cache / "bungie-plugsets.json",
        "manifest": cache / "manifest.json",
        "research": cache / "research1.json",
        "w46Extraction": root / "art/weapons/w46/extraction.json",
        "w46Runtime": root / "src/main/resources/destiny/weapons/w46-timing.json",
    }
    require(paths.keys() == PINS.keys(), "Every consumed source requires a literal pin")
    sources, pins = {}, {}
    # All inputs fail closed BEFORE output writes. No network/fetch/cache repair.
    for key, path in paths.items():
        raw = path.read_bytes()
        require(digest(raw) == PINS[key], "Source SHA256 mismatch: " + key)
        sources[key] = json.loads(raw)
        path = path.resolve()
        pins[key] = {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                     "sha256": PINS[key], "bytes": len(raw)}
    manifest_response = sources["manifest"]
    require(manifest_response["ErrorCode"] == 1, "Manifest API response failed")
    manifest = manifest_response["Response"]
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
            and w40["source"] == BUNGIE + inventory_path, "W40 lineage mismatch")
    selected, inventory, plugsets = sources["selected"], sources["inventory"], sources["plugSets"]
    require(len(selected) == len({w["id"] for w in selected})
            == len({w["bungieHash"] for w in selected}) == 63, "Expected 63 exact selected definitions")
    definitions = []
    for h, kind, description in (
            (BASE, "Trait", "Draw time decreases after every precision hit."),
            (ENHANCED, "Enhanced Trait", "Draw time substantially decreases after every precision hit for a longer duration.")):
        perk = inventory[str(h)]
        require(perk["hash"] == h and perk["displayProperties"]["name"] == "Archer's Tempo"
                and perk["displayProperties"]["description"] == description
                and perk["itemTypeDisplayName"] == kind and perk["itemType"] == 19
                and not perk["redacted"] and not perk["blacklisted"]
                and not perk["plug"]["isDummyPlug"], "Invalid exact perk: " + str(h))
        definitions.append({"hash": h, "name": perk["displayProperties"]["name"],
                            "description": description, "itemTypeDisplayName": kind,
                            "disposition": "exact base" if h == BASE else "excluded enhanced"})
    verify_research(sources["research"])

    rolls, proofs, direct, enhanced, other_base, exotics, audit = [], [], [], [], [], [], []
    socket_total = set_total = 0
    # Independent traversal: all selected exact hashes, all socket categories,
    # initial/reusable direct items, BOTH randomized/reusable plug-set fields.
    # No name, family, EXPECTED_*, or assumed bow restricts this enumeration.
    for weapon in sorted(selected, key=lambda w: (w["id"], w["bungieHash"])):
        item = inventory[str(weapon["bungieHash"])]
        require(item["hash"] == weapon["bungieHash"] and item["itemType"] == 3
                and not item["redacted"] and not item["blacklisted"]
                and (item["inventory"]["tierType"] == 6) == weapon["exotic"],
                "Invalid exact weapon: " + weapon["id"])
        sockets = item.get("sockets", {})
        entries = sockets.get("socketEntries", [])
        trait_indexes = {i for c in sockets.get("socketCategories", [])
                         if c["socketCategoryHash"] == TRAIT_CATEGORY for i in c["socketIndexes"]}
        require(all(0 <= i < len(entries) for i in trait_indexes), "Invalid trait indexes")
        before = len(rolls)
        socket_audit = []
        for index, socket in enumerate(entries):
            socket_total += 1
            identity = {"id": weapon["id"], "hash": item["hash"], "socket": index}
            direct_hashes = {socket["singleInitialItemHash"],
                             *[p["plugItemHash"] for p in socket.get("reusablePlugItems", [])]}
            for h in (BASE, ENHANCED):
                if h in direct_hashes:
                    option = {**identity, "perkHash": h, "source": "direct",
                              "initialPerk": socket["singleInitialItemHash"] == h,
                              "reusablePlugItems": [p for p in socket.get("reusablePlugItems", []) if p["plugItemHash"] == h],
                              "traitCategory": index in trait_indexes}
                    (enhanced if h == ENHANCED else exotics if weapon["exotic"] else direct).append(option)
            reviewed_sets = []
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                set_hash = socket.get(field)
                if not set_hash:
                    continue
                set_total += 1
                pool = plugsets[str(set_hash)]
                require(pool["hash"] == set_hash and not pool["redacted"] and not pool["blacklisted"],
                        "Invalid referenced plug set: " + str(set_hash))
                pool_items = pool.get("reusablePlugItems", [])
                reviewed_sets.append({"field": field, "hash": set_hash,
                                      "isFakePlugSet": pool["isFakePlugSet"], "entryCount": len(pool_items)})
                for h in (BASE, ENHANCED):
                    matches = [{"index": n, "item": p} for n, p in enumerate(pool_items) if p["plugItemHash"] == h]
                    if not matches:
                        continue
                    option = {**identity, "perkHash": h, "plugSetHash": set_hash, "plugSetField": field,
                              "isFakePlugSet": pool["isFakePlugSet"], "traitCategory": index in trait_indexes,
                              "matchingEntries": matches}
                    if h == ENHANCED:
                        enhanced.append(option)
                        continue
                    if weapon["exotic"]:
                        exotics.append(option)
                        continue
                    rollable = [m for m in matches if m["item"].get("currentlyCanRoll") is True]
                    if (field != "randomizedPlugSetHash" or index not in trait_indexes
                            or pool["isFakePlugSet"] is not False or not rollable):
                        other_base.append(option)
                        continue
                    require(len(matches) == len(rollable) == 1, "Duplicate/unrollable base entries need audit")
                    row = {**identity, "perkHash": h, "plugSetHash": set_hash}
                    rolls.append(row)
                    proofs.append({**row, "weaponType": item["itemTypeDisplayName"],
                                   "socketCategoryHash": TRAIT_CATEGORY, "socketEntry": socket,
                                   "plugSetField": field, "isFakePlugSet": False,
                                   "matchingEntries": matches})
            socket_audit.append({"socket": index, "traitCategory": index in trait_indexes,
                                 "singleInitialItemHash": socket["singleInitialItemHash"],
                                 "directReusableCount": len(socket.get("reusablePlugItems", [])),
                                 "reviewedPlugSets": reviewed_sets})
        audit.append({"id": weapon["id"], "hash": item["hash"], "exotic": weapon["exotic"],
                      "weaponType": item["itemTypeDisplayName"], "socketCount": len(entries),
                      "traitSocketIndexes": sorted(trait_indexes),
                      "officialBaseRandomizedRows": len(rolls) - before, "sockets": socket_audit})

    # All regressions follow the complete independent scan above.
    require((len(audit), socket_total, set_total) == (63, 678, 627), "Full scan coverage changed")
    require({row_key(r) for r in rolls} == EXPECTED_ROLLS and len(rolls) == 1,
            "Independent scan differs from recorded eligible tuples")
    require(not direct and not enhanced and not other_base and not exotics,
            "New direct/enhanced/noneligible/exotic occurrence requires explicit audit")
    require(not any(w["exotic"] for w in selected), "Selected exotic/catalyst coverage changed")
    rolls.sort(key=row_key)
    proofs.sort(key=row_key)

    extraction, base_runtime = sources["w46Extraction"], sources["w46Runtime"]
    raw_entries = extraction["entries"]
    raw_by_id = {e["id"]: (i, e) for i, e in enumerate(raw_entries)}
    base_by_id = {e["id"]: e["timing"] for e in base_runtime}
    ids = {w["id"] for w in selected}
    require(len(raw_entries) == len(raw_by_id) == len(base_runtime) == len(base_by_id) == 63
            and ids == raw_by_id.keys() == base_by_id.keys(), "W46 exact selected coverage mismatch")
    require(extraction["runtimeSha256"] == PINS["w46Runtime"]
            and extraction["sourceHashes"]["art/weapons/w40/definitions.json"] == PINS["selected"]
            and extraction["sourceHashes"]["art/weapons/w40/provenance.json"] == PINS["w40Provenance"]
            and extraction["officialManifest"] == w40 and extraction["profileCount"] == 63,
            "W46 raw/runtime/official lineage mismatch")
    timings, timing_audit = [], []
    for weapon in sorted(selected, key=lambda w: w["id"]):
        wid = weapon["id"]
        index, entry = raw_by_id[wid]
        require(entry["bungieHash"] == weapon["bungieHash"], "W46 exact hash mismatch: " + wid)
        official = inventory[str(weapon["bungieHash"])]; profile = base_by_id[wid]
        is_bow = entry["family"] == "bow"
        require(is_bow == (official["itemTypeDisplayName"] == "Combat Bow"), "W46/official bow family mismatch")
        record = {"id": wid, "hash": weapon["bungieHash"], "rawEntryIndex": index,
                  "family": entry["family"], "isBow": is_bow,
                  "runtimeSelectable": any(r["id"] == wid for r in rolls)}
        if is_bow:
            ms = entry["officialStats"]["drawMillis"]
            require(type(ms) is int and ms > 0 and profile["supported"] is True
                    and profile["drawMillis"] == ms
                    and weapon["stats"][DRAW_STAT] == ms
                    and official["stats"]["stats"][DRAW_STAT]["value"] == ms,
                    "W46 raw/selected/official draw-stat binding changed: " + wid)
            # Exact rational integer arithmetic: scale RAW milliseconds first.
            # ceil(ms / 50) and ceil(ms * 3/4 / 50); no rounded-tick scaling.
            base_ticks = (ms + 49) // 50
            accelerated = (ms * 3 + 199) // 200
            require(profile["drawTicks"] == base_ticks, "W46 base tick mismatch: " + wid)
            timings.append({"id": wid, "baseDrawMs": ms, "baseDrawTicks": base_ticks,
                            "acceleratedTicks": accelerated})
            record.update(baseDrawMs=ms, baseDrawTicks=base_ticks, acceleratedTicks=accelerated,
                          scaledDrawMs=ms * 0.75, drawStatHash=int(DRAW_STAT),
                          rawDrawMillisPointer="/entries/" + str(index) + "/officialStats/drawMillis",
                          reason="Candidate timing only; membership in weapons independently gates the perk.")
        else:
            require(profile["drawMillis"] is None and profile["drawTicks"] is None,
                    "Non-bow unexpectedly carries W46 draw timing")
            record.update(reason="Non-bow: no Archer's Tempo draw timing inferred.")
        timing_audit.append(record)
    require({tuple(t[k] for k in ("id", "baseDrawMs", "baseDrawTicks", "acceleratedTicks"))
             for t in timings} == EXPECTED_TIMINGS and len(timings) == 2, "Bow timing regression changed")
    require(all(r["id"] in {t["id"] for t in timings} for r in rolls), "Eligible roll lacks bow timing")
    resource = {"stage": "W73", "perk": {"id": "archers_tempo", "hash": BASE,
                "durationTicks": 60, "drawScalar": 0.75, "timingSource": TIMING_SOURCE},
                "weapons": rolls, "timings": timings}
    pools = {
        "stage": "W73", "selectedCount": 63, "socketCount": socket_total,
        "plugSetReferencesReviewed": set_total, "runtimeRollCount": len(rolls),
        "perkDefinitions": definitions,
        "policy": "Scan all exact selected hashes and all sockets, direct initial/reusable items and both plug-set fields. Require exact base hash, trait category, nonfake randomized set and currentlyCanRoll=true. Preserve zero weights; never infer availability from weights or names. Exclude enhanced traits and exotics/catalysts.",
        "weapons": proofs, "runtimeRolls": rolls, "directSocketOptions": direct,
        "enhancedSelectedOptionsExcluded": enhanced,
        "otherBasePoolOccurrencesNotSelected": other_base, "exoticBaseOccurrencesExcluded": exotics,
        "exoticCatalystExclusion": {"selectedExoticCount": 0, "selectedExoticIds": [],
             "scope": "Selected 63 only; no global catalyst census. Leviathan's Breath and its separate 0.5625 scalar are excluded."},
        "selectionAudit": audit,
        "noOfficialBaseRandomizedRollIds": sorted(ids - {r["id"] for r in rolls}),
    }
    timing_evidence = {
        "stage": "W73", "selectedCount": 63, "bowTimingCount": 2, "nonBowCount": 61,
        "rawSource": "art/weapons/w46/extraction.json", "rawSourceSha256": PINS["w46Extraction"],
        "baseSource": "src/main/resources/destiny/weapons/w46-timing.json", "baseSourceSha256": PINS["w46Runtime"],
        "policy": "Use raw W46 officialStats.drawMillis after exact official-stat/hash binding. baseDrawTicks=ceil(ms/50); acceleratedTicks=ceil(ms*0.75/50). Compute with integer rational arithmetic. Never multiply rounded base ticks. Candidate timing is not roll eligibility.",
        "entries": timing_audit,
    }
    mechanics = {
        "stage": "W73", "baseHash": BASE, "enhancedHashExcluded": ENHANCED,
        "officialIdentity": definitions,
        "localizedName": {"name": "Archer's Tempo", "locale": "en",
             "reason": "No pinned official Korean inventory component was available in the inspected local source caches; no community translation is promoted to an official localized name."},
        "officialPrimary": {"url": PATCH_URL, "publisher": "Bungie", "primary": True,
             "title": "Destiny 2 Update 4.1.0", "standardDrawScalar": 0.75,
             "context": "The Leviathan's Breath catalyst discussion distinguishes the standard perk from the exotic-only 0.5625 scalar. Only the standard scalar is used.",
             "privateCapture": "research1.json", "captureLines": [309, 310, 311],
             "scope": "Historical official scalar statement; not a current live gameplay measurement."},
        "communitySecondary": {"url": COMMUNITY_URL, "capturedUrl": CAPTURED_COMMUNITY_URL,
             "publisher": "light.gg", "primary": False, "section": "Community Research",
             "lastUpdatedReported": "2024-07-16", "trigger": "precision hit",
             "drawTimeReductionPercent": 25, "durationSeconds": 3, "removedOnStow": True,
             "privateCapture": "research1.json",
             "retrieval": "Search tool returned a bounded exact-base English section with API ID 201365942. Direct opens returned 402/unavailable; this is search-captured community research, not fresh measurement."},
        "serverPolicy": {"durationTicks": 60, "drawScalar": 0.75, "ticksPerSecond": 20,
             "duration": "Quantize the community 3 seconds to 60 server ticks.",
             "draw": "ceil(raw W46 drawMillis * 0.75 / 50); only a selected eligible exact base roll may activate the candidate timing.",
             "trigger": "Successful precision-hit event; no kill requirement is supplied by the sources.",
             "refresh": "Use one nonstacking 60-tick window refreshed on qualifying hits; deadline representation and event ordering are project policy, not source-verified details.",
             "stow": "Clear on stow per community research; runtime integration belongs to the main worker."},
        "unknowns": {"midDrawRescaling": "Neither captured source establishes whether an in-progress draw is rescaled when the buff starts or expires. Any snapshot-at-draw-start or dynamic rescaling decision must be labeled project policy.",
             "refreshAndStacking": "The captured text does not precisely document stacking, hit-refresh ordering, death/disconnect cleanup, or server-tick expiry ordering."},
        "sourceBoundary": "Official manifest identity/socket pools establish exact selected roll eligibility and the precision-hit description. Bungie 4.1.0 establishes standard 0.75 separately from Leviathan's catalyst. The bounded exact-base light.gg section supplies 3s and stow removal. W46 supplies raw official draw milliseconds. 20-TPS quantization and runtime ordering are project choices.",
        "limitations": ["No native application, Gradle, production Java or tests were run or changed by this source/data worker.",
             "No claim of current Destiny measurement or official confirmation of the community duration/stow behavior.",
             "An optional eligible roll does not activate the perk on every weapon copy.",
             "No enhanced mechanics or Leviathan catalyst scalar is supported.",
             "The privately fetched official HTML is only a JavaScript shell; mechanics use the pinned web-tool capture of the official article instead."],
    }
    outputs = {TARGET: resource, REF + "socket-pools.json": pools,
               REF + "timings.json": timing_evidence, REF + "mechanics.json": mechanics,
               NOTES: make_notes(rolls, timings)}
    outputs[REF + "provenance.json"] = {
        "stage": "W73", "manifestVersion": VERSION,
        "inventoryUrl": BUNGIE + inventory_path, "plugSetsUrl": BUNGIE + plugsets_path,
        "sourceHashes": pins, "generator": SCRIPT,
        "generatorSha256": digest(Path(__file__).resolve().read_bytes()),
        "runtimeSha256": digest(encoded(resource)),
        "outputHashes": {name: digest(encoded(value)) for name, value in outputs.items()},
        "capturedAtDate": "2026-10-24",
        "privateSources": "run/private-sources/w73 retains byte-identical pinned official inventory/plug sets/manifest and raw web-tool research. research2.json, official-identity.json and the HTML/retrieval pair preserve ancillary retrieval attempts and are not consumed inputs.",
        "sourceBoundary": mechanics["sourceBoundary"],
        "reproduce": "rtk proxy python3 scripts/extract_archers_tempo_w73.py --verify",
        "verification": "Eight literal input SHA256 pins. Compare all six outputs byte for byte including Markdown. Verify performs no writes, directory creation, fetch, cache repair or networking. Missing/changed inputs fail before writes. Generator and five non-provenance output hashes are recorded; no self-hash cycle.",
    }
    require(len(outputs) == 6, "Expected six generated W73 outputs")
    return outputs, paths


def make_notes(rolls, timings):
    rows = "\n".join(f'| {r["id"]} | {r["hash"]} | {r["socket"]} | {r["perkHash"]} | {r["plugSetHash"]} |' for r in rolls)
    tick_rows = "\n".join(f'| {t["id"]} | {t["baseDrawMs"]} | {t["baseDrawTicks"]} | {t["acceleratedTicks"]} | {"yes" if any(r["id"] == t["id"] for r in rolls) else "no"} |' for t in timings)
    return f'''# W73 Archer's Tempo source and data

Independent enumeration of all **63** exact W40 selected weapon hashes, **678 sockets**, and **627 plug-set references** yields **one** eligible base roll: Whispering Slab. Biting Winds has no exact base roll. No base direct occurrence or enhanced occurrence exists within the selected 63; no selected weapons are exotic. The full traversal precedes literal regression checks.

## Runtime contract

`src/main/resources/destiny/weapons/w73-archers-tempo.json` contains `stage: "W73"`, `perk`, `weapons`, and `timings`. `perk` has `id: "archers_tempo"`, `hash: 201365942`, `durationTicks: 60`, `drawScalar: 0.75`, and a `timingSource` string identifying the distinct official, community, and W46 inputs. Each `weapons` row is exactly `{{id,hash,socket,perkHash,plugSetHash}}`. Each `timings` row is exactly `{{id,baseDrawMs,baseDrawTicks,acceleratedTicks}}`.

**Candidate timing != eligible roll.** Only `weapons` controls eligibility. The two timing rows are candidates for both selected bows; they do not grant Biting Winds the perk. The supplied main-worker integration contract requires `ArcherTempoProfile.accelerated` to reject IDs absent from `rolls()`, explicitly including `biting_winds`. This sidecar does not independently audit that Java implementation. A proven optional roll must still be selected on the weapon copy before the runtime grants its effect.

## Exact eligible roll

Socket indexes are zero based.

| ID | Weapon hash | Socket | Base perk hash | Randomized plug set |
|---|---:|---:|---:|---:|
{rows}

The match is entry index **3** of its own official randomized trait set. `currentlyCanRoll=true`, `isFakePlugSet=false`, socket category **4241085061**. Both `weight` and `alternateWeight` are **0.0**; these values do not override the explicit rollability flag. Full socket and matching-entry records are retained in `references/socket-pools.json`.

The generator scans every socket of all 63 selected exact definitions, including initial/direct reusable plugs and both `randomizedPlugSetHash` and `reusablePlugSetHash`. It retains a per-weapon/per-socket audit and all 62 negative IDs. It does not filter by presumed bow name or family during discovery. Exact base **201365942** is required. Enhanced **3523746922** is a separately checked official Enhanced Trait and is excluded. Leviathan's Breath/catalysts are excluded; this is selected-inventory coverage, not a global catalyst census.

## Milliseconds before tick rounding

| ID | W46 raw draw ms | Base ticks | Accelerated ticks | Eligible roll |
|---|---:|---:|---:|---|
{tick_rows}

Use **`ceil(rawDrawMs * 0.75 / 50)`**, after binding W46 `entries[n].officialStats.drawMillis` to the exact selected and official inventory draw stat **447667954**. Preserve W46 `drawTicks=ceil(rawDrawMs/50)`. Integer rational arithmetic uses `(ms*3+199)//200` for accelerated ticks. Whispering Slab: 567 ms × 0.75 = 425.25 ms → 9 ticks. Biting Winds: 667 ms × 0.75 = 500.25 ms → 11 ticks. Never scale rounded base ticks. The references audit all 63 W46 rows: two bows and 61 explicit non-bow exclusions with no fabricated draw timing.

## Mechanics and evidence boundaries

[Bungie Update 4.1.0]({PATCH_URL}) supplies the **standard 0.75 draw scalar** in a discussion that separately identifies Leviathan's Breath's catalyst-specific **0.5625** scalar. This historical official statement supports the standard scalar only; it does not prove today's exact implementation or the 3-second duration. The generator verifies the official capture's identity and the distinct standard/exotic values.

The exact-base [light.gg Community Research]({COMMUNITY_URL}) reports **25% less draw time for 3 seconds after precision hits**, with removal on stow, and a reported update date of **2024-07-16**. This is community evidence. Direct browser-tool opens failed with 402/unavailable. The pinned raw search response returned the complete bounded English Community Research section at the same base-perk URL with `?_=727`, `Basic / Trait`, and API ID **201365942**. No enhanced, translated, mirror, or catalyst section establishes the selected base mechanics.

At the project's **20 TPS**, 3 seconds becomes **60 ticks**. One nonstacking window refreshed by a qualifying hit is a project runtime policy; the captured sources do not precisely document refresh/event ordering. Neither source establishes **mid-draw rescaling on buff activation or expiry**. A snapshot-at-draw-start or dynamic-rescaling choice must remain labeled project policy. Death/disconnect cleanup and exact expiry ordering are also runtime policy. This sidecar changes no runtime Java/HUD/tests.

`references/mechanics.json` separates official scalar, community duration/stow evidence, project quantization/policy, and unknown behavior. The pinned official English name is **Archer's Tempo**. No pinned official Korean inventory component was found in the inspected local source caches; a community Korean translation is not used as an official name.

## Reproduction and provenance

```sh
rtk proxy python3 scripts/extract_archers_tempo_w73.py
rtk proxy python3 scripts/extract_archers_tempo_w73.py --verify
```

All **eight consumed inputs** have literal SHA256 pins: W40 definitions/provenance, official English inventory/plug sets/manifest, raw research capture, W46 extraction, and W46 runtime. The default private raw directory is `run/private-sources/w73`. Official component copies retain the exact historical W40/W60 bytes; no older pins or historical metadata are rewritten. The fetched official HTML is a JavaScript shell and is not used as article-body proof. Ancillary raw retrieval attempts remain private and are listed in provenance as unconsumed evidence.

`--root` selects the input checkout, `--sources-dir` overrides the raw cache directory without relaxing pins, and `--output-root` selects a separate output tree. Generation writes only this Markdown, the four `references/*.json` files, and the runtime JSON. Provenance includes the generator SHA256 and all five other generated output hashes. Changing cache location changes recorded source paths, not the required content hashes.

**`--verify` is offline and read only.** It compares all six generated outputs byte for byte, including Markdown and provenance. It creates no files/directories, fetches nothing, repairs nothing, and fails on missing or changed input/output. Input validation completes before any output write. No native application or Gradle was run for this source/data task, and no fresh gameplay measurement is claimed.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Offline read-only byte-exact comparison of all six outputs")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--sources-dir", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    args.sources_dir = args.sources_dir or args.root / "run/private-sources/w73"
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
              ": W73; 63 selected; 678 sockets; 627 plug-set references; one eligible base roll.")
        print("whispering_slab 211938782 socket 3 set 1885424927: 567ms, 12 -> 9 ticks.")
        print("biting_winds: no eligible roll; timing candidate 667ms, 14 -> 11 ticks.")
        print("Base 201365942; 60 ticks; scalar 0.75; enhanced/catalyst excluded; mid-draw behavior unproven.")
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print("W73 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
