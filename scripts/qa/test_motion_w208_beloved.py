#!/usr/bin/env python3
"""Bounded W208 Beloved tests; stdlib only, no asset/bytecode writes."""
import ast
from collections import Counter
from contextlib import ExitStack, contextmanager
import copy
import io
import json
import math
import os
from pathlib import Path
import runpy
import struct
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / 'scripts/generate_reload_w208_beloved.py'
g = runpy.run_path(str(GENERATOR))


def read_json(path):
    return json.loads(path.read_bytes())


@contextmanager
def forbid_writes():
    """Reject real write attempts, including pathlib/io and low-level os APIs."""
    def guard_open(real):
        def opened(file, mode='r', *args, **kwargs):
            if any(flag in str(mode) for flag in 'wax+'):
                raise AssertionError('Disk write attempted: ' + str(file))
            return real(file, mode, *args, **kwargs)
        return opened
    real_os_open = os.open
    def os_open(path, flags, *args, **kwargs):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise AssertionError('Low-level disk write attempted: ' + str(path))
        return real_os_open(path, flags, *args, **kwargs)
    with ExitStack() as stack:
        stack.enter_context(patch('builtins.open', guard_open(open)))
        stack.enter_context(patch('io.open', guard_open(io.open)))
        stack.enter_context(patch('os.open', os_open))
        for name in ('mkdir', 'makedirs', 'remove', 'unlink', 'rename', 'replace', 'rmdir', 'chmod', 'utime'):
            stack.enter_context(patch('os.' + name, side_effect=AssertionError('Mutation attempted: ' + name)))
        yield


def select(node, context='firstperson_righthand', mode='hip', grip=False, progress=.5):
    """Small independent evaluator of only the emitted Minecraft item node types."""
    kind = node['type']
    if kind == 'minecraft:select':
        value = context if node['property'] == 'minecraft:display_context' else mode
        for case in node.get('cases', []):
            when = case['when']
            if value in (when if isinstance(when, list) else [when]):
                return select(case['model'], context, mode, grip, progress)
        return select(node['fallback'], context, mode, grip, progress)
    if kind == 'minecraft:condition':
        return select(node['on_true' if grip else 'on_false'], context, mode, grip, progress)
    if kind == 'minecraft:range_dispatch':
        chosen = node['fallback']
        for entry in node['entries']:
            if progress >= entry['threshold']:
                chosen = entry['model']
        return select(chosen, context, mode, grip, progress)
    if kind == 'minecraft:composite':
        return [select(n, context, mode, grip, progress) for n in node['models']]
    if kind == 'minecraft:model':
        return node['model']
    raise AssertionError('Unsupported model graph node: ' + kind)


class BelovedMotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with forbid_writes():
            cls.outputs = g['generate'](root=ROOT)
        cls.asset = ROOT / g['ASSET']
        cls.wrapper = read_json_bytes(cls.outputs[cls.asset / ('items/' + g['KEY'] + '.json')])
        cls.fp = cls.wrapper['model']['cases'][0]['model']
        cls.dispatch = cls.fp['fallback']
        cls.source = read_json(ROOT / g['SURFACE'] / 'beloved.json')
        cls.twohand = read_json(ROOT / g['TWOHAND'])['display']
        cls.item = read_json(ROOT / g['ITEM'])

    def test_import_generate_have_no_disk_side_effects_and_are_deterministic(self):
        with forbid_writes():
            imported = runpy.run_path(str(GENERATOR))
            actual = imported['generate'](root=ROOT)
            default = imported['generate']()
        self.assertEqual(actual, self.outputs)
        self.assertEqual(actual, default)
        # Ensure the guard catches pathlib writes rather than silently missing them.
        with self.assertRaisesRegex(AssertionError, 'Disk write'):
            with forbid_writes():
                Path('/private/tmp/w208-beloved-should-never-exist').write_bytes(b'no')

    def test_new_namespace_absolute_paths_counts_and_manifest(self):
        self.assertEqual(len(self.outputs), 248)  # 2 geometries, 244 poses, item, manifest
        allowed = [self.asset / 'models/weapon_reload_w208_beloved',
                   self.asset / 'items/weapon_reload_w208_beloved']
        for path, raw in self.outputs.items():
            self.assertTrue(path.is_absolute())
            self.assertIsInstance(raw, bytes)
            self.assertTrue(path == ROOT/g['MANIFEST'] or any(path.is_relative_to(a) for a in allowed))
            read_json_bytes(raw)  # finite, strict JSON
        manifest = read_json_bytes(self.outputs[ROOT/g['MANIFEST']])
        self.assertEqual(manifest['sourceCubes'], 99)
        self.assertEqual(manifest['partCubes'], {'body':94, 'magazine':5})
        self.assertEqual(manifest['outputCount'], len(self.outputs))
        self.assertFalse(manifest['nativeGameplayVerified'])
        for path, digest in manifest['outputSha256'].items():
            self.assertEqual(g['sha'](self.outputs[ROOT/path]), digest)

    def test_current_remodeled_geometry_partition_and_all_uv_exact(self):
        packed = lambda e: json.dumps(e, sort_keys=True, separators=(',', ':'))
        joined = []
        for part, count in [('body',94), ('magazine',5)]:
            current = read_json(ROOT/g['SURFACE']/('beloved_' + part + '.json'))
            expected = {k:v for k,v in current.items() if k != 'display'}
            emitted = read_json_bytes(self.outputs[self.asset/('models/' + g['KEY'] + '_' + part + '.json')])
            self.assertEqual(emitted, expected)
            self.assertEqual(len(emitted['elements']), count)
            for element in emitted['elements']:
                self.assertEqual(len(element['faces']), 6)
                for face in element['faces'].values():
                    self.assertEqual(len(face['uv']), 4)
            joined += emitted['elements']
        self.assertEqual(Counter(map(packed, joined)), Counter(map(packed, self.source['elements'])))
        self.assertEqual(len(joined), 99)

    def test_61_runtime_float_thresholds_and_entire_pose_graph_resolve(self):
        entries = self.dispatch['entries']
        self.assertEqual(len(entries), 61)
        self.assertEqual((self.dispatch['property'],self.dispatch['index']), ('minecraft:custom_model_data',1))
        prior = -1
        for i, entry in enumerate(entries):
            expected = struct.unpack('!f', struct.pack('!f', i/60))[0]
            self.assertEqual(entry['threshold'], expected)
            self.assertGreater(entry['threshold'], prior)
            prior = entry['threshold']
            for grip in (False, True):
                selected = select(self.wrapper['model'], grip=grip, progress=expected)
                if i in (0, 60):
                    self.assertEqual(selected, select(self.item['model'], grip=grip))
                else:
                    self.assertEqual(selected, ['destiny:' + g['KEY'] + f'_{i:02}_{part}_' + ('twohand' if grip else 'native') for part in g['PARTS']])
                    # Threshold is inclusive; its immediately previous float64 remains on prior pose.
                    self.assertEqual(select(self.dispatch, grip=grip, progress=math.nextafter(expected,-math.inf)),
                                     select(entries[i-1]['model'], grip=grip))
        for i in range(61):
            for part in g['PARTS']:
                for grip in ('native','twohand'):
                    pose = read_json_bytes(self.outputs[self.asset/('models/'+g['KEY']+f'_{i:02}_{part}_{grip}.json')])
                    parent = self.asset/('models/'+pose['parent'].split(':',1)[1]+'.json')
                    self.assertIn(parent,self.outputs)
                    for display in pose['display'].values():
                        for values in display.values():
                            self.assertTrue(all(math.isfinite(v) for v in values))

    def test_both_grips_endpoint_and_non_fp_display_restoration(self):
        for i in range(61):
            for part in g['PARTS']:
                for grip, accepted in [('native',self.source['display']),('twohand',self.twohand)]:
                    pose = read_json_bytes(self.outputs[self.asset/('models/'+g['KEY']+f'_{i:02}_{part}_{grip}.json')])
                    if i in (0,60):
                        self.assertEqual(pose['display'], accepted)
                    for context in set(accepted)-set(g['FP']):
                        self.assertEqual(pose['display'][context], accepted[context])
                    for context in g['FP']:
                        self.assertEqual(pose['display'][context]['scale'],accepted[context]['scale'])

    def test_source_ads_scope_inspect_and_non_fp_fallback_exact(self):
        self.assertEqual(self.wrapper['model']['fallback'],self.item['model'])
        self.assertEqual(self.dispatch['fallback'],self.item['model'])
        self.assertEqual({k:v for k,v in self.wrapper.items() if k!='model'},
                         {k:v for k,v in self.item.items() if k!='model'})
        for mode in ('ads','scope','inspect'):
            case = next(c for c in self.fp['cases'] if c['when']==mode)
            self.assertEqual(case['model'],self.item['model'])
        for context in ('gui','ground','fixed','head','thirdperson_righthand','thirdperson_lefthand',*g['FP']):
            for mode in ('hip','ads','scope','inspect'):
                for grip in (False,True):
                    if context in g['FP'] and mode=='hip':
                        continue
                    for p in (-1,0,.38,.52,.99,1):
                        self.assertEqual(select(self.wrapper['model'],context,mode,grip,p),
                                         select(self.item['model'],context,mode,grip,p))

    def test_original_authored_timing_values_and_magazine_holds(self):
        tree = ast.parse((ROOT/'scripts/generate_reload_models_w47.py').read_text())
        old = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                   and any(isinstance(t,ast.Name) and t.id=='KEYS' for t in n.targets))
        for current, previous in zip(g['KEYS'],old):
            self.assertEqual(current[0],previous[0])
            self.assertEqual(list(current[1]),previous[1])
            self.assertEqual(list(current[2]),previous[2])
            self.assertEqual(list(current[3]),[0,-previous[3],0])
            self.assertEqual(g['sample'](current[0]),tuple(list(v) for v in current[1:]))
        self.assertEqual(len(g['KEYS']),len(old))
        for lo,hi in ((0,.18),(.72,1)):
            for n in range(11):
                p=lo+(hi-lo)*n/10
                self.assertEqual(g['sample'](p)[2],[0,0,0])
                for grip in ('native','twohand'):
                    self.assertEqual(g['pose_display'](self.source['display'],self.twohand,p,'body',grip),
                                     g['pose_display'](self.source['display'],self.twohand,p,'magazine',grip))

    def test_curve_finite_bounded_and_monotone_on_each_authored_span(self):
        for a,b in zip(g['KEYS'],g['KEYS'][1:]):
            samples=[g['sample'](a[0]+(b[0]-a[0])*i/40) for i in range(41)]
            for channel in range(3):
                for axis in range(3):
                    values=[v[channel][axis] for v in samples]
                    lo,hi=sorted((a[channel+1][axis],b[channel+1][axis]))
                    self.assertTrue(all(math.isfinite(v) and lo-1e-10<=v<=hi+1e-10 for v in values))
                    sign=1 if b[channel+1][axis]>=a[channel+1][axis] else -1
                    self.assertTrue(all(sign*(y-x)>=-1e-10 for x,y in zip(values,values[1:])))
        for p in (float('nan'),float('inf'),-0.001,1.001):
            with self.assertRaises(ValueError):g['sample'](p)

    def test_c1_shared_velocity_at_knots_and_zero_idle_velocity(self):
        h=1e-7
        moving=0
        for channel in range(3):
            for axis in range(3):
                values=[k[channel+1][axis] for k in g['KEYS']]
                for i,k in enumerate(g['KEYS'][1:-1],1):
                    p=k[0];v=g['sample'](p)[channel][axis]
                    left=(v-g['sample'](p-h)[channel][axis])/h
                    right=(g['sample'](p+h)[channel][axis]-v)/h
                    self.assertAlmostEqual(left,right,delta=.002)
                    before=(values[i]-values[i-1])/(p-g['KEYS'][i-1][0])
                    after=(values[i+1]-values[i])/(g['KEYS'][i+1][0]-p)
                    if before*after>0:
                        self.assertGreater(abs(left),min(abs(before),abs(after))*.5)
                        moving+=1
                for p,q in ((0,h),(1,1-h)):
                    derivative=(g['sample'](p)[channel][axis]-g['sample'](q)[channel][axis])/h
                    self.assertLess(abs(derivative),.001)
        self.assertGreater(moving,5)  # Would fail per-segment smoothstep that halts at every knot.

    def test_rigid_magazine_follows_rotation_and_both_carriers(self):
        for p in (.25,.45,.6):
            for grip in ('native','twohand'):
                body=g['pose_display'](self.source['display'],self.twohand,p,'body',grip)
                mag=g['pose_display'](self.source['display'],self.twohand,p,'magazine',grip)
                offset=g['sample'](p)[2]
                for ctx in g['FP']:
                    expected=g['vec'](g['xyz'](body[ctx]['rotation']),offset)
                    self.assertEqual(body[ctx]['rotation'],mag[ctx]['rotation'])
                    for axis in range(3):
                        delta=mag[ctx]['translation'][axis]-body[ctx]['translation'][axis]
                        self.assertAlmostEqual(delta,expected[axis]*body[ctx]['scale'][axis],places=7)

    def test_profile_mesh_anchor_rig_calibration_and_full_ads_identity(self):
        profile=read_json(ROOT/g['PROFILE']);f=profile['framing']
        self.assertEqual((profile['schemaVersion'],profile['weapon']),(1,'beloved'))
        self.assertEqual(f['scale'],.98)
        self.assertTrue(f['keepMeshSupport'])
        self.assertNotIn('cameraDepth',f)
        self.assertTrue(set(profile['contacts'])<={'right','left','reload'})
        self.assertNotIn('right',profile['contacts']);self.assertNotIn('left',profile['contacts'])
        reload=profile['contacts']['reload']
        base=read_json(ROOT/'art/weapons/w201/contacts.json')['weapons']['beloved']
        self.assertEqual(reload['contact'],base['reload']['contact'])
        self.assertEqual(reload['partHint'],'magazine')
        self.assertEqual(reload['rigAction'],'80A8A140')
        rig=read_json(ROOT/g['RIG'])
        self.assertIn('beloved',rig['weapons']);self.assertFalse(rig['cameraExported'])
        self.assertEqual(len(rig['actions'][reload['rigAction']]['frames']),61)
        # Read-only shared helper validates the contract without requiring master's new loader.
        helper=runpy.run_path(str(ROOT/'scripts/first_person_framing_w205.py'))
        for mode in ('ads','scope','inspect'):
            amount=helper['weight']({'mode':mode},'destiny:weapon/sniper_rifle/beloved')
            self.assertEqual(amount,0)
            for display in (self.source['display'],self.twohand):
                self.assertEqual(helper['display'](display,f,amount,g['xyz'],g['mul'],g['euler'],g['vec']),display)
        self.assertEqual(helper['weight']({3:1},'destiny:weapon/sniper_rifle/beloved'),0)


def read_json_bytes(raw):
    def fail(value):raise AssertionError('Nonfinite JSON: '+value)
    return json.loads(raw,parse_constant=fail)


if __name__=='__main__':
    unittest.main()
