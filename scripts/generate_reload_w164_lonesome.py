#!/usr/bin/env python3
"""W164 Lonesome: W123 semantic heel split, authored grip-fed FP reload.
No DCC, runtime, timing, sound, ammo or canonical asset mutation. --verify is read-only.
"""
import argparse,copy,hashlib,io,itertools,json,math,runpy
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/'src/main/resources/assets/destiny'
ART=ROOT/'art/weapons/w164/lonesome'
SOURCE=ASSET/'models/weapon_surface_w123/lonesome.json'
KEY='weapon_reload_w164_lonesome/lonesome'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','moving')
MOVING=(77,78)
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/lonesome.json': '5420acfac0c21795a37d206091fa2a79373d58ea124bb07351d2c4dacdeb5605', 'src/main/resources/assets/destiny/models/weapon/sidearm/lonesome.json': '91c2a950f979dee2e22afe74f75206bf53a451ab725ebb837b025bd52b4c0872', 'src/main/resources/assets/destiny/models/weapon/sidearm/lonesome_twohand.json': '0b91770790ffd1267b850e44969113177a049800bdaa4c21d8eb34d849bc47a0', 'src/main/resources/assets/destiny/items/weapon/lonesome.json': '7665d22fe3263f21ef8618ba27dbbb9c5528e665df2c43758b8b3198e6f19232', 'src/main/resources/assets/destiny/textures/item/weapon/w123/lonesome.png': '71b2d1bfbf73a4d2d483c4f8bb4bf95f4f0b785a9c146e81af45722dbd2042af'}
# progress, body Euler delta, body translation, magazine travel along tilted grip.
KEYS=[(0,[0,0,0],[0,0,0],0),(.15,[18,-5,-12],[-.4,.2,0],0),
 (.30,[36,-10,-24],[-.8,.5,.3],3),(.45,[40,-12,-27],[-.8,.5,.3],6.7),
 (.60,[40,-12,-27],[-.8,.5,.3],5.2),(.75,[34,-8,-20],[-.5,.3,.2],0),
 (.85,[16,-3,-8],[-.2,.1,0],0),(1,[0,0,0],[0,0,0],0)]
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def rotate(v,r):
 x,y,z=v;a,b,c=map(math.radians,r)
 x,y=x*math.cos(c)-y*math.sin(c),x*math.sin(c)+y*math.cos(c)
 x,z=x*math.cos(b)+z*math.sin(b),-x*math.sin(b)+z*math.cos(b)
 y,z=y*math.cos(a)-z*math.sin(a),y*math.sin(a)+z*math.cos(a)
 return [x,y,z]
def sample(t):
 if not math.isfinite(t) or not 0<=t<=1:raise ValueError(t)
 for a,b in zip(KEYS,KEYS[1:]):
  if t<=b[0]:
   u=(t-a[0])/(b[0]-a[0]);u=u*u*(3-2*u)
   return [[a[k][i]+(b[k][i]-a[k][i])*u for i in range(3)] for k in (1,2)]+[a[3]+(b[3]-a[3])*u]
def compose(a,b):
 # Build columns of R_idle * R_body with native ItemTransform Rx*Ry*Rz order.
 m=[[rotate(rotate([int(k==j) for k in range(3)],b),a)[i] for j in range(3)] for i in range(3)]
 return [math.degrees(v) for v in (math.atan2(-m[1][2],m[2][2]),math.asin(max(-1,min(1,m[0][2]))),math.atan2(-m[0][1],m[0][0]))]
def pose(frame,part,base):
 d=copy.deepcopy(base)
 if frame in (0,20):return d
 r,t,travel=sample(frame/20)
 pivot=[0,1.44,.81] # W123 grip_core rotation origin minus model centre (8,8,8).
 offset=rotate([0,-travel,0],[-10,0,0]) if part=='moving' else [0,0,0]
 turned=rotate(pivot,r);moved=rotate(offset,r)
 local=[t[i]+pivot[i]-turned[i]+moved[i] for i in range(3)]
 for context in FP:
  p=d[context];idle=p['rotation']
  delta=rotate([local[i]*p['scale'][i] for i in range(3)],idle)
  p['rotation']=[round(v,6) for v in compose(idle,r)]
  p['translation']=[round(v+delta[i],6) for i,v in enumerate(p['translation'])]
 return d
def png(im):
 out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def storyboard():
 im=Image.new('RGB',(1440,900),'#121c26');draw=ImageDraw.Draw(im)
 for i,p in enumerate(sorted(ART.glob('reference-*.png'))):
  tile=Image.open(p).convert('RGB');tile.thumbnail((360,203));x=i%4*360;y=i//4*280+32
  im.paste(tile,(x,y));draw.text((x+8,y+209),f'{10.25+i*.1:.2f}s | Lonesome manual reload',fill='white')
 draw.text((12,872),'UFahmRrAruE | 10.25-11.35s | observed rigid upper / hand at grip heel; exact magazine path occluded',fill='white')
 return png(im)
def comparison(original,geos):
 im=Image.new('RGB',(1600,980),'#121c26');draw=ImageDraw.Draw(im)
 for tile,frame in enumerate((0,3,6,9,12,15,18,20)):
  x0=tile%4*400;y0=tile//4*460+25;polys=[]
  for part in PARTS:
   transform=pose(frame,part,original['display'])[FP[0]]
   for e in geos[part]['elements']:
    points=[]
    for mask in range(8):
     v=[e['to' if mask>>a&1 else 'from'][a] for a in range(3)]
     if 'rotation' in e:
      q=e['rotation'];axis='xyz'.index(q['axis']);r=[0,0,0];r[axis]=q['angle']
      v=[v[i]-q['origin'][i] for i in range(3)];v=rotate(v,r);v=[v[i]+q['origin'][i] for i in range(3)]
     v=rotate([(v[i]-8)*transform['scale'][i] for i in range(3)],transform['rotation'])
     points.append([v[i]+transform['translation'][i] for i in range(3)])
    for face in ((0,1,3,2),(0,4,5,1),(0,2,6,4),(7,6,2,3),(7,3,1,5),(7,5,4,6)):
     ps=[points[i] for i in face];screen=[(x0+180+(p[2]*.86+p[0]*.5)*16,y0+230-(p[1]+p[0]*.18-p[2]*.15)*16) for p in ps]
     polys.append((sum(p[0]-p[2]*.5 for p in ps),screen, '#abb6ba' if part=='body' else '#e9b55c'))
  for _,poly,color in sorted(polys,key=lambda p:p[0]):draw.polygon(poly,fill=color,outline='#35434a')
  draw.text((x0+10,y0),f'Frame {frame:02d}/20 | native FP transform',fill='white')
 draw.text((15,948),'OFFLINE semantic volume comparison | grey body / gold heel + authored hidden insert | original face UVs preserved; no hands / native acceptance pending',fill='white')
 return png(im)
def generate():
 for p,h in PINS.items():assert sha((ROOT/p).read_bytes())==h,p
 original=json.loads(SOURCE.read_bytes());assert len(original['elements'])==97
 item=json.loads((ASSET/'items/weapon/lonesome.json').read_bytes())
 two=json.loads((ASSET/'models/weapon/sidearm/lonesome_twohand.json').read_bytes())['display']
 twohand=runpy.run_path(str(ROOT/'scripts/build_weapons_w30.py'))['two_hand_display']
 geos={}
 for part in PARTS:
  g={k:copy.deepcopy(v) for k,v in original.items() if k not in ('display','elements')}
  g['elements']=[copy.deepcopy(e) for i,e in enumerate(original['elements']) if (i in MOVING)==(part=='moving')];geos[part]=g
 # Small solid internal insert, fully inside grip_core in ready. Same cant/pivot,
 # extents strictly inside the unrotated core. Existing dark grip UV reused.
 insert=copy.deepcopy(original['elements'][72]);insert.update(name='authored_internal_magazine',**{'from':[7.6,6.5,8.3],'to':[8.4,11.4,9.3]})
 geos['moving']['elements'].append(insert)
 out={ASSET/f'models/{KEY}_{p}.json':encode(g) for p,g in geos.items()};entries=[]
 for frame in range(21):
  leaves={}
  for part in PARTS:
   native=pose(frame,part,original['display'])
   for grip in ('native','twohand'):
    d=copy.deepcopy(native if grip=='native' else two if frame in (0,20) else twohand(native,'sidearm'))
    if grip=='twohand':
     for c in two:
      if c not in FP:d[c]=copy.deepcopy(two[c])
    name=f'{KEY}_{frame:02d}_{part}_{grip}';out[ASSET/f'models/{name}.json']=encode(dict(parent=f'destiny:{KEY}_{part}',display=d))
    leaves[part,grip]=dict(type='minecraft:model',model='destiny:'+name)
  def comp(grip):return dict(type='minecraft:composite',models=[leaves[p,grip] for p in PARTS])
  entries.append(dict(threshold=frame/20,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=comp('twohand'),on_false=comp('native'))))
 graph=copy.deepcopy(item);graph['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=item['model']))],fallback=item['model'])
 out[ASSET/f'items/{KEY}.json']=encode(graph)
 assert len(out)==87
 motion=dict(url='https://www.youtube.com/watch?v=UFahmRrAruE',title='Destiny 2 | Lonesome God Roll Gambit Sidearm PvP Gameplay Review | Season Of Opulence',clip=[0,50],frames=[dict(file=f'reference-{i:02d}.png',seconds=round(10.25+i*.1,2)) for i in range(12)],
 observed=['Manual reload at approximately 10.4-11.1 seconds: gun rolls upward, support hand operates at lower grip/heel; returns to ready.', 'Barrel/shroud/breech remain a rigid upper with grip during observed sequence; no visible break-action hinge opening.', 'HUD changes 3 to 12 during seating phase; this is not a dodge refill.'],
 mechanism='grip-fed magazine/heel exchange',confidence='moderate: lower-grip support-hand operation visible, magazine body obscured',
 authoredAssumptions=['Heel and heel_lower treated as magazine baseplate; names alone do not prove a magazine.', 'One internal cuboid strictly inside rotated grip_core at rest; dimensions and exit distance authored.', 'Travel, easing, roll angles and normalized timing are approximate, not measured original bones. R_idle * R_body about grip_core pivot, then rotated magazine delta; native RxRyRz order.', 'Solid grip well retained; no interior socket cut; insert intersects hidden solid grip while seating.'],rejected=['Rat King footage not used','1JGqI6tdbgI 40-85 and 130-170 seconds inspected: dodge refills excluded as mechanism evidence'],
 rawCache='/private/tmp/destiny-weapons-w30/raw/lonesome/extracted',rawFbxSha256=sha(Path('/private/tmp/destiny-weapons-w30/raw/lonesome/extracted/Lonesome.fbx').read_bytes()),rawInspection='inert FBX nodes: only Mesh_0000.rip..Mesh_0009.rip models; no AnimationStack or semantic bones recovered',sourceAnimationRecovered=False,handIK=False,keyframes=KEYS)
 out[ART/'motion-reference.json']=encode(motion);out[ART/'storyboard.png']=storyboard();out[ART/'comparison.png']=comparison(original,geos)
 assets={str(p.relative_to(ROOT)):sha(v) for p,v in out.items() if p.is_relative_to(ASSET)}
 manifest=dict(stage='W164',weapon='lonesome',graphId='destiny:'+KEY,assets=87,frames=21,parts=list(PARTS),partCounts={p:len(g['elements']) for p,g in geos.items()},sourceElements=97,assembledElements=98,maxAssembledElements=1000,movingOriginalIndices=list(MOVING),movingOriginalNames=['heel','heel_lower'],addedInternalDetails=1,progressFloatIndex=1,gripBooleanIndex=0,firstPersonOnly=True,exactOriginalGraphFallback=True,endpointsExactDisplay=True,sourceModel=str(SOURCE.relative_to(ROOT)),originalSha256=PINS,sha256=assets,referenceSha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(ART.glob('reference-*.png'))},evidenceSha256={str(p.relative_to(ROOT)):sha(v) for p,v in out.items() if p.is_relative_to(ART)},generatorSha256=sha(Path(__file__).read_bytes()),mechanismConfidence=motion['confidence'],authoredApproximation=True,sourceAnimationRecovered=False,handIK=False,nativeGameplayVerified=False,runtimeIntegration='master-owned and pending',limitations=motion['authoredAssumptions'])
 out[ART/'manifest.json']=encode(manifest);return out
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
 owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w164-worktrees.json').read_bytes())['features'] if f['name']=='w164-lonesome-reload'))
 out=generate()
 for p,data in out.items():
  rel=str(p.relative_to(ROOT));assert rel in owned,rel
  if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+rel
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 print(('Verified' if args.verify else 'Generated')+' 87 pack files / 21 frames x 2 parts x 2 grips / 98 assembled elements')
if __name__=='__main__':main()
