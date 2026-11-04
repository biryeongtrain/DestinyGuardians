#!/usr/bin/env python3
"""W213 Steelfeather Repeater: unchanged W166 knots, 61-pose PCHIP bank.

Pure stdlib: import and generate(root=ROOT) never write or execute old generators.
The master owns source-chain integration, arms, materialization and native review.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
ASSET = Path("src/main/resources/assets/destiny")
A = ASSET
ART = Path("art/weapons/w213/steelfeather_repeater")
KEY = "weapon_reload_w213_steelfeather_repeater/steelfeather_repeater"
SOURCE = ASSET / "models/weapon_surface_w123/steelfeather_repeater.json"
TWOHAND = ASSET / "models/weapon/auto_rifle/steelfeather_repeater_twohand.json"
ITEM = ASSET / "items/weapon/steelfeather_repeater.json"
TEXTURE = ASSET / "textures/item/weapon/w123/steelfeather_repeater.png"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w213_steelfeather_repeater.py")
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "moving")
INTERVALS = 60
SAMPLES = INTERVALS + 1
RIG_ACTION = "80A8A395"
SOURCE_SHA256 = "436102933704423c0b27f72da5400c520f8e00c2b715fca2f63f2127d2f1124f"
FIXED_NAMES = ("magwell", "magwell_gold_trim")
# Shared hands builder reserves <=112 elements per classic/slim arm segment.
ARM_ELEMENT_RESERVE = 4 * 112
MOVING = (45, 46, 47, 48)
NAMES = ('magazine_core', 'magazine_side_bevel_-1', 'magazine_side_bevel_1', 'magazine_floor')
FIXED_MAGWELL = (49, 50)
GRIP = (8, 8.31, 8.195)

# Exact W166 authored knots: exchange hold .40..55; seated from .74.
KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.10,(18,-5,-15),(-.15,.35,-.15),(0,0,0)),
 (.20,(36,-11,-30),(-.35,.85,-.45),(0,-.25,0)),
 (.30,(29,-9,-23),(-.4,.65,-.5),(-.45,-3.9,.1)),
 (.40,(28,-9,-22),(-.4,.65,-.5),(-.65,-6.1,.2)),
 (.55,(28,-9,-22),(-.4,.65,-.5),(-.65,-6.1,.2)),
 (.66,(29,-9,-23),(-.4,.7,-.5),(-.25,-2.7,.1)),
 (.74,(36,-11,-29),(-.3,1.0,-.55),(0,0,0)),
 (.82,(30,-8,-23),(-.2,.65,-.35),(0,0,0)),
 (1., (0,0,0), (0,0,0), (0,0,0)),
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
    """Evaluate the unchanged authored knots with shape-preserving Hermite."""
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError("Reload progress must be finite and within 0..1")
    for key in KEYS:
        if progress == key[0]:
            return tuple(list(v) for v in key[1:])
    times = [key[0] for key in KEYS]
    index = next(i for i in range(len(KEYS)-1) if progress < times[i+1])
    h = times[index+1]-times[index]
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
    """W166 rigid-body/pivot algebra, with only the scalar curve replaced."""
    if part not in PARTS or grip not in ("native", "twohand"):
        raise ValueError("Unknown Steelfeather part or grip")
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
            raise ValueError("Rigid part motion requires uniform first-person scale")
        rotation = mul(base, body)
        position = add(add(idle["translation"], shift),
                       vec(base, [scale[0]*v for v in local]))
        if grip == "twohand":
            compensation = mul(xyz(twohand[context]["rotation"]), transpose(base))
            carrier = sub(twohand[context]["translation"], vec(compensation, idle["translation"]))
            position = add(vec(compensation, position), carrier)
            rotation = mul(compensation, rotation)
        display[context]["rotation"] = euler(rotation)
        display[context]["translation"] = [round(v, 9) for v in position]
    return display


def generate(root=ROOT) -> dict[Path, bytes]:
    """Return only absolute owned output paths and bytes; perform no writes."""
    root = Path(root).resolve()
    inputs = [SOURCE, TWOHAND, ITEM, TEXTURE,
              Path("art/weapons/w123/steelfeather_repeater/design.json"),
              Path("art/weapons/w123/steelfeather_repeater/manifest.json"),
              Path("scripts/generate_reload_w166_steelfeather_repeater.py"),
              Path("art/weapons/w201/contacts.json"),
              Path("art/weapons/w205/first-person-framing.json"),
              Path("art/weapons/w205/rigs/auto_rifle_943c13a2.json"),
              GENERATOR, ART / "profile.json"]
    raw_inputs = {p: (root/p).read_bytes() for p in inputs}
    source_raw = raw_inputs[SOURCE]
    source = json.loads(source_raw)
    twohand = json.loads(raw_inputs[TWOHAND])["display"]
    item = json.loads(raw_inputs[ITEM])
    profile = json.loads(raw_inputs[ART / "profile.json"])
    if sha(source_raw) != SOURCE_SHA256:
        raise ValueError("Accepted W134 Steelfeather geometry/display changed; re-audit")
    if profile.get("schemaVersion") != 1 or profile.get("weapon") != "steelfeather_repeater":
        raise ValueError("Wrong Steelfeather profile")
    framing = profile["framing"]
    for flag, expected in (("sourceFullChain", True), ("keepMeshSupport", True),
                           ("hideSupportAtRest", False)):
        if framing.get(flag) is not expected:
            raise ValueError("Source-chain/support policy drift: " + flag)
    reload = profile["contacts"]["reload"]
    if reload.get("rigAction") != RIG_ACTION or reload.get("partHint") != "moving":
        raise ValueError("Steelfeather source action or moving-part hint drift")
    elements = source["elements"]
    if (len(elements) != 89
            or [elements[i]["name"] for i in MOVING] != list(NAMES)
            or [elements[i]["name"] for i in FIXED_MAGWELL] != list(FIXED_NAMES)):
        raise ValueError("Steelfeather magazine/fixed-magwell partition changed")
    geometries = {}
    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k, v in source.items() if k not in ("elements", "display")}
        geo["elements"] = [copy.deepcopy(e) for i, e in enumerate(elements)
                           if (i in MOVING) == (part == "moving")]
        geometries[part] = geo
    expected = {ASSET/f"models/{KEY}_{part}.json" for part in PARTS}
    expected.update(ASSET/f"models/{KEY}_{i:02}_{part}_{grip}.json"
                    for i in range(SAMPLES) for part in PARTS for grip in ("native", "twohand"))
    expected.update((ASSET/f"items/{KEY}.json", MANIFEST))
    output = {}

    def emit(path, value):
        if path not in expected:
            raise ValueError("Output outside W213 Steelfeather ownership")
        output[root/path] = encode(value)

    for part in PARTS:
        emit(ASSET/f"models/{KEY}_{part}.json", geometries[part])
    entries = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        for part in PARTS:
            for grip in ("native", "twohand"):
                emit(ASSET/f"models/{KEY}_{frame:02}_{part}_{grip}.json", {
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
    emit(ASSET/f"items/{KEY}.json", wrapper)
    counts = {part: len(geometries[part]["elements"]) for part in PARTS}
    if sum(counts.values()) + ARM_ELEMENT_RESERVE > 1000:
        raise ValueError("Weapon plus ordinary full-chain arm reserve exceeds 1000 elements")
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W213", "weapon": "steelfeather_repeater",
        "generator": str(GENERATOR), "generatorSha256": sha(raw_inputs[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0,
        "thresholdEncoding": "float32(i/60), matching master runtime grid60",
        "firstPersonContexts": list(FP),
        "curve": "C1 shape-preserving cubic Hermite; weighted harmonic knot tangents, zero at endpoints/holds/extrema",
        "keyframes": KEYS, "gripPivot": GRIP,
        "authoredTimingSource": "scripts/generate_reload_w166_steelfeather_repeater.py",
        "normalizedPhases": {"raise": [0, .20], "withdraw": [.20, .40],
                             "exchange": [.40, .55], "insert": [.55, .74],
                             "basePress": [.74, .82], "recover": [.82, 1]},
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(source_raw),
        "sourceElements": len(elements), "partElements": counts,
        "sourceCubes": len(elements), "partCubes": counts,
        "maxAssembledElements": sum(counts.values()), "elementLimit": 1000,
        "ordinaryArmSegmentReserve": 112, "ordinaryArmSegments": 4,
        "ordinaryArmElementReserve": ARM_ELEMENT_RESERVE,
        "maxAssembledWithOrdinaryArms": sum(counts.values()) + ARM_ELEMENT_RESERVE,
        "armBudgetBasis": "Shared master hands builder upper bound: four ordinary fingerless player-skin segments, <=112 emitted elements each; final materialized count is master-owned.",
        "movingIndices": list(MOVING), "movingNames": list(NAMES),
        "fixedMagwellIndices": list(FIXED_MAGWELL), "fixedMagwellNames": list(FIXED_NAMES),
        "partitionRationale": "Only magazine core, two bevels and floor (45..48) detach; magwell and gold trim (49..50) remain body despite sharing the design magazine group.",
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {part: sha(encode(geo["elements"])) for part, geo in geometries.items()},
        "geometryAndUVUnchanged": True, "geometryAndUVPreserved": True,
        "hipEndpoints": [0, INTERVALS], "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Exact canonical graph for negative progress and non-FP; ADS/inspect precede reload dispatch.",
        "rigAction": RIG_ACTION, "partHint": "moving",
        "sourceGroup": "auto_rifle_943c13a2", "sourceFullChain": True,
        "sourceActionWeaponExclusive": False, "sourceCameraRecovered": False,
        "sourceProvenance": copy.deepcopy(profile["sourceProvenance"]),
        "motionAuthorship": "Exact W166 authored part keys/holds with local W212 weighted-harmonic PCHIP; original61 source FK replay, rest mesh offsets and shared weapon parent are master-owned.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "assets": len(output), "packFiles": len(output), "generatedFiles": len(output)+1,
        "limitations": [
            "Original source is shared-family ARMATURE only, without mesh/camera; 395 is an audited candidate, not a weapon-exclusive selector.",
            "61 poses remove /20 bank quantization; server-paced state updates do not prove 60fps interpolation.",
            "Part motion remains authored; no recovered magazine path or physical finger IK is claimed.",
            "Master imports source61 and shoulders, loads this profile/action, routes runtime60 and materializes normal-length skin arms and outputs.",
            "FIRST Vision, image-backed worker correction or documented no-change, and SECOND Vision remain pending."],
        "inputSha256": {str(p): sha(raw) for p, raw in raw_inputs.items()},
        "outputSha256": {str(p.relative_to(root)): sha(raw) for p, raw in output.items()}})
    if set(output) != {root/p for p in expected}:
        raise ValueError("Incomplete W213 Steelfeather output mapping")
    return output
