#!/usr/bin/env python3
"""Offline, pinned W68 Snapshot Sights sidecar; --verify never writes or fetches.

Enumerate all 63 exact selected definitions before applying regression oracles.
Official Heavy rolls remain evidence; only measured Primary/Special rolls enter
the runtime resource. Raw ADS seconds come directly from W44 extraction entries.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/extract_snapshot_w68.py"
REF = "art/weapons/w68/references/"
NOTES = "art/weapons/w68/reference-notes.md"
TARGET = "src/main/resources/destiny/weapons/w68-snapshot.json"
BASE = 957782887
ENHANCED = 4116820839
TRAIT_CATEGORY = 4241085061
SCALARS = {1: 0.5, 2: 0.8}  # No measured Heavy scalar; do not add a fallback.
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
BUNGIE = "https://www.bungie.net"
MEASURED_URL = "https://www.light.gg/db/items/957782887/snapshot-sights/?_=150"
HISTORICAL_URLS = (
    "https://www.bungie.net/7/en/News/article/51319",
    "https://www.bungie.net/7/en/News/article/51380",
    "https://www.bungie.net/7/en/News/Article/51250?hidenav=true",
)
PINS = {
    "selected": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "w40Provenance": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "research1.json": "e54640c12c6c1ecd8ccf5d66b18f2517d5d220f1f888310cfcecdcbd036422c1",
    "w44Extraction": "6a82eb21264ffab1e897cf9b0a74ad0cef0c252b129438f2938d82414a7da9fc",
    "w44Runtime": "0d0a38469c28a74c1a77489d346184eccef347a604c0c0c455d1c7c2e1a80fc8",
}
# Literal regressions recorded AFTER an independent full selected/socket scan.
# They never select weapons or drive enumeration. id, hash, socket, perk, set.
EXPECTED_RANDOM = {
    ("apostate", 2164448701, 4, BASE, 2826016044),
    ("austringer", 3055790362, 3, BASE, 2750499928),
    ("bad_omens", 991314988, 3, BASE, 457210958),
    ("beloved", 3107853529, 3, BASE, 1196545279),
    ("bite_of_the_fox", 1403800851, 3, BASE, 563442205),
    ("biting_winds", 1621657423, 4, BASE, 2763203653),
    ("blast_furnace", 3843477312, 3, BASE, 1976101165),
    ("claws_of_the_wolf", 1280933460, 3, BASE, 206409262),
    ("deafening_whisper", 981718087, 4, BASE, 3588287812),
    ("dream_breaker", 2931957300, 3, BASE, 3785896921),
    ("dust_rock_blues", 636912560, 4, BASE, 1624251370),
    ("edge_transit", 218335759, 3, BASE, 447678063),
    ("high_albedo", 1197486957, 4, BASE, 718633408),
    ("mindbender_s_ambition_adept", 912150785, 3, BASE, 1732284294),
    ("parcel_of_stardust_fell_to_earth", 2217366863, 3, BASE, 2514419370),
}
EXPECTED_DIRECT = {
    ("bite_of_the_fox", 1403800851, 3, BASE),
    ("mindbender_s_ambition_adept", 912150785, 3, BASE),
}
EXPECTED_ENHANCED = {
    ("austringer", 3055790362, 3, ENHANCED, 2750499928),
    ("beloved", 3107853529, 3, ENHANCED, 1196545279),
}
EXPECTED_HEAVY = {
    ("bad_omens", 991314988, 3, BASE, 457210958),
    ("edge_transit", 218335759, 3, BASE, 447678063),
}
EXPECTED_NEUTRAL = {
    "abide_the_return", "crown_splitter", "falling_guillotine", "goldtusk",
    "nezarec_s_whisper", "temptation_s_hook",
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


def option_key(row):
    return (row["id"], row["hash"], row["socket"], row["perkHash"],
            row.get("plugSetField", ""), row.get("plugSetHash", 0))


def capture_block(text, url):
    blocks = [b for b in text.split("--------------------------------------------------------------------------------") if "(" + url + ")" in b]
    require(len(blocks) == 1, "Missing or ambiguous exact source URL: " + url)
    return blocks[0]


def verify_research(capture):
    require(capture.get("isError") is False, "Research capture failed")
    text = "\n".join(c.get("text", "") for c in capture["content"])
    block = capture_block(text, MEASURED_URL)
    require("Basic / Trait" in block and "API ID: " + str(BASE) in block,
            "Measured block must identify the exact base trait")
    require(block.count("#### Community Research") == 1 and "#### Details" in block,
            "Missing bounded community section")
    section = block.split("#### Community Research", 1)[1].split("#### Details", 1)[0]
    require("Passively decreases the ADS Animation Duration:" in section
            and "Last Updated 2024-04-12" in section, "Measurement meaning/date changed")
    measured = re.findall(r"(\d+)% decrease on (Primary|Special|Heavy) Weapons", section)
    require(measured == [("50", "Primary"), ("20", "Special")],
            "Expected only Primary/Special duration measurements; no Heavy scalar")
    for url in HISTORICAL_URLS:
        historical = capture_block(text, url)
        require("Snapshot Sights" in historical and "0.5" in historical
                and "0.75" in historical and "Special" in historical,
                "Historical 2022 conflicting statement changed: " + url)
    # Do not publish the captures or use enhanced/mirror/catalyst text as base proof.


def extract(args):
    root = args.root.resolve()
    paths = {
        "selected": root / "art/weapons/w40/definitions.json",
        "w40Provenance": root / "art/weapons/w40/provenance.json",
        "inventory": args.inventory,
        "plugSets": args.shared_sources_dir / "bungie-plugsets.json",
        "manifest": args.shared_sources_dir / "manifest.json",
        "research1.json": args.sources_dir / "research1.json",
        "w44Extraction": root / "art/weapons/w44/extraction.json",
        "w44Runtime": root / "src/main/resources/destiny/weapons/w44-aim.json",
    }
    require(paths.keys() == PINS.keys(), "Every consumed input needs a hardcoded SHA256 pin")
    sources, pins, raw_ads_literals = {}, {}, None
    for key, path in paths.items():
        raw = path.read_bytes()
        require(digest(raw) == PINS[key], "Source SHA256 mismatch: " + key)
        sources[key] = json.loads(raw)
        if key == "w44Extraction":
            raw_ads_literals = json.loads(raw, parse_float=str)["entries"]
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
            "Inventory and plug sets must belong to the exact pinned manifest")
    w40 = sources["w40Provenance"]
    require(w40["manifest"] == {"version": VERSION, "path": inventory_path}
            and w40["cachedInventorySha256"] == PINS["inventory"]
            and w40["source"] == BUNGIE + inventory_path, "W40 source lineage mismatch")
    selected, inventory, plugsets = sources["selected"], sources["inventory"], sources["plugSets"]
    require(len(selected) == len({w["id"] for w in selected})
            == len({w["bungieHash"] for w in selected}) == 63, "Expected 63 unique selected weapons")
    definitions = []
    for h, kind in ((BASE, "Trait"), (ENHANCED, "Enhanced Trait")):
        perk = inventory[str(h)]
        require(perk["hash"] == h and perk["displayProperties"]["name"] == "Snapshot Sights"
                and perk["itemTypeDisplayName"] == kind and perk["itemType"] == 19
                and not perk["redacted"] and not perk["blacklisted"]
                and not perk["plug"]["isDummyPlug"], "Invalid exact perk definition: " + str(h))
        require(perk["displayProperties"]["description"] == (
            "Faster time to aim down sights." if h == BASE else
            "Faster time to aim down sights. Stability is increased."), "Official description changed")
        definitions.append({"hash": h, "name": "Snapshot Sights", "itemTypeDisplayName": kind,
                            "itemType": 19, "disposition": "exact base" if h == BASE else "excluded enhanced"})
    verify_research(sources["research1.json"])

    official_rows, proofs, direct, enhanced, other_base, exotics, audit = [], [], [], [], [], [], []
    ammo_by_id = {}
    # ALL selected items, ALL sockets, direct initial/reusable items and BOTH set
    # fields are examined. No EXPECTED_* oracle participates in this traversal.
    for weapon in sorted(selected, key=lambda w: (w["id"], w["bungieHash"])):
        item = inventory[str(weapon["bungieHash"])]
        require(item["hash"] == weapon["bungieHash"] and item["itemType"] == 3
                and not item["redacted"] and not item["blacklisted"]
                and (item["inventory"]["tierType"] == 6) == weapon["exotic"],
                "Invalid exact selected weapon: " + weapon["id"])
        ammo = item["equippingBlock"]["ammoType"]
        require(type(ammo) is int and ammo in (1, 2, 3)
                and {1: "PRIMARY", 2: "SPECIAL", 3: "HEAVY"}[ammo] == weapon["ammo"],
                "Official ammo type mismatch: " + weapon["id"])
        ammo_by_id[weapon["id"]] = ammo
        sockets = item.get("sockets", {})
        entries = sockets.get("socketEntries", [])
        trait_indexes = {i for c in sockets.get("socketCategories", [])
                         if c["socketCategoryHash"] == TRAIT_CATEGORY for i in c["socketIndexes"]}
        require(all(0 <= i < len(entries) for i in trait_indexes), "Invalid trait indexes")
        socket_audit, before = [], len(official_rows)
        for index, socket in enumerate(entries):
            identity = {"id": weapon["id"], "hash": item["hash"], "socket": index}
            category = TRAIT_CATEGORY if index in trait_indexes else None
            direct_hashes = {socket["singleInitialItemHash"],
                             *[p["plugItemHash"] for p in socket.get("reusablePlugItems", [])]}
            for h in (BASE, ENHANCED):
                if h not in direct_hashes:
                    continue
                option = {**identity, "perkHash": h, "source": "direct",
                          "initialPerk": socket["singleInitialItemHash"] == h,
                          "reusablePlugItems": [p for p in socket.get("reusablePlugItems", []) if p["plugItemHash"] == h],
                          "socketCategoryHash": category}
                (enhanced if h == ENHANCED else exotics if weapon["exotic"] else direct).append(option)
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
                for h in (BASE, ENHANCED):
                    matches = [{"index": n, "item": p} for n, p in enumerate(pool_items) if p["plugItemHash"] == h]
                    if not matches:
                        continue
                    option = {**identity, "perkHash": h, "plugSetHash": set_hash, "plugSetField": field,
                              "isFakePlugSet": pool["isFakePlugSet"], "socketCategoryHash": category,
                              "matchingEntries": matches}
                    if h == ENHANCED:
                        enhanced.append(option)
                        continue
                    if weapon["exotic"]:
                        exotics.append(option)
                        continue
                    eligible = [m for m in matches if m["item"].get("currentlyCanRoll") is True]
                    if (field != "randomizedPlugSetHash" or not eligible or category != TRAIT_CATEGORY
                            or pool["isFakePlugSet"] is not False
                            or item["itemTypeDisplayName"] in ("Sword", "Glaive")):
                        other_base.append(option)
                        continue
                    require(len(matches) == len(eligible) == 1, "Duplicate/unrollable base entries need explicit audit")
                    row = {**identity, "perkHash": h, "plugSetHash": set_hash}
                    official_rows.append(row)
                    proofs.append({**row, "ammoType": ammo, "selection": "randomized",
                                   "socketCategoryHash": TRAIT_CATEGORY, "weaponType": item["itemTypeDisplayName"],
                                   "socketEntry": socket, "plugSetField": field,
                                   "isFakePlugSet": False, "matchingEntries": eligible})
            socket_audit.append({"socket": index, "traitCategory": index in trait_indexes,
                                 "singleInitialItemHash": socket["singleInitialItemHash"],
                                 "directReusableCount": len(socket.get("reusablePlugItems", [])),
                                 "reviewedPlugSets": reviewed_sets})
        audit.append({"id": weapon["id"], "hash": item["hash"], "ammoType": ammo,
                      "weaponType": item["itemTypeDisplayName"], "exotic": weapon["exotic"],
                      "socketCount": len(entries), "traitSocketIndexes": sorted(trait_indexes),
                      "officialRandomizedBaseRows": len(official_rows) - before, "sockets": socket_audit})

    # Literal regressions run only AFTER the complete enumeration above.
    require({row_key(r) for r in official_rows} == EXPECTED_RANDOM and len(official_rows) == 15,
            "Independent enumeration differs from the 15-row official regression")
    require({tuple(r[k] for k in ("id", "hash", "socket", "perkHash")) for r in direct} == EXPECTED_DIRECT
            and len(direct) == 2, "Direct occurrence regression changed")
    row_sockets = {row_key(r)[:4] for r in official_rows}
    for option in direct:
        require(tuple(option[k] for k in ("id", "hash", "socket", "perkHash")) in row_sockets,
                "Direct occurrence lacks its own exact randomized row")
        option.update(alsoProvenRandomized=True, addsRuntimeRow=False)
    require({row_key(e) for e in enhanced} == EXPECTED_ENHANCED and len(enhanced) == 2
            and all(e.get("plugSetField") == "randomizedPlugSetHash" for e in enhanced),
            "Enhanced occurrence regression changed")
    require(not other_base, "Additional noneligible base occurrence needs explicit audit")
    require(not [w for w in selected if w["exotic"]] and not exotics, "Selected exotic/catalyst coverage changed")
    official_rows.sort(key=row_key)
    proofs.sort(key=row_key)
    direct.sort(key=option_key)
    enhanced.sort(key=option_key)
    rolls = [r for r in official_rows if ammo_by_id[r["id"]] in SCALARS]
    excluded_heavy = [{**r, "ammoType": 3, "reason": "Official base Snapshot roll exists, but no measured Heavy scalar; not runtime selectable."}
                      for r in official_rows if ammo_by_id[r["id"]] == 3]
    require(len(rolls) == len({r["id"] for r in rolls}) == 13
            and {row_key(r) for r in excluded_heavy} == EXPECTED_HEAVY and len(excluded_heavy) == 2,
            "Measured roll eligibility regression changed")

    extraction, base_profiles = sources["w44Extraction"], sources["w44Runtime"]
    raw_entries = extraction["entries"]
    raw_by_id = {e["id"]: (i, e) for i, e in enumerate(raw_entries)}
    profiles = {p["id"]: p["profile"] for p in base_profiles}
    ids = {w["id"] for w in selected}
    require(len(raw_entries) == len(raw_by_id) == len(base_profiles) == len(profiles) == 63
            and ids == raw_by_id.keys() == profiles.keys(), "W44/selected coverage mismatch")
    require(extraction["runtimeSha256"] == PINS["w44Runtime"]
            and extraction["sourceHashes"]["art/weapons/w40/definitions.json"] == PINS["selected"]
            and extraction["sourceHashes"]["art/weapons/w40/provenance.json"] == PINS["w40Provenance"]
            and extraction["officialManifest"] == w40
            and extraction["profileCount"] == 63 and extraction["supportedCount"] == 57,
            "W44 pinned raw/runtime/official lineage mismatch")
    timings, timing_audit = [], []
    for weapon in sorted(selected, key=lambda w: w["id"]):
        wid = weapon["id"]
        entry_index, entry = raw_by_id[wid]
        require(entry["bungieHash"] == weapon["bungieHash"], "Raw ADS exact weapon hash mismatch: " + wid)
        base_ticks = profiles[wid]["transitionTicks"]
        ammo = ammo_by_id[wid]
        require(type(base_ticks) is int and 2 <= base_ticks <= 20, "Unsafe W44 base ticks: " + wid)
        neutral = entry["family"] in ("sword", "glaive")
        require(entry["supported"] is (not neutral), "W44 supported-family mismatch: " + wid)
        record = {"id": wid, "hash": weapon["bungieHash"], "ammoType": ammo, "baseTicks": base_ticks,
                  "exitTicks": base_ticks, "noSnapshotTicks": base_ticks, "rawEntryIndex": entry_index,
                  "w44Supported": not neutral, "runtimeSelectable": any(r["id"] == wid for r in rolls)}
        if neutral:
            require("adsSeconds" not in entry and base_ticks == 2, "Neutral row has invented raw timing: " + wid)
            record.update(snapshotTicks=base_ticks, reason="W44 neutral sword/glaive; no raw ADS seconds and no Snapshot support.")
        else:
            seconds = entry["adsSeconds"]  # Preserve W44's parsed value; never round or infer from ticks.
            require(type(seconds) in (int, float) and math.isfinite(seconds) and seconds > 0,
                    "Unsafe raw ADS seconds: " + wid)
            curve, handling = entry["adsCurve"], entry["officialStats"]["handling"]
            require(handling == weapon["stats"]["943549884"] and type(handling) is int
                    and 0 <= handling <= 100 and curve.get("evpp", 0) == 0
                    and seconds == curve["offset"] + curve["vpp"] * handling,
                    "Raw ADS curve/stat binding changed: " + wid)
            require(base_ticks == max(2, min(20, math.ceil(seconds * 20))), "W44 base timing mismatch: " + wid)
            snapshot_ticks = (max(1, min(20, math.ceil(seconds * SCALARS[ammo] * 20)))
                              if ammo in SCALARS else base_ticks)
            timings.append({"id": wid, "baseTicks": base_ticks, "snapshotTicks": snapshot_ticks,
                            "ammoType": ammo, "adsSeconds": seconds})
            literal = raw_ads_literals[entry_index]["adsSeconds"]
            require(float(literal) == seconds, "Raw ADS literal binding mismatch: " + wid)
            record.update(adsSeconds=seconds, rawAdsSecondsLiteral=str(literal),
                          rawAdsSecondsPointer="/entries/" + str(entry_index) + "/adsSeconds",
                          adsCurve=curve, handling=handling, snapshotTicks=snapshot_ticks,
                          durationScalar=SCALARS.get(ammo),
                          reason="Measured Primary/Special candidate; apply only to a selected runtime roll."
                          if ammo in SCALARS else "Heavy has no measured scalar; keep W44 timing unchanged.")
        timing_audit.append(record)
    require(len(timings) == 57 and len(timing_audit) == 63
            and {e["id"] for e in timing_audit if not e["w44Supported"]} == EXPECTED_NEUTRAL,
            "Expected 57 raw timing rows plus six explicit neutral rows")
    require(all(r["id"] in {t["id"] for t in timings} for r in rolls), "Selectable roll lacks a raw timing")
    resource = {"schemaVersion": 1, "perkHash": BASE, "primaryScalar": SCALARS[1],
                "specialScalar": SCALARS[2], "rolls": rolls, "timings": timings}
    pools = {
        "stage": "W68", "selectedCount": 63, "officialBaseRandomizedRows": 15,
        "runtimeRollCount": 13, "perkDefinitions": definitions,
        "policy": "Enumerate every selected exact hash, every socket, initial/direct reusable items and both plug-set fields. Exact base 957782887 must be currentlyCanRoll=true in its own nonfake randomized trait pool. Weights do not override rollability. Preserve official Heavy rolls as evidence but exclude them from runtime for lack of a measured scalar. Direct overlaps add no rows. Enhanced 4116820839, exotics, catalysts and neutral sword/glaive timings are unsupported.",
        "officialBaseRows": official_rows, "weapons": proofs, "runtimeRolls": rolls,
        "excludedHeavy": excluded_heavy, "directSocketOptions": direct,
        "enhancedSelectedOptionsExcluded": enhanced, "otherBasePoolOccurrencesNotSelected": other_base,
        "exoticBaseOccurrencesExcluded": exotics,
        "exoticCatalystExclusion": {"selectedExoticCount": 0, "selectedExoticIds": [],
                                   "scope": "Selected 63 only; no global catalyst census. Shared names or catalyst text cannot establish base randomized eligibility."},
        "selectionAudit": audit,
        "noOfficialBaseRandomizedRollIds": sorted(ids - {r["id"] for r in official_rows}),
        "notRuntimeSelectableIds": sorted(ids - {r["id"] for r in rolls}),
    }
    timing_evidence = {
        "stage": "W68", "selectedCount": 63, "rawTimingCount": 57, "neutralCount": 6,
        "ammoTypes": {"1": "Primary", "2": "Special", "3": "Heavy"},
        "rawSource": "art/weapons/w44/extraction.json", "rawSourceSha256": PINS["w44Extraction"],
        "baseSource": "src/main/resources/destiny/weapons/w44-aim.json", "baseSourceSha256": PINS["w44Runtime"],
        "formulaLineage": {k: extraction[k] for k in ("repository", "commit", "commitDate", "source", "sourceSha256")},
        "policy": "Use each exact W44 entries[n].adsSeconds value at its stored precision. Verify its curve/official Handling binding and W44 base ticks. Apply scalar to seconds BEFORE ceil(*20), then clamp 1..20. Retain all 63 base/noSnapshot/exit ticks. Heavy snapshot ticks equal base with no duration scalar; six neutral rows have no invented adsSeconds. Candidate timing is not roll eligibility.",
        "entries": timing_audit,
    }
    mechanics = {
        "stage": "W68", "baseHash": BASE, "enhancedHashExcluded": ENHANCED,
        "measuredSecondary": {"url": MEASURED_URL, "publisher": "light.gg", "primary": False,
                              "privateCapture": "research1.json", "section": "Community Research",
                              "lastUpdatedReported": "2024-04-12", "primaryDurationScalar": 0.5,
                              "specialDurationScalar": 0.8,
                              "retrieval": "Pinned search capture bound to the exact base URL and its own bounded section; no fresh gameplay measurement."},
        "historicalOfficialConflict": {"urls": list(HISTORICAL_URLS), "year": 2022,
                                       "primaryDurationScalar": 0.5, "specialDurationScalar": 0.75,
                                       "status": "Unresolved. Historical official Special duration differs from the captured 2024 community measurement; no intervening patch explanation or independent current confirmation is established."},
        "serverPolicy": {"choice": "Measured-modern", "primaryScalar": 0.5, "specialScalar": 0.8,
                         "explanation": "Explicit supplied server choice follows the exact-base 2024 measurement despite the unresolved historical 2022 official conflict. This is not a claim that Bungie verified 0.8.",
                         "entry": "clamp(ceil(adsSeconds * ammoScalar * 20),1,20), only with a supported exact-base roll selected",
                         "exit": "Unchanged W44 baseTicks; entry-only speed is supplied project policy, not proven Destiny exit behavior.",
                         "unselected": "Keep each W44 base timing unchanged.",
                         "heavy": "No measured scalar. Official Heavy rolls remain references only; runtime selectable rolls exclude them and timing rows preserve snapshotTicks=baseTicks.",
                         "neutral": "Preserve six W44 two-tick neutral rows in reference evidence only; omit them from runtime timings."},
        "sourceBoundary": "Bungie inventory/plug sets prove exact identity, official faster-ADS description, ammo enum and selected roll eligibility. W44 is the pinned community-derived base-stat ADS model. Only the exact-base light.gg section supplies the chosen numeric duration reductions. Enhanced/mirror/catalyst sections do not establish base mechanics or eligibility.",
        "limitations": ["No native evidence or client launch; no live Destiny measurement.",
                        "No claim that historical/community conflict is resolved or that the chosen scalar matches today's Destiny sandbox.",
                        "20 Hz quantization/clamps and entry-only policy belong to this project.",
                        "A proven optional roll does not activate Snapshot on every weapon copy.",
                        "No production Java, test, implementation manifest or main-doc changes are generated."],
    }
    notes = make_notes(rolls, excluded_heavy, timings, timing_audit, enhanced)
    outputs = {TARGET: resource, REF + "socket-pools.json": pools,
               REF + "timings.json": timing_evidence, REF + "mechanics.json": mechanics, NOTES: notes}
    outputs[REF + "provenance.json"] = {
        "stage": "W68", "manifestVersion": VERSION,
        "inventoryUrl": BUNGIE + inventory_path, "plugSetsUrl": BUNGIE + plugsets_path,
        "sourceHashes": pins, "generator": SCRIPT,
        "generatorSha256": digest(Path(__file__).resolve().read_bytes()),
        "runtimeSha256": digest(encoded(resource)),
        "outputHashes": {name: digest(encoded(value)) for name, value in outputs.items()},
        "capturedAtDate": "2026-10-24",
        "privateSources": "Raw manifest, inventory, plug sets and research capture remain in private /tmp caches; only bounded paraphrased findings and selected socket proof are published.",
        "sourceBoundary": mechanics["sourceBoundary"],
        "reproduce": "rtk proxy python3 scripts/extract_snapshot_w68.py --verify",
        "verification": "All eight consumed inputs have literal SHA256 pins. Byte-exact read-only comparison covers all six outputs including Markdown. Missing/changed sources fail before writes; verify does not write, create directories, fetch, repair caches or access the network. Provenance records generator and five other output hashes, excluding its own hash.",
    }
    require(len(outputs) == 6, "Expected exactly six generated sidecar outputs")
    return outputs, paths


def make_notes(rolls, heavy, timings, audit, enhanced):
    by_id = {t["id"]: t for t in timings}
    roll_lines = "\n".join(
        f'| {r["id"]} | {r["hash"]} | {r["socket"]} | {r["perkHash"]} | {r["plugSetHash"]} |'
        for r in rolls)
    heavy_lines = "\n".join(
        f'| {r["id"]} | {r["hash"]} | {r["socket"]} | {r["plugSetHash"]} | {by_id[r["id"]]["baseTicks"]} |'
        for r in heavy)
    example_lines = "\n".join(
        f'| {wid} | {by_id[wid]["adsSeconds"]!r} | {by_id[wid]["ammoType"]} | {by_id[wid]["baseTicks"]} | {by_id[wid]["snapshotTicks"]} |'
        for wid in ("austringer", "beloved", "dust_rock_blues", "apostate", "bad_omens", "edge_transit"))
    neutral_ids = ", ".join('`' + e["id"] + '`' for e in audit if not e["w44Supported"])
    ammo_counts = {a: sum(t["ammoType"] == a for t in timings) for a in (1, 2, 3)}
    enhanced_lines = "\n".join(
        f'| {e["id"]} | {e["hash"]} | {e["socket"]} | {e["perkHash"]} | {e["plugSetHash"]} |'
        for e in enhanced)
    return f'''# W68 Snapshot Sights source and data sidecar

Full enumeration of all **63** selected exact official hashes yields **15 official randomized base rows**. **13 Primary/Special rows** are runtime selectable. Bad Omens and Edge Transit have official base Snapshot rolls, but their **2 Heavy rows** are excluded from runtime because no Heavy scalar was measured. Both direct duplicates and both enhanced occurrences are preserved separately. No native evidence is available.

## Exact runtime schema

`src/main/resources/destiny/weapons/w68-snapshot.json` has exactly `schemaVersion`, `perkHash`, `primaryScalar`, `specialScalar`, `rolls`, `timings`. Values are `1`, `957782887`, `0.5`, `0.8`, then the arrays. Each `rolls` entry uses the full WeaponPerks.Roll shape: `{{id,hash,socket,perkHash,plugSetHash}}`. Each `timings` entry has exactly `{{id,baseTicks,snapshotTicks,ammoType,adsSeconds}}`. `ammoType` is the official integer enum: **1 Primary, 2 Special, 3 Heavy**.

There are **57 raw timing rows** ({ammo_counts[1]} Primary, {ammo_counts[2]} Special, {ammo_counts[3]} Heavy). Their presence does not imply perk eligibility. All Heavy timing rows explicitly retain `snapshotTicks=baseTicks`; no Heavy scalar is guessed or supplied. The six W44 neutral entries are omitted from runtime timings and retained with unchanged two-tick base/noSnapshot/exit values in `references/timings.json`: {neutral_ids}.

## Exact selectable rolls

Socket indexes are zero based. Every row below comes from its own exact randomized trait plug set, with `currentlyCanRoll=true` and `isFakePlugSet=false`.

| ID | Weapon hash | Socket | Base perk hash | Randomized plug set |
|---|---:|---:|---:|---:|
{roll_lines}

## Official Heavy rolls excluded from runtime

These are real official base Snapshot rolls. They are unsupported for measured speed selection, rather than weapons without the perk.

| ID | Weapon hash | Socket | Randomized plug set | Unchanged base/snapshot ticks |
|---|---:|---:|---:|---:|
{heavy_lines}

## Complete enumeration and exclusions

`references/socket-pools.json` records all 15 official base rows, the 13 runtime rows, `excludedHeavy` with its reason, full matching entry records/indexes, each eligible socket entry, and an audit of every socket of all 63 selected definitions. Both `randomizedPlugSetHash` and `reusablePlugSetHash` are visited, along with direct initial/reusable items, including negative findings. Zero weights are preserved and do not negate `currentlyCanRoll=true`. No inferred name/reissue eligibility is used. Literal enumerated tuple regressions are checked only after the independent traversal finishes.

The two base direct defaults are Bite of the Fox (1403800851, socket 3) and Mindbender's Ambition Adept (912150785, socket 3). Each duplicates its own proven randomized row, adding **zero** runtime rows. The complete direct records appear in `directSocketOptions` with `alsoProvenRandomized=true` and `addsRuntimeRow=false`. The complete enhanced occurrences are excluded:

| ID | Weapon hash | Socket | Enhanced perk hash | Randomized plug set |
|---|---:|---:|---:|---:|
{enhanced_lines}

The exact base definition is **957782887**, while enhanced Snapshot is **4116820839**. Enhanced stability bonuses and shared mechanics text cannot make an enhanced entry a supported base roll. There are no additional base pool occurrences outside the 15 proven randomized rows. All 63 selected items are nonexotic. Exotics/catalysts remain unsupported; this is selected-item coverage, not a global catalyst census.

## Raw ADS provenance and tick policy

Raw seconds are read by exact ID/hash from the actual `entries` array in pinned `art/weapons/w44/extraction.json`, preserving its stored float precision. W44 records its community formula lineage as `d2foundry/oracle_engine`, commit `dcd0c7d302b056ffbb532edcb711d724a17ca8c1` (2026-05-20), `build_resources/weapon_formulas.json`, SHA256 `fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d`. This generator consumes the pinned W44 extraction, not an independently fetched/recomputed upstream formula snapshot. It checks the stored ADS curve against the exact official Handling value and binds the W44 runtime hash and all 63 IDs. `references/timings.json` preserves each raw numeric literal, JSON pointer, curve, Handling, and base/noSnapshot/exit ticks for all 63 selected weapons. The original upstream formula file is lineage metadata, not an additional consumed input.

For a selected supported roll, entry ticks are **`clamp(ceil(adsSeconds * ammoScalar * 20),1,20)`**. Scale raw seconds before rounding. Never scale W44's already rounded `baseTicks`, and never round raw seconds for calculation. Base ticks remain the pinned W44 runtime ticks, checked against its `clamp(ceil(adsSeconds*20),2,20)` policy. Unselected weapons retain those base ticks. **Exit remains unchanged at W44 base ticks**: entry-only speed is supplied project policy, not proof of Destiny's exit behavior.

| ID | Exact W44 adsSeconds | ammoType | baseTicks | snapshotTicks |
|---|---:|---:|---:|---:|
{example_lines}

Beloved demonstrates the rounding order: raw `0.41048327600999995 * 0.8 * 20` yields **7** ticks after ceil, while incorrectly scaling its rounded nine-tick base would yield eight. Dust Rock Blues similarly yields **6**, rather than seven from rounded base ticks. W44 source/runtime files are not modified.

## Numeric evidence and unresolved historical conflict

The exact-base [light.gg Community Research section]({MEASURED_URL}), reporting an update of **2024-04-12**, describes Primary ADS duration reduced by 50% and Special duration reduced by 20%. These correspond to duration scalars **0.5** and **0.8**. The generator binds those measurements to that exact URL, base API ID and bounded section. Enhanced sections, a mirror-domain result, and other weapon pages are not numeric base evidence. Official pinned definitions describe faster ADS and official socket pools prove roll availability; neither supplies these numeric reductions.

Historical official 2022 [May 5 clarification]({HISTORICAL_URLS[0]}), [Update 4.1.0]({HISTORICAL_URLS[1]}) and [April 21 preview]({HISTORICAL_URLS[2]}) instead document **0.75 Special**, with Primary remaining **0.5**. Their source statements are preserved as paraphrased findings in `references/mechanics.json`. **The conflict is unresolved.** No intervening patch explanation or fresh gameplay measurement establishes why 0.75 and 0.8 differ. The explicit **measured-modern server choice is 0.8 Special**, following the captured 2024 community measurement; this does not assert that Bungie confirmed 0.8 or certify today's Destiny sandbox. Heavy has no measured scalar and remains unsupported.

Raw source capture `/tmp/destiny-weapons-w68/research1.json` and official caches remain private. Public reference files contain bounded findings and selected socket proof, without full web/search captures. No native/client launch or live test was performed.

## Offline reproduction and verification

```sh
rtk proxy python3 scripts/extract_snapshot_w68.py
rtk proxy python3 scripts/extract_snapshot_w68.py --verify
```

All **eight consumed source files** have literal SHA256 pins: W40 definitions/provenance, official inventory/plug sets/manifest, the W68 research capture, W44 extraction, and W44 runtime. Default private caches are `/tmp/destiny-weapons-w30/bungie-items.json`, `/tmp/destiny-weapons-w60/{{manifest,bungie-plugsets}}.json`, and `/tmp/destiny-weapons-w68/research1.json`. Missing or changed input fails before any output write.

`--root` selects the input checkout. `--output-root` selects a separate output tree without changing inputs. `--inventory`, `--shared-sources-dir`, and `--sources-dir` override private source locations; content pins remain mandatory. Provenance records resolved source locations, so changing those locations changes provenance metadata only. The generator records its own SHA256 and all five non-provenance output hashes.

**`--verify` compares all six generated outputs byte for byte, including this Markdown**, collects every mismatch, and performs no writes, directory creation, networking, fetch or cache repair. Missing outputs fail without repair. Generation is limited to this notes file, the four `references/*.json` files, and the W68 runtime JSON. Production Java/tests, implementation.json, main docs and the existing W68 QA baseline are outside this generator's write scope.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Read-only byte-exact check of all six outputs")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    parser.add_argument("--shared-sources-dir", type=Path, default=Path("/tmp/destiny-weapons-w60"))
    parser.add_argument("--sources-dir", type=Path, default=Path("/tmp/destiny-weapons-w68"))
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
              ": W68; 63 selected; 15 official base randomized rows; 13 measured runtime rolls; 2 Heavy exclusions.")
        print("57 raw timing rows; 63 preserved base/noSnapshot/exit rows; 2 direct duplicates; 2 enhanced exclusions.")
        print("Primary 0.5; Special 0.8 measured-modern server policy; historical official 0.75 conflict unresolved; Heavy unchanged.")
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print("W68 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
