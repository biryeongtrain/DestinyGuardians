#!/usr/bin/env python3
"""W95 full inheritance/source/JAR/pack/cache audit. No build or launch."""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
sys.dont_write_bytecode=True
from verify_runtime_w84 import archive_verification
ROOT=Path(__file__).resolve().parents[2]; QA=ROOT/'docs/qa/2026-10-25/w95'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def require(v,m):
 if not v:raise SystemExit(m)
def snapshot():
 old=read(ROOT/'art/qa/w93/implementation.json');base=read(QA/'baseline.json');accepted=read(QA/'integration.json')
 require(sha(ROOT/'art/qa/w93/implementation.json')==base['previousProductManifestSha256'],'W93 manifest drift')
 require(sha(ROOT/'docs/qa/2026-10-25/w94/SHA256SUMS')==base['previousDiagnosticSealSha256'],'W94 seal drift')
 inherited=old['sha256']; current={p:sha(ROOT/p) for p in inherited}
 changed=sorted(p for p,h in inherited.items()if current[p]!=h)
 require(changed==sorted(accepted['acceptedOldChanges']),'Unexpected old-pin changes: '+str(changed))
 additions=set()
 for folder in ('src/main/java','src/main/resources','src/test/java','src/test/resources','src/gametest/java','src/gametest/resources'):
  paths={p.relative_to(ROOT).as_posix()for p in(ROOT/folder).rglob('*')if p.is_file()};oldpaths={p for p in inherited if p.startswith(folder+'/')}
  require(oldpaths<=paths,'Old sources removed');additions|=paths-oldpaths
 require(additions==set(accepted['newSourcePaths']),'Unexpected added sources: '+str(additions))
 current.update({p:sha(ROOT/p)for p in additions})
 for p,h in accepted['reviewedSourceSha256'].items():require(current[p]==h,'Reviewed-source drift '+p)
 external={p:sha(p)for p in old['externalSha256']};require(external==old['externalSha256'],'External drift')
 require(all(sha(p)==h for p,h in base['protected'].items()),'Protected Vision drift')
 require(all(sha(ROOT/x['path'])==x['sha256']for x in base['normalQAPlayers']),'Normal QA player drift')
 for p in (ROOT/'scripts').rglob('*'):
  if p.is_file()and 'w95'in p.name.lower():current[p.relative_to(ROOT).as_posix()]=sha(p)
 for p in ('art/qa/w93/implementation.json','docs/qa/2026-10-25/w95/baseline.json','docs/qa/2026-10-25/w95/integration.json'):current[p]=sha(ROOT/p)
 assets={p:h for p,h in current.items()if p.startswith('src/main/resources/assets/')};require(assets==old['clientAssets'],'Assets changed')
 return dict(sha256=current,externalSha256=external,clientAssets=assets,changedPreviousPins=changed)
def main():
 a=argparse.ArgumentParser();a.add_argument('--pack',type=Path,required=True);a.add_argument('--config',type=Path,required=True);a.add_argument('--cache',type=Path);a.add_argument('--native',action='store_true');a.add_argument('--finalize',action='store_true');a.add_argument('--out',type=Path,required=True);args=a.parse_args()
 before=snapshot();jar=ROOT/'build/libs/destiny-guardians-0.1.0+26.3.jar'
 require(read(args.config)['dynamic-fov-shader']==args.native,'Wrong FOV config')
 baseline=Path('/tmp/destiny-w40/client-run/downloads/653fa1a3-81b6-41a1-b143-b0663d0c53f1/5ef21f6f57815a927332cada904b723854b7e338')
 report=archive_verification(jar,args.pack,args.config,baseline,args.cache,before)
 with zipfile.ZipFile(jar)as z:
  require(not any('w94-probe'in n or n.startswith('qa/w94')or n.startswith('kim/biryeong/destiny/test/')or n.startswith('destiny-test')for n in z.namelist()),'QA code leaked')
 require(snapshot()==before,'Source changed during audit')
 manifest=ROOT/'art/qa/w95/implementation.json'
 if args.finalize:
  gates=read(QA/'gate-summary.json');require(not args.native and len(gates['finalPassingGates'])==2 and gates['jarSha256']==sha(jar),'Final gates mismatch')
  manifest.parent.mkdir(parents=True,exist_ok=True);manifest.write_text(json.dumps(dict(stage='W95',baseline='W93 product + W94 diagnostic',wholeGoalAchieved=False,pinnedVariant='headless',jarSha256=sha(jar),serverPackSha256=sha(args.pack),shaderConfigSha256=sha(args.config),**before),indent=2)+'\n')
 else:
  m=read(manifest);require(m['sha256']==before['sha256']and m['jarSha256']==sha(jar),'Final source/JAR drift')
  if not args.native:require(m['serverPackSha256']==sha(args.pack)and m['shaderConfigSha256']==sha(args.config),'Headless pack/config drift')
 report.update(stage='W95',sourcePins=len(before['sha256']),nativeVariant=args.native,wholeGoalAchieved=False,evidenceBoundary='Provenance only; encoded GT and native visual scope separately documented')
 args.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(stage='W95',sourcePins=len(before['sha256']),assets=len(before['clientAssets']),jarSha256=sha(jar))))
if __name__=='__main__':main()
