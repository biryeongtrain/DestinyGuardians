#!/usr/bin/env python3
"""W156 Ammit rotation-only sidecar. No shared generators, build or native QA.

Run after canonical source regeneration and before master propagates derived graphs.
Only seven exact Ammit models and the W156 manifest are eligible outputs.
Translations, scales, first-person, geometry and UV are preserved byte-for-byte.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'src/main/resources/assets/destiny/models/'
MODELS = tuple(PREFIX + 'weapon/auto_rifle/ammit_ar2' + suffix + '.json'
               for suffix in ('', '_ads', '_inspect', '_twohand', '_ads_twohand', '_inspect_twohand')) + (
    PREFIX + 'weapon_surface_w123/ammit_ar2.json',)
MANIFEST = 'art/weapons/w156/ammit-pose.json'
CONTEXTS = ('thirdperson_righthand', 'thirdperson_lefthand')
# Immutable dirty-seed evidence, not HEAD hashes. Independent from live main state.
BASELINE = {'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2.json': '07baa6310f8563c21fe6276975830b64c2052e3cd06dd9015855d78956b47673', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_ads.json': '169ca377736c95c053f11a941fea9f7a498e2620518d1f89ce2f34b348c9df61', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_inspect.json': '90fea3e1cd403ac9e27c3321177973851ad8d2c040c84747d2e8b453dfdd9428', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_twohand.json': '0c71893a4c065d17d0f6b3d936cd6410e29b9f2182cf5845e62228abc41c2c2b', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_ads_twohand.json': 'b23f42ef2f015454a39329200324d140934fc4e21efbc5cf9bf3da1456c922ec', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_inspect_twohand.json': '49d6c77385ce93aba412e58dc7bae128841878480516d6f99dc04ca28e4e9e98', 'src/main/resources/assets/destiny/models/weapon_surface_w123/ammit_ar2.json': 'ddc6600f85ff39cc437bd3f6e3d0f44eb79d91e7e638dc4cc0e6ec035c7a5905'}
PRESERVED = {'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2.json': '25fefce3e5c67b4d302ae81bc0b77a945212ea03b9c4cb08813f527b629fa445', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_ads.json': '8bfe78d9c459e721c516ceb68c37d68346d5c1d7fc876a03626bbfc310bf3bb9', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_inspect.json': '5eb6894de8057cc6328b02f3d3663778bb7ca8a6ac9992594f78680091cd5096', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_twohand.json': 'a6e2606be1fe9ca36ac820ef1b061072013a2f46a0270ef9a0a29d4cca57aa28', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_ads_twohand.json': 'e96ba32c5ed3212c6cdea764509714173a24c41cabdc53d820a52e3b016a6ae7', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_inspect_twohand.json': '6df63f8603d1f865d3f7762570aae526a3ce8aab1a71ca865eeaeabe8745f528', 'src/main/resources/assets/destiny/models/weapon_surface_w123/ammit_ar2.json': '21b4254b0889a67136ddbe572a105d5e30ed07a65555b32cea67463920e4a0ef'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def enc(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def preserved_hash(value):
    value = copy.deepcopy(value)
    for context in CONTEXTS:
        value['display'][context].pop('rotation')
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


def rotation(twohand=False):
    # Humanoid ITEM stationary xRot = -pi/10. CROSSBOW_HOLD uses
    # xRot = -pi/2 + .1; yRot = -.3 (right), +.3 (left).
    # ModelPart: Ry(armYaw) Rx(armPitch), then ItemInHandLayer Rx(-90) Ry(180).
    # ItemTransform: Rx(displayX) Ry(displayY) Rz(displayZ).
    # Solve inverse(arm * layer) * Rz(180), where local -Z remains avatar
    # forward -Z and local +Y becomes humanoid-model up -Y.
    if twohand:
        return [round(math.degrees(.1), 6), round(math.degrees(-.3), 6), 0]
    return [72, 0, 0]


def member_span(text, key, start=0):
    """Find a direct object's member value without rewriting unrelated JSON bytes."""
    decoder = json.JSONDecoder()
    index = start
    while text[index].isspace():
        index += 1
    if text[index] != '{':
        raise ValueError('Expected object')
    index += 1
    while True:
        while text[index].isspace() or text[index] == ',':
            index += 1
        if text[index] == '}':
            raise ValueError('Missing member: ' + key)
        name, index = decoder.raw_decode(text, index)
        while text[index].isspace():
            index += 1
        if text[index] != ':':
            raise ValueError('Expected colon')
        index += 1
        while text[index].isspace():
            index += 1
        begin = index
        _, index = decoder.raw_decode(text, index)
        if name == key:
            return begin, index


def patch(raw, twohand=False):
    text = raw.decode('utf-8')
    wanted = rotation(twohand)
    for context in CONTEXTS:
        display_start, _ = member_span(text, 'display')
        context_start, _ = member_span(text, context, display_start)
        start, end = member_span(text, 'rotation', context_start)
        old = json.loads(text[start:end])
        if old != wanted:
            indent = ' ' * (start - text.rfind('\n', 0, start) - 1 - len('"rotation": '))
            replacement = json.dumps(wanted, indent=2).replace('\n', '\n' + indent)
            text = text[:start] + replacement + text[end:]
    return text.encode('utf-8')


def generate(root=ROOT):
    outputs = {}
    for rel in MODELS:
        raw = (root / rel).read_bytes()
        if preserved_hash(json.loads(raw)) != PRESERVED[rel]:
            raise ValueError('Non-rotation input drift: ' + rel)
        outputs[rel] = patch(raw, '_twohand.json' in rel)
    manifest = dict(
        schema=1, stage='W156', weapon='ammit_ar2', generator='scripts/fix_ammit_pose_w156.py',
        policy='Rotation only; every translation/scale, FP context, geometry, UV, texture and parent preserved.',
        seed=dict(head='bfd4b4573fd8651bf1ea850bf829622ccce5c3c2',
                  baselineSha256='ba0d9ccaa50fc5c77c5c9a5ce58ae732f11f25c4505a796572e27f2467feeade'),
        beforeSha256=BASELINE, preservedExceptThirdpersonRotationSha256=PRESERVED,
        outputSha256={p: sha(b) for p, b in outputs.items()},
        rotations=dict(native=rotation(), twohand=rotation(True)),
        evidence=dict(
            observation='W151 README records downward/off-axis third-person fidelity follow-up; native acceptance remains pending.',
            sourceAxes=dict(muzzle=[0, 0, -1], up=[0, 1, 0], anchor=[8, 8, 8]),
            originalDirection='Original W30 source mapping [8+X*s,8+Z*s,8+Y*s] preserved. W126 Grip_backstrap [8,8.885,8.355], Stock_rubber_pad [8,10.43,15.3], bore [8,12.37,-8.91]: muzzle ahead of grip, butt behind grip, grip below bore.',
            references=['art/weapons/w123/ammit_ar2/design.json', 'art/weapons/w123/ammit_ar2/review.md',
                        'docs/qa/2026-10-26/w151/README.md', 'scripts/build_weapons_w30.py'],
            vanillaVersion='26.3; inspected read-only cached minecraft-client.jar with javap -c -p',
            vanillaChain='ModelPart T(shoulder/16) Rz(armZ) Ry(armY) Rx(armX); ItemInHandLayer Rx(-90) Ry(180) T(sign/16,2/16,-10/16); ItemTransform T(display/16) Rx(x) Ry(sign*y) Rz(sign*z) S(scale) T(-.5,-.5,-.5). Left also negates display translation X.',
            stationaryNative='HumanoidModel.poseRightArm/poseLeftArm ITEM: armX=-pi/10. Existing display Rx(90) leaves 18 degrees of elevation in humanoid coordinates; Rx(72) gives level -Z and upright -Y.',
            stationaryTwohand='AnimationUtils.animateCrossbowHold: armX=-pi/2+.1 and armY=-.3*sign. Existing display [.1 rad,-.3 rad,0] already gives level forward -Z and upright -Y; retained exactly. W151 pixels alone do not establish a different rotation.',
            limitations='Head pitch/yaw, arm bob, motion and actual grip/shoulder contact are not certified by this stationary calculation. No arbitrary static two-hand rotation or translation is introduced.'),
        integration=dict(
            order=['Apply export only after comparing every owned before SHA with main.',
                   'Regenerate any canonical W30/W123 art inputs first; this sidecar must run AFTER them.',
                   'rtk proxy python3 -B scripts/fix_ammit_pose_w156.py',
                   'rtk proxy python3 -B scripts/fix_ammit_pose_w156.py --verify',
                   'rtk proxy python3 -B scripts/qa/test_ammit_pose_w156.py',
                   'Master refreshes shared Ammit source/replacement hashes in generate_surface_pack_w123.py and surface manifest; old source pin otherwise rejects the model.',
                   'Master propagates canonical native/twohand thirdperson rotations to Ammit aim/reload/swap/sight derived graphs only, preserving their FP/display translations/scales. Do not rerun broad W30 generation afterward.',
                   'Master performs one integrated native front + side session.'],
            sharedBuildsRun=False, nativeProof=False,
            acceptance=['Inspect native grip and two_hand HIP/ADS third-front AND side at level aim; ensure muzzle forward, top upright, stock behind grip.',
                        'Recheck W151 two_hand observation from side before declaring its fidelity follow-up fixed; its stationary rotation was already correct.',
                        'Confirm unchanged FP/ADS/inspect, reload/swap fallback pose and no UV/geometry/combat/other-weapon drift.']))
    outputs[MANIFEST] = enc(manifest)
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args(argv)
    outputs = generate()
    stale = [p for p, b in outputs.items() if not (ROOT/p).exists() or (ROOT/p).read_bytes() != b]
    if args.verify:
        if stale:
            print('W156 stale:', *stale, sep='\n')
            return 1
    else:
        for rel in stale:
            path = ROOT / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(outputs[rel])
    print(f'W156 {"verified" if args.verify else "patched"}: {len(outputs)} scoped outputs; {len(stale)} changed; native pending')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
