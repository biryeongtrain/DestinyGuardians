#!/usr/bin/env python3
"""Bounded W208 Recluse presentation checks; no native/gameplay claims."""
import ast
import builtins
from collections import Counter
import copy
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT/'scripts/generate_reload_w208_the_recluse.py'


def read(path):
    return json.loads(path.read_bytes())


def load(path):
    spec = importlib.util.spec_from_file_location('w208_recluse', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate(node, context, grip=False, progress=-1, mode='hip'):
    kind = node['type'].split(':')[-1]
    if kind == 'select':
        value = context if node['property'].endswith('display_context') else mode
        for case in node['cases']:
            names = case['when'] if isinstance(case['when'], list) else [case['when']]
            if value in names:
                return evaluate(case['model'], context, grip, progress, mode)
        return evaluate(node['fallback'], context, grip, progress, mode)
    if kind == 'range_dispatch':
        selected = node['fallback']
        for entry in node['entries']:
            if progress >= entry['threshold']:
                selected = entry['model']
        return evaluate(selected, context, grip, progress, mode)
    if kind == 'condition':
        return evaluate(node['on_true' if grip else 'on_false'], context, grip, progress, mode)
    return node


class RecluseMotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = load(GENERATOR)
        cls.out = cls.g.generate(ROOT)
        cls.assets = ROOT/cls.g.ASSET
        cls.source = read(ROOT/cls.g.SURFACE/'the_recluse.json')
        cls.two = read(ROOT/cls.g.TWOHAND)['display']
        cls.item = read(ROOT/cls.g.ITEM)
        cls.wrapper = json.loads(cls.out[cls.assets/f'items/{cls.g.KEY}.json'])

    def test_import_and_generate_never_write(self):
        original_open, original_io = builtins.open, io.open
        def safe_open(fn):
            def wrapped(file, mode='r', *args, **kwargs):
                if any(c in str(mode) for c in 'wax+'):
                    raise AssertionError('disk write attempted')
                return fn(file, mode, *args, **kwargs)
            return wrapped
        with mock.patch('builtins.open', safe_open(original_open)), mock.patch('io.open', safe_open(original_io)), \
             mock.patch('os.open', side_effect=AssertionError('os.open attempted')), \
             mock.patch.object(Path, 'mkdir', side_effect=AssertionError('mkdir attempted')), \
             mock.patch.object(Path, 'unlink', side_effect=AssertionError('unlink attempted')), \
             mock.patch.object(Path, 'rename', side_effect=AssertionError('rename attempted')), \
             mock.patch('os.replace', side_effect=AssertionError('replace attempted')):
            module = load(GENERATOR)
            self.assertEqual(module.generate(ROOT), self.out)

    def test_namespace_count_manifest_and_model_references(self):
        g = self.g
        self.assertEqual(len(self.out), 248)
        for path, raw in self.out.items():
            self.assertTrue(path.is_absolute())
            allowed = [self.assets/f'models/weapon_reload_w208_the_recluse',
                       self.assets/f'items/weapon_reload_w208_the_recluse']
            self.assertTrue(path == ROOT/g.MANIFEST or any(path.is_relative_to(p) for p in allowed))
            json.loads(raw)
        manifest = json.loads(self.out[ROOT/g.MANIFEST])
        self.assertEqual(manifest['assets'], 247)
        self.assertEqual(manifest['partCubes'], {'body':62, 'magazine':4})
        for path, digest in manifest['outputSha256'].items():
            self.assertEqual(g.sha(self.out[ROOT/path]), digest)
        for frame in range(1,60):
            for grip in (False,True):
                node = evaluate(self.wrapper['model'], g.FP[0], grip, g.float32(frame/60))
                self.assertEqual(node['type'], 'minecraft:composite')
                self.assertEqual(len(node['models']), 2)
                for part, leaf in zip(g.PARTS,node['models']):
                    key = leaf['model'].split(':',1)[1]
                    self.assertEqual(key, f'{g.KEY}_{frame:02}_{part}_{"twohand" if grip else "native"}')
                    pose = json.loads(self.out[self.assets/f'models/{key}.json'])
                    self.assertIn(self.assets/'models'/(pose['parent'].split(':',1)[1]+'.json'), self.out)

    def test_current_geometry_partition_texture_and_uv_exact(self):
        packed = lambda e: json.dumps(e,sort_keys=True)
        joined = []
        for part in self.g.PARTS:
            original = read(ROOT/self.g.SURFACE/f'the_recluse_{part}.json')
            emitted = json.loads(self.out[self.assets/f'models/{self.g.KEY}_{part}.json'])
            original.pop('display',None)
            self.assertEqual(emitted, original)
            joined.extend(emitted['elements'])
            self.assertEqual(sum(len(e['faces']) for e in emitted['elements']),len(emitted['elements'])*6)
        self.assertEqual(Counter(map(packed,joined)),Counter(map(packed,self.source['elements'])))
        self.assertEqual(len(joined),66)

    def test_endpoints_exact_idle_for_both_grips_and_parts(self):
        for frame in (0,60):
            for part in self.g.PARTS:
                for grip in ('native','twohand'):
                    node = json.loads(self.out[self.assets/f'models/{self.g.KEY}_{frame:02}_{part}_{grip}.json'])
                    self.assertEqual(node['display'],self.source['display'] if grip=='native' else self.two)
            entry = self.wrapper['model']['cases'][0]['model']['fallback']['entries'][frame]
            self.assertEqual(entry['model'],self.item['model'])

    def test_61_runtime_float_thresholds_and_boundary_dispatch(self):
        entries = self.wrapper['model']['cases'][0]['model']['fallback']['entries']
        self.assertEqual(len(entries),61)
        thresholds = [e['threshold'] for e in entries]
        expected = [struct.unpack('!f',struct.pack('!f',i/60))[0] for i in range(61)]
        self.assertEqual(thresholds,expected)
        self.assertTrue(all(a<b for a,b in zip(thresholds,thresholds[1:])))
        for i in range(1,60):
            node = evaluate(self.wrapper['model'],self.g.FP[0],False,expected[i])
            self.assertIn(f'_{i:02}_body_native',node['models'][0]['model'])
            bits = struct.unpack('!I',struct.pack('!f',expected[i]))[0]
            before = struct.unpack('!f',struct.pack('!I',bits-1))[0]
            prior = evaluate(self.wrapper['model'],self.g.FP[0],False,before)
            self.assertEqual(prior,evaluate(self.item['model'],self.g.FP[0]) if i==1 else
                             evaluate(self.wrapper['model'],self.g.FP[0],False,expected[i-1]))

    def test_non_fp_ads_inspect_and_inactive_fallback_exact(self):
        self.assertEqual({k:v for k,v in self.wrapper.items() if k!='model'},
                         {k:v for k,v in self.item.items() if k!='model'})
        select = self.wrapper['model']
        original = self.item['model']
        self.assertEqual(select['fallback'],original)
        self.assertEqual(select['cases'][0]['model']['fallback']['fallback'],original)
        for context in (*self.g.FP,'gui','ground','fixed','head','thirdperson_righthand','thirdperson_lefthand'):
            for grip in (False,True):
                for mode in ('hip','ads','inspect'):
                    for p in (-1,0,.4,1):
                        if context not in self.g.FP or mode!='hip' or p in (-1,0,1):
                            self.assertEqual(evaluate(select,context,grip,p,mode),evaluate(original,context,grip,p,mode))

    def test_authored_timing_and_magazine_visibility_path_retained(self):
        tree = ast.parse((ROOT/'scripts/generate_reload_framing_w101.py').read_text())
        old = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                   and any(isinstance(t,ast.Name) and t.id=='KEYS' for t in n.targets))
        self.assertEqual(json.loads(json.dumps(self.g.KEYS)),json.loads(json.dumps(old)))
        self.assertEqual(self.g.sample(.4)[1],[-4.5,8,-2])
        self.assertEqual(self.g.sample(.4)[2],[.5,-4.2,.3])
        for p in (.4,.43,.48,.52):
            self.assertLess(math.dist(self.g.sample(p)[2],[.5,-4.2,.3]),1e-12)
        for p in (0,.03,.08,.12,.78,.82,.95,1):
            self.assertLess(math.dist(self.g.sample(p)[2],[0,0,0]),1e-12)
        for p in (.24,.3,.5,.6,.68):
            self.assertLess(math.dist(self.g.sample(p)[1],[-4.5,8,-2]),1e-12)

    def test_curve_is_finite_bounded_monotone_with_shared_velocity(self):
        g = self.g
        for a,b in zip(g.KEYS,g.KEYS[1:]):
            samples = [g.sample(a[0]+(b[0]-a[0])*i/24) for i in range(25)]
            for ch in range(3):
                for axis in range(3):
                    values = [v[ch][axis] for v in samples]
                    lo,hi = sorted((a[ch+1][axis],b[ch+1][axis]))
                    self.assertTrue(all(math.isfinite(v) and lo-1e-10<=v<=hi+1e-10 for v in values))
                    direction = 1 if hi==b[ch+1][axis] else -1
                    self.assertTrue(all((v-u)*direction>=-1e-10 for u,v in zip(values,values[1:])))
        h = 1e-7
        moving = 0
        for key in g.KEYS[1:-1]:
            p = key[0];left,mid,right = g.sample(p-h),g.sample(p),g.sample(p+h)
            speed = []
            for ch in range(3):
                for axis in range(3):
                    dl=(mid[ch][axis]-left[ch][axis])/h
                    dr=(right[ch][axis]-mid[ch][axis])/h
                    self.assertAlmostEqual(dl,dr,delta=.005)
                    speed.append(abs((dl+dr)/2))
            moving += max(speed)>.1
        self.assertGreaterEqual(moving,5) # Holds/extrema do not stop every moving knot.
        for endpoint,near in ((0,h),(1,1-h)):
            a,b=g.sample(endpoint),g.sample(near)
            self.assertLess(max(abs(a[c][i]-b[c][i])/h for c in range(3) for i in range(3)),.005)
        for invalid in (-.1,1.1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):g.sample(invalid)

    def test_all_pose_fields_finite_and_other_contexts_exact(self):
        for frame in range(61):
            for part in self.g.PARTS:
                for grip in ('native','twohand'):
                    display=json.loads(self.out[self.assets/f'models/{self.g.KEY}_{frame:02}_{part}_{grip}.json'])['display']
                    base=self.source['display'] if grip=='native' else self.two
                    for context,pose in display.items():
                        if context not in self.g.FP:self.assertEqual(pose,base[context])
                        for field in ('translation','rotation','scale'):
                            self.assertEqual(len(pose[field]),3)
                            self.assertTrue(all(math.isfinite(v) for v in pose[field]))
                        self.assertTrue(all(abs(v)<40 for v in pose['translation']))
                        self.assertEqual(pose['scale'],base[context]['scale'])

    def test_magazine_contact_follows_actual_moving_part_both_grips(self):
        g=self.g;anchor=[7.3,7.85,8.82]
        for p in (.24,.4,.52,.68):
            for grip in ('native','twohand'):
                body=g.pose_display(self.source['display'],self.two,p,'body',grip)
                mag=g.pose_display(self.source['display'],self.two,p,'magazine',grip)
                for context in g.FP:
                    self.assertEqual(body[context]['rotation'],mag[context]['rotation'])
                    delta=[mag[context]['translation'][i]-body[context]['translation'][i] for i in range(3)]
                    expected=g.vec(g.xyz(mag[context]['rotation']),g.sample(p)[2])
                    for i in range(3):self.assertAlmostEqual(delta[i],expected[i]*mag[context]['scale'][i],places=7)
                    # Shared anchor transformed by either pose differs solely by actual part displacement.
                    local=[v-8 for v in anchor]
                    self.assertEqual(g.vec(g.xyz(mag[context]['rotation']),local),g.vec(g.xyz(body[context]['rotation']),local))

    def test_shared_framing_moves_weapon_and_contact_without_stretch(self):
        g=self.g
        framing=load(ROOT/'scripts/first_person_framing_w205.py')
        settings=read(ROOT/'art/weapons/w208/the_recluse/profile.json')['framing']
        for grip in ('native','twohand'):
            for part in g.PARTS:
                base=g.pose_display(self.source['display'],self.two,.43,part,grip)
                self.assertEqual(framing.display(base,settings,0,g.xyz,g.mul,g.euler,g.vec),base)
                calibrated=framing.display(base,settings,1,g.xyz,g.mul,g.euler,g.vec)
                for context in g.FP:
                    side=-1 if context.endswith('lefthand') else 1
                    q=g.xyz([settings['rotation'][0],settings['rotation'][1]*side,settings['rotation'][2]*side])
                    anchor=[-.7,-.15,.82] # magazine handling palm relative to model [8,8,8]
                    offset=g.vec(g.xyz(base[context]['rotation']),[v*base[context]['scale'][0] for v in anchor])
                    before=[v+offset[i] for i,v in enumerate(base[context]['translation'])]
                    expected=g.vec(q,[v*settings['scale'] for v in before])
                    shift=[settings['translation'][0]*side,*settings['translation'][1:]]
                    expected=[v+shift[i] for i,v in enumerate(expected)]
                    actual=g.vec(g.xyz(calibrated[context]['rotation']),[v*calibrated[context]['scale'][0] for v in anchor])
                    actual=[v+calibrated[context]['translation'][i] for i,v in enumerate(actual)]
                    self.assertLess(math.dist(expected,actual),1e-7)
                for context in set(base)-set(g.FP):self.assertEqual(calibrated[context],base[context])
        # The source forearm length is retained by the common rig sampler;
        # keepMeshSupport must also leave the supplied mesh hand positions alone.
        rig=load(ROOT/'scripts/rig_arms_w205.py')
        data=read(ROOT/'art/weapons/w205/rigs/submachine_gun_dc16526f.json')
        rig.RELOAD_ACTIONS={**rig.RELOAD_ACTIONS,'the_recluse':('80A8A192',)}
        config={'weapon':'the_recluse','family':'submachine_gun','reload':{'rigAction':'80A8A192'}}
        scales=[]
        for progress in (.2,.43,.68,.9):
            base={c:{'translation':[1,2,3],'scale':[1,1,1],'rotation':[0,0,0]} for c in g.FP}
            right,left=copy.deepcopy(base),copy.deepcopy(base)
            dynamic=rig.apply(data,{},progress,config,right,left,base,base,
                {c:g.xyz([0,0,0]) for c in g.FP},settings,1,g.xyz,g.mul,g.euler,g.vec)
            self.assertTrue(dynamic)
            self.assertEqual(left[g.FP[0]]['translation'],[1,2,3])
            scales.append((right[g.FP[0]]['scale'][1],left[g.FP[0]]['scale'][1]))
        self.assertTrue(all(s==scales[0] for s in scales))

    def test_profile_mesh_contacts_source_rig_and_no_arm_extension(self):
        profile=read(ROOT/'art/weapons/w208/the_recluse/profile.json')
        base=read(ROOT/'art/weapons/w201/contacts.json')['weapons']['the_recluse']
        self.assertEqual(profile['schemaVersion'],1);self.assertEqual(profile['weapon'],'the_recluse')
        framing=profile['framing'];self.assertTrue(framing['keepMeshSupport']);self.assertEqual(framing['scale'],.98)
        self.assertLessEqual(max(map(abs,framing['translation'])),1)
        self.assertLessEqual(max(map(abs,framing['rotation'])),2)
        self.assertEqual(set(profile['contacts']),{'right','left','reload'})
        # W209 corrects the old coincident foregrip anchors: trigger hand aft,
        # support hand forward. Do not freeze the known-bad W201 placement.
        self.assertTrue(framing['meshArmDirections'])
        self.assertGreater(profile['contacts']['right']['position'][2]-profile['contacts']['left']['position'][2],4)
        reload=profile['contacts']['reload']
        self.assertEqual(reload['rigAction'],'80A8A192');self.assertEqual(reload['partHint'],'magazine')
        self.assertLess(reload['contact'][0],7.44) # outside the magazine's left face
        self.assertLess(abs(reload['contact'][2]-8.82),1)
        self.assertFalse(any('length' in k.lower() or 'extend' in k.lower() for k in framing))
        data=read(ROOT/'art/weapons/w205/rigs/submachine_gun_dc16526f.json')
        self.assertIn('the_recluse',data['weapons']);self.assertFalse(data['fallback']);self.assertFalse(data['cameraExported'])
        frames=data['actions'][reload['rigAction']]['frames']
        self.assertEqual(len(frames),61)
        self.assertTrue(all(a['progress']<b['progress'] for a,b in zip(frames,frames[1:])))
        self.assertGreater(math.dist([frames[5]['joints']['leftWrist'][i][3] for i in range(3)],
                                     [frames[10]['joints']['leftWrist'][i][3] for i in range(3)]),1e-4)


if __name__=='__main__':
    unittest.main()
