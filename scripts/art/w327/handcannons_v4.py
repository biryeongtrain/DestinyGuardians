"""V4 geometry-first proof, authored semantic solids in source metres.
Run headless Blender with the read-only rip loaded. No native production asset is overwritten.
No source vertices, polygons or connected components are copied into the proposal.
Contour stations below are authored from matched orthographic source views.
"""
import bpy,math,mathutils,json,sys
from pathlib import Path
from mathutils import Vector
wid=sys.argv[sys.argv.index('--')+1];ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'art/weapons/w327'/wid/'v4';OUT.mkdir(exist_ok=True)
source=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('Plane')]
meta=json.loads((OUT/'source_parts.json').read_text());lo,hi=meta['lo'],meta['hi'];center=Vector([(a+b)/2 for a,b in zip(lo,hi)]);scale=1400/((hi[1]-lo[1])*1.2)
proposal=[];records=[]
mat=bpy.data.materials.new('V4_uniform_neutral');mat.diffuse_color=(.45,.48,.50,1)
def yz(px,py):return ((px-700)/scale+center.y,(450-py)/scale+center.z)
def mesh(name,verts,faces):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('V4/'+name,me);bpy.context.scene.collection.objects.link(o);o.data.materials.append(mat);proposal.append(o)
 records.append({'name':name,'vertices':[list(v) for v in verts],'faces':[list(f) for f in faces]});return o
def outline(name,pts,halfwidth=.015):
 # Closed thick contour solid, not alpha side sheets. Caps retain the authored silhouette.
 vv=[(x,*yz(px,py)) for x in [-halfwidth,halfwidth] for px,py in pts];n=len(pts)
 return mesh(name,vv,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)])
def loft(name,sections):
 # Cross sections have matching authored perimeter stations; join into a watertight solid.
 n=len(sections[0]);vv=[p for row in sections for p in row];ff=[tuple(range(n-1,-1,-1)),tuple(range((len(sections)-1)*n,len(sections)*n))]
 for j in range(len(sections)-1):
  for i in range(n):ff.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 return mesh(name,vv,ff)
def grip(name,rows):
 sections=[]
 for py,front,back,hw in rows:
  ya,zz=yz(front,py);yb,_=yz(back,py);b=(yb-ya)*.18;xb=hw*.25
  sections.append([(-hw+xb,ya,zz),(hw-xb,ya,zz),(hw,ya+b,zz),(hw,yb-b,zz),(hw-xb,yb,zz),(-hw+xb,yb,zz),(-hw,yb-b,zz),(-hw,ya+b,zz)])
 return loft(name,sections)
def tube(name,px0,px1,py,radius,x=0,wall=.002,N=16,flutes=False):
 y0,z=yz(px0,py);y1,_=yz(px1,py);rows=[]
 if wall>=radius*.9:
  for yy in [y0,y1]:
   rows.append([(x+(radius-(.0045*(.5+.5*math.cos(a*6)) if flutes else 0))*math.cos(a),yy,z+(radius-(.0045*(.5+.5*math.cos(a*6)) if flutes else 0))*math.sin(a)) for a in [2*math.pi*i/N for i in range(N)]])
  return loft(name,rows)
 # Full mechanical cylinder with a real bore and front/rear lips.
 for yy,rr in [(y0,radius),(y1,radius),(y1,radius-wall),(y0,radius-wall)]:
  rows.append([(x+(rr-(.0045*(.5+.5*math.cos(a*6)) if flutes else 0))*math.cos(a),yy,z+(rr-(.0045*(.5+.5*math.cos(a*6)) if flutes else 0))*math.sin(a)) for a in [2*math.pi*i/N for i in range(N)]])
 vv=[p for row in rows for p in row];ff=[]
 for j in range(4):
  for i in range(N):ff.append((j*N+i,j*N+(i+1)%N,((j+1)%4)*N+(i+1)%N,((j+1)%4)*N+i))
 return mesh(name,vv,ff)
def swept(name,points,depth=.008,width=.0025,N=8):
 rows=[]
 for j,(px,py) in enumerate(points):
  y,z=yz(px,py);pa=points[max(0,j-1)];pb=points[min(len(points)-1,j+1)];dy=pb[0]-pa[0];dz=-(pb[1]-pa[1]);ll=math.hypot(dy,dz);ny,nz=-dz/ll,dy/ll
  rows.append([(depth*math.cos(a),y+ny*width*math.sin(a),z+nz*width*math.sin(a)) for a in [2*math.pi*i/N for i in range(N)]])
 return loft(name,rows)
def box(name,xh,xa,ya,xb,yb):return outline(name,[(xa,ya),(xb,ya),(xb,yb),(xa,yb)],xh)
def barrel(name,p0,p1,cross,bore):
 # Machined muzzle profile is genuinely wider at the lower shoulder.
 y0,_=yz(p0,0);y1,_=yz(p1,0)
 rows=[[(xx*.94,y0,yz(0,288+(py-288)*.94)[1]) for xx,py in cross],[(xx,y0+8/scale,yz(0,py)[1]) for xx,py in cross],[(xx,y1,yz(0,py)[1]) for xx,py in cross]]
 o=loft(name,rows)
 # Authored bore subtraction makes the visual mesh a closed hollow solid.
 py,r=bore;yy,zz=yz(p0,py);length=abs(y1-y0)+.002
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=length,location=(0,yy+length*.5-.001,zz),rotation=(math.pi/2,0,0));cut=bpy.context.object
 mod=o.modifiers.new('real muzzle bore','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
 # The source muzzle has a recessed beveled lip, visible even directly down the bore.
 bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=r,radius2=r+.0018,depth=.004,location=(0,yy+.0015,zz),rotation=(math.pi/2,0,0));cut=bpy.context.object
 mod=o.modifiers.new('muzzle recessed lip','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
 return o
def eyasluna():
 # Screen contour stations map exactly through one source-world calibration; no per-part fit.
 cross=[(-.0085,225),(.0085,225),(.0118,232),(.0172,270),(.0258,301),(.0263,328),(.019,347),(-.019,347),(-.0263,328),(-.0258,301),(-.0172,270),(-.0118,232)]
 barrel('barrel/shaped_shroud',116,782,cross,(288,.0120))
 outline('barrel/rear_raised_shoulder',[(620,226),(632,213),(656,213),(660,233),(747,233),(761,225),(784,225),(784,256),(752,256),(742,247),(637,247)],.0125)
 # Original cylinder is tightly nestled between front spigot, topstrap, lower frame and breech dome.
 tube('mag_cylinder/drum',783,988,325,.0292,wall=.0285,N=24,flutes=True)
 tube('mag_cylinder/front_rim',780,794,325,.0290,wall=.003,N=16)
 tube('mag_cylinder/rear_rim',977,992,325,.0300,wall=.003,N=16)
 tube('barrel/cylinder_spigot',757,781,322,.0132,wall=.006,N=12)
 outline('frame/topstrap',[(655,213),(820,213),(823,219),(907,219),(916,211),(1008,211),(1015,218),(1015,238),(996,245),(786,246),(786,231),(663,231)],.0107)
 outline('frame/lower_rail',[(754,408),(983,408),(985,377),(995,386),(998,420),(754,420)],.015)
 outline('frame/trigger_web',[(754,422),(994,422),(1001,439),(970,445),(882,446),(841,456),(806,472),(768,478),(768,448),(689,448),(689,422)],.008)
 outline('frame/front_module_root',[(686,447),(770,447),(770,475),(686,475)],.010)
 # Dome/breech is a sequence of true elliptical sections rather than a square vertical block.
 rows=[]
 for px,rx,rz in [(984,.0255,.029),(999,.023,.028),(1011,.018,.025),(1022,.010,.020)]:
  y,z=yz(px,326);rows.append([(rx*math.cos(a),y,z+rz*math.sin(a)) for a in [2*math.pi*i/16 for i in range(16)]])
 loft('frame/breech_dome',rows)
 outline('frame/beavertail',[(1006,242),(1018,258),(1033,276),(1069,298),(1104,312),(1158,312),(1182,320),(1182,332),(1160,341),(1142,360),(1093,386),(1057,413),(1025,432),(1005,411)],.014)
 # Raked grip curves through several measured silhouette stations, with a rounded lower toe.
 rows=[(346,1137,1158,.010),(379,1088,1164,.014),(418,1025,1179,.0175),(458,1014,1200,.020),(502,1042,1232,.021),(545,1078,1259,.0215),(588,1101,1276,.021),(628,1110,1281,.020),(666,1110,1248,.019),(702,1110,1224,.0175),(720,1120,1189,.015),(728,1134,1167,.010)]
 grip('grip/frame',[(py,f,b,hw*.84) for py,f,b,hw in rows])
 grip('grip/inset',[(372,1126,1148,.010),(396,1082,1159,.016),(425,1055,1164,.022),(451,1059,1185,.022),(474,1062,1200,.020),(503,1063,1215,.019),(547,1096,1241,.0196),(589,1118,1257,.0191),(630,1129,1261,.0183),(669,1135,1234,.0174),(696,1142,1204,.0157),(704,1162,1179,.012)])
 swept('guard/asymmetric_loop',[(817,464),(815,495),(826,517),(850,537),(880,552),(912,561),(945,560),(975,548),(1002,527),(1023,500),(1045,505)],.008,.0028,N=8)
 outline('trigger/curved_blade',[(925,449),(956,448),(974,458),(964,477),(957,502),(942,528),(925,544),(921,544),(934,518),(942,489),(938,468)],.0033)
 outline('hammer/curved_spur',[(1013,246),(1026,258),(1050,266),(1071,261),(1103,237),(1110,232),(1122,249),(1119,259),(1092,277),(1078,296),(1064,299),(1034,282)],.0085)
 # Lower ventilated rail: actual slot openings, continuous lower flange and local bridges.
 cross=[(-.019,373),(-.018,386),(-.012,400),(-.008,405),(.008,405),(.012,400),(.018,386),(.019,373),(.014,373),(.013,384),(.008,394),(-.008,394),(-.013,384),(-.014,373)]
 loft('underbarrel/lower_flange',[[(x,yz(px,0)[0],yz(0,py)[1]) for x,py in cross] for px in [163,750]])
 for j,(a,b) in enumerate([(156,225),(359,444),(523,548),(620,648),(724,751)]):box('underbarrel/vent_bridge'+str(j),.017,a,352,b,373)
 # Three source pods occupy the actual full width; V3 incorrectly simplified them to two.
 tube('module/central_body',426,613,453,.0120,0,.003,16)
 for side in [-1,1]:
  tube('module/side_body'+str(side),510,685,451,.0096,side*.022,.004,12)
  tube('module/side_collar'+str(side),545,555,451,.0104,side*.022,.0015,12)
  tube('module/rear_collar'+str(side),612,623,451,.0104,side*.022,.0015,12)
 tube('module/central_lens',429,430,453,.0088,0,.0087,16)
 for side in [-1,1]:tube('module/side_lens'+str(side),513,514,451,.0067,side*.022,.0066,12)
 outline('module/clamp',[(547,348),(556,343),(614,343),(621,350),(621,401),(630,414),(651,424),(489,424),(508,412),(547,408)],.025)
 for side in [-1,1]:
  o=swept('module/cable'+str(side),[(687,450),(710,459),(732,480),(755,489),(782,487),(810,472),(840,452)],.0022,.0022,N=8)
  for v in o.data.vertices:v.co.x+=side*.026
  o=swept('module/cable_socket'+str(side),[(814,470),(841,453)],.0035,.0035,N=8)
  for v in o.data.vertices:v.co.x+=side*.026
 box('sight/base',.0095,916,211,980,218)
 for side in [-1,1]:
  o=box('sight/notch'+str(side),.002,955,206,973,214)
  for v in o.data.vertices:v.co.x+=side*.0065

def profiled(name,stations):
 # Each axial station changes depth, upper/lower silhouette and ridge height.
 rows=[]
 for px,top,bottom,hw,ridge in stations:
  yy,_=yz(px,0);z=lambda py:yz(0,py)[1];dh=bottom-top
  rows.append([(-hw*.48,yy,z(top)),(hw*.48,yy,z(top)),(hw*.72,yy,z(top+dh*.08)),(hw,yy,z(ridge)),(hw*.78,yy,z(bottom-dh*.08)),(hw*.48,yy,z(bottom)),(-hw*.48,yy,z(bottom)),(-hw*.78,yy,z(bottom-dh*.08)),(-hw,yy,z(ridge)),(-hw*.72,yy,z(top+dh*.08))])
 if name=='shell/crown':
  rows=[]
  for px,top,bottom,hw,ridge in stations:
   hw*=.68;yy,_=yz(px,0);z=lambda py:yz(0,py)[1];dh=bottom-top;t=.0022
   xx=[(-hw,bottom),(-hw*.75,top+dh*.30),(-hw*.40,top),(hw*.40,top),(hw*.75,top+dh*.30),(hw,bottom),(hw-t,bottom),(hw*.75-t,top+dh*.30+5),(hw*.4,top+5),(-hw*.4,top+5),(-hw*.75+t,top+dh*.30+5),(-hw+t,bottom)]
   rows.append([(x,yy,z(py)) for x,py in xx])
 if name=='shell/tapered_barrel':
  rows=[]
  for px,top,bottom,hw,ridge in stations:
   yy,_=yz(px,0);z=lambda py:yz(0,py)[1];dh=bottom-top;up=max(1,min(dh*.08,(ridge-top)*.45));dn=max(1,min(dh*.08,(bottom-ridge)*.45));a=min(top+dh*.05,ridge-up-.5);b=max(bottom-dh*.05,ridge+dn+.5)
   right=[(hw*.48,top),(hw*.76,a),(hw*.96,ridge-up),(hw,ridge),(hw*.96,ridge+dn),(hw*.76,b),(hw*.48,bottom)]
   rows.append([(x,yy,z(py)) for x,py in right]+[(-x,yy,z(py)) for x,py in reversed(right)])
 return loft(name,rows)

def bore(o,px,py,r,length=.035):
 yy,zz=yz(px,py);bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=length,location=(0,yy+length*.43,zz),rotation=(math.pi/2,0,0));cut=bpy.context.object
 mod=o.modifiers.new('authored bore','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)

def igneous():
 # Swept crown is a continuous volume, widest at the upper receiver, with a true pointed rear tip.
 crown=profiled('shell/crown',[(132,266,307,.007,285),(230,244,291,.012,265),(340,234,278,.014,253),(420,236,263,.018,248),(550,217,241,.021,228),(650,207,236,.024,220),(730,202,249,.025,230),(840,204,260,.025,233),(970,204,264,.024,234),(1030,204,210,.012,207)])
 core=profiled('shell/lower_core',[(136,331,398,.010,363),(160,323,419,.013,377),(265,313,425,.017,401),(420,310,443,.022,391),(580,292,460,.025,370),(655,277,469,.024,359),(700,268,414,.021,352),(783,268,414,.016,351)])
 profiled('shell/swept_wing',[(146,316,334,.014,325),(280,302,336,.018,321),(420,275,334,.022,317),(560,258,324,.025,308),(640,231,309,.0258,287),(735,258,276,.024,266),(757,267,271,.019,269)])
 tube('barrel/upper_muzzle',130,165,293,.0068,wall=.0022,N=16)
 tube('barrel/upper_outer_lip',118,123,293,.0073,wall=.0017,N=16)
 tube('barrel/upper_inner_lip',123,130,293,.0058,wall=.001,N=16)
 tube('barrel/lower_muzzle',131,169,354,.0094,wall=.0026,N=16)
 tube('barrel/lower_outer_lip',116,122,354,.0100,wall=.0020,N=16)
 tube('barrel/lower_inner_lip',122,131,354,.0082,wall=.0011,N=16)
 bore(core,116,354,.0068,.05)
 bore(crown,118,293,.0046,.05)
 # Chamber diameter/length follow the original opening, no donor-profile lowering.
 tube('mag_cylinder/drum',797,958,329,.0258,wall=.025,N=20)
 tube('mag_cylinder/front_lip',796,807,329,.0265,wall=.003,N=16)
 tube('mag_cylinder/back_lip',950,964,329,.0265,wall=.003,N=16)
 outline('frame/chamber_back',[(965,261),(993,241),(1032,245),(1054,256),(1083,252),(1090,269),(1072,292),(1090,303),(1120,315),(1160,326),(1171,337),(1174,367),(1020,370),(1004,416),(951,416),(951,400),(968,389)],.0155)
 outline('frame/lower_rail',[(782,353),(798,355),(798,390),(813,402),(953,402),(953,414),(1004,414),(1004,444),(798,444),(798,429),(783,429)],.013)
 outline('frame/trigger_root',[(704,415),(796,414),(800,446),(797,492),(781,495),(779,515),(701,515),(680,502),(661,465),(679,434)],.012)
 grip('grip/curved_core',[(374,1022,1151,.013),(416,1010,1180,.0145),(465,1004,1202,.016),(510,1030,1225,.017),(550,1048,1247,.018),(590,1072,1263,.0185),(630,1092,1276,.018),(674,1108,1280,.017),(704,1114,1194,.014),(719,1118,1138,.007)])
 # Diagonal wraps are modeled as closed bands around the curved grip section.
 gr=[(374,1022,1151,.013),(416,1010,1180,.0145),(465,1004,1202,.016),(510,1030,1225,.017),(550,1048,1247,.018),(590,1072,1263,.0185),(630,1092,1276,.018),(674,1108,1280,.017),(704,1114,1194,.014),(719,1118,1138,.007)]
 def gs(py):
  for i in range(len(gr)-1):
   a,b=gr[i:i+2]
   if a[0]<=py<=b[0]:
    t=(py-a[0])/(b[0]-a[0]);return [a[k]*(1-t)+b[k]*t for k in [1,2,3]]
  return list(gr[0 if py<gr[0][0] else -1][1:])
 rim=[(-.75,-1),(.75,-1),(1,-.64),(1,.64),(.75,1),(-.75,1),(-1,.64),(-1,-.64)]
 for j,py0 in enumerate([470,545,615,680]):
  rows=[];f0,b0,_=gs(py0);mid=(f0+b0)/2
  for dy,offset in [(-17,.0017),(17,.0017),(17,.0001),(-17,.0001)]:
   row=[]
   for xn,yn in rim:
    py=py0+dy
    for _ in range(5):
     ff,bb,hw=gs(py);px=(ff+bb)/2+(bb-ff)*yn/2;py=py0+dy-.31*(px-mid)
    yy,zz=yz(px,py);row.append((xn*hw+math.copysign(offset,xn),yy,zz))
   rows.append(row)
  n=8;vv=[v for row in rows for v in row];ff=[]
  for k0 in range(4):
   for i in range(n):ff.append((k0*n+i,k0*n+(i+1)%n,((k0+1)%4)*n+(i+1)%n,((k0+1)%4)*n+i))
  mesh('grip/wrap'+str(j),vv,ff)
 swept('guard/outer',[(799,454),(797,493),(777,499),(777,514),(788,532),(808,542),(836,546),(949,546),(978,539),(996,522),(1004,498),(1000,459)],.0068,.0022,N=8)
 swept('guard/inner_diagonal',[(822,498),(845,515),(884,545)],.0068,.0018,N=6)
 outline('trigger/curved',[(929,457),(960,456),(976,469),(976,489),(963,509),(941,529),(924,533),(937,516),(944,496),(941,477)],.0032)
 box('sight/top_base',.007,851,200,1003,208)

def nation():
 # The diagonal cheek ridge changes both height and transverse width; it is not a flat side outline.
 body=profiled('shell/tapered_barrel',[(132,234,417,.0120,387),(250,230,421,.016,331),(400,225,423,.021,282),(550,218,426,.025,246),(680,214,429,.026,224),(750,211,430,.027,216),(803,210,419,.024,214)])
 bore(body,132,272,.0081,.039)
 outline('shell/muzzle_lower_lip',[(116,400),(123,391),(132,387),(143,405),(137,418),(127,420),(119,410)],.012)
 tube('mag_cylinder/drum',814,997,302,.0284,wall=.0278,N=20)
 profiled('shell/rear_crown',[(803,210,231,.020,220),(840,196,229,.022,212),(995,197,232,.023,216),(1060,203,250,.026,227),(1110,229,277,.026,254),(1170,278,309,.020,295),(1200,294,299,.004,297)])
 rows=[]
 for px,py,rx,rz in [(995,325,.026,.038),(1040,325,.026,.039),(1085,336,.024,.039),(1123,350,.021,.034),(1152,372,.015,.027)]:
  yy,zz=yz(px,py);rows.append([(rx*math.cos(a),yy,zz+rz*math.sin(a)) for a in [2*math.pi*i/16 for i in range(16)]])
 loft('frame/curved_breech',rows)
 profiled('frame/lower_cylinder_bridge',[(803,379,420,.014,400),(997,379,421,.014,400)])
 outline('frame/forward_trigger_shroud',[(475,425),(650,438),(698,450),(730,473),(761,516),(779,526),(801,530),(834,527),(834,503),(843,477),(858,457),(883,440),(909,423)],.010)
 grip('grip/flowing_body',[(370,1090,1147,.018),(395,1030,1159,.019),(418,1015,1174,.0195),(465,1040,1200,.019),(510,1065,1220,.018),(555,1083,1240,.0175),(600,1097,1258,.016),(640,1101,1249,.015),(680,1099,1200,.014),(708,1088,1140,.012),(728,1072,1088,.006)])
 # Thin hooked heel follows the long raked bottom line, with actual tip volume.
 outline('grip/hooked_heel',[(1068,727),(1087,710),(1100,681),(1101,648),(1114,649),(1115,676),(1135,686),(1263,609),(1275,614),(1282,623),(1074,741)],.012)
 outline('trigger/curved_blade',[(951,421),(982,421),(1007,438),(995,469),(978,501),(953,532),(941,525),(955,498),(962,474),(962,450)],.0031)
 profiled('sight/molded_foundation',[(811,203,214,.013,208),(833,201,214,.016,207),(870,201,212,.016,207),(903,203,212,.013,208)])
 cup=[(-.014,175),(-.014,194),(-.011,202),(-.007,207),(.007,207),(.011,202),(.014,194),(.014,175),(.009,175),(.009,190),(.007,197),(.004,200),(-.004,200),(-.007,197),(-.009,190),(-.009,175)]
 loft('sight/open_U_prongs',[[(x,yz(px,0)[0],yz(0,py)[1]) for x,py in cup] for px in [839,863]])

{'eyasluna':eyasluna,'igneous_hammer':igneous,'nation_of_beasts':nation}[wid]()
sc=bpy.context.scene;sc.render.use_compositing=False;sc.render.use_sequencer=False;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.background_type='WORLD';sc.world.color=(.11,.13,.15)
sc.render.resolution_x=1400;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
for o in source:o.data.materials.clear();o.data.materials.append(mat)
cam=bpy.data.cameras.new('V4 fixed source camera');cam.type='ORTHO';co=bpy.data.objects.new('V4 fixed source camera',cam);sc.collection.objects.link(co);sc.camera=co;cam.ortho_scale=(hi[1]-lo[1])*1.2
for mode in ['source','proposal']:
 for o in source:o.hide_render=mode!='source' or '.02.' in o.name or o.name in ('Eye','Reticle') or (wid=='nation_of_beasts' and o.name.endswith('.00.001'))
 for o in proposal:o.hide_render=mode!='proposal'
 for view,vec in [('side',(1,0,0)),('q',(1,-.60,.28)),('front',(0,-1,0)),('rear',(-1,.65,.28)),('back',(0,1,0))]:
  v=Vector(vec).normalized();co.location=center+v*2;co.rotation_euler=(-v).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(OUT/(mode+'_'+view+'.png'));bpy.ops.render.render(write_still=True)
 # Export evaluated authored proposal only for later native adapter work, never source geometry.
export=[]
for o in proposal:
 export.append({'name':o.name,'vertices':[list(o.matrix_world@v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]})
(OUT/'authored_geometry.json').write_text(json.dumps(export,indent=2))
(OUT/'camera_contract.json').write_text(json.dumps({'source_center':list(center),'orthographic_scale':cam.ortho_scale,'resolution':[1400,900],'source_to_canonical':'uniform scale pending native integration; no per-axis or per-component fit','stage':'neutral authored geometry proof; native export and element optimization intentionally deferred until shape review'},indent=2))
print('V4 proof solids',len(proposal),'faces',sum(len(o.data.polygons) for o in proposal))
