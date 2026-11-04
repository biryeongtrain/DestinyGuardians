#!/usr/bin/env python3
"""Read-only W103 candidate audit; never builds, launches, generates, or accepts native QA.

Default/--source-only validates source preservation and frozen research. --jar and
--pack inspect existing archived artifacts. --finalize additionally requires two
explicit serial full gates, complete registered new tests and both artifacts.
Reports go to stdout; callers own retaining them. A PASS is not native acceptance.
Common parsers are imported only after verifying the reviewed W102 auditor pin.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
QA = "docs/qa/2026-10-25/w103"
OLD_QA = "docs/qa/2026-10-25/w102"
OLD = "art/qa/w102/implementation.json"
OLD_SHA = "55e643f4b0d9548e615e4ae54ff9a0a01404fd019f94be9850a036ab3ed467ef"
COMMON = "scripts/qa/audit_named_audio_w102.py"
COMMON_SHA = "f05bfc4db1324639c1218cc7b5965fca97f05bf0043ac3939d60012ac3e4c4ff"
REF = "art/weapons/w103/references/"
CONTRACT = QA + "/integration.json"
RES = "src/main/resources/"
BASE = "src/main/java/kim/biryeong/destiny/weapon/"
PROFILE = RES + "destiny/weapons/w103-demolitionist.json"
REGISTRY = "src/gametest/resources/fabric.mod.json"
UNIT = "src/test/java/kim/biryeong/destiny/weapon/DemolitionistW103Test.java"
GT = "src/gametest/java/kim/biryeong/destiny/test/DemolitionistW103GameTests.java"
GT_CLASS = "kim.biryeong.destiny.test.DemolitionistW103GameTests"
UNIT_CLASS = "kim.biryeong.destiny.weapon.DemolitionistW103Test"
SELF = "scripts/qa/audit_demolitionist_w103.py"
ROOTS = ("src/main/java", "src/main/resources", "src/test/java", "src/test/resources", "src/gametest/java", "src/gametest/resources")
# Literal hashes of directly reviewed production, not a broad file-prefix allowance.
REVIEWED = {
 BASE+"WeaponRuntime.java": "c8ef97a7d4de1b6ba63b9dd56b4f05437f267295f1ef73dc6889754cef2bc4c1",
 BASE+"WeaponPerks.java": "9ae6f9e3a09b75e13e7c946628e89be86c9e1352ec637548a3b6b26b4864cfab",
 BASE+"WeaponPerkCommands.java": "a81b506adde0e37efc467bc865872cf94422b073cfb53c7e743df59d9526fb3c",
 BASE+"DemolitionistProfile.java": "0a71d0f67ce0786038f37ec0c2c661677680c7e53edf184b4eed6c2c50414860",
 BASE+"WeaponDemolitionist.java": "3d59da5906b70812bb9ec711545beef0737d13562228a9ce6fce03e9d0f6935a",
 "src/main/java/kim/biryeong/destiny/ability/hunter/HunterGrenade.java": "8e84224e90001511fef817c7dfd46eb4c97328b37cedc80d238d3f972892a11e",
}
FROZEN = {
 CONTRACT: "8e6407903f96d112ec7993a1beb950f2902001330c64972f43eae74eb8643cab",
 UNIT: "1207f0f13127e44327571029aa97bd446f130ba70aa9db4539f98223f869435a",
 GT: "781ec5f8b3c9e380863e2734ed07953e6d3b2e7918e18ee6d84ef1580a25796e",
 "scripts/extract_demolitionist_w103.py": "68a5b2c2edee41e3e8864c56118fc7d01402d98165b231f0fdd2be2ab4aa97d4",
 PROFILE: "b7aa18096002f5a9a66892027c6fb57295e3a09864ff52a1f889d6f732c10905",
 REF+"mechanics.json": "02278c0c6e53f44a3b43d2a6a3954890bb5e1a8498fcf2cafe058c4cb78fe6ae",
 REF+"socket-pools.json": "4aa26b3f7fc4baa7aec9a603f23a8c2de38d712a54273778429d60465e3a86ff",
 REF+"provenance.json": "8188bd3ce1c88abd5b27815ade884743eb36f961fd1b90bf15e9bfe8ecf85d41",
}
EXPECTED = {
 "austringer": (3055790362,4,785215120,10), "gnawing_hunger": (821154603,4,594510568,10),
 "bug_out_bag": (2744715540,4,575371383,10), "lonesome": (2199171672,4,167712635,10),
 "high_albedo": (1197486957,4,718633408,10), "whispering_slab": (211938782,4,967526625,10),
 "first_in_last_out": (3616586446,4,1439234589,20), "stormchaser": (3652506829,4,4213354588,10),
 "retraced_path": (548958835,4,398391969,10), "salvager_s_salvo": (2060863616,3,253,10),
 "nezarec_s_whisper": (254636484,3,210449465,20),
}

# Four independently disassembled classes changed only their LineNumberTable entries.
# Pin exact old/new bytes; no wildcard or arbitrary nested-class allowance.
METADATA_ONLY = {
 "kim/biryeong/destiny/ability/hunter/HunterGrenade$1.class": (
  "877bfecec04ffb01e96ec411db35b6b6211e56567c0d4903c4d9ec66e3c1cf42",
  "158fd11743ef14b33de59164be73daa82695f9511e5cbb8266398fa93e432c64",
  "723e01c9f588803d009f54c9ced8ca1a8bf0723740d6b437b8ef981439c98236"),
 "kim/biryeong/destiny/weapon/WeaponRuntime$GlaiveStatus.class": (
  "2dd9c819c789b0bd7949c6694e088c70fd82dc7bfc6ee74c8f2a50e9e25ae8bd",
  "ef821b3d6116f28b4d10dca0b65bf15b58a3c6ed8406ca65f172179e20f21d8a",
  "b8a6f4ff6e940b47b3a402fd0983f7fbdd4d47a5d397d87c333064d352cb3243"),
 "kim/biryeong/destiny/weapon/WeaponRuntime$SwordStatus.class": (
  "d1703a0d03c4d973a9806e02c8d0ff387be0e72b30849d7cf6e89a446c398d73",
  "7acfa722ff20aa71046e8dacbe9a80ac4b5861c611f5c50b68d320a192eb0546",
  "1baf544dc8d10c2258363f37ce5def74ab5a1071008ef42510a8f902a80e8d80"),
 "kim/biryeong/destiny/weapon/WeaponRuntime$HitDamage.class": (
  "4ff4ab599a90d5d25a06d223e34a514297a005a3879f134bb55c18123ad793d1",
  "f01f4a9f80fe3c82d03faa9d2b8792f2005dfcebd15a58eff94efd207f2a6a7f",
  "914a6893c6b302570db9de34fd207bf6ffc861f1f0a2ec9595474f8354518c39"),
}
JAR_REVIEW_EVIDENCE = {
 QA+"/jar-audit-attempt-1.log": "a2026d575ca62c33e6e0701c9d36704006267cabb649c31bb4f3ed400137a26f",
 QA+"/auditor-before-nested-review.py": "fb3955fdb68b4b999a00f0b9a0100d6f511e173a97b61dadbfbdf3b90e5dc0a0",
 QA+"/nested-bytecode-review.json": "367d4fb0fa62086be94a74ee26f309a4a198942154848980804a45d1dd472697",
}

def common():
    path=ROOT/COMMON
    if hashlib.sha256(path.read_bytes()).hexdigest()!=COMMON_SHA:
        raise RuntimeError("Reviewed common auditor changed")
    spec=importlib.util.spec_from_file_location("w103_frozen_common",path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module



def integration_contract(c, inp):
    contract=inp.json(CONTRACT)
    c.need(contract["stage"]=="W103" and contract["previous"]=="W102","Integration stage")
    c.need(contract["expectedJUnit"]==731 and contract["expectedGameTests"]==841,"Frozen integration totals")
    c.need(contract["newTestPins"]=={UNIT:FROZEN[UNIT],GT:FROZEN[GT]},"Exact reviewed test pins")
    for path,pin in contract["newTestPins"].items():
        c.need(inp.hash(path)==pin,"Test source changed: "+path)
    # These reviewed files use simple @Test and @GameTest methods, not parameterized/dynamic tests.
    unit_names=re.findall(r"^\s*@Test\s+(?:public\s+)?void\s+(\w+)\s*\(\s*\)",inp.data(UNIT).decode(),re.M)
    gt_names=re.findall(r"^\s*@GameTest\([^\n]*\)\s+public\s+void\s+(\w+)\s*\(GameTestHelper h\)",inp.data(GT).decode(),re.M)
    identities=[[UNIT_CLASS,name+"()"] for name in unit_names]
    c.need(len(unit_names)==len(set(unit_names))==6 and identities==contract["newJUnitIdentities"],"Literal source/JUnit method identities")
    c.need(len(gt_names)==len(set(gt_names))==10 and gt_names==contract["newGameTestMethods"],"Literal source/GameTest method identities")
    c.need(contract["nativeSequences"]==0 and contract["nativePNG"]==0 and
           all(contract[field] is False for field in ("nativeAudioAccepted","nativeRenderingAccepted","wholeGoalAchieved")),"Integration native/whole-goal boundaries")
    return contract


def source_audit(c, inp):
    need=c.need
    need(inp.hash(OLD)==OLD_SHA,"W102 manifest changed")
    old=inp.json(OLD)
    seal=OLD_QA+"/SHA256SUMS"
    need(inp.hash(seal)=="61b1448d3b540e08a6e59d0a5d6f591adecef41b9132650adc446f768c9402dc","W102 QA seal changed")
    lines=inp.data(seal).decode().splitlines(); need(len(lines)==410,"W102 seal inventory")
    for line in lines:
        m=re.fullmatch(r"([0-9a-f]{64})  (.+)",line); need(m is not None,"Malformed seal")
        need(inp.hash(OLD_QA+"/"+c.safe(m[2]))==m[1],"Changed sealed W102 evidence")
    for path,pin in {**REVIEWED,**FROZEN}.items():
        need(inp.hash(path)==pin,"Changed reviewed source: "+path)
    migrations=(set(REVIEWED)&set(old["sha256"]))|{REGISTRY}
    need(len(migrations)==5,"Unexpected existing source migration scope")
    for path,pin in old["sha256"].items():
        if path not in migrations: need(inp.hash(path)==pin,"Inherited source changed: "+path)
    before=inp.json(QA+"/before-shared.json")
    need(set(before)==migrations,"Before snapshot inventory")
    for path,pin in before.items():
        need(pin==old["sha256"][path] and inp.hash(QA+"/before/"+path)==pin,"Wrong before snapshot: "+path)
    original=inp.json(QA+"/before/"+REGISTRY); current=inp.json(REGISTRY)
    original_classes=original["entrypoints"]["fabric-gametest"]
    current_classes=current["entrypoints"]["fabric-gametest"]
    pending=[]
    if current_classes==original_classes: pending.append("registry")
    else:
        need(current_classes==original_classes+[GT_CLASS],"Non-additive or reordered GameTest registry")
        normalized=json.loads(json.dumps(current)); normalized["entrypoints"]["fabric-gametest"]=original_classes
        need(normalized==original,"Unrelated registry mutation")
    allowed_new={BASE+"DemolitionistProfile.java",BASE+"WeaponDemolitionist.java",PROFILE,UNIT,GT}
    files=set().union(*(inp.files(root) for root in ROOTS))
    old_files={p for p in old["sha256"] if any(p.startswith(root+"/") for root in ROOTS)}
    need(not old_files-files,"Removed source files")
    need(files-old_files<=allowed_new,"Unexpected new source files: "+repr(sorted(files-old_files-allowed_new)))
    for test in (UNIT,GT):
        if test not in files: pending.append(test)
    clients={p:inp.hash(p) for p in files if p.startswith(RES+"assets/")}
    need(clients==old["clientAssets"],"Client assets changed in server-only stage")
    provenance=inp.json(REF+"provenance.json")
    for pin in provenance["sourcePins"].values():
        need(inp.hash(pin["path"])==pin["sha256"],"Research source pin mismatch: "+pin["path"])
    need(provenance["generatorSha256"]==FROZEN[provenance["generator"]],"Extractor provenance pin")
    verify=inp.json(REF+"verification.json")
    need(verify["offlineVerify"]=="PASS" and verify["disjointReproduction"]=="BYTE_IDENTICAL","Missing source reproduction evidence")
    for row in verify["generated"]:
        need(inp.hash(row["path"])==row["sha256"] and row["sha256"]==FROZEN[row["path"]],"Extractor output mismatch")
    # Independently inspect official components, not only worker success strings.
    inventory=inp.json(provenance["sourcePins"]["inventory"]["path"])
    pools=inp.json(provenance["sourcePins"]["plugSets"]["path"])
    profile=inp.json(PROFILE); rows=profile["weapons"]
    need(len(rows)==11 and {r["id"] for r in rows}==set(EXPECTED),"Exact roster")
    for row in rows:
        ident=row["id"]; h,s,p,e=EXPECTED[ident]
        need((row["hash"],row["socket"],row["plugSetHash"],row["baseEnergyPercent"])==(h,s,p,e)
             and row["perkHash"]==3523296417,"Literal socket/energy oracle")
        item=inventory[str(h)]; sockets=item["sockets"]
        need(any(cat["socketCategoryHash"]==4241085061 and s in cat["socketIndexes"]
                 for cat in sockets["socketCategories"]),"Not actual weapon-trait socket")
        slot=sockets["socketEntries"][s]; pool=pools[str(p)]
        field="reusablePlugSetHash" if ident=="salvager_s_salvo" else "randomizedPlugSetHash"
        need(slot[field]==p,"Official pool identity")
        need(pool.get("isFakePlugSet",False)==(ident=="salvager_s_salvo"),"Official pool fake/curated classification")
        need(any(v["plugItemHash"]==3523296417 and v.get("currentlyCanRoll") is True
                 for v in pool["reusablePlugItems"]),"Base trait unavailable in exact socket")
        need(row["proofMode"]==("fixedCuratedOption" if ident=="salvager_s_salvo" else "randomized"),"Proof mode")
    mechanics=inp.json(REF+"mechanics.json")
    need(mechanics["unimplementedEnergyModifiers"]=={"abilityTierScalar":None,"grenadeStatScalar":None}
         and mechanics["reloadCooldownScope"]["proven"] is False,"Unknown modifier/scope misrepresented")
    integration_contract(c,inp)
    snapshot={p:inp.hash(p) for p in sorted(set(old["sha256"])|files|set(FROZEN)|{SELF})}
    return old,pending,snapshot,clients


def artifact_audit(c,inp,args,old):
    result={}
    if args.pack: c.need(args.jar is not None,"Pack requires JAR")
    if args.jar:
        previous_raw=inp.data(OLD_QA+"/product.jar")
        c.need(c.sha(previous_raw)==old["jarSha256"],"W102 JAR identity")
        raw=inp.data(args.jar); jar=c.archive(raw); previous=c.archive(previous_raw)
        delta=c.delta(c.hashes(previous),c.hashes(jar))
        stem="kim/biryeong/destiny/weapon/"
        additions={"destiny/weapons/w103-demolitionist.json"}
        additions|={stem+"DemolitionistProfile"+suffix+".class" for suffix in ("","$Perk","$Row","$Data")}
        additions|={stem+"WeaponDemolitionist"+suffix+".class" for suffix in ("","$ReloadLock","$Session","$Source","$Token","$GrenadeToken")}
        modified={stem+v+".class" for v in ("WeaponRuntime","WeaponRuntime$Shot","WeaponPerks","WeaponPerkCommands")}
        modified.add("kim/biryeong/destiny/ability/hunter/HunterGrenade.class")
        modified.update(METADATA_ONLY)
        c.need(len(additions)==11 and len(modified)==9,"Exact reviewed JAR migration cardinality")
        for path,pin in JAR_REVIEW_EVIDENCE.items():
            c.need(inp.hash(path)==pin,"Changed retained nested-class audit evidence: "+path)
        for path,(old_pin,new_pin,disassembly_pin) in METADATA_ONLY.items():
            c.need(c.sha(previous[path])==old_pin and c.sha(jar[path])==new_pin,"Reviewed metadata-only class bytes changed: "+path)
            name=path.rsplit("/",1)[-1][:-6]
            for phase in ("before","after"):
                c.need(inp.hash(QA+"/"+name+"-"+phase+"-javap.txt")==disassembly_pin,"Reviewed class disassembly changed: "+name)
        c.need(delta=={"added":sorted(additions),"removed":[],"modified":sorted(modified)},"Finite JAR delta: "+repr(delta))
        for path in inp.files("src/main/resources"):
            key=path[len(RES):]
            if key=="fabric.mod.json":
                source=inp.json(path); built=c.decode(jar[key])
                c.need(source["version"]=="${version}" and source["depends"]["fabricloader"]==">=${loader_version}"
                       and source["depends"]["minecraft"]=="${minecraft_version}","Known Fabric source template fields")
                source["version"]="0.1.0+26.3"
                source["depends"]["fabricloader"]=">=0.20.1"; source["depends"]["minecraft"]="26.3"
                c.need(source==built and jar[key]==previous[key],"Exact unchanged processed Fabric metadata")
            else: c.need(jar.get(key)==inp.data(path),"JAR/source resource mismatch: "+key)
        result.update(jarSha256=c.sha(raw),jarDelta=delta)
    if args.pack:
        before_raw=inp.data(OLD_QA+"/headless/resource_pack.zip")
        c.need(c.sha(before_raw)==old["serverPackSha256"],"W102 actual pack identity")
        raw=inp.data(args.pack); before=c.archive(before_raw); pack=c.archive(raw)
        delta=c.delta(c.hashes(before),c.hashes(pack))
        c.need(delta=={"added":[],"removed":[],"modified":[]},"Server-only stage changed pack entries: "+repr(delta))
        result.update(serverPackSha256=c.sha(raw),previousPackSha256=c.sha(before_raw),packEntries=len(pack),packEntryDelta=delta)
    return result


def gate_audit(c,inp,args,jar_sha):
    c.need(args.gates is not None and args.gates[0]>=1 and args.gates[1]==args.gates[0]+1,"Explicit consecutive full gates required")
    contract=integration_contract(c,inp)
    prior=c.junit(inp,OLD_QA+"/gate-3-xml")
    new_gt=len(re.findall(r"^\s*@GameTest\(",inp.data(GT).decode(),re.M))
    new_unit=len(re.findall(r"^\s*@Test\b",inp.data(UNIT).decode(),re.M))
    c.need(new_gt==10 and new_unit==6,"Reviewed new test annotations")
    expected_cases={tuple(v) for v in contract["newJUnitIdentities"]}
    prior_gt=int(re.findall(r"All (\d+) required tests passed",inp.data(OLD_QA+"/gate-3.log").decode())[0])
    c.need(len(prior)+new_unit==contract["expectedJUnit"] and prior_gt+new_gt==contract["expectedGameTests"],"Inherited plus new integration totals")
    result=[]
    for n in args.gates:
        prefix=QA+f"/gate-{n}"; row=inp.json(prefix+"-exit.json")
        c.need(row["returncode"]==0 and row["finishedAt"]>row["startedAt"],"Failed/incomplete gate")
        log=inp.data(prefix+".log").decode()
        c.need(re.findall(r"All (\d+) required tests passed",log)==[str(prior_gt+new_gt)]
               and re.findall(r"(\d+) GAME TESTS COMPLETE",log)==[str(prior_gt+new_gt)]
               and "BUILD SUCCESSFUL" in log and all(x not in log for x in ("BUILD FAILED","UP-TO-DATE","FROM-CACHE"))
               and re.search(r"(\d+) actionable tasks: \1 executed",log),"Not full forced fresh gate")
        cases=c.junit(inp,prefix+"-xml")
        c.need(prior<=cases and len(cases)==len(prior)+new_unit and cases-prior==expected_cases,"Inherited/new JUnit identities")
        names={Path(p).name for p in inp.files(prefix+"-xml") if p.endswith(".xml")}
        c.need(set(row["xmlFreshness"])==names and all(v is True for v in row["xmlFreshness"].values()),"XML freshness inventory")
        c.need(inp.data(prefix+"-jar.sha256").decode().strip().split()[0]==jar_sha,"Gate JAR pin")
        result.append({"gate":n,"junit":len(cases),"inheritedJUnit":len(prior),"gametests":prior_gt+new_gt,
                       "startedAt":row["startedAt"],"finishedAt":row["finishedAt"]})
    c.need(result[0]["finishedAt"]<=result[1]["startedAt"],"Gates are not serial independent runs")
    failures=[]
    for n in range(1,args.gates[-1]+1):
        prefix=QA+f"/gate-{n}"; row=inp.json(prefix+"-exit.json")
        if row["returncode"]!=0:
            failures.append({"gate":n,"returncode":row["returncode"],"exitSha256":inp.hash(prefix+"-exit.json"),"logSha256":inp.hash(prefix+".log")})
    return result,failures


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-only",action="store_true")
    parser.add_argument("--jar",type=Path); parser.add_argument("--pack",type=Path)
    parser.add_argument("--finalize",action="store_true")
    parser.add_argument("--gates",nargs=2,type=int)
    args=parser.parse_args()
    try:
        c=common(); inp=c.Inputs(); inp.hash(COMMON); inp.hash(SELF)
        c.need(not(args.source_only and (args.jar or args.pack or args.finalize)),"Source-only cannot accept artifacts/finalize")
        if args.finalize: c.need(args.jar and args.pack and args.gates,"Finalization requires JAR, actual pack and explicit gates")
        old,pending,snapshot,clients=source_audit(c,inp)
        contract=integration_contract(c,inp)
        artifacts=artifact_audit(c,inp,args,old)
        report={"stage":"W103","status":"SOURCE_PASS","candidateOnly":True,"finalized":False,
                "pending":pending,"expectedJUnit":contract["expectedJUnit"],"expectedGameTests":contract["expectedGameTests"],
                "newJUnitIdentities":contract["newJUnitIdentities"],"newGameTestMethods":contract["newGameTestMethods"],
                "sourcePins":len(snapshot),"clientAssetCount":len(clients),
                "acceptedOldChanges":sorted((set(REVIEWED)&set(old["sha256"]))|{REGISTRY}),
                "newSourcePaths":sorted(set(snapshot)-set(old["sha256"])),
                "sha256":snapshot,"clientAssets":clients,"previousManifestSha256":OLD_SHA,
                "nativeRenderingAccepted":False,"nativeAudioAccepted":False,"wholeGoalAchieved":False,
                "generatorExecutedByAuditor":False,"childAgentAvailable":False,**artifacts}
        if args.jar: report["status"]="JAR_PASS"
        if args.pack: report["status"]="PACK_PASS"
        if args.finalize:
            c.need(not pending,"Finalization requires complete new tests/registry")
            report["gates"],report["retainedPriorGateFailures"]=gate_audit(c,inp,args,report["jarSha256"])
            report.update(status="SEALED_CANDIDATE",finalized=True,finalPassingGates=args.gates)
        inp.recheck(); report["inputSha256"]=dict(sorted(inp.hashes.items()))
        print(json.dumps(report,indent=2,sort_keys=True)); return 0
    except Exception as error:
        print(json.dumps({"stage":"W103","status":"FAIL","reason":str(error)},sort_keys=True),file=sys.stderr); return 1

if __name__=="__main__":
    raise SystemExit(main())
