#!/usr/bin/env python3
"""Bounded Coriolis W189 assets, exact source preservation and mechanism tests."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w189_coriolis_force.py'))
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

class ReloadW189CoriolisTest(unittest.TestCase):
    def test_canonical104_partition_all_geometry_uv_display_preserved(self):
        source=read(G['SOURCE']);m=read(ART/'manifest.json');rebuilt={}
        for part,count in [('body',102),('magazine',2)]:
            model=read(A/f'models/{KEY}_{part}.json');self.assertEqual(count,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            self.assertEqual(count,len(m['partitionIndices'][part]))
            for i,e in zip(m['partitionIndices'][part],model['elements']):self.assertNotIn(i,rebuilt);rebuilt[i]=e
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(104)])
        self.assertEqual(624,sum(len(e['faces']) for e in rebuilt.values()))
        self.assertEqual((104,102,2,104,0,0),tuple(m[k] for k in ('sourceElements','bodyElements','movingElements','maxAssembledElements','addedElements','triangleAdapterElements')))

    def test_complete_central_cell_and_fixed_surround_not_grip_battery(self):
        mag=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements']
        self.assertEqual(list(G['MAGAZINE_NAMES']),[e['name'] for e in mag])
        self.assertEqual([60,61],read(ART/'manifest.json')['partitionIndices']['magazine'])
        self.assertTrue(set(read(ART/'manifest.json')['semanticGroups']['fixed'])<={e['name'] for e in body})
        self.assertEqual(104,len(body)+len(mag));self.assertLessEqual(len(body)+len(mag),1000)

    def test_gameplay_audio_ads_and_canonical_hash_pins(self):
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        t=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='coriolis_force')
        self.assertEqual((6,45,667,14,7,True,False),tuple(t[k] for k in ('magazine','reloadTicks','chargeMillis','chargeTicks','burstSize','sharedBurstAmmo','shellReload')))
        audio=next(x for x in read(Path('src/main/resources/destiny/sounds/w63-reload.json'))['entries'] if x['id']=='coriolis_force');self.assertEqual(45,audio['ticks'])

    def test_graph21_samples_exact0_1_negative_overshoot_nonfp_ads_inspect(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap'])
        self.assertEqual(canonical['model'],graph['fallback']);self.assertEqual(list(FP),graph['cases'][0]['when'])
        guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases'])
        rg=guard['fallback'];self.assertEqual(1,rg['index']);self.assertEqual(canonical['model'],rg['fallback'])
        self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        cases=0
        for ctx in read(G['SOURCE'])['display']:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in (-1,0,.05,.35,.6,.95,1,1.5):
                        got=resolve(graph,ctx,mode,progress,grip);cases+=1
                        if ctx not in FP or mode or progress<=0 or progress>=1:self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got)
                        else:
                            i=math.floor(progress*20+1e-10);suffix='twohand' if grip else 'native'
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{part}_{suffix}' for part in ('body','magazine')),got)
        self.assertEqual(384,cases)

    def test84_children_constant_scale_exact_endpoints_nonfp(self):
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

    def test_independent_cell_motion_full_clearance_and_reseat(self):
        sample=G['sample'];zeros=tuple([0,0,0] for _ in range(5));self.assertEqual(zeros,sample(0));self.assertEqual(zeros,sample(1))
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)
        source=read(G['SOURCE']);parts=G['partition'](source)
        points=G['geometry_points'](parts['magazine']);anchor=np.array(G['MAGAZINE_ANCHOR'])
        _,_,offset,angles,_=sample(.47);clear=(points-anchor)@np.array(G['xyz'](angles)).T+anchor+offset
        # Entire outgoing cell clears the original fixed red floor (Y5.63) before replacement.
        self.assertLess(clear[:,1].max(),5.63)
        self.assertEqual([0,0,0],sample(.74)[2]);self.assertEqual([0,0,0],sample(.74)[3])
        self.assertNotEqual(sample(.36)[3],[0,0,0]);self.assertLess(sample(.90)[0][0],sample(.74)[0][0])
        self.assertLess(max(k[1][0] for k in G['KEYS']),60) # Coriolis-specific medium lift, not W188's76-degree hold.

    def test_rigid_cell_distances_all21_samples_hands_and_grips(self):
        source=read(G['SOURCE']);two=read(G['TWOHAND'])['display'];points=np.array([[7.562,5.795,-2.19],[8.438,11.045,2.23],[8,10.95,-.52]])
        for i in range(21):
            for grip in ('native','twohand'):
                for hand in FP:
                    d=G['pose_display'](source['display'],two,i/20,'magazine',grip)[hand]
                    actual=((points-8)*d['scale'])@np.array(G['xyz'](d['rotation'])).T+np.array(d['translation'])
                    for a,b in ((0,1),(1,2),(0,2)):self.assertAlmostEqual(np.linalg.norm(actual[a]-actual[b]),.85*np.linalg.norm(points[a]-points[b]),places=8)

    def test_practical_perspective_proxy_all_exchange_cell_corners(self):
        m=read(ART/'manifest.json');proxy=m['viewportProxy'];self.assertEqual(48,len(proxy['samples']))
        self.assertEqual(1,proxy['minVisibleCornerFraction'])
        for row in proxy['samples']:self.assertEqual(row['corners'],row['visibleCorners'])
        self.assertFalse(m['nativeGameplayVerified'])

    def test_actual_same_weapon_pts_provenance_and_offline_rasters(self):
        m=read(ART/'manifest.json');ref=m['reference'];source=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=67wv69MomYQ',ref['url']);self.assertEqual('Ironworker Gaming',ref['creator']);self.assertTrue(ref['inspectedActualFrames'])
        self.assertEqual([772,856],ref['actionFrameRange']);self.assertEqual((60,1,'1/15360'),tuple(ref[k] for k in ('fpsNumerator','fpsDenominator','sourceTimebase')))
        self.assertEqual(16,len(ref['frames']));self.assertEqual(16,len({f['sha256'] for f in ref['frames']}));self.assertIn('CORIOLIS FORCE',ref['frames'][-1]['observation'])
        for f in ref['frames']:
            self.assertAlmostEqual(f['sourceFrameIndex']/60,f['timestampSeconds']);self.assertEqual(f['sourceFrameIndex']*256,f['pts']);self.assertIn(f['sha256'],source)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertTrue(m['ripProvenance']['inertBlendRead']);self.assertEqual(13801,m['ripProvenance']['acceptedTriangles']);self.assertFalse(m['ripProvenance']['cellStoredAsSeparateObject']);self.assertIn('OFFLINE',source)
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)

    def test_exact94_owned_paths_refs_and_deterministic_manifest_hashes(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren')));self.assertEqual(90,len(G['expected_output_paths']()));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in G['expected_output_paths']()}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w189_coriolis_force.py','scripts/qa/test_reload_w189_coriolis_force.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW189CoriolisTest.java'};self.assertEqual(94,len(exact))
        def visit(x):
            if isinstance(x,dict):
                if x.get('type')=='minecraft:model':
                    ns,path=x['model'].split(':');self.assertEqual('destiny',ns);self.assertTrue((ROOT/A/f'models/{path}.json').is_file(),path)
                for v in x.values():visit(v)
            elif isinstance(x,list):
                for v in x:visit(v)
        visit(read(A/f'items/{KEY}.json'))

if __name__=='__main__':unittest.main(verbosity=2)
