#!/usr/bin/env python3
"""Bounded stdlib W208 Austringer checks, entirely against in-memory outputs."""
import ast
import bisect
import builtins
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import runpy
import struct
import sys
import unittest
from contextlib import ExitStack
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT/'scripts/generate_reload_w208_austringer.py'


def f32(v):
    return struct.unpack('!f', struct.pack('!f', v))[0]


def rotate(angles, point):
    """Independent Rx Ry Rz point oracle, applying Z then Y then X."""
    x, y, z = map(math.radians, angles)
    a, b, c = point
    a, b = a*math.cos(z)-b*math.sin(z), a*math.sin(z)+b*math.cos(z)
    a, c = a*math.cos(y)+c*math.sin(y), -a*math.sin(y)+c*math.cos(y)
    b, c = b*math.cos(x)-c*math.sin(x), b*math.sin(x)+c*math.cos(x)
    return [a, b, c]


def add(a, b):
    return [x+y for x, y in zip(a, b)]


def sub(a, b):
    return [x-y for x, y in zip(a, b)]


def apply_display(display, point):
    return add(display['translation'], rotate(display['rotation'],
               [s*(x-8) for s, x in zip(display['scale'], point)]))


def readonly_open(original):
    def guarded(file, mode='r', *args, **kwargs):
        if any(c in mode for c in 'wax+'):
            raise AssertionError('Unexpected disk write: ' + str(file))
        return original(file, mode, *args, **kwargs)
    return guarded


def evaluate(node, context, progress, mode, flag):
    typ = node['type']
    if typ == 'minecraft:select':
        value = context if node['property'] == 'minecraft:display_context' else mode
        for case in node['cases']:
            if value in (case['when'] if isinstance(case['when'], list) else [case['when']]):
                return evaluate(case['model'], context, progress, mode, flag)
        return evaluate(node['fallback'], context, progress, mode, flag)
    if typ == 'minecraft:condition':
        return evaluate(node['on_true' if flag else 'on_false'], context, progress, mode, flag)
    if typ == 'minecraft:range_dispatch':
        index = bisect.bisect_right([e['threshold'] for e in node['entries']], progress)-1
        child = node['entries'][index]['model'] if index >= 0 else node['fallback']
        return evaluate(child, context, progress, mode, flag)
    return node


class AustringerMotionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Guard import AND generate, including open variants and Path/os mutators.
        with ExitStack() as stack:
            stack.enter_context(patch('builtins.open', readonly_open(builtins.open)))
            stack.enter_context(patch('io.open', readonly_open(io.open)))
            real_os_open = os.open
            def guarded_os_open(path, flags, *args, **kwargs):
                if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                    raise AssertionError('Unexpected os.open write: ' + str(path))
                return real_os_open(path, flags, *args, **kwargs)
            stack.enter_context(patch('os.open', guarded_os_open))
            for name in ('write_bytes', 'write_text', 'mkdir', 'touch', 'unlink', 'rename', 'replace', 'rmdir'):
                stack.enter_context(patch.object(Path, name, side_effect=AssertionError('Disk mutation: '+name)))
            for name in ('mkdir', 'makedirs', 'remove', 'unlink', 'rename', 'replace', 'rmdir'):
                stack.enter_context(patch.object(os, name, side_effect=AssertionError('Disk mutation: '+name)))
            cls.g = runpy.run_path(str(GENERATOR))
            cls.output = cls.g['generate'](root=ROOT)
            cls.repeat = cls.g['generate'](root=ROOT)
        cls.a, cls.key = cls.g['ASSET'], cls.g['KEY']
        cls.source = json.loads((ROOT/cls.g['SOURCE']).read_bytes())
        cls.twohand = json.loads((ROOT/cls.g['TWOHAND']).read_bytes())['display']
        cls.canonical = json.loads((ROOT/cls.g['ITEM']).read_bytes())

    def read(self, path):
        return json.loads(self.output[ROOT/path])

    def child(self, frame, part, grip):
        return self.read(self.a/f'models/{self.key}_{frame:02}_{part}_{grip}.json')

    def test_01_import_generate_read_only_deterministic_and_owned(self):
        self.assertEqual(self.output, self.repeat)
        self.assertEqual(248, len(self.output))
        self.assertEqual(247, sum(p.is_relative_to(ROOT/self.a) for p in self.output))
        allowed = [ROOT/self.a/f'{kind}/weapon_reload_w208_austringer' for kind in ('models', 'items')]
        for p, raw in self.output.items():
            self.assertTrue(p.is_absolute())
            self.assertIsInstance(raw, bytes)
            self.assertTrue(p == ROOT/self.g['MANIFEST'] or any(p.is_relative_to(d) for d in allowed), p)
            json.loads(raw)

    def test_02_current_geometry_partition_and_default_uv(self):
        body = self.read(self.a/f'models/{self.key}_body.json')
        moving = self.read(self.a/f'models/{self.key}_moving.json')
        self.assertEqual(self.source['elements'][32:44], moving['elements'])
        self.assertEqual(self.source['elements'][:32]+self.source['elements'][44:], body['elements'])
        self.assertEqual((114, 12), (len(body['elements']), len(moving['elements'])))
        for part in (body, moving):
            self.assertEqual(self.source['textures'], part['textures'])
        self.assertEqual(756, sum(len(e['faces']) for e in self.source['elements']))
        design = json.loads((ROOT/'art/weapons/w123/austringer/design.json').read_bytes())
        self.assertEqual([p['geometry'] for p in design['parts']], self.source['elements'])

    def test_03_endpoint_idle_display_restoration_both_grips(self):
        for grip, accepted in [('native', self.source['display']), ('twohand', self.twohand)]:
            for frame in (0, 60):
                for part in ('body', 'moving'):
                    self.assertEqual(accepted, self.child(frame, part, grip)['display'])

    def test_04_threshold_graph_references_and_exact_fallbacks(self):
        wrapper = self.read(self.a/f'items/{self.key}.json')
        graph = wrapper['model']; dispatch = graph['cases'][0]['model']
        self.assertEqual(self.canonical['model'], graph['fallback'])
        self.assertEqual(self.canonical['model'], dispatch['fallback'])
        self.assertEqual(1, dispatch['index'])
        self.assertEqual(list(self.g['FP']), graph['cases'][0]['when'])
        entries = dispatch['entries']; self.assertEqual(61, len(entries))
        self.assertEqual([f32(i/60) for i in range(61)], [e['threshold'] for e in entries])
        for i, entry in enumerate(entries):
            self.assertEqual(i, bisect.bisect_right([e['threshold'] for e in entries], f32(i/60))-1)
            if i in (0, 60):
                self.assertEqual(self.canonical['model'], entry['model']); continue
            for branch, grip in [('on_true', 'twohand'), ('on_false', 'native')]:
                refs = entry['model'][branch]['models']
                for part, ref in zip(('body', 'moving'), refs):
                    self.assertEqual(f'destiny:{self.key}_{i:02}_{part}_{grip}', ref['model'])
                    self.assertEqual(f'destiny:{self.key}_{part}', self.child(i, part, grip)['parent'])
        for context in ('gui', 'ground', 'fixed', 'head', 'thirdperson_righthand', 'thirdperson_lefthand', *self.g['FP']):
            for mode in ('hip', 'ads', 'inspect'):
                for flag in (False, True):
                    for progress in (-1, 0, 1) if context in self.g['FP'] else (-1, .35, 1):
                        self.assertEqual(evaluate(self.canonical['model'], context, progress, mode, flag),
                                         evaluate(graph, context, progress, mode, flag))
        self.assertEqual(self.canonical['hand_animation_on_swap'], wrapper['hand_animation_on_swap'])

    def test_05_authored_key_times_and_values_preserved(self):
        tree = ast.parse((ROOT/'scripts/generate_reload_w168_austringer.py').read_text())
        old = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'KEYS' for t in n.targets))
        self.assertEqual(old, self.g['KEYS'])
        for key in old:
            self.assertEqual(tuple(list(v) for v in key[1:]), self.g['sample'](key[0]))

    def test_06_curve_finite_monotone_bounded_per_authored_span(self):
        for a, b in zip(self.g['KEYS'], self.g['KEYS'][1:]):
            samples = [self.g['sample'](a[0]+(b[0]-a[0])*i/24) for i in range(25)]
            for channel in range(3):
                for axis in range(3):
                    values = [s[channel][axis] for s in samples]
                    lo, hi = sorted((a[channel+1][axis], b[channel+1][axis]))
                    self.assertTrue(all(math.isfinite(v) and lo-1e-10 <= v <= hi+1e-10 for v in values))
                    direction = 1 if values[-1] >= values[0] else -1
                    self.assertTrue(all(direction*(y-x) >= -1e-10 for x, y in zip(values, values[1:])))
        for bad in (-.1, 1.1, float('inf'), float('nan')):
            with self.assertRaises(ValueError): self.g['sample'](bad)

    def test_07_velocity_continuity_moving_knots_and_settled_endpoints(self):
        eps = 1e-7; sample = self.g['sample']
        for key in self.g['KEYS'][1:-1]:
            p = key[0]; left, center, right = sample(p-eps), sample(p), sample(p+eps)
            for channel in range(3):
                for axis in range(3):
                    before = (center[channel][axis]-left[channel][axis])/eps
                    after = (right[channel][axis]-center[channel][axis])/eps
                    self.assertAlmostEqual(before, after, delta=.01)
        # Smoothstep per segment would stop at both these moving x-angle knots.
        for p in (.09, .20, .50, .62, .76):
            self.assertGreater(abs((sample(p+eps)[0][0]-sample(p-eps)[0][0])/(2*eps)), 1)
        for p, q in ((0, eps), (1, 1-eps)):
            for a, b in zip(sample(p), sample(q)):
                for x, y in zip(a, b): self.assertLess(abs((y-x)/eps), .01)

    def test_08_meaningful_holds_and_cylinder_closed_seam(self):
        for p in (.20, .29, .35, .50, .62, .76):
            self.assertEqual([0, 0, 78], self.g['sample'](p)[2])
        for p in (.29, .35, .45, .50):
            self.assertEqual([.25, -.20, -.25], self.g['sample'](p)[1])
        for frame in range(54, 61):
            for grip in ('native', 'twohand'):
                self.assertEqual(self.child(frame, 'body', grip)['display'],
                                 self.child(frame, 'moving', grip)['display'])
        # Actual rotated solid corners clear the fixed lower frame while open.
        xs = []
        cylinder = self.g['sample'](.35)[2]
        hinge = self.g['HINGE']
        for element in self.source['elements'][32:44]:
            r = element['rotation']; angles = [r.get(axis, 0) for axis in 'xyz']
            for x in (element['from'][0], element['to'][0]):
                for y in (element['from'][1], element['to'][1]):
                    for z in (element['from'][2], element['to'][2]):
                        point = add(rotate(angles, sub([x, y, z], r['origin'])), r['origin'])
                        xs.append(add(rotate(cylinder, sub(point, hinge)), hinge)[0])
        self.assertGreater(self.source['elements'][44]['from'][0]-max(xs), .10)

    def test_09_rigid_cylinder_hinge_and_carrier_point_oracle(self):
        for frame in (1, 6, 17, 28, 40, 47, 52, 57, 59):
            angles, shift, cylinder = self.g['sample'](frame/60)
            for grip in ('native', 'twohand'):
                for context in self.g['FP']:
                    idle = self.source['display'][context]
                    # Build inverse source rotation by transposed basis columns.
                    basis = [rotate(idle['rotation'], [float(j == i) for j in range(3)]) for i in range(3)]
                    def carrier(point):
                        if grip == 'native': return point
                        relative = sub(point, idle['translation'])
                        unrotated = [sum(a*b for a, b in zip(axis, relative)) for axis in basis]
                        return add(self.twohand[context]['translation'], rotate(self.twohand[context]['rotation'], unrotated))
                    for part in ('body', 'moving'):
                        display = self.child(frame, part, grip)['display'][context]
                        for point in (self.g['HINGE'], self.g['GRIP'], [8, 12.43, 4.34], [6.85, 12.35, 4.8]):
                            posed = add(rotate(cylinder, sub(point, self.g['HINGE'])), self.g['HINGE']) if part == 'moving' else point
                            posed = add(rotate(angles, sub(posed, self.g['GRIP'])), self.g['GRIP'])
                            expected = carrier(add(apply_display(idle, posed), shift))
                            actual = apply_display(display, point)
                            for x, y in zip(actual, expected): self.assertAlmostEqual(x, y, delta=4e-9)
                        self.assertEqual(idle['scale'], display['scale'])
            for grip, accepted in [('native', self.source['display']), ('twohand', self.twohand)]:
                for part in ('body', 'moving'):
                    for ctx in set(accepted)-set(self.g['FP']):
                        self.assertEqual(accepted[ctx], self.child(frame, part, grip)['display'][ctx])

    def test_10_profile_mesh_contacts_source_rig_and_no_stretch(self):
        profile = json.loads((ROOT/self.g['PROFILE']).read_bytes())
        base = json.loads((ROOT/'art/weapons/w201/contacts.json').read_bytes())['weapons']['austringer']
        self.assertEqual(1, profile['schemaVersion']); self.assertEqual('austringer', profile['weapon'])
        framing = profile['framing']
        self.assertTrue(framing['keepMeshSupport']); self.assertFalse(framing['hideSupportAtRest']); self.assertTrue(framing['meshArmDirections'])
        self.assertEqual(.98, framing['scale'])
        self.assertFalse({'armLength', 'armExtension', 'cameraDepth'} & set(framing))
        self.assertTrue(set(profile['contacts']) <= {'right', 'left', 'reload'})
        reload = {**base['reload'], **profile['contacts']['reload']}
        self.assertEqual('moving', reload['partHint']); self.assertEqual('80A8A53D', reload['rigAction'])
        self.assertEqual(base['reload']['contact'], reload['contact'])
        rig = json.loads((ROOT/self.g['RIG']).read_bytes())
        self.assertFalse(rig['fallback']); self.assertFalse(rig['cameraExported'])
        self.assertIn('austringer', rig['weapons']); self.assertEqual(61, len(rig['actions']['80A8A53D']['frames']))
        self.assertEqual('80A8A575', rig['idle']); self.assertEqual('80A8A579', rig['ads'])
        # Shared affine framing keeps both palm-to-weapon offsets attached.
        helper = runpy.run_path(str(ROOT/'scripts/first_person_framing_w205.py'))
        original = self.source['display']
        calibrated = helper['display'](original, framing, 1, self.g['xyz'], self.g['mul'], self.g['euler'], self.g['vec'])
        for context in self.g['FP']:
            side = -1 if context.endswith('lefthand') else 1
            angles = list(framing['rotation']); angles[1] *= side; angles[2] *= side
            shift = list(framing['translation']); shift[0] *= side
            for point in (base['right']['position'], base['left']['position'], reload['contact']):
                expected = add(rotate(angles, [v*.98 for v in apply_display(original[context], point)]), shift)
                for x, y in zip(apply_display(calibrated[context], point), expected):
                    self.assertAlmostEqual(x, y, delta=2e-8)
        self.assertEqual(original, helper['display'](original, framing, 0, self.g['xyz'], self.g['mul'], self.g['euler'], self.g['vec']))

    def test_11_manifest_hashes_counts_and_honest_limits(self):
        manifest = self.read(self.g['MANIFEST'])
        self.assertEqual({'body': 114, 'moving': 12}, manifest['partCubes'])
        self.assertEqual(126, manifest['maxAssembledElements'])
        self.assertEqual(12, manifest['evidence']['sourceFrameCount'])
        self.assertFalse(manifest['nativeGameplayVerified'])
        self.assertFalse(manifest['gameplayTimingChanged']); self.assertFalse(manifest['ammoOrAudioChanged'])
        self.assertEqual(247, len(manifest['outputSha256']))
        for path, digest in manifest['inputSha256'].items():
            self.assertEqual(digest, hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), path)
        for path, digest in manifest['outputSha256'].items():
            self.assertEqual(digest, hashlib.sha256(self.output[ROOT/path]).hexdigest(), path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
