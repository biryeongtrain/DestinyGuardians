#!/usr/bin/env python3
"""Offline stdlib regression for W157 assets, no Gradle/native/external bbmodel."""
import copy
import hashlib
import importlib.util
import itertools
import json
import math
import struct
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('ace_w157', ROOT/'scripts/generate_ace_reload_w157.py')
G = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)
A = ROOT/G.ASSET


def rotate(v, angles):
    """Independent sequential-axis reference, not the generator matrix routine."""
    x, y, z = v
    a, b, c = map(math.radians, angles)
    x, y = x*math.cos(c)-y*math.sin(c), x*math.sin(c)+y*math.cos(c)
    x, z = x*math.cos(b)+z*math.sin(b), -x*math.sin(b)+z*math.cos(b)
    y, z = y*math.cos(a)-z*math.sin(a), y*math.sin(a)+z*math.cos(a)
    return [x, y, z]


def about(v, p, angles):
    return [x+y for x,y in zip(p, rotate([x-y for x,y in zip(v,p)], angles))]


def display_point(v, display):
    return [t+s*x for t,s,x in zip(display['translation'], display['scale'],
            rotate([x-8 for x in v], display['rotation']))]


def f32(value):
    return struct.unpack("!f", struct.pack("!f", value))[0]


def resolve(node, context='firstperson_righthand', progress=0, grip=False, state='hip'):
    kind = node['type'].removeprefix('minecraft:')
    if kind == 'model':
        return node['model']
    if kind == 'composite':
        return tuple(resolve(n,context,progress,grip,state) for n in node['models'])
    if kind == 'condition':
        assert node['property'] == 'minecraft:custom_model_data' and node.get('index',0) == 0
        return resolve(node['on_true' if grip else 'on_false'],context,progress,grip,state)
    if kind == 'select':
        v = context if node['property'] == 'minecraft:display_context' else state
        for case in node['cases']:
            if v in (case['when'] if isinstance(case['when'],list) else [case['when']]):
                return resolve(case['model'],context,progress,grip,state)
        return resolve(node['fallback'],context,progress,grip,state)
    if kind == 'range_dispatch':
        assert node['property'] == 'minecraft:custom_model_data' and node['index'] == 1
        eligible = [e for e in node['entries'] if f32(progress) >= f32(e['threshold'])]
        return resolve(eligible[-1]['model'] if eligible else node['fallback'],context,progress,grip,state)
    raise AssertionError(kind)


class AceReloadW157Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = G.generate()
        cls.source = json.loads((ROOT/G.SOURCE).read_bytes())
        cls.original_item = json.loads((ROOT/G.ITEM).read_bytes())
        cls.twohand = json.loads((ROOT/G.TWOHAND).read_bytes())['display']
        cls.manifest = json.loads((ROOT/G.MANIFEST).read_bytes())
        cls.graph = cls.read_asset('items/'+G.KEY+'.json')['model']
        cls.body = cls.read_asset('models/'+G.KEY+'_body.json')
        cls.cylinder = cls.read_asset('models/'+G.KEY+'_cylinder.json')

    @staticmethod
    def read_asset(path):
        return json.loads((A/path).read_bytes())

    @classmethod
    def frame(cls, frame, part, grip='native'):
        return cls.read_asset(f'models/{G.KEY}_{frame:02}_{part}_{grip}.json')

    def assertVector(self,a,b,delta=3e-8):
        for x,y in zip(a,b):
            self.assertAlmostEqual(x,y,delta=delta)

    def test_01_partition_and_original_geometry(self):
        expected = [*range(25,33), *range(37,45), *range(48,53)]
        self.assertEqual(list(G.CYLINDER),expected)
        self.assertEqual(len(self.body['elements']),66)
        self.assertEqual(len(self.cylinder['elements']),21)
        self.assertEqual(self.cylinder['elements'],[self.source['elements'][i] for i in expected])
        self.assertEqual(self.body['elements'],[e for i,e in enumerate(self.source['elements']) if i not in expected])
        self.assertEqual(self.cylinder['display'],self.source['display'])
        self.assertEqual(self.body['textures'],self.source['textures'])
        audit=json.loads((ROOT/G.AUDIT).read_bytes())
        self.assertEqual(tuple(audit['conversion']['mapping'][i]['sourceUuid'] for i in expected),G.CYLINDER_UUIDS)
        self.assertEqual(audit['source']['sha256'],self.manifest['externalSource']['sha256'])

    def test_02_uv_and_source_shape_preserved_every_frame(self):
        for frame in range(61):
            for grip in ('native','twohand'):
                m=self.frame(frame,'cylinder',grip)
                elements=m.get('elements',self.cylinder['elements'])
                for i,e in zip(G.CYLINDER,elements):
                    original=copy.deepcopy(self.source['elements'][i])
                    moved=copy.deepcopy(e)
                    if i == 48:
                        for axis in range(3):
                            self.assertAlmostEqual(moved['to'][axis]-moved['from'][axis],
                                                   original['to'][axis]-original['from'][axis])
                        for key in ('from','to'):
                            moved[key][2]=original[key][2]
                    self.assertEqual(moved,original,(frame,grip,i))
                for e in elements:
                    self.assertEqual(set(e['faces']),{'north','south','east','west','up','down'})
                    for face in e['faces'].values():
                        self.assertEqual(face['texture'],'#0')
                        self.assertTrue(all(0<=n<=16 for n in face['uv']))

    def test_03_original_idle_endpoints_exact(self):
        for frame,part,grip in itertools.product((0,60),('body','cylinder'),('native','twohand')):
            m=self.frame(frame,part,grip)
            self.assertNotIn('elements',m)
            self.assertEqual(m['display'],self.source['display'] if grip=='native' else self.twohand)

    def test_04_independent_corner_composition_and_hinge(self):
        # Nonzero idle yaw/pitch + body multi-axis tilt + cylinder roll is the
        # case that Euler component addition gets wrong. Check actual JSON poses.
        for frame,hand,part in itertools.product(range(61),G.FP,('body','cylinder')):
            body,translation,swing,_=G.sample(frame/60)
            delta=G.euler(body)
            d=self.frame(frame,part)['display'][hand]
            idle=self.source['display'][hand]
            points=[list(G.HINGE),list(G.GRIP)]
            for i in ((25,38,48,50) if part=='cylinder' else (0,63,82)):
                e=self.source['elements'][i]
                for v in itertools.product(*zip(e['from'],e['to'])):
                    r=e.get('rotation')
                    points.append(about(v,r['origin'],[r['x'],r['y'],r['z']]) if r else list(v))
            for point in points:
                local=about(point,G.HINGE,(0,0,swing)) if part=='cylinder' else point
                local=about(local,G.GRIP,delta)
                ref=display_point([x+y for x,y in zip(local,translation)],idle)
                self.assertVector(display_point(point,d),ref)
        # The hinge's world point must be identical on both sides of the joint.
        for frame in range(61):
            for hand in G.FP:
                self.assertVector(display_point(G.HINGE,self.frame(frame,'body')['display'][hand]),
                                  display_point(G.HINGE,self.frame(frame,'cylinder')['display'][hand]))

    def test_05_noncommuting_rotations_and_singular_xyz(self):
        for angles in ((27,-18,86),(65,30,-22),(17,90,33),(17,-90,33),(210,0,-7)):
            matrix=G.xyz(angles)
            decomposed=G.euler(matrix)
            for point in ((1,0,0),(0,1,0),(0,0,1),(3,-2,5)):
                self.assertVector(rotate(point,decomposed),rotate(point,angles))
        # Deliberately ensure this test would reject W64's angle-add shortcut.
        idle=self.source['display'][G.FP[0]]['rotation']
        body,_,swing,_=G.sample(.35)
        delta=G.euler(body)
        point=(1,2,3)
        naive=rotate(point,[idle[i]+delta[i]+(swing if i==2 else 0) for i in range(3)])
        actual=rotate(rotate(rotate(point,(0,0,swing)),delta),idle)
        self.assertGreater(math.dist(naive,actual),.1)

    def test_06_twohand_existing_idle_compensation(self):
        # Undo the existing crossbow idle yaw and horizontal shift; no invented IK.
        # Rotation error is bounded by the accepted source's stored precision.
        for frame,part,hand in itertools.product(range(61),('body','cylinder'),G.FP):
            native=self.frame(frame,part)['display'][hand]
            two=self.frame(frame,part,'twohand')['display'][hand]
            for p in (G.HINGE,G.GRIP,(7.3,10.23,-4.38)):
                restored=rotate(display_point(p,two),(0,10,0))
                restored[0]-=.641864*16
                self.assertVector(restored,display_point(p,native),delta=2e-8)

    def test_07_graph_contexts_flags_and_states(self):
        for context,state,grip,p in itertools.product(
            ('thirdperson_righthand','thirdperson_lefthand','gui','ground','fixed','head','none'),
            ('hip','ads','inspect','scope','unknown'),(False,True),(.0,.35,.55,1.0)):
            self.assertEqual(resolve(self.graph,context,p,grip,state),
                             resolve(self.original_item['model'],context,p,grip,state))
        self.assertEqual(self.graph['fallback'],self.original_item['model'])
        for context,p,grip in itertools.product(G.FP,(.05,.34,.55,.95),(False,True)):
            frame=math.floor(p*60)
            expected=tuple(f'destiny:{G.KEY}_{frame:02}_{part}_{"twohand" if grip else "native"}'
                           for part in ('body','cylinder'))
            self.assertEqual(resolve(self.graph,context,p,grip),expected)

    def test_08_graph_endpoints_fallback_thresholds(self):
        self.assertEqual(self.manifest['frames'],61)
        self.assertEqual(self.manifest['intervals'],60)
        dispatch=self.graph['cases'][0]['model']
        self.assertEqual(dispatch['index'],1)
        self.assertEqual([e['threshold'] for e in dispatch['entries']],[f32(f/60) for f in range(61)])
        self.assertEqual(self.graph['cases'][0]['when'],list(G.FP))
        for context,p,grip,state in itertools.product(G.FP,(-1,0,1,2),(False,True),('hip','ads','inspect','scope')):
            self.assertEqual(resolve(self.graph,context,p,grip,state),
                             resolve(self.original_item['model'],context,p,grip,state))
        self.assertEqual(self.read_asset('items/'+G.KEY+'.json')['hand_animation_on_swap'],
                         self.original_item['hand_animation_on_swap'])

    def test_09_semantic_eject_load_and_close(self):
        def round_centres(frame):
            m=self.frame(frame,'cylinder')
            return [[(a+b)/2 for a,b in zip(e['from'],e['to'])] for e in m.get('elements',[])[21:]]
        self.assertEqual(len(round_centres(21)),6)
        self.assertEqual(len(round_centres(33)),6)
        self.assertGreater(round_centres(24)[0][2],round_centres(21)[0][2])
        self.assertLess(round_centres(24)[0][1],round_centres(21)[0][1])
        self.assertLess(round_centres(36)[0][2],round_centres(33)[0][2])
        self.assertLess(round_centres(39)[0][2],round_centres(36)[0][2])
        self.assertAlmostEqual(self.frame(21,'cylinder')['elements'][16]['from'][2],
                               self.source['elements'][48]['from'][2]+.65)
        self.assertEqual(G.sample(.70)[2:],(0,0))
        self.assertNotIn('elements',self.frame(42,'cylinder'))
        # At .35 the real drum centre separates from its body position; yoke hinge stays fixed.
        pc=display_point(G.DRUM_CENTER,self.frame(21,'cylinder')['display'][G.FP[0]])
        pb=display_point(G.DRUM_CENTER,self.frame(21,'body')['display'][G.FP[0]])
        self.assertGreater(math.dist(pc,pb),1.0)
        self.assertGreater(abs(G.euler(G.sample(.10)[0])[0]),90)  # real source early spin

    def test_10_budget_model_parents_and_finite_values(self):
        counts=[]
        for frame in range(61):
            for grip in ('native','twohand'):
                assembled=0
                for part in ('body','cylinder'):
                    m=self.frame(frame,part,grip)
                    self.assertEqual(m['parent'],f'destiny:{G.KEY}_{part}')
                    base=self.body if part=='body' else self.cylinder
                    assembled+=len(m.get('elements',base['elements']))
                    for hand in G.FP:
                        self.assertTrue(all(math.isfinite(v) for key in ('rotation','translation','scale') for v in m['display'][hand][key]))
                self.assertLessEqual(assembled,1000)
            counts.append(assembled)
        self.assertEqual(counts,self.manifest['assembledElementsByFrame'])
        self.assertEqual(max(counts),93)

    def test_11_generated_bytes_and_exact_inventory(self):
        self.assertEqual(len(self.generated),248)
        expected={ROOT/G.MANIFEST,A/f'items/{G.KEY}.json'}
        expected.update(A/f'models/{G.KEY}_{part}.json' for part in ('body','cylinder'))
        expected.update(A/f'models/{G.KEY}_{f:02}_{part}_{grip}.json'
                        for f,part,grip in itertools.product(range(61),('body','cylinder'),('native','twohand')))
        self.assertEqual(set(self.generated),expected)
        self.assertEqual(len(expected|{ROOT/'scripts/generate_ace_reload_w157.py',Path(__file__).resolve()}),250)
        for p,data in self.generated.items():
            self.assertEqual(p.read_bytes(),data,str(p.relative_to(ROOT)))

    def test_12_input_and_output_hashes(self):
        for path,digest in self.manifest['sourceSha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
        for path,digest in self.manifest['sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
        self.assertFalse(self.manifest['nativeGameplayVerified'])
        self.assertFalse(self.manifest['mechanicsOrAudioChanged'])

    def test_13_invalid_progress_rejected(self):
        for value in (-.01,1.01,float('nan'),float('inf'),-float('inf')):
            with self.assertRaises(ValueError):
                G.sample(value)

    def test_14_offline_relocated_generation(self):
        # Only repo-relative inputs are required; no Downloads, network, Java or game.
        with tempfile.TemporaryDirectory(prefix='w157-offline-') as tmp:
            root=Path(tmp)
            for path in self.manifest['sourceSha256']:
                target=root/path
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((ROOT/path).read_bytes())
            relocated=G.generate(root)
            self.assertEqual({str(p.relative_to(root)):data for p,data in relocated.items()},
                             {str(p.relative_to(ROOT)):data for p,data in self.generated.items()})


    def test_15_reload_joint_offline_framing_guard(self):
        # Only a rough fixed-camera crop guard, not a native visibility certificate.
        # Retain the existing crop bound for the new source body motion.
        for frame in (12,21,33,42,48,51,54):
            p=display_point(G.DRUM_CENTER,self.frame(frame,'cylinder')['display'][G.FP[0]])
            x,y,z=[v/16+offset for v,offset in zip(p,(.56,-.52,-.72))]
            self.assertLess(z,-.5)
            screen_x=.5+(x/-z)/(2*math.tan(math.radians(35)))*.75
            screen_y=.5-(y/-z)/(2*math.tan(math.radians(35)))
            self.assertTrue(.2<screen_x<.9,(frame,screen_x))
            self.assertTrue(.25<screen_y<.85,(frame,screen_y))


    def test_16_float32_all_buckets_boundaries_and_generation_offset(self):
        entries=self.graph['cases'][0]['model']['entries']
        self.assertEqual(len(entries),61)
        for frame in range(61):
            threshold=f32(frame/60)
            bits=struct.unpack('!I',struct.pack('!f',threshold))[0]
            # Immediately below each interior float threshold selects its predecessor.
            if frame:
                below=struct.unpack('!f',struct.pack('!I',bits-1))[0]
                for context,grip in itertools.product(G.FP,(False,True)):
                    self.assertEqual(resolve(self.graph,context,below,grip),
                                     resolve(entries[frame-1]['model'],context,below,grip))
            for offset,context,grip in itertools.product((0,f32(.001)),G.FP,(False,True)):
                wire=f32(threshold+offset)
                if frame<60:
                    self.assertLess(wire,f32((frame+1)/60))
                self.assertEqual(resolve(self.graph,context,wire,grip),
                                 resolve(entries[frame]['model'],context,wire,grip))

    def test_17_dense_bank_retains_all_legacy_poses_and_adds_real_intermediates(self):
        # Frozen pre-W198 21-sample product bytes, concatenated frame/part/grip.
        # Every third dense pose must reproduce those exact models, not a new curve.
        digest=hashlib.sha256()
        for frame,part,grip in itertools.product(range(0,61,3),('body','cylinder'),('native','twohand')):
            digest.update((A/f'models/{G.KEY}_{frame:02}_{part}_{grip}.json').read_bytes())
        self.assertEqual(digest.hexdigest(),'0ed9df83b00e9fe6ec144cf7387231097067b4703b08b1e68b70f8fd2105b2d0')
        added=[f for f in range(61) if f%3]
        self.assertEqual(len(added),40)
        for frame,part,grip in itertools.product(added,('body','cylinder'),('native','twohand')):
            display=self.frame(frame,part,grip)['display']
            for coarse in (frame//3*3,(frame//3+1)*3):
                self.assertNotEqual(display,self.frame(coarse,part,grip)['display'],(frame,coarse,part,grip))


if __name__ == '__main__':
    unittest.main()
