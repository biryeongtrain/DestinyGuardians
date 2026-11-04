#!/usr/bin/env python3
"""Extract only explicit historical Oracle ammo_percent; missing is unknown, not 1.

Captured 20-Hz full-duration * fraction, ceil once, is the server integration
policy. It is not an exact modern sandbox or perk-modified Oracle reproduction.
--verify reconstructs outputs without writing or downloading anything.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ['art/weapons/w46/extraction.json', 'art/weapons/w46/weapon_formulas.json',
          'art/weapons/w46/stat_calc.rs', 'art/weapons/w46/rs_types.rs',
          'art/weapons/w46/build.rs', 'art/weapons/w30/catalog.json']


def encode(v): return (json.dumps(v, ensure_ascii=False, indent=2) + '\n').encode()
def sha(v): return hashlib.sha256(v).hexdigest()


def generate():
    source = json.loads((ROOT / INPUTS[0]).read_bytes())
    formulas = json.loads((ROOT / INPUTS[1]).read_bytes())
    rows, excluded = [], []
    for row in source['entries']:
        curve = row.get('reloadCurve', {})
        if 'ammo_percent' not in curve:
            excluded.append(row['id'])
            continue
        original = formulas[row['oracleFamily']]['cat'][row['category']]['reload']
        assert curve == original
        ratio = curve['ammo_percent']
        assert type(ratio) in (int, float) and 0 < ratio < 1
        rows.append({'id': row['id'], 'hash': row['bungieHash'], 'family': row['family'],
                     'fraction': ratio, 'oracleFamily': row['oracleFamily'],
                     'category': row['category']})
    assert {r['id'] for r in rows} == {'duke_mk_44', 'austringer',
        'seventh_seraph_officer_revolver', 'fixed_odds', 'hammerhead', 'retrofit_escapade'}
    resource = ROOT / 'src/main/resources/destiny/weapons/w65-reload-credit.json'
    raw = encode({'stage': 'W65', 'policy': 'ceil(captured full phase ticks * explicit fraction)',
                  'weapons': rows})
    return {resource: raw, ROOT / 'art/weapons/w65/provenance.json': encode({
        'stage': 'W65', 'oracleCommit': source['commit'],
        'generator': 'scripts/extract_reload_credit_w65.py',
        'inputSha256': {p: sha((ROOT / p).read_bytes()) for p in INPUTS},
        'outputSha256': {str(resource.relative_to(ROOT)): sha(raw)},
        'selectedWeapons': len(rows), 'excludedWithoutExplicitFraction': excluded,
        'nativeVerified': False, 'modernSandboxExact': False,
        'limitations': ['Historical approximate reload curves, not official exact timings',
            'No missing-value default inferred', 'Full ready deadline is unchanged',
            'Apply explicit ratio to captured effective integer ticks; perk expiry cannot retime',
            'Oracle modifier changes reload_time but not ammo_time; not copied as perk behavior',
            'Duke footage corroborates earlier ammo credit, not exact ratio or earliest fire input']})}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    for path, raw in generate().items():
        if args.verify:
            if not path.is_file() or path.read_bytes() != raw:
                raise SystemExit(f'W65 differs: {path.relative_to(ROOT)}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    print('W65 explicit ammo-credit data verified' if args.verify else 'W65 explicit ammo-credit data generated')
