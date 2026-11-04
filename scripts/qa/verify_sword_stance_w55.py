#!/usr/bin/env python3
"""W55 read-only independent installed limb verification. No native rendering claim."""
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
    p.add_argument('--model', type=Path, default=ROOT / 'build/run/gameTest/config/bettermodel/players/guardian_sword_w55.bbmodel')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    with zipfile.ZipFile(a.bettermodel_jar) as z:
        cores = [n for n in z.namelist() if n.startswith('META-INF/jars/bettermodel-core-') and n.endswith('.jar')]
        assert len(cores) == 1
        core_raw = z.read(cores[0])
        with zipfile.ZipFile(io.BytesIO(core_raw)) as core:
            base_raw = core.read('steve.bbmodel')
    template = json.loads(base_raw)
    expected = copy.deepcopy(template)
    expected['name'] = expected['model_identifier'] = 'guardian_sword_w55'
    resource = 'src/main/resources/destiny/animation/sword_w55.animation.json'
    raw = (ROOT / resource).read_bytes()
    clips = json.loads(raw)['animations']
    previous = json.loads((ROOT / 'src/main/resources/destiny/animation/sword_w53.animation.json').read_bytes())['animations']
    assert len(clips) == 12 and clips[:8] == previous
    assert {c['name'] for c in clips[8:]} == {f'h15_sword_{s}' for s in ('idle', 'move', 'guard', 'air')}
    assert all(c['loop'] == 'loop' for c in clips[8:])
    groups = {g['name']: g['uuid'] for g in template['groups']}
    for clip in copy.deepcopy(clips):
        clip['animators'] = {groups[animator['name']]: animator for animator in clip['animators'].values()}
        expected.setdefault('animations', []).append(clip)
    installed_raw = a.model.read_bytes()
    installed = json.loads(installed_raw)
    assert installed == expected, 'Installed W55 differs from fresh exact rig/name-remapped clip build'
    assert len(installed['animations']) == len(template.get('animations', [])) + 12
    previous_implementation = json.loads((ROOT / 'art/weapons/w54/implementation.json').read_text())
    preserved = {}
    for path in ('art/blockbench/animations/guardian_sword_w53.bbmodel',
                 'src/main/resources/destiny/animation/sword_w53.animation.json',
                 'src/main/java/kim/biryeong/destiny/fx/SwordModelAssets.java'):
        digest = sha((ROOT / path).read_bytes())
        assert digest == previous_implementation['sha256'][path], path
        preserved[path] = digest
    report = dict(stage='W55', installedModel=str(a.model), installedModelSha256=sha(installed_raw),
                  templateJar=str(a.bettermodel_jar), templateJarSha256=sha(a.bettermodel_jar.read_bytes()),
                  nestedCoreSha256=sha(core_raw), templateSha256=sha(base_raw),
                  sourceResource=resource, sourceResourceSha256=sha(raw),
                  runtimeInheritedClips=len(template.get('animations', [])), runtimeAttackClips=8,
                  runtimeStanceLoops=4, runtimeTotalClips=len(installed['animations']),
                  runtimeRigGroups=len(installed['groups']),
                  allTemplateFieldsPreservedExceptIdentifiersAndAddedClips=True,
                  allRuntimeClipsExactlyRemappedByBoneName=True, originalAttacksUnchanged=True,
                  preservedPriorVersion=preserved, nativeFramebuffers=0, nativeInputVerified=False,
                  evidenceBoundary='Installed isolated GameTest JSON/rig/clip equality only. No native grip, skin rendering, IK or camera interpolation proof.')
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
