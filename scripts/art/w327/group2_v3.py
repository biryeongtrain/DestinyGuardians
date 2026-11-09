#!/usr/bin/env python3
"""Exclusive V3 source-calibrated reconstruction for five group-B weapons. No other IDs."""
from pathlib import Path
import json,math,sys,importlib.util,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[3]
IDS=['deliverance','forbearance','apex_predator','palmyra_b','cataclysmic']
SPEC={'deliverance':(.033,-9.83,15.6),'forbearance':(.0325,-9.625,17.2),'cataclysmic':(.0234,-10.234,14.1),'apex_predator':(.0234,-5.734,14.0),'palmyra_b':(.0244,.403,14.009)}
VOW={k:dict(color=c,kind=t) for k,c,t in [('shell',[86,83,77],'metal'),('edge',[105,101,93],'steel'),('steel',[137,136,124],'steel'),('black',[24,25,25],'metal'),('accent',[186,61,32],'ceramic'),('rubber',[49,48,45],'rubber'),('purple',[103,78,111],'paint'),('ivory',[194,191,172],'ceramic')]}
APEX={k:dict(color=c,kind=t) for k,c,t in [('shell',[201,193,161],'bone'),('edge',[222,212,176],'bone'),('steel',[116,132,143],'steel'),('black',[20,26,37],'metal'),('accent',[34,46,75],'paint'),('rubber',[34,41,56],'rubber'),('gold',[173,142,75],'gold'),('ivory',[218,209,179],'bone')]}
PAL={k:dict(color=c,kind=t) for k,c,t in [('shell',[195,198,166],'paint'),('edge',[220,223,195],'paint'),('steel',[143,155,151],'steel'),('black',[39,44,43],'metal'),('accent',[214,76,19],'paint'),('rubber',[61,55,44],'rubber'),('ivory',[224,224,202],'paint'),('glass',[64,109,119],'glass')]}
class Design:
 def __init__(self,w):
  self.w=w;self.E=[];self.C=[];self.q,self.z0,self.y0=SPEC[w];self.M=APEX if w=='apex_predator' else PAL if w=='palmyra_b' else VOW
  self.man=json.loads((Path('/tmp/destiny-perks-20261106/group2-cache')/w/'manifest.json').read_text());self.px=self.man['views']['px'];self.sx=self.q*1000
 def p(self,u,v,x=8):return [x,self.y0-v*self.q,self.z0+u*self.q]
 def add(self,n,a,b,role,r=None):
  e={'name':n,'from':[round(v,6) for v in a],'to':[round(v,6) for v in b],'role':role}
  if r:e['rotation']=r
  self.E.append(e)
 def rect(self,n,u,v,U,V,width,role,xc=8):self.add(n,self.p(u,V,xc-width/2),self.p(U,v,xc+width/2),role)
 def beam(self,n,a,b,t,width,role,xc=8):
  p=self.p(*a,xc[0] if isinstance(xc,tuple) else xc);q=self.p(*b,xc[1] if isinstance(xc,tuple) else xc);c=[(p[i]+q[i])/2 for i in range(3)];L=math.dist(p,q);ang=math.degrees(math.asin(-(q[1]-p[1])/L));yaw=math.degrees(math.atan2(q[0]-p[0],q[2]-p[2]));tt=t*self.q
  self.add(n,[c[0]-width/2,c[1]-tt/2,c[2]-L/2],[c[0]+width/2,c[1]+tt/2,c[2]+L/2],role,dict(origin=c,x=ang,y=yaw,z=0))
 def ring(self,n,u,v,r,depth,wall,role,N=8,xc=8):
  c=self.p(u,v,xc);rr=r*self.q;tt=wall*self.q;L=2*(rr-tt/2)*math.tan(math.pi/N)
  for j in range(N):
   a=j*2*math.pi/N;xs=.55 if self.w=='deliverance' else 1;cc=[xc+(rr-tt/2)*math.sin(a)*xs,c[1]+(rr-tt/2)*math.cos(a),c[2]];ll=2*(rr-tt/2)*math.sqrt((xs*math.cos(a))**2+math.sin(a)**2)*math.tan(math.pi/N);angle=math.degrees(math.atan2(-math.sin(a),xs*math.cos(a)))
   self.add(n+f'/{j}',[cc[0]-ll/2,cc[1]-tt/2,cc[2]-depth*self.q/2],[cc[0]+ll/2,cc[1]+tt/2,cc[2]+depth*self.q/2],role,dict(origin=cc,x=0,y=0,z=angle))
 def tube(self,n,u,U,v,r,role):
  c=self.p((u+U)/2,v);rr=r*self.q;aa=rr*(math.sqrt(2)-1)
  for j in range(4):self.add(n+f'/{j}',[8-aa,c[1]-rr,self.p(u,v)[2]],[8+aa,c[1]+rr,self.p(U,v)[2]],role,dict(origin=c,x=0,y=0,z=j*45))
 def pin(self,n,u,v,r,depth,role,xc):
  c=self.p(u,v,xc);rr=r*self.q;aa=rr*(math.sqrt(2)-1)
  for j in range(4):self.add(n+f'/{j}',[xc-depth/2,c[1]-aa,c[2]-rr],[xc+depth/2,c[1]+aa,c[2]+rr],role,dict(origin=c,x=j*45,y=0,z=0))
 def roundpanel(self,n,u,v,r,width,role,xc=8,quarter=False,ry=None):
  # Adjacent solid bands approximate one intentional curved end plate; no floating overlays.
  N=10;ry=ry or r
  for j in range(N):
   y0=v-ry+j*ry/N;y1=v-ry+(j+1)*ry/N;yy=(y0+y1)/2;reach=r*math.sqrt(max(0,1-((yy-v)/ry)**2))
   self.rect(n+f'/{j}',u-reach,y0,u,y1,width,role,xc)
 def write(self):
  a=ROOT/'art/weapons/w327'/self.w;doc=dict(revision=3,materials=self.M,elements=self.E,contours=self.C,source_mapping=dict(q=self.q,z0=self.z0,y0=self.y0,sx=self.sx,centre=self.px['centre'],res=self.px['res'],ppm=self.man['ppm'],note='Calibrated source side coordinates; uniform source scale, Palmyra anchored at actual pistol-grip contact'))
  (a/'design.json').write_text(json.dumps(doc,indent=1)+'\n')
  (a/'design.py').write_text("""from pathlib import Path
import json
D=json.loads(Path(__file__).with_name('design.json').read_text())
REVISION=3
STYLE='material'
T=20
ATLAS=1024
NO_OVERLAY=False
MATERIALS=D['materials']
def elements():return D['elements']
def model2world(name,p):
 m=D['source_mapping'];u=(p[2]-m['z0'])/m['q'];v=(m['y0']-p[1])/m['q'];return ((p[0]-8)/m['sx'],m['centre'][1]+(u-m['res'][0]/2)/m['ppm'],m['centre'][2]+(m['res'][1]/2-v)/m['ppm'])
def is_magazine(name):return name.startswith('mag_')
def special(e,fn,s,t):return None
def material(name,fn):return next(e['role'] for e in D['elements'] if e['name']==name)
""")
  print(self.w,len(self.E),'cuboids',len(self.C),'closed contour solids')

def contour(d,n,outline,width,role,xc=8):
 d.C.append(dict(name=n,vertices=[d.p(u,v,xc-width/2) for u,v in outline],extrude=[width,0,0],role=role))
def cross_prism(d,n,profile,u,U,role,angle=0,center_v=None):
 # profile is authored source cross-section (lateral model offset, side-view image v).
 a=math.radians(angle);c=d.p(u,center_v if center_v is not None else (121 if d.w=='deliverance' else 132));points=[]
 for x,v in profile:
  y=d.p(u,v)[1]-c[1];points.append([8+x*math.cos(a)-y*math.sin(a),c[1]+x*math.sin(a)+y*math.cos(a),c[2]])
 d.C.append(dict(name=n,vertices=points,extrude=[0,0,(U-u)*d.q],role=role))

def deliverance(d):
 r=d.rect;b=d.beam;ring=d.ring;pin=d.pin
 # Layered muzzle and fluted front chamber with a sloping cast lower cheek.
 ring('muzzle/cast_outer',22,121,44,25,10,'shell');ring('muzzle/steel_lip',10,121,35,8,5,'steel');ring('muzzle/deep_bore',28,121,31,30,5,'black');r('muzzle/barrel_socket',33,92,57,151,1.50,'black')
 r('chamber/central',51,91,292,173,1.62,'shell');b('chamber/lower_slope',(54,168),(291,203),18,1.39,'shell')
 r('chamber/dark_flute_bed',53,73,293,123,1.54,'black')
 for j in range(23):
  u=53+j*10.4;top=70-6*math.sin(j*.45);r(f'chamber/flute{j}',u,top,u+7.6,123,1.73,'shell')
 # Raised crown with large circular recessed relief; the orange quarter-disc is actual volume.
 r('junction/crown_core',297,22,415,72,1.68,'shell');r('junction/crown_edge',292,17,416,23,1.77,'edge')
 for side in [-1,1]:
  x=8+side*.87;pin(f'crown{side}/disc',356,27,34,.08,'shell',x);r(f'crown{side}/cutline',295,68,414,72,.10,'black',x)
 d.roundpanel('junction/orange_quadrant',416,122,121,1.84,'accent',ry=50)
 r('junction/rear_spigot',415,27,445,69,1.08,'black')
 for i in range(5):r(f'junction/spigot_ring{i}',418+i*5,28,420+i*5,68,1.22,'steel')
 r('front_handle/upper_socket',294,123,417,188,1.57,'shell');r('front_handle/main_block',323,185,413,274,1.53,'shell')
 b('front_handle/outer_curve',(306,181),(324,279),25,1.55,'shell');b('front_handle/heel_curve',(326,273),(354,322),35,1.44,'shell')
 r('front_handle/face_recess',327,214,363,239,1.63,'black');r('front_handle/face_insert',333,215,357,237,1.68,'edge')
 # Source's compact open shoulder frame, return curve and diagonal inner handhold.
 r('frame/top_beam',416,104,751,143,1.18,'shell');r('frame/lower_rail',416,151,735,173,1.00,'shell')
 r('frame/recessed_long_channel',424,141,736,155,.86,'black')
 for s in [-1,1]:
  x=8+s*.63
  for i in range(10):r(f'frame{s}/square_socket{i}',499+i*20,108,514+i*20,119,.08,'black',x);pin(f'frame{s}/socket_pin{i}',506+i*20,114,4,.11,'steel',x)
 b('frame/inner_grip',(508,180),(565,269),43,1.10,'shell');b('frame/grip_edge',(531,177),(585,267),7,1.15,'edge')
 r('frame/rear_vertical',672,165,730,265,1.22,'shell');b('frame/rear_inward_curve',(671,175),(652,228),31,1.17,'shell');b('frame/rear_return',(651,226),(612,276),30,1.16,'shell')
 b('frame/lower_return',(608,278),(553,311),34,1.10,'shell');b('frame/lower_belly',(549,311),(397,316),33,1.12,'shell');b('frame/lower_front',(397,311),(351,285),33,1.20,'shell')
 r('frame/lower_dark_socket',435,276,560,301,.94,'black');r('frame/lower_sliding_rod',474,283,552,290,1.02,'steel')
 for s in [-1,1]:
  x=8+s*.59;r(f'frame{s}/rear_panel',671,170,729,262,.10,'shell',x);r(f'frame{s}/lower_mechanism',514,280,558,299,.10,'black',x)
 b('trigger/guard_top',(428,214),(484,214),4,.20,'ivory');b('trigger/guard_front',(428,215),(437,170),4,.20,'ivory');b('trigger/curve1',(487,208),(465,236),4,.20,'ivory');b('trigger/curve2',(465,236),(453,282),4,.20,'ivory');b('trigger/hook',(482,169),(470,209),5,.23,'steel')
 # Butt wire is a purposeful broad curve, attached at both ends.
 b('butt/wire_top',(788,104),(759,138),8,.18,'ivory');b('butt/wire_bend',(759,138),(744,179),8,.18,'ivory');b('butt/wire_leg',(744,179),(744,324),8,.18,'ivory');r('butt/wire_mount',727,175,748,190,.75,'steel')
 r('mag_cell/main',325,333,456,359,1.27,'shell');r('mag_cell/heel',326,358,455,367,1.39,'edge');r('mag_cell/socket',326,318,451,334,1.22,'shell')
 for s in [-1,1]:pin(f'mag_cell{ s}/pin',358,344,5,.18,'steel',8+s*.68)

def forbearance(d):
 r=d.rect;b=d.beam;ring=d.ring;pin=d.pin
 # Moving barrel remains a distinct inherited break-action assembly.
 d.tube('mag_barrel/core',12,415,132,24,'black');ring('mag_barrel/muzzle_shell',25,132,28,30,7,'shell');ring('mag_barrel/muzzle_lip',11,132,22,7,3,'steel');ring('mag_barrel/bore',26,132,19,24,3,'black');r('mag_barrel/front_top',11,90,187,109,1.61,'shell');r('mag_barrel/front_bottom',11,155,187,172,1.61,'shell');r('mag_barrel/side_core',50,107,187,155,1.56,'black')
 for i in range(11):
  u=69+i*10;r(f'mag_barrel/top_flute{i}',u,85+(i%3)*2,u+7,103,1.81,'shell')
 r('mag_barrel/lower_shoe',68,155,190,172,1.24,'steel');r('mag_barrel/forward_bedding',185,92,414,171,1.73,'black')
 d.roundpanel('breech/orange_quadrant',414,174,98,1.90,'accent',ry=80);r('breech/break_hinge',316,174,412,211,1.60,'shell')
 for s in [-1,1]:
  x=8+s*.83
  for j in range(3):b(f'breech{s}/recess_lip{j}',(326+j*6,207-j*6),(397-j*4,207-j*6),5,.10,'black',x)
 r('receiver/upper_rail',416,92,598,127,1.38,'shell');r('receiver/lower_core',426,133,598,160,1.56,'shell');r('receiver/recess',423,127,592,136,1.18,'black')
 for i in range(5):r(f'receiver/vertical_lock{i}',538+i*12,85,545+i*12,121,1.46,'edge');r(f'receiver/lock_inset{i}',539+i*12,111,545+i*12,120,1.58,'black')
 # Distinct rear shoulder plate and its underside cutout, not a plain stock stick.
 r('stock/top_shell',598,94,775,130,1.50,'shell');r('stock/lower_cheek',641,130,742,169,1.44,'shell');b('stock/front_swept_face',(603,103),(635,162),22,1.62,'shell');b('stock/heel_sweep',(757,128),(742,168),19,1.35,'shell')
 for s in [-1,1]:r(f'stock{s}/circuit_face',645,99,773,146,.08,'shell',8+s*.79);pin(f'stock{s}/rear_socket',750,113,10,.13,'black',8+s*.82);pin(f'stock{s}/rear_pin',750,113,5,.16,'steel',8+s*.84)
 b('stock/wire_front',(648,164),(672,210),6,.18,'ivory');b('stock/wire_floor',(671,210),(756,210),6,.18,'ivory');b('stock/wire_heel',(756,210),(772,194),6,.18,'ivory');b('stock/wire_rear',(772,194),(774,127),6,.18,'ivory')
 # Source's raked rear grip and sculpted purple inset.
 r('grip/root_socket',465,155,519,187,1.15,'shell');b('grip/main',(484,182),(545,288),48,1.20,'shell');b('grip/backstrap',(511,180),(570,287),12,1.25,'edge');b('grip/heel',(530,302),(572,280),10,1.28,'shell')
 for s in [-1,1]:b(f'grip{s}/purple_inlay',(490,223),(532,283),22,.10,'purple',8+s*.66)
 r('foregrip/socket',187,170,219,188,1.17,'black');r('foregrip/core',188,181,217,263,1.04,'shell')
 for s in [-1,1]:b(f'foregrip{s}/purple_inlay',(207,196),(209,247),18,.09,'purple',8+s*.56)
 b('guard/front',(431,177),(415,228),4,.22,'ivory');b('guard/floor',(414,228),(486,228),4,.22,'ivory');r('guard/rear_join',471,204,478,229,.22,'ivory');r('trigger/root_socket',453,156,463,183,.26,'steel');b('trigger',(458,178),(455,211),5,.26,'steel')
 # Original fine sight wire cross and spine, attached via two feet.
 b('sight/wire_top',(232,76),(393,76),4,.17,'ivory');b('sight/front_staff',(232,76),(237,17),5,.18,'ivory');b('sight/rear_staff',(391,87),(393,62),4,.17,'ivory');r('sight/front_foot',225,77,238,94,.34,'steel');r('sight/rear_foot',369,77,381,94,.34,'steel');b('sight/diagonal',(261,88),(277,76),4,.17,'ivory')


def cataclysmic(d):
 r=d.rect;b=d.beam;ring=d.ring;pin=d.pin
 # Two separated electromagnetic beams and narrow open channel.
 r('fork/top_body',10,65,386,111,1.76,'shell');r('fork/lower_body',10,146,445,190,1.72,'shell');r('fork/front_bridge',15,112,43,148,.70,'accent')
 r('fork/top_inset',125,53,386,101,1.52,'black')
 for j in range(24):r(f'fork/flute{j}',131+j*10.4,54+(j%3)*3,138+j*10.4,104,1.73,'shell')
 b('fork/under_swept_keel',(17,185),(43,252),15,1.28,'shell');b('fork/lower_root',(376,183),(439,247),17,1.55,'shell')
 r('fork/rear_socket',386,89,446,124,1.67,'shell');b('fork/top_sloping_bridge',(385,78),(585,55),21,1.47,'shell')
 b('fork/channel_wire',(29,119),(368,138),4,.15,'ivory');b('fork/channel_return',(134,134),(379,134),4,.15,'ivory')
 # Large vertical cell stack with square seats, recessed mechanics and source rune blocks.
 r('cells/dark_bed',449,110,605,184,1.15,'black')
 for i in range(8):
  u=453+i*19;c=d.p(u+6.5,147);rad=6.5*d.q
  for j in range(4):d.add(f'cells/vertical_rod{i}/{j}',[8-rad*.414,d.p(u,181)[1],c[2]-rad],[8+rad*.414,d.p(u,112)[1],c[2]+rad],'black',dict(origin=c,x=0,y=j*45,z=0))
 r('cells/top_clamp',457,96,598,118,1.67,'shell')
 for i in range(3):r(f'cells/top_clamp_split{i}',471+i*40,96,496+i*40,118,1.72,'edge')
 for s in [-1,1]:
  x=8+s*.87
  for i in range(5):r(f'cells{s}/rune_block{i}',576+i*32,154,600+i*32,178,.30,'shell',x)
 r('receiver/spine',601,91,1060,149,1.62,'shell');r('receiver/rear_cheek',810,149,1017,190,1.70,'shell')

 for j in range(12):
  u=622+j*125/12;U=622+(j+1)*125/12;v=88+32*math.sqrt(max(0,1-(((u+U)/2-684.5)/62.5)**2));r(f'receiver/orange_cap{j}',u,88,U,v,1.78,'accent')
 b('receiver/sight_hump',(587,62),(621,92),22,1.50,'shell')
 # Orange forward loop surrounds the inner mechanism; it is a thick arch with a true void.
 b('frame/orange_upper',(450,160),(482,198),23,1.62,'accent');b('frame/orange_front',(481,196),(492,258),25,1.61,'accent');b('frame/orange_lower',(492,257),(472,344),24,1.58,'accent')
 b('frame/front_dark_inset',(467,206),(475,324),28,1.70,'shell');r('frame/lower_bed',481,303,786,344,1.37,'shell')
 b('frame/rear_curve',(785,176),(773,262),30,1.50,'shell');b('frame/rear_return',(773,260),(749,321),28,1.43,'shell')
 r('frame/lower_recess',495,305,670,326,1.49,'black');r('frame/lower_rod',503,312,659,317,1.56,'steel')
 for i in range(3):r(f'frame/lower_slider{i}',603+i*22,307,614+i*22,325,1.58,'shell')
 b('grip/diagonal_core',(668,190),(722,285),52,1.20,'shell');b('grip/rear_bevel',(696,185),(749,287),9,1.27,'edge');b('grip/heel',(694,296),(751,287),12,1.30,'shell')
 # Fine white internal trigger bow, following actual characteristic hook.
 b('guard/top',(583,214),(640,214),4,.22,'ivory');b('guard/curve',(640,214),(675,248),4,.22,'ivory');b('guard/rear',(675,248),(696,302),4,.22,'ivory');b('trigger/front',(582,185),(586,207),5,.22,'ivory');b('trigger/curl',(586,207),(608,214),5,.22,'ivory');b('trigger/rear',(608,214),(631,198),5,.22,'ivory');r('trigger/socket',629,180,635,200,.22,'ivory')
 # Rear stock stepped cutout and large outer ivory wire.
 for j in range(3):r(f'stock/lower_step{j}',816+j*13,211+j*15,1008-j*13,225+j*15,1.25-j*.1,'shell')
 r('stock/rear_leg',982,184,1009,294,1.18,'shell');b('stock/front_leg',(821,213),(809,286),16,1.21,'shell')
 b('stock/wire_rear',(1052,115),(1048,285),6,.18,'ivory');b('stock/wire_curve1',(1048,283),(1032,320),6,.18,'ivory');b('stock/wire_curve2',(1032,320),(1003,341),6,.18,'ivory');b('stock/wire_floor',(1003,341),(824,343),6,.18,'ivory');r('stock/wire_mount',808,315,829,350,.53,'shell')
 # Lower magazine is the shallow crescent beneath the frame, not a tall generic box.
 r('mag_cell/socket',486,340,665,360,1.22,'shell');b('mag_cell/front_bevel',(484,351),(535,378),17,1.14,'shell');b('mag_cell/rear_bevel',(662,351),(620,378),17,1.14,'shell');r('mag_cell/belly',532,367,620,387,1.12,'shell')
 for s in [-1,1]:r(f'mag_cell{s}/latch',565,352,594,384,.10,'black',8+s*.62);r(f'mag_cell{s}/latch_insert',576,357,583,380,.13,'steel',8+s*.65)
 b('sight/staff',(592,88),(592,40),4,.18,'ivory');b('sight/cross',(554,45),(613,45),4,.18,'ivory');b('sight/rear_branch',(620,86),(643,64),4,.18,'ivory');b('sight/top',(592,64),(687,64),4,.18,'ivory')

def apex_predator(d):
 r=d.rect;b=d.beam;ring=d.ring;pin=d.pin
 # Exposed deep-blue launcher tube with separate front bore and exhaust; supplied tube shader is corrupt.
 d.tube('tube/navy_front',15,518,75,38,'accent');d.tube('tube/navy_rear',519,1150,75,38,'accent')
 ring('muzzle/steel_outer',24,75,40,25,8,'steel');ring('muzzle/recess',13,75,32,8,5,'black');ring('muzzle/bore_lip',12,75,27,6,3,'steel')
 ring('exhaust/steel_shell',1145,75,40,25,7,'steel');ring('exhaust/dark_recess',1155,75,33,8,5,'black');ring('exhaust/inner_wall',1142,75,29,22,4,'black')
 ring('tube/gold_collar',742,75,43,17,6,'gold')
 # Bone shell is a swept organic armature with deliberate large windows.
 b('bone/front_tip',(22,124),(111,101),12,.58,'edge')
 b('bone/front_lower',(101,110),(202,105),39,1.13,'shell')
 b('bone/front_cheek',(197,103),(300,108),61,1.47,'shell')
 b('bone/front_arch',(105,91),(167,51),25,1.13,'shell')
 b('bone/arch_shoulder',(161,54),(228,34),30,1.43,'shell')
 b('bone/arch_crest',(223,32),(330,24),20,1.37,'shell')
 b('bone/top_spine',(329,24),(454,17),14,1.05,'edge')
 b('bone/spine_tip',(453,17),(552,13),6,.55,'edge')
 b('bone/window_lower_rim',(301,79),(414,79),13,1.18,'edge')
 b('bone/receiver_lower',(296,117),(423,117),45,1.49,'shell')
 b('bone/receiver_cheek',(423,113),(507,110),65,1.65,'shell')
 b('bone/rear_chamber',(503,111),(571,123),66,1.63,'shell')
 b('bone/chamber_rear',(569,124),(610,139),42,1.40,'shell')
 # Triangular rear window cage is continuous from crest to shoulder frame.
 b('bone/rear_top_sweep',(508,42),(594,44),13,1.18,'edge')
 b('bone/rear_top_drop',(590,44),(651,67),16,1.10,'shell')
 b('bone/rear_nose',(649,67),(712,97),17,.86,'shell')
 b('bone/rear_window_lower',(607,138),(710,106),16,1.02,'shell')
 b('bone/rear_window_strut',(588,73),(672,112),11,.96,'edge')
 b('bone/rear_inner_rib',(595,64),(674,88),7,1.00,'edge')
 # Source grip frame is a broad continuous palm opening with carved bone, not added generic grips.
 b('grip/front_shoulder',(322,141),(352,177),22,1.15,'shell')
 b('grip/front_rake',(352,174),(372,244),23,1.06,'shell')
 b('grip/front_curve',(372,241),(394,285),25,1.13,'shell')
 b('grip/front_heel',(391,284),(427,306),22,1.18,'shell')
 b('grip/floor',(423,306),(544,290),18,1.08,'edge')
 b('grip/rear_floor',(543,290),(620,276),20,1.13,'shell')
 b('grip/rear_heel',(619,278),(663,254),29,1.24,'shell')
 b('grip/rear_palm',(651,254),(622,203),40,1.29,'shell')
 b('grip/rear_root',(620,205),(600,157),32,1.28,'shell')
 b('grip/heel_point',(650,266),(701,241),10,.74,'edge')
 # Navy lower edging and open heel loop are source motifs with actual depth.
 b('grip/navy_front_edge',(327,149),(361,250),9,.99,'accent')
 b('grip/navy_curve',(361,248),(398,307),10,1.02,'accent')
 b('grip/navy_floor',(399,314),(528,297),10,.99,'accent')
 b('grip/navy_heel1',(526,298),(584,321),10,.84,'accent')
 b('grip/navy_heel2',(584,321),(615,287),10,.84,'accent')
 b('trigger/gold_root',(569,145),(577,187),5,.20,'gold');b('trigger/gold_hook',(577,187),(569,205),5,.20,'gold');b('trigger/second',(559,144),(563,186),4,.18,'gold')
 # Offset source sight tower, face plate and small pin details.
 r('sight/tower',499,46,551,96,.72,'black',8.74);r('sight/ivory_face',502,51,533,93,.10,'shell',9.14);r('sight/lower_tab',498,94,555,103,.78,'black',8.75)
 for side in [-1,1]:
  x=8+side*.86;pin(f'receiver{side}/shoulder_seal',571,127,12,.10,'shell',x)
  b(f'receiver{side}/carved_lip',(307,136),(354,151),5,.10,'edge',8+side*.76)
 # Inherited removable rocket remains axial; source itself is static.
 d.tube('mag_rocket/body',774,959,75,18,'black');d.tube('mag_rocket/collar',770,792,75,22,'gold');d.tube('mag_rocket/tip',959,986,75,13,'steel')

def palmyra_b(d):
 r=d.rect;b=d.beam;ring=d.ring;pin=d.pin
 # True source-to-canonical transform is anchored on the pistol grip, so rear tube extends farther than donor.
 # Main barrel is a continuous round shell, including its genuinely recessed open bore.
 ring('tube/front_cylinder',202,102,35,372,2,'shell',16)
 for j,u in enumerate([19,122,343,376]):ring(f'hoop{j}/round_clamp',u,102,40,12,5,'steel',16)
 ring('muzzle/outer_lip',12,102,39,10,4,'steel',16)
 ring('muzzle/inner_step',21,102,37,12,3,'shell',16)
 ring('muzzle/recessed_bore',48,102,35,52,2,'black',16)
 # Receiver broad plates around a genuine recessed sliding bolt window.
 ring('receiver/round_core',535.5,102,37,291,3,'shell',16)
 for s in [-1,1]:
  x=8+s*.88
  r(f'receiver{s}/window_shadow',506,82,619,121,.10,'black',x)
  r(f'receiver{s}/window_slider',517,88,608,114,.12,'steel',x+s*.04)
  r(f'receiver{s}/window_top_lip',503,79,622,84,.10,'edge',x+s*.05)
  r(f'receiver{s}/window_sill',503,120,622,125,.10,'edge',x+s*.05)
  r(f'receiver{s}/window_front_jamb',502,83,507,122,.10,'edge',x+s*.05)
  r(f'receiver{s}/window_rear_jamb',618,83,624,122,.10,'edge',x+s*.05)
 # Source offset cylindrical sight housing (one side only), including its deep round opening.
 ring('aux_sight/tube',410,103,22,106,4,'black',12,9.59)
 ring('aux_sight/front_bezel',356,103,24,9,5,'black',12,9.59)
 ring('aux_sight/inner_lens',361,103,17,4,2,'glass',12,9.59)
 r('aux_sight/rear_housing',447,85,499,122,.85,'black',9.59)
 r('aux_sight/inner_mount',404,88,423,116,.75,'black',8.98)
 r('aux_sight/top_shoe',398,77,425,84,.80,'steel',9.59)
 for v in [118,127]:ring(f'aux_sight/lower_socket{v}',356,v,6,7,2,'steel',8,9.77 if v==118 else 9.41)
 # Cylindrical rear shroud with real shallow hexagonal panel rims around its surface.
 ring('tail/orange_cylinder',903,101,35,398,2,'accent',16)
 ring('tail/front_clamp',692,101,40,20,5,'steel',16)
 r('tail/top_rail',708,62,1103,66,.55,'steel')
 ring('tail/rear_exhaust',1105,101,36,12,3,'steel',16)
 # Native cuboid hex-edge ribs, placed tangent to each upper/lower side of the shroud.
 for side in [-1,1]:
  for row,v in enumerate([85,119]):
   for j in range(5):
    u=746+j*61
    # Source has six-sided stamped panels, not a repeated painted substitute for recess depth.
    path=[(u-22,v-8),(u+18,v-8),(u+26,v),(u+18,v+8),(u-22,v+8),(u-29,v),(u-22,v-8)]
    xc=8+side*.775
    for h,(p0,p1) in enumerate(zip(path,path[1:])):
     xs=tuple(8+side*(math.sqrt(max(0,35**2-(p[1]-101)**2))*d.q+.012) for p in [p0,p1]);b(f'tail{side}/hex{row}_{j}_{h}',p0,p1,1.5,.055,'accent',xs)
 for s in [-1,1]:
  x=8+s*.89;r(f'tail{s}/warning_plate',783,110,831,141,.10,'steel',x);b(f'tail{s}/bracket',(625,142),(783,142),12,.13,'steel',x)
 # Lower receiver and real hand anchors, chamfered cheek and inset trigger housing.
 r('lower/receiver_upper',390,139,613,180,1.48,'black');r('lower/receiver_main',414,174,594,204,1.40,'black');b('lower/rear_bevel',(609,179),(589,204),16,1.38,'black');b('lower/front_bevel',(393,172),(429,196),14,1.39,'black')
 r('lower/steel_top',392,138,582,160,1.58,'steel');r('lower/bolt_slot',421,144,497,157,1.66,'black')
 for s in [-1,1]:
  x=8+s*.77
  for px,py in [(413,176),(444,187),(502,201),(561,201)]:pin(f'lower{s}/pin{px}',px,py,3,.08,'steel',x)
 # Actual source palm curves, filled by narrow contacting sections rather than large angled sticks.
 def curve_at(points,y):
  for (a,b),(c,e) in zip(points,points[1:]):
   if b<=y<=e:return a+(c-a)*(y-b)/(e-b)
  return points[0][0] if y<points[0][1] else points[-1][0]
 def handle(n,front,back,ymin,ymax,width):
  step=8
  for j,y in enumerate(range(ymin,ymax,step)):
   Y=min(y+step,ymax);mid=(y+Y)/2;u=curve_at(front,mid);U=curve_at(back,mid);ww=width
   if n=='foregrip':ww=width*(1-.14*min(1,max(0,(mid-160)/70))+.18*max(0,(mid-265)/24))
   r(f'{n}/palm_section{j}',u,y,U,Y,ww,'rubber')
  for label,path in [('front',front),('back',back)]:
   for j,(p0,p1) in enumerate(zip(path,path[1:])):b(f'{n}/{label}_contour{j}',p0,p1,4,width+.035,'rubber')
 handle('foregrip',[(342,145),(326,169),(313,193),(307,219),(307,264),(298,289)],[(387,145),(375,166),(353,181),(340,204),(339,263),(330,289)],145,289,.85)
 handle('grip',[(549,211),(549,233),(561,248),(557,265),(568,289),(582,323)],[(589,211),(600,243),(610,273),(632,307),(601,323)],211,323,.85)
 for side in [-1,1]:b(f'grip{side}/checkered_insert',(571,249),(594,292),28,.07,'rubber',8+side*.46)
 r('guard/front',462,207,470,246,.26,'black');r('guard/floor',465,242,542,249,.28,'black');r('guard/rear',537,207,545,248,.27,'black');r('trigger/root_socket',513,199,523,215,.21,'steel');b('trigger/root',(518,211),(524,225),5,.21,'steel');b('trigger/hook',(524,225),(515,238),5,.21,'steel')
 # Top accessory rail is built from connected raised teeth over a continuous rail bed.
 r('rail/front_bed',37,49,642,57,.78,'steel')
 for j in range(43):r(f'rail/tooth{j}',38+j*14,46,45+j*14,51,.86,'steel')
 r('sight/front_foot',86,47,114,56,.99,'steel');r('sight/front_block',88,28,112,47,.67,'steel');r('sight/front_aperture',95,33,106,41,.74,'black')
 r('optic/mount',337,39,415,59,.95,'steel');r('optic/main',350,19,426,42,1.07,'black');r('optic/roof',345,13,433,21,.99,'black');r('optic/rear_block',420,20,434,38,.94,'black');ring('optic/front_ocular',334,31,15,16,3,'steel',12);ring('optic/front_bore',345,31,12,20,2,'black',12);ring('optic/rear_ocular',433,31,12,6,3,'black',10)
 for s in [-1,1]:pin(f'optic{s}/dial',374,32,8,.08,'steel',8+s*.58)
 r('sight/rear_foot',505,47,532,56,.87,'steel');r('sight/rear_post',512,27,524,47,.27,'steel')
 b('tail/handle_front',(998,58),(998,35),5,.20,'steel');b('tail/handle_top',(998,34),(1080,34),5,.20,'steel');b('tail/handle_rear',(1080,34),(1098,57),5,.20,'steel')
 # Small removable rocket is nested inside the tube, as inherited donor animation expects.
 ring('mag_rocket/core',854,102,34,166,1,'black',12);ring('mag_rocket/collar',776,102,34,17,1,'steel',12);ring('mag_rocket/nose',952,102,34,31,1,'steel',12)

def finish(self,faces,k):
 from PIL import ImageFilter
 for name,fn,img,clear,e,others,painted in faces:
  if clear:continue
  role=e['role'];base=self.D.MATERIALS[role]['color'];kind=self.D.MATERIALS[role]['kind'];raw=img.copy();rp=raw.load();px=img.load();w,h=img.size;lumim=raw.convert('L');smooth=lumim.filter(ImageFilter.GaussianBlur(2));sp=smooth.load()
  for i in range(w):
   for j in range(h):
    rc=rp[i,j];lum=.299*rc[0]+.587*rc[1]+.114*rc[2];rel=lum-sp[i,j];c=base[:];f=1
    if self.wid in ('deliverance','forbearance','cataclysmic'):
     if role in ('shell','edge'):
      # Retain actual engraved seams, relief and side-specific circuit patterns in calm cast-metal fields.
      if lum<25:f=.43
      elif lum<37:f=.73
      elif lum<51:f=.91
      elif lum>83:f=1.10
      if rel<-11:f*=.86
     elif role=='accent':
      f=.86 if rc[0]<105 else 1.0 if rc[0]<140 else 1.10
      if rel<-14:f*=.88
     elif role=='purple':
      f=.92 if lum<75 else 1.06
     elif role=='rubber':f=.86 if rel<-8 else 1.0
    elif self.wid=='apex_predator':
     if role in ('shell','edge','ivory'):
      # Reject the source's broken tube diagnostic grid; only bone chroma/luminance enters the bone field.
      valid=rc[0]>60 and rc[1]>60 and .85<rc[0]/(rc[1]+1)<1.3 and rc[2]<rc[0]*.98
      if valid:
       f=.77 if rel<-12 else .9 if rel<-6 else 1.04 if rel>12 else 1
      if (fn in ('east','west') or e.get('_surface')) and 'grip/navy' not in name and rc[2]>rc[0]*1.15 and max(rc[:3])<95:c=self.D.MATERIALS['accent']['color'];f=1
    else:
     if role in ('shell','edge','ivory'):
      # Real HAKKE panel seams, screw marks and serial decals; source is intentionally pale painted metal.
      if lum<50:f=.48
      elif lum<100:f=.81
      elif lum>205:f=1.05
      if rel<-16:f*=.86
     elif role=='accent':
      # Source white HAKKE label and recessed hex stamp repeat retain correct face placement.
      if min(rc[:3])>150 and max(rc[:3])-min(rc[:3])<70:c=[234,234,217]
      else:f=.70 if rel<-17 else 1.04 if rel>15 else 1
     elif 'checkered_insert' in name:
      f=.68 if (i+j)%5<1 or (i-j)%5<1 else 1
    if role in ('steel','black','gold'):
     f*= {'up':1.14,'down':.76,'east':1,'west':.96,'north':.91,'south':.9}[fn]
     if role=='black' and rel<-12:f*=.8
    px[i,j]=tuple(max(0,min(255,round(v*f))) for v in c)+(255,)
  if e.get('_surface'):continue
  # Shared, restrained single-texel exposed edges; broad sheen comes from real cross-sections and lighting.
  o,u,v=k.face_frame(e,fn);lu=math.dist((0,0,0),u) or 1;lv=math.dist((0,0,0),v) or 1;flags=[]
  for ss,tt in ((-.004,.5),(1.004,.5),(.5,-.004),(.5,1.004)):
   ss=.5+(ss-.5)*(1+.06/lu) if ss!=.5 else .5;tt=.5+(tt-.5)*(1+.06/lv) if tt!=.5 else .5
   flags.append(not any(k.inside(x,k.face_point(e,fn,ss,tt,push=-.015)) for x in others))
  hi=.10 if kind in ('steel','metal','gold') else .04;lo=-.13 if kind in ('steel','metal','gold') else -.07
  def tint(i,j,f):px[i,j]=k.lighten(px[i,j],f)+(255,)
  if w>2 and h>2:
   if flags[2]:
    for i in range(w):tint(i,0,hi)
   if flags[3]:
    for i in range(w):tint(i,h-1,lo)
   if flags[0]:
    for j in range(h):tint(0,j,hi*.5)
   if flags[1]:
    for j in range(h):tint(w-1,j,lo*.5)

def setup():
 spec=importlib.util.spec_from_file_location('g2',ROOT/'scripts/art/w327/group2.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);k=g.setup();k.Baker.materialize=lambda self,faces:finish(self,faces,k);return g,k

def build(w):
 g,k=setup();k.Baker(w).build();a=ROOT/'art/weapons/w327'/w;p=a/'manifest.json';m=json.loads(p.read_text());old=json.loads((a/'review/v2/manifest.json').read_text());d=json.loads((a/'design.json').read_text());source=json.loads((a/'source-evaluation.json').read_text());assert k.sha(Path(source['source']))==source['sha256']
 for key in ['original_blend','original_blend_sha256','source_actions','source_bones','source_hand_rig','official_icon_url','official_icon_sha256','reload_contract','reticle']:m[key]=old[key]
 m.update(batch='W327',revision=3,source_original_unchanged=True,original_blend_unchanged=True,authoring='Purposeful solid cross-sections and secondary mechanisms reconstructed from actual side, top and front source views; native 26.3 rotated cuboids',source_mapping=d['source_mapping'],material_pipeline='Calibrated per-face six-view source mapping with controlled material palette, preserved engraved motifs and single-texel exposed edges; no generic broad gradients',materials=d['materials'],validation='See validation.json and adscheck.json; master native acceptance pending')
 if w=='palmyra_b':m['anchor_note']=dict(method='Uniform source transform anchored at actual pistol-grip contact',source_px=[580,260],canonical=[8,7.665,14.555],donor='Pyroclastic Flow',consequence='Authentic tube fore/aft proportions retained; rear tube extends past donor bounds; native framing/ADS required')
 p.write_text(json.dumps(m,indent=1,sort_keys=True)+'\n')

def validate(w):
 g,k=setup();a=ROOT/'art/weapons/w327'/w;d=json.loads(k.skin_path(w).read_text());es=[e for p in d['parts'].values() for e in p]
 assert len(es)<1000 and len({e['name'] for e in es})==len(es)
 for e in es:
  assert all(-16<=e['from'][i]<e['to'][i]<=32 for i in range(3)),e['name']
  assert len(e['faces'])==6
  for f in e['faces'].values():assert all(0<=v<=16 for v in f['uv']) and f['texture']=='#0'
 def dot(a,b):return sum(x*y for x,y in zip(a,b))
 def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
 def obb(e):return k.rotate(tuple((e['from'][i]+e['to'][i])/2 for i in range(3)),k.rot_of(e)),[k.rotate_vec(tuple(int(i==j) for j in range(3)),k.rot_of(e)) for i in range(3)],[(e['to'][i]-e['from'][i])/2 for i in range(3)]
 O=[obb(e) for e in es]
 def hit(a,b):
  c,u,h=a;d,v,g=b;delta=[d[i]-c[i] for i in range(3)]
  for ax in u+v+[cross(x,y) for x in u for y in v]:
   nn=math.sqrt(dot(ax,ax))
   if nn<1e-7:continue
   if abs(dot(delta,ax))>sum(h[i]*abs(dot(u[i],ax))+g[i]*abs(dot(v[i],ax)) for i in range(3))+.035*nn:return False
  return True
 adj=[set() for e in es]
 for i in range(len(es)):
  for j in range(i):
   if hit(O[i],O[j]):adj[i].add(j);adj[j].add(i)
 seen=set();comps=[]
 for i in range(len(es)):
  if i in seen:continue
  q=[i];seen.add(i);out=[]
  while q:
   x=q.pop();out.append(es[x]['name'])
   for y in adj[x]-seen:seen.add(y);q.append(y)
  comps.append(out)
 from PIL import Image
 im=Image.open(k.atlas_path(w));assert list(im.size)==d['texture_size']
 report=dict(revision=3,parse='PASS',strict_positive_boxes='PASS',unique_names='PASS',normalized_uv='PASS',elements=len(es),parts={p:len(v) for p,v in d['parts'].items()},atlas=list(im.size),atlas_bytes=k.atlas_path(w).stat().st_size,rotated_elements=sum(bool(e.get('rotation')) for e in es),bounds=[[min(v[i] for e in es for v in k._corners(e)) for i in range(3)],[max(v[i] for e in es for v in k._corners(e)) for i in range(3)]],source_original_unchanged=True,connection_method='Native rotated OBB separating-axis adjacency, 0.035px tolerance',connected_components=comps,connections='PASS' if len(comps)==1 else 'REVIEW',native_pack_load='MASTER_PENDING',native_hand_ads_reload='MASTER_PENDING',native_10_20_display='MASTER_PENDING')
 (a/'validation.json').write_text(json.dumps(report,indent=1)+'\n');print(w,'components',[len(c) for c in comps],[c for c in comps if len(c)<25]);g.adscheck(w)

def render(w):
 g,k=setup();a=ROOT/'art/weapons/w327'/w;out=a/'review/v3';out.mkdir(exist_ok=True)
 subprocess.run([k.BLENDER,'--disable-autoexec','--factory-startup','-b','-t','2','--python',str(ROOT/'art/weapons/w327/brigands_law/v3_render.py'),'--',str(out/w),str(k.skin_path(w)),str(k.atlas_path(w)),'east,q,rearq,front'],check=True,stdout=subprocess.DEVNULL)

if __name__=='__main__':
 cmd=sys.argv[1];ids=sys.argv[2:] or IDS
 for w in ids:
  assert w in IDS
  if cmd=='author':
   d=Design(w);globals()[w](d)
   if w=='palmyra_b':
    for e in d.E:
     if e['name'].startswith('lower/'):
      e['from'][0]=8+(e['from'][0]-8)*.64;e['to'][0]=8+(e['to'][0]-8)*.64
   if w=='apex_predator':
    for e in d.E:
     if e['name'].startswith('bone/'):
      e['from'][0]=8+(e['from'][0]-8)*1.4;e['to'][0]=8+(e['to'][0]-8)*1.4
   if w in ('deliverance','forbearance','apex_predator','cataclysmic'):
    sp=importlib.util.spec_from_file_location('exterior_refine',ROOT/'scripts/art/w327/group2_exterior.py');mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod);mod.refine(d,contour,cross_prism)
   d.write()
  elif cmd=='build':build(w)
  elif cmd=='validate':validate(w)
  elif cmd=='render':render(w)
