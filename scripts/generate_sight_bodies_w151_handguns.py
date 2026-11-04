#!/usr/bin/env python3
"""Six ADS-only iron-sight bodies. No registry, pose, HIP or reload writes.

Run with python3 -B; --verify compares all seven generated outputs byte for byte.
Geometry uses the source frame: eye +Z, sight plane XY, muzzle -Z.
"""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path("src/main/resources/assets/destiny")
MODEL_DIR = ASSETS / "models/weapon_sight_w151"
MANIFEST = Path("art/weapons/w151/handguns-sights.json")
PREFIX = "w151_"
CLEAR_HALF_WIDTH = 0.025
# W154: preserve the full .025 square under the steeper near-eye perspective.
# Austringer has a much shorter front/rear baseline, so it needs less tip gap.
SMALL_SIGHTS = {
    "duke_mk_44": dict(eye=.36, width=.18, gap=.085),
    "austringer": dict(eye=.35, width=.20, gap=.055),
    "seventh_seraph_officer_revolver": dict(eye=.36, width=.18, gap=.085),
    "allied_demand": dict(eye=.32, width=.18, gap=.070),
    "farewell": dict(eye=.38, width=.18, gap=.080),
    "lonesome": dict(eye=.34, width=.18, gap=.085),
}
WEAPONS = {
    "duke_mk_44": dict(
        family="hand_cannon", center=[8, 15.06, 5.04], front=-4.98,
        profile="low_blade_on_blue_top_strap", remove=["Front_sight"],
        cues=["Blue shroud with continuous long top strap and small black front blade.",
              "Low narrow rear notch above the cylinder; exposed loop hammer stays intact."],
        reason="The wide old Front_sight crosses the aiming ray and its clear margin; replace only that blade with a lower narrow ramp and tip.",
    ),
    "austringer": dict(
        family="hand_cannon", center=[8, 14.03, 5.24], front=2.26,
        profile="low_gold_notch_above_black_receiver", remove=[],
        cues=["Pale gold shroud and low gold rear notch above the black cylinder/frame.",
              "The black cylindrical underbarrel accessory is below the bore, not the aiming optic; its opaque lens, hose and mount are retained."],
        reason="No old element obstructs this sight line. Retain all 126 source elements, extending the low front blade and gold rear shoulders only.",
    ),
    "seventh_seraph_officer_revolver": dict(
        family="hand_cannon", center=[8, 14.03, 6.39], front=-4.79,
        profile="raised_block_notch_over_long_rail", remove=["rear_sight_blade"],
        cues=["Long black toothed top rail, wedge front ramp and raised broad rear sight block.",
              "Silver muzzle/latch, brass chamber trim and the lower forward hood remain source geometry; the raised rear block needs a real U slot."],
        reason="The opaque full-width rear_sight_blade crosses the aperture. Split its silhouette into a low sill and two separate ears; keep its rotated saddle, forks, lower hood and rail.",
    ),
    "allied_demand": dict(
        family="sidearm", center=[8, 13.42, 8.40], front=1.92,
        profile="compact_slide_u_notch_behind_suppressor", remove=["front_sight"],
        cues=["Conventional compact front blade and small U-shaped rear notch on the pale ribbed slide.",
              "The long silver perforated suppressor is in front of the blade; green frame and wolf-pattern slide remain untouched."],
        reason="The old front_sight fills the center ray. Replace it with a low foot and narrow tip, and join the retained rear ears with a low sill.",
    ),
    "farewell": dict(
        family="sidearm", center=[8, 14.15, 7.39], front=-1.02,
        profile="guarded_front_post_and_raked_rear_fins", remove=["front_sight_post"],
        cues=["Raised angular silver front sight with a small opening; paired purple raked rear ears.",
              "Black/blue body, magenta markings, bound green cables, heat sink and hanging bayonet are retained."],
        reason="The old front_sight_post enters the small clear aperture. Replace it with a lower pin inside a genuinely open protective hood; extend the retained rear ears into raked fins.",
    ),
    "lonesome": dict(
        family="sidearm", center=[8, 15.04, 8.71], front=-1.01,
        profile="flared_rear_u_above_bronze_breech", remove=["front_sight_blade"],
        cues=["Tall flared U rear ears above the rounded breech and a narrow blade over the front clamp.",
              "Muted bronze/steel pierced-pattern shroud, separate diagonal braces and projecting barrel remain intact."],
        reason="The old front_sight_blade fills the center. Narrow and lower that blade and flare the retained rear wings with two outward shoulders.",
    ),
}


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def rotate(vector, axis, degrees):
    """Right-handed component rotation; 26.3 Euler order is Rz * Ry * Rx."""
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    x, y, z = vector
    if axis == "x":
        return (x, c * y - s * z, s * y + c * z)
    if axis == "y":
        return (c * x + s * z, y, -s * x + c * z)
    if axis == "z":
        return (c * x - s * y, s * x + c * y, z)
    raise ValueError(f"Unknown rotation axis: {axis}")


def inverse_ray(element, origin, direction):
    """Transform the world ray into the element's *local* unrotated box.

    Supports both classic axis/angle and native 26.3 x/y/z rotations. Translate
    the origin, but never the direction; reverse Rz,Ry,Rx for the inverse.
    """
    rotation = element.get("rotation", {})
    pivot = rotation.get("origin", [8, 8, 8])
    local_origin = tuple(v - p for v, p in zip(origin, pivot))
    local_direction = tuple(direction)
    angles = {axis: rotation.get(axis, 0) for axis in "xyz"}
    if "axis" in rotation:
        angles[rotation["axis"]] = rotation.get("angle", 0)
    for axis in "zyx":
        local_origin = rotate(local_origin, axis, -angles[axis])
        local_direction = rotate(local_direction, axis, -angles[axis])
    if rotation.get("rescale"):
        # Legacy rescale stretches perpendicular axes before rotation.
        axis = rotation["axis"]
        factor = abs(math.cos(math.radians(rotation["angle"])))
        local_origin = tuple(v if a == axis else v * factor for a, v in zip("xyz", local_origin))
        local_direction = tuple(v if a == axis else v * factor for a, v in zip("xyz", local_direction))
    return tuple(v + p for v, p in zip(local_origin, pivot)), local_direction


def ray_hit(element, origin, direction=(0, 0, -1)):
    """Nearest nonnegative intersection parameter, or None; all boxes opaque.

    Treat even a zero-depth lens/card as an obstruction. No name-based exemption
    or texture-alpha exemption can make an opaque old optic pass clearance.
    """
    origin, direction = inverse_ray(element, origin, direction)
    near, far = 0.0, math.inf
    for p, d, low, high in zip(origin, direction, element["from"], element["to"]):
        if abs(d) < 1e-12:
            if p < low - 1e-9 or p > high + 1e-9:
                return None
        else:
            a, b = sorted(((low - p) / d, (high - p) / d))
            near, far = max(near, a), min(far, b)
            if near > far + 1e-9:
                return None
    return near


def aperture_blockers(model, row):
    """9x9 local-inverse rays through the whole assembly, from eye toward -Z.

    Check both parallel rays and rays from the common eye through the sampled
    square, so the body ahead of the sight cannot hide behind the sight plane.
    """
    x, y, z = row["sightCenter"]
    eye_z = z + row["eyeToSightMeters"] * 16 / row["scale"]
    half = row["clearApertureHalfWidth"]
    blocked = set()
    for ix in range(9):
        for iy in range(9):
            dx, dy = half * (ix - 4) / 4, half * (iy - 4) / 4
            rays = [((x + dx, y + dy, eye_z), (0, 0, -1)),
                    ((x, y, eye_z), (dx / (eye_z - z), dy / (eye_z - z), -1))]
            for origin, direction in rays:
                for element in model["elements"]:
                    if ray_hit(element, origin, direction) is not None:
                        blocked.add(element["name"])
    return sorted(blocked)


def authored_sights(weapon_id, source):
    """Small weapon-specific solid volumes; six existing atlases, no new PNG."""
    by_name = {element["name"]: element for element in source["elements"]}
    elements, uv_donors = [], {}

    def box(name, low, high, donor, rotation=None):
        name = PREFIX + name
        element = dict(name=name, **{"from": low, "to": high},
                       faces=copy.deepcopy(by_name[donor]["faces"]))
        if rotation:
            element["rotation"] = rotation
        elements.append(element)
        uv_donors[name] = donor

    def tilted(name, low, high, donor, axis, angle):
        pivot = [round((a + b) / 2, 6) for a, b in zip(low, high)]
        box(name, low, high, donor, dict(origin=pivot, axis=axis, angle=angle))

    if weapon_id == "duke_mk_44":
        box("duke_blade_foot", [7.79, 14.91, -5.24], [8.21, 14.96, -4.72], "Front_sight")
        box("duke_aim_tip", [7.94, 14.955, -5.16], [8.06, 15.005, -4.86], "Front_sight")
    elif weapon_id == "austringer":
        box("austringer_aim_tip", [7.95, 13.935, 2.10], [8.05, 13.975, 2.28], "Front_sight")
        box("austringer_gold_left", [7.685, 14.015, 4.955], [7.855, 14.095, 5.525], "Rear_sight_ear_-1")
        box("austringer_gold_right", [8.145, 14.015, 4.955], [8.315, 14.095, 5.525], "Rear_sight_ear_1")
    elif weapon_id == "seventh_seraph_officer_revolver":
        box("seraph_notch_sill", [7.62, 13.80, 5.79], [8.38, 13.87, 7.00267753], "rear_sight_blade")
        box("seraph_notch_left", [7.62, 13.85, 5.79], [7.78, 14.101973705299681, 7.00267753], "rear_sight_blade")
        box("seraph_notch_right", [8.22, 13.85, 5.79], [8.38, 14.101973705299681, 7.00267753], "rear_sight_blade")
        box("seraph_aim_tip", [7.945, 13.82, -4.98], [8.055, 13.975, -4.74], "front_sight_ramp")
    elif weapon_id == "allied_demand":
        box("allied_blade_foot", [7.84, 13.295, 1.75], [8.16, 13.33, 2.09], "front_sight")
        box("allied_aim_tip", [7.945, 13.32, 1.78], [8.055, 13.365, 2.00], "front_sight")
        box("allied_notch_sill", [7.69, 13.31, 8.19], [8.31, 13.34, 8.61], "rear_sight_base")
    elif weapon_id == "farewell":
        box("farewell_aim_tip", [7.94, 13.68, -1.15], [8.06, 14.095, -0.89], "front_sight_post")
        box("farewell_front_guard_left", [7.64, 13.66, -1.28], [7.76, 14.28, -0.76], "front_sight_base")
        box("farewell_front_guard_right", [8.24, 13.66, -1.28], [8.36, 14.28, -0.76], "front_sight_base")
        box("farewell_front_guard_bridge", [7.64, 14.25, -1.28], [8.36, 14.34, -0.76], "front_sight_base")
        tilted("farewell_rear_fin_left", [7.49, 14.08, 7.02], [7.73, 14.34, 7.76], "rear_sight_ear_-1", "x", -16)
        tilted("farewell_rear_fin_right", [8.27, 14.08, 7.02], [8.51, 14.34, 7.76], "rear_sight_ear_1", "x", -16)
    elif weapon_id == "lonesome":
        box("lonesome_blade_foot", [7.85, 14.79, -1.18], [8.15, 14.88, -0.84], "front_sight_blade")
        box("lonesome_aim_tip", [7.95, 14.86, -1.13], [8.05, 14.985, -0.89], "front_sight_blade")
        tilted("lonesome_flared_left", [7.44, 14.80, 8.44], [7.70, 15.15, 8.98], "rear_sight_wing_-1", "z", 12)
        tilted("lonesome_flared_right", [8.30, 14.80, 8.44], [8.56, 15.15, 8.98], "rear_sight_wing_1", "z", -12)
    else:
        raise ValueError(weapon_id)
    # Only the authored front tip changes. Every retained source element,
    # rear notch, front guard and atlas remains in its original frame.
    tuning = SMALL_SIGHTS[weapon_id]
    tip = next(e for e in elements if e["name"].endswith("_aim_tip"))
    top = round(WEAPONS[weapon_id]["center"][1] - tuning["gap"], 6)
    tip["from"][0] = round(8 - tuning["width"] / 2, 6)
    tip["to"][0] = round(8 + tuning["width"] / 2, 6)
    tip["to"][1] = top
    tip["from"][1] = min(tip["from"][1], round(top - .07, 6))
    return elements, uv_donors


def build_outputs(root=ROOT):
    outputs, rows = {}, []
    references_path = Path("art/weapons/w31/references.json")
    references = {row["id"]: row for row in read(root / references_path)}
    for weapon_id, cfg in WEAPONS.items():
        source_path = ASSETS / f"models/weapon_surface_w123/{weapon_id}.json"
        source = read(root / source_path)
        names = [element["name"] for element in source["elements"]]
        if len(set(names)) != len(names) or not set(cfg["remove"]).issubset(names):
            raise ValueError(f"Unexpected source elements: {weapon_id}")
        model = copy.deepcopy(source)
        model.pop("display", None)
        preserved = [e for e in model["elements"] if e["name"] not in cfg["remove"]]
        added, donors = authored_sights(weapon_id, source)
        model["elements"] = preserved + added
        ref = references[weapon_id]
        prior = Path("art/weapons/w123") / weapon_id
        design = read(root / prior / "design.json")
        row = dict(
            id=weapon_id, family=cfg["family"], body=f"weapon_sight_w151/{weapon_id}_body",
            sightCenter=cfg["center"],
            forwardPoint=[cfg["center"][0], cfg["center"][1], round(cfg["center"][2] - 2, 6)],
            style="iron", profile=cfg["profile"], eyeSide="+Z", plane="XY", scale=0.9,
            eyeToSightMeters=SMALL_SIGHTS[weapon_id]["eye"], removedSightNames=cfg["remove"],
            elementCount=len(model["elements"]), source=source_path.as_posix(),
            sourceSha256=sha((root / source_path).read_bytes()),
            sourceElementCount=len(source["elements"]), preservedElementCount=len(preserved),
            addedSightNames=[e["name"] for e in added], sightUvDonors=donors,
            aimingTip=next(e["name"] for e in added if e["name"].endswith("_aim_tip")),
            frontPoint=[8, cfg["center"][1], cfg["front"]],
            tipGap=SMALL_SIGHTS[weapon_id]["gap"], clearApertureHalfWidth=CLEAR_HALF_WIDTH,
            clearance="9x9 square, parallel and common-eye -Z rays; inverse local rotations; all original/added solids and opaque lenses included",
            removalReason=cfg["reason"], referenceNotes=cfg["cues"],
            reference=dict(
                photo=f"/tmp/destiny-weapons-w31/references/{weapon_id}.jpg",
                photoSha256=ref["sha256"], url=ref["screenshot"],
                catalog=references_path.as_posix(),
                design=(prior / "design.json").as_posix(),
                designSha256=sha((root / prior / "design.json").read_bytes()),
                review=(prior / "review.md").as_posix(),
                reviewSha256=sha((root / prior / "review.md").read_bytes()),
                rawSourceFiles=design["source"]["source_files"],
                sourceTriangles=design["source"]["source_triangles"],
                limitation="Default side/oblique photos and prior rip study establish shape/material cues; rear microprofile is an authored approximation, not an extracted first-person optic or native acceptance.",
            ),
        )
        blockers = aperture_blockers(model, row)
        if blockers:
            raise ValueError(f"{weapon_id}: obstructed aperture: {blockers}")
        if len(model["elements"]) > 1000:
            raise ValueError(f"{weapon_id}: assembly exceeds 1000 elements")
        outputs[root / MODEL_DIR / f"{weapon_id}_body.json"] = encode(model)
        rows.append(row)
    outputs[root / MANIFEST] = encode({"weapons": rows})
    return outputs


def output_mismatches(outputs):
    return [path for path, expected in outputs.items()
            if not path.is_file() or path.read_bytes() != expected]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    outputs = build_outputs()
    if args.verify:
        mismatches = output_mismatches(outputs)
        if mismatches:
            parser.exit(1, "W151 handguns stale/missing outputs:\n" + "\n".join(str(p) for p in mismatches) + "\n")
    else:
        for path, data in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f"W151 handguns: 6 weapons, {len(outputs)} outputs {'verified' if args.verify else 'generated'}")


if __name__ == "__main__":
    main()
