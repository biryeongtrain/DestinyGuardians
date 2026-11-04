#!/usr/bin/env python3
"""Bounded stdlib checks; no generated pack files are written."""
import ast
import bisect
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT/'scripts/generate_insert_w208_first_in_last_out.py'


def load():
    spec = importlib.util.spec_from_file_location('filo_w208', GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rotate(angles, point):
    # Independent Rx*Ry*Rz point evaluation: apply Z, Y, X in that order.
    x, y, z = point
    ax, ay, az = map(math.radians, angles)
    x, y = math.cos(az)*x-math.sin(az)*y, math.sin(az)*x+math.cos(az)*y
    x, z = math.cos(ay)*x+math.sin(ay)*z, -math.sin(ay)*x+math.cos(ay)*z
    y, z = math.cos(ax)*y-math.sin(ax)*z, math.sin(ax)*y+math.cos(ax)*z
    return [x, y, z]


def point(display, position):
    transformed = rotate(display['rotation'], [(p-8)*s for p, s in zip(position, display['scale'])])
    return [p+t for p, t in zip(transformed, display['translation'])]


class FirstInLastOutMotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = load()
        cls.output = cls.g.generate(root=ROOT)
        cls.source = json.loads((ROOT/cls.g.SOURCE).read_bytes())
        cls.twohand = json.loads((ROOT/cls.g.TWOHAND).read_bytes())['display']
        cls.item = json.loads((ROOT/cls.g.ITEM).read_bytes())

    def model(self, suffix):
        return json.loads(self.output[ROOT/self.g.A/f'models/{self.g.KEY}_{suffix}.json'])

    def test_import_and_generate_are_write_free_and_deterministic(self):
        active = [True]
        def audit(event, args):
            if not active[0]:
                return
            if event == 'open':
                mode, flags = args[1:3]
                if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
                    raise AssertionError('Unexpected write open: '+str(args[0]))
            if event in ('os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.link', 'os.symlink', 'os.truncate', 'os.chmod', 'os.utime'):
                raise AssertionError('Unexpected filesystem mutation: '+event)
        sys.addaudithook(audit)
        try:
            module = load()
            self.assertEqual(module.generate(root=ROOT), self.output)
        finally:
            active[0] = False

    def test_only_new_namespace_absolute_outputs_and_complete_references(self):
        g = self.g
        self.assertEqual(len(self.output), 737)
        allowed = (ROOT/g.A/'models/weapon_insert_w208_first_in_last_out', ROOT/g.A/'items/weapon_insert_w208_first_in_last_out')
        def walk(value):
            if isinstance(value, dict):
                if value.get('type') == 'minecraft:model' and value.get('model', '').startswith('destiny:'+g.KEY):
                    path = ROOT/g.A/'models'/(value['model'].removeprefix('destiny:')+'.json')
                    self.assertIn(path, self.output)
                for v in value.values(): walk(v)
            elif isinstance(value, list):
                for v in value: walk(v)
        for path, raw in self.output.items():
            self.assertTrue(path.is_absolute())
            self.assertTrue(path == ROOT/g.ART/'manifest.json' or any(path.is_relative_to(a) for a in allowed))
            self.assertIsInstance(raw, bytes)
            data = json.loads(raw)
            if path.is_relative_to(allowed[0]):
                if 'parent' in data:
                    parent = ROOT/g.A/'models'/(data['parent'].removeprefix('destiny:')+'.json')
                    self.assertIn(parent, self.output)
            walk(data)

    def test_current_body_and_original_shell_geometry_uv_exact(self):
        self.assertEqual(self.model('body'), self.source)
        self.assertEqual(len(self.source['elements']), 97)
        self.assertEqual(sum(len(e['faces']) for e in self.source['elements']), 582)
        # Execute only the old geometry function, never the W178 generator/imports.
        tree = ast.parse((ROOT/'scripts/generate_insert_w178_first_in_last_out.py').read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'shell_geometry')
        scope = {'copy': copy, 'math': math, 'SHELL_ANCHOR': self.g.SHELL_ANCHOR}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'old-shell-only', 'exec'), scope)
        shell = self.model('shell')
        self.assertEqual(shell, scope['shell_geometry'](self.source))
        self.assertEqual(len(shell['elements']), 12)
        self.assertEqual(self.model('shell_hidden'), {'elements': []})
        self.assertEqual(shell['textures'], self.source['textures'])

    def test_idle_endpoints_and_held_seams_both_grips(self):
        for grip, accepted in [('native', self.source['display']), ('twohand', self.twohand)]:
            self.assertEqual(self.model('initial_00_body_'+grip)['display'], accepted)
            self.assertEqual(self.model('return_60_body_'+grip)['display'], accepted)
            for part in ('body', 'shell'):
                displays = [self.model(f'{phase}_{frame:02}_{part}_{grip}')['display'] for phase, frame in [('initial', 60), ('loop', 0), ('loop', 60), ('return', 0)]]
                for d in displays[1:]: self.assertEqual(d, displays[0])
            for phase, frame in [('initial', 0), ('initial', 60), ('loop', 0), ('loop', 60), ('return', 0), ('return', 60)]:
                self.assertTrue(self.model(f'{phase}_{frame:02}_shell_{grip}')['parent'].endswith('_shell_hidden'))

    def test_61_pose_threshold_graph_matches_java_float_operations(self):
        graph = json.loads(self.output[ROOT/self.g.A/f'items/{self.g.KEY}.json'])['model']
        self.assertEqual(graph['fallback'], self.item['model'])
        self.assertEqual(graph['cases'][0]['when'], list(self.g.FP))
        modes = graph['cases'][0]['model']
        self.assertEqual({c['when'] for c in modes['cases']}, {'ads', 'inspect'})
        for case in modes['cases']: self.assertEqual(case['model'], self.item['model'])
        dispatch = modes['fallback']
        self.assertEqual((dispatch['index'], dispatch['fallback']), (4, self.item['model']))
        entries = dispatch['entries']; values = [e['threshold'] for e in entries]
        self.assertEqual(len(entries), 183)
        self.assertTrue(all(a < b for a, b in zip(values, values[1:])))
        f32 = lambda x: struct.unpack('>f', struct.pack('>f', x))[0]
        for index, entry in enumerate(entries):
            phase, frame = divmod(index, 61)
            expected = f32(phase*2 + f32(frame/60))
            self.assertEqual(entry['threshold'], expected)
            self.assertEqual(bisect.bisect_right(values, expected)-1, index)
            if expected > 0:
                bits = struct.unpack('>I', struct.pack('>f', expected))[0]
                below = struct.unpack('>f', struct.pack('>I', bits-1))[0]
                self.assertEqual(bisect.bisect_right(values, below)-1, index-1)
            condition = entry['model']
            self.assertEqual(condition['index'], 0)
            for flag, grip in [('on_true', 'twohand'), ('on_false', 'native')]:
                self.assertEqual(condition[flag]['models'], [
                    {'type':'minecraft:model', 'model':f'destiny:{self.g.KEY}_{self.g.PHASES[phase]}_{frame:02}_{part}_{grip}'} for part in self.g.PARTS])
        self.assertEqual(bisect.bisect_right(values, -1)-1, -1)
        # Wrapper metadata is also preserved, not just its fallback node.
        wrapped = json.loads(self.output[ROOT/self.g.A/f'items/{self.g.KEY}.json'])
        self.assertEqual({k:v for k,v in wrapped.items() if k != 'model'}, {k:v for k,v in self.item.items() if k != 'model'})

    def test_finite_monotone_bounded_curves_and_moving_knot_velocity(self):
        g = self.g
        all_keys = []
        for phase in g.PHASES:
            all_keys.extend(tuple((k[0], k[channel]) for k in g.KEYS[phase]) for channel in (1, 2))
            all_keys.append(g.SHELL_KEYS[phase])
        moving = 0
        epsilon = 1e-7
        for keys in all_keys:
            times = [k[0] for k in keys]
            for axis in range(3):
                for a, b in zip(keys, keys[1:]):
                    values = [g.interpolate(keys, a[0]+(b[0]-a[0])*i/20)[axis] for i in range(21)]
                    self.assertTrue(all(math.isfinite(v) and min(a[1][axis],b[1][axis])-1e-10 <= v <= max(a[1][axis],b[1][axis])+1e-10 for v in values))
                    direction = b[1][axis]-a[1][axis]
                    self.assertTrue(all((y-x)*direction >= -1e-10 for x,y in zip(values,values[1:])))
                self.assertAlmostEqual((g.interpolate(keys, epsilon)[axis]-keys[0][1][axis])/epsilon, 0, delta=.005)
                self.assertAlmostEqual((keys[-1][1][axis]-g.interpolate(keys,1-epsilon)[axis])/epsilon, 0, delta=.005)
                slopes = g.tangents(times, [k[1][axis] for k in keys])
                for i, (t, value) in enumerate(keys[1:-1], 1):
                    left = (value[axis]-g.interpolate(keys,t-epsilon)[axis])/epsilon
                    right = (g.interpolate(keys,t+epsilon)[axis]-value[axis])/epsilon
                    self.assertAlmostEqual(left, right, delta=.005)
                    self.assertAlmostEqual(left, slopes[i], delta=.005)
                    if abs(slopes[i]) > .1: moving += 1
        self.assertGreater(moving, 10)  # Reject stop-at-every-key smoothstep banks.
        # Lift/held plateau is an intentional rest, not erased by interpolation.
        for p in (.30,.35,.40,.50,.58):
            self.assertEqual(g.sample('initial',p)[:2], (list(g.HOLD[0]),list(g.HOLD[1])))

    def test_visible_timing_and_authored_body_knots_retained(self):
        tree = ast.parse((ROOT/'scripts/generate_insert_w178_first_in_last_out.py').read_text())
        nodes = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('HOLD','KEYS','VISIBLE') for t in n.targets)]
        values = {}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'w178-values','exec'), values)
        self.assertEqual(self.g.KEYS, values['KEYS'])
        self.assertEqual(self.g.VISIBLE, values['VISIBLE'])
        for phase in self.g.PHASES:
            for key in values['KEYS'][phase]:
                sampled = self.g.sample(phase,key[0])
                self.assertEqual(sampled[:2], (list(key[1]), list(key[2])))
                if self.g.shell_visible(phase,key[0]): self.assertEqual(sampled[2], list(key[3]))

    def test_shell_contact_tracks_full_size_part_even_while_hidden(self):
        g = self.g
        for phase in g.PHASES:
            for frame in range(61):
                offset = g.sample(phase,frame/60)[2]
                for grip, accepted in [('native',self.source['display']),('twohand',self.twohand)]:
                    body = self.model(f'{phase}_{frame:02}_body_{grip}')
                    shell = self.model(f'{phase}_{frame:02}_shell_{grip}')
                    self.assertEqual(shell['parent'].endswith('_hidden'), not g.shell_visible(phase,frame/60))
                    for ctx in g.FP:
                        b, s = body['display'][ctx], shell['display'][ctx]
                        self.assertEqual(s['scale'],accepted[ctx]['scale'])
                        self.assertTrue(all(v>0 for v in s['scale']))
                        a = point(b,g.SHELL_ANCHOR);c = point(s,g.SHELL_ANCHOR)
                        delta = rotate(b['rotation'],[v*scale for v,scale in zip(offset,b['scale'])])
                        for actual, expected in zip(c,[v+d for v,d in zip(a,delta)]):
                            self.assertAlmostEqual(actual,expected,places=7)
                    for ctx in set(accepted)-set(g.FP):
                        self.assertEqual(body['display'][ctx],accepted[ctx])
                        self.assertEqual(shell['display'][ctx],accepted[ctx])

    def test_profile_mesh_support_reload_action_and_manifest(self):
        g = self.g
        p = json.loads((ROOT/g.ART/'profile.json').read_bytes())
        self.assertEqual((p['schemaVersion'],p['weapon']),(1,'first_in_last_out'))
        self.assertTrue(p['framing']['keepMeshSupport'])
        self.assertEqual(p['framing']['scale'],.98)
        self.assertEqual(p['framing']['sourceViewRotation'],[0,0,0])
        self.assertLessEqual(set(p['contacts']),{'right','left','reload'})
        self.assertNotIn('cameraDepth',p['framing'])
        self.assertEqual(p['contacts']['reload']['contact'],list(g.SHELL_ANCHOR))
        self.assertEqual(p['contacts']['reload']['partHint'],'shell')
        rig = json.loads((ROOT/g.RIG).read_bytes())
        self.assertIn(p['contacts']['reload']['rigAction'],rig['actions'])
        self.assertFalse(rig['fallback']);self.assertFalse(rig['cameraExported'])
        manifest = json.loads(self.output[ROOT/g.ART/'manifest.json'])
        self.assertEqual(manifest['generatedFiles'],len(self.output))
        self.assertEqual(manifest['packFiles'],len(self.output)-1)
        self.assertEqual(manifest['maxAssembledElements'],109)
        self.assertFalse(manifest['nativeGameplayVerified'])
        self.assertFalse(manifest['mechanicsOrAudioChanged'])
        for path, raw in self.output.items():
            if path != ROOT/g.ART/'manifest.json':
                self.assertEqual(manifest['outputSha256'][str(path.relative_to(ROOT))],g.sha(raw))

    def test_invalid_progress_rejected(self):
        for phase in self.g.PHASES:
            for p in (-.01,1.01,float('nan'),float('inf')):
                with self.assertRaises(ValueError): self.g.sample(phase,p)
        with self.assertRaises(ValueError): self.g.sample('missing',.5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
