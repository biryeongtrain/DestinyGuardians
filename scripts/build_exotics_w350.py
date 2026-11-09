#!/usr/bin/env python3
"""Pin exact Bungie identities and regenerate the nine W350 base exotics offline.

Official identity/stats are separate from historical W46 timing curves and local HP/blocks.
No catalysts are enabled. --capture reads the reviewed public-source cache; --verify is offline.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'art/weapons/w350/catalog-source.json'
OUT = ROOT / 'src/main/resources/destiny/weapons/w350-exotics.json'
FORMULAS = ROOT / 'art/weapons/w46/weapon_formulas.json'
SPECS = [
    ('crimson', 3437746471, 'hand_cannon', 'Hand Cannon', 24, 3),
    ('thorn', 3973202132, 'hand_cannon', 'Hand Cannon', 11, 1),
    ('outbreak_perfected', 3824673936, 'pulse_rifle', 'Pulse Rifle', 36, 3),
    ('sunshot', 2907129557, 'hand_cannon', 'Hand Cannon', 12, 1),
    ('graviton_lance', 3628991658, 'pulse_rifle', 'Pulse Rifle', 30, 2),
    ('jotunn', 417164956, 'fusion_rifle', 'Fusion Rifle', 5, 1),
    ('gjallarhorn', 1363886209, 'rocket_launcher', 'Rocket Launcher', 1, 1),
    ('whisper_of_the_worm', 1891561814, 'sniper_rifle', 'Sniper Rifle', 3, 1),
    ('tractor_cannon', 3580904581, 'shotgun', 'Shotgun', 4, 1),
]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def encoded(data): return (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(encoded(data))

def capture(cache):
    defs = {r['hash']: r for r in read(cache / 'selected-definitions.json')}
    rows = []
    for id, h, family, formula_family, magazine, burst in SPECS:
        r = defs[h]; item = r['en']; ko = r['ko']
        assert item['inventory']['tierType'] == 6
        rows.append(dict(id=id, hash=h, family=family, formulaFamily=formula_family,
            name=item['displayProperties']['name'], nameKo=ko['displayProperties']['name'],
            inventory=item['inventory'], ammo=item['equippingBlock']['ammoType'],
            damage=item['defaultDamageType'], stats={k: v['value'] for k, v in item['stats']['stats'].items()},
            intrinsic=item['sockets']['socketEntries'][0]['singleInitialItemHash'],
            plugs=[dict(hash=p['hash'], name=p['displayProperties']['name'],
                        description=p['displayProperties']['description']) for p in r['plugs']],
            icon='https://www.bungie.net' + item['displayProperties']['icon'],
            magazine=magazine, burst=burst))
    return dict(stage='W350', retrieved='2026-11-09', manifestVersion=read(cache/'manifest.json')['Response']['version'],
        manifestUrl='https://www.bungie.net/Platform/Destiny2/Manifest/',
        externalPins={n: sha(cache/n) for n in ['manifest.json','items-en.json','items-ko.json','selected-definitions.json']},
        formulaSha256=sha(FORMULAS),
        policy='Base weapons, catalysts excluded. Raw manifest magazine is a display stat; Crimson uses 24 paid cartridges for eight 3-round bursts (W46 crimson magazine profile), Outbreak rounds to a complete 3-round burst (36). Other magazines use current manifest base values. W46 historical category curves supply approximate reload/handling/falloff, not current D2 certification. Tractor full-mag reload is locally calibrated to 91 ticks from the complete supplied 4.51775-second cue. Projectile speed/range/damage and 20 TPS quantization are Minecraft adaptations.',
        weapons=rows)

def generate(source):
    assert source['formulaSha256'] == sha(FORMULAS), 'historical formula source drift'
    formulas = read(FORMULAS); rows = []
    for r in source['weapons']:
        id = r['id']; h = r['hash']; family = r['family']; s = r['stats']
        f = formulas[r['formulaFamily']]; mapping = f[str(r['intrinsic'])]
        c = f['cat'][mapping['cat']]; fire = f['subFam'][mapping['subFam']]
        solve = lambda q, x: q.get('evpp',0)*x*x + q.get('vpp',0)*x + q['offset']
        curve = lambda q: {k: q.get(k,0) for k in ['evpp','vpp','offset']}
        ticks = lambda v: max(1, math.ceil(v*20 - 1e-9))
        handling = s['943549884']; reload = s['4188031367']; stability = s['155624089']
        reload_ticks = 91 if id == 'tractor_cannon' else ticks(solve(c['reload'], reload))
        burst = r['burst']; spacing = fire.get('inner_burst_delay',0) / 30 * 20 if burst > 1 else 0
        cadence = (fire['burst_delay']/30*20 + (burst-1)*spacing) if burst > 1 else 1200/s['4284893193'] if s.get('4284893193') else 9
        # Jotunn has a charged single shot followed by a short recovery, never an ordinary fusion bolt train.
        charge = math.ceil(s['2961396640']/50) if id == 'jotunn' else None
        precision = 1 if id in ('jotunn','gjallarhorn','tractor_cannon') else 1.85 if id == 'crimson' else fire['pve_crit_mult']/51 + 1.5
        timing = dict(supported=True, magazine=r['magazine'], rpm=s.get('4284893193'), chargeMillis=s.get('2961396640'), drawMillis=None,
            cadenceTicks=round(cadence,12), burstSpacingTicks=round(spacing,12), burstSize=burst, sharedBurstAmmo=False,
            chargeTicks=charge, drawTicks=None, reloadTicks=reload_ticks, shellReload=False, reloadPerRoundTicks=None, reloadInitialTicks=None)
        rg = c['range']; ballistics = dict(id=id, offsetStart=rg['offset_start'], vppStart=rg['vpp_start'], offsetEnd=rg['offset_end'],
            vppEnd=rg['vpp_end'], floor=rg.get('pve_floor_percent',rg['floor_percent']), precision=precision)
        if id == 'tractor_cannon': ballistics.update(offsetStart=9, vppStart=0, offsetEnd=9.01, vppEnd=0, floor=.001)
        slot = {1498876634:'KINETIC',2465295065:'ENERGY',953998645:'POWER'}[r['inventory']['bucketTypeHash']]
        damage = {1:'KINETIC',2:'ARC',3:'SOLAR',4:'VOID'}[r['damage']]
        aim = dict(transitionTicks=ticks(solve(c['handling']['ads'],handling)), zoom=max(1,min(6,s['3555269338']/10)),
            falloffScalar=1.4 if family=='hand_cannon' else 1.8 if family=='pulse_rifle' else 4 if family=='sniper_rifle' else 1.5,
            stability=float(stability),recoilDirection=s['2715839340'],kick=round(1.3*(1-.6*stability/100),6),
            bloomPerShot=round(.02+.18*(1-stability/100),6),recoveryPerTick=.04)
        rows.append(dict(stage='W350', nameKo=r['nameKo'],
            catalog=dict(id=id,family=family,frame='exotic',name=r['name'],source_frame_label=r['plugs'][0]['name'],item_model='destiny:weapon/'+id),
            characteristics=dict(id=id,bungieHash=h,slot=slot,ammo={1:'PRIMARY',2:'SPECIAL',3:'HEAVY'}[r['ammo']],damage=damage,exotic=True,stats=s),
            timing=dict(id=id,timing=timing),ballistics=ballistics,aim=dict(id=id,profile=aim),
            handling=dict(id=id,profile=dict(supported=True,handling=handling,readyTicks=ticks(solve(c['handling']['ready'],handling)),stowTicks=ticks(max(solve(c['handling']['stow'],handling),solve(c['handling']['stow'],100))))),
            aimMovement=dict(id=id,scalar=.75,rule='ordinary'),
            reloadCredit=dict(id=id,hash=h,family=family,fraction=.71) if family=='hand_cannon' else [],reloadAudio=[],
            curves=dict(id=id,hash=h,family=family,baseHandlingStat=handling,baseReloadStat=reload,reload=curve(c['reload']),**{k:curve(v) for k,v in c['handling'].items()})))
    assert len(rows) == 9 and all(sum(r['characteristics']['slot']==s for r in rows)==3 for s in ['KINETIC','ENERGY','POWER'])
    audio = ROOT/'art/weapons/w350/audio/reload-profile-snippet.json'
    if audio.exists():
        clips = {r['id']: r for r in read(audio)}
        for r in rows:
            clip = clips[r['catalog']['id']]
            assert clip['ticks'] == r['timing']['timing']['reloadTicks']
            r['reloadAudio'] = [clip]
    return rows

def main():
    p=argparse.ArgumentParser(); p.add_argument('--capture',action='store_true'); p.add_argument('--verify',action='store_true')
    p.add_argument('--cache',type=Path,default=Path('/tmp/exotic-expansion-20261109/data')); a=p.parse_args()
    source=capture(a.cache) if a.capture else read(SOURCE)
    rows=generate(source)
    if a.verify: assert OUT.read_bytes()==encoded(rows), 'runtime definition drift'
    else:
        if a.capture: write(SOURCE,source)
        write(OUT,rows)
    print({r['catalog']['id']:r['timing']['timing']['reloadTicks'] for r in rows})
if __name__=='__main__': main()
