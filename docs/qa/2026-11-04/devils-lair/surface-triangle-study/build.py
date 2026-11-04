"""Bake a static diagnostic native-plane control from the reduced source surface."""
import sys,json,math,hashlib,os
from pathlib import Path
import numpy as np
from PIL import Image
root=Path.cwd();sys.path.insert(0,str(root/'scripts/mesh'))
from native_triangle_elements_w115 import split_triangle,to_element
out=Path(os.environ.get('DEVILS_TRIANGLE_DIR','/tmp/devils-triangle-study'));cache=Path('/tmp/devils-drive-marauder-dual')
d=np.load(out/'surface.npz');stats=json.loads((cache/'marauder_stats.json').read_text());k=stats['k'];y0=stats['y0']
source=np.array(Image.open(cache/'combined.png').convert('RGBA'));h,w=source.shape[:2]
# Fit native unrotated element coordinates; diagnostic renderer undoes this factor.
v=d['V'];verts=np.stack([v[:,:,0]*k,v[:,:,2]*k+y0,-v[:,:,1]*k],axis=-1)*.5+8
parts=[];degenerate=0
for i,tri in enumerate(verts):
 try:split=split_triangle(tri)
 except ValueError:degenerate+=1;continue
 for part in split:parts.append((i,part))
tile=32;stride=tile+2;columns=math.ceil(math.sqrt(len(parts)));size=2**math.ceil(math.log2(columns*stride));columns=size//stride
atlas=np.zeros((size,size,4),np.uint8);elements=[]
grid=(np.arange(tile)+.5)/tile;uu,vv=np.meshgrid(grid,grid)
for index,(i,part) in enumerate(parts):
 xyz=np.array(part['origin'])+uu[:,:,None]*part['width']*np.array(part['u'])+(1-vv[:,:,None])*part['height']*np.array(part['v'])
 tri=verts[i];basis=np.stack([tri[1]-tri[0],tri[2]-tri[0]],axis=1)
 weights=(xyz-tri[0])@np.linalg.pinv(basis).T
 uv=d['UV'][i,0]+weights[:,:,0,None]*(d['UV'][i,1]-d['UV'][i,0])+weights[:,:,1,None]*(d['UV'][i,2]-d['UV'][i,0])
 x=np.clip((uv[:,:,0]*w).astype(int),0,w-1);y=np.clip(((1-uv[:,:,1])*h).astype(int),0,h-1)
 rgba=source[y,x].copy();rgba[:,:,3]=np.where((uu<=vv)&(rgba[:,:,3]>=128),255,0)
 tx=(index%columns)*stride+1;ty=(index//columns)*stride+1
 atlas[ty:ty+tile,tx:tx+tile]=rgba
 element=to_element(part,str(d['BONE'][i]),[tx/size*16,ty/size*16,(tx+tile)/size*16,(ty+tile)/size*16]);elements.append(element)
Image.fromarray(atlas).save(out/'atlas.png')
(out/'native-model.json').write_text(json.dumps(dict(textures={'0':'diagnostic:atlas'},elements=elements),separators=(',',':')))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(out/'manifest.json').write_text(json.dumps(dict(sourceTriangles=len(v),nativePlanes=len(parts),degenerateTriangles=degenerate,atlasSize=size,tile=tile,scale=.5,offset=8,sourceCacheSha256=sha(cache/'marauder_mesh.npz'),shaderSha256=sha(cache/'combined.png'),reducedSha256=sha(out/'surface.npz'),geometrySha256=sha(out/'native-model.json'),atlasSha256=sha(out/'atlas.png'),status='static isolated diagnostic; no rig, animation, Minecraft or performance acceptance'),indent=2)+'\n')
print((out/'manifest.json').read_text())
