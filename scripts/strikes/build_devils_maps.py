#!/usr/bin/env python3
"""Source-derived Devils' Lair collision maps; Downloads inputs are read-only.

Run with numpy + Pillow: python build_devils_maps.py build --source <extraction> --evidence /tmp/devils-map-evidence
The source GLB root rotates Z-up to Y-up. The reused sampler intentionally reads its direct
Z-up children and applies (x,z,-y) exactly once. Crops retain source scale 1 block/metre.
Arrival/boss pads and navigation clearance are explicit Minecraft adaptations, not extracted collision.
"""
from __future__ import annotations
import argparse, csv, hashlib, importlib.util, json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_SOURCE=Path('/Users/qf/Downloads/Devils-Lair-Strike-KO-2026-11-02')
OUT=ROOT/'src/main/resources/data/destiny/devils_lair/zones'
SPECS={
 'rocketyard':dict(zone='RY',glb='rocketyard',lo=[175,-350,-5],hi=[303,-244,65],seed='IN',cut=20,
  anchors={'IN':[255,-265,5],'C1':[239,-281,5],'C2':[228,-301,5],'L':[211,-284,5],'R':[257,-302,7],'OUT':[206,-319,5]},
  lanes=['C1','R','L'],route=['IN','C1','C2','OUT']),
 'refinery':dict(zone='RF',glb='refinery',lo=[-15,-180,-5],hi=[85,-85,45],seed='G',cut=20,
  anchors={'IN':[6,-108,6],'G':[28.00349,-131.09035,7.4045687],'A':[10,-128,6],'B':[43,-122,6],'C':[48,-151,13],'D':[15,-152,6],'EXIT':[43,-154,7]},
  lanes=['A','B','C','D'],route=['IN','G','EXIT']),
 'blast':dict(zone='BL',glb='the_blast',lo=[-20,-372,-5],hi=[110,-248,75],seed='IN',cut=25,
  anchors={'IN':[60,-269,5],'H':[47,-309,4],'L':[18,-317,5],'R':[78,-316,7],'D1':[69,-336,6],'W':[41.50606,-349.42175,7.792013],'B1':[67,-324,4],'B2':[28,-331,4],'EXIT':[19.49999,-359.3998,9.399996]},
  lanes=['R','L','H','D1','EXIT'],route=['IN','H','W','EXIT']),
 'lair':dict(zone='SP',glb='devils_lair',lo=[-82,-440,12],hi=[25,-350,100],seed='IN',cut=40,
  anchors={'IN':[-5.0322313,-372.56586,24.49999],'C':[-30,-396,26],'L':[-46,-390,25],'R':[-16,-413,25],'B':[-52,-415,25],'D1':[-54,-399,25],'D2':[-27,-422,25],'CHEST':[-28,-385,25]},
  lanes=['L','R','D1','D2'],route=['IN','CHEST','L','B','R','CHEST']),
}
# Authored shield lanes, retaining their three distinct arena sectors. Real NBT-world
# admission found S2 inside the side wall and S1/S3 occluded from the arrival pad.
# Each lane has three explicit clear-air alternatives; runtime still checks every
# live player's distance, collision, reservations and firing line before accepting.
FLOATS={
 'SP.S1':[[-43,-414,29],[-41,-412,29],[-45,-410,34]],
 'SP.S2':[[-22,-415,31],[-22,-417,31],[-22,-419,32]],
 'SP.S3':[[-52,-400,33],[-56,-396,33],[-56,-400,34]],
}
SOURCE_REFS={'RF.G':'o_ghost_scan_cage_orb','BL.EXIT':'o_cosmo_strike01_door01','SP.IN':'o_cosmo_strike01_hangar_door01'}

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def write_json(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def helper(source,evidence):
 spec=importlib.util.spec_from_file_location('devils_voxel_sampler',ROOT/'scripts/campaign/rising_maps.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.SRC=source;m.EVIDENCE=evidence;m.CACHE_DIR=evidence/'cache';m.CACHE_DIR.mkdir(parents=True,exist_ok=True)
 m._load_full_texture=lambda p:np.asarray(Image.open(p).convert('RGBA'),dtype=np.float32)/255
 return m

def centered(cell):return [float(cell[0])+.5,float(cell[1]),float(cell[2])+.5]

def point(m,state,pal,grid,src,seen,radius=16):
 c=m.nearest_standable(seen,grid.to_block(src),radius)
 if c is None:raise ValueError('No reachable source anchor near '+str(src))
 return tuple(map(int,c))

def ground_masks(m,state,states):
 return m.standable(state,states),m.passable_mask(state,states)

def pad(state,pal,cell,radius,height):
 """Small authored landing/footprint, never a whole replacement arena."""
 x,y,z=cell;sy,sz,sx=state.shape
 if min(x-radius,z-radius,y-1)<1 or x+radius>=sx-1 or z+radius>=sz-1 or y+height>=sy:raise ValueError('Pad outside map')
 state[y-1,z-radius:z+radius+1,x-radius:x+radius+1]=pal.id('minecraft:polished_andesite')
 state[y:y+height,z-radius:z+radius+1,x-radius:x+radius+1]=0

def route(m,state,states,a,b):
 st,pas=ground_masks(m,state,states)
 path=m.shortest_path(m.route_moves(st,pas,max_down=2),tuple(a),{tuple(b)})
 if path is None:raise ValueError('Disconnected route '+str((a,b)))
 return [tuple(map(int,p)) for p in path]

def mark(id,pos,role='ground',**tags):return dict(id=id,pos=pos,yaw=0.0,tags=dict(role=role,**{k:str(v) for k,v in tags.items()}))

def build_one(m,name,spec,source,evidence):
 glb_path=source/'maps_glb'/(spec['glb']+'.textured.glb');glb=m.Glb(glb_path)
 root=glb.j['nodes'][glb.j['scenes'][0]['nodes'][0]]
 if not np.allclose(root.get('rotation'),[-math.sqrt(.5),0,0,math.sqrt(.5)]):raise ValueError('Unexpected GLB axis root')
 if any('children' in n or 'matrix' in n for n in glb.nodes):raise ValueError('Nested/matrix geometry needs transform composition')
 grid=m.Grid(spec['lo'],spec['hi'],1.0);agg=m.voxelize(glb,grid,spec['lo'],spec['hi'],step=.3)
 pal=m.Palette();labels,terr,_=m.classify(agg,pal);labels=m.majority_smooth(grid,agg.key,labels)
 state=m.shape_blocks(grid,agg,labels,terr,pal);source_state=state.copy();stand,pas=ground_masks(m,state,pal.states)
 seed=m.nearest_standable(stand,grid.to_block(spec['anchors'][spec['seed']]),8)
 if seed is None:raise ValueError('Missing connected seed')
 seen=m.reach(stand,pas,seed,max_down=2)
 cells={k:point(m,state,pal,grid,p,seen) for k,p in spec['anchors'].items()}
 # Arrival pads fit all three Guardians without stacking. Boss feet have an explicit footprint.
 adaptations=[]
 for k,r,h in [('IN',4,4)]+([('W',4,9),('B1',3,9),('B2',3,9)] if name=='blast' else []):
  before=state.copy();pad(state,pal,cells[k],r,h);changed=int(np.count_nonzero(before!=state))
  adaptations.append(dict(kind='authored_landing_or_boss_pad',anchor=k,radius=r,height=h,changedBlocks=changed))
 # The entry-to-left-flank source route drops two blocks at this lip. Add a visible
 # two-block-wide step so ground enemies can traverse it in the reverse direction.
 if name=='rocketyard':
  for z in (29,30):state[14,z,69]=pal.id('minecraft:polished_andesite')
  adaptations.append(dict(kind='authored_bidirectional_flank_step',cells=[[69,14,29],[69,14,30]],reason='Reverse mob route cannot climb the source two-block drop'))
 if name=='refinery':
  # Native navigation: a Dreg passes here, but Vandal/Captain heads hit this voxel.
  # Preserve the surrounding ceiling and floor; open only the verified bottleneck.
  clearance=[(54,14,65),(62,19,71),(53,14,64),(47,14,58),(46,14,57)]
  # Diagonal navigation checks both orthogonal neighbour columns as well.
  # Widen the headroom at the diagnosed slab corners, without changing the floor.
  clearance=sorted({(x+dx,y,z+dz) for x,y,z in clearance for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]})
  for x,y,z in clearance:state[y,z,x]=0
  adaptations.append(dict(kind='authored_tall_actor_clearance',cells=[list(c) for c in clearance],reason='Native RF.C-to-entry path: full voxel and top slabs block the three-cell navigation envelope of 2.3-block actors'))
 # Reproject onto post-pad collision; retaining a pad's elevation keeps the promised landing surface.
 stand,pas=ground_masks(m,state,pal.states);seen=m.reach(stand,pas,cells[spec['seed']],max_down=2)
 for k in cells:
  if not seen[cells[k][1],cells[k][2],cells[k][0]]:
   cells[k]=point(m,state,pal,grid,spec['anchors'][k],seen)
 prefix=spec['zone'];markers=[];provenance=[]
 for k,c in cells.items():
  mid=prefix+'.'+k;at=centered(c)
  markers.append(mark(mid,at))
  provenance.append(dict(id=mid,kind='source_reference_projected_to_reachable_voxel' if mid in SOURCE_REFS or mid=='BL.W' else 'authored_gameplay_anchor_on_source_geometry',sourceReference=SOURCE_REFS.get(mid,'walker_actor_80CC073C' if mid=='BL.W' else None),sourceXYZ=spec['anchors'][k],mappedBeforeProjection=grid.to_block(spec['anchors'][k]).tolist(),final=at,projectionBlocks=round(float(np.linalg.norm(np.array(at)-grid.to_block(spec['anchors'][k]))),4)))
 # Three distinct entry positions are on the inspected arrival pad.
 x,y,z=cells['IN']
 for i,(dx,dz) in enumerate([(-2,0),(0,0),(2,0)]):markers.append(mark(prefix+'.IN.'+str(i),[x+dx+.5,float(y),z+dz+.5],seat=i))
 # Each lane has at least eight grounded, mutually spaced alternatives. Runtime still checks player distance/LOS/path.
 for lane in spec['lanes']:
  x,y,z=cells[lane];chosen=[]
  for radius in (3,6,10,14):
   candidates=[]
   for yy,zz,xx in np.argwhere(seen[max(1,y-3):min(seen.shape[0]-1,y+4),max(0,z-radius):min(seen.shape[1],z+radius+1),max(0,x-radius):min(seen.shape[2],x+radius+1)]):
    c=(int(xx)+max(0,x-radius),int(yy)+max(1,y-3),int(zz)+max(0,z-radius))
    if c[1]+3>=state.shape[0] or not pas[c[1]:c[1]+3,c[2],c[0]].all():continue
    candidates.append(c)
   for c in sorted(candidates,key=lambda c:((c[0]-x)**2+(c[2]-z)**2+2*(c[1]-y)**2,c)):
    if any((c[0]-a[0])**2+(c[2]-a[2])**2<4 for a in chosen):continue
    chosen.append(c)
    if len(chosen)>=16:break
   if len(chosen)>=16:break
  if len(chosen)<8:raise ValueError(f'{name} lane {lane} has only {len(chosen)} spawn candidates')
  for i,c in enumerate(chosen):markers.append(mark(prefix+'.spawn.'+lane+'.'+str(i),centered(c),lane=prefix+'.'+lane))
 # Preserve original prop positions separately from their interaction anchors.
 with (source/'encounters/prop-markers.csv').open(encoding='utf-8-sig') as f:props=list(csv.DictReader(f))
 zone_name={'rocketyard':'Rocketyard','refinery':'Refinery','blast':'The Blast','lair':"Devils' Lair"}[name]
 for p in props:
  if p['zone']!=zone_name or not any(t in p['name'] for t in ['ghost_scan','laserweb','servitor_warp','door01']):continue
  xyz=[float(p[k]) for k in ['x','y','z']];at=grid.to_block(xyz)
  if not np.all((at>=0)&(at<grid.size)):continue
  mid=prefix+'.source.'+p['name'];markers.append(mark(mid,at.tolist(),'source_prop',source=p['name'],entity=p['entity']))
  provenance.append(dict(id=mid,kind='exact_source_marker_transform',sourceXYZ=xyz,final=at.tolist(),worldID=p['worldID']))
 if name=='lair':
  for lane,positions in FLOATS.items():
   for index,src in enumerate(positions):
    mid=lane if index==0 else f'{lane}.alternative.{index}'
    at=grid.to_block(src)
    markers.append(mark(mid,at.tolist(),'flying',authored=True,lane=lane))
    provenance.append(dict(id=mid,kind='authored_shield_servitor',sourceXYZ=src,final=at.tolist(),reason='Distinct arena sectors with alternate clear-air pads; native-world collision and arrival firing-line regression'))
  # Boss starts at original warp 2, not the unusable zero actor record. Keep ground C as C.ground.
  c=next(x for x in markers if x['id']=='SP.C');c['id']='SP.C.ground'
  warp=next(x for x in markers if x['id']=='SP.source.servitor_warp_2')
  markers.append(mark('SP.C',warp['pos'],'flying',source='servitor_warp_2'))
  for i in range(1,5):
   warp=next(x for x in markers if x['id']==f'SP.source.servitor_warp_{i}')
   markers.append(mark(f'SP.WARP.{i}',warp['pos'],'flying',source=f'servitor_warp_{i}'))
 routes=[]
 pairs=list(zip(spec['route'],spec['route'][1:]))+[(spec['seed'],k) for k in spec['lanes']]
 for a,b in pairs:
  path=route(m,state,pal.states,cells[a],cells[b]);routes.append(dict(id=prefix+'.'+a+'-'+b,fromAnchor=prefix+'.'+a,toAnchor=prefix+'.'+b,cells=[list(c) for c in path],points=[centered(c) for c in path],maxStepUp=1,maxDrop=2))
 # Add local lighting to roofed combat paths, using side-mounted bulbs rather than full-bright mobs.
 for k,c in cells.items():
  x,y,z=c
  if not np.any(state[min(y+4,state.shape[0]):,z,x]):continue
  for dx,dz in [(-3,0),(3,0),(0,-3),(0,3)]:
   xx,zz=x+dx,z+dz
   if 0<xx<state.shape[2]-1 and 0<zz<state.shape[1]-1 and state[y+2,zz,xx]==0:
    state[y+2,zz,xx]=pal.id('minecraft:light[level=12,waterlogged=false]')
 # No hidden block barriers: runtime owns explicit out-of-bounds recovery; cropped vistas are not playable.
 meta=m.write_zone(OUT/(name+'.zone'),state,pal.states)
 m.render_top(state,pal.states,evidence/(name+'-voxel-top.png'),ycut=int(spec['cut']-spec['lo'][2]),marks=[(int(v['pos'][0]),int(v['pos'][2]),(0,255,130)) for v in markers if v['tags']['role']=='ground' and '.spawn.' not in v['id']])
 np.save(evidence/(name+'-state.npy'),state);write_json(evidence/(name+'-palette.json'),pal.states)
 write_json(evidence/(name+'-anchors.json'),provenance)
 return dict(size=meta['size'],markers=markers),dict(routes=routes),dict(**meta,sourceGlb=str(glb_path.relative_to(source)),sourceSha256=sha(glb_path),cropSourceZUp=dict(min=spec['lo'],max=spec['hi']),mapping='local = (source.x-minX, source.z-minZ, -source.y+maxY)',scale=1.0,sourceSampleStep=.3,sourceVoxelCount=int(np.count_nonzero(source_state)),adaptations=adaptations,changedFromSourceBlocks=int(np.count_nonzero(source_state!=state)),anchorProvenance=provenance,reachableCells=int(seen.sum()),routeCount=len(routes),offlineRoutesVerified=True,inGameVerified=False,remainingChecks=['3-player travel, boss footprint and all spawn LoS','native screenshots and lighting','combat corridor widths and all flank paths','continuous outer boundary and fall-recovery runtime'])

def build(source,evidence):
 evidence.mkdir(parents=True,exist_ok=True);m=helper(source,evidence);markers={'schema':1,'zones':{}};routes={'schema':1,'zones':{}};manifest={'schema':1,'activity':'devils_lair','fixedPlayers':3,'sourceRoot':str(source),'status':'source-derived implementation candidate; native QA required','samplerSha256':sha(ROOT/'scripts/campaign/rising_maps.py'),'generatorSha256':sha(Path(__file__)),'zones':{}}
 for name,spec in SPECS.items():
  print('Building',name,flush=True);markers['zones'][name],routes['zones'][name],manifest['zones'][name]=build_one(m,name,spec,source,evidence)
 write_json(OUT/'markers.json',markers);write_json(OUT/'routes.json',routes)
 manifest['texturesSha256']={u:sha((source/'maps_glb'/u).resolve()) for u in sorted(m._TEX_CACHE)}
 manifest['outputsSha256']={p.name:sha(p) for p in [*(OUT/(n+'.zone') for n in SPECS),OUT/'markers.json',OUT/'routes.json']}
 write_json(OUT/'manifest.json',manifest);print('Built source-derived maps; native acceptance still required.',flush=True)

def verify(source):
 manifest=json.loads((OUT/'manifest.json').read_text())
 for name,digest in manifest['outputsSha256'].items():
  if sha(OUT/name)!=digest:raise ValueError('Output drift '+name)
 for name,z in manifest['zones'].items():
  if sha(source/z['sourceGlb'])!=z['sourceSha256']:raise ValueError('Source drift '+name)
 print('Verified bundled outputs and four GLB hashes. No native gameplay claim.')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['build','verify']);p.add_argument('--source',type=Path,default=DEFAULT_SOURCE);p.add_argument('--evidence',type=Path,default=Path('/tmp/devils-map-evidence'));a=p.parse_args()
 if a.command=='build':build(a.source.resolve(),a.evidence.resolve())
 else:verify(a.source.resolve())
