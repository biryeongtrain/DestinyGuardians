"""Scoped dynamic bow integration regression; not native rendering evidence."""
import collections
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import generate_surface_bow_body_w147 as w

class BowBodyIntegration(unittest.TestCase):
    def test_actual_historical_dynamic_graph_and_states_unchanged(self):
        old=w.read(ROOT/'art/weapons/w50/manifest.json')
        for p,h in old['sha256'].items():
            self.assertEqual(h,w.sha((ROOT/p).read_bytes()),p)

    def test_rest_string_and_arrow_are_not_baked_into_rigid_body(self):
        for id in w.IDS:
            d=w.read(ROOT/f'art/weapons/w123/{id}/design.json')
            full=w.read(w.RES/f'assets/destiny/models/weapon_surface_w123/{id}.json')
            body=w.read(w.RES/f'assets/destiny/models/weapon_surface_w123/{id}_body_hip.json')
            names=set(d['moving_element_names'])
            self.assertEqual([e for e in full['elements'] if e['name'] not in names],body['elements'])
            self.assertFalse(names & {e['name'] for e in body['elements']})
            self.assertEqual(full['textures'],body['textures'])
            original=w.read(w.RES/f'assets/destiny/models/weapon/bow/{id}.json')
            _,moving=w.bow.parts(original,w.bow.CONFIG[id])
            self.assertEqual(collections.Counter(w.normalized(e,original['textures']) for e in moving),
                collections.Counter(w.normalized(e,full['textures']) for e in full['elements'] if e['name'] in names))

    def test_draw_and_nock_all_twenty_steps_remain_physical_motion(self):
        for id in w.IDS:
            base=w.RES/'assets/destiny/models/weapon_bow_w50'
            rest=w.read(base/f'{id}_loaded_hip.json')
            draw=w.read(base/f'{id}_draw_20_hip.json')
            self.assertNotEqual(rest['elements'],draw['elements'])
            for kind in ('draw','nock'):
                for i in range(21):
                    state=w.read(base/f'{id}_{kind}_{i:02}_hip.json')
                    body=w.read(w.RES/f'assets/destiny/models/weapon_surface_w123/{id}_body_hip.json')
                    self.assertLessEqual(len(state['elements'])+len(body['elements']),1000)
                    for pose in ('ads','inspect'):
                        child=w.read(base/f'{id}_{kind}_{i:02}_{pose}.json')
                        self.assertEqual(f'destiny:weapon_bow_w50/{id}_{kind}_{i:02}_hip',child['parent'])

    def test_new_body_displays_match_existing_active_bow_parents(self):
        for id in w.IDS:
            old=w.read(w.RES/f'assets/destiny/models/weapon_bow_w50/{id}_body_hip.json')
            new=w.read(w.RES/f'assets/destiny/models/weapon_surface_w123/{id}_body_hip.json')
            self.assertEqual(old['display'],new['display'])
            for pose in ('ads','inspect'):
                child=w.read(w.RES/f'assets/destiny/models/weapon_bow_w50/{id}_body_{pose}.json')
                self.assertEqual(f'destiny:weapon_bow_w50/{id}_body_hip',child['parent'])

    def test_generator_is_deterministic_and_writes_only_replacement_bodies(self):
        out=w.generate();self.assertEqual(out,w.generate())
        self.assertEqual(3,len(out))
        for p,b in out.items():
            self.assertNotIn('assets/destiny/models/weapon_bow_w50/',p)
            self.assertEqual(b,(ROOT/p).read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)
