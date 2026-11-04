#!/usr/bin/env python3
"""Targeted sword pose regressions; static FK is not native pixel acceptance."""
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_sword_pose_w146 as w


class SwordPoseW146Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = json.loads((w.ROOT / w.ART).read_text())
        cls.clips = {a['name']: a for a in json.loads((w.ROOT / w.PACK).read_text())['animations']}

    def test_high_close_hilt_and_dropped_elbows(self):
        for kind in ('idle', 'move', 'air', 'guard'):
            for phase in (0, .25, .5, .75, 1):
                matrices = w.fk.fk(self.model, w.raised(self.model, kind, phase))
                right = w.fk.point(matrices['pri_right_item'], [0, 0, 0])
                left = w.fk.point(matrices['pli_left_item'], [0, 0, 0])
                support = w.fk.point(matrices['pri_right_item'], w.SUPPORT_LOCAL)
                self.assertGreater(right[1], 24.9)
                self.assertGreater(left[1], 22.5)
                self.assertLess(right[2], -5)
                self.assertLess(w.fk.norm(w.fk.sub(left, support)), 1e-5)
                for side, wrist in (('right', right), ('left', left)):
                    elbow = w.fk.point(matrices['prfa_right_forearm' if side == 'right' else 'plfa_left_forearm'], [0, 0, 0])
                    self.assertLess(elbow[1], wrist[1] - 2)
                self.assertGreater(w.fk.vector(matrices['pri_right_item'], [0, 0, 1])[1], .9)

    def test_left_releases_before_windup_and_stays_clear_through_contact(self):
        for suffix, _, cue, _, _ in w.old.CUES[:3]:
            clip = self.clips['h15_sword_' + suffix]
            for t in (.05, .10, cue, cue + .05):
                p, y = w.fk.sample(clip, t)
                matrices = w.fk.fk(self.model, p, y)
                left = w.fk.point(matrices['pli_left_item'], [0, 0, 0])
                support = w.fk.point(matrices['pri_right_item'], w.SUPPORT_LOCAL)
                self.assertLess(left[0], -5.8)
                self.assertLess(left[1] - y, 18)
                # Four model units clear even when the follow-through passes left.
                self.assertGreater(w.fk.norm(w.fk.sub(left, support)), 5 if t <= cue else 4)

    def test_lights_recover_to_new_high_ready_not_old_low_mix(self):
        ready = w.raised(self.model)
        for suffix, length, _, _, _ in w.old.CUES[:3]:
            clip = self.clips['h15_sword_' + suffix]
            p, y = w.fk.sample(clip, length)
            for bone in w.h15.BONES:
                for axis in range(3):
                    self.assertAlmostEqual(0, (p[bone][axis] - ready[bone][axis] + 180) % 360 - 180, places=5)
            p, _ = w.fk.sample(clip, length - .05)
            wrist = w.fk.point(w.fk.fk(self.model, p)['pri_right_item'], [0, 0, 0])
            self.assertGreater(wrist[1], 23.5)

    def test_preserves_all_durations_and_no_horizontal_root_motion(self):
        self.assertEqual(12, len(self.clips))
        for suffix, length, _, _, _ in w.old.CUES:
            self.assertEqual(length, self.clips['h15_sword_' + suffix]['length'])
        for clip in self.clips.values():
            for animator in clip['animators'].values():
                for key in animator['keyframes']:
                    point = key['data_points'][0]
                    self.assertTrue(all(math.isfinite(point[k]) for k in 'xyz'))
                    if key['channel'] == 'position':
                        self.assertEqual('player_root', animator['name'])
                        self.assertEqual((0, 0), (point['x'], point['z']))
        clip = self.clips['h15_sword_vortex']
        ys = [w.fk.sample(clip, i / 100)[0]['player_root'][1] for i in range(106)]
        self.assertTrue(all(a <= b for a, b in zip(ys, ys[1:])))
        self.assertEqual(360, ys[-1])

    def test_rig_and_historical_assets_untouched(self):
        source = json.loads((w.ROOT / w.SOURCE).read_text())
        for key in source:
            if key not in ('name', 'model_identifier', 'animations'):
                self.assertEqual(source[key], self.model[key])
        for path, digest in w.old.PINS.items():
            self.assertEqual(digest, hashlib.sha256((w.ROOT / path).read_bytes()).hexdigest())
        historical = w.prior.generate()
        for path, data in historical.items():
            self.assertEqual(data, (w.ROOT / path).read_bytes())


if __name__ == '__main__':
    unittest.main(verbosity=2)
