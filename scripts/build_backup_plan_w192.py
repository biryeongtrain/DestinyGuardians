#!/usr/bin/env python3
"""Offline deterministic base Backup Plan extraction. --verify never writes."""
import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons/"
TARGET = PREFIX + "w192-backup-plan.json"
SOURCE = "art/weapons/w192/backup-plan/source.json"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
DDC_SHA = "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437"
BASE, ENHANCED, TRAIT = 1600092898, 828056542, 4241085061
KEYS = ("id", "hash", "socket", "perkHash", "plugSetHash")
EXPECTED = [dict(zip(KEYS, r)) for r in (
    ("hollow_words", 607191995, 4, BASE, 1485010760),
    ("dream_breaker", 2931957300, 4, BASE, 1206254527),
    ("line_in_the_sand", 946443267, 4, BASE, 3257645194))]
# Explicit frozen input list: output does not depend on directory iteration or another W192 worker.
PROFILES = ("w60-holster.json", "w66-rampage.json", "w68-snapshot.json", "w77-dragonfly.json",
            "w108-feeding-frenzy.json", "w109-surrounded.json", "w169-rapid-hit.json",
            "w171-tap-the-trigger.json", "w172-frenzy.json", "w177-heating-up.json",
            "w178-threat-detector.json", "w181-vorpal.json", "w182-high_impact_reserves.json",
            "w185-quickdraw.json", "w187-lead_from_gold.json", "w189-firmly_planted.json",
            "w190-under-pressure.json", "w191-firing-line.json", "w191-wellspring.json")


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
    require(manifest["version"] == VERSION, "pinned manifest version")
    inventory = read(args.inventory, "inventory")
    pools = read(args.plugsets, "plugsets")
    require({v["hash"] for v in inventory.values()
             if v.get("displayProperties", {}).get("name") == "Backup Plan"} == {BASE, ENHANCED},
            "exact base/enhanced definitions")
    require(inventory[str(BASE)]["itemTypeDisplayName"] == "Trait"
            and inventory[str(ENHANCED)]["itemTypeDisplayName"] == "Enhanced Trait", "trait types")
    ddc = read(args.ddc, "ddc", text=True)
    require(pins["ddc"]["sha256"] == DDC_SHA, "pinned DDC SHA256")
    rows = [row for row in re.findall(r"<tr\b[^>]*>.*?</tr>", ddc, re.S)
            if any(html.unescape(re.sub(r"<[^>]+>", "", cell)).strip() == "Backup Plan"
                   for cell in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S))]
    require(len(rows) == 1, "unique exact Backup Plan name cell")
    raw_row = rows[0]
    row_text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw_row)).split())
    require(row_text.startswith("24 Backup Plan") and all(s in row_text for s in
            ("20% decreased damage", "+100 Handling", "0.7x Charge Time Multiplier",
             "2 ↑2.5 seconds", "Linear Fusion Rifle exclusive : Shooting refreshes the buff duration.",
             "Weapon must be stowed for 3 seconds")), "row24 base values and enhanced annotation")
    selected = read(args.root / PREFIX / "w40-characteristics.json")
    for file in ("w83-exotics.json", "w84-exotics.json"):
        selected += [r["characteristics"] for r in read(args.root / PREFIX / file)]
    require(len(selected) == len({r["bungieHash"] for r in selected}) == 65, "catalog65")
    catalog = {w["id"]: w for w in read(args.root / PREFIX / "w30.json")}
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
    candidates = read(args.candidates, "candidates")["Backup Plan"]
    require(found == EXPECTED == candidates, "exact three base rolls")
    pairs, audit = [], []
    for file in PROFILES:
        d = read(args.root / PREFIX / file)
        if "perk" in d:
            groups = [(d["perk"]["id"], d["weapons"])]
        elif "perks" in d:
            groups = [(p["id"], p["weapons"]) for p in d["perks"]]
        else:
            groups = [("snapshot_sights", d["rolls"])]
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
                  {"frenzy", "quickdraw", "threat_detector", "snapshot_sights"}}
    require(stat_pairs == {("hollow_words", "quickdraw"), ("dream_breaker", "snapshot_sights"),
                           ("dream_breaker", "threat_detector"), ("line_in_the_sand", "threat_detector")},
            "legal handling composition")
    mapping = {r["id"]: r for r in read(args.root / "art/weapons/w43/extraction.json")["entries"]}
    formulas = read(args.root / "art/weapons/w46/weapon_formulas.json")
    handling = {r["id"]: r["profile"] for r in read(args.root / PREFIX / "w58-handling.json")}
    aim = {r["id"]: r["profile"] for r in read(args.root / PREFIX / "w44-aim.json")}
    timing = {r["id"]: r["timing"] for r in read(args.root / PREFIX / "w46-timing.json")}
    snapshot = read(args.root / PREFIX / "w68-snapshot.json")
    quickdraw = read(args.root / PREFIX / "w185-quickdraw.json")
    require(snapshot["specialScalar"] == .8 and quickdraw["perk"]["readyScalar"] == .95, "companion scalars")
    curves, proof = [], []
    for r in found:
        w, item, m = by_id[r["id"]], inventory[str(r["hash"])], mapping[r["id"]]
        raw = formulas[m["family"]]["cat"][m["category"]]["handling"]
        c = {"id": r["id"], "baseHandlingStat": w["stats"]["943549884"],
             "chargeMillis": w["stats"]["2961396640"],
             "linearFusion": catalog[r["id"]]["family"] == "linear_fusion_rifle",
             "snapshotScalar": .8 if (r["id"], "snapshot_sights") in stat_pairs else None,
             "quickdrawReadyScalar": .95 if (r["id"], "quickdraw") in stat_pairs else None}
        require(c["baseHandlingStat"] == item["stats"]["stats"]["943549884"]["value"]
                and c["chargeMillis"] == item["stats"]["stats"]["2961396640"]["value"]
                == timing[r["id"]]["chargeMillis"], "official raw handling and charge milliseconds")
        for key in ("ready", "stow", "ads"):
            c[key] = {k: raw[key].get(k, 0.0) for k in ("evpp", "vpp", "offset")}
        def solve(key):
            return sum(c[key][k] * x for k, x in
                       (("evpp", c["baseHandlingStat"] ** 2), ("vpp", c["baseHandlingStat"]), ("offset", 1)))
        require(math.ceil(solve("ready") * 20) == handling[r["id"]]["readyTicks"]
                and math.ceil(solve("stow") * 20) == handling[r["id"]]["stowTicks"]
                and max(2, min(20, math.ceil(solve("ads") * 20))) == aim[r["id"]]["transitionTicks"],
                "historical raw curve baseline")
        curves.append(c)
        sockets = []
        for n in sorted(traits(item)):
            e = item["sockets"]["socketEntries"][n]
            ph = e.get("randomizedPlugSetHash")
            if ph is not None:
                sockets.append({"socket": n, "entry": e, "plugSet": pools[str(ph)]})
        proof.append({"id": r["id"], "hash": r["hash"],
                      "socketCategories": item["sockets"]["socketCategories"], "sockets": sockets})
    components = manifest["jsonWorldComponentContentPaths"]["en"]
    provenance = {"version": VERSION, "manifestComponents": {k: components[k] for k in
                  ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
                  "inputSHA": pins, "rawRow": raw_row, "rowText": row_text, "socketProof": proof}
    resource = {"stage": "W192", "perk": {"id": "backup_plan", "hash": BASE,
                "damageMultiplier": .8, "handlingBonus": 100, "chargeTimeMultiplier": .7,
                "durationTicks": 40, "stowTicks": 60}, "weapons": found, "curves": curves,
                "coSelections": pairs, "source": provenance}
    evidence = {"stage": "W192", **provenance, "ddc": {"row": 24, "tab": "Weapon Perks",
                "url": "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278"},
                "catalogScan": scans, "companionAudit": audit, "curves": curves,
                "historicalOracleCommit": "dcd0c7d302b056ffbb532edcb711d724a17ca8c1",
                "enhancedExcludedHash": ENHANCED, "enhancedDurationExcludedTicks": 50,
                "resourceSHA256": hashlib.sha256(encode(resource)).hexdigest()}
    return {TARGET: resource, SOURCE: evidence}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    p.add_argument("--plugsets", type=Path, default=Path("/tmp/destiny-weapons-w60/bungie-plugsets.json"))
    p.add_argument("--manifest", type=Path, default=Path("/tmp/destiny-weapons-w60/manifest.json"))
    p.add_argument("--ddc", type=Path, default=Path("/private/tmp/destiny-w190/ddc-perks.html"))
    p.add_argument("--candidates", type=Path, default=Path("/private/tmp/destiny-w192/base-sockets.json"))
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
