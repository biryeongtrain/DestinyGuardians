#!/usr/bin/env python3
"""Offline W191 Pugilist extraction. --verify checks the two generated JSON files."""
import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons/"
TARGET = PREFIX + "w191-pugilist.json"
SOURCE = "art/weapons/w191/pugilist/source.json"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
BASE, ENHANCED, TRAIT = 691659142, 536173722, 4241085061
KEYS = ("id", "hash", "socket", "perkHash", "plugSetHash")
EXPECTED = [dict(zip(KEYS, r)) for r in (
    ("ammit_ar2", 2119346509, 4, BASE, 560115158),
    ("mindbender_s_ambition_adept", 912150785, 3, BASE, 1732284294),
    ("dimensional_hypotrochoid", 1311684613, 4, BASE, 1092097342))]
PROFILES = ("w60-holster.json", "w67-precision-return.json", "w68-snapshot.json",
            "w109-one-for-all.json", "w110-swashbuckler.json", "w171-tap-the-trigger.json",
            "w173-adrenaline-junkie.json", "w176-stats-for-all.json", "w178-threat-detector.json",
            "w181-vorpal.json", "w183-surplus.json", "w187-lead_from_gold.json")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def generate(args):
    pins = {}

    def read(path, key=None, text=False):
        raw = path.read_bytes()
        pins[key or str(path.relative_to(args.root))] = {
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        return raw.decode() if text else json.loads(raw)

    manifest = read(args.manifest, "manifest")["Response"]
    require(manifest["version"] == VERSION, "wrong pinned manifest version")
    inventory = read(args.inventory, "inventory")
    pools = read(args.plugsets, "plugsets")
    require({d["hash"] for d in inventory.values()
             if d.get("displayProperties", {}).get("name") == "Pugilist"} == {BASE, ENHANCED},
            "base/enhanced Pugilist definitions")
    require(inventory[str(BASE)]["itemTypeDisplayName"] == "Trait"
            and inventory[str(ENHANCED)]["itemTypeDisplayName"] == "Enhanced Trait", "trait types")
    ddc = read(args.ddc, "ddc", text=True)
    rows = [r for r in re.findall(r"<tr\b[^>]*>.*?</tr>", ddc, re.S)
            if any(html.unescape(re.sub(r"<[^>]+>", "", c)).strip() == "Pugilist"
                   for c in re.findall(r"<td\b[^>]*>(.*?)</td>", r, re.S))]
    require(len(rows) == 1, "unique exact td name Pugilist")
    raw_row = rows[0]
    row_text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw_row)).split())
    require(row_text.startswith("170 Pugilist") and all(s in row_text for s in
            ("10%", "20%", "Fusion Rifles, Glaives, Shotguns, and Sniper Rifles", "+35 Handling", "3 seconds")),
            "DDC row170 base values")
    selected = read(args.root / PREFIX / "w40-characteristics.json")
    for file in ("w83-exotics.json", "w84-exotics.json"):
        selected += [r["characteristics"] for r in read(args.root / PREFIX / file)]
    require(len(selected) == len({r["bungieHash"] for r in selected}) == 65, "catalog65")
    by_id = {w["id"]: w for w in selected}

    def traits(item):
        return {n for c in item["sockets"]["socketCategories"]
                if c["socketCategoryHash"] == TRAIT for n in c["socketIndexes"]}

    def official(w, n, perk):
        item = inventory[str(w["bungieHash"])]
        entry = item["sockets"]["socketEntries"][n]
        ph = entry.get("randomizedPlugSetHash")
        pool = pools.get(str(ph), {})
        definition = inventory.get(str(perk), {})
        if (w["exotic"] or n not in traits(item) or pool.get("isFakePlugSet") is not False
                or definition.get("itemTypeDisplayName") != "Trait"
                or definition.get("plug", {}).get("isDummyPlug") is not False
                or definition.get("redacted") or definition.get("blacklisted")
                or not any(p.get("currentlyCanRoll") is True and p["plugItemHash"] == perk
                           for p in pool.get("reusablePlugItems", []))):
            return None
        return dict(zip(KEYS, (w["id"], w["bungieHash"], n, perk, ph)))

    found, scans = [], []
    for w in selected:
        item = inventory[str(w["bungieHash"])]
        matches = [r for n in sorted(traits(item)) if (r := official(w, n, BASE))]
        found += matches
        scans.append({"id": w["id"], "hash": w["bungieHash"], "matches": matches})
    candidates = read(args.candidates, "candidates")["pugilist"]
    require(found == EXPECTED == candidates, "exact three requested rolls")

    # Every implemented legal other-socket companion, plus explicit same-socket exclusions.
    pairs, audit = [], []
    for file in PROFILES:
        d = read(args.root / PREFIX / file)
        if "perk" in d:
            groups = [(d["perk"]["id"], d["weapons"])]
        elif "perks" in d:
            groups = [(p["id"], p["weapons"]) for p in d["perks"]]
        else:
            groups = [("snapshot", d["rolls"])]
        for name, rolls in groups:
            for r in rolls:
                source = next((s for s in found if s["id"] == r["id"]), None)
                if source is None:
                    continue
                require(r == official(by_id[r["id"]], r["socket"], r["perkHash"]), "companion proof " + name)
                allowed = r["socket"] != source["socket"]
                audit.append({"perk": name, "roll": r, "allowed": allowed})
                if allowed:
                    pairs.append({"id": r["id"], "perk": name, "roll": r})
    stat_pairs = {(p["id"], p["perk"]) for p in pairs if p["perk"] in
                  {"surplus", "stats_for_all", "threat_detector", "snapshot"}}
    require(stat_pairs == {("ammit_ar2", "surplus"), ("ammit_ar2", "stats_for_all"),
                           ("dimensional_hypotrochoid", "stats_for_all"),
                           ("dimensional_hypotrochoid", "threat_detector")}, "handling composition")
    mapping = {r["id"]: r for r in read(args.root / "art/weapons/w43/extraction.json")["entries"]}
    formulas = read(args.root / "art/weapons/w46/weapon_formulas.json")
    handling = {r["id"]: r["profile"] for r in read(args.root / PREFIX / "w58-handling.json")}
    aim = {r["id"]: r["profile"] for r in read(args.root / PREFIX / "w44-aim.json")}
    curves, proof = [], []
    for r in found:
        w = by_id[r["id"]]
        item = inventory[str(r["hash"])]
        m = mapping[r["id"]]
        raw = formulas[m["family"]]["cat"][m["category"]]["handling"]
        c = {"id": r["id"], "baseHandlingStat": w["stats"]["943549884"], "snapshotScalar": None}
        require(c["baseHandlingStat"] == item["stats"]["stats"]["943549884"]["value"], "official handling")
        for key in ("ready", "stow", "ads"):
            c[key] = {k: raw[key].get(k, 0.0) for k in ("evpp", "vpp", "offset")}
        solve = lambda key: sum(c[key][k] * x for k, x in
                                (("evpp", c["baseHandlingStat"] ** 2), ("vpp", c["baseHandlingStat"]), ("offset", 1)))
        require(math.ceil(solve("ready") * 20) == handling[r["id"]]["readyTicks"]
                and math.ceil(solve("stow") * 20) == handling[r["id"]]["stowTicks"]
                and max(2, min(20, math.ceil(solve("ads") * 20))) == aim[r["id"]]["transitionTicks"],
                "historical baseline mapping")
        curves.append(c)
        sockets = []
        for n in sorted(traits(item)):
            e = item["sockets"]["socketEntries"][n]
            ph = e.get("randomizedPlugSetHash")
            if ph is not None:
                sockets.append({"socket": n, "entry": e, "plugSet": pools[str(ph)]})
        proof.append({"id": r["id"], "hash": r["hash"], "socketCategories": item["sockets"]["socketCategories"],
                      "sockets": sockets})
    components = manifest["jsonWorldComponentContentPaths"]["en"]
    provenance = {"version": VERSION, "manifestComponents": {k: components[k] for k in
                  ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
                  "inputSHA": pins, "rawRow": raw_row, "rowText": row_text,
                  "socketProof": proof}
    resource = {"stage": "W191", "perk": {"id": "pugilist", "hash": BASE,
                "energyPercent": 10, "specialEnergyPercent": 20, "handlingBonus": 35, "durationTicks": 60},
                "weapons": found, "curves": curves, "coSelections": pairs, "source": provenance}
    evidence = {"stage": "W191", **provenance, "ddc": {"row": 170, "tab": "Weapon Perks",
                "url": "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278"},
                "catalogScan": scans, "companionAudit": audit, "curves": curves,
                "historicalOracleCommit": "dcd0c7d302b056ffbb532edcb711d724a17ca8c1",
                "enhancedExcludedHash": ENHANCED, "resourceSHA256": hashlib.sha256(encode(resource)).hexdigest()}
    return {TARGET: resource, SOURCE: evidence}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    p.add_argument("--plugsets", type=Path, default=Path("/tmp/destiny-weapons-w60/bungie-plugsets.json"))
    p.add_argument("--manifest", type=Path, default=Path("/tmp/destiny-weapons-w60/manifest.json"))
    p.add_argument("--ddc", type=Path, default=Path("/private/tmp/destiny-w190/ddc-perks.html"))
    p.add_argument("--candidates", type=Path, default=Path("/private/tmp/destiny-w191/sockets.json"))
    p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    for name, value in generate(args).items():
        path, raw = args.root / name, encode(value)
        if args.verify:
            require(path.read_bytes() == raw, "generated output differs: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        print(("verified " if args.verify else "wrote ") + name)


if __name__ == "__main__":
    main()
