#!/usr/bin/env python3
"""Targeted Retrofit Escapade asset acceptance. No native/client/runtime claim."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w181_retrofit_escapade.py'))
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
class ReloadW181RetrofitTest(unittest.TestCase):
    def test_exact_canonical_partition_uv_dye_and_unchanged_gameplay_assets(self):
        source=read(G['SOURCE']);m=read(ART/'manifest.json');rebuilt={}
        for part,count in [('body',83),('magazine',51)]:
            model=read(A/f'models/{KEY}_{part}.json');self.assertEqual(count,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            for i,e in zip(m['partitionIndices'][part],model['elements']):self.assertNotIn(i,rebuilt);rebuilt[i]=e
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(134)])
        self.assertEqual((134,0,0),(m['maxAssembledElements'],m['addedElements'],m['triangleAdapterElements']))
        self.assertLessEqual(m['maxAssembledElements'],1000)
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='retrofit_escapade')
        self.assertEqual((77,90,900,1,1.333333333333,False),tuple(timing[k] for k in ('magazine','reloadTicks','rpm','burstSize','cadenceTicks','shellReload')))
    def test_complete_drum_and_physically_connected_belt_remain_one_rigid_payload(self):
        es=read(A/f'models/{KEY}_magazine.json')['elements'];by={e['name']:e for e in es}
        for prefix,count in [('drum_',10),('round_',35),('feed_join_',6)]:self.assertEqual(count,sum(n.startswith(prefix) for n in by))
        self.assertEqual(51,len(es));self.assertEqual(51,len(by))
        for i in range(6):
            e=by[f'feed_join_{i}'];o=e['rotation']['origin'];a=math.radians(e['rotation']['z']);half=(e['to'][0]-e['from'][0])/2
            for sign,j in [(-1,i),(1,i+1)]:
                point=[o[0]+sign*half*math.cos(a),o[1]+sign*half*math.sin(a),o[2]];link=by[f'round_link_{j}']
                self.assertTrue(all(link['from'][k]-.03<=point[k]<=link['to'][k]+.03 for k in range(3)),(i,j,point))
        tail=by['round_link_6'];center=[(a+b)/2 for a,b in zip(tail['from'],tail['to'])];neck=by['drum_feed_neck']
        self.assertTrue(all(a<v<b for a,v,b in zip(neck['from'],center,neck['to'])))
        for i in range(21):
            for grip in ('native','twohand'):
                c=read(A/f'models/{KEY}_{i:02}_magazine_{grip}.json');self.assertNotIn('elements',c)
                self.assertEqual(f'destiny:{KEY}_magazine',c['parent'])
    def test_reference_specific_cover_optic_feed_close_side_action_order(self):
        sample=G['sample']
        self.assertEqual([0,0,0],sample(.18)[2]);self.assertEqual(-96,sample(.18)[3])
        self.assertEqual([-3.4,-3.8,.3],sample(.26)[2]);self.assertEqual(sample(.26)[2],sample(.30)[2])
        self.assertEqual([0,0,0],sample(.50)[2]);self.assertEqual(-96,sample(.58)[3]);self.assertEqual(0,sample(.66)[3])
        self.assertEqual(0,sample(.66)[4]);self.assertEqual(1.05,sample(.80)[4]);self.assertEqual(0,sample(.88)[4])
        self.assertGreater(sample(.80)[0][0],15)
        for bad in (-.1,1.1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):sample(bad)
    def test_articulation_only_changes_original_cover_optic_and_handle_solids(self):
        body=read(A/f'models/{KEY}_body.json')['elements'];base={e['name']:e for e in body}
        self.assertEqual(24,len(G['COVER_NAMES']));self.assertTrue(set(G['COVER_NAMES'])<=set(base))
        for i in range(21):
            es=read(A/f'models/{KEY}_{i:02}_body_native.json').get('elements',body)
            self.assertEqual(list(base),[e['name'] for e in es])
            for e in es:
                old=base[e['name']];self.assertEqual(old['faces'],e['faces'])
                self.assertFalse({'vertices','triangles','mesh'}&set(e))
                for a,b,c,d in zip(e['from'],e['to'],old['from'],old['to']):self.assertAlmostEqual(b-a,d-c,places=6)
                if e['name'] not in G['COVER_NAMES']+G['BOLT_NAMES']:self.assertEqual(old,e)
    def test_exact_endpoints_nonfp_displays_and_no_scale_fade(self):
        for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            accepted=read(path)['display']
            for i in (0,4,9,15,18,20):
                for part in ('body','magazine'):
                    c=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    for context,d in c['display'].items():
                        self.assertEqual(accepted[context]['scale'],d['scale']);self.assertTrue(all(math.isfinite(v) for arr in d.values() for v in arr))
                        if context not in FP or i in (0,20):self.assertEqual(accepted[context],d)
                    if i in (0,20):self.assertNotIn('elements',c)
    def test_graph_both_contexts_grips_21_thresholds_and_canonical_guards(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap']);self.assertEqual(canonical['model'],graph['fallback'])
        guard=graph['cases'][0]['model'];self.assertEqual(canonical['model']['cases'],guard['cases']);rg=guard['fallback']
        self.assertEqual(1,rg['index']);self.assertEqual([i/20 for i in range(21)],[e['threshold'] for e in rg['entries']])
        for ctx in list(FP)+['thirdperson_righthand','thirdperson_lefthand','gui','ground','fixed','head','none']:
            for grip in (False,True):
                for mode in ('','ads','inspect'):
                    for progress in (-1,0,.049,.05,.45,.999,1,1.1):
                        got=resolve(graph,ctx,mode,progress,grip)
                        if ctx not in FP or mode or progress<0:self.assertEqual(resolve(canonical['model'],ctx,mode,progress,grip),got)
                        else:
                            i=min(20,math.floor(progress*20+1e-10));suffix='twohand' if grip else 'native'
                            self.assertEqual(tuple(f'destiny:{KEY}_{i:02}_{p}_{suffix}' for p in ('body','magazine')),got)
    def test_independent_rigid_anchor_matrix_with_scale_and_grip_carrier(self):
        native=read(G['SOURCE'])['display'];two=read(G['TWOHAND'])['display'];pivot=np.array(G['GRIP'])-8
        for i in (0,4,9,15,18,20):
            angles,shift,offset,_,_=G['sample'](i/20);motion=matrix(angles)
            for grip in ('native','twohand'):
                for hand in FP:
                    idle=native[hand];accepted=(native if grip=='native' else two)[hand]
                    base=matrix(idle['rotation']);carrier=matrix(accepted['rotation'])@base.T
                    for part in ('body','magazine'):
                        d=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')['display'][hand]
                        anchor=np.array([6.52,8.47,3.92] if part=='magazine' else G['GRIP'])-8
                        local=pivot+motion@(anchor-pivot+(np.array(offset) if part=='magazine' else 0))
                        expected=carrier@(np.array(idle['translation'])+shift+base@(local*.85))+np.array(accepted['translation'])-carrier@idle['translation']
                        actual=np.array(d['translation'])+matrix(d['rotation'])@(anchor*np.array(d['scale']))
                        np.testing.assert_allclose(expected,actual,atol=1e-7,rtol=0)
    def test_independent_rodrigues_every_cover_optic_corner_preserves_rigid_assembly(self):
        def axis_matrix(axis,deg):
            u=np.eye(3)['xyz'.index(axis)];a=math.radians(deg)
            k=np.array([[0,-u[2],u[1]],[u[2],0,-u[0]],[-u[1],u[0],0]])
            return np.eye(3)+math.sin(a)*k+(1-math.cos(a))*(k@k)
        source={e['name']:e for e in read(G['SOURCE'])['elements']};hinge=np.array([8.,12.4,-.1])
        for i in range(1,14):
            body={e['name']:e for e in read(A/f'models/{KEY}_{i:02}_body_native.json').get('elements',list(source.values()))}
            turn=axis_matrix('x',G['sample'](i/20)[3])
            for name in G['COVER_NAMES']:
                old=source[name];new=body[name];r=old.get('rotation',{})
                oldr=axis_matrix('z',r.get('z',0))@axis_matrix('y',r.get('y',0))@axis_matrix('x',r.get('x',0));oo=np.array(r.get('origin',[0,0,0]))
                nr=new.get('rotation',{});newr=axis_matrix('z',nr.get('z',0))@axis_matrix('y',nr.get('y',0))@axis_matrix('x',nr.get('x',0));no=np.array(nr.get('origin',[0,0,0]))
                for mask in range(8):
                    oc=np.array([old['to' if mask>>a&1 else 'from'][a] for a in range(3)])
                    nc=np.array([new['to' if mask>>a&1 else 'from'][a] for a in range(3)])
                    expected=hinge+turn@(oo+oldr@(oc-oo)-hinge);actual=no+newr@(nc-no)
                    np.testing.assert_allclose(expected,actual,atol=1e-7,rtol=0)
    def test_core_regeneration_is_byte_deterministic(self):
        one=G['generate']();two=G['generate']();self.assertEqual(one,two)
        for path,data in one.items():self.assertEqual((ROOT/path).read_bytes(),data,str(path))
    def test_evidence_authorship_hashes_and_exact94_owned_files(self):
        m=read(ART/'manifest.json');ref=m['reference'];self.assertEqual('https://www.youtube.com/watch?v=z7MW1pAbSxM',ref['url']);self.assertEqual(12,len(ref['frames']))
        for f in ref['frames']:
            self.assertEqual(f['sourceFrameIndex']/60,f['timestampSeconds']);self.assertTrue(f['observation']);self.assertEqual(64,len(f['sha256']))
            path=Path(f['path'])
            if path.exists():self.assertEqual(f['sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual((90,87,84,134),(m['generatedFiles'],m['packFiles'],m['parentDisplayChildren'],m['maxAssembledElements']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertEqual('retrofit_escapade',m['integration']['catalogId'])
        owned={str(p) for p in G['expected_output_paths']()}|{'scripts/generate_reload_w181_retrofit_escapade.py','scripts/qa/test_reload_w181_retrofit_escapade.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW181RetrofitTest.java',str(ART/'SOURCE.md')}
        self.assertEqual(94,len(owned));self.assertTrue(all((ROOT/p).is_file() for p in owned))
        manifest=Path('/private/tmp/w181-manifest.json')
        if manifest.exists():self.assertEqual(owned,set(next(f['owned_paths'] for f in json.loads(manifest.read_bytes())['features'] if f['name']=='w181-retrofit')))
        source=(ROOT/ART/'SOURCE.md').read_text();self.assertIn('authored interpretations',source);self.assertIn('No native success',source);self.assertIn('472.30',source)
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)
if __name__=='__main__':unittest.main(verbosity=2)
