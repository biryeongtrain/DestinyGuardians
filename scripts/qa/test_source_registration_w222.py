"""Rigid mesh registration must preserve source wrist travel and real lengths."""
import copy,json,sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import rig_arms_w205 as rig
import first_person_framing_w205 as framing
from build_first_person_hands_w201 import xyz,mul,euler,vec,FP

class SourceRegistrationW222(unittest.TestCase):
    def config(self):
        c=json.loads((ROOT/'art/weapons/w201/contacts.json').read_text())['weapons']['nezarec_s_whisper']
        settings=framing.load()
        c=framing.contacts(settings,'nezarec_s_whisper',c)
        c['framing']=framing.profile(settings,'nezarec_s_whisper',c['family'])
        self.assertTrue(c['framing']['sourceMeshPivot'])
        return c,rig.load()[0]['nezarec_s_whisper']

    def test_registered_palm_replays_actual_source_world_travel_for_all61poses(self):
        c,data=self.config();original=copy.deepcopy(c)
        rest=rig.rest_joints(data,{})
        basis=rig.source_mesh_basis(c,mul)
        source_line=vec(basis,vec(rig.transpose(rig.weapon_basis(rest)),rig.sub(rig.pos(rest['leftWrist']),rig.pos(rest['rightWrist']))))
        target=rig.sub(c['left']['position'],c['right']['position'])
        self.assertGreater(rig.dot(rig.unit(source_line),rig.unit(target)),1-1e-8)
        ready={ctx:{'rotation':[7.,-11.,13.],'translation':[1.,2.,3.],'scale':[.7,.7,.7]} for ctx in FP}
        contacts={side:framing.contact(c,side) for side in ('right','left')}
        settled=rig.source_palm_translations(data,{},None,c,ready,contacts,xyz,vec)
        parent=mul(mul(xyz(ready[FP[0]]['rotation']),basis),rig.transpose(rig.weapon_basis(rest)))
        for index in range(61):
            p=index/60;current,_=rig.joints(data,{},p,c)
            body=rig.source_weapon_display(data,{},p,c,ready,ready,ready,xyz,mul,euler,vec)
            actual=rig.source_palm_translations(data,{},p,c,body,contacts,xyz,vec)
            # Independent armature-space oracle: the accepted rest palm plus
            # actual source world wrist travel through ONE fixed rigid basis.
            travel=vec(parent,rig.sub(rig.pos(current['rightWrist']),rig.pos(rest['rightWrist'])))
            for ctx in FP:
                for axis in range(3):
                    self.assertAlmostEqual(settled['right'][ctx][axis]+32*.7*travel[axis],actual['right'][ctx][axis],places=6)
            for side in ('left','right'):
                limb=rig.sub(rig.pos(current[side+'Wrist']),rig.pos(current[side+'Elbow']))
                self.assertAlmostEqual(rig.norm(limb),rig.norm(vec(basis,limb)),places=9)
        self.assertEqual(original,c)

    def test_bad_basis_cannot_scale_reflect_or_corrupt_source_motion(self):
        for q in ([[2,0,0],[0,1,0],[0,0,1]],[[-1,0,0],[0,1,0],[0,0,1]],[[float('nan'),0,0],[0,1,0],[0,0,1]]):
            with self.assertRaises(ValueError):rig.source_mesh_basis({'framing':{'sourceMeshBasis':q}},mul)
        self.assertEqual(rig.C,rig.source_mesh_basis({},mul))

if __name__=='__main__':unittest.main(verbosity=2)
