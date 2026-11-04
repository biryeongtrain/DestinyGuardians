#!/usr/bin/env python3
"""Isolated Hammerhead data/math regressions. No game, Gradle, or live editor.

Run with bundled Python and PYTHONDONTWRITEBYTECODE=1. Optional --junit writes
an XML report to a private temporary path (not a repository build directory).
"""
import argparse
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy
import struct
import sys
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
ART = ROOT / 'art/weapons/w114/hammerhead'
KEY = 'weapon_reload_w114_hammerhead/hammerhead'
PARTS = ('body', 'magazine', 'cover')
MAGAZINE = [0, 1, 2, 3, 4, 5, 6, 7, 87, 169, 174, 175, 186, 188, 210, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222]
COVER = [89, 94, 95, 98, 100, 101, 102, 103, 104, 105, 106, 183, 184, 185, 207]
FP = ('firstperson_righthand', 'firstperson_lefthand')


def read(path):
    return json.loads(path.read_bytes())


def f32(value):
    return struct.unpack('!f', struct.pack('!f', value))[0]


def adjacent(value, direction):
    bits = struct.unpack('!I', struct.pack('!f', value))[0]
    return struct.unpack('!f', struct.pack('!I', bits + direction))[0]


def matrix(degrees):
    # Independent explicit R_x R_y R_z matrix (native quaternion rotationXYZ).
    a, b, c = map(math.radians, degrees)
    ca, cb, cc = math.cos(a), math.cos(b), math.cos(c)
    sa, sb, sc = math.sin(a), math.sin(b), math.sin(c)
    return [[cb * cc, -cb * sc, sb],
            [ca * sc + sa * sb * cc, ca * cc - sa * sb * sc, -sa * cb],
            [sa * sc - ca * sb * cc, sa * cc + ca * sb * sc, ca * cb]]


def transform(pose, point):
    m = matrix(pose['rotation'])
    return [sum(m[i][j] * point[j] * pose['scale'][j] for j in range(3)) + pose['translation'][i] for i in range(3)]


class HammerheadReload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gen = runpy.run_path(str(ROOT / 'scripts/generate_reload_w114_hammerhead.py'))
        cls.original = read(ASSETS / 'models/weapon/machine_gun/hammerhead.json')
        cls.two = read(ASSETS / 'models/weapon/machine_gun/hammerhead_twohand.json')
        cls.item = read(ASSETS / 'items/weapon/hammerhead.json')
        cls.graph = read(ASSETS / f'items/{KEY}.json')
        cls.audit = read(ART / 'partition-audit.json')
        cls.manifest = read(ART / 'manifest.json')

    def pose(self, part, frame, grip):
        return read(ASSETS / f'models/{KEY}_{frame:02}_{part}_{grip}.json')

    def test_01_literal_original_hashes(self):
        self.assertEqual(hashlib.sha256((ASSETS / 'models/weapon/machine_gun/hammerhead.json').read_bytes()).hexdigest(),
                         '7890eb2e60dc2a6547c7af7278a079b9e28575fd186683769c41f3c725c990bb')
        self.assertEqual(hashlib.sha256((ROOT / 'art/blockbench/weapons/w30/hammerhead.bbmodel').read_bytes()).hexdigest(),
                         '960021a67f284f7f7af7121c8b0e78f7b2e643d6f8d73e8fd67a775c837a3d24')
        self.gen['verify_pins']()

    def test_02_partition_literal_indices_and_complete_unchanged_elements(self):
        self.assertEqual(self.audit['indices']['magazine'], MAGAZINE)
        self.assertEqual(self.audit['indices']['cover'], COVER)
        rebuilt = {}
        for part in PARTS:
            geometry = read(ASSETS / f'models/{KEY}_{part}.json')
            self.assertEqual({k: v for k, v in geometry.items() if k != 'elements'},
                             {k: v for k, v in self.original.items() if k not in ('elements', 'display')})
            for index, element in zip(self.audit['indices'][part], geometry['elements'], strict=True):
                self.assertNotIn(index, rebuilt); rebuilt[index] = element
        self.assertEqual([rebuilt[i] for i in range(223)], self.original['elements'])
        self.assertEqual(len(rebuilt), 223)
        self.assertLessEqual(len(rebuilt), 256)

    def test_03_all_frame_grip_references_and_inventory(self):
        entries = self.graph['model']['cases'][0]['model']['entries']
        self.assertEqual(len(entries), 21)
        seen = set()
        for frame, entry in enumerate(entries):
            self.assertEqual(entry['threshold'], frame / 20)
            gate = entry['model']
            self.assertEqual((gate['type'], gate['property'], gate['index']),
                             ('minecraft:condition', 'minecraft:custom_model_data', 0))
            for grip, branch in (('native', 'on_false'), ('twohand', 'on_true')):
                composite = gate[branch]
                self.assertEqual(composite['type'], 'minecraft:composite')
                self.assertEqual(len(composite['models']), 3)
                for part, ref in zip(PARTS, composite['models'], strict=True):
                    expected = f'destiny:{KEY}_{frame:02}_{part}_{grip}'
                    self.assertEqual(ref, dict(type='minecraft:model', model=expected))
                    seen.add(expected)
                    self.assertEqual(self.pose(part, frame, grip)['parent'], f'destiny:{KEY}_{part}')
        self.assertEqual(len(seen), 126)
        self.assertEqual(len(self.manifest['assetSha256']), 130)
        for rel, pin in self.manifest['assetSha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), pin, rel)

    def test_04_exact_fp_endpoints_both_hands_all_parts_grips(self):
        for part in PARTS:
            for grip, base in (('native', self.original), ('twohand', self.two)):
                for frame in (0, 20):
                    self.assertEqual(self.pose(part, frame, grip)['display'], base['display'])

    def test_05_exact_full_fallback_and_non_fp_displays(self):
        select = self.graph['model']; case = select['cases'][0]
        self.assertEqual(select['property'], 'minecraft:display_context')
        self.assertEqual(case['when'], list(FP))
        self.assertEqual(select['fallback'], self.item['model'])
        self.assertEqual(case['model']['fallback'], self.item['model'])
        self.assertEqual((case['model']['property'], case['model']['index']), ('minecraft:custom_model_data', 1))
        self.assertEqual({k: v for k, v in self.graph.items() if k != 'model'}, {k: v for k, v in self.item.items() if k != 'model'})
        for part, frame, grip in ((p, f, g) for p in PARTS for f in range(21) for g in ('native', 'twohand')):
            base = self.original if grip == 'native' else self.two
            for context, display in self.pose(part, frame, grip)['display'].items():
                if context not in FP:
                    self.assertEqual(display, base['display'][context])

    def test_06_float32_frame_boundaries_and_inactive_fallback(self):
        entries = self.graph['model']['cases'][0]['model']['entries']
        def selected(value):
            return max((i for i, row in enumerate(entries) if f32(row['threshold']) <= value), default=-1)
        self.assertEqual(selected(-1), -1)
        for i in range(1, 21):
            threshold = f32(i / 20)
            self.assertEqual(selected(adjacent(threshold, -1)), i - 1)
            self.assertEqual(selected(threshold), i)
            self.assertEqual(selected(adjacent(threshold, 1)), i)
            if i < 20:
                self.assertEqual(selected(f32(threshold + .001)), i, 'live ownership offset remains in its frame')
        self.assertEqual(selected(0), 0)
        self.assertEqual(selected(1.001), 20)

    def test_07_actual_source_semantics_material_and_topology(self):
        source = read(ART / 'original-model-audit.json')
        self.assertEqual(source['sourceTriangles'], 25499)
        self.assertEqual([(m['material'], m['triangles']) for m in source['meshes']], [('Mag', 4334), ('Frame', 19033), ('Sight', 2132)])
        self.assertEqual(source['meshes'][1]['rigidBoneTriangles']['Magazine'], 5084)
        self.assertEqual(source['meshes'][2]['rigidBoneTriangles'], {'Cover': 2132})
        self.assertEqual(sum(c['triangles'] for c in source['components']), 25499)
        for mesh in source['meshes']:
            components = [c for c in source['components'] if c['mesh'] == mesh['name']]
            ids = sum([c['sourcePolygonIndices'] for c in components], [])
            self.assertEqual(sorted(ids), list(range(mesh['triangles'])))
            self.assertEqual(len(components), mesh['connectedComponents'])

    def test_08_triangle_distance_oracle_interior_edge_vertex_degenerate(self):
        fn = self.gen['surface_distance']
        tri = [[[0, 0, 0], [2, 0, 0], [0, 2, 0]]]
        self.assertEqual(fn([[.5, .5, 3], [-1, -1, 0], [2, 2, 0]], tri), [3, round(math.sqrt(2), 9), round(math.sqrt(2), 9)])
        self.assertEqual(fn([[1, 1, 0]], [[[0, 0, 0], [2, 0, 0], [2, 0, 0]]]), [1])

    def test_09_sample_distances_and_mixed_seam_honesty(self):
        self.assertEqual(self.audit['surfaceDisagreementIndices'], [182, 206, 207])
        self.assertEqual(len(self.audit['mixedCubeIndices']), 19)
        self.assertEqual(self.audit['noIntersectionIndices'], [])
        for row in self.audit['cubes']:
            self.assertEqual(row['part'], max(PARTS, key=lambda p: row['clippedArea'][p]))
            self.assertEqual(len(row['samplePoints']), 7)
            for p in PARTS:
                values = row['sampleSurfaceDistances'][p]
                self.assertEqual(len(values), 7)
                self.assertTrue(all(math.isfinite(v) and v >= 0 for v in values))
                self.assertAlmostEqual(sum(values) / 7, row['sampleMeanDistance'][p], places=8)
        self.assertGreater(self.audit['metrics']['magazine']['capturedClippedSemanticAreaFraction'], .94)
        self.assertGreater(self.audit['metrics']['cover']['capturedClippedSemanticAreaFraction'], .90)

    def test_10_cover_hinge_stationary_relative_to_body_in_both_hands(self):
        # Independent original TransformLink->W30 pivot oracle, relative to centre.
        pivot = [0, .22101600646972656 * 23.3089771408205, -.2692169761657715 * 23.3089771408205]
        for frame in range(21):
            for grip in ('native', 'twohand'):
                for context in FP:
                    body = transform(self.pose('body', frame, grip)['display'][context], pivot)
                    cover = transform(self.pose('cover', frame, grip)['display'][context], pivot)
                    for a, b in zip(body, cover):
                        self.assertAlmostEqual(a, b, delta=3e-6)

    def test_11_compensated_carrier_matches_native_every_sample(self):
        # Inverse carrier is Ry(-10) T(+.641864*16). Undo independently.
        for frame in range(21):
            for part in PARTS:
                for ctx in FP:
                    sign = 1 if ctx.endswith('righthand') else -1
                    inverse = matrix([0, 10 * sign, 0])
                    a = copy.deepcopy(self.pose(part, frame, 'native')['display'][ctx])
                    b = copy.deepcopy(self.pose(part, frame, 'twohand')['display'][ctx])
                    # Native ItemTransform mirrors translation X, yaw and roll.
                    for effective in (a, b):
                        effective['translation'][0] *= sign
                        effective['rotation'][1] *= sign
                        effective['rotation'][2] *= sign
                    for point in ((0, 0, 0), (1, 3, -7), (-2, 5, 4)):
                        n, t = transform(a, point), transform(b, point)
                        u = [sum(inverse[i][j] * t[j] for j in range(3)) for i in range(3)]
                        u[0] -= sign * .641864 * 16
                        for v, w in zip(n, u):
                            self.assertAlmostEqual(v, w, delta=3e-6)

    def test_12_finite_bounded_continuous_and_independent_parts(self):
        for part in PARTS:
            for grip in ('native', 'twohand'):
                previous = None
                for frame in range(21):
                    display = self.pose(part, frame, grip)['display'][FP[0]]
                    for values in display.values():
                        self.assertEqual(len(values), 3); self.assertTrue(all(math.isfinite(v) for v in values))
                    self.assertTrue(all(abs(v) < 80 for v in display['translation']))
                    self.assertTrue(all(0 < v <= 4 for v in display['scale']))
                    current = transform(display, (0, 0, 0))
                    if previous:
                        self.assertLess(math.dist(current, previous), 8)
                    previous = current
        self.assertNotEqual(self.pose('body', 9, 'native')['display'], self.pose('magazine', 9, 'native')['display'])
        self.assertNotEqual(self.pose('body', 9, 'native')['display'], self.pose('cover', 9, 'native')['display'])

    def test_13_inspection_conserves_original_bbmodel_elements_and_textures(self):
        original = read(ROOT / 'art/blockbench/weapons/w30/hammerhead.bbmodel')
        inspection = read(ART / 'inspection.bbmodel')
        self.assertEqual(inspection['elements'], original['elements'])
        self.assertEqual(inspection['textures'], original['textures'])
        ids = [u for group in inspection['outliner'] for u in group['children']]
        self.assertEqual(collections.Counter(ids), collections.Counter(e['uuid'] for e in original['elements']))

    def test_14_reviewed_reference_hashes_and_claim_limits(self):
        from PIL import Image
        provenance = read(ART / 'gameplay-provenance.json')
        self.assertEqual(len(provenance['frames']), 16)
        self.assertFalse(self.manifest['sourceAnimationRecovered'])
        self.assertFalse(self.manifest['handIK'])
        self.assertFalse(self.manifest['nativeGameplayVerified'])
        for frame in provenance['frames']:
            p = ART / frame['path']
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), frame['sha256'])
            image = Image.open(p); self.assertLessEqual(image.width, 1280); self.assertLessEqual(image.height, 720)
        for name in ('gameplay-contact.png', 'partition-contact.png', 'preview-contact.png'):
            Image.open(ART / name).verify()

    def test_15_generator_only_emits_exact_manifest_ownership(self):
        # Independent literal inventory: no generator constants or batch manifest.
        prefix = 'weapon_reload_w114_hammerhead/hammerhead'
        assets = {ASSETS / f'items/{prefix}.json'}
        for part in ('body', 'magazine', 'cover'):
            assets.add(ASSETS / f'models/{prefix}_{part}.json')
            for frame in range(21):
                for grip in ('native', 'twohand'):
                    assets.add(ASSETS / f'models/{prefix}_{frame:02}_{part}_{grip}.json')
        art = {ART / name for name in ('original-model-audit.json', 'partition-audit.json',
            'partition-contact.png', 'preview-contact.png', 'inspection.bbmodel', 'manifest.json')}
        expected = assets | art
        self.assertEqual(len(assets), 130)
        self.assertEqual(len(expected), 136)
        self.assertEqual(self.gen['expected_output_paths'](), expected)
        self.assertEqual({ROOT / p for p in self.manifest['assetSha256']}, assets)
        recorded = {ROOT / p for p in self.manifest['auditSha256']} | {ART / 'manifest.json'}
        self.assertEqual(recorded, art)
        valid = {p: p.read_bytes() for p in sorted(expected)}
        self.gen['write_outputs'](valid, True)
        # Put invalid paths last: complete preflight must reject before ANY write.
        for outside in (ROOT / 'README.md', ART / 'unexpected.json', ROOT.parent / 'escape.json'):
            invalid = {**valid, outside: b'bad'}
            for check in (False, True):
                with mock.patch.object(Path, 'mkdir') as mkdir, mock.patch.object(Path, 'write_bytes') as write:
                    with self.assertRaisesRegex(AssertionError, 'Not an exact generated path'):
                        self.gen['write_outputs'](invalid, check)
                    mkdir.assert_not_called(); write.assert_not_called()
        incomplete = dict(valid); incomplete.pop(ART / 'manifest.json')
        with mock.patch.object(Path, 'mkdir') as mkdir, mock.patch.object(Path, 'write_bytes') as write:
            with self.assertRaisesRegex(AssertionError, 'Missing generated paths'):
                self.gen['write_outputs'](incomplete)
            mkdir.assert_not_called(); write.assert_not_called()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--junit', type=Path); args = ap.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(HammerheadReload)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if args.junit:
        failures = dict((test.id(), message) for test, message in result.failures + result.errors)
        root = ET.Element('testsuite', name='HammerheadReloadW114Python', tests=str(result.testsRun),
                          failures=str(len(result.failures)), errors=str(len(result.errors)))
        for name in unittest.defaultTestLoader.getTestCaseNames(HammerheadReload):
            case = ET.SubElement(root, 'testcase', classname='HammerheadReload', name=name)
            key = '__main__.HammerheadReload.' + name
            if key in failures:
                ET.SubElement(case, 'failure').text = failures[key]
        args.junit.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(root).write(args.junit, encoding='utf-8', xml_declaration=True)
    sys.exit(not result.wasSuccessful())
