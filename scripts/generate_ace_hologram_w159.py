#!/usr/bin/env python3
"""Ace ADS red hologram: original reticle-mask brackets + screenshot-supported dot.

Native cuboid planes, not an opaque optic or a reproduction of Bungie's PBR shader.
Only the two final ADS samples light up; HIP, third-person and reload stay canonical.
Requires Pillow (the bundled Codex Python has it). Source extraction is vendored,
so regeneration does not need Drive, Blender, or the scratch download directory.
"""
import argparse
import copy
import hashlib
import io
import json
import runpy
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "src/main/resources/assets/destiny"
KEY = "weapon_sight_w159"
ID = "ace_of_spades"
FP = ("firstperson_righthand", "firstperson_lefthand")
CENTER = [8, 12.45, 4.075186918]
EYE, SCALE = .42, .95
ON_FRAME = 19
RED = (255, 33, 31)  # sRGB conversion of Reticle Shader.001 Color1/2/3.
SOURCE = ROOT / "art/weapons/w159/source"


def enc(v):
    return (json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def reticle_texture():
    # Original alpha is 255 even in the black background. Green GStack channel
    # supplies the bracket mask; an opaque black quad would conceal the target.
    raw = (SOURCE / "reticle-gstack.png").read_bytes()
    mask = Image.open(io.BytesIO(raw)).convert("RGBA").getchannel("G")
    mask = mask.resize((256, 256), Image.Resampling.LANCZOS)
    image = Image.new("RGBA", (256, 256), (*RED, 0))
    image.putalpha(mask)
    # Separate authored dot atlas tile: supported by the user's gameplay frame,
    # NOT part of the extracted 24-vertex bracket mesh. No black backing.
    image.paste((*RED, 0), (120, 120, 136, 136))
    draw = ImageDraw.Draw(image)
    draw.ellipse((124, 124, 131, 131), fill=(*RED, 255))
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=False, compress_level=9)
    return out.getvalue()


def generate():
    helper = runpy.run_path(str(ROOT / "scripts/art/build_ace_w83.py"))
    source_path = A / f"models/item/weapon/{ID}.json"
    source = json.loads(source_path.read_bytes())
    assert len(source["elements"]) == 87
    mesh = json.loads((SOURCE / "reticle-mesh.json").read_bytes())
    # Adapt original bracket proportions to the clean W83 gun's length; the
    # authored sight center remains clear of its rear receiver. Not original FOV.
    units_per_meter = (9.9629092487 - -4.520813082) / (.04935 - -.42978)
    center_z = (.1710921972990036 + .1790253221988678) / 2
    body = copy.deepcopy(source)
    body["textures"]["hologram"] = f"destiny:item/{KEY}/ace_reticle"
    added = []

    def plane(name, low, high, uv):
        added.append(dict(name="w159_hologram_" + name,
                          **{"from": low, "to": high},
                          light_emission=15, shade_direction_override="up",
                          # World view displays and held items can view opposite sides of the
                          # zero-depth reticle. Keep matching image orientation on both sides.
                          faces={"south": dict(uv=uv, texture="#hologram"),
                                 "north": dict(uv=[uv[2], uv[1], uv[0], uv[3]], texture="#hologram")}))

    # Source right quad uses the left atlas bracket with reversed U. Rear-facing
    # south cuboid faces advance U with X: preserve that reversal explicitly.
    for name, indices, u in (("right", range(16, 20), [.3096102774143219, .02934354543685913]),
                             ("left", range(20, 24), [.9706564545631409, .6903897523880005])):
        vertices = [mesh["vertices"][i] for i in indices]
        low = [8 + min(p[0] for p in vertices) * units_per_meter,
               CENTER[1] + (min(p[2] for p in vertices) - center_z) * units_per_meter, CENTER[2]]
        high = [8 + max(p[0] for p in vertices) * units_per_meter,
                CENTER[1] + (max(p[2] for p in vertices) - center_z) * units_per_meter, CENTER[2]]
        plane(name, low, high, [u[0] * 16, (1 - .656559944152832) * 16,
                               u[1] * 16, (1 - .34344005584716797) * 16])
    # Plane uses a padded atlas tile. Its visible 8px dot is .026 model units.
    half = .026
    plane("dot", [8 - half, CENTER[1] - half, CENTER[2]],
          [8 + half, CENTER[1] + half, CENTER[2]], [7.5, 7.5, 8.5, 8.5])
    body["elements"].extend(added)
    body["credit"] = "W159 Ace original D2 reticle-mask brackets, screenshot-supported dot; Bungie design; unchanged W83 87-cube gun"
    out = {A / f"models/{KEY}/{ID}_body.json": enc(body),
           A / f"textures/item/{KEY}/ace_reticle.png": reticle_texture()}
    hip = source["display"]
    ads = copy.deepcopy(hip)
    for ctx in FP:
        ads[ctx] = dict(rotation=[0, 0, 0],
                        translation=[-8.96, 8.32 - SCALE * (CENTER[1] - 8),
                                     16 * (.72 - EYE) - SCALE * (CENTER[2] - 8)], scale=[SCALE] * 3)
    mapping = {}
    for frame in range(21):
        display = helper["interpolate"](hip, ads, frame)
        for style in ("native", "twohand"):
            path = f"{KEY}/{ID}_{frame:02}_{style}"
            parent = f"item/weapon/{ID}" if frame < ON_FRAME else f"{KEY}/{ID}_body"
            out[A / f"models/{path}.json"] = enc(dict(parent="destiny:" + parent,
                display=display if style == "native" else helper["two_hand_display"](display)))
            mapping[f"destiny:item/weapon_aim_w70/{ID}_{frame:02}_{style}"] = "destiny:" + path

    def remap(v):
        if isinstance(v, dict):
            return {k: mapping.get(x, x) if k == "model" and isinstance(x, str) else remap(x) for k, x in v.items()}
        if isinstance(v, list):
            return [remap(x) for x in v]
        return v

    graph_path = A / f"items/weapon_aim_w70/{ID}.json"
    out[A / f"items/{KEY}/{ID}.json"] = enc(remap(json.loads(graph_path.read_bytes())))
    manifest = dict(stage="W159", id=ID, source=str(source_path.relative_to(ROOT)),
        sourceSha256=sha(source_path.read_bytes()), sourceCubes=87, addedCubes=3, totalCubes=90,
        reference="user gameplay screenshot codex-clipboard-0a07bfa0-8f20-49ff-806f-1d23dc078ea0.png",
        sourceArchiveSha256="f20cfb5e620d82421a3676fec2ee384c7ef1a7d68346ed957a5df16f69ba099b",
        extractedMesh=mesh["name"], sourceMaskSha256=sha((SOURCE / "reticle-gstack.png").read_bytes()),
        redSrgb=list(RED), sightCenter=CENTER, eyeToRearMeters=EYE, scale=SCALE,
        frames=21, onFrame=ON_FRAME, onsetProgress=.95,
        policy="Two source-mask red parentheses and screenshot-supported authored dot, ADS-only. Native double-sided emission15 planes, no opaque lens/hood. Canonical87 cubes/UV, HIP/third/inspect/reload retained. Proportion-adapted, not original PBR/parallax/camera.",
        outputSha256={str(p.relative_to(ROOT)): sha(b) for p, b in out.items()})
    out[ROOT / "art/weapons/w159/ace-hologram.json"] = enc(manifest)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    outputs = generate()
    for path, data in outputs.items():
        if args.verify:
            assert path.read_bytes() == data, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print("Ace W159", len(outputs), "verified" if args.verify else "generated", "87 cubes + 3 emissive planes; ADS-only")
