#!/usr/bin/env python3
"""Build only W181 Vorpal's filtered pinned evidence and resource, offline.
--verify is read-only; --self-test checks negative sockets and determinism.
No enhanced traits, implicit/default selections, game, Gradle, or network.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = "art/weapons/w181/vorpal/"
TARGET = "src/main/resources/destiny/weapons/w181-vorpal.json"
SCRIPT = "scripts/build_vorpal_profile_w181.py"
BASE, ENHANCED, TRAIT = 1546637391, 3418165135, 4241085061
VERSION = "245114.26.10.13.2000-1-bnet.66137"
KEYS = ("id", "hash", "socket", "perkHash", "plugSetHash")
# Reviewed exact catalog intersection, never a family-wide grant.
EXPECTED = {
    ("seventh_seraph_officer_revolver", 3037520408, 4, BASE, 3527094473),
    ("steelfeather_repeater", 1251729046, 4, BASE, 2645685327),
    ("patron_of_lost_causes", 2723241847, 4, BASE, 120674550),
    ("aishas_embrace", 2638190703, 4, BASE, 4211351701),
    ("farewell", 541188001, 4, BASE, 3819615926),
    ("whispering_slab", 211938782, 4, BASE, 967526625),
    ("bite_of_the_fox", 1403800851, 4, BASE, 2442672691),
    ("first_in_last_out", 3616586446, 4, BASE, 1439234589),
    ("hollow_words", 607191995, 4, BASE, 1485010760),
    ("stormchaser", 3652506829, 4, BASE, 4213354588),
    ("canis_major", 2066434718, 4, BASE, 2791121719),
    ("dimensional_hypotrochoid", 1311684613, 4, BASE, 1092097342),
    ("salvager_s_salvo", 2060863616, 4, BASE, 254),
    ("retrofit_escapade", 3103325054, 4, BASE, 2461260598),
    ("crown_splitter", 2782325302, 4, BASE, 99092784),
    ("temptation_s_hook", 35794111, 4, BASE, 2147541212),
    ("nezarec_s_whisper", 254636484, 4, BASE, 699056095),
}
PERK = {"id": "vorpal_weapon", "hash": BASE,
        "primaryMultiplier": 1.20, "specialMultiplier": 1.15, "heavyMultiplier": 1.10,
        "damageSource": ART + "clarity-source.json"}
PINS = {
    "src/main/resources/destiny/weapons/w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    "src/main/resources/destiny/weapons/w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "src/main/resources/destiny/weapons/w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    "src/main/resources/destiny/weapons/w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "clarity": "881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
}
NATIVE_PENDING = [
    "Master registry: explicit base selection, new/default/enhanced/corrupt socket inert; UI exact17 only.",
    "Paid PRIMARY/SPECIAL/HEAVY 1.20/1.15/1.10 versus native WitherBoss and EnderDragon.",
    "Ordinary/high-HP/named mob inert; destiny_boss/destiny_vehicle Mob tagged at impact eligible; untag removes bonus.",
    "Tagged Player/ArmorStand/nonmob, dead/removed target inert; no PvP or nonliving vehicle damage expansion.",
    "Direct and splash evaluate each target independently with one paid source token, including mixed target AoE.",
    "Paid projectile/beam/wave/sword source snapshot survives stow and edit; new unselected/invalid/super source inert.",
    "Source current held/equipped genuine stack only; preview/wrong slot/dead/disconnected/spectator/super rejected.",
    "Glaive projectile eligible; glaive melee and abilities inert; paid sword contacts eligible; no free attack capture.",
    "No countdown HUD, timer, stacks, bonus stat, ammo/cadence changes, or fresh source credit from target checks.",
]


def require(ok, why):
    if not ok:
        raise ValueError(why)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def eligible(index, traits, field, pool, match, exotic):
    # W320 follow-up: curated fixed-roll legendaries expose a reusablePlugSetHash with isFakePlugSet true.
    randomized = field == "randomizedPlugSetHash" and pool.get("isFakePlugSet") is False
    curated = field == "reusablePlugSetHash" and pool.get("isFakePlugSet") is True
    return (not exotic and index in traits and (randomized or curated)
            and match.get("plugItemHash") == BASE and match.get("currentlyCanRoll") is True)


def validate(resource):
    require(set(resource) == {"stage", "perk", "weapons"} and resource["stage"] == "W181"
            and resource["perk"] == PERK, "exact mechanics/schema")
    rows = resource["weapons"]
    require(all(set(r) == set(KEYS) and isinstance(r["id"], str)
                and all(type(r[k]) is int for k in KEYS[1:]) for r in rows), "roll schema")
    values = [tuple(r[k] for k in KEYS) for r in rows]
    require(len(values) == len(set(values)) == 17 and set(values) == EXPECTED, "exact17 base sockets")


def generate(args):
    paths = {k: args.root / k for k in PINS if "/" in k}
    paths.update(inventory=args.inventory, plugSets=args.plugsets, manifest=args.manifest, clarity=args.clarity)
    data, pins = {}, {}
    for key, path in paths.items():
        raw = path.read_bytes()
        require(digest(raw) == PINS[key], "source SHA mismatch: " + key)
        data[key] = json.loads(raw)
        pins[key] = {"sha256": digest(raw), "bytes": len(raw)}
    prefix = "src/main/resources/destiny/weapons/"
    catalog = data[prefix + "w30.json"][:]
    selected = data[prefix + "w40-characteristics.json"][:]
    for f in ("w83-exotics.json", "w84-exotics.json"):
        catalog += [r["catalog"] for r in data[prefix + f]]
        selected += [r["characteristics"] for r in data[prefix + f]]
    require(len(selected) == len({w["id"] for w in selected}) == len({w["bungieHash"] for w in selected})
            == len(catalog) == 65 and {w["id"] for w in selected} == {w["id"] for w in catalog}, "selected65")
    manifest = data["manifest"]["Response"]
    require(manifest["version"] == VERSION, "official manifest version")
    for component in ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition"):
        require(manifest["jsonWorldComponentContentPaths"]["en"][component] ==
                "/common/destiny2_content/json/en/" + component + "-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json",
                "component version")
    inv, pools = data["inventory"], data["plugSets"]
    same = {d["hash"] for d in inv.values() if d.get("displayProperties", {}).get("name") == "Vorpal Weapon"}
    require(same == {BASE, ENHANCED}, "unknown same-name trait")
    definitions = []
    for h in sorted(same):
        d = inv[str(h)]
        require(d["hash"] == h and d["itemType"] == 19 and not d["redacted"] and not d["blacklisted"]
                and not d["plug"]["isDummyPlug"]
                and d["itemTypeDisplayName"] == ("Trait" if h == BASE else "Enhanced Trait"), "trait definition")
        definitions.append({"hash": h, "accepted": h == BASE,
                            "displayProperties": {k: d["displayProperties"][k] for k in ("name", "description")},
                            "itemType": d["itemType"], "itemTypeDisplayName": d["itemTypeDisplayName"],
                            "isDummyPlug": d["plug"]["isDummyPlug"],
                            "redacted": d["redacted"], "blacklisted": d["blacklisted"]})
    rows, proofs, scans, excluded = [], [], [], []
    for w in selected:
        d = inv[str(w["bungieHash"])]
        require(d["hash"] == w["bungieHash"] and d["itemType"] == 3
                and not d["redacted"] and not d["blacklisted"]
                and (d["inventory"]["tierType"] == 6) == w["exotic"], "selected official identity")
        require(d["equippingBlock"]["ammoType"] == {"PRIMARY": 1, "SPECIAL": 2, "HEAVY": 3}[w["ammo"]], "official ammo")
        s = d.get("sockets", {})
        traits = {n for c in s.get("socketCategories", []) if c["socketCategoryHash"] == TRAIT for n in c["socketIndexes"]}
        scan = {"id": w["id"], "hash": d["hash"], "exotic": w["exotic"], "ammo": w["ammo"],
                "traitIndexes": sorted(traits), "references": []}
        for n, sock in enumerate(s.get("socketEntries", [])):
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                ph = sock.get(field)
                if not ph:
                    continue
                pool = pools[str(ph)]
                require(pool["hash"] == ph and not pool["redacted"] and not pool["blacklisted"], "official pool")
                matches = [m for m in pool.get("reusablePlugItems", []) if m["plugItemHash"] in same]
                # Filtered references suffice to reproduce inclusion and absence for all65.
                scan["references"].append({"socket": n, "field": field, "plugSetHash": ph,
                                           "isFakePlugSet": pool["isFakePlugSet"], "matches": matches})
                for match in matches:
                    if eligible(n, traits, field, pool, match, w["exotic"]):
                        require(d["inventory"]["tierType"] == 5, "legendary source")
                        row = dict(zip(KEYS, (w["id"], d["hash"], n, BASE, ph)))
                        rows.append(row)
                        proofs.append({**row, "ammo": w["ammo"], "socketCategoryHash": TRAIT,
                                       "socketEntry": sock, "matchingEntry": match})
                    else:
                        excluded.append({"id": w["id"], "socket": n, "field": field,
                                         "plugSetHash": ph, "isFakePlugSet": pool["isFakePlugSet"], "match": match})
        scans.append(scan)
    clarity = data["clarity"][str(BASE)]
    blocks = clarity["descriptions"]["en"]
    text = "\n".join("".join(l.get("text", "") for l in b.get("linesContent", [])) for b in blocks)
    require(clarity["hash"] == BASE and clarity["type"] == "Weapon Trait"
            and "Minibosses, Bosses, and Vehicles" in text and "Players in their Super Ability" in text, "target source")
    for label, percent in (("Primary Weapons: ", "20%"), ("Special Weapons: ", "15%"), ("Power Weapons: ", "10%")):
        matching = [b for b in blocks if any(l.get("text") == label for l in b.get("linesContent", []))]
        require(len(matching) == 1 and [l["text"] for l in matching[0]["linesContent"]
                                      if "pve" in l.get("classNames", [])] == [percent], "PvE percent semantics")
    resource = {"stage": "W181", "perk": PERK, "weapons": rows}
    validate(resource)
    outputs = {
        TARGET: resource,
        ART + "official-sockets.json": {"version": VERSION, "definitions": definitions,
            "selectedCount": 65, "rolls": rows, "proofs": proofs, "scans": scans, "excluded": excluded},
        ART + "clarity-source.json": {"source": "https://github.com/Clarity-Destiny/Descriptions",
            "cacheSha256": PINS["clarity"], "base": clarity, "enhancedExcludedHash": ENHANCED,
            "pveIncreases": {"PRIMARY": "20%", "SPECIAL": "15%", "HEAVY": "10%"},
            "multiplierSemantics": "1 + percent / 100; multiplicative weapon damage scalar, not flat damage or stat points",
            "mechanics": PERK},
    }
    outputs[ART + "manifest.json"] = {"stage": "W181", "generator": SCRIPT,
        "generatorSha256": digest((args.root / SCRIPT).read_bytes()), "sourcePins": pins, "version": VERSION,
        "outputs": {k: digest(encode(v)) for k, v in outputs.items()}, "nativePending": NATIVE_PENDING,
        "policies": {"capture": "PAID_EMISSION_ONLY_CURRENT_SELECTED_GENUINE_HELD_EQUIPPED_VALID_ALIVE_NOT_SUPER",
                     "snapshot": "IMMUTABLE_SOURCE_ENTRY_EXACT_ROLL_SCALAR_SURVIVE_STOW_EDIT_NO_FRESH_CREDIT",
                     "target": "AT_IMPACT_LIVE_WITHERBOSS_ENDERDRAGON_OR_MOB_TAG_DESTINY_BOSS_DESTINY_VEHICLE",
                     "excluded": "PLAYER_ARMORSTAND_DEAD_REMOVED_SPECTATOR_NONMOB_HP_NAME_HEURISTICS",
                     "damage": "MASTER_DIRECT_SPLASH_EACH_TARGET_INDEPENDENT_PAID_SWORD_ALLOWED_GLAIVE_MELEE_ABILITIES_INERT",
                     "hud": "TARGET_CONDITIONAL_PASSIVE_NO_COUNTDOWN_STACK_SESSION_TIMER"},
        "limitations": ["Pinned official manifest version above; no claim of an unpinned later live refresh.",
            "Original Clarity includes minibosses and players in Super. Local destiny_boss is the explicit mob classification; no HP/name inference.",
            "Project damage excludes players, so PvP bonuses are not implemented. Nonliving vehicles are out of scope.",
            "Master owns shared perk selection/registration, runtime damage wiring and native actualGT."]}
    return outputs


def self_test(outputs):
    resource = outputs[TARGET]
    checks = 0
    def rejects(value):
        nonlocal checks
        try:
            validate(value)
        except (ValueError, TypeError, KeyError):
            checks += 1
            return
        raise AssertionError("mutation accepted")
    for rows in (resource["weapons"][:-1], resource["weapons"] + [resource["weapons"][0]]):
        rejects({**resource, "weapons": rows})
    for key, value in (("perkHash", ENHANCED), ("socket", 3), ("hash", 1), ("plugSetHash", 1), ("socket", "4")):
        x = copy.deepcopy(resource)
        x["weapons"][0][key] = value
        rejects(x)
    x = copy.deepcopy(resource)
    x["perk"]["primaryMultiplier"] = 20
    rejects(x)
    rejects({**resource, "timerTicks": 100})
    pool, match = {"isFakePlugSet": False}, {"plugItemHash": BASE, "currentlyCanRoll": True}
    require(eligible(4, {4}, "randomizedPlugSetHash", pool, match, False), "positive socket")
    for args in ((3, {4}, "randomizedPlugSetHash", pool, match, False),
                 (4, {4}, "reusablePlugSetHash", pool, match, False),
                 (4, {4}, "randomizedPlugSetHash", {"isFakePlugSet": True}, match, False),
                 (4, {4}, "randomizedPlugSetHash", {}, match, False),
                 (4, {4}, "randomizedPlugSetHash", pool, dict(match, currentlyCanRoll=False), False),
                 (4, {4}, "randomizedPlugSetHash", pool, dict(match, plugItemHash=ENHANCED), False),
                 (4, {4}, "randomizedPlugSetHash", pool, dict(match, currentlyCanRoll=1), False),
                 (4, {4}, "randomizedPlugSetHash", pool, match, True)):
        require(not eligible(*args), "negative socket")
        checks += 1
    return checks


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    p.add_argument("--plugsets", type=Path, default=Path("/tmp/destiny-weapons-w60/bungie-plugsets.json"))
    p.add_argument("--manifest", type=Path, default=Path("/tmp/destiny-weapons-w60/manifest.json"))
    p.add_argument("--clarity", type=Path, default=Path("/private/tmp/w167-clarity.json"))
    p.add_argument("--verify", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    outputs = generate(args)
    if args.self_test:
        checks = self_test(outputs)
        require({k: encode(v) for k, v in outputs.items()} ==
                {k: encode(v) for k, v in generate(args).items()}, "deterministic repeat")
        print("negative checks", checks, "deterministic repeat PASS")
    for name, value in outputs.items():
        dest, raw = args.root / name, encode(value)
        if args.verify:
            require(dest.read_bytes() == raw, "generated drift: " + name)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
    print("W181 exact17, selected65, four filtered JSON outputs", "VERIFIED" if args.verify else "GENERATED")


if __name__ == "__main__":
    main()
