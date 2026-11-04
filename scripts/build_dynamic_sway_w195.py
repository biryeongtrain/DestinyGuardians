#!/usr/bin/env python3
"""Deterministically generate W195 Dynamic Sway Reduction; --verify is read-only."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons/"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
NAME, SLUG, BASE, ENHANCED, ROW = 'Dynamic Sway Reduction', 'dynamic-sway', 1359896290, 3060983774, 77
EXPECTED = [{'id': 'ammit_ar2', 'hash': 2119346509, 'socket': 3, 'perkHash': 1359896290, 'plugSetHash': 1723759242}, {'id': 'hammerhead', 'hash': 603242241, 'socket': 3, 'perkHash': 1359896290, 'plugSetHash': 2515290473}]
MECHANICS = {'id': 'dynamic_sway_reduction', 'hash': 1359896290, 'maxStacks': 10, 'stabilityPerShot': 1, 'growthReductionPerShot': 0.1, 'intermediateAccuracyConeSize': '?', 'maximumAccuracyScalar': 0, 'requiresHeldTrigger': True}
DDC_TEXT = ['While holding down the trigger:', '+1 Stability per shot.', '-100% Accuracy Cone Growth', 'removes all bullet spread']
PINS = {'/tmp/destiny-weapons-w30/bungie-items.json': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c', '/tmp/destiny-weapons-w60/bungie-plugsets.json': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959', '/tmp/destiny-weapons-w60/manifest.json': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce', '/private/tmp/destiny-w190/ddc-perks.html': '8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437', 'src/main/resources/destiny/weapons/w30.json': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a', 'src/main/resources/destiny/weapons/w40-characteristics.json': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1', 'src/main/resources/destiny/weapons/w83-exotics.json': 'bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56', 'src/main/resources/destiny/weapons/w84-exotics.json': '481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e'}
NOTE = '# W195 Dynamic Sway Reduction\n\nBase Trait 1359896290 only; enhanced 3060983774 excluded; no default selected trait.\nDDC Weapon Perks row 77; source.json preserves the exact raw HTML row including\nall yellow enhanced spans. HTML SHA256:\n8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437.\nAll 65 canonical catalog entries scanned, including exotic exclusions, against the\npinned official manifest. Only real randomized plugsets (isFakePlugSet=false),\ncurrentlyCanRoll=true and exact base Trait qualify. Exact tuples:\n[\n  {\n    "id": "ammit_ar2",\n    "hash": 2119346509,\n    "socket": 3,\n    "perkHash": 1359896290,\n    "plugSetHash": 1723759242\n  },\n  {\n    "id": "hammerhead",\n    "hash": 603242241,\n    "socket": 3,\n    "perkHash": 1359896290,\n    "plugSetHash": 2515290473\n  }\n]\nSource input hashes, complete definitions, scan and pool proofs are in source.json.\nRegenerate with scripts/build_dynamic_sway_w195.py --root <worktree>; --verify is read-only.\n\nConfirmed base: while continuously holding trigger, each paid shot adds +1 Stability\nand subtracts 10% Accuracy Cone Growth, capped at +10 and -100% at ten shots.\nThe intermediate Accuracy Cone Size curve is `?` UNKNOWN. Preserve incoming cone\nsize (scalar 1) below ten shots; at maximum return 0 because the DDC explicitly\nsays all bullet spread is removed. Do not interpolate or invent a percentage.\nThis is a provisional Minecraft mapping of that explicit maximum wording.\nNo timer is invented. Enhanced eight-shot ramp/-12.5% growth are excluded.\n\nSettled integration API (master owns all shared integration):\n- Register DynamicSwayProfile.ID/HASH/rolls; both real socket3 tuples only.\n- WeaponDynamicSway.paid(p, entry) AFTER actual payment, BEFORE trace/recoil.\n  Only actual paid emissions call it; duplicate input/polling never does.\n- stabilityBonus(p, token), accuracyScalar(p, token), growthScalar(p, token)\n  are pure captured shot snapshots. stabilityBonus(p) is the pure live contribution\n  for incoming flinch; stacks(p) is diagnostic. No writes in queries.\n- released(p, stack) on actual held release, including State.releaseHold lease\n  expiry, reload and cancel. Resets the chain and revokes its tokens immediately.\n- stowing(p, outgoing) resets before vanilla slot selection; update(p) also drops\n  unheld chains. changed/edited revoke same-tick tokens. cleanup/clear on lifecycle.\n  Tokens require the original held canonical selected tuple throughout evaluation.\n- No shared Aiming/Handling/Runtime/registry/HUD writes are included here.\n'

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
