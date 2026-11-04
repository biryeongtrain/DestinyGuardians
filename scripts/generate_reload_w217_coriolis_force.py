#!/usr/bin/env python3
"""W217 Coriolis Force: preserved W189 motion with 61 weighted-PCHIP poses.

Pure stdlib; import and generate(root=ROOT) never write. Master binds the fresh
original full-chain rig, materializes bytes, measures routes and owns FIRST/SECOND.
Weapon geometry, cell/socket boundary, authored cell path and mesh contacts remain authored.
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
ART = Path("art/weapons/w217/coriolis_force")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w217_coriolis_force.py")
AUTHORED_SOURCE = Path("scripts/generate_reload_w189_coriolis_force.py")
AUTHORED_MANIFEST = Path("art/weapons/w189/coriolis_force/manifest.json")
AUTHORED_REVIEW = Path("art/weapons/w189/coriolis_force/SOURCE.md")
SOURCE = A / "models/weapon_surface_w123/coriolis_force.json"
NATIVE = A / "models/weapon/fusion_rifle/coriolis_force.json"
TWOHAND = A / "models/weapon/fusion_rifle/coriolis_force_twohand.json"
ITEM = A / "items/weapon/coriolis_force.json"
TEXTURE = A / "textures/item/weapon/w123/coriolis_force.png"
CONTACTS = Path("art/weapons/w201/contacts.json")
RIG = Path("art/weapons/w205/rigs/fusion_rifle_9ab6be45.json")
SOURCE_REVIEW = Path("docs/qa/2026-10-28/w217/source/source-review.json")
FRAMING = Path("art/weapons/w205/first-person-framing.json")
FRAMING_LOADER = Path("scripts/first_person_framing_w205.py")
SURFACE_MAP = Path("src/main/resources/weapon_surface_w123/manifest.json")
KEY = "weapon_reload_w217_coriolis_force/coriolis_force"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine")
GRIPS = ("native", "twohand")
INTERVALS = 60
SAMPLES = 61
RIG_ACTION = "80A8A43C"
RIG_ACTION_NAME = "Armature|fp_80A8A43C_reload_full|Base"
ARM_ELEMENT_RESERVE = 4 * 112
MOVING = (60, 61)
SOURCE_SHA256 = "886a4e969b810a7963f88306446b0fef62355ea3213fcf2feb011a59a6f4c848"
RIG_SHA256 = "ed8727287afffb9ff4ca1f5d87bae9a83e8b92c269bd05a704b41d089f8c5fd5"
SOURCE_REVIEW_SHA256 = "d8edb0d97be1b4cc1446363216ac271fb6bbb1a91f3b52f1fa0b3dc48388fd6a"
EXPORTER_SHA256 = "69694b95b969d2027d7e1b2afc532b2c0a3480c8b86662fc7d61165ed2924769"
AUTHORED_SHA256 = "5284ddc18a02d642318773ad1a76d50cb0cbd34a08be475e7fef6822bcb14f39"
EXPECTED_FRAMING = {
    "translation": [-.65, .6, 0], "rotation": [-1, 2, 0], "scale": .98,
    "rightWristRoll": 28, "leftRotation": [15, 35, -35],
    "sourceFullChain": True, "keepMeshSupport": True, "hideSupportAtRest": False}
EXPECTED_SOURCE_RIG = {
    "group": "fusion_rifle_9ab6be45", "action": RIG_ACTION,
    "sourceBlendSha256": "3e3ca7e7d78ebdd6c95ff473a40d70303d3dc7ffd80f7135695abee2db79974b",
    "sourceMapSha256": "80fa9d69178874c44b71434e0f24d7ff25f0d76f847cbf56128e2f48fcadcfcc",
    "boneMapSha256": "a439c489fb5ab1de893beb8cfe682958641d1c2682059f849932a25db27d3fd4"}
GRIP = (8.,10.5,7.05)
MAGAZINE_ANCHOR = (8.,10.95,-.52)
MAGAZINE_NAMES = ('cartridge_solid','cartridge_upper')
KEYS = (
 (0,(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)),
 (.07,(15,-2,-5),(-.4,.4,-1.1),(0,0,0),(0,0,0),(-1.2,0,0)),
 (.18,(48,-6,-15),(-2,2,-5),(0,0,0),(0,0,0),(-6,0,0)),
 (.25,(47,-7,-16),(-2,2,-5),(0,-.8,0),(-2,0,0),(-6,0,0)),
 (.36,(45,-8,-17),(-2,2,-5),(-1.4,-5.9,.45),(-10,9,-8),(-6,0,0)),
 (.47,(43,-7,-16),(-2,2,-5),(-2.7,-6.6,.7),(-16,18,-12),(-6,0,0)),
 (.56,(44,-6,-15),(-2,2,-5),(-2.1,-5.5,.6),(-12,14,-9),(-6,0,0)),
 (.65,(49,-5,-14),(-2,2,-5),(-.65,-2.8,.2),(-5,5,-3),(-6,0,0)),
 (.74,(55,-4,-13),(-2,2,-5),(0,0,0),(0,0,0),(-6,0,0)),
 (.80,(45,-3,-11),(-1.8,1.8,-4.6),(0,0,0),(0,0,0),(-5.5,0,0)),
 (.90,(17,-1,-5),(-.7,.7,-1.8),(0,0,0),(0,0,0),(-2,0,0)),
 (.97,(2,0,-.5),(-.1,.1,-.2),(0,0,0),(0,0,0),(-.2,0,0)),
 (1,(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)))
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/coriolis_force.json': '886a4e969b810a7963f88306446b0fef62355ea3213fcf2feb011a59a6f4c848', 'src/main/resources/assets/destiny/items/weapon/coriolis_force.json': 'bb6752800536cb6ce9dd374eeb274c9880837773600d989c1c7f3330085ffbeb', 'src/main/resources/assets/destiny/textures/item/weapon/w123/coriolis_force.png': '0af64ab784c105af310da00feae21a73d57c76de8bf57e8d2d5e30573e700a8d', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/sounds/w63/reload/weapon_fusion_rifle_reload_45.ogg': '2f57dc824720837b3171fce240df54967365b11b404e62e9258b71deb5440184', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force.json': '70c6f30447cbae2a42dd7c6a3553e352aa6c6d7b61bd900180e8e8e37eaa2eac', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force_twohand.json': 'e006c486d92ec92d6508ac2f481ca133df1c4a1623dbc685cdd6ddece1ab2338', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force_ads.json': '487cc7d90baefe72288034c5d65b1e332b40bf565ddf001889741fe45e19acc9', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force_ads_twohand.json': '451ca2219efc95737966b764a807c4b8fbe13a41e3d1ade1808974f278c787e6', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force_inspect.json': '2d0d4c29857c840582d13bb32ad5d092980b3145f90aa7d56bf648d99be04285', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force_inspect_twohand.json': 'c5da1cefa49b1656e5693135cdbf09ea16c8103c63c05d11e83884eea1072800'}

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
    for channel in range(1, len(KEYS[0])):
        vector = []
        for axis in range(3):
            values = [key[channel][axis] for key in KEYS]
            slopes = tangents(times, values)
            vector.append(values[index] if values[index] == values[index+1] else
                          h00*values[index] + h10*h*slopes[index]
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

def is_payload(e):return e['name'] in MAGAZINE_NAMES

def partition(source):
    return {part:{**{k:copy.deepcopy(v) for k,v in source.items() if k!='elements'},
                  'elements':[copy.deepcopy(e) for e in source['elements'] if is_payload(e)==(part=='magazine')]}
            for part in PARTS}

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset,cell_angles,correction=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8));anchor=sub(MAGAZINE_ANCHOR,(8,8,8))
    local=sub(pivot,vec(motion,pivot));part_motion=motion
    if part=='magazine':
        cell=xyz(cell_angles)
        local=add(local,vec(motion,add(offset,sub(anchor,vec(cell,anchor)))))
        part_motion=mul(motion,cell)
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);scale=idle['scale']
        if twohand[context]['scale']!=scale or len(set(scale))!=1:raise ValueError('Expected equal uniform canonical scales')
        rotation=mul(base,part_motion)
        position=add(add(idle['translation'],shift),vec(base,[scale[0]*v for v in local]))
        if grip=='twohand':
            carrier=mul(xyz(twohand[context]['rotation']),transpose(base))
            position=add(add(vec(carrier,position),sub(twohand[context]['translation'],vec(carrier,idle['translation']))),correction)
            rotation=mul(carrier,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def expected_output_paths():
    paths = {A / f"models/{KEY}_{part}.json" for part in PARTS}
    paths.update(A / f"models/{KEY}_{i:02}_{part}_{grip}.json"
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f"items/{KEY}.json", MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Read current root inputs, return absolute Path -> bytes; no writes."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, PROFILE,
        GENERATOR, AUTHORED_SOURCE, AUTHORED_MANIFEST, AUTHORED_REVIEW, CONTACTS,
        RIG, SOURCE_REVIEW, FRAMING, FRAMING_LOADER, SURFACE_MAP,
        *(Path(p) for p in PINS)]))
    raw = {path: (root / path).read_bytes() for path in inputs}
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError("Canonical geometry/UV/gameplay/audio input drift: " + path)
    if sha(raw[AUTHORED_SOURCE]) != AUTHORED_SHA256:
        raise ValueError("W189 authored source changed; re-audit before generating")
    authored = {}
    for node in ast.parse(raw[AUTHORED_SOURCE]).body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in {"KEYS", "GRIP", "MAGAZINE_ANCHOR", "MAGAZINE_NAMES"}):
            authored[node.targets[0].id] = ast.literal_eval(node.value)
    if authored != {"KEYS": KEYS, "GRIP": GRIP, "MAGAZINE_ANCHOR": MAGAZINE_ANCHOR,
                    "MAGAZINE_NAMES": MAGAZINE_NAMES}:
        raise ValueError("W189 authored knots/anchors changed")
    if (sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != SOURCE_REVIEW_SHA256):
        raise ValueError("Master must install the reviewed fresh W217 normalized source export/report")
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    report = json.loads(raw[SOURCE_REVIEW])
    old = json.loads(raw[AUTHORED_MANIFEST])
    contacts = json.loads(raw[CONTACTS])["weapons"]["coriolis_force"]
    elements = source["elements"]
    if (len(elements) != 104 or
            tuple(i for i,e in enumerate(elements) if is_payload(e)) != MOVING or
            tuple(elements[i]["name"] for i in MOVING) != MAGAZINE_NAMES or
            old["sourceGeometryFileSha256"] != SOURCE_SHA256 or
            old["keyframes"] != json.loads(encode(KEYS)) or
            old["partitionIndices"]["magazine"] != list(MOVING)):
        raise ValueError("Coriolis Force W189 geometry/UV/partition drift")
    rule = next(r for r in json.loads(raw[SURFACE_MAP])["targets"]
                if r["path"] == "assets/destiny/models/weapon/fusion_rifle/coriolis_force.json")
    if (rule["replacement"] != "assets/destiny/models/weapon_surface_w123/coriolis_force.json"
            or rule["replacementSha256"] != SOURCE_SHA256):
        raise ValueError("Selected Coriolis Force surface mapping changed")
    if (profile.get("schemaVersion") != 1 or profile.get("weapon") != "coriolis_force"
            or profile.get("sourceAction") != RIG_ACTION
            or profile.get("sourceRig") != EXPECTED_SOURCE_RIG
            or profile.get("framing") != EXPECTED_FRAMING):
        raise ValueError("W217 profile/source/full-chain/effective framing drift")
    overrides = profile.get("contacts", {})
    reload = {**contacts["reload"], **overrides.get("reload", {})}
    if (set(overrides) != {"reload"} or
            set(overrides["reload"]) != {"rigAction", "partHint", "policy", "gripWindow"}
            or reload.get("rigAction") != RIG_ACTION
            or reload.get("partHint") != "magazine" or reload.get("policy") != "magazine"
            or reload.get("gripWindow") != [.05, .18, .65, .74]
            or contacts["family"] != "fusion_rifle"
            or contacts["canonicalModel"] != "destiny:weapon_surface_w123/coriolis_force"
            or contacts["right"] != {"position": [8.,9.15,7.52], "rotation": [-18.,0.,0.]}
            or contacts["left"] != {"position": [7.8,10.78,-6.], "rotation": [0.,90.,-85.]}
            or reload.get("contact") != [7.4,8.2,.02]
            or reload.get("rotation") != [0.,0.,0.]):
        raise ValueError("Rest contacts or authored .74 cell release changed")
    if (rig.get("group") != "fusion_rifle_9ab6be45" or rig.get("fallback") is not False
            or "coriolis_force" not in rig["weapons"] or rig.get("cameraExported") is not False
            or rig.get("space") != "armature_object"
            or rig.get("w217Source61", {}).get("exporterSha256") != EXPORTER_SHA256
            or rig["w217Source61"].get("reloadSamples") != SAMPLES
            or rig["w217Source61"].get("cameraExported") is not False):
        raise ValueError("Expected fresh master W217 original shoulder-chain source")
    action = rig["actions"][RIG_ACTION]
    if (action["action"] != RIG_ACTION_NAME or len(action["frames"]) != SAMPLES
            or (action["start"], action["end"]) != (1,106)):
        raise ValueError("Expected actual Blender action name and61 samples over1..106")
    joints = {"weapon", "leftShoulder", "leftElbow", "leftWrist",
              "rightShoulder", "rightElbow", "rightWrist"}
    for i,frame in enumerate(action["frames"]):
        if (not joints <= frame["joints"].keys()
                or abs(frame["progress"]-i/INTERVALS) > 1e-12
                or abs(frame["frame"]-(1+105*i/INTERVALS)) > 1e-10):
            raise ValueError("Expected uniformly evaluated original full shoulder chains")
    reviewed = report["groups"][rig["group"]]
    if (report.get("allInputsUnchanged") is not True
            or report.get("exporterSha256") != EXPORTER_SHA256
            or reviewed["objects"] != [{"name": "Armature", "type": "ARMATURE"}]
            or reviewed["actions"][RIG_ACTION]["action"] != RIG_ACTION_NAME
            or reviewed["actions"][RIG_ACTION]["sourceFrameRange"] != [1,106]
            or reviewed["actions"][RIG_ACTION]["samples"] != SAMPLES
            or reviewed["actions"][RIG_ACTION]["maxExistingCacheJointAbsError"] != 0):
        raise ValueError("Fresh original Blender report changed")
    for name in ("sourceBlendSha256", "sourceMapSha256", "boneMapSha256"):
        if rig.get(name) != EXPECTED_SOURCE_RIG[name]:
            raise ValueError("Original rig input changed: " + name)
    geometries = partition(source)
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError("Output outside W217 Coriolis Force namespace")
        output[root / path] = encode(value)

    for part in PARTS:
        emit(A / f"models/{KEY}_{part}.json", geometries[part])
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

        model = copy.deepcopy(item["model"]) if frame in (0,INTERVALS) else {
            "type": "minecraft:condition", "property": "minecraft:custom_model_data", "index": 0,
            "on_true": composite("twohand"), "on_false": composite("native")}
        entries.append({"threshold": float32(progress), "model": model})
    wrapper = copy.deepcopy(item)
    wrapper["model"] = {
        "type": "minecraft:select", "property": "minecraft:display_context",
        "cases": [{"when": list(FP), "model": {
            "type": "minecraft:select", "property": "minecraft:custom_model_data", "index": 0,
            "cases": [{"when": ["ads", "inspect"], "model": copy.deepcopy(item["model"])}],
            "fallback": {"type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data", "index": 1,
                         "entries": entries, "fallback": copy.deepcopy(item["model"])}}}],
        "fallback": copy.deepcopy(item["model"])}
    emit(A / f"items/{KEY}.json", wrapper)
    counts = {part:len(geo["elements"]) for part,geo in geometries.items()}
    canonical_count = len(json.loads(raw[NATIVE])["elements"])
    weapon_count = sum(counts.values())
    if max(weapon_count,canonical_count) + ARM_ELEMENT_RESERVE > 1000:
        raise ValueError("Weapon plus ordinary full-chain arm reserve exceeds1000 elements")
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W217", "weapon": "coriolis_force",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0, "firstPersonContexts": list(FP),
        "thresholdEncoding": "float32(i/60), matching master runtime grid60",
        "curve": "C1 weighted harmonic PCHIP; zero endpoints, holds and extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "magazineAnchor": MAGAZINE_ANCHOR,
        "authoredTimingSource": str(AUTHORED_SOURCE),
        "magazineNeutralSeatedProgress": .74, "reloadGripWindow": reload["gripWindow"],
        "normalizedPhases": old["normalizedPhases"],
        "reference": old["reference"],
        "referencePolicy": "Retain W189 same-weapon Ironworker Gaming 67wv69MomYQ n772..856 provenance; worker read SOURCE.md/manifest and viewed retained storyboard, did not decode source video.",
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": len(elements), "partElements": counts, "weaponElements": weapon_count,
        "bodyElements": counts["body"], "movingElements": counts["magazine"],
        "canonicalWeaponElements": canonical_count, "endpointAssembledElements": canonical_count,
        "elementLimit": 1000, "ordinaryArmElementReserve": ARM_ELEMENT_RESERVE,
        "candidateReloadWithArmsEstimate": weapon_count+ARM_ELEMENT_RESERVE,
        "candidateKnownCanonicalWithArmsEstimate": canonical_count+ARM_ELEMENT_RESERVE,
        "integratedAllRouteMaximumMeasured": False,
        "budgetBasis": "104 reload weapon+448 estimated ordinary arm elements=552; native241+448=689. Master measures all composed routes including ADS/inspect under1000.",
        "movingIndices": list(MOVING), "movingNames": list(MAGAZINE_NAMES),
        "partitionIndices": old["partitionIndices"], "semanticGroups": old["semanticGroups"],
        "partitionRationale": "102 body solids fixed; only cartridge_solid60 and cartridge_upper61 move rigidly about the original upper cell anchor. Red surround/floor/toe, rear grip, receiver, triggerguard, stock and U clamp stay fixed.",
        "addedElements": 0, "newElementsRelativeToW189": 0, "triangleAdapterElements": 0,
        "sourceLimitation": old["sourceLimitation"],
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {part:sha(encode(geo["elements"])) for part,geo in geometries.items()},
        "canonicalElementsAndUVPreserved": True, "geometryAndUVPreserved": True,
        "hipEndpoints": [0,INTERVALS], "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Canonical item graph at endpoints, negative progress, overshoot and nonFP; ADS/inspect precede reload; native/twohand flags preserved.",
        "sourceGroup": rig["group"], "sourceAction": RIG_ACTION, "rigAction": RIG_ACTION,
        "rigActionName": action["action"], "sourceActionSourceRange": [action["start"],action["end"]],
        "sourceRigSamples": len(action["frames"]), "sourceFullChain": True,
        "partHint": "magazine", "policy": "magazine", "w217Source61": rig["w217Source61"],
        "sourceCameraRecovered": False, "sourceEvidence": profile["evidence"],
        "motionAuthorship": "All13 W189 knots/holds and all five motion vector channels, rigid algebra, central-cell local rotation and twohand correction, anchors, geometry/UV and partition preserved. Only interpolation becomes W215 weighted harmonic PCHIP. Master binds original weapon-relative shoulder/elbow/wrist FK, ordinary limb lengths/axes and fingerless skin arms.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "timingPolicy": "Retain6 rounds,45tick reload,667ms charge/14charge ticks,7bolt shared-ammo volley, ammo lifecycle and reload audio; original30fps frames1..106 do not retime gameplay.",
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "packFiles": len(output), "totalReturnedFiles": len(output)+1,
        "staticParts": len(PARTS), "parentDisplayChildren": SAMPLES*len(PARTS)*len(GRIPS),
        "inputSha256": {str(path):sha(data) for path,data in raw.items()},
        "outputSha256": {str(path.relative_to(root)):sha(data) for path,data in output.items()},
        "limitations": [
            "Master evaluated original Blender; worker read fresh report/matrices and viewed the selected80A8A43C full-chain bone-only sheet and retained W189 same-weapon storyboard.",
            "Original ARMATURE only: no weapon mesh/camera/finger IK; authored cell/socket boundary, contacts and lower cell/grip clearance need FIRST.",
            "61 static poses do not prove native continuous60fps interpolation.",
            "Attachment releases through.65..74; cell neutral translation/rotation holds.74..1 so later wrist departure cannot drag seated payload.",
            "Current effective framing/rest contacts retained; no new arm/camera compensations, length changes or source attenuation.",
            "Master owns integration, all-route measured budget, FIRST feedback, worker correction/nochange and SECOND. Native acceptance pending."]})
    if set(output) != {root/path for path in allowed}:
        raise ValueError("Incomplete W217 Coriolis Force output mapping")
    return output
