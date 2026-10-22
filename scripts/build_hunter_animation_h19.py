#!/usr/bin/env python3
"""H19 Shadowshot authoring; only replaces H15 Void ready/attack clips.

Run: rtk proxy python3 scripts/build_hunter_animation_h19.py
Verify saved files without writing: add --verify. Export artist edits: --from-art.
References: art/blockbench/supers/references/Shadowshot{,2}.jpg (Bungie).
Read the extended support arm, cheek anchor and high/back draw elbow from the
references, adapted to the unchanged segmented Steve skin/armor rig.

Static FK uses the existing authoring pipeline's Rz*Ry*Rx group rotations,
+X right, +Y up, front -Z; Rx(+90) turns a downward arm toward -Z.
All ancestors, bind rotations, equipment pivots and root translation are included.
Bow contract: model grip (8,8,8), nock X=11.27 / 16.24, left display
Ry(-90), translation (0,2,0). Thus world item identity aims arrow -X along
world -Z, and the drawn nock is wrist+(0,2,8.24). Item rotations cancel
the complete arm chain AND the bind Rx(-90); they are not hand-wave offsets.
This is static/non-game verification, not a Blockbench or native-client check.
Minecraft/BetterModel handed display conversion still requires pixel inspection.
No build, client/server launch, runtime changes, or H15 writes.
"""
import argparse
import copy
import json
import math
from pathlib import Path

import build_hunter_animation_h15 as h15

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art/blockbench/animations/guardian_hunter_h15.bbmodel"
ART = ROOT / "art/blockbench/animations/guardian_hunter_h19.bbmodel"
PACK = ROOT / "src/main/resources/destiny/animation/hunter_h19.animation.json"
MODEL = "guardian_hunter_h19"
READY = "h15_super_void"
ATTACK = READY + "_attack"
RELEASE = .30  # six clip ticks + one start-transition tick = elapsed seven.
GRIP_OFFSET = [0, 2, 0]
REST_NOCK = [0, 2, 3.27]
DRAWN_NOCK = [0, 2, 8.24]


def add(a, b): return [x+y for x, y in zip(a, b)]
def sub(a, b): return [x-y for x, y in zip(a, b)]
def mul(a, s): return [x*s for x in a]
def dot(a, b): return sum(x*y for x, y in zip(a, b))
def norm(a): return math.sqrt(dot(a, a))
def unit(a): return mul(a, 1/norm(a))
def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def point(matrix, value):
    return [sum(matrix[i][j]*value[j] for j in range(3))+matrix[i][3] for i in range(3)]


def vector(matrix, value):
    return [sum(matrix[i][j]*value[j] for j in range(3)) for i in range(3)]


def inverse_rotation(matrix):
    return [[matrix[j][i] if i < 3 and j < 3 else int(i == j)
             for j in range(4)] for i in range(4)]


def euler(matrix):
    # Inverse of h15.rot: Rz*Ry*Rx, avoiding a gratuitous Euler wrap.
    y = math.asin(max(-1, min(1, -matrix[2][0])))
    assert abs(math.cos(y)) > 1e-6, "Unexpected gimbal lock"
    return [math.degrees(math.atan2(matrix[2][1], matrix[2][2])),
            math.degrees(y), math.degrees(math.atan2(matrix[1][0], matrix[0][0]))]


def fk(model, rotations, root_y=0):
    groups = {g["uuid"]: g for g in model["groups"]}
    result = {}
    def walk(nodes, parent, parent_origin):
        for node in nodes:
            if isinstance(node, str): continue
            g = groups[node["uuid"]]
            angles = add(g.get("rotation", [0, 0, 0]), rotations.get(g["name"], [0, 0, 0]))
            offset = sub(g["origin"], parent_origin)
            if g["name"] == "player_root": offset[1] += root_y
            matrix = h15.mm(parent, h15.mm(h15.tr(offset), h15.rot(angles)))
            result[g["name"]] = matrix
            walk(node["children"], matrix, g["origin"])
    walk(model["outliner"], h15.tr([0, 0, 0]), [0, 0, 0])
    return result


def solve_arm(model, pose, side, wrist, elbow_bias):
    """Two-link IK to the actual equipment pivot, including its +/- .625 X offset.

    Elbow bends only about local +X. Shoulder twist accounts for the transverse
    wrist offset, so contact is solved against the real rig, not a nominal 11u arm.
    """
    upper, fore, item = (("pla_left_arm", "plfa_left_forearm", "pli_left_item") if side == "left"
                         else ("pra_right_arm", "prfa_right_forearm", "pri_right_item"))
    groups = {g["name"]: g for g in model["groups"]}
    matrices = fk(model, pose)
    shoulder = point(matrices[upper], [0, 0, 0])
    a = groups[item]["origin"][0]-groups[fore]["origin"][0]
    l1 = norm(sub(groups[fore]["origin"], groups[upper]["origin"]))
    longitudinal = groups[fore]["origin"][1]-groups[item]["origin"][1]
    l2 = math.hypot(longitudinal, a)
    delta = sub(wrist, shoulder)
    distance = norm(delta)
    assert abs(l1-l2) < distance < l1+l2, (side, wrist, shoulder, distance)
    along = unit(delta)
    center = (l1*l1-l2*l2+distance*distance)/(2*distance)
    radius = math.sqrt(max(0, l1*l1-center*center))
    swivel = unit(sub(elbow_bias, mul(along, dot(elbow_bias, along))))
    elbow = add(shoulder, add(mul(along, center), mul(swivel, radius)))
    down = unit(sub(elbow, shoulder))
    end = sub(wrist, elbow)
    bend = math.acos(max(-1, min(1, dot(end, down)/longitudinal)))
    perpendicular = unit(sub(end, mul(down, dot(end, down))))
    y_axis = mul(down, -1)
    z0 = mul(perpendicular, -1)
    x0 = cross(y_axis, z0)
    twist = -math.atan2(a, longitudinal*math.sin(bend))
    x_axis = add(mul(x0, math.cos(twist)), mul(z0, math.sin(twist)))
    z_axis = add(mul(x0, -math.sin(twist)), mul(z0, math.cos(twist)))
    world = [[x_axis[i], y_axis[i], z_axis[i], 0] for i in range(3)]+[[0, 0, 0, 1]]
    local = h15.mm(inverse_rotation(matrices["pc_chest"]), world)
    pose[upper] = sub(euler(local), groups[upper].get("rotation", [0, 0, 0]))
    pose[fore] = [math.degrees(bend), 0, 0]
    actual = point(fk(model, pose)[item], [0, 0, 0])
    assert norm(sub(actual, wrist)) < 1e-6, (side, actual, wrist)


def aim_item(model, pose, world_pitch):
    """Cancel bind -90 X and all torso/arm rotations before display Ry(-90)."""
    fore = fk(model, pose)["plfa_left_forearm"]
    desired = h15.rot([world_pitch, 0, 0])
    local = euler(h15.mm(inverse_rotation(fore), desired))
    bind = next(g for g in model["groups"] if g["name"] == "pli_left_item")["rotation"]
    pose["pli_left_item"] = sub(local, bind)


def body(yaw, lean=0):
    return h15.pose(player_root=[0, -3, 0], phip_hip=[-2, 9, 0],
                    pw_waist=[1, -4, 0], pc_chest=[1+lean, yaw-2, 0],
                    h_ph_head=[-lean, -yaw, 0],
                    prl_right_leg=[-13, -12, -7], prfl_right_foreleg=[20, 0, 0],
                    pll_left_leg=[11, 16, 9], plfl_left_foreleg=[12, 0, 0],
                    cape_cape=[9, 0, 3])


def authored_pose(model, yaw, left, nock, pitch=0, lean=0, release_offset=None):
    pose = body(yaw, lean)
    right = add(left, vector(h15.rot([pitch, 0, 0]), nock))
    if release_offset is not None: right = add(right, release_offset)
    solve_arm(model, pose, "left", left, [-.2, -1, -.1])
    solve_arm(model, pose, "right", right, [1, .15, 1])
    aim_item(model, pose, pitch)
    return pose


def frames(model):
    # Hands remain on grip/nock while raising. At .15 the runtime drawn variant
    # appears (elapsed tick four including its transition); .25-.30 is the hold.
    low = authored_pose(model, -28, [-3, 17.5, -4.5], REST_NOCK, -30)
    raise_pose = authored_pose(model, -34, [.2, 21, -7.8], REST_NOCK, -12)
    head = point(fk(model, body(-42))["h_ph_head"], [4.2, 3, -2.6])
    # Make the drawn string meet the cheek, rather than guessing Euler angles.
    full_left = sub(head, DRAWN_NOCK)
    full = authored_pose(model, -42, full_left, DRAWN_NOCK)
    draw_left = add(mul([.2, 21, -7.8], .35), mul(full_left, .65))
    draw = authored_pose(model, -39, draw_left, [0, 2, 6.0], -3)
    follow = authored_pose(model, -42, full_left, DRAWN_NOCK, release_offset=[1.1, .35, 1.4])
    settle = authored_pose(model, -37, [1.0, 21.5, -8.8], DRAWN_NOCK, -12,
                           release_offset=[1.0, -.5, .6])
    return low, [(0, low), (.10, raise_pose), (.15, draw), (.25, full),
                 (RELEASE, copy.deepcopy(full)), (.35, follow), (.45, copy.deepcopy(follow)),
                 (.60, settle), (.75, h15.changed(low, cape_cape=[13, 0, 4])), (.90, low)]


def new_clip(model, name, keys, loop=False):
    result = h15.clip(model, name, keys, loop=loop)
    # Linear interpolation prevents Catmull-Rom pre-release drift/overshoot and
    # Euler-loop flourishes. The paired .25/.30 keys form an exact draw hold.
    result["snapping"] = 20
    for animator in result["animators"].values():
        for key in animator["keyframes"]:
            key["interpolation"] = "linear"
            key["data_points"][0] = {axis: round(float(v), 6) for axis, v in key["data_points"][0].items()}
    # Keep adjacent Euler representations continuous without changing orientations.
    for animator in result["animators"].values():
        previous = None
        for key in animator["keyframes"]:
            if key["channel"] != "rotation": continue
            values = key["data_points"][0]
            if previous is not None:
                for axis in "xyz":
                    while values[axis]-previous[axis] > 180: values[axis] -= 360
                    while values[axis]-previous[axis] < -180: values[axis] += 360
            previous = values.copy()
    return result


def sample(clip, time):
    pose, root_y = {}, 0
    for animator in clip["animators"].values():
        for channel in ("rotation", "position"):
            keys = sorted((k for k in animator["keyframes"] if k["channel"] == channel), key=lambda k: k["time"])
            if not keys: continue
            before = max((k for k in keys if k["time"] <= time), key=lambda k: k["time"], default=keys[0])
            after = min((k for k in keys if k["time"] >= time), key=lambda k: k["time"], default=keys[-1])
            span = after["time"]-before["time"]
            fraction = (time-before["time"])/span if span else 0
            a, b = before["data_points"][0], after["data_points"][0]
            value = [a[axis]+fraction*(b[axis]-a[axis]) for axis in "xyz"]
            if channel == "rotation": pose[animator["name"]] = value
            elif animator["name"] == "player_root": root_y = value[1]
    return pose, root_y


def landmarks(model, clip, time):
    pose, root_y = sample(clip, time)
    matrices = fk(model, pose, root_y)
    left = point(matrices["pli_left_item"], [0, 0, 0])
    right = point(matrices["pri_right_item"], [0, 0, 0])
    return dict(left=left, right=right,
                elbow=point(matrices["prfa_right_forearm"], [0, 0, 0]),
                head=point(matrices["h_ph_head"], [0, 0, 0]),
                cheek=point(matrices["h_ph_head"], [4.2, 3, -2.6]),
                grip=point(matrices["pli_left_item"], GRIP_OFFSET),
                nock=point(matrices["pli_left_item"], DRAWN_NOCK),
                rest_nock=point(matrices["pli_left_item"], REST_NOCK),
                arrow=vector(matrices["pli_left_item"], [0, 0, -1]),
                shoulder=point(matrices["pla_left_arm"], [0, 0, 0]))


def validate(model, pack, source):
    assert model["name"] == model["model_identifier"] == pack["model"] == MODEL
    for key in source:
        if key not in ("name", "model_identifier", "animations"):
            assert model[key] == source[key], "Changed original rig/skin: " + key
    original = {a["name"]: a for a in source["animations"]}
    animations = {a["name"]: a for a in model["animations"]}
    assert len(animations) == len(model["animations"]) == len(original)
    assert animations.keys() == original.keys()
    for name in animations:
        if name not in (READY, ATTACK): assert animations[name] == original[name], name
    exported = [a for a in model["animations"] if a["name"].startswith("h15_")]
    assert len(exported) == 10 and pack["animations"] == exported
    attack, ready = animations[ATTACK], animations[READY]
    assert attack["length"] == .90 and ready["loop"] == "loop" and ready["length"] == 2.4
    assert sample(attack, 0) == sample(attack, .90) == sample(ready, 0) == sample(ready, 2.4)
    assert sample(attack, .25) == sample(attack, .30), "No movement before .30 release"
    for t in (.25, .275, .30):
        p = landmarks(model, attack, t)
        assert norm(sub(p["right"], p["cheek"])) < .01, ("cheek", t, p)
        assert norm(sub(p["right"], p["nock"])) < .01, ("nock", t, p)
        assert norm(sub(p["left"], p["shoulder"])) > 10.4, ("support extension", p)
        assert p["left"][2] < p["head"][2]-9
        assert p["elbow"][2] > p["head"][2]+1 and p["elbow"][0] > p["right"][0]+2
        assert abs(p["grip"][1]-p["right"][1]) < .01
        assert dot(p["arrow"], [0, 0, -1]) > .9999
    for t in (0, .10):
        p = landmarks(model, attack, t)
        assert norm(sub(p["right"], p["rest_nock"])) < .01
    idle = landmarks(model, ready, 0)
    assert idle["left"][1] < idle["head"][1]-3
    follow = landmarks(model, attack, .35)
    assert norm(sub(follow["right"], follow["nock"])) > 1.5
    # Dense static sampling guards against NaNs, support-arm collapse, and root
    # sliding. This does not claim terrain, skin collision or engine verification.
    for i in range(181):
        t = i/200
        p = landmarks(model, attack, t)
        assert all(math.isfinite(v) for values in p.values() for v in values)
        pose, root_y = sample(attack, t)
        assert pose["player_root"][0] == pose["player_root"][2] == 0
        assert math.isfinite(root_y)
        if .25 <= t <= .45:
            assert norm(sub(p["left"], p["shoulder"])) > 10.4
    for t in (0, .10, .15, .25, .30, .35, .45, .60, .75, .90):
        p = landmarks(model, attack, t)
        print(f"{t:.2f}s " + " ".join(f"{key}={tuple(round(x, 3) for x in p[key])}" for key in ("left", "right", "elbow")))
    print("PASS: 10 compatible clips; untouched rig + eight H15 clips; .30s release/.90s length; full-chain grip/nock/cheek FK. Static only.")


def export(model):
    return {"model": MODEL, "animations": [a for a in model["animations"] if a["name"].startswith("h15_")]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--from-art", action="store_true")
    args = parser.parse_args()
    source = json.loads(SOURCE.read_text())
    if args.verify:
        model, pack = json.loads(ART.read_text()), json.loads(PACK.read_text())
    else:
        if args.from_art:
            model = json.loads(ART.read_text())
        else:
            model = copy.deepcopy(source)
            model["name"] = model["model_identifier"] = MODEL
            low, attack = frames(model)
            # Restrained breathing changes cape only: hands stay on the relaxed nock.
            idle = [(0, low), (.6, h15.changed(low, cape_cape=[10, 0, 3])),
                    (1.2, h15.changed(low, cape_cape=[11, 0, 3])),
                    (1.8, h15.changed(low, cape_cape=[10, 0, 3])), (2.4, low)]
            replacements = {READY: new_clip(model, READY, idle, True), ATTACK: new_clip(model, ATTACK, attack)}
            model["animations"] = [replacements.get(a["name"], a) for a in model["animations"]]
        pack = export(model)
        # Validate before either output is overwritten.
        validate(model, pack, source)
        ART.parent.mkdir(parents=True, exist_ok=True)
        PACK.parent.mkdir(parents=True, exist_ok=True)
        ART.write_text(json.dumps(model, indent=2)+"\n")
        PACK.write_text(json.dumps(pack, indent=2)+"\n")
        print(f"Saved {ART.relative_to(ROOT)} and {PACK.relative_to(ROOT)}")
        return
    validate(model, pack, source)


if __name__ == "__main__":
    main()
