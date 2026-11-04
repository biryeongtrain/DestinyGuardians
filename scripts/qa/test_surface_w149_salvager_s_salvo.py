#!/usr/bin/env python3
"""Targeted W149 Salvager's Salvo offline regression. Never starts native clients."""
import base64, copy, hashlib, io, json, math, runpy, unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_salvager_s_salvo.py'))
ART=G['ART'];MODEL=G['MODEL'];TEXTURE=G['TEXTURE']
def read(p):return json.loads((ROOT/p).read_bytes())
def contains(e,p):
 p=np.array(p,float);r=e.get('rotation')
 if r:p=(p-np.array(r['origin']))@G['H']['rotation']({r['axis']:r['angle']})+r['origin']
 return bool(np.all(p>np.array(e['from'])+1e-7) and np.all(p<np.array(e['to'])-1e-7))
class SalvagerW149(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=read(ART+'design.json');cls.m=read(MODEL);cls.man=read(ART+'manifest.json');cls.tex=Image.open(ROOT/TEXTURE).convert('RGBA')
 def test_01_full_only_budget_schema(self):
  es=self.m['elements'];self.assertTrue(80<=len(es)<=120);self.assertEqual(len(es),self.man['assembled_elements']);self.assertTrue(self.man['full_only'])
  self.assertFalse(self.man['native_accepted']);self.assertEqual(0,self.man['triangle_adapter_elements']);self.assertEqual(0,self.man['alpha_body_elements'])
  self.assertEqual(len(es),len({e['name'] for e in es}))
  for e in es:
   self.assertLessEqual(set(e),{'name','from','to','rotation','faces'})
   lo=np.array(e['from']);hi=np.array(e['to']);self.assertTrue(np.isfinite([lo,hi]).all());self.assertTrue((hi>lo).all())
   v=G['vertices'](e);self.assertTrue(np.isfinite(v).all());self.assertTrue((v> -16).all() and (v<32).all())
   self.assertEqual(set(e['faces']),set(G['FACES']))
   if 'rotation' in e:self.assertIn(e['rotation']['axis'],'xyz');self.assertTrue(math.isfinite(e['rotation']['angle']))
 def test_02_display_scale_anchor_axis(self):
  self.assertEqual(self.m['display'],read(G['BASE'])['display']);meta=read(G['SOURCE'])['destiny_w30']
  self.assertEqual(self.d['source'],meta);self.assertEqual(self.d['coordinate_policy']['scale'],meta['scale']);self.assertEqual(self.d['coordinate_policy']['anchor'],[8,8,8])
  self.assertEqual(meta['source_axis'],dict(length=1,thin=0,muzzle_sign=-1));self.assertEqual(self.d['coordinate_policy']['muzzle_axis'],'-Z')
 def test_03_source_object_transform_triangle_bounds(self):
  ms,meta=G['source_meshes']();fs,_=G['source_fbx']();self.assertEqual(sorted(m['name'] for m in ms),sorted(meta['source_objects']))
  self.assertEqual(sum(len(m['faces']) for m in ms),21314);self.assertEqual(meta['excluded_objects'],['Reticle'])
  for m in ms:
   self.assertEqual(m['object_matrix'],np.eye(4).tolist());f=next(x for x in fs if x['name']==m['name']);np.testing.assert_allclose(m['vertices'],f['vertices'],atol=1e-6,rtol=0)
 def test_04_all_provenance_hashes(self):
  for key in ('input_sha256','raw_input_sha256'):
   for p,s in self.d[key].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),s,p)
  for p,s in self.man['output_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),s,p)
  self.assertEqual(self.man['generator_sha256'],hashlib.sha256((ROOT/G['SCRIPT']).read_bytes()).hexdigest());self.assertEqual(self.man['test_sha256'],hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
  self.assertEqual(self.d['reference']['sha256'],hashlib.sha256(G['PHOTO'].read_bytes()).hexdigest())
 def test_05_texture_uv_opacity_gutters(self):
  a=np.asarray(self.tex);self.assertEqual(self.tex.size,(1024,1024));self.assertEqual(set(np.unique(a[:,:,3])),{255})
  ledger=self.d['atlas']['islands'];self.assertEqual(len(ledger),len(self.m['elements'])*6);occupied=np.zeros((1024,1024),np.uint8)
  lookup={e['name']:e for e in self.m['elements']}
  for i in ledger:
   x,y,xx,yy=i['pixels'];self.assertTrue(2<=x<xx<=1022 and 2<=y<yy<=1022)
   self.assertFalse(occupied[y-2:yy+2,x-2:xx+2].any());occupied[y-2:yy+2,x-2:xx+2]=1
   f=lookup[i['element']]['faces'][i['face']];self.assertEqual(f['texture'],'#0');self.assertEqual(f['uv'],[v/64 for v in [x,y,xx,yy]])
   np.testing.assert_array_equal(a[y:yy,x-1],a[y:yy,x]);np.testing.assert_array_equal(a[y-1,x:xx],a[y,x:xx])
 def test_06_physical_openings(self):
  for n,p in self.d['open_probes'].items():self.assertFalse(any(contains(e,p) for e in self.m['elements']),n)
  for z in np.linspace(-7.7,3.8,30):self.assertFalse(any(contains(e,[8,12.27,z]) for e in self.m['elements']),'bore')
  self.assertTrue(any(contains(e,[8,12.27,4.3]) for e in self.m['elements']))
 def test_07_filled_semantic_masses(self):
  for n,p in self.d['filled_probes'].items():self.assertTrue(any(contains(e,p) for e in self.m['elements']),n)
  core=next(e for e in self.m['elements'] if e['name']=='receiver_core');self.assertGreater(core['to'][0]-core['from'][0],1.8)
  for x in (7.45,8,8.55):self.assertTrue(contains(core,[x,12,6]))
 def test_08_ads_open_ray_and_pin(self):
  s=self.d['ads_sight'];self.assertEqual(s['eyeSide'],'+Z');self.assertEqual(s['style'],'iron');self.assertEqual(s['plane'],'XY')
  c=s['sightCenter'];self.assertEqual(s['forwardPoint'],[c[0],c[1],c[2]-2])
  for z in np.linspace(-10,20,601):self.assertFalse(any(contains(e,[c[0],c[1],z]) for e in self.m['elements']),f'blocked sight ray {z}')
  pin=next(e for e in self.m['elements'] if e['name']=='sight_pin');self.assertAlmostEqual(c[1]-pin['to'][1],.08);self.assertLess(pin['from'][0],c[0]);self.assertGreater(pin['to'][0],c[0])
 def test_09_feature_identity_proportions(self):
  names={e['name']:e for e in self.m['elements']};self.assertEqual(len([n for n in names if n.startswith('barrel_shell_')]),8)
  self.assertEqual(len([n for n in names if n.startswith('braced_panel_')]),2)
  self.assertGreater(names['ladder_side_1']['to'][1]-names['ladder_side_1']['from'][1],2.8)
  self.assertAlmostEqual(names['muzzle_lip_0']['from'][2],self.d['source']['model_bounds'][0][2],places=6)
  self.assertAlmostEqual(names['butt_pad']['to'][2],self.d['source']['model_bounds'][1][2],places=6)
  self.assertEqual(self.d['coordinate_policy']['grip_top'],[8,10.86,6.93]);self.assertEqual(self.d['coordinate_policy']['grip_heel'],[8,6.89,9.17])
  pts=np.concatenate([G['vertices'](e) for e in self.m['elements']]);self.assertAlmostEqual(pts[:,1].min(),self.d['source']['model_bounds'][0][1],delta=.08)
  self.assertLessEqual(pts[:,0].min(),6.3);self.assertGreaterEqual(pts[:,0].max(),9.1)
  self.assertGreater(names['front_strap']['to'][2]-names['front_strap']['from'][2],3.5)
  self.assertIn('sage',self.d['palette']);self.assertIn('wood',self.d['palette']);self.assertIn('wrap',self.d['palette'])
 def test_10_inspection_exact_geometry_and_atlas(self):
  bb=read(ART+'inspection.bbmodel');self.assertEqual(bb['display'],self.m['display']);self.assertEqual(len(bb['elements']),len(self.m['elements']))
  tex=base64.b64decode(bb['textures'][0]['source'].split(',')[1]);self.assertEqual(tex,(ROOT/TEXTURE).read_bytes())
  lookup={e['name']:e for e in bb['elements']}
  for e in self.m['elements']:
   b=lookup[e['name']];self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
   for f,v in e['faces'].items():self.assertEqual(b['faces'][f]['uv'],[n*64 for n in v['uv']])
   if 'rotation' in e:self.assertEqual(b['rotation']['xyz'.index(e['rotation']['axis'])],e['rotation']['angle'])
 def test_11_owned_ten_paths(self):
  f=next(f for f in read(G['BATCH'])['features'] if f['name']=='w149-salvager_s_salvo');self.assertEqual(len(f['owned_paths']),10)
  self.assertTrue(all((ROOT/p).is_file() for p in f['owned_paths']));self.assertEqual(set(f['owned_paths']),set(self.man['output_sha256'])|{ART+'manifest.json',G['SCRIPT'],G['TEST'],G['REPORT']})
 def test_12_deterministic_regeneration(self):
  a=G['generate'](include_comparison=False);b=G['generate'](include_comparison=False);self.assertEqual(a,b)
  for p,v in a.items():
   if not p.endswith('manifest.json'):self.assertEqual(v,(ROOT/p).read_bytes(),p)
 def test_13_comparison_is_modest_actual_evidence(self):
  with Image.open(ROOT/(ART+'comparison.png')) as im:self.assertEqual(im.size,(2160,1510))
  self.assertLess((ROOT/(ART+'comparison.png')).stat().st_size,2_000_000)
if __name__=='__main__':unittest.main(verbosity=2)
