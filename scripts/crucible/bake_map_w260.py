#!/usr/bin/env python3
"""Crop-first Javelin-4 surface/material bake. Originals are always read-only.
Requires numpy/Pillow and the repository's scripts/tower helpers. No Blender, game,
server or dependency mutation. --out receives only derived artifacts.
"""
from pathlib import Path
import os, sys, json, argparse, time, hashlib, gzip, struct, collections, math, re
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[2]
ROOT=Path(os.environ.get('DESTINY_SOURCE_ROOT',str(ROOT)))
sys.path.insert(0,str(ROOT/'scripts/tower'))
from tower_mesh import GLB,transform_bounds,overlaps
from voxelize_courtyard import surface_cells,barycentric_at_cells,Materials,sample_uv,linear_to_srgb,srgb_to_linear
from material_shader_w245 import MaterialBaker,SHADERS

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def geometry(c,out):
 g=GLB(c['source']); scale=c['scale'];offset=np.array(c['offset']);lo=np.floor(np.array(c['cropMin'])*scale+offset).astype(int);hi=np.ceil(np.array(c['cropMax'])*scale+offset).astype(int)-1;dims=hi-lo+1
 if int(np.prod(dims))>20_000_000:raise ValueError('Crop memory budget exceeded')
 mg=np.full(dims,-1,np.int16);ug=np.zeros(tuple(dims)+(2,),np.float32);ng=np.zeros(tuple(dims)+(3,),np.float32);terrain=np.zeros(dims,bool);quality=np.full(dims,-np.inf,np.float32)
 excluded=set()
 for i,m in enumerate(g.doc['materials']):
  material=json.loads((Path(c['materials'])/'Materials'/f"{m['name']}.json").read_text());shader=material['Material']['Pixel']['Hash'];hlsl=(Path(c['materials'])/'Shaders/HLSL'/f'PS_{shader}.hlsl').read_text()
  if 'SV_TARGET1' not in hlsl:excluded.add(i)
 stats=collections.Counter();selected=[];start=time.monotonic();last=start
 for ni,mi,w in g.world_instances():
  mesh=g.doc['meshes'][mi];a,b=transform_bounds(*g.mesh_bounds(mi),w)
  if not overlaps(a,b,np.array(c['cropMin']),np.array(c['cropMax'])):stats['outsideInstances']+=1;continue
  if np.max(b-a)>c['maxInstanceSpan']:stats['backdropInstances']+=1;continue
  stats['includedInstances']+=1;selected.append(ni)
  for p in mesh['primitives']:
   mat=p.get('material',-1)
   if mat<0 or mat in excluded:stats['excludedEffectPrimitives']+=1;continue
   attrs=p['attributes'];verts=g.accessor(attrs['POSITION'])@w[:3,:3].T+w[:3,3];verts=verts*scale+offset
   inds=g.accessor(p['indices']).reshape(-1,3);tris=verts[inds];inside=np.all(tris.max(1)>=lo,axis=1)&np.all(tris.min(1)<=hi+1,axis=1);inds=inds[inside];tris=tris[inside]
   uv=g.accessor(attrs['TEXCOORD_0']) if 'TEXCOORD_0'in attrs else None
   stats['includedTriangles']+=len(tris)
   for begin in range(0,len(tris),2048):
    tri=tris[begin:begin+2048];ind=inds[begin:begin+2048]
    for cells,ti in surface_cells(tri,lo,hi):
     norm=np.cross(tri[ti,1]-tri[ti,0],tri[ti,2]-tri[ti,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-12)
     # Closest plane to voxel center wins, with stable source traversal tie order.
     distance=np.abs(np.sum((cells+.5-tri[ti,0])*norm,axis=1));q=cells-lo;score=-distance
     unique=np.ravel_multi_index(q.T,dims);order=np.lexsort((-score,unique));unique2=unique[order];order=order[np.r_[True,unique2[1:]!=unique2[:-1]]];q=q[order];ti=ti[order];norm=norm[order];score=score[order];cells=cells[order]
     good=score>quality[tuple(q.T)];q=q[good];ti=ti[good];norm=norm[good];cells=cells[good];score=score[good]
     if not len(q):continue
     tex=np.einsum('ni,nij->nj',barycentric_at_cells(tri[ti],cells),uv[ind[ti]]) if uv is not None else np.full((len(q),2),np.nan)
     key=tuple(q.T);mg[key]=mat;ug[key]=tex;ng[key]=norm;terrain[key]=mesh.get('extras',{}).get('terrain',False);quality[key]=score
  if time.monotonic()-last>15:print('geometry',dict(stats),round(time.monotonic()-start,1),flush=True);last=time.monotonic()
 xyz=np.argwhere(mg>=0);key=tuple(xyz.T)
 np.savez_compressed(out/'geometry.npz',xyz=xyz+lo,material=mg[key],uv=ug[key],normal=ng[key],terrain=terrain[key])
 write_json(out/'geometry-audit.json',{'source':c['source'],'sha256':sha(c['source']),'sourceRootConversion':'glTF node ancestor composition exactly once; Destiny Zup -> glTF Yup','bounds':{'min':lo.tolist(),'max':hi.tolist()},'stats':dict(stats),'sourceInstances':selected,'surfaceCells':len(xyz),'seconds':time.monotonic()-start})
 print('geometry complete',len(xyz),flush=True)

class CrucibleBaker(MaterialBaker):
    """Explicit basecolor equations read from Javelin PS HLSL, not slot guesses."""
    RAMP_G={'80B2416E','80B242A7'}
    RAMP_A={'80B24168'}
    MASK={'80B24190','80B2413F','80B24296','80B243D2'}
    KNOWN=RAMP_G|RAMP_A|MASK|{'80B242F8','80B2403C','80B24017'}
    def _texture(self,spec):
        key=(spec['Hash'],spec['Colorspace'])
        a=super()._texture(spec)
        if max(a.shape[:2])>256:
            # Box-filter LINEAR channels before sampling: suppress sub-block texel aliasing.
            h,w=a.shape[:2];ratio=256/max(h,w);size=(max(1,round(w*ratio)),max(1,round(h*ratio)))
            reduced=np.stack([np.asarray(Image.fromarray(a[:,:,i],mode='F').resize(size,Image.Resampling.BOX)) for i in range(4)],axis=2)
            self._cache_bytes+=reduced.nbytes-a.nbytes;self._cache[key]=reduced;a=reduced
        return a
    def sample_javelin(self,tag,uv,world,normal):
        d,p,c=self.materials[tag];s=p['Hash'];sat=lambda a:np.clip(a,0,1)
        T=lambda i,q: self._sample_texture(p,i,q)
        if s in self.RAMP_G|self.RAMP_A:
            q=uv*c[3,:2]+c[3,2:];t=T(0,q);v=t[:,1:2] if s in self.RAMP_G else t[:,3:4]
            rgb=c[0,:3]+c[1,:3]*sat(v)
        elif s in self.MASK:
            q=T(1,uv*c[0,:2]+c[0,2:]);a=c[1]+c[2]*sat(q[:,3:4]);b=c[3]+c[4]*sat(q[:,3:4]);cc=c[5]+c[6]*sat(q[:,1:2]);base=np.where(uv[:,0:1]>0,a,b);t=T(0,uv)
            w=t[:,0:1] if s in {'80B24296','80B243D2'} else np.where(uv[:,1:2]>1,t[:,0:1],1)
            color=base+(cc-base)*w;w=sat(c[8,0]+c[8,1]*t[:,1:2]);rgb=(color+(c[7]-color)*w)[:,:3]
        elif s=='80B242F8':
            q=uv*c[0,:2]+c[0,2:];a=T(0,q)[:,:3]*c[1,:3];w=sat(c[3,0]+c[3,1]*T(1,q)[:,0:1]);rgb=a+(c[2,:3]-a)*w
        elif s=='80B2403C':
            # View-dependent parallax transition unavailable: fixed blend 0.
            t=T(1,uv);v=(world[:,0:1]-world[:,2:3])*c[2,0]+world[:,2:3];v=v*c[3,0]+c[4,0]+c[4,1]*t[:,0:1];lookup=T(3,np.repeat(v,2,axis=1));a=T(0,uv*c[0,:2]+c[0,2:])[:,:3];rgb=a*lookup[:,:3]*(c[7,:3]+c[8,:3]*sat(lookup[:,3:4]))
        elif s=='80B24017':
            a=T(0,uv*c[0,:2]+c[0,2:])[:,:3];t=T(1,uv);v=(world[:,0:1]-world[:,2:3])*c[2,0]+world[:,2:3];v=v*c[3,0]+c[5,0]+c[5,1]*t[:,0:1]*(c[4,0]+c[4,1]*a[:,1:2])*4.59479332;lut=T(2,np.repeat(v,2,axis=1));base=a*lut[:,:3]*(c[11,:3]+c[12,:3]*sat(lut[:,3:4]));w=sat(normal[:,2:3]*c[13,0]+c[13,1]);rgb=base+(a-base)*w
        else:return None
        return linear_to_srgb(np.clip(rgb,0,1))

def bake(c,out):
    g=GLB(c['source']);d=np.load(out/'geometry.npz');xyz=d['xyz'];mid=d['material'];uv=d['uv'];normal=d['normal'];terrain=d['terrain'];baker=CrucibleBaker(c['materials'],allow_representative=True,cache_mb=128)
    rgb=np.zeros((len(xyz),3),np.float32);keep=np.ones(len(xyz),bool);report={};swatches=[];counts=collections.Counter();offset=np.array(c['offset']);world=(xyz+.5-offset)/c['scale'];world=np.column_stack((world[:,0],-world[:,2],world[:,1]));norm=np.column_stack((normal[:,0],-normal[:,2],normal[:,1]));psuv=uv.copy();psuv[:,1]=1-psuv[:,1]
    aliases=c.get('shaderAliases',{});root=Path(c['materials'])
    for i in np.unique(mid):
        m=g.doc['materials'][i];tag=m['name'];sel=np.flatnonzero(mid==i);p=baker.materials[tag][1];s=p['Hash'];h=root/'Shaders/HLSL'/f'PS_{s}.hlsl';hlsl=h.read_text();r={'surfaceCells':len(sel),'shader':s,'shaderSHA256':sha(h),'materialSHA256':sha(root/'Materials'/f'{tag}.json'),'uvContract':'Static exported UV: (u,1-v); terrain UV remains unverified approximation','textures':p['Textures'],'dynamicCBufferOutputs':[x for x in p.get('Bytecode',[]) if x.startswith('PopOutput:')]};col=None
        if 'SV_TARGET1' not in hlsl:
            keep[sel]=False;r['method']='excluded_non_gbuffer_effect';report[tag]=r;continue
        if s in baker.KNOWN and not terrain[sel].any():
            col=baker.sample_javelin(tag,psuv[sel],world[sel],norm[sel]);r['method']='hlsl_basecolor_static_snapshot';counts['hlslCells']+=len(sel)
            if s=='80B2403C':r['substitute']='view/parallax transition weight fixed at zero'
            if s=='80B24017':r['substitute']='geometric world normal; source tangent-space normal unavailable'
        elif s in aliases and not terrain[sel].any():
            # Alias verified by complete comment/whitespace-stripped HLSL equality.
            assert hashlib.sha256(re.sub(r'\s+','',re.sub(r'//[^\n]*','',hlsl)).encode()).hexdigest()==c['shaderAliasDigests'][s], 'shader alias body drift'
            canonical=aliases[s];original=p['Hash'];p['Hash']=canonical;baker.recipes[tag]['supported']=True;baker.recipes[tag]['family']=SHADERS[canonical]
            col,valid=baker.sample(tag,psuv[sel],inputs={'world_xyz':world[sel],'normal':norm[sel]});p['Hash']=original
            if not valid.all():col=None
            else:r['method']='verified_equivalent_hlsl';r['canonicalShader']=canonical;counts['hlslCells']+=len(sel)
        if col is None:
            info=m.get('pbrMetallicRoughness',{}).get('baseColorTexture')
            if info is not None:
                image,sampler=g.texture(info['index']);col=sample_uv(uv[sel],image,sampler)[:,:3];r['method']='delivered_texture_heuristic';r['texture']=m.get('extras',{}).get('sourceTexture');counts['approxTextureCells']+=len(sel)
            else:
                col=np.tile(m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[.5,.5,.5,1])[:3],(len(sel),1));r['method']='unresolved_neutral';counts['unresolvedCells']+=len(sel)
        if not np.isfinite(col).all():raise ValueError('nonfinite bake '+tag)
        rgb[sel]=np.clip(col,0,1);r['medianSrgb']=np.median(col,axis=0).tolist();report[tag]=r
        if r['method']=='hlsl_basecolor_static_snapshot':
            side=96;u,v=np.meshgrid((np.arange(side)+.5)/side,(np.arange(side)+.5)/side);q=np.stack((u.ravel(),v.ravel()),1);center=np.median(world[sel],axis=0);n=np.median(norm[sel],axis=0);color=baker.sample_javelin(tag,q,np.tile(center,(len(q),1)),np.tile(n,(len(q),1)));swatches.append((tag,np.uint8(np.clip(color,0,1).reshape(side,side,3)*255)))
    xyz=xyz[keep];rgb=rgb[keep];mid=mid[keep]
    # Two bounded same-material surface filters suppress sub-block texel noise.
    # Never diffuse across material seams or empty cells.
    lo=xyz.min(0)-1;grid=np.full(xyz.max(0)-lo+2,-1,np.int32);q=xyz-lo;grid[tuple(q.T)]=np.arange(len(xyz))
    for _ in range(2):
        summed=rgb*2;weight=np.full((len(xyz),1),2,np.float32)
        for offset in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            idx=grid[tuple((q+offset).T)];safe=np.maximum(idx,0);valid=(idx>=0)&(mid[safe]==mid)
            summed[valid]+=rgb[safe[valid]];weight[valid]+=1
        rgb=summed/weight
    pal=json.loads((ROOT/c['palette']).read_text());matcher=Materials(g,{'palette':pal});block=matcher.nearest(rgb*255)
    np.savez_compressed(out/'baked.npz',xyz=xyz,rgb=rgb,material=mid,block=block)
    write_json(out/'material-audit.json',{'counts':dict(counts),'prefilter':'linear DDS box mip <=256; two same-material surface-cell smoothing passes before palette quantization','excludedEffectCells':int((~keep).sum()),'materials':report,'limitations':['Static CBuffer snapshots; TFX time/frame overrides are not evaluated.','Normals, reflection, emissive light and engine lighting are not reproduced.','Unknown shader and terrain materials retain explicitly counted delivered heuristic textures.','Source geometry is visual mesh, not original collision/navigation.']})
    w=576;canvas=Image.new('RGB',(w,122*math.ceil(len(swatches)/6)),(22,25,30));draw=ImageDraw.Draw(canvas)
    for i,(tag,a) in enumerate(swatches):x=(i%6)*96;y=(i//6)*122;canvas.paste(Image.fromarray(a),(x,y));draw.text((x+2,y+99),tag,fill='white')
    canvas.save(out/'material-swatches.png');print('material bake',dict(counts),flush=True)
    return xyz,block,pal,rgb

def first_solid(start,end,occupied):
    """Exact finite voxel DDA; cameras cannot start inside or look through blocks."""
    start=np.array(start,float);end=np.array(end,float);direction=end-start
    pos=np.floor(start).astype(int);last=np.floor(end).astype(int);step=np.sign(direction).astype(int)
    delta=np.full(3,np.inf);tmax=np.full(3,np.inf);moving=abs(direction)>1e-12
    delta[moving]=1/abs(direction[moving]);tmax[moving]=abs((pos[moving]+(step[moving]>0)-start[moving])/direction[moving])
    for _ in range(int(abs(last-pos).sum())+4):
        if tuple(pos)in occupied:return list(map(int,pos))
        if np.array_equal(pos,last):return None
        axis=int(np.argmin(tmax));pos[axis]+=step[axis];tmax[axis]+=delta[axis]
    raise ValueError('voxel DDA did not terminate')

def navigation(c,out,xyz,block,pal,rgb):
    lo=xyz.min(0)-2;hi=xyz.max(0)+3;dims=hi-lo+1;occ=np.zeros(dims,bool);occ[tuple((xyz-lo).T)]=True
    floor=np.zeros(dims,bool);floor[:,1:-2,:]=occ[:,:-3,:]&~occ[:,1:-2,:]&~occ[:,2:-1,:]&~occ[:,3:,:]
    # Only the combat elevation band, not building roofs or underworld shells.
    floor[:,:max(0,c['navigationMinY']-lo[1]),:]=False;floor[:,max(0,c['navigationMaxY']+1-lo[1]):,:]=False
    points=np.argwhere(floor)+lo;walk=set(map(tuple,points));components=[];unseen=walk.copy()
    while unseen:
        first=min(unseen);unseen.remove(first);queue=collections.deque([first]);comp={first}
        while queue:
            x,y,z=queue.popleft()
            for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
                for dy in (0,1,-1):
                    q=(x+dx,y+dy,z+dz)
                    if q not in unseen:continue
                    # A jump up needs air above the lower player's head too.
                    lower=(x,y,z) if dy>=0 else q
                    if dy and occ[tuple(np.array(lower)+[0,2,0]-lo)]:continue
                    unseen.remove(q);queue.append(q);comp.add(q)
        components.append(comp)
    components.sort(key=len,reverse=True);major=components[0];candidates=np.array(sorted(major));pad=[]
    for p in candidates:
        x,y,z=map(int,p)
        if all((x+dx,y,z+dz)in major for dx in range(-1,2) for dz in range(-1,2)):pad.append(p)
    pads=np.array(pad);markers=[m for m in json.loads(Path(c['markers']).read_text()) if m['activity']==c['markerActivity'] and m['phase']==c['markerPhase'] and m['name']=='capturable_object'];zones=[];evidence=[]
    def choose(target,yaw=0):
        dist=np.sum((pads-np.array(target))**2*np.array([1,4,1]),axis=1);q=pads[np.argmin(dist)];return {'x':float(q[0])+.5,'y':int(q[1]),'z':float(q[2])+.5,'yaw':float(yaw),'pitch':0.}
    for m in sorted(markers,key=lambda m:m['subname']):
        key=m['subname'][-1].upper();original=np.array([m['minecraft_x'],m['minecraft_y'],m['minecraft_z']]);target=original*c['scale']+np.array(c['offset']);p=choose(target);zones.append({'key':key,'name':f'{key} 거점','center':p,'radius':4.,'height':4.});evidence.append({'key':key,'sourceMarker':m,'transformed':target.tolist(),'floorAdjusted':p,'distance':float(np.linalg.norm(np.array([p['x'],p['y'],p['z']])-target))})
    # Authored team staging: interior flat patches behind A/C toward crop ends.
    alpha=[choose([c['alphaTarget'][0]+dx,c['alphaTarget'][1],c['alphaTarget'][2]+dz],c.get('alphaYaw',-90)) for dx,dz in ((0,0),(0,4),(0,-4),(4,0),(4,4),(4,-4))]
    bravo=[choose([c['bravoTarget'][0]+dx,c['bravoTarget'][1],c['bravoTarget'][2]+dz],90) for dx,dz in ((0,0),(0,4),(0,-4),(-4,0),(-4,4),(-4,-4))]
    alpha=list({(p['x'],p['y'],p['z']):p for p in alpha}.values());bravo=list({(p['x'],p['y'],p['z']):p for p in bravo}.values())
    def shot(key,cam,tgt,duration):return {'key':key,'camera':dict(zip(('x','y','z'),cam),yaw=0.,pitch=0.),'target':dict(zip(('x','y','z'),tgt),yaw=0.,pitch=0.),'durationTicks':duration}
    bounds={'min':xyz.min(0).tolist(),'max':xyz.max(0).tolist()};manifest={'schema':1,'id':c['key'],'key':c['key'],'name':c['name'],'voxelResource':'data/destiny/crucible/javelin4.vox.gz','bounds':bounds,'returnBelowY':c['returnBelowY'],'worldBorder':c['worldBorder'],'blockCount':len(xyz),'alphaSpawns':alpha,'bravoSpawns':bravo,'zones':zones,'shots':c['shots'],'spawnProvenance':'Authored staging on largest 2-block-clear connected voxel component; not decoded Destiny spawn markers.','zoneProvenance':'Source control/capturable_object zone_a/b/c, snapped onto Minecraft floors; snap distances in art provenance.'}
    write_json(out/'javelin4.json',manifest)
    # Authored lighting preserves collision: replace existing ceiling/floor cubes only.
    index={tuple(map(int,p)):i for i,p in enumerate(xyz)};light_indices=set()
    for x,y,z in sorted(major):
        if x%8 or z%8:continue
        ceiling=next(((x,yy,z)for yy in range(y+3,min(y+13,int(hi[1]))) if (x,yy,z)in index),None)
        light_indices.add(index[ceiling if ceiling is not None else (x,y-1,z)])
    for view in manifest['shots']:
        first=first_solid([view['camera'][k]for k in ('x','y','z')],[view['target'][k]for k in ('x','y','z')],index)
        if first is not None:raise ValueError(f"Blocked cinematic {view['key']}: {first}")
    light_id=len(pal);pal.append({'block':'minecraft:sea_lantern','rgb':[172,199,190]})
    for i in light_indices:block[i]=light_id;rgb[i]=np.array([172,199,190])/255
    write_json(out/'lighting-audit.json',{'authored':True,'replacementCells':len(light_indices),'method':'8-block grid on combat walk network; nearest ceiling within 12 blocks, otherwise floor inset; replace occupied full cubes only','sourceEquivalent':False})
    # Sparse voxel payload is sorted by chunk and uses bounded palette IDs.
    order=np.lexsort((xyz[:,2],xyz[:,0],xyz[:,1],xyz[:,2]>>4,xyz[:,0]>>4));packed=np.empty(len(xyz),dtype=[('x','>i4'),('y','>i4'),('z','>i4'),('p','>u2')]);packed['x']=xyz[order,0];packed['y']=xyz[order,1];packed['z']=xyz[order,2];packed['p']=block[order]
    with (out/'javelin4.vox.gz').open('wb') as f,gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0)as z:
        z.write(b'DGCRU001');z.write(struct.pack('>I',len(pal)))
        for v in pal:s=v['block'].encode();z.write(struct.pack('>H',len(s)));z.write(s)
        z.write(struct.pack('>I',len(xyz)));z.write(packed.tobytes())
    audit={'walkableCells':len(walk),'largestComponentCells':len(major),'componentSizes':[len(x)for x in components[:15]],'threeByThreePads':len(pads),'connectedPoints':True,'floorCheck':'floor(x), floor(y)-1, floor(z) occupied full block; feet and two cells above air; 3x3 flat patch; component allows <=1 block jump steps','zones':evidence,'alphaSpawns':alpha,'bravoSpawns':bravo}
    write_json(out/'navigation-audit.json',audit)
    np.savez_compressed(out/'navigation.npz',walk=np.array(sorted(major)))
    render_preview(out,xyz,block,pal,rgb,manifest,major)
    return manifest,audit

def interior_image(xyz,block,pal,eye,target,width=440,height=240):
    """Software voxel DDA from verified eye positions; neutral preview lighting."""
    lo=xyz.min(0)-1;hi=xyz.max(0)+1;grid=np.full(hi-lo+1,-1,np.int16);grid[tuple((xyz-lo).T)]=block
    eye=np.array(eye,float);forward=np.array(target,float)-eye;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    u,v=np.meshgrid((np.arange(width)+.5)/width*2-1,1-(np.arange(height)+.5)/height*2);direction=forward+right*u[...,None]*(width/height)*.58+up*v[...,None]*.58;direction=direction.reshape(-1,3);direction/=np.linalg.norm(direction,axis=1,keepdims=True)
    n=len(direction);pos=np.tile(np.floor(eye).astype(int),(n,1));step=np.where(direction>=0,1,-1);delta=1/np.maximum(np.abs(direction),1e-12);boundary=pos+(step>0);tmax=np.abs((boundary-eye)/np.where(np.abs(direction)>1e-12,direction,1e-12));active=np.ones(n,bool);face=np.ones(n,int);color=np.tile([41.,51.,65.],(n,1));palette=np.array([x['rgb']for x in pal])
    for iteration in range(650):
        ids=np.flatnonzero(active)
        if not len(ids):break
        q=pos[ids]-lo;inside=np.all((q>=0)&(q<np.array(grid.shape)),axis=1);active[ids[~inside]]=False;ids=ids[inside];q=q[inside];hit=grid[tuple(q.T)]>=0
        if hit.any():
            ii=ids[hit];pi=grid[tuple(q[hit].T)];distance=np.linalg.norm(pos[ii]-eye,axis=1);shade=np.array([.82,1.,.69])[face[ii]];shade*=.7+.3*np.exp(-distance/100);color[ii]=palette[pi]*shade[:,None];active[ii]=False
        ids=ids[~hit]
        if not len(ids):continue
        axis=np.argmin(tmax[ids],axis=1);pos[ids,axis]+=step[ids,axis];tmax[ids,axis]+=delta[ids,axis];face[ids]=axis
    return Image.fromarray(np.uint8(np.clip(color,0,255)).reshape(height,width,3))

def render_preview(out,xyz,block,pal,rgb,manifest,major):
    # Orthographic overview/cutaway are actual baked surface cells, not concept art.
    canvas=Image.new('RGB',(1400,1330),(18,23,30));draw=ImageDraw.Draw(canvas);draw.text((24,15),'JAVELIN-4 | source material bake -> vanilla blocks | W260',fill='white')
    colors=np.array([v['rgb'] for v in pal],np.uint8)
    for panel,(limit,label)in enumerate(((160,'Source facility roof / exterior retained; see provenance review'),(96,'Combat cutaway (Y <= 96), A/B/C source markers'))):
        size=(660,560);im=Image.new('RGB',size,(29,35,42));dr=ImageDraw.Draw(im)
        subset=np.flatnonzero(xyz[:,1]<=limit);order=subset[np.argsort(xyz[subset,1],kind='stable')]
        for i in order:
            x,y,z=xyz[i];px=int((x+150)*2.1+15);py=int((z+110)*2.1+18);col=colors[block[i]].astype(float)*(0.65+0.35*np.clip((y-65)/60,0,1));dr.rectangle((px,py,px+2,py+2),fill=tuple(col.astype(int)))
        if panel:
            for zone in manifest['zones']:
                p=zone['center'];x=int((p['x']+150)*2.1+15);z=int((p['z']+110)*2.1+18);dr.ellipse((x-9,z-9,x+9,z+9),outline='yellow',width=3);dr.text((x+10,z),zone['key'],fill='yellow')
            for name,ps,col in [('ALPHA',manifest['alphaSpawns'],'cyan'),('BRAVO',manifest['bravoSpawns'],'orange')]:
                p=ps[0];x=int((p['x']+150)*2.1+15);z=int((p['z']+110)*2.1+18);dr.rectangle((x-5,z-5,x+5,z+5),fill=col);dr.text((x+8,z+8),name,fill=col)
        canvas.paste(im,(20+panel*700,65));draw.text((24+panel*700,42),label,fill='white')
    sheet=Image.open(out/'material-swatches.png');sheet.thumbnail((690,390));canvas.paste(sheet,(25,640));draw.text((25,620),'HLSL basecolor swatches (static snapshots)',fill='white')
    # Palette distribution from output; evidence of actual retained source colors.
    draw.text((740,620),'Minecraft palette / output cell distribution',fill='white')
    for j,(idx,n)in enumerate(collections.Counter(map(int,block)).most_common(16)):
        y=645+j*23;draw.rectangle((740,y,762,y+17),fill=tuple(colors[idx]));draw.text((774,y),f'{pal[idx]["block"]}: {n:,}',fill='white')
    views=[('Central shaft / open sky',{'x':.5,'y':89.,'z':.5},[.5,110,8.5]),('Southern open exterior',{'x':2.5,'y':89.,'z':102.5},[2.5,87,87.5]),('B / clear camera',manifest['shots'][1]['camera'],[manifest['shots'][1]['target'][k]for k in ('x','y','z')])]
    for i,(label,p,target)in enumerate(views):
        eye=[p['x'],p['y'],p['z']];im=interior_image(xyz,block,pal,eye,target);canvas.paste(im,(20+i*460,1080));draw.text((20+i*460,1058),label+' (software voxel preview)',fill='white')
    canvas.save(out/'javelin4-preview.png')

def finish(c,out):
    xyz,block,pal,rgb=bake(c,out);m,nav=navigation(c,out,xyz,block,pal,rgb);geo=json.loads((out/'geometry-audit.json').read_text());mat=json.loads((out/'material-audit.json').read_text());report={'schema':1,'key':c['key'],'sourceGeometry':geo,'roofReview':c.get('roofReview'),'spawnReview':c.get('spawnReview'),'bake':mat,'navigation':nav,'authoredLighting':json.loads((out/'lighting-audit.json').read_text()),'resources':{'voxelBytes':(out/'javelin4.vox.gz').stat().st_size,'voxelSHA256':sha(out/'javelin4.vox.gz'),'blockCount':len(xyz),'packedRuntimeIntBytes':len(xyz)*4,'paletteSize':len(pal)},'limitations':['Source control markers verified, team spawns/cinematic shots authored.','Not original game collision or navigation, 1-block steps may require jumping.','No Minecraft/Vision/server QA by worker; master must check circulation, roofs, combat boundaries and lighting.','Geometry crop removes distant source scenery; not all 32 maps manually recreated.'],'sceneEvidence':'Direct glTF accessor/node-transform/triangle computation; preview is baked voxel surface, not live Minecraft.'};write_json(out/'map-provenance.json',report);print(json.dumps({'key':m['key'],'resources':report['resources']},ensure_ascii=False,indent=2),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--geometry-only',action='store_true');p.add_argument('--finish-only',action='store_true');p.add_argument('--preview-only',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);c=json.loads(a.config.read_text())
    if a.preview_only:
        with gzip.open(a.out/'javelin4.vox.gz','rb')as f:
            if f.read(8)!=b'DGCRU001':raise ValueError('voxel magic')
            palette=[]
            for _ in range(struct.unpack('>I',f.read(4))[0]):palette.append(f.read(struct.unpack('>H',f.read(2))[0]).decode())
            count=struct.unpack('>I',f.read(4))[0];data=np.frombuffer(f.read(),dtype=[('x','>i4'),('y','>i4'),('z','>i4'),('p','>u2')]);xyz=np.stack([data[n]for n in ('x','y','z')],axis=1);block=data['p'];known={v['block']:v for v in json.loads((ROOT/c['palette']).read_text())};known['minecraft:sea_lantern']={'block':'minecraft:sea_lantern','rgb':[172,199,190]};pal=[known[x]for x in palette]
        render_preview(a.out,xyz,block,pal,None,json.loads((a.out/'javelin4.json').read_text()),None);return
    if not a.finish_only: geometry(c,a.out)
    if not a.geometry_only: finish(c,a.out)
if __name__=='__main__':main()
