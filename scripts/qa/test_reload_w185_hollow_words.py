#!/usr/bin/env python3
"""Bounded W185 asset/reference contract tests; runtime lifecycle belongs to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w185_hollow_words.py'))
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
class ReloadW185HollowTest(unittest.TestCase):
    def test_exact_canonical96_partition_and_gameplay_pins(self):
        source=read(G['SOURCE']);m=read(ART/'manifest.json');rebuilt={}
        self.assertEqual(96,len(source['elements']))
        for part,count,original in [('body',95,95),('magazine',2,1)]:
            model=read(A/f'models/{KEY}_{part}.json');self.assertEqual(count,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            self.assertEqual(original,len(m['partitionIndices'][part]))
            for i,el in zip(m['partitionIndices'][part],model['elements']):self.assertNotIn(i,rebuilt);rebuilt[i]=el
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(96)])
        self.assertEqual(576,sum(len(el['faces']) for el in rebuilt.values()))
        self.assertEqual((96,95,2,97,1,0),tuple(m[k] for k in ('sourceElements','bodyElements','movingElements','maxAssembledElements','addedElements','triangleAdapterElements')))
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        t=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='hollow_words')
        self.assertEqual((6,50,800,16,7,True,False),tuple(t[k] for k in ('magazine','reloadTicks','chargeMillis','chargeTicks','burstSize','sharedBurstAmmo','shellReload')))

    def test_whole_cell53_moves_with_shaft_and_fixed_grip_heel46_stays(self):
        mag=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements'];source=read(G['SOURCE'])
        self.assertEqual(['under_grip_cell','magazine_shaft_upper'],[el['name'] for el in mag])
        self.assertEqual([53],read(ART/'manifest.json')['partitionIndices']['magazine'])
        self.assertEqual(source['elements'][53],mag[0]);self.assertIn(source['elements'][46],body)
        self.assertEqual('grip_heel',source['elements'][46]['name'])
        self.assertTrue(set(read(ART/'manifest.json')['semanticGroups']['fixed'])<={el['name'] for el in body})
        self.assertLessEqual(len(body)+len(mag),1000)

    def test_insert_coherent_overlaps_cell_and_seated_inside_original_solids(self):
        import numpy as np,itertools
        source=read(G['SOURCE']);neck=G['reload_shaft'](source)[0]
        self.assertEqual(source['elements'][53]['faces'],neck['faces']);self.assertEqual(source['elements'][43]['rotation'],neck['rotation'])
        self.assertEqual([7.65,6.25,-.35],neck['from']);self.assertEqual([8.35,6.85,1.9],neck['to'])
        def rotation(el):
            rr=el.get('rotation',{});angles=[rr.get(a,0) for a in 'xyz']
            if 'axis' in rr:angles['xyz'.index(rr['axis'])]=rr['angle']
            return np.array(G['xyz'](angles))
        def inside(el,p):
            o=np.array(el.get('rotation',{}).get('origin',[8]*3));q=(p-o)@rotation(el)+o
            return bool(np.all(q>=np.array(el['from'])-1e-6) and np.all(q<=np.array(el['to'])+1e-6))
        origin=np.array(neck['rotation']['origin']);cell_contacts=0
        for v in itertools.product(*[np.linspace(a,b,7) for a,b in zip(neck['from'],neck['to'])]):
            point=(np.array(v)-origin)@rotation(neck).T+origin
            self.assertTrue(any(inside(el,point) for el in source['elements']),str(point))
            cell_contacts+=int(inside(source['elements'][53],point))
        self.assertGreater(cell_contacts,0)
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

    def test_individually_authored_right_edge_lift_underside_cell_exchange_roll_lower(self):
        sample=G['sample'];self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(0));self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(1))
        self.assertEqual([66,-9,-24],sample(.26)[0]);self.assertEqual([-.3,-4.8,-1.99],sample(.38)[2])
        self.assertEqual(-4.8,sample(.48)[2][1]);self.assertGreater(sample(.58)[2][1],sample(.48)[2][1])
        self.assertEqual([0,0,0],sample(.64)[2]);self.assertLess(sample(.72)[0][2],sample(.64)[0][2]);self.assertLess(sample(.88)[0][0],0)
        old=runpy.run_path(str(ROOT/'scripts/generate_reload_w184_distant_relation.py'))
        self.assertNotEqual(old['KEYS'],G['KEYS'])
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)
        # Whole shaft clears original cell seat when withdrawn, rather than leaving a baseplate-only split.
        import numpy as np,itertools
        neck=G['reload_shaft'](read(G['SOURCE']))[0];rr=neck['rotation'];origin=np.array(rr['origin']);rot=np.array(G['xyz']([rr['angle'],0,0]))
        points=np.array([(np.array(v)-origin)@rot.T+origin+sample(.38)[2] for v in itertools.product(*zip(neck['from'],neck['to']))])
        self.assertLess(points[:,1].max(),3.875)

    def test_rigid_payload_distances_and_independent_matrix_points(self):
        import numpy as np
        source=read(G['SOURCE']);two=read(G['TWOHAND'])['display'];points=np.array([[7.465,3.875,1.93],[8.535,4.825,5.47],[8.35,6.85,1.9]])
        for p in (.2,.35,.6,.9):
            for grip in ('native','twohand'):
                d=G['pose_display'](source['display'],two,p,'magazine',grip)[FP[0]]
                actual=(points-8)*d['scale'];actual=actual@np.array(G['xyz'](d['rotation'])).T+np.array(d['translation'])
                for i,j in ((0,1),(1,2),(0,2)):
                    self.assertAlmostEqual(np.linalg.norm(actual[i]-actual[j]),.85*np.linalg.norm(points[i]-points[j]),places=8)

    def test_actual_same_weapon_provenance_pts_hashes_and_honest_offline_evidence(self):
        m=read(ART/'manifest.json');ref=m['reference'];source=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=ozOSAOr5T4c',ref['url']);self.assertEqual('Ironworker Gaming',ref['creator'])
        self.assertTrue(ref['inspectedActualFrames']);self.assertEqual([11204,11348],ref['actionFrameRange'])
        self.assertEqual((60,1,'1/15360'),tuple(ref[k] for k in ('fpsNumerator','fpsDenominator','sourceTimebase')))
        self.assertEqual(16,len(ref['frames']));self.assertEqual(16,len({f['sha256'] for f in ref['frames']}))
        self.assertIn('HOLLOW WORDS',ref['frames'][0]['observation'])
        for f in ref['frames']:
            self.assertAlmostEqual(f['sourceFrameIndex']/60,f['timestampSeconds']);self.assertEqual(f['sourceFrameIndex']*256,f['pts']);self.assertIn(f['sha256'],source)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['masterOwnsRegistryRuntime'])
        self.assertIn('OFFLINE',source)
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)

    def test_exact94_owned_paths_and_manifest_hashes(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren')))
        self.assertEqual(90,len(G['expected_output_paths']()));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in G['expected_output_paths']()}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w185_hollow_words.py','scripts/qa/test_reload_w185_hollow_words.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW185HollowTest.java'}
        self.assertEqual(94,len(exact))
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
