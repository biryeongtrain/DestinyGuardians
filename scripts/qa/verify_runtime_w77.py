#!/usr/bin/env python3
"""Read-only full W77 source/JAR/pack provenance. Framebuffer proof is separate."""
import argparse, hashlib, json, zipfile
from pathlib import Path
from verify_runtime_w42 import verify, ROOT, sha
PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument("--jar",type=Path,default=ROOT/"build/libs/destiny-guardians-0.1.0+26.3.jar")
PARSER.add_argument("--server-pack",type=Path,required=True)
PARSER.add_argument("--shader-config",type=Path,required=True)
PARSER.add_argument("--baseline-cache",type=Path,required=True)
PARSER.add_argument("--client-cache",type=Path)
PARSER.add_argument("--out",type=Path,required=True)

def main():
    a=PARSER.parse_args()
    report=verify(a.jar.resolve(),a.server_pack.resolve(),a.baseline_cache.resolve(),a.client_cache.resolve() if a.client_cache else None)
    manifest=json.loads((ROOT/"art/weapons/w77/implementation.json").read_text())
    assert manifest["jarSha256"]==sha(a.jar.read_bytes()),"Manifest pins another JAR"
    for path,h in manifest["sha256"].items():
        assert sha((ROOT/path).read_bytes())==h,path
    assets=sorted(p for p in (ROOT/"src/main/resources/assets").rglob("*") if p.is_file())
    shared={"assets/destiny/sounds.json","assets/destiny/lang/en_us.json","assets/destiny/lang/ko_kr.json"}
    w76=json.loads((ROOT/"src/main/resources/destiny/hud/w76-vanilla.json").read_text())
    shared.update("assets/minecraft/lang/"+loc+".json" for loc in w76["locales"])
    baseline=json.loads((ROOT/"docs/qa/2026-10-24/w77/baseline.json").read_text())
    current={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in assets}
    assert current==baseline["clientAssets"], "Existing client asset drift"
    records=[];server=[]
    with zipfile.ZipFile(a.jar) as jar,zipfile.ZipFile(a.server_pack) as pack:
        for source in assets:
            name=str(source.relative_to(ROOT/"src/main/resources"));raw=source.read_bytes()
            assert jar.read(name)==raw,name
            actual=pack.read(name)
            if name in shared:
                assert json.loads(actual)==json.loads(raw),name
            else:
                assert actual==raw,name
            records.append(dict(path=name,sourceJarSha256=sha(raw),packSha256=sha(actual),jsonReserialized=name in shared))
        for source in sorted((ROOT/"src/main/resources").rglob("*")):
            if not source.is_file() or source.is_relative_to(ROOT/"src/main/resources/assets"):continue
            name=str(source.relative_to(ROOT/"src/main/resources"))
            if name=="fabric.mod.json":continue # Gradle version expansion, verified separately below.
            assert jar.read(name)==source.read_bytes(),name
            server.append(dict(path=name,sha256=sha(source.read_bytes())))
        fabric=json.loads(jar.read("fabric.mod.json"));assert fabric["depends"]["minecraft"]=="26.3"
        enabled=json.loads(a.shader_config.read_text()).get("dynamic-fov-shader",False)
        assert type(enabled) is bool
        projection="assets/minecraft/shaders/include/projection.glsl"
        assert (projection in pack.namelist())==enabled
        if enabled:assert pack.read(projection)==(ROOT/"libs/minigame-lib/src/main/resources/shaders/optional/projection.glsl").read_bytes()
    report.update(stage="W77",sourcePins=len(manifest["sha256"]),allClientAssets=records,allServerResources=server,
                  dynamicFovConfigured=enabled,newClientAssets=0,fullHotbarSuppression=False,nativeClientRenderingCertified=False,
                  evidenceBoundary="Source/JAR/pack provenance only; no precision-kill gameplay, actual VFX framebuffer or acoustic claim.")
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(dict(stage="W77",sourcePins=report["sourcePins"],allClientAssets=len(records),serverResources=len(server),mainClasses=len(report["classes"]),preservedWeapons=len(report["unchangedWeaponAndGoldenGunAssets"]),jarSha256=report["jar"]["sha256"])))
if __name__=="__main__":main()
