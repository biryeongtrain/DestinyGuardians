#!/usr/bin/env python3
"""Generate pinned W194 base No Distractions; --verify compares bytes without writes."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 2866798147
ENHANCED = 3974407819
VERSION = "245114.26.10.13.2000-1-bnet.66137"
PREFIX = "src/main/resources/destiny/weapons/"
ART = "art/weapons/w194/no-distractions/"
JAVA = "src/main/java/kim/biryeong/destiny/weapon/"
EXPECTED = [
    dict(id="biting_winds", hash=1621657423, socket=3, perkHash=BASE, plugSetHash=3968704963),
    dict(id="bite_of_the_fox", hash=1403800851, socket=3, perkHash=BASE, plugSetHash=563442205),
    dict(id="beloved", hash=3107853529, socket=3, perkHash=BASE, plugSetHash=1196545279),
    dict(id="apostate", hash=2164448701, socket=3, perkHash=BASE, plugSetHash=1306932196),
    dict(id="fixed_odds", hash=2194955522, socket=3, perkHash=BASE, plugSetHash=4227334000),
]
PINS = {
    "/tmp/destiny-weapons-w30/bungie-items.json": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "/tmp/destiny-weapons-w60/bungie-plugsets.json": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "/tmp/destiny-weapons-w60/manifest.json": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "/private/tmp/destiny-w190/ddc-perks.html": "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437",
    PREFIX + "w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    PREFIX + "w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    PREFIX + "w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    PREFIX + "w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "art/weapons/w85/references/clarity-pinned-raw.json": "881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384",
}
# Reviewed application-path snapshot: evidence, not a constraint on master's integration.
REVIEW = [JAVA + name for name in (
    "WeaponAiming.java", "WeaponFlinchState.java", "WeaponRuntime.java", "WeaponPerks.java",
    "WeaponItems.java", "WeaponModels.java", "WeaponLoadout.java")]


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
    require(perk["hash"] == BASE and perk["displayProperties"]["name"] == "No Distractions"
            and perk["itemTypeDisplayName"] == "Trait" and perk["itemType"] == 19
            and not perk["plug"]["isDummyPlug"] and not perk["redacted"] and not perk["blacklisted"],
            "exact base Trait definition")
    require(inv[str(ENHANCED)]["itemTypeDisplayName"] == "Enhanced Trait", "enhanced exclusion")
    rows = [row for row in re.findall(r"<tr\b[^>]*>.*?</tr>", data["/private/tmp/destiny-w190/ddc-perks.html"], re.S)
            if any(plain(cell) == "No Distractions" for cell in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S))]
    require(len(rows) == 1 and 'id="1662574278R151"' in rows[0], "exact DDC row152")
    row = rows[0]
    description_html = re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S)[-1]
    description = plain(description_html)
    yellow = re.findall(r'<span\b[^>]*style="[^"]*color:#ffd966;[^"]*"[^>]*>(.*?)</span>', description_html, re.S)
    base_description = plain(re.sub(r'<span\b[^>]*style="[^"]*color:#ffd966;[^"]*"[^>]*>.*?</span>', '', description_html, flags=re.S))
    require("After 1  seconds of ADS without firing:" in base_description
            and "35% Flinch Resist while ADS." in base_description
            and "Timer starts as soon as the ADS input is pressed." in base_description
            and "0.9" not in base_description and any("↑0.9" == plain(v) for v in yellow),
            "base windup/resistance separated from yellow enhanced text")
    clarity = data["art/weapons/w85/references/clarity-pinned-raw.json"][str(BASE)]
    clarity_text = " ".join(line["text"] for block in clarity["descriptions"]["en"]
                            for line in block.get("linesContent", []))
    require("Remains active until you're no longer ADS." in clarity_text, "earned-buff retention source")
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
    require(found == EXPECTED, "exhaustive all65 scan: exact five base/currentlyCanRoll/nonfake socket tuples")
    resource = dict(stage="W194", perk=dict(id="no_distractions", hash=BASE, adsSeconds=1,
                    procTicks=20, resistance=.35), weapons=found)
    resource_raw = encode(resource)
    reviewed = {name: dict(sha256=digest((root / name).read_bytes())) for name in REVIEW}
    authored = {name: dict(sha256=digest((root / (JAVA + name)).read_bytes()))
                for name in ("NoDistractionsProfile.java", "WeaponNoDistractions.java")}
    source = dict(stage="W194", checked="2026-10-27", officialManifest=VERSION,
        sourcePins=sources, generatorSha256=digest(Path(__file__).read_bytes()),
        resourceSha256=digest(resource_raw), helperSources=authored, catalogCount=65,
        selectionRules=dict(socketCategoryHash=4241085061, randomizedPlugSet=True, isFakePlugSet=False,
                            currentlyCanRoll=True, itemTypeDisplayName="Trait", exactPerkHash=BASE),
        perkDefinition=perk, socketProofs=proofs, catalogAudit=audit,
        excludedSameNameDefinitions=[dict(hash=int(k), itemTypeDisplayName=v.get("itemTypeDisplayName"),
                                          description=v["displayProperties"].get("description"))
            for k, v in sorted(inv.items(), key=lambda pair: int(pair[0]))
            if v.get("displayProperties", {}).get("name") == "No Distractions" and int(k) != BASE],
        ddc=dict(url="https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278",
                 tab="Weapon Perks", row=152, rawHTML=row, text=description, baseText=base_description,
                 enhancedYellowHTML=yellow, enhancedExcluded=ENHANCED, activity="No PvE/PvP split stated"),
        retentionEvidence=dict(path="art/weapons/w85/references/clarity-pinned-raw.json",
            pointer="/2866798147/descriptions/en", commit="039cfbc4732c33573568b28cc6335dd3332a9296",
            retrieval="Existing pinned snapshot re-read locally; no new live or gameplay measurement.",
            record=clarity, text=clarity_text),
        reviewedApplicationSources=reviewed,
        applicationPath=["WeaponPerks.available/ids/name -> NoDistractionsProfile (master integration)",
            "WeaponPerks.selected -> strict LongTag/IntTag and allowed exact roll",
            "WeaponNoDistractions.selected(p, stack) -> eligible exact original held inventory object",
            "WeaponAiming.updateNoDistractions: (exactIza || selected(owner, stack)) && aimingInput(session)",
            "existing Session.flinch.tick -> WeaponFlinchState.PROC_TICKS20; shot resets unearned windup only",
            "WeaponAiming.damaged -> WeaponFlinchState.magnitude(..., flinch.active()) once",
            "WeaponPerkHud -> existing WeaponAiming.noDistractions earned flag"],
        policies=dict(clock="Reuse the existing Aiming Session.flinch; never parallel state or another .65 multiplier.",
            ownership="Pure exact selected-hotbar stack object/count1/live canonical entry/current exact allowed base roll; loadout usable, alive/connected/nonspectator, no active Super.",
            ads="Clock starts on actual ADS input press, not completed scope transition; outer Aiming eligibility/aimingInput retains camera, handling and reload boundaries.",
            fire="Existing accepted paid-shot path ticks then calls flinch.shot; unearned windup resets; earned buff survives until ADS ends.",
            edit="Master WeaponAiming.perksEdited(ItemStack): reset only matching Session.stack flinch clocks after every real WeaponPerks.select/clear tag change. No reset on no-op select or pure reads. Catch same-tick edit-away/back.",
            intrinsic="Fixed Izanagi remains exactIza and is excluded from the five randomized selection rolls. OR eligibility; no duplicate resistance.",
            conversion="20 elapsed server ticks is the local 20TPS conversion of 1 second; .35 resistance leaves .65 remaining flinch.",
            uncertainty="Clarity explicitly retains the earned buff while ADS; pre-proc reset rather than pause is an interpretation of without firing. Dry fire/rejected triggers, exact D2 same-tick threshold ordering and independent reload/handling rules are unresolved. Existing local ordering retained.",
            validation="Pinned source/exact row/all65 proof review, deterministic --verify, isolated Java25 compile. No new per-value tests, fullgate or Vision; master owns scoped integration GameTests."))
    return {PREFIX + "w194-no-distractions.json": resource_raw, ART + "source.json": encode(source)}


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
    print("W194 No Distractions: catalog65; five exact base socket3 rolls; DDC row152; enhanced excluded")


if __name__ == "__main__":
    main()
