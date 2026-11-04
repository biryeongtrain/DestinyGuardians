#!/usr/bin/env python3
"""W140 raised two-hand carry and one-hand cuts, preserving gameplay cues.
Historical W53/W55 and installed artist models are never overwritten.
"""
import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import build_sword_animation_w53 as old
import build_sword_stance_w55 as stance
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_animation_h20 as h20

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "art/blockbench/animations/guardian_sword_w55.bbmodel"
ART = "art/blockbench/animations/guardian_sword_w140.bbmodel"
PACK = "src/main/resources/destiny/animation/sword_w140.animation.json"
MODEL = "guardian_sword_w140"
# Same right-hand native sword frame: model +Y, display Rx(+90), .9 scale.
# A second grip ~2.7 raw units below the main grip, not an arbitrary free hand.
SUPPORT_LOCAL = [0, 0, -2.43]


def raised(model, kind="idle", phase=0):
    wave = math.sin(phase * math.tau)
    breath = (1 - math.cos(phase * math.tau)) / 2
    angles = [-78 + .6 * breath, -30, -12]
    wrist = [3, 23.4 + .12 * breath, -3.6]
    p = h20.stance(-12, -3, .8)
    if kind == "move":
        p["prl_right_leg"] = [-11 + 24 * wave, -8, -5]
        p["pll_left_leg"] = [7 - 24 * wave, 12, 6]
        p["prfl_right_foreleg"] = [25 + 11 * wave, 0, 0]
        p["plfl_left_foreleg"] = [25 - 11 * wave, 0, 0]
        wrist[1] += .12 * wave * wave
    elif kind == "air":
        p["prl_right_leg"] = [-40, -8, -5]
        p["pll_left_leg"] = [-30, 12, 6]
        p["prfl_right_foreleg"] = [45, 0, 0]
        p["plfl_left_foreleg"] = [38, 0, 0]
    elif kind == "guard":
        wrist = [1.2, 23.7 + .12 * breath, -5.4]
        angles = [-82, -20, -16]
    matrix = h15.rot(angles)
    support = h19.add(wrist, h19.vector(matrix, SUPPORT_LOCAL))
    h19.solve_arm(model, p, "right", wrist, [1, -.3, .45])
    h19.solve_arm(model, p, "left", support, [-1, -.2, .5])
    h20.aim_right(model, p, matrix)
    p["cape_cape"] = [12 + (5 if kind == "move" else 0) + wave, 0, .5 * wave]
    return p


def unwrap(frames):
    """Shortest Euler branch per interval; prevent a wrist taking a 300deg detour."""
    out = copy.deepcopy(frames)
    for i in range(1, len(out)):
        for bone in h15.BONES:
            for axis in range(3):
                previous, current = out[i-1][1][bone][axis], out[i][1][bone][axis]
                out[i][1][bone][axis] = previous + (current - previous + 180) % 360 - 180
    return out


def clips(model):
    ready = raised(model)
    result = []
    for clip in old.author(model):
        length = clip["length"]
        # Re-author endpoints; keep all clip durations/contact timing and interior
        # one-handed attack silhouettes. The left hand releases during the cut.
        times = sorted({k["time"] for a in clip["animators"].values()
                        for k in a["keyframes"] if k["channel"] == "rotation"})
        frames = [(t, h19.sample(clip, t)[0]) for t in times]
        frames[0] = (0, copy.deepcopy(ready))
        frames[-1] = (length, copy.deepcopy(ready))
        if "_light_" in clip["name"]:
            # Off-hand is away from the grip at every attack contact, then returns
            # with recovery. No duplicate offhand sword or two-handed cut.
            for t, pose in frames[1:-1]:
                if t <= .30:
                    h19.solve_arm(model, pose, "left", [-5.5, 18.6, -2.5], [-1, -.4, .5])
        result.append(h20.new_clip(model, clip["name"], unwrap(frames)))
    for kind, length, _ in stance.LOOPS:
        count = 16 if kind == "move" else 8
        frames = [(round(i * length / count, 6), raised(model, kind, i / count)) for i in range(count+1)]
        frames[-1] = (length, copy.deepcopy(frames[0][1]))
        result.append(h20.new_clip(model, "h15_sword_" + kind, unwrap(frames), loop=True))
    return result


def generate():
    source = json.loads((ROOT / SOURCE).read_text())
    authored = clips(source)
    art = copy.deepcopy(source)
    art["name"] = art["model_identifier"] = MODEL
    art["animations"] = [a for a in art["animations"] if not a["name"].startswith("h15_sword_")] + authored
    outputs = {ART: old.encode(art), PACK: old.encode({"model": MODEL, "animations": authored})}
    outputs["art/weapons/w140/manifest.json"] = old.encode({
        "stage": "W140", "model": MODEL, "source": SOURCE,
        "sourceSha256": hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest(),
        "intent": "raised two-hand carry, right-hand light cuts, support regrip on recovery",
        "supportLocalModelUnits": SUPPORT_LOCAL,
        "timing": [{"name": name, "length": length, "contact": cue} for name, length, cue, _, _ in old.CUES],
        "references": ["https://www.youtube.com/watch?v=tTjwM26ilgo&t=143",
                       "https://www.youtube.com/watch?v=5oHxtta-a_I&t=48"],
        "limits": "Authored adaptation, not extracted animation or measured D2 timing. Historical footage varies by sword frame.",
        "outputSha256": {p: hashlib.sha256(b).hexdigest() for p, b in outputs.items()}
    })
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    outputs = generate()
    assert outputs == generate()
    for name, data in outputs.items():
        p = ROOT / name
        if args.verify:
            assert p.read_bytes() == data, name
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    print("W140 " + ("VERIFY" if args.verify else "GENERATE") + " PASS: raised carry + 8 attacks + 4 loops; old W53/W55 untouched")


if __name__ == "__main__":
    main()
