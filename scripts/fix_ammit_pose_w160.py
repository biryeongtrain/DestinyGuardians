#!/usr/bin/env python3
"""Document an INACTIVE Ammit crouched-ADS candidate; never write model resources.

W156's standing crossbow inverse omits HumanoidModel's subsequent crouch +0.4.
The saved release frame also shows why applying that inverse to every ADS frame
is unsafe. Only the W160 sidecar is emitted until master can review native motion.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2_ads_twohand.json'
MANIFEST = 'art/weapons/w160/ammit-pose.json'
CONTEXTS = ('thirdperson_righthand', 'thirdperson_lefthand')
BEFORE_SHA256 = 'b23f42ef2f015454a39329200324d140934fc4e21efbc5cf9bf3da1456c922ec'
OLD = dict(rotation=[5.729578, -17.188734, 0], translation=[0, -2, 2], scale=[.7]*3)
CROUCH_RADIANS = .4
GRIP = [8, 8.885, 8.355]
STOCK = [8, 10.43, 15.3]
MUZZLE = [8, 12.37, -8.08]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def display_point(point, rotation):
    """Centered/scaled point in ItemTransform space, before its translation."""
    x, y, z = [.7*(v-8) for v in point]
    a, b, _ = map(math.radians, rotation)
    x, z = math.cos(b)*x+math.sin(b)*z, -math.sin(b)*x+math.cos(b)*z
    return [x, math.cos(a)*y-math.sin(a)*z, math.sin(a)*y+math.cos(a)*z]


def candidate():
    rotation = [round(math.degrees(.1+CROUCH_RADIANS), 6), OLD['rotation'][1], 0]
    old, new = display_point(GRIP, OLD['rotation']), display_point(GRIP, rotation)
    translation = [round(t+a-b, 6) for t, a, b in zip(OLD['translation'], old, new)]
    return dict(rotation=rotation, translation=translation, scale=[.7]*3)


def evidence(path, digest, observation):
    return dict(path=path, sha256=digest, observation=observation)


def generate(root=ROOT):
    raw = (root/MODEL).read_bytes()
    if sha(raw) != BEFORE_SHA256:
        raise ValueError('Active ADS source drift; re-evaluate the inactive candidate: '+MODEL)
    return {
        'schema': 1, 'stage': 'W160', 'weapon': 'ammit_ar2',
        'generator': 'scripts/fix_ammit_pose_w160.py',
        'status': 'inactive-candidate; visual acceptance unsatisfied',
        'activeResourceChanges': [], 'nativeOperations': 0, 'nativePixelAcceptance': False,
        'activeSource': dict(path=MODEL, beforeSha256=BEFORE_SHA256, afterSha256=sha(raw)),
        'candidateThirdperson': {context: candidate() for context in CONTEXTS},
        'currentThirdperson': {context: OLD for context in CONTEXTS},
        'constants': dict(crossbowArmPitch='-pi/2 + head.xRot + 0.1',
                          holdingArmYaw='head.yRot - sign*0.3',
                          subsequentCrouchArmPitchRadians=CROUCH_RADIANS,
                          itemLayer='Rx(-90) Ry(180) T(sign,2,-10)/16',
                          itemDisplay='T(display/16) Rx(x) Ry(sign*y) Rz(sign*z) S(0.7) T(-0.5)',
                          sourceMuzzleAxis=[0, 0, -1], gripBackstrap=GRIP,
                          stockRubberPad=STOCK, muzzleDarkRecess=MUZZLE,
                          anchorSource='src/main/resources/assets/destiny/models/weapon_surface_w123/ammit_ar2.json'),
        'rationale': [
            'W151 sample06 and W156 sample08 show the crouched two-hand muzzle below the shoulder line; standing W156 front is substantially more level.',
            'Read-only javap of the cached 26.3 client confirms setupAnim bytecode 433..475: after poseRightArm/poseLeftArm and setupAttackAnimation, crouching adds 0.4f to both arm xRot values.',
            'For stationary level head, display Rx(degrees(0.1+0.4)) with existing Ry(degrees(-0.3)) cancels that additional pitch. W156 tested only the standing chain.',
            'Translation is derived, not visually guessed: oldTranslation + oldDisplayRotation*(0.7*(grip-8)) - candidateDisplayRotation*(0.7*(grip-8)). Both reflected hands keep the same backstrap point.',
            'This levels the local -Z bore in the crouched stationary calculation, rotating the stock toward the shoulder plane around the retained grip; actual shoulder and support-hand contact remain unaccepted.'
        ],
        'whyInactive': [
            'W156 sample15 has sneaking=false while mainModel remains weapon_sight_w151/ammit_ar2. ADS release can retain the canonical ADS fallback while the arm is already standing; full static crouch compensation then elevates the bore.',
            'The owned model display contexts cannot distinguish crouching from the lingering ADS selector. No shared item graph or Java changes are authorized.',
            'No contemporary W151/W156 side PNG was found in saved QA or their temporary native directories. The actual W32 side reference is older geometry/fixture evidence only.',
            'No current native call surface or new native capture is available in W160. Historical pixels and stationary math do not establish a safe active transition or final Destiny fidelity.'
        ],
        'historicalPixels': [
            evidence('docs/qa/2026-10-26/w151/native/frames/w151-ammit-third-aim-sample-06.png',
                     '3b4c331d2ba807fa15441b0108feaea087d1690e5760d0085d2d7fb274ac7bcc',
                     'Actual opened front capture: crouched rifle muzzle points down.'),
            evidence('docs/qa/2026-10-26/w156/native/frames/w156-ammit-twohand-front-corrected.png',
                     'd5b32f999cf120744dfc6b32605b6e695634c7034eb9974612253728290cad86',
                     'Actual opened idle front; valid Ammit. Excludes incorrectly named uncorrected Ace capture.'),
            evidence('docs/qa/2026-10-26/w156/native/frames/w156-ammit-twohand-third-fire-sample-08.png',
                     '667e9afafcb13b0ca7fbc17d7219d5143ac9c107b66345769dc621552429cd51',
                     'Actual opened front; sequence before-state tick2521, pitch0, sneaking=true, usingItem=false, sight_w151 route.'),
            evidence('docs/qa/2026-10-23/w32/detail/ammit-side-r2.png',
                     'adbe0ecf6b7d63b84bb3f965c9b01b555d254c556c51dfd7aa71c6b63ecc1290',
                     'Actual opened older side fixture; shows stock/shoulder relationship, cannot certify current W126 geometry or current native posture.')
        ],
        'runtimeSources': [
            'scripts/fix_ammit_pose_w156.py', 'scripts/qa/test_ammit_pose_w156.py',
            'src/main/java/kim/biryeong/destiny/weapon/WeaponAiming.java',
            'src/main/resources/assets/destiny/items/weapon_sight_w151/ammit_ar2.json',
            'docs/qa/2026-10-26/w156/native/sequences/w156-ammit-twohand-third-fire.json',
            'docs/qa/NATIVE_QUEUE.md'
        ],
        'vanillaClassSha256': {
            'net/minecraft/client/model/HumanoidModel.class': 'd86498297d0837e473898a1d0c801b9c0b50182058982e8e257fd0d45bf896db',
            'net/minecraft/client/model/AnimationUtils.class': 'a5400fcfd185a985d3ae2b6b4a386436fe44f1b5ea4482e4a86b18e7ba18dfac',
            'net/minecraft/client/renderer/entity/layers/ItemInHandLayer.class': '313dca7407a757a377db4e2c9ebaf7c340df37c0b042f351fe6b3821aefa7c60',
            'net/minecraft/client/resources/model/cuboid/ItemTransform.class': '5753c00a8eab6d9ca2f284e2ba59aab1fecfe1e0d4ae89c2694ea81ab41273ae'
        },
        'effectiveScope': dict(
            proposedOnly=MODEL,
            explanation='Sight W151 and aim W70 select animation frames only in first person, then use canonical pose/grip fallback in third person. Crouched settled ADS reaches ammit_ar2_ads_twohand. No reason to edit 427 owned models.',
            derivedChangesNecessary=[],
            preserved='All active resources including FP, geometry, UV, textures, native grip, HIP, inspect, audio, item graphs and Java remain byte-identical.'),
        'masterFollowUp': [
            'Candidate is not wired to runtime; do not treat the sidecar as an integrated product fix.',
            'In a later authorized native session compare actual front AND side at standing HIP, crouched settled ADS, fire and release; inspect stock, backstrap and support hand.',
            'Resolve the standing-arm/lingering-ADS transition before activating this exact-context candidate. No native, Gradle, dependency or shared build was run here.'
        ]
    }


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args(argv)
    raw = encode(generate())
    path = ROOT/MANIFEST
    if args.verify:
        if not path.exists() or path.read_bytes() != raw:
            print('W160 inactive sidecar stale:', MANIFEST)
            return 1
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    print('W160 inactive candidate verified' if args.verify else 'W160 inactive candidate documented')
    print('0 active resource changes; native visual acceptance unsatisfied')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
