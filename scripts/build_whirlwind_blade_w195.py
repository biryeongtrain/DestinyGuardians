"""W195 exact base Trait pools and pinned DDC evidence; no network input."""
import argparse, hashlib, html, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CONFIG = {'id': 'whirlwind_blade', 'slug': 'whirlwind-blade', 'name': 'Whirlwind Blade', 'hash': 3913600130, 'enhanced': 147913470, 'row': 248, 'mechanics': {'step': 0.03, 'maxStacks': 10, 'durationTicks': 70}, 'expected': [{'id': 'abide_the_return', 'hash': 1644160541, 'socket': 4, 'perkHash': 3913600130, 'plugSetHash': 2761485963}, {'id': 'goldtusk', 'hash': 3371413057, 'socket': 4, 'perkHash': 3913600130, 'plugSetHash': 700250835}, {'id': 'crown_splitter', 'hash': 2782325302, 'socket': 4, 'perkHash': 3913600130, 'plugSetHash': 99092784}, {'id': 'falling_guillotine', 'hash': 614426548, 'socket': 4, 'perkHash': 3913600130, 'plugSetHash': 66521752}, {'id': 'temptation_s_hook', 'hash': 35794111, 'socket': 4, 'perkHash': 3913600130, 'plugSetHash': 2147541212}], 'mapping': 'Confirmed base DDC: powered sword positive-loss contacts add stacks, 3% each up to ten, 3.5 seconds = 70 ticks; refresh on additional contacts. Actual blocking/stow resets live stacks. Paid snapshot remains fixed; source lifecycle revokes it.', 'note': '# W195 Whirlwind Blade\n\nDDC Weapon Perks row 248; raw row and yellow enhanced markup retained in source.json.\nConfirmed base DDC: powered sword positive-loss contacts add stacks, 3% each up to ten, 3.5 seconds = 70 ticks; refresh on additional contacts. Actual blocking/stow resets live stacks. Paid snapshot remains fixed; source lifecycle revokes it.\n\nAll 65 canonical entries scanned against pinned official inventory and actual randomized\nplug sets. Require isFakePlugSet=false, currentlyCanRoll=true, exact base Trait.\nRuntime tuples are unique; raw matching pool entries remain in socketProofs.\nEnhanced/exotic unsupported; no default selections. No shared integration files owned.\n\nIntegration:\n- Register WhirlwindBladeProfile in master-owned WeaponPerks; no trait selected by default.\n- WeaponWhirlwindBlade.update(p) on server tick. EnGarde.update also BEFORE swordAttack,\n  after the actual held source can be observed and WeaponHandling.blocked is false.\n- capture(p) only AFTER payment for nonempty powered sword contact, BEFORE damage.\n  One exact Token across cleave/direct/splash; never fresh capture at explosion.\n- multiplier(p, token) is pure and frozen; remaining(p) is pure.\n- Whirlwind additionally stacks(p), confirmed(p,token,target,actualLoss) AFTER actual\n  positive damage, blocking(p,stack) only when actual guard becomes active.\n- stowing(p,outgoing) BEFORE selection changes, including same-tick away/back.\n- edited(stack)/changed(p,stack) revoke same-tick old tokens. For EnGarde,\n  source edits retain incoming readiness consumption and cannot rearm.\n- cleanup(p) for lifecycle; clear() on server stop. Old-owner cleanup cannot remove successor.\n- master excludes empty sword/glaive contacts, validates attributable enemy targets,\n  and owns shared Runtime/Handling/registry/damage integration.\n\nOnly focused pure cycle tests and standalone compile are in scope. No native/server QA,\nno broad gate, no numeric mirror tests, no model/animation work.\n'}
PINS = {'/tmp/destiny-weapons-w30/bungie-items.json': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c', '/tmp/destiny-weapons-w60/bungie-plugsets.json': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959', '/tmp/destiny-weapons-w60/manifest.json': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce', '/private/tmp/destiny-w190/ddc-perks.html': '8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437', 'src/main/resources/destiny/weapons/w30.json': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a', 'src/main/resources/destiny/weapons/w40-characteristics.json': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1', 'src/main/resources/destiny/weapons/w83-exotics.json': 'bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56', 'src/main/resources/destiny/weapons/w84-exotics.json': '481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e'}
def require(ok, why):
    if not ok: raise ValueError(why)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def encode(value): return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n").encode()
def plain(raw): return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())
def build(root):
    data, inputs = {}, {}
    for name, sha in PINS.items():
        raw = (root / name).read_bytes()
        require(digest(raw) == sha, "Pinned input drift: " + name)
        data[name] = json.loads(raw) if name.endswith(".json") else raw.decode()
        inputs[name] = dict(sha256=sha, bytes=len(raw))
    c=CONFIG
    inventory=data["/tmp/destiny-weapons-w30/bungie-items.json"]
    pools=data["/tmp/destiny-weapons-w60/bungie-plugsets.json"]
    manifest=data["/tmp/destiny-weapons-w60/manifest.json"]["Response"]
    require(manifest["version"]=="245114.26.10.13.2000-1-bnet.66137", "manifest version")
    perk=inventory[str(c["hash"])]
    require(perk["displayProperties"]["name"]==c["name"] and perk["hash"]==c["hash"]
        and perk["itemTypeDisplayName"]=="Trait" and perk["itemType"]==19
        and perk["plug"]["isDummyPlug"] is False and not perk.get("redacted")
        and not perk.get("blacklisted"), "exact usable base Trait")
    require(inventory[str(c["enhanced"])]["itemTypeDisplayName"]=="Enhanced Trait", "enhanced excluded")
    rows=[r for r in re.findall(r"<tr\b[^>]*>.*?</tr>",data["/private/tmp/destiny-w190/ddc-perks.html"],re.S)
          if any(plain(cell)==c["name"] for cell in re.findall(r"<td\b[^>]*>(.*?)</td>",r,re.S))]
    require(len(rows)==1 and 'id="1662574278R'+str(c["row"]-1)+'"' in rows[0], "exact DDC row")
    rawrow=rows[0]; text=plain(re.findall(r"<td\b[^>]*>(.*?)</td>",rawrow,re.S)[-1])
    require("#ffd966" in rawrow, "yellow enhanced raw distinction")
    required=["3.5","Powered Sword","Blocking or stowing"] if c["row"]==248 else ["30%","1.5","2?","after the buff is removed"]
    require(all(s in text for s in required), "DDC text")
    prefix="src/main/resources/destiny/weapons/"
    stats=list(data[prefix+"w40-characteristics.json"]); catalog=list(data[prefix+"w30.json"])
    for name in ("w83-exotics.json","w84-exotics.json"):
        stats.extend(x["characteristics"] for x in data[prefix+name])
        catalog.extend(x["catalog"] for x in data[prefix+name])
    require(len(stats)==len(catalog)==len({w["id"] for w in stats})==65, "canonical65")
    require({w["id"] for w in stats}=={w["id"] for w in catalog},"canonical identity")
    found=[]; scan=[]; proofs=[]
    for weapon in stats:
        item=inventory[str(weapon["bungieHash"])]; sockets=item["sockets"]; matches=[]
        categories=[x for x in sockets["socketCategories"] if x["socketCategoryHash"]==4241085061]
        for index in sorted({i for cat in categories for i in cat["socketIndexes"]}):
            socket=sockets["socketEntries"][index]; ph=socket.get("randomizedPlugSetHash")
            pool=pools.get(str(ph),{})
            if pool.get("isFakePlugSet") is not False: continue
            for plug in pool.get("reusablePlugItems",[]):
                definition=inventory.get(str(plug["plugItemHash"]),{})
                if plug.get("currentlyCanRoll") is not True or definition.get("itemTypeDisplayName")!="Trait" or plug["plugItemHash"]!=c["hash"]: continue
                require(not weapon["exotic"] and item["inventory"]["tierType"]==5 and next(w for w in catalog if w["id"]==weapon["id"])["family"]=="sword","legendary sword")
                roll=dict(id=weapon["id"],hash=weapon["bungieHash"],socket=index,perkHash=c["hash"],plugSetHash=ph)
                if roll not in found: found.append(roll)
                matches.append(roll)
                proofs.append(dict(roll=roll,socketCategories=categories,socketEntry=socket,plugSet=pool,matchingPlug=plug))
        scan.append(dict(id=weapon["id"],hash=weapon["bungieHash"],exotic=weapon["exotic"],matches=matches))
    require(found==c["expected"],"exact exhaustive actual pool")
    resource=dict(stage="W195",perk=dict(id=c["id"],hash=c["hash"],**c["mechanics"]),weapons=found)
    raw=encode(resource)
    source=dict(stage="W195",checked="2026-10-27",manifestVersion=manifest["version"],
        sourcePins=inputs,generatorSHA256=digest(Path(__file__).read_bytes()),
        manifestComponents={k:manifest["jsonWorldComponentContentPaths"]["en"][k] for k in ("DestinyInventoryItemDefinition","DestinyPlugSetDefinition")},
        perkDefinition=perk,enhancedExcludedHash=c["enhanced"],ddc=dict(tab="Weapon Perks",row=c["row"],rawHTML=rawrow,text=text,
        url="https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278"),
        catalogScan=scan,socketProofs=proofs,uniquePoolCount=len(found),rawMatchingPlugCount=len(proofs),resourceSHA256=digest(raw),
        mapping=c["mapping"])
    return {prefix+"w195-"+c["slug"]+".json":raw,
        "art/weapons/w195/"+c["slug"]+"/source.json":encode(source),
        "art/weapons/w195/"+c["slug"]+"/SOURCE.md":c["note"].encode()}
def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--root",type=Path,default=ROOT); parser.add_argument("--verify",action="store_true")
    args=parser.parse_args()
    for name,raw in build(args.root.resolve()).items():
        path=args.root/name
        if args.verify: require(path.read_bytes()==raw,"Generated output drift: "+name)
        else: path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)
        print(("verified " if args.verify else "wrote ")+name)
if __name__=="__main__": main()
