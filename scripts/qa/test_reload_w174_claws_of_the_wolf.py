#!/usr/bin/env python3
"""Focused W174 asset regression. Native gameplay/routing are master-owned."""
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w174_claws_of_the_wolf.py'))
A=G['A'];KEY=G['KEY'];ART=G['ART'];FP=G['FP']
def read(p): return json.loads((ROOT/p).read_bytes())
def matrix(a):
    x,y,z=np.radians(a)
    rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
    ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
    rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
    return rx@ry@rz
class ReloadW174ClawsOfTheWolfTest(unittest.TestCase):
    def test_exact_w138_geometry_uv_and_semantic_magazine(self):
        source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');moving=read(A/f'models/{KEY}_magazine.json')
        self.assertEqual(source['elements'][111:113],moving['elements'])
        self.assertEqual([e for i,e in enumerate(source['elements']) if i not in (111,112)],body['elements'])
        self.assertEqual((126,2),(len(body['elements']),len(moving['elements'])))
        self.assertEqual(source['textures'],body['textures']);self.assertEqual(source['textures'],moving['textures'])
        self.assertTrue(set(G['FIXED_NAMES'])<={e['name'] for e in body['elements']})
        design=read(Path('art/weapons/w123/claws_of_the_wolf/design.json'))
        self.assertEqual(list(G['NAMES']),[p['geometry']['name'] for p in design['parts']['full'] if p['group']=='magazine'])
        self.assertEqual(list(G['GRIP']),source['elements'][84]['rotation']['origin'])
        self.assertEqual(list(G['MAG_ANCHOR']),source['elements'][111]['rotation']['origin'])
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
        self.assertGreater(G['sample'](.3)[0][0],75)
        offset=np.array(G['sample'](.45)[2]);axis=matrix([101.52372170389735,0,0])@np.array([0,0,1])
        np.testing.assert_allclose(offset/np.linalg.norm(offset),axis,atol=1e-9)
        self.assertEqual([0,0,0],G['sample'](.79)[2])
    def test_rear_magazine_clears_stock_and_fixed_grip(self):
        source=read(G['SOURCE'])['elements']
        def corners(e):
            rot=e.get('rotation',{});o=np.array(rot.get('origin',[0,0,0]));rr=matrix([rot.get(k,0) for k in 'xyz'])
            return [rr@(np.array([x,y,z])-o)+o for x in (e['from'][0],e['to'][0]) for y in (e['from'][1],e['to'][1]) for z in (e['from'][2],e['to'][2])]
        moved=np.array([v+G['sample'](.45)[2] for i in G['MOVING'] for v in corners(source[i])])
        housing=np.array([v for i in (91,94,95,96,97) for v in corners(source[i])])
        self.assertLess(moved[:,1].max(),housing[:,1].min()-1)
        self.assertGreater(np.mean([source[i]['rotation']['origin'][2] for i in G['MOVING']]),G['GRIP'][2])
        self.assertEqual(128,len(source));self.assertLessEqual(len(source),1000)
    def test_actual_weapon_specific_frames_timestamps_and_hashes(self):
        ref=read(ART/'motion-reference.json');self.assertTrue(ref['inspectedActualFrames']);self.assertTrue(ref['authoredApproximation'])
        self.assertEqual('https://www.youtube.com/watch?v=y4zj-mxVqCQ',ref['url']);self.assertEqual('Rin',ref['creator'])
        self.assertEqual([96/30,170/30],ref['selectedSeconds']);self.assertEqual(12,len(ref['frames']))
        self.assertIn('Claws Of The Wolf',ref['identityVerification']['evidence'])
        self.assertEqual(12,len({f['sha256'] for f in ref['frames']}))
        self.assertEqual(sorted(f['timestampSeconds'] for f in ref['frames']),[f['timestampSeconds'] for f in ref['frames']])
        for f in ref['frames']:
            self.assertEqual(f['sourceFrameIndex']/30,f['timestampSeconds']);self.assertEqual(ref['url'],f['sourceURL'])
            self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest())
            self.assertTrue(f['observation']);self.assertTrue(f['confidence'])
            with Image.open(ROOT/f['path']) as im:self.assertEqual((1280,720),im.size)
        self.assertIn('guess',ref['limitations'][0])
    def test_output_counts_source_pins_and_honest_runtime_boundary(self):
        m=read(ART/'manifest.json');paths=set(m['sha256'])|{str(ART/'manifest.json')}
        self.assertEqual({str(p) for p in G['expected_output_paths']()},paths)
        self.assertEqual(90,len(paths));self.assertEqual(87,len([p for p in paths if p.startswith(str(A))]))
        self.assertEqual((126,2,128),(m['bodyElements'],m['movingElements'],m['maxAssembledElements']))
        for mapping in (m['sourceSha256'],m['sha256']):
            for p,digest in mapping.items():self.assertEqual(digest,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        self.assertFalse(m['nativeGameplayVerified']);self.assertFalse(m['handIK']);self.assertFalse(m['extractedBones']);self.assertFalse(m['mechanicsOrAudioChanged'])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['requiresNewMasterRoute'])
        self.assertEqual('destiny:'+KEY,m['integration']['requiredMasterModel']);self.assertEqual(18,m['integration']['expectedExistingRouteCount'])
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
        self.assertEqual(19,read(ART/'manifest.json')['integration']['intendedRouteNumber'])
    def test_sample_domain_and_readonly_generation_contract(self):
        for bad in (float('nan'),float('inf'),-.01,1.01):
            with self.assertRaises(ValueError):G['sample'](bad)
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),G['sample'](0))
        self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),G['sample'](1))
        # Generator --verify is run as its own focused gate, avoiding duplicate raster work here.
        self.assertEqual(90,len(G['expected_output_paths']()))
if __name__=='__main__':unittest.main(verbosity=2)
