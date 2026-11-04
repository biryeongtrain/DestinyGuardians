#!/usr/bin/env python3
"""W143 Dead Man Walking XX7463: semantic solids and opaque clean face UV.
Inert mesh/DDS data only; offline art evidence, no DCC, game, or PBR acceptance.
"""
import argparse, base64, copy, gzip, hashlib, io, json, math, re, runpy, struct, subprocess, uuid
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
ID = 'dead_man_walking_xx7463'
ART = f'art/weapons/w123/{ID}/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+f'models/weapon/sidearm/{ID}.json'
MODEL = ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE = ASSET+f'textures/item/weapon/w123/{ID}.png'
SOURCE = f'art/blockbench/weapons/w30/{ID}.bbmodel'
SCRIPT = f'scripts/generate_surface_w123_{ID}.py'
TEST = f'scripts/qa/test_surface_w123_{ID}.py'
REPORT = f'docs/qa/2026-10-26/w143/{ID}-worker.md'
REFS = 'art/weapons/w31/references.json'
RAW = Path('/tmp/destiny-weapons-w30/raw/dead_man_walking_xx7463/extracted/Dead Man Walking XX7463')
PHOTO = Path('/tmp/destiny-weapons-w31/references/dead_man_walking_xx7463.jpg')
HELPER = 'scripts/generate_surface_w123_beloved.py'
H = runpy.run_path(str(ROOT/HELPER))
FACES = H['FACES']
EDGE = 1024
PALETTE = dict(body=[92,110,111], edge=[118,134,132], dark=[43,52,53], rubber=[61,65,60],
               steel=[94,99,97], red=[177,27,32], rededge=[210,41,43], black=[13,20,21], violet=[67,64,85])
def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v): return hashlib.sha256(v).hexdigest()
def png(im):
    b=io.BytesIO(); im.save(b,format='PNG'); return b.getvalue()
def uid(v): return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w143:'+ID+':'+v))
def render_element(e):
    e=copy.deepcopy(e)
    if 'rotation' in e:
        r=e['rotation']; e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return e
def vertices(e): return H['vertices'](render_element(e))
def model_triangles(m,atlas):
    m=copy.deepcopy(m);m['elements']=[render_element(e) for e in m['elements']]
    return H['model_triangles']({'full':m},atlas)

class Blend:
    """Inert SDNA reader adapted from W138; reads Blender 2.91 data only. Never imports bpy or source code."""
    def __init__(self,path):
        data=path.read_bytes()
        if data[:2]==b'\x1f\x8b': data=gzip.decompress(data)
        if data[:4]==b'\x28\xb5\x2f\xfd':
            data=subprocess.check_output(['rtk','proxy','zstd','-dc',str(path)])
        assert data[:12]==b'BLENDER-v291',data[:12]
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
    """Decode only the seven W30 accepted objects; apply stored object matrices."""
    meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
    path=RAW/'Dead Man Walking XX7463.blend'
    assert sha(path.read_bytes())==meta['source_files']['Dead Man Walking XX7463/'+path.name]
    b=Blend(path); meshes=[]
    for _,o in b.records('Object'):
        name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
        if name not in meta['source_objects']:continue
        matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
        mesh=b.pointed(b.field(o,'Object','data')); n=b.field(mesh,'Mesh','totvert')
        v=np.ndarray((n,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),
            offset=b.fields['MVert']['co'][0],strides=(b.sizes['MVert'],4)).astype(float)
        world=(np.c_[v,np.ones(n)]@matrix)[:,:3]
        native=world[:,[0,2,1]]*meta['scale']+meta['anchor']
        nl=b.field(mesh,'Mesh','totloop')
        loops=np.ndarray((nl,),'<i4',b.pointed(b.field(mesh,'Mesh','mloop')),strides=(b.sizes['MLoop'],))
        uvs=np.ndarray((nl,2),'<f4',b.pointed(b.field(mesh,'Mesh','mloopuv')),strides=(b.sizes['MLoopUV'],4)).astype(float)
        uvs[:,1]=1-uvs[:,1]
        polys=b.pointed(b.field(mesh,'Mesh','mpoly'));faces=[];uv=[];mis=[];polycounts=Counter()
        for i in range(b.field(mesh,'Mesh','totpoly')):
            off=b.sizes['MPoly']*i; start,count=struct.unpack_from('<ii',polys,off)
            mi=struct.unpack_from('<h',polys,off+b.fields['MPoly']['mat_nr'][0])[0];polycounts[count]+=1
            for j in range(1,count-1):
                ix=[start,start+j,start+j+1];faces.append(loops[ix]);uv.append(uvs[ix]);mis.append(mi)
        mats=[];ptrs=b.pointed(b.field(mesh,'Mesh','mat'))
        for i in range(b.field(mesh,'Mesh','totcol')):
            ptr=struct.unpack_from('<Q',ptrs,i*8)[0]
            mats.append(b.field(b.field(b.pointed(ptr),'Material','id'),'ID','name')[2:])
        meshes.append(dict(name=name,vertices=native,faces=np.array(faces),uv=np.array(uv),materialIndices=mis,materials=mats,
            polygon_counts=dict(polycounts),world_bounds=[world.min(0).tolist(),world.max(0).tolist()],object_matrix=matrix.tolist()))
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    ps=np.concatenate([m['vertices'] for m in meshes]); world=np.array([m['world_bounds'] for m in meshes])
    np.testing.assert_allclose([world[:,0].min(0),world[:,1].max(0)],meta['source_bounds'],atol=1e-6,rtol=0)
    np.testing.assert_allclose([ps.min(0),ps.max(0)],meta['model_bounds'],atol=1e-6,rtol=0)
    ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta

def source_triangles(meshes):
    textures={n:np.array(Image.open(RAW/(n+'_Diffuse.dds')).convert('RGBA')) for n in ('Barrel','Stock','Reticule')}
    result=[]
    for m in meshes:
        for p,uv,mi in zip(m['vertices'][m['faces']],m['uv'],m['materialIndices']):
            material=m['materials'][mi]; key=next(n for n in textures if n.lower() in material.lower())
            n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((p,uv,textures[key],n))
    return result

def make_design(meta,meshes):
    parts=[]
    def box(group,name,c,size,mat,motif='plain',turn=None):
        c=np.array(c,float);size=np.array(size,float)
        e=dict(name=name,**{'from':(c-size/2).round(7).tolist(),'to':(c+size/2).round(7).tolist()})
        if turn:e['rotation']=dict(origin=c.tolist(),axis=turn[0],angle=turn[1])
        parts.append(dict(group=group,material=mat,motif=motif,kind='filled_opaque_cuboid',geometry=e))
    def beam(group,name,a,b,width,depth,mat,motif='plain'):
        a=np.array(a,float);b=np.array(b,float);v=b-a
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],mat,motif,('x',math.degrees(math.atan2(v[2],v[1]))))
    def octagon(group,name,y,z0,z1,width,height,bevel,mat,motif='plain'):
        # Two spanning cores + four corner diamonds make a filled octagonal union.
        z=(z0+z1)/2;hx=width/2;hy=height/2;b=bevel
        box(group,name+'_vertical_core',[8,y,z],[width-2*b,height,z1-z0],mat,motif)
        box(group,name+'_horizontal_core',[8,y,z],[width,height-2*b,z1-z0],mat,motif)
        for sx in (-1,1):
            for sy in (-1,1):
                box(group,f'{name}_chamfer_{sx}_{sy}',[8+sx*(hx-b),y+sy*(hy-b),z],
                    [b*math.sqrt(2),b*math.sqrt(2),z1-z0],mat,motif,('z',45))
    # Receiver sections reflect meaningful casing changes, never source islands.
    octagon('receiver','front_casing',13.96,-3.55,-.08,2.96,3.05,.40,'body','casing')
    octagon('receiver','central_casing',13.86,-.09,3.90,2.62,2.68,.32,'body','casing')
    octagon('receiver','rear_slide',14.22,3.89,9.15,2.25,1.98,.30,'body','branding')
    beam('receiver','sloping_upper_shoulder',[8,15.43,-.10],[8,15.12,3.95],1.98,.18,'edge','seam')
    box('receiver','forward_top_seam',[8,15.515,-2.30],[1.93,.10,2.18],'edge','seam')
    box('receiver','rear_closure',[8,14.22,9.25],[1.72,1.35,.30],'body','rear_cap')
    box('frame','under_action_core',[8,12.15,1.75],[1.95,.68,6.50],'dark','panel')
    box('frame','grip_throat',[8,12.22,5.88],[1.92,1.45,2.38],'rubber','panel')
    beam('frame','rear_swept_haunch',[8,12.32,6.65],[8,13.46,7.75],1.86,1.01,'rubber','panel')
    octagon('vent_housing','vent_pod',13.25,-3.55,-.55,3.24,1.80,.33,'body','vents')
    # Forward lobes flank the bore rather than plugging it with a full section.
    for side in (-1,1):
        box('vent_housing',f'forward_lobe_{side}',[8+side*1.17,13.25,-3.955],[.90,1.60,.81],'body','vents')
        box('receiver',f'nose_upper_cheek_{side}',[8+side*1.17,14.85,-3.96],[.25,.98,.82],'body','casing')
    box('receiver','nose_upper_bridge',[8,15.36,-3.96],[2.30,.25,.82],'body','casing')
    beam('vent_housing','pod_taper',[8,12.54,-.60],[8,13.14,.43],2.65,.55,'body','casing')
    # Thick vertical oval muzzle; the center remains empty ahead of the backstop.
    loop=[(-.43,1.38),(.43,1.38),(.75,1.02),(.75,-1.02),(.43,-1.38),(-.43,-1.38),(-.75,-1.02),(-.75,1.02)]
    for i,((x0,y0),(x1,y1)) in enumerate(zip(loop,loop[1:]+loop[:1])):
        dx=x1-x0;dy=y1-y0
        box('muzzle',f'oval_muzzle_wall_{i}',[8+(x0+x1)/2,13.70+(y0+y1)/2,-4.26],
            [math.hypot(dx,dy)+.12,.22,1.16],'steel','rim',('z',math.degrees(math.atan2(dy,dx))))
    box('muzzle','recessed_bore_backstop',[8,13.70,-3.63],[1.28,2.52,.09],'black')
    for side in (-1,1):
        box('muzzle',f'muzzle_cheek_{side}',[8+side*.97,13.43,-4.31],[.28,1.20,.44],'edge','fastener')
    # One full-width swept grip core carries straps, bevels and inset panels.
    beam('grip','filled_grip',[8,7.14,7.88],[8,11.72,5.92],1.74,2.02,'rubber','grip')
    beam('grip','filled_lower_haunch',[8,7.10,7.75],[8,8.75,7.20],1.78,2.35,'rubber','grip')
    beam('grip','backstrap',[8,7.19,8.96],[8,12.26,6.88],1.49,.29,'rubber','strap')
    beam('grip','frontstrap',[8,7.20,6.78],[8,11.47,4.97],1.36,.29,'rubber','strap')
    for side in (-1,1):
        beam('grip',f'checkered_panel_{side}',[8+side*.88,7.25,7.80],[8+side*.88,11.30,6.07],.10,1.55,'rubber','checkering')
        beam('grip',f'rear_grip_bevel_{side}',[8+side*.71,7.23,8.83],[8+side*.71,11.78,6.94],.31,.25,'dark','strap')
        box('grip',f'grip_latch_{side}',[8+side*.93,10.48,5.36],[.16,.43,.47],'steel','fastener',('x',-22.5))
    box('grip','heel_core',[8,6.96,7.75],[1.87,.65,3.00],'rubber','heel',('x',-6))
    for side in (-1,1):
        box('grip',f'heel_roundover_{side}',[8+side*.74,6.91,7.75],[.32,.35,2.83],'dark','heel',('z',side*35))
    # Five guard beams surround a continuous transverse finger opening.
    beam('guard','guard_front',[8,11.96,.68],[8,10.26,1.86],.39,.29,'rubber')
    beam('guard','guard_front_curve',[8,10.26,1.86],[8,10.12,2.24],.39,.29,'rubber')
    beam('guard','guard_floor',[8,10.12,2.24],[8,10.10,3.64],.39,.27,'rubber')
    beam('guard','guard_rear_curve',[8,10.10,3.64],[8,10.29,4.63],.39,.27,'rubber')
    beam('guard','guard_rear',[8,10.29,4.63],[8,10.79,5.10],.40,.28,'rubber')
    beam('trigger','trigger_root',[8,11.94,3.58],[8,11.40,3.86],.30,.23,'red')
    beam('trigger','trigger_arc',[8,11.40,3.86],[8,10.98,3.78],.30,.23,'rededge')
    beam('trigger','trigger_tip',[8,10.98,3.78],[8,10.66,3.53],.30,.22,'red')
    box('underbarrel','lower_rail',[8,10.73,-1.52],[1.77,.47,4.65],'dark','rail')
    for side in (-1,1):
        box('underbarrel',f'lower_rail_edge_{side}',[8+side*.78,10.94,-1.52],[.25,.17,4.62],'steel','rail')
        box('underbarrel',f'red_front_rail_band_{side}',[8+side*.56,10.75,-3.67],[.43,.47,.44],'red','fastener')
    box('underbarrel','rail_front_end',[8,10.73,-3.89],[1.58,.40,.22],'steel','twin_bolts')
    box('underbarrel','rail_rear_end',[8,10.74,.86],[1.55,.40,.35],'steel','twin_bolts')
    box('underbarrel','mounting_web',[8,11.74,-1.50],[2.18,1.52,1.52],'violet','web')
    box('underbarrel','suspension_crossblock',[8,12.23,-1.48],[2.35,.40,2.45],'dark','panel')
    octagon('underbarrel','front_cartridge',11.77,-4.78,-3.30,.91,.74,.13,'body','cartridge')
    box('underbarrel','cartridge_red_collar',[8,11.76,-3.29],[.94,.70,.18],'red','rim')
    box('underbarrel','nose_tip_base',[8,11.77,-5.05],[.61,.47,.58],'edge')
    box('underbarrel','nose_tip',[8,11.77,-5.40],[.28,.24,.20],'edge')
    for side in (-1,1):
        box('controls',f'red_control_base_{side}',[8+side*1.32,13.72,3.18],[.19,1.14,1.15],'red','rim')
        box('controls',f'control_rocker_{side}',[8+side*1.47,13.72,3.29],[.19,.91,.91],'steel','rocker')
        box('controls',f'control_lever_{side}',[8+side*1.62,13.57,3.78],[.20,.19,.91],'dark','lever',('x',-9))
        box('controls',f'control_pivot_{side}',[8+side*1.76,13.53,3.43],[.20,.31,.31],'steel','fastener')
    # Open rear frame follows the accepted source sight station/height. Its original
    # optic shader/card appearance cannot be recovered with a matte opaque atlas.
    box('sights','front_sight_base',[8,15.53,-3.28],[.65,.16,1.02],'dark')
    box('sights','front_sight_blade',[8,15.65,-3.35],[.17,.21,.58],'steel')
    box('sights','rear_sight_mount',[8,15.39,7.58],[1.14,.28,.73],'dark','rear_cap')
    box('sights','rear_sight_floor',[8,15.64,7.58],[1.15,.14,.26],'steel')
    for side in (-1,1):
        box('sights',f'rear_sight_post_{side}',[8+side*.51,15.98,7.58],[.13,.73,.26],'steel','sight_dot')
    local_inputs=[BASE,SOURCE,REFS,HELPER,'scripts/generate_surface_w123_long_arm.py']
    raw_inputs=[RAW/'Dead Man Walking XX7463.blend',PHOTO]+[RAW/(n+'_Diffuse.dds') for n in ('Barrel','Stock','Reticule')]
    return dict(id=ID,revision='W143',method='authored_semantic_filled_solids_clean_face_uv',source=meta,
        source_matching=dict(objects=len(meshes),decoded_triangles=sum(len(m['faces']) for m in meshes),w30_triangles=meta['source_triangles'],
            triangle_difference=sum(len(m['faces']) for m in meshes)-meta['source_triangles'],reader='gzip Blender 2.91 SDNA; stored matrices; accepted names only; inert arrays'),
        identity=['teal grey long SUROS casing','vertical oval muzzle','seven shallow vent dimples','red side controls and curved trigger',
                  'suspended lower rail with pointed nose','solid swept dark checkered grip'],
        construction_plan='Start near 100 solids; added forms must provide silhouette, cross section, opening, or mechanism depth.',
        source_frame_policy='No refit/recenter; W30 world [x,z,y] * scale + anchor; original display copied exactly.',
        reload_policy='Full model; existing ADS/twohand/generic reload; no split reload requirement or new pivots.',
        openings=dict(guard=[8,10.92,2.62],muzzle=[8,13.70,-4.40],rear_sight=[8,16.05,7.58],rail_gap=[8,11.45,.15]),
        filled_probes=dict(receiver=[8,13.9,1.3],front_housing=[8,13.6,-2.2],rear_slide=[8,14.2,6.5],grip=[8,9.4,6.92],web=[8,11.65,-1.5]),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in local_inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=['Matte default-dye interpretation, not original PBR or optic shader recovery.',
            'Vent dimples and screw recesses use opaque face UV, not drilled apertures.',
            'Octagonal/segmented curves and stepped tiny nose approximate sculpted originals.',
            'Open rear sight follows accepted rip station/height; default photo has a lower apparent sight profile.',
            'Offline renders do not establish native parser, pack routing, holding, ADS, reload, or performance acceptance.'],parts=parts)

def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])];u=(np.arange(w)+.5)/w;v=(np.arange(h)+.5)/h
    return p[0]+u[None,:,None]*(p[1]-p[0])+v[:,None,None]*(p[3]-p[0])

def branding_image():
    # Lettering transcribed from the default-photo SUROS mark, not unrelated decals.
    im=Image.new('L',(440,100));d=ImageDraw.Draw(im)
    glyphs={'S':[(1,0),(0,0),(0,.5),(1,.5),(1,1),(0,1)],'U':[(0,0),(0,1),(1,1),(1,0)],
            'R':[(0,1),(0,0),(1,0),(1,.5),(0,.5),(1,1)],'O':[(0,0),(1,0),(1,1),(0,1),(0,0)]}
    d.polygon([(4,10),(51,10),(63,29),(27,29),(18,68),(4,68)],fill=255)
    d.polygon([(35,38),(65,38),(65,68),(28,68)],fill=255)
    for i,ch in enumerate('SUROS'):
        x=90+i*67;points=[(x+a*45-b*6,12+b*60) for a,b in glyphs[ch]]
        d.line(points,fill=255,width=7,joint='curve')
    return np.asarray(im)
BRANDING=branding_image()

def tile(spec,face,w,h):
    q=world_points(spec['geometry'],face,w,h);x,y,z=np.moveaxis(q,2,0)
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    rgb=np.broadcast_to(np.array(PALETTE[spec['material']],float),(h,w,3)).copy()
    rgb*=(.965+.045*np.cos((v-.42)*math.pi))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<1.1]*=1.12
    motif=spec['motif'];side=face in ('east','west')
    def shade(mask,factor):rgb[mask]*=factor
    def rivet(cz,cy,r=.07):
        rr=np.hypot(z-cz,y-cy);rgb[rr<r]=[24,31,32];rgb[(rr>=r)&(rr<r*1.3)]=[127,137,133]
        rgb[(rr<r*.65)&(abs(y-cy)<.018)]=[75,83,83]
    if motif in ('casing','branding'):
        if side:
            seam=14.94-.15*np.clip(z,0,4)
            shade((abs(y-seam)<.022)&(z>-.04)&(z<4.2),.59)
            shade((abs(y-12.77)<.023)&(z<.1),.70)
            shade((abs(z+.12)<.018)&(y>14.8),.67)
            mask=(z>-.08)&(z<3.91)&(y>12.80)&(y<14.75-.15*z)&(y>13.0+.12*z)
            rgb[mask]*=1.105
        shade((abs(z+.09)<.018)&(y>14.8),.7)
    if motif=='branding' and side:
        uu=(z-4.60)/3.80 if face=='west' else (8.40-z)/3.80
        vv=(15.09-y)/.71;valid=(uu>=0)&(uu<1)&(vv>=0)&(vv<1)
        ix=np.clip((uu*BRANDING.shape[1]).astype(int),0,BRANDING.shape[1]-1)
        iy=np.clip((vv*BRANDING.shape[0]).astype(int),0,BRANDING.shape[0]-1)
        rgb[valid&(BRANDING[iy,ix]>128)]=[12,28,31]
        shade((abs(y-13.58)<.026)&(z>4.20)&(z<8.8),.67)
    if motif=='vents' and side:
        for cz,cy in [(-2.79,13.72),(-2.33,13.72),(-1.87,13.72),(-3.02,13.23),(-2.56,13.23),(-2.10,13.23),(-1.64,13.23)]:
            rr=np.hypot((z-cz)/.10,(y-cy)/.12)
            rgb[(rr>1)&(rr<1.25)]=[121,135,131];rgb[rr<1]=[12,23,24]
        shade((abs(y-(12.52+.11*(z+4)))<.024)&(z> -4.1),.67)
    if motif=='checkering' and side:
        t=(11.32-y)/4.12;s=z-(6.08+1.75*t)
        inside=(abs(s)<.61)&(t>.045)&(t<.97)
        a=np.mod((s*1.1+y)*5,1);b=np.mod((s*1.1-y)*5,1)
        rgb[inside]=[59,65,59];rgb[inside&((a<.18)|(b<.18))]=[24,30,27]
        rgb[inside&(a>.70)&(b>.70)]=[110,118,105]
        rgb[(abs(s)>.61)&(abs(s)<.64)&(t>.035)&(t<.98)]=[74,81,76]
        rivet(7.99,7.48,.14)
    if motif=='strap':shade(np.mod(y*9,1)<.18,.87)
    if motif=='heel':shade((v>.72)&(v<.79),.7)
    if motif=='rail':
        shade((abs(x-8)>.50)&(abs(x-8)<.59),.5)
        shade((abs(y-10.77)<.035),1.23)
    if motif=='web' and side:
        rivet(-1.98,11.74,.075);rivet(-1.01,11.74,.075)
        shade((u<.04)|(v>.96),1.30)
    if motif in ('fastener','rocker','twin_bolts','rear_cap'):
        if (side and motif!='twin_bolts') or face in ('north','south'):
            rr=np.hypot((u-.5)*w/max(w,h),(v-.5)*h/max(w,h))
            if motif=='fastener':
                rgb[rr<.29]=[26,35,36];rgb[(rr>.29)&(rr<.37)]=[139,152,151]
                rgb[(abs(u-.5)<.04)&(rr<.23)]=[75,93,95]
            elif motif=='twin_bolts':
                for cx in (.23,.77):
                    r=np.hypot((u-cx)*1.6,v-.5);rgb[r<.28]=[18,31,31];rgb[(r>.28)&(r<.34)]=[151,167,165]
            elif motif=='rocker':
                shade((abs(v-.5)<.035)&(u>.18)&(u<.84),.42)
                shade((u>.15)&(u<.19)&(v>.2)&(v<.8),.7)
            else:shade(np.mod(u*7,1)<.16,.72)
    if motif=='panel' and side:shade((abs(y-12.19)<.035)&(z>-.9)&(z<4),.72)
    if motif=='cartridge':shade((abs(z+4.15)<.018)|(abs(z+3.4)<.018),.48)
    if motif=='sight_dot' and face=='south':rgb[(abs(u-.5)<.24)&(v<.22)]=[178,50,46]
    if spec['material'] in ('red','rededge'):rgb[edge<1.5]*=1.12
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(19,26,27,255));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=28 if spec['motif'] in ('branding','checkering') and face in ('east','west') else 18
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,e['name'],face,spec))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));x=y=2;row=0;ledger=[];uvs={}
    for h,w,name,face,spec in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow '+name)
        im=tile(spec,face,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uvs[(name,face)]=[v*16/EDGE for v in [x,y,x+w,y+h]]
        ledger.append(dict(element=name,face=face,rect=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    es=[]
    for spec in d['parts']:
        e=copy.deepcopy(spec['geometry']);e['faces']={f:dict(uv=uvs[(e['name'],f)],texture='#0') for f in FACES};es.append(e)
    d['atlas']=dict(size=EDGE,gutter=2,density=18,detail_density=28,used_height=y+row+2,face_islands=len(ledger),islands=ledger)
    return atlas,dict(credit='W143 Dead Man Walking XX7463 / semantic solids + clean default-dye face UV',
        textures={'0':'destiny:item/weapon/w123/'+ID,'particle':'destiny:item/weapon/w123/'+ID},
        elements=es,display=json.loads((ROOT/BASE).read_bytes())['display'])

def inspection(d,model,atlas):
    es=[];groups=[]
    for group in sorted({s['group'] for s in d['parts']}):
        children=[];names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        for e in model['elements']:
            if e['name'] not in names:continue
            b=copy.deepcopy(e);r=b.pop('rotation',None)
            b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],
                rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
            es.append(b);children.append(b['uuid'])
        groups.append(dict(name=group,uuid=uid(group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Dead Man Walking XX7463 W143 offline inspection',
        resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name=ID+'.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=copy.deepcopy(model['display']),
        destiny_w143=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale']))

def comparison(d,meshes,atlas,model):
    w,h=900,410;sheet=Image.new('RGB',(2700,2140),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'DEAD MAN WALKING XX7463 / W143 / SEMANTIC SOLIDS + CLEAN FACE UV',29)
    photo=Image.open(PHOTO).convert('RGB').crop((800,160,1790,810));photo.thumbnail((930,485));sheet.paste(photo,(10,54))
    lines=[f'{len(model["elements"])} opaque cuboids / assembled full model',
           'Teal grey casing / SUROS mark / red controls / checkered solid grip',
           'Physical vertical oval muzzle + open guard + suspended lower rail',
           'Vent dimples and screws: opaque UV detail, not drilled holes',
           f'Inert BLEND: {len(meshes)} accepted objects / 12,061 triangles (W30 matches)',
           'Original source scale, anchor, display; existing ADS/twohand/generic reload',
           'Rear sight follows rip height; photo shows a lower apparent profile',
           'OFFLINE CPU ART EVIDENCE / native, optic shaders and PBR unverified']
    for i,line in enumerate(lines):label(960,85+i*49,line,23)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+f'textures/item/weapon/w30/{ID}.png'))
    tris=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for col,s in enumerate(['RAW / UNDYED DIFFUSE / 12,061 TRIANGLES','INHERITED DIRTY PRODUCT / 223 CUBOIDS',f'W143 / {len(model["elements"])} FILLED SEMANTIC CUBOIDS']):label(col*w+15,550,s,20)
    for row,(name,cam) in enumerate([('SIDE',[-1,0,0]),('MUZZLE THREE-QUARTER',[-1,.4,-.65]),('REAR THREE-QUARTER',[1,.32,.65])]):
        ext=H['frame'](points,cam,w,h)
        for col,ts in enumerate(tris):
            im,_=H['render'](ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,585+row*h));label(col*w+15,594+row*h,name,18)
    for i,(group,cam) in enumerate([('muzzle',[.25,.15,-1]),('grip',[-1,.15,.6]),('underbarrel',[-1,.1,-.35])]):
        names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        es=[e for e in model['elements'] if e['name'] in names];pts=np.concatenate([vertices(e) for e in es])
        im,_=H['render'](model_triangles(dict(elements=es),atlas),cam,H['frame'](pts,cam,900,275),(900,275))
        sheet.paste(im,(i*900,1830));label(i*900+15,1838,group.upper()+' / SOLID DETAIL',18)
    label(20,2110,'Same camera and source frame per full-model row. Central master: BB/native pack, 1st/3rd person, ADS, generic reload, 10-20 display review pending.',18)
    return png(sheet)

def review_text(d,counts):
    return f'''# Dead Man Walking XX7463 W143

{len(d['parts'])} authored opaque cuboids, zero triangle adapter outputs, assembled full-only. Groups: {json.dumps(counts,sort_keys=True)}. The inherited dirty product is the current W30 223-cuboid model; this worker adds its W123 replacement without changing canonical routing or shared integration.

Reference: actual W31 default photo (opened), accepted W30 metadata, original Blender 2.91 and Barrel/Stock/Reticule DDS arrays. Gzip is decompressed in memory; SDNA schema strides and stored object matrices are read as data. All seven accepted objects decode to exactly 12,061 triangles, matching W30 (difference 0); no source scripts, drivers, shaders, or DCC are executed. World-to-model mapping remains [x,z,y] * {d['source']['scale']} + {d['source']['anchor']}, without bounding-box refit. New bounds approximate the source envelope, not vertex equivalence.

Identity: long grey teal SUROS casing and lighter angled panel, elongated vertical muzzle, seven shallow vent dimples, red rocker and curved trigger, suspended forward rail with pointed nose, swept checkered dark grip. Broad receiver sections use filled octagonal unions and continuous faces; one full-width solid grip core carries straps and inset checkering. Guard beams, a 1.12-unit deep muzzle cavity and open rear sight have physical air space. The underbarrel web and isolated rail retain the original large gap. No alpha silhouette sheets, voxel skins, ripped connected-component exports, or arbitrary triangle JSON fields.

1024-square opaque RGBA atlas: 18 texels/model unit with independent face UV rectangles and two-pixel extruded gutters. Shallow vents, fasteners, restrained panel boundaries, rail grooves, grip diamonds and independently oriented SUROS marks are paint. SUROS lettering is transcribed from the default photo. Matte colors interpret the default dye; raw diffuse is mostly undyed and does not prove original PBR. Small sculpted nose and curve transitions are simplified. The open rear sight follows accepted source station/height rather than its black raw-diffuse reticle card; the default photo shows a lower apparent sight. Optic shader appearance remains unrepresented.

Preserved: exact original display, scale, anchor and -Z muzzle frame; full-model ADS/twohand/generic reload arrangement, no new magazine split/pivot. No shared registry, migration, HUD, Java, gameplay or audio edits. Offline side, muzzle/rear three-quarter and detail renders compare raw, actual inherited canonical and new output with matching full-model frames. The embedded-atlas BB file is editable inspection evidence, not evidence that native Blockbench/Minecraft rendering passed.

Practical Python tests cover source bounds/counts, positive dimensions, native element schema, budget, UV opacity/gutters, sampled muzzle/guard/sight/rail air channels, solid receiver/grip cross sections, display, BB parity, provenance and determinism. Native pack routing/parsing and textures, first/third-person holding, ADS/twohand, generic reload, muzzle/guard obliques and 10-20 display observation remain central master's scenarios. No live DCC, Computer Use, Vision, fixture, Gradle or dependency builds were run; no native, runtime PBR or performance acceptance is claimed.
'''

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta,meshes);atlas,model=compile_model(d)
    counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()))
    out={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),
         ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:out[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    ps=np.concatenate([vertices(e) for e in model['elements']]);assert 0<len(model['elements'])<=1000
    manifest=dict(id=ID,revision='W143',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),groups=counts,
        triangle_adapter_elements=0,alpha_body_elements=0,emitted_faces=len(model['elements'])*6,max_assembled_elements=1000,
        full_only=True,texture_size=[EDGE,EDGE],actual_bounds=[ps.min(0).round(7).tolist(),ps.max(0).round(7).tolist()],
        source_bounds=meta['model_bounds'],source_scale=meta['scale'],source_anchor=meta['anchor'],source_matching=d['source_matching'],
        source_triangles=meta['source_triangles'],inherited_cuboids=len(json.loads((ROOT/BASE).read_bytes())['elements']),
        canonical_display_exact=True,native_accepted=False,default_photo_sha256=sha(PHOTO.read_bytes()),
        generator_sha256=sha((ROOT/SCRIPT).read_bytes()),test_sha256=sha((ROOT/TEST).read_bytes()) if (ROOT/TEST).exists() else None,
        input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={p:sha(data) for p,data in out.items()},limitations=d['limitations'])
    out[ART+'manifest.json']=encode(manifest);return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    for path,data in generate().items():
        target=ROOT/path
        if args.verify:assert target.is_file() and target.read_bytes()==data,path
        else:target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(data)
    print('Dead Man Walking XX7463 W143', 'verified' if args.verify else 'generated')
if __name__=='__main__':main()
