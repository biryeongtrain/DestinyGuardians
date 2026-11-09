"""V3 source-led semantic geometry for five owned weapons; never rebuilds the other groups."""
import math,json,sys,importlib.util,hashlib,shutil,contextlib,io
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('old',Path(__file__).with_name('group1.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);k=old.kit
IDS=['igneous_hammer','eyasluna','nation_of_beasts','submission','hung_jury_sr4']
class Model:
 def __init__(self):self.e=[];self.roles={}
 def box(self,n,c,s,mat='shell',rot=None):
  e={'name':n,'from':[c[i]-s[i]/2 for i in range(3)],'to':[c[i]+s[i]/2 for i in range(3)]}
  if rot:e['rotation']={'origin':list(c),**rot}
  self.e.append(e);self.roles[n]=mat;return e
 def section(self,n,c,w,h,L,mat='shell',rx=0):
  b=min(.18,w*.18,h*.24);start=len(self.e)
  self.box(n+'/web',c,[w-2*b,h,L],mat);self.box(n+'/face',c,[w,h-2*b,L],mat)
  for sx in [-1,1]:
   for sy in [-1,1]:self.box(n+f'/corner{sx}{sy}',[c[0]+sx*(w/2-b),c[1]+sy*(h/2-b),c[2]],[b*math.sqrt(2),b*math.sqrt(2),L],mat,{'z':45})
  if rx:
   # Rotate section as one assembly: axisX pitch, local corner bevel converted to native X/Y/Z.
   for e in self.e[start:]:
    p=[(a+b)/2 for a,b in zip(e['from'],e['to'])];q=k.rotate(p,(c,[('x',rx)]));off=[q[i]-p[i] for i in range(3)]
    for t in ['from','to']:e[t]=[e[t][i]+off[i] for i in range(3)]
    if 'rotation' in e:
     # R_x(rx) R_z(45), decomposed ZYX.
     a=math.radians(rx);z=math.pi/4
     yy=math.asin(-math.sin(a)*math.sin(z));xx=math.atan2(math.sin(a)*math.cos(z),math.cos(a));zz=math.atan2(math.cos(a)*math.sin(z),math.cos(z))
     e['rotation']={'origin':q,'x':math.degrees(xx),'y':math.degrees(yy),'z':math.degrees(zz)}
    else:e['rotation']={'origin':q,'x':rx}
 def beam(self,n,p,q,w,h,mat='shell',bevel=False):
  d=[q[i]-p[i] for i in range(3)];L=math.sqrt(sum(t*t for t in d));c=[(p[i]+q[i])/2 for i in range(3)];a=-math.degrees(math.atan2(d[1],d[2]))
  if bevel and abs(d[0])<.001:self.section(n,c,w,h,L,mat,a)
  else:self.box(n,c,[w,h,L],mat,{'x':a,'y':math.degrees(math.atan2(d[0],math.hypot(d[1],d[2])))})
 def ring(self,n,c,r,L,wall=.15,mat='steel',axis='z',N=8):
  for j in range(N):
   a=2*math.pi*j/N;rr=r-wall/2;w=2*rr*math.tan(math.pi/N)+.01
   if axis=='z':p=[c[0]+rr*math.cos(a),c[1]+rr*math.sin(a),c[2]];s=[w,wall,L];rot={'z':math.degrees(a)-90}
   else:p=[c[0],c[1]+rr*math.sin(a),c[2]+rr*math.cos(a)];s=[L,wall,w];rot={'x':90-math.degrees(a)}
   self.box(n+'/'+str(j),p,s,mat,rot)
 def panel(self,n,x,y,z,h,L,mat='steel',depth=.08):
  for side in [-1,1]:self.box(n+str(side),[8+side*x,y,z],[depth,h,L],mat)
 def guard(self,y,z,ry,rz):
  # Actual continuous polygonal guard, with a clear through opening.
  pts=[(8,y+ry*math.sin(a*math.pi/4),z+rz*math.cos(a*math.pi/4)) for a in range(9)]
  for i in range(8):self.beam('guard/'+str(i),pts[i],pts[i+1],.35,.16,'steel')
 def cylinder(self,cy,z0,z1):
  self.ring('mag_cylinder/sleeve',[8,cy,(z0+z1)/2],1.04,z1-z0,.24,'steel')
  self.box('mag_cylinder/core',[8,cy,(z0+z1)/2],[1.15,1.15,z1-z0],'black_steel')
  for z in [z0+.10,z1-.10]:self.ring('mag_cylinder/collar'+str(z),[8,cy,z],1.09,.20,.20,'trim')
  for side in [-1,1]:
   for y in [cy-.5,cy+.5]:self.box('mag_cylinder/flute'+str(side)+str(y),[8+side*.93,y,(z0+z1)/2],[.055,.12,(z1-z0)*.68],'black_steel')
 def pin(self,n,y,z,x=.79):self.panel(n,x,y,z,.15,.15,'trim',.06)

def handcannon(w):
 s=Model();ig=w=='igneous_hammer';nb=w=='nation_of_beasts';cy=12.9 if ig else 12.45
 s.cylinder(cy,2.85,5.85)
 s.section('frame/rear',[8,12.6 if ig else 12.0,6.35],1.36,3.0 if ig else 2.7,.95,'shell' if nb else 'black_steel')
 s.section('frame/under_cylinder',[8,11.44 if ig else 10.93,4.10],1.15,.42,4.6,'steel')
 s.section('frame/top_bridge',[8,13.66 if not ig else 14.12,4.45],.91,.32,3.9,'shell')
 s.beam('hammer/spur',[8,13.30,6.8],[8,13.97,7.46],.42,.34,'steel',True)
 s.beam('grip/core',[8,10.55,6.95],[8,6.75 if not ig else 6.1,8.48],1.37,1.43,'shell' if nb else 'rubber',True)
 s.section('grip/toe',[8,6.65 if not ig else 6.0,8.5],1.48,.42,1.64,'shell' if nb else 'black_steel',-12)
 if not nb:s.guard(10.40 if ig else 10.18,4.83,.95,1.70 if ig else 1.57)
 s.beam('trigger',[8,10.78,5.12],[8,9.85,4.82],.24,.16,'steel')
 for y,z in [(11.4,6.12),(10.85,2.53),(8.75,7.68),(6.95,8.6)]:s.pin('pin/'+str(y),y,z) if not(nb and y==10.85) else None
 s.box('rear_sight/base',[8,14.44 if ig else 13.87,5.9],[.7,.15,.7],'steel')
 for side in [-1,1]:s.box('rear_sight/notch'+str(side),[8+side*.31,14.6 if ig else 14.0,6.0],[.13,.25,.35],'black_steel')
 if w=='eyasluna':
  s.section('barrel/red_shroud',[8,12.88,-1.8],1.78,1.78,8.8,'shell')
  s.ring('barrel/muzzle',[8,12.88,-6.27],.76,.35,.22,'shell')
  s.ring('barrel/bore',[8,12.88,-6.03],.43,.45,.13,'black_steel')
  s.section('barrel/lower_rail',[8,11.75,-1.75],1.27,.40,8.5,'steel')
  s.section('barrel/upper_sightline',[8,13.89,3.40],.63,.23,4.8,'steel')
  for z in [-.55,.25,1.05,1.85]:s.box('rail/lug'+str(z),[8,11.91,z],[1.36,.15,.28],'black_steel')
  s.section('underbarrel/clamp',[8,11.57,-1.15],1.60,.66,.64,'black_steel')
  for i,(x,y,z0,z1,r) in enumerate([(7.64,10.85,-1.7,2.0,.31),(8.43,10.90,-.7,2.5,.27)]):
   s.ring('module/tube'+str(i),[x,y,(z0+z1)/2],r,z1-z0,.13,'steel');s.ring('module/lip'+str(i),[x,y,z0],r+.05,.17,.11,'trim')
  s.beam('module/wire1',[8.7,10.9,2.4],[8.7,10.36,2.8],.11,.11,'black_steel');s.beam('module/wire2',[8.7,10.36,2.8],[8.7,10.4,3.6],.11,.11,'black_steel')
  s.panel('grip/inset',.70,8.5,7.85,1.45,.9,'rubber',.03)
 elif ig:
  s.section('barrel/central',[8,12.47,-1.5],1.7,2.4,8.0,'shell')
  # Paired muzzles and swept crown are the Trials silhouette, distinct from a plain revolver slide.
  for i,(yy,r) in enumerate([(11.77,.48),(13.09,.35)]):s.ring('barrel/muzzle'+str(i),[8,yy,-5.75],r,.65,.15,'steel')
  for j,(z0,z1,y0,y1) in enumerate([(-6,-3.6,13.35,13.7),(-3.6,-.7,13.7,14.1),(-.7,2.3,14.1,14.1),(2.3,5.9,14.1,14.2)]):
   s.beam('crown/spine'+str(j),[8,y0,z0],[8,y1,z1],.9,.25,'trim',True)
  for side in [-1,1]:
   s.beam('wing/forward'+str(side),[8+side*.87,11.35,-5.9],[8+side*.87,12.15,-1.9],.14,.42,'shell',True)
   s.beam('wing/rear'+str(side),[8+side*.87,12.15,-1.9],[8+side*.87,13.72,2.6],.14,.4,'shell',True)
  s.section('frame/trigger_root',[8,10.95,2.65],1.2,1.1,.80,'shell')
  s.section('crown/root',[8,13.67,1.25],1.30,.85,2.7,'shell')
  s.section('underbarrel/chin',[8,11.25,-.65],1.3,.62,6.8,'black_steel')
  # True diagonal fabric strips across a raked continuous grip, rather than horizontal generic ribbing.
  for j in range(5):
   yy=6.5+j*.76;zz=8.35-j*.28
   s.panel('wrap/'+str(j),.73,yy,zz,.24,1.35,'rubber',.07)
 else:
  s.section('ivory/barrel_core',[8,12.75,-1.65],1.61,1.7,8.6,'shell',-4.5)
  s.ring('ivory/muzzle',[8,12.85,-6.03],.46,.40,.12,'shell')
  s.ring('ivory/bore',[8,12.85,-5.92],.30,.45,.10,'black_steel')
  # Broad swept shell with real diagonal lower edge and two carved shoulder ridges.
  for side in [-1,1]:
   s.beam('shell/swept_edge'+str(side),[8+side*.76,11.61,-6.2],[8+side*.76,13.63,2.7],.18,.34,'trim',True)
   s.beam('shell/crown'+str(side),[8+side*.42,13.35,-5.8],[8+side*.42,14.03,2.6],.18,.22,'shell')
  s.beam('shell/rear_horn',[8,13.85,5.7],[8,13.45,7.1],1.55,.3,'shell',True)
  s.beam('grip/outer_carve',[8,10.6,7.4],[8,6.72,8.94],1.51,.22,'trim',True)
  s.section('grip/flared_tip',[8,6.42,8.48],1.65,.28,1.95,'trim',-13)
 return s

def submission():
 s=Model();s.section('front/lower',[8,10.45,-.2],1.8,1.38,4.9,'shell');s.ring('front/muzzle',[8,11.24,-2.85],.62,.4,.15,'steel')
 s.section('front/chin',[8,9.55,-.15],1.55,.44,4.65,'steel');s.section('front/fin_floor',[8,11.34,-.18],1.3,.2,4.2,'black_steel')
 # Alternating folded V fins, each with real depth and gaps, matching Vow's forward mechanism.
 for j in range(8):
  z=-2.05+j*.51
  for side in [-1,1]:s.beam('fins/'+str(j)+str(side),[8,11.52,z-.16],[8+side*.72,12.60,z+.20],.13,.72,'steel')
 s.section('upper/receiver',[8,11.65,5.50],1.85,1.92,7.25,'shell');s.section('upper/rear',[8,11.87,12.75],1.85,1.67,7.25,'steel')
 s.section('upper/spine',[8,12.85,10.2],1.1,.22,11.7,'steel')
 s.panel('lower/glyph_rail',.95,10.57,5.5,.45,7.2,'steel',.10)
 s.panel('rear/window_rim',.97,12.0,13.8,.85,4.7,'black_steel',.07);s.panel('rear/window_inset',1.02,12.0,13.8,.46,4.25,'steel',.05)
 s.section('rear/forward_shoulder',[8,9.65,10.96],1.65,2.72,2.05,'shell')
 s.section('rear/centre_panel',[8,9.18,13.15],1.63,2.1,2.32,'shell')
 s.section('rear/high_panel',[8,10.1,15.15],1.60,1.2,1.63,'shell')
 s.section('rear/low_lobe',[8,7.73,11.15],1.70,1.35,2.15,'shell')
 for side in [-1,1]:s.ring('rear/hinge'+str(side),[8+side*.89,9.0,12.65],.51,.18,.14,'steel','x')
 pts=[[8,6.77,10.2],[8,6.8,12.6],[8,7.36,14.6],[8,8.5,16.2],[8,10.8,17.05]]
 for j in range(len(pts)-1):s.beam('stock/curved_rail'+str(j),pts[j],pts[j+1],.30,.24,'trim')
 s.beam('stock/diagonal_brace',[8,7.06,14.2],[8,8.10,13.1],.23,.19,'black_steel')
 s.section('mag_upper',[8,8.30,7.53],1.22,4.3,1.63,'shell');s.section('mag_heel',[8,6.15,7.53],1.38,.59,1.81,'steel')
 pts=[[8,10.2,6.6],[8,8.66,5.9],[8,7.0,6.05],[8,6.35,7.0]]
 for j in range(3):s.beam('grip/bowed_front'+str(j),pts[j],pts[j+1],.37,.22,'trim')
 s.beam('front/red_rake',[8,11.5,2.3],[8,9.22,3.0],1.85,.30,'accent',True)
 s.beam('trigger/guard',[8,9.72,3.6],[8,9.72,6.55],.25,.17,'steel');s.beam('trigger/blade',[8,10.5,5.97],[8,9.72,5.63],.18,.12,'steel')
 s.box('sight/foot',[8,12.78,3.35],[.8,.25,.6],'steel');s.ring('sight/hoop',[8,13.45,3.55],.68,.13,.09,'trim',N=12)
 for z in [5.0,10.5,14.0]:s.pin('fastener'+str(z),12.83,z,.56)
 return s

def hung_jury():
 s=Model()
 for j,(z0,z1,y,h,w) in enumerate([(-8.2,-4.2,10.03,1.9,1.75),(-4.2,.8,10.06,2.0,1.83),(.8,6.2,10.04,2.05,1.89),(6.2,10.8,10.26,1.6,1.82),(10.8,15.8,10.40,1.38,1.74)]):s.section('receiver/station'+str(j),[8,y,(z0+z1)/2],w,h,z1-z0)
 s.section('stock/butt',[8,9.3,16.1],1.75,3.85,.7,'shell');s.box('stock/pad',[8,9.3,16.51],[1.5,3.6,.15],'rubber')
 # Open rear thumbhole is framed by three connected raked members.
 s.beam('grip/root',[8,9.7,7.2],[8,7.05,8.35],1.28,1.24,'shell',True)
 s.beam('stock/low_rake',[8,7.05,8.35],[8,8.53,12.65],1.34,.70,'shell',True)
 s.beam('stock/rear_rise',[8,8.53,12.65],[8,9.72,14.25],1.34,.72,'shell',True)
 s.section('grip/heel',[8,6.85,8.55],1.55,.45,1.56,'shell',-12)
 s.panel('grip/inset',.70,8.1,7.75,1.5,.58,'rubber',.04)
 # Upper rolled shell and optic/feed recess are independent curved volumes.
 s.ring('upper/front_roll',[8,10.92,-3.15],.45,8.2,.16,'shell')
 s.ring('upper/rear_roll',[8,10.92,11.23],.48,4.2,.17,'shell')
 s.ring('upper/feed_port',[8,10.99,7.8],.52,1.8,.15,'black_steel')
 s.ring('upper/feed_rim',[8,10.99,6.88],.56,.2,.15,'trim')
 s.section('muzzle/slab',[8,10.0,-8.31],1.65,1.85,.27,'shell')
 for yy in [9.57,10.36]:s.ring('muzzle/bore'+str(yy),[8,yy,-8.5],.23,.20,.08,'black_steel')
 s.panel('front/inset',.96,9.48,-3.25,1.08,7.5,'black_steel',.08)
 s.section('mag_tank',[8,7.8,3.56],1.36,3.6,1.60,'black_steel',-8)
 for side in [-1,1]:
  s.ring('fluid/main_rim'+str(side),[8+side*1.04,9.88,3.65],.99,.3,.20,'trim','x',12)
  s.ring('fluid/inner'+str(side),[8+side*1.22,9.88,3.65],.71,.09,.11,'black_steel','x')
  s.box('fluid/core'+str(side),[8+side*1.18,9.88,3.65],[.14,.95,.95],'lens')
  s.box('fluid/secondary_mount'+str(side),[8+side*.70,7.78,4.5],[.45,.70,.65],'black_steel')
  s.ring('fluid/secondary'+str(side),[8+side*.85,7.78,4.66],.60,.27,.15,'trim','x')
  s.box('fluid/secondary_core'+str(side),[8+side*1.0,7.78,4.66],[.10,.61,.61],'lens')
  pts=[[8+side*1.05,9.9,1.95],[8+side*1.20,8.6,2.63],[8+side*1.15,8.48,3.4]]
  for j in range(2):s.beam('fluid/pipe'+str(side)+str(j),pts[j],pts[j+1],.19,.19,'steel')
 s.box('sight/front',[8,11.2,2.2],[.32,.5,.25],'steel')
 for z in [-1.7,-1.2,-.7,-.2,.3,.8]:s.box('top/rail'+str(z),[8,11.15,z],[.65,.16,.22],'steel')
 for y,z in [(9.9,-4.8),(10.5,11.3),(10.0,14.7),(8.6,11.7)]:s.pin('pin'+str(z),y,z,.96)
 return s

def build(w):
 assert w in ("submission","hung_jury_sr4"), "Hand cannons now use the V4 generator; do not overwrite with rejected V3 geometry"
 assert w in IDS
 s=handcannon(w) if w in IDS[:3] else submission() if w=='submission' else hung_jury()
 art=k.art(w);out=art/'v3';out.mkdir(exist_ok=True)
 D=importlib.util.spec_from_file_location('v2_'+w,art/'revisions/v2/design.py');dm=importlib.util.module_from_spec(D);D.loader.exec_module(dm)
 cache=art/'v3/source_bake';man=json.loads((cache/'manifest.json').read_text());views={n:k.View(cache,n,man) for n in man['views']}
 colors={role:tuple(spec['color']) for role,spec in dm.MATERIALS.items()};T=22;A=1024;jobs=[]
 for e in s.e:
  e['faces']={}
  for f in k.FACE_AXES:
   _,u,v=k.face_frame(e,f);ww=max(3,math.ceil(math.sqrt(sum(a*a for a in u))*T));hh=max(3,math.ceil(math.sqrt(sum(a*a for a in v))*T));jobs.append((hh,ww,e,f))
 atlas=Image.new('RGBA',(A,A));x=y=2;row=0
 for h,ww,e,f in sorted(jobs,key=lambda a:-a[0]):
  if x+ww+3>A:x=2;y+=row+3;row=0
  assert y+h+3<A,(w,y,h)
  role=s.roles[e['name']];base=colors[role];name=e['name'];tile=Image.new('RGBA',(ww,h),(*base,255));px=tile.load();normal=k.rotate_vec(k.NORMALS[f],k.rot_of(e))
  p=k.face_point(e,f,.5,.5);a=dm.model2world(name,p);b=dm.model2world(name,[p[i]+normal[i]*.25 for i in range(3)]);wn=[b[i]-a[i] for i in range(3)];axis=max(range(3),key=lambda i:abs(wn[i]));view=views[('p' if wn[axis]>0 else 'n')+'xyz'[axis]]
  for ix in range(ww):
   for iy in range(h):
    p=k.face_point(e,f,(ix+.5)/ww,(iy+.5)/h);wp=dm.model2world(name,p);u,v=view.project(wp);rgb=view.sample(u,v)
    if rgb and role!='lens':
     if w=='eyasluna' and role!='shell' and max(rgb)-min(rgb)>45:rgb=base
     if w=='submission' and (rgb[2]>rgb[0]*1.45 or rgb[1]>rgb[0]*1.45):rgb=base
     if w=='nation_of_beasts':
      # Invalid diagnostic RGB areas are not actual material; preserve ivory engraving only.
      if max(rgb)-min(rgb)<65 and sum(rgb)>220 and role in ('shell','trim'):rgb=tuple(rgb[j]*.75+base[j]*.25 for j in range(3))
      else:rgb=None
     elif w=='hung_jury_sr4':
      # Selected icon is teal/gold; use undyed source as motif/value mask, not white final pigment.
      lum=sum(rgb)/3;fac=.48+.52*min(1,lum/180);rgb=tuple(b*fac for b in base)
     if rgb: px[ix,iy]=tuple(max(0,min(255,int(c*.9+base[j]*.1+4))) for j,c in enumerate(rgb))+(255,)
    if w=='igneous_hammer' and name.startswith('barrel/central') and f in ('east','west'):
     yy,zz=p[1]-12.14,p[2]+.70;rr=math.hypot(yy,zz);aa=math.atan2(yy,zz)
     if .16<rr<.205 or (.24<rr<.43 and math.cos(aa*20)>.40):px[ix,iy]=(221,181,73,255)
  tile=tile.convert('RGB').quantize(colors=24,method=Image.Quantize.MEDIANCUT).convert('RGBA');d=ImageDraw.Draw(tile)
  if min(ww,h)>5:
   d.line((0,0,ww-1,0),fill=tuple(min(255,b+15) for b in base)+(255,))
  if role=='lens':
   d.ellipse((max(0,ww*.1),max(0,h*.1),ww*.9,h*.9),outline=tuple(min(255,b+32) for b in base)+(255,),width=1)
  atlas.paste(tile,(x,y));e['faces'][f]={'uv':[x/64,y/64,(x+ww)/64,(y+h)/64],'texture':'#0'};x+=ww+3;row=max(row,h)
 skin={'texture_size':[A,A],'no_overlay':True,'parts':{'body':[e for e in s.e if not e['name'].startswith('mag_')],'magazine':[e for e in s.e if e['name'].startswith('mag_')]}}
 k.skin_path(w).write_text(json.dumps(skin,separators=(',',':'))+'\n');atlas.save(k.atlas_path(w));k.hud_icon(s.e,k.hud_path(w),lambda n:False)
 (out/'skin.json').write_text(json.dumps(skin,indent=2)+'\n');atlas.save(out/'atlas.png')
 # Store the exact reusable authored design and calibration, independent of old generator mutations.
 calibration=(art/'revisions/v2/design.py').read_text().split('def model2world(name,p):')[1].split('\nWID=')[0]
 (art/'design.py').write_text('"""V3 source-led design; generator scripts/art/w327/group1_v3.py."""\nT=22\nATLAS=1024\nNO_OVERLAY=True\nELEMENTS='+repr([{a:b for a,b in e.items() if a!='faces'} for e in s.e])+'\nROLES='+repr(s.roles)+'\nMATERIALS='+repr(dm.MATERIALS)+'\ndef elements():return ELEMENTS\ndef is_magazine(name):return name.startswith("mag_")\ndef model2world(name,p):'+calibration+'\n')
 m=json.loads((art/'manifest.json').read_text());m.update(revision=3,atlas=[A,A],texels_per_px=T,element_total=len(s.e),elements={p:len(es) for p,es in skin['parts'].items()},hidden_faces=0,generator='scripts/art/w327/group1_v3.py',native_acceptance='pending master Vision',material_finish='source-calibrated face motifs with selected official finish; diagnostic shader pixels excluded')
 for p in [k.skin_path(w),k.atlas_path(w),k.hud_path(w)]:m['outputs_sha256'][str(p.relative_to(ROOT))]=k.sha(p)
 assert m['source_blend_sha256']==k.sha(k.blend_of(w))
 (art/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 text=io.StringIO()
 with contextlib.redirect_stdout(text):k.adscheck(w)
 report={'revision':3,'total':len(s.e),'elements':m['elements'],'uv_in_range':all(0<=q<=16 for e in s.e for f in e['faces'].values() for q in f['uv']),'source_sha_unchanged':True,'atlas':[A,A],'ads_profile':text.getvalue(),'native_qa':'pending master'}
 (art/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(w,len(s.e),'elements',y+row,'atlas rows',flush=True)

if __name__=='__main__':
 for wid in ('submission','hung_jury_sr4') if len(sys.argv)<2 else sys.argv[1:]:build(wid)
