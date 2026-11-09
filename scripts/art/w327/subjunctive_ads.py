"""Subjunctive-only ADS framing; source geometry, foliage and UVs stay unchanged.

The reused camera was too close to the rear chamber. Move the eye back and aim
through the upper clear portion of the circular hood, above the real foliage.
No pitch is needed: pitching down would raise the front chamber into the aim ray.
Frame zero retains the donor hip transform; reload assets are not generated here.
"""
import argparse, copy, json, math, runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def build(source_root=ROOT):
    assets = source_root / 'src/main/resources/assets/destiny'
    mapping = next(row for row in json.loads((source_root / 'src/main/resources/destiny/weapons/w327-legendary.json').read_text()) if row['id'] == 'subjunctive')
    base, family = mapping['base'], mapping['catalog']['family']
    route = 'weapon_sight_w153'
    donor = json.loads((assets / f'models/{route}/{base}_20_native.json').read_text())
    assert donor['parent'].startswith(f'destiny:{route}/'), donor['parent']
    output = ROOT / f'src/main/resources/assets/destiny/models/{route}'
    output.mkdir(parents=True, exist_ok=True)
    hip = json.loads((assets / f'models/weapon/{family}/{base}.json').read_text())['display']
    two_hand = runpy.run_path(str(source_root / 'scripts/build_weapons_w30.py'))['two_hand_display']
    # Hood center is (8,13.45,3.23); its top inner edge is above 14.2.
    # Center-crossing foliage peaks at 13.804, leaving ~0.246 model px clearance.
    anchor = [8, 14.05, 3.23]
    angle, scale, distance = 0., .9, 1.10
    a = math.radians(angle)
    y = (anchor[1] - 8) * math.cos(a) - (anchor[2] - 8) * math.sin(a)
    z = (anchor[1] - 8) * math.sin(a) + (anchor[2] - 8) * math.cos(a)
    target = {'rotation': [angle, 0, 0],
              'translation': [-8.96, round(8.32 - scale * y, 6), round(16 * (.72 - distance) - scale * z, 6)],
              'scale': [scale] * 3}
    outputs = []
    for frame in range(21):
        display = copy.deepcopy(hip)
        for context in ['firstperson_righthand', 'firstperson_lefthand']:
            for key in ['rotation', 'translation', 'scale']:
                display[context][key] = [round(v + (q - v) * frame / 20, 6)
                                         for v, q in zip(hip[context][key], target[key])]
        for style in ['native', 'twohand']:
            donor_leaf = json.loads((assets / f'models/{route}/{base}_{frame:02}_{style}.json').read_text())
            parent = donor_leaf['parent'].replace(base, 'subjunctive')
            doc = {'parent': parent, 'display': display if style == 'native'
                   else two_hand(display, family)}
            path = output / f'subjunctive_{frame:02}_{style}.json'
            path.write_text(json.dumps(doc, indent=2) + '\n')
            outputs.append(path)
    return outputs, {'sight_anchor': anchor, 'pitch_degrees': angle, 'scale': scale,
                     'eye_to_sight_meters': distance, 'target_display': target,
                     'route': route, 'base': base, 'native_qa': 'pending master', 'scope': 'Subjunctive ADS display leaves only'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, default=ROOT)
    args = parser.parse_args()
    paths, report = build(args.source_root)
    print(json.dumps(report, indent=2))
    print('Wrote', len(paths), 'Subjunctive-only ADS leaves')
