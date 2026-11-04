#!/usr/bin/env python3
"""Offline W176 Stats for All: exact selected65 scanner, historical curves, joint sockets.

--verify writes nothing. --self-test checks mutations and deterministic repeat in memory.
No runtime/native claims. All input bytes are pinned; only four owned JSON outputs.
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
SCRIPT = "scripts/build_stats_for_all_profile_w176.py"
ART = "art/weapons/w176/stats-for-all/"
TARGET = "src/main/resources/destiny/weapons/w176-stats-for-all.json"
BASE, ENHANCED, TRAIT_CATEGORY = 1583705720, 1409206216, 4241085061
COMMIT = "039cfbc4732c33573568b28cc6335dd3332a9296"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
EXPECTED = {
    ("ammit_ar2", 2119346509, 3, BASE, 1723759242),
    ("aishas_embrace", 2638190703, 3, BASE, 7997267),
    ("dimensional_hypotrochoid", 1311684613, 3, BASE, 3235863202),
    ("retrofit_escapade", 3103325054, 3, BASE, 3756086698),
}
PERK = {"id": "stats_for_all", "hash": BASE, "hitWindowTicks": 60, "durationTicks": 200,
        "handlingBonus": 35, "reloadBonus": 35, "stabilityBonus": 10, "rangeBonus": 10,
        "falloffScalar": 1.05, "reloadScalar": 0.95, "refresh": False}
POLICIES = {
    "statCap": 100, "rounding": "CEIL_SECONDS_TIMES_20_ONCE",
    "bonusInputs": "TOTALS_INCLUDE_SFA_DO_NOT_ADD_35_AGAIN",
    "reloadScalarInput": "TOTAL_PRODUCT_INCLUDES_SFA_0_95_ONCE",
    "handling": "W58_STOW_AT100_FLOOR_NO_EXTRA_CLAMP",
    "ads": "W44_CLAMP_2_20_NO_COMPATIBLE_SNAPSHOT_ON_THESE_FOUR",
    "ballistics": "W43_HIP_RANGE_PLUS10_CAP100_THEN_1_05_BOTH_ENDPOINTS_MASTER_ADS_AFTER",
    "explosive": "RANGE_INDEPENDENT_SENTINEL_NEUTRAL_NO_TRAVEL_OR_BLAST_INVENTION",
    "collection": "NEW_DISTINCT_TARGET_RENEWS60_DUPLICATE_NO_EXTEND_NO_COLLECTION_WHILE_ACTIVE",
    "expiry": "INCLUSIVE_DEADLINE_EXPIRED_QUERIES_PURE",
    "stowReload": "LOCAL_PRESERVE_DEADLINES_TIME_CONTINUES_NOT_SOURCE_PROVEN",
    "lifecycle": "MASTER_IDENTITY_SESSIONS_ATTRIBUTION_LOCAL_POLICY",
}
PINS = {
    "src/main/resources/destiny/weapons/w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    "src/main/resources/destiny/weapons/w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "src/main/resources/destiny/weapons/w46-timing.json": "e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07",
    "src/main/resources/destiny/weapons/w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    "src/main/resources/destiny/weapons/w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "art/weapons/w40/provenance.json": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "clarity": "881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
    "scripts/build_focused_fury_profile_w174.py": "16af0279de7274a1912f247fe275413bcc98c748b59fe5eab3a5ae9c0505a7ab",
    "scripts/build_frenzy_profile_w172.py": "9796b90db4e8cf8f8fc64e33663e5e2ea2d820a0d94f5c7f3937c3645d393795",
    "src/main/resources/destiny/weapons/w43-ballistics.json": "0e5f7031795f4db7596664a97229699b8d4eb054d8450d0fb6e7e53368946ec0",
    "src/main/resources/destiny/weapons/w44-aim.json": "0d0a38469c28a74c1a77489d346184eccef347a604c0c0c455d1c7c2e1a80fc8",
    "src/main/resources/destiny/weapons/w58-handling.json": "4de7d346a93c822784fafa69b62ac66148d51cc11cf2da6706367682b414d3f1",
    "art/weapons/w43/extraction.json": "a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5",
    "art/weapons/w46/weapon_formulas.json": "fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d",
    "art/weapons/w46/stat_calc.rs": "5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2",
    "art/weapons/w46/rs_types.rs": "faa476e6589d2362cf9ee8dd948410adfa7fa8507e8809f3cd10bb13ebba9b90",
    "art/weapons/w44/extraction.json": "6a82eb21264ffab1e897cf9b0a74ad0cef0c252b129438f2938d82414a7da9fc",
    "art/weapons/w58/extraction.json": "934511861839eb1fa5b60ea1cc0d5a9ad5e133a08ac1ee8d567a431044e7063d",
    "scripts/extract_aim_w44.py": "0c1160b2a846165dad7820fa1a085198a7a51650312d78fdabdbe4ff3b492ea6",
    "scripts/extract_handling_w58.py": "177981eb79edd79bb2c4c1e80618183ac2156ddfe5106e93fa70d69786b9b934",
    "art/weapons/w46/MIT-LICENSE": "50173139375c53459837abdeb7ad9f264eba4f0bc2bb2c676932991ce158778d",
    "art/weapons/w46/UNLICENSE": "6b0382b16279f26ff69014300541967a356a666eb0b91b422f6862f6b7dad17e",
    "src/main/resources/destiny/weapons/w68-snapshot.json": "7e824633be32953e6c75d3d856ce765223fbb1cbcc3b01affca3d83eb8fcb738",
    "src/main/resources/destiny/weapons/w172-frenzy.json": "28a3722a9ea57dc7400a68ddcee80f6c661bf23a1abd0f4dc92dec9065120862",
    "src/main/resources/destiny/weapons/w173-adrenaline-junkie.json": "b2c0d5865d9d72f9ee4d1bd3439d940d52574d7d7539604a9b4fe1e82c3fbf65"
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def eligible(socket_index, trait_indexes, field, pool, match, exotic, perk_hash=BASE):
    # Same predicate as pinned W174. Zero weight is eligible if currentlyCanRoll is true.
    return (not exotic and socket_index in trait_indexes and field == "randomizedPlugSetHash"
            and not pool["isFakePlugSet"] and match["plugItemHash"] == perk_hash
            and match.get("currentlyCanRoll") is True)


def validate_membership(rows):
    require(all(type(r) is dict and set(r) == {"id", "hash", "socket", "perkHash", "plugSetHash"}
                for r in rows), "Exact roll schema")
    keys = [tuple(r[k] for k in ("id", "hash", "socket", "perkHash", "plugSetHash")) for r in rows]
    require(len(keys) == len(set(keys)) == 4 and set(keys) == EXPECTED, "Exact selected4 sockets")


def solve(curve, stat):
    require(set(curve) == {"evpp", "vpp", "offset"} and all(type(v) in (int, float)
            and math.isfinite(v) for v in curve.values()), "Finite exact quadratic schema")
    result = curve["evpp"] * stat * stat + curve["vpp"] * stat + curve["offset"]
    require(math.isfinite(result) and 0 < result <= 60, "Safe duration")
    return result


def evaluate(curve, bonus=0, scalar=1.0):
    require(type(bonus) is int and type(scalar) in (int, float) and math.isfinite(scalar)
            and 0 < scalar <= 1, "Safe total bonus/scalar")
    h = min(100, max(0, curve["baseHandlingStat"] + bonus))
    r = min(100, max(0, curve["baseReloadStat"] + bonus))
    seconds = {"reload": solve(curve["reload"], r) * scalar,
               "ready": solve(curve["ready"], h),
               "stow": max(solve(curve["stow"], h), solve(curve["stow"], 100)),
               "ads": solve(curve["ads"], h)}
    return {k + "Ticks": (max(2, min(20, math.ceil(v * 20))) if k == "ads" else max(1, math.ceil(v * 20)))
            for k, v in seconds.items()}


def ballistics(curve, active):
    require(type(active) is bool, "Boolean active")
    b = curve["ballistics"]
    neutral = curve["baseRangeStat"] is None
    require(not neutral or b["vppStart"] == b["vppEnd"] == 0, "Range-independent sentinel")
    stat = 0 if neutral else min(100, max(0, curve["baseRangeStat"] + (10 if active else 0)))
    scale = 1.05 if active and not neutral else 1
    return {"start": (b["offsetStart"] + b["vppStart"] * stat) * scale,
            "end": (b["offsetEnd"] + b["vppEnd"] * stat) * scale,
            "floor": b["floor"], "precision": b["precision"]}


def validate_resource(resource, curves):
    require(set(resource) == {"stage", "perk", "policies", "weapons", "curves"}
            and resource["stage"] == "W176" and resource["perk"] == PERK
            and resource["policies"] == POLICIES, "Pinned resource schema/mechanics/policies")
    validate_membership(resource["weapons"])
    require(resource["curves"] == curves, "Pinned exact curves/stats/ballistics")


def generate(args):
    root = args.root.resolve()
    paths = {p: root / p for p in PINS if "/" in p}
    paths.update(inventory=args.inventory, plugSets=args.shared_sources_dir / "bungie-plugsets.json",
                 manifest=args.shared_sources_dir / "manifest.json", clarity=args.clarity)
    data, pins, raw = {}, {}, {}
    for key, path in paths.items():
        value = path.read_bytes()
        require(digest(value) == PINS[key], "Source SHA256 mismatch: " + key)
        raw[key] = value
        pins[key] = {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                     "sha256": digest(value), "bytes": len(value)}
        if key.endswith(".json") or key in ("inventory", "plugSets", "manifest", "clarity"):
            data[key] = json.loads(value)
    catalog = data["src/main/resources/destiny/weapons/w30.json"][:]
    selected = data["src/main/resources/destiny/weapons/w40-characteristics.json"][:]
    timing = data["src/main/resources/destiny/weapons/w46-timing.json"][:]
    for f in ("w83-exotics.json", "w84-exotics.json"):
        for row in data["src/main/resources/destiny/weapons/" + f]:
            catalog.append(row["catalog"])
            selected.append(row["characteristics"])
            timing.append(row["timing"])
    require(len(catalog) == len(selected) == len({w["id"] for w in selected})
            == len({w["bungieHash"] for w in selected}) == 65, "Selected65 coverage")
    require({w["id"] for w in selected} == {w["id"] for w in catalog}, "Selected IDs")
    inv, pools, response = data["inventory"], data["plugSets"], data["manifest"]
    ipath = "/common/destiny2_content/json/en/DestinyInventoryItemDefinition-" + SUFFIX
    ppath = ipath.replace("DestinyInventoryItemDefinition-", "DestinyPlugSetDefinition-")
    require(response["ErrorCode"] == 1 and response["Response"]["version"] == VERSION
            and response["Response"]["jsonWorldComponentContentPaths"]["en"]["DestinyInventoryItemDefinition"] == ipath
            and response["Response"]["jsonWorldComponentContentPaths"]["en"]["DestinyPlugSetDefinition"] == ppath,
            "Same pinned inventory/plugset manifest")
    provenance = data["art/weapons/w40/provenance.json"]
    require(provenance["manifest"] == {"version": VERSION, "path": ipath}
            and provenance["cachedInventorySha256"] == PINS["inventory"], "Selected provenance")
    same_name = {i["hash"] for i in inv.values() if i.get("displayProperties", {}).get("name") == "Stats for All"}
    require(same_name == {BASE, ENHANCED}, "Review unknown same-name copy")
    definitions = []
    for h in sorted(same_name):
        item = inv[str(h)]
        require(item["hash"] == h and item["itemType"] == 19 and not item["redacted"]
                and not item["blacklisted"] and not item["plug"]["isDummyPlug"]
                and item["itemTypeDisplayName"] == ("Trait" if h == BASE else "Enhanced Trait"),
                "Base/enhanced definition")
        definitions.append({"hash": h, "description": item["displayProperties"]["description"],
                            "accepted": h == BASE, "reason": "EXACT_BASE" if h == BASE else "ENHANCED_EXCLUDED"})
    rows, proofs, scans, excluded, direct = [], [], [], [], []
    for w in selected:
        item = inv[str(w["bungieHash"])]
        require(item["hash"] == w["bungieHash"] and item["itemType"] == 3 and not item["redacted"]
                and not item["blacklisted"] and (item["inventory"]["tierType"] == 6) == w["exotic"],
                "Official selected identity")
        if not w["exotic"]:
            require({k: v["value"] for k, v in item["stats"]["stats"].items()} == w["stats"], "Official selected stats")
        sockets = item.get("sockets", {})
        traits = {n for c in sockets.get("socketCategories", []) if c["socketCategoryHash"] == TRAIT_CATEGORY
                  for n in c["socketIndexes"]}
        scan = {"id": w["id"], "hash": item["hash"], "exotic": w["exotic"],
                "traitSocketIndexes": sorted(traits), "scannedSocketCount": len(sockets.get("socketEntries", [])),
                "referencedPools": []}
        for index, socket in enumerate(sockets.get("socketEntries", [])):
            hashes = {socket["singleInitialItemHash"], *[p["plugItemHash"] for p in socket.get("reusablePlugItems", [])]}
            direct.extend({"id": w["id"], "socket": index, "perkHash": h,
                           "policy": "DIRECT_REFERENCE_ALONE_DOES_NOT_AUTHORIZE"} for h in sorted(hashes & same_name))
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                ph = socket.get(field)
                if not ph:
                    continue
                pool = pools[str(ph)]
                require(pool["hash"] == ph and not pool["redacted"] and not pool["blacklisted"], "Referenced pool")
                matches = [{"index": n, "item": p} for n, p in enumerate(pool.get("reusablePlugItems", []))
                           if p["plugItemHash"] in same_name]
                scan["referencedPools"].append({"socket": index, "field": field, "plugSetHash": ph,
                                               "isFakePlugSet": pool["isFakePlugSet"], "matchingEntries": matches})
                for match in matches:
                    if not eligible(index, traits, field, pool, match["item"], w["exotic"]):
                        excluded.append({"id": w["id"], "socket": index, "field": field, "plugSetHash": ph,
                                         "isFakePlugSet": pool["isFakePlugSet"], "match": match})
                        continue
                    require(item["inventory"]["tierType"] == 5, "Legendary owner")
                    row = {"id": w["id"], "hash": item["hash"], "socket": index, "perkHash": BASE, "plugSetHash": ph}
                    rows.append(row)
                    proofs.append({**row, "socketCategoryHash": TRAIT_CATEGORY, "socketEntry": socket,
                                   "plugSetField": field, "isFakePlugSet": False, "matchingEntries": [match]})
        scans.append(scan)
    validate_membership(rows)
    base = data["clarity"][str(BASE)]
    text = "\n".join(line.get("text", "") for block in base["descriptions"]["en"] for line in block.get("linesContent", []))
    require(base["hash"] == BASE and base["name"] == "Stats for All" and base["type"] == "Weapon Trait"
            and all(s in text for s in ("3 Separate Enemies within 3 seconds of each, for 10 seconds",
                "35 Handling and Reload Speed", "10 Stability and Range", "5% increased Damage Falloff Distance",
                "0.95x Reload Duration Multiplier", "Buff duration cannot be refreshed.")), "Exact base Clarity mechanics")
    mapping_source = data["art/weapons/w43/extraction.json"]
    mapping = {m["id"]: m for m in mapping_source["entries"]}
    formulas = data["art/weapons/w46/weapon_formulas.json"]
    by_id = {w["id"]: w for w in selected}
    def indexed(file):
        return {r["id"]: r for r in data["src/main/resources/destiny/weapons/" + file]}
    reloads, handling, aim, hip = [indexed(f) for f in ("w46-timing.json", "w58-handling.json", "w44-aim.json", "w43-ballistics.json")]
    require("self.evpp * _x * _x + self.vpp * _x + self.offset" in raw["art/weapons/w46/rs_types.rs"].decode()
            and "let x = x.clamp(0, 100) as f64;" in raw["art/weapons/w46/rs_types.rs"].decode()
            and "self.stow.solve_at(100.0)" in raw["art/weapons/w46/stat_calc.rs"].decode()
            and "out.reload_time *= modifiers.reload_time_scale;" in raw["art/weapons/w46/stat_calc.rs"].decode()
            and "max(2, min(20, math.ceil(ads_seconds * 20)))" in raw["scripts/extract_aim_w44.py"].decode()
            and "max(raw_stow_seconds, floor_seconds)" in raw["scripts/extract_handling_w58.py"].decode(), "Historical solver semantics")
    curves, audit = [], []
    for row in rows:
        id = row["id"]
        stats, m = by_id[id]["stats"], mapping[id]
        category = formulas[m["family"]]["cat"][m["category"]]
        b = {k: v for k, v in hip[id].items() if k != "id"}
        oracle_range = category["range"]
        require(b == {"offsetStart": oracle_range["offset_start"], "vppStart": oracle_range["vpp_start"],
                "offsetEnd": oracle_range["offset_end"], "vppEnd": oracle_range["vpp_end"],
                "floor": oracle_range["floor_percent"], "precision": m["encodedPveCrit"] / 51 + 1.5}, "W43 hip curves")
        c = {"id": id, "baseReloadStat": stats["4188031367"], "baseHandlingStat": stats["943549884"],
             "baseRangeStat": stats.get("1240592695"), "ballistics": b}
        for key, source in {"reload": category["reload"], **category["handling"]}.items():
            require(set(source) <= {"evpp", "vpp", "offset", "ammo_percent"}, "Unexpected source curve")
            c[key] = {k: source.get(k, 0.0) for k in ("evpp", "vpp", "offset")}
        t, h, a = reloads[id]["timing"], handling[id]["profile"], aim[id]["profile"]
        require(t["supported"] and h["supported"] and not t["shellReload"]
                and t["reloadInitialTicks"] is None and t["reloadPerRoundTicks"] is None, "Whole magazine topology")
        baseline = {"reloadTicks": t["reloadTicks"], "readyTicks": h["readyTicks"], "stowTicks": h["stowTicks"], "adsTicks": a["transitionTicks"]}
        require(evaluate(c) == baseline, "Reproduce W46/W58/W44 baseline " + id)
        active = evaluate(c, 35, .95)
        require(all(active[k] <= baseline[k] for k in baseline), "Buff cannot slow baseline")
        curves.append(c)
        audit.append({"id": id, "mapping": m, "baseline": baseline, "activeSfa": active,
                      "baselineHip": ballistics(c, False), "activeHip": ballistics(c, True),
                      "shellReload": False, "reloadPerRoundTicks": None, "reloadInitialTicks": None})
    # Prove the two requested co-selections against the same official pools and existing profiles.
    pairs = []
    for id, perk, hash_, pool_hash, profile in (
        ("retrofit_escapade", "frenzy", 4104185692, 2461260598, "w172-frenzy.json"),
        ("ammit_ar2", "adrenaline_junkie", 11612903, 560115158, "w173-adrenaline-junkie.json")):
        owner = next(r for r in rows if r["id"] == id)
        item = inv[str(owner["hash"])]
        socket = item["sockets"]["socketEntries"][4]
        traits = {n for c in item["sockets"]["socketCategories"] if c["socketCategoryHash"] == TRAIT_CATEGORY for n in c["socketIndexes"]}
        pool = pools[str(pool_hash)]
        require(socket["randomizedPlugSetHash"] == pool_hash and pool["hash"] == pool_hash
                and not pool["redacted"] and not pool["blacklisted"] and owner["socket"] != 4, "Distinct valid pair sockets")
        matches = [{"index": i, "item": p} for i, p in enumerate(pool["reusablePlugItems"])
                   if eligible(4, traits, "randomizedPlugSetHash", pool, p, False, hash_)]
        roll = {"id": id, "hash": owner["hash"], "socket": 4, "perkHash": hash_, "plugSetHash": pool_hash}
        require(len(matches) == 1 and roll in data["src/main/resources/destiny/weapons/" + profile]["weapons"], "Exact paired base roll")
        pairs.append({"sfa": owner, "otherPerk": perk, "otherRoll": roll, "socketEntry": socket, "matches": matches})
    snapshot = data["src/main/resources/destiny/weapons/w68-snapshot.json"]
    require(not {r["id"] for r in rows} & {r["id"] for r in snapshot["rolls"]}, "Unexpected Snapshot eligibility")
    # Re-scan every selected SFA owner's trait pools so absence is official, not only W68.
    require(not any(eligible(i, {3, 4}, "randomizedPlugSetHash", pools[str(s["randomizedPlugSetHash"])], p, False, 957782887)
            for row in rows for i, s in enumerate(inv[str(row["hash"])]["sockets"]["socketEntries"])
            if s.get("randomizedPlugSetHash") for p in pools[str(s["randomizedPlugSetHash"])]["reusablePlugItems"]), "Official Snapshot intersection nonempty")
    resource = {"stage": "W176", "perk": PERK, "policies": POLICIES, "weapons": rows, "curves": curves}
    validate_resource(resource, curves)
    limitations = [
        "Bungie manifest 245114.26.10.13.2000-1-bnet.66137 establishes exact base legendary randomized trait sockets; base1583705720 accepted; enhanced1409206216 excluded.",
        "Clarity at pinned039cfbc establishes distinct3 hits,3s per new target,10s nonrefresh,+35handling/reload,+10stability/range,1.05falloff,.95reload. Exact tick boundaries, duplicate handling, no collection while active and clock rejection are local discrete policy.",
        "Stow/reload preserve local cycle deadlines with time continuing; this is NOT proven by pinned SFA text. Master identity sessions own lifecycle and cleanup.",
        "Oracle May20 2026 curves are historical community estimates, separate from Bungie Oct13 membership. Reproduces all four existing W46/W58/W44 baselines; not current official animation measurements.",
        "Bonus arguments are TOTALS including SFA; clamp base+total to0..100 before raw curves, apply total reload scalar product once, then ceil20 once. No automatic+35 or extra .95. Combined stat/bonus behavior is local composition, not measured joint Destiny behavior.",
        "W43 hip: active+10Range cap100, then1.05 to both endpoints; floor/precision unchanged. Master applies W44ADS distance scalar afterward. Dimensional has no Range stat and a999/999.9 sentinel: return neutral sentinel; no projectile distance or blast radius invention.",
        "No compatible Snapshot among selected4; snapshotEntering=true fails explicitly rather than inventing a Heavy scalar or unsupported joint effect. false covers ordinary entry and exit.",
        "SFA+Frenzy Retrofit and SFA+AJ Ammit exact distinct sockets proven; activating shot ordering, combined runtime, stability consumption, shared registry/gate and all native/CU remain master-owned. No native/runtime was launched by this worker.",
    ]
    sockets = {"stage": "W176", "selectedCount": 65, "supportedCount": 4, "randomizedCount": 4, "fixedCuratedCount": 0,
               "scanner": "Pinned W174 identical predicate: real randomized trait pool, exact base, currentlyCanRoll=true; weight0 accepted; no reusable/direct/fake/exotic authorization.",
               "perkDefinitions": definitions, "weapons": proofs, "selectedScan": scans,
               "excludedReferences": excluded, "directReferences": direct, "compatiblePairs": pairs,
               "snapshotIntersection": [], "unsupportedSelectedIds": [w["id"] for w in selected if w["id"] not in {r["id"] for r in rows}]}
    clarity = {"stage": "W176", "repository": "https://github.com/Database-Clarity/Live-Clarity-Database",
               "commit": COMMIT, "url": f"https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/{COMMIT}/descriptions/clarity.json",
               "sourceSha256": PINS["clarity"], "base": base, "enhancedExcludedHash": ENHANCED,
               "enhancedExcluded": data["clarity"][str(ENHANCED)], "verifiedMechanics": PERK,
               "localPolicies": POLICIES, "limitations": limitations}
    outputs = {TARGET: resource, ART + "official-sockets.json": sockets, ART + "clarity-source.json": clarity}
    outputs[ART + "manifest.json"] = {"stage": "W176", "selectedCount": 65, "supportedCount": 4,
        "manifestVersion": VERSION, "inventoryUrl": "https://www.bungie.net" + ipath, "plugSetsUrl": "https://www.bungie.net" + ppath,
        "sourcePins": pins, "generator": SCRIPT, "generatorSha256": digest((root / SCRIPT).read_bytes()),
        "outputSha256": {p: digest(encoded(v)) for p, v in outputs.items()},
        "timingProvenance": {k: mapping_source[k] for k in ("repository", "commit", "commitDate", "source")},
        "licenses": ["art/weapons/w46/MIT-LICENSE", "art/weapons/w46/UNLICENSE"], "audit": audit,
        "compatiblePairs": pairs, "reproduce": "rtk proxy python3 " + SCRIPT + " --verify --self-test", "limitations": limitations}
    return outputs, paths


def self_test(outputs):
    original = outputs[TARGET]
    rejected = []
    def rejects(name, f):
        try:
            f()
        except (ValueError, KeyError, TypeError):
            rejected.append(name)
            return
        raise ValueError("Accepted negative case: " + name)
    for key in PINS:
        require(digest(b"mutated") != PINS[key], "Invalid pin")
    cases = [lambda r: r.update(stage="W175"), lambda r: r["perk"].update(hash=ENHANCED),
             lambda r: r["perk"].update(durationTicks=220), lambda r: r["perk"].update(refresh=True),
             lambda r: r["perk"].update(reloadScalar=1), lambda r: r["policies"].update(stowReload="SOURCE_PROVEN"),
             lambda r: r["weapons"].pop(), lambda r: r["weapons"].append(r["weapons"][0]),
             lambda r: r["weapons"][0].update(socket=4), lambda r: r["weapons"][0].update(plugSetHash=1),
             lambda r: r["curves"][0].update(baseRangeStat=100),
             lambda r: r["curves"][0]["reload"].update(offset=float("nan"))]
    for i, edit in enumerate(cases):
        bad = copy.deepcopy(original)
        edit(bad)
        rejects("resource mutation " + str(i), lambda: validate_resource(bad, original["curves"]))
    pool, match = {"isFakePlugSet": False}, {"plugItemHash": BASE, "currentlyCanRoll": True, "weight": 0}
    require(eligible(3, {3}, "randomizedPlugSetHash", pool, match, False), "Weight0 eligibility")
    for name, idx, traits, field, p, m, exotic in (
        ("fake", 3, {3}, "randomizedPlugSetHash", {"isFakePlugSet": True}, match, False),
        ("reusable", 3, {3}, "reusablePlugSetHash", pool, match, False),
        ("nontrait", 3, {4}, "randomizedPlugSetHash", pool, match, False),
        ("exotic", 3, {3}, "randomizedPlugSetHash", pool, match, True),
        ("enhanced", 3, {3}, "randomizedPlugSetHash", pool, {**match, "plugItemHash": ENHANCED}, False),
        ("unrollable", 3, {3}, "randomizedPlugSetHash", pool, {**match, "currentlyCanRoll": False}, False),
        ("missing rollability", 3, {3}, "randomizedPlugSetHash", pool, {"plugItemHash": BASE}, False)):
        require(not eligible(idx, traits, field, p, m, exotic), "Accepted " + name)
        rejected.append(name)
    c = original["curves"][0]
    for value in (0, -1, 1.01, float("nan"), float("inf")):
        rejects("unsafe scalar " + str(value), lambda: evaluate(c, 35, value))
    require(evaluate(c, 2**31-1) == evaluate(c, 100), "Positive overflow safe cap")
    require(evaluate(c, -2**31) == evaluate(c, -100), "Negative overflow safe cap")
    require(math.ceil(1.255 * .95 * 20) != math.ceil(math.ceil(1.255 * 20) * .95), "Single ceil regression witness")
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    parser.add_argument("--shared-sources-dir", type=Path, default=Path("/tmp/destiny-weapons-w60"))
    parser.add_argument("--clarity", type=Path, default=Path("/private/tmp/w167-clarity.json"))
    args = parser.parse_args()
    try:
        require(not (args.verify and args.output_root), "--verify cannot write --output-root")
        outputs, paths = generate(args)
        rejected = self_test(outputs) if args.self_test else []
        if args.self_test:
            repeated, _ = generate(args)
            require({k: encoded(v) for k, v in outputs.items()} == {k: encoded(v) for k, v in repeated.items()}, "Nondeterministic output")
        destination = (args.output_root or args.root).resolve()
        inputs = {p.resolve() for p in paths.values()} | {(args.root / SCRIPT).resolve()}
        for relative, value in outputs.items():
            target = (destination / relative).resolve()
            require(target.is_relative_to(destination) and target not in inputs, "Output aliases source/escapes root")
            content = encoded(value)
            if args.verify:
                require(target.read_bytes() == content, "Generated bytes differ: " + relative)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
        print(json.dumps({"stage": "W176", "status": "VERIFY_PASS" if args.verify else "GENERATED", "supported": 4,
                          "deterministicRepeat": args.self_test, "negativeCasesRejected": rejected, "outputs": list(outputs)}, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("W176 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
