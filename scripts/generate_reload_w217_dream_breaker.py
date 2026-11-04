#!/usr/bin/env python3
"""W217 Dream Breaker: preserved W178 cell reload with61 weighted-PCHIP poses.

Pure stdlib. Import and generate(root=ROOT) never write or execute the legacy
generator. Master owns materialization, original full-chain binding and native QA.
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
ART = Path("art/weapons/w217/dream_breaker")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w217_dream_breaker.py")
AUTHORED_SOURCE = Path("scripts/generate_reload_w178_dream_breaker.py")
AUTHORED_MANIFEST = Path("art/weapons/w178/dream_breaker/manifest.json")
AUTHORED_REVIEW = Path("art/weapons/w178/dream_breaker/motion-reference.json")
SOURCE = A / "models/weapon_surface_w123/dream_breaker.json"
NATIVE = A / "models/weapon/fusion_rifle/dream_breaker.json"
TWOHAND = A / "models/weapon/fusion_rifle/dream_breaker_twohand.json"
ITEM = A / "items/weapon/dream_breaker.json"
TEXTURE = A / "textures/item/weapon/w123/dream_breaker.png"
CONTACTS = Path("art/weapons/w201/contacts.json")
RIG = Path("art/weapons/w205/rigs/fusion_rifle_04669cdb.json")
SOURCE_REVIEW = Path("docs/qa/2026-10-28/w217/source/source-review.json")
FRAMING = Path("art/weapons/w205/first-person-framing.json")
FRAMING_LOADER = Path("scripts/first_person_framing_w205.py")
SURFACE_MAP = Path("src/main/resources/weapon_surface_w123/manifest.json")
KEY = "weapon_reload_w217_dream_breaker/dream_breaker"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine")
GRIPS = ("native", "twohand")
INTERVALS = 60
SAMPLES = 61
RIG_ACTION = "80A8ADD3"
RIG_ACTION_NAME = "Armature|fp_80A8ADD3_reload_full|Base"
ARM_ELEMENT_RESERVE = 448
MOVING = (27, 28, 29, 30)
SOURCE_SHA256 = '2116c53ffc4ad4ec6fa7c0cd9c8ff96fe71b8233af9b0927c579ed594d4d8e93'
RIG_SHA256 = '747749cea16ee1bec34df57fbb7fb8b6c7bb32e6dd1dfef6188991a0d2e4d76a'
SOURCE_REVIEW_SHA256 = 'd8edb0d97be1b4cc1446363216ac271fb6bbb1a91f3b52f1fa0b3dc48388fd6a'
EXPORTER_SHA256 = '69694b95b969d2027d7e1b2afc532b2c0a3480c8b86662fc7d61165ed2924769'
AUTHORED_SHA256 = '2b280f470ee2fbcc00fc6f906550cd65a0f1d4c37b16156261dcf90441cf739c'
EXPECTED_FRAMING = {'translation': [-0.65, 0.6, 0],
 'rotation': [-1, 2, 0],
 'scale': 0.98,
 'rightWristRoll': 28,
 'leftRotation': [15, 35, -35],
 'sourceFullChain': True,
 'keepMeshSupport': True,
 'hideSupportAtRest': False}
EXPECTED_SOURCE_RIG = {'group': 'fusion_rifle_04669cdb',
 'action': '80A8ADD3',
 'sourceBlendSha256': 'cdf955feedf818492dd395a2866beb19ed11bb35944544c05c3cd4eb00eeee36',
 'sourceMapSha256': '27b7520526de9abf593e208b6f0b52f70c83e2a4a6ddaada7bcd3dc40eac9ad2',
 'boneMapSha256': 'a439c489fb5ab1de893beb8cfe682958641d1c2682059f849932a25db27d3fd4'}
CELL_NAMES = ('powerpack_full', 'pack_heel', 'pack_ribbed_side_-1', 'pack_ribbed_side_1')
GRIP = (8.0, 8.05, 9.21)
MAG_ANCHOR = (8.0, 7.75, 3.57)
KEYS = ((0.0, (0, 0, 0), (0, 0, 0), (0, 0, 0)),
 (0.09, (40, -6, -15), (0.15, -0.25, 0.15), (0, 0, 0)),
 (0.2, (62, -12, -27), (0.25, -0.15, 0.25), (0, -0.5, 0)),
 (0.3, (66, -10, -25), (0.2, -0.1, 0.3), (-0.5, -4.3, 0.25)),
 (0.43, (69, -9, -23), (0.2, -0.1, 0.3), (-2.4, -7.8, 0.5)),
 (0.54, (61, -12, -27), (0.2, -0.15, 0.25), (-2.4, -7.8, 0.5)),
 (0.66, (59, -12, -27), (0.2, -0.15, 0.25), (-1.2, -5.5, 0.3)),
 (0.78, (62, -11, -24), (0.2, -0.1, 0.2), (0, -1.2, 0)),
 (0.84, (60, -10, -22), (0.15, -0.1, 0.15), (0, 0, 0)),
 (0.92, (29, -5, -11), (0.05, -0.05, 0.05), (0, 0, 0)),
 (1.0, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/dream_breaker.json': '2116c53ffc4ad4ec6fa7c0cd9c8ff96fe71b8233af9b0927c579ed594d4d8e93',
 'src/main/resources/assets/destiny/textures/item/weapon/w123/dream_breaker.png': 'c9bcbf03e80e6209c46fc13ea6b1097161d74fbb1983e1162fdeccc1d72a5b1c',
 'src/main/resources/assets/destiny/items/weapon/dream_breaker.json': '5e5ee00e4d9473bd672f16eabece08040b660c8420817ac7ddf1cb158098e540',
 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07',
 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b',
 'src/main/resources/weapon_surface_w123/manifest.json': '4972bd808e5150d09e8f55e2c663b45f88ad8e660300310c5ecc04f4f672db6b',
 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker.json': 'c76b3daea47cdc06ed707bc178884f78a669762f6fea35d3fc811422269ddf42',
 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker_ads.json': 'fe623cf2b7406cc392faf49339ca2c6d1a8318a044dc85bb16eca8ab83d776a7',
 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker_ads_twohand.json': '58283e54b15e5f3aefa92487c172171934d70ae783dcf596cdedbec77edfa0e4',
 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker_inspect.json': '1d86bff6c34993a1c39246d8d899c7a47806a2a2656cf450e14561a94e060137',
 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker_inspect_twohand.json': '4f742e62ad2da47bda62ed931a3e6f927d8a315423226282e756f366fcaae34c',
 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker_twohand.json': '65edb5025d2143143f8c389d2f81fbd98286699ba01c725fa092076fef84102f',
 'src/main/resources/assets/destiny/items/weapon_sight_w153/dream_breaker.json': '7509576bf38bb5dbc5042a1b3cb69247bd08260eaafa3cba69b8a3a3aa594a19',
 'src/main/resources/assets/destiny/items/weapon_aim_w70/dream_breaker.json': '9c2fe78b37bfe96b43066d9f5c0568aa3c3edfc3b7cc707c5b4a493f66f79055'}

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
    """Four connected canonical cell solids; cuff/hose/ropes remain receiver cradle.
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
    """Read root inputs; return absolute Path -> bytes without filesystem writes."""
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
        raise ValueError("W178 authored source changed; re-audit before generation")
    authored = {}
    for node in ast.parse(raw[AUTHORED_SOURCE]).body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in {"KEYS", "GRIP", "MAG_ANCHOR", "CELL_NAMES"}):
            authored[node.targets[0].id] = ast.literal_eval(node.value)
    if authored != {"KEYS": KEYS, "GRIP": GRIP, "MAG_ANCHOR": MAG_ANCHOR, "CELL_NAMES": CELL_NAMES}:
        raise ValueError("W178 knots, pivots or cell identity changed")
    if sha(raw[RIG]) != RIG_SHA256 or sha(raw[SOURCE_REVIEW]) != SOURCE_REVIEW_SHA256:
        raise ValueError("Install the fresh master-reviewed W217 normalized source/report")
    source, item = json.loads(raw[SOURCE]), json.loads(raw[ITEM])
    twohand = json.loads(raw[TWOHAND])["display"]
    profile, rig = json.loads(raw[PROFILE]), json.loads(raw[RIG])
    report, old = json.loads(raw[SOURCE_REVIEW]), json.loads(raw[AUTHORED_MANIFEST])
    reference = json.loads(raw[AUTHORED_REVIEW])
    contacts = json.loads(raw[CONTACTS])["weapons"]["dream_breaker"]
    elements = source["elements"]
    if (len(elements) != 186
            or tuple(i for i,e in enumerate(elements) if e["name"] in CELL_NAMES) != MOVING
            or tuple(elements[i]["name"] for i in MOVING) != CELL_NAMES
            or old["sourceGeometryFileSha256"] != SOURCE_SHA256
            or old["keyframes"] != json.loads(encode(KEYS))
            or old["partitionIndices"]["magazine"] != list(MOVING)
            or reference.get("inspectedActualFrames") is not True):
        raise ValueError("Dream Breaker authored geometry/UV/partition/reference drift")
    rule = next(r for r in json.loads(raw[SURFACE_MAP])["targets"]
                if r["path"] == "assets/destiny/models/weapon/fusion_rifle/dream_breaker.json")
    if (rule["replacement"] != "assets/destiny/models/weapon_surface_w123/dream_breaker.json"
            or rule["replacementSha256"] != SOURCE_SHA256):
        raise ValueError("Selected Dream Breaker surface mapping changed")
    if (profile.get("schemaVersion") != 1 or profile.get("weapon") != "dream_breaker"
            or profile.get("sourceAction") != RIG_ACTION
            or profile.get("sourceRig") != EXPECTED_SOURCE_RIG
            or profile.get("framing") != EXPECTED_FRAMING):
        raise ValueError("W217 profile/source/full-chain/framing drift")
    overrides = profile.get("contacts", {})
    reload = {**contacts["reload"], **overrides.get("reload", {})}
    if (set(overrides) != {"reload"}
            or set(overrides["reload"]) != {"rigAction", "partHint", "policy", "gripWindow"}
            or reload.get("rigAction") != RIG_ACTION or reload.get("partHint") != "magazine"
            or reload.get("policy") != "magazine"
            or reload.get("gripWindow") != [.05, .20, .78, .84]
            or contacts["family"] != "fusion_rifle"
            or contacts["canonicalModel"] != "destiny:weapon_surface_w123/dream_breaker"
            or contacts["right"] != {"position": [8.,8.05,9.1], "rotation": [-26.,0.,0.]}
            or contacts["left"] != {"position": [7.8,10.08,-4.4], "rotation": [0.,90.,-85.]}
            or reload.get("contact") != [7.15,7.3,3.57]
            or reload.get("rotation") != [0.,0.,0.]):
        raise ValueError("Rest contacts or authored .84 cell-seat release changed")
    if (rig.get("group") != "fusion_rifle_04669cdb" or rig.get("fallback") is not False
            or "dream_breaker" not in rig["weapons"] or rig.get("cameraExported") is not False
            or rig.get("space") != "armature_object"
            or rig.get("w217Source61", {}).get("exporterSha256") != EXPORTER_SHA256
            or rig["w217Source61"].get("reloadSamples") != SAMPLES
            or rig["w217Source61"].get("cameraExported") is not False):
        raise ValueError("Expected fresh master original shoulder-chain source")
    action = rig["actions"][RIG_ACTION]
    if (action["action"] != RIG_ACTION_NAME or len(action["frames"]) != SAMPLES
            or (action["start"], action["end"]) != (1,100)):
        raise ValueError("Expected original ADD3 action61 samples over1..100")
    joints = {"weapon", "leftShoulder", "leftElbow", "leftWrist",
              "rightShoulder", "rightElbow", "rightWrist"}
    for i,frame in enumerate(action["frames"]):
        if (not joints <= frame["joints"].keys()
                or abs(frame["progress"]-i/INTERVALS) > 1e-12
                or abs(frame["frame"]-(1+99*i/INTERVALS)) > 1e-10):
            raise ValueError("Expected uniformly evaluated original full shoulder chains")
    reviewed = report["groups"][rig["group"]]
    reviewed_action = reviewed["actions"][RIG_ACTION]
    if (report.get("allInputsUnchanged") is not True
            or report.get("exporterSha256") != EXPORTER_SHA256
            or reviewed["objects"] != [{"name": "Armature", "type": "ARMATURE"}]
            or reviewed_action["action"] != RIG_ACTION_NAME
            or reviewed_action["slot"] != "OBSlot"
            or reviewed_action["sourceFrameRange"] != [1,100]
            or reviewed_action["maxExistingCacheJointAbsError"] != 0):
        raise ValueError("Fresh original Blender report changed")
    for name in ("sourceBlendSha256", "sourceMapSha256", "boneMapSha256"):
        if rig.get(name) != EXPECTED_SOURCE_RIG[name]:
            raise ValueError("Original source provenance changed: " + name)
    geometries, output = partition(source), {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError("Output outside W217 Dream Breaker namespace")
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
        raise ValueError("Weapon plus full-chain arm reserve exceeds1000 elements")
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W217", "weapon": "dream_breaker",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0, "firstPersonContexts": list(FP),
        "thresholdEncoding": "float32(i/60), matching master runtime grid60",
        "curve": "C1 weighted harmonic PCHIP; zero endpoints, holds and extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "magazineAnchor": MAG_ANCHOR,
        "authoredTimingSource": str(AUTHORED_SOURCE),
        "magazineNeutralSeatedProgress": .84, "reloadGripWindow": reload["gripWindow"],
        "normalizedPhases": old["normalizedPhases"], "reference": reference["url"],
        "referencePolicy": "W178 same-weapon DFP footage provenance retained; worker viewed archived storyboard, did not reopen video.",
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": len(elements), "partElements": counts, "weaponElements": weapon_count,
        "bodyElements": counts["body"], "movingElements": counts["magazine"],
        "canonicalWeaponElements": canonical_count, "endpointAssembledElements": canonical_count,
        "elementLimit": 1000, "ordinaryArmElementReserve": ARM_ELEMENT_RESERVE,
        "candidateReloadWithArmsEstimate": weapon_count+ARM_ELEMENT_RESERVE,
        "candidateKnownCanonicalWithArmsEstimate": canonical_count+ARM_ELEMENT_RESERVE,
        "integratedAllRouteMaximumMeasured": False,
        "budgetBasis": "186 reload weapon+448 ordinary arm reserve=634; native247+448=695. Master measures all composed routes including ADS/inspect.",
        "movingIndices": list(MOVING), "movingNames": list(CELL_NAMES),
        "partitionIndices": old["partitionIndices"], "partitionRationale": old["partitionRationale"],
        "addedElements": 0, "triangleAdapterElements": 0,
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
        "motionAuthorship": "All11 W178 Dream Breaker knots, exact cell hold.43..54, anchors, rigid carrier algebra, canonical solids/UV and .84seat preserved. Only interpolation changes. Shared fusion original armature is not weapon-exclusive. Master binds original shoulder/elbow/wrist chain to ordinary-length fingerless skin arms; weapon/cell path and contacts remain authored.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "timingPolicy": "Retain magazine6/reload46ticks/charge667ms/burst7/cadence13ticks, ammo lifecycle and audio; source30fps frames1..100 do not retime gameplay.",
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "packFiles": len(output), "totalReturnedFiles": len(output)+1,
        "staticParts": len(PARTS), "parentDisplayChildren": SAMPLES*len(PARTS)*len(GRIPS),
        "inputSha256": {str(path):sha(data) for path,data in raw.items()},
        "outputSha256": {str(path.relative_to(root)):sha(data) for path,data in output.items()},
        "limitations": [
            "Master evaluated original Blender; worker read fresh report/export and viewed actual ADD3 chain sheet plus legacy W178 storyboard.",
            "ARMATURE only: no recovered weapon mesh/camera/finger IK; contact and hidden cell path remain authored approximations.",
            "61 static poses do not establish native continuous60fps interpolation.",
            "Attachment releases.78..84 by same-weapon authored seat; neutral cell offset holds.84..1.",
            "Effective framing/rest contacts retained; fixed receiver/grip/triggerguard/cradle geometry unchanged.",
            "Master owns all-route measured budget, materialization, FIRST feedback, same-worker response and SECOND. Native acceptance pending."]})
    if set(output) != {root/path for path in allowed}:
        raise ValueError("Incomplete W217 Dream Breaker output mapping")
    return output
