#!/usr/bin/env python3
"""Scoped real-source Hunter retarget regression. No runtime/GUI/subprocess use.

rtk proxy python3 -B scripts/qa/test_hunter_source_w197.py
"""
import copy
import gzip
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_hunter_source_w197 as w


def difference(a, b):
    return max(abs(a[i][j]-b[i][j]) for i in range(3) for j in range(3))


def angle(a, b):
    delta = w.h15.mm(w.h19.inverse_rotation(w.rotation(a)), w.rotation(b))
    return math.degrees(math.acos(max(-1, min(1, (sum(delta[i][i] for i in range(3))-1)/2))))


class HunterSourceW197(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(w.SOURCE.read_text())
        cls.data = json.loads(w.DATA.read_text())
        cls.model = json.loads(w.ART.read_text())
        cls.pack = json.loads(w.PACK.read_text())
        cls.clips = {c['name']: c for c in cls.model['animations']}
        cls.ready, cls.ready_y = w.h19.sample(cls.clips['h15_super_arc'], 0)

    def test_product_scope_and_reproduction(self):
        w.validate(self.model, self.source)
        regenerated, metrics = w.compose(self.source, self.data)
        self.assertEqual(regenerated, self.model)
        self.assertEqual(w.export(self.model), self.pack)
        self.assertLess(max(metrics.values()), 8.1)
        self.assertEqual(len(self.model['elements']), 26)
        self.assertEqual(len(self.model['groups']), 18)
        self.assertEqual(len(self.pack['animations']), 20)
        self.assertEqual(next(c for c in self.source['animations'] if c['name'] == 'h15_super_void_attack'),
                         self.clips['h15_super_void_attack'])

    def test_dataset_matches_w196_evaluated_matrices(self):
        # Optional original-source audit. Normal reproduction requires only the
        # checked-in compact dataset, never the SSD or Blender.
        sample = Path('/Users/qf/IdeaProjects/DestinyGuardians') / self.data['samplePath']
        if not sample.exists():
            self.skipTest('W196 read-only original not present; compact dataset remains sufficient')
        compressed = sample.read_bytes()
        raw = gzip.decompress(compressed)
        self.assertEqual(w.sha(raw), self.data['sampleSHA256'])
        self.assertEqual(w.sha(compressed), self.data['sampleGzipSHA256'])
        evaluated = json.loads(raw)
        by_hash = {bone['name']: i for i, bone in enumerate(evaluated['bones'])}
        for clip in evaluated['clips']:
            if clip['tag'] not in self.data['clips']:
                continue
            for actual, saved in zip(clip['frames'], self.data['clips'][clip['tag']]['frames']):
                self.assertEqual(actual['frame'], saved['frame'])
                self.assertEqual(actual['seconds'], saved['seconds'])
                for bone in self.data['sampledBoneIds']:
                    original = actual['matrices'][by_hash[bone]]
                    observed = saved['matrices'][bone]
                    self.assertLessEqual(max(abs(original[i][j]-observed[i][j])
                                             for i in range(4) for j in range(4)), 5.01e-10)

    def test_hash_hierarchy_mapping_and_order_independence(self):
        w.validate_data(self.data)
        self.assertEqual(self.data['targetMap']['prfa_right_forearm'], 'A3781DCD')
        self.assertEqual(self.data['targetMap']['pla_left_arm'], 'D1232BA2')
        reordered = copy.deepcopy(self.data)
        reordered['bones'] = dict(reversed(list(reordered['bones'].items())))
        reordered['sampledBoneIds'].reverse()
        a, ai = w.pose_from_source(self.model, self.data, '80A8A937', .3, 40, self.ready)
        b, bi = w.pose_from_source(self.model, reordered, '80A8A937', .3, 40, self.ready)
        self.assertEqual(a, b)
        self.assertEqual(ai, bi)

    def test_neutral_calibration_and_endpoints(self):
        for tag, frame in [('80A8A922', 44), ('80A8A937', 40)]:
            p, item = w.pose_from_source(self.model, self.data, tag, (frame-1)/30, frame, self.ready)
            for bone in self.ready:
                self.assertLess(difference(w.h15.rot(p[bone]), w.h15.rot(self.ready[bone])), 1e-6, bone)
            self.assertLess(difference(item, w.rotation(w.h19.fk(self.model, self.ready)['pri_right_item'])), 1e-6)
        for name in w.PHASES:
            clip = self.clips[name]
            for time, expected in [(0, w.h15.zero() if name == w.START else self.ready),
                                   (clip['length'], self.ready)]:
                p, y = w.h19.sample(clip, time)
                for bone in expected:
                    self.assertLess(difference(w.h15.rot(p[bone]), w.h15.rot(expected[bone])), 1e-6)
                self.assertAlmostEqual(y, w.h15.floor_y(self.model, expected), places=4)

    def test_source_materially_drives_torso_limbs_and_staff(self):
        accepted = w.h19.fk(self.model, self.ready)
        for name, spec in w.PHASES.items():
            clip = self.clips[name]
            matrices = []
            hips, tips = [], []
            for i in range(21):
                p, y = w.h19.sample(clip, clip['length']*i/20)
                fk = w.h19.fk(self.model, p, y)
                matrices.append(fk)
                hips.append(fk['phip_hip'][1][3])
                tips.append(w.h19.point(fk['pri_right_item'], [0, 14, 0]))
            self.assertGreater(max(angle(accepted['pc_chest'], f['pc_chest']) for f in matrices), 60)
            self.assertGreater(max(angle(accepted['prl_right_leg'], f['prl_right_leg']) for f in matrices), 30)
            self.assertLess(min(hips), 11.25+self.ready_y-2)
            self.assertGreater(max(w.h19.norm(w.h19.sub(a, b)) for a in tips for b in tips), 25)
            # Ablate sampled rotations at an interior source time: target torso
            # must change substantially, rather than merely carry source tags.
            changed = copy.deepcopy(self.data)
            frames = changed['clips'][spec['tag']]['frames']
            ref = frames[spec['neutralFrame']-1]['matrices']
            for frame in frames:
                for bone in frame['matrices']:
                    for i in range(3):
                        frame['matrices'][bone][i][:3] = ref[bone][i][:3]
            t = .3
            p, _ = w.pose_from_source(self.model, self.data, spec['tag'], t, spec['neutralFrame'], self.ready)
            ablated, _ = w.pose_from_source(self.model, changed, spec['tag'], t, spec['neutralFrame'], self.ready)
            self.assertGreater(angle(w.h19.fk(self.model, p)['pc_chest'],
                                     w.h19.fk(self.model, ablated)['pc_chest']), 30)

    def test_interpolated_support_ground_and_knee_guards(self):
        for name in w.PHASES:
            clip = self.clips[name]
            worst_gap, worst_floor = 0, 0
            for i in range(round(clip['length']*1000)+1):
                t = i/1000
                p, root_y = w.h19.sample(clip, t)
                matrices = w.h19.fk(self.model, p, root_y)
                support = w.h19.point(matrices['pri_right_item'], [0, 6, 0])
                hand = w.h19.point(matrices['pli_left_item'], [0, 0, 0])
                if name == w.ATTACK or t >= .025:
                    worst_gap = max(worst_gap, w.h19.norm(w.h19.sub(support, hand)))
                worst_floor = max(worst_floor, abs(root_y-w.h15.floor_y(self.model, p)))
                for bone in ('prfl_right_foreleg', 'plfl_left_foreleg'):
                    # Geometric knee flex is positive; tiny roundoff allowed.
                    self.assertTrue(-1e-5 <= p[bone][0] <= 155.00001)
                    self.assertLess(abs(p[bone][1])+abs(p[bone][2]), 1e-5)
            self.assertLess(worst_gap, .05, (name, worst_gap))
            self.assertLess(worst_floor, .1, (name, worst_floor))
            print(f'{name}: 1ms linear FK support gap={worst_gap:.6f}u; skin-floor error={worst_floor:.6f}u')

    def test_part_separation_and_fixed_gameplay_timing(self):
        for name, length in [(w.START, .5), (w.ATTACK, .35)]:
            clip = self.clips[name]
            self.assertEqual(clip['length'], length)
            self.assertEqual(clip['loop'], 'once')
            ids = {g['name']: g['uuid'] for g in self.model['groups']}
            for bone in ('pri_right_item', 'pli_left_item', 'pra_right_arm', 'pla_left_arm'):
                self.assertEqual(clip['animators'][ids[bone]]['name'], bone)
            a, _ = w.h19.sample(clip, .1)
            b, _ = w.h19.sample(clip, .15)
            af, bf = w.h19.fk(self.model, a), w.h19.fk(self.model, b)
            # Staff attitude relative to the torso changes: not one rigid whole-
            # player wiggle carrying a fixed staff/arm group.
            ar = w.h15.mm(w.h19.inverse_rotation(af['pc_chest']), w.rotation(af['pri_right_item']))
            br = w.h15.mm(w.h19.inverse_rotation(bf['pc_chest']), w.rotation(bf['pri_right_item']))
            self.assertGreater(angle(ar, br), 10)
        self.assertEqual(w.curve(w.PHASES[w.ATTACK]['phaseSeconds'], .1), .3)
        self.assertEqual(w.PHASES[w.ATTACK]['contact']['sourceFrame'], 10)
        root = next(a for a in self.clips[w.ATTACK]['animators'].values() if a['name'] == 'player_root')
        self.assertIn(.1, [k['time'] for k in root['keyframes']])
        for name in w.PHASES:
            root = next(a for a in self.clips[name]['animators'].values() if a['name'] == 'player_root')
            for key in root['keyframes']:
                values = key['data_points'][0]
                if key['channel'] == 'position':
                    self.assertEqual(values['x'], 0)
                    self.assertEqual(values['z'], 0)
                if key['channel'] == 'rotation':
                    self.assertEqual(values, dict.fromkeys('xyz', 0))

    def test_translation_outer_axis_scale_not_baked(self):
        shifted = copy.deepcopy(self.data)
        for clip in shifted['clips'].values():
            for frame in clip['frames']:
                for matrix in frame['matrices'].values():
                    for i in range(3):
                        matrix[i][3] += [123, -456, 789][i]
        shifted['provenance']['importObjectMatrix'] = w.h15.tr([100, 100, 100])
        a, ai = w.pose_from_source(self.model, self.data, '80A8A937', .3, 40, self.ready)
        b, bi = w.pose_from_source(self.model, shifted, '80A8A937', .3, 40, self.ready)
        for bone in a:
            self.assertLess(difference(w.h15.rot(a[bone]), w.h15.rot(b[bone])), 1e-8)
        self.assertLess(difference(ai, bi), 1e-8)

    def test_guards_reject_invalid_source(self):
        broken = copy.deepcopy(self.data)
        broken['targetMap']['pla_left_arm'] = '17025F50'
        with self.assertRaises(AssertionError):
            w.validate_data(broken)
        broken = copy.deepcopy(self.data)
        broken['clips']['80A8A922']['frames'][0]['matrices']['C7C0BA6E'][0][0] = math.nan
        with self.assertRaises(AssertionError):
            w.validate_data(broken)
        broken = copy.deepcopy(self.data)
        broken['bones']['A3781DCD']['parent'] = 'C7C0BA6E'
        with self.assertRaises(AssertionError):
            w.validate_data(broken)
        broken = copy.deepcopy(self.data)
        broken['retarget']['basis'][0][1] = 1
        with self.assertRaises(AssertionError):
            w.validate_data(broken)


if __name__ == '__main__':
    unittest.main(verbosity=2)
