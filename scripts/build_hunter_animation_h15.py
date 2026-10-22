#!/usr/bin/env python3
"""H15 animation authoring source. No build, server install, or legacy model writes.
Usage: rtk proxy sh -c 'python3 scripts/build_hunter_animation_h15.py --template /path/to/steve.bbmodel'
The artist .bbmodel is authoritative after editing; --from-art exports its H15 clips.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/blockbench/animations/guardian_hunter_h15.bbmodel"
PACK = ROOT / "src/main/resources/destiny/animation/hunter_h15.animation.json"
NAMESPACE = uuid.UUID("1fec419d-4e1c-5ca4-949e-c66c9d936d15")
BONES = ["player_root", "phip_hip", "pw_waist", "pc_chest", "h_ph_head",
         "pra_right_arm", "prfa_right_forearm", "pri_right_item",
         "pla_left_arm", "plfa_left_forearm", "pli_left_item",
         "prl_right_leg", "prfl_right_foreleg", "pll_left_leg", "plfl_left_foreleg", "cape_cape"]


def uid(label):
    return str(uuid.uuid5(NAMESPACE, label))


def zero():
    return {b: [0, 0, 0] for b in BONES}


def pose(**bones):
    p = zero()
    p.update(bones)
    return p


ARC = pose(phip_hip=[-5, 8, 0], pw_waist=[-3, -6, 0], pc_chest=[-5, -18, -3],
           h_ph_head=[8, 16, 0], pra_right_arm=[-48, -12, -32], prfa_right_forearm=[-38, 0, 0],
           pla_left_arm=[-28, 15, 26], plfa_left_forearm=[-56, 0, 0],
           prl_right_leg=[-15, -8, -8], prfl_right_foreleg=[23, 0, 0],
           pll_left_leg=[8, 12, 10], plfl_left_foreleg=[12, 0, 0], cape_cape=[8, 0, -3])
SOLAR = pose(phip_hip=[0, -8, 0], pw_waist=[0, 5, 0], pc_chest=[-3, 15, -3],
             h_ph_head=[3, -12, 0], pra_right_arm=[-88, -12, -4], prfa_right_forearm=[-5, 0, 0],
             pla_left_arm=[-35, 15, 18], plfa_left_forearm=[-58, 0, 0],
             prl_right_leg=[-8, -8, -6], prfl_right_foreleg=[13, 0, 0],
             pll_left_leg=[8, 10, 7], plfl_left_foreleg=[8, 0, 0], cape_cape=[5, 0, 0])
VOID = pose(phip_hip=[-3, 10, 0], pw_waist=[-2, -6, 0], pc_chest=[-4, -22, -4],
            h_ph_head=[6, 18, 0], pra_right_arm=[-87, -24, -6], prfa_right_forearm=[-8, 0, 0],
            pla_left_arm=[-77, 42, 22], plfa_left_forearm=[-66, 0, -8],
            prl_right_leg=[-13, -12, -7], prfl_right_foreleg=[20, 0, 0],
            pll_left_leg=[11, 16, 9], plfl_left_foreleg=[12, 0, 0], cape_cape=[9, 0, 3])


def changed(base, **bones):
    p = copy.deepcopy(base)
    p.update(bones)
    return p


def mm(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def tr(v):
    return [[1, 0, 0, v[0]], [0, 1, 0, v[1]], [0, 0, 1, v[2]], [0, 0, 0, 1]]


def rot(v):
    x, y, z = map(math.radians, v)
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    rx = [[1, 0, 0, 0], [0, cx, -sx, 0], [0, sx, cx, 0], [0, 0, 0, 1]]
    ry = [[cy, 0, sy, 0], [0, 1, 0, 0], [-sy, 0, cy, 0], [0, 0, 0, 1]]
    rz = [[cz, -sz, 0, 0], [sz, cz, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    return mm(mm(rz, ry), rx)  # Blockbench group Euler order ZYX.


def floor_y(model, p):
    """Fit authored contact keys to the lowest skin cube, with no horizontal root motion.
    This is a key-pose authoring aid; interpolated/terrain contact still needs a game check.
    """
    groups = {g["uuid"]: g for g in model["groups"]}
    elements = {e["uuid"]: e for e in model["elements"]}
    ys = []

    def walk(nodes, parent_matrix, parent_origin):
        for node in nodes:
            if isinstance(node, str):
                e = elements.get(node, {})
                if e.get("name") != "skin":
                    continue
                for x in (e["from"][0], e["to"][0]):
                    for y in (e["from"][1], e["to"][1]):
                        for z in (e["from"][2], e["to"][2]):
                            v = [x-parent_origin[0], y-parent_origin[1], z-parent_origin[2], 1]
                            ys.append(sum(parent_matrix[1][i]*v[i] for i in range(4)))
            else:
                g = groups[node["uuid"]]
                origin = g["origin"]
                offset = [origin[i]-parent_origin[i] for i in range(3)]
                rotation = [g.get("rotation", [0]*3)[i]+p.get(g["name"], [0]*3)[i] for i in range(3)]
                walk(node["children"], mm(parent_matrix, mm(tr(offset), rot(rotation))), origin)

    walk(model["outliner"], tr([0, 0, 0]), [0, 0, 0])
    return round(-min(ys), 4)


def clip(model, name, frames, loop=False, root_positions=None, linear_root=False):
    length = frames[-1][0]
    groups = {g["name"]: g["uuid"] for g in model["groups"]}
    result = {"uuid": uid(name), "name": name, "loop": "loop" if loop else "once",
              "override": False, "length": length, "snapping": 20,
              "animators": {}}
    for bone in BONES:
        keys = []
        for t, p in frames:
            channels = [("rotation", p[bone])]
            if bone == "player_root":
                y = root_positions.get(t, 0) if root_positions is not None else floor_y(model, p)
                channels.append(("position", [0, y, 0]))
            for channel, v in channels:
                keys.append({"uuid": uid(f"{name}/{bone}/{channel}/{t}"), "channel": channel, "time": t,
                             "interpolation": "linear" if (bone == "player_root" and linear_root) else "catmullrom",
                             "data_points": [dict(zip(("x", "y", "z"), v))]})
        result["animators"][groups[bone]] = {"name": bone, "type": "bone", "rotation_global": False,
                                           "quaternion_interpolation": False, "keyframes": keys}
    return result


def roll(model, direction):
    # 0-.10 anticipation; .10-.40 shoulder contact/tuck; .40-.70 plant/uncoil/settle.
    times = [0, .05, .10, .20, .30, .40, .50, .60, .70]
    spin = [0, 8, -24, -100, -188, -270, -326, -354, -360]
    tuck = [0, .35, .80, 1, 1, .85, .50, .18, 0]
    axis = 0 if direction in ("forward", "back") else 2
    sign = -1 if direction in ("back", "left") else 1
    frames = []
    for t, angle, f in zip(times, spin, tuck):
        p = pose(phip_hip=[-24*f, 0, 0], pw_waist=[-16*f, 0, 0],
                 pc_chest=[-22*f, 0, 0], h_ph_head=[26*f, 0, 0],
                 pra_right_arm=[-75*f, -8*f, -18*f], prfa_right_forearm=[-90*f, 0, 0],
                 pla_left_arm=[-66*f, 8*f, 24*f], plfa_left_forearm=[-100*f, 0, 0],
                 prl_right_leg=[-65*f, 0, -9*f], prfl_right_foreleg=[105*f, 0, 0],
                 pll_left_leg=[-50*f, 0, 9*f], plfl_left_foreleg=[92*f, 0, 0],
                 cape_cape=[28*f, 0, 0])
        p["player_root"][axis] = angle*sign
        if direction in ("left", "right"):
            side = 1 if direction == "left" else -1
            # Leading shoulder and opposing leg make the side roll readable in silhouette.
            p["pc_chest"][2] = 8*f*side
            p["pra_right_arm"][2] -= 16*f*side
            p["pla_left_arm"][2] -= 16*f*side
        frames.append((t, p))
    return clip(model, "h15_roll_" + direction, frames, linear_root=True)


def ready(model, name, base, length):
    frames = []
    for phase, breath in [(0, 0), (.25, .55), (.5, 1), (.75, .4), (1, 0)]:
        p = copy.deepcopy(base)
        p["pc_chest"][0] -= 1.6*breath
        p["pw_waist"][0] += .8*breath
        p["h_ph_head"][0] += .8*breath
        p["prfa_right_forearm"][0] -= 1.2*breath
        p["cape_cape"][0] += 2.5*breath
        frames.append((round(length*phase, 4), p))
    return clip(model, name, frames, loop=True)


def attacks(model):
    arc = [(0, ARC),
           (.05, changed(ARC, phip_hip=[-7, -18, 2], pc_chest=[-12, -42, -10],
                          pra_right_arm=[-72, -52, -38], pla_left_arm=[-40, -20, 20])),
           (.10, changed(ARC, phip_hip=[-12, 20, -3], pc_chest=[-8, 34, 12],
                          pra_right_arm=[-78, 42, 34], prfa_right_forearm=[-16, 0, 0],
                          pla_left_arm=[-70, 22, -15], plfa_left_forearm=[-35, 0, 0],
                          pri_right_item=[0, 0, 32])),
           (.15, changed(ARC, pc_chest=[-4, 46, 8], pra_right_arm=[-35, 70, 38],
                          pla_left_arm=[-45, 36, -12], cape_cape=[22, -16, -8])),
           (.22, changed(ARC, pc_chest=[-5, 4, 1], pra_right_arm=[-42, 14, -12], cape_cape=[16, -4, -3])),
           (.30, ARC)]
    solar = [(0, SOLAR),
             (.05, changed(SOLAR, prfa_right_forearm=[-8, 0, 0], h_ph_head=[2, -12, 0])),
             (.10, changed(SOLAR, pc_chest=[4, 18, -4], pra_right_arm=[-112, -12, -7],
                            prfa_right_forearm=[-19, 0, 0], pri_right_item=[-12, 0, 0],
                            pla_left_arm=[-43, 18, 22], cape_cape=[15, 0, 0])),
             (.18, changed(SOLAR, pc_chest=[1, 16, -3], pra_right_arm=[-101, -12, -5],
                            prfa_right_forearm=[-13, 0, 0], pri_right_item=[-4, 0, 0])),
             (.30, changed(SOLAR, pra_right_arm=[-85, -12, -4], cape_cape=[9, 0, 0])),
             (.40, SOLAR)]
    void = [(0, VOID),
            (.08, changed(VOID, pc_chest=[-6, -32, -4], pla_left_arm=[-85, 56, 25],
                           plfa_left_forearm=[-94, 0, -8], pri_right_item=[0, 0, -5])),
            (.16, changed(VOID, pc_chest=[-7, -37, -4], pla_left_arm=[-88, 63, 28],
                           plfa_left_forearm=[-108, 0, -8])),
            (.21, changed(VOID, pc_chest=[1, -16, -3], pra_right_arm=[-92, -22, -7],
                           pla_left_arm=[-76, 82, 32], plfa_left_forearm=[-35, 0, -8],
                           pri_right_item=[0, 0, 8], cape_cape=[21, 0, 7])),
            (.30, changed(VOID, pla_left_arm=[-54, 62, 25], plfa_left_forearm=[-42, 0, -5],
                           cape_cape=[16, 0, 4])),
            (.42, changed(VOID, pla_left_arm=[-68, 44, 22], cape_cape=[11, 0, 3])),
            (.55, VOID)]
    return [clip(model, "h15_super_arc_attack", arc), clip(model, "h15_super_solar_attack", solar),
            clip(model, "h15_super_void_attack", void)]


def export(model):
    clips = [a for a in model["animations"] if a["name"].startswith("h15_")]
    # Animators retain their names; runtime remaps UUIDs to the current BetterModel template.
    PACK.parent.mkdir(parents=True, exist_ok=True)
    PACK.write_text(json.dumps({"model": "guardian_hunter_h15", "animations": clips}, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--from-art", action="store_true", help="Export edited artist file without regenerating poses")
    args = parser.parse_args()
    if args.from_art:
        export(json.loads(ART.read_text()))
        return
    if args.template is None:
        parser.error("--template is required unless --from-art")
    model = json.loads(args.template.read_text())
    model["name"] = model["model_identifier"] = "guardian_hunter_h15"
    model["animations"] = [a for a in model.get("animations", []) if not a["name"].startswith("h15_")]
    model["animations"] += [roll(model, d) for d in ("forward", "back", "left", "right")]
    model["animations"] += [ready(model, "h15_super_arc", ARC, 1.6),
                            ready(model, "h15_super_solar", SOLAR, 2.0),
                            ready(model, "h15_super_void", VOID, 2.4)]
    model["animations"] += attacks(model)
    ART.parent.mkdir(parents=True, exist_ok=True)
    ART.write_text(json.dumps(model, indent=2) + "\n")
    export(model)
    print(f"H15: wrote {ART.relative_to(ROOT)} and {PACK.relative_to(ROOT)} (10 clips, rig unchanged)")


if __name__ == "__main__":
    main()
