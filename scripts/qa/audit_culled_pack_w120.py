#!/usr/bin/env python3
"""Exact W120 server-generated pack audit vs sealed W118 actual pack.

Not a client render/animation/performance test. JUnit exports actual Java output
rules into build/qa/w119-culling; stale or altered expected inputs are rejected.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources"
BASE = Path("/private/tmp/destiny-w118-native/server/polymer/resource_pack.zip")
NEW = Path("/private/tmp/destiny-w120-pack/server/polymer/resource_pack.zip")
EXPORT = ROOT / "build/qa/w119-culling"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit(old=BASE, new=NEW):
    provenance = json.loads((ROOT / "docs/qa/2026-10-25/w118/runtime-artifact-provenance.json").read_text())
    pin = next(r["sha256"] for r in provenance if r["path"] == str(BASE))
    assert sha(old.read_bytes()) == pin, "Sealed W118 actual pack drift"
    manifest = json.loads((RES / "weapon_surface_w115/manifest.json").read_text())
    expected_audit = json.loads((EXPORT / "audit.json").read_text())
    rules = {r["path"]: r for r in manifest["targets"]}
    assert len(rules) == 7 and set(rules) == set(expected_audit)
    rows = []
    with zipfile.ZipFile(old) as a, zipfile.ZipFile(new) as b:
        for z in (a, b):
            names = z.namelist()
            assert len(names) == len(set(names)), "Duplicate ZIP entry"
        inventory = lambda z: {n for n in z.namelist() if n.startswith("assets/destiny/") and not n.endswith("/")}
        before, after = inventory(a), inventory(b)
        assert before == after, {"added": sorted(after-before), "removed": sorted(before-after)}
        changed = {n for n in before if a.read(n) != b.read(n)}
        assert changed == set(rules), ("Only exact seven optimized destinations may change", sorted(changed))
        for path, rule in rules.items():
            authored = (RES / rule["replacement"]).read_bytes()
            expected = (EXPORT / Path(path).name).read_bytes()
            meta = expected_audit[path]
            assert sha(authored) == meta["inputSha256"] == rule["replacementSha256"], "Stale authored input"
            assert sha(expected) == meta["outputSha256"], "Stale Java output export"
            assert a.read(path) == authored, "Baseline is not the sealed authored candidate"
            assert b.read(path) == expected, "Real callback output differs from tested Java rule"
            assert b.read(rule["replacement"]) == authored, "Editable classpath source was rewritten"
            original, optimized = json.loads(authored), json.loads(expected)
            source = {e["name"]: e for e in original["elements"]}
            assert all(source[e["name"]] == e for e in optimized["elements"])
            rows.append(dict(path=path, authoredSha256=sha(authored), emittedSha256=sha(expected),
                             elementsBefore=len(original["elements"]), elementsAfter=len(optimized["elements"]),
                             facesBefore=sum(len(e["faces"]) for e in original["elements"]),
                             facesAfter=sum(len(e["faces"]) for e in optimized["elements"])))
        for weapon, family, parts in (("blast_furnace", "pulse_rifle", ("body", "magazine")),
                                      ("hammerhead", "machine_gun", ("body", "magazine", "cover"))):
            full = json.loads(b.read(f"assets/destiny/models/weapon/{family}/{weapon}.json"))
            assembly = []
            for part in parts:
                split = json.loads(b.read(f"assets/destiny/models/weapon_reload_w114_{weapon}/{weapon}_{part}.json"))
                assert split["textures"] == full["textures"]
                assembly.extend(split["elements"])
            assert assembly == full["elements"], "Actual pack must preserve ordered independently-culled parts"
            atlas = f"assets/destiny/textures/item/weapon/w115/{weapon}.png"
            assert b.read(atlas) == (RES / atlas).read_bytes() == a.read(atlas)
            assert atlas + ".mcmeta" not in b.namelist(), "Opacity proof assumes static source atlas"
    return dict(kind="actual_headless_server_output_not_client_evidence", oldPackSha256=pin,
                newPackSha256=sha(new.read_bytes()), destinyFiles=len(after), changed=sorted(changed),
                unchanged=len(after)-len(changed), added=0, removed=0, targets=rows,
                authoredSourcesUnchanged=True, samePartFullAssemblyVerified=True,
                framebuffer=False, nativeInput=False, fpsMeasurement=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=NEW)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists(), "Never overwrite prior audit evidence"
    result = audit(new=args.pack)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("destinyFiles", "unchanged", "newPackSha256")}))
