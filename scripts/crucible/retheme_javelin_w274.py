#!/usr/bin/env python3
"""W274: Javelin-4 art + playability pass over the W260 baked voxels (original kept in art/crucible).
Siberian launch-complex look: cold slate concrete, snow, safety orange, patinated copper.
Adds recessed 'light' blocks (indoor), cover props, capture pads and spawn pads.
Deterministic. Usage: python3 retheme_javelin_w274.py  (needs numpy)."""
import gzip,struct,json,sys,collections
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
SRC_VOX=ROOT/'art/crucible/javelin4_w260_original.vox.gz';SRC_JSON=ROOT/'art/crucible/javelin4_w260_original.json'
OUT_VOX=ROOT/'src/main/resources/data/destiny/crucible/javelin4.vox.gz';OUT_JSON=ROOT/'src/main/resources/data/destiny/crucible/javelin4.json'
LO=np.array([-150,66,-110]);DIMS=np.array([300,90,230])

def read(path):
    d=gzip.open(path).read();assert d[:8]==b'DGCRU001';o=8;n=struct.unpack('>i',d[o:o+4])[0];o+=4;pal=[]
    for _ in range(n):
        l=struct.unpack('>H',d[o:o+2])[0];o+=2;pal.append(d[o:o+l].decode());o+=l
    o+=4;a=np.frombuffer(d[o:],dtype=[('x','>i4'),('y','>i4'),('z','>i4'),('p','>u2')])
    return pal,np.stack([a['x'],a['y'],a['z'],a['p']],1).astype(np.int64)

def write(path,pal,xyz,pid):
    order=np.lexsort((xyz[:,2],xyz[:,0],xyz[:,1],xyz[:,2]>>4,xyz[:,0]>>4))
    rec=np.empty(len(xyz),dtype=[('x','>i4'),('y','>i4'),('z','>i4'),('p','>u2')])
    rec['x']=xyz[order,0];rec['y']=xyz[order,1];rec['z']=xyz[order,2];rec['p']=pid[order]
    body=struct.pack('>i',len(pal))+b''.join(struct.pack('>H',len(s.encode()))+s.encode() for s in pal)+struct.pack('>i',len(xyz))+rec.tobytes()
    with gzip.GzipFile(path,'wb',mtime=0) as f:f.write(b'DGCRU001'+body)

def h3(x,y,z,seed):
    n=(x*374761393+y*668265263+z*2147483647+seed*1274126177)&0xFFFFFFFF
    n=((n^(n>>13))*1274126177)&0xFFFFFFFF
    return ((n^(n>>16))&0xFFFF)/65535.0
def vnoise(x,y,z,scale,seed):
    fx,fy,fz=x/scale,y/scale,z/scale;ix,iy,iz=np.floor(fx).astype(np.int64),np.floor(fy).astype(np.int64),np.floor(fz).astype(np.int64)
    tx,ty,tz=fx-ix,fy-iy,fz-iz;sm=lambda t:t*t*(3-2*t);tx,ty,tz=sm(tx),sm(ty),sm(tz);r=0
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1):
                w=(tx if dx else 1-tx)*(ty if dy else 1-ty)*(tz if dz else 1-tz);r=r+w*h3(ix+dx,iy+dy,iz+dz,seed)
    return r
def pick(n,table):
    """table: [(block,weight)...]; n in [0,1) -> block name array"""
    w=np.array([t[1] for t in table],float);c=np.cumsum(w)/w.sum();idx=np.minimum(np.searchsorted(c,n,side='right'),len(table)-1)
    return idx,[t[0] for t in table]

def main():
    pal,a=read(SRC_VOX);names=np.array([p.split(':')[1] for p in pal]);orig=names[a[:,3]]
    x,y,z=a[:,0],a[:,1],a[:,2];q=a[:,:3]-LO
    occ=np.zeros(DIMS,bool);occ[tuple(q.T)]=True
    pad=np.pad(occ,1)
    nb=lambda dx,dy,dz:pad[1+q[:,0]+dx,1+q[:,1]+dy,1+q[:,2]+dz]
    top=~nb(0,1,0);bottom=~nb(0,-1,0);side=~nb(1,0,0)|~nb(-1,0,0)|~nb(0,0,1)|~nb(0,0,-1)
    exposed=top|bottom|side
    # outdoors: nothing solid above this cell in the column
    colmax=np.full((DIMS[0],DIMS[2]),-1);np.maximum.at(colmax,(q[:,0],q[:,2]),q[:,1]);outdoor=colmax[q[:,0],q[:,2]]<=q[:,1]
    n1=vnoise(x,y,z,9,1);n2=vnoise(x,y,z,4,2);nh=h3(x,y,z,3);nw=vnoise(x,y,z,22,4)
    out=np.array([p.split(':')[1] for p in pal])[a[:,3]].astype(object)  # default: unchanged
    role=np.full(len(a),'keep',dtype=object)
    structural={'stone_bricks','smooth_stone','polished_andesite','light_gray_concrete','gray_concrete','polished_deepslate','light_gray_terracotta','gray_terracotta','black_concrete','iron_block'}
    whites={'white_terracotta','white_concrete','smooth_quartz','quartz_bricks'}
    hazards={'yellow_terracotta','yellow_concrete','orange_terracotta','orange_concrete'}
    rusts={'mud_bricks','brown_concrete','brown_terracotta','cut_sandstone','smooth_sandstone','cut_copper','red_terracotta'}
    for r,s in (('struct',structural),('white',whites),('hazard',hazards),('rust',rusts)):role[np.isin(orig,list(s))]=r
    role[orig=='cyan_terracotta']='cyan';role[orig=='red_wool']='red';role[orig=='sea_lantern']='lamp'
    def setm(mask,table,noise):
        if not mask.any():return
        idx,bl=pick(noise[mask],table);out[mask]=np.array(bl,dtype=object)[idx]
    floorf=top&exposed;wall=side&~top&~bottom;ceil=bottom&~top
    tile=((x//4+z//4)&1);seam=((x%8==0)|(z%8==0))
    # ---- structural / cyan shells -------------------------------------------------
    shell=(role=='struct')|(role=='cyan')
    ind_floor=shell&floorf&~outdoor
    setm(ind_floor&(tile==0),[('smooth_stone',4),('polished_andesite',3),('light_gray_concrete',2),('stone',1)],n2)
    setm(ind_floor&(tile==1),[('gray_concrete',3),('andesite',2),('smooth_stone',2),('deepslate_tiles',1)],n2)
    out[ind_floor&((x%16==0)|(z%16==0))]='polished_deepslate'
    wear=ind_floor&(nw>.72);setm(wear,[('cracked_stone_bricks',3),('stone',2),('gray_concrete',2)],nh)
    # hazard edge lines every 16 blocks on indoor floors
    out[ind_floor&((x%16==0)|(z%16==0))&(tile==0)]='orange_concrete'
    out_floor=shell&floorf&outdoor
    setm(out_floor,[('snow_block',62),('white_concrete',14),('packed_ice',5),('light_gray_concrete',9),('stone',6),('calcite',4)],np.clip(n1*.7+nh*.3,0,.999))
    out[out_floor&(n1>.72)&(n2>.5)]='blue_ice'
    wallm=shell&wall&(role!='keep')
    panel=(((x+z)//4+y//4)&1)
    setm(wallm&(panel==0),[('light_gray_concrete',4),('stone_bricks',3),('white_concrete',2),('polished_andesite',2)],n1)
    setm(wallm&(panel==1),[('gray_concrete',3),('cyan_terracotta',1),('gray_concrete',3),('stone_bricks',3),('deepslate_bricks',1)],n1)
    out[wallm&(y%8==0)]='gray_concrete'
    out[wallm&(y%16==5)]='orange_concrete'          # high-visibility belt
    out[wallm&outdoor&(y%5<2)&(n1>.55)]='snow_block'  # wind-blown snow on outdoor walls
    ceilm=shell&ceil
    setm(ceilm,[('deepslate_tiles',4),('polished_deepslate',3),('gray_concrete',3)],n2)
    out[ceilm&(x%6==0)&(z%6==0)]='sea_lantern'
    out[shell&top&bottom]=out[shell&top&bottom]  # slabs keep chosen top
    # remaining shell interior stays as before to keep payload stable
    # ---- white panels -----------------------------------------------------------
    wm=(role=='white')&exposed
    setm(wm,[('white_concrete',5),('calcite',3),('quartz_bricks',2),('light_gray_concrete',2),('light_blue_concrete',1)],n2)
    # ---- hazard ----------------------------------------------------------------
    hz=(role=='hazard')&exposed
    stripe=(((x+y+z)//2)%4==0)
    setm(hz,[('orange_terracotta',5),('orange_concrete',4),('yellow_terracotta',1)],n2)
    hzfloor=hz&top&~outdoor|hz&top&outdoor
    diag=((x+z)%8)<4
    out[hzfloor&diag]='orange_concrete'
    out[hzfloor&~diag]=np.where((nh[hzfloor&~diag]>.5),'gray_concrete','light_gray_concrete')
    # ---- rust/copper patina ---------------------------------------------------
    rm=(role=='rust')&exposed
    setm(rm,[('cut_copper',3),('exposed_cut_copper',4),('weathered_cut_copper',2),('oxidized_cut_copper',1)],n1)
    # ---- red rocket stripes ----------------------------------------------------
    out[role=='red']='red_concrete'
    arr_pal=sorted(set(out.tolist())|{'light','orange_concrete','white_concrete','cyan_concrete','light_blue_concrete','black_concrete','yellow_concrete','smooth_quartz','sea_lantern','stone','deepslate_tiles','gray_concrete','smooth_stone','polished_andesite','polished_deepslate','light_gray_concrete','orange_terracotta'})
    # ---- build new voxel list with additions ----------------------------------
    new={}  # (x,y,z)->block name
    for xi,yi,zi,b in zip(x.tolist(),y.tolist(),z.tolist(),out.tolist()):new[(xi,yi,zi)]=b
    man=json.loads(SRC_JSON.read_text());idx3={k for k in new}
    # walkable floor cells (3 clear above, solid below) on the combat band
    floor=np.zeros(DIMS,bool);floor[:,1:-4,:]=occ[:,:-5,:]&~occ[:,1:-4,:]&~occ[:,2:-3,:]&~occ[:,3:-2,:]&~occ[:,4:-1,:]
    floor[:,:10,:]=False;floor[:,45:,:]=False
    # largest connected floor component = real combat network
    pts=set(map(tuple,np.argwhere(floor)));un=set(pts);best=set()
    while un:
        f=un.pop();dq=collections.deque([f]);comp={f}
        while dq:
            cx,cy,cz=dq.popleft()
            for dx,dz in((1,0),(-1,0),(0,1),(0,-1)):
                for dy in(0,1,-1):
                    nn=(cx+dx,cy+dy,cz+dz)
                    if nn in un:
                        low=(cx,cy,cz) if dy>=0 else nn
                        if dy and occ[low[0],low[1]+3,low[2]]:continue
                        un.remove(nn);dq.append(nn);comp.add(nn)
        if len(comp)>len(best):best=comp
    W=lambda c:(c[0]-150,c[1]+66,c[2]-110)  # floor cell -> feet world coords
    feet=[W(c) for c in best];feetset=set(feet)
    def clearbox(fx,fy,fz,r,h=4):
        for dx in range(-r,r+1):
            for dz in range(-r,r+1):
                if (fx+dx,fy,fz+dz) not in feetset:return False
                for dy in range(0,h):
                    if (fx+dx,fy+dy,fz+dz) in idx3:return False
        return True
    keepaway=[(s['x'],s['y'],s['z']) for s in man['alphaSpawns']+man['bravoSpawns']]+[(zn['center']['x'],zn['center']['y'],zn['center']['z']) for zn in man['zones']]
    # indoor lights: one invisible light block on a 5-block lattice above the walkable network
    lights=0
    for fx,fy,fz in feet:
        if fx%4==0 and fz%4==0 and colmax[fx+150,fz+110]>fy-66+4:  # covered => indoor
            p=(fx,fy+3,fz)
            if p not in new:new[p]='light[level=15]';lights+=1
    # capture pads + spawn pads
    def disc(cx,cy,cz,r_in,r_out,inner,ring):
        R=int(np.ceil(r_out));
        for dx in range(-R-1,R+2):
            for dz in range(-R-1,R+2):
                d=(dx*dx+dz*dz)**.5;p=(int(np.floor(cx))+dx,int(cy)-1,int(np.floor(cz))+dz)
                if p in new and d<=r_out+.5:
                    sector=int(((np.arctan2(dz,dx)+np.pi)/(2*np.pi))*8)%8
                    new[p]=inner if d<=r_in else (ring if sector%2==0 else 'white_concrete')
    for zn in man['zones']:
        c=zn['center'];disc(c['x'],c['y'],c['z'],3.2,4.6,'smooth_quartz','orange_concrete')
        disc(c['x'],c['y'],c['z'],1.2,1.2,'light_blue_concrete','light_blue_concrete')
    for s in man['alphaSpawns']:disc(s['x'],s['y'],s['z'],1.4,2.2,'white_concrete','cyan_concrete')
    for s in man['bravoSpawns']:disc(s['x'],s['y'],s['z'],1.4,2.2,'white_concrete','orange_concrete')
    # cover props on open ground
    rng=np.random.default_rng(274);cand=[f for f in feet if clearbox(f[0],f[1],f[2],3)];rng.shuffle(cand)
    placed=[];props=0
    def far(f,rad):return all((f[0]-k[0])**2+(f[2]-k[2])**2>rad*rad for k in keepaway)
    for f in cand:
        if not far(f,13):continue
        if any((f[0]-p[0])**2+(f[2]-p[2])**2<16*16 for p in placed):continue
        kind=len(placed)%3;fx,fy,fz=f;along_x=bool(rng.integers(2))
        if kind==0:   # shipping container 6x2x2, jump-over not required; paths remain open around it
            for i in range(-3,3):
                for j in (0,1):
                    for k in range(2):
                        p=(fx+(i if along_x else j),fy+k,fz+(j if along_x else i))
                        new[p]=('orange_concrete' if (i+3)%3 else 'orange_terracotta') if k==1 else 'light_blue_concrete'
            for i in range(-3,3):  # roof stripe
                p=(fx+(i if along_x else 0),fy+1,fz+(0 if along_x else i));new[p]='white_concrete' if i%2 else 'orange_concrete'
        elif kind==1: # jump-height barrier wall 5x1
            for i in range(-2,3):
                p=(fx+(i if along_x else 0),fy,fz+(0 if along_x else i));new[p]='stone_bricks' if i%2 else 'gray_concrete'
            for i in (-2,2):
                p=(fx+(i if along_x else 0),fy,fz+(0 if along_x else i));new[p]='orange_concrete'
        else:         # stacked crates 2x2 + 1 block
            for i in range(2):
                for j in range(2):
                    for k in range(2):new[(fx+i,fy+k,fz+j)]='barrel_placeholder' if False else ('stripped_oak_log' if k==0 else 'spruce_planks')
            new[(fx,fy+2,fz)]='orange_concrete'
        placed.append(f);props+=1
        if props>=34:break
    keys=list(new.keys());names_out=[new[k] for k in keys]
    final=sorted(set(names_out));ids={'minecraft:'+n:i for i,n in enumerate(final)}
    palette=['minecraft:'+n for n in final];pid=np.array([ids['minecraft:'+n] for n in names_out],np.int64)
    xyz=np.array(keys,np.int64)
    write(OUT_VOX,palette,xyz,pid)
    man['blockCount']=int(len(xyz));man['bounds']={'min':xyz.min(0).tolist(),'max':xyz.max(0).tolist()}
    man['artProvenance']='W274 retheme of W260 Javelin-4 bake: Siberian launch-complex palette, indoor light blocks, capture/spawn pads and cover props. Original in art/crucible.'
    OUT_JSON.write_text(json.dumps(man,ensure_ascii=False,indent=2)+'\n')
    cnt=collections.Counter(names_out);print('voxels',len(xyz),'lights',lights,'props',props,'palette',len(palette))
    for k,v in cnt.most_common(18):print(f'{v/len(xyz)*100:5.1f}% {k}')
if __name__=='__main__':main()
