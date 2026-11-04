#!/usr/bin/env python3
"""Sight-anchored sampled ADS, new namespace only; historical graphs stay intact."""
import argparse,copy,hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'src/main/resources/assets/destiny'
KEY='weapon_sight_w148'
SHOTGUNS={
 'dust_rock_blues':dict(y=12.85,rear=10.15,front=-4.1,style='iron'),
 'first_in_last_out':dict(y=13.4,rear=5.2,front=-8.5,style='open_reflex'),
 'ikelos_sg_v1_0_1':dict(y=14.0,rear=3.9,front=-8.7,style='open_reflex'),
 'parcel_of_stardust_fell_to_earth':dict(y=13.15,rear=5.0,front=-9.1,style='iron'),
 'mindbender_s_ambition_adept':dict(y=13.15,rear=5.1,front=-9.1,style='iron'),
}
BOWS=('biting_winds','whispering_slab')
FP=('firstperson_righthand','firstperson_lefthand')
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def read(p):return json.loads(p.read_bytes())

def endpoint(hip,center,scale):
    d=copy.deepcopy(hip)
    # Vanilla mainhand T(sign*.56,-.52,-.72), then ItemTransform about (8,8,8).
    # Left ItemTransform reflects X itself: solve its translation before reflection.
    for c in FP:
        d[c]=dict(rotation=[0,0,0],translation=[round(-8.96-scale*(center[0]-8),6),round(8.32-scale*(center[1]-8),6),-7 if scale<.94 else round(2.72-scale*(center[2]-8),6)],scale=[scale]*3)
    return d

def display(hip,ads,p):
    d=copy.deepcopy(hip)
    for c in FP:
        for k in ('rotation','translation','scale'):d[c][k]=[round(a+(b-a)*p,6) for a,b in zip(hip[c][k],ads[c][k])]
    return d

def shotgun_body(id,cfg):
    source=A/f'models/weapon_surface_w123/{id}.json';m=read(source)
    # The prior artist proxy sights did not form a common sight line. Replace only
    # these ADS proxies, not the hip/thirdperson artwork or receiver/body geometry.
    removed=[e['name'] for e in m['elements'] if 'sight' in e.get('name','').lower()]
    elements=[copy.deepcopy(e) for e in m['elements'] if e.get('name') not in removed]
    def box(name,lo,hi,uv=(0,0,1,1)):
        elements.append(dict(name='w148_'+name,**{'from':lo,'to':hi},faces={f:dict(uv=list(uv),texture='#sight') for f in ('north','south','east','west','up','down')}))
    y,z=cfg['y'],cfg['rear'];sightbottom=y-.64
    box('sight_mount',[7.35,sightbottom-.18,z-.65],[8.65,sightbottom,z+.35],(0,0,2,2))
    if cfg['style']=='iron':
        # U-notch has a genuinely empty viewing channel; luminous bead at front.
        box('rear_ear_left',[7.46,y-.55,z-.12],[7.76,y+.23,z+.12])
        box('rear_ear_right',[8.24,y-.55,z-.12],[8.54,y+.23,z+.12])
        box('rear_notch_bottom',[7.46,y-.66,z-.12],[8.54,y-.46,z+.12])
        front=cfg['front'];box('front_ramp',[7.73,y-1.0,front-.48],[8.27,y-.3,front+.48])
        box('front_bead',[7.94,y-.3,front-.12],[8.06,y,front+.12],(4,0,5,1))
    else:
        # Small 3D open reflex hood on the existing optic rail, not an opaque
        # scope card. The illuminated physical pin points to the clear aperture.
        box('optic_left',[7.20,y-.6,z-.18],[7.38,y+.58,z+.18])
        box('optic_right',[8.62,y-.6,z-.18],[8.80,y+.58,z+.18])
        box('optic_roof',[7.2,y+.56,z-.18],[8.8,y+.74,z+.18])
        box('optic_base',[7.2,y-.75,z-.18],[8.8,y-.56,z+.18])
        box('optic_pin',[7.96,y-.55,z-.12],[8.04,y-.05,z+.12],(6,0,7,1))
    m={k:v for k,v in m.items() if k!='display'};m['elements']=elements;m['textures']['sight']='destiny:item/weapon/w148/sights'
    return m,dict(id=id,sightCenter=[8,y,z],forwardPoint=[8,y,z-2],style=cfg['style'],removedSightNames=removed,elements=len(elements),source=str(source.relative_to(ROOT)),sourceSha256=sha(source.read_bytes()))

def generate():
    out={};inputs={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in (Path(__file__).resolve(),ROOT/'scripts/build_weapons_w30.py',ROOT/'art/weapons/w148/bow-sights.json',A/'textures/item/weapon/w148/sights.png')};rows=[]
    two_hand=runpy.run_path(str(ROOT/'scripts/build_weapons_w30.py'))['two_hand_display']
    bows=read(ROOT/'art/weapons/w148/bow-sights.json')['bows']
    def load(p):inputs[str(p.relative_to(ROOT))]=sha(p.read_bytes());return read(p)
    def child(key,parent,d):
        out[A/f'models/{key}.json']=encode(dict(parent='destiny:'+parent,display=d))
        return dict(type='minecraft:model',model='destiny:'+key)
    def remap(v,mapping):
        if isinstance(v,dict):
            if v.get('type')=='minecraft:model' and v.get('model') in mapping:return dict(v,model=mapping[v['model']])
            return {k:remap(x,mapping) for k,x in v.items()}
        if isinstance(v,list):return [remap(x,mapping) for x in v]
        return v
    for id in (*SHOTGUNS,*BOWS):
        bow=id in BOWS;family='bow' if bow else 'shotgun'
        hip=load(A/f'models/weapon/{family}/{id}.json')['display']
        if bow:
            data=next(b for b in bows if b['id']==id);center=data['sightCenter'];body=data['model'].removeprefix('destiny:');scale=.9
            load(A/f'models/{body}.json')
        else:
            model,data=shotgun_body(id,SHOTGUNS[id]);center=data['sightCenter'];scale=.95;body=f'{KEY}/{id}_body'
            load(ROOT/data['source'])
            out[A/f'models/{body}.json']=encode(model)
        ads=endpoint(hip,center,scale);mapping={}
        for f in range(21):
            d=display(hip,ads,f/20)
            for style in ('native','twohand'):
                old=f'weapon_aim_w70/{id}_{f:02}_{style}';key=f'{KEY}/{id}_{f:02}_{style}'
                # Frame0 remains exact old geometry/display; no HIP jump on admission.
                parent=f'weapon/{family}/{id}' if f==0 else body
                child(key,parent,d if style=='native' else two_hand(d,family));mapping['destiny:'+old]='destiny:'+key
        original=load(A/f'items/weapon_aim_w70/{id}.json');out[A/f'items/{KEY}/{id}.json']=encode(remap(original,mapping))
        if bow:
            original=load(A/f'items/weapon_aim_w70/{id}_bow.json')
            for f in range(21):
                d=display(hip,ads,f/20)
                for p in sorted((A/'models/weapon_aim_w70').glob(f'{id}_bow_*_{f:02}.json')):
                    old=load(p);parent=old['parent'].removeprefix('destiny:')
                    if parent.endswith('_body_hip') and f>0:parent=body
                    key=f'{KEY}/'+p.stem
                    child(key,parent,d);mapping['destiny:weapon_aim_w70/'+p.stem]='destiny:'+key
            out[A/f'items/{KEY}/{id}_bow.json']=encode(remap(original,mapping))
        rows.append(dict(id=id,family=family,body=body,sight=data,hip=hip,ads=ads,scale=scale,frames=21))
    out[ROOT/'art/weapons/w148/ads-manifest.json']=encode(dict(stage='W148',weapons=rows,inputSha256=inputs,outputs={str(p.relative_to(ROOT)):sha(v) for p,v in out.items()},policy='Sight plane, not bounds. New namespace; historical W50/W70 graphs unchanged; fallback HIP/thirdperson preserved. New ADS physical sight proxies, not exact extracted D2 optic meshes.'))
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args();out=generate()
    for path,data in out.items():
        if a.verify:assert path.read_bytes()==data,path
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print('W148 sight ADS',len(out),'verified' if a.verify else 'generated')
