#!/usr/bin/env python3
"""Offline W46 timing extraction; --verify never writes. Optional --inventory audits
the original W40 full Bungie cache (SHA pinned), rather than just its selected rows.
No RPM-to-burst guessing, reload-stat-as-seconds, tick truncation or runtime policy.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/weapons/w46"
TARGET = ROOT / "src/main/resources/destiny/weapons/w46-timing.json"
STATS = {"magazine": "3871231066", "rpm": "4284893193",
         "chargeMillis": "2961396640", "drawMillis": "447667954",
         "reloadSpeed": "4188031367"}
NAMES = dict(zip(STATS, ("Magazine", "Rounds Per Minute", "Charge Time", "Draw Time", "Reload Speed")))
PINS = {
    "src/main/resources/destiny/weapons/w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    "art/weapons/w40/definitions.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "art/weapons/w40/provenance.json": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "art/weapons/w43/extraction.json": "a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5",
    "art/weapons/w46/weapon_formulas.json": "fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d",
    "art/weapons/w46/stat_calc.rs": "5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2",
    "art/weapons/w46/build.rs": "85b2e35f1db47f55c58900020ebf44be0e409802beac395b4b4c538fad67a1bd",
    "art/weapons/w46/weapon_constructor.rs": "50ea523af8ec5df1041e5f3cb1cafc84b03d2ffb59029f81303ec41ae4e367b9",
    "art/weapons/w46/rs_types.rs": "faa476e6589d2362cf9ee8dd948410adfa7fa8507e8809f3cd10bb13ebba9b90",
    "art/weapons/w46/stat-definitions.json": "e7959edc50506f902e548b5c9a7d55b119e1e14d0268d046259f13a4bd38b8fe",
    "art/weapons/w46/d2_enums.rs": "db791f6c709e7007f8fab3fddc46ab34a0f78b9958fd9a0f897ad27f133baa4a",
    "art/weapons/w46/official-item-evidence.json": "030bb98e997df7c3c89bc23db75c5990234f762c5a41f075cd95fa7a7ba4ba2c",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def read(name):
    return (ROOT / name).read_bytes()


def positive(value):
    return value if type(value) is int and value > 0 else None


def ceil_ticks(seconds):
    require(math.isfinite(seconds) and seconds > 0, "Nonpositive/nonfinite duration")
    return math.ceil(seconds * 20)


def generate(inventory=None):
    for path, sha in PINS.items():
        require(digest(read(path)) == sha, "Pinned source drift: " + path)
    catalog = json.loads(read("src/main/resources/destiny/weapons/w30.json"))
    official = json.loads(read("art/weapons/w40/definitions.json"))
    require(official == json.loads(read("src/main/resources/destiny/weapons/w40-characteristics.json")), "W40 runtime/source drift")
    provenance = json.loads(read("art/weapons/w40/provenance.json"))
    w43 = json.loads(read("art/weapons/w43/extraction.json"))
    mapping = {r["id"]: r for r in w43["entries"]}
    source = json.loads((ART / "weapon_formulas.json").read_bytes())
    stat_defs = json.loads((ART / "stat-definitions.json").read_bytes())
    evidence = json.loads((ART / "official-item-evidence.json").read_bytes())
    ids = {r["id"] for r in catalog}
    require(len(ids) == len(catalog) == len(official) == len(mapping) == len(evidence) == 63, "63 unique selected items required")
    require(ids == {r["id"] for r in official} == mapping.keys() == {r["id"] for r in evidence}, "Coverage drift")
    for name, stat in STATS.items():
        require(stat_defs[stat]["displayProperties"]["name"] == NAMES[name], "Official stat identity drift")
    for name in ("chargeMillis", "drawMillis"):
        require("milliseconds" in stat_defs[STATS[name]]["displayProperties"]["description"], "Unverified millisecond unit")
    build = (ART / "build.rs").read_text()
    calc = (ART / "stat_calc.rs").read_text()
    types = (ART / "rs_types.rs").read_text()
    require("burst_delay: value.burst_delay / 30.0" in build and "inner_burst_delay: value.inner_burst_delay / 30.0" in build, "Unverified firing units")
    require("self.evpp * _x * _x + self.vpp * _x + self.offset" in types, "Unverified quadratic")
    require("reload_time = self.reload_data.solve_at(_reload_stat as f64)" in calc and "reload_stat.clamp(0, 85)" in calc, "Unverified reload semantics")
    require("0.45" in calc and "0.95" in calc and "(inner_burst_delay * (burst_size as f64 - 1.0))" in calc, "Unverified firing period")
    require("pub type Seconds = f64;" in (ART / "d2_enums.rs").read_text(), "Seconds alias missing")
    by_id = {r["id"]: r for r in official}
    for e in evidence:
        r = by_id[e["id"]]
        require(e["hash"] == r["bungieHash"] and e["stats"] == r["stats"], "Selected official evidence drift")
    if inventory:
        raw = inventory.read_bytes()
        require(digest(raw) == provenance["cachedInventorySha256"], "Unexpected full inventory cache")
        full = json.loads(raw)
        for e in evidence:
            item = full[str(e["hash"])]
            require(item["displayProperties"]["name"] == e["name"] and
                    {k: v["value"] for k, v in item["stats"]["stats"].items()} == e["stats"], "Full-cache evidence mismatch")

    rows, audit = [], []
    for e in catalog:
        r, m = by_id[e["id"]], mapping[e["id"]]
        family = e["family"]
        raw_stats = {k: r["stats"].get(h) for k, h in STATS.items()}
        supported = "family" in m
        charged = family in ("fusion_rifle", "linear_fusion_rifle")
        shell = family == "shotgun"
        warnings = []
        p = dict(supported=supported,
                 magazine=positive(raw_stats["magazine"]),
                 rpm=positive(raw_stats["rpm"]),
                 chargeMillis=positive(raw_stats["chargeMillis"]) if charged else None,
                 drawMillis=positive(raw_stats["drawMillis"]) if family == "bow" else None,
                 cadenceTicks=None, burstSpacingTicks=None, burstSize=1,
                 sharedBurstAmmo=charged, chargeTicks=None, drawTicks=None,
                 reloadTicks=None, shellReload=shell,
                 reloadPerRoundTicks=None, reloadInitialTicks=None)
        a = dict(id=e["id"], bungieHash=r["bungieHash"], family=family, officialStats=raw_stats)
        if p["chargeMillis"] is not None:
            p["chargeTicks"] = ceil_ticks(p["chargeMillis"] / 1000)
        if p["drawMillis"] is not None:
            p["drawTicks"] = ceil_ticks(p["drawMillis"] / 1000)
        if raw_stats["chargeMillis"] is not None and not charged:
            warnings.append("Charge Time hash reused for non-charge stat; not interpreted as milliseconds for this family")
        if p["magazine"] is None:
            warnings.append("Official magazine stat absent/nonpositive; no override")
        if family == "sword":
            warnings.append("Exact Magazine stat is sword ammo capacity, not a reloadable magazine; supported=false")
        if supported:
            data = source[m["family"]]
            firing = data["subFam"][m["subfamily"]]
            curve = data["cat"][m["category"]]["reload"]
            require(set(curve) <= {"evpp", "vpp", "offset", "ammo_percent"}, "Unknown reload curve fields")
            n = firing.get("burst_size", 1)
            end, inner = firing["burst_delay"] / 30, firing["inner_burst_delay"] / 30
            require(type(n) is int and 1 <= n <= 12 and end >= 0 and inner >= 0, "Unsafe firing data")
            simultaneous_pellets = family == "shotgun" and inner == 0
            p["burstSize"] = 1 if simultaneous_pellets else n
            p["burstSpacingTicks"] = 0.0 if simultaneous_pellets else round(inner * 20, 12)
            extra = .45 if family == "fusion_rifle" else .95 if family == "linear_fusion_rifle" else 0
            seconds = end + (n - 1) * inner + extra
            if charged:
                # Main scheduler applies the subsequent official charge independently.
                # Oracle end delay is itself charge-like, so do not add it a second time.
                p["cadenceTicks"] = round(((n - 1) * inner + extra) * 20, 12)
            elif p["rpm"] is not None and (n == 1 or simultaneous_pellets):
                p["cadenceTicks"] = round(1200 / p["rpm"], 12)
            elif seconds > 0:
                p["cadenceTicks"] = round(seconds * 20, 12)
            else:
                warnings.append("Oracle has zero firing period for bows; draw/nock cycle is separate, no cadence override")
            reload_stat = raw_stats["reloadSpeed"]
            require(type(reload_stat) is int and 0 <= reload_stat <= 100, "Unsafe/missing Reload Speed stat")
            x = min(reload_stat, 85) if family == "bow" else reload_stat
            reload_seconds = curve.get("evpp", 0) * x * x + curve.get("vpp", 0) * x + curve["offset"]
            ticks = ceil_ticks(reload_seconds)
            p["reloadPerRoundTicks" if shell else "reloadTicks"] = ticks
            a.update(oracleFamily=m["family"], category=m["category"], subfamily=m["subfamily"],
                     firingFrames={k: firing.get(k, False if k == "one_ammo" else 1) for k in ("burst_delay", "inner_burst_delay", "burst_size", "one_ammo")},
                     oraclePeriodSeconds=seconds, extraRecoverySeconds=extra,
                     reloadCurve=curve, reloadStatUsed=x, reloadSeconds=reload_seconds)
            if charged:
                warnings.append("Cadence is post-first-bolt lockout: bolt span plus fixed recovery, EXCLUDES charge. Subsequent official chargeTicks is separate; historical Oracle end delay is NOT added")
                if abs(end * 1000 - p["chargeMillis"]) > 1:
                    warnings.append("Official charge milliseconds differ from historical Oracle end delay; both retained independently")
            if shell:
                warnings.append("Per-shell/per-round classification is a gameplay assumption, not independently established by the Oracle quadratic; initial-entry delay unverified and intentionally absent")
            if e["id"] == "long_arm":
                warnings.append("Original two-round loading not reconstructed; no verified per-insert curve. Whole-magazine default scout reload approximation retained, shellReload=false")
            if simultaneous_pellets:
                a["simultaneousPellets"] = n
                warnings.append("Oracle burst_size counts simultaneous pellets; runtime burstSize=1, existing pellet geometry must remain separate")
            if p["rpm"] and not charged and seconds > 0:
                effective_rpm = 60 * (1 if simultaneous_pellets else n) / seconds
                a["oracleEffectiveRpm"] = effective_rpm
                if abs(effective_rpm - p["rpm"]) > 1:
                    warnings.append("Official RPM differs from pinned Oracle cadence; official raw RPM retained, cadence uses verified frame delays")
        else:
            warnings.append("Sword unsupported: no Oracle timing model; retain existing runtime policy")
        a["warnings"] = warnings
        rows.append(dict(id=e["id"], timing=p))
        audit.append(a)
    runtime = encoded(rows)
    paths = list(PINS) + ["src/main/resources/destiny/weapons/w40-characteristics.json",
                         "art/weapons/w46/MIT-LICENSE", "art/weapons/w46/UNLICENSE",
                         "scripts/extract_weapon_timing_w46.py"]
    metadata = dict(schemaVersion=1, profileCount=63, supportedCount=sum(r["timing"]["supported"] for r in rows),
                    officialManifest=provenance,
                    officialStatSource="https://www.bungie.net" + provenance["manifest"]["path"].replace("DestinyInventoryItemDefinition-", "DestinyStatDefinition-"),
                    statHashes=STATS, statMeanings={k: stat_defs[h]["displayProperties"] for k, h in STATS.items()},
                    repository=w43["repository"], commit=w43["commit"], commitDate=w43["commitDate"],
                    sourceHashes={p: digest(read(p)) for p in paths}, runtimeSha256=digest(runtime),
                    policies=dict(magazine="Exact positive official base stat; absent remains null, no perk/mag interpolation. Sword value is ammo capacity only; supported=false",
                                  cadence="FIRING LOCKOUT AFTER FIRST BOLT, excludes subsequent charge: normal single-shot/pellet guns 1200/officialRPM; pulse/burst-sidearm 20*(endFrames+(N-1)*innerFrames)/30; fusion/LFR 20*((N-1)*innerFrames/30+fixedRecoverySeconds). Do not add Oracle charge-like end delay",
                                  charge="Official milliseconds only for fusion/LFR; ceil(milliseconds/50), independent from historical Oracle cadence",
                                  draw="Official bow Draw Time milliseconds only; ceil(milliseconds/50)",
                                  reload="Historical community approximation evpp*x*x+vpp*x+offset seconds; ceil(seconds*20); bow x=min(ReloadSpeed,85); not raw Reload Speed seconds",
                                  shell="Only shotguns use per-shell model (classification requires direct-source confirmation; Oracle does not encode granularity). Long Arm retains whole-mag scout approximation: original two-round loading not reconstructed; no verified insert timing",
                                  burst="Pulse/sidearm consume per bullet. Fusion/LFR shared ammo per burst; shotgun zero-spacing pellets stay geometry, burstSize=1"),
                    limitations=["Official base snapshot Oct13 vs historical community curves May20; no current sandbox exactness claim",
                                 "No perk/armor/frame/exotic animation modifiers; reload quadratics explicitly approximate in source",
                                 "Shotgun per-shell classification needs independent direct-source confirmation; Oracle does not establish granularity or initial delay. Long Arm keeps whole-mag scout approximation, not an unverified per-insert duration",
                                 "Unknown/missing values remain null; five swords unsupported, bows have no cadence or official magazine override",
                                 "Glaive reused Charge Time ignored; ranged cadence/reload/magazine only, no melee timing",
                                 "ceil to 20 Hz is Minecraft adaptation; fractional cadence and bolt spacing retained to 12 decimals",
                                 "Pure data/API only; no WeaponProfile, WeaponCycle or runtime integration"], entries=audit)
    return runtime, encoded(metadata)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--inventory", type=Path, help="Optional full W40 official inventory cache audit")
    args = parser.parse_args()
    runtime, metadata = generate(args.inventory)
    for path, expected in ((TARGET, runtime), (ART / "extraction.json", metadata)):
        if args.verify:
            require(path.read_bytes() == expected, "W46 generated drift: " + str(path.relative_to(ROOT)))
        else:
            path.write_bytes(expected)
    print(("Verified" if args.verify else "Generated") + " 63 W46 timing rows; 58 ranged / 5 unsupported swords; pinned official and Oracle sources")


if __name__ == "__main__":
    main()
