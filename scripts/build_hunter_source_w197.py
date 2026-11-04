#!/usr/bin/env python3
"""Retarget W196 evaluated Arc Staff matrices; standard run needs no SSD/Blender.

rtk proxy python3 -B scripts/build_hunter_source_w197.py
--extract /absolute/path/to/hunter_arc_staff.json.gz refreshes the pinned dataset.
--verify reconstructs and compares saved products without writing.
Only the six W197 Hunter owned paths may be written. No subprocesses.
"""
import argparse
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_animation_h20 as h20

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'art/blockbench/animations/guardian_hunter_h26_r2.bbmodel'
DATA = ROOT / 'art/weapons/w197/hunter-source-motion.json'
ART = ROOT / 'art/blockbench/animations/guardian_hunter_w197_r1.bbmodel'
PACK = ROOT / 'src/main/resources/destiny/animation/hunter_w197.animation.json'
MODEL = 'guardian_hunter_w197_r1'
START, ATTACK = 'h15_super_arc_start', 'h15_super_arc_attack'
# Source +Y is anatomical left (known left foot), +Z up, +X forward
# (toe heads ahead of ankles and face heads ahead of skull). Proper rotation.
# This anatomical forward choice is still awaiting native camera verification.
C = [[0, -1, 0, 0], [0, 0, 1, 0], [-1, 0, 0, 0], [0, 0, 0, 1]]
MAP = {
    'phip_hip': 'C7C0BA6E', 'pw_waist': 'A252A6A2', 'pc_chest': 'A352A6A2',
    'h_ph_head': '7E92D640',
    'pra_right_arm': '17025F50', 'prfa_right_forearm': 'A3781DCD',
    'pla_left_arm': 'D1232BA2', 'plfa_left_forearm': '897A1504',
    'prl_right_leg': '9F0FD28C', 'prfl_right_foreleg': '8BD44A3F',
    'pll_left_leg': '695DAF09', 'plfl_left_foreleg': '35B14D1B',
}
EXTRA = ['1A5C68E5', 'A152A6A2', '0D4EBB10', '0E4EBB10',
         'A9D76416', '038E2D3A', 'DE9D6BEA', '8C83CB67', 'B9B9E05D', '0F8B505D']
PHASES = {
    START: {'tag': '80A8A922', 'length': .5, 'neutralFrame': 44,
            'phaseSeconds': [[0, 0], [.025, 0], [.12, .3], [.2, 13/30],
                             [.27, .6], [.4, 1.1], [.45, 1.3], [.5, 43/30]],
            'blendSeconds': [[0, 0], [.025, 1], [.45, 1], [.5, 0]]},
    ATTACK: {'tag': '80A8A937', 'length': .35, 'neutralFrame': 40,
             'phaseSeconds': [[0, 0], [.035, .1], [.1, .3], [.15, 17/30],
                              [.24, 28/30], [.315, 1.2], [.35, 1.3]],
             'blendSeconds': [[0, 0], [.0175, 1], [.315, 1], [.35, 0]],
             'contact': {'targetSeconds': .1, 'sourceFrame': 10,
                         'reason': 'first outward right-hand sweep; gameplay alignment, not decoded damage event'}},
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rotation(m):
    """Remove tiny evaluated numerical shear/scale, never the outer FBX matrix."""
    x = h19.unit([m[i][0] for i in range(3)])
    y0 = [m[i][1] for i in range(3)]
    y = h19.unit(h19.sub(y0, h19.mul(x, h19.dot(x, y0))))
    z = h19.cross(x, y)
    assert h19.dot(z, [m[i][2] for i in range(3)]) > .99, 'Non-rigid/reflected source matrix'
    return [[x[i], y[i], z[i], 0] for i in range(3)] + [[0, 0, 0, 1]]


def quat(m):
    # Largest diagonal branch remains stable at 180 degrees.
    tr = sum(m[i][i] for i in range(3))
    if tr > 0:
        s = math.sqrt(tr+1)*2
        return [s/4, (m[2][1]-m[1][2])/s, (m[0][2]-m[2][0])/s, (m[1][0]-m[0][1])/s]
    i = max(range(3), key=lambda k: m[k][k])
    j, k = (i+1) % 3, (i+2) % 3
    s = math.sqrt(1+m[i][i]-m[j][j]-m[k][k])*2
    q = [0]*4
    q[0], q[i+1] = (m[k][j]-m[j][k])/s, s/4
    q[j+1], q[k+1] = (m[j][i]+m[i][j])/s, (m[k][i]+m[i][k])/s
    return q


def qmatrix(q):
    w, x, y, z = q
    return [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w), 0],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w), 0],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y), 0], [0, 0, 0, 1]]


def slerp(a, b, t):
    a, b = quat(a), quat(b)
    dot = sum(x*y for x, y in zip(a, b))
    if dot < 0:
        b, dot = [-v for v in b], -dot
    if dot > .9995:
        q = [x+(y-x)*t for x, y in zip(a, b)]
        q = [v/math.sqrt(sum(x*x for x in q)) for v in q]
    else:
        angle = math.acos(max(-1, min(1, dot)))
        q = [(x*math.sin((1-t)*angle)+y*math.sin(t*angle))/math.sin(angle) for x, y in zip(a, b)]
    return qmatrix(q)


def curve(keys, t):
    for (ta, a), (tb, b) in zip(keys, keys[1:]):
        if t <= tb+1e-10:
            return a+(b-a)*max(0, min(1, (t-ta)/(tb-ta)))
    return keys[-1][1]


def extract(path):
    compressed = path.read_bytes()
    raw = gzip.decompress(compressed)
    source = json.loads(raw)
    assert source['sampleSpace'] == 'armature_object' and len(source['bones']) == 72
    assert source['sourceFbxSHA256'] == '99355ab41c746ea4665f763036480e01d8559b256ca9c25b3e5df33a5d8c8add'
    selected = sorted(set(MAP.values()) | set(EXTRA))
    # Look up the evaluated sample's own hash names, NEVER bone-map Index order.
    indices = {b['name']: i for i, b in enumerate(source['bones'])}
    clips = {}
    for c in source['clips']:
        if c['tag'] not in ('80A8A922', '80A8A937'):
            continue
        clips[c['tag']] = {k: v for k, v in c.items() if k not in ('frames', 'maxBoneHeadDisplacement')}
        clips[c['tag']]['frames'] = [
            {'frame': f['frame'], 'seconds': f['seconds'],
             'matrices': {name: [[round(v, 9) for v in row] for row in f['matrices'][indices[name]]]
                          for name in selected}}
            for f in c['frames']]
    result = {'schemaVersion': 1,
              'provenance': {k: v for k, v in source.items() if k not in ('bones', 'clips')},
              'sampleSHA256': sha(raw), 'sampleGzipSHA256': sha(compressed),
              'samplePath': 'docs/qa/2026-10-27/w196/samples/hunter_arc_staff.json.gz',
              'acceptedModelSHA256': sha(SOURCE.read_bytes()),
              'bones': {b['name']: b for b in source['bones']},
              'sampledBoneIds': selected, 'targetMap': MAP, 'clips': clips,
              'retarget': {'basis': C, 'targetSpace': '+X right, +Y up, -Z front; Rz*Ry*Rx',
                  'basisEvidence': '+Y left from b_l_foot; +Z height; +X toe/face anterior rest heads',
                  'basisStatus': 'anatomical choice; native camera unverified',
                  'formula': 'D=Rpose*transpose(Rrest); K=transpose(Dneutral)*transpose(C)*Tready_world; T=C*D*K; local=transpose(Tparent)*T; remove bind at final Euler export',
                  'chainCollapse': 'spine1+2 -> waist; spine3 -> chest; neck1+2+head -> head; clavicle+upperarm -> upperarm; forearm retained; fingers omitted',
                  'limbProvenance': 'left arm 038E2D3A>D1232BA2>897A1504>8C83CB67 mirrors named right clavicle>17025F50>A3781DCD>DE9D6BEA at positive source Y; hip>695DAF09>35B14D1B>b_l_foot mirrors hip>9F0FD28C>8BD44A3F>b_r_foot; intermediate joints located by rest head heights and parent paths, not list order',
                  'staff': 'right hand DE9D6BEA delta calibrates accepted item world orientation; left wrist constrained to right-item local (0,6,0); source elbow attitude biases IK; existing display/left reflection/twohand compensation unchanged',
                  'root': 'no source translation; no pedestal rotation; skin-floor Y correction only, no entity flight; no horizontal root motion',
                  'adaptation': 'finite rigid rotations, quaternion interpolation; neutral blend only at declared clip ends; coupled reach projection for fixed Steve arm lengths; 200Hz base plus source-evaluated midpoint refinement when linear support gap or floor error exceeds .035 model units, max256 keys/channel',
                  'legs': 'hip/knee/ankle heads define anatomical bend-plane frames F; target thigh=C*F(t)*transpose(F(neutral))*transpose(C)*Tready_thigh; positive knee hinge flex=clamp(source_bend-source_neutral_bend+accepted_ready_bend,0,155deg). Scalar geometric flex angles are not copied local Euler channels; prevents hashed roll axes causing hyperextension',
                  'phases': PHASES}}
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(result, separators=(',', ':'), allow_nan=False)+'\n')


def validate_data(data):
    assert data['targetMap'] == MAP and data['retarget']['basis'] == C
    assert data['retarget']['phases'] == PHASES
    assert data['acceptedModelSHA256'] == sha(SOURCE.read_bytes()), 'Accepted model drift'
    assert data['sampleSHA256'] == 'b1395f5c3a5907cf003c480c3854dc7b9170a67d080acf20fb02f7e8a3798ea7'
    assert data['provenance']['sourceManifestSHA256'] == '19ed4b5677ef2bf44aebf9ed9d2dc1f36ab4b27022553a67510fa570590d1243'
    assert data['provenance']['sourceFbxSHA256'] == '99355ab41c746ea4665f763036480e01d8559b256ca9c25b3e5df33a5d8c8add'
    bones = data['bones']
    for chain in (['C7C0BA6E', '695DAF09', '35B14D1B', '0F8B505D'],
                  ['C7C0BA6E', '9F0FD28C', '8BD44A3F', 'B9B9E05D'],
                  ['A352A6A2', '038E2D3A', 'D1232BA2', '897A1504', '8C83CB67'],
                  ['A352A6A2', 'A9D76416', '17025F50', 'A3781DCD', 'DE9D6BEA']):
        for parent, child in zip(chain, chain[1:]):
            assert bones[child]['parent'] == parent, (parent, child)
    for tag, count in [('80A8A922', 44), ('80A8A937', 40)]:
        clip = data['clips'][tag]
        assert clip['sampleCount'] == len(clip['frames']) == count
        assert [f['frame'] for f in clip['frames']] == list(range(1, count+1))
        for i, f in enumerate(clip['frames']):
            assert abs(f['seconds']-i/30) < 1e-8
            assert set(f['matrices']) == set(data['sampledBoneIds'])
            for matrix in f['matrices'].values():
                assert len(matrix) == 4 and all(len(row) == 4 for row in matrix)
                assert all(math.isfinite(v) for row in matrix for v in row)
                assert matrix[3] == [0, 0, 0, 1]
                rotation(matrix)


def source_at(data, tag, seconds):
    frames = data['clips'][tag]['frames']
    i = min(len(frames)-1, int(seconds*30+1e-10))
    j = min(len(frames)-1, i+1)
    f = max(0, min(1, seconds*30-i))
    return {n: slerp(rotation(frames[i]['matrices'][n]), rotation(frames[j]['matrices'][n]), f)
            for n in data['sampledBoneIds']}


def source_points(data, tag, seconds):
    frames = data['clips'][tag]['frames']
    i = min(len(frames)-1, int(seconds*30+1e-10))
    j = min(len(frames)-1, i+1)
    f = max(0, min(1, seconds*30-i))
    return {n: [frames[i]['matrices'][n][k][3]*(1-f)+frames[j]['matrices'][n][k][3]*f
                for k in range(3)] for n in data['sampledBoneIds']}


def leg_frame(points, names):
    hip, knee, ankle = [points[n] for n in names]
    down = h19.unit(h19.sub(knee, hip))
    lower = h19.unit(h19.sub(ankle, knee))
    # Anatomical bend plane, independent of arbitrary hashed bone roll axes.
    x = h19.unit(h19.cross(down, lower))
    y = h19.mul(down, -1)
    z = h19.cross(x, y)
    frame = [[x[i], y[i], z[i], 0] for i in range(3)]+[[0, 0, 0, 1]]
    return frame, math.degrees(math.acos(max(-1, min(1, h19.dot(down, lower)))))


def bind_angles(matrix, bind):
    # h19.euler uses the same Rz Ry Rx convention as target FK.
    return h19.sub(h19.euler(matrix), bind)


def pose_from_source(model, data, tag, seconds, neutral_frame, ready):
    current = source_at(data, tag, seconds)
    neutral = source_at(data, tag, (neutral_frame-1)/30)
    accepted = h19.fk(model, ready)
    groups = {g['name']: g for g in model['groups']}
    p = copy.deepcopy(ready)
    points = source_points(data, tag, seconds)
    neutral_points = source_points(data, tag, (neutral_frame-1)/30)
    legs = {}
    for upper, lower, names in (
            ('prl_right_leg', 'prfl_right_foreleg', ['9F0FD28C', '8BD44A3F', 'B9B9E05D']),
            ('pll_left_leg', 'plfl_left_foreleg', ['695DAF09', '35B14D1B', '0F8B505D'])):
        frame, bend = leg_frame(points, names)
        ref, neutral_bend = leg_frame(neutral_points, names)
        delta = h15.mm(C, h15.mm(frame, h15.mm(h19.inverse_rotation(ref), h19.inverse_rotation(C))))
        legs[upper] = h15.mm(delta, rotation(accepted[upper]))
        # A target knee has one positive flex axis. Preserve measured source
        # flex relative to the accepted neutral, without inventing Euler sums.
        # Bend magnitudes are scalar anatomical joint angles, not Euler curves.
        flex = max(0, min(155, bend-neutral_bend+ready[lower][0]))
        legs[lower] = h15.mm(legs[upper], h15.rot([flex, 0, 0]))
    for target, source in MAP.items():
        rest = rotation(data['bones'][source]['restMatrix'])
        deform = h15.mm(current[source], h19.inverse_rotation(rest))
        neutral_deform = h15.mm(neutral[source], h19.inverse_rotation(rest))
        calibration = h15.mm(h19.inverse_rotation(neutral_deform),
                            h15.mm(h19.inverse_rotation(C), rotation(accepted[target])))
        desired = h15.mm(C, h15.mm(deform, calibration))
        if target in legs:
            desired = legs[target]
        # Evaluate actual target parent after previously mapped ancestors. This
        # collapses missing source spine/clavicle/neck joints in matrix space.
        actual = h19.fk(model, p)[target]
        local_now = h15.rot(h19.add(groups[target].get('rotation', [0]*3), p[target]))
        parent = h15.mm(rotation(actual), h19.inverse_rotation(local_now))
        p[target] = bind_angles(h15.mm(h19.inverse_rotation(parent), desired),
                                groups[target].get('rotation', [0]*3))
    hand = 'DE9D6BEA'
    # Same rest-basis formula simplifies algebraically to pose * neutral^-1.
    delta = h15.mm(C, h15.mm(current[hand], h15.mm(h19.inverse_rotation(neutral[hand]), h19.inverse_rotation(C))))
    item = h15.mm(delta, rotation(accepted['pri_right_item']))
    return p, item


def blend_pose(a, b, weight):
    if weight == 0:
        return copy.deepcopy(a)
    if weight == 1:
        return copy.deepcopy(b)
    return {name: h19.euler(slerp(h15.rot(a[name]), h15.rot(b[name]), weight)) for name in a}


def attach_staff(model, p, item):
    """Project a source-driven wrist into both arm reach spheres, then use H19 IK.

    Source right/left elbow positions from calibrated FK select bend direction.
    The item orientation stays source-driven; only wrist position is adapted to
    the shorter target limbs. No authored replacement swing curve is introduced.
    """
    matrices = h19.fk(model, p)
    wrist = h19.point(matrices['pri_right_item'], [0, 0, 0])
    original = wrist[:]
    offset = h19.vector(item, [0, 6, 0])
    centers = [h19.point(matrices['pra_right_arm'], [0, 0, 0]),
               h19.sub(h19.point(matrices['pla_left_arm'], [0, 0, 0]), offset)]
    # 11.1596 is the actual target arm reach; leave .25u from singular extension.
    radius = 10.9
    for _ in range(48):
        for center in centers:
            v = h19.sub(wrist, center)
            if h19.norm(v) > radius:
                wrist = h19.add(center, h19.mul(h19.unit(v), radius))
    for side, arm, fore, endpoint in (
            ('right', 'pra_right_arm', 'prfa_right_forearm', wrist),
            ('left', 'pla_left_arm', 'plfa_left_forearm', h19.add(wrist, offset))):
        bias = h19.sub(h19.point(matrices[fore], [0, 0, 0]), h19.point(matrices[arm], [0, 0, 0]))
        along = h19.unit(h19.sub(endpoint, h19.point(matrices[arm], [0, 0, 0])))
        if h19.norm(h19.sub(bias, h19.mul(along, h19.dot(bias, along)))) < .01:
            bias = [1 if side == 'right' else -1, -1, .2]
        h19.solve_arm(model, p, side, endpoint, bias)
    h20.aim_right(model, p, item)
    return h19.norm(h19.sub(wrist, original))


def generate_clip(model, data, name, ready):
    spec = PHASES[name]
    length = spec['length']
    # 200Hz authoring samples bound fast interpolated IK gaps; runtime progress
    # and all gameplay durations remain unchanged. Include source phase corners.
    times = sorted({round(i/200, 6) for i in range(round(length*200)+1)} |
                   {t for t, _ in spec['phaseSeconds']} | {t for t, _ in spec['blendSeconds']})
    corrections = []
    neutral = h15.zero() if name == START else ready

    def evaluate(t):
        seconds = curve(spec['phaseSeconds'], t)
        p, item = pose_from_source(model, data, spec['tag'], seconds, spec['neutralFrame'], ready)
        weight = curve(spec['blendSeconds'], t)
        endpoint = neutral if t <= spec['blendSeconds'][1][0] else ready
        p = blend_pose(endpoint, p, weight)
        item = slerp(rotation(h19.fk(model, endpoint)['pri_right_item']), item, weight)
        if t == 0 or t == length:
            p = copy.deepcopy(neutral if t == 0 else ready)
        else:
            # Deploy's first 25ms is the declared hidden-item neutral transition.
            # Begin enforcing two-hand attachment once staff first appears.
            if name == ATTACK or t >= .025:
                corrections.append(attach_staff(model, p, item))
            else:
                h20.aim_right(model, p, item)
        return p

    frames = [(t, evaluate(t)) for t in times]
    scales = [(0, .001), (.025, .001), (.05, .35), (.1, 1), (.5, 1)] if name == START else None
    # Rz Ry Rx has two equivalent Euler families. Per-axis +/-360 unwrap alone
    # cannot cross its +/-90 Y boundary: it creates a false 180-degree elbow /
    # item excursion between otherwise adjacent rigid matrices.
    for _ in range(9):
        previous = None
        for _, p in frames:
            if previous is not None:
                for bone in p:
                    x, y, z = p[bone]
                    candidates = []
                    for v in ([x, y, z], [x+180, 180-y, z+180]):
                        candidates.append([a+360*round((b-a)/360) for a, b in zip(v, previous[bone])])
                    p[bone] = min(candidates, key=lambda v: sum((a-b)**2 for a, b in zip(v, previous[bone])))
            previous = copy.deepcopy(p)
        insertions = []
        for (ta, a), (tb, b) in zip(frames, frames[1:]):
            t = round((ta+tb)/2, 9)
            mid = h20.mix(a, b, .5)
            matrices = h19.fk(model, mid)
            gap = h19.norm(h19.sub(h19.point(matrices['pri_right_item'], [0, 6, 0]),
                                    h19.point(matrices['pli_left_item'], [0, 0, 0])))
            floor_error = abs((h15.floor_y(model, a)+h15.floor_y(model, b))/2-h15.floor_y(model, mid))
            if ((name == ATTACK or t >= .025) and gap > .035) or floor_error > .035:
                insertions.append((t, evaluate(t)))
        if not insertions:
            break
        frames = sorted(frames+insertions, key=lambda v: v[0])
        assert len(frames) <= 256, 'Contact adaptation exceeded bounded key budget'
    else:
        raise AssertionError('Contact interpolation failed to converge')
    clip = h20.new_clip(model, name, frames, scales=scales)
    clip['snapping'] = 200
    return clip, max(corrections, default=0)


def compose(source, data):
    validate_data(data)
    model = copy.deepcopy(source)
    model['name'] = model['model_identifier'] = MODEL
    ready, _ = h19.sample(next(c for c in model['animations'] if c['name'] == 'h15_super_arc'), 0)
    replacements, metrics = {}, {}
    for name in PHASES:
        replacements[name], metrics[name] = generate_clip(model, data, name, ready)
    model['animations'] = [replacements.get(c['name'], c) for c in model['animations']]
    return model, metrics


def export(model):
    return {'model': MODEL, 'animations': [c for c in model['animations'] if c['name'].startswith('h15_')]}


def validate(model, source):
    assert model['name'] == model['model_identifier'] == MODEL
    assert len(model['groups']) == 18 and len(model['elements']) <= 1000
    for key in source:
        if key not in ('name', 'model_identifier', 'animations'):
            assert source[key] == model[key], 'Geometry/rig/UV changed: '+key
    before = {c['name']: c for c in source['animations']}
    after = {c['name']: c for c in model['animations']}
    assert set(before) == set(after) and len(export(model)['animations']) == 20
    assert sum(before[n] == after[n] for n in before if n.startswith('h15_')) == 18
    for name in before:
        if name not in PHASES:
            assert before[name] == after[name], name
    ready, root = h19.sample(after['h15_super_arc'], 0)
    for name, spec in PHASES.items():
        clip = after[name]
        assert clip['length'] == spec['length'] and clip['loop'] == 'once'
        end, end_y = h19.sample(clip, clip['length'])
        for bone in ready:
            a, b = h15.rot(end[bone]), h15.rot(ready[bone])
            assert max(abs(a[i][j]-b[i][j]) for i in range(3) for j in range(3)) < 1e-5
        assert abs(end_y-root) < 1e-5
        for animator in clip['animators'].values():
            for channel in {k['channel'] for k in animator['keyframes']}:
                keys = [k for k in animator['keyframes'] if k['channel'] == channel]
                times = [k['time'] for k in keys]
                assert len(times) == len(set(times)) <= 256
                assert min(times) == 0 and max(times) == clip['length']
                assert all(k['interpolation'] == 'linear' for k in keys)
                for k in keys:
                    assert all(math.isfinite(v) for v in k['data_points'][0].values())
                    if animator['name'] == 'player_root' and channel == 'position':
                        assert k['data_points'][0]['x'] == k['data_points'][0]['z'] == 0
    assert .1 in [k['time'] for a in after[ATTACK]['animators'].values() for k in a['keyframes']]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', type=Path)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.extract and args.verify:
        parser.error('--extract and --verify are mutually exclusive')
    if args.extract:
        extract(args.extract)
    data = json.loads(DATA.read_text())
    source = json.loads(SOURCE.read_text())
    model, metrics = compose(source, data)
    validate(model, source)
    for path, obj in ((ART, model), (PACK, export(model))):
        encoded = (json.dumps(obj, indent=2, allow_nan=False)+'\n').encode()
        if args.verify:
            assert path.read_bytes() == encoded, 'Reproduction differs: '+str(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(encoded)
    print('PASS W197 Hunter: 20 h15 clips, 18 preserved; rig/skin unchanged; .50/.35/.10 seconds')
    print('Max source-driven wrist reach adaptation (model units):', metrics)


if __name__ == '__main__':
    main()
