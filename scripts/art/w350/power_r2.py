#!/usr/bin/env python3
"""Source-proportioned W350 R2 authored closed solids; native polygon adapter.
Source meshes are evidence only. All lofts/outlines here are authored.
"""
import sys,math,json,copy,subprocess,hashlib,importlib.util
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[3]
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=module('power_base',ROOT/'scripts/art/w350/power.py')
g=module('accepted_g3',ROOT/'scripts/art/w327/group3_v3.py')
opt=module('accepted_opt',ROOT/'scripts/art/w327/group3_optimize.py')
A=p.A;ART=p.ART
FRAMES={'gjallarhorn':(29.75,78,1120,297,11.4),'whisper_of_the_worm':(33.6,78,1120,350,10.7),'tractor_cannon':(21.9,78,1120,350,10.0)}
class Shape(g.SourceShape):
 def __init__(self,w):
  super().__init__('krait');self.w=w;self.L,self.p0,self.p1,self.py,self.ym=FRAMES[w];self.u=self.L/(self.p1-self.p0);self.z0={'gjallarhorn':-10.5,'whisper_of_the_worm':-15.2,'tractor_cannon':-8.9}[w]
 def point(self,x,px,py):return (8+x,self.ym+(self.py-py)*self.u,self.z0+(px-self.p0)*self.u)
 def cyl(self,n,stations,m='shell',N=12,wall=None):
  rings=[]
  for px,py,r in stations:
   rings.append([self.point(r*math.sin(i*math.tau/N),px,py-r*math.cos(i*math.tau/N)/self.u) for i in range(N)])
  if wall is None:self.loft(n,rings,m)
  else:
   inner=[]
   for px,py,r in stations:inner.append([self.point((r-wall)*math.sin(i*math.tau/N),px,py-(r-wall)*math.cos(i*math.tau/N)/self.u) for i in range(N)])
   # Closed annular wall: outer, inner and both annular caps, central bore remains real.
   for k in range(len(rings)-1):
    for j in range(N):
     q=(j+1)%N
     for tag,R in [('out',rings),('in',inner)]:
      a,b=R[k],R[k+1];self.triangle(f'{n}_{tag}_{k}_{j}a',a[j],a[q],b[q],m);self.triangle(f'{n}_{tag}_{k}_{j}b',a[j],b[q],b[j],m)
   for k in [0,len(rings)-1]:
    for j in range(N):
     q=(j+1)%N;a,b=rings[k],inner[k];self.triangle(f'{n}_rim{k}_{j}a',a[j],a[q],b[q],m);self.triangle(f'{n}_rim{k}_{j}b',a[j],b[q],b[j],m)
 def relief(self,n,points,x,depth,m='gold'):
  # Authored closed profiled relief on each side, rather than texture-only silhouette.
  start=len(self.e);startt=len(self.authored_triangles);self.panel(n,points,depth,m)
  for e in self.e[start:]:
   e['from'][0]+=x;e['to'][0]+=x
   if 'rotation' in e:e['rotation']['origin'][0]+=x
  for t in self.authored_triangles[startt:]:t['vertices']=[(a+x,b,c) for a,b,c in t['vertices']]

def gjallarhorn():
 s=Shape('gjallarhorn')
 s.cyl('forward_ivory',[(80,297,1.17),(92,297,1.23),(340,297,1.23),(386,297,1.28)],'ivory',12,.26)
 s.cyl('muzzle_gold',[(78,297,1.27),(88,297,1.27),(94,297,1.19)],'gold',12,.28)
 s.cyl('chamber_rear',[(344,298,1.20),(382,298,1.34),(498,298,1.34)],'steel',12)
 s.cyl('aft_ivory',[(500,297,.97),(584,297,.94),(598,297,.89),(1012,297,.87),(1076,297,.81)],'ivory',12,.19)
 s.cyl('rear_gold_cap',[(1074,297,.85),(1081,297,.85)],'gold',12,.20)
 for i in range(10):
  a=i*math.tau/10;b=(i+1)*math.tau/10
  s.beamp('rear_loop'+str(i),(1098+20*math.cos(a),297+17*math.sin(a)),(1098+20*math.cos(b),297+17*math.sin(b)),.38,.19,'gold')
 for i,x in enumerate([506,538,570]):s.cyl('gold_binding'+str(i),[(x,297,1.08),(x+11,297,1.08)],'gold',12,.21)
 # Source cover crown changes height and width; top plateau descends into hinge.
 s.shell('cover_crown',[(155,226,253,1.7,.55),(180,192,253,2.0,.68),(230,178,253,2.22,.70),(300,170,253,2.3,.75),(450,172,253,2.3,.75),(499,196,253,2.18,.65),(560,228,253,1.88,.65),(588,240,253,1.65,.55)],'gold')
 # Side scope housing is visibly proud of the crown and barrel; source asymmetry retained.
 s.relief('scope_side',[(388,216),(456,214),(470,225),(470,279),(457,293),(398,293),(385,280)],-1.40,.72,'ivory')
 # Wolf head with separate muzzle, brow, ear and interlocking mane tiers.
 wolf=[(153,236),(163,226),(166,208),(178,199),(196,195),(210,181),(229,179),(234,187),(255,183),(279,176),(299,173),(319,169),(327,179),(314,193),(297,202),(292,212),(280,218),(272,228),(253,233),(245,245),(225,248),(219,241),(207,248),(194,246),(187,251),(177,243),(164,243)]
 for sd in [-1,1]:
  s.relief('cover_wolf_head'+str(sd),wolf,sd*1.12,.23,'gold')
  s.relief('cover_wolf_muzzle'+str(sd),[(153,236),(169,222),(184,221),(194,230),(183,240),(167,244)],sd*1.27,.12,'trim')
  s.relief('cover_wolf_brow'+str(sd),[(172,207),(183,203),(199,208),(198,212),(181,211)],sd*1.28,.10,'trim')
  s.relief('cover_wolf_eye'+str(sd),[(174,209),(183,209),(181,212),(174,212)],sd*1.35,.025,'dark')
 # Lower rail/stock are a multi-part structural frame around two true voids.
 for sd in [-1,1]:
  s.beamp('chamber_lower_rail'+str(sd),(351,331),(458,331),.16,.13,'gold',sd*1.28)
  s.beamp('chamber_upper_rail'+str(sd),(346,269),(384,269),.16,.12,'gold',sd*1.28)
 s.panel('fore_cradle',[(177,346),(345,346),(345,357),(388,357),(388,418),(291,418),(255,403),(215,403)],1.40,'ivory')
 s.panel('stock_upper',[(389,353),(492,353),(511,342),(590,351),(711,351),(723,362),(723,389),(710,399),(689,399),(689,375),(505,375),(473,391),(389,391)],1.25,'ivory')
 s.panel('stock_rear',[(687,373),(723,373),(723,391),(711,406),(568,483),(510,483),(504,469),(556,464)],1.27,'ivory')
 s.panel('rear_grip',[(476,389),(500,389),(509,400),(507,418),(526,442),(539,468),(513,473),(503,452),(492,434),(470,417)],.94,'rubber')
 s.beamp('trigger_guard_front',(395,389),(398,415),.25,.19,'gold');s.beamp('trigger_guard_floor',(398,415),(446,420),.25,.20,'gold');s.beamp('trigger',(446,390),(441,411),.18,.18,'dark')
 s.beamp('front_grip',(275,414),(161,523),.72,.72,'rubber');s.cyl('front_grip_pivot',[(269,414,.30),(282,414,.30)],'gold',8)
 s.panel('rear_fin_top',[(1015,266),(1077,248),(1080,266)],.29,'gold');s.panel('rear_fin_bottom',[(1015,325),(1080,325),(1080,342),(1053,339)],.29,'gold')
 # Lateral scope apertures have real ring geometry and recessed dark glass.
 for j,py in enumerate([237,271]):
  rings=[]
  for xx,rr in [(-1.80,.28),(-1.67,.28),(-1.67,.17),(-1.80,.17)]:
   rings.append([s.point(xx,394+rr*math.cos(k*math.tau/8)/s.u,py+rr*math.sin(k*math.tau/8)/s.u) for k in range(8)])
  # Annular rectangular cross section in an X-oriented plane.
  for k in range(4):
   a,b=rings[k],rings[(k+1)%4]
   for i in range(8):
    q=(i+1)%8;s.triangle(f'scope_aperture{j}_{k}_{i}a',a[i],a[q],b[q],'gold');s.triangle(f'scope_aperture{j}_{k}_{i}b',a[i],b[q],b[i],'gold')
 s.cyl('mag_rocket',[(350,297,.78),(475,297,.78),(489,297,.48)],'steel',8)
 return s

def whisper_of_the_worm():
 s=Shape('whisper_of_the_worm')
 # Long mechanical barrel and Taken four-jaw skull, authored from source silhouette.
 s.cyl('barrel',[(150,336,.43),(536,336,.43),(632,336,.60)],'steel',10,.14)
 s.cyl('muzzle_throat',[(84,338,.40),(115,338,.61),(191,338,.53),(225,338,.44)],'bone',10,.20)
 s.shell('receiver',[(555,325,360,1.34,.55),(620,317,375,1.7,.60),(690,312,385,1.8,.7),(791,314,387,1.85,.7),(852,326,382,1.66,.55)],'shell')
 s.panel('lower_receiver',[(615,355),(713,350),(794,365),(793,405),(755,405),(755,382),(688,378)],1.57,'bone')
 s.panel('stock_upper',[(846,328),(918,318),(988,307),(1093,314),(1086,336),(1003,335),(964,347),(852,350)],1.42,'shell')
 s.panel('stock_butt',[(1067,333),(1095,321),(1093,412),(1081,424),(1061,419)],1.62,'bone')
 s.panel('stock_bottom',[(938,404),(960,407),(1070,382),(1070,414),(944,434),(936,426)],1.22,'shell')
 s.panel('stock_grip_bridge',[(849,347),(934,347),(945,374),(930,387),(914,378),(849,374)],1.25,'shell')
 s.panel('pistol_grip',[(913,367),(931,372),(939,397),(959,413),(946,431),(937,428),(928,400),(915,391)],1.02,'bone')
 s.beamp('trigger_guard',(876,380),(874,401),.20,.18,'bone');s.beamp('trigger_floor',(874,401),(914,397),.20,.18,'bone');s.beamp('trigger',(897,377),(889,391),.16,.15,'dark')
 s.panel('mag_shell',[(787,385),(859,385),(869,437),(870,450),(836,460),(797,457)],1.38,'shell')
 s.panel('mag_floor',[(796,451),(870,445),(872,455),(839,464),(795,461)],1.54,'bone')
 s.boxp('scope_mount',(763,304),(886,318),.74,'dark',.08)
 s.cyl('scope_objective',[(725,280,.90),(732,280,.90),(775,280,.82),(814,280,.58)],'shell',12,.18)
 s.cyl('scope_tube',[(813,280,.58),(884,280,.58),(936,280,.55)],'bone',10,.16)
 s.cyl('scope_ocular',[(936,280,.62),(948,280,.62),(956,280,.57)],'shell',10,.17)
 s.boxp('scope_turret',(840,251),(864,271),.62,'steel',.07)
 # Bone jaw silhouettes contain real negative gaps around the barrel.
 for sd in [-1,1]:
  s.relief('skull_upper'+str(sd),[(81,323),(89,303),(95,317),(111,320),(128,314),(152,319),(174,313),(186,323),(178,332),(154,333),(140,341),(121,338),(109,345),(91,339)],sd*.42,.26,'bone')
  s.relief('skull_lower'+str(sd),[(82,352),(99,348),(117,356),(134,351),(153,356),(168,353),(159,366),(139,369),(118,365),(102,373),(88,376)],sd*.42,.26,'bone')
  # Only deep, source-evidenced spines are geometry. Thin Taken ribbons become UV.
  for j,(px,py,tipx,tipy) in enumerate([(139,320,211,292),(168,324,259,294),(194,329,285,317),(206,350,278,377),(155,361,227,397),(181,361,258,405),(245,330,309,307),(286,345,345,370)]):
   s.relief('jaw_spine'+str(sd)+'_'+str(j),[(px,py),(px+20,py+3),(tipx,tipy)],sd*(.50+j*.02),.14,'bone')
  for j,(px,py,tx,ty) in enumerate([(604,351,662,392),(650,357,714,401),(704,355,750,395),(949,325,1012,297),(984,323,1050,304)]):
   s.relief('receiver_spine'+str(sd)+'_'+str(j),[(px,py),(px+27,py+10),(tx,ty)],sd*.83,.18,'bone')
  for j,(px,py,tx,ty) in enumerate([(759,255,779,244),(783,257,802,243),(807,257,826,245),(884,262,898,249),(906,263,920,249)]):s.relief('scope_spine'+str(sd)+'_'+str(j),[(px,py),(px+6,py+5),(tx,ty)],sd*.52,.10,'bone')
 return s

def tractor_cannon():
 s=Shape('tractor_cannon')
 def drum(n,stations,m='shell',wall=None):
  # Longitudinal elliptical cross sections, preserving measured transverse width.
  N=12;rings=[]
  for px,py,rx,ry in stations:rings.append([s.point(rx*math.sin(k*math.tau/N),px,py-ry*math.cos(k*math.tau/N)/s.u) for k in range(N)])
  if wall is None:s.loft(n,rings,m)
  else:
   inn=[]
   for px,py,rx,ry in stations:inn.append([s.point((rx-wall)*math.sin(k*math.tau/N),px,py-(ry-wall)*math.cos(k*math.tau/N)/s.u) for k in range(N)])
   for k in range(len(rings)-1):
    for R,tag in [(rings,'o'),(inn,'i')]:
     a,b=R[k],R[k+1]
     for j in range(N):
      q=(j+1)%N;s.triangle(f'{n}_{tag}_{k}_{j}a',a[j],a[q],b[q],m);s.triangle(f'{n}_{tag}_{k}_{j}b',a[j],b[q],b[j],m)
   for k in [0,len(rings)-1]:
    a,b=rings[k],inn[k]
    for j in range(N):
     q=(j+1)%N;s.triangle(f'{n}_rim{k}_{j}a',a[j],a[q],b[q],m);s.triangle(f'{n}_rim{k}_{j}b',a[j],b[q],b[j],m)
 drum('main_white',[(376,350,3.5,3.1),(422,350,4.1,3.55),(575,350,4.1,3.72),(650,350,3.6,3.60),(682,350,3.0,3.0)],'shell')
 drum('front_steel',[(153,350,2.25,2.5),(275,350,2.8,2.8),(353,350,3.0,3.0)],'steel',.32)
 drum('main_collar',[(350,350,3.23,3.23),(362,350,3.23,3.23),(376,350,3.15,3.15)],'dark',.35)
 drum('collar_rim',[(359,350,3.30,3.30),(367,350,3.30,3.30)],'silver',.26)
 drum('emitter_inset',[(142,350,1.9,2.13),(206,350,1.9,2.13)],'dark',.30)
 drum('emitter_back',[(207,350,1.6,1.7),(218,350,1.6,1.7)],'steel')
 # Rear grip housings form two large open handle frames around the central gap.
 s.panel('upper_handle',[(661,155),(803,143),(927,137),(1069,135),(1082,147),(1081,219),(1118,257),(1120,323),(994,324),(992,258),(948,198),(813,216),(735,245),(684,254)],2.7,'shell')
 s.panel('lower_handle',[(728,429),(807,430),(837,439),(1004,431),(1016,442),(1015,497),(700,551),(692,534),(723,507),(742,474)],2.40,'shell')
 s.panel('rear_recess',[(735,256),(810,235),(900,207),(947,202),(948,232),(925,255),(857,282),(810,315),(731,329)],1.55,'dark')
 # Upper arch is load-bearing; broad side insert is a dark material field.
 for sd in [-1,1]:
  s.relief('upper_handle_insert'+str(sd),[(708,176),(813,156),(952,145),(990,151),(990,181),(943,194),(814,212),(737,237)],sd*1.36,.08,'steel')
  s.relief('lower_handle_insert'+str(sd),[(745,439),(815,446),(1003,441),(1004,481),(749,522),(733,506)],sd*1.22,.07,'steel')
 # Three closed swept claws distributed radially, not side alpha blades.
 for j,a in enumerate([0,120,240]):
  aa=math.radians(a);rings=[]
  for px,rad,w,t in [(288,2.8,.76,.25),(234,3.5,1.20,.28),(161,4.55,1.27,.22),(108,4.75,.34,.15),(102,4.70,.06,.08)]:
   ring=[]
   for u,v in [(-w/2,-t/2),(w/2,-t/2),(w/2,t/2),(-w/2,t/2)]:
    xx=(rad+v)*math.sin(aa)+u*math.cos(aa);yy=(rad+v)*math.cos(aa)-u*math.sin(aa);ring.append(s.point(xx,px,350-yy/s.u))
   rings.append(ring)
  s.loft('claw'+str(j),rings,'shell')
  # Talon fork piston, structural rod and hinge are real side-depth parts.
  cx=2.45*math.sin(aa);cy=350-2.45*math.cos(aa)/s.u
  s.beamp('claw_piston'+str(j),(292,cy),(175,cy),.26,.26,'silver',cx)
 # Side loader collar and prominent recoil pivot.
 for sd in [-1,1]:
  s.relief('loader_pivot'+str(sd),[(615,446),(635,426),(670,414),(701,430),(726,460),(718,496),(686,523),(648,516),(618,492)],sd*2.85,.30,'steel')
  s.relief('body_vertical_panel'+str(sd),[(445,264),(460,264),(460,388),(448,398)],sd*4.08,.07,'silver')
 # Twin diagonal exhaust pipes; circles are perpendicular to the authored axis.
 for sd in [-1,1]:
  rings=[];xx=sd*1.90
  path=[(472,210,.60),(491,188,.64),(552,143,.64),(598,108,.63),(610,103,.63)]
  inn=[]
  for k,(px,py,r) in enumerate(path):
   a=path[max(0,k-1)];b=path[min(len(path)-1,k+1)];dy,dz=(a[1]-b[1]),(b[0]-a[0]);L=math.hypot(dy,dz);vy,vz=dz/L,-dy/L
   def rr(rad):
    out=[]
    for i in range(8):
     co=math.cos(i*math.tau/8)*rad;si=math.sin(i*math.tau/8)*rad
     out.append(s.point(xx+co,px+vz*si/s.u,py-vy*si/s.u))
    return out
   rings.append(rr(r));inn.append(rr(r-.15))
  for R,tag in [(rings,'o'),(inn,'i')]:
   for k,(a,b) in enumerate(zip(R,R[1:])):
    for j in range(8):
     q=(j+1)%8;s.triangle(f'exhaust{sd}_{tag}_{k}_{j}a',a[j],a[q],b[q],'steel');s.triangle(f'exhaust{sd}_{tag}_{k}_{j}b',a[j],b[q],b[j],'steel')
  for k in [0,len(rings)-1]:
   a,b=rings[k],inn[k]
   for j in range(8):
    q=(j+1)%8;s.triangle(f'exhaust{sd}_rim{k}_{j}a',a[j],a[q],b[q],'silver');s.triangle(f'exhaust{sd}_rim{k}_{j}b',a[j],b[q],b[j],'silver')
 s.panel('mag_cell',[(579,156),(663,156),(667,216),(590,215)],2.45,'dark')
 s.boxp('mag_top',(580,150),(663,158),2.58,'yellow',.08)
 return s

def bake(w,s):
 # New source-derived contacts; explicit arm geometry remains an approximation.
 refs={'gjallarhorn':{'right':(500,427),'left':(225,460),'loading':(420,297),'moving_pivot':(588,250)},'whisper_of_the_worm':{'right':(931,394),'left':(651,374),'loading':(830,409),'moving_pivot':(827,386)},'tractor_cannon':{'right':(854,190),'left':(520,514),'loading':(622,184),'moving_pivot':(622,216)}}[w]
 for key,xy in refs.items():p.CONFIG[w][key]=list(s.point(0,*xy))
 p.CONFIG[w]['pivot']=p.CONFIG[w]['right']
 s=opt.optimize(s);assert len(s.e)<=1000,(w,len(s.e));out=ART/w/'r2';out.mkdir(exist_ok=True)
 p.write(out/'geometry.json',{'elements':s.e,'roles':s.roles,'authored_triangles':s.authored_triangles,'authored_polygons':s.authored_polygons,'optimization':s.optimization})
 source=Image.open(ART/w/'source_side.png').convert('RGB');lum=source.convert('L');blur=lum.filter(ImageFilter.GaussianBlur(2));pal=p.PALETTES[w];faces=[];T=22;SZ=2048
 def color(e,fn,u,v):
  role=s.roles[e['name']];c=pal[role];pt=p.kit.face_point(e,fn,u,v);px=s.p0+(pt[2]-s.z0)/s.u;py=s.py-(pt[1]-s.ym)/s.u;n=e['name'];normal=p.kit.rotate_vec(p.kit.NORMALS[fn],p.kit.rot_of(e));side=abs(normal[0])>.42
  if side and 0<=px<source.width and 0<=py<source.height and role not in ['dark','rubber'] and w!='whisper_of_the_worm':
   ix,iy=int(px),int(py);delta=lum.getpixel((ix,iy))-blur.getpixel((ix,iy));shift=-18 if delta<-13 else -9 if delta<-5 else 9 if delta>8 else 0;c=tuple(max(0,min(255,x+shift)) for x in c)
  if side and role=='rubber' and int((pt[1]+pt[2]*.2)*20)%7==0:c=tuple(max(0,x-9) for x in c)
  if w=='gjallarhorn' and side:
   if n.startswith('aft_ivory') and (abs(py-272)<1.0 or abs(py-322)<1.0):c=pal['gold']
   if n.startswith('cover_crown') and py>242:c=pal['trim']
   if n.startswith('forward_ivory'):
    if abs(py-265)<1 or abs(py-328)<1:c=pal['gold']
    if (99<px<150 and abs(py-(271-.13*(px-100)))<3) or (99<px<150 and abs(py-(325+.13*(px-100)))<3):c=pal['steel']
    if (278<px<304 and 272<py<279) or (278<px<304 and 317<py<325):c=pal['trim']
   if n.startswith('cover_wolf_head'):
    # Clean source-anchored shallow mane engraving; no coplanar tier overlap.
    fur=[[(199,210),(213,201),(234,197),(248,191)],[(198,221),(213,216),(225,207),(252,203),(269,194)],[(205,234),(223,225),(243,222),(256,212),(279,207)],[(222,243),(237,234),(254,231),(266,222)],[(243,245),(259,238),(269,228)]]
    for path in fur:
     for (ax,ay),(bx,by) in zip(path,path[1:]):
      vx,vy=bx-ax,by-ay;t=max(0,min(1,((px-ax)*vx+(py-ay)*vy)/(vx*vx+vy*vy)));dist=math.hypot(px-ax-t*vx,py-ay-t*vy)
      if dist<.85:c=(131,99,40)
      elif dist<1.45:c=(217,176,82)
   if n.startswith('scope_side'):
    if abs(py-221)<.9 or abs(py-286)<.9:c=pal['gold']
    if 435<px<461 and (abs(py-233)<.9 or abs(py-242)<.9 or abs(py-251)<.9):c=pal['steel']
  if w=='whisper_of_the_worm' and side:
   # Authored bounded Taken fissures, tied to body panels; no opaque source FX-card shadows.
   if n.startswith(('receiver','stock','mag_')):
    paths=[[(581,341),(638,337),(663,346),(703,339),(748,350),(785,347)],[(618,366),(664,357),(706,373),(751,365)],[(856,335),(901,328),(948,328),(983,317),(1038,320)],[(800,394),(818,417),(814,450)],[(845,395),(850,430),(840,451)]]
    for path in paths:
     for (ax,ay),(bx,by) in zip(path,path[1:]):
      vx,vy=bx-ax,by-ay;t=max(0,min(1,((px-ax)*vx+(py-ay)*vy)/(vx*vx+vy*vy)));dist=math.hypot(px-ax-t*vx,py-ay-t*vy)
      if dist<.65:c=(167,191,185)
      elif dist<1.2:c=(74,101,97)
   if n.startswith('skull_') and 103<px<179 and abs(py-(329+.16*(px-103)))<1:c=(150,173,167)
  if w=='tractor_cannon' and side:
   if n.startswith('main_white'):
    # Evidenced inset slots, restrained blue material panels and selected source seam paths.
    if 478<px<622 and 319<py<373:
     if abs(py-321)<1.1 or abs(py-371)<1.1 or abs(px-480)<1.0:c=pal['trim']
    if 491<px<527 and 331<py<355:c=pal['yellow']
    if 535<px<606 and 336<py<351:
     if abs(py-338)<1 or abs(py-347)<1:c=pal['steel']
    if 465<px<613 and abs(py-(465+.13*(px-465)))<1.1:c=pal['trim']
   if n.startswith('upper_handle_insert'):
    if 769<px<808 and 174<py<189:c=pal['dark']
    if abs(py-(218-.16*(px-720)))<.8:c=pal['silver']
   if n.startswith('lower_handle_insert') and 774<px<905 and abs(py-(502-.17*(px-774)))<.9:c=pal['silver']
  return c+(255,)
 for e in s.e:
  plane=e['from'][2]==e['to'][2] and len(e.get('faces',{}))==2;polys=e.pop('_polygons',None);e['faces']={}
  for fn in ['south'] if plane else p.kit.FACE_AXES:
   _,u,v=p.kit.face_frame(e,fn);W=max(2,round(math.sqrt(sum(x*x for x in u))*T));H=max(2,round(math.sqrt(sum(x*x for x in v))*T));im=Image.new('RGBA',(W,H));mask=None
   if polys:
    mask=Image.new('L',(W*4,H*4));d=ImageDraw.Draw(mask)
    for poly in polys:d.polygon([(u*W*4-.5,v*H*4-.5) for u,v in poly],fill=255)
    mask=mask.resize((W,H),Image.Resampling.BOX).point(lambda a:255 if a else 0)
   q=im.load()
   for x in range(W):
    for y in range(H):q[x,y]=color(e,fn,(x+.5)/W,(y+.5)/H) if mask is None or mask.getpixel((x,y)) else (0,0,0,0)
   faces.append((e,fn,im,plane))
 faces.sort(key=lambda f:(-f[2].height,-f[2].width,f[0]['name'],f[1]));at=Image.new('RGBA',(SZ,SZ));x=y=row=0
 for e,fn,im,plane in faces:
  W,H=im.size
  if x+W+2>SZ:x=0;y+=row;row=0
  assert y+H+2<=SZ,(w,y,H)
  at.paste(im,(x+1,y+1));at.paste(im.crop((0,0,W,1)),(x+1,y));at.paste(im.crop((0,H-1,W,H)),(x+1,y+H+1));at.paste(im.crop((0,0,1,H)),(x,y+1));at.paste(im.crop((W-1,0,W,H)),(x+W+1,y+1))
  uv=[16*(x+1)/SZ,16*(y+1)/SZ,16*(x+W+1)/SZ,16*(y+H+1)/SZ];e['faces'][fn]={'uv':uv,'texture':'#0'}
  if plane:e['faces']['north']={'uv':[uv[2],uv[1],uv[0],uv[3]],'texture':'#0'}
  x+=W+2;row=max(row,H+2)
 H=min(SZ,2**math.ceil(math.log2(y+row)));at=at.crop((0,0,SZ,H))
 for e in s.e:
  for f in e['faces'].values():f['uv'][1]*=SZ/H;f['uv'][3]*=SZ/H
 parts={}
 for e in s.e:
  part='cover' if e['name'].startswith('cover_') else 'magazine' if e['name'].startswith('mag_') else 'body';parts.setdefault(part,[]).append(e)
 skin={'texture_size':[SZ,H],'parts':parts,'no_overlay':True};p.write(ART/w/'skin.json',skin);at.save(A/f'textures/item/weapon/w350/{w}.png',optimize=True)
 p.write(out/'optimization.json',s.optimization);p.native(w,skin)
 p.write(ART/w/'design.json',{'revision':2,'generator':'scripts/art/w350/power_r2.py','sourceFrame':FRAMES[w],'elements':s.e,'roles':s.roles,'authoredClosedSurfaceTriangles':s.authored_triangles,'optimization':s.optimization})
 manifest=json.loads((ART/w/'manifest.json').read_text());manifest.update(revision=2,partElements={k:len(v) for k,v in parts.items()},weaponElements=len(s.e),firstPersonElementsMaximum=len(s.e)+224,atlas=[SZ,H],generator='scripts/art/w350/power_r2.py',nativeAcceptance='pending master first/second Vision');p.write(ART/w/'manifest.json',manifest)
 # Exact emitted native elements are what the offline renderer reads.
 native=json.loads((A/f'models/weapon_w350/{w}/full.json').read_text());p.write(out/'native-render-input.json',{'texture_size':skin['texture_size'],'parts':{'body':native['elements']}})
 print(w,'emitted',len(s.e),{k:len(v) for k,v in parts.items()},'atlas',skin['texture_size'],flush=True)
 return s

def check(w):
 skin=json.loads((ART/w/'skin.json').read_text());es=sum(skin['parts'].values(),[])
 assert 0<len(es)<=1000 and len({e['name'] for e in es})==len(es)
 planes=0
 for e in es:
  assert all(-16<=v<=32 for v in e['from']+e['to']),(e['name'],e['from'],e['to'])
  assert all(a<=b for a,b in zip(e['from'],e['to']))
  zero=[i for i,(a,b) in enumerate(zip(e['from'],e['to'])) if a==b]
  if zero:assert zero==[2] and set(e['faces'])=={'south','north'};planes+=1
  else:assert set(e['faces'])==set(p.kit.FACE_AXES)
  for f in e['faces'].values():assert len(f['uv'])==4 and all(0<=x<=16 for x in f['uv'])
 assert Image.open(A/f'textures/item/weapon/w350/{w}.png').size==tuple(skin['texture_size'])
 poses=json.loads((ART/w/'reload-poses.json').read_text())['poses'];assert len(poses)==61
 for i,x in enumerate(poses):assert x['frame']==i and x['progress']==i/60
 for i in [0,60]:assert poses[i]['bodyRotation']==[0,0,0] and poses[i]['magazineOffset']==[0,0,0]
 missing=[];seen=set()
 def graph(q):
  if isinstance(q,dict):
   if q.get('type')=='minecraft:model' and q.get('model','').startswith('destiny:'):
    f=A/'models'/(q['model'].split(':',1)[1]+'.json')
    if not f.exists():missing.append(str(f))
    seen.add(q['model'])
   for v in q.values():graph(v)
  elif isinstance(q,list):
   for v in q:graph(v)
 for f in [A/f'items/weapon/{w}.json',A/f'items/weapon_reload_w350/{w}.json',A/f'items/weapon_aim_w350/{w}.json']:graph(json.loads(f.read_text()))
 assert not missing,missing
 arms=[k for k in seen if '/hands/' in k];assert len(arms)>0 and all(k.startswith('destiny:weapon_w350/'+w+'/hands/') for k in arms)
 aim=json.loads((A/f'items/weapon_aim_w350/{w}.json').read_text());assert len(aim['model']['cases'][0]['model']['entries'])==21
 ev=json.loads((ART/w/'source-evaluation.json').read_text());assert p.sha(ev['blend'])==ev['sha256']
 full=json.loads((A/f'models/weapon_w350/{w}/full.json').read_text())['elements'];assert len(full)==sum(len(v) for k,v in skin['parts'].items() if not(w=='gjallarhorn' and k=='magazine'))
 report={'revision':2,'jsonAndUV':'PASS','emittedWeaponElements':len(es),'partElements':{k:len(v) for k,v in skin['parts'].items()},'nativeMaskedPolygonPlanes':planes,'firstPersonWithClassicForearmsMaximum':len(es)+224,'atlas':skin['texture_size'],'reloadSamples':61,'aimSamples':21,'endpointRest':'PASS','graphReferences':'PASS','ownedW204HandPrefix':'destiny:weapon_w350/'+w+'/hands/','referencedHandVariants':len(arms),'sourceOriginalUnchanged':True,'sourceActions':ev['actions'],'animation':'Authored approximation, no source actions or player hand rig','nativePackLoad':'MASTER_PENDING','firstSecondVision':'MASTER_PENDING','performance':'NOT_MEASURED','audio':'NOT_OWNED'}
 p.write(ART/w/'validation.json',report);p.write(ART/w/'r2/validation.json',report)
 print('CHECK',w,len(es),planes,'planes',len(arms),'hand variants',flush=True)

def render(w):
 out=ART/w/'r2';renderer=out/'render_native.py';text=(ROOT/'scripts/art/w325/render_model.py').read_text().replace("'q': (-0.7, 0.45, -0.45)","'q': (-1, .65, -.45), 'otherq': (1, .65, -.45)")
 # Source uses ext*1.15; exact corresponding source/model handedness camera.
 text=text.replace('* 1.1','* 1.15');renderer.write_text(text)
 subprocess.run([p.BLENDER,'-b','--python',str(renderer),'--',str(out/'native'),str(out/'native-render-input.json'),str(A/f'textures/item/weapon/w350/{w}.png'),'east,q,otherq,front'],check=True)
 board=Image.new('RGB',(2400,1460),(28,33,39));d=ImageDraw.Draw(board)
 for col in range(2):
  d.text((col*1200+16,12),['Readonly source .blend (Workbench silhouette)','R2 actual native item JSON / offline only'][col],fill='white')
  for row,view in enumerate(['side','oblique']):
   f=ART/w/f'source_{view}.png' if col==0 else out/('native_'+('east' if row==0 else 'q')+'.png');board.paste(Image.open(f).convert('RGB'),(col*1200,40+row*710))
 board.save(out/'source-vs-native.png')
if __name__=='__main__':
 cmd=sys.argv[1];ws=sys.argv[2:] or ['gjallarhorn']
 for w in ws:
  if cmd=='build':bake(w,globals()[w]())
  elif cmd=='render':render(w)
  elif cmd=='check':check(w)
