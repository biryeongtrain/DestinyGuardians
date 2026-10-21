// Executed inside Blockbench through MCP risky_eval; orchestrator supplies propName.
// Original cubes and atlas; visual references: docs/design/14_헌터_능력_모델.md.
(() => {
    const name = propName;
    if (Cube.all.length || Texture.all.length) throw new Error("Use a new empty java_block project");
    const palette = {
        arc_flashbang: ["#9BAEBB", "#DFEAF0", "#354956", "#28323D", "#72E5FF", "#2E9CB5", "#F4FCFF", "#131D27"],
        solar_incendiary: ["#B96535", "#EFB565", "#523C30", "#33303A", "#FFD263", "#E75626", "#FFF0B1", "#211E25"],
        void_vortex: ["#786E9A", "#C2B8DA", "#40364E", "#292637", "#D898FF", "#8F49CE", "#F2D7FF", "#171523"],
        solar_knife: ["#AFBBC4", "#E4EDF1", "#495463", "#493627", "#FFCC63", "#C9823D", "#FFF1C1", "#1F252D"],
        void_smoke_bomb: ["#62776C", "#B8B8AC", "#35453E", "#292F32", "#C29AEF", "#8B64A2", "#E0D7E8", "#181F23"]
    }[name];
    if (!palette) throw new Error("Unknown prop " + name);
    Undo.initEdit({elements:[],textures:[],outliner:true});
    Project.texture_width = 64; Project.texture_height = 32;
    Project.credit = "Original Destiny Guardians props, AI-assisted in Blockbench MCP; references credited in docs";
    Project.ambientocclusion = false;
    const canvas = document.createElement("canvas"); canvas.width=64; canvas.height=32;
    const ctx=canvas.getContext("2d");
    palette.forEach((color,i) => {
        const x=i*8; ctx.fillStyle=color; ctx.fillRect(x,0,8,32);
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
        if(mat===4||mat===6)c.light_emission=8;
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
        belt(3,8,2.6,0,"ceramic_body");belt(2.6,.8,2.9,2,"base");belt(10.8,.9,2.9,2,"cap");
        for(const y of [4,6.4,8.8]) {
            box("north_vent_"+y,[6,y,5.3],[10,y+.8,5.65],7,"hardware");
            box("south_vent_"+y,[6,y,10.35],[10,y+.8,10.7],7,"hardware");
            box("east_vent_"+y,[10.35,y,6],[10.7,y+.8,10],7,"hardware");
            box("west_vent_"+y,[5.3,y,6],[5.65,y+.8,10],7,"hardware");
        }
        for(const x of [6,9.4])box("cyan_conduit_"+x,[x,3.5,5.1],[x+.6,10.3,5.4],4,"energy");
        box("charge_window",[7.2,6.3,4.95],[8.8,8.2,5.2],4,"energy");pin(11.4);
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
        // Blade points along -Z; the fixed projectile orientation follows velocity.
        box("blade_centre",[6.8,7.6,3],[9.2,8.4,9.3],0);
        box("blade_tip",[7.65,7.7,.2],[8.35,8.3,3.3],1);
        box("blade_tip_step",[7.2,7.65,1.8],[8.8,8.35,4.4],1);
        box("left_bevel",[6.35,7.85,3.6],[6.85,8.15,8.9],1);
        box("right_bevel",[9.15,7.85,3.6],[9.65,8.15,8.9],1);
        box("blade_spine",[7.7,8.4,3.4],[8.3,8.65,9.1],2,"hardware");
        box("solar_inlay",[7.83,8.66,4.2],[8.17,8.8,8.3],4,"energy");
        box("guard",[5.8,7.25,9.1],[10.2,8.75,10],5,"hardware");
        box("grip",[7.1,7.15,10],[8.9,8.85,14.6],3,"hardware");
        for(let i=0;i<5;i++)box("grip_wrap_"+i,[6.95,7,10.2+i*.8],[9.05,9,10.55+i*.8],2,"hardware");
        box("pommel",[6.8,6.95,14.5],[9.2,9.05,15.4],5,"hardware");
        box("pommel_gem",[7.4,7.5,15.35],[8.6,8.5,15.7],4,"energy");
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
