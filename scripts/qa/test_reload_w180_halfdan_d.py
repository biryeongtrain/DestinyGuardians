#!/usr/bin/env python3
"""Bounded W180 asset/reference contract tests; runtime lifecycle belongs to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w180_halfdan_d.py'))
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
class ReloadW180HalfdanDTest(unittest.TestCase):
    def test_canonical_partition_uv_texture_and_data_preserved(self):
        source=read(G['SOURCE']);m=read(ART/'manifest.json');rebuilt={}
        for part,count in (('body',110),('magazine',4)):
            model=read(A/f'models/{KEY}_{part}.json')
            self.assertEqual(count,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            indices=m['partitionIndices'][part];self.assertEqual(count,len(indices))
            for index,element in zip(indices,model['elements']):
                self.assertNotIn(index,rebuilt);rebuilt[index]=element
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(114)])
        self.assertEqual((114,0,114),tuple(m[k] for k in ('cubeElements','triangleAdapterElements','maxAssembledElements')))
        self.assertLessEqual(m['maxAssembledElements'],1000)
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='halfdan_d')
        self.assertEqual((33,44,None,1,3.0),tuple(timing[k] for k in ('magazine','reloadTicks','chargeMillis','burstSize','cadenceTicks')))

    def test_connected_whole_magazine_and_fixed_well_charging_handle(self):
        magazine=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements']
        self.assertEqual(list(G['MAGAZINE_NAMES']),[e['name'] for e in magazine])
        for e in magazine:
            self.assertEqual(6,len(e['faces']));self.assertTrue(all(b>a for a,b in zip(e['from'],e['to'])))
        for a,b in zip(magazine,magazine[1:]):
            self.assertTrue(all(min(a['to'][k],b['to'][k])>max(a['from'][k],b['from'][k]) for k in range(3)))
        names={e['name'] for e in body}
        self.assertTrue({'Well_front','Well_rear','Well_lower_bridge','Well_strap','Charging_handle','Guard_floor','Pistol_grip'}<=names)
        self.assertFalse(set(G['MAGAZINE_NAMES'])&names)

    def test_fp_graph_grips_thresholds_and_exact_ads_inspect_nonfp_fallback(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap'])
        self.assertEqual(canonical['model'],graph['fallback']);self.assertEqual(list(FP),graph['cases'][0]['when'])
        guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases'])
        rg=guard['fallback'];self.assertEqual(1,rg['index']);self.assertEqual(canonical['model'],rg['fallback'])
        self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        for ctx in list(FP)+['thirdperson_righthand','gui','ground','fixed','head']:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in (-1,0,.35,.65,1):
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

    def test_halfdan_withdraw_clear_well_insertion_then_seat_rock(self):
        sample=G['sample']
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(0))
        self.assertEqual([0,0,0],sample(.10)[2])
        self.assertLess(sample(.20)[2][1],0)
        self.assertEqual([-.65,-6.2,-.65],sample(.33)[2]);self.assertEqual(sample(.33)[2],sample(.53)[2])
        self.assertGreater(sample(.60)[2][1],sample(.53)[2][1]);self.assertEqual([0,0,0],sample(.67)[2])
        self.assertGreater(sample(.73)[0][0],sample(.67)[0][0]);self.assertLess(sample(.80)[0][0],sample(.73)[0][0])
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(1))
        # Representative full clearance: highest magazine point below canonical well/guard bottom.
        source=read(G['SOURCE']);parts=G['partition'](source)
        highest=max(e['to'][1] for e in parts['magazine']['elements'])+sample(.33)[2][1]
        lowest_well=min(e['from'][1] for e in parts['body']['elements'] if e['name'].startswith('Well_'))
        self.assertLess(highest,lowest_well-4)
        # Whole-part display translations keep a single rigid relative vector at every selected phase.
        for p in (0,.10,.20,.33,.53,.60,.67,.73,.90,1):
            angles,_,offset=sample(p);self.assertLessEqual(max(abs(v) for v in angles),33);self.assertGreaterEqual(offset[1],-6.2)
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)
        for args in ((.5,'cell','native'),(.5,'body','other')):
            with self.assertRaises(ValueError):G['pose_display'](read(G['SOURCE'])['display'],read(G['TWOHAND'])['display'],*args)

    def test_observed_source_vs_authored_motion_and_offline_limits(self):
        m=read(ART/'manifest.json');ref=m['reference'];source=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=JkSdcwO-MGM',ref['url']);self.assertEqual('CammyCakes Gaming',ref['creator'])
        self.assertTrue(ref['inspectedActualFrames']);self.assertEqual([77.1,78.6],ref['selectedSeconds'])
        self.assertEqual(17,len(ref['frames']));self.assertEqual(17,len({f['sha256'] for f in ref['frames']}))
        self.assertIn('HALFDAN-D',ref['frames'][0]['observation'])
        for f in ref['frames']:
            self.assertEqual(round(f['timestampSeconds']*60),f['sourceFrameIndex']);self.assertIn(f['sha256'],source)
        self.assertIn('conceal',m['authoredHiddenDetails']);self.assertIn('seatingRock',m['normalizedPhases'])
        self.assertIn('stays fixed',ref['chargingObservation']);self.assertEqual(3,len(m['sourceChronology']))
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['masterOwnsRegistryRuntime'])
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)

    def test_exact_owned_output_graph_and_hash_contract(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84,0),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren','addedElements')))
        outputs=G['expected_output_paths']();self.assertEqual(90,len(outputs));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in outputs}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w180_halfdan_d.py','scripts/qa/test_reload_w180_halfdan_d.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW180HalfdanDTest.java'}
        self.assertEqual(94,len(exact));scope=Path('/private/tmp/w180-manifest.json')
        if scope.exists():self.assertEqual(exact,set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w180-halfdan-d')))
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
