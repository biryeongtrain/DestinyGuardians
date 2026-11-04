#!/usr/bin/env python3
"""Offline regressions for the W144 full-only Null Composure candidate."""
import base64, io, json, runpy, unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_null_composure.py'))
def read(p):return json.loads((ROOT/p).read_bytes())
def inside(p,e):
 r=e.get('rotation',{'origin':[8,8,8]});o=np.array(r['origin']);q=(np.array(p)-o)@G['H']['rotation'](r)+o
 return bool(np.all(q>np.array(e['from'])+1e-5) and np.all(q<np.array(e['to'])-1e-5))
class NullComposureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=read(G['MODEL']);cls.d=read(G['ART']+'design.json');cls.man=read(G['ART']+'manifest.json');cls.bb=read(G['ART']+'inspection.bbmodel');cls.es=cls.m['elements']
 def test_native_schema_full_only(self):
  self.assertEqual(set(self.m),{'credit','textures','elements','display'})
  self.assertEqual(self.m['textures'],dict.fromkeys(('0','particle'),'destiny:item/weapon/w123/null_composure'))
  self.assertTrue(self.man['full_only']);self.assertFalse(self.man['native_accepted'])
  self.assertEqual(self.man['model'],'destiny:weapon_surface_w123/null_composure')
  for e in self.es:
   self.assertEqual(set(e),{'name','from','to','rotation','faces'})
   self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
   self.assertEqual(set(e['faces']),set(G['FACES']))
   self.assertTrue(np.all(np.array(e['to'])>e['from']))
   self.assertTrue(np.isfinite(G['vertices'](e)).all())
 def test_emitted_budget_semantic_volumes(self):
  n=len(self.es);self.assertLessEqual(n,1000);self.assertLessEqual(n,120);self.assertGreaterEqual(n,80)
  self.assertEqual(self.man['counts'],dict(full=n,cubes=n,triangle_adapter_elements=0,assembled_emitted=n,faces=6*n))
  self.assertEqual(n,len(self.d['parts']));self.assertEqual(n,len(self.bb['elements']))
  self.assertEqual(n,sum(self.d['groups'].values()));self.assertEqual(n,len({e['name'] for e in self.es}))
  self.assertTrue(all(s['kind']=='filled_solid' for s in self.d['parts']))
  lookup={e['name']:e for e in self.es}
  for name in ('Battery_keel_solid','Grip_main','Underbarrel_core','Shroud_vault'):
   self.assertGreater(lookup[name]['to'][0]-lookup[name]['from'][0],1.2)
  self.assertTrue({'receiver','capacitor','forearm','frame','breech','stock','grip','guard','muzzle','sight'}<=set(self.d['groups']))
 def test_source_counts_frame_and_all_objects(self):
  ms,meta,ref=G['source_meshes']()
  self.assertEqual(sum(len(m['faces']) for m in ms),15171)
  self.assertEqual(sum(len(m['uv']) for m in ms),15171)
  self.assertTrue(all(len(m['faces'])>0 for m in ms))
  self.assertEqual(meta['raw_fbx_triangles'],15415)
  self.assertEqual(meta['retained_textured_triangles'],15171)
  self.assertEqual(meta['excluded_reticle_triangles'],244)
  self.assertEqual([(o['name'],o['status'],o['triangles']) for o in meta['object_audit']],
   [('Null-Composure.00.000','retained',1746),('Null-Composure.00.001','retained',13425),('Null-Composure.01.000','excluded_reticle',244)])
  for o in meta['object_audit']:self.assertAlmostEqual(o['blend_matrix'][3][1],-.08916319906711578)
  self.assertEqual(ref,self.d['reference'])
  source=read(G['SOURCE'])['destiny_w30'];ps=np.concatenate([m['vertices'] for m in ms])
  np.testing.assert_allclose([ps.min(0),ps.max(0)],source['model_bounds'],atol=5e-6,rtol=0)
  self.assertEqual(self.man['source_triangle_accounting'],dict(raw=15415,retained=15171,textured=15171,excluded_reticle=244))
 def test_reference_immutable_inputs_and_outputs(self):
  self.assertEqual(self.d['reference']['sha256'],'48a6fc624ae06d766947dcbae4568e78412b6284947031d580097787799754ad')
  self.assertEqual(self.d['reference']['bungie_hash'],'1644680957')
  self.assertEqual(G['sha'](G['PHOTO'].read_bytes()),self.d['reference']['sha256'])
  self.assertFalse(any('migration' in p for p in self.d['input_sha256']))
  for p,pin in self.d['input_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),pin,p)
  for p,pin in self.d['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(p).read_bytes()),pin,p)
  self.assertGreater(len(self.d['raw_input_sha256']),20)
  for p,pin in self.man['outputs'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),pin,p)
 def test_opaque_unique_face_uv_and_gutters(self):
  with Image.open(ROOT/G['TEXTURE']) as im:
   self.assertEqual(im.size,(1024,1024));self.assertEqual(im.mode,'RGBA');self.assertEqual(im.getchannel('A').getextrema(),(255,255))
  occ=np.zeros((1024,1024),bool);lookup={e['name']:e for e in self.es};ledger=self.d['atlas']['islands']
  self.assertEqual(len(ledger),6*len(self.es))
  for q in ledger:
   x0,y0,x1,y1=q['pixels'];self.assertTrue(2<=x0<x1<=1022 and 2<=y0<y1<=1022)
   region=occ[y0-2:y1+2,x0-2:x1+2];self.assertFalse(region.any(),(q['element'],q['face']));region[:]=True
   face=lookup[q['element']]['faces'][q['face']];self.assertEqual(face['texture'],'#0');self.assertEqual(face['uv'],[v/64 for v in q['pixels']])
  for name in ('Battery_keel_solid','Shroud_rear_cheek_-1'):
   self.assertNotEqual(lookup[name]['faces']['east']['uv'],lookup[name]['faces']['west']['uv'])
 def test_source_scale_display_and_grip_contact(self):
  source=read(G['SOURCE'])['destiny_w30'];old=read(G['BASE'])
  self.assertEqual(self.d['anchor'],source['anchor']);self.assertEqual(self.d['scale'],source['scale']);self.assertEqual(self.m['display'],old['display'])
  for name,p in self.d['contact_probes'].items():self.assertTrue(any(inside(p,e) for e in self.es),name)
  self.assertTrue(any(inside(self.d['contact_probes']['grip'],e) for e in old['elements']))
  for p in ([8,10.40,4.78],[8,10.33,4.78],[8,10.20,4.78],[8,9.95,4.78],[8,7.10,6.02]):self.assertTrue(any(inside(p,e) for e in self.es),str(p))
  ps=np.concatenate([G['vertices'](e) for e in self.es]);bounds=np.array([ps.min(0),ps.max(0)])
  self.assertTrue(np.all(np.abs(bounds-np.array(source['model_bounds']))<.16))
 def test_real_openings_and_dark_recessed_bore(self):
  for name,p in self.d['required_air_probes'].items():self.assertFalse(any(inside(p,e) for e in self.es),name)
  for x in (6.7,7.4,8,8.6,9.3):
   self.assertFalse(any(inside([x,7.8,3.1],e) for e in self.es),'through grip frame')
  for z in (-13.02,-12.84,-12.65):self.assertFalse(any(inside([8,11.78,z],e) for e in self.es),'bore channel')
  back=[s for s in self.d['parts'] if inside([8,11.78,-12.30],s['geometry'])]
  self.assertTrue(back);self.assertTrue(all(s['material']=='recess' for s in back))
  for z in (-.10,.30,.70,1.0):self.assertFalse(any(inside([8,14.40,z],e) for e in self.es),'through open reflex')
 def test_editable_inspection_complete_and_views_unclipped(self):
  self.assertEqual(self.bb['display'],self.m['display']);self.assertEqual(self.bb['resolution'],dict(width=1024,height=1024))
  self.assertEqual(base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]),(ROOT/G['TEXTURE']).read_bytes())
  for b,e in zip(self.bb['elements'],self.es):
   self.assertEqual(b['type'],'cube');self.assertEqual(b['name'],e['name']);self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
   self.assertEqual(b['rotation'],[e['rotation'][a] for a in 'xyz'])
   for f in G['FACES']:self.assertEqual(b['faces'][f]['uv'],[v*64 for v in e['faces'][f]['uv']])
  self.assertEqual({u for g in self.bb['outliner'] for u in g['children']},{e['uuid'] for e in self.bb['elements']})
  ps=np.concatenate([G['vertices'](e) for e in self.es]);self.assertEqual(len(self.d['comparison_views']),3)
  for view in self.d['comparison_views']:
   cam=np.array(view['camera'],float);cam/=np.linalg.norm(cam);right=np.cross([0,1,0],cam);right/=np.linalg.norm(right);up=np.cross(cam,right)
   projected=(np.c_[ps@right,ps@up]-view['center'])*view['scale']
   self.assertTrue(np.all(abs(projected)<np.array(view['viewport'])/2-10),view['name'])
  with Image.open(ROOT/G['ART']/'comparison.png') as im:self.assertEqual(im.size,(2400,2000));self.assertGreater(np.array(im).std(),15)
 def test_ten_owned_paths_and_seven_generator_products(self):
  batch=read('docs/qa/2026-10-26/w144/batch.json');feature=next(f for f in batch['features'] if f['name']=='w144-null_composure')
  self.assertEqual(len(feature['owned_paths']),10)
  generated=set(self.man['outputs'])|{G['ART']+'manifest.json'}
  self.assertEqual(len(generated),7)
  self.assertEqual(generated|{G['SCRIPT'],G['TEST'],G['REPORT']},set(feature['owned_paths']))
if __name__=='__main__':unittest.main()
