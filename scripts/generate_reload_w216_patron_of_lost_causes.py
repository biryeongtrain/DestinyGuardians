#!/usr/bin/env python3
"""W216 Patron: unchanged W183 authored parts/knots, 61-pose C1 PCHIP bank.

Pure stdlib; importing and generate(root=ROOT) never write. Master owns fresh
original-chain binding, arms, materialization, integration and FIRST/SECOND QA.
"""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
A = Path("src/main/resources/assets/destiny")
ART = Path("art/weapons/w216/patron_of_lost_causes")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w216_patron_of_lost_causes.py")
AUTHORED_SOURCE = Path("scripts/generate_reload_w183_patron_of_lost_causes.py")
AUTHORED_MANIFEST = Path("art/weapons/w183/patron_of_lost_causes/manifest.json")
AUTHORED_NOTES = Path("art/weapons/w183/patron_of_lost_causes/SOURCE.md")
SOURCE = A / "models/weapon_surface_w123/patron_of_lost_causes.json"
NATIVE = A / "models/weapon/scout_rifle/patron_of_lost_causes.json"
TWOHAND = A / "models/weapon/scout_rifle/patron_of_lost_causes_twohand.json"
ITEM = A / "items/weapon/patron_of_lost_causes.json"
TEXTURE = A / "textures/item/weapon/w123/patron_of_lost_causes.png"
CONTACTS = Path("art/weapons/w201/contacts.json")
FRAMING = Path("art/weapons/w205/first-person-framing.json")
RIG = Path("art/weapons/w205/rigs/scout_rifle_98cec92a.json")
KEY = "weapon_reload_w216_patron_of_lost_causes/patron_of_lost_causes"
PARTS = ("body", "magazine")
GRIPS = ("native", "twohand")
INTERVALS = 60
SAMPLES = INTERVALS + 1
RIG_ACTION = "80A8A345"
ACTION_NAME = "Armature|fp_80A8A345_reload_full|Base"
ARM_ELEMENT_RESERVE = 4 * 112
EXPECTED_FRAMING = {"translation": [-.65, .6, 0], "rotation": [-1, 2, 0],
                    "scale": .98, "rightWristRoll": 28, "leftRotation": [15, 35, -35],
                    "sourceFullChain": True, "keepMeshSupport": True,
                    "hideSupportAtRest": False}
AUTHORED_SHA256 = 'd1d5341aa9d7de0d3056f48c07881406b5bebba87c089c58e68089653e484a62'
EXPORTER_SHA256 = '54b2f8673aaf75b97a388077ecad683eef2441a73f313194e52ce9b6cd514a38'
SOURCE_HASHES = {'sourceBlendSha256': 'be7c6bb31dc5734de8a82d93fb92c619e581fa2c7bd04951e59e884aebf49941', 'sourceMapSha256': 'd97ed313c4bcec5414900a745b6657e578623348908b0ed91205f5e34f5d3315', 'boneMapSha256': '34cc654306ee835cf908f72fed910a3955868195289e1109178a45c237fcee40'}
FP = ('firstperson_righthand', 'firstperson_lefthand')
MAGAZINE_NAMES = ('magazine_body', 'magazine_floor')
GRIP = (8.0, 7.65, 8.8)
MAG_ANCHOR = (8.0, 8.25, 12.14)
KEYS = ((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.08, (3, -1, -2), (0.02, -0.03, 0), (0, 0, 0)), (0.2, (72, -14, -10), (0.35, 0.05, 0.15), (0, -4.8, 0.675)), (0.3, (82, -17, -13), (0.55, 0.1, 0.25), (-0.25, -5.8, 0.815)), (0.42, (78, -16, -11), (0.55, 0.1, 0.25), (-0.25, -5.8, 0.815)), (0.5, (70, -13, -8), (0.4, 0.05, 0.2), (-0.12, -2.9, 0.4075)), (0.6, (73, -12, -7), (0.35, 0.12, 0.15), (0, 0, 0)), (0.7, (25, -4, -3), (0.15, -0.05, 0.05), (0, 0, 0)), (0.8, (-4, 1, 1), (0.02, -0.15, 0), (0, 0, 0)), (0.9, (2, 0, 0), (0, -0.03, 0), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/patron_of_lost_causes.json': 'e0afa39e288ca3fee279ea49237ae5233ea7747775b601f67fec2b94b3d5609e', 'src/main/resources/assets/destiny/textures/item/weapon/w123/patron_of_lost_causes.png': 'c2fde451365efd21ab1c3940695eff5a254fae8ea3188c31b8af69e1d42ac0d8', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/items/weapon/patron_of_lost_causes.json': 'cfcc2f992c8119ac461d9f1baf943a5e0d38edf23e4c6b1f0f6a58e832cdd900', 'src/main/resources/assets/destiny/items/weapon_aim_w70/patron_of_lost_causes.json': '7ddfdd4b14a76cd956bc459df795e130a012a8212f079d1c65f8e600ef12841d', 'src/main/resources/assets/destiny/items/weapon_sight_w153/patron_of_lost_causes.json': '581f32398c3bef161f566edb543f3711ae35c9e1979b58dca565dd78556be0da', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes.json': 'd1086431cad2a610031c46f4c6990c3ae9680b605a44990b3cd9adf428bfdae8', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes_twohand.json': 'bfb7d23f17b16b5d483318d57b6b651a1dd3fd273f6de7336e0fa12ac137205c', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes_ads.json': 'dd79a321166e00ba61041285bde6ceb9ea5275777fc59479cb61b2260cdd289b', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes_ads_twohand.json': 'b6c25873acac25023ca96b9906926660473122ff02f3db47e15ac1b3b22cea5f', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes_inspect.json': 'e4acc2572ab9d9bca32651518e07c5cde85d454008921ac76e576c0206e10c0d', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes_inspect_twohand.json': 'c667780295c146b87706f1dae23da46e39d0cda5c621e042bee8336b07dab331'}

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
    """Two canonical rear magazine solids; pistol grip/stock/charging components stay fixed.
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
            vector.append(values[index] if values[index] == values[index+1] else
                          h00*values[index] + h10*h*slopes[index]
                          + h01*values[index+1] + h11*h*slopes[index+1])
        result.append(vector)
    return tuple(result)

def expected_output_paths():
    paths = {A / f"models/{KEY}_{part}.json" for part in PARTS}
    paths.update(A / f"models/{KEY}_{i:02}_{part}_{grip}.json"
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f"items/{KEY}.json", MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Return absolute Path -> bytes only; no directories or files are written."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, PROFILE,
        GENERATOR, AUTHORED_SOURCE, AUTHORED_MANIFEST, AUTHORED_NOTES,
        CONTACTS, FRAMING, RIG, *(Path(p) for p in PINS)]))
    raw = {path: (root / path).read_bytes() for path in inputs}
    if sha(raw[AUTHORED_SOURCE]) != AUTHORED_SHA256:
        raise ValueError("W183 authored source drift; re-audit before porting")
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError("Canonical geometry/UV/gameplay/audio input drift: " + path)
    # Read literals, never import/execute the historical PIL/NumPy generator.
    authored = {}
    for node in ast.parse(raw[AUTHORED_SOURCE]).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("KEYS", "GRIP", "MAG_ANCHOR", "MAGAZINE_NAMES"):
                authored[name] = ast.literal_eval(node.value)
    if authored != {"KEYS": KEYS, "GRIP": GRIP, "MAG_ANCHOR": MAG_ANCHOR,
                    "MAGAZINE_NAMES": MAGAZINE_NAMES}:
        raise ValueError("Patron authored knots/anchors/part identities changed")
    historical = json.loads(raw[AUTHORED_MANIFEST])
    if (historical["weapon"] != "patron_of_lost_causes"
            or historical["keyframes"] != json.loads(encode(KEYS))
            or historical["partitionIndices"]["magazine"] != [82, 83]
            or historical["sourceGeometryFileSha256"] != sha(raw[SOURCE])):
        raise ValueError("W183 manifest no longer matches authored Patron source")
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    contacts = json.loads(raw[CONTACTS])["weapons"]["patron_of_lost_causes"]
    if (profile.get("schemaVersion") != 1 or profile.get("weapon") != "patron_of_lost_causes"
            or profile.get("sourceAction") != RIG_ACTION
            or profile.get("framing") != EXPECTED_FRAMING
            or set(profile.get("contacts", {})) != {"reload"}):
        raise ValueError("W216 Patron framing/full-chain/rest-contact policy drift")
    reload = {**contacts["reload"], **profile["contacts"]["reload"]}
    if (reload.get("rigAction") != RIG_ACTION or reload.get("partHint") != "magazine"
            or reload.get("policy") != "magazine"
            or reload.get("contact") != [7.2, 6.85, 12.14]
            or reload.get("rotation") != [-8.0, 0.0, 0.0]):
        raise ValueError("Patron magazine attachment/rest-contact policy drift")
    window = reload.get("gripWindow")
    if not (isinstance(window, list) and len(window) == 4
            and all(isinstance(v, (int, float)) and math.isfinite(v) for v in window)
            and 0 <= window[0] < window[1] <= window[2] < window[3] <= .60):
        raise ValueError("Patron magazine must release from source palm by authored .60 seat")
    fresh = rig.get("w216Source61", {})
    if (rig.get("group") != "scout_rifle_98cec92a" or rig.get("fallback") is not False
            or "patron_of_lost_causes" not in rig.get("weapons", [])
            or rig.get("space") != "armature_object" or rig.get("cameraExported") is not False
            or fresh.get("reloadSamples") != SAMPLES
            or fresh.get("exporterSha256") != EXPORTER_SHA256
            or fresh.get("cameraExported") is not False):
        raise ValueError("Master must bind the reviewed fresh W216 original full-chain rig")
    for name, digest in SOURCE_HASHES.items():
        if rig.get(name) != digest or profile["sourceRig"].get(name) != digest:
            raise ValueError("Reviewed original source hash drift: " + name)
    if (profile["sourceRig"].get("group") != rig["group"]
            or profile["sourceRig"].get("action") != RIG_ACTION):
        raise ValueError("Profile source action/group mismatch")
    action = rig["actions"][RIG_ACTION]
    if (action.get("action") != ACTION_NAME or (action["start"], action["end"]) != (1, 105)
            or len(action["frames"]) != SAMPLES):
        raise ValueError("Expected actual original action name, frames1..105 and61 poses")
    joints = {"weapon", "leftShoulder", "leftElbow", "leftWrist",
              "rightShoulder", "rightElbow", "rightWrist"}
    for i, frame in enumerate(action["frames"]):
        if (abs(frame["progress"] - i / INTERVALS) > 1e-12
                or abs(frame["frame"] - (1 + 104 * i / INTERVALS)) > 1e-9
                or not joints <= frame["joints"].keys()):
            raise ValueError("Expected uniform original weapon/shoulder/elbow/wrist samples")
        for name in joints:
            matrix = frame["joints"][name]
            if (len(matrix) != 4 or any(len(row) != 4 for row in matrix)
                    or any(not math.isfinite(v) for row in matrix for v in row)):
                raise ValueError("Invalid source full-chain matrix")
    elements = source["elements"]
    moving = [i for i, e in enumerate(elements) if e["name"] in MAGAZINE_NAMES]
    if (len(elements) != 98 or moving != [82, 83]
            or tuple(elements[i]["name"] for i in moving) != MAGAZINE_NAMES):
        raise ValueError("Patron whole rear-magazine partition drift")
    parts = partition(source)
    if {p: len(m["elements"]) for p, m in parts.items()} != {"body": 96, "magazine": 2}:
        raise ValueError("Expected unchanged96 body +2 whole-magazine solids")
    allowed = expected_output_paths()
    output = {}

    def emit(path, value):
        if path not in allowed:
            raise ValueError("Output outside W216 Patron namespace")
        output[root / path] = encode(value)

    for part, model in parts.items():
        emit(A / f"models/{KEY}_{part}.json", model)
    entries = []
    for frame in range(SAMPLES):
        progress = frame / INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A / f"models/{KEY}_{frame:02}_{part}_{grip}.json", {
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
    # Keep every canonical ADS/inspect case and grip flag, inserting reload only
    # into the original hip fallback. Endpoints and non-FP use the canonical graph.
    mode_guard = copy.deepcopy(item["model"])
    mode_guard["fallback"] = {
        "type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data", "index": 1,
        "entries": entries, "fallback": copy.deepcopy(item["model"])}
    wrapper = copy.deepcopy(item)
    wrapper["model"] = {
        "type": "minecraft:select", "property": "minecraft:display_context",
        "cases": [{"when": list(FP), "model": mode_guard}],
        "fallback": copy.deepcopy(item["model"])}
    emit(A / f"items/{KEY}.json", wrapper)
    counts = {part: len(model["elements"]) for part, model in parts.items()}
    canonical_count = len(json.loads(raw[NATIVE])["elements"])
    if max(sum(counts.values()), canonical_count) + ARM_ELEMENT_RESERVE > 1000:
        raise ValueError("Patron plus ordinary four-segment arm reserve exceeds1000")
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W216", "weapon": "patron_of_lost_causes",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0, "firstPersonContexts": list(FP),
        "thresholdEncoding": "float32(i/60), matching runtime grid60",
        "curve": "C1 shape-preserving Hermite; W215 weighted harmonic PCHIP; zero endpoints/holds/extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "magazineAnchor": MAG_ANCHOR,
        "authoredTimingSource": str(AUTHORED_SOURCE),
        "normalizedPhases": historical["normalizedPhases"],
        "magazineSeatedProgress": .60, "reloadGripWindow": window,
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceRevision": historical["sourceRevision"], "sourceElements": len(elements),
        "partElements": counts, "bodyElements": counts["body"], "movingElements": counts["magazine"],
        "weaponElements": sum(counts.values()), "canonicalWeaponElements": canonical_count,
        "maxAssembledWeaponElements": max(sum(counts.values()), canonical_count),
        "ordinaryArmElementReserve": ARM_ELEMENT_RESERVE, "elementLimit": 1000,
        "candidateReloadWithArmsEstimate": sum(counts.values()) + ARM_ELEMENT_RESERVE,
        "candidateKnownCanonicalWithArmsEstimate": canonical_count + ARM_ELEMENT_RESERVE,
        "integratedAllRouteMaximumMeasured": False,
        "budgetBasis": "98 reload solids +448 estimated arm surfaces=546; canonical241+448=689. Master measures all routes including ADS/inspect and arms under1000.",
        "partitionIndices": historical["partitionIndices"], "magazineNames": MAGAZINE_NAMES,
        "partitionRationale": historical["partitionRationale"],
        "addedElements": 0, "triangleAdapterElements": 0,
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {p: sha(encode(m["elements"])) for p, m in parts.items()},
        "geometryAndUVPreserved": True, "hipEndpoints": [0, INTERVALS],
        "endpointDisplayExact": True, "fallbackModelExact": True,
        "adsInspectPrecedencePreserved": True, "nonFirstPersonGraphExact": True,
        "fallback": "Exact canonical graph for inactive negative progress, endpoints, overshoot, non-FP and ADS/inspect; native/twohand flags retained.",
        "sourceGroup": rig["group"], "sourceAction": RIG_ACTION, "rigAction": RIG_ACTION,
        "rigActionName": action["action"], "sourceActionSourceRange": [action["start"], action["end"]],
        "sourceFullChain": True, "sourceRigSamples": len(action["frames"]),
        "source61Provenance": fresh, "sourceCameraRecovered": False,
        "partHint": "magazine", "policy": "magazine", "sourceEvidence": profile.get("evidence", []),
        "reference": historical["reference"],
        "motionAuthorship": "W183 Patron knots, holds, steep lift, rear-magazine path and rigid carrier preserved; only interpolation becomes W215 C1 weighted-harmonic PCHIP. Original shared scout-family FK drives master-owned ordinary arms; no weapon-exclusive mesh trajectory or finger IK recovered.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "timingPolicy": "Normalized visuals only; unchanged39tick reload,15round capacity,200RPM, ammo lifecycle and audio.",
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "packFiles": len(output), "totalReturnedFiles": len(output) + 1,
        "staticParts": len(PARTS), "parentDisplayChildren": SAMPLES * len(PARTS) * len(GRIPS),
        "inputSha256": {str(path): sha(data) for path, data in raw.items()},
        "outputSha256": {str(path.relative_to(root)): sha(data) for path, data in output.items()},
        "limitations": [
            "Worker reviewed fresh master Blender5.4 report, source matrices and three chain sheets; no independent Blender evaluation claimed.",
            "ARMATURE only, no weapon mesh/camera/finger IK. Shared scout-family action selection is explicit, not weapon-exclusive provenance.",
            "Authored magazine/contact path retained. Attachment releases by.60 seat; FIRST must verify actual fit and later wrist departure.",
            "No source length/axis compensation, camera changes, hidden support or rest-contact edits. Full-chain source direction priority remains master-owned.",
            "61 bank poses do not prove continuous native60fps interpolation.",
            "Master owns materialization, all-route budget, FIRST PNG feedback, integration of worker correction/no-change response, and SECOND. Native acceptance remains pending."]})
    if set(output) != {root / path for path in allowed}:
        raise ValueError("Incomplete W216 Patron output mapping")
    return output
