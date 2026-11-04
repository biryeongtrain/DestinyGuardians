import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('assembly',Path(__file__).resolve().parents[1]/'generate_surface_pack_w115.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ReviewedBudgetTests(unittest.TestCase):
 def test_r5_bf_increase_is_explicit_not_retroactive(self):
  self.assertEqual([m.review_budget('blast_furnace',r) for r in (2,3,4,5)],[4608,4608,4608,6144])
  self.assertEqual([m.review_budget('hammerhead',r) for r in (2,3,4,5)],[4608,6144,6144,6144])
 def test_unreviewed_revision_still_rejected(self):
  for r in (0,1,6,999):
   with self.assertRaises(AssertionError):m.review_budget('blast_furnace',r)
if __name__=='__main__':unittest.main(verbosity=2)
