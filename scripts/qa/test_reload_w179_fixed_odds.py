#!/usr/bin/env python3
"""Focused W179 Fixed Odds asset regression; runtime hooks/lifecycle belong to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w179_fixed_odds.py'))
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

class ReloadW179FixedOddsTest(unittest.TestCase):
    def test_canonical_partition_preserves_153_elements_uv_texture_display_and_data(self):
        source=read(G['SOURCE']);m=read(ART/'manifest.json');rebuilt={}
        for part,count in [('body',114),('magazine',39)]:
            model=read(A/f'models/{KEY}_{part}.json');self.assertEqual(count,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            for i,e in zip(m['partitionIndices'][part],model['elements']):self.assertNotIn(i,rebuilt);rebuilt[i]=e
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(153)])
        self.assertEqual((153,0,0),(m['maxAssembledElements'],m['addedElements'],m['triangleAdapterElements']))
        self.assertLessEqual(m['maxAssembledElements'],1000)
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='fixed_odds')
        self.assertEqual((44,106,360,1),tuple(timing[k] for k in ('magazine','reloadTicks','rpm','burstSize')))

    def test_complete_connected_belt_and_box_share_one_rigid_payload(self):
        payload=read(A/f'models/{KEY}_magazine.json')['elements'];es={e['name']:e for e in payload}
        self.assertEqual(5,len([n for n in es if n.startswith('ammo_box_')]))
        self.assertEqual(28,len([n for n in es if n.startswith('belt_')]))
        self.assertEqual(6,len([n for n in es if n.startswith('feed_join_')]))
        # Six physical links join adjacent canonical cartridge links, not free bullets.
        for i in range(6):
            e=es[f'feed_join_{i}'];o=e['rotation']['origin'];a=math.radians(e['rotation']['z']);half=(e['to'][0]-e['from'][0])/2
            for sign,j in [(-1,i),(1,i+1)]:
                point=[o[0]+sign*half*math.cos(a),o[1]+sign*half*math.sin(a),o[2]];link=es[f'belt_link_{j}']
                self.assertTrue(all(link['from'][k]-.03<=point[k]<=link['to'][k]+.03 for k in range(3)),(i,j,point))
        tail=es['belt_link_6'];center=[(a+b)/2 for a,b in zip(tail['from'],tail['to'])]
        self.assertTrue(all(a<v<b for a,v,b in zip([8.52,7.98,3.18],center,[12.44,9.79,6.03])))
        for i in (0,4,8,14,18,20):
            for grip in ('native','twohand'):
                c=read(A/f'models/{KEY}_{i:02}_magazine_{grip}.json')
                self.assertNotIn('elements',c);self.assertEqual(f'destiny:{KEY}_magazine',c['parent'])

    def test_representative_cover_then_box_feed_close_charge_and_only_original_solids(self):
        body=read(A/f'models/{KEY}_body.json')['elements'];base={e['name']:e for e in body}
        for i in (4,8,14,18):
            c=read(A/f'models/{KEY}_{i:02}_body_native.json');es=c.get('elements',body)
            self.assertEqual(list(base),[e['name'] for e in es])
            for e in es:
                old=base[e['name']]
                self.assertEqual(old['faces'],e['faces'])
                for a,b,c0,d in zip(e['from'],e['to'],old['from'],old['to']):self.assertAlmostEqual(b-a,d-c0,places=6)
                if e['name'] not in G['COVER_NAMES']+G['BOLT_NAMES']:self.assertEqual(old,e)
            if i in (4,8,14):
                cover=next(e for e in es if e['name']=='feed_roof');self.assertLess(cover['rotation']['x'],-100)
        sample=G['sample'];self.assertEqual([0,0,0],sample(.2)[2]);self.assertEqual(-103,sample(.2)[3]);self.assertGreater(sample(.4)[2][0],3)
        self.assertEqual(sample(.4)[2],sample(.48)[2]);self.assertEqual([0,0,0],sample(.68)[2]);self.assertEqual(-103,sample(.74)[3])
        self.assertEqual(0,sample(.82)[3]);self.assertEqual(0,sample(.82)[4]);self.assertGreater(sample(.89)[4],1);self.assertEqual(0,sample(.94)[4])
        for bad in (-.1,1.1,float('nan')):
            with self.assertRaises(ValueError):sample(bad)

    def test_exact_endpoints_both_contexts_grips_and_constant_scale(self):
        for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            accepted=read(path)['display']
            for i in (0,4,8,14,18,20):
                for part in ('body','magazine'):
                    c=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    for context,d in c['display'].items():
                        self.assertEqual(accepted[context]['scale'],d['scale']);self.assertTrue(all(math.isfinite(v) for arr in d.values() for v in arr))
                        if context not in FP or i in (0,20):self.assertEqual(accepted[context],d)
                    if i in (0,20):self.assertNotIn('elements',c)

    def test_item_graph_fp_only_exact_nonfp_and_ads_inspect_fallback(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap']);self.assertEqual(canonical['model'],graph['fallback'])
        guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases']);rg=guard['fallback']
        self.assertEqual(1,rg['index']);self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        for ctx in list(FP)+['thirdperson_righthand','thirdperson_lefthand','gui','ground','fixed','head','none']:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in (-1,0,.049,.05,.4,.999,1,1.1):
                        got=resolve(graph,ctx,mode,progress,grip)
                        if ctx not in FP or mode or progress<0:self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got)
                        else:
                            i=min(20,math.floor(progress*20+1e-10));suffix='twohand' if grip else 'native'
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{p}_{suffix}' for p in ('body','magazine')),got)

    def test_reference_documentation_manifest_hashes_and_exact_owned_set(self):
        m=read(ART/'manifest.json');ref=m['reference'];self.assertEqual('https://www.youtube.com/watch?v=cy3DRqtgKC8',ref['url']);self.assertEqual(12,len(ref['frames']))
        for f in ref['frames']:self.assertEqual(f['sourceFrameIndex']/60,f['timestampSeconds']);self.assertTrue(f['observation']);self.assertEqual(64,len(f['sha256']))
        self.assertEqual((90,87,84,153),(m['generatedFiles'],m['packFiles'],m['parentDisplayChildren'],m['maxAssembledElements']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited'])
        owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w179-manifest.json').read_bytes())['features'] if f['name']=='w179-fixed-odds'))
        extra={'scripts/generate_reload_w179_fixed_odds.py','scripts/qa/test_reload_w179_fixed_odds.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW179FixedOddsTest.java',str(ART/'SOURCE.md')}
        self.assertEqual(94,len(owned));self.assertEqual(owned,{str(p) for p in G['expected_output_paths']()}|extra)
        source=(ROOT/ART/'SOURCE.md').read_text();self.assertIn('DEFAULT',source);self.assertIn('authored interpretations',source);self.assertIn('No native success',source)
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)
if __name__=='__main__':unittest.main(verbosity=2)
