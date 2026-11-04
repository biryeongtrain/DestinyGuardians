#!/usr/bin/env python3
"""W153 targeted implementation regressions, standard library only.

rtk proxy python3 -B scripts/qa/test_sight_bodies_w153_sidearms_heavy.py
No builds, games, fixtures, source writes, or dependency writes.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy
import struct
import subprocess
import sys
import unittest
from unittest import mock
import zlib

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/generate_sight_bodies_w153_sidearms_heavy.py"
G = runpy.run_path(str(SCRIPT))
IDS = ("dead_man_walking_xx7463", "high_albedo", "brass_attacks",
       "edge_transit", "fixed_odds", "retrofit_escapade")
EXPECTED_COUNTS = (102, 105, 115, 98, 155, 134)
EXPECTED_RELIEF = (.36, .34, .34, .32, .44, .36)
ASSETS = ROOT / G["ASSETS"]


def read(path):
    def reject(value):
        raise ValueError(value)
    return json.loads(path.read_bytes(), parse_constant=reject)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(paths):
    return {p: (digest(p), p.stat().st_mtime_ns) for p in paths}


def tip_pixels(path):
    """Decode the existing small RGBA8 W148 atlas; no Pillow dependency."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not PNG")
    offset, compressed = 8, bytearray()
    while offset < len(data):
        n = struct.unpack(">I", data[offset:offset+4])[0]
        tag, chunk = data[offset+4:offset+8], data[offset+8:offset+8+n]
        if tag == b"IHDR":
            width, height, bits, color, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            if (bits, color, interlace) != (8, 6, 0):
                raise ValueError("Expected RGBA8")
        if tag == b"IDAT":
            compressed.extend(chunk)
        offset += n+12
    raw, previous, rows = zlib.decompress(compressed), [0]*(width*4), []
    stride = width*4
    for y in range(height):
        offset = y*(stride+1)
        mode, row = raw[offset], list(raw[offset+1:offset+1+stride])
        for i in range(stride):
            a, b, c = row[i-4] if i >= 4 else 0, previous[i], previous[i-4] if i >= 4 else 0
            if mode == 0:
                prediction = 0
            elif mode == 1:
                prediction = a
            elif mode == 2:
                prediction = b
            elif mode == 3:
                prediction = (a+b)//2
            elif mode == 4:
                p = a+b-c
                prediction = min((a,b,c), key=lambda v: abs(p-v))
            else:
                raise ValueError("Unknown filter")
            row[i] = (row[i]+prediction) % 256
        rows.append([tuple(row[i:i+4]) for i in range(0, stride, 4)])
        previous = row
    return width, height, rows


class SidearmsHeavySights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = read(ROOT/G["MANIFEST"])
        cls.rows = {r["id"]: r for r in cls.manifest["weapons"]}
        cls.models = {w: read(ASSETS/f"models/{cls.rows[w]['body']}.json") for w in IDS}
        cls.sources = {w: read(ROOT/cls.rows[w]["source"]) for w in IDS}

    def test_01_w151_contract_and_six_actual_sources(self):
        self.assertEqual(set(self.manifest), {"weapons"})
        self.assertEqual(tuple(self.rows), IDS)
        required = {"id", "family", "body", "sightCenter", "forwardPoint", "eyeSide", "plane",
                    "scale", "eyeToSightMeters", "elementCount", "source", "sourceSha256",
                    "removedSightNames", "addedSightNames", "style", "reference", "aimingTip"}
        for i, (w, row) in enumerate(self.rows.items()):
            with self.subTest(weapon=w):
                self.assertLessEqual(required, row.keys())
                self.assertEqual(row["family"], "sidearm" if i<3 else "heavy_grenade_launcher" if i==3 else "machine_gun")
                self.assertEqual(row["body"], f"weapon_sight_w153/{w}_body")
                self.assertEqual(row["source"], f"src/main/resources/assets/destiny/models/weapon_surface_w123/{w}.json")
                self.assertEqual((row["eyeSide"], row["plane"], row["scale"]), ("+Z", "XY", .9))
                self.assertEqual(row["eyeToSightMeters"], EXPECTED_RELIEF[i])
                x,y,z = row["sightCenter"]
                self.assertEqual(row["forwardPoint"], [x,y,round(z-2,7)])
                self.assertEqual(row["sourceSha256"], digest(ROOT/row["source"]))
        self.assertEqual(len({r["style"] for r in self.rows.values()}), 6)

    def test_02_original_non_sight_and_sight_records_preserved_exactly(self):
        for w, row in self.rows.items():
            with self.subTest(weapon=w):
                retained = [e for e in self.sources[w]["elements"] if e["name"] not in row["removedSightNames"]]
                actual = [e for e in self.models[w]["elements"] if e["name"] not in row["addedSightNames"]]
                self.assertEqual(actual, retained)  # Includes every geometry/UV/rotation record, in order.
                self.assertEqual(row["removedSightNames"], ["objective_lens", "ocular_lens"] if w==IDS[-1] else [])
                for key, value in self.sources[w].items():
                    if key not in ("display", "textures", "elements"):
                        self.assertEqual(self.models[w][key], value)
                self.assertNotIn("display", self.models[w])
                for key,value in self.sources[w]["textures"].items():
                    self.assertEqual(self.models[w]["textures"][key], value)

    def test_03_emitted_counts_full_only_and_seated_magazines_once(self):
        for w, count in zip(IDS, EXPECTED_COUNTS):
            row, model = self.rows[w], self.models[w]
            names = [e["name"] for e in model["elements"]]
            self.assertEqual(len(names), len(set(names)))
            self.assertEqual(len(names), count)
            self.assertEqual(row["elementCount"], count)
            self.assertEqual(row["assemblyElementCount"], count)
            self.assertEqual(row["assemblyWithSpareMagazineCount"], count)
            self.assertLessEqual(count, 1000)
            self.assertEqual(row["companionElementCount"], 0)
            self.assertNotIn("companionModel", row)
            original_mag = [e for e in self.sources[w]["elements"]
                            if any(p in e["name"] for p in ("magazine", "drum", "belt", "round", "cartridge"))]
            self.assertEqual([e for e in model["elements"] if e["name"] in {p["name"] for p in original_mag}], original_mag)

    def test_04_finite_native_cube_schema_and_face_uv(self):
        for w, model in self.models.items():
            for e in model["elements"]:
                with self.subTest(weapon=w, element=e["name"]):
                    self.assertNotIn("vertices", e)
                    self.assertNotIn("triangles", e)
                    self.assertEqual(len(e["from"]), 3)
                    self.assertTrue(all(math.isfinite(a) and math.isfinite(b) and a<b
                                        for a,b in zip(e["from"], e["to"])))
                    self.assertEqual(set(e["faces"]), set(G["FACES"]))
                    for f in e["faces"].values():
                        self.assertTrue(all(math.isfinite(v) and 0<=v<=16 for v in f["uv"]))
                        self.assertIn(f["texture"][1:], model["textures"])

    def test_05_real_photos_w123_design_manifest_review_and_texture_provenance(self):
        refs = {r["id"]: r for r in read(ROOT/"art/weapons/w31/references.json")}
        for w,row in self.rows.items():
            ref = row["reference"]
            self.assertEqual(ref["photoSha256"], digest(Path(ref["photo"])))
            self.assertEqual(ref["photoSha256"], refs[w]["sha256"])
            self.assertEqual(ref["url"], refs[w]["screenshot"])
            self.assertTrue(ref["notes"])
            self.assertEqual(len(ref["provenance"]), 3)
            for path,h in ref["provenance"].items():
                self.assertEqual(h, digest(ROOT/path))
            self.assertTrue(ref["priorRipSha256"])
            for path,h in ref["priorRipSha256"].items():
                self.assertEqual(h, digest(Path(path)))
            for resource,h in row["sourceTextureSha256"].items():
                self.assertEqual(h, digest(ASSETS/("textures/"+resource.split(":")[1]+".png")))
            self.assertEqual(row["sightTextureSha256"], digest(ROOT/G["TIP_TEXTURE"]))

    def test_06_added_pin_uses_real_sight_metal_uv_and_bright_opaque_cap(self):
        width,height,pixels = tip_pixels(ROOT/G["TIP_TEXTURE"])
        for row in self.rows.values():
            model, source = self.models[row["id"]], self.sources[row["id"]]
            by_name = {e["name"]:e for e in model["elements"]}
            originals = {e["name"]:e for e in source["elements"]}
            for name,donor in row["sightUvDonors"].items():
                self.assertEqual(by_name[name]["faces"], originals[donor]["faces"])
            tip = by_name[row["aimingTipName"]]
            expected = ["w153_aim_stem", "w153_aim_tip"]
            if row["id"] == "high_albedo":
                expected += ["w153_rear_sill", "w153_rear_left", "w153_rear_right"]
            elif row["id"] == "brass_attacks":
                expected += ["w153_rear_left", "w153_rear_right"]
            self.assertEqual(row["addedSightNames"], expected)
            for f in tip["faces"].values():
                u,v,u1,v1 = f["uv"]
                self.assertEqual(f["texture"], "#sight")
                for y in range(int(v*height/16), math.ceil(v1*height/16)):
                    for x in range(int(u*width/16), math.ceil(u1*width/16)):
                        self.assertGreaterEqual(min(pixels[y][x][:3]), 180)
                        self.assertEqual(pixels[y][x][3],255)

    def test_07_complete_assembly_center_and_contiguous_upper_window(self):
        for w,row in self.rows.items():
            self.assertEqual(G["channel_hits"](self.models[w], row), [])
            self.assertEqual(row["clearUpperWindow"], dict(halfWidth=.08, height=.07))
            for ix in range(-4,5):
                for iy in range(5):
                    self.assertEqual(G["channel_hits"](self.models[w],row,.08*ix/4,.07*iy/4), [], (w,ix,iy))

    def test_08_broad_usable_aperture_not_tiny_center_clearance(self):
        for w,row in self.rows.items():
            hx,hy = row["apertureHalfSize"]
            self.assertGreaterEqual(hx,.18)
            self.assertGreaterEqual(hy,.10)
            fraction = G["aperture_fraction"](self.models[w],row)
            self.assertGreaterEqual(fraction,.60,w)
            self.assertAlmostEqual(fraction,row["clearApertureFraction"],places=6)

    def test_09_rear_hardware_and_aiming_points_visible_from_actual_eye(self):
        for w,row in self.rows.items():
            self.assertTrue(row["hardwareLandmarks"])
            self.assertEqual(G["foreground_blockers"](self.models[w],row),{},w)
            self.assertEqual(G["tip_blockers"](self.models[w],row),[],w)
            # The landmark belongs to its real retained optic, not invented air.
            es={e["name"]:e for e in self.models[w]["elements"]}
            for landmark in row["hardwareLandmarks"]:
                local=G["transform_point"](es[landmark["name"]],landmark["point"],inverse=True)
                self.assertTrue(all(a-1e-6<=p<=b+1e-6 for a,p,b in zip(es[landmark["name"]]["from"],local,es[landmark["name"]]["to"])))
            self.assertGreater(row["sightCenter"][1],row["aimingTip"][1])
            self.assertLess((row["sightCenter"][1]-row["aimingTip"][1])/(G["eye"](row)[2]-row["aimingTip"][2]),.02)

    def test_10_regression_foreground_stock_ring_fails_despite_clear_center(self):
        w=IDS[-1]; row=self.rows[w]; model=copy.deepcopy(self.models[w])
        x,y,sight_z=row["sightCenter"]; z=sight_z+.6
        # A stock-like foreground wall with a .06-unit pinhole still passes a
        # center-only gate. It must fail BOTH the wide aperture and rim checks.
        for name,lo,hi in [
            ("left",[x-2,y-2,z],[x-.03,y+2,z+.1]),
            ("right",[x+.03,y-2,z],[x+2,y+2,z+.1]),
            ("bottom",[x-.03,y-2,z],[x+.03,y-.03,z+.1]),
            ("top",[x-.03,y+.03,z],[x+.03,y+2,z+.1])]:
            model["elements"].append(dict(name="stock_regression_"+name,**{"from":lo,"to":hi}))
        self.assertEqual(G["channel_hits"](model,row),[])
        self.assertLess(G["aperture_fraction"](model,row),.60)
        self.assertTrue(G["foreground_blockers"](model,row))
        self.assertTrue(G["tip_blockers"](model,row))

    def test_11_opaque_original_lenses_really_block_the_tube(self):
        w=IDS[-1]; row=self.rows[w]
        originals={e["name"]:e for e in self.sources[w]["elements"]}
        for n in row["removedSightNames"]:
            model=copy.deepcopy(self.models[w]); model["elements"].append(originals[n])
            self.assertIn(n,G["channel_hits"](model,row))
        # Preserve the optic itself, including every original hood/rim/top loop.
        before=[e for e in self.sources[w]["elements"] if any(t in e["name"] for t in ("optic_hood", "ocular_rim", "optic_loop"))]
        after=[e for e in self.models[w]["elements"] if e["name"] in {p["name"] for p in before}]
        self.assertEqual(after,before)
        self.assertEqual(len(before),19)

    def test_12_segment_bounds_and_rotations(self):
        e=dict(name="fixture", **{"from":[-.5,-.5,-1],"to":[.5,.5,1]},
               rotation=dict(origin=[0,0,0],axis="y",angle=90))
        self.assertIsNotNone(G["ray_hit"](e,[2,0,0],[-2,0,0]))
        self.assertIsNone(G["ray_hit"](e,[2,0,0],[1.1,0,0]))
        self.assertIsNone(G["ray_hit"](e,[0,2,2],[0,2,-2]))
        e["rotation"]=dict(origin=[1,2,3],x=31,y=-27,z=113)
        p=[3,5,-2]
        world=G["transform_point"](e,p)
        restored=G["transform_point"](e,world,inverse=True)
        for a,b in zip(p,restored):self.assertAlmostEqual(a,b,places=10)
        e["rotation"]=dict(origin=[0,0,0],axis="z",angle=45,rescale=True)
        p=[1,2,3]
        for a,b in zip(p,G["transform_point"](e,G["transform_point"](e,p),inverse=True)):
            self.assertAlmostEqual(a,b,places=10)

    def test_13_legacy_and_euler_have_same_actual_axis_rotation(self):
        for axis in "xyz":
            a=dict(rotation=dict(origin=[1,2,3],axis=axis,angle=37))
            b=dict(rotation=dict(origin=[1,2,3],**{axis:37}))
            self.assertEqual(G["transform_point"](a,[4,5,6]),G["transform_point"](b,[4,5,6]))
        e=dict(**{"from":[0,0,0],"to":[1,1,0]})
        self.assertIsNotNone(G["ray_hit"](e,[.5,.5,1],[.5,.5,-1]))

    def test_14_generate_is_deterministic_exact_owned_path_to_bytes(self):
        first,second=G["generate"](),G["generate"]()
        self.assertEqual(first,second)
        expected={G["ASSETS"]/f"models/weapon_sight_w153/{w}_body.json" for w in IDS}|{G["MANIFEST"]}
        self.assertEqual(set(first),expected)
        for p,data in first.items():
            self.assertIsInstance(p,Path)
            self.assertIsInstance(data,bytes)
            self.assertEqual((ROOT/p).read_bytes(),data)

    def test_15_verify_cli_is_nonwriting_and_sources_stay_intact(self):
        paths=set()
        for row in self.rows.values():
            paths.add(ROOT/row["source"])
            paths.update(ROOT/p for p in row["reference"]["provenance"])
            paths.update(Path(p) for p in row["reference"]["priorRipSha256"])
            paths.add(Path(row["reference"]["photo"]))
            paths.update(ASSETS/("textures/"+v.split(":")[1]+".png") for v in self.sources[row["id"]]["textures"].values())
        paths.update(ROOT/p for p in G["generate"]())
        paths.add(ROOT/G["TIP_TEXTURE"])
        before=snapshot(paths)
        result=subprocess.run(["rtk","proxy",sys.executable,"-B",str(SCRIPT),"--verify"],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(snapshot(paths),before)

    def test_16_stale_verify_fails_without_repair_or_any_write(self):
        globals_=G["main"].__globals__
        with mock.patch.dict(globals_,mismatches=lambda outputs:["deliberately_stale_body.json"]):
            with mock.patch.object(Path,"write_bytes",side_effect=AssertionError("verify tried to write")):
                with self.assertRaises(SystemExit) as caught:
                    G["main"](["--verify"])
        self.assertEqual(caught.exception.code,1)

    def test_17_duplicate_sources_or_unjustified_removals_rejected(self):
        original_read=G["read"]
        w=IDS[0]; source=copy.deepcopy(self.sources[w]);source["elements"].append(source["elements"][0])
        with mock.patch.dict(G["make_body"].__globals__,read=lambda path: source):
            with self.assertRaisesRegex(ValueError,"duplicate source"):
                G["make_body"](w,G["WEAPONS"][w])
        self.assertIs(G["read"],original_read)
        cfg=dict(G["WEAPONS"][w],removed=["absent_part"])
        with self.assertRaisesRegex(ValueError,"missing requested removal"):
            G["make_body"](w,cfg)
        cfg=dict(G["WEAPONS"][w],removed=["trigger_tip"])
        with self.assertRaisesRegex(ValueError,"unjustified removal"):
            G["make_body"](w,cfg)

    def test_18_offline_limitations_and_master_followups_are_explicit(self):
        review=(ROOT/"art/weapons/w153/sidearms-heavy-review.md").read_text()
        for term in ("26.3", "21", "HIP", "reload", "10–20", "master", "native"):
            self.assertIn(term,review)
        for w in IDS:self.assertIn(w,review)


if __name__=="__main__":
    unittest.main(verbosity=2)
