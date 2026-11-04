#!/usr/bin/env python3
"""Deterministic H20 authoring on the unchanged H19/H15 segmented player rig.

rtk proxy python3 -B scripts/build_hunter_animation_h20.py
--verify reads and validates saved outputs; --from-art exports artist edits.
No Minecraft/Blockbench process, installed model, or inherited asset is modified.
"""
import argparse
import copy
import json
import math
import sys
from pathlib import Path

# Imports must not write __pycache__ in another author's shared write set.
sys.dont_write_bytecode = True
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art/blockbench/animations/guardian_hunter_h19.bbmodel"
ART = ROOT / "art/blockbench/animations/guardian_hunter_h20.bbmodel"
PACK = ROOT / "src/main/resources/destiny/animation/hunter_h20.animation.json"
MODEL = "guardian_hunter_h20"
# Integer clip ticks. Current PLAY_ONCE start transition adds one server tick.
TIMING = {
    "h15_super_arc_start": (10, {}),
    "h15_super_arc_attack": (12, {"contact": 4}),
    "h15_super_arc_end": (7, {"hide_item": 5}),
    "h15_super_solar_start": (9, {}),
    "h15_super_solar_attack": (7, {"release": 2}),
    "h15_super_solar_end": (7, {"hide_item": 5}),
    "h15_super_void_attack": (18, {"release": 6}),
    "h15_grenade": (11, {"release": 3}),
    "h15_throw": (8, {"release": 3}),
    "h15_melee_solar": (8, {"release": 3}),
    "h15_melee_void": (8, {"release": 3}),
    "h15_melee": (8, {"contact": 3}),
}
# Time, nock local Z (local Y is always 2), authored world item pitch before aim modifier.
VOID_STAGES = [(0, 3.27, -30), (.05, 3.27, -20), (.10, 3.27, -12),
               (.15, 5.00, -6), (.20, 6.75, -2), (.25, 8.24, 0), (.30, 8.24, 0)]


def mix(a, b, fraction):
    return {bone: [x+(y-x)*fraction for x, y in zip(a[bone], b[bone])] for bone in h15.BONES}


def stance(yaw=0, lean=0, crouch=1):
    return h15.pose(phip_hip=[-5*crouch, yaw*.25, 0], pw_waist=[-2*crouch, -yaw*.15, 0],
                    pc_chest=[lean, yaw, -2], h_ph_head=[-lean+3, -yaw, 0],
                    prl_right_leg=[-14*crouch, -8, -7*crouch], prfl_right_foreleg=[23*crouch, 0, 0],
                    pll_left_leg=[9*crouch, 12, 8*crouch], plfl_left_foreleg=[12*crouch, 0, 0],
                    cape_cape=[9*crouch, 0, 2])


def aim_right(model, pose, desired):
    fore = h19.fk(model, pose)["prfa_right_forearm"]
    local = h19.euler(h15.mm(h19.inverse_rotation(fore), desired))
    bind = next(g for g in model["groups"] if g["name"] == "pri_right_item")["rotation"]
    pose["pri_right_item"] = h19.sub(local, bind)


def staff_pose(model, yaw, wrist, angles, lean=-3):
    p = stance(yaw, lean)
    matrix = h15.rot(angles)
    support = h19.add(wrist, h19.vector(matrix, [0, 6, 0]))
    h19.solve_arm(model, p, "right", wrist, [.8, -1, .2])
    h19.solve_arm(model, p, "left", support, [-.8, -1, .2])
    aim_right(model, p, matrix)
    return p


def gun_pose(model, wrist, pitch=0, yaw=10, lean=-2):
    p = stance(yaw, lean, .65)
    h19.solve_arm(model, p, "right", wrist, [.4, -1, .2])
    h19.solve_arm(model, p, "left", [-3.6, 18.2, -4.1], [-1, -1, .3])
    # Existing gun barrel is local +Z. Rotate it to world -Z, then pitch recoil upward.
    aim_right(model, p, h15.mm(h15.rot([pitch, 0, 0]), h15.rot([0, 180, 0])))
    return p


def scale_keys(clip, bone, values):
    animator = next(a for a in clip["animators"].values() if a["name"] == bone)
    for time, scale in values:
        animator["keyframes"].append({"uuid": h15.uid(f"{clip['name']}/{bone}/scale/{time}"),
            "channel": "scale", "time": time, "interpolation": "linear",
            "data_points": [dict.fromkeys("xyz", scale)]})


def new_clip(model, name, frames, loop=False, scales=None):
    # Full-body keys are linear: exact holds/contacts, no Catmull-Rom overshoot or windup drift.
    clip = h19.new_clip(model, name, frames, loop)
    root = next(a for a in clip["animators"].values() if a["name"] == "player_root")
    root["keyframes"] = [k for k in root["keyframes"] if k["channel"] != "position"]
    # Dense, bounded visual Y correction only. No horizontal root motion / entity teleport.
    rate = 100 if name.startswith("h15_roll_") else 40
    times = sorted({round(i/rate, 6) for i in range(round(clip["length"]*rate)+1)}
                   | {t for t, _ in frames})
    for time in times:
        p, _ = h19.sample(clip, time)
        root["keyframes"].append({"uuid": h15.uid(f"{name}/player_root/position/{time}"),
            "channel": "position", "time": time, "interpolation": "linear",
            "data_points": [{"x": 0, "y": h15.floor_y(model, p), "z": 0}]})
    # Explicit unit-scale endpoints prevent a previous summon/end leaking into ready/attack.
    scale_keys(clip, "pri_right_item", scales or [(0, 1), (clip["length"], 1)])
    scale_keys(clip, "pli_left_item", [(0, 1), (clip["length"], 1)])
    return clip



def densify_staff_support(model, clip):
    """Preserve authored keys/right-hand motion; re-solve support at each 25ms frame.

    Native staff (8,12,8), centered then translated +2Y, is local (0,6,0).
    DisplayRenderer's inner Ry180 leaves that +Y target unchanged. BM's X/Z
    basis conversion therefore preserves this authoring-space contact equation.
    This is an asset constraint, not a substitute for sent-snapshot/render tests.
    """
    original = copy.deepcopy(clip)
    times = {k["time"] for a in original["animators"].values()
             for k in a["keyframes"] if k["channel"] == "rotation"}
    for frame in range(round(clip["length"]*40)+1):
        time = frame/40
        if time in times: continue  # Keep every original silhouette/key verbatim.
        pose, _ = h19.sample(original, time)
        interpolated = copy.deepcopy(pose)
        right = h19.fk(model, pose)["pri_right_item"]
        h19.solve_arm(model, pose, "left", h19.point(right, [0, 6, 0]), [-.8, -1, .2])
        for animator in clip["animators"].values():
            bone = animator["name"]
            # Use the Euler branch nearest the old local trajectory; no 360-degree detours.
            angles = [v+360*round((old-v)/360) for v, old in zip(pose[bone], interpolated[bone])]
            animator["keyframes"].append({
                "uuid": h15.uid(f"{clip['name']}/{bone}/rotation/{time}"),
                "channel": "rotation", "time": time, "interpolation": "linear",
                "data_points": [dict(zip("xyz", [round(v, 6) for v in angles]))]})
    for animator in clip["animators"].values():
        animator["keyframes"].sort(key=lambda k: k["time"])
    clip["snapping"] = 40
    return clip

def arc_clips(model):
    ready = staff_pose(model, -12, [3, 17.8, -5.5], [4, -10, 62])
    coil1 = staff_pose(model, -25, [4, 18.2, -4.3], [12, -20, 48], -6)
    coil2 = staff_pose(model, -35, [4.5, 18.5, -3.5], [18, -28, 36], -8)
    drive = staff_pose(model, -8, [4.8, 20.2, -7], [7, -10, 68], -9)
    contact = staff_pose(model, 22, [3.8, 20.4, -8.1], [0, 0, 102], -7)
    follow = staff_pose(model, 34, [2.5, 19.7, -5.8], [-10, 22, 122], -4)
    recover = staff_pose(model, 16, [2.7, 17.7, -6], [-4, 12, 92], -2)
    breathe = h15.changed(ready, cape_cape=[12, 0, 3])
    idle = new_clip(model, "h15_super_arc", [(0, ready), (.4, breathe), (.8, ready),
                    (1.2, h15.changed(ready, cape_cape=[10, 0, 1])), (1.6, ready)], True)
    attack = new_clip(model, "h15_super_arc_attack", [(0, ready), (.05, coil1), (.10, coil2),
            (.15, drive), (.20, contact), (.25, follow), (.30, copy.deepcopy(follow)),
            (.40, recover), (.50, staff_pose(model, -5, [2.9, 17.8, -5.7], [1, 0, 72])), (.60, ready)])
    attack = densify_staff_support(model, attack)
    neutral = h15.zero()
    gather = mix(neutral, coil1, .65)
    start = new_clip(model, "h15_super_arc_start", [(0, neutral), (.10, gather), (.20, coil1),
            (.30, coil2), (.40, ready), (.50, ready)],
            scales=[(0, .001), (.10, .001), (.20, .35), (.30, 1), (.50, 1)])
    lower = mix(ready, neutral, .65)
    end = new_clip(model, "h15_super_arc_end", [(0, ready), (.10, recover), (.20, lower),
            (.25, mix(lower, neutral, .6)), (.35, neutral)],
            scales=[(0, 1), (.10, 1), (.20, .4), (.25, .001), (.35, .001)])
    return [idle, attack, start, end]


def solar_clips(model):
    ready = gun_pose(model, [4.3, 21.0, -9.0])
    recoil1 = gun_pose(model, [4.4, 21.7, -8.0], 12, 12, 3)
    recoil2 = gun_pose(model, [4.3, 21.5, -8.3], 9, 11, 2)
    settle = gun_pose(model, [4.3, 21.1, -8.8], 2, 10, -1)
    idle = new_clip(model, "h15_super_solar", [(0, ready),
            (.5, h15.changed(ready, cape_cape=[8, 0, 1])), (1, ready),
            (1.5, h15.changed(ready, cape_cape=[7, 0, -1])), (2, ready)], True)
    attack = new_clip(model, "h15_super_solar_attack", [(0, ready), (.05, copy.deepcopy(ready)),
            (.10, copy.deepcopy(ready)), (.15, recoil1), (.20, recoil2), (.25, settle), (.35, ready)])
    neutral = h15.zero()
    draw = gun_pose(model, [5, 16, -2.5], 55, 3, 0)
    lift = gun_pose(model, [5, 20, -6], 25, 7, -1)
    start = new_clip(model, "h15_super_solar_start", [(0, neutral), (.10, mix(neutral, draw, .6)),
            (.15, draw), (.20, lift), (.30, ready), (.45, ready)],
            scales=[(0, .001), (.15, .001), (.20, .4), (.30, 1), (.45, 1)])
    end = new_clip(model, "h15_super_solar_end", [(0, ready), (.10, lift), (.20, draw),
            (.25, mix(draw, neutral, .5)), (.35, neutral)],
            scales=[(0, 1), (.10, 1), (.20, .4), (.25, .001), (.35, .001)])
    return [idle, attack, start, end]


def void_clips(model):
    # H19 handed conversion/rig remain intact. Each server-tick bow stage gets its own IK solution.
    low = h19.authored_pose(model, -28, [-3, 17.5, -4.5], [0, 2, 3.27], -30)
    raise_left = [.2, 21, -7.8]
    cheek = h19.point(h19.fk(model, h19.body(-42))["h_ph_head"], [4.2, 3, -2.6])
    full_left = h19.sub(cheek, [0, 2, 8.24])
    wrists = [[-3, 17.5, -4.5], [-1.4, 19.3, -6.2], raise_left,
              h19.add(h19.mul(raise_left, .55), h19.mul(full_left, .45)),
              h19.add(h19.mul(raise_left, .2), h19.mul(full_left, .8)), full_left, full_left]
    frames = []
    for (time, nock_z, pitch), wrist, yaw in zip(VOID_STAGES, wrists, [-28, -31, -34, -37, -40, -42, -42]):
        frames.append((time, h19.authored_pose(model, yaw, wrist, [0, 2, nock_z], pitch)))
    follow = h19.authored_pose(model, -42, full_left, [0, 2, 8.24], release_offset=[1.1, .35, 1.4])
    settle = h19.authored_pose(model, -37, [1, 21.5, -8.8], [0, 2, 8.24], -12,
                              release_offset=[1, -.5, .6])
    frames += [(.35, follow), (.45, copy.deepcopy(follow)), (.60, settle),
               (.75, h15.changed(low, cape_cape=[13, 0, 4])), (.90, low)]
    # Preserve the original H19 ready exactly; only the attack's intermediate stages change.
    return new_clip(model, "h15_super_void_attack", frames)


def skill_pose(model, wrist, yaw, lean, left=(-4, 19.5, -3)):
    p = stance(yaw, lean, .8)
    h19.solve_arm(model, p, "right", wrist, [.8, -1, .3])
    h19.solve_arm(model, p, "left", list(left), [-1, -1, .3])
    return p


def skill_clips(model):
    neutral = h15.zero()
    wind = skill_pose(model, [6, 23, 1], -24, -7)
    cock = skill_pose(model, [5, 24, -3], -15, -6)
    release = skill_pose(model, [3.5, 23, -9], 16, -10)
    follow = skill_pose(model, [2.5, 18, -8.5], 25, -6)
    grenade = new_clip(model, "h15_grenade", [(0, neutral), (.05, mix(neutral, wind, .5)),
            (.10, cock), (.15, release), (.20, follow), (.25, copy.deepcopy(follow)),
            (.35, mix(follow, neutral, .4)), (.45, mix(follow, neutral, .8)), (.55, neutral)])
    guard = skill_pose(model, [4.5, 19.5, -2], -12, -5)
    chamber = skill_pose(model, [5.5, 20.2, -.5], -24, -7)
    contact = skill_pose(model, [3.5, 20.8, -9.8], 14, -9)
    follow = skill_pose(model, [3.5, 20.2, -8.8], 20, -6)
    melee = new_clip(model, "h15_melee", [(0, neutral), (.05, guard), (.10, chamber),
            (.15, contact), (.20, follow), (.25, guard), (.30, mix(guard, neutral, .6)), (.40, neutral)])
    solar_wind = skill_pose(model, [6, 23.5, -.5], -20, -5)
    solar_release = skill_pose(model, [3.5, 22, -9], 12, -8)
    solar_follow = skill_pose(model, [3.5, 19, -8], 22, -5)
    solar = [(0, neutral), (.05, solar_wind), (.10, copy.deepcopy(solar_wind)),
             (.15, solar_release), (.20, solar_follow), (.30, mix(solar_follow, neutral, .65)), (.40, neutral)]
    # Smoke uses a lower, underhand cast rather than recycling the knife's high elbow.
    void_wind = skill_pose(model, [5.5, 15, 1], -16, -4)
    void_cock = skill_pose(model, [5, 16, -2], -12, -5)
    void_release = skill_pose(model, [3.5, 18.5, -8.8], 10, -7)
    void_follow = skill_pose(model, [2.5, 19, -7], 16, -4)
    smoke = [(0, neutral), (.05, void_wind), (.10, void_cock), (.15, void_release),
             (.20, void_follow), (.30, mix(void_follow, neutral, .65)), (.40, neutral)]
    return [grenade, melee, new_clip(model, "h15_throw", solar),
            new_clip(model, "h15_melee_solar", solar), new_clip(model, "h15_melee_void", smoke)]


def head_bounds(model, matrices):
    # The original, unchanged Steve head skin spans these pivot-relative corners.
    matrix = matrices["h_ph_head"]
    corners = [h19.point(matrix, [x, y, z]) for x in (-3.75, 3.75)
               for y in (0, 7.5) for z in (-3.75, 3.75)]
    return h19.point(matrix, [0, 3.75, 0]), min(v[1] for v in corners)


def protect_roll_head(model, pose):
    # A guarding forearm, not the skull, leads the inverted part of the roll.
    matrices = h19.fk(model, pose)
    center, bottom = head_bounds(model, matrices)
    reached = 0
    for side, sign, arm in (("right", 1, "pra_right_arm"), ("left", -1, "pla_left_arm")):
        shoulder = h19.point(matrices[arm], [0, 0, 0])
        target = [center[0]+math.copysign(2, shoulder[0]-center[0]), bottom-.8, center[2]]
        if .2 < h19.norm(h19.sub(target, shoulder)) < 11.1:
            h19.solve_arm(model, pose, side, target, [sign, -.2, -1])
            reached += 1
    assert reached, ("At least one protective forearm must reach below the head", pose["player_root"], center, bottom)


def roll_clip(model, direction):
    # Preserve the four direction IDs/full-turn signs; improve shoulder lead and planted recovery.
    times = [0, .05, .10, .15, .20, .30, .40, .50, .60, .70]
    turns = [0, 7, -24, -62, -105, -190, -272, -328, -355, -360]
    tucks = [0, .3, .75, .95, 1, 1, .82, .45, .12, 0]
    axis = 0 if direction in ("forward", "back") else 2
    sign = -1 if direction in ("back", "left") else 1
    frames = []
    for time, angle, tuck in zip(times, turns, tucks):
        p = h15.pose(phip_hip=[-22*tuck, 0, 0], pw_waist=[-18*tuck, 0, 0],
                    pc_chest=[-24*tuck, 0, 0], h_ph_head=[28*tuck, 0, 0],
                    pra_right_arm=[48*tuck, -10*tuck, -24*tuck], prfa_right_forearm=[95*tuck, 0, 0],
                    pla_left_arm=[55*tuck, 10*tuck, 28*tuck], plfa_left_forearm=[105*tuck, 0, 0],
                    prl_right_leg=[-62*tuck, 0, -10*tuck], prfl_right_foreleg=[108*tuck, 0, 0],
                    pll_left_leg=[-48*tuck, 0, 10*tuck], plfl_left_foreleg=[94*tuck, 0, 0],
                    cape_cape=[30*tuck, 0, 0])
        p["player_root"][axis] = angle*sign
        shoulder = (1 if direction == "left" else -1) if axis == 2 else 0
        p["pc_chest"][2] = shoulder*9*tuck
        p["pra_right_arm"][2] -= shoulder*16*tuck
        p["pla_left_arm"][2] -= shoulder*16*tuck
        if .10 <= time <= .40: protect_roll_head(model, p)
        frames.append((time, p))
    return new_clip(model, "h15_roll_"+direction, frames)


def compose(source):
    model = copy.deepcopy(source)
    model["name"] = model["model_identifier"] = MODEL
    clips = arc_clips(model) + solar_clips(model) + skill_clips(model)
    clips += [void_clips(model)] + [roll_clip(model, d) for d in ("forward", "back", "left", "right")]
    replacements = {a["name"]: a for a in clips}
    model["animations"] = [replacements.pop(a["name"], a) for a in model["animations"]]
    model["animations"] += list(replacements.values())
    return model


def export(model):
    return {"model": MODEL, "animations": [a for a in model["animations"] if a["name"].startswith("h15_")]}


def at(clip, time, bone, channel="rotation"):
    animator = next(a for a in clip["animators"].values() if a["name"] == bone)
    keys = sorted((k for k in animator["keyframes"] if k["channel"] == channel), key=lambda k: k["time"])
    assert keys, (clip["name"], bone, channel)
    lo = max((k for k in keys if k["time"] <= time+1e-9), key=lambda k: k["time"], default=keys[0])
    hi = min((k for k in keys if k["time"] >= time-1e-9), key=lambda k: k["time"], default=keys[-1])
    t = (time-lo["time"])/(hi["time"]-lo["time"]) if hi["time"] != lo["time"] else 0
    return [lo["data_points"][0][axis]+t*(hi["data_points"][0][axis]-lo["data_points"][0][axis]) for axis in "xyz"]


def validate(model, pack, source):
    assert model["name"] == model["model_identifier"] == pack["model"] == MODEL
    for key in source:
        if key not in ("name", "model_identifier", "animations"):
            assert model[key] == source[key], "Original rig/skin changed: " + key
    original = {a["name"]: a for a in source["animations"]}
    clips = {a["name"]: a for a in model["animations"]}
    assert len(clips) == len(model["animations"]) == len(original)+9
    assert clips["h15_super_void"] == original["h15_super_void"], "H19 ready must be inherited verbatim"
    for name in original:
        if not name.startswith("h15_"): assert clips[name] == original[name], name
    assert len(pack["animations"]) == 19 and pack == export(model)
    group_ids = {g["name"]: g["uuid"] for g in model["groups"]}
    parents = {}
    def walk(nodes, parent=None):
        for node in nodes:
            if isinstance(node, dict):
                parents[node["uuid"]] = parent
                walk(node["children"], node["uuid"])
    walk(model["outliner"])
    for name in ("h_ph_head", "pra_right_arm", "pla_left_arm"):
        assert parents[group_ids[name]] == group_ids["pc_chest"], "Whole upper-body aim needs the same chest ancestor"
    uuids = set()
    for clip in pack["animations"]:
        assert clip["uuid"] not in uuids
        uuids.add(clip["uuid"])
        assert set(clip["animators"]) == {group_ids[b] for b in h15.BONES}
        for animator in clip["animators"].values():
            for channel in {k["channel"] for k in animator["keyframes"]}:
                keys = [k for k in animator["keyframes"] if k["channel"] == channel]
                times = [k["time"] for k in keys]
                assert 0 == min(times) and max(times) == clip["length"]
                assert len(times) == len(set(times)) and len(times) <= 256
                for key in keys:
                    assert key["uuid"] not in uuids
                    uuids.add(key["uuid"])
                    assert all(math.isfinite(v) for v in key["data_points"][0].values())
                    if clip["name"] != "h15_super_void": assert key["interpolation"] == "linear"
        for i in range(round(clip["length"]*100)+1):
            time = i/100
            p, root_y = h19.sample(clip, time)
            assert all(math.isfinite(v) for values in p.values() for v in values)
            x, y, z = at(clip, time, "player_root", "position")
            assert x == z == 0 and abs(y) < 32, (clip["name"], time, y)
            # Lowest skin-cube check; not terrain/armor/physics/engine validation.
            if clip["name"] != "h15_super_void":
                assert abs(root_y-h15.floor_y(model, p)) < .15, ("ground envelope", clip["name"], time)
        if clip["loop"] == "loop": assert h19.sample(clip, 0) == h19.sample(clip, clip["length"])
    for name, (length, markers) in TIMING.items():
        clip = clips[name]
        assert abs(clip["length"]*20-length) < 1e-8 and clip["loop"] == "once"
        all_times = {k["time"] for a in clip["animators"].values() for k in a["keyframes"]}
        for tick in markers.values(): assert tick/20 in all_times
        print(f"{name}: length={length}+1 transition; " + ", ".join(f"{k}={v}+1" for k, v in markers.items()))
    for element in ("arc", "solar"):
        ready, attack = clips[f"h15_super_{element}"], clips[f"h15_super_{element}_attack"]
        assert h19.sample(attack, 0) == h19.sample(attack, attack["length"]) == h19.sample(ready, 0)
        assert h19.sample(clips[f"h15_super_{element}_start"], clips[f"h15_super_{element}_start"]["length"]) == h19.sample(ready, 0)
        for suffix in ("start", "end"):
            clip = clips[f"h15_super_{element}_{suffix}"]
            scale = at(clip, 0 if suffix == "start" else .25, "pri_right_item", "scale")
            assert scale == [.001]*3
    for direction, axis, sign in [("forward", 0, -1), ("back", 0, 1), ("left", 2, 1), ("right", 2, -1)]:
        clip = clips["h15_roll_"+direction]
        assert clip["length"] == .7 and at(clip, .7, "player_root")[axis] == sign*360
        assert all(at(clip, t, "player_root")[1] == 0 for t in (0, .2, .4, .7))
        for time in (.20, .30, .40):
            pose, root_y = h19.sample(clip, time)
            _, head_bottom = head_bounds(model, h19.fk(model, pose, root_y))
            assert head_bottom > .25, ("Head must not be the ground contact", direction, time, head_bottom)
    for time in (0, .05, .10):
        assert h19.sample(clips["h15_super_solar_attack"], time) == h19.sample(clips["h15_super_solar_attack"], 0)
    # IK contracts on tick-aligned poses, including the display translation and complete ancestor chain.
    void = clips["h15_super_void_attack"]
    for time, nock_z, pitch in VOID_STAGES:
        p, root_y = h19.sample(void, time)
        matrices = h19.fk(model, p, root_y)
        right = h19.point(matrices["pri_right_item"], [0, 0, 0])
        nock = h19.point(matrices["pli_left_item"], [0, 2, nock_z])
        error = h19.norm(h19.sub(right, nock))
        expected = h19.vector(h15.rot([pitch, 0, 0]), [0, 0, -1])
        assert error < .0001 and h19.dot(h19.vector(matrices["pli_left_item"], [0, 0, -1]), expected) > .99999
        print(f"Void {time:.2f}s: nock=(0,2,{nock_z:.2f}), pitch={pitch}, wrist error={error:.7f} model units")
    assert h19.sample(void, .25) == h19.sample(void, .30), "Full draw holds until release"
    assert h19.sample(void, 0) == h19.sample(void, .90) == h19.sample(clips["h15_super_void"], 0)
    for time in (.25, .30):
        pose, root_y = h19.sample(void, time)
        matrices = h19.fk(model, pose, root_y)
        cheek = h19.point(matrices["h_ph_head"], [4.2, 3, -2.6])
        wrist = h19.point(matrices["pri_right_item"], [0, 0, 0])
        assert h19.norm(h19.sub(wrist, cheek)) < .0001
    for name in ("h15_super_arc", "h15_super_arc_attack"):
        clip = clips[name]
        # Check every authoritative 40Hz sample, not only sparse contact keys.
        times = [frame/40 for frame in range(round(clip["length"]*40)+1)]
        if name.endswith("_attack"):
            for animator in clip["animators"].values():
                assert [k["time"] for k in animator["keyframes"] if k["channel"] == "rotation"] == times
        for time in times:
            pose, root_y = h19.sample(clip, time)
            matrices = h19.fk(model, pose, root_y)
            support = h19.point(matrices["pri_right_item"], [0, 6, 0])
            left = h19.point(matrices["pli_left_item"], [0, 0, 0])
            assert h19.norm(h19.sub(support, left)) < .0001, ("staff support", name, time)
    print("PASS: 19 H15-compatible H20 clips; unchanged rig/skin/hierarchy; staged Void IK; static authoring checks only.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Validate saved outputs without writing")
    parser.add_argument("--from-art", action="store_true", help="Export edited H20 artist file without regenerating it")
    args = parser.parse_args()
    if args.verify and args.from_art: parser.error("Choose either --verify or --from-art")
    source = json.loads(SOURCE.read_text())
    if args.verify:
        model, pack = json.loads(ART.read_text()), json.loads(PACK.read_text())
    else:
        model = json.loads(ART.read_text()) if args.from_art else compose(source)
        pack = export(model)
    validate(model, pack, source)
    if not args.verify:
        ART.parent.mkdir(parents=True, exist_ok=True)
        PACK.parent.mkdir(parents=True, exist_ok=True)
        if not args.from_art: ART.write_text(json.dumps(model, indent=2)+"\n")
        PACK.write_text(json.dumps(pack, indent=2)+"\n")
        print(f"Saved {ART.relative_to(ROOT)} and {PACK.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
