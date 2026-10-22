// Original H14 hybrid VFX, authored with native Blockbench geometry through MCP.
// Mesh colors use BetterModel 3.5.1's normalized-16 sampler; cards retain full UV detail.
(() => {
    if (Outliner.elements.length || Texture.all.length) throw new Error("Use an empty free model");
    const name=vfxName, variant=name.replace("destiny_vfx_","").replace("_h14","");
    const palettes={arc:["#F5FDFF","#B4EFFF","#43B8F4","#2264A5"],solar:["#FFF8D1","#FFDA69","#FF8B2F","#B82C15"],
        vortex:["#FFE5FF","#D49DFF","#9053D4","#452462"],smoke:["#AB9FBD","#887A9A","#60536E","#382E48"]};
    const palette=palettes[variant]; if(!palette)throw new Error("Unknown VFX");
    Undo.initEdit({elements:[],textures:[],outliner:true});
    Project.name=name;Project.model_identifier=name;Project.texture_width=128;Project.texture_height=128;
    Project.ambientocclusion=false;Project.credit="Original H14 curved VFX; reference notes in docs; not extracted game assets";
    const canvas=document.createElement("canvas");canvas.width=128;canvas.height=128;const ctx=canvas.getContext("2d");
    palette.forEach((c,i)=>{ctx.fillStyle=c;ctx.fillRect(i*32,0,32,16);});
    const rgb=palette.map(s=>[1,3,5].map(i=>parseInt(s.slice(i,i+2),16)));
    const tiles={flame:[0,72,64,128],cloud:[64,16,128,128],flare:[0,16,64,72]};
    // Dense deterministic gradients and turbulent cutouts, not a coarse checkerboard.
    for(let y=16;y<128;y++)for(let x=0;x<128;x++){
        const cloud=x>=64,u=((x%64)+.5)/64,v=(y-15.5)/112;
        let strength=0,color;
        if(cloud){
            const xx=(u-.5)*2,yy=(v-.52)*2;
            const radius=Math.sqrt(xx*xx+yy*yy*.85),theta=Math.atan2(yy,xx);
            const edge=.86+.075*Math.sin(theta*5)+.045*Math.sin(theta*3+1);
            if(radius>edge)continue;
            const hash=Math.sin(x*12.9898+y*78.233)*43758.5453,noise=hash-Math.floor(hash);
            if(noise>Math.min(1,(edge-radius)/.18))continue;
            const dome=Math.sqrt(Math.max(0,1-Math.pow(radius/edge,2)));
            const turbulence=.055*Math.sin(u*18+Math.sin(v*12)*2)+.035*Math.cos(v*25-u*11);
            const q=Math.max(0,Math.min(1,.16+.48*dome-.10*xx-.12*yy+turbulence));
            strength=1-radius; color=rgb[3].map((c,i)=>Math.round(c+(rgb[0][i]-c)*q));
        }else if(y<72){
            const yy=(y-43.5)/28,xx=(u-.5)*2,r=Math.hypot(xx,yy);
            const theta=Math.atan2(yy,xx),edge=.88+.06*Math.sin(theta*9);
            if(r>edge)continue;
            const idx=r<.28?0:r<.52?1:2;color=rgb[idx];strength=1-r;
        }else{
            const v=(y-71.5)/56,t=1-v,center=.5+Math.sin(v*10)*.11+Math.sin(v*24)*.035;
            const width=.025+Math.pow(v,.8)*.37;
            const edge=Math.abs(u-center)/width;
            if(edge>1+Math.sin(v*42)*.1)continue;
            strength=Math.max(0,1-edge);
            const q=Math.min(3,Math.floor(edge*2.6+t*.8));color=rgb[q];
        }
        ctx.fillStyle="rgb("+color.join(",")+")";ctx.fillRect(x,y,1,1);
    }
    const tex=new Texture({name:name+".png",id:"0",particle:true}).fromDataURL(canvas.toDataURL());tex.add(false);
    const root=new Group({name:"root",origin:[0,0,0]}).init(),groups={},bones={},made=[];
    let triangleCount=0;
    const add=(a,b)=>a.map((v,i)=>v+b[i]),sub=(a,b)=>a.map((v,i)=>v-b[i]),mul=(a,s)=>a.map(v=>v*s);
    const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
    const unit=a=>mul(a,1/(Math.hypot(...a)||1));
    function group(n,origin=[0,0,0]){groups[n]=new Group({name:n,origin}).addTo(root).init();return n;}
    function mesh(g,n,vertices,faces,mats){
        const vs={},fs={};vertices.forEach((p,i)=>vs["v"+i]=p);
        faces.forEach((face,i)=>{const keys=face.map(v=>"v"+v),m=Array.isArray(mats)?mats[i]:mats;
            // BB viewport reads pixel UV; BetterModel reads normalized-16 UV. First top strip
            // is palette[0], so use a separate 16x16 constant-color texture per material below.
            const uv={};keys.forEach((k,j)=>uv[k]=[j===1?9:7,j===2?9:7]);
            fs["f"+i]={vertices:keys,uv,texture:meshTextures[m].uuid};triangleCount+=face.length-2;});
        const m=new Mesh({name:n,origin:[0,0,0],vertices:vs,faces:fs}).addTo(groups[g]).init();made.push(m);return m;
    }
    // Constant-color 16x16 textures avoid different BB/BetterModel UV conventions entirely.
    const meshTextures=palette.map((c,i)=>{const cv=document.createElement("canvas");cv.width=16;cv.height=16;
        const cx=cv.getContext("2d");cx.fillStyle=c;cx.fillRect(0,0,16,16);
        const t=new Texture({name:name+"_mesh_"+i+".png",id:String(i+1)}).fromDataURL(cv.toDataURL());t.add(false);return t;});
    function ribbon(g,n,path,width,mat,normal=[0,1,0]){
        const vs=[],fs=[];
        path.forEach((p,i)=>{let tangent=sub(path[Math.min(i+1,path.length-1)],path[Math.max(0,i-1)]);
            let side=unit(cross(tangent,normal)),w=typeof width==="function"?width(i/(path.length-1)):width;
            vs.push(add(p,mul(side,w/2)),add(p,mul(side,-w/2)));});
        for(let i=0;i<path.length-1;i++){let a=i*2,b=a+1,c=a+3,d=a+2;
            fs.push([a,b,c],[a,c,d],[c,b,a],[d,c,a]);}
        return mesh(g,n,vs,fs,mat);
    }
    function sphere(g,n,center,size,mat,sides=12,rings=5,seed=0){
        const vs=[add(center,[0,size[1],0])],fs=[];
        for(let j=1;j<rings;j++)for(let i=0;i<sides;i++){
            const a=i*Math.PI*2/sides,b=j*Math.PI/rings,w=1+.08*Math.sin(i*2+j*3+seed);
            vs.push(add(center,[Math.sin(b)*Math.cos(a)*size[0]*w,Math.cos(b)*size[1],Math.sin(b)*Math.sin(a)*size[2]*w]));}
        const bottom=vs.length;vs.push(add(center,[0,-size[1],0]));
        for(let i=0;i<sides;i++){const k=(i+1)%sides;fs.push([0,1+k,1+i]);
            for(let j=0;j<rings-2;j++){let a=1+j*sides+i,b=1+j*sides+k,c=b+sides,d=a+sides;fs.push([a,b,c],[a,c,d]);}
            fs.push([bottom,1+(rings-2)*sides+i,1+(rings-2)*sides+k]);}
        return mesh(g,n,vs,fs,fs.map((_,i)=>Math.min(3,mat+(i%11===0?1:0))));
    }
    function card(g,n,c,size,tile,rot=[0,0,0],mat=0){
        const faces={};for(const s of ["north","south","east","west","up","down"])faces[s]={texture:null};
        for(const s of ["north","south"])faces[s]={uv:tile||[mat*32,0,mat*32+32,16],texture:tex.uuid};
        const cube=new Cube({name:n,from:[c[0]-size[0]/2,c[1]-size[1]/2,c[2]-.012],to:[c[0]+size[0]/2,c[1]+size[1]/2,c[2]+.012],
            origin:c,rotation:rot,box_uv:false,autouv:0,faces}).addTo(groups[g]).init();cube.light_emission=15;made.push(cube);return cube;
    }
    function arcPath(r,y,start,sweep,steps=24){return Array.from({length:steps+1},(_,i)=>{let t=i/steps,a=start+sweep*t;
        return[Math.sin(a)*r*(.96+.04*Math.sin(t*7)),y+.4*Math.sin(t*6),Math.cos(a)*r];});}
    const scaleKeys=(ts,vs)=>ts.map((time,i)=>({time,scale:[vs[i],vs[i],vs[i]]}));
    if(variant==="arc"){
        group("core");group("wave");sphere("core","ion_seed",[0,1,0],[1.6,1.3,1.6],0);
        for(let i=0;i<3;i++)card("core","core_glint_"+i,[0,1,0],[7,7],tiles.flare,[0,i*60,0]);
        for(let i=0;i<3;i++)ribbon("wave","broken_shock_arc_"+i,arcPath(15,.4,i*2.1,1.65,20),t=>.12+.22*Math.sin(t*Math.PI),2);
        bones.core=scaleKeys([0,.05,.15,.35,.8],[.05,1.1,.6,.02,.01]);bones.wave=scaleKeys([0,.1,.3,.65,.8],[.05,.4,1,1.17,.01]);
        for(let i=0;i<4;i++){
            const n=group("bolt_"+i),a=i*Math.PI/2+.2;
            const path=Array.from({length:10},(_,j)=>{const r=1+j*1.55,off=j===0?0:Math.sin(j*2.4+i)*(.4+j*.07);
                return[Math.sin(a)*r+Math.cos(a)*off,1+Math.sin(j*1.7+i)*(.4+j*.12),Math.cos(a)*r-Math.sin(a)*off];});
            ribbon(n,"cyan_corona",path,t=>.58*(1-t)+.05,2);
            ribbon(n,"white_branching_spine",path,t=>.22*(1-t)+.025,0,[Math.cos(a),0,-Math.sin(a)]);
            for(let j=3;j<9;j+=2){const base=path[j],branch=[base,add(base,[Math.cos(a)*1.4,1.1,-Math.sin(a)*1.4]),add(base,[Math.cos(a)*2.8,1.6,-Math.sin(a)*2.8])];
                ribbon(n,"fork_"+j,branch,t=>.13*(1-t)+.02,1);}
            for(let j=0;j<4;j++){const p=add(path[j*2+2],[.6,1.2,-.6]);card(n,"ion_spark_"+j,p,[.1,.5+(j%2)*.4],null,[0,i*55,25+j*17],j%2);}
            bones[n]=scaleKeys([0,.05,.15,.3,.55,.8],[.1,1,.83,1.1,.01,.01]);
            bones[n].push({time:0,rotation:[0,-4,0]},{time:.1,rotation:[0,7,0]},{time:.25,rotation:[0,-8,0]},{time:.55,rotation:[0,2,0]});
        }
    }else if(variant==="solar"){
        group("core");group("wave");sphere("core","incandescent_kernel",[0,1.5,0],[2.4,2.1,2.4],0);
        for(let i=0;i<3;i++)card("core","core_glare_"+i,[0,2,0],[6.5,6],tiles.flare,[0,i*60,0]);
        for(let i=0;i<3;i++)ribbon("wave","expanding_heat_arc_"+i,arcPath(13,.4,i*2.1,1.45,16),t=>.6*Math.sin(t*Math.PI)+.03,2);
        bones.core=scaleKeys([0,.1,.25,.6,1.1],[.04,1.25,.7,.05,.01]);bones.wave=scaleKeys([0,.1,.4,.8,1.1],[.05,.45,1,1.15,.01]);
        for(let i=0;i<6;i++){
            const a=i*Math.PI/3,x=Math.sin(a)*3,z=Math.cos(a)*3,n=group("flame_"+i,[x,0,z]);
            const height=6.5+(i%3)*1.8;
            for(let k=0;k<2;k++){
                const path=Array.from({length:13},(_,j)=>{const t=j/12,r=3+t*(4+i%3)+Math.sin(t*6+i)*.8;
                    return[Math.sin(a)*r+Math.cos(a)*Math.sin(t*7+i)*t, .5+t*height, Math.cos(a)*r+Math.sin(t*8+i)*t];});
                ribbon(n,"curved_flame_layer_"+k,path,t=>(k?.65:1.45)*Math.pow(1-t,.7)+.015,k?1:2,[Math.cos(a),0,-Math.sin(a)]);
            }
            card(n,"turbulent_flame_cutout",[x,3.8,z],[3.4+(i%2),7.2+(i%3)],tiles.flame,[0,i*60,Math.sin(i)*15]);
            for(let j=0;j<6;j++)card(n,"ejected_ember_"+j,[Math.sin(a)*(5+j*.8),2+j*1.25+(i%2),Math.cos(a)*(5+j*.8)],
                [.07+(j%3)*.04,.4+(j%2)*.5],null,[0,i*60+j*17,25+(j%3)*18],j%3===0?0:1);
            bones[n]=scaleKeys([0,.1,.3,.65,1.1],[.05,1,.8,.45,.01]);
            bones[n].push({time:0,position:[0,0,0]},{time:.25,position:[Math.sin(a)*3,.5,Math.cos(a)*3]},
                {time:.65,position:[Math.sin(a)*6,1.2,Math.cos(a)*6]},{time:1.1,position:[Math.sin(a)*8,2,Math.cos(a)*8]});
        }
    }else if(variant==="vortex"){
        group("core");group("outer");group("inner");group("wisps");sphere("core","pink_white_singularity",[0,2.5,0],[1.35,1.7,1.35],0);
        for(let i=0;i<3;i++)card("core","core_radiance_"+i,[0,2.5,0],[5,6],tiles.flare,[0,i*60,0]);
        for(let k=0;k<6;k++){
            const path=Array.from({length:29},(_,j)=>{const t=j/28,a=k*Math.PI/3+t*2.4,r=16-t*(k%2?8:5);
                return[Math.sin(a)*r,.5+t*(2+k%3)+.6*Math.sin(t*6+k),Math.cos(a)*r];});
            ribbon(k%2?"inner":"outer","tapered_orbit_"+k,path,t=>.08+Math.sin(t*Math.PI)*(.5+(k%2)*.3),k%2?1:2);
        }
        for(let k=0;k<4;k++){
            const path=Array.from({length:17},(_,j)=>{let t=j/16,a=k*Math.PI/2+t*3.4,r=9-t*6;return[Math.sin(a)*r,1+t*4,Math.cos(a)*r];});
            ribbon("wisps","fine_infall_"+k,path,t=>.08+.10*Math.sin(t*Math.PI),k%2?0:1,[0,1,.3]);
        }
        for(let j=0;j<20;j++){let a=j*2.4,r=4+(j%5)*2;card("wisps","orbit_dust_"+j,[Math.sin(a)*r,1+j%4,Math.cos(a)*r],[.09,.18+j%3*.12],null,[0,j*31,45],j%3);}
        bones.core=scaleKeys([0,.5,1],[.8,1,.8]);bones.outer=[{time:0,rotation:[0,0,0]},{time:.5,rotation:[0,90,0]},{time:1,rotation:[0,180,0]}];
        bones.inner=[{time:0,rotation:[0,0,0],scale:1},{time:.5,rotation:[0,-180,0],scale:.83},{time:1,rotation:[0,-360,0],scale:1}];
        bones.wisps=[{time:0,rotation:[0,0,0],scale:1},{time:.5,rotation:[0,90,0],scale:.65},{time:1,rotation:[0,180,0],scale:1}];
    }else{
        for(let i=0;i<6;i++){
            const a=i*Math.PI/3,x=Math.sin(a)*8,z=Math.cos(a)*8,y=3+(i%3)*1.2,n=group("plume_"+i,[x,y,z]);
            // Overlapping textured cloud lobes share the billboard bone local facing.
            // Smoke is intentionally billboard cards only; no hidden mesh or cubic shell.
            for(let j=0;j<5;j++){
                const theta=j*2.4+i*.8,r=j===0?0:2.3;
                card(n,"curl_cutout_"+j,[x+Math.sin(theta)*r,y+Math.cos(theta)*1.3,z+Math.cos(theta)*r],
                    [6+(j%2),5.5+(j%3)*.5],tiles.cloud,[0,0,0]);
            }
            bones[n]=[{time:0,scale:.75,position:[0,-.5,0],rotation:[0,0,-4]},
                {time:1,scale:1,position:[0,1.2,0],rotation:[0,0,5]},{time:2,scale:.75,position:[0,-.5,0],rotation:[0,0,-4]}];
        }
    }
    if(triangleCount>1800)throw new Error("Triangle budget exceeded: "+triangleCount);
    Undo.finishEdit("Author H14 detailed "+variant+" VFX",{elements:made,textures:[tex,...meshTextures],outliner:true});Canvas.updateAll();
    return{name,variant,cubes:made.filter(e=>e instanceof Cube).length,meshes:made.filter(e=>e instanceof Mesh).length,triangles:triangleCount,
        renderBones:Object.keys(groups).length,bones,animation:variant==="arc"||variant==="solar"?"spawn":"loop",
        duration:variant==="arc"?.8:variant==="solar"?1.1:variant==="smoke"?2:1};
})()
