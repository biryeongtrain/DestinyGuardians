#!/usr/bin/env python3
"""W215 Fixed Odds: 61 authored part poses for the evaluated original arm chain.

Pure stdlib. Importing and generate(root=ROOT) never write or launch processes.
Master owns fresh source61 rig/action binding, ordinary player-skin arms,
output materialization, shared routes, FIRST feedback and SECOND acceptance.
W179 constants and rigid articulation are retained; scalar curves use C1 PCHIP.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = ASSET = Path("src/main/resources/assets/destiny")
ART = Path("art/weapons/w215/fixed_odds")
KEY = "weapon_reload_w215_fixed_odds/fixed_odds"
SOURCE = A / "models/weapon_surface_w123/fixed_odds.json"
TWOHAND = A / "models/weapon/machine_gun/fixed_odds_twohand.json"
ITEM = A / "items/weapon/fixed_odds.json"
TEXTURE = A / "textures/item/weapon/w123/fixed_odds.png"
GENERATOR = Path("scripts/generate_reload_w215_fixed_odds.py")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
RIG = Path("art/weapons/w205/rigs/machine_gun_82e319a0.json")
CONTACTS = Path("art/weapons/w201/contacts.json")
FRAMING = Path("art/weapons/w205/first-person-framing.json")
AUTHORED_SOURCE = Path("scripts/generate_reload_w179_fixed_odds.py")
SOURCE_GROUP = "machine_gun_82e319a0"
RIG_ACTION = "80A8A005"
INTERVALS = 60
SAMPLES = INTERVALS + 1
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine", "cover")
GRIPS = ("native", "twohand")
# Four ordinary skin/overlay arm segments; final composed counts are master-owned.
ARM_ELEMENT_RESERVE = 4 * 112
SOURCE_SHA256 = "593ade9e46dae518f28588890ce6e5f8a6b343113b419515c5b47f608b431761"
TEXTURE_SHA256 = "a4f5a08c0e74e565f8174505e361b7409ad35e3129e00cd8d514411a0fdfd769"
ITEM_SHA256 = "4c62589daf0642d5ea3147eb01c273e5d891f47b0028c1d92ac9c0e8d957c921"
# W179 authored knots: cover seats .82; the complete box/belt seats .68.
# Hidden clearances, pivots and angles are authored, not recovered mesh/IK data.


GRIP=(8.,8.7,8.3)

HINGE=(8.,11.91,3.17)

COVER_NAMES=('feed_roof','rear_action','rear_cheek_inlay_-1','rear_cheek_inlay_1','rear_purple_pin_-1','rear_purple_pin_1','rear_sight_pedestal','rear_sight_base','rear_sight_arch_-1','rear_sight_arch_1')

BOLT_NAMES=('charging_shaft','charging_knob')

KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0),0,0),
 (.08,(-5,-9,-12),(-.1,-.35,.15),(0,0,0),0,0),
 (.20,(-9,-16,-24),(-.15,-.55,.25),(0,0,0),-103,0),
 (.28,(-9,-16,-24),(-.15,-.55,.25),(1.1,-.15,0),-103,0),
 (.40,(-9,-16,-24),(-.15,-.55,.25),(4.0,-3.2,.5),-103,0),
 (.48,(-9,-16,-24),(-.15,-.55,.25),(4.0,-3.2,.5),-103,0),
 (.60,(-8,-15,-23),(-.15,-.50,.25),(1.2,-.15,0),-103,0),
 (.68,(-8,-15,-23),(-.15,-.50,.25),(0,0,0),-103,0),
 (.74,(-8,-15,-23),(-.15,-.50,.25),(0,0,0),-103,0),
 (.82,(-5,-10,-15),(-.10,-.30,.15),(0,0,0),0,0),
 (.89,(13,-6,-9),(-.05,-.15,.10),(0,0,0),0,1.1),
 (.94,(16,-4,-5),(0,-.10,.05),(0,0,0),0,0),
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
    """C1 weighted-harmonic PCHIP; exact W179 knots, extrema and holds."""
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
    return e['name'].startswith(('ammo_box_','belt_','feed_join_'))

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
    # Box, all rounds, links and connectors share exactly one rigid local transform.
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
    """Keep all five box solids, seven linked rounds and six connectors together."""
    if is_payload(element):
        return "magazine"
    return "cover" if element["name"] in COVER_NAMES else "body"


def expected_output_paths():
    paths = {A/f"models/{KEY}_{part}.json" for part in PARTS}
    paths.update(A/f"models/{KEY}_{frame:02}_{part}_{grip}.json"
                 for frame in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A/f"items/{KEY}.json", MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Return absolute output Path -> bytes records; never materialize assets."""
    root = Path(root).resolve()
    inputs = (SOURCE, TWOHAND, ITEM, TEXTURE, GENERATOR, PROFILE, RIG,
              CONTACTS, FRAMING, AUTHORED_SOURCE)
    raw = {path: (root/path).read_bytes() for path in inputs}
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    for path, expected in ((SOURCE, SOURCE_SHA256), (TEXTURE, TEXTURE_SHA256),
                           (ITEM, ITEM_SHA256)):
        if sha(raw[path]) != expected:
            raise ValueError("Canonical Fixed Odds input changed; re-audit: " + str(path))
    if profile.get("schemaVersion") != 1 or profile.get("weapon") != "fixed_odds":
        raise ValueError("Wrong Fixed Odds presentation profile")
    for flag, expected in (("sourceFullChain", True), ("keepMeshSupport", True),
                           ("hideSupportAtRest", False)):
        if profile["framing"].get(flag) is not expected:
            raise ValueError("Full-chain/support policy drift: " + flag)
    contact = json.loads(raw[CONTACTS])["weapons"]["fixed_odds"]
    reload = {**contact["reload"], **profile.get("contacts", {}).get("reload", {})}
    if (profile.get("sourceAction") != RIG_ACTION or reload.get("rigAction") != RIG_ACTION
            or reload.get("partHint") != "magazine" or reload.get("policy") != "magazine"):
        raise ValueError("Fixed Odds action or coherent box/belt contact policy drift")
    window = reload["gripWindow"]
    if len(window) != 4 or not all(math.isfinite(v) for v in window):
        raise ValueError("Invalid Fixed Odds handling envelope")
    start, attached, release, end = window
    if not 0 <= start < attached <= release < end <= .68:
        raise ValueError("Box/belt must release by its authored .68 seat")
    provenance = profile["sourceProvenance"]
    if rig.get("group") != SOURCE_GROUP or not rig.get("fallback"):
        raise ValueError("Expected evaluated fallback machine-gun family")
    for field in ("sourceBlendSha256", "sourceMapSha256", "boneMapSha256"):
        if rig.get(field) != provenance[field]:
            raise ValueError("Wrong original source-chain provenance: " + field)
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
    names = {e["name"] for e in elements}
    if (len(elements) != 153 or len(names) != 153
            or set(COVER_NAMES) - names or set(BOLT_NAMES) - names):
        raise ValueError("Fixed Odds canonical semantic membership drift")
    geometries, indices = {}, {}
    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k, v in source.items() if k != "elements"}
        indices[part] = [i for i, element in enumerate(elements) if part_of(element) == part]
        geo["elements"] = [copy.deepcopy(elements[i]) for i in indices[part]]
        geometries[part] = geo
    counts = {part: len(geo["elements"]) for part, geo in geometries.items()}
    if counts != {"body": 104, "magazine": 39, "cover": 10}:
        raise ValueError("Complete box/belt, cover or independent charging-handle partition drift")
    # Resolve the existing item graph read-only, including inherited native,
    # twohand, ADS and inspect geometry. Count alternatives by maximum, not sum.
    def existing_elements(key, stack=()):
        if key in stack or not key.startswith("destiny:"):
            raise ValueError("Unsupported/cyclic canonical model: " + key)
        path = A/"models"/(key.removeprefix("destiny:") + ".json")
        if path not in raw:
            raw[path] = (root/path).read_bytes()
        model = json.loads(raw[path])
        if "elements" in model:
            return len(model["elements"])
        return existing_elements(model["parent"], (*stack, key))
    def existing_graph_budget(node):
        if isinstance(node, list):
            return max((existing_graph_budget(value) for value in node), default=0)
        if not isinstance(node, dict):
            return 0
        if node.get("type") == "minecraft:model":
            return existing_elements(node["model"])
        if node.get("type") == "minecraft:composite":
            return sum(existing_graph_budget(value) for value in node["models"])
        return max((existing_graph_budget(value) for value in node.values()), default=0)
    fallback_elements = existing_graph_budget(item["model"])
    weapon_max = max(sum(counts.values()), fallback_elements)
    if weapon_max + ARM_ELEMENT_RESERVE > 1000:
        raise ValueError("Weapon plus ordinary full-chain arm reserve exceeds 1000 elements")
    allowed = expected_output_paths()
    output = {}
    def emit(path, value):
        if path not in allowed:
            raise ValueError("Output outside W215 Fixed Odds ownership")
        output[root/path] = encode(value)
    for part in PARTS:
        emit(A/f"models/{KEY}_{part}.json", geometries[part])
    entries = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        for part in PARTS:
            # W179's same rigid algebra, applied to disjoint memberships:
            # cover/sight hinge; body-local handle travel; coherent box/belt.
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
    if item["model"].get("type") != "minecraft:select" or item["model"].get("property") != "minecraft:custom_model_data":
        raise ValueError("Re-audit changed canonical ADS/inspect selector")
    guard = copy.deepcopy(item["model"])
    guard["fallback"] = dispatch  # Original ADS/inspect cases retain precedence.
    wrapper = copy.deepcopy(item)
    wrapper["model"] = {"type": "minecraft:select", "property": "minecraft:display_context",
                        "cases": [{"when": list(FP), "model": guard}],
                        "fallback": copy.deepcopy(item["model"])}
    emit(A/f"items/{KEY}.json", wrapper)
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W215", "weapon": "fixed_odds",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0, "firstPersonContexts": list(FP),
        "thresholdEncoding": "61 float32(i/60) thresholds; master binds runtime grid60",
        "curve": "C1 weighted harmonic PCHIP; exact W179 knots/holds; zero slopes only at endpoints, holds and extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "coverHinge": HINGE,
        "authoredTimingSource": str(AUTHORED_SOURCE),
        "normalizedPhases": {"present": [0, .08], "openCover": [.08, .20],
                             "boxAndConnectedBeltOut": [.20, .40], "holdClear": [.40, .48],
                             "returnBoxLayBelt": [.48, .68], "pressFeed": [.68, .74],
                             "closeCover": [.74, .82], "chargeAndRelease": [.82, .94], "recover": [.94, 1]},
        "magazineSeatedProgress": .68, "coverSeatedProgress": .82, "gripWindow": window,
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": len(elements), "sourceCubes": len(elements),
        "parts": list(PARTS), "partElements": counts, "partCubes": counts, "partitionIndices": indices,
        "coverNames": COVER_NAMES, "chargingHandleNames": BOLT_NAMES,
        "weaponElements": sum(counts.values()), "canonicalFallbackWeaponElements": fallback_elements,
        "elementLimit": 1000, "ordinaryArmElementReserve": ARM_ELEMENT_RESERVE,
        "maxAssembledWithOrdinaryArmsEstimate": weapon_max + ARM_ELEMENT_RESERVE,
        "budgetStatus": "Estimate including inherited canonical fallbacks; master must measure final skin/overlay routes",
        "payloadPolicy": "Five ammo-box solids, seven rounds with case/shoulder/tip/link and six feed connectors share one magazine display and master palm shift. Cover and handle never join that shift.",
        "partitionRationale": "W179 body114 splits into body104 including its independent charging_shaft/charging_knob, and cover10 including rear sights. Magazine39 remains intact. No canonical solids/faces/UVs added or deleted.",
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {part: sha(encode(geo["elements"])) for part, geo in geometries.items()},
        "geometryAndUVPreserved": True, "addedElements": 0, "triangleAdapterElements": 0,
        "hipEndpoints": [0, INTERVALS], "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Complete original graph at both endpoints, negative/absent progress and non-FP; existing native/twohand ADS/inspect selectors precede reload dispatch. Above1 resolves original endpoint graph.",
        "sourceGroup": SOURCE_GROUP, "sourceAction": RIG_ACTION, "rigAction": RIG_ACTION,
        "rigActionName": action["action"], "partHint": "magazine", "sourceFullChain": True,
        "sourceActionWeaponExclusive": False, "sourceFallbackFamily": True,
        "sourceCameraRecovered": False, "sourceMeshRecovered": False, "handIK": False,
        "sourceProvenance": copy.deepcopy(provenance),
        "motionAuthorship": "Exact W179 knots, holds, pivot, hinge and cover/handle algebra; scalar interpolation alone changes. Original FK, ordinary-length fingerless player-skin arms and source weapon parent are master-owned.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "assets": len(output), "packFiles": len(output), "generatedFiles": len(output)+1,
        "staticParts": len(PARTS), "parentDisplayChildren": SAMPLES*len(PARTS)*len(GRIPS),
        "limitations": [
            "Worker read master fresh original Blender evaluation/full-chain61 JSON and viewed actual bone-only sheet; did not open Blender.",
            "Fallback machine-gun family action005 selected; alternate032 also evaluated, neither is an exact weapon-specific recovered assignment.",
            "Authored .60..68 box/belt release requires FIRST contact review; no recovered attachment or finger IK.",
            "61 source/part poses do not prove continuous60fps interpolation.",
            "Final composed ordinary-arm budget, FIRST feedback/correction and SECOND Vision are master-owned and pending."],
        "inputSha256": {str(path): sha(data) for path, data in raw.items()},
        "outputSha256": {str(path.relative_to(root)): sha(data) for path, data in output.items()}})
    if set(output) != {root/path for path in allowed} or len(output) != 371:
        raise ValueError("Expected exactly370 pack outputs and one manifest")
    return output

