#!/usr/bin/env python3
"""Author original, opaque H25 energy cuboids and matching editable Blockbench sources.

Requires Pillow. Run with --verify to regenerate in memory and compare all 12 outputs
byte for byte without writing. No existing asset is used as a template or modified.
The .bbmodel files are deterministic authoring sources, not native codec exports:
the earlier read-only Blockbench MCP request timed out, so no native success is claimed.
Filament centerlines run from raw (8,8,8) to (8,8,-8), with identity fixed display.
"""

import argparse
import base64
import io
import itertools
import json
import math
from pathlib import Path
import uuid

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
ART = ROOT / "art/blockbench/vfx_h25"
SIDES = ("north", "east", "south", "west", "up", "down")
SIZE = 64
NAMES = ("arc_filament_h25", "void_filament_h25", "void_spark_h25")


def uid(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "destiny:vfx:h25:" + label))


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def atlas(arc):
    # Four full-height swatches: charged edge, exposed spine, branch, shard edge.
    # Integer hash grain and stepped longitudinal pulses require no random seed.
    colors = ([(44, 151, 255), (226, 251, 255), (105, 208, 255), (25, 97, 234)]
              if arc else [(143, 57, 244), (237, 215, 255), (189, 126, 255), (91, 36, 186)])
    image = Image.new("RGB", (SIZE, SIZE))
    for y in range(SIZE):
        for x in range(SIZE):
            swatch, u = divmod(x, 16)
            ridge = 10 - abs(2 * u - 15)
            grain = ((x * 19 + y * 31 + (x * y) % 17) % 9) - 4
            pulse = 8 if (y + swatch * 5) % 23 < 3 else 0
            image.putpixel((x, y), tuple(max(0, min(255, c + ridge + grain + pulse))
                                        for c in colors[swatch]))
    stream = io.BytesIO()
    image.save(stream, format="PNG", compress_level=9)
    return stream.getvalue()


class Energy:
    def __init__(self, name):
        self.name = name
        self.elements = []
        self.saved = []
        self.groups = {}

    def box(self, name, center, size, material, group, axis="y", angle=0):
        center = [round(v, 9) for v in center]
        lo = [round(c - s / 2, 9) for c, s in zip(center, size)]
        hi = [round(c + s / 2, 9) for c, s in zip(center, size)]
        # Half-pixel inset avoids bleeding into adjacent opaque color swatches.
        pixel_uv = [material * 16 + .5, .5, material * 16 + 15.5, 63.5]
        faces = {side: {"uv": [v / 4 for v in pixel_uv], "texture": "#0"} for side in SIDES}
        element = {"name": name, "from": lo, "to": hi, "faces": faces,
                   "shade": False, "light_emission": 15}
        rotation = [0, 0, 0]
        if angle:
            rotation["xyz".index(axis)] = round(angle, 9)
            element["rotation"] = {"axis": axis, "angle": round(angle, 9), "origin": center}
        self.elements.append(element)
        saved = {"name": name, "type": "cube", "uuid": uid(self.name + ":" + name),
                 "from": lo, "to": hi, "origin": center, "rotation": rotation,
                 "box_uv": False, "autouv": 0, "rescale": False, "export": True,
                 "shade": False, "light_emission": 15,
                 "faces": {side: {"uv": pixel_uv, "texture": 0} for side in SIDES}}
        self.saved.append(saved)
        self.groups.setdefault(group, []).append(saved["uuid"])

    def segment(self, name, a, b, width, depth, material, group, plane="z"):
        center = [(x + y) / 2 for x, y in zip(a, b)]
        dx, dy, dz = (x - y for x, y in zip(a, b))
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if plane == "xy":
            assert dz == 0
            size = (width, length, depth)
            axis, angle = "z", -math.degrees(math.atan2(dx, dy))
        elif dy == 0:
            size = (width, depth, length)
            axis, angle = "y", math.degrees(math.atan2(dx, dz))
        else:
            assert dx == 0, "Use one native rotation axis per cuboid"
            size = (width, depth, length)
            axis, angle = "x", math.degrees(math.atan2(-dy, dz))
        self.box(name, center, size, material, group, axis, angle)

    def ribbon(self, name, a, b, width, depth, material=0, group="filament", plane="z"):
        self.segment(name + "_outer", a, b, width, depth, material, group, plane)
        # The pale stripe protrudes through BOTH ribbon faces instead of disappearing
        # inside an opaque outer cuboid. Blue/violet shoulders remain visible.
        self.segment(name + "_spine", a, b, width * .34, depth * 1.24, 1, group, plane)

    def outputs(self):
        png = atlas(self.name.startswith("arc"))
        texture = f"destiny:item/fx/{self.name}"
        display = {"fixed": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]}}
        credit = "Original H25 procedural energy geometry and atlas; Codex deterministic authoring"
        model = {"format_version": "1.21.11", "credit": credit, "ambientocclusion": False,
                 "texture_size": [SIZE, SIZE], "textures": {"0": texture, "particle": texture},
                 "elements": self.elements, "display": display}
        groups = [{"name": name, "uuid": uid(self.name + ":group:" + name),
                   "origin": [8, 8, 8], "rotation": [0, 0, 0], "export": True}
                  for name in self.groups]
        bb = {"meta": {"format_version": "5.0", "model_format": "java_block", "box_uv": False},
              "name": self.name, "model_identifier": self.name, "java_block_version": "1.21.11",
              "credit": credit, "ambientocclusion": False, "resolution": {"width": SIZE, "height": SIZE},
              "ai_used": True, "ai_agents": "Codex H25 deterministic authoring",
              "elements": self.saved, "groups": groups,
              "outliner": [{"uuid": g["uuid"], "children": self.groups[g["name"]]} for g in groups],
              "textures": [{"name": self.name + ".png", "uuid": uid(self.name + ":texture"),
                            "id": "0", "namespace": "destiny", "folder": "item/fx",
                            "width": SIZE, "height": SIZE, "uv_width": SIZE, "uv_height": SIZE,
                            "particle": True, "render_mode": "default", "render_sides": "auto",
                            "visible": True, "internal": True, "saved": False,
                            "source": "data:image/png;base64," + base64.b64encode(png).decode()}],
              "display": display}
        validate(model, bb, png, self.name)
        return {ASSETS / f"models/fx/{self.name}.json": encoded(model),
                ASSETS / f"items/fx/{self.name}.json": encoded({"model": {"type": "minecraft:model", "model": f"destiny:fx/{self.name}"}}),
                ASSETS / f"textures/item/fx/{self.name}.png": png,
                ART / f"{self.name}.bbmodel": encoded(bb)}


def corners(element):
    r = element.get("rotation", {"axis": "y", "angle": 0, "origin": [0, 0, 0]})
    axis = "xyz".index(r["axis"])
    u, v = ((1, 2), (2, 0), (0, 1))[axis]
    cosine, sine = math.cos(math.radians(r["angle"])), math.sin(math.radians(r["angle"]))
    for p in itertools.product(*zip(element["from"], element["to"])):
        q = [x - y for x, y in zip(p, r["origin"])]
        q[u], q[v] = q[u] * cosine - q[v] * sine, q[u] * sine + q[v] * cosine
        yield [x + y for x, y in zip(q, r["origin"])]


def validate(model, bb, png, name):
    elements = model["elements"]
    assert 0 < len(elements) <= 36
    assert len(elements) == len(bb["elements"])
    image = Image.open(io.BytesIO(png))
    assert image.size == (SIZE, SIZE) and image.mode == "RGB"
    assert base64.b64decode(bb["textures"][0]["source"].split(",", 1)[1]) == png
    points = [p for e in elements for p in corners(e)]
    if "filament" in name:
        for axis in (0, 1):
            assert max(p[axis] for p in points) - min(p[axis] for p in points) <= 1.6
            assert max(abs(p[axis] - 8) for p in points) <= .8
        assert abs(min(p[2] for p in points) + 8) < 1e-7
        assert abs(max(p[2] for p in points) - 8) < 1e-7
    else:
        for axis in range(3):
            assert max(abs(p[axis] - 8) for p in points) <= .96 + 1e-7
    for e, b in zip(elements, bb["elements"]):
        assert e["from"] == b["from"] and e["to"] == b["to"]
        assert all(a < z for a, z in zip(e["from"], e["to"]))
        assert e["light_emission"] == 15 and not e["shade"]
        for side, face in e["faces"].items():
            assert all(0 <= u <= 16 for u in face["uv"])
            assert b["faces"][side]["uv"] == [u * 4 for u in face["uv"]]


def generate():
    arc = Energy(NAMES[0])
    zs = [8, 6.9, 5.6, 4.2, 2.9, 1.5, .2, -1.1, -2.5, -3.8, -5.3, -6.9, -8]
    offsets = [0, 0, -.29, .32, -.18, .36, -.31, .26, -.34, .29, -.18, 0, 0]
    points = [(8 + x, 8, z) for x, z in zip(offsets, zs)]
    for i, (a, b) in enumerate(zip(points, points[1:])):
        arc.ribbon(f"main_{i:02}", a, b, .17 + (i % 3) * .018, .12)
    for branch, chain in enumerate([
        [points[3], (8.65, 8, 3.65), (8.47, 8, 3.12)],
        [points[8], (7.66, 8.48, -3.04), (7.66, 8.30, -3.72)],
    ]):
        for i, (a, b) in enumerate(zip(chain, chain[1:])):
            arc.ribbon(f"branch_{branch}_{i}", a, b, .08 - i * .025, .06, 2, "branches")

    void = Energy(NAMES[1])
    offsets = [0, 0, .16, .36, .49, .33, -.10, -.37, -.48, -.29, -.10, 0, 0]
    points = [(8 + x, 8, z) for x, z in zip(offsets, zs)]
    for i, (a, b) in enumerate(zip(points, points[1:])):
        void.ribbon(f"main_{i:02}", a, b, .20 + (i % 3) * .012, .14)
    for i, (x, y, z, angle) in enumerate([(7.39, 8.23, 1.15, -28), (8.61, 7.80, -3.55, 34)]):
        void.box(f"fragment_{i}_shard", (x, y, z), (.10, .46, .12), 2, "fragments", "z", angle)
        void.box(f"fragment_{i}_glint", (x, y, z), (.034, .32, .154), 1, "fragments", "z", angle)

    spark = Energy(NAMES[2])
    diamond = [(8, 8.70, 8), (8.57, 8, 8), (8, 7.30, 8), (7.43, 8, 8), (8, 8.70, 8)]
    for i, (a, b) in enumerate(zip(diamond, diamond[1:])):
        spark.ribbon(f"diamond_edge_{i}", a, b, .084, .11, 0, "diamond", "xy")
    for axis in (0, 1):
        for sign in (-1, 1):
            for i, (start, end, width) in enumerate([(.12, .58, .16), (.58, .96, .052)]):
                a, b = [8, 8, 8], [8, 8, 8]
                a[axis] += sign * start
                b[axis] += sign * end
                spark.ribbon(f"star_arm_{axis}_{sign}_{i}", a, b, width, .13, 2, "star_arms", "xy")
    spark.box("central_violet_facet", (8, 8, 8), (.29, .29, .18), 0, "nucleus", "z", 45)
    spark.box("central_lavender_glint", (8, 8, 8), (.10, .24, .23), 1, "nucleus", "z", 45)
    outputs = {}
    for energy in (arc, void, spark):
        outputs.update(energy.outputs())
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Compare regenerated bytes; never write")
    args = parser.parse_args()
    outputs = generate()
    assert len(outputs) == 12
    for path, data in outputs.items():
        if args.verify:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit(f"Generated asset differs or is missing: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        print("verified" if args.verify else "wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
