#!/usr/bin/env python3
"""Offline exact-selected65 Rapid Hit extraction. --verify writes nothing.

All consumed inputs are SHA256 pinned; no network or game access. Only the five
owned JSON outputs are written. --self-test mutates in-memory copies only.
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
SCRIPT = "scripts/build_rapid_hit_profile_w169.py"
ART = "art/weapons/w169/rapid-hit/"
TARGET = "src/main/resources/destiny/weapons/w169-rapid-hit.json"
BASE, ENHANCED = 247725512, 2938480696
OTHER_COPIES = {3708253562, 2578928835}
TRAIT_CATEGORY = 4241085061
BONUSES = (5, 30, 35, 42, 60)
STABILITY = (2, 12, 14, 18, 25)
SCALARS = (.99, .96, .95, .945, .92)
COMMIT = "039cfbc4732c33573568b28cc6335dd3332a9296"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
EXPECTED = {
    ("duke_mk_44", 2112909414, 2, 3744182842),
    ("patron_of_lost_causes", 2723241847, 3, 2564227946),
    ("long_arm", 8293111, 3, 3056706286),
    ("allied_demand", 1532276803, 3, 3275836355),
    ("lonesome", 2199171672, 3, 3612808001),
    ("brass_attacks", 2121785039, 3, 100135553),
    ("biting_winds", 1621657423, 3, 3968704963),
    ("bite_of_the_fox", 1403800851, 3, 563442205),
    ("apostate", 2164448701, 4, 2826016044),
    ("line_in_the_sand", 946443267, 3, 1503774254),
    ("stormchaser", 3652506829, 3, 897699284),
}
POLICIES = {
    "sourceRefreshScope": "UNKNOWN",
    "sourceExpirationMode": "UNKNOWN",
    "sourceStowPersistence": "UNKNOWN",
    "sourceReloadConsumption": "UNKNOWN",
    "sourceReloadSnapshot": "UNKNOWN",
    "sourceCombinedReloadPerks": "UNKNOWN",
    "hitRefresh": "WHOLE_WINDOW_40_TICKS_LOCAL_POLICY",
    "expiration": "READ_ONLY_EXPIRE_LOCAL_POLICY",
    "stowPersistence": "SAME_IDENTITY_CLOCK_CONTINUES_LOCAL_POLICY",
    "reloadSnapshot": "AT_RELOAD_START_NONCONSUMING_NO_REFRESH_LOCAL_POLICY",
    "weakenedBodyHits": "SOURCE_WEAKENED_AT_ACTUAL_IMPACT_LOCAL_MAPPING",
    "stabilityIntegration": "MINECRAFT_CURVE_MASTER_OWNED_LOCAL_POLICY",
    "statCap": 100,
    "bowStatCap": 85,
    "rounding": "CEIL_SECONDS_TIMES_20_ONCE",
    "bowTiming": "HISTORICAL_W46_NOCK_ONLY_DRAW_UNCHANGED",
    "longArmTiming": "SOURCE_INSERT_UNKNOWN_LOCAL_BASE_PHASE_RATIO",
}
PINS = {
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
    "src/main/resources/destiny/weapons/w62-outlaw.json": "5188d73a271b0a5080eb99d47c50a6d37ccae11fe756ebd2893c70499f3637bc",
    "src/main/resources/destiny/weapons/w108-feeding-frenzy.json": "1ffbff575f0a29adc5a749d581f31c2f6dd67dfea20cf4a3484b6d2c1c522ce8",
    "src/main/resources/destiny/weapons/w61-kill-clip.json": "fb3374e775b9313619f34c1dda5681d391577c15279aa140f9fdc59b2d2ebd9a",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "clarity": "881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
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


def eligible(socket_index, trait_indexes, field, pool, match, exotic):
    return (not exotic and socket_index in trait_indexes and field == "randomizedPlugSetHash"
            and not pool["isFakePlugSet"] and match["plugItemHash"] == BASE
            and match.get("currentlyCanRoll") is True)


def validate_membership(rows):
    keys = [(r["id"], r["hash"], r["socket"], r["plugSetHash"]) for r in rows]
    require(len(keys) == len(set(keys)) == len(EXPECTED) and set(keys) == EXPECTED
            and all(r["perkHash"] == BASE for r in rows), "Exact selected socket membership changed")


def validate_tiers(tiers):
    require(tiers == [{"stacks": i, "stabilityBonus": s, "reloadBonus": b, "durationMultiplier": m}
                      for i, (s, b, m) in enumerate(zip(STABILITY, BONUSES, SCALARS), 1)],
            "Incomplete/incorrect sourced tiers")


def timing(curve, stat, tier, cap):
    require(type(stat) is int and 0 <= stat <= 100 and cap in (85, 100), "Invalid stat/cap")
    effective = min(cap, stat + tier["reloadBonus"])
    seconds = (curve.get("evpp", 0) * effective * effective
               + curve.get("vpp", 0) * effective + curve["offset"]) * tier["durationMultiplier"]
    require(math.isfinite(seconds) and 0 < seconds <= 60, "Unsafe reload duration")
    return effective, seconds, math.ceil(seconds * 20)


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
    same_name = {i["hash"] for i in inv.values() if i.get("displayProperties", {}).get("name") == "Rapid Hit"}
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
    require(base["hash"] == BASE and base["type"] == "Weapon Trait" and base["name"] == "Rapid Hit"
            and all(fragment in text for fragment in (
                '\"Buffed Hits\" grant 1 Stack of Rapid Hit for 2 seconds. Maximum of 5 Stacks.',
                'Precision Hits or Hits against debuffed targets.', '2|12|14|18|25 Stability',
                '5|30|35|42|60 Reload Speed', '0.99x|0.96x|0.95x|0.945x|0.92x Reload Duration Multiplier')),
            "Exact Clarity base mechanics not established")
    tiers = [{"stacks": i, "stabilityBonus": s, "reloadBonus": b, "durationMultiplier": m}
             for i, (s, b, m) in enumerate(zip(STABILITY, BONUSES, SCALARS), 1)]
    validate_tiers(tiers)
    mapping_source = data["art/weapons/w43/extraction.json"]
    mapping = {m["id"]: m for m in mapping_source["entries"]}
    formulas = data["art/weapons/w46/weapon_formulas.json"]
    timings = {r["id"]: r["timing"] for r in data["src/main/resources/destiny/weapons/w46-timing.json"]}
    require("self.evpp * _x * _x + self.vpp * _x + self.offset" in raw["art/weapons/w46/rs_types.rs"].decode()
            and all(s in raw["art/weapons/w46/stat_calc.rs"].decode() for s in (
                "reload_time = self.reload_data.solve_at(_reload_stat as f64)",
                "out.reload_time *= modifiers.reload_time_scale;", "reload_stat.clamp(0, 85)")),
            "Historical curve/stat/scalar/bow-cap semantics changed")
    by_id = {w["id"]: w for w in selected}
    curves, plans, audits = [], [], []
    for row in rows:
        id = row["id"]
        w, m, baseline = by_id[id], mapping[id], timings[id]
        require(baseline["supported"] and not baseline["shellReload"] and baseline["reloadInitialTicks"] is None,
                "Unreviewed shell/initial timing")
        curve = formulas[m["family"]]["cat"][m["category"]]["reload"]
        require(set(curve) <= {"evpp", "vpp", "offset", "ammo_percent"}, "Unknown curve fields")
        cap = 85 if families[id] == "bow" else 100
        stat = w["stats"]["4188031367"]
        _, seconds, ticks = timing(curve, stat, {"reloadBonus": 0, "durationMultiplier": 1}, cap)
        require(ticks == baseline["reloadTicks"], "Cannot reproduce W46 baseline")
        classification = ("HISTORICAL_W46_NOCK_ONLY_DRAW_UNCHANGED" if cap == 85 else
                          "SOURCE_INSERT_UNKNOWN_LOCAL_BASE_PHASE_RATIO" if id == "long_arm" else
                          "HISTORICAL_W46_WHOLE_MAGAZINE_CURVE")
        curves.append({"id": id, **{k: curve.get(k, 0) for k in ("evpp", "vpp", "offset")}, "statCap": cap})
        for tier in tiers:
            effective, buffed_seconds, buffed = timing(curve, stat, tier, cap)
            require(1 <= buffed <= ticks and 0 < buffed_seconds <= seconds, "Buff slows baseline")
            plans.append({"id": id, "stacks": tier["stacks"], "firstTicks": buffed, "intervalTicks": buffed,
                          "baseReloadStat": stat, "effectiveReloadStat": effective})
        audits.append({"id": id, "hash": row["hash"], "family": m["family"], "category": m["category"],
            "curve": curve, "statCap": cap, "baseReloadStat": stat, "baseSeconds": seconds, "baseTicks": ticks,
            "classification": classification, "shellReload": False, "reloadInitialTicks": None,
            "drawTicksUnchanged": baseline["drawTicks"],
            "phaseRatioPolicy": "ceil(existingPhaseTicks * unroundedBuffedCurveSeconds / unroundedBaseCurveSeconds); preserve distinct first/interval and2roundinsert; LOCAL approximation, no measured source insert duration" if id == "long_arm" else None})
    combos = []
    for perk, file in (("outlaw", "w62-outlaw.json"), ("feeding_frenzy", "w108-feeding-frenzy.json"),
                       ("kill_clip", "w61-kill-clip.json")):
        for row in rows:
            for other in data["src/main/resources/destiny/weapons/" + file]["weapons"]:
                if row["hash"] == other["hash"]:
                    combos.append({"id": row["id"], "hash": row["hash"], "otherPerk": perk,
                        "rapidHitSocket": row["socket"], "otherSocket": other["socket"],
                        "rapidHitPlugSetHash": row["plugSetHash"], "otherPlugSetHash": other["plugSetHash"],
                        "crossSocket": row["socket"] != other["socket"]})
    limitations = [
        "Official item/plug-set snapshot Oct13 and historical community W46 curves are independently sourced; no current sandbox exactness claim.",
        "Biting Winds uses historical nock curve with reload stat clamped at85; draw duration is unchanged, no magazine or full bow-cycle duration invented.",
        "Long Arm curve plans are historical reference only. Source insert timings remain unknown. Runtime applies unrounded curve ratio separately to existing local20tick first/13tick interval with ceil once each, preserving2roundinsert; this is explicitly LOCAL approximation.",
        "Lifecycle choices and Minecraft stability mapping are local master-owned policies; Clarity does not establish them.",
        "Cross-socket eligibility establishes available combinations only; combined Outlaw/Rapid Hit reload math is not source-proven here.",
    ]
    resource = {"stage": "W169", "perk": {"id": "rapid_hit", "hash": BASE, "durationTicks": 40, "maxStacks": 5,
        "mechanicsSource": ART + "clarity-source.json", "timingSource": ART + "reload-timings.json"},
        "policies": POLICIES, "tiers": tiers, "weapons": rows, "curves": curves, "reloads": plans}
    sockets = {"stage": "W169", "selectedCount": 65, "supportedCount": len(rows),
        "randomizedCount": len(rows), "fixedCuratedCount": 0,
        "policy": "Exact selected legendary trait-category socket; exact base hash, real randomized pool, currentlyCanRoll=true; weight0 is not exclusion. Fake/reusable/direct references alone never authorize a roll.",
        "perkDefinitions": definitions, "weapons": proofs, "allSelectedPoolScans": scans,
        "unsupportedSelectedIds": [w["id"] for w in selected if w["id"] not in {r["id"] for r in rows}],
        "excludedOptions": excluded, "directOptions": direct, "reloadPerkOverlaps": combos,
        "combinedReloadMathSourceStatus": "UNKNOWN_MASTER_LOCAL_POLICY_REQUIRED"}
    clarity = {"stage": "W169", "commit": COMMIT, "sourceFileSha256": PINS["clarity"],
        "url": "https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/" + COMMIT + "/descriptions/clarity.json",
        "entries": {str(BASE): base}, "communitySource": {"primary": False, "text": text},
        "officialTrigger": {"primary": True, "hash": BASE, "description": inv[str(BASE)]["displayProperties"]["description"]},
        "trigger": "PRECISION_OR_DEBUFFED_TARGET_YELLOW_HIT", "tiers": tiers, "policies": POLICIES,
        "limitations": limitations}
    timings = {"stage": "W169", "repository": mapping_source["repository"], "commit": mapping_source["commit"],
        "commitDate": mapping_source["commitDate"], "source": "build_resources/weapon_formulas.json",
        "licenseSources": ["art/weapons/w46/MIT-LICENSE", "art/weapons/w46/UNLICENSE"],
        "formula": "ceil(20 * (evpp*x*x + vpp*x + offset) * tierScalar), x=min(familyCap, officialReloadStat + tierBonus); bow familyCap=85, otherwise100",
        "entries": audits, "reloads": plans, "reloadPerkOverlaps": combos, "limitations": limitations}
    outputs = {TARGET: resource, ART + "official-sockets.json": sockets, ART + "clarity-source.json": clarity,
               ART + "reload-timings.json": timings}
    outputs[ART + "manifest.json"] = {"stage": "W169", "selectedCount": 65, "supportedCount": len(rows),
        "reloadPlans": len(plans), "manifestVersion": VERSION,
        "inventoryUrl": "https://www.bungie.net" + ipath, "plugSetsUrl": "https://www.bungie.net" + ppath,
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
        ("missing socket", lambda r: r.pop()),
        ("duplicate socket", lambda r: r.append(r[0])),
        ("wrong selected hash", lambda r: r[0].update(hash=1)),
        ("wrong socket", lambda r: r[0].update(socket=3)),
        ("enhanced trait", lambda r: r[0].update(perkHash=ENHANCED)),
        ("wrong pool", lambda r: r[0].update(plugSetHash=1)),
    ):
        rows = copy.deepcopy(resource["weapons"])
        edit(rows)
        rejects(name, lambda: validate_membership(rows))
    for name, edit in (
        ("missing tier", lambda t: t.pop()),
        ("wrong scalar", lambda t: t[0].update(durationMultiplier=.9)),
        ("wrong stability", lambda t: t[0].update(stabilityBonus=10)),
        ("wrong reload bonus", lambda t: t[0].update(reloadBonus=10)),
    ):
        tiers = copy.deepcopy(resource["tiers"])
        edit(tiers)
        rejects(name, lambda: validate_tiers(tiers))
    good = {"plugItemHash": BASE, "currentlyCanRoll": True, "weight": 0}
    pool = {"isFakePlugSet": False}
    require(eligible(3, {3}, "randomizedPlugSetHash", pool, good, False), "Weight0 must remain eligible")
    for name, idx, traits, field, p, match, exotic in (
        ("fake randomized", 3, {3}, "randomizedPlugSetHash", {"isFakePlugSet": True}, good, False),
        ("reusable only", 3, {3}, "reusablePlugSetHash", pool, good, False),
        ("unrollable", 3, {3}, "randomizedPlugSetHash", pool, {**good, "currentlyCanRoll": False}, False),
        ("rollability missing", 3, {3}, "randomizedPlugSetHash", pool, {"plugItemHash": BASE}, False),
        ("enhanced", 3, {3}, "randomizedPlugSetHash", pool, {**good, "plugItemHash": ENHANCED}, False),
        ("same name other hash", 3, {3}, "randomizedPlugSetHash", pool, {**good, "plugItemHash": 2578928835}, False),
        ("nontrait socket", 2, {3}, "randomizedPlugSetHash", pool, good, False),
        ("exotic owner", 3, {3}, "randomizedPlugSetHash", pool, good, True),
    ):
        require(not eligible(idx, traits, field, p, match, exotic), "Accepted " + name)
        rejected.append(name)
    rejects("invalid stat", lambda: timing({"offset": 1}, -1, resource["tiers"][0], 100))
    rejects("nonfinite curve", lambda: timing({"offset": float("nan")}, 50, resource["tiers"][0], 100))
    curves = {r["id"]: r for r in resource["curves"]}
    for row in resource["reloads"]:
        c = curves[row["id"]]
        eff, _, ticks = timing(c, row["baseReloadStat"], resource["tiers"][row["stacks"] - 1], c["statCap"])
        require(row["effectiveReloadStat"] == eff and row["firstTicks"] == row["intervalTicks"] == ticks, "Timing drift")
    require(len(resource["reloads"]) == 55, "Incomplete selected11 by five tier plans")
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
        print(json.dumps({"stage": "W169", "status": "VERIFY_PASS" if args.verify else "GENERATED",
            "selected": 65, "supported": 11, "reloadPlans": 55, "negativeCasesRejected": rejected,
            "outputs": list(outputs)}, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("W169 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
