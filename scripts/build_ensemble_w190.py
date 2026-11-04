#!/usr/bin/env python3
"""Rebuild W190's two JSON outputs from pinned offline official/DDC inputs.
--verify compares without writing. No game, Gradle, numeric perk tests or network.
"""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons/"
TARGET = PREFIX + "w190-ensemble.json"
SOURCE = "art/weapons/w190/ensemble/source.json"
BASE, ENHANCED, TRAIT = 2621346526, 2495011826, 4241085061
VERSION = "245114.26.10.13.2000-1-bnet.66137"
KEYS = ("id", "hash", "socket", "perkHash", "plugSetHash")
EXPECTED = dict(zip(KEYS, ("canis_major", 2066434718, 3, BASE, 4037911937)))
PINS = {
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugsets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "ddc": "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437",
    "w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    "w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    "w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "w183-surplus.json": "3a54d901e618b2472c8a2beff905ecb21d9aa0316628a0416adaf91242fccef6",
    "w46-timing.json": "e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07",
    "w58-handling.json": "4de7d346a93c822784fafa69b62ac66148d51cc11cf2da6706367682b414d3f1",
    "w44-aim.json": "0d0a38469c28a74c1a77489d346184eccef347a604c0c0c455d1c7c2e1a80fc8",
    "w61-kill-clip.json": "fb3374e775b9313619f34c1dda5681d391577c15279aa140f9fdc59b2d2ebd9a",
    "w66-rampage.json": "d03a2518629ce36aac140837f92950083c1a546c14f6cd5ff3310cac1f08f6e0",
    "w181-vorpal.json": "221b1ba84382272dbc679684a9885e9cee8399ef98714a76f113bdbdd930d76e",
}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def generate(args):
    paths = {key: args.root / PREFIX / key for key in PINS if key.endswith(".json")}
    paths.update({key: getattr(args, key) for key in ("inventory", "plugsets", "manifest", "ddc")})
    data, pins = {}, {}
    for key, path in paths.items():
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        require(digest == PINS[key], "source drift: " + key)
        pins[key] = {"sha256": digest, "bytes": len(raw)}
        data[key] = json.loads(raw) if key != "ddc" else raw.decode()
    manifest = data["manifest"]["Response"]
    require(manifest["version"] == VERSION, "manifest version")
    components = manifest["jsonWorldComponentContentPaths"]["en"]
    for name in ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition"):
        require(components[name] == "/common/destiny2_content/json/en/" + name
                + "-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json", "component version")
    inventory, pools = data["inventory"], data["plugsets"]
    same_name = [d for d in inventory.values() if d.get("displayProperties", {}).get("name") == "Ensemble"]
    require({d["hash"] for d in same_name} == {BASE, ENHANCED}, "base/enhanced definitions")
    for d in same_name:
        require(d["itemType"] == 19 and not d["redacted"] and not d["blacklisted"]
                and not d["plug"]["isDummyPlug"] and d["itemTypeDisplayName"]
                == ("Trait" if d["hash"] == BASE else "Enhanced Trait"), "trait definition")
    selected = list(data["w40-characteristics.json"])
    for name in ("w83-exotics.json", "w84-exotics.json"):
        selected += [r["characteristics"] for r in data[name]]
    require(len(selected) == len({r["bungieHash"] for r in selected}) == 65, "selected catalog65")

    def traits(item):
        return {n for cat in item["sockets"]["socketCategories"]
                if cat["socketCategoryHash"] == TRAIT for n in cat["socketIndexes"]}

    def official(weapon, socket, perk):
        item = inventory[str(weapon["bungieHash"])]
        source = item["sockets"]["socketEntries"][socket]
        pool_hash = source.get("randomizedPlugSetHash")
        pool = pools.get(str(pool_hash), {})
        matches = [m for m in pool.get("reusablePlugItems", [])
                   if m.get("plugItemHash") == perk and m.get("currentlyCanRoll") is True]
        if (weapon["exotic"] or socket not in traits(item) or pool.get("isFakePlugSet") is not False
                or not matches):
            return None
        return dict(zip(KEYS, (weapon["id"], weapon["bungieHash"], socket, perk, pool_hash)))

    rows, scans = [], []
    for weapon in selected:
        item = inventory[str(weapon["bungieHash"])]
        require(item["hash"] == weapon["bungieHash"] and item["itemType"] == 3
                and not item["redacted"] and not item["blacklisted"], "canonical weapon")
        matches = [roll for n in traits(item) if (roll := official(weapon, n, BASE))]
        rows += matches
        scans.append({"id": weapon["id"], "hash": weapon["bungieHash"], "exotic": weapon["exotic"], "matches": matches})
    require(rows == [EXPECTED], "exact Canis Major base socket3 only")
    weapon = next(w for w in selected if w["id"] == "canis_major")
    item = inventory[str(EXPECTED["hash"])]
    pairs, audit = [], []
    for perk, file in (("kill_clip", "w61-kill-clip.json"), ("rampage", "w66-rampage.json"),
                       ("vorpal", "w181-vorpal.json"), ("surplus", "w183-surplus.json")):
        candidates = [r for r in data[file]["weapons"] if r["id"] == "canis_major"]
        require(len(candidates) == 1, "companion source " + perk)
        roll = candidates[0]
        require(roll == official(weapon, roll["socket"], roll["perkHash"]), "official companion " + perk)
        distinct = roll["socket"] != EXPECTED["socket"]
        audit.append({"perk": perk, "roll": roll, "allowed": distinct,
                      "reason": "DISTINCT_SOCKET" if distinct else "SAME_SOCKET"})
        if distinct:
            pairs.append({"id": weapon["id"], "perk": perk, "roll": roll})
    require(not audit[-1]["allowed"] and audit[-1]["roll"]["socket"] == 3, "no Surplus combination")
    # Reuse the already pinned raw historical curves, never derive ratios from rounded ticks.
    curve = next(c for c in data["w183-surplus.json"]["curves"] if c["id"] == "canis_major")
    require(curve["baseHandlingStat"] == weapon["stats"]["943549884"]
            and curve["baseReloadStat"] == weapon["stats"]["4188031367"]
            and not curve["shellReload"] and curve["snapshotScalar"] is None, "raw curve stats/topology")
    row_html = [r for r in re.findall(r"<tr\b[^>]*>.*?</tr>", data["ddc"], re.S) if ">Ensemble<" in r]
    require(len(row_html) == 1, "unique DDC row")
    row_text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", row_html[0])).split())
    require(row_text.startswith("86 Ensemble") and all(s in row_text for s in
            ("ally", "within 15 metres", "+30", "+40", "1.5 seconds")), "DDC Weapon Perks row86")
    resource = {"stage": "W190", "perk": {"id": "ensemble", "hash": BASE, "radiusMetres": 15,
                "handlingBonus": 30, "reloadBonus": 40, "lingerSeconds": 1.5, "lingerTicks": 30},
                "policies": {"enhanced": "EXCLUDED", "geometry": "LOCAL_EUCLIDEAN_FOOTPOINT_INCLUSIVE_NO_LOS_1_BLOCK_PER_METRE",
                "ally": "OTHER_ALIVE_CONNECTED_NONSPECTATOR_SERVER_PLAYER_SAME_LEVEL_BOTH_UNTEAMED_OR_VANILLA_ALLIED",
                "state": "ACTUAL_EQUIPPED_STACK_OWNER_LEVEL_EXISTING_GUARDIAN_DATA_RUNTIME_CLASS_HELD_OR_ACCEPTED_SELECTION",
                "timing": "TOTAL_STATS_CAP100_RAW_CURVES_CEIL_ONCE_NO_ENSEMBLE_SCALAR",
                "coSelectedStatProviders": [], "surplus": "SAME_SOCKET3_EXCLUDED"},
                "weapons": rows, "curves": [curve], "coSelections": pairs}
    socket_proof = [{"socket": n, "socketEntry": item["sockets"]["socketEntries"][n],
                     "plugSet": pools[str(item["sockets"]["socketEntries"][n]["randomizedPlugSetHash"])]}
                    for n in (3, 4)]
    evidence = {"stage": "W190", "version": VERSION, "sourcePins": pins,
                "manifestComponents": {k: components[k] for k in ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
                "ddc": {"url": "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1662574278",
                        "tab": "Weapon Perks", "row": 86, "retrievedDate": "2026-10-27", "text": row_text,
                        "baseOnly": True, "conversion": "1.5 seconds * 20 TPS = 30 ticks exactly; no rounding"},
                "definitions": [{"hash": d["hash"], "type": d["itemTypeDisplayName"], "accepted": d["hash"] == BASE} for d in same_name],
                "catalogScans": scans, "socketProof": socket_proof, "companionAudit": audit,
                "curves": {"source": PREFIX + "w183-surplus.json", "origin": "D2Foundry historical oracle dcd0c7d302b056ffbb532edcb711d724a17ca8c1",
                           "currentDestinyTimingVerified": False, "curve": curve},
                "resourceSha256": hashlib.sha256(encode(resource)).hexdigest()}
    return {TARGET: resource, SOURCE: evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    parser.add_argument("--plugsets", type=Path, default=Path("/tmp/destiny-weapons-w60/bungie-plugsets.json"))
    parser.add_argument("--manifest", type=Path, default=Path("/tmp/destiny-weapons-w60/manifest.json"))
    parser.add_argument("--ddc", type=Path, default=Path("/private/tmp/destiny-w190/ddc-perks.html"))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    for name, value in generate(args).items():
        path, raw = args.root / name, encode(value)
        if args.verify:
            require(path.read_bytes() == raw, "generated output drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        print(("verified " if args.verify else "wrote ") + name)


if __name__ == "__main__":
    main()
