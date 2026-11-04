#!/usr/bin/env python3
"""Targeted W129 Halfdan-D export/paint/frame/real-aperture regressions; CPU only."""
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
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_halfdan_d.py'))
CANONICAL_SHA='a6c1fa0e4084403c66e8136179f320ace92bd4b7962f0bc59ae648df0830f378'

class HalfdanArtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design=json.loads((ROOT/G['ART']/'design.json').read_bytes())
        cls.model=json.loads((ROOT/G['MODEL']).read_bytes())
        cls.manifest=json.loads((ROOT/G['ART']/'manifest.json').read_bytes())
        cls.atlas=np.array(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))
        cls.bb=json.loads((ROOT/G['ART']/'inspection.bbmodel').read_bytes())
        cls.canonical=json.loads((ROOT/G['BASE']).read_bytes())

    def occupied(self,p):
        p=np.asarray(p)
        for e in self.model['elements']:
            r=e['rotation'];origin=np.array(r['origin']);R=G['helper']()['rotation'](r)
            q=(p-origin)@R+origin
            if np.all(q>np.array(e['from'])+1e-6) and np.all(q<np.array(e['to'])-1e-6):return True
        return False

    def test_01_readonly_canonical_and_pinned_inputs(self):
        self.assertEqual(hashlib.sha256((ROOT/G['BASE']).read_bytes()).hexdigest(),CANONICAL_SHA)
        for p,digest in self.design['input_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),digest,p)
        for p,digest in self.design['raw_input_sha256'].items():
            self.assertEqual(hashlib.sha256(Path(p).read_bytes()).hexdigest(),digest,p)

    def test_02_original_frame_display_and_grip(self):
        self.assertEqual(self.model['display'],self.canonical['display'])
        self.assertEqual(self.design['anchor'],[8,8,8])
        self.assertEqual(self.design['scale'],29.139159344078795)
        meshes,meta=G['source_meshes']()
        self.assertEqual(sum(len(m['faces']) for m in meshes),11642)
        pts=np.concatenate([G['vertices'](e) for e in self.model['elements']])
        self.assertTrue(np.all(np.abs(np.array([pts.min(0),pts.max(0)])-np.array(meta['model_bounds']))<.22))
        # Original hand contact volume, without global or per-part recentering.
        for p in ([8,9.2,8.38],[8,8.3,8.62],[8,7.5,8.85]):self.assertTrue(self.occupied(p),p)

    def test_03_native_cuboids_budget_and_complete_faces(self):
        elements=self.model['elements'];n=len(elements)
        self.assertEqual(n,self.manifest['assembled_elements'])
        self.assertLessEqual(n,1000)
        self.assertEqual(self.manifest['emitted_faces'],6*n)
        self.assertEqual(self.manifest['alpha_contour_elements'],0)
        self.assertEqual(self.manifest['triangle_adapter_elements'],0)
        self.assertEqual(len({e['name'] for e in elements}),n)
        for e in elements:
            self.assertEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>np.array(e['from'])))
            self.assertEqual(set(e['faces']),set(G['FACES']))
            self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
            self.assertTrue(np.isfinite(G['vertices'](e)).all())

    def test_04_opaque_unique_face_islands_with_dilation(self):
        used=np.zeros((G['EDGE'],G['EDGE']),bool);islands=self.design['atlas']['islands']
        self.assertEqual(len(islands),6*len(self.model['elements']))
        byname={e['name']:e for e in self.model['elements']}
        for r in islands:
            x0,y0,x1,y1=r['pixels']
            self.assertTrue(2<=x0<x1<=1022 and 2<=y0<y1<=1022)
            self.assertFalse(used[y0-2:y1+2,x0-2:x1+2].any(),r)
            used[y0-2:y1+2,x0-2:x1+2]=True
            self.assertTrue((self.atlas[y0-2:y1+2,x0-2:x1+2,3]==255).all(),r)
            face=byname[r['element']]['faces'][r['face']]
            self.assertEqual(face['texture'],'#0')
            self.assertEqual(face['uv'],[q*16/1024 for q in r['pixels']])

    def test_05_real_air_and_deep_bore(self):
        for name,p in self.design['required_air_probes'].items():self.assertFalse(self.occupied(p),name)
        for z in np.linspace(-9.42,-8.20,30):self.assertFalse(self.occupied([8,10.66,z]),z)
        self.assertTrue(self.occupied([8,10.66,-8.12]),'bore must have recessed backstop')
        # These windows must pass through both sides, not be alpha-painted holes.
        for x in np.linspace(6.8,9.3,20):
            for y,z in ((9.65,5.90),(11.10,12.90)):
                self.assertFalse(self.occupied([x,y,z]),(x,y,z))
        # Sight aperture passes ALONG Z between its solid side ears.
        for x in (7.85,8,8.15):
            for z in np.linspace(6.9,8.2,15):self.assertFalse(self.occupied([x,13.65,z]),(x,z))

    def test_06_broad_receiver_and_magazine_are_solid(self):
        for x in (7.4,8,8.6):
            for y in (11.7,12.3):
                for z in (3.6,5.4,8.2):self.assertTrue(self.occupied([x,y,z]))
        for x in (7.7,8,8.3):
            for z in (2.1,3.1,4.1):self.assertTrue(self.occupied([x,8,z]))

    def test_07_inspection_geometry_uv_texture_and_display_match(self):
        self.assertEqual(self.bb['display'],self.model['display'])
        self.assertEqual(len(self.bb['elements']),len(self.model['elements']))
        self.assertEqual(base64.b64decode(self.bb['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
        for b,e in zip(self.bb['elements'],self.model['elements']):
            self.assertEqual(b['type'],'cube')
            self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
            self.assertEqual(b['origin'],e['rotation']['origin'])
            self.assertEqual(b['rotation'],[e['rotation'][a] for a in 'xyz'])
            for f in G['FACES']:
                self.assertEqual(b['faces'][f]['uv'],[q*64 for q in e['faces'][f]['uv']])
        for group in self.bb['outliner']:self.assertEqual(group['origin'],[8,8,8])

    def test_08_manifest_hashes_references_and_full_only(self):
        for p,digest in self.manifest['output_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),digest,p)
        ref=next(r for r in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if r['id']=='halfdan_d')
        self.assertEqual(self.design['raw_input_sha256'][str(G['PHOTO'])],ref['sha256'])
        self.assertTrue(self.manifest['full_only']);self.assertFalse(self.manifest['native_accepted'])
        self.assertEqual(self.model['textures']['0'],'destiny:item/weapon/w123/halfdan_d')
        batch=json.loads((ROOT/'docs/qa/2026-10-26/w129/batch.json').read_bytes())
        scope=next(f['owned_paths'] for f in batch['features'] if f['name']=='w129-halfdan_d')
        self.assertEqual(len(scope),10)
        self.assertEqual([p for p in scope if '/models/' in p],[G['MODEL']])
        self.assertTrue(all((ROOT/p).is_file() for p in scope))

    def test_09_deterministic_regeneration(self):
        for p,data in G['generate']().items():
            self.assertEqual((ROOT/p).read_bytes(),data,p)

if __name__=='__main__':unittest.main(verbosity=2)
