#!/usr/bin/env python3
"""W147 Whispering Slab semantic solids; inert local FBX/DDS inspection only."""
import argparse, base64, copy, hashlib, io, json, math, struct, uuid, zlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import generate_bow_models_w50 as w50
ROOT = Path(__file__).resolve().parents[1]
ID = 'whispering_slab'
ART = 'art/weapons/w123/'+ID+'/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/bow/'+ID+'.json'
TEXTURE = ASSET+'textures/item/weapon/w123/'+ID+'.png'
MODEL = ASSET+'models/weapon_surface_w123/'+ID+'.json'
RAW = Path('/tmp/destiny-weapons-w30/raw/whispering_slab/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/whispering_slab.jpg')
EDGE=1024
FACES = {'north': (3,2,0,1), 'south': (6,7,5,4), 'west': (2,6,4,0), 'east': (7,3,1,5), 'up': (2,3,7,6), 'down': (4,5,1,0)}
NORMALS = {'north': (0,0,-1), 'south': (0,0,1), 'west': (-1,0,0), 'east': (1,0,0), 'up': (0,1,0), 'down': (0,-1,0)}
def encode(v):
    return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def png(im):
    buf = io.BytesIO()
    im.save(buf, format='PNG')
    return buf.getvalue()

def parse_fbx(path):
    """Binary FBX 7400 node reader; inert arrays only, no source execution."""
    data = path.read_bytes()
    assert data[:23] == b'Kaydara FBX Binary  \x00\x1a\x00'
    assert struct.unpack_from('<I', data, 23)[0] == 7400

    def node(pos):
        end, count, _, length = struct.unpack_from('<IIIB', data, pos)
        pos += 13
        if end == 0:
            return None, pos
        name = data[pos:pos + length].decode()
        pos += length
        properties = []
        for _ in range(count):
            kind = chr(data[pos]); pos += 1
            if kind in 'YCFDIL':
                fmt = {'Y': 'h', 'C': '?', 'I': 'i', 'F': 'f', 'D': 'd', 'L': 'q'}[kind]
                value = struct.unpack_from('<' + fmt, data, pos)[0]
                pos += struct.calcsize(fmt)
            elif kind in 'SR':
                length = struct.unpack_from('<I', data, pos)[0]; pos += 4
                value = data[pos:pos + length]; pos += length
                if kind == 'S':
                    value = value.decode(errors='replace')
            elif kind in 'fdlibc':
                length, compression, size = struct.unpack_from('<III', data, pos); pos += 12
                raw = data[pos:pos + size]; pos += size
                assert compression in (0, 1)
                if compression:
                    raw = zlib.decompress(raw)
                fmt = {'f': 'f', 'd': 'd', 'l': 'q', 'i': 'i', 'b': '?', 'c': 'b'}[kind]
                value = struct.unpack('<' + str(length) + fmt, raw)
            else:
                raise ValueError('Unsupported FBX type ' + kind)
            properties.append(value)
        children = []
        while pos < end - 13:
            child, pos = node(pos)
            assert child is not None
            children.append(child)
        return (name, properties, children), end

    roots = []; pos = 27
    while pos < len(data):
        value, pos = node(pos)
        if value is None:
            break
        roots.append(value)
    return roots

def render(triangles, camera, extent, viewport, raw=False):
    width,height = viewport; cam = np.array(camera,float); cam /= np.linalg.norm(cam)
    right = np.cross([0,1,0],cam); right /= np.linalg.norm(right); up = np.cross(cam,right)
    center,scale = extent
    bg = np.broadcast_to(np.array([32,39,48],float),(height,width,3)).copy()
    depth = np.full((height,width),-np.inf); light = np.array([.45,.85,-.35]); light /= np.linalg.norm(light)
    for ps,uv,texture,normal in triangles:
        facing = normal@cam
        if not raw and facing < -1e-8:
            continue
        n = normal if facing >= 0 else -normal
        screen = np.c_[(ps@right-center[0])*scale+width/2,height/2-(ps@up-center[1])*scale]
        z = ps@cam; a,b,c = screen
        x0 = max(0,int(math.floor(screen[:,0].min()))); x1 = min(width-1,int(math.ceil(screen[:,0].max())))
        y0 = max(0,int(math.floor(screen[:,1].min()))); y1 = min(height-1,int(math.ceil(screen[:,1].max())))
        if x1<x0 or y1<y0:
            continue
        den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-10:
            continue
        gx,gy = np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        wa = ((b[1]-c[1])*(gx-c[0])+(c[0]-b[0])*(gy-c[1]))/den
        wb = ((c[1]-a[1])*(gx-c[0])+(a[0]-c[0])*(gy-c[1]))/den; wc = 1-wa-wb
        zz = wa*z[0]+wb*z[1]+wc*z[2]; q = wa[:,:,None]*uv[0]+wb[:,:,None]*uv[1]+wc[:,:,None]*uv[2]
        th,tw = texture.shape[:2]
        tx = np.clip((q[:,:,0]*tw).astype(int),0,tw-1); ty = np.clip((q[:,:,1]*th).astype(int),0,th-1)
        sample = texture[ty,tx]
        visible = (wa>=-1e-7)&(wb>=-1e-7)&(wc>=-1e-7)&(zz>=depth[y0:y1+1,x0:x1+1])&(sample[:,:,3]>=128)
        shade = .64+.36*max(0,float(n@light))
        bg[y0:y1+1,x0:x1+1][visible] = (sample[:,:,:3]*shade)[visible]
        depth[y0:y1+1,x0:x1+1][visible] = zz[visible]
    return Image.fromarray(np.clip(bg,0,255).astype('uint8')), np.isfinite(depth)

def frame(points, camera, w, h):
    cam = np.array(camera,float); cam /= np.linalg.norm(cam); right = np.cross([0,1,0],cam)
    right /= np.linalg.norm(right); up = np.cross(cam,right)
    proj = np.c_[points@right,points@up]; lo,hi = proj.min(0),proj.max(0)
    return (lo+hi)/2,min((w-65)/max(hi[0]-lo[0],.1),(h-65)/max(hi[1]-lo[1],.1))


def rotation(r):
    r = dict(r)
    if 'axis' in r: r[r['axis']] = r['angle']
    x,y,z = [math.radians(r.get(a,0)) for a in 'xyz']
    cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])

def vertices(e):
    v=np.array([[e['to' if m>>a&1 else 'from'][a] for a in range(3)] for m in range(8)],float)
    if 'rotation' in e:
        o=np.array(e['rotation']['origin']); v=(v-o)@rotation(e['rotation']).T+o
    return v

def source_meshes():
    meta=json.loads((ROOT/'art/blockbench/weapons/w30/whispering_slab.bbmodel').read_bytes())['destiny_w30']
    assert sha((RAW/'Whispering Slab.fbx').read_bytes())==meta['source_files']['Whispering Slab.fbx']
    roots=parse_fbx(RAW/'Whispering Slab.fbx'); objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]
    for node in objects:
        if node[0]!='Geometry':continue
        mid=next(p for c,p in links if c==node[1][0]); model=models[mid]; name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=1e-4)
        cs={c[0]:c for c in node[2]}; raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        t=np.array(props['Lcl Translation'])/100
        v=np.c_[raw[:,0]+t[0],raw[:,2]+t[1],raw[:,1]-t[2]]*meta['scale']+meta['anchor']
        fs=[];face=[]
        for i in cs['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:
                assert len(face)==3
                fs.append(face);face=[]
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        vals={c[0]:c[1][0] for c in layer[2]}
        uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
        mat=next(materials[c] for c,p in links if p==mid and c in materials)
        meshes.append(dict(name=name,vertices=v,faces=np.array(fs),uv=uv,material=mat))
    pts=np.concatenate([m['vertices'] for m in meshes]);assert np.allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-5)
    assert sum(len(m['faces']) for m in meshes)==28726 and len(meshes)==10
    return meshes,meta

def source_triangles(meshes):
    textures={m:np.asarray(Image.open(RAW/(m+'_Diffuse.dds')).convert('RGBA')) for m in {x['material'] for x in meshes} if m!='WhisperingSlabBowstring'}
    textures['WhisperingSlabBowstring']=np.full((4,4,4),[32,33,36,255],dtype='uint8')
    result=[]
    for m in meshes:
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);length=np.linalg.norm(n)
            if length>1e-10:result.append((ps,uv,textures[m['material']],n/length))
    return result

def model_triangles(model,textures):
    result=[]
    for e in model['elements']:
        v=vertices(e);R=rotation(e.get('rotation',{}))
        for face,f in e['faces'].items():
            ps=v[list(FACES[face])];n=R@np.array(NORMALS[face]);a,b,c,d=f['uv'];uv=np.array([[a,b],[c,b],[c,d],[a,d]])/16
            if f.get('rotation'):uv=np.roll(uv,-f['rotation']//90,axis=0)
            tex=np.asarray(textures[f['texture']].convert('RGBA'))
            for ix in ((0,1,2),(0,2,3)):result.append((ps[list(ix)],uv[list(ix)],tex,n))
    return result

PALETTE={'silver':[137,145,147],'edge':[82,91,94],'black':[25,29,32],
         'grip':[35,39,42],'steel':[105,115,119],'brass':[157,126,78],'teal':[48,124,128]}

def make_design(meta):
    parts=[]
    def box(name,lo,hi,mat,group,motif='panel',turn=None):
        e={'name':name,'from':lo,'to':hi}
        if turn:
            axis,angle=turn;e['rotation']={'origin':[(a+b)/2 for a,b in zip(lo,hi)],'axis':axis,'angle':angle,'rescale':False}
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif,classification='rigid_body'))
    def center(name,c,size,mat,group,motif='panel',turn=None):
        box(name,[round(a-b/2,7) for a,b in zip(c,size)],[round(a+b/2,7) for a,b in zip(c,size)],mat,group,motif,turn)
    def link(name,a,b,depth,width,mat,group,motif='panel',x=6.382):
        # A solid beam spanning two authored YZ control points; never source islands.
        y,z=(a[0]+b[0])/2,(a[1]+b[1])/2
        center(name,[x,y,z],[depth,math.dist(a,b),width],mat,group,motif,('x',math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))))
    # Taper represented by two continuous overlapping broad load-bearing volumes.
    for tag,y0,y1,a,b in [('lower',4.28,13.55,(4.7,4.10),(13.1,5.60)),('upper',21.68,29.45,(22.05,5.33),(29.0,4.14))]:
        box(tag+'_limb_core',[6.195,y0,3.057],[6.569,y1,4.70 if tag=='lower' else 4.55],'silver','limbs','limb')
        link(tag+'_swept_blade',a,b,.390,1.50,'silver','limbs','limb')
        box(tag+'_leading_spine',[6.055,y0+.08,3.01],[6.709,y1-.08,3.25],'black','limbs','perforated')
        # Narrow bearing section, structurally deeper than the silver blade.
        ry=13.45 if tag=='lower' else 21.75
        center(tag+'_root_neck',[6.382,ry,3.65],[.66,.64,1.40],'black','limbs','flute')
    # Tip bridge, swept heel and eight-facet solid cable rollers. No baked string.
    for tag,y,sy,heel in [('lower',4.545847,1,4.10),('upper',29.152990,-1,29.59)]:
        link(tag+'_tip_crossbar',(y,3.6),(y,6.95),.55,.26,'steel','tips','perforated')
        link(tag+'_swept_tip_strut',(y+sy*2.15,3.02),(y+sy*.12,3.75),.55,.27,'black','tips')
        box(tag+'_heel',[6.04,3.8494189088840667 if tag=='lower' else 29.42,2.46],[6.724,4.28 if tag=='lower' else 29.849418908884065,4.48],'black','tips')
        center(tag+'_end_clamp',[6.382,y+sy*.67,6.95],[.50,1.15,.18],'black','tips','fastener')
        # Four crossing solids make the roller an opaque octagonal drum.
        for i in range(4):
            center(tag+f'_roller_{i}',[6.382,y,6.9493195],[.72,.52,.2154],'steel','tips','roller',('x',i*45))
        center(tag+'_cable_eye',[6.382,y,7.224],[.28,.18,.137156336586752],'black','tips','fastener')
        center(tag+'_roller_axle',[6.382,y,6.9493195],[.87,.22,.22],'black','tips','fastener')
    # Offset central riser: keep the original grip/rest frame and open side loop.
    link('grip_spine',(14.95,3.65),(16.85,4.18),.56,.70,'grip','grip','grip')
    center('grip_heel',[6.382,14.85,3.36],[.69,.28,2.82],'black','grip','fastener')
    center('grip_upper_saddle',[6.382,16.95,3.70],[.62,.34,1.62],'black','grip','flute')
    center('grip_forward_toe',[6.382,14.66,2.20],[.66,.32,.58],'steel','grip')
    box('original_arrow_rest_shelf',[6.1565234,16.9244105,1.2383105],[6.6076124,17.2179945,3.1315600],'steel','arrow_rest')
    center('arrow_rest_lip',[6.18,17.10,2.80],[.15,.42,.43],'black','arrow_rest')
    box('riser_rear_column',[5.53,17.70,3.95],[5.91,19.93,4.74],'black','riser','glyph')
    box('riser_side_collar',[5.61,17.65,2.97],[5.97,18.15,4.74],'black','riser','flute')
    box('riser_lower_join',[5.75,17.17,3.05],[6.63,17.73,4.69],'black','riser')
    box('riser_upper_join',[5.529,19.65,2.35],[6.60,20.05,4.85],'black','riser')
    box('offset_side_dock',[5.441588955983752,19.7,1.65],[5.76,20.25,2.55],'black','riser')
    # Open U-shaped cage: beams follow its perimeter, never a filled alpha card.
    loop=[(18.16,3.96),(18.16,1.48),(18.43,1.01),(19.03,.98),(19.36,1.46),(19.36,3.96)]
    for i,(a,b) in enumerate(zip(loop,loop[1:])):link('open_sight_cage_'+str(i),a,b,.34,.18,'steel','sight_cage',x=5.70)
    # Exact raw sight envelope; independent physical hole in the XY plane.
    cx,cy=6.3821564758,18.8958083271
    for i in range(8):
        a=i*45;rad=math.radians(a);r=.477
        center('sight_ring_'+str(i),[cx-r*math.sin(rad),cy+r*math.cos(rad),2.349],[.413,.125,.218],'black','sight','sight',('z',a))
    # Arched teal insert, built as a few broad solid facets, not thin side cards.
    box('inlay_base',[5.9879,19.83,2.1683],[6.7762,20.45,4.8863],'teal','inlay','inlay')
    box('inlay_crown',[5.9879,20.45,2.64],[6.7762,21.15,4.42],'teal','inlay','inlay')
    box('inlay_top',[5.9879,21.15,3.10],[6.7762,21.47,3.96],'teal','inlay','inlay')
    link('inlay_front_shoulder',(20.44,2.46),(20.98,2.99),.7883,.58,'teal','inlay','inlay')
    link('inlay_rear_shoulder',(20.44,4.59),(20.98,4.06),.7883,.58,'teal','inlay','inlay')
    arc=[(19.92,2.10),(20.55,2.22),(21.17,2.80),(21.51,3.53),(21.17,4.25),(20.55,4.84),(19.92,4.96)]
    for side,x in [('left',5.95),('right',6.81)]:
        for i,(a,b) in enumerate(zip(arc,arc[1:])):link('brass_inlay_rim_'+side+'_'+str(i),a,b,.10,.095,'brass','inlay_rim','rim',x=x)
    box('lower_riser_load_joint',[6.10,13.5,3.06],[6.66,14.90,3.83],'black','grip','grip')
    box('upper_grip_load_joint',[5.75,16.9,3.9],[6.63,17.78,4.3],'black','riser')
    # Distinct blade root mounts, bolt faces in UV rather than screw cube forests.
    for tag,y in [('lower',12.72),('upper',23.03)]:
        center(tag+'_mount',[6.382,y,5.73],[.87,1.42,1.06],'black','mounts','fastener')
        center(tag+'_mount_shoulder',[6.382,y+( .65 if tag=='lower' else -.65),5.15],[.68,.35,.73],'steel','mounts')
        for x,side in [(5.94,'left'),(6.82,'right')]:
            center(tag+'_bearing_'+side,[x,y,5.82],[.10,.56,.56],'steel','mounts','roller',('x',45))
    # Source clamp bridging the inlay to the main blade has real thickness.
    center('upper_limb_inlay_spine',[6.382,22.08,3.65],[.54,1.45,1.02],'black','limbs','perforated')
    center('inlay_lower_sill',[6.382,19.75,3.53],[.84,.17,2.84],'steel','riser')
    center('forward_rest_support',[6.08,17.43,3.55],[.35,.60,.72],'black','riser')
    # Stabilizer fixture sits on the rigid body; no alternate cable geometry.
    center('sight_side_foot',[5.71,18.86,3.22],[.36,1.18,.46],'black','sight_cage','glyph')
    d=dict(id=ID,revision='W147',source=meta,parts=parts,moving_element_names=[],
           body_element_names=[p['geometry']['name'] for p in parts],
           semantics='Solid structural limbs, real open cage/sight, full-depth grip and faceted teal inlay. Surface engraving and perforations use opaque face UV.',
           native_frame_policy='Unscaled native coordinates; anchor 8^3; original X offset retained. No recenter, display or W50 animation changes.',
           reference_default_dye='Actual JPG: silver-black limbs, teal contour-pattern inlay and restrained brass rim.',
           atlas=dict(size=[EDGE,EDGE],independent_faces=True,gutter_px=2,opacity=255,islands=[]),
           limitations=['Offline visual review only; native loading/rotation, held poses/ADS, draw/nock and 10-20 displays remain master QA.','Taper and arched plaque use authored cuboid facets; subtle sculpting/PBR and source microdetail are simplified.','W50 moving copies intentionally retain historical cuboid geometry and original texture.'])
    paths=[BASE,'art/blockbench/weapons/w30/whispering_slab.bbmodel',ASSET+'textures/item/weapon/w30/'+ID+'.png','scripts/generate_bow_models_w50.py']
    d['input_sha256']={p:sha((ROOT/p).read_bytes()) for p in paths}
    d['raw_input_sha256']={str(p):sha(p.read_bytes()) for p in sorted(RAW.iterdir()) if p.is_file()}
    d['raw_input_sha256'][str(PHOTO)]=sha(PHOTO.read_bytes())
    return d

class Paint:
    def __init__(self):
        self.contour=np.asarray(Image.open(RAW/'EnviousTouch_TiledDiffuse01.dds').convert('RGB').resize((256,256),Image.Resampling.LANCZOS)).astype(float)
    def tile(self,spec,face,w,h):
        v,u=np.mgrid[0:h,0:w];u=(u+.5)/w;v=(v+.5)/h
        pts=vertices(spec['geometry'])[list(FACES[face])]
        pos=((1-u)*(1-v))[:,:,None]*pts[0]+(u*(1-v))[:,:,None]*pts[1]+(u*v)[:,:,None]*pts[2]+((1-u)*v)[:,:,None]*pts[3]
        y,z=pos[:,:,1],pos[:,:,2];mat=spec['material'];motif=spec['motif'];side=face in ('east','west')
        rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
        # Soft satin edge roll; large material values are kept quiet.
        edge=np.minimum.reduce([u,1-u,v,1-v]);rgb*=np.where(edge<.018,1.12,np.where(edge<.035,.83,1))[:,:,None]
        if face in ('up','down'):rgb*=.85
        if motif=='limb' and side:
            # Two observed perforation columns along the continuous fore edge.
            ly=np.mod(y-.11,.50)-.25
            for zz in [3.46,3.70]:
                r=((z-zz)/.073)**2+(ly/.085)**2
                rgb[(r>.90)&(r<1.5)]*=1.20;rgb[r<.90]*=.28
            # Broad source-like geometric scribing kept extremely restrained.
            lines=(abs(np.mod((y+z*.8)*.34,1)-.5)<.004)&(z>3.9)
            rgb[lines]*=.88
        if motif=='inlay' and side:
            tex=self.contour; th,tw=tex.shape[:2]
            # Continuous world frame across all plaque facets; source tiled relief.
            a=np.mod((z-2.1)*.48,1);b=np.mod((y-19.83)*.55,1)
            q=tex[np.minimum((b*th).astype(int),th-1),np.minimum((a*tw).astype(int),tw-1)]@np.array([.2126,.7152,.0722])
            tone=np.clip((q-75)/95,.05,1.0)
            rgb=np.array([12,35,39])+tone[:,:,None]*np.array([54,119,119])
        if motif in ('perforated','flute'):
            stripe=(abs(np.mod(y*2,1)-.5)<.06)&(u>.15)&(u<.85);rgb[stripe]*=.65
        if motif=='grip' and side:
            stripe=(np.mod(y*7+z*2,1)<.11);rgb[stripe]*=.60
            rgb[(u>.16)&(u<.20)]*=1.25
        if motif in ('fastener','roller') and side:
            # Observed large circular axle and paired small clamp screws.
            for cu,cv,rr in [(.50,.50,.27),(.22,.18,.06),(.78,.18,.06)]:
                r=((u-cu)**2+(v-cv)**2)**.5
                rgb[(r>rr*.84)&(r<rr)]*=1.55;rgb[r<rr*.67]*=.62
        if motif=='sight' and face in ('north','south'):
            rgb[:]=[37,40,40]
            rgb[(u<.2)|(u>.8)]=[144,119,76]
        if motif=='glyph' and side:
            # Six elongated diamond plaques observed below the inlay, no invented lettering.
            q=np.mod(u*6,1);dia=(abs(q-.5)/.34+abs(v-.5)/.30)
            rgb[(dia>.80)&(dia<1.0)]*=1.45
        return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,dtype='uint8')]))

def compile_model(d,original):
    atlas=Image.new('RGBA',(EDGE,EDGE),(22,27,30,255));paint=Paint();tiles=[]
    for spec in d['parts']:
        vs=vertices(spec['geometry'])
        for face,ix in FACES.items():
            ps=vs[list(ix)];w=max(6,min(360,math.ceil(np.linalg.norm(ps[1]-ps[0])*32)));h=max(6,min(360,math.ceil(np.linalg.norm(ps[3]-ps[0])*32)))
            tiles.append((spec,face,w,h))
    tiles.sort(key=lambda t:(-t[3],-t[2],t[0]['geometry']['name'],t[1]));uvmap={};x=y=2;row=0
    for spec,face,w,h in tiles:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        assert y+h+2<=EDGE,'UV atlas overflow'
        tile=paint.tile(spec,face,w,h);padded=Image.fromarray(np.pad(np.array(tile),((2,2),(2,2),(0,0)),mode='edge'));atlas.paste(padded,(x-2,y-2))
        name=spec['geometry']['name'];uvmap[name,face]=[q*16/EDGE for q in [x,y,x+w,y+h]]
        d['atlas']['islands'].append(dict(element=name,face=face,rect=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    d['atlas']['used_height']=y+row+2
    body=[]
    for spec in d['parts']:
        e=copy.deepcopy(spec['geometry']);e['faces']={f:dict(uv=uvmap[e['name'],f],texture='#0') for f in FACES};body.append(e)
    _,moving=w50.parts(original,w50.CONFIG[ID])
    # Exact W50 geometry/UV/rotation, changing only stable name and texture slot.
    for i,e in enumerate(moving):
        e['name']=f'moving_rest_{i:03}';d['moving_element_names'].append(e['name'])
        for f in e['faces'].values():
            assert f['texture']=='#0';f['texture']='#original'
    d['moving_copies']=[dict(name=e['name'],classification='resting_W50_moving_copy',source='parts(original, CONFIG[id])[1]',index=i) for i,e in enumerate(moving)]
    model={k:copy.deepcopy(v) for k,v in original.items() if k not in ('elements','textures','credit')}
    model.update(credit='W147 Whispering Slab | authored semantic solids + exact W50 rest moving copies',
                 textures={'0':'destiny:item/weapon/w123/'+ID,'original':original['textures']['0'],'particle':'destiny:item/weapon/w123/'+ID},elements=body+moving)
    states=[{},dict(empty=True)]+[dict(draw=i/w50.STEPS) for i in range(w50.STEPS+1)]+[dict(nock=i/w50.STEPS) for i in range(w50.STEPS+1)]
    d['budget']={'rigid_body':len(body),'resting_moving':len(moving),'largest_existing_W50_moving_state':max(len(w50.parts(original,w50.CONFIG[ID],**s)[1]) for s in states)}
    d['budget']['max_assembled']=len(body)+d['budget']['largest_existing_W50_moving_state'];assert d['budget']['max_assembled']<=1000
    return atlas,model

def uid(name):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w147:'+ID+':'+name))

def inspection(d,model,atlas,original_texture):
    es=[];groups={};sizes=[atlas.size,original_texture.size]
    for e in model['elements']:
        b=copy.deepcopy(e);r=b.pop('rotation',{});angles=[r.get(a,0) for a in 'xyz']
        if 'axis' in r:angles['xyz'.index(r['axis'])]=r['angle']
        b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,origin=r.get('origin',[8,8,8]),rotation=angles)
        moving=e['name'] in d['moving_element_names'];group='W50_rest_moving_EXACT' if moving else next(s['group'] for s in d['parts'] if s['geometry']['name']==e['name'])
        for f in b['faces'].values():
            ti=1 if f['texture']=='#original' else 0;w,h=sizes[ti];f['texture']=ti;f['uv']=[val*(w if i%2==0 else h)/16 for i,val in enumerate(f['uv'])]
        es.append(b);groups.setdefault(group,[]).append(b['uuid'])
    textures=[]
    for ti,(im,name) in enumerate([(atlas,'whispering_slab_w147.png'),(original_texture,'whispering_slab_original_w30.png')]):
        w,h=im.size;textures.append(dict(name=name,id=str(ti),uuid=uid('texture_'+str(ti)),width=w,height=h,uv_width=w,uv_height=h,source='data:image/png;base64,'+base64.b64encode(png(im)).decode()))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Whispering Slab W147 | semantic solids + W50 rest',resolution={'width':EDGE,'height':EDGE},
                elements=es,outliner=[dict(name=g,uuid=uid(g),origin=[8,8,8],rotation=[0,0,0],children=cs,export=True) for g,cs in groups.items()],textures=textures,display=copy.deepcopy(model['display']),
                destiny_w147=dict(nativeAccepted=False,bodyNames=d['body_element_names'],movingNames=d['moving_element_names'],sourceScale=d['source']['scale'],sourceAnchor=d['source']['anchor']))

def comparison(d,meshes,atlas,model,old,oldtex):
    w,h=800,820;top=410;sheet=Image.new('RGB',(w*3,top+h*3+510),'#151c25');draw=ImageDraw.Draw(sheet)
    def label(x,y,t,size=20):draw.text((x,y),t,fill='#e4eaf1',font_size=size)
    label(20,15,'WHISPERING SLAB / W147 / semantic solid volumes + exact W50 rest / OFFLINE',30)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((850,310));sheet.paste(photo,(0,65))
    photo2=Image.open(PHOTO).convert('RGB').crop((940,300,1300,760));photo2.thumbnail((440,310));sheet.paste(photo2,(900,65))
    label(1390,90,'Default dye: silver-black slabs',24);label(1390,126,'Teal original tiled contour; brass rim',24)
    label(1390,175,f'{d["budget"]["rigid_body"]} rigid + {d["budget"]["resting_moving"]} exact rest moving',24)
    label(1390,219,'Two native/BB textures; no static string in body',22)
    label(1390,265,'Original X offset / scale / anchor / display',22)
    for col,t in enumerate(['RAW FBX / 28,726 triangles / undyed DDS','OLD CANONICAL / 200 cuboids',f'W147 / {len(model["elements"])} solid cuboids']):label(col*w+14,top-36,t,20)
    ts=[source_triangles(meshes),model_triangles(old,{'#0':oldtex}),model_triangles(model,{'#0':atlas,'#original':oldtex})]
    pts=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('FRONT THREE-QUARTER',[1,.18,-.68]),('REAR THREE-QUARTER',[-1,.18,.68])]):
        for col,t in enumerate(ts):
            im,_=render(t,cam,frame(pts,cam,w,h),(w,h),raw=col==0);sheet.paste(im,(w*col,top+row*h));label(col*w+12,top+row*h+10,name,18)
    y=top+3*h
    for col,(name,cam,groups) in enumerate([('INLAY / OPEN CAGE / SIGHT',[1,.13,-.6],{'inlay','inlay_rim','riser','sight_cage','sight'}),('GRIP / REST / SOURCE ARROW',[-1,.2,.6],{'grip','arrow_rest','riser'}),('LIMB CROSS-SECTION / TIP',[-.65,.15,1],{'limbs','tips','mounts'})]):
        names={s['geometry']['name'] for s in d['parts'] if s['group'] in groups}
        sub={'elements':[e for e in model['elements'] if e['name'] in names or (col==1 and e['name'] in d['moving_element_names'][2:])]}
        points=np.concatenate([vertices(e) for e in sub['elements']])
        if col==2:points=points[points[:,1]>25]
        im,_=render(model_triangles(sub,{'#0':atlas,'#original':oldtex}),cam,frame(points,cam,w,440),(w,440));sheet.paste(im,(col*w,y));label(col*w+12,y+10,name,18)
    label(15,sheet.height-44,'Native pack loading, 26.3 rotations, first/third person, ADS, W50 draw/nock and 10-20 displays: pending master.',20)
    return png(sheet)

def review_text(d):
    b=d['budget']
    return f'''# Whispering Slab W147 — offline art review

Actual default reference: `{PHOTO}`. Inert binary FBX inspection retained ten named objects, excluded `Whispering-Slab.08.000`, and verified 28,726 textured triangles against the W30 BB metadata. FBX local rotation/translation is converted to the native basis; measured bounds match the supplied offset frame. Raw diffuse is undyed and is explicitly labeled in the comparison. The original `EnviousTouch_TiledDiffuse01.dds` supplies the teal contour relief, recolored against the photo; arbitrary noise and invented lettering are absent.

The body uses **{b['rigid_body']} opaque cuboids**: continuous silver limb slabs and swept taper volumes, deeper leading spines, tip bridges/drums, grip/rest, an open sight cage and ring, arched teal insert/brass edging, and structural root mounts. Thin skin, two alpha cards, source component conversion and voxel reconstruction are not used. Taper is an intentional overlap of broad solid planes; the arch is a few cuboid facets. Perforations, fasteners and quiet panel scribing use independent opaque face UV rectangles with 2px extruded gutters. Front/rear and the opposite side have separate islands. Source-backed teal UV coordinates stay continuous across the arch's facets.

Canonical assembly: {b['rigid_body']} rigid + **{b['resting_moving']} exact W50 moving copies** = {b['rigid_body']+b['resting_moving']} resting elements. The maximum existing W50 state has {b['largest_existing_W50_moving_state']} moving elements; maximum assembled count is **{b['max_assembled']}**, below 1,000. `design.json.moving_element_names` identifies every copy. Geometry, UVs, rotations and ordering match `parts(original, CONFIG[id])[1]`; only names and resolved texture slot change. `#original` resolves to the original W30 PNG; body `#0` resolves to the new atlas. Rigid body contains no baked string or arrow. Master filters the names to create NEW migration W50 body resources; historical W50 files and item graphs remain untouched.

Native source scale {d['source']['scale']}, anchor [8,8,8], off-center X envelope and original display transforms are preserved. Grip/rest and sight are authored in the same native frame; original W50 string endpoints/rest arrow, draw/nock timings, input/audio and third-person transform are unchanged. This preserves the coordinate contract; actual hand contact and visual alignment still require native verification.

`inspection.bbmodel` embeds two textures and has editable semantic groups plus a separate exact-W50-rest group. UVs use each texture's actual pixel dimensions. The offline renderer resolves both slots separately and supports axis/angle rotations. The final comparison shows actual photo, inert raw geometry, old canonical and new full assembly at identical scale per side/front/rear row, plus central open geometry and tip cross-section details.

Pixel inspection: photo colors, broad limb planes and distinct teal/brass center read clearly. Open sight/cage and solid blade thickness remain visible on opposite obliques. Historical moving geometry is visibly coarser than the new rigid body, intentionally preserved by contract. The actual full bounds are recorded separately from raw reference bounds: the exact W50 moving subset reaches native Z=-4.378223, while the raw arrow tip reaches -4.8359015; no recentering or extension of the contracted moving copies is applied. Silhouette/arch facets and subtle sculpted transitions are simplified; offline directional light and static dye are not original PBR. Source photo crops the upper tip; retained raw geometry supplies both full tips. No native loading, parser acceptance, ADS/first-third-person, draw/nock playback, 10–20 display performance or audio listening pass is claimed. Master owns those checks and integration.
'''

def generate(include_comparison=True):
    meshes,meta=source_meshes();old=json.loads((ROOT/BASE).read_bytes());d=make_design(meta);atlas,model=compile_model(d,old)
    oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/'+ID+'.png')).convert('RGBA')
    pts=np.concatenate([vertices(e) for e in model['elements']]);bp=np.concatenate([vertices(e) for e in model['elements'] if e['name'] in d['body_element_names']])
    d['actual_bounds']=[pts.min(0).tolist(),pts.max(0).tolist()];d['body_bounds']=[bp.min(0).tolist(),bp.max(0).tolist()]
    outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas,oldtex)),ART+'review.md':review_text(d).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model,old,oldtex)
    manifest=dict(id=ID,revision='W147',counts=d['budget'],emitted_elements=len(model['elements']),emitted_faces=len(model['elements'])*6,max_assembled_elements=1000,alpha_body_elements=0,
                  actual_bounds=d['actual_bounds'],body_bounds=d['body_bounds'],source_bounds=meta['model_bounds'],source_scale=meta['scale'],source_anchor=meta['anchor'],source_triangles=28726,
                  moving_element_names=d['moving_element_names'],two_textures=True,canonical_display_exact=True,native_accepted=False,
                  generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={p:sha(b) for p,b in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest);return outputs

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args();outputs=generate()
    batch=json.loads((ROOT/'docs/qa/2026-10-26/w147/batch.json').read_bytes());owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w147-'+ID));assert set(outputs)<=owned
    for rel,raw in outputs.items():
        p=ROOT/rel
        if args.verify:assert p.is_file() and p.read_bytes()==raw,'Regeneration differs: '+rel
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts; '+json.dumps(m['counts']))

if __name__=='__main__':main()
