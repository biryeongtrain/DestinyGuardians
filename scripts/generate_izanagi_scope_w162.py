#!/usr/bin/env python3
"""W162 Izanagi scope redraw from pinned W84 gameplay; never an exact Bungie sprite.

Pillow required. --verify is read-only. Writes only seven pack resources and its
manifest. No weapon cubes, original textures, animations, stats or camera edits.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
A = "src/main/resources/assets/destiny/"
MANIFEST = "art/weapons/w162/izanagi-scope.json"
W91 = A + "items/weapon_izanagi_w91/izanagis_burden.json"
WRAPPER = A + "items/weapon_scope_w45/izanagis_burden.json"
NAME = "scope_w162_izanagis_burden_"
PINS = {
    "src/main/resources/destiny/weapons/w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "art/weapons/w84/model/source/izanagi.bbmodel": "9ae28369f80ff0f81bb7e1344ee50b618b9a2de62dcafc631287084dbe3c8f31",
    "art/weapons/w84/references/gameplay-evidence.json": "9f7acd97e856158a947e23540827cdef52129c7ca196ce69f4d8e190268f0623",
    "art/weapons/w84/references/youtube-KgJR3zohsEs-storyboard-L3-M0-raw.jpg": "180b84805dba18ffcb5da5a7d8c5d3941572fb32b482017b98b38d2afda87de6",
    "art/weapons/w84/references/youtube-ov6C5oF7KSc-storyboard-L2-M1-raw.jpg": "dda6164cbcf6e13645bc7c78cc489de0915a13301c9841f10b7f9c0ef3159978",
    "art/weapons/w84/references/youtube-ov6C5oF7KSc-storyboard-L2-M2-raw.jpg": "b92105f1ae48bfd0211890d4e5387ce51649ac935adfada60b5f419a3121a920",
    # W197 adds source-driven body/magazine/bolt FP composites; specialize the
    # updated graph while retaining the exact same non-FP scope fallback.
    W91: "e1a32bbdff914271fa611f8ec8366fbe3985e475c17f1d002d2a4d1325a94a07",
    A + "items/weapon/izanagis_burden.json": "aacf7db971fb5172cea6e515a105dc1f467ccf370f603504ca2ae14cd153dc4d",
    A + "textures/item/weapon/izanagis_burden_lens.png": "905b370044dbbb942b2db8515e29f2a053725a8d67268ad7c9d376124b7b7423",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(data):
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()


def png(image):
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def non_first_person(node):
    """Specialize W91 for all non-FP contexts without changing its slot6/pose/grip graph.

    Every existing display-context selector branches only on the two FP contexts.
    Remove those unreachable branches, rather than copying 642KB of FP animations.
    No item-model reference to this wrapper or W91 is introduced (no recursion).
    """
    if isinstance(node, list):
        return [non_first_person(value) for value in node]
    if not isinstance(node, dict):
        return node
    if node.get("property") == "minecraft:display_context":
        assert node["type"] == "minecraft:select"
        for case in node["cases"]:
            values = case["when"] if isinstance(case["when"], list) else [case["when"]]
            assert set(values) <= {"firstperson_righthand", "firstperson_lefthand"}
        return non_first_person(node["fallback"])
    return {key: non_first_person(value) for key, value in node.items()}


def frame():
    # 3840 virtual square: visible 16:9 crop is [256,368,768,656]. The opening is
    # 1515 x 1080 virtual px, with clipped corners and joined half-lens side marks.
    # Dimensions, line weight and vignette are authored estimates, not measured pixels.
    scale = 3
    image = Image.new("RGBA", (1024 * scale, 1024 * scale), (0, 0, 0, 255))
    d = ImageDraw.Draw(image)
    points = [(354, 368), (670, 368), (714, 404), (714, 497), (710, 508),
              (704, 512), (710, 516), (714, 527), (714, 620), (678, 656),
              (346, 656), (310, 620), (310, 527), (314, 516), (320, 512),
              (314, 508), (310, 497), (310, 404)]
    polygon = [(x * scale, y * scale) for x, y in points]
    d.polygon(polygon, fill=(0, 0, 0, 0))
    d.line(polygon + [polygon[0]], fill=(210, 218, 205, 170), width=scale, joint="curve")
    # Thin dark edge shading leaves the world untinted and the central aiming ray clear.
    for offset in range(2, 7):
        inset = [(512 + (x - 512) * (1 - offset / 200),
                  512 + (y - 512) * (1 - offset / 200)) for x, y in points]
        coords = [(round(x * scale), round(y * scale)) for x, y in inset]
        d.line(coords + [coords[0]], fill=(5, 8, 6, 70 - offset * 7), width=scale)
    for side in (-1, 1):
        def xy(x, y):
            return ((512 + side * x) * scale, y * scale)
        d.line([xy(192, 512), xy(146, 512)], fill=(216, 223, 210, 185), width=scale)
        # Inward endpoint and fine etched marks, visible in the normal/charged footage.
        d.line([xy(146, 510), xy(146, 514)], fill=(240, 241, 229, 220), width=scale)
        for y in (422, 430, 438, 446, 578, 586, 594, 602):
            d.line([xy(197, y), xy(194, y)], fill=(187, 200, 183, 95), width=scale)
    return image.resize((1024, 1024), Image.Resampling.LANCZOS)


def reticle():
    # Small hollow aim point. The sampled gameplay is too coarse to certify its
    # exact contour; do not upscale the source physical lens border into a huge sight.
    image = Image.new("RGBA", (512, 512))
    d = ImageDraw.Draw(image)
    d.ellipse((228, 228, 284, 284), outline=(5, 8, 6, 170), width=12)
    d.ellipse((232, 232, 280, 280), outline=(244, 242, 225, 255), width=6)
    return image.resize((128, 128), Image.Resampling.LANCZOS)


def generate():
    for path, expected in PINS.items():
        if sha((ROOT / path).read_bytes()) != expected:
            raise ValueError("W162 source pin changed: " + path)
    source = json.loads((ROOT / W91).read_bytes())
    output = {WRAPPER: encode({"hand_animation_on_swap": False, "model": {
        "type": "minecraft:select", "property": "minecraft:display_context",
        "cases": [{"when": ["firstperson_righthand", "firstperson_lefthand"],
                   "model": {"type": "minecraft:empty"}}],
        "fallback": non_first_person(source["model"]),
    }})}
    for part, image in (("frame", frame()), ("reticle", reticle())):
        key = "gui/hud/" + NAME + part
        texture = "item/hud/" + NAME + part
        output[A + "textures/" + texture + ".png"] = png(image)
        output[A + "models/" + key + ".json"] = encode({
            "gui_light": "front", "textures": {"0": "destiny:" + texture, "particle": "destiny:" + texture},
            "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "faces": {
                face: {"texture": "#0", "uv": [0, 0, 16, 16], "tintindex": 0}
                for face in ("north", "south")}}]})
        output[A + "items/" + key + ".json"] = encode({"model": {
            "type": "minecraft:model", "model": "destiny:" + key,
            "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}})
    output[MANIFEST] = encode({
        "stage": "W162", "weapon": "izanagis_burden", "generator": "scripts/generate_izanagi_scope_w162.py",
        "artwork": "Authored approximation from inspected original gameplay samples; not extracted or pixel-exact Bungie scope art",
        "references": [
            {"url": "https://www.youtube.com/watch?v=KgJR3zohsEs", "author": "Cheese Forever",
             "sample": "W84 L3 M0 tiles1,7 (approx sampler2s,14s), 320x180",
             "observed": "Wide clipped top corners, joined side contours, inward bars and small center sight"},
            {"url": "https://www.youtube.com/watch?v=ov6C5oF7KSc", "author": "Ultraclocked",
             "sample": "W84 L2 M1 ADS sequence; M2 tiles4,5,6 (approx sampler108s,110s,112s), 160x90",
             "observed": "Normal/Honed/empty reticle comparison, warm brighter charged side contours",
             "limitation": "Storyboard samples establish qualitative form, not exact linework, timing or dynamic reticle values"},
            {"path": "art/weapons/w84/model/source/izanagi.bbmodel",
             "observed": "79 canonical source cubes; zero-thickness lenses43,78, south UV[0,32,20.5,52] red clipped ring/ticks",
             "limitation": "Physical lens texture is not a full-screen scope asset; unchanged and not repackaged as exact HUD"},
        ],
        "sourceSha256": PINS,
        "render": {"frameVirtualSize": 3840, "reticleVirtualSize": 80, "aimPoint": [960, 540],
                   "atlas": "Physical textures/item/hud PNGs and destiny:item/hud model references; no automatic conversion assumed",
                   "frameDepth": 0, "reticleDepth": 6, "normalTint": "FFFFFF", "fundedHonedTint": "FFAA8C",
                   "perspective": "Only held-item FP contexts are empty. Vanilla server HUD follows ADS in F5 too; no forced camera",
                   "zoom": "Unchanged sourced45 / 4.5x in existing aim profile; no FOV writes here"},
        "nonFirstPerson": "W91 graph specialized by removing only unreachable FP display-context branches; preserves slot6, pose and both grips",
        "sharedIntegration": [
            "Parent: active W91 scoped IDLE selects WeaponScopes wrapper; RELOAD/HONED retain W91",
            "Parent: register WeaponIzanagiScopeW162GameTests in shared fabric-gametest entrypoint",
            "Parent: update superseded W84 no-scope, W45 exactly-five and W91 charged ADS routing assertions",
        ],
        "nativeQueue": ["Pack reload and actual scope PNG at16:9/ultrawide", "Both FP hands/grips; F5 observer charged cosmetic",
                        "Normal/Honed reload visible,61-tick commit and real charged shot", "ADS release,swap,death,external camera cleanup; ammo/vitals above mask"],
        "proofBoundary": "Offline artwork/codec/regressions only; GameTests authored for parent central run; no native client/server execution by worker",
        "sha256": {path: sha(data) for path, data in output.items()},
    })
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    outputs = generate()
    for name, data in outputs.items():
        path = ROOT / name
        if args.verify:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit("W162 output differs: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(("Verified" if args.verify else "Generated") + " W162 Izanagi scope: " + str(len(outputs)) + " files")
