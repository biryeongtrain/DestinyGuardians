#!/usr/bin/env python3
"""Small authoring regression; native pixels, damage and sound are separate."""
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_sword_pose_w140 as w
import build_hunter_animation_h19 as fk


class SwordPoseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = json.loads((w.ROOT/w.ART).read_text())
        cls.pack = json.loads((w.ROOT/w.PACK).read_text())
        cls.clips = {c['name']: c for c in cls.pack['animations']}

    def test_support_hand_meets_same_handle_not_an_independent_free_hand(self):
        for kind in ('idle', 'move', 'air', 'guard'):
            for phase in (0, .25, .5, .75, 1):
                p = w.raised(self.model, kind, phase)
                bones = fk.fk(self.model, p)
                support = fk.point(bones['pri_right_item'], w.SUPPORT_LOCAL)
                left = fk.point(bones['pli_left_item'], [0, 0, 0])
                self.assertLess(fk.norm(fk.sub(support, left)), 1e-5)
                self.assertGreater(fk.point(bones['pri_right_item'], [0, 0, 0])[1], 23)
                # Native model +Y becomes +Z in pinned display Rx(+90).
                self.assertGreater(fk.vector(bones['pri_right_item'], [0, 0, 1])[1], .85)

    def test_lights_release_support_hand_at_unchanged_contact_cue(self):
        for suffix, _, cue, _, _ in w.old.CUES[:3]:
            p, y = fk.sample(self.clips['h15_sword_'+suffix], cue)
            bones = fk.fk(self.model, p, y)
            support = fk.point(bones['pri_right_item'], w.SUPPORT_LOCAL)
            free = fk.point(bones['pli_left_item'], [0, 0, 0])
            self.assertGreater(fk.norm(fk.sub(support, free)), 5)

    def test_attack_lengths_and_contact_timing_unchanged(self):
        self.assertEqual(12, len(self.clips))
        for suffix, length, _, _, _ in w.old.CUES:
            self.assertEqual(length, self.clips['h15_sword_'+suffix]['length'])
        manifest = json.loads((w.ROOT/'art/weapons/w140/manifest.json').read_text())
        self.assertEqual([r[2] for r in w.old.CUES], [r['contact'] for r in manifest['timing']])

    def test_new_ready_recovery_matches_modulo_full_spin(self):
        expected = w.raised(self.model)
        for suffix, length, _, _, _ in w.old.CUES:
            for t in (0, length):
                p, _ = fk.sample(self.clips['h15_sword_'+suffix], t)
                for b in w.h15.BONES:
                    for a in range(3):
                        self.assertAlmostEqual(0, (p[b][a]-expected[b][a]+180)%360-180, places=6)

    def test_preserves_historical_rig_and_non_sword_clips(self):
        source = json.loads((w.ROOT/w.SOURCE).read_text())
        for key in source:
            if key not in ('name', 'model_identifier', 'animations'):
                self.assertEqual(source[key], self.model[key], key)
        inherited = [a for a in source['animations'] if not a['name'].startswith('h15_sword_')]
        self.assertEqual(inherited, self.model['animations'][:len(inherited)])
        for path, expected in w.old.PINS.items():
            self.assertEqual(expected, hashlib.sha256((w.ROOT/path).read_bytes()).hexdigest(), path)

    def test_finite_channels_and_no_horizontal_root_motion(self):
        for clip in self.clips.values():
            self.assertEqual(16, len(clip['animators']))
            for a in clip['animators'].values():
                for key in a['keyframes']:
                    point = key['data_points'][0]
                    self.assertTrue(all(math.isfinite(point[k]) for k in 'xyz'))
                    if key['channel'] == 'position':
                        self.assertEqual('player_root', a['name'])
                        self.assertEqual(0, point['x']); self.assertEqual(0, point['z'])
                    if key['channel'] == 'scale':
                        self.assertEqual({1}, set(point.values()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
