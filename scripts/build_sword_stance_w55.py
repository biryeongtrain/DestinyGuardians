#!/usr/bin/env python3
"""W55: four authored persistent sword loops, preserving every W53 raw clip.

rtk proxy python3 -B scripts/build_sword_stance_w55.py [--verify]
Only the five declared W55 paths may be written; --verify writes nothing.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_animation_h20 as h20
import build_sword_animation_w53 as w53

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/build_sword_stance_w55.py"
SOURCE = "art/blockbench/animations/guardian_sword_w53.bbmodel"
SOURCE_PACK = "src/main/resources/destiny/animation/sword_w53.animation.json"
ART = "art/blockbench/animations/guardian_sword_w55.bbmodel"
PACK = "src/main/resources/destiny/animation/sword_w55.animation.json"
MANIFEST = "art/weapons/w55/manifest.json"
NOTES = "art/weapons/w55/animation-notes.md"
MODEL = "guardian_sword_w55"
PINS = {
    **w53.PINS,
    w53.SCRIPT: "6f96b1f1bb7b276b11b733b0186c07959402e57dd53dd5d02f7ade0b53f5a0ae",
    SOURCE: "41ff15db10994f1871ccb8ccb49a5aa9ba962aba2515381cdf77cf771fb77f3f",
    SOURCE_PACK: "78c6a81b019cc659ea99f048c44de8f01d77b48d1cb3fe482121fc5f4234cd45",
}
LOOPS = [
    ("idle", 2.40, "W53 low ready with subtle breath and cape settling"),
    ("move", .80, "alternating leg/knee gait, steady weapon carry, cape sway"),
    ("guard", 1.60, "raised frontal blade, free hand up, defensive breath pulse"),
    ("air", 1.20, "tucked knees, restrained torso motion and flowing cape"),
]
NAMES = ["h15_sword_" + row[0] for row in LOOPS]
sha, encode = w53.sha, w53.encode


def check_pins():
    for path, expected in PINS.items():
        assert sha((ROOT / path).read_bytes()) == expected, "Changed pinned input: " + path


def replace_identifiers(raw, names):
    text = raw.decode()
    spans = w53.fields(text)
    for start, end in sorted((spans[k] for k in names), reverse=True):
        text = text[:start] + json.dumps(MODEL) + text[end:]
    return text.encode()


def append_art(raw, clips):
    # W53's exact byte-splice preserves every inherited top-level rig field and
    # all 29 animation objects. Only the two model identity values change.
    return replace_identifiers(w53.append_preserving_bytes(raw, clips), ("name", "model_identifier"))


def append_pack(raw, clips):
    # Same raw-tail splice as W53; re-encoding the original eight is forbidden.
    text = raw.decode()
    tail = w53.fields(text)["animations"][1] - 1
    while text[tail-1].isspace():
        tail -= 1
    added = ",\n" + ",\n".join(
        "\n".join("    " + line for line in json.dumps(c, indent=2, allow_nan=False).splitlines())
        for c in clips)
    return replace_identifiers((text[:tail] + added + text[tail:]).encode(), ("model",))


def pose(model, kind, phase):
    s, c = math.sin(2*math.pi*phase), math.cos(2*math.pi*phase)
    breath = (1-c)/2
    if kind == "idle":
        p = w53.sword_pose(model, -10 + .6*s, [4, 18 + .16*breath, -5.3],
                           [65 + .7*breath, -15, 0], lean=-3-.3*breath,
                           crouch=.75+.015*breath,
                           free=[-5.5, 17.2+.10*breath, -2.5], cape=10+.9*s)
        p["cape_cape"][2] += .6*s
    elif kind == "move":
        p = w53.sword_pose(model, -10+2*s, [4+.15*s, 18+.18*(1-c*c), -5.3],
                           [65+2*s, -15, -1.5*s], lean=-6-.5*(1-c*c), crouch=.75,
                           free=[-5.5, 17.5-.4*s, -2.5+.65*s], cape=18+3*math.sin(2*math.pi*phase-.5))
        p["phip_hip"][2] = 1.4*s
        p["pw_waist"][2] = -.8*s
        p["prl_right_leg"] = [-10.5+25*s, -8, -5.25]
        p["pll_left_leg"] = [6.75-25*s, 12, 6]
        p["prfl_right_foreleg"] = [26+12*s, 0, 0]
        p["plfl_left_foreleg"] = [26-12*s, 0, 0]
        p["cape_cape"][1:] = [4*s, 1+5*math.sin(2*math.pi*phase-.5)]
    elif kind == "guard":
        # Native sword blade +Y becomes +Z after the pinned display Rx(+90).
        # Item Rx(-75) therefore lifts the blade; wrist remains in front (-Z).
        p = w53.sword_pose(model, -5+.5*s, [2.5, 21.1+.16*breath, -6],
                           [-75+1.5*breath, -10, -15+1*s], lean=-5-.6*breath,
                           crouch=.95+.03*breath,
                           free=[-3.8, 22.5+.16*breath, -5], cape=12+1.3*s)
        p["cape_cape"][2] += .8*s
    else:
        assert kind == "air"
        p = w53.sword_pose(model, -10+1.4*s, [4, 18.6+.25*breath, -5.5],
                           [55+2*s, -15, -2*s], lean=-7-1.2*breath, crouch=.75,
                           free=[-5.5, 19+.2*s, -3], cape=22+4*s)
        p["prl_right_leg"] = [-42-3*breath, -8, -5]
        p["pll_left_leg"] = [-32-3*breath, 12, 6]
        p["prfl_right_foreleg"] = [82+4*breath, 0, 0]
        p["plfl_left_foreleg"] = [68+4*breath, 0, 0]
        p["cape_cape"][1:] = [4*s, 2+3*math.sin(2*math.pi*phase-.4)]
    return p


def author(model):
    clips = []
    ready, _ = h19.sample(model["animations"][21], 0)
    for kind, length, _ in LOOPS:
        frames = [(round(length*i/16, 6), pose(model, kind, i/16)) for i in range(16)]
        if kind == "idle":
            frames[0] = (0, copy.deepcopy(ready))
        # Literal equal endpoints, including Euler representation (no 360 wrap).
        frames.append((length, copy.deepcopy(frames[0][1])))
        clip = h20.new_clip(model, "h15_sword_"+kind, frames, loop=True)
        if kind == "move":
            # Alternating support feet make the lowest-corner envelope sharper.
            # Keep H20's keys and add 80 Hz fit samples, without a bob offset.
            root = next(a for a in clip["animators"].values() if a["name"] == "player_root")
            existing = {k["time"] for k in root["keyframes"] if k["channel"] == "position"}
            for time in sorted({round(i/80, 6) for i in range(round(length*80)+1)} - existing):
                p, _ = h19.sample(clip, time)
                root["keyframes"].append({"uuid": h15.uid(f"{clip['name']}/player_root/position/{time}"),
                    "channel": "position", "time": time, "interpolation": "linear",
                    "data_points": [{"x": 0, "y": h15.floor_y(model, p), "z": 0}]})
        clips.append(clip)
    return clips


def raw_fields_preserved(before_raw, after_raw, excluded):
    before, after = before_raw.decode(), after_raw.decode()
    a, b = w53.fields(before), w53.fields(after)
    assert a.keys() == b.keys()
    for key in a.keys() - set(excluded):
        assert before[slice(*a[key])] == after[slice(*b[key])], "Raw field changed: " + key


def channel_keys(animator, channel):
    return sorted((k for k in animator["keyframes"] if k["channel"] == channel), key=lambda k: k["time"])


def validate(source_raw, source_pack_raw, art_raw, pack_raw):
    source, original_pack, model, pack = map(json.loads, (source_raw, source_pack_raw, art_raw, pack_raw))
    assert model["name"] == model["model_identifier"] == pack["model"] == MODEL
    raw_fields_preserved(source_raw, art_raw, ("name", "model_identifier", "animations"))
    raw_fields_preserved(source_pack_raw, pack_raw, ("model", "animations"))
    assert len(source["animations"]) == 29 and len(original_pack["animations"]) == 8
    assert source["animations"][21:] == original_pack["animations"]
    assert model["animations"][:29] == source["animations"]
    assert pack["animations"][:8] == original_pack["animations"]
    art_spans, pack_spans = map(w53.animation_spans, (art_raw.decode(), pack_raw.decode()))
    assert art_spans[:29] == w53.animation_spans(source_raw.decode())
    assert pack_spans[:8] == w53.animation_spans(source_pack_raw.decode())
    assert art_spans[21:] == pack_spans  # old eight AND new four byte-identical between exports
    assert len(model["animations"]) == 33 and len(pack["animations"]) == 12
    clips = model["animations"][29:]
    assert clips == pack["animations"][8:] and [c["name"] for c in clips] == NAMES
    assert len({a["name"] for a in model["animations"]}) == 33
    assert len({a["uuid"] for a in model["animations"]}) == 33
    groups = {g["name"]: g for g in model["groups"]}
    assert len(h15.BONES) == 16 and set(h15.BONES) <= groups.keys()
    for bone in ("pri_right_item", "pli_left_item"):
        assert groups[bone]["rotation"] == [-90, 0, 0]
    used = {a["uuid"] for a in source["animations"]}
    used.update(k["uuid"] for a in source["animations"] for b in a["animators"].values() for k in b.get("keyframes", []))
    ready, ready_y = h19.sample(source["animations"][21], 0)
    stats = []
    for clip, (kind, length, _) in zip(clips, LOOPS):
        assert clip["length"] == length and clip["loop"] == "loop" and clip["override"] is False
        assert clip["uuid"] not in used
        used.add(clip["uuid"])
        assert {a["name"] for a in clip["animators"].values()} == set(h15.BONES)
        root_ys, motion = [], {}
        for group_uuid, animator in clip["animators"].items():
            bone = animator["name"]
            assert group_uuid == groups[bone]["uuid"] and animator["type"] == "bone"
            assert animator["rotation_global"] is animator["quaternion_interpolation"] is False
            expected = ({"rotation", "position"} if bone == "player_root" else
                        {"rotation", "scale"} if bone.endswith("_item") else {"rotation"})
            assert {k["channel"] for k in animator["keyframes"]} == expected
            for key in animator["keyframes"]:
                assert key["uuid"] not in used
                used.add(key["uuid"])
                assert key["interpolation"] == "linear"
                assert math.isfinite(key["time"]) and 0 <= key["time"] <= length
                assert len(key["data_points"]) == 1
                v = key["data_points"][0]
                assert set(v) == set("xyz")
                assert all(type(x) in (int, float) and math.isfinite(x) for x in v.values())
                if key["channel"] == "position":
                    assert bone == "player_root" and v["x"] == v["z"] == 0
                    root_ys.append(v["y"])
                elif key["channel"] == "scale":
                    assert bone.endswith("_item") and set(v.values()) == {1}
                elif bone == "player_root":
                    assert set(v.values()) == {0}
            for channel in expected:
                keys = channel_keys(animator, channel)
                times = [k["time"] for k in keys]
                assert len(times) == len(set(times)) and times[0] == 0 and times[-1] == length
                assert keys[0]["data_points"] == keys[-1]["data_points"], (kind, bone, channel, "seam")
                if channel == "rotation":
                    motion[bone] = max(max(k["data_points"][0][a] for k in keys)-min(k["data_points"][0][a] for k in keys) for a in "xyz")
                    for left, right in zip(keys, keys[1:]):
                        assert max(abs(left["data_points"][0][a]-right["data_points"][0][a]) for a in "xyz") < 90
        if kind == "idle":
            assert h19.sample(clip, 0) == (ready, ready_y), "W53 ready changed"
        assert motion["pc_chest"] > .25 and motion["cape_cape"] > 1, "Static loop"
        max_floor_error, feet, blade_min_y, left_min_y = 0, [], 1, float("inf")
        for i in range(round(length*200)+1):
            time = round(i/200, 6)
            p, y = h19.sample(clip, time)
            max_floor_error = max(max_floor_error, abs(y-h15.floor_y(model, p)))
            matrices = h19.fk(model, p, y)
            assert all(math.isfinite(v) for matrix in matrices.values() for row in matrix for v in row)
            feet.append([h19.point(matrices[b], [0, -5.625, 0]) for b in ("prfl_right_foreleg", "plfl_left_foreleg")])
            if kind == "guard":
                right = h19.point(matrices["pri_right_item"], [0, 0, 0])
                left = h19.point(matrices["pli_left_item"], [0, 0, 0])
                assert right[1] > 20 and right[2] < -5 and left[2] < -4
                left_min_y = min(left_min_y, left[1])
                blade_min_y = min(blade_min_y, h19.vector(matrices["pri_right_item"], [0, 0, 1])[1])
                assert left[1] > 21 and blade_min_y > .85
            elif kind == "air":
                assert p["prl_right_leg"][0] <= -40 and p["pll_left_leg"][0] <= -30
                assert p["prfl_right_foreleg"][0] >= 80 and p["plfl_left_foreleg"][0] >= 65
        assert max_floor_error <= .04, (kind, max_floor_error)
        foot_excursion = [max(f[side][2] for f in feet)-min(f[side][2] for f in feet) for side in (0, 1)]
        if kind == "move":
            assert min(foot_excursion) > 4 and motion["prl_right_leg"] >= 49 and motion["pll_left_leg"] >= 49
            a, b = (h19.sample(clip, length*f)[0] for f in (.25, .75))
            assert a["prl_right_leg"][0] > a["pll_left_leg"][0]
            assert b["prl_right_leg"][0] < b["pll_left_leg"][0]
        stat = {"name": clip["name"], "lengthSeconds": length, "loop": True,
                "rotationKeyCountPerBone": 17, "rootYRangeModelUnits": [min(root_ys), max(root_ys)],
                "maxSampledFloorErrorModelUnits": round(max_floor_error, 6),
                "capeRotationExcursionDegrees": round(motion["cape_cape"], 6),
                "footZExcursionModelUnits": [round(x, 6) for x in foot_excursion]}
        if kind == "guard":
            stat.update(bladeDirectionMinUpComponent=round(blade_min_y, 6), freeWristMinYModelUnits=round(left_min_y, 6))
        stats.append(stat)
    return stats


def notes():
    rows = "\n".join(f"| `h15_sword_{kind}` | {length:.2f} | {shape} |" for kind, length, shape in LOOPS)
    return ("""# W55 persistent sword stances — 2026-10-24

`guardian_sword_w55` inherits the entire W53 skin/equipment rig and all 29
animation objects (21 Hunter + 8 sword) as literal unchanged UTF-8 JSON bytes.
Exactly four loops are appended. The runtime sidecar has 12 clips: W53's eight
original sword objects, byte-identical and in original order, followed by four
loops. Every original attack length, key time, cue, transform and UUID is intact.

| Clip | Length (s) | Authored visual intention |
|---|---:|---|
""" + rows + """

Idle begins/ends at the exact sampled W53 ready pose, including fitted root Y.
Move alternates hips/thighs/knees and feet with restrained weapon carry and
cape follow-through. Guard holds a raised blade in front of the torso and a
raised free hand, with a small defensive pulse. Air keeps both knees tucked
while torso and cape move; it has no launch/fall trajectory. All four loops
have identical first/last values on every channel, including Euler angles,
root position and item scale. Seventeen authored poses per loop use linear
interpolation, with gradual sinusoidal changes and no full-turn Euler seams.

## Rig / root contract

All existing rig fields, elements, textures, UVs, equipment pivots, outliner,
bind transforms and inherited animation bytes remain unchanged. Only top-level
`name`/`model_identifier` become `guardian_sword_w55`. The original rig has 18
groups; the same 16 H15 bones animate in each new loop. Both item bind rotations
stay `[-90,0,0]`, both item scales stay 1, and the existing five native sword
models/display mappings remain pinned. H19 arm IK targets the equipment pivots;
H20 cancels torso/arm/bind rotation for the right item. With pinned native
third-person display Rx(+90), model blade +Y maps to item +Z; guard points
that direction upward and keeps both wrists in front (-Z).

Root rotation and X/Z translation are zero throughout all new loops. Root Y
is exclusively H15's lowest-skin-corner floor fit, keyed by H20 at 40 Hz
(including authored pose times), with move refined to 80 Hz for support-foot\ncrossovers. This applies to air too: its root correction
fits tucked legs to the same authoring floor; there is NO extra jump height,
bobbing offset, ballistic arc or entity motion. Move is an in-place gait;
static floor fit does not promise terrain contact, foot locking or no sliding.

## Existing reference boundary

No downloads or new external references. Reused only W53's already pinned W51
`official-manifest.json` and W52 `videos.json`, `mechanics.json`, and four
contact sheets. Inspected the W52 light and mixed aerial contact sheets locally:
torso/leg counter-motion and cape silhouettes are broad pose inspiration.
Aerial 124.8s is Warframe and excluded; 126.3/128.2/130.5s are Destiny frames.
Ultraclocked's *Destiny 2 vs Warframe - Sword Animations*:
<https://www.youtube.com/watch?v=tTjwM26ilgo> (uploaded 2026-04-21).
W52 also pins historical aggressive-heavy material by selFu:
<https://www.youtube.com/watch?v=5oHxtta-a_I> (2023-08-23); this is inherited
provenance, not evidence for these guard/idle loops or current mechanics.

All stance angles, gait/breath periods, guard pulse, knee tuck and cape curves
are authored adaptations, not exact Destiny 2 capture, traced timing or measured
animation. No input, damage, range, energy, grounded flag, activation policy or
per-frame sword behavior is inferred. Runtime selection/install/tests/docs
belong to main; no existing files, gameplay code or integration assets are edited.
No Gradle, Blockbench, Blender, native apps or client/server builds were run.

## Reproduce / verify

`rtk proxy python3 -B scripts/build_sword_stance_w55.py`

`rtk proxy python3 -B scripts/build_sword_stance_w55.py --verify`

Verification is read-only, including no Python cache writes. It checks SHA-256
pins, all rig fields and all 29 inherited raw animation objects, old eight raw
runtime objects and timings, 33/12 counts/order, all 16 animated bones, UUID
uniqueness, finite transforms/FK, explicit unit item scales, unchanged item
binds, literal endpoint equality and bounded adjacent Euler deltas. At 200 Hz
it checks floor-fit error <=0.04 model units, frontal lifted guard/free hand,
tucked air knees, alternating moving feet, and nonstatic torso/cape motion.
Two independent generations must be byte-identical and match saved artifacts;
manifest includes input/output hashes (excluding its own hash). Static FK is
not rendered/native/terrain verification; main owns that downstream validation.
""").encode()


def generate():
    raw, old_pack = (ROOT / SOURCE).read_bytes(), (ROOT / SOURCE_PACK).read_bytes()
    clips = author(json.loads(raw))
    art, pack = append_art(raw, clips), append_pack(old_pack, clips)
    stats = validate(raw, old_pack, art, pack)
    outputs = {ART: art, PACK: pack, NOTES: notes()}
    manifest = {
        "schemaVersion": 1, "stage": "W55", "authoredOn": "2026-10-24", "model": MODEL,
        "baseline": SOURCE, "baselineRuntime": SOURCE_PACK,
        "inheritedAnimationCount": 29, "inheritedHunterAnimationCount": 21,
        "inheritedSwordAnimationCount": 8, "appendedLoopCount": 4,
        "totalAnimationCount": 33, "runtimeExportCount": 12,
        "authoredNotD2Measured": True,
        "clips": [dict(s, visualIntention=row[2]) for s, row in zip(stats, LOOPS)],
        "preservedSwordClips": [{"name": c["name"], "lengthSeconds": c["length"], "rawSha256": sha(b)}
                                for c, b in zip(json.loads(old_pack)["animations"], w53.animation_spans(old_pack.decode()))],
        "rootPolicy": "All new loops: zero rotation/X/Z; H15 floor-fit Y only, including air. No jump offset.",
        "heldItemPolicy": "Unchanged equipment pivots/bind rotations/native display mapping; unit scales.",
        "inputSha256": PINS,
        "outputSha256": {SCRIPT: sha((ROOT / SCRIPT).read_bytes()), **{p: sha(b) for p, b in outputs.items()}},
        "validation": {"nativeClientVerified": False, "appOrBuildRun": False,
                       "rawRigFieldsPreserved": True, "rawInheritedClipsPreserved": True,
                       "rawOriginalRuntimeClipsPreserved": True, "loopEndpointsIdentical": True,
                       "floorSampleRateHz": 200, "floorFitKeyRateHz": 40, "moveFloorFitKeyRateHz": 80,
                       "finiteTransformsAndFK": True, "animatedBoneCount": 16,
                       "deterministicGeneration": "two independent byte comparisons in --verify"},
    }
    outputs[MANIFEST] = encode(manifest)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="read-only saved-byte verification")
    args = parser.parse_args()
    check_pins()
    outputs = generate()
    assert outputs == generate(), "Nondeterministic generation"
    if args.verify:
        for path, expected in outputs.items():
            assert (ROOT / path).read_bytes() == expected, "Saved output differs: " + path
        validate(*[(ROOT / p).read_bytes() for p in (SOURCE, SOURCE_PACK, ART, PACK)])
    else:
        for path, data in outputs.items():
            target = ROOT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    check_pins()
    print("W55 " + ("VERIFY PASS (read-only)" if args.verify else "GENERATE PASS"))
    print(f"{len(PINS)} input pins unchanged; raw rig + 29 inherited clips exact; original runtime 8 byte-identical")
    print("ART: 29+4=33; runtime: 8+4=12; 16 bones/loop; finite/FK/endpoints/unit scale/floor-fit/motion PASS")
    print("Determinism: two independent generations byte-identical; saved outputs " + ("MATCH" if args.verify else "WRITTEN"))
    for kind, length, _ in LOOPS:
        print(f"h15_sword_{kind}: {length:.2f}s loop")
    for path, data in outputs.items():
        print(sha(data) + "  " + path)


if __name__ == "__main__":
    main()
