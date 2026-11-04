"""Targeted ADS framing regression; original Ace art remains unchanged."""
import json
import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
G = runpy.run_path(str(ROOT / 'scripts/art/build_ace_w83.py'))
A = ROOT / G['ASSETS']


class AceCloserSight(unittest.TestCase):
    def test_rear_sight_is_readable_and_both_anchors_remain_centered(self):
        checks = json.loads((ROOT / 'art/weapons/w83/model/pose-checks.json').read_bytes())
        for anchor in checks['adsIdleSightAlignment']:
            x, y, z = anchor['cameraPointBlocks']
            self.assertAlmostEqual(x, 0, places=7)
            self.assertAlmostEqual(y, 0, places=7)
            if anchor['anchor'] == 'rear':
                self.assertAlmostEqual(z, -.42, places=7)
            else:
                self.assertLess(z, -.42)

    def test_source_geometry_uv_and_non_ads_poses_are_preserved(self):
        model = json.loads((A / 'models/item/weapon/ace_of_spades.json').read_bytes())
        self.assertEqual(len(model['elements']), 87)
        endpoint = json.loads((A / 'models/item/weapon_aim_w70/ace_of_spades_20_native.json').read_bytes())
        frame0 = json.loads((A / 'models/item/weapon_aim_w70/ace_of_spades_00_native.json').read_bytes())
        self.assertEqual(frame0['display'], model['display'])
        for key, value in model['display'].items():
            if key not in G['FP']:
                self.assertEqual(endpoint['display'][key], value)
        # Keep the complete assembly beyond a practical preview near plane.
        pose = endpoint['display']['firstperson_righthand']
        closest = max(G['item_point'](p, pose)[2] / 16 - .72
                      for e in model['elements'] for p in G['corners'](e))
        self.assertLess(closest, -.05)


if __name__ == '__main__':
    unittest.main(verbosity=2)
