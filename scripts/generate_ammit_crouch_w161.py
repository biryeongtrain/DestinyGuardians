#!/usr/bin/env python3
"""W161 Ammit third-person crouch graphs; flag[1] is server entity isCrouching().

Only seven item graphs, three inherited cuboid models and this stage's manifest
are generated. First-person animation subtrees (including fallbacks) are opaque.
Run with --verify to check without writing. Source drift fails before any writes.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = {
    "src/main/resources/assets/destiny/items/weapon_swap_w113/the_recluse_to_ammit_ar2.json": "2114da6f617a9b85abed53c7bbf3e4b1831fd2a7880b8e1b3446ea357299d3ca",
    "src/main/resources/assets/destiny/items/weapon_swap_w113/beloved_to_ammit_ar2.json": "dc5cd86fed3422d876f5a61f267d7bf2e0c6236ecb5017cd63bd658f4fdf0284",
    "src/main/resources/assets/destiny/items/weapon_swap_w113/austringer_to_ammit_ar2.json": "e95f74f767b2ebf63bd1aab8de54d6965430247a3cb2e89a928fb3bcc6853523",
    "src/main/resources/assets/destiny/items/weapon_sight_w151/ammit_ar2.json": "cef53065c2a86a8bb6b71ad66580d49d53e6c0f02aed5f90ae638b91dd87abff",
    "src/main/resources/assets/destiny/items/weapon/ammit_ar2.json": "e029d018bbb12dba3a5b941afa36e2d408a6b93c387d64bcef3ebb4f7dad43a4",
    "src/main/resources/assets/destiny/items/weapon_reload_w69/ammit_ar2.json": "cb09f44be0f8c139827eb99b183e28a73d938a32099d550664b6fdf853e202f8",
    "src/main/resources/assets/destiny/items/weapon_aim_w70/ammit_ar2.json": "67e383e83ee437165aac45fc51dd585b93df444457fd9d6cc9c4abaffdc0264c"
}
PROTECTED = {
    "src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_twohand.json": "0c71893a4c065d17d0f6b3d936cd6410e29b9f2182cf5845e62228abc41c2c2b",
    "src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2.json": "b531f95f712e369098043ebb73a91065130bf7f6dcaeac185ad550d9d9f3ebf9",
    "src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_ads_twohand.json": "b23f42ef2f015454a39329200324d140934fc4e21efbc5cf9bf3da1456c922ec",
    "src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_ads.json": "b2d1b7f8e9e7af4d59bb4e30307a551d7d8818c671fda48adcd839de563c066c",
    "src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_inspect_twohand.json": "49d6c77385ce93aba412e58dc7bae128841878480516d6f99dc04ca28e4e9e98",
    "src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_inspect.json": "97ad6a7443da2e6ec36e4f3031892f4cad2fd593c85a5a64e1ed356685e76e2b",
    "art/weapons/w160/ammit-pose.json": "e767f9834e6be7befe11c579374313e159b6d04da6bad43048358b02615feb91",
    "scripts/fix_ammit_pose_w160.py": "1fe07832bf185593901c40a9f9d482fa3dd327392838b8651900f1c0a085ae50"
}
MANIFEST = "art/weapons/w161/ammit-crouch.json"
THIRD = ("thirdperson_righthand", "thirdperson_lefthand")
FIRST = ("firstperson_righthand", "firstperson_lefthand")
POSES = {"hip": "ammit_ar2_twohand", "ads": "ammit_ar2_ads_twohand",
         "inspect": "ammit_ar2_inspect_twohand"}
CANONICAL = {"destiny:weapon/auto_rifle/" + name: pose for pose, name in POSES.items()}
OLD = dict(rotation=[5.729578, -17.188734, 0], translation=[0, -2, 2], scale=[.7]*3)
CORRECTED = dict(rotation=[28.64789, -17.188734, 0],
                 translation=[0, -1.837142, 1.792719], scale=[.7]*3)
GRIP = [8, 8.885, 8.355]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def model_path(identifier):
    namespace, name = identifier.split(":")
    return f"src/main/resources/assets/{namespace}/models/{name}.json"


def child_id(pose):
    return f"destiny:weapon_pose_w161/ammit_ar2_{pose}"


def wrapper(leaf):
    return {
        "type": "minecraft:select", "property": "minecraft:display_context",
        "cases": [{"when": list(THIRD), "model": {
            "type": "minecraft:condition", "property": "minecraft:custom_model_data",
            "index": 1,
            "on_true": {"type": "minecraft:model", "model": child_id(CANONICAL[leaf["model"]])},
            "on_false": copy.deepcopy(leaf)}}],
        "fallback": copy.deepcopy(leaf)}


def unwrap(node):
    """Recover the seeded graph exactly; reject damaged or unexpected W161 nodes."""
    if isinstance(node, list):
        return [unwrap(v) for v in node]
    if not isinstance(node, dict):
        return node
    if node.get("property") == "minecraft:display_context":
        leaf = node.get("fallback", {})
        if isinstance(leaf, dict) and leaf.get("model") in CANONICAL:
            if node != wrapper(leaf):
                raise ValueError("Malformed W161 third-person wrapper")
            return copy.deepcopy(leaf)
    if str(node.get("model", "")).startswith("destiny:weapon_pose_w161/"):
        raise ValueError("W161 model outside its exact wrapper")
    return {k: unwrap(v) for k, v in node.items()}


def transform(node):
    if isinstance(node, list):
        return [transform(v) for v in node]
    if not isinstance(node, dict):
        return node
    if node.get("type") == "minecraft:model" and node.get("model") in CANONICAL:
        return wrapper(node)
    out = {}
    for key, value in node.items():
        if key == "cases" and node.get("property") == "minecraft:display_context":
            out[key] = []
            for case in value:
                when = case["when"] if isinstance(case["when"], list) else [case["when"]]
                # Do not traverse animated FP lists or their canonical fallback.
                out[key].append(copy.deepcopy(case) if set(when) <= set(FIRST) else transform(case))
        else:
            out[key] = transform(value)
    return out


def walk(node, path=""):
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            yield from walk(v, path + "/" + k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, path + "/" + str(i))


def fingerprint(node, key):
    return [{"path": p + "/" + key, "sha256": sha(encode(v[key]))}
            for p, v in walk(node) if key in v]


def firstperson(node):
    out = []
    for p, n in walk(node):
        if n.get("property") != "minecraft:display_context":
            continue
        for i, case in enumerate(n["cases"]):
            when = case["when"] if isinstance(case["when"], list) else [case["when"]]
            if set(when) <= set(FIRST):
                out.append({"path": p + "/cases/" + str(i), "sha256": sha(encode(case))})
    return out


def display_point(point, transform, hand=1):
    x, y, z = [s * (v - 8) for v, s in zip(point, transform["scale"])]
    a, b, c = map(math.radians, transform["rotation"])
    b *= hand
    c *= hand
    x, y = math.cos(c)*x-math.sin(c)*y, math.sin(c)*x+math.cos(c)*y
    x, z = math.cos(b)*x+math.sin(b)*z, -math.sin(b)*x+math.cos(b)*z
    y, z = math.cos(a)*y-math.sin(a)*z, math.sin(a)*y+math.cos(a)*z
    t = transform["translation"]
    return [x + hand*t[0], y + t[1], z + t[2]]


def generate(root=ROOT):
    protected = {}
    for path, expected in PROTECTED.items():
        actual = sha((root/path).read_bytes())
        if actual != expected:
            raise ValueError("Preserved source drift: " + path)
        protected[path] = {"beforeSha256": expected, "afterSha256": actual}
    candidate = json.loads((root/"art/weapons/w160/ammit-pose.json").read_text())
    assert candidate["candidateThirdperson"] == {hand: CORRECTED for hand in THIRD}
    outputs, graphs, bases = {}, {}, {}
    for identifier, pose in CANONICAL.items():
        path = model_path(identifier)
        base = json.loads((root/path).read_text())
        before = {hand: base["display"][hand] for hand in THIRD}
        if before != {hand: OLD for hand in THIRD}:
            raise ValueError("Recalculate crouch transform for base: " + path)
        child = {"parent": identifier, "display": {hand: copy.deepcopy(CORRECTED) for hand in THIRD}}
        outputs[model_path(child_id(pose))] = encode(child)
        bases[pose] = {"parent": identifier, "oldThirdperson": before,
                       "newThirdperson": child["display"]}
    for path, expected in BASELINE.items():
        original = unwrap(json.loads((root/path).read_text()))
        if sha(encode(original)) != expected:
            raise ValueError("Seeded graph drift: " + path)
        updated = transform(original)
        if unwrap(updated) != original:
            raise ValueError("Source restoration failed: " + path)
        before_fp, after_fp = firstperson(original), firstperson(updated)
        before_frames, after_frames = fingerprint(original, "entries"), fingerprint(updated, "entries")
        if before_fp != after_fp or before_frames != after_frames:
            raise ValueError("First-person/animation preservation failed: " + path)
        outputs[path] = encode(updated)
        graphs[path] = {
            "beforeSha256": expected, "afterSha256": sha(outputs[path]),
            "restoredSourceSha256": sha(encode(unwrap(updated))),
            "firstpersonBefore": before_fp, "firstpersonAfter": after_fp,
            "animatedEntriesBefore": before_frames, "animatedEntriesAfter": after_frames,
            "thirdpersonWrappers": sum(n.get("property") == "minecraft:display_context"
                                      and n.get("fallback", {}).get("model") in CANONICAL
                                      for _, n in walk(updated))}
    outputs[MANIFEST] = encode({
        "schema": 1, "stage": "W161", "weapon": "ammit_ar2",
        "generator": "scripts/generate_ammit_crouch_w161.py",
        "status": "product graphs generated; server transport integration and native acceptance pending",
        "contract": {"condition": "minecraft:custom_model_data", "booleanIndex": 1,
                     "serverSource": "actual live combat Ammit server entity isCrouching()",
                     "gripBooleanIndex": 0,
                     "lifecycle": "Main updates/clears transient flag; item snapshots preserve it",
                     "standingRelease": "flag[1]=false selects original pose immediately, independent of ADS progress/key state"},
        "basis": "art/weapons/w160/ammit-pose.json",
        "rationale": [
            "26.3 HumanoidModel adds +0.4 radians to both arm pitches after crossbow posing; use Rx(degrees(0.1+0.4)).",
            "All three canonical twohand bases have identical third-person transforms.",
            "Translation = oldTranslation + oldRotation*(scale*(grip-8)) - newRotation*(scale*(grip-8)); anchor backstrap [8,8.885,8.355].",
            "Use only thirdperson_righthand/lefthand display-context cases and item CMD boolean flag[1].",
            "W160 lingering ADS standing-release hazard is gated by server crouch state, independent of the selected pose string.",
            "Inherited parent preserves all elements, UVs, textures and other display contexts; no new emitted elements.",
            "Art skill and Ace/Izanagi study reviewed; existing Ammit identity and geometry retained."
        ],
        "bases": bases, "graphs": graphs, "preservedSources": protected,
        "generatedModels": {p: sha(b) for p, b in outputs.items() if "/models/" in p},
        "native": {"status": "pending; unavailable this turn", "operations": 0,
                   "visualAcceptance": False,
                   "required": ["front and side standing HIP", "crouched HIP/ADS/inspect",
                                "fire and standing release with lingering ADS",
                                "right/left hand backstrap, stock and support-hand contact",
                                "representative first-person ADS/reload/swap preservation"]},
        "centralJUnit": {"class": "AmmitCrouchModelsW161Test", "status": "pending main central codec run"}
    })
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    outputs = generate()  # All guards run before the first write.
    stale = [p for p, b in outputs.items() if not (ROOT/p).exists() or (ROOT/p).read_bytes() != b]
    if args.verify and stale:
        print("W161 stale: " + ", ".join(stale))
        return 1
    if not args.verify:
        for path in stale:
            (ROOT/path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT/path).write_bytes(outputs[path])
    print("W161 verified: 7 graphs, 21 third-person wrappers, 3 inherited models; native acceptance pending")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

