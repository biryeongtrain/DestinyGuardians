#!/usr/bin/env python3
"""Predrawn Shadowshot: readable taut cord and matching held hands, on the H21 rig.

Writes only new H22 assets. No installed model, inherited asset or process is modified.
--verify regenerates in memory and compares byte-for-byte without writing.
"""
import copy
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_animation_h20 as h20
import build_hunter_animation_h21 as h21

ROOT = Path(__file__).resolve().parents[1]
MODEL = "guardian_hunter_h22"
BOW = "shadow_bow_h22_drawn"
SOURCE = ROOT / "art/blockbench/animations/guardian_hunter_h21.bbmodel"
ART = ROOT / f"art/blockbench/animations/{MODEL}.bbmodel"
PACK = ROOT / "src/main/resources/destiny/animation/hunter_h22.animation.json"
ITEM_ART = ROOT / f"art/blockbench/supers/{BOW}.bbmodel"
ITEM = ROOT / f"src/main/resources/assets/destiny/models/item/{BOW}.json"
ITEM_DEF = ROOT / f"src/main/resources/assets/destiny/items/{BOW}.json"
VOID = ("h15_super_void", "h15_super_void_attack")
# Hold the actual H21 full-draw upper body, including cheek anchor and item orientation.
# Legs/cape retain the H21 crouch/hop sequence. No fake entity/root lift is added.
UPPER = tuple(b for b in h15.BONES if b not in h21.LEGS + ("cape_cape",))


def compose(source):
    model = copy.deepcopy(source)
    model["name"] = model["model_identifier"] = MODEL
    original = {a["name"]: a for a in source["animations"]}
    full, _ = h19.sample(original[VOID[1]], .25)
    for clip in model["animations"]:
        if clip["name"] not in VOID:
            continue
        old = original[clip["name"]]
        ready = clip["name"] == VOID[0]
        clip["uuid"] = h15.uid("h22/" + clip["name"])
        times = [i / 40 for i in range(round(clip["length"] * 40) + 1)]
        animators = {a["name"]: a for a in clip["animators"].values()}
        changed = UPPER + ("player_root",)
        for bone in set(changed):
            channels = {"rotation"} if bone != "player_root" else {"rotation", "position"}
            animators[bone]["keyframes"] = [k for k in animators[bone]["keyframes"]
                                               if k["channel"] not in channels]
        for time in times:
            pose, _ = h19.sample(old, time)
            if ready or time <= .30:
                amount = 1
            elif time <= .60:
                amount = 0
            else:
                amount = min(1, (time - .60) / .15)
            for bone in UPPER:
                if ready or time <= .30 or time >= .75:
                    pose[bone] = full[bone][:]
                elif time > .60:
                    # Finish returning to the new predrawn ready rather than old lowered rest.
                    # Choose the equivalent Euler branch nearest full pose.
                    values = [v + 360 * round((target - v) / 360) for v, target in zip(pose[bone], full[bone])]
                    pose[bone] = [v + (target - v) * amount for v, target in zip(values, full[bone])]
                animators[bone]["keyframes"].append(h21.key("h22/" + clip["name"], bone, "rotation", time, pose[bone]))
            animators["player_root"]["keyframes"].append(h21.key("h22/" + clip["name"], "player_root", "position", time,
                                                           [0, h15.floor_y(model, pose), 0]))
        clip["snapping"] = 40
    return model


def bow_assets():
    model = json.loads((ROOT / "src/main/resources/assets/destiny/models/item/shadow_bow_h20_3.json").read_text())
    art = json.loads((ROOT / "art/blockbench/supers/shadow_bow_h20_3.bbmodel").read_text())
    art["name"] = art["model_identifier"] = BOW
    # Both arms of the V already meet raw (16.24,8,8); preserve nock, limbs, UV detail
    # and the complete native handed recipe. Only cord cross-section/brightness change.
    for index in (201, 202):
        for obj, bb in ((model, False), (art, True)):
            cord = obj["elements"][index]
            cord["from"][0], cord["to"][0] = 11.15, 11.39
            cord["from"][2], cord["to"][2] = 7.88, 8.12
            for face in cord["faces"].values():
                # Constant pale violet, not a long UV that averages dark texture pixels.
                face["uv"] = [200, 8, 208, 12] if bb else [12.5, 1, 13, 1.5]
    return art, model, {"model": {"type": "minecraft:model", "model": f"destiny:item/{BOW}"}}


def validate(model, source, item):
    for field in source:
        if field not in ("name", "model_identifier", "animations"):
            assert model[field] == source[field], "Changed rig/skin: " + field
    old = {a["name"]: a for a in source["animations"]}
    clips = {a["name"]: a for a in model["animations"]}
    assert len([n for n in clips if n.startswith("h15_")]) == 19
    for name, clip in clips.items():
        if name not in VOID:
            assert clip == old[name], "Changed inherited clip " + name
            continue
        # Every H21 leg curve is JSON-identical; entity lift remains gameplay-owned.
        for bone in h21.LEGS:
            before = next(a for a in old[name]["animators"].values() if a["name"] == bone)
            after = next(a for a in clip["animators"].values() if a["name"] == bone)
            assert before == after
        max_gap = 0
        end = clip["length"] if name == VOID[0] else .30
        for i in range(round(end * 200) + 1):
            t = i / 200
            pose, y = h19.sample(clip, t)
            m = h19.fk(model, pose, y)
            gap = h19.norm(h19.sub(h19.point(m["pri_right_item"], [0, 0, 0]),
                                   h19.point(m["pli_left_item"], [0, 2, 8.24])))
            cheek = h19.point(m["h_ph_head"], [4.2, 3, -2.6])
            assert gap < .0001 and h19.norm(h19.sub(cheek, h19.point(m["pri_right_item"], [0, 0, 0]))) < .0001
            assert h19.dot(h19.vector(m["pli_left_item"], [0, 0, -1]), [0, 0, -1]) > .99999
            max_gap = max(max_gap, gap)
        print(name, "predrawn nock/hand/cheek dense FK max gap", max_gap, "model units; static only")
    ready, attack = (clips[n] for n in VOID)
    assert h19.sample(ready, 0) == h19.sample(ready, ready["length"])
    assert h19.sample(attack, 0) == h19.sample(attack, .90) == h19.sample(ready, 0)
    # Full-draw correction remains exactly H21's .2098875m relative to H20.
    assert h19.sample(attack, .30) == h19.sample(old[VOID[1]], .30)
    for index in (201, 202):
        cord = item["elements"][index]
        length = cord["to"][1] - cord["from"][1]
        angle = math.radians(abs(cord["rotation"]["angle"]))
        assert abs(11.27 + length * math.sin(angle) - 16.24) < 1e-8
        assert abs(length * math.cos(angle) - 12) < 1e-8
        assert abs(cord["to"][0] - cord["from"][0] - .24) < 1e-8
    print("PASS: 19 clips; 17 unchanged; H21 legs/hop/full-draw/release contract preserved; taut V cord 3x cross-section")


def main():
    verify = sys.argv[1:] == ["--verify"]
    if sys.argv[1:] and not verify:
        raise SystemExit("Usage: build_shadowshot_h22.py [--verify]")
    source = json.loads(SOURCE.read_text())
    model = compose(source)
    art, item, definition = bow_assets()
    validate(model, source, item)
    pack = {"model": MODEL, "animations": [a for a in model["animations"] if a["name"].startswith("h15_")]}
    for path, value in ((ART, model), (PACK, pack), (ITEM_ART, art), (ITEM, item), (ITEM_DEF, definition)):
        raw = (json.dumps(value, indent=2) + "\n").encode()
        if verify:
            assert path.read_bytes() == raw, path
        else:
            path.write_bytes(raw)
        print("verified" if verify else "saved", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
