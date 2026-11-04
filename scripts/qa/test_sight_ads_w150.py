import json,math,runpy,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];g=runpy.run_path(str(ROOT/'scripts/generate_sight_ads_w150.py'))
read=lambda p:json.loads(p.read_bytes())
class TraceRocketSight(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.m=read(ROOT/'art/weapons/w150/ads-manifest.json')
 def test_optical_ray_and_distance(self):
  for r in self.m['weapons']:
   x,y,z=r['sight']['sightCenter'];s=r['scale']
   for hand,sign in [('righthand',1),('lefthand',-1)]:
    d=r['ads']['firstperson_'+hand];a,b,c=d['translation']
    self.assertEqual(d['rotation'],[0,0,0]);self.assertAlmostEqual(sign*(.56+a/16+s*(x-8)/16),0,places=6);self.assertAlmostEqual(-.52+b/16+s*(y-8)/16,0,places=6);self.assertAlmostEqual(-.72+c/16+s*(z-8)/16,-.65,places=6)
 def test_hip_third_and_fallback_preserved(self):
  for r in self.m['weapons']:
   for f in range(21):
    d=read(g['A']/f'models/{g["KEY"]}/{r["id"]}_{f:02}_native.json')['display']
    for context in r['hip']:
     if context not in g['FP']:self.assertEqual(d[context],r['hip'][context])
    if f==0:self.assertEqual(d,r['hip'])
 def test_inputs_outputs_and_determinism(self):
  for p,h in self.m['inputSha256'].items():self.assertEqual(g['sha']((ROOT/p).read_bytes()),h)
  for p,b in g['generate']().items():self.assertEqual(p.read_bytes(),b,p)
 def test_all_new_firstperson_references_resolve(self):
  def visit(v):
   if isinstance(v,dict):
    if v.get('type')=='minecraft:model':
     model=v['model'];self.assertTrue((g['A']/('models/'+model.removeprefix('destiny:')+'.json')).is_file(),model)
    for x in v.values():visit(x)
   elif isinstance(v,list):
    for x in v:visit(x)
  for id in g['IDS']:visit(read(g['A']/f'items/{g["KEY"]}/{id}.json'))
if __name__=='__main__':unittest.main(verbosity=2)
