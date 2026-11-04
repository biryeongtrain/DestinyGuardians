#!/usr/bin/env python3
"""Canis Major W149: authored filled solids and opaque face UV. Offline full-only product.
Inert SDNA decoding, no rip-script/shader/DCC execution. Writes only seven owned artifacts.
"""
import argparse, base64, copy, hashlib, io, json, math, re, runpy, struct, subprocess, uuid
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='canis_major'
ART=f'art/weapons/w123/{ID}/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/heavy_grenade_launcher/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
SOURCE=f'art/blockbench/weapons/w30/{ID}.bbmodel'
SCRIPT=f'scripts/generate_surface_w123_{ID}.py'
TEST=f'scripts/qa/test_surface_w149_{ID}.py'
REPORT=f'docs/qa/2026-10-26/w149/{ID}-worker.md'
REFS='art/weapons/w31/references.json'
BATCH='docs/qa/2026-10-26/w149/batch.json'
RAW=Path('/tmp/destiny-weapons-w30/raw/canis_major/extracted')
PHOTO=Path('/tmp/destiny-weapons-w31/references/canis_major.jpg')
HELPER='scripts/generate_surface_w123_beloved.py'
H=runpy.run_path(str(ROOT/HELPER))
FACES=H['FACES']; EDGE=1024
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w149:canis_major:'+n))
def render_element(e):
 e=copy.deepcopy(e)
 if 'rotation' in e:
  r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
 return e
def vertices(e):return H['vertices'](render_element(e))
def model_triangles(m,tex):
 m=copy.deepcopy(m);m['elements']=[render_element(e) for e in m['elements']]
 return H['model_triangles']({'full':m},tex)

class Blend:
    """Inert SDNA reader adapted from W138; reads Blender 2.93 data only. Never imports bpy or source code."""
    def __init__(self,path):
        data=path.read_bytes()
        if data[:4]==b'\x28\xb5\x2f\xfd':
            data=subprocess.check_output(['rtk','proxy','zstd','-dc',str(path)])
        assert data[:12]==b'BLENDER-v293',data[:12]
        self.blocks={};pos=12
        while pos+24<=len(data):
            code,size,addr,dna,count=struct.unpack_from('<4sIQII',data,pos);pos+=24
            raw=data[pos:pos+size];pos+=size
            self.blocks[addr]=(code,dna,count,raw)
            if code==b'DNA1': self.dna=raw
            if code==b'ENDB': break
        d=self.dna;pos=0
        def tag(s):
            nonlocal pos
            assert d[pos:pos+4]==s;(pos:=pos+4)
        def integer():
            nonlocal pos
            v=struct.unpack_from('<I',d,pos)[0];pos+=4;return v
        def strings(n):
            nonlocal pos
            a=[]
            for _ in range(n):
                end=d.index(0,pos);a.append(d[pos:end].decode());pos=end+1
            pos=(pos+3)//4*4;return a
        tag(b'SDNA');tag(b'NAME');names=strings(integer())
        tag(b'TYPE');types=strings(integer());tag(b'TLEN')
        sizes=struct.unpack_from('<'+str(len(types))+'H',d,pos);pos+=2*len(types);pos=(pos+3)//4*4
        tag(b'STRC');n=integer();self.structs=[];self.fields={};self.sizes=dict(zip(types,sizes))
        for _ in range(n):
            ti,nf=struct.unpack_from('<HH',d,pos);pos+=4;fields={};offset=0
            for _ in range(nf):
                ft,fn=struct.unpack_from('<HH',d,pos);pos+=4;name=names[fn]
                count=math.prod(int(x) for x in re.findall(r'\[(\d+)\]',name))
                size=(8 if '*' in name else sizes[ft])*count
                key=re.sub(r'\[.*','',name).lstrip('*')
                fields[key]=(offset,types[ft],count,'*' in name,size);offset+=size
            assert offset==sizes[ti],(types[ti],offset,sizes[ti])
            self.structs.append(types[ti]);self.fields[types[ti]]=fields
    def field(self,raw,kind,name):
        off,typ,count,ptr,size=self.fields[kind][name]
        if ptr:return struct.unpack_from('<Q',raw,off)[0]
        fmts={'int':'i','short':'h','float':'f','double':'d','char':'b','uchar':'B','uint':'I'}
        if typ=='char':return raw[off:off+size].split(b'\0')[0].decode(errors='replace')
        if typ not in fmts:return raw[off:off+size]
        v=struct.unpack_from('<'+str(count)+fmts[typ],raw,off);return v[0] if count==1 else v
    def records(self,kind):
        for addr,(code,dna,count,raw) in self.blocks.items():
            if self.structs[dna]==kind:
                size=self.sizes[kind]
                for i in range(count):yield addr+i*size,raw[i*size:(i+1)*size]
    def pointed(self,addr):return self.blocks[addr][3]

def source_meshes():
    """Retained meshes only, stored matrices + SDNA strides, never bpy/shaders."""
    meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
    path=RAW/"Canis Major.blend"
    assert sha(path.read_bytes())==meta['source_files'][path.name]
    b=Blend(path);meshes=[]
    for _,o in b.records('Object'):
        name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
        if name not in meta['source_objects']:continue
        matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
        mesh=b.pointed(b.field(o,'Object','data'));n=b.field(mesh,'Mesh','totvert')
        v=np.ndarray((n,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),
            offset=b.fields['MVert']['co'][0],strides=(b.sizes['MVert'],4)).astype(float)
        world=(np.c_[v,np.ones(n)]@matrix)[:,:3]
        native=world[:,[0,2,1]]*meta['scale']+meta['anchor']
        nl=b.field(mesh,'Mesh','totloop')
        loops=np.ndarray((nl,),'<i4',b.pointed(b.field(mesh,'Mesh','mloop')),strides=(b.sizes['MLoop'],))
        uvptr=b.field(mesh,'Mesh','mloopuv')
        uvs=(np.ndarray((nl,2),'<f4',b.pointed(uvptr),strides=(b.sizes['MLoopUV'],4)).astype(float) if uvptr else np.zeros((nl,2)))
        uvs[:,1]=1-uvs[:,1];polys=b.pointed(b.field(mesh,'Mesh','mpoly'));faces=[];uv=[]
        for i in range(b.field(mesh,'Mesh','totpoly')):
            start,count=struct.unpack_from('<ii',polys,b.sizes['MPoly']*i)
            assert count==3,count
            ix=[start,start+1,start+2];faces.append(loops[ix]);uv.append(uvs[ix])
        material_data=b.pointed(b.field(mesh,'Mesh','mat')) if b.field(mesh,'Mesh','mat') else b''
        ptr=struct.unpack_from('<Q',material_data)[0] if len(material_data)>=8 else 0
        material=b.field(b.field(b.pointed(ptr),'Material','id'),'ID','name')[2:] if ptr else 'Untextured'
        meshes.append(dict(name=name,vertices=native,faces=np.array(faces),uv=np.array(uv),material=material,
            world_bounds=[world.min(0).tolist(),world.max(0).tolist()],object_matrix=matrix.tolist()))
    pts=np.concatenate([m['vertices'] for m in meshes]);world=np.array([m['world_bounds'] for m in meshes])
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==33007
    np.testing.assert_allclose([world[:,0].min(0),world[:,1].max(0)],meta['source_bounds'],atol=1e-6,rtol=0)
    np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-6,rtol=0)
    ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta


PALETTE=dict(silver=[178,184,185],edge=[108,117,121],black=[29,34,39],steel=[55,61,65],violet=[125,123,194],gold=[173,150,94],recess=[13,18,22],pin=[245,229,147])

def source_triangles(meshes):
    # Neutral raw geometry, not the embedded neutral shader/dye evaluated in Blender.
    texture=np.array([[[126,139,145,255]]],np.uint8);result=[]
    for m in meshes:
        for p,uv in zip(m['vertices'][m['faces']],m['uv']):
            normal=np.cross(p[1]-p[0],p[2]-p[0]);normal/=max(np.linalg.norm(normal),1e-20)
            result.append((p,uv,texture,normal))
    return result

def make_design(meta,meshes):
    parts=[]
    def c(name,pos,size,mat,group,motif='plain',turn=None):
        e=dict(name=name,**{'from':[round(a-b/2,7) for a,b in zip(pos,size)],'to':[round(a+b/2,7) for a,b in zip(pos,size)]})
        if turn:e['rotation']=dict(origin=pos,axis=turn[0],angle=turn[1])
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def beam(name,a,b,w,h,mat,group,motif='plain'):
        c(name,[(x+y)/2 for x,y in zip(a,b)],[w,h,math.dist(a,b)],mat,group,motif,('x',-math.degrees(math.atan2(b[1]-a[1],b[2]-a[2]))))
    def tube(name,x,y,z0,z1,r,t,mat,group,motif='plain'):
        for i in range(8):
            a=i*45;q=math.radians(a);rr=r-t/2
            c(f'{name}_{i}',[x-rr*math.sin(q),y+rr*math.cos(q),(z0+z1)/2],
                [2*rr*math.tan(math.pi/8)+.015,t,z1-z0],mat,group,motif,('z',a))
    def solid(name,x,y,z0,z1,r,mat,group,motif='plain'):
        for i in range(4):c(f'{name}_{i}',[x,y,(z0+z1)/2],[2*r,2*r*math.tan(math.pi/8),z1-z0],mat,group,motif,('z',i*45))
    # Real bore, patterned long silver barrel and broad violet cover.
    tube('muzzle_lip',8,12.58,-8.94218,-8.56,1.04,.19,'black','barrel','rim')
    tube('etched_barrel',8,12.58,-8.58,-4.78,.99,.23,'silver','barrel','damascus')
    tube('gold_breech_collar',8,12.58,-4.86,-4.57,1.05,.25,'gold','barrel','rivets')
    tube('ribbed_breech',8,12.58,-4.62,-.48,1.015,.26,'black','barrel','breech')
    c('bore_back',[8,12.58,-.43],[1.42,1.42,.09],'recess','barrel')
    c('forward_violet_cover',[8,13.67,-2.61],[1.62,.32,7.35],'violet','cover','panel')
    for side in (-1,1):
        c(f'cover_shoulder_{side}',[8+side*.72,13.46,-2.61],[.33,.34,7.35],'violet','cover','panel',('z',side*35))
    # Solid offset drum, eight longitudinal lobes, meaningful continuous belts.
    dx,dy=8.84,10.15
    solid('drum_core',dx,dy,-1.68,5.31,3.12,'black','drum','drum_end')
    for i in range(8):
        a=i*45;q=math.radians(a)
        c(f'drum_lobe_{i}',[dx-2.98*math.sin(q),dy+2.98*math.cos(q),1.85],
            [1.88,.38,6.70],'black','drum','lobe',('z',a))
    tube('etched_drum_belt',dx,dy,-1.75,-.97,3.22,.20,'silver','drum','greek')
    tube('rear_gold_belt',dx,dy,4.92,5.23,3.22,.17,'gold','drum','rim')
    # Side crank and lower silver crossbar have actual parallax, not side cards.
    for side in (-1,1):
        x=dx+side*3.12
        beam(f'drum_cradle_{side}',[x,9.44,-1.22],[x,8.30,5.12],.35,.42,'steel','cradle')
        c(f'cradle_pivot_{side}',[x,9.42,-1.34],[.43,.67,.67],'gold','cradle','fastener')
    solid('lower_crossbar',8.84,8.35,4.58,5.48,.42,'silver','cradle','damascus')
    # Long rear barrel, dark structural bridge and suspended pistol-grip frame.
    solid('rear_silver_tube',8,12.96,5.26,15.61,.65,'silver','receiver','damascus')
    c('rear_violet_cover',[8,13.65,7.58],[1.42,.32,6.05],'violet','cover','panel')
    for side in (-1,1):
        c(f'rear_cover_bevel_{side}',[8+side*.64,13.49,7.58],[.28,.30,6.05],'violet','cover','panel',('z',side*35))
    c('receiver_spine',[8,11.55,10.20],[1.64,1.04,10.68],'steel','receiver','vents')
    c('receiver_lower_rail',[8,10.86,10.35],[1.50,.34,10.05],'black','receiver','rail')
    c('rear_hinge',[8,12.22,15.64],[1.64,2.48,.58],'black','receiver','hinge')
    beam('pistol_grip',[8,10.73,6.6],[8,6.59,9.0],1.12,1.16,'black','grip','grip')
    c('grip_heel',[8,6.44,9.1],[1.42,.35,1.78],'steel','grip','rim')
    beam('front_grip',[8,10.34,-4.25],[8,7.05,-2.30],1.03,1.05,'black','grip','grip')
    c('front_grip_gold_cap',[8,7.06,-2.31],[1.12,.23,1.10],'gold','grip','rim')
    c('rear_hanger_blade',[8,10.9,15.55],[.42,2.55,.35],'black','receiver')
    c('rear_hanger_foot',[8,9.45,15.50],[1.18,.35,.70],'steel','receiver')
    for side in (-1,1):beam(f'stock_tension_wire_{side}',[8+side*.50,7.35,9.8],[8+side*.50,9.22,15.38],.045,.045,'steel','stock_wire')
    # Thin physical guard surrounds open air below action, not a filled panel.
    beam('trigger_guard_front',[8,10.62,4.8],[8,8.76,5.3],.23,.24,'steel','guard')
    beam('trigger_guard_floor',[8,8.76,5.3],[8,8.69,7.5],.23,.24,'steel','guard')
    c('trigger',[8,9.93,6.0],[.17,.75,.25],'black','guard',turn=('x',-16))
    # Raised open rear irons and front post: shared optical line above both covers.
    sy=14.43;rear=4.36
    c('rear_sight_mount',[8,13.88,rear],[1.12,.40,.94],'steel','sight')
    for side in (-1,1):
        c(f'rear_sight_ear_{side}',[8+side*.43,14.43,rear],[.22,1.12,.22],'black','sight')
    c('rear_notch_floor',[8,13.99,rear],[1.08,.22,.24],'black','sight')
    c('front_post_mount',[8,13.96,-7.43],[.44,.63,.58],'black','sight')
    c('front_post_pin',[8,14.29,-7.43],[.12,.28,.16],'pin','sight')
    # Rear latch horn observed above the long patterned tube.
    beam('rear_latch_blade',[8,13.66,13.64],[8,14.09,14.66],.45,.18,'silver','latch','damascus')
    c('rear_latch_root',[8,13.68,13.53],[.63,.30,.68],'steel','latch')
    ref=next(x for x in json.loads((ROOT/REFS).read_bytes()) if x['id']==ID)
    inputs=[BASE,SOURCE,HELPER,'scripts/generate_surface_w123_long_arm.py',REFS,ASSET+'textures/item/weapon/w30/'+ID+'.png']
    return dict(id=ID,revision='W149',source=meta,reference=ref,parts=parts,palette=PALETTE,full_only=True,
        method='Authored filled semantic solids / world-continuous opaque face UV; not rip-island or voxel conversion',
        identity=['violet upper covers','silver etched barrel/rear tube','offset black lobed drum with Greek-key belt and gold rims','two hanging dark grips and open trigger frame'],
        ads_sight=dict(sightCenter=[8,sy,rear],forwardPoint=[8,sy,rear-2],eyeSide='+Z',plane='XY',style='iron'),
        atlas=dict(size=EDGE,gutter=2,texels_per_unit=18),
        openings=dict(bore=[8,12.58,-8.7],trigger_guard=[8,9.25,6.2],rear_notch=[8,sy,rear]),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in [RAW/'Canis Major.blend',PHOTO]},
        limitations=['Static photo-backed painted material, not original shader/PBR or exact curved mesh.','Raw comparison is neutral geometry, not embedded shader evaluation.','Greek-key/etched waves are hand-authored approximations; opposite-side marks omitted without photo.','No animated drum/latch; existing generic reload path retained.','Native holding/ADS/audio/performance still needs master verification.'])

def tile(spec,face,w,h):
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    pts=vertices(spec['geometry'])[list(FACES[face])]
    p=((1-u)*(1-v))[:,:,None]*pts[0]+(u*(1-v))[:,:,None]*pts[1]+(u*v)[:,:,None]*pts[2]+((1-u)*v)[:,:,None]*pts[3]
    x,y,z=p[:,:,0],p[:,:,1],p[:,:,2];mat=spec['material'];motif=spec['motif']
    rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
    rgb*=(.97+.035*np.cos(v*math.pi))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<.8]*=.70;rgb[(edge>=.8)&(edge<1.65)]*=1.12
    if motif=='damascus':
        # Repeating flowing engraving follows world position over neighboring faces.
        wave=z*12+1.7*np.sin(y*4.3+np.sin(z*.8))+1.2*np.sin(y*8.6+z*.37)
        phase=np.mod(wave,2*math.pi);rgb[phase<.58]*=.64;rgb[(phase>=.58)&(phase<.83)]*=1.06
    elif motif=='greek':
        # Photo's broad angular scroll belt, in UV, not repeated ornament cubes.
        t=(np.arctan2(x-8.84,y-10.15)/(2*math.pi)*16)%1
        zz=np.clip((z+1.75)/.78,0,1)
        key=((t>.16)&(t<.80)&(zz>.15)&(zz<.30))|((t>.16)&(t<.32)&(zz>.15)&(zz<.83))|((t>.16)&(t<.65)&(zz>.68)&(zz<.83))|((t>.51)&(t<.65)&(zz>.43)&(zz<.83))
        rgb[key]=PALETTE['black']
    elif motif=='lobe':
        rgb[np.mod(z*1.5,1)<.055]*=.60
        studs=(abs(np.mod(z*1.5,1)-.5)<.06)&(abs(u-.5)<.08);rgb[studs]=PALETTE['gold']
    elif motif=='breech':
        rgb[(np.mod(z*2,1)<.065)|(np.mod(y*2,1)<.09)]*=.55
    elif motif=='grip':
        rgb[np.mod(y*9+z*.3,1)<.18]*=.54
        rgb[(abs(u-.5)<.015)&(edge>2)]=PALETTE['steel']
    elif motif in ('panel','vents','rail'):
        rgb[(edge>2)&(edge<2.8)]*=.70
        if motif=='vents':rgb[(np.mod(z*1.4,1)<.38)&(abs(v-.5)<.16)]=PALETTE['black']
        if motif=='panel':rgb[(np.mod(z*1.5,1)<.1)&(v>.80)]*=.48
    elif motif in ('fastener','rivets','hinge'):
        rgb[(abs(u-.5)<.15)&(abs(v-.5)<.07)]*=.45
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))



def compile_model(d):
 atlas=Image.new('RGBA',(EDGE,EDGE),(18,23,24,255));requests=[]
 for s in d['parts']:
  for f,ix in FACES.items():
   p=vertices(s['geometry'])[list(ix)];w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*18));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*18))
   requests.append((h,w,s['geometry']['name'],f,s))
 requests.sort(key=lambda a:(-a[0],-a[1],a[2],a[3]));x=y=2;row=0;islands=[];uvmap={}
 for h,w,name,f,s in requests:
  if x+w+2>EDGE:x=2;y+=row+4;row=0
  assert y+h+2<=EDGE,'UV atlas overflow'
  atlas.paste(Image.fromarray(np.pad(np.asarray(tile(s,f,w,h)),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
  rect=[x,y,x+w,y+h];uvmap[name,f]=[a*16/EDGE for a in rect];islands.append(dict(element=name,face=f,rect=rect));x+=w+4;row=max(row,h)
 es=[]
 for s in d['parts']:
  e=copy.deepcopy(s['geometry']);e['faces']={f:dict(uv=uvmap[e['name'],f],texture='#0') for f in FACES};es.append(e)
 d['atlas'].update(used_height=y+row+2,islands=islands,face_islands=len(islands),paint_policy='Opaque independent faceUV, continuous silver etching and photo-backed violet/black/gold panels')
 return atlas,dict(credit='Canis Major W149 / semantic filled solids and default-photo face UV / full only',
  textures={'0':'destiny:item/weapon/w123/canis_major','particle':'destiny:item/weapon/w123/canis_major'},
  display=copy.deepcopy(json.loads((ROOT/BASE).read_bytes())['display']),elements=es)


def inspection(d,model,atlas):
 es=[];groups={}
 for s,e in zip(d['parts'],model['elements']):
  b=copy.deepcopy(e);r=b.pop('rotation',None);b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,
   origin=r['origin'] if r else [8,8,8],rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'])
  for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
  es.append(b);groups.setdefault(s['group'],[]).append(b['uuid'])
 return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name='Canis Major W149 / editable full solid inspection',
  resolution=dict(width=EDGE,height=EDGE),elements=es,display=copy.deepcopy(model['display']),
  outliner=[dict(name=n,uuid=uid(n),origin=[8,8,8],rotation=[0,0,0],children=cs,export=True) for n,cs in groups.items()],
  textures=[dict(name='canis_major.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
   source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
  destiny_w149=dict(nativeAccepted=False,fullOnly=True,sourceScale=d['source']['scale'],sourceAnchor=d['source']['anchor']))

def comparison(d,meshes,atlas,model):
    w,h=500,260;sheet=Image.new('RGB',(1500,1150),'#171e26');draw=ImageDraw.Draw(sheet)
    draw.text((14,10),'CANIS MAJOR W149 / real default photo + inert SDNA geometry / authored solids and face UV',fill='white',font_size=21)
    photo=Image.open(PHOTO).convert('RGB').crop((700,220,1880,900));photo.thumbnail((770,285));sheet.paste(photo,(12,45))
    draw.text((810,75),f'{len(model["elements"])} solid cuboids / full only\nViolet cover, etched silver tubes\nOffset drum, angular belt, two grips\nNo native acceptance from CPU views',fill='white',font_size=23,spacing=14)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+f'textures/item/weapon/w30/{ID}.png'))
    points=np.concatenate([m['vertices'][m['faces']].reshape(-1,3) for m in meshes]);tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    for col,name in enumerate(('RAW NEUTRAL GEOMETRY (not shader)','OLD CANONICAL','W149 SOLID + PHOTO PAINT')):draw.text((col*w+10,342),name,fill='white',font_size=18)
    for row,(label,cam) in enumerate([('SIDE',[-1,0,0]),('FRONT QUARTER',[-1,.35,-.65]),('OPPOSITE REAR',[1,.3,.65])]):
        extent=H['frame'](points,cam,w,h)
        for col,t in enumerate(tris):
            im,_=H['render'](t,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,370+row*h));draw.text((col*w+10,375+row*h),label,fill='white',font_size=15)
    return png(sheet)

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta,meshes);atlas,model=compile_model(d)
    counts=dict(sorted(Counter(p['group'] for p in d['parts']).items()))
    review=f'''# Canis Major — W149 solid reinterpretation

Actual default photo `{PHOTO}` and inert Blender2.93 SDNA rip (6 retained objects,33007 triangles) informed silhouette, proportions and paint. Stored object matrices and native [world.X,world.Z,world.Y] coordinates use the original scale/anchor; source hash, referenced object selection and bounds are checked. No embedded Blender scripts, node shaders or DCC execution. Raw comparison is neutral geometry, not dye/PBR. All original canonical display fields and generic reload/audio/combat timings are retained.

Identity is the violet upper covers, long silver etched barrel and rear tube, big offset black lobed drum with broad angular belt/two gold rims, twin hanging grips and open trigger frame. {len(model['elements'])} filled cuboids / {len(model['elements'])*6} faces / no triangle adapters / full-only assembled count, below1000. Groups: {json.dumps(counts)}. A four-prism union makes the solid drum, longitudinal lobes/rims explain its cross-section; bore, guard and rear notch contain genuine air. Long components are continuous volumes, not rip components or voxels. Source curves are intentionally faceted.

Opaque1024 face atlas with extruded2px gutters: flowing etched silver lines and Greek-key approximation use world-continuous UV paint; violet/black/gold material boundaries have restrained edge definition. No alpha body cards or random dirt, no decorative screw cubes. This static authored material is not original iridescence, PBR, exact engraving or every opposite-side mark.

Actual physical rear notch/front bead follow design.ads_sight; master aligns ADS to it instead of bounds. No separate moving drum/latch or invented reload parts. Inspection BBModel embeds final UV, texture and semantic groups. CPU comparison is artwork evidence only; native parser/pack/first-third/ADS/use/reload/10-20displays remain master scope.
'''
    out={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review.encode()}
    if include_comparison:out[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    pts=np.concatenate([vertices(e) for e in model['elements']])
    manifest=dict(id=ID,revision='W149',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=len(model['elements'])*6,max_assembled_elements=1000,texture_size=[EDGE,EDGE],full_only=True,native_accepted=False,canonical_display_exact=True,actual_bounds=[pts.min(0).tolist(),pts.max(0).tolist()],source_scale=meta['scale'],source_anchor=meta['anchor'],source_triangles=meta['source_triangles'],generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={p:sha(b) for p,b in out.items()},limitations=d['limitations'])
    out[ART+'manifest.json']=encode(manifest);return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');p.add_argument('--no-comparison',action='store_true');a=p.parse_args();out=generate(not a.no_comparison)
    for name,data in out.items():
        path=ROOT/name
        if a.verify:assert path.read_bytes()==data,name
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print('Canis W149',len(out),'files',json.loads(out[ART+'manifest.json'])['assembled_elements'],'solid cuboids','verified' if a.verify else 'generated')


