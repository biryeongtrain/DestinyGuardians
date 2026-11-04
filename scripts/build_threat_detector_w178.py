#!/usr/bin/env python3
"""Pinned offline Threat Detector base sockets/curves. No game or Gradle.
--verify is read-only; --self-test runs bounded negative and reproducibility checks.
Only four owned JSON outputs are written. Historical curves are not current sandbox measurements.
"""
import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ART = "art/weapons/w178/threat-detector/"
TARGET = "src/main/resources/destiny/weapons/w178-threat-detector.json"
SCRIPT = "scripts/build_threat_detector_w178.py"
BASE, ENHANCED, TRAIT = 4071163871, 494941759, 4241085061
VERSION = "245114.26.10.13.2000-1-bnet.66137"
EXPECTED = {
("seventh_seraph_officer_revolver",3037520408,3,BASE,903350103),
("cold_denial",1216130969,3,BASE,330841869),
("claws_of_the_wolf",1280933460,3,BASE,206409262),
("bug_out_bag",2744715540,3,BASE,907333373),
("dead_man_walking_xx7463",3751622019,3,BASE,3268663985),
("high_albedo",1197486957,3,BASE,2797218184),
("brass_attacks",2121785039,3,BASE,100135553),
("mindbender_s_ambition_adept",912150785,3,BASE,1732284294),
("dust_rock_blues",636912560,3,BASE,3511609070),
("parcel_of_stardust_fell_to_earth",2217366863,3,BASE,2514419370),
("dream_breaker",2931957300,3,BASE,3785896921),
("ikelos_smg_v1_0_1",1723472487,4,BASE,1329),
("ikelos_sg_v1_0_1",1887808042,4,BASE,1324),
("line_in_the_sand",946443267,3,BASE,1503774254),
("deafening_whisper",981718087,4,BASE,3588287812),
("edge_transit",218335759,3,BASE,447678063),
("dimensional_hypotrochoid",1311684613,3,BASE,3235863202),
("bellowing_giant",2186258845,4,BASE,1722393382),
("hammerhead",603242241,3,BASE,2515290473),
}
KEYS = ("id", "hash", "socket", "perkHash", "plugSetHash")
PERK = {"id":"threat_detector", "hash":BASE, "radius":15.0,
        "stabilityBonus":[0,15,40], "reloadBonus":[0,18,60],
        "handlingBonus":[0,25,100], "handlingScalar":[1.0,0.9,0.81]}
POLICIES = {
"radius":"LOCAL_INCLUSIVE_FINITE_EUCLIDEAN_FOOTPOINT_SPHERE_ONE_BLOCK_PER_METRE",
"enemies":"LOCAL_PROJECT_COMBAT_ENEMY_MOB_OR_ENEMY_EXCLUDE_PLAYERS_ARMORSTANDS_ALLIES_TAMED_DEAD_REMOVED_SPECTATORS",
"visibility":"NO_WALL_TEST_SOURCE_UNSPECIFIED",
"activation":"HELD_EXACT_ORIGINAL_LAST_UPDATE_SAMPLE_NO_LINGER_NO_TIMER_RESCAN_SAME_TICK",
"identity":"OWNER_LEVEL_GUARDIAN_DATA_RUNTIME_CLASS_CANONICAL_ENTRY_EXACT_ROLL_STACK_IDENTITY",
"timing":"SUM_STATS_CAP_0_100_RAW_CURVES_SCALE_THEN_CEIL_ONCE",
"handling":"READY_AND_STOW_ONLY_SCALAR_STOW_AT100_FLOOR_BEFORE_SCALAR",
"ads":"NO_THREAT_SCALAR_SNAPSHOT_ENTRY_ONLY_PRIMARY_0_5_SPECIAL_0_8",
"reload":"NO_THREAT_SCALAR_PRESERVE_DISTINCT_SHELL_PHASES_ACCEPTED_PLAN_IMMUTABLE",
"combination":"LOCAL_SUM_COMPATIBLE_STATS_MULTIPLY_SOURCED_SCALARS_BEFORE_QUANTIZATION",
"damageRange":"UNCHANGED",
"historical":"D2FOUNDRY_ORACLE_DCD0C7D302B056FFBB532EDCB711D724A17CA8C1_NOT_CURRENT_SANDBOX_MEASUREMENT"
}
PROFILES = {
"snapshot":"w68-snapshot.json", "frenzy":"w172-frenzy.json",
"adrenaline_junkie":"w173-adrenaline-junkie.json", "perpetual_motion":"w170-perpetual-motion.json",
"outlaw":"w62-outlaw.json", "feeding_frenzy":"w108-feeding-frenzy.json",
"rapid_hit":"w169-rapid-hit.json", "stats_for_all":"w176-stats-for-all.json"}
PINS = {'src/main/resources/destiny/weapons/w30.json': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a', 'src/main/resources/destiny/weapons/w40-characteristics.json': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/weapons/w58-handling.json': '4de7d346a93c822784fafa69b62ac66148d51cc11cf2da6706367682b414d3f1', 'src/main/resources/destiny/weapons/w44-aim.json': '0d0a38469c28a74c1a77489d346184eccef347a604c0c0c455d1c7c2e1a80fc8', 'src/main/resources/destiny/weapons/w83-exotics.json': 'bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56', 'src/main/resources/destiny/weapons/w84-exotics.json': '481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e', 'src/main/resources/destiny/weapons/w68-snapshot.json': '7e824633be32953e6c75d3d856ce765223fbb1cbcc3b01affca3d83eb8fcb738', 'src/main/resources/destiny/weapons/w172-frenzy.json': '28a3722a9ea57dc7400a68ddcee80f6c661bf23a1abd0f4dc92dec9065120862', 'src/main/resources/destiny/weapons/w173-adrenaline-junkie.json': 'b2c0d5865d9d72f9ee4d1bd3439d940d52574d7d7539604a9b4fe1e82c3fbf65', 'src/main/resources/destiny/weapons/w170-perpetual-motion.json': 'e4155158bf1692797a3f1c1b0e49d80360c5494173b384a738c3a337fe47275f', 'src/main/resources/destiny/weapons/w62-outlaw.json': '5188d73a271b0a5080eb99d47c50a6d37ccae11fe756ebd2893c70499f3637bc', 'src/main/resources/destiny/weapons/w108-feeding-frenzy.json': '1ffbff575f0a29adc5a749d581f31c2f6dd67dfea20cf4a3484b6d2c1c522ce8', 'src/main/resources/destiny/weapons/w169-rapid-hit.json': '3406dea192367d0f64406d473ab6996b5b6085dfaeb279c571209a84ec6dd8cd', 'src/main/resources/destiny/weapons/w176-stats-for-all.json': 'fbe3b8d75f696681e11e878c5a334567616351f07855fe9a07d3b211c47d3e9c', 'art/weapons/w43/extraction.json': 'a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5', 'art/weapons/w46/weapon_formulas.json': 'fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d', 'art/weapons/w46/stat_calc.rs': '5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2', 'art/weapons/w46/rs_types.rs': 'faa476e6589d2362cf9ee8dd948410adfa7fa8507e8809f3cd10bb13ebba9b90', 'art/weapons/w46/MIT-LICENSE': '50173139375c53459837abdeb7ad9f264eba4f0bc2bb2c676932991ce158778d', 'art/weapons/w46/UNLICENSE': '6b0382b16279f26ff69014300541967a356a666eb0b91b422f6862f6b7dad17e', 'inventory': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c', 'plugSets': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959', 'manifest': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce', 'clarity': '881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384'}

def require(ok, why):
    if not ok: raise ValueError(why)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def encode(x): return (json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+"\n").encode()
def eligible(index, traits, field, pool, match, exotic, perk=BASE):
    # W320 follow-up: curated fixed-roll legendaries (e.g. IKELOS) expose their trait column as a
    # reusablePlugSetHash with isFakePlugSet true; both forms are official rollable trait pools.
    randomized=field=="randomizedPlugSetHash" and pool.get("isFakePlugSet") is False
    curated=field=="reusablePlugSetHash" and pool.get("isFakePlugSet") is True
    return (not exotic and index in traits and (randomized or curated) and match.get("plugItemHash")==perk
            and match.get("currentlyCanRoll") is True)
def membership(rows):
    require(all(set(r)==set(KEYS) and all(type(r[k]) is int for k in KEYS[1:]) for r in rows),"roll schema")
    keys=[tuple(r[k] for k in KEYS) for r in rows]
    require(len(keys)==len(set(keys))==19 and set(keys)==EXPECTED,"exact19 base sockets")
def solve(c, stat):
    require(set(c)=={"evpp","vpp","offset"} and all(type(x) in (int,float) and math.isfinite(x) for x in c.values()),"finite curve")
    v=c["evpp"]*stat*stat+c["vpp"]*stat+c["offset"]
    require(math.isfinite(v) and 0<v<=60,"safe raw seconds")
    return v
def ticks(v): return max(1,math.ceil(v*20))
def evaluate(c,handling=0,reload=0,hs=1.0,rs=1.0,snapshot=False):
    require(type(handling) is int and type(reload) is int and all(math.isfinite(s) and 0<s<=1 for s in (hs,rs)),"safe total stat/scalar")
    h=min(100,max(0,c["baseHandlingStat"]+handling)); r=min(100,max(0,c["baseReloadStat"]+reload))
    ads=solve(c["ads"],h)
    if snapshot:
        require(c["snapshotScalar"] is not None,"no distinct Snapshot pair")
        ads*=c["snapshotScalar"]
    return {"readyTicks":ticks(solve(c["ready"],h)*hs),
            "stowTicks":ticks(max(solve(c["stow"],h),solve(c["stow"],100))*hs),
            "adsTicks":max(1 if snapshot else 2,min(20,ticks(ads))),
            "reloadTicks":ticks(solve(c["reload"],r)*rs)}
def validate(resource,curves,pairs):
    require(set(resource)=={"stage","perk","policies","weapons","curves","coSelections"} and resource["stage"]=="W178"
            and resource["perk"]==PERK and resource["policies"]==POLICIES,"schema/mechanics/policies")
    membership(resource["weapons"])
    require(resource["curves"]==curves and resource["coSelections"]==pairs,"pinned curves/pairs")

def generate(args):
    paths={k:args.root/k for k in PINS if "/" in k}
    paths.update(inventory=args.inventory,plugSets=args.plugsets,clarity=args.clarity,manifest=args.manifest)
    data={}; pins={}
    for key,path in paths.items():
        raw=path.read_bytes();require(digest(raw)==PINS[key],"source SHA mismatch: "+key)
        pins[key]={"sha256":digest(raw),"bytes":len(raw)}
        if path.suffix==".json": data[key]=json.loads(raw)
    prefix="src/main/resources/destiny/weapons/"
    selected=data[prefix+"w40-characteristics.json"][:]
    catalog=data[prefix+"w30.json"][:]
    for f in ("w83-exotics.json","w84-exotics.json"):
        selected += [r["characteristics"] for r in data[prefix+f]]
        catalog += [r["catalog"] for r in data[prefix+f]]
    require(len(selected)==len({r["id"] for r in selected})==len({r["bungieHash"] for r in selected})==len(catalog)==65,"selected65")
    manifest=data["manifest"]["Response"]; require(manifest["version"]==VERSION,"official version")
    suffix="e677f6ea-2a1e-48d4-a8c8-700a39a62585.json"
    for component in ("DestinyInventoryItemDefinition","DestinyPlugSetDefinition"):
        require(manifest["jsonWorldComponentContentPaths"]["en"][component]=="/common/destiny2_content/json/en/"+component+"-"+suffix,"official component version")
    inv,pools=data["inventory"],data["plugSets"]
    same={i["hash"] for i in inv.values() if i.get("displayProperties",{}).get("name")=="Threat Detector"}
    require(same=={BASE,ENHANCED},"unknown same-name trait")
    for h in same:
        d=inv[str(h)]; require(d["hash"]==h and d["itemType"]==19 and not d["redacted"] and not d["blacklisted"]
            and not d["plug"]["isDummyPlug"] and d["itemTypeDisplayName"]==("Trait" if h==BASE else "Enhanced Trait"),"trait definition")
    rows=[]; proofs=[]; scans=[]; excluded=[]
    for w in selected:
        d=inv[str(w["bungieHash"])];require(d["hash"]==w["bungieHash"] and d["itemType"]==3 and not d["redacted"] and not d["blacklisted"]
            and (d["inventory"]["tierType"]==6)==w["exotic"],"selected official item")
        if not w["exotic"]: require({k:v["value"] for k,v in d["stats"]["stats"].items()}==w["stats"],"official stats")
        s=d.get("sockets",{}); traits={n for c in s.get("socketCategories",[]) if c["socketCategoryHash"]==TRAIT for n in c["socketIndexes"]}
        scan={"id":w["id"],"hash":d["hash"],"exotic":w["exotic"],"traitIndexes":sorted(traits),"references":[]}
        for n,sock in enumerate(s.get("socketEntries",[])):
            for field in ("randomizedPlugSetHash","reusablePlugSetHash"):
                ph=sock.get(field)
                if not ph: continue
                pool=pools[str(ph)];require(pool["hash"]==ph and not pool["redacted"] and not pool["blacklisted"],"official pool")
                matches=[p for p in pool.get("reusablePlugItems",[]) if p["plugItemHash"] in same]
                scan["references"].append({"socket":n,"field":field,"plugSetHash":ph,"isFakePlugSet":pool["isFakePlugSet"],"matches":matches})
                for match in matches:
                    if eligible(n,traits,field,pool,match,w["exotic"]):
                        require(d["inventory"]["tierType"]==5,"legendary owner")
                        row=dict(zip(KEYS,(w["id"],d["hash"],n,BASE,ph)));rows.append(row)
                        proofs.append({**row,"socketEntry":sock,"socketCategoryHash":TRAIT,"matchingEntry":match})
                    else: excluded.append({"id":w["id"],"socket":n,"field":field,"plugSetHash":ph,"match":match})
        scans.append(scan)
    membership(rows)
    clarity=data["clarity"][str(BASE)]
    text="\n".join(l.get("text","") for b in clarity["descriptions"]["en"] for l in b.get("linesContent",[]))
    require(clarity["hash"]==BASE and clarity["type"]=="Weapon Trait" and all(s in text for s in
        ("1|2 Stacks while within 15 meters of 1|2+ enemies", "15|40 Stability", "18|60 Reload Speed", "25|100 Handling", "0.9x|0.81x Handling Animation Duration Multiplier")),"Clarity base mechanics")
    pairs=[]; pairAudit=[]
    for name,file in PROFILES.items():
        profile=data[prefix+file]; accepted=[]; rejected=[]
        for a in rows:
            for b in profile.get("rolls",profile.get("weapons",[])):
                if a["id"]!=b["id"]:continue
                d=inv[str(a["hash"])];s=d["sockets"]; traits={n for c in s["socketCategories"] if c["socketCategoryHash"]==TRAIT for n in c["socketIndexes"]}
                sock=s["socketEntries"][b["socket"]];ph=sock.get("randomizedPlugSetHash");pool=pools.get(str(ph),{})
                require(ph==b["plugSetHash"] and b["hash"]==a["hash"] and any(eligible(b["socket"],traits,"randomizedPlugSetHash",pool,m,False,b["perkHash"]) for m in pool.get("reusablePlugItems",[])),"official companion roll")
                if a["socket"]!=b["socket"]:
                    pairs.append({"id":a["id"],"perk":name,"roll":b});accepted.append(b)
                else: rejected.append({"roll":b,"reason":"SAME_SOCKET"})
        pairAudit.append({"perk":name,"accepted":accepted,"rejected":rejected})
    require({(p["id"],p["perk"]) for p in pairs}=={
        ("dust_rock_blues","snapshot"),("high_albedo","snapshot"),("brass_attacks","frenzy"),
        ("dream_breaker","frenzy"),("parcel_of_stardust_fell_to_earth","outlaw"),("seventh_seraph_officer_revolver","feeding_frenzy")},"review exact six companion pairs")
    mapping={m["id"]:m for m in data["art/weapons/w43/extraction.json"]["entries"]}
    formulas=data["art/weapons/w46/weapon_formulas.json"]
    byid={w["id"]:w for w in selected}
    indexed=lambda file:{r["id"]:r for r in data[prefix+file]}
    reloads,handling,aim=[indexed(f) for f in ("w46-timing.json","w58-handling.json","w44-aim.json")]
    curves=[];audit=[];cases=[]
    for row in rows:
        id=row["id"]; w=byid[id];m=mapping[id];cat=formulas[m["family"]]["cat"][m["category"]]
        c={"id":id,"baseReloadStat":w["stats"]["4188031367"],"baseHandlingStat":w["stats"]["943549884"],
           "shellReload":reloads[id]["timing"]["shellReload"],
           "snapshotScalar":(0.5 if inv[str(w["bungieHash"])]["equippingBlock"]["ammoType"]==1 else 0.8) if any(p["id"]==id and p["perk"]=="snapshot" for p in pairs) else None}
        for key,source in {"reload":cat["reload"],**cat["handling"]}.items():c[key]={k:source.get(k,0.0) for k in ("evpp","vpp","offset")}
        baseline=evaluate(c);t=reloads[id]["timing"];h=handling[id]["profile"];a=aim[id]["profile"]
        require(t["supported"] and h["supported"] and baseline=={"readyTicks":h["readyTicks"],"stowTicks":h["stowTicks"],"adsTicks":a["transitionTicks"],"reloadTicks":t["reloadPerRoundTicks"] if c["shellReload"] else t["reloadTicks"]},"reproduce W46/W58/W44 "+id)
        curves.append(c);audit.append({"id":id,"mapping":m,"baseline":baseline,"timing":t,"tiers":[evaluate(c,PERK["handlingBonus"][i],PERK["reloadBonus"][i],PERK["handlingScalar"][i]) for i in range(3)]})
        for pair in [p for p in pairs if p["id"]==id]:
            name=pair["perk"];profile=data[prefix+PROFILES[name]]
            tiers=profile["tiers"] if name=="feeding_frenzy" else [{"stacks":1,"reloadBonus":profile["perk"]["reloadBonus"],"durationMultiplier":profile["perk"]["durationMultiplier"]}] if name=="outlaw" else [{"stacks":1}]
            for i in (1,2):
                for tier in tiers:
                    hb=PERK["handlingBonus"][i]+(100 if name=="frenzy" else 0)
                    rb=PERK["reloadBonus"][i]+(100 if name=="frenzy" else tier.get("reloadBonus",0))
                    rs=tier.get("durationMultiplier",1.0)
                    cases.append({"id":id,"perk":name,"stacks":i,"companionStacks":tier["stacks"],"handlingBonus":hb,"reloadBonus":rb,
                                  "handlingScalar":PERK["handlingScalar"][i],"reloadScalar":rs,"snapshotEntering":name=="snapshot",
                                  "expected":evaluate(c,hb,rb,PERK["handlingScalar"][i],rs,name=="snapshot")})
    resource={"stage":"W178","perk":PERK,"policies":POLICIES,"weapons":rows,"curves":curves,"coSelections":pairs}
    validate(resource,curves,pairs)
    outputs={TARGET:resource,ART+"official-sockets.json":{"version":VERSION,"definitions":[{"hash":h,"accepted":h==BASE} for h in sorted(same)],"selectedCount":65,"rolls":rows,"proofs":proofs,"scans":scans,"excluded":excluded,"companionAudit":pairAudit},
             ART+"clarity-source.json":{"source":"https://github.com/Clarity-Destiny/Descriptions","cacheSha256":PINS["clarity"],"base":clarity,"enhancedExcludedHash":ENHANCED,"mechanics":PERK,"policies":POLICIES}}
    outputs[ART+"manifest.json"]={"stage":"W178","generator":SCRIPT,"generatorSha256":digest((args.root/SCRIPT).read_bytes()),"sourcePins":pins,"version":VERSION,"curveAudit":audit,"pairCases":cases,"outputs":{k:digest(encode(v)) for k,v in outputs.items()},
        "nativePending":["MASTER actualGT integration","HUD four nodes no countdown","paid recoil/bloom/flinch and no damage/range change","identity lifecycle and accepted in-flight reload timing","ready/stow and ADS entry/exit"],
        "limitations":["Current official sockets; historical community raw stat curves.","Local Minecraft footpoint sphere and project PvE enemy policy; no line-of-sight requirement in source.","Only Snapshot2/Frenzy2/Outlaw1/FeedingFrenzy1 distinct pairs. AJ/PM/RapidHit/SFA impossible in selected19.","No original first-shell delay inferred; preserve accepted base phases by unrounded ratio if distinct."]}
    return outputs

def self_test(outputs):
    r=outputs[TARGET];curves=r["curves"];pairs=r["coSelections"];n=0
    def rejects(f):
        nonlocal n
        try:f()
        except (ValueError,KeyError,TypeError):n+=1;return
        raise AssertionError("mutation unexpectedly accepted")
    for key,value in [("weapons",r["weapons"][:-1]),("weapons",r["weapons"]+[r["weapons"][0]]),("policies",{}),("perk",dict(PERK,radius=16)),("curves",[]),("coSelections",[])]:
        x=copy.deepcopy(r);x[key]=value;rejects(lambda:validate(x,curves,pairs))
    for key,value in [("perkHash",ENHANCED),("socket",4),("hash",1),("plugSetHash",1)]:
        x=copy.deepcopy(r);x["weapons"][0][key]=value;rejects(lambda:validate(x,curves,pairs))
    pool={"isFakePlugSet":False};match={"plugItemHash":BASE,"currentlyCanRoll":True}
    require(eligible(3,{3},"randomizedPlugSetHash",pool,match,False),"positive roll predicate")
    for args in [(4,{3},"randomizedPlugSetHash",pool,match,False),(3,{3},"reusablePlugSetHash",pool,match,False),(3,{3},"randomizedPlugSetHash",{"isFakePlugSet":True},match,False),(3,{3},"randomizedPlugSetHash",pool,dict(match,currentlyCanRoll=False),False),(3,{3},"randomizedPlugSetHash",pool,dict(match,plugItemHash=ENHANCED),False),(3,{3},"randomizedPlugSetHash",pool,match,True)]:
        require(not eligible(*args),"negative predicate");n+=1
    for c in curves:
        for i in (1,2):
            x=evaluate(c,PERK["handlingBonus"][i],PERK["reloadBonus"][i],PERK["handlingScalar"][i]);b=evaluate(c)
            require(all(x[k]<=b[k] for k in x),"buff monotonic")
        for bad in (float("nan"),float("inf"),0,-1,1.1):rejects(lambda:evaluate(c,hs=bad))
        require(evaluate(c,2**31-1,2**31-1)==evaluate(c,100,100),"wide capped stat")
    return n

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--inventory",type=Path,default=Path("/tmp/destiny-weapons-w30/bungie-items.json"))
    p.add_argument("--plugsets",type=Path,default=Path("/tmp/destiny-weapons-w60/bungie-plugsets.json"))
    p.add_argument("--manifest",type=Path,default=Path("/tmp/destiny-weapons-w60/manifest.json"))
    p.add_argument("--clarity",type=Path,default=Path("/private/tmp/w167-clarity.json"))
    p.add_argument("--verify",action="store_true");p.add_argument("--self-test",action="store_true");a=p.parse_args()
    outputs=generate(a)
    if a.self_test:
        n=self_test(outputs);require({k:encode(v) for k,v in generate(a).items()}=={k:encode(v) for k,v in outputs.items()},"repeat deterministic");print("negative checks",n,"deterministic repeat PASS")
    for name,value in outputs.items():
        dest=a.root/name;raw=encode(value)
        if a.verify:require(dest.read_bytes()==raw,"generated drift: "+name)
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    print("W178 exact19, selected65, six distinct pairs, four outputs", "VERIFIED" if a.verify else "GENERATED")
if __name__=="__main__":main()
