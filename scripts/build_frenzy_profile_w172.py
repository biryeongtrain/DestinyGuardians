#!/usr/bin/env python3
"""Offline exact-selected65 base Frenzy profile; --verify writes nothing.

All consumed inputs are pinned. Only five owned JSON outputs are written.
--self-test mutates memory only. Audited W171 socket scanner and W170 stat-curve provenance; no runtime claims.
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
SCRIPT = "scripts/build_frenzy_profile_w172.py"
ART = "art/weapons/w172/frenzy/"
TARGET = "src/main/resources/destiny/weapons/w172-frenzy.json"
BASE, ENHANCED = 4104185692, 3007133316
OTHER_COPIES = set()
TRAIT_CATEGORY = 4241085061
COMMIT = "039cfbc4732c33573568b28cc6335dd3332a9296"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
EXPECTED = {
    ("austringer", 3055790362, 4, 785215120),
    ("allied_demand", 1532276803, 4, 703779397),
    ("farewell", 541188001, 4, 3819615926),
    ("brass_attacks", 2121785039, 4, 3403850295),
    ("dream_breaker", 2931957300, 4, 1206254527),
    ("stormchaser", 3652506829, 4, 4213354588),
    ("retraced_path", 548958835, 4, 398391969),
    ("code_duello", 2496242052, 4, 147528717),
    ("retrofit_escapade", 3103325054, 4, 2461260598),
    ("nezarec_s_whisper", 254636484, 4, 699056095),
}
PERK = {"id": "frenzy", "hash": BASE, "activationTicks": 240, "combatGraceTicks": 100,
        "durationTicks": 144, "damageMultiplier": 1.15, "handlingBonus": 100,
        "reloadBonus": 100, "worksStowed": True,
        "refreshOnDealtDamage": True, "refreshOnReceivedDamage": True,
        "selfDamageCounts": False, "environmentalDamageCounts": False}
POLICIES = {
    "statCap": 100, "durationMultiplier": 1.0,
    "rounding": "CEIL_SECONDS_TIMES_20_ONCE",
    "adsBounds": "CLAMP_TICKS_2_20_W44",
    "glaiveAds": "W44_UNSUPPORTED_NEUTRAL_2_TICKS_ZERO_ORACLE_CURVE",
    "handlingBounds": "W58_NO_EXTRA_TICK_CLAMP_STOW_AT_100_FLOOR",
    "combatDefinition": "DEALT_OR_RECEIVED_DAMAGE_WITHIN_LAST_5_SECONDS",
    "sourceDamageAttribution": "MASTER_OWNED_LOCAL_POLICY",
    "sourceCombinedPerks": "UNKNOWN_MASTER_OWNED_LOCAL_POLICY",
    "cycleIntegration": "MASTER_OWNED_LOCAL_POLICY",
    "snapshotComposition": "W68_ENTRY_SCALAR_AFTER_FRENZY_STAT100_BEFORE_SINGLE_CEIL_CLAMP1_20",
}
PINS = {
    'art/weapons/w68/references/mechanics.json': 'eee2abee2a74e55f785fcc1fcc923e3159c95604165ed53ad915c57f570f8245',
    'scripts/extract_snapshot_w68.py': '13b265aca2db03f4e3e417a5911ffb36292c6b74b1475fa193223187471fa4a2',
    'src/main/resources/destiny/weapons/w68-snapshot.json': '7e824633be32953e6c75d3d856ce765223fbb1cbcc3b01affca3d83eb8fcb738',
    'art/weapons/w170/perpetual-motion/timings.json': 'be88e1fa8c09b989058d4e07b3e3123d28c744f763b7fe884662da239dd518b4',
    'scripts/build_perpetual_motion_profile_w170.py': '4b30cb849e91d7afd48146e184405370e150f7623de3836ba1366beaec1ef678',
    'scripts/build_tap_the_trigger_profile_w171.py': '9404bc9f7de01dd20cdbfab4d1bbb68599ced7047d553c259529a4baddf0d4b1',
    "src/main/resources/destiny/weapons/w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    "src/main/resources/destiny/weapons/w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "src/main/resources/destiny/weapons/w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    "src/main/resources/destiny/weapons/w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "art/weapons/w40/provenance.json": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "art/weapons/w43/extraction.json": "a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5",
    "art/weapons/w46/weapon_formulas.json": "fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d",
    "art/weapons/w46/stat_calc.rs": "5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2",
    "art/weapons/w46/rs_types.rs": "faa476e6589d2362cf9ee8dd948410adfa7fa8507e8809f3cd10bb13ebba9b90",
    "src/main/resources/destiny/weapons/w46-timing.json": "e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "clarity": "881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
    "src/main/resources/destiny/weapons/w44-aim.json": "0d0a38469c28a74c1a77489d346184eccef347a604c0c0c455d1c7c2e1a80fc8",
    "src/main/resources/destiny/weapons/w58-handling.json": "4de7d346a93c822784fafa69b62ac66148d51cc11cf2da6706367682b414d3f1",
    "art/weapons/w44/extraction.json": "6a82eb21264ffab1e897cf9b0a74ad0cef0c252b129438f2938d82414a7da9fc",
    "art/weapons/w58/extraction.json": "934511861839eb1fa5b60ea1cc0d5a9ad5e133a08ac1ee8d567a431044e7063d",
    "scripts/extract_aim_w44.py": "0c1160b2a846165dad7820fa1a085198a7a51650312d78fdabdbe4ff3b492ea6",
    "scripts/extract_handling_w58.py": "177981eb79edd79bb2c4c1e80618183ac2156ddfe5106e93fa70d69786b9b934",
    "art/weapons/w46/MIT-LICENSE": "50173139375c53459837abdeb7ad9f264eba4f0bc2bb2c676932991ce158778d",
    "art/weapons/w46/UNLICENSE": "6b0382b16279f26ff69014300541967a356a666eb0b91b422f6862f6b7dad17e",
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


def eligible(socket_index, trait_indexes, field, pool, match, exotic, perk_hash=BASE):
    return (not exotic and socket_index in trait_indexes and field == "randomizedPlugSetHash"
            and not pool["isFakePlugSet"] and match["plugItemHash"] == perk_hash
            and match.get("currentlyCanRoll") is True)


def validate_membership(rows):
    keys = [(r["id"], r["hash"], r["socket"], r["plugSetHash"]) for r in rows]
    require(len(keys) == len(set(keys)) == len(EXPECTED) and set(keys) == EXPECTED
            and all(r["perkHash"] == BASE for r in rows), "Exact selected socket membership changed")


def solve(curve, stat):
    require(set(curve) <= {"evpp", "vpp", "offset", "ammo_percent"} and "offset" in curve,
            "Unknown curve fields")
    require(all(type(v) in (int, float) and math.isfinite(v) for v in curve.values()), "Nonfinite coefficient")
    return curve.get("evpp", 0) * stat * stat + curve.get("vpp", 0) * stat + curve["offset"]


def evaluate(curves, reload_stat, handling_stat, active, neutral_ads=False):
    require(type(active) is bool, "Invalid activation")
    require(type(reload_stat) is int and type(handling_stat) is int, "Invalid stats")
    bonus = 100 if active else 0
    reload = min(100, max(0, reload_stat + bonus))
    handling = min(100, max(0, handling_stat + bonus))
    seconds = {"reload": solve(curves["reload"], reload),
               "ready": solve(curves["ready"], handling),
               "stow": max(solve(curves["stow"], handling), solve(curves["stow"], 100)),
               "ads": solve(curves["ads"], handling)}
    require(not neutral_ads or seconds["ads"] == 0, "Neutral ADS requires exact zero curve")
    require(all(math.isfinite(v) and (v == 0 if k == "ads" and neutral_ads else 0 < v <= 60)
                for k, v in seconds.items()), "Unsafe duration")
    ticks = {k + "Ticks": (max(2, min(20, math.ceil(v * 20))) if k == "ads" else math.ceil(v * 20))
             for k, v in seconds.items()}
    return {"effectiveReloadStat": reload, "effectiveHandlingStat": handling, "seconds": seconds, **ticks}


def snapshot_ticks(seconds, scalar):
    require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= 60,
            "Unsafe Snapshot ADS seconds")
    require(scalar in (.5, .8), "No measured Snapshot scalar")
    return max(1, min(20, math.ceil(seconds * scalar * 20)))


def snapshot_intersection(rows, inv, pools, selected, curves, w68):
    require(w68["perkHash"] == 957782887 and w68["primaryScalar"] == .5
            and w68["specialScalar"] == .8, "W68 scalar policy changed")
    snapshot_by_id = {r["id"]: r for r in w68["rolls"]}
    result, proofs = [], []
    for row in rows:
        item = inv[str(row["hash"])]
        sockets = item["sockets"]
        traits = {n for c in sockets["socketCategories"] if c["socketCategoryHash"] == TRAIT_CATEGORY
                  for n in c["socketIndexes"]}
        for n, socket in enumerate(sockets["socketEntries"]):
            ph = socket.get("randomizedPlugSetHash")
            if not ph:
                continue
            pool = pools[str(ph)]
            for index, match in enumerate(pool["reusablePlugItems"]):
                if not eligible(n, traits, "randomizedPlugSetHash", pool, match, selected[row["id"]]["exotic"], 957782887):
                    continue
                require(n != row["socket"], "Snapshot and Frenzy share socket; cannot coexist")
                snapshot = {"id": row["id"], "hash": row["hash"], "socket": n,
                            "perkHash": 957782887, "plugSetHash": ph}
                require(snapshot_by_id.get(row["id"]) == snapshot, "Official Snapshot intersection differs from W68")
                ammo = item["equippingBlock"]["ammoType"]
                require(selected[row["id"]]["ammo"] == {1: "PRIMARY", 2: "SPECIAL", 3: "HEAVY"}[ammo], "Official ammo enum mismatch")
                require(ammo in (1, 2), "No measured Heavy Snapshot scalar")
                scalar = .5 if ammo == 1 else .8
                curve = next(c for c in curves if c["id"] == row["id"])
                require(not curve["neutralAds"], "No Snapshot on neutral ADS")
                seconds = solve(curve["ads"], 100)
                result.append({"id": row["id"], "frenzySocket": row["socket"], "snapshotSocket": n,
                    "snapshotPlugSetHash": ph, "perkHash": 957782887, "ammoType": ammo,
                    "scalar": scalar, "adsSeconds": seconds, "adsTicks": snapshot_ticks(seconds, scalar)})
                proofs.append({**snapshot, "frenzySocket": row["socket"], "socketCategoryHash": TRAIT_CATEGORY,
                    "socketEntry": socket, "plugSetField": "randomizedPlugSetHash", "isFakePlugSet": pool["isFakePlugSet"],
                    "matchingEntry": {"index": index, "item": match}})
    require({(r["id"], r["frenzySocket"], r["snapshotSocket"], r["snapshotPlugSetHash"]) for r in result}
            == {("austringer", 4, 3, 2750499928), ("dream_breaker", 4, 3, 3785896921)}
            and len(result) == 2, "Exact distinct-socket Snapshot intersection changed")
    return result, proofs


def generate(args):
    root = args.root.resolve()
    paths = {p: root / p for p in PINS if "/" in p}
    paths.update(inventory=args.inventory, plugSets=args.shared_sources_dir / "bungie-plugsets.json",
                 manifest=args.shared_sources_dir / "manifest.json", clarity=args.clarity)
    data, pins, raw = {}, {}, {}
    for key, path in paths.items():
        value = path.read_bytes()
        check_pin(key, value)
        raw[key] = value
        pins[key] = {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                     "sha256": digest(value), "bytes": len(value)}
        if key.endswith(".json") or key in ("inventory", "plugSets", "manifest", "clarity"):
            data[key] = json.loads(value)
    catalog = data["src/main/resources/destiny/weapons/w30.json"][:]
    selected = data["src/main/resources/destiny/weapons/w40-characteristics.json"][:]
    for f in ("w83-exotics.json", "w84-exotics.json"):
        for row in data["src/main/resources/destiny/weapons/" + f]:
            catalog.append(row["catalog"])
            selected.append(row["characteristics"])
    require(len(selected) == len(catalog) == len({w["id"] for w in selected})
            == len({w["bungieHash"] for w in selected}) == 65, "Expected selected65")
    require({w["id"] for w in catalog} == {w["id"] for w in selected}, "Selected ID mismatch")
    families = {w["id"]: w["family"] for w in catalog}
    inv, pools = data["inventory"], data["plugSets"]
    response = data["manifest"]
    require(response["ErrorCode"] == 1, "Official manifest failed")
    manifest = response["Response"]
    ipath = "/common/destiny2_content/json/en/DestinyInventoryItemDefinition-" + SUFFIX
    ppath = ipath.replace("DestinyInventoryItemDefinition-", "DestinyPlugSetDefinition-")
    require(manifest["version"] == VERSION
            and manifest["jsonWorldComponentContentPaths"]["en"]["DestinyInventoryItemDefinition"] == ipath
            and manifest["jsonWorldComponentContentPaths"]["en"]["DestinyPlugSetDefinition"] == ppath,
            "Inventory/plug sets must share exact pinned manifest")
    provenance = data["art/weapons/w40/provenance.json"]
    require(provenance["manifest"] == {"version": VERSION, "path": ipath}
            and provenance["cachedInventorySha256"] == PINS["inventory"], "Official selection provenance")
    same_name = {i["hash"] for i in inv.values() if i.get("displayProperties", {}).get("name") == "Frenzy"}
    require(same_name == {BASE, ENHANCED} | OTHER_COPIES, "Review unknown same-name copy")
    definitions = []
    for h in sorted(same_name):
        item = inv[str(h)]
        require(item["hash"] == h and not item["redacted"] and not item["blacklisted"], "Invalid perk definition")
        if h in (BASE, ENHANCED):
            require(item["itemType"] == 19 and not item["plug"]["isDummyPlug"]
                    and item["itemTypeDisplayName"] == ("Trait" if h == BASE else "Enhanced Trait"),
                    "Wrong base/enhanced definition")
        definitions.append({"hash": h, "itemType": item["itemType"], "itemTypeDisplayName": item["itemTypeDisplayName"],
            "description": item["displayProperties"]["description"], "accepted": h == BASE,
            "reason": "EXACT_BASE" if h == BASE else "ENHANCED_EXCLUDED" if h == ENHANCED else "OTHER_HASH_EXCLUDED"})
    rows, proofs, scans, excluded, direct = [], [], [], [], []
    for w in selected:
        item = inv[str(w["bungieHash"])]
        require(item["hash"] == w["bungieHash"] and item["itemType"] == 3
                and not item["redacted"] and not item["blacklisted"]
                and (w["exotic"] or {k: v["value"] for k, v in item["stats"]["stats"].items()} == w["stats"])
                and (item["inventory"]["tierType"] == 6) == w["exotic"], "Official selected metadata mismatch")
        sockets = item.get("sockets", {})
        traits = {i for c in sockets.get("socketCategories", [])
                  if c["socketCategoryHash"] == TRAIT_CATEGORY for i in c["socketIndexes"]}
        scan = {"id": w["id"], "hash": item["hash"], "exotic": w["exotic"],
                "traitSocketIndexes": sorted(traits), "scannedSocketCount": len(sockets.get("socketEntries", [])),
                "runtimeStatDifferences": {k: {"official": item["stats"]["stats"].get(k, {}).get("value"), "runtime": v}
                    for k, v in w["stats"].items() if item["stats"]["stats"].get(k, {}).get("value") != v},
                "referencedPools": []}
        for index, socket in enumerate(sockets.get("socketEntries", [])):
            direct_hashes = {socket["singleInitialItemHash"], *[p["plugItemHash"] for p in socket.get("reusablePlugItems", [])]}
            for h in sorted(direct_hashes & same_name):
                direct.append({"id": w["id"], "socket": index, "perkHash": h,
                               "policy": "DIRECT_REFERENCE_ALONE_DOES_NOT_PROVE_ROLLABILITY"})
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                ph = socket.get(field)
                if not ph:
                    continue
                pool = pools[str(ph)]
                require(pool["hash"] == ph and not pool["redacted"] and not pool["blacklisted"], "Invalid referenced pool")
                matches = [{"index": n, "item": p} for n, p in enumerate(pool.get("reusablePlugItems", []))
                           if p["plugItemHash"] in same_name]
                scan["referencedPools"].append({"socket": index, "field": field, "plugSetHash": ph,
                    "isFakePlugSet": pool["isFakePlugSet"], "matchingEntries": matches})
                for match in matches:
                    p = match["item"]
                    if not eligible(index, traits, field, pool, p, w["exotic"]):
                        excluded.append({"id": w["id"], "socket": index, "field": field, "plugSetHash": ph,
                                         "isFakePlugSet": pool["isFakePlugSet"], "match": match})
                        continue
                    require(item["inventory"]["tierType"] == 5, "Expected legendary trait owner")
                    row = {"id": w["id"], "hash": item["hash"], "socket": index, "perkHash": BASE, "plugSetHash": ph}
                    rows.append(row)
                    proofs.append({**row, "selection": "randomized", "socketCategoryHash": TRAIT_CATEGORY,
                        "socketEntry": socket, "plugSetField": field, "isFakePlugSet": pool["isFakePlugSet"],
                        "matchingEntries": [match]})
        scans.append(scan)
    validate_membership(rows)
    base = data["clarity"][str(BASE)]
    text = "\n".join(line.get("text", "") for block in base["descriptions"]["en"] for line in block.get("linesContent", []))
    require(base["hash"] == BASE and base["type"] == "Weapon Trait" and base["name"] == "Frenzy"
            and all(fragment in text for fragment in (
                "After being in Combat for 12 seconds:",
                "Grants 15% increased damage, 100 Handling, and 100 Reload Speed for 7.2 seconds.",
                "Works and can activate while stowed. Dealing and receiving damage refreshes the buff duration.",
                "having either dealt or received damage within the last 5 seconds.",
                "Self-damage and environmental damage do not count.")),
            "Exact Clarity base mechanics not established")
    mapping_source = data["art/weapons/w43/extraction.json"]
    mapping = {m["id"]: m for m in mapping_source["entries"]}
    formulas = data["art/weapons/w46/weapon_formulas.json"]
    by_id = {w["id"]: w for w in selected}
    baselines = {}
    for filename, field in (("w46-timing.json", "timing"), ("w44-aim.json", "profile"), ("w58-handling.json", "profile")):
        baselines[filename] = {r["id"]: r[field] for r in data["src/main/resources/destiny/weapons/" + filename]}
    calc = " ".join(raw["art/weapons/w46/stat_calc.rs"].decode().split())
    types = raw["art/weapons/w46/rs_types.rs"].decode()
    require("self.evpp * _x * _x + self.vpp * _x + self.offset" in types
            and "let x = x.clamp(0, 100) as f64;" in types
            and all(s in calc for s in (
                "reload_time = self.reload_data.solve_at(_reload_stat as f64)",
                "out.reload_time *= modifiers.reload_time_scale;",
                "self.ready.solve_at_i(handling_stat + _modifiers.draw_add) * _modifiers.draw_scale",
                "self.stow.solve_at(100.0)",
                "self.ads.solve_at_i(handling_stat + _modifiers.ads_add) * _modifiers.ads_scale")),
            "Pinned Oracle solver semantics changed")
    require("max(2, min(20, math.ceil(ads_seconds * 20)))" in raw["scripts/extract_aim_w44.py"].decode()
            and "max(raw_stow_seconds, floor_seconds)" in raw["scripts/extract_handling_w58.py"].decode(),
            "Existing W44/W58 bounds changed")
    curves, plans, audits = [], [], []
    for row in rows:
        id = row["id"]
        w, m = by_id[id], mapping[id]
        category = formulas[m["family"]]["cat"][m["category"]]
        c = {"reload": category["reload"], **category["handling"]}
        require(set(c) == {"reload", "ready", "stow", "ads"}, "Unreviewed timing fields")
        stats = w["stats"]
        reload, handling = (stats[k] for k in ("4188031367", "943549884"))
        require(all(type(v) is int and 0 <= v <= 100 for v in (reload, handling)), "Invalid official stats")
        neutral_ads = families[id] == "glaive"
        baseline = evaluate(c, reload, handling, False, neutral_ads)
        prior_reload, prior_handling, prior_aim = (baselines[f][id] for f in ("w46-timing.json", "w58-handling.json", "w44-aim.json"))
        require(prior_reload["supported"] and not prior_reload["shellReload"]
                and prior_reload["reloadInitialTicks"] is None and prior_handling["supported"]
                and baseline["reloadTicks"] == prior_reload["reloadTicks"]
                and baseline["readyTicks"] == prior_handling["readyTicks"]
                and baseline["stowTicks"] == prior_handling["stowTicks"]
                and baseline["adsTicks"] == prior_aim["transitionTicks"], "Cannot reproduce all four base timings: " + id)
        curves.append({"id": id, "baseReloadStat": reload, "baseHandlingStat": handling,
                       "neutralAds": neutral_ads, **c})
        result = evaluate(c, reload, handling, True, neutral_ads)
        plan = {"id": id, **{k: result[k] for k in ("reloadTicks", "readyTicks", "stowTicks", "adsTicks")},
                "shellReload": False, "reloadPerRoundTicks": None, "reloadInitialTicks": None,
                "reloadPlanKind": "WHOLE_MAGAZINE", "adsSupported": not neutral_ads}
        require(all(plan[k] <= baseline[k] for k in ("reloadTicks", "readyTicks", "stowTicks", "adsTicks")), "Buff slows baseline")
        plans.append(plan)
        audits.append({"id": id, "hash": row["hash"], "family": m["family"], "category": m["category"],
                       "curves": c, "baseReloadStat": reload, "baseHandlingStat": handling,
                       "baseline": baseline, "modified": {**plan, **result},
                       "unsupportedEvidence": (["W44 explicitly excludes glaive ADS; zero Oracle ADS curve; retain neutral2ticks. Reload/ready/stow supported."] if neutral_ads else [])})
    w68 = data["src/main/resources/destiny/weapons/w68-snapshot.json"]
    mechanics = data["art/weapons/w68/references/mechanics.json"]
    require(mechanics["serverPolicy"]["primaryScalar"] == .5
            and mechanics["serverPolicy"]["specialScalar"] == .8, "W68 measured-modern server choice")
    snapshot_ads, snapshot_proofs = snapshot_intersection(rows, inv, pools, by_id, curves, w68)
    limitations = [
        "Bungie Oct13 manifest and Oracle May20 curves are separate pinned snapshots. Community timings are historical approximations, not exact official animation measurements.",
        "Clarity combat12s, damage15percent, handling/reload+100, buff7.2s, stowed activation, damage refresh and combat5s definition are source mechanics. Runtime attribution and cycle integration are master-owned local policies.",
        "Stats clamp0..100, duration scalar1, stow-at100 floor, W44 ADS2..20ticks, no extra ready/stow clamp, ceil seconds*20 once.",
        "Nezarec glaive ADS unsupported by W44: exact zero Oracle curve maps to existing neutral2ticks; no ADS improvement claimed. All10 eligible weapons retained.",
        "No eligible shell reload or sword. Each plan explicitly includes shellReload=false, reloadPerRoundTicks=null, reloadInitialTicks=null; unexpected topology fails instead of dropping membership.",
        "Snapshot co-selection is exact only for Austringer and Dream Breaker, socket3 vs Frenzy4. Apply W68 scalar .5/.8 to Frenzy stat100 ADS seconds before one ceil and W68 clamp1..20; entry-only local composition, not a measured joint Destiny effect. W68 historical Special .75 vs selected .8 conflict remains unresolved.",
        "Other combined perks, armor, masterworks, combat runtime, native Vision and final gates are master-owned. Enhanced Frenzy is excluded.",
    ]
    resource = {"stage": "W172", "perk": PERK, "policies": POLICIES,
                "weapons": rows, "curves": curves, "timings": plans, "snapshotADS": snapshot_ads}
    sockets = {"stage": "W172", "selectedCount": 65, "supportedCount": len(rows), "randomizedCount": len(rows), "fixedCuratedCount": 0,
               "policy": "Audited W171 scanner: exact base hash in selected legendary trait-category real randomized pool; currentlyCanRoll=true. Weight0 eligible. Reusable/fake/direct/enhanced/exotic references alone do not authorize rolls.",
               "perkDefinitions": definitions, "weapons": proofs, "selectedScan": scans,
               "excludedReferences": excluded, "directReferences": direct, "snapshotIntersection": snapshot_proofs,
               "unsupportedSelectedIds": [w["id"] for w in selected if w["id"] not in {r["id"] for r in rows}]}
    clarity = {"stage": "W172", "repository": "https://github.com/Database-Clarity/Live-Clarity-Database", "commit": COMMIT,
               "url": "https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/" + COMMIT + "/descriptions/clarity.json",
               "sourceSha256": PINS["clarity"], "base": base, "enhancedExcludedHash": ENHANCED,
               "mechanics": PERK, "durationMultiplier": 1.0,
               "sourceDurationMultiplier": "NO_DURATION_SCALAR_SPECIFIED_NEUTRAL_1",
               "policies": POLICIES, "limitations": limitations}
    timings = {"stage": "W172", "repository": mapping_source["repository"], "commit": mapping_source["commit"],
               "commitDate": mapping_source["commitDate"], "source": "build_resources/weapon_formulas.json",
               "licenseSources": ["art/weapons/w46/MIT-LICENSE", "art/weapons/w46/UNLICENSE"],
               "formula": "q(x)=evpp*x*x+vpp*x+offset; x=clamp(baseStat+100,0,100); scalar1; ceil20*q once; stow=max(q(x),q(100)); ADS clamp2..20ticks; glaive W44 neutral2",
               "entries": audits, "timings": plans, "snapshotADS": snapshot_ads,
               "snapshotPolicy": mechanics["serverPolicy"], "snapshotHistoricalConflict": mechanics["historicalOfficialConflict"],
               "limitations": limitations}
    outputs = {TARGET: resource, ART + "official-sockets.json": sockets, ART + "clarity-source.json": clarity,
               ART + "timings.json": timings}
    outputs[ART + "manifest.json"] = {"stage": "W172", "selectedCount": 65, "supportedCount": len(rows), "timingPlans": len(plans),
        "manifestVersion": VERSION, "inventoryUrl": "https://www.bungie.net" + ipath, "plugSetsUrl": "https://www.bungie.net" + ppath,
        "sourcePins": pins, "generator": SCRIPT, "generatorSha256": digest((root / SCRIPT).read_bytes()),
        "outputSha256": {p: digest(encoded(v)) for p, v in outputs.items()},
        "reproduce": "rtk proxy python3 " + SCRIPT + " --verify --self-test", "limitations": limitations}
    return outputs, paths


def self_test(outputs):
    resource = outputs[TARGET]
    rejected = []
    def rejects(name, fn):
        try:
            fn()
        except (ValueError, KeyError, TypeError):
            rejected.append(name)
            return
        raise ValueError("Negative case accepted: " + name)
    rejects("mutated pinned source", lambda: check_pin("clarity", b"mutated"))
    for name, edit in (
        ("missing socket", lambda r: r.pop()), ("duplicate socket", lambda r: r.append(r[0])),
        ("wrong hash", lambda r: r[0].update(hash=1)), ("wrong socket", lambda r: r[0].update(socket=1)),
        ("enhanced trait", lambda r: r[0].update(perkHash=ENHANCED)), ("wrong pool", lambda r: r[0].update(plugSetHash=1))):
        rows = copy.deepcopy(resource["weapons"])
        edit(rows)
        rejects(name, lambda: validate_membership(rows))
    good = {"plugItemHash": BASE, "currentlyCanRoll": True, "weight": 0}
    pool = {"isFakePlugSet": False}
    require(eligible(3, {3}, "randomizedPlugSetHash", pool, good, False), "Weight0 eligible")
    for name, idx, traits, field, p, match, exotic in (
        ("fake", 3, {3}, "randomizedPlugSetHash", {"isFakePlugSet": True}, good, False),
        ("reusable", 3, {3}, "reusablePlugSetHash", pool, good, False),
        ("unrollable", 3, {3}, "randomizedPlugSetHash", pool, {**good, "currentlyCanRoll": False}, False),
        ("missing rollability", 3, {3}, "randomizedPlugSetHash", pool, {"plugItemHash": BASE}, False),
        ("enhanced", 3, {3}, "randomizedPlugSetHash", pool, {**good, "plugItemHash": ENHANCED}, False),
        ("nontrait", 2, {3}, "randomizedPlugSetHash", pool, good, False),
        ("exotic", 3, {3}, "randomizedPlugSetHash", pool, good, True)):
        require(not eligible(idx, traits, field, p, match, exotic), "Accepted " + name)
        rejected.append(name)
    c = resource["curves"][0]
    for value in (float("nan"), float("inf"), -1):
        bad = copy.deepcopy(c)
        bad["ready"]["offset"] = value
        rejects("unsafe curve " + str(value), lambda: evaluate(bad, 50, 50, True))
    require(evaluate(c, 1000, 1000, True) == evaluate(c, 100, 100, True), "Upper stat clamp")
    require(evaluate(c, -1000, -1000, True) == evaluate(c, -100, -100, True), "Lower stat clamp")
    rejects("integer activation", lambda: evaluate(c, 50, 50, 1))
    rejects("false neutral ADS", lambda: evaluate(c, 50, 50, True, True))
    require(len(resource["timings"]) == 10, "Complete timing coverage")
    require([(r["id"], r["adsTicks"]) for r in resource["snapshotADS"]] ==
            [("austringer", 2), ("dream_breaker", 4)], "Combined ADS expectations")
    require(snapshot_ticks(.16, .8) == 3 and math.ceil(math.ceil(.16 * 20) * .8) == 4,
            "Snapshot must precede quantization")
    rejects("Snapshot Heavy scalar", lambda: snapshot_ticks(.2, 1.0))
    rejects("Snapshot NaN seconds", lambda: snapshot_ticks(float("nan"), .5))
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
        outputs, inputs = generate(args)
        rejected = self_test(outputs) if args.self_test else []
        if args.self_test:
            repeated, _ = generate(args)
            require({k: encoded(v) for k, v in outputs.items()} ==
                    {k: encoded(v) for k, v in repeated.items()}, "Nondeterministic generation")
        output_root = (args.output_root or args.root).resolve()
        input_paths = {p.resolve() for p in inputs.values()} | {(args.root / SCRIPT).resolve()}
        for relative, value in outputs.items():
            path = (output_root / relative).resolve()
            require(path.is_relative_to(output_root) and path not in input_paths, "Output aliases input/escapes root")
            content = encoded(value)
            if args.verify:
                require(path.read_bytes() == content, "Generated bytes differ: " + relative)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        print(json.dumps({"stage": "W172", "status": "VERIFY_PASS" if args.verify else "GENERATED",
            "selected": 65, "supported": 10, "timingPlans": 10, "deterministicRepeat": bool(args.self_test), "negativeCasesRejected": rejected,
            "outputs": list(outputs)}, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("W172 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
