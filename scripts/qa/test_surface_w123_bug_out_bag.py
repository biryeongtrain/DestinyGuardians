#!/usr/bin/env python3
"""Portable W138 Bug-Out Bag offline checks; no git/worktree path assumption.
Run this same file from the isolated worker or after hash-checked integration.
"""
import base64
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_bug_out_bag.py'))
ART=G['ART'];MODEL=G['MODEL'];TEXTURE=G['TEXTURE']


def load(p):return json.loads((ROOT/p).read_bytes())


def inside(point,e):
    p=np.array(point,float)
    if 'rotation' in e:
        r=e['rotation'];o=np.array(r['origin']);R=G['H']['rotation']({r['axis']:r['angle']})
        p=(p-o)@R+o
    return bool(np.all(p>=np.array(e['from'])-1e-7) and np.all(p<=np.array(e['to'])+1e-7))


class BugOutBagArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(ART+'design.json');cls.m=load(MODEL);cls.man=load(ART+'manifest.json');cls.bb=load(ART+'inspection.bbmodel')
        cls.atlas=Image.open(ROOT/TEXTURE).convert('RGBA');cls.pixels=np.asarray(cls.atlas)
        cls.names={e['name']:e for e in cls.m['elements']}

    def test_01_exact_ten_full_only_portable(self):
        # Project-relative contract, independent of branch name or .git location.
        batch=load('docs/qa/2026-10-26/w138/batch.json')
        owned=next(f['owned_paths'] for f in batch['features'] if f['name']=='w138-bug_out_bag')
        self.assertEqual(10,len(owned));self.assertTrue(all((ROOT/p).is_file() for p in owned))
        self.assertEqual([MODEL],[p for p in owned if '/models/' in p])
        self.assertFalse((ROOT/MODEL.replace('.json','_body.json')).exists())
        self.assertFalse((ROOT/MODEL.replace('.json','_magazine.json')).exists())
        self.assertEqual(10,len(set(owned)))

    def test_02_native_cuboid_schema_and_budget(self):
        es=self.m['elements'];self.assertEqual(100,len(es));self.assertLessEqual(len(es),1000)
        self.assertEqual(len(es),self.man['assembled_elements']);self.assertEqual(len(es)*6,self.man['emitted_faces'])
        self.assertEqual(len(es),sum(self.man['groups'].values()));self.assertEqual(0,self.man['alpha_body_elements'])
        self.assertEqual(0,self.man['triangle_adapter_elements']);self.assertEqual(len(es),len(self.names))
        self.assertNotIn('parent',self.m)
        for e in es:
            self.assertTrue(set(e)<={'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.all(np.isfinite(G['vertices'](e))))
            self.assertEqual(set(G['FACES']),set(e['faces']))
            if 'rotation' in e:
                self.assertEqual({'origin','axis','angle'},set(e['rotation']))
                self.assertIn(e['rotation']['axis'],'xyz');self.assertTrue(-45<=e['rotation']['angle']<=45)

    def test_03_filled_semantic_volumes(self):
        # Occupancy through center sections catches thin side-shell substitutes.
        for name,point in [('receiver_core',[8,12,7]),('grip_core',[8,9.12,7.42]),
            ('magazine_core',[8,6,7.5]),('cloth_upper_core',[8,12.9,10.8]),
            ('cloth_lower_core',[8,12.1,10.8]),('barrel_core',[8,12.03,0])]:
            e=self.names[name];self.assertTrue(inside(point,e),name)
            self.assertGreater(e['to'][0]-e['from'][0],.6)
            self.assertGreater(e['to'][1]-e['from'][1],.6)
        for x in np.linspace(7.46,8.54,13):self.assertTrue(inside([x,12,7],self.names['receiver_core']))
        self.assertGreater(self.names['receiver_core']['to'][2]-self.names['receiver_core']['from'][2],4)

    def test_04_atlas_unique_face_uv_opaque_extruded_gutters(self):
        self.assertEqual((1024,1024),self.atlas.size)
        ledger=self.d['atlas']['islands'];self.assertEqual(len(self.m['elements'])*6,len(ledger))
        coverage=np.zeros((1024,1024),np.uint8);keys=set()
        for rec in ledger:
            key=(rec['element'],rec['face']);self.assertNotIn(key,keys);keys.add(key)
            x0,y0,x1,y1=rec['pixels'];self.assertGreater(x1,x0);self.assertGreater(y1,y0)
            self.assertGreaterEqual(min(x0,y0),2);self.assertLessEqual(max(x1,y1),1022)
            rect=self.pixels[y0-2:y1+2,x0-2:x1+2]
            self.assertTrue(np.all(rect[:,:,3]==255))
            expected=np.pad(self.pixels[y0:y1,x0:x1],((2,2),(2,2),(0,0)),mode='edge')
            self.assertTrue(np.array_equal(expected,rect))
            uv=self.names[rec['element']]['faces'][rec['face']]['uv']
            self.assertTrue(np.array_equal(uv,np.array([x0,y0,x1,y1])*16/1024))
            self.assertTrue(np.all(coverage[y0-2:y1+2,x0-2:x1+2]==0))
            coverage[y0-2:y1+2,x0-2:x1+2]=1
            self.assertEqual('#0',self.names[rec['element']]['faces'][rec['face']]['texture'])

    def test_05_source_specific_fbx_basis_and_frame(self):
        meshes,meta=G['source_meshes']();points=np.concatenate([m['vertices'] for m in meshes])
        self.assertTrue(np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=4e-5))
        self.assertEqual(27895,sum(len(m['faces']) for m in meshes))
        self.assertEqual(11,len(meta['fbx_basis_evidence']))
        for evidence in meta['fbx_basis_evidence']:
            self.assertTrue(np.allclose(evidence['rotation'],[-90,90,0],atol=.00001))
            self.assertTrue(np.allclose(evidence['scaling'],[135.46978759765625]*3))
            self.assertTrue(np.allclose(evidence['translation'],[4.7623462677,4.5683441162,0]))
        self.assertEqual(meta['scale'],self.man['source_scale']);self.assertEqual([8,8,8],self.man['source_anchor'])
        self.assertEqual(load(G['BASE'])['display'],self.m['display'])
        self.assertEqual([8,9.12,7.42],self.names['grip_core']['rotation']['origin'])
        self.assertAlmostEqual(meta['model_bounds'][0][2],self.man['actual_bounds'][0][2],delta=1e-6)
        self.assertAlmostEqual(meta['model_bounds'][1][2],self.man['actual_bounds'][1][2],delta=1e-6)
        self.assertAlmostEqual(meta['model_bounds'][0][1],self.man['actual_bounds'][0][1],delta=1e-6)
        self.assertAlmostEqual(meta['model_bounds'][1][1],self.man['actual_bounds'][1][1],delta=.01)

    def assert_air(self,points):
        for p in points:self.assertEqual([],[e['name'] for e in self.m['elements'] if inside(p,e)],str(p))

    def test_06_real_bore_with_depth_and_terminal(self):
        self.assert_air([[8,12.03,float(z)] for z in np.linspace(-4,-2.15,29)])
        self.assertTrue(inside([8,12.03,-2.10],self.names['bore_stop']))
        self.assertTrue(any(inside([8,12.41,-3],e) for e in self.m['elements']))

    def test_07_foregrip_guard_and_stock_through_air(self):
        for y,z in ((9.91,3.6),(10.60,5.65),(11.38,14.9)):
            self.assert_air([[float(x),y,z] for x in np.linspace(6.5,9.5,23)])
        self.assertTrue(inside([8,8.68,3.84],self.names['foregrip_heel']))
        self.assertTrue(inside([8,10.16,5.7],self.names['foregrip_guard_bridge']))

    def test_08_protective_cage_parallax_and_recessed_optic(self):
        # Air outside the thick bronze wall but inside the protective rail width.
        self.assert_air([[8.76,12.25,float(z)] for z in np.linspace(1.3,4.3,13)])
        self.assertTrue(inside([8.88,13.09,3],self.names['protective_rail_upper_1']))
        self.assert_air([[8,13.85,float(z)] for z in np.linspace(2.85,3.30,11)])
        self.assertTrue(inside([8,13.85,3.335],self.names['optic_lens']))
        self.assertGreater(self.names['optic_lens']['from'][2]-2.84,.45)

    def test_09_input_hashes_and_identity_materials(self):
        for p,digest in self.d['input_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        for p,digest in self.d['raw_input_sha256'].items():self.assertEqual(digest,G['sha'](Path(p).read_bytes()),p)
        self.assertEqual(self.d['input_sha256'],self.man['input_sha256'])
        self.assertEqual(self.d['raw_input_sha256'],self.man['raw_input_sha256'])
        self.assertGreater(self.d['palette']['bronze'][0],self.d['palette']['bronze'][2])
        # A cloth island actually has source pattern contrast, not flat gray.
        rec=next(r for r in self.d['atlas']['islands'] if r['element']=='cloth_upper_core' and r['face']=='east')
        x0,y0,x1,y1=rec['pixels'];tile=self.pixels[y0:y1,x0:x1,:3]
        self.assertGreater(np.percentile(tile,90)-np.percentile(tile,10),75)

    def test_10_inspection_geometry_atlas_parity(self):
        self.assertEqual(len(self.m['elements']),len(self.bb['elements']));self.assertEqual(self.m['display'],self.bb['display'])
        embedded=base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1])
        self.assertEqual((ROOT/TEXTURE).read_bytes(),embedded)
        self.assertEqual(set(self.names),{e['name'] for e in self.bb['elements']})
        for b in self.bb['elements']:
            e=self.names[b['name']];self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            for f in G['FACES']:self.assertTrue(np.array_equal(np.array(e['faces'][f]['uv'])*64,b['faces'][f]['uv']))
            r=e.get('rotation');self.assertEqual([r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],b['rotation'])
        children=[v for g in self.bb['outliner'] for v in g['children']]
        self.assertEqual(len(children),len(set(children)));self.assertEqual(len(self.names),len(children))

    def test_11_manifest_and_native_pending(self):
        self.assertFalse(self.man['native_accepted']);self.assertTrue(self.man['full_only'])
        self.assertTrue(self.man['generic_reload_ADS_unchanged'])
        self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_bug_out_bag.py').read_bytes()))
        for p,digest in self.man['output_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        with Image.open(ROOT/(ART+'comparison.png')) as im:self.assertEqual((2700,2070),im.size)
        batch=load('docs/qa/2026-10-26/w138/batch.json')
        owned=next(f['owned_paths'] for f in batch['features'] if f['name']=='w138-bug_out_bag')
        self.assertLess(sum((ROOT/p).stat().st_size for p in owned),25*1024*1024)

    def test_12_deterministic_regeneration_without_render(self):
        generated=G['generate'](include_comparison=False)
        # Complete raster regeneration is separately enforced by --verify.
        for p,data in generated.items():
            if p!=ART+'manifest.json':self.assertEqual(data,(ROOT/p).read_bytes(),p)

if __name__=='__main__':unittest.main(verbosity=2)
