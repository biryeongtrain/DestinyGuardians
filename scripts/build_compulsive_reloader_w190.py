#!/usr/bin/env python3
"""Generate W190 from pinned offline sources. --verify is read-only; no tests/builds."""
import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = "src/main/resources/destiny/weapons/w190-compulsive-reloader.json"
ART = "art/weapons/w190/compulsive-reloader/"
BASE, ENHANCED = 671806388, 595108252
VERSION = "245114.26.10.13.2000-1-bnet.66137"
EXPECTED = {
    "aishas_embrace": (2638190703, 7997267),
    "austringer": (3055790362, 2750499928),
    "beloved": (3107853529, 1196545279),
    "long_arm": (8293111, 3056706286),
    "nezarec_s_whisper": (254636484, 210449465),
}
PINS = {
    "inventory": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "plugsets": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "manifest": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "ddc": "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437",
    "src/main/resources/destiny/weapons/w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    "src/main/resources/destiny/weapons/w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "src/main/resources/destiny/weapons/w46-timing.json": "e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07",
    "art/weapons/w43/extraction.json": "a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5",
    "art/weapons/w46/weapon_formulas.json": "fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d",
    "src/main/java/kim/biryeong/destiny/weapon/WeaponReloadPolicy.java": "44fa1ae11e09f67371383cb82112fa0a3fe57b58a003441abade833173a43f54",
}
# Implemented trait resources only; same-socket choices are audited but never composed.
PROFILES = {
    "auto_loading_holster": "w60-holster.json", "kill_clip": "w61-kill-clip.json",
    "outlaw": "w62-outlaw.json", "rampage": "w66-rampage.json",
    "triple_tap": "w67-precision-return.json", "fourth_times_the_charm": "w67-precision-return.json",
    "snapshot_sights": "w68-snapshot.json", "archers_tempo": "w73-archers-tempo.json",
    "dragonfly": "w77-dragonfly.json", "explosive_payload": "w80-payload.json",
    "demolitionist": "w103-demolitionist.json", "tracking_module": "w104-tracking.json",
    "feeding_frenzy": "w108-feeding-frenzy.json", "one_for_all": "w109-one-for-all.json",
    "surrounded": "w109-surrounded.json", "grave_robber": "w110-grave-robber.json",
    "swashbuckler": "w110-swashbuckler.json", "multikill_clip": "w165-multikill-clip.json",
    "subsistence": "w167-subsistence.json", "rapid_hit": "w169-rapid-hit.json",
    "perpetual_motion": "w170-perpetual-motion.json", "tap_the_trigger": "w171-tap-the-trigger.json",
    "frenzy": "w172-frenzy.json", "adrenaline_junkie": "w173-adrenaline-junkie.json",
    "focused_fury": "w174-focused-fury.json", "stats_for_all": "w176-stats-for-all.json",
    "heating_up": "w177-heating-up.json", "threat_detector": "w178-threat-detector.json",
    "vorpal_weapon": "w181-vorpal.json", "high_impact_reserves": "w182-high_impact_reserves.json",
    "surplus": "w183-surplus.json", "elemental_capacitor": "w184-elemental_capacitor.json",
    "quickdraw": "w185-quickdraw.json", "lead_from_gold": "w187-lead_from_gold.json",
    "zen_moment": "w188-zen_moment.json", "firmly_planted": "w189-firmly_planted.json",
}


def require(ok, why):
    if not ok:
        raise ValueError(why)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def seconds(curve, stat):
    return curve["evpp"] * stat * stat + curve["vpp"] * stat + curve["offset"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    parser.add_argument("--plugsets", type=Path, default=Path("/tmp/destiny-weapons-w60/bungie-plugsets.json"))
    parser.add_argument("--manifest", type=Path, default=Path("/tmp/destiny-weapons-w60/manifest.json"))
    parser.add_argument("--ddc", type=Path, default=Path("/private/tmp/destiny-w190/ddc-perks.html"))
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    data, sources = {}, {}
    for key, pin in PINS.items():
        path = ROOT / key if "/" in key else getattr(args, key)
        raw = path.read_bytes()
        require(digest(raw) == pin, "source drift: " + key)
        sources[key] = {"sha256": pin, "bytes": len(raw)}
        data[key] = json.loads(raw) if path.suffix == ".json" else raw.decode()
    manifest = data["manifest"]["Response"]
    require(manifest["version"] == VERSION, "manifest version")
    components = manifest["jsonWorldComponentContentPaths"]["en"]
    require(all(components[k].endswith("-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json")
                for k in ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")), "component versions")
    rows = re.findall(r"<tr\b[^>]*>.*?</tr>", data["ddc"], re.S)
    row = next(r for r in rows if "Compulsive Reloader" in r)
    text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", row)).split())
    require(text.startswith("54 Compulsive Reloader") and "above 50%" in text
            and "+50" in text and "↑55" in text and "0.95x" in text, "DDC base/enhanced row54")
    inv, pools = data["inventory"], data["plugsets"]
    for perk_hash in (BASE, ENHANCED):
        p = inv[str(perk_hash)]
        require(p["hash"] == perk_hash and p["itemType"] == 19 and not p["plug"]["isDummyPlug"]
                and not p["redacted"] and not p["blacklisted"], "base/enhanced definition")
    prefix = "src/main/resources/destiny/weapons/"
    stats = {r["id"]: r for r in data[prefix + "w40-characteristics.json"]}
    timings = {r["id"]: r["timing"] for r in data[prefix + "w46-timing.json"]}
    mapping = {r["id"]: r for r in data["art/weapons/w43/extraction.json"]["entries"]}

    def official(roll):
        weapon = inv[str(roll["hash"])]
        traits = {i for c in weapon["sockets"]["socketCategories"]
                  if c["socketCategoryHash"] == 4241085061 for i in c["socketIndexes"]}
        socket = weapon["sockets"]["socketEntries"][roll["socket"]]
        pool = pools[str(roll["plugSetHash"])]
        return (weapon["inventory"]["tierType"] == 5 and roll["socket"] in traits
                and socket.get("randomizedPlugSetHash") == roll["plugSetHash"] and not pool["isFakePlugSet"]
                and any(p["plugItemHash"] == roll["perkHash"] and p.get("currentlyCanRoll") is True
                        for p in pool["reusablePlugItems"]))

    weapons, curves, baseline = [], [], []
    for weapon_id, (weapon_hash, pool_hash) in EXPECTED.items():
        roll = dict(id=weapon_id, hash=weapon_hash, socket=3, perkHash=BASE, plugSetHash=pool_hash)
        require(official(roll) and stats[weapon_id]["bungieHash"] == weapon_hash, "exact current socket " + weapon_id)
        # The exact W43 frame/category selects W46's original raw reload curve.
        m = mapping[weapon_id]
        raw = data["art/weapons/w46/weapon_formulas.json"][m["family"]]["cat"][m["category"]]["reload"]
        curve = {k: raw.get(k, 0.0) for k in ("evpp", "vpp", "offset")}
        stat = stats[weapon_id]["stats"]["4188031367"]
        require(inv[str(weapon_hash)]["stats"]["stats"]["4188031367"]["value"] == stat, "official reload stat")
        require(math.ceil(seconds(curve, stat) * 20) == timings[weapon_id]["reloadTicks"], "W46 baseline")
        long_arm = weapon_id == "long_arm"
        c = dict(id=weapon_id, baseReloadStat=stat, magazine=timings[weapon_id]["magazine"], reload=curve,
                 firstSeconds=1.0 if long_arm else None, intervalSeconds=0.65 if long_arm else None,
                 roundsPerInsert=2 if long_arm else 0)
        weapons.append(roll)
        curves.append(c)
        active_seconds = seconds(curve, min(100, stat + 50)) * .95
        ratio = active_seconds / seconds(curve, stat)
        baseline.append(dict(id=weapon_id, baseReloadStat=stat, rawBaseSeconds=seconds(curve, stat),
                             rawActiveSeconds=active_seconds,
                             firstTicks=math.ceil((1.0 * ratio if long_arm else active_seconds) * 20),
                             intervalTicks=math.ceil((.65 * ratio if long_arm else active_seconds) * 20)))
    pairs, excluded = [], []
    for perk_id, filename in PROFILES.items():
        path = prefix + filename
        raw = (ROOT / path).read_bytes()
        sources[path] = {"sha256": digest(raw), "bytes": len(raw)}
        profile = json.loads(raw)
        if filename == "w67-precision-return.json":
            profile = next(p for p in profile["perks"] if p["id"] == perk_id)
        for roll in profile.get("weapons", profile.get("rolls", [])):
            if roll["id"] not in EXPECTED:
                continue
            require(roll["hash"] == EXPECTED[roll["id"]][0] and official(roll), "current companion " + perk_id)
            pair = dict(id=roll["id"], perk=perk_id, roll=roll)
            (excluded if roll["socket"] == 3 else pairs).append(pair)
    pairs.sort(key=lambda p: (p["id"], p["perk"]))
    excluded.sort(key=lambda p: (p["id"], p["perk"]))
    reload_perks = {"outlaw", "feeding_frenzy", "rapid_hit", "perpetual_motion", "frenzy",
                    "stats_for_all", "threat_detector", "surplus", "elemental_capacitor"}
    reload_pairs = [(p["id"], p["perk"]) for p in pairs if p["perk"] in reload_perks]
    require(reload_pairs == [("austringer", "frenzy"), ("nezarec_s_whisper", "frenzy")], "reload companion audit drift")
    resource = dict(stage="W190", perk=dict(id="compulsive_reloader", hash=BASE, reloadBonus=50, durationMultiplier=.95),
                    policies=dict(threshold="STRICTLY_ABOVE_HALF_AT_RELOAD_ACCEPTANCE",
                                  rounding="CAP_TOTAL_STAT_0_100_RAW_SECONDS_SCALARS_SINGLE_CEIL_20TPS",
                                  longArm="LOCAL_1S_0_65S_PAIR_PHASES_TIMES_RAW_CURVE_RATIO",
                                  enhanced="EXCLUDED"), weapons=weapons, curves=curves, coSelections=pairs)
    resource_bytes = encode(resource)
    source = dict(stage="W190", manifestVersion=VERSION, componentPaths={k: components[k] for k in
                  ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")}, sourcePins=sources,
                  ddc=dict(url="https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1662574278",
                           tab="Weapon Perks", row=54, text=text, checked="2026-10-27", enhancedExcluded=ENHANCED),
                  generatorSha256=digest(Path(__file__).read_bytes()), resourceSha256=digest(resource_bytes),
                  baselineMath=baseline, coSelections=pairs, excludedSameSocket=excluded,
                  reloadCompanions=reload_pairs,
                  timingStatus="Historical approximate W46 community curves, not official current durations; Long Arm insert scaling is local policy.")
    for name, raw in ((RESOURCE, resource_bytes), (ART + "source.json", encode(source))):
        path = ROOT / name
        if args.verify:
            require(path.read_bytes() == raw, "generated output drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print(f"W190 {'verified' if args.verify else 'generated'}: five exact rolls; {len(pairs)} distinct companion pairs; reload companions {reload_pairs}; resource SHA256 {digest(resource_bytes)}")


if __name__ == "__main__":
    main()
