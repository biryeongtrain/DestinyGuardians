#!/usr/bin/env python3
"""Bounded W181 asset/reference contract tests; runtime lifecycle belongs to master."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w181_seventh_seraph_officer_revolver.py'))
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
class ReloadW181OfficerTest(unittest.TestCase):
    def test_canonical_partition_uv_dye_audio_and_timing_preserved(self):
        source=read(G['SOURCE']);m=read(ART/'manifest.json');rebuilt={}
        for part,count in (('body',111),('magazine',10)):
            model=read(A/f'models/{KEY}_{part}.json')
            self.assertEqual(count,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            for index,element in zip(m['partitionIndices'][part],model['elements']):
                self.assertNotIn(index,rebuilt);rebuilt[index]=element
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(121)])
        self.assertEqual((121,0,121,0),tuple(m[k] for k in ('cubeElements','triangleAdapterElements','maxAssembledElements','addedElements')))
        self.assertLessEqual(m['maxAssembledElements'],1000)
        self.assertEqual(726,sum(len(e['faces']) for e in source['elements']))
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='seventh_seraph_officer_revolver')
        self.assertEqual((11,52,None,1,180),tuple(timing[k] for k in ('magazine','reloadTicks','chargeMillis','burstSize','rpm')))
        self.assertAlmostEqual(20/3,timing['cadenceTicks'])

    def test_entire_cylinder_and_brass_move_fixed_frame_and_rail_do_not(self):
        cylinder=read(A/f'models/{KEY}_magazine.json')['elements'];body=read(A/f'models/{KEY}_body.json')['elements']
        self.assertEqual(list(G['CYLINDER_NAMES']),[e['name'] for e in cylinder])
        self.assertEqual(list(range(72,82)),read(ART/'manifest.json')['partitionIndices']['magazine'])
        for e in cylinder:
            self.assertEqual(6,len(e['faces']));self.assertTrue(all(b>a for a,b in zip(e['from'],e['to'])))
        self.assertGreater(cylinder[0]['to'][0]-cylinder[0]['from'][0],1.7)
        self.assertGreater(cylinder[0]['to'][2]-cylinder[0]['from'][2],3)
        names={e['name'] for e in body}
        self.assertTrue({'rear_frame','chamber_bottom_rail','underbarrel_body','shroud_main','top_rail','sight_base','grip_core'}<=names)
        self.assertFalse(set(G['CYLINDER_NAMES'])&names)

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

    def test_independent_emitted_transform_cylinder_rigidity_and_open_clearance(self):
        import numpy as np
        def rot(a):
            x,y,z=np.radians(a)
            return np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])@np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])@np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        def transform(i,part,grip,hand):
            d=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')['display'][hand]
            return rot(d['rotation']),np.array(d['translation'])
        source=read(G['SOURCE']);pivot=np.array(G['GRIP'])-8;hinge=np.array(G['HINGE'])-8
        # Use true rotated vertices of canonical cubes, no pose generator calls.
        vertices=[]
        for e in read(A/f'models/{KEY}_magazine.json')['elements']:
            ps=np.array([[e['to' if mask>>a&1 else 'from'][a] for a in range(3)] for mask in range(8)])
            if 'rotation' in e:
                er=e['rotation'];x,y,z=np.radians([er.get(a,0) for a in 'xyz'])
                rr=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])@np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])@np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
                ps=(ps-np.array(er['origin']))@rr.T+er['origin']
            vertices.extend(ps)
        vertices=np.array(vertices)-8
        for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            for hand in FP:
                idle=source['display'][hand];accepted=read(path)['display'][hand]
                q=rot(accepted['rotation']);carrier=q@rot(idle['rotation']).T;s=accepted['scale'][0]
                for i in range(21):
                    angles,shift,cyl=G['sample'](i/20);b=rot(angles);c=rot(cyl)
                    for part in ('body','magazine'):
                        r,t=transform(i,part,grip,hand)
                        pts=vertices if part=='magazine' else np.array([[0,0,0],[1,3,-4],pivot,hinge])
                        local=(pts-hinge)@c.T+hinge if part=='magazine' else pts
                        expected=((local-pivot)@b.T+pivot)*s@q.T+np.array(accepted['translation'])+np.array(shift)@carrier.T
                        actual=(pts*s)@r.T+t
                        self.assertTrue(np.allclose(actual,expected,atol=2e-8),(i,grip,hand,part))
                        self.assertTrue(np.allclose(r.T@r,np.eye(3),atol=1e-9));self.assertAlmostEqual(1,np.linalg.det(r))
                    rb,tb=transform(i,'body',grip,hand);rc,tc=transform(i,'magazine',grip,hand)
                    # Part-relative coordinates remove carrier/body; hinge remains fixed.
                    self.assertTrue(np.allclose((hinge*s)@rc.T+tc,(hinge*s)@rb.T+tb,atol=2e-8))
                    opened=((vertices*s)@rc.T+tc-tb)@rb/s+8
                    if 4<=i<=14:
                        self.assertLess(opened[:,0].max(),7.23,'Cylinder must clear fixed rear-frame side at held-open samples')
                    if i in (0,20):self.assertTrue(np.allclose(opened,vertices+8,atol=1e-9))

    def test_officer_phase_order_and_invalid_input(self):
        sample=G['sample'];m=read(ART/'manifest.json')
        for p in (0,1):self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),sample(p))
        self.assertEqual([0,0,0],sample(1/11)[2]);self.assertEqual([0,0,82],sample(2/11)[2])
        self.assertTrue(all(math.isclose(a,b,abs_tol=1e-12) for aa,bb in zip(sample(4/11),sample(5/11)) for a,b in zip(aa,bb)));self.assertGreater(sample(4/11)[0][0],70)
        self.assertLess(sample(7/11)[0][0],10);self.assertEqual([0,0,82],sample(8/11)[2])
        self.assertEqual([0,0,0],sample(9/11)[2]);self.assertGreater(sample(10/11)[0][0],sample(9/11)[0][0])
        self.assertIn('closeFlick',m['normalizedPhases'])
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)
        for args in ((.5,'cell','native'),(.5,'body','other')):
            with self.assertRaises(ValueError):G['pose_display'](read(G['SOURCE'])['display'],read(G['TWOHAND'])['display'],*args)

    def test_actual_officer_frames_authorship_and_native_limits(self):
        m=read(ART/'manifest.json');ref=m['reference'];source=(ROOT/ART/'SOURCE.md').read_text()
        self.assertEqual('https://www.youtube.com/watch?v=CT0EUpyTweM',ref['url']);self.assertEqual('madmaxdrj Gaming',ref['creator'])
        self.assertTrue(ref['inspectedActualFrames']);self.assertEqual([18.5,1220/60],ref['selectedSeconds'])
        self.assertEqual(12,len(ref['frames']));self.assertEqual(12,len({f['sha256'] for f in ref['frames']}))
        self.assertEqual(list(range(1110,1221,10)),[f['sourceFrameIndex'] for f in ref['frames']])
        for f in ref['frames']:
            self.assertAlmostEqual(f['sourceFrameIndex']/60,f['timestampSeconds']);self.assertIn(f['sha256'],source)
        self.assertIn('authored',m['authoredHiddenDetails']);self.assertEqual(4,len(m['sourceChronology']))
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['masterOwnsRegistryRuntime'])
        self.assertEqual('destiny:'+KEY,m['integration']['requiredMasterModel'])
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)

    def test_exact_owned_asset_graph_and_hash_contract_without_shared_route(self):
        m=read(ART/'manifest.json');self.assertEqual((94,90,87,84,0),tuple(m[k] for k in ('ownedFiles','generatedFiles','packFiles','parentDisplayChildren','addedElements')))
        outputs=G['expected_output_paths']();self.assertEqual(90,len(outputs));self.assertEqual(89,len(m['sha256']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        exact={str(p) for p in outputs}|{str(ART/'SOURCE.md'),'scripts/generate_reload_w181_seventh_seraph_officer_revolver.py','scripts/qa/test_reload_w181_seventh_seraph_officer_revolver.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW181OfficerTest.java'}
        self.assertEqual(94,len(exact));scope=Path('/private/tmp/w181-manifest.json')
        if scope.exists():self.assertEqual(exact,set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w181-officer')))
        graph=read(A/f'items/{KEY}.json');models=set()
        def visit(x):
            if isinstance(x,dict):
                if x.get('type')=='minecraft:model':models.add(x['model'])
                for v in x.values():visit(v)
            elif isinstance(x,list):
                for v in x:visit(v)
        visit(graph)
        self.assertEqual(84,len([model for model in models if model.startswith('destiny:weapon_reload_w181_')]))
        for model in models:
            namespace,path=model.split(':');self.assertEqual('destiny',namespace);self.assertTrue((ROOT/A/f'models/{path}.json').is_file(),model)

if __name__=='__main__':unittest.main(verbosity=2)
