#!/usr/bin/env python3
"""W103 source-backed, exact selected-hash Demolitionist profile.

No network, third-party dependencies, Java build, game launch, or code execution
from sources. --verify is read-only; all consumed bytes are SHA-pinned.
Only this new resource and art/weapons/w103/references JSON outputs are generated.
Tool development version: CPython 3.14.0; standard-library implementation supports
Python >=3.10. Fixed manifest version is intentional, not auto-refreshed.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/extract_demolitionist_w103.py"
TARGET = "src/main/resources/destiny/weapons/w103-demolitionist.json"
REF = "art/weapons/w103/references/"
BASE, ENHANCED, TRAIT_CATEGORY = 3523296417, 1906147653, 4241085061
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
BUNGIE = "https://www.bungie.net"
BASE_URL = "https://www.light.gg/db/items/3523296417/demolitionist/?_=707"
PATCH_URL = BUNGIE + "/7/en/News/Article/update-7-3-0-patch-notes"
STATS_URL = "https://origin-static01.bungie.net/7/en/News/Article/twid_06_05_2025"
CLARITY_URL = "https://www.d2clarity.com/blog/destiny-science-6/chunk-energy-scalars-breakdown-12"
PINS = {'selected': {'path': 'art/weapons/w40/definitions.json', 'sha256': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1'}, 'w40Provenance': {'path': 'art/weapons/w40/provenance.json', 'sha256': '281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42'}, 'catalog': {'path': 'src/main/resources/destiny/weapons/w30.json', 'sha256': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a'}, 'inventory': {'path': '/tmp/destiny-weapons-w30/bungie-items.json', 'sha256': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c'}, 'plugSets': {'path': '/tmp/destiny-weapons-w60/bungie-plugsets.json', 'sha256': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959'}, 'manifest': {'path': '/tmp/destiny-weapons-w60/manifest.json', 'sha256': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce'}, 'holsterExtractor': {'path': 'scripts/extract_holster_w60.py', 'sha256': '94f46644cbd3199dc06f168156598157e9bde06fb6a60c78abddcd12e8fbf5b6'}, 'outlawExtractor': {'path': 'scripts/extract_outlaw_w62.py', 'sha256': '06a900e736c96897199351de2e4194d59e6d20cbed03ba305abc24beac99dce7'}, 'clarity-contents.json': {'path': 'run/private-sources/w103/clarity-contents.json', 'sha256': 'f001d99c170a7867c2160cfab53585f3670e8f9a0f4f6cff032193f68fbfd814'}, 'clarity-readme.md': {'path': 'run/private-sources/w103/clarity-readme.md', 'sha256': 'f5b25df5fd1642d477d235a9ae40f820ce03fed67d1e93468c4a555850ad7cef'}, 'clarity-update.json': {'path': 'run/private-sources/w103/clarity-update.json', 'sha256': '001862d6b8fb43ef3a4e871ac18573e95df67bf7b030b2e0ab51b4decb590d76'}, 'research1.json': {'path': 'run/private-sources/w103/research1.json', 'sha256': '641b5cb2c2369df372e466d45107e07fa8e1097537f757b1a43984363ef3273d'}, 'research2.json': {'path': 'run/private-sources/w103/research2.json', 'sha256': '2869995b3d309ed216bda1f98c0d587194efe9db28389d7a099b70dfd4eec360'}, 'research3.json': {'path': 'run/private-sources/w103/research3.json', 'sha256': '3c0c1ef3b67b7ac3ea877cf8367699f516b18b13b900e3ee9e52444bed8c86f8'}, 'research4.json': {'path': 'run/private-sources/w103/research4.json', 'sha256': 'a8fbfcc7a37e631528665fef585cb4ee03e6785964389621b66492695a946069'}, 'research5.json': {'path': 'run/private-sources/w103/research5.json', 'sha256': '7c0bbc9ebfa603147ae573dc9f83e5cabe0f97e3e1dfc0b7e4248980a5aebe68'}, 'research6.json': {'path': 'run/private-sources/w103/research6.json', 'sha256': '1a7bf6fbfcd2c980dd75c2ded5aac71b1cbf55ce8d99613f5b03d987556dbddb'}}

EXPECTED = {
    "austringer": (3055790362, 4, 785215120),
    "gnawing_hunger": (821154603, 4, 594510568),
    "bug_out_bag": (2744715540, 4, 575371383),
    "lonesome": (2199171672, 4, 167712635),
    "high_albedo": (1197486957, 4, 718633408),
    "whispering_slab": (211938782, 4, 967526625),
    "first_in_last_out": (3616586446, 4, 1439234589),
    "stormchaser": (3652506829, 4, 4213354588),
    "retraced_path": (548958835, 4, 398391969),
    "salvager_s_salvo": (2060863616, 3, 253),
    "nezarec_s_whisper": (254636484, 3, 210449465),
}
EXCEPTION_FAMILIES = ["sniper_rifle", "shotgun", "glaive", "fusion_rifle"]
EXCEPTION_TYPES = {"Sniper Rifle", "Shotgun", "Glaive", "Fusion Rifle"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def text_blocks(response):
    return "\n".join(c.get("text", "") for c in response["content"]).split(
        "--------------------------------------------------------------------------------")


def assert_evidence(response, url, fragments):
    blocks = [b for b in text_blocks(response)
              if "(" + url + ")" in b and all(t in b for t in fragments)]
    require(len(blocks) == 1, "Missing or ambiguous URL-bound evidence: " + url)


def extract(args):
    root = args.root.resolve()
    raw, data, source_pins = {}, {}, {}
    for key, pin in PINS.items():
        path = Path(pin["path"])
        if not path.is_absolute():
            path = root / path
        content = path.read_bytes()
        require(digest(content) == pin["sha256"], "Source SHA256 mismatch: " + key)
        raw[key] = content
        if path.suffix == ".json":
            data[key] = json.loads(content)
        source_pins[key] = {**pin, "bytes": len(content)}
    selected, catalog = data["selected"], data["catalog"]
    require(len(selected) == len(catalog) == 63
            and len({w["id"] for w in selected}) == 63
            and len({w["bungieHash"] for w in selected}) == 63,
            "Expected 63 exact selected weapon hashes")
    catalog_by_id = {w["id"]: w for w in catalog}
    require(set(catalog_by_id) == {w["id"] for w in selected}, "Catalog selection drift")
    response = data["manifest"]
    require(response["ErrorCode"] == 1, "Official manifest API did not succeed")
    manifest = response["Response"]
    inventory_path = "/common/destiny2_content/json/en/DestinyInventoryItemDefinition-" + SUFFIX
    plugsets_path = inventory_path.replace("DestinyInventoryItemDefinition-", "DestinyPlugSetDefinition-")
    paths = manifest["jsonWorldComponentContentPaths"]["en"]
    require(manifest["version"] == VERSION
            and paths["DestinyInventoryItemDefinition"] == inventory_path
            and paths["DestinyPlugSetDefinition"] == plugsets_path,
            "Inventory/plugsets must be matching pinned official manifest components")
    provenance = data["w40Provenance"]
    require(provenance["manifest"] == {"version": VERSION, "path": inventory_path}
            and provenance["cachedInventorySha256"] == PINS["inventory"]["sha256"]
            and provenance["source"] == BUNGIE + inventory_path,
            "W40 official inventory provenance mismatch")
    inv, pools = data["inventory"], data["plugSets"]
    definitions = []
    same_name_nontraits = []
    for item in inv.values():
        if item.get("displayProperties", {}).get("name") != "Demolitionist":
            continue
        if item["hash"] not in (BASE, ENHANCED):
            same_name_nontraits.append({"hash": item["hash"], "itemType": item["itemType"],
                                       "itemTypeDisplayName": item["itemTypeDisplayName"]})
    for h, kind in ((BASE, "Trait"), (ENHANCED, "Enhanced Trait")):
        perk = inv[str(h)]
        require(perk["hash"] == h and perk["displayProperties"]["name"] == "Demolitionist"
                and perk["itemType"] == 19 and perk["itemTypeDisplayName"] == kind
                and not perk["redacted"] and not perk["blacklisted"]
                and not perk["plug"]["isDummyPlug"], "Invalid Demolitionist trait definition")
        definitions.append({"hash": h, "name": "Demolitionist", "itemTypeDisplayName": kind,
                            "description": perk["displayProperties"]["description"]})
    require({v["hash"] for v in same_name_nontraits} == {2291139173, 2222960133},
            "Same-name nontrait scope changed; inspect instead of guessing")

    rows, proofs, scanned, enhanced_options, direct_options = [], [], [], [], []
    for weapon in selected:
        item = inv[str(weapon["bungieHash"])]
        cat = catalog_by_id[weapon["id"]]
        require(item["hash"] == weapon["bungieHash"] and item["itemType"] == 3
                and not item["redacted"] and not item["blacklisted"]
                and {k: v["value"] for k, v in item["stats"]["stats"].items()} == weapon["stats"],
                "Selected official item/stat identity mismatch: " + weapon["id"])
        require(item["equippingBlock"]["ammoType"] == {"PRIMARY": 1, "SPECIAL": 2, "HEAVY": 3}[weapon["ammo"]],
                "Selected ammo metadata drift: " + weapon["id"])
        sockets = item.get("sockets", {})
        trait_indexes = {i for c in sockets.get("socketCategories", [])
                         if c["socketCategoryHash"] == TRAIT_CATEGORY for i in c["socketIndexes"]}
        scanned_weapon = {"id": weapon["id"], "hash": item["hash"], "family": cat["family"],
                          "frame": cat["frame"], "ammo": weapon["ammo"], "examinedPools": []}
        for index, socket in enumerate(sockets.get("socketEntries", [])):
            direct = {socket["singleInitialItemHash"],
                      *[p["plugItemHash"] for p in socket.get("reusablePlugItems", [])]}
            if BASE in direct:
                direct_options.append({"id": weapon["id"], "hash": item["hash"], "socket": index,
                                       "perkHash": BASE, "initialPerk": socket["singleInitialItemHash"] == BASE})
            if ENHANCED in direct:
                enhanced_options.append({"id": weapon["id"], "socket": index, "source": "direct"})
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                set_hash = socket.get(field)
                if not set_hash:
                    continue
                pool = pools[str(set_hash)]
                require(pool["hash"] == set_hash and not pool["redacted"] and not pool["blacklisted"],
                        "Missing/invalid selected referenced plug set")
                entries = pool.get("reusablePlugItems", [])
                matching = [{"index": i, "item": e} for i, e in enumerate(entries) if e["plugItemHash"] == BASE]
                if index in trait_indexes:
                    scanned_weapon["examinedPools"].append({"socket": index, "field": field,
                        "plugSetHash": set_hash, "isFakePlugSet": pool["isFakePlugSet"],
                        "baseMatches": matching})
                if any(e["plugItemHash"] == ENHANCED for e in entries):
                    enhanced_options.append({"id": weapon["id"], "socket": index,
                                             "source": field, "plugSetHash": set_hash})
                rollable = [m for m in matching if m["item"].get("currentlyCanRoll") is True]
                if not rollable:
                    continue
                # No family gate. Every selected weapon type is scanned before policy checks.
                require(index in trait_indexes and not weapon["exotic"]
                        and item["inventory"]["tierType"] == 5 and len(rollable) == 1,
                        "Not one real selected legendary base trait option")
                if field == "randomizedPlugSetHash":
                    require(not pool["isFakePlugSet"], "Fake pool cannot prove randomized availability")
                    selection = "randomized"
                else:
                    require(weapon["id"] == "salvager_s_salvo" and item["hash"] == 2060863616
                            and index == 3 and set_hash == 253 and pool["isFakePlugSet"]
                            and not socket.get("randomizedPlugSetHash")
                            and socket["singleInitialItemHash"] == 2010801679
                            and [(p["plugItemHash"], p.get("currentlyCanRoll")) for p in entries]
                            == [(2010801679, True), (BASE, True)]
                            and socket["plugSources"] == 6,
                            "Salvo curated two-choice reusable socket proof changed")
                    selection = "fixedCuratedOption"
                energy_percent = 20 if item["itemTypeDisplayName"] in EXCEPTION_TYPES else 10
                require((cat["family"] in EXCEPTION_FAMILIES) == (energy_percent == 20),
                        "Official weapon type and selected family exception mismatch")
                row = {"id": weapon["id"], "hash": item["hash"], "socket": index,
                       "perkHash": BASE, "plugSetHash": set_hash, "proofMode": selection,
                       "baseEnergyPercent": energy_percent}
                rows.append(row)
                proofs.append({**row, "family": cat["family"], "frame": cat["frame"],
                               "ammo": weapon["ammo"], "officialWeaponType": item["itemTypeDisplayName"],
                               "socketCategoryHash": TRAIT_CATEGORY, "socketEntry": socket,
                               "plugSetField": field, "isFakePlugSet": pool["isFakePlugSet"],
                               "matchingEntries": rollable})
        scanned.append(scanned_weapon)
    actual = {r["id"]: (r["hash"], r["socket"], r["plugSetHash"]) for r in rows}
    require(actual == EXPECTED and len(rows) == len(actual) == 11, "Exact 11 selected socket contracts changed")
    require(sum(r["proofMode"] == "randomized" for r in rows) == 10
            and sum(r["proofMode"] == "fixedCuratedOption" for r in rows) == 1,
            "Expected ten randomized pools and one curated option")
    require(not direct_options, "Direct base sockets changed; inspect before supporting")
    require(enhanced_options == [
        {"id": "austringer", "socket": 4, "source": "randomizedPlugSetHash", "plugSetHash": 785215120},
        {"id": "retraced_path", "socket": 4, "source": "randomizedPlugSetHash", "plugSetHash": 398391969},
        {"id": "nezarec_s_whisper", "socket": 3, "source": "randomizedPlugSetHash", "plugSetHash": 210449465}],
        "Enhanced options changed; never silently accept enhanced energy")

    assert_evidence(data["research1.json"], BASE_URL,
                    ["API ID: 3523296417", "Weapon Kills grant 10%", "Sniper Rifles, Shotguns, Glaives, and Fusion Rifles",
                     "grant 20%", "3 second cooldown", "Chunk Energy Scalar"])
    assert_evidence(data["research3.json"], PATCH_URL,
                    ["Neutral game abilities", "50% for grenades", "60% for melee"])
    assert_evidence(data["research2.json"], PATCH_URL, ["Nov 28, 2023", "Destiny 2 Update 7.3.0"])
    assert_evidence(data["research5.json"], STATS_URL,
                    ["Jun 5, 2025", "Any “chunk” energy gains", "scaled by your stat investment", "At 70 stat"])
    assert_evidence(data["research4.json"], CLARITY_URL,
                    ["partially outdated", "0.5x CES", "Vortex Grenade"])
    require(b"Currently SEVERELY Outdated" in raw["clarity-readme.md"]
            and b"Please do not use for ANYTHING" in raw["clarity-readme.md"]
            and data["clarity-update.json"]["schemaVersion"] == "1.9",
            "Clarity dataset status changed; re-review rather than assuming current scalar data")

    limitations = [
        "All fractions/percentages are BASE perk chunks, not exact current final received energy.",
        "Ability tier and Armor 3.0 grenade-stat scaling are not encoded; never infer scalars from authored Minecraft cooldowns.",
        "A local flat percent of the existing Minecraft cooldown is a staged adaptation, not measured live Destiny 2 energy.",
        "The 3-second reload-effect cooldown is supported, but owner-wide versus per-weapon/per-instance scope is not proven by these sources.",
        "The selected weapon must actually have the base trait selected; pool availability is not a default-equipped claim.",
        "Salvo proves a fixed curated selectable option, not its initial equipped perk and not a randomized pool.",
        "Manifest and secondary research snapshot may lag current live balance; no enhanced perk is supported.",
        "Glaive melee is not assumed to be a qualifying weapon final blow. Projectile kills are the verified intended integration scope; current melee-specific numeric behavior remains unverified.",
    ]
    mechanics = {
        "stage": "W103", "officialDescription": definitions[0],
        "baseEnergyPercent": 10, "exceptionEnergyPercent": 20,
        "exceptionOfficialWeaponTypes": sorted(EXCEPTION_TYPES),
        "exceptionFamilies": EXCEPTION_FAMILIES,
        "reloadCooldownSeconds": 3, "ticksPerSecond": 20, "reloadCooldownTicks": 60,
        "reloadFromReserves": True,
        "reloadSemantics": "On accepted grenade activation refill only available magazine space from existing reserves; no ammunition is created. Capacity/reserve arithmetic is the local conservation interpretation of the official description.",
        "reloadCooldownScope": {"proven": False, "scope": None,
            "policy": "Master must explicitly label any owner-wide or per-instance choice as a local policy, not source-proven."},
        "numericSource": {"url": BASE_URL, "publisher": "light.gg / Clarity Community Research",
            "primary": False, "updatedAt": "2024-12-17", "retrieval": "Pinned URL-bound search result, not successful direct HTTP body",
            "summary": "10 percent baseline per qualifying weapon kill; sniper, shotgun, glaive and fusion rifle exception 20 percent; grenade activation refills magazine and has a 3-second refill cooldown.",
            "specialAmmoPolicy": "Not all Special-ammo weapons get 20 percent. Selected trace Retraced Path and GL Salvager's Salvo use the general 10-percent baseline; selected shotgun/glaive use 20 percent."},
        "historicalAndCurrentQualifiers": [
            {"url": PATCH_URL, "publisher": "Bungie", "primary": True, "date": "2023-11-28",
             "summary": "Update 7.3.0 introduced passive-cooldown-tier scaling of percentage chunk energy; slowest grenades receive half the baseline. This is not a present-day complete ability/stat formula."},
            {"url": STATS_URL, "publisher": "Bungie", "primary": True, "date": "2025-06-05",
             "summary": "Armor 3.0 preview additionally ties chunk and recharge gains to stat investment; 70 stat matched then-live gains. No current curve is inferred from this historical preview."},
            {"url": CLARITY_URL, "publisher": "Clarity", "primary": False, "date": "2024-12-21",
             "summary": "Explains ability-specific penalties and Vortex as historical 0.5 scalar example, but now explicitly warns portions are outdated; not adopted as current per-Hunter numeric data."},
            {"url": "https://github.com/Database-Clarity/Character-Stats", "publisher": "Clarity", "primary": False,
             "summary": "Fetched README says severely outdated and instructs not to use; update.json schema 1.9. No scalar data was adopted."}],
        "unimplementedEnergyModifiers": {"abilityTierScalar": None, "grenadeStatScalar": None},
        "enhanced": {"hash": ENHANCED, "implemented": False},
        "limitations": limitations,
    }
    resource = {"stage": "W103", "perk": {
        "id": "demolitionist", "hash": BASE, "energyPercent": 10, "specialEnergyPercent": 20,
        "specialEnergyFamilies": EXCEPTION_FAMILIES, "reloadCooldownTicks": 60,
        "reloadFromReserves": True, "energyIsBaseChunk": True,
        "mechanicsSource": REF + "mechanics.json"}, "weapons": rows}
    source_provenance = {
        "stage": "W103", "manifestVersion": VERSION,
        "manifestEndpoint": BUNGIE + "/Platform/Destiny2/Manifest/",
        "inventoryUrl": BUNGIE + inventory_path, "plugSetsUrl": BUNGIE + plugsets_path,
        "cacheFormat": "Official matching JSON components, not SQLite; no cached SQLite was found in the inspected /tmp and run/private-sources caches.",
        "selectedCount": 63, "sourcePins": source_pins,
        "generator": SCRIPT, "generatorSha256": digest((root / SCRIPT).read_bytes()),
        "toolchain": {"developmentPython": "3.14.0", "minimumPython": "3.10", "dependencies": "standard library only",
                      "generatorVersion": 1, "byteOrder": "selected catalog order; UTF-8 JSON indent=2 newline"},
        "research": {"targetedSearchQueries": 8, "childToolsAvailable": False,
                     "childWorkClaimed": False, "sourcesAreUntrustedData": True,
                     "directLightggFetch": "Failed through web tool (402); numeric assertions use pinned URL-bound search excerpts.",
                     "bounds": "Eight query strings; subsequent opens/clicks fetched only specific discovered references, no broad searches."},
        "reproduce": "rtk proxy python3 scripts/extract_demolitionist_w103.py --verify",
        "reproduceElsewhere": "rtk proxy python3 scripts/extract_demolitionist_w103.py --output-root /tmp/w103-repro",
        "privateSources": "Cached official components remain at existing /tmp paths. Web captures and Clarity status responses are ignored under run/private-sources/w103. No network in extractor or verify.",
        "limitations": limitations,
    }
    scope = {"stage": "W103", "selectedCount": 63, "supportedCount": 11,
             "randomizedCount": 10, "fixedCuratedCount": 1,
             "policy": "Base trait only, exact selected hash and trait-category socket, currentlyCanRoll=true for randomized real pools; one explicitly validated fixed curated reusable pool for Salvo. No broad family exclusion or enhanced/name match.",
             "perkDefinitions": definitions, "sameNameNontraitsExcluded": same_name_nontraits,
             "weapons": proofs, "enhancedOptionsExcluded": enhanced_options,
             "unsupportedSelectedIds": [w["id"] for w in selected if w["id"] not in EXPECTED],
             "allSelectedPoolScans": scanned,
             "explicitCoverage": {"bow": "whispering_slab", "trace": "retraced_path",
                 "specialGL": "salvager_s_salvo", "glaive": "nezarec_s_whisper",
                 "wave": {"id": "deafening_whisper", "eligible": False,
                          "reason": "Exact selected item hash pools contain no base Demolitionist; no family gate."},
                 "swords": {"eligible": False,
                            "reason": "All five selected sword hashes scanned; no base Demolitionist in referenced pools."}},
             "limitations": limitations}
    return {TARGET: resource, REF + "mechanics.json": mechanics,
            REF + "socket-pools.json": scope, REF + "provenance.json": source_provenance}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Read-only byte-exact offline reproduction")
    parser.add_argument("--root", type=Path, default=ROOT, help="Root of pinned existing source inputs")
    parser.add_argument("--output-root", type=Path, default=None, help="Disjoint generation root; never changes source pins")
    args = parser.parse_args()
    try:
        require(not (args.verify and args.output_root), "--verify cannot write to --output-root")
        outputs = extract(args)
        for relative, value in outputs.items():
            content = encoded(value)
            path = (args.output_root or args.root) / relative
            if args.verify:
                require(path.read_bytes() == content, "Generated output differs: " + relative)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        print(json.dumps({"stage": "W103", "status": "VERIFY_PASS" if args.verify else "GENERATED",
                          "selected": 63, "supported": 11, "randomized": 10,
                          "fixedCurated": 1, "outputs": list(outputs)}, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("W103 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
