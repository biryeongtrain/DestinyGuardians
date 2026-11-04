#!/usr/bin/env python3
"""Representative scoped W189 checks. Actual codecs/JOML are in ReloadW189ErentilTest."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w189_erentil_fr4.py'))
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

class ReloadW189ErentilTest(unittest.TestCase):
    def test_canonical_partition135_elements810_uvs_gameplay_audio_pins(self):
        s=read(G['SOURCE']);b=read(A/f'models/{KEY}_body.json');c=read(A/f'models/{KEY}_magazine.json');m=read(ART/'manifest.json')
        self.assertEqual(135,len(s['elements']));self.assertEqual(810,sum(len(e['faces']) for e in s['elements']))
        self.assertEqual([e for i,e in enumerate(s['elements']) if i!=16],b['elements'])
        self.assertEqual(s['elements'][16],c['elements'][0]);self.assertEqual(G['cell_core'](s),c['elements'][1:])
        self.assertEqual((134,2,136,135,1,0),tuple(m[k] for k in ('bodyElements','movingElements','maxAssembledElements','endpointAssembledElements','addedElements','triangleAdapterElements')))
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        t=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='erentil_fr4')
        self.assertEqual((5,50,20,5,True,False),tuple(t[k] for k in ('magazine','reloadTicks','chargeTicks','burstSize','sharedBurstAmmo','shellReload')))

    def test_cell_is_connected_whole_sleeve_with_fixed_grip_brace_and_cylinders(self):
        import numpy as np
        s=read(G['SOURCE']);core=G['cell_core'](s)[0];h=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
        base=h['vertices'](s['elements'][16]);sleeve=h['vertices'](core)
        self.assertTrue(np.all(np.minimum(base.max(0),sleeve.max(0))>np.maximum(base.min(0),sleeve.min(0))))
        self.assertEqual(s['elements'][16]['faces'],core['faces']);self.assertGreater(sleeve[:,1].max()-base[:,1].max(),2)
        fixed=read(A/f'models/{KEY}_body.json')['elements'];names={e['name'] for e in fixed}
        self.assertTrue({'Grip_main','Grip_heel','Triangle_lower_brace','Omolon_receiver','Upper_chamber_facet_0','Hose_7.1_0_0'}<=names)
        self.assertEqual([*range(8),*range(11,21)],[i for i in range(21) if G['payload_visible'](i)])

    def test_representative21_samples_both_grips_hands_guards(self):
        canonical=read(G['ITEM']);graph=read(A/f'items/{KEY}.json')['model']
        self.assertEqual(canonical['model'],graph['fallback']);guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases'])
        rg=guard['fallback'];self.assertEqual(1,rg['index']);self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        for ctx in (*FP,'thirdperson_righthand','thirdperson_lefthand','gui','ground','fixed','head'):
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for p in (-.1,*[i/20 for i in range(21)],1.1):
                        got=resolve(graph,ctx,mode,p,grip)
                        if ctx not in FP or mode or p<=0 or p>=1:self.assertEqual(resolve(canonical['model'],ctx,mode,p,grip),got)
                        else:
                            i=round(p*20);parts=('body','magazine') if G['payload_visible'](i) else ('body',);suffix='twohand' if grip else 'native'
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{part}_{suffix}' for part in parts),got)

    def test84_children_canonical_endpoints_nonfp_and_constant_scale(self):
        n=0
        for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            accepted=read(path)['display']
            for i in range(21):
                for part in ('body','magazine'):
                    c=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json');n+=1
                    self.assertEqual({'parent','display'},set(c));self.assertEqual(f'destiny:{KEY}_{part}',c['parent'])
                    for ctx,d in c['display'].items():
                        self.assertEqual(accepted[ctx]['scale'],d['scale']);self.assertTrue(all(math.isfinite(v) for a in d.values() for v in a))
                        if ctx not in FP or i in (0,20):self.assertEqual(accepted[ctx],d)
        self.assertEqual(84,n)

    def test_independent_mechanism_and_positive_lift_in_practical_frame(self):
        sample=G['sample'];self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(0));self.assertEqual(sample(0),sample(1))
        self.assertGreater(sample(.28)[0][0],70);self.assertEqual([0,-2.1,-.64],sample(.28)[2]);self.assertLess(sample(.54)[2][0],-2)
        self.assertLess(sample(.69)[2][1],0);self.assertGreater(sample(.74)[2][1],0);self.assertEqual([0,0,0],sample(.80)[2])
        for p in (.2,.28,.54,.69):self.assertGreater(sample(p)[1][1],2.9)
        w188=runpy.run_path(str(ROOT/'scripts/generate_reload_w188_line_in_the_sand.py'));self.assertNotEqual(w188['KEYS'],G['KEYS']);self.assertNotEqual(w188['GRIP'],G['GRIP'])
        q=G['practical_clearance'](read(G['SOURCE']),read(G['TWOHAND'])['display']);self.assertEqual(46,len(q['points']))
        for row in q['points']:
            for v in row['screenUV']:self.assertTrue(.06<=v<=.94)
        for p in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(p)

    def test_rigid_cell_distances21_samples_both_grips_and_hands(self):
        import numpy as np
        s=read(G['SOURCE']);two=read(G['TWOHAND'])['display'];ps=np.array([[7.48,4.37,1.58],[8.52,7.55,3.1],[8,4.37,3.115]])
        for i in range(21):
            for grip in ('native','twohand'):
                for hand in FP:
                    d=G['pose_display'](s['display'],two,i/20,'magazine',grip)[hand]
                    actual=((ps-8)*d['scale'])@np.array(G['xyz'](d['rotation'])).T+np.array(d['translation'])
                    self.assertAlmostEqual(np.linalg.norm(actual[0]-actual[1]),.85*np.linalg.norm(ps[0]-ps[1]),places=8)

    def test_actual16_frame_pts_rip_provenance_and_authored_limitations(self):
        m=read(ART/'manifest.json');ref=m['reference'];text=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=539XTHi69Pg',ref['url']);self.assertEqual('ThatUnknown',ref['creator']);self.assertEqual([8088,8166],ref['actionFrameRange'])
        self.assertEqual((30000,1001,'1/30000'),tuple(ref[k] for k in ('fpsNumerator','fpsDenominator','sourceTimebase')))
        self.assertEqual(16,len(ref['frames']));self.assertEqual(16,len({f['sha256'] for f in ref['frames']}));self.assertIn('ERENTIL FR4',ref['frames'][0]['observation'])
        for f in ref['frames']:
            self.assertEqual(f['sourceFrameIndex']*1001,f['pts']);self.assertAlmostEqual(f['pts']/30000,f['timestampSeconds']);self.assertIn(f['sha256'],text)
        self.assertEqual((328,336),tuple(m['originalRip'][k] for k in ('vertices','triangles')))
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['sourceLimitation']['fullPayloadSourceFidelityVerified']);self.assertIn('OFFLINE / NO HANDS / NOT NATIVE',text)
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreaterEqual(im.width,1600);self.assertGreater(im.height,1000)

    def test_exact94_owned_paths_hashes_and_model_reference_closure(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren')))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in G['expected_output_paths']()}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w189_erentil_fr4.py','scripts/qa/test_reload_w189_erentil_fr4.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW189ErentilTest.java'}
        self.assertEqual(94,len(exact));self.assertEqual(89,len(m['sha256']))
        def visit(x):
            if isinstance(x,dict):
                if x.get('type')=='minecraft:model':self.assertTrue((ROOT/A/f"models/{x['model'].split(':')[1]}.json").is_file())
                for v in x.values():visit(v)
            elif isinstance(x,list):
                for v in x:visit(v)
        visit(read(A/f'items/{KEY}.json'))
if __name__=='__main__':unittest.main(verbosity=2)
