#!/usr/bin/env python3
"""Reproduce W226 BASIC Slickdraw data and bounded proof; --check is read-only."""
import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

TRAIT = "slickdraw"
NAME = "Slickdraw"
HASH = 1821614984
SOCKET = 3
POOL = 563442205
ROW = 200
SLUG = TRAIT.replace("_", "-")
PREFIX = "src/main/resources/destiny/weapons/"
DDC = "/private/tmp/destiny-w226/ddc-perks-live.html"
URL = "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278"
PINS = {
    "/tmp/destiny-weapons-w30/bungie-items.json": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "/tmp/destiny-weapons-w60/bungie-plugsets.json": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "/tmp/destiny-weapons-w60/manifest.json": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    DDC: "6430f2f552832b903efb85be59adf4a1791d956d30fee4e4fe79c8ad2c53bc15",
    PREFIX + "w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    PREFIX + "w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    PREFIX + "w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    PREFIX + "w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "src/main/java/kim/biryeong/destiny/weapon/WeaponExotics.java": "8bc75359ace0e885e10e1b95811b6bb43e3a242cc720e7ce6427b763e3b2a4a7",
}
if TRAIT == "slickdraw":
    PINS[PREFIX + "w202-steady-hands.json"] = "95c6c89dc5c8490ccc5561753a2ef7d2eb8a3c474c07078c79d55f34e7cd1417"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def row_proof(rows, name, expected_row=None):
    found = []
    for row in rows:
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S)
        if cells and html.unescape(re.sub("<[^>]+>", "", cells[0])).strip() == name:
            found.append(row)
    require(len(found) == 1, "unique DDC row: " + name)
    row = found[0]
    row_id = re.search(r'id="(1662574278R(\d+))"', row)
    require(row_id is not None, "DDC row id")
    number = int(row_id[2]) + 1
    require(expected_row is None or number == expected_row, "DDC displayed row")
    # Retain raw evidence; yellow enhanced annotations never supply BASIC mechanics.
    basic = re.sub(r'<span style="color:#ffd966;">.*?</span>', "", row, flags=re.S)
    text = " ".join(html.unescape(re.sub("<[^>]+>", " ", basic)).split())
    return dict(name=name, tab="Weapon Perks", gid=1662574278, row=number,
                rowID=row_id[1], url=URL, baseText=text, rawHTML=row)


def definition(d):
    return {k: d[k] for k in ("hash", "displayProperties", "itemTypeDisplayName", "inventory",
                              "plug", "investmentStats", "perks", "redacted", "blacklisted")}


def generate(root):
    raw = {name: (root / name).read_bytes() for name in PINS}
    for name, pin in PINS.items():
        require(sha(raw[name]) == pin, "Pinned input drift: " + name)
    data = lambda name: json.loads(raw[name])
    inv = data("/tmp/destiny-weapons-w30/bungie-items.json")
    pools = data("/tmp/destiny-weapons-w60/bungie-plugsets.json")
    manifest = data("/tmp/destiny-weapons-w60/manifest.json")["Response"]
    require(manifest["version"] == "245114.26.10.13.2000-1-bnet.66137", "manifest version")
    d = inv[str(HASH)]
    require(d["hash"] == HASH and d["displayProperties"]["name"] == NAME
            and d["itemTypeDisplayName"] == "Trait" and d["inventory"]["tierType"] == 2
            and d["plug"]["isDummyPlug"] is False and not d["redacted"] and not d["blacklisted"], "BASIC real Trait")
    rows = re.findall(r"<tr\b[^>]*>.*?</tr>", raw[DDC].decode(), re.S)
    ddc = row_proof(rows, NAME, ROW)
    catalog = data(PREFIX + "w30.json")
    stats = data(PREFIX + "w40-characteristics.json")
    for extension in ("w83-exotics.json", "w84-exotics.json"):
        for x in data(PREFIX + extension):
            catalog.append(x["catalog"]); stats.append(x["characteristics"])
    require(len(catalog) == 65 and len({x["id"] for x in catalog}) == 65
            and {x["id"] for x in catalog} == {x["id"] for x in stats}, "current canonical coverage")
    rolls, proofs, audit = [], [], []
    for w in stats:
        item = inv[str(w["bungieHash"])]
        matches = []
        if not w["exotic"] and item["inventory"]["tierType"] == 5:
            for cat in item["sockets"]["socketCategories"]:
                if cat["socketCategoryHash"] != 4241085061:
                    continue
                for index in cat["socketIndexes"]:
                    socket = item["sockets"]["socketEntries"][index]
                    ph = socket.get("randomizedPlugSetHash")
                    pool = pools.get(str(ph), {})
                    if pool.get("isFakePlugSet") is not False:
                        continue
                    require(pool["hash"] == ph, "official pool hash")
                    for plug in pool.get("reusablePlugItems", []):
                        if plug.get("plugItemHash") == HASH and plug.get("currentlyCanRoll") is True:
                            roll = dict(id=w["id"], hash=w["bungieHash"], socket=index, perkHash=HASH, plugSetHash=ph)
                            rolls.append(roll); matches.append(roll)
                            proofs.append(dict(roll=roll, tierType=5, traitCategory=cat,
                                               socketEntry=socket, plugSet=pool, matchingPlug=plug))
        audit.append(dict(id=w["id"], hash=w["bungieHash"], exotic=w["exotic"], matches=matches))
    require(rolls == [dict(id="bite_of_the_fox", hash=1403800851, socket=SOCKET,
                         perkHash=HASH, plugSetHash=POOL)], "exact BASIC currentlyCanRoll canonical tuple")
    perk = dict(id=TRAIT, hash=HASH)
    resource = dict(stage="W226", perk=perk, weapons=rolls)
    policies = dict(basicOnly=True, enhancedExcluded=True, fakePoolFallback=False,
                    ownership="Live count-one real WeaponItems source; original reference uniquely owned in inventory hotbar/loadout. No proc or persistent state.",
                    initialization="JSON-only. Canonical registries checked lazily in supports(entry).",
                    testing="User simple-stat exception: no numerical-only unit tests, whole gate or Vision. Master owns integration.")
    extra = {}
    if TRAIT == "iron_gaze":
        require("+20 Aim Assist and -20" in ddc["baseText"] and "Range" in ddc["baseText"], "BASIC DDC values")
        values = {x["statTypeHash"]: x["value"] for x in d["investmentStats"] if not x["isConditionallyActive"]}
        require(values == {1345609583: 20, 1240592695: -20}, "official BASIC investment stats")
        perk.update(rangeBonus=-20, aimAssistBonus=20, aimAssistPolicy="source-only; unsimulated")
        policies.update(apply="WeaponIronGaze.rangeBonus(player): signed -20 in master raw Range sum before existing clamp; held selected exact source only.",
                        aimAssist="+20 Aim Assist is source-only and unsimulated; no spread, cone or magnetism invented.")
    else:
        require(all(s in ddc["baseText"] for s in ("+100 Handling", "0.95x Ready Animation Duration Multiplier", "-20%", "Auto Aim Cone Size")), "BASIC DDC values")
        perk.update(handlingBonus=100, readyScalar=.95, stowScalar=1.0, adsScalar=1.0, autoAimPolicy="source-only; unsimulated")
        curves = data(PREFIX + "w202-steady-hands.json")["curves"]
        curve = next(c for c in curves if c["id"] == "bite_of_the_fox")
        stat = next(w for w in stats if w["id"] == "bite_of_the_fox")["stats"]["943549884"]
        require(curve["baseHandlingStat"] == stat == 25, "original raw handling")
        def seconds(key):
            q = curve[key]
            return q["evpp"] * 100 * 100 + q["vpp"] * 100 + q["offset"]
        resource["curve"] = curve
        weapon = inv["1403800851"]
        companion_socket = weapon["sockets"]["socketEntries"][4]
        require(companion_socket["randomizedPlugSetHash"] == 2442672691, "companion socket4")
        companion_pool = pools["2442672691"]
        require(companion_pool["isFakePlugSet"] is False, "real companion pool")
        names = {3038247973: "Explosive Payload", 588594999: "Moving Target", 47981717: "Opening Shot",
                 1546637391: "Vorpal Weapon", 1870851715: "Under-Over", 4152709778: "Iron Gaze"}
        legal = [p for p in companion_pool["reusablePlugItems"] if p.get("currentlyCanRoll") is True]
        require({p["plugItemHash"] for p in legal} == names.keys(), "exact companion set")
        companion_rows = []
        for plug in legal:
            item = inv[str(plug["plugItemHash"])]
            require(item["displayProperties"]["name"] == names[plug["plugItemHash"]]
                    and item["itemTypeDisplayName"] == "Trait", "BASIC companion definition")
            require(not any(s["statTypeHash"] == 943549884 and s["value"] != 0 for s in item["investmentStats"]), "no companion handling stat")
            proof = row_proof(rows, names[plug["plugItemHash"]])
            require("handling" not in proof["baseText"].lower() and "ready" not in proof["baseText"].lower()
                    and "stow" not in proof["baseText"].lower(), "no DDC handling duration effect")
            companion_rows.append(dict(plug=plug, definition=definition(item), ddc=proof))
        extra.update(curveProof=dict(source=PREFIX + "w202-steady-hands.json", curve=curve,
                        rawSecondsAt100={k: seconds(k) for k in ("ready", "stow", "ads")},
                        calculation="ceil(rawSeconds(100) * (0.95 iff ready else 1) * 20); ADS clamp2..20; never scale rounded ticks",
                        units="Historical W46 community seconds mapped to local20TPS. Not a current exact Destiny animation measurement."),
                     companionProof=dict(weaponHash=1403800851, socket=4, socketEntry=companion_socket,
                        plugSet=companion_pool, legalBasicPerks=companion_rows,
                        conclusion="No legal socket4 perk adds Handling or ready/stow/ADS duration scalar. Snapshot Sights and Firmly Planted share Slickdraw socket3 and are exclusive."))
        policies.update(apply="Master wraps WeaponSlickdraw.handlingTicks(player,stack,ready,base) and adsTicks(player,entry,base,entering) outermost. Raw Handling25+100 saturates100; ready .95 only; stow and ADS scalar1.",
                        incoming="Ready accepts exact original owned incoming hotbar item before actual selection. Stow and ADS require current selected held source. No stored proc or selecting hook.",
                        composition="No speculative companion scalar or rounded-duration composition. Other positive raw handling buffs are redundant at100.",
                        autoAim="BASIC -20% Auto Aim Cone Size is source-only and unsimulated; no spread penalty invented. Enhanced -15%? excluded.")
    source = dict(stage="W226", checked="2026-10-28", manifestVersion=manifest["version"], sourcePins=PINS,
                  officialComponentURLs={k: "https://www.bungie.net" + manifest["jsonWorldComponentContentPaths"]["en"][k]
                      for k in ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
                  generatorSHA256=sha(Path(__file__).read_bytes()), resourceSHA256=sha(encode(resource)),
                  baseDefinition=definition(d), socketProofs=proofs, canonicalScan=audit, ddc=ddc, policies=policies, **extra)
    md = [f"# W226 {NAME} — BASIC", "", f"Weapon Perks gid1662574278 displayed row{ROW}, HTML id1662574278R{ROW-1}.",
          f"[User DDC]({URL}). Live snapshot checked 2026-10-28; yellow enhanced annotations excluded.", "", ddc["baseText"], "",
          f"Exact sole legal canonical roll: Bite of the Fox hash1403800851, socket{SOCKET}, pool{POOL}, BASIC perk hash{HASH}.",
          "Official legendary tier5; category4241085061; real randomized pool; currentlyCanRoll=true. All65 current canonical entries scanned including W83/W84 exotics; no fake/default/reusable fallback.", "",
          "## Apply and limits", ""]
    md += [f"- {v}" for k, v in policies.items() if isinstance(v, str)]
    if TRAIT == "slickdraw":
        md += ["", "## Bounded raw curve proof", "", "Only Bite's ready/stow/ADS curve is emitted. Source: pinned w202-steady-hands.json, original Handling25.",
               "These are historical W46 community curves, not a new current-Destiny animation calibration.", "", "```json", json.dumps(extra["curveProof"], indent=2), "```", "",
               "Exact socket4 pool2442672691 (all currentlyCanRoll BASIC):"]
        md += [f"- {x['definition']['displayProperties']['name']} hash{x['plug']['plugItemHash']}: DDC row{x['ddc']['row']} ({x['ddc']['rowID']}); no Handling/ready/stow/ADS duration effect." for x in extra["companionProof"]["legalBasicPerks"]]
        md += ["", extra["companionProof"]["conclusion"]]
    md += ["", "## Reproduce", "", f"`python3 scripts/build_{TRAIT}_w226.py --root X --check` validates every input pin and all three generated outputs without writes.",
           "Omit --check to regenerate the owned resource, source.json and SOURCE.md only. No network or registry access.", "", "## SHA-256 input pins", ""]
    md += [f"- `{name}`: `{pin}`" for name, pin in PINS.items()]
    md += ["", f"Manifest envelope version: {manifest['version']}. Inventory and pool bytes are independently pinned; their local download dates differ.",
           "Bounded raw HTML, socket/pool entries, canonical scan, definition excerpts and curve proof are retained in source.json.", ""]
    art = f"art/weapons/w226/{SLUG}/"
    return {PREFIX + f"w226-{SLUG}.json": encode(resource), art + "source.json": encode(source),
            art + "SOURCE.md": "\n".join(md).encode()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    root = args.root.resolve()
    for name, content in generate(root).items():
        path = root / name
        if args.check:
            require(path.read_bytes() == content, "Generated drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        print(("checked " if args.check else "wrote ") + name)


if __name__ == "__main__":
    main()
