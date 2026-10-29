from pathlib import Path
import sys,json,gzip,hashlib,collections,argparse
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/tower'))
from material_shader_w245 import MaterialBaker
from voxelize_courtyard import srgb_to_linear

def lab(rgb):
 l=srgb_to_linear(np.asarray(rgb));a=l@np.array([[.4122214708,.2119034982,.0883024619],[.5363325363,.6806995451,.2817188376],[.0514459929,.1073969566,.6299787005]])
 a=np.cbrt(a);return a@np.array([[.2104542553,1.9779984951,.0259040371],[.7936177850,-2.4285922050,.7827717662],[-.0040720468,.4505937099,-.8086757660]])

def generate(cache,material_root,block_palette,out,resource):
 d=np.load(cache);xyz=d['xyz'];mats=d['materials'];mid=d['material'];uv=d['uv'];normal=d['normal'];srcpalette=d['palette'];ids=d['source_id']
 baker=MaterialBaker(material_root,allow_representative=True);pal=json.loads(Path(block_palette).read_text());colors=np.array([p['rgb'] for p in pal])/255.;pallab=lab(colors);rgb=np.zeros((len(xyz),3));valid=np.zeros(len(xyz),dtype=bool)
 out.mkdir(parents=True,exist_ok=True);baked=out/'baked';baked.mkdir(exist_ok=True)
 report={};supported=[]
 for idx in np.unique(mid):
  tag=str(mats[idx]);which=mid==idx
  world=xyz[which].astype(float)/2;world=np.column_stack((world[:,0],-world[:,2],world[:,1]-20));norm=normal[which];norm=np.column_stack((norm[:,0],-norm[:,2],norm[:,1]));psuv=uv[which].copy();psuv[:,1]=1-psuv[:,1];uvok=np.isfinite(psuv).all(axis=1,keepdims=True);color,ok=baker.sample(tag,psuv,inputs={'world_xyz':world,'world_xy':world[:,:2],'normal':norm});ok=ok.ravel() & uvok.ravel();
  if baker.recipes.get(tag,{}).get('family')=='projected_decal':ok[:]=False
  rgb[which]=color;valid[which]=ok
  count=int(np.count_nonzero(ok));report[tag]={'surfaceCells':int(which.sum()),'bakedCells':count,'medianSrgb':np.median(color[ok],axis=0).tolist() if count else None}
  if count:
   im=Image.fromarray(baker.bake(tag,size=128));im.save(baked/(tag+'.png'));supported.append(tag)
 # Per-material quantization avoids stochastic dithering; only source-defined color variation remains.
 rgb=np.clip(rgb,0,1);dist=np.square(lab(rgb)[:,None,:]-pallab[None,:,:]).sum(2);chosen=dist.argmin(1)
 # Remove one-cell speckles only where four same-material neighbors agree; retain edges, stripes, and seams.
 lo=xyz.min(0)-1;dims=xyz.max(0)-lo+2;lookup=np.full(dims,-1,dtype=np.int32);q=xyz-lo;lookup[tuple(q.T)]=np.arange(len(xyz))
 neighbors=[]
 for off in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
  ni=lookup[tuple((q+off).T)];safe=np.maximum(ni,0);good=(ni>=0)&valid[safe]&(mid[safe]==mid);neighbors.append(np.where(good,chosen[safe],-1))
 neigh=np.stack(neighbors,axis=1)
 for ci in range(len(pal)):
  common=(neigh==ci).sum(1)>=4;chosen[common]=ci
 priorpath=ROOT/'src/main/resources/data/destiny/tower/courtyard-materials-w243.json.gz';prior=json.loads(gzip.decompress(priorpath.read_bytes()));priorcells={tuple(c[:3]):prior['palette'][c[3]]for c in prior['cells']}
 palette=[];cells=[];counts=collections.Counter()
 def pi(s):
  if s not in palette:palette.append(s)
  return palette.index(s)
 for i in np.flatnonzero(valid):
  pos=tuple(map(int,xyz[i]));expected=priorcells.get(pos,str(srcpalette[ids[i]]));state=pal[int(chosen[i])]['block']
  if state==expected:continue
  # Greenery comes from the earlier geometry pass and remains vegetation.
  if expected in ('minecraft:moss_block','minecraft:green_terracotta','minecraft:green_concrete'):continue
  cells.append([*pos,pi(expected),pi(state)]);counts[state]+=1
 cells.sort(key=lambda c:(c[0]>>4,c[2]>>4,c[1],c[0],c[2]))
 source=ROOT/'src/main/resources/data/destiny/tower/courtyard.vox.gz';body={'schema':1,'sourceVoxelSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'priorMaterialSHA256':hashlib.sha256(priorpath.read_bytes()).hexdigest(),'palette':palette,'cells':cells}
 resource.parent.mkdir(parents=True,exist_ok=True)
 with resource.open('wb')as f,gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0)as z:z.write(json.dumps(body,separators=(',',':')).encode())
 summary={'cells':len(cells),'mappedCells':len(xyz),'bakedCells':int(valid.sum()),'sourceVoxelSHA256':body['sourceVoxelSHA256'],'priorMaterialSHA256':body['priorMaterialSHA256'],'outputBytes':resource.stat().st_size,'paletteCounts':dict(counts),'materials':report,'uvContract':'Charm StaticPart.TransformUVs already applied scale/offset and V flip: PS UV=(exported U,1-exported V); source crop contains no terrain meshes.','limits':['Representative static basecolor bake; TEXCOORD8 vertex buffer and lighting/reflection/engine channels not fully reconstructed.','Minecraft palette quantization; no new client textures or shaders.']}
 (out/'bake-audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 np.savez_compressed(out/'surface-colors.npz',xyz=xyz,material=mid,valid=valid,rgb=rgb,block=chosen)
 contact=Image.new('RGB',(600,100*((len(supported)+3)//4)),'#202020');draw=ImageDraw.Draw(contact)
 for i,tag in enumerate(supported):
  im=Image.open(baked/(tag+'.png')).convert('RGB').resize((90,72));x=(i%4)*150;y=(i//4)*100;contact.paste(im,(x,y));draw.text((x,y+75),tag,fill='white')
 contact.save(out/'baked-materials.png');print(json.dumps({k:v for k,v in summary.items() if k!='materials'},indent=2))
 return baker,supported

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,default=Path('/private/tmp/destiny-w245/geometry-uv.npz'));p.add_argument('--materials',type=Path,default=Path('/Volumes/qf-ssd/Destiny-Tower-Materials-2026-10-29'));p.add_argument('--palette',type=Path,default=ROOT/'scripts/tower/block-palette-w245.json');p.add_argument('--out',type=Path,default=Path('/private/tmp/destiny-w245/bake'));p.add_argument('--resource',type=Path,default=ROOT/'src/main/resources/data/destiny/tower/courtyard-baked-w245.json.gz');a=p.parse_args();generate(a.cache,a.materials,a.palette,a.out,a.resource)
