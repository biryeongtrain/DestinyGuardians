#!/usr/bin/env python3
"""W128 Chattering Bone: authored solid volumes, face atlas, offline evidence only."""
import argparse
import base64
import copy
import json
import math
from pathlib import Path
import sys
import uuid
import numpy as np
from PIL import Image, ImageDraw

# Read-only W126 inert FBX reader, cuboid math and software rasterizer.
import generate_surface_w123_beloved as helper
from generate_surface_w123_beloved import encode, sha, png, vertices, rotation, FACES, NORMALS
ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/chattering_bone/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/pulse_rifle/chattering_bone.json'
MODEL = ASSET+'models/weapon_surface_w123/chattering_bone.json'
TEXTURE = ASSET+'textures/item/weapon/w123/chattering_bone.png'
REPORT = 'docs/qa/2026-10-26/w128/chattering_bone-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/chattering_bone/extracted/Chattering Bone')
W31 = Path('/tmp/destiny-weapons-w31')
EDGE = 1024
PALETTE = {'ivory':[211,201,171], 'edge':[227,218,188], 'carving':[153,135,99],
           'violet':[37,28,62], 'steel':[24,28,43], 'gold':[175,151,99], 'rubber':[20,23,33]}

def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w128:chattering_bone:'+name))

def source_meshes():
    meta = json.loads((ROOT/'art/blockbench/weapons/w30/chattering_bone.bbmodel').read_bytes())['destiny_w30']
    path = RAW/'Chattering Bone.fbx'
    assert sha(path.read_bytes()) == meta['source_files']['Chattering Bone/Chattering Bone.fbx']
    roots = helper.parse_fbx(path)
    objects = next(n[2] for n in roots if n[0]=='Objects')
    links = [n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models = {n[1][0]:n for n in objects if n[0]=='Model'}
    meshes=[]
    for node in objects:
        if node[0]!='Geometry': continue
        m = models[next(parent for child,parent in links if child==node[1][0])]
        name = m[1][1].split('\x00')[0]; idx=int(name[5:9])
        if idx==6: continue  # Original reticle plane, not a physical volume.
        props={p[1][0]:p[1][4:] for c in m[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
        assert props['Lcl Scaling']==[100,100,100]
        cs={c[0]:c for c in node[2]}
        raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        v=np.c_[-raw[:,1],raw[:,2],-raw[:,0]]*meta['scale']+meta['anchor']
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        vals={c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])]
        uv[:,1]=1-uv[:,1]
        fs=[];us=[];face=[];ui=[]
        for k,i in enumerate(cs['PolygonVertexIndex'][1][0]):
            face.append(i if i>=0 else -i-1);ui.append(k)
            if i<0:
                for j in range(1,len(face)-1):
                    fs.append([face[0],face[j],face[j+1]]);us.append(uv[[ui[0],ui[j],ui[j+1]]])
                face=[];ui=[]
        meshes.append(dict(name=name,vertices=v,faces=np.array(fs),uv=np.array(us),material='Scope' if idx>=7 else 'Barrel'))
    pts=np.concatenate([m['vertices'] for m in meshes])
    # W30 blend frame has a 0.0005-source-unit lower heel adjustment vs FBX.
    assert np.allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=.013)
    meta=copy.deepcopy(meta)
    meta['fbx_reference_triangles']=sum(len(m['faces']) for m in meshes)
    meta['fbx_reference_bounds']=[pts.min(0).tolist(),pts.max(0).tolist()]
    return meshes,meta

def make_design(meta):
    specs=[]
    def box(name,c,size,mat,group,motif='plain',turn=None):
        e=dict(name=name,**{'from':[round(a-b/2,6) for a,b in zip(c,size)],'to':[round(a+b/2,6) for a,b in zip(c,size)]})
        if turn:
            axis,angle=turn;e['rotation']=dict(origin=c,x=0,y=0,z=0);e['rotation'][axis]=round(angle,6)
        specs.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def beam(name,a,b,width,thick,mat,group,motif='plain',x=8):
        # Endpoints are (Y,Z); rotation preserves long uninterrupted surfaces.
        dy=b[0]-a[0];dz=b[1]-a[1]
        box(name,[x,(a[0]+b[0])/2,(a[1]+b[1])/2],[width,thick,math.hypot(dy,dz)],mat,group,motif,('x',-math.degrees(math.atan2(dy,dz))))
    def tube(name,y,z0,z1,r,wall,mat,group,n=8):
        for i in range(n):
            angle=i*360/n;rad=math.radians(angle);rr=r-wall/2
            box(name+'_'+str(i),[8-rr*math.sin(rad),y+rr*math.cos(rad),(z0+z1)/2],
                [2*r*math.tan(math.pi/n)+.008,wall,z1-z0],mat,group,'tube',('z',angle))
    # Violet barrel: hollow walls and open fork ahead of the deep bore.
    tube('barrel',11.12,-8.12,-4.40,.47,.15,'violet','barrel')
    for side in (-1,1):
        x=8+side*.37
        beam('fork_upper_'+str(side),(11.45,-8.65),(11.40,-7.96),.20,.17,'violet','muzzle',x=x)
        beam('fork_lower_'+str(side),(10.69,-8.65),(10.81,-7.96),.20,.17,'violet','muzzle',x=x)
    box('bore_back',[8,11.12,-4.36],[.64,.64,.08],'steel','barrel')
    # Long solid inner action: visibly narrower than sculpted ivory frame.
    box('forearm_violet_core',[8,10.93,-.20],[1.05,1.85,8.20],'violet','forearm','filaments')
    box('receiver_violet_core',[8,11.14,5.75],[1.04,1.68,4.0],'violet','receiver','filaments')
    box('receiver_lower_spine',[8,9.95,5.75],[1.10,.53,4.15],'ivory','receiver','carved')
    beam('top_continuous_spine',(12.22,-4.65),(12.34,6.90),1.05,.24,'edge','forearm','carved')
    beam('lower_continuous_keel',(9.58,-4.66),(9.76,3.68),1.10,.33,'ivory','forearm','carved')
    # Raised side frame has real thickness and diagonal parallax, not alpha sheets.
    for side in (-1,1):
        x=8+side*.59
        beam('upper_shell_'+str(side),(11.86,-4.50),(12.02,4.05),.34,.89,'ivory','forearm','carved',x)
        beam('lower_shell_'+str(side),(9.76,-4.45),(9.92,3.68),.34,.61,'ivory','forearm','carved',x)
        beam('swept_diagonal_rib_'+str(side),(9.98,-.87),(11.99,2.88),.37,.68,'ivory','forearm','carved',x)
        beam('nose_cheek_top_'+str(side),(11.58,-4.68),(12.04,-4.36),.29,.44,'ivory','forearm','carved',x)
        beam('nose_cheek_bottom_'+str(side),(9.72,-4.60),(10.10,-4.68),.29,.35,'ivory','forearm','carved',x)
        # Broad swept receiver ribs leave the purple upper inset clearly exposed.
        beam('receiver_upper_rib_'+str(side),(12.20,3.98),(12.06,7.12),.29,.39,'ivory','receiver','carved',x)
        beam('receiver_low_rib_'+str(side),(10.05,3.90),(10.48,7.94),.34,.88,'ivory','receiver','carved',x)
        beam('receiver_rising_wrist_'+str(side),(10.48,7.70),(11.55,9.91),.34,.77,'ivory','receiver','carved',x)
        beam('receiver_swept_arch_'+str(side),(12.06,7.12),(11.70,9.12),.34,.56,'ivory','receiver','carved',x)
    # Continuous wrist closes the source's solid receiver behind its violet inset.
    beam('receiver_wrist_core',(10.33,8.08),(11.13,10.31),1.12,.85,'ivory','receiver','carved')
    beam('grip_upper_socket',(9.92,8.29),(10.50,9.63),1.03,.63,'ivory','receiver','carved')
    # Broad shoulder chamfers change the top cross section under oblique light.
    for side in (-1,1):
        box('shell_upper_chamfer_'+str(side),[8+side*.58,12.15,-.29],[.35,.35,8.51],'edge','forearm','carved',('z',45*side))
        box('shell_lower_chamfer_'+str(side),[8+side*.58,9.73,-.42],[.32,.32,8.44],'ivory','forearm','carved',('z',45*side))
    # Nose open yoke spans width; no opaque cap across the barrel exit.
    box('nose_upper_bridge',[8,12.12,-4.68],[1.41,.39,.34],'ivory','forearm','carved')
    box('nose_lower_bridge',[8,9.71,-4.68],[1.41,.39,.34],'ivory','forearm','carved')
    # Small metallic seam is structural around body, not many coplanar ornaments.
    for side in (-1,1):
        box('joint_band_'+str(side),[8+side*.754,11.08,3.83],[.10,2.40,.23],'gold','receiver','band')
    box('joint_top',[8,12.31,3.83],[1.48,.12,.23],'gold','receiver','band')
    box('joint_bottom',[8,9.87,3.83],[1.48,.12,.23],'gold','receiver','band')
    # Full-depth stock carved from broad volumes, tapering in plan and elevation.
    beam('stock_comb',(11.74,9.10),(11.60,15.82),1.31,.53,'ivory','stock','stock')
    box('stock_main',[8,10.73,12.96],[1.36,1.58,5.90],'ivory','stock','stock')
    beam('stock_lower_front',(10.04,10.00),(8.75,12.65),1.25,.62,'ivory','stock','stock')
    box('stock_lower_rear',[8,9.48,14.04],[1.24,1.31,3.26],'ivory','stock','stock')
    beam('stock_rear_slope',(8.74,14.90),(11.62,16.08),1.17,.49,'ivory','stock','stock')
    beam('butt_blade',(7.00,14.67),(11.56,16.24),.67,.23,'steel','stock','butt')
    beam('butt_bone_edge',(7.00,14.61),(11.56,16.13),.81,.14,'ivory','stock','butt')
    for side in (-1,1):
        box('stock_top_chamfer_'+str(side),[8+side*.59,11.62,12.91],[.31,.31,5.84],'edge','stock','stock',('z',45*side))
        beam('stock_wrist_flare_'+str(side),(10.16,10.0),(10.78,11.54),.30,.75,'ivory','stock','stock',8+side*.57)
    # Integral magazine is behind the grip; this weapon has only a full output.
    box('magazine_root',[8,8.98,11.75],[.79,.95,1.87],'violet','magazine','filaments',('x',15))
    box('magazine_main',[8,7.93,11.91],[.86,1.91,2.12],'violet','magazine','filaments',('x',15))
    box('magazine_foot',[8,6.89,12.18],[.92,.17,2.26],'edge','magazine','band',('x',15))
    # Pistol grip near source origin: thick solid surfaces, original wrist/heel.
    beam('grip_wrist',(9.74,8.39),(8.98,8.05),.87,.87,'violet','grip','filaments')
    beam('grip_main',(9.03,8.10),(7.29,9.24),.99,.98,'violet','grip','filaments')
    beam('grip_heel',(7.28,9.23),(6.67,8.31),1.01,.43,'violet','grip','filaments')
    # Open teardrop guard is built around the void, never masked by alpha.
    beam('guard_front_root',(9.65,3.86),(8.69,4.84),.73,.38,'ivory','guard','carved')
    beam('guard_front',(8.69,4.84),(7.22,6.01),.73,.40,'ivory','guard','carved')
    beam('guard_lower_front',(7.22,6.01),(6.59,6.85),.77,.39,'ivory','guard','carved')
    beam('guard_lower_arc',(6.59,6.85),(6.40,7.68),.80,.40,'ivory','guard','carved')
    beam('guard_heel_join',(6.40,7.68),(6.78,8.47),.82,.39,'ivory','guard','carved')
    # Trigger curls inside the larger bow, independently visible through it.
    beam('trigger_shank',(9.83,6.67),(9.18,6.94),.22,.20,'steel','trigger')
    beam('trigger_tip',(9.18,6.94),(8.96,6.66),.22,.18,'gold','trigger')
    # Small open optic hood: two faceted open rings + deep connecting violet tube.
    box('optic_rail',[8,12.47,6.63],[.56,.15,3.21],'steel','optic','rail')
    box('optic_pedestal',[8,12.66,7.18],[.53,.31,1.24],'gold','optic','band')
    tube('optic_hood',12.99,6.84,7.75,.46,.105,'violet','optic')
    tube('optic_rear_rim',12.99,7.75,8.02,.48,.10,'edge','optic')
    # No opaque lens spanning optic opening; inner depth and rim are actual walls.
    return dict(id='chattering_bone',revision='W128',family='pulse_rifle',
        method='Hand-authored semantic opaque cuboids; source meshes are reference-only',
        source=meta,palette=PALETTE,parts={'full':specs},atlas=dict(size=EDGE,gutter=2,texels_per_unit=23),
        identity=['Warm carved ivory shell','Violet starfield insets with blue filaments','Long forked barrel and open nose yoke',
                  'Hollow raised optic hood','Large open teardrop guard and rear magazine'],
        frame=dict(anchor=meta['anchor'],source_scale=meta['scale'],muzzle_axis='-Z',grip_policy='Source wrist and heel coordinates; no recentering',display='Exact canonical display copy'),
        reload_policy='Full only; no custom moving reload split. Generic graphs and ADS inherit full at master integration.',
        limitations=['Offline rasterizer only; native 26.3/parser/pack/held/ADS/reload/10-20 display QA pending master.',
                     'Faceted interpretation of organic ivory curves; no exact source mesh equivalence.',
                     'Static violet filaments approximate parallax material; no animated iridescence/PBR.'])

def reference_relief(meshes):
    """Two continuous side relief maps, sampled from actual inert FBX/DDS.

    Only the source's shallow ivory carving luminance is used; geometry,
    source islands, source shading and undyed RGB are not emitted.
    """
    width,height=850,264
    tex=np.asarray(Image.open(RAW/'ChatteringBoneBarrel_Diffuse.dds').convert('RGB'))/255.
    maps={}
    for side in (-1,1):
        relief=np.full((height,width),.52);depth=np.full((height,width),-np.inf)
        for m in meshes:
            if m['material']!='Barrel':continue
            for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
                screen=np.c_[(ps[:,2]+5)*40,(12.6-ps[:,1])*40]
                x0=max(0,int(np.floor(screen[:,0].min())));x1=min(width-1,int(np.ceil(screen[:,0].max())))
                y0=max(0,int(np.floor(screen[:,1].min())));y1=min(height-1,int(np.ceil(screen[:,1].max())))
                if x1<x0 or y1<y0:continue
                a,b,c=screen;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den)<1e-10:continue
                x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
                wa=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
                wb=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;wc=1-wa-wb
                z=(wa*ps[0,0]+wb*ps[1,0]+wc*ps[2,0])*side
                q=wa[:,:,None]*uv[0]+wb[:,:,None]*uv[1]+wc[:,:,None]*uv[2]
                sample=tex[np.clip((q[:,:,1]*2048).astype(int),0,2047),np.clip((q[:,:,0]*2048).astype(int),0,2047)]
                visible=(wa>=0)&(wb>=0)&(wc>=0)&(z>=depth[y0:y1+1,x0:x1+1])
                relief[y0:y1+1,x0:x1+1][visible]=(sample@np.array([.2126,.7152,.0722]))[visible]
                depth[y0:y1+1,x0:x1+1][visible]=z[visible]
        maps[side]=relief
    return maps

class Paint:
    def __init__(self,meshes):
        self.filaments=np.asarray(Image.open(RAW/'ChatteringBoneParallax_Diffuse.dds').convert('RGB'))/255.
        self.stars=np.asarray(Image.open(RAW/'DetailTextures/Chattering-Bone/3104558709_comet_2_star_detail_dif.png').convert('RGB'))/255.
        self.relief=reference_relief(meshes)
    def tile(self,spec,face,w,h):
        u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
        pts=vertices(spec['geometry'])[list(FACES[face])]
        pos=((1-u)*(1-v))[:,:,None]*pts[0]+(u*(1-v))[:,:,None]*pts[1]+(u*v)[:,:,None]*pts[2]+((1-u)*v)[:,:,None]*pts[3]
        yy,zz=pos[:,:,1],pos[:,:,2]
        mat=spec['material'];rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
        edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
        rgb *= (.96+.055*np.sin(v*math.pi))[:,:,None]
        rgb[edge<.65]*=.77
        rgb[(edge>=.65)&(edge<1.4)]*=1.055
        if mat in ('ivory','edge'):
            if face in ('west','east'):
                # Continuous world-space original engraving, separately for each side.
                relief=self.relief[-1 if face=='west' else 1]
                rx=np.clip(((zz+5)*40).astype(int),0,relief.shape[1]-1)
                ry=np.clip(((12.6-yy)*40).astype(int),0,relief.shape[0]-1)
                q=relief[ry,rx]
                rgb*=np.clip(1+(q-.52)*1.4,.78,1.08)[:,:,None]
                if spec['group']=='stock':
                    window=(zz>13.42)&(zz<14.48)&(yy>10.48)&(yy<10.68)
                    rgb[window]=[40,36,66]
        if mat=='violet':
            # Original parallax map is a channel mask, not an RGB rainbow skin.
            tx=((zz+8.7)/27.0+pos[:,:,0]*.013)%1;ty=((yy-6.1)/7.5+pos[:,:,0]*.01)%1
            q=self.filaments[(ty*512).astype(int)%512,(tx*512).astype(int)%512]
            filament=q.max(2)
            stars=self.stars[((yy*85)%self.stars.shape[0]).astype(int),((zz*85)%self.stars.shape[1]).astype(int)].mean(2)
            glint=np.clip((stars-.77)*.6,0,.055)
            rgb+=glint[:,:,None]*[64,56,95]
            rgb+=(np.exp(-((v-.28)/.23)**2))[:,:,None]*[10,6,18]
            rgb+=filament[:,:,None]*[65,99,138]
        return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,dtype='uint8')]))

def compile_model(d,meshes):
    paint=Paint(meshes);atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));tiles=[]
    for s in d['parts']['full']:
        vv=vertices(s['geometry'])
        for f,inds in FACES.items():
            p=vv[list(inds)];w=max(5,min(300,math.ceil(np.linalg.norm(p[1]-p[0])*23)));h=max(5,min(300,math.ceil(np.linalg.norm(p[3]-p[0])*23)))
            tiles.append((s,f,w,h))
    tiles.sort(key=lambda t:(-t[3],-t[2],t[0]['geometry']['name'],t[1]))
    x=y=2;row=0;uv={};islands=[]
    for s,f,w,h in tiles:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        assert y+h+2<=EDGE,'Atlas overflow'
        tile=paint.tile(s,f,w,h);pad=Image.fromarray(np.pad(np.asarray(tile),((2,2),(2,2),(0,0)),mode='edge'));atlas.paste(pad,(x-2,y-2))
        key=(s['geometry']['name'],f);uv[key]=[q*16/EDGE for q in (x,y,x+w,y+h)]
        islands.append(dict(element=key[0],face=f,rect=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    elements=[]
    for s in d['parts']['full']:
        e=copy.deepcopy(s['geometry']);e['faces']={f:dict(uv=uv[(e['name'],f)],texture='#0') for f in FACES};elements.append(e)
    model=dict(credit='W128 Chattering Bone | authored solid anatomy and face UV',
        textures={'0':'destiny:item/weapon/w123/chattering_bone','particle':'destiny:item/weapon/w123/chattering_bone'},
        elements=elements,display=json.loads((ROOT/BASE).read_bytes())['display'])
    d['atlas']['islands']=islands;d['atlas']['used_height']=y+row+2
    return atlas,model

def inspection(d,model,atlas):
    es=[];groups={}
    for s,e in zip(d['parts']['full'],model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation',{});b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,
            origin=r.get('origin',[8,8,8]),rotation=[r.get(a,0) for a in 'xyz'])
        for f in b['faces'].values():f['texture']=0;f['uv']=[q*EDGE/16 for q in f['uv']]
        es.append(b);groups.setdefault(s['group'],[]).append(b['uuid'])
    return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name='Chattering Bone W128 / full-only offline inspection',
        resolution=dict(width=EDGE,height=EDGE),elements=es,
        outliner=[dict(name=g,uuid=uid('group:'+g),origin=[8,8,8],rotation=[0,0,0],children=cs,export=True) for g,cs in groups.items()],
        textures=[dict(name='chattering_bone.png',id='0',uuid=uid('texture'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=model['display'],
        destiny_w128=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale'],reloadPolicy=d['reload_policy']))

def source_triangles(meshes):
    textures={m:np.asarray(Image.open(RAW/('ChatteringBone'+m+'_Diffuse.dds')).convert('RGBA')) for m in ('Scope','Barrel')}
    result=[]
    for m in meshes:
        for p,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(p[1]-p[0],p[2]-p[0]);ll=np.linalg.norm(n)
            if ll>1e-10:result.append((p,uv,textures[m['material']],n/ll))
    return result

def comparison(d,meshes,atlas,model):
    w,h=900,335;sheet=Image.new('RGB',(2700,1740),'#151c25');draw=ImageDraw.Draw(sheet)
    def label(x,y,t,size=20):draw.text((x,y),t,fill='#e1e4e9',font_size=size)
    label(20,16,'CHATTERING BONE / W128 / authored solid anatomy / offline inspection',29)
    photo=Image.open(W31/'references/chattering_bone.jpg').convert('RGB').crop((420,175,1900,800));photo.thumbnail((1550,340));sheet.paste(photo,(20,60))
    historical=Image.open(W31/'renders/chattering_bone-after.png').convert('RGB');historical.thumbnail((640,325));sheet.paste(historical,(1840,60))
    label(20,400,'Default-paint photo: ivory shell / violet starfield / blue filaments / hollow optic',20)
    label(1835,400,'W31 historical bake (not palette authority)',18)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/chattering_bone.png'))
    triangles=[source_triangles(meshes),helper.model_triangles({'old':old},oldtex),helper.model_triangles({'full':model},atlas)]
    points=np.concatenate([m['vertices'] for m in meshes]);points=np.concatenate([points]+[vertices(e) for e in model['elements']])
    for col,t in enumerate([f'RAW FBX / {d["source"]["fbx_reference_triangles"]:,} triangles / undyed DDS','LOCAL CANONICAL / 212 cuboids',f'W128 / {len(model["elements"])} opaque cuboids / full only']):label(col*w+15,445,t,21)
    for row,(title,cam) in enumerate([('SIDE',[-1,0,0]),('FRONT OBLIQUE',[-1,.48,-.65]),('REAR OBLIQUE',[1,.40,.60])]):
        extent=helper.frame(points,cam,w,h)
        for col,ts in enumerate(triangles):
            im,_=helper.render(ts,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,480+row*h));label(col*w+15,490+row*h,title,17)
    # Detail views are entire model occlusion, not isolated holes without backing.
    ts=triangles[2]
    for i,(name,lo,hi,cam) in enumerate([
        ('MUZZLE / open bore + nose yoke',[7,9,-9],[9,12.8,-4],[-.50,.25,-1]),
        ('OPTIC / hollow hood',[7.1,12.1,6.5],[8.9,13.6,8.2],[-.35,.18,-1]),
        ('GUARD / real through opening',[7.2,6.1,3.3],[8.8,10.3,10],[-1,.25,-.25])]):
        ps=np.array([[hi[a] if mask>>a&1 else lo[a] for a in range(3)] for mask in range(8)])
        im,_=helper.render(ts,cam,helper.frame(ps,cam,900,215),(900,215));sheet.paste(im,(i*900,1490));label(i*900+12,1497,name,18)
    label(20,1715,'Matched camera and scale per full-model row. Native pack/parser, held views, ADS, generic reload and 10-20 display QA pending master.',18)
    return png(sheet)

def review_text(d,counts):
    return f'''# Chattering Bone W128 art review

Default appearance evidence: W31 reference record for Bungie 568515759, its actual photograph, W31 default dye JSON, the actual raw FBX, Barrel/Scope undyed DDS, parallax map and original star-detail map. W31 palette-overrides contains no Chattering Bone override. Its historical baked render loses violet detail; that bake is shown for context, while the photo establishes the finished ivory/violet/blue appearance.

The remodel emits **{counts['full']} solid opaque cuboids**, full only. Semantic groups: {', '.join(f"{k} {v}" for k,v in counts['groups'].items())}. Magazine is integral geometry within full; no invented split graph or moving reload output. Every box has six authored face UVs, 2px extruded gutters and opaque sampled texels. Wide rails, action volumes, a carved stock and thick grip replace source component/voxel decomposition. The W30 Blender record has 13,882 triangles; the FBX reference has {d['source']['fbx_reference_triangles']:,} triangles after excluding its reticle plane. Both remain offline references and are never emitted.

Identity: long ivory body with diagonal bone ribs and inset violet starfield, narrow forward barrel with forked mouth, small gold seam, high hollow violet optic with ivory rear ring, curved open teardrop guard, rear magazine and swept butt blade. The eight-sided barrel and optic are tangent solid walls with true bores. The forearm nose is an open upper/lower yoke. The guard's interior is empty geometry; no alpha silhouette card is present. Raised ribs have actual thickness beyond the narrower violet action, visible in oblique views.

Paint: ivory and restrained source-backed relief; broad warm highlights; original parallax map channel masks recolored to the photo's fine blue filaments; original star-detail luminance used sparingly. Atlas painting is independent of raw mesh islands. Flowing shallow ivory grooves transfer only the original diffuse carving luminance through two continuous side relief maps; they do not transfer undyed RGB, source mesh islands or source lighting. The stock inset is face paint, not added coplanar cubes. This is a static material approximation; metallic reflection and animated parallax are not reproduced.

Frame retained: source scale {d['source']['scale']}, anchor {d['source']['anchor']}, -Z muzzle, original wrist/heel placement and canonical display dictionary. No global recentering or automatic bounds normalization. Curved organic transitions are intentionally faceted and simplified. The Blender source record differs from raw FBX by about 0.012 native units at the lowest heel; the canonical Blender frame is retained and both bounds are recorded. The comparison uses actual raw-source rasterization, canonical and new geometry in matched side/front-oblique/rear-oblique rows, plus photo and actual new-model depth details. The raw DDS column is clearly undyed.

Offline validation covers actual emitted elements, all-six-face UVs, source/input hashes, atlas gutters, physical open rays through optic/barrel/guard, frame and grip landmarks, inspection parity, full-only output, and byte-identical regeneration. No GUI/DCC/native game/server/Gradle was used. Native 26.3 rotation and parser acceptance, shared registration/ADS inheritance, first/third-person held views, generic reload, and 10-20 simultaneous displays remain pending master. No native success or performance result is claimed.
'''

def provenance():
    rels=[BASE,'art/blockbench/weapons/w30/chattering_bone.bbmodel',ASSET+'textures/item/weapon/w30/chattering_bone.png',
          'art/weapons/w31/references.json','art/weapons/w31/palette-overrides.json','scripts/generate_surface_w123_beloved.py']
    raw=[RAW/'Chattering Bone.fbx',RAW/'ChatteringBoneBarrel_Diffuse.dds',RAW/'ChatteringBoneScope_Diffuse.dds',
         RAW/'ChatteringBoneParallax_Diffuse.dds',RAW/'DetailTextures/Chattering-Bone/3104558709_comet_2_star_detail_dif.png',
         W31/'references/chattering_bone.jpg',W31/'renders/chattering_bone-after.png',W31/'gear-json/chattering_bone.json']
    return {r:sha((ROOT/r).read_bytes()) for r in rels},{str(p):sha(p.read_bytes()) for p in raw}

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d,meshes)
    groups={}
    for s in d['parts']['full']:groups[s['group']]=groups.get(s['group'],0)+1
    counts=dict(full=len(model['elements']),groups=groups)
    inputs,raw_inputs=provenance();d['input_sha256']=inputs;d['raw_input_sha256']=raw_inputs
    outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    points=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id='chattering_bone',revision='W128',counts=counts,assembled_elements=counts['full'],max_assembled_elements=1000,
        emitted_faces=counts['full']*6,opaque_cuboids=counts['full'],alpha_elements=0,mesh_elements=0,outputs='full only',
        source_triangles=meta['source_triangles'],fbx_reference_triangles=meta['fbx_reference_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],source_bounds=meta['model_bounds'],
        actual_bounds=[points.min(0).round(7).tolist(),points.max(0).round(7).tolist()],canonical_display_exact=True,
        native_accepted=False,input_sha256=inputs,raw_input_sha256=raw_inputs,generator_sha256=sha(Path(__file__).read_bytes()),
        output_sha256={p:sha(b) for p,b in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w128/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w128-chattering_bone'))
    assert set(outputs)<=owned
    for rel,data in outputs.items():
        p=ROOT/rel
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+rel
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts; {m["counts"]}')
if __name__=='__main__':main()
