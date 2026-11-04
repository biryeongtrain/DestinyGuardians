#!/usr/bin/env python3
"""Targeted W151 artwork regression; standard library, no game/build/dependencies.

Run: rtk proxy python3 -B scripts/qa/test_sight_bodies_w151_rifles.py
Tests never write fixtures, caches, models, textures or shared generators.
"""
import copy
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import runpy
import struct
import subprocess
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT/'scripts/generate_sight_bodies_w151_rifles.py'
G = runpy.run_path(str(SCRIPT))
ASSETS = ROOT/'src/main/resources/assets/destiny'
IDS = ('halfdan_d', 'ammit_ar2', 'gnawing_hunger', 'steelfeather_repeater',
       'frontier_justice', 'distant_relation')
REMOVALS = ['optic_housing_core', 'optic_housing_shoulder_l', 'objective_glass', 'ocular_glass']


def strict_read(path):
    def reject(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    return json.loads(path.read_bytes(), parse_constant=reject)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_rgba(path):
    """Decode the small existing W148 RGBA atlas without installing Pillow."""
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Not a PNG')
    offset, compressed = 8, bytearray()
    while offset < len(data):
        size = struct.unpack('>I', data[offset:offset+4])[0]
        tag, chunk = data[offset+4:offset+8], data[offset+8:offset+8+size]
        if tag == b'IHDR':
            width, height, bits, color, _, _, interlace = struct.unpack('>IIBBBBB', chunk)
            if (bits, color, interlace) != (8, 6, 0):
                raise ValueError('Expected noninterlaced RGBA8')
        elif tag == b'IDAT':
            compressed.extend(chunk)
        offset += size + 12
    raw, stride, pixels = zlib.decompress(compressed), width*4, []
    previous = [0]*stride
    for y in range(height):
        start = y*(stride+1)
        filter_, row = raw[start], list(raw[start+1:start+1+stride])
        for i in range(stride):
            a, b, c = row[i-4] if i >= 4 else 0, previous[i], previous[i-4] if i >= 4 else 0
            if filter_ == 0:
                predictor = 0
            elif filter_ == 1:
                predictor = a
            elif filter_ == 2:
                predictor = b
            elif filter_ == 3:
                predictor = (a+b)//2
            elif filter_ == 4:
                p = a+b-c
                predictor = min((a, b, c), key=lambda v: abs(p-v))
            else:
                raise ValueError('Unknown PNG filter')
            row[i] = (row[i]+predictor) % 256
        pixels.append([tuple(row[i:i+4]) for i in range(0, stride, 4)])
        previous = row
    return width, height, pixels


class SightBodies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = strict_read(ROOT/'art/weapons/w151/rifles-sights.json')
        cls.rows = {r['id']: r for r in cls.manifest['weapons']}
        cls.models = {w: strict_read(ASSETS/f"models/{cls.rows[w]['body']}.json") for w in IDS}
        cls.sources = {w: strict_read(ROOT/cls.rows[w]['source']) for w in IDS}

    def test_all_six_contract_and_finite_json(self):
        self.assertEqual(set(self.manifest), {'weapons'})
        self.assertEqual(tuple(self.rows), IDS)
        required = {'id', 'family', 'body', 'sightCenter', 'forwardPoint', 'style',
                    'eyeSide', 'plane', 'scale', 'eyeToSightMeters', 'removedSightNames',
                    'elementCount', 'source', 'sourceSha256', 'reference'}
        for w, row in self.rows.items():
            with self.subTest(weapon=w):
                self.assertLessEqual(required, row.keys())
                self.assertEqual(row['body'], f'weapon_sight_w151/{w}_body')
                self.assertEqual(row['family'], 'scout_rifle' if w in IDS[-2:] else 'auto_rifle')
                self.assertEqual((row['eyeSide'], row['plane'], row['scale'], row['eyeToSightMeters']),
                                 ('+Z', 'XY', .9, .65))
                x, y, z = row['sightCenter']
                self.assertEqual(row['forwardPoint'], [x, y, round(z-2, 6)])
                self.assertEqual(len(row['sightCenter']), 3)
                self.assertTrue(all(math.isfinite(v) for v in (x, y, z)))
                self.assertEqual(row['clearApertureHalfSize'], .03)

    def test_source_geometry_faces_uv_rotation_order_preserved(self):
        for w in IDS:
            with self.subTest(weapon=w):
                removed = self.rows[w]['removedSightNames']
                expected = [e for e in self.sources[w]['elements'] if e['name'] not in removed]
                actual = [e for e in self.models[w]['elements'] if not e['name'].startswith('w151_')]
                self.assertEqual(actual, expected)  # Entire records, including faces/UV/rotations.

    def test_source_model_metadata_and_textures_preserved(self):
        for w in IDS:
            with self.subTest(weapon=w):
                source = copy.deepcopy(self.sources[w])
                source.pop('display', None)
                source.pop('elements')
                actual = copy.deepcopy(self.models[w])
                actual.pop('elements')
                sight = actual['textures'].pop('sight')
                self.assertEqual(sight, 'destiny:item/weapon/w148/sights')
                self.assertEqual(actual, source)
                self.assertNotIn('display', self.models[w])

    def test_only_named_obstructing_sight_parts_removed(self):
        for w in IDS:
            expected = REMOVALS if w == 'distant_relation' else []
            self.assertEqual(self.rows[w]['removedSightNames'], expected)
            names = {e['name']: e for e in self.sources[w]['elements']}
            for name in expected:
                self.assertTrue(any(G['ray_hit'](names[name], a, b)
                                    for a, b in G['sight_rays'](self.rows[w])), name)
                restored = copy.deepcopy(self.models[w])
                restored['elements'].append(names[name])
                self.assertIn(name, G['blockers'](restored, self.rows[w]))

    def test_complete_body_parallel_and_eye_perspective_clearance(self):
        for w in IDS:
            with self.subTest(weapon=w):
                self.assertEqual(len(list(G['sight_rays'](self.rows[w]))), 98)
                self.assertEqual(G['blockers'](self.models[w], self.rows[w]), [])

    def test_dense_aperture_rays_independent_of_generator_grid(self):
        # Independent sample spacing and endpoints; catches changes to grid logic.
        for w in IDS:
            row = self.rows[w]
            x, y, z = row['sightCenter']
            eye = z + .65*16/.9
            for dx, dy in itertools.product((-.03, -.019, -.007, 0, .011, .023, .03), repeat=2):
                factor = (eye+35)/(eye-z)
                a, b = [x, y, eye], [x+dx*factor, y+dy*factor, -35]
                hits = [e['name'] for e in self.models[w]['elements'] if G['ray_hit'](e, a, b)]
                self.assertEqual(hits, [], (w, dx, dy, hits))

    def test_tip_is_centered_below_air_and_visible_from_eye(self):
        for w in IDS:
            row = self.rows[w]
            tip = next(e for e in self.models[w]['elements'] if e['name'] == row['aimingTipName'])
            x, y, z = row['sightCenter']
            self.assertAlmostEqual((tip['from'][0]+tip['to'][0])/2, x)
            self.assertAlmostEqual(tip['to'][1], y-.085)
            self.assertLess(tip['to'][1], y-row['clearApertureHalfSize'])
            self.assertLess(tip['to'][2], z)
            self.assertEqual(row['aimingTip'], [x, tip['to'][1], (tip['from'][2]+tip['to'][2])/2])
            eye = z+.65*16/.9
            target = [x, tip['to'][1]-.01, row['aimingTip'][2]]
            self.assertTrue(G['ray_hit'](tip, [x, y, eye], target))
            projected_top = (y-tip['to'][1])*(eye-z)/(eye-row['aimingTip'][2])
            self.assertGreater(projected_top, .03)
            self.assertLess(projected_top, .1)

    def test_reference_specific_frames_retained(self):
        frames = {
            'halfdan_d': ['Sight_base', 'Sight_ear_-1', 'Sight_ear_1', 'Sight_sill'],
            'ammit_ar2': ['Sight_rail', 'Peep_post_-1', 'Peep_post_1', 'Peep_top', 'Peep_base'],
            'gnawing_hunger': ['optic/base', 'optic/rear-adjuster', 'optic/stalk'] + [f'optic/hood-{i}' for i in range(8)],
            'steelfeather_repeater': ['sight_base', 'sight_ear_-1', 'sight_ear_1', 'sight_cradle', 'sight_front_saddle'],
            'frontier_justice': ['post_base', 'post_riser', 'post_cheek_-1', 'post_cheek_1', 'post_corner_-1', 'post_corner_1', 'post_cap'],
            'distant_relation': ['optic_roof', 'optic_mount_0', 'optic_mount_1', 'optic_dial_near', 'optic_dial_far'] +
                [f'{end}_rim_{i}' for end in ('objective', 'ocular') for i in range(8)],
        }
        self.assertEqual(len({r['style'] for r in self.rows.values()}), 6)
        for w, names in frames.items():
            body = {e['name']: e for e in self.models[w]['elements']}
            source = {e['name']: e for e in self.sources[w]['elements']}
            for name in names:
                self.assertEqual(body[name], source[name])
            if w != 'distant_relation':
                self.assertEqual(self.rows[w]['addedSightNames'], ['w151_aim_stem', 'w151_aim_tip'])

    def test_scope_has_long_hollow_housing_and_original_colored_uv(self):
        body = {e['name']: e for e in self.models['distant_relation']['elements']}
        for name in ['scope_floor', 'scope_ceiling', 'scope_inner_left', 'scope_inner_right',
                     'scope_outer_left', 'scope_outer_right']:
            e = body['w151_'+name]
            self.assertEqual((e['from'][2], e['to'][2]), (4.21, 7.09))
            self.assertTrue(all(f['texture'] == '#0' for f in e['faces'].values()))
        self.assertEqual(len(self.rows['distant_relation']['addedSightNames']), 8)

    def test_real_counts_include_moving_magazine_and_spare(self):
        for w in IDS:
            row = self.rows[w]
            count = len(self.models[w]['elements'])
            self.assertEqual(row['elementCount'], count)
            companion = 0
            if w == 'ammit_ar2':
                self.assertEqual(row['companionModel'], 'src/main/resources/assets/destiny/models/weapon_surface_w123/ammit_ar2_magazine.json')
                companion = len(strict_read(ROOT/row['companionModel'])['elements'])
                self.assertEqual(companion, 5)
                self.assertEqual(row['companionSha256'], digest(ROOT/row['companionModel']))
            self.assertEqual(row['companionElementCount'], companion)
            self.assertEqual(row['assemblyElementCount'], count+companion)
            self.assertEqual(row['assemblyWithSpareMagazineCount'], count+2*companion)
            self.assertLessEqual(count+2*companion, 1000)

    def test_native_cuboids_explicit_faces_resolved_opaque_tip(self):
        width, height, pixels = png_rgba(ASSETS/'textures/item/weapon/w148/sights.png')
        for w in IDS:
            model = self.models[w]
            names = [e['name'] for e in model['elements']]
            self.assertEqual(len(names), len(set(names)))
            for e in model['elements']:
                self.assertLessEqual(set(e), {'name', 'from', 'to', 'faces', 'rotation'})
                self.assertTrue(all(math.isfinite(v) for v in e['from']+e['to']))
                self.assertTrue(all(a < b for a, b in zip(e['from'], e['to'])))
                self.assertEqual(set(e['faces']), set(G['FACES']))
                for face in e['faces'].values():
                    self.assertTrue(all(math.isfinite(v) and 0 <= v <= 16 for v in face['uv']))
                    texture = model['textures'][face['texture'].removeprefix('#')]
                    self.assertTrue((ASSETS/('textures/'+texture.removeprefix('destiny:')+'.png')).is_file())
                    if face['texture'] == '#sight':
                        u, v, u1, v1 = face['uv']
                        samples = [pixels[y][x] for y in range(int(v*height/16), math.ceil(v1*height/16))
                                   for x in range(int(u*width/16), math.ceil(u1*width/16))]
                        self.assertTrue(samples)
                        self.assertTrue(all(p[3] == 255 for p in samples))

    def test_current_source_and_texture_hashes(self):
        for row in self.rows.values():
            self.assertEqual(row['sourceSha256'], digest(ROOT/row['source']))
            self.assertTrue(row['source'].startswith('src/main/resources/assets/destiny/models/weapon_surface_w123/'))
            self.assertEqual(row['sightTextureSha256'], digest(ROOT/G['SIGHT_TEXTURE']))

    def test_actual_default_photos_and_prior_rip_provenance(self):
        references = {r['id']: r for r in strict_read(ROOT/'art/weapons/w31/references.json')}
        for w in IDS:
            r = self.rows[w]['reference']
            self.assertEqual(r['photo'], f'/tmp/destiny-weapons-w31/references/{w}.jpg')
            self.assertEqual(r['photoSha256'], references[w]['sha256'])
            self.assertEqual(digest(Path(r['photo'])), r['photoSha256'])
            self.assertEqual(Path(r['photo']).read_bytes()[:2], b'\xff\xd8')
            self.assertEqual(r['screenshot'], references[w]['screenshot'])
            self.assertEqual(r['bungieHash'], references[w]['bungie_hash'])
            self.assertGreater(len(r['notes']), 90)
            for p, h in r['provenance'].items():
                self.assertEqual(digest(ROOT/p), h)
            prior = strict_read(ROOT/f'art/weapons/w123/{w}/manifest.json')['raw_input_sha256']
            self.assertTrue(r['priorRipSha256'])
            for p, h in r['priorRipSha256'].items():
                self.assertEqual(prior[p], h)

    def test_deterministic_outputs_and_exact_output_scope(self):
        first, second = G['generate'](), G['generate']()
        expected = {Path('art/weapons/w151/rifles-sights.json')} | {
            Path(f'src/main/resources/assets/destiny/models/weapon_sight_w151/{w}_body.json') for w in IDS}
        self.assertEqual(set(first), expected)
        self.assertEqual(first, second)
        for path, data in first.items():
            self.assertEqual((ROOT/path).read_bytes(), data, str(path))

    def test_comparator_rejects_tampered_and_missing_output_without_writes(self):
        outputs = G['generate']()
        path = next(iter(outputs))
        outputs[path] += b' '
        self.assertEqual(G['mismatches'](outputs), [str(path)])
        absent = Path('src/main/resources/assets/destiny/models/weapon_sight_w151/no_such_w151_model.json')
        self.assertEqual(G['mismatches']({absent: b'{}\n'}), [str(absent)])
        self.assertFalse((ROOT/absent).exists())

    def test_verify_cli_is_read_only(self):
        inputs = [ROOT/r['source'] for r in self.rows.values()]
        outputs = [ROOT/p for p in G['generate']()]
        paths = inputs+outputs+[SCRIPT, ROOT/'scripts/generate_sight_ads_w148.py',
            ROOT/'scripts/qa/test_sight_bodies_w151_rifles.py', ROOT/G['SIGHT_TEXTURE']]
        before = {p: (digest(p), p.stat().st_mtime_ns) for p in paths}
        process = subprocess.run(['rtk', 'proxy', sys.executable, '-B', str(SCRIPT), '--verify'],
            cwd=ROOT, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
            capture_output=True, text=True, check=False)
        self.assertEqual(process.returncode, 0, process.stdout+process.stderr)
        self.assertIn('verified', process.stdout)
        self.assertEqual(before, {p: (digest(p), p.stat().st_mtime_ns) for p in paths})


class RotationAwareRays(unittest.TestCase):
    def test_rotated_bar_hit_outside_unrotated_bounds(self):
        e = dict(name='slanted_ear', **{'from': [-1, -.04, -.1], 'to': [1, .04, .1]},
                 rotation=dict(origin=[0, 0, 0], axis='z', angle=45))
        self.assertTrue(G['ray_hit'](e, [.5, .5, 3], [.5, .5, -3]))
        unrotated = {k: v for k, v in e.items() if k != 'rotation'}
        self.assertFalse(G['ray_hit'](unrotated, [.5, .5, 3], [.5, .5, -3]))

    def test_rotated_bar_miss_inside_world_aabb(self):
        e = dict(name='slanted_ear', **{'from': [-1, -.04, -.1], 'to': [1, .04, .1]},
                 rotation=dict(origin=[0, 0, 0], x=0, y=0, z=45))
        self.assertFalse(G['ray_hit'](e, [0, .5, 3], [0, .5, -3]))

    def test_compound_xyz_inverse_order_and_nonzero_origin(self):
        e = dict(rotation=dict(origin=[5, 6, 7], x=90, y=90, z=90))
        for a, b in zip(G['inverse_point'](e, [8, 8, 6]), [6, 8, 10]):
            self.assertAlmostEqual(a, b)

    def test_arbitrary_rotated_opaque_lens_rejected_in_actual_bodies(self):
        rows = strict_read(ROOT/'art/weapons/w151/rifles-sights.json')['weapons']
        for row in rows:
            x, y, z = row['sightCenter']
            lens = dict(name='old_non_sight_named_opaque_pane',
                **{'from': [x-.5, y-.5, z-.015], 'to': [x+.5, y+.5, z+.015]},
                rotation=dict(origin=[x, y, z], x=17, y=31, z=23))
            body = strict_read(ASSETS/f"models/{row['body']}.json")
            body['elements'].append(lens)
            self.assertIn(lens['name'], G['blockers'](body, row))

    def test_thin_rotated_lens_between_z_samples_is_hit(self):
        e = dict(name='thin_glass', **{'from': [-.5, -.5, .12345], 'to': [.5, .5, .12346]},
                 rotation=dict(origin=[0, 0, .123455], axis='y', angle=67))
        self.assertTrue(G['ray_hit'](e, [0, 0, 10], [0, 0, -20]))

    def test_legacy_rescale_and_finite_segment(self):
        e = dict(name='rescaled', **{'from': [-.1, -.1, -.1], 'to': [.1, .1, .1]},
                 rotation=dict(origin=[0, 0, 0], axis='z', angle=45, rescale=True))
        self.assertTrue(G['ray_hit'](e, [.18, 0, 1], [.18, 0, -1]))
        e['rotation']['rescale'] = False
        self.assertFalse(G['ray_hit'](e, [.18, 0, 1], [.18, 0, -1]))
        self.assertFalse(G['ray_hit'](e, [0, 0, 3], [0, 0, 2]))
        self.assertFalse(G['ray_hit'](e, [0, 0, -2], [0, 0, -3]))


if __name__ == '__main__':
    unittest.main(verbosity=2)
