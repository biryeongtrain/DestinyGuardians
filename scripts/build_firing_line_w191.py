#!/usr/bin/env python3
"""Build only W191 base Firing Line from pinned local DDC and official manifest inputs."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

VERSION = "245114.26.10.13.2000-1-bnet.66137"
BASE = 1771339417
CATEGORY = 4241085061
EXPECTED = [
    {"id": "line_in_the_sand", "hash": 946443267, "socket": 4, "perkHash": BASE, "plugSetHash": 3257645194},
    {"id": "stormchaser", "hash": 3652506829, "socket": 4, "perkHash": BASE, "plugSetHash": 4213354588},
    {"id": "fixed_odds", "hash": 2194955522, "socket": 4, "perkHash": BASE, "plugSetHash": 1686775256},
]


def load(path):
    return json.loads(path.read_text())


def plain(value):
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    paths = {
        "inventory": Path("/tmp/destiny-weapons-w30/bungie-items.json"),
        "plugsets": Path("/tmp/destiny-weapons-w60/bungie-plugsets.json"),
        "manifest": Path("/tmp/destiny-weapons-w60/manifest.json"),
        "candidates": Path("/private/tmp/destiny-w191/sockets.json"),
        "ddc": Path("/private/tmp/destiny-w190/ddc-perks.html"),
        "catalog": root / "src/main/resources/destiny/weapons/w40-characteristics.json",
    }
    manifest = load(paths["manifest"])["Response"]
    assert manifest["version"] == VERSION, "Use the pinned manifest; do not refresh the whole manifest"
    inventory = load(paths["inventory"])
    pools = load(paths["plugsets"])
    catalog = {w["id"]: w for w in load(paths["catalog"])}
    rolls = load(paths["candidates"])["firing_line"]
    assert rolls == EXPECTED, "Only the three assigned exact candidate rolls"
    perk = inventory[str(BASE)]
    assert perk["displayProperties"]["name"] == "Firing Line"
    assert perk["itemTypeDisplayName"] == "Trait"  # Enhanced Trait is a different item.
    proofs = []
    for roll in rolls:
        weapon = catalog[roll["id"]]
        assert weapon["bungieHash"] == roll["hash"] and not weapon["exotic"]
        item = inventory[str(roll["hash"])]
        assert item["inventory"]["tierType"] == 5
        sockets = item["sockets"]
        category = next(c for c in sockets["socketCategories"]
                        if c["socketCategoryHash"] == CATEGORY and roll["socket"] in c["socketIndexes"])
        socket = sockets["socketEntries"][roll["socket"]]
        assert socket["randomizedPlugSetHash"] == roll["plugSetHash"]
        pool = pools[str(roll["plugSetHash"])]
        assert pool["isFakePlugSet"] is False
        matches = [plug for plug in pool["reusablePlugItems"]
                   if plug["plugItemHash"] == BASE and plug.get("currentlyCanRoll") is True]
        assert len(matches) == 1
        proofs.append({"roll": roll, "weaponName": item["displayProperties"]["name"],
                       "socketCategory": category, "socketEntry": socket,
                       "isFakePlugSet": pool["isFakePlugSet"], "matchingPlug": matches[0]})
    rows = [row for row in re.findall(r"<tr\b[^>]*>.*?</tr>", paths["ddc"].read_text(), re.S)
            if any(plain(cell) == "Firing Line" for cell in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S))]
    assert len(rows) == 1, "Exact td name match, not a substring match"
    row = rows[0]
    cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S)
    description = plain(cells[-1])
    assert 'id="1662574278R95"' in row
    assert "15 metres" in description and "2 allies" in description
    assert "20% Increased Precision Damage." in description
    provenance = {
        "date": "2026-10-27", "officialManifest": VERSION,
        "inputs": {name: {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                   for name, path in paths.items()},
        "ddc": {"url": "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278",
                "tab": "Weapon Perks", "row": 96, "name": "Firing Line", "text": description, "html": row},
        "socketProofs": proofs, "baseValuesVerifiedFromDDC": True, "enhancedExcluded": True,
        "mapping": "15 metres = 15 blocks, finite inclusive 3D radius; two other alive connected nonspectator same-level players, same vanilla team or both unteamed. No LOS/chunk loads/attachments.",
        "limits": "Paid emission freezes ally eligibility; original owner/level/stack/selected roll revalidated on query, stow allowed while still owned/equipped. No live buff timer, linger or enhanced +10 Handling. Master integrates precision component only; body/splash/abilities excluded.",
    }
    resource = {"stage": "W191", "perk": {"id": "firing_line", "hash": BASE, "radiusBlocks": 15,
                "requiredAllies": 2, "precisionMultiplier": 1.2}, "weapons": rolls, "source": provenance}
    source = {**provenance, "perkDefinition": perk}
    for relative, data in [("src/main/resources/destiny/weapons/w191-firing-line.json", resource),
                           ("art/weapons/w191/firing-line/source.json", source)]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("Firing Line: DDC row96, 15m / 2 allies / +20% precision only; three exact base sockets verified.")


if __name__ == "__main__":
    main()
