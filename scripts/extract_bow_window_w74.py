#!/usr/bin/env python3
"""Offline deterministic W74 perfect-window data. --verify performs no writes/network.

Pinned W46 Oracle community formula, official W40/W46 selected base stats.
This is NOT a source of max-hold, late damage, accuracy decay or exotic bonuses.
"""
import argparse, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ["art/weapons/w46/stat_calc.rs", "art/weapons/w46/build.rs",
          "art/weapons/w46/extraction.json", "art/weapons/w46/official-item-evidence.json",
          "art/weapons/w46/stat-definitions.json", "src/main/resources/destiny/weapons/w30.json",
          "src/main/resources/destiny/weapons/w40-characteristics.json"]
OUTPUT = "src/main/resources/destiny/weapons/w74-bow-window.json"
EVIDENCE = "art/weapons/w74/references/perfect-window.json"

def encoded(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()

def generate():
    raw = {p: (ROOT / p).read_bytes() for p in INPUTS}
    calc = raw[INPUTS[0]].decode(); mapping = raw[INPUTS[1]].decode()
    assert "906 => stability * 1.0 / 400.0 + 0.3" in calc
    assert "905 => stability * 3.0 / 1000.0 + 0.5" in calc
    assert '905u32 => &["Lightweight Frame", "MIDA Synergy"]' in mapping
    assert '906u32 => &["Precision Frame", "Häkke Precision Frame"]' in mapping
    extraction = json.loads(raw[INPUTS[2]])
    assert extraction["commit"] == "dcd0c7d302b056ffbb532edcb711d724a17ca8c1"
    definitions = {e["id"]: e for e in json.loads(raw[INPUTS[3]])}
    stat = json.loads(raw[INPUTS[4]])["155624089"]
    assert stat["displayProperties"]["name"] == "Stability"
    catalog = json.loads(raw[INPUTS[5]])
    characteristics = {e["id"]: e for e in json.loads(raw[INPUTS[6]])}
    rows = []
    for e in catalog:
        if e["family"] != "bow":
            continue
        official = definitions[e["id"]]; base = characteristics[e["id"]]
        assert official["hash"] == base["bungieHash"]
        assert official["stats"] == base["stats"]
        s = official["stats"]["155624089"]
        assert 0 <= s <= 100
        if e["frame"] == "precision":
            micros = 300_000 + 2_500 * s
        elif e["frame"] == "lightweight":
            micros = 500_000 + 3_000 * s
        else:
            raise AssertionError("Unreviewed bow frame")
        rows.append(dict(id=e["id"], hash=official["hash"], frame=e["frame"], stability=s,
                         windowMicros=micros, windowTicks=(micros + 49_999) // 50_000))
    assert {r["id"] for r in rows} == {"biting_winds", "whispering_slab"}
    data = dict(stage="W74", weapons=rows)
    evidence = dict(stage="W74", oracleCommit=extraction["commit"], oracleRepository=extraction["repository"],
                    oracleFormulaSource="https://github.com/d2foundry/oracle_engine/blob/" + extraction["commit"] + "/src/weapons/stat_calc.rs",
                    officialCorroboration="https://www.bungie.net/7/en/News/article/51707",
                    officialScope="6.2.0 lightweight window endpoints 0.50s/0.80s and qualitative late damage/accuracy loss; no exact max-hold/decay curve",
                    interpolationScope="Precision and lightweight linear interpolation from pinned community calculator, not official engine measurement",
                    rounding="Integer microseconds; ceil(windowMicros/50000); half-open [fullDraw, fullDraw+windowTicks)",
                    baseStatsOnly=True, stabilityStatHash=155624089, weapons=rows,
                    forcedReleaseImplemented=False, lateDamageOrAccuracyPenaltyImplemented=False,
                    sha256={p: hashlib.sha256(v).hexdigest() for p, v in raw.items()})
    return {OUTPUT: encoded(data), EVIDENCE: encoded(evidence)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    outputs = generate()
    if args.verify:
        for p, raw in outputs.items():
            assert (ROOT / p).read_bytes() == raw, "W74 output drift: " + p
    else:
        for p, raw in outputs.items():
            path = ROOT / p; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    print(json.dumps(dict(stage="W74", outputs=len(outputs), selectedNormalBows=2, verified=args.verify)))

if __name__ == "__main__":
    main()
