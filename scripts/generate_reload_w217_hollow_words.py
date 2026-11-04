#!/usr/bin/env python3
"""W217 Hollow Words: preserved W185 motion with 61 weighted-PCHIP poses.

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
ART = Path("art/weapons/w217/hollow_words")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w217_hollow_words.py")
AUTHORED_SOURCE = Path("scripts/generate_reload_w185_hollow_words.py")
AUTHORED_MANIFEST = Path("art/weapons/w185/hollow_words/manifest.json")
AUTHORED_REVIEW = Path("art/weapons/w185/hollow_words/SOURCE.md")
SOURCE = A / "models/weapon_surface_w123/hollow_words.json"
NATIVE = A / "models/weapon/fusion_rifle/hollow_words.json"
TWOHAND = A / "models/weapon/fusion_rifle/hollow_words_twohand.json"
ITEM = A / "items/weapon/hollow_words.json"
TEXTURE = A / "textures/item/weapon/w123/hollow_words.png"
CONTACTS = Path("art/weapons/w201/contacts.json")
RIG = Path("art/weapons/w205/rigs/fusion_rifle_04669cdb.json")
SOURCE_REVIEW = Path("docs/qa/2026-10-28/w217/source/source-review.json")
FRAMING = Path("art/weapons/w205/first-person-framing.json")
FRAMING_LOADER = Path("scripts/first_person_framing_w205.py")
SURFACE_MAP = Path("src/main/resources/weapon_surface_w123/manifest.json")
KEY = "weapon_reload_w217_hollow_words/hollow_words"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine")
GRIPS = ("native", "twohand")
INTERVALS = 60
SAMPLES = 61
RIG_ACTION = "80A8ADD3"
RIG_ACTION_NAME = "Armature|fp_80A8ADD3_reload_full|Base"
ARM_ELEMENT_RESERVE = 4 * 112
MOVING = (53,)
SOURCE_SHA256 = '328eed84bf275da019d40d25e3306d48bd00473cf4f64c19d088e6fec91d330a'
RIG_SHA256 = '747749cea16ee1bec34df57fbb7fb8b6c7bb32e6dd1dfef6188991a0d2e4d76a'
SOURCE_REVIEW_SHA256 = 'd8edb0d97be1b4cc1446363216ac271fb6bbb1a91f3b52f1fa0b3dc48388fd6a'
EXPORTER_SHA256 = '69694b95b969d2027d7e1b2afc532b2c0a3480c8b86662fc7d61165ed2924769'
AUTHORED_SHA256 = 'c48e870328e097cecd568f9097181e4730cf9cd49f9a24ae560c78d45333dec1'
EXPECTED_FRAMING = {'translation': [-0.65, 0.6, 0], 'rotation': [-1, 2, 0], 'scale': 0.98, 'rightWristRoll': 28, 'leftRotation': [15, 35, -35], 'sourceFullChain': True, 'keepMeshSupport': True, 'hideSupportAtRest': False}
EXPECTED_SOURCE_RIG = {'group': 'fusion_rifle_04669cdb', 'action': '80A8ADD3', 'sourceBlendSha256': 'cdf955feedf818492dd395a2866beb19ed11bb35944544c05c3cd4eb00eeee36', 'sourceMapSha256': '27b7520526de9abf593e208b6f0b52f70c83e2a4a6ddaada7bcd3dc40eac9ad2', 'boneMapSha256': 'a439c489fb5ab1de893beb8cfe682958641d1c2682059f849932a25db27d3fd4'}
GRIP = (8.0, 7.17, 2.55)
MAGAZINE_ANCHOR = (8.0, 4.35, 3.7)
MAGAZINE_NAMES = ('under_grip_cell',)
KEYS = ((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.08, (18, -3, -7), (0.12, -0.06, 0.03), (0, 0, 0)), (0.18, (60, -8, -22), (0.34, 0.15, 0.16), (0, 0, 0)), (0.26, (66, -9, -24), (0.38, 0.24, 0.2), (0, -1.65, -0.685)), (0.38, (65, -8, -25), (0.4, 0.23, 0.21), (-0.3, -4.8, -1.99)), (0.48, (64, -8, -24), (0.39, 0.2, 0.2), (-0.5, -4.8, -1.99)), (0.58, (63, -7, -23), (0.36, 0.16, 0.18), (-0.1, -1.55, -0.643)), (0.64, (61, -7, -22), (0.34, 0.12, 0.16), (0, 0, 0)), (0.72, (48, -3, -30), (0.27, 0.03, 0.12), (0, 0, 0)), (0.8, (20, 3, -18), (0.16, -0.1, 0.06), (0, 0, 0)), (0.88, (-4, 2, -4), (0.05, -0.15, 0.01), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/hollow_words.json': '328eed84bf275da019d40d25e3306d48bd00473cf4f64c19d088e6fec91d330a', 'src/main/resources/assets/destiny/textures/item/weapon/w123/hollow_words.png': '6d1ddd0c20a29f7415d9915ccf5dc1137ff3cc0b8539165327ab012a2a5329cf', 'src/main/resources/assets/destiny/items/weapon/hollow_words.json': 'ab5a2dab42d81d8d5fd412f49a0fff5f9759fb8b6659f015ac770ed70683bf31', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words_twohand.json': 'a0cea3376e63fc39ead3af6218963483f124e1eab2ac29fac170812c86b53a4f', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words_ads.json': 'c56abca4a30e460bc86f069b89b213c5ab5754e07ba5c3e849f1dddc39f48fcf', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words_inspect.json': 'd645952f47c92417069075bd00b11b97e1c801f845b56dc0a10a605f67a7519b', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words.json': 'eaf326afdc1711f6ae642c178398f39ef75038b83f705128e11963636a267fb5', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words_inspect_twohand.json': '35afc5f4b17f51c1189c446232696ff8611efc61cc00b50505ed638ddf5107c2', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words_ads_twohand.json': '9254ade2b2599a3cf98c46696fca5b3c4ae4c5a284536bb002a04caa4e644a77'}

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
    # Reference n11244..11292: underside exchange, fixed open grip intact.
    # A single narrow insert follows the existing front-grip axis; hidden proportions authored.
    shaft=copy.deepcopy(source['elements'][53])
    shaft.update(name='magazine_shaft_upper', **{'from':[7.65,6.25,-.35],'to':[8.35,6.85,1.9]})
    shaft['rotation']=copy.deepcopy(source['elements'][43]['rotation'])
    return [shaft]

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
        raise ValueError("W185 authored source changed; re-audit before generating")
    authored = {}
    for node in ast.parse(raw[AUTHORED_SOURCE]).body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in {"KEYS", "GRIP", "MAGAZINE_ANCHOR", "MAGAZINE_NAMES"}):
            authored[node.targets[0].id] = ast.literal_eval(node.value)
    if authored != {"KEYS": KEYS, "GRIP": GRIP, "MAGAZINE_ANCHOR": MAGAZINE_ANCHOR,
                    "MAGAZINE_NAMES": MAGAZINE_NAMES}:
        raise ValueError("W185 authored knots/anchors changed")
    if (sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != SOURCE_REVIEW_SHA256):
        raise ValueError("Master must install the reviewed fresh W217 normalized source export/report")
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    report = json.loads(raw[SOURCE_REVIEW])
    old = json.loads(raw[AUTHORED_MANIFEST])
    contacts = json.loads(raw[CONTACTS])["weapons"]["hollow_words"]
    elements = source["elements"]
    if (len(elements) != 96 or
            tuple(i for i,e in enumerate(elements) if is_payload(e)) != MOVING or
            tuple(elements[i]["name"] for i in MOVING) != MAGAZINE_NAMES or
            old["sourceGeometryFileSha256"] != SOURCE_SHA256 or
            old["keyframes"] != json.loads(encode(KEYS)) or
            old["partitionIndices"]["magazine"] != list(MOVING) or
            old["reloadOnlyGeometry"]["elements"] != reload_shaft(source)):
        raise ValueError("Hollow Words W185 geometry/UV/partition drift")
    rule = next(r for r in json.loads(raw[SURFACE_MAP])["targets"]
                if r["path"] == "assets/destiny/models/weapon/fusion_rifle/hollow_words.json")
    if (rule["replacement"] != "assets/destiny/models/weapon_surface_w123/hollow_words.json"
            or rule["replacementSha256"] != SOURCE_SHA256):
        raise ValueError("Selected Hollow Words surface mapping changed")
    if (profile.get("schemaVersion") != 1 or profile.get("weapon") != "hollow_words"
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
            or reload.get("gripWindow") != [.05, .18, .58, .64]
            or contacts["family"] != "fusion_rifle"
            or contacts["canonicalModel"] != "destiny:weapon_surface_w123/hollow_words"
            or contacts["right"] != {"position": [8.,7.2,2.55], "rotation": [22.,0.,0.]}
            or contacts["left"] != {"position": [7.8,9.05,-4.6], "rotation": [0.,90.,-85.]}
            or reload.get("contact") != [7.3,4.35,3.7]
            or reload.get("rotation") != [22.,0.,0.]):
        raise ValueError("Rest contacts or authored .64 cell release changed")
    if (rig.get("group") != "fusion_rifle_04669cdb" or rig.get("fallback") is not False
            or "hollow_words" not in rig["weapons"] or rig.get("cameraExported") is not False
            or rig.get("space") != "armature_object"
            or rig.get("w217Source61", {}).get("exporterSha256") != EXPORTER_SHA256
            or rig["w217Source61"].get("reloadSamples") != SAMPLES
            or rig["w217Source61"].get("cameraExported") is not False):
        raise ValueError("Expected fresh master W217 original shoulder-chain source")
    action = rig["actions"][RIG_ACTION]
    if (action["action"] != RIG_ACTION_NAME or len(action["frames"]) != SAMPLES
            or (action["start"], action["end"]) != (1,100)):
        raise ValueError("Expected actual Blender action name and61 samples over1..100")
    joints = {"weapon", "leftShoulder", "leftElbow", "leftWrist",
              "rightShoulder", "rightElbow", "rightWrist"}
    for i,frame in enumerate(action["frames"]):
        if (not joints <= frame["joints"].keys()
                or abs(frame["progress"]-i/INTERVALS) > 1e-12
                or abs(frame["frame"]-(1+99*i/INTERVALS)) > 1e-10):
            raise ValueError("Expected uniformly evaluated original full shoulder chains")
    reviewed = report["groups"][rig["group"]]
    if (report.get("allInputsUnchanged") is not True
            or report.get("exporterSha256") != EXPORTER_SHA256
            or reviewed["objects"] != [{"name": "Armature", "type": "ARMATURE"}]
            or reviewed["actions"][RIG_ACTION]["action"] != RIG_ACTION_NAME
            or reviewed["actions"][RIG_ACTION]["sourceFrameRange"] != [1,100]
            or reviewed["actions"][RIG_ACTION]["slot"] != "OBSlot"
            or reviewed["actions"][RIG_ACTION]["samples"] != SAMPLES
            or reviewed["actions"][RIG_ACTION]["maxExistingCacheJointAbsError"] != 0.0):
        raise ValueError("Fresh original Blender report changed")
    for name in ("sourceBlendSha256", "sourceMapSha256", "boneMapSha256"):
        if rig.get(name) != EXPECTED_SOURCE_RIG[name]:
            raise ValueError("Original rig input changed: " + name)
    geometries = partition(source)
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError("Output outside W217 Hollow Words namespace")
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
        "schemaVersion": 1, "stage": "W217", "weapon": "hollow_words",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0, "firstPersonContexts": list(FP),
        "thresholdEncoding": "float32(i/60), matching master runtime grid60",
        "curve": "C1 weighted harmonic PCHIP; zero endpoints, holds and extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "magazineAnchor": MAGAZINE_ANCHOR,
        "authoredTimingSource": str(AUTHORED_SOURCE),
        "magazineNeutralSeatedProgress": .64, "reloadGripWindow": reload["gripWindow"],
        "normalizedPhases": old["normalizedPhases"],
        "reference": old["reference"],
        "referencePolicy": "Retain W185 same-weapon Ironworker Gaming ozOSAOr5T4c footage provenance; worker read SOURCE.md/manifest and viewed retained storyboard; did not reopen video.",
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": len(elements), "partElements": counts, "weaponElements": weapon_count,
        "bodyElements": counts["body"], "movingElements": counts["magazine"],
        "canonicalWeaponElements": canonical_count, "endpointAssembledElements": len(elements),
        "elementLimit": 1000, "ordinaryArmElementReserve": ARM_ELEMENT_RESERVE,
        "candidateReloadWithArmsEstimate": weapon_count+ARM_ELEMENT_RESERVE,
        "candidateKnownCanonicalWithArmsEstimate": canonical_count+ARM_ELEMENT_RESERVE,
        "integratedAllRouteMaximumMeasured": False,
        "budgetBasis": "97 reload weapon+448 estimated ordinary arm elements=545; raw native238+448=686. Master measures all composed routes including ADS/inspect under1000.",
        "movingIndices": list(MOVING), "movingNames": list(MAGAZINE_NAMES),
        "partitionIndices": old["partitionIndices"], "semanticGroups": old["semanticGroups"],
        "partitionRationale": "95 body solids fixed; under_grip_cell53 plus existing W185 narrow upper insert move rigidly. Entire front grip/heel, lower brace, receiver, triggerguard, rear struts and optic stay on the body. Lower-cell intersection does not justify moving fixed grip solids.",
        "addedElements": 1, "newElementsRelativeToW185": 0, "triangleAdapterElements": 0,
        "reloadOnlyGeometry": old["reloadOnlyGeometry"], "sourceLimitation": old["sourceLimitation"],
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
        "motionAuthorship": "All12 W185 Hollow Words knots/holds, rigid algebra, whole powercell path, geometry/UV and hidden insert preserved. Only interpolation becomes W215/W216 weighted harmonic PCHIP. Shared original fusion ARMATURE handling is not a weapon-exclusive recovered mesh or action. Master binds full original weapon-relative shoulder/elbow/wrist FK with ordinary limb lengths/axes and fingerless skin arms.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "timingPolicy": "Retain capacity6,50tick reload,800ms/16tick charge,7-shot burst/sharedBurstAmmo=true,13tick cadence, ammo lifecycle and audio; original30fps frames1..100 do not retime gameplay.",
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "packFiles": len(output), "totalReturnedFiles": len(output)+1,
        "staticParts": len(PARTS), "parentDisplayChildren": SAMPLES*len(PARTS)*len(GRIPS),
        "inputSha256": {str(path):sha(data) for path,data in raw.items()},
        "outputSha256": {str(path.relative_to(root)):sha(data) for path,data in output.items()},
        "limitations": [
            "Master evaluated original Blender5.4; worker read fresh report/matrices and viewed actual80A8ADD3 bone-only upper-chain sheet.",
            "Original ARMATURE only: no recovered weapon mesh/camera/finger IK; this shared fusion source is not weapon-exclusive. Authored contacts and hidden cell/insert proportions need FIRST.",
            "61 static poses do not prove native continuous60fps interpolation.",
            "Attachment releases through.58..64; powercell neutral offset holds.64..1 so later wrist departure cannot drag the seated payload.",
            "Current effective framing/rest contacts retained; no new arm/camera compensations, length changes or source attenuation.",
            "Master owns integration, all-route measured budget, FIRST feedback, worker correction/nochange and SECOND. Native acceptance pending."]})
    if set(output) != {root/path for path in allowed}:
        raise ValueError("Incomplete W217 Hollow Words output mapping")
    return output
