#!/usr/bin/env python3
"""H27 independently authored cuboid props from visual reference; no extracted data.
Deterministic source + runtime geometry. Does not write animations or older assets.
"""
import base64, copy, hashlib, io, json, math, sys, uuid
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/"src/main/resources/assets/destiny"
ART=ROOT/"art/blockbench/supers"
SIDES=("north","east","south","west","up","down")
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,"destiny:h27:"+s))
def encode(o): return (json.dumps(o,ensure_ascii=False,indent=2)+"\n").encode()
def lerp(points,y):
    for (a,x),(b,z) in zip(points,points[1:]):
        if a<=y<=b:return x+(z-x)*(y-a)/(b-a)
    raise ValueError(y)
def smooth(points,y):
    y=max(points[0][0],min(points[-1][0],y))
    for i,((a,x),(b,z)) in enumerate(zip(points,points[1:])):
        if a<=y<=b:
            prev=points[max(0,i-1)];nxt=points[min(len(points)-1,i+2)]
            ma=(z-prev[1])/(b-prev[0]);mb=(nxt[1]-x)/(nxt[0]-a)
            t=(y-a)/(b-a)
            return (2*t**3-3*t*t+1)*x+(t**3-2*t*t+t)*(b-a)*ma+(-2*t**3+3*t*t)*z+(t**3-t*t)*(b-a)*mb
    raise ValueError(y)
class Prop:
    def __init__(self,name,base,palette):
        self.name=name; self.model=copy.deepcopy(base);self.model["elements"]=[]
        self.bb=[];self.groups={};self.palette=palette
        im=Image.new("RGBA",(256,128));d=ImageDraw.Draw(im)
        for m,c in enumerate(palette):
            for y in range(128):
                for x in range(32):
                    f=.85+.22*math.sin((x+1)/33*math.pi)+((x*7+y*11)%17-8)*.0015
                    d.point((32*m+x,y),fill=tuple(min(255,round(v*f)) for v in c)+(255,))
        buf=io.BytesIO();im.save(buf,format="PNG");self.png=buf.getvalue()
    def box(self,name,c,size,m=0,group="body",rot=0,axis="z",emission=0):
        lo=[round(v-s/2,7) for v,s in zip(c,size)];hi=[round(v+s/2,7) for v,s in zip(c,size)]
        uv=[32*m+3,4,32*m+29,124]
        e={"name":name,"from":lo,"to":hi,"shade":True,"light_emission":emission,
           "faces":{s:{"uv":[uv[0]/16,uv[1]/8,uv[2]/16,uv[3]/8],"texture":"#0"} for s in SIDES}}
        if rot:e["rotation"]={"axis":axis,"angle":rot,"origin":list(c)}
        self.model["elements"].append(e)
        b=copy.deepcopy(e);b.update(type="cube",uuid=uid(self.name+name),box_uv=False,autouv=0,origin=list(c),rotation=[0,0,0],export=True,rescale=False)
        b["rotation"]["xyz".index(axis)]=rot
        for f in b["faces"].values():f.update(uv=uv,texture=0)
        self.bb.append(b);self.groups.setdefault(group,[]).append(b["uuid"])
    def ring(self,name,y,h,r,m=0):
        for angle in (0,45):self.box(name+str(angle),(8,y,8),(r*math.sqrt(2),h,r*math.sqrt(2)),m,"collars",angle,"y")
    def line(self,name,a,b,width,m,group="detail",emission=0):
        dx,dy=b[0]-a[0],b[1]-a[1];ang=-math.degrees(math.atan2(dx,dy))
        while ang>90:ang-=180
        while ang< -90:ang+=180
        self.box(name,[(a[i]+b[i])/2 for i in range(3)],(width,math.hypot(dx,dy)+.012,width),m,group,ang,emission=emission)
    def inherited(self,e,b):
        e=copy.deepcopy(e);b=copy.deepcopy(b);name=b["name"];e["name"]=name
        # Historical H20 rest .bbmodel tail was stale; runtime geometry is canonical.
        b["from"],b["to"]=copy.deepcopy(e["from"]),copy.deepcopy(e["to"])
        b["origin"]=[8,8,8];b["rotation"]=[0,0,0]
        if "rotation" in e:
            b["origin"]=copy.deepcopy(e["rotation"]["origin"])
            b["rotation"]["xyz".index(e["rotation"]["axis"])]=e["rotation"]["angle"]
        # Recolor without changing a single coordinate/rotation of string and arrow.
        for obj,scale in ((e,False),(b,True)):
            for f in obj["faces"].values():f.update(uv=[163,4,189,124] if scale else [163/16,.5,189/16,15.5],texture=0 if scale else "#0")
        b["uuid"]=uid(self.name+name)
        self.model["elements"].append(e);self.bb.append(b);self.groups.setdefault("string_arrow",[]).append(b["uuid"])
    def files(self):
        name=self.name
        self.model.update(format_version="1.21.11",credit="H27 independently authored reconstruction; Destiny design Bungie; docs/design/40_H27_원본_모델_검토.md",ambientocclusion=False,texture_size=[256,128],textures={"0":f"destiny:item/supers/{name}","particle":f"destiny:item/supers/{name}"})
        bb=json.loads((ART/"arc_staff_h24.bbmodel").read_text())
        bb.update(name=name,model_identifier=name,credit=self.model["credit"],elements=self.bb,display=copy.deepcopy(self.model["display"]),ai_used=True,ai_agents="Codex H27 deterministic authoring")
        bb["groups"]=[dict(name=g,uuid=uid(name+g),origin=[8,8,8],rotation=[0,0,0],export=True) for g in self.groups]
        bb["outliner"]=[dict(uuid=uid(name+g),children=ids) for g,ids in self.groups.items()]
        t=bb["textures"][0];t.update(name=name+".png",uuid=uid(name+"texture"),source="data:image/png;base64,"+base64.b64encode(self.png).decode())
        return {A/f"models/item/{name}.json":encode(self.model),A/f"items/{name}.json":encode({"model":{"type":"minecraft:model","model":f"destiny:item/{name}"}}),A/f"textures/item/supers/{name}.png":self.png,ART/f"{name}.bbmodel":encode(bb)}
def read(n):return json.loads((A/f"models/item/{n}.json").read_text())
def arc():
    p=Prop("arc_staff_h27",read("arc_staff_h24"),[(69,79,88),(24,31,40),(188,202,210),(93,111,126),(47,177,228),(211,246,255),(112,126,140),(65,72,79)])
    p.ring("continuous_shaft",8,35,.44)
    p.ring("wrapped_grip",6,7,.49,1)
    # Genuine diagonal wrap across all four faces, not glowing white shaft stripes.
    for i in range(14):
        y=2.6+i*.49
        for side in (-1,1):
            p.line(f"grip_diagonal_{i}_{side}",(7.66,y,8+side*.36),(8.34,y+.4,8+side*.36),.045,6,"grip")
    for label,start,end in (("upper",13,18),("lower",-6,-1)):
        p.ring(label+"_ribbed_sleeve",(start+end)/2,end-start,.53,1)
        for i in range(12):p.ring(label+f"_rib_{i}",start+i*(end-start)/11,.12,.62,2)
    for i,y in enumerate((-10,-8,-6,-1,2.4,9.6,12.8,18.2,20.8,24.7)):
        p.ring(f"collar_dark_{i}",y,.38,.64,1);p.ring(f"collar_steel_{i}",y+.16,.14,.68,2)
    for label,y in (("upper",22.5),("lower",-11.1)):
        p.ring(label+"_neck",y,2.7,.38,3)
        for i in range(8):p.ring(label+f"_neck_etch_{i}",y-1.1+i*.3,.055,.43,6)
    # Solid upper spear: narrow throat, flared shoulders and a fine long tip.
    upper=[(25,.39),(26,.27),(28.8,.28),(29.3,.72),(32,.025)]
    for i in range(42):
        y=25+(i+.5)*7/42;w=lerp(upper,y)
        p.box(f"upper_spear_{i:02}",(8,y,8),(2*w,7/42,.23),0,"upper_blade")
        p.box(f"upper_edge_{i:02}",(8-w+.035,y,8.005),(.07,7/42,.25),2,"upper_blade")
    # Lower blade is a split, open blade around an actual empty slot; not a mirrored spear.
    lower=[(-16,.025),(-14.5,.52),(-14,.38),(-12.5,.36),(-12,.67),(-11.8,.40)]
    for i in range(28):
        y=-16+(i+.5)*4.2/28;w=lerp(lower,y)
        gap=lerp([(-16,0),(-15.3,0),(-14.6,.13),(-13.0,.16),(-12.5,.10),(-11.8,0)],y)
        if gap>.015:
            for s in (-1,1):p.box(f"lower_slot_rail_{i:02}_{s}",(8+s*(gap+w)/2,y,8),(w-gap,.15,.25),0,"lower_blade")
        else:p.box(f"lower_point_{i:02}",(8,y,8),(2*w,.15,.25),0,"lower_blade")
        p.box(f"lower_edge_{i:02}",(8+w-.025,y,8),(.05,.15,.27),2,"lower_blade")
    return p
# Manually authored smooth centerline + width profile; no source mesh/texture sampling.
CURVE=[(-12,11.27),(-11,10.95),(-9,9.55),(-7,7.6),(-5,6.45),(-3,7.5),(0,8),(3,7.6),(5,6.0),(7,7.1),(9,9.3),(11,10.9),(12,11.27)]
WIDTH=[(-12,.06),(-10,.15),(-8,.28),(-6,.48),(-4,.68),(-2,.27),(0,.26),(2,.27),(4,.75),(6,.55),(8,.29),(10,.14),(12,.06)]
def bow(drawn):
    name="shadow_bow_h27_drawn" if drawn else "shadow_bow_h27"
    p=Prop(name,read("shadow_bow_h22_drawn"),[(66,36,115),(31,16,62),(150,99,222),(89,48,157),(192,139,255),(232,203,255),(117,71,190),(52,26,98)])
    for i in range(120):
        y=-12+(i+.5)*.2;x=smooth(CURVE,y);w=smooth(WIDTH,y);dep=.16+w*.46
        dx=smooth(CURVE,y+.1)-smooth(CURVE,y-.1)
        angle=-math.degrees(math.atan2(dx,.2));r=math.radians(angle)
        # Overlap through the tight belly bend; tiny depth ramp avoids coplanar flicker.
        length=math.hypot(dx,.2)+.16;dep+=i*.000001
        # Tangent-oriented strips remove the horizontal staircase of voxel slices.
        p.box(f"curved_limb_{i:03}",(x,8+y,8),(w*2,length,dep),0,"limbs",angle,emission=4)
        p.box(f"violet_rim_{i:03}",(x-(w-.045)*math.cos(r),8+y-(w-.045)*math.sin(r),8),(.09,length,dep+.025),2,"limbs",angle,emission=12)
    for j,(a,b,w) in enumerate([((6.8,13,8),(8.6,12.0,8),.3),((8.4,16.6,8),(10.1,15.1,8),.21),((7,2.3,8),(8.8,3.5,8),.32),((9,-.8,8),(10.6,1,8),.18)]):
        # Taper each inward thorn instead of rectangular spikes.
        for k in range(8):
            t=k/8;u=(k+1)/8
            p.line(f"inward_spur_{j}_{k}",tuple(a[v]+(b[v]-a[v])*t for v in range(3)),tuple(a[v]+(b[v]-a[v])*u for v in range(3)),max(.025,w*(1-t)),2,"spurs",8)
    old=read("shadow_bow_h22_drawn" if drawn else "shadow_bow_h20")
    art=json.loads((ART/("shadow_bow_h22_drawn.bbmodel" if drawn else "shadow_bow_h20.bbmodel")).read_text())
    tail=5 if drawn else 1
    for e,b in zip(old["elements"][-tail:],art["elements"][-tail:]):
        if not drawn:b=copy.deepcopy(b);b["name"]="rest_string"
        p.inherited(e,b)
    return p
def generate():
    output={};meta={"source":"Independent cuboid reconstruction from cited visual references; no extracted assets", "models":{}}
    for p in (arc(),bow(True),bow(False)):
        files=p.files();output.update(files)
        meta["models"][p.name]={"cuboids":len(p.bb),"triangles":len(p.bb)*12,"display":p.model["display"],"geometry_sha256":hashlib.sha256(encode(p.model)).hexdigest()}
    output[ART/"super_props_h27.manifest.json"]=encode(meta)
    return output
if __name__=="__main__":
    verify=sys.argv[1:]==["--verify"]
    for path,data in generate().items():
        if verify:assert path.read_bytes()==data,path
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        print("verified" if verify else "wrote",path.relative_to(ROOT))
