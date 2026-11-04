#!/usr/bin/env python3
"""Reproduce W60 ALH membership offline; --verify performs no writes or network IO.

Raw sources default to /tmp/destiny-weapons-w60 and the pinned W30 inventory.
Generation writes ONLY the W60 resource and art/weapons/w60/references/*.json.
No dependencies beyond the Python standard library. Pins never auto-refresh.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = "art/weapons/w60/references/"
TARGET = "src/main/resources/destiny/weapons/w60-holster.json"
SCRIPT = "scripts/extract_holster_w60.py"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
BASE, ENHANCED = 3300816228, 3528046508
TRAIT_CATEGORY = 4241085061
BUNGIE = "https://www.bungie.net"
PATCH_URL = BUNGIE + "/7/en/News/article/destiny_update_8_1_0"
PINS = {
    "selected": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "w40Provenance": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "patch": "bce48fc2ba681344f67e608001d46895197679f7d89cbba6ee51d79b1b48ba1d",
    "preview": "42291604f5aa02398e2106765c835c8140f4978b65384875241c8169467ef20b",
    "baseMeasurement": "b09a8536e9a1ba4f73e5abaa4f9c395033e37be036f7114e301da7abb0c3241d",
    "enhancedMeasurement": "d8cfe851931713dff03ec11f8555cd65ce4f667b8e293e383447964767016e85",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def normalize(value):
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", value)).split())


def article(response, slug, title, date, heading, quote):
    require(response["count"] == 1 and len(response["entries"]) == 1,
            "Article selector is ambiguous: " + slug)
    entry = response["entries"][0]
    require(entry["url"]["hosted_url"] == "/" + slug and entry["title"] == title
            and entry["date"] == date and entry["locale"] == "en-us",
            "Official article identity/date mismatch: " + slug)
    text = normalize(entry["html_content"])
    require(text.count(heading) == 1, "Ambiguous perk heading: " + slug)
    window = text.split(heading, 1)[1][:120]
    require(quote in window, "Official change excerpt absent: " + slug)
    return {"url": BUNGIE + "/7/en/News/article/" + slug,
            "publisher": "Bungie", "primary": True, "title": title,
            "publishedAt": date, "deliveryUid": entry["uid"],
            "bodyField": "html_content", "heading": heading, "excerpt": quote}


def extract(args):
    root, cache = args.root, args.sources_dir
    paths = {
        "selected": root / "art/weapons/w40/definitions.json",
        "w40Provenance": root / "art/weapons/w40/provenance.json",
        "inventory": args.inventory,
        "plugSets": cache / "bungie-plugsets.json",
        "manifest": cache / "manifest.json",
        "patch": cache / "destiny_update_8_1_0-response.json",
        "preview": cache / "twid_10_03_2024-response.json",
        "baseMeasurement": cache / "lightgg-search-evidence.json",
        "enhancedMeasurement": cache / "lightgg-enhanced-search-evidence.json",
    }
    sources, source_pins = {}, {}
    # Fail before any writes on missing, truncated or changed source bytes.
    for key, path in paths.items():
        raw = path.read_bytes()
        require(digest(raw) == PINS[key], "Source SHA256 mismatch: " + key)
        sources[key] = json.loads(raw)
        source_pins[key] = {"path": str(path.relative_to(root)) if path.is_relative_to(root)
                            else str(path), "sha256": PINS[key], "bytes": len(raw)}

    manifest_response = sources["manifest"]
    require(manifest_response["ErrorCode"] == 1, "Manifest API response failed")
    manifest = manifest_response["Response"]
    require(manifest["version"] == VERSION, "Manifest version changed")
    component_paths = manifest["jsonWorldComponentContentPaths"]["en"]
    inventory_path = "/common/destiny2_content/json/en/DestinyInventoryItemDefinition-" + SUFFIX
    plugsets_path = "/common/destiny2_content/json/en/DestinyPlugSetDefinition-" + SUFFIX
    require(component_paths["DestinyInventoryItemDefinition"] == inventory_path
            and component_paths["DestinyPlugSetDefinition"] == plugsets_path,
            "Inventory and plug sets are not from the pinned matching manifest")
    w40 = sources["w40Provenance"]
    require(w40["manifest"] == {"version": VERSION, "path": inventory_path}
            and w40["cachedInventorySha256"] == PINS["inventory"]
            and w40["source"] == BUNGIE + inventory_path, "W40 provenance mismatch")

    selected, inventory, plugsets = sources["selected"], sources["inventory"], sources["plugSets"]
    require(len(selected) == 63 and len({w["id"] for w in selected}) == 63
            and len({w["bungieHash"] for w in selected}) == 63, "Expected 63 unique selected weapons")
    perk_excerpts = []
    for perk_hash, kind in [(BASE, "Trait"), (ENHANCED, "Enhanced Trait")]:
        perk = inventory[str(perk_hash)]
        require(perk["hash"] == perk_hash and perk["displayProperties"]["name"] == "Auto-Loading Holster"
                and perk["itemTypeDisplayName"] == kind and perk["itemType"] == 19
                and not perk["redacted"] and not perk["blacklisted"]
                and not perk["plug"]["isDummyPlug"], "Not the genuine ALH trait definition")
        perk_excerpts.append({"hash": perk_hash, "name": perk["displayProperties"]["name"],
                              "itemTypeDisplayName": kind, "itemType": perk["itemType"],
                              "description": perk["displayProperties"]["description"]})

    rows, evidence, static_options, enhanced_options = [], [], [], []
    for weapon in selected:
        item = inventory[str(weapon["bungieHash"])]
        require(item["hash"] == weapon["bungieHash"] and item["itemType"] == 3
                and not item["redacted"] and not item["blacklisted"], "Selected weapon definition invalid")
        sockets = item.get("sockets", {})
        trait_indexes = {i for cat in sockets.get("socketCategories", [])
                         if cat["socketCategoryHash"] == TRAIT_CATEGORY for i in cat["socketIndexes"]}
        for index, socket in enumerate(sockets.get("socketEntries", [])):
            direct = {p["plugItemHash"] for p in socket.get("reusablePlugItems", [])}
            direct.add(socket["singleInitialItemHash"])
            if BASE in direct:
                static_options.append({"id": weapon["id"], "socket": index,
                                       "perkHash": BASE, "includedByStaticEvidence": False})
            if ENHANCED in direct:
                enhanced_options.append({"id": weapon["id"], "socket": index, "source": "direct"})
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                set_hash = socket.get(field)
                if not set_hash:
                    continue
                pool = plugsets[str(set_hash)]  # Missing pool must fail, never silently omit.
                require(pool["hash"] == set_hash and not pool["redacted"] and not pool["blacklisted"],
                        "Invalid referenced plug set")
                entries = pool.get("reusablePlugItems", [])
                if any(p["plugItemHash"] == ENHANCED for p in entries):
                    enhanced_options.append({"id": weapon["id"], "socket": index, "source": field})
                matches = [p for p in entries if p["plugItemHash"] == BASE and p.get("currentlyCanRoll") is True]
                if field != "randomizedPlugSetHash" or not matches:
                    continue
                require(len(matches) == 1 and index in trait_indexes and not pool["isFakePlugSet"],
                        "ALH is not in a real weapon trait pool")
                require(weapon["exotic"] is False and item["itemTypeDisplayName"] != "Sword"
                        and isinstance(set_hash, int) and set_hash > 0,
                        "W60 runtime only supports nonexotic, nonsword weapons with a real plug-set hash")
                row = {"id": weapon["id"], "hash": item["hash"], "socket": index,
                       "perkHash": BASE, "plugSetHash": set_hash}
                rows.append(row)
                evidence.append({**row, "socketEntry": socket,
                                 "socketCategoryHash": TRAIT_CATEGORY, "plugSetField": field,
                                 "plugSetItem": matches[0], "isFakePlugSet": pool["isFakePlugSet"]})
    require(len(rows) == 18 and len({r["id"] for r in rows}) == 18,
            "Expected one proven randomized socket for each of 18 weapons")
    require(not enhanced_options, "Selected enhanced ALH scope changed; review timing before including")
    require({"id": "bad_omens", "hash": 991314988, "socket": 3,
             "perkHash": BASE, "plugSetHash": 457210958} in rows, "Bad Omens proof missing")

    quote = "Increased time to reload by one second for both base and enhanced."
    patch = article(sources["patch"], "destiny_update_8_1_0", "Destiny 2 Update 8.1.0",
                    "2024-10-08T17:00:00.000Z", "Auto Loading Holster", quote)
    preview = article(sources["preview"], "twid_10_03_2024", "This Week In Destiny - 10/03/2024",
                      "2024-10-03T18:00:00.000Z", "Auto-Loading Holster", quote.rstrip("."))
    base_text = "\n".join(c.get("text", "") for c in sources["baseMeasurement"]["content"])
    enhanced_text = "\n".join(c.get("text", "") for c in sources["enhancedMeasurement"]["content"])
    base_quote = "Refills stowed weapon from reserves after 3.5 seconds of it being stowed."
    require(base_quote in base_text and "https://www.light.gg/db/items/3300816228/auto-loading-holster/" in base_text,
            "Base duration secondary evidence missing")
    require("3.3 seconds of it being stowed" in enhanced_text
            and "https://www.light.gg/db/items/3528046508/auto-loading-holster/" in enhanced_text,
            "Enhanced duration secondary evidence missing")
    timing = {
        "stage": "W60", "primaryChange": patch, "primaryPreview": preview,
        "baseSeconds": 3.5, "ticksPerSecond": 20, "stowedTicks": 70,
        "baseMeasurement": {"url": "https://www.light.gg/db/items/3300816228/auto-loading-holster/",
                            "primary": False, "section": "Community Research", "excerpt": base_quote},
        "enhancedMeasurement": {"url": "https://www.light.gg/db/items/3528046508/auto-loading-holster/",
                                "primary": False, "excerpt": "3.3 seconds of it being stowed",
                                "seconds": 3.3, "implemented": False},
        "historicalBaseSeconds": 2.5,
        "historicalBaseDerivation": "3.5-second secondary measurement minus Bungie's one-second Revenant increase; not an absolute number quoted by Bungie.",
        "limitation": "Bungie proves the +1 second change, not the absolute durations. Manifest descriptions contain no numeric timing. Absolute values are secondary community measurements retrieved through web search; direct light.gg HTTP returned 403. No enhanced selected socket is supported.",
    }
    coverage = {r["id"] for r in rows}
    pools = {
        "stage": "W60", "selectedCount": 63, "supportedCount": len(rows),
        "policy": "Only base ALH in the selected item hash's own non-fake randomizedPlugSetHash, currentlyCanRoll=true, in its weapon-perks socket category. Zero-based manifest socket indexes. Pool weight is not used as availability evidence.",
        "perkDefinitions": perk_excerpts, "weapons": evidence,
        "staticSocketEvidenceNotUsedForSelection": static_options,
        "unsupportedSelectedIds": [w["id"] for w in selected if w["id"] not in coverage],
        "enhancedSelectedOptions": enhanced_options,
        "limitations": ["A supported pool permits an optional perk; it does not mean every copy rolled ALH.",
                        "Static reusablePlugItems do not expand this randomized-pool subset. Dust Rock Blues socket 3 is a separate static option; W60 selects randomized socket 4.",
                        "No exotic catalyst, armor holster mod, or same-name reprised weapon is inferred."],
    }
    provenance = {
        "stage": "W60", "manifestVersion": VERSION,
        "manifestEndpoint": BUNGIE + "/Platform/Destiny2/Manifest/",
        "manifestCapture": "Byte-for-byte copy of W57 manifest-current.json; matching version and both component URLs verified offline.",
        "inventoryUrl": BUNGIE + inventory_path, "plugSetsUrl": BUNGIE + plugsets_path,
        "sourceHashes": source_pins, "generator": SCRIPT,
        "generatorSha256": digest((root / SCRIPT).read_bytes()),
        "articleRetrieval": {"deliveryEndpoint": "https://cdn.contentstack.io/v3/content_types/news_article/entries",
                             "environment": "live", "locale": "en-us", "selector": "Exact url.hosted_url; limit=2; count=1",
                             "credentialsOrigin": "Official Bungie /Platform/Settings/ ContentStack parameters, reused privately from W57; never published."},
        "measurementRetrieval": "Pinned raw web-search tool responses; quotes checked offline, not hashes of direct light.gg HTTP bodies.",
        "reproduce": "rtk proxy python3 scripts/extract_holster_w60.py --verify",
        "privateSources": "Full inventory, plug sets, manifest and article/search responses remain outside the repository under /tmp. --verify requires every pinned source and never downloads or repairs files.",
    }
    resource = {"stage": "W60", "perk": {"id": "auto_loading_holster", "hash": BASE,
                "stowedTicks": 70, "timingSource": REF + "timing.json"}, "weapons": rows}
    return {TARGET: resource, REF + "timing.json": timing,
            REF + "socket-pools.json": pools, REF + "provenance.json": provenance}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Read-only byte-exact reproduction check; fail on missing/changed sources or outputs")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    parser.add_argument("--sources-dir", type=Path, default=Path("/tmp/destiny-weapons-w60"))
    args = parser.parse_args()
    try:
        outputs = extract(args)
        if args.verify:
            for name, value in outputs.items():
                require((args.root / name).read_bytes() == encoded(value), "Generated output differs: " + name)
        else:
            for name, value in outputs.items():
                path = args.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(encoded(value))
        print(("VERIFIED" if args.verify else "GENERATED") + ": W60, 63 selected, 18 base ALH randomized socket pools, 70 ticks; 0 enhanced pools.")
        print("Timing: Bungie 8.1.0 proves +1 second; 3.5 seconds is secondary community evidence.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("W60 verification failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
