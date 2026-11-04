#!/usr/bin/env python3
"""Targeted Edge Transit asset acceptance. No native/client/runtime claim."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w180_edge_transit.py'))
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
class ReloadW180EdgeTransitTest(unittest.TestCase):
    def test_exact_canonical_partition_uv_dye_and_unchanged_gameplay_assets(self):
        source=read(G['SOURCE']);m=read(ART/'manifest.json');rebuilt={}
        for part,count in [('body',68),('magazine',28)]:
            model=read(A/f'models/{KEY}_{part}.json');self.assertEqual(count,len(model['elements']))
            self.assertEqual({k:v for k,v in source.items() if k!='elements'},{k:v for k,v in model.items() if k!='elements'})
            for i,e in zip(m['partitionIndices'][part],model['elements']):self.assertNotIn(i,rebuilt);rebuilt[i]=e
        self.assertEqual(source['elements'],[rebuilt[i] for i in range(96)])
        self.assertEqual((96,0,0),(m['maxAssembledElements'],m['addedElements'],m['triangleAdapterElements']))
        self.assertLessEqual(m['maxAssembledElements'],1000)
        for path,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='edge_transit')
        self.assertEqual((5,66,120,1,10,False),tuple(timing[k] for k in ('magazine','reloadTicks','rpm','burstSize','cadenceTicks','shellReload')))
    def test_complete_drum_core_bays_and_rims_use_single_rigid_payload(self):
        es=read(A/f'models/{KEY}_magazine.json')['elements'];names=[e['name'] for e in es]
        for prefix,count in [('drum_core_',4),('drum_bay_',8),('drum_front_rim_',8),('drum_rear_rim_',8)]:self.assertEqual(count,sum(n.startswith(prefix) for n in names))
        self.assertEqual(28,len(names));self.assertEqual(28,len(set(names)))
        for i in (0,4,9,15,18,20):
            for grip in ('native','twohand'):
                c=read(A/f'models/{KEY}_{i:02}_magazine_{grip}.json');self.assertNotIn('elements',c)
                self.assertEqual(f'destiny:{KEY}_magazine',c['parent'])
    def test_dedicated_steep_presentation_release_out_empty_reseat_secure_action_order(self):
        sample=G['sample']
        self.assertEqual([0,0,0],sample(.2)[2]);self.assertEqual(38,sample(.2)[3]);self.assertEqual([-6.4,0,0],sample(.3)[2])
        self.assertGreater(sample(.42)[0][0],60);self.assertEqual(sample(.42)[2],sample(.52)[2]);self.assertLess(sample(.42)[2][1],-4)
        self.assertEqual([-6.4,0,0],sample(.64)[2]);self.assertEqual([0,0,0],sample(.74)[2]);self.assertEqual(38,sample(.74)[3])
        self.assertEqual(0,sample(.81)[3]);self.assertEqual(0,sample(.81)[4]);self.assertEqual(.85,sample(.89)[4]);self.assertEqual(0,sample(.94)[4])
        for bad in (-.1,1.1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):sample(bad)
    def test_representative_articulation_is_rigid_and_preserves_all_uv_faces(self):
        body=read(A/f'models/{KEY}_body.json')['elements'];base={e['name']:e for e in body}
        self.assertEqual(4,len(G['CRADLE_NAMES']));self.assertTrue(set(G['CRADLE_NAMES'])<=set(base))
        for i in (4,9,15,18):
            es=read(A/f'models/{KEY}_{i:02}_body_native.json').get('elements',body)
            self.assertEqual(list(base),[e['name'] for e in es])
            changed=[]
            for e in es:
                old=base[e['name']];self.assertEqual(old['faces'],e['faces'])
                for a,b,c,d in zip(e['from'],e['to'],old['from'],old['to']):self.assertAlmostEqual(b-a,d-c,places=6)
                if old!=e:changed.append(e['name'])
                if e['name'] not in G['CRADLE_NAMES']+G['BOLT_NAMES']:self.assertEqual(old,e)
            self.assertEqual(set(G['CRADLE_NAMES']) if i in (4,9,15) else set(G['BOLT_NAMES']),set(changed))
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
                        anchor=np.array(G['DRUM_ANCHOR'] if part=='magazine' else G['GRIP'])-8
                        local=pivot+motion@(anchor-pivot+(np.array(offset) if part=='magazine' else 0))
                        expected=carrier@(np.array(idle['translation'])+shift+base@(local*.85))+np.array(accepted['translation'])-carrier@idle['translation']
                        actual=np.array(d['translation'])+matrix(d['rotation'])@(anchor*np.array(d['scale']))
                        np.testing.assert_allclose(expected,actual,atol=1e-7,rtol=0)
    def test_original_axis_angle_cradle_rotation_composes_about_hinge(self):
        # Independent Rodrigues matrices exercise actual original tilted brackets,
        # not only parent/display routing or values copied from emitted children.
        def axis_matrix(axis,deg):
            u=np.eye(3)['xyz'.index(axis)];a=math.radians(deg)
            k=np.array([[0,-u[2],u[1]],[u[2],0,-u[0]],[-u[1],u[0],0]])
            return np.eye(3)+math.sin(a)*k+(1-math.cos(a))*(k@k)
        source={e['name']:e for e in read(G['SOURCE'])['elements']}
        hinge=np.array([8.53,9.67,.85])
        for i in (4,14):
            body={e['name']:e for e in read(A/f'models/{KEY}_{i:02}_body_native.json')['elements']}
            turn=axis_matrix('x',38)
            for name in G['CRADLE_NAMES']:
                old=source[name];new=body[name];r=old.get('rotation',{})
                oldr=axis_matrix(r.get('axis','x'),r.get('angle',0));oldorigin=np.array(r.get('origin',[0,0,0]))
                nr=new['rotation'];newr=axis_matrix('z',nr['z'])@axis_matrix('y',nr['y'])@axis_matrix('x',nr['x']);no=np.array(nr['origin'])
                for corner in ('from','to'):
                    expected=hinge+turn@(oldorigin+oldr@(np.array(old[corner])-oldorigin)-hinge)
                    actual=no+newr@(np.array(new[corner])-no)
                    np.testing.assert_allclose(expected,actual,atol=1e-7,rtol=0)
    def test_evidence_authorship_hashes_and_exact94_owned_files(self):
        m=read(ART/'manifest.json');ref=m['reference'];self.assertEqual('https://www.youtube.com/watch?v=afQnPfb4ZK4',ref['url']);self.assertEqual(12,len(ref['frames']))
        for f in ref['frames']:self.assertEqual(f['sourceFrameIndex']/60,f['timestampSeconds']);self.assertTrue(f['observation']);self.assertEqual(64,len(f['sha256']))
        self.assertEqual((90,87,84,96),(m['generatedFiles'],m['packFiles'],m['parentDisplayChildren'],m['maxAssembledElements']))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertEqual('edge_transit',m['integration']['catalogId'])
        owned={str(p) for p in G['expected_output_paths']()}|{'scripts/generate_reload_w180_edge_transit.py','scripts/qa/test_reload_w180_edge_transit.py','src/test/java/kim/biryeong/destiny/weapon/ReloadW180EdgeTransitTest.java',str(ART/'SOURCE.md')}
        self.assertEqual(94,len(owned));self.assertTrue(all((ROOT/p).is_file() for p in owned))
        manifest=Path('/private/tmp/w180-manifest.json')
        if manifest.exists():self.assertEqual(owned,set(next(f['owned_paths'] for f in json.loads(manifest.read_bytes())['features'] if f['name']=='w180-edge-transit')))
        source=(ROOT/ART/'SOURCE.md').read_text();self.assertIn('authored interpretations',source);self.assertIn('No native success',source);self.assertIn('51.051',source)
        for name in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/name) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)
if __name__=='__main__':unittest.main(verbosity=2)
