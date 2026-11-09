"""Source-led semantic reconstruction. V3 hero, separate from frozen V2 generator."""
import sys, math, json, importlib.util
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
ROOT=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('kit',ROOT/'scripts/art/w325/kit.py'); k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k)
OUT=Path(__file__).parent/'v3';OUT.mkdir(exist_ok=True)
E=[];R={}
COLORS={'alloy':(54,64,60),'edge':(101,105,77),'barrel':(154,181,183),'clamp':(127,116,85),'dark':(37,48,45),'pipe':(142,159,158),'leaf':(104,110,43),'leafdark':(73,88,38),'leaflight':(139,137,57),'grip':(64,77,66),'cell':(151,174,135),'lens':(100,195,179)}
def box(n,c,s,mat='alloy',rotation=None):
 e={'name':n,'from':[round(c[i]-s[i]/2,5) for i in range(3)],'to':[round(c[i]+s[i]/2,5) for i in range(3)]}
 if rotation:e['rotation']={'origin':list(c),**rotation}
 E.append(e);R[n]=mat;return e
def beam(n,p,q,w,h,mat='alloy'):
 c=[(p[i]+q[i])/2 for i in range(3)];d=[q[i]-p[i] for i in range(3)];L=math.sqrt(sum(v*v for v in d))
 # longitudinal local Z, pitch in YZ; supports source frame and routed pipes.
 return box(n,c,[w,h,L],mat,{'x':-math.degrees(math.atan2(d[1],d[2])),'y':math.degrees(math.atan2(d[0],math.hypot(d[1],d[2])))})
def ring(n,c,r,l,wall=.15,mat='alloy',axis='z',sectors=8):
 for j in range(sectors):
  a=2*math.pi*j/sectors;rr=r-wall/2;w=2*rr*math.tan(math.pi/sectors)+.015
  if axis=='z':cc=[c[0]+rr*math.cos(a),c[1]+rr*math.sin(a),c[2]];s=[w,wall,l];rot={'z':math.degrees(a)-90}
  elif axis=='x':cc=[c[0],c[1]+rr*math.sin(a),c[2]+rr*math.cos(a)];s=[l,wall,w];rot={'x':90-math.degrees(a)}
  else:cc=[c[0]+rr*math.cos(a),c[1],c[2]+rr*math.sin(a)];s=[w,l,wall];rot={'y':90-math.degrees(a)}
  box(n+f'/{j}',cc,s,mat,rot)
def section(n,c,w,h,l,mat='alloy',angle=0):
 # Central web, two broad flat faces and four genuine chamfer edges.
 b=min(.16,w*.18,h*.18)
 for suffix,off,s in [('web',(0,0,0),(w-2*b,h,l)),('face',(0,0,0),(w,h-2*b,l))]:
  box(n+'/'+suffix,[c[i]+off[i] for i in range(3)],s,mat,{'x':angle} if angle else None)
 for sx in [-1,1]:
  for sy in [-1,1]:
   # Rotate full local section around its centre so diagonal members stay connected.
   off=[sx*(w/2-b),sy*(h/2-b),0];a=math.radians(angle);cc=[c[0]+off[0],c[1]+off[1]*math.cos(a),c[2]+off[1]*math.sin(a)]
   # bevel rotation about Z then pitch requires local transformed corners; leave corner on straight sections only.
   if not angle:box(n+f'/bevel{sx}{sy}',cc,[b*math.sqrt(2),b*math.sqrt(2),l],mat,{'z':45})
def framebeam(n,p,q,w,h,mat='alloy'):
 d=[q[i]-p[i] for i in range(3)];L=math.hypot(d[1],d[2]);a=-math.degrees(math.atan2(d[1],d[2]));c=[(p[i]+q[i])/2 for i in range(3)]
 section(n,c,w,h,L,mat,a)
def pipe(n,pts,width=.13):
 for j,(p,q) in enumerate(zip(pts,pts[1:])):beam(n+f'/segment{j}',p,q,width,width,'pipe')
def leaf(n,c,length,width,rx,rz,shade):
 # Three contiguous tapered leaf sections; twists are real organic leaf orientation.
 # Apply all local offsets through same transform, avoiding detached square pads.
 rot=(c,[('x',rx),('z',rz)])
 for j,(pos,ww,ll) in enumerate([(-.40,width*.32,.20),(-.20,width*.77,.20),(0,width,.20),(.20,width*.67,.20),(.40,width*.24,.20)]):
  cc=k.rotate((c[0],c[1],c[2]+pos*length),rot)
  box(n+f'/lobe{j}',cc,[ww,.055,ll*length],shade,{'x':rx,'z':rz})

def geometry():
 # Source lower barrel rail and raised receiver transition.
 section('lower/barrel_rail',[8,9.55,2.05],1.22,.73,8.9)
 section('lower/receiver_step',[8,10.02,8.6],1.44,1.12,4.6)
 section('lower/stock_shoulder',[8,10.28,11.7],1.25,.85,2.6)
 # Dominant hollow cylindrical chambers, with visible seam gaps and narrow collars.
 for name,z0,z1,r in [('muzzle',-2.3,-.35,1.03),('front_chamber',-.18,4.90,1.13),('front_band',4.90,5.34,1.20),('rear_chamber',8.85,12.45,1.06)]:
  ring('chamber/'+name,[8,11.55,(z0+z1)/2],r,z1-z0,.21,'barrel')
 ring('muzzle/lip',[8,11.55,-2.38],1.04,.22,.16,'edge')
 ring('muzzle/inner_bore',[8,11.55,-1.88],.50,.65,.13,'dark')
 ring('front/neck',[8,11.55,5.67],.79,.7,.17,'dark')
 ring('rear/neck',[8,11.55,8.36],.73,.55,.16,'dark')
 # Exposed central spine between the two chambers is substantially narrower.
 section('spine/bridge',[8,11.32,7.15],.72,.68,2.7,'dark')
 box('spine/top_rail',[8,12.36,7.2],[.64,.2,3.3],'edge')
 for i in range(7):box('rail/tooth'+str(i),[8,12.51,5.9+i*.40],[.75,.13,.16],'alloy')
 # Chamber bolted saddles and raised locking straps are structural, not texture lines.
 for j,z in enumerate([-.22,2.05,4.8,9.0,12.25]):
  for side in [-1,1]:box(f'saddle/{j}/{side}',[8+side*.94,11.5,z],[.18,1.06,.26],'clamp')
 # The side energy cell has an octagonal collar, deep well and inset luminous face.
 for side in [-1,1]:
  ring(f'cell/{side}/rim',[8+side*.89,9.35,5.05],1.03,.25,.19,'edge','x')
  ring(f'cell/{side}/inner',[8+side*1.03,9.35,5.05],.76,.10,.11,'dark','x')
  box(f'cell/{side}/core_mid',[8+side*1.0,9.35,5.05],[.14,.70,1.29],'cell')
  for dy in [-.48,.48]:box(f'cell/{side}/core_edge{dy}',[8+side*1.0,9.35+dy,5.05],[.14,.27,.84],'cell')
 # Actual vertical cylinder links cell to the forebrace.
 ring('cell/strut',[8,8.34,4.5],.31,3.6,.11,'alloy','y')
 ring('cell/strut_top',[8,9.87,4.5],.40,.42,.12,'edge','y')
 ring('cell/strut_foot',[8,6.62,4.5],.40,.42,.12,'edge','y')
 framebeam('frame/forebrace',[8,10.22,-.85],[8,6.35,4.10],.88,.66)
 section('frame/brace_foot',[8,6.44,4.17],.93,.7,.65)
 # Connected rear rake, round upper stock strut and thin tall buttplate.
 framebeam('frame/rear_rake',[8,10.78,12.28],[8,7.10,16.43],1.06,.78)
 ring('stock/upper_strut',[8,10.25,14.6],.29,3.65,.12,'edge')
 section('stock/butt',[8,10.1,16.83],1.18,6.3,.60)
 box('stock/butt_pad',[8,10.1,17.18],[1.04,5.83,.12],'grip')
 # Long narrow source magazine extends from the integral grip frame, not arbitrary giant cuboid.
 section('grip/housing',[8,8.45,8.65],1.20,4.60,1.30,'alloy')
 section('grip/heel',[8,6.18,8.65],1.34,.45,1.48,'edge')
 section('mag_insert',[8,4.70,8.70],.66,3.40,.94,'dark')
 section('mag_floor',[8,3.03,8.70],.76,.19,1.05,'edge')
 box('trigger/tang',[8,9.22,7.53],[.22,.68,.18],'dark',{'x':-19})
 # True open hood at source forward sight station.
 box('sight/foot',[8,12.6,3.2],[.73,.26,1.08],'dark')
 ring('sight/hood',[8,13.45,3.23],.91,.94,.14,'alloy',sectors=12)
 box('sight/notch',[8,12.78,3.52],[.14,.16,.08],'lens')
 # Visible pipe network follows the original shoulder routing, with discrete couplers.
 for side in [-1,1]:
  xx=8+side*1.06
  pipe(f'pipe/{side}/long',[(xx,10.94,-1.60),(xx,10.85,.3),(xx,10.92,3.0),(xx,11.1,5.65),(xx,10.96,7.6),(xx,11.0,10.25)])
  pipe(f'pipe/{side}/cell',[(xx,10.53,6.12),(xx,10.21,6.25),(xx,10.15,5.86),(xx,10.13,5.38)])
  pipe(f'pipe/{side}/upper',[(8+side*.72,12.03,5.45),(8+side*.72,12.14,7.0),(8+side*.72,12.0,8.7)])
  for j,z in enumerate([-1.6,5.5,10.1]):box(f'pipe/{side}/coupler{j}',[xx,10.99,z],[.24,.24,.34],'edge')
  for j,(y,z) in enumerate([(10.1,10.2),(10.0,7.3),(9.55,2.8),(6.22,9.1)]):box(f'pin/{side}/{j}',[8+side*.75,y,z],[.12,.19,.19],'edge')
 # Three growth origins, varied leaves draping over chamber shoulders/front; never aligned top pads.
 clusters=[(-1.05,0),(4.65,1),(11.65,2)]
 for zz,j in clusters:
  for i,(x,y,z,l,w,rx,rz) in enumerate([(7.45,12.55,zz,1.8,.65,12,-22),(8.5,12.6,zz+.2,1.9,.76,-10,22),(6.99,12.05,zz-.1,2.05,.74,82,-8),(9.04,12.00,zz+.35,2.0,.66,74,8),(7.8,12.72,zz-.65,1.8,.68,-23,8)]):
   leaf(f'leaf/{j}/{i}',[x,y,z],l*1.35,w*1.55,rx+(j-1)*7,rz+(i%2)*9,['leaf','leafdark','leaflight'][(i+j)%3])
geometry()
# Align semantic stations to the source's orthographic landmarks, keeping lower anchors.
for e in E:
 n=e['name'];dy=0;dz=0
 if n.startswith(('chamber/','muzzle/','front/','rear/','spine/','rail/','saddle/','leaf/','pipe/')):dy=.65
 if n.startswith('lower/barrel'):dy=1.08
 elif n.startswith(('lower/receiver','lower/stock')):dy=.74
 elif n.startswith('stock/upper'):dy=.5
 elif n.startswith('pin/') and e['from'][1]>8:dy=1.0
 elif n.startswith('cell/') and not n.startswith('cell/strut'):dy=1.4;dz=-.55
 for a in ['from','to']:
  e[a][1]+=dy;e[a][2]+=dz
 if 'rotation' in e:e['rotation']['origin'][1]+=dy;e['rotation']['origin'][2]+=dz
CACHE=Path('/tmp/w327-v3-cache/subjunctive');MAN=json.loads((CACHE/'manifest.json').read_text());VIEWS={n:k.View(CACHE,n,MAN) for n in MAN['views']}
def world(p):return ((8-p[0])/34,(p[2]-8.26)/33.92,(p[1]-8.4)/28)
def painted(e,f,w,h):
 mat=R[e['name']];base=COLORS[mat];name=e['name'];tile=Image.new('RGBA',(w,h),(*base,255));pix=tile.load()
 normal=k.rotate_vec(k.NORMALS[f],k.rot_of(e));wn=(-normal[0]/34,normal[2]/33.92,normal[1]/28);axis=max(range(3),key=lambda a:abs(wn[a]));view=VIEWS[('p' if wn[axis]>0 else 'n')+'xyz'[axis]]
 # Source colour defines corrosion and panel boundaries. Deep occluded leaf projections are excluded.
 for ix in range(w):
  for iy in range(h):
   p=k.face_point(e,f,(ix+.5)/w,(iy+.5)/h);wp=world(p);u,v=view.project(wp);src=view.sample(u,v);depth=view.depth_at(u,v)
   good=src and depth is not None and abs(depth-sum(wp[a]*view.d[a] for a in range(3)))<.035
   if good and mat not in ('leaf','leafdark','leaflight','pipe','lens'):
    # Keep source hue/surface wear, gently lift for Minecraft diffuse presentation.
    rgb=tuple(max(0,min(255,int(a*.84+b*.16+6))) for a,b in zip(src,base))
    if mat=='barrel' and src[1]>src[2]*1.28:rgb=base
    pix[ix,iy]=(*rgb,255)
 # Deliberately discrete palette; do not bake smooth gradients onto every face.
 tile=tile.convert('RGB').quantize(colors=18,method=Image.Quantize.MEDIANCUT).convert('RGBA');d=ImageDraw.Draw(tile)
 if mat.startswith('leaf'):
  # Veins follow each authored lobe and remain legible at close range.
  mid=w//2;dark=tuple(max(0,c-24) for c in base)+(255,);light=tuple(min(255,c+22) for c in base)+(255,)
  d.line((mid,0,mid,h-1),fill=light,width=1)
  for yy in range(3,h-2,5):
   d.line((mid,yy,1,max(0,yy-4)),fill=dark);d.line((mid,yy,w-2,max(0,yy-4)),fill=dark)
 elif mat=='pipe':
  # Narrow continuous cool metal line, not an all-around airbrush edge.
  if w>h:d.line((0,h//3,w-1,h//3),fill=(183,199,196,255))
  else:d.line((w//3,0,w//3,h-1),fill=(183,199,196,255))
 if min(w,h)>5 and not mat.startswith('leaf'):
  # One physical edge line; source faces retain their material rather than uniform bevel gradients.
  d.line((0,0,w-1,0),fill=tuple(min(255,a+15) for a in base)+(255,))
 return tile

def bake():
 atlas=Image.new('RGBA',(1024,1024),(0,0,0,0));x=y=2;row=0;jobs=[]
 for e in E:
  e['faces']={}
  for f in k.FACE_AXES:
   _,u,v=k.face_frame(e,f);w=max(3,math.ceil(math.sqrt(sum(a*a for a in u))*22));h=max(3,math.ceil(math.sqrt(sum(a*a for a in v))*22))
   jobs.append((h,w,e,f))
 for h,w,e,f in sorted(jobs,key=lambda a:-a[0]):
   mat=R[e['name']];color=COLORS[mat]
   if x+w+3>1024:x=2;y+=row+3;row=0
   assert y+h+3<1024,(y,h)
   tile=painted(e,f,w,h)
   atlas.paste(tile,(x,y));e['faces'][f]={'uv':[x/64,y/64,(x+w)/64,(y+h)/64],'texture':'#0'};x+=w+3;row=max(row,h)
 skin={'texture_size':[1024,1024],'no_overlay':True,'parts':{'body':[e for e in E if not e['name'].startswith('mag_')],'magazine':[e for e in E if e['name'].startswith('mag_')]}}
 (OUT/'hero.json').write_text(json.dumps(skin,indent=2));atlas.save(OUT/'hero.png');(OUT/'roles.json').write_text(json.dumps(R,indent=2))
 print(len(E),'elements',y+row,'atlas rows')
if __name__=='__main__':bake()
