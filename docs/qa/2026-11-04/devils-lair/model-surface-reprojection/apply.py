from pathlib import Path
from PIL import Image
import numpy as np,json,base64,io,shutil,hashlib
P=Path('/tmp/devils-thrall-baseline-20261104');O=Path('/tmp/devils-thrall-reproject-20261104');d=np.load(O/'mapping.npz');m=json.loads((P/'dl_thrall.bbmodel').read_text());src=np.asarray(Image.open('/tmp/devils-drive-models/thrall/combined.png').convert('RGB'));atlas=np.asarray(Image.open(io.BytesIO(base64.b64decode(m['textures'][0]['source'].split(',')[1]))).convert('RGBA')).copy();h,w=src.shape[:2];uv=d['uv'];xx=(uv[:,0]%1)*w-.5;yy=(1-uv[:,1]%1)*h-.5;ix=np.floor(xx).astype(int);iy=np.floor(yy).astype(int);fx=(xx-ix)[:,None];fy=(yy-iy)[:,None]
c=(src[iy%h,ix%w]*(1-fx)*(1-fy)+src[iy%h,(ix+1)%w]*fx*(1-fy)+src[(iy+1)%h,ix%w]*(1-fx)*fy+src[(iy+1)%h,(ix+1)%w]*fx*fy)
atlas[d['y'],d['x'],:3]=np.clip(c,0,255).astype(np.uint8);buf=io.BytesIO();Image.fromarray(atlas).save(buf,format='PNG');m['textures'][0]['source']='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode();(O/'dl_thrall.bbmodel').write_text(json.dumps(m));
for n in ['thrall_mesh.npz','thrall_stats.json']:shutil.copy2(P/n,O/n)
(O/'result.json').write_text(json.dumps({'texels':len(d['x']),'distancePxPercentiles':np.percentile(d['distance'],[0,50,95,99,100]).tolist(),'geometryUnchanged':True,'alphaUnchanged':True,'method':'nearest source triangle at final pixel center; bilinear shader atlas RGB; global source BVH, no per-bone restriction; diagnostic only'},indent=2))
print((O/'result.json').read_text())
