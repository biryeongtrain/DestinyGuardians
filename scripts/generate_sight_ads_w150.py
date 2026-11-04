#!/usr/bin/env python3
"""W150 trace rifle, rockets and real LFR optics: align real authored rear sights, preserve HIP/3rd graphs."""
import argparse,copy,hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'src/main/resources/assets/destiny';KEY='weapon_sight_w150'
IDS=('retraced_path','bellowing_giant','pyroclastic_flow','line_in_the_sand','stormchaser')
FP=('firstperson_righthand','firstperson_lefthand')
def enc(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()

def generate():
    out={};inputs={};rows=[];two_hand=runpy.run_path(str(ROOT/'scripts/build_weapons_w30.py'))['two_hand_display']
    def read(p):inputs[str(p.relative_to(ROOT))]=sha(p.read_bytes());return json.loads(p.read_bytes())
    def remap(v,mapping):
        if isinstance(v,dict):
            if v.get('type')=='minecraft:model' and v.get('model') in mapping:return dict(v,model=mapping[v['model']])
            return {k:remap(x,mapping) for k,x in v.items()}
        if isinstance(v,list):return [remap(x,mapping) for x in v]
        return v
    for id in IDS:
        family='trace_rifle' if id=='retraced_path' else 'linear_fusion_rifle' if id in ('line_in_the_sand','stormchaser') else 'rocket_launcher'
        hip=read(A/f'models/weapon/{family}/{id}.json')['display'];design=read(ROOT/f'art/weapons/w123/{id}/design.json')
        sight=design['ads_sight'];center=sight['sightCenter']
        assert sight['eyeSide']=='+Z' and sight['plane']=='XY'
        assert all(abs(a-b)<1e-6 for a,b in zip(sight['forwardPoint'],[center[0],center[1],center[2]-2])),id
        s=.9;ads=copy.deepcopy(hip)
        for c in FP:
            ads[c]=dict(rotation=[0,0,0],translation=[round(-8.96-s*(center[0]-8),6),round(8.32-s*(center[1]-8),6),round(1.12-s*(center[2]-8),6)],scale=[s]*3)
        read(A/f'models/weapon_surface_w123/{id}.json');mapping={}
        for f in range(21):
            d=copy.deepcopy(hip)
            for c in FP:
                for k in ('rotation','translation','scale'):d[c][k]=[round(a+(b-a)*f/20,6) for a,b in zip(hip[c][k],ads[c][k])]
            for style in ('native','twohand'):
                key=f'{KEY}/{id}_{f:02}_{style}';old=f'destiny:weapon_aim_w70/{id}_{f:02}_{style}'
                parent=f'weapon/{family}/{id}' if f==0 else f'weapon_surface_w123/{id}'
                out[A/f'models/{key}.json']=enc(dict(parent='destiny:'+parent,display=d if style=='native' else two_hand(d,family)))
                mapping[old]='destiny:'+key
        graph=remap(read(A/f'items/weapon_aim_w70/{id}.json'),mapping)
        # W155: suppress the repeated CONSUME hand-height dip only on the LFR
        # ADS route. Canonical HIP, third-person transforms and reload graphs
        # remain independent; authored ADS transition/recoil are not disabled.
        if family=='linear_fusion_rifle':graph['swap_animation_scale']=0.0
        out[A/f'items/{KEY}/{id}.json']=enc(graph)
        rows.append(dict(id=id,family=family,sight=sight,hip=hip,ads=ads,eyeToSightMeters=.65,scale=s,frames=21))
    for id in ('line_in_the_sand','stormchaser'):
        value=read(A/f'models/weapon_surface_w123/{id}.json')
        old=read(A/f'models/weapon_scope_w45/{id}_geometry.json')
        assert value['display']==old['display'],id
        out[A/f'models/weapon_surface_w123/{id}_geometry.json']=enc(value)
    for p in (Path(__file__).resolve(),ROOT/'scripts/build_weapons_w30.py'):inputs[str(p.relative_to(ROOT))]=sha(p.read_bytes())
    out[ROOT/'art/weapons/w150/ads-manifest.json']=enc(dict(stage='W150',weapons=rows,inputSha256=inputs,outputs={str(p.relative_to(ROOT)):sha(v) for p,v in out.items()},policy='Physical authored sight, not bounds; historical W70/W148/W149 and existing LFR scope fallback untouched; LFR 3D ADS aligned to authored optic, HIP/third fallback unchanged.'))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args();out=generate()
    for p,b in out.items():
        if a.verify:assert p.read_bytes()==b,p
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    print('W150 sight ADS',len(out),'verified' if a.verify else 'generated')
