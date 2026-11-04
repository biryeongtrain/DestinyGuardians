#!/usr/bin/env python3
"""Light offline regression for W136 Edge Transit; no native art gate."""
import base64
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_edge_transit.py'))
ART=G['ART'];MODEL=G['MODEL'];TEXTURE=G['TEXTURE']


def load(p):return json.loads((ROOT/p).read_bytes())


def inside(point,e):
    p=np.array(point,float)
    if 'rotation' in e:
        r=e['rotation'];o=np.array(r['origin']);R=G['H']['rotation']({r['axis']:r['angle']})
        p=(p-o)@R+o
    return bool(np.all(p>=np.array(e['from'])-1e-7) and np.all(p<=np.array(e['to'])+1e-7))


class EdgeTransitArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(ART+'design.json');cls.m=load(MODEL);cls.man=load(ART+'manifest.json');cls.bb=load(ART+'inspection.bbmodel')
        cls.atlas=Image.open(ROOT/TEXTURE).convert('RGBA');cls.pixels=np.asarray(cls.atlas)
        cls.names={e['name']:e for e in cls.m['elements']}

    def test_01_exclusive_full_only_scope(self):
        self.assertEqual(10,len(set(G['OWNED'])))
        owned=next(f['owned_paths'] for f in load('docs/qa/2026-10-26/w136/batch.json')['features'] if f['name']=='w136-edge_transit')
        self.assertEqual(set(owned),set(G['OWNED']))
        self.assertEqual([MODEL],[p for p in G['OWNED'] if '/models/' in p])
        self.assertTrue(all((ROOT/p).is_file() for p in G['OWNED'] if p!=G['REPORT']))
        self.assertFalse((ROOT/MODEL.replace('.json','_body.json')).exists())
        self.assertFalse((ROOT/MODEL.replace('.json','_magazine.json')).exists())

    def test_02_schema_and_combined_count(self):
        es=self.m['elements'];self.assertLessEqual(len(es),1000);self.assertGreater(len(es),75)
        self.assertEqual(len(es),self.man['assembled_elements']);self.assertEqual(len(es)*6,self.man['emitted_faces'])
        self.assertEqual(len(es),sum(self.man['groups'].values()));self.assertEqual(0,self.man['alpha_body_elements'])
        self.assertEqual(0,self.man['triangle_adapter_elements']);self.assertEqual(len(es),len(self.names))
        for e in es:
            self.assertTrue(set(e)<={'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.all(np.isfinite(G['vertices'](e))))
            self.assertEqual(set(G['FACES']),set(e['faces']))
            if 'rotation' in e:
                self.assertEqual({'origin','axis','angle'},set(e['rotation']));self.assertIn(e['rotation']['axis'],'xyz')

    def test_03_filled_semantic_depth(self):
        for name in ('receiver_core','stock_slab','lower_frame_rail','pistol_grip','front_grip_upper'):
            size=np.array(self.names[name]['to'])-self.names[name]['from']
            self.assertGreaterEqual(size[0],1.0);self.assertGreater(size[1],.8);self.assertGreater(size[2],.8)
        self.assertTrue(inside([8,11.5,10],self.names['receiver_core']))
        self.assertTrue(inside([8,10,15],self.names['stock_slab']))
        self.assertTrue(inside([8,5.8,3],self.names['lower_frame_rail']))
        # Grid samples through the drum's cross section catch a hollow side shell.
        for x in np.linspace(6.7,10.3,7):
            for y in np.linspace(8.4,12,7):
                if np.hypot(x-8.53,y-10.22)<2.25:
                    self.assertTrue(any(inside([x,y,2.4],e) for e in self.m['elements']))

    def test_04_face_uv_alpha_and_gutters(self):
        self.assertEqual((1024,1024),self.atlas.size)
        ledger=self.d['atlas']['islands'];self.assertEqual(len(self.m['elements'])*6,len(ledger))
        coverage=np.zeros((1024,1024),np.uint8)
        for v in ledger:
            x0,y0,x1,y1=v['pixels'];self.assertGreater(x1,x0);self.assertGreater(y1,y0)
            self.assertGreaterEqual(min(x0,y0),2);self.assertLessEqual(max(x1,y1),1022)
            rect=self.pixels[y0-2:y1+2,x0-2:x1+2]
            self.assertTrue(np.all(rect[:,:,3]==255))
            self.assertTrue(np.all(rect[:2,2:-2]==rect[2:3,2:-2]));self.assertTrue(np.all(rect[2:-2,:2]==rect[2:-2,2:3]))
            uv=self.names[v['element']]['faces'][v['face']]['uv']
            self.assertTrue(np.allclose(uv,np.array([x0,y0,x1,y1])*16/1024))
            self.assertTrue(np.all(coverage[y0-2:y1+2,x0-2:x1+2]==0));coverage[y0-2:y1+2,x0-2:x1+2]=1
            self.assertEqual('#0',self.names[v['element']]['faces'][v['face']]['texture'])
        self.assertGreater(len(np.unique(self.pixels[coverage>0,:3],axis=0)),100)

    def test_05_source_frame_display_and_default_photo_hash(self):
        source=load('art/blockbench/weapons/w30/edge_transit.bbmodel')['destiny_w30']
        self.assertEqual(load(G['BASE'])['display'],self.m['display'])
        self.assertEqual(source['scale'],self.man['source_scale']);self.assertEqual(source['anchor'],self.man['source_anchor'])
        self.assertEqual(source['model_bounds'],self.man['source_bounds']);self.assertEqual(30450,self.man['source_triangles'])
        self.assertEqual(source,self.d['source'])
        self.assertAlmostEqual(source['model_bounds'][0][2],self.man['actual_bounds'][0][2],delta=1e-6)
        self.assertAlmostEqual(source['model_bounds'][1][2],self.man['actual_bounds'][1][2],delta=1e-6)
        self.assertAlmostEqual(source['model_bounds'][0][1],self.man['actual_bounds'][0][1],delta=1e-6)
        self.assertEqual([8,8.30,8.79],self.names['pistol_grip']['rotation']['origin'])
        self.assertEqual([8,9.82,7.98],self.d['coordinate_policy']['grip_top'])
        self.assertEqual([8,6.78,9.60],self.d['coordinate_policy']['grip_heel'])
        self.assertAlmostEqual(source['model_bounds'][1][1],self.names['sight_ear_-1']['to'][1])
        self.assertEqual('heavy_grenade_launcher',self.d['catalogue']['family'])
        for p,digest in self.d['input_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        for p,digest in self.d['raw_input_sha256'].items():self.assertEqual(digest,G['sha'](Path(p).read_bytes()),p)
        ref=next(r for r in load('art/weapons/w31/references.json') if r['id']=='edge_transit')
        self.assertEqual(ref['sha256'],G['sha'](G['PHOTO'].read_bytes()));self.assertEqual(ref,self.d['reference'])
        self.assertEqual(self.man['default_photo_sha256'],ref['sha256'])
        meshes,meta=G['source_meshes']()
        self.assertEqual(meta,source);self.assertEqual(sorted(source['source_objects']),sorted(m['name'] for m in meshes))
        pts=np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([pts.min(0),pts.max(0)],source['model_bounds'],atol=1e-6,rtol=0)
        self.assertEqual(30450,sum(len(m['faces']) for m in meshes))
        # Explicit basis probes ensure it cannot silently switch to Beloved's basis.
        self.assertIn('native X=raw X, Y=raw Z, Z=raw Y',self.d['coordinate_policy']['basis'])

    def assert_air(self,points):
        for p in points:
            self.assertEqual([],[e['name'] for e in self.m['elements'] if inside(p,e)],str(p))

    def test_06_bore_depth(self):
        self.assert_air([[8,11.58,float(z)] for z in np.linspace(-8.62,.10,37)])
        self.assertTrue(inside([8,11.58,.18],self.names['bore_depth_stop']))
        self.assertTrue(any(inside([8,12.25,-8.2],e) for e in self.m['elements']))
        self.assertTrue(any(inside([8,12.45,-4],e) for e in self.m['elements']))

    def test_07_sight_guard_stock_and_front_frame_air(self):
        self.assert_air([[8,13.10,float(z)] for z in np.linspace(7.75,9.20,9)])
        self.assert_air([[float(x),9.58,6.85] for x in np.linspace(6.6,9.4,15)])
        self.assert_air([[float(x),9.24,11.35] for x in np.linspace(6.6,9.4,15)])
        self.assert_air([[float(x),6.92,3.0] for x in np.linspace(6.6,9.4,15)])
        self.assertTrue(inside([8,9.03,6.8],self.names['guard_bottom']))

    def test_08_editable_inspection_parity(self):
        self.assertEqual(len(self.names),len(self.bb['elements']));self.assertEqual(self.m['display'],self.bb['display'])
        self.assertEqual((ROOT/TEXTURE).read_bytes(),base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]))
        self.assertEqual(set(self.names),{e['name'] for e in self.bb['elements']})
        for b in self.bb['elements']:
            e=self.names[b['name']];self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            self.assertFalse(b['box_uv']);self.assertEqual('cube',b['type'])
            for f in G['FACES']:self.assertTrue(np.allclose(np.array(e['faces'][f]['uv'])*64,b['faces'][f]['uv']))
            r=e.get('rotation');self.assertEqual([r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],b['rotation'])
            if r:self.assertEqual(r['origin'],b['origin'])
        children=[v for g in self.bb['outliner'] for v in g['children']]
        self.assertEqual(len(children),len(set(children)));self.assertEqual(len(self.names),len(children))

    def test_09_manifest_hashes_and_native_pending(self):
        self.assertFalse(self.man['native_accepted']);self.assertTrue(self.man['full_only']);self.assertTrue(self.man['generic_reload_ADS_unchanged'])
        self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_edge_transit.py').read_bytes()))
        for p,digest in self.man['output_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        with Image.open(ROOT/(ART+'comparison.png')) as im:self.assertEqual((2700,2100),im.size)
        self.assertLess(sum((ROOT/p).stat().st_size for p in G['OWNED'] if (ROOT/p).exists()),25*1024*1024)

    def test_10_deterministic_regeneration(self):
        generated=G['generate'](include_comparison=False)
        for p,data in generated.items():
            if p!=ART+'manifest.json':self.assertEqual(data,(ROOT/p).read_bytes(),p)

if __name__=='__main__':unittest.main(verbosity=2)
