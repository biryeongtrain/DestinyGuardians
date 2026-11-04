#!/usr/bin/env python3
"""Bounded W188 asset/reference contract tests; runtime lifecycle belongs to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w188_stormchaser.py'))
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
class ReloadW188StormTest(unittest.TestCase):
    def test_canonical95_partition_and_gameplay_audio_pins(self):
        source=read(G['SOURCE']);m=read(ART/'manifest.json');rebuilt={}
        for part,count,original in [('body',89,89),('magazine',7,6)]:
            model=read(A/f'models/{KEY}_{part}.json');self.assertEqual(count,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            self.assertEqual(original,len(m['partitionIndices'][part]))
            for i,el in zip(m['partitionIndices'][part],model['elements']):self.assertNotIn(i,rebuilt);rebuilt[i]=el
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(95)])
        self.assertEqual(570,sum(len(e['faces']) for e in rebuilt.values()))
        self.assertEqual((95,89,7,96,1,0),tuple(m[k] for k in ('sourceElements','bodyElements','movingElements','maxAssembledElements','addedElements','triangleAdapterElements')))
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        t=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='stormchaser')
        self.assertEqual((5,49,533,11,3,True,False),tuple(t[k] for k in ('magazine','reloadTicks','chargeMillis','chargeTicks','burstSize','sharedBurstAmmo','shellReload')))
        audio=next(x for x in read(Path('src/main/resources/destiny/sounds/w63-reload.json'))['entries'] if x['id']=='stormchaser');self.assertEqual(49,audio['ticks'])

    def test_complete_six_element_heel_not_receiver_plate(self):
        mag=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements'];source=read(G['SOURCE'])
        self.assertEqual(list(G['MAGAZINE_NAMES'])+['reload_battery_stem'],[e['name'] for e in mag])
        self.assertEqual(list(range(80,86)),read(ART/'manifest.json')['partitionIndices']['magazine'])
        self.assertEqual(source['elements'][80:86],mag[:6])
        self.assertTrue(set(read(ART/'manifest.json')['semanticGroups']['fixed'])<={e['name'] for e in body})
        self.assertLessEqual(len(body)+len(mag),1000)

    def test_stem_hidden_inside_original_grip_and_contacts_battery_crown(self):
        import numpy as np,itertools
        source=read(G['SOURCE']);stem=G['reload_shaft'](source)[0];grip=source['elements'][76]
        self.assertEqual(grip['faces'],stem['faces']);self.assertEqual(grip['rotation'],stem['rotation'])
        self.assertTrue(all(a<=c<d<=b for a,b,c,d in zip(grip['from'],grip['to'],stem['from'],stem['to'])))
        def rotation(el):
            rr=el.get('rotation',{});angles=[rr.get(a,0) for a in 'xyz']
            if 'axis' in rr:angles['xyz'.index(rr['axis'])]=rr['angle']
            return np.array(G['xyz'](angles))
        def inside(el,p):
            o=np.array(el.get('rotation',{}).get('origin',[8]*3));q=(p-o)@rotation(el)+o
            return bool(np.all(q>=np.array(el['from'])-1e-6) and np.all(q<=np.array(el['to'])+1e-6))
        origin=np.array(stem['rotation']['origin']);contacts=0
        for v in itertools.product(*[np.linspace(a,b,9) for a,b in zip(stem['from'],stem['to'])]):
            pt=(np.array(v)-origin)@rotation(stem).T+origin
            self.assertTrue(inside(grip,pt));contacts+=int(any(inside(e,pt) for e in source['elements'][80:86]))
        self.assertGreater(contacts,0)
        self.assertFalse(read(ART/'manifest.json')['sourceLimitation']['exactOriginalShaftFidelityVerified'])

    def test_graph21_samples_both_hands_grips_and_canonical_fallbacks(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap'])
        self.assertEqual(canonical['model'],graph['fallback']);self.assertEqual(list(FP),graph['cases'][0]['when'])
        guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases'])
        rg=guard['fallback'];self.assertEqual(1,rg['index']);self.assertEqual(canonical['model'],rg['fallback'])
        self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        for ctx in read(G['SOURCE'])['display']:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in (-1,0,.05,.35,.6,.95,1,1.5):
                        got=resolve(graph,ctx,mode,progress,grip)
                        if ctx not in FP or mode or progress<=0 or progress>=1:self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got)
                        else:
                            i=math.floor(progress*20+1e-10);suffix='twohand' if grip else 'native'
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{part}_{suffix}' for part in ('body','magazine')),got)
        for i,e in enumerate(rg['entries']):
            if i in (0,20):self.assertEqual(canonical['model'],e['model'])
            else:self.assertEqual(('minecraft:custom_model_data',0),(e['model']['property'],e['model']['index']))

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

    def test_independent_steep_lift_axis_exchange_seat_and_fast_lower(self):
        sample=G['sample'];self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(0));self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(1))
        self.assertEqual([73,-10,-15],sample(.22)[0]);self.assertEqual([-.9,-5.2,2.282],sample(.49)[2])
        self.assertEqual([-1.4,-1.2,-2.8],sample(.49)[1]);self.assertGreater(sample(.58)[2][1],sample(.49)[2][1]);self.assertEqual([0,0,0],sample(.75)[2])
        self.assertLess(sample(.88)[0][0],sample(.79)[0][0])
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)
        # Axial withdrawal must clear the stem from the fixed pistol grip.
        import numpy as np,itertools
        neck=G['reload_shaft'](read(G['SOURCE']))[0];rr=neck['rotation'];o=np.array(rr['origin']);rot=np.array(G['xyz']([rr['angle'],0,0]))
        points=np.array([(np.array(v)-o)@rot.T+o+sample(.49)[2] for v in itertools.product(*zip(neck['from'],neck['to']))])
        self.assertLess(points[:,1].max(),5.1)

    def test_rigid_payload_distances_all_four_fp_configurations(self):
        import numpy as np
        source=read(G['SOURCE']);two=read(G['TWOHAND'])['display'];points=np.array([[7.73,8.02,6.55],[8.27,8.50,9.62],[8.625,6.72,8.93]])
        for p in (.2,.35,.6,.9):
            for grip in ('native','twohand'):
                for hand in FP:
                    d=G['pose_display'](source['display'],two,p,'magazine',grip)[hand]
                    actual=((points-8)*d['scale'])@np.array(G['xyz'](d['rotation'])).T+np.array(d['translation'])
                    for i,j in ((0,1),(1,2),(0,2)):self.assertAlmostEqual(np.linalg.norm(actual[i]-actual[j]),.85*np.linalg.norm(points[i]-points[j]),places=8)

    def test_actual_source_pts_hashes_rip_and_offline_evidence(self):
        m=read(ART/'manifest.json');ref=m['reference'];source=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=Ev71jjG4JbQ',ref['url']);self.assertEqual('Ehroar',ref['creator']);self.assertTrue(ref['inspectedActualFrames'])
        self.assertEqual([26872,27000],ref['actionFrameRange']);self.assertEqual((60000,1001,'1/60000'),tuple(ref[k] for k in ('fpsNumerator','fpsDenominator','sourceTimebase')))
        self.assertEqual(16,len(ref['frames']));self.assertEqual(16,len({f['sha256'] for f in ref['frames']}));self.assertIn('STORMCHASER',ref['frames'][0]['observation'])
        for f in ref['frames']:
            self.assertAlmostEqual(f['sourceFrameIndex']*1001/60000,f['timestampSeconds']);self.assertEqual(f['sourceFrameIndex']*1001,f['pts']);self.assertIn(f['sha256'],source)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertTrue(m['ripProvenance']['inertFbxBlendCompared']);self.assertEqual(29718,m['ripProvenance']['acceptedTriangles']);self.assertIn('OFFLINE',source)
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)

    def test_exact94_paths_references_and_manifest_hashes(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren')));self.assertEqual(90,len(G['expected_output_paths']()));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in G['expected_output_paths']()}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w188_stormchaser.py','scripts/qa/test_reload_w188_stormchaser.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW188StormTest.java'};self.assertEqual(94,len(exact))
        def visit(x):
            if isinstance(x,dict):
                if x.get('type')=='minecraft:model':
                    ns,path=x['model'].split(':');self.assertEqual('destiny',ns);self.assertTrue((ROOT/A/f'models/{path}.json').is_file(),path)
                for v in x.values():visit(v)
            elif isinstance(x,list):
                for v in x:visit(v)
        visit(read(A/f'items/{KEY}.json'))

if __name__=='__main__':unittest.main(verbosity=2)
