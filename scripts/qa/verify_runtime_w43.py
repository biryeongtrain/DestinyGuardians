#!/usr/bin/env python3
"""Read-only W43 metadata/class provenance plus the W42 model/HUD pack gate."""
from pathlib import Path
import argparse, json, zipfile
from verify_runtime_w42 import verify, ROOT, sha

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--jar',type=Path,default=ROOT/'build/libs/destiny-guardians-0.1.0+26.3.jar')
    p.add_argument('--server-pack',type=Path,default=ROOT/'run/server/polymer/resource_pack.zip')
    p.add_argument('--baseline-cache',type=Path,required=True)
    p.add_argument('--client-cache',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    report=verify(a.jar.resolve(),a.server_pack.resolve(),a.baseline_cache.resolve(),a.client_cache.resolve() if a.client_cache else None)
    report['serverOnlySourceJar']=[]
    paths=['destiny/weapons/w43-ballistics.json','data/destiny/tags/entity_type/weapon_precision_humanoids.json',
           'META-INF/licenses/oracle_engine.MIT-LICENSE','META-INF/licenses/oracle_engine.UNLICENSE']
    with zipfile.ZipFile(a.jar) as z:
        for path in paths:
            raw=(ROOT/'src/main/resources'/path).read_bytes()
            assert z.read(path)==raw,path
            report['serverOnlySourceJar'].append(dict(path=path,sha256=sha(raw)))
    metadata=json.loads((ROOT/'art/weapons/w43/extraction.json').read_text())
    assert sha((ROOT/'src/main/resources'/paths[0]).read_bytes())==metadata['runtimeSha256']
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(packResources=len(report['checks']),serverOnlyResources=len(paths),
                          classes=len(report['classes']),unchangedWeaponAndGoldenGunAssets=len(report['unchangedWeaponAndGoldenGunAssets']),
                          clientCacheVerified=report['clientCache']['verified'],jarSha256=report['jar']['sha256'])))
