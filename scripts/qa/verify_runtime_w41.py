#!/usr/bin/env python3
"""Read-only W41 provenance gate. A downloaded cache is not a framebuffer test."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(jar, server_pack, baseline_cache, client_cache=None):
    old = json.loads((ROOT / 'docs/qa/2026-10-24/w40/runtime-pack-verification.json').read_text())
    manifest = json.loads((ROOT / 'art/hud/w41/manifest.json').read_text())
    paths = {c['path'] for c in old['checks']}
    for source, expected in manifest['sha256'].items():
        path = Path(source)
        assert sha((ROOT / path).read_bytes()) == expected, source
        paths.add(str(path.relative_to('src/main/resources')))
    assert len(paths) == 120, len(paths)
    report = {'jar': {'path': str(jar.relative_to(ROOT)), 'sha256': sha(jar.read_bytes())},
              'serverPack': {'sha256': sha(server_pack.read_bytes())},
              'clientCache': {'verified': client_cache is not None},
              'checks': [], 'classes': [], 'unchangedWeaponAndGoldenGunAssets': [],
              'evidenceBoundary': 'Byte equality proves provenance, not pack application or visual correctness.'}
    if client_cache:
        report['clientCache']['sha256'] = sha(client_cache.read_bytes())
        assert report['clientCache']['sha256'] == report['serverPack']['sha256']
    archives = [zipfile.ZipFile(jar), zipfile.ZipFile(server_pack)]
    if client_cache:
        archives.append(zipfile.ZipFile(client_cache))
    try:
        for path in sorted(paths):
            raw = (ROOT / 'src/main/resources' / path).read_bytes()
            assert all(z.read(path) == raw for z in archives), path
            report['checks'].append({'path': path, 'sha256': sha(raw),
                                     'sourceJarServerPack': True,
                                     'clientCache': client_cache is not None})
        for source in sorted((ROOT / 'build/classes/java/main').rglob('*.class')):
            path = str(source.relative_to(ROOT / 'build/classes/java/main'))
            assert archives[0].read(path) == source.read_bytes(), path
            report['classes'].append({'path': path, 'sha256': sha(source.read_bytes()),
                                      'runtimeClasspathJar': True})
        with zipfile.ZipFile(baseline_cache) as baseline:
            assert sha(baseline_cache.read_bytes()) == old['clientCache']['sha256']
            for path in old['unchangedWeaponAndGoldenGunAssets']:
                raw = baseline.read(path)
                assert (ROOT / 'src/main/resources' / path).read_bytes() == raw, path
                assert all(z.read(path) == raw for z in archives), path
                report['unchangedWeaponAndGoldenGunAssets'].append(path)
        path = 'destiny/weapons/w40-characteristics.json'
        assert archives[0].read(path) == (ROOT / 'src/main/resources' / path).read_bytes()
        report['metadataSourceJar'] = True
    finally:
        for archive in archives:
            archive.close()
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--jar', type=Path, default=ROOT / 'build/libs/destiny-guardians-0.1.0+26.3.jar')
    p.add_argument('--server-pack', type=Path, default=ROOT / 'run/server/polymer/resource_pack.zip')
    p.add_argument('--baseline-cache', type=Path, required=True)
    p.add_argument('--client-cache', type=Path)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = verify(a.jar.resolve(), a.server_pack.resolve(), a.baseline_cache.resolve(),
                    a.client_cache.resolve() if a.client_cache else None)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'resources': len(result['checks']), 'classes': len(result['classes']),
                      'unchangedWeaponAndGoldenGunAssets': len(result['unchangedWeaponAndGoldenGunAssets']),
                      'clientCacheVerified': result['clientCache']['verified'],
                      'jarSha256': result['jar']['sha256']}))
