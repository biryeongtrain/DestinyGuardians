#!/usr/bin/env python3
"""Build the original W171 TAP THE TRIGGER label in the existing 94x24 TIMER slot.

W170 typography: pinned Arial Narrow Bold at 22px, horizontal condensation,
4x supersampling, Pillow 12.3.0 / FreeType 2.14.3. No official sprite or font
is distributed. --verify is read-only; --self-test runs bounded generator tests.
"""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "w108_label_codec", ROOT / "scripts/build_feeding_frenzy_hud_w108.py")
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)

NAME = "perk_tap_the_trigger_w171"
LABEL = "TAP THE TRIGGER"
SIZE = (94, 24)
BASE = Path("src/main/resources/assets/destiny")
ART = Path("art/hud/w171")
TEXTURE = BASE / f"textures/item/hud/{NAME}.png"
MODEL = BASE / f"models/gui/hud/{NAME}.json"
ITEM = BASE / f"items/gui/hud/{NAME}.json"
SOURCE = ART / "tap-the-trigger.svg"
MANIFEST = ART / "manifest.json"
PACK = (TEXTURE, MODEL, ITEM)


def raster_label(font_bytes):
    font = codec.ImageFont.truetype(io.BytesIO(font_bytes), 22 * codec.SCALE,
                                    layout_engine=codec.ImageFont.Layout.BASIC)
    left, top, right, bottom = font.getbbox(LABEL)
    ink = codec.Image.new("L", (right - left, bottom - top))
    codec.ImageDraw.Draw(ink).text((-left, -top), LABEL, font=font, fill=255)
    width = min(ink.width, (SIZE[0] - 2 * codec.PADDING) * codec.SCALE)
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


def source_svg(image):
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE[0]}" height="{SIZE[1]}" '
             f'viewBox="0 0 {SIZE[0]} {SIZE[1]}">',
             f"  <title>{LABEL} - original W171 generated label</title>",
             "  <desc>Original system-font coverage, consistent with W170. No official game sprite.</desc>"]
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
    image, bounds, horizontal_scale = raster_label(font)
    result = {
        TEXTURE: codec.png(image),
        MODEL: codec.encode({
            "ambientocclusion": False, "gui_light": "front",
            "textures": {"0": f"destiny:item/hud/{NAME}", "particle": "#0"},
            "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "shade": False,
                          "faces": {face: {"texture": "#0", "uv": [0, 0, 16, 16], "tintindex": 0}
                                    for face in ("north", "south")}}]}),
        ITEM: codec.encode({"model": {
            "type": "minecraft:model", "model": f"destiny:gui/hud/{NAME}",
            "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}}),
        SOURCE: source_svg(image),
    }
    pack_bytes = sum(len(result[path]) for path in PACK)
    if pack_bytes > 16384:
        raise ValueError("Three-file pack exceeds 16KiB")
    result[MANIFEST] = codec.encode({
        "stage": "W171", "label": LABEL, "size": list(SIZE),
        "font_family": "Arial Narrow Bold", "font_sha256": codec.FONT_SHA256,
        "font_size_px": 22, "horizontal_scale": horizontal_scale, "alpha_bounds_px": list(bounds),
        "pillow_version": codec.PILLOW_VERSION,
        "freetype_version": codec.features.version("freetype2"),
        "layout_engine": "BASIC", "supersampling": codec.SCALE,
        "provenance": "Original generated system-font label, not an official Destiny sprite; "
                      "no ripped asset or bundled font; W170 font, cap height and coverage method",
        "runtime_contract": {
            "icon_id": f"destiny:gui/hud/{NAME}", "layout": "TIMER",
            "valid_ticks": [1, 12], "seconds": "ceil(ticks / 20): 0:01 throughout ticks 1..12; absent at 0",
            "activation": "Observed live remaining ticks only; no manufactured activation or counter",
            "priority": "Reload/utility, after existing fourteen kinds, including PERPETUAL_MOTION",
            "max_rows": 4,
            "node_suffixes": ["marker", "label", "minutes", "colon", "tens", "ones"],
            "marker": "Green utility 0x8DE2AF; gold remains Memento Mori / Honed Edge only",
            "visibility": "Held weapon; hidden rows use current remaining ticks on promotion",
            "layout_limits": "Existing TIMER renderer: label center 168, width 94, height 24; "
                             "marker right 113, label left 121, label right 215, timer left 227; "
                             "8/12-unit gaps; 32-unit row pitch; no native validation claim",
            "native_validation": "Pending master Vision: short timer, expiry, cap promotion, cleanup, readability",
            "integration": "Master owns WeaponPerkHud live adapter; pass actual ticks as twentieth Snapshot argument"},
        "source_facts": ["W170 pinned font, 22px cap-size input, BASIC engine, 4x supersampling",
                         "WeaponPerkHud TIMER slot is 94x24 and marker is green unless Mori/Honed"],
        "local_choices": ["Condense full authored label into existing TIMER slot; 12-tick bound from W171 task contract"],
        "pack_bytes": pack_bytes, "pack_byte_budget": 16384,
        "pack_files": {str(path): hashlib.sha256(result[path]).hexdigest() for path in PACK},
        "source_files": {str(SOURCE): hashlib.sha256(result[SOURCE]).hexdigest()},
        "generated_paths": [str(path) for path in (*result, MANIFEST)],
    })
    return result


def differences(root, generated):
    return [str(path) for path, data in generated.items()
            if not (root / path).is_file() or (root / path).read_bytes() != data]


class GeneratorTests(unittest.TestCase):
    def test_reproducible_five_owned_outputs_and_budget(self):
        first = outputs()
        self.assertEqual(first, outputs())
        self.assertEqual({TEXTURE, MODEL, ITEM, SOURCE, MANIFEST}, set(first))
        self.assertLessEqual(sum(len(first[p]) for p in PACK), 16384)

    def test_coverage_svg_exactly_matches_png(self):
        generated = outputs()
        image = codec.Image.open(io.BytesIO(generated[TEXTURE]))
        self.assertEqual(SIZE, image.size)
        self.assertEqual("RGBA", image.mode)
        reconstructed = codec.Image.new("L", SIZE)
        for rect in ET.fromstring(generated[SOURCE]).findall("{http://www.w3.org/2000/svg}rect"):
            x, y, width = (int(rect.attrib[key]) for key in ("x", "y", "width"))
            alpha = round(float(rect.attrib["fill-opacity"]) * 255)
            for dx in range(width):
                reconstructed.putpixel((x + dx, y), alpha)
        self.assertEqual(image.getchannel("A").tobytes(), reconstructed.tobytes())
        x0, y0, x1, y1 = reconstructed.getbbox()
        self.assertTrue(0 < x0 < x1 < SIZE[0] and 0 < y0 < y1 < SIZE[1])
        self.assertGreater(sum(a == 255 for a in reconstructed.tobytes()), 25)

    def test_resource_graph_and_existing_timer_spacing(self):
        generated = outputs()
        graph = json.loads(generated[ITEM])["model"]
        self.assertEqual(f"destiny:gui/hud/{NAME}", graph["model"])
        self.assertEqual(f"destiny:item/hud/{NAME}", json.loads(generated[MODEL])["textures"]["0"])
        self.assertEqual(8, 168 - SIZE[0] / 2 - (104 + 18 / 2))
        self.assertEqual(12, 232 - 10 / 2 - (168 + SIZE[0] / 2))
        self.assertGreater(32, SIZE[1])

    def test_verify_reports_corrupt_and_missing_without_repair(self):
        generated = outputs()
        with tempfile.TemporaryDirectory(prefix="w171-tap-generator-", dir="/private/tmp") as directory:
            root = Path(directory)
            self.assertEqual(5, len(differences(root, generated)))
            self.assertEqual([], list(root.iterdir()))
            for path, data in generated.items():
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            self.assertEqual([], differences(root, generated))
            (root / TEXTURE).write_bytes(b"corrupted control")
            (root / SOURCE).unlink()
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual({str(TEXTURE), str(SOURCE)}, set(differences(root, generated)))
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def test_modified_font_rejected_before_rasterization(self):
        with self.assertRaisesRegex(ValueError, "Pinned system font changed"):
            outputs(b"invalid font control")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GeneratorTests))
        return 0 if result.wasSuccessful() else 1
    try:
        generated = outputs()
        if args.verify:
            different = differences(args.output_root, generated)
            if different:
                parser.exit(1, "W171 output differs (no writes):\n" + "\n".join(different) + "\n")
        else:
            for path, data in generated.items():
                target = args.output_root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    except (OSError, ValueError) as error:
        parser.exit(1, f"W171: {error}\n")
    print(f"{'verified (read-only)' if args.verify else 'generated'} 5 W171 files; "
          "1 original label / 3 pack assets; 94x24 RGBA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
