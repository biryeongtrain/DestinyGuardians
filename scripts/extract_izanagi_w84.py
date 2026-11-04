#!/usr/bin/env python3
"""Additive exotic profile derived from SHA-pinned W84 research + historical W46 curves.
--verify reconstructs bytes without writing. No current exact Destiny timing claim.
"""
import argparse,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
sha=lambda b:hashlib.sha256(b).hexdigest()
def generate():
    research_path=ROOT/'art/weapons/w84/data/extraction.json'
    raw=research_path.read_bytes();research=json.loads(raw);o=research['official']
    formula_path=ROOT/'art/weapons/w46/weapon_formulas.json';formula_raw=formula_path.read_bytes()
    assert sha(formula_raw)=='fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d'
    f=json.loads(formula_raw)['Sniper Rifle'];assert f['1070100196']['subFam']=='Adaptive'
    c=f['cat']['default'];s=o['derivedFixedRollDisplayStats'];id='izanagis_burden'
    ticks=lambda curve,stat:math.ceil(20*(curve['offset']+curve.get('vpp',0)*stat+curve.get('evpp',0)*stat**2))
    reload=ticks(c['reload'],s['4188031367']);assert reload==61
    row=dict(catalog=dict(id=id,family='sniper_rifle',frame='exotic',name="Izanagi's Burden",source_frame_label='Honed Edge',item_model='destiny:weapon/'+id),
        characteristics=dict(id=id,bungieHash=o['weaponHash'],slot='KINETIC',ammo='SPECIAL',damage='KINETIC',exotic=True,stats=s),
        timing=dict(id=id,timing=dict(supported=True,magazine=s['3871231066'],rpm=s['4284893193'],chargeMillis=None,drawMillis=None,cadenceTicks=round(1200/s['4284893193'],12),burstSpacingTicks=0.,burstSize=1,sharedBurstAmmo=False,chargeTicks=None,drawTicks=None,reloadTicks=reload,shellReload=False,reloadPerRoundTicks=None,reloadInitialTicks=None)),
        ballistics=dict(id=id,offsetStart=999.,vppStart=0.,offsetEnd=999.9,vppEnd=0.,floor=.999,precision=2.5),
        aim=dict(id=id,profile=dict(transitionTicks=ticks(c['handling']['ads'],s['943549884']),zoom=s['3555269338']/10,falloffScalar=4.5,stability=float(s['155624089']),recoilDirection=s['2715839340'],kick=round(1.60*(1-.6*s['155624089']/100),6),bloomPerShot=round(.02+.18*(1-s['155624089']/100),6),recoveryPerTick=.04)),
        handling=dict(id=id,profile=dict(supported=True,handling=s['943549884'],readyTicks=ticks(c['handling']['ready'],s['943549884']),stowTicks=ticks(c['handling']['stow'],s['943549884']))),
        aimMovement=dict(id=id,scalar=.75,rule='ordinary'),reloadCredit=[])
    audio=json.loads((ROOT/'art/weapons/w84/audio/implementation.json').read_text())
    row['reloadAudio']=audio['reloadAudio'];assert len(row['reloadAudio'])==1 and row['reloadAudio'][0]['ticks']==reload
    runtime=enc([row]);path=ROOT/'src/main/resources/destiny/weapons/w84-exotics.json'
    evidence=dict(stage='W84',formulaSource=str(formula_path.relative_to(ROOT)),formulaSha256=sha(formula_raw),researchSource=str(research_path.relative_to(ROOT)),researchSha256=sha(raw),runtimeSha256=sha(runtime),derived=row,
        policy=['Official fixed plug stats; historical curves ceil20Hz; timing not independently measured.',
                'Normal/Honed reload61ticks; Honed ignores reload modifiers, full-ready commit; exact original duration/commit unknown.',
                'Minecraft base damage16HP and base precision2.5 retained; Honed community same-hit-type multipliers separate; no catalyst.',
                'No Distractions flinch, unspecified range increase and Barrier behavior deferred, not silently fabricated.',
                'W70 three-dimensional scope-lens/reticle fallback, not an invented exact full-screen scope.'])
    return {path:runtime,ROOT/'art/weapons/w84/data/runtime-extraction.json':enc(evidence)}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');a=ap.parse_args()
    for p,b in generate().items():
        if a.verify:assert p.read_bytes()==b,p
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    print(json.dumps(dict(stage='W84',verified=a.verify)))
