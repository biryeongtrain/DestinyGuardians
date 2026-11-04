#!/usr/bin/env python3
"""W147 targeted offline bow product regression. ROOT is relative to this file."""
import base64,copy,hashlib,io,json,runpy,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
H=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_biting_winds.py'))
def read(p):return json.loads((ROOT/p).read_bytes())
class BitingWindsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=read(H['ART']+'design.json');cls.m=read(H['MODEL']);cls.mf=read(H['ART']+'manifest.json');cls.bb=read(H['ART']+'inspection.bbmodel');cls.old=read(H['BASE']);cls.body=cls.m['elements'][:len(cls.d['parts'])];cls.atlas=np.asarray(Image.open(ROOT/H['TEXTURE']))
 def test_exact_moving_rest_and_texture_remap(self):
  expect=H['moving_rest'](self.old);actual=[e for e in self.m['elements'] if e['name'] in self.d['moving_element_names']];self.assertEqual(actual,expect);self.assertEqual(len(actual),23)
  original=H['W50']['parts'](self.old,H['W50']['CONFIG']['biting_winds'])[1]
  for a,b in zip(actual,original):
   a=copy.deepcopy(a);a.pop('name')
   for f in a['faces'].values():f['texture']='#0'
   self.assertEqual(a,b)
 def test_two_textures_resolve_original(self):
  self.assertEqual(self.m['textures']['original'],self.old['textures']['0']);self.assertEqual(len([k for k in self.m['textures'] if k!='particle']),2)
  for e in self.body:self.assertTrue(all(f['texture']=='#0' for f in e['faces'].values()))
 def test_body_budget_and_classification(self):
  self.assertTrue(80<=len(self.body)<=160);self.assertLessEqual(self.mf['max_assembled_elements'],1000);self.assertEqual(self.mf['max_assembled_elements'],len(self.body)+23)
  self.assertEqual([e['name'] for e in self.body],self.d['body_element_names']);self.assertFalse(set(self.d['body_element_names'])&set(self.d['moving_element_names']))
  self.assertTrue(all(s['classification']=='rigid_body' for s in self.d['parts']))
  self.assertFalse(any('string' in e['name'] or 'arrow' in e['name'] and 'shelf' not in e['name'] for e in self.body if 'arrow_shelf'!=e['name']))
 def test_native_frame_and_display(self):
  self.assertEqual(self.m['display'],self.old['display']);self.assertEqual(self.d['source']['scale'],22.000896462875446);self.assertEqual(self.d['source']['anchor'],[8,8,8])
  p=np.concatenate([H['vertices'](e) for e in self.m['elements']]);bounds=np.array(self.d['source']['model_bounds']);self.assertTrue(np.all(p.min(0)>=bounds[0]-1e-5),(p.min(0),bounds[0]));self.assertTrue(np.all(p.max(0)<=bounds[1]+1e-5),(p.max(0),bounds[1]))
  np.testing.assert_allclose([p.min(0),p.max(0)],bounds,atol=1e-6,rtol=0)
 def test_filled_cubes_and_explicit_uv(self):
  for e in self.body:
   self.assertTrue(np.all(np.array(e['to'])-e['from']>.10));self.assertEqual(set(e['faces']),set(H['FACES']));self.assertNotIn('vertices',e)
   for f in e['faces'].values():self.assertEqual(len(f['uv']),4);self.assertTrue(all(0<=v<=16 for v in f['uv']))
 def test_opaque_independent_uv_and_gutters(self):
  self.assertTrue(np.all(self.atlas[:,:,3]==255));islands=self.d['atlas']['islands'];self.assertEqual(len(islands),len(self.body)*6);occupied=np.zeros((1024,1024),bool)
  for island in islands:
   x,y,X,Y=island['rect'];self.assertTrue(x>=2 and y>=2 and X<=1022 and Y<=1022);self.assertFalse(occupied[y-2:Y+2,x-2:X+2].any());occupied[y-2:Y+2,x-2:X+2]=True
   np.testing.assert_array_equal(self.atlas[y:Y,x-1],self.atlas[y:Y,x]);np.testing.assert_array_equal(self.atlas[y-1,x:X],self.atlas[y,x:X])
 def test_structural_windows_and_cam_depth(self):
  def occupied(point):
   for e in self.body:
    r=H['native_rotation'](e);p=np.array(point);o=np.array(r.get('origin',[0,0,0]));p=(p-o)@H['H']['rotation'](r)+o
    if np.all(p>np.array(e['from'])+1e-6) and np.all(p<np.array(e['to'])-1e-6):return True
   return False
  for y,z in [(8.6,7.35),(6.95,7.15),(6.2,6.6),(13,6.95),(15.6,5.7)]:
   for x in [7.8,8,8.2]:self.assertFalse(occupied([x,y,z]),(x,y,z))
  for name in ['upper_tip_wheel_section_0','lower_tip_wheel_section_0']:
   e=next(e for e in self.body if e['name']==name);self.assertGreater(e['to'][0]-e['from'][0],.5)
 def test_renderer_uses_both_face_slots(self):
  ts=H['model_triangles'](self.m,{'0':Image.new('RGBA',(4,4),(255,0,0,255)),'original':Image.new('RGBA',(4,4),(0,255,0,255))})
  self.assertEqual(len(ts),len(self.m['elements'])*12);self.assertEqual(sum(int(t[2][0,0,1])==255 for t in ts),23*12);self.assertEqual(sum(int(t[2][0,0,0])==255 for t in ts),len(self.body)*12)
 def test_raw_sdna_audit(self):
  ms,meta,audit=H['source_meshes']();self.assertEqual(len(ms),8);self.assertEqual(sum(len(m['faces']) for m in ms),23528);self.assertEqual(sum(not a['retained'] for a in audit),3)
 def test_direct_input_hashes(self):
  for p,v in self.d['input_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),v,p)
  for p,v in self.d['raw_input_sha256'].items():self.assertEqual(hashlib.sha256(Path(p).read_bytes()).hexdigest(),v,p)
  self.assertFalse(any('migration' in p for p in self.d['input_sha256']))
 def test_output_hashes(self):
  for p,v in self.mf['output_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),v,p)
  self.assertEqual(self.mf['test_sha256'],hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 def test_bb_dual_texture_geometry_uv_parity(self):
  self.assertEqual(len(self.bb['textures']),2);self.assertEqual(len(self.bb['elements']),len(self.m['elements']));self.assertEqual(self.bb['display'],self.m['display'])
  imgs=[Image.open(io.BytesIO(base64.b64decode(t['source'].split(',')[1]))) for t in self.bb['textures']]
  self.assertEqual(imgs[0].tobytes(),Image.open(ROOT/H['TEXTURE']).tobytes());self.assertEqual(imgs[1].convert('RGBA').tobytes(),Image.open(ROOT/(H['ASSET']+'textures/item/weapon/w30/biting_winds.png')).convert('RGBA').tobytes())
  for e,b in zip(self.m['elements'],self.bb['elements']):
   self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to']);r=H['native_rotation'](e);self.assertEqual(b['rotation'],[r.get(a,0) for a in 'xyz'])
   for f,v in e['faces'].items():
    ix=1 if v['texture']=='#original' else 0;self.assertEqual(b['faces'][f]['texture'],ix);w,h=imgs[ix].size;np.testing.assert_allclose(b['faces'][f]['uv'],[q*(w if i%2==0 else h)/16 for i,q in enumerate(v['uv'])],atol=1e-10)
 def test_exact_ten_owned_paths_and_comparison(self):
  spec=next(f for f in read(H['BATCH'])['features'] if f['name']=='w147-biting_winds');self.assertEqual(len(spec['owned_paths']),10);self.assertTrue(all((ROOT/p).is_file() for p in spec['owned_paths']));
  with Image.open(ROOT/(H['ART']+'comparison.png')) as image:self.assertEqual(image.size,(2550,2890))
  self.assertFalse(self.mf['native_accepted'])
if __name__=='__main__':unittest.main(verbosity=2)
