#!/usr/bin/env python3
"""Default-pack art -> HUD synchronization, separate from W118 historical masks."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('w137hud', ROOT / 'scripts/build_weapon_hud_w112.py')
hud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hud)


class HudSurfaceW137Test(unittest.TestCase):
    def test_current_masks_follow_every_registered_full_replacement(self):
        rules = hud.active_rules()
        records = {w['id']: w for w in hud.read_json(hud.HUD / 'manifest.json')['weapons']}
        replaced = set()
        for row in hud.catalog():
            canonical = hud.canonical_source_path(row)
            actual = rules.get(canonical, canonical)
            record = records[row['id']]
            self.assertEqual(str(canonical), record['canonical_model'])
            self.assertEqual(str(actual), record['source_model'])
            data = (ROOT / actual).read_bytes()
            self.assertEqual(hud.sha(data), record['source_sha256'])
            image, stats = hud.render(json.loads(data), row['family'])
            self.assertEqual(stats['alpha_sha256'], record['alpha_sha256'])
            self.assertEqual(hud.png_bytes(image), (ROOT / hud.pack_paths(row['id'])[2]).read_bytes())
            if actual != canonical:
                replaced.add(row['id'])
        expected = {p.stem for p in rules if '/models/weapon/' in str(p)}
        self.assertEqual(expected, replaced)

    def test_ace_izanagi_and_nonmigrated_sources_remain_canonical(self):
        rules = hud.active_rules()
        for row in hud.catalog():
            canonical = hud.canonical_source_path(row)
            if row['id'] in ('ace_of_spades', 'izanagis_burden') or canonical not in rules:
                self.assertEqual(canonical, hud.source_path(row, rules))

    def test_empty_mapping_does_not_activate_candidate_directory_files(self):
        row = next(r for r in hud.catalog() if r['id'] == 'ammit_ar2')
        self.assertNotEqual(hud.canonical_source_path(row), hud.source_path(row))
        self.assertEqual(hud.canonical_source_path(row), hud.source_path(row, {}))

    def test_stale_duplicate_missing_and_unsafe_declared_rules_do_not_fallback(self):
        original = hud.ROOT
        with tempfile.TemporaryDirectory(prefix='w137-hud-') as temp:
            hud.ROOT = Path(temp)
            canonical = 'assets/destiny/models/weapon/test/example.json'
            replacement = 'assets/destiny/models/weapon_surface_w123/example.json'
            for path, data in ((canonical, b'canonical'), (replacement, b'current')):
                p = hud.ROOT / 'src/main/resources' / path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
            rule = dict(path=canonical, sourceSha256=hud.sha(b'canonical'),
                        replacement=replacement, replacementSha256=hud.sha(b'current'))
            base = dict(schema=1, stage='W123', targets=[rule])
            manifest_path = hud.ROOT / hud.SURFACE_MANIFEST
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                manifest_path.write_text(json.dumps(base))
                self.assertEqual(1, len(hud.active_rules()))
                variants = []
                for field in ('sourceSha256', 'replacementSha256'):
                    bad = copy.deepcopy(base); bad['targets'][0][field] = '0' * 64; variants.append(bad)
                bad = copy.deepcopy(base); bad['targets'] *= 2; variants.append(bad)
                bad = copy.deepcopy(base); bad['targets'][0]['replacement'] = 'assets/destiny/models/../escaped.json'; variants.append(bad)
                bad = copy.deepcopy(base); bad['schema'] = 99; variants.append(bad)
                for bad in variants:
                    manifest_path.write_text(json.dumps(bad))
                    with self.assertRaises(ValueError):
                        hud.active_rules()
                manifest_path.write_text(json.dumps(base))
                (hud.ROOT / 'src/main/resources' / replacement).unlink()
                with self.assertRaises(FileNotFoundError):
                    hud.active_rules()
            finally:
                hud.ROOT = original


if __name__ == '__main__':
    unittest.main(verbosity=2)
