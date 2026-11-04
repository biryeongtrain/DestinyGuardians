#!/usr/bin/env python3
"""Targeted W150 Pyroclastic Flow offline regression. Never starts native clients."""
import base64, copy, hashlib, io, json, math, runpy, unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_pyroclastic_flow.py'))
ART=G['ART'];MODEL=G['MODEL'];TEXTURE=G['TEXTURE']
def read(p):return json.loads((ROOT/p).read_bytes())
def contains(e,p):
 p=np.array(p,float);r=e.get('rotation')
 if r:p=(p-np.array(r['origin']))@G['H']['rotation']({r['axis']:r['angle']})+r['origin']
 return bool(np.all(p>np.array(e['from'])+1e-7) and np.all(p<np.array(e['to'])-1e-7))
class PyroclasticW150(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=read(ART+'design.json');cls.m=read(MODEL);cls.man=read(ART+'manifest.json');cls.tex=Image.open(ROOT/TEXTURE).convert('RGBA')
 def test_01_full_only_budget_schema(self):
  es=self.m['elements'];self.assertTrue(1<=len(es)<=1000);self.assertEqual(len(es),self.man['assembled_elements']);self.assertTrue(self.man['full_only'])
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
  self.assertEqual(meta['source_axis'],dict(length=1,thin=0,muzzle_sign=1));self.assertEqual(self.d['coordinate_policy']['muzzle_axis'],'-Z')
 def test_03_source_object_transform_triangle_bounds(self):
  ms,meta=G['source_meshes']();fs,_=G['source_fbx']();self.assertEqual(sorted(m['name'] for m in ms),sorted(meta['source_objects']))
  self.assertEqual(sum(len(m['faces']) for m in ms),28675);self.assertEqual(meta['excluded_objects'],['Reticle','Reticle Back'])
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
  # Practical finite bore + carry + stock aperture areas, beyond isolated point probes.
  for z in (-7.6,-4.0,0,4.8):
   for dx,dy in [(0,0),(.32,0),(-.32,0),(0,.32),(0,-.32)]:
    self.assertFalse(any(contains(e,[8+dx,11.9+dy,z]) for e in self.m['elements']),'bore')
  self.assertTrue(any(contains(e,[8,11.9,5.32]) for e in self.m['elements']))
  for center in ([8,11.84,17.5],[8,8.7,8.7],[8,8.9,11.5]):
   for dx in (-1.0,0,1.0):self.assertFalse(any(contains(e,[center[0]+dx,*center[1:]]) for e in self.m['elements']))
 def test_07_filled_semantic_masses(self):
  for n,p in self.d['filled_probes'].items():self.assertTrue(any(contains(e,p) for e in self.m['elements']),n)
  core=next(e for e in self.m['elements'] if e['name']=='receiver_core');self.assertGreater(core['to'][0]-core['from'][0],2.0)
  for x in (7.1,8,8.9):self.assertTrue(contains(core,[x,11.6,12]))
  for side in (-1,1):
   armor=next(e for e in self.m['elements'] if e['name']==f'legion_armor_{side}')
   self.assertGreater(armor['to'][0]-armor['from'][0],.5)
 def test_08_ads_open_ray_and_pin(self):
  s=self.d['ads_sight'];self.assertEqual(s['eyeSide'],'+Z');self.assertEqual(s['style'],'optic');self.assertEqual(s['plane'],'XY')
  c=s['sightCenter'];self.assertEqual(s['forwardPoint'],[c[0],c[1],c[2]-2])
  # Analytic slab intersection over full ray, including oblique closed solids.
  for e in self.m['elements']:
   o=np.array(c,float);v=np.array([0.,0.,-1.]);r=e.get('rotation')
   if r:
    rot=G['H']['rotation']({r['axis']:r['angle']});o=(o-r['origin'])@rot+r['origin'];v=v@rot
   lower,upper=-100.,100.
   for k in range(3):
    lo,hi=e['from'][k]+1e-7,e['to'][k]-1e-7
    if abs(v[k])<1e-10:
     if o[k]<=lo or o[k]>=hi:lower,upper=1,0;break
    else:
     a,b=sorted(((lo-o[k])/v[k],(hi-o[k])/v[k]));lower=max(lower,a);upper=min(upper,b)
   self.assertGreaterEqual(lower,upper,'blocked sight ray: '+e['name'])
  pin=next(e for e in self.m['elements'] if e['name']=='optic_pin_tip');self.assertAlmostEqual(c[1]-pin['to'][1],.0675)
  self.assertLess(pin['from'][0],c[0]);self.assertGreater(pin['to'][0],c[0]);self.assertEqual(s['pinTop'],[c[0],pin['to'][1],8.71])
 def test_09_feature_identity_proportions(self):
  names={e['name']:e for e in self.m['elements']};self.assertEqual(len([n for n in names if n.startswith('launch_tube_')]),8)
  self.assertEqual(len([n for n in names if n.startswith('optic_housing_')]),8)
  self.assertAlmostEqual(names['muzzle_crown_0']['from'][2],self.d['source']['model_bounds'][0][2],places=6)
  self.assertEqual(self.d['coordinate_policy']['grip_root'],[8,9.08,13.02]);self.assertEqual(self.d['coordinate_policy']['grip_heel'],[8,6.25,16.09])
  pts=np.concatenate([G['vertices'](e) for e in self.m['elements']]);actual=np.array([pts.min(0),pts.max(0)]);source=np.array(self.d['source']['model_bounds'])
  np.testing.assert_allclose(actual,source,atol=.35,rtol=0)
  for f in ('east','west'):self.assertGreater(len(self.d['logo_silhouettes'][f]),5)
  # Red Legion dye must be present on face paint; no geometry decal card.
  rgb=np.asarray(self.tex)[:,:,:3];red=(rgb[:,:,0]>75)&(rgb[:,:,0]>rgb[:,:,1]*2)&(rgb[:,:,0]>rgb[:,:,2]*1.8)
  self.assertGreater(int(red.sum()),120)
  for mat in ('purple','gold','black','red'):self.assertIn(mat,self.d['palette'])
 def test_10_inspection_exact_geometry_and_atlas(self):
  bb=read(ART+'inspection.bbmodel');self.assertEqual(bb['display'],self.m['display']);self.assertEqual(len(bb['elements']),len(self.m['elements']))
  tex=base64.b64decode(bb['textures'][0]['source'].split(',')[1]);self.assertEqual(tex,(ROOT/TEXTURE).read_bytes())
  lookup={e['name']:e for e in bb['elements']}
  for e in self.m['elements']:
   b=lookup[e['name']];self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
   for f,v in e['faces'].items():self.assertEqual(b['faces'][f]['uv'],[n*64 for n in v['uv']])
   if 'rotation' in e:self.assertEqual(b['rotation']['xyz'.index(e['rotation']['axis'])],e['rotation']['angle'])
 def test_11_owned_ten_paths(self):
  f=next(f for f in read(G['BATCH'])['features'] if f['name']=='w150-pyroclastic_flow');self.assertEqual(len(f['owned_paths']),10)
  self.assertTrue(all((ROOT/p).is_file() for p in f['owned_paths']));self.assertEqual(set(f['owned_paths']),set(self.man['output_sha256'])|{ART+'manifest.json',G['SCRIPT'],G['TEST'],G['REPORT']})
 def test_12_deterministic_regeneration(self):
  a=G['generate'](include_comparison=False)
  for p,v in a.items():
   if not p.endswith('manifest.json'):self.assertEqual(v,(ROOT/p).read_bytes(),p)
 def test_13_comparison_is_modest_actual_evidence(self):
  with Image.open(ROOT/(ART+'comparison.png')) as im:self.assertEqual(im.size,(2220,1650))
  self.assertLess((ROOT/(ART+'comparison.png')).stat().st_size,2_000_000)
if __name__=='__main__':unittest.main(verbosity=2)
