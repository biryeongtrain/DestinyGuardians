// Executed inside Blockbench through MCP risky_eval; orchestrator supplies propName.
// Original cubes and atlas; H12 source-verified knife/flashbang, other H11 props provisional; references: docs/design/14_헌터_능력_모델.md.
(() => {
    const name = propName;
    if (Cube.all.length || Texture.all.length) throw new Error("Use a new empty java_block project");
    const palette = {
        arc_flashbang: ["#343E48", "#DFE2DF", "#1C252D", "#56626B", "#9AA4AA", "#757F84", "#F1F0E7", "#11191F"],
        solar_incendiary: ["#B96535", "#EFB565", "#523C30", "#33303A", "#FFD263", "#E75626", "#FFF0B1", "#211E25"],
        void_vortex: ["#786E9A", "#C2B8DA", "#40364E", "#292637", "#D898FF", "#8F49CE", "#F2D7FF", "#171523"],
        solar_knife: ["#575B60", "#8F9398", "#34393F", "#22262C", "#686C71", "#494D52", "#B1B4B7", "#14191F"],
        void_smoke_bomb: ["#62776C", "#B8B8AC", "#35453E", "#292F32", "#C29AEF", "#8B64A2", "#E0D7E8", "#181F23"]
    }[name];
    if (!palette) throw new Error("Unknown prop " + name);
    Undo.initEdit({elements:[],textures:[],outliner:true});
    Project.texture_width = 64; Project.texture_height = 32;
    Project.credit = "New Blockbench reconstruction; Destiny design copyright Bungie. H12 verified references/status in docs and manifest";
    Project.ambientocclusion = false;
    const canvas = document.createElement("canvas"); canvas.width=64; canvas.height=32;
    const ctx=canvas.getContext("2d");
    palette.forEach((color,i) => {
        const x=i*8; ctx.fillStyle=color; ctx.fillRect(x,0,8,32);
        if(name==="solar_knife") {
            for(let j=0;j<13;j++){ctx.fillStyle=j%2?"rgba(0,0,0,0.04)":"rgba(255,255,255,0.05)";ctx.fillRect(x+(j*3+i)%8,(j*7+i)%32,1+(j%3),1);}
            return;
        }
        ctx.fillStyle="rgba(255,255,255,0.16)"; ctx.fillRect(x+1,1,6,1); ctx.fillRect(x+1,1,1,6);
        ctx.fillStyle="rgba(0,0,0,0.20)"; ctx.fillRect(x,7,8,1); ctx.fillRect(x+7,0,1,8);
        for(let y=10;y<32;y+=4) {ctx.fillStyle="rgba(0,0,0,0.12)"; ctx.fillRect(x+((y+i)%6),y,2,1);}
        ctx.fillStyle="rgba(255,255,255,0.12)";ctx.fillRect(x+3,18,3,1);
    });
    const tex=new Texture({name:name+".png",id:"0",namespace:"destiny",folder:"item/hunter",particle:true}).fromDataURL(canvas.toDataURL());tex.add(false);
    const root=new Group({name:"root",origin:[8,8,8]}).init();
    const groups={};
    for(const key of ["shell","hardware","energy"]) groups[key]=new Group({name:key,origin:[8,8,8]}).addTo(root).init();
    const made=[];
    function box(n,f,t,mat=0,group="shell",rot=null,origin=[8,8,8]) {
        const faces={};
        for(const side of ["north","south","east","west","up","down"]) faces[side]={uv:[mat*8+.5,.5,mat*8+7.5,7.5],texture:tex.uuid};
        const c=new Cube({name:n,from:f,to:t,origin,rotation:rot||[0,0,0],box_uv:false,autouv:0,faces}).addTo(groups[group]).init();
        if(name!=="solar_knife"&&name!=="arc_flashbang"&&(mat===4||mat===6))c.light_emission=8;
        made.push(c);return c;
    }
    function belt(y,h,r,mat,n) {
        box(n+"_cross_x",[8-r,y,8-r*.70],[8+r,y+h,8+r*.70],mat);
        box(n+"_cross_z",[8-r*.70,y,8-r],[8+r*.70,y+h,8+r],mat);
    }
    function pin(y) {
        box("fuse_neck",[7.15,y,7.15],[8.85,y+1.5,8.85],2,"hardware");
        box("lever",[7.2,y+1.3,6.8],[11.7,y+1.8,7.7],1,"hardware",[0,0,-22.5],[8,y+1.5,8]);
        box("ring_left",[5.9,y+1.3,7.7],[6.3,y+3.4,8.1],1,"hardware");
        box("ring_right",[8.1,y+1.3,7.7],[8.5,y+3.4,8.1],1,"hardware");
        box("ring_top",[6.3,y+3,7.7],[8.1,y+3.4,8.1],1,"hardware");
        box("ring_bottom",[6.3,y+1.3,7.7],[8.1,y+1.7,8.1],1,"hardware");
    }
    if(name==="arc_flashbang") {
        // The game screenshot shows a studded dark bulb, white tapered cap and side lever.
        const layers=[[3.2,.6,1.55],[3.8,.9,2.1],[4.7,1.2,2.55],[5.9,2.2,2.8],[8.1,1.1,2.6],[9.2,.6,2.35]];
        for(let i=0;i<layers.length;i++){const [y,h,r]=layers[i];belt(y,h,r,0,"bulb_"+i);}
        belt(9.8,.55,2.65,2,"cap_seam");belt(10.35,.7,2.7,1,"white_collar");
        belt(11.05,.65,2.25,1,"white_taper_lower");belt(11.7,.65,1.8,1,"white_taper_middle");
        belt(12.35,.65,1.3,1,"white_taper_top");belt(13,.65,.9,6,"fuse_crown");
        box("crown_slot",[7.35,13.65,7.8],[8.65,13.72,8.05],7,"hardware");
        box("lever_spine",[4.85,5.4,7.5],[5.3,12.25,8.5],2,"hardware",[0,0,-22.5],[5.15,11,8]);
        box("lever_top",[5.1,12,7.5],[7.1,12.6,8.5],2,"hardware");
        box("lever_hinge",[6.6,11.8,7.35],[7.4,12.7,8.65],3,"hardware");
        for(const y of [5.3,7.6,9])for(const x of [6.7,9.3]) {
            for(const z of [5.07,10.65]) {
                box("body_stud_"+x+"_"+y+"_"+z,[x-.31,y-.31,z],[x+.31,y+.31,z+.28],2,"hardware");
                box("stud_recess_"+x+"_"+y+"_"+z,[x-.11,y-.11,z-.02],[x+.11,y+.11,z+.3],5,"hardware");
            }
        }
        for(const x of [5.05,10.65])for(const y of [5.8,8.2])
            box("side_stud_"+x+"_"+y,[x,y-.3,7.7],[x+.3,y+.3,8.3],2,"hardware");
    } else if(name==="solar_incendiary") {
        belt(4,7,3.2,0,"fuel_body");belt(2.7,1.4,2.5,2,"base");belt(10.9,1.3,2.5,2,"cap");
        belt(6.5,1.4,3.35,5,"hazard_band");
        for(const x of [5.6,9.6])for(const z of [5.3,10.15])box("thermal_fin_"+x+"_"+z,[x,4.3,z],[x+.8,10.7,z+.55],1,"hardware");
        box("igniter",[7.1,12.1,7.1],[8.9,13.8,8.9],1,"hardware");
        box("flame_core",[7,5.5,4.4],[9,9.2,4.8],4,"energy");
        for(let i=0;i<3;i++)box("dark_warning_"+i,[5.8+i*1.4,6.8,4.45],[6.4+i*1.4,7.5,4.7],7,"hardware");
        box("fuse_tab",[8.9,12.5,7.5],[11.1,13.2,8.5],2,"hardware");
    } else if(name==="void_vortex") {
        belt(3.2,8,2.55,0,"reactor");
        for(const y of [2.3,3.3,10.6,11.6])belt(y,.65,3.2,2,"magnetic_coil_"+y);
        for(const x of [5.3,10.1]) {
            box("purple_rail_"+x,[x,4,5.2],[x+.6,10.4,5.65],4,"energy");
            box("back_rail_"+x,[x,4,10.35],[x+.6,10.4,10.8],5,"energy");
        }
        box("dark_core_socket",[6.1,5.2,4.95],[9.9,9.2,5.3],7,"hardware");
        box("vortex_crystal",[6.85,6.15,4.6],[9.15,8.45,5.1],4,"energy",[0,0,45],[8,7.3,4.8]);
        for(const x of [5.5,9.8])box("base_claw_"+x,[x,1.4,7.35],[x+.7,3.5,8.65],1,"hardware");
        pin(12.1);
    } else if(name==="solar_knife") {
        // Side silhouette traced from Bungie's Hunter knife reference; tip is local -Z.
        // Original textures are NOT sampled. Empty regions are actual holes through the cuboids.
        const blade=[[2028,43],[1360,24],[1562,77],[1580,94],[1564,113],[1530,121],
            [1200,56],[810,52],[748,100],[654,130],[560,134],[530,196],[570,296],
            [610,295],[651,312],[664,341],[790,350],[1200,355],[1430,335],[1620,290],
            [1770,240],[1920,140]];
        const grip=[[560,134],[475,119],[370,100],[220,112],[115,128],[50,165],[22,213],
            [20,282],[42,332],[94,364],[148,368],[192,338],[216,279],[250,256],
            [328,246],[405,264],[438,316],[480,337],[535,332],[572,302],[593,252],[583,184]];
        const holes=[[1236,193,56],[503,253,53],[120,279,59]];
        function inside(x,y,poly) {
            let hit=false;
            for(let i=0,j=poly.length-1;i<poly.length;j=i++){
                const a=poly[i],b=poly[j];
                if(((a[1]>y)!==(b[1]>y))&&(x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]))hit=!hit;
            }return hit;
        }
        const step=.125;const active=new Map();const rects=[];
        for(let zi=0;zi<128;zi++){
            const z=(zi+.5)*step;const px=(16-z)*128;
            const spans=[];let start=-1;let prev=-1;
            for(let xi=0;xi<=32;xi++){
                const x=6+(xi+.5)*step;const py=(x-6.2)*115;
                let mat=-1;
                if(xi<32&&(inside(px,py,blade)||inside(px,py,grip))&&!holes.some(h=>Math.hypot(px-h[0],py-h[1])<h[2])){
                    mat=px<550?3:(py>300?1:0);
                    if(px<550&&(Math.floor((px+py*.42)/24)%3===0))mat=2;
                }
                if(mat!==prev){if(prev>=0)spans.push([start,xi,prev]);start=xi;prev=mat;}
            }
            const keys=new Set();
            for(const [a,b,mat] of spans){const key=a+","+b+","+mat;keys.add(key);let r=active.get(key);
                if(r)r.z1=zi+1;else{r={a,b,mat,z0:zi,z1:zi+1};active.set(key,r);rects.push(r);}}
            for(const key of active.keys())if(!keys.has(key))active.delete(key);
        }
        rects.forEach((r,i)=>box("silhouette_"+i,[6+r.a*step,7.84,r.z0*step],[6+r.b*step,8.16,r.z1*step],r.mat));
        for(const yy of [7.80,8.16])for(let i=0;i<3;i++){
            const z=8.5+i*.48;
            box("hunter_chevron_left_"+yy+"_"+i,[7.15,yy,z],[7.82,yy+.04,z+.10],2,"hardware",[0,-22.5,0],[7.82,8,z]);
            box("hunter_chevron_right_"+yy+"_"+i,[7.82,yy,z],[8.49,yy+.04,z+.10],2,"hardware",[0,22.5,0],[7.82,8,z]);
        }
    } else {
        belt(3.7,6.8,3.05,0,"canister");belt(2.8,1,3.2,2,"base");belt(10.3,1,3.2,2,"lid");
        belt(6.9,1.6,3.15,5,"violet_id_band");
        for(const x of [6,8.9])for(const y of [4.5,5.7,8.9])box("vent_"+x+"_"+y,[x,y,4.85],[x+1.1,y+.55,5.2],7,"hardware");
        box("label_plate",[6.8,6.8,4.7],[9.2,8.5,5.1],1,"hardware");
        box("violet_label",[7.5,7.05,4.6],[8.5,8.2,4.8],4,"energy");
        box("nozzle",[10.8,9.3,7.2],[12,10.2,8.8],1,"hardware");
        box("nozzle_hole",[11.95,9.5,7.6],[12.15,10,8.4],7,"hardware");pin(11.2);
    }
    Project.display_settings.gui=new DisplaySlot("gui",{rotation:[25,35,0],scale:[1.1,1.1,1.1]});
    Project.display_settings.ground=new DisplaySlot("ground",{translation:[0,3,0],scale:[.7,.7,.7]});
    Project.display_settings.fixed=new DisplaySlot("fixed",{scale:[1,1,1]});
    Project.display_settings.thirdperson_righthand=new DisplaySlot("thirdperson_righthand",{scale:[.8,.8,.8]});
    Project.display_settings.firstperson_righthand=new DisplaySlot("firstperson_righthand",{rotation:[0,-25,0],translation:[1,1,0],scale:[.8,.8,.8]});
    Undo.finishEdit("Create original hunter "+name,{elements:made,textures:[tex],outliner:true});
    Canvas.updateAll();
    return {name,cubes:made.length,texture:tex.javaTextureLink(),project:Project.uuid};
})()
