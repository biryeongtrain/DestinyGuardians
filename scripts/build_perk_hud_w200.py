#!/usr/bin/env python3
"""Build three original W200 perk HUD labels. --verify never writes; --self-test is in memory.

Uses the W183 pinned Arial Narrow Bold 22px / BASIC / 4x coverage raster,
Pillow 12.3.0 and FreeType 2.14.3. No official sprites or bundled font.
"""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "w108_label_codec", ROOT / "scripts/build_feeding_frenzy_hud_w108.py")
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
BASE = Path("src/main/resources/assets/destiny")
ART = Path("art/hud/w200")
MANIFEST = ART / "manifest.json"
# key, authored label, layout, observed count maximum, observed tick maximum
LABELS = (
    ("box_breathing", "BOX BREATHING", "FLAG", 0, 0),
    ("pulse_monitor", "PULSE MONITOR", "FLAG", 0, 0),
    ("unrelenting", "UNRELENTING", "FLAG", 0, 0),
)


def paths(key):
    name = f"perk_{key}_w200"
    return (BASE / f"textures/item/hud/{name}.png",
            BASE / f"models/gui/hud/{name}.json",
            BASE / f"items/gui/hud/{name}.json", ART / f"{name}.svg")


def raster_label(font_bytes, LABEL, SIZE):
    font = codec.ImageFont.truetype(io.BytesIO(font_bytes), 22 * codec.SCALE,
                                    layout_engine=codec.ImageFont.Layout.BASIC)
    left, top, right, bottom = font.getbbox(LABEL)
    ink = codec.Image.new("L", (right - left, bottom - top))
    codec.ImageDraw.Draw(ink).text((-left, -top), LABEL, font=font, fill=255)
    width = min(round(ink.width * 0.9), (SIZE[0] - 2 * codec.PADDING) * codec.SCALE)
    horizontal_scale = width / ink.width
    ink = ink.resize((width, ink.height), codec.Image.Resampling.LANCZOS)
    mask = codec.Image.new("L", (SIZE[0] * codec.SCALE, SIZE[1] * codec.SCALE))
    mask.paste(ink, ((mask.width - ink.width) // 2, (mask.height - ink.height) // 2))
    mask = mask.resize(SIZE, codec.Image.Resampling.LANCZOS)
    bounds = mask.getbbox()
    if not bounds or bounds[0] <= 0 or bounds[1] <= 0 or bounds[2] >= SIZE[0] or bounds[3] >= SIZE[1]:
        raise ValueError("Full label must fit without clipping")
    image = codec.Image.new("RGBA", SIZE, (255, 255, 255, 0))
    image.putalpha(mask)
    return image, bounds, horizontal_scale


def source_svg(image, LABEL, SIZE):
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE[0]}" height="{SIZE[1]}" '
             f'viewBox="0 0 {SIZE[0]} {SIZE[1]}">',
             f"  <title>{LABEL} - original W200 generated label</title>",
             "  <desc>Original system-font coverage, consistent with W171. No official game sprite.</desc>"]
    alpha = image.getchannel("A")
    for y in range(SIZE[1]):
        x = 0
        while x < SIZE[0]:
            value, end = alpha.getpixel((x, y)), x + 1
            while end < SIZE[0] and alpha.getpixel((end, y)) == value:
                end += 1
            if value:
                lines.append(f'  <rect x="{x}" y="{y}" width="{end-x}" height="1" '
                             f'fill="white" fill-opacity="{value/255:.8f}"/>')
            x = end
    return ("\n".join([*lines, "</svg>"]) + "\n").encode()


def outputs(font_bytes=None):
    if codec.PILLOW_VERSION != "12.3.0" or codec.features.version("freetype2") != "2.14.3":
        raise ValueError("Reproducibility requires Pillow 12.3.0 / FreeType 2.14.3")
    font = codec.FONT.read_bytes() if font_bytes is None else font_bytes
    if hashlib.sha256(font).hexdigest() != codec.FONT_SHA256:
        raise ValueError("Pinned system font changed")
    result, labels = {}, []
    for key, label, layout, max_count, max_ticks in LABELS:
        name = f"perk_{key}_w200"
        texture, model, item, source = paths(key)
        size = (94 if layout == "TIMER" else 118, 24)
        image, bounds, scale = raster_label(font, label, size)
        result.update({
            texture: codec.png(image),
            model: codec.encode({
                "ambientocclusion": False, "gui_light": "front",
                "textures": {"0": f"destiny:item/hud/{name}", "particle": "#0"},
                "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "shade": False,
                              "faces": {face: {"texture": "#0", "uv": [0, 0, 16, 16], "tintindex": 0}
                                        for face in ("north", "south")}}]}),
            item: codec.encode({"model": {
                "type": "minecraft:model", "model": f"destiny:gui/hud/{name}",
                "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}}),
            source: source_svg(image, label, size),
        })
        labels.append({"key": key, "label": label, "icon_id": f"destiny:gui/hud/{name}",
                       "layout": layout, "size": list(size), "alpha_bounds_px": list(bounds),
                       "horizontal_scale": scale, "valid_count": [1, max_count] if max_count else None,
                       "valid_ticks": [1, max_ticks] if max_ticks else None,
                       "timer": "Observed remaining ticks only" if max_ticks else "None; no invented timer",
                       "visibility": {"box_breathing": "Earned original held-source cycle plus validated live ADS and nonempty magazine",
                                      "pulse_monitor": "Actual owned active observer; source may be stowed",
                                      "unrelenting": "Actual owned active recovery observer; no kill-progress label"}[key]})
    pack = [p for key, *_ in LABELS for p in paths(key)[:3]]
    sources = [paths(key)[3] for key, *_ in LABELS]
    result[MANIFEST] = codec.encode({
        "stage": "W200", "font_family": "Arial Narrow Bold", "font_size_px": 22,
        "font_sha256": codec.FONT_SHA256, "layout_engine": "BASIC", "supersampling": codec.SCALE,
        "pillow_version": codec.PILLOW_VERSION, "freetype_version": codec.features.version("freetype2"),
        "provenance": "Original generated system-font coverage matching W183; no official Destiny sprite, ripped asset or bundled font",
        "max_rows": 4, "labels": labels,
        "priority": "All pre-W200 kinds and priorities preserved; Box Breathing, Pulse Monitor, Unrelenting appended",
        "display_policy": "Label and marker only; no invented duration, progress, count, or Opening Shot active row",
        "observers": ["WeaponBoxBreathing.ready", "WeaponPulseMonitor.active", "WeaponUnrelenting.active"],
        "source_policy": "DDC base perk rows; visibility is a server-runtime observation, not an official HUD-layout claim",
        "ddc_snapshot": "/private/tmp/destiny-w190/ddc-perks.html",
        "native_validation": "Pending master central Gradle/Vision; offline generation is not native QA",
        "pack_bytes": sum(len(result[p]) for p in pack),
        "pack_files": {str(p): hashlib.sha256(result[p]).hexdigest() for p in pack},
        "source_files": {str(p): hashlib.sha256(result[p]).hexdigest() for p in sources},
        "generated_paths": [str(p) for p in (*result, MANIFEST)],
    })
    return result


def differences(root, generated):
    return [str(path) for path, data in generated.items()
            if not (root / path).is_file() or (root / path).read_bytes() != data]


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = outputs()

    def test_determinism_owned_coverage_and_font_pin(self):
        self.assertEqual(self.generated, outputs())
        self.assertEqual({MANIFEST, *(p for key, *_ in LABELS for p in paths(key))}, set(self.generated))
        with self.assertRaisesRegex(ValueError, "Pinned system font changed"):
            outputs(b"invalid font control")
        for key, _, layout, *_ in LABELS:
            texture, _, _, source = paths(key)
            image = codec.Image.open(io.BytesIO(self.generated[texture]))
            self.assertEqual((94 if layout == "TIMER" else 118, 24), image.size)
            self.assertEqual("RGBA", image.mode)
            alpha = codec.Image.new("L", image.size)
            for rect in ET.fromstring(self.generated[source]).findall("{http://www.w3.org/2000/svg}rect"):
                x, y, width = (int(rect.attrib[k]) for k in ("x", "y", "width"))
                value = round(float(rect.attrib["fill-opacity"]) * 255)
                for dx in range(width):
                    alpha.putpixel((x + dx, y), value)
            self.assertEqual(image.getchannel("A").tobytes(), alpha.tobytes())
            x0, y0, x1, y1 = alpha.getbbox()
            self.assertTrue(0 < x0 < x1 < image.width and 0 < y0 < y1 < image.height)
            self.assertGreater(sum(a == 255 for a in alpha.tobytes()), 25)

    def test_actual_java_and_resource_mapping(self):
        java = (ROOT / "src/main/java/kim/biryeong/destiny/hud/WeaponPerkRows.java").read_text()
        combat = (ROOT / "src/main/java/kim/biryeong/destiny/hud/CombatHud.java").read_text()
        self.assertIn('Identifier.fromNamespaceAndPath("destiny", "gui/hud/" + image)', combat)
        actual = re.findall(r'(\w+)\("[^"\n]*", "(perk_[^"\n]*_w200)", Layout\.(\w+)\)', java)
        self.assertEqual({(key.upper(), f"perk_{key}_w200", layout) for key, _, layout, *_ in LABELS}, set(actual))
        for key, *_ in LABELS:
            texture, model, item, _ = paths(key)
            graph = json.loads(self.generated[item])["model"]
            self.assertEqual(BASE / ("models/" + graph["model"].split(":")[1] + ".json"), model)
            mapping = json.loads(self.generated[model])
            self.assertEqual(BASE / ("textures/" + mapping["textures"]["0"].split(":")[1] + ".png"), texture)
            self.assertEqual([{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}], graph["tints"])
            for face in mapping["elements"][0]["faces"].values():
                self.assertEqual(0, face["tintindex"])
            self.assertLessEqual(sum(len(self.generated[p]) for p in (texture, model, item)), 16384)
        for digit in range(10):
            self.assertTrue((BASE / f"items/gui/hud/ammo_digit_{digit}.json").is_file())

    def test_readonly_verify_detects_missing_and_corrupt(self):
        generated = self.generated
        root = ROOT / "__in_memory_verification_only__"
        virtual = {root / p: data for p, data in generated.items()}
        texture, _, _, source = paths("box_breathing")
        virtual[root / texture] = b"corrupt control"
        del virtual[root / source]
        with patch.object(Path, "is_file", lambda p: p in virtual), \
             patch.object(Path, "read_bytes", lambda p: virtual[p]), \
             patch.object(Path, "write_bytes", side_effect=AssertionError("verify attempted write")):
            self.assertEqual({str(texture), str(source)}, set(differences(root, generated)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GeneratorTests))
        return 0 if result.wasSuccessful() else 1
    try:
        generated = outputs()
        if args.verify:
            different = differences(ROOT, generated)
            if different:
                parser.exit(1, "W200 output differs (no writes):\n" + "\n".join(different) + "\n")
        else:
            # This batch intentionally writes only the 13 exact generated paths above.
            for path, data in generated.items():
                target = ROOT / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    except (OSError, ValueError) as error:
        parser.exit(1, f"W200: {error}\n")
    print(f"{'verified (read-only)' if args.verify else 'generated'} 13 W200 files; 3 original labels / 9 pack assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
