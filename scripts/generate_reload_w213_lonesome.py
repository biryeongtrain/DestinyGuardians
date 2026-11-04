#!/usr/bin/env python3
"""W213 Lonesome: 61 poses preserving the W164 grip-fed semantic assembly.

Pure standard library. Import and generate(root=ROOT) never write. Master owns
materialization, original-source61/shoulder import, arms and both native reviews.
Authored weapon/heel motion is not recovered source mesh or camera animation.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
ASSET = Path("src/main/resources/assets/destiny")
ART = Path("art/weapons/w213/lonesome")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w213_lonesome.py")
AUTHORED_SOURCE = Path("scripts/generate_reload_w164_lonesome.py")
SOURCE = ASSET / "models/weapon_surface_w123/lonesome.json"
NATIVE = ASSET / "models/weapon/sidearm/lonesome.json"
TWOHAND = ASSET / "models/weapon/sidearm/lonesome_twohand.json"
ITEM = ASSET / "items/weapon/lonesome.json"
TEXTURE = ASSET / "textures/item/weapon/w123/lonesome.png"
CONTACTS = Path("art/weapons/w201/contacts.json")
RIG = Path("art/weapons/w205/rigs/sidearm_c0461d9d.json")
KEY = "weapon_reload_w213_lonesome/lonesome"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "moving")
INTERVALS = 60
SAMPLES = 61
MOVING = (77, 78)
NAMES = ("heel", "heel_lower")
GRIP = (8, 9.44, 8.81)
RIG_ACTION = "80A8A560"
SOURCE_SHA256 = "5420acfac0c21795a37d206091fa2a79373d58ea124bb07351d2c4dacdeb5605"
AUTHORED_SHA256 = "8b551423b84fce176ed43925f277a8f873579ad41cfb33c51d8a9ffea614f365"
# Exact W164 progress, body Euler delta, local translation, tilted-grip travel.
KEYS = (
 (0, (0,0,0), (0,0,0), 0),
 (.15, (18,-5,-12), (-.4,.2,0), 0),
 (.30, (36,-10,-24), (-.8,.5,.3), 3),
 (.45, (40,-12,-27), (-.8,.5,.3), 6.7),
 (.60, (40,-12,-27), (-.8,.5,.3), 5.2),
 (.75, (34,-8,-20), (-.5,.3,.2), 0),
 (.85, (16,-3,-8), (-.2,.1,0), 0),
 (1, (0,0,0), (0,0,0), 0),
)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def float32(value):
    return struct.unpack("!f", struct.pack("!f", value))[0]


def tangents(times, values):
    """Shared C1 weighted harmonic slopes; zero at endpoints, holds, extrema."""
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
    """C1 weighted-harmonic PCHIP; authored holds/extrema remain exact."""
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError("Reload progress must be finite and within 0..1")
    for key in KEYS:
        if progress == key[0]:
            return list(key[1]), list(key[2]), key[3]
    times = [key[0] for key in KEYS]
    index = next(i for i in range(len(KEYS)-1) if progress < times[i+1])
    h = times[index+1]-times[index]
    t = (progress-times[index])/h
    def channel(values):
        if values[index] == values[index+1]:
            return values[index]  # Preserve authored holds bit-for-bit.
        slopes = tangents(times, values)
        return ((2*t**3-3*t**2+1)*values[index]
                + (t**3-2*t**2+t)*h*slopes[index]
                + (-2*t**3+3*t**2)*values[index+1]
                + (t**3-t**2)*h*slopes[index+1])
    return ([channel([k[1][a] for k in KEYS]) for a in range(3)],
            [channel([k[2][a] for k in KEYS]) for a in range(3)],
            channel([k[3] for k in KEYS]))


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
    """Exact W164 local shift/pivot algebra and W30 crossbow compensation."""
    if part not in PARTS or grip not in ("native", "twohand"):
        raise ValueError("Unknown Lonesome part or grip")
    accepted = original if grip == "native" else twohand
    if progress in (0, 1):
        return copy.deepcopy(accepted)
    angles, shift, travel = sample(progress)
    body = xyz(angles)
    pivot = sub(GRIP, (8, 8, 8))
    offset = vec(xyz((-10, 0, 0)), (0, -travel, 0)) if part == "moving" else [0, 0, 0]
    local = add(add(shift, sub(pivot, vec(body, pivot))), vec(body, offset))
    display = copy.deepcopy(accepted)
    for context in FP:
        idle = original[context]
        base = xyz(idle["rotation"])
        delta = vec(base, [local[i]*idle["scale"][i] for i in range(3)])
        rotation = [round(v, 6) for v in euler(mul(base, body))]
        position = [round(v+delta[i], 6) for i, v in enumerate(idle["translation"])]
        if grip == "twohand":
            # Same six-decimal native pose -> inverse-crossbow operation as W164.
            rotation = [round(v, 6) for v in euler(mul(xyz((0, -10, 0)), xyz(rotation)))]
            position = vec(xyz((0, -10, 0)), add(position, (.641864*16, 0, 0)))
            position = [round(position[0], 6), position[1], round(position[2], 6)]
        display[context]["rotation"] = rotation
        display[context]["translation"] = position
    return display


def generate(root=ROOT) -> dict[Path, bytes]:
    """Return absolute Path -> bytes only; this function has no output writes."""
    root = Path(root).resolve()
    variants = [ASSET / f"models/weapon/sidearm/lonesome{suffix}.json"
                for suffix in ("_ads", "_ads_twohand", "_inspect", "_inspect_twohand")]
    inputs = [SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, PROFILE, GENERATOR,
              AUTHORED_SOURCE, CONTACTS, RIG, *variants,
              Path("art/weapons/w123/lonesome/design.json"),
              Path("art/weapons/w123/lonesome/manifest.json"),
              Path("art/weapons/w205/first-person-framing.json"),
              Path("scripts/generate_reload_w212_bygones.py"),
              Path("scripts/build_weapons_w30.py"),
              Path("scripts/rig_arms_w205.py"),
              Path("scripts/skin_arm_models_w204.py")]
    raw = {p: (root/p).read_bytes() for p in inputs}
    source = json.loads(raw[SOURCE])
    native = json.loads(raw[NATIVE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    contacts = json.loads(raw[CONTACTS])["weapons"]["lonesome"]
    if sha(raw[SOURCE]) != SOURCE_SHA256 or sha(raw[AUTHORED_SOURCE]) != AUTHORED_SHA256:
        raise ValueError("Accepted W164 Lonesome source drift; re-audit before materialization")
    elements = source["elements"]
    if (len(elements) != 97 or [elements[i]["name"] for i in MOVING] != list(NAMES)
            or elements[72]["name"] != "grip_core"):
        raise ValueError("Lonesome semantic grip/heel partition changed")
    if profile.get("schemaVersion") != 1 or profile.get("weapon") != "lonesome":
        raise ValueError("Invalid Lonesome profile")
    framing = profile["framing"]
    reload_contact = {**contacts["reload"], **profile.get("contacts", {}).get("reload", {})}
    if (framing.get("sourceFullChain") is not True
            or framing.get("keepMeshSupport") is not True
            or framing.get("hideSupportAtRest") is not False
            or reload_contact.get("rigAction") != RIG_ACTION
            or reload_contact.get("partHint") != "moving"):
        raise ValueError("Lonesome full-chain/contact policy changed")
    if rig.get("fallback") is not False or "lonesome" not in rig["weapons"]:
        raise ValueError("Expected original shared sidearm source family")
    action = rig["actions"][RIG_ACTION]
    # Master owns updating the inherited21 cache to original61 with shoulders.
    # Report the current cache honestly; do not manufacture intermediate FK.
    if len(action["frames"]) not in (21, 61):
        raise ValueError("Unexpected source cache density")
    parts = {part: [copy.deepcopy(e) for i, e in enumerate(elements)
                    if (i in MOVING) == (part == "moving")] for part in PARTS}
    insert = copy.deepcopy(elements[72])
    insert.update(name="authored_internal_magazine", **{"from": [7.6,6.5,8.3], "to": [8.4,11.4,9.3]})
    parts["moving"].append(insert)
    output = {}
    def emit(path, value):
        allowed = (ASSET / "models" / KEY.split("/")[0], ASSET / "items" / KEY.split("/")[0])
        if path != MANIFEST and not any(path.is_relative_to(p) for p in allowed):
            raise ValueError("Output outside W213 Lonesome namespace")
        output[root/path] = encode(value)
    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k, v in source.items() if k not in ("elements", "display")}
        geo["elements"] = parts[part]
        emit(ASSET / f"models/{KEY}_{part}.json", geo)
    entries = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        for part in PARTS:
            for grip in ("native", "twohand"):
                emit(ASSET / f"models/{KEY}_{frame:02}_{part}_{grip}.json", {
                    "parent": f"destiny:{KEY}_{part}",
                    "display": pose_display(source["display"], twohand, progress, part, grip)})
        def composite(grip):
            return {"type": "minecraft:composite", "models": [
                {"type": "minecraft:model", "model": f"destiny:{KEY}_{frame:02}_{part}_{grip}"} for part in PARTS]}
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
            "fallback": {"type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data", "index": 1,
                         "entries": entries, "fallback": copy.deepcopy(item["model"])}}}],
        "fallback": copy.deepcopy(item["model"])}
    emit(ASSET / f"items/{KEY}.json", wrapper)
    counts = {part: len(values) for part, values in parts.items()}
    # Current shared classic arm surfaces:112 per forearm/upper arm; slim is lower.
    arms = 4*112
    reload_count = sum(counts.values())
    canonical_count = len(native["elements"])
    maximum = max(reload_count, canonical_count) + arms
    if maximum > 1000:
        raise ValueError("Lonesome weapon plus ordinary full arms exceeds element limit")
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W213", "weapon": "lonesome",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0,
        "thresholdEncoding": "float32(i/60)", "firstPersonContexts": list(FP),
        "curve": "C1 PCHIP; shared weighted-harmonic tangents; zero at endpoints/holds/extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "authoredTimingSource": str(AUTHORED_SOURCE),
        "normalizedPhases": {"raise": [0,.15], "withdraw": [.15,.45], "insert": [.45,.75], "recover": [.75,1]},
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": len(elements), "partElements": counts,
        "movingIndices": list(MOVING), "movingNames": list(NAMES),
        "addedInternalDetails": 1, "fixedGripIndex": 72,
        "partitionRationale": "95 body; heel77/heel_lower78 plus exact W164 internal insert form3 moving solids. Fixed grip72 remains solid; seated insert intersects hidden grip as before.",
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {p: sha(encode(v)) for p, v in parts.items()},
        "geometryAndUVPreserved": True,
        "reloadWeaponElements": reload_count, "canonicalWeaponElements": canonical_count,
        "ordinaryFullArmElementsUpperBound": arms,
        "reloadWithArmsElementsUpperBound": reload_count+arms,
        "maxAssembledElements": maximum, "elementLimit": 1000,
        "budgetBasis": "Alternative canonical236 or split98, plus four classic112 arm segments; master verifies actual composed graph.",
        "hipEndpoints": [0, INTERVALS], "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Canonical graph at negative progress, endpoints and non-FP; ADS/inspect precede reload dispatch.",
        "sourceGroup": rig["group"], "rigAction": RIG_ACTION, "partHint": "moving",
        "sourceActionSourceRange": [action["start"], action["end"]],
        "currentSharedRigSamples": len(action["frames"]), "requiredIntegratedSourceSamples": SAMPLES,
        "sourceFullChain": True, "sourceActionWeaponExclusive": False, "sourceCameraRecovered": False,
        "sourceEvidence": profile.get("evidence", []),
        "motionAuthorship": "Exact W164 part knots/holds, PCHIP between knots; original shared-family FK/shoulders and normal fingerless player-skin arm materialization are master-owned.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "packFiles": len(output), "totalReturnedFiles": len(output)+1,
        "inputSha256": {str(p): sha(v) for p, v in raw.items()},
        "outputSha256": {str(p.relative_to(root)): sha(v) for p, v in output.items()},
        "limitations": [
            "Shared family ARMATURE ONLY, no mesh/camera or weapon-exclusive selector claim.",
            "61 bank poses do not establish native60fps or change server pacing.",
            "Original61 shoulder cache import, loader/runtime60grid and ordinary arm integration remain master-owned.",
            "Keep REST mesh offsets plus original wrist FK; reload.contact relocates held part relative to palm, not the source chain.",
            "No stretch, attenuation, hiding, finger IK or native acceptance claim.",
            "FIRST Vision feedback, image-backed worker review/correction and SECOND Vision pending."]})
    return output
