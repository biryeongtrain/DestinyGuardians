// Blockbench Generic Model, authored through MCP with Undo; no filesystem/native APIs.
// Original geometry/atlases. Actual references and limits: docs/design/15_헌터_VFX_레퍼런스.md.
(() => {
    if (Cube.all.length || Texture.all.length) throw new Error("Use an empty free model");
    const name = vfxName;
    const variant = name.replace("destiny_vfx_", "").replace("_h13", "");
    const palettes = {
        arc: ["#F4FCFF", "#B7F3FF", "#51CFFF", "#2477BC"],
        solar: ["#FFF3BE", "#FFD15B", "#FF872B", "#BE351A"],
        vortex: ["#F2D7FF", "#C589FA", "#7446B9", "#271B42"],
        smoke: ["#B4A8C6", "#877991", "#62596F", "#443D54"]
    };
    const palette = palettes[variant];
    if (!palette) throw new Error("Unknown VFX");
    Undo.initEdit({elements:[],textures:[],outliner:true});
    Project.name = name; Project.model_identifier = name;
    Project.texture_width = 32; Project.texture_height = 32; Project.ambientocclusion = false;
    Project.credit = "Destiny reference-based low-poly VFX reconstruction; no original meshes/textures; source notes in docs";
    const canvas = document.createElement("canvas"); canvas.width = 32; canvas.height = 32;
    const ctx = canvas.getContext("2d");
    palette.forEach((color, i) => {
        ctx.fillStyle = color; ctx.fillRect(i*8,0,8,32);
        if (variant === "smoke") {
            for(let x=0;x<8;x++)for(let y=0;y<32;y++)
                if ((x+y*3)%5<2 || Math.hypot(x-3.5,(y%8)-3.5)>4.1) ctx.clearRect(i*8+x,y,1,1);
        } else {
            ctx.fillStyle = "rgba(255,255,255,0.1)"; ctx.fillRect(i*8,0,3,32);
        }
    });
    if (variant === "solar") {
        ctx.clearRect(0,8,32,24);
        for (let x=0;x<32;x++) for (let y=8;y<32;y++) {
            const t=(y-8)/23, center=15.5 + Math.sin(t*9)*2.2;
            const edge=Math.abs(x-center)/(1+t*14);
            if (edge>1 || (t<.25 && (x+y)%6===0)) continue;
            ctx.fillStyle=edge<.27 ? palette[0] : edge<.52 ? palette[1] : edge<.82 ? palette[2] : palette[3];
            ctx.fillRect(x,y,1,1);
        }
    }
    const tex = new Texture({name:name+".png",id:"0",particle:true}).fromDataURL(canvas.toDataURL()); tex.add(false);
    const root = new Group({name:"root",origin:[0,0,0]}).init();
    const groups = {}; const made=[]; const bones={};
    function group(n, origin=[0,0,0]) {groups[n]=new Group({name:n,origin}).addTo(root).init();return n;}
    function box(g,n,c,size,mat,rot=[0,0,0]) {
        const f=c.map((v,i)=>v-size[i]/2),t=c.map((v,i)=>v+size[i]/2),faces={};
        for(const side of ["north","south","east","west","up","down"])
            faces[side]={uv:[mat*8,0,mat*8+8,8],texture:tex.uuid};
        const cube = new Cube({name:n,from:f,to:t,origin:c,rotation:rot,box_uv:false,autouv:0,faces}).addTo(groups[g]).init();
        cube.light_emission=15; made.push(cube);
        return cube;
    }
    function ring(g,r,y,thick,mat,segments=16,gaps=0) {
        for(let i=0;i<segments;i++){
            if(gaps&&i%gaps===0)continue;
            const a=i*360/segments,rad=a*Math.PI/180;
            let angle=a,swap=false;
            while(angle>45){angle-=90;swap=!swap;}while(angle< -45){angle+=90;swap=!swap;}
            const len=2*r*Math.tan(Math.PI/segments)*.94;
            box(g,g+"_segment_"+i,[Math.sin(rad)*r,y,Math.cos(rad)*r],swap?[thick,.30,len]:[len,.30,thick],mat,[0,angle,0]);
        }
    }
    function scaleKeys(times,values){return times.map((time,i)=>({time,scale:[values[i],values[i],values[i]]}));}
    if(variant==="arc") {
        group("core");group("wave");
        box("core","white_snap",[0,1,0],[3.5,3.5,3.5],0,[0,45,0]);
        box("core","cross_x",[0,1,0],[9,.9,.9],1);box("core","cross_z",[0,1,0],[.9,.9,9],1);
        ring("wave",15,.3,.35,2);
        bones.core=scaleKeys([0,.05,.15,.35,.8],[.05,1.15,.6,.02,.01]);
        bones.wave=scaleKeys([0,.10,.30,.65,.8],[.05,.4,1,1.17,.01]);
        for(let i=0;i<4;i++) {
            const n=group("bolt_"+i),a=i*Math.PI/2;
            for(let j=0;j<4;j++){
                const r=4+j*2.6,offset=j%2?1.2:-.7;
                const x=Math.sin(a)*r+Math.cos(a)*offset,z=Math.cos(a)*r-Math.sin(a)*offset;
                box(n,n+"_jag_"+j,[x,.6+j*.25,z],[i%2?3.5:.38,.38,i%2?.38:3.5],j%2?0:2,[0,((i+j)%2?22.5:-22.5),0]);
            }
            bones[n]=scaleKeys([0,.05,.15,.3,.55,.8],[.1,1,.83,1.1,.01,.01]);
            bones[n].push({time:0,rotation:[0,-4,0]},{time:.10,rotation:[0,7,0]},{time:.25,rotation:[0,-8,0]},{time:.55,rotation:[0,2,0]});
        }
    } else if(variant==="solar") {
        group("core"); group("wave");
        box("core","hot_seed",[0,1.6,0],[4,3.4,4],0,[0,45,0]);
        box("core","hot_vertical",[0,2,0],[1.3,8,1.3],0,[0,0,22.5]);
        ring("wave",13,.3,.65,2,16,4);
        bones.core=scaleKeys([0,.1,.25,.6,1.1],[.04,1.25,.7,.05,.01]);
        bones.wave=scaleKeys([0,.1,.4,.8,1.1],[.05,.45,1,1.15,.01]);
        for(let i=0;i<6;i++) {
            const a=i*Math.PI/3,x=Math.sin(a)*5,z=Math.cos(a)*5,n=group("flame_"+i,[x,0,z]);
            groups[n].rotation=[-Math.cos(a)*42,0,Math.sin(a)*42];
            for (let side=0;side<2;side++) {
                const flame=box(n,n+"_cutout_"+side,[x,3.2,z],side?[.08,6.4,3.2]:[3.2,6.4,.08],2);
                for (const [direction,face] of Object.entries(flame.faces)) {
                    face.uv=[0,8,32,32];
                    if (!(side ? ["east","west"] : ["north","south"]).includes(direction)) face.texture=null;
                }
            }
            box(n,n+"_ember",[x+.8,8+(i%3),z],[.3,.9,.3],1,[0,0,22.5]);
            bones[n]=scaleKeys([0,.1,.3,.65,1.1],[.05,1,.8,.45,.01]);
            bones[n].push({time:0,position:[0,0,0]},{time:.25,position:[Math.sin(a)*5,1.5,Math.cos(a)*5]},
                {time:.65,position:[Math.sin(a)*9,3,Math.cos(a)*9]},{time:1.1,position:[Math.sin(a)*11,4,Math.cos(a)*11]});
        }
    } else if(variant==="vortex") {
        group("core");group("outer");group("inner");group("wisps");
        box("core","pink_white_seed",[0,2,0],[2.5,2.5,2.5],0,[0,45,0]);
        box("core","bright_filament_x",[0,2,0],[6,.3,.3],0);
        box("core","bright_filament_z",[0,2,0],[.3,.3,6],0);
        ring("core",3.4,2.1,.5,0,12,3);
        ring("outer",15,.3,.55,2,16,4);ring("outer",16,.45,.2,1,16,4);
        ring("inner",10,1.2,.4,1,16,3);
        for(let i=0;i<8;i++){
            const a=i*Math.PI/4,r=5+i%3;
            box("wisps","infall_"+i,[Math.sin(a)*r,1+i%4,Math.cos(a)*r],[.4,.45,2.8],i%2?0:1,[0,i%2?45:0,0]);
        }
        bones.core=scaleKeys([0,.5,1],[.65,1,.65]);
        bones.outer=[{time:0,rotation:[0,0,0]},{time:.5,rotation:[0,90,0]},{time:1,rotation:[0,180,0]}];
        bones.inner=[{time:0,rotation:[0,0,0],scale:1},{time:.5,rotation:[0,-180,0],scale:.83},{time:1,rotation:[0,-360,0],scale:1}];
        bones.wisps=[{time:0,rotation:[0,0,0],scale:1},{time:.5,rotation:[0,90,0],scale:.5},{time:1,rotation:[0,180,0],scale:1}];
    } else {
        for(let i=0;i<6;i++){
            const a=i*Math.PI/3,x=Math.sin(a)*8,z=Math.cos(a)*8,y=3+(i%3)*2,n=group("plume_"+i,[x,y,z]);
            const size=6+(i%2);
            box(n,n+"_billow_x",[x,y,z],[size,size*.50,size*.65],i%3,[0,45,0]);
            box(n,n+"_billow_y",[x,y,z],[size*.65,size*.8,size*.65],i%3,[0,45,0]);
            box(n,n+"_billow_z",[x,y,z],[size*.65,size*.50,size],i%3,[0,45,0]);
            box(n,n+"_facet",[x,y+size*.3,z],[size*.64,size*.55,size*.64],(i+1)%4);
            bones[n]=[{time:0,scale:.65,position:[0,-1,0],rotation:[0,-8,0]},
                {time:1,scale:1,position:[0,1.2,0],rotation:[0,12,0]},
                {time:2,scale:.65,position:[0,-1,0],rotation:[0,-8,0]}];
        }
    }
    Undo.finishEdit("Author H13 low-poly "+variant+" VFX",{elements:made,textures:[tex],outliner:true});
    Canvas.updateAll();
    return {name,variant,cubes:made.length,renderBones:Object.keys(groups).length,bones,
        animation:(variant==="arc"||variant==="solar")?"spawn":"loop",
        duration:variant==="arc"?.8:variant==="solar"?1.1:variant==="smoke"?2:1};
})()
