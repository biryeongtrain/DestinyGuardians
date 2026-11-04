#!/usr/bin/env python3
"""Focused offline W143 asset checks; source frame, solids, UV, evidence and repeatability."""
import base64,io,json,runpy,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_high_albedo.py'))

class HighAlbedoTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.meshes,cls.meta=G['source_meshes']()
  cls.d=json.loads((ROOT/G['ART']/'design.json').read_bytes())
  cls.m=json.loads((ROOT/G['MODEL']).read_bytes())
  cls.man=json.loads((ROOT/G['ART']/'manifest.json').read_bytes())
  cls.atlas=Image.open(ROOT/G['TEXTURE']).convert('RGBA')
  cls.bb=json.loads((ROOT/G['ART']/'inspection.bbmodel').read_bytes())
 def hits(self,p):
  p=np.array(p,float)
  for e in self.m['elements']:
   q=p.copy();r=e.get('rotation')
   if r:
    o=np.array(r['origin']);q=(q-o)@G['H']['rotation']({r['axis']:r['angle']})+o
   if np.all(q>=np.array(e['from'])-1e-7) and np.all(q<=np.array(e['to'])+1e-7):return True
  return False
 def test_accepted_inert_source_and_coordinate_frame(self):
  self.assertEqual(sorted(m['name'] for m in self.meshes),sorted(self.meta['source_objects']))
  self.assertEqual(len(self.meshes),2)
  self.assertEqual([len(m['faces']) for m in self.meshes],[10378,26])
  self.assertEqual(sum(len(m['faces']) for m in self.meshes),self.meta['source_triangles'])
  self.assertEqual(self.d['source_matching']['triangle_difference'],0)
  pts=np.concatenate([m['vertices'] for m in self.meshes])
  np.testing.assert_allclose([pts.min(0),pts.max(0)],self.meta['model_bounds'],atol=1e-6,rtol=0)
  self.assertEqual(self.d['source'],self.meta)
  self.assertEqual(self.man['source_scale'],self.meta['scale']);self.assertEqual(self.man['source_anchor'],[8,8,8])
  self.assertEqual(self.man['source_axis'],dict(length=1,thin=0,muzzle_sign=-1))
 def test_emitted_schema_positive_dimensions_and_budget(self):
  es=self.m['elements'];self.assertLessEqual(len(es),1000);self.assertEqual(len(es),self.man['assembled_elements'])
  self.assertEqual(len({e['name'] for e in es}),len(es));self.assertEqual(self.man['emitted_faces'],len(es)*6)
  self.assertEqual(sum(self.man['groups'].values()),len(es))
  self.assertEqual(self.man['triangle_adapter_elements'],0);self.assertEqual(self.man['alpha_body_elements'],0)
  for e in es:
   self.assertTrue(np.all(np.isfinite([e['from'],e['to']])));self.assertTrue(np.all(np.array(e['to'])>e['from']))
   self.assertEqual(set(e['faces']),set(G['FACES']));self.assertFalse({'vertices','triangles'}&set(e))
   if 'rotation' in e:
    self.assertEqual(set(e['rotation']),{'origin','axis','angle'});self.assertIn(e['rotation']['axis'],'xyz')
 def test_envelope_and_canonical_display(self):
  p=np.concatenate([G['vertices'](e) for e in self.m['elements']]);bounds=np.array([p.min(0),p.max(0)])
  np.testing.assert_allclose(bounds,self.man['actual_bounds'],atol=1e-7,rtol=0)
  self.assertLess(float(np.max(np.abs(bounds-self.meta['model_bounds']))),.20)
  self.assertEqual(self.m['display'],json.loads((ROOT/G['BASE']).read_bytes())['display'])
  self.assertTrue(self.man['full_only']);self.assertTrue(self.man['canonical_display_exact'])
 def test_filled_receiver_frame_and_grip(self):
  for name,p in self.d['filled_probes'].items():
   for x in np.linspace(7.5,8.5,17):
    for dy in (-.1,0,.1):self.assertTrue(self.hits([x,p[1]+dy,p[2]]),f'empty {name} at {x}')
 def test_real_transverse_clearances(self):
  for name,p in self.d['openings'].items():
   for x in np.linspace(6.65,9.35,35):self.assertFalse(self.hits([x,p[1],p[2]]),f'{name} blocked {x}')
 def test_two_recessed_physical_bores(self):
  for bore in self.d['bore_probes']:
   x,y=bore['center']
   for z in np.linspace(*bore['z_range'],71):
    for dx,dy in ((0,0),(.07,0),(-.07,0),(0,.07),(0,-.07)):
     self.assertFalse(self.hits([x+dx,y+dy,z]),f'{bore["name"]} blocked at {z}')
   self.assertTrue(self.hits(bore['back']),bore['name'])
  for p in ([8,13.69,-1.30],[8,12.63,-1.30],[7.47,13.16,-1.30],[8.53,13.16,-1.30],[8,11.78,-3.20],[8,10.98,-3.20]):
   self.assertTrue(self.hits(p),f'missing bore wall {p}')
 def test_uv_opaque_atlas_rectangles_and_gutters(self):
  a=np.asarray(self.atlas);self.assertEqual(self.atlas.size,(1024,1024));self.assertEqual(int(a[:,:,3].min()),255)
  used=np.zeros((1024,1024),bool);lookup={e['name']:e for e in self.m['elements']}
  self.assertEqual(len(self.d['atlas']['islands']),6*len(lookup))
  for it in self.d['atlas']['islands']:
   x,y,r,b=it['pixels'];self.assertTrue(2<=x<r<=1022 and 2<=y<b<=1022)
   self.assertFalse(used[y-2:b+2,x-2:r+2].any());used[y-2:b+2,x-2:r+2]=True
   np.testing.assert_array_equal(a[y-2:y,x:r],np.repeat(a[y:y+1,x:r],2,axis=0))
   np.testing.assert_array_equal(a[y:b,r:r+2],np.repeat(a[y:b,r-1:r],2,axis=1))
   f=lookup[it['element']]['faces'][it['face']];self.assertEqual(f['texture'],'#0');self.assertEqual(f['uv'],[v/64 for v in it['pixels']])
 def test_blockbench_geometry_and_atlas_parity(self):
  self.assertEqual(self.bb['display'],self.m['display']);self.assertEqual(len(self.bb['elements']),len(self.m['elements']))
  self.assertEqual(sum(len(g['children']) for g in self.bb['outliner']),len(self.m['elements']))
  self.assertEqual(base64.b64decode(self.bb['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
  lookup={e['name']:e for e in self.bb['elements']}
  for a in self.m['elements']:
   b=lookup[a['name']]
   for k in ('from','to'):self.assertEqual(a[k],b[k])
   r=a.get('rotation');self.assertEqual(b['rotation'],[r['angle'] if r and r['axis']==ax else 0 for ax in 'xyz'])
   for f in a['faces']:self.assertEqual(b['faces'][f]['uv'],[v*64 for v in a['faces'][f]['uv']])
 def test_provenance_without_downstream_manifest_pin(self):
  for key in ('input_sha256','raw_input_sha256','output_sha256'):
   for p,digest in self.man[key].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),digest,p)
  self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/G['SCRIPT']).read_bytes()))
  self.assertEqual(self.man['test_sha256'],G['sha'](Path(__file__).read_bytes()))
  self.assertFalse(any('manifest' in p or 'migration' in p for p in self.man['input_sha256']))
  self.assertFalse(self.man['native_accepted']);self.assertFalse(self.man['pbr_accepted'])
 def test_deterministic_owned_regeneration(self):
  outputs=G['generate'](include_comparison=False)
  allowed={G['MODEL'],G['TEXTURE'],*[G['ART']+x for x in ('design.json','manifest.json','review.md','inspection.bbmodel','comparison.png')]}
  self.assertLessEqual(set(outputs),allowed)
  for p,data in outputs.items():
   if p.endswith('manifest.json'):continue
   self.assertEqual((ROOT/p).read_bytes(),data,p)
 def test_real_comparison_photo_and_seed_counts(self):
  with Image.open(ROOT/G['ART']/'comparison.png') as im:
   self.assertEqual(im.size,(3000,2260));self.assertGreater(float(np.asarray(im).std()),10)
  ref=next(x for x in json.loads((ROOT/G['REFS']).read_bytes()) if x['id']=='high_albedo')
  self.assertEqual(self.man['default_photo_sha256'],ref['sha256'])
  self.assertEqual(self.man['canonical_seed_elements'],len(json.loads((ROOT/G['BASE']).read_bytes())['elements']))

if __name__=='__main__':unittest.main(verbosity=2)
