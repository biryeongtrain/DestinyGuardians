#!/usr/bin/env python3
"""W207 Blast Furnace reload: 61 poses, continuous authored movement spans.

Standard-library only. Import and generate() never write files; master owns
output materialization, runtime routing, skin arms and native verification.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
ART = ROOT / "art/weapons/w207/blast_furnace"
KEY = "weapon_reload_w207_blast_furnace/blast_furnace"
FP = ("firstperson_righthand", "firstperson_lefthand")
PARTS = ("body", "magazine")
GRIPS = ("native", "twohand")
STEPS = 60
# W114 gameplay-informed times/landmarks. The repeated .36/.48 keys are an
# intentional extracted-magazine hold, not a stop at every movement waypoint.
KEYS = (
    (0, (0,0,0), (0,0,0), (0,0,0)),
    (.10, (8,-6,-18), (-.3,1.0,-.3), (0,0,0)),
    (.22, (58,-10,-22), (-.7,2.8,-.8), (0,-2.0,.15)),
    (.36, (66,-12,-26), (-.8,3.2,-1), (.2,-5.8,.35)),
    (.48, (66,-12,-26), (-.8,3.2,-1), (.2,-5.8,.35)),
    (.62, (64,-11,-25), (-.8,3.1,-1), (.1,-3.4,.2)),
    (.72, (67,-9,-23), (-.6,3.0,-.8), (0,0,0)),
    (.80, (60,-8,-21), (-.4,2.7,-.6), (0,0,0)),
    (.90, (26,-4,-12), (-.1,1.2,-.25), (0,0,0)),
    (1, (0,0,0), (0,0,0), (0,0,0)),
)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2,
                       allow_nan=False) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tangents(times, values):
    """PCHIP weighted harmonic interior slopes; zero only at holds/reversals.

    Both adjacent Hermite segments use the same derivative. Zero endpoint
    slopes meet stationary idle with C1 continuity without changing duration.
    """
    widths = [b-a for a,b in zip(times,times[1:])]
    slopes = [(b-a)/h for a,b,h in zip(values,values[1:],widths)]
    result = [0.0] * len(values)
    for i in range(1,len(values)-1):
        before, after = slopes[i-1], slopes[i]
        if before * after > 0:
            w1 = 2*widths[i]+widths[i-1]
            w2 = widths[i]+2*widths[i-1]
            result[i] = (w1+w2)/(w1/before+w2/after)
    return result


TIMES = tuple(key[0] for key in KEYS)
CHANNELS = tuple(tuple(key[column][axis] for key in KEYS)
                 for column in (1,2,3) for axis in range(3))
TANGENTS = tuple(tangents(TIMES,channel) for channel in CHANNELS)


def sample(progress):
    """Rotation degrees XYZ, view translation, then local magazine offset."""
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError(progress)
    if progress in (0,1):
        return tuple(list(v) for v in KEYS[0 if progress == 0 else -1][1:])
    i = next(i for i in range(len(TIMES)-1) if progress <= TIMES[i+1])
    h = TIMES[i+1]-TIMES[i]
    u = (progress-TIMES[i])/h
    h00,h10 = 2*u**3-3*u**2+1, u**3-2*u**2+u
    h01,h11 = -2*u**3+3*u**2, u**3-u**2
    values = [y[i] if y[i] == y[i+1] else
              h00*y[i]+h10*h*m[i]+h01*y[i+1]+h11*h*m[i+1]
              for y,m in zip(CHANNELS,TANGENTS)]
    return tuple(values[i:i+3] for i in (0,3,6))


def xyz(degrees):
    x,y,z = map(math.radians,degrees)
    a,b,c,d,e,f = math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return [[c*e,-c*f,d], [b*d*e+a*f,-b*d*f+a*e,-b*c],
            [-a*d*e+b*f,a*d*f+b*e,a*c]]


def mul(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def vec(matrix,vector):
    return [sum(row[i]*vector[i] for i in range(3)) for row in matrix]


def euler(matrix):
    y = math.asin(max(-1.0,min(1.0,matrix[0][2])))
    if abs(math.cos(y)) > 1e-8:
        x,z = math.atan2(-matrix[1][2],matrix[2][2]),math.atan2(-matrix[0][1],matrix[0][0])
    else:
        x,z = math.atan2(matrix[2][1],matrix[1][1]),0.0
    return [round(math.degrees(v),8) for v in (x,y,z)]


def pose_display(base, twohand_base, progress, part, grip):
    # Exact accepted idle endpoint objects, including numeric precision and
    # non-FP contexts; no accumulated Euler or carrier compensation drift.
    if progress in (0,1):
        return copy.deepcopy(base if grip == "native" else twohand_base)
    rotation,translation,offset = sample(progress)
    display = copy.deepcopy(base)
    for context in FP:
        pose = display[context]
        pose["rotation"] = [v+rotation[i] for i,v in enumerate(pose["rotation"])]
        local = vec(xyz(pose["rotation"]),offset) if part == "magazine" else [0,0,0]
        pose["translation"] = [v+translation[i]+local[i]*pose["scale"][i]
                               for i,v in enumerate(pose["translation"])]
        if grip == "twohand":
            # W32 inverse charged-crossbow carrier, before ItemTransform.
            # Same convention as build_weapons_w30.two_hand_display, with
            # accepted twohand non-FP displays copied instead of regenerated.
            inverse = xyz([0,-10,0])
            t = list(pose["translation"])
            t[0] += .641864*16
            pose["translation"] = vec(inverse,t)
            pose["rotation"] = euler(mul(inverse,xyz(pose["rotation"])))
        for field in ("rotation","translation"):
            pose[field] = [round(v,8) for v in pose[field]]
    if grip == "twohand":
        for context,value in twohand_base.items():
            if context not in FP:
                display[context] = copy.deepcopy(value)
    return display


def generate() -> dict[Path, bytes]:
    """Return only NEW W207 namespace assets and the NEW W207 manifest."""
    paths = {
        "canonical": ASSETS/"models/weapon_surface_w123/blast_furnace.json",
        "body": ASSETS/"models/weapon_surface_w123/blast_furnace_body.json",
        "magazine": ASSETS/"models/weapon_surface_w123/blast_furnace_magazine.json",
        # Read accepted carrier display only, never its old ripped geometry.
        "twohand": ASSETS/"models/weapon/pulse_rifle/blast_furnace_twohand.json",
        "item": ASSETS/"items/weapon/blast_furnace.json",
    }
    raw = {name:path.read_bytes() for name,path in paths.items()}
    sources = {name:json.loads(data) for name,data in raw.items()}
    canonical = sources["canonical"]
    base,twohand = canonical["display"],sources["twohand"]["display"]
    assert all(context in base and context in twohand for context in FP)
    assert canonical["elements"] == sources["body"]["elements"]+sources["magazine"]["elements"]
    assert (len(sources["body"]["elements"]),len(sources["magazine"]["elements"])) == (92,5)
    for part in PARTS:
        assert sources[part]["textures"] == canonical["textures"]
    outputs = {}
    for part in PARTS:
        geometry = {k:copy.deepcopy(v) for k,v in sources[part].items() if k != "display"}
        outputs[ASSETS/f"models/{KEY}_{part}.json"] = encode(geometry)
    entries = []
    for frame in range(STEPS+1):
        progress = frame/STEPS
        refs = {}
        for part in PARTS:
            for grip in GRIPS:
                name = f"{KEY}_{frame:02d}_{part}_{grip}"
                outputs[ASSETS/f"models/{name}.json"] = encode({
                    "parent":"destiny:"+KEY+"_"+part,
                    "display":pose_display(base,twohand,progress,part,grip)})
                refs[part,grip] = {"type":"minecraft:model","model":"destiny:"+name}
        def composite(grip):
            return {"type":"minecraft:composite","models":[refs[part,grip] for part in PARTS]}
        entries.append({"threshold":progress,"model":{
            "type":"minecraft:condition","property":"minecraft:custom_model_data","index":0,
            "on_true":composite("twohand"),"on_false":composite("native")}})
    source_item = sources["item"]
    item = copy.deepcopy(source_item)
    item["model"] = {"type":"minecraft:select","property":"minecraft:display_context",
        "cases":[{"when":list(FP),"model":{
            "type":"minecraft:range_dispatch","property":"minecraft:custom_model_data","index":1,
            "entries":entries,"fallback":copy.deepcopy(source_item["model"])}}],
        "fallback":copy.deepcopy(source_item["model"])}
    outputs[ASSETS/f"items/{KEY}.json"] = encode(item)
    manifest = {
        "schemaVersion":1,"stage":"W207","weapon":"blast_furnace",
        "graphId":"destiny:"+KEY,"generator":"scripts/generate_reload_w207_blast_furnace.py",
        "generatorSha256":sha(Path(__file__).read_bytes()),
        "frames":STEPS+1,"quantization":STEPS,"parts":list(PARTS),
        "partCounts":{part:len(sources[part]["elements"]) for part in PARTS},
        "compositeCubes":len(canonical["elements"]),"progressFloatIndex":1,"gripBooleanIndex":0,
        "firstPersonContexts":list(FP),"keyframes":KEYS,
        "interpolation":"C1 piecewise Hermite; weighted harmonic monotone interior slopes; zero endpoint slopes",
        "intentionalHold":[.36,.48],"gameplayDurationChanged":False,
        "originalGraphFallbackExact":True,"endpointsExactBaseDisplay":True,
        "nativeGameplayVerified":False,"sourceAnimationRecovered":False,
        "inputSha256":{str(paths[name].relative_to(ROOT)):sha(data) for name,data in raw.items()},
        "sha256":{str(path.relative_to(ROOT)):sha(data) for path,data in outputs.items()},
        "assets":len(outputs),
        "references":["art/weapons/w114/blast_furnace/reference-notes.md",
                      "art/weapons/w114/blast_furnace/gameplay-provenance.json",
                      "https://www.youtube.com/watch?v=SRNv0YDgYBM"],
        "limitations":["Authored reference-informed motion, not recovered source animation/camera/IK.",
                       "61 poses remove 21-bank quantization loss; server item-state updates remain up to 20Hz, not proof of 60fps.",
                       "Skin-arm contacts and runtime routing owned by master; native reload/ADS/interrupt checks pending."]}
    outputs[ART/"manifest.json"] = encode(manifest)
    allowed = (ASSETS/"models/weapon_reload_w207_blast_furnace",
               ASSETS/"items/weapon_reload_w207_blast_furnace")
    assert all(path.is_absolute() and (path == ART/"manifest.json" or
               any(path.is_relative_to(folder) for folder in allowed)) for path in outputs)
    return outputs
