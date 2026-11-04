#!/usr/bin/env python3
"""W214 Claws of the Wolf: 61 poses of the unchanged W174 rear-magazine motion.

Pure stdlib. Import and generate() do not write; master owns materialization,
source-chain integration, player-skin arms and both native Vision passes.
The part keys remain authored, not a recovered source mesh/camera trajectory.
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
ART = Path("art/weapons/w214/claws_of_the_wolf")
KEY = "weapon_reload_w214_claws_of_the_wolf/claws_of_the_wolf"
SOURCE = ASSET / "models/weapon_surface_w123/claws_of_the_wolf.json"
TWOHAND = ASSET / "models/weapon/pulse_rifle/claws_of_the_wolf_twohand.json"
ITEM = ASSET / "items/weapon/claws_of_the_wolf.json"
TEXTURE = ASSET / "textures/item/weapon/w123/claws_of_the_wolf.png"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w214_claws_of_the_wolf.py")
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "moving")
INTERVALS = 60
SAMPLES = INTERVALS + 1
# Exact audited W174 constants; old generator is never imported or executed.
MOVING = (111,112)

NAMES = ('magazine_core','magazine_floor')

FIXED_HOUSING = (29,30,84,85,86,87,88,91,94,95,96,97,98)

FIXED_NAMES = ('receiver_core','receiver_lower','grip_core','grip_backstrap','grip_heel',
 'rear_action','receiver_wrist','stock_core','stock_lower','stock_lower_rear','stock_butt','stock_toe','stock_tail')

GRIP = (8.,8.215,7.960000000000001)

MAG_ANCHOR = (8.,8.094999999999999,11.335)

MAG_AXIS = (0.,-math.sin(math.radians(101.52372170389735)),math.cos(math.radians(101.52372170389735)))

def withdrawal(distance): return tuple(distance*v for v in MAG_AXIS)

KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.10,(36,-13,-9),(.08,-.06,-.08),(0,0,0)),
 (.22,(80,-24,-15),(.16,.02,-.16),(0,0,0)),
 (.30,(82,-24,-16),(.17,.04,-.18),withdrawal(.2)),
 (.40,(82,-24,-16),(.17,.04,-.18),withdrawal(4.5)),
 (.57,(81,-23,-16),(.17,.04,-.18),withdrawal(4.5)),
 (.68,(81,-23,-16),(.17,.06,-.18),withdrawal(3.0)),
 (.79,(80,-23,-15),(.16,.08,-.16),(0,0,0)),
 (.84,(77,-22,-15),(.15,.12,-.14),(0,0,0)),
 (.93,(32,-9,-6),(.06,.02,-.06),(0,0,0)),
 (1., (0,0,0), (0,0,0), (0,0,0)),
)

SOURCE_SHA256 = 'ecb84f5fce44abe45a7f2d8f36b0e0f7d9e4d5b0b20688c95bb914ea2326a1c3'

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
    if part not in PARTS or grip not in ('native', 'twohand'):
        raise ValueError('Unknown Claws of the Wolf part or grip')
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8))
    anchor=sub(MAG_ANCHOR,(8,8,8))
    # Place the unchanged magazine anchor at its body-carried position plus
    # source-local withdrawal, then subtract its rotated child-space anchor.
    # This is translation only; no recentering or extra magazine spin.
    local=(sub(add(h,vec(body,add(sub(anchor,h),offset))),vec(body,anchor))
           if part=='moving' else sub(h,vec(body,h)))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
        if twohand[context]['scale'] != s: raise ValueError('Grip scale mismatch')
        if len(set(s))!=1: raise ValueError('Rigid part motion requires uniform first-person scale')
        rotation=mul(base,body)
        position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
        if grip=='twohand':
            comp=mul(xyz(twohand[context]['rotation']),transpose(base))
            carrier=sub(twohand[context]['translation'],vec(comp,idle['translation']))
            position=add(vec(comp,position),carrier);rotation=mul(comp,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display


def expected_output_paths():
    paths = {ASSET / f"models/{KEY}_{part}.json" for part in PARTS}
    paths.update(ASSET / f"models/{KEY}_{i:02}_{part}_{grip}.json"
                 for i in range(SAMPLES) for part in PARTS for grip in ("native", "twohand"))
    return paths | {ASSET / f"items/{KEY}.json", MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Return absolute output Path -> bytes, without writing output or caches."""
    root = Path(root).resolve()
    inputs = [SOURCE, TWOHAND, ITEM, TEXTURE,
              Path("src/main/resources/weapon_surface_w123/manifest.json"),
              Path("art/weapons/w123/claws_of_the_wolf/design.json"),
              Path("art/weapons/w123/claws_of_the_wolf/manifest.json"),
              Path("scripts/generate_reload_w174_claws_of_the_wolf.py"),
              Path("scripts/generate_reload_w212_bygones.py"),
              Path("art/weapons/w174/claws_of_the_wolf/motion-reference.json"),
              Path("art/weapons/w201/contacts.json"),
              Path("art/weapons/w205/first-person-framing.json"),
              Path("art/weapons/w205/rigs/pulse_rifle_b4d01502.json"),
              ART / "profile.json", GENERATOR]
    # Snapshot bytes once so input hashes describe exactly what was consumed.
    raw = {p: (root / p).read_bytes() for p in inputs}
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[ART / "profile.json"])
    if sha(raw[SOURCE]) != SOURCE_SHA256:
        raise ValueError("Accepted W138 Claws of the Wolf source changed; re-audit")
    elements = source["elements"]
    if (len(elements) != 128
            or [elements[i]["name"] for i in MOVING] != list(NAMES)
            or [elements[i]["name"] for i in FIXED_HOUSING] != list(FIXED_NAMES)):
        raise ValueError("W138 rear-magazine/housing partition changed")
    design = json.loads(raw[Path("art/weapons/w123/claws_of_the_wolf/design.json")])
    if (design["revision"] != "W138"
            or [p["geometry"]["name"] for p in design["parts"]["full"]
                if p["group"] == "magazine"] != list(NAMES)):
        raise ValueError("Semantic magazine provenance changed")
    rules = json.loads(raw[Path("src/main/resources/weapon_surface_w123/manifest.json")])["targets"]
    rule = next(r for r in rules if r["path"] ==
                "assets/destiny/models/weapon/pulse_rifle/claws_of_the_wolf.json")
    if (rule["replacement"] != "assets/destiny/models/weapon_surface_w123/claws_of_the_wolf.json"
            or rule["replacementSha256"] != SOURCE_SHA256):
        raise ValueError("Selected source mapping changed")
    if (profile["schemaVersion"] != 1 or profile["weapon"] != "claws_of_the_wolf"
            or profile["contacts"]["reload"]["rigAction"] != "80A8A36A"
            or profile["contacts"]["reload"]["partHint"] != "moving"
            or profile["contacts"]["reload"]["policy"] != "magazine"
            or profile["framing"].get("sourceFullChain") is not True
            or profile["framing"].get("keepMeshSupport") is not True
            or profile["framing"].get("hideSupportAtRest") is not False
            or profile["contacts"]["reload"].get("gripWindow") != [.05, .20, .68, .79]):
        raise ValueError("W214 source-chain/contact profile changed")
    rig = json.loads(raw[Path("art/weapons/w205/rigs/pulse_rifle_b4d01502.json")])
    action = rig["actions"]["80A8A36A"]
    if (rig["group"] != "pulse_rifle_b4d01502" or rig.get("cameraExported") is not False
            or len(action["frames"]) != SAMPLES or not rig.get("w214Source61")
            or any(frame["progress"] != i / INTERVALS
                   or not {"weapon", "leftShoulder", "leftElbow", "leftWrist",
                           "rightShoulder", "rightElbow", "rightWrist"} <= frame["joints"].keys()
                   for i, frame in enumerate(action["frames"]))):
        raise ValueError("Master W214 evaluated61 shoulder rig is required")
    geometries = {}
    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k, v in source.items() if k not in ("elements", "display")}
        geo["elements"] = [copy.deepcopy(e) for i, e in enumerate(elements)
                           if (i in MOVING) == (part == "moving")]
        geometries[part] = geo
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError("Output outside W214 Claws of the Wolf namespace")
        output[root / path] = encode(value)

    for part in PARTS:
        emit(ASSET / f"models/{KEY}_{part}.json", geometries[part])
    entries = []
    for frame in range(SAMPLES):
        progress = frame / INTERVALS
        for part in PARTS:
            for grip in ("native", "twohand"):
                emit(ASSET / f"models/{KEY}_{frame:02}_{part}_{grip}.json", {
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
    emit(ASSET / f"items/{KEY}.json", wrapper)
    counts = {part: len(geometries[part]["elements"]) for part in PARTS}
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W214", "weapon": "claws_of_the_wolf",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0,
        "thresholdEncoding": "float32(i/60), matching runtime float quantization",
        "firstPersonContexts": list(FP),
        "curve": "C1 shape-preserving cubic Hermite; weighted harmonic knot tangents, zero at endpoints/holds/extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "magazineAnchor": MAG_ANCHOR,
        "magazineExtractionAxis": MAG_AXIS,
        "authoredTimingSource": "scripts/generate_reload_w174_claws_of_the_wolf.py",
        "normalizedPhases": {"raiseForRearAccess": [0, .22], "withdrawGuess": [.22, .40],
                             "exchangeBelowFrame": [.40, .57], "replacementApproachGuess": [.57, .68],
                             "reseat": [.68, .79], "basePress": [.79, .84], "recover": [.84, 1]},
        "magazineSeatedProgress": .79,
        "gripWindow": profile["contacts"]["reload"]["gripWindow"],
        "sourceObservedSeconds": json.loads(raw[Path("art/weapons/w174/claws_of_the_wolf/motion-reference.json")])["selectedSeconds"],
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": len(elements), "partElements": counts,
        "sourceCubes": len(elements), "partCubes": counts,
        "weaponElements": sum(counts.values()), "bothClassicForearmElements": 224,
        "bothClassicUpperArmElements": 224, "maxAssembledElements": sum(counts.values()) + 448,
        "assembledBudgetVerified": False, "measuredAllRouteElements": None,
        "elementLimit": 1000,
        "assembledBudgetBasis": "Candidate estimate only: 128 weapon + 224 classic forearm + 224 classic upper-arm surfaces = 576; master must measure all materialized routes including arms.",
        "movingIndices": list(MOVING), "movingNames": list(NAMES),
        "fixedHousingIndices": list(FIXED_HOUSING), "fixedHousingNames": list(FIXED_NAMES),
        "partitionRationale": "W138 semantic rear-magazine indices111,112: magazine_core/floor. All126 receiver, stock, grip, guard, wrist housing and optic elements stay body; no duplicate guard/grip, hidden insert or invented geometry.",
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {part: sha(encode(geo["elements"])) for part, geo in geometries.items()},
        "geometryAndUVUnchanged": True, "geometryAndUVPreserved": True,
        "hipEndpoints": [0, INTERVALS], "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Canonical graph for negative progress and non-FP; ADS/inspect precede dense dispatch; canonical endpoint item graphs.",
        "rigAction": "80A8A36A", "rigActionName": action["action"], "partHint": "moving", "sourceGroup": "pulse_rifle_b4d01502",
        "sourceFullChain": True, "sourceActionWeaponExclusive": False, "sourceCameraRecovered": False,
        "sourceReviewEvidence": [e for e in profile.get("evidence", []) if e["role"] in (
            "master_original_blender_evaluation", "evaluated_source61_full_chain", "viewed_bone_only_source_sheet", "shared_family_action_limit")],
        "motionAuthorship": "Exact W174 part knots/holds, grip and magazine-anchor algebra; W212 weighted-harmonic PCHIP only replaces scalar interpolation. Source-chain replay and hands materialization are master-owned.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "assets": len(output), "packFiles": len(output), "generatedFiles": len(allowed), "staticParts": 2,
        "parentDisplayChildren": SAMPLES * len(PARTS) * 2,
        "limitations": [
            "Original source is a shared-family armature only, without mesh/camera or weapon-exclusive selector.",
            "61 poses and 60 thresholds do not establish continuous 60fps client interpolation.",
            "Part path remains authored; no recovered magazine trajectory or finger IK is claimed.",
            "Ordinary fingerless player-skin arms retain source FK and lengths; rest mesh offsets are not reload contact offsets.",
            "First Vision feedback, image-backed worker correction/review and second Vision remain pending."],
        "inputSha256": {str(p): sha(b) for p, b in raw.items()},
        # Manifest cannot contain its own final hash; all other outputs are included.
        "outputSha256": {str(p.relative_to(root)): sha(b) for p, b in output.items()}})
    if set(output) != {root / p for p in allowed}:
        raise ValueError("Incomplete W214 output mapping")
    return output
