#!/usr/bin/env python3
"""W151 handgun art regressions; stdlib only, no game/build/shared writes.

rtk proxy python3 -B scripts/qa/test_sight_bodies_w151_handguns.py
"""

import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "w151_handgun_generator", ROOT / "scripts/generate_sight_bodies_w151_handguns.py")
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)

# Independent expected assignment/removal set: expanding the generator's deletion
# policy cannot silently make body-preservation tests accept extra deletions.
ASSIGNED = {
    "duke_mk_44": ("hand_cannon", ["Front_sight"]),
    "austringer": ("hand_cannon", []),
    "seventh_seraph_officer_revolver": ("hand_cannon", ["rear_sight_blade"]),
    "allied_demand": ("sidearm", ["front_sight"]),
    "farewell": ("sidearm", ["front_sight_post"]),
    "lonesome": ("sidearm", ["front_sight_blade"]),
}


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def world_vertices(element):
    """Independent forward-matrix oracle; does not call inverse-ray code."""
    rotation = element.get("rotation", {})
    angles = [rotation.get(axis, 0) for axis in "xyz"]
    if "axis" in rotation:
        angles["xyz".index(rotation["axis"])] = rotation.get("angle", 0)
    (cx, sx), (cy, sy), (cz, sz) = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in angles]
    rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    matrix = matmul(matmul(rz, ry), rx)
    pivot = rotation.get("origin", [8, 8, 8])
    vertices = []
    for bits in range(8):
        local = [element["to" if bits & (1 << i) else "from"][i] - pivot[i] for i in range(3)]
        if rotation.get("rescale"):
            scale = 1 / abs(math.cos(math.radians(rotation["angle"])))
            local = [v if axis == rotation["axis"] else v * scale for axis, v in zip("xyz", local)]
        vertices.append(tuple(dot(row, local) + p for row, p in zip(matrix, pivot)))
    return vertices


TRIANGLES = ((0, 2, 3), (0, 3, 1), (4, 5, 7), (4, 7, 6),
             (0, 1, 5), (0, 5, 4), (2, 6, 7), (2, 7, 3),
             (0, 4, 6), (0, 6, 2), (1, 3, 7), (1, 7, 5))


def triangle_hit(vertices, origin, direction):
    """Double-sided Moller-Trumbore against the twelve world-space triangles."""
    for indices in TRIANGLES:
        a, b, c = [vertices[i] for i in indices]
        ab, ac = sub(b, a), sub(c, a)
        p = cross(direction, ac)
        determinant = dot(ab, p)
        if abs(determinant) < 1e-12:
            continue
        tvec = sub(origin, a)
        u = dot(tvec, p) / determinant
        q = cross(tvec, ab)
        v = dot(direction, q) / determinant
        t = dot(ac, q) / determinant
        if u >= -1e-9 and v >= -1e-9 and u + v <= 1 + 1e-9 and t >= 0:
            return True
    return False


# W154 deliberately closer eye and more legible physical tips.
W154_EYE = dict(duke_mk_44=.36, austringer=.35, seventh_seraph_officer_revolver=.36,
                allied_demand=.32, farewell=.38, lonesome=.34)
W154_GAP = dict(duke_mk_44=.085, austringer=.055, seventh_seraph_officer_revolver=.085,
                allied_demand=.070, farewell=.080, lonesome=.085)

class HandgunSightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {r["id"]: r for r in GEN.read(ROOT / GEN.MANIFEST)["weapons"]}
        cls.models = {i: GEN.read(ROOT / GEN.ASSETS / "models" / (r["body"] + ".json")) for i, r in cls.rows.items()}
        cls.sources = {i: GEN.read(ROOT / r["source"]) for i, r in cls.rows.items()}

    def contract(self, weapon_id):
        row = self.rows[weapon_id]
        self.assertEqual(row["family"], ASSIGNED[weapon_id][0])
        self.assertEqual(row["body"], f"weapon_sight_w151/{weapon_id}_body")
        self.assertEqual(row["source"], f"{GEN.ASSETS}/models/weapon_surface_w123/{weapon_id}.json")
        self.assertEqual((row["style"], row["eyeSide"], row["plane"], row["scale"], row["eyeToSightMeters"]),
                         ("iron", "+Z", "XY", 0.9, W154_EYE[weapon_id]))
        x, y, z = row["sightCenter"]
        self.assertEqual(x, 8)
        self.assertGreater(y, 13)
        self.assertEqual(row["forwardPoint"], [x, y, round(z - 2, 6)])
        self.assertGreater(z, row["frontPoint"][2])
        self.assertEqual(row["clearApertureHalfWidth"], 0.025)
        GEN.encode(row)  # Reject NaN/Infinity in the actual manifest too.

    def preservation(self, weapon_id):
        row, source, model = self.rows[weapon_id], self.sources[weapon_id], self.models[weapon_id]
        self.assertEqual(row["sourceSha256"], GEN.sha((ROOT / row["source"]).read_bytes()))
        kept = [e for e in source["elements"] if e["name"] not in ASSIGNED[weapon_id][1]]
        actual_kept = [e for e in model["elements"] if not e["name"].startswith("w151_")]
        self.assertEqual(actual_kept, kept, "Preserve every UV/face/rotation/name/coordinate and the original ordering")
        self.assertEqual({k: v for k, v in model.items() if k != "elements"},
                         {k: v for k, v in source.items() if k not in ("elements", "display")})
        self.assertNotIn("display", model)
        self.assertEqual(row["preservedElementCount"], len(kept))
        self.assertEqual(row["sourceElementCount"], len(source["elements"]))

    def clearance(self, weapon_id):
        row, model = self.rows[weapon_id], self.models[weapon_id]
        self.assertEqual(GEN.aperture_blockers(model, row), [])
        x, y, z = row["sightCenter"]
        eye_z = z + row["eyeToSightMeters"] * 16 / row["scale"]
        # Off-grid rays with a completely independent forward geometry oracle.
        for dx, dy in ((0, 0), (.0193, -.0137), (-.0211, .0179), (.0233, .0221)):
            for origin, direction in (((x + dx, y + dy, eye_z), (0, 0, -1)),
                                      ((x, y, eye_z), (dx / (eye_z - z), dy / (eye_z - z), -1))):
                for element in model["elements"]:
                    vertices = world_vertices(element)
                    self.assertFalse(triangle_hit(vertices, origin, direction), (weapon_id, element["name"], dx, dy))
                    self.assertIsNone(GEN.ray_hit(element, origin, direction), element["name"])

    def aiming_tip(self, weapon_id):
        row, model = self.rows[weapon_id], self.models[weapon_id]
        tip = next(e for e in model["elements"] if e["name"] == row["aimingTip"])
        self.assertNotIn("rotation", tip)
        self.assertAlmostEqual((tip["from"][0] + tip["to"][0]) / 2, 8)
        self.assertAlmostEqual(row["sightCenter"][1] - tip["to"][1], W154_GAP[weapon_id])
        self.assertEqual(row["tipGap"], W154_GAP[weapon_id])
        self.assertAlmostEqual(tip["to"][0] - tip["from"][0], .20 if weapon_id == "austringer" else .18)
        self.assertLess(abs((tip["from"][2] + tip["to"][2]) / 2 - row["frontPoint"][2]), .1)
        x, y, z = row["sightCenter"]
        eye_z = z + row["eyeToSightMeters"] * 16 / row["scale"]
        target = [8, tip["to"][1] - .008, tip["to"][2]]
        direction = [(target[0] - x) / (eye_z - target[2]), (target[1] - y) / (eye_z - target[2]), -1]
        hits = sorted((t, e["name"]) for e in model["elements"]
                      if (t := GEN.ray_hit(e, (x, y, eye_z), direction)) is not None)
        self.assertTrue(hits)
        self.assertEqual(hits[0][1], row["aimingTip"], "Aiming tip must be visible through the rear notch")

    def references(self, weapon_id):
        row = self.rows[weapon_id]
        ref = row["reference"]
        photo = Path(ref["photo"])
        self.assertEqual(photo, Path("/tmp/destiny-weapons-w31/references") / f"{weapon_id}.jpg")
        self.assertEqual(GEN.sha(photo.read_bytes()), ref["photoSha256"])
        catalog = next(r for r in GEN.read(ROOT / ref["catalog"]) if r["id"] == weapon_id)
        self.assertEqual((ref["photoSha256"], ref["url"]), (catalog["sha256"], catalog["screenshot"]))
        for kind in ("design", "review"):
            self.assertEqual(ref[kind], f"art/weapons/w123/{weapon_id}/{'design.json' if kind == 'design' else 'review.md'}")
            self.assertEqual(GEN.sha((ROOT / ref[kind]).read_bytes()), ref[kind + "Sha256"])
        design = GEN.read(ROOT / ref["design"])
        self.assertEqual(ref["rawSourceFiles"], design["source"]["source_files"])
        self.assertEqual(ref["sourceTriangles"], design["source"]["source_triangles"])
        self.assertTrue(ref["rawSourceFiles"])
        self.assertGreaterEqual(len(row["referenceNotes"]), 2)
        self.assertIn("approximation", ref["limitation"])

    def removals(self, weapon_id):
        row, model, source = self.rows[weapon_id], self.models[weapon_id], self.sources[weapon_id]
        expected = ASSIGNED[weapon_id][1]
        self.assertEqual(row["removedSightNames"], expected)
        self.assertEqual(GEN.aperture_blockers(source, row), sorted(expected),
                         "Every deletion must be a measured old sight obstruction; no body deletion")
        self.assertGreater(len(row["removalReason"]), 60)
        actual_names = {e["name"] for e in model["elements"]}
        for name in expected:
            self.assertNotIn(name, actual_names)
        if weapon_id == "austringer":
            self.assertEqual(next(e for e in source["elements"] if e["name"] == "Optic_lens"),
                             next(e for e in model["elements"] if e["name"] == "Optic_lens"))

    def art_and_budget(self, weapon_id):
        row, source, model = self.rows[weapon_id], self.sources[weapon_id], self.models[weapon_id]
        added = [e for e in model["elements"] if e["name"].startswith("w151_")]
        self.assertEqual(row["addedSightNames"], [e["name"] for e in added])
        self.assertGreaterEqual(len(added), 2)
        self.assertLessEqual(len(added), 6)
        self.assertEqual(row["elementCount"], len(model["elements"]))
        self.assertEqual(row["elementCount"], len(source["elements"]) - len(ASSIGNED[weapon_id][1]) + len(added))
        self.assertLessEqual(row["elementCount"], 1000)  # Full assembly, including Duke cylinder/yoke.
        self.assertEqual(len({e["name"] for e in model["elements"]}), len(model["elements"]))
        by_name = {e["name"]: e for e in source["elements"]}
        for element in added:
            self.assertEqual(element["faces"], by_name[row["sightUvDonors"][element["name"]]]["faces"])
            self.assertEqual(set(element["faces"]), {"up", "down", "north", "south", "east", "west"})
            self.assertTrue(all(a < b for a, b in zip(element["from"], element["to"])))
            self.assertNotIn("vertices", element)
            self.assertNotIn("triangles", element)
            for face in element["faces"].values():
                self.assertEqual(face["texture"], "#0")
                self.assertTrue(all(0 <= value <= 16 for value in face["uv"]))
        self.assertEqual(model["textures"], source["textures"])
        for value in model["textures"].values():
            self.assertTrue((ROOT / GEN.ASSETS / "textures" / (value.removeprefix("destiny:") + ".png")).is_file())

    def test_deterministic_outputs_and_readonly_inputs(self):
        paths = {ROOT / row["source"] for row in self.rows.values()}
        paths.add(ROOT / "art/weapons/w31/references.json")
        for weapon_id, (family, _) in ASSIGNED.items():
            for namespace in ("models", "items"):
                base = ROOT / GEN.ASSETS / namespace
                paths.update(base.glob(f"weapon*/{weapon_id}*.json"))
                paths.update((base / "weapon" / family).glob(f"{weapon_id}*.json"))
            paths.update((ROOT / f"art/weapons/w123/{weapon_id}").glob("*.json"))
            paths.add(ROOT / f"art/weapons/w123/{weapon_id}/review.md")
        before = {p: GEN.sha(p.read_bytes()) for p in paths}
        first, second = GEN.build_outputs(), GEN.build_outputs()
        self.assertEqual(first, second)
        self.assertEqual(GEN.output_mismatches(first), [])
        self.assertEqual(before, {p: GEN.sha(p.read_bytes()) for p in paths})

    def test_verify_detects_changed_and_missing_output(self):
        path = ROOT / GEN.MODEL_DIR / "duke_mk_44_body.json"
        missing = ROOT / GEN.MODEL_DIR / "intentionally_absent_test_model.json"
        self.assertFalse(missing.exists())
        self.assertEqual(GEN.output_mismatches({path: path.read_bytes() + b"\n", missing: b"{}"}), [path, missing])

    def test_reject_nonfinite_json(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                GEN.encode({"bad": value})

    def test_opaque_old_lens_cannot_hide_by_name_or_rotation(self):
        row = self.rows["austringer"]
        model = copy.deepcopy(self.models["austringer"])
        lens = copy.deepcopy(next(e for e in model["elements"] if e["name"] == "Optic_lens"))
        x, y, z = row["sightCenter"]
        lens["from"], lens["to"] = [x - .3, y - .3, z - .04], [x + .3, y + .3, z + .04]
        lens["rotation"] = dict(origin=[x, y, z], x=37, y=29, z=18)
        model["elements"].append(lens)
        self.assertIn("Optic_lens", GEN.aperture_blockers(model, row))

    def test_classic_rotation_detects_off_axis_hit_and_false_positive(self):
        lens = {"from": [-.5, -.5, 1.95], "to": [.5, .5, 2.05],
                "rotation": dict(origin=[0, 0, 0], axis="y", angle=90)}
        # Ignoring rotation would invert both answers.
        self.assertIsNotNone(GEN.ray_hit(lens, [2, 0, 10]))
        self.assertIsNone(GEN.ray_hit(lens, [0, 0, 10]))
        self.assertTrue(triangle_hit(world_vertices(lens), [2, 0, 10], [0, 0, -1]))
        lens["rotation"].update(angle=45, rescale=True)
        for origin in ([1.3, .1, 10], [3, .1, 10]):
            self.assertEqual(GEN.ray_hit(lens, origin) is not None,
                             triangle_hit(world_vertices(lens), origin, [0, 0, -1]))

    def test_compound_native_rotation_and_noncentral_pivot(self):
        lens = {"from": [1.7, 2.3, 4.1], "to": [2.9, 3.1, 4.16],
                "rotation": dict(origin=[1, 2, 3], x=27, y=43, z=19)}
        vertices = world_vertices(lens)
        center = [sum(v[i] for v in vertices) / 8 for i in range(3)]
        origin = [center[0], center[1], center[2] + 10]
        self.assertIsNotNone(GEN.ray_hit(lens, origin))
        self.assertTrue(triangle_hit(vertices, origin, [0, 0, -1]))
        for dx in (-1.1, -.31, .23, .9):
            origin = [center[0] + dx, center[1] + .07, center[2] + 10]
            self.assertEqual(GEN.ray_hit(lens, origin) is not None, triangle_hit(vertices, origin, [0, 0, -1]))

    def test_zero_depth_card_is_an_obstruction(self):
        card = {"from": [7.8, 13.8, 4], "to": [8.2, 14.2, 4],
                "rotation": dict(origin=[8, 14, 4], axis="y", angle=22.5)}
        self.assertIsNotNone(GEN.ray_hit(card, [8, 14, 20]))
        self.assertIsNone(GEN.ray_hit(card, [8.7, 14, 20]))

    def test_exact_assignment_output_scope_and_distinct_profiles(self):
        self.assertEqual(set(self.rows), set(ASSIGNED))
        outputs = GEN.build_outputs()
        expected = {ROOT / GEN.MANIFEST} | {ROOT / GEN.MODEL_DIR / f"{i}_body.json" for i in ASSIGNED}
        self.assertEqual(set(outputs), expected)
        self.assertEqual(len({r["profile"] for r in self.rows.values()}), 6)
        signatures = set()
        for model in self.models.values():
            additions = [{k: e[k] for k in ("from", "to", "rotation") if k in e}
                         for e in model["elements"] if e["name"].startswith("w151_")]
            signatures.add(json.dumps(additions, sort_keys=True))
        self.assertEqual(len(signatures), 6)


# Seven individually reported tests for each of the six required weapons.
for _weapon_id in ASSIGNED:
    for _check in ("contract", "preservation", "clearance", "aiming_tip", "references", "removals", "art_and_budget"):
        def _test(self, weapon_id=_weapon_id, check=_check):
            getattr(self, check)(weapon_id)
        setattr(HandgunSightTests, f"test_{_weapon_id}_{_check}", _test)


if __name__ == "__main__":
    unittest.main(verbosity=2)
