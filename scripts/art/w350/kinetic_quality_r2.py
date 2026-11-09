#!/usr/bin/env python3
"""Authored source-measured closed solids -> accepted W327 native polygon adapter.
No ripped mesh conversion. All counts are emitted elements, not source triangles.
"""
import sys,json,math,copy
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).parent))
import kinetic as old
native=old.module('w350_r2_native','scripts/art/w327/native_contours.py')
closed=old.module('w350_r2_closed','scripts/art/w327/closed_sections.py')
kit=old.kit;A=old.A
FRAME={'crimson':(79,1123,126,20,-10,13.6),'thorn':(79,1123,128,21.5,-10.7,13.6),'outbreak_perfected':(79,1123,216,27.5,-11.5,13.6)}
PAL={
 'crimson':dict(shell=(65,69,69),steel=(108,116,117),trim=(203,209,200),accent=(119,26,29),rubber=(34,38,37),recess=(13,17,18),glow=(190,202,52)),
 'thorn':dict(shell=(47,54,49),steel=(77,86,74),trim=(117,126,107),accent=(138,110,47),rubber=(109,111,95),recess=(13,21,17),glow=(88,221,38)),
 'outbreak_perfected':dict(shell=(35,38,43),steel=(65,74,79),trim=(146,157,159),accent=(148,25,26),rubber=(24,28,30),recess=(10,13,17),glow=(231,49,40))}
class Shape:
 def __init__(self,w):self.w=w;self.solids=[];self.e=[];self.roles={}
 def p(self,px,py,x=0):
  lo,hi,top,L,z0,yt=FRAME[self.w];u=L/(hi-lo)
  return (8+x,yt-(py-top)*u,z0+(px-lo)*u)
 def panel(self,n,pts,w,role='shell',x=0,bevel=.05):
  c=(sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts));fac=max(.94,1-bevel/max(.01,w))
  inset=[(c[0]+(a-c[0])*fac,c[1]+(b-c[1])*fac) for a,b in pts]
  rr=[(-w/2,inset),(-w/2+bevel,pts),(w/2-bevel,pts),(w/2,inset)] if bevel and w>bevel*2 else [(-w/2,pts),(w/2,pts)]
  self.solid(n,[[self.p(a,b,x+xx) for a,b in pp] for xx,pp in rr],role)
 def solid(self,n,rings,role='shell'):self.solids.append(closed.solid_loft(n,rings,role))
 def shell(self,n,stations,role='shell'):
  rings=[]
  for px,top,bottom,w in stations:
   be=min((bottom-top)*.15,5)
   rings.append([self.p(px,top,-w*.30),self.p(px,top,w*.30),self.p(px,top+be,w/2),self.p(px,bottom-be,w/2),self.p(px,bottom,w*.30),self.p(px,bottom,-w*.30),self.p(px,bottom-be,-w/2),self.p(px,top+be,-w/2)])
  self.solid(n,rings,role)
 def tube(self,n,front,back,py,r,role='steel',wall=.16,segments=12):
  verts=[]
  for px,R in [(front,r),(back,r),(front,r-wall),(back,r-wall)]:
   cc=self.p(px,py);verts += [(8+R*math.cos(i*2*math.pi/segments),cc[1]+R*math.sin(i*2*math.pi/segments),cc[2]) for i in range(segments)]
  N=segments;faces=[]
  for i in range(N):
   j=(i+1)%N;faces += [(i,j,N+j,N+i),(2*N+i,3*N+i,3*N+j,2*N+j),(i,2*N+i,2*N+j,j),(N+i,N+j,3*N+j,3*N+i)]
  self.solids.append(dict(name=n,vertices=verts,mesh_faces=faces,role=role))
 def cylinder(self,n,front,back,py,r,role='trim',segments=12,bevel=3):
  rings=[]
  stations=[(front,r*.91),(front+bevel,r),(back-bevel,r),(back,r*.91)] if bevel else [(front,r),(back,r)]
  for px,rr in stations:
   cc=self.p(px,py);rings.append([(8+rr*math.cos(i*2*math.pi/segments),cc[1]+rr*math.sin(i*2*math.pi/segments),cc[2]) for i in range(segments)])
  self.solid(n,rings,role)
 def grip(self,n,stations,role='shell'):
  rings=[]
  for py,front,back,w in stations:
   dz=(back-front)*.17
   rings.append([self.p(front,py),self.p(front+dz,py,w/2),self.p(back-dz,py,w/2),self.p(back,py),self.p(back-dz,py,-w/2),self.p(front+dz,py,-w/2)])
  self.solid(n,rings,role)
 def beam(self,n,a,b,w,t,role='steel',x=0):
  dx,dy=b[0]-a[0],b[1]-a[1];ll=math.hypot(dx,dy);dt=t/FRAME[self.w][3]*(FRAME[self.w][1]-FRAME[self.w][0])/2;nx,ny=-dy/ll*dt,dx/ll*dt
  self.panel(n,[(a[0]+nx,a[1]+ny),(b[0]+nx,b[1]+ny),(b[0]-nx,b[1]-ny),(a[0]-nx,a[1]-ny)],w,role,x,min(.025,w*.1))
 def finish(self):
  raw=native.surfaces(self.solids);groups={};tri=native.tri
  # W327 strategy: only coplanar faces in the same semantic solid/material.
  # This consolidates adjoining loft-ring surfaces without filling their contour.
  for f in raw:
   pp=f['source_points'];normal=tri.unit(tri.cross(f['part']['u'],f['part']['v']))
   if next(v for v in normal if abs(v)>1e-8)<0:normal=tri.mul(normal,-1)
   key=(f['name'].split('/')[0],f['role'],*(round(v,7) for v in normal),round(tri.dot(normal,pp[0]),6))
   groups.setdefault(key,[]).append(f)
  self.surfaces=[]
  for ix,(key,fs) in enumerate(groups.items()):
   pp=[p for f in fs for p in f['source_points']];a,b=max([(p,q) for f in fs for p,q in zip(f['source_points'],f['source_points'][1:]+f['source_points'][:1])],key=lambda pq:math.dist(*pq));u=tri.unit(tri.sub(b,a));normal=tuple(key[2:5]);v=tri.unit(tri.cross(normal,u));coords=[[(tri.dot(tri.sub(p,a),u),tri.dot(tri.sub(p,a),v)) for p in f['source_points']] for f in fs];x0=min(p[0] for q in coords for p in q);x1=max(p[0] for q in coords for p in q);y0=min(p[1] for q in coords for p in q);y1=max(p[1] for q in coords for p in q);ww=x1-x0;hh=y1-y0
   origin=tri.add(a,tri.add(tri.mul(u,x0),tri.mul(v,y0)));part=native.stable(dict(origin=origin,u=u,v=v,width=ww,height=hh,rotation=tri.euler_zyx(u,v,normal)))
   masks=[[( (x-x0)/ww,1-(y-y0)/hh) for x,y in q] for q in coords]
   self.surfaces.append(dict(name=key[0]+'/plane'+str(ix),part=part,triangle=False,polygons=masks,source_points=pp,role=key[1]))
  self.optimization=dict(before=len(raw),after=len(self.surfaces),method='same semantic solid and material coplanar unions; exact polygon masks; no filled rectangles')
  for f in self.surfaces:
   e,error=native.emit_element(f['part'],f['name'],[0,0,16,16],f['triangle']);e['_polygons']=f['polygons'];self.e.append(e);self.roles[e['name']]=f['role']
  return self

def crimson():
 s=Shape('crimson')
 s.shell('barrel_front',[(309,174,288,1.75),(345,173,298,1.88),(470,173,298,1.86),(563,173,296,1.83)],'accent')
 s.shell('barrel_skull_panel',[(563,173,296,1.83),(725,175,296,1.83)])
 s.shell('upper_slide',[(550,160,176,1.18),(625,151,176,1.3),(750,126,176,1.5),(867,126,176,1.48)])
 s.shell('top_rib',[(310,165,175,.95),(556,165,175,.98),(625,154,169,1.05),(751,130,145,1.15),(867,130,145,1.15)],'trim')
 s.tube('muzzle_upper',237,310,194,.55,'steel',.15);s.tube('muzzle_lower',237,310,253,.50,'accent',.16)
 s.panel('front_yoke',[(236,166),(257,167),(271,197),(276,281),(242,289),(233,278)],1.15,'accent')
 s.panel('front_sight',[(242,129),(257,129),(269,156),(276,164),(239,164)],.46,'trim',bevel=.02)
 s.panel('frame_lower',[(685,294),(728,294),(729,220),(739,218),(739,309),(855,309),(880,288),(893,328),(868,339),(770,339),(749,351),(678,350)],1.20)
 s.panel('frame_rear',[(867,145),(921,148),(922,211),(951,253),(1003,255),(1007,287),(964,292),(954,335),(921,350),(886,333),(875,303),(878,193),(868,182)],1.60)
 s.cylinder('mag_cylinder',734,876,239,1.0,'trim',14);s.cylinder('mag_front_band',731,743,239,1.035,'steel',14,0);s.cylinder('mag_rear_band',841,852,239,1.035,'steel',14,0)
 for n,px,py,r,role in [('pivot',914,318,.33,'trim'),('latch',902,261,.16,'steel')]:
  s.panel(n,[(px+math.cos(i*math.pi/6)*r*52.2,py+math.sin(i*math.pi/6)*r*52.2) for i in range(12)],1.73,role,bevel=.025)
 s.panel('hammer',[(927,162),(973,160),(980,138),(992,138),(992,213),(935,214)],.57,'accent',bevel=.02)
 grip=[(957,279),(1000,280),(1009,328),(1034,352),(1072,403),(1122,506),(1042,554),(1009,575),(984,531),(962,488),(935,461),(941,435),(921,382),(902,351),(922,335)]
 s.panel('grip_frame',grip,1.50,'trim',bevel=.07)
 s.panel('grip_stock',[(981,337),(1012,338),(1045,375),(1076,424),(1115,503),(1047,546),(1013,466),(987,414),(947,382),(950,357)],1.57,'rubber',bevel=.04)
 for n,a,b in [('front',(772,339),(768,390)),('floor',(768,390),(793,405)),('bottom',(793,405),(861,405)),('rear',(861,405),(906,386))]:s.beam('guard_'+n,a,b,.38,.22,'accent')
 s.panel('trigger',[(858,341),(873,342),(866,373),(850,393),(844,391),(856,369)],.22,'steel',bevel=.02)
 s.panel('blade',[(79,323),(153,303),(242,300),(311,301),(376,304),(463,304),(463,356),(382,355),(295,355),(153,354),(105,337)],.30,'accent',bevel=.025)
 s.panel('blade_edge',[(79,323),(105,337),(153,354),(382,355),(383,348),(155,347),(111,333)],.33,'steel',bevel=.01)
 s.panel('knife_handle',[(463,305),(560,306),(560,345),(463,345)],.72,'rubber',bevel=.035)
 s.panel('knife_mount',[(560,301),(684,299),(684,345),(560,345)],1.05,'accent')
 s.panel('bayonet_front_post',[(242,276),(270,276),(273,329),(242,329)],.45,'accent',bevel=.025)
 s.panel('rear_sight_bridge',[(879,138),(923,139),(923,153),(879,152)],.75,'accent',bevel=.02)
 s.anchors=[list(s.p(981,415)),list(s.p(901,355)),list(s.p(738,272))]
 return s.finish()

def thorn():
 s=Shape('thorn')
 s.shell('barrel_upper',[(179,168,221,1.20),(300,169,230,1.45),(465,169,239,1.53),(575,165,242,1.72),(717,176,243,1.87)])
 s.shell('barrel_roof',[(176,143,164,.75),(285,165,180,1.13),(467,162,179,1.22),(604,150,174,1.32),(725,157,186,1.4)],'steel')
 s.panel('lower_jaw',[(79,319),(120,306),(157,281),(181,247),(200,221),(241,219),(217,258),(198,297),(270,307),(327,303),(400,306),(471,309),(563,306),(644,316),(685,348),(699,392),(684,440),(665,391),(640,365),(601,348),(470,342),(331,340),(347,326),(191,325)],1.30)
 s.panel('forward_web',[(263,222),(301,230),(327,252),(300,287),(272,308),(225,305),(251,281),(269,250)],1.4,'steel')
 s.panel('middle_web',[(470,234),(530,242),(503,269),(482,298),(446,312),(459,274)],1.48,'steel')
 s.panel('rear_web',[(577,244),(716,273),(717,313),(635,298),(544,294),(532,282)],1.52)
 s.tube('bore',157,244,263,.49,'steel',.16)
 s.panel('muzzle_jaw',[(155,220),(184,215),(184,252),(163,286),(145,293)],1.06,'steel')
 s.panel('dorsal_thorn_long',[(548,128),(599,140),(668,151),(751,160),(853,169),(909,191),(909,202),(748,202),(693,193),(629,172),(585,151)],1.06,'steel',bevel=.025)
 s.panel('dorsal_thorn_mid',[(475,137),(537,146),(598,160),(654,168),(609,173),(538,162)],.69,'steel',bevel=.02)
 s.panel('dorsal_thorn_front',[(410,157),(466,166),(500,177),(458,176),(431,169)],.60,'steel',bevel=.02)
 s.shell('rear_crown',[(719,158,176,1.4),(739,143,178,1.43),(904,149,177,1.39),(916,168,183,1.37)])
 s.panel('chamber_lower_frame',[(717,319),(920,319),(951,338),(939,360),(864,351),(795,359),(756,388),(713,409),(716,359)],1.25)
 s.panel('chamber_rear',[(914,188),(939,206),(968,235),(1008,236),(1031,259),(1012,278),(976,273),(962,298),(946,324),(916,323)],1.63)
 s.cylinder('mag_bone_chamber',753,914,262,1.15,'accent',14);s.cylinder('mag_front_rim',750,769,262,1.18,'steel',14)
 for i in range(4):s.cylinder('mag_cage_band'+str(i),772+i*36,780+i*36,262,1.18,'accent',14,0)
 grip=[(949,270),(1005,278),(1047,340),(1077,379),(1095,429),(1116,483),(1120,543),(1095,562),(1052,588),(967,596),(955,584),(1000,570),(994,535),(978,463),(956,421),(931,391),(920,355)]
 grip_stations=[(278,949,1005,1.23),(337,954,1045,1.48),(388,964,1077,1.55),(447,978,1100,1.45),(502,996,1114,1.34),(546,1003,1117,1.25)]
 s.grip('grip_bone',grip_stations)
 def band_station(y):
  a,b=next((a,b) for a,b in zip(grip_stations,grip_stations[1:]) if a[0]<=y<=b[0]);t=(y-a[0])/(b[0]-a[0]);return (y,a[1]+(b[1]-a[1])*t-2,a[2]+(b[2]-a[2])*t+2,a[3]+(b[3]-a[3])*t+.07)
 for i,y in enumerate([387,415,444,473,502,528]):s.grip('wrap'+str(i),[band_station(y),band_station(y+17)],'rubber')
 s.panel('grip_heel',[(1000,555),(1117,535),(1117,551),(1053,589),(968,596),(955,584)],1.43,'steel',bevel=.025)
 s.panel('guard',[(911,352),(930,359),(934,381),(930,409),(913,431),(885,443),(850,442),(828,434),(827,428),(851,432),(880,432),(903,421),(918,404),(922,380),(918,364)],.36,'steel',bevel=.02)
 s.panel('trigger',[(887,353),(897,357),(891,382),(878,406),(870,416),(866,411),(878,390)],.23,'steel',bevel=.018)
 s.panel('hammer',[(940,213),(955,198),(978,190),(996,191),(993,197),(978,197),(959,219)],.48,'steel',bevel=.02)
 s.panel('sight_bead',[(174,161),(182,161),(182,168),(174,168)],.17,'glow',bevel=0)
 s.anchors=[list(s.p(1037,467)),list(s.p(961,397)),list(s.p(754,295))]
 return s.finish()

def outbreak_perfected():
 s=Shape('outbreak_perfected')
 s.tube('muzzle',79,143,304,.47,'steel',.15);s.tube('muzzle_ring',89,108,304,.54,'shell',.11)
 s.shell('core_barrel',[(143,292,316,.69),(366,292,316,.69),(409,283,324,1.09),(711,282,327,1.14)],'steel')
 for i,x in enumerate([185,241,297,353]):
  for tag,yy in [('upper',268),('lower',340)]:s.panel('small_siva_'+tag+str(i),[(x-26,yy),(x,yy-24),(x+27,yy),(x,yy+24)],1.3,bevel=.04)
 s.beam('lattice_upper_rail',(150,251),(402,251),.43,.17,'steel');s.beam('lattice_lower_rail',(154,356),(402,356),.43,.17,'steel')
 for i,x in enumerate([444,550,656]):
  s.panel('diamond_upper'+str(i),[(x-59,270),(x,216),(x+59,267),(x,315)],2.02,bevel=.075)
  s.panel('diamond_lower'+str(i),[(x-59,335),(x,288),(x+59,340),(x,391)],2.02,bevel=.075)
 s.panel('foregrip_shield',[(185,363),(393,363),(419,389),(402,427),(245,427)],1.12,bevel=.05)
 s.shell('receiver',[(704,283,345,1.5),(786,282,350,1.53),(843,286,354,1.40),(862,309,341,1.13)])
 s.panel('upper_trace_bank',[(675,238),(799,240),(830,268),(865,276),(865,291),(823,284),(790,256),(690,255)],1.33,bevel=.03)
 s.shell('rear_rail',[(829,280,303,.84),(898,278,303,.84)],'steel')
 s.shell('butt_cheek',[(898,248,348,1.64),(912,246,348,1.75),(1069,247,349,1.75)])
 s.panel('butt_contact',[(1067,260),(1122,262),(1119,367),(1104,423),(1028,470),(1009,444),(1044,347),(1068,347)],1.94,'rubber',bevel=.05)
 s.panel('mag_rear',[(934,346),(1044,346),(1015,459),(1018,490),(1006,541),(983,552),(912,537),(903,509),(914,445),(914,409)],1.52,bevel=.055)
 s.panel('mag_feed',[(931,331),(1053,333),(1050,353),(930,353)],1.62,'steel',bevel=.02)
 for i,x in enumerate([939,1050]):s.panel('stock_clamp'+str(i),[(x,276),(x+15,276),(x+15,349),(x,349)],1.84,'steel',bevel=.025)
 s.panel('grip_front',[(671,353),(700,353),(700,412),(687,423),(664,416),(655,375)],1.26,bevel=.04)
 s.panel('trigger_bridge',[(698,347),(788,347),(788,364),(766,380),(705,380),(705,412),(687,412),(687,366)],1.16,bevel=.035)
 s.panel('grip_rear',[(798,347),(828,349),(831,373),(855,412),(882,448),(881,474),(860,524),(827,525),(816,511),(835,462),(823,434),(806,416),(793,378)],1.30,bevel=.04)
 s.panel('grip_floor',[(600,445),(678,470),(775,504),(832,507),(860,493),(873,506),(858,525),(776,526),(594,464)],1.27,bevel=.04)
 for n,a,b in [('front_post',(581,366),(607,450)),('front_mid',(595,405),(659,418)),('front_diag',(607,443),(659,418)),('rear_upper',(805,391),(850,416)),('rear_mid',(817,424),(871,444)),('rear_diag',(838,463),(871,445)),('rear_lower',(837,475),(872,474))]:s.beam(n,a,b,.27,.16,'steel')
 s.panel('trigger',[(749,379),(759,380),(754,398),(745,407),(738,408),(746,394)],.21,'steel',bevel=.015)
 s.panel('sight',[(557,162),(568,162),(568,240),(557,240)],.45,'accent',bevel=.02)
 s.anchors=[list(s.p(829,431)),list(s.p(295,384)),list(s.p(973,360))]
 return s.finish()

BUILDERS={'crimson':crimson,'thorn':thorn,'outbreak_perfected':outbreak_perfected}
def bake(w,s):
 pal=PAL[w];src=Image.open(old.art(w)/'source_material_side.png').convert('RGBA');lum=src.convert('L');blur=lum.filter(ImageFilter.GaussianBlur(2.2))
 def paint(e,fn,u,v):
  role=s.roles[e['name']];col=pal[role];p=kit.face_point(e,fn,u,v);n=kit.rotate_vec(kit.NORMALS[fn],kit.rot_of(e));side=abs(n[0])>.50
  lo,hi,top,L,z0,yt=FRAME[w];px=lo+(p[2]-z0)/L*(hi-lo);py=top+(yt-p[1])/L*(hi-lo);ix,iy=round(px),round(py)
  if side and 0<=ix<src.width and 0<=iy<src.height:
   r,g,b,a=src.getpixel((ix,iy));delta=lum.getpixel((ix,iy))-blur.getpixel((ix,iy))
   if a>240:
    if role not in ('recess','glow','rubber'):
     step=-11 if delta < -17 else -5 if delta < -7 else 8 if delta>18 else 0;col=tuple(max(0,min(255,c+step)) for c in col)
    if w=='crimson':
     if e['name'].startswith('barrel_skull'):
      col=pal['shell']
      # Isolate the seven complete source skull markings; exclude the bracket
      # and cut-off lower paint flakes rather than baking them as broken glyphs.
      glyph=any(abs(px-x)<14 and abs(py-y)<17 for x,y in [(572,217),(611,219),(650,214),(690,220),(572,258),(611,261),(650,262)])
      if glyph and min(r,g,b)>114:col=tuple(max(0,c-7) for c in pal['trim'])
     if e['name'].startswith(('barrel_front','blade')):
      if min(r,g,b)>113 and r<g*1.5:col=pal['trim']
      elif r<67 and g<40:col=(65,20,24)
      elif delta<-10:col=(82,22,26)
      elif r>g*1.45 and r>b*1.25:col=pal['accent']
     if e['name'].startswith('grip_stock') and min(r,g,b)>145:col=pal['trim']
    if w=='thorn' and e['name'].startswith('mag_'):
     if delta<-5 or max(r,g,b)<86:col=(78,65,33)
     elif delta>9:col=(169,140,66)
    if w=='outbreak_perfected':
     if min(r,g,b)>167 and e['name'].startswith(('diamond','upper_trace','mag_','receiver')):col=pal['glow']
     elif e['name'].startswith('diamond') and delta<-6:col=pal['recess']
  return col+(255,)
 faces=[];T=32;SIZE=2048
 for e,f in zip(s.e,s.surfaces):
  polygons=e.pop('_polygons');e.pop('triangle_mask',None);e['faces']={};tt=64 if e['name'].startswith('barrel_skull') else T
  _,u,v=kit.face_frame(e,'south');W=max(2,round(math.sqrt(sum(q*q for q in u))*tt));H=max(2,round(math.sqrt(sum(q*q for q in v))*tt));mask=Image.new('L',(W*4,H*4));d=ImageDraw.Draw(mask)
  if polygons:
   for polygon in polygons:d.polygon([(u*W*4-.5,v*H*4-.5) for u,v in polygon],fill=255)
  elif f['triangle']:d.polygon([(0,0),(0,H*4),(W*4,H*4)],fill=255)
  else:d.rectangle((0,0,W*4,H*4),fill=255)
  mask=mask.resize((W,H),Image.Resampling.BOX).point(lambda a:255 if a else 0);im=Image.new('RGBA',(W,H));pix=im.load()
  for x in range(W):
   for y in range(H):
    if mask.getpixel((x,y)):pix[x,y]=paint(e,'south',(x+.5)/W,(y+.5)/H)
  faces.append((e,im))
 faces.sort(key=lambda f:(-f[1].height,-f[1].width,f[0]['name']));atlas=Image.new('RGBA',(SIZE,SIZE));x=y=row=0
 for e,im in faces:
  W,H=im.size
  if x+W+2>SIZE:x=0;y+=row;row=0
  assert y+H+2<SIZE,(w,y,H)
  atlas.paste(im,(x+1,y+1));atlas.paste(im.crop((0,0,W,1)),(x+1,y));atlas.paste(im.crop((0,H-1,W,H)),(x+1,y+H+1));atlas.paste(im.crop((0,0,1,H)),(x,y+1));atlas.paste(im.crop((W-1,0,W,H)),(x+W+1,y+1))
  uv=[16*(x+1)/SIZE,16*(y+1)/SIZE,16*(x+W+1)/SIZE,16*(y+H+1)/SIZE]
  e['faces']={'south':dict(uv=uv,texture='#0'),'north':dict(uv=[uv[2],uv[1],uv[0],uv[3]],texture='#0')};x+=W+2;row=max(row,H+2)
 H=min(SIZE,1<<math.ceil(math.log2(y+row)))
 if H<SIZE:
  atlas=atlas.crop((0,0,SIZE,H))
  for e in s.e:
   for f in e['faces'].values():f['uv'][1]*=SIZE/H;f['uv'][3]*=SIZE/H
 atlas.save(A/f'textures/item/weapon/w350/{w}.png',optimize=True)
 parts={'body':[e for e in s.e if not e['name'].startswith('mag_')],'magazine':[e for e in s.e if e['name'].startswith('mag_')]};assert len(s.e)<=1000,(w,len(s.e))
 old.emit(old.art(w)/'parts.json',dict(texture_size=[SIZE,H],parts=parts,no_overlay=True))
 old.emit(old.art(w)/'r2-authored-solids.json',dict(revision=2,sourceFrame=FRAME[w],solids=s.solids,solidCount=len(s.solids),emittedElements=len(s.e),anchors=s.anchors,optimization=s.optimization,material=pal,method='Manually authored source measured closed lofts, annular tubes and concave extruded profiles; W327 native_contours; no ripped mesh conversion'))
 return parts,[SIZE,H]

def build(w):
 old.BUILDERS[w]=BUILDERS[w];old.PAL[w]=PAL[w];old.bake=bake;old.build(w)
 d=json.loads((old.art(w)/'design.json').read_text());d['geometry']='R2 semantic closed lofts and physical annular/concave solids. Each native masked polygon belongs to a closed solid, source mesh never converted.';old.emit(old.art(w)/'design.json',d)
 manifest=json.loads((old.art(w)/'manifest.json').read_text());manifest.update(revision=2,solidCount=len(json.loads((old.art(w)/'r2-authored-solids.json').read_text())['solids']),material='Canonical role palette plus bounded actual source albedo panel relief and motifs',generator='scripts/art/w350/kinetic_quality_r2.py');old.emit(old.art(w)/'manifest.json',manifest)
 print('R2 COMPLETE',w,manifest['assembledWeapon'],flush=True)
if __name__=='__main__':
 for w in sys.argv[1:] or old.IDS:build(w)
