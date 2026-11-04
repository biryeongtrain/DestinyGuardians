#!/usr/bin/env python3
"""Targeted offline regression for the W129 Antiope-D art-only full model."""
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_antiope_d.py'))
ART=G['ART'];MODEL=G['MODEL'];TEXTURE=G['TEXTURE']


def load(p):return json.loads((ROOT/p).read_bytes())


def inside(point,e):
    p=np.array(point,float)
    if 'rotation' in e:
        r=e['rotation'];o=np.array(r['origin']);R=G['H']['rotation']({r['axis']:r['angle']})
        p=(p-o)@R+o
    return bool(np.all(p>=np.array(e['from'])-1e-7) and np.all(p<=np.array(e['to'])+1e-7))


class AntiopeArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(ART+'design.json');cls.m=load(MODEL);cls.man=load(ART+'manifest.json');cls.bb=load(ART+'inspection.bbmodel')
        cls.atlas=Image.open(ROOT/TEXTURE).convert('RGBA');cls.pixels=np.asarray(cls.atlas)
        cls.names={e['name']:e for e in cls.m['elements']}

    def test_01_owned_exact_ten_and_full_only(self):
        batch=load('docs/qa/2026-10-26/w129/batch.json');owned=next(f['owned_paths'] for f in batch['features'] if f['name']=='w129-antiope_d')
        self.assertEqual(10,len(owned));self.assertTrue(all((ROOT/p).is_file() for p in owned))
        self.assertEqual([MODEL],[p for p in owned if '/models/' in p])
        self.assertFalse((ROOT/MODEL.replace('.json','_body.json')).exists())
        self.assertFalse((ROOT/MODEL.replace('.json','_magazine.json')).exists())

    def test_02_schema_and_emitted_count(self):
        es=self.m['elements'];self.assertEqual(118,len(es));self.assertLessEqual(len(es),1000)
        self.assertEqual(len(es),self.man['assembled_elements']);self.assertEqual(len(es)*6,self.man['emitted_faces'])
        self.assertEqual(len(es),sum(self.man['groups'].values()));self.assertEqual(0,self.man['alpha_body_elements'])
        self.assertEqual(len(es),len(self.names));self.assertNotIn('parent',self.m)
        for e in es:
            self.assertTrue(set(e)<={'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.all(np.isfinite(G['vertices'](e))))
            self.assertEqual(set(G['FACES']),set(e['faces']))
            if 'rotation' in e:
                self.assertEqual({'origin','axis','angle'},set(e['rotation']))
                self.assertIn(e['rotation']['axis'],'xyz');self.assertTrue(-45<=e['rotation']['angle']<=45)

    def test_03_broad_semantic_solids(self):
        for name in ('upper_receiver','lower_receiver','grip_core','foregrip_body','stock_comb','magazine_core'):
            size=np.array(self.names[name]['to'])-self.names[name]['from']
            self.assertGreater(size[0],.7);self.assertGreater(size[1],1);self.assertGreater(size[2],1)
        self.assertGreater(self.names['upper_receiver']['to'][2]-self.names['upper_receiver']['from'][2],10)
        self.assertNotIn('source_volume',str(self.m))

    def test_04_face_uv_and_opaque_gutters(self):
        self.assertEqual((1024,1024),self.atlas.size)
        ledger=self.d['atlas']['islands'];self.assertEqual(len(self.m['elements'])*6,len(ledger))
        coverage=np.zeros((1024,1024),np.uint8)
        for v in ledger:
            x0,y0,x1,y1=v['pixels'];self.assertGreater(x1,x0);self.assertGreater(y1,y0)
            self.assertGreaterEqual(min(x0,y0),2);self.assertLessEqual(max(x1,y1),1022)
            rect=self.pixels[y0-2:y1+2,x0-2:x1+2]
            self.assertTrue(np.all(rect[:,:,3]==255))
            uv=self.names[v['element']]['faces'][v['face']]['uv']
            self.assertTrue(np.allclose(uv,np.array([x0,y0,x1,y1])*16/1024))
            self.assertTrue(np.all(coverage[y0-2:y1+2,x0-2:x1+2]==0))
            coverage[y0-2:y1+2,x0-2:x1+2]=1
            self.assertEqual('#0',self.names[v['element']]['faces'][v['face']]['texture'])

    def test_05_canonical_frame_display_and_provenance(self):
        base=load(G['BASE']);source=load('art/blockbench/weapons/w30/antiope_d.bbmodel')['destiny_w30']
        self.assertEqual(base['display'],self.m['display']);self.assertEqual(source['scale'],self.man['source_scale'])
        self.assertEqual([8,8,8],self.man['source_anchor']);self.assertEqual(source['anchor'],self.d['coordinate_policy']['anchor'])
        self.assertEqual(source['model_bounds'],self.man['source_bounds']);self.assertEqual(17248,self.man['source_triangles'])
        self.assertAlmostEqual(-2.785893526985056,self.man['actual_bounds'][0][2],delta=1e-6);self.assertAlmostEqual(17.214106473014944,self.man['actual_bounds'][1][2])
        self.assertAlmostEqual(3.3626039679040387,self.man['actual_bounds'][0][1]);self.assertLess(abs(self.man['actual_bounds'][1][1]-15.761438883603107),.05)
        # Pistol grip uses the source native frame, no display compensation.
        grip=self.names['grip_core'];self.assertEqual([8,9.32,9.49],grip['rotation']['origin'])
        for path,digest in self.d['input_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/path).read_bytes()),path)
        for path,digest in self.d['raw_input_sha256'].items():self.assertEqual(digest,G['sha'](Path(path).read_bytes()),path)
        refs=load('art/weapons/w31/references.json');photo=next(r for r in refs if r['id']=='antiope_d')
        self.assertEqual(photo['sha256'],G['sha'](G['PHOTO'].read_bytes()))
        self.assertNotIn('antiope_d',load('art/weapons/w31/palette-overrides.json'))

    def assert_air(self,points):
        for p in points:
            hits=[e['name'] for e in self.m['elements'] if inside(p,e)]
            self.assertEqual([],hits,str(p))

    def test_06_real_muzzle_depth(self):
        self.assert_air([[8,12.33,float(z)] for z in np.linspace(-2.75,.60,35)])
        self.assertTrue(inside([8,12.33,.67],self.names['bore_depth_stop']))
        self.assertTrue(any(inside([8,12.77,-2],e) for e in self.m['elements']))

    def test_07_peep_and_front_sight_gap(self):
        self.assert_air([[8,15.22,float(z)] for z in np.linspace(7.20,7.80,11)])
        self.assert_air([[8.28,14.37,float(z)] for z in np.linspace(.72,1.2,8)])
        self.assertTrue(any(inside([8,15.69,7.5],e) for e in self.m['elements']))

    def test_08_guard_and_stock_through_gaps(self):
        self.assert_air([[float(x),10.25,6.9] for x in np.linspace(6.6,9.4,21)])
        self.assert_air([[float(x),11.15,15.65] for x in np.linspace(6.6,9.4,21)])
        self.assertTrue(inside([8,9.6,7.0],self.names['guard_floor']))

    def test_09_side_lens_recess(self):
        self.assert_air([[9.18,13.18,float(z)] for z in np.linspace(1.98,2.30,15)])
        self.assertTrue(inside([9.18,13.18,2.325],self.names['side_objective_lens']))
        self.assertGreater(self.names['side_objective_lens']['from'][2]-1.98,.3)

    def test_10_inspection_geometry_atlas_parity(self):
        self.assertEqual(118,len(self.bb['elements']));self.assertEqual(self.m['display'],self.bb['display'])
        embedded=base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1])
        self.assertEqual((ROOT/TEXTURE).read_bytes(),embedded)
        self.assertEqual(set(self.names),{e['name'] for e in self.bb['elements']})
        for b in self.bb['elements']:
            e=self.names[b['name']];self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            for f in G['FACES']:self.assertTrue(np.allclose(np.array(e['faces'][f]['uv'])*64,b['faces'][f]['uv']))
            r=e.get('rotation');self.assertEqual([r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],b['rotation'])
        children=[v for g in self.bb['outliner'] for v in g['children']]
        self.assertEqual(len(children),len(set(children)));self.assertEqual(118,len(children))

    def test_11_manifest_hashes_and_pending_native(self):
        self.assertFalse(self.man['native_accepted']);self.assertTrue(self.man['full_only'])
        self.assertTrue(self.man['generic_reload_ADS_unchanged'])
        self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_antiope_d.py').read_bytes()))
        for p,digest in self.man['output_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        with Image.open(ROOT/(ART+'comparison.png')) as im:self.assertEqual((2700,2070),im.size)

    def test_12_deterministic_regeneration_without_render(self):
        generated=G['generate'](include_comparison=False)
        # Full render is separately regenerated and compared with --verify.
        # This inexpensive test covers every non-manifest generated asset.
        for path,data in generated.items():
            if path!=ART+'manifest.json':self.assertEqual(data,(ROOT/path).read_bytes(),path)

if __name__=='__main__':unittest.main(verbosity=2)
