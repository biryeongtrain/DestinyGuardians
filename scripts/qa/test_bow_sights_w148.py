#!/usr/bin/env python3
"""Geometric W148 sight checks; these do not claim native visual acceptance."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
import generate_bow_sights_w148 as gen
from PIL import Image


def read(path):
    return json.loads((ROOT/path).read_bytes())


def rotate(v, axis, angle):
    i, j = {'x': (1, 2), 'y': (2, 0), 'z': (0, 1)}[axis]
    result = list(v)
    c, s = math.cos(angle), math.sin(angle)
    result[i], result[j] = c*v[i]-s*v[j], s*v[i]+c*v[j]
    return result


def local(e, point, direction=False):
    r = e.get('rotation')
    if not r:
        return point
    assert not r.get('rescale', False), 'Ray test must account for rescale before allowing it'
    origin = r['origin']
    shifted = point if direction else [a-b for a, b in zip(point, origin)]
    result = rotate(shifted, r['axis'], -math.radians(r['angle']))
    return result if direction else [a+b for a, b in zip(result, origin)]


def ray_interval(e, x, y):
    """Exact ray/rotated-cuboid slab intersection, +Z=100 toward -Z=-100.

    Checks both in front of and behind the aperture, including the string near
    the eye. World AABBs alone would incorrectly fill rotated ring corners.
    """
    origin = local(e, [x, y, 100.])
    direction = local(e, [0., 0., -1.], direction=True)
    near, far = 0., 200.
    for p, v, lo, hi in zip(origin, direction, e['from'], e['to']):
        if abs(v) < 1e-12:
            if p < lo-1e-8 or p > hi+1e-8:
                return None
        else:
            a, b = sorted(((lo-p)/v, (hi-p)/v))
            near, far = max(near, a), min(far, b)
            if near > far+1e-8:
                return None
    return near, far


def hits(elements, x, y):
    return [e for e in elements if ray_interval(e, x, y) is not None]


def inside(e, point):
    return all(lo-1e-6 <= p <= hi+1e-6
               for p, lo, hi in zip(local(e, point), e['from'], e['to']))


class BowSightsW148Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = read(gen.META)
        cls.bows = {r['id']: r for r in cls.meta['bows']}
        cls.models = {id: read(r['bodyModelPath']) for id, r in cls.bows.items()}
        cls.states = {id: [read(s['path'])['elements'] for s in r['retainedMovingStates']]
                      for id, r in cls.bows.items()}

    def test_master_endpoint_contract(self):
        self.assertIsInstance(self.meta['bows'], list)
        self.assertEqual(set(self.bows), set(gen.IDS))
        self.assertFalse(self.meta['nativeAccepted'])
        for id, r in self.bows.items():
            with self.subTest(id=id):
                x, y, z = r['sightCenter']
                self.assertEqual(r['model'], 'destiny:weapon_sight_w148/'+id+'_body')
                self.assertEqual(r['forwardPoint'], [x, y, round(z-2, 7)])
                self.assertEqual(r['forwardAxis'], [0, 0, -1])
                model = self.models[id]
                self.assertEqual(set(model), {'credit', 'textures', 'elements'})
                self.assertTrue(model['elements'])
                self.assertEqual(gen.sha((ROOT/r['bodyModelPath']).read_bytes()), r['outputSha256'])

    def test_retained_body_is_exact_and_no_static_motion(self):
        for id, r in self.bows.items():
            with self.subTest(id=id):
                original = read(r['sourceBodyModelPath'])
                retained = [e for e in original['elements'] if e['name'] not in r['removedNames']]
                output = self.models[id]
                self.assertEqual(output['elements'][:len(retained)], retained)
                self.assertEqual(output['textures'], original['textures'])
                self.assertEqual(len(retained), r['retainedBodyElements'])
                moving_names = read(f'art/weapons/w123/{id}/design.json')['moving_element_names']
                self.assertFalse(set(moving_names) & {e['name'] for e in output['elements']})
                self.assertTrue(set(r['removedNames']) <= {e['name'] for e in original['elements']})
                self.assertTrue(all('sight' in name for name in r['removedNames']))
                self.assertEqual([e['name'] for e in output['elements'][len(retained):]], r['addedNames'])

    def test_center_ray_and_finite_corridor_clear_in_all_88_motion_states(self):
        for id, r in self.bows.items():
            self.assertEqual(len(self.states[id]), 44)
            cx, cy, _ = r['sightCenter']
            radius = r['clearCenterCorridorRadius']
            offsets = [(0., 0.)]+[(radius*math.cos(t*math.pi/4), radius*math.sin(t*math.pi/4)) for t in range(8)]
            for frame, moving in enumerate(self.states[id]):
                for dx, dy in offsets:
                    obstruction = hits(self.models[id]['elements']+moving, cx+dx, cy+dy)
                    self.assertFalse(obstruction, (id, frame, dx, dy, [e.get('name', 'W50 motion') for e in obstruction]))

    def test_original_obstruction_negative_controls(self):
        # These must fail for the original problems; a weak count-only gate
        # would accept both the solid Biting blade and Slab's string projection.
        old = read(self.bows['biting_winds']['sourceBodyModelPath'])['elements']
        self.assertTrue(hits(old, 7.10, 11.85))
        self.assertTrue(hits(read(gen.ASSET+'models/weapon_bow_w50/whispering_slab_loaded_hip.json')['elements'],
                             6.3821565, 18.8958083))
        for id, r in self.bows.items():
            bad = copy.deepcopy(self.models[id]['elements'])
            x, y, z = r['sightCenter']
            bad.append({'name': 'opaque_card_negative_control', 'from': [x-.3, y-.3, z-.02], 'to': [x+.3, y+.3, z+.02]})
            self.assertTrue(hits(bad, x, y))

    def test_open_aperture_area_and_continuous_physical_perimeter(self):
        for id, r in self.bows.items():
            cfg = gen.CONFIG[id]
            cx, cy, cz = r['sightCenter']
            added = [e for e in self.models[id]['elements'] if e['name'] in r['addedNames']]
            frame = [e for e in added if e['name'].startswith('w148_sight_frame_')]
            self.assertEqual(len(frame), 8)
            # Every rail's actual endpoints and intermediate points are joined
            # to a solid rail, and the complete ring has physical Z depth.
            for e in frame:
                center = e['rotation']['origin']
                half = (e['to'][0]-e['from'][0])/2-.006
                for fraction in (-1., -.5, 0., .5, 1.):
                    delta = rotate([half*fraction, 0., 0.], 'z', math.radians(e['rotation']['angle']))
                    point = [a+b for a, b in zip(center, delta)]
                    self.assertTrue(any(inside(other, point) for other in frame))
                self.assertAlmostEqual(e['to'][2]-e['from'][2], r['sightDepth'])
                self.assertGreater(r['sightDepth'], .35)
            samples = [(x/20*.36, y/20*.36) for x in range(-20, 21) for y in range(-20, 21)
                       if x*x+y*y <= 400]
            clear = sum(not hits(added, cx+dx, cy+dy) for dx, dy in samples)/len(samples)
            self.assertGreater(clear, .92, (id, 'aperture filled', clear))
            # Even with retained body/string, most of the central opening is
            # usable. Center corridor above is stricter and checks every state.
            assembled = self.models[id]['elements']+self.states[id][0]
            clear = sum(not hits(assembled, cx+dx, cy+dy) for dx, dy in samples)/len(samples)
            self.assertGreater(clear, .80, (id, 'body across opening', clear))

    def test_visible_small_pin_and_connected_mount(self):
        for id, r in self.bows.items():
            with self.subTest(id=id):
                es = self.models[id]['elements']
                named = {e['name']: e for e in es}
                tip, stem = named['w148_sight_pin_tip'], named['w148_sight_pin_stem']
                cx, cy, cz = r['sightCenter']
                self.assertAlmostEqual(tip['to'][1], cy-.07)
                self.assertLess(tip['to'][0]-tip['from'][0], .12)
                self.assertLess(stem['to'][0]-stem['from'][0], .07)
                # Aiming tip has exposed opaque eye-facing area and is the
                # first physical hit from the eye, rather than behind a blade.
                pin_y = (tip['from'][1]+tip['to'][1])/2
                candidates = [(ray_interval(e, cx, pin_y), e) for e in es+self.states[id][0]]
                nearest = min((t[0], e['name']) for t, e in candidates if t is not None)
                self.assertEqual(nearest[1], 'w148_sight_pin_tip')
                self.assertTrue(inside(stem, [cx, cy-.16, cz+.08]))
                self.assertTrue(inside(tip, [cx, cy-.16, cz+.08]))
                bridge, anchor = named['w148_sight_mount_bridge'], named[r['mountAnchorName']]
                self.assertFalse(anchor.get('rotation'))
                self.assertTrue(all(min(a, b)-max(c, d) > 0 for a, b, c, d in
                                    zip(bridge['to'], anchor['to'], bridge['from'], anchor['from'])))
                rail_x = cx+gen.CONFIG[id]['halfWidth']*(1 if id == 'biting_winds' else -1)
                rail_y = cy+(.4 if id == 'biting_winds' else 0.)
                join = [rail_x, rail_y, cz]
                self.assertTrue(inside(bridge, join))
                self.assertTrue(any(inside(e, join) for e in es if e['name'].startswith('w148_sight_frame_')))

    def test_existing_palette_faces_opaque_and_pin_contrasts(self):
        for id, r in self.bows.items():
            texture = ROOT/(gen.ASSET+'textures/item/weapon/w123/'+id+'.png')
            with Image.open(texture) as image:
                self.assertEqual(image.size, (1024, 1024))
                def color(face):
                    u, v, U, V = face['uv']
                    return image.getpixel((int((u+U)/2*64), int((v+V)/2*64)))
                added = [e for e in self.models[id]['elements'] if e['name'] in r['addedNames']]
                for e in added:
                    self.assertEqual(set(e['faces']), {'north', 'south', 'east', 'west', 'up', 'down'})
                    self.assertTrue(all(b > a for a, b in zip(e['from'], e['to'])))
                    for face in e['faces'].values():
                        self.assertEqual(face['texture'], '#0')
                        self.assertEqual(set(face), {'texture', 'uv'})
                        self.assertEqual(color(face)[3], 255)
                tip = next(e for e in added if e['name'] == 'w148_sight_pin_tip')
                tip_color = color(tip['faces']['south'])
                dark_pixel = gen.CONFIG[id]['palette']['black']
                dark = image.getpixel(tuple(dark_pixel))
                self.assertGreater(sum(tip_color[:3])-sum(dark[:3]), 250)

    def test_retained_w50_hashes_and_maximum_assembled_budget(self):
        for id, r in self.bows.items():
            for path, digest in r['retainedDynamicAndGraphSha256'].items():
                self.assertEqual(gen.sha((ROOT/path).read_bytes()), digest, path)
            counts = [len(state) for state in self.states[id]]
            self.assertEqual(max(counts), r['maxRetainedW50MovingElements'])
            actual = len(self.models[id]['elements'])
            self.assertEqual(actual, r['bodyElements'])
            self.assertEqual(actual+max(counts), r['maxAssembledElements'])
            self.assertLessEqual(actual+max(counts), 1000)

    def test_input_pins_and_deterministic_exact_outputs(self):
        self.assertEqual(self.meta['inputSha256'], gen.INPUT_PINS)
        gen.verify_inputs()
        first, second = gen.generate(), gen.generate()
        self.assertEqual(first, second)
        self.assertEqual(set(first), {gen.META} | {r['bodyModelPath'] for r in self.bows.values()})
        for path, raw in first.items():
            self.assertEqual((ROOT/path).read_bytes(), raw, path)
        damaged = dict(gen.INPUT_PINS)
        damaged[next(iter(damaged))] = '0'*64
        with mock.patch.object(gen, 'INPUT_PINS', damaged):
            with self.assertRaisesRegex(ValueError, 'Input pin drift'):
                gen.generate()


if __name__ == '__main__':
    unittest.main()
