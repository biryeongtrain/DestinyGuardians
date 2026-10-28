"""New weapon bindings must reach evaluated reload motion, not silently idle."""
import sys
import unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import rig_arms_w205 as rig
import first_person_framing_w205 as framing

class SourceBindingsW212(unittest.TestCase):
    def test_new_profiles_use_real_dense_motion_and_restore_rest(self):
        rigs,_=rig.load();profiles=framing.load()
        for weapon in ('antiope_d','bug_out_bag','cold_denial','bygones','lonesome','steelfeather_repeater','aishas_embrace','chattering_bone','halfdan_d','claws_of_the_wolf','bite_of_the_fox','retrofit_escapade','duke_mk_44','farewell','apostate','fixed_odds','distant_relation','patron_of_lost_causes','brass_attacks','ikelos_smg_v1_0_1','erentil_fr4','hollow_words','dream_breaker','null_composure','coriolis_force','line_in_the_sand','stormchaser','code_duello','bellowing_giant','bad_omens','allied_demand','dead_man_walking_xx7463','high_albedo','frontier_justice','retraced_path','edge_transit','canis_major','dimensional_hypotrochoid','deafening_whisper','salvager_s_salvo','ikelos_sg_v1_0_1','mindbender_s_ambition_adept','parcel_of_stardust_fell_to_earth','pyroclastic_flow','seventh_seraph_officer_revolver'):
            with self.subTest(weapon=weapon):
                data=rigs[weapon]
                reload=profiles['contactOverrides'][weapon]['reload']
                config={'weapon':weapon,'reload':reload}
                self.assertEqual(61,len(data['actions'][reload['rigAction']]['frames']))
                self.assertTrue(profiles['weapons'][weapon]['sourceFullChain'])
                self.assertIn('leftShoulder',data['names'])
                shell=weapon in ('ikelos_sg_v1_0_1','mindbender_s_ambition_adept','parcel_of_stardust_fell_to_earth')
                if shell:config['insertPhase']='initial'
                # These shell actions deliberately hold the port pose after
                # .36; test the moving initial slice, not that calibrated hold.
                a,dynamic=rig.joints(data,{},.21 if shell else .41,config)
                b,_=rig.joints(data,{},.22 if shell else .42,config)
                self.assertTrue(dynamic)
                self.assertGreater(max(abs(a[k][i][3]-b[k][i][3]) for k in ('weapon','leftWrist','rightWrist') for i in range(3)),1e-6)
                for p in (0,1):
                    if shell:config['insertPhase']='initial' if p==0 else 'return'
                    settled,active=rig.joints(data,{},p,config)
                    self.assertFalse(active)
                    self.assertEqual(rig.rest_joints(data,{}),settled)

if __name__=='__main__':unittest.main(verbosity=2)
