#!/usr/bin/env python3
"""W156 narrow stationary pose + preservation checks; no native/client/build claim."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fix_ammit_pose_w156 as w


def rotate(v, axis, angle):
    x, y, z = v
    c, s = math.cos(angle), math.sin(angle)
    if axis == 'x':
        return [x, c*y-s*z, s*y+c*z]
    if axis == 'y':
        return [c*x+s*z, y, -s*x+c*z]
    return [c*x-s*y, s*x+c*y, z]


def held(v, display_rotation, twohand, left=False):
    """Independent vector evaluation, in humanoid coordinates (+Y down)."""
    x, y, z = map(math.radians, display_rotation)
    sign = -1 if left else 1
    # ItemTransform.rotationXYZ, then layer, then ModelPart.rotationZYX.
    for axis, angle in [('z', sign*z), ('y', sign*y), ('x', x),
                        ('y', math.pi), ('x', -math.pi/2),
                        ('x', -math.pi/2+.1 if twohand else -math.pi/10),
                        ('y', -.3*sign if twohand else 0)]:
        v = rotate(v, axis, angle)
    return v


class AmmitPoseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = w.generate()

    def assertVector(self, actual, expected):
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b, places=7)

    def test_actual_vanilla_chain_levels_both_hands_in_each_state(self):
        for rel in w.MODELS:
            model = json.loads(self.outputs[rel])
            for hand in w.CONTEXTS:
                with self.subTest(model=rel, hand=hand):
                    rotation = model['display'][hand]['rotation']
                    two = '_twohand.json' in rel
                    self.assertVector(held([0, 0, -1], rotation, two, hand.endswith('lefthand')), [0, 0, -1])
                    self.assertVector(held([0, 1, 0], rotation, two, hand.endswith('lefthand')), [0, -1, 0])

    def test_regression_generic_native_ninety_has_eighteen_degree_tilt(self):
        old = held([0, 0, -1], [90, 0, 0], False)
        self.assertAlmostEqual(math.degrees(math.acos(-old[2])), 18)
        self.assertGreater(abs(old[1]), .3)
        self.assertVector(held([0, 0, -1], [72, 0, 0], False), [0, 0, -1])
        # The preexisting two-hand rotation already cancels crossbow aim.
        self.assertVector(held([0, 0, -1], [5.729578, -17.188734, 0], True), [0, 0, -1])

    def test_grip_translation_scale_fp_geometry_uv_and_parents_preserved(self):
        for rel in w.MODELS:
            self.assertEqual(w.PRESERVED[rel], w.preserved_hash(json.loads(self.outputs[rel])), rel)
        # Every byte in all three two-hand parents remains exactly as seeded.
        for rel in w.MODELS:
            if '_twohand.json' in rel:
                self.assertEqual(w.BASELINE[rel], w.sha(self.outputs[rel]), rel)
        full = json.loads(self.outputs[w.MODELS[-1]])
        asset = w.ROOT/'src/main/resources/assets/destiny/models/weapon_surface_w123'
        body = json.loads((asset/'ammit_ar2_body.json').read_bytes())
        magazine = json.loads((asset/'ammit_ar2_magazine.json').read_bytes())
        self.assertEqual(full['elements'], body['elements']+magazine['elements'])
        self.assertEqual(len(full['elements']), 126)
        self.assertNotIn('display', body)
        self.assertNotIn('display', magazine)

    def test_original_grip_stock_and_bore_direction_stays_upright(self):
        model = json.loads(self.outputs[w.MODELS[-1]])
        geometry = {e['name']: e for e in model['elements']}
        grip = geometry['Grip_backstrap']['rotation']['origin']
        stock = geometry['Stock_rubber_pad']['rotation']['origin']
        bore = geometry['Muzzle_dark_recess']['rotation']['origin']
        self.assertGreater(stock[2], grip[2])
        self.assertLess(bore[2], grip[2])
        self.assertGreater(bore[1], grip[1])
        for two in (False, True):
            r = w.rotation(two)
            to_bore = held([b-a for a, b in zip(grip, bore)], r, two)
            to_stock = held([b-a for a, b in zip(grip, stock)], r, two)
            self.assertLess(to_bore[2], 0)
            self.assertLess(to_bore[1], 0)  # above grip in humanoid coordinates
            self.assertGreater(to_stock[2], 0)

    def test_exact_output_scope_idempotency_and_read_only_verify_inputs(self):
        self.assertEqual(set(self.outputs), set(w.MODELS)|{w.MANIFEST})
        for rel in w.MODELS:
            output = self.outputs[rel]
            self.assertEqual(output, w.patch(output, '_twohand.json' in rel))
        before = {p: (w.ROOT/p).read_bytes() for p in self.outputs}
        self.assertEqual(self.outputs, w.generate())
        self.assertEqual(before, {p: (w.ROOT/p).read_bytes() for p in self.outputs})
        manifest = json.loads(self.outputs[w.MANIFEST])
        self.assertFalse(manifest['integration']['nativeProof'])
        self.assertEqual(w.BASELINE, manifest['beforeSha256'])
        for p, digest in manifest['outputSha256'].items():
            self.assertEqual(digest, w.sha(self.outputs[p]))
        self.assertEqual(self.outputs, before)

    def test_source_dependency_and_shared_weapon_files_preserved(self):
        pins = {
            'scripts/build_weapons_w30.py': 'e087fca588231486505691e97b5c2b581382c1055c76d64300dbc24118bf1d83',
            'src/main/java/kim/biryeong/destiny/weapon/WeaponCombatItem.java': '1b69f247170f05e8590c8fb512643d92c92e21cd3af446848bf1e9fa85c3442e',
            'src/main/resources/assets/destiny/textures/item/weapon/w123/ammit_ar2.png': 'cc5a68851c4af60bab1156b79e25f540b9e640d1b33bc4a774075688c8a6cfff',
            'src/main/resources/assets/destiny/models/weapon/auto_rifle/gnawing_hunger_twohand.json': '854daa937d4cd5734fb3c5161e204c10c88c7415d5c2fcef47fb186e370dab9f',
            'src/main/resources/assets/destiny/items/weapon/ammit_ar2.json': 'e029d018bbb12dba3a5b941afa36e2d408a6b93c387d64bcef3ebb4f7dad43a4',
            'art/weapons/w123/ammit_ar2/design.json': 'e6bf1bbf308023405bcba57d64591f6132c86fca6073df3f5cd535f349ab67aa',
        }
        for rel, digest in pins.items():
            self.assertEqual(digest, hashlib.sha256((w.ROOT/rel).read_bytes()).hexdigest(), rel)


if __name__ == '__main__':
    unittest.main(verbosity=2)
