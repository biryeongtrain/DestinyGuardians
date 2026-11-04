import copy,json,runpy,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/"scripts/generate_ace_sight_w156.py"))
H=runpy.run_path(str(ROOT/"scripts/art/build_ace_w83.py"))
R=runpy.run_path(str(ROOT/"scripts/generate_sight_bodies_w151_handguns.py"))
A=G["A"]
class AceSight(unittest.TestCase):
    def setUp(self):
        self.outputs=G["generate"]()
        self.body=json.loads(self.outputs[A/"models/weapon_sight_w156/ace_of_spades_body.json"])
    def test_canonical_geometry_and_uv_are_preserved(self):
        old=json.loads((A/"models/item/weapon/ace_of_spades.json").read_bytes())
        self.assertEqual(self.body["elements"][:87],old["elements"])
        self.assertEqual(len(self.body["elements"]),92)
        self.assertEqual(self.body["textures"],old["textures"])
    def test_ray_is_above_body_not_through_rear_block(self):
        center=G["CENTER"];eye=[center[0],center[1],center[2]+G["EYE"]*16/G["SCALE"]]
        # All retained parts and new notch remain clear, no exempted geometry.
        for dx in (-.025,0,.025):
            for dy in (-.025,0,.025):
                for e in self.body["elements"]:
                    self.assertIsNone(R["ray_hit"](e,eye,[dx/(eye[2]-center[2]),dy/(eye[2]-center[2]),-1]))
    def test_both_hands_center_front_and_rear(self):
        frame=json.loads(self.outputs[A/"models/weapon_sight_w156/ace_of_spades_20_native.json"])
        for left,ctx in enumerate(G["FP"]):
            for p in (G["CENTER"],[8,G["CENTER"][1],G["FRONT_Z"]]):
                v=H["item_point"](p,frame["display"][ctx],bool(left))
                v=[v[0]+(-8.96 if left else 8.96),v[1]-8.32,v[2]-11.52]
                self.assertAlmostEqual(v[0],0,places=7);self.assertAlmostEqual(v[1],0,places=7)
                self.assertLessEqual(v[2]/16,-.42+1e-7)
    def test_graph_maps_all_42_frames_and_preserves_other_contexts(self):
        graph=json.loads(self.outputs[A/"items/weapon_sight_w156/ace_of_spades.json"])
        refs=[]
        def walk(v):
            if isinstance(v,dict):
                if v.get("type")=="minecraft:model":refs.append(v["model"])
                for x in v.values():walk(x)
            elif isinstance(v,list):
                for x in v:walk(x)
        walk(graph)
        self.assertEqual(len(set(x for x in refs if x.startswith("destiny:weapon_sight_w156/"))),42)
        self.assertFalse(any("item/weapon_aim_w70" in x for x in refs))
        source=json.loads((A/"models/item/weapon/ace_of_spades.json").read_bytes())
        for f in range(21):
            d=json.loads(self.outputs[A/f"models/weapon_sight_w156/ace_of_spades_{f:02}_native.json"])
            for ctx,p in source["display"].items():
                if ctx not in G["FP"]:self.assertEqual(d["display"][ctx],p)
    def test_written_bytes_reconstruct(self):
        for p,b in self.outputs.items():self.assertEqual(p.read_bytes(),b,str(p))
if __name__=="__main__":unittest.main(verbosity=2)
