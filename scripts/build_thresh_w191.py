#!/usr/bin/env python3
"""Build base Thresh only from pinned official sockets and the user's exact DDC row."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

PERK = 'thresh'
NAME = 'Thresh'
HASH = 2726471870
ROW = 227
PIN = '245114.26.10.13.2000-1-bnet.66137'

def build(root):
    inventory = Path('/tmp/destiny-weapons-w30/bungie-items.json')
    plugsets = Path('/tmp/destiny-weapons-w60/bungie-plugsets.json')
    manifest = Path('/tmp/destiny-weapons-w60/manifest.json')
    candidates = Path('/private/tmp/destiny-w191/sockets.json')
    ddc = Path('/private/tmp/destiny-w190/ddc-perks.html')
    characteristics = root / 'src/main/resources/destiny/weapons/w40-characteristics.json'
    catalog_file = root / 'src/main/resources/destiny/weapons/w30.json'
    load = lambda p: json.loads(p.read_text())
    assert load(manifest)['Response']['version'] == PIN
    inv, pools = load(inventory), load(plugsets)
    rolls = load(candidates)[PERK]
    assert len(rolls) == 6
    catalog = {w['id']: w for w in load(catalog_file)}
    meta = {w['id']: w for w in load(characteristics)}
    perk = inv[str(HASH)]
    assert perk['displayProperties']['name'] == NAME and perk['itemTypeDisplayName'] == 'Trait'
    proofs = []
    seen = set()
    for roll in rolls:
        weapon = inv[str(roll['hash'])]
        assert roll['id'] in catalog and meta[roll['id']]['bungieHash'] == roll['hash']
        assert not meta[roll['id']]['exotic'] and weapon['inventory']['tierType'] == 5
        assert roll['perkHash'] == HASH and (roll['id'], roll['socket']) not in seen
        seen.add((roll['id'], roll['socket']))
        sockets = weapon['sockets']
        category = next(c for c in sockets['socketCategories']
                        if c['socketCategoryHash'] == 4241085061 and roll['socket'] in c['socketIndexes'])
        entry = sockets['socketEntries'][roll['socket']]
        assert entry['randomizedPlugSetHash'] == roll['plugSetHash']
        pool = pools[str(roll['plugSetHash'])]
        assert pool['isFakePlugSet'] is False
        matching = [p for p in pool['reusablePlugItems']
                    if p['plugItemHash'] == HASH and p.get('currentlyCanRoll') is True]
        assert len(matching) == 1
        proofs.append({'roll': roll, 'traitCategory': category, 'socketEntry': entry,
                       'isFakePlugSet': pool['isFakePlugSet'], 'matchingPlug': matching[0]})
    clean = lambda text: html.unescape(re.sub(r'<[^>]+>', ' ', text)).strip()
    rows = [r for r in re.findall(r'<tr\b[^>]*>.*?</tr>', ddc.read_text(), re.S)
            if any(clean(td) == NAME for td in re.findall(r'<td\b[^>]*>.*?</td>', r, re.S))]
    assert len(rows) == 1
    raw = rows[0]
    assert f'1662574278R{ROW-1}' in raw
    text = clean(raw)
    assert '1%' in text and '1.5%' in text and all(x in text for x in ('Fusion Rifles', 'Glaives', 'Shotguns', 'Sniper Rifles'))
    resource = {'stage': 'W191', 'perk': {'id': PERK, 'hash': HASH, 'energyPercent': 1.0, 'specialEnergyPercent': 1.5, 'specialEnergyFamilies': ['fusion_rifle', 'glaive', 'shotgun', 'sniper_rifle']}, 'weapons': rolls}
    inputs = (inventory, plugsets, manifest, candidates, ddc, characteristics, catalog_file)
    source = {'date': '2026-10-27', 'officialManifest': PIN, 'perkDefinition': perk,
              'inputs': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
              'socketProofs': proofs, 'ddc': {'url': 'https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278',
              'row': ROW, 'nameCellExactMatch': NAME, 'text': text, 'html': raw},
              'enhancedExcluded': True, 'mapping': 'Add 1% Super, or 1.5% for fusion_rifle/glaive/shotgun/sniper_rifle; clamp to 1. Paid Sword qualifies; glaive melee excluded. Weapon final blow is additional to existing baseline onKill Super. No enhanced values.'}
    for path, value in [(f'src/main/resources/destiny/weapons/w191-{PERK}.json', resource),
                        (f'art/weapons/w191/{PERK}/source.json', source)]:
        dest = root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(f'{NAME}: DDC row{ROW}, six exact base randomized trait sockets; provenance retained.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    build(parser.parse_args().root.resolve())
