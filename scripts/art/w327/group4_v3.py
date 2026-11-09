"""W327 V3 group 4: semantic solid reconstruction and calm face-specific pixel finishes.
Original static .blend evaluation is reused verbatim; no animation provenance is invented.
"""
from pathlib import Path
import json, math, sys, hashlib, importlib.util, subprocess
from PIL import Image, ImageDraw, ImageFilter
ROOT=Path(__file__).resolve().parents[3]
MAIN=Path('/Users/qf/IdeaProjects/DestinyGuardians')
IDS='trustee succession heritage commemoration iterative_loop circular_logic'.split()
def art(w):return ROOT/'art/weapons/w327'/w
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def skin(w):return ROOT/f'src/main/resources/destiny/weapon_skins/{w}.json'
def atlas(w):return ROOT/f'src/main/resources/assets/destiny/textures/item/weapon/w327/{w}.png'
def hud(w):return ROOT/f'src/main/resources/assets/destiny/textures/item/hud/w327/ammo_{w}.png'
def kit():
 s=importlib.util.spec_from_file_location('w325kit',MAIN/'scripts/art/w325/kit.py');k=importlib.util.module_from_spec(s);s.loader.exec_module(k);return k
class Model:
 def __init__(self,w):
  self.w=w;self.e=[];self.old=json.loads((MAIN/'art/weapons/w327'/w/'design.json').read_text());self.mat=self.old['materials']
  self.mat['seam']=dict(kind='dark',color=[16,23,26]);self.mat['white']=dict(kind='paint',color=[218,226,220]);self.mat['cyan']=dict(kind='paint',color=[46,153,167])
 def box(self,n,x,y,z,X,Y,Z,m='shell',rot=None):
  e=dict(name=n,**{'from':[x,y,z],'to':[X,Y,Z]},role=m)
  if rot:e['rotation']=rot
  self.e.append(e);return e
 def b(self,n,z,Z,y,Y,width,m='shell',x=8):return self.box(n,x-width/2,y,z,x+width/2,Y,Z,m)
 def beam(self,n,z,y,Z,Y,width,thick,m='shell',x=8):
  cy=(y+Y)/2;cz=(z+Z)/2;L=math.hypot(Y-y,Z-z)
  return self.box(n,x-width/2,cy-thick/2,cz-L/2,x+width/2,cy+thick/2,cz+L/2,m,dict(origin=[x,cy,cz],x=-math.degrees(math.atan2(Y-y,Z-z)),y=0,z=0))
 def roundbeam(self,n,z,y,Z,Y,diam,m='shell',x=8):
  a=-math.atan2(Y-y,Z-z);cy=(y+Y)/2;cz=(z+Z)/2;length=math.hypot(Y-y,Z-z);r=diam/2;t=r*.38;R=r-t/2;wall=2*R*math.tan(math.pi/8)
  self.beam(n+'/core',z,y,Z,Y,diam*.63,diam*.63,m,x)
  for i in range(8):
   b=math.radians(i*45);cx=x-R*math.sin(b);yy=cy+R*math.cos(b)*math.cos(a);zz=cz+R*math.cos(b)*math.sin(a)
   # Euler decomposition of Rx(a)*Rz(b), emitted in native Rz*Ry*Rx order.
   ry=math.asin(-math.sin(a)*math.sin(b));rx=math.atan2(math.sin(a)*math.cos(b),math.cos(a));rz=math.atan2(math.cos(a)*math.sin(b),math.cos(b))
   self.box(n+'/oct'+str(i),cx-wall/2,yy-t/2,zz-length/2,cx+wall/2,yy+t/2,zz+length/2,m,dict(origin=[cx,yy,zz],x=math.degrees(rx),y=math.degrees(ry),z=math.degrees(rz)))
 def tube(self,n,z,Z,y,r,m='steel',open=False,sides=8,slots=None):
  # Eight exactly meeting tangential walls, real through bore.
  t=r*.22;R=r-t/2;L=2*R*math.tan(math.pi/sides)
  for i in range(sides):
   a=i*360/sides;rad=math.radians(a);cx=8-R*math.sin(rad);cy=y+R*math.cos(rad)
   spans=slots if slots and i%3==1 else [(z,Z)]
   for j,(zz,ZZ) in enumerate(spans):self.box(n+f'/wall{i}_{j}',cx-L/2,cy-t/2,zz,cx+L/2,cy+t/2,ZZ,m,dict(origin=[cx,cy,(zz+ZZ)/2],x=0,y=0,z=a))
  if not open:self.b(n+'/bore',z+.05,Z-.05,y-r*.6,y+r*.6,r*1.2,'seam')
 def prism(self,n,z,Z,y,Y,w,m='shell',x=8):
  # True flat chamfer planes, with a filled interior. No stair-step cross-section.
  c=min(w*.18,(Y-y)*.2);t=c*.65;cy=(y+Y)/2;hx=w/2;hy=(Y-y)/2
  pts=[(-hx+c,-hy),(hx-c,-hy),(hx,-hy+c),(hx,hy-c),(hx-c,hy),(-hx+c,hy),(-hx,hy-c),(-hx,-hy+c)]
  self.box(n+'/web',x-hx+t,y+t,z,x+hx-t,Y-t,Z,m)
  for i,(a,b) in enumerate(zip(pts,pts[1:]+pts[:1])):
   dx=b[0]-a[0];dy=b[1]-a[1];L=math.hypot(dx,dy);nx=-dy/L;ny=dx/L;xx=x+(a[0]+b[0])/2+nx*t/2;yy=cy+(a[1]+b[1])/2+ny*t/2
   self.box(n+'/chamfer'+str(i),xx-L/2,yy-t/2,z,xx+L/2,yy+t/2,Z,m,dict(origin=[xx,yy,(z+Z)/2],x=0,y=0,z=math.degrees(math.atan2(dy,dx))))
 def frame(self,n,z,Z,y,Y,w,m='shell'):
  t=min(w*.22,(Y-y)*.22)
  self.b(n+'/top',z,Z,Y-t,Y,w,m);self.b(n+'/bottom',z,Z,y,y+t,w,m)
  self.box(n+'/left',8-w/2,y+t,z,8-w/2+t,Y-t,Z,m)
  self.box(n+'/right',8+w/2-t,y+t,z,8+w/2,Y-t,Z,m)
 def sides(self,n,z,Z,y,Y,w,m='shell',depth=.16):
  for s in [-1,1]:self.box(n+str(s),8+s*w/2-(depth if s<0 else 0),y,z,8+s*w/2+(depth if s>0 else 0),Y,Z,m)
 def sideplate(self,n,z,Z,y,Y,w,m='shell',depth=.16):
  t=min((Z-z)*.12,(Y-y)*.2)
  self.sides(n+'/center',z+t,Z-t,y,Y,w,m,depth)
  self.sides(n+'/front',z,z+t,y+t,Y-t,w,m,depth)
  self.sides(n+'/rear',Z-t,Z,y+t,Y-t,w,m,depth)
 def loft(self,n,sections,axis='z',m='shell',sides=8):
  """Closed authored homothetic section loft, native masked polygon faces.
  Parallel similar sections yield exactly planar quad panels without diagonal seams.
  """
  spec=importlib.util.spec_from_file_location('native_tri',MAIN/'scripts/mesh/native_triangle_elements_w115.py');tri=importlib.util.module_from_spec(spec);spec.loader.exec_module(tri)
  ratios=sorted(ra/rb for center,ra,rb in sections);ratio=ratios[len(ratios)//2];rings=[]
  for center,ra,rb in sections:
   ra=rb*ratio
   rings.append([[center[0]+math.cos(2*math.pi*i/sides)*ra,center[1]+(math.sin(2*math.pi*i/sides)*rb if axis=='z' else 0),center[2]+(math.sin(2*math.pi*i/sides)*rb if axis=='y' else 0)] for i in range(sides)])
  polygons=[]
  for a,b in zip(rings,rings[1:]):
   for i in range(sides):
    j=(i+1)%sides;polygons.append([a[i],a[j],b[j],b[i]])
  polygons.extend([rings[0],rings[-1]])
  self.surface_polygons(n,polygons,m)
 def profile_solid(self,n,outline,width,m='shell'):
  cy=sum(v[0] for v in outline)/len(outline);cz=sum(v[1] for v in outline)/len(outline);rings=[]
  for x,fac in [(8-width/2,.94),(8-width*.35,1),(8+width*.35,1),(8+width/2,.94)]:rings.append([[x,cy+(y-cy)*fac,cz+(z-cz)*fac] for y,z in outline])
  polygons=[]
  for a,b in zip(rings,rings[1:]):
   for i in range(len(a)):j=(i+1)%len(a);polygons.append([a[i],a[j],b[j],b[i]])
  polygons.extend([rings[0],rings[-1]]);self.surface_polygons(n,polygons,m)
 def surface_polygons(self,n,polygons,m):
  spec=importlib.util.spec_from_file_location('native_tri',MAIN/'scripts/mesh/native_triangle_elements_w115.py');tri=importlib.util.module_from_spec(spec);spec.loader.exec_module(tri)
  for i,vs in enumerate(polygons):
   a,b=max(((vs[j],vs[(j+1)%len(vs)]) for j in range(len(vs))),key=lambda q:tri.norm(tri.sub(q[1],q[0])))
   u=tri.unit(tri.sub(b,a));normal=tri.unit(max((tri.cross(tri.sub(vs[j],vs[0]),tri.sub(vs[j+1],vs[0])) for j in range(1,len(vs)-1)),key=tri.norm));v=tri.cross(normal,u)
   xy=[(tri.dot(tri.sub(p,a),u),tri.dot(tri.sub(p,a),v)) for p in vs];lo=[min(p[j] for p in xy) for j in range(2)];hi=[max(p[j] for p in xy) for j in range(2)];width=hi[0]-lo[0];height=hi[1]-lo[1]
   assert max(abs(tri.dot(tri.sub(p,a),normal)) for p in vs)<1e-7
   origin=tri.add(a,tri.add(tri.mul(u,lo[0]),tri.mul(v,lo[1])))
   part=dict(origin=origin,u=u,v=v,width=width,height=height,rotation=tri.euler_zyx(u,v,normal),vertices=vs,mask=[[(p[0]-lo[0])/width,1-(p[1]-lo[1])/height] for p in xy])
   e=tri.to_element(part,n+'/'+str(i),[0,0,1,1]);e['role']=m;e['_surface']=part;self.e.append(e)
 def make(self):
  return self.trustee_source_geometry() if self.w=='trustee' else self.other_source_geometry()
 def other_source_geometry(self):
  w=self.w;self.mat['pink']=dict(kind='paint',color=[155,83,110])
  dims={'succession':(643,130,28.8,-15.3,12.8),'heritage':(453,114,24.3,-8.3,12.9),'commemoration':(585,158,26.9,-11.8,13.8),'iterative_loop':(335,123,24.8,-13,14.3),'circular_logic':(559,147,26.9,-11.8,13.8)}
  W,H,length,z0,top=dims[w];s=length/W;Z=lambda u:z0+u*s;Y=lambda v:top-v*s;side_sign=-1 if w in ('commemoration','iterative_loop','circular_logic') else 1
  def B(n,a,b,t,bot,width,m='shell',xc=0):return self.box(n,8+(side_sign*xc-width/2)*s,Y(bot),Z(a),8+(side_sign*xc+width/2)*s,Y(t),Z(b),m)
  def P(n,a,b,t,bot,width,m='shell',xc=0):self.prism(n,Z(a),Z(b),Y(bot),Y(t),width*s,m,8+side_sign*xc*s)
  def E(n,a,b,width,thick,m='shell',xc=0,round=False):
   if round:self.roundbeam(n,Z(a[0]),Y(a[1]),Z(b[0]),Y(b[1]),thick*s,m,8+side_sign*xc*s)
   else:self.beam(n,Z(a[0]),Y(a[1]),Z(b[0]),Y(b[1]),width*s,thick*s,m,8+side_sign*xc*s)
  def path(n,ps,width,thick,m='shell',xc=0,round=False):
   for i,(a,b) in enumerate(zip(ps,ps[1:])):E(n+'/'+str(i),a,b,width,thick,m,xc,round)
  def S(n,a,b,t,bot,width,m='shell',depth=3):self.sides(n,Z(a),Z(b),Y(bot),Y(t),width*s,m,depth*s)
  def R(n,a,b,cy,r,m='steel',open=False):self.tube(n,Z(a),Z(b),Y(cy),r*s,m,open)
  def F(n,a,b,t,bot,width,m='shell'):self.frame(n,Z(a),Z(b),Y(bot),Y(t),width*s,m)
  def L(n,sections,axis='z',m='shell'):
   self.loft(n,[([8,Y(v),Z(u)],rx*s,ry*s) for u,v,rx,ry in sections],axis,m)
  def C(n,outline,width,m='shell'):
   self.profile_solid(n,[(Y(v),Z(u)) for u,v in outline],width*s,m)
  def grip(a,b,neo=False):
   mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
   if not neo:
    profiles={
     'succession':[(502,54),(519,58),(522,63),(524,68),(527,73),(529,78),(534,88),(539,98),(541,103),(541,108),(538,113),(528,118),(525,128),(522,129),(523,120),(524,115),(517,108),(512,98),(508,88),(503,78),(500,73),(498,68),(500,63)],
     'heritage':[(296,49),(309,50),(314,59),(316,64),(319,69),(324,79),(329,89),(332,99),(332,105),(328,110),(316,111),(309,104),(306,99),(301,89),(297,79),(292,69),(288,64),(287,59),(294,56)],
     'commemoration':[(439,84),(458,87),(461,90),(466,100),(470,110),(476,122),(480,132),(477,137),(471,141),(465,147),(461,145),(461,140),(460,135),(457,130),(454,125),(452,120),(449,115),(446,110),(444,105),(441,100),(440,95),(438,90)]}
    C('grip/source_specific_contour',profiles[w],23,'shell')
   else:
    E('grip/source_mount',(a[0]-2,a[1]-13),a,18,12,'black')
    C('grip/covered_palm',[(a[0]-8,a[1]-2),(a[0]+8,a[1]-4),(b[0]+10,b[1]+1),(b[0]-8,b[1]+5)],20,'rubber')
  if w=='succession':
   R('muzzle/open_ring',0,5,39,7,'steel',True);R('muzzle/suppressor',5,77,39,7,'steel',True);P('muzzle/rear_lock',77,86,30,49,18,'shell')
   P('barrel/front_shroud',86,191,29,47,21,'shell');R('barrel/collar',189,209,38,10,'steel')
   for xc in [-12,12]:B('barrel/channel'+str(xc),91,184,34,39,2,'black',xc);B('barrel/lip'+str(xc),91,185,30,33,3,'steel',xc)
   R('fore/round_upper_core',209,384,39,9,'shell');P('receiver/narrow_action',384,499,26,56,33,'shell')
   for xc in [-18,18]:
    path('fore/long_return'+str(xc),[(218,33),(380,33),(385,38),(381,44),(220,52),(214,48),(214,38),(218,33)],5,5,'shell',xc,True)
    B('fore/recess'+str(xc),226,374,37,41,2,'black',xc)
    path('receiver/slanted_return'+str(xc),[(397,49),(459,38),(474,40),(477,45),(471,49),(420,68),(411,69),(406,62),(397,49)],6,6,'shell',xc,True)
   P('scoop/front',293,336,53,65,24,'rubber');P('scoop/belly',336,378,54,68,25,'rubber');E('scoop/rear',(378,64),(392,54),24,5)
   P('stock/core',499,625,29,50,22,'shell')
   for a in [505,613]:B('stock/return_saddle'+str(a),a,a+8,35,47,34,'steel')
   P('stock/butt_hinge',625,630,30,52,24,'steel')
   for xc in [-15,15]:path('stock/return'+str(xc),[(502,37),(615,37),(622,42),(617,49),(503,56)],5,5,'shell',xc,True)
   L('stock/curved_butt',[(630,17,9,3),(635,27,12,5),(637,64,12,5),(633,84,11,4),(629,91,8,2)],'y','rubber');P('stock/top_lug',622,633,13,25,20,'steel')
   E('mag/angled_case',(442,69),(452,94),31,54,'energy');E('mag/floor',(427,103),(480,85),34,6,'steel')
   for xc in [-18,18]:
    E('mag/coupling'+str(xc),(413,64),(469,47),4,5,'steel',xc)
    for i in range(9):E('mag/loop'+str(xc)+str(i),(420+i*5,73-i*1.5),(422+i*5,80-i*1.5),3,2,'steel',xc)
   grip((509,62),(534,111));path('trigger/open_guard',[(494,57),(502,66),(500,76)],7,3,'steel');E('trigger/blade',(508,54),(513,67),5,3,'black')
   F('optic/long_hood',399,475,5,24,24,'steel');B('optic/bottom_rail',391,485,24,29,23,'black');P('optic/rear_lens_frame',472,481,2,24,28,'steel');B('optic/rear_lens',475,479,7,18,21,'glow')
   anchors=((522,87),(448,80),(438,14))
  elif w=='heritage':
   R('muzzle/lip',0,5,28,7,'steel',True);R('barrel/front',5,65,28,7,'steel',True);R('barrel/central',65,157,28,8,'steel',True);R('barrel/rear',157,211,28,9,'steel',True)
   for z in [50,95,150,199]:R('barrel/collar'+str(z),z,z+5,28,9,'shell')
   B('barrel/rear_saddle',192,211,18,26,13,'shell');R('lower/separate_cylinder',3,211,45,5,'shell');R('lower/secondary_tube',43,209,53,4,'steel')
   for xc in [-17,17]:path('fore/return'+str(xc),[(13,46),(15,32),(23,28),(201,28),(209,33),(207,38),(25,40)],5,5,'shell',xc,True)
   P('receiver/action',211,310,23,49,34,'shell');P('receiver/upper',214,292,18,26,28,'steel');B('receiver/lower_rail',208,304,49,56,30,'shell')
   for xc in [-18,18]:
    B('receiver/bolt_recess'+str(xc),221,271,29,38,3,'black',xc);B('receiver/bolt'+str(xc),225,268,30,34,4,'steel',xc)
    for i in range(8):B('receiver/lower_rib'+str(xc)+str(i),213+i*6,216+i*6,49,56,3,'steel',15.8 if xc>0 else -15.8)
   P('pump/front',85,105,48,66,26,'rubber');P('pump/palm',105,164,55,68,24,'rubber');E('pump/heel',(164,62),(176,71),25,5,'shell')
   for xc in [-15,15]:path('pump/outer_rail'+str(xc),[(87,51),(105,56),(163,56),(170,62)],3,3,'shell',xc)
   grip((293,58),(319,102));path('trigger/open_guard',[(280,50),(286,60),(290,68)],8,3,'steel');E('trigger/blade',(295,48),(299,60),5,3,'black')
   P('stock/front_hinge',309,330,25,48,29,'shell');P('stock/spine',325,430,31,44,20,'shell')
   B('stock/front_crosspin',320,326,32,39,44,'steel');B('stock/back_crosspin',404,411,34,42,44,'steel');B('stock/butt_crosspin',440,446,59,70,44,'steel')
   for a in [228,269]:B('optic/source_mount'+str(a),a,a+6,12,23,18,'steel')
   for xc in [-19,19]:
    path('stock/front_return'+str(xc),[(314,35),(324,35),(385,74),(390,75),(394,70),(388,62),(337,28)],7,7,'shell',xc,True)
    path('stock/back_return'+str(xc),[(402,35),(428,35),(431,40),(412,43),(406,49),(412,55),(437,75),(441,72),(443,63)],7,7,'shell',xc,True)
   L('stock/curved_butt',[(447,21,10,3),(449,29,13,5),(447,72,13,5),(450,84,11,4),(453,88,8,2)],'y','rubber');B('optic/low_hood_floor',220,281,8,12,21,'black');F('optic/open_sides',220,281,1,12,22,'steel')
   B('shell_insert',235,249,49,55,14,'gold');anchors=((307,80),(242,52),(250,7))
  elif w=='commemoration':
   F('muzzle/paired_port',0,19,33,75,35,'steel');P('fore/upper_shroud',20,341,28,63,48,'shell');P('fore/lower_body',27,342,64,87,44,'shell')
   B('fore/top_rail',26,339,24,29,35,'steel');B('fore/barrel_recess',27,337,62,68,32,'black')
   for xc in [-27,27]:
    path('fore/upper_return'+str(xc),[(27,45),(30,36),(39,33),(328,33),(337,38),(338,46),(330,49),(37,49)],7,7,'shell',xc,True)
    path('fore/lower_return'+str(xc),[(110,57),(89,78),(96,82),(330,82),(339,77),(336,70),(122,70)],7,7,'shell',xc,True)
    B('fore/slot1'+str(xc),41,148,42,47,3,'black',xc);B('fore/slot2'+str(xc),249,327,42,47,3,'black',xc)
    for i in range(4):B('fore/round_vent'+str(xc)+str(i),156+i*10,162+i*10,36,43,3,'black',xc)
   B('fore/underbody_front_mount',95,103,84,94,30,'steel');B('fore/underbody_rear_mount',150,158,84,94,30,'steel')
   C('fore/long_bowed_underbody',[(169,86),(204,85),(335,94),(337,103),(285,99),(235,94),(201,92),(188,100),(180,103),(174,96)],30,'rubber')
   B('fore/underbridge',86,163,91,98,30,'steel');L('fore/bowed_hand_support',[(87,99,10,4),(103,102,13,7),(129,108,14,8),(150,112,13,7),(163,111,10,4)],'z','shell');B('fore/handstop',157,164,99,130,27,'steel')
   for a in [97,129]:B('fore/slot_divider'+str(a),a,a+5,97,108,26,'shell')
   P('receiver/feed_action',341,421,23,104,49,'shell');B('receiver/top_cover',345,421,20,26,43,'steel')
   P('mag/upper_latch',348,421,104,116,57,'steel');P('mag/body',349,420,116,149,60,'energy');P('mag/floor',355,414,149,156,52,'steel')
   for xc in [-32,32]:
    for i in range(10):B('mag/rib'+str(xc)+str(i),352+i*6,355+i*6,112,120,3,'steel',xc)
   # Actual descending ammunition belt on the source's exposed side.
   for i in range(7):
    xc=26+i*4.3;yy=48+i*7.4;P('feed/round'+str(i),352,382,yy,yy+4,9,'steel',xc);P('feed/link'+str(i),367,373,yy-1,yy+6,11,'black',xc)
   P('rear/receiver',421,563,30,90,42,'shell');P('rear/upper_rail',426,562,27,35,34,'steel')
   for xc in [-24,24]:
    path('rear/long_return'+str(xc),[(430,42),(551,42),(558,46),(553,51),(431,51)],5,5,'shell',xc,True)
    B('rear/actuator'+str(xc),503,561,52,62,5,'steel',xc)
   grip((442,93),(466,139));E('trigger/blade',(433,84),(439,99),6,4,'black')
   path('stock/lower_frame',[(471,93),(477,125),(557,118),(563,92)],25,7,'shell');B('stock/mid_divider',508,514,95,123,24,'shell');P('stock/recessed_cell',481,557,92,108,18,'energy');L('stock/curved_butt',[(566,15,13,3),(575,28,17,5),(578,70,17,5),(573,118,17,5),(568,139,12,3)],'y','steel')
   B('optic/base',366,395,18,23,22,'black');F('optic/prong',377,381,1,18,21,'steel');B('optic/emitter',391,395,17,20,4,'glow');anchors=((454,117),(385,133),(381,10))
  elif w=='iterative_loop':
   # Rectangular three-level muzzle and deep lower casing, not a round sci-fi tube.
   F('muzzle/rectangular_port',0,8,5,29,35,'steel');P('fore/upper_bar',8,141,5,16,32,'shell');P('fore/lower_case',0,141,28,52,35,'shell');P('fore/inner_core',8,141,17,29,25,'black')
   for xc in [-20,20]:B('fore/neon_recess'+str(xc),8,136,18,22,3,'glow',xc);B('fore/blue_lip'+str(xc),8,137,15,18,4,'accent',xc)
   for a in [15,77,123]:P('fore/top_panel'+str(a),a,a+16,3,5,29,'shell')
   P('receiver/breech_coupling',141,143,16,52,33,'steel');P('receiver/central_shoulder',142,194,3,60,41,'shell');P('receiver/top_latch',146,190,0,6,34,'steel');B('receiver/upper_step',151,174,0,3,20,'black')
   P('mag/main_cell',144,193,36,108,36,'accent');P('mag/bottom',142,195,108,122,40,'steel')
   for xc in [-21,21]:
    B('mag/vertical_channel'+str(xc),153,158,36,108,3,'black',xc);B('mag/inner_light'+str(xc),161,164,34,105,3,'gold',xc);B('mag/rear_channel'+str(xc),180,184,36,108,3,'black',xc)
    for yy in [105,111,117]:B('mag/cell_clamp'+str(xc)+str(yy),143,194,yy,yy+3,4,'steel',xc)
   P('rear/main_action',194,319,18,44,29,'shell');B('rear/top_lip',197,318,15,19,24,'steel')
   for xc in [-14.5,14.5]:B('rear/neon_recess'+str(xc),201,313,22,26,3,'glow',xc);B('rear/lower_rail'+str(xc),199,314,34,38,3,'steel',xc)
   P('stock/butt',320,333,3,61,31,'steel');B('stock/rear_pad',333,335,7,57,27,'rubber');P('stock/rear_sight',313,324,1,15,21,'steel')
   grip((225,51),(250,101),True);B('trigger/upper_pivot',214,223,42,50,14,'black');E('trigger/blade',(220,48),(220,61),6,4,'steel');anchors=((238,75),(168,78),(170,3))
  else:
   R('muzzle/open_lip',0,7,44,12,'steel',True);R('fore/round_lower_barrel',7,298,46,19,'shell');P('fore/upper_case',7,298,24,38,41,'shell');P('fore/upper_shoulder',9,298,21,29,38,'black');P('fore/lower_rail',7,298,62,70,36,'steel')
   for xc in [-21,21]:
    B('fore/light_channel'+str(xc),15,290,29,33,3,'glow',xc);B('fore/blue_channel_lip'+str(xc),15,290,25,29,4,'accent',xc)
    path('fore/coolant_loop'+str(xc),[(85,25),(89,43),(96,50),(166,50),(181,53),(204,50),(217,31),(229,25)],4,4,'black',19 if xc>0 else -19,True)
    B('fore/lower_recess'+str(xc),10,291,57,60,3,'black',20.5 if xc>0 else -20.5)
   P('underbarrel/front_mount',83,153,68,78,26,'black');P('underbarrel/handguard',153,295,70,86,31,'steel')
   for xc in [-16.5,16.5]:B('underbarrel/source_tech_panel'+str(xc),162,282,74,83,4,'shell',xc)
   P('receiver/front_breech',297,328,23,80,48,'steel');P('receiver/action',328,422,24,78,44,'black');P('receiver/top_latch',307,419,19,26,37,'shell')
   for xc in [-23,23]:B('receiver/long_port'+str(xc),337,395,33,45,4,'black',xc);B('receiver/bolt'+str(xc),341,390,35,39,4,'steel',xc)
   # Rounded box drum has a broad cross-section, rolled lower body and recessed top.
   P('mag/upper',330,395,78,98,55,'black');P('mag/middle',327,398,98,124,65,'shell');P('mag/lower',334,392,124,136,57,'shell');P('mag/floor',342,384,136,141,43,'steel')
   for xc in [-35,35]:
    path('mag/rounded_wall'+str(xc),[(334,85),(330,94),(330,120),(338,131),(350,136),(381,136),(392,125),(395,94),(391,85)],5,5,'steel',xc,True)
    for yy in [113,119,125]:B('mag/corrugation'+str(xc)+str(yy),335,391,yy,yy+3,4,'steel',xc)
   for i in range(8):
    xc=25+i*8;yy=47+i*4.6;P('feed/round'+str(i),342,361,yy,yy+4,10,'steel',xc);P('feed/link'+str(i),349,354,yy-1,yy+6,12,'black',xc)
   P('rear/main_action',422,548,30,64,31,'shell');P('rear/top_panel',431,546,26,34,26,'steel')
   for xc in [-16,16]:B('stock/neon_recess'+str(xc),431,542,34,38,3,'glow',xc);B('stock/lower_line'+str(xc),430,542,54,57,3,'steel',xc)
   P('stock/butt',548,559,22,79,32,'steel');grip((442,78),(472,132),True);E('trigger/blade',(431,74),(434,88),6,4,'black');B('optic/base',346,379,19,23,23,'black');F('optic/hood',360,365,1,19,22,'steel');anchors=((457,105),(363,111),(362,10))
  self.source_transform=dict(kind='one uniform source-to-model transform',scale_model_px_per_source_metre=s*420,side_crop_pixels=[W,H],uniform_model_px_per_reference_pixel=s,canonical_from_reference=dict(z_offset=z0,y_top=top,x_center=8),grip_model=[8,Y(anchors[0][1]),Z(anchors[0][0])],magazine_model=[8,Y(anchors[1][1]),Z(anchors[1][0])],sight_model=[8,Y(anchors[2][1]),Z(anchors[2][0])],donor_framing='No per-part stretch. Master must adapt donor hand/sight framing to authored source proportions.')
  return self.e
 def trustee_source_geometry(self):
  """Authored in the calibrated original side-image coordinates, one uniform scale.
  Input crop is 566x178 at 420 px/m. All three spatial axes use 24.85/566.
  No donor-grip split warp. Main shape and pipe routes are source observations.
  """
  self.mat['pink']=dict(kind='paint',color=[155,83,110]);s=24.85/566;z0=-9.2;yTop=12.4
  Z=lambda u:z0+u*s;Y=lambda v:yTop-v*s
  def B(n,a,b,top,bottom,width,m='shell',xc=0):return self.box(n,8+(xc-width/2)*s,Y(bottom),Z(a),8+(xc+width/2)*s,Y(top),Z(b),m)
  def P(n,a,b,top,bottom,width,m='shell',xc=0):self.prism(n,Z(a),Z(b),Y(bottom),Y(top),width*s,m,8+xc*s)
  def E(n,a,b,width,thick,m='shell',xc=0):
   if 'return' in n:self.roundbeam(n,Z(a[0]),Y(a[1]),Z(b[0]),Y(b[1]),thick*s,m,8+xc*s)
   else:self.beam(n,Z(a[0]),Y(a[1]),Z(b[0]),Y(b[1]),width*s,thick*s,m,8+xc*s)
  def S(n,a,b,top,bottom,width,m='shell',depth=3):self.sides(n,Z(a),Z(b),Y(bottom),Y(top),width*s,m,depth*s)
  def R(n,a,b,cy,r,m='steel',open=False):self.tube(n,Z(a),Z(b),Y(cy),r*s,m,open)
  def path(n,points,width,thick,m='shell',xc=0):
   for i,(a,b) in enumerate(zip(points,points[1:])):E(n+'/'+str(i),a,b,width,thick,m,xc)
  def L(n,sections,axis='z',m='shell'):
   self.loft(n,[([8,Y(v),Z(u)],rx*s,ry*s) for u,v,rx,ry in sections],axis,m)
  # Slotted muzzle, stepped locking collars, and narrow connecting barrel.
  self.tube('muzzle/open_lip',Z(0),Z(5),Y(44),6*s,'steel',True,12)
  self.tube('muzzle/perforated_sleeve',Z(5),Z(65),Y(44),6*s,'steel',True,12,[(Z(a),Z(b)) for a,b in [(5,10),(18,23),(31,36),(44,49),(57,65)]])
  P('muzzle/bore_end',65,70,39,49,8,'black')
  R('muzzle/lock_collar',70,89,44,10,'shell');R('muzzle/collar_front',68,73,44,8,'steel');R('muzzle/collar_rear',87,93,44,8,'steel')
  P('barrel/neck',93,121,39,49,10,'steel');R('barrel/coupling',120,143,44,9,'shell');R('barrel/gold_lock',137,143,44,9.5,'gold')
  # Tapered narrow upper mechanism: width and vertical profile change by section.
  P('action/front_taper',143,161,35,57,22,'shell');R('action/front_shroud',161,234,46,14,'shell');R('action/rear_shroud',234,278,47,16,'shell')
  P('action/central_breech',278,350,31,62,37,'shell');P('action/rear_carrier',350,425,35,62,31,'shell')
  P('action/rear_hinge',420,448,34,66,36,'steel')
  # Real longitudinal recessed channels, bounded by structural top and lower lips.
  for xc in [-1,1]:
   x=xc*17
   B('fore/deep_channel'+str(xc),159,268,40,46,2,'black',x)
   B('fore/upper_runner'+str(xc),154,269,36,40,3,'steel',x)
   B('fore/lower_runner'+str(xc),163,255,46,50,3,'shell',x)
   E('fore/lower_ramp'+str(xc),(255,48),(276,42),3,4,'shell',x)
   B('fore/secondary_channel'+str(xc),169,258,54,57,2,'black',x)
   E('fore/angled_front_face'+str(xc),(146,38),(162,33),4,4,'white',xc*13)
   B('receiver/upper_recess'+str(xc),285,334,35,40,2,'black',xc*20)
   B('receiver/steel_bolt'+str(xc),288,329,36,38,3,'steel',xc*21)
   B('receiver/teal_cartridge'+str(xc),354,409,38,44,3,'energy',xc*17)
   B('receiver/pink_actuator'+str(xc),368,400,45,52,4,'pink',xc*18)
   B('receiver/action_latch'+str(xc),336,344,33,59,4,'steel',xc*20)
  # Bowed lower scoop, open upper relief and a lower grip with stepped end ramps.
  L('scoop/closed_bowed_palm',[(169,67,10,4),(181,74,13,6),(213,75,14,7),(250,79,14,9),(272,78,13,8),(286,72,10,5)],'z','rubber')
  E('scoop/rear_mount',(288,77),(281,65),24,5,'shell')
  for xc in [-15,15]:
   path('scoop/outer_rail'+str(xc),[(169,64),(183,68),(261,68),(280,64)],3,3,'shell',xc)
  # Trigger opening, continuous raked grip and white projecting heel.
  path('trigger/front_open_guard',[(293,65),(299,74),(313,70)],10,3,'steel')
  E('trigger/rear_open_guard',(350,74),(356,87),8,3,'steel')
  E('trigger/blade',(345,64),(350,76),5,4,'black')
  B('trigger/front_mount',290,297,59,67,12,'steel');B('trigger/rear_mount',342,351,58,66,10,'steel')
  self.profile_solid('grip/source_specific_contour',[(Y(v),Z(u)) for u,v in [(360,59),(380,59),(383,65),(385,70),(388,75),(390,80),(392,85),(397,95),(402,105),(406,115),(401,120),(398,125),(395,130),(391,135),(388,140),(385,140),(385,135),(388,130),(389,125),(386,120),(384,115),(381,110),(378,105),(374,95),(371,90),(368,85),(368,80),(364,75),(364,70),(361,65)]],23*s,'shell')
  # Rear mechanism is a deep group of rounded return tubes, not flat stock strips.
  P('rear/central_spine',430,547,32,53,25,'shell')
  for xc in [-19,19]:
   path('rear/upper_return'+str(xc),[(438,39),(455,39),(517,68),(524,68),(531,61),(533,52),(529,47),(504,34)],7,7,'shell',xc)
   path('rear/middle_return'+str(xc),[(432,51),(489,78),(508,88),(517,88),(524,80),(522,72),(478,49)],7,7,'shell',xc)
   path('rear/lower_return'+str(xc),[(439,66),(491,96),(503,104),(511,102),(519,93),(513,85),(474,63)],7,7,'shell',xc)
   B('rear/pink_release'+str(xc),470,486,51,60,5,'pink',xc)
   E('rear/teal_actuator'+str(xc),(444,39),(480,55),5,6,'energy',xc)
  L('rear/curved_butt',[(552,27,11,3),(561,36,14,5),(562,66,14,5),(555,84,13,4),(551,89,10,3)],'y','rubber')
  P('rear/butt_hinge',543,555,36,58,28,'steel')
  B('rear/butt_upper_pin',549,556,28,34,41,'steel');B('rear/butt_lower_pin',549,556,84,90,41,'steel')
  for xc in [-18,18]:
   path('rear/butt_upper_frame'+str(xc),[(547,28),(554,25),(562,32),(552,40)],4,4,'steel',xc)
   path('rear/butt_lower_frame'+str(xc),[(552,78),(562,85),(553,94),(549,89)],4,4,'steel',xc)
  # Source magazine follows the full-depth downward-forward rake.
  E('mag/core',(486,109),(452,161),31,41,'shell')
  E('mag/backbone',(504,115),(471,168),32,6,'steel')
  E('mag/floor',(432,153),(469,176),35,8,'energy')
  for xc in [-18,18]:
   E('mag/coupling_band'+str(xc),(453,100),(497,127),4,7,'steel',xc)
   for i in range(7):E('mag/spring'+str(xc)+str(i),(454+i*6,99+i*3.7),(451+i*6,105+i*3.7),4,2,'black',xc)
  # Source prongs sit above the central breech, long open rail between them.
  P('optic/rail',271,345,24,29,20,'black')
  for a in [279,331]:B('optic/source_foot'+str(a),a,a+7,29,34,16,'steel')
  for a in [273,342]:
   for xc in [-10,10]:B('optic/prong'+str(a)+str(xc),a,a+4,9,27,4,'shell',xc)
  B('optic/front_crossbar',273,277,20,23,20,'steel')
  B('optic/rear_emitter',339,343,24,26,4,'glow')
  self.source_transform=dict(kind='one uniform source-to-model transform',scale_model_px_per_source_metre=s*420,side_crop_pixels=[566,178],uniform_model_px_per_reference_pixel=s,canonical_from_reference=dict(z_offset=z0,y_top=yTop,x_center=8),grip_model=[8,Y(93),Z(380)],magazine_model=[8,Y(135),Z(474)],sight_model=[8,Y(20),Z(310)],donor_framing='Not used to warp source proportions; master adapts framing')
  return self.e

def paint(e,fn,size,mats,projection=None):
 w,h=size;m=mats[e['role']];c=tuple(m['color']);im=Image.new('RGBA',size,c+(255,));d=ImageDraw.Draw(im);name=e['name'];side=fn in ('east','west');dark=tuple(max(0,int(v*.63)) for v in c)+(255,);lit=tuple(min(255,v+13) for v in c)+(255,)
 if projection and side and any(v in name for v in ['source_shell_panel','inset_circuit','tech_panel','rear_action','mag/core']):
  # Calibrated silhouette fit of actual evaluated albedo side, restricted to
  # shallow engraved detail. Not a PBR bake or an exact per-part correspondence.
  raw,blur,alpha,bounds,k,transform,source=projection;z0,z1,y0,y1=bounds;px=im.load()
  for i in range(1,w-1):
   for j in range(1,h-1):
    p=k.face_point(e,fn,(i+.5)/w,(j+.5)/h);u=int((p[2]-z0)/(z1-z0)*(raw.width-1));v=int((y1-p[1])/(y1-y0)*(raw.height-1))
    if 2<=u<raw.width-2 and 2<=v<raw.height-2 and alpha.getpixel((u,v))>250:
     delta=raw.getpixel((u,v))-blur.getpixel((u,v));q=-17 if delta<-13 else -8 if delta<-5 else 0
     px[i,j]=tuple(max(0,a+q) for a in c)+(255,)
 # Source-calibrated grip material masks; geometry is kept fixed at R6.
 if projection and e.get('_surface') and name.startswith('grip/'):
  raw,blur,alpha,bounds,k,transform,source=projection;normal=k.rotate_vec(k.NORMALS[fn],k.rot_of(e));ss=transform['uniform_model_px_per_reference_pixel'];offset=transform['canonical_from_reference'];px=im.load()
  if abs(normal[0])>.7:
   for i in range(w):
    for j in range(h):
     p=k.face_point(e,fn,(i+.5)/w,(j+.5)/h);u=round((p[2]-offset['z_offset'])/ss);v=round((offset['y_top']-p[1])/ss)
     if 0<=u<source.width and 0<=v<source.height:
      rgb=source.getpixel((u,v));value=sum(rgb[:3])/3
      if rgb[3]>128 and value<78:px[i,j]=tuple(mats['rubber']['color'])+(255,)
      elif 'covered_palm' in name:px[i,j]=tuple(mats['steel']['color'])+(255,)
 # Single-pixel material edge; no airbrush field, dirt, or all-edge broad gradients.
 if min(w,h)>3 and not e.get('_surface') and e['role'] not in ('glow','gold','seam'):
  d.line((0,0,w-1,0),fill=lit);d.line((0,h-1,w-1,h-1),fill=dark)
 if side and min(w,h)>6:
  if any(t in name for t in ['inset','tech_panel','face_channel','sleeve']):
   d.line([(2,h-4),(max(3,w//6),h-4),(max(3,w//6)+2,h-2),(w-5,h-2),(w-3,h-4),(w-3,3)],fill=dark,width=1)
   d.line((2,2,w-3,2),fill=lit)
   if 'circuit' in name:
    if '/center' in name:
     d.rectangle((max(2,w-8),3,max(3,w-4),max(4,h//4)),fill=tuple(mats['pink']['color'])+(255,))
     for x in range(4,min(w-8,20),3):d.line((x,h-6,x,h-5),fill=dark)
     for x in [4,w-5]:d.ellipse((x-1,4,x+1,6),outline=dark)
   if 'tech' in name:
    for x in range(4,w-3,6):d.line((x,3,x,min(h-3,6)),fill=tuple(mats['steel']['color'])+(255,))
  if 'lattice' in name:
   for x in range(-h,w+h,7):d.line((x,0,x+h,h),fill=dark);d.line((x,0,x-h,h),fill=dark)
  if 'rubber' in name or 'pump/' in name:
   for x in range(3,w-2,5):d.line((x,2,x,h-3),fill=dark)
  if name.startswith('mag/') and 'core' in name:
   for y in [h//3,2*h//3]:d.line((3,y,w-4,y),fill=dark)
   for x in range(3,w-4,5):d.arc((x,3,x+4,8),180,360,fill=dark,width=1)
  if 'source_shell_panel' in name and '/center' in name:
   d.line([(2,4),(5,2),(w-6,2),(w-3,5)],fill=lit)
   d.line([(2,h-3),(w-5,h-3),(w-3,h-5)],fill=dark)
   for x in [5,w-6]:d.ellipse((x-1,h//2-1,x+1,h//2+1),outline=dark)
 return im

def coplanar(es,k):
 """Same-facing world-space planes with actual polygon overlap; rotations supported."""
 def dot(a,b):return sum(x*y for x,y in zip(a,b))
 def sub(a,b):return [x-y for x,y in zip(a,b)]
 def clip(poly,mask):
  cross=lambda a,b:a[0]*b[1]-a[1]*b[0]
  area=sum(cross(mask[i],mask[(i+1)%len(mask)]) for i in range(len(mask)))
  if area<0:mask=mask[::-1]
  for a,b in zip(mask,mask[1:]+mask[:1]):
   out=[];edge=sub(b,a)
   for p,q in zip(poly,poly[1:]+poly[:1]):
    dp=cross(edge,sub(p,a));dq=cross(edge,sub(q,a));ip=dp>=-1e-7;iq=dq>=-1e-7
    if ip:out.append(p)
    if ip!=iq:
     t=dp/(dp-dq);out.append([p[j]+t*(q[j]-p[j]) for j in range(2)])
   poly=out
   if not poly:break
  return poly
 fs=[]
 for i,e in enumerate(es):
  if e.get('_surface') or e['from'][2]==e['to'][2]:continue
  for fn in k.FACE_AXES:
   n=k.rotate_vec(k.NORMALS[fn],k.rot_of(e));p=k.face_point(e,fn,0,0);_,u,v=k.face_frame(e,fn);u=k.rotate_vec(u,k.rot_of(e));v=k.rotate_vec(v,k.rot_of(e));u=[q/math.dist(u,(0,0,0)) for q in u];v=[q/math.dist(v,(0,0,0)) for q in v]
   ps=[k.face_point(e,fn,s,t) for s,t in [(0,0),(1,0),(1,1),(0,1)]];fs.append((i,fn,n,p,u,v,ps))
 bad=[]
 for pos,(i,fn,n,p,u,v,ps) in enumerate(fs):
  for j,gn,nn,q,_,__,qs in fs[pos+1:]:
   if i==j or es[i]['name'].startswith('mag/')!=es[j]['name'].startswith('mag/'):continue
   if dot(n,nn)<.999999 or abs(dot(n,sub(p,q)))>1e-6:continue
   proj=lambda pts:[[dot(sub(t,p),u),dot(sub(t,p),v)] for t in pts]
   overlap=clip(proj(ps),proj(qs))
   if len(overlap)<3:continue
   area=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(overlap,overlap[1:]+overlap[:1])))/2
   if area<1e-5:continue
   c=[sum(t[a] for t in overlap)/len(overlap) for a in range(2)];world=[p[a]+u[a]*c[0]+v[a]*c[1]+n[a]*.002 for a in range(3)]
   if any(k.inside(o,world) for oi,o in enumerate(es) if oi not in (i,j)):continue
   bad.append((i,fn,j,gn,round(area,6)))
 return bad

def clean_joins(es,k):
 edits=[]
 for _ in range(12):
  bad=coplanar(es,k)
  if not bad:break
  seen=set()
  for i,fn,j,gn,area in bad:
   ax,side,*_=k.FACE_AXES[gn];key='to' if side else 'from'
   if (j,key,ax) in seen:continue
   seen.add((j,key,ax));eps=.002+j*.000001;es[j][key][ax]+=eps if side else -eps;edits.append(dict(element=es[j]['name'],face=gn,outward=eps,overlap_area=area))
 return edits

def optimize_document(doc, image):
 """Cull only faces covered by opaque solid volumes in the SAME animated part.

 A face is offset 1e-6 outward before subtracting convex OBB volumes. This
 retains coincident exterior paint layers and only removes buried/contact
 surfaces. Alpha polygon lofts never occlude other geometry. UVs, transforms,
 silhouette and material pixels of all surviving faces are untouched.
 """
 import copy
 k=kit();result=copy.deepcopy(doc);removed=[];empty=[]
 def dot(a,b):return sum(x*y for x,y in zip(a,b))
 def clip(poly,n,d,inside):
  out=[]
  for a,b in zip(poly,poly[1:]+poly[:1]):
   da=dot(a,n)-d;db=dot(b,n)-d;ia=da<=0 if inside else da>=0;ib=db<=0 if inside else db>=0
   if ia:out.append(a)
   if ia!=ib:
    t=da/(da-db);out.append([a[j]+t*(b[j]-a[j]) for j in range(3)])
  return out
 def area(poly):
  if len(poly)<3:return 0
  a=poly[0];s=[0.,0.,0.]
  for b,c in zip(poly[1:],poly[2:]):
   u=[b[j]-a[j] for j in range(3)];v=[c[j]-a[j] for j in range(3)]
   for j in range(3):s[j]+=u[(j+1)%3]*v[(j+2)%3]-u[(j+2)%3]*v[(j+1)%3]
  return math.sqrt(dot(s,s))/2
 def opaque(e):
  if any(e['to'][i]-e['from'][i]<1e-8 for i in range(3)):return False
  if set(e['faces'])!=set(k.FACE_AXES):return False
  for f in e['faces'].values():
   u,v,U,V=f['uv'];x,X=sorted((u*image.width/16,U*image.width/16));y,Y=sorted((v*image.height/16,V*image.height/16))
   if image.crop((math.floor(x),math.floor(y),math.ceil(X),math.ceil(Y))).getchannel('A').getextrema()[0]!=255:return False
  return True
 for part,es in result['parts'].items():
  solids=[]
  for i,e in enumerate(es):
   if not opaque(e):continue
   points=k._corners(e);bounds=([min(p[j] for p in points) for j in range(3)],[max(p[j] for p in points) for j in range(3)])
   planes=[]
   for fn in k.FACE_AXES:
    n=k.rotate_vec(k.NORMALS[fn],k.rot_of(e));p=k.face_point(e,fn,0,0);planes.append((n,dot(p,n)))
   solids.append((i,bounds,planes))
  for i,e in enumerate(es):
   for fn in list(e['faces']):
    n=k.rotate_vec(k.NORMALS[fn],k.rot_of(e));poly=[[v+1e-6*n[j] for j,v in enumerate(k.face_point(e,fn,s,t))] for s,t in [(0,0),(1,0),(1,1),(0,1)]]
    bounds=([min(p[j] for p in poly) for j in range(3)],[max(p[j] for p in poly) for j in range(3)])
    remaining=[poly];occluders=[]
    for j,(lo,hi),planes in solids:
     if i==j or any(bounds[1][a]<lo[a] or bounds[0][a]>hi[a] for a in range(3)):continue
     next_remaining=[];changed=False
     for polygon in remaining:
      intersection=polygon
      for normal,distance in planes:
       intersection=clip(intersection,normal,distance,True)
       if area(intersection)<1e-14:break
      if area(intersection)<1e-14:next_remaining.append(polygon);continue
      changed=True;inside=polygon
      for normal,distance in planes:
       outside=clip(inside,normal,distance,False)
       if area(outside)>1e-14:next_remaining.append(outside)
       inside=clip(inside,normal,distance,True)
       if not inside:break
     remaining=next_remaining
     if changed:occluders.append(es[j]['name'])
     if not remaining:break
    if not remaining:
     del e['faces'][fn];removed.append(dict(part=part,element=e['name'],face=fn,occluders=occluders))
  empty.extend(dict(part=part,element=e['name']) for e in es if not e['faces'])
  result['parts'][part]=[e for e in es if e['faces']]
 def counts(d):return dict(elements=sum(len(es) for es in d['parts'].values()),faces=sum(len(e['faces']) for es in d['parts'].values() for e in es),parts={p:len(es) for p,es in d['parts'].items()})
 return result,dict(method='Exact convex-volume subtraction of outward-offset faces; opaque cuboids only; per animated part',before=counts(doc),after=counts(result),removed_faces=removed,removed_elements=empty,uv_and_material_pixels='UNCHANGED',native_qa='MASTER_PENDING')

def optimize(w):
 doc=json.loads(skin(w).read_text());before=sha(skin(w));out,report=optimize_document(doc,Image.open(atlas(w)).convert('RGBA'))
 skin(w).write_text(json.dumps(out,separators=(',',':')))
 report.update(before_sha256=before,after_sha256=sha(skin(w)))
 (art(w)/'optimization.json').write_text(json.dumps(report,indent=1)+'\n')
 manifest=json.loads((art(w)/'manifest.json').read_text());manifest.update(element_total=report['after']['elements'],elements=report['after']['parts'],optimization=report['method'])
 manifest['outputs_sha256'][str(skin(w).relative_to(ROOT))]=sha(skin(w))
 (art(w)/'manifest.json').write_text(json.dumps(manifest,indent=1)+'\n')
 print(w,report['before'],report['after'],flush=True)

def build(w):
 M=Model(w);es=M.make();k=kit();T=14 if w=='commemoration' else 16;W=1024;faces=[]
 joins=clean_joins(es,k);(art(w)/'v3/join-adjustments.json').write_text(json.dumps(joins,indent=1))
 source=Image.open(MAIN/'art/weapons/w327'/w/'review'/('source_py.png' if w in ('commemoration','circular_logic','iterative_loop') else 'source_px.png')).convert('RGBA');source=source.crop(source.getbbox())
 raw=source.convert('L').filter(ImageFilter.MedianFilter(3));blur=raw.filter(ImageFilter.GaussianBlur(3));alpha=source.getchannel('A').filter(ImageFilter.MinFilter(5))
 pts=[p for e in es for p in k._corners(e)];bounds=[min(p[2] for p in pts),max(p[2] for p in pts),min(p[1] for p in pts),max(p[1] for p in pts)];projection=(raw,blur,alpha,bounds,k,M.source_transform,source)
 for e in es:
  for fn in (['south'] if e.get('_surface') else k.FACE_AXES):
   _,u,v=k.face_frame(e,fn);density=32 if e.get('_surface') else T;size=(max(2,round(math.dist((0,0,0),u)*density)),max(2,round(math.dist((0,0,0),v)*density)))
   im=paint(e,fn,size,M.mat,projection)
   if e.get('_surface'):
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon([(u*(im.width-1),v*(im.height-1)) for u,v in e['_surface']['mask']],fill=255);im.putalpha(mask.filter(ImageFilter.MaxFilter(3)))
   faces.append((e,fn,im))
 faces.sort(key=lambda f:(-f[2].height,-f[2].width));at=Image.new('RGBA',(W,W));x=y=row=1
 for e,fn,im in faces:
  if x+im.width+2>W:x=1;y+=row;row=0
  assert y+im.height+2<=W,(w,'atlas overflow')
  at.paste(im,(x,y));at.paste(im.crop((0,0,im.width,1)),(x,y-1));at.paste(im.crop((0,im.height-1,im.width,im.height)),(x,y+im.height))
  e.setdefault('faces',{})[fn]=dict(texture='#0',uv=[16*x/W,16*y/W,16*(x+im.width)/W,16*(y+im.height)/W]);x+=im.width+2;row=max(row,im.height+2)
 H=2**math.ceil(math.log2(y+row));at=at.crop((0,0,W,H))
 for e in es:
  for f in e['faces'].values():f['uv'][1]*=W/H;f['uv'][3]*=W/H
 out=[]
 for e in es:
  if e.get('_surface'):
   uv=e['faces']['south']['uv'];e['faces']['north']=dict(texture='#0',uv=[uv[2],uv[1],uv[0],uv[3]])
  out.append({a:b for a,b in e.items() if a not in ('role','_surface')})
 doc=dict(texture_size=[W,H],parts=dict(body=[e for e in out if not e['name'].startswith('mag/')],magazine=[e for e in out if e['name'].startswith('mag/')]))
 skin(w).write_text(json.dumps(doc,separators=(',',':')));at.save(atlas(w),optimize=True);k.hud_icon(out,hud(w),lambda n:False)
 (art(w)/'design.json').write_text(json.dumps(dict(revision=3,materials=M.mat,elements=es,source_transform=getattr(M,'source_transform',None)),indent=1)+'\n')
 (art(w)/'design.py').write_text("from pathlib import Path\nimport json\nD=json.loads(Path(__file__).with_name('design.json').read_text())\nSTYLE='material'\nT=16\nATLAS=1024\nMATERIALS=D['materials']\ndef elements():return D['elements']\ndef is_magazine(n):return n.startswith('mag/')\n")
 ev=json.loads((art(w)/'source-evaluation.json').read_text());assert sha(ev['source'])==ev['sha256']
 old=json.loads((art(w)/'manifest.json').read_text());old.update(revision=3,element_total=len(es),elements={p:len(e) for p,e in doc['parts'].items()},atlas=[W,H],authoring='Source-coordinate reconstruction with round tube sections and closed sculpted section lofts, native cuboids plus alpha-masked closed polygon lofts; original blend reopened in independent background review',material_pipeline='Role color blocks + face-specific single-texel seams/DSC and Neomuna motifs; static RGBA, no PBR claim',outputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in (skin(w),atlas(w),hud(w))},source_evaluation_reused=True,source_transform=getattr(M,'source_transform',None),acceptance='PROVISIONAL_SOURCE_FIDELITY_REVIEW',priority='Source exterior first; materials second; optimization last')
 (art(w)/'manifest.json').write_text(json.dumps(old,indent=1)+'\n');print(w,len(es),[W,H],flush=True)
 optimize(w)

def render(w,version='v3'):
 k=kit();src=(MAIN/'scripts/art/w325/render_model.py').read_text();src=src.replace("for f, fc in e['faces'].items():","for f, fc in e['faces'].items():\n        if lo[2]==hi[2] and f=='north':continue");src=src.replace("'rear': (0, -1, 0)","'rear': (-0.7, -0.45, -0.45)")
 src=src.replace("sc.render.engine = 'BLENDER_EEVEE'", "sc.render.engine = 'CYCLES'; sc.cycles.samples=16; sc.cycles.use_denoising=True; sc.cycles.max_bounces=3; sc.render.threads_mode='FIXED'; sc.render.threads=4")
 if version=='neutral':src=src.replace("nt.links.new(ti.outputs[0], bs.inputs['Base Color']); nt.links.new(ti.outputs[1], bs.inputs['Alpha']);", "bs.inputs['Base Color'].default_value=(.45,.45,.45,1); nt.links.new(ti.outputs[1], bs.inputs['Alpha']);")
 src=src.replace('cam.ortho_scale = ext',"M=co.rotation_euler.to_matrix().transposed(); pp=[M @ (mathutils.Vector(v)-c) for v in pts]; rw=max(v.x for v in pp)-min(v.x for v in pp); rh=max(v.y for v in pp)-min(v.y for v in pp); cam.ortho_scale=max(rw,rh*1200/700)*1.12")
 p=art(w)/'v3/render-review.py';p.write_text(src)
 sp=skin(w) if version in ('v3','neutral','hero') else art(w)/'v3/v2_skin.json';tp=atlas(w) if version in ('v3','neutral','hero') else art(w)/'v3/v2_atlas.png'
 subprocess.run([k.BLENDER,'-b','--factory-startup','--disable-autoexec','--python',str(p),'--',str(art(w)/'v3'/version),str(sp),str(tp),('q' if version=='hero' else 'east,q,rear,front')],check=True,stdout=subprocess.DEVNULL)

def render_source(w,neutral=False):
 # Evaluate original mesh again in a fresh owned background Blender; never save.
 prefix=(MAIN/'scripts/art/w325/extract_projection_cache.py').read_text().split('meshes = ')[0]
 src=prefix+'''
deps=bpy.context.evaluated_depsgraph_get(); keep=[]
for ob in list(bpy.data.objects):
 if ob.type!='MESH' or ob.name.lower().startswith('plane') or not ob.visible_get() or ob.hide_render:continue
 if any(any(t in m.name.lower() for t in ['reticle','fx','glass','lens']) for m in ob.data.materials if m):continue
 eo=ob.evaluated_get(deps);me=bpy.data.meshes.new_from_object(eo);me.transform(eo.matrix_world)
 no=bpy.data.objects.new('review_'+ob.name,me);sc.collection.objects.link(no);keep.append(no)
for ob in list(bpy.data.objects):
 if ob not in keep:bpy.data.objects.remove(ob,do_unlink=True)
xlong=WID in ('commemoration','circular_logic','iterative_loop')
for ob in keep:
 if xlong:
  for v in ob.data.vertices:v.co=(v.co.y,-v.co.x,v.co.z)
for m in bpy.data.materials:
 if not m.node_tree:continue
 nt=m.node_tree;outs=[n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'];groups=[n for n in nt.nodes if n.type=='GROUP' and n.node_tree and 'PlayerGear' in n.node_tree.name];tex=[n for n in nt.nodes if n.type=='TEX_IMAGE' and n.image and 'Diffuse' in n.image.name]
 bs=nt.nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.85;bs.inputs['Metallic'].default_value=0
 if groups:nt.links.new(groups[0].outputs['Bake_Color'],bs.inputs['Base Color'])
 elif tex:nt.links.new(tex[0].outputs['Color'],bs.inputs['Base Color'])
 else:bs.inputs['Base Color'].default_value=(.08,.09,.1,1)
 if not groups:
  original_bs=[n for n in nt.nodes if n.type=='BSDF_PRINCIPLED' and n!=bs]
  for oldbs in original_bs:
   if oldbs.inputs['Alpha'].links:nt.links.new(oldbs.inputs['Alpha'].links[0].from_socket,bs.inputs['Alpha']);break
 for o in outs:nt.links.new(bs.outputs[0],o.inputs['Surface'])
sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.cycles.max_bounces=3;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.render.film_transparent=False;sc.use_nodes=False
sc.world=bpy.data.worlds.new('review_neutral_world');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.47,.5,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.7
for ang,en in [((.9,.2,.5),2.2),((-.5,-.4,.3),.8),((2.6,.3,-2.5),.6)]:
 l=bpy.data.lights.new('review_sun','SUN');l.energy=en;o=bpy.data.objects.new('review_sun',l);sc.collection.objects.link(o);o.rotation_euler=ang
pts=[v.co.copy() for ob in keep for v in ob.data.vertices];lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)];c=mathutils.Vector([(lo[i]+hi[i])/2 for i in range(3)])
cam=bpy.data.cameras.new('review_camera');cam.type='ORTHO';co=bpy.data.objects.new('review_camera',cam);sc.collection.objects.link(co);sc.camera=co;sc.render.resolution_x=1200;sc.render.resolution_y=700
for name,direction in {'east':(-1,0,0),'q':(-.7,.45,-.45),'rear':(-.7,-.45,-.45),'front':(0,1,0)}.items():
 d=mathutils.Vector(direction).normalized();co.location=c-d*max(5,max(hi[i]-lo[i] for i in range(3))*3);co.rotation_euler=d.to_track_quat('-Z','Y').to_euler();M=co.rotation_euler.to_matrix().transposed();pp=[M@(v-c) for v in pts];rw=max(v.x for v in pp)-min(v.x for v in pp);rh=max(v.y for v in pp)-min(v.y for v in pp);cam.ortho_scale=max(rw,rh*1200/700)*1.12;sc.render.filepath=out+'/source_'+name+'.png';bpy.ops.render.render(write_still=True)
'''
 if neutral:
  src=src.replace("if groups:nt.links.new(groups[0].outputs['Bake_Color'],bs.inputs['Base Color'])", "if groups:bs.inputs['Base Color'].default_value=(.45,.45,.45,1)").replace("elif tex:nt.links.new(tex[0].outputs['Color'],bs.inputs['Base Color'])", "elif tex:bs.inputs['Base Color'].default_value=(.45,.45,.45,1)").replace("else:bs.inputs['Base Color'].default_value=(.08,.09,.1,1)","else:bs.inputs['Base Color'].default_value=(.45,.45,.45,1)").replace("out+'/source_'", "out+'/source_neutral_'")
 p=art(w)/'v3'/('render-source-neutral.py' if neutral else 'render-source.py');p.write_text('WID='+repr(w)+'\n'+src);ev=json.loads((art(w)/'source-evaluation.json').read_text())
 subprocess.run([kit().BLENDER,'-b',ev['source'],'--disable-autoexec','--python',str(p),'--',str(art(w)/'v3'),'420'],check=True,stdout=subprocess.DEVNULL)

def benchmark(w='trustee'):
 d=json.loads((MAIN/'src/main/resources/assets/destiny/models/weapon_surface_w123/blast_furnace.json').read_text());p=art(w)/'v3/benchmark_skin.json';p.write_text(json.dumps(dict(texture_size=[1024,1024],parts=dict(body=d['elements']))))
 script=art(w)/'v3/render-review.py'
 subprocess.run([kit().BLENDER,'-b','--factory-startup','--disable-autoexec','--python',str(script),'--',str(art(w)/'v3/benchmark'),str(p),str(MAIN/'src/main/resources/assets/destiny/textures/item/weapon/w123/blast_furnace.png'),'east,q,rear,front'],check=True,stdout=subprocess.DEVNULL)

def validate(w):
 k=kit();d=json.loads(skin(w).read_text());es=[e for p in d['parts'].values() for e in p];assert len(es)<1000 and len({e['name'] for e in es})==len(es)
 for e in es:
  assert all(-16<=e['from'][i]<=e['to'][i]<=32 for i in range(3)),e['name']
  assert sum(e['to'][i]>e['from'][i] for i in range(3))>=2,e['name']
  assert e['faces'] and set(e['faces']).issubset(k.FACE_AXES)
  for f in e['faces'].values():assert all(0<=v<=16 for v in f['uv']) and f['texture']=='#0'
 im=Image.open(atlas(w));assert list(im.size)==d['texture_size'];assert max(im.size)<=1024
 bad=coplanar(es,k);assert not bad,bad
 # Conservative world AABB adjacency catches floating parts; it does not claim
 # exact swept collision/contact against the client's hand animation.
 bounds=[]
 for e in es:
  p=k._corners(e);bounds.append(([min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]))
 unseen=set(range(len(es)));components=[]
 while unseen:
  comp={unseen.pop()};stack=list(comp)
  while stack:
   i=stack.pop();a,A=bounds[i]
   for j in list(unseen):
    b,B=bounds[j]
    if all(min(A[t],B[t])-max(a[t],b[t])>=-.045 for t in range(3)):unseen.remove(j);comp.add(j);stack.append(j)
  components.append([es[i]['name'] for i in sorted(comp)])
 spec=importlib.util.spec_from_file_location('g2_review',MAIN/'scripts/art/w327/group2.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);oldsetup=g.setup
 def setup():
  kk=oldsetup();kk.ROOT=ROOT;return kk
 g.setup=setup;g.art=art;g.adscheck(w)
 ev=json.loads((art(w)/'source-evaluation.json').read_text());assert sha(ev['source'])==ev['sha256']
 authored=json.loads((art(w)/'design.json').read_text())['elements'];groups={};maxerr=0.;tri_count=0
 for e in authored:
  if '_surface' not in e:continue
  tri_count+=1;part=e['_surface'];lo,hi=e['from'],e['to'];r=e['rotation'];pts=[]
  for u,v in part['mask']:
   local=[lo[0]+u*(hi[0]-lo[0]),hi[1]-v*(hi[1]-lo[1]),lo[2]];off=[local[i]-r['origin'][i] for i in range(3)];rv=k.rotate_vec(off,k.rot_of(e));pts.append([rv[i]+r['origin'][i] for i in range(3)])
  maxerr=max(maxerr,max(min(math.dist(a,b) for b in part['vertices']) for a in pts));group=e['name'].rsplit('/',1)[0];edges=groups.setdefault(group,{})
  vs=[tuple(round(q,8) for q in p) for p in part['vertices']]
  for a,b in zip(vs,vs[1:]+vs[:1]):key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
 assert maxerr<1e-7,maxerr
 assert all(v==2 for edges in groups.values() for v in edges.values()),'Loft has open geometric edge'
 triangle_report=dict(elements=tri_count,closed_lofts={n:len(edges) for n,edges in groups.items()},edge_incidence='Every authored closed loft edge has exactly two adjacent authored polygons',max_native_vertex_error=maxerr,alpha_mask='General convex polygon island, 32 texels/model-pixel; conservative 1 texel edge dilation; north mirrored',offline_renderer='One double-sided face rendered per zero-depth element to avoid duplicate coplanar Blender faces; runtime preserves both oppositely oriented faces',native_acceptance='MASTER_PENDING')
 (art(w)/'v3/loft-validation.json').write_text(json.dumps(triangle_report,indent=1)+'\n')
 report=dict(id=w,revision=3,parse='PASS',positive_bounds='PASS',normalized_uv='PASS',parts={p:len(e) for p,e in d['parts'].items()},assembled_elements=len(es),atlas=list(im.size),cuboid_coplanar_same_facing_world_polygon_overlaps=len(bad),authored_lofts=triangle_report,connections=dict(method='World AABB graph, 0.045px tolerance; conservative offline broadphase only',components=len(components),small_components=[c for c in components if len(c)<100]),source_original_sha256=ev['sha256'],source_original_unchanged=True,original_blend_reopened_for_v3_aligned_review=True,native_pack_load='MASTER_PENDING',native_hand_ads_reload='MASTER_PENDING',native_10_20_display='MASTER_PENDING',output_sha256={str(p.relative_to(ROOT)):sha(p) for p in [skin(w),atlas(w),hud(w)]})
 (art(w)/'validation.json').write_text(json.dumps(report,indent=1)+'\n');(art(w)/'surface-joins.json').write_text(json.dumps(dict(method='World-space rotation-aware convex face overlap',unresolved=bad,adjustments=json.loads((art(w)/'v3/join-adjustments.json').read_text())),indent=1)+'\n');print(w,'validated',len(es),'components',len(components),[c for c in components if len(c)<6],flush=True)
def snapshot(w,revision='source-form-r5'):
 import shutil
 root=art(w)/'v3';out=root/revision;out.mkdir(exist_ok=False)
 board=Image.new('RGB',(2400,1460),(8,10,12));draw=ImageDraw.Draw(board)
 for row,v in enumerate(['east','q']):
  for col,prefix in enumerate(['source_neutral','neutral']):
   im=Image.open(root/(prefix+'_'+v+'.png'));board.paste(im,(col*1200,row*730+30));draw.text((col*1200+14,row*730+9),('ORIGINAL evaluated .blend' if col==0 else revision+' native geometry / closed polygon lofts')+' / '+v,fill='white')
 board.save(out/'board.png')
 for prefix in ['source_neutral','neutral']:
  for v in ['east','q','rear','front']:shutil.copy2(root/(prefix+'_'+v+'.png'),out/(prefix+'_'+v+'.png'))
 for src,name in [(skin(w),'skin.json'),(atlas(w),'atlas.png'),(art(w)/'design.json','design.json'),(art(w)/'validation.json','validation.json'),(root/'loft-validation.json','loft-validation.json')]:shutil.copy2(src,out/name)
 (out/'hashes.json').write_text(json.dumps({p.name:sha(p) for p in out.iterdir() if p.is_file()},indent=1)+'\n')
 print(out/'board.png',flush=True)

if __name__=='__main__':
 cmd=sys.argv[1]
 for w in sys.argv[2:] or IDS:
  if cmd=='build':build(w)
  elif cmd=='optimize':optimize(w)
  elif cmd=='render':render(w)
  elif cmd=='hero':render(w,'hero')
  elif cmd=='render-v2':render(w,'v2')
  elif cmd=='source':render_source(w)
  elif cmd=='neutral-source':render_source(w,True)
  elif cmd=='neutral':render(w,'neutral')
  elif cmd=='benchmark':benchmark(w)
  elif cmd=='validate':validate(w)
  elif cmd=='snapshot':snapshot(w)
