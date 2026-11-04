#!/usr/bin/env python3
"""Offline W75 ADS ratio table; optional raw primary CSV proof, never network.

--verify is read-only. --source-dir additionally audits pinned original DDC exports.
The native-sneak adaptation is project policy, not the original Destiny motor.
"""
from pathlib import Path
import argparse, csv, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ["src/main/resources/destiny/weapons/w30.json", "art/weapons/w75/references/movement-source.json"]
OUTPUT = "src/main/resources/destiny/weapons/w75-aim-movement.json"
EVIDENCE = "art/weapons/w75/references/extraction.json"

def encoded(d):
    return (json.dumps(d, ensure_ascii=False, indent=2) + "\n").encode()

def generate(source_dir=None):
    raw = {p: (ROOT/p).read_bytes() for p in INPUTS}
    source = json.loads(raw[INPUTS[1]])
    assert source["stage"] == "W75"
    assert (source["ordinaryAdsScalar"], source["sidearmAdsScalar"], source["precisionHandCannonPenaltyReduction"],
            source["derivedPrecisionHandCannonScalar"]) == (.75, .85, .1, .775)
    if source_dir is not None:
        for name, expected in source["cacheSha256"].items():
            assert hashlib.sha256((source_dir/name).read_bytes()).hexdigest() == expected, name
        mechanics = list(csv.reader((source_dir/"ddc-game-mechanics.csv").open()))
        assert any("ADS has a 0.75x Movement Speed Multiplier" in c
                   and "Sidearms have a 0.85x Movement Speed Multiplier" in c for r in mechanics for c in r)
        perks = list(csv.reader((source_dir/"ddc-weapon-perks.csv").open()))
        r = next(r for r in perks if any("Precision Frame" in c and "(Hand Cannon)" in c for c in r))
        assert "10% Decreased ADS Movement Speed Penalty" in r[2]
    rows = []
    for e in json.loads(raw[INPUTS[0]]):
        if e["family"] in ("sword", "glaive"):
            continue
        scalar, rule = .75, "ordinary"
        if e["family"] == "sidearm":
            scalar, rule = .85, "sidearm"
        elif e["family"] == "hand_cannon" and e["frame"] == "precision":
            scalar, rule = .775, "precision_hand_cannon"
        rows.append(dict(id=e["id"], scalar=scalar, rule=rule))
    assert len(rows) == 57
    assert sum(r["rule"] == "sidearm" for r in rows) == 6
    assert [r["id"] for r in rows if r["rule"] == "precision_hand_cannon"] == ["seventh_seraph_officer_revolver"]
    return {OUTPUT: encoded(dict(stage="W75", weapons=rows)),
            EVIDENCE: encoded(dict(stage="W75", selectedAdsWeapons=57, ordinary=50, sidearm=6, precisionHandCannon=1,
                                  nativeSneakBase=.3, nativeAttributes=["minecraft:sneaking_speed","minecraft:movement_speed"],
                                  modifierOperation="ADD_MULTIPLIED_TOTAL", sneakAmount="1/0.3 - 1", speedAmount="sourcedScalar - 1",
                                  originalAbsoluteMovementRecreated=False,
                                  sha256={p:hashlib.sha256(v).hexdigest() for p,v in raw.items()}))}

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("--verify", action="store_true")
    p.add_argument("--source-dir", type=Path); a = p.parse_args(); outputs = generate(a.source_dir)
    for name, raw in outputs.items():
        path = ROOT/name
        if a.verify: assert path.read_bytes() == raw, "W75 drift: " + name
        else: path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    print(json.dumps(dict(stage="W75", outputs=2, weapons=57, verify=a.verify, rawPrimaryVerified=a.source_dir is not None)))

if __name__ == "__main__":
    main()
