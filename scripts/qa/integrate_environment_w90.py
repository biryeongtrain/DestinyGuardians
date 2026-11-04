#!/usr/bin/env python3
"""Master's one-time environment integration; preserves old gameplay/test bodies byte-for-byte."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / 'docs/qa/2026-10-25/w90'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def main():
    plan = json.loads((QA / 'environment-plan.json').read_text())
    assert not plan['applied'], 'One-time integration already applied'
    migration = json.loads((QA / 'cleanup-migration.json').read_text())
    assert migration['existingFileCount'] == 78 and migration['registrationCount'] == 139
    inventory = json.loads((QA / 'before-inventory.json').read_text())['files']
    replacements = {x['path']: x for x in migration['files']}
    # Check the complete 95-file checkpoint, not just git-tracked files.
    for row in inventory:
        before = (QA / 'before' / row['path']).read_bytes()
        assert sha(before) == row['sha256'], row['path']
        expected = before
        if row['path'] in replacements:
            entry = replacements[row['path']]
            assert sha(before) == entry['beforeSha256']
            for r in sorted(entry['replacements'], key=lambda r: r['originalByteOffset'], reverse=True):
                pos = r['originalByteOffset']
                old = r['before'].encode()
                assert expected[pos:pos + len(old)] == old
                expected = expected[:pos] + r['after'].encode() + expected[pos + len(old):]
            assert sha(expected) == entry['afterSha256'], row['path']
        assert (ROOT / row['path']).read_bytes() == expected, 'Unexpected pre-integration edit: ' + row['path']

    mapping = plan['mapping']
    fov = {
        'fovIsRestoredAndExternalOwnershipIsNotOverwritten': 'w90_fov_w44',
        'reloadSwapSuspendAndExternalFovTakeoverResetOwnedScope': 'w90_fov_w45',
        'fovTakeoverReleasesBothInTheSameTickAndPreservesForeignFov': 'w90_fov_w75',
        'realReloadSuperHandlingBlockedAdsAndExternalCamerasSuppressIncomingFlinch': 'w90_fov_w85',
    }
    env_root = ROOT / 'src/gametest/resources/data/destiny-test/test_environment'
    for original, new in mapping.items():
        if original in ('minecraft:default', 'destiny-test:w78_allied'):
            continue
        dump(env_root / (new.split(':')[1] + '.json'), {
            'type': 'minecraft:all_of', 'definitions': ['destiny-test:w90_isolated', original]})
    for name in fov.values():
        dump(env_root / (name + '.json'), {
            'type': 'minecraft:all_of', 'definitions': ['destiny-test:w90_isolated', 'minecraft:default']})

    counts = {'oldAnnotations': 0, 'cleanupRegressions': 0, 'fovOverrides': 0}
    for path in sorted((ROOT / 'src/gametest/java').rglob('*.java')):
        if path.name == 'SpawnIsolationW90GameTests.java':
            continue  # Its explicit registered-environment contracts were already reviewed.
        original = path.read_text()
        current = original
        # Only known environment constants, not structure IDs, test IDs or other literals.
        current = re.sub(r'(String\s+(?:GLOBAL|VISUAL_ENV)\s*=\s*)"([^"]+)"',
                         lambda m: m[1] + '"' + mapping.get(m[2], m[2]) + '"', current)

        def annotation(m):
            args, method = m[1], m[3]
            counter = 'cleanupRegressions' if path.name == 'FixtureCleanupW90GameTests.java' else 'oldAnnotations'
            counts[counter] += 1
            if 'environment' not in args:
                args += ', environment = "destiny-test:w90_isolated"'
            else:
                args = re.sub(r'(environment\s*=\s*)"([^"]+)"',
                              lambda n: n[1] + '"' + mapping.get(n[2], n[2]) + '"', args)
            if method in fov:
                args = re.sub(r'environment\s*=\s*(?:"[^"]+"|\w+)',
                              'environment = "destiny-test:' + fov[method] + '"', args)
                counts['fovOverrides'] += 1
            return '@GameTest(' + args + ')' + m[2] + method + '('

        # Group 3 preserves every inter-annotation/method byte, including whitespace.
        current = re.sub(r'@GameTest\(([^)]*)\)(\s+public void\s+)(\w+)\(',
                         annotation, current)
        if current != original:
            path.write_text(current)
    assert counts == {'oldAnnotations': 758, 'cleanupRegressions': 11, 'fovOverrides': 4}, counts
    mod_path = ROOT / 'src/gametest/resources/fabric.mod.json'
    mod = json.loads(mod_path.read_text())
    mod['mixins'] = ['destiny-test-cleanup.mixins.json']
    mod['entrypoints']['fabric-gametest'] += [
        'kim.biryeong.destiny.test.SpawnIsolationW90GameTests',
        'kim.biryeong.destiny.test.FixtureCleanupW90GameTests']
    dump(mod_path, mod)
    plan.update(applied=True, parentVerifiedCleanupRegistrations=139, counts=counts,
                fovMethodEnvironments={k: 'destiny-test:' + v for k, v in fov.items()})
    dump(QA / 'environment-plan.json', plan)
    print(json.dumps(counts))


if __name__ == '__main__':
    main()
