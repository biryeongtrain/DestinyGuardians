#!/usr/bin/env python3
"""W151 ADS-only pulse/MG bodies. No canonical model or registry writes."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
KEY = "weapon_sight_w151"
SIGHT_TEXTURE = "destiny:item/weapon/w148/sights"
# Coordinates follow the photographed, already-authored W123 sight hardware.
SPECS = {
    "cold_denial": (15.03, 5.53, 4.8, "open_ramp_reflex"),
    "bygones": (12.8, 6.77, 5.3, "compact_tube"),
    "chattering_bone": (12.99, 7.885, 6.95, "violet_tube_ivory_rim"),
    "blast_furnace": (14.73, 8.065, 5.5, "raised_reflex"),
    "claws_of_the_wolf": (12.53, 7.32, 4.22, "burgundy_long_tube"),
    "hammerhead": (14.16, 3.37, 3.14, "angular_reflex"),
}
REMOVALS = {
    "claws_of_the_wolf": ("optic_rear", "optic_lens"),
}
CUES = {
    "cold_denial": "Tall black twin swept ramps on the teal top rail; open top and bronze conduits. Keep source wings and raked ramp UVs; add low central aiming pin.",
    "bygones": "Short green-black cylindrical optic on narrow riser over walnut furniture, side dial and top band. Preserve the eight-wall tube and its source paint.",
    "chattering_bone": "Small violet cylindrical hood with pale ivory/gold rear ring over carved ivory body. Preserve both different-depth eight-wall rings and their original UVs.",
    "blast_furnace": "W152 correction: restore the W123 breech-mounted open optic and its source UVs. Seat the ADS eye ahead of the stock at 0.32m eye relief; retain the entire stock for HIP/third-person. This is a usable source-model optic, not a claim of exact original sight reproduction.",
    "claws_of_the_wolf": "Long burgundy tube with dark mouth, brass side dial and top plate above wolf studs. Keep shell/dials; replace opaque rear cap and lens with real air and an eight-wall rear collar.",
    "hammerhead": "Thin angular reflex window, slanted shoulders and flat short bridge above long cover mount. Keep the asymmetric-depth source legs, hood, base and red emitter; add an aligned front pin.",
}


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def rotate(vector, axis, degrees):
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    x, y, z = vector
    if axis == "x":
        return [x, c*y-s*z, s*y+c*z]
    if axis == "y":
        return [c*x+s*z, y, -s*x+c*z]
    return [c*x-s*y, s*x+c*y, z]


def local_point(element, point):
    """Invert native Rz*Ry*Rx about origin, plus legacy axis rescale.

    Testing in local space avoids both rotated-AABB false positives and
    unrotated-box false negatives. No projection onto unrotated XY bounds.
    """
    r = element.get("rotation")
    if not r:
        return list(point)
    origin = r["origin"]
    v = [a-b for a, b in zip(point, origin)]
    if "axis" in r:
        if r.get("rescale"):
            factor = abs(math.cos(math.radians(r["angle"])))
            v = [n if axis == r["axis"] else n*factor
                 for axis, n in zip("xyz", v)]
        v = rotate(v, r["axis"], -r["angle"])
    else:
        for axis in "zyx":
            v = rotate(v, axis, -r.get(axis, 0))
    return [a+b for a, b in zip(v, origin)]


def segment_hits(element, start, end):
    """Closed segment/slab test; zero-thickness opaque lens cards also count."""
    start, end = local_point(element, start), local_point(element, end)
    t0, t1 = 0.0, 1.0
    for lo, hi, a, b in zip(element["from"], element["to"], start, end):
        delta = b-a
        if abs(delta) < 1e-12:
            if a < lo-1e-10 or a > hi+1e-10:
                return False
        else:
            near, far = sorted(((lo-a)/delta, (hi-a)/delta))
            t0, t1 = max(t0, near), min(t1, far)
            if t0 > t1+1e-10:
                return False
    return True


def blockers(model, center, dx=0, dy=0, perspective=False, eye_meters=.65):
    x, y, z = center
    distance = eye_meters*16/.9
    far = z-64
    if perspective:
        start = [x, y, z+distance]
        ratio = (distance+64)/distance
        end = [x+dx*ratio, y+dy*ratio, far]
    else:
        start, end = [x+dx, y+dy, z+64], [x+dx, y+dy, far]
    return [e["name"] for e in model["elements"] if segment_hits(e, start, end)]


def body(id):
    source = ASSETS / f"models/weapon_surface_w123/{id}.json"
    original = read(source)
    model = copy.deepcopy(original)
    model.pop("display", None)  # Master owns sampled ADS wrappers/poses.
    removed = REMOVALS.get(id, ())
    by_name = {e["name"]: e for e in original["elements"]}
    assert all(name in by_name for name in removed)
    model["elements"] = [e for e in model["elements"] if e["name"] not in removed]
    model["textures"]["sight"] = SIGHT_TEXTURE
    elements = model["elements"]
    y, rear, front, style = SPECS[id]

    def box(name, lo, hi, uv=(0, 0, 1, 1), faces=None, rotation=None):
        e = {"name": "w151_"+name, "from": [round(v, 7) for v in lo],
             "to": [round(v, 7) for v in hi],
             "faces": copy.deepcopy(faces) if faces else {
                 f: {"uv": list(uv), "texture": "#sight"}
                 for f in ("north", "south", "east", "west", "up", "down")}}
        if rotation:
            e["rotation"] = rotation
        elements.append(e)

    if id == "claws_of_the_wolf":
        # Rebuild the filled rear cap as tangent wall segments; no glass card.
        radius, thick = .5, .1
        width = 2*(radius+thick/2)*math.tan(math.pi/8)
        for n in range(8):
            a = n*math.pi/4
            cx, cy = 8-radius*math.sin(a), y+radius*math.cos(a)
            box(f"rear_collar_{n}", [cx-width/2, cy-thick/2, 7.08],
                [cx+width/2, cy+thick/2, 7.46972291],
                faces=by_name[f"optic_shell_{n}"]["faces"],
                rotation={"origin": [cx, cy, 7.27], "z": n*45})
    bottoms = {"cold_denial": 14.5, "bygones": 12.33,
               "chattering_bone": 12.62, "blast_furnace": 14.03,
               "claws_of_the_wolf": 12.04, "hammerhead": 13.75}
    bottom = bottoms[id]
    # Keep apparent tip gap at 0.055 on the rear sight plane at the declared eye.
    # Blast stock is behind the ADS eye, rather than a large foreground wall.
    eye_meters = .32 if id == "blast_furnace" else .65
    gap = .055*(1+(rear-front)/(eye_meters*16/.9))
    box("front_pin_stem", [7.96, bottom, front-.07], [8.04, y-gap-.07, front+.07])
    box("front_pin_tip", [7.965, y-gap-.07, front-.075],
        [8.035, y-gap, front+.075], (6, 0, 7, 1))
    center = [8, y, rear]
    assert len(elements) <= 1000
    assert not blockers(model, center), (id, blockers(model, center))
    ref = next(r for r in read(ROOT / "art/weapons/w31/references.json") if r["id"] == id)
    provenance = ROOT / f"art/weapons/w123/{id}"
    manifest = read(provenance / "manifest.json")
    raw = manifest["raw_input_sha256"]
    photo = f"/tmp/destiny-weapons-w31/references/{id}.jpg"
    assert raw[photo] == ref["sha256"]
    row = dict(id=id, family="machine_gun" if id == "hammerhead" else "pulse_rifle",
               body=f"{KEY}/{id}_body", sightCenter=center,
               forwardPoint=[8, y, rear-2], style=style, eyeSide="+Z", plane="XY",
               scale=.9, eyeToSightMeters=eye_meters, removedSightNames=list(removed),
               elementCount=len(elements), source=str(source.relative_to(ROOT)),
               sourceSha256=sha(source), reference={
                   "photo": photo, "photoSha256": ref["sha256"], "url": ref["screenshot"],
                   "notes": CUES[id],
                   "review": str((provenance / "review.md").relative_to(ROOT)),
                   "reviewSha256": sha(provenance / "review.md"),
                   "design": str((provenance / "design.json").relative_to(ROOT)),
                   "designSha256": sha(provenance / "design.json"),
                   "ripProvenance": str((provenance / "manifest.json").relative_to(ROOT)),
                   "ripProvenanceSha256": sha(provenance / "manifest.json"),
                   "rawFbxSha256": {p: h for p, h in raw.items() if p.lower().endswith(".fbx")}},
               addedSightNames=[e["name"] for e in elements if e["name"].startswith("w151_")],
               aimingTip=[8, round(y-gap, 7), front], clearApertureRadius=.04,
               sourceElementCount=len(original["elements"]),
               sightTextureSha256=sha(ASSETS / "textures/item/weapon/w148/sights.png"),
               assemblyPolicy="Full static ADS assembly includes magazine/cover once; master supplies ADS wrapper only.",
               nativeChecks="pending master")
    return model, row


def generate():
    outputs, rows = {}, []
    for id in SPECS:
        model, row = body(id)
        outputs[ASSETS / f"models/{KEY}/{id}_body.json"] = encode(model)
        rows.append(row)
    outputs[ROOT / "art/weapons/w151/pulse-sights.json"] = encode({"weapons": rows})
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    outputs = generate()
    for path, data in outputs.items():
        if args.verify:
            if not path.is_file() or path.read_bytes() != data:
                parser.exit(1, f"W151 output differs: {path.relative_to(ROOT)}\n")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f"W151 pulse: {len(SPECS)} weapons / {len(outputs)} outputs "
          + ("verified" if args.verify else "generated"))


if __name__ == "__main__":
    main()
