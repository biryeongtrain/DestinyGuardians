#!/usr/bin/env python3
"""Targeted offline W149 product regression. No client/DCC/build/cache writes."""
import base64, copy, io, json, runpy, unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_dimensional_hypotrochoid.py'))
def read(p):return json.loads((ROOT/p).read_bytes())
class SurfaceW149(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=read(G['ART']+'design.json');cls.m=read(G['MODEL']);cls.man=read(G['ART']+'manifest.json')
  cls.atlas=Image.open(ROOT/G['TEXTURE']).convert('RGBA');cls.es=cls.m['elements']
 def occupied(self,points,elements=None):
  p=np.atleast_2d(points).astype(float);hit=np.zeros(len(p),bool)
  for e in elements or self.es:
   q=p
   if 'rotation' in e:
    r=e['rotation'];o=np.array(r['origin']);R=G['H']['rotation']({r['axis']:r['angle']});q=(p-o)@R+o
   hit|=((q>=np.array(e['from'])-1e-7)&(q<=np.array(e['to'])+1e-7)).all(1)
  return hit
 def test_01_exact_ten_owned_paths(self):
  f=next(x for x in read(G['BATCH'])['features'] if x['name']=='w149-'+G['ID'])
  self.assertEqual(set(f['owned_paths']),set(G['OWNED']));self.assertEqual(len(f['owned_paths']),10)
  self.assertTrue(all((ROOT/p).is_file() for p in f['owned_paths']))
 def test_02_full_only_schema_budget(self):
  self.assertEqual(len(self.es),self.man['assembled_elements']);self.assertGreaterEqual(len(self.es),80);self.assertLessEqual(len(self.es),1000)
  self.assertTrue(self.man['full_only']);self.assertTrue(self.man['existing_generic_reload']);self.assertFalse(self.man['native_accepted'])
  self.assertEqual(self.man['triangle_adapter_elements'],0);self.assertEqual(self.man['alpha_body_elements'],0)
  self.assertNotIn('parent',self.m);self.assertNotIn('animations',self.m)
  self.assertEqual(self.m['textures']['0'],'destiny:item/weapon/w123/dimensional_hypotrochoid')
  for e in self.es:
   self.assertEqual(set(e)-{'name','from','to','rotation','faces'},set())
   self.assertEqual(set(e['faces']),set(G['FACES']))
   if 'rotation' in e:self.assertEqual(set(e['rotation']),{'origin','axis','angle'})
 def test_03_finite_positive_bounds(self):
  names=[]
  for e in self.es:
   names.append(e['name']);v=G['vertices'](e);self.assertTrue(np.isfinite(v).all())
   self.assertTrue((np.array(e['to'])>e['from']).all());self.assertTrue((v>-32).all() and (v<48).all())
  self.assertEqual(len(names),len(set(names)))
  p=np.concatenate([G['vertices'](e) for e in self.es]);np.testing.assert_allclose([p.min(0),p.max(0)],self.man['actual_bounds'])
  self.assertLess(np.max(np.abs(np.array(self.man['actual_bounds'])-self.d['source']['model_bounds'])),.35)
 def test_04_exact_display_anchor_and_grips(self):
  self.assertEqual(self.m['display'],read(G['BASE'])['display'])
  self.assertEqual(self.d['coordinate_policy']['anchor'],[8,8,8]);self.assertEqual(self.man['source_scale'],self.d['source']['scale'])
  c=self.d['coordinate_policy'];self.assertEqual(c['grip_top'],[8,9.55,8.78]);self.assertEqual(c['grip_heel'],[8,6.90,7.94])
  self.assertEqual(c['foregrip_top'],[8,9.35,-3.4]);self.assertEqual(c['foregrip_heel'],[8,6.48,-2.01])
 def test_05_actual_source_transforms_selection_and_bounds(self):
  ms,meta=G['source_meshes']();self.assertEqual(meta['source_triangles'],15434)
  self.assertEqual({m['name'] for m in ms},set(meta['source_objects']))
  self.assertFalse(set(meta['excluded_objects'])&{m['name'] for m in ms})
  self.assertEqual(meta['source_axis'],dict(length=0,thin=1,muzzle_sign=1))
  self.assertEqual(sum(len(m['faces']) for m in ms),15434)
  for m in ms:
   np.testing.assert_allclose(m['object_transform']['Lcl Rotation'],[-90,90,0],atol=.00002)
   self.assertEqual(m['object_transform']['Lcl Scaling'],[100,100,100])
 def test_06_input_and_default_photo_hashes(self):
  for key in ('input_sha256','raw_input_sha256'):
   for path,digest in self.d[key].items():
    p=Path(path) if Path(path).is_absolute() else ROOT/path
    self.assertEqual(G['sha'](p.read_bytes()),digest,path)
  self.assertEqual(self.d['reference']['sha256'],'88d70d4fec7e31491c4e2df187f204c6c1a896352fc3decb26c612143e7ac466')
 def test_07_opaque_atlas_and_unique_uv_islands(self):
  a=np.array(self.atlas);self.assertEqual(self.atlas.size,(1024,1024));self.assertTrue((a[:,:,3]==255).all())
  ledger=self.d['atlas']['islands'];self.assertEqual(len(ledger),len(self.es)*6)
  used=np.zeros((1024,1024),bool);islands={(s['element'],s['face']):s['pixels'] for s in ledger}
  for e in self.es:
   for face,f in e['faces'].items():
    self.assertEqual(f['texture'],'#0');uv=np.array(f['uv']);self.assertTrue(np.isfinite(uv).all())
    x,y,xx,yy=islands[(e['name'],face)];self.assertGreaterEqual(min(x,y),2);self.assertLessEqual(max(xx,yy),1022)
    np.testing.assert_allclose(uv,np.array([x,y,xx,yy])/64)
    self.assertFalse(used[y-2:yy+2,x-2:xx+2].any());used[y-2:yy+2,x-2:xx+2]=True
    self.assertTrue((a[y-2:yy+2,x-2:xx+2,3]==255).all())
    np.testing.assert_array_equal(a[y-1,x:xx],a[y,x:xx]);np.testing.assert_array_equal(a[yy,x:xx],a[yy-1,x:xx])
 def test_08_real_open_muzzle(self):
  # Sample a narrow cylinder, not merely a black texture dot.
  points=[[8+dx,11.35+dy,z] for dx in (-.25,0,.25) for dy in (-.25,0,.25) for z in np.linspace(-9.10,-.16,48)]
  self.assertFalse(self.occupied(points).any());self.assertTrue(self.occupied([[8,11.35,-.06]])[0])
 def test_09_sight_ray_and_pin(self):
  s=self.d['ads_sight'];self.assertEqual(s['eyeSide'],'+Z');self.assertEqual(s['plane'],'XY');self.assertEqual(s['style'],'optic')
  np.testing.assert_allclose(np.array(s['forwardPoint'])-s['sightCenter'],[0,0,-2])
  x,y,z=s['sightCenter'];points=[[x+dx,y+dy,zz] for dx in (-.10,0,.10) for dy in (-.02,0,.08) for zz in np.linspace(-10,18,180)]
  self.assertFalse(self.occupied(points).any())
  pin=next(e for e in self.es if e['name']=='aiming_pin');self.assertAlmostEqual(pin['to'][1],14.21)
  self.assertLess(y-pin['to'][1],.06);self.assertGreater(y-pin['to'][1],0)
  self.assertTrue(self.occupied([[8.19,14.1,5.24]],[pin])[0])
 def test_10_stock_trigger_and_lattice_openings(self):
  for y,z in [(10.95,13.0),(9.68,6.70),(8.0,8.72)]:
   self.assertFalse(self.occupied([[x,y,z] for x in np.linspace(3,11,100)]).any(),(y,z))
 def test_11_semantic_filled_volumes_and_continuous_beam(self):
  self.assertTrue(self.occupied([[8,10.16,2.6],[8,12.7,-4],[8,12.7,3],[8,12.7,10],[8,8.1,-2.5]]).all())
  self.assertTrue(self.occupied([[8,12.65,z] for z in np.linspace(-9.0,15.4,120)]).all())
  groups=self.man['groups'];self.assertGreaterEqual(groups['drum'],12);self.assertGreaterEqual(groups['sight'],10)
 def test_12_feature_identity_and_material_contrast(self):
  self.assertEqual(len(self.d['identity']),4)
  for role in ('cyan','silver','graphite','navy','magenta','violet','pin'):self.assertIn(role,self.d['palette'])
  rgb=np.array(self.atlas)[:,:,:3];magenta=(rgb[:,:,0]>190)&(rgb[:,:,2]>190)&(rgb[:,:,1]<180)
  self.assertGreater(magenta.sum(),300)
  self.assertIn('latch_upper_panel',{e['name'] for e in self.es});self.assertIn('central_crown',{e['name'] for e in self.es})
 def test_13_inspection_exact_parity(self):
  b=read(G['ART']+'inspection.bbmodel');self.assertEqual(b['display'],self.m['display'])
  self.assertEqual(len(b['elements']),len(self.es));by={e['name']:e for e in b['elements']}
  for e in self.es:
   bb=by[e['name']];self.assertEqual(bb['from'],e['from']);self.assertEqual(bb['to'],e['to'])
   rr=e.get('rotation');self.assertEqual(bb['rotation'],[rr['angle'] if rr and rr['axis']==a else 0 for a in 'xyz'])
   for f in G['FACES']:np.testing.assert_allclose(bb['faces'][f]['uv'],np.array(e['faces'][f]['uv'])*64)
  self.assertEqual(base64.b64decode(b['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
 def test_14_output_hashes(self):
  self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/G['SCRIPT']).read_bytes()))
  for path,digest in self.man['output_sha256'].items():self.assertEqual(G['sha']((ROOT/path).read_bytes()),digest,path)
 def test_15_deterministic_regeneration(self):
  # In-memory generation; comparison is checked by the separate full --verify run.
  outputs=G['generate'](include_comparison=False)
  for path,data in outputs.items():
   if path!=G['ART']+'manifest.json':self.assertEqual(data,(ROOT/path).read_bytes(),path)
if __name__=='__main__':unittest.main(verbosity=2)
