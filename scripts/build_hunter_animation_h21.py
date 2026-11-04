#!/usr/bin/env python3
"""H21 Shadowshot knee tuck on the final H20 rig and upper-body contract.

Only the two Void clips' four leg channels and ground-fit root Y are authored.
The real server, not this asset, supplies lift/hover. No native item-transform
changes, implicit asset installation, Minecraft launch, or inherited-file writes.
Run with -B; --verify validates saved files; --from-art exports artist edits.
"""
import argparse
import copy
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_animation_h20 as h20

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art/blockbench/animations/guardian_hunter_h20.bbmodel"
ART = ROOT / "art/blockbench/animations/guardian_hunter_h21.bbmodel"
PACK = ROOT / "src/main/resources/destiny/animation/hunter_h21.animation.json"
MODEL = "guardian_hunter_h21"
READY, ATTACK = "h15_super_void", "h15_super_void_attack"
LEGS = ("prl_right_leg", "prfl_right_foreleg", "pll_left_leg", "plfl_left_foreleg")
# Positive thigh X lifts knees toward authoring-front (-Z); negative foreleg X
# folds heels back. Do not copy the reverse-knee sign of the old roll recipe.
LOW = ([32, -10, -8], [-62, 0, 0], [48, 15, 10], [-82, 0, 0])
TUCK = ([58, -10, -10], [-108, 0, 0], [82, 18, 12], [-132, 0, 0])
TUCK_KEYS = [(0, 0), (.05, .2), (.10, .5), (.15, .8), (.20, .95),
             (.25, 1), (.30, 1), (.35, 1), (.45, .85), (.60, .45),
             (.75, .1), (.90, 0)]


def tuck_at(time):
    for (ta, a), (tb, b) in zip(TUCK_KEYS, TUCK_KEYS[1:]):
        if time <= tb + 1e-9:
            return a + (b-a) * (time-ta) / (tb-ta)
    return TUCK_KEYS[-1][1]


def leg_pose(original, amount):
    pose = copy.deepcopy(original)
    for bone, low, high in zip(LEGS, LOW, TUCK):
        pose[bone] = [a + (b-a) * amount for a, b in zip(low, high)]
    return pose


def key(name, bone, channel, time, vector):
    return {"uuid": h15.uid(f"h21/{name}/{bone}/{channel}/{time}"),
            "channel": channel, "time": time, "interpolation": "linear",
            "data_points": [dict(zip("xyz", [round(v, 6) for v in vector]))]}


def author_clip(model, original):
    clip = copy.deepcopy(original)
    name = clip["name"]
    clip["uuid"] = h15.uid("h21/" + name)
    clip["snapping"] = 40
    times = [frame/40 for frame in range(round(clip["length"]*40)+1)]
    animators = {a["name"]: a for a in clip["animators"].values()}
    for bone in LEGS:
        animators[bone]["keyframes"] = [k for k in animators[bone]["keyframes"]
                                           if k["channel"] != "rotation"]
    root = animators["player_root"]
    root["keyframes"] = [k for k in root["keyframes"] if k["channel"] != "position"]
    for time in times:
        old_pose, _ = h19.sample(original, time)
        pose = leg_pose(old_pose, tuck_at(time) if name == ATTACK else 0)
        for bone in LEGS:
            animators[bone]["keyframes"].append(key(name, bone, "rotation", time, pose[bone]))
        # This translates DOWN to the lowest skin cube, never adds flight height.
        root["keyframes"].append(key(name, "player_root", "position", time,
                                      [0, h15.floor_y(model, pose), 0]))
    return clip


def compose(source):
    model = copy.deepcopy(source)
    model["name"] = model["model_identifier"] = MODEL
    model["animations"] = [author_clip(model, a) if a["name"] in (READY, ATTACK) else a
                           for a in model["animations"]]
    return model


def export(model):
    return {"model": MODEL, "animations": [a for a in model["animations"]
                                           if a["name"].startswith("h15_")]}


def validate(model, pack, source):
    assert model["name"] == model["model_identifier"] == pack["model"] == MODEL
    for field in source:
        if field not in ("name", "model_identifier", "animations"):
            assert model[field] == source[field], "Changed inherited rig/skin: " + field
    before = {a["name"]: a for a in source["animations"]}
    clips = {a["name"]: a for a in model["animations"]}
    assert before.keys() == clips.keys() and len(clips) == len(model["animations"])
    assert len(pack["animations"]) == 19 and pack == export(model)
    untouched = 0
    for name, clip in clips.items():
        if name not in (READY, ATTACK):
            assert clip == before[name], "Changed inherited clip: " + name
            if name.startswith("h15_"): untouched += 1
            continue
        old = before[name]
        for field in old:
            if field not in ("uuid", "snapping", "animators"):
                assert clip[field] == old[field], (name, field)
        for ident, animator in clip["animators"].items():
            bone = animator["name"]
            if bone not in LEGS + ("player_root",):
                assert animator == old["animators"][ident], "Changed upper-body channel: " + bone
            elif bone == "player_root":
                assert [k for k in animator["keyframes"] if k["channel"] != "position"] == [
                    k for k in old["animators"][ident]["keyframes"] if k["channel"] != "position"]
        # Dense half-tick regression includes complete ancestor chain/bind/root.
        max_gap = 0
        for frame in range(round(clip["length"]*40)+1):
            time = frame/40
            pose, root_y = h19.sample(clip, time)
            old_pose, old_y = h19.sample(old, time)
            assert all(math.isfinite(v) for vs in pose.values() for v in vs)
            assert root_y <= 0, "Model root must not fake real entity lift"
            assert abs(root_y-h15.floor_y(model, pose)) < .00011
            assert h20.at(clip, time, "player_root", "position")[::2] == [0, 0]
            mats, original = h19.fk(model, pose, root_y), h19.fk(source, old_pose, old_y)
            # Every upper landmark changes only by shared ground-fit Y translation.
            for bone in h15.BONES:
                if bone in LEGS: continue
                assert pose[bone] == old_pose[bone], (name, time, bone)
                for point in ([0, 0, 0], [0, 2, 8.24], [4.2, 3, -2.6], [0, 0, -1]):
                    expected = h19.add(h19.point(original[bone], point), [0, root_y-old_y, 0])
                    assert h19.norm(h19.sub(h19.point(mats[bone], point), expected)) < 1e-8
            if name == ATTACK and time <= .30:
                # Interpolated nock path is an authoring regression only; actual
                # discrete rendered bow stages still need native sent-pose tests.
                nock_z = next(z for t, z, _ in h20.VOID_STAGES if abs(t-time) < 1e-8) if frame % 2 == 0 else (
                    h20.VOID_STAGES[frame//2][1] + h20.VOID_STAGES[frame//2+1][1])/2
                error = h19.norm(h19.sub(h19.point(mats["pri_right_item"], [0, 0, 0]),
                                         h19.point(mats["pli_left_item"], [0, 2, nock_z])))
                max_gap = max(max_gap, error)
                if frame % 2 == 0: assert error < .0001, (name, time, error)
        print(f"{name}: 40Hz FK regression; max interpolated nock gap={max_gap:.6f} model units (unchanged H20 upper channels)")
    assert untouched == 17
    ready, attack = clips[READY], clips[ATTACK]
    assert h19.sample(ready, 0) == h19.sample(ready, ready["length"])
    assert h19.sample(attack, 0) == h19.sample(attack, .90) == h19.sample(ready, 0)
    assert h19.sample(attack, .25) == h19.sample(attack, .30)
    for time, nock_z, pitch in h20.VOID_STAGES:
        pose, y = h19.sample(attack, time)
        mats = h19.fk(model, pose, y)
        expected = h19.vector(h15.rot([pitch, 0, 0]), [0, 0, -1])
        assert h19.dot(h19.vector(mats["pli_left_item"], [0, 0, -1]), expected) > .99999
        if time >= .25:
            cheek = h19.point(mats["h_ph_head"], [4.2, 3, -2.6])
            assert h19.norm(h19.sub(h19.point(mats["pri_right_item"], [0, 0, 0]), cheek)) < .0001
            assert y < -2, "Clear lowering at full tuck"
            # The left knee is higher and farther forward than the right knee.
            left, right = (h19.point(mats[b], [0, 0, 0]) for b in ("plfl_left_foreleg", "prfl_right_foreleg"))
            assert left[1] > right[1]+1 and left[2] < right[2]-.5
        print(f"Void {time:.3f}s: rootY={y:.4f}; thighX={pose[LEGS[0]][0]:.1f}/{pose[LEGS[2]][0]:.1f}; kneeX={pose[LEGS[1]][0]:.1f}/{pose[LEGS[3]][0]:.1f}")
    # Dense floor envelope between authored samples, not terrain/collision proof.
    for clip in (ready, attack):
        for frame in range(round(clip["length"]*200)+1):
            pose, y = h19.sample(clip, frame/200)
            assert abs(y-h15.floor_y(model, pose)) < .025
    print("PASS: 19 clips; 17 inherited JSON-identical; unchanged rig/upper channels/native transforms; asymmetric knees; no fake flight root. Static only.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--from-art", action="store_true")
    args = parser.parse_args()
    if args.verify and args.from_art: parser.error("Choose --verify or --from-art")
    source = json.loads(SOURCE.read_text())
    model = json.loads(ART.read_text()) if args.verify or args.from_art else compose(source)
    pack = json.loads(PACK.read_text()) if args.verify else export(model)
    validate(model, pack, source)
    if not args.verify:
        if not args.from_art: ART.write_text(json.dumps(model, indent=2)+"\n")
        PACK.write_text(json.dumps(pack, indent=2)+"\n")
        print(f"Saved {ART.relative_to(ROOT)} and {PACK.relative_to(ROOT)}")


if __name__ == "__main__": main()
