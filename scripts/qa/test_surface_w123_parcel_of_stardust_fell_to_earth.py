"""W147 Parcel art checks, not visual/native/FPS certification."""
import base64
import json
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_parcel_of_stardust_fell_to_earth.py'))
def read(p):return json.loads((ROOT/p).read_bytes())
def inside(point,e):
    p=np.array(point,float)
    if 'rotation' in e:
        q=e['rotation'];o=np.array(q['origin']);p=(p-o)@G['H']['rotation']({q['axis']:q['angle']})+o
    return bool(np.all(p>np.array(e['from'])+1e-6) and np.all(p<np.array(e['to'])-1e-6))

class ParcelArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=read(G['ART']+'design.json');cls.m=read(G['ART']+'manifest.json')
        cls.model=read(G['MODEL']);cls.es=cls.model['elements'];cls.lookup={e['name']:e for e in cls.es}
        cls.bb=read(G['ART']+'inspection.bbmodel');cls.px=np.array(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))

    def test_solid_geometry_and_assembled_budget(self):
        self.assertTrue(0<len(self.es)<=1000);self.assertEqual(len(self.es),len(self.lookup))
        self.assertEqual(len(self.es),self.m['assembled_elements']);self.assertEqual(0,self.m['alpha_body_elements'])
        self.assertEqual(0,self.m['triangle_adapter_elements'])
        for e in self.es:
            self.assertLessEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']));self.assertTrue(np.isfinite(G['vertices'](e)).all())
            self.assertEqual(set(G['FACES']),set(e['faces']))
        for name,p in self.d['solid_probes'].items():self.assertTrue(any(inside(p,e) for e in self.es),name)

    def test_actual_air_ports_grip_guard_and_sight(self):
        for name,p in self.d['required_air_probes'].items():self.assertFalse(any(inside(p,e) for e in self.es),name)
        for name in ('bore_backstop','magazine_front_depth'):
            self.assertLess(self.lookup[name]['to'][2],-9.1)
            self.assertGreater(self.lookup[name]['from'][2],-9.3)
        self.assertEqual(10,sum(e['name'].startswith('finger_scallop_') for e in self.es))

    def test_verified_source_counts_and_frame_not_erentil_basis(self):
        meshes,meta,ref=G['source_meshes']();self.assertEqual(2,len(meshes))
        self.assertEqual(11272,sum(len(m['faces']) for m in meshes))
        self.assertEqual(11272,sum(len(m['faces']) for m in meshes if m['material']))
        p=np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=1e-5,rtol=0)
        self.assertIn('[X,Z,Y]',self.d['source_mapping']);self.assertEqual(ref['sha256'],G['sha'](G['PHOTO'].read_bytes()))

    def test_accepted_display_and_anchor_preserved(self):
        self.assertEqual(read(G['BASE'])['display'],self.model['display'])
        meta=read(G['BB'])['destiny_w30'];self.assertEqual(meta['scale'],self.d['scale']);self.assertEqual(meta['anchor'],self.d['anchor'])
        p=np.concatenate([G['vertices'](e) for e in self.es]);bounds=np.array([p.min(0),p.max(0)])
        # Representative span/hand frame check, not an exact source-equivalence gate.
        self.assertLess(abs(bounds[0,2]-meta['model_bounds'][0][2]),.15)
        self.assertLess(abs(bounds[1,2]-meta['model_bounds'][1][2]),.15)
        self.assertLess(abs(bounds[0,1]-meta['model_bounds'][0][1]),.15)

    def test_opaque_uv_faces_and_nonoverlapping_gutters(self):
        self.assertEqual((1024,1024,4),self.px.shape);cover=np.zeros((1024,1024),bool)
        self.assertEqual(6*len(self.es),len(self.d['atlas']['islands']))
        for row in self.d['atlas']['islands']:
            x,y,X,Y=row['pixels'];self.assertFalse(cover[y-2:Y+2,x-2:X+2].any());cover[y-2:Y+2,x-2:X+2]=True
            self.assertTrue(np.all(self.px[y-2:Y+2,x-2:X+2,3]==255))
            np.testing.assert_allclose(self.lookup[row['element']]['faces'][row['face']]['uv'],np.array([x,y,X,Y])/64,atol=1e-9)

    def test_clean_default_bluel_steel_and_warm_wood(self):
        self.assertGreater(G['PALETTE']['blue'][2],G['PALETTE']['blue'][0])
        self.assertGreater(G['PALETTE']['wood'][0],G['PALETTE']['wood'][2])
        self.assertEqual(0,self.m['alpha_body_elements'])
        self.assertIn('not recovered PBR',self.d['limitations'][0])

    def test_input_pins_do_not_include_shared_migration_manifest(self):
        for p,h in self.d['input_sha256'].items():self.assertEqual(h,G['sha']((ROOT/p).read_bytes()),p)
        for p,h in self.d['raw_input_sha256'].items():self.assertEqual(h,G['sha'](Path(p).read_bytes()),p)
        self.assertNotIn('src/main/resources/weapon_surface_w123/manifest.json',self.d['input_sha256'])

    def test_editable_inspection_and_full_only(self):
        self.assertTrue(self.m['full_only']);self.assertFalse(self.m['native_accepted'])
        self.assertEqual(len(self.es),len(self.bb['elements']));self.assertEqual(len(self.es),sum(len(g['children']) for g in self.bb['outliner']))
        self.assertEqual((ROOT/G['TEXTURE']).read_bytes(),base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]))
        self.assertEqual(self.model['display'],self.bb['display'])
        self.assertFalse((ROOT/G['MODEL'].replace('.json','_magazine.json')).exists())
        for p,h in self.m['output_sha256'].items():self.assertEqual(h,G['sha']((ROOT/p).read_bytes()),p)

    def test_deterministic_products(self):
        for p,data in G['generate'](include_comparison=False).items():
            if not p.endswith('manifest.json'):self.assertEqual(data,(ROOT/p).read_bytes(),p)

if __name__=='__main__':unittest.main(verbosity=2)
