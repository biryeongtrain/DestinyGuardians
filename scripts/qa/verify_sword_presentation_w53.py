#!/usr/bin/env python3
"""Read-only W53 installed-limb and Blockbench evidence provenance, not native rendering."""
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bettermodel-jar', type=Path, required=True)
    p.add_argument('--model', type=Path, default=ROOT / 'build/run/gameTest/config/bettermodel/players/guardian_sword_w53.bbmodel')
    p.add_argument('--out', type=Path, default=ROOT / 'docs/qa/2026-10-24/w53/presentation-verification.json')
    a = p.parse_args()
    with zipfile.ZipFile(a.bettermodel_jar) as z:
        cores = [name for name in z.namelist()
                 if name.startswith('META-INF/jars/bettermodel-core-') and name.endswith('.jar')]
        assert len(cores) == 1, 'Expected exactly one nested BetterModel core'
        core_raw = z.read(cores[0])
        with zipfile.ZipFile(io.BytesIO(core_raw)) as core:
            base_raw = core.read('steve.bbmodel')
    template = json.loads(base_raw)
    expected = copy.deepcopy(template)
    expected['name'] = expected['model_identifier'] = 'guardian_sword_w53'
    resource = 'src/main/resources/destiny/animation/sword_w53.animation.json'
    raw = (ROOT / resource).read_bytes()
    clips = json.loads(raw)['animations']
    assert len(clips) == 8
    groups = {g['name']: g['uuid'] for g in template['groups']}
    for clip in copy.deepcopy(clips):
        clip['animators'] = {groups[animator['name']]: animator for animator in clip['animators'].values()}
        expected.setdefault('animations', []).append(clip)
    installed_raw = a.model.read_bytes()
    installed = json.loads(installed_raw)
    assert installed == expected, 'Actual installed sword model differs from fresh rig/remapped runtime clips'
    assert len(installed['animations']) == len(template.get('animations', [])) + 8
    previews = json.loads((ROOT / 'docs/qa/2026-10-24/w53/blockbench-preview.json').read_text())
    for record in previews['files']:
        assert sha((ROOT / record['path']).read_bytes()) == record['sha256'], record['path']
    report = {
        'stage': 'W53', 'installedModel': str(a.model), 'installedModelSha256': sha(installed_raw),
        'templateJar': str(a.bettermodel_jar), 'templateJarSha256': sha(a.bettermodel_jar.read_bytes()),
        'nestedCorePath': cores[0], 'nestedCoreSha256': sha(core_raw),
        'templateSha256': sha(base_raw), 'sourceResource': resource, 'sourceResourceSha256': sha(raw),
        'runtimeInheritedClips': len(template.get('animations', [])), 'runtimeSwordClips': 8,
        'runtimeTotalClips': len(installed['animations']), 'runtimeRigGroups': len(installed['groups']),
        'sourceArtInheritedClips': 21, 'sourceArtTotalClips': 29,
        'allTemplateFieldsPreservedExceptIdentifiersAndAddedClips': True,
        'allRuntimeClipsExactlyRemappedByBoneName': True,
        'previewEvidenceFiles': len(previews['files']), 'blockbenchFrames': previews['animationFrames'],
        'nativeFramebuffers': 0, 'nativeInputVerified': False,
        'evidenceBoundary': 'Installed GameTest model JSON and saved Blockbench bytes only. '
                            'Preview attachment is approximate; no exact native grip, skin, IK or client rendering claim.'
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
