#!/usr/bin/env python3
"""Bounded W178 asset/reference contract tests; runtime lifecycle belongs to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w178_dream_breaker.py'))
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
class ReloadW178DreamBreakerTest(unittest.TestCase):
    def test_canonical_partition_reconstructs_all_geometry_uv_paint_and_timing(self):
        source=read(G['SOURCE']);parts={p:read(A/f'models/{KEY}_{p}.json') for p in ('body','magazine')}
        m=read(ART/'manifest.json');rebuilt={}
        for part,model in parts.items():
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            for index,element in zip(m['partitionIndices'][part],model['elements']):
                self.assertNotIn(index,rebuilt);rebuilt[index]=element
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(186)])
        self.assertEqual([182,4],[len(parts[p]['elements']) for p in ('body','magazine')]);self.assertLessEqual(sum(len(x['elements']) for x in parts.values()),1000)
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='dream_breaker')
        self.assertEqual((6,46,667,7,13.),tuple(timing[k] for k in ('magazine','reloadTicks','chargeMillis','burstSize','cadenceTicks')))
    def test_cell_is_existing_connected_volume_with_receiver_cradle(self):
        cell=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements']
        self.assertEqual(list(G['CELL_NAMES']),[e['name'] for e in cell]);self.assertEqual((1.42,6.54,3.45),tuple(round(b-a,2) for a,b in zip(cell[0]['from'],cell[0]['to'])))
        connected={0}
        while True:
            previous=set(connected)
            for i,a in enumerate(cell):
                if any(all(min(a['to'][k],cell[j]['to'][k])-max(a['from'][k],cell[j]['from'][k])>0 for k in range(3)) for j in connected):connected.add(i)
            if previous==connected:break
        self.assertEqual(set(range(4)),connected)
        for e in cell:self.assertEqual(6,len(e['faces']));self.assertTrue(all(b>a for a,b in zip(e['from'],e['to'])))
        names={e['name'] for e in body}
        self.assertTrue({'upper_pack_cuff','lower_pack_cuff','power_hose_0','upper_brass_feed'}<=names)
        self.assertFalse(set(G['CELL_NAMES'])&names)
    def test_graph_fp_only_both_grips_boundaries_and_ads_inspect_precedence(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap']);self.assertEqual(canonical['model'],graph['fallback'])
        case=graph['cases'][0];self.assertEqual(list(FP),case['when']);guard=case['model'];self.assertEqual(canonical['model']['cases'],guard['cases'])
        rg=guard['fallback'];self.assertEqual(1,rg['index']);self.assertEqual(canonical['model'],rg['fallback']);self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        contexts=list(FP)+['thirdperson_righthand','thirdperson_lefthand','gui','ground','fixed','head','none','on_shelf']
        for ctx in contexts:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in (-1,-.001,0,.049,.05,.45,.999,1,1.1):
                        got=resolve(graph,ctx,mode,progress,grip)
                        if ctx not in FP or mode or progress<0:self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got,(ctx,mode,progress,grip))
                        else:
                            i=min(20,math.floor(progress*20+1e-10));suffix='twohand' if grip else 'native'
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{p}_{suffix}' for p in ('body','magazine')),got)
    def test_exact_endpoints_constant_scale_and_bespoke_cell_phase_order(self):
        for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            accepted=read(path)['display']
            for i in range(21):
                for part in ('body','magazine'):
                    c=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json');self.assertEqual({'parent','display'},set(c));self.assertEqual(f'destiny:{KEY}_{part}',c['parent'])
                    for ctx,d in c['display'].items():
                        self.assertEqual(accepted[ctx]['scale'],d['scale'])
                        self.assertTrue(all(math.isfinite(v) for arr in d.values() for v in arr))
                        if ctx not in FP or i in (0,20):self.assertEqual(accepted[ctx],d)
        sample=G['sample'];self.assertGreater(sample(.2)[0][0],60);self.assertEqual([0,0,0],sample(0)[2]);self.assertLess(sample(.43)[2][1],-7);self.assertEqual(sample(.43)[2],sample(.54)[2]);self.assertGreater(sample(.78)[2][1],sample(.66)[2][1]);self.assertEqual([0,0,0],sample(.84)[2]);self.assertEqual([0,0,0],sample(1)[0])
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)
    def test_twelve_inspected_actual_same_weapon_frames_and_authorship_limits(self):
        ref=read(ART/'motion-reference.json');self.assertTrue(ref['inspectedActualFrames']);self.assertTrue(ref['authoredApproximation']);self.assertEqual('https://www.youtube.com/watch?v=10u8PCK4B2c',ref['url']);self.assertEqual('DFP',ref['creator']);self.assertEqual(32,ref['identitySeconds']);self.assertIn('DREAM BREAKER',ref['identityVerification']['evidence']);self.assertEqual(12,len(ref['frames']));self.assertEqual(12,len({f['sha256'] for f in ref['frames']}))
        for f in ref['frames']:
            self.assertEqual(f['sourceFrameIndex']/60,f['timestampSeconds']);self.assertEqual(ref['url'],f['sourceURL']);self.assertTrue(f['observation']);self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest())
            with Image.open(ROOT/f['path']) as im:self.assertEqual((1280,720),im.size)
        self.assertIn('authored',ref['frames'][-1]['observation']);self.assertIn('occluded',ref['authoredHiddenMotion'])
    def test_manifest_exact_output_hashes_ownership_and_master_boundary(self):
        m=read(ART/'manifest.json');self.assertEqual((90,87,84,186,0),tuple(m[k] for k in ('generatedFiles','packFiles','parentDisplayChildren','maxAssembledElements','addedElements')))
        self.assertEqual(90,len(G['expected_output_paths']()));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertEqual(23,m['integration']['masterRoute']);self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['masterOwnsRegistryRuntime'])
        owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w178-manifest.json').read_bytes())['features'] if f['name']=='w178-dream-breaker-reload'))
        self.assertEqual(106,len(owned));self.assertTrue({str(p) for p in G['expected_output_paths']()}<=owned)
        self.assertEqual(owned,{str(p) for p in G['expected_output_paths']()}|{str(ART/f'reference-{i:02}.png') for i in range(12)}|{str(ART/'motion-reference.json'),'scripts/generate_reload_w178_dream_breaker.py','scripts/qa/test_reload_w178_dream_breaker.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW178DreamBreakerTest.java'})
        for p in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/p) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)
if __name__=='__main__':unittest.main(verbosity=2)
