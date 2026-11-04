#!/usr/bin/env python3
"""W136 art regressions. Offline evidence only; does not launch native software."""
import base64
import hashlib
import json
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_crown_splitter.py'))
CANONICAL_SHA='50c519fa916a61e749ed7c72c29cf9fc4f173e93d8bbeaad98ad330dabfc3cdf'

def read(p):
    return json.loads((ROOT/p).read_bytes())

def inside(p,e):
    p=np.array(p,float);r=e.get('rotation')
    if r:
        o=np.array(r['origin']);p=(p-o)@G['H']['rotation']({r['axis']:r['angle']})+o
    return bool(np.all(p>=np.array(e['from'])-1e-8) and np.all(p<=np.array(e['to'])+1e-8))

class CrownSplitterArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=read(G['MODEL']);cls.d=read(G['ART']+'design.json');cls.man=read(G['ART']+'manifest.json')
        cls.bb=read(G['ART']+'inspection.bbmodel');cls.es={e['name']:e for e in cls.m['elements']}
        cls.px=np.asarray(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))

    def test_assembled_budget_and_native_cube_schema(self):
        n=len(self.m['elements'])
        self.assertEqual(78,n);self.assertEqual(n,len(self.es));self.assertLessEqual(n,1000)
        self.assertEqual(n,self.man['assembled_elements']);self.assertEqual(n,sum(self.man['groups'].values()))
        self.assertEqual(n*6,self.man['emitted_faces']);self.assertEqual(0,self.man['triangle_adapter_elements'])
        for e in self.es.values():
            self.assertTrue(set(e)<={'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.isfinite(G['vertices'](e)).all())
            self.assertEqual(set(G['FACES']),set(e['faces']))
            if 'rotation' in e:
                self.assertEqual({'axis','angle','origin'},set(e['rotation']))
                self.assertIn(e['rotation']['axis'],'xyz')

    def test_filled_blade_grip_and_physical_fuller(self):
        # The middle of the sword is solid; depression must not become a hole.
        for y in (13,18,24,27):
            self.assertTrue(inside([8,y,8],self.es['fuller_web']))
            self.assertFalse(any(inside([8.15,y,8],e) for e in self.es.values()))
            self.assertTrue(any(inside([8.15,y,8.25],e) for e in self.es.values()))
        for p in ([8,12.4,7.25],[8,15,7.50],[8,26,7.55],[8,30,8],[8,4.9901939311001655,8]):
            self.assertTrue(any(inside(p,e) for e in self.es.values()),p)
        self.assertGreater(self.es['blade_shoulder_1']['to'][1]-self.es['blade_shoulder_1']['from'][1],17)
        self.assertGreater(self.es['blade_shoulder_1']['to'][0]-self.es['blade_shoulder_1']['from'][0],.4)
        self.assertGreater(self.es['grip_core']['to'][1]-self.es['grip_core']['from'][1],5.9)
        self.assertGreater(self.es['grip_core']['to'][2]-self.es['grip_core']['from'][2],.59)

    def test_guard_finger_air_is_geometry(self):
        # Two representative gaps above the wing support, visible from either side.
        for z in (6.48,9.52):
            self.assertFalse(any(inside([8,10.18,z],e) for e in self.es.values()),z)
        for z in (6.32,9.68):
            self.assertTrue(any(inside([8,10.18,z],e) for e in self.es.values()),z)

    def test_canonical_display_hand_scale_and_positive_y_sword(self):
        self.assertEqual(CANONICAL_SHA,G['sha']((ROOT/G['BASE']).read_bytes()))
        self.assertEqual(read(G['BASE'])['display'],self.m['display'])
        self.assertEqual([8,4.9901939311001655,8],self.man['source_anchor'])
        self.assertEqual(18.28510919435076,self.man['source_scale'])
        np.testing.assert_allclose(self.man['actual_bounds'],self.man['source_bounds'],atol=.06,rtol=0)
        self.assertEqual('+Y',self.d['coordinate_policy']['length'])
        self.assertGreater(self.es['tip_core']['to'][1],31)
        self.assertLess(self.es['pommel_tip']['from'][1],2.51)
        catalogue=read('src/main/resources/destiny/weapons/w30.json')
        self.assertEqual('sword',next(w for w in catalogue if w['id']=='crown_splitter')['family'])

    def test_real_source_objects_translation_and_hashes(self):
        meshes,meta=G['source_meshes']()
        self.assertEqual(['Crown-Splitter.00.000','Crown-Splitter.01.000'],sorted(m['name'] for m in meshes))
        self.assertEqual(4240,sum(len(m['faces']) for m in meshes))
        pts=np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=2e-6,rtol=0)
        self.assertEqual([0,10,0],self.d['coordinate_policy']['fbx_translation_cm'])
        # Omitting translation yields exactly this erroneous native displacement.
        self.assertAlmostEqual(1.828510919435076,meta['scale']*.1)
        for p,digest in self.d['input_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        for p,digest in self.d['raw_input_sha256'].items():self.assertEqual(digest,G['sha'](Path(p).read_bytes()),p)
        ref=next(r for r in read('art/weapons/w31/references.json') if r['id']=='crown_splitter')
        self.assertEqual(ref['sha256'],G['sha'](G['PHOTO'].read_bytes()))
        self.assertEqual('062d34953b1f11e4ac76204c95f073b9684387fd90468d78f3612031d3f7caf1',meta['source_files']['Crown-Splitter.fbx'])

    def test_all_faces_opaque_with_continuous_uv_and_gutters(self):
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
            self.assertTrue((self.px[y-2:y,x:X]==self.px[y:y+1,x:X]).all())
        self.assertEqual(468,len(seen));self.assertEqual(0,self.man['alpha_body_elements'])
        # Long broad faces retain hundreds of texels, rather than tiny tiled islands.
        face=next(r for r in self.d['atlas']['islands'] if r['element']=='blade_shoulder_1' and r['face']=='east')
        self.assertGreater(max(face['pixels'][2]-face['pixels'][0],face['pixels'][3]-face['pixels'][1]),350)

    def test_editable_bb_and_paint_identity(self):
        self.assertEqual({*self.es},{e['name'] for e in self.bb['elements']})
        self.assertEqual(78,sum(len(g['children']) for g in self.bb['outliner']))
        self.assertEqual((ROOT/G['TEXTURE']).read_bytes(),base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]))
        self.assertEqual(self.m['display'],self.bb['display'])
        self.assertEqual([8,4.9901939311001655,8],self.bb['destiny_w136']['sourceAnchor'])
        for e in self.bb['elements']:
            for face,f in e['faces'].items():
                np.testing.assert_allclose(f['uv'],np.array(self.es[e['name']]['faces'][face]['uv'])*64)
        self.assertEqual([17,25,39],G['PALETTE']['navy']);self.assertEqual([198,204,199],G['PALETTE']['wrap'])

    def test_manifest_artifacts_and_scope(self):
        scope=next(f['owned_paths'] for f in read('docs/qa/2026-10-26/w136/batch.json')['features'] if f['name']=='w136-crown_splitter')
        self.assertEqual(10,len(scope));self.assertTrue(all((ROOT/p).is_file() for p in scope))
        self.assertLess(sum((ROOT/p).stat().st_size for p in scope),25*1024*1024)
        for p,digest in self.man['output_sha256'].items():
            self.assertIn(p,scope);self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()))
        self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_crown_splitter.py').read_bytes()))
        self.assertFalse(self.man['native_accepted']);self.assertTrue(self.man['full_only'])
        self.assertFalse((ROOT/G['MODEL'].replace('.json','_body.json')).exists())
        self.assertFalse((ROOT/G['MODEL'].replace('.json','_magazine.json')).exists())
        with Image.open(ROOT/G['ART']/'comparison.png') as im:self.assertEqual((1800,2100),im.size)

    def test_deterministic_all_generated_bytes_including_comparison(self):
        outputs=G['generate']()
        self.assertEqual(7,len(outputs))
        for p,data in outputs.items():self.assertEqual((ROOT/p).read_bytes(),data,p)

if __name__=='__main__':unittest.main(verbosity=2)
