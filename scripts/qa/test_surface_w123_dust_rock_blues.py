#!/usr/bin/env python3
"""Lightweight W128 asset regression; no Gradle, server, DCC or native input."""
import base64
import hashlib
import io
import json
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_dust_rock_blues.py'))
ART=G['ART']

def read(rel):return json.loads((ROOT/rel).read_bytes())
def inside(point,e):
    r=e.get('rotation',{});o=np.array(r.get('origin',[0,0,0]))
    p=(np.array(point)-o)@G['HELPER']['rotation'](r)+o
    return bool(np.all(p>np.array(e['from'])+1e-7) and np.all(p<np.array(e['to'])-1e-7))

class DustRockBlues(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=read(ART+'design.json');cls.m=read(ART+'manifest.json')
        cls.model=read(G['MODEL']);cls.elements=cls.model['elements']
        cls.texture=Image.open(ROOT/G['TEXTURE']).convert('RGBA')

    def test_emitted_budget_and_semantic_solids(self):
        n=len(self.elements)
        self.assertEqual(n,self.m['assembled_elements']);self.assertLessEqual(n,1000)
        self.assertEqual(self.m['counts'],{'full':n})
        self.assertEqual(sum(self.d['groups'].values()),n)
        self.assertEqual(self.m['triangle_adapter_elements'],0)
        self.assertEqual(self.m['alpha_contour_elements'],0)
        self.assertTrue(all(s['kind']=='solid_cuboid' for s in self.d['parts']['full']))
        self.assertTrue(all('vertices' not in e and 'triangles' not in e for e in self.elements))
        for name in ('Long_red_shroud','Ivory_stock','Ivory_grip','Loading_housing','Red_butt_main'):
            e=next(e for e in self.elements if e['name']==name)
            self.assertGreater(float(np.min(np.array(e['to'])-e['from'])),.70)

    def test_canonical_display_and_contact_frame(self):
        self.assertEqual(self.model['display'],read(G['BASE'])['display'])
        frame=self.d['frame'];self.assertEqual(frame['anchor'],[8,8,8])
        self.assertAlmostEqual(frame['scale'],27.595219964806475)
        self.assertEqual(frame['grip_axis_endpoints'],[[8,9.24,10.62],[8,6.43,12.30]])
        a,b=np.array(frame['grip_axis_endpoints'])
        # Endpoints lie on the end faces; probe the actual hand contact interior.
        for t in (.1,.5,.9):
            p=a*(1-t)+b*t
            self.assertTrue(any(inside(p,e) for e in self.elements),p)
        bounds=np.array(self.m['actual_bounds'])
        self.assertLess(bounds[0,2],-5.4);self.assertGreater(bounds[1,2],19)
        self.assertTrue(np.all(abs(bounds-np.array(self.d['source']['model_bounds']))<.6))

    def test_reference_inputs_unchanged(self):
        for rel,h in self.d['input_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),h,rel)
        for path,h in self.d['raw_input_sha256'].items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(),h,path)
        refs=read('art/weapons/w31/references.json')
        photo=next(r for r in refs if r['id']=='dust_rock_blues')
        self.assertEqual(hashlib.sha256(G['PHOTO'].read_bytes()).hexdigest(),photo['sha256'])
        self.assertNotIn('dust_rock_blues',read('art/weapons/w31/palette-overrides.json'))

    def test_real_air_probes(self):
        for name,p in self.d['required_air_probes'].items():
            blockers=[e['name'] for e in self.elements if inside(p,e)]
            self.assertEqual(blockers,[],f'{name}: {blockers}')

    def test_bore_open_depth_and_solid_backstop(self):
        # A central ray travels almost a model unit past the lip without hitting
        # the red shroud; test radial offsets too, not just one lucky point.
        for dx,dy in ((0,0),(.17,0),(-.17,0),(0,.17),(0,-.17)):
            for z in np.linspace(-5.58,-4.56,25):
                self.assertFalse(any(inside([8+dx,10.96+dy,z],e) for e in self.elements),(dx,dy,z))
        self.assertTrue(any(inside([8,10.96,-4.48],e) for e in self.elements))
        self.assertTrue(any(inside([8.47,10.96,-5.48],e) for e in self.elements))
        # Lamp's front central ray must reach the lens, not an opaque bezel.
        self.assertFalse(any(inside([8,9.72,-5.335],e) for e in self.elements))
        self.assertTrue(inside([8,9.72,-5.30],next(e for e in self.elements if e['name']=='Lamp_lens')))

    def test_every_face_is_opaque_and_islands_do_not_overlap(self):
        self.assertEqual(self.texture.size,(1024,1024));pixels=np.asarray(self.texture)
        coverage=np.zeros((1024,1024),bool);ledger=self.d['uv']['islands']
        self.assertEqual(len(ledger),len(self.elements)*6)
        lookup={e['name']:e for e in self.elements}
        for r in ledger:
            x0,y0,x1,y1=r['pixels'];self.assertGreater(x1,x0);self.assertGreater(y1,y0)
            self.assertFalse(coverage[y0-2:y1+2,x0-2:x1+2].any(),r)
            coverage[y0-2:y1+2,x0-2:x1+2]=True
            self.assertTrue((pixels[y0-2:y1+2,x0-2:x1+2,3]==255).all(),r)
            f=lookup[r['element']]['faces'][r['face']]
            self.assertEqual(f['texture'],'#0')
            self.assertTrue(np.array_equal(np.array(f['uv'])*64,r['pixels']))

    def test_inspection_roundtrip_and_texture(self):
        bb=read(ART+'inspection.bbmodel');self.assertEqual(len(bb['elements']),len(self.elements))
        native={e['name']:e for e in self.elements}
        for b in bb['elements']:
            e=native[b['name']];self.assertEqual(b['type'],'cube');self.assertFalse(b['box_uv'])
            self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
            self.assertEqual(b['origin'],e['rotation']['origin'])
            self.assertEqual(b['rotation'],[e['rotation'][a] for a in 'xyz'])
            for face,f in b['faces'].items():self.assertEqual(f['uv'],[v*64 for v in e['faces'][face]['uv']])
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
        self.assertEqual(bb['display'],self.model['display'])
        self.assertTrue(all(g['origin']==[8,8,8] and g['rotation']==[0,0,0] for g in bb['outliner']))

    def test_full_only_ownership_and_no_invented_split(self):
        feature=next(f for f in read('docs/qa/2026-10-26/w128/batch.json')['features'] if f['name']=='w128-dust_rock_blues')
        self.assertEqual(len(feature['owned_paths']),10)
        model_paths=[p for p in feature['owned_paths'] if '/models/' in p]
        self.assertEqual(model_paths,[G['MODEL']]);self.assertEqual(set(self.d['parts']),{'full'})
        self.assertTrue(self.m['full_only']);self.assertFalse(self.m['native_accepted'])

    def test_output_hashes_and_comparison(self):
        for rel,h in self.m['output_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),h,rel)
        self.assertEqual(self.m['generator_sha256'],hashlib.sha256((ROOT/G['GENERATOR']).read_bytes()).hexdigest())
        im=Image.open(ROOT/ART/'comparison.png');self.assertEqual(im.size,(1900,1555))
        self.assertGreater(float(np.asarray(im)[310:].std()),20)

    def test_raw_fbx_axis_translation_and_triangles(self):
        meshes,meta=G['source_meshes']();points=np.concatenate([m['vertices'] for m in meshes])
        self.assertEqual(sum(len(m['faces']) for m in meshes),19031)
        np.testing.assert_allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=1e-5)

if __name__=='__main__':unittest.main(verbosity=2)
