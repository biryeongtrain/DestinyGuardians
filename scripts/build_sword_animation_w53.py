#!/usr/bin/env python3
"""W53: eight authored sword clips on an otherwise byte-preserved H26-r2 rig.

rtk proxy python3 -B scripts/build_sword_animation_w53.py [--verify]
Only the five W53 paths below may be written. --verify is strictly read-only.
No builds, app launches, geometry, gameplay motion, or downloaded references.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

# Shared checkout: imports must not create cache files outside our write set.
sys.dont_write_bytecode = True
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_animation_h20 as h20

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "scripts/build_sword_animation_w53.py"
SOURCE = "art/blockbench/animations/guardian_hunter_h26_r2.bbmodel"
ART = "art/blockbench/animations/guardian_sword_w53.bbmodel"
PACK = "src/main/resources/destiny/animation/sword_w53.animation.json"
NOTES = "art/weapons/w53/animation-notes.md"
MANIFEST = "art/weapons/w53/manifest.json"
MODEL = "guardian_sword_w53"
PINS = {
    SOURCE: "47f058bcc8f768ef310a4d7e49a9b4aa6ce05fa3e769224809097afcd2a3a7c9",
    "scripts/build_hunter_animation_h15.py": "3908d921f42d52ae84f880021a6e06d10316084aec8a309453a338abb24805c6",
    "scripts/build_hunter_animation_h19.py": "483a796efdcab5dbf3fcc997ca5fc3118c4b693da6a3f47f520b5e06561af9ef",
    "scripts/build_hunter_animation_h20.py": "8d8dde7a49b54af3a31c3c78c1182c2851784277b75a8510a301fcdf95c79428",
    "art/weapons/w51/references/official-manifest.json": "15e159014db61a2838559fbc9ca581f7ec98e605ea0e0df216bdb94fbbb55eba",
    "art/weapons/w52/references/videos.json": "8536cbb4c75da9324fc5cd4b08877d7e1ae58c9dd51e1a4981087b647aef2b5a",
    "art/weapons/w52/references/mechanics.json": "d910a9dfc46413116554f4d8621ba57ccf35e17e72b36abf67d3b1b86a6c7492",
    "art/weapons/w52/references/light-contact.jpg": "d2e70012effb80c800da9a412e65d0519572424490fbce3c04399ee3ea624241",
    "art/weapons/w52/references/heavy-contact.jpg": "e36b208be67fe9a812d344b8d61e8eafb1fe5c93b6f98dc71c1ab093cd489e5f",
    "art/weapons/w52/references/aerial-contact.jpg": "84e5d567bb1f3316ffc74e2af88fdf33e622f02594022c23770011c9a93af4e0",
    "art/weapons/w52/references/aggressive-heavy-contact.jpg": "940978070d28df70582797784ea11a2263d2885aae496440115956a81ceafccc",
    "src/main/resources/assets/destiny/models/weapon/sword/abide_the_return.json": "8f6f9593d9a8dbd84022d4fe726152f799b71a55ae253e3f636e0bc5f46534c8",
    "src/main/resources/assets/destiny/models/weapon/sword/goldtusk.json": "ca9d5e0f093983cf833417408fef8cb6a70a130fbb442938cb1b5a8d3be980f0",
    "src/main/resources/assets/destiny/models/weapon/sword/crown_splitter.json": "50c519fa916a61e749ed7c72c29cf9fc4f173e93d8bbeaad98ad330dabfc3cdf",
    "src/main/resources/assets/destiny/models/weapon/sword/falling_guillotine.json": "324e1e54a8b6b70ab91be37286a4c172a42abdb9fe8716b9d6a76e721ba931b6",
    "src/main/resources/assets/destiny/models/weapon/sword/temptation_s_hook.json": "f5c48f76395c7b969fbb6867d75fd3b0bf038e1f1d6a73992d91e94a01b92277",
}
# Clip-local seconds, NOT D2 measurements or automatically dispatched hit events.
CUES = [
    ("light_1", .45, .15, "right-to-left horizontal cut", [.10, .20]),
    ("light_2", .50, .20, "left-to-right horizontal cut", [.15, .25]),
    ("light_3", .55, .20, "broad right-to-left low finisher", [.15, .25]),
    ("uppercut", .85, .35, "low-to-high uppercut", [.25, .45]),
    ("dash", .75, .25, "forward drive silhouette; stationary root", [.15, .30]),
    ("slam", .95, .40, "overhead-to-low slam; no jump", [.30, .45]),
    ("vortex", 1.05, .45, "one visual yaw turn; no gameplay facing change", [.20, .75]),
    ("caster", .80, .30, "blade sweep/release silhouette; no projectile asset", [.20, .40]),
]
NAMES = ["h15_sword_" + row[0] for row in CUES]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def check_pins():
    for path, expected in PINS.items():
        assert sha((ROOT / path).read_bytes()) == expected, "Changed pinned input: " + path


def fields(text):
    """Return exact top-level JSON value spans without reserializing source bytes."""
    decoder = json.JSONDecoder()
    spans, i = {}, text.index("{") + 1
    while True:
        while text[i].isspace() or text[i] == ",":
            i += 1
        if text[i] == "}":
            return spans
        name, i = decoder.raw_decode(text, i)
        while text[i].isspace():
            i += 1
        assert text[i] == ":"
        i += 1
        while text[i].isspace():
            i += 1
        start = i
        _, i = decoder.raw_decode(text, i)
        spans[name] = (start, i)


def animation_spans(text):
    start, end = fields(text)["animations"]
    decoder, result, i = json.JSONDecoder(), [], start + 1
    while i < end:
        while text[i].isspace() or text[i] == ",":
            i += 1
        if text[i] == "]":
            return result
        begin = i
        _, i = decoder.raw_decode(text, i)
        result.append(text[begin:i].encode())
    raise AssertionError("Unterminated animation array")


def append_preserving_bytes(raw, clips):
    """Only replace two identifiers and insert new clips at the array tail.

    Every original rig/texture value and inherited animation object retains its
    literal UTF-8 byte representation, not merely JSON semantic equivalence.
    """
    text = raw.decode()
    spans = fields(text)
    tail = spans["animations"][1] - 1
    while text[tail-1].isspace():
        tail -= 1
    added = ",\n" + ",\n".join(
        "\n".join("    " + line for line in json.dumps(c, indent=2, allow_nan=False).splitlines())
        for c in clips)
    edits = [(tail, tail, added)]
    edits += [(spans[k][0], spans[k][1], json.dumps(MODEL)) for k in ("name", "model_identifier")]
    for start, end, value in sorted(edits, reverse=True):
        text = text[:start] + value + text[end:]
    return text.encode()


def sword_pose(model, yaw, wrist, angles, lean=-3, crouch=.75, free=None, cape=10):
    """IK against existing right/left equipment pivots; no assumed staff support.

    angles is an authored item-frame world orientation, NOT a measured blade
    angle. Keep bind Rx(-90) and all existing native display/model mappings.
    """
    p = h20.stance(yaw, lean, crouch)
    p["cape_cape"] = [cape, -yaw * .15, yaw * -.10]
    h19.solve_arm(model, p, "right", wrist, [1, -.5, .35])
    h19.solve_arm(model, p, "left", free or [-5.5, 17.2, -2.5], [-1, -.4, .5])
    h20.aim_right(model, p, h15.rot(angles))
    return p


def author(model):
    def p(yaw, wrist, angles, **kw):
        return sword_pose(model, yaw, wrist, angles, **kw)
    ready = p(-10, [4, 18, -5.3], [65, -15, 0])
    right_coil = p(-30, [7, 19.3, -1.5], [6, -95, 0], free=[-5, 18, -3.5], cape=8)
    cut_mid = p(2, [2, 19, -8.2], [0, 0, -4], lean=-6, crouch=.9, cape=16)
    left_follow = p(28, [-2.5, 18.8, -5], [-3, 95, 0], free=[-5.5, 18, -.5], cape=22)
    left_coil = p(34, [-2, 19, -4], [5, 100, 0], free=[-4, 18.5, -2.5], cape=9)
    reverse_mid = p(0, [2.3, 18.5, -8.2], [0, 0, 6], lean=-5, crouch=.9, cape=15)
    right_follow = p(-30, [7, 18.5, -2.5], [-4, -95, 0], free=[-5.5, 17, -3], cape=21)
    finish_coil = p(-40, [7, 20, -1.5], [10, -100, 0], crouch=.9, cape=10)
    finish_mid = p(4, [1, 18, -8.2], [-5, 5, -8], lean=-9, crouch=1.1, cape=22)
    finish_follow = p(38, [-2.5, 16.5, -4.5], [-12, 100, 0], lean=-6, crouch=1.1, cape=26)
    low = p(-26, [5.5, 13.4, -2], [-25, -30, 0], lean=-8, crouch=1.05, cape=9)
    rise_mid = p(-3, [3, 19, -8], [25, 0, 0], lean=-5, crouch=.9, cape=17)
    rise_high = p(18, [2.5, 24, -6], [112, 5, -8], lean=3, crouch=.6,
                  free=[-5.5, 17, -1], cape=23)
    dash_coil = p(-24, [5, 19, -2.5], [85, -20, -12], lean=-6, crouch=.9, cape=10)
    dash_drive = p(-4, [2.5, 19, -8.5], [5, 0, 0], lean=-10, crouch=1,
                   free=[-6, 18, 1], cape=24)
    dash_follow = p(8, [1.2, 18.2, -8], [-5, 20, -3], lean=-9, crouch=1, cape=20)
    overhead = p(-14, [2.8, 25.7, -2.5], [150, -10, -8], lean=2, crouch=.8,
                 free=[-.5, 24, -2.3], cape=11)
    slam_down = p(5, [1.5, 14, -6], [-45, 0, 0], lean=-13, crouch=1.2,
                  free=[-1, 15, -5], cape=25)
    slam_follow = p(12, [1.5, 13.7, -5.5], [-55, 5, 0], lean=-12, crouch=1.2,
                    free=[-1, 14.8, -4.5], cape=27)
    spin = p(-8, [7, 18.5, -2.5], [0, -85, 0], lean=-3, crouch=.9,
             free=[-6, 19, -.5], cape=24)
    def turn(degrees, flare):
        q = copy.deepcopy(spin)
        q["player_root"] = [0, degrees, 0]
        q["cape_cape"] = [flare, -12, 10]
        return q
    spin_ready = h15.changed(ready, player_root=[0, 360, 0])
    cast_coil = p(-35, [6, 22, -2], [95, -70, -12], free=[-5, 18, -4], cape=8)
    cast_mid = p(-6, [2.7, 21, -8], [10, -10, -8], lean=-5, crouch=.9,
                 free=[-6, 19, -1], cape=18)
    cast_follow = p(30, [-1, 18.5, -6.5], [-5, 75, 0], lean=-4, crouch=.85,
                    free=[-5, 19, .5], cape=24)
    frames = [
        [(0, ready), (.10, right_coil), (.15, cut_mid), (.20, left_follow),
         (.25, left_follow), (.35, h20.mix(left_follow, ready, .65)), (.45, ready)],
        [(0, ready), (.10, left_coil), (.15, left_coil), (.20, reverse_mid),
         (.25, right_follow), (.30, right_follow), (.40, h20.mix(right_follow, ready, .65)), (.50, ready)],
        [(0, ready), (.10, finish_coil), (.15, finish_coil), (.20, finish_mid),
         (.25, finish_follow), (.30, finish_follow), (.45, h20.mix(finish_follow, ready, .7)), (.55, ready)],
        [(0, ready), (.15, low), (.25, low), (.35, rise_mid), (.45, rise_high),
         (.50, rise_high), (.65, h20.mix(rise_high, ready, .65)), (.85, ready)],
        [(0, ready), (.10, dash_coil), (.15, dash_coil), (.25, dash_drive),
         (.30, dash_drive), (.40, dash_follow), (.55, h20.mix(dash_follow, ready, .7)), (.75, ready)],
        [(0, ready), (.15, overhead), (.30, overhead), (.40, slam_down),
         (.45, slam_follow), (.55, slam_follow), (.75, h20.mix(slam_follow, ready, .7)), (.95, ready)],
        [(0, ready), (.15, right_coil), (.20, turn(0, 15)), (.30, turn(90, 25)),
         (.45, turn(180, 28)), (.60, turn(270, 26)), (.75, turn(360, 22)),
         (.90, h20.mix(turn(360, 18), spin_ready, .7)), (1.05, spin_ready)],
        [(0, ready), (.10, cast_coil), (.20, cast_coil), (.30, cast_mid),
         (.40, cast_follow), (.45, cast_follow), (.60, h20.mix(cast_follow, ready, .7)), (.80, ready)],
    ]
    return [h20.new_clip(model, name, keys) for name, keys in zip(NAMES, frames)]


def validate(source_raw, art_raw, pack_raw):
    source, model, pack = map(json.loads, (source_raw, art_raw, pack_raw))
    assert model["name"] == model["model_identifier"] == pack["model"] == MODEL
    before, after = fields(source_raw.decode()), fields(art_raw.decode())
    assert before.keys() == after.keys()
    for key in before:
        if key in ("name", "model_identifier", "animations"):
            continue
        a, b = before[key], after[key]
        assert source_raw.decode()[a[0]:a[1]].encode() == art_raw.decode()[b[0]:b[1]].encode(), key
        assert source[key] == model[key], key
    inherited = source["animations"]
    assert len(inherited) == 21
    assert model["animations"][:21] == inherited
    assert animation_spans(source_raw.decode()) == animation_spans(art_raw.decode())[:21]
    assert len(model["animations"]) == 29
    clips = model["animations"][21:]
    assert pack["animations"] == clips and [c["name"] for c in clips] == NAMES
    assert len({a["uuid"] for a in model["animations"]}) == 29
    groups = {g["name"]: g for g in model["groups"]}
    assert set(h15.BONES) <= groups.keys()
    assert groups["pri_right_item"]["rotation"] == groups["pli_left_item"]["rotation"] == [-90, 0, 0]
    reference = h19.sample(clips[0], 0)[0]
    stats, all_uuids = [], set()
    for clip, (_, length, contact, _, _) in zip(clips, CUES):
        assert clip["length"] == length <= (.55 if "_light_" in clip["name"] else 1.2)
        assert clip["loop"] == "once" and clip["override"] is False
        assert {a["name"] for a in clip["animators"].values()} == set(h15.BONES)
        root_ys = []
        for group_uuid, animator in clip["animators"].items():
            bone = animator["name"]
            assert group_uuid == groups[bone]["uuid"] and animator["type"] == "bone"
            assert animator["rotation_global"] is animator["quaternion_interpolation"] is False
            channels = {}
            for key in animator["keyframes"]:
                assert key["uuid"] not in all_uuids
                all_uuids.add(key["uuid"])
                assert key["interpolation"] == "linear"
                assert math.isfinite(key["time"]) and 0 <= key["time"] <= length
                assert len(key["data_points"]) == 1
                values = key["data_points"][0]
                assert set(values) == set("xyz")
                assert all(isinstance(v, (float, int)) and math.isfinite(v) for v in values.values())
                channels.setdefault(key["channel"], []).append(key)
                if key["channel"] == "position":
                    assert bone == "player_root" and values["x"] == values["z"] == 0
                    assert abs(values["y"]) <= 3, "Excess visual root Y"
                    root_ys.append(values["y"])
                elif key["channel"] == "scale":
                    assert bone in ("pri_right_item", "pli_left_item") and set(values.values()) == {1}
                else:
                    assert key["channel"] == "rotation"
                    if bone == "player_root":
                        assert values["x"] == values["z"] == 0
                        assert values["y"] == 0 or clip["name"] == "h15_sword_vortex"
            assert "rotation" in channels
            assert set(channels) == ({"rotation", "position"} if bone == "player_root" else
                                     {"rotation", "scale"} if bone.endswith("_item") else {"rotation"})
            for keys in channels.values():
                times = [k["time"] for k in keys]
                assert len(times) == len(set(times)) and min(times) == 0 and max(times) == length
        assert max(root_ys) - min(root_ys) <= 3, "Excess root Y excursion"
        # Sample at 200 Hz: dense floor-fit keys must keep the lowest skin corner
        # at authored ground, not create an airborne arc. No claim of native QA.
        max_floor_error = 0
        for i in range(round(length * 200) + 1):
            time = round(i / 200, 6)
            pose, y = h19.sample(clip, time)
            max_floor_error = max(max_floor_error, abs(y - h15.floor_y(model, pose)))
            for matrix in h19.fk(model, pose, y).values():
                assert all(math.isfinite(v) for row in matrix for v in row)
        assert max_floor_error <= .04, (clip["name"], max_floor_error)
        for time in (0, length):
            pose, _ = h19.sample(clip, time)
            assert all(abs((pose[b][i] - reference[b][i] + 180) % 360 - 180) < .00001
                       for b in h15.BONES for i in range(3)), "Recovery mismatch"
        stats.append({"name": clip["name"], "lengthSeconds": length,
                      "authoredContactOrReleaseSeconds": contact,
                      "rootYRangeModelUnits": [min(root_ys), max(root_ys)],
                      "maxSampledFloorErrorModelUnits": round(max_floor_error, 6)})
    return stats


def notes():
    rows = "\n".join(f"| `h15_sword_{suffix}` | {length:.2f} | {contact:.2f} | {shape} |"
                     for suffix, length, contact, shape, _ in CUES)
    return ("""# W53 sword animation sidecar — 2026-10-24

`guardian_sword_w53`: unchanged full H26-r2 skin/equipment rig, 21 literal-byte
inherited animations plus exactly eight new `h15_` clips. Runtime export contains
only the eight sword clips; it is not an inherited-super animation replacement.

## Authored clip-local cues

All values below are authored visual timing, not measured Destiny 2 timings,
server ticks, collision windows, input evidence, or automatic animation events.

| Clip | Length (s) | Contact/release cue (s) | Visual intention |
|---|---:|---:|---|
""" + rows + """

Lights alternate right/left/right with a lower, wider third-cut finisher.
Linear keys give anticipation, fast slash, brief follow-through, and recovery.
Each clip uses all 16 animated rig bones, including hips/waist/chest, head,
legs/knees, both arms/forearms/items, and cape. Start/end silhouettes agree
modulo 360 degrees; vortex alone finishes one continuous visual root-yaw turn.

## Held-item contract / motion boundaries

- Existing `pri_right_item` is the right-hand weapon pivot. Both item bind
  rotations stay `[-90,0,0]`; no added sword, model, element, texture, or UV.
- Existing five native sword models retain third-person right-hand display
  rotation `[90,0,0]`, translation `[0,2,0]`, scale `[0.9,0.9,0.9]`.
  Their paths/SHA-256 are pinned in the generator/manifest. The clips compensate
  torso/arm/bind rotations with the existing H20 right-item helper, not a new
  runtime model mapping. Item scales stay 1; the free hand is not a staff grip.
- Root X/Z position is always zero. Dash is only a forward-drive body silhouette.
  Vortex yaw is visual animation only, not entity/camera rotation or targeting.
- Root Y is ONLY H15 skin-floor fitting, sampled at 40 Hz by H20. No jump,
  airborne arc, lunge displacement, gravity, projectile, physics, hitbox, damage,
  energy curve, camera code, or grounded/air activation policy is implemented.
  200 Hz static verification bounds floor-fit interpolation error; this is not
  rendered/native-client/terrain validation. Air variants are not claimed.

## Reused evidence (no downloads)

Visually inspected all four existing `art/weapons/w52/references/*contact.jpg`:
light (0.7/1.7/3.0/4.5s), heavy (143.9/144.3/144.7/145.1s), aerial, aggressive-heavy.
Source metadata and clip/still hashes remain in W52 `videos.json`; input hashes
are repeated in the W53 manifest without editing W52.

- Ultraclocked, **Destiny 2 vs Warframe - Sword Animations**, uploaded 2026-04-21:
  <https://www.youtube.com/watch?v=tTjwM26ilgo>. Light/body counter-rotation,
  planted low cuts, cape follow-through, and dash lean are pose inspiration only.
  Aerial 124.8s is **Warframe and excluded**; 126.3/128.2/130.5s Destiny poses do
  not prove inputs, current restrictions, frame identity, or world-unit motion.
- selFu, **You can now double heavy attack with Aggressive Frame Swords**,
  uploaded 2023-08-23: <https://www.youtube.com/watch?v=5oHxtta-a_I>.
  Historical 48.7/50.0/51.4/53.0s slam silhouette reference; predates October 2023
  fix. No assumption of a double-heavy mechanic, verified hash, or present rules.
- Official heavy *shape labels* are from pinned W51 `official-manifest.json`
  (manifest `245114.26.10.13.2000-1-bnet.66137`) and W52 `mechanics.json`:
  Abide/uppercut, Goldtusk/dash, Crown-Splitter/slam, Guillotine/spin,
  Temptation's Hook/projectile. These sources do not measure these authored poses.
  Uppercut/vortex/caster choreography is semantic authoring, not a traced capture.

Every joint angle, blade arc, pose, contact cue, transition, and recovery curve
is authored. No exact D2 distance, hit count, damage, attack time, energy curve,
air flag, or input is inferred from stills. Main owns runtime/camera integration.
No Blockbench/Minecraft/Gradle/native app was run; held-item render alignment and
camera behavior still need main's downstream native-client validation.

## Reproduce / read-only verify

`rtk proxy python3 -B scripts/build_sword_animation_w53.py --verify`

Verifies pinned input bytes, every rig field's raw bytes, each inherited clip's
raw bytes/order, required bones, finite transforms/FK, timing caps, root/scale
policy, endpoint recovery, runtime-only-eight export, and two independent
byte-identical generations. Only the five declared W53 paths may be written;
`--verify` compares saved outputs and writes nothing (including no pycache).
The manifest hashes the generator/model/export/notes, excluding its own hash.
""").encode()


def generate():
    raw = (ROOT / SOURCE).read_bytes()
    source = json.loads(raw)
    clips = author(source)
    art, pack = append_preserving_bytes(raw, clips), encode({"model": MODEL, "animations": clips})
    stats = validate(raw, art, pack)
    result = {ART: art, PACK: pack, NOTES: notes()}
    manifest = {
        "schemaVersion": 1, "stage": "W53", "authoredOn": "2026-10-24", "model": MODEL,
        "baseline": SOURCE, "inheritedAnimationCount": 21, "totalAnimationCount": 29,
        "runtimeExportCount": 8, "authoredNotD2Measured": True,
        "clips": [dict(s, visualIntention=row[3], authoredSlashIntervalSeconds=row[4])
                  for s, row in zip(stats, CUES)],
        "rootPolicy": "No X/Z translation. Floor-fit Y only. Vortex visual yaw 0..360 only; no entity/camera motion.",
        "heldItemPolicy": "Unchanged right equipment pivot, native sword/display mapping and UV; explicit item scale 1.",
        "inputSha256": PINS,
        "outputSha256": {SCRIPT: sha((ROOT / SCRIPT).read_bytes()),
                         **{path: sha(data) for path, data in result.items()}},
        "validation": {"nativeClientVerified": False, "appOrBuildRun": False,
                       "rawRigFieldsPreserved": True, "rawInheritedClipsPreserved": True,
                       "floorSampleRateHz": 200, "floorFitKeyRateHz": 40,
                       "deterministicGeneration": "two independent byte comparisons in --verify"},
    }
    result[MANIFEST] = encode(manifest)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="read-only saved-byte verification")
    args = parser.parse_args()
    check_pins()
    outputs = generate()
    assert outputs == generate(), "Generation is not deterministic"
    if args.verify:
        for path, expected in outputs.items():
            assert (ROOT / path).read_bytes() == expected, "Saved output differs: " + path
        validate((ROOT / SOURCE).read_bytes(), (ROOT / ART).read_bytes(), (ROOT / PACK).read_bytes())
    else:
        for path, data in outputs.items():
            target = ROOT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    check_pins()
    print("W53 " + ("VERIFY PASS (read-only)" if args.verify else "GENERATE PASS"))
    print("Pinned inputs: 16 unchanged; rig fields/raw inherited clips: exact; clips: 21 + 8 = 29; runtime: 8 only")
    print("16 bones/clip; finite keys + FK; linear; item scale 1; root X/Z 0; floor-fit Y; caps/recovery: PASS")
    print("Determinism: two independent generations byte-identical; saved outputs: " + ("MATCH" if args.verify else "WRITTEN"))
    for path, data in outputs.items():
        print(sha(data) + "  " + path)


if __name__ == "__main__":
    main()
