#!/usr/bin/env python3
"""W219 Allied Demand: source61 FK and its own grip-fed magazine assembly.

Pure stdlib. Import and generate(root=ROOT) perform no writes. Master owns
source installation, shared arms/routing, materialization and native reviews.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path("src/main/resources/assets/destiny")
ART = Path("art/weapons/w219/allied_demand")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w219_allied_demand.py")
SOURCE = A / "models/weapon_surface_w123/allied_demand.json"
NATIVE = A / "models/weapon/sidearm/allied_demand.json"
TWOHAND = A / "models/weapon/sidearm/allied_demand_twohand.json"
ITEM = A / "items/weapon/allied_demand.json"
CONTACTS = Path("art/weapons/w201/contacts.json")
FRAMING = Path("art/weapons/w205/first-person-framing.json")
RIG = Path("art/weapons/w219/rigs/sidearm_c0461d9d.json")
PREP_RIG = Path("/private/tmp/destiny-w219-source/sidearm_c0461d9d.json")
KEY = "weapon_reload_w219_allied_demand/allied_demand"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine")
GRIPS = ("native", "twohand")
INTERVALS = 60
SAMPLES = INTERVALS + 1
SOURCE_ACTION = "80A8A560"
MOVING = (63, 64)
MOVING_NAMES = ("magazine_lower", "magazine_floor")
FIXED = {57: "green_grip_core", 58: "recessed_grip_panel_-1",
         59: "recessed_grip_panel_1", 60: "frontstrap", 61: "backstrap", 62: "heel"}
GRIP_WINDOW = (.05, .10, .45, .55)
ARM_ELEMENT_RESERVE = 448
# Existing source-to-canonical calibration: source X-forward/Z-up -> -Z/Y-up.
C = ((0, -1, 0), (0, 0, 1), (-1, 0, 0))


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack("!f", struct.pack("!f", value))[0]


def add(a, b):
    return [x+y for x, y in zip(a, b)]


def sub(a, b):
    return [x-y for x, y in zip(a, b)]


def mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def vec(m, v):
    return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]


def transpose(m):
    return list(map(list, zip(*m)))


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def unit(a):
    length = math.sqrt(dot(a, a))
    if length < 1e-10:
        raise ValueError("Degenerate source basis")
    return [x/length for x in a]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def pos(m):
    return [m[i][3] for i in range(3)]


def basis(m):
    # Normalize only tiny exported scale/shear, matching shared weapon_basis.
    x = unit([m[i][0] for i in range(3)])
    y = [m[i][1] for i in range(3)]
    y = unit(sub(y, [v*dot(x, y) for v in x]))
    z = unit(cross(x, y))
    return transpose([x, cross(z, x), z])


def xyz(angles):
    x, y, z = map(math.radians, angles)
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[c*e, -c*f, d], [b*d*e+a*f, -b*d*f+a*e, -b*c],
            [-a*d*e+b*f, a*d*f+b*e, a*c]]


def euler(m):
    y = math.asin(max(-1., min(1., m[0][2])))
    if abs(math.cos(y)) > 1e-8:
        x, z = math.atan2(-m[1][2], m[2][2]), math.atan2(-m[0][1], m[0][0])
    else:
        x, z = math.atan2(m[2][1], m[1][1]), 0
    return [round(math.degrees(v), 9) for v in (x, y, z)]


def quaternion(m):
    values = [1+m[0][0]+m[1][1]+m[2][2], 1+m[0][0]-m[1][1]-m[2][2],
              1-m[0][0]+m[1][1]-m[2][2], 1-m[0][0]-m[1][1]+m[2][2]]
    i = max(range(4), key=values.__getitem__)
    a = math.sqrt(max(0, values[i]))/2
    d = 4*a
    if i == 0:
        q = [a, (m[2][1]-m[1][2])/d, (m[0][2]-m[2][0])/d, (m[1][0]-m[0][1])/d]
    elif i == 1:
        q = [(m[2][1]-m[1][2])/d, a, (m[0][1]+m[1][0])/d, (m[0][2]+m[2][0])/d]
    elif i == 2:
        q = [(m[0][2]-m[2][0])/d, (m[0][1]+m[1][0])/d, a, (m[1][2]+m[2][1])/d]
    else:
        q = [(m[1][0]-m[0][1])/d, (m[0][2]+m[2][0])/d, (m[1][2]+m[2][1])/d, a]
    return unit(q)


def interpolate(a, b, t):
    """Shortest-arc rigid rotation and linear position; no Euler-axis damping."""
    if t <= 0:
        return copy.deepcopy(a)
    if t >= 1:
        return copy.deepcopy(b)
    qa, qb = quaternion(a), quaternion(b)
    cosine = dot(qa, qb)
    if cosine < 0:
        qb, cosine = [-v for v in qb], -cosine
    if cosine > .9995:
        q = unit([x+(y-x)*t for x, y in zip(qa, qb)])
    else:
        angle = math.acos(max(-1., min(1., cosine)))
        q = [(x*math.sin((1-t)*angle)+y*math.sin(t*angle))/math.sin(angle)
             for x, y in zip(qa, qb)]
    w, x, y, z = q
    p = [a[i][3]+(b[i][3]-a[i][3])*t for i in range(3)]
    return [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w), p[0]],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w), p[1]],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y), p[2]], [0., 0., 0., 1.]]


def smooth(t):
    t = max(0., min(1., t))
    return t*t*(3-2*t)


def source_pose(rig, progress):
    """Own original61, with existing shared .1 boundary transition only."""
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError("Progress must be finite and in 0..1")
    rest = rig["actions"][rig["idle"]]["frames"][0]["joints"]
    frames = rig["actions"][SOURCE_ACTION]["frames"]
    if progress in (0, 1):
        return copy.deepcopy(rest)
    index = min(INTERVALS-1, int(progress*INTERVALS))
    a, b = frames[index], frames[index+1]
    t = (progress-a["progress"])/(b["progress"]-a["progress"])
    weight = smooth(progress/.1)*smooth((1-progress)/.1)
    return {name: interpolate(rest[name], interpolate(a["joints"][name], b["joints"][name], t), weight)
            for name in rest}


def attachment_weight(progress):
    start, attached, release, end = GRIP_WINDOW
    return smooth((progress-start)/(attached-start)) * (1-smooth((progress-release)/(end-release)))


def magazine_offset(rest, current, progress):
    """Authored mesh contact path from source LEFT wrist in weapon space.

    Its reach/withdraw/return is source FK, while seat/release is authored.
    After .55 the magazine is seated despite later source slide handling.
    Master then fits this part to the source palm using the retained contact.
    """
    weight = attachment_weight(progress)
    if weight == 0:
        return [0., 0., 0.]
    def relative(j):
        return vec(C, vec(transpose(basis(j["weapon"])),
                          sub(pos(j["leftWrist"]), pos(j["weapon"]))))
    return [32*weight*v for v in sub(relative(current), relative(rest))]


def pose_display(original, twohand, rig, progress, part, grip):
    if part not in PARTS or grip not in GRIPS:
        raise ValueError("Unknown Allied Demand part/grip")
    accepted = original if grip == "native" else twohand
    if progress in (0, 1):
        return copy.deepcopy(accepted)
    rest = rig["actions"][rig["idle"]]["frames"][0]["joints"]
    current = source_pose(rig, progress)
    wr, wt = basis(rest["weapon"]), basis(current["weapon"])
    rotation = mul(mul(C, mul(transpose(wr), wt)), transpose(C))
    shift = vec(C, vec(transpose(wr), sub(pos(current["weapon"]), pos(rest["weapon"]))))
    offset = magazine_offset(rest, current, progress) if part == "magazine" else [0., 0., 0.]
    display = copy.deepcopy(accepted)
    for context in FP:
        idle = original[context]
        base = xyz(idle["rotation"])
        active = mul(base, rotation)
        position = add(idle["translation"], vec(base, [32*shift[i]*idle["scale"][i] for i in range(3)]))
        position = add(position, vec(active, [offset[i]*idle["scale"][i] for i in range(3)]))
        if grip == "twohand":
            # Derive current carrier correction dynamically; no copied pivot.
            if twohand[context]["scale"] != idle["scale"]:
                raise ValueError("Carrier scale changed")
            compensation = mul(xyz(twohand[context]["rotation"]), transpose(base))
            carrier = sub(twohand[context]["translation"], vec(compensation, idle["translation"]))
            position = add(vec(compensation, position), carrier)
            active = mul(compensation, active)
        display[context] = {"rotation": euler(active),
                            "translation": [round(v, 8) for v in position],
                            "scale": list(idle["scale"])}
    return display


def partition(source):
    elements = source["elements"]
    if len(elements) != 85 or [elements[i]["name"] for i in MOVING] != list(MOVING_NAMES):
        raise ValueError("Allied Demand canonical magazine partition changed")
    if any(elements[i]["name"] != name for i, name in FIXED.items()):
        raise ValueError("Allied Demand fixed grip/heel changed")
    parts = {part: [copy.deepcopy(e) for i, e in enumerate(elements)
                    if (i in MOVING) == (part == "magazine")] for part in PARTS}
    # Small hidden continuation inside this magazine, using its exact atlas faces.
    # This is not recovered .blend geometry; the original contains bones only.
    shaft = copy.deepcopy(elements[MOVING[0]])
    shaft.update(name="authored_internal_magazine_shaft",
                 **{"from": [7.64, 8.20, 8.50], "to": [8.36, 10.35, 9.30]})
    parts["magazine"].append(shaft)
    return parts


def expected_output_paths():
    return {MANIFEST, A / f"items/{KEY}.json",
            *(A / f"models/{KEY}_{part}.json" for part in PARTS),
            *(A / f"models/{KEY}_{i:02}_{part}_{grip}.json"
              for i in range(SAMPLES) for part in PARTS for grip in GRIPS)}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Absolute Path -> bytes; do not materialize resources here."""
    root = Path(root).resolve()
    raw = {}
    def read(path):
        if path not in raw:
            raw[path] = (root/path).read_bytes()
        return json.loads(raw[path])
    source, native, twohand, item = read(SOURCE), read(NATIVE), read(TWOHAND)["display"], read(ITEM)
    profile, contacts, framing = read(PROFILE), read(CONTACTS)["weapons"]["allied_demand"], read(FRAMING)
    raw[GENERATOR] = (root/GENERATOR).read_bytes()
    rig_path = root/RIG
    if not rig_path.is_file():
        rig_path = PREP_RIG  # Read-only preparation; never create/install a rig.
    raw[RIG] = rig_path.read_bytes()
    rig = json.loads(raw[RIG])
    action = rig["actions"][SOURCE_ACTION]
    if (rig["group"] != "sidearm_c0461d9d" or rig.get("fallback") is not False
            or "allied_demand" not in rig["weapons"] or len(action["frames"]) != SAMPLES
            or [action["start"], action["end"]] != [1., 67.]
            or not all(name in rig["names"] for name in
                       ("leftShoulder", "leftElbow", "leftWrist", "rightShoulder", "rightElbow", "rightWrist"))):
        raise ValueError("Need original Allied Demand61 shoulder/FK source")
    for i, frame in enumerate(action["frames"]):
        if abs(frame["progress"]-i/INTERVALS) > 1e-12 or not all(name in frame["joints"] for name in rig["names"]):
            raise ValueError("Source61 grid or full chain changed")
    if (profile.get("schemaVersion"), profile.get("stage"), profile.get("weapon"), profile.get("sourceAction")) != (1, "W219", "allied_demand", SOURCE_ACTION):
        raise ValueError("Invalid W219 Allied Demand profile")
    settings = profile["framing"]
    if any(settings.get(k) is not v for k, v in
           {"sourceFullChain": True, "keepMeshSupport": True, "hideSupportAtRest": False}.items()):
        raise ValueError("Ordinary full-chain visible support required")
    effective = {**framing["families"]["sidearm"], **framing.get("weapons", {}).get("allied_demand", {})}
    for key in ("translation", "rotation", "scale", "rightWristRoll"):
        if settings[key] != effective[key]:
            raise ValueError("Existing effective spatial framing drift: " + key)
    reload = {**contacts["reload"], **profile["contacts"]["reload"]}
    if (reload.get("rigAction") != SOURCE_ACTION or reload.get("hand") != "left"
            or reload.get("partHint") != "magazine" or reload.get("policy") != "magazine"
            or reload.get("gripWindow") != list(GRIP_WINDOW)
            or reload["contact"] != contacts["reload"]["contact"]
            or reload["rotation"] != contacts["reload"]["rotation"]):
        raise ValueError("Source left-hand magazine/contact policy changed")
    parts = partition(source)
    allowed = expected_output_paths()
    output = {}
    def emit(path, value):
        if path not in allowed:
            raise ValueError("Output outside owned W219 Allied Demand namespace")
        output[root/path] = encode(value)
    for part in PARTS:
        model = {k: copy.deepcopy(v) for k, v in source.items() if k not in ("elements", "display")}
        model["elements"] = parts[part]
        emit(A / f"models/{KEY}_{part}.json", model)
    entries = []
    for i in range(SAMPLES):
        progress = i/INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A / f"models/{KEY}_{i:02}_{part}_{grip}.json", {
                    "parent": f"destiny:{KEY}_{part}",
                    "display": pose_display(source["display"], twohand, rig, progress, part, grip)})
        def composite(grip):
            return {"type": "minecraft:composite", "models": [
                {"type": "minecraft:model", "model": f"destiny:{KEY}_{i:02}_{part}_{grip}"} for part in PARTS]}
        model = copy.deepcopy(item["model"]) if i in (0, INTERVALS) else {
            "type": "minecraft:condition", "property": "minecraft:custom_model_data", "index": 0,
            "on_true": composite("twohand"), "on_false": composite("native")}
        entries.append({"threshold": float32(progress), "model": model})
    guard = copy.deepcopy(item["model"])
    if (guard.get("type") != "minecraft:select" or guard.get("property") != "minecraft:custom_model_data"
            or guard.get("index", 0) != 0 or [case["when"] for case in guard["cases"]] != ["ads", "inspect"]):
        raise ValueError("Canonical ADS/inspect guards changed")
    guard["fallback"] = {"type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data", "index": 1,
                         "entries": entries, "fallback": copy.deepcopy(item["model"])}
    wrapper = copy.deepcopy(item)
    wrapper["model"] = {"type": "minecraft:select", "property": "minecraft:display_context",
                        "cases": [{"when": list(FP), "model": guard}], "fallback": copy.deepcopy(item["model"])}
    emit(A / f"items/{KEY}.json", wrapper)

    # Count simultaneous components, using max across canonical alternatives.
    def model_count(key, stack=()):
        if key in stack or not key.startswith("destiny:"):
            raise ValueError("Unsupported/cyclic canonical model: " + key)
        model = read(A / ("models/" + key.split(":", 1)[1] + ".json"))
        if "elements" in model:
            return len(model["elements"])
        return model_count(model["parent"], (*stack, key))
    def graph_count(node):
        kind = node["type"]
        if kind == "minecraft:model":
            return model_count(node["model"])
        if kind == "minecraft:composite":
            return sum(graph_count(n) for n in node["models"])
        if kind == "minecraft:condition":
            return max(graph_count(node["on_true"]), graph_count(node["on_false"]))
        children = [case["model"] for key in ("cases", "entries") for case in node.get(key, [])]
        if "fallback" in node:
            children.append(node["fallback"])
        if not children:
            raise ValueError("Unsupported canonical graph: " + kind)
        return max(map(graph_count, children))
    counts = {part: len(values) for part, values in parts.items()}
    reload_count = sum(counts.values())
    canonical_count = max(graph_count(item["model"]), len(native["elements"]))
    maximum = max(reload_count, canonical_count) + ARM_ELEMENT_RESERVE
    if maximum > 1000:
        raise ValueError("Allied Demand plus four ordinary classic arms exceeds1000")
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W219", "weapon": "allied_demand",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": "destiny:" + KEY, "frames": SAMPLES, "intervals": INTERVALS,
        "thresholdEncoding": "float32(i/60)", "progressFloatIndex": 1, "gripFlagIndex": 0,
        "firstPersonContexts": list(FP), "sourceAction": SOURCE_ACTION, "rigAction": SOURCE_ACTION,
        "sourceGroup": rig["group"], "sourceActionName": action["action"],
        "sourceActionSourceRange": [action["start"], action["end"]], "sourceRigSamples": len(action["frames"]),
        "sourceRigPath": str(RIG), "sourceRigReadFrom": str(rig_path),
        "sourceFullChain": True, "keepMeshSupport": True, "hideSupportAtRest": False,
        "sourceCameraRecovered": False, "sourceWeaponMeshRecovered": False,
        "curve": "Original evaluated61 FK; shortest-arc quaternion boundary transition matching shared source_pose; no Lonesome motion knots/pivot/geometry",
        "sourceCoordinateConversion": C, "sourceModelUnitsPerRigUnit": 32,
        "partHint": "magazine", "hand": "left", "policy": "magazine", "gripWindow": list(GRIP_WINDOW),
        "magazineSeatedProgress": .55,
        "normalizedPhases": {"reach": [0,.10], "withdraw": [.10,.35], "returnAndSeat": [.35,.55], "laterHandlingAndRecover": [.55,1]},
        "phasePolicy": "Authored attachment boundaries from source left-wrist excursion; no exported magazine events or finger IK",
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": len(source["elements"]), "partElements": counts,
        "movingIndices": list(MOVING), "movingNames": list(MOVING_NAMES),
        "fixedGripIndices": list(FIXED), "fixedGripNames": list(FIXED.values()),
        "partitionIndices": {part: [i for i in range(len(source["elements"])) if (i in MOVING) == (part == "magazine")] for part in PARTS},
        "partitionRationale": "Own magazine_lower63/floor64 move;83 canonical body solids including fixed grip57 and heel62 remain. One small internal shaft continues this magazine inside the grip.",
        "authoredInternalShaft": parts["magazine"][-1], "addedInternalDetails": 1,
        "hiddenDetailInterpretation": "Authored shaft fitted to existing magazine cross-section/rotation, cloned per-face UVs; absent in armature-only source. No new texture/canonical edits.",
        "canonicalGeometryAndUVPreserved": True, "sourceElementsAndUVSha256": sha(encode(source["elements"])),
        "partElementsAndUVSha256": {part: sha(encode(values)) for part, values in parts.items()},
        "reloadWeaponElements": reload_count, "canonicalWeaponElements": canonical_count,
        "ordinaryFullArmElementsUpperBound": ARM_ELEMENT_RESERVE,
        "reloadWithArmsElementsUpperBound": reload_count+ARM_ELEMENT_RESERVE,
        "maxAssembledElements": maximum, "elementLimit": 1000,
        "budgetBasis": "Max of actual canonical item alternatives and split86, plus four classic112 arm surfaces; alternatives never summed. Shared integrated all-route count pending master.",
        "assembledBudgetVerified": False, "hipEndpoints": [0, INTERVALS],
        "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Exact canonical item graph for0/1, negative inactive, overshoot and non-FP; canonical ADS/inspect guards precede reload",
        "motionAuthorship": "Weapon FK from own fresh source61. Magazine translation is source left-wrist-relative excursion with authored attachment/seat envelope; master fits part contact to palm. No inferred mesh/camera or Lonesome geometry/pivot.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "packFiles": len(output), "totalReturnedFiles": len(allowed),
        "sourceEvidence": profile.get("evidence", []),
        "inputSha256": {str(path): sha(data) for path, data in raw.items()},
        "outputSha256": {str(path.relative_to(root)): sha(data) for path, data in output.items()},
        "limitations": [
            "Master evaluated original .blend read-only; worker read report/FK and viewed actual bone-chain PNG, never independently operated Blender.",
            "ARMATURE ONLY: no weapon mesh, camera, exported magazine events or finger IK; internal shaft/contact/phase boundaries are authored interpretations.",
            "61 poses/60 intervals do not certify native60fps interpolation. Gameplay duration, ammo, cadence, sounds and clocks are unchanged.",
            "No arm stretching, per-axis damping, hiding, camera compensation or new textures.",
            "Master owns original rig installation, shared loaders/routing/full-arm materialization, integrated budget and FIRST/SECOND Vision.",
            "FIRST actual PNG review by this worker, correction or justified nochange, then SECOND remain pending. Final native acceptance is not claimed."]})
    if set(output) != {root/p for p in allowed}:
        raise ValueError("Incomplete W219 Allied Demand output mapping")
    return output
