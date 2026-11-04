"""Practical art regression, not a substitute for actual held/ADS PNG review."""
import base64,copy,hashlib,io,json,math,runpy,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
g=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_canis_major.py'))
read=lambda p:json.loads((ROOT/p).read_bytes())

def local(element,point):
    r=element.get('rotation')
    if not r:return point
    q=[x-o for x,o in zip(point,r['origin'])];a,b={'x':(1,2),'y':(2,0),'z':(0,1)}[r['axis']]
    t=-math.radians(r['angle']);c,s=math.cos(t),math.sin(t);q[a],q[b]=q[a]*c-q[b]*s,q[a]*s+q[b]*c
    return [x+o for x,o in zip(q,r['origin'])]

def contains(e,p):return all(a+1e-6<v<b-1e-6 for a,v,b in zip(e['from'],local(e,p),e['to']))

class CanisArt(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=read(g['ART']+'design.json');cls.m=read(g['MODEL']);cls.manifest=read(g['ART']+'manifest.json');cls.texture=Image.open(ROOT/g['TEXTURE']).convert('RGBA')
 def test_semantic_solids_budget_and_schema(self):
  es=self.m['elements'];self.assertTrue(80<=len(es)<=1000);self.assertEqual(len({e['name'] for e in es}),len(es));self.assertEqual(self.manifest['assembled_elements'],len(es))
  for e in es:
   self.assertEqual(set(e['faces']),set(g['FACES']));self.assertTrue(all(math.isfinite(a) and a<b for a,b in zip(e['from'],e['to'])))
   self.assertFalse('vertices' in e or 'triangles' in e)
 def test_uv_and_opaque_atlas(self):
  self.assertEqual(self.texture.size,(1024,1024));self.assertEqual(self.texture.getchannel('A').getextrema(),(255,255))
  for e in self.m['elements']:
   for f in e['faces'].values():
    a,b,c,d=f['uv'];self.assertTrue(0<=a<c<=16 and 0<=b<d<=16);self.assertEqual(f['texture'],'#0')
  self.assertEqual(len(self.d['atlas']['islands']),len(self.m['elements'])*6)
 def test_photo_backed_identity_is_volumetric_not_alpha_cards(self):
  groups=self.manifest['groups'];self.assertGreater(groups['drum'],20);self.assertGreater(groups['barrel'],20)
  names={e['name']:e for e in self.m['elements']}
  for name in ['receiver_spine','pistol_grip','front_grip','rear_silver_tube_0','drum_core_0']:
   e=names[name];self.assertGreater(min(b-a for a,b in zip(e['from'],e['to'])),.25)
  self.assertIn('greek',{p['motif'] for p in self.d['parts']});self.assertIn('damascus',{p['motif'] for p in self.d['parts']})
 def test_real_bore_guard_and_rear_notch_openings(self):
  for point in self.d['openings'].values():self.assertFalse(any(contains(e,point) for e in self.m['elements']),point)
  center=self.d['ads_sight']['sightCenter'];self.assertEqual(center,[8,14.43,4.36])
  for z in np.linspace(-20,30,201):self.assertFalse(any(contains(e,[8,14.43,float(z)]) for e in self.m['elements']))
 def test_source_and_photo_provenance(self):
  ms,meta=g['source_meshes']();self.assertEqual(len(ms),6);self.assertEqual(sum(len(x['faces']) for x in ms),33007)
  self.assertEqual(self.d['source'],meta)
  for p,h in self.d['raw_input_sha256'].items():self.assertEqual(g['sha'](Path(p).read_bytes()),h)
  for p,h in self.d['input_sha256'].items():self.assertEqual(g['sha']((ROOT/p).read_bytes()),h)
 def test_original_display_and_native_frame_preserved(self):
  self.assertEqual(self.m['display'],read(g['BASE'])['display']);pts=np.concatenate([g['vertices'](e) for e in self.m['elements']])
  native=self.d['source']['model_bounds'];self.assertLess(np.max(np.abs(np.array([pts.min(0),pts.max(0)])-native)),1.0)
  grip=next(e for e in self.m['elements'] if e['name']=='pistol_grip');self.assertTrue(contains(grip,[8,8.2,8.1]))
 def test_inspection_embeds_exact_texture_and_geometry(self):
  bb=read(g['ART']+'inspection.bbmodel');self.assertEqual(len(bb['elements']),len(self.m['elements']))
  raw=base64.b64decode(bb['textures'][0]['source'].split(',',1)[1]);self.assertEqual(raw,(ROOT/g['TEXTURE']).read_bytes())
  for a,b in zip(bb['elements'],self.m['elements']):
   self.assertEqual(a['from'],b['from']);self.assertEqual(a['to'],b['to']);self.assertEqual(a['name'],b['name'])
 def test_manifest_pins_actual_files_and_generator(self):
  self.assertEqual(self.manifest['generator_sha256'],g['sha']((ROOT/g['SCRIPT']).read_bytes()))
  for p,h in self.manifest['output_sha256'].items():self.assertEqual(g['sha']((ROOT/p).read_bytes()),h,p)
 def test_deterministic_non_render_outputs(self):
  out=g['generate'](include_comparison=False)
  for p,b in out.items():
   if p!=g['ART']+'manifest.json':self.assertEqual((ROOT/p).read_bytes(),b,p)

if __name__=='__main__':unittest.main(verbosity=2)
