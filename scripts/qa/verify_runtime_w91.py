#!/usr/bin/env python3
"""Master integration acceptance and full source/JAR/pack/cache audit, never a build/launch.
The acceptance inventory is authored after code review, not inferred by this verifier.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
sys.dont_write_bytecode=True
from verify_runtime_w84 import archive_verification
ROOT=Path(__file__).resolve().parents[2];QA=ROOT/'docs/qa/2026-10-25/w91'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def require(ok,msg):
 if not ok:raise SystemExit(msg)
def snapshot():
 old=read(ROOT/'art/qa/w90/implementation.json');base=read(QA/'baseline.json');accepted=read(QA/'integration.json')
 require(sha(ROOT/'art/qa/w90/implementation.json')==base['previousManifestSha256'],'W90 manifest drift')
 inherited=old['sha256'];current={p:sha(ROOT/p)for p in inherited}
 changed=sorted(p for p,h in inherited.items()if current[p]!=h)
 require(changed==sorted(accepted['acceptedOldChanges']),'Changes differ from reviewed acceptance')
 additions=set()
 for folder in ('src/main/java','src/main/resources','src/test/java','src/test/resources','src/gametest/java','src/gametest/resources'):
  paths={p.relative_to(ROOT).as_posix()for p in(ROOT/folder).rglob('*')if p.is_file()}
  old_paths={p for p in inherited if p.startswith(folder+'/')}
  require(old_paths<=paths,'Old source removed: '+folder);additions|=paths-old_paths
 require(additions==set(accepted['newSourcePaths']),'Added source inventory differs from reviewed acceptance')
 current.update({p:sha(ROOT/p)for p in additions})
 for p,h in accepted['reviewedSourceSha256'].items():require(current[p]==h,'Reviewed source changed: '+p)
 external={p:sha(p)for p in old['externalSha256']};require(external==old['externalSha256'],'External source drift')
 require(all(sha(p)==h for p,h in base['protected'].items()),'Protected Vision drift')
 require(all(sha(ROOT/x['path'])==x['sha256']for x in base['normalQAPlayers']),'Normal QA player drift')
 for folder in ('art/weapons/w91-izanagi','art/weapons/w91-swap','scripts'):
  for p in (ROOT/folder).rglob('*'):
   if p.is_file() and (folder!='scripts' or 'w91' in p.name.lower()):current[p.relative_to(ROOT).as_posix()]=sha(p)
 for path in ('art/qa/w90/implementation.json','docs/qa/2026-10-25/w91/baseline.json','docs/qa/2026-10-25/w91/integration.json'):
  current[path]=sha(ROOT/path)
 assets={p:h for p,h in current.items()if p.startswith('src/main/resources/assets/')}
 require(len(assets)==accepted['clientAssetCount'],'Accepted asset count mismatch')
 return dict(sha256=current,externalSha256=external,clientAssets=assets,changedPreviousPins=changed)
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--pack',type=Path,required=True);a.add_argument('--config',type=Path,required=True);a.add_argument('--cache',type=Path);a.add_argument('--native',action='store_true');a.add_argument('--finalize',action='store_true');a.add_argument('--out',type=Path,required=True);args=a.parse_args()
 before=snapshot();jar=ROOT/'build/libs/destiny-guardians-0.1.0+26.3.jar'
 require(read(args.config)['dynamic-fov-shader']==args.native,'Wrong FOV variant')
 baseline=Path('/tmp/destiny-w40/client-run/downloads/653fa1a3-81b6-41a1-b143-b0663d0c53f1/5ef21f6f57815a927332cada904b723854b7e338')
 report=archive_verification(jar,args.pack,args.config,baseline,args.cache,before)
 with zipfile.ZipFile(jar)as z:
  require(not any(n.startswith('destiny-test') and n.endswith('.mixins.json') for n in z.namelist()),'Test-only mixin leaked into product JAR')
  require(not any(n.startswith('kim/biryeong/destiny/test/')for n in z.namelist()),'Test classes leaked into product JAR')
 require(snapshot()==before,'Source changed during audit')
 report.update(stage='W91',sourcePins=len(before['sha256']),changedPreviousPins=before['changedPreviousPins'],wholeGoalAchieved=False,nativeVariant=args.native,evidenceBoundary='Source/JAR/pack/cache provenance only. Framebuffer and native input acceptance separately documented.')
 manifest=ROOT/'art/qa/w91/implementation.json'
 if args.finalize:
  require(not args.native,'Pin headless first')
  gates=read(QA/'gate-summary.json');require(len(gates['finalPassingGates'])==2 and gates['jarSha256']==sha(jar),'Final gates/JAR mismatch')
  manifest.parent.mkdir(parents=True,exist_ok=True);manifest.write_text(json.dumps(dict(stage='W91',baseline='W90',pinStatus='pinned',wholeGoalAchieved=False,pinnedVariant='headless',jarSha256=sha(jar),serverPackSha256=sha(args.pack),shaderConfigSha256=sha(args.config),**before),indent=2)+'\n')
 else:
  m=read(manifest);require(m['sha256']==before['sha256'] and m['jarSha256']==sha(jar),'Final pins differ')
  if not args.native:require(m['serverPackSha256']==sha(args.pack) and m['shaderConfigSha256']==sha(args.config),'Pinned pack/config differ')
 args.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(stage='W91',sourcePins=len(before['sha256']),assets=len(before['clientAssets']),native=args.native,jarSha256=sha(jar),out=str(args.out))))
if __name__=='__main__':main()
