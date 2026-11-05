"""Material allocation from the six hand-cannon rips; special() contains decals only."""
import math
from hc import fpoint, inpoly
from identity import glyph, GLYPHS

def mat(kind,color,detail=.5,**kw):return dict(kind=kind,color=color,detail=detail,**kw)
COMMON={
 'recess':mat('dark',(15,18,19),0,amp=1,rim=.03),
 'sight':mat('polymer',(26,29,30),0,amp=3,rim=.07),
 'rubber':mat('rubber',(35,37,36),0,amp=5,rim=.05),
 'black_polymer':mat('polymer',(47,49,46),.12,amp=4,rim=.08),
 'dark_steel':mat('metal',(57,60,59),.4,amp=6,field=.07),
 'silver':mat('steel',(177,184,184),.45,amp=7,field=.08),
 'fastener':mat('steel',(131,141,140),.15,amp=5,field=.08),
}
CONFIG={
'allegro_34':{
 'materials':{'olive':mat('paint',(86,102,55),.65),'shroud':mat('metal',(64,65,61),.5),'shell':mat('steel',(159,165,157),.4,amp=7),'white':mat('steel',(210,215,204),.5,amp=6),'frame':mat('metal',(52,53,49),.6),'drum':mat('metal',(77,79,74),.45,field=.1)},
 'rules':[('rim_','white'),('bolt_','fastener'),('sight_','sight'),('guard_','white'),('trigger','white'),('hammer','white'),('rail_','white'),('frame_guard','frame'),('frame_lower','frame'),('frame_rear','frame'),('tang','dark_steel'),('grip_panel','rubber'),('grip_','black_polymer'),('muzzle','silver'),('shroud_low','shell'),('shroud_main','shroud'),('shroud','shroud'),('top_strap','olive'),('frame_fore','shell'),('mag_core','recess'),('mag_drum_fband','silver'),('mag_drum_rband','silver'),('mag_drum','drum')]},
'ballyhoo_mk_27':{
 'materials':{'brown_shell':mat('metal',(86,77,66),.6,amp=6),'teal':mat('paint',(54,86,91),.85,amp=2),'blue_steel':mat('steel',(171,199,202),.65,amp=7),'grip':mat('polymer',(44,34,28),.1,amp=4),'teal_drum':mat('metal',(59,93,96),.7,amp=7,field=.1)},
 'rules':[('rim_','blue_steel'),('strap_','blue_steel'),('bolt_','silver'),('sight_','sight'),('loop','blue_steel'),('guard_','blue_steel'),('trigger','blue_steel'),('hammer','blue_steel'),('grip_frame','blue_steel'),('grip_heel','blue_steel'),('grip_medallion','silver'),('grip_','grip'),('front_lug','dark_steel'),('muzzle','silver'),('shroud','brown_shell'),('barrel_lower','teal'),('top_strap','brown_shell'),('frame_front','teal'),('frame_lower','blue_steel'),('frame_rear','blue_steel'),('mag_core','recess'),('mag_drum_fband','blue_steel'),('mag_drum_rband','blue_steel'),('mag_drum','teal_drum')]},
'lamia_hc2':{
 'materials':{'maroon':mat('paint',(107,62,57),.65,amp=3),'warm_alloy':mat('steel',(184,170,142),.6,amp=7,field=.08),'cell':mat('metal',(92,112,98),.55,amp=5,field=.11),'red_lamp':mat('glow',(204,43,45),0),'blue_lamp':mat('glow',(51,159,194),0)},
 'rules':[('lamp_red','red_lamp'),('lamp_blue','blue_lamp'),('lamp_frame','warm_alloy'),('bolt_','dark_steel'),('sight_','sight'),('guard_','maroon'),('trigger','warm_alloy'),('grip_panel','rubber'),('grip_','maroon'),('muzzle','warm_alloy'),('shroud_endcap','warm_alloy'),('shroud','maroon'),('barrel_block','maroon'),('lower_tail','warm_alloy'),('lower','maroon'),('frame_cell','dark_steel'),('frame','maroon'),('mag_core','recess'),('mag_drum_fband','warm_alloy'),('mag_drum_rband','warm_alloy'),('mag_drum','cell')]},
'mos_ultima_ii':{
 'materials':{'slate':mat('paint',(91,107,124),.7,amp=2),'rib':mat('metal',(82,80,74),.4,amp=6),'cylinder':mat('steel',(156,171,181),.5,amp=8,field=.08)},
 'rules':[('bolt_','silver'),('sight_','sight'),('rim_','silver'),('guard_','dark_steel'),('trigger','dark_steel'),('hammer','dark_steel'),('grip_heel','rib'),('grip_medallion','silver'),('grip_panel','rubber'),('grip_','black_polymer'),('top_rib','rib'),('top_strap','rib'),('muzzle','dark_steel'),('latch','dark_steel'),('mag_core','recess'),('mag_drum_fband','dark_steel'),('mag_drum_rband','dark_steel'),('mag_drum','cylinder'),('frame_','slate'),('shroud','slate')]},
'azimuth_dsu':{
 'materials':{'sage':mat('paint',(165,177,140),.6,amp=3),'cream':mat('paint',(219,210,190),.7,amp=2),'olive_alloy':mat('metal',(112,109,89),.5,amp=7),'panel':mat('polymer',(42,46,38),.35,amp=3),'cylinder':mat('metal',(149,164,137),.55,amp=7,field=.09)},
 'rules':[('bolt_','olive_alloy'),('sight_','sight'),('rim_','cream'),('guard_','cream'),('trigger','silver'),('hammer','cream'),('grip_heel','olive_alloy'),('grip_medallion','silver'),('grip_panel','rubber'),('grip_frame','cream'),('grip_','black_polymer'),('top_rib','olive_alloy'),('top_strap','olive_alloy'),('side_panel','panel'),('muzzle_tube','olive_alloy'),('muzzle','olive_alloy'),('latch','dark_steel'),('mag_core','recess'),('mag_drum_fband','cream'),('mag_drum_rband','cream'),('mag_drum','cylinder'),('frame_','sage'),('shroud','sage')]},
'guseva_c':{
 'materials':{'white_enamel':mat('paint',(215,217,204),.55,amp=2),'orange':mat('paint',(209,94,59),.65,amp=2),'alloy':mat('steel',(176,185,174),.65,amp=8),'brown_grip':mat('polymer',(59,44,33),.15,amp=5),'drum':mat('metal',(53,48,40),.7,amp=7),'lens':mat('lens',(64,132,171),0,field=.16),'light':mat('metal',(43,48,44),.3,amp=5)},
 'rules':[('bolt_','dark_steel'),('sight_','sight'),('rim_','alloy'),('light_','light'),('peg','dark_steel'),('bottom_rail','alloy'),('top_rail','alloy'),('guard','dark_steel'),('trigger','dark_steel'),('frame_lower','dark_steel'),('grip_stock_slope','orange'),('grip_buttplate','dark_steel'),('grip_stock','white_enamel'),('grip_','brown_grip'),('muzzle','alloy'),('shroud_face','alloy'),('top_strap','orange'),('frame_','white_enamel'),('mag_core','recess'),('mag_drum','drum'),('shroud','white_enamel')]}}

# R2: exposed metal is allocated by the actual part, paint stays on the outer coat.
COMMON['rubber']=mat('rubber',(20,23,22),0,amp=4,plate=False,rim=.03)
COMMON['black_polymer']=mat('polymer',(57,62,59),.1,amp=4,rim=.07)
COMMON['dark_steel']=mat('metal',(88,94,93),.35,amp=6,field=.07)
CONFIG['allegro_34']['materials']['frame']=mat('metal',(55,59,55),.5)
CONFIG['allegro_34']['materials']['drum']=mat('metal',(96,101,94),.4,field=.1)
CONFIG['ballyhoo_mk_27']['materials']['brown_shell']=mat('metal',(116,103,87),.5,amp=6)
CONFIG['ballyhoo_mk_27']['materials']['teal_frame']=mat('steel',(104,140,142),.45,amp=6)
CONFIG['ballyhoo_mk_27']['materials']['grip']=mat('polymer',(75,58,46),.1,amp=4)
CONFIG['lamia_hc2']['materials']['red_alloy']=mat('metal',(143,104,95),.4,amp=6)
CONFIG['mos_ultima_ii']['materials']['blue_alloy']=mat('steel',(112,130,145),.45,amp=6)
CONFIG['mos_ultima_ii']['materials']['slate']=mat('paint',(71,85,102),.6,amp=2)
CONFIG['mos_ultima_ii']['materials']['rib']=mat('metal',(62,65,63),.4,amp=6)
CONFIG['azimuth_dsu']['materials']['panel']=mat('metal',(65,74,62),.3,amp=5)
CONFIG['azimuth_dsu']['materials']['exposed_frame']=mat('steel',(174,184,162),.4,amp=6)
CONFIG['guseva_c']['materials']['drum']=mat('metal',(88,86,75),.5,amp=7)
CONFIG['guseva_c']['materials']['brown_grip']=mat('polymer',(65,46,34),.1,amp=4)
for wid,key,color in [
 ('allegro_34','olive',(174,179,152)),('ballyhoo_mk_27','teal',(175,202,203)),
 ('lamia_hc2','maroon',(187,172,143)),('mos_ultima_ii','slate',(151,165,173)),
 ('azimuth_dsu','sage',(224,213,187)),('azimuth_dsu','cream',(116,129,101)),
 ('guseva_c','white_enamel',(129,137,119)),('guseva_c','orange',(208,188,153))]:
 CONFIG[wid]['materials'][key]['wear']=color

def exposed_material(wid,name,face,key):
 if wid=='ballyhoo_mk_27' and name.startswith('frame_front'):return 'teal_frame'
 if wid=='lamia_hc2':
  if name.startswith(('frame_mid','frame_cell','guard_')):return 'red_alloy'
  if name.startswith(('barrel_block','lower_tail','muzzle')):return 'warm_alloy'
 if wid=='mos_ultima_ii':
  if name.startswith(('frame_','shroud_face')):return 'blue_alloy'
  if name.startswith('shroud_s') and ('l' in name.split('_')[1] or 'r' in name.split('_')[1]):return 'blue_alloy'
 if wid=='azimuth_dsu' and name.startswith(('frame_window','frame_rear','guard_','rim_')):return 'exposed_frame'
 if wid=='guseva_c':
  if name.startswith(('frame_window','frame_rear','grip_stock')) and not name.startswith('grip_stock_slope'):return 'alloy'
  if name.startswith('shroud_s') and ('l' in name.split('_')[1] or 'r' in name.split('_')[1]):return 'alloy'
 return key

def materials(wid):return dict(COMMON,**CONFIG[wid]['materials'])
def material(wid,name,face):
 if name.endswith('_bore'):key='recess'
 elif wid=='guseva_c' and name=='light_head' and face=='north':key='lens'
 else:key=next((v for pre,v in CONFIG[wid]['rules'] if name.startswith(pre)),None)
 if key is None:raise ValueError('Unmapped material: '+wid+' '+name)
 key=exposed_material(wid,name,face,key) if not name.endswith('_bore') else key
 m=materials(wid)[key]
 # New cavity caps, end grain and squeezed/raked grips do not have a reliable rip projection.
 if face in ('north','south') or name.startswith(('grip_panel','grip_core','grip_frame','grip_stock','tang')):return dict(m,detail=0,wear=False)
 if face in ('up','down'):return dict(m,detail=min(.25,m['detail']),wear=False)
 return key

def decals(wid,e,fn,s,t,C):
 n=e['name'];p=fpoint(e,fn,s,t);x,y=C.img(n,p);side=fn in ('west','east')
 def box(a,b,d,f):return a<=x<=d and b<=y<=f
 def line(a,b,d,f,width=.65):
  dx,dy=d-a,f-b;l=dx*dx+dy*dy;k=max(0,min(1,((x-a)*dx+(y-b)*dy)/l)) if l else 0
  return math.hypot(x-a-k*dx,y-b-k*dy)<width
 def ring(a,b,r,width=.7):return abs(math.hypot(x-a,y-b)-r)<width
 def label(text,x0,y0,scale):
  width=sum(len(GLYPHS.get(ch,['0'])[0])+1 for ch in text)-1
  xx=x0+width*scale-(x-x0) if fn=='west' else x
  return glyph(xx,y,text,x0,y0,scale)
 def ink(rgb):return (*rgb,255)
 def paint(rgb):
  # Colour decals retain a subdued painted surface instead of forming flat plastic patches.
  grain=((int(x*2)*17+int(y*2)*29)%23-11)*.16
  v=.97+.04*math.cos(t*math.pi)
  return tuple(max(0,min(255,round(c*v+grain))) for c in rgb)+(255,)
 if n.startswith('sight_rear_') and fn=='south' and n in ('sight_rear_l','sight_rear_r') and .3<s<.7 and .3<t<.7:return ink((179,203,160))
 if n.startswith('lamp_') and t<.2:return ink((235,214,186))
 if wid=='guseva_c' and n=='light_head' and fn=='north':
  if .25<s<.38 and .23<t<.38:return ink((231,244,246))
  if .27<math.hypot(s-.5,t-.5)<.31:return ink((163,198,211))
  return None
 # R2 hand-authored shallow motifs: no added cubes and no filled face overlays.
 if side and wid=='mos_ultima_ii' and n.startswith('shroud'):
  # Source service-door outline and tiny cooling slots along the receiver shoulder.
  if line(255,51,365,51,.65) or line(255,51,255,80,.65):return ink((158,176,188))
  for a in range(220,351,13):
   if box(a,38,a+5,39):return ink((40,51,59))
 if side and wid=='azimuth_dsu' and n.startswith('side_panel'):
  if line(265,62,351,62,.65) or line(265,62,265,91,.65):return ink((133,144,117))
  for a in (272,345):
   if line(a,68,a,85,.65):return ink((30,37,29))
 if side and wid=='ballyhoo_mk_27' and n.startswith('front_lug'):
  for a in (232,258):
   if line(a,83,a,94,.65):return ink((149,184,184))
 if side and wid=='guseva_c' and n.startswith('light_body'):
  if abs((p[2]*20)%9)<.9:return ink((27,34,29))
 if not side:return None
 if n.startswith(('bolt_','grip_medallion')) and abs(t-.5)<.065 and .22<s<.78:return ink((29,33,32))
 if n.startswith('grip_medallion') and abs(s-.5)<.055 and .22<t<.78:return ink((29,33,32))
 if wid=='allegro_34':
  if n.startswith('shroud'):
   if box(251,34,276,39) or box(288,34,366,39):return ink((218,224,211))
   if line(242,47,370,47):return ink((27,31,27))
   for j in range(2):
    for i in range(11):
     if math.hypot(x-(274+i*8.7+j*3),y-(60+j*6))<1.8:return ink((22,26,22))
   for pg in [[(196,22),(240,22),(334,41),(344,50),(300,50),(228,37),(196,30)],[(330,50),(343,50),(374,78),(360,80)],[(350,50),(360,50),(380,66),(380,76)]]:
    if inpoly(x,y,pg):return paint((86,102,55))
  if n.startswith('frame_fore') and ring(196,50,4.5):return ink((116,130,88))
  if n.startswith('hammer') and ring(86,42,6):return ink((58,65,58))
 elif wid=='ballyhoo_mk_27':
  if n.startswith('shroud_front'):
   if line(293,60,315,22,1.8):return paint((203,221,221))
   for a in (207,280):
    if abs(x-a)<.7 and 27<y<56:return ink((40,38,32))
    for b in (29,39,49):
     if box(a-3,b-1,a-1,b+1):return ink((154,150,132))
 elif wid=='lamia_hc2':
  if n.startswith(('shroud','barrel_block')):
   if box(205,49,317,65):
    for j in range(3):
     for i in range(18):
      if math.hypot(x-(210+i*6+(j%2)*3),y-(52+j*5))<1.3:return ink((28,31,27))
    # Leave the unperforated area to the warm-alloy material.
   if ring(242,29,5.2) or ring(268,29,5.2) or line(248,29,262,29,.5):return ink((202,188,159))
  if n.startswith(('grip_frame','shroud_rear')):
   if ring(76,49,7) or math.hypot(x-76,y-49)<2 or box(63,60,89,62):return ink((205,194,167))
  if n.startswith('frame_mid') and label('OMOLON',124,87,1.35):return ink((205,194,167))
 elif wid=='azimuth_dsu':
  if n.startswith(('shroud','frame_','top_strap')):
   for pg in [[(100,30),(150,30),(140,50),(118,60),(100,55)],[(165,70),(215,62),(240,85),(200,98),(160,92)],[(220,30),(270,32),(262,46),(230,50)],[(330,32),(385,36),(385,50),(350,52)],[(90,80),(150,82),(150,92),(92,92)]]:
    if inpoly(x,y,pg):return paint((224,215,194))
 elif wid=='guseva_c':
  if n.startswith('shroud'):
   if label('HAKKE',205,49,1.5):return ink((237,237,220))
   if box(200,30,350,40) or box(200,48,340,64):return paint((162,165,124))
  if n.startswith('grip_stock'):
   if ((71<x<75 or 84<x<88) and 51<y<62) or (68<x<91 and 55<y<58):return ink((177,46,34))
 return None
