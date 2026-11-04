#!/usr/bin/env python3
"""Reproduce the bounded W226 BASIC Gutshot sockets and DDC evidence; never run gameplay."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

BASE = 1365187766
PINS = {
    '/tmp/destiny-weapons-w30/bungie-items.json': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c',
    '/tmp/destiny-weapons-w60/bungie-plugsets.json': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959',
    '/tmp/destiny-weapons-w60/manifest.json': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce',
    '/private/tmp/destiny-w226/ddc-perks-live.html': '6430f2f552832b903efb85be59adf4a1791d956d30fee4e4fe79c8ad2c53bc15',
}
EXPECTED = [
    dict(id='allied_demand', hash=1532276803, socket=4, perkHash=BASE, plugSetHash=703779397),
    dict(id='ammit_ar2', hash=2119346509, socket=4, perkHash=BASE, plugSetHash=560115158),
]
URL = 'https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278'


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(root, check):
    for path, expected in PINS.items():
        if sha(path) != expected:
            raise SystemExit(f'Pinned input changed: {path}')
    inventory, plugsets, manifest, ddc = map(Path, PINS)
    inv, pools = load(inventory), load(plugsets)
    catalog_path = root / 'src/main/resources/destiny/weapons/w30.json'
    stats_path = root / 'src/main/resources/destiny/weapons/w40-characteristics.json'
    entries = {e['id']: e for e in load(catalog_path)}
    stats = load(stats_path)
    assert len({w['id'] for w in stats}) == len(stats), 'duplicate characteristics'
    perk = inv[str(BASE)]
    assert perk['hash'] == BASE and perk['displayProperties']['name'] == 'Gutshot Straight'
    assert perk['itemTypeDisplayName'] == 'Trait' and perk['inventory']['tierType'] == 2
    assert perk['plug']['isDummyPlug'] is False
    rolls, proofs = [], []
    for weapon in stats:
        assert weapon['id'] in entries
        item = inv[str(weapon['bungieHash'])]
        assert item['hash'] == weapon['bungieHash']
        if weapon['exotic'] or item['inventory']['tierType'] != 5:
            continue
        sockets = item['sockets']
        indexes = {i for c in sockets['socketCategories'] if c['socketCategoryHash'] == 4241085061
                   for i in c['socketIndexes']}
        for index in sorted(indexes):
            socket = sockets['socketEntries'][index]
            # BASIC randomized trait pool only. No reusable/crafted/enhanced/fake fallback.
            pool_hash = socket.get('randomizedPlugSetHash')
            pool = pools.get(str(pool_hash), {})
            if pool.get('isFakePlugSet') is not False:
                continue
            assert pool['hash'] == pool_hash
            matches = [p for p in pool.get('reusablePlugItems', [])
                       if p.get('plugItemHash') == BASE and p.get('currentlyCanRoll') is True]
            for plug in matches:
                roll = dict(id=weapon['id'], hash=weapon['bungieHash'], socket=index,
                            perkHash=BASE, plugSetHash=pool_hash)
                rolls.append(roll)
                proofs.append(dict(roll=roll, name=item['displayProperties']['name'],
                                   family=entries[weapon['id']]['family'], tierType=5, exotic=False,
                                   traitCategory=4241085061, socket=socket, isFakePlugSet=False,
                                   matchingPlug=plug,
                                   itemPointer=f'/{weapon["bungieHash"]}/sockets/socketEntries/{index}',
                                   poolPointer=f'/{pool_hash}/reusablePlugItems/{pool["reusablePlugItems"].index(plug)}'))
    rolls.sort(key=lambda r: (r['id'], r['socket']))
    proofs.sort(key=lambda p: (p['roll']['id'], p['roll']['socket']))
    assert rolls == EXPECTED, rolls
    assert {p['family'] for p in proofs} == {'auto_rifle', 'sidearm'}
    rows = [r for r in re.findall(r'<tr\b[^>]*>.*?</tr>', ddc.read_text(), re.S)
            if '1662574278R109' in r]
    assert len(rows) == 1
    row = rows[0]
    text = ' '.join(html.unescape(re.sub('<[^>]+>', ' ', row)).split())
    for value in ('110', 'Gutshot Straight', 'While ADS', '-15%', '-10%?',
                  '20% Increased', 'Auto Rifles', '10% Increased', 'Sidearm', 'Non-Weakspot'):
        assert value in text, (value, text)
    manifest_response = load(manifest)['Response']
    version = manifest_response['version']
    components = manifest_response['jsonWorldComponentContentPaths']['en']
    resource = dict(stage='W226', perk=dict(id='gutshot_straight', hash=BASE,
                    autoRifleBodyMultiplier=1.2, sidearmBodyMultiplier=1.1), weapons=rolls)
    limitations = [
        'BASIC only: hash1365187766. Enhanced uncertain -10%? AA cone entry is excluded.',
        'Base AA cone scalar0.85 is evidence only: no auto-aim cone engine path exists; no stability/spread surrogate.',
        'ADS means actual WeaponAiming.aimInput(p) at accepted paid fire, including an accepted ADS transition before completion; no raw sneak, pose, FOV preview or progress threshold.',
        'Only direct BODY components are scaled. Precision, weakspot, perk splash and unpaid/preview/rejected contexts use no Gutshot token. The existing hit classifier provides body versus precision; no separate Destiny weakspot/shield simulation is added.',
        'Token is immutable and self-contained. ADS release, later selection or source changes cannot retroactively alter an already-paid attack. No timer/lifecycle, metadata, ammunition, inventory, pose or registry mutation.',
        'Master owns selection registration, WeaponShotTraits.Snapshot capture, damageOnly token stripping, and applying bodyDamage only to hits.body; this slice does not implement those shared hooks.',
    ]
    source = dict(stage='W226', date='2026-10-28', basicPerk=dict(hash=BASE,
                  name=perk['displayProperties']['name'], description=perk['displayProperties']['description'],
                  itemTypeDisplayName=perk['itemTypeDisplayName'], tierType=perk['inventory']['tierType'],
                  plug=perk['plug'], itemCategoryHashes=perk['itemCategoryHashes']),
                  officialManifest=version,
                  officialComponentUrls={key: 'https://www.bungie.net' + components[key] for key in
                                         ('DestinyInventoryItemDefinition', 'DestinyPlugSetDefinition')},
                  inputs=PINS,
                  canonicalInputs={str(p.relative_to(root)): sha(p) for p in (catalog_path, stats_path)},
                  scannedCanonicalCount=len(stats), socketProofs=proofs,
                  ddc=dict(url=URL, tab='Weapon Perks', gid=1662574278, row=110,
                           htmlId='1662574278R109', text=text, html=row,
                           baseAutoRifleBodyMultiplier=1.2, baseSidearmBodyMultiplier=1.1,
                           baseAutoAimConeScalar=0.85, autoAimImplemented=False), limitations=limitations)
    markdown = '\n'.join([
        '# W226 Gutshot Straight — bounded BASIC source proof', '',
        f'- Bungie manifest: `{version}`.',
        f'- BASIC hash `{BASE}`: Trait/Common, non-dummy. Only real legendary canonical sources with trait category `4241085061`, `isFakePlugSet=false`, and `currentlyCanRoll=true` are emitted.',
        f'- Scanned all {len(stats)} canonical characteristics; exactly two legal BASIC sockets. Full selected socket and matching plug rows, JSON pointers, hashes and bounded DDC HTML row are in `source.json`.',
        '- `ammit_ar2` / Ammit AR2: item `2119346509`, socket `4`, randomized pool `560115158`, BODY ×1.2.',
        '- `allied_demand` / Allied Demand: item `1532276803`, socket `4`, randomized pool `703779397`, BODY ×1.1.',
        f'- [User DDC Weapon Perks]({URL}): row **110**, HTML ID `1662574278R109`; BASIC ADS nonprecision/nonweakspot damage +20% Auto Rifles / +10% Sidearms; AA cone −15% (scalar0.85), source-only. Enhanced −10%? excluded.', '',
        '## Input SHA-256 pins', '',
        *[f'- `{p}`: `{h}`' for p, h in PINS.items()], '',
        '## Runtime contract and limits', '',
        *[f'- {s}' for s in limitations], '',
        '- API: `GutshotProfile.ID`, `HASH`, `rolls()`, `supports(entry)`, `bodyMultiplier(entry)`; `WeaponGutshot.Token.NONE`, `capture(p, entry)`, `bodyDamage(token, body)`. No precision method or lifecycle API.',
        '- `capture` is called only after the master accepts and pays an individual direct emission. It observes exact main-hand/inventory object identity, count1, current owner/use eligibility, canonical entry and exact selected BASIC socket. It does not infer payment from a roll or ammo count.',
        '- Master stores the token in `WeaponShotTraits.Snapshot`, strips it in `damageOnly()`, and transforms only `hits.body` before combining mixed hit components. Preview, unpaid and perk splash callers retain `Token.NONE`.', '',
        '## Reproduce', '',
        '```sh',
        'rtk proxy python3 scripts/build_gutshot_w226.py --root "$WORKTREE" --check',
        '```', '',
        'Without `--check`, only the three owned resource/evidence files are generated. No registry, build, game or pose assets are changed.', '',
        'The targeted unit suite covers accepted versus rejected/unpaid contexts, actual ADS input policy, exact held identity/count/selected socket, immutable paid-shot snapshots, mixed BODY/precision/splash policy, and resource corruption. Minecraft bootstrap/real selected-roll capture and shared integration are master-owned checks; see the worker report for executed results.', '',
    ])
    outputs = {
        'src/main/resources/destiny/weapons/w226-gutshot.json': json.dumps(resource, indent=2) + '\n',
        'art/weapons/w226/gutshot/source.json': json.dumps(source, indent=2, ensure_ascii=False) + '\n',
        'art/weapons/w226/gutshot/SOURCE.md': markdown,
    }
    for name, data in outputs.items():
        path = root / name
        if check:
            assert path.read_text() == data, f'Stale generated file: {name}'
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data)
    print('W226 Gutshot: two exact BASIC currentlyCanRoll sockets; DDC110/R109; ' +
          ('all three generated outputs reproduce' if check else 'three owned outputs written'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    build(args.root, args.check)
