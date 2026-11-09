"""W327 group C V4 source-proportioned art. Own six skins only.
Run material ID|all for the current V4 candidate; fidelity ID for neutral geometry.
Legacy build/render/check commands are explicitly named v3-build/v3-render/v3-check.
Final runtime export and checks are recorded in each art/weapons/w327/ID/v4/validation.json.
Offline art is not native QA. Shared helpers are read-only.
"""
import json, math, hashlib, importlib.util, subprocess, sys, copy, contextlib, io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
ROOT=Path(__file__).resolve().parents[3]
MAIN=Path('/Users/qf/IdeaProjects/DestinyGuardians')
IDS=['krait','rufuss_fury','origin_story','age_old_bond','insidious','phyllotactic_spiral']
spec=importlib.util.spec_from_file_location('g3kit',ROOT/'scripts/art/w325/kit.py');kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
AS=ROOT/'src/main/resources/assets/destiny'
kit.ROOT=ROOT;kit.ASSETS=AS;kit.REG=Path('/tmp/destiny-perks-20261106/candidates/final-registry.json')
def art(w):return ROOT/'art/weapons/w327'/w
def skin(w):return ROOT/f'src/main/resources/destiny/weapon_skins/{w}.json'
def atlas(w):return AS/f'textures/item/weapon/w327/{w}.png'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

COMMON={'shell':(64,73,70),'steel':(100,113,116),'dark':(30,37,39),'rubber':(25,30,29),'recess':(13,19,21),'trim':(159,174,171),'accent':(186,204,45),'lens':(86,159,170)}
PAL={
 'krait':{'shell':(58,69,63),'steel':(100,115,107),'trim':(144,160,149),'accent':(185,205,48)},
 'rufuss_fury':{'shell':(157,184,199),'steel':(73,94,114),'accent':(83,133,174),'trim':(204,216,220),'dark':(32,45,59)},
 'origin_story':{'shell':(47,68,91),'steel':(106,119,126),'accent':(215,112,45),'trim':(214,220,215)},
 'age_old_bond':{'shell':(221,213,184),'accent':(167,144,86),'trim':(237,229,199),'steel':(70,72,79),'dark':(39,38,47)},
 'insidious':{'shell':(65,64,62),'steel':(108,108,101),'accent':(184,64,41),'trim':(145,142,127),'dark':(31,33,32)},
 'phyllotactic_spiral':{'shell':(76,50,97),'steel':(114,131,143),'accent':(49,145,166),'trim':(163,187,195),'rubber':(41,86,103),'dark':(31,42,52)}
}

class Shape:
 def __init__(self):self.e=[];self.roles={}
 def box(self,n,x0,x1,y0,y1,z0,z1,m='shell',rot=None):
  assert x1>x0 and y1>y0 and z1>z0,(n,x0,x1,y0,y1,z0,z1)
  e={'name':n,'from':[x0,y0,z0],'to':[x1,y1,z1]}
  if rot:e['rotation']=rot
  self.e.append(e);self.roles[n]=m
 def block(self,n,w,y0,y1,z0,z1,m='shell',b=.13):
  # Three adjoining bands; paint follows continuous model coordinates across bands.
  b=min(b,w*.23,(y1-y0)*.23)
  self.box(n+'_web',8-w/2+b,8+w/2-b,y0,y1,z0,z1,m)
  self.box(n+'_L',8-w/2,8-w/2+b,y0+b,y1-b,z0,z1,m)
  self.box(n+'_R',8+w/2-b,8+w/2,y0+b,y1-b,z0,z1,m)
 def beam(self,n,a,b,w,t,m='shell',x=8):
  # A true straight structural member in YZ, not overlapping disconnected stair plates.
  y,z=(a[0]+b[0])/2,(a[1]+b[1])/2;L=math.dist(a,b);ang=-math.degrees(math.atan2(b[0]-a[0],b[1]-a[1]))
  self.box(n,x-w/2,x+w/2,y-t/2,y+t/2,z-L/2,z+L/2,m,{'origin':[x,y,z],'x':ang,'y':0,'z':0})
 def side(self,n,w,y0,y1,z0,z1,m='steel',d=.10):
  for s in [-1,1]:
   x=8+s*w/2;self.box(n+('_L' if s<0 else '_R'),x-d if s<0 else x,x if s<0 else x+d,y0,y1,z0,z1,m)
 def tube(self,n,r,y,z0,z1,m='steel',wall=.14,x=8):
  # Eight edge-aligned segments form a real octagonal aperture.
  R=r-wall/2;length=2*R*math.tan(math.pi/8)
  for i in range(8):
   a=i*45;cx=x+R*math.sin(math.radians(a));cy=y+R*math.cos(math.radians(a))
   self.box(n+str(i),cx-length/2,cx+length/2,cy-wall/2,cy+wall/2,z0,z1,m,{'origin':[cx,cy,(z0+z1)/2],'x':0,'y':0,'z':-a})
 def eye(self,n,x,y,z,r,wall=.14,m='accent',depth=.18):
  R=r-wall/2
  for i in range(8):
   a=i*math.pi/4;b=(i+1)*math.pi/4
   self.beam(n+str(i),(y+R*math.sin(a),z+R*math.cos(a)),(y+R*math.sin(b),z+R*math.cos(b)),depth,wall,m,x)
 def grip(self,n,top,heel,w=1.1,depth=1.25,m='rubber'):
  self.beam(n+'_core',top,heel,w,depth,m)
  self.beam(n+'_backstrap',(top[0]-.05,top[1]+.55),(heel[0],heel[1]+.55),w+.06,.18,'dark')
 def rail(self,n,z0,z1,y,w=.8,spacing=.45):
  self.box(n+'_root',8-w/2,8+w/2,y-.13,y,z0,z1,'dark')
  for i in range(int((z1-z0)/spacing)):
   z=z0+i*spacing;self.box(n+str(i),8-w/2-.06,8+w/2+.06,y,y+.12,z,z+.17,'steel')
 def optic(self,z,y,r=.57,L=.9):
  self.block('optic_saddle',.72,y-.47,y-.20,z+.05,z+L-.05,'dark',.08)
  self.tube('optic_hood',r,y+r-.22,z,z+L,'dark',.13)
  self.tube('optic_front_rim',r+.04,y+r-.22,z-.08,z,'steel',.10)
  self.box('optic_adjuster',8+r-.1,8+r+.23,y+.13,y+.48,z+.25,z+.58,'steel')
 def mag(self,z0,z1,y0,y1,w=1.15,angle=0,m='dark'):
  start=len(self.e)
  self.block('mag_shell',w,y0+.25,y1,z0,z1,m)
  self.block('mag_floor',w+.16,y0,y0+.25,z0-.12,z1+.1,'steel',.09)
  self.side('mag_channel',w,y0+.45,y1-.25,z0+.35,z1-.35,'recess',.035)
  self.block('mag_feed',w*.80,y1,y1+.35,z0+.14,z1-.16,'dark',.06)
  if angle:
   for e in self.e[start:]:e['rotation']={'origin':[8,y1,(z0+z1)/2],'x':angle,'y':0,'z':0}

def krait():
 s=Shape()
 s.tube('suppressor',.52,10.86,-9.5,-5.3,'dark',.19)
 s.tube('suppressor_front',.56,10.86,-9.52,-9.28,'steel',.11)
 s.tube('barrel_link',.27,10.86,-5.3,-3.25,'steel',.12)
 s.tube('open_collar',.62,10.86,-4.95,-4.48,'steel',.15)
 s.box('collar_top_web',7.87,8.13,11.05,11.45,-4.87,-4.57,'steel')
 s.box('collar_lower_web',7.87,8.13,10.28,10.64,-4.87,-4.57,'steel')
 s.block('front_canopy',1.38,11.65,12.1,-5.15,-2.3)
 s.beam('canopy_tip',(11.71,-5.25),(11.98,-4.5),1.38,.20)
 s.block('mechanism_lower',1.35,9.48,10.10,-3.7,7.65,'dark')
 s.block('receiver_inner',1.35,10.12,11.73,-3.40,7.8,'dark')
 # Main top side is layered over a narrower mechanism; side carrier remains removable.
 s.block('receiver_roof',1.75,11.46,12.18,-2.4,6.5)
 s.block('receiver_brow',1.65,11.83,12.42,.15,3.3)
 s.beam('cheek_slope',(12.0,3.3),(12.55,8.7),1.35,.30)
 s.side('receiver_side_panel',1.46,10.96,11.62,-2.4,6.9,'shell',.16)
 s.side('carrier_recess',1.36,10.32,10.99,-1.42,7.35,'recess',.11)
 s.side('mag_charge_bar',1.59,10.50,10.87,-.08,7.4,'accent',.10)
 s.side('mag_charge_end',1.59,10.42,10.93,-1.20,-.08,'steel',.13)
 s.side('carrier_guide',1.59,10.28,10.40,-1.38,7.50,'steel',.08)
 for z in [-1.15,-.55]:s.side('carrier_latch'+str(z),1.83,10.42,11.00,z,z+.15,'dark',.08)
 s.side('lower_release',1.35,9.60,10.01,3.85,4.65,'steel',.12)
 # Stock rises toward the upper rear, then widens into a flared shoulder and lower notch.
 for i,(a,b,lo,hi,w) in enumerate([(7.65,9,10.07,12.20,1.65),(9,10.1,10.0,12.27,1.70),(10.1,11.1,9.12,12.34,1.78),(11.1,12.1,9.30,12.41,1.83),(12.1,13.1,9.45,12.48,1.90),(13.1,14.1,9.60,12.55,1.96),(14.1,15.25,9.76,12.62,2.04)]):
  if i<2:s.block('stock_flare'+str(i),w,lo,hi,a,b)
  else:
   s.block('stock_inner'+str(i),1.55,lo,hi,a,b,'dark')
   s.block('stock_upper_shoulder'+str(i),w,hi-.45,hi,a,b,'shell')
   s.block('stock_lower_shoulder'+str(i),w,lo,lo+.40,a,b,'shell')
 s.beam('stock_upper_ridge',(12.22,8.5),(12.68,15.3),1.60,.20,'dark')
 s.block('butt_contact',2.14,9.60,12.78,15.25,15.65,'rubber')
 s.side('stock_inset',1.56,10.27,11.82,10.52,14.94,'shell',.07)
 s.side('stock_cheek',1.72,11.64,12.00,12.0,14.95,'shell',.055)
 for sd in [-1,1]:
  s.beam('stock_lower_panel_channel'+str(sd),(10.20,10.58),(10.65,14.92),.08,.10,'recess',8+sd*.87)
  s.beam('stock_plate_frontstep'+str(sd),(10.22,10.58),(11.55,11.28),.10,.10,'steel',8+sd*.87)
 s.block('foregrip_shelf',1.45,9.08,9.49,-4.25,.50,'shell')
 s.beam('foregrip_hookfront',(9.18,-4.2),(8.35,-4.95),1.35,.30)
 s.beam('foregrip_hole_front',(9.05,-3.70),(8.18,-3.38),.95,.23,'dark')
 s.beam('foregrip_hole_rear',(9.05,-1.96),(8.18,-2.32),.95,.23,'dark')
 s.beam('foregrip_hole_floor',(8.18,-3.38),(8.18,-2.32),.95,.22,'dark')
 s.grip('forward_grip',(9.12,-.85),(6.95,.10),1.15,1.33)
 s.beam('forward_heel_hook',(7.0,.25),(6.52,-.28),1.12,.27)
 s.grip('rear_grip',(10.62,8.861),(6.83,10.20),1.25,1.40)
 s.beam('rear_heel_hook',(6.89,10.22),(6.32,9.67),1.20,.30)
 for n,y,z in [('forward_finger1',8.36,-1.09),('forward_finger2',7.67,-.73),('rear_finger1',9.03,8.90),('rear_finger2',8.23,9.25)]:s.block(n,1.18,y-.15,y+.15,z-.27,z+.18,'dark',.06)
 s.beam('trigger_guard_front',(9.50,5.00),(8.65,5.31),.28,.20,'steel')
 s.beam('trigger_guard_floor',(8.65,5.31),(8.65,9.00),.28,.20,'steel')
 s.beam('trigger',(9.6,6.76),(9.01,6.51),.18,.22,'dark')
 s.rail('top_forward',-3.2,-1.1,12.25,.68)
 s.optic(4.75,12.40,.36,.60)
 return s

def rufuss_fury():
 s=Shape()
 s.tube('mechanical_bore',.40,10.85,-9.65,-2.25,'dark',.14)
 s.block('mechanical_spine',1.35,10.10,11.40,-7.5,7.2,'dark')
 # Paired asymmetrical shell lobes: each changes width and forks around the visible core.
 for side in [-1,1]:
  for i,(a,b,y0,y1,x0,x1) in enumerate([(-9.85,-8.75,11.14,11.46,.40,.63),(-8.75,-7.7,11.10,11.88,.40,.91),(-7.7,-6.3,10.82,12.03,.55,1.13),(-6.3,-4.6,10.56,12.16,.66,1.24),(-4.6,-2.9,10.40,12.29,.72,1.34),(-2.9,-1.5,10.58,12.42,.72,1.28),(-1.5,.2,11.02,12.38,.60,1.16),(.2,1.5,11.47,12.59,.64,1.20)]):
   xlo,xhi=(8+x0,8+x1) if side>0 else (8-x1,8-x0)
   s.box('upper_shell_'+str(side)+'_'+str(i),xlo,xhi,y0,y1,a,b,'shell')
  for i,(a,b,y0,y1,x0,x1) in enumerate([(-9.95,-8.9,10.00,10.25,.30,.55),(-8.9,-7.5,9.66,10.31,.45,.82),(-7.5,-5.9,9.37,10.21,.60,1.05),(-5.9,-4.0,9.25,10.02,.64,1.14),(-4.0,-2.35,9.36,10.06,.62,1.21),(-2.35,-.9,9.64,10.35,.58,1.16),(-.9,.8,9.88,10.49,.55,1.00)]):
   xlo,xhi=(8+x0,8+x1) if side>0 else (8-x1,8-x0)
   s.box('lower_shell_'+str(side)+'_'+str(i),xlo,xhi,y0,y1,a,b,'shell')
  # Prominent rear eye is real negative space inside a separately layered blue lobe.
  s.eye('rear_eye_'+str(side)+'_',8+side*1.12,11.76,3.5,.76,.22,'accent',.38)
  s.box('rear_lobe_top_'+str(side),8+side*1.12-.22,8+side*1.12+.22,12.32,12.59,1.1,5.05,'accent')
  s.box('rear_lobe_floor_'+str(side),8+side*1.12-.22,8+side*1.12+.22,10.56,11.12,1.6,5.45,'accent')
  s.box('rear_lobe_rear_'+str(side),8+side*.98-.23,8+side*.98+.23,10.95,12.39,4.35,6.45,'accent')
  s.beam('rear_lobe_front_horn'+str(side),(11.60,2.79),(11.25,1.35),.40,.22,'shell',8+side*1.09)
  for pi,(py,pz,pr) in enumerate([(11.0,-3.45,.30),(11.33,-4.05,.19),(11.25,-2.60,.15)]):
   s.eye('organic_pore_'+str(side)+'_'+str(pi)+'_',8+side*1.40,py,pz,pr,.075,'steel',.16)
   cx=8+side*1.35;s.box('organic_pore_back'+str(side)+'_'+str(pi),cx-.025,cx+.025,py-pr*.70,py+pr*.70,pz-pr*.70,pz+pr*.70,'recess')
 # Top/lower bridges have purposeful varying widths rather than filling the shell with a cuboid.
 s.block('dorsal_front',.76,11.86,12.28,-6.0,-2.8,'shell')
 s.block('dorsal_shell_bridge',1.66,11.82,12.04,-6.0,-3.0,'shell')
 s.beam('dorsal_rise',(12.16,-2.8),(12.36,2.2),1.02,.40,'shell')
 s.block('dorsal_rear_bridge',1.51,12.12,12.34,-2.8,2.2,'shell')
 s.block('blue_receiver',1.5,10.12,11.13,1.2,7.2,'accent')
 s.block('stock_socket',1.26,10.85,11.95,6.45,8.0,'steel')
 s.block('stock_beam',1.05,11.15,11.87,8,14.8,'accent')
 s.side('stock_side_rail',1.06,11.40,11.57,8.25,14.55,'trim',.06)
 s.beam('stock_lower_brace',(10.14,10.1),(10.4,14.8),.66,.35,'steel')
 s.block('butt_cap',1.40,9.75,12.15,14.8,15.35,'rubber')
 s.block('magwell',1.75,9.62,10.25,1.7,4.98,'steel')
 s.mag(2.1,4.65,6.2,9.85,1.15,0,'steel')
 s.grip('grip',(10.27,8.385),(6.93,9.70),1.2,1.37)
 s.block('grip_neck',1.25,10.08,11.20,7.70,8.80,'accent')
 s.beam('lower_frame',(6.65,4.58),(6.65,9.70),.45,.25,'accent')
 s.beam('rear_frame',(6.65,9.70),(8.30,9.10),.45,.25,'accent')
 s.beam('trigger_guard',(10.18,5.2),(8.75,5.40),.28,.20,'steel')
 s.beam('trigger_floor',(8.75,5.40),(8.75,7.30),.28,.20,'steel')
 s.beam('trigger',(10.20,6.90),(9.22,6.66),.20,.17,'dark')
 s.rail('receiver_rail',5.2,7.5,12.05,.8)
 s.optic(5.25,12.32,.35,.63)
 return s

def origin_story():
 s=Shape()
 s.tube('muzzle',.49,11.12,-9.0,-7.45,'dark',.17)
 s.tube('muzzle_ring',.54,11.12,-7.75,-7.45,'steel',.12)
 s.block('barrel_sleeve',1.45,10.50,11.88,-7.45,-5.55,'steel')
 s.beam('front_slope',(11.90,-5.55),(12.35,-3.9),1.65,.28)
 s.block('receiver_main',1.83,10.30,12.12,-5.5,7.95)
 s.block('upper_slide',1.40,12.12,12.48,-3.9,6.1)
 s.side('side_recess',1.84,10.76,11.50,.6,6.9,'dark',.035)
 s.side('receiver_side',1.88,10.88,11.72,-4.8,3.9,'shell',.055)
 s.side('selector_panel',1.92,11.00,11.44,1.03,2.43,'steel',.06)
 s.side('charging_handle',1.88,11.15,11.32,5.13,6.68,'steel',.16)
 s.block('foreend',1.53,9.57,10.30,-5.1,.62,'dark')
 s.tube('underbarrel_tube',.24,9.70,-7.08,-5.1,'steel',.12)
 s.side('foreend_side',1.55,9.65,10.09,-4.75,-.08,'steel',.05)
 s.block('magwell',1.79,8.55,10.30,.68,4.45,'dark')
 s.beam('lower_front_slope',(9.52,3.30),(8.00,4.67),1.70,.44,'dark')
 s.beam('lower_frame_front',(9.8,4.57),(7.50,5.25),1.30,.35,'dark')
 s.beam('lower_frame_floor',(7.50,5.25),(7.50,8.49),1.30,.32,'dark')
 s.grip('grip',(10.52,7.341),(7.55,8.42),1.22,1.24,'shell')
 s.beam('trigger',(10.12,6.72),(9.15,6.37),.22,.20,'steel')
 s.mag(1.0,4.2,5.6,8.7,1.1,0,'dark')
 s.block('stock_socket',1.52,10.82,12.18,7.95,9.2,'dark')
 s.block('stock_upper',1.16,11.15,12.12,9.2,14.48,'dark')
 s.block('stock_lower',.96,10.38,11.15,11.75,14.48,'dark')
 s.side('stock_slot',1.17,11.30,11.67,9.67,11.17,'recess',.025)
 s.side('stock_latch',1.2,11.10,11.87,10.65,11.05,'steel',.05)
 s.block('stock_orange',1.52,10.07,12.29,14.48,14.70,'accent')
 s.block('stock_butt',1.58,10.02,12.35,14.70,15.18,'rubber')
 s.rail('upper_rail',-1.6,5.1,12.53,.85)
 s.optic(5.30,12.57,.44,.70)
 return s

def age_old_bond():
 s=Shape()
 s.tube('inner_barrel',.26,10.98,-9.46,-5.7,'steel',.12)
 # Ivory upper shell leaves an open low muzzle slot; stations narrow toward the tail.
 for i,(a,b,lo,hi,w) in enumerate([(-9.15,-7.4,11.40,12.53,1.48),(-7.4,-4.8,11.19,12.58,1.62),(-4.8,-2.4,10.97,12.58,1.78),(-2.4,.0,10.73,12.56,1.86),(.0,2.5,10.48,12.50,1.90),(2.5,5.4,10.42,12.45,1.80),(5.4,7.7,10.65,12.33,1.55)]):s.block('ivory_shell'+str(i),w,lo,hi,a,b)
 s.beam('muzzle_lower_lip',(10.23,-9.15),(10.53,-7.0),1.22,.25,'trim')
 s.block('muzzle_side_support',1.30,10.55,11.32,-7.00,-6.7,'shell')
 s.side('nose_carved_insert',1.64,11.15,11.35,-6.7,-4.8,'dark',.055)
 s.block('mechanism_core',1.18,10.04,10.73,-4.2,6.8,'dark')
 s.block('join_band',1.98,10.30,12.64,.05,.40,'trim')
 s.side('join_gold',1.98,10.65,12.22,.16,.29,'accent',.018)
 s.beam('stock_top',(12.03,7.7),(12.02,14.95),.90,.44,'dark')
 s.beam('stock_taper',(11.80,8.2),(12.04,14.9),.82,.22,'steel')
 s.block('stock_end',.92,9.05,12.22,14.83,15.15,'steel',.08)
 s.beam('stock_diagonal',(6.95,9.30),(10.95,14.83),.59,.42,'shell')
 s.beam('stock_diagonal_inlay',(7.25,9.75),(10.99,14.83),.62,.10,'accent')
 s.grip('grip',(10.77,8.135),(7.0,9.30),1.10,1.24,'dark')
 s.beam('grip_heel',(7.00,9.30),(6.65,9.67),1.08,.23,'steel')
 s.beam('trigger_guard_front',(10.12,4.76),(8.95,5.2),.25,.19,'steel')
 s.beam('trigger_guard_floor',(8.95,5.2),(8.95,8.30),.25,.19,'steel')
 s.beam('trigger',(10.25,6.65),(9.49,6.42),.18,.18,'dark')
 s.mag(1.75,4.6,5.6,10.25,1.15,0,'dark')
 s.optic(4.12,12.56,.38,.83)
 return s

def insidious():
 s=Shape()
 s.block('muzzle_chin',1.52,10.48,11.12,-6.8,-5.85,'steel')
 s.tube('muzzle',.47,11.45,-6.8,-6.05,'steel',.18)
 s.block('lower_rail',1.36,10.75,11.25,-6.05,4.0,'dark')
 # The wedge is a long inclined roof with thin side blades, not tall uniform body segments.
 s.beam('wedge_roof',(11.52,-5.9),(13.10,3.9),1.33,.26,'shell')
 for side in [-1,1]:
  for i,(a,b,hi) in enumerate([(-5.9,-4.6,11.72),(-4.6,-3.2,11.94),(-3.2,-1.8,12.16),(-1.8,-.4,12.39),(-.4,1.0,12.61),(1.0,2.4,12.83),(2.4,3.9,13.07)]):
   x=8+side*.72;s.box('wedge_side'+str(side)+'_'+str(i),x-.12,x+.12,11.18,hi,a,b,'shell')
 s.block('central_shoulder',1.79,10.95,13.17,3.9,6.72,'shell')
 s.block('rear_receiver',1.99,10.60,13.24,6.72,10.45,'shell')
 s.block('rear_top',1.84,11.3,13.23,10.45,17.85,'shell')
 s.block('rear_butt',1.79,7.0,11.30,16.7,17.85,'shell')
 s.block('rear_bay_frame',1.65,7.0,7.4,12.8,16.7,'dark')
 s.side('hanging_side_plate',2.0,8.88,12.72,11.55,16.64,'shell',.16)
 s.side('side_plate_hinge',2.24,11.65,12.28,10.4,11.6,'steel',.12)
 s.block('side_plate_cross_hinge',2.50,11.75,12.05,10.4,10.8,'steel',.08)
 s.side('side_plate_latch',2.26,10.95,11.70,10.74,11.20,'dark',.10)
 s.side('plate_lower_rail',2.04,8.73,8.92,12.25,16.0,'steel',.10)
 s.side('insert_recess',2.0,11.50,13.15,7.02,10.18,'dark',.06)
 s.side('red_triangular_insert',2.13,11.69,12.86,7.05,10.02,'accent',.035)
 s.side('organic_rear_panel',2.0,12.80,13.20,7.15,9.0,'steel',.11)
 s.mag(10.3,13.0,6.6,11.7,1.25,0,'dark')
 s.grip('grip',(10.97,7.267),(6.97,8.30),1.22,1.40)
 s.beam('lower_frame_front',(11.00,4.54),(7.06,5.63),.36,.26,'steel')
 s.beam('lower_frame_floor',(7.06,5.63),(7.06,8.32),.36,.26,'steel')
 s.beam('lower_frame_rear',(7.06,8.32),(10.70,9.65),.36,.26,'steel')
 s.beam('trigger',(11.04,6.18),(9.73,5.93),.18,.18,'dark')
 points=[(10.50,-5.95),(9.96,-3.7),(9.52,-1.0),(9.25,1.65),(9.25,3.75),(9.60,4.90)]
 for i,(a,b) in enumerate(zip(points,points[1:])):s.beam('lower_bow'+str(i),a,b,.18,.15,'trim')
 for i in range(16):
  z=-5.65+i*.27;h=11.55+(z+5.65)*.10
  s.beam('barrel_fin'+str(i),(h,z),(h+.65,z+.28),1.40,.13,'steel')
 s.rail('rear_track',11.65,16.75,13.24,1.22,.54)
 # Square wire optic and independent forward wire sight.
 for z,y,w,h in [(5.4,13.35,1.25,1.2),(.35,12.8,.95,.67)]:
  s.box('sight_saddle'+str(z),8-w/2-.06,8+w/2+.06,y-.40,y+.02,z-.06,z+.18,'dark')
  for side in [-1,1]:s.box('sight_post'+str(z)+str(side),8+side*w/2-.045,8+side*w/2+.045,y,y+h,z,z+.10,'trim')
  s.box('sight_bridge'+str(z),8-w/2,8+w/2,y+h-.08,y+h,z,z+.10,'trim')
 s.box('optic_rear_shield',7.35,8.65,13.35,13.99,6.25,6.55,'shell')
 s.box('optic_shield_foot',7.65,8.35,13.12,13.45,6.25,6.55,'dark')
 return s

def phyllotactic_spiral():
 s=Shape()
 s.tube('muzzle',.48,11.48,-6.72,-6.23,'steel',.16)
 s.block('barrel_front',1.50,10.76,12.14,-6.23,-3.2,'steel')
 s.block('barrel_rear',1.62,10.76,12.27,-3.2,.4,'steel')
 s.side('barrel_long_groove',1.62,11.02,11.20,-5.75,.25,'dark',.05)
 s.block('barrel_top_rail',.94,12.14,12.44,-5.75,.4,'dark')
 s.block('receiver_front',1.85,10.49,12.45,.4,2.9)
 s.block('receiver_main',1.93,10.40,12.52,2.9,7.9)
 s.side('receiver_inset',1.94,10.83,12.02,3.2,7.55,'dark',.035)
 s.side('receiver_panel',2.0,10.98,11.86,3.4,7.35,'shell',.05)
 for i,z in enumerate([.55,1.2,1.85]):
  s.side('upper_module'+str(i),1.90,12.07,12.65,z,z+.55,'steel',.09)
 s.block('lower_front',1.46,9.27,10.23,-4.25,1.85,'accent')
 s.tube('underbarrel_muzzle',.43,9.77,-4.58,-4.25,'steel',.15)
 s.side('lower_module_panel',1.47,9.44,10.03,-3.9,1.5,'dark',.05)
 s.block('lower_support',.85,10.23,10.76,.15,1.7,'dark')
 s.block('lower_receiver',1.42,9.51,10.40,2.3,6.60,'dark')
 s.block('stock_socket',1.69,10.63,12.28,7.9,9.53)
 s.block('stock_beam',1.14,11.24,12.19,9.53,17.05)
 s.block('stock_butt',1.48,8.68,12.38,17.05,17.63,'accent')
 s.beam('stock_lower_brace',(9.03,13.30),(10.53,14.25),.56,.25,'accent')
 s.beam('stock_lower_tail',(10.53,14.25),(10.53,17.08),.56,.25,'accent')
 s.block('rear_magwell',1.82,9.33,11.24,10.58,13.42,'shell')
 for i in range(5):s.side('magwell_fin'+str(i),1.84,9.72+i*.28,9.86+i*.28,10.58,13.43,'steel',.12)
 s.mag(11.0,13.3,6.0,10.7,1.3,0,'accent')
 s.grip('grip',(10.57,7.645),(6.9,8.80),1.2,1.25,'accent')
 s.beam('grip_heel',(6.89,8.80),(6.49,9.18),1.16,.24,'steel')
 s.beam('trigger_front',(10.0,4.64),(8.88,4.9),.28,.22,'steel')
 s.beam('trigger_floor',(8.88,4.9),(8.88,6.85),.28,.22,'steel')
 s.beam('trigger',(10.05,6.25),(9.37,6.05),.20,.20,'steel')
 s.rail('receiver_top',2.8,5.05,12.60,.92)
 s.optic(5.10,12.70,.60,1.12)
 return s

BUILDERS={w:globals()[w] for w in IDS}

def krait_fidelity():
 """Source-space silhouette reconstruction; one uniform source-image mapping for every part.
 Source orthographic is actual blend neutral image, 1200x700, length 1091 pixels.
 Keep barrel axis at existing 10.86; do not warp donor grips or compress the stock for ADS.
 """
 s=Shape();unit=25.15/1091.0
 def cv(p):return (9.55+(350-p[1])*unit,-9.5+(p[0]-54.5)*unit)
 def poly(n,points,width,role='shell',step=.15,bevel=True):
  ps=[cv(p) for p in points];zs=[p[1] for p in ps];lo,hi=min(zs),max(zs)
  cuts=sorted(set([lo,hi]+zs+[lo+i*step for i in range(1,math.ceil((hi-lo)/step))]));count=0
  for a,b in zip(cuts,cuts[1:]):
   if b-a<.0001:continue
   z=(a+b)/2;ys=[]
   for p,q in zip(ps,ps[1:]+ps[:1]):
    if min(p[1],q[1])<=z<max(p[1],q[1]):ys.append(p[0]+(q[0]-p[0])*(z-p[1])/(q[1]-p[1]))
   ys.sort()
   for y0,y1 in zip(ys[::2],ys[1::2]):
    if y1-y0<.003:continue
    w=width(z) if callable(width) else width
    if bevel:s.block(n+str(count),w,y0,y1,a,b,role,.075)
    else:s.box(n+str(count),8-w/2,8+w/2,y0,y1,a,b,role)
    count+=1
 def beam(n,p,q,w,t,role='shell'):s.beam(n,cv(p),cv(q),w,t,role)
 def rect(n,x0,y0,x1,y1,w,role='shell',bevel=True):poly(n,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],w,role,step=100,bevel=bevel)
 # Suppressor length and receiver throat are measured from the neutral source, not donor proportions.
 for n,px0,px1,r,mat in [('suppressor_nose',55,75,.43,'steel'),('suppressor_shell',75,255,.48,'dark'),('suppressor_rear',255,339,.57,'dark'),('barrel_exposed',339,440,.23,'steel')]:
  z0=cv((px0,293))[1];z1=cv((px1,293))[1];s.tube(n,r,cv((0,293))[0],z0,z1,mat,.13)
 for i,(px0,px1,r) in enumerate([(340,354,.48),(368,385,.60),(420,439,.61)]):s.tube('throat_collar'+str(i),r,cv((0,293))[0],cv((px0,0))[1],cv((px1,0))[1],'steel',.15)
 beam('collar_upper_tie',(370,268),(436,265),.85,.16,'steel')
 beam('collar_lower_tie',(370,319),(436,322),.85,.16,'steel')
 poly('upper_canopy',[(350,215),(459,215),(458,252),(440,279),(394,259),(389,245),(352,231)],1.51,'shell',.18)
 poly('receiver_crown',[(458,214),(566,211),(658,229),(751,231),(824,239),(850,246),(800,278),(439,279)],1.80,'shell',.19)
 poly('receiver_lower',[(439,279),(800,278),(850,284),(895,298),(894,326),(847,330),(775,329),(740,340),(580,345),(436,342)],1.53,'dark',.19,False)
 # Stock crown visibly dips beside receiver, then rises sharply; lower heel sweeps under the rear shell.
 poly('stock_flared',[(810,239),(825,217),(855,215),(938,204),(1104,173),(1127,157),(1118,193),(1118,321),(1147,339),(1146,371),(1092,383),(915,444),(891,389),(850,330),(814,328),(793,289)],lambda z:1.49+max(0,min(1,(z-8)/7.65))*.52,'shell',.18)
 poly('stock_cheek_lip',[(749,231),(825,217),(855,215),(951,202),(1103,174),(1106,191),(953,218),(856,238),(825,245)],1.59,'steel',.20,False)
 # Recess channel with a separate moving carrier, positioned against the actual source geometry.
 rect('carrier_channel',492,280,897,317,1.70,'recess')
 for sd in [-1,1]:
  a=cv((500,286));b=cv((891,310));cx=8+sd*.89
  s.box('mag_charge_bar_'+str(sd),cx-.05,cx+.05,b[0],a[0],a[1],b[1],'accent')
  a=cv((500,286));b=cv((558,310));s.box('mag_charge_latch_'+str(sd),cx-.08,cx+.08,b[0],a[0],a[1],b[1],'steel')
 rect('receiver_lower_rail',440,321,778,338,1.74,'steel')
 poly('forward_shelf',[(304,333),(438,333),(438,350),(581,352),(580,382),(465,388),(443,399),(419,389),(330,369),(244,392),(276,357)],1.39,'shell',.20,False)
 # Actual fore grip aperture: round opening framed by a swept horn rather than a rectangular loop.
 center=cv((383,397))
 for sd in [-1,1]:s.eye('fore_aperture_'+str(sd)+'_',8+sd*.37,center[0],center[1],.75,.17,'dark',.74)
 poly('fore_grip_sculpt',[(422,383),(457,391),(451,418),(477,444),(493,472),(493,491),(422,544),(446,504),(418,480),(423,465),(403,451),(413,438),(397,425),(404,411),(421,408)],1.20,'rubber',.12)
 poly('rear_grip_sculpt',[(700,346),(748,342),(748,372),(774,408),(806,423),(806,486),(771,502),(755,542),(757,496),(739,474),(732,456),(716,452),(710,428),(691,421),(701,405),(676,403),(683,381),(687,371)],1.26,'rubber',.12)
 # Distinct curved low sight spine, including small front/rear lips; source has no tall generic tube optic.
 poly('sight_spine',[(538,184),(553,159),(561,178),(584,187),(719,200),(722,208),(575,205),(550,201),(541,212)],.62,'dark',.16,False)
 rect('front_sight_step',426,195,461,207,.74,'steel')
 rect('front_sight_foot',420,207,469,215,.87,'dark')
 # The small trigger is inside the sculpted grip neck; no invented hanging rectangular guard.
 beam('rear_trigger',(692,359),(679,389),.21,.18,'steel')
 return s

def krait_fidelity_volumes():
 """Second source-space draft: semantic compound solids, no thin silhouette tracing."""
 s=Shape();u=25.15/1091
 def cv(p):return (9.55+(350-p[1])*u,-9.5+(p[0]-54.5)*u)
 def box(n,p,q,w,m='shell'):
  a,b=cv(p),cv(q);s.block(n,w,min(a[0],b[0]),max(a[0],b[0]),min(a[1],b[1]),max(a[1],b[1]),m,.10)
 def beam(n,a,b,w,t,m='shell',x=8):s.beam(n,cv(a),cv(b),w,t,m,x)
 def rounded(n,a,b,w,t,m='shell'):
  # Full-volume cross-section: wider palm side cheeks surround a narrower central web.
  beam(n+'_web',a,b,max(.04,w-.20),t,m)
  if w>.24:
   beam(n+'_left',a,b,.10,max(.05,t-.20),m,8-w/2+.05)
   beam(n+'_right',a,b,.10,max(.05,t-.20),m,8+w/2-.05)
 def inset(n,points,width):
  # A recessed solid field behind the semantic rim. Its contour edge is covered by the rim;
  # it is not an outer-shell stack or an alpha plate.
  ps=[cv(p) for p in points];zs=[p[1] for p in ps];lo,hi=min(zs),max(zs);cuts=sorted(set(zs+[lo+i*.22 for i in range(math.ceil((hi-lo)/.22))]+[hi]))
  for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
   if b-a<.0001:continue
   z=(a+b)/2;ys=[]
   for p,q in zip(ps,ps[1:]+ps[:1]):
    if min(p[1],q[1])<=z<max(p[1],q[1]):ys.append(p[0]+(q[0]-p[0])*(z-p[1])/(q[1]-p[1]))
   if len(ys)>1:
    ww=width(z) if callable(width) else width;s.box(n+str(i),8-ww/2,8+ww/2,min(ys),max(ys),a,b,'shell')
 # Suppressor has a fuller rear collar and a reduced exposed barrel within separate supporting hoops.
 for n,px0,px1,r,m in [('suppressor_nose',55,75,.43,'steel'),('suppressor_shell',75,255,.48,'dark'),('suppressor_rear',255,339,.57,'dark'),('barrel_exposed',339,440,.23,'steel')]:
  s.tube(n,r,cv((0,293))[0],cv((px0,0))[1],cv((px1,0))[1],m,.13)
 for i,(a,b,r) in enumerate([(340,354,.48),(368,385,.60),(420,439,.61)]):s.tube('throat_collar'+str(i),r,cv((0,293))[0],cv((a,0))[1],cv((b,0))[1],'steel',.15)
 beam('collar_upper_tie',(370,268),(436,265),.85,.16,'steel')
 beam('collar_lower_tie',(370,319),(436,322),.85,.16,'steel')
 # Broad canopy and diagonal throat are distinct from the narrower mechanism underneath.
 rounded('canopy_roof',(351,222),(457,222),1.52,.34)
 rounded('canopy_chin',(375,238),(421,256),1.45,.36)
 rounded('diagonal_throat',(452,227),(427,273),1.76,.44)
 box('receiver_front_bulk',(452,225),(568,280),1.76)
 box('receiver_mid_bulk',(568,239),(800,280),1.50)
 box('receiver_rear_bulk',(800,247),(850,291),1.70)
 rounded('receiver_crown_front',(460,218),(565,218),1.65,.28)
 rounded('receiver_crown_fall',(565,219),(656,236),1.60,.27)
 rounded('receiver_crown_tail',(656,236),(821,244),1.48,.24)
 # Upper central recess is bounded by raised shoulders, leaving a visible depth change from front/rear.
 box('receiver_top_recess',(580,228),(750,240),1.0,'recess')
 box('receiver_lower_core',(437,280),(850,327),1.30,'dark')
 box('receiver_magwell_transition',(850,290),(896,326),1.43,'dark')
 box('lower_rail',(440,321),(778,340),1.76,'steel')
 # Two long mechanical side faces with genuinely recessed carrier field.
 for sd in [-1,1]:
  x=8+sd*.79
  beam('upper_panel_shoulder'+str(sd),(462,239),(792,259),.15,.29,'shell',x)
  a=cv((492,282));b=cv((897,317));s.box('carrier_recess'+str(sd),x-.05,x+.05,b[0],a[0],a[1],b[1],'recess')
  cx=8+sd*.89;a=cv((500,287));b=cv((891,311));s.box('mag_charge_bar_'+str(sd),cx-.06,cx+.06,b[0],a[0],a[1],b[1],'accent')
  a=cv((500,286));b=cv((558,312));s.box('mag_charge_latch_'+str(sd),cx-.10,cx+.10,b[0],a[0],a[1],b[1],'steel')
 # Stock: narrow central field, heavy outer shoulder rim, rising concave crown and swept heel.
 inset('stock_recessed_field',[(814,246),(852,233),(1108,186),(1114,351),(919,422),(897,383),(850,327),(813,327)],lambda z:1.18+.25*max(0,min(1,(z-8)/7.6)))
 rounded('stock_throat_lower',(848,324),(897,389),1.78,.44)
 rounded('stock_lower_heel',(897,389),(919,430),1.91,.50)
 rounded('stock_bottom_rim',(919,430),(1118,361),2.01,.43)
 rounded('stock_rear_shoulder',(1118,191),(1118,360),2.08,.46)
 rounded('stock_crown_dip',(811,238),(852,224),1.49,.30)
 rounded('stock_crown_rise1',(852,224),(942,208),1.60,.38)
 rounded('stock_crown_rise2',(942,208),(1030,190),1.76,.42)
 rounded('stock_crown_rise3',(1030,190),(1118,174),1.94,.45)
 rounded('stock_crown_tip',(1118,174),(1127,159),1.95,.18)
 # Recessed side field follows the slope, set inboard of the shoulder rim instead of a flat filled outline.
 for sd in [-1,1]:
  x=8+sd*.74
  beam('stock_recess_upper'+str(sd),(857,247),(1099,206),.10,.14,'dark',x)
  beam('stock_recess_lower'+str(sd),(900,386),(1099,327),.10,.14,'dark',x)
  beam('stock_recess_back'+str(sd),(1099,206),(1099,327),.10,.14,'dark',x)
 # Fore shelf, swept horn, and circular aperture; no filled side plate closes the hole.
 rounded('fore_shelf',(306,343),(438,343),1.43,.39)
 rounded('fore_shelf_rear',(438,357),(579,367),1.42,.43)
 rounded('fore_horn_rise',(247,389),(304,344),1.12,.20)
 rounded('fore_horn_brow',(293,369),(353,385),1.22,.29)
 center=cv((383,397));s.eye('fore_aperture_',8,center[0],center[1],.73,.18,'dark',1.15)
 rounded('fore_aperture_neck',(414,395),(438,400),1.24,.38)
 # Palm bulges and finger facets are full transverse solids with different widths; hooks taper in 3D.
 for n,a,b,w,t in [
  ('front_neck',(435,397),(443,424),1.07,.55),('front_palm_upper',(443,424),(459,454),1.34,.83),
  ('front_palm_lower',(459,454),(468,479),1.43,.93),('front_heel',(468,479),(449,506),1.19,.58),
  ('front_hook',(449,506),(424,538),.56,.20),('front_hook_tip',(424,538),(421,544),.18,.08),
  ('rear_neck',(720,354),(733,384),1.12,.58),('rear_palm_upper',(733,384),(759,420),1.37,.96),
  ('rear_palm_lower',(759,420),(783,462),1.52,1.02),('rear_heel',(783,462),(776,491),1.37,.69),
  ('rear_hook',(776,491),(760,520),.71,.26),('rear_hook_tip',(760,520),(755,541),.24,.11)]:rounded(n,a,b,w,t,'rubber')
 for n,a,b,w,t in [('front_finger1',(432,418),(410,419),1.20,.30),('front_finger2',(446,444),(416,447),1.30,.35),('front_finger3',(459,471),(424,475),1.33,.32),('rear_finger1',(731,386),(686,395),1.20,.31),('rear_finger2',(745,414),(705,424),1.35,.34),('rear_finger3',(764,444),(724,453),1.40,.35)]:rounded(n,a,b,w,t,'rubber')
 # Low source sight spine with real base attachment, a raised front lip and tapering rear leg.
 rounded('sight_base',(541,210),(720,210),.70,.18,'dark')
 rounded('sight_front_lip',(541,193),(555,170),.65,.18,'dark')
 rounded('sight_front_curve',(555,170),(582,190),.63,.18,'dark')
 rounded('sight_rear_spine',(582,190),(720,205),.57,.16,'dark')
 box('front_sight_step',(426,195),(461,207),.74,'steel')
 box('front_sight_foot',(420,207),(469,215),.87,'dark')
 beam('rear_trigger',(692,359),(679,389),.21,.18,'steel')
 return s

def krait_fidelity_loft():
 """Authored semantic closed lofts, preserving source transverse and side sections."""
 base=krait_fidelity_volumes();s=Shape()
 keep=('suppressor','barrel_exposed','throat_collar','collar_','lower_rail','carrier_recess','mag_charge','front_sight','rear_trigger')
 for e in base.e:
  if e['name'].startswith(keep):s.e.append(e);s.roles[e['name']]=base.roles[e['name']]
 spec=importlib.util.spec_from_file_location('owned_tri_adapter',ROOT/'scripts/mesh/native_triangle_elements_w115.py');tri=importlib.util.module_from_spec(spec);spec.loader.exec_module(tri)
 u=25.15/1091
 def p(x,px,py):return (8+x,9.55+(350-py)*u,-9.5+(px-54.5)*u)
 s.authored_triangles=[]
 def triangle(n,a,b,c,m):
  try:
   pieces=None
   for o,aa,bb in [(a,b,c),(b,c,a),(c,a,b)]:
    eu,ev=tri.sub(aa,o),tri.sub(bb,o)
    if tri.norm(eu)>1e-8 and tri.norm(ev)>1e-8 and abs(tri.dot(eu,ev))<1e-7:
     uu,vv=tri.unit(eu),tri.unit(ev);pieces=[dict(origin=o,u=uu,v=vv,width=tri.norm(eu),height=tri.norm(ev),rotation=tri.euler_zyx(uu,vv,tri.unit(tri.cross(uu,vv))))];break
   if pieces is None:pieces=tri.split_triangle([a,b,c])
  except ValueError:return
  s.authored_triangles.append({'name':n,'vertices':[a,b,c],'role':m})
  for j,part in enumerate(pieces):
   assert max(math.dist(tri.rotate((1,0,0),part['rotation']),part['u']),math.dist(tri.rotate((0,1,0),part['rotation']),part['v']))<1e-6,(n,part)
   name=n+'_'+str(j);e=tri.to_element(part,name,[0,0,16,16]);s.e.append(e);s.roles[name]=m
 def loft(n,rings,m='shell'):
  # Adjacent rings share exactly the same vertices; every authored shell is closed.
  for k,(a,b) in enumerate(zip(rings,rings[1:])):
   for j in range(len(a)):
    q=(j+1)%len(a);triangle(f'{n}_{k}_{j}a',a[j],a[q],b[q],m);triangle(f'{n}_{k}_{j}b',a[j],b[q],b[j],m)
  for end,ring in [(0,rings[0]),(1,rings[-1])]:
   for j in range(1,len(ring)-1):triangle(f'{n}_cap{end}_{j}',ring[0],ring[j],ring[j+1],m)
 def section(px,top,bottom,width=1.67,tip=.45):
  # Thin top crown, sloping shoulder, broad side field, lower bevel.
  shoulder=min(top+38,bottom-13);lower=bottom-8
  return [p(-tip/2,px,top),p(tip/2,px,top),p(width/2,px,shoulder),p(width*.44,px,bottom),p(-width*.44,px,bottom),p(-width/2,px,shoulder)]
 def rectsection(px,top,bottom,width,tip=None):
  return [p(-width/2,px,top),p(width/2,px,top),p(width/2,px,bottom),p(-width/2,px,bottom)]
 # Two shouldered banks leave a genuine recessed upper mechanism channel.
 for sd in [-1,1]:
  rings=[]
  for x,t,b,w in [(438,217,280,1.32),(560,207,280,2.02),(790,214,280,1.67)]:
   rings.append([p(sd*.36,x,t),p(sd*w/2,x,t+38),p(sd*w*.44,x,b),p(sd*.30,x,t+8)])
  loft('receiver_upper_bank'+str(sd),rings)
 q0,q1=p(0,438,225),p(0,790,280);s.box('receiver_upper_channel_floor',7.70,8.30,q1[1],q0[1],q0[2],q1[2],'recess')
 loft('receiver_lower',[rectsection(x,278,b,w) for x,b,w in [(438,341,1.67),(665,357,1.67),(775,333,1.67),(895,326,1.67)]],'dark')
 # Fore canopy folds into a diagonal throat, not a hanging disconnected slab.
 loft('front_canopy',[rectsection(x,t,b,w) for x,t,b,w in [(351,215,232,1.30),(405,215,260,1.47),(438,215,273,1.53),(461,215,248,1.65)]])
 # Stock shell with an authored recessed side field and raised shoulder rim.
 outer=[(790,214,.72),(825,217,.55),(855,214,.42),(965,196,.36),(1030,189,.33),(1104,175,.28),(1127,157,.24),(1118,318,1.67),(1145,341,1.765),(1145,397,1.765),(916,443,1.765),(895,396,1.765),(850,331,1.67),(790,331,1.67)]
 inner=[(814,250),(840,249),(870,244),(965,228),(1012,257),(1082,257),(1082,257),(1082,316),(947,354),(936,378),(894,389),(870,318),(814,313),(814,313)]
 def cap_indices(points):
  ids=list(range(len(points)));area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]));sgn=1 if area>0 else -1;out=[]
  def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  # Drop coincident authored contour points only from the cap; perimeter correspondence remains intact.
  ids=[i for i in ids if points[i]!=points[i-1]]
  while len(ids)>3:
   for k,i in enumerate(ids):
    a,b,c=ids[k-1],i,ids[(k+1)%len(ids)]
    if sgn*cross(points[a],points[b],points[c])<=1e-7:continue
    inside=False
    for j in ids:
     if j in (a,b,c):continue
     if all(sgn*cross(points[v],points[w],points[j])>=-1e-7 for v,w in [(a,b),(b,c),(c,a)]):inside=True;break
    if not inside:out.append((a,b,c));ids.pop(k);break
   else:raise ValueError('authored stock cap triangulation')
  out.append(tuple(ids));return out
 out_rings=[]
 for sd in [-1,1]:
  oo=[p(sd*w/2,x,y) for x,y,w in outer];ii=[p(sd*.79,x,y) for x,y in inner];out_rings.append(oo)
  for j in range(len(oo)):
   k=(j+1)%len(oo);triangle(f'stock_rim{sd}_{j}a',oo[j],oo[k],ii[k],'shell');triangle(f'stock_rim{sd}_{j}b',oo[j],ii[k],ii[j],'shell')
  for j,(a,b,c) in enumerate(cap_indices(inner)):triangle(f'stock_recess{sd}_{j}',ii[a],ii[b],ii[c],'shell')
 for j in range(len(outer)):
  k=(j+1)%len(outer);a,b=out_rings;triangle(f'stock_edge{j}a',a[j],a[k],b[k],'shell');triangle(f'stock_edge{j}b',a[j],b[k],b[j],'shell')
 # Swept fore horn, aperture frame and neck: a closed changing cross-section lower shelf.
 loft('fore_shelf',[rectsection(x,t,b,w,tip) for x,t,b,w,tip in [(245,389,391,.09,.04),(280,355,376,.85,.40),(304,333,369,1.44,.90),(383,333,365,1.48,1.0),(420,333,389,1.48,1.0),(438,333,395,1.48,1.0),(465,350,388,1.30,.85),(580,351,359,1.12,.9)]])
 # Open fore aperture: paired curved sides, continuously lofted from top to lower tip.
 for tag,points in [('front',[(383,367,.70),(364,372,.65),(354,384,.56),(353,400,.46),(364,416,.30),(367,425,.15)]),('rear',[(383,367,.70),(398,371,.68),(410,384,.64),(412,400,.55),(401,416,.38),(385,425,.20)])]:
  for j,(a,b) in enumerate(zip(points,points[1:])):
   pa,pb=p(0,a[0],a[1]),p(0,b[0],b[1]);s.beam('fore_aperture_'+tag+str(j),(pa[1],pa[2]),(pb[1],pb[2]),(a[2]+b[2])/2,.22,'dark')
 def grip(n,stations):
  rings=[]
  for py,front,back,w in stations:
   dz=(back-front)*.18
   rings.append([p(0,front,py),p(w/2,front+dz,py),p(w/2,back-dz,py),p(0,back,py),p(-w/2,back-dz,py),p(-w/2,front+dz,py)])
  loft(n,rings,'rubber')
 grip('front_grip',[(386,422,454,.64),(410,403,455,.70),(425,398,466,.78),(438,414,477,.90),(451,404,487,.95),(465,424,493,.90),(480,419,493,.80),(495,443,483,.74),(510,442,464,.64),(542,422,424,.08)])
 grip('rear_grip',[(347,700,747,.74),(373,686,751,.80),(402,677,769,.81),(410,703,777,.85),(425,692,807,.97),(452,717,807,.98),(475,741,807,.86),(494,758,791,.66),(541,755,757,.08)])
 fin=[(553,180),(553,204),(720,207)];loft('sight_fin',[[p(sd*.31,*q) for q in fin] for sd in [-1,1]],'dark')
 for j,(a,b) in enumerate([((541,184),(553,163)),((553,163),(562,182))]):
  aa,bb=p(0,*a),p(0,*b);s.beam('sight_front_hook'+str(j),aa[1:],bb[1:],.62,.17,'dark')
 return s

FIDELITY_FRAME={'krait':(25.15,-9.5,9.55),'rufuss_fury':(25.30,-9.95,9.83),'origin_story':(24.18,-9,9.458),'age_old_bond':(24.61,-9.46,9.852),'insidious':(24.65,-6.8,10.727),'phyllotactic_spiral':(24.35,-6.72,9.761)}
class SourceShape(Shape):
 """Small owned authoring helper: source-space cuboids and closed semantic lofts."""
 def __init__(self,w):
  super().__init__();self.w=w;self.L,self.z0,self.ym=FIDELITY_FRAME[w];self.u=self.L/1091;self.authored_triangles=[]
  spec=importlib.util.spec_from_file_location('owned_triangle_adapter',ROOT/'scripts/mesh/native_triangle_elements_w115.py');self.tri=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.tri)
 def point(self,x,px,py):return (8+x,self.ym+(350-py)*self.u,self.z0+(px-54.5)*self.u)
 def boxp(self,n,a,b,w,m='shell',bevel=.10):
  p,q=self.point(0,*a),self.point(0,*b);self.block(n,w,min(p[1],q[1]),max(p[1],q[1]),min(p[2],q[2]),max(p[2],q[2]),m,bevel)
 def beamp(self,n,a,b,w,t,m='shell',x=0):
  p,q=self.point(x,*a),self.point(x,*b);self.beam(n,p[1:],q[1:],w,t,m,8+x)
 def tubep(self,n,a,b,py,r,m='steel',wall=.13):self.tube(n,r,self.point(0,0,py)[1],self.point(0,a,0)[2],self.point(0,b,0)[2],m,wall)
 def triangle(self,n,a,b,c,m='shell'):
  tri=self.tri
  try:
   parts=None
   for o,aa,bb in [(a,b,c),(b,c,a),(c,a,b)]:
    eu,ev=tri.sub(aa,o),tri.sub(bb,o)
    if tri.norm(eu)>1e-8 and tri.norm(ev)>1e-8 and abs(tri.dot(eu,ev))<1e-7:
     u,v=tri.unit(eu),tri.unit(ev);parts=[dict(origin=o,u=u,v=v,width=tri.norm(eu),height=tri.norm(ev),rotation=tri.euler_zyx(u,v,tri.unit(tri.cross(u,v))))];break
   if parts is None:parts=tri.split_triangle([a,b,c])
  except ValueError:return
  self.authored_triangles.append(dict(name=n,vertices=[a,b,c],role=m))
  for j,part in enumerate(parts):
   assert max(math.dist(tri.rotate((1,0,0),part['rotation']),part['u']),math.dist(tri.rotate((0,1,0),part['rotation']),part['v']))<1e-6
   name=n+'_'+str(j);self.e.append(tri.to_element(part,name,[0,0,16,16]));self.roles[name]=m
 def loft(self,n,rings,m='shell'):
  for k,(a,b) in enumerate(zip(rings,rings[1:])):
   for j in range(len(a)):
    q=(j+1)%len(a);self.triangle(f'{n}_{k}_{j}a',a[j],a[q],b[q],m);self.triangle(f'{n}_{k}_{j}b',a[j],b[q],b[j],m)
  for end,ring in enumerate([rings[0],rings[-1]]):
   for j in range(1,len(ring)-1):self.triangle(f'{n}_cap{end}_{j}',ring[0],ring[j],ring[j+1],m)
 def section(self,px,top,bottom,w,tip=.5):
  shoulder=top+(bottom-top)*.45
  return [self.point(-w*tip/2,px,top),self.point(w*tip/2,px,top),self.point(w/2,px,shoulder),self.point(w*.38,px,bottom),self.point(-w*.38,px,bottom),self.point(-w/2,px,shoulder)]
 def shell(self,n,stations,m='shell'):self.loft(n,[self.section(*st) for st in stations],m)
 def griploft(self,n,stations,m='rubber'):
  rings=[]
  for py,front,back,w in stations:
   dz=(back-front)*.18;rings.append([self.point(0,front,py),self.point(w/2,front+dz,py),self.point(w/2,back-dz,py),self.point(0,back,py),self.point(-w/2,back-dz,py),self.point(-w/2,front+dz,py)])
  self.loft(n,rings,m)
 def panel(self,n,points,w,m='shell'):
  # Closed source-shaped plate, with real concavities preserved in both side caps.
  ids=list(range(len(points)));area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]));sgn=1 if area>0 else -1;caps=[]
  def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  while len(ids)>3:
   for k,i in enumerate(ids):
    a,b,c=ids[k-1],i,ids[(k+1)%len(ids)]
    if sgn*cross(points[a],points[b],points[c])<=1e-7:continue
    if any(all(sgn*cross(points[v],points[q],points[j])>=-1e-7 for v,q in [(a,b),(b,c),(c,a)]) for j in ids if j not in (a,b,c)):continue
    caps.append((a,b,c));ids.pop(k);break
   else:raise ValueError((n,'profile is not simple'))
  caps.append(tuple(ids));rings=[[self.point(sd*w/2,*p) for p in points] for sd in [-1,1]]
  for k,ring in enumerate(rings):
   for j,(a,b,c) in enumerate(caps):self.triangle(f'{n}_cap{k}_{j}',ring[a],ring[b],ring[c],m)
  for j in range(len(points)):
   k=(j+1)%len(points);a,b=rings;self.triangle(f'{n}_edge{j}a',a[j],a[k],b[k],m);self.triangle(f'{n}_edge{j}b',a[j],b[k],b[j],m)

def origin_story_fidelity():
 s=SourceShape('origin_story')
 s.tubep('muzzle',55,132,275,.45,'dark');s.tubep('suppressor',132,253,275,.53,'steel');s.tubep('barrel_collar',253,281,275,.55,'dark');s.tubep('barrel_front_rim',126,135,275,.57,'steel',.08)
 s.boxp('receiver_core',(283,242),(952,316),1.00,'dark')
 s.shell('receiver_front',[(283,250,315,1.42,.65),(323,242,320,1.70,.65),(535,241,318,1.70,.65)])
 s.boxp('receiver_upper_lip',(550,241),(952,251),1.70,'shell',.05);s.boxp('receiver_lower_lip',(550,298),(952,318),1.70,'shell',.06)
 s.boxp('receiver_recess_field',(550,253),(951,297),1.04,'recess',.03)
 s.panel('receiver_channel_nose',[(535,241),(570,241),(570,251),(559,253),(553,261),(550,276),(553,289),(558,296),(568,300),(568,318),(535,318)],1.70,'shell')
 for sd in [-1,1]:
  x=8+sd*.735;a=s.point(0,611,267);b=s.point(0,630,283);s.box('selector_'+str(sd),x-.035,x+.035,b[1],a[1],a[2],b[2],'steel')
  x=8+sd*.74;a=s.point(0,647,269);b=s.point(0,670,281);s.box('receiver_port_'+str(sd),x-.035,x+.035,b[1],a[1],a[2],b[2],'dark')
 s.boxp('top_rail',(300,229),(858,241),.82,'steel',.04)
 s.panel('top_forward_cover',[(430,240),(465,225),(541,225),(542,240)],.91)
 s.panel('rear_sight_base',[(659,229),(692,219),(840,219),(861,232),(859,239),(659,239)],.95,'dark')
 s.boxp('rear_sight',(727,215),(812,225),.65,'steel',.03);s.boxp('rear_sight_post',(791,207),(814,216),.44,'dark',.02)
 s.boxp('front_sight_base',(300,228),(370,240),.87,'dark',.03)
 s.shell('foreend',[(294,322,361,1.48,.8),(341,320,371,1.55,.8),(548,320,373,1.55,.8),(577,330,367,1.44,.8)])
 s.tubep('underbarrel_stub',217,294,346,.25,'steel',.10)
 s.panel('lower_frame_front',[(551,321),(718,324),(766,482),(734,488),(676,419),(579,364)],1.43,'shell')
 s.beamp('lower_frame_bottom',(767,476),(926,440),1.25,.27,'steel')
 s.boxp('lower_frame_top',(715,325),(869,339),1.35,'shell',.04)
 s.griploft('grip',[(336,837,873,.82),(362,849,887,.94),(386,863,904,1.00),(411,879,916,.98),(438,894,921,.86)])
 s.beamp('trigger',(820,339),(813,367),.22,.20,'steel')
 s.boxp('mag_shell',(580,365),(717,490),1.28,'dark');s.boxp('mag_floor',(582,484),(718,495),1.40,'steel',.04)
 for px in [590,663,691]:s.boxp('mag_rib'+str(px),(px,381),(px+7,490),1.35,'steel',.02)
 s.panel('stock_core',[(952,241),(1118,241),(1118,356),(1038,316),(952,316)],1.35,'shell')
 s.boxp('stock_upper_rim',(951,232),(1116,244),1.50,'steel',.04)
 s.boxp('stock_butt',(1111,219),(1143,381),1.70,'rubber');s.boxp('stock_butt_rim',(1107,227),(1116,376),1.62,'steel',.03)
 s.boxp('stock_recess',(974,252),(1032,278),1.38,'dark',.02)
 return s

def rufuss_fury_fidelity():
 s=SourceShape('rufuss_fury')
 stations=[(134,248,337,1.65,.28),(280,240,327,2.05,.28),(427,230,354,2.30,.30),(468,236,359,2.45,.29),(503,247,358,2.55,.28),(550,230,341,2.70,.27),(600,218,333,2.65,.26),(650,205,352,2.81,.26),(710,198,359,2.95,.26),(750,212,360,2.90,.28),(793,216,353,2.72,.30),(848,222,328,1.95,.34),(865,248,300,1.30,.42)]
 s.shell('organic_shell',stations)
 # Raised side streams follow the organic shell, and terminate in source forked tips.
 for sd in [-1,1]:
  for tag,stations in [('upper',[(78,264,267,.10,.55),(100,272,280,.30,.65),(138,270,291,.55,.80)]),('lower',[(70,337,340,.09,.55),(100,326,335,.30,.65),(138,316,334,.55,.80)])]:
   rings=[]
   for px,top,bottom,width,cx in stations:rings.append([s.point(sd*cx-width/2,px,top),s.point(sd*cx+width/2,px,top),s.point(sd*cx+width/2,px,bottom),s.point(sd*cx-width/2,px,bottom)])
   s.loft(f'front_tendril{sd}_{tag}',rings,'shell')
  s.beamp(f'front_tendril{sd}_middle',(56,306),(140,306),.20,.11,'shell',sd*.72)
 # Swept side wings are continuous triangular sections whose bases enter the shell.
 def surface_x(px,py):
  aa,bb=next(((a,b) for a,b in zip(stations,stations[1:]) if a[0]<=px<=b[0]),(stations[-2],stations[-1]));t=max(0,min(1,(px-aa[0])/(bb[0]-aa[0])));vals=[a+(b-a)*t for a,b in zip(aa[1:],bb[1:])];top,bottom,w,tip=vals;f=max(0,min(1,(py-top)/(bottom-top)))
  return w*(tip/2+(0.5-tip/2)*f/.45) if f<.45 else w*(.5-(.5-.38)*(f-.45)/.55)
 for sd in [-1,1]:
  for tag,path,width in [('upper',[(596,292),(655,288),(718,280),(731,258),(690,229)],10),('lower',[(651,364),(680,347),(770,347),(841,298)],10)]:
   rings=[]
   for j,(px,py) in enumerate(path):
    prev=path[max(0,j-1)];nxt=path[min(len(path)-1,j+1)];dx,dy=nxt[0]-prev[0],nxt[1]-prev[1];ll=math.hypot(dx,dy);nx,ny=-dy/ll,dx/ll;scale=.12 if j==0 else .55 if j==len(path)-1 else 1.0
    a=(px+nx*width*scale,py+ny*width*scale);b=(px-nx*width*scale,py-ny*width*scale);raise_x=.025 if j==0 else .06 if j==len(path)-1 else .24
    rings.append([s.point(sd*(surface_x(*a)-.015),*a),s.point(sd*(surface_x(px,py)+raise_x),px,py),s.point(sd*(surface_x(*b)-.015),*b)])
   for j,(a,b) in enumerate(zip(rings,rings[1:])):
    edges=[(0,1),(1,2),(2,0)] if tag=='lower' else [(0,1),(1,2)]
    for k,(i,q) in enumerate(edges):s.triangle(f'organic_wing{sd}_{tag}{j}_{k}a',a[i],a[q],b[q],'shell');s.triangle(f'organic_wing{sd}_{tag}{j}_{k}b',a[i],b[q],b[i],'shell')
   if tag=='lower':
    for k,r in enumerate([rings[0],rings[-1]]):s.triangle(f'organic_wing{sd}_{tag}_cap{k}',*r,'shell')
 s.tubep('inner_muzzle',55,155,307,.22,'dark',.09)
 s.tubep('lower_barrel',138,276,359,.27,'steel',.10)
 s.panel('lower_barrel_shroud',[(261,365),(279,342),(371,338),(416,365),(558,365),(639,389),(740,389),(740,402),(638,402),(558,382),(309,389)],1.42,'dark')
 s.boxp('receiver_rear',(752,328),(936,351),1.55,'dark',.06)
 s.boxp('trigger_bridge',(717,350),(853,374),1.37,'dark',.05);s.boxp('trigger_front_wall',(718,372),(750,409),1.28,'dark',.04);s.boxp('trigger_rear_wall',(816,371),(850,406),1.28,'dark',.04)
 s.boxp('stock_upper_slide',(852,261),(938,284),1.42,'steel',.06);s.boxp('stock_upper_rail',(938,274),(1133,284),1.35,'steel',.04)
 s.boxp('stock_core',(849,284),(1136,315),1.38,'shell',.08)
 s.boxp('stock_lower_beam',(852,315),(1098,332),1.27,'dark',.05)
 s.boxp('stock_rail',(879,254),(937,270),1.45,'steel',.04)
 s.beamp('stock_lower_brace',(999,332),(1100,383),1.15,.27,'shell')
 s.panel('stock_butt',[(1125,254),(1142,254),(1134,334),(1143,400),(1098,405),(1098,382),(1110,320)],1.49,'rubber')
 s.boxp('stock_top_ridge',(939,276),(1119,281),.63,'steel',.03)
 s.boxp('mag_shell',(618,398),(718,529),1.32,'dark');s.boxp('mag_floor',(615,521),(689,533),1.42,'steel',.04)
 for x in [625,649]:s.boxp('mag_rib'+str(x),(x,411),(x+7,519),1.40,'steel',.02)
 s.beamp('lower_frame_front',(727,405),(740,512),1.26,.25,'steel');s.beamp('lower_frame_bottom',(737,515),(922,474),1.24,.28,'steel')
 s.griploft('grip',[(351,852,885,.83),(376,847,875,.94),(404,872,902,1.06),(437,887,916,1.09),(475,900,927,.95)])
 s.beamp('trigger',(791,374),(793,399),.22,.16,'steel')
 s.boxp('sight_base',(751,204),(832,214),1.33,'dark',.03)
 s.beamp('sight_roof',(766,171),(792,171),1.27,.13,'steel');s.beamp('sight_front',(766,171),(753,202),1.26,.14,'dark');s.beamp('sight_rear',(792,171),(808,197),1.27,.14,'dark')
 # Source eyes are recessed sockets with shell backing, not through-holes.
 for sd in [-1,1]:
  for j,(px,py,r,x) in enumerate([(429,311,.21,1.11),(453,331,.30,1.08),(497,316,.14,1.18)]):
   pp=s.point(sd*x,px,py)
   for k in range(6):
    a,b=k*math.pi/3,(k+1)*math.pi/3;s.beam(f'socket{sd}_{j}_{k}',(pp[1]+(r-.045)*math.sin(a),pp[2]+(r-.045)*math.cos(a)),(pp[1]+(r-.045)*math.sin(b),pp[2]+(r-.045)*math.cos(b)),.07,.09,'recess',pp[0])
  out=[];inside=[];back=[]
  for j in range(6):
   theta=j*math.pi/3
   for arr,r,depth in [(out,18,.14),(inside,12,-.005),(back,18,-.005)]:
    px,py=794+r*math.cos(theta),252+r*math.sin(theta);arr.append(s.point(sd*(surface_x(px,py)+depth),px,py))
  for j in range(6):
   k=(j+1)%6;s.triangle(f'eye_socket{sd}_{j}a',out[j],out[k],inside[k],'recess');s.triangle(f'eye_socket{sd}_{j}b',out[j],inside[k],inside[j],'recess');s.triangle(f'eye_outer_wall{sd}_{j}a',out[j],out[k],back[k],'shell');s.triangle(f'eye_outer_wall{sd}_{j}b',out[j],back[k],back[j],'shell')
 return s

def age_old_bond_fidelity():
 s=SourceShape('age_old_bond')
 s.shell('ivory_upper_shell',[(59,231,283,2.64,.30),(210,231,289,2.90,.30),(490,232,290,2.65,.35),(551,239,294,2.28,.40)])
 s.shell('ivory_lower_lip',[(59,317,367,2.45,.50),(78,318,346,2.48,.65),(490,321,353,2.34,.65),(550,323,383,1.75,.65)])
 s.tubep('exposed_barrel',55,210,300,.29,'dark',.10)
 s.boxp('fore_inner_core',(210,281),(550,327),2.38,'dark',.08)
 s.shell('receiver',[(550,239,335,2.13,.5),(699,232,334,1.85,.5),(772,235,320,1.64,.5)])
 s.panel('magwell_front_throat',[(489,342),(542,347),(570,382),(570,410),(550,392),(538,369)],1.52,'shell')
 s.panel('mag_shell',[(576,333),(695,333),(695,503),(640,503),(616,481),(589,435),(574,411)],1.28,'dark')
 for x in [661,677,688]:s.boxp('mag_channel'+str(x),(x,344),(x+5,501),1.35,'steel',.02)
 s.shell('stock_upper_sweep',[(772,235,313,1.67,.32),(917,241,296,1.52,.32),(1143,253,266,1.16,.32)])
 s.panel('stock_lower_sweep',[(819,521),(850,462),(1024,322),(1037,307),(1043,294),(1039,281),(1075,281),(1080,300),(944,423),(870,482)],1.36,'shell')
 s.griploft('grip',[(299,775,875,1.40),(313,788,851,1.36),(328,790,836,1.25),(350,803,839,1.20),(388,828,868,1.22),(423,850,895,1.18),(459,849,868,1.05)])
 s.beamp('rear_butt_back',(1107,275),(1107,420),1.34,.16,'shell');s.beamp('rear_butt_front',(1067,287),(1107,414),1.25,.16,'shell');s.beamp('rear_butt_cross',(1085,333),(1107,302),1.22,.13,'shell')
 s.beamp('trigger',(762,336),(766,356),.22,.18,'dark');s.beamp('trigger_hook',(766,356),(758,377),.20,.16,'dark')
 s.boxp('optic_base',(662,222),(751,232),.82,'dark',.05)
 rings=[]
 for radius,back in [(.49,False),(.49,True),(.37,False),(.37,True)]:
  ring=[]
  for j in range(8):
   theta=j*math.pi/4;px=max(675,701+31*math.cos(theta)) if back else 670;v=s.point(radius*math.sin(theta),px,202);ring.append((v[0],v[1]+radius*math.cos(theta),v[2]))
  rings.append(ring)
 for n,(aa,bb) in enumerate([(0,1),(2,3),(0,2),(1,3)]):
  a,b=rings[aa],rings[bb]
  for j in range(8):
   k=(j+1)%8;s.triangle(f'optic_cut_hood{n}_{j}a',a[j],a[k],b[k],'steel');s.triangle(f'optic_cut_hood{n}_{j}b',a[j],b[k],b[j],'steel')
 s.tubep('optic_front_rim',670,675,202,.53,'shell',.09)
 s.boxp('optic_base_rear',(751,226),(781,235),.72,'steel',.03)
 return s

def insidious_fidelity():
 s=SourceShape('insidious')
 s.boxp('fore_chassis',(177,317),(675,359),1.84,'dark',.05)
 # Separated wedge banks enclose a genuine long upper channel.
 wedge=[(178,315),(537,241),(674,237),(674,316),(868,316),(868,355),(178,359)]
 for sd in [-1,1]:
  before=len(s.e);before_t=len(s.authored_triangles);s.panel('wedge_bank'+str(sd),wedge,.30,'shell')
  for e in s.e[before:]:
   for key in ['from','to']:e[key][0]+=sd*1.11
   if 'rotation' in e:e['rotation']['origin'][0]+=sd*1.11
  for t in s.authored_triangles[before_t:]:t['vertices']=[(p[0]+sd*1.11,p[1],p[2]) for p in t['vertices']]
 s.boxp('muzzle_lower',(85,316),(177,359),1.72,'steel',.06);s.boxp('muzzle_front_floor',(55,342),(85,359),1.72,'steel',.04)
 s.tubep('muzzle_aperture',54,88,318,.39,'dark',.12)
 s.boxp('muzzle_upper_left',(56,283),(83,300),1.67,'steel',.05)
 for sd in [-1,1]:
  a,b=s.point(sd*.70,55,300),s.point(sd*.70,85,342);s.box('muzzle_jaw'+str(sd),a[0]-.12,a[0]+.12,b[1],a[1],a[2],b[2],'steel')
 s.boxp('muzzle_recess_floor',(89,298),(93,339),.86,'recess',.02)
 for i in range(16):
  px=88+i*18;top=253+max(0,px-171)*.085;s.beamp('top_fin'+str(i),(px,top),(px-6,314),1.48,.30,'steel')
 s.boxp('rear_receiver',(675,239),(868,358),1.84,'dark',.06)
 for sd in [-1,1]:
  before=len(s.e);before_t=len(s.authored_triangles);s.panel('receiver_slope_insert'+str(sd),[(677,242),(866,310),(677,310)],.07,'accent')
  for e in s.e[before:]:
   for key in ['from','to']:e[key][0]+=sd*.96
   e['rotation']['origin'][0]+=sd*.96
  for t in s.authored_triangles[before_t:]:t['vertices']=[(p[0]+sd*.96,p[1],p[2]) for p in t['vertices']]
 s.boxp('organic_rear_panel',(773,237),(868,275),2.01,'shell',.06)
 s.boxp('rear_upper_plate',(868,258),(1117,419),2.30,'dark',.08);s.boxp('rear_upper_foreblock',(868,237),(965,258),2.30,'dark',.06)
 for sd in [-1,1]:
  a,b=s.point(sd*1.06,965,237),s.point(sd*1.06,1117,258);s.box('rear_channel_bank'+str(sd),a[0]-.09,a[0]+.09,b[1],a[1],a[2],b[2],'steel')
 s.boxp('rear_butt_spine',(1117,237),(1145,514),2.60,'dark',.09)
 s.boxp('rear_top_spine',(966,253),(1118,264),1.36,'steel',.04)
 for px in range(969,1115,23):s.boxp('rear_rail'+str(px),(px,249),(px+17,254),1.38,'steel',.02)
 s.boxp('mag_cell_core',(869,419),(1080,512),1.90,'dark',.07)
 for px in [895,930,963,1005,1036,1065]:s.boxp('mag_cell_rib'+str(px),(px,424),(px+4,512),2.01,'steel',.02)
 for py in [420,473,509]:s.boxp('mag_cell_cross'+str(py),(895,py),(999,py+4),2.01,'steel',.02)
 s.griploft('grip',[(359,713,761,1.09),(403,734,783,1.17),(455,755,808,1.22),(514,780,828,1.11)])
 for j,(a,b) in enumerate([((689,386),(715,400)),((715,400),(717,472)),((717,472),(704,495)),((704,495),(683,514)),((683,514),(833,514))]):s.beamp('trigger_frame'+str(j),a,b,1.23,.16,'steel')
 s.panel('rear_grip_guard',[(810,359),(866,359),(866,516),(829,516),(846,485),(853,442),(846,399)],1.37,'shell')
 bow=[(198,358),(198,368),(263,395),(347,420),(450,443),(559,457),(674,461)]
 for j,(a,b) in enumerate(zip(bow,bow[1:])):s.beamp('underslung_bow'+str(j),a,b,.47,.13,'steel')
 s.boxp('bow_rear_mount',(610,420),(626,453),1.24,'steel',.04);s.boxp('bow_rear_foot',(610,452),(674,464),1.27,'steel',.04)
 s.panel('fore_lower_sweep',[(470,358),(553,358),(579,369),(610,419),(643,419),(643,363),(675,358)],1.82,'dark')
 s.boxp('sight_base',(675,234),(771,244),1.36,'steel',.04)
 s.boxp('sight_rear_wall',(728,185),(771,237),1.35,'dark',.06)
 for sd in [-1,1]:
  s.beamp('sight_front'+str(sd),(677,233),(677,195),.11,.11,'steel',sd*.63);s.beamp('sight_roof'+str(sd),(680,188),(729,188),.11,.11,'steel',sd*.63);s.beamp('sight_corner'+str(sd),(677,195),(680,188),.11,.11,'steel',sd*.63)
 s.beamp('front_sight',(542,186),(542,238),.11,.10,'steel')
 return s

def phyllotactic_spiral_fidelity():
 s=SourceShape('phyllotactic_spiral')
 s.shell('barrel_shroud',[(78,237,302,1.42,.50),(309,236,303,1.52,.50),(442,235,304,1.65,.50)])
 s.tubep('muzzle_aperture',54,78,273,.68,'dark',.43)
 s.boxp('barrel_top_rail',(82,237),(307,251),.81,'steel',.04);s.boxp('barrel_side_plate',(252,276),(435,302),1.58,'steel',.05)
 s.boxp('receiver_core',(443,226),(812,310),1.61,'dark',.07)
 for i,(a,b) in enumerate([(443,535),(535,652),(652,812)]):
  s.boxp('receiver_panel'+str(i),(a+3,237),(b-3,303),1.81,'shell',.05);s.boxp('receiver_crown'+str(i),(a+2,225),(b-2,238),1.52,'steel',.04)
 s.boxp('forward_upper_rail',(535,219),(557,226),1.56,'steel',.03);s.boxp('rear_upper_rail',(678,219),(698,227),1.56,'steel',.03)
 for sd in [-1,1]:
  for j,px in enumerate([465,497,529]):
   p=s.point(sd*.93,px,253);s.eye(f'front_module{sd}_{j}_',p[0],p[1],p[2],.18,.07,'steel',.055)
 s.shell('lower_module',[(244,325,375,1.53,.62),(461,325,375,1.53,.62),(473,322,366,1.42,.62)])
 s.tubep('lower_module_bore',220,244,352,.57,'dark',.31)
 for j,(a,b) in enumerate([((470,322),(533,322)),((470,324),(518,397)),((533,322),(533,399)),((518,399),(533,399))]):s.beamp('lower_module_bridge'+str(j),a,b,1.30,.22,'dark')
 s.boxp('receiver_lower',(533,321),(811,362),1.40,'dark',.06)
 s.beamp('trigger',(658,363),(667,397),.20,.18,'steel')
 s.griploft('grip',[(365,685,748,.92),(393,697,749,1.10),(412,708,765,1.17),(494,741,795,1.15),(518,731,748,.85)])
 # Raised diagonal grip lattice follows the palm face, backed by the sculpted grip solid.
 for sd in [-1,1]:
  for row in range(5):
   py=423+14*row;front=708+(py-412)*.405
   for col in range(3):
    px=front+13+13*col;v=[(px,py-6),(px+6,py),(px,py+6),(px-6,py)]
    for k,(a,b) in enumerate(zip(v,v[1:]+v[:1])):s.beamp(f'grip_lattice{sd}_{row}_{col}_{k}',a,b,.035,.045,'steel',sd*.58)
 s.shell('stock_upper',[(812,225,296,1.55,.55),(951,246,294,1.35,.55),(1124,246,294,1.25,.55)])
 s.boxp('stock_butt',(1123,246),(1143,405),1.90,'rubber',.06);s.boxp('stock_butt_rail',(1122,250),(1128,400),1.72,'steel',.03)
 s.boxp('magwell_upper',(827,294),(950,350),1.60,'dark',.05)
 for i,py in enumerate([297,308,319,330,341]):s.boxp('magwell_rib'+str(i),(835,py),(948,py+5),1.87,'steel',.03)
 s.panel('magwell_lower',[(826,350),(949,350),(956,369),(1014,390),(1004,425),(828,367)],1.68,'shell')
 for j,(a,b) in enumerate([((1008,416),(1026,365)),((1026,365),(1040,351)),((1040,351),(1121,351))]):s.beamp('stock_lower_brace'+str(j),a,b,.89,.18,'steel')
 s.panel('mag_shell',[(852,377),(958,413),(923,529),(818,493)],1.28,'dark')
 s.beamp('mag_floor',(821,490),(926,526),1.43,.16,'steel')
 s.boxp('optic_base',(621,213),(710,224),.78,'dark',.04);s.tubep('optic_hood',622,709,193,.48,'steel',.12);s.tubep('optic_rim',621,629,193,.52,'steel',.08)
 return s

def fidelity(w):
 s={'krait':krait_fidelity_loft,'origin_story':origin_story_fidelity,'rufuss_fury':rufuss_fury_fidelity,'age_old_bond':age_old_bond_fidelity,'insidious':insidious_fidelity,'phyllotactic_spiral':phyllotactic_spiral_fidelity}[w]();assert len(s.e)<1000,len(s.e)
 parts={'body':[],'magazine':[]}
 for e in s.e:
  if 'faces' in e:
   e['faces']['south']['uv']=[0,0,8,16];e['faces']['north']['uv']=[8,0,0,16]
  else:e['faces']={f:{'uv':[8,0,16,16],'texture':'#0'} for f in kit.FACE_AXES}
  parts['magazine' if e['name'].startswith('mag_') else 'body'].append(e)
 d=art(w)/'fidelity_review';(d/'authored_closed_lofts.json').write_text(json.dumps(s.authored_triangles,separators=(',',':')));model=d/'corrected_geometry.json';model.write_text(json.dumps({'texture_size':[512,256],'parts':parts},separators=(',',':')))
 clay=Image.new('RGBA',(512,256),(113,130,141,255));pix=clay.load()
 for xx in range(256):
  for yy in range(256):
   if xx>yy:pix[xx,yy]=(113,130,141,0)
 clay.save(d/'corrected_geometry.png')
 L,z0,ym=FIDELITY_FRAME[w];u=L/1091
 refs={'krait':{'front_grip':[435,386],'rear_grip':[724,347],'magazine':[695,298],'sight':[560,185]},'origin_story':{'rear_grip':[855,336],'magazine':[650,400],'sight':[800,212]},'rufuss_fury':{'rear_grip':[866,360],'magazine':[666,402],'sight':[778,190]},'age_old_bond':{'rear_grip':[815,339],'magazine':[633,350],'sight':[702,203]},'insidious':{'rear_grip':[750,368],'magazine':[960,430],'sight':[725,211]},'phyllotactic_spiral':{'rear_grip':[705,370],'magazine':[895,400],'sight':[662,194]}}[w]
 (d/'correction-reference-points.json').write_text(json.dumps({'uniform_mapping':{'model_units_per_source_pixel':u,'z_at_pixel_x_54_5':z0,'y_at_pixel_y_350':ym},'model_references':{n:[8,ym+(350-py)*u,z0+(px-54.5)*u] for n,(px,py) in refs.items()},'source_fidelity_precedes_donor_ads':True,'native_binding':'requires source-proportioned whole-weapon framing; no runtime change in this worker','elements':{k:len(v) for k,v in parts.items()}},indent=2)+'\n')
 subprocess.run([kit.BLENDER,'-b','--python',str(art('krait')/'v3/neutral_geometry_review.py'),'--','native',str(model),str(d/'corrected')],check=True)
 board=Image.new('RGB',(2400,1490),(23,31,37));dr=ImageDraw.Draw(board)
 for col,prefix in enumerate(['source','corrected']):
  dr.text((col*1200+20,12),w+' original .blend neutral' if col==0 else w+' source proportions / provisional geometry',fill='white')
  for row,v in enumerate(['side','q']):board.paste(Image.open(d/f'{prefix}_{v}.png').convert('RGB'),(col*1200,40+row*725))
 board.save(d/'source_corrected_neutral.png');print('Fidelity draft',w,len(s.e),flush=True)

def bake_fidelity(w):
 s={'krait':krait_fidelity_loft,'origin_story':origin_story_fidelity,'rufuss_fury':rufuss_fury_fidelity,'age_old_bond':age_old_bond_fidelity,'insidious':insidious_fidelity,'phyllotactic_spiral':phyllotactic_spiral_fidelity}[w]();assert len(s.e)<1000
 spec=importlib.util.spec_from_file_location('g3_optimize',ROOT/'scripts/art/w327/group3_optimize.py');opt=importlib.util.module_from_spec(spec);spec.loader.exec_module(opt);s=opt.optimize(s)
 out=art(w)/'v4';out.mkdir(exist_ok=True)
 pal=dict(COMMON);pal.update(PAL[w])
 if w=='krait':pal.update(shell=(44,49,44),steel=(72,79,73),dark=(24,27,25),trim=(104,114,106),recess=(14,17,16),accent=(178,196,45))
 src=Image.open(art(w)/'source_albedo.png').convert('RGBA');src=src.crop(src.getchannel('A').getbbox());lum=src.convert('L');blur=lum.filter(ImageFilter.GaussianBlur(2))
 normal_image=None
 if (art(w)/'v3/source_normal_projection.png').exists():
  normal_image=Image.open(art(w)/'v3/source_normal_projection.png').convert('RGBA');normal_image=normal_image.crop(normal_image.getchannel('A').getbbox())
 ev=json.loads((art(w)/'source-evaluation.json').read_text());source_length=max(b-a for a,b in zip(ev['lo'],ev['hi']));source_height=ev['hi'][2]-ev['lo'][2];L,z0,ym=FIDELITY_FRAME[w];height=source_height/source_length*L;yhi=ym+height/2
 def paint(e,fn,u,v):
  role=s.roles[e['name']];col=pal[role];p=kit.face_point(e,fn,u,v);normal=kit.rotate_vec(kit.NORMALS[fn],kit.rot_of(e));side=abs(normal[0])>.42
  uu=(p[2]-z0)/L;vv=(yhi-p[1])/height
  if side and 0<=uu<1 and 0<=vv<1:
   ix=min(src.width-1,int(uu*src.width));iy=min(src.height-1,int(vv*src.height));r,g,b,a=src.getpixel((ix,iy));delta=lum.getpixel((ix,iy))-blur.getpixel((ix,iy))
   if a>240 and not (w=='age_old_bond' and (max(r,g,b)-min(r,g,b)>65 or r+g+b<210)):
    if w=='krait' and g>b*1.65 and r>b*1.35 and g>58:col=pal['accent']
    elif w=='krait' and min(r,g,b)>145:col=pal['trim']
    elif w=='origin_story' and r>g*1.2 and r>b*1.4 and r>65:col=pal['accent']
    elif w=='origin_story' and min(r,g,b)>140:col=pal['trim']
    elif w=='phyllotactic_spiral' and g>r*1.25 and b>r*1.2 and g>55:col=pal['accent']
    elif role not in ('rubber','recess'):
     step=-13 if delta<-20 else -7 if delta<-9 else 8 if delta>22 else 0;col=tuple(max(0,min(255,c+step)) for c in col)
  if w=='rufuss_fury' and side and normal_image is not None and e['name'].startswith(('organic_shell','organic_wing','front_tendril')) and 0<=uu<1 and 0<=vv<1:
   nr,ng,nb,na=normal_image.getpixel((min(normal_image.width-1,int(uu*normal_image.width)),min(normal_image.height-1,int(vv*normal_image.height))))
   if na>240:
    q=max(-2,min(2,round(((nr-128)*.55+(ng-128)*.40)/14)));col=tuple(max(0,min(255,c+q*10)) for c in col)
  if w=='krait':
   px=(p[2]-z0)/L*1091+54.5;py=350-(p[1]-ym)/L*1091
   if e['name'].startswith('mag_charge_bar') and side:
    if 562<px<884 and 290<py<310 and (int((px-565)/6)%2==0 and int((py-289)/5)%2==0):col=(137,152,34)
   if e['name'].startswith(('front_grip','rear_grip')) and side:
    if int((py+px*.25)/3)%9==0:col=tuple(max(0,c-5) for c in col)
   if e['name'].startswith('stock_recess'):col=tuple(max(0,c-3) for c in col)
  return col+(255,)
 faces=[];T=18;A=1024
 for e in s.e:
  triangle=len(e.get('faces',{}))==2 and e['from'][2]==e['to'][2];polygons=e.pop('_polygons',None);e['faces']={}
  for fn in (['south'] if triangle else list(kit.FACE_AXES)):
   _,u,v=kit.face_frame(e,fn);W=max(2,round(math.sqrt(sum(q*q for q in u))*T));H=max(2,round(math.sqrt(sum(q*q for q in v))*T));im=Image.new('RGBA',(W,H));pixels=im.load()
   mask=None
   if polygons:
    mask_hi=Image.new('L',(W*4,H*4));draw=ImageDraw.Draw(mask_hi)
    for poly in polygons:draw.polygon([(u*W*4-.5,v*H*4-.5) for u,v in poly],fill=255)
    mask=mask_hi.resize((W,H),Image.Resampling.BOX).point(lambda a:255 if a else 0)
   for x in range(W):
    for y in range(H):
     uu,vv=(x+.5)/W,(y+.5)/H;visible=bool(mask.getpixel((x,y))) if mask else not triangle or uu<=vv;pixels[x,y]=paint(e,fn,uu,vv) if visible else (0,0,0,0)
   if not triangle and any(k in e['name'] for k in ['sight','collar','mag_charge','lower_rail']):
    dr=ImageDraw.Draw(im);c=pal[s.roles[e['name']]];dr.line((0,0,W-1,0),fill=tuple(min(255,v+8) for v in c)+(255,))
   faces.append((e,fn,im,triangle))
 faces.sort(key=lambda f:(-f[2].height,-f[2].width,f[0]['name'],f[1]));atlas_image=Image.new('RGBA',(A,A));x=y=row=0
 for e,fn,im,triangle in faces:
  W,H=im.size
  if x+W+2>A:x=0;y+=row;row=0
  if y+H+2>A:raise ValueError((w,'fidelity atlas overflow',y,H))
  atlas_image.paste(im,(x+1,y+1));atlas_image.paste(im.crop((0,0,W,1)),(x+1,y));atlas_image.paste(im.crop((0,H-1,W,H)),(x+1,y+H+1));atlas_image.paste(im.crop((0,0,1,H)),(x,y+1));atlas_image.paste(im.crop((W-1,0,W,H)),(x+W+1,y+1))
  uv=[16*(x+1)/A,16*(y+1)/A,16*(x+W+1)/A,16*(y+H+1)/A];e['faces'][fn]={'uv':uv,'texture':'#0'}
  if triangle:e['faces']['north']={'uv':[uv[2],uv[1],uv[0],uv[3]],'texture':'#0'}
  x+=W+2;row=max(row,H+2)
 H=min(A,1<<math.ceil(math.log2(y+row)))
 if H<A:
  atlas_image=atlas_image.crop((0,0,A,H))
  for e in s.e:
   for f in e['faces'].values():f['uv'][1]*=A/H;f['uv'][3]*=A/H
 parts={k:[e for e in s.e if e['name'].startswith('mag_')==(k=='magazine')] for k in ['body','magazine']}
 model={'texture_size':[A,H],'parts':parts,'no_overlay':True};(out/'model.json').write_text(json.dumps(model,separators=(',',':'))+'\n');atlas_image.save(out/'atlas.png',optimize=True)
 (out/'geometry.json').write_text(json.dumps({'elements':s.e,'roles':s.roles,'authored_triangles':s.authored_triangles,'authored_polygons':s.authored_polygons,'optimization':s.optimization},separators=(',',':'))+'\n')
 report={'revision':4,'stage':'source-proportioned material candidate; native QA pending','elements':{k:len(v) for k,v in parts.items()},'total':len(s.e),'atlas':[A,H],'texels_per_model_unit':T,'source_blend_sha256':sha(ev['blend']),'generator_sha256':sha(__file__),'model_sha256':sha(out/'model.json'),'atlas_sha256':sha(out/'atlas.png'),'optimization':s.optimization,'triangle_alpha':'coplanar authored triangle union mask shared by mirrored south/north faces','material':'bounded actual source albedo panel relief and markings; flat role palette; no triangle seam lines or broad gradients'}
 (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print('Material candidate',w,len(s.e),[A,H],flush=True)
 return out

SOURCE_DETAIL={}
NORMAL_DETAIL={}
def source_detail(w,p,c,n,role):
 """Limited actual source panel relief, mapped across side surfaces; no dye/wireframe baking."""
 if w not in SOURCE_DETAIL:return c
 if role not in ('shell','dark','steel'):return c
 if not n.startswith(('receiver','stock_','ivory_shell','upper_shell','rear_lobe','hanging_side','rear_butt','wedge_side','mag_shell','barrel_front','barrel_rear')):return c
 im,L,B,bounds=SOURCE_DETAIL[w];x,y,z=p;z0,z1,y0,y1=bounds
 u=(z-z0)/(z1-z0);v=1-(y-y0)/(y1-y0)
 if not 0<u<1 or not 0<v<1:return c
 ix=int(u*(im.width-1));iy=int(v*(im.height-1));r,g,b,a=im.getpixel((ix,iy))
 if a<250 or (w=='age_old_bond' and (max(r,g,b)-min(r,g,b)>65 or (r+g+b)<210)):return c
 delta=L.getpixel((ix,iy))-B.getpixel((ix,iy))
 # Quantized bounded detail. Broad baked lighting and all random noise are excluded.
 change=-15 if delta<-22 else -8 if delta<-10 else 9 if delta>24 else 0
 if not change:return c
 return tuple(max(0,min(255,q+change)) for q in c)

GLYPHS={'V':['101','101','101','101','010'],'E':['111','100','110','100','111'],'I':['111','010','010','010','111'],'S':['111','100','111','001','111'],'T':['111','010','010','010','010']}
def textbit(txt,u,v,x,y,k=.07):
 a=int((u-x)/k);b=int((v-y)/k)
 return u>=x and v>=y and 0<=b<5 and 0<=a<len(txt)*4 and a%4<3 and GLYPHS[txt[a//4]][b][a%4]=='1'

def color_at(w,e,fn,u,v,pal):
 n=e['name'];role=e['_role'];c=pal[role];p=kit.face_point(e,fn,u,v);x,y,z=p;side=fn in ('east','west')
 if side:c=source_detail(w,p,c,n,role)
 if w=='rufuss_fury' and side and n.startswith(('upper_shell','lower_shell','rear_lobe','dorsal')) and w in NORMAL_DETAIL:
  im=NORMAL_DETAIL[w];uu=(z+9.95)/25.30;vv=1-(y-6.2)/6.62
  if 0<uu<1 and 0<vv<1:
   nr,ng,nb,na=im.getpixel((int(uu*(im.width-1)),int(vv*(im.height-1))))
   if na>250:
    # Actual rip normal relief, quantized into a calm 5-level static RGBA cue.
    q=max(-2,min(2,round(((nr-128)*.55+(ng-128)*.40)/14)))
    c=tuple(max(0,min(255,ch+q*9)) for ch in c)
 dark=pal['recess'];trim=pal['trim'];accent=pal['accent']
 # Coordinate-aware face paint: intentionally continuous across adjoining shell parts.
 if side:
  if w=='krait':
   if n.startswith('mag_charge_bar'):
    if (int((z+.1)*9)%3==0 and 10.58<y<10.75):c=(112,132,27)
    if -.07<z<.52 and abs(y-(10.50+(z+.07)*.6))<.10:c=trim
   if n.startswith('receiver_side'):
    if 11.12<y<11.20 and -1.85<z<5.9:c=dark
    for zz in [-1.6,2.9,5.6]:
     if math.hypot((z-zz)*1.3,y-11.42)<.075:c=trim
   if n.startswith('receiver_roof') and textbit('VEIST',z if fn=='west' else 3.16-z,12.05-y,.9,0,.068):c=accent
   if n.startswith('stock_') and 10.4<y<12.4:
    line=11.04+(z-10.6)*.12
    if 10.6<z<14.8 and abs(y-line)<.045:c=(29,39,34)
   if n.startswith('rear_grip') or n.startswith('forward_grip'):
    if int((y+z*.3)*11)%7==0:c=(15,23,18)
  elif w=='rufuss_fury':
   if role in ('shell','accent'):
    curve=10.80+.48*math.sin((z+3.2)*.66)
    if abs(y-curve)<.055:c=(92,134,166)
    if abs(y-curve-.12)<.035:c=trim
    if n.startswith('upper_shell') and y>11.88+.10*math.sin(z):c=(178,201,211)
    if n.startswith('rear_lobe') and y<11.34+.13*math.sin(z*1.8):c=(49,87,125)
   if n.startswith('mag_channel'):
    if abs(z-3.1)<.09 or abs(z-3.75)<.07:c=trim
   if n.startswith('stock_beam') and any(abs(z-q)<.08 for q in [9.0,9.5,10.0]):c=dark
  elif w=='origin_story':
   if n.startswith(('receiver_main','receiver_side','upper_slide','receiver_front')):
    stripe=z+(y-10.30)*.85
    if -.65<stripe<.25 or 3.22<stripe<4.12:c=accent
    elif .25<stripe<.69:c=trim
    if -4.9<z<-3.9 and 11.12<y<11.94:
     a=z+4.9;b=11.94-y
     if abs(a-(.12+b*.48))<.095 or abs(a-(.88-b*.48))<.095:c=accent
   if n.startswith('selector_panel') and any(math.hypot(z-q,y-11.24)<.09 for q in [1.29,1.72,2.14]):c=dark
   if n.startswith('foreend') and int((z+.2)*6)%5==0:c=dark
   if n.startswith('mag_channel') and any(abs(z-q)<.055 for q in [1.70,2.42,3.15]):c=pal['steel']
   if n.startswith('lower_front_slope') and z>3.8:c=accent
  elif w=='age_old_bond':
   if role in ('shell','trim') and n.startswith(('ivory','join','muzzle')):
    # Flowing source-carved motif: nested curved bands and sparse teardrop nodes.
    curves=[11.45+.40*math.sin((z+2)*.45),11.76+.32*math.sin((z+2)*.45),12.10+.22*math.sin((z+2)*.45)]
    if any(abs(y-q)<.035 for q in curves):c=(175,161,121)
    if any(abs(y-q-.07)<.028 for q in curves):c=(238,228,194)
    for zz,yy in [(-6.4,11.66),(-2.5,11.28),(3.1,11.62),(5.2,11.23)]:
     rr=math.hypot((z-zz)*.75,(y-yy)*1.6)
     if .13<rr<.19:c=(178,161,117)
   if n.startswith('mag_channel') and any(abs(z-q)<.04 for q in [2.4,3.1,3.8]):c=pal['steel']
  elif w=='insidious':
   if n.startswith('red_triangular_insert'):
    c=accent if y < 12.87-(z-7.05)*.33 else pal['dark']
   if n.startswith('organic_rear_panel'):
    if abs(math.sin(z*6)+math.cos(y*8))<.32:c=dark
   if n.startswith('hanging_side_plate'):
    if abs(y-9.16)<.035 or abs(z-12.0)<.035 or abs(z-16.1)<.035:c=dark
   if n.startswith('rear_butt') and 7.45<y<8.75:
    if abs((y-7.45)%0.62)<.05 or abs((z-16.78)%0.48)<.05:c=dark
   if n.startswith('mag_channel'):
    if abs((z-10.68)%0.67)<.045 or abs((y-7.0)%0.78)<.045:c=pal['steel']
    elif abs((z+y*.6)%1.2-.6)<.06:c=(17,24,22)
   if n.startswith('wedge_side') and 10.97<y<11.28:c=(26,29,27)
  elif w=='phyllotactic_spiral':
   if n.startswith('upper_module'):
    # Three evidenced concentric top-side modules.
    mid=(e['from'][2]+e['to'][2])/2;cy=(e['from'][1]+e['to'][1])/2;r=math.hypot(z-mid,y-cy)
    if .11<r<.19:c=dark
    if r<.065:c=pal['accent']
   if n.startswith('lower_module_panel'):
    wave=9.71+.14*(1 if int((z+4)*2.4)%2 else -1)
    if abs(y-wave)<.04 or abs(y-9.97)<.025:c=pal['steel']
   if n.startswith('receiver_panel'):
    if abs(y-11.12)<.035 or abs(y-11.72)<.035 or abs(z-3.7)<.035 or abs(z-7.05)<.035:c=pal['accent']
   if n.startswith('grip_core'):
    if abs((y+z)*6-round((y+z)*6))<.19 or abs((y-z)*6-round((y-z)*6))<.19:c=dark
   if n.startswith('mag_channel') and (z<11.60 or y<6.60):c=pal['trim']
 # Selected shallow role texture, never generic gradient/noise.
 if role=='rubber' and side and int(y*16)%5==0:c=tuple(max(0,q-5) for q in c)
 return c+(255,)

def bake(w,s):
 pal=dict(COMMON);pal.update(PAL[w]);T=18;A=1024;faces=[]
 im=Image.open(art(w)/'source_albedo.png').convert('RGBA')
 # Trim transparent source viewport padding before mapping broad semantic side surfaces.
 bbox=im.getchannel('A').getbbox()
 if bbox:im=im.crop(bbox)
 lum=im.convert('L');blur=lum.filter(ImageFilter.GaussianBlur(2.2))
 bounds={'krait':(-9.5,15.65,6.32,13.57),'rufuss_fury':(-9.95,15.35,6.2,12.82),'origin_story':(-9,15.18,5.6,13.4),'age_old_bond':(-9.46,15.15,5.6,13.6),'insidious':(-6.8,17.85,6.6,14.55),'phyllotactic_spiral':(-6.72,17.63,6.0,14.1)}[w]
 SOURCE_DETAIL[w]=(im,lum,blur,bounds)
 if (art(w)/'v3/source_normal_projection.png').exists():
  ni=Image.open(art(w)/'v3/source_normal_projection.png').convert('RGBA');bb=ni.getchannel('A').getbbox();NORMAL_DETAIL[w]=ni.crop(bb) if bb else ni
 # Write every six-face native box; no invented mesh fields or side alpha impostors.
 for e in s.e:
  e['_role']=s.roles[e['name']]
  for fn in kit.FACE_AXES:
   _,u,v=kit.face_frame(e,fn);W=max(2,round(math.dist((0,0,0),u)*T));H=max(2,round(math.dist((0,0,0),v)*T))
   im=Image.new('RGBA',(W,H));px=im.load()
   for xx in range(W):
    for yy in range(H):px[xx,yy]=color_at(w,e,fn,(xx+.5)/W,(yy+.5)/H,pal)
   # A single texel seam only on mechanically separate panels; no every-station bevel gradient.
   if any(k in e['name'] for k in ['panel','plate','mag_floor','optic','selector','butt','collar','module']):
    dr=ImageDraw.Draw(im);c=pal[e['_role']];dr.line((0,0,W-1,0),fill=tuple(min(255,v+9) for v in c)+(255,));dr.line((0,H-1,W-1,H-1),fill=tuple(max(0,v-9) for v in c)+(255,))
   faces.append((e,fn,im))
 faces.sort(key=lambda f:(-f[2].height,-f[2].width,f[0]['name'],f[1]))
 at=Image.new('RGBA',(A,A));xx=yy=row=0
 for e,fn,im in faces:
  W,H=im.size
  if xx+W+2>A:xx=0;yy+=row;row=0
  if yy+H+2>A:raise RuntimeError((w,'atlas overflow',yy,H))
  at.paste(im,(xx+1,yy+1));at.paste(im.crop((0,0,W,1)),(xx+1,yy));at.paste(im.crop((0,H-1,W,H)),(xx+1,yy+H+1));at.paste(im.crop((0,0,1,H)),(xx,yy+1));at.paste(im.crop((W-1,0,W,H)),(xx+W+1,yy+1))
  e.setdefault('faces',{})[fn]={'uv':[16*(xx+1)/A,16*(yy+1)/A,16*(xx+W+1)/A,16*(yy+H+1)/A],'texture':'#0'}
  xx+=W+2;row=max(row,H+2)
 actual_h=min(A,1<<math.ceil(math.log2(yy+row)))
 if actual_h<A:
  at=at.crop((0,0,A,actual_h))
  for e in s.e:
   for f in e['faces'].values():f['uv'][1]*=A/actual_h;f['uv'][3]*=A/actual_h
 parts={'body':[],'magazine':[]}
 for e in s.e:
  e.pop('_role',None);mag=e['name'].startswith('mag_')
  parts['magazine' if mag else 'body'].append(e)
 doc={'texture_size':[A,actual_h],'parts':parts,'no_overlay':True}
 skin(w).parent.mkdir(parents=True,exist_ok=True);skin(w).write_text(json.dumps(doc,separators=(',',':'))+'\n');at.save(atlas(w),optimize=True)
 hud=AS/f'textures/item/hud/w327/ammo_{w}.png';kit.hud_icon(s.e,hud,lambda n:False)
 return doc

def build(w):
 s=BUILDERS[w]();assert len(s.e)<1000
 d=art(w);(d/'v3').mkdir(exist_ok=True)
 (d/'v3/geometry.json').write_text(json.dumps({'elements':s.e,'roles':s.roles},indent=2)+'\n')
 (d/'design.py').write_text('"""W327 V3 semantic geometry; generator scripts/art/w327/group3_v3.py. Native QA pending."""\nELEMENTS='+repr(s.e)+'\nROLES='+repr(s.roles)+'\ndef elements():return ELEMENTS\n')
 doc=bake(w,s)
 old=json.loads((d/'manifest.json').read_text());old.update(revision=3,atlas=doc['texture_size'],elements={k:len(v) for k,v in doc['parts'].items()},element_total=len(s.e),generator='scripts/art/w327/group3_v3.py',generator_sha256=sha(__file__),material_finish='flat selected palette; semantic surface motifs and separate face UV; no broad gradients',native_acceptance='pending master Vision')
 old['outputs_sha256']={str(p.relative_to(ROOT)):sha(p) for p in [skin(w),atlas(w),AS/f'textures/item/hud/w327/ammo_{w}.png']};old.pop('hidden_faces',None);old['texels_per_px']=18
 (d/'manifest.json').write_text(json.dumps(old,indent=2)+'\n')
 check(w)
 print(w,len(s.e),doc['texture_size'],flush=True)

def check(w):
 d=json.loads(skin(w).read_text());es=sum(d['parts'].values(),[])
 for e in es:
  assert all(e['to'][i]>e['from'][i] for i in range(3)),e['name']
  assert set(e['faces'])==set(kit.FACE_AXES)
  for f in e['faces'].values():assert len(f['uv'])==4 and all(0<=q<=16 for q in f['uv'])
 assert len({e['name'] for e in es})==len(es)
 assert len(es)<1000
 assert Image.open(atlas(w)).size==tuple(d['texture_size'])
 ev=json.loads((art(w)/'source-evaluation.json').read_text());assert sha(ev['blend'])==ev['sha256']
 out=io.StringIO()
 with contextlib.redirect_stdout(out):kit.adscheck(w)
 ads=out.getvalue();(art(w)/'v3/adscheck.txt').write_text(ads)
 comps=components(d['parts']['body']);(art(w)/'v3/connections.json').write_text(json.dumps({'method':'OBB separating axes; contact tolerance .06 model units; body only','components':comps},indent=2)+'\n')
 report={'revision':3,'elements':{k:len(v) for k,v in d['parts'].items()},'total':len(es),'uv_in_range':True,'positive_dimensions':True,'source_blend_hash_matches':True,'atlas':d['texture_size'],'same_existing_coordinate_basis':True,'ads_base_profile_pass':'  OK:' in ads,'body_component_count':len(comps),'base_motion':'reused; no source actions','native_qa':'not performed; master pending','performance':'not measured'}
 (art(w)/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Checks',w,'ADS',report['ads_base_profile_pass'],'body_components',list(map(len,comps)),flush=True)

def components(es):
 def dot(a,b):return sum(x*y for x,y in zip(a,b))
 def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
 ps=[(kit._corners(e),[kit.rotate_vec([int(i==j) for i in range(3)],kit.rot_of(e)) for j in range(3)]) for e in es]
 def touch(a,b):
  ca,aa=a;cb,ab=b
  for ax in aa+ab+[cross(x,y) for x in aa for y in ab]:
   L=math.sqrt(dot(ax,ax))
   if L<1e-6:continue
   ax=[q/L for q in ax];pa=[dot(p,ax) for p in ca];pb=[dot(p,ax) for p in cb]
   if min(pa)>max(pb)+.06 or min(pb)>max(pa)+.06:return False
  return True
 adj=[set() for e in es]
 for i,a in enumerate(ps):
  for j in range(i):
   if touch(a,ps[j]):adj[i].add(j);adj[j].add(i)
 unseen=set(range(len(es)));comps=[]
 while unseen:
  st=[unseen.pop()];co=[]
  while st:
   i=st.pop();co.append(es[i]['name'])
   for j in adj[i]&unseen:unseen.remove(j);st.append(j)
  comps.append(co)
 return sorted(comps,key=len,reverse=True)

def render(w):
 p=art(w)/'v3'/w
 subprocess.run([kit.BLENDER,'-b','--python',str(ROOT/'scripts/art/w325/render_model.py'),'--',str(p),str(skin(w)),str(atlas(w)),'west,q,rear,front'],check=True)

def comparison(w):
 d=art(w)/'v3';d.mkdir(exist_ok=True)
 # Own a renderer copy, preserving the shared kit. Same lens, lights and normalized weapon size.
 script=(ROOT/'scripts/art/w325/render_model.py').read_text().replace("'rear': (0, -1, 0)","'rear': (0, -1, 0), 'rearq': (-0.70,-0.55,-0.43)")
 renderer=d/'render_review.py';renderer.write_text(script)
 views='west,q,rearq'
 def run(prefix,model,texture):subprocess.run([kit.BLENDER,'-b','--python',str(renderer),'--',str(prefix),str(model),str(texture),views],check=True)
 run(d/'v3',skin(w),atlas(w))
 run(d/'v2',art(w)/'revisions/v2'/f'{w}.json',art(w)/'revisions/v2'/f'{w}.png')
 bench='the_recluse' if w in ('krait','rufuss_fury','age_old_bond') else 'blast_furnace'
 native=json.loads((MAIN/f'src/main/resources/assets/destiny/models/weapon_surface_w123/{bench}.json').read_text())
 bd=d/'benchmark.json';bd.write_text(json.dumps({'texture_size':[1024,1024],'parts':{'body':native['elements']}}))
 run(d/'benchmark',bd,MAIN/f'src/main/resources/assets/destiny/textures/item/weapon/w123/{bench}.png')
 board=Image.new('RGB',(2400,1515),(23,31,37));dr=ImageDraw.Draw(board)
 for col,(prefix,title) in enumerate([('benchmark','Existing W251 '+bench),('v2','Rejected V2'),('v3','V3 semantic redesign / native QA pending')]):
  dr.text((col*800+18,12),title,fill='white')
  for row,view in enumerate(views.split(',')):
   im=Image.open(d/f'{prefix}_{view}.png').convert('RGB').resize((800,467),Image.Resampling.LANCZOS);board.paste(im,(col*800,45+row*490));dr.text((col*800+12,47+row*490),view,fill=(12,20,25))
 board.save(d/'benchmark_v2_v3.png')
 print('Comparison',w,flush=True)

if __name__=='__main__':
 cmd=sys.argv[1] if len(sys.argv)>1 else 'build';ws=IDS if len(sys.argv)<3 or sys.argv[2]=='all' else sys.argv[2:]
 for w in ws:
  assert w in IDS
  if cmd=='material':bake_fidelity(w)
  elif cmd=='v3-build':build(w)
  elif cmd=='v3-render':render(w)
  elif cmd=='v3-check':check(w)
  elif cmd=='comparison':comparison(w)
  elif cmd=='fidelity':fidelity(w)
