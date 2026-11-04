#!/usr/bin/env python3
"""W153 fusion ADS-only physical sights; deterministic stdlib-only owned outputs.

W151 bodies supply the schema/finite rotated-box ray pattern. Actual W123 full
assemblies supply the geometry and face UVs. No shared generator is imported.
"""
import argparse
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path("src/main/resources/assets/destiny")
KEY = "weapon_sight_w153"
MANIFEST = Path("art/weapons/w153/fusion-sights.json")
SIGHT_TEXTURE = "destiny:item/weapon/w148/sights"
FACES = ("north", "south", "east", "west", "up", "down")
SPECS = {
    "erentil_fr4": dict(center=[8, 14.6, 2.815], eye=.48, front=2.46,
        seat=14.195, width=.07, style="omolon_blue_raked_reflex",
        prefixes=("Reflex_",), witnesses=("Reflex_upright_7.46", "Reflex_upright_8.54", "Reflex_roof"),
        window=[-.18, -.055, .18, .20],
        notes="Photographed blue raked reflex on toothed silver rail, left adjustment dial, open square window. Preserve all original roof/uprights/sill/dial UVs and hoses. A small pale pin seats on the real sill; 0.48m relief keeps the blue frame visible above the stock."),
    "hollow_words": dict(center=[8, 14.48, 5.56], eye=.60, front=1.30,
        seat=14.05, width=.07, style="taken_long_chamfered_box_tube",
        prefixes=("optic_",), witnesses=("optic_wall_-1", "optic_wall_1", "optic_roof"),
        window=[-.18, -.055, .18, .20],
        notes="Photographed long dark rectangular tube, chamfered corners and narrow base over teal/gold marbled rail. Retain all nine original optic solids and their UVs; no opaque glass exists in W123. A small pale pin stands at the objective end inside the existing tunnel; 0.60m relief preserves its long-wall perspective."),
    "dream_breaker": dict(center=[8, 13.62, 3.79], eye=.55, front=-7.55,
        seat=13.36, width=.09, style="lunar_original_fork_and_post_irons",
        prefixes=("sight_", "rear_sight_", "front_sight_"),
        witnesses=("rear_sight_fork_-1", "rear_sight_fork_1"),
        window=[-.12, -.05, .12, .25],
        notes="Actual photo has low irons along the ivory cord-wrapped housing, not a scope. Keep the source fork pair and foot. The tall original front post would overlap the useful lower sight field; shorten only that post in the ADS copy, crop its original side UVs, and give its upper 0.05 units a pale cap. 0.55m relief views the real notch ahead of the shoulder, without removing the stock."),
    "null_composure": dict(center=[8, 14.30, 1.57], eye=.42, front=.40,
        seat=13.71, width=.07, style="gold_foot_arched_black_reflex",
        prefixes=("Reflex_",), witnesses=("Reflex_arch_-1", "Reflex_arch_1", "Reflex_rear_hood"),
        window=[-.18, -.055, .18, .18],
        notes="Photographed black arched reflex with open low cheeks, gold feet and side dial above blue breech. Keep every original hood/arch/dial/foot and face UV; place the pale guide on its existing sill inside the real opening. 0.42m relief keeps the sight ahead of the rear buffer and shoulder."),
    "coriolis_force": dict(center=[8, 15.30, -.20], eye=.32, front=-3.42,
        seat=15.075, width=.08, style="europa_red_twin_open_ears",
        prefixes=("sight_ear", "rear_sight_sill"),
        witnesses=("sight_ear-1", "sight_ear1"),
        window=[-.18, -.055, .18, .25],
        notes="Actual photo shows two tall red open ears on the ribbed top shroud; no reflex roof/tube is invented. Keep both source ears, rear sill and all asymmetric U-clamp/stock parts. Seat a short pale guide on an existing shroud bridge. Forward 0.32m relief puts the rear upper stock rail behind the eye and leaves both ears visible."),
}


def read(path):
    return json.loads((ROOT / path).read_bytes())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def rotate(v, axis, degrees):
    x, y, z = v
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    if axis == "x":
        return [x, c*y-s*z, s*y+c*z]
    if axis == "y":
        return [c*x+s*z, y, -s*x+c*z]
    return [c*x-s*y, s*x+c*y, z]


def world_point(element, point):
    r = element.get("rotation", {})
    origin = r.get("origin", [0, 0, 0])
    v = [a-b for a, b in zip(point, origin)]
    if "axis" in r:
        v = rotate(v, r["axis"], r["angle"])
        if r.get("rescale"):
            factor = abs(math.cos(math.radians(r["angle"])))
            v = [n if a == r["axis"] else n/factor for a, n in zip("xyz", v)]
    else:
        for axis in "xyz":
            v = rotate(v, axis, r.get(axis, 0))
    return [a+b for a, b in zip(v, origin)]


def local_point(element, point):
    r = element.get("rotation", {})
    origin = r.get("origin", [0, 0, 0])
    v = [a-b for a, b in zip(point, origin)]
    if "axis" in r:
        if r.get("rescale"):
            factor = abs(math.cos(math.radians(r["angle"])))
            v = [n if a == r["axis"] else n*factor for a, n in zip("xyz", v)]
        v = rotate(v, r["axis"], -r["angle"])
    else:
        for axis in "zyx":
            v = rotate(v, axis, -r.get(axis, 0))
    return [a+b for a, b in zip(v, origin)]


def ray_entry(element, start, end):
    """Finite segment against the rotated cuboid, including opaque thin cards."""
    a, b = local_point(element, start), local_point(element, end)
    near, far = 0., 1.
    for lo, hi, u, v in zip(element["from"], element["to"], a, b):
        delta = v-u
        if abs(delta) < 1e-12:
            if u < lo-1e-10 or u > hi+1e-10:
                return None
        else:
            t0, t1 = sorted(((lo-u)/delta, (hi-u)/delta))
            near, far = max(near, t0), min(far, t1)
            if near > far+1e-10:
                return None
    return near


def eye(row):
    x, y, z = row["sightCenter"]
    return [x, y, z+row["eyeToSightMeters"]*16/row["scale"]]


def sight_rays(row):
    """A usable asymmetric viewing window, not merely a tiny central ray.

    Include the entire assembled body from the real eye to beyond the muzzle.
    The lower edge clears the physical aiming tip; open irons extend upward.
    """
    x, y, z = row["sightCenter"]
    ex, ey, ez = eye(row)
    left, bottom, right, top = row["usableSightWindow"]
    for i, j in itertools.product(range(9), repeat=2):
        dx, dy = left+(right-left)*i/8, bottom+(top-bottom)*j/8
        yield [x+dx, y+dy, ez], [x+dx, y+dy, -40]
        factor = (ez+40)/(ez-z)
        yield [ex, ey, ez], [x+dx*factor, y+dy*factor, -40]


def blockers(model, row):
    return sorted({e["name"] for a, b in sight_rays(row)
                   for e in model["elements"] if ray_entry(e, a, b) is not None})


def visible_samples(model, row, name):
    """Return visible points on an actual optic's eye-facing surface.

    Target the physical rim itself and test every other assembled part up to
    that surface. This catches foreground stocks that leave only a tiny hole.
    """
    part = next(e for e in model["elements"] if e["name"] == name)
    visible = []
    for u, v in itertools.product((.2, .5, .8), repeat=2):
        p = world_point(part, [part["from"][0]+u*(part["to"][0]-part["from"][0]),
                              part["from"][1]+v*(part["to"][1]-part["from"][1]),
                              part["to"][2]+.00001])
        if p[2] >= eye(row)[2]:
            continue
        if not any(ray_entry(e, eye(row), p) is not None
                   for e in model["elements"] if e["name"] != name):
            visible.append(p)
    return visible


def box(name, lo, hi, donor=None, pale=False):
    faces = copy.deepcopy(donor["faces"]) if donor else {
        f: {"texture": "#sight", "uv": [0, 0, 1, 1]} for f in FACES}
    if pale:
        faces = {f: {"texture": "#sight", "uv": [4.25, .25, 4.75, .75]} for f in FACES}
    return {"name": "w153_"+name, "from": [round(v, 7) for v in lo],
            "to": [round(v, 7) for v in hi], "faces": faces}


def body(id, cfg):
    source = ASSETS / f"models/weapon_surface_w123/{id}.json"
    original = read(source)
    model = copy.deepcopy(original)
    model.pop("display", None)  # master owns all sampled ADS poses
    by_name = {e["name"]: e for e in original["elements"]}
    if len(by_name) != len(original["elements"]):
        raise ValueError(f"{id}: duplicate source names")
    x, y, z = cfg["center"]
    distance = cfg["eye"]*16/.9
    front, seat = cfg["front"], cfg["seat"]
    top = y-.075*(1+(z-front)/distance)
    removed = ["front_sight_post"] if id == "dream_breaker" else []
    model["elements"] = [e for e in model["elements"] if e["name"] not in removed]
    if removed:
        # Keep the actual iron's location, X/Z footprint, original side material
        # and texel density. Only its ADS height changes; no non-sight changes.
        donor = by_name["front_sight_post"]
        stem = copy.deepcopy(donor)
        stem["name"] = "w153_shortened_original_front_post"
        stem["to"][1] = round(top-.05, 7)
        for face, data in stem["faces"].items():
            if face in ("north", "south", "east", "west"):
                u0, v0, u1, v1 = data["uv"]
                fraction = (stem["to"][1]-stem["from"][1])/(donor["to"][1]-donor["from"][1])
                data["uv"][1] = round(v1-(v1-v0)*fraction, 7)
        model["elements"].append(stem)
        lo, hi = list(donor["from"]), list(donor["to"])
        lo[1], hi[1] = top-.05, top
        model["elements"].append(box("aim_tip", lo, hi, pale=True))
    else:
        half = cfg["width"]/2
        model["elements"].append(box("aim_stem", [x-half, seat, front-.06],
                                      [x+half, top-.06, front+.06]))
        model["elements"].append(box("aim_tip", [x-half, top-.06, front-.06],
                                      [x+half, top, front+.06], pale=True))
    model["textures"]["sight"] = SIGHT_TEXTURE
    prior = Path("art/weapons/w123") / id
    reference = next(r for r in read("art/weapons/w31/references.json") if r["id"] == id)
    photo = Path(f"/tmp/destiny-weapons-w31/references/{id}.jpg")
    manifest, design = read(prior / "manifest.json"), read(prior / "design.json")
    if sha(photo) != reference["sha256"] or manifest["raw_input_sha256"][str(photo)] != reference["sha256"]:
        raise ValueError(f"{id}: reference photo/provenance mismatch")
    if design.get("reference", {}).get("sha256", design.get("default_photo_sha256")) != reference["sha256"]:
        raise ValueError(f"{id}: design/photo mismatch")
    row = dict(id=id, family="fusion_rifle", body=f"{KEY}/{id}_body",
        sightCenter=list(cfg["center"]), forwardPoint=[x, y, z-2],
        eyeSide="+Z", plane="XY", scale=.9, eyeToSightMeters=cfg["eye"],
        elementCount=len(model["elements"]), source=source.as_posix(), sourceSha256=sha(source),
        removedSightNames=removed, addedSightNames=[e["name"] for e in model["elements"] if e["name"].startswith("w153_")],
        retainedSightNames=[n for n in by_name if n.startswith(cfg["prefixes"]) and n not in removed],
        style=cfg["style"], aimingTip=[x, round(top, 7), front], aimingTipName="w153_aim_tip",
        aimingTipApparentGap=.075, clearApertureHalfSize=.04,
        usableSightWindow=cfg["window"], visibleOpticNames=list(cfg["witnesses"]),
        sourceElementCount=len(original["elements"]), companionElementCount=0,
        assemblyElementCount=len(model["elements"]), assemblyWithSpareMagazineCount=len(model["elements"]),
        assemblyPolicy="Full W123 static assembly includes the seated cartridge/powerpack once. No companion model. Master must not append a magazine to this ADS body.",
        sightTextureSha256=sha(ASSETS / "textures/item/weapon/w148/sights.png"),
        sourceTextureSha256={v: sha(Path("src/main/resources/assets") / v.split(":")[0] / "textures" / (v.split(":")[1]+".png")) for v in sorted(set(original["textures"].values()))},
        reference=dict(photo=str(photo), photoSha256=reference["sha256"], url=reference["screenshot"],
            notes=cfg["notes"],
            provenance={str(prior/p): sha(prior/p) for p in ("design.json", "manifest.json", "review.md")},
            priorRipSha256={p:h for p,h in manifest["raw_input_sha256"].items() if p.lower().endswith((".fbx", ".blend"))},
            limitation="Actual default three-quarter photo and W123 authored source study; pale physical point is an ADS guide, not recovered shader reticle, glass or PBR."),
        nativeChecks="Pending master: shared18 ADS21frame wrappers/Java admission, actual26.3 parser/pack and native visibility/charge/reload/twohand checks.")
    if len(model["elements"]) > 1000:
        raise ValueError(f"{id}: assembled budget exceeded")
    blocked = blockers(model, row)
    if blocked:
        raise ValueError(f"{id}: usable sight window blocked by {blocked}")
    for name in cfg["witnesses"]:
        if len(visible_samples(model, row, name)) < 4:
            raise ValueError(f"{id}: actual optic hidden: {name}")
    return model, row


def generate():
    outputs, rows = {}, []
    for id, cfg in SPECS.items():
        model, row = body(id, cfg)
        outputs[ASSETS / f"models/{KEY}/{id}_body.json"] = encode(model)
        rows.append(row)
    outputs[MANIFEST] = encode({"weapons": rows})
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    outputs = generate()
    if args.verify:
        different = [str(p) for p, data in outputs.items() if not (ROOT/p).is_file() or (ROOT/p).read_bytes() != data]
        if different:
            parser.exit(1, "W153 output differs: " + ", ".join(different) + "\n")
    else:
        for path, data in outputs.items():
            (ROOT/path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT/path).write_bytes(data)
    print(f"W153 fusion: 5 weapons / {len(outputs)} outputs " + ("verified" if args.verify else "generated"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
