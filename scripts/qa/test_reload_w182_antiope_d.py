#!/usr/bin/env python3
"""Bounded W182 asset/reference contract tests; runtime lifecycle belongs to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w182_antiope_d.py'))
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
class ReloadW182AntiopeTest(unittest.TestCase):
    def test_exact_canonical_partition_uv_paint_and_gameplay_pins(self):
        source=read(G['SOURCE']);manifest=read(ART/'manifest.json');rebuilt={}
        self.assertEqual(118,len(source['elements']))
        for part,count in (('body',113),('magazine',5)):
            m=read(A/f'models/{KEY}_{part}.json')
            self.assertEqual(count,len(m['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in m.items() if k!='elements'})
            for i,e in zip(manifest['partitionIndices'][part],m['elements']):
                self.assertNotIn(i,rebuilt);rebuilt[i]=e
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(118)])
        self.assertEqual(708,sum(len(e['faces']) for e in rebuilt.values()))
        self.assertEqual((118,113,5,0,118,0),tuple(manifest[k] for k in ('sourceElements','bodyElements','movingElements','triangleAdapterElements','maxAssembledElements','addedElements')))
        self.assertLessEqual(manifest['maxAssembledElements'],1000)
        for p,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='antiope_d')
        self.assertEqual((30,46,600,2.,1,False),tuple(timing[k] for k in ('magazine','reloadTicks','rpm','cadenceTicks','burstSize','shellReload')))

    def test_five_connected_magazine_solids_and_hakke_identity_remain(self):
        mag=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements']
        self.assertEqual(list(G['MAGAZINE_NAMES']),[e['name'] for e in mag])
        connected={0}
        def overlap(a,b):return all(min(a['to'][k],b['to'][k])>max(a['from'][k],b['from'][k]) for k in range(3))
        while True:
            more={i for i,e in enumerate(mag) if any(overlap(e,mag[j]) for j in connected)}
            if more<=connected:break
            connected|=more
        self.assertEqual(set(range(5)),connected)
        for e in mag:self.assertEqual(6,len(e['faces']));self.assertNotIn('rotation',e)
        names={e['name'] for e in body}
        self.assertTrue({'upper_receiver','lower_receiver','orange_rear_cap','stock_comb','foregrip_body','grip_core','guard_floor','charging_rail','charging_handle','side_cylinder_core','rear_peep_0','bore_depth_stop'}<=names)
        self.assertFalse(set(G['MAGAZINE_NAMES'])&names)
        # No child geometry overrides: all body details and magazine solids are rigid.
        for child in (ROOT/A/f'models/{KEY}').parent.glob('antiope_d_*_*_*.json'):
            self.assertEqual({'parent','display'},set(json.loads(child.read_bytes())))

    def test_fp_graph_exact_ads_inspect_inactive_and_nonfp_for_all_samples(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap'])
        self.assertEqual(canonical['model'],graph['fallback']);self.assertEqual(list(FP),graph['cases'][0]['when'])
        guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases'])
        rg=guard['fallback'];self.assertEqual(1,rg['index']);self.assertEqual(canonical['model'],rg['fallback'])
        self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        contexts=list(read(G['SOURCE'])['display'])
        for ctx in contexts:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in [-1,-.001]+[i/20 for i in range(21)]+[1.1]:
                        got=resolve(graph,ctx,mode,progress,grip)
                        if ctx not in FP or mode or progress<0:
                            self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got,(ctx,mode,progress,grip))
                        else:
                            i=min(20,math.floor(progress*20+1e-10));suffix='twohand' if grip else 'native'
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{part}_{suffix}' for part in ('body','magazine')),got)
        for e in rg['entries']:
            c=e['model'];self.assertEqual('minecraft:custom_model_data',c['property']);self.assertEqual(0,c['index'])

    def test_all_84_children_constant_scale_and_exact_endpoints(self):
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

    def test_source_order_upward_extraction_grip_socket_seat_forward_recovery(self):
        sample=G['sample']
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(0))
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(1))
        self.assertEqual([-.6,-7.4,.25],sample(.16)[2]);self.assertEqual(sample(.16)[2],sample(.40)[2])
        self.assertGreater(sample(.16)[0][0],sample(.27)[0][0])
        self.assertGreater(sample(.50)[2][1],sample(.40)[2][1]);self.assertEqual([0,0,0],sample(.60)[2])
        self.assertGreater(sample(.68)[0][0],sample(.60)[0][0]);self.assertLess(sample(.77)[0][0],sample(.68)[0][0])
        mag=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements']
        highest=max(e['to'][1] for e in mag)+sample(.16)[2][1]
        lowest_grip=min(e['from'][1] for e in body if e['name'] in ('grip_core','grip_heel'))
        self.assertLess(highest,lowest_grip-6)
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)
        for args in ((.5,'cell','native'),(.5,'body','other')):
            with self.assertRaises(ValueError):G['pose_display'](read(G['SOURCE'])['display'],read(G['TWOHAND'])['display'],*args)

    def test_same_weapon_actual_source_hashes_and_explicit_limits(self):
        m=read(ART/'manifest.json');ref=m['reference'];source=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=M3tC-IkkFRU',ref['url']);self.assertEqual('CammyCakes Gaming',ref['creator'])
        self.assertTrue(ref['inspectedActualFrames']);self.assertEqual([99.65,101.],ref['selectedSeconds'])
        self.assertEqual(16,len(ref['frames']));self.assertEqual(16,len({f['sha256'] for f in ref['frames']}))
        self.assertIn('ANTIOPE-D',ref['frames'][0]['observation']);self.assertIn('Partial reload',ref['chargingObservation'])
        for f in ref['frames']:
            self.assertEqual(round(f['timestampSeconds']*60),f['sourceFrameIndex']);self.assertIn(f['sha256'],source)
        self.assertIn('conceal',m['authoredHiddenDetails']);self.assertIn('seatingRock',m['normalizedPhases'])
        self.assertIn('stays fixed',ref['chargingObservation']);self.assertEqual(3,len(m['sourceChronology']))
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['masterOwnsRegistryRuntime'])
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)

    def test_exact94_owned_paths_hashes_and_local_reference_resolution(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84,0),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren','addedElements')))
        outputs=G['expected_output_paths']();self.assertEqual(90,len(outputs));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in outputs}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w182_antiope_d.py','scripts/qa/test_reload_w182_antiope_d.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW182AntiopeTest.java'}
        self.assertEqual(94,len(exact));scope=Path('/private/tmp/w182-manifest.json')
        if scope.exists():self.assertEqual(exact,set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w182-antiope')))
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
