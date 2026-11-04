import bpy,numpy as np,json
from pathlib import Path
out=Path('/tmp/devils-source-alpha');out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath='/tmp/devils-drive-marauder-dual/evaluated-qa.blend')
rows=[]
for im in bpy.data.images:
 if im.name.startswith('source_'):
  pix=np.array(im.pixels[:],dtype=np.float32).reshape(-1,4)
  rows.append(dict(name=im.name,source=im.source,channels=im.channels,size=list(im.size),hasData=im.has_data,alphaMin=float(pix[:,3].min()),alphaMax=float(pix[:,3].max()),alphaBelowHalf=int((pix[:,3]<.5).sum())))
  bpy.context.scene.render.image_settings.file_format='PNG';bpy.context.scene.render.image_settings.color_mode='RGBA'
  im.save_render(str(out/(im.name+'.png')),scene=bpy.context.scene)
(out/'images.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows),flush=True)
