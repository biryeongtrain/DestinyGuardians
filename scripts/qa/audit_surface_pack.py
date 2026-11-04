#!/usr/bin/env python3
"""Check emitted W123-migration bytes; not a client parser or visual acceptance.

Read the current manifest only after worker integration/regeneration. No server,
download, GUI, game input or source modification is performed by this helper.
"""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit(pack, resources):
    manifest = json.loads((resources / 'weapon_surface_w123/manifest.json').read_bytes())
    models, sprites, fallbacks = [], {}, []
    assert manifest['schema'] == 1 and manifest['stage'] == 'W123'
    targets = manifest['targets']
    assert targets and len({row['path'] for row in targets}) == len(targets)
    with ZipFile(pack) as archive:
        for row in targets:
            expected = (resources / row['replacement']).read_bytes()
            emitted = archive.read(row['path'])
            assert sha(expected) == row['replacementSha256'], row['replacement']
            assert emitted == expected, row['path']
            model = json.loads(emitted)
            assert 0 < len(model['elements']) <= manifest['maxAssembledElements']
            models.append(dict(path=row['path'],bytes=len(emitted),sha256=sha(emitted)))
            for sprite in model.get('textures', {}).values():
                if sprite.startswith('destiny:item/weapon/w123/'):
                    texture = 'assets/destiny/textures/' + sprite.split(':', 1)[1] + '.png'
                    data = archive.read(texture)
                    assert data == (resources / texture).read_bytes(), texture
                    sprites[texture] = dict(path=texture,bytes=len(data),sha256=sha(data))
        # Existing standalone HUD planes + the one glaive FX root are repaired
        # output-only. Preserve every other JSON field, including all UVs/tints.
        candidates = list((resources/'assets/destiny/models/gui/hud').rglob('*.json'))
        fx = resources/'assets/destiny/models/fx/glaive_shield_w41.json'
        if fx.is_file(): candidates.append(fx)
        for source in candidates:
            old = json.loads(source.read_bytes())
            if ('parent' in old or 'elements' not in old or 'textures' not in old
                    or 'particle' in old['textures']): continue
            path = source.relative_to(resources).as_posix()
            emitted = json.loads(archive.read(path))
            particle = emitted['textures'].pop('particle')
            assert emitted == old, path
            namespace, sprite = particle.split(':', 1)
            archive.getinfo('assets/'+namespace+'/textures/'+sprite+'.png')
            fallbacks.append(dict(path=path,particle=particle,allOtherFieldsUnchanged=True))
    data = pack.read_bytes()
    return dict(pack=str(pack),bytes=len(data),sha1=hashlib.sha1(data).hexdigest(),sha256=sha(data),
                models=models,modelCount=len(models),textures=list(sprites.values()),textureCount=len(sprites),
                particleFallbacks=fallbacks,particleFallbackCount=len(fallbacks),
                evidence='actual emitted ZIP bytes only; not native parsing, downloaded pack, PNG, audio or FPS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', required=True, type=Path)
    parser.add_argument('--resources', type=Path, default=ROOT/'src/main/resources')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.pack, args.resources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('modelCount','textureCount','particleFallbackCount','sha256')}))
