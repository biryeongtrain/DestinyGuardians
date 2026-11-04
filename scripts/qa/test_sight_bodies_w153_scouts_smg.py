#!/usr/bin/env python3
"""Targeted W153 regression, standard library only; no build, caches or fixtures.

Run: rtk proxy python3 -B scripts/qa/test_sight_bodies_w153_scouts_smg.py
Offline schema/geometry checks are not the actual 26.3 parser or native QA.
"""
import contextlib
import copy
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import runpy
import struct
import subprocess
import sys
import unittest
from unittest import mock
import zlib

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT/'scripts/generate_sight_bodies_w153_scouts_smg.py'
G = runpy.run_path(str(SCRIPT))
IDS = ('patron_of_lost_causes', 'aishas_embrace', 'long_arm', 'antiope_d',
       'bug_out_bag', 'ikelos_smg_v1_0_1', 'the_recluse')
COUNTS = (98, 92, 119, 120, 101, 135, 68)
EYES = (.42, .38, .38, .52, .32, .32, .48)
REMOVED = {
    IDS[0]: {'front_recessed_glass', 'rear_recessed_glass'},
    IDS[1]: {'front_recessed_lens', 'rear_recessed_lens'},
    IDS[2]: {'wrapped_sight_core', 'wrapped_sight_corner_-1_1',
             'wrapped_sight_corner_1_1', 'sight_front_core',
             'sight_front_corner_-1_1', 'sight_front_corner_1_1'},
    IDS[3]: set(), IDS[4]: {'optic_lens', 'optic_rear_ramp'},
    IDS[5]: set(), IDS[6]: set(),
}


def read(path):
    def reject(value):
        raise ValueError('Nonfinite JSON: '+value)
    return json.loads((ROOT/path).read_bytes(), parse_constant=reject)


def digest(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def png_rgba(path):
    """Decode existing noninterlaced RGBA8 atlas; no Pillow installation."""
    data = (ROOT/path).read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Not PNG')
    offset, compressed = 8, bytearray()
    while offset < len(data):
        size = struct.unpack('>I', data[offset:offset+4])[0]
        tag, chunk = data[offset+4:offset+8], data[offset+8:offset+8+size]
        if tag == b'IHDR':
            width, height, bits, color, _, _, interlace = struct.unpack('>IIBBBBB', chunk)
            if (bits, color, interlace) != (8, 6, 0):
                raise ValueError('Expected RGBA8 PNG')
        elif tag == b'IDAT':
            compressed.extend(chunk)
        offset += size+12
    raw, stride, pixels = zlib.decompress(compressed), width*4, []
    previous = bytearray(stride)
    for y in range(height):
        offset = y*(stride+1)
        filter_, row = raw[offset], bytearray(raw[offset+1:offset+1+stride])
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
        pixels.append(row)
        previous = row
    return width, height, pixels


def face_pixel(image, uv, fx=.5, fy=.5):
    w, h, rows = image
    u, v, u1, v1 = uv
    x, y = min(w-1, int((u+(u1-u)*fx)*w/16)), min(h-1, int((v+(v1-v)*fy)*h/16))
    return tuple(rows[y][x*4:x*4+4])


class W153Sights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = read(G['MANIFEST'])
        cls.rows = {r['id']: r for r in cls.manifest['weapons']}
        cls.sources = {w: read(cls.rows[w]['source']) for w in IDS}
        cls.models = {w: read(G['ASSETS']/f"models/{cls.rows[w]['body']}.json") for w in IDS}

    def test_exact_manifest_and_wrapper_contract(self):
        self.assertEqual(set(self.manifest), {'weapons'})
        self.assertEqual(tuple(self.rows), IDS)
        for w, row in self.rows.items():
            with self.subTest(weapon=w):
                self.assertEqual(row['body'], f'weapon_sight_w153/{w}_body')
                self.assertEqual(row['family'], 'scout_rifle' if w in IDS[:3] else 'submachine_gun')
                self.assertTrue((ROOT/G['ASSETS']/f"models/weapon/{row['family']}/{w}.json").is_file())
                self.assertEqual((row['eyeSide'], row['plane'], row['scale']), ('+Z', 'XY', .9))
                x, y, z = row['sightCenter']
                self.assertEqual(row['forwardPoint'], [x, y, round(z-2, 6)])
                self.assertEqual(row['source'], str(G['ASSETS']/f'models/weapon_surface_w123/{w}.json'))

    def test_distinct_original_optics_and_eye_relief(self):
        self.assertEqual(len({r['style'] for r in self.rows.values()}), 7)
        self.assertEqual(tuple(r['eyeToSightMeters'] for r in self.rows.values()), EYES)
        self.assertGreater(len(set(EYES)), 3)
        # The actual original optic bars, not new generic frames, define anchors.
        for w, row in self.rows.items():
            source = {e['name']: e for e in self.sources[w]['elements']}
            self.assertGreaterEqual(len(row['visibleSightNames']), 3)
            self.assertTrue(set(row['visibleSightNames']) <= source.keys())
            for name in row['visibleSightNames']:
                self.assertIn(source[name], self.models[w]['elements'])

    def test_finite_emitted_schema_and_assembled_budget(self):
        for w, expected in zip(IDS, COUNTS):
            row, model = self.rows[w], self.models[w]
            with self.subTest(weapon=w):
                self.assertEqual(len(model['elements']), expected)
                self.assertEqual(row['elementCount'], expected)
                self.assertEqual(row['assemblyElementCount'], expected)
                self.assertLessEqual(expected, 1000)
                self.assertEqual(len({e['name'] for e in model['elements']}), expected)
                self.assertNotIn('display', model)
                for e in model['elements']:
                    self.assertNotIn('vertices', e)
                    self.assertNotIn('triangles', e)
                    self.assertTrue(all(math.isfinite(v) for v in e['from']+e['to']))
                    self.assertTrue(all(a < b for a, b in zip(e['from'], e['to'])))
                    self.assertEqual(set(e['faces']), set(G['FACES']))
                    for f in e['faces'].values():
                        self.assertEqual(len(f['uv']), 4)
                        self.assertTrue(all(math.isfinite(v) and 0 <= v <= 16 for v in f['uv']))
                        self.assertIn(f['texture'][1:], model['textures'])

    def test_source_non_sight_records_exact_including_uv_and_order(self):
        for w in IDS:
            with self.subTest(weapon=w):
                self.assertEqual(set(self.rows[w]['removedSightNames']), REMOVED[w])
                expected = [e for e in self.sources[w]['elements'] if e['name'] not in REMOVED[w]]
                actual = [e for e in self.models[w]['elements'] if not e['name'].startswith('w153_')]
                self.assertEqual(actual, expected)

    def test_all_source_metadata_and_texture_bindings_preserved(self):
        for w in IDS:
            source, model = copy.deepcopy(self.sources[w]), copy.deepcopy(self.models[w])
            source.pop('display', None)
            source.pop('elements')
            model.pop('elements')
            self.assertEqual(model['textures'].pop('sight'), 'destiny:item/weapon/w148/sights')
            self.assertEqual(model, source)

    def test_magazines_once_and_no_companion_required(self):
        for w, row in self.rows.items():
            self.assertEqual(row['companionElementCount'], 0)
            self.assertNotIn('companionModel', row)
            original_mag = [e for e in self.sources[w]['elements'] if 'magazine' in e['name']]
            actual_mag = [e for e in self.models[w]['elements'] if 'magazine' in e['name']]
            self.assertEqual(actual_mag, original_mag)
            self.assertIn('seated magazine once', row['assemblyPolicy'])
        recluse_mag = read(G['ASSETS']/'models/weapon_surface_w123/the_recluse_magazine.json')['elements']
        self.assertEqual(len(recluse_mag), 4)
        for piece in recluse_mag:
            self.assertEqual(self.models['the_recluse']['elements'].count(piece), 1)

    def test_photo_and_w123_design_manifest_review_provenance(self):
        refs = {r['id']: r for r in read('art/weapons/w31/references.json')}
        for w, row in self.rows.items():
            with self.subTest(weapon=w):
                ref = row['reference']
                self.assertEqual(digest(row['source']), row['sourceSha256'])
                self.assertEqual(ref['photoSha256'], refs[w]['sha256'])
                self.assertEqual(digest(Path(ref['photo'])), ref['photoSha256'])
                self.assertEqual(ref['url'], refs[w]['screenshot'])
                self.assertEqual(ref['bungieHash'], refs[w]['bungie_hash'])
                self.assertGreater(len(ref['notes']), 150)
                self.assertTrue(ref['priorRipSha256'])
                self.assertEqual(set(Path(p).name for p in ref['provenance']),
                                 {'design.json', 'manifest.json', 'review.md'})
                for path, sha in ref['provenance'].items():
                    self.assertEqual(digest(path), sha)

    def test_original_texture_canonical_split_and_reload_hashes(self):
        for w, row in self.rows.items():
            hashes = row['reference']['preservedInputSha256']
            self.assertIn(str(G['ASSETS']/f"models/weapon/{row['family']}/{w}.json"), hashes)
            self.assertIn(row['source'], hashes)
            self.assertTrue(any(p.endswith(f'/w123/{w}.png') for p in hashes))
            for path, sha in hashes.items():
                self.assertEqual(digest(path), sha)
            self.assertEqual(digest(G['SIGHT_TEXTURE']), row['sightTextureSha256'])

    def test_actual_eye_usable_perspective_aperture(self):
        for w, row in self.rows.items():
            with self.subTest(weapon=w):
                self.assertEqual(row['clearApertureBounds'], [[-.1, -.06], [.1, .1]])
                rays = list(G['aperture_rays'](row))
                self.assertEqual(len(rays), 72)
                self.assertEqual(G['blockers'](self.models[w], row), [])

    def test_original_rim_not_hidden_by_foreground(self):
        for w, row in self.rows.items():
            with self.subTest(weapon=w):
                visible = G['rim_visibility'](self.models[w], row)
                self.assertEqual(visible, row['rimVisibility'])
                allowed = set(row['visibleSightNames']+row['allowedRimSelfOccluders'])
                self.assertTrue(set(visible.values()) <= allowed)
                self.assertFalse(any(any(v in n.lower() for v in ('stock', 'receiver', 'cloth', 'disc'))
                                     for n in visible.values()))
                direct = sum(n in row['visibleSightNames'] for n in visible.values())
                self.assertGreaterEqual(direct/len(visible), .625)

    def test_all_aiming_tips_visible_and_seated(self):
        for w, row in self.rows.items():
            with self.subTest(weapon=w):
                model = self.models[w]
                tip = next(e for e in model['elements'] if e['name'] == 'w153_aim_tip')
                stem = next(e for e in model['elements'] if e['name'] == 'w153_aim_stem')
                target = [(a+b)/2 for a, b in zip(tip['from'], tip['to'])]
                hits = [(t, e['name']) for e in model['elements']
                        if (t := G['segment_entry'](e, G['eye'](row), target)) is not None]
                self.assertEqual(min(hits)[1], 'w153_aim_tip')
                self.assertEqual(stem['to'][1], tip['from'][1])
                self.assertEqual(tip['to'][1], row['aimingTip'][1])
                distance = row['eyeToSightMeters']*16/.9
                gap = (row['sightCenter'][1]-row['aimingTip'][1])*distance/(G['eye'](row)[2]-row['aimingTip'][2])
                self.assertAlmostEqual(gap, .08, places=6)
                cfg = G['SPECS'][w]
                self.assertEqual(stem['from'][1], cfg['floor'])

    def test_reinserting_opaque_glass_is_rejected(self):
        for w, names in ((IDS[0], REMOVED[IDS[0]]), (IDS[1], REMOVED[IDS[1]]),
                         (IDS[4], {'optic_lens'})):
            for name in names:
                with self.subTest(weapon=w, lens=name):
                    mutant = copy.deepcopy(self.models[w])
                    mutant['elements'].append(next(e for e in self.sources[w]['elements'] if e['name'] == name))
                    self.assertIn(name, G['blockers'](mutant, self.rows[w]))

    def test_center_ray_alone_cannot_pass_foreground_regression(self):
        # A broad foreground stock-like slab leaves the center ray clear but
        # hides the upper window/rim. This is the W152 failure class.
        for w, row in self.rows.items():
            x, y, z = row['sightCenter']
            cap = dict(name='stock/foreground_regression', **{'from': [x-2, y+.025, z+.7],
                       'to': [x+2, y+2, z+1.0]})
            mutant = copy.deepcopy(self.models[w])
            mutant['elements'].append(cap)
            self.assertIsNone(G['segment_entry'](cap, G['eye'](row), [x, y, -40]))
            self.assertIn(cap['name'], G['blockers'](mutant, row))
            self.assertIn(cap['name'], G['rim_visibility'](mutant, row).values())

    def test_long_arm_restored_filled_wrap_obstructs_peep(self):
        row = self.rows['long_arm']
        mutant = copy.deepcopy(self.models['long_arm'])
        removed = REMOVED['long_arm']
        mutant['elements'] = [e for e in mutant['elements'] if '_groove_' not in e['name']]
        mutant['elements'].extend(e for e in self.sources['long_arm']['elements'] if e['name'] in removed)
        self.assertIn('wrapped_sight_core', G['blockers'](mutant, row))
        # The real aperture and most of the original wrap cylinder survive.
        for name in row['visibleSightNames']:
            self.assertTrue(any(e['name'] == name for e in mutant['elements']))
        self.assertTrue(all(row['replacedSightPieces'].values()))

    def test_bug_out_bag_original_ramp_really_occludes(self):
        w = 'bug_out_bag'
        mutant = copy.deepcopy(self.models[w])
        mutant['elements'] = [e for e in mutant['elements'] if e['name'] != 'w153_ramp_lower']
        ramp = next(e for e in self.sources[w]['elements'] if e['name'] == 'optic_rear_ramp')
        mutant['elements'].append(ramp)
        self.assertIn('optic_rear_ramp', G['blockers'](mutant, self.rows[w]))
        cropped = next(e for e in self.models[w]['elements'] if e['name'] == 'w153_ramp_lower')
        self.assertEqual(cropped['rotation'], ramp['rotation'])
        self.assertEqual(cropped['from'], ramp['from'])
        self.assertAlmostEqual(ramp['to'][1]-cropped['to'][1], .185)
        self.assertEqual((cropped['to'][0], cropped['to'][2]), (ramp['to'][0], ramp['to'][2]))

    def test_replacement_crops_are_inside_own_donors(self):
        for w, row in self.rows.items():
            source = {e['name']: e for e in self.sources[w]['elements']}
            model = {e['name']: e for e in self.models[w]['elements']}
            for old, names in row['replacedSightPieces'].items():
                donor = source[old]
                for name in names:
                    e = model[name]
                    self.assertEqual(e.get('rotation'), donor.get('rotation'))
                    self.assertTrue(all(a <= b < c <= d for a, b, c, d in
                        zip(donor['from'], e['from'], e['to'], donor['to'])))
                    for face, data in e['faces'].items():
                        old_face = donor['faces'][face]
                        self.assertEqual({k: v for k, v in data.items() if k != 'uv'},
                                         {k: v for k, v in old_face.items() if k != 'uv'})
                        for axis in range(2):
                            low, high = sorted((old_face['uv'][axis], old_face['uv'][axis+2]))
                            self.assertTrue(all(low-1e-8 <= data['uv'][i] <= high+1e-8
                                                for i in (axis, axis+2)))

    def test_added_geometry_uses_opaque_existing_texture_texels(self):
        cache = {}
        for w, model in self.models.items():
            for e in model['elements']:
                if not e['name'].startswith('w153_'):
                    continue
                for face in e['faces'].values():
                    texture = model['textures'][face['texture'][1:]]
                    path = G['ASSETS']/f'textures/{texture.split(":", 1)[1]}.png'
                    if path not in cache:
                        cache[path] = png_rgba(path)
                    for u, v in itertools.product((.1, .5, .9), repeat=2):
                        self.assertEqual(face_pixel(cache[path], face['uv'], u, v)[3], 255)
        tip_color = face_pixel(cache[G['SIGHT_TEXTURE']], [4.25, .25, 4.75, .75])
        self.assertGreater(min(tip_color[:3]), 150)

    def test_segment_geometry_native_xyz_legacy_and_rescale(self):
        # Known forward transforms and slabs, independent of resource contents.
        cube = {'from': [-1, -2, -3], 'to': [1, 2, 3]}
        self.assertAlmostEqual(G['segment_entry'](cube, [0, 0, 10], [0, 0, -10]), .35)
        self.assertIsNone(G['segment_entry'](cube, [2, 0, 10], [2, 0, -10]))
        cube['rotation'] = dict(origin=[0, 0, 0], z=90)
        self.assertIsNotNone(G['segment_entry'](cube, [1.5, 0, 10], [1.5, 0, -10]))
        self.assertIsNone(G['segment_entry'](cube, [0, 1.5, 10], [0, 1.5, -10]))
        for r in (dict(origin=[3, 5, 7], x=31, y=-19, z=76),
                  dict(origin=[3, 5, 7], axis='z', angle=45, rescale=True)):
            cube['rotation'] = r
            p = [.4, .8, 1.2]
            actual = G['local_point'](cube, G['world_point'](cube, p))
            for a, b in zip(actual, p):
                self.assertAlmostEqual(a, b, places=9)
        sheet = dict(cube, rotation={}, **{'from': [-1, -1, 0], 'to': [1, 1, 0]})
        self.assertIsNotNone(G['segment_entry'](sheet, [0, 0, 1], [0, 0, -1]))

    def test_generate_is_deterministic_and_writes_nothing(self):
        with (mock.patch.object(Path, 'write_bytes', side_effect=AssertionError('generate wrote')),
              mock.patch.object(Path, 'mkdir', side_effect=AssertionError('generate mkdir'))):
            first, second = G['generate'](), G['generate']()
        self.assertEqual(first, second)
        for path, data in first.items():
            self.assertIsInstance(path, Path)
            self.assertIsInstance(data, bytes)
            self.assertEqual((ROOT/path).read_bytes(), data)

    def test_generated_path_scope_exact(self):
        expected = {G['ASSETS']/f'models/weapon_sight_w153/{w}_body.json' for w in IDS}
        expected.update((G['MANIFEST'], G['REVIEW']))
        self.assertEqual(set(G['generate']()), expected)
        self.assertEqual(len(expected), 9)

    def test_verify_cli_is_nonwriting(self):
        outputs = G['generate']()
        before = {p: ((ROOT/p).read_bytes(), (ROOT/p).stat().st_mtime_ns) for p in outputs}
        result = subprocess.run(['rtk', 'proxy', sys.executable, '-B', str(SCRIPT), '--verify'],
                                capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('9 outputs verified', result.stdout)
        after = {p: ((ROOT/p).read_bytes(), (ROOT/p).stat().st_mtime_ns) for p in outputs}
        self.assertEqual(before, after)

    def test_verify_detects_stale_bytes_without_repair(self):
        real_read = Path.read_bytes
        stale = ROOT/G['MANIFEST']
        def altered_read(path):
            return b'{}\n' if path == stale else real_read(path)
        with mock.patch.object(Path, 'read_bytes', altered_read), \
             mock.patch.object(Path, 'write_bytes', side_effect=AssertionError('verify wrote')), \
             mock.patch.object(Path, 'mkdir', side_effect=AssertionError('verify mkdir')), \
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as failed:
                G['main'](['--verify'])
        self.assertEqual(failed.exception.code, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
