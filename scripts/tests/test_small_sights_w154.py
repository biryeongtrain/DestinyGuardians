#!/usr/bin/env python3
"""W154 offline art tests. Run with bundled Python -B; --preview emits PNG data.

No game, wrappers, Gradle, source writes or shared application operations.
The forward-matrix/triangle oracle is reused from the sealed W151 test module;
none of its obsolete .65m/.055/.13 assertions are invoked.
"""
import base64
import copy
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import runpy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "src/main/resources/assets/destiny"
REPORT = ROOT / "art/weapons/w154/small-sights.json"
EXPECTED = {
    "duke_mk_44": (.36, .18, .085, ["Front_sight"]),
    "austringer": (.35, .20, .055, []),
    "seventh_seraph_officer_revolver": (.36, .18, .085, ["rear_sight_blade"]),
    "allied_demand": (.32, .18, .070, ["front_sight"]),
    "farewell": (.38, .18, .080, ["front_sight_post"]),
    "lonesome": (.34, .18, .085, ["front_sight_blade"]),
    "dead_man_walking_xx7463": (.36, .18, .085, []),
    "high_albedo": (.34, .18, .085, []),
    "brass_attacks": (.34, .18, .085, []),
}


def load_generator(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


W151 = load_generator("w154_handguns", "generate_sight_bodies_w151_handguns.py")
W153 = load_generator("w154_sidearms", "generate_sight_bodies_w153_sidearms_heavy.py")
ORACLE = runpy.run_path(str(ROOT / "scripts/qa/test_sight_bodies_w151_handguns.py"))
vertices = ORACLE["world_vertices"]
triangle_hit = ORACLE["triangle_hit"]


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows():
    result = {}
    for p in (W151.MANIFEST, W153.MANIFEST):
        result.update({r["id"]: r for r in read(ROOT / p)["weapons"] if r["id"] in EXPECTED})
    return result


def eye_relative(point, row):
    """Final ADS camera coordinates in meters: X right, Y up, depth forward.

    Wrapper translation cancels the supplied X/Y sight center; positive source
    Z is toward the eye. Check all rotated corners, including low grip heels.
    """
    x, y, z = row["sightCenter"]
    s = row["scale"] / 16
    return ((point[0] - x) * s, (point[1] - y) * s,
            row["eyeToSightMeters"] - (point[2] - z) * s)


def camera_metrics(model, row):
    points = [(eye_relative(p, row), e["name"])
              for e in model["elements"] for p in vertices(e)]
    closest, name = min(points, key=lambda item: item[0][2])
    return dict(nearestDepthMeters=round(closest[2], 9), nearestElement=name,
                nearestCornerEyeRelativeMeters=[round(v, 9) for v in closest],
                boundsEyeRelativeMeters=[[round(min(p[i] for p, _ in points), 9),
                                           round(max(p[i] for p, _ in points), 9)]
                                          for i in range(3)],
                minimumRequiredDepthMeters=.08)


def tip_for(model, row):
    name = row.get("aimingTipName", row["aimingTip"])
    return next(e for e in model["elements"] if e["name"] == name)


def projection(tip, row):
    depth = eye_relative([8, row["sightCenter"][1], tip["to"][2]], row)[2]
    return dict(widthOverDepth=(tip["to"][0]-tip["from"][0])*row["scale"]/16/depth,
                topGapOverDepth=(row["sightCenter"][1]-tip["to"][1])*row["scale"]/16/depth)


class SmallSights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = rows()
        cls.report = read(REPORT)
        cls.records = {r["id"]: r for r in cls.report["weapons"]}
        cls.models = {i: read(A / "models" / (r["body"] + ".json")) for i, r in cls.rows.items()}

    def contract(self, weapon):
        row, expected = self.rows[weapon], EXPECTED[weapon]
        self.assertEqual(row["eyeToSightMeters"], expected[0])
        self.assertEqual((row["eyeSide"], row["plane"], row["scale"]), ("+Z", "XY", .9))
        self.assertEqual(row["sightCenter"], self.records[weapon]["before"]["sightCenter"])
        self.assertEqual(row["removedSightNames"], expected[3])
        self.assertLess(row["eyeToSightMeters"], self.records[weapon]["before"]["eyeToSightMeters"])

    def preserve(self, weapon):
        row, model = self.rows[weapon], self.models[weapon]
        source = read(ROOT / row["source"])
        retained = [e for e in source["elements"] if e["name"] not in EXPECTED[weapon][3]]
        self.assertEqual([e for e in model["elements"] if e["name"] not in row["addedSightNames"]], retained)
        self.assertEqual(sha(ROOT / row["source"]), row["sourceSha256"])
        self.assertEqual({k: v for k, v in model.items() if k not in ("elements", "textures")},
                         {k: v for k, v in source.items() if k not in ("elements", "textures", "display")})
        for k, v in source["textures"].items():
            self.assertEqual(model["textures"][k], v)

    def camera(self, weapon):
        model, row = self.models[weapon], self.rows[weapon]
        metrics = camera_metrics(model, row)
        self.assertGreaterEqual(metrics["nearestDepthMeters"], .08, metrics)
        self.assertEqual(metrics, self.records[weapon]["after"]["camera"])

    def readable_tip(self, weapon):
        model, row = self.models[weapon], self.rows[weapon]
        tip = tip_for(model, row)
        self.assertAlmostEqual((tip["from"][0]+tip["to"][0])/2, row["sightCenter"][0])
        self.assertAlmostEqual(tip["to"][0]-tip["from"][0], EXPECTED[weapon][1])
        self.assertAlmostEqual(row["sightCenter"][1]-tip["to"][1], EXPECTED[weapon][2])
        new = projection(tip, row)
        before = self.records[weapon]["before"]
        old = projection(before["tip"], dict(row, eyeToSightMeters=before["eyeToSightMeters"]))
        self.assertGreater(new["widthOverDepth"] / old["widthOverDepth"], 1.7)
        self.assertLess(new["topGapOverDepth"], .006)
        eye_z = row["sightCenter"][2] + row["eyeToSightMeters"]*16/row["scale"]
        origin = [*row["sightCenter"][:2], eye_z]
        target = [8, tip["to"][1]-.008, tip["to"][2]]
        delta = [t-o for t, o in zip(target, origin)]
        hits = sorted((t, e["name"]) for e in model["elements"]
                      if (t := W151.ray_hit(e, origin, delta)) is not None)
        self.assertTrue(hits)
        self.assertEqual(hits[0][1], tip["name"], hits[:4])

    def aperture(self, weapon):
        model, row = self.models[weapon], self.rows[weapon]
        x, y, z = row["sightCenter"]
        eye_z = z + row["eyeToSightMeters"]*16/row["scale"]
        # Independent forward triangle checks, including asymmetric off-grid
        # samples; no alpha or name exemptions for original optics or chassis.
        offsets = [(0, 0), (.0193, -.0137), (-.0211, .0179), (.0233, .0221)]
        if weapon in W151.WEAPONS:
            self.assertEqual(row["clearApertureHalfWidth"], .025)
            self.assertEqual(W151.aperture_blockers(model, row), [])
        else:
            self.assertEqual(W153.channel_hits(model, row), [])
            self.assertEqual(W153.tip_blockers(model, row), [])
            self.assertEqual(W153.foreground_blockers(model, row), {})
            self.assertGreaterEqual(W153.aperture_fraction(model, row), .60)
            offsets += [(ix*.02, iy*.0175) for ix in range(-4, 5) for iy in range(5)]
        for dx, dy in offsets:
            origin = [x, y, eye_z]
            direction = [dx/(eye_z-z), dy/(eye_z-z), -1]
            for e in model["elements"]:
                self.assertFalse(triangle_hit(vertices(e), origin, direction), (weapon, e["name"], dx, dy))

    def schema_and_references(self, weapon):
        from PIL import Image
        row, model, record = self.rows[weapon], self.models[weapon], self.records[weapon]
        self.assertLessEqual(len(model["elements"]), 1000)
        self.assertEqual(len(model["elements"]), row["elementCount"])
        self.assertEqual(len({e["name"] for e in model["elements"]}), len(model["elements"]))
        for e in model["elements"]:
            self.assertTrue(all(math.isfinite(a) and math.isfinite(b) and a<b for a,b in zip(e["from"], e["to"])))
            self.assertNotIn("vertices", e)
            self.assertNotIn("triangles", e)
            self.assertEqual(set(e["faces"]), set(W153.FACES))
            for f in e["faces"].values():
                self.assertIn(f["texture"][1:], model["textures"])
                self.assertTrue(all(math.isfinite(v) and 0<=v<=16 for v in f["uv"]))
        for texture in model["textures"].values():
            with Image.open(A / "textures" / (texture.split(":")[1]+".png")) as image:
                image.verify()
        self.assertEqual(sha(record["referencePhoto"]), row["reference"]["photoSha256"])
        self.assertEqual(sha(record["sealedScreenshot"]), record["sealedScreenshotSha256"])

    def test_assignment_and_non_small_w153_untouched(self):
        self.assertEqual(set(self.rows), set(EXPECTED))
        current = {r["id"]: r for r in read(ROOT / W153.MANIFEST)["weapons"]}
        for entry in self.report["preservedW153Rows"]:
            if entry["id"] in ("fixed_odds", "retrofit_escapade"):
                # Master integration deliberately replaces the MG feed/atlas.
                # Preserve its independent sight design, not obsolete source hashes.
                for key in ("id", "family", "body", "sightCenter", "forwardPoint",
                            "scale", "eyeToSightMeters", "style", "removedSightNames",
                            "addedSightNames", "aimingTip"):
                    self.assertEqual(current[entry["id"]][key], entry["row"][key])
                body = W153.ASSETS / "models" / (entry["row"]["body"]+".json")
                self.assertEqual((ROOT/body).read_bytes(), W153.generate()[body])
            else:
                self.assertEqual(current[entry["id"]], entry["row"])
                self.assertEqual(sha(A / "models" / (entry["row"]["body"]+".json")), entry["bodySha256"])

    def test_both_generators_reproduce_without_writes(self):
        outputs = W151.build_outputs()
        outputs.update({ROOT/p: b for p, b in W153.generate().items()})
        before = {p: (sha(p), p.stat().st_mtime_ns) for p in outputs}
        for p, data in outputs.items():
            self.assertEqual(p.read_bytes(), data, p)
        self.assertEqual(before, {p: (sha(p), p.stat().st_mtime_ns) for p in outputs})

    def test_near_plane_guard_detects_rotated_grip_regression(self):
        row = self.rows["duke_mk_44"]
        model = self.models["duke_mk_44"]
        self.assertLess(camera_metrics(model, dict(row, eyeToSightMeters=.30))["nearestDepthMeters"], .08)
        self.assertLess(camera_metrics(model, dict(row, eyeToSightMeters=.20))["nearestDepthMeters"], 0)

    def test_opaque_center_obstruction_is_rejected(self):
        for weapon in ("duke_mk_44", "brass_attacks"):
            row = self.rows[weapon]
            model = copy.deepcopy(self.models[weapon])
            x, y, z = row["sightCenter"]
            model["elements"].append(dict(name="regression_opaque_plate", **{
                "from": [x-.5, y-.5, z], "to": [x+.5, y+.5, z+.1]}))
            blockers = (W151.aperture_blockers(model, row) if weapon in W151.WEAPONS
                        else W153.channel_hits(model, row))
            self.assertIn("regression_opaque_plate", blockers)


for _weapon in EXPECTED:
    for _check in ("contract", "preserve", "camera", "readable_tip", "aperture", "schema_and_references"):
        def _test(self, weapon=_weapon, check=_check):
            getattr(self, check)(weapon)
        setattr(SmallSights, f"test_{_weapon}_{_check}", _test)


def preview():
    """Eye projection of current solids, not a native rendering or acceptance.

    Side-by-side previous/new sight size. Flat shaded forward triangles use a
    depth buffer, including rotations and hidden rear chassis. No disk output.
    """
    import numpy as np
    from PIL import Image, ImageDraw
    records = {r["id"]: r for r in read(REPORT)["weapons"]}
    sheet = Image.new("RGB", (840, 9*210), "#202936")
    draw = ImageDraw.Draw(sheet)
    for index, (weapon, row) in enumerate(rows().items()):
        model = read(A / "models" / (row["body"]+".json"))
        for column in (0, 1):
            active = copy.deepcopy(model)
            r = dict(row)
            if column == 0:
                r["eyeToSightMeters"] = records[weapon]["before"]["eyeToSightMeters"]
                # Only original tip substituted; added W154 rear shoulders
                # removed to represent the actual prior sight construction.
                old_tip = records[weapon]["before"]["tip"]
                active["elements"] = [old_tip if e["name"]==old_tip["name"] else e
                                      for e in active["elements"] if not e["name"].startswith("w153_rear_")]
            width, height, focal = 420, 180, 600.
            pixels = np.full((height, width, 3), [170, 198, 229], dtype=np.uint8)
            depth = np.full((height, width), np.inf)
            for e in active["elements"]:
                v = np.array([eye_relative(p, r) for p in vertices(e)])
                screen = np.column_stack((width/2+focal*v[:,0]/v[:,2], 78-focal*v[:,1]/v[:,2]))
                color = [238, 212, 140] if e["name"]==tip_for(active, r)["name"] else ([84, 108, 122] if "sight" in e["name"] or e["name"].startswith(("w151_", "w153_rear_")) else [60, 70, 78])
                for indices in ORACLE["TRIANGLES"]:
                    pts = screen[list(indices)]
                    lo = np.maximum(np.floor(pts.min(axis=0)).astype(int), [0, 0])
                    hi = np.minimum(np.ceil(pts.max(axis=0)).astype(int), [width-1, height-1])
                    if np.any(lo>hi): continue
                    p, q, t = pts
                    den = (q[1]-t[1])*(p[0]-t[0])+(t[0]-q[0])*(p[1]-t[1])
                    if abs(den)<1e-10: continue
                    xx, yy = np.meshgrid(np.arange(lo[0], hi[0]+1)+.5, np.arange(lo[1], hi[1]+1)+.5)
                    a = ((q[1]-t[1])*(xx-t[0])+(t[0]-q[0])*(yy-t[1]))/den
                    b = ((t[1]-p[1])*(xx-t[0])+(p[0]-t[0])*(yy-t[1]))/den
                    c = 1-a-b
                    reciprocal = a/v[indices[0],2]+b/v[indices[1],2]+c/v[indices[2],2]
                    zz = np.divide(1., reciprocal, out=np.full_like(reciprocal, np.inf),
                                   where=np.abs(reciprocal)>1e-12)
                    section = np.s_[lo[1]:hi[1]+1, lo[0]:hi[0]+1]
                    mask = (a>=0)&(b>=0)&(c>=0)&(zz<depth[section])
                    depth[section][mask]=zz[mask]
                    pixels[section][mask]=color
            sheet.paste(Image.fromarray(pixels), (column*420,index*210+25))
            draw.text((column*420+8,index*210+7), f"{weapon}: {'before' if column==0 else 'W154'} {r['eyeToSightMeters']:.2f}m", fill="white")
    data = io.BytesIO()
    sheet.save(data, format="PNG")
    print("data:image/png;base64,"+base64.b64encode(data.getvalue()).decode())


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview()
    else:
        unittest.main(verbosity=2)
