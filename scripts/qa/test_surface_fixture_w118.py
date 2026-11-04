"""Read-only A/B pack checks; does not start Minecraft or mutate product assets."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('fixture', Path(__file__).with_name('prepare_surface_fixture_w118.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SurfaceFixtureTests(unittest.TestCase):
    def setUp(self):
        self.files = m.build()

    def test_exactly_six_models_six_items_two_frozen_atlases_and_metadata(self):
        self.assertEqual(15, len(self.files))
        self.assertEqual(6, sum('/models/' in p for p in self.files))
        self.assertEqual(6, sum('/items/' in p for p in self.files))
        self.assertEqual(2, sum('/textures/' in p for p in self.files))
        self.assertTrue(all(p == 'pack.mcmeta' or p.startswith('assets/w118qa/') for p in self.files))

    def test_original_means_exact_current_canonical_not_raw_fbx(self):
        for weapon, family in [('blast_furnace', 'pulse_rifle'), ('hammerhead', 'machine_gun')]:
            self.assertEqual((m.RES/f'assets/destiny/models/weapon/{family}/{weapon}.json').read_bytes(),
                             self.files[f'assets/w118qa/models/{weapon}_original.json'])

    def test_revised_is_exact_product_candidate_with_unchanged_display(self):
        for weapon in ('blast_furnace', 'hammerhead'):
            raw = (m.RES/f'assets/destiny/models/weapon_surface_w115/{weapon}.json').read_bytes()
            self.assertEqual(raw, self.files[f'assets/w118qa/models/{weapon}_revised.json'])
            original = json.loads(self.files[f'assets/w118qa/models/{weapon}_original.json'])
            self.assertEqual(original['display'], json.loads(raw)['display'])

    def test_frozen_r4_keeps_its_own_pixels_and_geometry_not_r5_atlas(self):
        pins = json.loads((m.FROZEN/'SHA256SUMS.json').read_text())
        for weapon in ('blast_furnace', 'hammerhead'):
            raw = self.files[f'assets/w118qa/textures/item/prior_r4/{weapon}.png']
            self.assertEqual(pins[weapon+'.png'], hashlib.sha256(raw).hexdigest())
            old = json.loads((m.FROZEN/(weapon+'.json')).read_bytes())
            candidate = json.loads(self.files[f'assets/w118qa/models/{weapon}_prior_r4.json'])
            self.assertTrue(all(t == 'w118qa:item/prior_r4/'+weapon for t in candidate.pop('textures').values()))
            old.pop('textures')
            self.assertEqual(old, candidate)

    def test_each_item_resolves_to_its_own_model_without_swap_animation(self):
        for path, raw in self.files.items():
            if '/items/' not in path:
                continue
            item = json.loads(raw)
            self.assertIs(False, item['hand_animation_on_swap'])
            key = path.split('/')[-1][:-5]
            self.assertEqual({'type': 'minecraft:model', 'model': 'w118qa:'+key}, item['model'])
            self.assertIn(f'assets/w118qa/models/{key}.json', self.files)

    def test_output_is_deterministic_and_build_does_not_write_runtime_pack(self):
        with patch.object(m, 'OUTPUT', Path('/nonexistent/never-written/resources.zip')):
            self.assertEqual(self.files, m.build())

    def test_frozen_textures_are_in_vanilla_item_atlas_directory(self):
        # Native PNG caught missing-texture magenta when this was /textures/prior_r4.
        for path in self.files:
            if '/textures/' in path:
                self.assertTrue(path.startswith('assets/w118qa/textures/item/'), path)
        for weapon in ('blast_furnace', 'hammerhead'):
            model=json.loads(self.files[f'assets/w118qa/models/{weapon}_prior_r4.json'])
            for ref in model['textures'].values():
                namespace, texture=ref.split(':')
                self.assertIn(f'assets/{namespace}/textures/{texture}.png', self.files)

    def test_frozen_hash_drift_is_rejected(self):
        read_bytes = Path.read_bytes
        def changed(path):
            raw = read_bytes(path)
            return raw+b'bad' if path == m.FROZEN/'hammerhead.png' else raw
        with patch.object(Path, 'read_bytes', changed), self.assertRaises(AssertionError):
            m.build()


if __name__ == '__main__':
    unittest.main(verbosity=2)
