#!/usr/bin/env python3
"""Reproduce exact base Quickdraw official sockets and historical raw handling curves.
Writes only five assigned JSON files. --verify is read-only. No game, Gradle or media.
"""
import argparse, copy, csv, hashlib, json, math, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASE, ENHANCED, TRAIT = 706527188, 1961144892, 4241085061
KEYS = ("id", "hash", "socket", "perkHash", "plugSetHash")
ART = "art/weapons/w185/quickdraw/"
TARGET = "src/main/resources/destiny/weapons/w185-quickdraw.json"
SCRIPT = "scripts/build_quickdraw_profile_w185.py"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
PERK = {"id":"quickdraw","hash":BASE,"handling":100,"durationTicks":20,"readyScalar":0.95}
PINS = {'src/main/resources/destiny/weapons/w30.json': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a', 'src/main/resources/destiny/weapons/w40-characteristics.json': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1', 'src/main/resources/destiny/weapons/w58-handling.json': '4de7d346a93c822784fafa69b62ac66148d51cc11cf2da6706367682b414d3f1', 'src/main/resources/destiny/weapons/w83-exotics.json': 'bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56', 'src/main/resources/destiny/weapons/w84-exotics.json': '481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e', 'art/weapons/w43/extraction.json': 'a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5', 'art/weapons/w46/weapon_formulas.json': 'fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d', 'art/weapons/w46/stat_calc.rs': '5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2', 'art/weapons/w46/rs_types.rs': 'faa476e6589d2362cf9ee8dd948410adfa7fa8507e8809f3cd10bb13ebba9b90', 'art/weapons/w46/MIT-LICENSE': '50173139375c53459837abdeb7ad9f264eba4f0bc2bb2c676932991ce158778d', 'art/weapons/w46/UNLICENSE': '6b0382b16279f26ff69014300541967a356a666eb0b91b422f6862f6b7dad17e', 'src/main/resources/destiny/weapons/w109-surrounded.json': '799f763f0f0882eec7b3a172592fdeb3f95e8fca1a95149274f3db82fac6f777', 'src/main/resources/destiny/weapons/w77-dragonfly.json': '239e4fa48afebebd20ed765fc05b3e61bb34532bffea3a8cffdc536c867eab06', 'src/main/resources/destiny/weapons/w170-perpetual-motion.json': 'e4155158bf1692797a3f1c1b0e49d80360c5494173b384a738c3a337fe47275f', 'src/main/resources/destiny/weapons/w165-multikill-clip.json': 'f878e4d5c699bdc8d77fc8b86ee653caf8cb4dc4532c641b27d5f3c3be94f593', 'src/main/resources/destiny/weapons/w73-archers-tempo.json': '19a3f2d275846b512a62b9f4d090765f9c8efc35096ba77c823d509420708c85', 'src/main/resources/destiny/weapons/w103-demolitionist.json': 'b7aa18096002f5a9a66892027c6fb57295e3a09864ff52a1f889d6f732c10905', 'src/main/resources/destiny/weapons/w172-frenzy.json': '28a3722a9ea57dc7400a68ddcee80f6c661bf23a1abd0f4dc92dec9065120862', 'src/main/resources/destiny/weapons/w177-heating-up.json': '2a6995836e7aaecd7a7e2ce1af519e0fa34597998e59ad5ccf6483b5ebc44098', 'src/main/resources/destiny/weapons/w178-threat-detector.json': '8e593a1698dff17bb8260e40b9b1e3befe3efaca9fd54d990e89fdddf62cb4e4', 'src/main/resources/destiny/weapons/w109-one-for-all.json': '65c25d83386071571beb012122f7d4834194812713152863575300537a881613', 'src/main/resources/destiny/weapons/w66-rampage.json': 'd03a2518629ce36aac140837f92950083c1a546c14f6cd5ff3310cac1f08f6e0', 'src/main/resources/destiny/weapons/w80-payload.json': '000fef1ccea2cdc653f723be8d8eeefb209255673dcc8189b3732c69173a03fc', 'src/main/resources/destiny/weapons/w174-focused-fury.json': 'bf8604f8758cf698b3d4307d682db54a98ba8afd0631855b8d253d53ca02d60c', 'src/main/resources/destiny/weapons/w61-kill-clip.json': 'fb3374e775b9313619f34c1dda5681d391577c15279aa140f9fdc59b2d2ebd9a', 'src/main/resources/destiny/weapons/w173-adrenaline-junkie.json': 'b2c0d5865d9d72f9ee4d1bd3439d940d52574d7d7539604a9b4fe1e82c3fbf65', 'src/main/resources/destiny/weapons/w169-rapid-hit.json': '3406dea192367d0f64406d473ab6996b5b6085dfaeb279c571209a84ec6dd8cd', 'src/main/resources/destiny/weapons/w104-tracking.json': 'c4ecf3805a1cc7c6529565f899cc45efbb811bf07c743558a40c76aadd3e789e', 'src/main/resources/destiny/weapons/w167-subsistence.json': 'abe5e37fb0632fb9da5a65f803b33349337d686523d4eef054bcb10742dc0835', 'src/main/resources/destiny/weapons/w183-surplus.json': '3a54d901e618b2472c8a2beff905ecb21d9aa0316628a0416adaf91242fccef6', 'src/main/resources/destiny/weapons/w68-snapshot.json': '7e824633be32953e6c75d3d856ce765223fbb1cbcc3b01affca3d83eb8fcb738', 'src/main/resources/destiny/weapons/w182-high_impact_reserves.json': '0f428969fd69b7cc874171f875a963af9eac27a30974d111189ad7754626d5e1', 'src/main/resources/destiny/weapons/w171-tap-the-trigger.json': '94d8fb588f44eff1dd41c056fadd555d37c7266116e0c10311df906fd0bbd7e9', 'src/main/resources/destiny/weapons/w184-elemental_capacitor.json': '254c688e41275e59e153238523a36e22a6b107945c0c8a48ed0ef0966fa5ff1c', 'src/main/resources/destiny/weapons/w176-stats-for-all.json': 'fbe3b8d75f696681e11e878c5a334567616351f07855fe9a07d3b211c47d3e9c', 'src/main/resources/destiny/weapons/w110-grave-robber.json': 'd8746295ed704fa6d5db254247baf000228655924629a3fd4cc4b067cd9a759b', 'src/main/resources/destiny/weapons/w181-vorpal.json': '221b1ba84382272dbc679684a9885e9cee8399ef98714a76f113bdbdd930d76e', 'src/main/resources/destiny/weapons/w108-feeding-frenzy.json': '1ffbff575f0a29adc5a749d581f31c2f6dd67dfea20cf4a3484b6d2c1c522ce8', 'src/main/resources/destiny/weapons/w110-swashbuckler.json': '0315293d63b74a8fd224772832dea879851151a6ec34998d47d268d170eec7b6', 'src/main/resources/destiny/weapons/w60-holster.json': '78411445e481200481389df552b293be36a03643d753be9372ebb974cec953b6', 'src/main/resources/destiny/weapons/w62-outlaw.json': '5188d73a271b0a5080eb99d47c50a6d37ccae11fe756ebd2893c70499f3637bc', 'inventory': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c', 'plugSets': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959', 'manifest': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce', 'clarity': '881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384', 'ddc': '7880b2029a7e7b8f97afb8f079ca48a585ec0765a94b6b3f983a47daf983ba30'}
PROFILES = {'surrounded': 'src/main/resources/destiny/weapons/w109-surrounded.json', 'dragonfly': 'src/main/resources/destiny/weapons/w77-dragonfly.json', 'perpetual_motion': 'src/main/resources/destiny/weapons/w170-perpetual-motion.json', 'multikill_clip': 'src/main/resources/destiny/weapons/w165-multikill-clip.json', 'archers_tempo': 'src/main/resources/destiny/weapons/w73-archers-tempo.json', 'demolitionist': 'src/main/resources/destiny/weapons/w103-demolitionist.json', 'frenzy': 'src/main/resources/destiny/weapons/w172-frenzy.json', 'heating_up': 'src/main/resources/destiny/weapons/w177-heating-up.json', 'threat_detector': 'src/main/resources/destiny/weapons/w178-threat-detector.json', 'one_for_all': 'src/main/resources/destiny/weapons/w109-one-for-all.json', 'rampage': 'src/main/resources/destiny/weapons/w66-rampage.json', 'explosive_payload': 'src/main/resources/destiny/weapons/w80-payload.json', 'focused_fury': 'src/main/resources/destiny/weapons/w174-focused-fury.json', 'kill_clip': 'src/main/resources/destiny/weapons/w61-kill-clip.json', 'adrenaline_junkie': 'src/main/resources/destiny/weapons/w173-adrenaline-junkie.json', 'rapid_hit': 'src/main/resources/destiny/weapons/w169-rapid-hit.json', 'tracking_module': 'src/main/resources/destiny/weapons/w104-tracking.json', 'subsistence': 'src/main/resources/destiny/weapons/w167-subsistence.json', 'surplus': 'src/main/resources/destiny/weapons/w183-surplus.json', 'snapshot': 'src/main/resources/destiny/weapons/w68-snapshot.json', 'high_impact_reserves': 'src/main/resources/destiny/weapons/w182-high_impact_reserves.json', 'tap_the_trigger': 'src/main/resources/destiny/weapons/w171-tap-the-trigger.json', 'elemental_capacitor': 'src/main/resources/destiny/weapons/w184-elemental_capacitor.json', 'stats_for_all': 'src/main/resources/destiny/weapons/w176-stats-for-all.json', 'grave_robber': 'src/main/resources/destiny/weapons/w110-grave-robber.json', 'vorpal_weapon': 'src/main/resources/destiny/weapons/w181-vorpal.json', 'feeding_frenzy': 'src/main/resources/destiny/weapons/w108-feeding-frenzy.json', 'swashbuckler': 'src/main/resources/destiny/weapons/w110-swashbuckler.json', 'auto_loading_holster': 'src/main/resources/destiny/weapons/w60-holster.json', 'outlaw': 'src/main/resources/destiny/weapons/w62-outlaw.json'}
EXPECTED = [{'id': 'blast_furnace', 'hash': 3843477312, 'socket': 3, 'perkHash': 706527188, 'plugSetHash': 1976101165}, {'id': 'dead_man_walking_xx7463', 'hash': 3751622019, 'socket': 3, 'perkHash': 706527188, 'plugSetHash': 3268663985}, {'id': 'biting_winds', 'hash': 1621657423, 'socket': 3, 'perkHash': 706527188, 'plugSetHash': 3968704963}, {'id': 'whispering_slab', 'hash': 211938782, 'socket': 3, 'perkHash': 706527188, 'plugSetHash': 1885424927}, {'id': 'beloved', 'hash': 3107853529, 'socket': 4, 'perkHash': 706527188, 'plugSetHash': 887157889}, {'id': 'apostate', 'hash': 2164448701, 'socket': 4, 'perkHash': 706527188, 'plugSetHash': 2826016044}, {'id': 'parcel_of_stardust_fell_to_earth', 'hash': 2217366863, 'socket': 4, 'perkHash': 706527188, 'plugSetHash': 3424940310}, {'id': 'hollow_words', 'hash': 607191995, 'socket': 3, 'perkHash': 706527188, 'plugSetHash': 637298592}, {'id': 'dream_breaker', 'hash': 2931957300, 'socket': 4, 'perkHash': 706527188, 'plugSetHash': 1206254527}, {'id': 'edge_transit', 'hash': 218335759, 'socket': 4, 'perkHash': 706527188, 'plugSetHash': 2535579724}, {'id': 'bad_omens', 'hash': 991314988, 'socket': 4, 'perkHash': 706527188, 'plugSetHash': 2955928741}, {'id': 'bellowing_giant', 'hash': 2186258845, 'socket': 3, 'perkHash': 706527188, 'plugSetHash': 2605036073}, {'id': 'code_duello', 'hash': 2496242052, 'socket': 3, 'perkHash': 706527188, 'plugSetHash': 3719628667}, {'id': 'pyroclastic_flow', 'hash': 1289324202, 'socket': 3, 'perkHash': 706527188, 'plugSetHash': 528513254}, {'id': 'fixed_odds', 'hash': 2194955522, 'socket': 3, 'perkHash': 706527188, 'plugSetHash': 4227334000}, {'id': 'hammerhead', 'hash': 603242241, 'socket': 3, 'perkHash': 706527188, 'plugSetHash': 2515290473}]

def require(ok, why):
    if not ok: raise ValueError(why)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def encode(x): return (json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+"\n").encode()
def eligible(index,traits,field,pool,match,exotic,perk=BASE):
    return (not exotic and index in traits and field=="randomizedPlugSetHash"
        and pool.get("isFakePlugSet") is False and match.get("plugItemHash")==perk
        and match.get("currentlyCanRoll") is True)
def membership(rows):
    require(all(set(r)==set(KEYS) and isinstance(r['id'],str) and all(type(r[k]) is int for k in KEYS[1:]) for r in rows),"roll schema")
    tuples=[tuple(r[k] for k in KEYS) for r in rows]
    require(len(tuples)==len(set(tuples))==16 and set(tuples)=={tuple(r[k] for k in KEYS) for r in EXPECTED},"exact16 base sockets")
def solve(c,stat):
    require(set(c)=={'evpp','vpp','offset'} and all(type(v) in (int,float) and math.isfinite(v) for v in c.values()),'finite curve')
    value=c['evpp']*stat*stat+c['vpp']*stat+c['offset']
    require(math.isfinite(value) and 0<value<=60,'safe raw seconds')
    return value
def evaluate(c,scalar=1,active=True):
    require(type(scalar) in (float,int) and math.isfinite(scalar) and scalar in (1,.9,.81),'only sourced TD scalars')
    h=100 if active else c['baseHandlingStat']
    return {'readyTicks':max(1,math.ceil(solve(c['ready'],h)*scalar*(.95 if active else 1)*20)),
        'stowTicks':max(1,math.ceil(max(solve(c['stow'],h),solve(c['stow'],100))*scalar*20))}
def validate(resource,curves,pairs):
    require(set(resource)=={'stage','perk','weapons','curves','coSelections'} and resource['stage']=='W185' and resource['perk']==PERK,'schema/mechanics')
    membership(resource['weapons'])
    require(resource['curves']==curves and resource['coSelections']==pairs,'pinned curves/pairs')

def generate(args):
    paths={k:args.root/k for k in PINS if '/' in k}
    paths.update(inventory=args.inventory,plugSets=args.plugsets,manifest=args.manifest,clarity=args.clarity,ddc=args.ddc)
    data={};pins={}
    for key,path in paths.items():
        raw=path.read_bytes();require(digest(raw)==PINS[key],'source SHA mismatch: '+key)
        pins[key]={'sha256':digest(raw),'bytes':len(raw)}
        if path.suffix=='.json':data[key]=json.loads(raw)
    prefix='src/main/resources/destiny/weapons/'
    selected=data[prefix+'w40-characteristics.json'][:]
    for f in ('w83-exotics.json','w84-exotics.json'):selected += [r['characteristics'] for r in data[prefix+f]]
    require(len(selected)==len({r['id'] for r in selected})==len({r['bungieHash'] for r in selected})==65,'selected65')
    manifest=data['manifest']['Response'];require(manifest['version']==VERSION,'official version')
    for component in ('DestinyInventoryItemDefinition','DestinyPlugSetDefinition'):
        require(manifest['jsonWorldComponentContentPaths']['en'][component]=='/common/destiny2_content/json/en/'+component+'-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json','component version')
    inv,pools=data['inventory'],data['plugSets']
    same={d['hash'] for d in inv.values() if d.get('displayProperties',{}).get('name')=='Quickdraw'}
    require(same=={BASE,ENHANCED},'same-name variants')
    for h in same:
        d=inv[str(h)];require(d['hash']==h and d['itemType']==19 and not d['redacted'] and not d['blacklisted'] and not d['plug']['isDummyPlug'] and d['itemTypeDisplayName']==('Trait' if h==BASE else 'Enhanced Trait'),'trait definition')
    rows=[];proofs=[];scans=[];excluded=[]
    for w in selected:
        d=inv[str(w['bungieHash'])];require(d['hash']==w['bungieHash'] and d['itemType']==3 and not d['redacted'] and not d['blacklisted'] and (d['inventory']['tierType']==6)==w['exotic'],'official weapon')
        if not w['exotic']:require({k:v['value'] for k,v in d['stats']['stats'].items()}==w['stats'],'official stats')
        s=d.get('sockets',{});traits={n for c in s.get('socketCategories',[]) if c['socketCategoryHash']==TRAIT for n in c['socketIndexes']}
        scan={'id':w['id'],'hash':d['hash'],'exotic':w['exotic'],'traitIndexes':sorted(traits),'references':[]}
        for n,sock in enumerate(s.get('socketEntries',[])):
            for field in ('randomizedPlugSetHash','reusablePlugSetHash'):
                ph=sock.get(field)
                if not ph:continue
                pool=pools[str(ph)];require(pool['hash']==ph and not pool['redacted'] and not pool['blacklisted'],'official pool')
                matches=[m for m in pool.get('reusablePlugItems',[]) if m['plugItemHash'] in same]
                scan['references'].append({'socket':n,'field':field,'plugSetHash':ph,'isFakePlugSet':pool['isFakePlugSet'],'matches':matches})
                for m in matches:
                    if eligible(n,traits,field,pool,m,w['exotic']):
                        require(d['inventory']['tierType']==5,'legendary')
                        row=dict(zip(KEYS,(w['id'],d['hash'],n,BASE,ph)))
                        # Apostate repeats the same base plug in this official pool; keep both proofs, one roll.
                        if row not in rows:rows.append(row)
                        proofs.append({**row,'socketEntry':sock,'socketCategoryHash':TRAIT,'matchingEntry':m})
                    else:excluded.append({'id':w['id'],'socket':n,'field':field,'plugSetHash':ph,'match':m})
        scans.append(scan)
    membership(rows)
    clarity=data['clarity'][str(BASE)]
    text='\n'.join(l.get('text','') for b in clarity['descriptions']['en'] for l in b.get('linesContent',[]))
    require(clarity['hash']==BASE and clarity['type']=='Weapon Trait' and all(s in text for s in ('100 Ready/Stow Handling','0.95x Ready Animation Duration Multiplier','1 second','ADS input is pressed')),'Clarity mechanics')
    ddc=[r for r in csv.reader(args.ddc.read_text().splitlines()) if r and r[0]=='Quickdraw']
    require(len(ddc)==1 and all(s in ddc[0][2].split('↑')[0] for s in ('100 Ready/Stow Handling','0.95x Ready Animation Duration Multiplier','1 second, or until ADS')),'DDC base mechanics')
    pairs=[];audit=[]
    for name,file in PROFILES.items():
        profile=data[file];accepted=[];rejected=[]
        for a in rows:
            for b in profile.get('rolls',profile.get('weapons',[])):
                if b.get('id')!=a['id']:continue
                b={k:b[k] for k in KEYS}
                d=inv[str(a['hash'])];s=d['sockets'];traits={n for c in s['socketCategories'] if c['socketCategoryHash']==TRAIT for n in c['socketIndexes']}
                sock=s['socketEntries'][b['socket']];ph=sock.get('randomizedPlugSetHash');pool=pools.get(str(ph),{})
                require(ph==b['plugSetHash'] and b['hash']==a['hash'] and any(eligible(b['socket'],traits,'randomizedPlugSetHash',pool,m,False,b['perkHash']) for m in pool.get('reusablePlugItems',[])),'official companion '+name)
                if a['socket']!=b['socket']:pairs.append({'id':a['id'],'perk':name,'roll':b});accepted.append(b)
                else:rejected.append({'roll':b,'reason':'SAME_SOCKET'})
        audit.append({'perk':name,'accepted':accepted,'rejected':rejected})
    td={p['id'] for p in pairs if p['perk']=='threat_detector'}
    require(td=={'parcel_of_stardust_fell_to_earth','dream_breaker','edge_transit','bellowing_giant'},'exact TD scalar pairs')
    scalarNames={'threat_detector','frenzy','surplus','perpetual_motion','adrenaline_junkie','stats_for_all','elemental_capacitor'}
    require({p['perk'] for p in pairs if p['perk'] in scalarNames}=={'threat_detector','frenzy','surplus'},'implemented handling companions')
    mapping={m['id']:m for m in data['art/weapons/w43/extraction.json']['entries']}
    formulas=data['art/weapons/w46/weapon_formulas.json'];byid={w['id']:w for w in selected}
    handling={w['id']:w['profile'] for w in data[prefix+'w58-handling.json']}
    curves=[];cases=[];curveAudit=[]
    for row in rows:
        id=row['id'];w=byid[id];m=mapping[id];cat=formulas[m['family']]['cat'][m['category']]
        c={'id':id,'baseHandlingStat':w['stats']['943549884']}
        for key in ('ready','stow'):c[key]={k:cat['handling'][key].get(k,0.0) for k in ('evpp','vpp','offset')}
        base=evaluate(c,active=False);h=handling[id]
        require(h['supported'] and base=={'readyTicks':h['readyTicks'],'stowTicks':h['stowTicks']},'W58 baseline '+id)
        curves.append(c);curveAudit.append({'id':id,'mapping':m,'baseline':base,'active':evaluate(c)})
        for scalar in ((1,.9,.81) if id in td else (1,)):
            cases.append({'id':id,'scalar':scalar,'expected':evaluate(c,scalar)})
    resource={'stage':'W185','perk':PERK,'weapons':rows,'curves':curves,'coSelections':pairs};validate(resource,curves,pairs)
    outputs={TARGET:resource,ART+'official-sockets.json':{'version':VERSION,'selectedCount':65,'definitions':[{'hash':h,'accepted':h==BASE} for h in sorted(same)],'rolls':rows,'proofs':proofs,'scans':scans,'excluded':excluded,'companionAudit':audit,'officialCompanionPools':[{'id':r['id'],'socket':n,'socketEntry':sock,'pool':pools[str(sock['randomizedPlugSetHash'])]} for r in rows for n,sock in enumerate(inv[str(r['hash'])]['sockets']['socketEntries']) if sock.get('randomizedPlugSetHash') and n in {i for cat in inv[str(r['hash'])]['sockets']['socketCategories'] if cat['socketCategoryHash']==TRAIT for i in cat['socketIndexes']}]},
        ART+'clarity-source.json':{'source':'https://github.com/Database-Clarity/Live-Clarity-Database/blob/live/descriptions/clarity.json','ddcSource':'https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278','cacheSha256':PINS['clarity'],'base':clarity,'ddcSha256':PINS['ddc'],'ddcRow':ddc[0],'enhancedExcludedHash':ENHANCED,'mechanics':PERK,'enhancedOnlyNotation':'DDC upward arrow marks enhanced +5 handling; excluded from base'},
        ART+'curves.json':{'curves':curves,'curveAudit':curveAudit,'cases':cases}}
    outputs[ART+'manifest.json']={'stage':'W185','generator':SCRIPT,'generatorSha256':digest((args.root/SCRIPT).read_bytes()),'sourcePins':pins,'version':VERSION,'outputs':{k:digest(encode(v)) for k,v in outputs.items()},'selectedCount':65,'baseRollCount':len(rows),'coSelectionCount':len(pairs),'scalarCompanion':'threat_detector only; .9/.81; four distinct socket pairs','nativePending':['master actualGT and native ADS/selection/lifecycle','shared hooks/registry/debug integration'],'limitations':['Historical d2foundry oracle dcd0c7d302b056ffbb532edcb711d724a17ca8c1 raw curves; not new current sandbox measurement','No invented HUD, ADS, reload, damage, stability or ammo bonus']}
    return outputs,resource,curves,pairs

def self_test(resource,curves,pairs):
    count=0
    def reject(fn):
        nonlocal count
        try:fn()
        except (ValueError,KeyError,TypeError):count+=1;return
        raise AssertionError('negative accepted')
    for mode in ('missing','duplicate','enhanced','socket','pool','hash','perk','curve','pair'):
        b=copy.deepcopy(resource)
        if mode=='missing':b['weapons'].pop()
        elif mode=='duplicate':b['weapons'].append(b['weapons'][0])
        elif mode=='enhanced':b['weapons'][0]['perkHash']=ENHANCED
        elif mode in ('socket','pool','hash'):b['weapons'][0][{'pool':'plugSetHash'}.get(mode,mode)]+=1
        elif mode=='perk':b['perk']['readyScalar']=.94
        elif mode=='curve':b['curves'][0]['ready']['offset']+=.01
        else:b['coSelections'].pop()
        reject(lambda:validate(b,curves,pairs))
    for scalar in (float('nan'),float('inf'),0,-1,1.1,.8):reject(lambda:evaluate(curves[0],scalar))
    good={'plugItemHash':BASE,'currentlyCanRoll':True};pool={'isFakePlugSet':False}
    require(eligible(3,{3},'randomizedPlugSetHash',pool,good,False),'positive predicate')
    negatives=[(3,{3},'reusablePlugSetHash',pool,good,False),(3,{4},'randomizedPlugSetHash',pool,good,False),(3,{3},'randomizedPlugSetHash',{'isFakePlugSet':True},good,False),(3,{3},'randomizedPlugSetHash',pool,good,True),(3,{3},'randomizedPlugSetHash',pool,{'plugItemHash':BASE,'currentlyCanRoll':False},False),(3,{3},'randomizedPlugSetHash',pool,{'plugItemHash':ENHANCED,'currentlyCanRoll':True},False)]
    for args in negatives:require(not eligible(*args),'illegal pool predicate');count+=1
    return count

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT)
    for name,default in [('inventory','/tmp/destiny-weapons-w30/bungie-items.json'),('plugsets','/tmp/destiny-weapons-w60/bungie-plugsets.json'),('manifest','/tmp/destiny-weapons-w60/manifest.json'),('clarity','/private/tmp/w167-clarity.json'),('ddc','/private/tmp/w182-hir-report/ddc-perks.csv')]:p.add_argument('--'+name,type=Path,default=Path(default))
    p.add_argument('--verify',action='store_true');p.add_argument('--self-test',action='store_true');args=p.parse_args()
    outputs,resource,curves,pairs=generate(args)
    negatives=self_test(resource,curves,pairs) if args.self_test else 0
    for path,obj in outputs.items():
        target=args.root/path;raw=encode(obj)
        if args.verify:require(target.read_bytes()==raw,'generated output drift '+path)
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    print(json.dumps({'verified':args.verify,'outputs':len(outputs),'selected':65,'rolls':16,'coSelections':len(pairs),'negativeChecks':negatives}))
if __name__=='__main__':main()
