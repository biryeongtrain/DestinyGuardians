#!/usr/bin/env python3
"""W327 exact-identity legendary data. --capture pins external manifest evidence;
default regenerates offline, --verify checks byte-identical runtime output.
No base weapon's resulting stats or perk pools are copied.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'art/weapons/w327/catalog-source.json'
OUTPUT = ROOT / 'src/main/resources/destiny/weapons/w327-legendary.json'
LOCAL = ['art/weapons/w46/weapon_formulas.json', 'art/weapons/w43/extraction.json',
         'src/main/resources/destiny/weapons/w30.json', 'src/main/resources/destiny/weapons/w326-components.json',
         'scripts/extract_aim_w44.py']

def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encode(x): return (json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
def write(p,x): p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(encode(x))
def require(ok,msg):
    if not ok: raise ValueError(msg)

def capture(cache,candidates):
    paths = {k:cache/v for k,v in [('items','items.json'),('ko','items-ko.json'),('plugsets','plugsets.json'),('manifest','manifest.json')]}
    paths.update(registry=candidates/'final-registry.json',shortlist=candidates/'shortlist-24.json')
    data={k:read(v) for k,v in paths.items()}; items=data['items']; ko=data['ko']; sets=data['plugsets']
    rows=[]
    for r in data['registry']:
        h=str(r['bungie_hash']); item=items[h]; socketrows=[]
        require(sha(r['archive_path'])==r['archive_sha256'],'archive drift '+r['id'])
        for n,s in enumerate(item['sockets']['socketEntries'][:5]):
            sh=s.get('randomizedPlugSetHash') or s.get('reusablePlugSetHash')
            plugs=sets[str(sh)]['reusablePlugItems'] if sh and str(sh) in sets else s.get('reusablePlugItems',[])
            hashes=list(dict.fromkeys(p['plugItemHash'] for p in plugs))
            if not hashes: hashes=[s['singleInitialItemHash']]
            socketrows.append(dict(socket=n,plugSetHash=sh,entry=s,plugs=[dict(hash=q,name=items[str(q)]['displayProperties']['name'],nameKo=ko[str(q)]['displayProperties']['name'],type=items[str(q)].get('itemTypeDisplayName',''),category=items[str(q)].get('plug',{}).get('plugCategoryIdentifier'),investmentStats=items[str(q)].get('investmentStats',[]),itemCategoryHashes=items[str(q)].get('itemCategoryHashes',[]),insertionRules=items[str(q)].get('plug',{}).get('insertionRules',[]),enabledRules=items[str(q)].get('plug',{}).get('enabledRules',[])) for q in hashes]))
        short=next(x for x in data['shortlist']['weapons'] if x['id']==r['id'])
        require(short['bungieHash']==int(h),'shortlist identity mismatch')
        rows.append(dict(registry=r,name=item['displayProperties']['name'],nameKo=ko[h]['displayProperties']['name'],inventory=item['inventory'],equippingBlock=item['equippingBlock'],damageType=item['defaultDamageType'],stats=item['stats']['stats'],sockets=socketrows,drive=short['source']))
    return dict(stage='W327',manifestVersion=data['shortlist']['manifestVersion'],externalPins={k:dict(path=str(p),sha256=sha(p)) for k,p in paths.items()},localPins={p:sha(ROOT/p) for p in LOCAL},policy='Exact selected manifest identity; source art archive can predate reissue. Historical Oracle coefficients and Minecraft recoil/20 TPS adaptations are not guaranteed current Destiny timing.',weapons=rows)

def generate(source):
    for p,h in source['localPins'].items(): require(sha(ROOT/p)==h,'local source drift '+p)
    formulas=read(ROOT/LOCAL[0]); mappings={x['id']:x for x in read(ROOT/LOCAL[1])['entries']}; bases={x['id']:x for x in read(ROOT/LOCAL[2])}
    components=read(ROOT/LOCAL[3])['components']; byhash={x['hash']:x for x in components}
    spec=importlib.util.spec_from_file_location('aim_source',ROOT/LOCAL[4]); aim_module=importlib.util.module_from_spec(spec); spec.loader.exec_module(aim_module)
    rows=[]
    for evidence in source['weapons']:
        reg=evidence['registry']; id=reg['id']; base=reg['base']; family=reg['family']; h=reg['bungie_hash']; m=mappings[base]; catalog=dict(bases[base],id=id,name=evidence['name'],item_model='destiny:weapon/'+id)
        require(catalog['family']==family,'family mismatch '+id)
        catalog['source_frame_label']=reg['frame']
        s={k:v['value'] for k,v in evidence['stats'].items()}; c=formulas[m['family']]['cat'][m['category']]; fire=formulas[m['family']]['subFam'][m['subfamily']]
        stat=lambda key:s.get(key,0)
        handling=stat('943549884'); reload=stat('4188031367'); stability=stat('155624089')
        require(all(0<=v<=100 for v in [handling,reload,stability]),'invalid stat '+id)
        curve=lambda q:dict(evpp=q.get('evpp',0.0),vpp=q.get('vpp',0.0),offset=q['offset'])
        solve=lambda q,x:q.get('evpp',0)*x*x+q.get('vpp',0)*x+q['offset']
        ticks=lambda seconds:math.ceil(seconds*20)
        curves=dict(id=id,hash=h,family=family,baseHandlingStat=handling,baseReloadStat=reload,reload=curve(c['reload']),**{k:curve(v) for k,v in c['handling'].items()})
        charged=family in ('fusion_rifle','linear_fusion_rifle'); shell=family=='shotgun'; rpm=stat('4284893193') or None; charge=(stat('2961396640') or None) if charged else None
        n=fire.get('burst_size',1); inner=fire['inner_burst_delay']/30; simultaneous=shell and inner==0; extra=.45 if family=='fusion_rifle' else .95 if family=='linear_fusion_rifle' else 0
        cadence=((n-1)*inner+extra)*20 if charged else 1200/rpm if rpm and (n==1 or simultaneous) else (fire['burst_delay']/30+(n-1)*inner+extra)*20
        rt=ticks(solve(c['reload'],reload))
        timing=dict(supported=True,magazine=stat('3871231066') or None,rpm=rpm,chargeMillis=charge,drawMillis=None,cadenceTicks=round(cadence,12),burstSpacingTicks=0.0 if simultaneous else round(inner*20,12),burstSize=1 if simultaneous else n,sharedBurstAmmo=charged,chargeTicks=ticks(charge/1000) if charge else None,drawTicks=None,reloadTicks=None if shell else rt,shellReload=shell,reloadPerRoundTicks=rt if shell else None,reloadInitialTicks=None)
        _,scalar,kick=aim_module.FAMILIES[family]
        if family=='pulse_rifle' and m['subfamily']=='Aggressive': scalar=1.8
        if family=='shotgun' and m['category']=='slug': scalar=1.2
        aim=dict(transitionTicks=max(2,min(20,ticks(solve(c['handling']['ads'],handling)))),zoom=max(1.0,min(6.0,stat('3555269338')/10)),falloffScalar=scalar,stability=float(stability),recoilDirection=stat('2715839340'),kick=round(max(.1,min(2.0,kick*(1-.6*stability/100))),6),bloomPerShot=round(.02+.18*(1-stability/100),6),recoveryPerTick=.04)
        range_=c['range']; ballistics=dict(id=id,offsetStart=range_['offset_start'],vppStart=range_['vpp_start'],offsetEnd=range_['offset_end'],vppEnd=range_['vpp_end'],floor=range_.get('pve_floor_percent',range_['floor_percent']),precision=fire['pve_crit_mult']/51+1.5)
        pools={}; traits=[]
        for socket in evidence['sockets'][1:]:
            if socket['socket'] in (1,2):
                slot='barrel' if socket['socket']==1 else 'magazine'; ids=[]
                for plug in socket['plugs']:
                    if plug['type'].startswith('Enhanced'): continue
                    # Shared manifest sets are broader than valid frame components.
                    # Preserve every raw member in evidence, expose only explicit
                    # implementation-compatible components; no name/hash aliases.
                    if plug['hash']==3678323611: continue
                    if plug['hash'] in (1047830412,1332244541) and (family!='shotgun' or catalog['frame']=='pinpoint_slug'): continue
                    if plug['hash']==791862061 and family!='shotgun': continue
                    if plug['hash']==409831596 and catalog['frame']=='wave': continue
                    category=plug['category']
                    allowed_categories=({'tubes'} if family in ('grenade_launcher','heavy_grenade_launcher','rocket_launcher') else {'barrels','scopes'}) if slot=='barrel' else ({'batteries'} if family in ('fusion_rifle','linear_fusion_rifle','trace_rifle') else {'magazines_gl'} if family in ('grenade_launcher','heavy_grenade_launcher','rocket_launcher') else {'magazines'})
                    if category not in allowed_categories: continue
                    component=byhash.get(plug['hash'])
                    require(component is not None,'unmapped base component '+id+' '+str(plug))
                    require(component['slot']==slot,'component slot mismatch')
                    ids.append(component['id'])
                pools[slot]=list(dict.fromkeys(ids)); require(ids,'empty component pool '+id)
            else: traits.append(dict(socket=socket['socket'],plugSetHash=socket['plugSetHash'],perks=socket['plugs']))
        slot={1498876634:'KINETIC',2465295065:'ENERGY',953998645:'POWER'}[evidence['inventory']['bucketTypeHash']]
        characteristics=dict(id=id,bungieHash=h,slot=slot,ammo={1:'PRIMARY',2:'SPECIAL',3:'HEAVY'}[evidence['equippingBlock']['ammoType']],damage={1:'KINETIC',2:'ARC',3:'SOLAR',4:'VOID',6:'STASIS',7:'STRAND'}[evidence['damageType']],exotic=False,stats=s)
        credit=dict(id=id,hash=h,family=family,fraction=.71 if family=='hand_cannon' else .65) if family in ('hand_cannon','machine_gun') else []
        rows.append(dict(base=base,id=id,nameKo=evidence['nameKo'],source=dict(manifestVersion=source['manifestVersion'],bungieHash=h,driveFileId=reg['drive_file_id'],archiveSha256=reg['archive_sha256'],formulaMapping=m,uncertainty=source['policy']),catalog=catalog,characteristics=characteristics,timing=dict(id=id,timing=timing),ballistics=ballistics,aim=dict(id=id,profile=aim),handling=dict(id=id,profile=dict(supported=True,handling=handling,readyTicks=ticks(solve(c['handling']['ready'],handling)),stowTicks=ticks(max(solve(c['handling']['stow'],handling),solve(c['handling']['stow'],100))))),aimMovement=dict(id=id,scalar=.85 if family=='sidearm' else .775 if family=='hand_cannon' and catalog['frame']=='precision' else .75,rule='sidearm' if family=='sidearm' else 'precision hand cannon' if family=='hand_cannon' and catalog['frame']=='precision' else 'ordinary'),reloadCredit=credit,reloadAudio=[],curves=curves,componentPools=pools,officialTraits=traits))
    require(len(rows)==len({x['id'] for x in rows})==len({x['characteristics']['bungieHash'] for x in rows})==24,'expected 24 unique identities')
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--capture',action='store_true'); p.add_argument('--verify',action='store_true'); p.add_argument('--cache',type=Path,default=Path('/tmp/dg-loot')); p.add_argument('--candidates',type=Path,default=Path('/tmp/destiny-perks-20261106/candidates')); a=p.parse_args()
    source=capture(a.cache,a.candidates) if a.capture else read(SOURCE)
    rows=generate(source)
    if a.verify: require(OUTPUT.read_bytes()==encode(rows),'generated runtime drift')
    else:
        if a.capture: write(SOURCE,source)
        write(OUTPUT,rows)
    print(('Verified' if a.verify else 'Generated')+' 24 exact legendary identities; '+str(sum(len(p['perks']) for r in rows for p in r['officialTraits']))+' official trait socket entries')
if __name__=='__main__': main()
