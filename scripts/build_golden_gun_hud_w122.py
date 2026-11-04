#!/usr/bin/env python3
"""W122 Golden Gun HUD from the current H29 held-item composite, offline only.

The requested models/item/golden_gun_h29.json is display metadata with NO elements.
Follow SuperVisuals' ITEM_MODEL to items/golden_gun_h29.json instead. Its matrices
map the alpha-cut right-triangle primitive to the actual H29 mesh. Never replace
that mesh by cuboid bounds, Ace, or a generic hand cannon. Bundled Pillow only.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys
import unittest

# Importing must not create an unowned scripts/__pycache__.
sys.dont_write_bytecode = True
import build_weapon_hud_w112 as w112
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
A = w112.ASSETS
ART = Path("art/weapons/w122/golden_gun_hud")
NAME = "ammo_golden_gun_w122"
SOURCE = A / "models/item/golden_gun_h29.json"
ITEM = A / "items/golden_gun_h29.json"
PRIMITIVE = A / "models/mesh/h29/golden_gun_triangle.json"
ATLAS = A / "textures/item/supers/mesh_triangle_h28.png"
MESH = Path("art/mesh/supers/h29/golden_gun.mesh.json")
RUNTIME = Path("src/main/java/kim/biryeong/destiny/fx/SuperVisuals.java")
SESSION = Path("src/main/java/kim/biryeong/destiny/ability/hunter/HunterSuper.java")
PACK = [A / f"items/gui/hud/{NAME}.json", A / f"models/gui/hud/{NAME}.json",
        A / f"textures/item/hud/{NAME}.png"]
METHOD = "union of actual H29 composite alpha-cut triangles; row-major affine matrices; Y yaw180 then W112 upright YZ; 8x BOX coverage"
ORIENTATION = dict(plane="YZ", screen_x="-Z", screen_y="-Y", side_rotation_degrees=180,
                   direction="H29 +Z muzzle points left; +Y stays up", policy="upright_side")


def read(path):
    return w112.json.loads((ROOT / path).read_bytes())


def project(point):
    # H29 source mapping explicitly says muzzle+Z, opposite to ordinary guns.
    x, y, z = point
    return w112.project((-x, y, -z), "gun")


def transform(matrix, point):
    w112.require(isinstance(matrix, list) and len(matrix) == 16 and
                 all(isinstance(v, (int, float)) and math.isfinite(v) for v in matrix), "Invalid affine matrix")
    w112.require(matrix[12:] == [0, 0, 0, 1], "Perspective transform unsupported")
    return tuple(16 * sum(matrix[i * 4 + j] * v for j, v in enumerate((*point, 1))) for i in range(3))


def triangles(item, primitive, atlas):
    w112.require(set(item) == {"model"} and set(item["model"]) == {"type", "models"}
                 and item["model"]["type"] in ("composite", "minecraft:composite"), "Expected held-item composite")
    # Validate the actual alpha-mask primitive, not merely its bounding rectangle.
    e = primitive["elements"]
    w112.require(len(e) == 1 and e[0]["from"] == [-16, 0, 0] and e[0]["to"] == [0, 16, 0]
                 and not e[0].get("rotation") and set(e[0]["faces"]) == {"north", "south"}, "Unsupported H29 primitive")
    w112.corners(e[0])  # Shared W112 vector/face validation.
    for face, uv in (("north", [0, 0, 16, 16]), ("south", [16, 0, 0, 16])):
        w112.require(e[0]["faces"][face] == dict(uv=uv, texture="#0", tintindex=0), "Unsupported triangle UV")
    w112.require(primitive["textures"]["0"] == "destiny:item/supers/mesh_triangle_h28", "Unexpected triangle atlas")
    w112.require(atlas.mode == "RGBA" and atlas.size == (128, 128), "Unexpected triangle atlas dimensions/mode")
    w112.require(all(atlas.getpixel((x, y)) == (255, 255, 255, 255 if x <= y else 0)
                     for y in range(128) for x in range(128)), "Triangle alpha contract changed")
    # North and south UVs cover the SAME spatial triangle. Unit positions follow
    # FaceBakery's /16 coordinates. Matrix origin is the first mesh vertex.
    unit = ((0, 0, 0), (-1, 0, 0), (0, 1, 0))
    result = []
    for child in item["model"]["models"]:
        w112.require(set(child) == {"type", "model", "transformation", "tints"} and
                     child["type"] in ("model", "minecraft:model") and
                     child["model"] == "destiny:mesh/h29/golden_gun_triangle", "Unexpected held model child")
        result.append([transform(child["transformation"], p) for p in unit])
    w112.require(result, "Empty runtime mesh")
    return result


def validate_mesh(actual, mesh):
    w112.require("muzzle+Z" in mesh["coordinate_mapping"], "H29 orientation changed")
    w112.require(len(actual) == len(mesh["triangles"]), "Dropped runtime triangles")
    error = max(abs(a - b) for triangle, record in zip(actual, mesh["triangles"])
                for point, index in zip(triangle, record["v"])
                for a, b in zip(point, mesh["vertices"][index]))
    w112.require(error < 0.00001, f"Runtime/source mesh mismatch: {error}")
    return error


def render(actual):
    faces = [[project(p) for p in triangle] for triangle in actual]
    faces = [p for p in faces if abs(sum(a[0] * b[1] - b[0] * a[1]
             for a, b in zip(p, p[1:] + p[:1]))) > 1e-10]
    w112.require(faces, "No projected triangles")
    bounds = [min(p[0] for f in faces for p in f), min(p[1] for f in faces for p in f),
              max(p[0] for f in faces for p in f), max(p[1] for f in faces for p in f)]
    x0, y0, x1, y1 = bounds
    width, height = w112.SIZE
    scale = min((width - 1 - 2 * w112.PAD) / (x1 - x0), (height - 1 - 2 * w112.PAD) / (y1 - y0))
    offset = [(width - 1 - (x1 - x0) * scale) / 2, (height - 1 - (y1 - y0) * scale) / 2]
    mask = Image.new("L", (width * w112.SS, height * w112.SS), 0)
    draw = ImageDraw.Draw(mask)
    for face in faces:
        draw.polygon([(round(((x - x0) * scale + offset[0]) * w112.SS),
                       round(((y - y0) * scale + offset[1]) * w112.SS)) for x, y in face], fill=255)
    mask = mask.resize(w112.SIZE, Image.Resampling.BOX)
    image = Image.new("RGBA", w112.SIZE, (255, 255, 255, 0))
    image.putalpha(mask)
    bbox = mask.getbbox()
    w112.require(bbox and bbox[0] >= w112.PAD and bbox[1] >= w112.PAD and
                 bbox[2] <= width - w112.PAD and bbox[3] <= height - w112.PAD, "Clipped silhouette")
    return image, dict(triangles=len(actual), projected_triangles=len(faces),
                       projected_bounds=[round(v, 9) for v in bounds], pixels_per_model_unit=round(scale, 9),
                       alpha_bbox=list(bbox), visible_pixels=sum(a > 0 for a in mask.tobytes()),
                       alpha_sha256=w112.sha(mask.tobytes()))


def contact(image):
    sheet = Image.new("RGB", (800, 330), "#18212b")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=14)
    d.text((16, 12), "W122 Golden Gun | current H29 held mesh | OFFLINE geometry evidence", font=font, fill="white")
    d.text((16, 36), "2350 alpha-cut triangles; muzzle left; neutral white; runtime tint stays gold", font=font, fill="#b9c7d4")
    for x, y, size, label in [(16, 95, (480, 192), "3x inspection"), (520, 95, (160, 64), "160x64 texture"),
                                (520, 216, (80, 32), "80x32 selected quad")]:
        d.text((x, y - 24), label, font=font, fill="white")
        im = image.resize(size, Image.Resampling.NEAREST if size[0] > 160 else Image.Resampling.BOX)
        sheet.paste(im, (x, y), im)
    d.text((16, 307), "Geometry projection; ideal triangle alpha boundary; no native framebuffer or gameplay claim.", font=font, fill="#b9c7d4")
    return sheet


def build():
    metadata = read(SOURCE)
    w112.require(metadata.get("elements") == [], "H29 metadata gained geometry; review runtime path")
    w112.require('case SOLAR -> "golden_gun_h29"' in (ROOT / RUNTIME).read_text() and
                 "handItem(kim.biryeong.destiny.fx.SuperVisuals.item(element()))" in (ROOT / SESSION).read_text(), "Held-model binding changed")
    with Image.open(ROOT / ATLAS) as atlas:
        actual = triangles(read(ITEM), read(PRIMITIVE), atlas)
    error = validate_mesh(actual, read(MESH))
    image, stats = render(actual)
    # Reuse W112's complete tint-index-0 explicit HUD transport, not its catalog.
    item, model = w112.transport("unused")
    item["model"]["model"] = "destiny:gui/hud/" + NAME
    model["textures"]["layer0"] = "destiny:item/hud/" + NAME
    outputs = dict(zip(PACK, (w112.json_bytes(item), w112.json_bytes(model), w112.png_bytes(image))))
    outputs[ART / "contact.png"] = w112.png_bytes(contact(image))
    inputs = [SOURCE, ITEM, PRIMITIVE, ATLAS, MESH, RUNTIME, SESSION,
              Path("scripts/build_weapon_hud_w112.py"), Path("scripts/build_golden_gun_hud_w122.py"),
              A / "items/gui/hud/ammo_hand_cannon.json", A / "models/gui/hud/ammo_hand_cannon.json"]
    manifest = dict(schema=1, batch="W122", id="golden_gun", source_model=SOURCE.as_posix(),
                    source_sha256=w112.sha((ROOT / SOURCE).read_bytes()), runtime_item=ITEM.as_posix(),
                    runtime_primitive=PRIMITIVE.as_posix(), source_model_role="display metadata; empty elements; not held geometry",
                    runtime_path="HunterSuper.GoldenGun -> SuperVisuals.item(SOLAR) -> destiny:golden_gun_h29 -> composite -> destiny:mesh/h29/golden_gun_triangle",
                    source_mesh=MESH.as_posix(), max_runtime_mesh_vertex_error=error,
                    method=METHOD, orientation=ORIENTATION, texture_size=list(w112.SIZE), selected_quad_size=[80, 32],
                    padding_pixels=w112.PAD, supersampling=w112.SS, pillow_version=w112.PIL.__version__,
                    alpha_policy="Neutral RGB white including transparent pixels; union of analytic right triangles validated against current 128x128 x<=y atlas; 8x BOX edge coverage; no source color",
                    framing="Same W112 uniform fit and >=4 clear pixels, yaw180 for H29 muzzle+Z; no hull, dilation, rectangle filling or aspect stretch",
                    provenance="Current H29 Bungie Eyasluna-derived product geometry; see existing H29 provenance; not extracted official HUD art or native QA",
                    **stats, inputs_sha256={p.as_posix(): w112.sha((ROOT / p).read_bytes()) for p in inputs},
                    outputs_sha256={p.as_posix(): w112.sha(b) for p, b in outputs.items()})
    outputs[ART / "manifest.json"] = w112.json_bytes(manifest)
    return outputs


class GoldenGunTest(unittest.TestCase):
    def actual(self):
        with Image.open(ROOT / ATLAS) as atlas:
            return triangles(read(ITEM), read(PRIMITIVE), atlas)

    def test_all_actual_runtime_vertices_match_independent_mesh(self):
        self.assertLess(validate_mesh(self.actual(), read(MESH)), 1e-5)

    def test_row_major_translation_and_direction(self):
        matrix = [1, 0, 0, 2, 0, 1, 0, 3, 0, 0, 1, 4, 0, 0, 0, 1]
        self.assertEqual((48, 80, 112), transform(matrix, (1, 2, 3)))
        self.assertEqual((-7, -5), project((3, 5, 7)))

    def test_triangle_does_not_fill_primitive_rectangle(self):
        image, _ = render([[(0, 0, 0), (0, 0, 10), (0, 10, 0)]])
        self.assertEqual(0, image.getpixel((60, 10))[3])
        self.assertEqual(255, image.getpixel((98, 48))[3])

    def test_reject_perspective_nonfinite_and_wrong_primitive(self):
        for m in ([0] * 16, [float('nan')] * 16, [1, 2]):
            with self.assertRaises(ValueError): transform(m, (0, 0, 0))
        item = read(ITEM); item['model']['models'][0]['model'] = 'destiny:item/weapon/ace_of_spades'
        with Image.open(ROOT / ATLAS) as atlas:
            with self.assertRaises(ValueError): triangles(item, read(PRIMITIVE), atlas)

    def test_reject_opaque_rectangular_atlas(self):
        with self.assertRaises(ValueError):
            triangles(read(ITEM), read(PRIMITIVE), Image.new('RGBA', (128, 128), 'white'))

    def test_mesh_oracle_rejects_perturbed_runtime(self):
        actual = self.actual(); actual[0][0] = (0, 0, 0)
        with self.assertRaises(ValueError): validate_mesh(actual, read(MESH))

    def test_current_mask_distinct_from_ace_and_generic(self):
        image, _ = render(self.actual())
        for name in ('ammo_weapon_w112_ace_of_spades', 'ammo_hand_cannon'):
            with Image.open(ROOT / A / f'textures/item/hud/{name}.png') as other:
                self.assertNotEqual(image.getchannel('A').tobytes(), other.getchannel('A').tobytes())

    def test_build_is_deterministic_and_exactly_five_owned_outputs(self):
        first = build(); self.assertEqual(first, build())
        self.assertEqual(set(PACK + [ART / 'contact.png', ART / 'manifest.json']), set(first))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('command', nargs='?', choices=['build'])
    mode.add_argument('--verify', action='store_true')
    mode.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(w112.ProjectionTest),
                                    unittest.defaultTestLoader.loadTestsFromTestCase(GoldenGunTest)])
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1
    outputs = build()
    if args.verify:
        stale = [str(p) for p, b in outputs.items() if not (ROOT / p).is_file() or (ROOT / p).read_bytes() != b]
        w112.require(not stale, 'Stale/missing W122 outputs: ' + ', '.join(stale))
    else:
        for p, b in outputs.items():
            (ROOT / p).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / p).write_bytes(b)
    print(f"W122 {'verified' if args.verify else 'generated'}: 2350 runtime triangles; 3 pack files + manifest/contact; offline only")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
