#!/usr/bin/env python3
"""Focused W176 asset regression. Native gameplay/routing are master-owned."""
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w176_brass_attacks.py'))
A=G['A'];KEY=G['KEY'];ART=G['ART'];FP=G['FP']
def read(p): return json.loads((ROOT/p).read_bytes())
def matrix(a):
    x,y,z=np.radians(a)
    rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
    ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
    rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
    return rx@ry@rz
class ReloadW176BrassAttacksTest(unittest.TestCase):
    def test_exact_w143_geometry_uv_and_semantic_magazine(self):
        source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');moving=read(A/f'models/{KEY}_magazine.json')
        self.assertEqual(source['elements'][103:104],moving['elements'][:1])
        self.assertEqual([e for i,e in enumerate(source['elements']) if i not in (103,)],body['elements'])
        self.assertEqual((110,3),(len(body['elements']),len(moving['elements'])))
        self.assertEqual(source['textures'],body['textures']);self.assertEqual(source['textures'],moving['textures'])
        self.assertTrue(set(G['FIXED_NAMES'])<={e['name'] for e in body['elements']})
        design=read(Path('art/weapons/w123/brass_attacks/design.json'))
        self.assertEqual(list(G['NAMES']),[p['geometry']['name'] for p in design['parts'] if p['group']=='magazine'])
        self.assertEqual(list(G['GRIP']),source['elements'][95]['rotation']['origin'])
        self.assertEqual(list(G['MAG_ANCHOR']),source['elements'][103]['rotation']['origin'])
    def test_exact_endpoints_both_grips_and_all_nonfp(self):
        for grip,src in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            display=read(src)['display']
            for i in range(21):
                for part in ('body','magazine'):
                    child=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    self.assertEqual({'parent','display'},set(child))
                    self.assertEqual('destiny:'+KEY+'_'+part,child['parent'])
                    if i in (0,20):self.assertEqual(display,child['display'])
                    for ctx in set(display)-set(FP):self.assertEqual(display[ctx],child['display'][ctx])
                    for ctx in FP:
                        self.assertEqual(display[ctx]['scale'],child['display'][ctx]['scale'])
                        for k in ('rotation','translation','scale'):self.assertTrue(all(math.isfinite(v) for v in child['display'][ctx][k]))
    def test_fp_graph_canonical_inactive_fallback_and_ads_inspect(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['model'],graph['fallback']);self.assertEqual(False,wrapper['hand_animation_on_swap'])
        self.assertEqual(['ads','inspect'],[c['when'] for c in graph['fallback']['cases']])
        self.assertEqual(list(FP),graph['cases'][0]['when']);dispatch=graph['cases'][0]['model']
        self.assertEqual(canonical['model'],dispatch['fallback']);self.assertEqual(1,dispatch['index'])
        self.assertEqual(21,len(dispatch['entries']))
        for i,e in enumerate(dispatch['entries']):
            self.assertEqual(i/20,e['threshold']);self.assertEqual(0,e['model']['index'])
            for branch,grip in [('on_true','twohand'),('on_false','native')]:
                c=e['model'][branch];self.assertEqual('minecraft:composite',c['type']);self.assertEqual(2,len(c['models']))
                for part,m in zip(('body','magazine'),c['models']):self.assertEqual(f'destiny:{KEY}_{i:02}_{part}_{grip}',m['model'])
        for p,want in [(-1,None),(0,0),(.049,0),(.05,1),(.999,19),(1,20)]:
            matches=[i for i,e in enumerate(dispatch['entries']) if p>=e['threshold']];self.assertEqual(want,matches[-1] if matches else None)
    def test_independent_representative_grip_and_rotated_withdrawal(self):
        source=read(G['SOURCE'])['display'];two=read(G['TWOHAND'])['display'];h=np.array(G['GRIP'])-8
        for i in (2,7,13,18):
            angles,shift,offset=G['sample'](i/20);b=matrix(angles)
            for grip in ('native','twohand'):
                bd=read(A/f'models/{KEY}_{i:02}_body_{grip}.json')['display'];md=read(A/f'models/{KEY}_{i:02}_magazine_{grip}.json')['display']
                for ctx in FP:
                    r=matrix(source[ctx]['rotation']);comp=np.eye(3) if grip=='native' else matrix(two[ctx]['rotation'])@r.T
                    expected=comp@r@b@(np.array(offset)*source[ctx]['scale'][0])
                    np.testing.assert_allclose(np.array(md[ctx]['translation'])-bd[ctx]['translation'],expected,atol=2e-9)
                    np.testing.assert_allclose(matrix(bd[ctx]['rotation']),comp@r@b,atol=3e-10)
                    pivot=np.array(source[ctx]['translation'])+r@(source[ctx]['scale'][0]*h)+shift
                    if grip=='twohand':pivot=comp@pivot+np.array(two[ctx]['translation'])-comp@np.array(source[ctx]['translation'])
                    np.testing.assert_allclose(np.array(bd[ctx]['translation'])+matrix(bd[ctx]['rotation'])@(source[ctx]['scale'][0]*h),pivot,atol=2e-9)
        self.assertGreater(G['sample'](.12)[0][0],40)
        offset=np.array(G['sample'](.24)[2]);axis=matrix([-19.05,0,0])@np.array([0,-1,0])
        np.testing.assert_allclose(offset/np.linalg.norm(offset),axis,atol=1e-9)
        self.assertEqual([0,0,0],G['sample'](.43)[2])
    def test_magazine_clears_fixed_heel_with_core_and_neck(self):
        source=read(G['SOURCE'])['elements']
        def corners(e):
            rot=e.get('rotation',{});o=np.array(rot.get('origin',[0,0,0]))
            angles=[rot.get('angle',0) if rot.get('axis')==k else 0 for k in 'xyz'];rr=matrix(angles)
            return [rr@(np.array([x,y,z])-o)+o for x in (e['from'][0],e['to'][0]) for y in (e['from'][1],e['to'][1]) for z in (e['from'][2],e['to'][2])]
        moved=np.array([v+G['sample'](.24)[2] for e in read(A/f'models/{KEY}_magazine.json')['elements'] for v in corners(e)])
        fixed=np.array([v for i in (95,96,97,98,99,100,101,102) for v in corners(source[i])])
        self.assertLess(moved[:,1].max(),fixed[:,1].min()-.2)
        self.assertEqual([103],list(G['MOVING']))
        self.assertEqual('heel',source[102]['name']);self.assertIn(102,G['FIXED_HOUSING'])
        self.assertEqual(111,len(source));self.assertLessEqual(len(source),1000)
        self.assertEqual(2,read(ART/'manifest.json')['addedElements'])
    def test_actual_weapon_specific_frames_timestamps_and_hashes(self):
        ref=read(ART/'motion-reference.json');self.assertTrue(ref['inspectedActualFrames']);self.assertTrue(ref['authoredApproximation'])
        self.assertEqual('https://www.youtube.com/watch?v=F6-wH23URIw',ref['url']);self.assertEqual('Ultraclocked',ref['creator'])
        self.assertEqual([792/60,900/60],ref['selectedSeconds']);self.assertEqual(12,len(ref['frames']))
        self.assertIn('BRASS ATTACKS',ref['identityVerification']['evidence'])
        self.assertEqual(12,len({f['sha256'] for f in ref['frames']}))
        self.assertEqual(sorted(f['timestampSeconds'] for f in ref['frames']),[f['timestampSeconds'] for f in ref['frames']])
        for f in ref['frames']:
            self.assertEqual(f['sourceFrameIndex']/60,f['timestampSeconds']);self.assertEqual(ref['url'],f['sourceURL'])
            self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest())
            self.assertTrue(f['observation']);self.assertTrue(f['confidence'])
            with Image.open(ROOT/f['path']) as im:self.assertEqual((1280,720),im.size)
        self.assertIn('guess',ref['limitations'][0])
    def test_output_counts_source_pins_and_honest_runtime_boundary(self):
        m=read(ART/'manifest.json');paths=set(m['sha256'])|{str(ART/'manifest.json')}
        self.assertEqual({str(p) for p in G['expected_output_paths']()},paths)
        self.assertEqual(90,len(paths));self.assertEqual(87,len([p for p in paths if p.startswith(str(A))]))
        self.assertEqual((110,3,113),(m['bodyElements'],m['movingElements'],m['maxAssembledElements']))
        for mapping in (m['sourceSha256'],m['sha256']):
            for p,digest in mapping.items():self.assertEqual(digest,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        self.assertFalse(m['nativeGameplayVerified']);self.assertFalse(m['handIK']);self.assertFalse(m['extractedBones']);self.assertFalse(m['mechanicsOrAudioChanged'])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['requiresNewMasterRoute'])
        self.assertEqual('destiny:'+KEY,m['integration']['requiredMasterModel'])
    def test_graph_preserves_canonical_ads_inspect_and_inactive_nonfp(self):
        wrapper=read(A/f'items/{KEY}.json');canonical=read(G['ITEM']);graph=wrapper['model']
        self.assertEqual(canonical.get('hand_animation_on_swap'),wrapper.get('hand_animation_on_swap'))
        self.assertEqual('minecraft:display_context',graph['property'])
        self.assertEqual(list(FP),graph['cases'][0]['when']);self.assertEqual(canonical['model'],graph['fallback'])
        dispatch=graph['cases'][0]['model']
        self.assertEqual(('minecraft:custom_model_data',1),(dispatch['property'],dispatch['index']))
        self.assertEqual(canonical['model'],dispatch['fallback']);self.assertEqual(21,len(dispatch['entries']))
        # Independent consumer: only FP + nonnegative live progress selects reload.
        # Publication to the live owner is runtime-owned; JSON cannot enforce it.
        for context in (*FP,'gui','ground','fixed','head','thirdperson_righthand','thirdperson_lefthand'):
            for progress in (-1,-.001,0,.049,.05,.5,.999,1):
                if context not in FP or progress<0:
                    chosen=graph['fallback'] if context not in FP else dispatch['fallback']
                    self.assertEqual(canonical['model'],chosen)
                else:
                    selected=max(e for e in range(21) if e/20<=progress)
                    entry=dispatch['entries'][selected];self.assertEqual(selected/20,entry['threshold'])
                    cond=entry['model'];self.assertEqual(0,cond['index'])
                    for branch,grip in [('on_true','twohand'),('on_false','native')]:
                        models=cond[branch]['models'];self.assertEqual(2,len(models))
                        self.assertEqual(['destiny:'+KEY+f'_{selected:02}_{part}_{grip}' for part in ('body','magazine')],[m['model'] for m in models])
    def test_sample_domain_and_readonly_generation_contract(self):
        for bad in (float('nan'),float('inf'),-.01,1.01):
            with self.assertRaises(ValueError):G['sample'](bad)
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),G['sample'](0))
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),G['sample'](1))
        # Generator --verify is run as its own focused gate, avoiding duplicate raster work here.
        self.assertEqual(90,len(G['expected_output_paths']()))
    def test_unchanged_catalog_timing_audio_and_canonical_pins(self):
        m=read(ART/'manifest.json')
        for p,digest in m['canonicalSha256'].items():
            self.assertEqual(digest,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='brass_attacks')
        self.assertEqual((24,37,325,2),(timing['magazine'],timing['reloadTicks'],timing['rpm'],timing['burstSize']))
        self.assertEqual('W143',read(Path('art/weapons/w123/brass_attacks/design.json'))['revision'])
    def test_brass_motion_is_bespoke_and_seated_during_action_dip(self):
        # Observed early exchange followed by action gesture, unlike Claws rear-well hold.
        self.assertLess(G['sample'](.78)[0][0],0)
        self.assertGreater(G['sample'](.69)[0][0],20)
        for p in (.43,.5,.58,.69,.78,.9,1):self.assertEqual([0,0,0],G['sample'](p)[2])
        self.assertEqual(13,len(G['KEYS']))
        ref=read(ART/'motion-reference.json');self.assertEqual(1.,ref['identityVerification']['identityFrameSeconds'])
        self.assertIn('one reload-only box',ref['limitations'][1])
    def test_exactly_one_substantial_core_inside_opaque_grip_with_reused_uv(self):
        source=read(G['SOURCE']);magazine=read(A/f'models/{KEY}_magazine.json')
        core=magazine['elements'][1];grip=source['elements'][95]
        self.assertEqual('authored_internal_magazine_core',core['name'])
        self.assertEqual(3,len(magazine['elements']))
        self.assertEqual(grip['rotation'],core['rotation'])
        self.assertEqual(grip['faces'],core['faces'])
        # Same local frame: strict corner containment proves opaque occlusion
        # under either grip/hand rigid transform, without shrinking at endpoints.
        for k in range(3):
            self.assertGreater(core['from'][k],grip['from'][k])
            self.assertLess(core['to'][k],grip['to'][k])
        size=np.array(core['to'])-core['from']
        self.assertGreater(size[0],1);self.assertGreater(size[1],5);self.assertGreater(size[2],1.8)
        self.assertGreater(np.prod(size),10)
        with Image.open(ROOT/G['TEXTURE']) as image:
            rgba=np.asarray(image.convert('RGBA'))
        for face in grip['faces'].values():
            u,v,x,y=face['uv'];h,w=rgba.shape[:2]
            pixels=rgba[int(v*h/16):int(y*h/16),int(u*w/16):int(x*w/16)]
            self.assertTrue(np.all(pixels[:,:,3]==255))
            self.assertLess(np.mean(pixels[:,:,:3]),70)
        m=read(ART/'manifest.json');self.assertEqual(111,m['canonicalPartitionElements'])
        self.assertEqual(95,m['authoredCoreContainingElement']);self.assertEqual(core,m['authoredCore'])
        neck=magazine['elements'][2];base=magazine['elements'][0]
        self.assertEqual('authored_internal_magazine_neck',neck['name'])
        self.assertEqual(base['rotation'],neck['rotation'])
        self.assertEqual(grip['faces'],neck['faces'])
        self.assertLess(neck['from'][1],base['to'][1])
        self.assertGreater(neck['to'][1],7.3) # overlap core bottom in base-local frame
        self.assertEqual(neck,m['authoredNeck'])
    def test_offline_idle_render_smoke_and_withdrawn_core_has_volume(self):
        import copy
        helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
        source=read(G['SOURCE']);parts=[read(A/f'models/{KEY}_{p}.json') for p in ('body','magazine')]
        with Image.open(ROOT/G['TEXTURE']) as image:texture=image.convert('RGBA')
        def triangles(models):
            models=copy.deepcopy(models)
            for m in models:
                for e in m['elements']:
                    r=e.get('rotation',{})
                    if 'axis' in r:e['rotation']={'origin':r['origin'],r['axis']:r['angle']}
            return helper['model_triangles'](dict(enumerate(models)),texture)
        canonical=triangles([source]);assembled=triangles(parts)
        points=np.concatenate([t[0] for t in canonical])
        for camera in ([1,.2,-.45],[-1,.35,.6],[.4,.4,1]):
            extent=helper['frame'](points,camera,320,280)
            original=helper['render'](canonical,camera,extent,(320,280))[0]
            endpoint=helper['render'](assembled,camera,extent,(320,280))[0]
            # Render smoke only. Idle material protrusion is reviewed in the
            # three-view comparison, not an arbitrary pixel-exact proof:
            # the recessed neck can fill the small existing grip/heel seam.
            self.assertEqual(original.size,endpoint.size)
            self.assertIsNotNone(endpoint.getbbox())
        # A true solid box clears the heel, rather than just enlarging the tile.
        core=parts[1]['elements'][1];cap=parts[1]['elements'][0]
        self.assertGreater(core['to'][1]-core['from'][1],15*(cap['to'][1]-cap['from'][1]))
        for i in (4,5):
            child=read(A/f'models/{KEY}_{i:02}_magazine_native.json')
            self.assertEqual('destiny:'+KEY+'_magazine',child['parent'])
            self.assertNotIn('elements',child) # core and base share one rigid parent
if __name__=='__main__':unittest.main(verbosity=2)
