"""Vanilla block textures and approximate shaderless light for offline NBT review.

No downloaded/reference art is used as a game texture. Assets come from the
installed Minecraft client. Exact stair/wall meshes and client AO remain native QA.
"""
import json
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile
import numpy as np

CLIENT = Path.home()/'.gradle/caches/fabric-loom/26.3/minecraft-client.jar'
CACHE = Path('/tmp/exodus-nessus-art/vanilla-textures')


@lru_cache(None)
def asset(path):
    with ZipFile(CLIENT) as jar:
        return json.loads(jar.read('assets/minecraft/'+path))


@lru_cache(None)
def model(name):
    name=name.removeprefix('minecraft:')
    data=asset('models/'+name+'.json')
    inherited=model(data['parent']) if data.get('parent','').startswith(('minecraft:block/','block/')) else {}
    return {**inherited,**data,'textures':{**inherited.get('textures',{}),**data.get('textures',{})}}


@lru_cache(None)
def face_texture(state, face):
    name=state.split(':')[1].split('[')[0];props={}
    if '[' in state:
        props=dict(p.split('=')for p in state.split('[')[1].rstrip(']').split(','))
    try:
        variants=asset('blockstates/'+name+'.json').get('variants',{})
        chosen=next((v for key,v in variants.items() if all(props.get(k)==v for k,v in
                    (p.split('=')for p in key.split(',')if p))),None)
        if chosen is None:chosen=next(iter(variants.values()),{'model':'minecraft:block/'+name})
        if isinstance(chosen,list):chosen=chosen[0]
        data=model(chosen['model']);textures=data.get('textures',{})
        value=None
        for element in data.get('elements',[]):
            if face in element.get('faces',{}):value=element['faces'][face]['texture'];break
        if value is None:value=next((textures[k]for k in ('all',face,'side','cross','texture','particle')if k in textures),None)
        for _ in range(12):
            if isinstance(value,dict):value=value.get('sprite')
            if not value or not value.startswith('#'):break
            value=textures.get(value[1:])
        if not value:return None
        path='assets/minecraft/textures/'+value.removeprefix('minecraft:')+'.png'
        target=CACHE/Path(path).name
        if not target.exists():
            CACHE.mkdir(parents=True,exist_ok=True)
            with ZipFile(CLIENT)as jar:target.write_bytes(jar.read(path))
        return target
    except (KeyError,FileNotFoundError,StopIteration):
        return None


def light_levels(grid, states, opaque):
    """Open-sky level 15 plus emissive blocks, with Manhattan light attenuation."""
    sky=np.maximum.accumulate(opaque[::-1],axis=0)[::-1]
    light=np.where(sky,0,15).astype(np.uint8)
    seeds=[]
    for i,s in enumerate(states):
        level=0
        if s.startswith('minecraft:light['):level=int(s.split('level=')[1].split(',')[0].rstrip(']'))
        elif any(n in s for n in ('sea_lantern','froglight','glowstone')):level=15
        if level:
            mask=grid==i;light[mask]=level;seeds.append((mask,level))
    for _ in range(14):
        old=light.copy()
        for axis in range(3):
            a=[slice(None)]*3;b=list(a);a[axis]=slice(1,None);b[axis]=slice(None,-1)
            np.maximum(light[tuple(a)],np.maximum(old[tuple(b)],1)-1,out=light[tuple(a)])
            np.maximum(light[tuple(b)],np.maximum(old[tuple(a)],1)-1,out=light[tuple(b)])
        light[opaque]=0
        for mask,level in seeds:light[mask]=level
    return light


def blender_material(state, face, fallback_rgb):
    import bpy
    import baked_source
    mat=bpy.data.materials.new(state+' '+face);mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
    out=nodes.new('ShaderNodeOutputMaterial');emit=nodes.new('ShaderNodeEmission')
    texpath=face_texture(state,face)
    tint=np.ones(3)
    if 'oak_leaves' in state:tint=np.array([189,62,43])/255
    if texpath:
        tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(texpath),check_existing=True);tex.interpolation='Closest'
        mult=nodes.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1
        mult.inputs[2].default_value=(*baked_source.srgb_to_linear(tint),1)
        links.new(tex.outputs['Color'],mult.inputs[1]);links.new(mult.outputs[0],emit.inputs['Color'])
    else:
        emit.inputs['Color'].default_value=(*baked_source.srgb_to_linear(np.clip(fallback_rgb,0,1)),1)
    attr=nodes.new('ShaderNodeVertexColor');attr.layer_name='BlockLight'
    links.new(attr.outputs['Color'],emit.inputs['Strength'])
    if texpath and any(n in state for n in ('leaves','roots','dead_bush','bars','chain')):
        trans=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
        cut=nodes.new('ShaderNodeMath');cut.operation='GREATER_THAN';cut.inputs[1].default_value=.5
        links.new(tex.outputs['Alpha'],cut.inputs[0]);links.new(cut.outputs[0],mix.inputs[0])
        links.new(trans.outputs[0],mix.inputs[1]);links.new(emit.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs[0])
    else:links.new(emit.outputs[0],out.inputs[0])
    return mat
