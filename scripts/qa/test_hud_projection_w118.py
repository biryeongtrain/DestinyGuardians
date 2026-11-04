#!/usr/bin/env python3
"""Python fixtures consumed independently by HudProjectionW118Test's engine oracle.

--write-fixtures refreshes only the owned fixture; --verify-fixtures is read-only.
The pinned W118 baseline masks are preserved across refreshes.
"""
import argparse
import copy
import importlib.util
import itertools
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("hud_w112", ROOT / "scripts/build_weapon_hud_w112.py")
hud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hud)
FIXTURE = ROOT / "src/test/resources/weapon_hud_w118/rotation-fixtures.json"


def fixtures():
    cases = []

    def add(name, element, **source):
        points = hud.corners(element)
        cases.append(dict(name=name, element=element, python_corners=points,
                          gun_yz=[hud.project(p, "gun") for p in points],
                          melee_yz=[hud.project(p, "sword") for p in points], **source))

    lo, hi, origin = [-2, 3, 5], [7, 13, 17], [1, 8, 9]
    add("identity", hud.cube(lo, hi))
    for angles in ([90, 90, 90], [17.3, -61.2, 134.7], [-31, 52, -77],
                   [23, 41, 0], [23, 0, -37], [0, 41, -37],
                   [90, 0, 0], [0, -90, 0], [0, 0, 90]):
        add("native_" + "_".join(map(str, angles)), hud.cube(lo, hi,
            dict(origin=origin, **dict(zip("xyz", angles)), rescale=False)))
    for axis, angle, native in itertools.product("xyz", (-45, -22.5, 22.5, 45), (False, True)):
        rotation = dict(origin=origin, rescale=True)
        rotation.update({axis: angle} if native else dict(axis=axis, angle=angle))
        add(f"rescale_{axis}_{angle}_{'native' if native else 'axis'}", hud.cube(lo, hi, rotation))
    for row in hud.catalog():
        path = hud.canonical_source_path(row)
        source = (ROOT / path).read_bytes()
        for index, element in enumerate(json.loads(source)["elements"]):
            if element.get("rotation"):
                add(f"{row['id']}:{index}", element, source_model=path.as_posix(),
                    source_sha256=hud.sha(source), source_element=index)
    manifest = hud.read_json(hud.HUD / "manifest.json")
    baseline = (json.loads(FIXTURE.read_text())["baseline_alpha_sha256"] if FIXTURE.exists()
                else {w["id"]: w["alpha_sha256"] for w in manifest["weapons"]})
    return dict(schema=1, engine="Minecraft 26.3 CuboidModel element parser + FaceBakery.rotateVertexBy",
                matrix="Rz*Ry*Rx; X then Y then Z around declared origin; model units",
                tolerance_model_units=0.00005, baseline_alpha_sha256=baseline, cases=cases)


def wrong_order(point, angles):
    """Historical Rx*Ry*Rz kept as a negative control, never production."""
    x, y, z = point
    a, b, c = map(math.radians, angles)
    x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    return x, y, z


class HudProjectionW118Test(unittest.TestCase):
    def test_historical_fixture_contains_all_71_canonical_rotations(self):
        data = json.loads(FIXTURE.read_text())
        self.assertEqual(hud.json_bytes(fixtures()), FIXTURE.read_bytes())
        product = [c for c in data["cases"] if "source_model" in c]
        self.assertEqual(71, len(product))
        self.assertEqual({"ace_of_spades", "izanagis_burden"}, {c["name"].split(":")[0] for c in product})
        self.assertEqual(24, sum(c["name"].startswith("rescale_") for c in data["cases"]))

    def test_wrong_order_is_rejected_for_asymmetric_multi_axis_element(self):
        element = hud.cube([-2, 3, 5], [7, 13, 17],
                           dict(origin=[1, 8, 9], x=17.3, y=-61.2, z=134.7))
        origin = element["rotation"]["origin"]
        angles = [element["rotation"][a] for a in "xyz"]
        wrong = [tuple(o + v for o, v in zip(origin, wrong_order(
            [v - o for v, o in zip(p, origin)], angles)))
            for p in itertools.product(*zip(element["from"], element["to"]))]
        self.assertGreater(max(math.dist(a, b) for a, b in zip(hud.corners(element), wrong)), 10)
        # An asymmetric multi-axis fixture must also expose the error in actual
        # raster coverage. Current product rotations are all single-axis, so
        # demanding changed product pixels would assert an invented art delta.
        model = {"elements": [element]}
        correct = hud.render(model, "gun")[1]["alpha_sha256"]
        rotate = hud.rotate
        try:
            hud.rotate = wrong_order
            incorrect = hud.render(model, "gun")[1]["alpha_sha256"]
        finally:
            hud.rotate = rotate
        self.assertNotEqual(correct, incorrect)

    def test_24_single_axis_rescale_cases_keep_axis_and_origin(self):
        for case in fixtures()["cases"]:
            if not case["name"].startswith("rescale_"):
                continue
            e = case["element"]
            r = e["rotation"]
            axis = "xyz".index(r.get("axis", next((a for a in "xyz" if a in r), "x")))
            angle = r.get("angle", r.get("xyz"[axis]))
            plain = copy.deepcopy(e)
            plain["rotation"]["rescale"] = False
            for a, b in zip(hud.corners(e), hud.corners(plain)):
                for i in range(3):
                    factor = 1 if i == axis else 1 / math.cos(math.radians(angle))
                    self.assertAlmostEqual(a[i], r["origin"][i] + (b[i] - r["origin"][i]) * factor)

    def test_unsupported_multi_axis_rescale_still_fails(self):
        with self.assertRaisesRegex(ValueError, "Multi-axis rescale"):
            hud.corners(hud.cube([0, 0, 0], [1, 2, 3],
                                dict(origin=[0, 0, 0], x=22.5, y=45, rescale=True)))

    def test_particle_alias_is_only_transport_extension_for_all_65(self):
        template = hud.read_json(hud.ASSETS / "models/gui/hud/ammo_hand_cannon.json")
        for row in hud.catalog():
            item, model = hud.transport(row["id"])
            expected = copy.deepcopy(template)
            texture = "destiny:item/hud/ammo_weapon_w112_" + row["id"]
            expected["textures"].update(layer0=texture, particle="#layer0")
            self.assertEqual(expected, model)
            expected_item = hud.read_json(hud.ASSETS / "items/gui/hud/ammo_hand_cannon.json")
            expected_item["model"]["model"] = "destiny:gui/hud/ammo_weapon_w112_" + row["id"]
            self.assertEqual(expected_item, item)
            self.assertTrue((ROOT / hud.ASSETS / "textures" / (texture.split(":")[1] + ".png")).is_file())

    def test_historical_65_canonical_masks_still_match_pinned_baseline(self):
        baseline = json.loads(FIXTURE.read_text())["baseline_alpha_sha256"]
        hashes, changed = set(), set()
        canonical_records = []
        for catalog_row in hud.catalog():
            path = hud.canonical_source_path(catalog_row)
            source = (ROOT / path).read_bytes()
            stats = hud.render(json.loads(source), catalog_row["family"])[1]
            canonical_records.append(dict(id=catalog_row["id"], source_model=path.as_posix(),
                                          source_sha256=hud.sha(source), **stats))
        for row in canonical_records:
            self.assertNotIn(row["alpha_sha256"], hashes)
            hashes.add(row["alpha_sha256"])
            self.assertEqual(hud.sha((ROOT / row["source_model"]).read_bytes()), row["source_sha256"])
            if row["alpha_sha256"] != baseline[row["id"]]:
                changed.add(row["id"])
        self.assertEqual(65, len(hashes))
        product = [c for c in fixtures()["cases"] if "source_model" in c]
        self.assertEqual(71, len(product))
        for case in product:
            self.assertEqual(1, sum(bool(case["element"]["rotation"].get(a, 0)) for a in "xyz"))
        self.assertEqual(set(), changed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-fixtures", action="store_true")
    parser.add_argument("--verify-fixtures", action="store_true")
    args = parser.parse_args()
    if args.write_fixtures:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_bytes(hud.json_bytes(fixtures()))
        print("W118 wrote rotation fixtures")
    elif args.verify_fixtures:
        hud.require(FIXTURE.read_bytes() == hud.json_bytes(fixtures()), "Stale W118 fixtures")
        print("W118 verified rotation fixtures")
    else:
        unittest.main(argv=[__file__], verbosity=2)
