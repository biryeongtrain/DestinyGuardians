#!/usr/bin/env python3
"""Targeted Farewell source-led motion asset acceptance. No native/client/runtime claim."""
import hashlib,json,math,runpy,unittest,itertools
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w184_farewell.py'))
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
def matrix(a):
    x,y,z=np.radians(a)
    rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
    ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
    rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
    return rx@ry@rz
class ReloadW184FarewellTest(unittest.TestCase):
    def test_exact_canonical_115_partition_uv_paint_and_gameplay_pins(self):
        source=read(G['SOURCE']);m=read(ART/'manifest.json');rebuilt={}
        for part,count in [('body',106),('magazine',9)]:
            model=read(A/f'models/{KEY}_{part}.json');self.assertEqual(count+(3 if part=='magazine' else 0),len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            for i,e in zip(m['partitionIndices'][part],model['elements']):
                self.assertNotIn(i,rebuilt);rebuilt[i]=e
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(115)])
        self.assertEqual((118,3,0),(m['maxAssembledElements'],m['addedElements'],m['triangleAdapterElements']))
        self.assertLessEqual(m['maxAssembledElements'],1000)
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='farewell')
        self.assertEqual((15,32,360,1,3.333333333333,False),tuple(timing[k] for k in ('magazine','reloadTicks','rpm','burstSize','cadenceTicks','shellReload')))

    def test_whole_magazine_heel_loop_shaft_and_fixed_grip(self):
        body=read(A/f'models/{KEY}_body.json')['elements'];mag=read(A/f'models/{KEY}_magazine.json')['elements']
        self.assertEqual('heel',mag[0]['name']);self.assertEqual(12,len(mag));self.assertEqual(G['reload_shaft'](read(G['SOURCE'])),mag[9:]);names={e['name'] for e in body}
        for name in ('grip_shoulder','grip_core','palm_panel_-1','palm_panel_1','backstrap','blade_body','rear_sight_floor'):self.assertIn(name,names)
        m=read(ART/'manifest.json');self.assertFalse(m['sourceLimitation']['fullMagazineFidelityBlocked']);self.assertEqual((118,115),(m['maxAssembledElements'],m['endpointAssembledElements']))
        self.assertEqual(list(range(81,90)),m['partitionIndices']['magazine'])
        self.assertEqual([*range(81),*range(90,115)],m['partitionIndices']['body'])

    def test_shaft_grip_bounds_heel_overlap_existing_uv_and_full_extraction(self):
        source=read(G['SOURCE']);grip=source['elements'][78]
        for e in G['reload_shaft'](source):
            self.assertEqual(grip['rotation'],e['rotation']);self.assertEqual(source['elements'][81]['faces'],e['faces'])
            for corner in itertools.product(*zip(e['from'],e['to'])):
                # Identical element pivot/axis means containment can be tested in shared local frame.
                lower=np.array(grip['from']);lower[1]-=.071 if e['name']=='magazine_shaft_core' else 0
                self.assertTrue(np.all(np.array(corner)>=lower))
                self.assertTrue(np.all(np.array(corner)<=np.array(grip['to'])))
        # The shaft physically overlaps the heel, not merely a shared transform.
        point=np.array([8,7.20,8.30]);heel=source['elements'][81];core=G['reload_shaft'](source)[0]
        self.assertTrue(np.all(point>np.array(heel['from'])) and np.all(point<np.array(heel['to'])))
        origin=np.array(grip['rotation']['origin']);local=matrix((-14.00158177855961,0,0)).T@(point-origin)+origin
        self.assertTrue(np.all(local>np.array(core['from'])) and np.all(local<np.array(core['to'])))
        self.assertFalse(read(ART/'manifest.json')['sourceLimitation']['exactOriginalShaftFidelityVerified'])
        # Fully clear a3.72unit shaft, including heel, along grip axis at max withdrawal.
        offset=np.array(G['sample'](.5)[2]);axis=matrix((-14.00158177855961,0,0))@np.array([0,1,0])
        self.assertLess(np.dot(offset,axis),-5.4)
        graph=read(A/f'items/{KEY}.json')['model']['cases'][0]['model']['fallback'];canonical=read(G['ITEM'])['model']
        self.assertEqual(canonical,graph['entries'][0]['model']);self.assertEqual(canonical,graph['entries'][20]['model'])

    def test_unique_farewell_raise_exchange_insert_wrist_roll_order(self):
        s=G['sample'];self.assertEqual([0,0,0],s(.2)[2]);self.assertEqual([-.1,-1.7,.424],s(.3)[2])
        self.assertEqual([-.8,-5.4,1.346],s(.5)[2]);self.assertLess(s(.6)[2][1],0)
        self.assertEqual([0,0,0],s(.72)[2]);self.assertLess(s(.4)[0][1],0)
        self.assertLess(s(.86)[0][2],s(.72)[0][2]);self.assertGreater(s(.93)[0][0],s(.86)[0][0])
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),s(1))
        for bad in (-.1,1.1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):s(bad)
        old=runpy.run_path(str(ROOT/'scripts/generate_reload_w183_high_albedo.py'))
        self.assertNotEqual(old['KEYS'],G['KEYS'])

    def test_exact_endpoints_nonfp_displays_and_all21_constant_scales(self):
        for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            accepted=read(path)['display']
            for i in range(21):
                for part in ('body','magazine'):
                    c=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    for context,d in c['display'].items():
                        self.assertEqual(accepted[context]['scale'],d['scale']);self.assertTrue(all(math.isfinite(v) for arr in d.values() for v in arr))
                        if context not in FP or i in (0,20):self.assertEqual(accepted[context],d)

    def test_graph_both_contexts_grips_21_thresholds_and_exact_canonical_guards(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap']);self.assertEqual(canonical['model'],graph['fallback'])
        guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases']);rg=guard['fallback']
        self.assertEqual(1,rg['index']);self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        # Representative guards and frame selection; no exhaustive permutations.
        cases=[(FP[0],'',.4,False),(FP[1],'',.6,True),(FP[0],'',0,True),(FP[1],'',1,False),
               (FP[0],'ads',.4,True),(FP[1],'inspect',.8,False),(FP[0],'',-1,False),
               ('thirdperson_righthand','',.4,True),('gui','',.8,False),('ground','',.2,True),
               ('fixed','ads',.4,False),('head','',.4,True),('none','',.6,False)]
        for ctx,mode,progress,grip in cases:
            got=resolve(graph,ctx,mode,progress,grip)
            if ctx not in FP or mode or progress<0 or progress==0 or progress>=1:self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got)
            else:
                i=min(20,math.floor(progress*20+1e-10));suffix='twohand' if grip else 'native'
                self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{p}_{suffix}' for p in ('body','magazine')),got)

    def test_independent_representative_rigid_anchor_matrix_and_grip_carrier(self):
        native=read(G['SOURCE'])['display'];two=read(G['TWOHAND'])['display'];pivot=np.array(G['GRIP'])-8
        for i in (0,6,8,16,20):
            angles,shift,offset=G['sample'](i/20);motion=matrix(angles)
            for grip in ('native','twohand'):
                for hand in FP:
                    idle=native[hand];accepted=(native if grip=='native' else two)[hand]
                    base=matrix(idle['rotation']);carrier=matrix(accepted['rotation'])@base.T
                    for part in ('body','magazine'):
                        d=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')['display'][hand]
                        for point in ([G['MAGAZINE_ANCHOR'],(7.58,7.23,7.57),(8.42,10.95,8.85)] if part=='magazine' else [G['GRIP'],(8,13.16,-1.68),(8,12.92,8.23)]):
                            anchor=np.array(point)-8
                            local=pivot+motion@(anchor-pivot+(np.array(offset) if part=='magazine' else 0))
                            expected=carrier@(np.array(idle['translation'])+shift+base@(local*.85))+np.array(accepted['translation'])-carrier@idle['translation']
                            actual=np.array(d['translation'])+matrix(d['rotation'])@(anchor*np.array(d['scale']))
                            np.testing.assert_allclose(expected,actual,atol=1e-7,rtol=0)

    def test_pack_references_exist_all_json_parse_and_no_new_geometry_fields(self):
        count=0
        for p in G['expected_output_paths']():
            if p.suffix=='.json' and str(p).startswith(str(A)):
                node=read(p);count+=1
                def walk(x):
                    if isinstance(x,dict):
                        for k,v in x.items():
                            if k in ('parent','model') and isinstance(v,str) and v.startswith('destiny:'+KEY):self.assertTrue((ROOT/A/('models/'+v.removeprefix('destiny:')+'.json')).is_file(),v)
                            self.assertNotIn(k,('vertices','triangles','mesh'));walk(v)
                    elif isinstance(x,list):
                        for v in x:walk(v)
                walk(node)
        self.assertEqual(87,count)

    def test_core_regeneration_is_byte_deterministic(self):
        one=G['generate']();two=G['generate']();self.assertEqual(one,two)
        for path,data in one.items():self.assertEqual((ROOT/path).read_bytes(),data,str(path))

    def test_same_weapon_reference_exact_timestamps_and_optional_retained_media(self):
        m=read(ART/'manifest.json');ref=m['reference'];self.assertEqual('https://www.youtube.com/watch?v=2VaZGMrEfjQ',ref['url'])
        self.assertEqual('20210514',ref['uploadDate']);self.assertIn('Farewell',ref['title']);self.assertEqual(12,len(ref['frames']))
        self.assertEqual((60000,1001,'1/60000'),(ref['fpsNumerator'],ref['fpsDenominator'],ref['sourceTimebase']))
        for f in ref['frames']:
            self.assertAlmostEqual(f['sourceFrameIndex']*1001/60000,f['timestampSeconds'],places=9);self.assertTrue(f['observation']);self.assertEqual(64,len(f['sha256']))
            path=Path(f['path'])
            if path.exists():self.assertEqual(f['sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
        for field,file in [('sourceVideoSha256','farewell-reference.mp4'),('sourceMetadataSha256','farewell-reference.info.json')]:
            path=Path('/private/tmp/w184-farewell-report')/file
            if path.exists():self.assertEqual(ref[field],hashlib.sha256(path.read_bytes()).hexdigest())
        source=(ROOT/ART/'SOURCE.md').read_text();self.assertIn('No independently resolved bolt motion animated',source)
        self.assertIn('Exact dimensions',source);self.assertIn('24.290933',source)

    def test_evidence_authorship_hashes_and_exact94_owned_files(self):
        m=read(ART/'manifest.json');self.assertEqual((90,87,84,118),(m['generatedFiles'],m['packFiles'],m['parentDisplayChildren'],m['maxAssembledElements']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertEqual('farewell',m['integration']['catalogId'])
        owned={str(p) for p in G['expected_output_paths']()}|{'scripts/generate_reload_w184_farewell.py','scripts/qa/test_reload_w184_farewell.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW184FarewellTest.java',str(ART/'SOURCE.md')}
        self.assertEqual(94,len(owned));self.assertTrue(all((ROOT/p).is_file() for p in owned))
        manifest=Path('/private/tmp/w184-manifest.json')
        if manifest.exists():self.assertEqual(owned,set(next(f['owned_paths'] for f in json.loads(manifest.read_bytes())['features'] if f['name']=='w184-farewell')))
        source=(ROOT/ART/'SOURCE.md').read_text();self.assertIn('authored interpretations',source);self.assertIn('No native success',source);self.assertIn('24.290933',source)
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)
if __name__=='__main__':unittest.main(verbosity=2)
