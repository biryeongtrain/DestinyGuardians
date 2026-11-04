#!/usr/bin/env python3
"""W212 Bygones: dense W168 authored motion and unchanged semantic solids.

Import and generate() do not write. The master owns materialization and native
review. The part curve is authored, not recovered source mesh/camera motion.
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
ART = Path("art/weapons/w212/bygones")
KEY = "weapon_reload_w212_bygones/bygones"
SOURCE = ASSET / "models/weapon_surface_w123/bygones.json"
TWOHAND = ASSET / "models/weapon/pulse_rifle/bygones_twohand.json"
ITEM = ASSET / "items/weapon/bygones.json"
TEXTURE = ASSET / "textures/item/weapon/w123/bygones.png"
MANIFEST = ART / "manifest.json"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "moving")
INTERVALS = 60
SAMPLES = INTERVALS + 1
MOVING = (106, 107, 108, 109, 110)
NAMES = ("magazine", "magazine_shoulder_-1", "magazine_shoulder_1",
         "magazine_front_spine", "magazine_floorplate")
FIXED_MAGWELL = (82, 98, 99)
FIXED_NAMES = ("receiver_keel", "stock_belly_join", "stock_toe")
GRIP = (8, 8.61, 8.43)
SOURCE_SHA256 = "501fee4fd8f4e23de98df29011ab2a5fd8757907de077aaea5488fb3e01ba3bb"
# Exact W168 authored keys. Body hold .22..57, magazine hold .30..48;
# magazine is seated through .065 and from .68. Do not retime these knots.
KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.065,(46,8,-16),(.18,.08,-.12),(0,0,0)),
 (.13,(78,14,-32),(.35,.12,-.25),(0,-.15,-.029)),
 (.22,(80,14,-34),(.38,.10,-.28),(-.25,-3.8,-.739)),
 (.30,(80,14,-34),(.38,.10,-.28),(-1.15,-6.0,-1.166)),
 (.48,(80,14,-34),(.38,.10,-.28),(-1.15,-6.0,-1.166)),
 (.57,(80,14,-34),(.38,.10,-.28),(-.45,-3.9,-.758)),
 (.68,(79,14,-33),(.36,.10,-.26),(0,0,0)),
 (.74,(81,14,-34),(.36,.19,-.27),(0,0,0)),
 (.80,(73,12,-28),(.30,.06,-.22),(0,0,0)),
 (.89,(31,5,-10),(.12,-.05,-.08),(0,0,0)),
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
    """W168 rigid-body/pivot algebra, with only the scalar curve replaced."""
    if part not in PARTS or grip not in ("native", "twohand"):
        raise ValueError("Unknown Bygones part or grip")
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
    """Return absolute output Path -> bytes; never materialize any output."""
    root = Path(root).resolve()
    inputs = [SOURCE, TWOHAND, ITEM, TEXTURE,
              Path("art/weapons/w123/bygones/design.json"),
              Path("art/weapons/w123/bygones/manifest.json"),
              Path("scripts/generate_reload_w168_bygones.py"),
              Path("scripts/generate_reload_w208_the_recluse.py"),
              Path("art/weapons/w201/contacts.json"),
              Path("art/weapons/w205/first-person-framing.json"),
              Path("art/weapons/w205/rigs/pulse_rifle_b4d01502.json"),
              ART / "profile.json"]
    source_raw = (root/SOURCE).read_bytes()
    source = json.loads(source_raw)
    twohand = json.loads((root/TWOHAND).read_bytes())["display"]
    item = json.loads((root/ITEM).read_bytes())
    if sha(source_raw) != SOURCE_SHA256:
        raise ValueError("Accepted W134 Bygones source changed; re-audit geometry/display")
    elements = source["elements"]
    if (len(elements) != 129
            or [elements[i]["name"] for i in MOVING] != list(NAMES)
            or [elements[i]["name"] for i in FIXED_MAGWELL] != list(FIXED_NAMES)):
        raise ValueError("Bygones semantic rear-magazine partition changed")
    geometries = {}
    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k, v in source.items() if k not in ("elements", "display")}
        geo["elements"] = [copy.deepcopy(e) for i, e in enumerate(elements)
                           if (i in MOVING) == (part == "moving")]
        geometries[part] = geo
    output = {}

    def emit(path, value):
        allowed = (ASSET/"models/weapon_reload_w212_bygones",
                   ASSET/"items/weapon_reload_w212_bygones")
        if path != MANIFEST and not any(path.is_relative_to(p) for p in allowed):
            raise ValueError("Output outside W212 Bygones namespace")
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

        # Canonical endpoints preserve ready/ADS/inspect and grip selection.
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
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W212", "weapon": "bygones",
        "generator": "scripts/generate_reload_w212_bygones.py",
        "generatorSha256": sha((root/"scripts/generate_reload_w212_bygones.py").read_bytes()),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0,
        "thresholdEncoding": "float32(i/60), matching runtime float quantization",
        "firstPersonContexts": list(FP),
        "curve": "C1 shape-preserving cubic Hermite; weighted harmonic knot tangents, zero at endpoints/holds/extrema",
        "keyframes": KEYS, "gripPivot": GRIP,
        "authoredTimingSource": "scripts/generate_reload_w168_bygones.py",
        "normalizedPhases": {"raise": [0, .13], "withdraw": [.13, .30],
                             "exchange": [.30, .48], "insert": [.48, .68],
                             "basePress": [.68, .80], "recover": [.80, 1]},
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(source_raw),
        "sourceElements": len(elements), "partElements": counts,
        "sourceCubes": len(elements), "partCubes": counts,
        "maxAssembledElements": sum(counts.values()), "elementLimit": 1000,
        "movingIndices": list(MOVING), "movingNames": list(NAMES),
        "fixedMagwellIndices": list(FIXED_MAGWELL), "fixedMagwellNames": list(FIXED_NAMES),
        "partitionRationale": "Five rear magazine solids 106..110 detach as moving; receiver_keel 82, stock_belly_join 98 and stock_toe 99 remain body. No explicit magazine_socket solid exists.",
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {part: sha(encode(geo["elements"])) for part, geo in geometries.items()},
        "geometryAndUVUnchanged": True, "geometryAndUVPreserved": True,
        "hipEndpoints": [0, INTERVALS], "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Exact canonical graph for negative progress and non-FP; ADS/inspect precede dense dispatch.",
        "rigAction": "80A8A36A", "partHint": "moving",
        "sourceGroup": "pulse_rifle_b4d01502", "sourceFullChain": True,
        "sourceActionWeaponExclusive": False, "sourceCameraRecovered": False,
        "motionAuthorship": "Exact W168 authored part keys/holds with W208 PCHIP; source-chain replay/rig cache and native QA are master-owned.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "assets": len(output), "packFiles": len(output),
        "limitations": [
            "Original source is bone-only, without mesh/camera; action is shared family evidence.",
            "61 poses remove /20 bank quantization; server-paced state updates are not proof of 60fps interpolation.",
            "Part motion remains authored; no recovered magazine path or finger IK is claimed.",
            "Master integration, first Vision feedback, warranted correction and second Vision remain pending."],
        "inputSha256": {str(p): sha((root/p).read_bytes()) for p in inputs},
        "outputSha256": {str(p.relative_to(root)): sha(raw) for p, raw in output.items()}})
    return output
