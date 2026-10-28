#!/usr/bin/env python3
"""Read-only hidden-shell regression; no generators, Gradle or runtime are run.

Run with python3 -B scripts/qa/test_hidden_shells_w235.py -v.
DESTINY_W235_USER_LOG overrides the historical client-log path. If the log is
absent, its closure test is explicitly skipped; the remaining checks still run.
"""
import ast
from collections import Counter
import json
import os
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / 'src/main/resources'
USER_LOG = Path(os.environ.get('DESTINY_W235_USER_LOG', '/private/tmp/destiny-user-0U2mtrD.log'))
WEAPONS = {
    'dust_rock_blues': (207, 236),
    'first_in_last_out': (208, 230),
    'ikelos_sg_v1_0_1': (221, 242),
    'mindbender_s_ambition_adept': (221, 210),
    'parcel_of_stardust_fell_to_earth': (221, 224),
}


def hidden_id(weapon, stage):
    return f'destiny:weapon_insert_w{stage}_{weapon}/{weapon}_shell_hidden'


def sprite_path(sprite):
    if not isinstance(sprite, str) or not re.fullmatch(r'[a-z0-9_.-]+:[a-z0-9_./-]+', sprite):
        raise ValueError(f'Invalid sprite: {sprite!r}')
    namespace, path = sprite.split(':', 1)
    return f'assets/{namespace}/textures/{path}.png'


def closure(model_id, load_model, texture_exists):
    """Resolve child overrides, inherited geometry and texture aliases independently."""
    chain, textures, elements = [], {}, None
    current = model_id
    while current:
        if current in chain:
            raise ValueError(f'Parent cycle at {current}')
        chain.append(current)
        model = load_model(current)
        textures = {**model.get('textures', {}), **textures}
        if elements is None and 'elements' in model:
            elements = model['elements']
        current = model.get('parent')
    sprite, visited = textures.get('particle'), set()
    while isinstance(sprite, str) and sprite.startswith('#'):
        if sprite in visited:
            raise ValueError(f'Texture alias cycle at {sprite}')
        visited.add(sprite)
        sprite = textures.get(sprite[1:])
    path = sprite_path(sprite)
    if not texture_exists(path):
        raise ValueError(f'Missing PNG: {path}')
    return chain, sprite, elements


def source_loader():
    cache = {}

    def load(model_id):
        if model_id not in cache:
            namespace, path = model_id.split(':', 1)
            file = RES / f'assets/{namespace}/models/{path}.json'
            cache[model_id] = json.loads(file.read_bytes())
        return cache[model_id]

    return load


class HiddenShellsW235Test(unittest.TestCase):
    def test_five_roots_keep_empty_geometry_and_own_weapon_sprite(self):
        load = source_loader()
        for weapon, (stage, _) in WEAPONS.items():
            with self.subTest(weapon=weapon):
                model_id = hidden_id(weapon, stage)
                expected = f'destiny:item/weapon/w123/{weapon}'
                model = load(model_id)
                self.assertEqual(model, {'textures': {'particle': expected}, 'elements': []})
                self.assertEqual(load(model_id.replace('_shell_hidden', '_shell'))['textures']['particle'], expected)
                chain, sprite, elements = closure(model_id, load, lambda p: (RES / p).is_file())
                self.assertEqual((chain, sprite, elements), ([model_id], expected, []))

    def test_generators_emit_the_same_empty_model_using_source_particle(self):
        # Inspect only the emit argument; importing/running these generators would
        # perform unrelated regeneration and require external animation sources.
        for weapon, (stage, _) in WEAPONS.items():
            with self.subTest(weapon=weapon):
                file = ROOT / f'scripts/generate_insert_w{stage}_{weapon}.py'
                tree = ast.parse(file.read_text(), filename=str(file))
                calls = [node for node in ast.walk(tree)
                         if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                         and node.func.id == 'emit' and len(node.args) == 2
                         and any(isinstance(part, ast.Constant) and isinstance(part.value, str)
                                 and '_shell_hidden.json' in part.value
                                 for part in ast.walk(node.args[0]))]
                self.assertEqual(len(calls), 1)
                value = calls[0].args[1]
                # Permit only this small data expression before evaluating it.
                allowed = (ast.Dict, ast.List, ast.Constant, ast.Subscript, ast.Name, ast.Load)
                self.assertTrue(all(isinstance(node, allowed) for node in ast.walk(value)))
                self.assertEqual({n.id for n in ast.walk(value) if isinstance(n, ast.Name)}, {'source'})
                expression = compile(ast.Expression(value), str(file), 'eval')
                for particle in (f'destiny:item/weapon/w123/{weapon}', 'destiny:item/test/alternate'):
                    emitted = eval(expression, {'__builtins__': {}}, {'source': {'textures': {'particle': particle}}})
                    self.assertEqual(emitted, {'textures': {'particle': particle}, 'elements': []})

    @unittest.skipUnless(USER_LOG.is_file(), f'Historical user log unavailable: {USER_LOG}')
    def test_actual_2284_warning_models_resolve_through_only_five_repaired_roots(self):
        lines = USER_LOG.read_text(errors='replace').splitlines()
        warnings = []
        for index, line in enumerate(lines):
            match = re.search(r'Missing texture references in model ([a-z0-9_.-]+:[a-z0-9_./-]+):$', line)
            if match:
                self.assertLess(index + 1, len(lines))
                self.assertEqual(lines[index + 1].strip(), 'particle')
                warnings.append(match[1])
        self.assertEqual(len(warnings), 2284)
        self.assertEqual(len(set(warnings)), 2284)
        load = source_loader()
        roots = {hidden_id(w, stage): (w, count) for w, (stage, count) in WEAPONS.items()}

        def original_load(model_id):
            return {'elements': []} if model_id in roots else load(model_id)

        terminal_counts, families = Counter(), Counter()
        for model_id in warnings:
            with self.subTest(model=model_id):
                with self.assertRaisesRegex(ValueError, 'Invalid sprite: None'):
                    closure(model_id, original_load, lambda p: (RES / p).is_file())
                chain, sprite, elements = closure(model_id, load, lambda p: (RES / p).is_file())
                self.assertIn(chain[-1], roots)
                weapon, _ = roots[chain[-1]]
                self.assertEqual(sprite, f'destiny:item/weapon/w123/{weapon}')
                self.assertEqual(elements, [])
                self.assertEqual(len(chain), 3 if model_id.startswith('destiny:first_person_framing_w205/') else 2)
                terminal_counts[chain[-1]] += 1
                families[model_id.split('/')[0]] += 1
        self.assertEqual(terminal_counts, Counter({root: count * 2 for root, (_, count) in roots.items()}))
        self.assertEqual(families['destiny:first_person_framing_w205'], 1142)
        for weapon, (stage, count) in WEAPONS.items():
            self.assertEqual(families[f'destiny:weapon_insert_w{stage}_{weapon}'], count)

    def test_inheritance_honors_child_alias_override_and_empty_geometry(self):
        models = {
            'destiny:child': {'parent': 'destiny:parent', 'textures': {'paint': 'destiny:item/child'}, 'elements': []},
            'destiny:parent': {'textures': {'particle': '#paint', 'paint': 'destiny:item/parent'}, 'elements': [{}]},
        }
        chain, sprite, elements = closure('destiny:child', models.__getitem__,
                                           lambda p: p == 'assets/destiny/textures/item/child.png')
        self.assertEqual((chain, sprite, elements), (['destiny:child', 'destiny:parent'], 'destiny:item/child', []))

    def test_rejects_missing_parent_and_parent_cycles(self):
        for models, error in (({'destiny:a': {'parent': 'destiny:missing'}}, KeyError),
                              ({'destiny:a': {'parent': 'destiny:b'}, 'destiny:b': {'parent': 'destiny:a'}}, ValueError)):
            with self.subTest(models=models), self.assertRaises(error):
                closure('destiny:a', models.__getitem__, lambda _: True)

    def test_rejects_original_empty_root_missing_alias_and_alias_cycle(self):
        for model in ({'elements': []},
                      {'textures': {'particle': '#absent'}, 'elements': []},
                      {'textures': {'particle': '#a', 'a': '#b', 'b': '#a'}, 'elements': []},
                      {'textures': {'particle': 'not a sprite'}, 'elements': []}):
            with self.subTest(model=model), self.assertRaises(ValueError):
                closure('destiny:a', lambda _: model, lambda _: True)

    def test_rejects_resolved_sprite_when_png_is_missing(self):
        model = {'textures': {'particle': 'destiny:item/weapon/w123/dust_rock_blues'}, 'elements': []}
        with self.assertRaisesRegex(ValueError, 'Missing PNG'):
            closure('destiny:a', lambda _: model, lambda _: False)


if __name__ == '__main__':
    unittest.main()
