#!/usr/bin/env python3
"""W141 focused offline art checks. Not a visual-fidelity or performance certificate."""
import base64
import hashlib
import json
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_allied_demand.py'))

def read(p):return json.loads((ROOT/p).read_bytes())
def inside(p,e):
    p=np.array(p,float);r=e.get('rotation')
    if r:
        o=np.array(r['origin']);p=(p-o)@G['H']['rotation']({r['axis']:r['angle']})+o
    return bool(np.all(p>np.array(e['from'])+1e-7) and np.all(p<np.array(e['to'])-1e-7))

class AlliedArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=read(G['ART']+'design.json');cls.m=read(G['ART']+'manifest.json');cls.model=read(G['MODEL'])
        cls.es=cls.model['elements'];cls.lookup={e['name']:e for e in cls.es};cls.bb=read(G['ART']+'inspection.bbmodel')
        cls.px=np.array(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))

    def test_semantic_solids_schema_and_budget(self):
        self.assertEqual(85,len(self.es));self.assertEqual(85,len(self.lookup));self.assertLessEqual(len(self.es),1000)
        self.assertEqual(0,self.m['alpha_body_elements']);self.assertEqual(0,self.m['triangle_adapter_elements'])
        for e in self.es:
            self.assertLessEqual(set(e),{'name','from','to','faces','rotation'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']));self.assertTrue(np.isfinite(G['vertices'](e)).all())
            self.assertEqual(set(G['FACES']),set(e['faces']))
        self.assertGreater(self.lookup['slide_core']['to'][2]-self.lookup['slide_core']['from'][2],7)
        self.assertGreater(self.lookup['green_grip_core']['to'][1]-self.lookup['green_grip_core']['from'][1],3)

    def test_canonical_display_and_frame_preserved(self):
        self.assertEqual(read(G['BASE'])['display'],self.model['display'])
        meta=read(G['BB'])['destiny_w30'];self.assertEqual(meta['anchor'],self.m['source_anchor']);self.assertEqual(meta['scale'],self.m['source_scale'])
        self.assertEqual('-Z',self.d['coordinate_policy']['muzzle'])
        self.assertTrue(inside([8,8.8,8.95],self.lookup['green_grip_core']))
        self.assertTrue(np.all(abs(np.array(self.m['actual_bounds'])-meta['model_bounds'])<.3))

    def test_physical_bore_guard_and_sight(self):
        for p in ([8,12.536,-4.7],[8,12.536,-3.8],[8,10.1,6.1],[8,13.35,8.4]):
            self.assertFalse(any(inside(p,e) for e in self.es),p)
        self.assertTrue(inside([8,12.536,-3.45],self.lookup['deep_bore_backstop']))
        self.assertTrue(inside([8,9.43,6.5],self.lookup['guard_bottom']))

    def test_face_uv_opacity_gutters(self):
        self.assertEqual((1024,1024,4),self.px.shape);cover=np.zeros((1024,1024),bool)
        self.assertEqual(len(self.es)*6,len(self.d['atlas']['islands']))
        for row in self.d['atlas']['islands']:
            x,y,X,Y=row['pixels'];self.assertTrue(np.all(self.px[y-2:Y+2,x-2:X+2,3]==255))
            self.assertFalse(cover[y-2:Y+2,x-2:X+2].any());cover[y-2:Y+2,x-2:X+2]=True
            self.assertTrue(np.allclose(self.lookup[row['element']]['faces'][row['face']]['uv'],np.array([x,y,X,Y])/64))

    def test_reference_provenance(self):
        meshes,meta=G['source_meshes']();self.assertEqual(10089,sum(len(m['faces']) for m in meshes))
        self.assertEqual(5,len(meshes));self.assertEqual(10089,meta['source_triangles'])
        ref=next(r for r in read('art/weapons/w31/references.json') if r['id']=='allied_demand')
        self.assertEqual(ref['sha256'],hashlib.sha256(G['PHOTO'].read_bytes()).hexdigest())
        for p,h in self.d['input_sha256'].items():self.assertEqual(h,G['sha']((ROOT/p).read_bytes()),p)
        for p,h in self.d['raw_input_sha256'].items():self.assertEqual(h,G['sha'](Path(p).read_bytes()),p)

    def test_default_materials_and_source_motif(self):
        self.assertGreater(G['PALETTE']['green'][1],G['PALETTE']['green'][0]*1.8)
        self.assertTrue(any(s['motif']=='wolf' for s in self.d['parts']))
        self.assertTrue(any(s['motif']=='perforated' for s in self.d['parts']))
        self.assertIn('not physical holes',self.m['limitations'][0])

    def test_editable_bb_manifest_full_only(self):
        self.assertEqual(len(self.es),len(self.bb['elements']))
        self.assertEqual(len(self.es),sum(len(g['children']) for g in self.bb['outliner']))
        self.assertEqual((ROOT/G['TEXTURE']).read_bytes(),base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]))
        self.assertTrue(self.m['full_only']);self.assertFalse(self.m['native_accepted'])
        for path,h in self.m['output_sha256'].items():self.assertEqual(h,G['sha']((ROOT/path).read_bytes()),path)
        self.assertFalse((ROOT/G['MODEL'].replace('.json','_magazine.json')).exists())

    def test_deterministic_generation(self):
        for path,b in G['generate'](include_comparison=False).items():
            if not path.endswith('manifest.json'):self.assertEqual(b,(ROOT/path).read_bytes(),path)

if __name__=='__main__':unittest.main(verbosity=2)
