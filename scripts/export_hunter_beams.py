#!/usr/bin/env python3
"""Author unit-length flame/tether item models through NEW Blockbench MCP projects."""
import base64
import json
from pathlib import Path
from export_hunter_props import Blockbench, write_json

ROOT = Path(__file__).resolve().parents[1]

def main():
    bb=Blockbench("http://localhost:3000/bb-mcp")
    for variant, colors in [("solar_trail",["#FFF4C9","#FFD56B","#FF872B","#D44422"]),
                            ("void_link",["#F4DFFF","#D3A3FF","#995CE2","#4D2B73"])]:
        name=variant+"_h15"
        created=bb.tool("create_project",{"name":name,"format":"java_block"})
        uid=next(c["uri"].split("/")[-1].removesuffix(".bbmodel") for c in created["content"] if c["type"]=="resource_link")
        select="ModelProject.all.find(p=>p.uuid==="+json.dumps(uid)+").select();"
        code="""
        (()=>{
          Undo.initEdit({elements:[],textures:[],outliner:true});
          Project.texture_width=Project.texture_height=128;
          const cv=document.createElement("canvas");cv.width=cv.height=128;
          const ctx=cv.getContext("2d");colors.forEach((c,i)=>{ctx.fillStyle=c;ctx.fillRect(i*32,0,32,128);});
          const tex=new Texture({name:name+".png",id:"0"}).fromDataURL(cv.toDataURL());tex.add(false);
          const root=new Group({name:"beam",origin:[8,8,8]}).init(),made=[];
          function rod(n,a,b,w,m){
            const mid=a.map((v,i)=>(v+b[i])/2),d=b.map((v,i)=>v-a[i]),length=Math.hypot(...d);
            const yaw=Math.atan2(-d[0],-d[2])*180/Math.PI,pitch=Math.asin(d[1]/length)*180/Math.PI;
            const faces={};for(const side of ["north","south","east","west","up","down"])faces[side]={texture:tex.uuid,uv:[m*32+2,2,m*32+30,126]};
            made.push(new Cube({name:n,from:[mid[0]-w/2,mid[1]-w/2,mid[2]-length/2],to:[mid[0]+w/2,mid[1]+w/2,mid[2]+length/2],origin:mid,rotation:[pitch,yaw,0],box_uv:false,autouv:0,faces}).addTo(root).init());
          }
          for(let i=0;i<16;i++)rod("bright_spine_"+i,[8,8,8-i],[8,8,7-i],.085,0);
          for(let strand=0;strand<2;strand++){
            const points=Array.from({length:17},(_,i)=>{const t=i/16,a=t*Math.PI*4+strand*Math.PI;
              const radius=(variant==="void_link"?.26:.40)*Math.sin(t*Math.PI);
              return [8+Math.sin(a)*radius,8+Math.cos(a)*radius,8-t*16];});
            for(let i=0;i<16;i++)rod("spiral_"+strand+"_"+i,points[i],points[i+1],variant==="void_link"?.07:.10,strand+1);
          }
          Undo.finishEdit("Author H15 "+variant+" unit beam",{elements:made,textures:[tex],outliner:true});Canvas.updateAll();
          const model=Codecs.java_block.compile({raw:true});
          model.textures={particle:"destiny:item/fx/"+name,"0":"destiny:item/fx/"+name};
          model.ambientocclusion=false;model.display={fixed:{rotation:[0,0,0],translation:[0,0,0],scale:[1,1,1]}};
          return {model,project:Codecs.project.compile({raw:true,absolute_paths:false}),texture:tex.getDataURL(),cubes:made.length};
        })()
        """
        data=bb.evaluate(select+"const colors="+json.dumps(colors)+",variant="+json.dumps(variant)+",name="+json.dumps(name)+";"+code)
        write_json(ROOT/f"src/main/resources/assets/destiny/models/fx/{name}.json",data["model"])
        write_json(ROOT/f"src/main/resources/assets/destiny/items/fx/{name}.json",{"model":{"type":"minecraft:model","model":"destiny:fx/"+name}})
        path=ROOT/f"art/blockbench/vfx/{name}.bbmodel";write_json(path,data["project"])
        texpath=ROOT/f"src/main/resources/assets/destiny/textures/item/fx/{name}.png";texpath.parent.mkdir(parents=True,exist_ok=True)
        texpath.write_bytes(base64.b64decode(data["texture"].split(",")[1]))
        bb.evaluate(select+"Project.save_path="+json.dumps(str(path))+";Project.saved=true;true")
        print(name,data["cubes"],"cubes; -Z unit beam",flush=True)

if __name__=="__main__":main()
