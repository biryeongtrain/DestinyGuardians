#!/usr/bin/env python3
"""W215 Apostate: W185 authored reload, 61-pose weighted-harmonic PCHIP bank.

Pure stdlib: importing and generate(root=ROOT) perform no writes. Master owns
fresh source61 FK, action binding, arms, output materialization and FIRST/SECOND.
Weapon motion stays authored; no recovered mesh, camera or finger IK is claimed.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
ASSET = Path("src/main/resources/assets/destiny")
A = ASSET
ART = Path("art/weapons/w215/apostate")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w215_apostate.py")
AUTHORED_SOURCE = Path("scripts/generate_reload_w185_apostate.py")
SOURCE = ASSET / "models/weapon_surface_w123/apostate.json"
NATIVE = ASSET / "models/weapon/sniper_rifle/apostate.json"
TWOHAND = ASSET / "models/weapon/sniper_rifle/apostate_twohand.json"
ITEM = ASSET / "items/weapon/apostate.json"
TEXTURE = ASSET / "textures/item/weapon/w123/apostate.png"
CONTACTS = Path("art/weapons/w201/contacts.json")
RIG = Path("art/weapons/w205/rigs/sniper_rifle_c96fceca.json")
DESIGN = Path("art/weapons/w123/apostate/design.json")
SURFACE_MAP = Path("src/main/resources/weapon_surface_w123/manifest.json")
FRAMING = Path("art/weapons/w205/first-person-framing.json")
KEY = "weapon_reload_w215_apostate/apostate"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine")
GRIPS = ("native", "twohand")
INTERVALS = 60
SAMPLES = INTERVALS + 1
RIG_ACTION = "80A8A17D"
ARM_ELEMENT_RESERVE = 4 * 112
MOVING = (29, 30, 31, 32)
SOURCE_SHA256 = "846daf98a5efa055722fcac68d6020636aa1ed3f8c428c4870ada7eee8bd4f99"
AUTHORED_SHA256 = "d7a49e2a3ac792422098b5d3f6ec2268587900409d7d27cdb6e31bceadfe2db0"
GRIP = (8.0, 8.6, 8.4)
MAGAZINE_ANCHOR = (8.0, 8.6, 3.1)
MAGAZINE_NAMES = ('magazine/main', 'magazine/toe', 'magazine/heel', 'magazine/base')
KEYS = ((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.1, (10, -3, -4), (0.1, -0.05, 0.05), (0, 0, 0)), (0.22, (78, -6, -7), (0.4, 0.05, 0.2), (0, 0, 0)), (0.34, (88, -7, -9), (0.55, 0.1, 0.22), (-0.1, -3.9, 0.15)), (0.46, (87, -6, -8), (0.55, 0.1, 0.22), (-0.45, -4.3, -0.4)), (0.58, (86, -5, -7), (0.5, 0.08, 0.2), (0.1, -1.55, 0.12)), (0.68, (84, -4, -6), (0.45, 0.06, 0.18), (0, 0.06, 0)), (0.74, (83, -4, -6), (0.42, 0.04, 0.16), (0, 0, 0)), (0.84, (48, -2, -3), (0.22, -0.03, 0.08), (0, 0, 0)), (0.94, (11, -1, -1), (0.04, -0.04, 0.01), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/apostate.json': '846daf98a5efa055722fcac68d6020636aa1ed3f8c428c4870ada7eee8bd4f99', 'src/main/resources/assets/destiny/textures/item/weapon/w123/apostate.png': 'aa888e15fe0f9e4cb0a858971fade9cb60689fec40acb1fcfdead6cc6bd59b9e', 'src/main/resources/assets/destiny/items/weapon/apostate.json': 'dfc64a7c51cbd2a4a11065858a9127a92585b6f7702cab4240611933441c73f3', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate_inspect_twohand.json': '1d8230f62d97728f2167b50d54909a183f499a930212a070646f39e4162a4a0f', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate_inspect.json': 'ce797223b0d95370e770042bdf38172d2b2d46aa4fba277251a59773e1f63fc8', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate.json': 'b5a2400a8cbe5d281783dd5f4850ac6d3f5847aa84db16b029288ec9c0b63923', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate_ads.json': '283bd4a366dacf7853636881febca94454176e14c5397720ac5704cffb6465d4', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate_twohand.json': 'a715871885be1b1c0a9e55aa512c16a70a0308dc426134a9cc9e9028cd1ced72', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate_ads_twohand.json': '1bb68509bf972213fd6f9e7bcd652d80d1b3d01f095731b4f2ebb36d3098b339'}

# Exact W185 knots, near-vertical lift, low exchange and .68 seat overtravel.

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
    # The full dark incoming magazine/upper neck is visible n9939. Add only
    # the short seated portion hidden in socket28, retaining the original atlas.
    shaft=copy.deepcopy(source['elements'][29])
    shaft.update(name='magazine_shaft_upper',**{'from':[7.57,8.55,1.30],'to':[8.43,9.10,4.90]})
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
    # Four canonical magazine solids and small upper shaft move as one rigid payload.
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
    paths = {ASSET / f"models/{KEY}_{part}.json" for part in PARTS}
    paths.update(ASSET / f"models/{KEY}_{i:02}_{part}_{grip}.json"
                 for i in range(SAMPLES) for part in PARTS for grip in GRIPS)
    return paths | {ASSET / f"items/{KEY}.json", MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Return absolute Path -> bytes only. Read inputs under root; never write."""
    root = Path(root).resolve()
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE, PROFILE,
        GENERATOR, AUTHORED_SOURCE, CONTACTS, RIG, DESIGN, SURFACE_MAP, FRAMING,
        *(Path(p) for p in PINS)]))
    raw = {path: (root / path).read_bytes() for path in inputs}
    if sha(raw[SOURCE]) != SOURCE_SHA256 or sha(raw[AUTHORED_SOURCE]) != AUTHORED_SHA256:
        raise ValueError("Accepted W138 geometry or W185 authored source drift; re-audit")
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError("Canonical/gameplay/audio input drift: " + path)
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    contacts = json.loads(raw[CONTACTS])["weapons"]["apostate"]
    elements = source["elements"]
    if (len(elements) != 114 or
            tuple(i for i, e in enumerate(elements) if is_payload(e)) != MOVING or
            tuple(elements[i]["name"] for i in MOVING) != MAGAZINE_NAMES or
            elements[28]["name"] != "magazine/socket"):
        raise ValueError("Apostate whole-magazine partition drift")
    design = json.loads(raw[DESIGN])
    if (design["revision"] != "W138" or
            tuple(p["geometry"]["name"] for p in design["parts"]["full"]
                  if p["geometry"]["name"] in MAGAZINE_NAMES) != MAGAZINE_NAMES):
        raise ValueError("W138 semantic magazine provenance drift")
    rule = next(r for r in json.loads(raw[SURFACE_MAP])["targets"]
                if r["path"] == "assets/destiny/models/weapon/sniper_rifle/apostate.json")
    if (rule["replacement"] != "assets/destiny/models/weapon_surface_w123/apostate.json"
            or rule["replacementSha256"] != SOURCE_SHA256):
        raise ValueError("Selected Apostate surface mapping drift")
    if profile.get("schemaVersion") != 1 or profile.get("weapon") != "apostate":
        raise ValueError("Invalid W215 Apostate profile")
    settings = profile["framing"]
    reload = {**contacts["reload"], **profile.get("contacts", {}).get("reload", {})}
    if (settings.get("sourceFullChain") is not True or settings.get("keepMeshSupport") is not True
            or settings.get("hideSupportAtRest") is not False
            or profile.get("sourceAction") != RIG_ACTION
            or reload.get("rigAction") != RIG_ACTION or reload.get("partHint") != "magazine"
            or reload.get("policy") != "magazine"):
        raise ValueError("Original-chain/contact policy drift")
    window = reload.get("gripWindow")
    if not (isinstance(window, list) and len(window) == 4
            and 0 <= window[0] < window[1] <= window[2] < window[3] <= 1):
        raise ValueError("Invalid Apostate magazine attachment window")
    if (rig.get("group") != "sniper_rifle_c96fceca" or rig.get("fallback") is not False
            or "apostate" not in rig["weapons"]):
        raise ValueError("Expected original Apostate source rig")
    action = rig["actions"][RIG_ACTION]
    if len(action["frames"]) != SAMPLES or (action["start"], action["end"]) != (1, 111):
        raise ValueError("Master must bind the fresh61 original action, frames1..111")
    joints = {"weapon", "leftShoulder", "leftElbow", "leftWrist",
              "rightShoulder", "rightElbow", "rightWrist"}
    if any(not joints <= frame["joints"].keys() or abs(frame["progress"]-i/INTERVALS) > 1e-12
           for i, frame in enumerate(action["frames"])):
        raise ValueError("Expected uniformly evaluated full shoulder chains")
    for key in ("sourceBlendSha256", "sourceMapSha256", "boneMapSha256"):
        if rig.get(key) != profile["sourceRig"][key]:
            raise ValueError("Reviewed original source hash changed: " + key)
    geometries = partition(source)
    output = {}
    allowed = expected_output_paths()

    def emit(path, value):
        if path not in allowed:
            raise ValueError("Output outside W215 Apostate ownership")
        output[root / path] = encode(value)

    for part in PARTS:
        emit(ASSET / f"models/{KEY}_{part}.json", geometries[part])
    entries = []
    for frame in range(SAMPLES):
        progress = frame / INTERVALS
        for part in PARTS:
            for grip in GRIPS:
                emit(ASSET / f"models/{KEY}_{frame:02}_{part}_{grip}.json", {
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
            "fallback": {"type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data", "index": 1,
                         "entries": entries, "fallback": copy.deepcopy(item["model"])}}}],
        "fallback": copy.deepcopy(item["model"])}
    emit(ASSET / f"items/{KEY}.json", wrapper)
    counts = {part: len(geo["elements"]) for part, geo in geometries.items()}
    weapon_count = sum(counts.values())
    canonical_count = len(json.loads(raw[NATIVE])["elements"])
    if max(weapon_count, canonical_count) + ARM_ELEMENT_RESERVE > 1000:
        raise ValueError("Weapon plus ordinary full-chain arm reserve exceeds 1000 elements")
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W215", "weapon": "apostate",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0, "firstPersonContexts": list(FP),
        "thresholdEncoding": "exact float32(i/60), matching master runtime grid60",
        "curve": "C1 PCHIP, weighted harmonic tangents; zero endpoints/holds/extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "magazineAnchor": MAGAZINE_ANCHOR,
        "authoredTimingSource": str(AUTHORED_SOURCE),
        "magazineSeatOvertravelProgress": .68, "magazineNeutralSeatedProgress": .74,
        "reloadGripWindow": window,
        "normalizedPhases": {"lift": [0,.22], "withdraw": [.22,.34],
            "lowerExchange": [.34,.46], "incoming": [.46,.58], "seat": [.58,.68],
            "release": [.68,.74], "authoredRecovery": [.74,1]},
        "reference": {"url": "https://www.youtube.com/watch?v=h835sF3Ouvo",
            "creator": "Aztecross", "selectedSeconds": [164.8,166.1],
            "policy": "W185 retained footage provenance; worker did not re-open video. Rift interrupts recovery; lowering remains authored."},
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": len(elements), "partElements": counts, "weaponElements": weapon_count,
        "bodyElements": counts["body"], "movingElements": counts["magazine"],
        "canonicalWeaponElements": canonical_count, "endpointAssembledElements": canonical_count,
        "elementLimit": 1000, "ordinaryArmElementReserve": ARM_ELEMENT_RESERVE,
        "candidateReloadWithArmsEstimate": weapon_count+ARM_ELEMENT_RESERVE,
        "candidateKnownCanonicalWithArmsEstimate": canonical_count+ARM_ELEMENT_RESERVE,
        "integratedAllRouteMaximumMeasured": False,
        "budgetBasis": "115 reload weapon +448 estimated four classic arm segments=563; native236+448=684. Master measures every materialized route including ADS/inspect and arms under1000.",
        "movingIndices": list(MOVING), "movingNames": list(MAGAZINE_NAMES),
        "partitionIndices": {part: [i for i,e in enumerate(elements) if is_payload(e)==(part=="magazine")]
                             for part in PARTS},
        "partitionRationale": "Four whole-magazine solids29..32 plus the existing W185 hidden upper shaft move rigidly. Socket28, receiver, fore-end, trigger, stock, optics and all110 original body solids remain fixed.",
        "addedElements": 1, "newElementsRelativeToW185": 0, "triangleAdapterElements": 0,
        "reloadOnlyGeometry": {"elements": reload_shaft(source), "count": 1,
            "policy": "Preserve W185 authored upper shaft and original magazine/main face UV; no recovered hidden interface claim."},
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {part: sha(encode(geo["elements"])) for part,geo in geometries.items()},
        "canonicalElementsAndUVPreserved": True, "geometryAndUVPreserved": True,
        "hipEndpoints": [0, INTERVALS], "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Exact canonical item graph at negative inactive progress, endpoints, overshoot and non-FP; ADS/inspect precede reload dispatch, preserving native/twohand branches.",
        "sourceGroup": rig["group"], "sourceAction": RIG_ACTION, "rigAction": RIG_ACTION,
        "partHint": "magazine", "policy": "magazine", "rigActionName": action["action"],
        "sourceActionSourceRange": [action["start"],action["end"]],
        "sourceRigSamples": len(action["frames"]), "sourceFullChain": True,
        "sourceCameraRecovered": False, "sourceEvidence": profile.get("evidence", []),
        "motionAuthorship": "Exact W185 knots, holds, rigid transform algebra and reload-only shaft; interpolation alone becomes weighted-harmonic PCHIP. Master attaches original weapon-relative shoulder/elbow/wrist FK with ordinary fingerless skin arms and no attenuation.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "timingPolicy": "Preserve6 rounds,140RPM,54tick full reload, existing ammo lifecycle and all audio; source30fps/action length does not retime gameplay.",
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "packFiles": len(output), "totalReturnedFiles": len(output)+1,
        "staticParts": len(PARTS), "parentDisplayChildren": SAMPLES*len(PARTS)*len(GRIPS),
        "inputSha256": {str(path): sha(data) for path,data in raw.items()},
        "outputSha256": {str(path.relative_to(root)): sha(data) for path,data in output.items()},
        "limitations": [
            "Master evaluated original Blender; worker read the fresh record/matrices and viewed the bone-only chain sheet.",
            "ARMATURE only; no recovered mesh, camera, fingers or IK. Mesh contacts and weapon part path remain authored.",
            "61 poses do not prove native continuous60fps interpolation.",
            "Attachment release .58..68 protects seat overtravel; neutral magazine holds .74..1. FIRST must verify contact and recovery.",
            "Master binds original61 action, W215 framing loader, runtime60grid and full-chain normal-length arms; no stretch, source damping, hidden support or camera corrections added.",
            "Integrated all-route budget, FIRST image-backed review/correction and SECOND remain pending."]})
    if set(output) != {root/path for path in allowed}:
        raise ValueError("Incomplete W215 Apostate output mapping")
    return output
