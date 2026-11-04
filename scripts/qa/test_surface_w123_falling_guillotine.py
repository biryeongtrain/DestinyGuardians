#!/usr/bin/env python3
"""Light art regression. Not a native parser, fidelity score or performance test."""
import base64,hashlib,io,json,runpy,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_falling_guillotine.py'))
def read(p):return json.loads((ROOT/p).read_bytes())
def inside(p,e):
 p=np.array(p,float);r=e.get('rotation')
 if r:
  o=np.array(r['origin']);p=(p-o)@G['H']['rotation']({r['axis']:r['angle']})+o
 return bool(np.all(p>np.array(e['from'])-1e-8) and np.all(p<np.array(e['to'])+1e-8))
class FallingGuillotineArt(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=read(G['MODEL']);cls.d=read(G['ART']+'design.json');cls.man=read(G['ART']+'manifest.json');cls.bb=read(G['ART']+'inspection.bbmodel');cls.es={e['name']:e for e in cls.m['elements']};cls.px=np.asarray(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))
 def test_schema_budget_and_broad_solids(self):
  self.assertEqual(96,len(self.es));self.assertLessEqual(len(self.es),1000);self.assertEqual(576,self.man['emitted_faces']);self.assertEqual(96,sum(self.man['groups'].values()))
  for e in self.es.values():
   self.assertTrue(set(e)<={'name','from','to','rotation','faces'});self.assertTrue(np.all(np.array(e['to'])>e['from']));self.assertEqual(set(G['FACES']),set(e['faces']));self.assertTrue(np.isfinite(G['vertices'](e)).all())
  self.assertGreater(self.es['blade_core']['to'][1]-self.es['blade_core']['from'][1],18)
  self.assertGreater(self.es['handle_core']['to'][1]-self.es['handle_core']['from'][1],7)
 def test_frame_display_canonical_immutable(self):
  scope=read('docs/qa/2026-10-26/w135/scope.json');self.assertEqual(scope['canonical_sha256'],hashlib.sha256((ROOT/G['BASE']).read_bytes()).hexdigest());self.assertEqual(read(G['BASE'])['display'],self.m['display']);self.assertEqual([8,5.825038936061844,8],self.man['source_anchor']);self.assertEqual(22.17949538471806,self.man['source_scale'])
  self.assertLess(abs(self.man['actual_bounds'][0][2]-self.man['source_bounds'][0][2]),.10);self.assertLess(abs(self.man['actual_bounds'][0][1]-self.man['source_bounds'][0][1]),.15)
  self.assertTrue(inside([8,5.825038936061844,8],self.es['handle_core']))
 def test_air_and_bore_depth(self):
  # Representative physical openings, not an all-angle mathematical art gate.
  for p in ([8,21,7.12],[8,27,7.12],[8,29.0,6.74],[8,20,6.20]):
   self.assertEqual([], [e['name'] for e in self.es.values() if inside(p,e)],p)
  self.assertTrue(inside([8,20,8.3],self.es['blade_core']))
 def test_uv_opaque_and_gutters(self):
  self.assertEqual((1024,1024,4),self.px.shape);cover=np.zeros((1024,1024),bool)
  for row in self.d['atlas']['islands']:
   x,y,X,Y=row['pixels'];self.assertGreaterEqual(min(x,y),2);self.assertLessEqual(max(X,Y),1022)
   self.assertTrue(np.all(self.px[y-2:Y+2,x-2:X+2,3]==255));self.assertFalse(cover[y-2:Y+2,x-2:X+2].any());cover[y-2:Y+2,x-2:X+2]=True
   self.assertTrue(np.allclose(self.es[row['element']]['faces'][row['face']]['uv'],np.array([x,y,X,Y])/64))
  self.assertEqual(576,len(self.d['atlas']['islands']))
 def test_original_photo_and_raw_evidence(self):
  for p,h in self.d['input_sha256'].items():self.assertEqual(h,G['sha']((ROOT/p).read_bytes()))
  for p,h in self.d['raw_input_sha256'].items():self.assertEqual(h,G['sha'](Path(p).read_bytes()))
  photo=next(r for r in read('art/weapons/w31/references.json') if r['id']=='falling_guillotine');self.assertEqual(photo['sha256'],G['sha'](G['PHOTO'].read_bytes()));self.assertEqual(12233,self.man['source_triangles'])
 def test_editable_inspection_and_manifest(self):
  tex=base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]);self.assertEqual((ROOT/G['TEXTURE']).read_bytes(),tex)
  self.assertEqual(set(self.es),{e['name'] for e in self.bb['elements']});self.assertEqual(96,sum(len(g['children']) for g in self.bb['outliner']))
  for p,h in self.man['output_sha256'].items():self.assertEqual(h,G['sha']((ROOT/p).read_bytes()),p)
  self.assertFalse(self.man['native_accepted']);self.assertTrue(self.man['full_only']);self.assertEqual(0,self.man['alpha_body_elements'])
 def test_owned_scope_no_fake_split(self):
  scope=read('docs/qa/2026-10-26/w135/scope.json');self.assertEqual(10,len(scope['owned_paths']));self.assertTrue(all((ROOT/p).exists() for p in scope['owned_paths']))
  self.assertFalse((ROOT/G['MODEL'].replace('.json','_body.json')).exists());self.assertFalse((ROOT/G['MODEL'].replace('.json','_magazine.json')).exists())
 def test_deterministic_regeneration(self):
  for p,b in G['generate'](include_comparison=False).items():
   if not p.endswith('manifest.json'):self.assertEqual(b,(ROOT/p).read_bytes(),p)
if __name__=='__main__':unittest.main(verbosity=2)
