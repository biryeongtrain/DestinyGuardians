#!/usr/bin/env python3
"""Bounded W185 asset/reference contract tests; runtime lifecycle belongs to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w185_apostate.py'))
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
class ReloadW185ApostateTest(unittest.TestCase):
    def test_exact_partition_original114_elements684faces_and_pins(self):
        source=read(G['SOURCE']);manifest=read(ART/'manifest.json');rebuilt={}
        self.assertEqual(114,len(source['elements']))
        for part,total,original in [('body',110,110),('magazine',5,4)]:
            model=read(A/f'models/{KEY}_{part}.json')
            self.assertEqual(total,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            self.assertEqual(original,len(manifest['partitionIndices'][part]))
            for i,e in zip(manifest['partitionIndices'][part],model['elements']):
                self.assertNotIn(i,rebuilt);rebuilt[i]=e
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(114)])
        self.assertEqual(684,sum(len(e['faces']) for e in rebuilt.values()))
        self.assertEqual((114,110,5,115,1,0),tuple(manifest[k] for k in ('sourceElements','bodyElements','movingElements','maxAssembledElements','addedElements','triangleAdapterElements')))
        for p,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        t=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='apostate')
        self.assertEqual((6,54,140,1,False),tuple(t[k] for k in ('magazine','reloadTicks','rpm','burstSize','shellReload')))

    def test_complete_main_toe_heel_base_and_fixed_socket28(self):
        source=read(G['SOURCE'])['elements'];mag=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements']
        self.assertEqual([source[i] for i in (29,30,31,32)],mag[:4])
        self.assertEqual(['magazine/main','magazine/toe','magazine/heel','magazine/base','magazine_shaft_upper'],[e['name'] for e in mag])
        self.assertIn(source[28],body);self.assertEqual('magazine/socket',source[28]['name'])
        self.assertFalse(set(G['MAGAZINE_NAMES'])&{e['name'] for e in body})
        self.assertEqual(115,len(body)+len(mag));self.assertLessEqual(len(body)+len(mag),1000)

    def test_small_connected_shaft_original_atlas_hidden_in_fixed_socket(self):
        source=read(G['SOURCE']);shaft=G['reload_shaft'](source)[0];socket=source['elements'][28];main=source['elements'][29]
        self.assertEqual(main['faces'],shaft['faces']);self.assertNotIn('rotation',shaft)
        self.assertEqual([7.57,8.55,1.30],shaft['from']);self.assertEqual([8.43,9.10,4.90],shaft['to'])
        for lo,hi,slo,shi,mlo,mhi in zip(shaft['from'],shaft['to'],socket['from'],socket['to'],main['from'],main['to']):
            self.assertGreaterEqual(lo,slo);self.assertLessEqual(hi,shi)
            self.assertGreater(min(hi,mhi)-max(lo,mlo),0,'shaft must intersect main in every dimension')
        self.assertFalse(read(ART/'manifest.json')['sourceLimitation']['exactOriginalShaftFidelityVerified'])

    def test_graph_both_fp_hands_grips_and_exact_canonical_fallbacks(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap'])
        self.assertEqual(canonical['model'],graph['fallback']);self.assertEqual(list(FP),graph['cases'][0]['when'])
        guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases'])
        rg=guard['fallback'];self.assertEqual(1,rg['index']);self.assertEqual(canonical['model'],rg['fallback'])
        self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        for ctx in read(G['SOURCE'])['display']:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in (-1,0,.35,.6,1,1.5):
                        got=resolve(graph,ctx,mode,progress,grip)
                        if ctx not in FP or mode or progress<0 or progress==0 or progress>=1:
                            self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got,(ctx,mode,progress,grip))
                        else:
                            i=math.floor(progress*20+1e-10);suffix='twohand' if grip else 'native'
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{part}_{suffix}' for part in ('body','magazine')),got)
        for i,e in enumerate(rg['entries']):
            if i in (0,20):self.assertEqual(canonical['model'],e['model'])
            else:self.assertEqual(('minecraft:custom_model_data',0),(e['model']['property'],e['model']['index']))

    def test_84_children_constant_scale_and_exact_endpoints(self):
        count=0
        for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            accepted=read(path)['display']
            for i in range(21):
                for part in ('body','magazine'):
                    c=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json');count+=1
                    self.assertEqual({'parent','display'},set(c));self.assertEqual(f'destiny:{KEY}_{part}',c['parent'])
                    for ctx,d in c['display'].items():
                        self.assertEqual(accepted[ctx]['scale'],d['scale'])
                        self.assertTrue(all(math.isfinite(v) for arr in d.values() for v in arr))
                        if ctx not in FP or i in (0,20):self.assertEqual(accepted[ctx],d)
        self.assertEqual(84,count)

    def test_independent_apostate_vertical_lift_underbody_axis_and_seat(self):
        sample=G['sample'];self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(0));self.assertEqual(sample(0),sample(1))
        self.assertGreater(sample(.34)[0][0],85);self.assertLess(sample(.34)[0][1],0)
        
        for expected,actual in zip([-.10,-3.90,.15],sample(.34)[2]):self.assertAlmostEqual(expected,actual,places=10)
        for expected,actual in zip([-.45,-4.30,-.40],sample(.46)[2]):self.assertAlmostEqual(expected,actual,places=10)
        self.assertGreater(sample(.68)[2][1],0);self.assertEqual([0,0,0],sample(.74)[2])
        self.assertGreater(sample(.74)[0][0],sample(.84)[0][0]);self.assertGreater(sample(.84)[0][0],sample(.94)[0][0])
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)
        import numpy as np,itertools
        mag=read(A/f'models/{KEY}_magazine.json')['elements'];tops=[]
        for e in mag:
            r=e.get('rotation',{});origin=np.array(r.get('origin',[8]*3));rot=np.array(G['xyz']([r.get(a,0) for a in 'xyz']))
            for v in itertools.product(*zip(e['from'],e['to'])):tops.append(((np.array(v)-origin)@rot.T+origin+sample(.34)[2])[1])
        self.assertLess(max(tops),6.77,'entire magazine clears fixed canonical body')

    def test_rigid_payload_distances_and_independent_matrix_points(self):
        import numpy as np
        source=read(G['SOURCE']);two=read(G['TWOHAND'])['display'];points=np.array([[7.49,7.62,1.185],[8.51,8.60,5.035],[8.43,9.10,4.90]])
        for p in (.2,.35,.6,.9):
            for grip in ('native','twohand'):
                d=G['pose_display'](source['display'],two,p,'magazine',grip)[FP[0]]
                actual=(points-8)*d['scale'];actual=actual@np.array(G['xyz'](d['rotation'])).T+np.array(d['translation'])
                for i,j in ((0,1),(1,2),(0,2)):
                    self.assertAlmostEqual(np.linalg.norm(actual[i]-actual[j]),.85*np.linalg.norm(points[i]-points[j]),places=8)

    def test_original_source_provenance_pts_hashes_limits_and_images(self):
        m=read(ART/'manifest.json');ref=m['reference'];source=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=h835sF3Ouvo',ref['url']);self.assertEqual('Aztecross',ref['creator'])
        self.assertTrue(ref['inspectedActualFrames']);self.assertEqual([164.8,166.1],ref['actionSeconds'])
        self.assertEqual((60,1,'1/15360'),tuple(ref[k] for k in ('fpsNumerator','fpsDenominator','sourceTimebase')))
        self.assertEqual(16,len(ref['frames']));self.assertEqual(16,len({f['sha256'] for f in ref['frames']}))
        self.assertIn('APOSTATE',ref['frames'][0]['observation'])
        for f in ref['frames']:
            self.assertAlmostEqual(f['sourceFrameIndex']/60,f['timestampSeconds']);self.assertEqual(f['sourceFrameIndex']*256,f['pts']);self.assertIn(f['sha256'],source)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['masterOwnsRegistryRuntime'])
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)

    def test_exact94_owned_paths_and_manifest_hashes(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren')))
        self.assertEqual(90,len(G['expected_output_paths']()));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in G['expected_output_paths']()}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w185_apostate.py','scripts/qa/test_reload_w185_apostate.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW185ApostateTest.java'}
        self.assertEqual(94,len(exact))
        self.assertEqual(exact,set(m['ownedPaths']))
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
