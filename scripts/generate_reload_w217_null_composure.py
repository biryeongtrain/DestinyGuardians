#!/usr/bin/env python3
"""W217 Null Composure: exact W179 geometry/motion with61 weighted-PCHIP poses.

Pure stdlib: import and generate(root=ROOT) never write. Master binds the original
full shoulder chain, materializes output and owns FIRST feedback and SECOND.
The shared fusion ARMATURE is not weapon-exclusive mesh/camera/finger IK evidence.
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
ART = Path("art/weapons/w217/null_composure")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w217_null_composure.py")
AUTHORED_SOURCE = Path("scripts/generate_reload_w179_null_composure.py")
AUTHORED_MANIFEST = Path("art/weapons/w179/null_composure/manifest.json")
AUTHORED_REVIEW = Path("art/weapons/w179/null_composure/SOURCE.md")
SOURCE = A / "models/weapon_surface_w123/null_composure.json"
NATIVE = A / "models/weapon/fusion_rifle/null_composure.json"
TWOHAND = A / "models/weapon/fusion_rifle/null_composure_twohand.json"
ITEM = A / "items/weapon/null_composure.json"
TEXTURE = A / "textures/item/weapon/w123/null_composure.png"
CONTACTS = Path("art/weapons/w201/contacts.json")
RIG = Path("art/weapons/w205/rigs/fusion_rifle_04669cdb.json")
SOURCE_REVIEW = Path("docs/qa/2026-10-28/w217/source/source-review.json")
FRAMING = Path("art/weapons/w205/first-person-framing.json")
FRAMING_LOADER = Path("scripts/first_person_framing_w205.py")
SURFACE_MAP = Path("src/main/resources/weapon_surface_w123/manifest.json")
KEY = "weapon_reload_w217_null_composure/null_composure"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine")
GRIPS = ("native", "twohand")
INTERVALS = 60
SAMPLES = 61
RIG_ACTION = "80A8ADD3"
RIG_ACTION_NAME = "Armature|fp_80A8ADD3_reload_full|Base"
ARM_ELEMENT_RESERVE = 448
MOVING = (28, 29, 32)
SOURCE_SHA256 = "37a221b93407ff720959b59c7192135cff81f6658743a92892204916e00d0c5f"
RIG_SHA256 = "747749cea16ee1bec34df57fbb7fb8b6c7bb32e6dd1dfef6188991a0d2e4d76a"
SOURCE_REVIEW_SHA256 = "d8edb0d97be1b4cc1446363216ac271fb6bbb1a91f3b52f1fa0b3dc48388fd6a"
EXPORTER_SHA256 = "69694b95b969d2027d7e1b2afc532b2c0a3480c8b86662fc7d61165ed2924769"
AUTHORED_SHA256 = "221a1f1a260b04b57fa42f2752b380f5ed8ff82bc11cd54dac2468f1bc01351b"
EXPECTED_FRAMING = {
    "translation": [-.65,.6,0], "rotation": [-1,2,0], "scale": .98,
    "rightWristRoll": 28, "leftRotation": [15,35,-35],
    "sourceFullChain": True, "keepMeshSupport": True, "hideSupportAtRest": False}
EXPECTED_SOURCE_RIG = {
    "group": "fusion_rifle_04669cdb", "action": RIG_ACTION,
    "sourceBlendSha256": "cdf955feedf818492dd395a2866beb19ed11bb35944544c05c3cd4eb00eeee36",
    "sourceMapSha256": "27b7520526de9abf593e208b6f0b52f70c83e2a4a6ddaada7bcd3dc40eac9ad2",
    "boneMapSha256": "a439c489fb5ab1de893beb8cfe682958641d1c2682059f849932a25db27d3fd4"}
GRIP = (8.,8.4,5.4)
MAG_ANCHOR = (8.,7.48,.27)
CELL_NAMES = ('Battery_keel_solid','Battery_blue_spine','Battery_heel')
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0)),
 (.11,(78,5,14),(.35,-.45,.35),(0,0,0)),
 (.22,(84,9,18),(.50,-.35,.45),(0,-.6,-.35)),
 (.34,(80,11,21),(.55,-.35,.50),(-.3,-3.2,-.4)),
 (.45,(81,11,20),(.55,-.35,.50),(-.3,-3.2,-.4)),
 (.56,(82,10,17),(.50,-.30,.45),(-.1,-1.25,-.35)),
 (.64,(80,7,14),(.40,-.30,.35),(0,0,0)),
 (.73,(68,3,9),(.30,-.25,.25),(0,0,0)),
 (.80,(71,3,6),(.25,-.20,.20),(0,0,0)),
 (.90,(34,1,2),(.10,-.10,.10),(0,0,0)),
 (1.,(0,0,0),(0,0,0),(0,0,0)),
)
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/null_composure.json': '37a221b93407ff720959b59c7192135cff81f6658743a92892204916e00d0c5f', 'src/main/resources/assets/destiny/textures/item/weapon/w123/null_composure.png': '0a37c3c55da27f611bc6129d1995e892656f3e66bc32594f7c1af9444a5db823', 'src/main/resources/assets/destiny/items/weapon/null_composure.json': 'dc07bbf4c78835f030430fd3e3335d26e3b154c409b9b5c38803accbe2e11e62', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/weapon_surface_w123/manifest.json': '4972bd808e5150d09e8f55e2c663b45f88ad8e660300310c5ecc04f4f672db6b', 'src/main/resources/assets/destiny/items/weapon_sight_w153/null_composure.json': 'b191c508ac6cec7c63d50736384dc109faca0f6615fde22227074412e1715922', 'src/main/resources/assets/destiny/items/weapon_aim_w70/null_composure.json': 'e1cb1cae46bef879e55f2010eef551784bacb98f9b673e9d8db7fe3f3e4be0b3', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure.json': 'e5e5ead55de6a921d9bb452c9ea460c573f36150c625a526df7db10d04c5bc75', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure_ads.json': '336241a84c9037af386724ce0c10be1e4be25bf0a7e5a8ccff610ceb7de29dc7', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure_ads_twohand.json': 'a1e7aa04b9d88e516d1153b7f90bfb85d5bad61e27a7419b922d332efec24ed2', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure_inspect.json': '6618d1a786c6265e05e5c9e5052d72da6eba90a40e444ca4bcf06dc5bc1a3abf', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure_inspect_twohand.json': '50412d28adb055cb68865b37b4229485348842186dad000197e5fec1542e5b65', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure_twohand.json': '7479921650278a6901ed39bf72a41c16de75b8fdb3021964dac966b2539c9a96'}

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

def partition(source):
    """Three connected canonical battery solids; diagonal web and frame stay fixed.
    Each original element appears exactly once, with every field/UV value retained.
    """
    parts={}
    for part in ('body','magazine'):
        model={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        model['elements']=[copy.deepcopy(e) for e in source['elements'] if (e['name'] in CELL_NAMES)==(part=='magazine')]
        parts[part]=model
    return parts

def pose_display(original,twohand,p,part,grip):
    if part not in ('body','magazine') or grip not in ('native','twohand'):raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8));anchor=sub(MAG_ANCHOR,(8,8,8))
    # Rotate both intact canonical parts around pistol contact. Cell receives only
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

def expected_output_paths():
    paths = {A / f"models/{KEY}_{part}.json" for part in PARTS}
    paths.update(A / f"models/{KEY}_{i:02}_{part}_{grip}.json"
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {A / f"items/{KEY}.json", MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Read inputs and return an absolute Path->bytes mapping without writing."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, PROFILE,
        GENERATOR, AUTHORED_SOURCE, AUTHORED_MANIFEST, AUTHORED_REVIEW, CONTACTS,
        RIG, SOURCE_REVIEW, FRAMING, FRAMING_LOADER, SURFACE_MAP,
        *(Path(p) for p in PINS)]))
    raw = {path: (root/path).read_bytes() for path in inputs}
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError("Canonical geometry/UV/gameplay/audio drift: "+path)
    if sha(raw[AUTHORED_SOURCE]) != AUTHORED_SHA256:
        raise ValueError("W179 authored source changed; re-audit first")
    authored = {}
    for node in ast.parse(raw[AUTHORED_SOURCE]).body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in {"KEYS","GRIP","MAG_ANCHOR","CELL_NAMES"}):
            authored[node.targets[0].id] = ast.literal_eval(node.value)
    if authored != {"KEYS":KEYS,"GRIP":GRIP,"MAG_ANCHOR":MAG_ANCHOR,"CELL_NAMES":CELL_NAMES}:
        raise ValueError("W179 authored knots/anchors/parts drift")
    if sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != SOURCE_REVIEW_SHA256:
        raise ValueError("Master must install exact reviewed W217 fresh source export/report")
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    report = json.loads(raw[SOURCE_REVIEW])
    old = json.loads(raw[AUTHORED_MANIFEST])
    contacts = json.loads(raw[CONTACTS])["weapons"]["null_composure"]
    elements = source["elements"]
    if (len(elements) != 91
            or tuple(i for i,e in enumerate(elements) if e["name"] in CELL_NAMES) != MOVING
            or tuple(elements[i]["name"] for i in MOVING) != CELL_NAMES
            or old["sourceGeometryFileSha256"] != SOURCE_SHA256
            or old["keyframes"] != json.loads(encode(KEYS))
            or old["partitionIndices"]["magazine"] != list(MOVING)
            or old["gripPivot"] != list(GRIP) or old["magazineAnchor"] != list(MAG_ANCHOR)):
        raise ValueError("Null Composure W179 geometry/UV/partition/anchor drift")
    rule = next(r for r in json.loads(raw[SURFACE_MAP])["targets"]
                if r["path"] == "assets/destiny/models/weapon/fusion_rifle/null_composure.json")
    if (rule["replacement"] != "assets/destiny/models/weapon_surface_w123/null_composure.json"
            or rule["replacementSha256"] != SOURCE_SHA256):
        raise ValueError("Selected Null Composure surface mapping drift")
    if (profile.get("schemaVersion") != 1 or profile.get("weapon") != "null_composure"
            or profile.get("sourceAction") != RIG_ACTION
            or profile.get("sourceRig") != EXPECTED_SOURCE_RIG
            or profile.get("framing") != EXPECTED_FRAMING):
        raise ValueError("W217 profile/source/full-chain/effective framing drift")
    framing = json.loads(raw[FRAMING])
    effective = {**framing["families"]["fusion_rifle"],
                 **framing.get("weapons",{}).get("null_composure",{})}
    if effective != {k:v for k,v in EXPECTED_FRAMING.items()
                     if k not in {"sourceFullChain","keepMeshSupport","hideSupportAtRest"}}:
        raise ValueError("Effective fusion framing changed; re-audit before compensating")
    overrides = profile.get("contacts",{})
    reload = {**contacts["reload"], **overrides.get("reload",{})}
    if (set(overrides) != {"reload"}
            or set(overrides["reload"]) != {"rigAction","partHint","policy","gripWindow"}
            or reload.get("rigAction") != RIG_ACTION
            or reload.get("partHint") != "magazine" or reload.get("policy") != "magazine"
            or reload.get("gripWindow") != [.05,.20,.56,.64]
            or contacts["family"] != "fusion_rifle"
            or contacts["canonicalModel"] != "destiny:weapon_surface_w123/null_composure"
            or contacts["right"] != {"position":[8.,8.5,5.35],"rotation":[-26.,0.,0.]}
            or contacts["left"] != {"position":[7.8,9.35,-5.2],"rotation":[0.,90.,-85.]}
            or reload.get("contact") != [7.1,7.1,.27]
            or reload.get("rotation") != [0.,0.,0.]):
        raise ValueError("Rest contacts or authored .64 battery release drift")
    if (rig.get("group") != EXPECTED_SOURCE_RIG["group"] or rig.get("fallback") is not False
            or "null_composure" not in rig["weapons"] or rig.get("cameraExported") is not False
            or rig.get("space") != "armature_object"
            or rig.get("w217Source61",{}).get("exporterSha256") != EXPORTER_SHA256
            or rig["w217Source61"].get("reloadSamples") != SAMPLES
            or rig["w217Source61"].get("cameraExported") is not False):
        raise ValueError("Expected master W217 original full shoulder-chain source")
    action = rig["actions"][RIG_ACTION]
    if (action["action"] != RIG_ACTION_NAME or len(action["frames"]) != SAMPLES
            or (action["start"],action["end"]) != (1,100)):
        raise ValueError("Expected actual Blender action with61 samples over1..100")
    joints = {"weapon","leftShoulder","leftElbow","leftWrist",
              "rightShoulder","rightElbow","rightWrist"}
    for i,frame in enumerate(action["frames"]):
        if (not joints <= frame["joints"].keys()
                or abs(frame["progress"]-i/INTERVALS) > 1e-12
                or abs(frame["frame"]-(1+99*i/INTERVALS)) > 1e-10):
            raise ValueError("Expected uniformly evaluated original full shoulder chains")
    reviewed = report["groups"][rig["group"]]
    if (report.get("allInputsUnchanged") is not True
            or report.get("exporterSha256") != EXPORTER_SHA256
            or reviewed["objects"] != [{"name":"Armature","type":"ARMATURE"}]
            or reviewed["actions"][RIG_ACTION]["action"] != RIG_ACTION_NAME
            or reviewed["actions"][RIG_ACTION]["slot"] != "OBSlot"
            or reviewed["actions"][RIG_ACTION]["sourceFrameRange"] != [1,100]
            or reviewed["actions"][RIG_ACTION]["maxExistingCacheJointAbsError"] != 0):
        raise ValueError("Fresh original Blender evidence drift")
    for name in ("sourceBlendSha256","sourceMapSha256","boneMapSha256"):
        if rig.get(name) != EXPECTED_SOURCE_RIG[name]:
            raise ValueError("Original rig input changed: "+name)
    geometries = partition(source)
    output = {}
    allowed = expected_output_paths()

    def emit(path,value):
        if path not in allowed:
            raise ValueError("Output outside W217 Null Composure namespace")
        output[root/path] = encode(value)

    for part in PARTS:
        emit(A/f"models/{KEY}_{part}.json",geometries[part])
    entries = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f"models/{KEY}_{frame:02}_{part}_{grip}.json",{
                    "parent":f"destiny:{KEY}_{part}",
                    "display":pose_display(source["display"],twohand,progress,part,grip)})

        def composite(grip):
            return {"type":"minecraft:composite","models":[
                {"type":"minecraft:model","model":f"destiny:{KEY}_{frame:02}_{part}_{grip}"}
                for part in PARTS]}

        model = copy.deepcopy(item["model"]) if frame in (0,INTERVALS) else {
            "type":"minecraft:condition","property":"minecraft:custom_model_data","index":0,
            "on_true":composite("twohand"),"on_false":composite("native")}
        entries.append({"threshold":float32(progress),"model":model})
    wrapper = copy.deepcopy(item)
    wrapper["model"] = {
        "type":"minecraft:select","property":"minecraft:display_context",
        "cases":[{"when":list(FP),"model":{
            "type":"minecraft:select","property":"minecraft:custom_model_data","index":0,
            "cases":[{"when":["ads","inspect"],"model":copy.deepcopy(item["model"])}],
            "fallback":{"type":"minecraft:range_dispatch","property":"minecraft:custom_model_data",
                        "index":1,"entries":entries,"fallback":copy.deepcopy(item["model"])}}}],
        "fallback":copy.deepcopy(item["model"])}
    emit(A/f"items/{KEY}.json",wrapper)
    counts = {part:len(geo["elements"]) for part,geo in geometries.items()}
    canonical_count = len(json.loads(raw[NATIVE])["elements"])
    weapon_count = sum(counts.values())
    if max(weapon_count,canonical_count)+ARM_ELEMENT_RESERVE > 1000:
        raise ValueError("Weapon plus ordinary full-chain arm reserve exceeds1000 elements")
    emit(MANIFEST,{
        "schemaVersion":1,"stage":"W217","weapon":"null_composure",
        "generator":str(GENERATOR),"generatorSha256":sha(raw[GENERATOR]),
        "itemModel":f"destiny:{KEY}","frames":SAMPLES,"intervals":INTERVALS,
        "progressFloatIndex":1,"gripFlagIndex":0,"firstPersonContexts":list(FP),
        "thresholdEncoding":"float32(i/60), matching master runtime grid60",
        "curve":"C1 weighted harmonic PCHIP; zero endpoints, holds and extrema",
        "keyframes":KEYS,"gripPivot":GRIP,"magazineAnchor":MAG_ANCHOR,
        "authoredTimingSource":str(AUTHORED_SOURCE),
        "magazineNeutralSeatedProgress":.64,"reloadGripWindow":reload["gripWindow"],
        "normalizedPhases":old["normalizedPhases"],"reference":old["reference"],
        "referencePolicy":"Retain W179 same-weapon Datto FdLSPBirfps footage provenance; worker read SOURCE.md/manifest, did not reopen video.",
        "sourceGeometryPath":str(SOURCE),"sourceGeometryFileSha256":sha(raw[SOURCE]),
        "sourceElements":len(elements),"partElements":counts,"weaponElements":weapon_count,
        "bodyElements":counts["body"],"movingElements":counts["magazine"],
        "canonicalWeaponElements":canonical_count,"endpointAssembledElements":canonical_count,
        "elementLimit":1000,"ordinaryArmElementReserve":ARM_ELEMENT_RESERVE,
        "candidateReloadWithArmsEstimate":weapon_count+ARM_ELEMENT_RESERVE,
        "candidateKnownCanonicalWithArmsEstimate":canonical_count+ARM_ELEMENT_RESERVE,
        "integratedAllRouteMaximumMeasured":False,
        "budgetBasis":"91 reload weapon+448 ordinary arm reserve=539; native211+448=659. Master measures all composed routes including ADS/inspect under1000.",
        "movingIndices":list(MOVING),"movingNames":list(CELL_NAMES),
        "partitionIndices":old["partitionIndices"],
        "partitionRationale":old["partitionRationale"],
        "authoredHiddenDetails":old["authoredHiddenDetails"],
        "addedElements":0,"triangleAdapterElements":0,
        "sourceElementsAndUVSha256":sha(encode(elements)),
        "partElementsAndUVSha256":{part:sha(encode(geo["elements"])) for part,geo in geometries.items()},
        "canonicalElementsAndUVPreserved":True,"geometryAndUVPreserved":True,
        "hipEndpoints":[0,INTERVALS],"endpointDisplayExact":True,"fallbackModelExact":True,
        "fallback":"Canonical item graph at endpoints, negative progress, overshoot and nonFP; ADS/inspect precede reload; native/twohand flags preserved.",
        "sourceGroup":rig["group"],"sourceAction":RIG_ACTION,"rigAction":RIG_ACTION,
        "rigActionName":action["action"],"sourceActionSourceRange":[action["start"],action["end"]],
        "sourceRigSamples":len(action["frames"]),"sourceFullChain":True,
        "partHint":"magazine","policy":"magazine","w217Source61":rig["w217Source61"],
        "sourceCameraRecovered":False,"sourceEvidence":profile["evidence"],
        "motionAuthorship":"All11 W179 Null Composure knots/holds, grip/cell anchors, rigid composition, three-solid battery, body geometry/UV preserved. W216 contributes weighted harmonic PCHIP only. Master binds shared fusion original shoulder/elbow/wrist FK to ordinary-length fingerless skin arms.",
        "gameplayTimingChanged":False,"mechanicsOrAudioChanged":False,
        "timingPolicy":old["timingPolicy"],
        "nativeGameplayVerified":False,"nativeVisibilityAccepted":False,
        "packFiles":len(output),"totalReturnedFiles":len(output)+1,
        "staticParts":len(PARTS),"parentDisplayChildren":SAMPLES*len(PARTS)*len(GRIPS),
        "inputSha256":{str(path):sha(data) for path,data in raw.items()},
        "outputSha256":{str(path.relative_to(root)):sha(data) for path,data in output.items()},
        "limitations":[
            "Master evaluated original Blender; worker read report/matrices and viewed selected actual bone-only sheet.",
            "Shared fusion ARMATURE only: no recovered weapon mesh/camera/finger IK or weapon-exclusive action.",
            "Hidden battery stroke and mesh contacts remain authored; original source full-chain motion is preserved by master binding.",
            "61 static poses do not prove native continuous60fps interpolation.",
            "Attachment releases during.56..64; battery neutral offset holds.64..1 so later wrist departure cannot drag seated battery.",
            "Effective framing, rest contacts and receiver/grip/triggerguard remain unchanged; no source damping or limb-length compensation.",
            "Master owns measured all-route budget, FIRST images, worker correction/nochange and SECOND; native acceptance pending."]})
    if set(output) != {root/path for path in allowed}:
        raise ValueError("Incomplete W217 Null Composure output mapping")
    return output
