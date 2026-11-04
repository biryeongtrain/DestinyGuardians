#!/usr/bin/env python3
"""Focused W173 Salvo asset checks; independent rigid geometry, not native QA."""
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w173_salvager_s_salvo.py'))
A=G['A'];ART=G['ART'];KEY=G['KEY'];FP=G['FP']
def read(p):return json.loads((ROOT/p).read_bytes())
def matrix(a):
    x,y,z=np.radians(a);cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z)
    return np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
def child(i,part,grip):return read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')['display']
def point(d,p):return matrix(d['rotation'])@((np.array(p)-8)*d['scale'])+d['translation']
class SalvoReload(unittest.TestCase):
    def test_exact_partition_fixed_grip_breech_face_and_hinged_foreend(self):
        source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');barrel=read(A/f'models/{KEY}_barrel.json');round_=read(A/f'models/{KEY}_round.json')
        self.assertEqual((28,73,6),tuple(len(m['elements']) for m in (body,barrel,round_)))
        moving=set(range(32))|set(range(36,58))|set(range(73,76))|set(range(85,101))
        self.assertEqual(moving,set(G['BARREL']))
        b=h=0
        for i,e in enumerate(source['elements']):
            if i in moving:self.assertEqual(e,barrel['elements'][h]);h+=1
            else:self.assertEqual(e,body['elements'][b]);b+=1
        fixed={e['name'] for e in body['elements']};hinged={e['name'] for e in barrel['elements']}
        self.assertTrue({'grip_main','receiver_core','stock_wood','trigger','guard_floor','breech_plug_0','breech_plug_3'}<=fixed)
        self.assertTrue({'foregrip_0','foregrip_socket','lower_barrel_cradle','sight_pedestal','front_bead','top_rail'}<=hinged)
        for m in (body,barrel,round_):self.assertEqual(source['textures'],m['textures'])
        for e in round_['elements']:
            self.assertTrue(e['name'].startswith('cosmetic_round_'))
            self.assertEqual(source['elements'][75]['faces'],e['faces'])
        self.assertEqual(107,b+h+len(round_['elements']));self.assertLessEqual(107,1000)
        design=read(G['DESIGN']);self.assertEqual('W149',design['revision'])
        self.assertEqual([e['name'] for e in source['elements']],[p['geometry']['name'] for p in design['parts']])
        self.assertEqual(G['SOURCE_SHA256'],hashlib.sha256((ROOT/G['SOURCE']).read_bytes()).hexdigest())
    def test_children_endpoints_and_non_fp_are_exact(self):
        for grip in G['GRIPS']:
            expected=read(G['SOURCE'] if grip=='native' else G['TWOHAND'])['display']
            for i in range(21):
                for part in G['PARTS']:
                    p=A/f'models/{KEY}_{i:02}_{part}_{grip}.json';j=read(p);d=j['display']
                    self.assertEqual(f'destiny:{KEY}_{part}',j['parent']);self.assertNotIn('elements',j)
                    if i in (0,20):self.assertEqual(expected,d)
                    for ctx in expected:
                        if ctx not in FP:self.assertEqual(expected[ctx],d[ctx])
                    for ctx in FP:
                        self.assertEqual(expected[ctx]['scale'],d[ctx]['scale'])
                        for k in ('rotation','translation','scale'):self.assertTrue(all(math.isfinite(v) for v in d[ctx][k]))
    def test_independent_hinge_grip_and_twohand_carrier_all_samples(self):
        source=read(G['SOURCE'])['display'];two=read(G['TWOHAND'])['display'];q=np.array([8,10.91,4.14]);h=np.array([8,8.155,8.25])
        for i in range(21):
            angles,shift,hinge,approach=G['sample'](i/20);b=matrix(angles);hr=matrix([hinge,0,0])
            for ctx in FP:
                base=matrix(source[ctx]['rotation']);s=source[ctx]['scale'][0]
                expected=base@(s*(h-8))+source[ctx]['translation']+np.array(shift)
                comp=matrix(two[ctx]['rotation'])@base.T
                for grip in G['GRIPS']:
                    bd=child(i,'body',grip)[ctx];hd=child(i,'barrel',grip)[ctx];rd=child(i,'round',grip)[ctx]
                    c=np.eye(3) if grip=='native' else comp
                    origin=expected if grip=='native' else c@expected+two[ctx]['translation']-c@np.array(source[ctx]['translation'])
                    np.testing.assert_allclose(point(bd,h),origin,atol=3e-9)
                    np.testing.assert_allclose(point(bd,q),point(hd,q),atol=4e-9)
                    np.testing.assert_allclose(matrix(hd['rotation']),c@base@b@hr,atol=4e-10)
                    if i not in (0,20):np.testing.assert_allclose(np.array(rd['translation'])-hd['translation'],c@base@b@hr@(np.array(approach)*s),atol=3e-9)
        self.assertLess(G['sample'](.3)[2],-45)
        self.assertEqual(-48,G['sample'](.65)[2]);self.assertEqual(0,G['sample'](.76)[2])
    def test_single_round_fits_open_bore_and_is_gone_before_close(self):
        # The six short hex volumes have circumradius below the barrel's .86 inner radius.
        self.assertLess(.68*2/math.sqrt(3),.86)
        self.assertEqual(list(range(9,14)),list(G['ROUND_VISIBLE']))
        q=np.array([8,10.91,4.14]);rr=matrix([-48,0,0])
        rear=rr@(np.array([8,12.27,4.22])-q)+q
        self.assertLess(rear[2],4.05-.7)  # clears the unchanged fixed receiver face
        for ctx in FP:
            for grip in G['GRIPS']:
                self.assertEqual(child(13,'barrel',grip)[ctx],child(13,'round',grip)[ctx])
        # Progress 0.65 seats the cosmetic round; 0.70 hides it while still open.
        self.assertEqual([0,0,0],G['sample'](.65)[3]);self.assertLess(G['sample'](.7)[2],-40)
    def test_fp_only_graph_hidden_round_and_exact_ads_inspect_fallback(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap']);self.assertEqual(canonical['model'],graph['fallback'])
        self.assertEqual(['ads','inspect'],[c['when'] for c in graph['fallback']['cases']]);self.assertEqual(list(FP),graph['cases'][0]['when'])
        dispatch=graph['cases'][0]['model'];self.assertEqual(1,dispatch['index']);self.assertEqual(canonical['model'],dispatch['fallback']);self.assertEqual(21,len(dispatch['entries']))
        for i,e in enumerate(dispatch['entries']):
            self.assertEqual(i/20,e['threshold']);self.assertEqual(0,e['model']['index'])
            for branch,grip in (('on_true','twohand'),('on_false','native')):
                c=e['model'][branch];self.assertEqual('minecraft:composite',c['type'])
                parts=('body','barrel','round') if 9<=i<=13 else ('body','barrel')
                self.assertEqual([f'destiny:{KEY}_{i:02}_{p}_{grip}' for p in parts],[m['model'] for m in c['models']])
        for p,want in [(-1,None),(0,0),(.049,0),(.05,1),(.449,8),(.45,9),(.699,13),(.7,14),(1,20)]:
            matches=[i for i,e in enumerate(dispatch['entries']) if p>=e['threshold']];self.assertEqual(want,matches[-1] if matches else None)
    def test_actual_salvo_reference_pixels_timestamps_identity_and_limitations(self):
        ref=read(ART/'motion-reference.json');self.assertTrue(ref['inspectedActualFrames']);self.assertTrue(ref['authoredApproximation']);self.assertEqual('Aztecross',ref['creator'])
        self.assertEqual('https://www.youtube.com/watch?v=waod2MdK13w',ref['url']);self.assertEqual([84.1,85.6],ref['selectedSeconds'])
        self.assertEqual(12,len(ref['frames']));self.assertEqual(12,len({f['sha256'] for f in ref['frames']}))
        self.assertIn('ladder sight',ref['identityVerification']['evidence']);self.assertTrue(ref['identityVerification']['sourceTitleIsNotSoleEvidence'])
        self.assertIn('shader',ref['identityVerification']['appearance'])
        for f in ref['frames']:
            self.assertEqual(f['sourceFrameIndex']/60,f['timestampSeconds']);self.assertEqual(ref['url'],f['sourceURL']);self.assertTrue(f['observation']);self.assertTrue(f['confidence'])
            self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest())
            with Image.open(ROOT/f['path']) as im:self.assertEqual((1280,720),im.size)
        self.assertIn('authored estimates',ref['limitations'][0])
    def test_output_counts_hashes_and_master_owned_route18_native_queue(self):
        m=read(ART/'manifest.json');paths=set(m['sha256'])|{str(ART/'manifest.json')}
        self.assertEqual(133,len(paths));self.assertEqual({str(p) for p in G['expected_output_paths']()},paths)
        self.assertEqual(130,len([p for p in paths if p.startswith(str(A))]));self.assertEqual(126,m['parentDisplayChildren']);self.assertEqual(107,m['maxAssembledElements'])
        for mapping in (m['sourceSha256'],m['sha256']):
            for p,h in mapping.items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        for k in ('nativeGameplayVerified','handIK','extractedAnimation','extractedBones','mechanicsOrAudioChanged','newTexture'):self.assertFalse(m[k])
        self.assertEqual(18,m['integration']['intendedRouteNumber']);self.assertEqual(17,m['integration']['expectedExistingRouteCount']);self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['requiresNewMasterRoute'])
        self.assertEqual('destiny:'+KEY,m['integration']['requiredMasterModel']);self.assertEqual(4,len(m['nativeQueue']))
        ownership=Path('/private/tmp/w173-manifest.json')
        if ownership.exists():
            owned=set(next(f['owned_paths'] for f in json.loads(ownership.read_bytes())['features'] if f['name']=='w173-salvo-reload'));self.assertEqual(149,len(owned));self.assertTrue(paths<=owned)
    def test_domain_is_bounded_and_ready_endpoints(self):
        for bad in (float('nan'),float('inf'),-.01,1.01):
            with self.assertRaises(ValueError):G['sample'](bad)
        for p in (0,1):self.assertEqual(([0,0,0],[0,0,0],0.,[0,0,0]),G['sample'](p))
if __name__=='__main__':unittest.main(verbosity=2)
