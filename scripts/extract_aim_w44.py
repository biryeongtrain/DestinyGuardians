#!/usr/bin/env python3
"""Generate/verify 63 W44 aim profiles from pinned W40 stats and W43 ADS curves.

Offline; --source must be the W43-pinned weapon_formulas.json. All generated
files stay in W44 scope. Verification never writes files. See W44 README.md.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/weapons/w44"
RUNTIME = ROOT / "src/main/resources/destiny/weapons/w44-aim.json"
STATS = {"handling": "943549884", "stability": "155624089",
         "zoom": "3555269338", "recoilDirection": "2715839340"}
FAMILIES = {
    "hand_cannon": ("Hand Cannon", 1.5, 1.5),
    "auto_rifle": ("Auto Rifle", 1.6, .45),
    "submachine_gun": ("Submachine Gun", 1.4, .30),
    "pulse_rifle": ("Pulse Rifle", 1.7, .60),
    "scout_rifle": ("Scout Rifle", 2.0, .80),
    "sidearm": ("Sidearm", 1.2, .55),
    "sniper_rifle": ("Sniper Rifle", 4.5, 1.60),
    "fusion_rifle": ("Fusion Rifle", 1.3, .90),
    "linear_fusion_rifle": ("Linear Fusion Rifle", 2.5, 1.25),
    "trace_rifle": ("Trace Rifle", 1.6, .10),
    "machine_gun": ("Machine Gun", 1.6, .65),
    "shotgun": ("Shotgun", 1.0, 2.0),
    "bow": ("Combat Bow", 1.8, .35),
    "grenade_launcher": ("Grenade Launcher", 1.0, 1.25),
    "heavy_grenade_launcher": ("Grenade Launcher", 1.0, 1.40),
    "rocket_launcher": ("Rocket Launcher", 1.0, 2.0),
}
NEUTRAL = dict(transitionTicks=2, zoom=1.0, falloffScalar=1.0,
               stability=0.0, recoilDirection=0, kick=0.0,
               bloomPerShot=0.0, recoveryPerTick=0.0)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def read(relative):
    return (ROOT / relative).read_bytes()


def generate(source_path):
    w43_raw = read("art/weapons/w43/extraction.json")
    w43 = json.loads(w43_raw)
    raw = source_path.read_bytes()
    require(digest(raw) == w43["sourceSha256"], "Unexpected W43 formula snapshot")
    source = json.loads(raw)
    stat_raw = (ART / "stat_calc.rs").read_bytes()
    build_raw = (ART / "build.rs").read_bytes()
    require(digest(stat_raw) == "5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2", "Unexpected pinned stat_calc.rs")
    require(digest(build_raw) == "85b2e35f1db47f55c58900020ebf44be0e409802beac395b4b4c538fad67a1bd", "Unexpected pinned build.rs")
    # Verify the special frame's intrinsic identity and multiplier, not its Zoom.
    require('904u32 => &["Aggressive Frame", "Aggressive Glaive", "Aggressive Burst"]' in build_raw.decode(), "Aggressive intrinsic mapping changed")
    require(re.search(r"\(WeaponType::PULSERIFLE, 904 \| 907\) => 1\.8", stat_raw.decode()), "Aggressive pulse scalar not verified")
    require('(WeaponType::MACHINEGUN, _) => 1.6, //this is a guess from zoom values' in stat_raw.decode(), "MG community guess annotation changed")

    catalog_raw = read("src/main/resources/destiny/weapons/w30.json")
    official_raw = read("art/weapons/w40/definitions.json")
    official_runtime_raw = read("src/main/resources/destiny/weapons/w40-characteristics.json")
    official_provenance_raw = read("art/weapons/w40/provenance.json")
    catalog = json.loads(catalog_raw)
    official_rows = json.loads(official_raw)
    official = {e["id"]: e for e in official_rows}
    mapping = {e["id"]: e for e in w43["entries"]}
    ids = {e["id"] for e in catalog}
    require(len(catalog) == len(ids) == len(official_rows) == len(official) == len(w43["entries"]) == len(mapping) == 63, "Expected 63 unique source entries")
    require(ids == official.keys() == mapping.keys(), "Source catalog coverage mismatch")
    require(json.loads(official_runtime_raw) == official_rows, "W40 runtime/source drift")

    rows, entries = [], []
    for e in catalog:
        item, m = official[e["id"]], mapping[e["id"]]
        supported = e["family"] not in ("sword", "glaive")
        provenance = dict(id=e["id"], family=e["family"], frame=e["frame"],
                          bungieHash=item["bungieHash"], supported=supported,
                          officialStats={k: item["stats"].get(v) for k, v in STATS.items()})
        if not supported:
            profile = dict(NEUTRAL)
            provenance["policy"] = "Unsupported sword/glaive; neutral, no ADS/recoil tuning"
        else:
            family, scalar, base_kick = FAMILIES[e["family"]]
            require(m.get("family") == family, "W43 family mismatch: " + e["id"])
            # Exact W43 category, including slug/aggressive/special/heavy and 'aggresive'.
            curve = source[family]["cat"][m["category"]]["handling"]["ads"]
            require(set(curve) <= {"offset", "vpp", "evpp"} and curve.get("evpp", 0) == 0, "Expected linear ADS curve")
            stats = provenance["officialStats"]
            require(all(type(v) is int and 0 <= v <= 100 for v in stats.values()), "Missing/out-of-range official aim stat: " + e["id"])
            handling = stats["handling"]
            stability = stats["stability"]
            ads_seconds = curve["offset"] + curve["vpp"] * handling
            require(math.isfinite(ads_seconds) and ads_seconds > 0, "Unsafe ADS curve")
            if e["family"] == "pulse_rifle" and m["subfamily"] == "Aggressive":
                require(e["source_frame_label"] == "Aggressive Burst", "Unverified aggressive pulse intrinsic")
                scalar = 1.8
                provenance["falloffPolicy"] = "Pinned Foundry intrinsic 904 aggressive pulse exception"
            elif e["family"] == "shotgun" and m["category"] == "slug":
                require(e["frame"] == "pinpoint_slug", "Unverified slug mapping")
                scalar = 1.2
            elif e["family"] == "machine_gun":
                provenance["falloffPolicy"] = "1.6 is explicitly a community guess in pinned Foundry source"
            elif e["family"] == "auto_rifle" and e["frame"] == "high_impact":
                provenance["falloffPolicy"] = "May 29 official correction supplied by task: 1.6, overrides pinned 1.7"
            elif e["family"] == "pulse_rifle" and e["frame"] in ("high_impact", "legacy_pr55"):
                provenance["falloffPolicy"] = "May 29 official correction supplied by task: 1.7, overrides pinned 1.6"
            elif e["family"] in ("grenade_launcher", "heavy_grenade_launcher", "rocket_launcher"):
                provenance["falloffPolicy"] = "Neutral explosive scalar 1; does not extend blast radius"
            profile = dict(transitionTicks=max(2, min(20, math.ceil(ads_seconds * 20))),
                           zoom=max(1.0, min(6.0, stats["zoom"] / 10)),
                           falloffScalar=scalar, stability=float(stability),
                           recoilDirection=stats["recoilDirection"],
                           kick=round(max(.1, min(2.0, base_kick * (1 - .6 * stability / 100))), 6),
                           bloomPerShot=round(.02 + .18 * (1 - stability / 100), 6),
                           recoveryPerTick=.04)
            provenance.update(oracleFamily=family, category=m["category"], subfamily=m["subfamily"],
                              adsCurve=curve, adsSeconds=ads_seconds, baseKickDegrees=base_kick)
        rows.append(dict(id=e["id"], profile=profile))
        entries.append(provenance)
    runtime = encoded(rows)
    sources = [
        ("src/main/resources/destiny/weapons/w30.json", catalog_raw),
        ("art/weapons/w40/definitions.json", official_raw),
        ("src/main/resources/destiny/weapons/w40-characteristics.json", official_runtime_raw),
        ("art/weapons/w40/provenance.json", official_provenance_raw),
        ("art/weapons/w43/extraction.json", w43_raw),
        ("art/weapons/w44/stat_calc.rs", stat_raw),
        ("art/weapons/w44/build.rs", build_raw),
        ("scripts/extract_aim_w44.py", Path(__file__).read_bytes()),
    ]
    for name in ("MIT-LICENSE", "UNLICENSE"):
        license_raw = (ART / name).read_bytes()
        require(license_raw == read("art/weapons/w43/" + name), "W43 license attribution drift")
        sources.append(("art/weapons/w44/" + name, license_raw))
    metadata = dict(schemaVersion=1, repository=w43["repository"], commit=w43["commit"],
                    commitDate=w43["commitDate"], source=w43["source"],
                    sourceSha256=digest(raw), sourceHashes={p: digest(b) for p, b in sources},
                    officialManifest=json.loads(official_provenance_raw),
                    runtimeSha256=digest(runtime), profileCount=63, supportedCount=57,
                    formulaPolicy=dict(
                        transitionTicks="clamp(ceil((offset + vpp * clamp(Handling,0,100)) * 20),2,20)",
                        zoom="clamp(official Zoom / 10,1,6); visual magnification only",
                        falloffScalar="Historical Foundry family/frame mappings, independent of Zoom",
                        corrections="May 29 official High-Impact AR 1.6 and High-Impact/Legacy Pulse 1.7, as explicitly supplied in task; official article text could not be retrieved independently",
                        stability="Official Stability stat, 0..100 (not normalized)",
                        recoilDirection="Official RecoilDirection stat, 0..100; metadata, not a reconstructed pattern",
                        kick="clamp(familyBaseDegrees * (1 - 0.6 * Stability / 100),0.1,2); rounded to 6 decimals",
                        bloomPerShot="0.02 + 0.18 * (1 - Stability / 100) normalized bloom (0..1); rounded to 6 decimals",
                        recoveryPerTick="0.04 normalized bloom per Minecraft tick; local tuning",
                        neutral=NEUTRAL),
                    familyTuning={k: dict(oracleFamily=v[0], defaultFalloffScalar=v[1], baseKickDegrees=v[2]) for k, v in FAMILIES.items()},
                    licenses=["MIT-LICENSE", "UNLICENSE"],
                    limitations=[
                        "Pinned community handling/range model, not a claim of current exact Destiny sandbox",
                        "Only selected-item base stats; no perk, armor, frame bonus, or animation modifiers",
                        "Kick, bloom, recovery and 20 Hz rounding/bounds are Minecraft tuning, not original recoil formulas",
                        "No deterministic recoil pattern, yaw direction or exact recoil claim; RecoilDirection is metadata only",
                        "Machine Gun falloff 1.6 is explicitly a community guess",
                        "Sword/glaive unsupported: six neutral entries; 57 supported ranged profiles",
                        "Data/API only; no runtime, input, HUD, camera, registration or build integration",
                    ], entries=entries)
    return runtime, encoded(metadata)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    runtime, metadata = generate(args.source)
    targets = [(RUNTIME, runtime), (ART / "extraction.json", metadata)]
    if args.verify:
        for path, expected in targets:
            require(path.read_bytes() == expected, "W44 extraction drift: " + str(path.relative_to(ROOT)))
    else:
        for path, expected in targets:
            path.write_bytes(expected)
    print(("Verified" if args.verify else "Generated") + " 63/63 W44 aim profiles (57 ranged + 6 neutral), pinned source hashes and attribution")


if __name__ == "__main__":
    main()
