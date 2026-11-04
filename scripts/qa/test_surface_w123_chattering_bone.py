#!/usr/bin/env python3
"""Targeted offline structural/provenance regression for W128 Chattering Bone."""
import base64
import copy
import io
import json
from pathlib import Path
import sys
import unittest
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import generate_surface_w123_chattering_bone as g

class ChatteringBoneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design=json.loads((g.ROOT/(g.ART+'design.json')).read_bytes())
        cls.model=json.loads((g.ROOT/g.MODEL).read_bytes())
        cls.manifest=json.loads((g.ROOT/(g.ART+'manifest.json')).read_bytes())
        cls.bb=json.loads((g.ROOT/(g.ART+'inspection.bbmodel')).read_bytes())
        cls.tex=np.asarray(Image.open(g.ROOT/g.TEXTURE))
        cls.elements=cls.model['elements']

    def assert_clear_segment(self,a,b):
        a=np.array(a,float);b=np.array(b,float)
        for e in self.elements:
            r=e.get('rotation',{});R=g.rotation(r);origin=np.array(r.get('origin',[0,0,0]))
            p=(a-origin)@R+origin;q=(b-origin)@R+origin;v=q-p
            lo=np.array(e['from']);hi=np.array(e['to']);t0=0.;t1=1.
            for axis in range(3):
                if abs(v[axis])<1e-10:
                    if p[axis]<lo[axis] or p[axis]>hi[axis]:t1=-1;break
                else:
                    ts=sorted([(lo[axis]-p[axis])/v[axis],(hi[axis]-p[axis])/v[axis]])
                    t0=max(t0,ts[0]);t1=min(t1,ts[1])
            self.assertGreater(t0,t1,'Opening blocked by '+e['name'])

    def test_emitted_full_only_budget_and_semantic_volumes(self):
        self.assertEqual(len(self.elements),self.manifest['assembled_elements'])
        self.assertLessEqual(len(self.elements),1000)
        self.assertGreaterEqual(len(self.elements),75)
        self.assertEqual(len(self.elements)*6,self.manifest['emitted_faces'])
        self.assertEqual(set(self.design['parts']),{'full'})
        self.assertEqual(self.manifest['counts']['groups']['magazine'],3)
        self.assertEqual(sum(self.manifest['counts']['groups'].values()),len(self.elements))
        self.assertFalse(any((g.ROOT/(g.MODEL[:-5]+suffix+'.json')).exists() for suffix in ('_body','_magazine')))
        thick=0
        for e in self.elements:
            size=np.array(e['to'])-e['from'];self.assertTrue(np.all(size>0))
            self.assertNotIn('vertices',e);self.assertNotIn('triangles',e)
            thick+=int(np.all(size>.35))
        self.assertGreaterEqual(thick,12)

    def test_canonical_frame_display_and_scale(self):
        canonical=json.loads((g.ROOT/g.BASE).read_bytes())
        self.assertEqual(canonical['display'],self.model['display'])
        meta=json.loads((g.ROOT/'art/blockbench/weapons/w30/chattering_bone.bbmodel').read_bytes())['destiny_w30']
        self.assertEqual(self.design['frame']['source_scale'],meta['scale'])
        self.assertEqual(self.design['frame']['anchor'],[8,8,8])
        self.assertEqual(self.design['frame']['muzzle_axis'],'-Z')
        ps=np.concatenate([g.vertices(e) for e in self.elements]);bounds=np.array([ps.min(0),ps.max(0)])
        self.assertTrue(np.all(abs(bounds-np.array(meta['model_bounds']))<.25),str(bounds))
        e=next(e for e in self.elements if e['name']=='grip_wrist')
        center=(np.array(e['from'])+e['to'])/2
        np.testing.assert_allclose(center,[8,9.36,8.22],atol=.00001)

    def test_real_bore_depth(self):
        for dx,dy in [(0,0),(.12,0),(0,.12)]:
            self.assert_clear_segment([8+dx,11.12+dy,-8.8],[8+dx,11.12+dy,-4.50])
        self.assertTrue(any(e['name']=='bore_back' for e in self.elements))

    def test_real_optic_through_opening(self):
        for dx,dy in [(0,0),(.15,0),(0,.15),(-.15,-.10)]:
            self.assert_clear_segment([8+dx,12.99+dy,6.70],[8+dx,12.99+dy,8.2])

    def test_real_guard_and_nose_openings(self):
        for y,z in [(8.4,6.3),(7.6,7.1),(8.5,7.7)]:
            self.assert_clear_segment([6.9,y,z],[9.1,y,z])
        self.assert_clear_segment([8,10.4,-4.9],[8,10.4,-4.6])

    def test_atlas_faces_and_gutters_are_opaque(self):
        self.assertEqual(self.tex.shape,(1024,1024,4))
        occupancy=np.zeros((1024,1024),bool)
        mapping={(i['element'],i['face']):i['rect'] for i in self.design['atlas']['islands']}
        for e in self.elements:
            self.assertEqual(set(e['faces']),set(g.FACES))
            for face,f in e['faces'].items():
                self.assertEqual(f['texture'],'#0');self.assertEqual(len(f['uv']),4)
                x0,y0,x1,y1=mapping[(e['name'],face)]
                self.assertEqual(f['uv'],[q*16/1024 for q in (x0,y0,x1,y1)])
                self.assertTrue(np.all(self.tex[y0-2:y1+2,x0-2:x1+2,3]==255))
                self.assertFalse(occupancy[y0-2:y1+2,x0-2:x1+2].any(),'Overlapping UV padding')
                occupancy[y0-2:y1+2,x0-2:x1+2]=True
                np.testing.assert_array_equal(self.tex[y0:y1,x0-1],self.tex[y0:y1,x0])
                np.testing.assert_array_equal(self.tex[y0:y1,x1],self.tex[y0:y1,x1-1])

    def test_face_palette_contains_default_ivory_and_violet(self):
        specs={s['geometry']['name']:s for s in self.design['parts']['full']}
        values={}
        for island in self.design['atlas']['islands']:
            x0,y0,x1,y1=island['rect'];mat=specs[island['element']]['material']
            values.setdefault(mat,[]).append(self.tex[y0:y1,x0:x1,:3].reshape(-1,3))
        ivory=np.concatenate(values['ivory']).mean(0);violet=np.concatenate(values['violet']).mean(0)
        self.assertGreater(ivory[0],180);self.assertGreater(ivory[1],175)
        self.assertGreater(violet[2],violet[0]*1.3)
        self.assertLess(violet.mean(),85)

    def test_embedded_inspection_geometry_and_texture_parity(self):
        self.assertEqual(len(self.bb['elements']),len(self.elements))
        self.assertEqual(self.bb['display'],self.model['display'])
        embedded=base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1])
        self.assertEqual(embedded,(g.ROOT/g.TEXTURE).read_bytes())
        for e,b in zip(self.elements,self.bb['elements']):
            self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            self.assertEqual([e.get('rotation',{}).get(a,0) for a in 'xyz'],b['rotation'])
            for f in g.FACES:self.assertEqual(b['faces'][f]['uv'],[q*1024/16 for q in e['faces'][f]['uv']])
        ids=[x for group in self.bb['outliner'] for x in group['children']]
        self.assertEqual(len(ids),len(set(ids)));self.assertEqual(set(ids),{e['uuid'] for e in self.bb['elements']})

    def test_input_and_output_provenance(self):
        for p,h in self.manifest['input_sha256'].items():self.assertEqual(g.sha((g.ROOT/p).read_bytes()),h,p)
        for p,h in self.manifest['raw_input_sha256'].items():self.assertEqual(g.sha(Path(p).read_bytes()),h,p)
        for p,h in self.manifest['output_sha256'].items():self.assertEqual(g.sha((g.ROOT/p).read_bytes()),h,p)
        self.assertFalse(self.manifest['native_accepted'])
        self.assertEqual(g.sha(Path(g.__file__).read_bytes()),self.manifest['generator_sha256'])

    def test_actual_fbx_is_reference_only(self):
        meshes,meta=g.source_meshes()
        self.assertEqual(len(meshes),11)
        self.assertEqual(sum(len(m['faces']) for m in meshes),11558)
        self.assertEqual(meta['source_triangles'],13882)
        self.assertEqual(self.manifest['fbx_reference_triangles'],11558)
        self.assertTrue(all(s['geometry']['name'] not in meta['source_objects'] for s in self.design['parts']['full']))

    def test_geometry_artifact_regeneration(self):
        for p,data in g.generate(include_comparison=False).items():
            if p.endswith('manifest.json'):continue  # Full manifest additionally hashes the comparison.
            self.assertEqual((g.ROOT/p).read_bytes(),data,p)

    def test_ownership_exact_ten(self):
        batch=json.loads((g.ROOT/'docs/qa/2026-10-26/w128/batch.json').read_bytes())
        owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w128-chattering_bone'))
        self.assertEqual(len(owned),10)
        generated=set(self.manifest['output_sha256'])|{g.ART+'manifest.json'}
        self.assertEqual(owned-generated,{'scripts/generate_surface_w123_chattering_bone.py','scripts/qa/test_surface_w123_chattering_bone.py',g.REPORT})

if __name__=='__main__':unittest.main()
