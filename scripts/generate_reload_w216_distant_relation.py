#!/usr/bin/env python3
"""W216 Distant Relation: preserved W184 motion with 61 weighted-PCHIP poses.

Pure stdlib; import and generate(root=ROOT) never write. Master binds the fresh
original full-chain rig, materializes bytes, measures routes and owns FIRST/SECOND.
Weapon geometry, occluded magazine path and mesh contacts remain authored.
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
ART = Path("art/weapons/w216/distant_relation")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w216_distant_relation.py")
AUTHORED_SOURCE = Path("scripts/generate_reload_w184_distant_relation.py")
AUTHORED_MANIFEST = Path("art/weapons/w184/distant_relation/manifest.json")
AUTHORED_REVIEW = Path("art/weapons/w184/distant_relation/SOURCE.md")
SOURCE = A / "models/weapon_surface_w123/distant_relation.json"
NATIVE = A / "models/weapon/scout_rifle/distant_relation.json"
TWOHAND = A / "models/weapon/scout_rifle/distant_relation_twohand.json"
ITEM = A / "items/weapon/distant_relation.json"
TEXTURE = A / "textures/item/weapon/w123/distant_relation.png"
CONTACTS = Path("art/weapons/w201/contacts.json")
RIG = Path("art/weapons/w205/rigs/scout_rifle_98cec92a.json")
SOURCE_REVIEW = Path("docs/qa/2026-10-28/w216/source/source-review.json")
FRAMING = Path("art/weapons/w205/first-person-framing.json")
FRAMING_LOADER = Path("scripts/first_person_framing_w205.py")
SURFACE_MAP = Path("src/main/resources/weapon_surface_w123/manifest.json")
KEY = "weapon_reload_w216_distant_relation/distant_relation"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine")
GRIPS = ("native", "twohand")
INTERVALS = 60
SAMPLES = 61
RIG_ACTION = "80A8A345"
RIG_ACTION_NAME = "Armature|fp_80A8A345_reload_full|Base"
ARM_ELEMENT_RESERVE = 4 * 112
MOVING = (58, 59)
SOURCE_SHA256 = "d10b3875818623b552230fa53bfa26625e3faf86db450ec964aaabd1bb59f8e5"
RIG_SHA256 = "83b850d2d8c60439aefd0f56eb9d6374e38fa237be81e8b5a5ae09e2f6a9c544"
SOURCE_REVIEW_SHA256 = "3b5ec3c27772222c14730457fd1d9ff431c39802ae4df10bb7f286440aaf61d6"
EXPORTER_SHA256 = "54b2f8673aaf75b97a388077ecad683eef2441a73f313194e52ce9b6cd514a38"
AUTHORED_SHA256 = "d62c0ff6c4b33cac5ad3595ff9106d47af0da8c0a85d4811fc662cc82880a6f9"
EXPECTED_FRAMING = {
    "translation": [-.65, .6, 0], "rotation": [-1, 2, 0], "scale": .98,
    "rightWristRoll": 28, "leftRotation": [15, 35, -35],
    "sourceFullChain": True, "keepMeshSupport": True, "hideSupportAtRest": False}
EXPECTED_SOURCE_RIG = {
    "group": "scout_rifle_98cec92a", "action": RIG_ACTION,
    "sourceBlendSha256": "be7c6bb31dc5734de8a82d93fb92c619e581fa2c7bd04951e59e884aebf49941",
    "sourceMapSha256": "d97ed313c4bcec5414900a745b6657e578623348908b0ed91205f5e34f5d3315",
    "boneMapSha256": "34cc654306ee835cf908f72fed910a3955868195289e1109178a45c237fcee40"}
GRIP = (8.0, 8.55, 8.3)
MAGAZINE_ANCHOR = (8.0, 6.69, 10.72)
MAGAZINE_NAMES = ('magazine_body', 'magazine_floor')
KEYS = ((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.08, (16, -2, -2), (0.08, -0.1, 0), (0, 0, 0)), (0.2, (70, 7, -10), (0.3, 0.15, 0.18), (0, 0, 0)), (0.32, (75, 9, -12), (0.38, 0.23, 0.22), (0.2, -4.5, -3.1)), (0.44, (73, 8, -13), (0.38, 0.23, 0.22), (-0.35, -4.5, -3.1)), (0.6, (71, 9, -12), (0.35, 0.2, 0.2), (-0.04, -0.6, -0.42)), (0.66, (68, 8, -10), (0.32, 0.17, 0.17), (0, 0, 0)), (0.74, (35, 4, -5), (0.18, 0.04, 0.08), (0, 0, 0)), (0.82, (4, 1, -1), (0.04, -0.08, 0.02), (0, 0, 0)), (0.9, (-6, -1, 1), (0, -0.16, 0), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/distant_relation.json': 'd10b3875818623b552230fa53bfa26625e3faf86db450ec964aaabd1bb59f8e5', 'src/main/resources/assets/destiny/textures/item/weapon/w123/distant_relation.png': '693ded07b8b1f398bf9a9d9791ce49af945a4e524d11a200f9239943d64a161a', 'src/main/resources/assets/destiny/items/weapon/distant_relation.json': 'f27c06fa03339ee11092a836cf078cf3d114a078c3e66a1ebd0d1ab1799fd473', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation_inspect_twohand.json': '22615532c09371ff3e0a8b4a3d944d5cfef5f3c852d70acec959016ae274d69d', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation_ads_twohand.json': 'b08764a5018b4e6c20e50ec381ffe9742e32a7dad936a32c8cfc9cb44f2cb15f', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation_inspect.json': 'da1f721a14d5d231aba7c9ee25adeed051b91a6ccdc42438f53f4c6c1ed9de6a', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation.json': '126bd1a3aea23bbbb77ae010441e102a751a281defd4e59f6aa6f46ba2ae4801', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation_ads.json': '30444a73329e00d1b7d006ef82777fc58357cbc1d2416a59bb52d7ada81b82bf', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation_twohand.json': '844668f0dbc31731c018e736f25ae4a1720ce18b9f1c4ab5846c41898fa898fb'}

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

def is_payload(e):return e['name'] in MAGAZINE_NAMES

def reload_shaft(source):
    # Incoming full box visible n20118. Only hidden upper neck is added;
    # original body/floor and existing fluted face paint remain exact.
    neck=copy.deepcopy(source['elements'][58])
    neck.update(name='magazine_shaft_upper',**{'from':[7.73,6.80,11.50],'to':[8.27,7.00,13.00]})
    return [neck]

def partition(source):
    return {part:{**{k:copy.deepcopy(v) for k,v in source.items() if k!='elements'},
                  'elements':[copy.deepcopy(e) for e in source['elements']
                              if is_payload(e)==(part=='magazine')]+(reload_shaft(source) if part=='magazine' else [])}
            for part in PARTS}

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8))
    # Original body/floor and reference-backed reload-only upper neck move as one rigid payload.
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
        raise ValueError("W184 authored source changed; re-audit before generating")
    authored = {}
    for node in ast.parse(raw[AUTHORED_SOURCE]).body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in {"KEYS", "GRIP", "MAGAZINE_ANCHOR", "MAGAZINE_NAMES"}):
            authored[node.targets[0].id] = ast.literal_eval(node.value)
    if authored != {"KEYS": KEYS, "GRIP": GRIP, "MAGAZINE_ANCHOR": MAGAZINE_ANCHOR,
                    "MAGAZINE_NAMES": MAGAZINE_NAMES}:
        raise ValueError("W184 authored knots/anchors changed")
    if (sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != SOURCE_REVIEW_SHA256):
        raise ValueError("Master must install the reviewed fresh W216 normalized source export/report")
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    report = json.loads(raw[SOURCE_REVIEW])
    old = json.loads(raw[AUTHORED_MANIFEST])
    contacts = json.loads(raw[CONTACTS])["weapons"]["distant_relation"]
    elements = source["elements"]
    if (len(elements) != 88 or
            tuple(i for i,e in enumerate(elements) if is_payload(e)) != MOVING or
            tuple(elements[i]["name"] for i in MOVING) != MAGAZINE_NAMES or
            old["sourceGeometryFileSha256"] != SOURCE_SHA256 or
            old["keyframes"] != json.loads(encode(KEYS)) or
            old["partitionIndices"]["magazine"] != list(MOVING) or
            old["reloadOnlyGeometry"]["elements"] != reload_shaft(source)):
        raise ValueError("Distant Relation W184 geometry/UV/partition drift")
    rule = next(r for r in json.loads(raw[SURFACE_MAP])["targets"]
                if r["path"] == "assets/destiny/models/weapon/scout_rifle/distant_relation.json")
    if (rule["replacement"] != "assets/destiny/models/weapon_surface_w123/distant_relation.json"
            or rule["replacementSha256"] != SOURCE_SHA256):
        raise ValueError("Selected Distant Relation surface mapping changed")
    if (profile.get("schemaVersion") != 1 or profile.get("weapon") != "distant_relation"
            or profile.get("sourceAction") != RIG_ACTION
            or profile.get("sourceRig") != EXPECTED_SOURCE_RIG
            or profile.get("framing") != EXPECTED_FRAMING):
        raise ValueError("W216 profile/source/full-chain/effective framing drift")
    overrides = profile.get("contacts", {})
    reload = {**contacts["reload"], **overrides.get("reload", {})}
    if (set(overrides) != {"reload"} or
            set(overrides["reload"]) != {"rigAction", "partHint", "policy", "gripWindow"}
            or reload.get("rigAction") != RIG_ACTION
            or reload.get("partHint") != "magazine" or reload.get("policy") != "magazine"
            or reload.get("gripWindow") != [.05, .20, .60, .66]
            or contacts["family"] != "scout_rifle"
            or contacts["canonicalModel"] != "destiny:weapon_surface_w123/distant_relation"
            or contacts["right"] != {"position": [8.,8.62,8.35], "rotation": [-22.,0.,0.]}
            or contacts["left"] != {"position": [7.8,9.05,-.4], "rotation": [0.,90.,-85.]}
            or reload.get("contact") != [7.55,6.65,10.68]
            or reload.get("rotation") != [35.,0.,0.]):
        raise ValueError("Rest contacts or authored .66 magazine release changed")
    if (rig.get("group") != "scout_rifle_98cec92a" or rig.get("fallback") is not False
            or "distant_relation" not in rig["weapons"] or rig.get("cameraExported") is not False
            or rig.get("space") != "armature_object"
            or rig.get("w216Source61", {}).get("exporterSha256") != EXPORTER_SHA256
            or rig["w216Source61"].get("reloadSamples") != SAMPLES
            or rig["w216Source61"].get("cameraExported") is not False):
        raise ValueError("Expected fresh master W216 original shoulder-chain source")
    action = rig["actions"][RIG_ACTION]
    if (action["action"] != RIG_ACTION_NAME or len(action["frames"]) != SAMPLES
            or (action["start"], action["end"]) != (1,105)):
        raise ValueError("Expected actual Blender action name and61 samples over1..105")
    joints = {"weapon", "leftShoulder", "leftElbow", "leftWrist",
              "rightShoulder", "rightElbow", "rightWrist"}
    for i,frame in enumerate(action["frames"]):
        if (not joints <= frame["joints"].keys()
                or abs(frame["progress"]-i/INTERVALS) > 1e-12
                or abs(frame["frame"]-(1+104*i/INTERVALS)) > 1e-10):
            raise ValueError("Expected uniformly evaluated original full shoulder chains")
    reviewed = report["groups"][rig["group"]]
    if (report.get("allInputsUnchanged") is not True
            or report.get("exporterSha256") != EXPORTER_SHA256
            or reviewed["objects"] != [{"name": "Armature", "type": "ARMATURE"}]
            or reviewed["actions"][RIG_ACTION]["action"] != RIG_ACTION_NAME
            or reviewed["actions"][RIG_ACTION]["sourceFrameRange"] != [1,105]):
        raise ValueError("Fresh original Blender report changed")
    for name in ("sourceBlendSha256", "sourceMapSha256", "boneMapSha256"):
        if rig.get(name) != EXPECTED_SOURCE_RIG[name]:
            raise ValueError("Original rig input changed: " + name)
    geometries = partition(source)
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError("Output outside W216 Distant Relation namespace")
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
        "schemaVersion": 1, "stage": "W216", "weapon": "distant_relation",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0, "firstPersonContexts": list(FP),
        "thresholdEncoding": "float32(i/60), matching master runtime grid60",
        "curve": "C1 weighted harmonic PCHIP; zero endpoints, holds and extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "magazineAnchor": MAGAZINE_ANCHOR,
        "authoredTimingSource": str(AUTHORED_SOURCE),
        "magazineNeutralSeatedProgress": .66, "reloadGripWindow": reload["gripWindow"],
        "normalizedPhases": old["normalizedPhases"],
        "reference": old["reference"],
        "referencePolicy": "Retain W184 same-weapon DFP footage provenance; worker read SOURCE.md/manifest, did not reopen video.",
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": len(elements), "partElements": counts, "weaponElements": weapon_count,
        "bodyElements": counts["body"], "movingElements": counts["magazine"],
        "canonicalWeaponElements": canonical_count, "endpointAssembledElements": canonical_count,
        "elementLimit": 1000, "ordinaryArmElementReserve": ARM_ELEMENT_RESERVE,
        "candidateReloadWithArmsEstimate": weapon_count+ARM_ELEMENT_RESERVE,
        "candidateKnownCanonicalWithArmsEstimate": canonical_count+ARM_ELEMENT_RESERVE,
        "integratedAllRouteMaximumMeasured": False,
        "budgetBasis": "89 reload weapon+448 estimated ordinary arm elements=537; native244+448=692. Master measures all composed routes including ADS/inspect under1000.",
        "movingIndices": list(MOVING), "movingNames": list(MAGAZINE_NAMES),
        "partitionIndices": old["partitionIndices"], "semanticGroups": old["semanticGroups"],
        "partitionRationale": "86 body solids fixed; magazine_body58 and magazine_floor59 plus existing W184 upper neck move rigidly. Bolt_slide/stem/knob, grip, stock, loops and optic stay fixed.",
        "addedElements": 1, "newElementsRelativeToW184": 0, "triangleAdapterElements": 0,
        "reloadOnlyGeometry": old["reloadOnlyGeometry"], "sourceLimitation": old["sourceLimitation"],
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {part:sha(encode(geo["elements"])) for part,geo in geometries.items()},
        "canonicalElementsAndUVPreserved": True, "geometryAndUVPreserved": True,
        "hipEndpoints": [0,INTERVALS], "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Canonical item graph at endpoints, negative progress, overshoot and nonFP; ADS/inspect precede reload; native/twohand flags preserved.",
        "sourceGroup": rig["group"], "sourceAction": RIG_ACTION, "rigAction": RIG_ACTION,
        "rigActionName": action["action"], "sourceActionSourceRange": [action["start"],action["end"]],
        "sourceRigSamples": len(action["frames"]), "sourceFullChain": True,
        "partHint": "magazine", "policy": "magazine", "w216Source61": rig["w216Source61"],
        "sourceCameraRecovered": False, "sourceEvidence": profile["evidence"],
        "motionAuthorship": "All11 W184 knots/holds, rigid algebra, whole-magazine path, geometry/UV and hidden upper neck preserved. Only interpolation becomes W215 weighted harmonic PCHIP. Master binds original weapon-relative shoulder/elbow/wrist FK, ordinary limb lengths/axes and fingerless skin arms.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "timingPolicy": "Retain16 rounds,180RPM,44tick reload, ammo lifecycle and audio; original30fps frames1..105 do not retime gameplay.",
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "packFiles": len(output), "totalReturnedFiles": len(output)+1,
        "staticParts": len(PARTS), "parentDisplayChildren": SAMPLES*len(PARTS)*len(GRIPS),
        "inputSha256": {str(path):sha(data) for path,data in raw.items()},
        "outputSha256": {str(path.relative_to(root)):sha(data) for path,data in output.items()},
        "limitations": [
            "Master evaluated original Blender; worker read fresh report/matrices and viewed selected plus two alternative bone-only sheets.",
            "Original ARMATURE only: no weapon mesh/camera/finger IK; authored contacts and hidden magazine/neck proportions need FIRST.",
            "61 static poses do not prove native continuous60fps interpolation.",
            "Attachment releases through.60..66; magazine neutral offset holds.66..1 so later wrist departure cannot drag seated payload.",
            "Current effective framing/rest contacts retained; no new arm/camera compensations, length changes or source attenuation.",
            "Master owns integration, all-route measured budget, FIRST feedback, worker correction/nochange and SECOND. Native acceptance pending."]})
    if set(output) != {root/path for path in allowed}:
        raise ValueError("Incomplete W216 Distant Relation output mapping")
    return output
