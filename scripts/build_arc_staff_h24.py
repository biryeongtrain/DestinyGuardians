#!/usr/bin/env python3
"""Original Arc Staff reconstruction from H24 visual references; no extracted game assets.

Requires Pillow. Writes ONLY new H24 assets, or compares them byte-for-byte with --verify.
Native Blockbench MCP was unavailable (read-only request timed out); .bbmodel is authored
deterministically, not claimed as a native Blockbench codec export.
"""
import argparse
import base64
import copy
import io
import json
import math
from pathlib import Path
import uuid

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
ART = ROOT / "art/blockbench/supers"
NAME = "arc_staff_h24"
SIDES = ("north", "east", "south", "west", "up", "down")


def uid(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "destiny:h24:" + label))


def generate():
    # Brushed silver, blue-shadowed seams, pale ceramic, charged ice, blue edge, white core.
    palette = [(166, 200, 219), (45, 84, 113), (211, 235, 245),
               (149, 233, 255), (58, 172, 242), (238, 253, 255), (90, 133, 159), (190, 218, 231)]
    atlas = Image.new("RGBA", (256, 128))
    draw = ImageDraw.Draw(atlas)
    for m, color in enumerate(palette):
        for y in range(128):
            for x in range(32):
                # Wide longitudinal highlight, fine brushed scratches; no random source imagery.
                light = 1 + .14 * math.cos((x - 12) / 32 * math.pi) - .10 * (x > 25)
                light += ((y * 17 + x * 7) % 13 - 6) * .002
                draw.point((m * 32 + x, y), fill=tuple(min(255, round(c * light)) for c in color) + (255,))
        if m in (0, 2, 7):
            for y in (18, 46, 88, 114):
                draw.line((m*32+5, y, m*32+12+(y%9), y), fill=(134, 177, 200, 255))
        if m == 1:
            for y in range(4, 128, 8):
                draw.line((m*32, y, m*32+31, y), fill=(28, 58, 81, 255))
    png = io.BytesIO(); atlas.save(png, format="PNG")
    elements, bb_elements = [], []
    groups = {n: [] for n in ("shaft", "machined_sleeves", "lance_tips", "arc_filaments")}

    def box(name, center, size, material=0, group="shaft", rotation=0, emission=6):
        lo = [round(c - s/2, 7) for c, s in zip(center, size)]
        hi = [round(c + s/2, 7) for c, s in zip(center, size)]
        uv = [material*32+3, 4, material*32+29, 124]
        e = dict(name=name, **{"from": lo, "to": hi},
                 faces={s: {"uv": [uv[0]/16, uv[1]/8, uv[2]/16, uv[3]/8], "texture": "#0"} for s in SIDES},
                 light_emission=emission, shade=False)
        if rotation:
            e["rotation"] = {"axis": "y", "angle": rotation, "origin": list(center)}
        elements.append(e)
        b = dict(name=name, type="cube", uuid=uid(name), box_uv=False, autouv=0,
                 **{"from": lo, "to": hi}, origin=list(center), rotation=[0, rotation, 0],
                 faces={s: {"uv": uv, "texture": 0} for s in SIDES},
                 light_emission=emission, shade=False, export=True, rescale=False)
        bb_elements.append(b); groups[group].append(b["uuid"])

    def ring(name, y, length, radius, material=0, group="machined_sleeves", emission=6):
        # Crossed prisms approximate a turned, eight-faceted shaft at item-display scale.
        side = radius * math.sqrt(2)
        for rot in (0, 45):
            box(name + f"_{rot}", (8, y, 8), (side, length, side), material, group, rot, emission)

    ring("continuous_silver_shaft", 8, 35, .49, 0, "shaft", 8)
    # Smooth central hand area retains right grip (8,8,8) and left support (8,12,8).
    # Thin ice-white longitudinal highlight is readable from front AND back.
    for axis in (0, 2):
        for sign in (-1, 1):
            c, size = [8, 8, 8], [.16, 30.5, .16]
            c[axis] += sign * .365
            box(f"charged_shaft_line_{axis}_{sign}", c, size, 3, emission=15)
    for sign in (-1, 1):
        tag = "upper" if sign > 0 else "lower"
        def cy(distance): return 8 + sign*distance
        # Reference has repeated turned collars, then a ribbed sleeve before a SINGLE spear tip.
        for k, distance in enumerate((6.5, 9.2, 12.7, 15.7)):
            ring(f"{tag}_collar_recess_{k}", cy(distance), .42, .62, 1)
            ring(f"{tag}_silver_collar_{k}", cy(distance), .20, .73, 2, emission=9)
            ring(f"{tag}_collar_light_{k}", cy(distance+.19), .075, .68, 3, emission=15)
        ring(f"{tag}_ribbed_sleeve", cy(11.1), 2.4, .55, 1)
        for i in range(11):
            ring(f"{tag}_turned_rib_{i}", cy(10+i*.22), .10, .64, 7, emission=8)
        ring(f"{tag}_neck", cy(17), 2.4, .39, 0, emission=10)
        for i in range(10):
            ring(f"{tag}_neck_rib_{i}", cy(16+i*.20), .07, .49, 2, emission=10)
        # Flat double-edged lance blade, with fine sliced taper instead of the old outward forks.
        for i in range(24):
            t = (i+.5)/24
            y = cy(18+t*6)
            width = 1.42*(1-t)**.85 + .035
            depth = .31*(1-t)+.025
            box(f"{tag}_lance_blade_{i:02}", (8, y, 8), (width, .25, depth), 2, "lance_tips", emission=12)
            box(f"{tag}_blade_spine_{i:02}", (8, y, 8), (max(.025, width*.28), .25, depth+.025), 5, "lance_tips", emission=15)
        # Small secondary edge facets at the heel, not an extra fork/prong.
        for side in (-1, 1):
            box(f"{tag}_blade_heel_{side}", (8+side*.53, cy(18.1), 8), (.20, .44, .21), 4, "lance_tips", emission=15)
        # Sparse static ion filaments accompany existing animated runtime VFX. Stay off the grip.
        for side in (-1, 1):
            points = [(8+side*.42, cy(14.1)), (8+side*.97, cy(14.8)),
                      (8+side*.71, cy(15.2)), (8+side*1.10, cy(15.8)), (8+side*.40, cy(16.8))]
            for j, (a, b) in enumerate(zip(points, points[1:])):
                dx, dy = b[0]-a[0], b[1]-a[1]
                length = math.hypot(dx, dy)
                mid = [(a[0]+b[0])/2, (a[1]+b[1])/2, 8.12]
                label = f"{tag}_ion_filament_{side}_{j}"
                box(label, mid, (.045, length+.015, .045), 3, "arc_filaments", emission=15)
                angle = -math.degrees(math.atan2(dx, dy))
                if angle > 90: angle -= 180
                if angle < -90: angle += 180
                # The 26.3 parser supports arbitrary cuboid angles; matching saved BB rotation.
                elements[-1]["rotation"] = {"axis": "z", "angle": angle, "origin": mid}
                bb_elements[-1]["rotation"] = [0, 0, angle]

    old = json.loads((ASSETS / "models/item/arc_staff.json").read_text())
    model = {"format_version": "1.21.11", "credit": "H24 original reconstruction; Destiny design copyright Bungie; see docs/design/37_H24_아크_지팡이.md",
             "ambientocclusion": False, "texture_size": [256, 128],
             "textures": {"0": f"destiny:item/supers/{NAME}", "particle": f"destiny:item/supers/{NAME}"},
             "elements": elements, "display": copy.deepcopy(old["display"])}
    # Use the existing known-compatible BB project schema, but replace ALL its geometry/atlas.
    bb = json.loads((ART / "arc_staff.bbmodel").read_text())
    bb.update(name=NAME, model_identifier=NAME, credit=model["credit"], elements=bb_elements,
              display=copy.deepcopy(old["display"]), ai_used=True, ai_agents="Codex H24 deterministic authoring")
    bb["groups"] = [{"name": g, "uuid": uid(g), "origin": [8,8,8], "rotation": [0,0,0], "export": True} for g in groups]
    bb["outliner"] = [{"uuid": uid(g), "children": ids} for g, ids in groups.items()]
    texture = copy.deepcopy(bb["textures"][0])
    texture.update(name=NAME+".png", uuid=uid("texture"), width=256, height=128,
                   source="data:image/png;base64,"+base64.b64encode(png.getvalue()).decode())
    bb["textures"] = [texture]
    def encoded(obj): return (json.dumps(obj, ensure_ascii=False, indent=2)+"\n").encode()
    return {
        ASSETS / f"models/item/{NAME}.json": encoded(model),
        ASSETS / f"items/{NAME}.json": encoded({"model": {"type": "minecraft:model", "model": f"destiny:item/{NAME}"}}),
        ASSETS / f"textures/item/supers/{NAME}.png": png.getvalue(),
        ART / f"{NAME}.bbmodel": encoded(bb),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    for path, data in generate().items():
        if args.verify:
            assert path.read_bytes() == data, f"Generated asset differs: {path}"
        else:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        print(("verified" if args.verify else "wrote"), path.relative_to(ROOT))
