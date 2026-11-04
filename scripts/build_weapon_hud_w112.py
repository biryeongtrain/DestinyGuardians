#!/usr/bin/env python3
"""W112: neutral HUD masks from the CURRENT selected weapon cuboid geometry.

Run with the bundled Pillow Python. --verify recomputes every byte without writing;
--self-test exercises geometry independently. No network, subprocess or game runtime.
This is a projection of original-derived product models, NOT extracted D2 HUD art.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import unittest

import PIL
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path("src/main/resources/assets/destiny")
HUD = Path("art/weapons/w112/hud")
SIZE = (160, 64)
PAD = 4
SS = 8
CATALOGS = [Path("src/main/resources/destiny/weapons") / f for f in
            ("w30.json", "w83-exotics.json", "w84-exotics.json")]
METHOD = "orthographic union of each present cuboid face; native element Rz*Ry*Rx (26.3 EulerXYZ); 8x BOX coverage"
FACE_CORNERS = {
    "west": (0, 1, 3, 2), "east": (4, 6, 7, 5),
    "down": (0, 4, 5, 1), "up": (2, 3, 7, 6),
    "north": (0, 2, 6, 4), "south": (1, 5, 7, 3),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads((ROOT / path).read_text())


def json_bytes(data):
    return (json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def png_bytes(image):
    out = io.BytesIO()
    image.save(out, "PNG", compress_level=9, optimize=False)
    return out.getvalue()


def catalog():
    rows = read_json(CATALOGS[0])
    require(len(rows) == 63, "W30 must contain exactly 63 selected entries")
    for path, expected in zip(CATALOGS[1:], ("ace_of_spades", "izanagis_burden")):
        extra = [r["catalog"] for r in read_json(path)]
        require([r["id"] for r in extra] == [expected], f"Unexpected exotic catalog: {path}")
        rows += extra
    require(len({r["id"] for r in rows}) == 65, "Duplicate or missing catalog IDs")
    return rows


def canonical_source_path(row):
    # Historical baseline for W118 engine fixtures, not the default product.
    base = ("item/weapon/" if row["id"] in ("ace_of_spades", "izanagis_burden")
            else "weapon/" + row["family"] + "/")
    return ASSETS / ("models/" + base + row["id"] + ".json")


SURFACE_MANIFEST = Path("src/main/resources/weapon_surface_w123/manifest.json")


def active_rules():
    """Resolve the default emitted pack, never unregistered candidate files.

    Diagnostic -Ddestiny.weapon.surface.w115=true is not the shipped HUD profile.
    Fail on stale declared inputs rather than silently using old geometry.
    """
    manifest = read_json(SURFACE_MANIFEST)
    require(manifest.get("schema") == 1 and manifest.get("stage") == "W123",
            "Unsupported active surface migration")
    rules = {}
    for rule in manifest["targets"]:
        path = Path("src/main/resources") / rule["path"]
        replacement = Path("src/main/resources") / rule["replacement"]
        require(rule["path"].startswith("assets/destiny/models/") and
                rule["replacement"] == "assets/destiny/models/weapon_surface_w123/" + path.name
                and ".." not in path.parts and path not in rules, "Invalid/duplicate migration target")
        require(sha((ROOT / path).read_bytes()) == rule["sourceSha256"],
                "Stale canonical migration source: " + str(path))
        require(sha((ROOT / replacement).read_bytes()) == rule["replacementSha256"],
                "Stale active migration replacement: " + str(replacement))
        rules[path] = replacement
    return rules


def source_path(row, rules=None):
    canonical = canonical_source_path(row)
    return (active_rules() if rules is None else rules).get(canonical, canonical)


def rotate(point, angles):
    """Rz * Ry * Rx: local X, then Y, then Z, for native ELEMENT geometry.

    Installed 26.3 CuboidRotation.EulerXYZRotation.transformation() calls
    Matrix4f.rotationZYX(z, y, x). ItemTransform is a different transform.
    The old Z-first assertion tested our assumption, not the engine; W118
    compares all eight corners with the actual element parser/FaceBakery.
    """
    x, y, z = point
    a, b, c = map(math.radians, angles)
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
    return x, y, z


def vector(value):
    require(isinstance(value, list) and len(value) == 3 and
            all(isinstance(v, (float, int)) and math.isfinite(v) for v in value),
            f"Invalid 3D vector: {value}")
    return value


def corners(element):
    require(set(element) <= {"from", "to", "faces", "rotation", "shade", "light_emission", "name"},
            f"Unsupported element fields: {set(element)}")
    require(element.get("faces") and set(element["faces"]) <= FACE_CORNERS.keys(),
            "Unsupported or absent cube faces")
    lo, hi = vector(element["from"]), vector(element["to"])
    require(all(a <= b for a, b in zip(lo, hi)), "Inverted cuboid")
    points = list(itertools.product(*zip(lo, hi)))
    rotation = element.get("rotation")
    if rotation:
        require(isinstance(rotation, dict), "Unsupported rotation type")
        if "axis" in rotation:
            require(set(rotation) <= {"origin", "axis", "angle", "rescale"}, "Unsupported axis rotation")
            require(rotation["axis"] in "xyz" and len(rotation["axis"]) == 1, "Invalid rotation axis")
            angles = [rotation["angle"] if a == rotation["axis"] else 0 for a in "xyz"]
        else:
            require(set(rotation) <= {"origin", "x", "y", "z", "rescale"}, "Unsupported native rotation")
            angles = [rotation.get(a, 0) for a in "xyz"]
        vector(angles)
        origin = vector(rotation["origin"])
        require(isinstance(rotation.get("rescale", False), bool), "Invalid rescale")
        factors = [1., 1., 1.]
        if rotation.get("rescale"):
            nonzero = [i for i, a in enumerate(angles) if a]
            require(len(nonzero) <= 1, "Multi-axis rescale is unsupported, refusing approximation")
            if nonzero:
                axis = nonzero[0]
                require(abs(angles[axis]) in (22.5, 45), "Unsupported rescale angle")
                factors = [1 if i == axis else 1 / math.cos(math.radians(angles[axis])) for i in range(3)]
        points = [tuple(o + v * s for o, v, s in zip(origin, rotate(
            [v - o for v, o in zip(p, origin)], angles), factors)) for p in points]
    return points


def orientation(family):
    if family in ("sword", "glaive"):
        return dict(plane="YZ", screen_x="+Y", screen_y="+Z", side_rotation_degrees=90,
                    direction="+Y blade/head points right", policy="horizontal_melee")
    return dict(plane="YZ", screen_x="+Z", screen_y="-Y", side_rotation_degrees=0,
                direction="-Z muzzle/arrow points left; +Y stays up", policy="upright_side")


def project(point, family):
    _, y, z = point
    return (y, z) if family in ("sword", "glaive") else (z, -y)


def polygons(model, family):
    require(set(model) <= {"credit", "ambientocclusion", "gui_light", "textures", "elements", "display"},
            f"Unsupported model fields (mesh/parent not approximated): {set(model)}")
    require(model.get("elements"), "No explicit cuboid elements")
    result, all_points = [], []
    face_count = 0
    for element in model["elements"]:
        points = [project(p, family) for p in corners(element)]
        for face in element["faces"]:
            face_count += 1
            poly = [points[i] for i in FACE_CORNERS[face]]
            area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
            # Edge-on and zero-thickness faces have no coverage. Do not draw a
            # line or an element bounding rectangle that could bridge a hole.
            if abs(area) > 1e-10:
                result.append(poly)
                all_points.extend(poly)
    require(result, "No projected faces")
    bounds = [min(p[0] for p in all_points), min(p[1] for p in all_points),
              max(p[0] for p in all_points), max(p[1] for p in all_points)]
    return result, bounds, face_count


def render(model, family):
    faces, bounds, face_count = polygons(model, family)
    x0, y0, x1, y1 = bounds
    require(x1 > x0 and y1 > y0, "Degenerate silhouette")
    # Pixel centers span [0, size-1]; reserve the full four clear border pixels.
    scale = min((SIZE[0] - 1 - 2 * PAD) / (x1 - x0), (SIZE[1] - 1 - 2 * PAD) / (y1 - y0))
    offset = [(SIZE[0] - 1 - (x1 - x0) * scale) / 2, (SIZE[1] - 1 - (y1 - y0) * scale) / 2]
    mask = Image.new("L", tuple(s * SS for s in SIZE), 0)
    draw = ImageDraw.Draw(mask)
    for poly in faces:
        draw.polygon([(round(((x - x0) * scale + offset[0]) * SS),
                       round(((y - y0) * scale + offset[1]) * SS)) for x, y in poly], fill=255)
    mask = mask.resize(SIZE, Image.Resampling.BOX)
    image = Image.new("RGBA", SIZE, (255, 255, 255, 0))
    image.putalpha(mask)
    bbox = mask.getbbox()
    require(bbox and bbox[0] >= PAD and bbox[1] >= PAD and
            bbox[2] <= SIZE[0] - PAD and bbox[3] <= SIZE[1] - PAD, "Clipped silhouette")
    stats = dict(elements=len(model["elements"]), source_faces=face_count, projected_faces=len(faces),
                 rotated_elements=sum(bool(e.get("rotation")) for e in model["elements"]),
                 projected_bounds=[round(v, 9) for v in bounds], pixels_per_model_unit=round(scale, 9),
                 alpha_bbox=list(bbox), visible_pixels=sum(v > 0 for v in mask.tobytes()),
                 alpha_sha256=sha(mask.tobytes()))
    return image, stats


def pack_paths(id):
    name = "ammo_weapon_w112_" + id
    return [ASSETS / f"items/gui/hud/{name}.json", ASSETS / f"models/gui/hud/{name}.json",
            ASSETS / f"textures/item/hud/{name}.png"]


def transport(id):
    name = "ammo_weapon_w112_" + id
    item = read_json(ASSETS / "items/gui/hud/ammo_hand_cannon.json")
    item["model"]["model"] = "destiny:gui/hud/" + name
    model = read_json(ASSETS / "models/gui/hud/ammo_hand_cannon.json")
    model["textures"]["layer0"] = "destiny:item/hud/" + name
    # Explicit cuboid HUD quads have no generated-item parent to supply this.
    # ResolvedModel requests particle even when every face resolves layer0.
    model["textures"]["particle"] = "#layer0"
    return item, model


def contact_sheet(rows, images):
    # Full texture plus the selected 80x32 product quad size, at 1:1 pixels.
    sheet = Image.new("RGB", (1600, 54 + 13 * 124), "#18212b")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=12)
    draw.text((12, 8), "W112 | 65 CURRENT model side projections | texture 160x64 + selected quad 80x32", font=font, fill="#ffffff")
    draw.text((12, 29), "White/alpha geometry masks. Original-derived product geometry; not extracted Destiny 2 HUD sprites.", font=font, fill="#b9c7d4")
    for i, (row, image) in enumerate(zip(rows, images)):
        x, y = (i % 5) * 320, 54 + (i // 5) * 124
        draw.rectangle((x + 1, y + 1, x + 318, y + 122), fill="#25313e")
        draw.text((x + 8, y + 5), f"{i+1:02} {row['id']}", font=font, fill="#ffffff")
        draw.text((x + 8, y + 23), row["family"], font=font, fill="#a5bbc9")
        sheet.paste(image, (x + 8, y + 47), image)
        small = image.resize((80, 32), Image.Resampling.BOX)
        sheet.paste(small, (x + 217, y + 63), small)
    return sheet


def build():
    rows = catalog()
    rules = active_rules()
    outputs, records, images, family_masks = {}, [], [], {}
    for row in rows:
        path = source_path(row, rules)
        source = (ROOT / path).read_bytes()
        image, stats = render(json.loads(source), row["family"])
        key = (row["family"], stats["alpha_sha256"])
        require(key not in family_masks, f"Duplicate same-family silhouette: {row['id']} / {family_masks.get(key)}")
        family_masks[key] = row["id"]
        paths = pack_paths(row["id"])
        item, model = transport(row["id"])
        data = [json_bytes(item), json_bytes(model), png_bytes(image)]
        outputs.update(zip(paths, data))
        records.append(dict(id=row["id"], family=row["family"], source_model=path.as_posix(),
                            source_sha256=sha(source), canonical_model=canonical_source_path(row).as_posix(),
                            source_profile="default W123 pack migration" if path != canonical_source_path(row) else "canonical unchanged",
                            method=METHOD, orientation=orientation(row["family"]),
                            **stats, pack_files={p.as_posix(): sha(v) for p, v in zip(paths, data)}))
        images.append(image)
    outputs[HUD / "contact-sheet.png"] = png_bytes(contact_sheet(rows, images))
    inputs = CATALOGS + [ASSETS / "items/gui/hud/ammo_hand_cannon.json",
                        ASSETS / "models/gui/hud/ammo_hand_cannon.json", Path("scripts/build_weapon_hud_w112.py"), SURFACE_MANIFEST]
    manifest = dict(schema=1, batch="W112", count=65, texture_size=list(SIZE), selected_quad_size=[80, 32],
                    padding_pixels=PAD, supersampling=SS, pillow_version=PIL.__version__,
                    provenance="Derived from current original-derived product cuboids, including supplied Ace/Izanagi; not official extracted D2 HUD sprites",
                    source_layout="Default pack: declared active W123 full replacements, otherwise canonical W30/W83/W84. Diagnostic legacy W115 opt-in excluded.",
                    method=METHOD, alpha_policy="Union of present geometric faces, opaque neutral white with antialiased coverage; source material color/UV opacity intentionally excluded",
                    framing="Uniform scale from actual rotated projected face bounds, centered with >=4 clear pixels on all edges; no hull, dilation, family substitution or aspect stretch",
                    family_policy={"default": orientation("gun"), "sword": orientation("sword"), "glaive": orientation("glaive"),
                                   "bow": orientation("bow")},
                    unsupported_policy="Fail on mesh, parent inheritance, unknown geometry or unsupported rotation; never substitute",
                    inputs_sha256={p.as_posix(): sha((ROOT / p).read_bytes()) for p in inputs},
                    contact_sheet_sha256=sha(outputs[HUD / "contact-sheet.png"]), weapons=records)
    outputs[HUD / "manifest.json"] = json_bytes(manifest)
    return outputs


def cube(lo, hi, rotation=None):
    result = {"from": lo, "to": hi, "faces": {f: {"texture": "#0"} for f in FACE_CORNERS}}
    if rotation:
        result["rotation"] = rotation
    return result


class ProjectionTest(unittest.TestCase):
    def test_cube_exact_yz_bounds(self):
        _, bounds, count = polygons({"elements": [cube([0, 1, 2], [3, 5, 9])]}, "gun")
        self.assertEqual([2, -5, 9, -1], bounds)
        self.assertEqual(6, count)

    def test_native_rotation_changes_face_vertices(self):
        el = cube([0, 0, 0], [2, 4, 8], dict(origin=[0, 0, 0], x=90, y=0, z=0, rescale=False))
        _, bounds, _ = polygons({"elements": [el]}, "gun")
        for a, b in zip([0, 0, 4, 8], bounds):
            self.assertAlmostEqual(a, b)

    def test_native_element_local_x_then_y_then_z(self):
        # Native rotationZYX maps this point to -Z. Old Rx*Ry*Rz gives +Z.
        p = rotate((1, 0, 0), (90, 90, 90))
        for a, b in zip((0, 0, -1), p):
            self.assertAlmostEqual(a, b)
        self.assertGreater(math.dist((0, 0, 1), p), 1.9)

    def test_axis_rotation_rescale(self):
        points = corners(cube([0, 0, 0], [1, 1, 1], dict(origin=[0, 0, 0], axis="x", angle=45, rescale=True)))
        self.assertAlmostEqual(2, max(p[2] for p in points))

    def test_hole_stays_empty(self):
        bars = [cube([0, 0, 0], [1, 1, 10]), cube([0, 9, 0], [1, 10, 10]),
                cube([0, 1, 0], [1, 9, 1]), cube([0, 1, 9], [1, 9, 10])]
        im, _ = render({"elements": bars}, "gun")
        self.assertEqual((255, 255, 255, 0), im.getpixel((80, 32)))
        self.assertEqual(255, im.getpixel((80, 5))[3])

    def test_only_present_faces(self):
        el = cube([0, 0, 0], [1, 2, 3])
        el["faces"] = {"north": {"texture": "#0"}}
        with self.assertRaisesRegex(ValueError, "No projected faces"):
            polygons({"elements": [el]}, "gun")

    def test_reject_unknown_geometry(self):
        for model in ({"elements": [dict(type="mesh", vertices={})]}, {"parent": "x"},
                      {"elements": [cube([0, 0, 0], [1, 2, 3])], "meshes": []}):
            with self.assertRaises(ValueError):
                polygons(model, "gun")

    def test_melee_family_policy_only(self):
        self.assertEqual((3, -2), project((1, 2, 3), "gun"))
        self.assertEqual((3, -2), project((1, 2, 3), "bow"))
        for family in ("sword", "glaive"):
            self.assertEqual((2, 3), project((1, 2, 3), family))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProjectionTest))
        raise SystemExit(0 if result.wasSuccessful() else 1)
    outputs = build()
    expected_pack = {p for p in outputs if str(p).startswith(str(ASSETS))}
    actual_pack = {p.relative_to(ROOT) for directory in ("items/gui/hud", "models/gui/hud", "textures/item/hud")
                   for p in (ROOT / ASSETS / directory).glob("ammo_weapon_w112_*")}
    require(not (actual_pack - expected_pack), f"Unexpected W112 variants: {actual_pack - expected_pack}")
    if args.verify:
        bad = [str(p) for p, data in outputs.items() if not (ROOT / p).is_file() or (ROOT / p).read_bytes() != data]
        require(not bad, "Stale or missing outputs: " + ", ".join(bad))
    else:
        for path, data in outputs.items():
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / path).write_bytes(data)
    print(f"W112 {'verified' if args.verify else 'generated'}: 65 source models, 195 pack files + manifest/contact sheet; geometry-only evidence")


if __name__ == "__main__":
    main()
