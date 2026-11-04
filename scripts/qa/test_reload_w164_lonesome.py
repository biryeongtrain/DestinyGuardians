#!/usr/bin/env python3
"""Targeted W164 Lonesome geometry/graph/transform and read-only regeneration tests."""
import copy,hashlib,importlib.util,json,math,subprocess,sys,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('lonesome',ROOT/'scripts/generate_reload_w164_lonesome.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
def j(path):return json.loads(path.read_bytes())
def child(i,p,h):return j(g.ASSET/f'models/{g.KEY}_{i:02d}_{p}_{h}.json')
def matrix(p,left=False):
 a,b,c=np.radians(p['rotation']);sgn=-1 if left else 1;b*=sgn;c*=sgn
 rx=np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
 ry=np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]])
 rz=np.array([[math.cos(c),-math.sin(c),0],[math.sin(c),math.cos(c),0],[0,0,1]])
 m=np.eye(4);m[:3,:3]=rx@ry@rz@np.diag(p['scale']);m[:3,3]=np.array(p['translation'])/16;m[0,3]*=sgn;return m
class ReloadTest(unittest.TestCase):
 def test_geometry_and_hidden_insert(self):
  source=j(g.SOURCE);body=j(g.ASSET/f'models/{g.KEY}_body.json');moving=j(g.ASSET/f'models/{g.KEY}_moving.json')
  self.assertEqual(95,len(body['elements']));self.assertEqual(3,len(moving['elements']))
  bi=mi=0
  for i,e in enumerate(source['elements']):
   actual=moving['elements'][mi] if i in g.MOVING else body['elements'][bi]
   self.assertEqual(e,actual)
   if i in g.MOVING:mi+=1
   else:bi+=1
  core=source['elements'][72];insert=moving['elements'][-1];self.assertEqual(core['rotation'],insert['rotation'])
  for a in range(3):self.assertLess(core['from'][a],insert['from'][a]);self.assertLess(insert['to'][a],core['to'][a])
  self.assertEqual(source['textures'],body['textures']);self.assertEqual(source['textures'],moving['textures'])
 def test_graph_fallback_and_84_children(self):
  source=j(g.ASSET/'items/weapon/lonesome.json');item=j(g.ASSET/f'items/{g.KEY}.json');outer=item['model'];self.assertEqual(source['model'],outer['fallback'])
  case=outer['cases'][0];self.assertEqual(list(g.FP),case['when']);r=case['model'];self.assertEqual(1,r['index']);self.assertEqual(source['model'],r['fallback'])
  self.assertEqual(21,len(r['entries']));seen=set()
  for i,row in enumerate(r['entries']):
   self.assertEqual(i/20,row['threshold']);c=row['model'];self.assertEqual(0,c['index'])
   for grip,key in [('native','on_false'),('twohand','on_true')]:
    leaves=c[key]['models'];self.assertEqual(2,len(leaves))
    for part,leaf in zip(g.PARTS,leaves):
     self.assertEqual(f'destiny:{g.KEY}_{i:02d}_{part}_{grip}',leaf['model']);seen.add(leaf['model'])
  self.assertEqual(84,len(seen));metadata=copy.deepcopy(item);metadata['model']=source['model'];self.assertEqual(source,metadata)
 def test_endpoints_and_carrier_inverse_both_hands(self):
  base=j(g.SOURCE)['display'];two=j(g.ASSET/'models/weapon/sidearm/lonesome_twohand.json')['display']
  for i in range(21):
   for part in g.PARTS:
    for grip,expected in [('native',base),('twohand',two)]:
     c=child(i,part,grip);self.assertEqual({'parent','display'},set(c));d=c['display']
     if i in (0,20):self.assertEqual(expected,d)
     for context in expected:
      if context not in g.FP:self.assertEqual(expected[context],d[context])
    for context in g.FP:
     left=context==g.FP[1];sign=-1 if left else 1;a=math.radians(10)*sign
     carrier=np.eye(4);carrier[:3,:3]=[[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]];carrier[0,3]=-.641864*sign
     np.testing.assert_allclose(matrix(child(i,part,'native')['display'][context],left),carrier@matrix(child(i,part,'twohand')['display'][context],left),atol=1e-7)
 def test_rotation_composed_travel(self):
  for frame in range(21):
   _,_,travel=g.sample(frame/20)
   for context in g.FP:
    b=child(frame,'body','native')['display'][context];m=child(frame,'moving','native')['display'][context]
    self.assertEqual(b['rotation'],m['rotation']);self.assertEqual(b['scale'],m['scale'])
    actual=np.linalg.inv(matrix(b))@matrix(m)
    expected=np.eye(4);expected[:3,3]=np.array([0,-travel*math.cos(math.radians(10)),travel*math.sin(math.radians(10))])/16
    np.testing.assert_allclose(actual,expected,atol=1e-7)
 def test_manifest_reference_hashes(self):
  m=j(g.ART/'manifest.json');self.assertEqual(87,len(m['sha256']));self.assertEqual(12,len(m['referenceSha256']));self.assertFalse(m['nativeGameplayVerified'])
  for k in ('sha256','originalSha256','referenceSha256','evidenceSha256'):
   for p,h in m[k].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest())
 def test_verify_is_read_only(self):
  paths=list(g.ART.iterdir())+list((g.ASSET/'models/weapon_reload_w164_lonesome').iterdir())+list((g.ASSET/'items/weapon_reload_w164_lonesome').iterdir())
  before={p:(p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths}
  subprocess.run([sys.executable,str(ROOT/'scripts/generate_reload_w164_lonesome.py'),'--verify'],check=True)
  self.assertEqual(before,{p:(p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths})
if __name__=='__main__':unittest.main()
