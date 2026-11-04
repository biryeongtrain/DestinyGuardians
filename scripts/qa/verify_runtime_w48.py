#!/usr/bin/env python3
"""Read-only W48-W75 asset/JAR provenance; distinguishes GameTest packs from live QA.

The isolated GameTest shader config defaults dynamic FOV off. Never use a previous
runtime pack to silently satisfy a failed current-GameTest FOV assertion.
"""
from pathlib import Path
import argparse
import json
import zipfile
from verify_runtime_w42 import verify, ROOT, sha

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--jar', type=Path, default=ROOT/'build/libs/destiny-guardians-0.1.0+26.3.jar')
p.add_argument('--server-pack', type=Path, required=True)
p.add_argument('--shader-config', type=Path, required=True)
p.add_argument('--pack-kind', choices=['gametest', 'runtime'], required=True)
p.add_argument('--stage', choices=['W48', 'W49', 'W50', 'W51', 'W52', 'W53', 'W54', 'W55', 'W56', 'W57', 'W58', 'W59', 'W60', 'W61', 'W62', 'W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'], default='W48')
p.add_argument('--baseline-cache', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
r = verify(a.jar.resolve(), a.server_pack.resolve(), a.baseline_cache.resolve())
r['stage'] = a.stage
r['packKind'] = a.pack_kind
r['packPath'] = str(a.server_pack)
r['nativeClientVerified'] = False
r['serverOnlySourceJar'] = []
paths = ['destiny/weapons/w43-ballistics.json',
         'data/destiny/tags/entity_type/weapon_precision_humanoids.json',
         'META-INF/licenses/oracle_engine.MIT-LICENSE', 'META-INF/licenses/oracle_engine.UNLICENSE',
         'destiny/weapons/w44-aim.json', 'destiny/weapons/w46-timing.json']
if a.stage in ('W53', 'W54', 'W55', 'W56', 'W57', 'W58', 'W59', 'W60', 'W61', 'W62', 'W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/animation/sword_w53.animation.json')
if a.stage in ('W55', 'W56', 'W57', 'W58', 'W59', 'W60', 'W61', 'W62', 'W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/animation/sword_w55.animation.json')
if a.stage in ('W56', 'W57', 'W58', 'W59', 'W60', 'W61', 'W62', 'W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/sounds/w56.json')
if a.stage in ('W58', 'W59', 'W60', 'W61', 'W62', 'W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/weapons/w58-handling.json')
if a.stage in ('W60', 'W61', 'W62', 'W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/weapons/w60-holster.json')
if a.stage in ('W61', 'W62', 'W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/weapons/w61-kill-clip.json')
if a.stage in ('W62', 'W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/weapons/w62-outlaw.json')
if a.stage in ('W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/sounds/w63-reload.json')
if a.stage in ('W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/weapons/w65-reload-credit.json')
if a.stage in ('W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/weapons/w66-rampage.json')
if a.stage in ('W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/weapons/w67-precision-return.json')
if a.stage in ('W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
    paths.append('destiny/weapons/w68-snapshot.json')
if a.stage in ('W73', 'W74', 'W75'):
    paths.append('destiny/weapons/w73-archers-tempo.json')
if a.stage in ('W74', 'W75'):
    paths.append('destiny/weapons/w74-bow-window.json')
if a.stage == 'W75':
    paths.append('destiny/weapons/w75-aim-movement.json')
with zipfile.ZipFile(a.jar) as jar, zipfile.ZipFile(a.server_pack) as pack:
    for path in paths:
        raw = (ROOT/'src/main/resources'/path).read_bytes()
        assert jar.read(path) == raw, path
        r['serverOnlySourceJar'].append(dict(path=path, sha256=sha(raw)))
    manifests = ['art/hud/w44-reticle/manifest.json', 'art/hud/w45-scope/manifest.json',
                 'art/weapons/w45-models/manifest.json', 'art/weapons/w47/manifest.json']
    if a.stage in ('W50', 'W51', 'W52', 'W53', 'W54', 'W55', 'W56', 'W57', 'W58', 'W59', 'W60', 'W61', 'W62', 'W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75'):
        manifests.append('art/weapons/w50/manifest.json')
    if a.stage == 'W51':
        manifests.append('art/weapons/w51/implementation.json')
    if a.stage == 'W52':
        # W51 source pins are historical. W52 must use its own implementation
        # snapshot, never silently rewrite a previous stage's source hashes.
        manifests.append('art/weapons/w52/implementation.json')
    if a.stage == 'W53':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w53/implementation.json']
    if a.stage == 'W54':
        # W53 animation assets are preserved, but its implementation source pins
        # are historical after W54 runtime/timeline changes.
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w54/implementation.json']
    if a.stage == 'W55':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/weapons/w55/implementation.json']
    if a.stage == 'W56':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/weapons/w56/implementation.json']
    if a.stage == 'W57':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/weapons/w57/implementation.json']
    if a.stage == 'W58':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/weapons/w58/implementation.json']
    if a.stage == 'W59':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/weapons/w59/implementation.json']
    if a.stage == 'W60':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/weapons/w60/implementation.json']
    if a.stage == 'W61':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/weapons/w61/implementation.json']
    if a.stage == 'W62':
        # Keep W61 implementation source pins historical; W62 pins current sources.
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w62/implementation.json']
    if a.stage == 'W63':
        # Prior implementation pins are historical; current resources are pinned by W63.
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w63/implementation.json']
    if a.stage == 'W64':
        # Previous implementation manifests remain historical.
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/weapons/w64/implementation.json']
    if a.stage == 'W65':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/weapons/w65/implementation.json']
    if a.stage == 'W66':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/hud/w66-rampage/manifest.json',
                      'art/weapons/w66/implementation.json']
    if a.stage == 'W67':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/hud/w66-rampage/manifest.json',
                      'art/weapons/w67/implementation.json']
    if a.stage == 'W68':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/hud/w66-rampage/manifest.json',
                      'art/weapons/w68/implementation.json']
    if a.stage == 'W69':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/hud/w66-rampage/manifest.json',
                      'art/weapons/w69/manifest.json', 'art/weapons/w69/implementation.json']
    if a.stage == 'W70':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/hud/w66-rampage/manifest.json',
                      'art/weapons/w69/manifest.json', 'art/weapons/w70/manifest.json',
                      'art/weapons/w70/implementation.json']
    if a.stage == 'W71':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/hud/w66-rampage/manifest.json',
                      'art/weapons/w69/manifest.json', 'art/weapons/w70/manifest.json',
                      'art/weapons/w71/manifest.json', 'art/weapons/w71/implementation.json']
    if a.stage == 'W72':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/hud/w66-rampage/manifest.json',
                      'art/weapons/w69/manifest.json', 'art/weapons/w70/manifest.json',
                      'art/weapons/w71/manifest.json', 'art/weapons/w72/implementation.json']
    if a.stage == 'W73':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/hud/w66-rampage/manifest.json',
                      'art/weapons/w69/manifest.json', 'art/weapons/w70/manifest.json',
                      'art/weapons/w71/manifest.json', 'art/hud/w73-archers-tempo/manifest.json',
                      'art/weapons/w73/implementation.json']
    if a.stage == 'W74':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/hud/w66-rampage/manifest.json',
                      'art/weapons/w69/manifest.json', 'art/weapons/w70/manifest.json',
                      'art/weapons/w71/manifest.json', 'art/hud/w73-archers-tempo/manifest.json',
                      'art/weapons/w74/implementation.json']
    if a.stage == 'W75':
        manifests += ['art/weapons/w53/manifest.json', 'art/weapons/w55/manifest.json',
                      'art/hud/w61-perks/manifest.json', 'art/hud/w62-outlaw/manifest.json',
                      'art/weapons/w64/manifest.json', 'art/hud/w66-rampage/manifest.json',
                      'art/weapons/w69/manifest.json', 'art/weapons/w70/manifest.json',
                      'art/weapons/w71/manifest.json', 'art/hud/w73-archers-tempo/manifest.json',
                      'art/weapons/w75/implementation.json']
    for manifest_path in manifests:
        manifest=json.loads((ROOT/manifest_path).read_text())
        if a.stage in ('W53', 'W54', 'W55', 'W56', 'W57', 'W58', 'W59', 'W60', 'W61', 'W62', 'W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75') and manifest_path == f'art/weapons/{a.stage.lower()}/implementation.json':
            assert manifest['jarSha256'] == r['jar']['sha256'], f'{a.stage} manifest pins a different built JAR'
        inventory=manifest.get('sha256')
        if inventory is None:
            inventory={**manifest['inputSha256'],**manifest['outputSha256']}
        for path, expected in inventory.items():
            source = ROOT/path
            raw = source.read_bytes()
            assert sha(raw) == expected, path
            if not source.is_relative_to(ROOT/'src/main/resources'):
                continue
            name = str(source.relative_to(ROOT/'src/main/resources'))
            if not name.startswith('assets/'):
                assert jar.read(name) == raw, name
                continue # Server-side animation data is not a client resource-pack asset.
            assert jar.read(name) == raw, name
            # Polymer parses/merges and compact-serializes these shared JSON tables.
            # Keep source/JAR byte equality; require exact JSON equivalence for only these
            # three known generated files, not a blanket relaxation for model/texture data.
            shared_json = a.stage in ('W56', 'W57', 'W58', 'W59', 'W60', 'W61', 'W62', 'W63', 'W64', 'W65', 'W66', 'W67', 'W68', 'W69', 'W70', 'W71', 'W72', 'W73', 'W74', 'W75') and name in {
                'assets/destiny/sounds.json', 'assets/destiny/lang/en_us.json',
                'assets/destiny/lang/ko_kr.json'}
            packed_raw = pack.read(name)
            if shared_json:
                assert json.loads(packed_raw) == json.loads(raw), name
            else:
                assert packed_raw == raw, name
            existing = [c for c in r['checks'] if c['path'] == name]
            if existing:
                assert all(c['sha256'] == expected for c in existing), name
            else:
                check = dict(path=name, sha256=expected,
                             sourceJarServerPack=packed_raw == raw, clientCache=False)
                if shared_json:
                    check.update(sourceJarBytes=True, serverPackJsonEquivalent=True,
                                 serverPackSha256=sha(packed_raw),
                                 transformation='Polymer compact JSON serialization')
                r['checks'].append(check)
    config_raw = a.shader_config.read_bytes()
    config = json.loads(config_raw)
    enabled = config.get('dynamic-fov-shader', False)
    assert isinstance(enabled, bool), 'Invalid shader configuration'
    name = 'assets/minecraft/shaders/include/projection.glsl'
    present = name in pack.namelist()
    assert present == enabled, 'Generated FOV shader presence must match the supplied generating configuration'
    projection = (ROOT/'libs/minigame-lib/src/main/resources/shaders/optional/projection.glsl').read_bytes()
    if present:
        assert pack.read(name) == projection, 'Projection shader bytes differ'
    r['dynamicFovProjection'] = dict(path=name, configured=enabled, present=present,
                                    bytesVerified=present, sourceSha256=sha(projection),
                                    configPath=str(a.shader_config), configSha256=sha(config_raw),
                                    clientCache=False)
r['evidenceBoundary'] = ('Current source/JAR byte equality and generated-pack equality only '
                        '(the three W56+ shared JSON tables allow exact parsed JSON equivalence after Polymer serialization). '
                        'GameTest configuration differs from normal QA; no live-client rendering, '
                        'native input, current client cache or normal-server deployment is certified.')
a.out.parent.mkdir(parents=True, exist_ok=True)
a.out.write_text(json.dumps(r, indent=2)+'\n')
print(json.dumps(dict(packKind=a.pack_kind, packResources=len(r['checks']),
                      serverOnlyResources=len(paths), mainClasses=len(r['classes']),
                      unchangedWeaponAndGoldenGunAssets=len(r['unchangedWeaponAndGoldenGunAssets']),
                      dynamicFovConfigured=enabled, dynamicFovPresent=present,
                      jarSha256=r['jar']['sha256'])))
