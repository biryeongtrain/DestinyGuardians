#!/usr/bin/env python3
"""Focused offline product regressions; no game, DCC, Gradle or source scripts."""
import base64
import copy
import io
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_aishas_embrace.py'))

def read(path):return json.loads((ROOT/path).read_bytes())

def ray_hit(e,point,direction):
    """First positive intersection with an oriented solid, in native units."""
    o=np.array(point,float);v=np.array(direction,float)
    if 'rotation' in e:
        r=e['rotation'];rot=G['H']['rotation'](r);c=np.array(r['origin'])
        o=(o-c)@rot+c;v=v@rot
    low,high=-np.inf,np.inf
    for a in range(3):
        lo,hi=e['from'][a],e['to'][a]
        if abs(v[a])<1e-12:
            if o[a]<lo or o[a]>hi:return None
        else:
            t=sorted(((lo-o[a])/v[a],(hi-o[a])/v[a]));low=max(low,t[0]);high=min(high,t[1])
    if high<max(low,0):return None
    return max(low,0)

class AishasEmbraceProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=read(G['ART']+'design.json');cls.m=read(G['ART']+'manifest.json')
        cls.model=read(G['MODEL']);cls.bb=read(G['ART']+'inspection.bbmodel')
        cls.atlas=np.array(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))

    def test_emitted_full_budget_and_filled_native_elements(self):
        es=self.model['elements'];self.assertEqual(len(es),self.m['assembled_elements'])
        self.assertTrue(0<len(es)<=1000);self.assertEqual(self.m['counts'],{'full':len(es)})
        self.assertEqual(len(es)*6,self.m['emitted_faces'])
        self.assertEqual(len({e['name'] for e in es}),len(es))
        for e in es:
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertEqual(set(e['faces']),set(G['FACES']))
            self.assertFalse({'vertices','triangles','rescale'}&set(e))

    def test_opaque_face_uvs_and_gutters(self):
        self.assertEqual(self.atlas.shape,(1024,1024,4))
        for island in self.d['atlas']['islands']:
            x0,y0,x1,y1=island['pixels'];self.assertGreater(x1,x0);self.assertGreater(y1,y0)
            self.assertTrue(np.all(self.atlas[y0-2:y1+2,x0-2:x1+2,3]==255))
        for e in self.model['elements']:
            for f in e['faces'].values():
                self.assertEqual(f['texture'],'#0');self.assertTrue(all(0<=v<=16 for v in f['uv']))

    def test_canonical_frame_display_and_full_only(self):
        base=read(G['BASE']);meta=read(G['BB'])['destiny_w30']
        self.assertEqual(self.model['display'],base['display'])
        self.assertEqual(self.d['coordinate_policy']['anchor'],meta['anchor'])
        self.assertEqual(self.d['coordinate_policy']['scale'],meta['scale'])
        self.assertEqual(self.m['source_bounds'],meta['model_bounds']);self.assertTrue(self.m['full_only'])
        self.assertEqual(self.d['coordinate_policy']['muzzle'],'-Z')
        self.assertFalse(self.m['native_accepted'])

    def test_real_transverse_air_spaces(self):
        for name in ('trigger_space','stock_air','optic_saddle'):
            p=self.d['openings'][name]['probe']
            for sign in (-1,1):
                hits=[e['name'] for e in self.model['elements'] if ray_hit(e,p,[sign,0,0]) is not None]
                self.assertEqual(hits,[],(name,hits))

    def test_muzzle_and_optic_have_recess_depth(self):
        for name,sign,expected in [('muzzle',1,'bore_backstop'),('optic_front',1,'front_recessed_lens'),('optic_rear',-1,'rear_recessed_lens')]:
            p=self.d['openings'][name]['probe'];hits=[]
            for e in self.model['elements']:
                distance=ray_hit(e,p,[0,0,sign])
                if distance is not None:hits.append((distance,e['name']))
            distance,first=min(hits);self.assertEqual(first,expected);self.assertGreater(distance,0)

    def test_editable_inspection_matches_native(self):
        self.assertEqual(self.bb['display'],self.model['display'])
        self.assertEqual(len(self.bb['elements']),len(self.model['elements']))
        embedded=base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1])
        self.assertEqual(embedded,(ROOT/G['TEXTURE']).read_bytes())
        for b,e in zip(self.bb['elements'],self.model['elements']):
            self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
            r=e.get('rotation',{});self.assertEqual(b['rotation'],[r.get(a,0) for a in 'xyz'])
            for face in G['FACES']:
                np.testing.assert_allclose(np.array(b['faces'][face]['uv'])/64,e['faces'][face]['uv'])
        grouped=[c for g in self.bb['outliner'] for c in g['children']]
        self.assertEqual(set(grouped),{e['uuid'] for e in self.bb['elements']})
        self.assertEqual(len(grouped),len(self.bb['elements']))

    def test_immutable_inputs_and_output_provenance(self):
        for p,digest in self.m['input_sha256'].items():
            self.assertEqual(G['sha']((ROOT/p).read_bytes()),digest,p)
            self.assertNotIn('manifest.json',p)
        for p,digest in self.m['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(p).read_bytes()),digest,p)
        for p,digest in self.m['output_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),digest,p)
        self.assertEqual(self.m['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_aishas_embrace.py').read_bytes()))

    def test_actual_accepted_fbx_and_frame(self):
        meshes,meta=G['source_meshes']()
        self.assertEqual(len(meshes),8);self.assertEqual(sum(len(m['faces']) for m in meshes),26485)
        self.assertEqual(self.m['source_triangles'],meta['source_triangles'])

    def test_review_evidence_and_exact_owned_outputs(self):
        batch=read('docs/qa/2026-10-26/w142/batch.json')
        scope=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w142-aishas_embrace'))
        self.assertEqual(len(scope),10);self.assertTrue(set(self.m['output_sha256'])<=scope)
        with Image.open(ROOT/(G['ART']+'comparison.png')) as im:self.assertEqual(im.size,(3000,1940));im.verify()
        self.assertTrue((ROOT/(G['ART']+'review.md')).is_file())

if __name__=='__main__':unittest.main(verbosity=2)
