#!/usr/bin/env python3
"""Targeted IKELOS v1.0.1 asset acceptance. No native/client/runtime claim."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w182_ikelos_smg_v1_0_1.py'))
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
class ReloadW182IkelosTest(unittest.TestCase):
    def test_exact_canonical_133_partition_uv_dye_and_unchanged_gameplay_assets(self):
        source=read(G['SOURCE']);m=read(ART/'manifest.json');rebuilt={}
        for part,count in [('body',132),('magazine',1)]:
            model=read(A/f'models/{KEY}_{part}.json');self.assertEqual(count,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            for i,e in zip(m['partitionIndices'][part],model['elements']):
                self.assertNotIn(i,rebuilt);rebuilt[i]=e
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(133)])
        self.assertEqual((133,0,0),(m['maxAssembledElements'],m['addedElements'],m['triangleAdapterElements']))
        self.assertLessEqual(m['maxAssembledElements'],1000)
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='ikelos_smg_v1_0_1')
        self.assertEqual((32,45,720,1,1.666666666667,False),tuple(timing[k] for k in ('magazine','reloadTicks','rpm','burstSize','cadenceTicks','shellReload')))

    def test_only_complete_grip_magazine_is_payload_cells_wiring_and_knob_stay_body(self):
        body=read(A/f'models/{KEY}_body.json')['elements'];mag=read(A/f'models/{KEY}_magazine.json')['elements']
        self.assertEqual(['magazine'],[e['name'] for e in mag]);names={e['name'] for e in body}
        for name in ('magazine_well','charging_handle_stem','charging_handle_knob','lower_swivel_cap_1','cell_3_1','cell_lead_0_-1','sight_base','ribbed_foregrip'):self.assertIn(name,names)
        self.assertEqual(8,sum(e['name'].startswith('cell_') and not e['name'].startswith(('cell_socket','cell_lead','cell_saddle')) for e in body))
        for i in range(21):
            for part in ('body','magazine'):
                for grip in ('native','twohand'):
                    c=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    self.assertEqual({'parent','display'},set(c));self.assertEqual(f'destiny:{KEY}_{part}',c['parent'])

    def test_observed_lift_exchange_insert_palmseat_order_no_fabricated_bolt(self):
        s=G['sample'];self.assertEqual([0,0,0],s(0)[2]);self.assertGreater(s(.22)[0][0],50)
        self.assertEqual([0,-4.8,.3],s(.34)[2]);self.assertEqual(s(.34)[2],s(.46)[2])
        self.assertLess(s(.62)[2][1],0);self.assertEqual([0,0,0],s(.70)[2])
        self.assertGreater(s(.76)[0][0],s(.70)[0][0]);self.assertLess(s(.80)[0][0],s(.76)[0][0])
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),s(1))
        for bad in (-.1,1.1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):s(bad)

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
        for ctx in list(FP)+['thirdperson_righthand','thirdperson_lefthand','gui','ground','fixed','head','none']:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in [-1,-.0001]+[i/20 for i in range(21)]+[.049,.499,.999,1.1]:
                        got=resolve(graph,ctx,mode,progress,grip)
                        if ctx not in FP or mode or progress<0:self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got)
                        else:
                            i=min(20,math.floor(progress*20+1e-10));suffix='twohand' if grip else 'native'
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{p}_{suffix}' for p in ('body','magazine')),got)

    def test_independent_all21_rigid_anchor_matrix_scale_and_grip_carrier(self):
        native=read(G['SOURCE'])['display'];two=read(G['TWOHAND'])['display'];pivot=np.array(G['GRIP'])-8
        for i in range(21):
            angles,shift,offset=G['sample'](i/20);motion=matrix(angles)
            for grip in ('native','twohand'):
                for hand in FP:
                    idle=native[hand];accepted=(native if grip=='native' else two)[hand]
                    base=matrix(idle['rotation']);carrier=matrix(accepted['rotation'])@base.T
                    for part in ('body','magazine'):
                        d=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')['display'][hand]
                        for point in ([G['MAGAZINE_ANCHOR'],(7.655,3.38466275,7.7),(8.345,5.77,8.82)] if part=='magazine' else [G['GRIP'],(8,12.16,0),(8,10.25,17.7)]):
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

    def test_original2018_reference_frame_rational_timestamps_and_hashes(self):
        m=read(ART/'manifest.json');ref=m['reference'];self.assertEqual('https://www.youtube.com/watch?v=pJdMgzVISnM',ref['url'])
        self.assertEqual('20180518',ref['uploadDate']);self.assertIn('v1.0.1',ref['title']);self.assertEqual(12,len(ref['frames']))
        for f in ref['frames']:
            self.assertAlmostEqual(f['sourceFrameIndex']*1001/60000,f['timestampSeconds'],places=9);self.assertTrue(f['observation']);self.assertEqual(64,len(f['sha256']))
            path=Path(f['path'])
            if path.exists():self.assertEqual(f['sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
        for field,file in [('sourceVideoSha256','original.mp4'),('sourceMetadataSha256','original.info.json')]:
            path=Path('/private/tmp/w182-ikelos-report')/file
            if path.exists():self.assertEqual(ref[field],hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertIn('No distinct top charging-handle stroke', (ROOT/ART/'SOURCE.md').read_text())

    def test_evidence_authorship_hashes_and_exact94_owned_files(self):
        m=read(ART/'manifest.json');self.assertEqual((90,87,84,133),(m['generatedFiles'],m['packFiles'],m['parentDisplayChildren'],m['maxAssembledElements']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertEqual('ikelos_smg_v1_0_1',m['integration']['catalogId'])
        owned={str(p) for p in G['expected_output_paths']()}|{'scripts/generate_reload_w182_ikelos_smg_v1_0_1.py','scripts/qa/test_reload_w182_ikelos_smg_v1_0_1.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW182IkelosTest.java',str(ART/'SOURCE.md')}
        self.assertEqual(94,len(owned));self.assertTrue(all((ROOT/p).is_file() for p in owned))
        manifest=Path('/private/tmp/w182-manifest.json')
        if manifest.exists():self.assertEqual(owned,set(next(f['owned_paths'] for f in json.loads(manifest.read_bytes())['features'] if f['name']=='w182-ikelos')))
        source=(ROOT/ART/'SOURCE.md').read_text();self.assertIn('authored interpretations',source);self.assertIn('No native success',source);self.assertIn('23.42340',source)
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)
if __name__=='__main__':unittest.main(verbosity=2)
