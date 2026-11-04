#!/usr/bin/env python3
"""Bounded W179 asset/reference contract tests; runtime lifecycle belongs to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w179_null_composure.py'))
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
class ReloadW179NullComposureTest(unittest.TestCase):
    def test_canonical_partition_uv_texture_and_data_preserved(self):
        source=read(G['SOURCE']);m=read(ART/'manifest.json');rebuilt={}
        for part,count in (('body',88),('magazine',3)):
            model=read(A/f'models/{KEY}_{part}.json')
            self.assertEqual(count,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            indices=m['partitionIndices'][part];self.assertEqual(count,len(indices))
            for index,element in zip(indices,model['elements']):
                self.assertNotIn(index,rebuilt);rebuilt[index]=element
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(91)])
        self.assertEqual((91,0,91),tuple(m[k] for k in ('cubeElements','triangleAdapterElements','maxAssembledElements')))
        self.assertLessEqual(m['maxAssembledElements'],1000)
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='null_composure')
        self.assertEqual((6,41,533,9,14.333333333333),tuple(timing[k] for k in ('magazine','reloadTicks','chargeMillis','burstSize','cadenceTicks')))

    def test_three_solid_battery_and_fixed_frame_assignment(self):
        cell=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements']
        self.assertEqual(list(G['CELL_NAMES']),[e['name'] for e in cell])
        self.assertEqual((1.47,6.75,3.24),tuple(round(b-a,2) for a,b in zip(cell[0]['from'],cell[0]['to'])))
        for e in cell:
            self.assertEqual(6,len(e['faces']));self.assertTrue(all(b>a for a,b in zip(e['from'],e['to'])))
        for e in cell[1:]:
            self.assertTrue(all(min(e['to'][k],cell[0]['to'][k])>max(e['from'][k],cell[0]['from'][k]) for k in range(3)))
        names={e['name'] for e in body}
        self.assertTrue({'Keel_forward_diagonal_web','Keel_upper_web_fill','Open_frame_lower_brace','Blue_capacitor_facet_0','Reflex_roof'}<=names)
        self.assertFalse(set(G['CELL_NAMES'])&names)

    def test_fp_graph_grips_thresholds_and_exact_ads_inspect_nonfp_fallback(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap'])
        self.assertEqual(canonical['model'],graph['fallback']);self.assertEqual(list(FP),graph['cases'][0]['when'])
        guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases'])
        rg=guard['fallback'];self.assertEqual(1,rg['index']);self.assertEqual(canonical['model'],rg['fallback'])
        self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        for ctx in list(FP)+['thirdperson_righthand','thirdperson_lefthand','gui','ground','fixed','head','none','on_shelf']:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in (-1,-.001,0,.049,.05,.35,.65,.999,1,1.1):
                        got=resolve(graph,ctx,mode,progress,grip)
                        if ctx not in FP or mode or progress<0:self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got,(ctx,mode,progress,grip))
                        else:
                            i=min(20,math.floor(progress*20+1e-10));suffix='twohand' if grip else 'native'
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{part}_{suffix}' for part in ('body','magazine')),got)

    def test_endpoints_all_contexts_and_constant_scale(self):
        for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            accepted=read(path)['display']
            for i in range(21):
                for part in ('body','magazine'):
                    c=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    self.assertEqual({'parent','display'},set(c));self.assertEqual(f'destiny:{KEY}_{part}',c['parent'])
                    for ctx,d in c['display'].items():
                        self.assertEqual(accepted[ctx]['scale'],d['scale'])
                        self.assertTrue(all(math.isfinite(v) for arr in d.values() for v in arr))
                        if ctx not in FP or i in (0,20):self.assertEqual(accepted[ctx],d)

    def test_null_composure_upright_battery_and_top_sweep_phase_order(self):
        sample=G['sample']
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(0))
        self.assertGreater(sample(.11)[0][0],75);self.assertGreater(sample(.34)[0][2],15)
        self.assertEqual([0,0,0],sample(.11)[2]);self.assertEqual([-.3,-3.2,-.4],sample(.34)[2])
        self.assertEqual(sample(.34)[2],sample(.45)[2]);self.assertGreater(sample(.56)[2][1],sample(.45)[2][1])
        self.assertEqual([0,0,0],sample(.64)[2]);self.assertGreater(sample(.80)[0][0],sample(.73)[0][0])
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(1))
        for i in range(101):
            angles,_,offset=sample(i/100);self.assertLessEqual(max(abs(v) for v in angles),84);self.assertGreaterEqual(offset[1],-3.2)
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)
        for args in ((.5,'cell','native'),(.5,'body','other')):
            with self.assertRaises(ValueError):G['pose_display'](read(G['SOURCE'])['display'],read(G['TWOHAND'])['display'],*args)

    def test_observed_source_vs_authored_motion_and_offline_limits(self):
        m=read(ART/'manifest.json');ref=m['reference'];source=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=FdLSPBirfps',ref['url']);self.assertEqual('Datto',ref['creator'])
        self.assertTrue(ref['inspectedActualFrames']);self.assertEqual([137,138.8],ref['selectedSeconds'])
        self.assertEqual(12,len(ref['frames']));self.assertEqual(12,len({f['sha256'] for f in ref['frames']}))
        self.assertIn('NULL COMPOSURE',ref['frames'][0]['observation'])
        for f in ref['frames']:
            self.assertEqual(round(f['timestampSeconds']*60),f['sourceFrameIndex']);self.assertIn(f['sha256'],source)
        self.assertIn('conceal',m['authoredHiddenDetails']);self.assertIn('topHandSweepRock',m['normalizedPhases'])
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['masterOwnsRegistryRuntime'])
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)

    def test_exact_owned_output_graph_and_hash_contract(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84,0),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren','addedElements')))
        outputs=G['expected_output_paths']();self.assertEqual(90,len(outputs));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in outputs}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w179_null_composure.py','scripts/qa/test_reload_w179_null_composure.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW179NullComposureTest.java'}
        self.assertEqual(94,len(exact));scope=Path('/private/tmp/w179-manifest.json')
        if scope.exists():self.assertEqual(exact,set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w179-null-composure')))
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
