"""Practical W150 master art checks; no claim of native visual/performance acceptance."""
import base64,hashlib,json,math,runpy,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];g=runpy.run_path(str(ROOT/'scripts/generate_surface_w150_master.py'))
read=lambda p:json.loads((ROOT/p).read_bytes())
def inside(e,p):
 r=e.get('rotation')
 if r:
  q=np.array(p)-r['origin'];a,b={'x':(1,2),'y':(2,0),'z':(0,1)}[r['axis']];t=-math.radians(r['angle']);q[a],q[b]=q[a]*math.cos(t)-q[b]*math.sin(t),q[a]*math.sin(t)+q[b]*math.cos(t);p=q+r['origin']
 return all(a+1e-6<v<b-1e-6 for a,v,b in zip(e['from'],p,e['to']))
class MasterArt(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=[(id,g['paths'](id),read(g['paths'](id)['art']+'design.json'),read(g['paths'](id)['model'])) for id in g['IDS']]
 def test_model_schema_budget_and_unique_semantic_volumes(self):
  for id,p,d,m in self.rows:
   self.assertTrue(0<len(m['elements'])<=1000);self.assertEqual(len({x['name'] for x in m['elements']}),len(m['elements']))
   for e in m['elements']:
    self.assertTrue(all(math.isfinite(a) and a<b for a,b in zip(e['from'],e['to'])),(id,e['name']));self.assertEqual(set(e['faces']),set(g['FACES']));self.assertNotIn('vertices',e);self.assertNotIn('triangles',e)
 def test_opaque_independent_uv_atlas_with_gutters(self):
  for id,p,d,m in self.rows:
   tex=Image.open(ROOT/p['texture']).convert('RGBA');self.assertEqual(tex.size,(1024,1024));self.assertEqual(tex.getchannel('A').getextrema(),(255,255));self.assertEqual(len(d['atlas']['islands']),len(m['elements'])*6)
   for e in m['elements']:
    for f in e['faces'].values():
     a,b,c,dd=f['uv'];self.assertTrue(0<=a<c<=16 and 0<=b<dd<=16);self.assertEqual(f['texture'],'#0')
 def test_real_openings_and_clear_negative_z_sight_ray(self):
  for id,p,d,m in self.rows:
   for name,point in d['openings'].items():self.assertFalse(any(inside(e,point) for e in m['elements']),(id,name))
   x,y,z=d['ads_sight']['sightCenter']
   for depth in np.linspace(-20,20,321):self.assertFalse(any(inside(e,[x,y,depth]) for e in m['elements']),(id,depth))
   pin=next(e for e in m['elements'] if e['name']=='optic_pin');self.assertLess(pin['to'][1],y);self.assertLess(y-pin['to'][1],.15)
 def test_canonical_display_axis_scale_and_proportions(self):
  for id,p,d,m in self.rows:
   self.assertEqual(m['display'],read(p['base'])['display']);self.assertEqual(d['source']['anchor'],[8,8,8]);self.assertEqual(d['source']['source_axis']['muzzle_sign'],-1)
   pts=np.concatenate([g['vertices'](e) for e in m['elements']]);self.assertLess(np.max(abs(np.array([pts.min(0),pts.max(0)])-d['source']['model_bounds'])),1.0,id)
 def test_actual_source_and_photo_hashes_and_object_selection(self):
  for id,p,d,m in self.rows:
   meshes,meta,ref,fbx,photo=g['source_meshes'](id);self.assertEqual(meta,d['source']);self.assertEqual(ref,d['reference']);self.assertEqual(sum(len(x['faces']) for x in meshes),meta['source_triangles'])
   for file,h in d['raw_input_sha256'].items():self.assertEqual(g['sha'](Path(file).read_bytes()),h)
   for file,h in d['input_sha256'].items():self.assertEqual(g['sha']((ROOT/file).read_bytes()),h)
 def test_inspection_exact_final_geometry_and_embedded_texture(self):
  for id,p,d,m in self.rows:
   bb=read(p['art']+'inspection.bbmodel');self.assertEqual(len(bb['elements']),len(m['elements']));self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',',1)[1]),(ROOT/p['texture']).read_bytes())
   for a,b in zip(bb['elements'],m['elements']):self.assertEqual(a['from'],b['from']);self.assertEqual(a['to'],b['to']);self.assertEqual(a['name'],b['name'])
 def test_photo_identity_is_not_flat_cards_or_voxels(self):
  for id,p,d,m in self.rows:
   names={x['name']:x for x in m['elements']}
   targets=['receiver_solid','rear_action','pistol_grip','magazine_well'] if id=='retraced_path' else ['receiver_coil_spine','lower_battery','pistol_grip','upper_rail_core']
   for n in targets:self.assertGreater(min(b-a for a,b in zip(names[n]['from'],names[n]['to'])),.45,(id,n))
   self.assertTrue(all('voxel' not in x and 'island' not in x for x in names));self.assertGreater(len(d['identity']),2)
 def test_manifest_matches_current_files(self):
  for id,p,d,m in self.rows:
   man=read(p['art']+'manifest.json');self.assertEqual(man['assembled_elements'],len(m['elements']));self.assertEqual(man['generator_sha256'],g['sha']((ROOT/g['SCRIPT']).read_bytes()))
   for file,h in man['output_sha256'].items():self.assertEqual(g['sha']((ROOT/file).read_bytes()),h,file)
 def test_deterministic_non_render_outputs(self):
  for id,p,d,m in self.rows:
   for file,b in g['generate'](id,False).items():
    if file!=p['art']+'manifest.json':self.assertEqual((ROOT/file).read_bytes(),b,file)
if __name__=='__main__':unittest.main(verbosity=2)
