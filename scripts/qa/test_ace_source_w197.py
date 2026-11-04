#!/usr/bin/env python3
"""Scoped offline source-motion tests; no SSD, Blender, Java or native client needed.

When the read-only main W196 sample is present, also compare every retained pose
against its gzip. All ordinary generation uses the portable dataset alone.
"""
import copy
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('ace_w197', ROOT/'scripts/generate_ace_reload_w157.py')
G = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)
W196 = Path('/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-27/w196/samples/hand_cannon_f163a4c8.json.gz')


def mm(a,b):
    return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]


def mv(a,v):
    return [sum(x*y for x,y in zip(row,v)) for row in a]


def tr(a):
    return list(map(list,zip(*a)))


def minus(a,b):
    return [x-y for x,y in zip(a,b)]


def rp(m):
    return [r[:3] for r in m[:3]], [r[3] for r in m[:3]]


def angle(a,b):
    delta=mm(tr(a),b)
    return math.acos(max(-1,min(1,(sum(delta[i][i] for i in range(3))-1)/2)))


class AceSourceW197Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=G.load_motion()
        cls.idle=json.loads((ROOT/G.SOURCE).read_text())['display']
        cls.two=json.loads((ROOT/G.TWOHAND).read_text())['display']

    def assertVec(self,a,b,tol=1.5e-4):
        for x,y in zip(a,b):
            self.assertAlmostEqual(x,y,delta=tol)

    def test_source_identity_and_portable_tracks(self):
        d=self.data
        self.assertEqual(hashlib.sha256((ROOT/G.MOTION).read_bytes()).hexdigest(),
                         'd275a0b6e4beecf8089dce29489695fef026e9704cd3b4238f6f3d15bcdac666')
        self.assertEqual(d['clip']['tag'],'80A8A567')
        self.assertNotEqual(d['clip']['tag'],'80A8A53D')
        self.assertEqual(d['clip']['durationSeconds'],4.2)
        self.assertEqual(d['provenance']['sourceMap']['selector'],'5267F9DF')
        self.assertEqual(d['provenance']['sourceMap']['weapons'][0]['apiHash'],347366834)
        self.assertEqual(d['provenance']['sourceFbxSHA256'],'38a735435828f321973a46abc50c16016ef74e503883f8284897c771f2afc4b0')
        self.assertEqual(len(d['bones']),8)
        self.assertEqual(len(d['samples']),127)
        self.assertLess((ROOT/G.MOTION).stat().st_size,350000)
        self.assertEqual(G.track_sha(d),G.TRACK_SHA)
        # Bone map indices are NOT sample-array offsets: retain identity by hash.
        self.assertEqual(d['bones']['3C37833F']['weaponBoneIndex'],5)
        self.assertEqual(d['bones']['9A633D9C']['weaponBoneIndex'],3)

    @unittest.skipUnless(W196.is_file(),'read-only W196 sample absent; portable checks still run')
    def test_exact_evaluated_source_evidence_all_eight_bones(self):
        raw=gzip.decompress(W196.read_bytes()); src=json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),G.ACE_SAMPLE_SHA)
        self.assertEqual(hashlib.sha256(W196.read_bytes()).hexdigest(),self.data['provenance']['sampleGzipSHA256'])
        byname={b['name']:i for i,b in enumerate(src['bones'])}
        for f,source in zip(self.data['samples'],src['clips'][0]['frames']):
            self.assertEqual(f['seconds'],source['seconds'])
            for name,pose in f['poses'].items():
                self.assertEqual(pose,source['matrices'][byname[name]])
        for name,b in self.data['bones'].items():
            self.assertEqual(b,src['bones'][byname[name]])

    def test_rest_skinning_and_neutral_calibration_reference(self):
        # Independent point calculation: source rest attachment -> pose skinning
        # -> inverse neutral calibration -> accepted grip. The .01 outer FBX
        # scale/axis transform must not enter any of these model-space operations.
        # Reference uses raw float matrices; allow 0.00015 model units for
        # orthonormalization drift (not animation/retarget tolerance).
        d=self.data; c=d['conversion']['sourceRootToModelBasis']
        rr,pr=rp(d['bones'][G.BODY_BONE]['restMatrix'])
        r0,p0=rp(d['samples'][0]['poses'][G.BODY_BONE])
        points=((1,2,3),G.HINGE,G.DRUM_CENTER,G.GRIP)
        for frame in (6,13,25,38,63,88,101,114):
            rt,pt=rp(d['samples'][frame]['poses'][G.BODY_BONE])
            body,delta,_,_=G.sample(frame/126,d)
            for v in points:
                attachment=mv(rr,[x/32 for x in mv(tr(c),minus(v,G.GRIP))])
                rest=[x+y for x,y in zip(pr,attachment)]
                posed=[x+y for x,y in zip(pt,mv(mm(rt,tr(rr)),minus(rest,pr)))]
                reference=[a+32*x for a,x in zip(G.GRIP,mv(c,mv(tr(r0),minus(posed,p0))))]
                actual=[a+b+x for a,b,x in zip(G.GRIP,delta,mv(body,minus(v,G.GRIP)))]
                self.assertVec(actual,reference)
        self.assertGreater(angle(G.xyz((0,0,0)),G.sample(.1,d)[0]),math.radians(90))

    def test_fractional_time_uses_rigid_shortest_arc_not_matrix_lerp(self):
        d=self.data; b,p,_,_=G.sample(.05,d)  # source index 6.3
        c=d['conversion']['sourceRootToModelBasis']; r0,p0=G.rigid(d['samples'][0]['poses'][G.BODY_BONE])
        ra,pa=G.rigid(d['samples'][6]['poses'][G.BODY_BONE]); rb,pb=G.rigid(d['samples'][7]['poses'][G.BODY_BONE])
        recovered=mm(r0,mm(mm(tr(c),b),c))
        self.assertAlmostEqual(angle(ra,recovered),.3*angle(ra,rb),delta=1e-7)
        self.assertAlmostEqual(angle(recovered,rb),.7*angle(ra,rb),delta=1e-7)
        expected=mv(c,mv(tr(r0),minus([a+.3*(v-a) for a,v in zip(pa,pb)],p0)))
        self.assertVec(p,[32*x for x in expected],1e-8)
        for f in range(61):
            r,_,_,_=G.sample(f/60,d); identity=mm(tr(r),r)
            for i in range(3):
                self.assertVec(identity[i],[int(i==j) for j in range(3)],1e-9)

    def test_endpoints_and_end_only_blend(self):
        d=self.data
        for progress in (0,1):
            r,p,_,_=G.sample(progress,d)
            self.assertEqual(r,G.xyz((0,0,0))); self.assertEqual(p,[0,0,0])
            for part in ('body','cylinder'):
                for grip,accepted in (('native',self.idle),('twohand',self.two)):
                    self.assertEqual(G.pose_display(self.idle,self.two,progress,part,grip,d),accepted)
        # End-only correction is small because the evaluated source itself returns.
        r0,p0=rp(d['samples'][0]['poses'][G.BODY_BONE]); re,pe=rp(d['samples'][-1]['poses'][G.BODY_BONE])
        self.assertLess(math.dist(p0,pe),1e-5); self.assertLess(angle(r0,re),.002)
        for progress in (.951,.975,.999):
            r,p,_,_=G.sample(progress,d)
            self.assertLess(angle(G.xyz((0,0,0)),r),.01)
            self.assertLess(math.dist(p,[0,0,0]),.15)

    def test_child_motion_inspected_but_binding_disclosed_as_unknown(self):
        d=self.data
        self.assertIn('Unresolved',d['conversion']['mechanicalBinding'])
        self.assertNotIn('cylinderBone',d)
        def relative(f,name):
            rr,pr=rp(d['samples'][f]['poses'][G.BODY_BONE]); rb,pb=rp(d['samples'][f]['poses'][name])
            return mm(tr(rr),rb),mv(tr(rr),minus(pb,pr))
        fixed0,_=relative(0,'2234F927'); fixed1,_=relative(50,'2234F927')
        open0,_=relative(0,'3F37833F'); open1,_=relative(50,'3F37833F')
        self.assertLess(angle(fixed0,fixed1),.002)
        self.assertGreater(angle(open0,open1),math.radians(95))
        _,a=relative(0,'82C5B60A'); _,b=relative(50,'82C5B60A')
        self.assertGreater(math.dist(a,b),.2)
        self.assertEqual(G.sample(.35,d)[2:],(86,.65))
        self.assertEqual(G.sample(.7,d)[2:],(0,0))

    def test_tampered_tracks_and_wrong_identity_rejected(self):
        for kind in ('clip','basis','pose','neutral'):
            d=copy.deepcopy(self.data)
            if kind=='clip': d['clip']['tag']='80A8A53D'
            if kind=='basis': d['conversion']['sourceRootToModelBasis'][0][1]=1
            if kind=='pose': d['samples'][10]['poses'][G.BODY_BONE][0][3]+=.001
            if kind=='neutral': d['conversion']['neutralSourceFrame']=127
            with tempfile.TemporaryDirectory(prefix='ace-source-guard-') as tmp:
                p=Path(tmp)/G.MOTION; p.parent.mkdir(parents=True); p.write_text(json.dumps(d))
                with self.assertRaises(ValueError): G.load_motion(tmp)
        for bad in ([[1,0,0,0],[0,2,0,0],[0,0,1,0],[0,0,0,1]],
                    [[-1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
                    [[1,0,0,float('nan')],[0,1,0,0],[0,0,1,0],[0,0,0,1]]):
            with self.assertRaises(ValueError): G.rigid(bad)


    def test_dense_samples_reproduce_source_with_independent_axis_angle_interpolation(self):
        # Reference uses Rodrigues axis-angle on adjacent evaluated rotations,
        # independent of the generator's quaternion conversion/SLERP routines.
        def interpolate(a,b,t):
            delta=mm(tr(a),b)
            theta=angle(a,b)
            if theta<1e-9:
                return a
            axis=[(delta[2][1]-delta[1][2])/(2*math.sin(theta)),
                  (delta[0][2]-delta[2][0])/(2*math.sin(theta)),
                  (delta[1][0]-delta[0][1])/(2*math.sin(theta))]
            x,y,z=axis; c=math.cos(theta*t); sn=math.sin(theta*t); v=1-c
            turn=[[c+x*x*v,x*y*v-z*sn,x*z*v+y*sn],
                  [y*x*v+z*sn,c+y*y*v,y*z*v-x*sn],
                  [z*x*v-y*sn,z*y*v+x*sn,c+z*z*v]]
            return mm(a,turn)
        d=self.data; c=d['conversion']['sourceRootToModelBasis']
        r0,p0=G.rigid(d['samples'][0]['poses'][G.BODY_BONE])
        identity=[[1,0,0],[0,1,0],[0,0,1]]
        for frame in range(61):
            progress=frame/60; source_index=progress*126
            i=min(int(source_index),125); t=source_index-i
            ra,pa=G.rigid(d['samples'][i]['poses'][G.BODY_BONE])
            rb,pb=G.rigid(d['samples'][i+1]['poses'][G.BODY_BONE])
            rotation=mm(c,mm(mm(tr(r0),interpolate(ra,rb,t)),tr(c)))
            position=[a+(b-a)*t for a,b in zip(pa,pb)]
            translation=[32*v for v in mv(c,mv(tr(r0),minus(position,p0)))]
            if progress>.95:
                blend=(progress-.95)/.05; blend=blend*blend*(3-2*blend)
                rotation=interpolate(rotation,identity,blend)
                translation=[v*(1-blend) for v in translation]
            if frame in (0,60): rotation,translation=identity,[0,0,0]
            body,actual,_,_=G.sample(progress,d)
            # The established near-equal quaternion normalized-lerp shortcut is
            # indistinguishable here within 0.000002 radians, unchanged from W197.
            self.assertLess(angle(rotation,body),2e-6,frame)
            self.assertVec(actual,translation,1e-8)


if __name__=='__main__':
    unittest.main()
