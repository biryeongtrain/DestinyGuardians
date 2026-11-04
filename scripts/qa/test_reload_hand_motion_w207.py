#!/usr/bin/env python3
"""Plain Python regression for interpolated arm FK and reload lifecycle."""
import copy
import math
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import rig_arms_w205 as rig


def matrix(angle=0,x=0):
 c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
 return [[c,-s,0,x],[s,c,0,0],[0,0,1,0],[0,0,0,1]]


def distance(a,b):
 return max(abs(x-y) for n in a for row,row2 in zip(a[n],b[n]) for x,y in zip(row,row2))


class ReloadHandMotion(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rigs,_=rig.load()

 def test_subsample_positions_and_short_rotation_arc(self):
  action={'frames':[{'progress':0,'joints':{'wrist':matrix(170,0)}},
                    {'progress':.4,'joints':{'wrist':matrix(-170,4)}}]}
  mid=rig.sample(action,.2)['wrist']
  self.assertAlmostEqual(mid[0][3],2)
  self.assertLess(mid[0][0],-.999)
  self.assertNotEqual(rig.sample(action,.1)['wrist'][0][3],mid[0][3])

 def test_whole_reload_settles_to_idle_without_endpoint_pop(self):
  data=self.rigs['ace_of_spades'];rest=rig.rest_joints(data,{})
  for p in (0,1):
   j,dynamic=rig.joints(data,{},p)
   self.assertFalse(dynamic);self.assertEqual(j,rest)
  for p in (1e-7,1-1e-7):
   j,_=rig.joints(data,{},p);self.assertLess(distance(j,rest),2e-6) # Evaluated matrices have sub-micro scale/shear noise.
  # Old nearest sampling held this entire interval on the same source pose.
  a,_=rig.joints(data,{},.41);b,_=rig.joints(data,{},.42)
  self.assertGreater(distance(a,b),1e-5)

 def test_five_routes_and_ambiguous_action_requires_selection(self):
  routes=[('ammit_ar2','80A8A38A'),('blast_furnace','80A8A366'),
          ('hammerhead','80A8A005'),('dust_rock_blues','80A8A3F1'),
          ('izanagis_burden','80A8A140')]
  for weapon,tag in routes:
   cfg={'weapon':weapon,'reload':{'rigAction':tag},'insertPhase':'loop'}
   a,dynamic=rig.joints(self.rigs[weapon],{},.43,cfg)
   b,_=rig.joints(self.rigs[weapon],{},.44,cfg)
   self.assertTrue(dynamic);self.assertGreater(distance(a,b),1e-7)
  with self.assertRaisesRegex(ValueError,'rigAction'):
   rig.joints(self.rigs['ammit_ar2'],{},.5,{'weapon':'ammit_ar2'})

 def test_izanagi_honed_and_charged_lifecycle(self):
  data=self.rigs['izanagis_burden']
  ordinary,_=rig.joints(data,{6:.5},.5)
  honed,_=rig.joints(data,{6:2.5},.5)
  self.assertGreater(distance(ordinary,honed),1e-4)
  charged,dynamic=rig.joints(data,{6:4},.5)
  self.assertFalse(dynamic);self.assertEqual(charged,rig.rest_joints(data,{}))

 def test_dust_phase_boundaries_hold_source_pose_until_return(self):
  data=self.rigs['dust_rock_blues']
  def pose(phase,p):return rig.joints(data,{},p,{'weapon':'dust_rock_blues','insertPhase':phase})[0]
  rest=rig.rest_joints(data,{})
  self.assertEqual(pose('initial',0),rest)
  self.assertEqual(pose('return',1),rest)
  port=pose('initial',1)
  self.assertGreater(distance(port,rest),1e-4)
  for phase,p in [('loop',0),('loop',1),('return',0)]:
   self.assertLess(distance(port,pose(phase,p)),1e-12)
  self.assertGreater(distance(port,pose('loop',.5)),1e-4)

 def test_mesh_contact_preserved_and_ordinary_length_constant(self):
  data=self.rigs['izanagis_burden'];contexts=('firstperson_righthand','firstperson_lefthand')
  def identity(_):return [[1,0,0],[0,1,0],[0,0,1]]
  def mul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
  def vec(a,b):return [sum(a[i][k]*b[k] for k in range(3)) for i in range(3)]
  scales=[]
  for progress in (.2,.5,.8):
   base={c:{'translation':[1,2,3],'scale':[1,1,1],'rotation':[0,0,0]} for c in contexts}
   right,left=copy.deepcopy(base),copy.deepcopy(base)
   settings={'keepMeshSupport':True}
   rig.apply(data,{6:progress},progress,{'family':'sniper_rifle'},right,left,base,base,
             {c:identity(None) for c in contexts},settings,1,identity,mul,lambda m:m,vec)
   self.assertEqual(left[contexts[0]]['translation'],[1,2,3])
   scales.append(right[contexts[0]]['scale'][1])
  self.assertEqual(scales[0],scales[1]);self.assertEqual(scales[1],scales[2])
  # Non-opted-in Ace still uses evaluated changing wrist separation.
  ace=self.rigs['ace_of_spades'];j,_=rig.joints(ace,{},.5)
  right,left=copy.deepcopy(base),copy.deepcopy(base)
  rig.apply(ace,{},.5,{'family':'hand_cannon'},right,left,base,base,
            {c:identity(None) for c in contexts},{},1,identity,mul,lambda m:m,vec)
  delta=vec(rig.C,rig.sub(rig.pos(j['leftWrist']),rig.pos(j['rightWrist'])))
  for i in range(3):self.assertAlmostEqual(left[contexts[0]]['translation'][i],1+i+delta[i]*32,places=7)



if __name__=='__main__':unittest.main()
