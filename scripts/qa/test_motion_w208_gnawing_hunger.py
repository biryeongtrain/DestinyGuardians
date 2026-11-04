#!/usr/bin/env python3
"""Bounded stdlib regression; no generated pack materialization or native claims."""
import ast
from bisect import bisect_right
from collections import Counter
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
import generate_reload_w208_gnawing_hunger as motion


def read(path):
    return json.loads((ROOT/path).read_bytes())


def resolve(node, context='firstperson_righthand', mode='hip', progress=-1, grip=False):
    typ = node['type']
    if typ == 'minecraft:select':
        value = context if node['property'] == 'minecraft:display_context' else mode
        for case in node['cases']:
            when = case['when']
            if value in (when if isinstance(when, list) else [when]):
                return resolve(case['model'], context, mode, progress, grip)
        return resolve(node['fallback'], context, mode, progress, grip)
    if typ == 'minecraft:condition':
        return resolve(node['on_true' if grip else 'on_false'], context, mode, progress, grip)
    if typ == 'minecraft:range_dispatch':
        index = bisect_right([e['threshold'] for e in node['entries']], progress)-1
        selected = node['fallback'] if index < 0 else node['entries'][index]['model']
        return resolve(selected, context, mode, progress, grip)
    return node


class GnawingHungerMotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = motion.generate(root=ROOT)
        cls.source = read(motion.SOURCE)
        cls.twohand = read(motion.TWOHAND)['display']
        cls.item = read(motion.ITEM)
        cls.wrapper = json.loads(cls.output[ROOT/motion.ASSET/f'items/{motion.KEY}.json'])
        cls.mode_graph = cls.wrapper['model']['cases'][0]['model']
        cls.dispatch = cls.mode_graph['fallback']

    def test_import_and_generate_never_write(self):
        def forbidden(*args, **kwargs):
            raise AssertionError('Import/generate attempted a disk mutation')
        import builtins
        real_open, real_os_open = builtins.open, os.open
        def guarded_open(file, mode='r', *args, **kwargs):
            if any(flag in mode for flag in 'wax+'):
                forbidden()
            return real_open(file, mode, *args, **kwargs)
        def guarded_os_open(path, flags, *args, **kwargs):
            if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                forbidden()
            return real_os_open(path, flags, *args, **kwargs)
        spec = importlib.util.spec_from_file_location('w208_pure_import', Path(motion.__file__))
        module = importlib.util.module_from_spec(spec)
        with patch('builtins.open', guarded_open), patch('os.open', guarded_os_open), \
             patch.object(Path, 'write_bytes', forbidden), patch.object(Path, 'write_text', forbidden), \
             patch.object(Path, 'mkdir', forbidden), patch.object(Path, 'touch', forbidden), \
             patch('os.mkdir', forbidden), patch('os.replace', forbidden), patch('os.rename', forbidden), \
             patch('os.remove', forbidden), patch('os.unlink', forbidden):
            spec.loader.exec_module(module)
            self.assertEqual(module.generate(root=ROOT), self.output)
        imports = [node for node in ast.walk(ast.parse(Path(motion.__file__).read_text()))
                   if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any(getattr(node, 'module', '') in ('PIL', 'numpy') or
                             any(n.name in ('PIL', 'numpy') for n in node.names) for node in imports))

    def test_output_ownership_references_and_finite_json(self):
        expected = {ROOT/motion.MANIFEST, ROOT/motion.ASSET/f'items/{motion.KEY}.json'}
        expected.update(ROOT/motion.ASSET/f'models/{motion.KEY}_{part}.json' for part in motion.PARTS)
        expected.update(ROOT/motion.ASSET/f'models/{motion.KEY}_{i:02}_{part}_{grip}.json'
                        for i in range(61) for part in motion.PARTS for grip in ('native', 'twohand'))
        self.assertEqual(set(self.output), expected)
        self.assertEqual(len(self.output), 248)
        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in ('model', 'parent') and isinstance(child, str) and child.startswith('destiny:'+motion.KEY):
                        self.assertIn(ROOT/motion.ASSET/f"models/{child.split(':',1)[1]}.json", self.output)
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
            elif isinstance(value, float):
                self.assertTrue(math.isfinite(value))
        for path, raw in self.output.items():
            self.assertTrue(path.is_absolute())
            self.assertIsInstance(raw, bytes)
            walk(json.loads(raw))
        manifest = json.loads(self.output[ROOT/motion.MANIFEST])
        self.assertEqual(len(manifest['outputSha256']), 247)
        for path, digest in manifest['outputSha256'].items():
            self.assertEqual(digest, motion.sha(self.output[ROOT/path]))

    def test_exact_partition_and_uv_with_no_inherited_idle_flash(self):
        parts = {part: json.loads(self.output[ROOT/motion.ASSET/f'models/{motion.KEY}_{part}.json'])
                 for part in motion.PARTS}
        packed = lambda e: json.dumps(e, sort_keys=True)
        self.assertEqual(Counter(map(packed, self.source['elements'])),
                         Counter(packed(e) for part in parts.values() for e in part['elements']))
        self.assertEqual([len(parts[p]['elements']) for p in motion.PARTS], [109, 5])
        self.assertEqual([e['name'] for e in parts['moving']['elements']],
                         ['magazine/'+name for name in motion.NAMES])
        for part in parts.values():
            self.assertEqual(part['textures'], self.source['textures'])
            self.assertNotIn('display', part)
        self.assertEqual(sum(len(e['faces']) for p in parts.values() for e in p['elements']), 684)

    def test_endpoint_restoration_and_non_fp_displays(self):
        for frame in range(61):
            for grip in ('native', 'twohand'):
                accepted = self.source['display'] if grip == 'native' else self.twohand
                for part in motion.PARTS:
                    leaf = json.loads(self.output[ROOT/motion.ASSET/f'models/{motion.KEY}_{frame:02}_{part}_{grip}.json'])
                    display = leaf['display']
                    if frame in (0, 60):
                        self.assertEqual(display, accepted)
                    for context in set(accepted)-set(motion.FP):
                        self.assertEqual(display[context], accepted[context])

    def test_float32_dispatch_and_exact_fallbacks(self):
        entries = self.dispatch['entries']
        self.assertEqual(len(entries), 61)
        self.assertEqual(self.dispatch['index'], 1)
        self.assertEqual([e['threshold'] for e in entries],
                         [struct.unpack('!f', struct.pack('!f', i/60))[0] for i in range(61)])
        self.assertEqual(entries[0]['model'], self.item['model'])
        self.assertEqual(entries[-1]['model'], self.item['model'])
        self.assertEqual(self.dispatch['fallback'], self.item['model'])
        self.assertEqual(self.wrapper['model']['fallback'], self.item['model'])
        self.assertEqual({k:v for k,v in self.wrapper.items() if k != 'model'},
                         {k:v for k,v in self.item.items() if k != 'model'})
        for ctx in ('gui', 'ground', 'fixed', 'head', 'thirdperson_righthand', 'thirdperson_lefthand'):
            for mode in ('hip', 'ads', 'inspect'):
                for grip in (False, True):
                    self.assertEqual(resolve(self.wrapper['model'], ctx, mode, .5, grip),
                                     resolve(self.item['model'], ctx, mode, .5, grip))
        for ctx in motion.FP:
            for grip in (False, True):
                for p in (-1, 0, 1):
                    self.assertEqual(resolve(self.wrapper['model'], ctx, 'hip', p, grip),
                                     resolve(self.item['model'], ctx, 'hip', p, grip))
                for mode in ('ads', 'inspect'):
                    self.assertEqual(resolve(self.wrapper['model'], ctx, mode, .5, grip),
                                     resolve(self.item['model'], ctx, mode, .5, grip))
                for i in range(1, 60):
                    leaf = resolve(self.wrapper['model'], ctx, 'hip', motion.float32(i/60), grip)
                    self.assertEqual(leaf['type'], 'minecraft:composite')
                    suffix = 'twohand' if grip else 'native'
                    self.assertEqual([n['model'] for n in leaf['models']],
                                     [f'destiny:{motion.KEY}_{i:02}_{p}_{suffix}' for p in motion.PARTS])

    def test_w164_timing_and_authored_knots_retained(self):
        tree = ast.parse((ROOT/'scripts/generate_reload_w164_gnawing_hunger.py').read_text())
        constants = {n.targets[0].id:ast.literal_eval(n.value) for n in tree.body
                     if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                     and n.targets[0].id in ('KEYS', 'MOVING', 'GRIP')}
        self.assertEqual(motion.KEYS, constants['KEYS'])
        self.assertEqual(motion.MOVING, constants['MOVING'])
        self.assertEqual(motion.GRIP, constants['GRIP'])
        for key in motion.KEYS:
            self.assertEqual(motion.sample(key[0]), tuple(list(v) for v in key[1:]))

    def test_curve_finite_monotone_and_bounded_per_authored_span(self):
        for a,b in zip(motion.KEYS, motion.KEYS[1:]):
            samples = [motion.sample(a[0]+(b[0]-a[0])*i/40) for i in range(41)]
            for channel in range(3):
                for axis in range(3):
                    lo,hi = sorted((a[channel+1][axis], b[channel+1][axis]))
                    values = [s[channel][axis] for s in samples]
                    self.assertTrue(all(math.isfinite(v) and lo-1e-10 <= v <= hi+1e-10 for v in values))
                    sign = 1 if b[channel+1][axis] >= a[channel+1][axis] else -1
                    self.assertTrue(all(sign*(v-u) >= -1e-10 for u,v in zip(values, values[1:])))
        for invalid in (-.001, 1.001, math.inf, -math.inf, math.nan):
            with self.assertRaises(ValueError):
                motion.sample(invalid)

    def test_c1_velocities_keep_moving_knots_and_settle_endpoints(self):
        times = [k[0] for k in motion.KEYS]
        eps = 1e-7
        moving = 0
        for channel in range(3):
            for axis in range(3):
                values = [k[channel+1][axis] for k in motion.KEYS]
                slopes = motion.tangents(times, values)
                self.assertEqual((slopes[0], slopes[-1]), (0, 0))
                for index, p in enumerate(times):
                    value = motion.sample(p)[channel][axis]
                    if p > 0:
                        before = (value-motion.sample(p-eps)[channel][axis])/eps
                        self.assertAlmostEqual(before, slopes[index], delta=.005)
                    if p < 1:
                        after = (motion.sample(p+eps)[channel][axis]-value)/eps
                        self.assertAlmostEqual(after, slopes[index], delta=.005)
                    if 0 < index < len(times)-1 and values[index-1] < values[index] < values[index+1]:
                        self.assertGreater(slopes[index], 0)
                        moving += 1
                for p in (eps, 1-eps):
                    endpoint = 0 if p < .5 else 1
                    velocity = (motion.sample(p)[channel][axis]-motion.sample(endpoint)[channel][axis])/eps
                    self.assertLess(abs(velocity), .005)
        self.assertGreater(moving, 5)

    def test_meaningful_exchange_and_seated_holds(self):
        for p in (.38, .4, .45, .49, .5):
            self.assertEqual(motion.sample(p), motion.sample(.38))
        for p in (0, .05, .12, .74, .8, .82, .9, 1):
            self.assertEqual(motion.sample(p)[2], [0,0,0])
        self.assertEqual(motion.sample(.5)[2], [-1.2,-6,.5])

    def test_grip_pivot_and_detached_magazine_rigid_transform(self):
        pivot = [v-8 for v in motion.GRIP]
        for p in (.07, .2, .35, .45, .6, .7, .9):
            _, shift, offset = motion.sample(p)
            for grip in ('native', 'twohand'):
                body = motion.pose_display(self.source['display'], self.twohand, p, 'body', grip)
                magazine = motion.pose_display(self.source['display'], self.twohand, p, 'moving', grip)
                for ctx in motion.FP:
                    b,m = body[ctx],magazine[ctx]
                    self.assertEqual(b['rotation'], m['rotation'])
                    idle = self.source['display'][ctx]
                    scale = idle['scale'][0]
                    q = motion.xyz(b['rotation'])
                    separation = motion.vec(q, [scale*v for v in offset])
                    for i in range(3):
                        self.assertAlmostEqual(m['translation'][i]-b['translation'][i], separation[i], places=7)
                    actual = [a+t for a,t in zip(motion.vec(q, [scale*v for v in pivot]), b['translation'])]
                    target = [a+t+s for a,t,s in zip(motion.vec(motion.xyz(idle['rotation']),
                              [scale*v for v in pivot]), idle['translation'], shift)]
                    if grip == 'twohand':
                        comp = motion.mul(motion.xyz(self.twohand[ctx]['rotation']),
                                          motion.transpose(motion.xyz(idle['rotation'])))
                        target = [a+t-b for a,t,b in zip(motion.vec(comp,target),
                                  self.twohand[ctx]['translation'], motion.vec(comp,idle['translation']))]
                    for a,b in zip(actual,target):
                        self.assertAlmostEqual(a,b,places=7)

    def test_profile_mesh_anchors_rig_metadata_and_conservative_framing(self):
        profile = read(motion.PROFILE)
        self.assertEqual(profile['schemaVersion'], 1)
        self.assertEqual(profile['weapon'], 'gnawing_hunger')
        framing = profile['framing']
        self.assertIs(framing['keepMeshSupport'], True)
        self.assertEqual(framing['scale'], .98)
        self.assertLessEqual(max(abs(v) for v in framing['translation']), 1.5)
        self.assertLessEqual(max(abs(v) for v in framing['rotation']), 3)
        self.assertLessEqual(max(abs(v) for v in framing['sourceViewRotation']), 5)
        self.assertFalse(set(profile['contacts'])-{'right','left','reload'})
        base = read(Path('art/weapons/w201/contacts.json'))['weapons']['gnawing_hunger']
        cfg = copy.deepcopy(base)
        for role, override in profile['contacts'].items():
            cfg[role].update(override)
        self.assertEqual(cfg['right'], base['right'])
        self.assertEqual(cfg['left'], base['left'])
        self.assertEqual(cfg['reload']['contact'], [7.4,6.7,3.35])
        self.assertIn(cfg['reload']['partHint'], motion.PARTS)
        data = read(Path('art/weapons/w205/rigs/auto_rifle_943c13a2.json'))
        self.assertIn('gnawing_hunger', data['weapons'])
        self.assertFalse(data['fallback'])
        self.assertFalse(data['cameraExported'])
        self.assertEqual(cfg['reload']['rigAction'], '80A8A395')
        for tag in ('80A8A395','80A8A38C','80A8A38A'):
            self.assertEqual(data['actions'][tag]['sourceNames'], ['reload_full','reload_empty'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
