#!/usr/bin/env python3
"""W350 energy exotics: authored solid-block models, materials and native 61-pose presentation.
Sources are read-only Blender evaluations. No source reload action exists in these archives.
python energy.py [build|render|check|all] [sunshot|graviton_lance|jotunn|all]
"""
import copy, hashlib, importlib.util, json, math, struct, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=module('w327_energy_basis',ROOT/'scripts/art/w327/group1.py');kit=g.kit
from PIL import Image
import generate_ace_reload_w157 as rigid
import build_first_person_hands_w201 as hands
kit.ROOT=ROOT;kit.ASSETS=ROOT/'src/main/resources/assets/destiny';A=kit.ASSETS
kit.art=lambda w:ROOT/'art/weapons/w350'/w
kit.atlas_path=lambda w:A/f'textures/item/weapon/w350/{w}.png'
kit.hud_path=lambda w:A/f'textures/item/hud/w350/ammo_{w}.png'
kit.skin_path=lambda w:kit.art(w)/'geometry.json'
IDS=['sunshot','graviton_lance','jotunn']
DRIVE=['1eLcLwHo611phmMPuO7dDwpnkjA5n498n','1PX34CMHAIR9ifeNCCsbQIDDPOWZ7Kb9O','1cs5oXWIySj8o_9ErbleY8CtOdE8HS_W7']
kit.reg=lambda w:dict(id=w,name=w.replace('_',' ').title(),tier='exotic',base=w,drive_file_id=DRIVE[IDS.index(w)])
kit.RIPS=Path('/tmp/exotic-expansion-20261109/sources')
S=g.Shape
FP=('firstperson_righthand','firstperson_lefthand')
PALETTES={
 'sunshot':{'shell':('steel',[182,182,170]),'accent':('gold',[174,133,76]),'trim':('steel',[138,139,129]),'steel':('steel',[116,118,113]),'black_steel':('metal',[42,44,44]),'rubber':('paint',[187,184,163]),'recess':('dark',[18,18,19]),'lens':('glow',[255,176,61])},
 'graviton_lance':{'shell':('metal',[37,35,47]),'accent':('paint',[106,66,130]),'trim':('steel',[147,146,162]),'steel':('steel',[71,71,86]),'black_steel':('metal',[21,23,30]),'rubber':('rubber',[30,29,38]),'recess':('dark',[12,12,20]),'lens':('glow',[166,123,230])},
 'jotunn':{'shell':('paint',[51,56,55]),'accent':('gold',[185,160,110]),'trim':('steel',[169,168,157]),'steel':('steel',[83,88,90]),'black_steel':('metal',[32,37,39]),'rubber':('rubber',[28,31,30]),'recess':('dark',[14,17,18]),'lens':('glow',[252,134,36])}}
NOTES={
 'sunshot':'Split flared blade-like solar barrel, real muzzle/diamond-slot openings, dark perforated cylinder and swept dark grip. Cylinder swings from the source CraneRotate hinge; transport/hand timing is authored, not source animation.',
 'graviton_lance':'Long slim black-violet hexagonal bore, exposed lower conductor, compact high optic, skeleton shoulder opening and separate rear battery. The source mesh action animates UV coordinates only; no weapon/hand reload action is present.',
 'jotunn':'Broad rectangular furnace muzzle, long twin upper rails, side U-shaped protective pipes, short rear cage/cables and separate top battery. Source has a single shader-node key only; weapon-only rig bone names are not player bones.'}

def sunshot():
 s=S()
 # Two deep barrel jaws. Their changing silhouettes and three openings are solid geometry.
 s.stair('upper_jaw',[(-9.8,-8.9,10.45,11.65),(-8.9,-7.2,10.0,11.7),(-7.2,-5.4,10.0,11.75),(-5.4,-3.6,10.0,11.8),(-3.6,-1.5,9.8,11.85),(-1.5,1.6,9.5,11.9)],1.32,'accent')
 s.stair('lower_jaw',[(-10,-8.9,7.5,8.1),(-8.9,-7.3,7.5,9.1),(-7.3,-5.5,7.5,9.3),(-5.5,-3.7,7.5,9.3),(-3.7,-1.5,7.5,9.4),(-1.5,1.6,7.75,9.5)],1.4,'shell')
 for i,z in enumerate([-7.3,-5.5]):
  s.block('slot_bridge'+str(i),1.2,9.3,10,z-.14,z+.14,'steel',.05)
 s.block('barrel_rear',1.45,7.9,9.4,1.6,3.25,'shell')
 s.block('top_spine',.65,11.85,12.05,-8.2,6.9,'black_steel',.05)
 s.block('frame_top',1.25,11.55,11.85,1.6,6.8,'shell',.1)
 s.block('frame_rear',1.25,8.0,11.55,6.1,7.1,'shell')
 s.block('frame_bottom',1.1,7.7,8.15,3.25,6.1,'steel',.08)
 s.block('mag_cylinder',1.8,8.5,11.1,2.85,5.45,'black_steel',.3)
 s.block('mag_front_rim',1.75,8.75,10.85,2.5,2.85,'steel',.28)
 s.block('mag_rear_rim',1.75,8.75,10.85,5.45,5.8,'steel',.28)
 s.box('mag_crane',7.82,8.18,8.1,8.5,2.3,6.0,'steel')
 s.grip('pistol_grip',8.3,3.6,1.28,4.5,1.55,'rubber')
 s.guard(4.1,7.15,6.3,7.7)
 next(e for e in s.e if e['name']=='trigger')['to'][1]=8.1
 s.block('grip_heel',1.48,3.45,3.7,8.15,9.7,'trim',.1)
 s.sight(6.25,12.12,.65,.3)
 s.box('front_sight',7.91,8.09,12.05,12.28,-7.8,-7.4,'trim')
 s.panel('solar_heat_channel',.72,9.0,9.3,-3.5,1.5,'lens',.045)
 s.panel('front_chamfer_line',.68,11.48,11.62,-8.85,-1.65,'accent',.035)
 return s

def graviton_lance():
 s=S()
 s.tube('hex_muzzle',1.5,1.8,11.45,-10.6,-9.7,'steel',.25)
 s.stair('upper_bore',[(-9.7,-6.6,10.55,12.35),(-6.6,-2.2,10.55,12.4),(-2.2,2.4,10.55,12.4),(2.4,7.7,10.5,12.4)],1.58,'shell')
 s.block('lower_conductor',.85,8.95,9.8,-9.8,7.65,'black_steel',.2)
 s.block('conductor_nose',.85,9.2,10.55,-10.4,-9.8,'black_steel',.22)
 s.block('conductor_front_latch',1.0,8.9,9.85,-5.5,-5.1,'steel',.1)
 s.block('lower_receiver_rail',.8,8.4,8.95,-4.0,6.4,'steel',.06)
 s.block('rear_receiver',1.9,8.6,12.4,7.7,12.0,'shell',.2)
 s.block('stock_upper',1.35,11.65,12.4,12.0,16.2,'shell')
 s.block('stock_tail',1.35,9.45,11.65,15.5,16.2,'shell')
 s.block('stock_lower',1.35,8.9,9.65,12.0,15.5,'shell')
 # Open rectangular curved-return conductor in the stock, true through-hole around it.
 s.block('rear_conductor_upper',.65,10.9,11.3,12.0,14.5,'steel',.07)
 s.block('rear_conductor_return',.65,10.2,10.9,14.5,14.9,'steel',.07)
 s.block('rear_conductor_lower',.65,9.8,10.2,12.0,14.5,'steel',.07)
 s.grip('grip',7.4,4.9,1.0,3.9,1.1,'rubber')
 s.guard(3.8,6.3,7.0,8.4)
 s.mag(10.1,12.6,4.2,8.6,1.25,'shell')
 s.panel('receiver_voltage',.96,10.4,10.7,8.1,11.5,'accent',.045)
 for side in [-1,1]:
  for i in range(3):
   x=8+side*.86;s.box('filament'+str(side)+'_'+str(i),x-.055,x+.055,9.43+i*.27,9.54+i*.27,2.3,8.0,'lens')
 s.block('optic_mount',.65,12.4,12.9,4.2,6.5,'black_steel',.06)
 s.tube('optic_open',1.2,1.05,13.42,3.9,6.6,'steel',.18)
 s.box('optic_reticle_pin',7.95,8.05,12.94,13.20,4.0,4.12,'lens')
 s.block('upper_charge_band',.66,12.4,12.55,-7.5,2.7,'accent',.06)
 s.fins('optic_ridges',[5.9,6.15,6.4],12.88,14.0,1.25,'accent')
 return s

def jotunn():
 s=S()
 # Furnace face is a deep hollow square, no alpha facade.
 s.tube('furnace_muzzle',4.5,5.0,10.2,-7.1,-5.9,'shell',.65)
 s.tube('inner_hot_bore',3.2,3.7,10.2,-5.9,-4.9,'black_steel',.42)
 s.tube('ember_ring',2.4,2.9,10.2,-4.9,-4.5,'lens',.18)
 s.block('chamber_back',3.2,8.35,12.05,-4.5,-3.9,'recess',.15)
 s.block('upper_receiver',3.5,12.7,13.5,-5.9,7.8,'shell',.22)
 s.block('rear_receiver',3.4,10.7,12.7,6.1,10.2,'accent',.25)
 s.block('rear_spine',2.4,12.7,13.25,7.8,10.9,'black_steel',.15)
 s.block('lower_frame',3.5,6.9,7.7,-5.8,7.5,'black_steel',.15)
 s.block('rear_frame',2.9,7.7,10.7,7.5,8.4,'accent',.2)
 s.box('rear_cross_brace',5.45,10.55,12.7,13.3,8.0,8.4,'black_steel')
 s.box('rear_cable_return',5.45,10.55,7.9,9.65,7.3,7.5,'black_steel')
 for i,z in enumerate([-2.7,2.8]):
  s.box('cheek_internal_mount'+str(i),6.35,9.65,11.3,12.7,z,z+.45,'black_steel')
 # Jotunn side plates are broken into functional adjoining deep sections.
 for side in [-1,1]:
  x0,x1=(5.9,6.45) if side<0 else (9.55,10.1)
  s.box('cheek_front'+str(side),x0,x1,8.0,11.8,-3.0,.3,'shell')
  s.box('cheek_back'+str(side),x0,x1,8.8,11.8,.3,3.8,'shell')
  s.box('cheek_step'+str(side),x0,x1,8.4,8.8,.3,2.1,'shell')
  # Adjoining square U-shaped protective pipe around the cheek, open centre.
  x=5.65 if side<0 else 10.35
  for i,(z0,z1,y0,y1) in enumerate([(-4.8,-3.8,8.1,11.8),(-3.8,-2.6,11.8,12.35),(-2.6,3.0,12.0,12.6),(-3.8,-2.6,7.55,8.1),(-2.6,3.0,7.3,7.9)]):
   s.box('protect_pipe'+str(side)+'_'+str(i),x-.26,x+.26,y0,y1,z0,z1,'accent')
  # Three exposed return cables in rear cage, stair stations convey their sweep.
  for i in range(3):
   y=8.15+i*.6;s.box('return_cable'+str(side)+'_'+str(i),x-.13,x+.13,y,y+.18,3.1,7.55,'black_steel')
  s.box('rail_side'+str(side),x-.18,x+.18,13.2,13.8,-6.4,9.4,'accent')
  s.box('rail_clamp'+str(side),x-.33,x+.33,11.5,13.86,-1.0,-.6,'trim')
  s.box('lower_clamp'+str(side),x-.33,x+.85 if side<0 else x+.33,7.65,8.45,-1.0,-.6,'trim') if side<0 else s.box('lower_clamp'+str(side),x-.85,x+.33,7.65,8.45,-1.0,-.6,'trim')
  s.box('front_rail_mount'+str(side),x-.33,x+.75 if side<0 else x+.33,12.5,13.86,-5.97,-5.5,'steel') if side<0 else s.box('front_rail_mount'+str(side),x-.75,x+.33,12.5,13.86,-5.97,-5.5,'steel')
  s.box('latch'+str(side),x0-.04,x1+.04,10.45,11.25,-2.75,-1.9,'steel')
  s.box('cable_collar'+str(side),5.45 if side<0 else 9.50,6.50 if side<0 else 10.55,7.9,10.0,3.0,3.3,'steel')
 s.block('mag_topcell',2.4,13.5,14.15,1.0,5.8,'accent',.18)
 s.block('mag_latch',1.0,14.15,14.45,4.6,5.4,'steel',.08)
 s.grip('rear_palm_grip',8.9,4.7,1.4,2.95,.5,'rubber')
 s.guard(5.3,8.0,6.0,7.4)
 s.sight(6.5,13.6,1.25,.8)
 saddle=next(e for e in s.e if e['name']=='sight_saddle');saddle['from'][0]=7.35;saddle['to'][0]=8.65
 s.box('front_sight_post',7.9,8.1,13.5,14.0,-4.9,-4.6,'steel')
 return s

BUILD={'sunshot':sunshot,'graviton_lance':graviton_lance,'jotunn':jotunn}

def special(w,e,fn,u,v):
 if fn not in ('east','west'):return None
 p=kit.face_point(e,fn,u,v);x,y,z=p;n=e['name'];c=None
 if w=='sunshot':
  if n.startswith('mag_cylinder'):
   # The source cylinder has rows of small dimples: a UV mark instead of screw geometry.
   if (int((z-2.65)*10)%5==0 and int((y-8.5)*10)%5==0):c=[142,144,127]
  if n.startswith(('upper_jaw','lower_jaw')):
   # Solar red pigment with shallow black groove and restrained warm lower edge.
   if 10.65<y<11.04 and z<-2:c=[173,82,29]
   if 11.04<y<11.16 and z<-2:c=[42,43,40]
   if 7.65<y<7.8:c=[211,111,41]
  if n.startswith(('lower_jaw','pistol_grip')):
   # Sparse linear/geometric engraving visible on the source ivory grip and blade.
   if abs(((z+y*.7)*2.2)%3-1.5)<.055 or abs(((z-y*.7)*2.2)%3-1.5)<.055:c=[135,136,126]
 elif w=='graviton_lance':
  if n.startswith('upper_bore') and 10.9<y<11.8:
   curve=11.35+.12*math.sin(z*1.7)
   if abs(y-curve)<.045:c=[144,105,211]
   if abs(y-curve-.12)<.035:c=[75,49,108]
  if n.startswith('rear_receiver') and 8.85<y<10.25 and 8.2<z<11.65:
   if abs(y-(9.1+.17*(z-8.2)))<.045:c=[126,98,162]
 elif w=='jotunn':
  if n.startswith('cheek'):
   # Source hand-in-circle Armory mark, simplified in face UV, with no invented lettering.
   zz=z+.7;yy=y-10.0;r=math.hypot(zz,yy)
   if abs(r-.72)<.045:c=[187,187,168]
   if -.23<zz<.23 and -.30<yy<.12:c=[187,187,168]
   if -.25<zz<.25 and .12<yy<.5 and int((zz+.25)*24)%3<2:c=[187,187,168]
   if -.4<zz<-.2 and -.12<yy<.14:c=[187,187,168]
   if 8.35<y<8.55:c=[156,155,139]
 return tuple(c)+(255,) if c else None

class Baker(g.Baker):
 def __init__(self,w):
  self.wid=w;self.D=kit.load_design(w);self.T=self.D.T;self.A=self.D.ATLAS
  self.is_mag=lambda n:n.startswith('mag_');self.clear=lambda *a:False;self.fallback=(70,70,70,255)
 def face(self,e,fn):
  o,u,v=kit.face_frame(e,fn);w=max(1,round(math.dist((0,0,0),u)*self.T));h=max(1,round(math.dist((0,0,0),v)*self.T))
  role=self.D.ROLES[e['name']];im=Image.new('RGBA',(w,h),tuple(self.D.MATERIALS[role]['color'])+(255,));px=im.load()
  self._painted=[[False]*h for _ in range(w)]
  for i in range(w):
   for j in range(h):
    c=special(self.wid,e,fn,(i+.5)/w,(j+.5)/h)
    if c:px[i,j]=c;self._painted[i][j]=True
  return im,[[True]*h for _ in range(w)],False
 def materialize(self,faces):
  # W30-style calm pigment planes: material contrast and 1-texel edges, no universal chrome bands.
  for idx,(n,fn,img,clear,e,others,pm) in enumerate(faces):
   role=self.D.ROLES[n];mat=self.D.MATERIALS[role];w,h=img.size;out=Image.new('RGBA',(w,h));px=out.load();src=img.load()
   factor={'up':1.06,'down':.86,'north':.91,'south':.93,'east':1.0,'west':1.0}[fn]
   for i in range(w):
    for j in range(h):
     c=src[i,j][:3] if pm[i][j] else mat['color'];px[i,j]=tuple(max(0,min(255,round(v*factor))) for v in c)+(255,)
   if mat['kind']!='glow':self.rim(out,e,fn,others,.16 if mat['kind'] in ('steel','metal','gold') else .10)
   faces[idx]=(n,fn,out,clear,e,others,pm)

def enc(d):return (json.dumps(d,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(enc(d))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_design(w):
 s=BUILD[w]();p=kit.art(w);p.mkdir(parents=True,exist_ok=True)
 mats={r:dict(kind=k,color=c,detail=0,wear=False) for r,(k,c) in PALETTES[w].items()}
 for e in s.e:
  if s.roles[e['name']]=='lens':e['light_emission']=3
 text='"""'+NOTES[w]+'"""\nELEMENTS='+repr(s.e)+'\nROLES='+repr(s.roles)+'\nMATERIALS='+repr(mats)+'\nSTYLE="material"\nT=10\nATLAS=512\nNO_OVERLAY=True\ndef elements():return ELEMENTS\ndef material(n,fn):return ROLES[n]\n'
 (p/'design.py').write_text(text)
 return s

CONTACTS={
 'sunshot':{'right':([8,7.6,7.6],[-22,0,0]),'left':([7.3,7.3,7.8],[-22,0,-18]),'load':([7.05,9.75,4.3],[0,0,-80]),'pivot':[8,8.15,3.1]},
 'graviton_lance':{'right':([8,8.1,6.7],[-18,0,0]),'left':([8,8.65,-2.4],[-83,0,-20]),'load':([7.4,6.0,11.3],[0,0,-60]),'pivot':[8,8.4,11.4]},
 'jotunn':{'right':([8,7.3,8.6],[-8,0,0]),'left':([6.8,8.0,-1.8],[-80,0,-25]),'load':([7.0,13.9,3.6],[0,0,-100]),'pivot':[8,13.5,5.8]}}

def smooth(t):return max(0,min(1,t))**2*(3-2*max(0,min(1,t)))
def curve(p,knots):
 for (a,x),(b,y) in zip(knots,knots[1:]):
  if p<=b:
   t=smooth((p-a)/(b-a));return [u+(v-u)*t for u,v in zip(x,y)]
 return knots[-1][1]
def motion(w,p):
 # Deliberate hold/withdraw/insert beats. Endpoint transform is exactly identity.
 body=curve(p,[(0,[0,0,0]),(.13,[-13,-10,-18]),(.23,[-22,-10,-28]),(.70,[-22,-10,-28]),(.87,[-10,-4,-10]),(1,[0,0,0])])
 shift=curve(p,[(0,[0,0,0]),(.2,[.6,-.4,-.3]),(.75,[.6,-.4,-.3]),(1,[0,0,0])])
 if w=='sunshot':
  ang=curve(p,[(0,[0,0,0]),(.14,[0,0,0]),(.27,[0,0,76]),(.68,[0,0,76]),(.82,[0,0,0]),(1,[0,0,0])]);off=curve(p,[(0,[0,0,0]),(.31,[0,0,0]),(.39,[0,0,1.0]),(.48,[0,0,0]),(1,[0,0,0])])
 elif w=='graviton_lance':
  ang=[0,0,0];off=curve(p,[(0,[0,0,0]),(.22,[0,0,0]),(.38,[0,-4,0.6]),(.56,[0,-4,0.6]),(.72,[0,0,0]),(1,[0,0,0])])
 else:
  ang=curve(p,[(0,[0,0,0]),(.2,[0,0,0]),(.35,[-38,0,0]),(.57,[-38,0,0]),(.76,[0,0,0]),(1,[0,0,0])]);off=curve(p,[(0,[0,0,0]),(.25,[0,0,0]),(.4,[0,2.1,0]),(.56,[0,2.1,0]),(.76,[0,0,0]),(1,[0,0,0])])
 return body,shift,ang,off

def display_pose(idle,w,p,part):
 angles,shift,local,off=motion(w,p);b=rigid.xyz(angles);l=rigid.xyz(local if part=='magazine' else [0,0,0])
 h=rigid.sub(CONTACTS[w]['right'][0],[8]*3);q=rigid.sub(CONTACTS[w]['pivot'],[8]*3)
 offset=rigid.sub(h,rigid.vec(b,h))
 if part=='magazine':offset=rigid.add(offset,rigid.vec(b,rigid.add(rigid.sub(q,rigid.vec(l,q)),off)))
 out=copy.deepcopy(idle)
 for ctx in FP:
  d=idle[ctx];base=rigid.xyz(d['rotation']);scale=d['scale'][0]
  out[ctx]['rotation']=rigid.euler(rigid.mul(base,rigid.mul(b,l)))
  out[ctx]['translation']=[round(x,8) for x in rigid.add(d['translation'],rigid.vec(base,[scale*v for v in rigid.add(offset,shift)]))]
 return out

def model_node(k):return {'type':'minecraft:model','model':'destiny:'+k}
def fp_guard(node,full):return {'type':'minecraft:select','property':'minecraft:display_context','cases':[{'when':list(FP),'model':node}],'fallback':full}
def arm_node(w,side,display,key):
 refs={};offset=64 if side=='right' else 192
 for variant,count in [('classic',112),('slim',96)]:
  k=f'weapon_w350/{w}/hands/{key}_{side}_{variant}'
  write(A/f'models/{k}.json',{'parent':f'destiny:skin_arm_w204/{side}_{variant}','display':display})
  refs[variant]=dict(model_node(k),tints=[{'type':'minecraft:custom_model_data','index':offset+i,'default':16777215} for i in range(count)])
 return {'type':'minecraft:condition','property':'minecraft:custom_model_data','index':8,'on_false':{'type':'minecraft:empty'},'on_true':{'type':'minecraft:condition','property':'minecraft:custom_model_data','index':9,'on_true':refs['slim'],'on_false':refs['classic']}}

def composite(w,nodes,body_display,key,p=None,mag_display=None):
 models=list(nodes);c=CONTACTS[w]
 for side in ['right','left']:
  pos,rot=c[side];contact={'position':list(pos),'rotation':list(rot)};carrier=body_display
  if side=='left' and p is not None:
   # Approach, attach during withdrawal/insertion, then release back to support contact.
   weight=smooth((p-.08)/.15)*(1-smooth((p-.78)/.16))
   if weight>0:
    target=c['load'];a=hands.display_at(body_display,contact);b=hands.display_at(mag_display,{'position':target[0],'rotation':target[1]})
    disp=hands.blend_display(a,b,weight)
   else:disp=hands.display_at(carrier,contact)
  else:disp=hands.display_at(carrier,contact)
  models.append(arm_node(w,side,disp,key))
 return {'type':'minecraft:composite','models':models}

def presentation(w):
 d=json.loads(kit.skin_path(w).read_text());parts=d['parts'];prefix=f'weapon_w350/{w}'
 # Reuse family framing, not family geometry. Author new contacts against each source-inspired model.
 base='ace_of_spades' if w=='sunshot' else 'blast_furnace' if w=='graviton_lance' else 'null_composure'
 path=A/f'models/item/weapon/{base}.json'
 canonical=json.loads((ROOT/'art/weapons/w201/contacts.json').read_text())['weapons'][base]['canonicalModel']
 source,_=hands.resolve(canonical)
 idle=copy.deepcopy(source['display'])
 # New side/length proportions get explicit authored scales and framing, pending native QA.
 for ctx in FP:
  idle[ctx]={'rotation':[7.6,9.9,0],'translation':[0,-.6,-3.5],'scale':[.85]*3} if w=='sunshot' else {'rotation':[4,10,0],'translation':[0,-1.5,-5],'scale':[.7]*3}
 if w in ('graviton_lance','jotunn'):
  # First native Vision: crossbow-hold uses model -Z as forward.
  for ctx in ['thirdperson_righthand','thirdperson_lefthand']:
   idle[ctx]={'rotation':[5.729578,-17.188734,0],'translation':[0,-2,2],'scale':[.7]*3}
 idle['gui']={'rotation':[10,65,-10],'translation':[0,-1,0],'scale':[.63]*3 if w!='sunshot' else [.8]*3}
 tex={'0':f'destiny:item/weapon/w350/{w}','particle':f'destiny:item/weapon/w350/{w}'}
 common={'credit':'W350 authored block reinterpretation of Bungie weapon; source archive recorded in manifest.','ambientocclusion':True,'gui_light':'side','textures':tex,'display':idle}
 for part,els in [('full',parts['body']+parts['magazine']),*parts.items()]:write(A/f'models/{prefix}/{part}.json',dict(common,elements=els))
 full=model_node(prefix+'/full')
 hip=composite(w,[full],idle,'hip')
 ready={}
 for mode in ['ads','inspect']:
  disp=copy.deepcopy(idle)
  for ctx in FP:
   if mode=='ads':
    # Measured R2 geometry: front iron top, optic aperture center, clear rear-plate top.
    height={'sunshot':11.46,'graviton_lance':13.9776,'jotunn':14.22}[w]
    scale=.9 if w=='sunshot' else .78
    disp[ctx]={'rotation':[0,0,0],'translation':[-8.96,8.32-(height-8)*scale,5.0],'scale':[scale]*3}
   else:disp[ctx]={'rotation':[-14,-36,-16],'translation':[-1,1,-3],'scale':idle[ctx]['scale']}
  write(A/f'models/{prefix}/{mode}.json',{'parent':'destiny:'+prefix+'/full','display':disp})
  ready[mode]=composite(w,[model_node(prefix+'/'+mode)],disp,mode)
 entries=[];poses=[]
 for frame in range(61):
  p=frame/60;bd=display_pose(idle,w,p,'body');md=display_pose(idle,w,p,'magazine');nodes=[]
  for part,disp in [('body',bd),('magazine',md)]:
   k=f'{prefix}/reload/{frame}_{part}';write(A/f'models/{k}.json',{'parent':f'destiny:{prefix}/{part}','display':disp});nodes.append(model_node(k))
  node=composite(w,nodes,bd,'reload_'+str(frame),p,md)
  write(A/f'items/weapon_reload_w350/{w}/{frame}.json',{'model':fp_guard(node,full),'hand_animation_on_swap':False})
  entries.append({'threshold':struct.unpack('f',struct.pack('f',p))[0],'model':node})
  poses.append({'frame':frame,'progress':p,'body':bd['firstperson_righthand'],'magazine':md['firstperson_righthand'],'authoredChannels':motion(w,p)})
 dispatch={'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data','index':1,'entries':entries,'fallback':hip}
 select={'type':'minecraft:select','property':'minecraft:custom_model_data','index':0,'cases':[{'when':mode,'model':node} for mode,node in ready.items()],'fallback':hip}
 write(A/f'items/weapon_reload_w350/{w}.json',{'model':fp_guard(dispatch,full),'hand_animation_on_swap':False})
 write(A/f'items/weapon/{w}.json',{'model':fp_guard(select,full),'hand_animation_on_swap':False})
 aim_entries=[]
 adsdisp=json.loads((A/f'models/{prefix}/ads.json').read_text())['display']
 for frame in range(21):
  t=frame/20;disp=hands.blend_display(idle,adsdisp,t);disp={**idle,**disp}
  k=f'{prefix}/aim/{frame}';write(A/f'models/{k}.json',{'parent':'destiny:'+prefix+'/full','display':disp})
  node=composite(w,[model_node(k)],disp,'aim_'+str(frame))
  aim_entries.append({'threshold':struct.unpack('f',struct.pack('f',t))[0],'model':node})
 write(A/f'items/weapon_aim_w350/{w}.json',{'model':fp_guard({'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data','index':3,'entries':aim_entries,'fallback':hip},full),'hand_animation_on_swap':False})
 for mode,node in [('hip',hip),*ready.items()] :write(A/f'items/{prefix}/{mode}.json',{'model':fp_guard(node,full),'hand_animation_on_swap':False})
 rig={'schemaVersion':1,'weapon':w,'sourceRig':json.loads((kit.art(w)/'source-evaluation.json').read_text())['armatures'],'sourceHasReloadAction':False,'motionProvenance':'authored approximation; source weapon rig only; no player wrist/elbow bones','contacts':c if (c:=CONTACTS[w]) else {},'frames':poses}
 write(kit.art(w)/'rig-reload.json',rig)
 write(kit.art(w)/'integration.json',{'weapon':w,'model':'destiny:weapon/'+w,'hip':'destiny:'+prefix+'/hip','ads':'destiny:'+prefix+'/ads','inspect':'destiny:'+prefix+'/inspect','reloadModel':'destiny:weapon_reload_w350/'+w,'aimModel':'destiny:weapon_aim_w350/'+w,'aimFrames':21,'aimCmdFloatIndex':3,'reloadPrefix':'destiny:weapon_reload_w350/'+w+'/','reloadFrames':61,'reloadCmdFloatIndex':1,'modeCmdStringIndex':0,'skinReadyFlag':8,'skinSlimFlag':9,'skinTintStarts':{'right':64,'left':192},'hud':'destiny:item/hud/w350/ammo_'+w,'motion':'authored; native QA pending'})

def check(w):
 d=json.loads(kit.skin_path(w).read_text());els=sum(d['parts'].values(),[]);assert len(els)<=1000
 assert len({e['name'] for e in els})==len(els)
 for e in els:
  assert all(e['from'][i]<e['to'][i] for i in range(3))
  assert all(-16<=v<=32 for v in e['from']+e['to'])
  for f in e['faces'].values():assert all(0<=v<=16 for v in f['uv'])
 rig=json.loads((kit.art(w)/'rig-reload.json').read_text());assert len(rig['frames'])==61
 assert rig['frames'][0]['body']==rig['frames'][-1]['body'];assert rig['frames'][0]['magazine']==rig['frames'][-1]['magazine']
 max_rotation=max(abs(b['body']['rotation'][i]-a['body']['rotation'][i]) for a,b in zip(rig['frames'],rig['frames'][1:]) for i in range(3))
 assert max_rotation<15
 paths=[p for p in A.rglob('*.json') if w in p.parts or p.stem==w]
 refs=[]
 def visit(d):
  if isinstance(d,list):
   for x in d:visit(x)
  elif isinstance(d,dict):
   for k,v in d.items():
    if k in ['parent','model'] and isinstance(v,str) and v.startswith('destiny:'):
     path=A/('models/'+v.split(':',1)[1]+'.json');assert path.exists(),path;refs.append(v)
    else:visit(v)
 for p in paths:visit(json.loads(p.read_text()))
 overlaps=[]
 for part,partels in d['parts'].items():
  for i,a in enumerate(partels):
   for b in partels[i+1:]:
    for axis in range(3):
     for side in ['from','to']:
      if abs(a[side][axis]-b[side][axis])<1e-7 and g.visible_coplanar(a,b,axis,side,partels):overlaps.append([part,a['name'],b['name'],axis,side])
 write(kit.art(w)/'coplanar-review.json',overlaps)
 assert not overlaps,overlaps
 report={'weaponElements':{k:len(v) for k,v in d['parts'].items()},'totalWeaponElements':len(els),'atlas':d['texture_size'],'poses':61,'aimPoses':21,'endpointIdentity':True,'exposedCoplanarOverlaps':len(overlaps),'maxAdjacentBodyRotationDeg':max_rotation,'jsonFilesParsed':len(paths),'resolvedModelReferences':len(refs),'nativeQA':'pending first Vision, delegated review, second Vision','sourceReloadAnimation':False}
 write(kit.art(w)/'validation.json',report);print(w,json.dumps(report),flush=True)

def build(w):
 write_design(w);Baker(w).build();presentation(w);check(w)
 ev=json.loads((kit.art(w)/'source-evaluation.json').read_text());manifest=json.loads((kit.art(w)/'manifest.json').read_text());manifest.update(batch='W350',sourceBlendSha256=ev['sha256'],motion='61 authored poses; no source reload action',nativeAcceptance='pending first and second master Vision',identity=NOTES[w]);write(kit.art(w)/'manifest.json',manifest)
 (kit.art(w)/'DESIGN.md').write_text('# '+w+' — W350 energy exotic\n\n'+NOTES[w]+'\n\nSource .blend opened in owned headless Blender with auto-execution disabled; originals never saved. Source actions/slots/channels, actual evaluated bones and side/oblique/top images are recorded. No player wrist/elbow rig exists in these weapon archives. Authored model uses small adjoining blocks and face-specific 1-texel material edges, no ripped mesh conversion. Raw diffuse alone is not treated as authoritative final dye.\n\nReload has 61 samples with smooth authored transitions, deliberate holds, actual detached named assembly and support-hand approach/contact/release. 61 item poses do not imply continuous 60fps interpolation. Player-skin arms reuse the existing W204 tint contract. Native grip, ADS, part/hand contact, third person, firing and 10–20 item observation require master Vision.\n')

if __name__=='__main__':
 cmd=sys.argv[1] if len(sys.argv)>1 else 'all';ids=IDS if len(sys.argv)<3 or sys.argv[2]=='all' else [sys.argv[2]]
 for w in ids:
  if cmd in ('build','all'):build(w)
  if cmd in ('render','all'):kit.render(w)
  if cmd=='check':check(w)
