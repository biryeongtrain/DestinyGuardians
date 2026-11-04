#!/usr/bin/env python3
"""Mesh-contact frames must survive FK retargeting in ready, ADS and reload."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import first_person_framing_w205 as framing
import rig_arms_w205 as rig
import build_first_person_hands_w201 as hands

class MeshContacts(unittest.TestCase):
 def test_two_hands_and_mesh_frames_for_both_families(self):
  data=framing.load()
  for weapon,family in [('ace_of_spades','hand_cannon'),('austringer','hand_cannon'),('duke_mk_44','hand_cannon'),('seventh_seraph_officer_revolver','hand_cannon'),('the_recluse','submachine_gun'),('antiope_d','submachine_gun'),('bug_out_bag','submachine_gun'),('ikelos_smg_v1_0_1','submachine_gun')]:
   cfg=framing.profile(data,weapon,family)
   self.assertFalse(cfg.get('hideSupportAtRest'),weapon)
   self.assertTrue(cfg['keepMeshSupport'],weapon)
   self.assertTrue(cfg['meshArmDirections'],weapon)
   self.assertTrue(cfg['sourceWeaponRelative'],weapon)
 def test_contact_translation_rotation_and_normal_length_survive_fk(self):
  rigs,_=rig.load();contexts=hands.FP
  for weapon,family,tag in [('the_recluse','submachine_gun','80A8A192'),('austringer','hand_cannon','80A8A53D'),('ace_of_spades','hand_cannon','80A8A567')]:
   for state,p in [({},None),({'mode':'ads'},None),({},.2),({},.5),({},.9)]:
    base={c:{'translation':[1,2,3],'rotation':[15,-10,25],'scale':[.8,.8,.8]} for c in contexts}
    right,left=copy.deepcopy(base),copy.deepcopy(base)
    left[contexts[0]]['translation']=[-3,4,8]
    before=copy.deepcopy((right,left))
    rig.apply(rigs[weapon],state,p,{'weapon':weapon,'family':family,'reload':{'rigAction':tag}},right,left,base,base,{c:hands.xyz([0,0,0]) for c in contexts},{'meshArmDirections':True,'keepMeshSupport':True},1,hands.xyz,hands.mul,hands.euler,hands.vec)
    for old,new in zip(before,(right,left)):
     for c in contexts:
      self.assertEqual(old[c]['translation'],new[c]['translation'])
      self.assertEqual(old[c]['rotation'],new[c]['rotation'])
      self.assertEqual(old[c]['scale'][::2],new[c]['scale'][::2])
    rest=rig.rest_joints(rigs[weapon],state)
    expected=rig.norm(rig.sub(rig.pos(rest['leftWrist']),rig.pos(rest['leftElbow'])))*32/6.5*.8
    self.assertAlmostEqual(left[contexts[0]]['scale'][1],expected,places=7)

class SourceWeaponRelative(unittest.TestCase):
 def test_shell_hold_keeps_body_and_limb_samples_together_at_phase_seams(self):
  rigs,_=rig.load();data=rigs['first_in_last_out']
  cfg={'weapon':'first_in_last_out','reload':{'rigAction':'80A8A3F1','sourceShellPoseHold':True}}
  def at(phase,p):return rig.joints(data,{},p,{**cfg,'insertPhase':phase})[0]
  held=at('initial',1)
  for p in (0,.2,.4,.6,.8,1):
   self.assertEqual(at('loop',p),held)
  self.assertEqual(at('return',0),held)
  self.assertEqual(at('return',1),rig.rest_joints(data,{}))
  middle=at('return',.5)
  self.assertNotEqual(middle,held)
  self.assertNotEqual(middle,rig.rest_joints(data,{}))
 def test_source_wrist_travel_is_not_pinned_to_authored_reload_target(self):
  rigs,_=rig.load();data=rigs['austringer'];cfg={'weapon':'austringer','reload':{'rigAction':'80A8A53D'}}
  body={c:{'translation':[3,-2,1],'rotation':[0,0,0],'scale':[.7,.7,.7]} for c in hands.FP}
  contacts={s:{'position':[8,8,8]} for s in ('right','left')}
  at_rest=rig.source_palm_translations(data,{},None,cfg,body,contacts,hands.xyz,hands.vec)
  self.assertEqual(at_rest['left'][hands.FP[0]],body[hands.FP[0]]['translation'])
  active_body=rig.source_weapon_display(data,{},.3,cfg,body,body,body,hands.xyz,hands.mul,hands.euler,hands.vec)
  moving=rig.source_palm_translations(data,{},.3,cfg,active_body,contacts,hands.xyz,hands.vec)
  # Actual source reload puts the support wrist below the raised gun.
  # Pinning it to the cylinder instead put its shoulder into the sky.
  self.assertLess(moving['left'][hands.FP[0]][1],at_rest['left'][hands.FP[0]][1]-5)
  self.assertGreater(rig.norm(rig.sub(moving['left'][hands.FP[0]],at_rest['left'][hands.FP[0]])),5)
 def test_source_weapon_and_forearms_share_one_calibrated_parent(self):
  rigs,_=rig.load()
  for weapon,tag in [('the_recluse','80A8A192'),('austringer','80A8A53D')]:
   data=rigs[weapon];cfg={'weapon':weapon,'family':'submachine_gun' if weapon=='the_recluse' else 'hand_cannon','reload':{'rigAction':tag}}
   ready={c:{'translation':[3,-2,1],'rotation':[-8,14,3],'scale':[.7,.7,.7]} for c in hands.FP}
   authored={c:{'translation':[5,4,-1],'rotation':[55,-10,38],'scale':[.7,.7,.7]} for c in hands.FP}
   for p in (.2,.5,.8):
    body=rig.source_weapon_display(data,{},p,cfg,authored,ready,authored,hands.xyz,hands.mul,hands.euler,hands.vec)
    right,left=copy.deepcopy(authored),copy.deepcopy(authored)
    rig.apply(data,{},p,cfg,right,left,authored,body,{c:hands.xyz([0,0,0]) for c in hands.FP},{'sourceFullChain':True,'keepMeshSupport':True},1,hands.xyz,hands.mul,hands.euler,hands.vec)
    current,_=rig.joints(data,{},p,cfg);rest=rig.rest_joints(data,{})
    parent=hands.mul(hands.mul(hands.xyz(ready[hands.FP[0]]['rotation']),rig.C),rig.transpose(rig.weapon_basis(rest)))
    for side,display in [('right',right),('left',left)]:
     source=hands.vec(parent,rig.unit(rig.sub(rig.pos(current[side+'Wrist']),rig.pos(current[side+'Elbow']))))
     actual=hands.vec(hands.xyz(display[hands.FP[0]]['rotation']),[0,1,0])
     self.assertLess(max(abs(a-b) for a,b in zip(source,actual)),1e-7)
     self.assertEqual(display[hands.FP[0]]['translation'],authored[hands.FP[0]]['translation'])
 def test_source_body_replacement_retains_relative_moving_part_turn(self):
  rigs,_=rig.load();data=rigs['the_recluse'];cfg={'weapon':'the_recluse','reload':{'rigAction':'80A8A192'}}
  body={c:{'translation':[1,2,3],'rotation':[45,10,-8],'scale':[.7,.7,.7]} for c in hands.FP}
  ready={c:{'translation':[3,-2,1],'rotation':[-8,14,3],'scale':[.7,.7,.7]} for c in hands.FP}
  part=copy.deepcopy(body)
  for c in hands.FP:
   part[c]['rotation']=hands.euler(hands.mul(hands.xyz(body[c]['rotation']),hands.xyz([20,-15,5])))
   offset=hands.vec(hands.xyz(body[c]['rotation']),[1,-3,2])
   part[c]['translation']=[body[c]['translation'][i]+offset[i] for i in range(3)]
  b=rig.source_weapon_display(data,{},.47,cfg,body,ready,body,hands.xyz,hands.mul,hands.euler,hands.vec)
  p=rig.source_weapon_display(data,{},.47,cfg,body,ready,part,hands.xyz,hands.mul,hands.euler,hands.vec)
  for c in hands.FP:
   inverse=rig.transpose(hands.xyz(b[c]['rotation']));relative=hands.mul(inverse,hands.xyz(p[c]['rotation']))
   offset=hands.vec(inverse,rig.sub(p[c]['translation'],b[c]['translation']))
   self.assertLess(max(abs(a-b) for a,b in zip(offset,[1,-3,2])),1e-7)
   self.assertLess(max(abs(relative[i][j]-hands.xyz([20,-15,5])[i][j]) for i in range(3) for j in range(3)),1e-7)
 def test_upper_arm_connects_to_elbow_and_keeps_source_length(self):
  rigs,_=rig.load()
  for weapon,tag in [('the_recluse','80A8A192'),('austringer','80A8A53D')]:
   data=rigs[weapon]
   for p in (None,.1,.4,.7,1):
    base={c:{'translation':[1,2,3],'rotation':[15,-10,25],'scale':[.8,.8,.8]} for c in hands.FP}
    right,left=copy.deepcopy(base),copy.deepcopy(base)
    cfg={'weapon':weapon,'family':'submachine_gun' if weapon=='the_recluse' else 'hand_cannon','reload':{'rigAction':tag}}
    rig.apply(data,{},p,cfg,right,left,base,base,{c:hands.xyz([0,0,0]) for c in hands.FP},{'meshArmDirections':True,'sourceWeaponRelative':True,'keepMeshSupport':True},1,hands.xyz,hands.mul,hands.euler,hands.vec)
    upper=rig.upper_arm_displays(data,{},p,cfg,right,left,hands.xyz,hands.mul,hands.euler,hands.vec)
    for side,forearm in [('right',right),('left',left)]:
     rest=rig.rest_joints(data,{})
     length=rig.norm(rig.sub(rig.pos(rest[side+'Elbow']),rig.pos(rest[side+'Shoulder'])))*32*.8
     for c in hands.FP:
      f=forearm[c];offset=hands.vec(hands.xyz(f['rotation']),[0,-6.5*f['scale'][1],0])
      expected=[f['translation'][i]+offset[i] for i in range(3)]
      self.assertLess(max(abs(a-b) for a,b in zip(upper[side][c]['translation'],expected)),1e-7)
      self.assertAlmostEqual(upper[side][c]['scale'][1]*7.5,length,places=7)
 def test_no_upper_arm_without_source_shoulder(self):
  rigs,_=rig.load()
  legacy=copy.deepcopy(rigs['ace_of_spades'])
  # Explicit legacy fixture: W210 also evaluates Ace shoulders.
  for action in legacy['actions'].values():
   for frame in action['frames']:
    for side in ('right','left'):frame['joints'].pop(side+'Shoulder',None)
  self.assertEqual(rig.upper_arm_displays(legacy,{},None,{}, {},{},hands.xyz,hands.mul,hands.euler,hands.vec),{})
 def test_active_handling_frame_keeps_precomposed_part_turn(self):
  rigs,_=rig.load();data=rigs['the_recluse']
  base={c:{'translation':[1,2,3],'rotation':[0,0,0],'scale':[1,1,1]} for c in hands.FP}
  cfg={'weapon':'the_recluse','family':'submachine_gun','reload':{'rigAction':'80A8A192'}}
  outputs=[]
  for part_turn in (0,45):
   right,left=copy.deepcopy(base),copy.deepcopy(base)
   for c in hands.FP:left[c]['rotation']=[part_turn,0,0]
   rig.apply(data,{},.47,cfg,right,left,base,base,{c:hands.xyz([0,0,0]) for c in hands.FP},{'meshArmDirections':True,'sourceWeaponRelative':True,'keepMeshSupport':True},1,hands.xyz,hands.mul,hands.euler,hands.vec)
   self.assertEqual(left[hands.FP[0]]['translation'],[1,2,3])
   outputs.append(hands.xyz(left[hands.FP[0]]['rotation']))
  expected=hands.mul(outputs[0],hands.xyz([45,0,0]))
  self.assertLess(max(abs(outputs[1][i][j]-expected[i][j]) for i in range(3) for j in range(3)),1e-7)
 def test_source_weapon_axis_swing_is_independent_of_contact_calibration(self):
  rigs,_=rig.load();rest=rig.rest_joints(rigs['the_recluse'],{})
  source_swing=hands.xyz([0,0,35])
  w=rig.weapon_basis(rest)
  world_swing=hands.mul(hands.mul(w,source_swing),rig.transpose(w))
  current=copy.deepcopy(rest)
  origin=rig.pos(rest['weapon'])
  for name in ('rightElbow','rightWrist'):
   m=rest[name];upper=hands.mul(world_swing,[row[:3] for row in m[:3]])
   point=hands.vec(world_swing,rig.sub(rig.pos(m),origin))
   current[name]=[upper[i]+[point[i]+origin[i]] for i in range(3)]+[[0,0,0,1]]
  delta=rig.weapon_relative_delta(rest,current,'right',hands.mul)
  self.assertLess(max(abs(delta[i][j]-source_swing[i][j]) for i in range(3) for j in range(3)),1e-7)
  canonical=hands.mul(hands.mul(rig.C,delta),rig.transpose(rig.C))
  # Rotating around source Z must remain a canonical Y swing even when the
  # contact is rolled. It must not become a different per-hand rotation axis.
  for angles in ([0,0,0],[-30,0,35],[-25,0,-30]):
   contact=hands.xyz(angles);out=hands.mul(canonical,contact)
   swing=hands.mul(out,rig.transpose(contact))
   self.assertLess(max(abs(swing[i][j]-hands.xyz([0,35,0])[i][j]) for i in range(3) for j in range(3)),1e-7)
 def test_weapon_space_is_invariant_under_armature_global_rotation(self):
  rigs,_=rig.load()
  for weapon,tag in [('the_recluse','80A8A192'),('austringer','80A8A53D')]:
   data=rigs[weapon];rest=rig.rest_joints(data,{})
   current,_=rig.joints(data,{},.47,{'weapon':weapon,'reload':{'rigAction':tag}})
   rotation=hands.xyz([29,-43,17])
   def rotate(joints):
    result={}
    for name,m in joints.items():
     upper=hands.mul(rotation,[row[:3] for row in m[:3]])
     pos=hands.vec(rotation,rig.pos(m))
     result[name]=[upper[i]+[pos[i]+[4,-2,7][i]] for i in range(3)]+[[0,0,0,1]]
    return result
   for side in ('right','left'):
    delta=rig.weapon_relative_delta(rest,current,side,hands.mul)
    moved=rig.weapon_relative_delta(rotate(rest),rotate(current),side,hands.mul)
    self.assertLess(max(abs(delta[i][j]-moved[i][j]) for i in range(3) for j in range(3)),1e-7)
    identity=rig.weapon_relative_delta(rest,rest,side,hands.mul)
    self.assertLess(max(abs(identity[i][j]-(i==j)) for i in range(3) for j in range(3)),1e-7)
    self.assertGreater(max(abs(delta[i][j]-(i==j)) for i in range(3) for j in range(3)),.01)
 def test_wrist_twist_alignment_cannot_flip_forearm_basis(self):
  rigs,_=rig.load();j=rig.rest_joints(rigs['the_recluse'],{})
  expected=rig.forearm_basis(j,'left')
  changed=copy.deepcopy(j)
  # Hand articulation may point its X along the forearm. A forearm uses
  # elbow transverse Y, so this formerly near-singular wrist axis is irrelevant.
  direction=rig.unit(rig.sub(rig.pos(j['leftWrist']),rig.pos(j['leftElbow'])))
  for i in range(3):changed['leftWrist'][i][0]=direction[i]
  self.assertEqual(expected,rig.forearm_basis(changed,'left'))
 def test_source_reload_changes_orientation_without_detaching_mesh_palm(self):
  rigs,_=rig.load()
  data=rigs['the_recluse'];base={c:{'translation':[1,2,3],'rotation':[0,0,0],'scale':[1,1,1]} for c in hands.FP}
  cfg={'weapon':'the_recluse','family':'submachine_gun','right':{'rotation':[0,0,0]},'left':{'rotation':[0,0,0]},'reload':{'rigAction':'80A8A192'}}
  rotations=[]
  for p in [.3,.5,.7]:
   right,left=copy.deepcopy(base),copy.deepcopy(base)
   rig.apply(data,{},p,cfg,right,left,base,base,{c:hands.xyz([0,0,0]) for c in hands.FP},{'meshArmDirections':True,'sourceWeaponRelative':True,'keepMeshSupport':True},1,hands.xyz,hands.mul,hands.euler,hands.vec)
   self.assertEqual(left[hands.FP[0]]['translation'],[1,2,3])
   rotations.append(left[hands.FP[0]]['rotation'])
  self.assertGreater(max(abs(a-b) for a,b in zip(rotations[0],rotations[1])),1)

if __name__=='__main__':unittest.main()
