#!/usr/bin/env python3
"""W160 candidate-only regressions; no build or native invocation."""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fix_ammit_pose_w160 as w


def rotate(v, axis, a):
    x, y, z = v
    c, s = math.cos(a), math.sin(a)
    if axis == 'x':
        return [x, c*y-s*z, s*y+c*z]
    return [c*x+s*z, y, -s*x+c*z]


def held(v, transform, crouch=True, left=False, point=False):
    """Independent vector/point evaluation in humanoid units (+Y down)."""
    sign = -1 if left else 1
    if point:
        v = [scale*(x-8) for x, scale in zip(v, transform['scale'])]
    rx, ry, rz = map(math.radians, transform['rotation'])
    assert rz == 0
    v = rotate(rotate(v, 'y', sign*ry), 'x', rx)
    if point:
        tx, ty, tz = transform['translation']
        v = [v[0]+sign*tx+sign, v[1]+ty+2, v[2]+tz-10]
    for axis, angle in [('y', math.pi), ('x', -math.pi/2),
                        ('x', -math.pi/2+.1+(.4 if crouch else 0)), ('y', -.3*sign)]:
        v = rotate(v, axis, angle)
    return v


def select(node, context, pose, two=True, progress=1, crouch=False):
    """Evaluate the actual item's relevant vanilla model selectors."""
    kind = node['type'].removeprefix('minecraft:')
    if kind == 'model':
        return node['model']
    if kind == 'select':
        value = context if node['property'] == 'minecraft:display_context' else pose
        for case in node['cases']:
            when = case['when'] if isinstance(case['when'], list) else [case['when']]
            if value in when:
                return select(case['model'], context, pose, two, progress, crouch)
        return select(node['fallback'], context, pose, two, progress, crouch)
    if kind == 'condition':
        # W161: flag1 is actual crouch, not another copy of the grip selector.
        assert node['property'] == 'minecraft:custom_model_data' and node['index'] in (0, 1)
        value = two if node['index'] == 0 else crouch
        return select(node['on_true' if value else 'on_false'], context, pose, two, progress, crouch)
    if kind == 'range_dispatch':
        eligible = [e for e in node['entries'] if e['threshold'] <= progress]
        return select(eligible[-1]['model'] if eligible else node['fallback'], context, pose, two, progress, crouch)
    raise AssertionError(kind)


class AmmitCandidateTest(unittest.TestCase):
    def assertVector(self, actual, expected, places=6):
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b, places=places)

    def test_candidate_cancels_observed_crouch_bore_drop_and_yaw(self):
        for left in (False, True):
            with self.subTest(left=left):
                before = held([0, 0, -1], w.OLD, left=left)
                self.assertGreater(before[1], .35)  # Downward in humanoid coordinates.
                self.assertGreater(abs(before[0]), .02)  # Crouch/yaw coupling.
                self.assertVector(held([0, 0, -1], w.candidate(), left=left), [0, 0, -1])
                self.assertVector(held([0, 1, 0], w.candidate(), left=left), [0, -1, 0])

    def test_candidate_retains_grip_and_moves_stock_rearward_in_both_hands(self):
        for left in (False, True):
            old_grip = held(w.GRIP, w.OLD, left=left, point=True)
            grip = held(w.GRIP, w.candidate(), left=left, point=True)
            self.assertVector(grip, old_grip)
            old_stock = held(w.STOCK, w.OLD, left=left, point=True)
            stock = held(w.STOCK, w.candidate(), left=left, point=True)
            muzzle = held(w.MUZZLE, w.candidate(), left=left, point=True)
            self.assertGreater(stock[2], old_stock[2])  # Toward shoulder plane z=0.
            self.assertGreater(stock[2], grip[2])
            self.assertLess(muzzle[2], grip[2])
            self.assertLess(muzzle[1], grip[1])
        self.assertEqual(w.candidate()['rotation'], [28.64789, -17.188734, 0])
        self.assertEqual(w.candidate()['translation'], [0.0, -1.837142, 1.792719])

    def test_standing_release_is_a_real_reason_not_to_activate_static_candidate(self):
        self.assertVector(held([0, 0, -1], w.OLD, crouch=False), [0, 0, -1])
        candidate = held([0, 0, -1], w.candidate(), crouch=False)
        self.assertLess(candidate[1], -.35)  # Unwanted elevation after crouch ends.
        manifest = w.generate()
        self.assertEqual(manifest['activeResourceChanges'], [])
        self.assertFalse(manifest['nativePixelAcceptance'])
        self.assertTrue(any('sample15' in x for x in manifest['whyInactive']))

    def test_actual_sight_route_reaches_canonical_ads_only_in_third_person(self):
        path = w.ROOT/'src/main/resources/assets/destiny/items/weapon_sight_w151/ammit_ar2.json'
        graph = json.loads(path.read_bytes())['model']
        for context in w.CONTEXTS:
            self.assertEqual(select(graph, context, 'ads'), 'destiny:weapon/auto_rifle/ammit_ar2_ads_twohand')
            self.assertEqual(select(graph, context, 'hip'), 'destiny:weapon/auto_rifle/ammit_ar2_twohand')
            self.assertEqual(select(graph, context, 'ads', False), 'destiny:weapon/auto_rifle/ammit_ar2_ads')
            self.assertEqual(select(graph, context, 'ads', crouch=True), 'destiny:weapon_pose_w161/ammit_ar2_ads')
            self.assertEqual(select(graph, context, 'ads', False, crouch=True), 'destiny:weapon/auto_rifle/ammit_ar2_ads')
        for context in ('firstperson_righthand', 'firstperson_lefthand'):
            for frame in (0, .5, 1):
                self.assertTrue(select(graph, context, 'ads', progress=frame).startswith('destiny:weapon_sight_w151/'))

    def test_active_model_bytes_fp_geometry_and_all_contexts_remain_seeded(self):
        raw = (w.ROOT/w.MODEL).read_bytes()
        self.assertEqual(w.sha(raw), w.BEFORE_SHA256)
        model = json.loads(raw)
        for context in w.CONTEXTS:
            self.assertEqual(model['display'][context], w.OLD)
        before = copy.deepcopy(model)
        w.generate()
        self.assertEqual(raw, (w.ROOT/w.MODEL).read_bytes())
        self.assertEqual(before, json.loads(raw))

    def test_manifest_is_deterministic_explicitly_inactive_and_source_guarded(self):
        expected = w.encode(w.generate())
        self.assertEqual(expected, w.encode(w.generate()))
        self.assertEqual(expected, (w.ROOT/w.MANIFEST).read_bytes())
        manifest = json.loads(expected)
        self.assertEqual(manifest['activeSource']['beforeSha256'], manifest['activeSource']['afterSha256'])
        self.assertEqual(manifest['nativeOperations'], 0)
        self.assertEqual(manifest['effectiveScope']['derivedChangesNecessary'], [])
        self.assertEqual(len(manifest['historicalPixels']), 4)
        # Emission entry point has only one writable destination: its owned sidecar.
        self.assertIn('inactive-candidate', manifest['status'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
