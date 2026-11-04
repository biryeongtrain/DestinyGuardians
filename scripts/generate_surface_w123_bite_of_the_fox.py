#!/usr/bin/env python3
"""W134 Bite of the Fox: authored semantic solids, default-photo face paint.
Offline inert FBX input + CPU inspection. FULL candidate only; no registration.
"""
import argparse
import base64
import copy
import io
import json
import math
from pathlib import Path
import runpy
import uuid
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
HELPER = 'scripts/generate_surface_w123_beloved.py'
H = runpy.run_path(str(ROOT/HELPER))
encode, sha, png = H['encode'], H['sha'], H['png']
rotation, vertices = H['rotation'], H['vertices']
FACES, NORMALS = H['FACES'], H['NORMALS']
render, frame, model_triangles = H['render'], H['frame'], H['model_triangles']
ART = 'art/weapons/w123/bite_of_the_fox/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/sniper_rifle/bite_of_the_fox.json'
MODEL = ASSET+'models/weapon_surface_w123/bite_of_the_fox.json'
TEXTURE = ASSET+'textures/item/weapon/w123/bite_of_the_fox.png'
W30 = 'art/blockbench/weapons/w30/bite_of_the_fox.bbmodel'
REFERENCES = 'art/weapons/w31/references.json'
RAW = Path('/tmp/destiny-weapons-w30/raw/bite_of_the_fox/extracted/Bite of the Fox')
PHOTO = Path('/tmp/destiny-weapons-w31/references/bite_of_the_fox.jpg')
EDGE = 1024
PALETTE = {'burgundy':[62,31,30], 'burgundy_edge':[82,43,38],
           'steel':[112,120,125], 'chassis':[36,43,45], 'rubber':[27,32,34],
           'brass':[181,133,57], 'recess':[16,23,26], 'lens':[12,89,108]}

def source_meshes():
    meta=json.loads((ROOT/W30).read_bytes())['destiny_w30']
    assert sha((RAW/'Bite of the Fox.fbx').read_bytes()) == meta['source_files']['Bite of the Fox/Bite of the Fox.fbx']
    roots=H['parse_fbx'](RAW/'Bite of the Fox.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    meshes=[]
    for node in objects:
        if node[0]!='Geometry': continue
        mid=next(p for c,p in links if c==node[1][0]); m=models[mid]
        name=m[1][1].split('\x00')[0]
        if name not in meta['source_objects']: continue
        props={p[1][0]:p[1][4:] for c in m[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
        assert props['Lcl Scaling']==[100,100,100]
        cs={c[0]:c for c in node[2]}
        raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        # This FBX is X thin, Y length, Z vertical. NOT Beloved's basis.
        v=raw[:,[0,2,1]]*meta['scale']+meta['anchor']
        fs=[]; f=[]
        for i in cs['PolygonVertexIndex'][1][0]:
            f.append(i if i>=0 else -i-1)
            if i<0:
                assert len(f)==3
                fs.append(f); f=[]
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2)
        uv[:,:,1]=1-uv[:,:,1]
        meshes.append(dict(name=name,vertices=v,faces=np.array(fs),uv=uv,
                           material='Main' if name.startswith('Main') else 'Scope' if ' - ' in name else name))
    points=np.concatenate([m['vertices'] for m in meshes])
    np.testing.assert_allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=1e-5)
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==30932
    return meshes,meta

def make_design(meta):
    specs=[]
    def box(name,lo,hi,material,group,motif='panel',turn=None):
        e=dict(name=name,**{'from':lo,'to':hi})
        if turn:
            axis,angle=turn
            e['rotation']=dict(origin=[round((a+b)/2,7) for a,b in zip(lo,hi)],x=0,y=0,z=0)
            e['rotation'][axis]=angle
        specs.append(dict(geometry=e,material=material,group=group,motif=motif))
    def center(name,c,size,mat,group,motif='panel',turn=None):
        box(name,[round(a-b/2,7) for a,b in zip(c,size)],
            [round(a+b/2,7) for a,b in zip(c,size)],mat,group,motif,turn)
    def beam(name,a,b,width,thick,mat,group,motif='panel'):
        z0,y0=a;z1,y1=b
        center(name,[8,(y0+y1)/2,(z0+z1)/2],[width,thick,math.hypot(z1-z0,y1-y0)+.08],mat,group,motif,('x',-math.degrees(math.atan2(y1-y0,z1-z0))))
    def tube(name,y,z0,z1,r,t,mat,group,motif='ring',facets=range(8)):
        # Load-bearing opaque walls around a genuinely empty axial bore.
        for i in facets:
            a=i*45; rr=r-t/2
            center(f'{name}_{i}',[8-rr*math.sin(math.radians(a)),y+rr*math.cos(math.radians(a)),(z0+z1)/2],
                [2*r*math.tan(math.pi/8),t,z1-z0],mat,group,motif,('z',a))
    # Muzzle is left of forearm in -Z. Keep the supplied native endpoints.
    tube('barrel',9.89,-11.60,-6.22,.29,.17,'steel','barrel','barrel')
    center('barrel_root',[8,9.89,-6.3],[.77,.77,.58],'chassis','barrel','ring')
    # Box brake: upper/lower jaws + three bridging ribs per side, two real vents.
    box('brake_roof',[6.961,10.16,-13.80],[9.039033380776868,10.429,-11.43],'steel','muzzle','brake')
    box('brake_floor',[6.961,9.37,-13.80],[9.039033380776868,9.62,-11.43],'steel','muzzle','brake')
    for side in (-1,1):
        for i,z in enumerate((-13.66,-12.62,-11.56)):
            center(f'brake_web_{side}_{i}',[8+side*.9090333808,9.89,z],[.26,.62,.28],'steel','muzzle','brake')
    # Front rectangular ring, open bore and long lower blade on a solid spine.
    for x in (7.56,8.44):
        center('brake_front_cheek_'+str(x),[x,9.89,-13.94],[.25,.75,.28],'steel','muzzle','brake')
    center('brake_front_top',[8,10.20,-13.94],[.75,.19,.28],'steel','muzzle','brake')
    center('brake_front_bottom',[8,9.58,-13.94],[.75,.19,.28],'steel','muzzle','brake')
    # Broad filled forearm, bounded by distinct stepped shoulders, not alpha skins.
    box('forearm_core',[7.57,9.02,-6.5],[8.43,10.11,3.56],'chassis','forearm','ribbed')
    box('forearm_top_armor',[7.49,10.14,-7.25],[8.51,10.46,3.20],'burgundy','forearm','armor')
    for side in (-1,1):
        center(f'forearm_shoulder_{side}',[8+side*.46,10.13,-2.03],[.22,.40,10.44],'burgundy_edge','forearm','armor',('z',side*28))
    box('forearm_lower_armor',[7.52,8.83,-5.1],[8.48,9.25,3.46],'burgundy','forearm','armor')
    center('forearm_nose_collar',[8,9.74,-6.63],[1.32,1.30,.61],'burgundy','forearm','armor')
    # Four solid overlapping swept sections; deep enough to read from the front.
    # Frontmost tip exact -15.5, deliberately below rather than on the bore axis.
    box('blade_tip',[7.77,9.135,-15.5],[8.23,9.26,-14.91],'burgundy','blade','blade')
    beam('blade_front_sweep',[-14.97,9.19],[-11.64,8.81],.77,.24,'burgundy','blade','blade')
    beam('blade_long_edge',[-11.68,8.81],[-7.12,8.47],.83,.28,'burgundy','blade','blade')
    beam('blade_heel',[-7.16,8.60],[-5.10,9.03],1.04,.65,'burgundy','blade','blade')
    beam('blade_return',[-5.18,9.03],[-4.70,9.40],.94,.67,'burgundy','blade','blade')
    # Front and rear paired pointed tabs are characteristic broad armor, UV studs.
    for side in (-1,1):
        for i,z in enumerate((-6.80,-5.65,1.05,2.15)):
            center(f'armor_tab_{side}_{i}',[8+side*.55,9.85,z],[.22,.74,.75],'burgundy','forearm','tab',('x',45))
    # Small brass pin row reads in silhouette; bases/seams are face paint.
    for i,z in enumerate((-6.8,-5.5,-4.2,-2.9,-1.6,-.3)):
        center(f'crest_pin_{i}',[8,10.575,z],[.15,.27,.15],'brass','forearm','pin',('y',45))
    # Receiver, action and offset bolt follow original hand frame.
    box('receiver',[7.54,9.13,3.25],[8.44,10.20,8.25],'chassis','receiver','ribbed')
    box('receiver_top',[7.58,10.18,3.25],[8.42,10.49,7.15],'chassis','receiver','receiver')
    box('receiver_lower',[7.57,8.77,3.40],[8.43,9.18,7.35],'burgundy','receiver','armor')
    center('bolt_shaft',[7.28,9.55,4.48],[.82,.23,.24],'steel','receiver','ring',('y',-14))
    center('bolt_knob',[6.948,9.35,4.58],[.3422144473,.47,.42],'chassis','receiver','ribbed')
    # Integral magazine silhouette, no invented body/mag split output.
    box('magazine',[7.66,7.73,4.12],[8.34,8.89,5.63],'chassis','magazine','magazine')
    center('magazine_floor',[8,7.75,4.96],[.78,.24,1.65],'chassis','magazine','ring',('x',-7))
    center('magazine_brass_catch',[8.36,8.20,5.03],[.06,.31,.37],'brass','magazine','catch')
    # Genuine guard opening; wrist and grip carry real cross-section.
    center('grip_neck',[8,8.85,7.78],[.67,.66,1.02],'chassis','grip','ribbed')
    center('pistol_grip',[8,8.03,8.35],[.64,1.93,.66],'rubber','grip','grip',('x',-17))
    center('grip_heel',[8,7.24,8.61],[.71,.24,.76],'chassis','grip','ribbed',('x',-17))
    box('guard_forward',[7.72,7.85,6.05],[8.28,8.90,6.26],'chassis','guard','panel')
    box('guard_lower',[7.72,7.78,6.13],[8.28,8.00,7.57],'chassis','guard','panel')
    center('guard_rear_curve',[8,8.18,7.55],[.56,.70,.20],'chassis','guard','panel',('x',-22))
    center('trigger',[8,8.57,7.04],[.13,.51,.16],'steel','guard','panel',('x',20))
    # Stock comb + lower diagonal brace around an open thumb/stock aperture.
    box('stock_wrist',[7.64,9.32,8.11],[8.36,10.28,10.12],'chassis','stock','ribbed')
    box('stock_comb',[7.56,9.90,9.75],[8.44,10.45,13.18],'burgundy','stock','armor')
    center('stock_bottom_brace',[8,9.06,11.30],[.79,.42,3.65],'chassis','stock','ribbed',('x',26))
    box('stock_heel',[7.50,7.10,12.91],[8.50,10.29,13.30],'burgundy','stock','armor')
    box('stock_butt',[7.48,7.006180985632241,13.27],[8.52,10.25,13.5],'rubber','stock','butt')
    for side in (-1,1):
        center(f'stock_upper_bevel_{side}',[8+side*.43,10.21,11.50],[.19,.44,3.33],'burgundy_edge','stock','armor',('z',side*26))
    # Open iron sight in front of stock; window is structural, never alpha.
    box('rear_sight_base',[7.65,10.28,8.90],[8.35,10.43,9.32],'steel','sight','ring')
    for side in (-1,1):
        center(f'rear_sight_ear_{side}',[8+side*.25,10.57,9.11],[.14,.32,.22],'steel','sight','ring')
    # Scope two proper mounts; upper hood protects a recessed cyan objective.
    for i,z in enumerate((2.70,5.72)):
        center(f'scope_mount_{i}',[8,10.75,z],[.64,.82,.48],'chassis','scope','ring')
        center(f'hood_saddle_{i}',[8,10.89,z],[1.50,.22,.48],'chassis','scope','ring')
    tube('scope_body',11.16,-.55,6.37,.48,.19,'chassis','scope','scope')
    tube('objective_rim',11.16,-.74,-.38,.52,.16,'chassis','scope','ring')
    center('front_lens',[8,11.16,-.33],[.66,.66,.07],'lens','scope','lens')
    tube('eyepiece',11.16,6.10,7.52,.40,.15,'rubber','scope','ribbed')
    center('back_lens',[8,11.16,7.20],[.46,.46,.07],'lens','scope','lens')
    # Five longitudinal facets form a broad curved hood, rather than stacked plates.
    tube('scope_hood',11.16,-1.314434,-.56,.8020891882,.15,'burgundy','scope','hood',facets=(0,1,2,6,7))
    tube('scope_hood_long',11.16,-.60,6.48,.8020891882,.15,'burgundy','scope','hood',facets=(0,1,2,6,7))
    # Scope adjustment knob has real depth; concentric rings authored in UV.
    center('scope_adjustment',[7.35,10.94,2.73],[.35,.45,.47],'brass','scope','dial',('x',45))
    inputs=[BASE,W30,REFERENCES,HELPER,ASSET+'textures/item/weapon/w30/bite_of_the_fox.png']
    raw_inputs=[PHOTO,RAW/'Bite of the Fox.fbx',RAW/'Bite of the Fox.blend',RAW/'6902eb80_Diffuse.png',RAW/'86b0eb80_Diffuse.png',RAW/'fc6ba480.png']
    ref=next(x for x in json.loads((ROOT/REFERENCES).read_bytes()) if x['id']=='bite_of_the_fox')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return dict(id='bite_of_the_fox',revision='W134',method='authored opaque semantic volumes + authored face UV; no mesh/voxel transplant',
        source=meta,source_basis='native = raw[X,Z,Y] * source scale + source anchor; verified all selected bounds and 30932 triangles',
        default_photo=ref,palette=PALETTE,parts={'full':specs},atlas=dict(size=EDGE,gutter=2,texels_per_unit=23),
        identity=['burgundy armor / black ribbed chassis / brass studs','long hooded scope and cyan recessed objective',
                  'open box brake / sweeping lower blade','skeleton stock / open guard / offset bolt'],
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=['CPU art render only; native parser/pack/first-third person/ADS/reload/display QA pending master.',
                     'Default-photo palette is authored, not an exact dye shader reconstruction.',
                     'Raw neutral diffuse is shown on source only; sculpted curves and metallic response simplified.'])

class Paint:
    def tile(self,spec,face,w,h):
        u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
        mat=spec['material']; motif=spec['motif']
        rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
        rgb*= (.93+.14*np.exp(-((v-.28)/.29)**2))[:,:,None]
        edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
        rgb[edge<1.0]*=.64;rgb[(edge>=1)&(edge<2)]*=1.28
        side=face in ('east','west')
        # restrained, coherent engraved borders; hand-authored no random noise.
        if motif in ('armor','hood','blade'):
            line=(abs(v-(.78-.12*u))<.014)&(u>.07)&(u<.94)
            rgb[line]*=.48
            rgb[(abs(v-(.74-.12*u))<.010)&(u>.08)&(u<.94)]*=1.32
            # Sparse small edge chips, not baked whole-source grime.
            chips=((np.sin(u*71+v*19)>.94)&(edge<2.4))
            rgb[chips]=[139,128,114]
            if side and motif=='armor':
                for x in (.13,.86):
                    rr=((u-x)*w)**2+((v-.22)*h)**2
                    rgb[rr<2.5**2]=[108,106,96];rgb[rr<1.1**2]=[30,29,27]
            if motif=='blade':
                rgb[v>.78]*=1.39
        if motif in ('ribbed','grip','butt','magazine'):
            # Real body thickness; fine crosswise ribs live entirely in UV.
            stripes=np.mod(v*max(4,h/5),1)
            rgb[stripes<.17]*=.55;rgb[(stripes>.17)&(stripes<.30)]*=1.30
            if motif=='magazine':
                rgb[(abs(u-.19)<.025)|(abs(u-.81)<.025)]*=.50
        if motif=='tab' and side:
            # Broad plate + one brass rivet with dark socket in the face paint.
            rr=((u-.50)/.17)**2+((v-.53)/.17)**2
            rgb[rr<1.5]=[24,21,20];rgb[rr<1]=[177,128,54];rgb[rr<.32]=[220,176,91]
            rgb[(rr<.10)&(v>.50)]=[96,65,29]
        if motif=='barrel' and side:
            rgb[(v>.73)&(v<.80)]*=.48
        if motif=='brake':
            rgb[(u>.12)&(u<.88)&(abs(v-.23)<.02)]*=1.25
        if motif=='dial' and side:
            rr=((u-.5)*2)**2+((v-.5)*2)**2
            rgb[(rr>.40)&(rr<.62)]*=.43;rgb[rr<.08]*=1.3
        if motif=='lens' and face in ('north','south'):
            rr=((u-.50)/.50)**2+((v-.50)/.50)**2
            rgb[:]=[10,28,35]
            rgb+=np.clip(1-rr,0,1)[:,:,None]*[0,65,79]
            glint=np.exp(-(((u-.27)/.10)**2+((v-.29)/.21)**2))
            rgb+=glint[:,:,None]*[47,110,122]
        return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_models(d):
    atlas=Image.new('RGBA',(EDGE,EDGE));paint=Paint(); tiles=[]
    for spec in d['parts']['full']:
        e=spec['geometry'];v=vertices(e)
        for face,ix in FACES.items():
            ps=v[list(ix)];w=max(6,min(256,math.ceil(np.linalg.norm(ps[1]-ps[0])*23)));h=max(6,min(256,math.ceil(np.linalg.norm(ps[3]-ps[0])*23)))
            tiles.append((spec,face,w,h))
    tiles.sort(key=lambda t:(-t[3],-t[2],t[0]['geometry']['name'],t[1]))
    x=y=2; row=0;uvmap={};islands=[]
    for s,f,w,h in tiles:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('atlas overflow')
        tile=paint.tile(s,f,w,h);padded=Image.fromarray(np.pad(np.asarray(tile),((2,2),(2,2),(0,0)),mode='edge'))
        atlas.paste(padded,(x-2,y-2));uvmap[(s['geometry']['name'],f)]=[q*16/EDGE for q in (x,y,x+w,y+h)]
        islands.append(dict(element=s['geometry']['name'],face=f,rect=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    es=[]
    for s in d['parts']['full']:
        e=copy.deepcopy(s['geometry']);e['faces']={f:dict(uv=uvmap[(e['name'],f)],texture='#0') for f in FACES};es.append(e)
    model=dict(credit='W134 Bite of the Fox / authored semantic solid remodel / offline art',textures={'0':'destiny:item/weapon/w123/bite_of_the_fox','particle':'destiny:item/weapon/w123/bite_of_the_fox'},elements=es,display=json.loads((ROOT/BASE).read_bytes())['display'])
    d['atlas'].update(islands=islands,used_height=y+row+2)
    return atlas,model

def inspection(d,model,atlas):
    def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w134:bite_of_the_fox:'+n))
    es=[];groups={s['geometry']['name']:s['group'] for s in d['parts']['full']};out={}
    for e in model['elements']:
        b=copy.deepcopy(e);r=b.pop('rotation',{});b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,origin=r.get('origin',[8,8,8]),rotation=[r.get(a,0) for a in 'xyz'])
        for f in b['faces'].values():f['texture']=0;f['uv']=[q*EDGE/16 for q in f['uv']]
        es.append(b);out.setdefault(groups[e['name']],[]).append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Bite of the Fox W134 | CPU art inspection',resolution={'width':EDGE,'height':EDGE},elements=es,
        outliner=[dict(name=g,uuid=uid(g),origin=[8,8,8],rotation=[0,0,0],children=ids,export=True) for g,ids in out.items()],
        textures=[dict(name='bite_of_the_fox.png',id='0',uuid=uid('texture'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=model['display'],destiny_w134=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],rotationOrder='RzRyRx',candidate='FULL ONLY'))

def source_triangles(meshes):
    # Material-to-albedo correspondence recorded in original W30 audit; glass
    # rear has no albedo. Its explicit neutral tint is not default shader recovery.
    textures={n:np.asarray(Image.open(RAW/f).convert('RGBA')) for n,f in [('Main','6902eb80_Diffuse.png'),('Scope','86b0eb80_Diffuse.png'),('Scope Front Glass','fc6ba480.png')]}
    textures['Scope Back Glass']=np.array([[[25,56,63,255]]],np.uint8)
    out=[]
    for m in meshes:
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);length=np.linalg.norm(n)
            if length>1e-10:out.append((ps,uv,textures[m['material']],n/length))
    return out

def comparison(d,meshes,atlas,model):
    w,h=1000,320;sheet=Image.new('RGB',(3000,1820),'#161e28');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4e6e8',font_size=size)
    label(24,14,'BITE OF THE FOX / W134 / semantic solid remodel / CPU ART ONLY',30)
    photo=Image.open(PHOTO).convert('RGB').crop((0,300,1902,840));photo.thumbnail((1900,340));sheet.paste(photo,(20,60))
    label(1930,90,'Default photo: burgundy / charcoal / brass',24)
    label(1930,135,'Original FBX selected: 30,932 triangles',23)
    label(1930,180,'New: %d opaque cuboids, FULL only'%len(model['elements']),23)
    label(1930,225,'No native game / parser acceptance claimed',21)
    label(24,410,'RAW FBX / neutral undyed diffuse')
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/bite_of_the_fox.png'))
    label(1024,410,'CANONICAL / %d cuboids / not raw FBX'%len(old['elements']))
    label(2024,410,'W134 / authored default-photo face paint')
    tris=[source_triangles(meshes),model_triangles({'old':old},oldtex),model_triangles({'new':model},atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('FRONT OBLIQUE',[1,.50,-.60]),('REAR OBLIQUE',[-1,.42,.60])]):
        extent=frame(points,cam,w,h)
        for col,ts in enumerate(tris):
            im,_=render(ts,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,450+row*h));label(col*w+18,462+row*h,name,17)
    specs=d['parts']['full']
    for i,(group,cam) in enumerate([('muzzle',[.25,.15,-1]),('guard',[1,.25,-.25]),('stock',[1,.25,.32]),('scope',[.35,.18,-1])]):
        names={s['geometry']['name'] for s in specs if s['group']==group};es=[e for e in model['elements'] if e['name'] in names];ps=np.concatenate([vertices(e) for e in es])
        im,_=render(model_triangles({'detail':{'elements':es}},atlas),cam,frame(ps,cam,750,270),(750,270));sheet.paste(im,(i*750,1430));label(i*750+16,1440,group.upper()+' / geometry depth',18)
    thumb=atlas.copy();thumb.thumbnail((95,95));sheet.paste(thumb,(2870,1710))
    label(24,1728,'Same source frame / same camera and scale within each full row. Raw = original source geometry, canonical = existing cuboid model.',19)
    label(24,1762,'Native pending master: parser, pack loading, first/third person, ADS/reload and 10-20 simultaneous displays. Atlas embedded in editable BB.',18)
    return png(sheet)

def review_text(d,counts):
    return f"""# Bite of the Fox W134 — CPU art review

Actual supplied default photo opened with image tool: `{PHOTO}`. Bungie item 1403800851, source `{d['default_photo']['screenshot']}`. Photo SHA-256 `{d['default_photo']['sha256']}` matches W31 references.json.

The authored assembly has **{counts['full']} opaque cuboids**, {counts['triangles']} emitted contour/triangle elements, {counts['combined']} combined (limit 1000). FULL ONLY candidate; no invented reload/body/magazine split. Broad filled forearm, receiver, grip, stock comb and blade carry the form. Barrel walls, brake jaws and webs, guard segments, open stock brace and hooded scope create real empty spaces and depth. Brass tab rivets, armor seam lines, edge chips and chassis/grip ribs use clean independent face paint. The six small top pins contribute the observed silhouette rather than a field of bolt cubes.

Original retained FBX object names, 30,932 triangles, measured bounds, exact source scale {d['source']['scale']} and anchor {d['source']['anchor']} were verified against W30 metadata. The axis is native = raw [X,Z,Y] times source scale plus anchor, established from this weapon, not borrowed from Beloved. Canonical display is copied byte-equivalently as JSON values. Native -Z muzzle direction, -15.5 forward blade endpoint, 13.5 butt endpoint and source hand frame are retained. The cylindrical bore is centered at native [8,9.89]. Surface curvature is deliberately simplified; this is not a vertex-identical source reconstruction.

`comparison.png` distinguishes the actual original FBX with neutral undyed albedo (Main 6902eb80, Scope 86b0eb80, front glass fc6ba480; rear glass has no supplied albedo and uses an explicit neutral tint), the existing canonical 223-cuboid model, and the new authored default-photo palette. Main and Scope material correspondences agree with the read-only original W30 audit. No shader script or blend was executed. Source meshes are rendered for reference only, never used as design cubes/voxel islands. Raw diffuse is not a recovered default shader. New UV paint is authored from the photo, not transplanted source mesh islands; brass/burgundy/charcoal are an approximation, not exact shader/PBR recovery.

1024-square RGBA atlas: six unique face islands per solid, 2-pixel extruded gutters, opaque used pixels. No alpha silhouette shell or transparency hole. Inspection BB embeds precisely that atlas and editable semantic cube groups; no GUI/DCC was opened. Side/front/rear CPU rows and muzzle/guard/stock/optic details support a limited offline art review. Small sculpted irregular edges and specular metal behavior remain simplified.

Validation: targeted Python unittest plus generator --verify. These cover scope/schema, combined count, source basis/bounds and unchanged display, structural voids/depth, UV/alpha/gutters, hashes, editable BB parity, and exact deterministic regeneration. Native 26.3 parser/pack, holding/ADS/reload, audio/combat timing and 10–20 simultaneous displays remain pending master. Existing item graph and shared registration are untouched.
"""

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_models(d)
    groups={}
    for s in d['parts']['full']:groups[s['group']]=groups.get(s['group'],0)+1
    counts=dict(full=len(model['elements']),triangles=0,combined=len(model['elements']),by_semantic_group=groups)
    ps=np.concatenate([vertices(e) for e in model['elements']])
    outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    manifest=dict(id=d['id'],revision='W134',counts=counts,assembled_elements=counts['combined'],max_assembled_elements=1000,opaque_cuboids=counts['full'],alpha_elements=0,emitted_faces=6*counts['full'],texture_size=[EDGE,EDGE],
        actual_bounds=[ps.min(0).tolist(),ps.max(0).tolist()],source_bounds=meta['model_bounds'],source_scale=meta['scale'],source_anchor=meta['anchor'],source_axis=meta['source_axis'],source_triangles=meta['source_triangles'],canonical_display_exact=True,native_accepted=False,candidate='FULL ONLY',
        default_photo_sha256=d['default_photo']['sha256'],input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],generator_sha256=sha(Path(__file__).read_bytes()),
        output_sha256={p:sha(b) for p,b in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest);return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args();outputs=generate()
    allowed={ART+n for n in ('design.json','manifest.json','review.md','inspection.bbmodel','comparison.png')}|{MODEL,TEXTURE}
    assert set(outputs)==allowed
    for rel,b in outputs.items():
        p=ROOT/rel
        if args.verify:assert p.is_file() and p.read_bytes()==b,'Regeneration differs: '+rel
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' 7 owned artifacts; {m["counts"]}; {m["emitted_faces"]} faces')

if __name__=='__main__':main()
