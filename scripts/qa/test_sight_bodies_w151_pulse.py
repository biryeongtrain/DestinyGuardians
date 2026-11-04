#!/usr/bin/env python3
"""Offline W151 source/UV preservation, real aperture and provenance regression."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("w151_pulse", ROOT / "scripts/generate_sight_bodies_w151_pulse.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
IDS = ("cold_denial", "bygones", "chattering_bone", "blast_furnace", "claws_of_the_wolf", "hammerhead")
EXPECTED_REMOVED = {
    "claws_of_the_wolf": ["optic_rear", "optic_lens"],
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(data):
    def reject(value):
        raise ValueError("non-finite JSON: "+value)
    return json.loads(data, parse_constant=reject)


class W151PulseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = g.generate()
        cls.rows = strict_json((ROOT / "art/weapons/w151/pulse-sights.json").read_bytes())["weapons"]
        cls.models = {r["id"]: strict_json((g.ASSETS / ("models/"+r["body"]+".json")).read_bytes()) for r in cls.rows}

    def test_contract_all_six_and_anchors(self):
        self.assertEqual(tuple(r["id"] for r in self.rows), IDS)
        self.assertEqual(len({r["style"] for r in self.rows}), 6)
        for r in self.rows:
            with self.subTest(id=r["id"]):
                x, y, z = r["sightCenter"]
                self.assertEqual(r["forwardPoint"], [x, y, z-2])
                self.assertEqual(r["eyeSide"], "+Z")
                self.assertEqual(r["plane"], "XY")
                self.assertEqual((r["scale"], r["eyeToSightMeters"]), (.9, .32 if r["id"] == "blast_furnace" else .65))
                self.assertEqual(r["body"], "weapon_sight_w151/"+r["id"]+"_body")
                self.assertEqual(r["family"], "machine_gun" if r["id"] == "hammerhead" else "pulse_rifle")

    def test_entire_source_geometry_faces_uv_and_metadata_preserved(self):
        for r in self.rows:
            with self.subTest(id=r["id"]):
                source = ROOT / r["source"]
                self.assertEqual(r["source"], "src/main/resources/assets/destiny/models/weapon_surface_w123/"+r["id"]+".json")
                self.assertEqual(digest(source), r["sourceSha256"])
                original = strict_json(source.read_bytes())
                current = self.models[r["id"]]
                self.assertEqual(r["removedSightNames"], EXPECTED_REMOVED.get(r["id"], []))
                retained = [e for e in original["elements"] if e["name"] not in r["removedSightNames"]]
                self.assertEqual([e for e in current["elements"] if not e["name"].startswith("w151_")], retained)
                for key, value in original.items():
                    if key not in ("elements", "display", "textures"):
                        self.assertEqual(current[key], value)
                self.assertEqual({k: v for k, v in current["textures"].items() if k != "sight"}, original["textures"])
                self.assertNotIn("display", current)
                self.assertNotIn("parent", current)
                self.assertEqual(len(original["elements"]), r["sourceElementCount"])

    def test_full_assembled_budget_schema_textures(self):
        for r in self.rows:
            with self.subTest(id=r["id"]):
                model = self.models[r["id"]]
                elements = model["elements"]
                self.assertEqual(len(elements), r["elementCount"])
                self.assertLessEqual(len(elements), 1000)
                self.assertEqual(len({e["name"] for e in elements}), len(elements))
                self.assertEqual(len(elements), r["sourceElementCount"]-len(r["removedSightNames"])+len(r["addedSightNames"]))
                self.assertTrue(any("magazine" in e["name"].lower() or "drum" in e["name"].lower() for e in elements))
                self.assertEqual(model["textures"]["sight"], g.SIGHT_TEXTURE)
                for texture in set(model["textures"].values()):
                    ns, name = texture.split(":")
                    self.assertTrue((ROOT / "src/main/resources/assets" / ns / "textures" / (name+".png")).is_file())
                for e in elements:
                    self.assertEqual(len(e["from"]), 3)
                    self.assertTrue(all(math.isfinite(v) for v in e["from"]+e["to"]))
                    self.assertTrue(all(a < b for a, b in zip(e["from"], e["to"])), e["name"])
                    self.assertEqual(set(e["faces"]), {"north", "south", "east", "west", "up", "down"})
                    self.assertNotIn("vertices", e)
                    for f in e["faces"].values():
                        self.assertEqual(len(f["uv"]), 4)
                        self.assertTrue(all(math.isfinite(v) and 0 <= v <= 16 for v in f["uv"]))
                        self.assertIn(f["texture"].removeprefix("#"), model["textures"])

    def test_center_and_dense_clear_aperture_with_rotations(self):
        # Scan all emitted body parts, not only new sight names. Both parallel
        # rays and rays through the declared 0.65m eye catch hidden old lenses.
        for r in self.rows:
            model = self.models[r["id"]]
            self.assertTrue(any(e.get("rotation") for e in model["elements"]))
            for perspective in (False, True):
                for ix in range(-8, 9):
                    for iy in range(-8, 9):
                        dx, dy = ix*.005, iy*.005
                        if dx*dx+dy*dy > .04**2+1e-12:
                            continue
                        with self.subTest(id=r["id"], eye=perspective, xy=(dx, dy)):
                            self.assertEqual(g.blockers(model, r["sightCenter"], dx, dy, perspective, r["eyeToSightMeters"]), [])

    def test_tip_is_visible_below_center_and_front_of_rear(self):
        for r in self.rows:
            with self.subTest(id=r["id"]):
                x, y, z = r["aimingTip"]
                cx, cy, cz = r["sightCenter"]
                self.assertEqual(x, cx)
                self.assertLess(z, cz)
                self.assertLess(y, cy-.04)
                distance = r["eyeToSightMeters"]*16/r["scale"]
                self.assertAlmostEqual((cy-y)*distance/(distance+cz-z), .055, places=6)
                # The line just inside the aiming tip must hit that tip first.
                eye = [cx, cy, cz+distance]
                target = [x, y-.002, z]
                hits = [(e["name"], g.segment_hits(e, eye, target)) for e in self.models[r["id"]]["elements"]]
                self.assertEqual([name for name, hit in hits if hit], ["w151_front_pin_tip"])

    def test_blast_usable_optic_is_in_front_of_eye_and_stock_is_behind_it(self):
        r = next(r for r in self.rows if r["id"] == "blast_furnace")
        model = self.models["blast_furnace"]
        source = strict_json((ROOT / r["source"]).read_bytes())
        names = {e["name"]: e for e in model["elements"]}
        eye_z = r["sightCenter"][2] + r["eyeToSightMeters"]*16/r["scale"]
        # Native view acceptance needs a visible optic, not only a tiny clear ray.
        for e in source["elements"]:
            if e["name"].startswith(("Stock_", "Optic_")):
                self.assertEqual(names[e["name"]], e)
            if e["name"].startswith("Stock_"):
                z_values=[]
                for x in (e["from"][0], e["to"][0]):
                    for y in (e["from"][1], e["to"][1]):
                        for z in (e["from"][2], e["to"][2]):
                            v=[x,y,z];rot=e.get("rotation",{});origin=rot.get("origin",[0,0,0])
                            v=[a-b for a,b in zip(v,origin)]
                            for axis in "xyz":v=g.rotate(v,axis,rot.get(axis,0))
                            z_values.append(v[2]+origin[2])
                self.assertGreater(min(z_values), eye_z+.5, e["name"])
        self.assertLess(names["Optic_hood"]["to"][2], eye_z)
        self.assertEqual(r["removedSightNames"], [])

    def test_claws_original_lens_and_rear_cap_are_detected(self):
        r = next(r for r in self.rows if r["id"] == "claws_of_the_wolf")
        original = strict_json((ROOT / r["source"]).read_bytes())
        for perspective in (False, True):
            self.assertEqual(set(g.blockers(original, r["sightCenter"], perspective=perspective)), {"optic_rear", "optic_lens"})
            # Inject old opacity into the candidate: clearance must fail.
            for name in ("optic_lens", "optic_rear"):
                bad = copy.deepcopy(self.models[r["id"]])
                bad["elements"].append(next(e for e in original["elements"] if e["name"] == name))
                self.assertIn(name, g.blockers(bad, r["sightCenter"], perspective=perspective))

    def test_rotated_slab_crossing_missed_by_unrotated_box(self):
        for rotation in ({"axis": "z", "angle": 90}, {"z": 90}, {"x": 20, "y": 30, "z": 90}):
            e = {"name": "opaque_old_lens", "from": [.8, -.1, -.1], "to": [1.2, .1, .1],
                 "rotation": {"origin": [0, 0, 0], **rotation}}
            # Known transformed box center (Rz Ry Rx applied to [1,0,0]).
            target = [0, math.cos(math.radians(rotation.get("y", 0))), -math.sin(math.radians(rotation.get("y", 0)))]
            self.assertTrue(g.segment_hits(e, [target[0], target[1], 3], [target[0], target[1], -3]))
            plain = {k: v for k, v in e.items() if k != "rotation"}
            self.assertFalse(g.segment_hits(plain, [target[0], target[1], 3], [target[0], target[1], -3]))

    def test_rotation_avoids_unrotated_false_positive_and_handles_rescale(self):
        e = {"from": [-1, -.1, -.1], "to": [1, .1, .1], "rotation": {"origin": [0, 0, 0], "axis": "z", "angle": 90}}
        self.assertFalse(g.segment_hits(e, [.8, 0, 3], [.8, 0, -3]))
        # Rz*Ry*Rx inversion with a nonzero origin and compound angles.
        e["rotation"] = {"origin": [3, 4, 5], "x": 90, "y": 90, "z": 90}
        self.assertEqual([round(v, 7) for v in g.local_point(e, [3, 4, 4])], [4, 4, 5])
        e = {"from": [-1, -.1, -.1], "to": [1, .1, .1], "rotation": {"origin": [0, 0, 0], "axis": "z", "angle": 45, "rescale": True}}
        self.assertTrue(g.segment_hits(e, [.9, .9, 3], [.9, .9, -3]))
        e["rotation"]["rescale"] = False
        self.assertFalse(g.segment_hits(e, [.9, .9, 3], [.9, .9, -3]))

    def test_zero_depth_opaque_card_is_not_ignored(self):
        card = {"from": [-1, -1, 0], "to": [1, 1, 0]}
        self.assertTrue(g.segment_hits(card, [0, 0, 3], [0, 0, -3]))
        self.assertFalse(g.segment_hits(card, [2, 0, 3], [2, 0, -3]))

    def test_reference_photo_reviews_design_and_rip_provenance(self):
        refs = {r["id"]: r for r in strict_json((ROOT / "art/weapons/w31/references.json").read_bytes())}
        for r in self.rows:
            with self.subTest(id=r["id"]):
                ref = r["reference"]
                self.assertEqual(digest(Path(ref["photo"])), ref["photoSha256"])
                self.assertEqual(ref["photoSha256"], refs[r["id"]]["sha256"])
                self.assertEqual(ref["url"], refs[r["id"]]["screenshot"])
                self.assertGreater(len(ref["notes"]), 100)
                for key in ("review", "design", "ripProvenance"):
                    self.assertEqual(digest(ROOT / ref[key]), ref[key+"Sha256"])
                raw = strict_json((ROOT / ref["ripProvenance"]).read_bytes())["raw_input_sha256"]
                self.assertTrue(ref["rawFbxSha256"])
                self.assertEqual(ref["rawFbxSha256"], {p: h for p, h in raw.items() if p.lower().endswith(".fbx")})
                self.assertEqual(digest(g.ASSETS / "textures/item/weapon/w148/sights.png"), r["sightTextureSha256"])

    def test_generator_deterministic_exact_seven_output_scope(self):
        self.assertEqual(g.generate(), self.outputs)
        expected = {g.ASSETS / f"models/weapon_sight_w151/{id}_body.json" for id in IDS}
        expected.add(ROOT / "art/weapons/w151/pulse-sights.json")
        self.assertEqual(set(self.outputs), expected)
        for path, data in self.outputs.items():
            self.assertEqual(path.read_bytes(), data, str(path))
            strict_json(data)

    def test_verify_cli_success_and_mismatch_rejection_without_writes(self):
        command = ["rtk", "proxy", sys.executable, "-B", str(ROOT / "scripts/generate_sight_bodies_w151_pulse.py"), "--verify"]
        result = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        with patch.object(sys, "argv", [str(g.__file__), "--verify"]), patch.object(g, "generate", return_value={ROOT / "art/weapons/w151/pulse-sights.json": b"different\n"}), patch.object(Path, "write_bytes", side_effect=AssertionError("verify wrote")), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                g.main()
            self.assertEqual(error.exception.code, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
