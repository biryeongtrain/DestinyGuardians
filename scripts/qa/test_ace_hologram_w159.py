#!/usr/bin/env python3
"""Independent W159 contracts; generate() is read-only and never installs assets."""
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "src/main/resources/assets/destiny"
KEY = "weapon_sight_w159"
CANONICAL = "destiny:item/weapon/ace_of_spades"
BODY = f"destiny:{KEY}/ace_of_spades_body"
TEXTURE = f"destiny:item/{KEY}/ace_reticle"
FP = {"firstperson_righthand", "firstperson_lefthand"}
STYLES = ("native", "twohand")
NAMES = {"w159_hologram_left", "w159_hologram_right", "w159_hologram_dot"}


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


class AceHologramW159Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        generator = ROOT / "scripts/generate_ace_hologram_w159.py"
        if not generator.is_file():
            raise AssertionError("W159 generator baseline is required before running this suite")
        cls.generate = staticmethod(runpy.run_path(str(generator))["generate"])
        cls.outputs = {Path(p): b for p, b in cls.generate().items()}
        cls.source = json.loads((ASSETS / "models/item/weapon/ace_of_spades.json").read_bytes())
        cls.body = json.loads(cls.outputs[ASSETS / f"models/{KEY}/ace_of_spades_body.json"])
        cls.graph = json.loads(cls.outputs[ASSETS / f"items/{KEY}/ace_of_spades.json"])

    def frame(self, frame, style):
        return json.loads(self.outputs[ASSETS / f"models/{KEY}/ace_of_spades_{frame:02}_{style}.json"])

    def test_output_inventory_and_byte_reproducibility(self):
        expected = {ASSETS / f"models/{KEY}/ace_of_spades_{f:02}_{s}.json"
                    for f in range(21) for s in STYLES}
        expected.update({ASSETS / f"models/{KEY}/ace_of_spades_body.json",
                         ASSETS / f"items/{KEY}/ace_of_spades.json",
                         ASSETS / f"textures/item/{KEY}/ace_reticle.png",
                         ROOT / "art/weapons/w159/ace-hologram.json"})
        self.assertEqual(set(self.outputs), expected)
        self.assertEqual(len(self.outputs), 46)
        self.assertEqual(self.outputs, {Path(p): b for p, b in self.generate().items()})
        for path, data in self.outputs.items():
            with self.subTest(path=str(path)):
                self.assertIsInstance(data, bytes)
                self.assertEqual(path.read_bytes(), data)

    def test_all_87_original_elements_and_existing_texture_slots_are_unchanged(self):
        self.assertEqual(len(self.source["elements"]), 87)
        self.assertEqual(self.body["elements"][:87], self.source["elements"])
        self.assertEqual(len(self.body["elements"]), 90)
        textures = self.body["textures"]
        for slot, value in self.source["textures"].items():
            self.assertEqual(textures[slot], value, slot)
        self.assertEqual(set(textures) - set(self.source["textures"]), {"hologram"})
        self.assertEqual(textures["hologram"], TEXTURE)

    def test_three_double_sided_emissive_planes_keep_the_reticle_orientation(self):
        added = self.body["elements"][87:]
        self.assertEqual({element["name"] for element in added}, NAMES)
        for element in added:
            with self.subTest(plane=element["name"]):
                low, high = element["from"], element["to"]
                self.assertEqual(len(low), 3)
                self.assertEqual(len(high), 3)
                self.assertTrue(all(math.isfinite(v) for v in low + high))
                self.assertLess(low[0], high[0])
                self.assertLess(low[1], high[1])
                self.assertEqual(low[2], high[2], "No opaque scope plate or cube depth")
                self.assertEqual(set(element["faces"]), {"south", "north"})
                south, north = element["faces"]["south"], element["faces"]["north"]
                self.assertEqual(north["uv"], [south["uv"][2], south["uv"][1], south["uv"][0], south["uv"][3]])
                self.assertEqual(north["texture"], "#hologram")
                self.assertNotIn("cullface", north)
                self.assertEqual(element["light_emission"], 15)
                self.assertEqual(element["shade_direction_override"], "up")
                face = element["faces"]["south"]
                self.assertEqual(face["texture"], "#hologram")
                self.assertNotIn("cullface", face)
                self.assertEqual(len(face["uv"]), 4)
                self.assertTrue(all(0 <= v <= 16 for v in face["uv"]))
                self.assertNotEqual(face["uv"][0], face["uv"][2])
                self.assertNotEqual(face["uv"][1], face["uv"][3])

    def test_both_frame_families_turn_on_at_095_and_never_before(self):
        for style in STYLES:
            for frame in range(21):
                with self.subTest(style=style, frame=frame):
                    model = self.frame(frame, style)
                    self.assertEqual(model["parent"], CANONICAL if frame < 19 else BODY)
                    self.assertNotIn("elements", model)
                    self.assertNotIn("textures", model)

    def test_non_first_person_transforms_include_correct_twohand_third_person(self):
        for style in STYLES:
            suffix = "_twohand" if style == "twohand" else ""
            canonical = json.loads((ASSETS / f"models/item/weapon/ace_of_spades{suffix}.json").read_bytes())
            expected = {ctx: pose for ctx, pose in canonical["display"].items() if ctx not in FP}
            for frame in range(21):
                display = self.frame(frame, style)["display"]
                with self.subTest(style=style, frame=frame):
                    self.assertEqual({ctx: pose for ctx, pose in display.items() if ctx not in FP}, expected)
                    self.assertTrue(FP <= display.keys())
            self.assertEqual(self.frame(0, style)["display"], canonical["display"])

    def test_full_ads_native_transform_uses_independently_pinned_sight_center(self):
        # Fixed contract, deliberately independent of generator CENTER/EYE/SCALE globals.
        expected_translation = [-8.96, 8.32 - .95 * (12.45 - 8),
                                16 * (.72 - .42) - .95 * (4.075186918 - 8)]
        for context in FP:
            pose = self.frame(20, "native")["display"][context]
            self.assertEqual(pose["rotation"], [0, 0, 0])
            self.assertEqual(pose["scale"], [.95, .95, .95])
            for actual, expected in zip(pose["translation"], expected_translation):
                self.assertAlmostEqual(actual, expected, places=7)

    def test_graph_has_exact_progress_thresholds_and_both_styles(self):
        root = self.graph["model"]
        self.assertEqual(root["type"], "minecraft:select")
        self.assertEqual(root["property"], "minecraft:display_context")
        self.assertEqual(len(root["cases"]), 1)
        self.assertEqual(set(root["cases"][0]["when"]), FP)
        dispatches = [node for node in objects(root["cases"][0]["model"])
                      if node.get("type") == "minecraft:range_dispatch"]
        self.assertEqual(len(dispatches), 1)
        dispatch = dispatches[0]
        self.assertEqual(dispatch["property"], "minecraft:custom_model_data")
        self.assertEqual(dispatch["index"], 3)
        self.assertEqual(dispatch.get("scale", 1), 1)
        self.assertEqual([entry["threshold"] for entry in dispatch["entries"]],
                         [frame / 20 for frame in range(21)])
        for frame, entry in enumerate(dispatch["entries"]):
            node = entry["model"]
            self.assertEqual(node["type"], "minecraft:condition")
            self.assertEqual(node["property"], "minecraft:custom_model_data")
            self.assertEqual(node["index"], 0)
            for branch, style in (("on_false", "native"), ("on_true", "twohand")):
                self.assertEqual(node[branch], {"type": "minecraft:model",
                    "model": f"destiny:{KEY}/ace_of_spades_{frame:02}_{style}"})
        old = json.loads((ASSETS / "items/weapon_aim_w70/ace_of_spades.json").read_bytes())
        self.assertEqual(root["fallback"], old["model"]["fallback"])
        refs = {node["model"] for node in objects(self.graph) if node.get("type") == "minecraft:model"}
        self.assertEqual({ref for ref in refs if ref.startswith(f"destiny:{KEY}/")},
                         {f"destiny:{KEY}/ace_of_spades_{f:02}_{s}" for f in range(21) for s in STYLES})
        self.assertTrue(all(ref.startswith((f"destiny:{KEY}/", "destiny:item/weapon/")) for ref in refs))

    def test_all_model_parents_face_slots_and_texture_references_resolve(self):
        visited = set()

        def load_model(ref, ancestors=()):
            self.assertNotIn(ref, ancestors, "Model parent cycle")
            if ref in visited:
                return
            visited.add(ref)
            namespace, name = ref.split(":", 1)
            path = ROOT / f"src/main/resources/assets/{namespace}/models/{name}.json"
            model = json.loads(self.outputs[path] if path in self.outputs else path.read_bytes())
            parent = model.get("parent")
            if parent and not parent.startswith("minecraft:"):
                load_model(parent, ancestors + (ref,))
            textures = model.get("textures", {})
            refs = list(textures.values())
            refs += [face["texture"] for element in model.get("elements", [])
                     for face in element["faces"].values()]
            for texture in refs:
                slots = set()
                while texture.startswith("#"):
                    self.assertNotIn(texture, slots, "Texture alias cycle")
                    slots.add(texture)
                    texture = textures[texture[1:]]
                ns, name = texture.split(":", 1)
                path = ROOT / f"src/main/resources/assets/{ns}/textures/{name}.png"
                self.assertTrue(path in self.outputs or path.is_file(), str(path))

        for node in objects(self.graph):
            if node.get("type") == "minecraft:model":
                load_model(node["model"])
        load_model(BODY)

    def test_png_is_red_transparent_256_atlas_with_only_small_dot_at_center(self):
        raw = self.outputs[ASSETS / f"textures/item/{KEY}/ace_reticle.png"]
        # Existing standalone PNG decoder is a format helper, not the W159 implementation.
        decode = runpy.run_path(str(ROOT / "scripts/art/build_ace_w83.py"))["png_decode"]
        width, height, rgba = decode(raw)
        self.assertEqual((width, height), (256, 256))
        pixels = [tuple(rgba[i:i + 4]) for i in range(0, len(rgba), 4)]
        visible = [(i % width, i // width, pixel) for i, pixel in enumerate(pixels) if pixel[3]]
        self.assertGreater(len(visible), 16, "Parentheses must be present")
        self.assertLess(len(visible), width * height // 2, "No opaque scope plate")
        for x, y, (red, green, blue, alpha) in visible:
            self.assertGreater(red, 2 * max(green, blue), (x, y, red, green, blue, alpha))
        self.assertGreater(pixels[128 * width + 128][3], 0, "Authored center dot")
        central = [(x, y) for x, y, _ in visible if 112 <= x < 144 and 112 <= y < 144]
        self.assertTrue(central)
        self.assertTrue(all(abs(x - 127.5) <= 5 and abs(y - 127.5) <= 5 for x, y in central),
                        "Central aperture must be transparent outside the tiny dot")
        self.assertTrue(any(x < 112 for x, _, _ in visible), "Left parenthesis")
        self.assertTrue(any(x >= 144 for x, _, _ in visible), "Right parenthesis")

    def test_png_preserves_source_green_channel_mask_outside_authored_dot(self):
        from PIL import Image

        source = Image.open(ROOT / "art/weapons/w159/source/reticle-gstack.png").convert("RGBA")
        source_mask = source.getchannel("G").resize((256, 256), Image.Resampling.LANCZOS)
        generated = Image.open(io.BytesIO(self.outputs[ASSETS / f"textures/item/{KEY}/ace_reticle.png"]))
        alpha = generated.convert("RGBA").getchannel("A")
        # Only the small authored center tile may differ from the source brackets.
        for bounds in ((0, 0, 256, 120), (0, 136, 256, 256),
                       (0, 120, 120, 136), (136, 120, 256, 136)):
            self.assertEqual(alpha.crop(bounds).tobytes(), source_mask.crop(bounds).tobytes(), bounds)
        self.assertGreater(alpha.getpixel((128, 128)), source_mask.getpixel((128, 128)))

    def test_manifest_records_generated_output_hashes(self):
        path = ROOT / "art/weapons/w159/ace-hologram.json"
        manifest = json.loads(self.outputs[path])
        self.assertEqual(manifest["stage"], "W159")
        self.assertEqual(manifest["id"], "ace_of_spades")
        expected = {str(p.relative_to(ROOT)): hashlib.sha256(data).hexdigest()
                    for p, data in self.outputs.items() if p != path}
        self.assertEqual(manifest["outputSha256"], expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
