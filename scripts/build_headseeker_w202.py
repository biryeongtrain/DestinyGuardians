#!/usr/bin/env python3
"""Rebuild only W202 Headseeker owned evidence/resources from local official + DDC inputs."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDS = {"blast_furnace", "bygones", "chattering_bone", "claws_of_the_wolf", "cold_denial", "high_albedo"}
EXPECTED_HASHES = {"blast_furnace": 3843477312, "bygones": 2712244741,
                   "chattering_bone": 568515759, "claws_of_the_wolf": 1280933460,
                   "cold_denial": 1216130969, "high_albedo": 1197486957}
BASE = 460017080

def load(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build(root, check=False):
    if root.resolve() != ROOT:
        raise SystemExit("--root must be this script's own worktree")
    inventory = Path('/tmp/destiny-weapons-w30/bungie-items.json')
    plugsets = Path('/tmp/destiny-weapons-w60/bungie-plugsets.json')
    manifest = Path('/tmp/destiny-weapons-w60/manifest.json')
    ddc = Path('/private/tmp/destiny-w190/ddc-perks.html')
    inv, pools = load(inventory), load(plugsets)
    catalog = load(root/'src/main/resources/destiny/weapons/w40-characteristics.json')
    rolls, proofs = [], []
    for weapon in catalog:
        item = inv[str(weapon['bungieHash'])]
        if weapon['exotic'] or item['inventory']['tierType'] != 5:
            continue
        sockets = item['sockets']
        indexes = {i for category in sockets['socketCategories']
                   if category['socketCategoryHash'] == 4241085061 for i in category['socketIndexes']}
        for index in sorted(indexes):
            socket = sockets['socketEntries'][index]
            pool = pools.get(str(socket.get('randomizedPlugSetHash')), {})
            if pool.get('isFakePlugSet') is not False:
                continue
            for plug in pool.get('reusablePlugItems', []):
                if plug.get('plugItemHash') == BASE and plug.get('currentlyCanRoll') is True:
                    roll = dict(id=weapon['id'], hash=weapon['bungieHash'], socket=index,
                                perkHash=BASE, plugSetHash=socket['randomizedPlugSetHash'])
                    rolls.append(roll)
                    proofs.append(dict(roll=roll, tierType=5, exotic=False,
                                       traitCategory=4241085061, isFakePlugSet=False,
                                       socket=socket, matchingPlug=plug))
    rolls.sort(key=lambda r: (r['id'], r['socket']))
    proofs.sort(key=lambda p: (p['roll']['id'], p['roll']['socket']))
    assert len(rolls) == 6 and {r['id'] for r in rolls} == EXPECTED_IDS, rolls
    assert {r['id']: r['hash'] for r in rolls} == EXPECTED_HASHES, rolls
    row = next(r for r in re.findall(r'<tr\b[^>]*>.*?</tr>', ddc.read_text(), re.S)
               if '1662574278R112' in r)
    text = html.unescape(re.sub('<[^>]+>', ' ', row))
    for expected in ('Headseeker', '0.55 seconds', '1.2x', '3?%', 'refreshes', '+5 Stability'):
        assert expected in text, expected
    limitations = [
        'Uncertain 3?% Auto Aim Cone Size is unimplemented; no aim assistance is invented.',
        'Enhanced passive +5 Stability is excluded; only base hash 460017080 is supported.',
        'The port exposes a precision boolean. Original weakspot versus precision-hit and shielded-combatant distinctions are not modeled; this is not full Destiny weakspot parity.',
        'Uses the existing source-entry WeaponBallistics precision multiplier, not the DDC per-frame total-damage percentages.',
        'Only positive actual direct-hit weapon loss activates/refreshes. No splash, ability, blocked/immune hit, preview or unpaid emission credit.',
        '11 ticks is 0.55 seconds at 20 TPS. Accepted stow clears the window; paid emission snapshots cannot gain a buff from their own nonprecision hit.'
    ]
    resource = dict(stage='W202', perk=dict(id='headseeker', hash=BASE, durationTicks=11,
                    precisionBonusMultiplier=1.2), weapons=rolls)
    source = dict(date='2026-10-27', perkDefinition=inv[str(BASE)],
                  officialManifest=load(manifest)['Response']['version'],
                  inputs={str(p): sha(p) for p in (inventory, plugsets, manifest, ddc)},
                  socketProofs=proofs,
                  ddc=dict(url='https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278',
                           row=113, htmlId='1662574278R112', text=text, html=row),
                  formula='totalPrecision + (totalPrecision - totalPrecision / baseCritMultiplier) * 0.2',
                  limitations=limitations)
    for name, obj in [('src/main/resources/destiny/weapons/w202-headseeker.json', resource),
                      ('art/weapons/w202/headseeker/source.json', source)]:
        path = root/name
        data = json.dumps(obj, indent=2, ensure_ascii=False) + '\n'
        if check:
            assert path.read_text() == data, f'Stale generated file: {name}'
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data)
    print(json.dumps(rolls, indent=2))
    print('Headseeker: exact six base sockets; DDC row113/R112; 11-tick refresh, precision-bonus x1.2; ' + ('reproducible' if check else 'written'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    build(args.root, args.check)
