"""A source-chain upgrade must not erase the bow's real string draw offset."""
import copy,json,sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import build_first_person_hands_w201 as hands
import first_person_framing_w205 as framing
import rig_arms_w205 as rig

class BowContactsW222(unittest.TestCase):
    def test_full_chain_keeps_string_travel_and_lower_riser_without_mutating_contacts(self):
        all_contacts=json.loads((ROOT/'art/weapons/w201/contacts.json').read_text())['weapons']
        settings=framing.load();rigs,_=rig.load()
        for weapon,distance in [('biting_winds',4.8),('whispering_slab',3.4)]:
            with self.subTest(weapon=weapon):
                config={**all_contacts[weapon],'framing':framing.profile(settings,weapon,'bow')}
                original=copy.deepcopy(config)
                neutral=hands.source_mesh_contacts(config,1.,0.)
                drawn=hands.source_mesh_contacts(config,1.,distance)
                accepted_left=framing.contact(config,'left')
                self.assertAlmostEqual(accepted_left['position'][1]-.6,drawn['left']['position'][1])
                self.assertEqual(neutral['left'],drawn['left'])
                body={ctx:{'rotation':[12.,-17.,8.],'translation':[1.,2.,3.],'scale':[.8,.8,.8]} for ctx in hands.FP}
                a=rig.source_palm_translations(rigs[weapon],{},None,config,body,neutral,hands.xyz,hands.vec)
                b=rig.source_palm_translations(rigs[weapon],{},None,config,body,drawn,hands.xyz,hands.vec)
                expected=hands.vec(hands.xyz([12.,-17.,8.]),[0.,0.,distance*.8])
                for ctx in hands.FP:
                    self.assertEqual(a['left'][ctx],b['left'][ctx])
                    for axis in range(3):self.assertAlmostEqual(expected[axis],b['right'][ctx][axis]-a['right'][ctx][axis],places=6)
                self.assertEqual(original,config)

if __name__=='__main__':unittest.main(verbosity=2)
