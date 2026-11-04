#!/usr/bin/env python3
"""Targeted W147 art contracts; ROOT follows this file, never a worker absolute path."""
import base64, hashlib, io, json, runpy, unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
ID='mindbender_s_ambition_adept'
ART=ROOT/f'art/weapons/w123/{ID}'
G=runpy.run_path(str(ROOT/f'scripts/generate_surface_w123_{ID}.py'))

def read(p):return json.loads(p.read_bytes())
def contains(e,p):
 e=G['render_element'](e);p=np.array(p,float)
 if 'rotation' in e:
  r=e['rotation'];o=np.array(r['origin']);p=(p-o)@G['H']['rotation'](r)+o
 return bool(np.all(p>np.array(e['from'])+1e-6) and np.all(p<np.array(e['to'])-1e-6))
class MindbenderContracts(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.d=read(ART/'design.json');c.m=read(ROOT/G['MODEL']);c.man=read(ART/'manifest.json');c.bb=read(ART/'inspection.bbmodel');c.tex=Image.open(ROOT/G['TEXTURE']).convert('RGBA')
 def test_01_original_asset_pins(self):
  self.assertEqual(self.d['source']['source_files']["Mindbender's Ambition (Adept)/Mindbender's Ambition (Adept).blend"],'aa4710379daa24c5991a84127f4383cadf125312378196bb5ccd51830388cac7')
  self.assertEqual(self.d['source']['source_files']["Mindbender's Ambition (Adept)/Mindbender's Ambition (Adept).fbx"],'58ffdbc87222526047bf5aeabc4676f3c6304d5db4eaca2b141a35f5d583bd72')
  for p,h in self.d['input_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
  for p,h in self.d['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(p).read_bytes()),h,p)
  self.assertFalse(any('migration' in p for p in self.d['input_sha256']))
 def test_02_actual_inert_source_basis_and_inventory(self):
  ms,meta,ref=G['source_meshes']();self.assertEqual(len(ms),5);self.assertEqual(sum(len(m['faces']) for m in ms),11516)
  self.assertEqual(meta['scale'],25.017962836046397);self.assertEqual(meta['anchor'],[8,8,8])
  ps=np.concatenate([m['vertices'] for m in ms]);np.testing.assert_allclose([ps.min(0),ps.max(0)],meta['model_bounds'],atol=1e-6)
 def test_03_assembled_semantic_budget(self):
  n=len(self.m['elements']);self.assertTrue(80<=n<=120);self.assertLessEqual(n,1000);self.assertEqual(n,self.man['assembled_elements'])
  self.assertEqual(self.man['emitted_faces'],6*n);self.assertEqual(self.man['triangle_adapter_elements'],0);self.assertEqual(self.man['alpha_body_elements'],0)
  names=[e['name'] for e in self.m['elements']];self.assertEqual(len(set(names)),n)
  for e in self.m['elements']:
   self.assertTrue(np.all(np.array(e['to'])>np.array(e['from'])));self.assertEqual(set(e['faces']),set(G['FACES']))
   self.assertFalse({'vertices','triangles','shade','light_emission'}&set(e))
 def test_04_native_frame_and_canonical_display(self):
  self.assertEqual(self.m['display'],read(ROOT/G['BASE'])['display']);self.assertEqual(self.d['anchor'],[8,8,8])
  ps=np.concatenate([G['vertices'](e) for e in self.m['elements']]);bounds=np.array([ps.min(0),ps.max(0)]);ref=np.array(self.d['source']['model_bounds'])
  self.assertLess(np.max(abs(bounds-ref)),.30)
  self.assertAlmostEqual(bounds[0,2],ref[0,2],places=6);self.assertAlmostEqual(bounds[1,1],ref[1,1],places=6)
  np.testing.assert_allclose(bounds,self.man['actual_bounds'],atol=1e-7)
 def test_05_real_airways(self):
  for name,p in self.d['air_probes'].items():self.assertFalse(any(contains(e,p) for e in self.m['elements']),name)
 def test_06_filled_thick_structures(self):
  for name,p in self.d['solid_probes'].items():self.assertTrue(any(contains(e,p) for e in self.m['elements']),name)
  for group in ('receiver','forebone','grip','stock'):
   group_es=[s['geometry'] for s in self.d['parts'] if s['group']==group]
   self.assertTrue(any(e['to'][0]-e['from'][0]>.5 for e in group_es),group)
 def test_07_independent_opaque_uv_and_bleed(self):
  a=np.asarray(self.tex);self.assertEqual(self.tex.size,(1024,1024));self.assertTrue(np.all(a[:,:,3]==255))
  occupied=np.zeros((1024,1024),bool);islands=self.d['atlas']['islands'];self.assertEqual(len(islands),len(self.m['elements'])*6)
  lookup={e['name']:e for e in self.m['elements']}
  for q in islands:
   x,y,x1,y1=q['pixels'];self.assertGreaterEqual(x,2);self.assertLessEqual(x1,1022);self.assertGreaterEqual(y,2);self.assertLessEqual(y1,1022)
   self.assertFalse(occupied[y-2:y1+2,x-2:x1+2].any());occupied[y-2:y1+2,x-2:x1+2]=True
   f=lookup[q['element']]['faces'][q['face']];self.assertEqual(f['texture'],'#0');np.testing.assert_allclose(np.array(f['uv'])*64,q['pixels'])
   np.testing.assert_array_equal(a[y:y1,x-1],a[y:y1,x]);np.testing.assert_array_equal(a[y-1,x:x1],a[y,x:x1])
 def test_08_editable_inspection_parity(self):
  self.assertEqual(len(self.bb['elements']),len(self.m['elements']));self.assertEqual(self.bb['display'],self.m['display'])
  self.assertEqual(base64.b64decode(self.bb['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
  for b,e in zip(self.bb['elements'],self.m['elements']):
   self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to']);self.assertFalse(b['box_uv'])
   r=e.get('rotation',{});angles=[0,0,0]
   if r:angles['xyz'.index(r['axis'])]=r['angle']
   self.assertEqual(b['rotation'],angles)
   for f in e['faces']:np.testing.assert_allclose(np.array(b['faces'][f]['uv'])/64,e['faces'][f]['uv'])
  groups=[c for g in self.bb['outliner'] for c in g['children']];self.assertEqual(set(groups),{e['uuid'] for e in self.bb['elements']})
 def test_09_manifest_output_hashes(self):
  for p,h in self.man['output_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
  self.assertEqual(G['sha']((ROOT/f'scripts/generate_surface_w123_{ID}.py').read_bytes()),self.man['generator_sha256'])
 def test_10_full_only_no_magazine(self):
  self.assertTrue(self.man['full_only']);self.assertTrue(self.d['full_only']);self.assertFalse(self.man['native_accepted']);self.assertEqual(self.d['moving_element_names'],[])
  self.assertFalse(any('magazine' in e['name'] for e in self.m['elements']))
  self.assertEqual(self.bb['destiny_w147']['sourceAnchor'],[8,8,8]);self.assertEqual(self.bb['destiny_w147']['sourceScale'],25.017962836046397)
 def test_11_comparison_has_evidence_and_views(self):
  im=np.asarray(Image.open(ART/'comparison.png').convert('RGB'));self.assertEqual(im.shape,(1770,2700,3))
  self.assertEqual(len(self.man['comparison_metrics']),3)
  for row in range(3):
   for col in range(3):self.assertGreater(np.std(im[580+row*310:810+row*310,col*900:(col+1)*900]),10)
  for name,q in self.man['comparison_metrics'].items():self.assertGreater(q['silhouette_iou'],.63,name)
 def test_12_exact_batch_scope(self):
  f=next(f for f in read(ROOT/'docs/qa/2026-10-26/w147/batch.json')['features'] if f['name']=='w147-'+ID)
  self.assertEqual(len(f['owned_paths']),10)
  self.assertTrue(set(self.man['output_sha256'])|{str((ART/'manifest.json').relative_to(ROOT))}<=set(f['owned_paths']))
  for p in f['owned_paths']:self.assertTrue((ROOT/p).is_file(),p)
if __name__=='__main__':unittest.main(verbosity=2)
