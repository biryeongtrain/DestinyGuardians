"""Blender CPU review of actual baked albedo from independently placed cameras.

Run Blender --background --python this_file -- --output /absolute/directory.
Geometry crops are view-local, never height projections. Original map files are
read-only. --view selects one camera for iterative interior inspection.
"""
import argparse, importlib.util, json, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/maps'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baked_source
import section_nbt
import vanilla_review
spec=importlib.util.spec_from_file_location('source_sampler', ROOT/'scripts/campaign/rising_maps.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from exodus_palette import EXTRA_PALETTE
m.PALETTE_DEF.extend(EXTRA_PALETTE)
m.CACHE_DIR=Path('/tmp/exodus-review/material-cache')
SRC=Path('/Users/qf/Downloads/Exodus-Crash-Strike-KO-2026-11-08/Exodus-Crash-Strike-KO-2026-11-08')
VIEWS=[
 ('arrival_forward',(1474,491,-52.8),(1435,435,-62),125),
 ('trench_descent',(1447,440,-61),(1399,413,-59),140),
 ('trench_floor',(1378,365,-71),(1340,270,-74),130),
 ('trench_outer',(1244,63,-54),(1262,12,-45),115),
 ('trench_interior',(1260,-38,-32.38),(1257,-92,-32.38),100),
 ('trench_interior_reverse',(1260,-38,-32.38),(1252,27,-48),100),
 ('colony',(1198,-195,-42),(1194,-246,-39),140),
 ('plateau',(1040,-655,-42),(973,-689,-28),150),
 ('command_entry',(858,-790,-69),(828,-812,-73),100),
 ('command_inside',(828,-812,-73.38),(805,-826,-73.38),90),
 ('darkroom',(822,-836,-89.38),(802,-832,-84.38),90),
 ('darkroom_reverse',(802,-832,-84.38),(830,-809,-73.38),90),
]

def material(g, index):
    md=g.j['materials'][index];mat=bpy.data.materials.new(md['name']);mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
    out=nodes.new('ShaderNodeOutputMaterial');emit=nodes.new('ShaderNodeEmission')
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str((g.path.parent/g.material_texture(index)).resolve()),check_existing=True)
    tex.extension='EXTEND';links.new(tex.outputs['Color'],emit.inputs['Color'])
    trans=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');cut=nodes.new('ShaderNodeMath');cut.operation='GREATER_THAN';cut.inputs[1].default_value=.5
    links.new(tex.outputs['Alpha'],cut.inputs[0]);links.new(cut.outputs[0],mix.inputs[0]);links.new(trans.outputs[0],mix.inputs[1]);links.new(emit.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
    return mat

def build_source(g, eye, target, radius):
    lo=np.minimum(eye,target)-radius;hi=np.maximum(eye,target)+radius
    materials={};count=0
    for i in g.instances_in(lo,hi):
        n=g.nodes[i];matrix=g.inst_mat[i];ext=g.inst_max[i]-g.inst_min[i]
        if ext.max()>3000:continue
        for pos,uv,idx,mi in g.primitives(n['mesh']):
            w=pos@matrix[:3,:3].T+matrix[:3,3];tri=w[idx]
            keep=np.all(tri.max(1)>=lo,1)&np.all(tri.min(1)<=hi,1)
            if not keep.any():continue
            # Keep all triangles crossing the 3D crop, including ceiling and
            # lower-floor surfaces behind the eye. No topmost-column selection.
            ids=idx[keep].ravel();v=w[ids];u=uv[ids].copy();u[:,1]=1-u[:,1]
            mesh=bpy.data.meshes.new(n['name']);mesh.from_pydata(v.tolist(),[],np.arange(len(v)).reshape(-1,3).tolist())
            layer=mesh.uv_layers.new(name='BakedColorUV');layer.data.foreach_set('uv',u.reshape(-1))
            if mi not in materials:materials[mi]=material(g,mi)
            mesh.materials.append(materials[mi]);obj=bpy.data.objects.new(n['name'],mesh);bpy.context.scene.collection.objects.link(obj);count+=len(v)//3
    return count

def build_voxels(root, eye, target, radius):
    """Display the actual NBT with installed vanilla textures and block lighting.

    Slab top/bottom heights are retained; rods/walls/stairs are conservative
    cube proxies here. Minecraft remains authoritative for their exact shapes.
    """
    lo=np.floor(np.minimum(eye,target)-radius).astype(int);hi=np.ceil(np.maximum(eye,target)+radius).astype(int)
    origin=np.array([256,32,256]);size=np.array(root['bounds']['max'])-origin+1
    a=np.maximum([lo[0]-505,lo[2]+133,680-hi[1]],0);b=np.minimum([hi[0]-505,hi[2]+133,680-lo[1]],size)
    states=['minecraft:air'];lookup={states[0]:0}
    grid=np.zeros((b[1]-a[1],b[2]-a[2],b[0]-a[0]),np.uint16)
    for (cx,cy,cz),palette,index in section_nbt.sections(root):
        p=np.array([cx*16,cy*16,cz*16])-origin;q=p+16
        l=np.maximum(p,a);h=np.minimum(q,b)
        if np.any(l>=h):continue
        ids=[]
        for state in palette:
            if state not in lookup:lookup[state]=len(states);states.append(state)
            ids.append(lookup[state])
        cells=np.array(ids,np.uint16)[index]
        grid[l[1]-a[1]:h[1]-a[1],l[2]-a[2]:h[2]-a[2],l[0]-a[0]:h[0]-a[0]]=cells[l[1]-p[1]:h[1]-p[1],l[2]-p[2]:h[2]-p[2],l[0]-p[0]:h[0]-p[0]]
    invisible=[i for i,s in enumerate(states)if s.startswith('minecraft:light[')]
    crosses=[i for i,s in enumerate(states)if any(n in s for n in ('crimson_roots','dead_bush','short_grass'))]
    visible=~np.isin(grid,[0]+invisible+crosses);opaque=visible&~np.isin(grid,[i for i,s in enumerate(states)if 'leaves' in s or 'bars' in s or 'chain' in s])
    light=vanilla_review.light_levels(grid,states,opaque)
    solid=visible;verts=[];faces=[];mids=[];lighting=[]
    matkeys=[];matlookup={}
    def mid(pid,face):
        key=(int(pid),face)
        if key not in matlookup:matlookup[key]=len(matkeys);matkeys.append(key)
        return matlookup[key]
    # (array y,z,x offset, quad source xyz offsets)
    defs=[((0,0,1),[(1,0,0),(1,1,0),(1,1,1),(1,0,1)]),((0,0,-1),[(0,1,0),(0,0,0),(0,0,1),(0,1,1)]),
          ((0,-1,0),[(0,1,0),(1,1,0),(1,1,1),(0,1,1)]),((0,1,0),[(1,0,0),(0,0,0),(0,0,1),(1,0,1)]),
          ((1,0,0),[(0,0,1),(1,0,1),(1,1,1),(0,1,1)]),((-1,0,0),[(0,1,0),(1,1,0),(1,0,0),(0,0,0)])]
    bottom=np.array(['_slab['in s and 'type=bottom'in s for s in states]);top=np.array(['_slab['in s and 'type=top'in s for s in states])
    for (delta,quad),face,shade in zip(defs,['east','west','north','south','up','down'],[.65,.65,.8,.8,1,.5]):
        neighbour=np.roll(solid,tuple(-v for v in delta),(0,1,2));mask=solid&~neighbour
        yy,zz,xx=np.nonzero(mask);pid=grid[yy,zz,xx]
        points=np.stack([xx+a[0]+505,679-(zz+a[2]),yy+a[1]-133],1).astype(float)
        v=points[:,None,:]+np.array(quad)[None,:,:]
        for j,offset in enumerate(quad):
            if offset[2]:v[bottom[pid],j,2]-=.5
            else:v[top[pid],j,2]+=.5
        nl=light[np.clip(yy+delta[0],0,grid.shape[0]-1),np.clip(zz+delta[1],0,grid.shape[1]-1),np.clip(xx+delta[2],0,grid.shape[2]-1)]
        value=(.055+.945*(nl.astype(float)/15)**1.35)*shade
        emission=np.array([any(t in s for t in ('sea_lantern','froglight'))for s in states])
        value[emission[pid]]=1
        start=len(verts);verts.extend(v.reshape(-1,3).tolist());faces.extend((np.arange(len(v)*4).reshape(-1,4)+start).tolist())
        mids.extend([mid(i,face)for i in pid]);lighting.extend(value.tolist())
    yy,zz,xx=np.nonzero(np.isin(grid,crosses))
    for y,z,x in zip(yy,zz,xx):
        point=np.array([x+a[0]+505,679-(z+a[2]),y+a[1]-133],float)
        for quad in [[(0,0,0),(1,1,0),(1,1,1),(0,0,1)],[(0,1,0),(1,0,0),(1,0,1),(0,1,1)]]:
            start=len(verts);verts.extend((point+np.array(quad)).tolist());faces.append(list(range(start,start+4)))
            mids.append(mid(grid[y,z,x],'up'));lighting.append(.055+.945*(float(light[y,z,x])/15)**1.35)
    mesh=bpy.data.meshes.new('NBT exposed block faces');mesh.from_pydata(verts,[],faces)
    layer=mesh.uv_layers.new(name='Vanilla block UV')
    layer.data.foreach_set('uv',np.tile([[0,0],[1,0],[1,1],[0,1]],(len(faces),1)).reshape(-1))
    color=mesh.color_attributes.new(name='BlockLight',type='FLOAT_COLOR',domain='CORNER')
    brightness=np.repeat(np.array(lighting,dtype=np.float32),4)
    colors=np.ones((len(brightness),4),np.float32);colors[:,:3]=brightness[:,None]
    color.data.foreach_set('color',colors.reshape(-1))
    for pid,face in matkeys:
        state=states[pid]
        mesh.materials.append(vanilla_review.blender_material(state,face,m.state_rgb(state)))
    mesh.polygons.foreach_set('material_index',mids);obj=bpy.data.objects.new('Actual exported NBT',mesh);bpy.context.scene.collection.objects.link(obj)
    return len(faces)*2

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--view',nargs='*');p.add_argument('--save',action='store_true');p.add_argument('--inspect-only',action='store_true');p.add_argument('--route',type=Path);p.add_argument('--route-indices',type=int,nargs='*');p.add_argument('--nbt',type=Path);p.add_argument('--cameras',type=Path)
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);args.output.mkdir(parents=True,exist_ok=True)
    g=None if args.nbt else baked_source.load(SRC/'maps_baked/Exodus_Crash_Continuous.baked.glb',m)
    nbt=section_nbt.load(args.nbt)if args.nbt else None
    views=VIEWS
    if args.cameras:
        views=[(v['name'],v['eye'],v['target'],v.get('radius',100))for v in json.loads(args.cameras.read_text())]
    if args.route:
        route=np.load(args.route)
        def source(c):return (float(c[0]+505.5),float(679-c[2]+.5),float(c[1]-133+1.62))
        views=[(f'route_{i}',source(route[i]),source(route[min(i+10,len(route)-1)]),100)for i in args.route_indices]
    for name,eye,target,radius in views:
        if args.view and name not in args.view:continue
        bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
        count=build_voxels(nbt,np.array(eye),np.array(target),radius)if args.nbt else build_source(g,np.array(eye),np.array(target),radius)
        scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4
        scene.render.resolution_x=1100;scene.render.resolution_y=720;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard'
        scene.world=bpy.data.worlds.new('Review background');scene.world.use_nodes=True
        sky=[111,174,170] if nbt and nbt.get('biome')=='destiny:nessus' else [123,164,255]
        bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(*baked_source.srgb_to_linear(np.array(sky)/255),1);bg.inputs['Strength'].default_value=1 if args.nbt else .3
        cam=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'));scene.collection.objects.link(cam);scene.camera=cam
        cam.location=eye;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=22;cam.data.clip_start=.05;cam.data.clip_end=2000
        probes=[];dg=bpy.context.evaluated_depsgraph_get()
        for direction in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
            hit,loc,normal,face,obj,matrix=scene.ray_cast(dg,Vector(eye),Vector(direction),distance=200)
            material_index=obj.data.polygons[face].material_index if hit and 0<=face<len(obj.data.polygons) else 0
            probes.append(dict(direction=direction,distance=round((loc-Vector(eye)).length,3)if hit else None,object=obj.name if hit else None,material=obj.data.materials[material_index].name if hit and obj.data.materials else None))
        print('PROBES',name,json.dumps(probes),flush=True)
        scene.render.filepath=str(args.output/(name+'.png'))
        print('BAKED_VIEW',name,'triangles',count,flush=True)
        if not args.inspect_only:bpy.ops.render.render(write_still=True)
        if args.save:
            bpy.ops.file.pack_all()
            for screen in bpy.data.screens:
                for area in screen.areas:
                    if area.type=='VIEW_3D':
                        area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
            bpy.ops.wm.save_as_mainfile(filepath=str(args.output/(name+'.blend')))
        (args.output/(name+'.json')).write_text(json.dumps(dict(eye=eye,target=target,triangles=count,probes=probes,source=str(args.nbt if args.nbt else g.path),review='Blender Cycles CPU; installed vanilla textures, Nessus foliage tint, approximate vanilla block light; rods/walls/stairs proxies; not native client'if args.nbt else 'Blender Cycles CPU, actual unlit baked PNG + UV; not in-game'),indent=1))

if __name__=='__main__':main()
