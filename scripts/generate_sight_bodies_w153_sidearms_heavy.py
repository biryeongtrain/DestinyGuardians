#!/usr/bin/env python3
"""W153 six ADS-only bodies; original W123 geometry and atlases are read-only.

Standard library only. generate() returns relative Path -> bytes. --verify never
writes. Shared wrappers/Java admission/native acceptance belong to master.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path("src/main/resources/assets/destiny")
MANIFEST = Path("art/weapons/w153/sidearms-heavy-sights.json")
TIP_TEXTURE = ASSETS / "textures/item/weapon/w148/sights.png"
PREFIX = "w153_"
FACES = ("north", "south", "east", "west", "up", "down")
WEAPONS = {
    "dead_man_walking_xx7463": dict(
        family="sidearm", center=[8, 16.02, 7.58], eye=.36,
        style="suros_open_rear_ears", aperture=[.38, .24],
        donor="front_sight_blade", front=-3.35, seat=15.745, tip=15.935,
        width=.18, depth=.20, removed=[],
        hardware=["rear_sight_post_-1", "rear_sight_post_1", "rear_sight_floor"],
        notes="Long teal SUROS slide, original open parallel rear ears and front blade. Extend the existing short front blade with a pale tip within those ears; original six sight elements and their UVs survive. W154 uses .36m relief and a wider .18 pin.",
    ),
    "high_albedo": dict(
        family="sidearm", center=[8, 14.56, 9.02], eye=.34,
        style="europa_blade_and_carry_bridge", aperture=[.36, .17],
        donor="brace_top", front=-1.45, seat=14.35, tip=14.475,
        width=.18, depth=.18, removed=[],
        hardware=["rear_sight_blade"],
        notes="Blue rear blade, sloped narrow carry bridge and orange cruciform front brace. Keep all three; add a short aiming pin on the actual front brace. The blue rear blade remains a visible lower alignment cue; no invented reflex hood. W154 adds two narrow open shoulders on a low sill overlapping the retained blue blade, with .34m relief and a wider .18 pin.",
    ),
    "brass_attacks": dict(
        family="sidearm", center=[8, 17.09, 9.10], eye=.34,
        style="brass_stepped_rail_iron", aperture=[.36, .15],
        donor="front_crown", front=-3.65, seat=16.855, tip=17.005,
        width=.18, depth=.18, removed=[],
        hardware=["rear_crown"],
        notes="Pale cutaway shroud, copper bore and original stepped brass I-section top rail. Aim just above the rear crown toward a short front-crown pin. Retain every rail web/crown/foot and the seated grip magazine; no added generic sight frame. W154 adds two short shoulders on the real rear crown to form an open notch, with .34m relief and a wider .18 pin.",
    ),
    "edge_transit": dict(
        family="heavy_grenade_launcher", center=[8, 13.13, 9.26], eye=.32,
        style="protected_low_box_iron", aperture=[.27, .105],
        donor="sight_recess_7.86", front=7.86, seat=12.97, tip=13.075,
        width=.065, depth=.10, removed=[],
        hardware=["sight_ear_-1", "sight_ear_1", "sight_top", "sight_base"],
        notes="Seafoam stock and offset green drum with the original low protected box sight. Keep roof, long ears and three recessed range bars; put a tiny pale pin on the forward range bar. Short .32m eye relief keeps the low box visibly seated ahead of the stock.",
    ),
    "fixed_odds": dict(
        family="machine_gun", center=[8, 12.82, 4.42], eye=.44,
        style="calus_triangular_peep", aperture=[.18, .15],
        donor="front_sight_ear_-1", front=-9.85, seat=12.265, tip=12.76,
        width=.09, depth=.16, removed=[],
        hardware=["rear_sight_arch_-1", "rear_sight_arch_1", "rear_sight_base"],
        notes="Gold triangular rear peep, paired front ears, purple insets and black open stock. Preserve the inclined arch legs and all their original face UVs. Add one narrow pale front post between the real front ears; preserve ammunition box and seven belt rounds exactly once.",
    ),
    "retrofit_escapade": dict(
        family="machine_gun", center=[8, 13.52, 6.70], eye=.36,
        style="suros_open_hooded_tube", aperture=[.24, .22],
        donor="optic_hood_4", front=3.36, seat=13.06, tip=13.46,
        width=.065, depth=.10, removed=["objective_lens", "ocular_lens"],
        hardware=[f"ocular_rim_{i}" for i in range(8)],
        notes="Quilted wrap, teal chassis, copper belt and original long octagonal optic hood with teal ocular rim and top loop. Only the two opaque recessed lens plates are removed in ADS. Keep all hood staves/rim/loop UVs; seat a slim physical aiming pin on the tube floor. .36m relief puts the eye ahead of the butt while retaining a visible complete tube mouth.",
    ),
}


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_bytes())


def source_path(weapon):
    # All six originals are full-only: their seated magazine/belt is already here.
    return ASSETS / f"models/weapon_surface_w123/{weapon}.json"


def rotate(point, axis, degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    x, y, z = point
    if axis == "x":
        return [x, c*y-s*z, s*y+c*z]
    if axis == "y":
        return [c*x+s*z, y, -s*x+c*z]
    if axis == "z":
        return [c*x-s*y, s*x+c*y, z]
    raise ValueError(axis)


def angles(rotation):
    result = {axis: rotation.get(axis, 0) for axis in "xyz"}
    if "axis" in rotation:
        result[rotation["axis"]] = rotation["angle"]
    return result


def transform_point(element, point, inverse=False):
    r = element.get("rotation", {})
    origin = r.get("origin", [0, 0, 0])
    q = [v-o for v, o in zip(point, origin)]
    aa = angles(r)
    if r.get("rescale") and "axis" not in r:
        raise ValueError("Native Euler rescale is not supported")
    if not inverse and r.get("rescale"):
        factor = abs(math.cos(math.radians(r["angle"])))
        q = [v if a == r["axis"] else v/factor for a, v in zip("xyz", q)]
    for axis in ("zyx" if inverse else "xyz"):
        q = rotate(q, axis, -aa[axis] if inverse else aa[axis])
    if inverse and r.get("rescale"):
        factor = abs(math.cos(math.radians(r["angle"])))
        q = [v if a == r["axis"] else v*factor for a, v in zip("xyz", q)]
    return [v+o for v, o in zip(q, origin)]


def ray_hit(element, start, end):
    """Finite exact segment/rotated-box entry t, or None; every solid opaque."""
    a, b = (transform_point(element, p, inverse=True) for p in (start, end))
    near, far = 0., 1.
    for p, q, lo, hi in zip(a, b, element["from"], element["to"]):
        d = q-p
        if abs(d) < 1e-12:
            if p < lo-1e-9 or p > hi+1e-9:
                return None
        else:
            t0, t1 = sorted(((lo-p)/d, (hi-p)/d))
            near, far = max(near, t0), min(far, t1)
            if near > far+1e-10:
                return None
    return near


def eye(row):
    x, y, z = row["sightCenter"]
    return [x, y, z + row["eyeToSightMeters"]*16/row["scale"]]


def channel_hits(model, row, dx=0, dy=0):
    start = eye(row)
    x, y, z = row["sightCenter"]
    # Perspective through the actual aperture, extending beyond every muzzle.
    factor = (start[2]+40)/(start[2]-z)
    end = [x+dx*factor, y+dy*factor, -40]
    return sorted(e["name"] for e in model["elements"] if ray_hit(e, start, end) is not None)


def aperture_fraction(model, row):
    """21x21 area, not the W152 tiny-center-ray shortcut.

    The genuine frame and aiming pin may occupy part of this rectangle. Require
    most of a useful original-sized opening to show background. Foreground
    stock and all geometry along the complete eye ray count as obstructions.
    """
    hx, hy = row["apertureHalfSize"]
    clear = sum(not channel_hits(model, row, hx*ix/10, hy*iy/10)
                for ix in range(-10, 11) for iy in range(-10, 11))
    return clear/441


def south_point(element):
    return transform_point(element, [(a+b)/2 for a, b in
        zip(element["from"][:2], element["to"][:2])] + [element["to"][2]])


def foreground_blockers(model, row):
    """Check the actual visible sight, including bottom/rim, against the chassis.

    Exclude only the enumerated original sight hardware from this foreground
    test; full aperture and aiming-point tests include every emitted element.
    A center ray can be clear while the stock hides the entire rim below it.
    """
    targets = {p["name"] for p in row["hardwareLandmarks"]}
    blocked = {}
    for target in row["hardwareLandmarks"]:
        names = [e["name"] for e in model["elements"] if e["name"] not in targets
                 and not e["name"].startswith(PREFIX)
                 and (t := ray_hit(e, eye(row), target["point"])) is not None and t < 1-1e-7]
        if names:
            blocked[target["name"]] = names
    return blocked


def tip_blockers(model, row):
    return [e["name"] for e in model["elements"] if e["name"] != row["aimingTipName"]
            and (t := ray_hit(e, eye(row), row["aimingTip"])) is not None and t < 1-1e-7]


def make_body(weapon, cfg):
    path = source_path(weapon)
    source = read(path)
    by_name = {e["name"]: e for e in source["elements"]}
    if len(by_name) != len(source["elements"]):
        raise ValueError(f"{weapon}: duplicate source names")
    if not set(cfg["removed"]).issubset(by_name):
        raise ValueError(f"{weapon}: missing requested removal")
    model = copy.deepcopy(source)
    model.pop("display", None)
    model["elements"] = [e for e in model["elements"] if e["name"] not in cfg["removed"]]
    x, y, z = cfg["center"]
    front, width, depth, top = cfg["front"], cfg["width"], cfg["depth"], cfg["tip"]
    # A physical post specific to the original station, not an overlay/card/frame.
    # The original metal faces are reused verbatim; only its pale terminal cap
    # uses the existing W148 sight atlas. No source UV or texture is modified.
    stem = dict(name=PREFIX+"aim_stem", **{
        "from": [round(x-width/2, 7), cfg["seat"], round(front-depth/2, 7)],
        "to": [round(x+width/2, 7), round(top-.035, 7), round(front+depth/2, 7)]},
        faces=copy.deepcopy(by_name[cfg["donor"]]["faces"]))
    tip = dict(name=PREFIX+"aim_tip", **{
        "from": [round(x-width/2, 7), round(top-.04, 7), round(front-depth/2, 7)],
        "to": [round(x+width/2, 7), top, round(front+depth/2, 7)]},
        faces={f: dict(texture="#sight", uv=[4.25, .25, 4.75, .75]) for f in FACES})
    model["textures"]["sight"] = "destiny:item/weapon/w148/sights"
    model["elements"].extend([stem, tip])
    # W154: low open shoulders on the actual rear station, never a roof/ring.
    # The High Albedo sill overlaps its retained blue blade. Brass uses its
    # existing continuous crown as the sill; all source records stay exact.
    rear_boxes = []
    rear_donor = None
    if weapon == "high_albedo":
        rear_donor = "rear_sight_blade"
        rear_boxes = [
            ("sill", [7.57, 14.35, 8.72], [8.43, 14.40, 9.28]),
            ("left", [7.57, 14.38, 8.72], [7.64, 14.64, 9.28]),
            ("right", [8.36, 14.38, 8.72], [8.43, 14.64, 9.28]),
        ]
    elif weapon == "brass_attacks":
        rear_donor = "rear_crown"
        rear_boxes = [
            ("left", [7.52, 16.97, 8.88], [7.60, 17.17, 9.275]),
            ("right", [8.40, 16.97, 8.88], [8.48, 17.17, 9.275]),
        ]
    rear = [dict(name=PREFIX+"rear_"+name, **{"from": lo, "to": hi},
                 faces=copy.deepcopy(by_name[rear_donor]["faces"]))
            for name, lo, hi in rear_boxes]
    model["elements"].extend(rear)
    row = dict(id=weapon, family=cfg["family"], body=f"weapon_sight_w153/{weapon}_body",
        sightCenter=list(cfg["center"]), forwardPoint=[x, y, round(z-2, 7)],
        eyeSide="+Z", plane="XY", scale=.9, eyeToSightMeters=cfg["eye"],
        elementCount=len(model["elements"]), source=path.as_posix(),
        sourceSha256=sha((ROOT/path).read_bytes()), sourceElementCount=len(source["elements"]),
        removedSightNames=list(cfg["removed"]), addedSightNames=[e["name"] for e in [stem, tip] + rear],
        style=cfg["style"], aimingTip=[x, round(top-.02, 7), round(front+depth/2, 7)],
        aimingTipName=tip["name"], sightUvDonors={stem["name"]: cfg["donor"], **{e["name"]: rear_donor for e in rear}},
        apertureHalfSize=cfg["aperture"], minimumClearApertureFraction=.60,
        hardwareLandmarks=[dict(name=n, point=south_point(by_name[n])) for n in cfg["hardware"]],
        companionElementCount=0, assemblyElementCount=len(model["elements"]),
        assemblyWithSpareMagazineCount=len(model["elements"]),
        assemblyPolicy="Full-only source includes seated magazine/drum/belt once; no companion or spare model is required.",
        removalReason=("ADS-only opaque lens removal: both plates cross the tube's real center; original hood, rim and top loop stay intact."
                       if cfg["removed"] else "No original geometry or UV changed or removed."))
    if weapon == "retrofit_escapade":
        # Probe the inner lip of the actual rim, not its underside embedded in
        # the unchanged saddle (the bottom .045 units are a mounting joint).
        for landmark in row["hardwareLandmarks"]:
            point = landmark["point"]
            point[:2] = [c + .88*(p-c) for c, p in zip((x, y), point[:2])]
    if row["elementCount"] > 1000:
        raise ValueError(f"{weapon}: assembly exceeds 1000 emitted elements")
    if channel_hits(model, row):
        raise ValueError(f"{weapon}: blocked center {channel_hits(model, row)}")
    if tip_blockers(model, row):
        raise ValueError(f"{weapon}: aiming tip hidden {tip_blockers(model, row)}")
    foreground = foreground_blockers(model, row)
    if foreground:
        raise ValueError(f"{weapon}: sight hardware hidden by chassis {foreground}")
    for n in cfg["removed"]:
        if ray_hit(by_name[n], eye(row), [x, y, -40]) is None:
            raise ValueError(f"{weapon}: unjustified removal {n}")
    # A contiguous useful upper window must remain empty as well as the broad
    # area test. The .16 x .07 opening is independent of the pale pin below it.
    for ix in range(-4, 5):
        for iy in range(5):
            if channel_hits(model, row, .08*ix/4, .07*iy/4):
                raise ValueError(f"{weapon}: upper aiming window obstructed")
    row["clearUpperWindow"] = dict(halfWidth=.08, height=.07)
    fraction = aperture_fraction(model, row)
    if fraction < row["minimumClearApertureFraction"]:
        raise ValueError(f"{weapon}: usable aperture only {fraction:.3f}")
    row["clearApertureFraction"] = round(fraction, 6)
    return model, row


def generate():
    references = {r["id"]: r for r in read("art/weapons/w31/references.json")}
    outputs, rows = {}, []
    for weapon, cfg in WEAPONS.items():
        model, row = make_body(weapon, cfg)
        ref = references[weapon]
        prior = Path("art/weapons/w123") / weapon
        provenance = {str(prior/p): sha((ROOT/prior/p).read_bytes())
                      for p in ("design.json", "manifest.json", "review.md")}
        manifest = read(prior / "manifest.json")
        photo = Path(f"/tmp/destiny-weapons-w31/references/{weapon}.jpg")
        if sha(photo.read_bytes()) != ref["sha256"]:
            raise ValueError(f"{weapon}: default photo does not match W31")
        if manifest["raw_input_sha256"].get(str(photo)) != ref["sha256"]:
            raise ValueError(f"{weapon}: W123 photo provenance mismatch")
        row["reference"] = dict(photo=str(photo), photoSha256=ref["sha256"],
            url=ref["screenshot"], screenshot=ref["screenshot"], bungieHash=ref["bungie_hash"],
            notes=cfg["notes"], provenance=provenance,
            priorRipSha256={p: h for p, h in manifest["raw_input_sha256"].items()
                            if p.lower().endswith((".fbx", ".blend"))},
            limitation="Actual default oblique photo opened; hidden rear details follow this weapon's W123 design/source. Physical pale pin is an ADS adaptation, not a recovered shader reticle. Native acceptance pending master.")
        source = read(source_path(weapon))
        row["sourceTextureSha256"] = {v: sha((ROOT/ASSETS/("textures/"+v.split(":", 1)[1]+".png")).read_bytes())
                                     for v in sorted(set(source["textures"].values()))}
        row["sightTextureSha256"] = sha((ROOT/TIP_TEXTURE).read_bytes())
        outputs[ASSETS / f"models/{row['body']}.json"] = encode(model)
        rows.append(row)
    outputs[MANIFEST] = encode(dict(weapons=rows))
    return outputs


def mismatches(outputs):
    return [str(path) for path, data in outputs.items()
            if not (ROOT/path).is_file() or (ROOT/path).read_bytes() != data]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    outputs = generate()
    if args.verify:
        bad = mismatches(outputs)
        if bad:
            parser.exit(1, "W153 output mismatch: " + ", ".join(bad) + "\n")
    else:
        for path, data in outputs.items():
            if not (ROOT/path).is_file() or (ROOT/path).read_bytes() != data:
                (ROOT/path).parent.mkdir(parents=True, exist_ok=True)
                (ROOT/path).write_bytes(data)
    print(f"W153 sidearms-heavy: 6 weapons, {len(outputs)} outputs " + ("verified" if args.verify else "generated"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
