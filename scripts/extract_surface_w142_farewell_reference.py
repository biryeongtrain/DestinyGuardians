"""Run in a separate --background --disable-autoexec Blender, not the user's session.

Reads mesh datablocks, never imports or executes source scripts. Emits inert JSON
for offline art reference only; no ripped geometry is used by the authored model.
"""
import hashlib
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/tmp/destiny-weapons-w30/raw/farewell/extracted/Farewell.blend')
OUTPUT = ROOT / 'art/weapons/w123/farewell/source-reference.json'
meta = json.loads((ROOT/'art/blockbench/weapons/w30/farewell.bbmodel').read_bytes())['destiny_w30']
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == meta['source_files']['Farewell.blend']
with bpy.data.libraries.load(str(SOURCE), link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n in meta['source_objects']]
meshes = []
for obj in dst.objects:
    assert obj and obj.type == 'MESH'
    mesh = obj.data
    mesh.calc_loop_triangles()
    uv = mesh.uv_layers.active
    mats = []
    for material in mesh.materials:
        images = [] if not material or not material.node_tree else [n.image.name for n in material.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
        mats.append(dict(name=material.name if material else '', images=images))
    meshes.append(dict(name=obj.name,
        vertices=[list(obj.matrix_world @ v.co) for v in mesh.vertices],
        faces=[list(t.vertices) for t in mesh.loop_triangles],
        uv=[[list(uv.data[k].uv) for k in t.loops] for t in mesh.loop_triangles],
        materialIndices=[t.material_index for t in mesh.loop_triangles], materials=mats))
assert sum(len(m['faces']) for m in meshes) == meta['source_triangles']
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(dict(sourceSha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    source=str(SOURCE), extraction='Blender library mesh data only; autoexec disabled; no source geometry exported into product', meshes=meshes), separators=(',', ':'))+'\n')
print('W142 inert mesh reference exported', len(meshes), 'objects', meta['source_triangles'], 'triangles')
