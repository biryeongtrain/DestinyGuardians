#!/usr/bin/env python3
"""Bounded W187 asset/reference contract tests; runtime lifecycle belongs to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w187_bellowing_giant.py'))
A,KEY,ART,FP=(G[k] for k in ('A','KEY','ART','FP'))
def read(p):return json.loads((ROOT/p).read_bytes())
def resolve(node,ctx,mode,progress,grip):
    kind=node['type']
    if kind=='minecraft:select':
        value=ctx if node['property']=='minecraft:display_context' else mode
        for case in node['cases']:
            values=case['when'] if isinstance(case['when'],list) else [case['when']]
            if value in values:return resolve(case['model'],ctx,mode,progress,grip)
        return resolve(node['fallback'],ctx,mode,progress,grip)
    if kind=='minecraft:condition':return resolve(node['on_true' if grip else 'on_false'],ctx,mode,progress,grip)
    if kind=='minecraft:range_dispatch':
        matches=[e for e in node['entries'] if progress>=e['threshold']]
        return resolve(matches[-1]['model'] if matches else node['fallback'],ctx,mode,progress,grip)
    if kind=='minecraft:composite':return tuple(resolve(m,ctx,mode,progress,grip) for m in node['models'])
    if kind=='minecraft:model':return node['model']
    raise AssertionError(kind)
class ReloadW187BellowingTest(unittest.TestCase):
    def test_canonical114_entire_fixed_carrier_geometry_uv_paint_displays_and_pins(self):
        source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');m=read(ART/'manifest.json')
        self.assertEqual(source,body);self.assertEqual(114,len(source['elements']));self.assertEqual(684,sum(len(e['faces']) for e in source['elements']))
        self.assertEqual(list(range(114)),m['partitionIndices']['body']);self.assertEqual([],m['partitionIndices']['magazine'])
        self.assertEqual((114,114,16,130,16,0),tuple(m[k] for k in ('sourceElements','bodyElements','movingElements','maxAssembledElements','addedElements','triangleAdapterElements')))
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        t=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='bellowing_giant')
        self.assertEqual((1,64,60.,1,False,False),tuple(t[k] for k in ('magazine','reloadTicks','cadenceTicks','burstSize','sharedBurstAmmo','shellReload')))

    def test_coherent_whole_incoming_rocket_no_canonical_band_or_baseplate_moved(self):
        source=read(G['SOURCE']);rocket=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements']
        self.assertEqual(G['reload_rocket'](source),rocket);self.assertEqual(16,len(rocket));self.assertEqual(source['elements'],body)
        self.assertEqual(16,len({e['name'] for e in rocket}));self.assertTrue(all(e['name'].startswith('Reload_rocket_') for e in rocket))
        self.assertTrue(all(e['faces']==source['elements'][64]['faces'] for e in rocket))
        self.assertGreater(rocket[0]['to'][2]-rocket[0]['from'][2],4)
        self.assertLessEqual(len(body)+len(rocket),1000)
        self.assertEqual(4,sum('_fin_' in e['name'] for e in rocket))
        # Each jacket intersects the filled core; nose/tail/fins overlap adjoining solids.
        self.assertTrue(all(e['from'][2] < 2.25 and e['to'][2] > -1.8 for e in rocket[1:9]))
        for fin in rocket[12:]:self.assertLess(fin['from'][2],-1.65);self.assertGreater(fin['to'][2],-1.8)

    def test_seated_rocket_inside_unchanged_chamber_and_clear_muzzle_before_insert(self):
        import itertools
        import numpy as np
        source=read(G['SOURCE']);chamber=source['elements'][8];self.assertEqual('Launch_chamber_heart',chamber['name'])
        rocket=G['reload_rocket'](source);pts=[]
        for el in rocket:
            rr=el.get('rotation',{});rot=np.array(G['xyz']([rr.get(k,0) for k in 'xyz']));o=np.array(rr.get('origin',[8,8,8]))
            for v in itertools.product(*zip(el['from'],el['to'])):
                p=(np.array(v)-o)@rot.T+o;pts.append(p)
                self.assertTrue(np.all(p>=np.array(chamber['from'])-1e-6));self.assertTrue(np.all(p<=np.array(chamber['to'])+1e-6))
        pts=np.array(pts);self.assertLess((pts+G['sample'](.5)[2])[:,2].max(),-5.55)
        self.assertEqual([0,0,0],G['sample'](.65)[2])
        self.assertEqual(list(range(7,14)),[i for i in range(21) if G['payload_visible'](i)])

    def test_both_fp_hands_grips_exact_canonical_endpoint_negative_ads_inspect_nonfp(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap']);self.assertEqual(canonical['model'],graph['fallback'])
        self.assertEqual(list(FP),graph['cases'][0]['when']);guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases'])
        rg=guard['fallback'];self.assertEqual(1,rg['index']);self.assertEqual(canonical['model'],rg['fallback'])
        self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        for ctx in read(G['SOURCE'])['display']:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in (-1,0,.05,.3,.35,.5,.65,.7,.95,1,1.5):
                        got=resolve(graph,ctx,mode,progress,grip)
                        if ctx not in FP or mode or progress<=0 or progress>=1:
                            self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got,(ctx,mode,progress,grip))
                        else:
                            i=math.floor(progress*20+1e-10);suffix='twohand' if grip else 'native';parts=('body','magazine') if G['payload_visible'](i) else ('body',)
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{part}_{suffix}' for part in parts),got)
        for i,e in enumerate(rg['entries']):
            if i in (0,20):self.assertEqual(canonical['model'],e['model'])
            else:self.assertEqual(('minecraft:custom_model_data',0),(e['model']['property'],e['model']['index']))

    def test_84_children_constant_scale_exact_endpoints_and_nonfp_displays(self):
        count=0
        for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            accepted=read(path)['display']
            for i in range(21):
                for part in ('body','magazine'):
                    c=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json');count+=1
                    self.assertEqual({'parent','display'},set(c));self.assertEqual(f'destiny:{KEY}_{part}',c['parent'])
                    for ctx,d in c['display'].items():
                        self.assertEqual(accepted[ctx]['scale'],d['scale']);self.assertTrue(all(math.isfinite(v) for arr in d.values() for v in arr))
                        if ctx not in FP or i in (0,20):self.assertEqual(accepted[ctx],d)
        self.assertEqual(84,count)

    def test_independent_front_loading_motion_and_one_way_axial_seating(self):
        sample=G['sample'];self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(0));self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(1))
        self.assertGreater(sample(.35)[0][0],100);self.assertGreater(sample(.35)[2][0],0)
        self.assertEqual([0,0,-8.9],sample(.5)[2]);self.assertEqual([0,0,-5.7],sample(.55)[2]);self.assertEqual([0,0,-2.8],sample(.6)[2]);self.assertEqual([0,0,0],sample(.65)[2])
        self.assertGreater(sample(.72)[0][0],sample(.82)[0][0]);self.assertLess(sample(.9)[0][0],0)
        old=runpy.run_path(str(ROOT/'scripts/generate_reload_w185_hollow_words.py'));self.assertNotEqual(old['KEYS'],G['KEYS'])
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)

    def test_whole_payload_rigid_point_distances_both_grips_and_hands(self):
        import numpy as np
        source=read(G['SOURCE']);two=read(G['TWOHAND'])['display'];points=np.array([[7.46,11.51,-2.4],[8.54,12.59,3.2],[8,12.05,.4]])
        for p in (.35,.45,.55,.65):
            for grip in ('native','twohand'):
                for hand in FP:
                    d=G['pose_display'](source['display'],two,p,'magazine',grip)[hand]
                    actual=((points-8)*d['scale'])@np.array(G['xyz'](d['rotation'])).T+np.array(d['translation'])
                    for i,j in ((0,1),(1,2),(0,2)):self.assertAlmostEqual(np.linalg.norm(actual[i]-actual[j]),.85*np.linalg.norm(points[i]-points[j]),places=8)

    def test16_actual_same_weapon_source_hash_pts_and_honest_offline_status(self):
        m=read(ART/'manifest.json');ref=m['reference'];text=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=DemrVvcFFjI',ref['url']);self.assertEqual('The Silent Noob',ref['creator']);self.assertEqual([2940,3130],ref['actionFrameRange'])
        self.assertEqual((60000,1001,'1/60000'),tuple(ref[k] for k in ('fpsNumerator','fpsDenominator','sourceTimebase')));self.assertTrue(ref['inspectedActualFrames'])
        self.assertEqual(16,len(ref['frames']));self.assertEqual(16,len({f['sha256'] for f in ref['frames']}));self.assertIn('BELLOWING GIANT',ref['frames'][0]['observation'])
        for f in ref['frames']:
            self.assertAlmostEqual(f['sourceFrameIndex']*1001/60000,f['timestampSeconds']);self.assertEqual(f['sourceFrameIndex']*1001,f['pts']);self.assertIn(f['sha256'],text)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['sourceLimitation']['fullPayloadSourceFidelityVerified']);self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['masterOwnsRegistryRuntime'])
        self.assertIn('OFFLINE / NO HANDS / NOT NATIVE',text)
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)

    def test_exact94_paths_and_all_manifest_hashes(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren')))
        self.assertEqual(90,len(G['expected_output_paths']()));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in G['expected_output_paths']()}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w187_bellowing_giant.py','scripts/qa/test_reload_w187_bellowing_giant.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW187BellowingTest.java'};self.assertEqual(94,len(exact))
        graph=read(A/f'items/{KEY}.json');models=set()
        def visit(x):
            if isinstance(x,dict):
                if x.get('type')=='minecraft:model':models.add(x['model'])
                for v in x.values():visit(v)
            elif isinstance(x,list):
                for v in x:visit(v)
        visit(graph)
        for model in models:
            namespace,path=model.split(':');self.assertEqual('destiny',namespace);self.assertTrue((ROOT/A/f'models/{path}.json').is_file(),model)

if __name__=='__main__':unittest.main(verbosity=2)
