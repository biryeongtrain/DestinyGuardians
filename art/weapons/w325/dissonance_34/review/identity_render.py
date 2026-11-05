"""Owned W325-7 review framing; delegates materials/mesh creation to unchanged shared renderer."""
import sys,runpy,mathutils
from pathlib import Path
root=Path(__file__).resolve().parents[5]
a=sys.argv[sys.argv.index('--')+1:]; wid=a[0]
out=root/'art/weapons/w325'/wid/'review'/wid
skin=root/'src/main/resources/destiny/weapon_skins'/f'{wid}.json'
tex=root/'src/main/resources/assets/destiny/textures/item/weapon/w325'/f'{wid}.png'
sys.argv=['identity_render.py','--',str(out),str(skin),str(tex),'west']
g=runpy.run_path(str(root/'scripts/art/w325/render_model.py'))
sc,co,cam=g['sc'],g['co'],g['cam']; c=g['c']
for view in ('west','east','top','q','front'):
    direction=mathutils.Vector(g['dirs'][view]).normalized()
    co.location=c-direction*3
    co.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    sc.view_layers[0].update()
    transform=co.matrix_world.inverted()
    points=[transform@mathutils.Vector(p) for p in g['verts']]
    width=max(p.x for p in points)-min(p.x for p in points)
    height=max(p.y for p in points)-min(p.y for p in points)
    centre_x=(max(p.x for p in points)+min(p.x for p in points))/2
    centre_y=(max(p.y for p in points)+min(p.y for p in points))/2
    co.location += co.rotation_euler.to_quaternion() @ mathutils.Vector((centre_x,centre_y,0))
    cam.ortho_scale=max(width,height*sc.render.resolution_x/sc.render.resolution_y)*1.14
    sc.render.filepath=f'{out}_{view}.png'
    g['bpy'].ops.render.render(write_still=True)
