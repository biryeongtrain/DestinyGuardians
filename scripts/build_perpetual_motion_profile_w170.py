#!/usr/bin/env python3
"""Offline exact-selected65 base Perpetual Motion profile; --verify writes nothing.

All consumed inputs are pinned. Only five owned JSON outputs are written.
--self-test mutates memory only. No lifecycle or native-game behavior is inferred.
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
SCRIPT = "scripts/build_perpetual_motion_profile_w170.py"
ART = "art/weapons/w170/perpetual-motion/"
TARGET = "src/main/resources/destiny/weapons/w170-perpetual-motion.json"
BASE, ENHANCED = 1428297954, 2014892510
OTHER_COPIES = set()
TRAIT_CATEGORY = 4241085061
COMMIT = "039cfbc4732c33573568b28cc6335dd3332a9296"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
EXPECTED = {("aishas_embrace", 2638190703, 3, 7997267),
            ("retraced_path", 548958835, 3, 2945646047)}
POLICIES = {
    "statCap": 100, "durationMultiplier": 1.0,
    "rounding": "CEIL_SECONDS_TIMES_20_ONCE",
    "adsBounds": "CLAMP_TICKS_2_20_W44",
    "handlingBounds": "W58_NO_EXTRA_TICK_CLAMP_STOW_AT_100_FLOOR",
    "sourceMovementSampling": "UNKNOWN_MASTER_OWNED_LOCAL_POLICY",
    "sourceDiscontinuities": "UNKNOWN_MASTER_OWNED_LOCAL_POLICY",
    "sourceBriefPauseProgress": "UNKNOWN_MASTER_OWNED_LOCAL_POLICY",
    "sourceCombinedPerks": "UNKNOWN_MASTER_OWNED_LOCAL_POLICY",
    "stabilityIntegration": "MINECRAFT_CURVE_MASTER_OWNED_LOCAL_POLICY",
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


def eligible(socket_index, trait_indexes, field, pool, match, exotic):
    return (not exotic and socket_index in trait_indexes and field == "randomizedPlugSetHash"
            and not pool["isFakePlugSet"] and match["plugItemHash"] == BASE
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


def evaluate(curves, reload_stat, handling_stat, stacks):
    require(type(stacks) is int and 0 <= stacks <= 2, "Invalid stacks")
    require(type(reload_stat) is int and type(handling_stat) is int, "Invalid stats")
    reload = min(100, max(0, reload_stat + stacks * 10))
    handling = min(100, max(0, handling_stat + stacks * 10))
    seconds = {"reload": solve(curves["reload"], reload),
               "ready": solve(curves["ready"], handling),
               "stow": max(solve(curves["stow"], handling), solve(curves["stow"], 100)),
               "ads": solve(curves["ads"], handling)}
    require(all(math.isfinite(v) and 0 < v <= 60 for v in seconds.values()), "Unsafe duration")
    ticks = {k + "Ticks": (max(2, min(20, math.ceil(v * 20))) if k == "ads" else math.ceil(v * 20))
             for k, v in seconds.items()}
    return {"effectiveReloadStat": reload, "effectiveHandlingStat": handling, "seconds": seconds, **ticks}


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
    same_name = {i["hash"] for i in inv.values() if i.get("displayProperties", {}).get("name") == "Perpetual Motion"}
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
    require(base["hash"] == BASE and base["type"] == "Weapon Trait" and base["name"] == "Perpetual Motion"
            and all(fragment in text for fragment in (
                "minimum of 2 meters per second", "after 2 seconds and a second Stack after 10 seconds",
                "Each Stack provides 10 Stability, 10 Handling, and 10 Reload Speed.",
                "below 2 m/s for 0.5 seconds", "Works and can activate while stowed.")),
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
        reload, handling, stability = (stats[k] for k in ("4188031367", "943549884", "155624089"))
        require(all(type(v) is int and 0 <= v <= 100 for v in (reload, handling, stability)), "Invalid official stats")
        baseline = evaluate(c, reload, handling, 0)
        prior_reload, prior_handling, prior_aim = (baselines[f][id] for f in ("w46-timing.json", "w58-handling.json", "w44-aim.json"))
        require(prior_reload["supported"] and not prior_reload["shellReload"]
                and prior_reload["reloadInitialTicks"] is None and prior_handling["supported"]
                and baseline["reloadTicks"] == prior_reload["reloadTicks"]
                and baseline["readyTicks"] == prior_handling["readyTicks"]
                and baseline["stowTicks"] == prior_handling["stowTicks"]
                and baseline["adsTicks"] == prior_aim["transitionTicks"], "Cannot reproduce all four base timings")
        curves.append({"id": id, "baseReloadStat": reload, "baseHandlingStat": handling,
                       "baseStabilityStat": stability, **c})
        modified = []
        for stacks in (1, 2):
            result = evaluate(c, reload, handling, stacks)
            plan = {"id": id, "stacks": stacks, **{k: result[k] for k in ("reloadTicks", "readyTicks", "stowTicks", "adsTicks")},
                    "stabilityBonus": stacks * 10, "handlingBonus": stacks * 10, "reloadBonus": stacks * 10}
            require(all(plan[k] <= baseline[k] for k in ("reloadTicks", "readyTicks", "stowTicks", "adsTicks")), "Buff slows baseline")
            plans.append(plan)
            modified.append({**plan, **result, "effectiveStabilityStat": min(100, stability + stacks * 10)})
        audits.append({"id": id, "hash": row["hash"], "family": m["family"], "category": m["category"],
                       "curves": c, "baseReloadStat": reload, "baseHandlingStat": handling, "baseStabilityStat": stability,
                       "baseline": baseline, "modified": modified})
    limitations = [
        "Official Bungie Oct13 snapshot and historical Oracle May20 curves are separate snapshots; timings are community approximations, not current exact official animation measurements.",
        "Clarity establishes physical bonuses, threshold, stack times, removal grace and stowed activation only. Movement sampling, discontinuities and brief-pause progress are unknown and master-owned local policies.",
        "Stat cap100, scalar1; source stow-at100 floor; W44 ADS2..20tick bounds; W58 ready/stow no extra tick clamp; ceil once at20Hz is local adaptation.",
        "Combined perks/armor/masterworks, Minecraft stability mapping and native gameplay lifecycle are outside this profile. Enhanced Perpetual Motion is excluded.",
        "No native game, input, HUD, DCC or full gate validation performed by this bounded profile generator.",
    ]
    resource = {"stage": "W170", "perk": {"id": "perpetual_motion", "hash": BASE, "minSpeed": 2.0,
                "firstStackTicks": 40, "secondStackTicks": 200, "stopGraceTicks": 10, "maxStacks": 2, "worksStowed": True},
                "policies": POLICIES, "weapons": rows, "curves": curves, "timings": plans}
    sockets = {"stage": "W170", "selectedCount": 65, "supportedCount": 2, "randomizedCount": 2, "fixedCuratedCount": 0,
               "policy": "Exact base hash in selected legendary trait-category real randomized pool; currentlyCanRoll=true. Weight0 is eligible. Reusable/fake/direct/enhanced references alone never authorize rolls.",
               "perkDefinitions": definitions, "weapons": proofs, "allSelectedPoolScans": scans,
               "excludedReferences": excluded, "directReferences": direct,
               "unsupportedSelectedIds": [w["id"] for w in selected if w["id"] not in {r["id"] for r in rows}]}
    clarity = {"stage": "W170", "repository": "https://github.com/Database-Clarity/Live-Clarity-Database", "commit": COMMIT,
               "url": "https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/" + COMMIT + "/descriptions/clarity.json",
               "sourceSha256": PINS["clarity"], "base": base, "enhancedExcludedHash": ENHANCED,
               "physicalBonusesPerStack": {"stability": 10, "handling": 10, "reload": 10},
               "durationMultiplier": 1.0, "sourceDurationMultiplier": "NO_DURATION_SCALAR_SPECIFIED_NEUTRAL_1",
               "policies": POLICIES, "limitations": limitations}
    timings = {"stage": "W170", "repository": mapping_source["repository"], "commit": mapping_source["commit"],
               "commitDate": mapping_source["commitDate"], "source": "build_resources/weapon_formulas.json",
               "licenseSources": ["art/weapons/w46/MIT-LICENSE", "art/weapons/w46/UNLICENSE"],
               "formula": "q(x)=evpp*x*x+vpp*x+offset; x=clamp(baseStat+10*stacks,0,100); scalar1; ceil20*q once; stow=max(q(x),q(100)); ADS clamp2..20ticks",
               "entries": audits, "timings": plans, "limitations": limitations}
    outputs = {TARGET: resource, ART + "official-sockets.json": sockets, ART + "clarity-source.json": clarity,
               ART + "timings.json": timings}
    outputs[ART + "manifest.json"] = {"stage": "W170", "selectedCount": 65, "supportedCount": 2, "timingPlans": 4,
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
        ("wrong hash", lambda r: r[0].update(hash=1)), ("wrong socket", lambda r: r[0].update(socket=4)),
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
        rejects("unsafe curve " + str(value), lambda: evaluate(bad, 50, 50, 1))
    require(evaluate(c, 1000, 1000, 2) == evaluate(c, 100, 100, 2), "Upper stat clamp")
    require(evaluate(c, -1000, -1000, 2) == evaluate(c, -20, -20, 2), "Lower stat clamp")
    expected = [("aishas_embrace", 1, 42, 9, 9, 8), ("aishas_embrace", 2, 39, 9, 8, 7),
                ("retraced_path", 1, 39, 8, 7, 6), ("retraced_path", 2, 38, 7, 7, 6)]
    actual = [(r["id"], r["stacks"], r["reloadTicks"], r["readyTicks"], r["stowTicks"], r["adsTicks"]) for r in resource["timings"]]
    require(actual == expected, "Exact four timing plans changed: " + repr(actual))
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
        print(json.dumps({"stage": "W170", "status": "VERIFY_PASS" if args.verify else "GENERATED",
            "selected": 65, "supported": 2, "timingPlans": 4, "negativeCasesRejected": rejected,
            "outputs": list(outputs)}, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("W170 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
