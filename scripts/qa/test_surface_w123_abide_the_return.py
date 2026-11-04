#!/usr/bin/env python3
"""W141 isolated offline art regression; never invokes DCC, game or Gradle."""
import base64
import copy
import json
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_abide_the_return.py'))
CANONICAL_SHA='8f6f9593d9a8dbd84022d4fe726152f799b71a55ae253e3f636e0bc5f46534c8'
def read(p):return json.loads((ROOT/p).read_bytes())
def inside(p,e):
    p=np.array(p,float);r=e.get('rotation')
    if r:p=(p-r['origin'])@G['H']['rotation']({r['axis']:r['angle']})+r['origin']
    return bool(np.all(p>=np.array(e['from'])-1e-8) and np.all(p<=np.array(e['to'])+1e-8))
class AbideTheReturnArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=read(G['MODEL']);cls.d=read(G['ART']+'design.json');cls.man=read(G['ART']+'manifest.json')
        cls.bb=read(G['ART']+'inspection.bbmodel');cls.es={e['name']:e for e in cls.m['elements']}
        cls.px=np.asarray(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))
    def test_01_budget_and_native_cuboid_schema(self):
        n=len(self.es);self.assertEqual(n,len(self.m['elements']));self.assertLessEqual(n,1000)
        self.assertEqual(n,self.man['assembled_elements']);self.assertEqual(n,sum(self.man['groups'].values()))
        self.assertEqual(n*6,self.man['emitted_faces']);self.assertEqual(0,self.man['triangle_adapter_elements'])
        for e in self.es.values():
            self.assertTrue(set(e)<={'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.isfinite(G['vertices'](e)).all())
            self.assertEqual(set(G['FACES']),set(e['faces']))
            if 'rotation' in e:self.assertEqual({'axis','angle','origin'},set(e['rotation']))
    def test_02_blade_continuity_and_filled_center(self):
        stations=self.d['blade_stations']
        for a,b in zip(stations,stations[1:]):
            for t in np.linspace(0,1,13):
                y=(1-t)*a[0]+t*b[0];lo=(1-t)*a[1]+t*b[1];hi=(1-t)*a[2]+t*b[2]
                self.assertTrue(any(inside([8,y,(lo+hi)/2],e) for e in self.es.values()),(y,lo,hi))
        for p in ([8.1,15,7.5],[7.9,24,6.9],[8,30,7.9],[8,31.2,9]):
            self.assertTrue(any(inside(p,e) for e in self.es.values()),p)
    def test_03_structural_section_has_real_thickness(self):
        for p in ([8,15,7.4],[8,24,6.7]):self.assertTrue(any(inside(p,e) for e in self.es.values()))
        self.assertGreater(self.es['blade_shoulder_02']['to'][0]-self.es['blade_shoulder_02']['from'][0],.30)
        self.assertLess(self.es['cutting_margin_02']['to'][0]-self.es['cutting_margin_02']['from'][0],.09)
        self.assertFalse(any(inside([8.5,24,6.7],e) for e in self.es.values()))
    def test_04_grip_covers_exact_source_hand_anchor(self):
        anchor=self.d['source']['anchor'];self.assertEqual([8,5.754881070852484,8],anchor)
        self.assertTrue(inside(anchor,self.es['grip_core']))
        for y in (3.7,5.75,8.5):self.assertTrue(inside([8,y,7.7],self.es['grip_core']))
        self.assertGreater(self.es['grip_core']['to'][1]-self.es['grip_core']['from'][1],5)
        self.assertGreater(self.es['grip_core']['to'][2]-self.es['grip_core']['from'][2],.7)
    def test_05_guard_eye_and_hook_throat_are_actual_air(self):
        for x in np.linspace(7.5,8.5,9):
            self.assertFalse(any(inside([x,9.80,8.43],e) for e in self.es.values()),x)
        self.assertTrue(any(inside([8,9.57,8.43],e) for e in self.es.values()))
        self.assertFalse(any(inside([8,10.9,6.5],e) for e in self.es.values()))
        self.assertTrue(any(inside([8,11.10,6.09],e) for e in self.es.values()))
    def test_06_canonical_display_and_axis(self):
        self.assertEqual(CANONICAL_SHA,G['sha']((ROOT/G['BASE']).read_bytes()))
        self.assertEqual(read(G['BASE'])['display'],self.m['display'])
        self.assertEqual('+Y',self.d['coordinate_policy']['length'])
        self.assertEqual(21.448546065185557,self.man['source_scale'])
        np.testing.assert_allclose(self.man['actual_bounds'],self.man['source_bounds'],atol=.10,rtol=0)
        self.assertLess(self.man['actual_bounds'][0][1],2.51);self.assertGreater(self.man['actual_bounds'][1][1],31.4)
    def test_07_real_fbx_and_w30_duplicate_provenance(self):
        meshes,meta=G['source_meshes']();p=np.concatenate([m['vertices'] for m in meshes])
        self.assertEqual(2,len(meshes));self.assertEqual(19304,sum(len(m['faces']) for m in meshes))
        self.assertEqual(38608,meta['source_triangles']);self.assertEqual(4,len(meta['source_objects']))
        np.testing.assert_allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=2e-6,rtol=0)
        self.assertEqual([0,0,0],self.d['coordinate_policy']['fbx_translation_cm'])
        self.assertEqual(19304,self.man['fbx_source_triangles'])
    def test_08_all_input_hashes_and_default_reference(self):
        for p,digest in self.d['input_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        for p,digest in self.d['raw_input_sha256'].items():self.assertEqual(digest,G['sha'](Path(p).read_bytes()),p)
        ref=next(r for r in read('art/weapons/w31/references.json') if r['id']=='abide_the_return')
        self.assertEqual(ref['sha256'],G['sha'](G['PHOTO'].read_bytes()))
        row=next(r for r in read('src/main/resources/destiny/weapons/w30.json') if r['id']=='abide_the_return')
        self.assertEqual(('sword','adaptive'),(row['family'],row['frame']))
    def test_09_opaque_atlas_faces_and_extruded_gutters(self):
        self.assertEqual((1024,1024,4),self.px.shape);self.assertTrue((self.px[:,:,3]==255).all())
        cover=np.zeros((1024,1024),bool);seen=set()
        for r in self.d['atlas']['islands']:
            x,y,X,Y=r['pixels'];key=(r['element'],r['face']);self.assertNotIn(key,seen);seen.add(key)
            self.assertGreaterEqual(min(x,y),2);self.assertLessEqual(max(X,Y),1022)
            self.assertGreater(X,x);self.assertGreater(Y,y)
            self.assertFalse(cover[y-2:Y+2,x-2:X+2].any());cover[y-2:Y+2,x-2:X+2]=True
            f=self.es[r['element']]['faces'][r['face']]
            self.assertEqual('#0',f['texture']);np.testing.assert_allclose(f['uv'],np.array([x,y,X,Y])/64)
            self.assertNotIn('cullface',f)
            tile=self.px[y:Y,x:X]
            np.testing.assert_array_equal(self.px[y-2:Y+2,x-2:X+2],np.pad(tile,((2,2),(2,2),(0,0)),mode='edge'))
        self.assertEqual(len(self.es)*6,len(seen));self.assertEqual(0,self.man['alpha_body_elements'])
    def test_10_painted_default_material_identity(self):
        self.assertEqual([192,160,83],self.d['palette']['gold']);self.assertEqual([52,88,111],self.d['palette']['blue'])
        self.assertEqual([194,196,187],self.d['palette']['silver'])
        # Same material paint uses model coordinates and remains fully opaque on every side.
        for spec in self.d['parts']:
            for face in ('east','west'):
                px=np.asarray(G['tile'](spec,face,32,64));self.assertTrue((px[:,:,3]==255).all())
        grip=next(s for s in self.d['parts'] if s['geometry']['name']=='grip_core')
        px=np.asarray(G['tile'](grip,'east',64,256))[:,:,:3]
        self.assertGreater(np.unique(px.reshape(-1,3),axis=0).shape[0],8)
    def test_11_editable_inspection_geometry_texture_and_display(self):
        self.assertEqual(set(self.es),{e['name'] for e in self.bb['elements']})
        self.assertEqual(len(self.es),sum(len(g['children']) for g in self.bb['outliner']))
        self.assertEqual((ROOT/G['TEXTURE']).read_bytes(),base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]))
        self.assertEqual(self.m['display'],self.bb['display'])
        for e in self.bb['elements']:
            src=self.es[e['name']];self.assertEqual(src['from'],e['from']);self.assertEqual(src['to'],e['to'])
            r=src.get('rotation');self.assertEqual([r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],e['rotation'])
            for face,f in e['faces'].items():np.testing.assert_allclose(f['uv'],np.array(src['faces'][face]['uv'])*64)
        self.assertFalse(self.bb['destiny_w141']['nativeAccepted'])
    def test_12_manifest_scope_full_only_and_artifact_hashes(self):
        scope=next(f['owned_paths'] for f in read('docs/qa/2026-10-26/w141/batch.json')['features'] if f['name']=='w141-abide_the_return')
        self.assertEqual(10,len(scope));self.assertTrue(all((ROOT/p).is_file() for p in scope))
        for p,digest in self.man['output_sha256'].items():
            self.assertIn(p,scope);self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()))
        self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_abide_the_return.py').read_bytes()))
        self.assertFalse(self.man['native_accepted']);self.assertTrue(self.man['full_only'])
        self.assertFalse((ROOT/G['MODEL'].replace('.json','_body.json')).exists())
        self.assertFalse((ROOT/G['MODEL'].replace('.json','_magazine.json')).exists())
        self.assertLess(sum((ROOT/p).stat().st_size for p in scope),10*1024*1024)
    def test_13_comparison_contains_required_views(self):
        with Image.open(ROOT/G['ART']/'comparison.png') as im:
            self.assertEqual((1800,2500),im.size)
            for box in ((0,540,600,1250),(1200,540,1800,1250),(1200,1290,1800,2000),(0,2060,580,2470)):
                px=np.asarray(im.crop(box));mask=np.any(px!=[32,39,48],axis=2)
                yy,xx=np.where(mask);self.assertGreater(mask.mean(),.005);self.assertLess(mask.mean(),.15)
                self.assertGreater(np.ptp(yy),px.shape[0]*.70);self.assertGreater(np.ptp(xx),12)
    def test_14_deterministic_all_generated_bytes(self):
        outputs=G['generate']();self.assertEqual(7,len(outputs))
        for p,data in outputs.items():self.assertEqual((ROOT/p).read_bytes(),data,p)
if __name__=='__main__':unittest.main(verbosity=2)
