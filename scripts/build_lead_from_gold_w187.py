#!/usr/bin/env python3
"""Generate W187 base Lead from Gold from pinned official sockets and community mechanics.

Writes four owned JSON files only. --verify is read-only; --output-root allows
outside-repository reproduction. No Gradle, game, server, or media operations.
"""
import argparse
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASE, ENHANCED, TRAIT = 1556840489, 3442762221, 4241085061
VERSION = "245114.26.10.13.2000-1-bnet.66137"
COMPONENT_SUFFIX = "-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
KEYS = ("id", "hash", "socket", "perkHash", "plugSetHash")
ART = "art/weapons/w187/lead_from_gold/"
TARGET = "src/main/resources/destiny/weapons/w187-lead_from_gold.json"
SCRIPT = "scripts/build_lead_from_gold_w187.py"
LOCAL = {
    "catalog": "src/main/resources/destiny/weapons/w30.json",
    "characteristics": "src/main/resources/destiny/weapons/w40-characteristics.json",
    "exotics83": "src/main/resources/destiny/weapons/w83-exotics.json",
    "exotics84": "src/main/resources/destiny/weapons/w84-exotics.json",
}
PINS = {'catalog': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a', 'characteristics': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1', 'exotics83': 'bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56', 'exotics84': '481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e', 'inventory': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c', 'plugsets': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959', 'manifest': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce', 'clarity': '881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384', 'cachedClarity': '881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384', 'ddc': '6bd6dd4534aac0490e77cb4d94caba9f3de23e75a498fbf22c763c7013d95044'}
EXPECTED = [{'id': 'apostate', 'hash': 2164448701, 'socket': 3, 'perkHash': 1556840489, 'plugSetHash': 1306932196}, {'id': 'mindbender_s_ambition_adept', 'hash': 912150785, 'socket': 3, 'perkHash': 1556840489, 'plugSetHash': 1732284294}, {'id': 'hollow_words', 'hash': 607191995, 'socket': 3, 'perkHash': 1556840489, 'plugSetHash': 637298592}, {'id': 'dream_breaker', 'hash': 2931957300, 'socket': 3, 'perkHash': 1556840489, 'plugSetHash': 3785896921}, {'id': 'deafening_whisper', 'hash': 981718087, 'socket': 3, 'perkHash': 1556840489, 'plugSetHash': 3110206796}, {'id': 'nezarec_s_whisper', 'hash': 254636484, 'socket': 3, 'perkHash': 1556840489, 'plugSetHash': 210449465}]
PERK = {
    "id": "lead_from_gold", "hash": BASE, "reserveFraction": 0.25,
    "doubleSpecialFraction": 0.125, "worksStowed": True,
    "trigger": "accepted_real_heavy_pickup_transaction",
    "reserveBasis": "authored_WeaponProfile.reserve_capacity_excluding_magazine_and_overflow",
    "integerPolicy": "authored_single_ceiling_after_division_by_4_or_8",
    "originalRoundingVerified": False,
}
CLARITY_URL = "https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/live/descriptions/clarity.json"
DDC_URL = "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


class Rows(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "tr": self.row = []
        if tag in ("td", "th") and self.row is not None: self.cell = []
        if tag == "br" and self.cell is not None: self.cell.append(" ")

    def handle_data(self, data):
        if self.cell is not None: self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def eligible(index, traits, field, pool, match, exotic):
    return (not exotic and index in traits and field == "randomizedPlugSetHash"
            and pool.get("isFakePlugSet") is False
            and match.get("plugItemHash") == BASE and match.get("currentlyCanRoll") is True)


def validate(resource):
    require(set(resource) == {"stage", "perk", "weapons"}, "resource schema")
    require(resource["stage"] == "W187" and resource["perk"] == PERK, "base mechanics/policy")
    rows = resource["weapons"]
    require(all(set(r) == set(KEYS) and isinstance(r["id"], str)
                and all(type(r[k]) is int for k in KEYS[1:]) for r in rows), "roll schema")
    tuples = [tuple(r[k] for k in KEYS) for r in rows]
    require(len(tuples) == len(set(tuples)) == 6
            and set(tuples) == {tuple(r[k] for k in KEYS) for r in EXPECTED}, "exact6 base sockets")


def generate(args):
    paths = {k: args.root / v for k, v in LOCAL.items()}
    paths.update({k: getattr(args, k) for k in PINS if k not in LOCAL})
    data, pins = {}, {}
    for key, path in paths.items():
        raw = path.read_bytes()
        require(digest(raw) == PINS[key], "source SHA mismatch: " + key)
        pins[key] = {"sha256": digest(raw), "bytes": len(raw)}
        data[key] = json.loads(raw) if key != "ddc" else raw.decode()
    selected = data["characteristics"][:]
    for key in ("exotics83", "exotics84"):
        selected.extend(r["characteristics"] for r in data[key])
    require(len(selected) == len({r["id"] for r in selected})
            == len({r["bungieHash"] for r in selected}) == 65, "selected65")
    m = data["manifest"]["Response"]
    require(m["version"] == VERSION, "manifest version")
    for component in ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition"):
        require(m["jsonWorldComponentContentPaths"]["en"][component]
                == "/common/destiny2_content/json/en/" + component + COMPONENT_SUFFIX,
                "official component version")
    inv, pools = data["inventory"], data["plugsets"]
    variants = {d["hash"] for d in inv.values()
                if d.get("displayProperties", {}).get("name") == "Lead from Gold"}
    require(variants == {BASE, ENHANCED}, "same-name variants")
    for h in variants:
        d = inv[str(h)]
        require(d["hash"] == h and d["itemType"] == 19 and not d["redacted"]
                and not d["blacklisted"] and not d["plug"]["isDummyPlug"]
                and d["itemTypeDisplayName"] == ("Trait" if h == BASE else "Enhanced Trait"),
                "official trait definition")
    rows, proofs, scans, excluded = [], [], [], []
    for weapon in selected:
        d = inv[str(weapon["bungieHash"])]
        require(d["hash"] == weapon["bungieHash"] and d["itemType"] == 3
                and not d["redacted"] and not d["blacklisted"]
                and (d["inventory"]["tierType"] == 6) == weapon["exotic"], "official weapon")
        if not weapon["exotic"]:
            require({k: v["value"] for k, v in d["stats"]["stats"].items()}
                    == weapon["stats"], "official stats")
        sockets = d.get("sockets", {})
        traits = {n for c in sockets.get("socketCategories", [])
                  if c["socketCategoryHash"] == TRAIT for n in c["socketIndexes"]}
        scan = {"id": weapon["id"], "hash": d["hash"], "exotic": weapon["exotic"],
                "traitIndexes": sorted(traits), "references": []}
        for n, socket in enumerate(sockets.get("socketEntries", [])):
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                ph = socket.get(field)
                if not ph: continue
                pool = pools[str(ph)]
                require(pool["hash"] == ph and not pool["redacted"]
                        and not pool["blacklisted"], "official pool")
                matches = [v for v in pool.get("reusablePlugItems", [])
                           if v["plugItemHash"] in variants]
                scan["references"].append({"socket": n, "field": field, "plugSetHash": ph,
                                           "isFakePlugSet": pool["isFakePlugSet"], "matches": matches})
                for match in matches:
                    if eligible(n, traits, field, pool, match, weapon["exotic"]):
                        require(d["inventory"]["tierType"] == 5 and weapon["ammo"] == "SPECIAL",
                                "legendary Special only")
                        row = dict(zip(KEYS, (weapon["id"], d["hash"], n, BASE, ph)))
                        if row not in rows: rows.append(row)
                        proofs.append({**row, "socketEntry": socket, "socketCategoryHash": TRAIT,
                                       "matchingEntry": match, "pool": pool})
                    else:
                        excluded.append({"id": weapon["id"], "socket": n, "field": field,
                                         "plugSetHash": ph, "isFakePlugSet": pool["isFakePlugSet"],
                                         "matchingEntry": match})
        scans.append(scan)
    clarity = data["clarity"][str(BASE)]
    require(clarity == data["cachedClarity"][str(BASE)], "live/cache agreement")
    text = "\n".join("".join(l.get("text", "") for l in b.get("linesContent", []))
                     for b in clarity["descriptions"]["en"])
    require(clarity["hash"] == BASE and clarity["type"] == "Weapon Trait"
            and all(s in text for s in ("25% of your maximum", "even while the weapon is stowed",
                                       "Equipping two", "halves the amount")), "Clarity mechanics")
    parser = Rows(); parser.feed(data["ddc"])
    ddc = [r for r in parser.rows if "Lead from Gold" in r]
    require(len(ddc) == 1, "exact DDC row")
    ddc_text = " ".join(ddc[0])
    require(all(s in ddc_text for s in ("Heavy Ammo Brick Pickup", "25%", "12.5%",
                                      "Equipping two", "while stowed")), "DDC mechanics")
    resource = {"stage": "W187", "perk": PERK, "weapons": rows}
    validate(resource)
    outputs = {
        TARGET: resource,
        ART + "official-sockets.json": {"version": VERSION, "selectedCount": 65,
            "definitions": [inv[str(h)] for h in sorted(variants)], "rolls": rows,
            "proofs": proofs, "scans": scans, "excluded": excluded},
        ART + "clarity-source.json": {"clarityUrl": CLARITY_URL, "ddcUrl": DDC_URL,
            "clarityWholeFileSha256": PINS["clarity"], "ddcWholeFileSha256": PINS["ddc"],
            "baseEntry": clarity, "ddcRow": ddc[0], "authoredPolicy": PERK,
            "originalReserveBasisVerified": False, "originalIntegerRoundingVerified": False,
            "research": [
                {"url": "https://www.bungie.net/7/en/News/Article/51645",
                 "finding": "Official 2022 developer note confirms splitting pickups between two equipped Special weapons; no numeric integer algorithm."},
                {"url": "https://www.scribd.com/document/866079149/drfgdfgdgfdfgfdghyrtetryyrt",
                 "finding": "Unattributed mirror of an older test guide suggests total magazine+reserve and ceiling, explicitly estimated. Not accepted as current primary evidence."}]},
    }
    outputs[ART + "manifest.json"] = {
        "stage": "W187", "generator": SCRIPT,
        "generatorSha256": digest((args.root / SCRIPT).read_bytes()),
        "sourcePins": pins, "sourcePaths": LOCAL, "version": VERSION,
        "selectedCount": 65, "baseRollCount": len(rows), "matchingProofCount": len(proofs),
        "excludedMatchCount": len(excluded),
        "outputs": {k: digest(encode(v)) for k, v in outputs.items()},
        "limitations": ["Official socket snapshot is cached at pinned manifest version, not newly fetched Bungie inventory.",
                        "Reserve capacity and integer ceiling are authored port policy; original total reserve basis and rounding are not proven.",
                        "Master owns WeaponPerks registration, heavy pickup hook, aggregate broadcast, actualGT and native/runtime QA.",
                        "Worker offline JUnit/source-boundary checks are not runtime success."]}
    return outputs


def negative_checks(resource):
    count = 0
    for kind in ("missing", "duplicate", "enhanced", "socket", "pool", "hash", "id", "mechanics", "basis", "rounding", "field", "type"):
        bad = copy.deepcopy(resource)
        if kind == "missing": bad["weapons"].pop()
        elif kind == "duplicate": bad["weapons"].append(bad["weapons"][0])
        elif kind == "enhanced": bad["weapons"][0]["perkHash"] = ENHANCED
        elif kind in ("socket", "hash"): bad["weapons"][0][kind] += 1
        elif kind == "pool": bad["weapons"][0]["plugSetHash"] += 1
        elif kind == "id": bad["weapons"][0]["id"] = "fake"
        elif kind == "mechanics": bad["perk"]["reserveFraction"] = .35
        elif kind == "basis": bad["perk"]["reserveBasis"] = "current_ammo"
        elif kind == "rounding": bad["perk"]["originalRoundingVerified"] = True
        elif kind == "field": bad["weapons"][0]["extra"] = True
        elif kind == "type": bad["weapons"][0]["hash"] = str(bad["weapons"][0]["hash"])
        try: validate(bad)
        except ValueError: count += 1
        else: raise ValueError("negative accepted: " + kind)
    args = [3, {3, 4}, "randomizedPlugSetHash", {"isFakePlugSet": False},
            {"plugItemHash": BASE, "currentlyCanRoll": True}, False]
    require(eligible(*args), "positive predicate")
    for index, value in ((0, 2), (2, "reusablePlugSetHash"), (3, {"isFakePlugSet": True}),
                         (4, {"plugItemHash": ENHANCED, "currentlyCanRoll": True}),
                         (4, {"plugItemHash": BASE, "currentlyCanRoll": False}),
                         (4, {"plugItemHash": BASE}), (5, True)):
        bad = copy.deepcopy(args); bad[index] = value
        require(not eligible(*bad), "predicate negative")
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-root", type=Path)
    for name, default in {
        "inventory": "/tmp/destiny-weapons-w30/bungie-items.json",
        "plugsets": "/tmp/destiny-weapons-w60/bungie-plugsets.json",
        "manifest": "/tmp/destiny-weapons-w60/manifest.json",
        "clarity": "/private/tmp/w187-gold-report/clarity.json",
        "cachedClarity": "/private/tmp/w167-clarity.json",
        "ddc": "/private/tmp/w187-gold-report/ddc.html",
    }.items(): parser.add_argument("--" + name, type=Path, default=Path(default))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    outputs = generate(args)
    negatives = negative_checks(outputs[TARGET])
    destination = args.output_root or args.root
    for relative, value in outputs.items():
        path, raw = destination / relative, encode(value)
        if args.verify:
            require(path.read_bytes() == raw, "output differs: " + relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(json.dumps({"verified" if args.verify else "generated": len(outputs),
                      "catalogCount": 65, "baseRollCount": 6, "negativeChecks": negatives}))


if __name__ == "__main__":
    try: main()
    except (ValueError, KeyError, OSError, TypeError) as error:
        print("lead-from-gold: " + str(error), file=sys.stderr)
        sys.exit(1)
