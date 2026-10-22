// Runs only through Blockbench MCP, in a NEW empty Java Block/Item tab.
// Original reconstruction from fetched Destiny references; no extracted game geometry or textures.
(() => {
    if (Project.uuid !== superProjectId || Cube.all.length || Texture.all.length)
        throw new Error("Expected the new empty H15 project UUID");
    const name = superName;
    const palettes = {
        arc_staff:["#163A57","#366887","#76B9D5","#183040","#25B8F1","#99EBFF","#E8FDFF","#071825"],
        golden_gun:["#A64A16","#F0A52A","#FFD475","#512218","#F26A15","#FFD45E","#FFF2B3","#25191B"],
        shadow_bow:["#25183E","#4D3079","#8562B6","#150F29","#9A59ED","#D29CFF","#F7DFFF","#0B0916"],
        shadow_arrow:["#25183E","#4D3079","#8562B6","#150F29","#9A59ED","#D29CFF","#F7DFFF","#0B0916"]
    };
    const palette=palettes[name]; if(!palette) throw new Error("Unknown super");
    Undo.initEdit({elements:[],textures:[],outliner:true,display_slots:Object.keys(superDisplay)});
    Project.texture_width=256;Project.texture_height=128;Project.ambientocclusion=false;
    Project.credit="H15 original Blockbench reconstruction; Destiny designs copyright Bungie; references and caveats in supers manifest";
    const canvas=document.createElement("canvas");canvas.width=256;canvas.height=128;
    const ctx=canvas.getContext("2d");
    palette.forEach((color,m)=>{
        const x=m*32;ctx.fillStyle=color;ctx.fillRect(x,0,32,128);
        for(let y=0;y<128;y++){
            ctx.fillStyle="rgba(255,255,255,"+(0.025+0.10*Math.pow(Math.sin(y/128*Math.PI),2))+")";
            ctx.fillRect(x+1,y,30,1);
        }
        ctx.fillStyle="rgba(255,255,255,.20)";ctx.fillRect(x+2,2,28,1);ctx.fillRect(x+2,2,1,25);
        ctx.fillStyle="rgba(0,0,0,.22)";ctx.fillRect(x+29,3,1,26);ctx.fillRect(x+2,29,28,1);
        for(let i=0;i<45;i++){
            ctx.fillStyle=i%3?"rgba(255,255,255,.08)":"rgba(0,0,0,.10)";
            ctx.fillRect(x+3+(i*7+m)%25,34+(i*13)%89,1+i%4,1);
        }
        if(m===3){for(let y=36;y<125;y+=6){ctx.fillStyle="rgba(0,0,0,.22)";ctx.fillRect(x+2,y,28,2);}}
        if(m===4||m===5){
            ctx.strokeStyle=palette[6];ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(x+15,34);
            for(let y=36;y<126;y+=7)ctx.lineTo(x+8+(y*11)%17,y);ctx.stroke();
        }
    });
    const tex=new Texture({name:name+".png",id:"0",namespace:"destiny",folder:"item/supers",particle:true}).fromDataURL(canvas.toDataURL());tex.add(false);
    const root=new Group({name:name,origin:[8,8,8]}).init();
    const groups={};for(const n of ["structure","plating","hardware","inlay","energy","string"])groups[n]=new Group({name:n,origin:[8,8,8]}).addTo(root).init();
    const made=[];
    function box(n,f,t,m=0,g="structure",rot=[0,0,0],origin=[8,8,8]){
        const faces={};
        for(const s of ["north","south","east","west","up","down"]){
            const detail=(n.length+made.length)%3;
            faces[s]={uv:[m*32+3,detail?36:3,m*32+29,detail?124:29],texture:tex.uuid};
        }
        const c=new Cube({name:n,from:f,to:t,origin,rotation:rot,box_uv:false,autouv:0,faces}).addTo(groups[g]).init();
        if(m>=4&&m<=6){c.light_emission=m===6?15:10;c.shade=false;}
        made.push(c);return c;
    }
    function collar(n,y,h,r,m=1){
        box(n+"_x",[8-r,y,8-r*.72],[8+r,y+h,8+r*.72],m,"plating");
        box(n+"_z",[8-r*.72,y,8-r],[8+r*.72,y+h,8+r],m,"plating");
    }
    function strip(n,a,b,width,depth,m,g="energy"){
        const dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy);
        const mid=[(a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2];
        let ang=-Math.atan2(dx,dy)*180/Math.PI;
        while(ang>90)ang-=180;while(ang<-90)ang+=180;
        // Portable Java block angles: overlapping short sections approximate curves.
        const horizontal=Math.abs(ang)>45;
        if(horizontal)ang=ang>0?ang-90:ang+90;
        ang=Math.round(ang/22.5)*22.5;
        const sx=horizontal?len+.07:width,sy=horizontal?width:len+.07;
        return box(n,[mid[0]-sx/2,mid[1]-sy/2,mid[2]-depth/2],
            [mid[0]+sx/2,mid[1]+sy/2,mid[2]+depth/2],m,g,[0,0,ang],mid);
    }
    if(name==="arc_staff"){
        collar("central_octagonal_shaft",-10.7,37.4,.47,0);
        for(let i=0;i<15;i++){
            const y=-10.2+i*2.45;
            collar("shaft_segment_"+i,y,1.75,.59,i%3===0?1:0);
            collar("seam_ring_"+i,y+1.78,.17,.66,2);
            for(const x of [7.37,8.48])box("rail_"+i+"_"+x,[x,y+.12,7.66],[x+.15,y+1.55,8.34],4,"inlay");
            for(const z of [7.37,8.48])box("shaft_face_inlay_"+i+"_"+z,[7.77,y+.12,z],[8.23,y+1.55,z+.15],4,"inlay");
        }
        for(let i=0;i<13;i++)collar("central_grip_wrap_"+i,4.8+i*.49,.25,.67,3);
        for(const y of [-8.5,-3.6,14.8,19.7]){
            collar("armored_ferrule_"+y,y,.68,.85,1);
            collar("ferrule_lip_"+y,y+.08,.13,.9,2);
            for(const x of [7.08,8.76])box("locking_stud_"+x+"_"+y,[x,y+.24,7.57],[x+.16,y+.46,8.43],6,"hardware");
        }
        for(const sign of [-1,1]){
            const base=sign===1?25.7:-10.7;
            collar("end_socket_"+sign,base-.5,.9,.82,1);
            collar("socket_energy_band_"+sign,base-.15,.15,.87,5);
            for(const fork of [-1,1]){
                for(let i=0;i<7;i++){
                    const t=i/7,y=base+sign*(.5+t*4.1),x=8+fork*(.42+Math.sin(t*Math.PI*.85)*.85);
                    strip("fork_plate_"+sign+"_"+fork+"_"+i,[x,y,8],[x+fork*.09,y+sign*.66,8],.44*(1-t)+.09,.52*(1-t)+.08,1,"plating");
                    for(const z of [7.7,8.3])strip("electric_tip_"+sign+"_"+fork+"_"+i+"_"+z,[x,y,z],[x+fork*.09,y+sign*.66,z],.19*(1-t)+.05,.12, i%3?5:6);
                }
            }
            for(let i=0;i<4;i++){
                const y=base+sign*(.7+i*.65);
                strip("arc_bridge_"+sign+"_"+i,[7.8+(i%2)*.7,y,8],[8.6-(i%2)*.9,y+sign*.58,8],.07,.08,6);
            }
        }
    }else if(name==="golden_gun"){
        // Last Word side view: barrel to +Z, swept grip at rear, exposed round cylinder.
        box("lower_barrel_shroud",[7.03,9.15,7.1],[8.97,11.18,15.8],0);
        box("upper_gold_barrel",[7.07,11.18,5.05],[8.93,12.05,15.96],1,"plating");
        box("top_rail_highlight",[7.28,12.04,5.8],[8.72,12.14,15.7],2,"plating");
        box("receiver_bridge",[6.94,8.3,4.6],[9.06,11.4,8.6],0);
        box("cylinder_topstrap",[7.08,11.1,3.55],[8.92,12.28,6.6],1,"plating");
        box("rear_frame",[7.0,8.2,3.7],[9.0,11.2,4.9],0);
        // Round cross section composed of narrow horizontal strips, not a box cylinder.
        for(let i=0;i<20;i++){
            const y=8.5+i*.14,r=1.4,dy=y+.07-9.9,w=Math.sqrt(Math.max(0,r*r-dy*dy));
            box("cylinder_round_slice_"+i,[8-w,y,4.65],[8+w,y+.14,7.04],i<3||i>16?0:3,"hardware");
        }
        for(const side of [-1,1]){
            const x=8+side*1.4;
            for(let i=0;i<3;i++){
                const y=9.0+i*.66;
                box("cylinder_flute_"+side+"_"+i,[x-.05,y,4.86],[x+.05,y+.16,6.84],0,"hardware");
                box("cylinder_solar_etch_"+side+"_"+i,[x-.07,y+.03,5.25],[x+.07,y+.09,6.5],2,"inlay");
                for(let j=0;j<3;j++)box("cylinder_arrow_"+side+"_"+i+"_"+j,[x-.08,y-.015+j*.035,5.18+j*.12],[x+.08,y+.14-j*.035,5.23+j*.12],5,"inlay");
            }
            for(const z of [9.4,11.4,13.4])box("barrel_vent_"+side+"_"+z,[8+side*.94-.035,11.48,z],[8+side*.94+.035,11.7,z+1.24],7,"hardware");
            for(const y of [9.45,10.85])box("shroud_border_"+side+"_"+y,[8+side*.99-.04,y,8.7],[8+side*.99+.04,y+.08,15.6],2,"inlay");
            for(let j=0;j<14;j++){
                const z=8.9+j*.45;
                box("shroud_chevron_"+side+"_"+j,[8+side*1.01-.035,9.64,z],[8+side*1.01+.035,10.05,z+.09],1,"inlay",[side*22.5,0,0],[8,9.9,z]);
            }
            box("maker_inset_"+side,[8+side*1.01-.05,10.08,10],[8+side*1.01+.05,10.6,14.2],3,"inlay");
            for(let j=0;j<9;j++)box("maker_glyph_"+side+"_"+j,[8+side*1.03-.03,10.19,10.28+j*.4],[8+side*1.03+.03,10.46,10.39+j*.4],2,"inlay");
        }
        // Muzzle ring with a recessed bore, physically open at its front.
        for(const y of [9.2,10.9])box("muzzle_horizontal_"+y,[7.01,y,15.8],[8.99,y+.3,16.15],1,"hardware");
        for(const x of [7.01,8.69])box("muzzle_vertical_"+x,[x,9.5,15.8],[x+.3,10.9,16.15],1,"hardware");
        box("recessed_dark_bore",[7.31,9.5,15.7],[8.69,10.9,15.73],7,"hardware");
        box("front_sight",[7.76,12.13,14.6],[8.24,12.53,15.16],7,"hardware");
        for(const x of [7.42,8.34])box("rear_sight_"+x,[x,12.27,4.25],[x+.24,12.65,5.6],7,"hardware");
        box("hammer_spur",[7.65,10.75,2.95],[8.35,11.24,4.08],1,"hardware",[22.5,0,0],[8,10.8,3.9]);
        for(let i=0;i<14;i++){
            const y=3.05+i*.39,t=i/13,z=2.12+t*1.5,w=1.45-.20*t;
            box("swept_grip_frame_"+i,[8-w,y,z],[8+w,y+.4,z+2.14],0);
            for(const side of [-1,1]){
                const x=8+side*(w+.015);
                box("grip_panel_"+side+"_"+i,[x-.075,y,z+.18],[x+.075,y+.405,z+1.9],3,"plating");
                for(let j=0;j<3;j++)box("grip_checkering_"+side+"_"+i+"_"+j,[x-.09,y+.12,z+.3+j*.48],[x+.09,y+.2,z+.58+j*.48],0,"inlay");
            }
        }
        box("grip_heel",[6.48,2.9,2.05],[9.52,3.14,4.35],1,"hardware");
        // Open trigger guard: rims occupy only the perimeter.
        const guard=[[5.05,7.1],[5.6,6.8],[6.3,6.52],[7.1,6.5],[7.75,6.7],[8.2,7.1],[8.42,7.75],[8.45,8.4]];
        for(let i=0;i<guard.length-1;i++){
            const a=guard[i],b=guard[i+1],dz=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dz,dy);
            let ang=Math.atan2(dz,dy)*180/Math.PI;
            while(ang>90)ang-=180;while(ang<-90)ang+=180;
            const horizontal=Math.abs(ang)>45;
            if(horizontal)ang=ang>0?ang-90:ang+90;
            ang=Math.round(ang/22.5)*22.5;
            const cy=(a[1]+b[1])/2,cz=(a[0]+b[0])/2,sy=horizontal?.24:len+.08,sz=horizontal?len+.08:.24;
            box("curved_trigger_guard_"+i,[7.65,cy-sy/2,cz-sz/2],[8.35,cy+sy/2,cz+sz/2],0,"hardware",[ang,0,0],[8,cy,cz]);
        }
        box("trigger_curved",[7.83,7.25,6.3],[8.17,8.55,6.56],3,"hardware",[-22.5,0,0],[8,8.4,6.4]);
        for(const side of [-1,1])for(const yz of [[3.8,3.25],[7.7,4.5],[8.6,7.9]]){
            const x=8+side*1.43;
            box("gold_screw_"+side+"_"+yz[0],[x-.1,yz[0]-.19,yz[1]-.19],[x+.1,yz[0]+.19,yz[1]+.19],2,"hardware");
        }
        for(const side of [-1,1])for(let j=0;j<7;j++){
            const z=8.8+j*.9,y=11.98+(j%3)*.04;
            box("solar_edge_"+side+"_"+j,[8+side*.86-.055,y,z],[8+side*.86+.055,y+.08,z+.66],j%2?5:6,"energy");
        }
    }else if(name==="shadow_bow"){
        box("riser_core",[7.46,5.7,7.45],[8.54,10.3,8.55],0);
        for(let i=0;i<9;i++)box("wrapped_grip_"+i,[7.4,6+i*.44,7.38],[8.6,6.23+i*.44,8.62],3,"plating");
        const points=[[8,10],[6.85,11.8],[5.75,13.8],[5.6,15.8],[6.4,17.6],[8,19],[10.2,20.7]];
        for(const sign of [-1,1]){
            for(let k=0;k<points.length-1;k++){
                const a=points[k],b=points[k+1];
                for(let j=0;j<4;j++){
                    const t=j/4,u=(j+1)/4,progress=(k+t)/6;
                    const p=[a[0]+(b[0]-a[0])*t,8+sign*(a[1]+(b[1]-a[1])*t-8),8];
                    const q=[a[0]+(b[0]-a[0])*u,8+sign*(a[1]+(b[1]-a[1])*u-8),8];
                    strip("curved_limb_"+sign+"_"+k+"_"+j,p,q,.95-progress*.58,.8-progress*.45,1,"structure");
                    strip("spectral_limb_ridge_"+sign+"_"+k+"_"+j,[p[0]-.16,p[1],7.54],[q[0]-.16,q[1],7.54],.27,.12,j%4===0?6:5);
                    strip("limb_reverse_inlay_"+sign+"_"+k+"_"+j,[p[0]+.06,p[1],8.47],[q[0]+.06,q[1],8.47],.12,.1,4,"inlay");
                }
            }
            for(const fork of [-1,1])for(let i=0;i<8;i++){
                const t=i/8,u=(i+1)/8;
                const a=[8.0+t*3.3,8+sign*(10.6+Math.sin(t*Math.PI*.62)*1.65+fork*t*.65),8+fork*.32];
                const b=[8.0+u*3.3,8+sign*(10.6+Math.sin(u*Math.PI*.62)*1.65+fork*u*.65),8+fork*.32];
                strip("forked_tip_"+sign+"_"+fork+"_"+i,a,b,.40*(1-t)+.06,.24*(1-t)+.06,4);
            }
            for(let i=0;i<5;i++){
                const y=8+sign*(3.7+i*1.75),x=6.1+(i>2?(i-2)*.75:0);
                strip("void_wisp_"+sign+"_"+i,[x,y,7.97],[x-.35,y+sign*.85,7.97],.11,.12,5);
            }
        }
        box("spectral_bowstring",[11.23,-4.15,7.95],[11.31,20.15,8.05],6,"string");
        for(const sign of [-1,1]){
            box("string_nock_"+sign,[10.8,8+sign*12.0-.10,7.82],[11.4,8+sign*12.0+.10,8.18],2,"hardware");
            strip("riser_guard_"+sign,[7.4,8+sign*2.1,8],[6.6,8+sign*2.9,8],.35,.6,2,"hardware");
        }
        box("arrow_rest",[6.9,8.45,7.45],[8.15,8.65,8.55],2,"hardware");
    }else{
        // Small projectile prop, tip at -Z, centered on [8,8,8]. Total 2.6 x 2.6 x 14 units.
        box("spectral_shaft",[7.88,7.88,2.8],[8.12,8.12,13.8],4,"structure");
        box("whitehot_shaft_core",[7.96,7.96,2.5],[8.04,8.04,14],6,"energy");
        for(let i=0;i<12;i++){
            const z=1+i*.19,w=.10+i*.065;
            box("arrowhead_diamond_x_"+i,[8-w,7.92,z],[8+w,8.08,z+.2],i%3?5:6,"plating");
            box("arrowhead_diamond_y_"+i,[7.92,8-w,z],[8.08,8+w,z+.2],i%3?4:6,"plating");
        }
        for(const axis of [0,1])for(const sign of [-1,1])for(let i=0;i<7;i++){
            const z=11.1+i*.4,w=.35+i*.14;
            const f=[7.95,7.95,z],t=[8.05,8.05,z+.4];
            f[axis]=8+(sign<0?-w:.05);t[axis]=8+(sign<0?-.05:w);
            box("spectral_fletching_"+axis+"_"+sign+"_"+i,f,t,i%3?1:5,"plating");
        }
        for(const x of [7.74,8.14])box("split_nock_"+x,[x,7.88,13.8],[x+.12,8.12,15],2,"hardware");
    }
    for(const [slot,data] of Object.entries(superDisplay))Project.display_settings[slot]=new DisplaySlot(slot,data);
    Undo.finishEdit("H15 author "+name,{elements:made,textures:[tex],outliner:true,display_slots:Object.keys(superDisplay)});
    Canvas.updateAll();
    return {name,project:Project.uuid,cubes:made.length,faces:made.length*6,triangles:made.length*12,texture:tex.javaTextureLink()};
})()
