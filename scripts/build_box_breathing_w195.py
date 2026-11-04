#!/usr/bin/env python3
"""Generate pinned W195 base Box Breathing; --verify compares bytes without writes."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 2551157718
ENHANCED = 23371658
VERSION = "245114.26.10.13.2000-1-bnet.66137"
PREFIX = "src/main/resources/destiny/weapons/"
ART = "art/weapons/w195/box-breathing/"
JAVA = "src/main/java/kim/biryeong/destiny/weapon/"
EXPECTED = [{'id': 'beloved', 'hash': 3107853529, 'socket': 4, 'perkHash': 2551157718, 'plugSetHash': 887157889}, {'id': 'apostate', 'hash': 2164448701, 'socket': 4, 'perkHash': 2551157718, 'plugSetHash': 2826016044}]
PINS = {
    "/tmp/destiny-weapons-w30/bungie-items.json": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "/tmp/destiny-weapons-w60/bungie-plugsets.json": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "/tmp/destiny-weapons-w60/manifest.json": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "/private/tmp/destiny-w190/ddc-perks.html": "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437",
    PREFIX + "w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    PREFIX + "w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    PREFIX + "w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    PREFIX + "w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
}

def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def plain(value):
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def generate(root):
    data, sources = {}, {}
    for name, pin in PINS.items():
        path = root / name
        raw = path.read_bytes()
        require(digest(raw) == pin, "source drift: " + name)
        sources[name] = dict(sha256=pin, bytes=len(raw))
        data[name] = json.loads(raw) if path.suffix == ".json" else raw.decode()
    inv = data["/tmp/destiny-weapons-w30/bungie-items.json"]
    pools = data["/tmp/destiny-weapons-w60/bungie-plugsets.json"]
    manifest = data["/tmp/destiny-weapons-w60/manifest.json"]["Response"]
    require(manifest["version"] == VERSION, "official manifest version")
    perk = inv[str(BASE)]
    require(perk["hash"] == BASE and perk["displayProperties"]["name"] == "Box Breathing"
            and perk["itemTypeDisplayName"] == "Trait" and perk["itemType"] == 19
            and not perk["plug"]["isDummyPlug"] and not perk["redacted"] and not perk["blacklisted"],
            "exact base Trait definition")
    require(inv[str(ENHANCED)]["itemTypeDisplayName"] == "Enhanced Trait", "enhanced exclusion")
    rows = [row for row in re.findall(r"<tr\b[^>]*>.*?</tr>", data["/private/tmp/destiny-w190/ddc-perks.html"], re.S)
            if any(plain(cell) == "Box Breathing" for cell in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S))]
    require(len(rows) == 1 and 'id="1662574278R34"' in rows[0], "exact DDC row35")
    row = rows[0]
    description_html = re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S)[-1]
    description = plain(description_html)
    yellow = re.findall(r'<span\b[^>]*style="[^"]*color:#ffd966;[^"]*"[^>]*>(.*?)</span>', description_html, re.S)
    base_description = plain(re.sub(r'<span\b[^>]*style="[^"]*color:#ffd966;[^"]*"[^>]*>(.*?)</span>',
        lambda m: '' if plain(m.group(1)) == '↑1.4' else m.group(1), description_html, flags=re.S))
    require("After 1.5 seconds of ADS without firing while Magazine is >0:" in base_description
            and "10% Increased Aim Assist Falloff Distance" in base_description
            and "40% increased Weakspot Damage" in base_description
            and "Timer starts as soon as the Aim Down Sights input is pressed." in base_description
            and any("↑1.4" == plain(v) for v in yellow), "exact base DDC values and separate enhanced yellow")
    catalog = list(data[PREFIX + "w30.json"])
    stats = {r["id"]: r for r in data[PREFIX + "w40-characteristics.json"]}
    for name in ("w83-exotics.json", "w84-exotics.json"):
        for exotic in data[PREFIX + name]:
            catalog.append(exotic["catalog"])
            require(exotic["catalog"]["id"] not in stats, "unique exotic ID")
            stats[exotic["catalog"]["id"]] = exotic["characteristics"]
    require(len(catalog) == len(stats) == 65 and len({e["id"] for e in catalog}) == 65,
            "all65 unique canonical entries/characteristics")
    found, proofs, audit = [], [], []
    for entry in catalog:
        characteristic = stats[entry["id"]]
        item = inv[str(characteristic["bungieHash"])]
        require(item["hash"] == characteristic["bungieHash"], "official weapon hash")
        result = dict(id=entry["id"], hash=item["hash"], exotic=characteristic["exotic"],
                      examinedTraitSockets=[], matches=[])
        for category in item.get("sockets", {}).get("socketCategories", []):
            if category["socketCategoryHash"] != 4241085061:
                continue
            for index in category["socketIndexes"]:
                socket = item["sockets"]["socketEntries"][index]
                pool_hash = socket.get("randomizedPlugSetHash")
                pool = pools.get(str(pool_hash))
                result["examinedTraitSockets"].append(dict(socket=index, randomizedPlugSetHash=pool_hash,
                    singleInitialItemHash=socket.get("singleInitialItemHash"), poolPresent=pool is not None,
                    isFakePlugSet=pool.get("isFakePlugSet") if pool else None))
                if not pool or pool.get("isFakePlugSet") is not False:
                    continue
                require(pool["hash"] == pool_hash, "official plugset hash")
                for plug in pool["reusablePlugItems"]:
                    definition = inv.get(str(plug["plugItemHash"]), {})
                    if (plug.get("currentlyCanRoll") is not True
                            or definition.get("itemTypeDisplayName") != "Trait" or plug["plugItemHash"] != BASE):
                        continue
                    require(not characteristic["exotic"] and item["inventory"]["tierType"] == 5,
                            "legendary real randomized rolls only")
                    roll = dict(id=entry["id"], hash=item["hash"], socket=index, perkHash=BASE, plugSetHash=pool_hash)
                    found.append(roll)
                    result["matches"].append(roll)
                    proofs.append(dict(roll=roll, canonicalEntry=entry, category=category, socketEntry=socket,
                                       plugSetHash=pool["hash"], isFakePlugSet=pool["isFakePlugSet"], matchingPlug=plug,
                                       weaponItemTypeDisplayName=item["itemTypeDisplayName"],
                                       weaponTier=item["inventory"]["tierType"]))
        audit.append(result)
    require(found == EXPECTED, "exhaustive all65 scan: exact base/currentlyCanRoll/nonfake socket tuples")
    require(all(stats[x["id"]]["ammo"] == "SPECIAL"
                and next(e for e in catalog if e["id"] == x["id"])["family"] == "sniper_rifle"
                and inv[str(x["hash"])]["equippingBlock"]["ammoType"] == 2
                and inv[str(x["hash"])]["itemTypeDisplayName"] == "Sniper Rifle" for x in found),
            "both local and official canonical Box Breathing rolls are Special snipers")
    resource = dict(stage="W195", perk={'id': 'box_breathing', 'hash': 2551157718, 'procTicks': 30, 'precisionMultiplier': 1.4, 'aimAssistFalloffScalar': 1.1}, weapons=found)
    resource_raw = encode(resource)
    authored = {name: dict(sha256=digest((root / (JAVA + name)).read_bytes()))
                for name in ("BoxBreathingProfile.java", "WeaponBoxBreathing.java", "BoxBreathingCycle.java")}
    source = dict(stage="W195", checked="2026-10-27", officialManifest=VERSION,
        sourcePins=sources, generatorSha256=digest(Path(__file__).read_bytes()),
        resourceSha256=digest(resource_raw), helperSources=authored, catalogCount=65,
        selectionRules=dict(socketCategoryHash=4241085061, randomizedPlugSet=True, isFakePlugSet=False,
                            currentlyCanRoll=True, itemTypeDisplayName="Trait", exactPerkHash=BASE),
        perkDefinition=perk, socketProofs=proofs, catalogAudit=audit,
        excludedSameNameDefinitions=[dict(hash=int(k), itemTypeDisplayName=v.get("itemTypeDisplayName"),
                                          description=v["displayProperties"].get("description"))
            for k, v in sorted(inv.items(), key=lambda pair: int(pair[0]))
            if v.get("displayProperties", {}).get("name") == "Box Breathing" and int(k) != BASE],
        ddc=dict(url="https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278",
                 tab="Weapon Perks", row=35, rawHTML=row, text=description, baseText=base_description,
                 enhancedYellowHTML=yellow, enhancedExcluded=ENHANCED, activity="No PvE/PvP split stated"),
        policies={'defaultSelection': 'No trait selected by default; master registers only these exact base rolls. Enhanced/exotic unsupported.', 'ownership': 'Original count-one selected hotbar/equipped object, exact canonical entry and selected tuple; ServerPlayer/level/GuardianData/runtime/class/loadout/Super checked; accepted writers only; no query mutation. Old-owner cleanup cannot remove successor.', 'integration': 'Master owns shared registry/runtime/aiming/handling/HUD and central tests. Token.NONE for perkSplash; never fresh capture at explosion.', 'conversion': '20TPS elapsed server ticks are a provisional Minecraft mapping, not a measured Destiny clock.', 'aa': 'Sourced Aim Assist metadata is exposed only. This server port has no AA or client magnetism implementation.', 'validation': 'Focused event/timer/epoch cycle tests and isolated Java25 compile only; no numeric mirror tests, numeric-only Vision/fullgate, native or server QA.', 'paid': 'update(p,actualAds) only after master validated FOV/handling ownership. capture(p,entry,roundsBefore,actualAds) after actual payment before trace; do not update using post-payment empty magazine first. Supplementals and perkSplash use Token.NONE.', 'application': 'precisionMultiplier applies only to weakspot/precision hits; no body damage, generic damage or Dragonfly inheritance.', 'snapshot': '30 elapsed ticks from actual ADS input with positive magazine, no firing. Paid shot consumes readiness; release/stow/reload/edit resets. False/true same tick restarts clock. Natural magazine-empty polling does not erase accepted last-round snapshot.', 'uncertainty': 'DDC row35 text contains "Weakspot damage? Least convoluted way"; preserve raw question text as uncertainty. Shielded weakspot and Divinity semantics are not claimed simulated. Confirmed 40% for the two supported Special snipers; 30% Heavy/Glaive branch unsupported.'})
    return {PREFIX + "w195-box-breathing.json": resource_raw, ART + "source.json": encode(source)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    for name, raw in generate(args.root.resolve()).items():
        path = args.root.resolve() / name
        if args.verify:
            require(path.read_bytes() == raw, "generated output drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        print(("verified " if args.verify else "wrote ") + name)
    print("W195 Box Breathing: catalog65; 2 exact base rolls; DDC row35; enhanced excluded")


if __name__ == "__main__":
    main()
