"""Brigand's Law V3 semantic reconstruction. Side coordinates refer to actual px source view (515x341)."""
from pathlib import Path
import json, math
A=Path(__file__).resolve().parent
S=36.5;Q=S/1400
CY=-.12476199120283127;CZ=.056399501860141754
E=[]
M={
'ivory':{'color':[183,177,158],'kind':'bone'},
'ivory_edge':{'color':[201,195,174],'kind':'bone'},
'ivory_dark':{'color':[139,133,115],'kind':'bone'},
'steel':{'color':[112,125,128],'kind':'steel'},
'steel_edge':{'color':[153,165,165],'kind':'steel'},
'bolt':{'color':[48,55,56],'kind':'metal'},
'bore':{'color':[15,20,22],'kind':'rubber'},
'navy':{'color':[39,47,75],'kind':'paint'},
'gold':{'color':[160,139,88],'kind':'gold'},
'gold_edge':{'color':[197,176,119],'kind':'gold'},
'grip':{'color':[168,162,143],'kind':'bone'}}
def point(px,py,x=8):return [x,8.9+S*CZ+(170.5-py)*Q,7.7+S*CY+(px-257.5)*Q]
def box(n,lo,hi,role,rotation=None):
 e=dict(name=n,**{'from':[round(v,6) for v in lo],'to':[round(v,6) for v in hi]},role=role)
 if rotation:e['rotation']=rotation
 E.append(e);return e

def rect(n,x1,y1,x2,y2,width,role,xc=8):
 a=point(x1,y2,xc-width/2);b=point(x2,y1,xc+width/2);return box(n,a,b,role)
def beam(n,a,b,thick,width,role,xc=8):
 p=point(*a,xc[0] if isinstance(xc,tuple) else xc);q=point(*b,xc[1] if isinstance(xc,tuple) else xc);c=[(p[i]+q[i])/2 for i in range(3)];L=math.dist(p,q);t=thick*Q
 ang=math.degrees(math.asin(-(q[1]-p[1])/L));yaw=math.degrees(math.atan2(q[0]-p[0],q[2]-p[2]));return box(n,[c[0]-width/2,c[1]-t/2,c[2]-L/2],[c[0]+width/2,c[1]+t/2,c[2]+L/2],role,dict(origin=c,x=ang,y=yaw,z=0))
def ring(n,px,py,radius,depth,width,role,N=12):
 # Ring normal is gun Z; meaningful radial wall segments, recessed bore remains open.
 c=point(px,py);r=radius*Q;t=width*Q;L=2*(r-t/2)*math.tan(math.pi/N)
 for j in range(N):
  a=2*math.pi*j/N;cc=[c[0]+(r-t/2)*math.sin(a),c[1]+(r-t/2)*math.cos(a),c[2]]
  box(n+f'/{j:02}',[cc[0]-L/2,cc[1]-t/2,cc[2]-depth*Q/2],[cc[0]+L/2,cc[1]+t/2,cc[2]+depth*Q/2],role,dict(origin=cc,x=0,y=0,z=-math.degrees(a)))
def disk(n,px,py,r,depth,role,xc=8,N=8):
 # Side-facing solid polygon: a cross core plus diagonal corner blocks.
 c=point(px,py,xc);rr=r*Q;z=(math.sqrt(2)-1)*rr
 box(n+'/coreA',[xc-depth/2,c[1]-rr,c[2]-z],[xc+depth/2,c[1]+rr,c[2]+z],role)
 box(n+'/coreB',[xc-depth*.499,c[1]-z,c[2]-rr],[xc+depth*.499,c[1]+z,c[2]+rr],role)
 for j in range(4):
  ang=45+90*j;aa=math.radians(ang);cc=[xc,c[1]+rr*.5*math.cos(aa),c[2]+rr*.5*math.sin(aa)]
  # central overlap buried under core; outer flat follows octagon.
  box(n+f'/facet{j}',[xc-depth*.498,cc[1]-z,cc[2]-rr*.5],[xc+depth*.498,cc[1]+z,cc[2]+rr*.5],role,dict(origin=cc,x=-ang,y=0,z=0))

def tube(n,p1,p2,py,r,role):
 # 8-sided solid cylinder, 4 overlapping rectangular prisms, axial contact body.
 c=point((p1+p2)/2,py);rr=r*Q;a=rr*(math.sqrt(2)-1)
 for j in range(4):
  box(n+f'/{j}',[c[0]-a,c[1]-rr,point(p1,py)[2]],[c[0]+a,c[1]+rr,point(p2,py)[2]],role,dict(origin=c,x=0,y=0,z=j*45))

# Exposed barrel and rear breech are truly round, sitting inside an open swept ivory cradle.
tube('barrel/exposed_octagonal',49,276,51,12,'steel')
tube('breech/black_bolt',274,326,53,15,'bolt')
tube('breech/rear_sleeve',326,405,56,20,'ivory')
ring('breech/brass_lock_collar',327,53,17,5,3,'gold',8)
# Front layered collar, bore and interior: deliberately substantial in front view.
ring('muzzle/ivory_outer',39,66,33,12,9,'ivory',12)
ring('muzzle/steel_recess',34,66,24,5,6,'steel',12)
ring('muzzle/lip',31,66,19,3,2.5,'steel_edge',12)
ring('muzzle/inner_bore_wall',43,66,17,18,3,'bore',12)
rect('muzzle/bore_back',53,50,54,82,.78,'bore')
# Receiver keel follows the shallow bulge under the barrel; unequal widths create readable cross-sections.
beam('receiver/front_lower_cheek',(39,86),(119,102),38,1.79,'ivory')
beam('receiver/belly_forward',(110,107),(190,113),45,2.06,'ivory')
beam('receiver/belly_rear',(189,111),(261,106),48,2.16,'ivory')
beam('receiver/rising_rear_cheek',(258,104),(331,91),44,2.10,'ivory')
beam('receiver/grip_bridge',(327,103),(405,115),50,1.94,'ivory')
beam('receiver/rear_scroll',(402,96),(456,83),42,1.78,'ivory')
rect('receiver/steel_bedding',58,60,328,78,1.37,'steel')
# Chamfered lower ledges are narrower contact solids, not parallel floating rails.
beam('receiver/front_lower_chamfer',(40,104),(116,122),7,1.35,'ivory_dark')
beam('receiver/belly_lower_chamfer',(116,127),(212,135),7,1.61,'ivory_dark')
beam('receiver/rear_lower_chamfer',(211,134),(286,124),7,1.66,'ivory_dark')
# Top bow has real air underneath and sweeps down into the rear bridge.
beam('bow/front_nose',(34,31),(139,36),6,1.31,'ivory_edge')
beam('bow/rising_front',(139,32),(208,18),6,1.16,'ivory_edge')
beam('bow/crest',(207,18),(267,20),6,1.14,'ivory')
beam('bow/descending_rear',(266,20),(333,33),7,1.19,'ivory')
beam('bow/rear_bridge',(332,33),(398,32),9,1.38,'ivory')
beam('rear/upper_tail',(397,38),(465,54),17,1.42,'ivory')
beam('rear/raised_tail_point',(465,53),(495,44),14,1.04,'ivory')
rect('rear/cap',407,58,494,77,1.58,'ivory')
rect('rear/dark_breech_slot',347,53,389,61,1.66,'bolt')
rect('rear/breech_slot_roof',347,50,391,53,1.74,'ivory_edge')
rect('rear/breech_slot_sill',347,61,391,65,1.73,'ivory_dark')
rect('grip/shoulder_socket',377,123,443,152,1.56,'grip')
# Strong raked handle. Inner spine joins receiver to a palm swell, not a vertical stick.
beam('grip/internal_spine',(394,140),(443,288),43,1.35,'grip')
beam('grip/upper_raked_cheek',(405,143),(423,201),73,1.84,'grip')
beam('grip/palm_swell',(423,199),(447,262),80,2.00,'grip')
beam('grip/heel',(447,259),(447,293),82,1.91,'grip')
beam('grip/backstrap_upper',(440,145),(456,201),10,1.53,'ivory_edge')
beam('grip/backstrap_curve',(456,200),(482,249),11,1.64,'ivory_edge')
beam('grip/backstrap_palm',(482,248),(488,272),12,1.61,'ivory_edge')
beam('grip/heel_return',(488,272),(476,294),10,1.56,'ivory')
beam('grip/frontstrap_upper',(374,151),(392,222),7,1.45,'ivory_dark')
beam('grip/frontstrap_lower',(392,222),(410,287),8,1.51,'ivory_dark')
# Real cut-out trigger bow, three swept segments plus heel. Trigger curls inside clear negative space.
beam('guard/front_rising',(185,196),(218,166),6,0.34,'ivory')
beam('guard/front_root',(217,167),(256,120),7,0.38,'ivory')
beam('guard/long_floor',(184,197),(366,183),7,0.39,'ivory')
beam('guard/rear_root',(366,184),(386,150),8,0.49,'ivory')
beam('trigger/root',(337,128),(342,158),6,0.32,'steel')
beam('trigger/hook',(342,157),(335,171),6,0.32,'steel')
beam('trigger/curl',(336,170),(326,176),5,0.32,'steel_edge')
# Separate magazine at inherited heel; retain static-source caveat and existing 61-pose base movement.
rect('mag_floor/base',398,306,486,322,1.95,'ivory')
beam('mag_floor/front_lip',(396,306),(487,306),5,2.04,'ivory_edge')
beam('mag_floor/heel_lip',(399,323),(483,323),6,1.83,'ivory_dark')
rect('mag_floor/neck',410,294,473,306,1.58,'grip')
# Lateral steel tines are source features. Two different flanks, anchored to round pivots.
for sign in [-1,1]:
 x=8+sign*1.02
 beam(f'tine{sign}/root',(158,79),(118,104),11,.13,'steel',x)
 beam(f'tine{sign}/sweep',(118,104),(68,127),7,.11,'steel',(x,x+sign*.24))
 beam(f'tine{sign}/tip',(68,127),(17,150),3,.08,'steel_edge',(x+sign*.24,x+sign*1.15))
 disk(f'tine{sign}/pivot',156,76,7,.16,'steel',x)
 # Gold side lever is offset proud of cheek; it has two pivots and articulated link.
 disk(f'lever{sign}/forward_pivot',353,108,9,.36,'gold',x+.08*sign)
 disk(f'lever{sign}/rear_pivot',422,94,10,.46,'gold',x+.08*sign)
 beam(f'lever{sign}/forward_link',(354,108),(373,106),6,.14,'gold_edge',x+.16*sign)
 beam(f'lever{sign}/rising_link',(373,106),(395,91),7,.15,'gold',x+.16*sign)
 beam(f'lever{sign}/rear_link',(395,91),(423,94),7,.15,'gold_edge',x+.16*sign)
 # Trigger latch: open upright oval surrounding an actual recessed dark socket.
 rect(f'latch{sign}/dark_socket',263,92,288,120,.08,'bolt',x)
 beam(f'latch{sign}/front',(276,83),(269,98),4,.24,'steel',x+.12*sign)
 beam(f'latch{sign}/front_lower',(269,98),(274,123),4,.09,'steel',x+.12*sign)
 beam(f'latch{sign}/back',(288,86),(292,113),4,.09,'steel',x+.12*sign)
 beam(f'latch{sign}/top',(277,82),(287,85),4,.09,'steel',x+.12*sign)
 beam(f'latch{sign}/bottom',(274,123),(287,126),4,.09,'steel',x+.12*sign)
 # Recessed fastener plate below barrel and real large grip medallion.
 rect(f'plate{sign}/bedding',151,96,197,117,.12,'ivory_dark',x)
 rect(f'plate{sign}/steel_inset',157,100,192,112,.14,'bolt',x+.07*sign)
 for px in [166,185]:disk(f'plate{sign}/screw{px}',px,106,4,.16,'steel_edge',x+.15*sign)
 disk(f'grip{sign}/medallion_rim',441,257,31,.15,'navy',8+sign*1.04)
 disk(f'grip{sign}/medallion_face',441,257,26,.16,'navy',8+sign*1.12)
 disk(f'grip{sign}/root_pin',393,143,9,.15,'steel',8+sign*.99)
# Top aiming beads and source bolt collar, deliberately low enough for base ADS.
disk('rear/bolt_pin',394,27,5,.96,'steel',8)
rect('sight/rear_base',463,41,482,46,.64,'steel')
rect('sight/rear_left_ear',470,35,478,42,.14,'ivory',7.73)
rect('sight/rear_right_ear',470,35,478,42,.14,'ivory',8.27)
rect('sight/front_blade',44,25,49,34,.13,'steel')
# Face-level source projection shares one calibrated model/source transform.
import importlib.util
sp=importlib.util.spec_from_file_location('brigand_fidelity',A/'v3_fidelity.py');fidelity=importlib.util.module_from_spec(sp);sp.loader.exec_module(fidelity);E,C=fidelity.refine(E,point)
D=dict(revision=3,geometry_revision=4,materials=M,elements=E,contours=C,source_mapping=dict(scale=S,offset=[8,8.9,7.7],note='Exact calibrated source-space mapping, not stretched bounding-box fitting'))
(A/'design.json').write_text(json.dumps(D,indent=1)+'\n')
print(len(E),'purposeful elements')
