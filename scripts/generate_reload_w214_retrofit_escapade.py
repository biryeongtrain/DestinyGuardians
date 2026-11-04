#!/usr/bin/env python3
"""W214 Retrofit Escapade: original-chain profile and 61 authored part poses.

Pure stdlib; import and generate(root=ROOT) never write. Master owns source61
integration, ordinary fingerless player-skin arms, runtime60 and Vision passes.
W181 constants/algebra were statically audited; its generator is never executed.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = ASSET = Path("src/main/resources/assets/destiny")
ART = Path("art/weapons/w214/retrofit_escapade")
KEY = "weapon_reload_w214_retrofit_escapade/retrofit_escapade"
SOURCE = A / "models/weapon_surface_w123/retrofit_escapade.json"
TWOHAND = A / "models/weapon/machine_gun/retrofit_escapade_twohand.json"
ITEM = A / "items/weapon/retrofit_escapade.json"
TEXTURE = A / "textures/item/weapon/w123/retrofit_escapade.png"
GENERATOR = Path("scripts/generate_reload_w214_retrofit_escapade.py")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
RIG = Path("art/weapons/w205/rigs/machine_gun_e5b72131.json")
CONTACTS = Path("art/weapons/w201/contacts.json")
FRAMING = Path("art/weapons/w205/first-person-framing.json")
AUTHORED_SOURCE = Path("scripts/generate_reload_w181_retrofit_escapade.py")
RIG_ACTION = "80A8A005"
SOURCE_GROUP = "machine_gun_e5b72131"
SOURCE_SHA256 = "d7cc409964d15f6e7ed52298d944fb468c3d47e1f1c5f70ee9981977cbe0daba"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine", "cover")
GRIPS = ("native", "twohand")
INTERVALS = 60
SAMPLES = INTERVALS + 1
# Estimate only; master must count all materialized routes including skin overlays.
ARM_ELEMENT_RESERVE = 4 * 112


GRIP=(8.,8.54,8.49)

HINGE=(8.,12.4,-.1)

COVER_NAMES=('receiver_upper_rail', 'receiver_rear_shoulder', 'optic_saddle', 'optic_hood_0', 'optic_hood_1', 'optic_hood_2', 'optic_hood_3', 'optic_hood_4', 'optic_hood_5', 'optic_hood_6', 'optic_hood_7', 'objective_lens', 'ocular_lens', 'ocular_rim_0', 'ocular_rim_1', 'ocular_rim_2', 'ocular_rim_3', 'ocular_rim_4', 'ocular_rim_5', 'ocular_rim_6', 'ocular_rim_7', 'optic_loop_ear_-1', 'optic_loop_ear_1', 'optic_loop_top')

BOLT_NAMES=('charging_handle',)

KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0),0,0),
 (.08,(-6,8,10),(-.15,-.25,.10),(0,0,0),0,0),
 (.18,(-9,13,19),(-.25,-.45,.20),(0,0,0),-96,0),
 (.26,(-9,13,19),(-.25,-.45,.20),(-3.4,-3.8,.3),-96,0),
 (.30,(-9,13,19),(-.25,-.45,.20),(-3.4,-3.8,.3),-96,0),
 (.42,(-9,13,19),(-.25,-.45,.20),(-1.0,-.7,.1),-96,0),
 (.50,(-9,13,19),(-.25,-.45,.20),(0,0,0),-96,0),
 (.58,(-8,12,18),(-.20,-.40,.20),(0,0,0),-96,0),
 (.66,(-6,9,12),(-.15,-.25,.15),(0,0,0),0,0),
 (.80,(17,5,7),(-.10,-.15,.10),(0,0,0),0,1.05),
 (.88,(18,4,5),(-.05,-.10,.05),(0,0,0),0,0),
 (1.,(0,0,0),(0,0,0),(0,0,0),0,0),
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
    """C1 weighted-harmonic PCHIP; exact W181 knots, extrema and holds."""
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError("Reload progress must be finite and within 0..1")
    for key in KEYS:
        if progress == key[0]:
            return tuple(list(v) if isinstance(v, tuple) else v for v in key[1:])
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
    return tuple([channel([key[k][axis] for key in KEYS]) for axis in range(3)]
                 for k in (1, 2, 3)) + tuple(channel([key[k] for key in KEYS]) for k in (4, 5))


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

def is_payload(e):
    return e['name'].startswith(('drum_','round_','feed_join_'))

def articulated_elements(elements,p):
    """Rigid canonical cover assembly and handle. No new faces, cubes, UV or scale.
    Element rotations use Rz Ry Rx; display transforms below use JOML Rx Ry Rz.
    Non-moving elements and both endpoint assemblies retain exact original records.
    """
    _,_,_,cover,bolt=sample(p)
    result=copy.deepcopy(elements)
    for e in result:
        if e['name'] in COVER_NAMES and cover:
            turn=xyz((cover,0,0));center=[(a+b)/2 for a,b in zip(e['from'],e['to'])]
            old=e.get('rotation',{});origin=old.get('origin',center)
            old_angles=[old.get(axis,0) for axis in 'xyz']
            old_r=transpose(xyz([-v for v in old_angles]))
            actual_center=add(origin,vec(old_r,sub(center,origin)))
            new_center=add(HINGE,vec(turn,sub(actual_center,HINGE)))
            delta=sub(new_center,center)
            e['from']=add(e['from'],delta);e['to']=add(e['to'],delta)
            angles=[-v for v in euler(transpose(mul(turn,old_r)))]
            e['rotation']=dict(origin=new_center,**dict(zip('xyz',angles)))
        if e['name'] in BOLT_NAMES and bolt:
            e['from'][2]+=bolt;e['to'][2]+=bolt
            if 'rotation' in e:e['rotation']['origin'][2]+=bolt
    return result

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset,_,_=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8))
    # Drum, all rounds, links and connectors share exactly one rigid local transform.
    local=add(sub(pivot,vec(motion,pivot)),vec(motion,offset) if part=='magazine' else [0,0,0])
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);scale=idle['scale']
        if twohand[context]['scale']!=scale or len(set(scale))!=1:raise ValueError('Expected equal uniform canonical grip scales')
        rotation=mul(base,motion)
        position=add(add(idle['translation'],shift),vec(base,[scale[0]*v for v in local]))
        if grip=='twohand':
            carrier=mul(xyz(twohand[context]['rotation']),transpose(base))
            position=add(vec(carrier,position),sub(twohand[context]['translation'],vec(carrier,idle['translation'])))
            rotation=mul(carrier,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def part_of(element):
    """A complete feed assembly; cover/optic and charging handle never join it."""
    if is_payload(element):
        return "magazine"
    return "cover" if element["name"] in COVER_NAMES else "body"


def expected_output_paths():
    paths = {A/f"models/{KEY}_{part}.json" for part in PARTS}
    paths.update(A/f"models/{KEY}_{frame:02}_{part}_{grip}.json"
                 for frame in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A/f"items/{KEY}.json", MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Return absolute owned output paths and bytes, with no materialization."""
    root = Path(root).resolve()
    inputs = (SOURCE, TWOHAND, ITEM, TEXTURE, GENERATOR, PROFILE, RIG,
              CONTACTS, FRAMING, AUTHORED_SOURCE)
    raw = {path: (root/path).read_bytes() for path in inputs}
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    if sha(raw[SOURCE]) != SOURCE_SHA256:
        raise ValueError("Canonical W136 Retrofit geometry/display changed; re-audit")
    if profile.get("schemaVersion") != 1 or profile.get("weapon") != "retrofit_escapade":
        raise ValueError("Wrong Retrofit presentation profile")
    for flag, expected in (("sourceFullChain", True), ("keepMeshSupport", True),
                           ("hideSupportAtRest", False)):
        if profile["framing"].get(flag) is not expected:
            raise ValueError("Full-chain/support policy drift: " + flag)
    contact = json.loads(raw[CONTACTS])["weapons"]["retrofit_escapade"]
    reload = {**contact["reload"], **profile.get("contacts", {}).get("reload", {})}
    if (reload.get("rigAction") != RIG_ACTION or reload.get("partHint") != "magazine"
            or reload.get("policy") != "magazine"):
        raise ValueError("Retrofit action or coherent drum/belt contact policy drift")
    start, attached, release, end = reload["gripWindow"]
    if not 0 <= start < attached <= release < end <= 1:
        raise ValueError("Invalid Retrofit handling envelope")
    if rig.get("group") != SOURCE_GROUP or rig.get("sourceBlendSha256") != profile["sourceProvenance"]["sourceBlendSha256"]:
        raise ValueError("Wrong original source-chain provenance")
    action = rig["actions"][RIG_ACTION]
    frames = action["frames"]
    chain = ("leftShoulder", "leftElbow", "leftWrist", "rightShoulder", "rightElbow", "rightWrist", "weapon")
    if len(frames) != SAMPLES or (action["start"], action["end"]) != (1, 180):
        raise ValueError("Master must seed the evaluated original61 action first")
    for i, frame in enumerate(frames):
        if frame["progress"] != i/INTERVALS or any(name not in frame["joints"] for name in chain):
            raise ValueError("Missing uniform original61 full-chain sample")
        for name in chain:
            matrix = frame["joints"][name]
            if len(matrix) != 4 or any(len(row) != 4 or any(not math.isfinite(v) for v in row) for row in matrix):
                raise ValueError("Invalid source joint matrix")
    elements = source["elements"]
    if (len(elements) != 134 or len({e["name"] for e in elements}) != 134
            or set(COVER_NAMES) - {e["name"] for e in elements}
            or set(BOLT_NAMES) - {e["name"] for e in elements}):
        raise ValueError("Retrofit canonical semantic membership drift")
    geometries = {}
    indices = {}
    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k, v in source.items() if k != "elements"}
        indices[part] = [i for i, e in enumerate(elements) if part_of(e) == part]
        geo["elements"] = [copy.deepcopy(elements[i]) for i in indices[part]]
        geometries[part] = geo
    counts = {part: len(geo["elements"]) for part, geo in geometries.items()}
    if counts != {"body": 59, "magazine": 51, "cover": 24}:
        raise ValueError("Coherent drum/belt, cover/optic or independent handle partition drift")
    if sum(counts.values()) + ARM_ELEMENT_RESERVE > 1000:
        raise ValueError("Weapon plus estimated ordinary-arm reserve exceeds 1000")
    allowed = expected_output_paths()
    output = {}
    def emit(path, value):
        if path not in allowed:
            raise ValueError("Output outside W214 Retrofit ownership")
        output[root/path] = encode(value)
    for part in PARTS:
        emit(A/f"models/{KEY}_{part}.json", geometries[part])
    entries = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        for part in PARTS:
            # Same audited W181 articulation applied to disjoint parts:
            # body contains only the charging handle, cover only cover/optic.
            posed = (articulated_elements(geometries[part]["elements"], progress)
                     if part != "magazine" else geometries[part]["elements"])
            for grip in GRIPS:
                child = {"parent": f"destiny:{KEY}_{part}",
                         "display": pose_display(source["display"], twohand, progress, part, grip)}
                if posed != geometries[part]["elements"]:
                    child["elements"] = posed
                emit(A/f"models/{KEY}_{frame:02}_{part}_{grip}.json", child)
        def composite(grip):
            return {"type": "minecraft:composite", "models": [
                {"type": "minecraft:model", "model": f"destiny:{KEY}_{frame:02}_{part}_{grip}"}
                for part in PARTS]}
        model = copy.deepcopy(item["model"]) if frame in (0, INTERVALS) else {
            "type": "minecraft:condition", "property": "minecraft:custom_model_data", "index": 0,
            "on_true": composite("twohand"), "on_false": composite("native")}
        entries.append({"threshold": float32(progress), "model": model})
    dispatch = {"type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data", "index": 1,
                "entries": entries, "fallback": copy.deepcopy(item["model"])}
    guard = copy.deepcopy(item["model"])
    guard["fallback"] = dispatch  # Keep the complete original ADS/inspect cases.
    wrapper = copy.deepcopy(item)
    wrapper["model"] = {"type": "minecraft:select", "property": "minecraft:display_context",
                        "cases": [{"when": list(FP), "model": guard}],
                        "fallback": copy.deepcopy(item["model"])}
    emit(A/f"items/{KEY}.json", wrapper)
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W214", "weapon": "retrofit_escapade",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0, "firstPersonContexts": list(FP),
        "thresholdEncoding": "float32(i/60), matching master runtime grid60",
        "curve": "C1 weighted harmonic PCHIP; exact authored knots/holds, zero slopes at endpoints/holds/extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "coverHinge": HINGE, "drumAnchor": [6.52, 8.47, 3.92],
        "authoredTimingSource": str(AUTHORED_SOURCE),
        "normalizedPhases": {"present": [0, .08], "openCoverAndOptic": [.08, .18],
                             "withdrawCompleteFeed": [.18, .26], "occludedExchange": [.26, .30],
                             "returnDrumAndBelt": [.30, .50], "seatFeed": [.50, .58],
                             "closeCoverAndOptic": [.58, .66], "sideAction": [.66, .80],
                             "release": [.80, .88], "recover": [.88, 1]},
        "magazineSeatedProgress": .50, "gripWindow": reload["gripWindow"],
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": len(elements), "sourceCubes": len(elements),
        "parts": list(PARTS), "partElements": counts, "partCubes": counts, "partitionIndices": indices,
        "coverNames": COVER_NAMES, "chargingHandleNames": BOLT_NAMES,
        "weaponElements": sum(counts.values()), "maxAssembledElements": sum(counts.values()),
        "elementLimit": 1000, "ordinaryArmElementReserve": ARM_ELEMENT_RESERVE,
        "maxAssembledWithOrdinaryArmsEstimate": sum(counts.values()) + ARM_ELEMENT_RESERVE,
        "budgetStatus": "estimate; master must count all final routes including ordinary skin and overlay segments",
        "payloadPolicy": "All10 drum/neck solids,35 cartridge/link solids and6 feed connectors share one magazine display and one master palm-contact shift. Cover/optic and charging handle remain independent.",
        "partitionRationale": "W181 body83 is split into body59 and cover/optic24. Its independent handle remains body-local and translates only in the authored side-action phase. No canonical solid is added, deleted or retextured.",
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {part: sha(encode(geo["elements"])) for part, geo in geometries.items()},
        "geometryAndUVPreserved": True, "addedElements": 0, "triangleAdapterElements": 0,
        "hipEndpoints": [0, INTERVALS], "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Original complete item graph at both endpoints, negative progress and non-FP; original ADS/inspect cases precede dense reload dispatch.",
        "sourceGroup": SOURCE_GROUP, "rigAction": RIG_ACTION, "rigActionName": action["action"],
        "partHint": "magazine", "sourceFullChain": True, "sourceActionWeaponExclusive": False,
        "sourceCameraRecovered": False, "sourceMeshRecovered": False, "handIK": False,
        "sourceProvenance": copy.deepcopy(profile["sourceProvenance"]),
        "motionAuthorship": "Exact W181 knots, holds, pivot, hinge and independently articulated cover/handle algebra; only scalar interpolation changes. Original FK, ordinary-length fingerless player-skin arms and shared source weapon parent are master-owned.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "assets": len(output), "packFiles": len(output), "generatedFiles": len(output)+1,
        "staticParts": len(PARTS), "parentDisplayChildren": SAMPLES*len(PARTS)*len(GRIPS),
        "limitations": [
            "Worker read master Blender evaluation and viewed bone-only sheet; worker did not open Blender.",
            "Shared-family action has no recovered mesh/camera or weapon-exclusive selector.",
            "Grip window is an authored candidate ending before cover closure/charging, requiring FIRST image review.",
            "61 source/part poses and60 thresholds do not establish continuous60fps interpolation.",
            "Final ordinary player-skin arm and overlay budget, FIRST feedback, worker correction/no-change review and SECOND Vision remain master-owned and pending."],
        "inputSha256": {str(path): sha(data) for path, data in raw.items()},
        "outputSha256": {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root/path for path in allowed} or len(output) != 371:
        raise ValueError("Expected exactly370 pack outputs and one manifest")
    return output

