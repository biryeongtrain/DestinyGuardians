#!/usr/bin/env python3
"""Reproduce W58 Handling offline. --verify only reads; input SHA pins never refresh."""
import sys

# Keep first-use Python imports from creating bytecode caches during --verify.
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/weapons/w58"
TARGET = ROOT / "src/main/resources/destiny/weapons/w58-handling.json"
GENERATOR = "scripts/extract_handling_w58.py"
HANDLING = "943549884"
REPOSITORY = "https://github.com/d2foundry/oracle_engine"
COMMIT = "dcd0c7d302b056ffbb532edcb711d724a17ca8c1"
# Fixed reviewed baseline, deliberately independent of extraction.json/sourceHashes.
# A changed input fails generation AND verification; there is no refresh option.
PINS = {
    "src/main/resources/destiny/weapons/w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    "art/weapons/w40/definitions.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "src/main/resources/destiny/weapons/w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "art/weapons/w40/provenance.json": "281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42",
    "art/weapons/w43/extraction.json": "a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5",
    "art/weapons/w46/weapon_formulas.json": "fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d",
    "art/weapons/w46/stat_calc.rs": "5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2",
    "art/weapons/w46/rs_types.rs": "faa476e6589d2362cf9ee8dd948410adfa7fa8507e8809f3cd10bb13ebba9b90",
    "art/weapons/w46/d2_enums.rs": "db791f6c709e7007f8fab3fddc46ab34a0f78b9958fd9a0f897ad27f133baa4a",
    "art/weapons/w46/build.rs": "85b2e35f1db47f55c58900020ebf44be0e409802beac395b4b4c538fad67a1bd",
    "art/weapons/w46/stat-definitions.json": "e7959edc50506f902e548b5c9a7d55b119e1e14d0268d046259f13a4bd38b8fe",
    "art/weapons/w46/official-item-evidence.json": "030bb98e997df7c3c89bc23db75c5990234f762c5a41f075cd95fa7a7ba4ba2c",
    "art/weapons/w46/MIT-LICENSE": "50173139375c53459837abdeb7ad9f264eba4f0bc2bb2c676932991ce158778d",
    "art/weapons/w46/UNLICENSE": "6b0382b16279f26ff69014300541967a356a666eb0b91b422f6862f6b7dad17e",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return (ROOT / path).read_bytes()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def indexed(rows, label):
    require(isinstance(rows, list), label + " must be an array")
    result = {row["id"]: row for row in rows}
    require(len(rows) == len(result) == 63, label + " requires 63 unique ids")
    return result


def solve(curve, x):
    """Oracle StatQuadraticFormula::solve_at, including serde's default evpp=0."""
    require({"vpp", "offset"} <= curve.keys() <= {"evpp", "vpp", "offset"},
            "Unexpected handling curve fields")
    require(all(type(v) in (int, float) and math.isfinite(v) for v in curve.values()),
            "Nonfinite/nonnumeric handling coefficient")
    return curve.get("evpp", 0.0) * x * x + curve["vpp"] * x + curve["offset"]


def handling_times(ready, stow, stat):
    """Neutral modifiers only; source stat clamp and stow-at-100 floor retained."""
    require(type(stat) is int, "Handling must be an integer")
    x = min(100, max(0, stat))
    ready_seconds = solve(ready, x)
    raw_stow_seconds = solve(stow, x)
    floor_seconds = solve(stow, 100.0)
    return x, ready_seconds, raw_stow_seconds, floor_seconds, max(raw_stow_seconds, floor_seconds)


def ceil_ticks(seconds):
    require(math.isfinite(seconds) and seconds > 0, "Invalid handling duration")
    return math.ceil(seconds * 20)


def check_solver(sources):
    """Fail if the pinned implementation no longer establishes our solver semantics."""
    compact = lambda name: " ".join(sources["art/weapons/w46/" + name].decode().split())
    calc, types, build, enums = (compact(n) for n in
                                 ("stat_calc.rs", "rs_types.rs", "build.rs", "d2_enums.rs"))
    checks = (
        (types, "let x = x.clamp(0, 100) as f64;"),
        (types, "self.evpp * x * x + self.vpp * x + self.offset"),
        (types, "self.evpp * _x * _x + self.vpp * _x + self.offset"),
        (calc, "self.ready.solve_at_i(handling_stat + _modifiers.draw_add) * _modifiers.draw_scale"),
        (calc, "self.stow.solve_at_i(handling_stat + _modifiers.stow_add) * _modifiers.stow_scale) .clamp(self.stow.solve_at(100.0), f64::INFINITY)"),
        (calc, ".get(&StatHashes::HANDLING.into())"),
        (build, "#[serde(default)] pub evpp: f64"),
        (build, "let mut handling: HandlingFormula = cat.handling;"),
        (enums, "943549884 => StatHashes::HANDLING"),
        (enums, "StatHashes::HANDLING => 943549884"),
        (enums, "pub type Seconds = f64;"),
    )
    for source, snippet in checks:
        require(snippet in source, "Unverified Oracle handling semantics: " + snippet)
    # The build transfers category handling curves directly; /30 is firing-only.
    handling_struct = build.split("pub struct HandlingFormula {", 1)[1].split("}", 1)[0]
    require("pub ready: StatQuadraticFormula" in handling_struct and
            "pub stow: StatQuadraticFormula" in handling_struct,
            "Unverified direct handling curve representation")


def generate():
    # Read each dependency once: hashes and calculations describe identical bytes.
    sources = {path: read(path) for path in PINS}
    for path, sha in PINS.items():
        require(digest(sources[path]) == sha, "Pinned source drift: " + path)
    check_solver(sources)
    data = lambda path: json.loads(sources[path])
    catalog_rows = data("src/main/resources/destiny/weapons/w30.json")
    catalog = indexed(catalog_rows, "W30 catalog")
    official = indexed(data("art/weapons/w40/definitions.json"), "W40 official")
    runtime_official = indexed(data("src/main/resources/destiny/weapons/w40-characteristics.json"), "W40 runtime")
    evidence = indexed(data("art/weapons/w46/official-item-evidence.json"), "W46 selected official evidence")
    w43 = data("art/weapons/w43/extraction.json")
    mapping = indexed(w43["entries"], "W43 category mapping")
    require(catalog.keys() == official.keys() == runtime_official.keys() == evidence.keys() == mapping.keys(),
            "Selected weapon coverage mismatch")
    require(official == runtime_official, "Selected official stats differ from W40 runtime")
    require(w43["repository"] == REPOSITORY and w43["commit"] == COMMIT and
            w43["commitDate"] == "2026-05-20" and
            w43["sourceSha256"] == PINS["art/weapons/w46/weapon_formulas.json"],
            "W43/W46 Oracle provenance mismatch")
    provenance = data("art/weapons/w40/provenance.json")
    stat_definition = data("art/weapons/w46/stat-definitions.json")[HANDLING]
    require(stat_definition["hash"] == int(HANDLING) and
            stat_definition["displayProperties"]["name"] == "Handling" and
            stat_definition["displayProperties"]["description"] ==
            "The speed with which the weapon can be readied and aimed.",
            "Official Handling definition/name mismatch")
    formulas = data("art/weapons/w46/weapon_formulas.json")
    rows, audit = [], []
    for entry in catalog_rows:
        weapon_id = entry["id"]
        o, e, m = official[weapon_id], evidence[weapon_id], mapping[weapon_id]
        require(o["bungieHash"] == e["hash"] and o["stats"] == e["stats"],
                "Selected official item evidence mismatch: " + weapon_id)
        stat = o["stats"].get(HANDLING)
        sword = entry["family"] == "sword"
        require(("family" not in m) == sword, "W43 sword support mismatch: " + weapon_id)
        profile = dict(supported=not sword, handling=None, readyTicks=None, stowTicks=None)
        a = dict(id=weapon_id, bungieHash=o["bungieHash"], family=entry["family"],
                 catalogName=entry["name"], officialName=e["name"],
                 officialHandling=stat, supported=not sword,
                 oracleFamily=None, category=None, subfamily=None,
                 readyCurve=None, stowCurve=None, handlingStatUsed=None,
                 readySeconds=None, stowRawSeconds=None, stowFloorSeconds=None, stowSeconds=None)
        if sword:
            require(stat is None, "Unexpected sword Handling stat: " + weapon_id)
            a["unsupportedReason"] = "No pinned Oracle sword handling curves or official Handling stat; no inferred timings"
        else:
            require(type(stat) is int and 0 <= stat <= 100,
                    "Missing/out-of-range official Handling: " + weapon_id)
            family = formulas[m["family"]]
            require(m["subfamily"] in family["subFam"], "Unknown W43 subfamily")
            handling = family["cat"][m["category"]]["handling"]
            ready, stow = handling["ready"], handling["stow"]
            x, ready_s, raw_stow_s, floor_s, stow_s = handling_times(ready, stow, stat)
            profile.update(handling=stat, readyTicks=ceil_ticks(ready_s), stowTicks=ceil_ticks(stow_s))
            a.update(oracleFamily=m["family"], category=m["category"], subfamily=m["subfamily"],
                     readyCurve=ready, stowCurve=stow, handlingStatUsed=x,
                     readySeconds=ready_s, stowRawSeconds=raw_stow_s,
                     stowFloorSeconds=floor_s, stowSeconds=stow_s)
        rows.append(dict(id=weapon_id, profile=profile))
        audit.append(a)
    supported = sum(r["profile"]["supported"] for r in rows)
    require(len(rows) == 63 and supported == 58, "Expected 63 rows / 58 supported / 5 swords")
    runtime = encoded(rows)
    source_hashes = {path: digest(raw) for path, raw in sources.items()}
    # Self-hash is observational, not a self-referential constant; --verify detects
    # generator changes through the already-generated extraction bytes.
    source_hashes[GENERATOR] = digest(read(GENERATOR))
    metadata = dict(
        schemaVersion=1, profileCount=len(rows), supportedCount=supported, unsupportedCount=5,
        officialManifest=provenance,
        officialStatSource="https://www.bungie.net" + provenance["manifest"]["path"].replace(
            "DestinyInventoryItemDefinition-", "DestinyStatDefinition-"),
        statHashes=dict(handling=HANDLING), statDefinition=stat_definition,
        repository=REPOSITORY, commit=COMMIT, commitDate=w43["commitDate"],
        source=w43["source"], sourceUrl=REPOSITORY + "/blob/" + COMMIT + "/" + w43["source"],
        sourceSha256=PINS["art/weapons/w46/weapon_formulas.json"],
        categoryMapping="art/weapons/w43/extraction.json",
        solverSources=["art/weapons/w46/" + n for n in
                       ("stat_calc.rs", "rs_types.rs", "d2_enums.rs", "build.rs")],
        inputHashPolicy="Fixed PINS constants; fail closed on drift; never refresh from generated metadata",
        sourceHashes=source_hashes, runtimeSha256=digest(runtime),
        units=dict(handling="dimensionless official base stat", curves="seconds",
                   ticks="20 Hz Minecraft ticks", frameConversion="none; handling coefficients are already seconds"),
        policies=dict(
            official="Exact W40 selected Bungie base stats, equal to W40 runtime and W46 selected official evidence",
            curve="Historical community approximation; q(x)=evpp*x*x+vpp*x+offset; missing evpp=0 per build.rs serde default",
            stat="x=clamp(official Handling,0,100), as StatQuadraticFormula::solve_at_i; selected stats already in range",
            modifiers="Neutral base evaluation only: stat/draw/stow adds=0, draw/stow scales=1; no perks or armor",
            ready="ceil(q_ready(x)*20)",
            stow="ceil(max(q_stow(x),q_stow(100))*20); Oracle source floor retained",
            tickBounds="No additional minimum/maximum tick clamp; reject nonpositive/nonfinite source durations",
            unsupported="Five swords: supported=false; handling, readyTicks and stowTicks explicitly null",
            order="Exactly W30 selected catalog order; no clock, network, full inventory or environment-dependent input"),
        limitations=[
            "Official base manifest Oct13 2026 and community formula commit May20 2026 are distinct snapshots; no current exact balance claim",
            "Timings are historical community approximations, not official Bungie animation durations",
            "No perks, armor, subclass, masterwork, socket roll, exotic or other animation modifiers",
            "Glaive supports ready/stow only; its zero ADS curve does not make switching unsupported",
            "No sword handling is invented; unsupported runtime behavior belongs to the consumer",
            "20 Hz ceiling is the Minecraft adaptation; unrounded source curves and seconds are retained",
        ], entries=audit)
    return runtime, encoded(metadata)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Compare all generated bytes without writing anything")
    args = parser.parse_args()
    runtime, metadata = generate()
    outputs = ((TARGET, runtime), (ART / "extraction.json", metadata))
    if args.verify:
        for path, expected in outputs:
            require(path.read_bytes() == expected, "W58 generated drift: " + str(path.relative_to(ROOT)))
    else:
        ART.mkdir(parents=True, exist_ok=True)
        for path, expected in outputs:
            path.write_bytes(expected)
    print(("Verified" if args.verify else "Generated") +
          " 63 W58 handling profiles: 58 supported (including glaive), 5 unsupported swords")
    samples = {r["id"]: r["profile"] for r in json.loads(runtime)}
    for weapon_id in ("duke_mk_44", "austringer", "nezarec_s_whisper", "abide_the_return"):
        print(weapon_id + ": " + json.dumps(samples[weapon_id], separators=(",", ":")))


if __name__ == "__main__":
    main()
