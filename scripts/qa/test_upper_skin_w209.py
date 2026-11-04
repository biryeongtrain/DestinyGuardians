#!/usr/bin/env python3
"""Offline arm UV/geometry contract tests; never writes shared model assets.

Run with the bundled Pillow Python and -B. The official 26.3 client JAR is
read-only input for the frozen-default provenance test.
"""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import skin_arm_models_w204 as arms


class UpperSkinW209Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = arms.generated()
        cls.layout = json.loads(cls.outputs[arms.LAYOUT])

    def test_forearm_assets_and_old_three_argument_api_are_unchanged(self):
        old_layout = json.loads(arms.LAYOUT.read_bytes())
        self.assertEqual(old_layout['geometry'], self.layout['geometry'])
        for side in arms.SIDES:
            for variant in arms.VARIANTS:
                key = f'{side}_{variant}'
                self.assertEqual(old_layout['variants'][key], self.layout['variants'][key])
                path = arms.A / f'models/{arms.PREFIX}{key}.json'
                self.assertEqual(path.read_bytes(), self.outputs[path])
            display = {'firstperson_righthand': {'rotation': [1, 2, 3], 'translation': [4, 5, 6], 'scale': [1, 2, 3]}}
            default, explicit = {}, {}
            self.assertEqual(arms.arm_nodes(side, display, default),
                             arms.arm_nodes(side, display, explicit, segment='forearm'))
            self.assertEqual(default, explicit)

    def test_upper_uses_genuine_bettermodel_rows_and_shoulder_cap(self):
        # BetterModel 3.5.1 SkinManagerImpl LEFT_ARM/RIGHT_ARM and SLIM_*_ARM:
        # enum order NORTH,SOUTH,EAST,WEST,UP; X outer, Y/Z inner.
        for side, u, v, du, dv in [('right', 44, 20, 0, 16), ('left', 36, 52, 16, 0)]:
            for variant, width in [('classic', 4), ('slim', 3)]:
                expected = []
                for face, x, y, columns, rows in [
                    ('north', u, v, width, 6), ('south', u+width+4, v, width, 6),
                    ('east', u-4, v, 4, 6), ('west', u+width, v, 4, 6),
                    ('up', u, v-4, width, 4),
                ]:
                    for a in range(columns):
                        for b in range(rows):
                            expected.append((face, [x+a, y+b], [x+a+du, y+b+dv]))
                upper = arms.pixel_layout(side, variant, segment='upper')
                self.assertEqual(expected, [(p['sourceFace'], p['baseUV'], p['sleeveUV']) for p in upper])
                lower = arms.pixel_layout(side, variant)
                upper_side = {tuple(p['baseUV']) for p in upper if p['sourceFace'] != 'up'}
                lower_side = {tuple(p['baseUV']) for p in lower if p['sourceFace'] != 'down'}
                self.assertFalse(upper_side & lower_side)
                for a, b in zip(upper, lower):
                    if a['sourceFace'] != 'up':
                        self.assertEqual(a['baseUV'][0], b['baseUV'][0])
                        self.assertEqual(a['baseUV'][1]+6, b['baseUV'][1])

    def test_geometry_has_exact_joints_outward_normals_and_full_cross_section(self):
        for side in arms.SIDES:
            for variant, width in [('classic', 2.4), ('slim', 1.8)]:
                pixels = arms.pixel_layout(side, variant, 'upper')
                self.assertEqual(112 if variant == 'classic' else 96, len(pixels))
                bounds = [(min(p['from'][k] for p in pixels), max(p['to'][k] for p in pixels)) for k in range(3)]
                self.assertEqual([(8-width/2, 8+width/2), (.5, 8), (6.8, 9.2)], bounds)
                # Side rows run shoulder -> elbow and match the forearm's outward
                # normals. A rotated UP cap is DOWN at shoulder, never at elbow.
                planes = {'north': (2, 6.8), 'south': (2, 9.2),
                          'west': (0, 8-width/2), 'east': (0, 8+width/2), 'down': (1, .5)}
                for p in pixels:
                    axis, value = planes[p['face']]
                    self.assertEqual(value, p['from'][axis])
                    self.assertEqual(value, p['to'][axis])
                    if p['sourceFace'] != 'up':
                        self.assertEqual(.5 + 1.25*p['facePixel'][1], p['from'][1])
                        self.assertEqual(p['from'][1]+1.25, p['to'][1])
                model = json.loads(self.outputs[arms.A / f'models/{arms.PREFIX}{side}_upper_{variant}.json'])
                self.assertEqual(len(pixels), len(model['elements']))
                self.assertTrue(all(len(e['faces']) == 1 for e in model['elements']))
        self.assertEqual([8, 8, 8], self.layout['upperGeometry']['elbowJoint'])
        self.assertEqual([8, .5, 8], self.layout['upperGeometry']['shoulderJoint'])
        self.assertEqual(7.5, self.layout['upperGeometry']['length'])

    def test_upper_graph_has_own_parents_offsets_and_no_pose_adjustment(self):
        display = {'firstperson_righthand': {'rotation': [11, 22, 33], 'translation': [1, 2, 3], 'scale': [.2, .3, .4]}}
        for side, offset in [('right', 320), ('left', 448)]:
            outputs = {}
            graph = arms.arm_nodes(side, display, outputs, segment='upper')
            self.assertEqual(8, graph['index'])
            self.assertEqual({'type': 'minecraft:empty'}, graph['on_false'])
            self.assertEqual(9, graph['on_true']['index'])
            for branch, variant, n in [('on_true', 'slim', 96), ('on_false', 'classic', 112)]:
                node = graph['on_true'][branch]
                self.assertEqual(list(range(offset, offset+n)), [t['index'] for t in node['tints']])
                path = arms.A / ('models/' + node['model'].split(':', 1)[1] + '.json')
                record = json.loads(outputs[path])
                self.assertEqual(display, record['display'])
                parent = f'{arms.PREFIX}{side}_upper_{variant}'
                self.assertEqual('destiny:' + parent, record['parent'])
                self.assertIn(arms.A / ('models/' + parent + '.json'), self.outputs)
            self.assertEqual(2, len(outputs))
        self.assertEqual(10, len(self.outputs))
        with self.assertRaises(ValueError):
            arms.arm_nodes('right', {}, {}, segment='shoulder')

    def test_frozen_defaults_match_official_texture_pixels_and_provenance(self):
        from PIL import Image
        resource = json.loads(arms.DEFAULTS.read_bytes())
        provenance = json.loads(arms.SOURCES.read_bytes())
        self.assertEqual({'right': 320, 'left': 448}, resource['upperColorOffsets'])
        self.assertEqual(hashlib.sha256(arms.DEFAULTS.read_bytes()).hexdigest(), provenance['resourceSha256'])
        regenerated = arms.default_skin_files(self.layout)
        self.assertEqual(arms.DEFAULTS.read_bytes(), regenerated[arms.DEFAULTS])
        self.assertEqual(arms.SOURCES.read_bytes(), regenerated[arms.SOURCES])
        with ZipFile(arms.DEFAULT_INPUTS) as archive:
            for skin, source in zip(resource['skins'], provenance['sources']):
                data = archive.read('assets/' + source['vanillaTexture'].replace(':', '/', 1))
                self.assertEqual(hashlib.sha256(data).hexdigest(), source['sha256'])
                image = Image.open(io.BytesIO(data)).convert('RGBA')
                variant = 'slim' if skin['slim'] else 'classic'
                for side in arms.SIDES:
                    upper = self.layout['variants'][f'{side}_upper_{variant}']['pixels']
                    for bare in (True, False):
                        expected = []
                        for p in upper:
                            base = image.getpixel(tuple(p['baseUV']))
                            over = image.getpixel(tuple(p['sleeveUV']))
                            level = 0 if bare else int(over[3]/255*2 + .5)
                            rgb = [int((base[c]*(2-level)+over[c]*level)/2+.5) for c in range(3)]
                            expected.append(rgb[0]*65536+rgb[1]*256+rgb[2])
                        field = side+'Upper'+('Bare' if bare else '')
                        self.assertEqual(expected, skin[field])
                        self.assertNotEqual(skin[side+('Bare' if bare else '')], skin[field])


if __name__ == '__main__':
    unittest.main(verbosity=2)
