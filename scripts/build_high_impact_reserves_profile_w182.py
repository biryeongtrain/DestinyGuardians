#!/usr/bin/env python3
"""Build only W182 High-Impact Reserves's filtered pinned evidence and resource, offline.
--verify is read-only; --self-test checks negative sockets and determinism.
No enhanced traits, implicit/default selections, game, Gradle, or network.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = "art/weapons/w182/high_impact_reserves/"
TARGET = "src/main/resources/destiny/weapons/w182-high_impact_reserves.json"
SCRIPT = "scripts/build_high_impact_reserves_profile_w182.py"
BASE, ENHANCED, TRAIT = 2213355989, 2002547233, 4241085061
VERSION = "245114.26.10.13.2000-1-bnet.66137"
KEYS = ("id", "hash", "socket", "perkHash", "plugSetHash")
# Reviewed exact catalog intersection, never a family-wide grant.
EXPECTED = {
    ("seventh_seraph_officer_revolver", 3037520408, 4, BASE, 3527094473),
    ("bygones", 2712244741, 3, BASE, 1760176771),
    ("chattering_bone", 568515759, 4, BASE, 423791138),
    ("blast_furnace", 3843477312, 4, BASE, 169306153),
    ("claws_of_the_wolf", 1280933460, 4, BASE, 753756428),
    ("long_arm", 8293111, 4, BASE, 619833418),
    ("bug_out_bag", 2744715540, 4, BASE, 575371383),
    ("high_albedo", 1197486957, 4, BASE, 718633408),
    ("dream_breaker", 2931957300, 4, BASE, 1206254527),
    ("hammerhead", 603242241, 4, BASE, 2479293397),
}
MAPPING = "MEASURED_2019_40ROUND_QUANTIZED_ENDPOINT_NORMALIZATION_W182_NOT_CURRENT_EXACT_FORMULA"
PERK = {"id": "high_impact_reserves", "hash": BASE,
        "normalMinimum": 1.121, "normalMaximum": 1.256,
        "fusionMinimum": 1.103, "fusionMaximum": 1.229,
        "mapping": MAPPING, "damageSource": ART + "clarity-source.json"}
# Firsthand body-shot table, source edited2019-11-18. Index = rounds AFTER that shot
# in a40-round magazine. Preserve ALL measured rungs; no invented uniform ranks/ramp.
MEASURED = [595,595,595,595,595,582,570,568,556,555,544,543,542,541,531,531,531,531,531,530,530]
RESEARCH = [
    {"url": "https://www.bungie.net/en/Forums/Post/254403883", "author": "JadeRabbitEmperor",
     "date": "2019-11-18", "baselineDamage": 473, "magazine": 40,
     "shotDamageGroups": [[1,19,473],[20,21,530],[22,26,531],[27,27,541],[28,28,542],
         [29,29,543],[30,30,544],[31,31,555],[32,32,556],[33,33,568],[34,34,570],[35,35,582],[36,40,595]],
     "finding": "Dated firsthand body-shot observations, all12 nonneutral damage values preserved. Small-mag tests differ; not a current general formula."},
    {"url": "https://www.reddit.com/r/DestinyTheGame/comments/lpc5a9/", "author": "YeezyReddit",
     "date": "2021-02-21", "finding": "Firsthand Palindrome10 test reports plateaus and15/23 percent intermediates. Does not validate a universal mapping; no raw Reddit cache shipped."},
    {"url": "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1662574278",
     "sheet": "Weapon Perks", "row": 119, "retrievedAt": "2026-10-26T19:58:37Z",
     "finding": "Current retrieved row adds maximum effect at7.5% magazine, below50% base threshold; exact normal PvE endpoints12.1/25.6. No intermediate formula or integer rounding supplied."},
    {"url": "https://github.com/d2foundry/oracle_engine/blob/dcd0c7d302b056ffbb532edcb711d724a17ca8c1/src/perks/year_1_perks.rs",
     "commit": "dcd0c7d302b056ffbb532edcb711d724a17ca8c1", "commitDate": "2026-05-20T00:04:31Z",
     "finding": "Rejected as validation: HIR guard curr_mag<=curr_mag/2 cannot activate at positive ammo; includes no reduced fusion endpoints. Do not copy its apparent linear interpolation as exact mechanics."},
    {"url": "https://github.com/katzerax/Destiny2DPSGraphPY/blob/70252413562c66df886a7fffe79f67d8b48f1711/backend/perks.py",
     "finding": "Rejected as fidelity source: linear approximation uses1.125/1.255 despite docstring12.1/25.6 and obsolete enhanced75%."},
]
DISCRETE = {"status": MAPPING,
    "basis": "All measured2019 body-shot rungs retained, projected conservatively to canonical integer magazines; Clarity endpoints normalize old display damage rounding. This is a documented local adaptation, not current exact Destiny behavior.",
    "referenceDamageByRoundsAfter0Through20": MEASURED,
    "integerRule": "Require1<=roundsBefore<=canonicalBaseCapacity. after=roundsBefore-1. Above half after:1.0. Otherwise referenceAfter=ceil(40*after/capacity), integer arithmetic. Look up measured damage at that index; no interpolation between measured rungs.",
    "scalarRule": "minimumMultiplier+(measuredDamage-530)*(maximumMultiplier-minimumMultiplier)/65. Normal1.121..1.256; fusion1.103..1.229. Rescales measured DAMAGE differences, not equal rank increments.",
    "oddCapacity": "After-shot coordinate means first paid affected shot has roundsBefore=floor(capacity/2)+1, for odd and even capacities. This is explicitly an adaptation from the dated40-round test.",
    "lastCartridge": "roundsBefore1 is a paid cartridge with after0 and maximum. Input0 has no payable cartridge: profile throws; capture returnsNONE.",
    "ambiguity": "No retrieved current primary source establishes general integer formula. Dated40-round maximum plateau starts10% AFTER shot (12.5% BEFORE), whereas current Compendium says7.5% and cached Clarity only says empty. Small-mag observations differ. Projection, coordinate convention and endpoint normalization are authored adaptations of measured data, not resolved current fidelity."}

PINS = {
    "src/main/resources/destiny/weapons/w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    "src/main/resources/destiny/weapons/w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "src/main/resources/destiny/weapons/w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    "src/main/resources/destiny/weapons/w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "clarity": "881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
    "compendium": "7880b2029a7e7b8f97afb8f079ca48a585ec0765a94b6b3f983a47daf983ba30",
    "measurements": "59d8d8a5c3edb6929a3e5b4146dcc1f82242b5b7a8f0379afcf0f5d8cb59835a",
}
NATIVE_PENDING = [
    "Master registration: exact10 base selections; fresh/default/enhanced/corrupt/unsupported inert.",
    "Officer cap11: pre7 neutral, pre6 minimum1.121, pre1 maximum1.256. Long Arm cap14: pre9 neutral, pre8 minimum1.121, pre1 maximum1.256.",
    "Bygones cap38 ordinary3-bullet burst: recapture after each paid bullet using true pre-consumption rounds; crossing21->20 is neutral->minimum.",
    "Dream Breaker cap6 shared7-bolt fusion: pre5 neutral, pre4 minimum1.103, pre3 measured-adapted1.10493846, pre2 measured-adapted1.17666154, pre1 maximum1.229; all7 bolts retain same cartridge token.",
    "No eligible aggressive LFR or projectile in selected65; do not broaden official sockets for test convenience.",
    "Payload/Dragonfly/perk-generated splash MUST receive Token.NONE; ability/glaive melee inert.",
    "Genuine inventory identity/equipped/live/connected/notSuper source only; selection/ammo reads never mint free damage.",
    "Already-paid token survives stow/edit/refund, no ammo reads at impact; next paid cartridge recaptures. No session/timer/stacks/HUD/countdown/cleanup.",
    "No native/pixel/audio claims: worker runs only isolated Python/JUnit; master owns actualGT and runtime hooks.",
]



def require(ok, why):
    if not ok:
        raise ValueError(why)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def eligible(index, traits, field, pool, match, exotic):
    return (not exotic and index in traits and field == "randomizedPlugSetHash"
            and pool.get("isFakePlugSet") is False and match.get("plugItemHash") == BASE
            and match.get("currentlyCanRoll") is True)


def validate(resource):
    require(set(resource) == {"stage", "perk", "weapons"} and resource["stage"] == "W182"
            and resource["perk"] == PERK
            and type(resource["perk"].get("hash")) is int
            and all(type(resource["perk"].get(k)) in (int, float)
                    for k in ("normalMinimum", "normalMaximum", "fusionMinimum", "fusionMaximum")), "exact mechanics/schema")
    rows = resource["weapons"]
    require(all(set(r) == set(KEYS) and isinstance(r["id"], str)
                and all(type(r[k]) is int for k in KEYS[1:]) for r in rows), "roll schema")
    values = [tuple(r[k] for k in KEYS) for r in rows]
    require(len(values) == len(set(values)) == 10 and set(values) == EXPECTED, "exact10 base sockets")


def generate(args):
    paths = {k: args.root / k for k in PINS if "/" in k}
    paths.update(inventory=args.inventory, plugSets=args.plugsets, manifest=args.manifest, clarity=args.clarity, compendium=args.compendium, measurements=args.measurements)
    data, pins = {}, {}
    for key, path in paths.items():
        raw = path.read_bytes()
        require(digest(raw) == PINS[key], "source SHA mismatch: " + key)
        data[key] = raw.decode() if key in ("compendium", "measurements") else json.loads(raw)
        pins[key] = {"sha256": digest(raw), "bytes": len(raw)}
    import csv, io
    ddc = [r for r in csv.reader(io.StringIO(data["compendium"])) if r and r[0] == "High-Impact Reserves"]
    require(len(ddc) == 1 and "7.5% Magazine" in ddc[0][2] and "12.1%" in ddc[0][2]
            and "25.6%" in ddc[0][2] and "below 50%" in ddc[0][2], "current compendium endpoints")
    import re
    section = data["measurements"].split("[b]Breytech Werewolf (Auto Rifle) 40 round mag[/b]", 1)[1].split("[b]The Long Goodbye", 1)[0]
    groups = [[int(start), int(end or start), int(damage)]
              for start, end, damage in re.findall(r"Shots? #(\d+)(?:-(\d+))?: (\d+)", section)]
    require(groups == RESEARCH[0]["shotDamageGroups"], "exact measured40 shot table")
    measured = {40 - shot: damage for start, end, damage in groups for shot in range(start, end + 1)}
    require([measured[n] for n in range(21)] == MEASURED, "measured table reconstruction")
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
    same = {d["hash"] for d in inv.values() if d.get("displayProperties", {}).get("name") == "High-Impact Reserves"}
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
            and "50% of its base capacity to empty" in text
            and "Fusion Rifles and Aggressive Frame Linear Fusion Rifles" in text
            and "Does not buff the Splash/Explosive damage elements of other perks." in text, "mechanics source")
    pve = [l["text"] for block in blocks for l in block.get("linesContent", []) if "pve" in l.get("classNames", [])]
    require(pve == ["12.1%", "25.6%"] and "10.3% and 22.9%" in text, "exact PvE endpoints")
    resource = {"stage": "W182", "perk": PERK, "weapons": rows}
    validate(resource)
    outputs = {
        TARGET: resource,
        ART + "official-sockets.json": {"version": VERSION, "definitions": definitions,
            "selectedCount": 65, "rolls": rows, "proofs": proofs, "scans": scans, "excluded": excluded},
        ART + "clarity-source.json": {"source": "https://github.com/Clarity-Destiny/Descriptions",
            "cacheSha256": PINS["clarity"], "base": clarity, "enhancedExcludedHash": ENHANCED,
            "pveIncreases": {"normal": ["12.1%", "25.6%"], "fusionAndAggressiveLfr": ["10.3%", "22.9%"]},
            "discreteMapping": DISCRETE, "additionalResearch": RESEARCH,
            "currentCompendiumRow": ddc[0],
            "researchPins": {k: pins[k] for k in ("compendium", "measurements")},
            "mechanics": PERK},
    }
    outputs[ART + "manifest.json"] = {"stage": "W182", "generator": SCRIPT,
        "generatorSha256": digest((args.root / SCRIPT).read_bytes()), "sourcePins": pins, "version": VERSION,
        "outputs": {k: digest(encode(v)) for k, v in outputs.items()}, "nativePending": NATIVE_PENDING,
        "policies": {"capture": "AFTER_SUCCESSFUL_PAID_EMISSION_WITH_TRUE_PRECONSUMPTION_ROUNDS_CANONICAL_BASECAP",
                     "authority": "GENUINE_CURRENT_OWNED_EQUIPPED_LIVE_CONNECTED_NOT_SUPER_EXACT_BASE_SELECTION",
                     "snapshot": "IMMUTABLE_ENTRY_ROLL_ROUNDS_BASECAP_SCALAR_SURVIVES_STOW_EDIT_REFUND",
                     "damage": "MASTER_PER_PAID_CARTRIDGE_SHARED_BOLTS_REUSE_ORDINARY_BULLETS_RECAPTURE_PERKSPLASH_NONE",
                     "lifecycle": "NO_SESSION_TIMER_STACK_COUNTDOWN_CLEANUP"},
        "limitations": [DISCRETE["ambiguity"], "Only base2213355989, enhanced2002547233 excluded.",
            "Pinned selected65 official manifest; no eligible aggressive LFR or projectile.",
            "PvP excluded by project. Master owns registry/runtime integration and native verification."]}

    return outputs


def authored_scalar(rounds, cap, fusion):
    require(type(rounds) is int and type(cap) is int and 1 <= rounds <= cap, "ammo integers")
    after = rounds - 1
    if after * 2 > cap:
        return 1.0
    reference = (40 * after + cap - 1) // cap
    low, high = (1.103, 1.229) if fusion else (1.121, 1.256)
    return low + (MEASURED[reference] - 530) * (high - low) / 65


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
    x["perk"]["normalMinimum"] = 20
    rejects(x)
    rejects({**resource, "timerTicks": 100})
    for key in resource:
        x = copy.deepcopy(resource); del x[key]; rejects(x)
    for key in PERK:
        x = copy.deepcopy(resource); del x["perk"][key]; rejects(x)
    for key, val in [("socket", 4.5), ("hash", True), ("perkHash", str(BASE)), ("plugSetHash", 0)]:
        x = copy.deepcopy(resource); x["weapons"][0][key] = val; rejects(x)
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
    for cap in range(2, 101):
        previous = 1.0
        for rounds in range(cap, 0, -1):
            value = authored_scalar(rounds, cap, False)
            require(previous <= value <= 1.256, "finite monotone discrete mapping")
            require((value == 1.0) == (2 * (rounds - 1) > cap), "integer half threshold")
            previous = value
        require(authored_scalar(1, cap, False) == 1.256, "last cartridge endpoint")
        require(authored_scalar(1, cap, True) == 1.229, "fusion last cartridge")
    for rounds, cap in [(0, 6), (-1, 6), (7, 6), (1, 0), (True, 6), (1, 6.0)]:
        try:
            authored_scalar(rounds, cap, False)
        except ValueError:
            checks += 1
        else:
            raise AssertionError("bad ammo accepted")
    for key, value in [("normalMaximum", float("nan")), ("fusionMinimum", "1.103"), ("mapping", "guessed_exact")]:
        x = copy.deepcopy(resource); x["perk"][key] = value; rejects(x)

    return checks


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    p.add_argument("--plugsets", type=Path, default=Path("/tmp/destiny-weapons-w60/bungie-plugsets.json"))
    p.add_argument("--manifest", type=Path, default=Path("/tmp/destiny-weapons-w60/manifest.json"))
    p.add_argument("--clarity", type=Path, default=Path("/private/tmp/w167-clarity.json"))
    p.add_argument("--compendium", type=Path, default=Path("/private/tmp/w182-hir-report/ddc-perks.csv"))
    p.add_argument("--measurements", type=Path, default=Path("/private/tmp/w182-hir-report/bungie-2019.html"))
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
    print("W182 exact10, selected65, four filtered JSON outputs; MEASURED TABLE ADAPTATION; current exact formula unresolved", "VERIFIED" if args.verify else "GENERATED")


if __name__ == "__main__":
    main()
