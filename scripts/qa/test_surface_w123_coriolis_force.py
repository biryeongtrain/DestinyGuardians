#!/usr/bin/env python3
"""Targeted Coriolis Force W144 offline asset regression; no native/DCC claims."""
import base64,copy,io,json,runpy,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_coriolis_force.py'))

class CoriolisForceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ms,cls.meta,cls.audit=G['source_meshes']();cls.d=json.loads((ROOT/G['ART']/ 'design.json').read_bytes())
  cls.m=json.loads((ROOT/G['MODEL']).read_bytes());cls.man=json.loads((ROOT/G['ART']/ 'manifest.json').read_bytes())
  cls.atlas=Image.open(ROOT/G['TEXTURE']).convert('RGBA');cls.bb=json.loads((ROOT/G['ART']/ 'inspection.bbmodel').read_bytes())
 def hits(self,p):
  p=np.array(p,float)
  for e in self.m['elements']:
   r=e.get('rotation');q=p.copy()
   if r:
    o=np.array(r['origin']);q=(q-o)@G['H']['rotation'](r)+o
   if np.all(q>=np.array(e['from'])-1e-7) and np.all(q<=np.array(e['to'])+1e-7):return True
  return False
 def test_native_schema_and_assembled_budget(self):
  es=self.m['elements'];self.assertLessEqual(len(es),1000);self.assertEqual(len(es),self.man['assembled_elements'])
  self.assertEqual(len({e['name'] for e in es}),len(es));self.assertTrue(self.man['full_only'])
  self.assertEqual(self.man['triangle_adapter_elements'],0);self.assertEqual(self.man['alpha_body_elements'],0)
  for e in es:
   self.assertTrue(np.all(np.array(e['to'])>e['from']));self.assertEqual(set(e['faces']),set(G['FACES']))
   self.assertFalse({'vertices','triangles'}&set(e))
   if 'rotation' in e:self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
 def test_source_basis_and_original_display(self):
  self.assertEqual(self.d['source'],self.meta);self.assertEqual(self.meta['scale'],41.469411629369226)
  self.assertEqual(self.meta['anchor'],[8,8,8]);self.assertEqual(self.meta['source_axis'],dict(length=1,thin=0,muzzle_sign=-1))
  self.assertEqual(self.m['display'],json.loads((ROOT/G['BASE']).read_bytes())['display'])
  self.assertEqual(sum(len(m['faces']) for m in self.ms),13801);self.assertEqual(len(self.ms),5);self.assertEqual(sum(len(m['faces']) for m in self.ms if m['material']!='Fusion'),13799)
  ps=np.concatenate([m['vertices'] for m in self.ms]);np.testing.assert_allclose([ps.min(0),ps.max(0)],self.meta['model_bounds'],atol=1e-6,rtol=0)
 def test_physical_transverse_air_channels(self):
  for name,p in self.d['openings'].items():
   for x in np.linspace(6.8,9.2,61):self.assertFalse(self.hits([x,p[1],p[2]]),f'{name} blocked at X{x}')
 def test_source_object_accounting(self):
  audit=self.d['source_audit'];self.assertEqual(len(audit),7)
  self.assertEqual(sum(a['triangles'] for a in audit),13861)
  self.assertEqual(sum(a['triangles'] for a in audit if not a['retained']),60)
  self.assertEqual(sum(a['triangles'] for a in audit if a['material']=='Fusion'),2)
  self.assertEqual(len(G['source_triangles'](self.ms)),13799)
 def test_open_axial_sights(self):
  for z in np.linspace(-.52,-.18,20):self.assertFalse(self.hits([8,15.30,z]))
 def test_actual_recessed_muzzle(self):
  for z in np.linspace(-11,-10.25,50):self.assertFalse(self.hits([8,13.88,z]),f'bore blocked {z}')
  self.assertTrue(self.hits([8,13.88,-10.18]))
  for p in ([8,14.26,-10.6],[8,13.50,-10.6],[7.62,13.88,-10.6],[8.38,13.88,-10.6]):self.assertTrue(self.hits(p),p)
 def test_filled_transverse_masses(self):
  widths=dict(cartridge=.82,receiver=1.40,barrel=.50,stock=1.35,grip=.95)
  for name,p in self.d['filled_probes'].items():
   for x in np.linspace(8-widths[name]/2,8+widths[name]/2,31):self.assertTrue(self.hits([x,p[1],p[2]]),f'{name} empty core {x}')
 def test_asymmetric_clamp_has_depth(self):
  names=[e for e in self.m['elements'] if e['name'].startswith('u_clamp_')]
  self.assertEqual(len(names),5)
  pts=np.concatenate([G['vertices'](e) for e in names]);self.assertGreater(pts[:,0].min(),8.8)
  self.assertTrue(self.hits([9.12,12.05,4.5]));self.assertFalse(self.hits([9.12,13.2,4.5]))
 def test_connected_receiver_and_grip_mounts(self):
  for p in ([8,13.72,.16],[8,13.72,1.74],[8,11.81,2.0],[8,11.7,6.7],[8,11.05,6.8]):
   self.assertTrue(self.hits(p),p)
 def test_face_uv_opacity_nonoverlap_and_gutters(self):
  a=np.asarray(self.atlas);self.assertEqual(self.atlas.size,(1024,1024));self.assertEqual(int(a[:,:,3].min()),255)
  used=np.zeros((1024,1024),bool);lookup={e['name']:e for e in self.m['elements']}
  self.assertEqual(len(self.d['atlas']['islands']),len(lookup)*6)
  for it in self.d['atlas']['islands']:
   x,y,r,b=it['pixels'];self.assertTrue(2<=x<r<=1022 and 2<=y<b<=1022)
   self.assertFalse(used[y-2:b+2,x-2:r+2].any());used[y-2:b+2,x-2:r+2]=True
   np.testing.assert_array_equal(a[y-2:y,x:r],np.repeat(a[y:y+1,x:r],2,axis=0))
   np.testing.assert_array_equal(a[y:b,r:r+2],np.repeat(a[y:b,r-1:r],2,axis=1))
   f=lookup[it['element']]['faces'][it['face']];self.assertEqual(f['texture'],'#0');self.assertEqual(f['uv'],[q/64 for q in it['pixels']])
 def test_editable_inspection_parity(self):
  self.assertEqual(self.bb['display'],self.m['display']);self.assertEqual(len(self.bb['elements']),len(self.m['elements']))
  self.assertEqual(base64.b64decode(self.bb['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
  self.assertEqual(sum(len(g['children']) for g in self.bb['outliner']),len(self.m['elements']))
  for a,b in zip(self.m['elements'],self.bb['elements']):
   for k in ('from','to','name'):self.assertEqual(a[k],b[k])
   r=a.get('rotation');self.assertEqual(b['rotation'],[r[ax] if r else 0 for ax in 'xyz'])
   for f in a['faces']:self.assertEqual(b['faces'][f]['uv'],[v*64 for v in a['faces'][f]['uv']])
 def test_input_output_provenance(self):
  for p,digest in self.man['input_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),digest)
  for p,digest in self.man['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(p).read_bytes()),digest)
  for p,digest in self.man['output_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),digest)
  self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/G['SCRIPT']).read_bytes()))
  self.assertEqual(self.man['test_sha256'],G['sha'](Path(__file__).read_bytes()))
  self.assertFalse(any('manifest' in p for p in self.man['input_sha256']))
 def test_owned_ten_path_scope(self):
  f=next(f for f in json.loads((ROOT/G['BATCH']).read_bytes())['features'] if f['name']=='w144-coriolis_force')
  expected={G['SCRIPT'],G['TEST'],G['REPORT'],G['MODEL'],G['TEXTURE'],*[G['ART']+x for x in ['design.json','manifest.json','review.md','inspection.bbmodel','comparison.png']]}
  self.assertEqual(set(f['owned_paths']),expected);self.assertEqual(len(expected),10)
  self.assertLessEqual(set(self.man['output_sha256']),expected)
 def test_deterministic_regeneration(self):
  for p,data in G['generate'](include_comparison=False).items():
   if p.endswith('manifest.json'):continue
   self.assertEqual((ROOT/p).read_bytes(),data,p)
 def test_real_evidence_layout(self):
  with Image.open(ROOT/G['ART']/ 'comparison.png') as im:self.assertEqual(im.size,(3000,2040))
  ref=next(x for x in json.loads((ROOT/G['REFS']).read_bytes()) if x['id']=='coriolis_force')
  self.assertEqual(self.man['default_photo_sha256'],ref['sha256']);self.assertFalse(self.man['native_accepted'])
  self.assertEqual(self.man['source_matching']['objects'],5)

if __name__=='__main__':unittest.main(verbosity=2)
