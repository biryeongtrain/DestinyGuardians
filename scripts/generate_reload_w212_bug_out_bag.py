#!/usr/bin/env python3
"""W212 Bug-Out Bag: pure 61-pose reload bank over accepted semantic solids.

generate(root=ROOT) returns absolute Path -> bytes; import and generation never
write. Master owns materialization, shared routing, source rig cache and QA.
W166 authored weapon motion is retained; source-chain arms use shared 80A8A170.
"""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path("src/main/resources/assets/destiny")
SOURCE = A / "models/weapon_surface_w123/bug_out_bag.json"
TWOHAND = A / "models/weapon/submachine_gun/bug_out_bag_twohand.json"
ITEM = A / "items/weapon/bug_out_bag.json"
TEXTURE = A / "textures/item/weapon/w123/bug_out_bag.png"
DESIGN = Path("art/weapons/w123/bug_out_bag/design.json")
CONTACTS = Path("art/weapons/w201/contacts.json")
RIG = Path("art/weapons/w205/rigs/submachine_gun_cdf8185c.json")
PROFILE = Path("art/weapons/w212/bug_out_bag/profile.json")
GENERATOR = Path("scripts/generate_reload_w212_bug_out_bag.py")
PRIOR = Path("scripts/generate_reload_w166_bug_out_bag.py")
MANIFEST = Path("art/weapons/w212/bug_out_bag/manifest.json")
KEY = "weapon_reload_w212_bug_out_bag/bug_out_bag"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "moving")
INTERVALS = 60
SAMPLES = INTERVALS + 1
MOVING = (63, 64, 65, 66)
NAMES = ("magazine_core", "magazine_front_spine", "magazine_rear_spine", "magazine_base")
GRIP = (8, 9.12, 7.42)
RIG_ACTION = "80A8A170"
# Exact W166 knots: full body/magazine hold .34..46; magazine seated
# through .10 and from .66. These are authored timing, not extracted IK.
KEYS = (
    (0., (0, 0, 0), (0, 0, 0), (0, 0, 0)),
    (.10, (28, -5, -8), (.10, .25, -.20), (0, 0, 0)),
    (.20, (64, -10, -16), (.20, .60, -.45), (-.12, -.85, .04)),
    (.34, (57, -13, -19), (.15, .50, -.40), (-.65, -5.20, .20)),
    (.46, (57, -13, -19), (.15, .50, -.40), (-.65, -5.20, .20)),
    (.60, (61, -11, -17), (.15, .65, -.45), (-.12, -1.50, .06)),
    (.66, (64, -9, -15), (.12, .70, -.50), (0, 0, 0)),
    (.78, (39, -5, -9), (.05, .30, -.30), (0, 0, 0)),
    (1., (0, 0, 0), (0, 0, 0), (0, 0, 0)),
)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack("!f", struct.pack("!f", value))[0]


def tangents(times, values):
    """PCHIP weighted harmonic tangents; zero endpoints, holds and extrema."""
    steps = [b-a for a, b in zip(times, times[1:])]
    secants = [(b-a)/h for a, b, h in zip(values, values[1:], steps)]
    slopes = [0.0] * len(times)
    for i in range(1, len(times)-1):
        before, after = secants[i-1], secants[i]
        if before * after > 0:
            w1 = 2*steps[i] + steps[i-1]
            w2 = steps[i] + 2*steps[i-1]
            slopes[i] = (w1+w2)/(w1/before + w2/after)
    return slopes


def sample(progress):
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError("Reload progress must be finite and within 0..1")
    for key in KEYS:
        if progress == key[0]:
            return tuple(list(v) for v in key[1:])
    times = [key[0] for key in KEYS]
    index = next(i for i in range(len(KEYS)-1) if progress < times[i+1])
    h = times[index+1] - times[index]
    t = (progress-times[index])/h
    h00, h10 = 2*t**3-3*t**2+1, t**3-2*t**2+t
    h01, h11 = -2*t**3+3*t**2, t**3-t**2
    result = []
    for channel in range(1, 4):
        vector = []
        for axis in range(3):
            values = [key[channel][axis] for key in KEYS]
            slopes = tangents(times, values)
            vector.append(h00*values[index] + h10*h*slopes[index]
                          + h01*values[index+1] + h11*h*slopes[index+1])
        result.append(vector)
    return tuple(result)


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


def pose_display(original, twohand, progress, part, grip):
    """Stdlib port of W166 rigid body/grip algebra; only sampling changes."""
    accepted = original if grip == "native" else twohand
    if progress in (0, 1):
        return copy.deepcopy(accepted)
    angles, shift, offset = sample(progress)
    body = xyz(angles)
    h = sub(GRIP, (8, 8, 8))
    local = add(sub(h, vec(body, h)),
                vec(body, offset if part == "moving" else (0, 0, 0)))
    display = copy.deepcopy(accepted)
    for context in FP:
        idle = original[context]
        base = xyz(idle["rotation"])
        scale = idle["scale"]
        if len(set(scale)) != 1:
            raise ValueError("Rigid part motion requires uniform accepted FP scale")
        rotation = mul(base, body)
        position = add(add(idle["translation"], shift),
                       vec(base, [scale[0]*v for v in local]))
        if grip == "twohand":
            compensation = mul(xyz(twohand[context]["rotation"]), transpose(base))
            carrier = sub(twohand[context]["translation"],
                          vec(compensation, idle["translation"]))
            position = add(vec(compensation, position), carrier)
            rotation = mul(compensation, rotation)
        display[context]["rotation"] = euler(rotation)
        display[context]["translation"] = [round(v, 9) for v in position]
    return display


def _check_authored_constants(raw):
    # Read constants without importing W166's Pillow/numpy or its write-capable CLI.
    constants = {}
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("KEYS", "MOVING", "NAMES", "GRIP"):
                    constants[target.id] = ast.literal_eval(node.value)
    if constants != dict(KEYS=KEYS, MOVING=MOVING, NAMES=NAMES, GRIP=GRIP):
        raise ValueError("W166 authored keys/partition/grip changed; re-audit before generating")


def generate(root=ROOT) -> dict[Path, bytes]:
    """Return absolute output paths -> bytes without creating files or directories."""
    root = Path(root).resolve()
    inputs = (SOURCE, TWOHAND, ITEM, TEXTURE, DESIGN, CONTACTS, RIG, PROFILE,
              PRIOR, GENERATOR, Path("art/weapons/w205/first-person-framing.json"))
    raw_inputs = {path: (root/path).read_bytes() for path in inputs}
    source = json.loads(raw_inputs[SOURCE])
    twohand = json.loads(raw_inputs[TWOHAND])["display"]
    item = json.loads(raw_inputs[ITEM])
    design = json.loads(raw_inputs[DESIGN])
    profile = json.loads(raw_inputs[PROFILE])
    contacts = json.loads(raw_inputs[CONTACTS])["weapons"]["bug_out_bag"]
    rig = json.loads(raw_inputs[RIG])
    _check_authored_constants(raw_inputs[PRIOR])
    if (len(source["elements"]) != 100
            or tuple(source["elements"][i]["name"] for i in MOVING) != NAMES
            or tuple(i for i, p in enumerate(design["parts"]) if p["group"] == "magazine") != MOVING
            or tuple(design["parts"][57]["geometry"]["rotation"]["origin"]) != GRIP):
        raise ValueError("Current semantic Bug-Out Bag magazine/grip partition drift")
    if profile.get("schemaVersion") != 1 or profile.get("weapon") != "bug_out_bag":
        raise ValueError("Invalid W212 Bug-Out Bag profile")
    reload = {**contacts["reload"], **profile.get("contacts", {}).get("reload", {})}
    if reload.get("partHint") != "moving" or reload.get("rigAction") != RIG_ACTION:
        raise ValueError("W212 reload contact must follow moving using source action 80A8A170")
    if "bug_out_bag" not in rig["weapons"] or RIG_ACTION not in rig["actions"]:
        raise ValueError("Missing shared SMG source action")
    for flag, expected in (("sourceFullChain", True), ("keepMeshSupport", True), ("hideSupportAtRest", False)):
        if profile["framing"].get(flag) is not expected:
            raise ValueError("Invalid source-chain framing flag: " + flag)
    output = {}
    allowed = (A/"models/weapon_reload_w212_bug_out_bag", A/"items/weapon_reload_w212_bug_out_bag")

    def emit(path, value):
        if path != MANIFEST and not any(path.is_relative_to(prefix) for prefix in allowed):
            raise ValueError("Output outside W212 Bug-Out Bag namespace")
        output[root/path] = encode(value)

    # Exact canonical elements, face UVs, textures and metadata; only partition.
    counts = {}
    for part in PARTS:
        geometry = {k: copy.deepcopy(v) for k, v in source.items() if k != "elements"}
        geometry["elements"] = [copy.deepcopy(e) for i, e in enumerate(source["elements"])
                                if (i in MOVING) == (part == "moving")]
        counts[part] = len(geometry["elements"])
        emit(A/f"models/{KEY}_{part}.json", geometry)
    entries = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        for part in PARTS:
            for grip in ("native", "twohand"):
                emit(A/f"models/{KEY}_{frame:02}_{part}_{grip}.json", {
                    "parent": f"destiny:{KEY}_{part}",
                    "display": pose_display(source["display"], twohand, progress, part, grip)})

        def composite(grip):
            return {"type": "minecraft:composite", "models": [
                {"type": "minecraft:model", "model": f"destiny:{KEY}_{frame:02}_{part}_{grip}"}
                for part in PARTS]}

        model = copy.deepcopy(item["model"]) if frame in (0, INTERVALS) else {
            "type": "minecraft:condition", "property": "minecraft:custom_model_data", "index": 0,
            "on_true": composite("twohand"), "on_false": composite("native")}
        entries.append({"threshold": float32(progress), "model": model})
    wrapper = copy.deepcopy(item)
    wrapper["model"] = {
        "type": "minecraft:select", "property": "minecraft:display_context",
        "cases": [{"when": list(FP), "model": {
            "type": "minecraft:select", "property": "minecraft:custom_model_data", "index": 0,
            "cases": [{"when": ["ads", "inspect"], "model": copy.deepcopy(item["model"])}],
            "fallback": {
                "type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data", "index": 1,
                "entries": entries, "fallback": copy.deepcopy(item["model"])}}}],
        "fallback": copy.deepcopy(item["model"])}
    emit(A/f"items/{KEY}.json", wrapper)
    if len(output) != 247 or counts != {"body": 96, "moving": 4}:
        raise ValueError("Unexpected W212 output/partition count")
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W212", "weapon": "bug_out_bag",
        "generator": str(GENERATOR), "generatorSha256": sha(raw_inputs[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0,
        "thresholdEncoding": "float32(i/60), matching runtime float quantization",
        "curve": "C1 shape-preserving cubic Hermite; weighted harmonic knot tangents; zero endpoint/hold/extremum tangents",
        "keyframes": KEYS, "gripPivot": GRIP,
        "partition": {"body": {"elements": counts["body"]},
                      "moving": {"elements": counts["moving"], "indices": MOVING, "names": NAMES}},
        "sourceElements": 100, "partCubes": counts, "maxAssembledElements": 100,
        "geometryAndUVUnchanged": True, "geometryAndUVPreserved": True,
        "endpointDisplayExact": True, "fallbackModelExact": True,
        "adsInspectPrecedencePreserved": True, "firstPersonContexts": FP,
        "rigAction": RIG_ACTION, "partHint": "moving",
        "sourceRigGroup": rig["group"],
        "sourceRigSamples": len(rig["actions"][RIG_ACTION]["frames"]),
        "sourceBlendSha256": rig.get("sourceBlendSha256"),
        "authoredTimingSource": str(PRIOR), "gameplayTimingChanged": False,
        "mechanicsOrAudioChanged": False, "nativeGameplayVerified": False,
        "nativeVisibilityAccepted": False, "sourceCameraRecovered": False,
        "rotationConvention": "W166 JOML Rx Ry Rz; R_idle * R_body; rigid local magazine displacement; accepted twohand carrier compensation",
        "assets": len(output),
        "limitations": [
            "W166 weapon/body/magazine motion is authored reference-informed approximation, not recovered weapon-exclusive IK.",
            "Shared family 80A8A170 source is bone-only: no source mesh or camera.",
            "61 pose bank does not establish continuous 60fps; server update cadence is unchanged.",
            "Master owns W212 loader/runtime routing, source61 cache materialization, hand retargeting and FIRST/SECOND native Vision.",
            "Candidate only; no native contact, arm-length, ADS visibility or final acceptance claim."],
        "inputSha256": {str(path): sha(raw) for path, raw in raw_inputs.items()},
        "outputSha256": {str(path.relative_to(root)): sha(raw) for path, raw in output.items()}})
    return output
