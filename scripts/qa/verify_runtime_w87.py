#!/usr/bin/env python3
"""W87 fixture-only diagnostics provenance. Never builds/launches; audit is read-only.
Finalization is parent-only after gates/workers stop and verifies archives BEFORE pinning.
Existing W86 main code, 6588 assets, library sources and primary JAR/pack must remain exact.
"""
import argparse,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
from verify_runtime_w84 import archive_verification
from pin_runtime_w86 import run_components
ROOT=Path(__file__).resolve().parents[2]
QA=ROOT/'docs/qa/2026-10-25/w87'
MANIFEST=ROOT/'art/qa/w87/implementation.json'
ALLOWED={
 'src/gametest/java/kim/biryeong/destiny/test/TestPlayers.java',
 'src/gametest/java/kim/biryeong/destiny/test/IncomingDamageW86GameTests.java',
 'src/gametest/java/kim/biryeong/destiny/test/WeaponAceW83GameTests.java',
 'src/gametest/resources/fabric.mod.json',
}
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,reason):
 if not ok:raise SystemExit(reason)
def files(folder):return {p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*') if p.is_file()}
def snapshot():
 b=read(QA/'baseline.json');old=b['previousImplementation'];previous=old['sha256']
 require(old==read(ROOT/'art/hud/w86/implementation.json'),'Previous W86 manifest changed')
 require(len(previous)==1550 and len(b['clientAssets'])==6588,'Wrong baseline inventory')
 require(files('src/main/java')=={p for p in previous if p.startswith('src/main/java/')},'Production Java inventory changed')
 require(files('src/test/java')=={p for p in previous if p.startswith('src/test/java/')},'Pure test inventory changed')
 expected_resources={p for p in previous if p.startswith('src/main/resources/') and not p.startswith('src/main/resources/assets/')}|set(b['clientAssets'])
 require(files('src/main/resources')==expected_resources,'Production resource inventory changed')
 library_now={p.relative_to(ROOT).as_posix() for p in (ROOT/'libs/minigame-lib').rglob('*') if p.is_file() and '/build/'not in str(p) and '/.gradle/'not in str(p) and '/.git/'not in str(p)}
 require(library_now==set(b['librarySources']),'Library source inventory changed')
 current={p:sha(ROOT/p) for p in sorted(files('src/main/resources/assets'))}
 require(current==b['clientAssets'],'W87 fixture-only work must preserve ALL6588 client asset bytes')
 for p,h in b['librarySources'].items():require(sha(ROOT/p)==h,'Unexpected library change: '+p)
 paths=set(previous)|set(b['librarySources'])|{'art/hud/w86/implementation.json','docs/qa/2026-10-25/w87/baseline.json','docs/qa/2026-10-25/w87/w86-pack.zip'}
 for folder in ('src/main/java','src/main/resources','src/test/java','src/test/resources','src/gametest/java','src/gametest/resources'):
  paths.update(files(folder))
 paths.update(p for p in files('scripts') if 'w87' in Path(p).name.lower())
 hashes={p:sha(ROOT/p) for p in sorted(paths)}
 changed=sorted(p for p,h in previous.items() if hashes[p]!=h)
 require(set(changed)<=ALLOWED,'Unapproved old source/art/resource change: '+str(changed))
 external={p:sha(Path(p)) for p in old['externalSha256']}
 require(external==old['externalSha256'],'Inherited external source changed')
 require(sha(QA/'w86-pack.zip')==old['serverPackSha256'],'Archived W86 pack drift')
 return dict(sha256=hashes,externalSha256=external,clientAssets=current,changedPreviousPins=changed,
  previousPins=1550,addedPins=sorted(set(hashes)-set(previous)),librarySourcePins=len(b['librarySources']),
  preservation=dict(previousClientAssets=6588,allClientBytesExact=True,soundEvents=162,productionSourceUnchanged=True,librarySourcesUnchanged=True))
def main():
 a=argparse.ArgumentParser(description=__doc__);mode=a.add_mutually_exclusive_group();mode.add_argument('--audit',action='store_true');mode.add_argument('--finalize',action='store_true')
 a.add_argument('--python',type=Path,default=Path('/tmp/destiny-hud-venv/bin/python'));a.add_argument('--server-pack',type=Path);a.add_argument('--shader-config',type=Path);a.add_argument('--baseline-cache',type=Path);a.add_argument('--out',type=Path);args=a.parse_args()
 before=snapshot()
 if args.audit:
  require(not args.out,'Audit is stdout-only');print(json.dumps(dict(stage='W87',sourcePins=len(before['sha256']),**{k:v for k,v in before.items() if k not in ('sha256','externalSha256','clientAssets')},runtimeVerified=False),indent=2));return
 require(args.server_pack and args.shader_config and args.baseline_cache,'Full/finalize requires pack/config/historical cache')
 paths={'jarSha256':ROOT/'build/libs/destiny-guardians-0.1.0+26.3.jar','serverPackSha256':args.server_pack.resolve(),'shaderConfigSha256':args.shader_config.resolve()}
 artifact={k:sha(p) for k,p in paths.items()};old=read(QA/'baseline.json')['previousImplementation']
 require(all(old[k]==v for k,v in artifact.items()),'Fixture-only increment MUST keep exact W86 production JAR/pack/config')
 require(read(args.shader_config).get('dynamic-fov-shader',False)is False,'Expected unchanged headless FOV=false')
 checks=run_components(args.python)
 if not args.finalize:
  m=read(MANIFEST);require(m['sha256']==before['sha256'] and m['externalSha256']==before['externalSha256'],'Final source pins differ')
  require(all(m[k]==v for k,v in artifact.items()),'Final artifact pins differ')
 report=archive_verification(paths['jarSha256'],paths['serverPackSha256'],paths['shaderConfigSha256'],args.baseline_cache.resolve(),None,before)
 require(snapshot()==before,'Source changed during verification')
 require({k:sha(p)for k,p in paths.items()}==artifact,'Artifacts changed during verification')
 if args.finalize:
  gates=read(QA/'gate-summary.json');require(gates['jarSha256']==artifact['jarSha256'] and len(gates['finalPassingGates'])==2,'Final two passing gates must match pinned JAR')
  for n in gates['finalPassingGates']:
   text=(QA/f'gate-{n}.log').read_text();require('Some mod tried to create a chunk update packet'not in text,'Unresolved Polymer context warning in final gate')
  MANIFEST.parent.mkdir(parents=True,exist_ok=True)
  m=dict(stage='W87',baseline='W86',pinStatus='pinned',wholeGoalAchieved=False,pinnedVariant='headless',headlessDynamicFov=False,
   **artifact,sha256=before['sha256'],externalSha256=before['externalSha256'],preservation=before['preservation'],
   changedPreviousPins=before['changedPreviousPins'],addedPins=before['addedPins'],librarySourcePins=before['librarySourcePins'],
   nativeClientRenderingCertified=False,exactHistoricalAceFailureReproduced=False,componentVerifiers=checks,
   evidenceBoundary='Fixture login metadata and corrected paid-ray diagnostics; unchanged production. Original W86 Gate2 cause remains unknown; no native client certification.')
  MANIFEST.write_text(json.dumps(m,indent=2)+'\n')
 report.update(stage='W87',sourcePins=len(before['sha256']),previousPins=1550,sourceJarPackVerified=True,**artifact,
  preservation=before['preservation'],changedPreviousPins=before['changedPreviousPins'],addedPins=before['addedPins'],
  librarySourcePins=before['librarySourcePins'],componentVerifiers=checks,wholeGoalAchieved=False,nativeClientRenderingCertified=False,
  exactHistoricalAceFailureReproduced=False,evidenceBoundary='Source/JAR/pack and native-server tests are not native framebuffer/input/audio evidence.')
 if args.out:
  out=args.out.resolve();require(out.is_relative_to(QA.resolve()) and out.name not in ('baseline.json','w86-pack.zip'),'Report must be a new W87 QA output')
  require(str(out.relative_to(ROOT))not in before['sha256'],'Report cannot overwrite a pin');out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(stage='W87',sourcePins=len(before['sha256']),allClientAssets=len(report['allClientAssets']),serverResources=len(report['allServerResources']),mainClasses=len(report['classes']),**artifact,sourceJarPackVerified=True,nativeClientRenderingCertified=False)))
if __name__=='__main__':main()
