#!/usr/bin/env python3
"""Scoped W197 source fidelity and W198 dense real-bank regression; no apps/builds."""
import copy
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import struct
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('izanagi_w197', ROOT/'scripts/generate_izanagi_presentation_w91.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
EVIDENCE = Path('/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-27/w196/samples/sniper_rifle_ececad46.json.gz')


def matrix_product(a,b):
    return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]


def distance(a,b):
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))


class SourceMotionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=g.dataset()
        cls.base=json.loads((g.ASSETS/'models/item/weapon/izanagis_burden.json').read_bytes())
        cls.graph=json.loads(g.ITEM.read_bytes())['model']

    def test_pinned_source_tags_times_hash_mapping_and_no_outer_fbx_bake(self):
        d=self.data
        self.assertEqual(d['boneIds'], {'body':'4A0810C4','magazine':'52EDE88C','bolt':'69768858'})
        self.assertFalse(d['honedExclusivityConfirmed'])
        self.assertFalse(d['conversion']['outerFbxMatrixApplied'])
        self.assertEqual(d['unmappedBone'],'72997168')
        self.assertEqual(d['sourceManifestSHA256'],'a66c17bbe1fa158f14259b854f19841f6884241dbc233d3238dfaef01772fa73')
        self.assertEqual(d['sourceBoneMapSHA256'],'e8822bec7855e7c7e12b2fd0391dfb3ba6d01420140fb6a1badf9e39fa4113b1')
        for kind,tag in [('ordinary','80A8A140'),('honed','80A8A14D')]:
            clip=d['clips'][kind]
            self.assertEqual(clip['tag'],tag)
            self.assertEqual([f['frame'] for f in clip['samples']],list(range(1,103)))
            for i,f in enumerate(clip['samples']): self.assertAlmostEqual(f['seconds'],i/30)
            self.assertAlmostEqual(clip['durationSeconds'],101/30)
        self.assertGreater(d['conversion']['modelUnitsPerSourceUnit'],40)
        self.assertLess(d['conversion']['modelUnitsPerSourceUnit'],45)

    @unittest.skipUnless(EVIDENCE.exists(),'W196 read-only evidence not installed; standard generation stays portable')
    def test_every_compact_matrix_is_verbatim_evaluated_evidence(self):
        raw=gzip.decompress(EVIDENCE.read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(),self.data['evaluatedUncompressedSHA256'])
        original=json.loads(raw); by_hash={b['name']:i for i,b in enumerate(original['bones'])}
        for kind,tag in g.TAGS.items():
            clip=next(c for c in original['clips'] if c['tag']==tag)
            for actual,source in zip(self.data['clips'][kind]['samples'],clip['frames']):
                for part,bone in self.data['boneIds'].items():
                    self.assertEqual(actual['matrices'][part],source['matrices'][by_hash[bone]])
                    self.assertEqual(self.data['bones'][part],original['bones'][by_hash[bone]])
        self.assertEqual(g.extract_source(EVIDENCE),g.MOTION.read_bytes())

    def test_root_matrix_composition_matches_raw_source_not_euler_addition(self):
        for kind in g.TAGS:
            p=40/101
            raw=self.data['clips'][kind]['samples']
            a,b=raw[0]['matrices']['body'],raw[40]['matrices']['body']
            # Independent raw rotation calculation; source tiny shear permits2e-4.
            transpose=[[a[j][i] for j in range(3)] for i in range(3)]
            rel=matrix_product(transpose,[r[:3] for r in b[:3]])
            c=[r[:3] for r in g.BASIS[:3]]
            expected=matrix_product(matrix_product(c,rel),list(map(list,zip(*c))))
            transform=g.motion(kind,p)['body']
            for i in range(3):
                for j in range(3): self.assertAlmostEqual(expected[i][j],transform[i][j],delta=2e-4)
            displacement=[sum(a[k][i]*(b[k][3]-a[k][3]) for k in range(3)) for i in range(3)]
            expected_displacement=[sum(c[i][j]*displacement[j] for j in range(3))*self.data['conversion']['modelUnitsPerSourceUnit'] for i in range(3)]
            actual=g.point(transform,[8,8,8])
            self.assertLess(distance(actual,[8+v for v in expected_displacement]),.002)
            self.assertGreater(distance(actual,[8,8,8]),1)

    def test_magazine_really_withdraws_but_bolt_has_no_invented_cycle(self):
        for kind in g.TAGS:
            neutral=g.source_pose(kind,0)
            baseline={p:g.mul(g.inv(neutral['body']),neutral[p]) for p in ('magazine','bolt')}
            maxima={'magazine':0,'bolt':0}
            for i in range(102):
                pose=g.source_pose(kind,i/101)
                for p in maxima:
                    local=g.mul(g.inv(pose['body']),pose[p])
                    maxima[p]=max(maxima[p],distance([local[j][3] for j in range(3)],[baseline[p][j][3] for j in range(3)]))
            self.assertGreater(maxima['magazine'],.5)
            self.assertLess(maxima['bolt'],5e-7)
            transforms=g.motion(kind,.2)
            mag=g.mul(g.inv(transforms['body']),transforms['magazine'])
            anchor=self.data['conversion']['anchors']['magazine']
            self.assertGreater(distance(g.point(mag,anchor),anchor),10)
            bolt=g.mul(g.inv(transforms['body']),transforms['bolt'])
            self.assertLess(max(abs(v-(i==j)) for i,row in enumerate(bolt) for j,v in enumerate(row)),.001)

    def test_neutral_endpoints_all_parts_hands_and_grips_and_final_blend_scope(self):
        for kind in g.TAGS:
            for progress in (0,1):
                for part in g.PARTS:
                    self.assertEqual(g.display_for(self.base['display'],kind,progress,part),self.base['display'])
                    for branch,expected in [('native',self.base['display']),('twohand',g.two_hand_display(self.base['display']))]:
                        name=f'izanagis_burden_{kind}_{int(progress*60):02}_{part}_{branch}.json'
                        self.assertEqual(json.loads((g.MODEL_DIR/name).read_bytes())['display'],expected)
            for progress in (.05,.2,.5,.9): self.assertEqual(g.motion(kind,progress),g.motion(kind,progress,False))

    def test_partition_preserves_geometry_uv_grip_ads_and_charged(self):
        found=[]
        for part,count in [('body',76),('magazine',1),('bolt',2)]:
            model=json.loads((g.MODEL_DIR/f'izanagis_burden_{part}.json').read_bytes())
            self.assertEqual(len(model['elements']),count)
            self.assertEqual(model['elements'],[self.base['elements'][i] for i in g.part_indices(part)])
            self.assertEqual(model['textures'],self.base['textures'])
            found.extend(g.part_indices(part))
        self.assertEqual(sorted(found),list(range(79)))
        self.assertEqual(g.BOLT,(25,77))
        charged=json.loads((g.MODEL_DIR/'izanagis_burden_charged.json').read_bytes())
        self.assertEqual(charged['elements'][:79],self.base['elements'])
        self.assertEqual(charged['display'],self.base['display'])
        self.assertEqual(len(charged['elements']),95)
        self.assertLess(len(charged['elements']),1000)

    def test_both_hand_matrix_composition_and_twohand_carrier_inverse(self):
        for kind in g.TAGS:
            transforms=g.motion(kind,.35)
            for part in g.PARTS:
                native=g.display_for(self.base['display'],kind,.35,part)
                twohand=g.two_hand_display(native)
                for left,context in [(False,g.FP[0]),(True,g.FP[1])]:
                    mirror=g.identity();mirror[0][0]=-1;mirror[0][3]=16
                    local=g.mul(g.mul(mirror,transforms[part]),mirror) if left else transforms[part]
                    for p in ([8,8,8],[9,10,7]):
                        actual=g.H['item_point'](p,native[context],left)
                        expected=g.H['item_point'](g.point(local,p),self.base['display'][context],left)
                        self.assertLess(distance(actual,expected),3e-8)
                        carried=g.rotate(g.H['item_point'](p,twohand[context],left),[0,-10 if left else 10,0])
                        carried[0]-=.641864*16*(-1 if left else 1)
                        self.assertLess(distance(actual,carried),3e-8)

    def test_real_61_sample_bank_reproduces_source_curves_for_every_part_hand_and_grip(self):
        self.assertEqual((g.RELOAD_SAMPLES,g.RELOAD_INTERVALS),(61,60))
        self.assertEqual(hashlib.sha256(g.MOTION.read_bytes()).hexdigest(),
                         '16d333d78c42336e58116519b4fa951c5242326541ae7f5d8c33530fd3796e38')
        manifest=json.loads((g.ART/'asset-outputmanifest.json').read_bytes())
        self.assertEqual(manifest['samplesPerReload'],61)
        self.assertEqual(manifest['intervalsPerReload'],60)
        poses=json.loads((g.ART/'asset-poses.json').read_bytes())['samples']
        self.assertEqual(len(poses),122)
        for kind in g.TAGS:
            samples=[p for p in poses if p['kind']==kind]
            self.assertEqual([p['frame'] for p in samples],list(range(61)))
            signatures=set()
            for frame,sample in enumerate(samples):
                progress=frame/60
                self.assertEqual(sample['progress'],progress)
                self.assertAlmostEqual(sample['sourceSeconds'],progress*101/30)
                self.assertEqual(sample['partMatrices'],g.motion(kind,progress))
                for part in g.PARTS:
                    expected=g.display_for(self.base['display'],kind,progress,part)
                    for branch,display in [('native',expected),('twohand',g.two_hand_display(expected))]:
                        path=g.MODEL_DIR/f'izanagis_burden_{kind}_{frame:02}_{part}_{branch}.json'
                        actual=json.loads(path.read_bytes())
                        self.assertEqual(actual['parent'],f'destiny:{g.KEY}_{part}')
                        self.assertEqual(actual['display'],display)
                body=json.loads((g.MODEL_DIR/f'izanagis_burden_{kind}_{frame:02}_body_native.json').read_bytes())
                signatures.add(json.dumps(body['display'],sort_keys=True))
            self.assertEqual(len(signatures),60,'Only the exact neutral endpoints may repeat')

    def test_all_40_new_intermediate_samples_are_real_source_poses_between_old_samples(self):
        for kind in g.TAGS:
            for frame in range(1,60):
                if frame%3==0: continue
                old_lo=frame//3/20
                old_hi=(frame//3+1)/20
                actual=json.loads((g.MODEL_DIR/f'izanagis_burden_{kind}_{frame:02}_body_native.json').read_bytes())['display']
                self.assertNotEqual(actual,g.display_for(self.base['display'],kind,old_lo,'body'))
                self.assertNotEqual(actual,g.display_for(self.base['display'],kind,old_hi,'body'))
                # Independent source translation interpolation at this new time, before
                # the existing final 10% neutral blend, rather than a duplicated bank pose.
                source_frame=frame/60*101;lo=int(source_frame);weight=source_frame-lo
                raw=self.data['clips'][kind]['samples']
                pose=g.source_pose(kind,frame/60)
                for part in g.PARTS:
                    for axis in range(3):
                        a=raw[lo]['matrices'][part][axis][3]
                        b=raw[lo+1]['matrices'][part][axis][3]
                        self.assertAlmostEqual(pose[part][axis][3],a+(b-a)*weight,delta=1e-12)
                    # Slerp traverses the shortest rotation at a constant angular rate.
                    a=g.rigid(raw[lo]['matrices'][part]);b=g.rigid(raw[lo+1]['matrices'][part])
                    def angle(x,y):
                        cosine=(sum(x[i][j]*y[i][j] for i in range(3) for j in range(3))-1)/2
                        return math.acos(max(-1,min(1,cosine)))
                    self.assertAlmostEqual(angle(a,pose[part]),angle(a,b)*weight,delta=2e-6)

    def test_float32_thresholds_generation_offsets_and_adjacent_bucket_boundaries(self):
        # Independent Java float arithmetic and bit-adjacent boundary probes.
        single=lambda v:struct.unpack('!f',struct.pack('!f',v))[0]
        def below(v):
            bits=struct.unpack('!I',struct.pack('!f',v))[0]
            return struct.unpack('!f',struct.pack('!I',bits-1))[0]
        for kind,start in [('ordinary',0),('honed',2)]:
            for frame in range(61):
                threshold=single(start+single(frame/60))
                for offset in (0,.00025,.0005):
                    value=single(threshold+single(offset))
                    for context in g.FP:
                        for flag,branch in [(False,'native'),(True,'twohand')]:
                            expected=[f'destiny:{g.KEY}_{kind}_{frame:02}_{part}_{branch}' for part in g.PARTS]
                            self.assertEqual(g.evaluate(self.graph,context,'hip',flag,0,value),expected)
                            if frame:
                                previous=[f'destiny:{g.KEY}_{kind}_{frame-1:02}_{part}_{branch}' for part in g.PARTS]
                                self.assertEqual(g.evaluate(self.graph,context,'hip',flag,0,below(threshold)),previous)
        for context in g.FP:
            for flag in (False,True):
                charged=g.evaluate(self.graph,context,'scope',flag,.65,4)
                for offset in (0,.00025,.0005):
                    self.assertEqual(g.evaluate(self.graph,context,'scope',flag,.65,single(4+single(offset))),charged)

    def test_legacy_preview_names_keep_original_snapshot_progress(self):
        source=json.loads(g.SOURCE.read_bytes())
        for kind,legacy_frame in [('ordinary',7),('ordinary',14),('honed',10),('honed',17)]:
            preview=json.loads((g.ART/f'asset-preview-{kind}-{legacy_frame:02}.bbmodel').read_bytes())
            progress=legacy_frame/20
            self.assertEqual(preview['display'],g.display_for(self.base['display'],kind,progress,'body'))
            expected=g.preview_model(source,g.posed_elements(self.base['elements'],kind,progress),[],[0,0,0],
                                     preview['display'],b'')
            self.assertEqual(preview,expected)

    def test_source_and_finite_transform_guards(self):
        for p in (-.01,1.01):
            with self.assertRaises(ValueError): g.source_pose('ordinary',p)
        for change in ('nan','scale','affine'):
            m=g.identity()
            if change=='nan':m[0][0]=float('nan')
            elif change=='scale':m[0][0]=.01
            else:m[3][0]=1
            with self.assertRaises(ValueError):g.rigid(m)
        for field,value in [('sampleSpace','world'),('sourceFbxSHA256','invented')]:
            d=copy.deepcopy(self.data);d[field]=value
            with patch.object(Path,'read_bytes',return_value=json.dumps(d).encode()):
                with self.assertRaises(ValueError):g.dataset()
        d=copy.deepcopy(self.data);d['conversion']['basis'][0][0]=1
        with patch.object(Path,'read_bytes',return_value=json.dumps(d).encode()):
            with self.assertRaises(ValueError):g.dataset()


if __name__=='__main__':unittest.main()
