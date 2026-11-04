"""The new art revision does not loosen historical geometry budgets or change R3 bytes."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('surface_pack',ROOT/'scripts/generate_surface_pack_w115.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)

class SurfaceAssemblyTests(unittest.TestCase):
    def test_reviewed_r4_budget_is_same_as_r3_not_engine_limit(self):
        for weapon in M.WEAPONS:
            self.assertEqual(M.review_budget(weapon,4),M.review_budget(weapon,3))
        self.assertEqual(M.review_budget('blast_furnace',4),4608)
        self.assertEqual(M.review_budget('hammerhead',4),6144)
        self.assertEqual(M.review_budget('hammerhead',2),4608)

    def test_unknown_weapon_or_revision_cannot_silently_gain_budget(self):
        for args in [('other',4),('hammerhead',6),('blast_furnace',1)]:
            with self.assertRaises(AssertionError):M.review_budget(*args)

    def test_only_known_art_revisions_are_parsed(self):
        with tempfile.TemporaryDirectory(prefix='w117-art-revision-') as t:
            root=Path(t);p=root/'art/weapons/w115/hammerhead/manifest.json';p.parent.mkdir(parents=True)
            with patch.object(M,'ROOT',root):
                for raw,expected in [('r2',2),(2,2),('r3',3),('r4',4),('r4-fit',4),('r5',5),('r5-contour',5)]:
                    p.write_text(json.dumps(dict(revision=raw)))
                    self.assertEqual(M.art_revision('hammerhead'),expected)
                for raw in ['r1','r6','r4unreviewed',None,True]:
                    p.write_text(json.dumps(dict(revision=raw)))
                    with self.assertRaises(AssertionError):M.art_revision('hammerhead')

    def test_current_assembly_remains_deterministic_and_historical_sources_pinned(self):
        first=M.generate();second=M.generate()
        self.assertEqual(first,second)
        self.assertEqual(len(first),3)
        for path,expected in M.PINS.items():self.assertEqual(M.sha((M.RES/path).read_bytes()),expected)
        manifest=json.loads(first[M.RES/'weapon_surface_w115/manifest.json'])
        self.assertEqual(len(manifest['targets']),7)
        self.assertEqual({r['path'] for r in manifest['targets']},set(M.PINS))

if __name__=='__main__':unittest.main(verbosity=2)
