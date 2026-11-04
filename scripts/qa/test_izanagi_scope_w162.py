#!/usr/bin/env python3
"""Targeted offline W162 regressions. No native/client/server state is accessed."""
import importlib.util
import argparse
import io
import itertools
import json
from pathlib import Path
import sys
import unittest
import zipfile

from PIL import Image

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("w162", ROOT / "scripts/generate_izanagi_scope_w162.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def resolve(node, context, pose, grip, floats):
    kind = node["type"]
    if kind == "minecraft:select":
        value = context if node["property"] == "minecraft:display_context" else pose
        for case in node["cases"]:
            cases = case["when"] if isinstance(case["when"], list) else [case["when"]]
            if value in cases:
                return resolve(case["model"], context, pose, grip, floats)
        return resolve(node["fallback"], context, pose, grip, floats)
    if kind == "minecraft:condition":
        assert node["property"] == "minecraft:custom_model_data" and node["index"] == 0
        return resolve(node["on_true" if grip else "on_false"], context, pose, grip, floats)
    if kind == "minecraft:range_dispatch":
        assert node["property"] == "minecraft:custom_model_data"
        value = floats.get(node.get("index", 0), 0) * node.get("scale", 1)
        chosen = node["fallback"]
        for entry in node["entries"]:
            if value >= entry["threshold"]:
                chosen = entry["model"]
        return resolve(chosen, context, pose, grip, floats)
    assert kind in {"minecraft:model", "minecraft:empty", "minecraft:composite"}, kind
    return node


class IzanagiScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = g.generate()
        cls.wrapper = json.loads(cls.outputs[g.WRAPPER])["model"]
        cls.source = json.loads((ROOT / g.W91).read_bytes())["model"]

    def test_exact_outputs_are_reproducible_and_pinned(self):
        self.assertEqual(8, len(self.outputs))
        self.assertEqual(self.outputs, g.generate())
        for path, data in self.outputs.items():
            self.assertEqual(data, (ROOT / path).read_bytes(), path)
        m = json.loads(self.outputs[g.MANIFEST])
        self.assertEqual(7, len(m["sha256"]))
        self.assertIn("Authored approximation", m["artwork"])
        for path, sha in m["sha256"].items():
            self.assertEqual(sha, g.sha((ROOT / path).read_bytes()), path)

    def test_every_non_fp_context_retains_w91_pose_grip_and_charge_graph(self):
        contexts = ("thirdperson_righthand", "thirdperson_lefthand", "gui", "ground", "fixed", "head", "none", "on_shelf")
        poses = ("hip", "ads", "scope", "inspect", "unknown", "")
        # Include animation and generation-offset boundaries, not merely completed charge.
        selectors = (-1, 0, .00025, .50025, 1.0005, 2, 2.50025, 3.0005, 4, 4.0005, 5)
        for ctx, pose, grip, slot6, aim in itertools.product(contexts, poses, (False, True), selectors, (0, .49, .5, 1)):
            floats = {6: slot6, 3: aim}
            self.assertEqual(resolve(self.source, ctx, pose, grip, floats),
                             resolve(self.wrapper, ctx, pose, grip, floats), (ctx, pose, grip, floats))

    def test_only_two_first_person_contexts_are_empty(self):
        for ctx, pose, grip, slot6 in itertools.product(
                ("firstperson_righthand", "firstperson_lefthand"),
                ("hip", "ads", "scope", "inspect"), (False, True), (-1, 0, 2.5, 4.0005)):
            self.assertEqual({"type": "minecraft:empty"}, resolve(self.wrapper, ctx, pose, grip, {6: slot6}))
        # Runtime alone admits this wrapper; it is never referenced back from W91.
        self.assertNotIn("weapon_scope_w45/izanagis_burden", json.dumps(self.source))

    def test_clear_aim_ray_clipped_aperture_and_opaque_ultrawide_periphery(self):
        im = Image.open(io.BytesIO(self.outputs[g.A + "textures/item/hud/" + g.NAME + "frame.png"]))
        self.assertEqual((1024, 1024), im.size)
        self.assertEqual((0, 0), im.getchannel("A").crop((480, 480, 544, 544)).getextrema())
        for x, y in ((32, 512), (992, 512), (512, 32), (512, 992), (320, 380)):
            self.assertEqual(255, im.getpixel((x, y))[3])
        self.assertEqual(0, im.getpixel((330, 430))[3], "Broad opening differs from circular mask")
        self.assertGreater(im.getpixel((350, 512))[3], 100, "Inward side line")
        sight = Image.open(io.BytesIO(self.outputs[g.A + "textures/item/hud/" + g.NAME + "reticle.png"]))
        self.assertEqual((128, 128), sight.size)
        self.assertEqual(0, sight.getpixel((64, 64))[3], "Hollow center")
        self.assertGreater(sight.getpixel((64, 58))[3], 100)

    def test_hud_quads_use_owned_texture_locations_and_color_slot_zero(self):
        for part in ("frame", "reticle"):
            key = "gui/hud/" + g.NAME + part
            model = json.loads(self.outputs[g.A + "models/" + key + ".json"])
            item = json.loads(self.outputs[g.A + "items/" + key + ".json"])["model"]
            self.assertEqual("destiny:" + key, item["model"])
            self.assertEqual(0, item["tints"][0]["index"])
            sprite = "item/hud/" + g.NAME + part
            self.assertEqual("destiny:" + sprite, model["textures"]["0"])
            self.assertEqual("destiny:" + sprite, model["textures"]["particle"])
            self.assertIn(g.A + "textures/" + sprite + ".png", self.outputs, "Physical items-atlas texture, no conversion assumed")
            self.assertEqual(1, len(model["elements"]))
            self.assertEqual({"north", "south"}, model["elements"][0]["faces"].keys())
            for face in model["elements"][0]["faces"].values():
                self.assertEqual(0, face["tintindex"])

    def test_source_lenses_canonical_cubes_and_sourced_zoom_remain_intact(self):
        model = json.loads((ROOT / "art/weapons/w84/model/source/izanagi.bbmodel").read_bytes())
        self.assertEqual(79, len(model["elements"]))
        for i in (43, 78):
            e = model["elements"][i]
            self.assertEqual(e["from"][2], e["to"][2])
            self.assertEqual([0, 32, 20.5, 52], e["faces"]["south"]["uv"])
        exotic = json.loads((ROOT / "src/main/resources/destiny/weapons/w84-exotics.json").read_bytes())[0]
        self.assertEqual(45, exotic["characteristics"]["stats"]["3555269338"])
        self.assertEqual(4.5, exotic["aim"]["profile"]["zoom"])
        self.assertEqual(61, exotic["timing"]["timing"]["reloadTicks"])


def verify_pack(path):
    """Parent can check the actual Polymer ZIP after integration, without launching a client."""
    outputs = g.generate()
    with zipfile.ZipFile(path) as pack:
        for part in ("frame", "reticle"):
            name = g.NAME + part
            sprite = "item/hud/" + name
            png_path = "assets/destiny/textures/" + sprite + ".png"
            if pack.read(png_path) != outputs["src/main/resources/" + png_path]:
                raise AssertionError("Actual pack texture differs: " + png_path)
            model = json.loads(pack.read("assets/destiny/models/gui/hud/" + name + ".json"))
            if model["textures"]["0"] != "destiny:" + sprite or model["textures"]["particle"] != "destiny:" + sprite:
                raise AssertionError("Actual pack uses a non-items-atlas sprite: " + name)
            item = json.loads(pack.read("assets/destiny/items/gui/hud/" + name + ".json"))
            if item["model"]["model"] != "destiny:gui/hud/" + name:
                raise AssertionError("Actual HUD item model differs: " + name)
        wrapper = "assets/destiny/items/weapon_scope_w45/izanagis_burden.json"
        if json.loads(pack.read(wrapper)) != json.loads(outputs["src/main/resources/" + wrapper]):
            raise AssertionError("Actual pack scope wrapper differs")
    print("Verified actual Polymer pack: 7 W162 resources, physical items-atlas texture paths")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, help="Actual parent-built Polymer pack ZIP; omitted means no pack proof")
    args, unittest_args = parser.parse_known_args()
    result = unittest.main(argv=[sys.argv[0], *unittest_args], verbosity=2, exit=False)
    if not result.result.wasSuccessful():
        raise SystemExit(1)
    if args.pack:
        verify_pack(args.pack)
