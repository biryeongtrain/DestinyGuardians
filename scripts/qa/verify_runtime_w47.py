#!/usr/bin/env python3
"""W47 read-only provenance: unchanged W44 base, new scopes and actual client pack."""
from pathlib import Path
import argparse,json,zipfile
from contextlib import ExitStack
from verify_runtime_w42 import verify,ROOT,sha

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--jar',type=Path,default=ROOT/'build/libs/destiny-guardians-0.1.0+26.3.jar')
p.add_argument('--server-pack',type=Path,default=ROOT/'run/server/polymer/resource_pack.zip')
p.add_argument('--baseline-cache',type=Path,required=True)
p.add_argument('--client-cache',type=Path)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
r=verify(a.jar.resolve(),a.server_pack.resolve(),a.baseline_cache.resolve(),a.client_cache.resolve() if a.client_cache else None)
paths=['destiny/weapons/w43-ballistics.json','data/destiny/tags/entity_type/weapon_precision_humanoids.json',
       'META-INF/licenses/oracle_engine.MIT-LICENSE','META-INF/licenses/oracle_engine.UNLICENSE',
       'destiny/weapons/w44-aim.json','destiny/weapons/w46-timing.json']
r['serverOnlySourceJar']=[]
with ExitStack() as context:
    jar=context.enter_context(zipfile.ZipFile(a.jar));pack=context.enter_context(zipfile.ZipFile(a.server_pack))
    cache=context.enter_context(zipfile.ZipFile(a.client_cache)) if a.client_cache else None
    for path in paths:
        raw=(ROOT/'src/main/resources'/path).read_bytes();assert jar.read(path)==raw,path
        r['serverOnlySourceJar'].append(dict(path=path,sha256=sha(raw)))
    for manifestPath in ['art/hud/w44-reticle/manifest.json','art/hud/w45-scope/manifest.json',
                         'art/weapons/w45-models/manifest.json','art/weapons/w47/manifest.json']:
        manifest=json.loads((ROOT/manifestPath).read_text())
        for path,expected in manifest['sha256'].items():
            source=ROOT/path;raw=source.read_bytes();assert sha(raw)==expected,path
            if not source.is_relative_to(ROOT/'src/main/resources'):continue
            name=str(source.relative_to(ROOT/'src/main/resources'))
            assert jar.read(name)==pack.read(name)==raw,name
            if cache:assert cache.read(name)==raw,name
            r['checks'].append(dict(path=name,sha256=expected,sourceJarServerPack=True,clientCache=cache is not None))
    name='assets/minecraft/shaders/include/projection.glsl'
    projection=(ROOT/'libs/minigame-lib/src/main/resources/shaders/optional/projection.glsl').read_bytes()
    assert pack.read(name)==projection,'FOV shader must be in server pack'
    if cache:assert cache.read(name)==projection,'FOV shader must actually be in received pack'
    r['dynamicFovProjection']=dict(path=name,sha256=sha(projection),sourceServerPack=True,clientCache=cache is not None)
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(dict(packResources=len(r['checks']),serverOnlyResources=len(paths),classes=len(r['classes']),
                     unchangedWeaponAndGoldenGunAssets=len(r['unchangedWeaponAndGoldenGunAssets']),jarSha256=r['jar']['sha256'])))
