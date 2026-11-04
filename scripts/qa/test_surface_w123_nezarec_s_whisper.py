"""W143 focused Nezarec art checks; offline evidence, not visual/FPS certification."""
import base64
import hashlib
import json
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
G = runpy.run_path(str(ROOT/'scripts/generate_surface_w123_nezarec_s_whisper.py'))

def read(path):
    return json.loads((ROOT/path).read_bytes())

def inside(point, element):
    p = np.array(point, float)
    if 'rotation' in element:
        r = element['rotation']; o = np.array(r['origin'])
        p = (p-o) @ G['H']['rotation']({r['axis']:r['angle']})+o
    return bool(np.all(p > np.array(element['from'])+1e-6) and np.all(p < np.array(element['to'])-1e-6))

class NezarecArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = read(G['ART']+'design.json')
        cls.manifest = read(G['ART']+'manifest.json')
        cls.model = read(G['MODEL']); cls.es = cls.model['elements']
        cls.lookup = {e['name']:e for e in cls.es}
        cls.bb = read(G['ART']+'inspection.bbmodel')
        cls.px = np.array(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))

    def test_assembled_budget_native_schema_and_semantic_depth(self):
        self.assertTrue(0 < len(self.es) <= 1000)
        self.assertEqual(len(self.es), len(self.lookup))
        self.assertEqual(len(self.es), self.manifest['assembled_elements'])
        self.assertEqual(0, self.manifest['triangle_adapter_elements'])
        self.assertEqual(0, self.manifest['alpha_body_elements'])
        for e in self.es:
            self.assertLessEqual(set(e), {'name','from','to','faces','rotation'})
            self.assertTrue(np.all(np.array(e['to']) > e['from']))
            self.assertTrue(np.isfinite(G['vertices'](e)).all())
            self.assertEqual(set(G['FACES']), set(e['faces']))
        for name, point in [('gold_stock',[8,4.5,8]),('ivory_bound_grip_core',[8,12,8]),
                            ('forged_core_core',[8,16,7.91]),('blade_core',[8,24,7.8])]:
            self.assertTrue(inside(point, self.lookup[name]), name)

    def test_blade_axis_grip_and_accepted_display_preserved(self):
        self.assertEqual(read(G['BASE'])['display'], self.model['display'])
        meta = read(G['BB'])['destiny_w30']
        self.assertEqual(meta['scale'], self.manifest['source_scale'])
        self.assertEqual(meta['anchor'], self.manifest['source_anchor'])
        self.assertEqual('+Y', self.design['coordinate_policy']['blade_axis'])
        points = np.concatenate([G['vertices'](e) for e in self.es])
        self.assertLess(abs(points[:,1].min()-meta['model_bounds'][0][1]), .15)
        self.assertLess(abs(points[:,1].max()-meta['model_bounds'][1][1]), .15)
        self.assertTrue(inside([8,8,8], self.lookup['bare_fluted_shaft_core']))

    def test_open_crescent_and_stock_underguard(self):
        for point in ([8,16,6.65], [8,5.15,7.55]):
            self.assertFalse(any(inside(point,e) for e in self.es), point)
        self.assertEqual(7, sum(e['name'].startswith('gold_crescent_') for e in self.es))
        self.assertEqual(8, sum(e['name'].startswith('gold_pivot_rim_') for e in self.es))
        self.assertGreaterEqual(sum(e['name'].startswith('raised_rib_') for e in self.es), 20)

    def test_real_source_names_counts_and_frame(self):
        meshes, meta = G['source_meshes']()
        self.assertEqual(5,len(meshes)); self.assertEqual(34330,sum(len(m['faces']) for m in meshes))
        self.assertEqual(34246,sum(len(m['faces']) for m in meshes if m['textured']))
        self.assertEqual(84,self.manifest['untextured_auxiliary_triangles'])
        self.assertNotEqual(set(meta['source_objects']),{m['name'] for m in meshes})
        points = np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=1e-5,rtol=0)

    def test_reference_and_immutable_inputs(self):
        for path, expected in self.design['input_sha256'].items():
            self.assertEqual(expected,G['sha']((ROOT/path).read_bytes()),path)
        for path, expected in self.design['raw_input_sha256'].items():
            self.assertEqual(expected,G['sha'](Path(path).read_bytes()),path)
        row = next(x for x in read('art/weapons/w31/references.json') if x['id']=='nezarec_s_whisper')
        self.assertEqual(row['sha256'],hashlib.sha256(G['PHOTO'].read_bytes()).hexdigest())
        self.assertNotIn('src/main/resources/weapon_surface_w123/manifest.json',self.design['input_sha256'])

    def test_face_uv_opacity_and_gutters(self):
        self.assertEqual((1024,1024,4),self.px.shape)
        cover = np.zeros((1024,1024),bool)
        self.assertEqual(6*len(self.es),len(self.design['atlas']['islands']))
        for row in self.design['atlas']['islands']:
            x,y,X,Y = row['pixels']
            self.assertFalse(cover[y-2:Y+2,x-2:X+2].any())
            cover[y-2:Y+2,x-2:X+2] = True
            self.assertTrue(np.all(self.px[y-2:Y+2,x-2:X+2,3]==255))
            uv = self.lookup[row['element']]['faces'][row['face']]['uv']
            np.testing.assert_allclose(uv,np.array([x,y,X,Y])/64,atol=1e-9)

    def test_default_material_identity_and_honest_limits(self):
        self.assertGreater(G['PALETTE']['gold'][0],G['PALETTE']['gold'][2]*2)
        self.assertGreater(G['PALETTE']['red'][0],G['PALETTE']['red'][1]*3)
        self.assertIn('crescent', self.manifest['groups'])
        self.assertIn('grip', self.manifest['groups'])
        self.assertTrue(any('84 untextured' in x for x in self.manifest['limitations']))

    def test_editable_inspection_and_full_only_outputs(self):
        self.assertTrue(self.manifest['full_only']); self.assertFalse(self.manifest['native_accepted'])
        self.assertEqual(len(self.es),len(self.bb['elements']))
        self.assertEqual(len(self.es),sum(len(g['children']) for g in self.bb['outliner']))
        self.assertEqual((ROOT/G['TEXTURE']).read_bytes(),base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]))
        for path, expected in self.manifest['output_sha256'].items():
            self.assertEqual(expected,G['sha']((ROOT/path).read_bytes()),path)
        self.assertFalse((ROOT/G['MODEL'].replace('.json','_magazine.json')).exists())

    def test_deterministic_generation(self):
        for path, data in G['generate'](include_comparison=False).items():
            if not path.endswith('manifest.json'):
                self.assertEqual(data,(ROOT/path).read_bytes(),path)

if __name__=='__main__':
    unittest.main(verbosity=2)
