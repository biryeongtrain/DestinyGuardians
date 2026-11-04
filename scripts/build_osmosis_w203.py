#!/usr/bin/env python3
"""Pin base Osmosis sockets and bounded DDC row158; --check never writes outputs."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

BASE = 1774574192
TRAITS = 4241085061
EXPECTED = {
    "patron_of_lost_causes": (2723241847, 4, 120674550),
    "seventh_seraph_officer_revolver": (3037520408, 4, 3527094473),
    "steelfeather_repeater": (1251729046, 4, 2645685327),
}
PERK = {"id": "osmosis", "hash": BASE, "refillPercent": 50,
        "trigger": "successful_grenade_ability_activate", "refillsPerStowEpisode": 1,
        "element": "equipped_grenade_until_stowed", "rounding": "ceiling_tick_free"}

def load(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build(root):
    inventory = Path('/tmp/destiny-weapons-w30/bungie-items.json')
    plugsets = Path('/tmp/destiny-weapons-w60/bungie-plugsets.json')
    manifest = Path('/tmp/destiny-weapons-w60/manifest.json')
    ddc = Path('/private/tmp/destiny-w190/ddc-perks.html')
    catalog = root / 'src/main/resources/destiny/weapons/w30.json'
    characteristics = root / 'src/main/resources/destiny/weapons/w40-characteristics.json'
    inv, pools = load(inventory), load(plugsets)
    rolls, proofs = [], []
    for weapon in load(characteristics):
        item = inv[str(weapon['bungieHash'])]
        if item['inventory']['tierType'] != 5 or weapon['exotic']:
            continue
        sockets = item['sockets']
        indexes = {n for c in sockets['socketCategories'] if c['socketCategoryHash'] == TRAITS
                   for n in c['socketIndexes']}
        for index in sorted(indexes):
            socket = sockets['socketEntries'][index]
            pool_hash = socket.get('randomizedPlugSetHash')
            pool = pools.get(str(pool_hash), {})
            if pool.get('isFakePlugSet') is not False:
                continue
            matching = [p for p in pool.get('reusablePlugItems', [])
                        if p.get('plugItemHash') == BASE and p.get('currentlyCanRoll') is True]
            if not matching:
                continue
            assert len(matching) == 1
            assert weapon['id'] in EXPECTED
            assert (weapon['bungieHash'], index, pool_hash) == EXPECTED[weapon['id']]
            assert weapon['ammo'] == 'PRIMARY' and weapon['damage'] == 'KINETIC'
            assert item['hash'] == weapon['bungieHash'] and item.get('redacted') is False
            roll = {'id': weapon['id'], 'hash': weapon['bungieHash'], 'socket': index,
                    'perkHash': BASE, 'plugSetHash': pool_hash}
            rolls.append(roll)
            proofs.append({'roll': roll, 'itemName': item['displayProperties']['name'],
                           'itemHash': item['hash'], 'tierType': item['inventory']['tierType'],
                           'traitCategory': TRAITS, 'socket': socket,
                           'isFakePlugSet': pool['isFakePlugSet'], 'matchingPlug': matching[0]})
    rolls.sort(key=lambda r: r['id'])
    proofs.sort(key=lambda p: p['roll']['id'])
    assert len(rolls) == 3 and {r['id'] for r in rolls} == set(EXPECTED)
    # Only a bounded row is retained; never print or serialize the full HTML sheet.
    rows = [m.group() for m in re.finditer(r'<tr\b[^>]*>.*?</tr>', ddc.read_text(), re.S)
            if '1662574278R157"' in m.group()]
    assert len(rows) == 1 and len(rows[0]) < 16000
    row = rows[0]
    text = ' '.join(html.unescape(re.sub('<[^>]+>', ' ', row)).split())
    assert all(s in text for s in ('158 Osmosis', 'Grenade Ability Usage:', 'Refills 50% of Magazine',
                                  'until stowed.', 'Can only refill once per activation',
                                  'currently equipped grenade'))
    assert inv[str(BASE)]['displayProperties']['name'] == 'Osmosis'
    resource = {'stage': 'W203', 'perk': PERK, 'weapons': rolls}
    source = {'date': '2026-10-27', 'perkDefinition': inv[str(BASE)],
              'officialManifest': load(manifest)['Response']['version'],
              'inputs': {str(p): sha(p) for p in (inventory, plugsets, manifest, ddc)},
              'canonicalInputs': {str(p.relative_to(root)): sha(p) for p in (catalog, characteristics)},
              'socketProofs': proofs,
              'ddc': {'url': 'https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278',
                      'tab': 'Weapon Perks', 'row': 158, 'text': text, 'html': row},
              'baseValuesVerifiedFromDDC': True, 'enhancedExcluded': True,
              'localPolicy': {'ammo': 'ceil(capacity * 50 / 100), tick-free; existing reloadRounds transfer and capacity bounds; all three exact sources Primary infinite reserve',
                              'activation': 'successful ability.activate, not grenade release; full/no-reserve attempt spends the only refill opportunity until stow',
                              'element': 'snapshot equipped grenade at accepted; later successful grenades may change element without another refill',
                              'kineticPvEBonus': 'No subtraction: the local baseline does not model this DDC combatant bonus.',
                              'enhanced': 'No enhanced hash or passive +5 Handling.'}}
    return {'src/main/resources/destiny/weapons/w203-osmosis.json': resource,
            'art/weapons/w203/osmosis/source.json': source}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    for relative, obj in build(root).items():
        output = root / relative
        encoded = json.dumps(obj, indent=2, ensure_ascii=False) + '\n'
        if args.check:
            assert output.read_text() == encoded, f'stale generated output: {relative}'
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(encoded)
    print('Osmosis W203: three exact base legendary trait sockets; DDC row158; ' +
          ('deterministic outputs verified.' if args.check else 'profile and bounded source proof written.'))

if __name__ == '__main__':
    main()
