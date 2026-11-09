#!/usr/bin/env python3
"""W350 power exotics: semantic adjoining blocks and explicitly authored reloads.

Source .blend inspection is performed separately by power_source_evaluate.py.
No source meshes are converted. Run: power.py build|render|check [weapon|all].
"""
import copy, hashlib, importlib.util, json, math, shutil, struct, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
A=ROOT/'src/main/resources/assets/destiny'
ART=ROOT/'art/weapons/w350'
SOURCES=Path('/tmp/exotic-expansion-20261109/sources')
BLENDER='/Applications/Blender.app/Contents/MacOS/Blender'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
kit=module('power_kit',ROOT/'scripts/art/w325/kit.py')
old=module('power_math',ROOT/'scripts/generate_reload_w218_bad_omens.py')
IDS=['gjallarhorn','whisper_of_the_worm','tractor_cannon']
FILES=dict(zip(IDS,['17VVJjaL6LdACgtNha91ucAVfwXf_yzXU','1U2_omWmiBtfpiao1igYTJ6N3AsNgBYXc','1-GjkVvpkwhYVU76LlLuUoXympWc0wwJK']))
FP=('firstperson_righthand','firstperson_lefthand')
COMMON={'dark':(20,24,28),'steel':(88,99,107),'silver':(173,181,184),'gold':(179,143,67),'ivory':(222,218,197),'rubber':(32,34,36),'red':(149,42,39),'glow':(163,216,231)}
PALETTES={
 'gjallarhorn':{**COMMON,'shell':(213,207,180),'trim':(182,141,56)},
 'whisper_of_the_worm':{**COMMON,'shell':(26,36,35),'trim':(193,220,216),'bone':(66,83,83)},
 'tractor_cannon':{**COMMON,'shell':(218,222,215),'trim':(106,115,117),'yellow':(113,141,180)}
}

class Shape:
 def __init__(self):self.e=[];self.roles={}
 def box(self,n,x0,x1,y0,y1,z0,z1,m='shell',part='body'):
  assert x1>x0 and y1>y0 and z1>z0,(n,x0,x1,y0,y1,z0,z1)
  self.e.append({'name':n,'from':[x0,y0,z0],'to':[x1,y1,z1],'part':part});self.roles[n]=m
 def block(self,n,w,y0,y1,z0,z1,m='shell',b=.15,part='body'):
  b=min(b,w*.2,(y1-y0)*.22);l=8-w/2;r=8+w/2
  self.box(n+'_core',l+b,r-b,y0,y1,z0,z1,m,part)
  self.box(n+'_left',l,l+b,y0+b,y1-b,z0,z1,m,part)
  self.box(n+'_right',r-b,r,y0+b,y1-b,z0,z1,m,part)
 def ring(self,n,w,h,y,z0,z1,m='steel',wall=.24,part='body'):
  l,r,b,t=8-w/2,8+w/2,y-h/2,y+h/2;c=max(wall*1.4,min(w,h)*.18)
  # A twelve-block connected hollow octagonal cross section; true central bore.
  self.box(n+'_top',l+c,r-c,t-wall,t,z0,z1,m,part)
  self.box(n+'_bottom',l+c,r-c,b,b+wall,z0,z1,m,part)
  self.box(n+'_left',l,l+wall,b+c,t-c,z0,z1,m,part)
  self.box(n+'_right',r-wall,r,b+c,t-c,z0,z1,m,part)
  for sx in [-1,1]:
   for sy in [-1,1]:
    xx=l if sx<0 else r;yy=b if sy<0 else t
    xa,xb=(xx,xx+c-wall) if sx<0 else (xx-c+wall,xx)
    ya,yb=(yy+c-wall,yy+c) if sy<0 else (yy-c,yy-c+wall)
    self.box(n+f'_corner{sx}{sy}_a',xa,xb,ya,yb,z0,z1,m,part)
    xa,xb=(xx+c-wall,xx+c) if sx<0 else (xx-c,xx-c+wall)
    ya,yb=(yy,yy+c) if sy<0 else (yy-c,yy)
    self.box(n+f'_corner{sx}{sy}_b',xa,xb,ya,yb,z0,z1,m,part)
 def panel(self,n,x,y0,y1,z0,z1,m='trim',d=.12):
  for side in [-1,1]:
   a=8+side*x;self.box(n+str(side),a-d if side<0 else a,a if side<0 else a+d,y0,y1,z0,z1,m)
 def grip(self,n,z,y,w=1.25,h=3,lean=.8):
  for i in range(4):self.block(n+str(i),w,y+i*h/4,y+(i+1)*h/4,z-lean*i/4,z+1.25-lean*i/4,'rubber',.12)
 def guard(self,z0,z1,y0,y1,m='gold'):
  self.box('trigger_guard_front',7.83,8.17,y0,y1,z0,z0+.22,m)
  self.box('trigger_guard_floor',7.83,8.17,y0,y0+.22,z0+.22,z1,m)
  self.box('trigger',7.9,8.1,y1-.7,y1,z1-.45,z1-.22,'dark')

def gjallarhorn():
 s=Shape()
 # The thick forward chamber, wolf relief crown and slim long aft tube define Gjallarhorn.
 s.ring('front_lip',3.35,3.35,11.4,-10.5,-9.85,'gold',.36)
 s.ring('forward_chamber',3.05,3.05,11.4,-9.85,-2.8,'ivory',.35)
 s.ring('chamber_band',3.25,3.25,11.4,-2.8,-2.35,'gold',.38)
 s.ring('aft_open_tube',1.75,1.75,11.4,2.4,18.7,'ivory',.23)
 s.ring('aft_rim',2.05,2.05,11.4,18.7,19.25,'gold',.25)
 s.block('chamber_bridge',2.8,10.0,12.8,-2.35,2.4,'gold')
 for i,z in enumerate([-.8,.1,1.0]):s.block('chamber_flute'+str(i),3.05,10.1,12.7,z,z+.24,'gold')
 # Upper hinged cover is a separate moving part, source bones MagCover_1/2.
 for i,(z0,z1,y0,y1,w) in enumerate([(-8.4,-6.8,13.0,14.05,2.2),(-6.8,-3.7,12.94,14.55,2.65),(-3.7,-.2,12.94,14.48,2.6),(-.2,1.7,12.95,13.85,2.2)]):
  s.block('cover_crown'+str(i),w,y0,y1,z0,z1,'gold',part='cover')
 # Relief is real low, adjoining wolf head volumes; mane filigree is face UV.
 for side in [-1,1]:
  x=8+side*1.36
  for i,(z0,z1,y0,y1) in enumerate([(-8.4,-7.85,13.35,13.7),(-7.85,-7.0,13.35,14.03),(-7.,-6.45,13.45,14.35),(-6.45,-5.85,13.65,14.35)]):
   s.box('wolf_relief'+str(side)+'_'+str(i),x-.18,x+.18,y0,y1,z0,z1,'gold','cover')
  s.box('wolf_eye'+str(side),x-.19,x+.19,13.9,14.02,-7.1,-6.9,'dark','cover')
 s.block('lower_cradle',2.0,8.65,9.95,-7.7,-1.1,'ivory')
 s.block('grip_bridge',1.4,8.8,9.45,-1.1,5.6,'gold')
 s.grip('trigger_grip',3.4,5.5,1.3,3.3,1.15)
 s.guard(-.8,2.8,7.7,9.1)
 s.block('stock_upper',1.25,9.15,9.8,5.6,8.0,'ivory')
 s.block('stock_end',1.25,7.8,9.8,8.0,8.6,'ivory')
 for i in range(3):s.block('stock_lower'+str(i),1.15,5.5+i*.7,6.75+i*.7,4.65+i*(3.35/3),4.65+(i+1)*(3.35/3),'ivory')
 s.grip('front_support',-6.4,4.7,1.,3.9,-1.8)
 # Source Magazine is a chamber cartridge; it enters through the lifted crown.
 s.block('mag_rocket',1.8,10.6,12.2,-3.2,1.7,'steel',part='magazine')
 s.block('mag_rocket_nose',1.3,10.85,11.95,-4.,-3.2,'gold',part='magazine')
 return s

def whisper_of_the_worm():
 s=Shape()
 s.ring('muzzle_bore',1.25,1.25,11.1,-15.2,-13.2,'bone',.23)
 s.block('long_barrel',.78,10.71,11.49,-13.2,-1.5,'steel',.10)
 s.block('barrel_spine',.42,11.49,11.68,-12.8,-2.2,'trim',.08)
 for i,(z0,z1,y0,y1,w) in enumerate([(-3.,-.8,10.,12.,1.45),(-.8,2.5,9.8,12.25,1.9),(2.5,6.4,9.8,12.4,2.15),(6.4,10.,10.0,12.15,1.95)]):s.block('taken_receiver'+str(i),w,y0,y1,z0,z1,'shell')
 s.block('stock_spine',1.55,11.15,12.0,10.,17.2,'shell')
 s.block('stock_butt',1.65,8.0,12.0,17.2,18.0,'bone')
 s.block('stock_pad',1.7,7.8,12.1,18.0,18.4,'dark')
 for i in range(4):s.block('stock_lower'+str(i),1.15,6.65+i*.38,7.15+i*.38,11.2+i*1.5,12.7+i*1.5,'bone')
 s.grip('pistol_grip',10.8,6.0,1.2,4.1,1.25)
 s.guard(7.0,9.7,8.5,10.1,'bone')
 s.block('mag_upper',1.4,7.9,9.8,3.8,6.4,'shell',part='magazine')
 s.block('mag_lower',1.55,5.8,7.9,3.8,6.2,'bone',part='magazine')
 s.block('mag_foot',1.65,5.55,5.8,3.7,6.3,'dark',part='magazine')
 # Scope is physically open. Rear and objective lens surfaces are inset well inside rings.
 s.block('scope_foot',.7,12.4,13.0,4.6,7.2,'dark')
 s.ring('scope_body',1.2,1.2,13.75,3.1,10.6,'bone',.18)
 s.ring('scope_objective',1.85,1.85,13.75,1.4,3.1,'shell',.22)
 s.ring('scope_ocular',1.5,1.5,13.75,10.6,11.2,'shell',.20)
 s.block('scope_turret',.8,14.35,14.9,6.6,7.4,'bone')
 # Four skeletal muzzle jaws create gaps around the inner barrel; source thorn clusters simplified to solids.
 for side in [-1,1]:
  for i,(z0,z1,yy,ww) in enumerate([(-15.9,-15.1,11.65,.28),(-15.1,-13.7,11.7,.48),(-13.7,-12.2,11.65,.4),(-12.2,-10.8,11.5,.25)]):
   x=8+side*(.50+i*.035);s.box('worm_jaw'+str(side)+str(i),x-ww/2,x+ww/2,11.43,yy+.3,z0,z1,'bone')
  for i,z in enumerate([-14.8,-13.3,-11.6,-3.1,-1.5,.2]):
   x=8+side*(.48 if z<-5 else .75)
   s.box('thorn_root'+str(side)+str(i),x-.22,x+.22,11.43,12.0,z,z+.55,'bone')
   s.box('thorn_tip'+str(side)+str(i),x-.10,x+.10,12.0,12.35,z+.18,z+.55,'trim')
 s.panel('taken_fracture',1.08,10.2,11.8,2.5,6.3,'shell',.04)
 return s

def tractor_cannon():
 s=Shape()
 # Broad cylindrical laboratory housing and three open claws, narrow hollow grip frame.
 s.ring('front_lip',5.0,5.0,10.0,-6.7,-6.1,'silver',.42)
 s.ring('emitter_throat',4.4,4.4,10.0,-6.1,-3.5,'dark',.40)
 s.block('emitter_core',2.5,8.75,11.25,-3.7,-3.35,'steel')
 s.block('drum_front',5.45,7.35,12.65,-3.5,-1.3,'shell',.65)
 s.block('drum_middle',5.7,7.25,12.75,-1.3,1.4,'shell',.7)
 s.block('drum_rear',5.1,7.6,12.4,1.4,3.3,'shell',.6)
 s.block('rear_mechanism',3.0,8.4,11.7,3.3,4.2,'steel',.3)
 # Each claw has touching root, knuckle and tapered tip blocks; the central opening stays vacant.
 for side in [-1,1]:
  x=8+side*2.2
  s.box('claw_root'+str(side),x-.32,x+.32,10.6,11.3,-6.9,-4.9,'steel')
  s.box('claw_joint'+str(side),x-.42,x+.42,11.3,11.9,-7.0,-6.0,'yellow')
  s.box('claw_blade'+str(side),x-.38,x+.38,11.9,12.45,-8.5,-6.0,'shell')
  s.box('claw_tip'+str(side),x-.19,x+.19,12.45,12.7,-8.8,-7.5,'steel')
 s.block('claw_lower_root',.65,6.8,8.2,-6.9,-4.9,'steel')
 s.block('claw_lower_joint',.9,6.3,6.8,-7.0,-6.,'yellow')
 s.block('claw_lower_blade',.75,5.7,6.3,-8.6,-6.,'shell')
 s.block('claw_lower_tip',.38,5.45,5.7,-8.9,-7.6,'steel')
 # Rectangular source handle void remains open, with upper grip and lower return rail.
 s.block('handle_upper',1.6,11.0,12.2,4.2,11.8,'shell')
 s.block('handle_rear',1.8,8.15,12.2,11.8,12.6,'shell')
 s.block('handle_lower',1.4,7.7,8.4,4.2,11.8,'dark')
 s.block('handle_pad',1.85,8.15,12.2,12.6,13.0,'rubber')
 s.panel('handle_insert',.82,11.15,11.85,5.4,10.9,'rubber',.08)
 s.block('top_loader_rail',2.7,12.65,13.0,-1.5,2.8,'steel')
 s.block('mag_cell',2.2,12.9,13.7,-1.0,2.3,'dark',part='magazine')
 s.block('mag_cell_cap',2.4,13.7,14.,-.9,2.2,'yellow',part='magazine')
 # Twin vacuum pipes are adjoining stepped elbows, not crossed rotated plates.
 for side in [-1,1]:
  x=8+side*1.7
  for i in range(3):s.box('vacuum_pipe'+str(side)+str(i),x-.32,x+.32,12.3+i*.48,12.78+i*.48,-.9+i*.55,-.1+i*.55,'steel')
  s.box('vacuum_pipe_mouth'+str(side),x-.4,x+.4,13.74,13.97,.75,1.75,'dark')
  s.box('drum_hinge'+str(side),x-.4,x+.4,7.4,8.2,2.7,3.5,'silver')
  s.box('cable_rail'+str(side),x-.12,x+.12,7.05,7.28,-2.9,2.5,'dark')
 s.panel('caution_panel',2.86,9.0,11.35,-1.1,1.15,'yellow',.05)
 s.panel('side_label',2.58,8.2,9.3,1.65,2.95,'dark',.05)
 return s

BUILDERS=dict(zip(IDS,[gjallarhorn,whisper_of_the_worm,tractor_cannon]))
def enc(v):return (json.dumps(v,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(enc(v))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def paint(w,n,role,fn,img,e):
 """Restricted-palette face motifs. Flat base, bevel line; no noisy rip projection."""
 d=ImageDraw.Draw(img);W,H=img.size;palette=PALETTES[w];col=palette[role]
 hi=tuple(min(255,c+19) for c in col)+(255,);lo=tuple(max(0,c-20) for c in col)+(255,)
 if W>3 and H>3 and role not in ('dark','glow'):
  d.line((0,0,W-1,0),fill=hi);d.line((0,0,0,H-1),fill=hi)
  d.line((0,H-1,W-1,H-1),fill=lo);d.line((W-1,0,W-1,H-1),fill=lo)
 if fn not in ('east','west'):return
 if w=='gjallarhorn' and n.startswith(('cover_crown','forward_chamber','stock_')) and W>10 and H>8:
  ink=palette['gold']+(255,)
  # Repeating interlocked scroll runs on the cover, narrow gilded edges on ivory tube.
  if n.startswith('cover'):
   ink=palette['ivory']+(255,)
   for x in range(3,W-3,12):d.line([(x,H//2),(x+3,H//2-2),(x+6,H//2),(x+3,H//2+2),(x,H//2)],fill=ink,width=1)
  else:d.line((2,2,W-3,2),fill=ink);d.line((2,H-3,W-3,H-3),fill=ink)
 if w=='whisper_of_the_worm' and n.startswith(('taken_receiver','stock_','mag_','taken_fracture')) and W>8 and H>6:
  # Authored Taken white fissures derived from the base-finish identity, not random source alpha planes.
  p=[(int(W*t),int(H*(.48+.12*math.sin(t*11+len(n))))) for t in [0,.2,.38,.54,.72,1]]
  d.line(p,fill=palette['trim']+(255,),width=1)
  if H>14:d.line([(W//3,H//2),(W//3+2,H//3),(W//2,H//4)],fill=palette['bone']+(255,),width=1)
 if w=='tractor_cannon' and n.startswith('caution_panel'):
  for yy in range(3,H-2,4):d.line((3,yy,W-4,yy),fill=palette['dark']+(255,),width=1)
 if role=='rubber' and W>6 and H>6:
  for yy in range(3,H-2,4):d.line((2,yy,W-3,yy),fill=lo)

def bake(w,s):
 """Per-face UV packing using the established W325 frame and 1px gutters."""
 T=6;A_SIZE=512;faces=[]
 for e in s.e:
  for fn in kit.FACE_AXES:
   o,u,v=kit.face_frame(e,fn);W=max(2,round(math.dist((0,0,0),u)*T));H=max(2,round(math.dist((0,0,0),v)*T))
   role=s.roles[e['name']];img=Image.new('RGBA',(W,H),PALETTES[w][role]+(255,));paint(w,e['name'],role,fn,img,e)
   faces.append((e['name'],fn,img))
 faces.sort(key=lambda a:(-a[2].height,-a[2].width,a[0],a[1]));x=y=row=0;packed=[]
 for n,fn,img in faces:
  W,H=img.size
  if x+W+2>A_SIZE:y+=row;x=row=0
  packed.append((n,fn,img,x,y));x+=W+2;row=max(row,H+2)
 height=16
 while height<y+row:height*=2
 assert height<=1024,(w,height)
 atlas=Image.new('RGBA',(A_SIZE,height));uv={}
 for n,fn,img,x,y in packed:
  W,H=img.size;atlas.paste(img.resize((W+2,H+2),Image.Resampling.NEAREST),(x,y));atlas.paste(img,(x+1,y+1))
  uv.setdefault(n,{})[fn]={'uv':[(x+1)/A_SIZE*16,(y+1)/height*16,(x+1+W)/A_SIZE*16,(y+1+H)/height*16],'texture':'#0'}
 parts={p:[] for p in sorted(set(e['part'] for e in s.e))}
 for e in s.e:
  q={k:v for k,v in e.items() if k!='part'};q['faces']=uv[e['name']];parts[e['part']].append(q)
 p=A/f'textures/item/weapon/w350/{w}.png';p.parent.mkdir(parents=True,exist_ok=True);atlas.save(p,optimize=True)
 skin={'texture_size':list(atlas.size),'parts':parts};write(ART/w/'skin.json',skin)
 hp=A/f'textures/item/hud/w350/ammo_{w}.png';hp.parent.mkdir(parents=True,exist_ok=True);kit.hud_icon(s.e,hp,lambda n:n.startswith('mag_rocket'))
 return skin

CONFIG={
 'gjallarhorn':{'family':'rocket_launcher','donor':'bad_omens','right':[8,7.6,3.5],'left':[8,6.4,-5.8],'loading':[8,11.4,-1.4],'pivot':[8,7.6,3.5], 'moving_pivot':[8,12.94,1.7], 'mag_axis':[0,6.5,0]},
 'whisper_of_the_worm':{'family':'sniper_rifle','donor':'bite_of_the_fox','right':[8,8.1,10.8],'left':[8,9.0,-.7],'loading':[8,7.5,5.0],'pivot':[8,8.1,10.8],'moving_pivot':[8,9.8,5.0], 'mag_axis':[-2,-6,1]},
 'tractor_cannon':{'family':'shotgun','donor':'ikelos_sg_v1_0_1','right':[8,10.8,9.2],'left':[8,7.4,-.2],'loading':[8,13.5,.5],'pivot':[8,10.8,9.2],'moving_pivot':[8,12.9,.5], 'mag_axis':[-2,6,2]}
}
KEYS={
 'gjallarhorn':[(0,(0,0,0),(0,0,0),0,0),(.12,(-10,10,-12),(0,-.3,0),0,0),(.26,(-18,13,-28),(-.4,-.7,0),0,62),(.40,(-18,13,-28),(-.4,-.7,0),1,62),(.55,(-18,13,-28),(-.4,-.7,0),1,62),(.70,(-18,13,-28),(-.4,-.7,0),0,62),(.81,(-8,5,-13),(0,-.3,0),0,0),(1,(0,0,0),(0,0,0),0,0)],
 'whisper_of_the_worm':[(0,(0,0,0),(0,0,0),0,0),(.13,(-9,8,-23),(-.3,-.5,0),0,0),(.27,(-12,11,-28),(-.3,-.5,0),0,0),(.41,(-12,11,-28),(-.3,-.5,0),1,0),(.56,(-12,11,-28),(-.3,-.5,0),1,0),(.72,(-12,11,-28),(-.3,-.5,0),0,0),(.84,(-6,6,-14),(0,-.2,0),0,0),(1,(0,0,0),(0,0,0),0,0)],
 'tractor_cannon':[(0,(0,0,0),(0,0,0),0,0),(.15,(-20,9,-17),(-.3,-.6,0),0,0),(.30,(-25,12,-22),(-.3,-.8,0),0,0),(.44,(-25,12,-22),(-.3,-.8,0),1,0),(.57,(-25,12,-22),(-.3,-.8,0),1,0),(.72,(-25,12,-22),(-.3,-.8,0),0,0),(.85,(-9,4,-8),(0,-.2,0),0,0),(1,(0,0,0),(0,0,0),0,0)]
}
def curve(w,p):
 keys=KEYS[w];times=[r[0] for r in keys]
 if p>=1:return keys[-1][1:]
 i=next(i for i in range(len(keys)-1) if p<=times[i+1]);h=times[i+1]-times[i];t=(p-times[i])/h
 def one(vals):
  slopes=old.tangents(times,vals)
  return (2*t**3-3*t**2+1)*vals[i]+(t**3-2*t*t+t)*h*slopes[i]+(-2*t**3+3*t*t)*vals[i+1]+(t**3-t*t)*h*slopes[i+1]
 return ([one([r[1][a] for r in keys]) for a in range(3)],[one([r[2][a] for r in keys]) for a in range(3)],one([r[3] for r in keys]),one([r[4] for r in keys]))
def modelref(k):return {'type':'minecraft:model','model':'destiny:'+k}
def composite(nodes):return {'type':'minecraft:composite','models':nodes}
def f32(x):return struct.unpack('!f',struct.pack('!f',x))[0]

def transform_display(display,rot,pivot,shift,part_offset=(0,0,0),part_rot=(0,0,0),part_pivot=(8,8,8)):
 out=copy.deepcopy(display);R=old.xyz(rot);Q=old.xyz(part_rot);h=old.sub(pivot,[8,8,8]);a=old.sub(part_pivot,[8,8,8])
 local=old.sub(old.add(h,old.vec(R,old.add(old.sub(a,h),part_offset))),old.vec(old.mul(R,Q),a))
 for ctx in FP:
  d=display[ctx];B=old.xyz(d['rotation']);scale=d['scale'][0]
  out[ctx]={'rotation':old.euler(old.mul(B,old.mul(R,Q))), 'translation':old.add(old.add(d['translation'],shift),old.vec(B,[scale*v for v in local])), 'scale':d['scale']}
 return out

def arm_graph(w,label,side,display,contact,rotation):
 # W204 player-skin segments remain shared. Only weapon-owned display children are emitted.
 refs={};R=old.xyz(rotation)
 for variant in ['classic','slim']:
  d={}
  for ctx in FP:
   b=display[ctx];B=old.xyz(b['rotation']);scale=b['scale'][0]
   d[ctx]={'rotation':old.euler(old.mul(B,R)), 'translation':old.add(b['translation'],old.vec(B,[(contact[i]-8)*scale for i in range(3)])), 'scale':b['scale']}
  key=f'weapon_w350/{w}/hands/{label}_{side}_{variant}'
  write(A/f'models/{key}.json',{'parent':f'destiny:skin_arm_w204/{side}_{variant}','display':d})
  refs[variant]={'type':'minecraft:model','model':'destiny:'+key,'tints':[{'type':'minecraft:custom_model_data','index':(64 if side=='right' else 192)+i,'default':0xFFFFFF} for i in range(112 if variant=='classic' else 96)]}
 return {'type':'minecraft:condition','property':'minecraft:custom_model_data','index':8,'on_false':{'type':'minecraft:empty'},'on_true':{'type':'minecraft:condition','property':'minecraft:custom_model_data','index':9,'on_true':refs['slim'],'on_false':refs['classic']}}

def ads_translation(w,scale):
 # Native camera hand base is(+.56,-.52,-.72)m. Center a source-measured
 # clear top sightline, .20 model units above the crown/upper handle.
 # The old scoped Whisper route is intentionally preserved.
 sight_y={'gjallarhorn':11.4+(297-170)*29.75/1042+.20,
          'tractor_cannon':10.0+(350-135)*21.9/1042+.20}.get(w)
 if sight_y is None:return [-2.4,-2.3,-5.3]
 return [-8.96,8.32-scale*(sight_y-8),-5.3]

def native(w,skin):
 c=CONFIG[w];family=c['family'];donor=c['donor'];base=json.loads((A/f'models/weapon/{family}/{donor}.json').read_text());display=copy.deepcopy(base['display'])
 # Source-proportioned exotics are framed independently; body remains fully 3D and unchanged across views.
 for ctx in FP:
  display[ctx]['rotation']=[0,12 if ctx.endswith('righthand') else -12,0]
  display[ctx]['translation']=[0,-.4,-3.0];display[ctx]['scale']=[.72]*3 if w=='tractor_cannon' else [.78]*3
 tex={'0':f'destiny:item/weapon/w350/{w}','particle':f'destiny:item/weapon/w350/{w}'}
 full=sum((es for p,es in skin['parts'].items() if not (w=='gjallarhorn' and p=='magazine')),[])
 for part,es in {**skin['parts'],'full':full}.items():
  part_display=copy.deepcopy(display)
  if part=='full':
   # Root item falls back directly to full outside1P; match W327 TWO_HAND carry.
   carry=json.loads((A/f'models/weapon/{family}/{donor}_twohand.json').read_text())['display']
   for ctx in ('thirdperson_righthand','thirdperson_lefthand'):part_display[ctx]=copy.deepcopy(carry[ctx])
  write(A/f'models/weapon_w350/{w}/{part}.json',{'credit':'W350 authored semantic closed solids; native acceptance pending','textures':tex,'display':part_display,'elements':es})
 def pose(label,disp,parts,load=None):
  nodes=[]
  for part,dd in parts.items():
   key=f'weapon_w350/{w}/{label}_{part}';write(A/f'models/{key}.json',{'parent':f'destiny:weapon_w350/{w}/{part}','display':dd});nodes.append(modelref(key))
  nodes.append(arm_graph(w,label,'right',disp,c['right'],[-14,0,0]))
  if load is None:nodes.append(arm_graph(w,label,'left',disp,c['left'],[0,80,-80]))
  else:nodes.append(arm_graph(w,label,'left',load['display'],load['position'],load['rotation']))
  return composite(nodes)
 hip=pose('hip',display,{'full':display});states={}
 for state in ['ads','inspect']:
  ds=copy.deepcopy(display)
  for ctx in FP:
   ds[ctx]['rotation']=[0,0,0] if state=='ads' else [8,25,-12]
   ds[ctx]['translation']=ads_translation(w,display[ctx]['scale'][0]) if state=='ads' else [-1,-1,-4]
  states[state]=pose(state,ds,{'full':ds})
  write(A/f'items/weapon_sight_w350/{w}/{state}.json',{'model':states[state]})
 poses=[];entries=[]
 for i in range(61):
  p=i/60;rot,shift,mag,cover=curve(w,p);bd=transform_display(display,rot,c['pivot'],shift)
  md=transform_display(display,rot,c['pivot'],shift,[x*mag for x in c['mag_axis']]);parts={'body':bd,'magazine':md}
  if 'cover' in skin['parts']:parts['cover']=transform_display(display,rot,c['pivot'],shift,part_rot=[cover,0,0],part_pivot=c['moving_pivot'])
  if w=='gjallarhorn' and (p<.30 or p>.75):parts.pop('magazine')
  reach=min(1,max(0,(p-.12)/.15),max(0,(.88-p)/.16));reach=reach*reach*(3-2*reach)
  # Attach only through actual handling. Left wrist releases before carrier returns to rest.
  loadpos=[c['left'][a]*(1-reach)+c['loading'][a]*reach for a in range(3)]
  handdisp=md if .28<=p<=.73 else bd
  load={'display':handdisp,'position':loadpos,'rotation':[0,80*(1-reach),-80*(1-reach)]}
  node=hip if i in (0,60) else pose(f'reload_{i:02}',bd,parts,load)
  write(A/f'items/weapon_reload_w350/{w}/{i}.json',{'model':node})
  entries.append({'threshold':f32(p),'model':node})
  poses.append({'frame':i,'progress':p,'bodyRotation':rot,'bodyShift':shift,'magazineOffset':[x*mag for x in c['mag_axis']],'coverDegrees':cover,'rightContact':c['right'],'leftContact':loadpos,'handlingWeight':reach,'partsDisplay':parts})
 reload={'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data','index':1,'entries':entries,'fallback':hip}
 write(A/f'items/weapon_reload_w350/{w}.json',{'model':{'type':'minecraft:select','property':'minecraft:display_context','cases':[{'when':list(FP),'model':reload}],'fallback':modelref(f'weapon_w350/{w}/full')}})
 aim_entries=[]
 for i in range(21):
  t=i/20;t=t*t*(3-2*t);ds=copy.deepcopy(display)
  for ctx in FP:
   ds[ctx]['rotation']=[v*(1-t) for v in display[ctx]['rotation']]
   ds[ctx]['translation']=[v*(1-t)+target*t for v,target in zip(display[ctx]['translation'],ads_translation(w,display[ctx]['scale'][0]))]
  aim_entries.append({'threshold':f32(i/20),'model':pose(f'aim_{i:02}',ds,{'full':ds})})
 aim={'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data','index':3,'entries':aim_entries,'fallback':hip}
 write(A/f'items/weapon_aim_w350/{w}.json',{'model':{'type':'minecraft:select','property':'minecraft:display_context','cases':[{'when':list(FP),'model':aim}],'fallback':modelref(f'weapon_w350/{w}/full')}})
 select={'type':'minecraft:select','property':'minecraft:custom_model_data','index':0,'cases':[{'when':k,'model':v} for k,v in states.items()],'fallback':hip}
 root={'type':'minecraft:select','property':'minecraft:display_context','cases':[{'when':list(FP),'model':select}],'fallback':modelref(f'weapon_w350/{w}/full')}
 write(A/f'items/weapon/{w}.json',{'model':root})
 write(ART/w/'reload-poses.json',{'schemaVersion':1,'samples':61,'intervals':60,'interpolation':'PCHIP shared continuous derivatives; native item bank remains discrete','authorship':'Authored approximation; supplied weapon rig has no actions or player hand rig','keys':KEYS[w],'poses':poses})
 write(ART/w/'rig.json',{'schemaVersion':1,'sourceBones':json.loads((ART/w/'source-evaluation.json').read_text())['armatures'],'authoredContacts':c,'firstPersonArmParent':'skin_arm_w204','arms':'authored contact-aligned fingerless forearms; no source wrist/elbow animation claim','reloadActionSource':None,'runtime':{'rootItem':'destiny:weapon/'+w,'reloadItems':'destiny:weapon_reload_w350/'+w+'/{0..60}','reloadDispatcher':'destiny:weapon_reload_w350/'+w,'aimDispatcher':'destiny:weapon_aim_w350/'+w,'aimProgressFloatIndex':3,'aimSamples':21,'adsItem':'destiny:weapon_sight_w350/'+w+'/ads','inspectItem':'destiny:weapon_sight_w350/'+w+'/inspect','skinReadyFlag':8,'skinSlimFlag':9,'reloadProgressFloatIndex':1,'stateStringIndex':0}})

def build(w):
 out=ART/w;out.mkdir(parents=True,exist_ok=True)
 for name in ['source-evaluation.json','source_side.png','source_oblique.png','source_top.png']:shutil.copy2(SOURCES/w/'evaluation'/name,out/name)
 s=BUILDERS[w]();write(out/'design.json',{'elements':s.e,'roles':s.roles,'palette':PALETTES[w]})
 skin=bake(w,s);native(w,skin)
 evaluation=json.loads((out/'source-evaluation.json').read_text())
 title={'gjallarhorn':'Gjallarhorn','whisper_of_the_worm':'Whisper of the Worm','tractor_cannon':'Tractor Cannon'}[w]
 icon=Path('/tmp/exotic-expansion-20261109/data/icons')/(title.replace(' ','_')+'.jpg')
 if icon.exists():shutil.copy2(icon,out/'source_official_icon.jpg')
 urls=json.loads(Path('/tmp/exotic-expansion-20261109/data/icon-paths.json').read_text())
 write(out/'finish-provenance.json',{'source':'Bungie official inventory icon selected by master from current definition','name':title,'url':urls[title],'sha256':sha(icon),'palette':PALETTES[w],'interpretation':'Purpose-authored flat RGBA material roles; no dynamic PBR reconstruction claim'})
 manifest={'id':w,'stage':'W350','sourceDriveFileId':FILES[w],'sourceBlendSHA256':evaluation['sha256'],'sourceArchiveSHA256':sha(SOURCES/w/'source.archive'),'sourceActions':evaluation['actions'],'sourceOriginalUnchanged':sha(evaluation['blend'])==evaluation['sha256'],'partElements':{p:len(es) for p,es in skin['parts'].items()},'weaponElements':sum(map(len,skin['parts'].values())),'firstPersonElementsMaximum':sum(map(len,skin['parts'].values()))+224,'atlas':skin['texture_size'],'reloadSamples':61,'motionAuthorship':'New authored PCHIP motion; source static weapon bones only, no source hand animation','nativeAcceptance':'pending master first and second Vision','scope':'Independent full weapon assets, authored contacts, hip/ADS/inspect/thirdperson and 61 reload poses'}
 write(out/'manifest.json',manifest)
 (out/'DESIGN.md').write_text('# '+w+' — W350\n\nActual supplied .blend opened with --disable-autoexec in owned headless Blender. Source was not saved. SHA256, action/slot absence, weapon bones and materials are recorded in source-evaluation.json. Source Workbench renders are silhouette evidence, not recovered final PBR. No player wrists, elbows or hands exist in these sources.\n\nGeometry uses adjoining rectangular volumes, meaningful silhouette stations, real bore and frame voids. Flat material role colors, distinct metal/rubber/paint and 1-texel edges; no direct ripped mesh conversion, noisy reprojection, alpha body slabs or unrelated rotated plates.\n\nReload is authored for the source part hierarchy: Gjallarhorn cover plus chamber round; Whisper detachable lower magazine; Tractor top energy cell. The 61 poses use shared-derivative PCHIP with rest endpoints and handling holds. Skin forearms are contact-fitted approximations, not extracted character motion or finger IK. Native bank does not claim continuous 60fps interpolation.\n\nOffline model/UV/endpoint checks are separate from master first/second Vision grip, ADS, contact, display scale and 10–20 instance checks. Native quality remains pending.\n')
 check(w);print(w,manifest['weaponElements'],'elements',skin['texture_size'],flush=True)

def check(w):
 d=json.loads((ART/w/'skin.json').read_text());es=sum(d['parts'].values(),[])
 assert 0<len(es)<=1000 and len({e['name'] for e in es})==len(es)
 for e in es:
  assert all(-16<=v<=32 for v in e['from']+e['to'])
  assert all(a<b for a,b in zip(e['from'],e['to']))
  assert set(e['faces'])==set(kit.FACE_AXES)
  for face in e['faces'].values():assert all(0<=x<=16 for x in face['uv'])
 p=json.loads((ART/w/'reload-poses.json').read_text());assert len(p['poses'])==61
 for i,row in enumerate(p['poses']):assert row['frame']==i and row['progress']==i/60
 for i in (0,60):assert p['poses'][i]['bodyRotation']==[0,0,0] and p['poses'][i]['magazineOffset']==[0,0,0]
 graph_paths=list((A/'items').glob(f'**/{w}/**/*.json'))+[A/f'items/weapon/{w}.json',A/f'items/weapon_aim_w350/{w}.json',A/f'items/weapon_reload_w350/{w}.json']
 missing=[]
 def visit(n):
  if isinstance(n,dict):
   if n.get('type')=='minecraft:model' and n.get('model','').startswith('destiny:'):
    q=A/'models'/(n['model'].split(':',1)[1]+'.json')
    if not q.exists():missing.append(str(q))
   for v in n.values():visit(v)
  elif isinstance(n,list):
   for v in n:visit(v)
 for f in graph_paths:visit(json.loads(f.read_text()))
 assert not missing,missing
 report={'jsonAndUV':'PASS','weaponElements':len(es),'firstPersonWithTwoClassicForearms':len(es)+224,'reloadSamples':61,'endpointRest':'PASS','graphReferences':'PASS','sourceOriginalUnchanged':sha(json.loads((ART/w/'source-evaluation.json').read_text())['blend'])==json.loads((ART/w/'source-evaluation.json').read_text())['sha256'],'nativePackLoad':'MASTER_PENDING','firstSecondVision':'MASTER_PENDING','sourceAnimationAvailable':False}
 write(ART/w/'validation.json',report)

def render(w):
 out=ART/w/'review';out.mkdir(exist_ok=True)
 subprocess.run([BLENDER,'-b','--python',str(ROOT/'scripts/art/w325/render_model.py'),'--',str(out/w),str(ART/w/'skin.json'),str(A/f'textures/item/weapon/w350/{w}.png'),'west,east,top,q,front'],check=True)

if __name__=='__main__':
 cmd=sys.argv[1] if len(sys.argv)>1 else 'build';ids=IDS if len(sys.argv)<3 or sys.argv[2]=='all' else [sys.argv[2]]
 if cmd in ('build','render','check') and Path(__file__).with_name('power_r2.py').exists():
  subprocess.run([sys.executable,str(Path(__file__).with_name('power_r2.py')),cmd,*ids],check=True)
 else:
  for w in ids:globals()[cmd](w)
