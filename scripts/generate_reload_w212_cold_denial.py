#!/usr/bin/env python3
"""W212 Cold Denial: 61 poses of the accepted W167 semantic reload.

Standard library only. Import and generate(root=ROOT) do not write anything;
the master materializes the returned absolute Path -> bytes mapping.
Weapon motion is authored W167 motion, not recovered source hand/camera motion.
"""

import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
ASSET = Path("src/main/resources/assets/destiny")
SOURCE = ASSET / "models/weapon_surface_w123/cold_denial.json"
TWOHAND = ASSET / "models/weapon/pulse_rifle/cold_denial_twohand.json"
ITEM = ASSET / "items/weapon/cold_denial.json"
TEXTURE = ASSET / "textures/item/weapon/w123/cold_denial.png"
ART = Path("art/weapons/w212/cold_denial")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w212_cold_denial.py")
AUTHORED_SOURCE = Path("scripts/generate_reload_w167_cold_denial.py")
CURVE_SOURCE = Path("scripts/generate_reload_w208_the_recluse.py")
CONTACTS = Path("art/weapons/w201/contacts.json")
RIG = Path("art/weapons/w205/rigs/pulse_rifle_b4d01502.json")
KEY = "weapon_reload_w212_cold_denial/cold_denial"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "moving")  # Keep W201 reload.partHint="moving".
INTERVALS = 60
SAMPLES = INTERVALS + 1
RIG_ACTION = "80A8A36A"
SOURCE_SHA256 = "3d05d43d54d30b5e540e36843318f543731b0e33e7d5d7233befe63faf0bb220"
MOVING = (90, 91, 92, 93, 94)
NAMES = ("magazine_core", "magazine_edge_11.08", "magazine_edge_13.16",
         "magazine_floor", "magazine_feed_band")
FIXED_MAGWELL = (89,)
GRIP = (8, 8.755, 8.285)
# Exact W167 authored knots; retain every channel and hold. The source skeleton
# supplies the master's hand replay, not these authored weapon/magazine keys.
KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.07,(40,-6,-18),(.1,.05,-.12),(0,0,0)),
 (.16,(76,-11,-48),(.4,.1,-.4),(0,-.2,0)),
 (.23,(80,-12,-50),(.45,0,-.45),(-.15,-3.8,.1)),
 (.30,(80,-12,-50),(.45,0,-.45),(-.35,-6.6,.3)),
 (.46,(80,-12,-50),(.45,0,-.45),(-.35,-6.6,.3)),
 (.56,(80,-12,-50),(.45,0,-.45),(-.2,-3.4,.15)),
 (.65,(77,-11,-47),(.4,0,-.4),(0,0,0)),
 (.72,(72,-10,-44),(.4,-.1,-.35),(0,0,0)),
 (.85,(28,-4,-12),(.15,-.15,-.1),(0,0,0)),
 (1., (0,0,0), (0,0,0), (0,0,0)),
)

def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

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
            slopes = tangents(times, values)
            vector.append(h00*values[index] + h10*h*slopes[index]
                          + h01*values[index+1] + h11*h*slopes[index+1])
        result.append(vector)
    return tuple(result)

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

def pose_display(original,twohand,p,part,grip):
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8))
    local=add(sub(h,vec(body,h)),vec(body,offset if part=='moving' else (0,0,0)))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
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

def generate(root=ROOT) -> dict[Path, bytes]:
    """Return deterministic absolute output paths and bytes, without writes."""
    root = Path(root).resolve()
    inputs = (SOURCE, TWOHAND, ITEM, TEXTURE, PROFILE, CONTACTS, RIG,
              Path("art/weapons/w123/cold_denial/design.json"),
              Path("art/weapons/w205/first-person-framing.json"),
              AUTHORED_SOURCE, CURVE_SOURCE, GENERATOR)
    raw_inputs = {path: (root / path).read_bytes() for path in inputs}
    source = json.loads(raw_inputs[SOURCE])
    twohand = json.loads(raw_inputs[TWOHAND])["display"]
    item = json.loads(raw_inputs[ITEM])
    profile = json.loads(raw_inputs[PROFILE])
    contacts = json.loads(raw_inputs[CONTACTS])["weapons"]["cold_denial"]
    rig = json.loads(raw_inputs[RIG])
    if sha(raw_inputs[SOURCE]) != SOURCE_SHA256:
        raise ValueError("Accepted Cold Denial geometry/display source drift")
    elements = source["elements"]
    if (len(elements) != 100
            or [elements[i]["name"] for i in MOVING] != list(NAMES)
            or elements[89]["name"] != "magazine_socket"):
        raise ValueError("W138 semantic rear-magazine partition drift")
    if profile.get("schemaVersion") != 1 or profile.get("weapon") != "cold_denial":
        raise ValueError("Invalid Cold Denial profile")
    framing = profile["framing"]
    reload_contact = {**contacts["reload"], **profile.get("contacts", {}).get("reload", {})}
    if (framing.get("sourceFullChain") is not True
            or framing.get("keepMeshSupport") is not True
            or framing.get("hideSupportAtRest") is not False
            or reload_contact.get("partHint") != "moving"
            or reload_contact.get("rigAction") != RIG_ACTION):
        raise ValueError("Cold Denial full-chain/contact policy drift")
    action = rig["actions"][RIG_ACTION]
    if (rig.get("fallback") is not False or "cold_denial" not in rig["weapons"]
            or len(action["frames"]) != SAMPLES):
        raise ValueError("Expected shared pulse-rifle 61-sample source action")

    parts = {
        part: [copy.deepcopy(e) for i, e in enumerate(elements)
               if (i in MOVING) == (part == "moving")]
        for part in PARTS
    }
    output = {}

    def emit(path, value):
        allowed = (ASSET / "models" / KEY.split("/")[0],
                   ASSET / "items" / KEY.split("/")[0])
        if path != MANIFEST and not any(path.is_relative_to(p) for p in allowed):
            raise ValueError("Output outside W212 Cold Denial namespace")
        output[root / path] = encode(value)

    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k, v in source.items() if k != "elements"}
        geo["elements"] = parts[part]
        emit(ASSET / f"models/{KEY}_{part}.json", geo)

    entries = []
    for frame in range(SAMPLES):
        progress = frame / INTERVALS
        for part in PARTS:
            for grip in ("native", "twohand"):
                emit(ASSET / f"models/{KEY}_{frame:02}_{part}_{grip}.json", {
                    "parent": f"destiny:{KEY}_{part}",
                    "display": pose_display(source["display"], twohand, progress, part, grip),
                })

        def composite(grip):
            return {"type": "minecraft:composite", "models": [
                {"type": "minecraft:model",
                 "model": f"destiny:{KEY}_{frame:02}_{part}_{grip}"}
                for part in PARTS]}

        # At rest/return use the entire accepted graph, not a split approximation.
        model = copy.deepcopy(item["model"]) if frame in (0, INTERVALS) else {
            "type": "minecraft:condition", "property": "minecraft:custom_model_data",
            "index": 0, "on_true": composite("twohand"), "on_false": composite("native"),
        }
        entries.append({"threshold": float32(progress), "model": model})

    wrapper = copy.deepcopy(item)
    wrapper["model"] = {
        "type": "minecraft:select", "property": "minecraft:display_context",
        "cases": [{"when": list(FP), "model": {
            "type": "minecraft:select", "property": "minecraft:custom_model_data",
            "index": 0,
            "cases": [{"when": ["ads", "inspect"], "model": copy.deepcopy(item["model"])}],
            "fallback": {
                "type": "minecraft:range_dispatch",
                "property": "minecraft:custom_model_data", "index": 1,
                "entries": entries, "fallback": copy.deepcopy(item["model"]),
            },
        }}],
        "fallback": copy.deepcopy(item["model"]),
    }
    emit(ASSET / f"items/{KEY}.json", wrapper)
    expected = {root / ASSET / f"models/{KEY}_{part}.json" for part in PARTS}
    expected.update(root / ASSET / f"models/{KEY}_{i:02}_{part}_{grip}.json"
                    for i in range(SAMPLES) for part in PARTS
                    for grip in ("native", "twohand"))
    expected.add(root / ASSET / f"items/{KEY}.json")
    if set(output) != expected:
        raise ValueError("W212 Cold Denial output set mismatch")

    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W212", "weapon": "cold_denial",
        "generator": str(GENERATOR), "generatorSha256": sha(raw_inputs[GENERATOR]),
        "itemModel": f"destiny:{KEY}",
        "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0,
        "thresholdEncoding": "float32(i/60), matching runtime float quantization",
        "curve": "C1 shape-preserving cubic Hermite; weighted harmonic PCHIP tangents; zero at holds, extrema and endpoints",
        "keyframes": KEYS, "gripPivot": GRIP,
        "authoredTimingSource": str(AUTHORED_SOURCE),
        "normalizedPhases": {
            "raise": [0, .16], "withdraw": [.16, .30], "exchange": [.30, .46],
            "insert": [.46, .65], "seat": [.65, .72], "recover": [.72, 1],
        },
        "firstPersonContexts": list(FP), "partHint": "moving",
        "partition": {
            "body": {"indices": [i for i in range(len(elements)) if i not in MOVING],
                     "elements": len(parts["body"])},
            "moving": {"indices": list(MOVING), "names": list(NAMES),
                       "elements": len(parts["moving"])},
            "fixedMagwellIndices": list(FIXED_MAGWELL),
            "rationale": "Socket 89 stays fixed on rear receiver; detachable core, two edges, floor and feed band 90..94 move as one rigid assembly behind pistol grip.",
        },
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw_inputs[SOURCE]),
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {part: sha(encode(value)) for part, value in parts.items()},
        "sourceElements": len(elements), "bodyElements": len(parts["body"]),
        "movingElements": len(parts["moving"]), "maxAssembledElements": len(elements),
        "elementLimit": 1000, "geometryAndUVUnchanged": True,
        "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Exact canonical item graph for negative progress, non-FP, ADS/inspect precedence and endpoints.",
        "rigGroup": rig["group"], "rigAction": RIG_ACTION,
        "rigActionSamples": len(action["frames"]),
        "rigActionSourceRange": [action["start"], action["end"]],
        "sourceBlendSha256": rig["sourceBlendSha256"],
        "sourceMapSha256": rig["sourceMapSha256"],
        "boneMapSha256": rig["boneMapSha256"],
        "sourceActionWeaponExclusive": False, "sourceCameraRecovered": False,
        "rotationConvention": "W167 JOML Rx Ry Rz; R_idle * R_body; local rigid magazine displacement and grip pivot; accepted twohand carrier compensation.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "timingPolicy": "Original W167 normalized keys and holds preserved; no gameplay duration or source-FPS override.",
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "packFiles": len(output), "generatedFiles": len(output) + 1,
        "inputSha256": {str(path): sha(raw) for path, raw in raw_inputs.items()},
        "outputSha256": {str(path.relative_to(root)): sha(raw) for path, raw in output.items()},
        "limitations": [
            "Weapon/magazine movement is authored W167 motion, not recovered source IK.",
            "Shared pulse-family action is a selected source-chain candidate, not weapon-exclusive evidence.",
            "61 bank poses do not prove continuous 60fps; shared runtime and network pacing remain master-owned.",
            "Ordinary source limb lengths only; no invented source camera, stretch, or native acceptance.",
            "Master owns source-cache integration, materialization, loader/runtime/hands and both native Vision passes.",
            "Output hashes cover every returned pack file; manifest excludes its own self hash.",
        ],
    })
    return output
