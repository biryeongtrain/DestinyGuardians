#!/usr/bin/env python3
"""Build W192 base Rangefinder from pinned DDC, official sockets and existing W43 curves."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

VERSION = "245114.26.10.13.2000-1-bnet.66137"
DDC_SHA256 = "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437"
BASE = 2846385770
CATEGORY = 4241085061
EXPECTED = [
    ("duke_mk_44", 2112909414, 2, 3744182842),
    ("austringer", 3055790362, 4, 785215120),
    ("bygones", 2712244741, 3, 1760176771),
    ("chattering_bone", 568515759, 3, 216806616),
    ("claws_of_the_wolf", 1280933460, 4, 753756428),
    ("allied_demand", 1532276803, 3, 3275836355),
    ("farewell", 541188001, 3, 284168234),
    ("dead_man_walking_xx7463", 3751622019, 4, 1210839935),
    ("biting_winds", 1621657423, 4, 2763203653),
    ("whispering_slab", 211938782, 3, 1885424927),
    ("apostate", 2164448701, 3, 1306932196),
    ("dream_breaker", 2931957300, 3, 3785896921),
    ("coriolis_force", 3512349612, 4, 753624012),
    ("line_in_the_sand", 946443267, 3, 1503774254),
    ("stormchaser", 3652506829, 3, 897699284),
    ("edge_transit", 218335759, 3, 447678063),
    ("bellowing_giant", 2186258845, 3, 2605036073),
    ("fixed_odds", 2194955522, 4, 1686775256),
]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


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
        "candidates": Path("/private/tmp/destiny-w192/base-sockets.json"),
        "ddc": Path("/private/tmp/destiny-w190/ddc-perks.html"),
        "catalog": root / "src/main/resources/destiny/weapons/w40-characteristics.json",
        "curves": root / "src/main/resources/destiny/weapons/w43-ballistics.json",
    }
    assert load(paths["manifest"])["Response"]["version"] == VERSION
    assert hashlib.sha256(paths["ddc"].read_bytes()).hexdigest() == DDC_SHA256
    inventory = load(paths["inventory"])
    pools = load(paths["plugsets"])
    catalog = {w["id"]: w for w in load(paths["catalog"])}
    curves = {w["id"]: w for w in load(paths["curves"])}
    rolls = load(paths["candidates"])["Rangefinder"]
    expected = [dict(id=id_, hash=hash_, socket=socket, perkHash=BASE, plugSetHash=pool)
                for id_, hash_, socket, pool in EXPECTED]
    assert rolls == expected, "Only the 18 assigned base Trait rolls"
    perk = inventory[str(BASE)]
    assert perk["displayProperties"]["name"] == "Rangefinder"
    assert perk["itemTypeDisplayName"] == "Trait", "Enhanced Trait is excluded"
    proofs, ranges = [], []
    for roll in rolls:
        weapon = catalog[roll["id"]]
        assert weapon["bungieHash"] == roll["hash"] and not weapon["exotic"]
        item = inventory[str(roll["hash"])]
        assert item["inventory"]["tierType"] == 5
        sockets = item["sockets"]
        categories = [c for c in sockets["socketCategories"]
                      if c["socketCategoryHash"] == CATEGORY and roll["socket"] in c["socketIndexes"]]
        assert len(categories) == 1
        socket = sockets["socketEntries"][roll["socket"]]
        assert socket["randomizedPlugSetHash"] == roll["plugSetHash"]
        pool = pools[str(roll["plugSetHash"])]
        assert pool["isFakePlugSet"] is False
        matches = [p for p in pool["reusablePlugItems"]
                   if p["plugItemHash"] == BASE and p.get("currentlyCanRoll") is True]
        assert len(matches) == 1
        proofs.append({"roll": roll, "weaponName": item["displayProperties"]["name"],
                       "socketCategory": categories[0], "socketEntry": socket,
                       "isFakePlugSet": False, "matchingPlug": matches[0]})
        stat = weapon["stats"].get("1240592695")
        assert stat == item["stats"]["stats"].get("1240592695", {}).get("value")
        curve = curves[roll["id"]]
        assert stat is not None or (curve["vppStart"] == 0 and curve["vppEnd"] == 0)
        ranges.append({**curve, "baseRange": stat})
    rows = [row for row in re.findall(r"<tr\b[^>]*>.*?</tr>", paths["ddc"].read_text(), re.S)
            if any(plain(cell) == "Rangefinder"
                   for cell in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S))]
    assert len(rows) == 1, "Exact td name, never substring matching"
    row = rows[0]
    cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S)
    description = plain(cells[-1])
    assert 'id="1662574278R173"' in row
    assert "While ADS:+10 Range, 10% Increased Zoom and 5% Increased Projectile Velocity." in description
    assert "↑Passively grants +5 Handling" in description
    provenance = {
        "date": "2026-10-27", "officialManifest": VERSION,
        # Repository inputs use relative paths so relocating the isolated checkout changes no bytes.
        "inputs": {name: {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                   for name, path in paths.items()},
        "ddc": {"url": "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278",
                "tab": "Weapon Perks", "row": 174, "name": "Rangefinder", "text": description, "html": row},
        "socketProofs": proofs, "baseValuesVerifiedFromDDC": True, "enhancedExcluded": True,
        "mapping": "Range/speed use the existing scope boundary WeaponAiming.progress >= 0.5, with current crouch input, no handling/reload block and an actual matching owner/level/held-stack ADS session. Zoom exposes the selected held weapon target independently of ADS progress; existing FOV interpolation blends from zero without a 0.5 target jump. This threshold is Minecraft policy, not a DDC timing claim.",
        "rangeMapping": "Raw W43 hip curves and official base Range copied unchanged. Sum legal Range bonuses then clamp once to 0..100 before evaluating; apply existing ADS falloff scalar afterward. Zoom is visual only. Zero-slope sentinel curves stay unchanged; null Range is permitted only for zero slopes.",
        "limits": "Pure queries, no attachments/timers/lifecycle cache. Master registers the 18 exact rolls and integrates shared paths. Projectile speed is sampled once at accepted paid Shot creation; never query during flight or alter earlier projectiles. No enhanced +5 Handling, extra aim assist or inferred zoom-to-falloff scaling.",
    }
    resource = {"stage": "W192", "perk": {"id": "rangefinder", "hash": BASE,
                "rangeBonus": 10, "zoomScalar": 1.1, "projectileSpeedScalar": 1.05,
                "minAdsProgress": 0.5}, "weapons": rolls, "ranges": ranges, "source": provenance}
    source = {**provenance, "perkDefinition": perk, "ranges": ranges}
    for relative, data in [("src/main/resources/destiny/weapons/w192-rangefinder.json", resource),
                           ("art/weapons/w192/rangefinder/source.json", source)]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Rangefinder: DDC row174/hash verified; 18 exact base sockets; +10 Range / 1.10 zoom / 1.05 projectile speed while ADS.")


if __name__ == "__main__":
    main()
