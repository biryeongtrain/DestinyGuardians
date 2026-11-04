#!/usr/bin/env python3
"""W199 Shadowshot source lower-body retarget; no subprocess, runtime, or rig edits.

Use --extract <W196 hunter_shadowshot.json[.gz]> once to pin the evaluated data.
Normal generation and --verify need only this checkout, never the source SSD.
Only the assigned W199 art, pack and source record are written.
"""
import argparse
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_source_w197 as w197

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art/blockbench/animations/guardian_hunter_w197_r1.bbmodel"
BASE_PACK = ROOT / "src/main/resources/destiny/animation/hunter_w197.animation.json"
ART = ROOT / "art/blockbench/animations/guardian_hunter_w199_r1.bbmodel"
PACK = ROOT / "src/main/resources/destiny/animation/hunter_w199.animation.json"
DATA = ROOT / "art/animations/w199/shadowshot-source.json"
MODEL = "guardian_hunter_w199_r1"
ATTACK = "h15_super_void_attack"
GROUND, AIR = "80A8AD97", "80A8AD8A"
GZIP_SEAL_SHA = "ba2446732d8886cdd56bcfb5ae7bb61c6c728a85ddea44ceba25c4ca2e5dff93"
SAMPLE_SHA = "87ac7043e028650c596b4072c84a52e74bfe253428b5a7911a3484efc653d0f8"
BASE_SHA = "63b2f49688dcbf53e1e489335be5cd3d18da0e7bc6c014a02d1818bed2a53a20"
FBX_SHA = "6e1f83ce5d8f8c11ebb8d50d0b0192bb95106ea6bd60466e791b6d0b9ed54b00"
C = w197.C
HIP = "C7C0BA6E"
LEGS = (("prl_right_leg", "prfl_right_foreleg", ("9F0FD28C", "8BD44A3F", "B9B9E05D")),
        ("pll_left_leg", "plfl_left_foreleg", ("695DAF09", "35B14D1B", "0F8B505D")))
SELECTED = sorted({HIP, "A252A6A2", "A352A6A2", "7E92D640", "DE9D6BEA", "8C83CB67"} |
                  {n for _, _, chain in LEGS for n in chain})
# Target clip seconds -> source seconds (source frame = seconds*30+1).
# Frame22 is the last inspected close-cheek draw sample before outward hand
# travel at frame25. This is an authored phase alignment, NOT a decoded event.
PHASES = [[0, 0], [.05, 0], [.15, 9/30], [.25, 18/30], [.30, 21/30],
          [.35, 24/30], [.60, 33/30], [.75, 39/30], [.90, 39/30]]
BLEND = [[0, 0], [.05, 1], [.75, 1], [.90, 0]]
PLAN = {
    "selected": GROUND, "airStatus": "inspected/deferred: no runtime ground/air selector",
    "phaseSeconds": PHASES, "blendSeconds": BLEND, "neutralFrame": 40,
    "phaseBasis": "visual hand-head separation: frame22 draw, frame25 outward follow-through; unknown event semantics",
    "basis": C, "basisEvidence": "W197 anatomical +Y left, +Z up, +X anterior; target +X right,+Y up,-Z front; native camera unverified",
    "hip": "heading from projected C*Rpose*Rneutral^-1*C^-1 forward; postmultiply accepted hip by Ry(heading); premultiply waist by Ry(-heading)",
    "legs": "anatomical hip/knee/ankle frame F, independent of hashed roll; world thigh=C*Fpose*Fneutral^-1*C^-1*Taccepted; local against actual player_root parent (legs are siblings of hip); H21 negative-X knee=-max(0,min(155,bend-bendNeutral+abs(acceptedKnee)))",
    "upperBody": "chest subtree and arm/item locals retained; hip local Y twist preserves vertical hip-waist offset, inverse waist twist preserves chest, head, both hands and authoritative aim, including runtime chest pitch",
    "root": "all inherited player_root channels byte-identical; no fake movement or source translation; existing gameplay lift remains authoritative",
    "adaptation": "source frame40 calibrated to accepted ready, not raw source Euler; 200Hz linear keys, equivalent Euler family unwrap, midpoint chest-transform refinement, <=256 keys per changed channel",
    "limitations": ["source pelvis pitch/roll and source torso lean deferred to retain chest/cheek/nock trajectory",
                    "relative knee flex calibrated to Steve ready; not literal source joint angles or foot planting",
                    "source air take inspected but not selected; ground cast includes source airborne leg tuck",
                    "source root displacement, scale, pedestal and fingers omitted; no new movement",
                    "source S80808C1A fields remain unknown; no event, damage, timing, sound or session changes",
                    "inherited root retained for release/drop: source feet may extend below model anchor during assisted lift; native terrain clearance pending",
                    "static FK only; master owns model switch, Java gates and native pitch/lift/contact QA"],
    "nativeQueue": ["ground activation: start superAttack, DRAW tick4, automatic release tick7 at clip .30",
                    "live pitch up/level/down: grip, cheek/nock, taut cord, arrow heading before release; follow-through after .30",
                    "side/front/back crouch and airborne tuck: feet/armor/cape clipping and original lift/release drop",
                    "recovery/ready and cancel/replace cleanup; source Arc and all non-Void regression"]}


def encoded(obj):
    return (json.dumps(obj, indent=2, allow_nan=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def payload_sha(data):
    return sha(json.dumps({k: data[k] for k in ("bones", "clips")}, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode())


def extract(path):
    packed = path.read_bytes()
    if packed[:2] == b"\x1f\x8b":
        assert sha(packed) == GZIP_SEAL_SHA, "Not the sealed W196 gzip"
        raw = gzip.decompress(packed)
    else:
        raw = packed
    assert sha(raw) == SAMPLE_SHA, "Not the sealed W196 evaluated sample"
    source = json.loads(raw)
    assert source["sampleSpace"] == "armature_object" and len(source["bones"]) == 72
    indices = {b["name"]: i for i, b in enumerate(source["bones"])}
    clips = {}
    for c in source["clips"]:
        assert c["tag"] in (GROUND, AIR)
        clips[c["tag"]] = {k: v for k, v in c.items() if k != "frames"}
        clips[c["tag"]]["frames"] = [
            {"frame": f["frame"], "seconds": f["seconds"],
             "matrices": {n: f["matrices"][indices[n]] for n in SELECTED}}
            for f in c["frames"]]
    data = {"schemaVersion": 1, "sampleSHA256": SAMPLE_SHA,
            "sampleGzipSealSHA256": GZIP_SEAL_SHA,
            "extractionNote": "Canonical uncompressed SHA verified; equivalent original W196 raw sample accepted when gzip is absent from clone; recorded gzip seal is not recreated",
            "sampleOrigin": "W196 samples/hunter_shadowshot.json.gz (evaluated 3P player rig)",
            "acceptedModelSHA256": sha(SOURCE.read_bytes()),
            "acceptedPackSHA256": sha(BASE_PACK.read_bytes()),
            "provenance": {k: v for k, v in source.items() if k not in ("bones", "clips")},
            "bones": {b["name"]: b for b in source["bones"]},
            "sampledBoneIds": SELECTED, "clips": clips, "retarget": PLAN}
    data["selectedPayloadSHA256"] = payload_sha(data)
    data["inspection"] = inspection(data)
    return data


def inspection(data):
    result = {}
    for tag in (GROUND, AIR):
        frames = data["clips"][tag]["frames"]
        knees = [[] for _ in LEGS]
        for f in frames:
            points = {n: [m[i][3] for i in range(3)] for n, m in f["matrices"].items()}
            for values, (_, _, chain) in zip(knees, LEGS):
                values.append(w197.leg_frame(points, chain)[1])
        result[tag] = {"frames": len(frames), "durationSeconds": frames[-1]["seconds"],
                       "kneeDegreesMinMax": [[min(v), max(v)] for v in knees],
                       "hipHeightMinMax": [min(f["matrices"][HIP][2][3] for f in frames),
                                           max(f["matrices"][HIP][2][3] for f in frames)],
                       "eventStatus": "S80808C1A fields unknown; retained verbatim, never used as release markers"}
    return result


def validate_data(data):
    assert data["sampleGzipSealSHA256"] == GZIP_SEAL_SHA
    assert data["sampleSHA256"] == SAMPLE_SHA
    assert data["acceptedModelSHA256"] == sha(SOURCE.read_bytes()) == BASE_SHA
    assert data["acceptedPackSHA256"] == sha(BASE_PACK.read_bytes())
    assert data["provenance"]["sourceFbxSHA256"] == FBX_SHA
    assert data["provenance"]["sourceManifestSHA256"] == "19ed4b5677ef2bf44aebf9ed9d2dc1f36ab4b27022553a67510fa570590d1243"
    assert data["provenance"]["sourceBoneMapSHA256"] == "a2c4293d6b66363a78e1de681a2bdbbaf4a849e5a8cc09b4c154781993337f64"
    assert data["sampledBoneIds"] == SELECTED and data["retarget"] == PLAN
    assert data["selectedPayloadSHA256"] == payload_sha(data) == "5fda74d54c41d3549841954e6c3fd9599fbe6e9b1dc4ca1a59eb60edba47ae8a"
    assert data["inspection"] == inspection(data)
    for _, _, chain in LEGS:
        assert data["bones"][chain[0]]["parent"] == HIP
        for parent, child in zip(chain, chain[1:]):
            assert data["bones"][child]["parent"] == parent
    assert set(data["clips"]) == {GROUND, AIR}
    for clip in data["clips"].values():
        assert clip["sampleCount"] == len(clip["frames"]) == 40
        assert clip["perspective"] == "3P_player_rig" and clip["durationSeconds"] == 1.3
        for index, frame in enumerate(clip["frames"]):
            assert frame["frame"] == index+1 and abs(frame["seconds"]-index/30) < 1e-8
            assert set(frame["matrices"]) == set(SELECTED)
            for m in frame["matrices"].values():
                assert len(m) == 4 and all(len(r) == 4 for r in m)
                assert all(math.isfinite(v) for r in m for v in r) and m[3] == [0, 0, 0, 1]
                w197.rotation(m)


def heading(data, seconds):
    current = w197.source_at(data, GROUND, seconds)[HIP]
    neutral = w197.source_at(data, GROUND, 1.3)[HIP]
    delta = h15.mm(C, h15.mm(current, h15.mm(h19.inverse_rotation(neutral), h19.inverse_rotation(C))))
    forward = h19.vector(delta, [0, 0, -1])
    return math.degrees(math.atan2(-forward[0], -forward[2]))


def adapted_pose(model, data, old, time):
    p, _ = h19.sample(old, time)
    weight = w197.curve(BLEND, time)
    if weight == 0:
        return p
    seconds = w197.curve(PHASES, time)
    accepted = copy.deepcopy(p)
    original = h19.fk(model, p)
    yaw = heading(data, seconds) * weight
    twist = h15.rot([0, yaw, 0])
    # Right multiplication leaves the local +Y hip->waist offset invariant.
    # This compensates the entire chest subtree, not just the bow item angles.
    p["phip_hip"] = h19.euler(h15.mm(h15.rot(p["phip_hip"]), twist))
    p["pw_waist"] = h19.euler(h15.mm(h19.inverse_rotation(twist), h15.rot(p["pw_waist"])))
    points = w197.source_points(data, GROUND, seconds)
    neutral = w197.source_points(data, GROUND, 1.3)
    parent = h19.fk(model, p)["player_root"]
    for upper, lower, chain in LEGS:
        frame, bend = w197.leg_frame(points, chain)
        ref, neutral_bend = w197.leg_frame(neutral, chain)
        delta = h15.mm(C, h15.mm(frame, h15.mm(h19.inverse_rotation(ref), h19.inverse_rotation(C))))
        desired = h15.mm(delta, w197.rotation(original[upper]))
        flex = -max(0, min(155, bend-neutral_bend+abs(accepted[lower][0])))
        world = w197.slerp(w197.rotation(original[upper]), desired, weight)
        p[upper] = h19.euler(h15.mm(h19.inverse_rotation(parent), world))
        knee = accepted[lower][0]
        p[lower] = [knee+(flex-knee)*weight, 0, 0]
    return p


CHANGED = ("phip_hip", "pw_waist") + tuple(n for upper, lower, _ in LEGS for n in (upper, lower))


def unwrap(frames):
    previous = None
    for _, p in frames:
        if previous is not None:
            for bone in CHANGED:
                x, y, z = p[bone]
                candidates = []
                for v in ([x, y, z], [x+180, 180-y, z+180]):
                    candidates.append([a+360*round((b-a)/360) for a, b in zip(v, previous[bone])])
                p[bone] = min(candidates, key=lambda v: sum((a-b)**2 for a, b in zip(v, previous[bone])))
        previous = copy.deepcopy(p)


def generate_clip(model, data, old):
    times = {round(i/200, 6) for i in range(181)} | {t for t, _ in PHASES}
    times |= {k["time"] for a in old["animators"].values() for k in a["keyframes"]}
    frames = [(t, adapted_pose(model, data, old, t)) for t in sorted(times)]
    for _ in range(8):
        unwrap(frames)
        additions = []
        for (ta, a), (tb, b) in zip(frames, frames[1:]):
            t = round((ta+tb)/2, 9)
            p, _ = h19.sample(old, t)
            for n in CHANGED:
                p[n] = [(v+w)/2 for v, w in zip(a[n], b[n])]
            baseline, _ = h19.sample(old, t)
            before, after = h19.fk(model, baseline), h19.fk(model, p)
            error = max(abs(before["pc_chest"][i][j]-after["pc_chest"][i][j]) for i in range(3) for j in range(4))
            if error > .00001:
                additions.append((t, adapted_pose(model, data, old, t)))
        if not additions:
            break
        frames = sorted(frames+additions, key=lambda v: v[0])
        assert len(frames) <= 256, "Chest compensation exceeds bounded key budget"
    else:
        raise AssertionError("Chest compensation interpolation did not converge")
    clip = copy.deepcopy(old)
    clip["uuid"] = h15.uid("w199/"+ATTACK)
    clip["snapping"] = 200
    for animator in clip["animators"].values():
        bone = animator["name"]
        if bone not in CHANGED:
            continue
        animator["keyframes"] = [k for k in animator["keyframes"] if k["channel"] != "rotation"]
        for t, p in frames:
            animator["keyframes"].append({"uuid": h15.uid(f"w199/{ATTACK}/{bone}/rotation/{t}"),
                "channel": "rotation", "time": t, "interpolation": "linear",
                "data_points": [dict(zip("xyz", (round(v, 9) for v in p[bone]))) ]})
    return clip


def compose(source, data):
    validate_data(data)
    model = copy.deepcopy(source)
    model["name"] = model["model_identifier"] = MODEL
    model["animations"] = [generate_clip(model, data, c) if c["name"] == ATTACK else c
                           for c in model["animations"]]
    return model


def export(model):
    return {"model": MODEL, "animations": [c for c in model["animations"] if c["name"].startswith("h15_")]}


def validate(model, source):
    for key in source:
        if key not in ("name", "model_identifier", "animations"):
            assert model[key] == source[key], "Changed geometry/rig: "+key
    before = {c["name"]: c for c in source["animations"]}
    after = {c["name"]: c for c in model["animations"]}
    assert set(before) == set(after) and len(export(model)["animations"]) == 20
    for name, clip in before.items():
        if name != ATTACK:
            assert after[name] == clip, "Changed inherited clip "+name
    old, new = before[ATTACK], after[ATTACK]
    assert new["length"] == old["length"] == .90 and new["loop"] == old["loop"] == "once"
    old_bones = {a["name"]: a for a in old["animators"].values()}
    for a in new["animators"].values():
        if a["name"] not in CHANGED:
            assert a == old_bones[a["name"]], "Changed inherited upper/root/cape animator"
        for channel in {k["channel"] for k in a["keyframes"]}:
            keys = [k for k in a["keyframes"] if k["channel"] == channel]
            ts = [k["time"] for k in keys]
            assert len(ts) == len(set(ts)) <= 256
            assert all(math.isfinite(v) for k in keys for v in k["data_points"][0].values())
    for t in (0, .90):
        a, b = h19.sample(old, t)[0], h19.sample(new, t)[0]
        for n in h15.BONES:
            ar, br = h15.rot(a[n]), h15.rot(b[n])
            assert max(abs(ar[i][j]-br[i][j]) for i in range(3) for j in range(3)) < 1e-7


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.extract and args.verify:
        parser.error("--extract and --verify are mutually exclusive")
    data = extract(args.extract) if args.extract else json.loads(DATA.read_text())
    source = json.loads(SOURCE.read_text())
    model = compose(source, data)
    validate(model, source)
    for path, value in ((DATA, data), (ART, model), (PACK, export(model))):
        raw = encoded(value)
        if args.verify:
            assert path.read_bytes() == raw, "Reproduction differs: "+str(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print("PASS W199: 20 runtime clips, 19 byte-equivalent inherited clips; source ground hips/legs; inherited root/upper/aim/contact timing")


if __name__ == "__main__":
    main()
