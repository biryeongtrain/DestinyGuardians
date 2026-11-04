#!/usr/bin/env python3
"""W214 Bite of the Fox: original full-chain integration candidate, 61 weapon poses.

Pure stdlib; import and generate(root=ROOT) return data without writing. Master
owns source61/shoulders, skin arms, materialization, runtime and Vision. W177
weapon motion remains authored; no recovered mesh/camera/finger IK is claimed.
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
ART = Path("art/weapons/w214/bite_of_the_fox")
PROFILE = ART / "profile.json"
MANIFEST = ART / "manifest.json"
GENERATOR = Path("scripts/generate_reload_w214_bite_of_the_fox.py")
AUTHORED_SOURCE = Path("scripts/generate_reload_w177_bite_of_the_fox.py")
SOURCE = ASSET / "models/weapon_surface_w123/bite_of_the_fox.json"
NATIVE = ASSET / "models/weapon/sniper_rifle/bite_of_the_fox.json"
TWOHAND = ASSET / "models/weapon/sniper_rifle/bite_of_the_fox_twohand.json"
ITEM = ASSET / "items/weapon/bite_of_the_fox.json"
TEXTURE = ASSET / "textures/item/weapon/w123/bite_of_the_fox.png"
CONTACTS = Path("art/weapons/w201/contacts.json")
RIG = Path("art/weapons/w205/rigs/sniper_rifle_f22b9e87.json")
DESIGN = Path("art/weapons/w123/bite_of_the_fox/design.json")
SURFACE_MAP = Path("src/main/resources/weapon_surface_w123/manifest.json")
FRAMING = Path("art/weapons/w205/first-person-framing.json")
REFERENCE = Path("art/weapons/w177/bite_of_the_fox/motion-reference.json")
KEY = "weapon_reload_w214_bite_of_the_fox/bite_of_the_fox"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine")
INTERVALS = 60
SAMPLES = 61
RIG_ACTION = "80A8A140"
# Audited literal W177 constants, never imported or executed.
MOVING = (51, 52, 53)
NAMES = ('magazine', 'magazine_floor', 'magazine_brass_catch')
GRIP = (8.0, 8.03, 8.35)
MAG_ANCHOR = (8.0, 8.31, 4.875)
KEYS = ((0.0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.08, (9, -3, -10), (0.05, 0.06, 0.05), (0, 0, 0)), (0.16, (19, -6, -25), (0.14, 0.18, 0.12), (0, -0.2, 0)), (0.24, (22, -8, -32), (0.18, 0.22, 0.15), (-0.25, -2.4, 0.2)), (0.32, (25, -8, -38), (0.18, 0.25, 0.16), (-0.65, -3.6, 0.55)), (0.4, (26, -7, -36), (0.12, 0.25, 0.12), (-0.3, -1.6, 0.2)), (0.46, (24, -6, -33), (0.08, 0.2, 0.1), (0, 0, 0)), (0.54, (16, 2, -15), (-0.05, 0.08, 0.08), (0, 0, 0)), (0.62, (2, 12, 22), (-0.18, -0.1, 0.05), (0, 0, 0)), (0.72, (8, 10, 20), (-0.12, -0.08, 0.1), (0, 0, 0)), (0.8, (14, 8, 12), (-0.06, 0.05, 0.1), (0, 0, 0)), (0.88, (-5, 5, 5), (-0.02, -0.2, 0.05), (0, 0, 0)), (0.95, (-2, 2, 2), (0, -0.08, 0.02), (0, 0, 0)), (1.0, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
SOURCE_SHA256 = 'f80083332b3e0ee8903bc825287a254cd4cead6c9d8605896f51ce580b292c2a'
PINS = {'src/main/resources/assets/destiny/models/weapon/sniper_rifle/bite_of_the_fox.json': '00dce3691476617a9a0e9d98e7c18cc486a0c80f637a8ec6ad101cc76a261154', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/bite_of_the_fox_twohand.json': '217e9042fe3ccfc1b281d7d522a94b4535f58c500ed04f336371010dfb496b11', 'src/main/resources/assets/destiny/items/weapon/bite_of_the_fox.json': '620d970a89d977772f808425fff90db3949be88cb11007e7fa5dea9215e6bb54', 'src/main/resources/assets/destiny/textures/item/weapon/w123/bite_of_the_fox.png': '747f936b662b4c4e8857ee57142d35936a21df1dd6cd1dd19c7b66223836279b', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b'}
AUTHORED_SHA256 = '450f5e87f649585755f8d4138df2ef212257c29d7ba2bcf8eae94fdd0feb3d76'

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

def add(a, b):
    return [x+y for x, y in zip(a, b)]

def sub(a, b):
    return [x-y for x, y in zip(a, b)]

def mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def vec(m, v):
    return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]

def transpose(m):
    return list(map(list, zip(*m)))

def xyz(angles):
    x, y, z = map(math.radians, angles)
    a, b, c, d, e, f = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return [[c*e, -c*f, d], [b*d*e+a*f, -b*d*f+a*e, -b*c],
            [-a*d*e+b*f, a*d*f+b*e, a*c]]

def euler(m):
    y = math.asin(max(-1., min(1., m[0][2])))
    if abs(math.cos(y)) > 1e-8:
        x, z = math.atan2(-m[1][2], m[2][2]), math.atan2(-m[0][1], m[0][0])
    else:
        x, z = math.atan2(m[2][1], m[1][1]), 0
    return [round(math.degrees(v), 9) for v in (x, y, z)]

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in ('native', 'twohand'):
        raise ValueError('Unknown Bite of the Fox part or grip')
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8))
    anchor=sub(MAG_ANCHOR,(8,8,8))
    # Place the unchanged magazine anchor at its body-carried position plus
    # source-local withdrawal, then subtract its rotated child-space anchor.
    # This is translation only; no recentering or extra magazine spin.
    local=(sub(add(h,vec(body,add(sub(anchor,h),offset))),vec(body,anchor))
           if part=='magazine' else sub(h,vec(body,h)))
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


def expected_output_paths():
    paths = {ASSET / f"models/{KEY}_{part}.json" for part in PARTS}
    paths.update(ASSET / f"models/{KEY}_{i:02}_{part}_{grip}.json"
                 for i in range(SAMPLES) for part in PARTS for grip in ("native", "twohand"))
    return paths | {ASSET / f"items/{KEY}.json", MANIFEST}


def generate(root=ROOT) -> dict[Path, bytes]:
    """Return only absolute output Path -> bytes; all inputs resolve under root."""
    root = Path(root).resolve()
    variants = [ASSET / f"models/weapon/sniper_rifle/bite_of_the_fox{s}.json"
                for s in ("_ads", "_ads_twohand", "_inspect", "_inspect_twohand")]
    inputs = list(dict.fromkeys([SOURCE, NATIVE, TWOHAND, ITEM, TEXTURE,
        PROFILE, GENERATOR, AUTHORED_SOURCE, CONTACTS, RIG, DESIGN, SURFACE_MAP,
        FRAMING, REFERENCE, *variants, *(Path(p) for p in PINS)]))
    raw = {p: (root / p).read_bytes() for p in inputs}
    if sha(raw[SOURCE]) != SOURCE_SHA256 or sha(raw[AUTHORED_SOURCE]) != AUTHORED_SHA256:
        raise ValueError("Accepted W134/W177 source drift; re-audit")
    for path, digest in PINS.items():
        if sha(raw[Path(path)]) != digest:
            raise ValueError("Canonical/gameplay/audio input drift: " + path)
    source = json.loads(raw[SOURCE])
    twohand = json.loads(raw[TWOHAND])["display"]
    item = json.loads(raw[ITEM])
    profile = json.loads(raw[PROFILE])
    rig = json.loads(raw[RIG])
    contacts = json.loads(raw[CONTACTS])["weapons"]["bite_of_the_fox"]
    elements = source["elements"]
    if len(elements) != 112 or [elements[i]["name"] for i in MOVING] != list(NAMES):
        raise ValueError("W134 magazine partition drift")
    design = json.loads(raw[DESIGN])
    if (design["revision"] != "W134" or
            [p["geometry"]["name"] for p in design["parts"]["full"]
             if p["group"] == "magazine"] != list(NAMES)):
        raise ValueError("Semantic magazine provenance drift")
    rule = next(r for r in json.loads(raw[SURFACE_MAP])["targets"]
                if r["path"] == "assets/destiny/models/weapon/sniper_rifle/bite_of_the_fox.json")
    if (rule["replacement"] != "assets/destiny/models/weapon_surface_w123/bite_of_the_fox.json"
            or rule["replacementSha256"] != SOURCE_SHA256):
        raise ValueError("Selected surface mapping drift")
    if profile.get("schemaVersion") != 1 or profile.get("weapon") != "bite_of_the_fox":
        raise ValueError("Invalid W214 profile")
    framing = profile["framing"]
    reload = {**contacts["reload"], **profile.get("contacts", {}).get("reload", {})}
    if (framing.get("sourceFullChain") is not True or framing.get("keepMeshSupport") is not True
            or framing.get("hideSupportAtRest") is not False
            or reload.get("rigAction") != RIG_ACTION or reload.get("partHint") != "magazine"
            or reload.get("policy") != "magazine"):
        raise ValueError("Original-chain/contact policy drift")
    start, attached, release, end = reload.get("gripWindow", [.05, .20, .78, .98])
    if not 0 <= start < attached <= release < end <= 1:
        raise ValueError("Invalid magazine gripWindow")
    if (rig.get("group") != "sniper_rifle_f22b9e87" or rig.get("fallback") is not False
            or "bite_of_the_fox" not in rig["weapons"]):
        raise ValueError("Expected shared original sniper source")
    action = rig["actions"][RIG_ACTION]
    if len(action["frames"]) != SAMPLES or (action["start"], action["end"]) != (1, 102):
        raise ValueError("Master must seed original61 source range first")
    joints = {"weapon", "leftShoulder", "leftElbow", "leftWrist",
              "rightShoulder", "rightElbow", "rightWrist"}
    if any(not joints <= f["joints"].keys() or abs(f["progress"]-i/INTERVALS) > 1e-12
           for i, f in enumerate(action["frames"])):
        raise ValueError("Expected uniformly evaluated full shoulder chains")
    if rig.get("sourceBlendSha256") != profile["sourceRig"]["sourceBlendSha256"]:
        raise ValueError("Reviewed original source hash changed")
    geometries = {}
    for part in PARTS:
        geo = {k: copy.deepcopy(v) for k, v in source.items() if k not in ("elements", "display")}
        geo["elements"] = [copy.deepcopy(e) for i, e in enumerate(elements)
                           if (i in MOVING) == (part == "magazine")]
        geometries[part] = geo
    output = {}
    allowed = expected_output_paths()
    def emit(path, value):
        if path not in allowed:
            raise ValueError("Output outside W214 Bite of the Fox ownership")
        output[root / path] = encode(value)
    for part in PARTS:
        emit(ASSET / f"models/{KEY}_{part}.json", geometries[part])
    entries = []
    for frame in range(SAMPLES):
        progress = frame / INTERVALS
        for part in PARTS:
            for grip in ("native", "twohand"):
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
    counts = {p: len(g["elements"]) for p, g in geometries.items()}
    weapon_count = sum(counts.values())
    canonical_count = len(json.loads(raw[NATIVE])["elements"])
    if weapon_count > 1000:
        raise ValueError("Weapon-only element limit exceeded")
    emit(MANIFEST, {
        "schemaVersion": 1, "stage": "W214", "weapon": "bite_of_the_fox",
        "generator": str(GENERATOR), "generatorSha256": sha(raw[GENERATOR]),
        "itemModel": f"destiny:{KEY}", "frames": SAMPLES, "intervals": INTERVALS,
        "progressFloatIndex": 1, "gripFlagIndex": 0, "firstPersonContexts": list(FP),
        "thresholdEncoding": "exact float32(i/60), runtime float quantization",
        "curve": "C1 PCHIP, weighted harmonic tangents; zero endpoints/holds/extrema",
        "keyframes": KEYS, "gripPivot": GRIP, "magazineAnchor": MAG_ANCHOR,
        "authoredTimingSource": str(AUTHORED_SOURCE), "magazineSeatedProgress": .46,
        "gripWindow": reload.get("gripWindow"),
        "normalizedPhases": {"rifleRaiseAndCant": [0,.16], "underReceiverWithdrawal": [.16,.32],
            "replacementApproach": [.32,.46], "seatedSettle": [.46,.54],
            "receiverGestureProxy": [.54,.80], "recover": [.80,1]},
        "reference": json.loads(raw[REFERENCE])["url"],
        "sourceObservedSeconds": json.loads(raw[REFERENCE])["selectedSeconds"],
        "sourceGeometryPath": str(SOURCE), "sourceGeometryFileSha256": sha(raw[SOURCE]),
        "sourceElements": len(elements), "partElements": counts, "weaponElements": weapon_count,
        "canonicalWeaponElements": canonical_count, "elementLimit": 1000,
        "candidateArmElementsEstimate": 448, "candidateReloadWithArmsEstimate": weapon_count+448,
        "candidateKnownCanonicalWithArmsEstimate": canonical_count+448,
        "integratedAllRouteMaximumMeasured": False,
        "budgetBasis": "112 split weapon + estimated448 classic arm elements =560; known canonical223 +448 =671. These are estimates; master must measure every integrated route including ADS/inspect/arms under1000.",
        "movingIndices": list(MOVING), "movingNames": list(NAMES), "addedElements": 0,
        "partitionRationale": "109 fixed +3 connected magazine solids51..53 forward of trigger; guard57..60, grip54..56, bolt49/50 and all other geometry remain body. No independent bolt motion invented.",
        "sourceElementsAndUVSha256": sha(encode(elements)),
        "partElementsAndUVSha256": {p: sha(encode(g["elements"])) for p,g in geometries.items()},
        "geometryAndUVUnchanged": True, "geometryAndUVPreserved": True,
        "hipEndpoints": [0, INTERVALS], "endpointDisplayExact": True, "fallbackModelExact": True,
        "fallback": "Exact canonical graph at negative inactive progress, endpoints and non-FP. ADS/inspect precede reload dispatch; both grip branches preserved.",
        "sourceGroup": rig["group"], "rigAction": RIG_ACTION, "partHint": "magazine",
        "rigActionName": action["action"], "sourceActionSourceRange": [action["start"],action["end"]],
        "sourceRigSamples": len(action["frames"]), "sourceFullChain": True,
        "sourceActionWeaponExclusive": False, "sourceCameraRecovered": False,
        "sourceEvidence": profile.get("evidence", []),
        "motionAuthorship": "Exact W177 authored knots/holds, partition and rigid transform algebra; only scalar interpolation changes. Master attaches source weapon-relative FK, ordinary full-chain fingerless player-skin arms; no source attenuation.",
        "gameplayTimingChanged": False, "mechanicsOrAudioChanged": False,
        "nativeGameplayVerified": False, "nativeVisibilityAccepted": False,
        "packFiles": len(output), "totalReturnedFiles": len(output)+1,
        "staticParts": len(PARTS), "parentDisplayChildren": SAMPLES*len(PARTS)*2,
        "inputSha256": {str(p): sha(v) for p,v in raw.items()},
        "outputSha256": {str(p.relative_to(root)): sha(v) for p,v in output.items()},
        "limitations": [
            "Master evaluated Blender; worker read its record and viewed the bone-only source sheet.",
            "Shared sniper variants, not weapon-exclusive; no recovered mesh/camera/IK.",
            "61 bank poses do not establish continuous native60fps interpolation or change gameplay pacing.",
            "REST mesh contacts plus original FK determine palms; reload.contact attaches held part to palm.",
            "Attachment fades .40..46 to protect authored seating before later right-hand source rack/return; FIRST must verify contact.",
            "Master owns source61 copying, action whitelist, loader/runtime60grid and arms/upper-arms integration.",
            "All-route arms-inclusive budget is unmeasured. FIRST feedback, worker correction/review, then SECOND remain pending."]})
    if set(output) != {root/p for p in allowed}:
        raise ValueError("Incomplete W214 output mapping")
    return output
