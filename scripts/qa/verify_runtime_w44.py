#!/usr/bin/env python3
"""W44 read-only provenance: W42/W43 base, reticle assets, ADS metadata and FOV opt-in."""
from pathlib import Path
import argparse,json,zipfile
from verify_runtime_w42 import verify,ROOT,sha

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--jar',type=Path,default=ROOT/'build/libs/destiny-guardians-0.1.0+26.3.jar')
p.add_argument('--server-pack',type=Path,default=ROOT/'run/server/polymer/resource_pack.zip')
p.add_argument('--baseline-cache',type=Path,required=True)
p.add_argument('--client-cache',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
r=verify(a.jar.resolve(),a.server_pack.resolve(),a.baseline_cache.resolve(),a.client_cache.resolve())
paths=['destiny/weapons/w43-ballistics.json','data/destiny/tags/entity_type/weapon_precision_humanoids.json',
       'META-INF/licenses/oracle_engine.MIT-LICENSE','META-INF/licenses/oracle_engine.UNLICENSE',
       'destiny/weapons/w44-aim.json']
r['serverOnlySourceJar']=[]
with zipfile.ZipFile(a.jar) as jar,zipfile.ZipFile(a.server_pack) as pack,zipfile.ZipFile(a.client_cache) as cache:
    for path in paths:
        raw=(ROOT/'src/main/resources'/path).read_bytes();assert jar.read(path)==raw,path
        r['serverOnlySourceJar'].append(dict(path=path,sha256=sha(raw)))
    manifest=json.loads((ROOT/'art/hud/w44-reticle/manifest.json').read_text())
    for path,expected in manifest['sha256'].items():
        source=ROOT/path;raw=source.read_bytes();assert sha(raw)==expected,path
        if not source.is_relative_to(ROOT/'src/main/resources'):continue
        name=str(source.relative_to(ROOT/'src/main/resources'))
        assert jar.read(name)==pack.read(name)==cache.read(name)==raw,name
        r['checks'].append(dict(path=name,sha256=expected,sourceJarServerPack=True,clientCache=True))
    name='assets/minecraft/shaders/include/projection.glsl'
    projection=(ROOT/'libs/minigame-lib/src/main/resources/shaders/optional/projection.glsl').read_bytes()
    assert pack.read(name)==cache.read(name)==projection,'FOV shader must actually be in received pack'
    r['dynamicFovProjection']=dict(path=name,sha256=sha(projection),sourceServerPackClientCache=True)
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(dict(packResources=len(r['checks']),serverOnlyResources=len(paths),classes=len(r['classes']),
                     unchangedWeaponAndGoldenGunAssets=len(r['unchangedWeaponAndGoldenGunAssets']),jarSha256=r['jar']['sha256'])))
