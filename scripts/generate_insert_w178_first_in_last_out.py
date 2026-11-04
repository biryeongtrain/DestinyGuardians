#!/usr/bin/env python3
"""FIRST IN, LAST OUT: one-shell initial / held loop / cosmetic return.

Canonical W133 solids and face UV unchanged. New hidden cartridge only.
Actual esbeekay 5IZfs2bjrYY reference; curves/occluded path authored, no IK.
W177 rigid matrix composition pattern only; no other weapon motion copied.
"""
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w178/first_in_last_out')
KEY='weapon_insert_w178_first_in_last_out/first_in_last_out'
SOURCE=A/'models/weapon_surface_w123/first_in_last_out.json'
TWOHAND=A/'models/weapon/shotgun/first_in_last_out_twohand.json'
ITEM=A/'items/weapon/first_in_last_out.json'
TEXTURE=A/'textures/item/weapon/w123/first_in_last_out.png'
SELF=Path('scripts/generate_insert_w178_first_in_last_out.py')
FP=('firstperson_righthand','firstperson_lefthand')
PHASES=('initial','loop','return')
PARTS=('body','shell')
GRIPS=('native','twohand')
GRIP=(8.,8.88,8.53)
SHELL_ANCHOR=(8.,9.96,4.65)
HOLD=((18.,-8.,-42.),(-.35,.55,.20))
# Lift once; establish the held receiver before bringing ONE shell underneath.
# Each record: normalized phase, body local XYZ, presentation shift, shell local offset.
KEYS={
 'initial':(
  (0.,(0,0,0),(0,0,0),(-1.4,-2.1,1.9)),
  (.15,(8,-3,-19),(-.12,.2,.08),(-1.4,-2.1,1.9)),
  (.30,*HOLD,(-1.4,-2.1,1.9)),
  (.40,*HOLD,(-1.4,-2.1,1.9)),
  (.58,*HOLD,(-.70,-1.05,1.45)),
  (.70,(18.4,-8.3,-42.8),(-.34,.58,.21),(0,-.12,.8)),
  (.87,(18.9,-8.2,-42.4),(-.35,.62,.18),(0,0,-2.1)),
  (1.,*HOLD,(0,0,-2.1))),
 'loop':(
  (0.,*HOLD,(-1.4,-2.1,1.9)),
  (.15,*HOLD,(-1.4,-2.1,1.9)),
  (.38,*HOLD,(-.70,-1.05,1.45)),
  (.55,(18.4,-8.3,-42.8),(-.34,.58,.21),(0,-.12,.8)),
  (.80,(18.9,-8.2,-42.4),(-.35,.62,.18),(0,0,-2.1)),
  (1.,*HOLD,(0,0,-2.1))),
 'return':(
  (0.,*HOLD,(0,0,-2.1)),
  (.3,(13,-6,-31),(-.25,.35,.12),(0,0,-2.1)),
  (.7,(4,-2,-9),(-.07,.08,.03),(0,0,-2.1)),
  (1.,(0,0,0),(0,0,0),(0,0,-2.1)))
}
# Discrete occlusion: reveal already-full-size below the receiver, disappear only
# after the cartridge is seated inside the existing tube. Never shrink in air.
VISIBLE={'initial':(.40,.87),'loop':(.15,.80)}
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/first_in_last_out.json': '213472da31e85fe3a017496c59bd0bb544be9e2a66350f83611ea07fe267371b', 'src/main/resources/assets/destiny/textures/item/weapon/w123/first_in_last_out.png': 'd604cadade97cfbbac54dccb8d3d29f0a2f19b5872ed08305564fb12944c7fea', 'src/main/resources/assets/destiny/models/weapon/shotgun/first_in_last_out_twohand.json': '22249bc1042919540784f9fe794102d93410ff8860f9b09d0bbcbb9998e07f11', 'src/main/resources/assets/destiny/items/weapon/first_in_last_out.json': 'b68952d6959937986b16c116ee916d8e54d8b6ec5404e9ed116b50a703d475f7', 'src/main/resources/weapon_surface_w123/manifest.json': '4972bd808e5150d09e8f55e2c663b45f88ad8e660300310c5ecc04f4f672db6b', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b'}

def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def png(im):
 out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def mul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def vec(m,v):return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]
def transpose(m):return list(map(list,zip(*m)))
def xyz(angles):
 x,y,z=map(math.radians,angles);a,b,c,d,e,f=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
 return [[c*e,-c*f,d],[b*d*e+a*f,-b*d*f+a*e,-b*c],[-a*d*e+b*f,a*d*f+b*e,a*c]]
def euler(m):
 b=math.asin(max(-1.,min(1.,m[0][2])))
 a,c=(math.atan2(-m[1][2],m[2][2]),math.atan2(-m[0][1],m[0][0])) if abs(math.cos(b))>1e-8 else (math.atan2(m[2][1],m[1][1]),0)
 return [round(math.degrees(v),9) for v in (a,b,c)]
def sample(phase,p):
 if phase not in KEYS or not math.isfinite(p) or not 0<=p<=1:raise ValueError((phase,p))
 for a,b in zip(KEYS[phase],KEYS[phase][1:]):
  if p<=b[0]:
   t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
   return tuple([a[k][i]+(b[k][i]-a[k][i])*t for i in range(3)] for k in (1,2,3))
 raise ValueError((phase,p))
def shell_visible(phase,p):
 return phase in VISIBLE and VISIBLE[phase][0]<=p<VISIBLE[phase][1]

def pose_display(original,twohand,phase,p,part,grip):
 accepted=original if grip=='native' else twohand
 display=copy.deepcopy(accepted)
 if part=='body' and ((phase=='initial' and p==0) or (phase=='return' and p==1)):return display
 angles,shift,offset=sample(phase,p)
 body=xyz(angles);h=sub(GRIP,(8,8,8));anchor=sub(SHELL_ANCHOR,(8,8,8))
 visible=part=='body' or shell_visible(phase,p)
 # Source-local shell anchor, carried by same rigid receiver rotation.
 # Compensate rotation and visibility scale around the ANCHOR, not item origin.
 desired=add(h,vec(body,add(sub(anchor,h),offset)))
 local=sub(h,vec(body,h)) if part=='body' else sub(desired,vec(body,anchor if visible else (0,0,0)))
 for context in FP:
  idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
  if twohand[context]['scale']!=s or len(set(s))!=1:raise ValueError('Uniform equal first-person grip scale required')
  rotation=mul(base,body)
  position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
  if grip=='twohand':
   carrier=mul(xyz(twohand[context]['rotation']),transpose(base))
   position=add(vec(carrier,position),sub(twohand[context]['translation'],vec(carrier,idle['translation'])))
   rotation=mul(carrier,rotation)
  display[context]['rotation']=euler(rotation)
  display[context]['translation']=[round(v,9) for v in position]
  if not visible:display[context]['scale']=[0,0,0]
 if part=='shell':
  for ctx in set(display)-set(FP):display[ctx]['scale']=[0,0,0]
 return display

def shell_geometry(source):
 """Twelve overlapping solids: an octagonal case, head and joined rim.
 Four inscribed bars fill each octagonal section. Existing graphite34 / steel58
 atlas texels are reused; uniform end-face samples avoid coplanar face noise.
 """
 elements=[]
 for name,radius,z0,z1,uv_index in (
  ('case',.25,-.77,.49,34),('head',.26,.46,.70,58),('rim',.29,.67,.77,58)):
  for angle in (0,45,-45,90):
   c=list(SHELL_ANCHOR);c[2]+=(z0+z1)/2
   width=2*radius*math.tan(math.pi/8)
   sizes=[width,2*radius]
   if angle==90:sizes.reverse()
   faces=copy.deepcopy(source['elements'][uv_index]['faces'])
   # Equal UV endpoints sample a real existing texel. All overlapping front/back
   # faces share that texel, so they cannot introduce inconsistent end-face paint.
   for face in faces.values():
    uv=source['elements'][uv_index]['faces']['east']['uv'];u=(uv[0]+uv[2])/2;v=(uv[1]+uv[3])/2
    face['uv']=[u,v,u,v]
   e=dict(name='hidden_insert_'+name+'_'+str(angle),**{'from':[c[0]-sizes[0]/2,c[1]-sizes[1]/2,SHELL_ANCHOR[2]+z0],'to':[c[0]+sizes[0]/2,c[1]+sizes[1]/2,SHELL_ANCHOR[2]+z1]},faces=faces)
   if angle in (45,-45):e['rotation']=dict(origin=c,axis='z',angle=angle)
   elements.append(e)
 return dict(credit='W178 hidden cartridge only; existing graphite tube34 / steel sleeve58 atlas texels; no extracted shell',textures=copy.deepcopy(source['textures']),elements=elements)

def expected_output_paths():
 return ({A/f'models/{KEY}_{part}.json' for part in PARTS}|
 {A/f'models/{KEY}_{phase}_{i:02}_{part}_{grip}.json' for phase in PHASES for i in range(21) for part in PARTS for grip in GRIPS}|
 {A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'})

def previews(output,ref):
 """Reconstruct ONLY emitted JSON; independent display/element matrix code.
 Inert texture raster helper does not call the motion sampler or pivot algebra.
 """
 helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
 tex=Image.open(ROOT/TEXTURE).convert('RGBA');triangles={}
 for part in PARTS:
  parent=json.loads(output[A/f'models/{KEY}_{part}.json'])
  for e in parent['elements']:
   r=e.get('rotation',{})
   if 'axis' in r:e['rotation']={'origin':r['origin'],r['axis']:r['angle']}
  triangles[part]=helper['model_triangles']({part:parent},tex)
 def rotation(angles):
  x,y,z=np.radians(angles)
  rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
  ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
  rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
  return rx@ry@rz
 def posed(phase,i,parts=PARTS,grip='native',hand=FP[0]):
  result=[]
  for part in parts:
   d=json.loads(output[A/f'models/{KEY}_{phase}_{i:02}_{part}_{grip}.json'])['display'][hand]
   s=np.array(d['scale']);r=rotation(d['rotation']);t=np.array(d['translation'])
   if max(s)==0:continue
   for ps,uv,texture,n in triangles[part]:
    result.append(((np.asarray(ps)-8)*s@r.T+t,uv,texture,r@n))
  return result
 def raster(ts,cam,w,h,extent=None):
  if extent is None:extent=helper['frame'](np.concatenate([x[0] for x in ts]),cam,w,h)
  return helper['render'](ts,cam,extent,(w,h))[0]
 cams=([1,.35,-.6],[-1,-.4,.5],[.65,-.7,1])
 sheet=Image.new('RGB',(1600,1610),'#111925');draw=ImageDraw.Draw(sheet)
 draw.text((12,10),'W178 FIRST IN, LAST OUT | independent emitted-JSON reconstruction | OFFLINE: no hands / no native claim',fill='white')
 selections=(('initial',0),('initial',20),('loop',11),('return',20))
 for row,cam in enumerate(cams):
  groups=[posed(phase,i) for phase,i in selections]
  extent=helper['frame'](np.concatenate([x[0] for ts in groups for x in ts]),cam,400,290)
  for col,((phase,i),ts) in enumerate(zip(selections,groups)):
   y=50+row*325;sheet.paste(raster(ts,cam,400,290,extent),(col*400,y))
   draw.text((col*400+10,y-16),f'{phase} {i/20:.2f} | oblique {row+1}',fill='white')
 draw.text((12,1020),'97 exact canonical body + 12 connected shell volumes = 109 maximum. initial1 = loop0 = loop1 = return0 held body; shell hidden at seams.',fill='white')
 for col,cam in enumerate(cams):
  sheet.paste(raster(posed('loop',11,('shell',)),cam,530,245),(col*530,1080))
  draw.text((col*530+10,1058),'Shell close-up: case + overlapping steel head/rim',fill='white')
 for col,(phase,i) in enumerate((('loop',3),('loop',11),('loop',16),('return',0))):
  ts=posed(phase,i)
  # Framing uses a fixed receiver box in emitted HIP/held coordinates, never
  # the shell centroid, so actual insertion travel remains visible.
  cam=[1,-.65,.4]
  # All three views show the same world-space receiver/guard neighborhood.
  source_points=[]
  d=json.loads(output[A/f'models/{KEY}_loop_00_body_native.json'])['display'][FP[0]]
  rr=rotation(d['rotation']);ss=np.array(d['scale']);tt=np.array(d['translation'])
  for point in ([5.8,7.3,2],[9.2,11.6,8.5]):source_points.append((np.array(point)-8)*ss@rr.T+tt)
  extent=helper['frame'](np.array(source_points),cam,400,230)
  sheet.paste(raster(ts,cam,400,230,extent),(col*400,1350))
  draw.text((col*400+10,1332),f'{phase} {i/20:.2f} | below receiver / seat / seam',fill='white')
 draw.text((12,1590),'Same-size visibility ends inside the existing tube. Hidden shell angles/path authored from occluded contact. Canonical geometry, atlas and mechanics unchanged.',fill='white')
 story=Image.new('RGB',(1600,1630),'#111925');draw=ImageDraw.Draw(story)
 draw.text((12,10),'ACTUAL esbeekay 5IZfs2bjrYY / AUTHORED FIRST IN, LAST OUT | original reference PNG above; independent offline model below',fill='white')
 for i,f in enumerate(ref['frames']):
  x=i%4*400;y=40+i//4*520
  im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));story.paste(im,(x,y))
  draw.text((x+8,y+228),f"ACTUAL {f['timestampSeconds']:.3f}s / frame {f['sourceFrameIndex']}",fill='white')
  phase=f['authoredPhase'];j=round(f['authoredProgress']*20)
  story.paste(raster(posed(phase,j),[1,-.2,.5],400,225),(x,y+258))
  draw.text((x+8,y+487),('IDENTITY / HIP' if f['phase']=='identity' else f'AUTHORED {phase} {j/20:.2f}'),fill='white')
 draw.text((12,1605),'Actual frame pixels preserved in reference00..11. Camera pan / hand occlusion / flashes are not extracted motion; no hands or new third-person reload.',fill='white')
 return png(sheet),png(story)

def generate():
 for path,digest in PINS.items():
  if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical input drift: '+path)
 source=json.loads((ROOT/SOURCE).read_bytes());twohand=json.loads((ROOT/TWOHAND).read_bytes())['display']
 canonical=json.loads((ROOT/ITEM).read_bytes());ref=json.loads((ROOT/ART/'motion-reference.json').read_bytes())
 rules=json.loads((ROOT/'src/main/resources/weapon_surface_w123/manifest.json').read_bytes())['targets']
 rule=next(r for r in rules if r['path']=='assets/destiny/models/weapon/shotgun/first_in_last_out.json')
 if rule['replacement']!=str(SOURCE).removeprefix('src/main/resources/') or rule['replacementSha256']!=PINS[str(SOURCE)]:raise ValueError('Effective canonical surface mapping drift')
 if len(source['elements'])!=97:raise ValueError('Canonical element count drift')
 if len(ref['frames'])!=12 or not ref['inspectedActualFrames']:raise ValueError('Actual reference missing')
 for f in ref['frames']:
  if sha((ROOT/f['path']).read_bytes())!=f['sha256']:raise ValueError('Reference frame drift')
 output={}
 def emit(p,value):output[p]=encode(value)
 emit(A/f'models/{KEY}_body.json',copy.deepcopy(source))
 emit(A/f'models/{KEY}_shell.json',shell_geometry(source))
 entries=[]
 for phase_index,phase in enumerate(PHASES):
  for i in range(21):
   for part in PARTS:
    for grip in GRIPS:
     emit(A/f'models/{KEY}_{phase}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],twohand,phase,i/20,part,grip)))
   def composite(grip):return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{phase}_{i:02}_{part}_{grip}') for part in PARTS])
   entries.append(dict(threshold=phase_index*2+i/20,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
 range_model=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=4,entries=entries,fallback=copy.deepcopy(canonical['model']))
 # ADS and inspect stay canonical even if float4 is still present at a transition.
 modes=dict(type='minecraft:select',property='minecraft:custom_model_data',index=0,cases=[dict(when=mode,model=copy.deepcopy(canonical['model'])) for mode in ('ads','inspect')],fallback=range_model)
 wrapper=copy.deepcopy(canonical)
 wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=modes)],fallback=copy.deepcopy(canonical['model']))
 emit(A/f'items/{KEY}.json',wrapper)
 comparison,story=previews(output,ref);output[ART/'comparison.png']=comparison;output[ART/'storyboard.png']=story
 inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,SELF,ART/'motion-reference.json',Path('scripts/generate_surface_w123_hammerhead.py')]
 emit(ART/'manifest.json',dict(stage='W178',weapon='first_in_last_out',itemModel='destiny:'+KEY,ownedFiles=274,generatedFiles=258,packFiles=255,parents=2,displayChildren=252,phases=list(PHASES),framesPerPhase=21,progressFloatIndex=4,gripFlagIndex=0,firstPersonContexts=list(FP),sourceGeometryPath=str(SOURCE),sourceElements=97,bodyElements=97,shellElements=12,maxAssembledElements=109,elementLimit=1000,bodyGeometryAndUVPreserved=True,bodyElementsAndUVSha256=sha(encode(source['elements'])),addedHiddenElements=12,newTextures=0,hiddenGeometry='One model-only cartridge, twelve overlapping solid bars forming three connected octagonal case/head/rim sections. Reuses atlas texels from canonical graphite magazine_tube_0 index34 and steel silver_sleeve_0 index58; uniform existing texels avoid end-face overlap noise. Never visible at HIP, phase seams, non-FP, ADS or inspect. No detached cap.',shellAnchor=SHELL_ANCHOR,gripPivot=GRIP,keyframes=KEYS,visibility=VISIBLE,bodyHipEndpoints=[['initial',0],['return',20]],heldSeams=[['initial',20],['loop',0],['loop',20],['return',0]],shellVisibilityPolicy='Full size during approach/contact and insertion; no whole-mag fill. Hidden when in tube and at all phase seams; no size-fade in open air.',returnTicks=6,returnBlocksGameplay=False,ammoTransferPolicy='Existing mechanical WeaponCycle one-shell transfer is authoritative. initial raises once and inserts one; subsequent loop inserts one from same held pose; return is cosmetic only.',rotationConvention='Rigid Rx Ry Rz about authored source grip; rotate source-local cartridge offset and compensate anchor. Apply .85 scale once; carry native to authored twohand frame rigidly. No additive Euler.',fallback='Exact canonical item model graph for all non-FP and ADS/inspect even during progress; negative inactive float4 selects exact canonical graph.',reference=ref['url'],actualReferenceFrames=12,identityFrames=1,reloadFrames=11,referenceConfidence=ref['referenceConfidence'],motionAuthorship=ref['authorship'],nativeGameplayVerified=False,handIK=False,extractedBones=False,thirdPersonReloadClaim=False,mechanicsOrAudioChanged=False,integration=dict(masterOwnsRuntime=True,workerRuntimeEdited=False,requiredMasterModel='destiny:'+KEY,requiredContract='WeaponInsertPresentation supports first_in_last_out and model(entry); accepted INSERT initial0..1 / loop2..3 / cosmetic return4..5 on float4, flag0 grip, unchanged .001 collision-offset policy. No model-authored gameplay delay.',nativeQueue=['Both FP hands, native/twohand grips, initial from HIP, multiple successful one-shell inserts held without repeated lift; end/interruption/cancel and cosmetic return.','ADS/inspect and equip/swap/death/disconnect restores; float collision ownership; third-person observer plus GUI/ground/head/fixed canonical.','Brief 10-20 displayed weapons for obvious defects; actual server GT, listening and native visual performance belong to master.']),comparisonMethod='Independent reconstruction of emitted parent elements + child display transforms; three obliques for HIP/held/insert/return, three shell closeups and underside sequence. Storyboard pairs all twelve actual full frames with authored offline samples.',limitations=ref['limitations'],canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
 if set(output)!=expected_output_paths():raise ValueError('Generated path contract drift')
 return output

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args();output=generate()
 manifest=Path('/private/tmp/w178-manifest.json')
 if manifest.exists():
  owned=set(next(f['owned_paths'] for f in json.loads(manifest.read_bytes())['features'] if f['name']=='w178-first-in-last-out-insert'))
  if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
 for p,b in output.items():
  target=ROOT/p
  if args.verify:
   if not target.is_file() or target.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
  else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
 print(('Verified' if args.verify else 'Generated')+' 258 deterministic outputs; 255 pack assets; 97 canonical body + 12 hidden shell = 109 maximum; one-shell held insert phases')
if __name__=='__main__':main()
