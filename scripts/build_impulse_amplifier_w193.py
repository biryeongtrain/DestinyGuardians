#!/usr/bin/env python3
"""Build pinned W193 base Impulse Amplifier; --verify compares outputs without writes."""
import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 951095735
VERSION = "245114.26.10.13.2000-1-bnet.66137"
PREFIX = "src/main/resources/destiny/weapons/"
ART = "art/weapons/w193/impulse-amplifier/"
EXPECTED = [
    dict(id="canis_major", hash=2066434718, socket=3, perkHash=BASE, plugSetHash=4037911937),
    dict(id="code_duello", hash=2496242052, socket=3, perkHash=BASE, plugSetHash=3719628667),
    dict(id="nezarec_s_whisper", hash=254636484, socket=3, perkHash=BASE, plugSetHash=210449465),
]
PINS = {
    "/tmp/destiny-weapons-w30/bungie-items.json": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "/tmp/destiny-weapons-w60/bungie-plugsets.json": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "/tmp/destiny-weapons-w60/manifest.json": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "/private/tmp/destiny-w193/remaining-sockets.json": "f5025dc2ce7fc8ddf3e2c2493c32004c5739800262400b06c97df19d7e6fb393",
    "/private/tmp/destiny-w190/ddc-perks.html": "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437",
    PREFIX + "w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    PREFIX + "w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    PREFIX + "w46-timing.json": "e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07",
    PREFIX + "w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    PREFIX + "w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "art/weapons/w43/extraction.json": "a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5",
    "art/weapons/w46/weapon_formulas.json": "fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d",
}
# Includes implemented reload traits and unimplemented candidates: audit the actual other column.
RELOAD_NAMES = {
    "Outlaw": "outlaw", "Feeding Frenzy": "feeding_frenzy", "Rapid Hit": "rapid_hit",
    "Perpetual Motion": "perpetual_motion", "Frenzy": "frenzy", "Stats for All": "stats_for_all",
    "Threat Detector": "threat_detector", "Surplus": "surplus", "Elemental Capacitor": "elemental_capacitor",
    "Ensemble": "ensemble", "Compulsive Reloader": "compulsive_reloader", "Field Prep": "field_prep",
    "Impulse Amplifier": "impulse_amplifier", "Alloy Magazine": "alloy_magazine",
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
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
    require(manifest["version"] == VERSION, "manifest version")
    require(data["/private/tmp/destiny-w193/remaining-sockets.json"]["Impulse Amplifier"] == EXPECTED,
            "assigned three exact socket tuples")
    perk = inv[str(BASE)]
    require(perk["hash"] == BASE and perk["displayProperties"]["name"] == "Impulse Amplifier"
            and perk["itemTypeDisplayName"] == "Trait" and perk["itemType"] == 19
            and not perk["plug"]["isDummyPlug"] and not perk["redacted"] and not perk["blacklisted"],
            "exact base Trait, never Enhanced")
    rows = [r for r in re.findall(r"<tr\b[^>]*>.*?</tr>", data["/private/tmp/destiny-w190/ddc-perks.html"], re.S)
            if any(plain(c) == "Impulse Amplifier" for c in re.findall(r"<td\b[^>]*>(.*?)</td>", r, re.S))]
    require(len(rows) == 1 and 'id="1662574278R123"' in rows[0], "DDC exact row124")
    row = rows[0]
    description = plain(re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S)[-1])
    require(all(t in description for t in ["+20", "↑+25", "0.85x", "0.8x", "Rocket Launchers: 10%",
            "Support Auto Rifles: 15%", "Rocket Sidearm: 25%"]), "DDC base numbers")
    require("Glaive" not in description and "Grenade Launcher" not in description, "omitted families stay unknown")
    catalog = list(data[PREFIX + "w30.json"])
    stats = {r["id"]: r for r in data[PREFIX + "w40-characteristics.json"]}
    for name in ("w83-exotics.json", "w84-exotics.json"):
        for exotic in data[PREFIX + name]:
            catalog.append(exotic["catalog"])
            stats[exotic["catalog"]["id"]] = exotic["characteristics"]
    require(len(catalog) == len(stats) == 65 and len({e["id"] for e in catalog}) == 65, "catalog65 coverage")
    found, proofs, trait_audit = [], [], []
    for entry in catalog:
        characteristic = stats[entry["id"]]
        item = inv[str(characteristic["bungieHash"])]
        for category in item.get("sockets", {}).get("socketCategories", []):
            if category["socketCategoryHash"] != 4241085061:
                continue
            for index in category["socketIndexes"]:
                socket = item["sockets"]["socketEntries"][index]
                pool_hash = socket.get("randomizedPlugSetHash")
                pool = pools.get(str(pool_hash))
                if not pool or pool.get("isFakePlugSet") is not False:
                    continue
                for plug in pool["reusablePlugItems"]:
                    definition = inv.get(str(plug["plugItemHash"]), {})
                    if plug.get("currentlyCanRoll") is not True or definition.get("itemTypeDisplayName") != "Trait":
                        continue
                    roll = dict(id=entry["id"], hash=characteristic["bungieHash"], socket=index,
                                perkHash=plug["plugItemHash"], plugSetHash=pool_hash)
                    if plug["plugItemHash"] == BASE:
                        require(not characteristic["exotic"] and item["inventory"]["tierType"] == 5, "legendary only")
                        found.append(roll)
                        proofs.append(dict(roll=roll, socketEntry=socket, category=category,
                                           isFakePlugSet=False, matchingPlug=plug))
                    if entry["id"] in {r["id"] for r in EXPECTED}:
                        trait_audit.append(dict(name=definition["displayProperties"]["name"], roll=roll))
    require(found == EXPECTED, "exhaustive catalog65 base/currentlyCanRoll/realPool scan")
    reload_audit = [dict(**p, perk=RELOAD_NAMES[p["name"]],
                         distinctSocket=p["roll"]["socket"] != 3)
                    for p in trait_audit if p["name"] in RELOAD_NAMES and p["name"] != "Impulse Amplifier"]
    companions = [dict(id=p["roll"]["id"], perk=p["perk"], roll=p["roll"])
                  for p in reload_audit if p["distinctSocket"]]
    require([(c["id"], c["perk"]) for c in companions] ==
            [("code_duello", "frenzy"), ("nezarec_s_whisper", "frenzy")], "reload companion drift")
    timing = {r["id"]: r["timing"] for r in data[PREFIX + "w46-timing.json"]}
    mapping = {r["id"]: r for r in data["art/weapons/w43/extraction.json"]["entries"]}
    formulas = data["art/weapons/w46/weapon_formulas.json"]
    entries = {e["id"]: e for e in catalog}
    curves, velocity, baselines = [], [], []
    for roll in EXPECTED:
        id_ = roll["id"]
        m, t = mapping[id_], timing[id_]
        raw = formulas[m["family"]]["cat"][m["category"]]["reload"]
        curve = {k: raw.get(k, 0.0) for k in ("evpp", "vpp", "offset")}
        stat = stats[id_]["stats"]["4188031367"]
        require(stat == inv[str(roll["hash"])]["stats"]["stats"]["4188031367"]["value"], "official base reload")
        require(t["supported"] and not t["shellReload"], "whole-magazine only; no shell timing")
        seconds = lambda s: curve["evpp"] * s * s + curve["vpp"] * s + curve["offset"]
        require(math.ceil(seconds(stat) * 20) == t["reloadTicks"], "raw W46 baseline")
        curves.append(dict(id=id_, baseReloadStat=stat, reload=curve))
        rocket = entries[id_]["family"] == "rocket_launcher"
        velocity.append(dict(id=id_, family=entries[id_]["family"],
                             status="DDC_CONFIRMED" if rocket else "OMITTED_UNKNOWN",
                             scalar=1.10 if rocket else None))
        baselines.append(dict(id=id_, rawBaseSeconds=seconds(stat),
                              rawActiveSeconds=seconds(min(100, stat + 20)) * (.8 if rocket else .85)))
    resource = dict(stage="W193", perk=dict(id="impulse_amplifier", hash=BASE, reloadBonus=20,
                    durationMultiplier=.85, rocketDurationMultiplier=.8), weapons=EXPECTED,
                    curves=curves, coSelections=companions, projectileVelocity=velocity)
    resource_bytes = encode(resource)
    source = dict(stage="W193", checked="2026-10-27", officialManifest=VERSION, sourcePins=sources,
                  generatorSha256=digest(Path(__file__).read_bytes()), resourceSha256=digest(resource_bytes),
                  catalogCount=65, perkDefinition=perk, socketProofs=proofs, allBaseTraitsOnSupportedWeapons=trait_audit,
                  reloadCompanionAudit=reload_audit, coSelections=companions, baselineMath=baselines,
                  ddc=dict(url="https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278",
                           tab="Weapon Perks", row=124, text=description, html=row, enhancedExcluded=3878366039),
                  research=[dict(url="https://www.light.gg/db/items/951095735/impulse-amplifier/?_=738",
                                 retrieval="Indexed community-research text retrieved 2026-10-27; direct open returned HTTP402.",
                                 observation="Current base research, dated 2026-07-03, enumerates rocket, support-auto and micro-missile velocity bonuses. GL and glaive numeric bonuses are omitted, as in the pinned DDC.",
                                 decision="No concrete current GL or glaive scalar resolved; null means omitted/unknown, not a confirmed zero bonus."),
                            dict(url="https://www.bungie.net/7/en/News/Article/season-23-weapons-preview",
                                 date="2023-10-25", author="Destiny 2 Weapons Team",
                                 observation="Primary developer notes describe increased baseline glaive projectile speed and describe Impulse Amplifier as a historical desirable perk. They do not specify a current numerical perk scalar for glaives or GLs.",
                                 decision="Baseline archetype tuning cannot be substituted for a perk multiplier; no inferred 1.35 or 1.30 adopted.")],
                  policies=dict(reload="Sum actual colegal active stat bonuses; clamp official base + total to 0..100 once; raw quadratic seconds times total duration scalar; one ceil(seconds*20); no shell path.",
                                unknownVelocity="Keep incoming launch speed when scalar is null; uncertainty is retained in resource and API.",
                                ownership="Pure current original held-stack/canonical-roll checks; no mutation, attachments, timers or cached player identity.",
                                integration="Master registry + outermost accepted reload plan + once-only paid projectile launch sampling; Rangefinder composes independently only on distinct legal sockets.",
                                timing="Historical approximate W46 community curves, not newly measured official Destiny durations."))
    for relative, raw in [(PREFIX + "w193-impulse-amplifier.json", resource_bytes), (ART + "source.json", encode(source))]:
        path = root / relative
        if args.verify:
            require(path.read_bytes() == raw, "generated drift: " + relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(f"W193 {'verified' if args.verify else 'generated'}: catalog65; three exact base rolls; two Frenzy pairs; GL/glaive velocity omitted/unknown; {digest(resource_bytes)}")


if __name__ == "__main__":
    main()
