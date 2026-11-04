#!/usr/bin/env python3
"""Pinned selected65 exact-base Focused Fury. --verify writes nothing; no network.

W173 socket scanner predicates, without handling/ADS curves or runtime integration.
--self-test exercises selection and malformed output in memory only.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/build_focused_fury_profile_w174.py"
ART = "art/weapons/w174/focused-fury/"
TARGET = "src/main/resources/destiny/weapons/w174-focused-fury.json"
BASE, ENHANCED, TRAIT_CATEGORY, MAGAZINE = 2896038713, 2402480669, 4241085061, "3871231066"
COMMIT = "039cfbc4732c33573568b28cc6335dd3332a9296"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
EXPECTED = {
    ("aishas_embrace", 2638190703, 4, BASE, 4211351701),
    ("retraced_path", 548958835, 4, BASE, 398391969),
    ("fixed_odds", 2194955522, 4, BASE, 1686775256),
}
MAGAZINES = {"aishas_embrace": 17, "retraced_path": 94, "fixed_odds": 44}
PERK = {"id": "focused_fury", "hash": BASE, "durationTicks": 220,
        "damageMultiplier": 1.25, "precisionFraction": 0.35}
POLICIES = {
    "threshold": "CEIL_35_PERCENT_OFFICIAL_BASE_MAGAZINE",
    "progressReset": "STOW_OR_RELOAD",
    "buffWhileStowed": "REMAINS_ACTIVE_CLARITY",
    "refresh": "LOCAL_CONSUME_THRESHOLD_RESET_COUNTER_ZERO_REFRESH_220_TICKS",
    "deadline": "LOCAL_STOW_RELOAD_PRESERVE_DEADLINE_NO_PAUSE",
    "damageAttribution": "MASTER_PAID_DIRECT_ONLY_NO_OTHER_PERK_SPLASH",
    "lifecycle": "MASTER_OWNED_LOCAL_POLICY",
}
PINS = {
    "scripts/build_adrenaline_junkie_profile_w173.py": "93901fb9c6ca467fbe23a2e87f7fc3d494895aded53de2fccd3de893f2c2e45d",
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
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def eligible(socket_index, trait_indexes, field, pool, match, exotic, perk_hash=BASE):
    # Identical W173 eligibility: weight=0 is accepted when currentlyCanRoll=true.
    return (not exotic and socket_index in trait_indexes and field == "randomizedPlugSetHash"
            and not pool["isFakePlugSet"] and match["plugItemHash"] == perk_hash
            and match.get("currentlyCanRoll") is True)


def threshold(base_magazine):
    require(type(base_magazine) is int and 0 < base_magazine <= 2147483647, "Positive int base magazine")
    return (35 * base_magazine + 99) // 100


def validate_membership(rows):
    fields = {"id", "hash", "socket", "perkHash", "plugSetHash"}
    require(all(type(r) is dict and set(r) == fields for r in rows), "Exact roll fields")
    keys = [tuple(r[k] for k in ("id", "hash", "socket", "perkHash", "plugSetHash")) for r in rows]
    require(len(keys) == len(set(keys)) == len(EXPECTED) and set(keys) == EXPECTED,
            "Exact selected65 base socket membership")


def validate_resource(root):
    require(type(root) is dict and set(root) == {"stage", "perk", "policies", "weapons", "magazines"},
            "Resource schema")
    require(root["stage"] == "W174" and root["perk"] == PERK and root["policies"] == POLICIES,
            "Pinned mechanics and explicit local policies")
    validate_membership(root["weapons"])
    require(root["magazines"] == [{"id": r["id"], "baseMagazine": MAGAZINES[r["id"]],
                                   "threshold": threshold(MAGAZINES[r["id"]])} for r in root["weapons"]],
            "Official base magazine threshold plans")


def research(base, enhanced, raw_sha):
    return {
        "stage": "W174", "commit": COMMIT,
        "repository": "https://github.com/Database-Clarity/Live-Clarity-Database",
        "url": f"https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/{COMMIT}/descriptions/clarity.json",
        "sourceSha256": raw_sha, "base": base, "enhancedExcludedHash": ENHANCED,
        "enhancedExcluded": enhanced,
        "verifiedSourceMechanics": {
            "precisionFraction": 0.35, "baseMagazine": True, "durationSeconds": 11,
            "damageMultiplier": 1.25, "resetProgressOnReload": True, "resetProgressOnStow": True,
            "buffRemainsWhileStowed": True, "otherPerkSplashBuffed": False,
        },
        "externalResearch": [
            {"url": "https://www.bungie.net/7/en/News/Article/destiny_update_9_7_0",
             "date": "2026-06-09", "kind": "OFFICIAL_PATCH_NOTES", "checked": "2026-10-27",
             "finding": "Focused Fury now uses a 0.35 magazine fraction and 1.25 damage multiplier. The nearby pause-on-stow change belongs to All-Star, not Focused Fury.",
             "scope": "Does not establish threshold counter consumption or refresh cadence."},
            {"url": "https://www.light.gg/db/items/2896038713/focused-fury/?_=584",
             "kind": "CURRENT_COMMUNITY_RESEARCH", "checked": "2026-10-27",
             "finding": "Indexed community research corroborates pinned Clarity values and stowed persistence; it does not add explicit refresh-counter semantics.",
             "access": "Search index accessible; direct canonical URL returned HTTP402."},
            {"url": "https://www.reddit.com/r/DestinyTheGame/comments/teeeah/focused_fury_transverse_steps/",
             "date": "2022-03-15", "kind": "HISTORICAL_COMMUNITY_REPORT", "checked": "2026-10-27",
             "finding": "A commenter describes another complete precision-hit quota renewing the timer, with reload and swap clearing progress while retaining an active weapon-specific buff.",
             "scope": "Historical corroboration only, not authoritative current measurements; its old numerical tuning is superseded."},
        ],
        "localPolicies": {
            "counter": "Consume each threshold: counter becomes zero; each next full threshold refreshes a 220-tick deadline. No refresh from every single hit.",
            "stowReload": "Clear partial counter while retaining the original deadline; time continues while stowed. Do not pause or extend on stow/reload.",
            "nonPrecision": "Misses/body hits do not increment or clear progress; no same-target or inter-hit timeout requirement. Pinned sources list only reload/stow resets; additional reset boundaries are master policy.",
            "ammo": "Use immutable official base magazine, not current rounds, overflow or perk-refilled ammunition. Current W46 values equal all three official base values.",
            "damage": "Master applies the buff only to paid direct weapon damage; separate payload splash tokenNONE and Dragonfly generic damage stay unchanged.",
            "orderingLifecycle": "Master owns threshold-causing shot ordering, token deduplication, expiry edge, cancellation, selection changes, death/logout/session cleanup and combinations.",
        },
        "unresolved": [
            "No current authoritative source located that explicitly specifies counter consumption on activation, repeated-threshold refresh or stow timer progression. Those precise implementation rules remain local policy with historical corroboration.",
            "No Destiny client measurement or native Minecraft runtime QA was performed by this worker.",
        ],
    }


def generate(args):
    root = args.root.resolve()
    paths = {p: root / p for p in PINS if "/" in p}
    paths.update(inventory=args.inventory, plugSets=args.shared_sources_dir / "bungie-plugsets.json",
                 manifest=args.shared_sources_dir / "manifest.json", clarity=args.clarity)
    data, pins = {}, {}
    for key, path in paths.items():
        raw = path.read_bytes()
        require(digest(raw) == PINS[key], "Source SHA256 mismatch: " + key)
        pins[key] = {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                     "sha256": digest(raw), "bytes": len(raw)}
        if key.endswith(".json") or key in ("inventory", "plugSets", "manifest", "clarity"):
            data[key] = json.loads(raw)
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
    same_name = {i["hash"] for i in inv.values() if i.get("displayProperties", {}).get("name") == "Focused Fury"}
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
    by_id, timings = {w["id"]: w for w in selected}, {w["id"]: w["timing"] for w in timing}
    magazines, audit = [], []
    for r in rows:
        id = r["id"]
        official = inv[str(r["hash"])]["stats"]["stats"][MAGAZINE]["value"]
        selected_mag, profile_mag = by_id[id]["stats"][MAGAZINE], timings[id]["magazine"]
        require(official == selected_mag == profile_mag == MAGAZINES[id], "Base magazine discrepancy: " + id)
        magazines.append({"id": id, "baseMagazine": official, "threshold": threshold(official)})
        audit.append({"id": id, "officialBaseMagazine": official, "selectedW40Magazine": selected_mag,
                      "currentW46ProfileMagazine": profile_mag, "threshold": threshold(official), "discrepancy": False})
    base = data["clarity"][str(BASE)]
    text = "\n".join(line.get("text", "") for block in base["descriptions"]["en"] for line in block.get("linesContent", []))
    require(base["hash"] == BASE and base["name"] == "Focused Fury" and base["type"] == "Weapon Trait"
            and all(fragment in text for fragment in ("35% of the Base Magazine Capacity", "25% increased damage for 11 seconds",
                "Stowing or Reloading the weapon resets the Precision Hit counter", "buff remains active while stowed",
                "Does not buff the Splash/Explosive damage elements of other perks")), "Pinned current Clarity tuning")
    resource = {"stage": "W174", "perk": PERK, "policies": POLICIES, "weapons": rows, "magazines": magazines}
    validate_resource(resource)
    sockets = {"stage": "W174", "selectedCount": 65, "supportedCount": len(rows), "randomizedCount": len(rows),
               "fixedCuratedCount": 0, "policy": "W173 exact base, legendary trait category, real randomized pool, currentlyCanRoll=true; weight0 accepted. Direct/reusable/fake/enhanced/exotic alone rejected.",
               "perkDefinitions": definitions, "weapons": proofs, "selectedScan": scans, "excludedReferences": excluded,
               "directReferences": direct, "unsupportedSelectedIds": [w["id"] for w in selected if w["id"] not in MAGAZINES],
               "magazineAudit": audit, "magazineDiscrepancies": []}
    outputs = {TARGET: resource, ART + "official-sockets.json": sockets,
               ART + "clarity-source.json": research(base, data["clarity"][str(ENHANCED)], PINS["clarity"])}
    outputs[ART + "manifest.json"] = {
        "stage": "W174", "selectedCount": 65, "supportedCount": len(rows), "manifestVersion": VERSION,
        "inventoryUrl": "https://www.bungie.net" + ipath, "plugSetsUrl": "https://www.bungie.net" + ppath,
        "sourcePins": pins, "generator": SCRIPT, "generatorSha256": digest((root / SCRIPT).read_bytes()),
        "outputSha256": {p: digest(encoded(v)) for p, v in outputs.items()},
        "reproduce": "rtk proxy python3 scripts/build_focused_fury_profile_w174.py --verify --self-test",
        "eligibleIds": list(MAGAZINES), "magazineAudit": audit,
        "limitations": [
            "Official membership/base magazines and Clarity mechanics have separate pinned provenance. Enhanced Focused Fury is excluded.",
            "All three current W46 profile magazines match official base capacity. Threshold uses ceil(35*base/100); never current ammo or overflow. Drift fails verification rather than silently changing thresholds.",
            "Exact refresh/counter consumption/deadline and lifecycle rules are local policy; historical refresh reports do not constitute current authoritative measurements. See clarity-source.json.",
            "Registry/cycle/combat integration, combined selections, paid-token attribution, shared gate and native scenarios are master-owned; this worker makes no native QA claims.",
        ],
    }
    return outputs


def self_test(outputs):
    rejected = []
    resource = outputs[TARGET]
    cases = [lambda r: r.update(stage="W173"), lambda r: r["perk"].update(hash=ENHANCED),
             lambda r: r["perk"].update(precisionFraction=.5), lambda r: r["perk"].update(damageMultiplier=1.2),
             lambda r: r["perk"].update(durationTicks=240), lambda r: r["weapons"].pop(),
             lambda r: r["weapons"].append(copy.deepcopy(r["weapons"][0])),
             lambda r: r["weapons"][0].update(socket=3), lambda r: r["weapons"][0].update(plugSetHash=1),
             lambda r: r["weapons"][0].update(id="ammit_ar2"), lambda r: r["weapons"][0].update(perkHash=ENHANCED),
             lambda r: r["magazines"][0].update(baseMagazine=18), lambda r: r["magazines"][0].update(threshold=5),
             lambda r: r["policies"].update(refresh="EVERY_HIT"), lambda r: r.update(reloadBonus=20)]
    for key in resource:
        cases.extend([lambda r, k=key: r.pop(k), lambda r, k=key: r.update({k: None})])
    for n, mutation in enumerate(cases):
        changed = copy.deepcopy(resource)
        mutation(changed)
        try:
            validate_resource(changed)
        except (ValueError, TypeError, KeyError):
            rejected.append(n)
        else:
            raise AssertionError("Accepted malformed resource case " + str(n))
    pool, match = {"isFakePlugSet": False}, {"plugItemHash": BASE, "currentlyCanRoll": True, "weight": 0}
    require(eligible(4, {4}, "randomizedPlugSetHash", pool, match, False), "Weight0 must remain eligible")
    negative = [eligible(3, {4}, "randomizedPlugSetHash", pool, match, False),
                eligible(4, {4}, "reusablePlugSetHash", pool, match, False),
                eligible(4, {4}, "randomizedPlugSetHash", {"isFakePlugSet": True}, match, False),
                eligible(4, {4}, "randomizedPlugSetHash", pool, match, True)]
    negative.extend(eligible(4, {4}, "randomizedPlugSetHash", pool, {**match, **m}, False)
                    for m in [{"plugItemHash": ENHANCED}, {"currentlyCanRoll": False}, {"currentlyCanRoll": None}])
    require(not any(negative), "Scanner admitted excluded reference")
    require([threshold(v) for v in (1, 17, 20, 44, 94, 100, 2147483647)]
            == [1, 6, 7, 16, 33, 35, 751619277], "Exact integer ceil without overflow/float drift")
    for bad in (0, -1, True, 17.5, 2147483648):
        try:
            threshold(bad)
        except ValueError:
            rejected.append("magazine:" + str(bad))
        else:
            raise AssertionError("Invalid magazine accepted")
    return {"malformedResourcesRejected": len(cases), "excludedReferencesRejected": len(negative),
            "invalidMagazinesRejected": 5, "negativeCasesRejected": len(rejected) + len(negative)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    parser.add_argument("--shared-sources-dir", type=Path, default=Path("/tmp/destiny-weapons-w60"))
    parser.add_argument("--clarity", type=Path, default=Path("/private/tmp/w167-clarity.json"))
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    outputs = generate(args)
    results = self_test(outputs) if args.self_test else {}
    if args.self_test:
        require({k: encoded(v) for k, v in outputs.items()} == {k: encoded(v) for k, v in generate(args).items()},
                "Nondeterministic regeneration")
    for path, value in outputs.items():
        dest, raw = args.root / path, encoded(value)
        if args.verify:
            require(dest.is_file() and dest.read_bytes() == raw, "Generated output differs: " + path)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
    print(json.dumps({"stage": "W174", "mode": "verify" if args.verify else "generate", "selected": 65,
                      "supported": 3, "eligibleIds": list(MAGAZINES), "thresholds": {k: threshold(v) for k, v in MAGAZINES.items()},
                      "deterministicRepeat": args.self_test, **results, "outputs": list(outputs)}, indent=2))


if __name__ == "__main__":
    main()
