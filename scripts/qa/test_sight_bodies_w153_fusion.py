#!/usr/bin/env python3
"""W153 targeted product regressions: preserved source, usable sights and no writes."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("w153_fusion", ROOT / "scripts/generate_sight_bodies_w153_fusion.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
IDS = ("erentil_fr4", "hollow_words", "dream_breaker", "null_composure", "coriolis_force")
COUNTS = (137, 98, 187, 93, 106)
EYES = (.48, .60, .55, .42, .32)
CENTERS = ([8, 14.6, 2.815], [8, 14.48, 5.56], [8, 13.62, 3.79], [8, 14.3, 1.57], [8, 15.3, -.2])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict(data):
    def reject(value):
        raise ValueError(value)
    return json.loads(data, parse_constant=reject)


class FusionSightsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = g.generate()
        cls.rows = strict((ROOT / g.MANIFEST).read_bytes())["weapons"]
        cls.models = {r["id"]: strict((ROOT / g.ASSETS / ("models/"+r["body"]+".json")).read_bytes()) for r in cls.rows}
        cls.sources = {r["id"]: strict((ROOT/r["source"]).read_bytes()) for r in cls.rows}

    def test_w151_row_contract_and_varied_eye_relief(self):
        self.assertEqual(tuple(r["id"] for r in self.rows), IDS)
        self.assertEqual(len({r["style"] for r in self.rows}), 5)
        for r, count, relief, center in zip(self.rows, COUNTS, EYES, CENTERS):
            with self.subTest(id=r["id"]):
                self.assertEqual(r["family"], "fusion_rifle")
                self.assertEqual(r["body"], "weapon_sight_w153/"+r["id"]+"_body")
                self.assertEqual(r["sightCenter"], center)
                self.assertEqual(r["forwardPoint"], [center[0], center[1], center[2]-2])
                self.assertEqual((r["eyeSide"], r["plane"], r["scale"]), ("+Z", "XY", .9))
                self.assertEqual(r["eyeToSightMeters"], relief)
                self.assertEqual(r["elementCount"], count)

    def test_exact_owned_generator_outputs_and_determinism(self):
        expected = {g.ASSETS / f"models/weapon_sight_w153/{id}_body.json" for id in IDS} | {g.MANIFEST}
        self.assertEqual(set(self.outputs), expected)
        self.assertEqual(g.generate(), self.outputs)
        for p, data in self.outputs.items():
            self.assertIsInstance(data, bytes)
            self.assertEqual((ROOT/p).read_bytes(), data)
            self.assertTrue(data.endswith(b"\n"))
            strict(data)

    def test_source_geometry_uvs_rotations_and_metadata_preserved(self):
        for row in self.rows:
            with self.subTest(id=row["id"]):
                original, model = self.sources[row["id"]], self.models[row["id"]]
                removed = ["front_sight_post"] if row["id"] == "dream_breaker" else []
                self.assertEqual(row["removedSightNames"], removed)
                self.assertEqual(row["source"], f"src/main/resources/assets/destiny/models/weapon_surface_w123/{row['id']}.json")
                self.assertEqual(digest(ROOT/row["source"]), row["sourceSha256"])
                self.assertEqual([e for e in model["elements"] if not e["name"].startswith("w153_")],
                                 [e for e in original["elements"] if e["name"] not in removed])
                self.assertNotIn("display", model)
                self.assertNotIn("parent", model)
                for k, v in original.items():
                    if k not in ("elements", "display", "textures"):
                        self.assertEqual(model[k], v)
                self.assertEqual({k:v for k,v in model["textures"].items() if k != "sight"}, original["textures"])
                for name in row["retainedSightNames"]:
                    self.assertEqual(next(e for e in model["elements"] if e["name"] == name),
                                     next(e for e in original["elements"] if e["name"] == name))

    def test_seated_cartridge_once_no_companion_and_assembled_budget(self):
        for r in self.rows:
            with self.subTest(id=r["id"]):
                model, source = self.models[r["id"]], self.sources[r["id"]]
                names = [e["name"] for e in model["elements"]]
                self.assertEqual(len(set(names)), len(names))
                self.assertEqual(len(names), r["assemblyElementCount"])
                self.assertEqual(r["companionElementCount"], 0)
                self.assertNotIn("companionModel", r)
                self.assertEqual(r["assemblyWithSpareMagazineCount"], len(names))
                self.assertLessEqual(len(names), 1000)
                batteries = [e for e in source["elements"] if any(s in e["name"].lower() for s in ("cartridge", "powerpack", "pack_", "battery", "keel", "under_grip_cell"))]
                self.assertTrue(batteries)
                for e in batteries:
                    self.assertEqual([n for n in model["elements"] if n["name"] == e["name"]], [e])
                self.assertEqual(len(names), r["sourceElementCount"]-len(r["removedSightNames"])+len(r["addedSightNames"]))

    def test_emitted_cuboids_faces_uvs_and_resolved_texture_slots(self):
        for r in self.rows:
            model = self.models[r["id"]]
            for slot, name in model["textures"].items():
                ns, texture = name.split(":")
                self.assertTrue((ROOT / "src/main/resources/assets" / ns / "textures" / (texture+".png")).is_file(), slot)
            for e in model["elements"]:
                with self.subTest(id=r["id"], element=e["name"]):
                    self.assertEqual(len(e["from"]), 3)
                    self.assertEqual(len(e["to"]), 3)
                    self.assertTrue(all(math.isfinite(v) for v in e["from"]+e["to"]))
                    self.assertTrue(all(a < b for a,b in zip(e["from"],e["to"])))
                    self.assertNotIn("vertices", e)
                    self.assertNotIn("triangles", e)
                    self.assertEqual(set(e["faces"]), set(g.FACES))
                    for f in e["faces"].values():
                        self.assertEqual(len(f["uv"]), 4)
                        self.assertTrue(all(math.isfinite(v) and 0 <= v <= 16 for v in f["uv"]))
                        self.assertIn(f["texture"].removeprefix("#"), model["textures"])

    def test_hash_pinned_actual_photos_design_and_rip_provenance(self):
        refs = {r["id"]: r for r in g.read("art/weapons/w31/references.json")}
        for r in self.rows:
            ref = r["reference"]
            with self.subTest(id=r["id"]):
                self.assertEqual(ref["photoSha256"], refs[r["id"]]["sha256"])
                self.assertEqual(digest(Path(ref["photo"])), ref["photoSha256"])
                self.assertEqual(ref["url"], refs[r["id"]]["screenshot"])
                self.assertTrue(ref["notes"])
                self.assertTrue(ref["priorRipSha256"])
                self.assertEqual(len(ref["provenance"]), 3)
                for path, expected in ref["provenance"].items():
                    self.assertEqual(digest(ROOT/path), expected)
                prior = g.read(Path("art/weapons/w123")/r["id"]/"manifest.json")
                self.assertEqual(prior["raw_input_sha256"][ref["photo"]], ref["photoSha256"])
                for path, expected in ref["priorRipSha256"].items():
                    self.assertEqual(prior["raw_input_sha256"][path], expected)
                for texture, expected in r["sourceTextureSha256"].items():
                    ns, path = texture.split(":")
                    self.assertEqual(digest(ROOT/"src/main/resources/assets"/ns/"textures"/(path+".png")), expected)
                self.assertEqual(digest(ROOT/g.ASSETS/"textures/item/weapon/w148/sights.png"), r["sightTextureSha256"])

    def test_dense_useful_viewing_window_all_assembled_parts(self):
        for row in self.rows:
            left, bottom, right, top = row["usableSightWindow"]
            self.assertGreaterEqual(right-left, .24)
            self.assertGreaterEqual(top-bottom, .23)
            self.assertGreater((right-left)*(top-bottom), .07)
            self.assertEqual(len(list(g.sight_rays(row))), 162)
            self.assertEqual(g.blockers(self.models[row["id"]], row), [], row["id"])

    def test_actual_original_optic_sides_and_hood_visible_from_eye(self):
        for row in self.rows:
            for name in row["visibleOpticNames"]:
                with self.subTest(id=row["id"], name=name):
                    self.assertIn(name, row["retainedSightNames"])
                    self.assertGreaterEqual(len(g.visible_samples(self.models[row["id"]], row, name)), 4)

    def test_w152_foreground_wall_with_tiny_clear_center_is_rejected(self):
        # Both center and pin can remain clear while the original ears are lost.
        row = self.rows[-1]
        model = copy.deepcopy(self.models[row["id"]])
        x,y,z = g.eye(row)
        panels = [([x-10,y-10,z-1.05],[x-.025,y+10,z-1]),
                  ([x+.025,y-10,z-1.05],[x+10,y+10,z-1]),
                  ([x-.025,y-10,z-1.05],[x+.025,y-.025,z-1]),
                  ([x-.025,y+.025,z-1.05],[x+.025,y+10,z-1])]
        for i,(lo,hi) in enumerate(panels):
            model["elements"].append(g.box("foreground_stock_"+str(i),lo,hi))
        self.assertEqual([e["name"] for e in model["elements"] if g.ray_entry(e,g.eye(row),[x,y,-40]) is not None], [])
        tip = list(row["aimingTip"]);tip[1] -= .025
        self.assertEqual([e["name"] for e in model["elements"] if g.ray_entry(e,g.eye(row),tip) is not None], ["w153_aim_tip"])
        self.assertTrue(g.blockers(model,row))
        for name in row["visibleOpticNames"]:
            self.assertLess(len(g.visible_samples(model,row,name)),4)

    def test_aiming_point_is_seated_visible_and_has_clear_apparent_gap(self):
        for r in self.rows:
            with self.subTest(id=r["id"]):
                model = self.models[r["id"]]
                x,y,z = r["aimingTip"];cx,cy,cz = r["sightCenter"]
                self.assertEqual(x,cx)
                self.assertLess(z,cz)
                d = r["eyeToSightMeters"]*16/r["scale"]
                self.assertAlmostEqual((cy-y)*d/(d+cz-z),.075,places=6)
                self.assertGreater(cy-y,.055)
                target=[x,y-.025,z]
                self.assertEqual([e["name"] for e in model["elements"] if g.ray_entry(e,g.eye(r),target) is not None], [r["aimingTipName"]])
                tip = next(e for e in model["elements"] if e["name"] == r["aimingTipName"])
                stem = next(e for e in model["elements"] if e["name"] == ("w153_shortened_original_front_post" if r["id"] == "dream_breaker" else "w153_aim_stem"))
                self.assertAlmostEqual(tip["from"][1],stem["to"][1],places=6)
                self.assertTrue(all(f["uv"] == [4.25, .25, 4.75, .75] and f["texture"] == "#sight" for f in tip["faces"].values()))
                self.assertEqual(tip["from"][0],stem["from"][0])
                self.assertEqual(tip["to"][0],stem["to"][0])
                if r["id"] != "dream_breaker":
                    contact=[x,stem["from"][1]-.001,z]
                    self.assertTrue(any(g.ray_entry(e,contact,contact) is not None for e in self.sources[r["id"]]["elements"]))

    def test_dream_only_obstructing_post_trim_and_spatial_side_uv_crop(self):
        row = self.rows[2];model=self.models[row["id"]]
        original=next(e for e in self.sources[row["id"]]["elements"] if e["name"] == "front_sight_post")
        self.assertTrue(any(g.ray_entry(original,a,b) is not None for a,b in g.sight_rays(row)))
        bad=copy.deepcopy(model);bad["elements"].append(original)
        self.assertIn("front_sight_post",g.blockers(bad,row))
        stem=next(e for e in model["elements"] if e["name"] == "w153_shortened_original_front_post")
        tip=next(e for e in model["elements"] if e["name"] == "w153_aim_tip")
        self.assertEqual(stem["from"],original["from"])
        self.assertEqual(stem["to"][0::2],original["to"][0::2])
        self.assertEqual(tip["to"][0::2],original["to"][0::2])
        self.assertLess(tip["to"][1],original["to"][1])
        self.assertLess(original["to"][1]-tip["to"][1],.15)
        fraction=(stem["to"][1]-stem["from"][1])/(original["to"][1]-original["from"][1])
        for name, face in stem["faces"].items():
            old=original["faces"][name]
            if name in ("up","down"):
                self.assertEqual(face,old)
            else:
                self.assertEqual(face["texture"],old["texture"])
                self.assertEqual(face["uv"][0::2],old["uv"][0::2])
                self.assertEqual(face["uv"][3],old["uv"][3])
                self.assertAlmostEqual(face["uv"][1],old["uv"][3]-(old["uv"][3]-old["uv"][1])*fraction,places=6)

    def test_forward_coriolis_eye_clears_stock_without_deleting_it(self):
        row=self.rows[-1];model=self.models[row["id"]]
        rail=next(e for e in model["elements"] if e["name"] == "rear_upper_rail")
        self.assertLess(g.eye(row)[2]+.1,rail["from"][2])
        for name in ("rear_upper_rail","butt_pad","sight_ear-1","sight_ear1"):
            self.assertEqual(next(e for e in model["elements"] if e["name"]==name),next(e for e in self.sources[row["id"]]["elements"] if e["name"]==name))
        self.assertEqual(row["removedSightNames"],[])

    def test_rotated_native_xyz_legacy_rescale_and_finite_eye(self):
        for rot in ({"x":22,"y":-31,"z":47},{"axis":"z","angle":45,"rescale":True},{"axis":"x","angle":-23}):
            e={"from":[-2,-.1,-1],"to":[2,.1,1],"rotation":dict(origin=[.3,.4,.5],**rot)}
            for point in ([0,0,0],[2,-1,4]):
                back=g.local_point(e,g.world_point(e,point))
                for a,b in zip(back,point):self.assertAlmostEqual(a,b,places=8)
        e={"from":[1,-.1,-1],"to":[3,.1,1],"rotation":{"origin":[0,0,0],"z":90}}
        self.assertIsNotNone(g.ray_entry(e,[0,2,3],[0,2,-3]))
        self.assertIsNone(g.ray_entry(e,[2,0,3],[2,0,-3]))
        behind={"from":[-1,-1,5],"to":[1,1,6]}
        self.assertIsNone(g.ray_entry(behind,[0,0,4],[0,0,-40]))
        card={"from":[-1,-1,0],"to":[1,1,0]}
        self.assertIsNotNone(g.ray_entry(card,[0,0,1],[0,0,-1]))

    def test_verify_success_and_failure_never_write(self):
        with patch.object(Path,"write_bytes",side_effect=AssertionError("write forbidden")), patch.object(Path,"mkdir",side_effect=AssertionError("mkdir forbidden")), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(g.main(["--verify"]),0)
            with patch.object(g,"generate",return_value={g.MANIFEST:b"wrong bytes"}):
                with self.assertRaises(SystemExit) as failed, contextlib.redirect_stderr(io.StringIO()):
                    g.main(["--verify"])
                self.assertEqual(failed.exception.code,1)

    def test_generation_and_verify_preserve_all_source_and_canonical_inputs(self):
        protected=set()
        for r in self.rows:
            protected.add(ROOT/r["source"])
            protected.update(ROOT/p for p in r["reference"]["provenance"])
            for directory in (ROOT/g.ASSETS/"models/weapon/fusion_rifle",ROOT/g.ASSETS/"textures/item/weapon/w123"):
                protected.update(directory.glob(r["id"]+"*"))
        protected.add(ROOT/g.ASSETS/"textures/item/weapon/w148/sights.png")
        def snapshot():
            return {str(p):(digest(p),p.stat().st_mtime_ns) for p in protected if p.is_file()}
        before=snapshot()
        g.generate()
        with contextlib.redirect_stdout(io.StringIO()):g.main(["--verify"])
        self.assertEqual(snapshot(),before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
