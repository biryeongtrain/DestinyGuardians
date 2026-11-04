#!/usr/bin/env python3
"""Bounded W188 asset/reference contract tests; runtime lifecycle belongs to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w188_line_in_the_sand.py'))
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
class ReloadW188LineTest(unittest.TestCase):
    def test_canonical_partition_preserves79_elements474_uv_faces_and_pins(self):
        source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');battery=read(A/f'models/{KEY}_magazine.json');m=read(ART/'manifest.json')
        self.assertEqual(79,len(source['elements']));self.assertEqual(474,sum(len(e['faces']) for e in source['elements']))
        self.assertEqual([e for i,e in enumerate(source['elements']) if i not in range(56,64)],body['elements'])
        self.assertEqual(source['elements'][56:64],battery['elements'][:8]);self.assertEqual(G['contacts'](source),battery['elements'][8:])
        self.assertEqual((79,71,10,81,2,0),tuple(m[k] for k in ('sourceElements','bodyElements','movingElements','maxAssembledElements','addedElements','triangleAdapterElements')))
        self.assertEqual(source['textures'],body['textures']);self.assertEqual(source['textures'],battery['textures'])
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        t=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='line_in_the_sand')
        self.assertEqual((5,49,19.,11,1,True,False),tuple(t[k] for k in ('magazine','reloadTicks','cadenceTicks','chargeTicks','burstSize','sharedBurstAmmo','shellReload')))

    def test_pair_contacts_connected_to_real_battery_within_rip_envelope(self):
        source=read(G['SOURCE']);contacts=G['contacts'](source);box=source['elements'][56]
        self.assertEqual('lower_battery',box['name']);self.assertEqual(2,len(contacts))
        for e in contacts:
            self.assertEqual(source['elements'][57]['faces'],e['faces'])
            for k in range(3):self.assertLess(max(e['from'][k],box['from'][k]),min(e['to'][k],box['to'][k]))
            self.assertLessEqual(e['to'][1],6.194252009)
        self.assertEqual([i for i in range(21) if i<=7 or i>=12],[i for i in range(21) if G['payload_visible'](i)])

    def test_both_fp_hands_grips_canonical_endpoints_negative_ads_inspect_nonfp(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap']);self.assertEqual(canonical['model'],graph['fallback'])
        self.assertEqual(list(FP),graph['cases'][0]['when']);guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases'])
        rg=guard['fallback'];self.assertEqual(1,rg['index']);self.assertEqual(canonical['model'],rg['fallback'])
        self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        for ctx in read(G['SOURCE'])['display']:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in (-1,0,*[i/20 for i in range(1,20)],1,1.5):
                        got=resolve(graph,ctx,mode,progress,grip)
                        if ctx not in FP or mode or progress<=0 or progress>=1:
                            self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got,(ctx,mode,progress,grip))
                        else:
                            i=math.floor(progress*20+1e-10);suffix='twohand' if grip else 'native';parts=('body','magazine') if G['payload_visible'](i) else ('body',)
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{part}_{suffix}' for part in parts),got)

    def test84_children_constant_scale_exact_endpoints_and_nonfp(self):
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

    def test_independent_source_phases_whole_battery_and_common_framing(self):
        sample=G['sample'];self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(0));self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(1))
        self.assertGreater(sample(.3)[0][0],70);self.assertEqual([0,-2.,0],sample(.3)[2]);self.assertLess(sample(.48)[2][1],-6)
        self.assertLess(sample(.60)[2][0],-2);self.assertLess(sample(.68)[2][1],0);self.assertGreater(sample(.8)[2][1],0);self.assertEqual([0,0,0],sample(.84)[2])
        for p in (.2,.3,.6,.76):self.assertLess(sample(p)[1][2],-3);self.assertLess(sample(p)[1][1],-2)
        for path in ('generate_reload_w185_hollow_words.py','generate_reload_w187_code_duello.py','generate_reload_w187_bellowing_giant.py'):
            self.assertNotEqual(runpy.run_path(str(ROOT/'scripts'/path))['KEYS'],G['KEYS'])
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)

    def test_rigid_battery_distances_both_hands_and_grips(self):
        import numpy as np
        source=read(G['SOURCE']);two=read(G['TWOHAND'])['display'];points=np.array([[7.205,4.94,3.669],[8.795,6.17,9.941],[8,5.6,6.83]])
        for i in range(21):
            for grip in ('native','twohand'):
                for hand in FP:
                    d=G['pose_display'](source['display'],two,i/20,'magazine',grip)[hand]
                    actual=((points-8)*d['scale'])@np.array(G['xyz'](d['rotation'])).T+np.array(d['translation'])
                    for a,b in ((0,1),(1,2),(0,2)):self.assertAlmostEqual(np.linalg.norm(actual[a]-actual[b]),.85*np.linalg.norm(points[a]-points[b]),places=8)

    def test16_actual_same_weapon_source_pts_hash_and_honest_native_status(self):
        m=read(ART/'manifest.json');ref=m['reference'];text=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=hu_LOERnF6o',ref['url']);self.assertEqual('Plasma Alchemist',ref['creator']);self.assertEqual([3365,3417],ref['actionFrameRange'])
        self.assertEqual((25,1,'1/12800'),tuple(ref[k] for k in ('fpsNumerator','fpsDenominator','sourceTimebase')));self.assertTrue(ref['inspectedActualFrames'])
        self.assertEqual(16,len(ref['frames']));self.assertEqual(16,len({f['sha256'] for f in ref['frames']}));self.assertIn('LINE IN THE SAND',ref['frames'][0]['observation'])
        for f in ref['frames']:
            self.assertAlmostEqual(f['sourceFrameIndex']/25,f['timestampSeconds']);self.assertEqual(f['sourceFrameIndex']*512,f['pts']);self.assertIn(f['sha256'],text)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['sourceLimitation']['fullPayloadSourceFidelityVerified']);self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['masterOwnsRegistryRuntime'])
        self.assertIn('OFFLINE / NO HANDS / NOT NATIVE',text)
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)

    def test_exact94_paths_hashes_and_model_references(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren')))
        self.assertEqual(90,len(G['expected_output_paths']()));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in G['expected_output_paths']()}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w188_line_in_the_sand.py','scripts/qa/test_reload_w188_line_in_the_sand.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW188LineTest.java'};self.assertEqual(94,len(exact))
        models=set()
        def visit(x):
            if isinstance(x,dict):
                if x.get('type')=='minecraft:model':models.add(x['model'])
                for v in x.values():visit(v)
            elif isinstance(x,list):
                for v in x:visit(v)
        visit(read(A/f'items/{KEY}.json'))
        for model in models:
            namespace,path=model.split(':');self.assertEqual('destiny',namespace);self.assertTrue((ROOT/A/f'models/{path}.json').is_file(),model)

if __name__=='__main__':unittest.main(verbosity=2)
