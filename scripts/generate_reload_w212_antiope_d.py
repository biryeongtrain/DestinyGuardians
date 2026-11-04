#!/usr/bin/env python3
"""W212 Antiope-D dense reload and source-chain integration contract.

Pure standard-library port of the W182 semantic split and rigid carrier.
Authored W182 knots are retained; W208 PCHIP replaces per-key smoothstop.
Import and generate() never write. The master owns materialization and native QA.
The original shared-family source bones inform hands, not a recovered weapon mesh.
"""
import copy
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path("src/main/resources/assets/destiny")
ART = Path("art/weapons/w212/antiope_d")
KEY = "weapon_reload_w212_antiope_d/antiope_d"
SOURCE = A / "models/weapon_surface_w123/antiope_d.json"
TWOHAND = A / "models/weapon/submachine_gun/antiope_d_twohand.json"
ITEM = A / "items/weapon/antiope_d.json"
TEXTURE = A / "textures/item/weapon/w123/antiope_d.png"
PARTS = ("body", "magazine")
INTERVALS = 60
SAMPLES = INTERVALS + 1

# Master evaluated ORIGINAL source.blend separately; worker reviewed its report,
# actual matrices and bone-only sheet, never claiming an independent Blender run.
SOURCE_EVALUATION = {
    "group": "submachine_gun_cdf8185c",
    "rigAction": "80A8A170",
    "action": "Armature|fp_80A8A170_reload_full|Base",
    "slot": "OBSlot",
    "sourceNames": ["reload_full", "reload_empty"],
    "sourceFrameRange": [1.0, 91.0],
    "fps": 30,
    "samples": 61,
    "sharedFamilyAction": True,
    "weaponExclusive": False,
    "objects": [{"name": "Armature", "type": "ARMATURE"}],
    "sourceCameraRecovered": False,
    "space": "armature_object",
    "matrixConvention": "row-major, column vectors; matrix_world not applied",
    "masterReportsAllInputsUnchanged": True,
    "maxPriorCacheJointAbsError": 0.0,
    "inputSha256": {
        "sourceBlend": "474d2fb3e1b97e605ed54998e6a08311a0cba7f44e826f0b98f44076302caba6",
        "sourceMap": "ccf84b37d2f0b48a4ffd196ab31e19e48d169ed40363e80215bad6333e57cd34",
        "boneMap": "dfb12f16b062776714efec4bda53470ae694c0ec223773e9d3b48c688c522bf9",
        "priorCache": "3f39125de0d3e6f65cc98932e84dc9c88e3b75fbe5f28eb4a227962b75b89a22",
    },
    "reviewedEvidenceSha256": {
        "source-review.json": "a30b83e9b4babbfefe70e09ad3be2b36488b945e29b6b865656e2bce45966db5",
        "submachine_gun_cdf8185c.json": "d09352a9bd907ed80efdf4a46f4436500c4ed354175538d4fcf7b832bec6043f",
        "sheets/submachine_gun_cdf8185c-80A8A170-upper-chain.png":
            "e04731565886e7c6bd52e3c860bfe1de156792f9bd815bb0553597ea334b9164",
    },
}

# Original W182 authored values, holds, anchors and matrix algebra, ported without
# importing/executing its PIL/NumPy preview and historical-output writer.
FP=('firstperson_righthand','firstperson_lefthand')

MAGAZINE_NAMES=('magazine_core','magazine_front_spine','magazine_back_spine','magazine_floor','magazine_pull_front')

GRIP=(8.,9.35,9.45)

MAG_ANCHOR=(8.,8.16,8.675)

KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0)),
 (.08,(14,-5,18),(.15,-.10,.1),(0,-1.5,0)),
 (.16,(33,-9,43),(.40,.10,.2),(-.6,-7.4,.25)),
 (.27,(19,-9,32),(.30,-.10,.2),(-.6,-7.4,.25)),
 (.40,(20,-9,32),(.30,-.10,.2),(-.6,-7.4,.25)),
 (.50,(24,-8,35),(.25,-.05,.15),(-.2,-3.2,.05)),
 (.60,(28,-7,38),(.20,.05,.15),(0,0,0)),
 (.68,(29,-7,36),(.20,.10,.15),(0,0,0)),
 (.77,(14,-3,19),(.10,-.05,.1),(0,0,0)),
 (.90,(4,-1,5),(.03,-.03,.03),(0,0,0)),
 (1.,(0,0,0),(0,0,0),(0,0,0)),
)

def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()

def sha(b):return hashlib.sha256(b).hexdigest()

def add(a,b): return [x+y for x,y in zip(a,b)]

def sub(a,b): return [x-y for x,y in zip(a,b)]

def mul(a,b): return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def vec(m,v): return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]

def transpose(m): return list(map(list,zip(*m)))

def xyz(angles):
    x,y,z=map(math.radians,angles);a,b,c,d,e,f=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return [[c*e,-c*f,d],[b*d*e+a*f,-b*d*f+a*e,-b*c],[-a*d*e+b*f,a*d*f+b*e,a*c]]

def euler(m):
    b=math.asin(max(-1.,min(1.,m[0][2])))
    a,c=(math.atan2(-m[1][2],m[2][2]),math.atan2(-m[0][1],m[0][0])) if abs(math.cos(b))>1e-8 else (math.atan2(m[2][1],m[1][1]),0)
    return [round(math.degrees(v),9) for v in (a,b,c)]

def partition(source):
    """Five connected canonical magazine solids; pistol grip and charging handle stay fixed.
    Each original element appears exactly once, with every field/UV value retained.
    """
    parts={}
    for part in ('body','magazine'):
        model={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        model['elements']=[copy.deepcopy(e) for e in source['elements'] if (e['name'] in MAGAZINE_NAMES)==(part=='magazine')]
        parts[part]=model
    return parts

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


def float32(value):
    return struct.unpack("!f", struct.pack("!f", value))[0]

def tangents(times, values):
    """Shape-preserving PCHIP: shared derivative at knots; zero at holds/extrema.

    Weighted harmonic means preserve monotone spans without overshoot. Endpoint
    slopes are explicitly zero to settle into and out of the accepted idle pose.
    """
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
    times = [k[0] for k in KEYS]
    index = next(i for i in range(len(KEYS)-1) if progress < times[i+1])
    h = times[index+1]-times[index]
    t = (progress-times[index])/h
    h00, h10 = 2*t**3-3*t**2+1, t**3-2*t**2+t
    h01, h11 = -2*t**3+3*t**2, t**3-t**2
    result = []
    for channel in range(1, 4):
        vector = []
        for axis in range(3):
            values = [k[channel][axis] for k in KEYS]
            if values[index] == values[index+1]:
                vector.append(values[index])  # Preserve authored holds exactly.
                continue
            slopes = tangents(times, values)
            vector.append(h00*values[index] + h10*h*slopes[index]
                          + h01*values[index+1] + h11*h*slopes[index+1])
        result.append(vector)
    return tuple(result)


def generate(root=ROOT) -> dict[Path, bytes]:
    """Return absolute Path -> bytes; no output files or directories are written."""
    root = Path(root).resolve()
    inputs = [
        SOURCE, TWOHAND, ITEM, TEXTURE,
        Path("scripts/generate_reload_w182_antiope_d.py"),
        Path("scripts/generate_reload_w208_the_recluse.py"),
        Path("scripts/generate_reload_w212_antiope_d.py"),
        Path("art/weapons/w123/antiope_d/design.json"),
        Path("art/weapons/w123/antiope_d/manifest.json"),
        Path("art/weapons/w201/contacts.json"),
        Path("art/weapons/w205/first-person-framing.json"),
        Path("art/weapons/w205/rigs/submachine_gun_cdf8185c.json"),
        ART / "profile.json",
        Path("src/main/resources/destiny/weapons/w46-timing.json"),
        Path("src/main/resources/destiny/sounds/w63-reload.json"),
    ]
    inputs.extend(A / f"models/weapon/submachine_gun/antiope_d{suffix}.json"
                  for suffix in ("", "_ads", "_ads_twohand", "_inspect", "_inspect_twohand"))
    inputs.extend(A / f"items/{folder}/antiope_d.json"
                  for folder in ("weapon_aim_w70", "weapon_sight_w153"))
    source = json.loads((root/SOURCE).read_bytes())
    twohand = json.loads((root/TWOHAND).read_bytes())["display"]
    item = json.loads((root/ITEM).read_bytes())
    parts = partition(source)
    counts = {part: len(model["elements"]) for part, model in parts.items()}
    names = [e["name"] for e in parts["magazine"]["elements"]]
    if counts != {"body": 113, "magazine": 5} or Counter(names) != Counter(MAGAZINE_NAMES):
        raise ValueError("Current Antiope-D semantic partition changed; re-audit mesh")
    packed = lambda e: json.dumps(e, sort_keys=True, separators=(",", ":"))
    joined = [e for part in PARTS for e in parts[part]["elements"]]
    if Counter(map(packed, joined)) != Counter(map(packed, source["elements"])):
        raise ValueError("Parts must retain every canonical element and UV exactly once")

    output = {}
    def emit(path, value):
        allowed = (A/"models/weapon_reload_w212_antiope_d",
                   A/"items/weapon_reload_w212_antiope_d")
        if path != ART/"manifest.json" and not any(path.is_relative_to(p) for p in allowed):
            raise ValueError("Output outside W212 Antiope-D namespace")
        output[root/path] = encode(value)

    for part, model in parts.items():
        emit(A/f"models/{KEY}_{part}.json", model)
    entries = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        for part in PARTS:
            for grip in ("native", "twohand"):
                emit(A/f"models/{KEY}_{frame:02}_{part}_{grip}.json", {
                    "parent": f"destiny:{KEY}_{part}",
                    "display": pose_display(source["display"], twohand, progress, part, grip),
                })
        def composite(grip):
            return {"type": "minecraft:composite", "models": [
                {"type": "minecraft:model", "model": f"destiny:{KEY}_{frame:02}_{part}_{grip}"}
                for part in PARTS]}
        # Endpoints route the exact accepted item graph as well as retaining exact
        # native/twohand displays in their emitted children.
        model = copy.deepcopy(item["model"]) if frame in (0, INTERVALS) else {
            "type": "minecraft:condition", "property": "minecraft:custom_model_data", "index": 0,
            "on_true": composite("twohand"), "on_false": composite("native")}
        entries.append({"threshold": float32(progress), "model": model})

    reload = {"type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data",
              "index": 1, "entries": entries, "fallback": copy.deepcopy(item["model"])}
    # Preserve the exact accepted mode cases, including ADS and inspect precedence.
    mode_guard = copy.deepcopy(item["model"])
    mode_guard["fallback"] = reload
    wrapper = copy.deepcopy(item)
    wrapper["model"] = {
        "type": "minecraft:select", "property": "minecraft:display_context",
        "cases": [{"when": list(FP), "model": mode_guard}],
        "fallback": copy.deepcopy(item["model"])}
    emit(A/f"items/{KEY}.json", wrapper)

    emit(ART/"manifest.json", {
        "schemaVersion": 1, "stage": "W212", "weapon": "antiope_d",
        "generator": "scripts/generate_reload_w212_antiope_d.py",
        "generatorSha256": sha((root/"scripts/generate_reload_w212_antiope_d.py").read_bytes()),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0,
        "firstPersonContexts": list(FP),
        "thresholdEncoding": "float32(i/60), matching runtime float quantization",
        "curve": "C1 shape-preserving cubic Hermite; weighted harmonic PCHIP tangents; zero at endpoints, holds and extrema",
        "keyframes": KEYS, "authoredTimingSource": "scripts/generate_reload_w182_antiope_d.py",
        "gripPivot": GRIP, "magazineAnchor": MAG_ANCHOR,
        "normalizedPhases": {
            "liftAndWithdraw": [0, .16], "settleRolledGripSocket": [.16, .27],
            "emptyGripSocketHold": [.27, .40], "replacementApproachAndSeat": [.40, .60],
            "seatingRock": [.60, .68], "supportForwardRecovery": [.68, .90], "hipReturn": [.90, 1]},
        "sourceGeometryPath": str(SOURCE), "sourceElements": len(source["elements"]),
        "partCubes": counts, "sourceCubes": len(source["elements"]),
        "bodyElements": counts["body"], "movingElements": counts["magazine"],
        "maxAssembledElements": len(joined), "triangleAdapterElements": 0, "addedElements": 0,
        "partitionIndices": {
            part: [i for i, e in enumerate(source["elements"])
                   if (e["name"] in MAGAZINE_NAMES) == (part == "magazine")]
            for part in PARTS},
        "magazineNames": MAGAZINE_NAMES,
        "partitionRationale": "Five intact grip-fed magazine solids form one rigid part; fixed pistol grip, foregrip and charging handle stay on body; every original element/UV retained exactly once.",
        "geometryAndUVUnchanged": True, "geometryAndUVPreserved": True,
        "endpointDisplayExact": True, "fallbackModelExact": True,
        "adsInspectPrecedencePreserved": True, "nonFirstPersonGraphExact": True,
        "hipEndpoints": [0, INTERVALS], "partHint": "magazine", "rigAction": "80A8A170",
        "sourceEvaluation": SOURCE_EVALUATION,
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "timingPolicy": "Normalized visuals only; existing gameplay duration, ammunition transfer, combat and audio untouched.",
        "sourceCameraRecovered": False, "nativeGameplayVerified": False,
        "nativeVisibilityAccepted": False, "thirdPersonReloadClaimed": False,
        "assets": len(output), "generatedFiles": len(output)+1,
        "evidence": [
            "/private/tmp/destiny-w212-source/source-review.json",
            "/private/tmp/destiny-w212-source/submachine_gun_cdf8185c.json",
            "/private/tmp/destiny-w212-source/sheets/submachine_gun_cdf8185c-80A8A170-upper-chain.png",
            "art/weapons/w123/antiope_d/comparison.png",
            "art/weapons/w201/contacts.json",
            "https://www.youtube.com/watch?v=M3tC-IkkFRU"],
        "limitations": [
            "Weapon trajectory is the authored W182 Antiope-D approximation; original shared-family bones do not bind the semantic weapon mesh or recover contact/finger IK.",
            "Hidden exchange remains one intact magazine proxy, with original authored clearance, pivots and seating rock.",
            "61 bank poses do not prove continuous native 60fps interpolation; item updates remain server-paced.",
            "Master owns source61 rig materialization, W212 loader/runtime routing, hands generation, native FIRST review, corrections and SECOND review.",
            "FIRST native Vision screenshots have not yet been received; no native acceptance."],
        "inputSha256": {str(path): sha((root/path).read_bytes()) for path in inputs},
        # The manifest cannot hash itself; hashes cover all 247 returned pack assets.
        "outputSha256": {str(path.relative_to(root)): sha(raw) for path, raw in output.items()},
    })
    if len(output) != 248:
        raise ValueError("Expected 247 pack assets plus one returned-only manifest")
    return output
