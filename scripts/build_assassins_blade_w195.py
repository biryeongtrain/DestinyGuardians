#!/usr/bin/env python3
"""Deterministically generate W195 Assassin's Blade; --verify is read-only."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons/"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
NAME, SLUG, BASE, ENHANCED, ROW = "Assassin's Blade", 'assassins-blade', 354401740, 3678483220, 21
EXPECTED = [{'id': 'abide_the_return', 'hash': 1644160541, 'socket': 3, 'perkHash': 354401740, 'plugSetHash': 211008653}, {'id': 'abide_the_return', 'hash': 1644160541, 'socket': 4, 'perkHash': 354401740, 'plugSetHash': 2761485963}, {'id': 'goldtusk', 'hash': 3371413057, 'socket': 3, 'perkHash': 354401740, 'plugSetHash': 1162279549}]
MECHANICS = {'id': 'assassins_blade', 'hash': 354401740, 'damageMultiplier': 1.15, 'durationTicks': 100, 'persistsStow': True, 'movement': 'maximize Movement Speed', 'destinyMovementAlgorithm': 'unknown'}
DDC_TEXT = ['15% Increased damage and maximizes Movement Speed for 5', 'Additional Weapon Kills refresh', 'Buff remains active while stowed.']
PINS = {'/tmp/destiny-weapons-w30/bungie-items.json': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c', '/tmp/destiny-weapons-w60/bungie-plugsets.json': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959', '/tmp/destiny-weapons-w60/manifest.json': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce', '/private/tmp/destiny-w190/ddc-perks.html': '8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437', 'src/main/resources/destiny/weapons/w30.json': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a', 'src/main/resources/destiny/weapons/w40-characteristics.json': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1', 'src/main/resources/destiny/weapons/w83-exotics.json': 'bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56', 'src/main/resources/destiny/weapons/w84-exotics.json': '481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e'}
NOTE = '# W195 Assassin\'s Blade\n\nBase Trait 354401740 only; enhanced 3678483220 excluded; no default selected trait.\nDDC Weapon Perks row 21; source.json preserves the exact raw HTML row including\nall yellow enhanced spans. HTML SHA256:\n8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437.\nAll 65 canonical catalog entries scanned, including exotic exclusions, against the\npinned official manifest. Only real randomized plugsets (isFakePlugSet=false),\ncurrentlyCanRoll=true and exact base Trait qualify. Exact tuples:\n[\n  {\n    "id": "abide_the_return",\n    "hash": 1644160541,\n    "socket": 3,\n    "perkHash": 354401740,\n    "plugSetHash": 211008653\n  },\n  {\n    "id": "abide_the_return",\n    "hash": 1644160541,\n    "socket": 4,\n    "perkHash": 354401740,\n    "plugSetHash": 2761485963\n  },\n  {\n    "id": "goldtusk",\n    "hash": 3371413057,\n    "socket": 3,\n    "perkHash": 354401740,\n    "plugSetHash": 1162279549\n  }\n]\nSource input hashes, complete definitions, scan and pool proofs are in source.json.\nRegenerate with scripts/build_assassins_blade_w195.py --root <worktree>; --verify is read-only.\n\nConfirmed base: actual sword weapon final blow grants +15% damage and maximizes\nMovement Speed for five seconds (100 Minecraft ticks); further actual kills refresh.\nBuff persists while stowed. Enhanced 5.5-second duration is excluded.\nThe exact Destiny movement algorithm is UNKNOWN; this helper returns only a\nsource-backed active flag. Master owns a provisional native Minecraft locomotion\nmapping. Do not invent a Mobility stat, movement percentage or attribute write here.\n\nSettled integration API (master owns all shared integration):\n- Register AssassinsBladeProfile.ID/HASH/rolls. Abide has TWO legal source tuples;\n  preserve either exact selected tuple, plus Goldtusk socket3. No arbitrary name hash.\n- capture(p) AFTER actual paid nonempty sword acceptance and BEFORE own damage/kill.\n  Carry the SAME opaque Token to direct/cleave/splash. Never recapture on explosion.\n- multiplier(p, token) is pure pre-own-kill damage; it only benefits the original\n  accepted original selected source sword, including its paid in-flight caster shot\n  after ordinary stow. A later alternate weapon never gains damage.\n- killed(p, token, target) AFTER positive actual HP/absorption loss AND attributable\n  eligible enemy final blow. Generic deaths/abilities/empty swords never call it.\n  One corpse counts once per paid token, with a 256-target never-evicting bound.\n- remaining(p) returns maximum unexpired ticks across all still owned canonical\n  sources including stowed swords; active(p) == remaining(p)>0 for movement only.\n- update(p) retains ordinary stow. Optional stowing(p, outgoing) retains buff while\n  blocking transient outgoing damage evaluation before vanilla changes selection.\n- edited(stack)/changed(p,stack) revoke same-tick tokens and that source buff,\n  including while stowed. Removed/noncanonical/count!=1 sources are inert immediately.\n- cleanup(p)/clear() revoke lifecycle; old ServerPlayer cleanup cannot remove a\n  successor. Identity/level/data/runtime/class/Super/loadout checks are pure.\n'

def require(ok, detail):
    if not ok:
        raise ValueError(detail)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()

def plain(raw):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())

def build(root):
    data, inputs = {}, {}
    for name, pin in PINS.items():
        raw = (root / name).read_bytes()
        require(digest(raw) == pin, "Pinned input drift: " + name)
        inputs[name] = dict(sha256=pin, bytes=len(raw))
        data[name] = json.loads(raw) if name.endswith(".json") else raw.decode()
    inventory = data["/tmp/destiny-weapons-w30/bungie-items.json"]
    pools = data["/tmp/destiny-weapons-w60/bungie-plugsets.json"]
    manifest = data["/tmp/destiny-weapons-w60/manifest.json"]["Response"]
    require(manifest["version"] == VERSION, "manifest version")
    perk = inventory[str(BASE)]
    require(perk["hash"] == BASE and perk["displayProperties"]["name"] == NAME
            and perk["itemTypeDisplayName"] == "Trait" and perk["itemType"] == 19
            and perk["plug"]["isDummyPlug"] is False and not perk.get("redacted")
            and not perk.get("blacklisted"), "exact usable base Trait")
    require(inventory[str(ENHANCED)]["itemTypeDisplayName"] == "Enhanced Trait", "enhanced exclusion")
    rows = [row for row in re.findall(r"<tr\b[^>]*>.*?</tr>", data["/private/tmp/destiny-w190/ddc-perks.html"], re.S)
            if any(plain(cell) == NAME for cell in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S))]
    require(len(rows) == 1 and f'id="1662574278R{ROW-1}"' in rows[0], "unique exact DDC td name/row")
    raw_row = rows[0]
    description = plain(re.findall(r"<td\b[^>]*>(.*?)</td>", raw_row, re.S)[-1])
    require(all(value in description for value in DDC_TEXT), "base DDC mechanics")
    require("#ffd966" in raw_row, "retain yellow enhanced distinction")
    stats = list(data[PREFIX + "w40-characteristics.json"])
    catalog = list(data[PREFIX + "w30.json"])
    for name in ("w83-exotics.json", "w84-exotics.json"):
        stats.extend(e["characteristics"] for e in data[PREFIX + name])
        catalog.extend(e["catalog"] for e in data[PREFIX + name])
    require(len(stats) == len(catalog) == len({w["id"] for w in stats}) == 65, "canonical catalog65")
    require({w["id"] for w in catalog} == {w["id"] for w in stats}, "catalog/stats identity")
    found, proofs, scan = [], [], []
    for weapon in stats:
        item = inventory[str(weapon["bungieHash"])]
        sockets = item["sockets"]
        categories = [c for c in sockets["socketCategories"] if c["socketCategoryHash"] == 4241085061]
        matches = []
        for index in sorted({i for c in categories for i in c["socketIndexes"]}):
            socket = sockets["socketEntries"][index]
            ph = socket.get("randomizedPlugSetHash")
            pool = pools.get(str(ph), {})
            if pool.get("isFakePlugSet") is not False:
                continue
            for plug in pool.get("reusablePlugItems", []):
                definition = inventory.get(str(plug["plugItemHash"]), {})
                if (plug.get("currentlyCanRoll") is not True
                    or definition.get("itemTypeDisplayName") != "Trait" or plug["plugItemHash"] != BASE):
                    continue
                require(not weapon["exotic"] and item["inventory"]["tierType"] == 5, "legendary real pool")
                roll = dict(id=weapon["id"], hash=weapon["bungieHash"], socket=index,
                            perkHash=BASE, plugSetHash=ph)
                found.append(roll)
                matches.append(roll)
                proofs.append(dict(roll=roll, socketCategories=categories, socketEntry=socket,
                                   plugSet=pool, matchingPlug=plug))
        scan.append(dict(id=weapon["id"], hash=weapon["bungieHash"], exotic=weapon["exotic"], matches=matches))
    require(found == EXPECTED, "exhaustive exact canonical pool")
    resource = dict(stage="W195", perk=MECHANICS, weapons=found)
    resource_raw = encode(resource)
    source = dict(stage="W195", checked="2026-10-27", manifestVersion=VERSION, sourcePins=inputs,
                  generatorSHA256=digest(Path(__file__).read_bytes()), resourceSHA256=digest(resource_raw),
                  manifestComponents={k: manifest["jsonWorldComponentContentPaths"]["en"][k] for k in
                                      ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
                  perkDefinition=perk, enhancedExcludedHash=ENHANCED,
                  ddc=dict(url="https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278",
                           tab="Weapon Perks", row=ROW, name=NAME, rawHTML=raw_row, text=description),
                  catalogScan=scan, socketProofs=proofs)
    return {PREFIX + "w195-" + SLUG + ".json": resource_raw,
            "art/weapons/w195/" + SLUG + "/source.json": encode(source),
            "art/weapons/w195/" + SLUG + "/SOURCE.md": NOTE.encode()}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    for name, raw in build(args.root.resolve()).items():
        path = args.root / name
        if args.verify:
            require(path.read_bytes() == raw, "Generated output drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        print(("verified " if args.verify else "wrote ") + name)

if __name__ == "__main__":
    main()
