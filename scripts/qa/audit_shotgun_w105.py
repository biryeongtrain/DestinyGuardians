#!/usr/bin/env python3
"""Finite read-only W105 audit: no build, generator, process launch, client or CU.

Default/--source-only checks the independently reviewed freeze. --jar and
--pack inspect existing archives. --finalize requires two explicit consecutive
archived gates and both archives. JSON goes to stdout; master owns manifest/seal.
Counts and pins below are from the closed 750 JUnit / 865 GT freeze, not guesses.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[2]
QA="docs/qa/2026-10-25/w105"
OLD_QA="docs/qa/2026-10-25/w104"
OLD="art/qa/w104/implementation.json"
OLD_SHA="3462cc5507af11de73ef8031492949a5d2a755ead840ff09c94cea222269bcb5"
SEAL="run/private-sources/w105/sealed-before.json"
SEAL_SHA="4b2b2588be90aa47a7a099eaa2455c28eb0f3cf4f26b3f12e69bdcb9d860875f"
COMMON="scripts/qa/audit_named_audio_w102.py"
COMMON_SHA="f05bfc4db1324639c1218cc7b5965fca97f05bf0043ac3939d60012ac3e4c4ff"
SELF="scripts/qa/audit_shotgun_w105.py"
BASE="src/main/java/kim/biryeong/destiny/weapon/"
RES="src/main/resources/"
REGISTRY="src/gametest/resources/fabric.mod.json"
UNIT="src/test/java/kim/biryeong/destiny/weapon/ShotgunPatternW105Test.java"
GT="src/gametest/java/kim/biryeong/destiny/test/ShotgunPatternW105GameTests.java"
UNIT_CLASS="kim.biryeong.destiny.weapon.ShotgunPatternW105Test"
GT_CLASS="kim.biryeong.destiny.test.ShotgunPatternW105GameTests"
PROFILE=RES+"destiny/weapons/w105-shotgun-patterns.json"
CONTRACT=QA+"/integration.json"
FRAMES=("aggressive","precision","lightweight","rapid_fire")
ASSETS={RES+"assets/destiny/"+folder+"/reticle_w105_shotgun_"+frame+ext
        for frame in FRAMES for folder,ext in (("items/gui/hud",".json"),("models/gui/hud",".json"),("textures/item/hud",".png"))}
MIGRATIONS={BASE+"WeaponRuntime.java",BASE+"WeaponProfile.java",
 "src/main/java/kim/biryeong/destiny/hud/WeaponReticleHud.java",
 "src/test/java/kim/biryeong/destiny/weapon/WeaponCombatTest.java",
 "src/gametest/java/kim/biryeong/destiny/test/WeaponReticleW44GameTests.java",
 "src/test/java/kim/biryeong/destiny/sound/FireVariantsW98Test.java",REGISTRY}
NEW={BASE+"ShotgunSpread.java",BASE+"ShotgunPatternProfile.java",PROFILE,UNIT,GT}|ASSETS
ROOTS=("src/main/java","src/main/resources","src/test/java","src/test/resources","src/gametest/java","src/gametest/resources")
JAR_SHA="9b35e07e5b3e18b4c144341339f05d5d9f9c470b660de146d44df6b3feef53da"
PACK_SHA="24e97b07f720b8c58ab2679a58c9ca14acef136812acfbd1144ffab687ff455d"
ROWS=[("mindbender_s_ambition_adept",912150785,"aggressive",3983457027,"fixed_evenly_distributed_cone"),
 ("dust_rock_blues",636912560,"precision",1636108362,"vertical_oval"),
 ("first_in_last_out",3616586446,"pinpoint_slug",918679156,"single_slug"),
 ("parcel_of_stardust_fell_to_earth",2217366863,"lightweight",1458010786,"diamond"),
 ("ikelos_sg_v1_0_1",1887808042,"rapid_fire",996573084,"square")]
UNKNOWN={"currentPelletCount","currentPatternUnchangedSinceS19","genericAdsShrinksPelletSpread","genericAdsSpreadMultiplier",
 "pelletCoordinates","baseSpreadAngleDegrees","patternAspectRatios","sourceDamagePerPellet","sourceDamageScalars"}


def common():
    if hashlib.sha256((ROOT/COMMON).read_bytes()).hexdigest()!=COMMON_SHA:
        raise RuntimeError("Frozen common parsers changed")
    spec=importlib.util.spec_from_file_location("w105_frozen_common",ROOT/COMMON)
    c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
    return c


def profile_rules(c, d):
    c.need(d["stage"]=="W105" and d["schemaVersion"]==1 and d["patternScope"]=="historical_S19_2022_12_01_qualitative_only","Historical profile scope")
    c.need(len(d["weapons"])==5,"Exact five shotgun rows")
    for r,(ident,h,frame,intrinsic,pattern) in zip(d["weapons"],ROWS):
        slug=frame=="pinpoint_slug"
        c.need((r["id"],r["hash"],r["frame"],r["intrinsicHash"],r["socket"],r["pattern"])==(ident,h,frame,intrinsic,0,pattern),"Exact official row "+ident)
        c.need(r["singleSlugRound"] is slug and r["pelletCount"]==(None if slug else 12) and r["slugProjectileCount"]==(1 if slug else None),"Slug/pellet count separation")
        c.need(r["pelletCountScope"]==("not_applicable_single_slug" if slug else "historical_2021_text_and_2022_S19_illustrations"),"Count temporal scope")
    c.need(set(d["sourceRules"])==UNKNOWN and all(v is None for v in d["sourceRules"].values()),"Exact unknown source rules must stay null")
    local=d["localPolicy"]
    c.need(local["preserveExistingTotalHpBudget"] is True and local["retainExistingGenericAdsFactor"] is True and local["assumeFullChokeEquipped"] is False,"Local tuning/equipped barrel boundary")


def source_audit(c,inp):
    need=c.need
    need(inp.hash(OLD)==OLD_SHA,"W104 manifest changed");old=inp.json(OLD)
    need(len(old["sha256"])==old["sourcePins"]==8774 and len(old["clientAssets"])==7207,"Prior inventory")
    need(inp.hash(SEAL)==SEAL_SHA,"W104 before-seal changed")
    seal=inp.json(SEAL)
    need(len(seal)==314 and set(seal)==inp.files(OLD_QA)|{OLD},"Exact sealed W104 file inventory")
    for p,h in seal.items():need(inp.hash(p)==h,"Sealed W104 evidence changed: "+p)
    for p,h in REVIEWED.items():need(inp.hash(p)==h,"Reviewed freeze changed: "+p)
    for p,h in old["sha256"].items():
        if p not in MIGRATIONS:need(inp.hash(p)==h,"Unrelated inherited input changed: "+p)
    need(len(MIGRATIONS)==7 and all(inp.hash(p)!=old["sha256"][p] for p in MIGRATIONS),"Exact seven migrations")
    before=inp.json(QA+"/before-shared.json")
    need(set(before)==MIGRATIONS,"Exact before snapshot inventory")
    for p,h in before.items():need(h==old["sha256"][p] and inp.hash(QA+"/before/"+p)==h,"Before snapshot drift: "+p)
    original=inp.json(QA+"/before/"+REGISTRY);current=inp.json(REGISTRY)
    classes=original["entrypoints"]["fabric-gametest"]
    need(current["entrypoints"]["fabric-gametest"]==classes+[GT_CLASS],"Exact GameTest registry append")
    current["entrypoints"]["fabric-gametest"]=classes;need(current==original,"Unrelated registry change")
    old_gt=set();new_gt=set()
    for cls in classes+[GT_CLASS]:
        path="src/gametest/java/"+cls.replace(".","/")+".java"
        text=inp.data(path).decode()
        pattern=r"@GameTest\([^\n]*\)\s+public\s+void\s+(\w+)\s*\("
        new_gt.update((cls,n) for n in re.findall(pattern,text))
        if cls in classes:
            prior=inp.data(QA+"/before/"+path).decode() if path in MIGRATIONS else text
            old_gt.update((cls,n) for n in re.findall(pattern,prior))
    need(old_gt<=new_gt and new_gt-old_gt=={(GT_CLASS,n) for n in inp.json(CONTRACT)["newGameTestMethods"]},"Inherited registered GameTest source identities changed")

    files=set().union(*(inp.files(r) for r in ROOTS))
    inherited={p for p in old["sha256"] if any(p.startswith(r+"/") for r in ROOTS)}
    need(inherited<=files and files-inherited==NEW and len(NEW)==17,"Exact seventeen source additions/no removals")
    clients={p:inp.hash(p) for p in files if p.startswith(RES+"assets/")}
    need(clients==old["clientAssets"]|{p:REVIEWED[p] for p in ASSETS},"Exactly twelve client additions and unchanged inherited assets")
    contract=inp.json(CONTRACT)
    need(contract["stage"]=="W105" and contract["previous"]=="W104" and (contract["expectedJUnit"],contract["expectedGameTests"])==(750,865),"Closed test freeze")
    need(contract["newTestPins"]=={p:REVIEWED[p] for p in (UNIT,GT)},"Exact test pins")
    names=re.findall(r"^\s*@Test\s+(?:public\s+)?void\s+(\w+)\s*\(\s*\)",inp.data(UNIT).decode(),re.M)
    methods=re.findall(r"^\s*@GameTest\([^\n]*\)\s+public\s+void\s+(\w+)\s*\(GameTestHelper h\)",inp.data(GT).decode(),re.M)
    need(len(names)==len(set(names))==6 and [[UNIT_CLASS,n+"()"] for n in names]==contract["newJUnitIdentities"],"Exact six JUnit identities")
    need(len(methods)==len(set(methods))==13 and methods==contract["newGameTestMethods"],"Exact thirteen GameTest identities")
    need(all(contract[k] is False for k in ("nativeRenderingAccepted","nativeAudioAccepted","wholeGoalAchieved")),"Automatic candidate acceptance boundary")
    profile_rules(c,inp.json(PROFILE))
    provenance=inp.json("art/weapons/w105/references/provenance.json")
    for pin in provenance["sourcePins"].values():need(inp.hash(pin["path"])==pin["sha256"],"Official/private source bytes drift: "+pin["path"])
    need(inp.hash(provenance["generator"])==provenance["generatorSha256"],"Extractor provenance")
    evidence=inp.json("art/weapons/w105/references/evidence.json")
    need(set(evidence["unknownSourceRules"])==UNKNOWN and all(v is None for v in evidence["unknownSourceRules"].values()),"Evidence null boundary")
    inventory=inp.json(provenance["sourcePins"]["inventory"]["path"])
    for ident,h,frame,intrinsic,pattern in ROWS:
        sockets=inventory[str(h)]["sockets"]
        need(inventory[str(h)]["itemSubType"]==7 and sockets["socketEntries"][0]["singleInitialItemHash"]==intrinsic,"Official shotgun intrinsic identity: "+ident)
        need(any(cat["socketCategoryHash"]==3956125808 and 0 in cat["socketIndexes"] for cat in sockets["socketCategories"]),"Intrinsic socket category")
    art=inp.json("art/hud/w105-shotgun/manifest.json")
    need(set(art["frames"])==set(FRAMES) and art["renderer"]["version"]=="12.3.0" and art["provenance"]["unchanged2026BehaviorProven"] is False,"Historical art/provenance boundary")
    for frame,row in art["frames"].items():
        name="reticle_w105_shotgun_"+frame
        need(set(row["paths"].values())=={p for p in ASSETS if name in p},"Exact art output paths")
        item=inp.json(row["paths"]["item"]);model=inp.json(row["paths"]["model"])
        need(item["model"]["type"]=="minecraft:model" and item["model"]["model"]=="destiny:gui/hud/"+name,"Item model resolution")
        need(model["textures"]=={"0":"destiny:item/hud/"+name} and len(model["elements"])==1 and model["elements"][0]["from"][2]==model["elements"][0]["to"][2],"Transparent flat quad model")
        raw=inp.data(row["paths"]["texture"])
        need(raw[:8]==b"\x89PNG\r\n\x1a\n" and int.from_bytes(raw[16:20],"big")==128 and int.from_bytes(raw[20:24],"big")==128 and raw[25]==6,"128px RGBA texture")
    snapshot={p:inp.hash(p) for p in sorted(set(old["sha256"])|files|set(REVIEWED)|{SELF})}
    return old,contract,snapshot,clients


def normalized_verbose(raw):
    return "\n".join(line for line in raw.decode().splitlines() if not re.match(r"^(Classfile |  Last modified |  SHA-256 checksum )",line) and not re.fullmatch(r"\s*line [0-9]+: [0-9]+",line))+"\n"


def artifacts(c,inp,args,old):
    result={}
    if args.pack:c.need(args.jar is not None,"Pack requires product JAR")
    if args.jar:
        before=c.archive(inp.data(OLD_QA+"/product.jar"));raw=inp.data(args.jar);after=c.archive(raw)
        c.need(inp.hash(OLD_QA+"/product.jar")==old["jarSha256"] and c.sha(raw)==JAR_SHA,"Exact old/new JAR SHA")
        a=c.hashes(before);b=c.hashes(after);delta=c.delta(a,b)
        pins={"added":{p:b[p] for p in delta["added"]},"modified":{p:{"before":a[p],"after":b[p]} for p in delta["modified"]},"removed":delta["removed"]}
        c.need(pins==JAR_DELTA_PINS,"Exact reviewed JAR member delta")
        c.need(len(pins["added"])==19 and len(pins["modified"])==8 and not pins["removed"],"JAR addition/modification/removal inventory")
        c.need(inp.hash(QA+"/nested-bytecode-review.json")==NESTED_SHA,"Nested metadata review drift")
        nested=inp.json(QA+"/nested-bytecode-review.json")
        expected={"kim/biryeong/destiny/weapon/WeaponRuntime$"+n+".class" for n in ("FlightSnapshot","GlaiveStatus","HitDamage","SwordStatus")}
        c.need(set(nested["classes"])==expected and nested["status"]=="FULL_VERBOSE_LINE_NUMBER_ONLY","Exact four metadata classes")
        for p,row in nested["classes"].items():
            c.need((a[p],b[p])==(row["before"]["classSha256"],row["after"]["classSha256"]),"Nested raw class pins")
            texts=[]
            for phase in ("before","after"):
                r=row[phase];t=inp.data(r["javapPath"])
                c.need(c.sha(t)==r["javapSha256"] and ("SHA-256 checksum "+r["classSha256"]) in t.decode(),"Verbose text/raw class binding")
                texts.append(normalized_verbose(t))
            c.need(texts[0]==texts[1],"Not proven LineNumberTable-only: "+p)
            row["independentNormalizedVerboseSha256"]=c.sha(texts[0].encode())
            row["masterNormalizationHashMatched"]=row["independentNormalizedVerboseSha256"]==row["normalizedVerboseSha256"]
        for p in inp.files("src/main/resources"):
            member=p[len(RES):]
            c.need(after.get(member)==(before[member] if member=="fabric.mod.json" else inp.data(p)),"Packaged resource/source mismatch: "+member)
        result.update(jarSha256=JAR_SHA,jarDelta=delta,jarDeltaPins=pins,metadataOnlyClassPins=nested["classes"])
    if args.pack:
        prior=inp.data(OLD_QA+"/headless/resource_pack.zip");raw=inp.data(args.pack)
        c.need(c.sha(prior)==old["serverPackSha256"] and c.sha(raw)==PACK_SHA,"Exact actual pack pins")
        a=c.hashes(c.archive(prior));pack=c.archive(raw);b=c.hashes(pack);d=c.delta(a,b)
        expected=sorted(p[len(RES):] for p in ASSETS)
        c.need(d=={"added":expected,"modified":[],"removed":[]},"Actual pack must preserve every inherited member with only twelve additions")
        for p in ASSETS:c.need(pack[p[len(RES):]]==inp.data(p),"Actual pack/source asset mismatch")
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            counts={"files":sum(not i.is_dir() for i in z.infolist()),"directories":sum(i.is_dir() for i in z.infolist()),"total":len(z.infolist())}
        c.need(counts=={"files":12371,"directories":178,"total":12549},"Actual ZIP file/directory counts")
        provenance=inp.json(QA+"/headless/pack-provenance.json");prep=inp.json(QA+"/headless/preparation.json")
        c.need(provenance["sha256"]==PACK_SHA and provenance["postEditedPack"] is False and provenance["nativeClientLaunched"] is False,"Actual source/classes pack provenance")
        c.need(prep["shaderfxSha256"]==inp.hash(OLD_QA+"/headless/shaderfx.json")==inp.hash(QA+"/headless/shaderfx.json"),"Same W104 shader config")
        cleanup=inp.json(QA+"/headless/cleanup.json")
        c.need(all(cleanup[k] is True for k in ("done","packCreated","serverStopped","playersZero","forceloadEmptyAllDimensions","advanceTimeTrue","spawnMobsTrue","relayRemoved")) and cleanup["wrapperExit"]==0 and cleanup["probeMods"]==[],"Isolated actual pack clean stop")
        log=inp.data(QA+"/headless/server.log").decode()
        c.need("Done (" in log and "Stopping server" in log,"Actual pack server log incomplete")
        result.update(serverPackSha256=PACK_SHA,previousPackSha256=c.sha(prior),packEntries=len(pack),packArchiveCounts=counts,packEntryDelta=d)
    return result


def gate_audit(c,inp,args,contract):
    c.need(args.gates and args.gates[0]>=1 and args.gates[1]==args.gates[0]+1,"Two explicit consecutive gates")
    prior=c.junit(inp,OLD_QA+"/gate-2-xml");new={tuple(v) for v in contract["newJUnitIdentities"]}
    c.need(len(prior)==744 and len(new)==6 and not prior&new,"Old/new JUnit identities")
    summary=inp.json(QA+"/gate-summary.json")
    c.need(summary["finalPassingGates"]==args.gates and summary["jarSha256"]==JAR_SHA and (summary["previousJUnit"],summary["newJUnit"],summary["previousGameTests"],summary["newGameTests"])==(744,6,852,13),"Gate summary freeze")
    results=[]
    for n in args.gates:
        prefix=QA+f"/gate-{n}";row=inp.json(prefix+"-exit.json");log=inp.data(prefix+".log").decode()
        c.need(row["gate"]==n and row["returncode"]==0 and row["finishedAt"]>row["startedAt"],"Gate failed/incomplete")
        c.need(re.findall(r"All (\d+) required tests passed",log)==["865"] and re.findall(r"(\d+) GAME TESTS COMPLETE",log)==["865"] and "BUILD SUCCESSFUL" in log and all(v not in log for v in ("BUILD FAILED","UP-TO-DATE","FROM-CACHE")) and re.search(r"20 actionable tasks: 20 executed",log),"Not complete forced 865-GT gate")
        cases=c.junit(inp,prefix+"-xml");c.need(cases==prior|new and len(cases)==750,"Exact 744 inherited + six new passing JUnit identities")
        xmls={Path(p).name for p in inp.files(prefix+"-xml") if p.endswith(".xml")}
        c.need(set(row["xmlFreshness"])==xmls and all(v is True for v in row["xmlFreshness"].values()),"Complete fresh XML inventory")
        c.need(inp.data(prefix+"-jar.sha256").decode().strip()==JAR_SHA,"Gate/product JAR mismatch")
        listed=[r for r in summary["gates"] if r["gate"]==n];c.need(len(listed)==1,"Summary duplicate/missing gate")
        s=listed[0]
        c.need(s["returncode"]==0 and s["junit"]=={"tests":750,"failures":0,"errors":0,"skipped":0} and s["previousJUnitIdentitiesPreserved"]==744 and s["newJUnit"]==6 and s["requiredPassed"]==s["gameTestsTotal"]==865 and s["forcedAllTasks"] is True and s["allXmlFresh"] is True and s["jarSha256"]==JAR_SHA,"Summary/raw gate disagreement")
        results.append({"gate":n,"junit":750,"inheritedJUnit":744,"gametests":865,"inheritedGameTests":852,"startedAt":row["startedAt"],"finishedAt":row["finishedAt"]})
    c.need(results[0]["finishedAt"]<=results[1]["startedAt"],"Gates must be serial")
    failures=[]
    for n in range(1,args.gates[-1]+1):
        prefix=QA+f"/gate-{n}";row=inp.json(prefix+"-exit.json")
        if row["returncode"]!=0:
            paths={p:inp.hash(p) for p in inp.files(prefix+"-xml") if p.endswith(".xml")}
            failures.append({"gate":n,"returncode":row["returncode"],"exitSha256":inp.hash(prefix+"-exit.json"),"logSha256":inp.hash(prefix+".log"),"xmlSha256":paths})
    return results,failures


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--source-only",action="store_true")
    p.add_argument("--jar",type=Path);p.add_argument("--pack",type=Path);p.add_argument("--finalize",action="store_true");p.add_argument("--gates",nargs=2,type=int)
    args=p.parse_args()
    try:
        c=common();inp=c.Inputs();inp.hash(COMMON);inp.hash(SELF)
        c.need(not(args.source_only and (args.jar or args.pack or args.finalize or args.gates)),"Source-only cannot accept artifacts")
        if args.finalize:c.need(args.jar and args.pack and args.gates,"Finalize requires actual artifacts and explicit gates")
        c.need(not args.gates or args.finalize,"Gates require finalize")
        old,contract,snapshot,clients=source_audit(c,inp)
        report={"stage":"W105","status":"SOURCE_PASS","candidateOnly":True,"finalized":False,"pending":[],"sourcePins":len(snapshot),"sha256":snapshot,"clientAssetCount":len(clients),"clientAssets":clients,"previousManifestSha256":OLD_SHA,"acceptedOldChanges":sorted(MIGRATIONS),"newSourcePaths":sorted(set(snapshot)-set(old["sha256"])),"expectedJUnit":750,"expectedGameTests":865,"newJUnitIdentities":contract["newJUnitIdentities"],"newGameTestMethods":contract["newGameTestMethods"],"nativeRenderingAccepted":False,"nativeAudioAccepted":False,"wholeGoalAchieved":False,"generatorExecutedByAuditor":False,"childAgentWorkClaimed":False}
        report.update(artifacts(c,inp,args,old))
        if args.jar:report["status"]="JAR_PASS"
        if args.pack:report["status"]="PACK_PASS"
        if args.finalize:
            report["gates"],report["retainedPriorGateFailures"]=gate_audit(c,inp,args,contract)
            report.update(status="SEALED_CANDIDATE",finalized=True,finalPassingGates=args.gates)
        inp.recheck();report["inputSha256"]=dict(sorted(inp.hashes.items()))
        print(json.dumps(report,indent=2,sort_keys=True));return 0
    except Exception as error:
        print(json.dumps({"stage":"W105","status":"FAIL","reason":str(error)},sort_keys=True),file=sys.stderr);return 1


REVIEWED = {'art/hud/w105-shotgun/contact-sheet.png': '2d173ffe67c014e594ac9a94e196260fa9194f3cfd51c2f3cc6474578454e8ab', 'art/hud/w105-shotgun/manifest.json': '31128043dad59113862c00ad4b4073cd960acd7e77675d2d05f8f1a316321a33', 'art/weapons/w105/references/CONTRACT.md': '91701d08312510114d8fdff3ecafb0982c135c2e28991fe42623a95b4b15c55a', 'art/weapons/w105/references/REPORT.md': '291be9dbf5094184b6c8a4b2a4377c5a449e30bb19a262d770303c712b04cc56', 'art/weapons/w105/references/evidence.json': '5c638e685dd401690e05e153c5a1be18170c9a9ff0c6fba2b0fff0ba0a862cd9', 'art/weapons/w105/references/provenance.json': '2be00d6c3d54250b07181ceb42422c975a261d084b48d1159353a47a49828f79', 'art/weapons/w105/references/roster-proof.json': 'c25dd7010ac8c7f47ac339a8f419c4c3a93c96754c043b247e399fb0404dc635', 'art/weapons/w105/references/verification.json': 'bcc4d2ea392f9f0445d7b3c34a6092ca2acf1ba013eaa8998ff7f35883bd6e14', 'docs/qa/2026-10-25/w105/integration.json': '8c8d9229fa17b5caddd2f1e444cc3fcc3307d9ca30da3b76996771178444cd57', 'scripts/extract_shotgun_patterns_w105.py': '86d82236da34ae6584df5a3924aa727f229f45c983706344147b657785c47e7b', 'scripts/generate_shotgun_reticles_w105.py': '658789a8569d2f24f97cefea14a2e489c8223af6ef6fea90a4ef5c12a4221480', 'scripts/qa/run_gate_w105.py': '2b0eba99b7103cf2e83062fbb8fef726508b83b63a3bc433fadd77fb3e487d87', 'scripts/qa/summarize_w105_gates.py': 'a7687597faf2b2a310299061aef641780abdc24905dce403d23993b8671a8789', 'src/gametest/java/kim/biryeong/destiny/test/ShotgunPatternW105GameTests.java': 'a19bab53f8291e2ffc710ca9961ba7632e4070eaf5e6198c85179d76472eb6fa', 'src/gametest/java/kim/biryeong/destiny/test/WeaponReticleW44GameTests.java': '13dbe8df59be2e2280bad615d8ff304d3283cc2457528d04d77766df0221fef7', 'src/gametest/resources/fabric.mod.json': '670f0ee75b7e2de8e5f005ddc71b55f49f7b738abaafc675d5edf44b70968a7b', 'src/main/java/kim/biryeong/destiny/hud/WeaponReticleHud.java': '8fb885fd37c9e532176e24cb486883811977ccdb526e1c8b683b7772ceb49e80', 'src/main/java/kim/biryeong/destiny/weapon/ShotgunPatternProfile.java': 'a647b777724064dc2e2cf7cae7eae947896505ce6fa64da6d751a161734cfdf7', 'src/main/java/kim/biryeong/destiny/weapon/ShotgunSpread.java': '240473eac17aad0ad0d456ac6ab7a913742558ad0a57039298436cc5f4561522', 'src/main/java/kim/biryeong/destiny/weapon/WeaponProfile.java': 'b16a84f9d93d4537d4be8dbdded2d7a49b766fe169c2a27da7b515531f618ce4', 'src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java': '46f515ec2f387c9da3f4b57807041da0e7c2a511a2066db06b05fc98383d06ae', 'src/main/resources/assets/destiny/items/gui/hud/reticle_w105_shotgun_aggressive.json': 'eba35c538b1449ce7960838ae1f6aff6a4e37c8f611b33e4342bbac4b68bc0e1', 'src/main/resources/assets/destiny/items/gui/hud/reticle_w105_shotgun_lightweight.json': 'd1400b703a50e1a71ab22406b10a63477e4acf5924d139c146be44dbdd055b19', 'src/main/resources/assets/destiny/items/gui/hud/reticle_w105_shotgun_precision.json': 'd0ba22dc12bfd38689976313ef9a452e3a068bd09fad8fd8575605b264139d42', 'src/main/resources/assets/destiny/items/gui/hud/reticle_w105_shotgun_rapid_fire.json': '5aa301dbac73da49b8f4a83990c99ade4f65c6b632c6539d87f0d10ccc827f26', 'src/main/resources/assets/destiny/models/gui/hud/reticle_w105_shotgun_aggressive.json': 'd992dc0a1e7dbff11f04490d2a9f08655b95cd71014642e4717e3fef1deabcfa', 'src/main/resources/assets/destiny/models/gui/hud/reticle_w105_shotgun_lightweight.json': '76cbd547427cd8fa04937cfe168801b5d4cb22ca8f03953e660f0781410ff112', 'src/main/resources/assets/destiny/models/gui/hud/reticle_w105_shotgun_precision.json': 'f50072e018eba943cc1745fced50dd2ff31f215dd915dd0720252ecd5b17cef7', 'src/main/resources/assets/destiny/models/gui/hud/reticle_w105_shotgun_rapid_fire.json': 'e4564965d5561ae155479c56900e1e602e01dffd5309237a55cc82e1d4eb0932', 'src/main/resources/assets/destiny/textures/item/hud/reticle_w105_shotgun_aggressive.png': '1a002f3865add5e553010ddbff90b8dc4e3421c8520a8320dd16ac69f7187abe', 'src/main/resources/assets/destiny/textures/item/hud/reticle_w105_shotgun_lightweight.png': 'c6837d225c9cb309c69bbe5e05ab39e0a064f374ddefc86fb886060a176ff634', 'src/main/resources/assets/destiny/textures/item/hud/reticle_w105_shotgun_precision.png': '9e58979fac0cd041802bf3b0f0bb0a75a3ee8d527f4f1408a356d2ef0f6deb7e', 'src/main/resources/assets/destiny/textures/item/hud/reticle_w105_shotgun_rapid_fire.png': '28d5c5b4056bd0fca8569bbbdf8ea6cd70baf82c7c061acc7ac03b5fd8f11dc6', 'src/main/resources/destiny/weapons/w105-shotgun-patterns.json': '055ce7dd5e73c81f23adc94e9c12a132232c040be5ebe8f861c87f305133b5e3', 'src/test/java/kim/biryeong/destiny/sound/FireVariantsW98Test.java': 'ab4e0b832782cf33ac13d7a6035bb491a479d104406da0e81aa6e221538893d4', 'src/test/java/kim/biryeong/destiny/weapon/ShotgunPatternW105Test.java': '404b416f47c315999fe8b3c13465c5fe5c867120cec65c5d6857161e61ad903c', 'src/test/java/kim/biryeong/destiny/weapon/WeaponCombatTest.java': '8a807cb174cc04a0394e476a12c9f0b26c5c22a104db7480d215baacfac695ae'}
JAR_DELTA_PINS = {'added': {'assets/destiny/items/gui/hud/reticle_w105_shotgun_aggressive.json': 'eba35c538b1449ce7960838ae1f6aff6a4e37c8f611b33e4342bbac4b68bc0e1', 'assets/destiny/items/gui/hud/reticle_w105_shotgun_lightweight.json': 'd1400b703a50e1a71ab22406b10a63477e4acf5924d139c146be44dbdd055b19', 'assets/destiny/items/gui/hud/reticle_w105_shotgun_precision.json': 'd0ba22dc12bfd38689976313ef9a452e3a068bd09fad8fd8575605b264139d42', 'assets/destiny/items/gui/hud/reticle_w105_shotgun_rapid_fire.json': '5aa301dbac73da49b8f4a83990c99ade4f65c6b632c6539d87f0d10ccc827f26', 'assets/destiny/models/gui/hud/reticle_w105_shotgun_aggressive.json': 'd992dc0a1e7dbff11f04490d2a9f08655b95cd71014642e4717e3fef1deabcfa', 'assets/destiny/models/gui/hud/reticle_w105_shotgun_lightweight.json': '76cbd547427cd8fa04937cfe168801b5d4cb22ca8f03953e660f0781410ff112', 'assets/destiny/models/gui/hud/reticle_w105_shotgun_precision.json': 'f50072e018eba943cc1745fced50dd2ff31f215dd915dd0720252ecd5b17cef7', 'assets/destiny/models/gui/hud/reticle_w105_shotgun_rapid_fire.json': 'e4564965d5561ae155479c56900e1e602e01dffd5309237a55cc82e1d4eb0932', 'assets/destiny/textures/item/hud/reticle_w105_shotgun_aggressive.png': '1a002f3865add5e553010ddbff90b8dc4e3421c8520a8320dd16ac69f7187abe', 'assets/destiny/textures/item/hud/reticle_w105_shotgun_lightweight.png': 'c6837d225c9cb309c69bbe5e05ab39e0a064f374ddefc86fb886060a176ff634', 'assets/destiny/textures/item/hud/reticle_w105_shotgun_precision.png': '9e58979fac0cd041802bf3b0f0bb0a75a3ee8d527f4f1408a356d2ef0f6deb7e', 'assets/destiny/textures/item/hud/reticle_w105_shotgun_rapid_fire.png': '28d5c5b4056bd0fca8569bbbdf8ea6cd70baf82c7c061acc7ac03b5fd8f11dc6', 'destiny/weapons/w105-shotgun-patterns.json': '055ce7dd5e73c81f23adc94e9c12a132232c040be5ebe8f861c87f305133b5e3', 'kim/biryeong/destiny/weapon/ShotgunPatternProfile$Row.class': '9fed5e2a43e42825e2306badea0cbca36b962374f959800aac9a30bd74927361', 'kim/biryeong/destiny/weapon/ShotgunPatternProfile.class': '48f0da815427d9b6b188c421568bf362e0f45a2d3e31a140bed11d91f4f8eeae', 'kim/biryeong/destiny/weapon/ShotgunSpread$Point.class': 'cc0be32aa6e3808a8d33837aeb93dd134891a49a727fc40ad657327a5f434a7e', 'kim/biryeong/destiny/weapon/ShotgunSpread$Shape.class': '64ed9aaa5460d7fc9b11b3f40eb83b0674d004ff236b96f7dfd3bb6f05e0a0c4', 'kim/biryeong/destiny/weapon/ShotgunSpread$Vector.class': '19cc2ebb35e91ec41c12e3b0c59169643761eb117a31aa26f88f44b598a3c25f', 'kim/biryeong/destiny/weapon/ShotgunSpread.class': 'e9fa69975f27b6bdd6a8d26ecfc6df98ea79b5f2a7293d0ccca5aa48863dfe4c'}, 'modified': {'kim/biryeong/destiny/hud/WeaponReticleHud$1.class': {'before': '53110b7d1cf101d87b2a165884e390f612892c7cec66b474982613a6f33ef652', 'after': '07e890792788bc51a042a1585d5945ef6291ac15e15bc03537d5f1ac01aec3d3'}, 'kim/biryeong/destiny/hud/WeaponReticleHud.class': {'before': '613a15d10dbf1bbffeeb374efaf8c3187809689066ca4c79934db1d611fe858f', 'after': '9ec80a95bac376851784cc2367120268b50a97da30fd138a3cc3139a0862ba64'}, 'kim/biryeong/destiny/weapon/WeaponProfile.class': {'before': '9767b73aec307d94ff6afde012dc0c15430f1f742e1d00a20bfe1d50aff9f814', 'after': '5e342f4b674922f9efb621bb534b5ce35c412287d9066a132c4ff3210f9758c3'}, 'kim/biryeong/destiny/weapon/WeaponRuntime$FlightSnapshot.class': {'before': '1d256bd958421f011abe25e8ef78cd931157c06fb8ab79c626977ee15ee72120', 'after': '333c128ba13718c7b6fdb51b21ae15856db0317e55c9b76fd41e9c344b7d5ef6'}, 'kim/biryeong/destiny/weapon/WeaponRuntime$GlaiveStatus.class': {'before': '8a7d1dcef98fee4a5896587b42bb95b2f2c15a45a97bb7b2f67adbe732313a00', 'after': 'bfa7b5049e95c157d159046bac328925df2ec93e2f3ca64897f97f95d685b1a4'}, 'kim/biryeong/destiny/weapon/WeaponRuntime$HitDamage.class': {'before': '2a40306451eb3e4e76610d7e3b7139c8a2132705c8adb405ae16983898120ab6', 'after': '77194aa6f6445234fa509e30101e2d7be5d5b969b27bb26e716e4b7b6485c92e'}, 'kim/biryeong/destiny/weapon/WeaponRuntime$SwordStatus.class': {'before': '72e7a8d423ed5143f96549f54de7bdb0f28c337405cbcc935e44f02216c86262', 'after': 'a28991f06bd5cd39e77b336188a760d88c8e79e9b91e927b8896ccfa39352273'}, 'kim/biryeong/destiny/weapon/WeaponRuntime.class': {'before': '5654e3ae215bdf8c49d6487ece628b4805a28cbc07badcf7a811096cb00058cf', 'after': '5135f1e5def97a408cbeaf0875d25acf95c7e53c28442275e76b829dc77549f9'}}, 'removed': []}
NESTED_SHA = '82a323b998eb5353244fed26a93c6a9f2041d79dbcdf8af68d8bdd5c4d916b31'

if __name__=="__main__":
    raise SystemExit(main())
