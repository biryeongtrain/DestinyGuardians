#!/usr/bin/env python3
"""Offline W66 exact-base Rampage socket proof and mechanics sidecar.

Every consumed source is SHA256 pinned. --verify compares ALL five generated
outputs without writing, creating directories, downloading or repairing inputs.
Raw web captures remain private; only bounded public proof is emitted.
Use --output-root for a separate reproduction tree, as in the W62 extractor.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/extract_rampage_w66.py"
REF = "art/weapons/w66/references/"
NOTES = "art/weapons/w66/reference-notes.md"
TARGET = "src/main/resources/destiny/weapons/w66-rampage.json"
BASE, ENHANCED, HUCKLEBERRY = 3425386926, 288411554, 3551326236
TRAIT_CATEGORY = 4241085061
VERSION = "245114.26.10.13.2000-1-bnet.66137"
SUFFIX = "e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
BUNGIE = "https://www.bungie.net"
PATCH_URL = BUNGIE + "/7/en/News/Article/destiny_update_9_5_0"
PATCH_MIRROR = "https://origin-static01.bungie.net/7/en/News/Article/destiny_update_9_5_0"
LIGHTGG_URL = "https://www.light.gg/db/items/3425386926/rampage/?_=688"
ARSENAL_URL = "https://d2-arsenal.vercel.app/weapon/3132669561"
# Ten words from this public article; other findings are paraphrased below.
PATCH_QUOTE = "Now loses only one stack after the timer expires."
PINS = {
    "selected": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "w40Provenance": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugSets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "research1.json": "0c625014aaf5b3066622274e289c07115e612ab429a2ba217fad3853e9ff30fa",
    "research2.json": "a2e2c1964d0436ec6b7c9cb405c38ae39adfff9540390c1967fc76fda762266e",
    "research3.json": "0de7595629a87a4c4071f9c5f27f265e2231c240464f259f33a2d005f6e55c2e",
    "research4.json": "2524c9732272fcebbb1e35c2bc4384f83dbd15091d44292e65302d7ea8b11347",
}
# Regression oracle only: enumeration below scans all 63 selected weapons first.
# These tuples never filter weapons or infer eligibility from a weapon name.
EXPECTED_RANDOM = {
    ("duke_mk_44", 2112909414, 4, 3815727680),
    ("austringer", 3055790362, 4, 785215120),
    ("gnawing_hunger", 821154603, 4, 594510568),
    ("bygones", 2712244741, 3, 1760176771),
    ("chattering_bone", 568515759, 4, 423791138),
    ("blast_furnace", 3843477312, 4, 169306153),
    ("claws_of_the_wolf", 1280933460, 4, 753756428),
    ("dead_man_walking_xx7463", 3751622019, 4, 1210839935),
    ("brass_attacks", 2121785039, 4, 3403850295),
    ("beloved", 3107853529, 4, 887157889),
    ("dust_rock_blues", 636912560, 4, 1624251370),
    ("parcel_of_stardust_fell_to_earth", 2217366863, 4, 3424940310),
    ("dream_breaker", 2931957300, 4, 1206254527),
    ("line_in_the_sand", 946443267, 4, 3257645194),
    ("stormchaser", 3652506829, 4, 4213354588),
    ("deafening_whisper", 981718087, 4, 3588287812),
    ("edge_transit", 218335759, 4, 2535579724),
    ("canis_major", 2066434718, 4, 2791121719),
    ("fixed_odds", 2194955522, 4, 1686775256),
    ("hammerhead", 603242241, 4, 2479293397),
    ("retrofit_escapade", 3103325054, 4, 2461260598),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    if isinstance(value, str):
        return value.encode("utf-8")
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def evidence_block(capture, url, phrases):
    """Never mix claims from different URLs, perks or adjacent search results."""
    require(not capture.get("isError"), "Failed web capture: " + url)
    text = "\n".join(c.get("text", "") for c in capture["content"])
    matches = [b for b in text.split("--------------------------------------------------------------------------------")
               if "(" + url + ")" in b and all(p in b for p in phrases)]
    require(len(matches) == 1, "Missing or ambiguous URL-bound evidence: " + url)
    return matches[0]


def extract(args):
    root = args.root.resolve()
    paths = {
        "selected": root / "art/weapons/w40/definitions.json",
        "w40Provenance": root / "art/weapons/w40/provenance.json",
        "inventory": args.inventory,
        "plugSets": args.shared_sources_dir / "bungie-plugsets.json",
        "manifest": args.shared_sources_dir / "manifest.json",
        **{name: args.sources_dir / name for name in PINS if name.startswith("research")},
    }
    require(paths.keys() == PINS.keys(), "Every consumed source needs an explicit SHA256 pin")
    sources, pins = {}, {}
    for key, path in paths.items():
        raw = path.read_bytes()
        require(digest(raw) == PINS[key], "Source SHA256 mismatch: " + key)
        sources[key] = json.loads(raw)
        path = path.resolve()
        pins[key] = {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                     "sha256": PINS[key], "bytes": len(raw)}

    response = sources["manifest"]
    require(response["ErrorCode"] == 1, "Manifest API response failed")
    manifest = response["Response"]
    inventory_path = "/common/destiny2_content/json/en/DestinyInventoryItemDefinition-" + SUFFIX
    plugsets_path = inventory_path.replace("DestinyInventoryItemDefinition-", "DestinyPlugSetDefinition-")
    components = manifest["jsonWorldComponentContentPaths"]["en"]
    require(manifest["version"] == VERSION
            and components["DestinyInventoryItemDefinition"] == inventory_path
            and components["DestinyPlugSetDefinition"] == plugsets_path,
            "Inventory and plug sets must match the exact pinned manifest")
    w40 = sources["w40Provenance"]
    require(w40["manifest"] == {"version": VERSION, "path": inventory_path}
            and w40["cachedInventorySha256"] == PINS["inventory"]
            and w40["source"] == BUNGIE + inventory_path, "W40 provenance mismatch")
    selected, inventory, plugsets = sources["selected"], sources["inventory"], sources["plugSets"]
    require(len(selected) == len({w["id"] for w in selected})
            == len({w["bungieHash"] for w in selected}) == 63, "Expected 63 unique selected weapons")
    definitions = []
    for h, kind, disposition in [(BASE, "Trait", "supported exact base only"),
                                  (ENHANCED, "Enhanced Trait", "excluded enhanced"),
                                  (HUCKLEBERRY, "Trait", "excluded Huckleberry-specific hash")]:
        perk = inventory[str(h)]
        require(perk["hash"] == h and perk["displayProperties"]["name"] == "Rampage"
                and perk["itemTypeDisplayName"] == kind and perk["itemType"] == 19
                and not perk["redacted"] and not perk["blacklisted"]
                and not perk["plug"]["isDummyPlug"], "Invalid Rampage definition: " + str(h))
        definitions.append({"hash": h, "name": "Rampage", "itemTypeDisplayName": kind,
                            "itemType": 19, "disposition": disposition})

    rows, proofs, direct_options, excluded, other_base, audit = [], [], [], [], [], []
    for weapon in selected:
        item = inventory[str(weapon["bungieHash"])]
        require(item["hash"] == weapon["bungieHash"] and item["itemType"] == 3
                and not item["redacted"] and not item["blacklisted"]
                and (item["inventory"]["tierType"] == 6) == weapon["exotic"],
                "Invalid selected official weapon: " + weapon["id"])
        sockets = item.get("sockets", {})
        trait_indexes = {n for c in sockets.get("socketCategories", [])
                         if c["socketCategoryHash"] == TRAIT_CATEGORY for n in c["socketIndexes"]}
        before = len(rows)
        for index, socket in enumerate(sockets.get("socketEntries", [])):
            identity = {"id": weapon["id"], "hash": item["hash"], "socket": index}
            direct = {socket["singleInitialItemHash"],
                      *[p["plugItemHash"] for p in socket.get("reusablePlugItems", [])]}
            for h in (BASE, ENHANCED, HUCKLEBERRY):
                if h in direct:
                    option = {**identity, "perkHash": h, "source": "direct",
                              "initialPerk": socket["singleInitialItemHash"] == h,
                              "reusablePlugItems": [p for p in socket.get("reusablePlugItems", [])
                                                    if p["plugItemHash"] == h],
                              "socketCategoryHash": TRAIT_CATEGORY if index in trait_indexes else None}
                    (direct_options if h == BASE else excluded).append(option)
            for field in ("randomizedPlugSetHash", "reusablePlugSetHash"):
                set_hash = socket.get(field)
                if not set_hash:
                    continue
                pool = plugsets[str(set_hash)]
                require(pool["hash"] == set_hash and not pool["redacted"] and not pool["blacklisted"],
                        "Missing or invalid referenced plug set: " + str(set_hash))
                for h in (BASE, ENHANCED, HUCKLEBERRY):
                    matches = [{"index": n, "item": p} for n, p in enumerate(pool.get("reusablePlugItems", []))
                               if p["plugItemHash"] == h]
                    if not matches:
                        continue
                    option = {**identity, "perkHash": h, "plugSetHash": set_hash,
                              "plugSetField": field, "isFakePlugSet": pool["isFakePlugSet"],
                              "socketCategoryHash": TRAIT_CATEGORY if index in trait_indexes else None,
                              "matchingEntries": matches}
                    if h != BASE:
                        excluded.append(option)
                        continue
                    eligible = [p for p in matches if p["item"].get("currentlyCanRoll") is True]
                    if field != "randomizedPlugSetHash" or not eligible:
                        other_base.append(option)
                        continue
                    require(index in trait_indexes and pool["isFakePlugSet"] is False
                            and weapon["exotic"] is False and item["inventory"]["tierType"] != 6
                            and item["itemTypeDisplayName"] not in ("Sword", "Glaive"),
                            "Not a real randomized nonexotic firearm trait pool")
                    require(len(matches) == len(eligible) == 1,
                            "Duplicate/unrollable base entries changed; do not silently deduplicate")
                    row = {**identity, "perkHash": BASE, "plugSetHash": set_hash}
                    rows.append(row)
                    proofs.append({**row, "selection": "randomized", "socketCategoryHash": TRAIT_CATEGORY,
                                   "weaponType": item["itemTypeDisplayName"], "socketEntry": socket,
                                   "plugSetField": field, "isFakePlugSet": False, "matchingEntries": eligible})
        audit.append({"id": weapon["id"], "hash": item["hash"], "weaponType": item["itemTypeDisplayName"],
                      "exotic": weapon["exotic"], "socketCount": len(sockets.get("socketEntries", [])),
                      "traitSocketIndexes": sorted(trait_indexes), "randomizedBaseRows": len(rows) - before})

    keys = {(r["id"], r["hash"], r["socket"], r["plugSetHash"]) for r in rows}
    require(keys == EXPECTED_RANDOM and len(rows) == len({r["id"] for r in rows}) == 21,
            "Independently enumerated exact-base randomized rows differ from the 21-row oracle")
    row_sockets = {(r["id"], r["hash"], r["socket"]) for r in rows}
    require(len(direct_options) == 8 and all((r["id"], r["hash"], r["socket"]) in row_sockets
                                           for r in direct_options), "Direct options no longer overlap proven rows")
    for option in direct_options:
        option["alsoProvenRandomized"] = True
        option["addsRuntimeRow"] = False
    require(not other_base, "Unselected base pool evidence changed; audit explicitly")
    require(len(excluded) == 4 and all(e["perkHash"] == ENHANCED
            and e.get("plugSetField") == "randomizedPlugSetHash" for e in excluded)
            and {e["id"] for e in excluded} == {"austringer", "beloved", "fixed_odds", "retrofit_escapade"},
            "Enhanced/Huckleberry selected occurrences changed")

    # Exact URL and perk section binding avoids adjacent Outlaw/Killing Tally stow text.
    base_text = evidence_block(sources["research1.json"], LIGHTGG_URL,
                              ["API ID: 3425386926", "Community Research", "4.5 seconds",
                               "10%|21%|33.1%", "one at a time", "2025-12-27"])
    require("Maximum of 3" in base_text, "Exact-base maximum stack evidence absent")
    evidence_block(sources["research2.json"], PATCH_MIRROR, ["Destiny 2 Update 9.5.0", "Rampage", PATCH_QUOTE])
    evidence_block(sources["research3.json"], PATCH_URL,
                   ["Destiny 2 Update 9.5.0", "Dec 2, 2025", "Source: open("])
    arsenal = evidence_block(sources["research4.json"], ARSENAL_URL, ["#### Rampage", "4.5"])
    section = arsenal.split("#### Rampage", 1)[1].split("Image:", 1)[0]
    for phrase in ("10% | 21% | 33.1%", "Additional Weapon Kills", "refresh", "buff duration",
                   "one at a time", "Buff persists through stow."):
        require(phrase in section, "Missing Rampage-specific secondary evidence: " + phrase)
    require(re.search(r"4[.]5\s+↑5 seconds", section) is not None,
            "Arsenal base/enhanced duration boundary changed")

    mechanics = {
        "stage": "W66", "baseHash": BASE, "enhancedHashExcluded": ENHANCED,
        "huckleberryHashExcluded": HUCKLEBERRY, "maxStacks": 3,
        "baseDurationSeconds": 4.5, "decayTicks": 90, "ticksPerSecond": 20,
        "multipliers": [1.0, 1.1, 1.21, 1.331],
        "trigger": {"event": "weapon final blow", "precisionRequired": False, "reloadRequired": False,
                    "source": "Official base trait description establishes weapon kills and three stacks; numeric values are secondary."},
        "primaryChange": {
            "url": PATCH_URL, "publisher": "Bungie", "primary": True,
            "title": "Destiny 2 Update 9.5.0", "publishedAt": "2025-12-02",
            "sectionHeading": "Rampage", "excerpt": PATCH_QUOTE,
            "supports": "Each timer expiration removes one stack instead of clearing the entire buff.",
            "doesNotEstablish": ["Absolute duration", "Damage percentages", "Stow behavior", "Kill refresh behavior"],
            "privateEvidence": {"changeCapture": "research2.json", "changeUrl": PATCH_MIRROR,
                                "absoluteDateCapture": "research3.json", "dateUrl": PATCH_URL},
            "captureBoundary": "research3 reports 888 article lines but stores only lines 0-285; its stored body proves the date, not the later Rampage section. research2 carries the official mirror's Rampage change.",
        },
        "communityMeasurements": {
            "url": LIGHTGG_URL, "publisher": "light.gg", "primary": False,
            "exactPerkHash": BASE, "section": "Community Research", "privateCapture": "research1.json",
            "lastUpdatedReported": "2025-12-27", "maxStacks": 3,
            "durationSeconds": 4.5, "damageIncreasePercentByStack": [10, 21, 33.1],
            "decay": "One stack expires per duration interval.",
            "damageBoundary": "The damage from separate explosive/splash perks is outside this bonus.",
            "stowMentioned": False, "refreshMentionedExplicitly": False,
            "retrieval": "Pinned URL-bound search body; direct light.gg open in research3 returned HTTP 402. This is community documentation, not fresh gameplay testing.",
        },
        "stowAndRefreshSecondary": {
            "url": ARSENAL_URL, "publisher": "D2 Arsenal", "primary": False,
            "privateCapture": "research4.json", "sectionHeading": "Rampage",
            "confidence": "Single explicit secondary source for stow and refresh; no primary corroboration for either behavior.",
            "stowPersists": True, "additionalWeaponKillsRefresh": True,
            "durationSeconds": 4.5, "decaysOneStackAtATime": True,
            "enhancedDurationSecondsExcluded": 5,
            "identityBoundary": "A perk description on a different weapon page corroborates behavior only; this page does not prove selected-weapon eligibility or independently bind the description to the base hash.",
            "retrieval": "Pinned search result, restricted to the Rampage section before the next perk. Adjacent Killing Tally/Outlaw text and generic forum posts are not Rampage or official evidence.",
        },
        "sourceAudit": {
            "eligibility": "Official pinned manifest, item hash, real trait category, non-fake randomized set and currentlyCanRoll=true.",
            "oneStackDecay": "Official Bungie change plus exact-base light.gg and D2 Arsenal.",
            "durationAndMultipliers": "Exact-base light.gg; secondary D2 Arsenal agrees on base values.",
            "stow": "Single explicit D2 Arsenal secondary statement; exact-base light.gg omits stow and Bungie only proves decay. Do not infer cancellation from nearby other perks.",
            "refresh": "Single explicit D2 Arsenal secondary statement. Exact-base light.gg and the Bungie patch do not establish the precise refresh deadline.",
            "unresolved": ["Independent live validation of stow/refresh", "Precise tick endpoints and delayed-tick ordering",
                           "Destiny ownership/copy identity and in-flight projectile attribution"],
        },
        "projectIntegrationPolicy": {
            "verifiedDestinyBehavior": False,
            "session": "Maintain a timed session per owned ItemStack object; keep and advance decay while it is stowed.",
            "kill": "Credit a confirmed weapon final blow to its original stack only while the owner still possesses it and its exact Rampage socket is still selected, even if another weapon is now held.",
            "refresh": "After bringing due decay current, a qualifying kill adds one stack up to three and resets the next decay deadline to now+90, including at the cap.",
            "decay": "Each elapsed 90-tick interval removes one stack; process every elapsed interval and preserve the remaining interval when catching up. Never clear all stacks on the first expiry.",
            "stow": "Retain the session and its deadline through switching; stowing grants no extra time.",
            "projectile": "Capture the emitted shot's multiplier; later stack changes or a kill's newly granted stack do not retroactively alter that shot.",
            "identity": "Copies and new owners start without this object's session; no session inheritance. Possession/selection loss invalidates kill credit and the session.",
            "boundary": "These are the agreed W66 runtime integration rules. The sources do not prove object identity, ownership transfer, emitted-shot snapshots or transaction ordering.",
        },
        "limitations": [
            "No live Destiny test or exhaustive later-patch audit; pinned evidence is not a current sandbox certification.",
            "Pool eligibility grants an optional roll, not automatic trait selection on every weapon copy.",
            "No enhanced, Huckleberry, catalyst, same-name reissue, sword or glaive eligibility inferred.",
            "Base damage and separate explosive-damage perks require their own integration decisions; this resource only supplies Rampage's scalar.",
        ],
    }
    coverage = {r["id"] for r in rows}
    pools = {
        "stage": "W66", "selectedCount": 63, "supportedCount": 21,
        "poolRows": 21, "randomizedPoolRows": 21, "fixedDirectRows": 0,
        "perkDefinitions": definitions, "provenBaseHashes": [BASE],
        "policy": "Scan every selected item and every socket. Emit exact base hash only from its own randomizedPlugSetHash with currentlyCanRoll=true, isFakePlugSet=false and weapon-perks socket category 4241085061. Zero-based indexes. Weight zero does not negate currentlyCanRoll. Direct/curated defaults never add another allowlist row.",
        "weapons": proofs, "directSocketOptions": direct_options,
        "otherBasePoolOccurrencesNotSelected": other_base,
        "enhancedSelectedOptionsExcluded": [e for e in excluded if e["perkHash"] == ENHANCED],
        "huckleberrySelectedOptionsExcluded": [e for e in excluded if e["perkHash"] == HUCKLEBERRY],
        "selectionAudit": audit,
        "unsupportedSelectedIds": [w["id"] for w in selected if w["id"] not in coverage],
    }
    resource = {"stage": "W66", "perk": {"id": "rampage", "hash": BASE, "decayTicks": 90,
                "multipliers": [1.0, 1.1, 1.21, 1.331], "timingSource": REF + "mechanics.json"},
                "weapons": rows}
    # A bounded live corroboration made during authoring, not an offline generator input.
    # No HTTP body or credentials were written: the task permits only these six files.
    direct_corroboration = {
        "retrievedAtDate": "2026-10-24", "status": 200,
        "deliveryEndpoint": "https://cdn.contentstack.io/v3/content_types/news_article/entries",
        "selector": {"environment": "live", "locale": "en-us", "url.hosted_url": "/destiny_update_9_5_0",
                     "limit": 2, "include_count": True, "matchedEntries": 1},
        "deliveryUid": "bltbbe8d25b9e84adce", "bodyField": "html_content",
        "title": "Destiny 2 Update 9.5.0", "publishedAt": "2025-12-02T15:00:00.000Z",
        "responseBytes": 45303,
        "responseSha256": "ce1a531942faac0cc9550ffb16bf0a7f40bc0645782d4a9795e8aa81142e2bc5",
        "confirmed": "Exact article identity, absolute date and the Rampage change quoted in mechanics.json.",
        "credentialsOrigin": "Official Bungie /Platform/Settings/ ContentStack parameters; never emitted.",
        "offlineBoundary": "Supplemental authoring observation only. The response was read in memory and not retained on disk; --verify does not revalidate this response hash. Reproducible evidence instead comes from SHA-pinned research2/research3. No network is used by this extractor.",
    }
    notes = """# W66 Rampage source and data sidecar

The pinned selection independently yields **21 real randomized base-Rampage rows** from 63 exact weapon hashes. The runtime resource contains only `stage`, `perk` and `WeaponPerks.Roll`-shaped `weapons`. Its values are 90 ticks per decay interval and multipliers 1.0 / 1.1 / 1.21 / 1.331.

## Eligibility

`references/socket-pools.json` preserves each item's exact hash, zero-based socket, socket entry, trait category 4241085061, randomized plug-set hash, `isFakePlugSet=false`, original matching-entry index and full `currentlyCanRoll=true` record. Enumeration scans all selected sockets before checking the independent 21-tuple regression oracle. Zero weights are retained and are not a rejection criterion.

Eight direct/initial defaults overlap those randomized rows and add no runtime rows: Gnawing Hunger, Dust Rock Blues, Parcel of Stardust, Dream Breaker, Line in the Sand, Stormchaser, Deafening Whisper and Hammerhead. These are defaults/curated evidence, not a second allowlist. Enhanced 288411554 occurs in Austringer, Beloved, Fixed Odds and Retrofit Escapade pools and is excluded. Huckleberry-specific 3551326236 has zero selected occurrences and is excluded. No sword or glaive is supported; names and same-name reissues do not prove eligibility.

## Evidence layers

1. **Official inventory and plug sets** prove the exact eligible roll and weapon-kill trigger with a three-stack limit. They do not supply numeric damage, duration, stow or refresh behavior.
2. **Bungie Update 9.5.0, December 2, 2025** establishes gradual one-stack expiration. The bounded quote and URLs are in `references/mechanics.json`. This date comes from the absolute article date, not a relative search-engine timestamp. `research2.json` contains the official mirror's change; `research3.json` contains the canonical article date but its saved body stops at line 285 of a reported 888, before the Rampage section. A direct ContentStack body fetch independently confirmed the change and absolute timestamp; its bounded metadata is in provenance. That in-memory response was not retained and is not independently rechecked offline.
3. **Exact-base light.gg Community Research** (hash 3425386926, reported update December 27, 2025) supplies 4.5 seconds, 10/21/33.1 percent increases and one-at-a-time expiration. It omits explicit stow and refresh statements. These are secondary measurements captured by search, not fresh gameplay tests; direct open returned HTTP 402.
4. **D2 Arsenal's Rampage section** on weapon 3132669561 explicitly supports keeping the buff through stowing and renewing its duration after additional weapon kills. It also agrees with the base duration and gradual decay. This is a single explicit secondary source for stow and refresh, on another weapon's page; it proves no selected weapon's pool. Its enhanced five-second annotation is excluded. Adjacent Killing Tally/Outlaw text and generic forum posts supply no official Rampage evidence.

Sources: [Bungie 9.5.0](https://www.bungie.net/7/en/News/Article/destiny_update_9_5_0), [official mirror](https://origin-static01.bungie.net/7/en/News/Article/destiny_update_9_5_0), [exact-base light.gg](https://www.light.gg/db/items/3425386926/rampage/?_=688), [D2 Arsenal](https://d2-arsenal.vercel.app/weapon/3132669561). Full captures remain private in `/tmp/destiny-weapons-w66/research1.json` through `research4.json`. Public output is compact evidence and paraphrase, not full articles or search dumps; the Bungie quotation is ten words.

## Runtime integration boundary

The agreed W66 policy retains timed sessions per owned ItemStack through stow, advances each elapsed decay interval, and resets the next deadline after a qualifying kill even at the three-stack cap. A delayed projectile final blow credits its original stack only if still possessed by the original owner with Rampage selected; it need not be the currently held gun. A projectile retains the multiplier captured at emission. Copies and new owners inherit no session. These object/ownership rules, exact tick endpoints, refresh ordering and shot snapshots are authored integration decisions, not proven Destiny internals. Independent live confirmation of stow and refresh remains unresolved. This sidecar does not implement or test the concurrent runtime.

## Reproduction

Run from the shared repository, without Gradle:

```sh
rtk proxy python3 scripts/extract_rampage_w66.py --verify
rtk proxy python3 scripts/extract_rampage_w66.py --output-root /tmp/destiny-weapons-w66/reproduced
rtk proxy python3 scripts/extract_rampage_w66.py --output-root /tmp/destiny-weapons-w66/reproduced --verify
```

The script's `--root` selects the read-only input checkout; `--inventory`, `--shared-sources-dir` and `--sources-dir` locate the pinned source caches. Defaults are `/tmp/destiny-weapons-w30/bungie-items.json`, `/tmp/destiny-weapons-w60/{manifest,bungie-plugsets}.json` and `/tmp/destiny-weapons-w66/research{1,2,3,4}.json`. W40 definitions and provenance are read from the input checkout. Source locations are recorded in provenance; changing those locations changes that metadata. `--output-root` alone does not change bytes.

Every consumed local source has a hard-coded SHA256 pin. Missing or changed inputs fail before any output write. `--verify` checks every byte of the resource, all three reference JSON files and this Markdown file, and never creates directories, writes, fetches or repairs sources. The generator's own SHA256 and all non-provenance output hashes are included in provenance. Source caches must already exist; raw captures are intentionally not bundled. No Gradle, native app, assets, runtime code or git commit is part of this sidecar.
"""
    outputs = {TARGET: resource, REF + "socket-pools.json": pools,
               REF + "mechanics.json": mechanics, NOTES: notes}
    provenance = {
        "stage": "W66", "manifestVersion": VERSION,
        "inventoryUrl": BUNGIE + inventory_path, "plugSetsUrl": BUNGIE + plugsets_path,
        "sourceHashes": pins, "generator": SCRIPT, "generatorSha256": digest((root / SCRIPT).read_bytes()),
        "runtimeSha256": digest(encoded(resource)),
        "outputHashes": {name: digest(encoded(value)) for name, value in outputs.items()},
        "retrievedAtDate": "2026-10-24", "officialBodyDirectCorroboration": direct_corroboration,
        "sourceBoundary": "Official data proves roll eligibility. Bungie proves one-stack decay. Exact-base light.gg supplies numeric community measurements. D2 Arsenal alone explicitly supports stow persistence and kill refresh; runtime identity and shot snapshots are authored policy.",
        "privateSources": "Full inventory, plug sets, manifest and four raw web captures remain outside the repository. Public proof contains no full article/search dumps, forum posts presented as official, or credentials.",
        "reproduce": "rtk proxy python3 scripts/extract_rampage_w66.py --verify",
        "disjointReproduce": "rtk proxy python3 scripts/extract_rampage_w66.py --output-root /tmp/destiny-weapons-w66/reproduced",
        "verification": "Offline SHA pins for every consumed source; missing/changed inputs fail closed. --verify compares all five generated outputs byte-for-byte, including Markdown, and performs no writes or network IO. Supplemental live CMS observation is explicitly outside offline revalidation.",
    }
    outputs[REF + "provenance.json"] = provenance
    return outputs, paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Read-only, byte-exact check of every generated output")
    parser.add_argument("--root", type=Path, default=ROOT, help="Read-only input checkout")
    parser.add_argument("--output-root", type=Path, help="Separate output tree; inputs still come from --root")
    parser.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    parser.add_argument("--shared-sources-dir", type=Path, default=Path("/tmp/destiny-weapons-w60"))
    parser.add_argument("--sources-dir", type=Path, default=Path("/tmp/destiny-weapons-w66"))
    args = parser.parse_args()
    try:
        outputs, inputs = extract(args)
        output_root = (args.output_root or args.root).resolve()
        input_paths = {p.resolve() for p in inputs.values()} | {(args.root / SCRIPT).resolve()}
        resolved = [(output_root / name).resolve() for name in outputs]
        require(len(resolved) == len(set(resolved)), "Output paths alias each other")
        for name, path in zip(outputs, resolved):
            require(path.is_relative_to(output_root) and path not in input_paths,
                    "Output path aliases an input or escapes output root: " + name)
        if args.verify:
            for name, value in outputs.items():
                require((output_root / name).read_bytes() == encoded(value), "Generated bytes differ: " + name)
        else:
            for name, value in outputs.items():
                path = output_root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(encoded(value))
        print(("VERIFIED" if args.verify else "GENERATED") +
              ": W66; 63 selected; 21 exact-base randomized rows; 8 overlapping direct defaults add 0 rows; 4 enhanced options excluded; 0 Huckleberry options.")
        print("90-tick one-stack decay; multipliers 1/1.1/1.21/1.331. Stow/refresh: single explicit secondary source; identity/shot snapshots: project policy.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("W66 extraction failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
