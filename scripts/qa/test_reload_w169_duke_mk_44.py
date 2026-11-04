#!/usr/bin/env python3
"""W169 asset-only regression; no assumptions about master runtime support."""
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w169_duke_mk_44.py'))
A=G['A'];KEY=G['KEY'];ART=G['ART'];FP=G['FP']
MOTION=G['load_motion']()
def read(p): return json.loads((ROOT/p).read_bytes())
def matrix(angles):
    # Independent axis-angle oracle, assembled explicitly in JOML order.
    x,y,z=np.radians(angles)
    rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
    ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
    rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
    return rx@ry@rz
class ReloadW169DukeTest(unittest.TestCase):
    def test_01_exact_geometry_uv_partition(self):
        source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');moving=read(A/f'models/{KEY}_moving.json')
        self.assertEqual(source['elements'][78:147],moving['elements'])
        self.assertEqual(source['elements'][:78],body['elements'])
        self.assertEqual((78,69),(len(body['elements']),len(moving['elements'])))
        self.assertEqual(source['textures'],body['textures']);self.assertEqual(source['textures'],moving['textures'])
        self.assertEqual(147,len(body['elements'])+len(moving['elements']))
        self.assertEqual(list(G['NAMES']),[e['name'] for e in moving['elements']])
        fixed=set(G['FIXED_NAMES'])
        self.assertTrue(fixed <= {e['name'] for e in body['elements']})
        self.assertFalse(fixed & {e['name'] for e in moving['elements']})
        design=read(Path('art/weapons/w123/duke_mk_44/design.json'))
        self.assertEqual([p['geometry'] for p in design['parts']['body']],body['elements'])
        self.assertEqual([p['geometry'] for p in design['parts']['cylinder']],moving['elements'])
        self.assertEqual(['Yoke_vertical','Yoke_arm'],[e['name'] for e in moving['elements'][-2:]])
        self.assertEqual([8,10.2,5.17],list(G['HINGE']))
    def test_02_exact_hip_endpoints_all_contexts(self):
        for grip,src in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            expected=read(src)['display']
            for i in (0,60):
                for part in ('body','moving'):
                    m=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    self.assertEqual(expected,m['display']);self.assertEqual({'parent','display'},set(m))
    def test_03_graph_fallbacks_and_all_references(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['model'],graph['fallback'])
        self.assertEqual({k:v for k,v in canonical.items() if k!='model'},{k:v for k,v in wrapper.items() if k!='model'})
        self.assertEqual(list(FP),graph['cases'][0]['when'])
        dispatch=graph['cases'][0]['model'];self.assertEqual(1,dispatch['index']);self.assertEqual(canonical['model'],dispatch['fallback'])
        self.assertEqual(61,len(dispatch['entries']))
        for i,e in enumerate(dispatch['entries']):
            self.assertEqual(G['float32'](i/60),e['threshold']);c=e['model'];self.assertEqual(0,c['index'])
            for branch,grip in [('on_true','twohand'),('on_false','native')]:
                composite=c[branch];self.assertEqual('minecraft:composite',composite['type']);self.assertEqual(2,len(composite['models']))
                for part,m in zip(('body','moving'),composite['models']):
                    self.assertEqual(f'destiny:{KEY}_{i:02}_{part}_{grip}',m['model'])
                    child=read(A/('models/'+m['model'].split(':')[1]+'.json'))
                    self.assertEqual(f'destiny:{KEY}_{part}',child['parent'])
        # Negative/inactive selects fallback; exact 0 and 1 select assembled HIP.
        for progress,expected in [(-1,None),(0,0),(.016,0),(G['float32'](1/60),1),(.05,3),(.999,59),(1,60)]:
            matches=[i for i,e in enumerate(dispatch['entries']) if G['float32'](progress)>=e['threshold']]
            self.assertEqual(expected,matches[-1] if matches else None)
    def test_04_independent_cylinder_transform_point_oracle(self):
        source=read(G['SOURCE'])['display'];two=read(G['TWOHAND'])['display']
        hinge=np.array(G['HINGE']);pivot=np.array(G['GRIP'])
        points=[hinge,np.array([8.00596,12.8,3.766]),np.array([8,11.65,4.535])]
        for i in range(1,60):
            body_rotation,shift,cylinder=G['sample'](i/60,MOTION);b=np.array(body_rotation);c=matrix(cylinder)
            for grip in ('native','twohand'):
                moving=read(A/f'models/{KEY}_{i:02}_moving_{grip}.json')['display']
                body=read(A/f'models/{KEY}_{i:02}_body_{grip}.json')['display']
                for hand in FP:
                    idle=source[hand];r=matrix(idle['rotation']);scale=idle['scale'][0]
                    comp=np.eye(3) if grip=='native' else matrix(two[hand]['rotation'])@r.T
                    carrier=np.zeros(3) if grip=='native' else np.array(two[hand]['translation'])-comp@np.array(idle['translation'])
                    for point in points:
                        local=c@(point-hinge)+hinge
                        local=b@(local-pivot)+pivot
                        expected=comp@(np.array(idle['translation'])+r@(scale*(local-8+shift)))+carrier
                        actual=np.array(moving[hand]['translation'])+matrix(moving[hand]['rotation'])@(scale*(point-8))
                        np.testing.assert_allclose(actual,expected,atol=3e-9)
                    np.testing.assert_allclose(matrix(moving[hand]['rotation']),comp@r@b@c,atol=3e-10)
                    if .15<=i/60<=.85:
                        self.assertNotEqual(body[hand]['rotation'],moving[hand]['rotation'])
        self.assertGreater(np.linalg.norm(np.array(G['sample'](.40,MOTION)[0])-np.eye(3)),.5)
        self.assertEqual([0,0,80],G['sample'](.40,MOTION)[2])
        self.assertEqual([0,0,0],G['sample'](.92,MOTION)[2])
    def test_05_grip_pivot_preserved_and_nonfp_unchanged(self):
        source=read(G['SOURCE'])['display'];two=read(G['TWOHAND'])['display'];h=np.array(G['GRIP'])-8
        for grip,accepted in [('native',source),('twohand',two)]:
            for p in (.1,.45,.75,.95):
                display=G['pose_display'](source,two,p,'body',grip,MOTION)
                _,shift,_=G['sample'](p,MOTION)
                for hand in FP:
                    idle=source[hand];r=matrix(idle['rotation']);s=idle['scale'][0]
                    expected=np.array(idle['translation'])+r@(s*(h+shift))
                    if grip=='twohand':
                        c=matrix(two[hand]['rotation'])@r.T
                        expected=c@expected+np.array(two[hand]['translation'])-c@np.array(idle['translation'])
                    actual=np.array(display[hand]['translation'])+matrix(display[hand]['rotation'])@(s*h)
                    np.testing.assert_allclose(actual,expected,atol=2e-9)
                for context in set(accepted)-set(FP): self.assertEqual(accepted[context],display[context])
    def test_06_reference_pins_and_honest_limits(self):
        ref=read(ART/'motion-reference.json');self.assertTrue(ref['inspectedActualFrames']);self.assertEqual(12,len(ref['frames']))
        self.assertIn('-oS68Bu_sDs',ref['url'])
        self.assertEqual([25.5,27.9],ref['selectedSeconds'])
        self.assertIn('swing-out cylinder',ref['mechanism']['layout'])
        self.assertTrue(ref['authoredApproximation'])
        self.assertIn('occluded',ref['observations'][2]['fact']);self.assertEqual([],ref['pendingReferenceSlots'])
        self.assertEqual(12,len(set(f['sha256'] for f in ref['frames'])))
        self.assertEqual(sorted(f['timestampSeconds'] for f in ref['frames']),[f['timestampSeconds'] for f in ref['frames']])
        from PIL import Image
        for f in ref['frames']:
            self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest())
            self.assertEqual(ref['url'],f['sourceURL']);self.assertTrue(f['confidence'])
            with Image.open(ROOT/f['path']) as im: self.assertEqual((1280,720),im.size)
        manifest=read(ART/'manifest.json');self.assertFalse(manifest['nativeGameplayVerified']);self.assertFalse(manifest['handIK'])
        self.assertEqual(147,manifest['maxAssembledElements'])
        self.assertLessEqual(manifest['maxAssembledElements'],1000)
        self.assertEqual(hashlib.sha256((ROOT/G['SOURCE']).read_bytes()).hexdigest(),manifest['sourceGeometryFileSha256'])
        self.assertEqual(G['sha'](G['encode'](read(G['SOURCE'])['elements'])),manifest['sourceElementsAndUVSha256'])
        for part in ('body','moving'):
            self.assertEqual(G['sha'](G['encode'](read(A/f'models/{KEY}_{part}.json')['elements'])),manifest['partElementsAndUVSha256'][part])
        for p,digest in manifest['sourceSha256'].items(): self.assertEqual(digest,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
    def test_07_output_hashes_and_pack_count(self):
        m=read(ART/'manifest.json');paths=set(m['sha256'])|{str(ART/'manifest.json')}
        self.assertEqual({str(p) for p in G['expected_output_paths']()},paths)
        self.assertEqual(247,len([p for p in paths if p.startswith(str(A))]))
        for p,digest in m['sha256'].items(): self.assertEqual(digest,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
    def test_08_read_only_deterministic_verify(self):
        paths=G['expected_output_paths']();before={p:((ROOT/p).stat().st_mtime_ns,(ROOT/p).read_bytes()) for p in paths}
        generated=G['generate']();self.assertEqual(paths,set(generated))
        for p,data in generated.items():
            self.assertEqual(before[p][1],data,str(p));self.assertEqual(before[p][0],(ROOT/p).stat().st_mtime_ns,str(p))
        for bad in (float('nan'),float('inf'),-.1,1.1):
            with self.assertRaises(ValueError): G['sample'](bad,MOTION)
    def test_09_shell_clearance_and_attached_yoke(self):
        source=read(G['SOURCE'])['elements'];hinge=np.array(G['HINGE'])
        c=matrix(G['sample'](.40,MOTION)[2]);xs=[]
        # Source element rotation is Rz Ry Rx (display rotation is Rx Ry Rz).
        # These shell parts have Z rotations only, so both orders agree.
        for e in source[78:145]:
            center=np.array(e['rotation']['origin']);rot=matrix([e['rotation'][axis] for axis in 'xyz'])
            for x in (e['from'][0],e['to'][0]):
                for y in (e['from'][1],e['to'][1]):
                    for z in (e['from'][2],e['to'][2]):
                        point=rot@(np.array([x,y,z])-center)+center
                        xs.append((c@(point-hinge)+hinge)[0])
        self.assertLess(max(xs),source[16]['from'][0])
        # Yoke base lies on the authored swing axis and remains attached.
        np.testing.assert_allclose(c@(hinge-hinge)+hinge,hinge,atol=1e-12)
        self.assertEqual(hinge[1],source[145]['from'][1])
        m=read(ART/'manifest.json')
        self.assertTrue(m['integration']['replacementOnly']);self.assertFalse(m['integration']['addsRoute'])
        self.assertEqual(14,m['integration']['expectedExistingRouteCount'])
    def test_10_geometry_budget_resolves_every_assembled_sample(self):
        for i in range(61):
            for grip in ('native','twohand'):
                count=0
                for part in ('body','moving'):
                    child=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    self.assertNotIn('elements',child)
                    parent=read(A/('models/'+child['parent'].split(':')[1]+'.json'))
                    count+=len(parent['elements'])
                self.assertEqual(147,count);self.assertLessEqual(count,1000)
    def test_11_exact_duke_provenance_and_name_mapped_tracks(self):
        d=MOTION
        self.assertEqual('80A8A53D',d['clip']['tag'])
        self.assertEqual('Armature|fp_80A8A53D_reload_full|Base',d['clip']['action'])
        self.assertEqual('64A7DE8C',d['provenance']['sourceMap']['selector'])
        self.assertEqual(2112909414,d['provenance']['sourceMap']['weapons'][0]['apiHash'])
        self.assertEqual('armature_object',d['sampleSpace'])
        self.assertEqual((127,4.2),(len(d['samples']),d['clip']['durationSeconds']))
        self.assertEqual(8,len(d['bones']))
        self.assertEqual(5,d['bones']['3C37833F']['weaponBoneIndex'])
        self.assertEqual(3,d['bones']['9A633D9C']['weaponBoneIndex'])
        self.assertEqual(G['TRACK_SHA'],G['track_sha'](d))
        self.assertIn('Unresolved',d['conversion']['mechanicalBinding'])
        self.assertNotIn('cylinderBone',d)
        self.assertIn('no extracted cylinder claim',d['conversion']['authoredComponents']['cylinderYoke'])
        # Only this explicitly authorized cached sample is read from QA; no QA rewrite.
        cached=ROOT/'docs/qa/2026-10-27/w196/samples/hand_cannon_cedb29ae.json.gz'
        if not cached.is_file():
            cached=Path('/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-27/w196/samples/hand_cannon_cedb29ae.json.gz')
        if cached.is_file():
            compressed=cached.read_bytes();raw=gzip.decompress(compressed);src=json.loads(raw)
            self.assertEqual(G['SAMPLE_SHA'],G['sha'](raw))
            self.assertEqual(d['provenance']['sampleGzipSHA256'],G['sha'](compressed))
            byname={b['name']:i for i,b in enumerate(src['bones'])}
            clip=next(c for c in src['clips'] if c['tag']=='80A8A53D')
            for f,source in zip(d['samples'],clip['frames']):
                self.assertEqual(f['seconds'],source['seconds'])
                for name,pose in f['poses'].items():
                    self.assertEqual(src['bones'][byname[name]],d['bones'][name])
                    self.assertEqual(pose,source['matrices'][byname[name]])
        else:
            self.skipTest('Portable Duke tracks verified; cached source sample absent')

    def test_12_dense_body_against_independent_axis_angle_source_oracle(self):
        # Rodrigues interpolation is independent of the quaternion conversion/SLERP.
        def turn(a,b,t):
            delta=a.T@b; angle=math.acos(np.clip((np.trace(delta)-1)/2,-1,1))
            if angle<1e-9: return a
            axis=np.array([delta[2,1]-delta[1,2],delta[0,2]-delta[2,0],delta[1,0]-delta[0,1]])/(2*math.sin(angle))
            x,y,z=axis;k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
            return a@(np.eye(3)+math.sin(angle*t)*k+(1-math.cos(angle*t))*(k@k))
        d=MOTION;c=np.array(G['BASIS']);bone=G['BODY_BONE']
        r0,p0=G['rigid'](d['samples'][0]['poses'][bone]);r0=np.array(r0);p0=np.array(p0)
        for frame in range(61):
            p=frame/60;n=p*126;i=min(int(n),125);t=n-i
            ra,pa=G['rigid'](d['samples'][i]['poses'][bone]);rb,pb=G['rigid'](d['samples'][i+1]['poses'][bone])
            expected=c@r0.T@turn(np.array(ra),np.array(rb),t)@c.T
            delta=32*c@r0.T@(np.array(pa)+(np.array(pb)-pa)*t-p0)
            if p>.95:
                blend=(p-.95)/.05;blend=blend*blend*(3-2*blend)
                expected=turn(expected,np.eye(3),blend);delta*=1-blend
            if frame in (0,60): expected,delta=np.eye(3),np.zeros(3)
            body,shift,_=G['sample'](p,d)
            np.testing.assert_allclose(body,expected,atol=2e-6)
            np.testing.assert_allclose(shift,delta,atol=1e-8)
            np.testing.assert_allclose(np.array(body).T@body,np.eye(3),atol=1e-9)
        # Check fractional times around the source's large rotations for continuity.
        for p in (.05,.1,.25,.5,.7,.95,.975,.999):
            a,pa,_=G['sample'](p-1e-7,d);b,pb,_=G['sample'](p+1e-7,d)
            self.assertLess(np.linalg.norm(np.array(a)-b),1e-4)
            self.assertLess(math.dist(pa,pb),1e-4)

    def test_13_rest_attachment_neutral_calibration_point_oracle(self):
        d=MOTION;bone=G['BODY_BONE'];c=np.array(G['BASIS']);grip=np.array(G['GRIP'])
        rest=np.array(d['bones'][bone]['restMatrix']);neutral=np.array(d['samples'][0]['poses'][bone])
        for frame in (6,13,25,38,63,88,101,114):
            pose=np.array(d['samples'][frame]['poses'][bone])
            body,shift,_=G['sample'](frame/126,d)
            for point in ((1,2,3),G['HINGE'],G['GRIP']):
                attachment=rest[:3,3]+rest[:3,:3]@c.T@(np.array(point)-grip)/32
                posed=pose[:3,3]+pose[:3,:3]@rest[:3,:3].T@(attachment-rest[:3,3])
                expected=grip+32*c@neutral[:3,:3].T@(posed-neutral[:3,3])
                actual=grip+shift+np.array(body)@(np.array(point)-grip)
                np.testing.assert_allclose(actual,expected,atol=1.5e-4)

    def test_14_source_guards_reject_ace_and_pose_drift_without_writes(self):
        from unittest.mock import patch
        for kind in ('clip','pose','basis','bone'):
            data=copy.deepcopy(MOTION)
            if kind=='clip': data['clip']['tag']='80A8A567'
            if kind=='pose': data['samples'][10]['poses'][G['BODY_BONE']][0][3]+=.001
            if kind=='basis': data['conversion']['sourceRootToModelBasis'][0][1]=1
            if kind=='bone': data['bones']['3C37833F']['weaponBoneIndex']=3
            with patch.object(Path,'read_bytes',return_value=G['encode'](data)):
                with self.assertRaises(ValueError): G['load_motion']()
        for bad in ([[1,0,0,0],[0,2,0,0],[0,0,1,0],[0,0,0,1]],
                    [[-1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
                    [[1,0,0,float('nan')],[0,1,0,0],[0,0,1,0],[0,0,0,1]]):
            with self.assertRaises(ValueError): G['rigid'](bad)

if __name__=='__main__': unittest.main(verbosity=2)
