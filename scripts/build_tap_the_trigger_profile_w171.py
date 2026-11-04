#!/usr/bin/env python3
"""Pinned offline selected65 base Tap the Trigger extraction. --verify writes nothing."""
import sys
sys.dont_write_bytecode = True
import argparse
import copy
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/build_tap_the_trigger_profile_w171.py"
ART = "art/weapons/w171/tap-the-trigger/"
TARGET = "src/main/resources/destiny/weapons/w171-tap-the-trigger.json"
BASE, ENHANCED = 1890422124, 1523649716
OTHER_COPIES = set()
TRAIT_CATEGORY = 4241085061
COMMIT = "039cfbc4732c33573568b28cc6335dd3332a9296"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
EXPECTED = {
    ("ammit_ar2", 2119346509, 4, 560115158),
    ("gnawing_hunger", 821154603, 3, 1144396384),
    ("dead_man_walking_xx7463", 3751622019, 4, 1210839935),
    ("dream_breaker", 2931957300, 4, 1206254527),
    ("hammerhead", 603242241, 3, 2515290473),
    ("retrofit_escapade", 3103325054, 4, 2461260598),
}
PERK = {"id": "tap_the_trigger", "hash": BASE, "durationSeconds": 0.6, "durationTicks": 12,
        "ordinary": {"stabilityBonus": 40, "recoilScalar": 0.5, "accuracyScalar": 0.9},
        "fusion": {"stabilityBonus": 10, "recoilScalar": 0.875, "accuracyScalar": 0.975}}
POLICIES = {
    "refresh": "AFTER_AUTOMATIC_STOPS_FIRING_OR_NEXT_BURST",
    "cycleIntegration": "MASTER_OWNED_LOCAL_POLICY",
    "stabilityRecoilSpreadAdapters": "MASTER_OWNED_LOCAL_POLICY",
    "controllerPressure": "CONTROLLER_ONLY_OUTSIDE_JAVA_KEYBOARD_IMPLEMENTATION",
    "tickConversion": "0.6_SECONDS_TIMES_20_EQUALS_12",
}
PINS = {
    "src/main/resources/destiny/weapons/w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    "src/main/resources/destiny/weapons/w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "src/main/resources/destiny/weapons/w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    "src/main/resources/destiny/weapons/w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "art/weapons/w40/provenance.json": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "clarity": "881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384"
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
    same_name = {i["hash"] for i in inv.values() if i.get("displayProperties", {}).get("name") == "Tap the Trigger"}
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
    require({r["id"] for r in rows if families[r["id"]] == "fusion_rifle"} == {"dream_breaker"}, "Exact fusion membership")
    base = data["clarity"][str(BASE)]
    text = "\n".join(line.get("text", "") for block in base["descriptions"]["en"] for line in block.get("linesContent", []))
    require(base["hash"] == BASE and base["type"] == "Weapon Trait" and base["name"] == "Tap the Trigger"
            and all(fragment in text for fragment in (
                "for 0.6 seconds", "40 Stability", "50% decreased Recoil", "10% decreased Accuracy Cone Size",
                "Fusion Rifles only receive", "25% of the benefits",
                "Buff cannot be refreshed until Automatic Weapons stop firing, or until the next burst.",
                "[Controller-Only]", "Weapon fires the instant trigger pressure is applied.")),
            "Exact base Clarity mechanics not established")
    require(data["clarity"][str(ENHANCED)]["type"] == "Weapon Trait Enhanced", "Enhanced identity")
    limitations = [
        "Bungie membership is the pinned Oct13 manifest snapshot; Clarity community mechanics use the pinned commit, not official engine measurements.",
        "0.6 seconds maps to 12 ticks at 20Hz. Fusion gets 25% of bonuses: +10 stability, recoil x0.875, accuracy cone x0.975; ordinary +40, x0.5, x0.9.",
        "No refresh until automatic weapons stop firing or the next burst. Actual runtime cycle and source/end-held integration are master-owned.",
        "Controller trigger pressure behavior is source evidence only and outside the Java keyboard implementation.",
        "Stability/recoil/spread/HUD adapters, combined perks and native Vision validation remain master-owned. Enhanced hash is excluded.",
    ]
    resource = {"stage": "W171", "perk": PERK, "policies": POLICIES, "weapons": rows}
    sockets = {"stage": "W171", "selectedCount": 65, "supportedCount": len(rows),
        "randomizedCount": len(rows), "fixedCuratedCount": 0,
        "policy": "Exact base hash in selected legendary trait-category real randomized pool; currentlyCanRoll=true. Weight0 is eligible. Reusable/direct/enhanced/exotic references do not establish base membership.",
        "perkDefinitions": definitions, "weapons": proofs, "selectedScan": scans,
        "excludedReferences": excluded, "directReferences": direct}
    clarity = {"stage": "W171", "commit": COMMIT,
        "repository": "https://github.com/Database-Clarity/Live-Clarity-Database",
        "url": "https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/" + COMMIT + "/descriptions/clarity.json",
        "sourceSha256": PINS["clarity"], "base": base, "enhancedExcludedHash": ENHANCED,
        "mechanics": PERK, "policies": POLICIES, "limitations": limitations}
    outputs = {TARGET: resource, ART + "official-sockets.json": sockets, ART + "clarity-source.json": clarity}
    outputs[ART + "manifest.json"] = {"stage": "W171", "selectedCount": 65, "supportedCount": len(rows),
        "manifestVersion": VERSION, "inventoryUrl": "https://www.bungie.net" + ipath,
        "plugSetsUrl": "https://www.bungie.net" + ppath, "sourcePins": pins,
        "generator": SCRIPT, "generatorSha256": digest((root / SCRIPT).read_bytes()),
        "outputSha256": {p: digest(encoded(v)) for p, v in outputs.items()},
        "reproduce": "rtk proxy python3 " + SCRIPT + " --verify --self-test", "limitations": limitations}
    return outputs, paths


def self_test(outputs):
    rejected = []
    def rejects(name, fn):
        try:
            fn()
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError("Accepted " + name)
    rows = outputs[TARGET]["weapons"]
    rejects("missing socket", lambda: validate_membership(rows[:-1]))
    bad = copy.deepcopy(rows)
    bad[0]["perkHash"] = ENHANCED
    rejects("enhanced membership", lambda: validate_membership(bad))
    for key in ("hash", "socket", "plugSetHash"):
        bad = copy.deepcopy(rows)
        bad[0][key] = 1
        rejects("wrong " + key, lambda: validate_membership(bad))
    good = {"plugItemHash": BASE, "currentlyCanRoll": True, "weight": 0}
    pool = {"isFakePlugSet": False}
    require(eligible(3, {3}, "randomizedPlugSetHash", pool, good, False), "Weight0 must be eligible")
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
    rejects("source pin drift", lambda: check_pin("clarity", b"drift"))
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
        print(json.dumps({"stage": "W171", "status": "VERIFY_PASS" if args.verify else "GENERATED",
            "selected": 65, "supported": 6, "negativeCasesRejected": rejected,
            "outputs": list(outputs)}, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("W171 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
