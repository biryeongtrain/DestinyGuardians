#!/usr/bin/env python3
"""Bounded W187 asset/reference contract tests; runtime lifecycle belongs to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w187_code_duello.py'))
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
class ReloadW187CodeTest(unittest.TestCase):
    def test_exact_partition_canonical217_solids1302faces_and_timing(self):
        source=read(G['SOURCE']);manifest=read(ART/'manifest.json');rebuilt={}
        self.assertEqual(217,len(source['elements']))
        for part,total,original in [('body',161,161),('magazine',58,56)]:
            model=read(A/f'models/{KEY}_{part}.json')
            self.assertEqual(total,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            self.assertEqual(original,len(manifest['partitionIndices'][part]))
            for i,e in zip(manifest['partitionIndices'][part],model['elements']):
                self.assertNotIn(i,rebuilt);rebuilt[i]=e
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(217)])
        self.assertEqual(1302,sum(len(e['faces']) for e in rebuilt.values()))
        self.assertEqual((217,161,58,219,2,0),tuple(manifest[k] for k in ('sourceElements','bodyElements','movingElements','maxAssembledElements','addedElements','triangleAdapterElements')))
        for p,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        t=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='code_duello')
        self.assertEqual((1,67,15,1,False),tuple(t[k] for k in ('magazine','reloadTicks','rpm','burstSize','shellReload')))

    def test_complete_canister_not_band_only_and_fixed_socket_rails(self):
        source=read(G['SOURCE'])['elements'];mag=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements']
        self.assertEqual([source[i] for i in G['CANISTER_INDICES']],mag[:56])
        self.assertEqual(56,len(G['CANISTER_INDICES']))
        for i in (26,34,79,86,95,96,97,214):self.assertIn(source[i],body)
        self.assertLessEqual(len(body)+len(mag),1000)
        self.assertGreater(max(e['to'][2] for e in mag)-min(e['from'][2] for e in mag),17.)
        self.assertEqual({'reload_connector_core','reload_connector_diagonal'},{e['name'] for e in mag[56:]})

    def test_connected_source_backed_hidden_connector_inside_canonical_rear_heart(self):
        import itertools,numpy as np
        source=read(G['SOURCE']);shaft=G['reload_shaft'](source);socket=source['elements'][34]
        self.assertEqual(2,len(shaft));self.assertEqual(shaft[0]['faces'],source['elements'][71]['faces'])
        for e in shaft:
            rr=e.get('rotation',{});angles=[rr.get('angle',0) if rr.get('axis')==a else rr.get(a,0) for a in 'xyz'];rot=np.array(G['xyz'](angles));origin=np.array(rr.get('origin',[8,12,11.75]))
            for v in itertools.product(*zip(e['from'],e['to'])):
                point=(np.array(v)-origin)@rot.T+origin
                self.assertTrue(np.all(point>=np.array(socket['from'])-1e-8));self.assertTrue(np.all(point<=np.array(socket['to'])+1e-8))
        self.assertLess(shaft[0]['from'][2],source['elements'][71]['to'][2])
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

    def test_independent_code_duello_axial_whole_canister_withdrawal_exchange_seating(self):
        sample=G['sample'];self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(0));self.assertEqual(sample(0),sample(1))
        self.assertGreater(sample(.27)[0][0],80);self.assertLess(sample(.27)[0][1],0)
        self.assertEqual([0,0,-1],read(ART/'manifest.json')['magazineExtractionAxis'])
        self.assertAlmostEqual(-25,sample(.44)[2][2]);self.assertAlmostEqual(-25,sample(.53)[2][2])
        self.assertAlmostEqual(.08,sample(.74)[2][2]);self.assertEqual([0,0,0],sample(.80)[2])
        self.assertGreater(sample(.80)[0][0],sample(.90)[0][0]);self.assertGreater(sample(.90)[0][0],sample(.97)[0][0])
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)
        # Common framing correction is independent of extraction/rotations.
        self.assertEqual([-2.,-3.5,-6.5],list(G['FRAMING_DELTA']))
        self.assertEqual([0.,0.,0.],G['framing_delta'](0));self.assertEqual([0.,0.,0.],G['framing_delta'](1))
        for p in (.20,.45,.70,.80):
            before=G['interpolate'](G['ORIGINAL_KEYS'],p);after=sample(p)
            self.assertEqual(before[0],after[0]);self.assertEqual(before[2],after[2])
            for got,want in zip(G['framing_delta'](p),(-2.,-3.5,-6.5)):self.assertAlmostEqual(want,got)
        self.assertLess(abs(G['framing_delta'](.01)[1]),.1)
        self.assertLess(abs(G['framing_delta'](.99)[1]),.1)
        # Detached canister must clear its original fixed rear socket along model-Z.
        mag=read(A/f'models/{KEY}_magazine.json')['elements']
        self.assertLess(max(e['to'][2]+sample(.44)[2][2] for e in mag),-5.43)

    def test_rigid_payload_distances_and_independent_matrix_points(self):
        import numpy as np
        source=read(G['SOURCE']);two=read(G['TWOHAND'])['display'];points=np.array([[7.66,12.65,-5.35],[8.34,12.95,10.95],[8.32,12.32,12.40]])
        for p in (.2,.35,.6,.9):
            for grip in ('native','twohand'):
                d=G['pose_display'](source['display'],two,p,'magazine',grip)[FP[0]]
                actual=(points-8)*d['scale'];actual=actual@np.array(G['xyz'](d['rotation'])).T+np.array(d['translation'])
                for i,j in ((0,1),(1,2),(0,2)):
                    self.assertAlmostEqual(np.linalg.norm(actual[i]-actual[j]),.85*np.linalg.norm(points[i]-points[j]),places=8)

    def test_original_source_provenance_pts_hashes_limits_and_images(self):
        m=read(ART/'manifest.json');ref=m['reference'];source=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=tXfSro7b6y0',ref['url']);self.assertEqual('Marcusbgaming',ref['creator'])
        self.assertTrue(ref['inspectedActualFrames']);self.assertEqual([774,858],ref['actionFrameRange'])
        self.assertEqual((30000,1001,'1/30000'),tuple(ref[k] for k in ('fpsNumerator','fpsDenominator','sourceTimebase')))
        self.assertEqual(16,len(ref['frames']));self.assertEqual(16,len({f['sha256'] for f in ref['frames']}))
        self.assertIn('CODE DUELLO',ref['frames'][-1]['observation'])
        for f in ref['frames']:
            self.assertAlmostEqual(f['sourceFrameIndex']*1001/30000,f['timestampSeconds']);self.assertEqual(f['sourceFrameIndex']*1001,f['pts']);self.assertIn(f['sha256'],source)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['masterOwnsRegistryRuntime'])
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)

    def test_exact94_owned_paths_and_manifest_hashes(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren')))
        self.assertEqual(90,len(G['expected_output_paths']()));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in G['expected_output_paths']()}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w187_code_duello.py','scripts/qa/test_reload_w187_code_duello.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW187CodeTest.java'}
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
