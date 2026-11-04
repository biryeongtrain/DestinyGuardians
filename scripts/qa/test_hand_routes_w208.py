#!/usr/bin/env python3
"""W208 source-direction admission and repeated shell lifecycle regression."""
import math,sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import rig_arms_w205 as rig

def distance(a,b):
 return max(abs(x-y) for key in a for row,other in zip(a[key],b[key]) for x,y in zip(row,other))

class HandRoutesW208(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rigs,_=rig.load()
 def test_new_whole_reload_routes_animate_and_settle(self):
  for weapon,tag in [('the_recluse','80A8A192'),('beloved','80A8A140'),('gnawing_hunger','80A8A395'),('austringer','80A8A53D')]:
   d=self.rigs[weapon];c={'weapon':weapon,'reload':{'rigAction':tag}}
   a,active=rig.joints(d,{},.411,c);b,_=rig.joints(d,{},.419,c)
   self.assertTrue(active,weapon);self.assertGreater(distance(a,b),1e-7,weapon)
   rest=rig.rest_joints(d,{})
   for p in (0,1):
    j,active=rig.joints(d,{},p,c);self.assertEqual(j,rest);self.assertFalse(active)
 def test_shared_source_selection_is_explicit(self):
  for weapon in ('beloved','gnawing_hunger'):
   with self.assertRaisesRegex(ValueError,'rigAction'):
    rig.joints(self.rigs[weapon],{},.5,{'weapon':weapon})
 def test_first_in_last_out_port_pose_survives_repeated_inserts(self):
  d=self.rigs['first_in_last_out']
  def pose(phase,p):return rig.joints(d,{},p,{'weapon':'first_in_last_out','insertPhase':phase})[0]
  a=pose('initial',1)
  for phase,p in [('loop',0),('loop',1),('return',0)]:self.assertLess(distance(a,pose(phase,p)),1e-12)
  self.assertGreater(distance(a,pose('loop',.5)),1e-4)
  self.assertEqual(pose('initial',0),rig.rest_joints(d,{}));self.assertEqual(pose('return',1),rig.rest_joints(d,{}))

if __name__=='__main__':unittest.main()
