"""Blender-only, source-referenced cuboid reconstruction. Never saves source scenes.

Run in a separate Blender --background --disable-autoexec process, NOT the user's
MCP scene. --cache contains selection.json and raw/<id>/extracted. Imported
materials are read as data; scripts/drivers are never enabled. No mesh is shipped.
The checked-in bbmodels are the editable reconstruction source for normal builds.
"""
import argparse, base64, hashlib, json, math, os, pathlib, re, struct, sys, uuid, zlib
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

REPO = pathlib.Path(__file__).resolve().parents[2]
OUT = REPO / 'art/blockbench/weapons/w30'
MAX_CUBES = 128
ATLAS_SIZE = 512
NS = uuid.UUID('ba810f7c-0f72-473a-b9f6-1b55778fb030')

def uid(name): return str(uuid.uuid5(NS, name))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def png(array):
    h,w,_ = array.shape
    def chunk(t,b): return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
    raw=b''.join(b'\0'+row.tobytes() for row in array)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')

def material_image(mat, files, cache):
    if mat is None: return None
    if mat.name in cache:return cache[mat.name]
    nodes=list(mat.node_tree.nodes) if mat.node_tree else []
    candidates=[]
    for n in nodes:
        if n.type!='TEX_IMAGE' or not n.image:continue
        label=(n.name+' '+n.label+' '+n.image.name).lower()
        if any(s in label for s in ('normal','gstack','g_stack','dyemap','flowmap','height')):continue
        score=10*('diffuse' in label)+5*('base color' in label)+('color' in label)
        if score:candidates.append((score,n.image))
    image=max(candidates,key=lambda v:v[0])[1] if candidates else None
    if image:
        key=re.sub(r'\.\d{3}$','',image.name).lower()
        path=files.get(key)
        if not image.packed_file and path:
            image.filepath=str(path);image.reload()
        if image.size[0] and image.size[1]:
            pixels=np.empty(image.size[0]*image.size[1]*4,dtype=np.float32)
            image.pixels.foreach_get(pixels)
            result=pixels.reshape(image.size[1],image.size[0],4)
            cache[mat.name]=result
            return result
    # Old FBX-only files sometimes retain no image nodes; deterministic filename
    # matching is allowed, but an arbitrary normal/GStack image is never color.
    key=re.sub('[^a-z0-9]','',mat.name.lower())
    candidates=[p for n,p in files.items() if 'diffuse' in n and (key in re.sub('[^a-z0-9]','',n) or re.sub('[^a-z0-9]','',n.split('_diffuse')[0]) in key)]
    if candidates:
        image=bpy.data.images.load(str(sorted(candidates)[0]),check_existing=True)
        pixels=np.array(image.pixels[:],dtype=np.float32).reshape(image.size[1],image.size[0],4)
        cache[mat.name]=pixels;return pixels
    cache[mat.name]=None;return None

def read_source(row, folder):
    blends=sorted(folder.rglob('*.blend'))
    if blends:bpy.ops.wm.open_mainfile(filepath=str(blends[0]),load_ui=False,use_scripts=False)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        fbx=sorted(p for p in folder.rglob('*') if p.suffix.lower()=='.fbx')
        bpy.ops.import_scene.fbx(filepath=str(fbx[0]),use_anim=False)
    # For the posed glaive use FBX bind-space, not the artist's display scene.
    # Keep that scene's per-part material assignments as data (not shader code).
    fbx=sorted(p for p in folder.rglob('*') if p.suffix.lower()=='.fbx')
    if blends and fbx and row['family']=='glaive':
        part_materials={o.name:(len(o.data.vertices),list(o.data.materials)) for o in bpy.context.scene.objects if o.type=='MESH'}
        shader_materials={m.name:m for m in bpy.data.materials}
        scene=bpy.data.scenes.new('W30 isolated geometry')
        bpy.context.window.scene=scene
        bpy.ops.import_scene.fbx(filepath=str(fbx[0]),use_anim=False)
        for o in scene.objects:
            if o.type!='MESH':continue
            matches=[k for k,(count,mats) in part_materials.items() if count==len(o.data.vertices)]
            key=max(matches,key=lambda k:len(os.path.commonprefix([k,o.name]))) if matches else None
            if key:
                o.data.materials.clear()
                for m in part_materials[key][1]:o.data.materials.append(m)
            else:
                for i,m in enumerate(o.data.materials):
                    base=re.sub(r'\.\d{3}$','',m.name)
                    if base in shader_materials:o.data.materials[i]=shader_materials[base]
    files={p.name.lower():p for p in folder.rglob('*') if p.suffix.lower() in ('.png','.dds','.jpg','.tga')}
    cache={}; objects=[];excluded=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or len(o.data.vertices)<3:continue
        label=(o.name+' '+' '.join(m.name for m in o.data.materials if m)).lower()
        reject=any(w in label for w in ('ghost','simple_element','optical','flare','blf_material','backdrop','reticle','flowmap','_vfx',' vfx','floor','groundplane'))
        if any(m and re.sub(r'\.\d{3}$','',m.name).lower()=='ret' for m in o.data.materials):reject=True
        # Artist preview floor planes are not weapon geometry.
        if o.name.lower() in ('plane','plane.001','circle') and len(o.data.vertices)<=4:reject=True
        if o.name.lower()=='cube' and any(m and 'preset' in m.name.lower() for m in o.data.materials):reject=True
        if row['id']=='frontier_justice' and any(w in o.name for w in ('ATD RAPTOR','LD WATCHDOG','ATA SCOUT','SD THERMAL','SC HOLO','GB IRON')):reject=True
        if reject:excluded.append(o.name);continue
        objects.append(o)
    assert objects, 'No physical weapon geometry'
    # Imported legacy scenes can contain alternate shader meshes/decals; retain
    # physical parts, but never their artist's lighting/display stage.
    vertices=[];triangles=[];uvs=[];textures=[];materials=[]
    # Apostate's artist stage translates every part by (-.532, .800, 0).
    # Restore the common gear/grip coordinate system, not each part's origin.
    # FBX retains that same stage transform, so swapping file formats is no fix.
    source_correction=objects[0].matrix_world.inverted() if row['id']=='apostate' else None
    for o in objects:
        mesh=o.data;mesh.calc_loop_triangles();off=len(vertices)
        matrix=source_correction@o.matrix_world if source_correction is not None else o.matrix_world
        vertices.extend(tuple(matrix@v.co) for v in mesh.vertices)
        layer=mesh.uv_layers.active
        for t in mesh.loop_triangles:
            triangles.append(tuple(off+i for i in t.vertices))
            uvs.append(np.array([layer.data[i].uv[:] for i in t.loops]) if layer else np.zeros((3,2)))
            m=mesh.materials[t.material_index] if t.material_index<len(mesh.materials) else None
            textures.append(material_image(m,files,cache));materials.append(m.name if m else 'untextured')
    v=np.asarray(vertices,dtype=np.float64)
    lo=v.min(axis=0);hi=v.max(axis=0);extent=hi-lo
    family=row['family']
    if family in ('sword','bow'):
        # Z-up source, preserve the upright blade/bow, horizontal projection Y.
        # Goldtusk's thin axis is Y rather than X.
        thin=0 if extent[0]<extent[1] else 1
        long=1-thin;sign=-1 if abs(lo[long])>abs(hi[long]) else 1
    else:
        long=int(np.argmax(extent[:2]));thin=1-long
        sign=-1 if abs(lo[long])>abs(hi[long]) else 1
    # Negative model Z is the muzzle/arrow direction, Y is up.
    canonical=np.column_stack((v[:,thin]*(1 if long==1 else -1),v[:,2],v[:,long]*-sign))
    if family=='glaive':
        canonical=np.column_stack((v[:,0],-v[:,1],v[:,2]))
    size={'hand_cannon':16,'sidearm':15,'submachine_gun':20,'sniper_rifle':29,'rocket_launcher':27,'machine_gun':27,'sword':29,'glaive':29,'bow':26}.get(family,25)
    scale=size/max(np.ptp(canonical,axis=0))
    # Hand grip of D2 gear is close to source (0,0,0). Clamp the visual anchor only
    # when needed to keep vanilla cuboids in [-16,32]; record the exact adjustment.
    shift=np.array([8.,8.,8.]);coords=canonical*scale+shift
    for axis in range(3):
        delta=max(-15.5-coords[:,axis].min(),0)-max(coords[:,axis].max()-31.5,0)
        coords[:,axis]+=delta;shift[axis]+=delta
    bvh=BVHTree.FromPolygons([Vector(p) for p in coords],triangles,all_triangles=True)
    assert bvh
    textured=sum(t is not None for t in textures)
    info=dict(source_objects=[o.name for o in objects],excluded_objects=excluded,source_triangles=len(triangles),textured_triangles=textured,
              source_bounds=[lo.tolist(),hi.tolist()],model_bounds=[coords.min(axis=0).tolist(),coords.max(axis=0).tolist()],
              source_axis=dict(length=long,thin=thin,muzzle_sign=sign),scale=scale,anchor=shift.tolist(),
              source_files={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.suffix.lower() in ('.fbx','.blend')})
    if source_correction is not None:info['source_coordinate_correction']=[list(r) for r in source_correction]
    return coords,np.array(triangles),uvs,textures,bvh,info

def conservative_surface(coords,tris,lo,cell,dims):
    """Clip actual source triangles against YZ cells; never miss a thin limb.

    Center rays can step over an entire bowstring/diagonal limb. Conservative
    clipping keeps every intersected cell, without filling a triangle's whole
    bounding rectangle. X coverage is the clipped triangle's actual thickness.
    """
    volume=np.zeros(tuple(dims),dtype=bool)
    for triangle in coords[tris]:
        lower=np.maximum(0,np.floor((triangle.min(axis=0)-lo)/cell).astype(int))
        upper=np.minimum(dims-1,np.floor((triangle.max(axis=0)-lo)/cell).astype(int))
        for y in range(lower[1],upper[1]+1):
            for z in range(lower[2],upper[2]+1):
                polygon=list(triangle)
                for axis,index in ((1,y),(2,z)):
                    for edge,direction in ((lo[axis]+index*cell[axis],1),(lo[axis]+(index+1)*cell[axis],-1)):
                        clipped=[]
                        for i,p in enumerate(polygon):
                            q=polygon[i-1];a=(p[axis]-edge)*direction;b=(q[axis]-edge)*direction
                            if (a>=0)!=(b>=0):clipped.append(q+(p-q)*b/(b-a))
                            if a>=0:clipped.append(p)
                        polygon=clipped
                        if not polygon:break
                    if not polygon:break
                if not polygon:continue
                x=[p[0] for p in polygon]
                start=max(0,min(int(dims[0])-1,int(math.floor((min(x)-lo[0])/cell[0]))))
                end=max(start+1,min(int(dims[0]),int(math.ceil((max(x)-lo[0])/cell[0]))))
                volume[start:end,y,z]=True
    for y in range(dims[1]):
        for z in range(dims[2]):
            hit=np.flatnonzero(volume[:,y,z])
            if len(hit):volume[hit[0]:hit[-1]+1,y,z]=True
    return volume

def cuboids(coords,bvh,resolution,tris=None):
    lo=coords.min(axis=0);hi=coords.max(axis=0);ext=hi-lo
    # Preserve side silhouette at finer resolution than thickness. Cuboid merging
    # is 3D: this does NOT create a flat gun cutout or just one box per component.
    yz=max(ext[1:]);step=yz/resolution
    thickness_slices=8 if MAX_CUBES==256 else 6
    dims=np.maximum([5,2,2],np.ceil(ext/np.array([ext[0]/thickness_slices,step,step])).astype(int))
    cell=ext/dims;volume=np.zeros(tuple(dims),dtype=bool)
    for y in range(dims[1]) if tris is None else ():
        for z in range(dims[2]):
            origin=Vector((lo[0]-1,lo[1]+(y+.5)*cell[1],lo[2]+(z+.5)*cell[2]))
            a=bvh.ray_cast(origin,Vector((1,0,0)),ext[0]+2)[0]
            if a is None:continue
            origin.x=hi[0]+1
            b=bvh.ray_cast(origin,Vector((-1,0,0)),ext[0]+2)[0]
            if b is None:continue
            start=max(0,min(dims[0]-1,int(math.floor((a.x-lo[0])/cell[0]))))
            end=max(start+1,min(dims[0],int(math.ceil((b.x-lo[0])/cell[0]))))
            volume[start:end,y,z]=True
    if tris is not None:volume=conservative_surface(coords,tris,lo,cell,dims)
    # Greedy maximal rectangular cuboids; try each growth order and retain the
    # smallest representation without deleting silhouette cells.
    best=None
    import itertools
    for order in itertools.permutations((0,1,2)):
        left=volume.copy(); boxes=[]
        for point in np.argwhere(volume):
            p=tuple(point)
            if not left[p]:continue
            end=point+1
            for axis in order:
                while end[axis]<dims[axis]:
                    sl=[slice(int(point[k]),int(end[k])) for k in range(3)]
                    sl[axis]=int(end[axis])
                    if not left[tuple(sl)].all():break
                    end[axis]+=1
            left[tuple(slice(int(point[k]),int(end[k])) for k in range(3))]=False
            boxes.append((lo+point*cell,lo+end*cell))
        if best is None or len(boxes)<len(best):best=boxes
    return best,dict(grid=dims.tolist(),occupied_cells=int(volume.sum()),resolution=resolution)

def face_corners(a,b):
    x,y,z=a;X,Y,Z=b
    # Each array follows Minecraft's native face-UV orientation, top-left first.
    return {'north':[(X,Y,z),(x,Y,z),(x,y,z),(X,y,z)],'south':[(x,Y,Z),(X,Y,Z),(X,y,Z),(x,y,Z)],
            'west':[(x,Y,z),(x,Y,Z),(x,y,Z),(x,y,z)],'east':[(X,Y,Z),(X,Y,z),(X,y,z),(X,y,Z)],
            'up':[(x,Y,z),(X,Y,z),(X,Y,Z),(x,Y,Z)],'down':[(x,y,Z),(X,y,Z),(X,y,z),(x,y,z)]}

def bake(coords,tris,uvs,textures,bvh,boxes):
    faces=[]
    for i,(a,b) in enumerate(boxes):
        for name,corners in face_corners(a,b).items():
            c=np.array(corners);w=max(2,int(math.ceil(np.linalg.norm(c[1]-c[0])*5)));h=max(2,int(math.ceil(np.linalg.norm(c[3]-c[0])*5)))
            faces.append(dict(box=i,name=name,c=c,w=w,h=h))
    # Shelf packing with edge dilation prevents dark seams under mipmaps.
    edge=ATLAS_SIZE;x=y=1;rowh=0
    for f in sorted(faces,key=lambda f:(-f['h'],-f['w'],f['box'],f['name'])):
        if x+f['w']+2>edge:x=1;y+=rowh;rowh=0
        f['pos']=(x,y);x+=f['w']+2;rowh=max(rowh,f['h']+2)
    assert y+rowh<=edge, 'Atlas budget exceeded'
    atlas=np.zeros((edge,edge,4),dtype=np.uint8);mapping={}
    # Precompute barycentric matrices so nearest-surface colors are sampled from
    # their actual source triangle UV, not a global average or generic palette.
    tv=coords[tris];v0=tv[:,1]-tv[:,0];v1=tv[:,2]-tv[:,0]
    d00=(v0*v0).sum(axis=1);d01=(v0*v1).sum(axis=1);d11=(v1*v1).sum(axis=1);den=d00*d11-d01*d01
    for f in faces:
        w,h=f['w'],f['h'];x,y=f['pos'];c=f['c'];tile=np.empty((h,w,4),dtype=np.uint8)
        for j in range(h):
            for k in range(w):
                p=c[0]+(c[1]-c[0])*((k+.5)/w)+(c[3]-c[0])*((j+.5)/h)
                pos,normal,idx,distance=bvh.find_nearest(Vector(p))
                color=np.array([.35,.37,.39,1.])
                if idx is not None and textures[idx] is not None and abs(den[idx])>1e-15:
                    v2=np.array(pos)-tv[idx,0];d20=v2@v0[idx];d21=v2@v1[idx]
                    bv=(d11[idx]*d20-d01[idx]*d21)/den[idx];bw=(d00[idx]*d21-d01[idx]*d20)/den[idx]
                    uv=(1-bv-bw)*uvs[idx][0]+bv*uvs[idx][1]+bw*uvs[idx][2]
                    img=textures[idx];ix=int((uv[0]%1)*img.shape[1])%img.shape[1];iy=int((uv[1]%1)*img.shape[0])%img.shape[0]
                    color=img[iy,ix].copy();color[3]=1 # physical surface; source masks are not transparency
                tile[j,k]=np.clip(color*255,0,255).astype(np.uint8)
        atlas[y:y+h,x:x+w]=tile
        atlas[y-1:y+h+1,x-1:x+w+1]=np.pad(tile,((1,1),(1,1),(0,0)),mode='edge')
        mapping[(f['box'],f['name'])]=[x*16/edge,y*16/edge,(x+w)*16/edge,(y+h)*16/edge]
    return png(atlas),mapping

def build(row,cache):
    coords,tris,uvs,textures,bvh,info=read_source(row,cache/'raw'/row['id']/'extracted')
    chosen=None
    resolutions=(160,128,112,96,80,72,64,56,48,40,34,30,26,22,18,14,10) if row['family'] in ('sword','glaive','bow') else (80,72,64,56,48,40,34,30,26,22,18,14,10)
    if MAX_CUBES==256:resolutions=(320,256,224,192,160,144,128,112,96,80,72,64,56,48,40,34,30,26,22,18,14,10)
    for res in resolutions:
        boxes,grid=cuboids(coords,bvh,res,tris if row['id']=='biting_winds' else None)
        if row['id']=='biting_winds':print('W30 conservative bow',res,len(boxes),flush=True)
        if len(boxes)<=MAX_CUBES:chosen=(boxes,grid);break
    assert chosen, 'Cuboid budget exceeded'
    boxes,grid=chosen
    assert len(boxes)>8,'Degenerate model'
    texture,mapping=bake(coords,tris,uvs,textures,bvh,boxes)
    elements=[]
    for i,(a,b) in enumerate(boxes):
        elements.append(dict(name=f'source_volume_{i:03}',type='cube',uuid=uid(row['id']+str(i)),from_=list(np.round(a,6)),to=list(np.round(b,6)),origin=[8,8,8],box_uv=False,
                             faces={f:dict(uv=mapping[(i,f)],texture=0) for f in face_corners(a,b)}))
        elements[-1]['from']=elements[-1].pop('from_')
    model=dict(meta=dict(format_version='4.10',model_format='java_block',box_uv=False),name=row['name'],model_identifier=row['id'],resolution=dict(width=16,height=16),
               elements=elements,outliner=[e['uuid'] for e in elements],textures=[dict(name=row['id']+'.png',id='0',uuid=uid(row['id']+'texture'),width=ATLAS_SIZE,height=ATLAS_SIZE,uv_width=16,uv_height=16,source='data:image/png;base64,'+base64.b64encode(texture).decode())],
               destiny_w30=dict(info,**grid,method='source_conservative_volume_cuboids_v2' if row['id']=='biting_winds' else 'source_projected_volume_cuboids_v1',cube_count=len(boxes),texture_sha256=hashlib.sha256(texture).hexdigest()))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(row['id']+'.bbmodel')).write_text(json.dumps(model,separators=(',',':'),ensure_ascii=False)+'\n')
    print('W30 BUILT',row['id'],len(boxes),'cubes',info['source_triangles'],'source tris',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--cache',type=pathlib.Path,required=True);parser.add_argument('--only',nargs='*')
    parser.add_argument('--max-cubes',type=int,choices=(128,256),default=128)
    parser.add_argument('--atlas-size',type=int,choices=(512,1024),default=512)
    parser.add_argument('--out',type=pathlib.Path,default=OUT)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    MAX_CUBES=args.max_cubes;ATLAS_SIZE=args.atlas_size;OUT=args.out
    rows=json.loads((args.cache/'selection.json').read_text())
    for row in rows:
        if not args.only or row['id'] in args.only:build(row,args.cache)
