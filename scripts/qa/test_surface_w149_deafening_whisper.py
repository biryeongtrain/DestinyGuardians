#!/usr/bin/env python3
"""Targeted W149 offline product tests; no native/DCC/world fixture side effects."""
import base64,copy,hashlib,io,json,math,runpy,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_deafening_whisper.py'))
def read(p):return json.loads((ROOT/p).read_bytes())
def inside(e,p):
 p=np.array(p,float);r=e.get('rotation')
 if r:
  o=np.array(r['origin']);p=(p-o)@G['H']['rotation']({r['axis']:r['angle']})+o
 return bool(np.all(p>=np.array(e['from'])-1e-7) and np.all(p<=np.array(e['to'])+1e-7))
class DeafeningWhisper(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=read(G['ART']+'design.json');cls.m=read(G['MODEL']);cls.man=read(G['ART']+'manifest.json');cls.es=cls.m['elements'];cls.by={e['name']:e for e in cls.es};cls.atlas=np.asarray(Image.open(ROOT/G['TEXTURE']).convert('RGBA'));cls.bb=read(G['ART']+'inspection.bbmodel')
 def test_01_exact_ten_scope(self):
  f=next(f for f in read(G['BATCH'])['features'] if f['name']=='w149-deafening_whisper')
  self.assertEqual(set(f['owned_paths']),set(G['OWNED']));self.assertEqual(len(f['owned_paths']),10)
  for p in f['owned_paths']:self.assertTrue((ROOT/p).is_file(),p)
  self.assertIn('full only',self.d['coordinate_policy']['export']);self.assertTrue(self.man['full_only'])
 def test_02_native_cube_schema_budget_finite(self):
  self.assertEqual(len(self.es),88);self.assertLessEqual(len(self.es),1000);self.assertEqual(self.man['triangle_adapter_elements'],0)
  for e in self.es:
   self.assertLessEqual(set(e),{'name','from','to','rotation','faces'});self.assertEqual(set(e['faces']),set(G['FACES']))
   b=np.array([e['from'],e['to']]);self.assertTrue(np.isfinite(b).all());self.assertTrue((b[1]>b[0]).all())
   self.assertTrue((b>-32).all() and (b<48).all())
   if 'rotation' in e:
    r=e['rotation'];self.assertEqual(set(r),{'origin','axis','angle'});self.assertIn(r['axis'],'xyz');self.assertTrue(np.isfinite(r['origin']+[r['angle']]).all())
 def test_03_opaque_proportional_uv_and_gutters(self):
  self.assertEqual(self.atlas.shape,(1024,1024,4));self.assertTrue((self.atlas[:,:,3]==255).all());seen=set()
  for isle in self.d['atlas']['islands']:
   name,face=isle['element'],isle['face'];x0,y0,x1,y1=isle['pixels'];uv=self.by[name]['faces'][face]['uv'];seen.add((name,face))
   self.assertTrue(np.isfinite(uv).all());np.testing.assert_allclose(np.array(uv)*64,[x0,y0,x1,y1],atol=1e-9)
   self.assertGreater(x1,x0);self.assertGreater(y1,y0);self.assertGreaterEqual(min(x0,y0),2);self.assertLessEqual(max(x1,y1),1022)
   self.assertEqual(self.by[name]['faces'][face]['texture'],'#0')
   np.testing.assert_array_equal(self.atlas[y0:y1,x0-2:x0],np.repeat(self.atlas[y0:y1,x0:x0+1],2,axis=1))
   np.testing.assert_array_equal(self.atlas[y0-2:y0,x0:x1],np.repeat(self.atlas[y0:y0+1,x0:x1],2,axis=0))
  self.assertEqual(len(seen),len(self.es)*6);self.assertEqual(self.man['atlas_face_islands'],528)
 def test_04_real_bore_and_solid_breech(self):
  for z in np.linspace(-9.30,8.80,45):
   for x,y in [(8,12.94),(7.6,12.94),(8.4,12.94),(8,12.54),(8,13.34)]:
    self.assertFalse(any(inside(e,[x,y,z]) for e in self.es),(x,y,z))
  self.assertTrue(any(inside(e,[8,12.94,9.5]) for e in self.es))
  for p in ([8,14.33,-5],[8,11.55,-5],[6.61,12.94,-5],[9.39,12.94,-5]):self.assertTrue(any(inside(e,p) for e in self.es),p)
 def test_05_stock_air_and_solid_handholds(self):
  for p in ([8,12,12],[8,10,12],[8,12,13.5]):self.assertFalse(any(inside(e,p) for e in self.es),p)
  for p in ([8,9.69,-3.04],[8,9.3,7.6]):self.assertTrue(any(inside(e,p) for e in self.es),p)
  self.assertFalse(any(inside(e,[8,10.0,4.8]) for e in self.es))
 def test_06_sight_ray_aperture_and_pin(self):
  a=self.d['ads_sight'];self.assertEqual(a['eyeSide'],'+Z');self.assertEqual(a['plane'],'XY');self.assertEqual(a['style'],'optic')
  np.testing.assert_allclose(np.subtract(a['forwardPoint'],a['sightCenter']),[0,0,-2])
  for z in np.linspace(18,-12,601):
   self.assertFalse(any(inside(e,[8,15.86,z]) for e in self.es),z)
  for x in (7.75,8.0,8.25):
   for y in (15.88,16.4,17.1):self.assertFalse(any(inside(e,[x,y,-1.416]) for e in self.es),(x,y))
  pin=self.by['sight_pin_tip'];self.assertLess(pin['to'][1],a['sightCenter'][1]);self.assertLess(a['sightCenter'][1]-pin['to'][1],.04)
  self.assertTrue(inside(pin,[8,15.8,-1.416]));self.assertTrue(inside(self.by['sight_upright_1'],[8.49,16.5,-1.416]))
 def test_07_display_source_frame_and_endpoints(self):
  base=read(G['BASE']);meta=read(G['SOURCE'])['destiny_w30'];self.assertEqual(self.m['display'],base['display']);self.assertEqual(self.bb['display'],base['display'])
  c=self.d['coordinate_policy'];self.assertEqual(c['anchor'],meta['anchor']);self.assertEqual(c['scale'],meta['scale']);self.assertEqual(c['source_axis'],meta['source_axis'])
  self.assertEqual(c['grip_top'],[8,11.14,6.67]);self.assertEqual(c['grip_heel'],[8,7.57,8.55])
  pts=np.concatenate([G['vertices'](e) for e in self.es]);bounds=np.array([pts.min(0),pts.max(0)])
  np.testing.assert_allclose(bounds,self.man['actual_bounds'],atol=1e-8);self.assertLess(np.abs(bounds-np.array(meta['model_bounds'])).max(),.10)
 def test_08_source_objects_matrices_bounds_and_exclusions(self):
  ms,meta=G['source_meshes']();self.assertEqual(sorted(m['name'] for m in ms),sorted(meta['source_objects']));self.assertEqual(sum(len(m['faces']) for m in ms),30564)
  self.assertFalse(set(m['name'] for m in ms)&set(meta['excluded_objects']));self.assertEqual(self.d['source_matching']['excluded_preserved'],meta['excluded_objects'])
  self.assertEqual(len(self.d['source_matching']['object_transforms']),11)
  for m in ms:np.testing.assert_array_equal(m['object_matrix'],self.d['source_matching']['object_transforms'][m['name']])
 def test_09_all_source_photo_hashes(self):
  for p,h in self.d['input_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
  for p,h in self.d['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(p).read_bytes()),h,p)
  self.assertEqual(self.d['reference']['sha256'],G['sha'](G['PHOTO'].read_bytes()));self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/G['SCRIPT']).read_bytes()))
 def test_10_inspection_geometry_uv_texture_parity(self):
  self.assertEqual(len(self.bb['elements']),len(self.es));by={e['name']:e for e in self.bb['elements']}
  for e in self.es:
   b=by[e['name']];self.assertEqual(b['type'],'cube');self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
   expected=[0,0,0]
   if 'rotation' in e:expected['xyz'.index(e['rotation']['axis'])]=e['rotation']['angle'];self.assertEqual(b['origin'],e['rotation']['origin'])
   self.assertEqual(b['rotation'],expected)
   for face in e['faces']:np.testing.assert_allclose(b['faces'][face]['uv'],np.array(e['faces'][face]['uv'])*64)
  embedded=base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]);self.assertEqual(embedded,(ROOT/G['TEXTURE']).read_bytes())
  children=[u for g in self.bb['outliner'] for u in g['children']];self.assertEqual(set(children),set(b['uuid'] for b in by.values()))
 def test_11_identity_materials_and_continuous_volumes(self):
  for group in ('barrel','wrap','counter','foregrip','grip','stock','underbarrel','sight'):self.assertGreater(self.man['groups'][group],0)
  self.assertEqual(len([e for e in self.es if e['name'].startswith('barrel_')]),8)
  for i in range(8):self.assertGreater(self.by['barrel_'+str(i)]['to'][2]-self.by['barrel_'+str(i)]['from'][2],19)
  motifs={s['motif'] for s in self.d['parts']};self.assertTrue({'weave','silver_tube','counter','grip','red'}<=motifs)
  self.assertGreater(np.linalg.norm(np.array(self.d['palette']['silver'])-self.d['palette']['black']),180)
  self.assertEqual(self.man['groups']['wrap'],27)
 def test_12_output_hashes_and_no_native_claim(self):
  for p,h in self.man['output_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
  self.assertFalse(self.man['native_accepted']);self.assertTrue(self.man['generic_reload_unchanged']);self.assertEqual(self.man['assembled_elements'],len(self.es))
  with Image.open(ROOT/(G['ART']+'comparison.png')) as im:self.assertEqual(im.size,(2160,1530))
 def test_13_deterministic_regeneration(self):
  first=G['generate'](include_comparison=False);second=G['generate'](include_comparison=False);self.assertEqual(first,second)
  for p,v in first.items():
   if not p.endswith('manifest.json'):self.assertEqual((ROOT/p).read_bytes(),v,p)
  expected=json.loads(first[G['ART']+'manifest.json']);actual=copy.deepcopy(self.man);actual['output_sha256'].pop(G['ART']+'comparison.png');self.assertEqual(actual,expected)
if __name__=='__main__':unittest.main(verbosity=2)
