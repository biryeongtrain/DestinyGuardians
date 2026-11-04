#!/usr/bin/env python3
"""W213 Aisha's Embrace: exact W171 part keys, 61 PCHIP poses.

Pure stdlib. Import and generate(root) never write. Master owns original source61
import, ordinary fingerless player-skin arms, integration and both native reviews.
The source family is bone-only; magazine motion remains authored.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path("src/main/resources/assets/destiny")
ART = Path("art/weapons/w213/aishas_embrace")
KEY = "weapon_reload_w213_aishas_embrace/aishas_embrace"
SOURCE = A / "models/weapon_surface_w123/aishas_embrace.json"
TWOHAND = A / "models/weapon/scout_rifle/aishas_embrace_twohand.json"
ITEM = A / "items/weapon/aishas_embrace.json"
TEXTURE = A / "textures/item/weapon/w123/aishas_embrace.png"
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
RIG = Path("art/weapons/w205/rigs/scout_rifle_98cec92a.json")
RIG_ACTION = "80A8A345"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "moving")
INTERVALS = 60
SAMPLES = 61
MOVING = (56,57,58,59)
NAMES = ('magazine_feed','magazine_curve','magazine_lower','magazine_floor')
FIXED_HOUSING = (30,35,36,37,38,39,45,46,47,48)
FIXED_NAMES = ('receiver_core','guard_top_bridge','curved_stock_segment_0',
 'curved_stock_segment_1','curved_stock_segment_2','curved_stock_segment_3',
 'grip_frontstrap','palm_block','grip_heel','gold_upper_palm_insert')
GRIP = (8.0,8.850000000000001,10.265)  # source grip_frontstrap rotation origin
MAG_ANCHOR = (8.0,7.725,11.385000000000002)  # source magazine_feed rotation origin
# Source feed top face center after its existing element rotation. Derived point,
# not an extracted Destiny socket/bone. Withdrawal follows negative local feed Y.
PACK_INSERTION_ANCHOR = (8.0,8.27,11.72)
MAG_AXIS = (0,-math.cos(math.radians(31.578165)),-math.sin(math.radians(31.578165)))
def withdrawal(distance): return tuple(distance*v for v in MAG_AXIS)
# Actual ytb7f7nyrl8 84.60..86.40: raise/roll, rear mag down, replacement
# from below, reseat, support arm across action, recover. All numbers authored.
KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.09,(16,-8,10),(.10,.05,-.08),(0,0,0)),
 (.20,(61,-14,24),(.22,.15,-.18),withdrawal(.3)),
 (.30,(62,-14,25),(.22,.15,-.18),withdrawal(4.8)),
 (.38,(60,-13,25),(.22,.15,-.18),withdrawal(4.8)),
 (.46,(59,-12,24),(.22,.15,-.18),withdrawal(2.5)),
 (.54,(58,-12,24),(.22,.20,-.18),(0,0,0)),
 (.62,(28,-5,10),(.14,.12,-.10),(0,0,0)),
 (.78,(25,-7,11),(.12,.10,-.08),(0,0,0)),
 (.88,(15,-4,6),(.07,.04,-.04),(0,0,0)),
 (1., (0,0,0), (0,0,0), (0,0,0)),
)
SOURCE_SHA256 = 'a0dec168016ca1d3245519b93ffc74bb1df207a929063d13db74540b2dce5c5d'


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

def generate(root=ROOT) -> dict[Path, bytes]:
    """Return absolute output paths and bytes without materializing outputs."""
    root = Path(root).resolve()
    generator = Path("scripts/generate_reload_w213_aishas_embrace.py")
    inputs = [SOURCE, TWOHAND, ITEM, TEXTURE, PROFILE, RIG, generator,
              Path("art/weapons/w123/aishas_embrace/design.json"),
              Path("art/weapons/w123/aishas_embrace/manifest.json"),
              Path("art/weapons/w171/aishas_embrace/motion-reference.json"),
              Path("scripts/generate_reload_w171_aishas_embrace.py"),
              Path("src/main/resources/weapon_surface_w123/manifest.json"),
              Path("art/weapons/w201/contacts.json"),
              Path("art/weapons/w205/first-person-framing.json")]
    raw = {p: (root/p).read_bytes() for p in inputs}
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    contacts = json.loads(raw[Path("art/weapons/w201/contacts.json")])["weapons"]["aishas_embrace"]
    reload_contact = {**contacts["reload"], **profile.get("contacts", {}).get("reload", {})}
    if (profile.get("schemaVersion") != 1 or profile.get("weapon") != "aishas_embrace"
            or reload_contact.get("partHint") != "moving"
            or reload_contact.get("rigAction") != RIG_ACTION):
        raise ValueError("W213 Aisha profile/action/part mismatch")
    if sha(raw[SOURCE]) != SOURCE_SHA256:
        raise ValueError("W142 source drift; re-audit geometry and display")
    elements = source["elements"]
    if (len(elements) != 92
            or [elements[i]["name"] for i in MOVING] != list(NAMES)
            or [elements[i]["name"] for i in FIXED_HOUSING] != list(FIXED_NAMES)):
        raise ValueError("Aisha semantic magazine/housing partition drift")
    design = json.loads(raw[Path("art/weapons/w123/aishas_embrace/design.json")])
    if (design["revision"] != "W142"
            or [p["geometry"]["name"] for p in design["parts"] if p["group"] == "magazine"] != list(NAMES)):
        raise ValueError("W142 semantic design drift")
    rules = json.loads(raw[Path("src/main/resources/weapon_surface_w123/manifest.json")])["targets"]
    rule = next(r for r in rules if r["path"] == "assets/destiny/models/weapon/scout_rifle/aishas_embrace.json")
    if (rule["replacement"] != "assets/destiny/models/weapon_surface_w123/aishas_embrace.json"
            or rule["replacementSha256"] != SOURCE_SHA256):
        raise ValueError("Canonical surface mapping drift")
    rig = json.loads(raw[RIG])
    action = rig["actions"][RIG_ACTION]
    geometries = {}
    output = {}

    def emit(path, value):
        allowed = (A / "models/weapon_reload_w213_aishas_embrace",
                   A / "items/weapon_reload_w213_aishas_embrace")
        if path != MANIFEST and not any(path.is_relative_to(p) for p in allowed):
            raise ValueError("Output outside W213 Aisha namespace")
        output[root/path] = encode(value)

    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k, v in source.items() if k != "elements"}
        geo["elements"] = [copy.deepcopy(e) for i, e in enumerate(elements)
                           if (i in MOVING) == (part == "moving")]
        geometries[part] = geo
        emit(A/f"models/{KEY}_{part}.json", geo)
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
    counts = {part: len(geo["elements"]) for part, geo in geometries.items()}
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W213", "weapon": "aishas_embrace",
        "generator": str(generator), "generatorSha256": sha(raw[generator]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "thresholdEncoding": "float32(i/60), matching master runtime grid",
        "progressFloatIndex": 1, "gripFlagIndex": 0, "firstPersonContexts": list(FP),
        "curve": "C1 shape-preserving Hermite with shared weighted-harmonic slopes; zero only at endpoints, holds and extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "magazineAnchor": MAG_ANCHOR,
        "packInsertionAnchor": PACK_INSERTION_ANCHOR, "magazineExtractionAxis": MAG_AXIS,
        "normalizedPhases": {"raiseRollAccess": [0, .20], "withdrawGuess": [.20, .30],
                             "exchangeBelowFrame": [.30, .38], "insertGuess": [.38, .54],
                             "actionAreaSweep": [.54, .78], "recover": [.78, 1]},
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": 92, "partElements": counts, "sourceCubes": 92, "partCubes": counts,
        "maxAssembledElements": sum(counts.values()), "elementLimit": 1000,
        "elementCountScope": "Weapon body+moving only; master must add simultaneously emitted ordinary player-skin arms before acceptance",
        "remainingElementAllowanceForArms": 1000-sum(counts.values()),
        "combinedWeaponAndArmsBudgetVerified": False,
        "movingIndices": list(MOVING), "movingNames": list(NAMES),
        "fixedHousingIndices": list(FIXED_HOUSING), "fixedHousingNames": list(FIXED_NAMES),
        "partitionRationale": "Existing W142 magazine feed/curve/lower/floor 56..59 move together. Fixed receiver, grip_frontstrap, palm_block, grip_heel, gold_upper_palm_insert and stock remain body.",
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {p: sha(encode(g["elements"])) for p, g in geometries.items()},
        "geometryAndUVPreserved": True, "hipEndpoints": [0, INTERVALS],
        "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Exact canonical graph for inactive negative progress and non-FP; ADS/inspect precede reload dispatch",
        "rigAction": RIG_ACTION, "rigActionName": action["action"], "partHint": "moving",
        "sourceGroup": rig["group"], "sourceFullChain": True,
        "sourceActionWeaponExclusive": False, "sourceCameraRecovered": False,
        "sourceCacheSamplesAtGeneration": len(action["frames"]),
        "source61ImportOwnedByMaster": True,
        "originalBlendEvidence": profile.get("evidence", []),
        "motionAuthorship": "Exact W171 authored part knots/holds, same rigid pivot/magazine-anchor algebra; W212 weighted-harmonic PCHIP. Original shared family FK drives master-owned arms; no recovered mesh or magazine trajectory.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "assets": len(output), "packFiles": len(output),
        "limitations": [
            "Bone-only original has no mesh/camera. Shared scout selector does not establish weapon-exclusive action selection.",
            "Original FK and ordinary arm lengths remain master-owned; no stretch, attenuation or hiding to mask fit.",
            "61 poses do not prove vanilla 60fps continuous interpolation.",
            "FIRST Vision, image-backed worker response and SECOND Vision remain pending; no native acceptance claimed."],
        "inputSha256": {str(p): sha(b) for p, b in raw.items()},
        "outputSha256": {str(p.relative_to(root)): sha(b) for p, b in output.items()}})
    expected = {root/A/f"models/{KEY}_{part}.json" for part in PARTS}
    expected.update(root/A/f"models/{KEY}_{i:02}_{part}_{grip}.json"
                    for i in range(SAMPLES) for part in PARTS for grip in ("native", "twohand"))
    expected.update((root/A/f"items/{KEY}.json", root/MANIFEST))
    if set(output) != expected:
        raise ValueError("W213 output ownership mismatch")
    return output
