#!/usr/bin/env python3
"""Offline W194 base Relentless Strikes extraction. --verify is read-only."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons"
TARGET = PREFIX + "/w194-relentless-strikes.json"
SOURCE = "art/weapons/w194/relentless-strikes/source.json"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
DDC_SHA = "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437"
NAME, BASE, ENHANCED, ROW = 'Relentless Strikes', 1749209109, 4085959009, 182
TRAIT = 4241085061
KEYS = ("id", "hash", "socket", "perkHash", "plugSetHash")
EXPECTED = [dict(zip(KEYS, r)) for r in [['abide_the_return', 1644160541, 3, 1749209109, 211008653], ['goldtusk', 3371413057, 3, 1749209109, 1162279549], ['crown_splitter', 2782325302, 3, 1749209109, 427353656], ['falling_guillotine', 614426548, 3, 1749209109, 2228304432], ['temptation_s_hook', 35794111, 3, 1749209109, 4018960212]]]
PERK = {'id': 'relentless_strikes', 'hash': 1749209109, 'hits': 3, 'windowTicks': 40, 'returnRounds': 1}
POLICY = 'Base DDC: three powered sword hits with each successive gap at most 2 seconds. Local mapping: 20 server ticks per second; inclusive 40-tick gap; reset after reward. Cleave counts each actually damaged target once per paid contact; direct/explosion share that contact. Counters survive stow; time still passes. Only confirmed positive finite actual HP/absorption loss generates loaded ammunition, never reserve transfer. Bounded local ledger retains latest 128 accepted contacts and 256 target identities per contact; evicted contacts never become eligible again.'


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
    require(all(term in row_text for term in ['182 Relentless Strikes', '3 Powered Sword Hits', '2 ↑3 seconds', 'Generates +1 Ammo']), "DDC row and base values")
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
    require(found == EXPECTED, "exact assigned base sword socket rolls")
    require(all(catalog[r["id"]]["family"] == "sword" for r in found), "sword-only family")
    require({k: v["sha256"] for k, v in pins.items()} == {'manifest': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce', 'inventory': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c', 'plugsets': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959', 'ddc': '8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437', 'src/main/resources/destiny/weapons/w40-characteristics.json': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1', 'src/main/resources/destiny/weapons/w30.json': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a', 'src/main/resources/destiny/weapons/w83-exotics.json': 'bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56', 'src/main/resources/destiny/weapons/w84-exotics.json': '481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e'}, "all pinned source hashes")
    components = manifest["jsonWorldComponentContentPaths"]["en"]
    provenance = {"version": VERSION, "manifestComponents": {k: components[k] for k in
                  ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
                  "inputSHA": pins, "rawHTML": raw_row, "rowText": row_text,
                  "socketProof": proof}
    resource = {"stage": "W194", "perk": PERK, "weapons": found, "source": provenance}
    evidence = {"stage": "W194", **provenance, "ddc": {"row": ROW, "tab": "Weapon Perks",
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
