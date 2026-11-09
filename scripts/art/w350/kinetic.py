#!/usr/bin/env python3
"""W350 kinetic exotics: authored solid blocks, compact face atlas and 61 authored reload poses.
Sources are read-only evaluated .blend files. No recovered weapon/hand animation is claimed.
"""
import copy,hashlib,importlib.util,json,math,struct,sys,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];A=ROOT/"src/main/resources/assets/destiny"
sys.path.insert(0,str(ROOT/"scripts"))
def module(name,path):
 sp=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
base=module("w327_shapes","scripts/art/w327/group1.py");kit=base.kit
motion=module("w350_math","scripts/generate_reload_w213_chattering_bone.py")
import skin_arm_models_w204 as arms
import build_first_person_hands_w201 as hands
IDS=["crimson","thorn","outbreak_perfected"]
FILES={"crimson":"1fMX_9jWqIrjm9-Verh5-3NQGYlwL1QFd","thorn":"1obm9oFEegCgk-lavvPlkhYy5Qz2K94u3","outbreak_perfected":"1w5B18Z-fhUF98gWO7PV5WeGknffB3cS_"}
PAL={"crimson":{"shell":(76,79,77),"steel":(136,141,138),"trim":(207,210,197),"accent":(132,31,29),"rubber":(33,36,34),"recess":(16,19,20),"glow":(173,195,59)},"thorn":{"shell":(57,62,58),"steel":(88,96,87),"trim":(130,138,119),"accent":(145,116,49),"rubber":(75,77,65),"recess":(16,21,17),"glow":(93,222,49)},"outbreak_perfected":{"shell":(35,39,43),"steel":(77,84,88),"trim":(146,154,154),"accent":(163,30,27),"rubber":(25,28,30),"recess":(10,13,17),"glow":(244,54,40)}}
class Shape(base.Shape):
 def __init__(self):super().__init__()
 def diamond(self,n,z,y,l,h,w,m):
  # Five adjoining stepped sections retain a solid diamond section, not skew plates.
  for i,(a,b,k) in enumerate([(-1,-.6,.28),(-.6,-.2,.68),(-.2,.2,1),(.2,.6,.68),(.6,1,.28)]):self.box(n+str(i),8-w/2,8+w/2,y-h*k/2,y+h*k/2,z+a*l/2,z+b*l/2,m)
 def cylinder(self,z0,z1,cy,w,h,m):
  self.block("mag_cylinder",w,cy-h/2,cy+h/2,z0,z1,m,.35)
  self.block("mag_front_band",w+.08,cy-h/2+.05,cy+h/2-.05,z0-.15,z0,"steel",.3)
  self.block("mag_rear_band",w+.08,cy-h/2+.05,cy+h/2-.05,z1,z1+.15,"steel",.3)
  for side in [-1,1]:
   for i in range(3):self.box("mag_flute_%s_%s"%(side,i),8+side*w/2-.04,8+side*w/2+.04,cy-.65+i*.58,cy-.4+i*.58,z0+.18,z1-.18,"accent")

def crimson():
 s=Shape();s.tube("muzzle",1.8,2.2,11.7,-7.6,-6.7,"steel",.28)
 s.block("red_barrel_front",1.85,10.5,12.85,-6.7,-3.4,"accent")
 s.block("barrel_rear",1.85,10.5,12.85,-3.4,1.25,"shell")
 s.stair("upper_ridge",[(-2.7,-.8,12.85,13.1),(-.8,1.2,12.85,13.35),(1.2,3.2,12.9,13.6),(3.2,5.3,13.0,13.6)],1.35,"steel")
 s.block("lower_frame",1.28,9.5,10.25,.9,5.6,"shell")
 s.block("rear_frame",1.4,10.25,13.3,5.3,6.4,"shell")
 s.cylinder(1.5,4.9,11.55,2.1,2.15,"trim")
 s.grip("grip",7.8,4.7,1.45,5.0,2.0,"trim")
 for n in list(s.roles):
  if n.startswith("mag_flute"):s.roles[n]="steel"
 s.guard(3.6,6.3,8.1,9.5)
 s.block("bayonet_mount",.9,9.5,9.8,-6.8,.9,"accent")
 s.block("bayonet_grip",.8,8.8,9.5,-3.1,-.2,"rubber")
 # Four stepped solid blade stations including the forward point.
 s.stair("bayonet",[(-10,-9.1,9.07,9.35),(-9.1,-8,8.82,9.5),(-8,-6.1,8.72,9.55),(-6.1,-3.1,8.72,9.55)],.32,"accent")
 s.block("blade_edge",.34,8.56,8.72,-8,-3.1,"trim",.04)
 s.box("front_sight",7.8,8.2,12.85,13.55,-7.2,-6.9,"steel")
 s.sight(5.7,13.5,.9,.6)
 return s

def thorn():
 s=Shape();s.tube("muzzle",1.35,1.9,11.7,-8.4,-7.8,"shell",.22)
 s.block("upper_spine",1.35,12.4,13.05,-7.8,1.4,"shell")
 s.stair("bottom_spine",[(-9.5,-8,9.3,9.65),(-8,-6.3,9.3,9.9),(-6.3,-4.6,9.3,9.85),(-4.6,-2.6,9.3,9.8),(-2.6,-.5,9.3,9.75),(-.5,1.4,9.3,9.8)],1.1,"shell")
 # Large light-through barrel windows bounded by genuine separate diagonal steps.
 for i,(z0,z1,y0,y1) in enumerate([(-7.8,-7,9.65,11),(-7,-6.2,10.65,12.4),(-3.6,-2.8,9.8,11),(-2.8,-2.1,10.7,12.4),(.6,1.4,9.8,12.4)]):s.block("web"+str(i),1.3,y0,y1,z0,z1,"steel")
 s.block("inner_barrel",1.08,11.25,12.35,-7.8,1.3,"shell")
 s.stair("top_crown",[(-2,-.6,13.05,13.25),(-.6,.6,13.05,13.5),(.6,2.0,13.05,13.75),(2,4.5,13.05,13.6)],1.25,"steel")
 for i,z in enumerate([-5.4,-3.8,-2.2]):
  s.stair("thorn_spike"+str(i),[(z-.8,z-.25,13.05,13.16),(z-.25,z+.3,13.05,13.5),(z+.3,z+.9,13.05,13.85)],.45,"steel")
 s.block("cylinder_lower_frame",1.25,9.2,9.7,1.4,5.3,"shell")
 s.block("cylinder_rear_frame",1.45,9.7,13.25,4.8,5.65,"shell")
 s.cylinder(1.6,4.55,11.35,2.15,2.45,"accent")
 s.grip("grip",7.2,4.4,1.4,5.2,1.6,"shell")
 # Fabric bands are actual thin connected wraps, applied to grip frame.
 for i in range(5):
  yy=4.8+i*.65;zz=7.2-1.6*(yy-4.4)/5.2
  s.block("wrap"+str(i),1.48,yy,yy+.22,zz-.03,zz+1.3,"rubber",.08)
 s.guard(3.2,5.9,7.7,9.3)
 s.stair("grip_heel",[(6.7,7.4,4.15,4.4),(7.4,8.4,4.25,4.55)],1.2,"steel")
 s.sight(4.9,13.2,.65,.45)
 s.box("green_front_bead",7.92,8.08,13.13,13.3,-7.7,-7.5,"glow")
 return s

def outbreak_perfected():
 s=Shape();s.tube("muzzle",1.15,1.15,11.15,-10,-8.5,"steel",.22)
 s.block("core_barrel",1.1,10.6,11.8,-8.5,1.1,"black_steel")
 s.block("receiver",1.75,10.15,12.05,1.1,8,"shell")
 # Three characteristic angular SIVA chamber housings; adjoining solid cross sections.
 for i,z in enumerate([-.8,1.9,4.6]):s.diamond("diamond_chamber"+str(i),z,11.65,2.7,3.8,2.3,"shell")
 for i,z in enumerate([-8,-6.6,-5.2,-3.8]):
  s.diamond("barrel_node"+str(i),z,11.25,1.35,2.4,1.65,"shell")
  s.box("barrel_top_link"+str(i),7.7,8.3,12.05,12.23,z,z+.8,"glow")
  s.box("barrel_bottom_link"+str(i),7.7,8.3,10.25,10.43,z,z+.8,"glow")
 s.stair("forebrace",[(-7.2,-6.2,8.7,9.25),(-6.2,-5.1,8.15,9.25),(-5.1,-3.5,8.15,9.25),(-3.5,-2.6,8.5,9.25)],1.45,"shell")
 s.block("rear_tube",1.2,10.75,11.65,8,12.4,"steel")
 s.block("stock_upper",1.85,10.75,12.15,12.4,15.7,"shell")
 s.block("stock_end",1.95,7.3,12.15,15.7,16.25,"rubber")
 s.mag(12.1,14.7,5.25,10.75,1.65,"shell")
 s.grip("pistol_grip",9,5.7,1.15,4.5,1.5,"shell")
 s.guard(5.8,7.8,8.0,10.15)
 # Open lower skeletal frame, no filled side alpha plate.
 s.box("frame_front",7.75,8.25,6.2,10.1,4.4,4.7,"steel")
 s.box("frame_floor",7.75,8.25,5.8,6.2,4.4,9.4,"steel")
 s.box("frame_rear",7.75,8.25,5.8,6.7,9.1,9.4,"steel")
 s.sight(6.5,12.1,.8,1.4)
 s.box("sight_top",7.6,8.4,13.5,13.64,6.5,6.75,"steel")
 # Parallel SIVA conduit strip groups are painted into the large panels, not extra plates.
 return s

BUILDERS={x:globals()[x] for x in IDS}
def art(w):return ROOT/"art/weapons/w350"/w
def emit(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,separators=(",",":"),allow_nan=False)+"\n")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bake(w,s):
 colors={**PAL[w],"black_steel":PAL[w]["recess"]};faces=[];scale=12
 for e in s.e:
  for f in kit.FACE_AXES:
   o,u,v=kit.face_frame(e,f);ww=max(2,round(math.dist((0,0,0),u)*scale));hh=max(2,round(math.dist((0,0,0),v)*scale));role=s.roles[e["name"]];col=colors[role];im=Image.new("RGBA",(ww,hh),col+(255,));d=ImageDraw.Draw(im)
   # One texel edge, calm broad fields; restrained role-specific machining.
   if role not in ("recess","glow"):
    d.line((0,0,ww-1,0),fill=tuple(min(255,c+15) for c in col)+(255,));d.line((0,hh-1,ww-1,hh-1),fill=tuple(max(0,c-15) for c in col)+(255,))
   if role=="rubber" and ww>5 and hh>5:
    for j in range(3,hh-1,5):d.line((1,j,ww-2,j),fill=tuple(max(0,c-9) for c in col)+(255,))
   if f in ("west","east"):
    n=e["name"]
    if w=="crimson" and n.startswith("barrel_rear"):
     # Selected source repeated pale skull/stud marks, stylized at available texels.
     for x in range(8,ww-4,14):d.rectangle((x,hh//2-2,x+3,hh//2+1),fill=colors["trim"]+(255,));d.point((x+1,hh//2),fill=colors["recess"]+(255,))
    if w=="crimson" and n.startswith("grip") and ww>4 and hh>4:
     d.rectangle((2,1,ww-3,hh-2),fill=colors["rubber"]+(255,))
    if w=="thorn" and n.startswith("mag_") and role=="accent":
     for j in range(2,hh-2,4):d.line((1,j,ww-2,max(1,j-3)),fill=colors["trim"]+(255,))
    if w=="outbreak_perfected" and (n.startswith("diamond") or n.startswith("mag_")):
     if n.startswith("diamond"):
      d.rectangle((1,1,ww-2,hh-2),outline=colors["accent"]+(255,),width=1)
     else:
      for j in range(3,hh-2,5):d.line((2,j,ww-3,j),fill=colors["glow"]+(255,))
   faces.append((e["name"],f,im))
 order=sorted(faces,key=lambda x:(-x[2].height,-x[2].width,x[0],x[1]));size=512;x=y=row=0;pos={}
 for n,f,im in order:
  ww,hh=im.width+2,im.height+2
  if x+ww>size:x=0;y+=row;row=0
  pos[n,f]=(x,y);x+=ww;row=max(row,hh)
 used=y+row;H=32
 while H<used:H*=2
 assert H<=1024,(w,H);atlas=Image.new("RGBA",(size,H));uv={}
 for n,f,im in faces:
  x,y=pos[n,f];atlas.paste(im.resize((im.width+2,im.height+2),Image.Resampling.NEAREST),(x,y));atlas.paste(im,(x+1,y+1));uv[n,f]=[(x+1)/size*16,(y+1)/H*16,(x+1+im.width)/size*16,(y+1+im.height)/H*16]
 parts={"body":[],"magazine":[]}
 for e in s.e:
  e=copy.deepcopy(e);e["faces"]={f:{"uv":uv[e["name"],f],"texture":"#0"} for f in kit.FACE_AXES}
  if s.roles[e["name"]]=="glow":e.update(shade=False,light_emission=10)
  parts["magazine" if e["name"].startswith("mag_") else "body"].append(e)
 p=A/f"textures/item/weapon/w350/{w}.png";p.parent.mkdir(parents=True,exist_ok=True);atlas.save(p,optimize=True)
 emit(art(w)/"parts.json",{"texture_size":[size,H],"parts":parts});kit.hud_icon(s.e,A/f"textures/item/weapon/w350/{w}_hud.png",lambda n:False)
 return parts,[size,H]

def lerp_keys(keys,p):
 # Existing shape-preserving C1 Hermite avoids easing to zero speed every output frame.
 times=[k[0] for k in keys];idx=min(next((i for i in range(len(keys)-1) if p<=times[i+1]),len(keys)-2),len(keys)-2);h=times[idx+1]-times[idx];t=(p-times[idx])/h;out=[]
 for j in range(1,len(keys[0])):
  vs=[k[j] for k in keys];m=motion.tangents(times,vs);out.append((2*t**3-3*t*t+1)*vs[idx]+(t**3-2*t*t+t)*h*m[idx]+(-2*t**3+3*t*t)*vs[idx+1]+(t**3-t*t)*h*m[idx+1])
 return out

def posed(display,grip,angles,shift,pivot=None,swing=0,offset=(0,0,0)):
 b=motion.xyz(angles);l=motion.xyz((0,0,swing));h=motion.sub(grip,(8,8,8));pv=motion.sub(pivot or grip,(8,8,8));local=motion.add(motion.sub(h,motion.vec(b,h)),motion.vec(b,motion.add(motion.sub(pv,motion.vec(l,pv)),offset)))
 d=copy.deepcopy(display)
 for ctx in hands.FP:
  src=display[ctx];r=motion.xyz(src["rotation"]);sc=src["scale"][0];d[ctx]["rotation"]=motion.euler(motion.mul(r,motion.mul(b,l)));d[ctx]["translation"]=motion.add(src["translation"],motion.vec(r,[sc*(local[i]+shift[i]) for i in range(3)]))
 return d

def arm_graph(w,side,disp):
 out={};node=arms.arm_nodes(side,disp,out)
 # Shared immutable W204 parent remains; only own pose leaves are emitted.
 for path,data in out.items():
  old="destiny:"+str(path.relative_to(arms.A/"models")).removesuffix(".json");new=f"destiny:weapon_w350/{w}/hands/{path.stem}";node=json.loads(json.dumps(node).replace(old,new));emit(A/("models/"+new.split(":")[1]+".json"),json.loads(data))
 return node

def build(w):
 ad=art(w);ad.mkdir(parents=True,exist_ok=True);ev=json.loads((ad/"source-evaluation.json").read_text());assert sha(Path(ev["blend"]))==ev["sha256"];s=BUILDERS[w]();parts,texsize=bake(w,s)
 donor="weapon_surface_w123/blast_furnace" if w=="outbreak_perfected" else "item/weapon/ace_of_spades"
 display=json.loads((A/f"models/{donor}.json").read_text())["display"]
 grip=[8,8.1,7.5] if w=="outbreak_perfected" else [8,7.5,6.75]
 support=[8,9.6,-1.8] if w=="outbreak_perfected" else [8,7.3,5.8]
 pivot=[8,10.4,2] if w!="outbreak_perfected" else [8,10.5,13.4]
 if hasattr(s,"anchors"):grip,support,pivot=s.anchors
 # Native third person in the common -Z-forward block convention.
 for ctx in ("thirdperson_righthand","thirdperson_lefthand"):display[ctx]={"rotation":[90,0,0],"translation":[0,2,0],"scale":[.7]*3}
 if hasattr(s,"thirdPerson"):
  for ctx in ("thirdperson_righthand","thirdperson_lefthand"):display[ctx]=copy.deepcopy(s.thirdPerson)
 key=f"weapon_w350/{w}"
 def leaf(name,es,disp):emit(A/f"models/{key}/{name}.json",{"credit":"W350 authored blocks; read-only source provenance in art/weapons/w350/"+w,"textures":{"0":f"destiny:item/weapon/w350/{w}","particle":f"destiny:item/weapon/w350/{w}"},"display":disp,"elements":es})
 full=parts["body"]+parts["magazine"]
 for name,es in [("full",full),*parts.items()]:leaf(name,es,display)
 ads=copy.deepcopy(display)
 for ctx in hands.FP:ads[ctx].update(rotation=[0,0,0],translation=[-5.6,-2.8,-3.5] if ctx.endswith("righthand") else [5.6,-2.8,-3.5],scale=[.85]*3)
 if hasattr(s,"adsTarget"):
  for ctx in hands.FP:ads[ctx].update(copy.deepcopy(s.adsTarget))
 leaf("ads",full,ads)
 inspect=posed(display,grip,(12,-25,-15),(0,-.5,0));leaf("inspect",full,inspect)
 def model(n):return {"type":"minecraft:model","model":f"destiny:{key}/{n}"}
 def withhands(node,body,moving=None,p=0):
  rd=hands.display_at(body,{"position":grip,"rotation":[-12,0,-8]});ld=hands.display_at(moving or body,{"position":pivot if moving else support,"rotation":[-35,5,25]})
  return {"type":"minecraft:composite","models":[node,arm_graph(w,"right",rd),arm_graph(w,"left",ld)]}
 idle=model("full");hip=withhands(idle,display);adsnode=withhands(model("ads"),ads);inspectnode=withhands(model("inspect"),inspect)
 entries=[];poses=[]
 for i in range(61):
  p=i/60
  vals=lerp_keys([(0,0,0,0,0,0),(.14,38,-12,-16,0,0),(.28,56,-19,-22,1,0),(.43,56,-19,-22,1,1),(.62,54,-18,-20,1,1),(.76,48,-16,-17,0,0),(1,0,0,0,0,0)],p)
  ang=vals[:3];op,ex=vals[3:];swing=-75*op if w!="outbreak_perfected" else 0;offset=(0,0,1.5*ex) if w!="outbreak_perfected" else (0,-4.2*ex,0)
  body=posed(display,grip,ang,(0,0,0));moving=posed(display,grip,ang,(0,0,0),pivot,swing,offset)
  for part,d in [("body",body),("magazine",moving)]:emit(A/f"models/weapon_reload_w350/{w}/{i}_{part}.json",{"parent":f"destiny:{key}/{part}","display":d})
  comp={"type":"minecraft:composite","models":[{"type":"minecraft:model","model":f"destiny:weapon_reload_w350/{w}/{i}_{part}"} for part in parts]}
  comp=withhands(comp,body,moving,p);guard={"type":"minecraft:select","property":"minecraft:display_context","cases":[{"when":list(hands.FP),"model":comp}],"fallback":idle}
  emit(A/f"items/weapon_reload_w350/{w}/{i}.json",{"model":guard});entries.append({"threshold":struct.unpack("!f",struct.pack("!f",p))[0],"model":comp});poses.append({"frame":i,"progress":p,"bodyDisplay":body,"magazineDisplay":moving,"bodyEuler":ang,"cylinderSwing":swing,"magazineOffset":offset})
 reload={"type":"minecraft:range_dispatch","property":"minecraft:custom_model_data","index":1,"entries":entries,"fallback":hip}
 guard=lambda node:{"type":"minecraft:select","property":"minecraft:display_context","cases":[{"when":list(hands.FP),"model":node}],"fallback":idle}
 emit(A/f"items/weapon_reload_w350/{w}.json",{"model":guard(reload)})
 aim_entries=[]
 for i in range(21):
  t=i/20;d=hands.blend_display(display,ads,t)
  emit(A/f"models/weapon_aim_w350/{w}/{i}.json",{"parent":f"destiny:{key}/full","display":d})
  n=withhands({"type":"minecraft:model","model":f"destiny:weapon_aim_w350/{w}/{i}"},d)
  aim_entries.append({"threshold":struct.unpack("!f",struct.pack("!f",t))[0],"model":n})
 emit(A/f"items/weapon_aim_w350/{w}.json",{"model":guard({"type":"minecraft:range_dispatch","property":"minecraft:custom_model_data","index":3,"entries":aim_entries,"fallback":hip})})
 select={"type":"minecraft:select","property":"minecraft:custom_model_data","index":0,"cases":[{"when":"ads","model":adsnode},{"when":"inspect","model":inspectnode},{"when":"reload","model":reload}],"fallback":hip}
 # Runtime may route fixed aliases during reload. Root graph also supports string reload + float[1].
 emit(A/f"items/weapon/{w}.json",{"model":{"type":"minecraft:select","property":"minecraft:display_context","cases":[{"when":list(hands.FP),"model":select}],"fallback":idle}})
 for state,node in [("ads",adsnode),("inspect",inspectnode),("hip",hip)]:emit(A/f"items/{key}/{state}.json",{"model":{"type":"minecraft:select","property":"minecraft:display_context","cases":[{"when":list(hands.FP),"model":node}],"fallback":idle}})
 emit(ad/"rig.json",{"schemaVersion":1,"sourceBlendSha256":ev["sha256"],"sourceArmatures":ev["armatures"],"sourceActions":ev["actions"],"motionProvenance":"Authored 61-pose adaptation; supplied source contains no actions or player wrist/elbow rig","grip":grip,"support":support,"movingPivot":pivot,"movingBinding":"Magazine bone" if w=="outbreak_perfected" else "Cylinder/CraneRotate source bones" if w=="thorn" else "Authored cylinder partition; source has no bones","poses":poses})
 emit(ad/"design.json",{"id":w,"materials":PAL[w],"geometry":"Adjoining solid rectangular stations; holes remain geometric; no source polygon/voxel conversion","elements":s.e,"roles":s.roles})
 paths=sorted({p for branch in ("models","items") for namespace in ("weapon_w350","weapon_reload_w350","weapon_aim_w350") for p in (A/branch/namespace/w).rglob("*.json")} | {A/f"items/weapon/{w}.json",A/f"items/weapon_reload_w350/{w}.json",A/f"items/weapon_aim_w350/{w}.json",A/f"textures/item/weapon/w350/{w}.png",A/f"textures/item/weapon/w350/{w}_hud.png"})
 emit(ad/"integration.json",{"id":w,"itemModel":"destiny:weapon/"+w,"reloadPrefix":"destiny:weapon_reload_w350/"+w+"/","reloadFrames":61,"reloadModel":"destiny:weapon_reload_w350/"+w,"aimModel":"destiny:weapon_aim_w350/"+w,"aimFrames":21,"aimProgressFloatIndex":3,"adsModel":"destiny:"+key+"/ads","hipModel":"destiny:"+key+"/hip","inspectModel":"destiny:"+key+"/inspect","strings0":["hip","ads","inspect","reload"],"reloadProgressFloatIndex":1,"skinArmReadyFlag":8,"skinArmSlimFlag":9,"skinColorOffsets":{"right":64,"left":192},"requiresCarrierSkinArmProjection":True})
 emit(ad/"manifest.json",{"batch":"W350","id":w,"driveFileId":FILES[w],"sourceBlend":ev["blend"],"sourceBlendSha256":ev["sha256"],"sourceUnchanged":True,"sourceActions":len(ev["actions"]),"motion":"Authored mechanical reload, not extracted animation","elements":{k:len(v) for k,v in parts.items()},"assembledWeapon":len(full),"assembledWithClassicForearms":len(full)+224,"atlas":texsize,"frames":61,"nativeAcceptance":"PENDING master first Vision, delegated review and second Vision","outputsSha256":{str(p.relative_to(ROOT)):sha(p) for p in paths}})
 validate(w);print(w,len(full),texsize,len(paths),flush=True)

def validate(w):
 d=json.loads((art(w)/"parts.json").read_text());es=sum(d["parts"].values(),[]);assert len(es)<=1000;assert len(set(e["name"] for e in es))==len(es)
 for e in es:
  assert all(-16<=a<=b<=32 for a,b in zip(e["from"],e["to"]))
  assert sum(b-a>1e-8 for a,b in zip(e["from"],e["to"]))>=2
  for f in e["faces"].values():assert all(0<=n<=16 for n in f["uv"])
 rig=json.loads((art(w)/"rig.json").read_text());ps=rig["poses"];assert len(ps)==61;assert ps[0]["bodyDisplay"]==ps[-1]["bodyDisplay"];assert ps[0]["magazineDisplay"]==ps[-1]["magazineDisplay"]
 maxstep=max(abs(a-b) for q,r in zip(ps,ps[1:]) for a,b in zip(q["bodyEuler"],r["bodyEuler"]));assert maxstep<20
 emit(art(w)/"validation.json",{"parse":"PASS","positiveBounds":"PASS","uv":"PASS","poseCount":61,"endpoints":"Exact restored idle display","maxBodyAngularStepDegrees":maxstep,"sourceOriginalSha":"PASS","elements":len(es),"nativePackLoad":"PENDING","nativeHipADSReloadThirdPerson":"PENDING","native10To20":"PENDING","sourceMotionFidelity":"NOT_CLAIMED"})

def render(w):
 out=art(w)/"review";out.mkdir(exist_ok=True)
 subprocess.run(["/Applications/Blender.app/Contents/MacOS/Blender","--disable-autoexec","--factory-startup","-b","-t","2","--python",str(ROOT/"scripts/art/w325/render_model.py"),"--",str(out/w),str(art(w)/"parts.json"),str(A/f"textures/item/weapon/w350/{w}.png"),"west,east,q,top,front"],check=True)
if __name__=="__main__":
 cmd=sys.argv[1] if len(sys.argv)>1 else "build"
 for w in sys.argv[2:] or IDS:{"build":build,"render":render,"validate":validate}[cmd](w)
