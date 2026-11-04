"""Regression: rocket rounds follow original RIGHT loading palm, never the stabilizer."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reload_hand_w218 as hand

class ReloadHandW218(unittest.TestCase):
    def setUp(self):
        self.palms={'right':{'fp':{'translation':[10,6,-2]}},'left':{'fp':{'translation':[-10,2,8]}}}
        self.target={'fp':{'translation':[2,4,0]}}
    def test_rocket_payload_uses_right_hand_not_stationary_left(self):
        self.assertEqual({'fp':[8,2,-2]},hand.attached_translation_shift({'hand':'right'},self.palms,self.target,1,['fp']))
    def test_existing_routes_keep_left_hand_default(self):
        self.assertEqual('left',hand.side({}))
        self.assertEqual({'fp':[-12,-2,8]},hand.attached_translation_shift({},self.palms,self.target,1,['fp']))
    def test_seated_release_is_body_relative_and_blend_is_bounded(self):
        self.assertEqual({'fp':[0,0,0]},hand.attached_translation_shift({'hand':'right'},self.palms,self.target,0,['fp']))
        self.assertEqual({'fp':[4,1,-1]},hand.attached_translation_shift({'hand':'right'},self.palms,self.target,.5,['fp']))
    def test_invalid_side_or_weight_fails_instead_of_silent_wrong_hand(self):
        for value in ('both','',None):
            with self.assertRaises(ValueError):hand.side({'hand':value})
        for value in (-1,1.1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):hand.attached_translation_shift({},self.palms,self.target,value,['fp'])

if __name__=='__main__':unittest.main(verbosity=2)
