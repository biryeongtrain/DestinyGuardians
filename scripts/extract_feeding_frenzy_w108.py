#!/usr/bin/env python3
"""Offline W108 exact selected sockets and five Clarity Feeding Frenzy tiers.

No HTTP, credentials, build, or game access. --verify never writes. --self-test
adds negative input/membership/math tests in memory, without altering any files.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/extract_feeding_frenzy_w108.py"
REF = "art/weapons/w108/references/"
TARGET = "src/main/resources/destiny/weapons/w108-feeding-frenzy.json"
BASE, ENHANCED = 2779035018, 1171147302
TRAIT_CATEGORY, RELOAD_STAT = 4241085061, "4188031367"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
CLARITY_COMMIT = "039cfbc4732c33573568b28cc6335dd3332a9296"
DURATION_TICKS = 70
BONUSES = (8, 50, 60, 75, 100)
SCALARS = (.975, .9, .87, .84, .8)
POLICIES = {
    "stowPersistence": "UNKNOWN",
    "reloadConsumption": "UNKNOWN",
    "killRefreshAllStacks": "UNKNOWN",
    "expirationAllOrOneStack": "UNKNOWN",
    "reloadSnapshot": "AT_RELOAD_START_LOCAL_POLICY",
    "statCap": 100,
    "rounding": "CEIL_SECONDS_TIMES_20_ONCE",
    "shellFirstDelay": "PRESERVE_EXISTING_DISTINCT_FIRST_DELAY_IF_PRESENT",
    "combinedOutlaw": "NO_DISTINCT_SELECTED_SOCKET_PAIR",
}
# (exact selected ID, official item hash, zero-based socket, referenced pool)
EXPECTED_RANDOM = {
    ("seventh_seraph_officer_revolver", 3037520408, 4, 3527094473),
    ("steelfeather_repeater", 1251729046, 3, 473189353),
    ("cold_denial", 1216130969, 3, 330841869),
    ("blast_furnace", 3843477312, 3, 1976101165),
    ("brass_attacks", 2121785039, 3, 100135553),
    ("hollow_words", 607191995, 3, 637298592),
    ("coriolis_force", 3512349612, 3, 2568674372),
    ("retraced_path", 548958835, 3, 2945646047),
    ("fixed_odds", 2194955522, 3, 4227334000),
    ("hammerhead", 603242241, 3, 2515290473),
    ("retrofit_escapade", 3103325054, 3, 3756086698),
}
EXPECTED_FIXED = {("the_recluse", 3354242550, 3, 242),
                  ("null_composure", 1644680957, 3, 272)}
FIXED_POOL_HASHES = {242: [BASE], 272: [BASE, 1570042021]}
PINS = {
    "art/weapons/w40/definitions.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "art/weapons/w40/provenance.json": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "art/weapons/w43/extraction.json": "a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5",
    "art/weapons/w46/weapon_formulas.json": "fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d",
    "art/weapons/w46/stat_calc.rs": "5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2",
    "art/weapons/w46/rs_types.rs": "faa476e6589d2362cf9ee8dd948410adfa7fa8507e8809f3cd10bb13ebba9b90",
    "src/main/resources/destiny/weapons/w46-timing.json": "e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07",
    "src/main/resources/destiny/weapons/w62-outlaw.json": "5188d73a271b0a5080eb99d47c50a6d37ccae11fe756ebd2893c70499f3637bc",
    "src/main/resources/destiny/weapons/w77-dragonfly.json": "239e4fa48afebebd20ed765fc05b3e61bb34532bffea3a8cffdc536c867eab06",
    "src/main/resources/destiny/weapons/w80-payload.json": "000fef1ccea2cdc653f723be8d8eeefb209255673dcc8189b3732c69173a03fc",
    REF + "clarity-source.json": "0c44c13f8355b5b97e3502e6201315737521f7a3573a01f05201ee7a65c21461",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def check_pin(key, raw):
    require(digest(raw) == PINS[key], "Source SHA256 mismatch: " + key)


def validate_tiers(tiers):
    require(tiers == [{"stacks": i, "reloadBonus": b, "durationMultiplier": s}
                      for i, (b, s) in enumerate(zip(BONUSES, SCALARS), 1)],
            "Incomplete or incorrect five sourced tiers")


def validate_membership(rows):
    keys = [(r["id"], r["hash"], r["socket"], r["plugSetHash"]) for r in rows]
    require(len(keys) == len(set(keys)) == 13 and set(keys) == EXPECTED_RANDOM | EXPECTED_FIXED
            and all(r["perkHash"] == BASE for r in rows), "Exact selected socket membership changed")


def timing(curve, stat, tier):
    require(type(stat) is int and 0 <= stat <= 100, "Unsafe official Reload Speed stat")
    effective = min(100, stat + tier["reloadBonus"])
    seconds = (curve.get("evpp", 0) * effective * effective
               + curve.get("vpp", 0) * effective + curve["offset"]) * tier["durationMultiplier"]
    require(math.isfinite(seconds) and seconds > 0, "Invalid curve duration")
    return effective, seconds, math.ceil(seconds * 20)


def validate_proof(proof):
    socket = proof["socketEntry"]
    require(proof["socketCategoryHash"] == TRAIT_CATEGORY and proof["perkHash"] == BASE
            and len(proof["matchingEntries"]) == 1
            and proof["matchingEntries"][0]["item"]["plugItemHash"] == BASE
            and proof["matchingEntries"][0]["item"].get("currentlyCanRoll") is True,
            "Trait proof needs exactly one rollable base entry")
    if proof["selection"] == "randomized":
        require(not proof["isFakePlugSet"] and proof["plugSetField"] == "randomizedPlugSetHash"
                and socket.get("randomizedPlugSetHash") == proof["plugSetHash"],
                "Randomized proof cannot claim a fake or unrelated pool")
    else:
        require(proof["selection"] == "fixedCuratedInitialTrait" and proof["isFakePlugSet"]
                and proof["plugSetField"] == "reusablePlugSetHash"
                and socket.get("reusablePlugSetHash") == proof["plugSetHash"]
                and socket["singleInitialItemHash"] == BASE and not socket.get("randomizedPlugSetHash")
                and proof["fixedSelectablePerkHashes"] == FIXED_POOL_HASHES.get(proof["plugSetHash"]),
                "Curated proof needs exact initial trait and fixed selectable options")


def generate(args):
    root = args.root.resolve()
    paths = {p: root / p for p in PINS if "/" in p}
    paths.update(inventory=args.inventory, plugSets=args.shared_sources_dir / "bungie-plugsets.json",
                 manifest=args.shared_sources_dir / "manifest.json")
    require(paths.keys() == PINS.keys(), "All consumed inputs must be pinned")
    raw, sources, data = {}, {}, {}
    for key, path in paths.items():
        value = path.read_bytes()
        check_pin(key, value)
        raw[key] = value
        sources[key] = {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                        "sha256": digest(value), "bytes": len(value)}
        if key.endswith(".json") or key in ("inventory", "plugSets", "manifest"):
            data[key] = json.loads(value)
    selected = data["art/weapons/w40/definitions.json"]
    require(len(selected) == len({w["id"] for w in selected})
            == len({w["bungieHash"] for w in selected}) == 63, "Expected exact selected63")
    inv, pools = data["inventory"], data["plugSets"]
    response = data["manifest"]
    require(response["ErrorCode"] == 1, "Failed official manifest")
    manifest = response["Response"]
    ipath = "/common/destiny2_content/json/en/DestinyInventoryItemDefinition-" + SUFFIX
    ppath = ipath.replace("DestinyInventoryItemDefinition-", "DestinyPlugSetDefinition-")
    require(manifest["version"] == VERSION and
            manifest["jsonWorldComponentContentPaths"]["en"]["DestinyInventoryItemDefinition"] == ipath and
            manifest["jsonWorldComponentContentPaths"]["en"]["DestinyPlugSetDefinition"] == ppath,
            "Inventory and plug sets must share pinned manifest")
    w40 = data["art/weapons/w40/provenance.json"]
    require(w40["manifest"] == {"version": VERSION, "path": ipath}
            and w40["cachedInventorySha256"] == PINS["inventory"]
            and w40["source"] == "https://www.bungie.net" + ipath, "Selected provenance mismatch")
    definitions = []
    for h, kind in ((BASE, "Trait"), (ENHANCED, "Enhanced Trait")):
        perk = inv[str(h)]
        require(perk["hash"] == h and perk["displayProperties"]["name"] == "Feeding Frenzy"
                and perk["itemTypeDisplayName"] == kind and perk["itemType"] == 19
                and not perk["redacted"] and not perk["blacklisted"] and not perk["plug"]["isDummyPlug"],
                "Invalid Feeding Frenzy definition")
        definitions.append({"hash": h, "name": "Feeding Frenzy", "itemTypeDisplayName": kind,
                            "description": perk["displayProperties"]["description"]})
    require({i["hash"] for i in inv.values() if i.get("displayProperties", {}).get("name") == "Feeding Frenzy"}
            == {BASE, ENHANCED}, "Review unknown same-name base/enhanced copies")

    rows, proofs, scans, enhanced, direct = [], [], [], [], []
    random_keys, fixed_keys = set(), set()
    for w in selected:
        item = inv[str(w["bungieHash"])]
        require(item["hash"] == w["bungieHash"] and item["itemType"] == 3
                and not item["redacted"] and not item["blacklisted"]
                and {k: v["value"] for k, v in item["stats"]["stats"].items()} == w["stats"],
                "Selected official hash/stat mismatch")
        sockets = item.get("sockets", {})
        trait_indexes = {n for c in sockets.get("socketCategories", [])
                         if c["socketCategoryHash"] == TRAIT_CATEGORY for n in c["socketIndexes"]}
        scan = {"id": w["id"], "hash": item["hash"], "traitSocketIndexes": sorted(trait_indexes),
                "scannedSocketCount": len(sockets.get("socketEntries", [])), "referencedPools": []}
        for index, socket in enumerate(sockets.get("socketEntries", [])):
            direct_hashes = {socket["singleInitialItemHash"],
                             *[p["plugItemHash"] for p in socket.get("reusablePlugItems", [])]}
            for h in (BASE, ENHANCED):
                if h in direct_hashes:
                    direct.append({"id": w["id"], "hash": item["hash"], "socket": index,
                                   "perkHash": h, "initial": socket["singleInitialItemHash"] == h})
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                ph = socket.get(field)
                if not ph:
                    continue
                pool = pools[str(ph)]
                require(pool["hash"] == ph and not pool["redacted"] and not pool["blacklisted"],
                        "Invalid official referenced plug set")
                entries = pool.get("reusablePlugItems", [])
                matches = [{"index": n, "item": p} for n, p in enumerate(entries) if p["plugItemHash"] == BASE]
                ematches = [{"index": n, "item": p} for n, p in enumerate(entries) if p["plugItemHash"] == ENHANCED]
                scan["referencedPools"].append({"socket": index, "field": field, "plugSetHash": ph,
                    "isFakePlugSet": pool["isFakePlugSet"], "baseMatchingEntries": matches,
                    "enhancedMatchingEntries": ematches})
                if ematches:
                    enhanced.append({"id": w["id"], "hash": item["hash"], "socket": index,
                                     "field": field, "plugSetHash": ph, "perkHash": ENHANCED})
                eligible = [p for p in matches if p["item"].get("currentlyCanRoll") is True]
                fixed = (w["id"], item["hash"], index, ph) in EXPECTED_FIXED
                if field == "randomizedPlugSetHash" and eligible:
                    require(not pool["isFakePlugSet"] and len(eligible) == 1,
                            "Randomized pool must be real with exactly one eligible base entry")
                    selection = "randomized"
                    random_keys.add((w["id"], item["hash"], index, ph))
                elif fixed and field == "reusablePlugSetHash":
                    require(socket["singleInitialItemHash"] == BASE and not socket.get("randomizedPlugSetHash")
                            and pool["isFakePlugSet"] and len(eligible) == 1
                            and [p["plugItemHash"] for p in entries] == FIXED_POOL_HASHES[ph]
                            and all(p.get("currentlyCanRoll") is True for p in entries),
                            "Fixed curated initial trait or exact reusable options changed")
                    selection = "fixedCuratedInitialTrait"
                    fixed_keys.add((w["id"], item["hash"], index, ph))
                else:
                    continue
                require(index in trait_indexes and not w["exotic"] and item["inventory"]["tierType"] == 5,
                        "Base trait must occupy selected legendary trait-category socket")
                row = {"id": w["id"], "hash": item["hash"], "socket": index,
                       "perkHash": BASE, "plugSetHash": ph}
                rows.append(row)
                proofs.append({**row, "selection": selection, "socketCategoryHash": TRAIT_CATEGORY,
                               "socketEntry": socket, "plugSetField": field,
                               "isFakePlugSet": pool["isFakePlugSet"], "matchingEntries": eligible,
                               "fixedSelectablePerkHashes": FIXED_POOL_HASHES[ph] if fixed else None})
        scans.append(scan)
    validate_membership(rows)
    for proof in proofs:
        validate_proof(proof)
    require(random_keys == EXPECTED_RANDOM and fixed_keys == EXPECTED_FIXED,
            "Randomized versus curated classification changed")
    require({e["id"] for e in enhanced} == {"retraced_path", "fixed_odds", "retrofit_escapade"}
            and len(enhanced) == 3, "Enhanced selected exclusions changed")

    clarity = data[REF + "clarity-source.json"]
    require(clarity["commit"] == CLARITY_COMMIT and clarity["sourceFileSha256"] ==
            "881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
            "Unpinned Clarity commit or parent document")
    entry = clarity["entries"][str(BASE)]
    text = "\n".join(line.get("text", "") for block in entry["descriptions"]["en"]
                     for line in block.get("linesContent", []))
    require(entry["hash"] == BASE and entry["type"] == "Weapon Trait"
            and "Weapon Kills grant 1 Stack of Feeding Frenzy for 3.5 seconds" in text
            and "Maximum of 5 Stacks." in text and "8|50|60|75|100 Reload Speed" in text
            and "2.5%|10%|13%|16%|20% decreased Reload Animation Duration" in text,
            "Exact-base Clarity numbers not established")
    tiers = [{"stacks": i, "reloadBonus": b, "durationMultiplier": s}
             for i, (b, s) in enumerate(zip(BONUSES, SCALARS), 1)]
    validate_tiers(tiers)
    mapping_source = data["art/weapons/w43/extraction.json"]
    mapping = {m["id"]: m for m in mapping_source["entries"]}
    formulas = data["art/weapons/w46/weapon_formulas.json"]
    base_timings = {t["id"]: t["timing"] for t in data["src/main/resources/destiny/weapons/w46-timing.json"]}
    require("reload_time = self.reload_data.solve_at(_reload_stat as f64)" in raw["art/weapons/w46/stat_calc.rs"].decode()
            and "out.reload_time *= modifiers.reload_time_scale;" in raw["art/weapons/w46/stat_calc.rs"].decode()
            and "self.evpp * _x * _x + self.vpp * _x + self.offset" in raw["art/weapons/w46/rs_types.rs"].decode(),
            "Historical W46 curve/scalar semantics changed")
    by_id = {w["id"]: w for w in selected}
    curves, reloads, audits = [], [], []
    for row in rows:
        w, m, base = by_id[row["id"]], mapping[row["id"]], base_timings[row["id"]]
        require(base["supported"] and m["family"] not in ("Bow", "Sword"), "Unreviewed timing family")
        curve = formulas[m["family"]]["cat"][m["category"]]["reload"]
        require(set(curve) <= {"evpp", "vpp", "offset", "ammo_percent"}, "Unknown reload curve fields")
        stat = w["stats"][RELOAD_STAT]
        _, base_seconds, base_ticks = timing(curve, stat, {"reloadBonus": 0, "durationMultiplier": 1})
        require(base_ticks == base["reloadPerRoundTicks" if base["shellReload"] else "reloadTicks"],
                "W46 baseline cannot be reproduced")
        # No selected W108 shell weapon. Fail rather than invent an initial delay;
        # the declared policy requires separate review if membership ever changes.
        require(not base["shellReload"] and base["reloadInitialTicks"] is None,
                "Review and preserve distinct shell first-delay policy before adding a shell weapon")
        coefficients = {k: curve.get(k, 0) for k in ("evpp", "vpp", "offset")}
        curves.append({"id": row["id"], **coefficients})
        for tier in tiers:
            effective, seconds, ticks = timing(curve, stat, tier)
            require(1 <= ticks <= base_ticks, "Buff cannot slow selected baseline")
            reloads.append({"id": row["id"], "stacks": tier["stacks"], "firstTicks": ticks,
                            "intervalTicks": ticks, "baseReloadStat": stat, "effectiveReloadStat": effective})
        audits.append({"id": row["id"], "hash": row["hash"], "family": m["family"],
                       "category": m["category"], "subfamily": m["subfamily"], "curve": curve,
                       "baseReloadStat": stat, "baseSeconds": base_seconds, "baseTicks": base_ticks,
                       "shellReload": False, "firstDelayClassification": "HISTORICAL_W46_WHOLE_MAGAZINE_CURVE"})
    outlaw = data["src/main/resources/destiny/weapons/w62-outlaw.json"]
    overlaps = [{"id": a["id"], "hash": a["hash"], "feedingFrenzySocket": a["socket"],
                 "outlawSocket": b["socket"], "sameSocketExclusive": a["socket"] == b["socket"],
                 "feedingFrenzyPlugSetHash": a["plugSetHash"], "outlawPlugSetHash": b["plugSetHash"]}
                for a in rows for b in outlaw["weapons"] if a["hash"] == b["hash"]]
    require(len(overlaps) == 1 and overlaps[0]["id"] == "blast_furnace"
            and overlaps[0]["sameSocketExclusive"], "Review distinct-socket composition rather than inventing it")
    dragonfly = data["src/main/resources/destiny/weapons/w77-dragonfly.json"]
    payload = data["src/main/resources/destiny/weapons/w80-payload.json"]
    secondary_overlaps = {name: [{"id": a["id"], "hash": a["hash"],
        "feedingFrenzySocket": a["socket"], "otherSocket": b["socket"], "otherPerkHash": b["perkHash"],
        "otherPlugSetHash": b["plugSetHash"], "simultaneousSelectionPossible": a["socket"] != b["socket"]}
        for a in rows for b in other["weapons"] if a["hash"] == b["hash"]]
        for name, other in (("dragonfly", dragonfly), ("payload", payload))}
    require(len(secondary_overlaps["dragonfly"]) == 1
            and secondary_overlaps["dragonfly"][0]["id"] == "brass_attacks"
            and secondary_overlaps["dragonfly"][0]["simultaneousSelectionPossible"]
            and not secondary_overlaps["payload"], "Selected secondary-perk overlaps changed")
    limitations = [
        "Manifest proves exact selected optional traits and stats, not that any stack automatically selects a trait.",
        "Clarity is community research. Its live-branch commit is pinned; this is not a new Destiny gameplay measurement.",
        "The exact-base Clarity entry does not establish stow persistence, reload consumption, refresh scope or expiration mode.",
        "Absolute reload durations inherit W46 historical community approximations, not a current sandbox certification.",
        "Reload-start snapshot and tick quantization are local integration policies.",
        "No enhanced, newer weapon copies, armor/magazine/masterwork modifiers or unproved combined-perk formulas.",
        "All 13 selected supported weapons use whole-magazine timing; no first-shell measurement is inferred.",
    ]
    resource = {"stage": "W108", "perk": {"id": "feeding_frenzy", "hash": BASE,
        "durationTicks": DURATION_TICKS, "maxStacks": 5, "timingSource": REF + "reload-timings.json",
        "mechanicsSource": REF + "mechanics.json"}, "policies": POLICIES, "tiers": tiers,
        "weapons": rows, "curves": curves, "reloads": reloads}
    mechanics = {"stage": "W108", "baseHash": BASE, "enhancedHashExcluded": ENHANCED,
        "officialTrigger": {"description": definitions[0]["description"], "primary": True,
            "source": "Pinned official DestinyInventoryItemDefinition", "requiresPrecision": False,
            "requiresReloadToActivate": False},
        "communitySource": {"url": clarity["url"], "commit": CLARITY_COMMIT,
            "commitDate": clarity["commitDate"], "entryLastUploadEpochMillis": entry["lastUpload"],
            "primary": False, "localExcerpt": REF + "clarity-source.json", "text": text},
        "durationSeconds": 3.5, "durationTicks": DURATION_TICKS, "maxStacks": 5,
        "tiers": tiers, "policies": POLICIES,
        "unknownLifecycle": {"stowPersistence": None, "reloadConsumption": None,
            "killRefreshAllStacks": None, "expirationAllOrOneStack": None,
            "reason": "Not specified in the pinned base Clarity entry or official description; master must label any implementation choice local policy."},
        "reloadFormula": {"effectiveReloadStat": "min(100, baseReloadStat + tier.reloadBonus)",
            "seconds": "(evpp * effectiveReloadStat^2 + vpp * effectiveReloadStat + offset) * tier.durationMultiplier",
            "ticks": "ceil(seconds * 20), once after stat and scalar",
            "curveClassification": "Same pinned historical W46 Oracle curve inputs used by W62",
            "ammoPercent": "Source field retained in audit only; no independent ammo-transfer timing is claimed."},
        "outlawOverlap": overlaps, "distinctSocketCompositionProven": False,
        "secondaryPerkOverlaps": secondary_overlaps,
        "dragonflySecondaryKillFeedingFrenzyCredit": {"verifiedDestinyBehavior": False,
            "sourceProven": None,
            "localPolicy": "Master credits confirmed Dragonfly secondary weapon final blows using original paid source token; unrelated ability kills do not qualify.",
            "boundary": "Pinned exact-base Clarity entry says Weapon Kills, but does not explicitly establish Dragonfly secondary-kill proc attribution."},
        "limitations": limitations}
    sockets = {"stage": "W108", "selectedCount": 63, "supportedCount": 13,
        "randomizedCount": 11, "fixedCuratedCount": 2, "perkDefinitions": definitions,
        "policy": "Exact selected hash and trait-category socket. Randomized eligibility requires real randomized pool and currentlyCanRoll=true; weight0 is not exclusion. Fixed curated eligibility requires the selected item's own base initial trait and exact fake reusable pool; never called random. Recluse242 is singleton; NullComposure272 has FeedingFrenzy/HeatingUp choices.",
        "weapons": proofs, "enhancedOptionsExcluded": enhanced, "directOptions": direct,
        "unsupportedSelectedIds": [w["id"] for w in selected if w["id"] not in {r["id"] for r in rows}],
        "allSelectedPoolScans": scans, "outlawOverlap": overlaps, "secondaryPerkOverlaps": secondary_overlaps}
    timings = {"stage": "W108", "repository": mapping_source["repository"],
        "commit": mapping_source["commit"], "commitDate": mapping_source["commitDate"],
        "source": "build_resources/weapon_formulas.json",
        "licenseSources": ["art/weapons/w46/MIT-LICENSE", "art/weapons/w46/UNLICENSE"],
        "formula": mechanics["reloadFormula"], "entries": audits, "reloads": reloads,
        "limitations": limitations}
    provenance = {"stage": "W108", "selectedCount": 63, "manifestVersion": VERSION,
        "inventoryUrl": "https://www.bungie.net" + ipath, "plugSetsUrl": "https://www.bungie.net" + ppath,
        "sourcePins": sources, "generator": SCRIPT, "generatorSha256": digest((root / SCRIPT).read_bytes()),
        "runtimeSha256": digest(encoded(resource)), "retrievedAtDate": "2026-10-25",
        "reproduce": "rtk proxy python3 scripts/extract_feeding_frenzy_w108.py --verify --self-test",
        "verification": "Read-only offline byte comparison; every consumed source SHA pinned. Negative tests mutate in-memory copies only. No source credentials.",
        "research": {"primary": "Existing official matching inventory/plugset JSON caches",
            "numeric": "Public Clarity exact-base entry from pinned current live commit",
            "directLightgg": "HTTP403; no assertion based on unavailable page",
            "lifecycle": "Unknown beyond stated per-kill stack grant, duration and maximum; no defaults inferred",
            "researchChild": None}, "limitations": limitations}
    return {TARGET: resource, REF + "mechanics.json": mechanics, REF + "socket-pools.json": sockets,
            REF + "reload-timings.json": timings, REF + "provenance.json": provenance}, paths


def self_test(outputs):
    resource = outputs[TARGET]
    rejected = []

    def rejects(name, fn):
        try:
            fn()
        except (ValueError, KeyError, TypeError):
            rejected.append(name)
            return
        raise ValueError("Negative self-test unexpectedly accepted " + name)

    rejects("mutated pinned source", lambda: check_pin(REF + "clarity-source.json", b"mutated"))
    for name, edit in (
        ("missing selected socket", lambda r: r.pop()),
        ("duplicate selected socket", lambda r: r.append(r[0])),
        ("new weapon copy", lambda r: r[0].update(hash=r[0]["hash"] + 1)),
        ("wrong trait socket", lambda r: r[0].update(socket=0)),
        ("enhanced perk", lambda r: r[0].update(perkHash=ENHANCED)),
        ("curated treated as other pool", lambda r: next(x for x in r if x["id"] == "the_recluse").update(plugSetHash=243)),
    ):
        rows = copy.deepcopy(resource["weapons"])
        edit(rows)
        rejects(name, lambda: validate_membership(rows))
    for name, edit in (
        ("missing tier", lambda t: t.pop()),
        ("unsourced scalar", lambda t: t[0].update(durationMultiplier=.9)),
        ("unsourced bonus", lambda t: t[0].update(reloadBonus=10)),
    ):
        tiers = copy.deepcopy(resource["tiers"])
        edit(tiers)
        rejects(name, lambda: validate_tiers(tiers))
    for name, edit in (
        ("fake randomized pool", lambda p: p.update(isFakePlugSet=True)),
        ("not currently rollable", lambda p: p["matchingEntries"][0]["item"].update(currentlyCanRoll=False)),
        ("unrelated pool", lambda p: p["socketEntry"].update(randomizedPlugSetHash=1)),
    ):
        proof = copy.deepcopy(outputs[REF + "socket-pools.json"]["weapons"][0])
        edit(proof)
        rejects(name, lambda: validate_proof(proof))
    rejects("invalid stat", lambda: timing({"offset": 1}, -1, resource["tiers"][0]))
    rejects("nonfinite curve", lambda: timing({"offset": float("nan")}, 50, resource["tiers"][0]))
    curves = {c["id"]: c for c in resource["curves"]}
    for row in resource["reloads"]:
        tier = resource["tiers"][row["stacks"] - 1]
        effective, _, ticks = timing(curves[row["id"]], row["baseReloadStat"], tier)
        require(row["firstTicks"] == row["intervalTicks"] == ticks and row["effectiveReloadStat"] == effective,
                "Tier timing self-test mismatch")
    require(len(resource["reloads"]) == 65, "Incomplete weapon/tier Cartesian product")
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--self-test", action="store_true", help="Read-only negative input and math contracts")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    parser.add_argument("--shared-sources-dir", type=Path, default=Path("/tmp/destiny-weapons-w60"))
    args = parser.parse_args()
    try:
        require(not (args.verify and args.output_root), "--verify cannot write to --output-root")
        outputs, inputs = generate(args)
        rejected = self_test(outputs) if args.self_test else []
        output_root = (args.output_root or args.root).resolve()
        input_paths = {p.resolve() for p in inputs.values()} | {(args.root / SCRIPT).resolve()}
        for relative, value in outputs.items():
            path = (output_root / relative).resolve()
            require(path.is_relative_to(output_root) and path not in input_paths, "Output aliases input or escapes root")
            content = encoded(value)
            if args.verify:
                require(path.read_bytes() == content, "Generated bytes differ: " + relative)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        print(json.dumps({"stage": "W108", "status": "VERIFY_PASS" if args.verify else "GENERATED",
            "selected": 63, "supported": 13, "randomized": 11, "fixedCurated": 2,
            "reloadPlans": 65, "negativeCasesRejected": rejected, "outputs": list(outputs)}, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("W108 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
