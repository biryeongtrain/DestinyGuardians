#!/usr/bin/env python3
"""Practical W150 Stormchaser art regressions. Offline only, no full/native gate."""
import base64, copy, hashlib, io, json, runpy, unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_stormchaser.py'))
def read(p):return json.loads((ROOT/p).read_bytes())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inside(point,e,margin=1e-6):
 p=np.array(point,float)
 if 'rotation' in e:
  r=e['rotation'];o=np.array(r['origin']);p=(p-o)@G['H']['rotation']({r['axis']:r['angle']})+o
 return np.all(p>np.array(e['from'])+margin) and np.all(p<np.array(e['to'])-margin)

class Stormchaser(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=read(G['ART']+'design.json');cls.m=read(G['MODEL']);cls.man=read(G['ART']+'manifest.json');cls.bb=read(G['ART']+'inspection.bbmodel');cls.tex=Image.open(ROOT/G['TEXTURE']).convert('RGBA')
 def test_01_budget_and_full_only(self):
  self.assertEqual(len(self.m['elements']),self.man['assembled_elements']);self.assertLessEqual(len(self.m['elements']),1000);self.assertGreaterEqual(len(self.m['elements']),80)
  self.assertTrue(self.man['full_only']);self.assertEqual(self.man['triangle_adapter_elements'],0);self.assertEqual(self.man['alpha_body_elements'],0)
  owned=next(f['owned_paths'] for f in read('docs/qa/2026-10-26/w150/batch.json')['features'] if f['name']=='w150-stormchaser')
  self.assertEqual(len(owned),10);self.assertTrue(all((ROOT/p).is_file() for p in owned))
 def test_02_parse_closed_supported_solids(self):
  names=[]
  for e in self.m['elements']:
   names.append(e['name']);self.assertEqual(set(e['faces']),set(G['FACES']));self.assertNotIn('vertices',e);self.assertNotIn('triangles',e)
   self.assertTrue(np.all(np.array(e['to'])-e['from']>=.04));self.assertTrue(np.isfinite(G['vertices'](e)).all())
   if 'rotation' in e:self.assertIn(e['rotation']['axis'],'xyz');self.assertTrue(np.isfinite(e['rotation']['angle']))
  self.assertEqual(len(names),len(set(names)))
 def test_03_independent_opaque_face_uv(self):
  self.assertEqual(self.tex.size,(1024,1024));self.assertEqual(self.tex.getchannel('A').getextrema(),(255,255))
  islands=self.d['atlas']['islands'];self.assertEqual(len(islands),len(self.m['elements'])*6);used=np.zeros((1024,1024),bool);rects=[]
  byname={e['name']:e for e in self.m['elements']}
  for a in islands:
   x0,y0,x1,y1=a['rect'];self.assertTrue(2<=x0<x1<=1022 and 2<=y0<y1<=1022)
   self.assertFalse(used[y0-2:y1+2,x0-2:x1+2].any());used[y0-2:y1+2,x0-2:x1+2]=True
   self.assertEqual(byname[a['element']]['faces'][a['face']]['uv'],[v*16/1024 for v in a['rect']]);rects.append(tuple(a['rect']))
  self.assertEqual(len(set(rects)),len(rects));self.assertEqual(self.man['face_uv_islands'],len(islands))
 def test_04_real_openings_across_width(self):
  for name,p in self.d['openings'].items():
   # Multiple interior points, not just a single empty center.
   offsets=[-.12,0,.12] if name!='bore' else [-.10,0,.10]
   for dx in offsets:
    q=np.array(p)+[dx,0,0]
    self.assertFalse(any(inside(q,e) for e in self.m['elements']),(name,q.tolist()))
 def test_05_bore_depth_and_surrounding_walls(self):
  es=self.m['elements'];walls=[e for e in es if e['name'].startswith('bore_wall_')];self.assertEqual(len(walls),8)
  for z in np.linspace(-6.9,-5.96,14):
   self.assertFalse(any(inside([8,10.55,z],e) for e in es),z)
  for i in range(8):
   a=i*np.pi/4;p=[8+.36*np.sin(a),10.55+.36*np.cos(a),-6.43]
   self.assertTrue(any(inside(p,e) for e in walls))
  self.assertTrue(any(inside([8,10.55,-5.83],e) for e in es))
 def test_06_ads_ray_and_pin(self):
  s=self.d['ads_sight'];self.assertEqual(s['style'],'optic');self.assertEqual(s['eyeSide'],'+Z');self.assertEqual(s['plane'],'XY')
  c=np.array(s['sightCenter']);np.testing.assert_allclose(s['forwardPoint'],c+[0,0,-2],atol=1e-12)
  for z in np.linspace(-12,16,180):
   for dx,dy in [(0,0),(-.09,0),(.09,0),(0,-.08),(0,.08)]:
    self.assertFalse(any(inside([c[0]+dx,c[1]+dy,z],e) for e in self.m['elements']),(z,dx,dy))
  pin=next(e for e in self.m['elements'] if e['name']=='optic_center_pin');self.assertLess(pin['to'][1],c[1]);self.assertLess(c[1]-pin['to'][1],.25);self.assertEqual((pin['from'][0]+pin['to'][0])/2,c[0])
 def test_07_substantial_body_probes(self):
  for n,p in self.d['filled_probes'].items():self.assertTrue(any(inside(p,e) for e in self.m['elements']),n)
  for group in ('upper','body','grip','stock','receiver'):
   ps=[p for p in self.d['parts'] if p['group']==group]
   self.assertTrue(any(np.prod(np.array(p['geometry']['to'])-p['geometry']['from'])>.4 for p in ps),group)
 def test_08_original_display_frame_bounds(self):
  old=read(G['BASE']);meta=read(G['SOURCE'])['destiny_w30'];self.assertEqual(old['display'],self.m['display']);self.assertEqual(meta,self.d['source'])
  self.assertEqual(self.man['source_scale'],meta['scale']);self.assertEqual(self.man['source_anchor'],[8,8,8]);self.assertEqual(self.d['muzzle_axis'],'-Z')
  ps=np.concatenate([G['vertices'](e) for e in self.m['elements']]);bounds=np.array([ps.min(0),ps.max(0)])
  np.testing.assert_allclose(bounds,self.man['actual_bounds'],atol=1e-8);np.testing.assert_allclose(bounds,meta['model_bounds'],atol=.23,rtol=0)
  self.assertLess(next(e for e in self.m['elements'] if e['name']=='forward_keel_0')['from'][2],-11.4)
 def test_09_exact_source_hashes_and_inert_read(self):
  for p,h in self.d['input_sha256'].items():self.assertEqual(digest(ROOT/p),h,p)
  for p,h in self.d['raw_input_sha256'].items():self.assertEqual(digest(p),h,p)
  ms,meta,audit=G['source_meshes']();self.assertEqual(sum(len(m['faces']) for m in ms),29718)
  self.assertEqual(sum(a['triangles'] for a in audit if a['status']=='excluded'),546);self.assertEqual(audit,self.d['source_matching']['inventory'])
  self.assertEqual(meta['source_axis']['muzzle_sign'],-1)
 def test_10_bb_geometry_uv_texture_parity(self):
  self.assertEqual(len(self.bb['elements']),len(self.m['elements']));self.assertEqual(self.bb['display'],self.m['display'])
  embedded=base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]);self.assertEqual(embedded,(ROOT/G['TEXTURE']).read_bytes())
  self.assertEqual(len({e['uuid'] for e in self.bb['elements']}),len(self.m['elements']))
  children=[u for g in self.bb['outliner'] for u in g['children']];self.assertEqual(set(children),{e['uuid'] for e in self.bb['elements']});self.assertEqual(len(children),len(self.m['elements']))
  for e,b in zip(self.m['elements'],self.bb['elements']):
   self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to']);self.assertEqual(e['name'],b['name'])
   r=e.get('rotation');self.assertEqual(b['rotation'],[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'])
   for f in G['FACES']:self.assertEqual(b['faces'][f]['uv'],[v*64 for v in e['faces'][f]['uv']]);self.assertEqual(b['faces'][f]['texture'],0)
 def test_11_output_hashes_and_reference_evidence(self):
  for p,h in self.man['output_sha256'].items():self.assertEqual(digest(ROOT/p),h,p)
  self.assertEqual(digest(ROOT/G['SCRIPT']),self.man['generator_sha256']);self.assertEqual(digest(__file__),self.man['test_sha256'])
  im=Image.open(ROOT/(G['ART']+'comparison.png')).copy();self.assertEqual(im.size,(3000,2100));self.assertEqual(len(self.d['comparison_views']),3)
  self.assertEqual(self.man['native_accepted'],False);self.assertTrue(self.man['existing_ADS_scope_reload_timing_audio_unchanged'])
 def test_12_regeneration_exact_seven_outputs(self):
  outputs=G['generate']();self.assertEqual(len(outputs),7)
  for p,b in outputs.items():self.assertEqual(b,(ROOT/p).read_bytes(),p)

if __name__=='__main__':unittest.main(verbosity=2)
