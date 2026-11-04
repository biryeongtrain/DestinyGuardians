#!/usr/bin/env python3
"""Pinned offline Steady Hands source proof and raw timing curves; --verify is read-only."""
import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons/"
BASE = 509074078
VERSION = "245114.26.10.13.2000-1-bnet.66137"
PINS = {
    "/tmp/destiny-weapons-w30/bungie-items.json": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "/tmp/destiny-weapons-w60/bungie-plugsets.json": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "/tmp/destiny-weapons-w60/manifest.json": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "/private/tmp/destiny-w190/ddc-perks.html": "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437",
    PREFIX + "w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    PREFIX + "w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    PREFIX + "w58-handling.json": "4de7d346a93c822784fafa69b62ac66148d51cc11cf2da6706367682b414d3f1",
    PREFIX + "w44-aim.json": "0d0a38469c28a74c1a77489d346184eccef347a604c0c0c455d1c7c2e1a80fc8",
    PREFIX + "w68-snapshot.json": "7e824633be32953e6c75d3d856ce765223fbb1cbcc3b01affca3d83eb8fcb738",
    PREFIX + "w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    PREFIX + "w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "art/weapons/w43/extraction.json": "a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5",
    "art/weapons/w46/weapon_formulas.json": "fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d",
    "art/weapons/w46/stat_calc.rs": "5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2",
    "art/weapons/w46/rs_types.rs": "faa476e6589d2362cf9ee8dd948410adfa7fa8507e8809f3cd10bb13ebba9b90",
    "scripts/extract_handling_w58.py": "177981eb79edd79bb2c4c1e80618183ac2156ddfe5106e93fa70d69786b9b934",
    "art/weapons/w83/data/extraction.json": "1178d315202d0d78341c85f5e9aa8e765dc503ddfca8fba9c157f163ab717e90",
    "art/weapons/w84/data/runtime-extraction.json": "ccdaeb23dbadae9ef393ae7e2aa232c037c8e22278478c0844a1ec51e2599d59",
    "scripts/extract_izanagi_w84.py": "8b122f323af80faed33670c63188e5d9ac961ab3ff69cf7c710786ccc5400d39",
    "src/main/java/kim/biryeong/destiny/weapon/WeaponExotics.java": "8bc75359ace0e885e10e1b95811b6bb43e3a242cc720e7ce6427b763e3b2a4a7",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def generate(root):
    raw = {name: (root / name).read_bytes() for name in PINS}
    for name, expected in PINS.items():
        require(sha(raw[name]) == expected, "Pinned input drift: " + name)
    data = lambda name: json.loads(raw[name])
    inv = data("/tmp/destiny-weapons-w30/bungie-items.json")
    pools = data("/tmp/destiny-weapons-w60/bungie-plugsets.json")
    manifest = data("/tmp/destiny-weapons-w60/manifest.json")["Response"]
    require(manifest["version"] == VERSION, "manifest version")
    definition = inv[str(BASE)]
    require(definition["displayProperties"]["name"] == "Steady Hands"
            and definition["itemTypeDisplayName"] == "Trait"
            and definition["plug"]["isDummyPlug"] is False
            and not definition.get("redacted") and not definition.get("blacklisted"), "base Trait")
    row = next(r for r in re.findall(r"<tr\b[^>]*>.*?</tr>", raw["/private/tmp/destiny-w190/ddc-perks.html"].decode(), re.S)
               if 'id="1662574278R207"' in r)
    base_row = re.sub(r'<span style="color:#ffd966;">.*?</span>', "", row, flags=re.S)
    text = " ".join(html.unescape(re.sub("<[^>]+>", " ", base_row)).split())
    require(all(s in text for s in ("Steady Hands", "+100", "0.825x Handling Duration", "all equipped weapons",
                                   "8.5", "6.5 seconds", "Buff remains active while stowed")), "base DDC row208")
    catalog = data(PREFIX + "w30.json")
    stats = data(PREFIX + "w40-characteristics.json")
    handling = {r["id"]: r["profile"] for r in data(PREFIX + "w58-handling.json")}
    aim = {r["id"]: r["profile"] for r in data(PREFIX + "w44-aim.json")}
    rolls, proof, audit = [], [], []
    # Same strict current randomized Trait socket policy as W190, plus full pool/definition checks.
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
                    require(pool["hash"] == ph, "official pool identity")
                    for plug in pool.get("reusablePlugItems", []):
                        if plug.get("plugItemHash") == BASE and plug.get("currentlyCanRoll") is True:
                            r = dict(id=w["id"], hash=w["bungieHash"], socket=index, perkHash=BASE, plugSetHash=ph)
                            rolls.append(r); matches.append(r)
                            proof.append(dict(roll=r, traitCategory=cat, socketEntry=socket, plugSet=pool, matchingPlug=plug))
        audit.append(dict(id=w["id"], hash=w["bungieHash"], matches=matches))
    require(rolls == [dict(id="mindbender_s_ambition_adept", hash=912150785, socket=4,
                         perkHash=BASE, plugSetHash=4054654930)], "exact single base current roll")
    mappings = {r["id"]: r for r in data("art/weapons/w43/extraction.json")["entries"]}
    # These additive resources are the current W121-era exotic catalog extensions.
    # Do not infer a family from weapon name; retain their existing source mapping.
    ace = data("art/weapons/w83/data/extraction.json")
    izanagi = data("art/weapons/w84/data/runtime-extraction.json")
    require(ace["category"] == "Hand Cannon/default" and ace["derived"] == data(PREFIX + "w83-exotics.json")[0], "Ace source mapping")
    require(izanagi["derived"] == data(PREFIX + "w84-exotics.json")[0]
            and "['Sniper Rifle']" in raw["scripts/extract_izanagi_w84.py"].decode()
            and "['cat']['default']" in raw["scripts/extract_izanagi_w84.py"].decode(), "Izanagi source mapping")
    for name, family in (("w83-exotics.json", "Hand Cannon"), ("w84-exotics.json", "Sniper Rifle")):
        for exotic in data(PREFIX + name):
            e = exotic["catalog"]; catalog.append(e); stats.append(exotic["characteristics"])
            handling[e["id"]] = exotic["handling"]["profile"]
            aim[e["id"]] = exotic["aim"]["profile"]
            mappings[e["id"]] = dict(id=e["id"], family=family, category="default", source=name)
    formulas = data("art/weapons/w46/weapon_formulas.json")
    by_stats = {r["id"]: r for r in stats}
    curves, curve_proofs = [], []
    for e in catalog:
        id = e["id"]; h = handling[id]; m = mappings[id]
        c = dict(id=id, baseHandlingStat=h["handling"], ready=None, stow=None, ads=None)
        cp = dict(id=id, mapping=m, handlingBaseline=h, aimBaseline=aim[id])
        if h["supported"]:
            stat = by_stats[id]["stats"]["943549884"]
            require(stat == h["handling"], "original Handling stat: " + id)
            source = formulas[m["family"]]["cat"][m["category"]]["handling"]
            for key in ("ready", "stow", "ads"):
                if key != "ads" or e["family"] != "glaive":
                    c[key] = {k: source[key].get(k, 0.0) for k in ("evpp", "vpp", "offset")}
            def seconds(key, value):
                q = c[key]
                return q["evpp"] * value * value + q["vpp"] * value + q["offset"]
            require(math.ceil(seconds("ready", stat) * 20) == h["readyTicks"]
                    and math.ceil(max(seconds("stow", stat), seconds("stow", 100)) * 20) == h["stowTicks"], "W58/extension baseline: " + id)
            if c["ads"] is not None:
                require(max(2, min(20, math.ceil(seconds("ads", stat) * 20))) == aim[id]["transitionTicks"], "W44/extension ADS baseline: " + id)
            require(all(seconds(k, 100) > 0 for k in ("ready", "stow", "ads") if c[k] is not None), "positive supported curve")
            cp["rawHandling"] = source
        else:
            require(e["family"] == "sword", "unsupported policy")
            cp["unsupportedReason"] = "No pinned sword curves; preserve existing unsupported timing"
        curves.append(c); curve_proofs.append(cp)
    require(len(curves) == 65 and sum(c["ready"] is not None for c in curves) == 60
            and sum(c["ads"] is not None for c in curves) == 59, "all current canonical curve coverage")
    snapshot = data(PREFIX + "w68-snapshot.json")
    resource = dict(stage="W202", perk=dict(id="steady_hands", hash=BASE, initialTicks=170,
        refreshTicks=130, handlingBonus=100, handlingScalar=.825), weapons=rolls, curves=curves,
        snapshotRolls=snapshot["rolls"], primarySnapshotScalar=snapshot["primaryScalar"], specialSnapshotScalar=snapshot["specialScalar"])
    source = dict(stage="W202", checked="2026-10-27", manifestVersion=VERSION, sourcePins=PINS,
        generatorSHA256=sha(Path(__file__).read_bytes()), resourceSHA256=sha(encode(resource)),
        baseDefinition=definition, socketProofs=proof, catalogScan=audit, curveProofs=curve_proofs,
        ddc=dict(tab="Weapon Perks", row=208, rowID="1662574278R207", rawHTML=row, baseText=text,
            url="https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278"),
        policies=dict(enhanced="9.5 seconds excluded; no PvE/PvP split stated", units="20TPS local adaptation: 8.5s=170ticks, refresh6.5s=130ticks",
            refresh="Source weapon paid final blows only; while active replace expiry with now+130, even when shorter; after expiry start170",
            lifecycle="Original equipped count-one stack/owner/world/data/runtime/class/loadout/entry/selected exact tuple; ordinary stow retained",
            timing="Raw Handling100; .825 ready/stow only, TD .9/.81, active Pulse .95, ready-only active Quickdraw .95, one ceil",
            ads="Raw Handling100; no Steady/TD/Pulse/QD time scalar; exact Snapshot entry only .5 primary/.8 special",
            incoming="Master selecting hook caches legitimate TD sample before incoming duration; no scans from getters"),
        limitations=["W46 Oracle May20 historical community curves and Oct13 official base stats are distinct snapshots; no current exact D2 duration claim.",
            "W83/W84 additive exotic resources loaded by current WeaponExotics include Ace and Izanagi; no separate w121 file exists in this baseline.",
            "Five sword curves remain unsupported; glaive ready/stow supported but ADS unsupported.",
            "No armor/unknown exotic animation scalar or invented D2 current curve; existing positive raw stat contributors are redundant at100."])
    return {PREFIX + "w202-steady-hands.json": encode(resource), "art/weapons/w202/steady-hands/source.json": encode(source)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    for name, content in generate(args.root.resolve()).items():
        path = args.root / name
        if args.verify:
            require(path.read_bytes() == content, "Generated drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content)
        print(("verified " if args.verify else "wrote ") + name)


if __name__ == "__main__":
    main()
