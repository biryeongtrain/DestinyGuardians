#!/usr/bin/env python3
"""W141 Allied Demand: semantic solids, open muzzle/guard, clean default-dye face UV.

The inert Blender reference is never used as exported geometry. Full model only;
canonical item/ADS/generic reload/display and all gameplay remain unchanged.
"""
import argparse
import base64
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import uuid
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/allied_demand/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/sidearm/allied_demand.json'
MODEL = ASSET+'models/weapon_surface_w123/allied_demand.json'
TEXTURE = ASSET+'textures/item/weapon/w123/allied_demand.png'
RAW = Path('/tmp/destiny-weapons-w30/raw/allied_demand/extracted/Allied Demand')
PHOTO = Path('/tmp/destiny-weapons-w31/references/allied_demand.jpg')
BB = 'art/blockbench/weapons/w30/allied_demand.bbmodel'
EDGE = 1024
H = runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
FACES = H['FACES']
PALETTE = dict(green=[31,66,45], green_edge=[44,80,55], silver=[163,169,162],
               bright=[210,214,202], black=[28,32,31], rubber=[22,27,23], steel=[83,91,87],
               darksteel=[54,63,58], white=[213,216,202])

def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v): return hashlib.sha256(v).hexdigest()
def png(im):
    b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(v): return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w141:allied_demand:'+v))
def vertices(e):
    e=copy.deepcopy(e)
    if 'rotation' in e:
        r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return H['vertices'](e)

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    reference=json.loads((ROOT/ART/'source-reference.json').read_bytes())
    assert reference['sourceSha256']==sha((RAW/'Allied Demand.blend').read_bytes())
    meshes=[]
    for m in reference['meshes']:
        v=np.array(m['vertices'])[:,[0,2,1]]*meta['scale']+meta['anchor']
        uv=np.array(m['uv']);uv[:,:,1]=1-uv[:,:,1]
        meshes.append(dict(name=m['name'],vertices=v,faces=np.array(m['faces']),uv=uv,materials=m['materials'],materialIndices=m['materialIndices']))
    p=np.concatenate([m['vertices'] for m in meshes])
    assert sum(len(m['faces']) for m in meshes)==10089
    assert np.allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=1e-5)
    return meshes,meta

def make_design(meta):
    parts=[]
    def box(group,name,c,size,mat,motif='plain',turn=None):
        c=np.array(c,float);s=np.array(size,float)
        e=dict(name=name,**{'from':(c-s/2).round(6).tolist(),'to':(c+s/2).round(6).tolist()})
        if turn: e['rotation']=dict(origin=c.tolist(),axis=turn[0],angle=turn[1])
        parts.append(dict(group=group,material=mat,motif=motif,kind='opaque_solid_cuboid',geometry=e))
    def beam(group,name,a,b,width,depth,mat,motif='plain'):
        a=np.array(a,float);b=np.array(b,float);v=b-a
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],mat,motif,('x',round(math.degrees(math.atan2(v[2],v[1])),6)))
    def ring(group,name,z0,z1,r,t,mat,motif='plain'):
        for i in range(8):
            angle=i*45;rad=math.radians(angle);rc=r-t/2
            box(group,f'{name}_{i}',[8-rc*math.sin(rad),12.536+rc*math.cos(rad),(z0+z1)/2],
                [2*r*math.tan(math.pi/8)+.008,t,z1-z0],mat,motif,('z',angle))
    # The wide silencer and the dark patterned collar are the weapon's main silhouette.
    # Small silencer perforations stay recessed paint, not a grid of tiny geometry.
    ring('silencer','perforated_shroud',-4.78,-1.00,.69,.17,'silver','perforated')
    ring('silencer','muzzle_front_rim',-4.846,-4.65,.71,.19,'steel','rim')
    ring('silencer','inner_barrel',-4.66,-3.45,.25,.10,'black','bore')
    box('silencer','deep_bore_backstop',[8,12.536,-3.45],[.32,.32,.08],'black')
    ring('collar','black_patterned_collar',-1.00,1.40,.69,.19,'black','collar_art')
    ring('collar','white_collar_band',1.39,1.67,.70,.18,'white','grooves')
    # Continuous slide with chamfered shoulders, not stacked outlines/alpha plates.
    box('slide','slide_core',[8,12.53,5.51],[1.20,1.18,7.82],'silver','wolf')
    box('slide','slide_top',[8,13.18,5.46],[.99,.14,7.78],'bright','ribbed')
    for side in (-1,1):
        box('slide',f'slide_upper_chamfer_{side}',[8+side*.57,13.08,5.48],[.22,.24,7.80],'silver','wolf',('z',side*45))
        box('slide',f'slide_lower_chamfer_{side}',[8+side*.56,11.99,5.43],[.20,.20,7.77],'steel','ribbed',('z',side*45))
    box('slide','white_front_band',[8,12.55,2.02],[1.25,1.22,.48],'white','grooves')
    box('slide','rear_cap',[8,12.53,9.40],[1.12,1.15,.18],'steel','rear')
    # Ejection port: side recess with a dark inner floor and raised edge, no full cutthrough claim.
    box('slide','port_recess',[8.614,12.73,6.79],[.025,.42,1.06],'black','port')
    box('slide','port_floor',[8.633,12.56,6.79],[.045,.08,1.05],'steel')
    box('receiver','green_frame',[8,11.51,5.40],[1.19,1.14,8.18],'green','panel')
    box('receiver','front_underside',[8,11.10,2.02],[1.13,.46,1.37],'green_edge','panel')
    for side in (-1,1):
        box('receiver',f'frame_upper_bevel_{side}',[8+side*.54,11.92,5.46],[.25,.25,7.97],'green_edge','panel',('z',side*45))
        box('receiver',f'rear_cheek_{side}',[8+side*.58,11.39,8.89],[.14,1.23,1.78],'green','panel')
    # Sloped backstrap and a genuinely filled handle; original contact/scale retained.
    beam('grip','green_grip_core',[8,7.44,9.25],[8,10.94,8.49],1.12,1.49,'green','grip')
    for side in (-1,1):
        beam('grip',f'recessed_grip_panel_{side}',[8+side*.555,7.55,9.23],[8+side*.555,10.41,8.61],.09,1.24,'green_edge','grain')
    beam('grip','frontstrap',[8,7.51,8.43],[8,10.63,7.76],.94,.21,'green','grip_ribs')
    beam('grip','backstrap',[8,7.56,10.04],[8,11.23,9.27],1.06,.24,'green','grain')
    box('grip','heel',[8,7.30,9.13],[1.21,.44,1.88],'green_edge','heel',('x',-12))
    beam('magazine','magazine_lower',[8,6.84,8.94],[8,8.43,8.60],1.01,1.24,'darksteel','magazine')
    box('magazine','magazine_floor',[8,6.81,9.02],[1.13,.30,1.56],'green','grooves',('x',-12))
    # Five substantial guard segments surround physical finger space.
    beam('guard','guard_front',[8,10.95,5.39],[8,9.72,5.55],.32,.27,'green')
    beam('guard','guard_toe',[8,9.72,5.55],[8,9.43,5.99],.32,.27,'green')
    beam('guard','guard_bottom',[8,9.43,5.99],[8,9.43,7.19],.32,.28,'green')
    beam('guard','guard_heel',[8,9.43,7.19],[8,9.80,7.68],.32,.27,'green')
    beam('guard','guard_rear',[8,9.80,7.68],[8,10.77,7.86],.32,.27,'green')
    beam('trigger','trigger_shank',[8,10.88,7.02],[8,10.17,6.81],.18,.15,'black')
    beam('trigger','trigger_tip',[8,10.17,6.81],[8,9.97,6.49],.18,.15,'steel')
    # Source side controls, true forward underlug inset, front blade + rear U notch.
    for side in (-1,1):
        box('controls',f'safety_pivot_{side}',[8+side*.65,11.70,8.62],[.16,.33,.33],'black','bolt',('x',45))
        box('controls',f'slide_stop_{side}',[8+side*.65,11.60,7.34],[.16,.20,1.12],'black','control')
        box('controls',f'stop_button_{side}',[8+side*.69,11.56,6.90],[.14,.35,.38],'steel','grooves')
    box('controls','front_underlug',[8,11.10,1.31],[.55,.50,.15],'steel','bolt')
    box('controls','underlug_inset',[8,11.10,1.22],[.28,.28,.04],'black')
    box('sight','front_sight_base',[8,13.25,1.92],[.51,.11,.56],'steel')
    box('sight','front_sight',[8,13.34,1.92],[.16,.18,.34],'bright','dot')
    box('sight','rear_sight_base',[8,13.26,8.38],[.68,.11,.55],'steel')
    for side in (-1,1):box('sight',f'rear_sight_wing_{side}',[8+side*.24,13.35,8.40],[.16,.16,.42],'bright','dot')
    inputs=[BASE,BB,ART+'source-reference.json','art/weapons/w31/references.json']
    raw=[PHOTO,RAW/'Allied Demand.blend',RAW/'textures/Allied Demand_SlideDiffuse.png']
    return dict(id='allied_demand',stage='W141',source=meta,parts=parts,
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='[raw.X,raw.Z,raw.Y]*scale+anchor',muzzle='-Z',display='canonical exact'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw},
        identity=['green full lower frame/handle','long silver perforated silencer','black/white patterned collar','ribbed pale slide and source wolf artwork'],
        limitations=['Silencer small perforations are recessed UV artwork, not physical holes; central barrel bore is open',
                    'Source wolf crop is repainted by luminance with large dye fields; not original dynamic PBR/reflection',
                    'Full-only generic reload; no new separated sidearm magazine or moving slide'])

def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])];u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q

def tile(spec,face,w,h):
    u,v,q=world_points(spec['geometry'],face,w,h);mat=spec['material'];motif=spec['motif']
    rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
    rgb*=(.98+.025*np.cos(q[:,:,1]*3))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<.65]*=.72;rgb[(edge>.65)&(edge<1.3)]*=1.10
    side=face in ('east','west')
    if motif=='perforated':
        a=np.arctan2(q[:,:,0]-8,q[:,:,1]-12.536)
        t=np.mod((q[:,:,2]+4.72)*2.6,1)-.5;s=np.mod(a*4.2+np.floor((q[:,:,2]+4.72)*2.6)*.5,1)-.5
        r=np.sqrt(t*t+s*s);rgb[(r>.20)&(r<.33)]=PALETTE['bright'];rgb[r<.24]=[25,30,29];rgb[(r>.24)&(r<.28)]=[70,78,73]
    if motif=='collar_art':
        a=np.arctan2(q[:,:,0]-8,q[:,:,1]-12.536);z=q[:,:,2]
        wave=np.mod(a*1.6+np.abs(z-.15)*1.30,2)
        rgb[(wave<.13)|((wave>.28)&(wave<.36))]=PALETTE['white']
    if motif=='wolf' and side:
        # Actual source motif, not a newly invented emblem. World-mapped so each
        # chamfer shares the same field without random UV patches or mirrored text.
        raw=np.array(Image.open(RAW/'textures/Allied Demand_SlideDiffuse.png').convert('RGB'))
        z=q[:,:,2];vy=np.clip((13.14-q[:,:,1])/1.15,0,1)
        # Two source wolves with their crop's ~2:1 aspect, not one long stretched
        # atlas fragment. Opposed artwork is intentional; there is no mirrored text.
        first=(z>=2.65)&(z<=4.95);second=(z>=6.0)&(z<=8.3)
        uz=np.where(first,(z-2.65)/2.3,1-(z-6.0)/2.3);uz=np.clip(uz,0,1)
        x=(185+uz*440).astype(int);y=(1320+vy*215).astype(int)
        lum=raw[y,x].mean(2);mask=np.clip((lum-149)/24,0,1)*(first|second)
        rgb=rgb*(1-mask[:,:,None])+np.array(PALETTE['white'])*mask[:,:,None]
    if motif=='ribbed' and face=='up':
        # The slide has long longitudinal flutes, not vertical barcode stripes.
        rgb[np.mod((q[:,:,0]-8)*7,1)<.14]*=.72
    if motif=='wolf' and side:
        rgb[(np.mod(q[:,:,1]*5.5,1)<.08)]*=.87
    if motif in ('grip_ribs','grooves'):
        axis=q[:,:,1] if motif=='grip_ribs' else q[:,:,2];rgb[np.mod(axis*8,1)<.21]*=.62
    if motif=='grain':rgb*=(.98+.027*np.sin(q[:,:,2]*37+np.sin(q[:,:,1]*14)*2))[:,:,None]
    if motif=='panel' and side:
        rgb[(v>.14)&(v<.17)&(u>.15)&(u<.89)]*=.72
    if motif=='bolt':
        radius=np.hypot((u-.5),(v-.5));rgb[radius<.30]=PALETTE['black'];rgb[(radius>.30)&(radius<.40)]=PALETTE['silver']
    if motif=='dot' and face=='south':rgb[(abs(u-.5)<.17)&(abs(v-.5)<.17)]=[204,214,178]
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=24
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,e['name'],face,spec))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));x=y=2;row=0;ledger=[];uvs={}
    for h,w,name,face,spec in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow '+name)
        im=tile(spec,face,w,h);atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uvs[(name,face)]=[v*16/EDGE for v in [x,y,x+w,y+h]];ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    elements=[]
    for spec in d['parts']:
        e=copy.deepcopy(spec['geometry']);e['faces']={f:dict(uv=uvs[(e['name'],f)],texture='#0') for f in FACES};elements.append(e)
    d['atlas']=dict(size=EDGE,gutter=2,used_height=y+row+2,face_islands=len(ledger),islands=ledger)
    return atlas,dict(credit='W141 Allied Demand / authored solids / opaque default dye face atlas',
        textures={'0':'destiny:item/weapon/w123/allied_demand','particle':'destiny:item/weapon/w123/allied_demand'},
        elements=elements,display=json.loads((ROOT/BASE).read_bytes())['display'])

def model_triangles(model,atlas):
    m=copy.deepcopy(model)
    for e in m['elements']:
        if 'rotation' in e:
            r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return H['model_triangles']({'full':m},atlas)

def inspection(d,model,atlas):
    es=[];groups=[]
    for group in sorted({s['group'] for s in d['parts']}):
        children=[];names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        for e in model['elements']:
            if e['name'] not in names:continue
            b=copy.deepcopy(e);r=b.pop('rotation',None);b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
            es.append(b);children.append(b['uuid'])
        groups.append(dict(name=group,uuid=uid(group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Allied Demand W141 owned inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='allied_demand.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=copy.deepcopy(model['display']))

def comparison(d,meshes,atlas,model):
    w,h=820,400;sheet=Image.new('RGB',(2460,1780),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'ALLIED DEMAND W141 / SEMANTIC SOLIDS + CLEAN DEFAULT DYE UV',28)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((940,475));sheet.paste(photo,(0,50))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / full only / no alpha body shells','Green receiver / pale ribbed slide / original wolf artwork','Long octagonal silencer / black patterned collar','Actual central bore / open trigger guard / open rear notch','Small silencer perforations = recessed UV, not geometry','Original anchor/axis/display/ADS/audio/gameplay preserved','Offline comparison, not native or PBR certification']):label(1000,85+i*48,line,23)
    texroot=RAW/'textures';raw=[]
    for m in meshes:
        textures=[]
        for material in m['materials']:
            n=next(n for n in material['images'] if 'Diffuse' in n);textures.append(np.array(Image.open(texroot/n).convert('RGBA')))
        for ps,uv,mi in zip(m['vertices'][m['faces']],m['uv'],m['materialIndices']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);n/=max(np.linalg.norm(n),1e-20);raw.append((ps,uv,textures[mi],n))
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/allied_demand.png'))
    ts=[raw,model_triangles(old,oldtex),model_triangles(model,atlas)];points=np.concatenate([m['vertices'] for m in meshes])
    for col,s in enumerate(['RIP / UNDYED DIFFUSE','OLD CANONICAL / READ ONLY',f'NEW / {len(model["elements"])} SEMANTIC CUBOIDS']):label(col*w+15,540,s)
    for row,(s,cam) in enumerate([('SIDE',[1,0,0]),('MUZZLE OBLIQUE',[1,.4,-.65]),('REAR OBLIQUE',[-1,.3,.6])]):
        ext=H['frame'](points,cam,w,h)
        for col,tris in enumerate(ts):
            im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,580+row*h));label(col*w+15,588+row*h,s,18)
    return png(sheet)

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    review=f'''# Allied Demand W141\n\n{len(model['elements'])} hand-authored opaque semantic cuboids, original hand frame retained. Long silver silencer with actual central bore, green filled frame and grip, open guard, pale ribbed slide with the original source wolf motif on coherent face UV. Small silencer perforations use recessed paint, not physical openings. No alpha body shell, source-island direct transplant, or invented arbitrary triangle schema.\n\nSource: inert Blender5.4 library extraction of exactly5 W30 accepted mesh objects/10089triangles, --disable-autoexec, distinct background process; existing DCC session untouched. Default green/pale paint from W31 Bungie/light.gg reference, not undyed raw diffuse. New matte material interpretation is not original PBR recovery.\n\nOriginal scale/anchor/canonical display/ADS/generic reload/gameplay/audio preserved; full-only, no new moving magazine. CPU side/front/rear comparisons are art evidence, not native. Targeted tests, Blockbench and representative native checks are recorded by master separately.\n'''
    out={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review.encode()}
    if include_comparison:out[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    p=np.concatenate([vertices(e) for e in model['elements']]);assert 0<len(model['elements'])<=1000
    manifest=dict(id='allied_demand',revision='W141',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=6*len(model['elements']),max_assembled_elements=1000,texture_size=[EDGE,EDGE],actual_bounds=[p.min(0).tolist(),p.max(0).tolist()],source_bounds=meta['model_bounds'],source_triangles=10089,source_scale=meta['scale'],source_anchor=meta['anchor'],canonical_display_exact=True,full_only=True,native_accepted=False,input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={p:sha(data) for p,data in out.items()},limitations=d['limitations'])
    out[ART+'manifest.json']=encode(manifest);return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    for path,data in generate().items():
        target=ROOT/path
        if args.verify:assert target.is_file() and target.read_bytes()==data,path
        else:target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(data)
    print('Allied Demand W141', 'verified' if args.verify else 'generated')
if __name__=='__main__':main()
