#!/usr/bin/env python3
"""W350 R2 authored semantic solids. No source vertices exported.
Closed lofts and traced profiles use the accepted W327 native adapter.
"""
import sys,json,math,copy,hashlib,subprocess,importlib.util,functools
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[3]
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
energy=mod('energy_r1',ROOT/'scripts/art/w350/energy.py');kit=energy.kit;A=energy.A
ref=mod('energy_r2_reference',ROOT/'scripts/art/w327/group3_v3.py')
opt=mod('energy_r2_optimizer',ROOT/'scripts/art/w327/group3_optimize.py')
P=Path('/tmp/exotic-expansion-20261109/sources')
FRAME={'sunshot':(.020,-10,3.5,570,80,1122),'graviton_lance':(.0252,-10.6,4.2,550,80,1122),'jotunn':(.020,-7.1,5.3,625,80,1122)}
class Shape(ref.SourceShape):
 def __init__(self,w):
  ref.FIDELITY_FRAME[w]=(1,0,0);super().__init__(w);self.w=w;self.px,self.z0,self.y0,self.bottom,self.left,self.right=FRAME[w]
 def point(self,x,px,py):return (8+x,self.y0+(self.bottom-py)*self.px,self.z0+(px-self.left)*self.px)
 def outline(self,n,points,w,m='shell',x=0):
  start=len(self.authored_triangles);self.panel(n,points,w,m)
  if x:
   names={t['name'] for t in self.authored_triangles[start:]}
   for t in self.authored_triangles[start:]:t['vertices']=[[p[0]+x,p[1],p[2]] for p in t['vertices']]
   for e in self.e:
    if e['name'].rsplit('_',1)[0] in names:
     e['from'][0]+=x;e['to'][0]+=x;e['rotation']['origin'][0]+=x
 def cyl(self,n,x,py,a,b,r,m='steel',sides=12):
  cy=self.point(0,0,py)[1];za=self.point(0,a,0)[2];zb=self.point(0,b,0)[2]
  self.loft(n,[[(8+x+math.sin(i*math.tau/sides)*r,cy+math.cos(i*math.tau/sides)*r,z) for i in range(sides)] for z in [za,zb]],m)
 def pipe(self,n,points,r=.15,m='steel',x=0):
  rings=[];sides=6 if self.w=='jotunn' else 8
  for j,(px,py) in enumerate(points):
   a=points[max(0,j-1)];b=points[min(len(points)-1,j+1)];dy=-(b[1]-a[1]);dz=b[0]-a[0];L=math.hypot(dy,dz);cy,cz=self.point(x,px,py)[1:]
   rings.append([(8+x+r*math.cos(i*math.tau/sides),cy+r*math.sin(i*math.tau/sides)*dz/L,cz-r*math.sin(i*math.tau/sides)*dy/L) for i in range(sides)])
  self.loft(n,rings,m)

def sunshot():
 s=Shape('sunshot')
 s.shell('upper_solar_blade',[(118,179,183,.16,.30),(173,177,243,1.35,.45),(390,173,242,1.62,.43),(620,168,237,1.65,.42),(716,166,239,1.63,.43)],'accent')
 s.shell('lower_ivory_blade',[(80,384,385,.08,.4),(173,280,384,1.4,.45),(390,279,384,1.62,.43),(553,279,384,1.64,.43),(695,279,351,1.50,.45),(716,279,350,1.42,.46)],'shell')
 # A closed continuous vent frame: two diamond apertures cut through the web.
 # Upper/lower rails and each inter-hole pier meet; no detached capsule bars.
 s.outline('vent_web_upper',[(173,242),(403,242),(403,260),(351,260),(334,244),(317,260),(276,260),(259,244),(242,260),(173,260)],.88,'steel')
 s.outline('vent_web_lower',[(173,260),(242,260),(259,277),(276,260),(317,260),(334,277),(351,260),(403,260),(403,279),(173,279)],.88,'steel')
 s.outline('vent_rear_core',[(402,242),(716,239),(716,279),(403,279),(390,262)],.90,'steel')
 s.outline('top_spine',[(118,179),(982,178),(985,187),(135,190)],.65,'black_steel')
 s.outline('upper_rear_rail',[(715,166),(1034,154),(984,201),(847,202),(844,195),(750,195)],1.05,'accent')
 s.shell('rear_frame',[(865,199,316,1.03,.55),(902,201,318,1.25,.56),(972,200,319,1.37,.62),(993,242,290,.93,.60)],'black_steel')
 for sd in [-1,1]:
  s.outline('rear_side_shoulder'+str(sd),[(881,285),(976,284),(1007,321),(918,337),(890,316)],.12,'steel',sd*.74)
  s.outline('rear_side_recess'+str(sd),[(896,292),(966,290),(981,309),(916,319)],.07,'black_steel',sd*.82)
 s.outline('crane_lower_frame',[(715,294),(729,319),(851,319),(886,288),(917,349),(695,352),(715,348)],1.26,'steel')
 s.outline('cylinder_top_bridge',[(715,197),(852,197),(884,212),(894,236),(880,237),(865,214),(845,208),(737,208),(718,226)],1.08,'shell')
 s.loft('mag_cylinder',[[(8+math.sin(i*math.tau/12)*r,s.point(0,0,260)[1]+math.cos(i*math.tau/12)*r,s.point(0,z,0)[2]) for i in range(12)] for z,r in [(727,.78),(739,1.02),(755,1.12),(850,1.12),(866,1.02),(876,.78)]],'black_steel')
 s.cyl('mag_front_ring',0,260,725,739,1.15,'steel',12)
 s.cyl('mag_rear_ring',0,260,863,878,1.15,'steel',12)
 s.cyl('mag_axle',0,260,878,987,.34,'steel',8)
 s.beamp('mag_crane',(715,335),(867,335),.28,.22,'steel')
 s.griploft('ivory_grip',[(349,893,989,1.20),(387,910,1017,1.34),(447,937,1061,1.37),(515,968,1105,1.47),(549,979,1121,1.55),(570,976,1120,1.57)],'rubber')
 s.outline('grip_backstrap',[(978,351),(990,351),(1118,524),(1122,566),(1110,567),(1105,529)],.72,'steel')
 s.pipe('trigger_guard',[(788,353),(791,390),(809,425),(839,431),(870,425),(887,399),(895,357)],.11,'steel')
 s.outline('trigger',[(839,354),(849,353),(862,378),(862,389),(846,409),(839,408),(850,385),(847,371)],.20,'steel')
 s.boxp('sight_saddle',(803,160),(820,178),.67,'black_steel',.02)
 s.boxp('front_sight',(207,172),(219,180),.15,'steel',.02)
 return s

def graviton_lance():
 s=Shape('graviton_lance')
 # Long hollow faceted upper bore, with continuous chamfered surfaces.
 s.shell('upper_hex_bore',[(118,211,282,1.80,.56),(516,210,282,1.80,.56),(818,212,282,1.83,.56)],'shell')
 s.tubep('open_muzzle',80,118,246,.77,'steel',.14)
 s.boxp('top_spine',(90,199),(820,212),.70,'black_steel',.03)
 s.shell('receiver',[(818,211,364,1.83,.58),(843,213,378,2.15,.63),(970,213,378,2.15,.63),(993,214,360,1.89,.60)],'shell')
 s.boxp('receiver_upper_band',(820,199),(1109,214),.77,'steel',.035)
 # Stock loop leaves the central aperture genuinely empty, with internal U conductor.
 s.outline('stock_upper',[(991,213),(1117,213),(1117,231),(991,231)],1.60,'shell')
 s.outline('stock_butt',[(1107,198),(1120,198),(1122,353),(1109,360),(1107,320)],1.75,'black_steel')
 s.outline('stock_lower',[(991,324),(1107,324),(1107,357),(992,357)],1.60,'shell')
 s.pipe('rear_conductor',[(992,246),(1065,246),(1081,255),(1088,272),(1080,291),(1062,299),(992,299)],.22,'steel')
 # Forward return conductor has an open bend and independent lower spine.
 s.pipe('front_conductor',[(514,303),(111,303),(95,309),(92,323),(103,337),(124,340),(516,340)],.22,'steel')
 s.boxp('lower_rail',(262,328),(819,351),.68,'black_steel',.04)
 s.boxp('conductor_sleeve',(515,288),(638,323),.86,'steel',.06)
 s.boxp('rear_conductor_collar',(819,288),(867,320),1.02,'steel',.05)
 # Five conductors bridge the source cutaway. Each tube remains readable in oblique.
 for side in [-1,1]:
  for j in range(4):
   s.pipe('voltage_filament'+str(side)+'_'+str(j),[(638,292+j*7),(818,292+j*7)],.037,'accent',side*.45)
 # Lower hand structure, finger grooves and open skeleton triangle are functional solids.
 s.outline('lower_front_frame',[(490,351),(647,351),(648,359),(571,358),(596,386),(651,388),(657,395),(526,395)],.94,'steel')
 s.outline('grip',[(646,352),(664,350),(671,365),(665,375),(678,388),(671,400),(687,411),(690,428),(706,438),(730,468),(737,484),(724,501),(722,515),(761,515),(779,481),(784,464),(768,453),(753,427),(738,405),(720,388),(721,366),(732,354)],1.04,'rubber')
 s.pipe('skeleton_guard',[(732,355),(832,355),(837,365),(810,441),(796,459),(781,458)],.09,'steel')
 s.pipe('trigger',[(665,354),(664,364),(679,377),(678,386),(670,392)],.075,'steel')
 s.outline('mag_shell',[(851,377),(977,377),(924,540),(912,548),(815,520),(810,510)],1.30,'shell')
 # Prefix named magazine parts retain detached reload contract.
 for e in s.e:
  if e['name'].startswith('mag_shell'):e['name']='mag_'+e['name'];s.roles[e['name']]=s.roles[e['name'][4:]]
 for t in s.authored_triangles:
  if t['name'].startswith('mag_shell'):t['name']='mag_'+t['name']
 s.outline('mag_floor',[(814,514),(918,540),(914,549),(807,522)],1.43,'steel')
 s.boxp('optic_saddle',(670,182),(740,198),.60,'black_steel',.03)
 s.boxp('optic_roof',(619,143),(735,151),1.02,'steel',.035)
 s.boxp('optic_floor',(619,173),(735,180),1.02,'steel',.035)
 for sd in [-1,1]:s.boxp('optic_wall'+str(sd),(619,151),(735,173),.11,'shell',.025);s.e[-3]['from'][0]+=sd*.48;s.e[-3]['to'][0]+=sd*.48;s.e[-2]['from'][0]+=sd*.48;s.e[-2]['to'][0]+=sd*.48;s.e[-1]['from'][0]+=sd*.48;s.e[-1]['to'][0]+=sd*.48
 return s

def jotunn():
 s=Shape('jotunn')
 # Furnace is a genuinely deep rectangular hollow section, with four chamfered walls.
 # Rail pair defines the full upper outline, with a separate recessed central bridge.
 for sd in [-1,1]:
  s.outline('upper_rail'+str(sd),[(82,195),(916,192),(973,207),(1108,206),(1121,214),(1121,240),(90,241)],.58,'shell',sd*2.72)
  s.outline('furnace_wall'+str(sd),[(98,222),(235,239),(238,498),(226,510),(105,510)],.60,'shell',sd*2.48)
 s.boxp('furnace_roof',(99,220),(236,250),4.55,'steel',.08)
 s.boxp('furnace_floor',(101,484),(238,511),4.55,'black_steel',.08)
 # The square mouth has visible inner return walls and an ember recess, not painted black.
 for sd in [-1,1]:s.box('inner_bore_side'+str(sd),8+sd*1.86-.18,8+sd*1.86+.18,7.98,12.74,-6.75,-5.45,'black_steel')
 s.box('inner_bore_top',6.15,9.85,12.4,12.8,-6.75,-5.4,'steel')
 s.box('inner_bore_floor',6.15,9.85,7.98,8.35,-6.75,-5.4,'steel')
 s.box('furnace_recess',6.2,9.8,8.3,12.4,-5.4,-5.15,'recess')
 for j in range(3):s.box('furnace_ember'+str(j),6.9+j*.75,7.12+j*.75,8.8,11.9,-5.42,-5.38,'lens')
 s.boxp('top_bridge',(239,212),(838,240),3.95,'steel',.09)
 s.outline('rear_angular_receiver',[(626,244),(1121,244),(1110,276),(1060,278),(985,384),(953,384),(897,307),(687,307),(687,288)],4.55,'shell')
 # Side cheek compound shield has rounded front and swept lower rear; independent genuine depth.
 for sd in [-1,1]:
  s.outline('cheek'+str(sd),[(358,307),(741,307),(747,336),(742,378),(725,422),(697,464),(659,500),(621,521),(390,521),(390,346),(358,326)],.39,'shell',sd*2.60)
  s.outline('cheek_front_trim'+str(sd),[(390,348),(401,350),(401,513),(390,513)],.12,'trim',sd*2.85)
  s.outline('cheek_lower_trim'+str(sd),[(400,515),(620,515),(656,496),(666,499),(626,527),(400,527)],.12,'trim',sd*2.85)
  # Protective loop is one closed octagonal loft; tangent sections meet edge to edge.
  s.pipe('gold_return_pipe'+str(sd),[(685,267),(367,267),(317,280),(277,310),(253,349),(247,391),(256,438),(283,478),(323,508),(371,522),(617,522)],.29,'accent',sd*2.85)
  for j in range(3):
   s.pipe('rear_cable'+str(sd)+'_'+str(j),[(742,329+j*19),(797,328+j*21),(850,331+j*22),(896,326+j*22),(916,319+j*19)],.09,'black_steel',sd*1.65)
  s.boxp('pipe_clamp'+str(sd),(361,216),(377,289),.20,'trim',.025)
  # Move clamp to the real side pipe instead of spawning plates near centre.
  for e in s.e[-3:]:e['from'][0]+=sd*2.85;e['to'][0]+=sd*2.85
  s.boxp('lower_pipe_clamp'+str(sd),(377,506),(393,570),.20,'trim',.025)
  for e in s.e[-3:]:e['from'][0]+=sd*2.85;e['to'][0]+=sd*2.85
  s.pipe('lower_return'+str(sd),[(277,553),(288,574),(319,594),(362,605),(702,605),(736,600),(752,585),(752,567),(738,555),(697,552)],.27,'black_steel',sd*1.72)
 s.outline('lower_spine',[(80,537),(384,536),(384,548),(481,548),(492,560),(492,581),(370,581),(353,564),(81,549)],3.84,'steel')
 s.outline('lower_hand_frame',[(370,553),(704,553),(758,549),(801,556),(830,568),(835,581),(812,622),(806,625),(380,625)],2.8,'black_steel')
 s.outline('lower_forebrace',[(385,526),(430,527),(483,554),(441,554)],.40,'trim')
 s.outline('lower_rearbrace',[(626,527),(667,511),(679,517),(655,537),(683,551),(672,558),(625,539)],.40,'trim')
 # Liftable top cell, preserving a separately moving named magazine assembly.
 s.outline('mag_topcell',[(547,196),(814,195),(839,209),(839,224),(547,224)],2.75,'steel')
 s.cyl('mag_cell_latch',0,202,811,846,.25,'steel',8)
 s.boxp('optic_saddle',(825,188),(866,200),1.05,'black_steel',.02)
 s.outline('optic_plate',[(831,188),(832,183),(840,179),(848,179),(859,186),(869,198),(849,219)],.19,'steel')
 return s

BUILD={'sunshot':sunshot,'graviton_lance':graviton_lance,'jotunn':jotunn}
@functools.lru_cache(maxsize=3)
def source_eval(w):return json.loads((kit.art(w)/'source-evaluation.json').read_text())
def source_point(w,p):
 ev=source_eval(w);lo,hi=ev['lo'],ev['hi'];px,z0,y0,bottom,left,right=FRAME[w];scale=(right-left)*px/max(hi[i]-lo[i] for i in range(3))
 if w=='graviton_lance':return (hi[0]-(p[2]-z0)/scale,(lo[1]+hi[1])/2-(p[0]-8)/scale,lo[2]+(p[1]-y0)/scale)
 return ((lo[0]+hi[0])/2-(p[0]-8)/scale,lo[1]+(p[2]-z0)/scale,lo[2]+(p[1]-y0)/scale)
PALETTE=energy.PALETTES
PALETTE['sunshot'].update(shell=('steel',[207,205,189]),accent=('gold',[160,123,76]),rubber=('paint',[205,203,183]),steel=('steel',[98,105,103]),trim=('steel',[155,158,148]))
def bake(w):
 s=opt.optimize(BUILD[w]());assert len(s.e)<=1000,(w,len(s.e));out=kit.art(w)/'r2';out.mkdir(exist_ok=True)
 cache=P/w/('projection_r2' if (P/w/'projection_r2/manifest.json').exists() else 'projection');man=json.loads((cache/'manifest.json').read_text());views={n:kit.View(cache,n,man) for n in man['views']}
 def paint(e,fn,u,v):
  role=s.roles[e['name']];kind,col=PALETTE[w][role];col=list(col);p=kit.face_point(e,fn,u,v);normal=kit.rotate_vec(kit.NORMALS[fn],kit.rot_of(e))
  sn=(-normal[2],-normal[0],normal[1]) if w=='graviton_lance' else (-normal[0],normal[2],normal[1])
  ax=max(range(3),key=lambda i:abs(sn[i]));view=views[('p' if sn[ax]>0 else 'n')+'xyz'[ax]];sp=source_point(w,p);uu,vv=view.project(sp);rgb=view.sample(uu,vv)
  if rgb and role not in ('recess','lens'):
   r,g,b=rgb;lum=(r+g+b)/3
   if w=='sunshot':
    if role in ('shell','rubber'):
     lum=max(45,min(225,lum));d=round((lum-190)*.42/5)*5;col=[max(0,min(255,c+d)) for c in col]
    elif role=='accent':
     # Clean source-measured continuous groove; avoid copying source specular pixels
     # or source-side triangle seams into the solar metal.
     px=FRAME[w][4]+(p[2]-FRAME[w][1])/FRAME[w][0];py=FRAME[w][3]-(p[1]-FRAME[w][2])/FRAME[w][0]
     if abs(normal[0])>.35 and 130<px<981 and 185<py<193:col=[53,48,38]
     elif abs(normal[0])>.35 and 173<px<716 and 220<py<226:col=[154,105,58]
    elif role=='black_steel':
     d=max(-17,min(26,round((lum-45)*.4/4)*4));col=[max(0,min(255,c+d)) for c in col]
   else:
    d=max(-18,min(18,round((lum-100)*.22/5)*5));col=[max(0,min(255,c+d)) for c in col]
  return tuple(round(v) for v in col)+(255,)
 faces=[];T=23;size=1024 if w=='sunshot' else 2048
 for e in s.e:
  plane=e['from'][2]==e['to'][2] and len(e.get('faces',{}))==2;polygons=e.pop('_polygons',None);e['faces']={}
  for fn in (['south'] if plane else list(kit.FACE_AXES)):
   _,u,v=kit.face_frame(e,fn);W=max(3,round(math.sqrt(sum(q*q for q in u))*T));H=max(3,round(math.sqrt(sum(q*q for q in v))*T));im=Image.new('RGBA',(W,H));pxs=im.load()
   mask=None
   if polygons:
    hi=Image.new('L',(W*4,H*4));dr=ImageDraw.Draw(hi)
    for poly in polygons:dr.polygon([(x*W*4-.5,y*H*4-.5) for x,y in poly],fill=255)
    mask=hi.resize((W,H),Image.Resampling.BOX).point(lambda a:255 if a else 0).filter(ImageFilter.MaxFilter(3))
   for x in range(W):
    for y in range(H):
     if mask is None or mask.getpixel((x,y)):pxs[x,y]=paint(e,fn,(x+.5)/W,(y+.5)/H)
   if not plane and PALETTE[w][s.roles[e['name']]][0]!='glow':
    dr=ImageDraw.Draw(im);c=PALETTE[w][s.roles[e['name']]][1];dr.line((0,0,W-1,0),fill=tuple(min(255,q+10) for q in c)+(255,))
   faces.append((e,fn,im,plane))
 at=Image.new('RGBA',(size,size));x=y=row=0
 for e,fn,im,plane in sorted(faces,key=lambda f:(-f[2].height,-f[2].width)):
  W,H=im.size
  if x+W+4>size:x=0;y+=row;row=0
  assert y+H+4<=size,(w,'atlas overflow',y,H)
  at.paste(im,(x+2,y+2));at.paste(im.crop((0,0,W,1)),(x+2,y+1));at.paste(im.crop((0,H-1,W,H)),(x+2,y+H+2));at.paste(im.crop((0,0,1,H)),(x+1,y+2));at.paste(im.crop((W-1,0,W,H)),(x+W+2,y+2))
  uv=[16*(x+2)/size,16*(y+2)/size,16*(x+W+2)/size,16*(y+H+2)/size];e['faces'][fn]={'uv':uv,'texture':'#0'}
  if plane:e['faces']['north']={'uv':[uv[2],uv[1],uv[0],uv[3]],'texture':'#0'}
  x+=W+4;row=max(row,H+4)
 parts={k:[e for e in s.e if e['name'].startswith('mag_')==(k=='magazine')] for k in ['body','magazine']}
 d={'texture_size':[size,size],'parts':parts,'no_overlay':True};energy.write(kit.art(w)/'geometry.json',d);energy.write(out/'model.json',d);at.save(kit.atlas_path(w),optimize=True);at.save(out/'atlas.png',optimize=True)
 energy.write(out/'authored_solids.json',{'roles':s.roles,'triangles':s.authored_triangles,'polygons':s.authored_polygons,'optimization':s.optimization,'frame':FRAME[w]})
 energy.write(out/'validation.json',{'revision':2,'total':len(s.e),'parts':{k:len(v) for k,v in parts.items()},'atlas':[size,size],'optimization':s.optimization,'source':str(cache),'nativeQA':'pending master first Vision, delegated review, second Vision','sourceMeshConversion':False})
 # New grips/receiver lengths are intentional; original R1 contacts were tied to slabs.
 energy.CONTACTS.update({
  'sunshot':{'right':([8,6.9,8.0],[-22,0,0]),'left':([7.3,7.0,7.8],[-22,0,-18]),'load':([6.95,9.70,4.35],[0,0,-80]),'pivot':[8,8.2,2.7]},
  'graviton_lance':{'right':([8,8.0,5.6],[-18,0,0]),'left':([8,9.0,-2.4],[-83,0,-20]),'load':([7.4,6.0,10.0],[0,0,-60]),'pivot':[8,8.56,10.6]},
  'jotunn':{'right':([8,6.1,6.6],[-8,0,0]),'left':([6.2,7.2,-.5],[-80,0,-25]),'load':([7.0,13.9,5.0],[0,0,-100]),'pivot':[8,13.5,6.0]}})
 energy.presentation(w)
 print(w,len(s.e),'native elements',{k:len(v) for k,v in parts.items()},flush=True)
 return d
def render(w):
 out=kit.art(w)/'r2';out.mkdir(exist_ok=True)
 renderer=out/'render_native.py';txt=(ROOT/'scripts/art/w325/render_model.py').read_text().replace("'q': (-0.7, 0.45, -0.45)","'q': (-1, .65, -.45)")
 txt=txt.replace("for f, fc in e['faces'].items():","for f, fc in e['faces'].items():\n        if lo[2] == hi[2] and f == 'north': continue  # reverse face is coincident in Blender; native uses backface culling")
 txt=txt.replace("sc.render.engine = 'BLENDER_EEVEE'","sc.render.engine = 'CYCLES'; sc.cycles.samples=16; sc.cycles.use_denoising=True; sc.cycles.transparent_max_bounces=32")
 txt=txt.replace('max(hi[i] - lo[i] for i in range(3)) * 1.1','max(hi[i] - lo[i] for i in range(3)) * 1.15').replace("'rear': (0, -1, 0)","'rear': (0, -1, 0), 'rearq': (-1,-.65,-.45), 'frontq': (1,.65,-.45)");renderer.write_text(txt)
 subprocess.run([kit.BLENDER,'-b','-t','4','--python',str(renderer),'--',str(out/'native'),str(out/'model.json'),str(out/'atlas.png'),'east,q,rearq,frontq,top,front'],check=True)
 board=Image.new('RGB',(2400,1440),(40,43,47));dr=ImageDraw.Draw(board)
 for row,(src,native) in enumerate([('source_side.png','native_east.png'),('source_oblique.png','native_q.png')]):
  board.paste(Image.open(kit.art(w)/src).convert('RGB'),(0,20+row*710));board.paste(Image.open(out/native).convert('RGB'),(1200,20+row*710))
 dr.text((20,3),w+' actual source .blend (source neutral material)',fill='white');dr.text((1220,3),'R2 authored closed solids / actual native JSON + face UV / in-game pending',fill='white');board.save(out/'source_vs_native.png')
if __name__=='__main__':
 cmd=sys.argv[1];ids=sys.argv[2:] or ['sunshot']
 for w in ids:
  if cmd in ['build','all']:bake(w)
  if cmd in ['render','all']:render(w)
