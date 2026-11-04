#!/usr/bin/env python3
"""High close two-hand ready, dropped elbows and explicit one-hand light recovery.

An authored D2-inspired adaptation, not extracted animation. W140 stays intact.
"""
import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import build_sword_pose_w140 as prior

ROOT = Path(__file__).resolve().parents[1]
SOURCE = prior.SOURCE
ART = "art/blockbench/animations/guardian_sword_w146.bbmodel"
PACK = "src/main/resources/destiny/animation/sword_w146.animation.json"
MODEL = "guardian_sword_w146"
SUPPORT_LOCAL = prior.SUPPORT_LOCAL
h15, fk, h20, old = prior.h15, prior.h19, prior.h20, prior.old


def raised(model, kind="idle", phase=0):
    wave = math.sin(phase * math.tau)
    breath = (1 - math.cos(phase * math.tau)) / 2
    p = h20.stance(-12, -3, .8)
    # Close to the right temple, not arms spread horizontally at shoulder height.
    wrist = [2.8, 25.3 + .10 * breath, -5.4]
    angles = [-76 + .5 * breath, -16, -12]
    if kind == "move":
        p["prl_right_leg"] = [-11 + 24 * wave, -8, -5]
        p["pll_left_leg"] = [7 - 24 * wave, 12, 6]
        p["prfl_right_foreleg"] = [25 + 11 * wave, 0, 0]
        p["plfl_left_foreleg"] = [25 - 11 * wave, 0, 0]
        wrist[1] += .10 * wave * wave
    elif kind == "air":
        p["prl_right_leg"] = [-40, -8, -5]
        p["pll_left_leg"] = [-30, 12, 6]
        p["prfl_right_foreleg"] = [45, 0, 0]
        p["plfl_left_foreleg"] = [38, 0, 0]
    elif kind == "guard":
        wrist = [1.2, 25 + .1 * breath, -6.2]
        angles = [-82, -10, -16]
    matrix = h15.rot(angles)
    support = fk.add(wrist, fk.vector(matrix, SUPPORT_LOCAL))
    fk.solve_arm(model, p, "right", wrist, [.5, -1, .1])
    fk.solve_arm(model, p, "left", support, [-.6, -1, -.1])
    h20.aim_right(model, p, matrix)
    p["cape_cape"] = [12 + (5 if kind == "move" else 0) + wave, 0, .5 * wave]
    return p


def lights(model):
    ready = raised(model)
    def cut(yaw, wrist, angles, lean=-5, crouch=.9, cape=16):
        p = h20.stance(yaw, lean, crouch)
        p["cape_cape"] = [cape, -yaw * .15, -yaw * .1]
        fk.solve_arm(model, p, "right", wrist, [.8, -1, .1])
        # Support hand releases before anticipation, balances at the left waist,
        # stays clear through the cut, then meets the same hilt during recovery.
        fk.solve_arm(model, p, "left", [-6, 17.5, -.5], [-1, -.7, .3])
        h20.aim_right(model, p, h15.rot(angles))
        return p
    right = cut(-30, [6.2, 23.5, -3.0], [-24, -75, -8], cape=9)
    mid = cut(2, [2, 19.5, -8.2], [0, 0, -4], cape=18)
    left = cut(28, [-2.5, 18.8, -5], [-3, 95, 0], cape=22)
    reverse = cut(34, [-2, 21, -4], [-8, 80, 0], cape=9)
    rmid = cut(0, [2.3, 18.5, -8.2], [0, 0, 6], cape=17)
    rfollow = cut(-30, [7, 18.5, -2.5], [-4, -95, 0], cape=21)
    fin = cut(-40, [6.5, 24, -2.5], [-20, -80, -8], cape=10)
    fmid = cut(4, [1, 18, -8.2], [-5, 5, -8], lean=-9, crouch=1.1, cape=22)
    ffollow = cut(38, [-2.5, 16.5, -4.5], [-12, 100, 0], lean=-6, crouch=1.1, cape=26)
    released = copy.deepcopy(ready)
    fk.solve_arm(model, released, "left", [-6, 17.5, -.5], [-1, -.7, .3])
    frames = [
        [(0, ready), (.05, released), (.10, right), (.15, mid), (.20, left),
         (.25, left), (.35, h20.mix(left, ready, .65)), (.45, ready)],
        [(0, ready), (.05, released), (.10, reverse), (.15, reverse), (.20, rmid),
         (.25, rfollow), (.30, rfollow), (.40, h20.mix(rfollow, ready, .65)), (.50, ready)],
        [(0, ready), (.05, released), (.10, fin), (.15, fin), (.20, fmid),
         (.25, ffollow), (.30, ffollow), (.45, h20.mix(ffollow, ready, .7)), (.55, ready)],
    ]
    return [h20.new_clip(model, old.NAMES[i], prior.unwrap(keys)) for i, keys in enumerate(frames)]


def clips(model):
    ready = raised(model)
    result = lights(model)
    # Heavy silhouettes/contact/durations remain W53; remove their old low-ready
    # recovery mixes too. Do not change heavy shape selection or server mechanics.
    for clip, cue in zip(old.author(model)[3:], old.CUES[3:]):
        length, contact = clip["length"], cue[2]
        times = sorted({k["time"] for a in clip["animators"].values()
                        for k in a["keyframes"] if k["channel"] == "rotation"})
        frames = [(t, fk.sample(clip, t)[0]) for t in times]
        frames[0] = (0, copy.deepcopy(ready))
        end = copy.deepcopy(ready)
        if clip["name"].endswith("vortex"):
            end["player_root"] = [0, 360, 0]
        follow_time = max(t for t in times if contact < t <= length * .75)
        follow = fk.sample(clip, follow_time)[0]
        for i, (t, p) in enumerate(frames):
            if follow_time < t < length:
                frames[i] = (t, h20.mix(follow, end, (t-follow_time)/(length-follow_time)))
        frames[-1] = (length, end)
        result.append(h20.new_clip(model, clip["name"], prior.unwrap(frames)))
    for kind, length, _ in prior.stance.LOOPS:
        count = 16 if kind == "move" else 8
        frames = [(round(i * length / count, 6), raised(model, kind, i / count)) for i in range(count + 1)]
        frames[-1] = (length, copy.deepcopy(frames[0][1]))
        result.append(h20.new_clip(model, "h15_sword_" + kind, prior.unwrap(frames), loop=True))
    return result


def generate():
    source = json.loads((ROOT / SOURCE).read_text())
    authored = clips(source)
    art = copy.deepcopy(source)
    art["name"] = art["model_identifier"] = MODEL
    art["animations"] = [a for a in art["animations"] if not a["name"].startswith("h15_sword_")] + authored
    out = {ART: old.encode(art), PACK: old.encode({"model": MODEL, "animations": authored})}
    out["art/weapons/w146/manifest.json"] = old.encode({
        "stage": "W146", "model": MODEL, "source": SOURCE,
        "sourceSha256": hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest(),
        "intent": "close high two-hand carry / dropped elbows / released one-hand lights / high regrip",
        "supportLocalModelUnits": SUPPORT_LOCAL,
        "timing": [{"name": n, "length": l, "contact": c} for n, l, c, _, _ in old.CUES],
        "references": ["https://www.youtube.com/watch?v=tTjwM26ilgo&t=143",
                       "https://www.youtube.com/watch?v=5oHxtta-a_I&t=48"],
        "limits": "Authored, not extracted or D2 timing measurement; high common carry, not every frame-specific stance.",
        "outputSha256": {p: hashlib.sha256(b).hexdigest() for p, b in out.items()}
    })
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    outputs = generate()
    assert outputs == generate(), "Non-deterministic output"
    for name, data in outputs.items():
        path = ROOT / name
        if args.verify:
            assert path.read_bytes() == data, name
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print("W146 PASS: 12 versioned clips; close high hilt, lowered elbows, one-hand lights and high recovery")
