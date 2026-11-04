"""Scoped ADS contracts. Native PNGs, not these tests, decide sight readability."""
import copy,hashlib,json,math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import generate_sight_ads_w148 as g

class SightAds(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.manifest=g.read(ROOT/'art/weapons/w148/ads-manifest.json')
 def test_eye_ray_uses_actual_sight_center_not_extreme_bounds(self):
  for row in self.manifest['weapons']:
   c=row['sight']['sightCenter'];d=row['ads'];s=row['scale']
   for hand,sign in [('righthand',1),('lefthand',-1)]:
    t=d['firstperson_'+hand]['translation']
    self.assertAlmostEqual(sign*(.56+t[0]/16+s*(c[0]-8)/16),0,places=6)
    self.assertAlmostEqual(-.52+t[1]/16+s*(c[1]-8)/16,0,places=6)
    self.assertEqual(d['firstperson_'+hand]['rotation'],[0,0,0])
    if row['id'] in g.SHOTGUNS:
     self.assertAlmostEqual(-.72+t[2]/16+s*(c[2]-8)/16,-.55,places=6)
 def test_hip_sample_and_thirdperson_contexts_preserved(self):
  for row in self.manifest['weapons']:
   id=row['id'];hip=row['hip']
   self.assertEqual(g.read(g.A/f'models/{g.KEY}/{id}_00_native.json')['display'],hip)
   for f in range(21):
    d=g.read(g.A/f'models/{g.KEY}/{id}_{f:02}_native.json')['display']
    for c in hip:
     if c not in g.FP:self.assertEqual(d[c],hip[c])
 def test_old_generated_models_graphs_and_migration_stay_unchanged(self):
  for manifest,key in [('art/weapons/w50/manifest.json','sha256'),('art/weapons/w70/manifest.json','outputSha256')]:
   for p,h in g.read(ROOT/manifest)[key].items():self.assertEqual(g.sha((ROOT/p).read_bytes()),h,p)
  for row in self.manifest['weapons']:
   if row['id'] in g.SHOTGUNS:self.assertEqual(g.sha((ROOT/row['sight']['source']).read_bytes()),row['sight']['sourceSha256'])
 def test_bow_parts_share_every_corrected_transform_and_keep_motion_parent(self):
  for id in g.BOWS:
   for f in range(21):
    d=g.read(g.A/f'models/{g.KEY}/{id}_{f:02}_native.json')['display']
    for path in (g.A/f'models/{g.KEY}').glob(f'{id}_bow_*_{f:02}.json'):
     m=g.read(path);self.assertEqual(m['display'],d)
     if '_body_' in path.stem and f>0:self.assertEqual(m['parent'],f'destiny:{g.KEY}/{id}_body')
     else:self.assertTrue(m['parent'].startswith('destiny:weapon_bow_w50/'))
 def test_shotgun_sights_are_solid_open_geometry_and_budgeted(self):
  for id,cfg in g.SHOTGUNS.items():
   m=g.read(g.A/f'models/{g.KEY}/{id}_body.json');self.assertLessEqual(len(m['elements']),1000)
   e=[x for x in m['elements'] if x.get('name','').startswith('w148_')];self.assertGreaterEqual(len(e),6)
   self.assertTrue(all(len(x['faces'])==6 for x in e))
   y,z=cfg['y'],cfg['rear']
   # Existing receiver/stock must also leave the viewing axis clear. Rotated
   # semantic parts are checked with an inverse ray transform below.
   for part in m['elements']:
    for zsample in (cfg['rear']+1,cfg['rear'],cfg['front']):
     q=[8,y,zsample];rot=part.get('rotation')
     if rot:
      o=rot['origin'];q=[a-b for a,b in zip(q,o)]
      axes=[(rot['axis'],rot['angle'])] if 'angle' in rot else [(a,rot.get(a,0)) for a in ('x','y','z')]
      for axis,degrees in axes:
       angle=math.radians(-degrees);c,s=math.cos(angle),math.sin(angle);a,b={'x':(1,2),'y':(2,0),'z':(0,1)}[axis];q[a],q[b]=c*q[a]-s*q[b],s*q[a]+c*q[b]
      q=[a+b for a,b in zip(q,o)]
     self.assertFalse(all(a+1e-6<v<b-1e-6 for a,v,b in zip(part['from'],q,part['to'])),(id,part['name']))
   for x in e:
    self.assertFalse(all(a<q<b for a,q,b in zip(x['from'],[8,y,z],x['to'])),x['name'])
 def test_deterministic_outputs_and_inputs(self):
  for p,h in self.manifest['inputSha256'].items():self.assertEqual(g.sha((ROOT/p).read_bytes()),h,p)
  for p,b in g.generate().items():self.assertEqual(p.read_bytes(),b,str(p))

if __name__=='__main__':unittest.main(verbosity=2)
