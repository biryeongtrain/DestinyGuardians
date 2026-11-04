#!/usr/bin/env python3
"""Finite W104 source/artifact audit. No builds, generators, game launch or native acceptance.

Default/--source-only checks the reviewed source freeze. Existing --jar/--pack
are read only. --finalize requires both artifacts, an exact final integration,
and two explicit consecutive archived gates. JSON report is stdout; retain it
as art/qa/w104/implementation.json only after successful finalization.
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

ROOT = Path(__file__).resolve().parents[2]
QA = "docs/qa/2026-10-25/w104"
OLD_QA = "docs/qa/2026-10-25/w103"
OLD = "art/qa/w103/implementation.json"
OLD_SHA = "2e12f96a23c11f6a3429267c8fafb83dabe27371d581be7731259cafa9ca8488"
OLD_TREE_SHA = "8099794037dd04320689e1ea3a6adfd0eedebdaa547219ce9ae584eaf6522d9e"
COMMON = "scripts/qa/audit_named_audio_w102.py"
COMMON_SHA = "f05bfc4db1324639c1218cc7b5965fca97f05bf0043ac3939d60012ac3e4c4ff"
SELF = "scripts/qa/audit_tracking_w104.py"
REGISTRY = "src/gametest/resources/fabric.mod.json"
UNIT = "src/test/java/kim/biryeong/destiny/weapon/TrackingW104Test.java"
GT = "src/gametest/java/kim/biryeong/destiny/test/TrackingW104GameTests.java"
GT_CLASS = "kim.biryeong.destiny.test.TrackingW104GameTests"
UNIT_CLASS = "kim.biryeong.destiny.weapon.TrackingW104Test"
BASE = "src/main/java/kim/biryeong/destiny/weapon/"
RES = "src/main/resources/"
PROFILE = RES + "destiny/weapons/w104-tracking.json"
CONTRACT = QA + "/integration.json"
ROOTS = ("src/main/java", "src/main/resources", "src/test/java", "src/test/resources", "src/gametest/java", "src/gametest/resources")
MIGRATIONS = {BASE + n + ".java" for n in ("WeaponRuntime", "WeaponAiming", "WeaponPerks")}
MIGRATIONS.add("src/main/java/kim/biryeong/destiny/hud/WeaponReticleHud.java")
NEW = {BASE+n+".java" for n in ("TrackingProfile", "TrackingSteering", "WeaponTracking")} | {PROFILE, UNIT, GT}
REVIEWED = {'src/main/java/kim/biryeong/destiny/weapon/TrackingProfile.java': '125bb22a77d140d2d8bfc8888a212e0387676602e244b4192612e54f25289b5a', 'src/main/java/kim/biryeong/destiny/weapon/TrackingSteering.java': '4d50bb67431c6a2810663c513fa7ff6f5625b490119e2e2a305c982407164388', 'src/main/java/kim/biryeong/destiny/weapon/WeaponTracking.java': '239847e31cb619807e60afeac073d46362f4585399054aeb8b51d72f84ecc58a', 'src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java': '1e352d7d5c85b664f2c7ab7018c7298ccb582c90be2e4bea7bba66c113aa1aca', 'src/main/java/kim/biryeong/destiny/weapon/WeaponAiming.java': 'ffeff9973d99bcd1dee1988b59ebcb20b4bdc8c70f237bb4cf0c69be4cd4530b', 'src/main/java/kim/biryeong/destiny/weapon/WeaponPerks.java': '5b2e8b5916cffb103a77c1c0106dae29e13849986b225c3ab5ef7d518f95d640', 'src/main/java/kim/biryeong/destiny/hud/WeaponReticleHud.java': 'aec7e1c6543effe85147ca0b645942eda9f6928e3ce3bc355bec9e6d1f91d3ae', 'src/main/resources/destiny/weapons/w104-tracking.json': 'c4ecf3805a1cc7c6529565f899cc45efbb811bf07c743558a40c76aadd3e789e', 'src/test/java/kim/biryeong/destiny/weapon/TrackingW104Test.java': '87f221789853fcd7308898d9ff2420e3edffbc79cb0c6a485622a6742b84919c', 'src/gametest/java/kim/biryeong/destiny/test/TrackingW104GameTests.java': '03ae3cb2463ccd963786e5c4ec5d47164a797183ae71d6ed5cc8fc9d51f69c04', 'docs/qa/2026-10-25/w104/integration.json': 'b5da0758e6baf200d9dad15a7bcf7573f201e3950bf538a4f3255fd0def5deae', 'scripts/extract_tracking_w104.py': '4cb194f73765b74a73183f155dc9088062e11f5c7688fcd553eabce7132ca455', 'art/weapons/w104/references/CONTRACT.md': '8433a658e377957b1e452ab9b31e8f95040979bfbdd163b198b977e08362b7d2', 'art/weapons/w104/references/mechanics.json': '4cd9ff65a9f97fc9d9cd78e5845dc4e944bb7a6be623a75395944b985f639f01', 'art/weapons/w104/references/socket-pools.json': 'ec62c9481faea655883c3bccb175e972d0dcc2bfc9c851b24efabfcfba6f3ab6', 'art/weapons/w104/references/provenance.json': 'fc8b23f4988e7c76471955cc906ee0d0c1a01577c06a8a11523cb251e3019d16', 'art/weapons/w104/references/verification.json': '43e42d97e995b7d4684b260403e02b4463ca29df3fc3da4cdbdb2c9905725617'}
JAR_SHA = "9fe7c0f35aa3687ff3ba000399632ab34185f7962031a0d34e7cf9b01daf40c5"
JAR_DELTA_PINS = {'added': {'destiny/weapons/w104-tracking.json': 'c4ecf3805a1cc7c6529565f899cc45efbb811bf07c743558a40c76aadd3e789e', 'kim/biryeong/destiny/weapon/TrackingProfile.class': '822efd0a89bab801a28d8221dd78c6b6555a7f584804be4d3831df65319daa19', 'kim/biryeong/destiny/weapon/TrackingSteering$Vector.class': '04decc752ee0c935363d8f7b7d11681969d42d6be1aeb79c74315350379154d8', 'kim/biryeong/destiny/weapon/TrackingSteering.class': 'e098c4af7e03cc51d8eecdf383d9a07805e4aaa54219a32b5741ef7339b2e810', 'kim/biryeong/destiny/weapon/WeaponRuntime$FlightSnapshot.class': '1d256bd958421f011abe25e8ef78cd931157c06fb8ab79c626977ee15ee72120', 'kim/biryeong/destiny/weapon/WeaponTracking$Flight.class': '8b876cda264b27b787d4911d3f7598ab481a4faab0f22b8626a7562cc880519b', 'kim/biryeong/destiny/weapon/WeaponTracking$Phase.class': '917bfe3b1c8a4df8cfe44d4ad408edb7121ed7ec988d6c9dbf78c6aabd3b2bfe', 'kim/biryeong/destiny/weapon/WeaponTracking$Session.class': '4bd684b3cbdf544776b2eafe8c3fdcf45d41bccfb3d7054875179085beb8234e', 'kim/biryeong/destiny/weapon/WeaponTracking$Status.class': '8bf59953c60913900b6a5459fe35946c8ac98f35c5026808080b995ac121a49b', 'kim/biryeong/destiny/weapon/WeaponTracking.class': '2b5e0cc218327519939228f0b21703da15959b13e7450d0f6bec739ee4a06cf1'}, 'modified': {'kim/biryeong/destiny/hud/WeaponReticleHud$1.class': {'before': '7ccb43497efd42b3ad7eafd60abca8f37152ec79079703429f25682b3bb90122', 'after': '53110b7d1cf101d87b2a165884e390f612892c7cec66b474982613a6f33ef652'}, 'kim/biryeong/destiny/hud/WeaponReticleHud$Style.class': {'before': '24b96a51bc92d4d5ae26df3f47048ae3f562aecca06292350e85aa9b5629fc50', 'after': '1646c87cbd54d223ac04206a5cddafef12208a58e7d7543a42d19845c44e37dc'}, 'kim/biryeong/destiny/hud/WeaponReticleHud.class': {'before': '62bb5a72fbaaefc5ccd3121dedaecc16303901d679112a4a8183a02995020fcc', 'after': '613a15d10dbf1bbffeeb374efaf8c3187809689066ca4c79934db1d611fe858f'}, 'kim/biryeong/destiny/weapon/WeaponAiming.class': {'before': '652639d23170bde8346a9f5943bbf36a93d9c7d822aabce1aabacbb7b9d9fdae', 'after': 'fd6e3c60c9f024639b79bf8d5ba0326552319fbed20b521a1b386a6f09f99bc4'}, 'kim/biryeong/destiny/weapon/WeaponPerks.class': {'before': 'dba5c4cfd9cb3affe3de59cd4b170aa7751f58e92e0c3602d7d6a2be0e91f1aa', 'after': '2836e97f15178f06c35e1323636ca67e677d423934c7cfa060eac6c28f5e22cc'}, 'kim/biryeong/destiny/weapon/WeaponRuntime$GlaiveStatus.class': {'before': 'ef821b3d6116f28b4d10dca0b65bf15b58a3c6ed8406ca65f172179e20f21d8a', 'after': '8a7d1dcef98fee4a5896587b42bb95b2f2c15a45a97bb7b2f67adbe732313a00'}, 'kim/biryeong/destiny/weapon/WeaponRuntime$HitDamage.class': {'before': 'f01f4a9f80fe3c82d03faa9d2b8792f2005dfcebd15a58eff94efd207f2a6a7f', 'after': '2a40306451eb3e4e76610d7e3b7139c8a2132705c8adb405ae16983898120ab6'}, 'kim/biryeong/destiny/weapon/WeaponRuntime$Shot.class': {'before': 'adaace28ed3fef5b778344ac41f2c04768514b4f77401dbc28e0bf6ad4e370ce', 'after': '7b34f66f538535cae197d555cfa7a62ad27faffb51d354a03c3c0fc8589a3389'}, 'kim/biryeong/destiny/weapon/WeaponRuntime$SwordStatus.class': {'before': '7acfa722ff20aa71046e8dacbe9a80ac4b5861c611f5c50b68d320a192eb0546', 'after': '72e7a8d423ed5143f96549f54de7bdb0f28c337405cbcc935e44f02216c86262'}, 'kim/biryeong/destiny/weapon/WeaponRuntime.class': {'before': '53f703c93f37d4a5f9961ae438521945e27c9aceca830ab4e7b4ccd573a46c83', 'after': '5654e3ae215bdf8c49d6487ece628b4805a28cbc07badcf7a811096cb00058cf'}}, 'removed': []}
NESTED_REVIEW = {'stage': 'W104', 'status': 'FULL_VERBOSE_LINE_NUMBER_ONLY', 'classes': {'kim/biryeong/destiny/hud/WeaponReticleHud$Style.class': {'before': {'classSha256': '24b96a51bc92d4d5ae26df3f47048ae3f562aecca06292350e85aa9b5629fc50', 'javapPath': 'docs/qa/2026-10-25/w104/independent-WeaponReticleHud$Style-before-javap-v.txt', 'javapSha256': '24dc637e061182767a369bc68525d8974237275a606473c9d0e9c45cf11c4975'}, 'after': {'classSha256': '1646c87cbd54d223ac04206a5cddafef12208a58e7d7543a42d19845c44e37dc', 'javapPath': 'docs/qa/2026-10-25/w104/independent-WeaponReticleHud$Style-after-javap-v.txt', 'javapSha256': '97c8f6141fd5cfcc70d9652c60f22eb665c1e2cf53ee2b92842dc864f05d1b58'}, 'equalAfterRemovingOnlyArchiveHeaderAndLineRows': True, 'normalizedVerboseSha256': 'eec13ac126ea414e92ae3b0eace12b5a44a779afd8023582601b26b44a29f668'}, 'kim/biryeong/destiny/weapon/WeaponRuntime$GlaiveStatus.class': {'before': {'classSha256': 'ef821b3d6116f28b4d10dca0b65bf15b58a3c6ed8406ca65f172179e20f21d8a', 'javapPath': 'docs/qa/2026-10-25/w104/independent-WeaponRuntime$GlaiveStatus-before-javap-v.txt', 'javapSha256': 'aae0fe14a95ea2fa50c3fadaf7bd688d8fa8ff047d14b56ae018384701f1d2f3'}, 'after': {'classSha256': '8a7d1dcef98fee4a5896587b42bb95b2f2c15a45a97bb7b2f67adbe732313a00', 'javapPath': 'docs/qa/2026-10-25/w104/independent-WeaponRuntime$GlaiveStatus-after-javap-v.txt', 'javapSha256': '9c963d4618481f2a2ca493daa20d35912303354094efc88017e74d4a7058acb8'}, 'equalAfterRemovingOnlyArchiveHeaderAndLineRows': True, 'normalizedVerboseSha256': 'a6d0c2eb3d56556df25ae021941925fddc2f787563691813242c75c51f5d3ffe'}, 'kim/biryeong/destiny/weapon/WeaponRuntime$HitDamage.class': {'before': {'classSha256': 'f01f4a9f80fe3c82d03faa9d2b8792f2005dfcebd15a58eff94efd207f2a6a7f', 'javapPath': 'docs/qa/2026-10-25/w104/independent-WeaponRuntime$HitDamage-before-javap-v.txt', 'javapSha256': '138e6f66a4c566e5bf157127887bdd3b01269a8bb8ccd1c6c83b6cd9c3fdcee0'}, 'after': {'classSha256': '2a40306451eb3e4e76610d7e3b7139c8a2132705c8adb405ae16983898120ab6', 'javapPath': 'docs/qa/2026-10-25/w104/independent-WeaponRuntime$HitDamage-after-javap-v.txt', 'javapSha256': 'c74f84a0e2b149817d40848ed1ebe5f61714bfffdec63a4a35d67649ff8dd6f7'}, 'equalAfterRemovingOnlyArchiveHeaderAndLineRows': True, 'normalizedVerboseSha256': '2fad246107e5c1f7f1a93b31585459be6f8fa8db993a84d833052be569e88910'}, 'kim/biryeong/destiny/weapon/WeaponRuntime$SwordStatus.class': {'before': {'classSha256': '7acfa722ff20aa71046e8dacbe9a80ac4b5861c611f5c50b68d320a192eb0546', 'javapPath': 'docs/qa/2026-10-25/w104/independent-WeaponRuntime$SwordStatus-before-javap-v.txt', 'javapSha256': 'd41fc085938d3bd912fa7b6096fcc5e7247c0858ea9f737a3081939fb27035f2'}, 'after': {'classSha256': '72e7a8d423ed5143f96549f54de7bdb0f28c337405cbcc935e44f02216c86262', 'javapPath': 'docs/qa/2026-10-25/w104/independent-WeaponRuntime$SwordStatus-after-javap-v.txt', 'javapSha256': 'a92af41e287173e9902453f09d4643b23bf182a9d8c34b82bb7edb616e79dbf1'}, 'equalAfterRemovingOnlyArchiveHeaderAndLineRows': True, 'normalizedVerboseSha256': '3f39ca057629ab782d52ad2f2ab0389f995da1582eeb5cd61034b9124c241995'}}, 'nativeAccepted': False}
NESTED_REVIEW_SHA = "158809426b4be92388423db6772dfa2f8d803d518c2ac53a0937ea1bdc76a8d1"


def common():
    path=ROOT/COMMON
    if hashlib.sha256(path.read_bytes()).hexdigest()!=COMMON_SHA:
        raise RuntimeError("Frozen common parsers changed")
    spec=importlib.util.spec_from_file_location("w104_frozen_common",path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def source_audit(c, inp):
    need=c.need
    need(inp.hash(OLD)==OLD_SHA,"W103 manifest changed")
    old=inp.json(OLD)
    need(old["sourcePins"]==len(old["sha256"])==8760 and len(old["clientAssets"])==7207,"W103 inventory")
    tree={p:inp.hash(p) for p in sorted(inp.files(OLD_QA))}
    need(len(tree)==289 and c.sha(json.dumps(tree,sort_keys=True,separators=(",",":")).encode())==OLD_TREE_SHA,"W103 QA tree changed")
    need(inp.hash("scripts/qa/audit_demolitionist_w103.py")=="904d9421dfebcd5ce04804019b004a64a063fda3656e709b7ef2d58ac41c6a53","Frozen W103 auditor changed")
    for p,h in REVIEWED.items():need(inp.hash(p)==h,"Reviewed input changed: "+p)
    for p,h in old["sha256"].items():
        if p not in MIGRATIONS|{REGISTRY}:need(inp.hash(p)==h,"Inherited source changed: "+p)
    need(len(MIGRATIONS)==4 and all(REVIEWED[p]!=old["sha256"][p] for p in MIGRATIONS),"Exact four shared Java changes")
    before=inp.json(QA+"/before-shared.json")
    need(set(before)==MIGRATIONS|{BASE+"WeaponPerkCommands.java",REGISTRY},"Before snapshot inventory")
    for p,h in before.items():
        need(h==old["sha256"][p] and inp.hash(QA+"/before/"+p)==h,"Before snapshot changed: "+p)
    original=inp.json(QA+"/before/"+REGISTRY);current=inp.json(REGISTRY)
    classes=original["entrypoints"]["fabric-gametest"]
    need(current["entrypoints"]["fabric-gametest"]==classes+[GT_CLASS],"Registry must be exact append")
    current["entrypoints"]["fabric-gametest"]=classes
    need(current==original,"Unrelated registry edit")
    files=set().union(*(inp.files(folder) for folder in ROOTS))
    inherited={p for p in old["sha256"] if any(p.startswith(r+"/") for r in ROOTS)}
    need(inherited<=files and files-inherited==NEW,"Exact three Java/one JSON/two tests additions; no removals")
    clients={p:inp.hash(p) for p in files if p.startswith(RES+"assets/")}
    need(clients==old["clientAssets"],"Client asset inventory or content changed")
    contract=inp.json(CONTRACT)
    need(contract["stage"]=="W104" and contract["previous"]=="W103" and contract["expectedJUnit"]==744 and contract["expectedGameTests"]==852,"Integration totals/stage")
    need(contract["newTestPins"]=={UNIT:REVIEWED[UNIT],GT:REVIEWED[GT]},"Reviewed test pins")
    names=re.findall(r"^\s*@Test\s+(?:public\s+)?void\s+(\w+)\s*\(\s*\)",inp.data(UNIT).decode(),re.M)
    methods=re.findall(r"^\s*@GameTest\([^\n]*\)\s+public\s+void\s+(\w+)\s*\(GameTestHelper h\)",inp.data(GT).decode(),re.M)
    need(len(names)==len(set(names))==13 and [[UNIT_CLASS,n+"()"] for n in names]==contract["newJUnitIdentities"],"Exact thirteen JUnit identities")
    need(len(methods)==len(set(methods))==11 and methods==contract["newGameTestMethods"],"Exact eleven GameTest identities")
    need(all(contract[k] is False for k in ("nativeRenderingAccepted","nativeAudioAccepted","wholeGoalAchieved")),"Acceptance boundary")
    provenance=inp.json("art/weapons/w104/references/provenance.json")
    for pin in provenance["sourcePins"].values():need(inp.hash(pin["path"])==pin["sha256"],"Official source pin changed: "+pin["path"])
    need(provenance["generatorSha256"]==REVIEWED[provenance["generator"]],"Extractor provenance")
    profile=inp.json(PROFILE)
    need(profile["intrinsicWeapons"]==[{"id":"pyroclastic_flow","hash":1289324202,"socket":0,"intrinsicHash":3419274965,"proofMode":"initialIntrinsic"}],"Exact intrinsic")
    expected=[("bad_omens",991314988,457210958),("bellowing_giant",2186258845,2605036073)]
    need(profile["weapons"]==[{"id":i,"hash":h,"socket":3,"perkHash":3977735242,"plugSetHash":p,"proofMode":"randomized"} for i,h,p in expected],"Exact optional sockets")
    rules=profile["sourceRules"]
    need(rules["requiresAim"] is True and rules["continuousAimAfterLaunchRequired"] is None and len(rules["unknownSourceRules"])==17 and all(v is None for v in rules["unknownSourceRules"].values()),"Unknown source rules must stay null")
    inventory=inp.json(provenance["sourcePins"]["inventory"]["path"])
    pools=inp.json(provenance["sourcePins"]["plugSets"]["path"])
    for ident,h,poolhash in expected:
        sockets=inventory[str(h)]["sockets"];pool=pools[str(poolhash)]
        need(any(cat["socketCategoryHash"]==4241085061 and 3 in cat["socketIndexes"] for cat in sockets["socketCategories"]),"Official trait category")
        need(sockets["socketEntries"][3]["randomizedPlugSetHash"]==poolhash and pool.get("isFakePlugSet",False) is False,"Real randomized pool")
        need(any(v["plugItemHash"]==3977735242 and v.get("currentlyCanRoll") is True for v in pool["reusablePlugItems"]),"Official selected trait option")
    need(inventory["1289324202"]["sockets"]["socketEntries"][0]["singleInitialItemHash"]==3419274965,"Official intrinsic socket")
    snapshot={p:inp.hash(p) for p in sorted(set(old["sha256"])|files|set(REVIEWED)|{SELF})}
    return old,contract,snapshot,clients


def normalized_verbose(raw):
    return "\n".join(line for line in raw.decode().splitlines() if not re.match(r"^(Classfile |  Last modified |  SHA-256 checksum )",line) and not re.fullmatch(r"\s*line [0-9]+: [0-9]+",line))+"\n"


def artifacts(c,inp,args,old):
    result={}
    if args.pack:c.need(args.jar is not None,"Pack requires product JAR")
    if args.jar:
        oldraw=inp.data(OLD_QA+"/product.jar");raw=inp.data(args.jar)
        c.need(c.sha(oldraw)==old["jarSha256"] and c.sha(raw)==JAR_SHA,"Exact old/new product JAR pins")
        before=c.archive(oldraw);after=c.archive(raw);a=c.hashes(before);b=c.hashes(after)
        delta=c.delta(a,b)
        pins={"added":{p:b[p] for p in delta["added"]},"modified":{p:{"before":a[p],"after":b[p]} for p in delta["modified"]},"removed":delta["removed"]}
        c.need(pins==JAR_DELTA_PINS,"Exact 10 additions/10 modifications/zero removals with raw SHA pins")
        c.need(inp.hash(QA+"/independent-nested-1.json")==NESTED_REVIEW_SHA,"Independent verbose metadata review changed")
        nested=inp.json(QA+"/independent-nested-1.json")
        c.need(nested==NESTED_REVIEW,"Exact metadata review contents")
        for p,row in nested["classes"].items():
            c.need(a[p]==row["before"]["classSha256"] and b[p]==row["after"]["classSha256"],"Exact metadata-only raw class bytes: "+p)
            texts=[]
            for phase in ("before","after"):
                r=row[phase];rawtext=inp.data(r["javapPath"])
                c.need(c.sha(rawtext)==r["javapSha256"],"Verbose disassembly changed")
                texts.append(normalized_verbose(rawtext))
            c.need(texts[0]==texts[1] and c.sha(texts[0].encode())==row["normalizedVerboseSha256"],"Not proven LineNumberTable-only: "+p)
        for p in inp.files("src/main/resources"):
            member=p[len(RES):]
            if member=="fabric.mod.json":c.need(after.get(member)==before[member],"Processed Fabric metadata changed")
            else:c.need(after.get(member)==inp.data(p),"Packaged resource/source mismatch: "+member)
        result.update(jarSha256=JAR_SHA,jarDelta=delta,jarDeltaPins=pins,metadataOnlyClassPins=nested["classes"])
    if args.pack:
        previous=inp.data(OLD_QA+"/headless/resource_pack.zip");raw=inp.data(args.pack)
        c.need(c.sha(raw)==c.sha(previous)==old["serverPackSha256"],"Actual whole pack must be byte-identical to W103")
        pack=c.archive(raw);counts={}
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            infos=z.infolist();counts={"files":sum(not i.is_dir() for i in infos),"directories":sum(i.is_dir() for i in infos),"total":len(infos)}
        c.need(counts=={"files":12359,"directories":178,"total":12537} and len(pack)==12359,"Pack files/directories inventory")
        result.update(serverPackSha256=c.sha(raw),previousPackSha256=c.sha(previous),packEntries=len(pack),packArchiveCounts=counts,packEntryDelta={"added":[],"modified":[],"removed":[]})
    return result


def gate_audit(c,inp,args,contract):
    c.need(args.gates and args.gates[0]>=1 and args.gates[1]==args.gates[0]+1,"Two explicit consecutive gates required")
    prior=c.junit(inp,OLD_QA+"/gate-2-xml");expected={tuple(v) for v in contract["newJUnitIdentities"]}
    c.need(len(prior)==731 and len(expected)==13 and not prior&expected,"Inherited/new JUnit inventory")
    summary=inp.json(QA+"/gate-summary.json")
    c.need(summary["finalPassingGates"]==args.gates and summary["jarSha256"]==JAR_SHA and (summary["previousGameTests"],summary["newGameTests"],summary["previousJUnit"],summary["newJUnit"])==(841,11,731,13),"Final gate summary contract")
    results=[]
    for n in args.gates:
        prefix=QA+f"/gate-{n}";row=inp.json(prefix+"-exit.json");log=inp.data(prefix+".log").decode()
        c.need(row["gate"]==n and row["returncode"]==0 and row["finishedAt"]>row["startedAt"],"Gate failed/incomplete")
        c.need(re.findall(r"All (\d+) required tests passed",log)==["852"] and re.findall(r"(\d+) GAME TESTS COMPLETE",log)==["852"] and "BUILD SUCCESSFUL" in log and all(v not in log for v in ("BUILD FAILED","UP-TO-DATE","FROM-CACHE")) and re.search(r"20 actionable tasks: 20 executed",log),"Not complete forced 852-GT gate")
        cases=c.junit(inp,prefix+"-xml")
        c.need(cases==prior|expected and len(cases)==744,"Inherited plus exact 13 new passing JUnit cases")
        xmls={Path(p).name for p in inp.files(prefix+"-xml") if p.endswith(".xml")}
        c.need(set(row["xmlFreshness"])==xmls and all(v is True for v in row["xmlFreshness"].values()),"Full fresh XML inventory")
        c.need(inp.data(prefix+"-jar.sha256").decode().strip()==JAR_SHA,"Gate/product JAR mismatch")
        listed=[r for r in summary["gates"] if r["gate"]==n]
        c.need(len(listed)==1,"Summary duplicate/missing gate")
        s=listed[0]
        c.need(s["returncode"]==0 and s["junit"]=={"tests":744,"failures":0,"errors":0,"skipped":0} and s["previousJUnitIdentitiesPreserved"]==731 and s["newJUnit"]==13 and s["requiredPassed"]==s["gameTestsTotal"]==852 and s["forcedAllTasks"] is True and s["allXmlFresh"] is True and s["jarSha256"]==JAR_SHA,"Summary/raw artifact disagreement")
        results.append({"gate":n,"junit":744,"inheritedJUnit":731,"gametests":852,"startedAt":row["startedAt"],"finishedAt":row["finishedAt"]})
    c.need(results[0]["finishedAt"]<=results[1]["startedAt"],"Gates must be serial")
    failures=[]
    for n in range(1,args.gates[-1]+1):
        prefix=QA+f"/gate-{n}";r=inp.json(prefix+"-exit.json")
        if r["returncode"]!=0:failures.append({"gate":n,"returncode":r["returncode"],"exitSha256":inp.hash(prefix+"-exit.json"),"logSha256":inp.hash(prefix+".log")})
    retained={p:inp.hash(p) for p in inp.files(QA) if Path(p).name in {"pack-attempt-1-delta.json","pack-provenance.json","cleanup.json"}}
    return results,failures,retained


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-only",action="store_true")
    parser.add_argument("--jar",type=Path);parser.add_argument("--pack",type=Path)
    parser.add_argument("--finalize",action="store_true");parser.add_argument("--gates",nargs=2,type=int)
    args=parser.parse_args()
    try:
        c=common();inp=c.Inputs();inp.hash(COMMON);inp.hash(SELF)
        c.need(not(args.source_only and (args.jar or args.pack or args.finalize or args.gates)),"Source-only cannot accept artifacts/gates")
        if args.finalize:c.need(args.jar and args.pack and args.gates,"Finalization requires JAR, actual pack and explicit gates")
        c.need(not args.gates or args.finalize,"Gates are accepted only with --finalize")
        old,contract,snapshot,clients=source_audit(c,inp)
        report={"stage":"W104","status":"SOURCE_PASS","candidateOnly":True,"finalized":False,"pending":[],"sourcePins":len(snapshot),"sha256":snapshot,"clientAssetCount":len(clients),"clientAssets":clients,"previousManifestSha256":OLD_SHA,"acceptedOldChanges":sorted(MIGRATIONS|{REGISTRY}),"newSourcePaths":sorted(set(snapshot)-set(old["sha256"])),"expectedJUnit":744,"expectedGameTests":852,"newJUnitIdentities":contract["newJUnitIdentities"],"newGameTestMethods":contract["newGameTestMethods"],"nativeRenderingAccepted":False,"nativeAudioAccepted":False,"wholeGoalAchieved":False,"generatorExecutedByAuditor":False,"childAgentWorkClaimed":False}
        report.update(artifacts(c,inp,args,old))
        if args.jar:report["status"]="JAR_PASS"
        if args.pack:report["status"]="PACK_PASS"
        if args.finalize:
            report["gates"],report["retainedPriorGateFailures"],report["retainedDiagnosticPins"]=gate_audit(c,inp,args,contract)
            report.update(status="SEALED_CANDIDATE",finalized=True,finalPassingGates=args.gates)
        inp.recheck();report["inputSha256"]=dict(sorted(inp.hashes.items()))
        print(json.dumps(report,indent=2,sort_keys=True));return 0
    except Exception as error:
        print(json.dumps({"stage":"W104","status":"FAIL","reason":str(error)},sort_keys=True),file=sys.stderr);return 1

if __name__=="__main__":
    raise SystemExit(main())
