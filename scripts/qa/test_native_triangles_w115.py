#!/usr/bin/env python3
"""Geometry math tests; not framebuffer or performance acceptance."""
import importlib.util,math,random,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('tri',Path(__file__).resolve().parents[1]/'mesh/native_triangle_elements_w115.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
class Triangles(unittest.TestCase):
 def close(self,a,b,tol=2e-7):
  for x,y in zip(a,b):self.assertAlmostEqual(x,y,delta=tol)
 def verify(self,vertices):
  parts=t.split_triangle(vertices);self.assertTrue(1<=len(parts)<=2)
  area=t.norm(t.cross(t.sub(vertices[1],vertices[0]),t.sub(vertices[2],vertices[0])))/2
  self.assertAlmostEqual(area,sum(p['width']*p['height']/2 for p in parts),delta=1e-7)
  for p in parts:
   for local,expected in [((0,0,0),p['vertices'][0]),((p['width'],0,0),p['vertices'][1]),((0,p['height'],0),p['vertices'][2])]:
    self.close(t.add(p['origin'],t.rotate(local,p['rotation'])),expected)
   self.close(t.point_at(p,0,1),p['vertices'][0]);self.close(t.point_at(p,1,1),p['vertices'][1]);self.close(t.point_at(p,0,0),p['vertices'][2])
  return parts
 def test_axis_aligned(self):self.verify(((8,8,8),(12,8,8),(9,12,8)))
 def test_right_angle(self):self.verify(((8,8,8),(13,8,8),(8,12,8)))
 def test_obtuse(self):self.verify(((8,8,8),(12,8,8),(7,9,8)))
 def test_negative_normal(self):self.verify(((8,8,8),(8,12,8),(12,8,8)))
 def test_vertical(self):self.verify(((8,8,8),(8,12,8),(8,10,15)))
 def test_six_permutations(self):
  import itertools
  for v in itertools.permutations(((3,8,-4),(9,12,16),(7,16,3))):self.verify(v)
 def test_seeded_random(self):
  r=random.Random(115)
  for i in range(1000):self.verify([tuple(r.uniform(-8,24) for a in range(3)) for v in range(3)])
 def test_gimbal_lock(self):
  for y in (90.,-90.,89.999999999,-89.999999999,89.999999,-89.999999):
   for x in (-130,0,27):
    for z in (-80,0,141):
     basis=[t.rotate(v,(x,y,z)) for v in ((1,0,0),(0,1,0),(0,0,1))]
     angles=t.euler_zyx(*basis)
     for v,b in zip(((1,0,0),(0,1,0),(0,0,1)),basis):self.close(t.rotate(v,angles),b)
 def test_normalized_vertical_roundoff(self):
  # Actual authored Krait stock-heel section: normalization produced nextafter(1,0).
  for sign in (-1,1):
   u=(0.,0.,sign*math.nextafter(1.,0.));v=(1.,0.,0.);n=(0.,float(sign),0.)
   angles=t.euler_zyx(u,v,n)
   for local,expected in zip(((1,0,0),(0,1,0),(0,0,1)),(u,v,n)):
    self.close(t.rotate(local,angles),expected,tol=1e-12)
 def test_invalid_geometry(self):
  for bad in [[],[(0,0,0)]*3,[(0,0,0),(1,1,1),(2,2,2)],[(0,0,0),(math.nan,1,1),(1,2,0)],[(1,2),(2,3),(3,4)]]:
   with self.assertRaises(ValueError):t.split_triangle(bad)
 def test_native_element_corner_mapping(self):
  for p in self.verify(((3,8,-4),(9,12,16),(7,16,3))):
   e=t.to_element(p,'triangle',[0,0,4,4]);r=e['rotation'];pivot=r['origin'];angles=[r[a] for a in 'xyz'];lo=e['from'];hi=e['to']
   for local,expected in [(lo,p['vertices'][0]),((hi[0],lo[1],lo[2]),p['vertices'][1]),((lo[0],hi[1],lo[2]),p['vertices'][2])]:self.close(t.add(pivot,t.rotate(t.sub(local,pivot),angles)),expected)
   self.assertEqual(e['from'][2],e['to'][2]);self.assertEqual({'north','south'},set(e['faces']));self.assertEqual([4,0,0,4],e['faces']['north']['uv'])
 def test_bad_uvs(self):
  p=t.split_triangle(((8,8,8),(12,8,8),(9,12,8)))[0]
  for uv in [[],[-1,0,4,4],[0,0,17,4],[4,4,1,1],[0,0,math.nan,4]]:
   with self.assertRaises(ValueError):t.to_element(p,'bad',uv)
if __name__=='__main__':unittest.main()
