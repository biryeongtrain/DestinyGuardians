#!/usr/bin/env python3
"""Targeted offline Austringer regression. Native acceptance belongs to master."""
import base64
import io
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_austringer.py'))
CANONICAL_SHA='386c940d7e18bda739d7d7e77664c27db7e2e5d964fb79e0a6d32e8bc3ba0312'
PHOTO_SHA='3890337feb2d05235caf810125e64b4520a8a9a95650d6fb027dca01b4b9d02e'

class AustringerSurface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=json.loads((ROOT/G['MODEL']).read_bytes())
        cls.d=json.loads((ROOT/(G['ART']+'design.json')).read_bytes())
        cls.manifest=json.loads((ROOT/(G['ART']+'manifest.json')).read_bytes())
        cls.helper=G['helper']()
        cls.elements=cls.model['elements'];cls.byname={e['name']:e for e in cls.elements}
        cls.atlas=np.array(Image.open(ROOT/G['TEXTURE']))

    @classmethod
    def occupied(cls,point,e):
        r=e['rotation'];o=np.array(r['origin'])
        local=(np.array(point)-o)@cls.helper['rotation'](r)+o
        return bool(np.all(local>np.array(e['from'])+1e-6) and np.all(local<np.array(e['to'])-1e-6))

    def air(self,p):
        self.assertFalse([e['name'] for e in self.elements if self.occupied(p,e)],str(p))

    def test_native_cuboid_schema_and_one_assembled_budget(self):
        self.assertEqual(set(self.model),{'credit','textures','elements','display'})
        self.assertEqual(self.model['textures']['0'],'destiny:item/weapon/w123/austringer')
        self.assertTrue(0<len(self.elements)<=1000)
        self.assertEqual(len(self.byname),len(self.elements))
        self.assertEqual(self.manifest['native_elements'],len(self.elements))
        self.assertEqual(self.manifest['emitted_faces'],len(self.elements)*6)
        self.assertTrue(self.manifest['full_only'])
        for e in self.elements:
            self.assertEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
            self.assertEqual(set(e['faces']),set(G['FACES']))
            for a,b in zip(e['from'],e['to']):
                self.assertTrue(math.isfinite(a) and math.isfinite(b) and -16<=a<b<=32)
                self.assertGreater(b-a,.06)
            for f in e['faces'].values():
                self.assertEqual(set(f),{'uv','texture'});self.assertEqual(f['texture'],'#0')
                self.assertTrue(all(math.isfinite(x) and 0<=x<=16 for x in f['uv']))
                self.assertGreater(f['uv'][2],f['uv'][0]);self.assertGreater(f['uv'][3],f['uv'][1])

    def test_read_only_canonical_frame_display_and_grip_mass(self):
        canonical=(ROOT/G['BASE']).read_bytes()
        self.assertEqual(G['sha'](canonical),CANONICAL_SHA)
        self.assertEqual(self.model['display'],json.loads(canonical)['display'])
        self.assertEqual(self.d['anchor'],[8,8,8])
        self.assertAlmostEqual(self.d['source']['scale'],37.014420290213536)
        self.assertEqual(self.d['source']['source_axis'],{'length':1,'thin':0,'muzzle_sign':-1})
        p=np.concatenate([self.helper['vertices'](e) for e in self.elements]);b=np.array(self.d['source']['model_bounds'])
        self.assertTrue(np.all(abs(p.min(0)-b[0])<.20))
        self.assertTrue(np.all(abs(p.max(0)-b[1])<.20))
        # Independent hand-frame landmarks prevent a recentered or hollow grip.
        for point in ([8,8.0,8.2],[8,9.4,7.6],[8,10.7,7.0],[8,12.7,-1.5],[8,12.43,4.3]):
            self.assertTrue(any(self.occupied(point,e) for e in self.elements),point)
        self.assertGreater(self.byname['Shroud_mass']['to'][0]-self.byname['Shroud_mass']['from'][0],1.6)
        self.assertGreater(self.byname['Grip_heel']['to'][0]-self.byname['Grip_heel']['from'][0],1.3)

    def test_bore_and_optic_have_depth_and_solid_terminations(self):
        for y,zs,radius in ((12.77,(-6.29,-6.0,-5.6,-5.1,-4.99),.26),
                            (9.94,(-2.04,-1.9,-1.72,-1.49),.21)):
            for z in zs:
                self.air([8,y,z])
                for a in range(0,360,45):
                    t=math.radians(a);self.air([8+radius*math.cos(t),y+radius*math.sin(t),z])
        self.assertTrue(self.occupied([8,12.77,-4.80],self.byname['Muzzle_back']))
        self.assertTrue(self.occupied([8,9.94,-1.41],self.byname['Optic_lens']))
        self.assertTrue(any(self.occupied([8.55,12.77,-5.55],e) for e in self.elements))
        self.assertTrue(any(self.occupied([8.38,9.94,-1.63],e) for e in self.elements))

    def test_guard_underlug_and_rear_notch_are_actual_air(self):
        for point in self.d['air_probes'].values():self.air(point)
        for x in (7.82,8,8.18):
            for y in (9.65,9.9,10.15):
                for z in (4.45,4.9,5.2):self.air([x,y,z])
        for x in (7.7,8,8.3):
            for z in (-4,-3,-2):self.air([x,11.31,z])
        for x in (7.91,8,8.09):self.air([x,14.0,5.24])

    def test_uv_faces_are_opaque_dilated_nonoverlapping_and_proportioned(self):
        self.assertEqual(self.atlas.shape,(1024,1024,4))
        ledger=self.d['atlas']['islands'];self.assertEqual(len(ledger),6*len(self.elements))
        mask=np.zeros((1024,1024),bool)
        for q in ledger:
            x0,y0,x1,y1=q['pixels'];s=np.s_[y0-2:y1+2,x0-2:x1+2]
            self.assertFalse(mask[s].any(),q);mask[s]=True
            self.assertTrue((self.atlas[s][:,:,3]==255).all(),q)
            p=G['face_points'](self.byname[q['element']],q['face'])
            width=np.linalg.norm(p[1]-p[0]);height=np.linalg.norm(p[3]-p[0])
            if min(x1-x0,y1-y0)>4:
                self.assertLessEqual(max((x1-x0-1)/width,(y1-y0-1)/height),min((x1-x0)/width,(y1-y0)/height)+1e-5)
        self.assertGreater(self.d['atlas']['used_texels'],250000)
        for e in (self.byname['Shroud_mass'],self.byname['Grip_heel']):
            self.assertNotEqual(e['faces']['east']['uv'],e['faces']['west']['uv'])
        # Opaque UV paint carries the first front triangle rather than alpha.
        uv=self.byname['Nose_flank_-1']['faces']['west']['uv'];x0,y0,x1,y1=[round(q*64) for q in uv]
        self.assertGreater(np.all(self.atlas[y0:y1,x0:x1,:3]==[29,32,31],axis=2).sum(),10)

    def test_editable_inspection_matches_full_texture_and_frame(self):
        bb=json.loads((ROOT/(G['ART']+'inspection.bbmodel')).read_bytes())
        self.assertEqual(len(bb['elements']),len(self.elements))
        self.assertEqual(bb['display'],self.model['display'])
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
        self.assertEqual(len({e['uuid'] for e in bb['elements']}),len(self.elements))
        self.assertEqual(set(v for g in bb['outliner'] for v in g['children']),{e['uuid'] for e in bb['elements']})
        self.assertFalse(bb['destiny_w129']['nativeAccepted'])
        for e,b in zip(self.elements,bb['elements']):
            self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
            self.assertEqual(b['rotation'],[e['rotation'][a] for a in 'xyz'])

    def test_reference_evidence_and_untouched_graph_hashes(self):
        self.assertEqual(G['sha'](G['PHOTO'].read_bytes()),PHOTO_SHA)
        refs=json.loads((ROOT/'art/weapons/w31/references.json').read_bytes())
        self.assertEqual(next(r['sha256'] for r in refs if r['id']=='austringer'),PHOTO_SHA)
        self.assertIn('no Austringer palette override',self.d['paint_evidence']['palette_override'])
        self.assertEqual(self.d['palette']['gold'],[202,187,130])
        for p,h in self.manifest['input_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        for p,h in self.manifest['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(p).read_bytes()),h,p)
        for p,h in self.manifest['output_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        self.assertFalse(self.manifest['native_accepted'])
        self.assertEqual(self.manifest['alpha_contour_elements'],0)
        self.assertEqual(self.manifest['triangle_adapter_elements'],0)

    def test_exact_owned_artifacts_and_deterministic_generation(self):
        batch=json.loads((ROOT/'docs/qa/2026-10-26/w129/batch.json').read_bytes())
        owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w129-austringer'))
        outputs=G['generate']()
        self.assertEqual(set(outputs)|{G['GENERATOR'],G['TEST'],G['WORKER']},owned)
        self.assertEqual(len(owned),10)
        for p,data in outputs.items():self.assertEqual((ROOT/p).read_bytes(),data,p)
        self.assertEqual(Image.open(io.BytesIO(outputs[G['ART']+'comparison.png'])).size,(1800,1900))
        self.assertEqual([p for p in outputs if p.startswith(G['ASSET']+'models/')],[G['MODEL']])

if __name__=='__main__':unittest.main(verbosity=2)
