#!/usr/bin/env python3
"""Offline W193 base Clown Cartridge extraction. --verify is read-only."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons"
TARGET = PREFIX + "/w193-clown-cartridge.json"
SOURCE = "art/weapons/w193/clown-cartridge/source.json"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
DDC_SHA = "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437"
NAME, BASE, ENHANCED, ROW = "Clown Cartridge", 2284787283, 3563868667, 48
TRAIT = 4241085061
KEYS = ("id", "hash", "socket", "perkHash", "plugSetHash")
EXPECTED = [dict(zip(KEYS, r)) for r in [["line_in_the_sand",946443267,4,2284787283,3257645194],["stormchaser",3652506829,3,2284787283,897699284],["canis_major",2066434718,3,2284787283,4037911937]]]
PERK = {"id":"clown_cartridge","hash":2284787283,"minimumBonusPercent":10,"maximumBonusPercent":50,"sampling":"uniform_integer_inclusive"}
POLICY = "DDC specifies the range and rounding but not discreteness. Local policy samples one uniform integer percentage from 10 through 50 inclusive, only after successful timed reload ammo credit."


def require(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def generate(args):
    pins = {}

    def read(path, key=None, text=False):
        raw = path.read_bytes()
        pins[key or path.relative_to(args.root).as_posix()] = {
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        return raw.decode("utf-8") if text else json.loads(raw)

    manifest = read(args.manifest, "manifest")["Response"]
    require(manifest["version"] == VERSION, "pinned official manifest")
    inventory = read(args.inventory, "inventory")
    pools = read(args.plugsets, "plugsets")
    require({v["hash"] for v in inventory.values()
             if v.get("displayProperties", {}).get("name") == NAME} == {BASE, ENHANCED},
            "exact base and enhanced definitions")
    require(inventory[str(BASE)]["itemTypeDisplayName"] == "Trait"
            and inventory[str(ENHANCED)]["itemTypeDisplayName"] == "Enhanced Trait", "definition types")
    ddc = read(args.ddc, "ddc", text=True)
    require(pins["ddc"]["sha256"] == DDC_SHA, "pinned DDC SHA256")
    rows = [r for r in re.findall(r"<tr\b[^>]*>.*?</tr>", ddc, re.S)
            if any(html.unescape(re.sub(r"<[^>]+>", "", cell)).strip() == NAME
                   for cell in re.findall(r"<td\b[^>]*>(.*?)</td>", r, re.S))]
    require(len(rows) == 1, "unique exact DDC name cell")
    raw_row = rows[0]
    row_text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw_row)).split())
    require(all(term in row_text for term in ["48 Clown Cartridge","Upon finishing a reload","10% ↑13% to 50% Increased Magazine Capacity","Always rounds up","30% ↑31.5%"]), "DDC row and base values")
    selected = read(args.root / PREFIX / "w40-characteristics.json")
    catalog_rows = read(args.root / PREFIX / "w30.json")
    for filename in ("w83-exotics.json", "w84-exotics.json"):
        exotics = read(args.root / PREFIX / filename)
        selected += [r["characteristics"] for r in exotics]
        catalog_rows += [r["catalog"] for r in exotics]
    catalog = {w["id"]: w for w in catalog_rows}
    require(len(selected) == len({w["bungieHash"] for w in selected})
            == len(catalog_rows) == len(catalog) == 65
            and {w["id"] for w in selected} == set(catalog), "exact catalog65")
    found, scans, proof = [], [], []
    for w in selected:
        item = inventory[str(w["bungieHash"])]
        name = catalog[w["id"]]["name"]
        if w["id"] == "parcel_of_stardust_fell_to_earth":
            name = "Parcel of Stardust"  # Catalog label distinguishes the local prototype frame.
        require(item["hash"] == w["bungieHash"] and item["displayProperties"]["name"] == name,
                "canonical weapon identity " + w["id"])
        sockets = item["sockets"]
        traits = {n for c in sockets["socketCategories"] if c["socketCategoryHash"] == TRAIT
                  for n in c["socketIndexes"]}
        matches = []
        for n in sorted(traits):
            entry = sockets["socketEntries"][n]
            ph = entry.get("randomizedPlugSetHash")
            pool = pools.get(str(ph), {})
            plug = inventory[str(BASE)]
            if (w["exotic"] or pool.get("isFakePlugSet") is not False
                    or plug.get("plug", {}).get("isDummyPlug") is not False
                    or plug.get("redacted") or plug.get("blacklisted")
                    or not any(p.get("currentlyCanRoll") is True and p["plugItemHash"] == BASE
                               for p in pool.get("reusablePlugItems", []))):
                continue
            roll = dict(zip(KEYS, (w["id"], w["bungieHash"], n, BASE, ph)))
            matches.append(roll)
            proof.append({"roll": roll, "socketCategories": sockets["socketCategories"],
                          "socketEntry": entry, "plugSet": pool})
        found += matches
        scans.append({"id": w["id"], "hash": w["bungieHash"], "matches": matches})
    candidates = read(args.candidates, "candidates")[NAME]
    require(found == EXPECTED == candidates, "exact assigned three base socket rolls")
    components = manifest["jsonWorldComponentContentPaths"]["en"]
    provenance = {"version": VERSION, "manifestComponents": {k: components[k] for k in
                  ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
                  "inputSHA": pins, "rawRow": raw_row, "rowText": row_text,
                  "socketProof": proof}
    resource = {"stage": "W193", "perk": PERK, "weapons": found, "source": provenance}
    evidence = {"stage": "W193", **provenance, "ddc": {"row": ROW, "tab": "Weapon Perks",
                "url": "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278"},
                "catalogScan": scans, "enhancedExcludedHash": ENHANCED, "localPolicy": POLICY,
                "resourceSHA256": hashlib.sha256(encode(resource)).hexdigest()}
    return {TARGET: resource, SOURCE: evidence}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    p.add_argument("--plugsets", type=Path, default=Path("/tmp/destiny-weapons-w60/bungie-plugsets.json"))
    p.add_argument("--manifest", type=Path, default=Path("/tmp/destiny-weapons-w60/manifest.json"))
    p.add_argument("--ddc", type=Path, default=Path("/private/tmp/destiny-w190/ddc-perks.html"))
    p.add_argument("--candidates", type=Path, default=Path("/private/tmp/destiny-w193/remaining-sockets.json"))
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
