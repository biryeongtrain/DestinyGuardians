#!/usr/bin/env python3
"""W214 Halfdan-D: unchanged W180 knots, 61-pose PCHIP bank.

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
ART = Path("art/weapons/w214/halfdan_d")
KEY = "weapon_reload_w214_halfdan_d/halfdan_d"
SOURCE = ASSET / "models/weapon_surface_w123/halfdan_d.json"
TWOHAND = ASSET / "models/weapon/auto_rifle/halfdan_d_twohand.json"
ITEM = ASSET / "items/weapon/halfdan_d.json"
TEXTURE = ASSET / "textures/item/weapon/w123/halfdan_d.png"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w214_halfdan_d.py")
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine")
INTERVALS = 60
SAMPLES = INTERVALS + 1
RIG_ACTION = "80A8A395"
SOURCE_SHA256 = "74405ad3341ee8a0bc6240d29277337415df78421e2cba488bc72f54ad2c33c8"
# Candidate reserve only; master measures all emitted routes.
ARM_ELEMENT_RESERVE = 4 * 112
MOVING = (106, 107, 108, 109)
MAGAZINE_NAMES = ('Magazine_neck', 'Magazine_body', 'Magazine_floor', 'Magazine_heel')
GRIP = (8.0, 8.5, 8.55)
MAG_ANCHOR = (8.0, 10.0, 3.05)

# Exact W180 knots: magazine clear hold .33..53; seated .67.
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0)),
 (.10,(16,-3,17),(.25,-.25,.2),(0,0,0)),
 (.20,(22,-6,23),(.35,-.20,.25),(-.15,-1.3,-.15)),
 (.33,(23,-7,24),(.35,-.20,.25),(-.65,-6.2,-.65)),
 (.53,(24,-6,22),(.35,-.15,.25),(-.65,-6.2,-.65)),
 (.60,(25,-5,21),(.30,-.15,.20),(-.25,-2.8,-.25)),
 (.67,(25,-4,20),(.25,-.1,.15),(0,0,0)),
 (.73,(33,-3,25),(.25,-.05,.15),(0,0,0)),
 (.80,(18,-1,13),(.15,-.10,.1),(0,0,0)),
 (.90,(7,0,4),(.05,-.05,.05),(0,0,0)),
 (1.,(0,0,0),(0,0,0),(0,0,0)),
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


def pose_display(original,twohand,p,part,grip):
    if part not in ('body','magazine') or grip not in ('native','twohand'):raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8));anchor=sub(MAG_ANCHOR,(8,8,8))
    # Rotate both intact canonical parts around pistol contact. Magazine receives only
    # authored source-local withdrawal/clearance; no artificial scaling or generic spin.
    local=(sub(add(h,vec(body,add(sub(anchor,h),offset))),vec(body,anchor))
           if part=='magazine' else sub(h,vec(body,h)))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
        if twohand[context]['scale']!=s or len(set(s))!=1:raise ValueError('Rigid carrier requires equal uniform grip scales')
        rotation=mul(base,body)
        position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
        if grip=='twohand':
            carrier=mul(xyz(twohand[context]['rotation']),transpose(base))
            position=add(vec(carrier,position),sub(twohand[context]['translation'],vec(carrier,idle['translation'])))
            rotation=mul(carrier,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def generate(root=ROOT) -> dict[Path, bytes]:
    """Return only absolute owned output paths and bytes; perform no writes."""
    root = Path(root).resolve()
    inputs = [SOURCE, TWOHAND, ITEM, TEXTURE,
              Path("art/weapons/w123/halfdan_d/design.json"),
              Path("art/weapons/w123/halfdan_d/manifest.json"),
              Path("scripts/generate_reload_w180_halfdan_d.py"),
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
        raise ValueError("Accepted W129 Halfdan-D geometry/display changed; re-audit")
    if profile.get("schemaVersion") != 1 or profile.get("weapon") != "halfdan_d":
        raise ValueError("Wrong Halfdan-D profile")
    framing = profile["framing"]
    for flag, expected in (("sourceFullChain", True), ("keepMeshSupport", True),
                           ("hideSupportAtRest", False)):
        if framing.get(flag) is not expected:
            raise ValueError("Source-chain/support policy drift: " + flag)
    reload = profile["contacts"]["reload"]
    if reload.get("rigAction") != RIG_ACTION or reload.get("partHint") != "magazine":
        raise ValueError("Halfdan-D source action or moving-part hint drift")
    window = reload.get("gripWindow")
    if not (isinstance(window, list) and len(window) == 4
            and 0 <= window[0] < window[1] <= window[2] < window[3] <= 1):
        raise ValueError("Invalid Halfdan-D attachment window")
    elements = source["elements"]
    if (len(elements) != 114
            or tuple(i for i, e in enumerate(elements) if e["name"] in MAGAZINE_NAMES) != MOVING
            or tuple(elements[i]["name"] for i in MOVING) != MAGAZINE_NAMES):
        raise ValueError("Halfdan-D whole four-solid magazine partition changed")
    geometries = {}
    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k, v in source.items() if k not in ("elements", "display")}
        geo["elements"] = [copy.deepcopy(e) for i, e in enumerate(elements)
                           if (i in MOVING) == (part == "magazine")]
        geometries[part] = geo
    expected = {ASSET/f"models/{KEY}_{part}.json" for part in PARTS}
    expected.update(ASSET/f"models/{KEY}_{i:02}_{part}_{grip}.json"
                    for i in range(SAMPLES) for part in PARTS for grip in ("native", "twohand"))
    expected.update((ASSET/f"items/{KEY}.json", MANIFEST))
    output = {}

    def emit(path, value):
        if path not in expected:
            raise ValueError("Output outside W214 Halfdan-D ownership")
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
        "schemaVersion": 1, "stage": "W214", "weapon": "halfdan_d",
        "generator": str(GENERATOR), "generatorSha256": sha(raw_inputs[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0,
        "thresholdEncoding": "float32(i/60), matching master runtime grid60",
        "firstPersonContexts": list(FP),
        "curve": "C1 shape-preserving cubic Hermite; weighted harmonic knot tangents, zero at endpoints/holds/extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "magazineAnchor": MAG_ANCHOR,
        "authoredTimingSource": "scripts/generate_reload_w180_halfdan_d.py",
        "normalizedPhases": {"shallowPresentation": [0, .10], "magazineWithdrawal": [.10, .33],
                             "emptyWellHold": [.33, .53], "replacementAndSeat": [.53, .67],
                             "seatingRock": [.67, .73], "supportRecovery": [.73, .90], "hipReturn": [.90, 1]},
        "magazineSeatedProgress": .67, "reloadGripWindow": copy.deepcopy(window),
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(source_raw),
        "sourceElements": len(elements), "partElements": counts,
        "sourceCubes": len(elements), "partCubes": counts,
        "maxAssembledElements": sum(counts.values()), "elementLimit": 1000,
        "ordinaryArmSegmentReserve": 112, "ordinaryArmSegments": 4,
        "ordinaryArmElementReserve": ARM_ELEMENT_RESERVE,
        "candidateBankElementsWithArmReserve": sum(counts.values()) + ARM_ELEMENT_RESERVE,
        "candidateBudgetIsEstimate": True, "allEmittedRoutesBudgetMeasured": False,
        "armBudgetBasis": "Reload bank only:114 weapon + estimated four ordinary112-element skin-arm segments =562. Native fallback weapon238. Master must measure all emitted routes including arms; no all-route maximum claimed.",
        "movingIndices": list(MOVING), "movingNames": list(MAGAZINE_NAMES),
        "partitionIndices": {part: [i for i in range(len(elements)) if (i in MOVING) == (part == "magazine")] for part in PARTS},
        "partitionRationale": "Four connected Magazine_neck/body/floor/heel solids106..109 detach whole. Well, charging handle, grip, guard, straps and all other elements stay body. Each canonical element/UV occurs once.",
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {part: sha(encode(geo["elements"])) for part, geo in geometries.items()},
        "geometryAndUVUnchanged": True, "geometryAndUVPreserved": True,
        "hipEndpoints": [0, INTERVALS], "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Exact canonical graph for negative progress and non-FP; ADS/inspect precede reload dispatch.",
        "rigAction": RIG_ACTION, "partHint": "magazine",
        "sourceGroup": "auto_rifle_943c13a2", "sourceFullChain": True,
        "currentSharedRigSamples": len(json.loads(raw_inputs[Path("art/weapons/w205/rigs/auto_rifle_943c13a2.json")])["actions"][RIG_ACTION]["frames"]),
        "sourceActionWeaponExclusive": False, "sourceCameraRecovered": False,
        "sourceProvenance": copy.deepcopy(profile["sourceProvenance"]),
        "motionAuthorship": "Exact W180 authored part keys/holds with local weighted-harmonic PCHIP; original61 source FK replay, rest mesh offsets and shared weapon parent are master-owned.",
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
        raise ValueError("Incomplete W214 Halfdan-D output mapping")
    return output
