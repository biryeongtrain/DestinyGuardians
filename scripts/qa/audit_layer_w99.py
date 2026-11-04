#!/usr/bin/env python3
"""Finite W99 source/class/pack/cache boundary audit; renderer proof is separate."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import zipfile

ROOT=Path(__file__).resolve().parents[2]
QA=ROOT/"docs/qa/2026-10-25/w99"
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(value,why):
    if not value: raise RuntimeError(why)
def entries(p):
    with zipfile.ZipFile(p) as z:
        names=z.namelist();need(len(names)==len(set(names)),"Duplicate ZIP path")
        return {n:hashlib.sha256(z.read(n)).hexdigest() for n in names if not n.endswith("/")}
def delta(a,b): return dict(added=sorted(b.keys()-a.keys()),removed=sorted(a.keys()-b.keys()),modified=sorted(n for n in a.keys()&b.keys() if a[n]!=b[n]))
def verify_final_evidence(contract,caches,jar_hash):
    need(len(caches)==2 and len({p.resolve() for p in caches})==2,"Two distinct cache files required")
    need(not caches[0].samefile(caches[1]),"Two independent cache files required")
    summary=QA/"native-summary.json"
    need(sha(summary)==contract["nativeSummarySha256"],"Manual native summary drift")
    native=read(summary)
    need(native["reversibleProofSha256"]==sha(QA/"reversible-pixel-evidence.json"),"Reversible proof review drift")
    need(bool(native["manualPixelReview"]) and len(native["masterDirectRawVisualReview"])==12,"Missing bounded manual pixel review")
    for name,h in native["masterDirectRawVisualReview"].items():need(sha(QA/"final-native/frames"/(name+".png"))==h,"Reviewed PNG drift")
    profiles=native["profiles"]
    need([p["profile"] for p in profiles]==["default","small"],"Two intended profiles required")
    need({(ROOT/p["cache"]).resolve() for p in profiles}=={p.resolve() for p in caches},"Cache/profile binding mismatch")
    originals=[]
    for p,dims in zip(profiles,[(1708,960),(854,480)]):
        name=p["profile"];base=QA/"final-native"
        need(p["framebuffer"]==list(dims),"Profile dimensions mismatch")
        frames=list((base/"frames").glob(name+"-*.png"))
        need(len(frames)==p["pngCount"] and all(f.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") and struct.unpack(">II",f.read_bytes()[16:24])==dims for f in frames),"Actual framebuffer dimensions mismatch")
        provenance=base/(name+"-cache-provenance.json");need(sha(provenance)==p["provenanceSha256"],"Cache provenance drift")
        prov=read(provenance);originals.append(Path(prov["original"]).resolve())
        need(prov["original"]==p["originalCache"] and prov["sha256"]==p["cacheSha256"]==sha(ROOT/p["cache"]),"Cache origin/hash mismatch")
        for kind,key in [("readiness","readinessSha256"),("final-control","finalControlSha256")]:need(sha(base/(name+"-"+kind+".json"))==p[key],"Native state drift")
    need(len(set(originals))==2 and originals[0].parent!=originals[1].parent,"Independent profile download origins required")
    gates=read(QA/"gate-summary.json");rows=gates["gates"];last=rows[-2:]
    need(len(last)==2 and last[1]["gate"]==last[0]["gate"]+1,"Two latest consecutive gates required")
    need(gates["finalPassingGates"]==[r["gate"] for r in last] and gates["jarSha256"]==jar_hash,"Gate selection mismatch")
    for row in last:
        need(row["returncode"]==0 and row["forcedAllTasks"] and row["allXmlFresh"],"Gate execution/freshness failed")
        need(row["junit"]==dict(tests=contract["expectedJUnit"],failures=0,errors=0,skipped=0),"JUnit gate mismatch")
        need(row["previousJUnitIdentitiesPreserved"]==704 and row["newJUnit"]==0,"JUnit identities mismatch")
        need(row["requiredPassed"]==row["gameTestsTotal"]==contract["expectedGameTests"] and row["jarSha256"]==jar_hash,"GT/JAR gate mismatch")
    return native
def snapshot():
    contract=read(QA/"integration.json");oldpath=ROOT/"art/qa/w98/implementation.json"
    need(sha(oldpath)==contract["previousManifestSha256"],"Previous manifest drift")
    old=read(oldpath);current={p:sha(ROOT/p) for p in old["sha256"]}
    need(sorted(p for p in current if current[p]!=old["sha256"][p])==sorted(contract["acceptedOldChanges"]),"Unexpected inherited source change")
    for folder in ("src/main/java","src/main/resources","src/test/java","src/test/resources","src/gametest/java","src/gametest/resources"):
        live={p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob("*") if p.is_file()}
        expected={p for p in old["sha256"] if p.startswith(folder+"/")}
        need(live==expected,"Source path inventory changed "+folder)
    for p,h in contract["reviewedSourceSha256"].items():need(sha(ROOT/p)==h,"Reviewed source drift "+p);current[p]=h
    assets={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/"src/main/resources/assets").rglob("*") if p.is_file()}
    need(assets==old["clientAssets"],"Client asset changed")
    previous=read(QA/"before/src/gametest/resources/fabric.mod.json")["entrypoints"]["fabric-gametest"]
    now=read(ROOT/"src/gametest/resources/fabric.mod.json")["entrypoints"]["fabric-gametest"]
    need(now==previous+["kim.biryeong.destiny.test.CriticalHudLayerW97GameTests"],"GT registration scope changed")
    protected=read(ROOT/"docs/qa/2026-10-25/w98/baseline.json")
    need(all(sha(p)==h for p,h in protected["protected"].items()),"Protected Vision source drift")
    need(all(sha(ROOT/p["path"])==p["sha256"] for p in protected["normalQAPlayers"]),"Normal QA player drift")
    need(all(sha(p)==h for p,h in old["externalSha256"].items()),"External source drift")
    return dict(sha256=current,clientAssets=assets,externalSha256=old["externalSha256"])
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--pack",type=Path);ap.add_argument("--client-cache",type=Path,action="append",default=[]);ap.add_argument("--out",type=Path,required=True);ap.add_argument("--finalize",action="store_true");args=ap.parse_args()
    before=snapshot();contract=read(QA/"integration.json");jar=ROOT/"build/libs/destiny-guardians-0.1.0+26.3.jar";prior=QA/"before-product.jar"
    artifacts=[jar,prior,QA/"integration.json"]+([args.pack]+args.client_cache if args.pack else [])
    artifact_hashes={str(p):sha(p) for p in artifacts}
    need(sha(prior)==contract["previousJarSha256"],"Previous archived JAR drift")
    difference=delta(entries(prior),entries(jar));need(difference==dict(added=[],removed=[],modified=["kim/biryeong/destiny/hud/IncomingDamageHud.class"]),"Unexpected product JAR delta "+str(difference))
    need(not any(n.startswith("qa/w99/") or "w99-probe" in n for n in entries(jar)),"Probe leaked into product")
    report=dict(stage="W99",sourcePins=len(before["sha256"]),clientAssets=len(before["clientAssets"]),jarSha256=sha(jar),jarDelta=difference,wholeGoalAchieved=False,nativeAudioAccepted=False)
    if args.pack:
        data=entries(args.pack);oldpack=ROOT/"docs/qa/2026-10-25/w98/server-generated/resource_pack.zip"
        need(sha(oldpack)==read(ROOT/"art/qa/w98/implementation.json")["serverPackSha256"],"W98 reference pack drift")
        artifacts.append(oldpack);artifact_hashes[str(oldpack)]=sha(oldpack)
        need(data==entries(oldpack),"Final pack assets differ from W98 full pack")
        need(len(data)==12171,"Unexpected pack entry count")
        for cache in args.client_cache:need(sha(cache)==sha(args.pack),"Actual client cache differs from server ZIP")
        report.update(packEntries=len(data),packSha256=sha(args.pack),packEntryDelta=dict(added=[],removed=[],modified=[]),clientCaches={str(p):sha(p) for p in args.client_cache})
    need(snapshot()==before,"Inputs changed during audit")
    if args.finalize:
        need(args.pack is not None,"Server pack required")
        native=verify_final_evidence(contract,args.client_cache,sha(jar))
        report["manualNativeSummarySha256"]=sha(QA/"native-summary.json")
    need(all(sha(p)==artifact_hashes[str(p)] for p in artifacts),"Artifacts changed during audit")
    if args.finalize:
        target=ROOT/"art/qa/w99/implementation.json";target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(dict(stage="W99",baseline="W98",acceptance="minimal critical layer0 after reversible native proof; final rendering evidence separate",wholeGoalAchieved=False,jarSha256=sha(jar),serverPackSha256=sha(args.pack),**before),indent=2)+"\n")
    args.out.write_text(json.dumps(report,indent=2)+"\n");print(json.dumps(report))
if __name__=="__main__":main()
