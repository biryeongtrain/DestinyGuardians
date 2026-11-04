#!/usr/bin/env python3
"""W127 Hammerhead: authored broad solid volumes, native XYZ cubes and face UV.
W154 feeds are corrected by fix_belt_feed_w154 before UV compilation.
Bundled numpy/Pillow only. Reads inert reference data; no DCC/game subprocess.
Geometry is independent of source components and old W115 patch design.
"""
import argparse
import base64
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import uuid
import zlib
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/hammerhead/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/machine_gun/hammerhead.json'
RELOAD = ASSET+'models/weapon_reload_w114_hammerhead/hammerhead'
MODEL = ASSET+'models/weapon_surface_w123/hammerhead'
TEXTURE = ASSET+'textures/item/weapon/w123/hammerhead.png'
BB = 'art/blockbench/weapons/w30/hammerhead.bbmodel'
RAW = Path('/tmp/destiny-weapons-w30/raw/hammerhead/extracted/Hammerhead')
PHOTO = Path('/tmp/destiny-weapons-w31/references/hammerhead.jpg')
PARTS = ('body','magazine','cover')
EDGE = 1024
HINGE = [8.0, 13.151657042558291, 1.7248276566312146]
FACES = {'north':(3,2,0,1),'south':(6,7,5,4),'west':(2,6,4,0),
         'east':(7,3,1,5),'up':(2,3,7,6),'down':(4,5,1,0)}
NORMALS = {'north':(0,0,-1),'south':(0,0,1),'west':(-1,0,0),
           'east':(1,0,0),'up':(0,1,0),'down':(0,-1,0)}
PALETTE = {'graphite':[65,69,75], 'black':[35,39,45], 'steel':[123,128,134],
           'red':[170,30,29], 'red_edge':[204,44,37], 'rubber':[28,30,33],
           'belt':[135,139,140], 'recess':[17,20,24]}

def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def png(im):
    out=io.BytesIO(); im.save(out,format='PNG'); return out.getvalue()
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w127:hammerhead:'+s))

def rotation(r):
    x, y, z = [math.radians(r.get(a, 0)) for a in 'xyz']
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    return (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @
            np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @
            np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))

def vertices(e):
    v = np.array([[e['to' if mask >> a & 1 else 'from'][a] for a in range(3)] for mask in range(8)], float)
    if 'rotation' in e:
        o = np.array(e['rotation']['origin'])
        v = (v - o) @ rotation(e['rotation']).T + o
    return v

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

def model_triangles(models, texture):
    tex = np.asarray(texture.convert('RGBA')); result = []
    for m in models.values():
        for e in m['elements']:
            v = vertices(e); R = rotation(e.get('rotation',{}))
            for face, f in e['faces'].items():
                ps = v[list(FACES[face])]; n = R @ np.array(NORMALS[face]); a,b,c,d = f['uv']
                uv = np.array([[a,b],[c,b],[c,d],[a,d]]) / 16
                for ix in ((0,1,2),(0,2,3)):
                    result.append((ps[list(ix)],uv[list(ix)],tex,n))
    return result

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

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())["destiny_w30"]
    assert sha((RAW/"Hammerhead.fbx").read_bytes())==meta["source_files"]["Hammerhead/Hammerhead.fbx"]
    roots=parse_fbx(RAW/"Hammerhead.fbx")
    objects=next(n[2] for n in roots if n[0]=="Objects")
    links=[n[1][1:] for r in roots if r[0]=="Connections" for n in r[2] if n[1][0]=="OO"]
    byid={n[1][0]:n for n in objects if n[1]}; meshes=[]; hinge=None
    for g in objects:
        if g[0]!="Geometry": continue
        mid=next(p for c,p in links if c==g[1][0] and byid[p][0]=="Model")
        model=byid[mid]; name=model[1][1].split("\x00")[0]
        if name not in meta["source_objects"]: continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=="Properties70" for p in c[2]}
        assert np.allclose(props["Lcl Rotation"],[-90,0,0],atol=.0001)
        assert props["Lcl Scaling"]==[100,100,100]
        cs={c[0]:c for c in g[2]}; raw=np.array(cs["Vertices"][1][0]).reshape(-1,3)
        v=raw[:,[0,2,1]]*meta["scale"]+meta["anchor"]
        faces=[]; face=[]
        for i in cs["PolygonVertexIndex"][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0: assert len(face)==3; faces.append(face); face=[]
        uv_layer=next(c for c in g[2] if c[0]=="LayerElementUV" and c[1][0]==0)
        vals={c[0]:c[1][0] for c in uv_layer[2]}
        assert vals["MappingInformationType"]=="ByPolygonVertex" and vals["ReferenceInformationType"]=="IndexToDirect"
        uv=np.array(vals["UV"]).reshape(-1,2)[np.array(vals["UVIndex"])].reshape(-1,3,2); uv[:,:,1]=1-uv[:,:,1]
        skin=next(c for c,p in links if p==g[1][0] and byid[c][0]=="Deformer")
        bones={}
        for cid,p in links:
            if p!=skin: continue
            cluster=byid[cid]; cc={c[0]:c[1][0] for c in cluster[2] if c[1]}
            bid=next(c for c,p in links if p==cid and byid[c][0]=="Model")
            bone=byid[bid][1][1].split("\x00")[0]
            if name=="Hammerhead.01.000" and bone=="Cover":
                link=cc["TransformLink"]
                hinge=[8+link[12]/100*meta["scale"],8+link[13]/100*meta["scale"],8-link[14]/100*meta["scale"]]
            for i,w in zip(cc.get("Indexes",[]),cc.get("Weights",[])):
                assert abs(w-1)<1e-6; bones[i]=bone
        parts=[]
        for f in faces:
            assert len({bones[i] for i in f})==1
            b=bones[f[0]];parts.append("cover" if b=="Cover" else "magazine" if b=="Magazine" or b.startswith("Bullet") else "body")
        mat={"Hammerhead.00.000":"HMag", "Hammerhead.01.000":"HFrame", "Hammerhead.02.000":"HSight"}[name]
        meshes.append(dict(name=name,vertices=v,faces=np.array(faces),uv=uv,parts=parts,material=mat))
    pts=np.concatenate([m["vertices"] for m in meshes])
    assert np.allclose([pts.min(0),pts.max(0)],meta["model_bounds"],atol=1e-5)
    assert sum(len(m["faces"]) for m in meshes)==25499
    assert np.allclose(hinge,HINGE,atol=1e-10)
    return meshes,meta


def make_design(meta):
    parts={p:[] for p in PARTS}
    def box(name,lo,hi,mat,group,motif="panel",turn=None,part="body"):
        e=dict(name=name,**{"from":lo,"to":hi})
        if turn:
            axis,angle=turn;e["rotation"]=dict(origin=[round((a+b)/2,6) for a,b in zip(lo,hi)],x=0,y=0,z=0)
            e["rotation"][axis]=angle
        parts[part].append(dict(geometry=e,material=mat,group=group,motif=motif))
    def center(name,c,size,mat,group,motif="panel",turn=None,part="body"):
        box(name,[round(a-b/2,6) for a,b in zip(c,size)],[round(a+b/2,6) for a,b in zip(c,size)],mat,group,motif,turn,part)
    def tube(name,x,y,z0,z1,r,thick,mat,group,part="body"):
        # Eight solid tangent walls, physically open throughout the stated length.
        for i in range(8):
            a=math.radians(i*45);rr=r-thick/2
            # Tiny axial staggers prevent coincident end-cap faces at wall joins.
            za=z0+i*.0005;zb=z1-i*.0005
            center(f"{name}_{i}",[x-rr*math.sin(a),y+rr*math.cos(a),(za+zb)/2],
                   [2*r*math.tan(math.pi/8)+.012,thick,zb-za],mat,group,"rim",("z",i*45),part)
    # A continuous structural roof and two broad rear cheeks, not thin source islands.
    box("shroud_roof",[7.34,12.65,-10.5],[8.66,13.12,1.56],"graphite","shroud","shroud")
    for side in (-1,1):
        center(f"shroud_roof_bevel_{side}",[8+side*.72,12.66,-4.47],[.32,.32,12.06],"graphite","shroud","shroud",("z",45*side))
        center(f"shroud_front_ramp_{side}",[8+side*.52,12.62,-10.63],[.48,.30,1.70],"graphite","shroud","shroud",("x",-12))
        center(f"shroud_rear_cheek_{side}",[8+side*.72,11.91,-.89],[.45,1.27,4.90],"black","shroud","vents")
        center(f"red_upper_rail_{side}",[8+side*.56,12.37,-6.85],[.24,.22,7.1],"red","barrel","rail")
        center(f"red_lower_rail_{side}",[8+side*.56,11.36,-4.79],[.24,.23,12.40],"red_edge","barrel","rail")
        center(f"barrel_cheek_{side}",[8+side*.43,11.95,-6.40],[.22,.70,6.38],"black","barrel","inset")
        center(f"forearm_red_rail_{side}",[8+side*.27,10.57,-3.4],[.25,.22,11.35],"red","forearm","rail")
    tube("barrel",8,11.94,-11.55,2.05,.32,.11,"steel","barrel")
    tube("muzzle_bore_rim",8,11.94,-11.863723,-11.55,.39,.12,"steel","muzzle")
    # Fork muzzle: four walls and rear shoulders; bore and side windows are geometry.
    box("muzzle_top",[7.45,12.22,-11.883723],[8.55,12.43,-9.10],"black","muzzle","muzzle")
    box("muzzle_bottom",[7.45,11.42,-11.883723],[8.55,11.63,-9.10],"black","muzzle","muzzle")
    for side in (-1,1):
        center(f"muzzle_front_post_{side}",[8+side*.47,11.925,-11.72],[.16,.72,.32],"graphite","muzzle","rim")
        center(f"muzzle_rear_post_{side}",[8+side*.47,11.925,-9.28],[.16,.72,.36],"black","muzzle","muzzle")
        center(f"muzzle_fork_diagonal_{side}",[8+side*.48,11.92,-10.55],[.16,.19,1.85],"graphite","muzzle","panel",("x",22))
    # Long under-barrel gas cylinder, exposed red saddle at front.
    box("gas_cylinder",[7.71,10.16,-9.08],[8.29,10.78,2.15],"black","forearm","flute")
    box("gas_front_red_socket",[7.66,10.08,-9.10],[8.34,10.86,-8.20],"red","forearm","gas")
    box("gas_upper_spine",[7.76,10.74,-8.00],[8.24,11.20,-.36],"steel","forearm","flute")
    box("receiver_main",[7.08,10.02,2.63],[8.92,11.75,8.66],"black","receiver","receiver")
    box("receiver_rear",[7.30,10.14,8.66],[8.70,11.66,12.80],"black","receiver","receiver")
    box("receiver_front_bulkhead",[7.16,9.86,1.22],[8.84,12.60,2.79],"graphite","receiver","bulkhead")
    box("receiver_feed_floor",[7.18,11.75,2.79],[8.82,11.98,6.43],"steel","receiver","feed")
    for side in (-1,1):
        center(f"feed_tray_wall_{side}",[8+side*.77,12.14,2.92],[.22,.48,.30],"black","receiver","panel")
        center(f"receiver_side_rib_{side}",[8+side*.93,10.96,5.76],[.18,.39,5.55],"graphite","receiver","receiver")
        center(f"charging_handle_{side}",[8+side*1.10,11.28,6.97],[.95,.20,.25],"steel","receiver","handle")
        center(f"charging_knob_{side}",[8+side*1.52,11.27,7.0],[.25,.31,.40],"black","receiver","grip")
    # Real open forward carry/support handle; central opening remains unfilled.
    box("carry_bottom",[7.61,7.82,-3.11],[8.39,8.25,1.85],"black","carry","grip")
    center("carry_front",[8,8.88,-2.83],[.72,1.72,.37],"graphite","carry","panel",("x",-12))
    center("carry_rear",[8,8.88,1.58],[.72,1.72,.37],"graphite","carry","panel",("x",12))
    box("carry_upper",[7.69,9.49,-2.95],[8.31,10.18,1.72],"black","carry","rail")
    # Trigger well and hand grip remain at original held coordinates.
    box("pistol_wrist",[7.65,9.60,7.15],[8.35,10.12,8.20],"black","grip","panel")
    center("pistol_grip",[8,8.49,7.98],[.66,2.35,.85],"rubber","grip","grip",("x",-18))
    center("grip_heel",[8,7.43,8.34],[.74,.28,.96],"black","grip","panel",("x",-18))
    box("trigger_guard_bottom",[7.65,9.51,5.08],[8.35,9.73,7.25],"graphite","trigger","panel")
    center("trigger_guard_front",[8,9.91,5.18],[.70,.82,.22],"graphite","trigger","panel",("x",-10))
    center("trigger",[8,9.91,6.93],[.16,.63,.17],"steel","trigger","panel",("x",-20))
    # Open skeleton stock: upper beam, angled lower return and long butt.
    box("stock_upper_beam",[7.51,11.71,7.21],[8.49,12.24,14.42],"graphite","stock","stock")
    box("stock_top_red_latch",[7.52,12.25,8.18],[8.48,12.62,9.57],"red","stock","latch")
    box("stock_cheek",[7.59,12.22,9.59],[8.41,12.60,13.59],"graphite","stock","stock")
    center("stock_lower_brace",[8,8.20,11.45],[.75,.34,6.00],"graphite","stock","stock",("x",-13))
    box("stock_butt",[7.51,8.32,14.33],[8.49,12.84,15.116277],"rubber","stock","butt")
    center("stock_butt_toe",[8,8.45,13.89],[.70,.42,1.18],"black","stock","panel",("x",-18))
    # Top cover includes the whole sight. No recentering relative to native item [8,8,8].
    box("cover_shell",[7.18,12.58,1.60],[8.82,13.12,7.93],"graphite","cover","cover",part="cover")
    for side in (-1,1):
        center(f"cover_bevel_{side}",[8+side*.76,12.62,4.67],[.25,.25,6.17],"graphite","cover","cover",("z",45*side),"cover")
        center(f"cover_skirt_{side}",[8+side*.71,12.22,5.96],[.20,.73,3.85],"black","cover","cover",part="cover")
    box("cover_hinge_bar",[7.15,HINGE[1]-.12,HINGE[2]-.12],[8.85,HINGE[1]+.12,HINGE[2]+.12],"steel","cover","hinge",part="cover")
    box("cover_sight_mount",[7.57,13.12,3.26],[8.43,13.59,5.06],"black","sight","sightbase",part="cover")
    box("sight_base",[7.54,13.59,3.15],[8.46,13.76,5.0],"graphite","sight","sightbase",part="cover")
    for side in (-1,1):
        center(f"sight_lower_leg_{side}",[8+side*.39,14.02,3.37],[.13,.65,.18],"black","sight","rim",("z",-side*9),"cover")
        center(f"sight_upper_leg_{side}",[8+side*.34,14.43,3.37],[.13,.32,.18],"graphite","sight","rim",("z",side*20),"cover")
    box("sight_bridge",[7.73,14.50,3.28],[8.27,14.625413,3.47],"graphite","sight","rim",part="cover")
    box("sight_emitter",[7.93,13.75,4.30],[8.07,13.85,4.50],"red_edge","sight","emitter",part="cover")
    # Twin solid drums. Six overlapping opaque cuboids form each convex octagonal solid.
    # End-face paint is continuous in world XY so the subdivision has no painted seams.
    r=1.405;b=r*math.tan(math.pi/8)
    for i,x in enumerate([6.02,9.98]):
        center(f"drum_{i}_vertical_core",[x,8.415,3.86],[2*b,2*r,3.10],"black","drums","drum",part="magazine")
        center(f"drum_{i}_horizontal_core",[x,8.415,3.86],[2*r,2*b,3.10],"black","drums","drum",part="magazine")
        for sx in (-1,1):
            for sy in (-1,1):
                center(f"drum_{i}_corner_{sx}_{sy}",[x+sx*b,8.415+sy*b,3.86],[(r-b)*math.sqrt(2)]*2+[3.10],"black","drums","drum",("z",45),"magazine")
        tube(f"drum_{i}_front_rim",x,8.415,2.12,2.38,1.42,.14,"graphite","drums","magazine")
        tube(f"drum_{i}_rear_rim",x,8.415,5.34,5.60,1.42,.14,"graphite","drums","magazine")
        center(f"drum_{i}_saddle",[x,9.65,3.86],[1.42,.30,2.64],"graphite","drums","panel",part="magazine")
    box("feed_center",[7.13,8.18,2.82],[8.87,10.24,4.98],"black","feed","feed",part="magazine")
    box("feed_neck",[7.46,10.18,3.11],[8.54,12.24,4.60],"graphite","feed","feed",part="magazine")
    # W154: linked muzzleward rounds are authored by correct_parts below.
    from fix_belt_feed_w154 import correct_parts
    feed_w154=correct_parts('hammerhead',parts)
    inputs=[BASE,BB,*[RELOAD+"_"+p+".json" for p in PARTS],"scripts/generate_reload_w114_hammerhead.py"]
    raw_inputs=[RAW/"Hammerhead.fbx",PHOTO,*[RAW/(n+"_Diffuse.png") for n in ["HFrame","HMag","HSight"]]]
    return dict(id="hammerhead",revision="W154",belt_feed_w154=feed_w154,method="new authored semantic opaque cuboids; no source island fitting",parts=parts,
        source=meta,cover_pivot=HINGE,coordinate_basis="(X,Z,Y)*23.3089771408205+[8,8,8]; muzzle negative Z",palette=PALETTE,
        atlas=dict(size=EDGE,gutter=2,texels_per_unit=21),
        identity=["long charcoal roof, exposed deep red rails", "fork muzzle and actual bore", "twin drums and 8 red tipped feed cartridges", "open stock and forward carry handle", "hinged top cover carrying an open reflex sight"],
        anchor_policy="Native element space unchanged. Full display copied exactly. Parts have no display; W114 external sampled hinge compensation and feed translations remain applicable.",
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=["Offline Python raster inspection only; native parser, pack, held/ADS/reload and 10-20 displays pending master.",
        "Broad opaque cuboid reinterpretation, simplified octagonal drums and corners; no exact surface/triangle equivalence claimed.",
        "Authored default black/red paint, static satin highlights and restrained panel grain; no PBR or dynamic reflection reconstruction.",
        "Belt remains a rigid magazine assembly, preserving existing W114 semantics; no new belt deformation or hand IK.",
        "One supplied oblique default-paint photo; reverse paint details are conservative and not independently photo-verified."])
class Paint:
    def tile(self,spec,face,w,h):
        e=spec["geometry"];mat=spec["material"];motif=spec["motif"]
        u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
        rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
        rgb*= (.96+.09*np.exp(-((v-.27)/.30)**2))[:,:,None]
        edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
        rgb[edge<.75]*=.70;rgb[(edge>=.75)&(edge<1.65)]*=1.18
        side=face in ("west","east"); pts=vertices(e)[list(FACES[face])]
        pos=((1-u)*(1-v))[:,:,None]*pts[0]+(u*(1-v))[:,:,None]*pts[1]+(u*v)[:,:,None]*pts[2]+((1-u)*v)[:,:,None]*pts[3]
        # Black Armory restrained metal grain follows the long axis; no random grime.
        if mat in ("graphite","black"):
            grain=np.sin(pos[:,:,2]*21+np.sin(pos[:,:,1]*17)*1.4)
            rgb+=grain[:,:,None]*1.1
        if motif in ("shroud","cover","stock","receiver") and side:
            # Fine seams + paired shallow stamps live on one broad face.
            panel=((u>.08)&(u<.92)&(abs(v-.78)<max(.007,1.0/h)))
            rgb[panel]*=.52
            seam=(np.mod(pos[:,:,2]+.4,2.75)<.018)&(v>.18)&(v<.80)
            rgb[seam]*=.58
            stamp=(np.mod(pos[:,:,2]+.21,.79)<.20)&(v>.30)&(v<.42)
            rgb[stamp]*=.76
        if motif=="vents" and side:
            vent=(u>.20)&(u<.58)&(np.mod(v,.19)<.075)&(v>.20)&(v<.82)
            rgb[vent]=[14,17,21]
            rgb[(u>.20)&(u<.58)&(np.mod(v,.19)>.075)&(np.mod(v,.19)<.095)&(v>.20)&(v<.82)]=[80,84,89]
        if motif in ("rail","gas","latch"):
            groove=(v>.32)&(v<.42)&(u>.08)&(u<.90)
            rgb[groove]*=.58
            joint=(np.mod(pos[:,:,2],1.9)<.025)&(v>.1)&(v<.9)
            rgb[joint]*=.45
        if motif in ("grip","butt"):
            grooves=(np.mod(v*12,1)<.23)&(u>.10)&(u<.90)
            rgb[grooves]*=.64
        if motif=="inset" and side:
            rgb[(v<.12)|(v>.88)]=[108,112,117]
            rgb[(v>.15)&(v<.82)]*=.62
        if motif=="feed" and side:
            rgb[(np.mod(u*5,1)<.11)&(v>.12)&(v<.89)]*=.54
        if motif=="cartridge":
            rgb[(u>.32)&(u<.39)]*=.35
            rgb[(u>.64)&(u<.71)]*=.40
            rgb[(v>.43)&(v<.57)]*=.62
        if motif=="links":
            rgb[np.mod(pos[:,:,0]-.1,.6528)<.10]*=.55
        if motif=="rim" and face in ("north","south"):
            # End caps have continuous satin color, no artificial UV border seams.
            rgb[:]=np.array(PALETTE[mat],float)*.98
        if motif=="drum" and face in ("north","south"):
            # World-aligned continuous cap on the solid octagonal decomposition.
            cx=6.02 if "drum_0" in e["name"] else 9.98
            dx=pos[:,:,0]-cx;dy=pos[:,:,1]-8.415;rr=np.sqrt(dx*dx+dy*dy)
            rgb[:]=[34,38,44]
            rgb+=(4*np.exp(-((rr-.78)/.42)**2))[:,:,None]
            rgb[(rr>1.08)&(rr<1.12)]=[53,57,63]
            rgb[(rr>.29)&(rr<.33)]=[38,42,48]
            rgb[rr<.18]=[40,44,49]
        if motif=="drum" and face not in ("north","south"):
            rgb[(np.mod(pos[:,:,2]-2.5,.74)<.035)]*=.52
        if motif in ("bulkhead","receiver","sightbase") and side and w>13 and h>13:
            # Sparse source-style fasteners, painted rather than individual cubes.
            for a,b in ((.12,.18),(.88,.18)):
                dist=((u-a)*w)**2+((v-b)*h)**2
                rgb[dist<3.6]=[121,123,126];rgb[dist<1]=[31,33,36]
        out=np.empty((h,w,4),dtype=np.uint8);out[:,:,:3]=np.clip(rgb,0,255);out[:,:,3]=255
        return Image.fromarray(out)


def compile_models(d):
    atlas=Image.new("RGBA",(EDGE,EDGE),(0,0,0,0));paint=Paint();tiles=[]
    for part,specs in d["parts"].items():
        for spec in specs:
            e=spec["geometry"];vs=vertices(e)
            for face,ix in FACES.items():
                p=vs[list(ix)];w=max(6,min(272,math.ceil(np.linalg.norm(p[1]-p[0])*21)))
                h=max(6,min(272,math.ceil(np.linalg.norm(p[3]-p[0])*21)))
                tiles.append((part,spec,face,w,h))
    tiles.sort(key=lambda t:(-t[4],-t[3],t[1]["geometry"]["name"],t[2]))
    x=y=2;row=0;uvmap={};islands=[]
    for part,spec,face,w,h in tiles:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError("Atlas overflow")
        tile=paint.tile(spec,face,w,h)
        padded=Image.fromarray(np.pad(np.asarray(tile),((2,2),(2,2),(0,0)),mode="edge"));atlas.paste(padded,(x-2,y-2))
        uvmap[(spec["geometry"]["name"],face)]=[q*16/EDGE for q in (x,y,x+w,y+h)]
        islands.append(dict(element=spec["geometry"]["name"],face=face,rect=[x,y,x+w,y+h]))
        x+=w+4;row=max(row,h)
    models={}
    for part,specs in d["parts"].items():
        es=[]
        for spec in specs:
            e=copy.deepcopy(spec["geometry"]);e["faces"]={f:dict(uv=uvmap[(e["name"],f)],texture="#0") for f in FACES};es.append(e)
        models[part]=dict(credit="W127 Hammerhead | authored opaque semantic volumes / face UV",textures={"0":"destiny:item/weapon/w123/hammerhead","particle":"destiny:item/weapon/w123/hammerhead"},elements=es)
    full=copy.deepcopy(models["body"]);full["elements"]+=copy.deepcopy(models["magazine"]["elements"]+models["cover"]["elements"])
    full["display"]=json.loads((ROOT/BASE).read_bytes())["display"];models["full"]=full
    assert len(full["elements"])<=1000
    d["atlas"]["islands"]=islands;d["atlas"]["used_height"]=y+row+2
    return atlas,models


def inspection(d,models,atlas):
    es=[];groups=[]
    for part in PARTS:
        children=[]
        for e in models[part]["elements"]:
            b=copy.deepcopy(e);r=b.pop("rotation",{})
            b.update(type="cube",uuid=uid(e["name"]),box_uv=False,autouv=0,origin=r.get("origin",[8,8,8]),rotation=[r.get(a,0) for a in "xyz"])
            for f in b["faces"].values():f["texture"]=0;f["uv"]=[v*EDGE/16 for v in f["uv"]]
            es.append(b);children.append(b["uuid"])
        groups.append(dict(name=part,uuid=uid(part),origin=HINGE if part=="cover" else [8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={"format_version":"4.10","model_format":"free","box_uv":False},name="Hammerhead W127 | OFFLINE inspection",resolution={"width":EDGE,"height":EDGE},elements=es,outliner=groups,
        textures=[dict(name="hammerhead.png",id="0",uuid=uid("texture"),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source="data:image/png;base64,"+base64.b64encode(png(atlas)).decode())],display=models["full"]["display"],
        destiny_w127=dict(nativeAccepted=False,rotationOrder="RzRyRx",coverPivot=HINGE,sourceAnchor=d["source"]["anchor"],sourceScale=d["source"]["scale"],reloadFramePolicy=d["anchor_policy"]))


def source_triangles(meshes,opened=False):
    textures={n:np.asarray(Image.open(RAW/(n+"_Diffuse.png")).convert("RGBA")) for n in ("HMag","HFrame","HSight")};result=[]
    for m in meshes:
        for ps,uv,part in zip(m["vertices"][m["faces"]],m["uv"],m["parts"]):
            ps=ps.copy()
            if opened and part=="cover":ps=(ps-np.array(HINGE))@rotation({"x":-92}).T+HINGE
            if opened and part=="magazine":ps+=np.array([-2.8,-5.2,.8])
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);l=np.linalg.norm(n)
            if l>1e-10:result.append((ps,uv,textures[m["material"]],n/l))
    return result


def posed_triangles(models,atlas):
    result=[]
    for part in PARTS:
        for ps,uv,tex,n in model_triangles({part:models[part]},atlas):
            if part=="cover":
                R=rotation({"x":-92});ps=(ps-np.array(HINGE))@R.T+HINGE;n=R@n
            if part=="magazine":ps=ps+np.array([-2.8,-5.2,.8])
            result.append((ps,uv,tex,n))
    return result


def comparison(d,meshes,atlas,models):
    w,h=880,300;sheet=Image.new("RGB",(w*3,2060),"#151c25");draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=20):draw.text((x,y),s,fill="#e3e7ed",font_size=size)
    label(20,15,"HAMMERHEAD / W127 / authored broad volumes + face UV / OFFLINE ART INSPECTION",28)
    photo=Image.open(PHOTO).convert("RGB").crop((410,170,1880,790));photo.thumbnail((1550,375));sheet.paste(photo,(20,65))
    label(1640,100,"DEFAULT PAINT REFERENCE",23)
    label(1640,150,"Long black/red Black Armory MG",20)
    label(1640,192,"Twin drums / rigid feed belt",20)
    label(1640,234,"Real carry / stock / muzzle / sight gaps",20)
    label(1640,276,"Cover opens about ORIGINAL hinge",20)
    label(20,447,"RAW FBX / 25,499 triangles / undyed diffuse")
    label(w+20,447,"CANONICAL / 223 cuboids")
    label(2*w+20,447,f"W127 / {len(models['full']['elements'])} opaque cuboids")
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+"textures/item/weapon/w30/hammerhead.png"))
    tri=[source_triangles(meshes),model_triangles({"old":old},oldtex),model_triangles({"full":models["full"]},atlas)]
    points=np.concatenate([m["vertices"] for m in meshes])
    for row,(name,cam) in enumerate([("SIDE",[1,0,0]),("FRONT OBLIQUE",[1,.52,-.62]),("REAR OBLIQUE",[-1,.42,.62])]):
        ext=frame(points,cam,w,h)
        for col,ts in enumerate(tri):
            im,_=render(ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,485+row*h));label(col*w+15,492+row*h,name,18)
    cam=[1,.45,-.5];opened=posed_triangles(models,atlas)
    ps=np.concatenate([t[0] for t in opened]);ext=frame(ps,cam,1320,360)
    for i,ts in enumerate([source_triangles(meshes,True),opened]):
        im,_=render(ts,cam,ext,(1320,360),raw=i==0);sheet.paste(im,(i*1320,1392));label(i*1320+15,1400,"RAW / OPEN COVER + FEED REMOVED" if i==0 else "W127 / SAME ORIGINAL HINGE + FEED OFFSET",19)
    for i,group in enumerate(["muzzle","sight","carry","stock"]):
        names={s["geometry"]["name"] for ss in d["parts"].values() for s in ss if s["group"]==group}
        sub=[e for e in models["full"]["elements"] if e["name"] in names];ps=np.concatenate([vertices(e) for e in sub])
        cam=[.3,.1,-1] if group in ("muzzle","sight") else [1,.28,-.25]
        im,_=render(model_triangles({"sub":dict(elements=sub)},atlas),cam,frame(ps,cam,660,240),(660,240))
        sheet.paste(im,(i*660,1760));label(i*660+12,1765,group.upper()+" / actual opening",18)
    label(20,2020,"Shared camera/scale within rows. Offline raster only. Native parser / pack / held, ADS, reload / 10-20 displays: pending master.",18)
    return png(sheet)


def review_text(counts):
    return f"""# Hammerhead W127 offline art review

New design from functional volumes; no W115 source-fitted geometry reused.
{counts['full']} opaque cuboids = body {counts['body']} + magazine {counts['magazine']} + cover {counts['cover']}.
All emitted native elements counted once in the assembly, including moving parts.
No alpha body plates, triangle adapters, or source-island wall fitting.

Reference: supplied default-paint oblique photo and inert local FBX / diffuse PNG.
Long charcoal continuous shroud, exposed red rails, narrow fork muzzle, twin drums,
red tipped lateral belt, skeleton stock, forward carry handle and open reflex sight.
Broad receiver/roof/stock volumes have authored seams, vent lines, restrained grain,
and fasteners in independent per-face UVs. Solid drum caps use world-aligned radial
paint across a small octagonal decomposition, with true raised opaque rims. Ring-wall caps have tiny axial staggers to avoid
coincident surfaces at their joins; the muzzle ring is recessed behind its fork.

Full is byte-for-byte element concatenation body + magazine + cover; canonical
223 elements also partition as 183+25+15, with no canonical/reload delta.
Native full display is copied exactly. Anchor [8,8,8], W30 scale
23.3089771408205, axis (X,Z,Y), muzzle -Z are retained. Cover remains in original
absolute local coordinates with hinge {HINGE}; the sight belongs to cover.
Parts intentionally omit display so existing W114 wrappers own all poses.
Open-cover raster uses -92 degrees about this hinge, magazine offset [-2.8,-5.2,.8],
matching W114 relative pose at progress .48 (shared body pose omitted for clarity).
No animation graph, timing, sound, reticle, registration or shared manifest edited.

comparison.png includes source / canonical / new side and two oblique rows,
source/new open-cover pose, and close views of muzzle, sight, carry and stock.
inspection.bbmodel embeds the atlas, display and three parts; cover group has the
original hinge. Raster is a Python orthographic inspection, not native evidence.

Known limits: simplified corners/octagonal drums, fixed satin paint, rigid belt,
no extracted animation or dynamic PBR; reverse paint is conservative from one
oblique reference. Native pack/parser, held first/third person, ADS, inspection,
twohand, hinge/cover and feed detach/reinsert, plus 10-20 displays are master QA.
"""


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,models=compile_models(d)
    counts={p:len(models[p]["elements"]) for p in (*PARTS,"full")}
    outputs={ART+"design.json":encode(d),TEXTURE:png(atlas),ART+"inspection.bbmodel":encode(inspection(d,models,atlas)),ART+"review.md":review_text(counts).encode()}
    for p,m in models.items():outputs[MODEL+("" if p=="full" else "_"+p)+".json"]=encode(m)
    manifest=dict(stage="W127",id="hammerhead",family="machine_gun",counts=counts,emitted_faces=counts["full"]*6,
        maximum_assembled_elements=1000,opaque_cuboids=counts["full"],alpha_body_plates=0,triangle_adapter_elements=0,
        canonical_counts=dict(full=223,body=183,magazine=25,cover=15),canonical_reload_delta=0,
        full_is_body_plus_magazine_plus_cover=True,canonical_display_exact=True,part_display_absent=True,
        cover_pivot=HINGE,anchor=meta["anchor"],scale=meta["scale"],source_triangles=meta["source_triangles"],
        texture_size=[EDGE,EDGE],face_uv_islands=len(d["atlas"]["islands"]),atlas_used_height=d["atlas"]["used_height"],
        worst_two_feeds=counts["body"]+counts["cover"]+2*counts["magazine"],
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d["input_sha256"],raw_input_sha256=d["raw_input_sha256"],
        output_sha256={p:sha(b) for p,b in sorted(outputs.items())},native_accepted=False,
        validation=dict(targeted_python="scripts/qa/test_surface_w123_hammerhead.py",native_parser="pending master",gameplay="pending master",performance="not measured; offline only"),limitations=d["limitations"])
    outputs[ART+"manifest.json"]=encode(manifest)
    from fix_belt_feed_w154 import finish_outputs
    return finish_outputs("hammerhead",outputs,include_comparison)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--verify",action="store_true");args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/"docs/qa/2026-10-26/w127/batch.json").read_bytes())
    owned=set(next(f["owned_paths"] for f in batch["features"] if f["name"]=="w127-hammerhead"))
    assert len(owned)==13 and set(outputs)<=owned
    for p,data in outputs.items():
        dst=ROOT/p
        if args.verify:assert dst.is_file() and dst.read_bytes()==data,"Regeneration differs: "+p
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
    m=json.loads(outputs[ART+"manifest.json"])
    print(("Verified" if args.verify else "Generated")+f" {len(outputs)} artifacts; {m['counts']}; {m['emitted_faces']} faces")

if __name__=="__main__":main()
