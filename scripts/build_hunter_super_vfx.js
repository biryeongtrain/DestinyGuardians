(() => {
    if (Outliner.elements.length || Texture.all.length) throw new Error("Use a new empty free project");
    const variant=superVfxName, name="destiny_super_"+variant+"_h15";
    const arc=variant.startsWith("arc"),solar=variant.startsWith("solar");
    const colors=arc?["#F0FDFF","#ACEFFF","#45BEF7","#2766A0"]:solar?["#FFF9DD","#FFE595","#FF9D35","#C73D1C"]:["#F9E2FF","#D4A4FF","#995CE2","#4E2679"];
    Undo.initEdit({elements:[],textures:[],outliner:true});
    Project.name=name;Project.model_identifier=name;Project.texture_width=128;Project.texture_height=128;
    Project.credit="Original H15 ultimate VFX reconstruction; not extracted Bungie assets";
    const textures=colors.map((color,i)=>{const c=document.createElement("canvas");c.width=c.height=16;const x=c.getContext("2d");x.fillStyle=color;x.fillRect(0,0,16,16);
        const t=new Texture({name:name+"_"+i+".png",id:String(i)}).fromDataURL(c.toDataURL());t.add(false);return t;});
    const root=new Group({name:"root",origin:[0,0,0]}).init(),groups={},bones={},elements=[];let triangles=0;
    const add=(a,b)=>a.map((v,i)=>v+b[i]),sub=(a,b)=>a.map((v,i)=>v-b[i]),mul=(a,s)=>a.map(v=>v*s),unit=a=>mul(a,1/(Math.hypot(...a)||1));
    const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
    function group(n){groups[n]=new Group({name:n,origin:[0,0,0]}).addTo(root).init();}
    function mesh(g,n,vs,fs,mat){const vertices={},faces={};vs.forEach((p,i)=>vertices["v"+i]=p);
        fs.forEach((f,i)=>{const keys=f.map(v=>"v"+v),uv={};keys.forEach((k,j)=>uv[k]=[j===1?9:7,j===2?9:7]);
            faces["f"+i]={vertices:keys,uv,texture:textures[mat].uuid};triangles++;});
        const m=new Mesh({name:n,origin:[0,0,0],vertices,faces}).addTo(groups[g]).init();elements.push(m);}
    function ribbon(g,n,path,width,mat,normal=[0,1,0]){const vs=[],fs=[];
        path.forEach((p,i)=>{const tangent=sub(path[Math.min(i+1,path.length-1)],path[Math.max(0,i-1)]),side=unit(cross(tangent,normal)),w=typeof width==="function"?width(i/(path.length-1)):width;
            vs.push(add(p,mul(side,w/2)),add(p,mul(side,-w/2)));});
        for(let i=0;i<path.length-1;i++){const a=i*2,b=a+1,c=a+3,d=a+2;fs.push([a,b,c],[a,c,d],[c,b,a],[d,c,a]);}mesh(g,n,vs,fs,mat);}
    function orb(g,n,c,r,mat){const vs=[add(c,[0,r,0])],fs=[],sides=12,rings=5;
        for(let j=1;j<rings;j++)for(let i=0;i<sides;i++){const a=i*Math.PI*2/sides,b=j*Math.PI/rings;
            vs.push(add(c,[Math.cos(a)*Math.sin(b)*r,Math.cos(b)*r,Math.sin(a)*Math.sin(b)*r]));}
        const bottom=vs.length;vs.push(add(c,[0,-r,0]));
        for(let i=0;i<sides;i++){const k=(i+1)%sides;fs.push([0,1+k,1+i]);
            for(let j=0;j<rings-2;j++){let a=1+j*sides+i,b=1+j*sides+k,d=a+sides,e=b+sides;fs.push([a,b,e],[a,e,d]);}
            fs.push([bottom,1+(rings-2)*sides+i,1+(rings-2)*sides+k]);}mesh(g,n,vs,fs,mat);}
    const keys=(times,scales)=>times.map((time,i)=>({time,scale:scales[i]}));
    let duration=.6,animation="spawn";
    if(variant==="arc_sweep"){
        group("edge");group("forks");group("sparks");
        for(let layer=0;layer<3;layer++){
            const path=Array.from({length:33},(_,j)=>{const t=j/32,a=(-.88+t*1.76),r=15.6-layer*.6;
                return[Math.sin(a)*r,(t-.5)*3+Math.sin(t*Math.PI)*.7,Math.cos(a)*r];});
            ribbon("edge","crescent_layer_"+layer,path,t=>(.13+Math.sin(t*Math.PI)*(.72-layer*.2)),layer===0?2:layer===1?1:0);
        }
        for(let k=0;k<6;k++){
            const a=-.72+k*.29,r=13.8,path=Array.from({length:6},(_,j)=>{const rr=r+j*.8;return[Math.sin(a)*rr+Math.cos(a)*Math.sin(j*2+k)*.3,j*.2+(k-2.5)*.4,Math.cos(a)*rr];});
            ribbon("forks","branched_tip_"+k,path,t=>.19*(1-t)+.025,k%2?0:1,[1,.2,0]);
            orb("sparks","ion_"+k,[Math.sin(a)*17,Math.sin(k)*1.5,Math.cos(a)*17],.14,k%2);
        }
        bones.edge=[{time:0,rotation:[0,-28,-4],scale:.01},{time:.05,rotation:[0,-20,-2],scale:.72},{time:.15,rotation:[0,0,0],scale:1},{time:.3,rotation:[0,20,4],scale:.93},{time:.6,rotation:[0,38,9],scale:.01}];
        bones.forks=keys([0,.05,.2,.4,.6],[.01,.8,1,.65,.01]);bones.sparks=keys([0,.1,.3,.6],[.01,.9,1.15,.01]);
    }else if(variant==="solar_muzzle"||variant==="solar_impact"){
        group("core");group("flames");group("embers");duration=variant==="solar_muzzle"?.45:.7;
        orb("core","incandescent_kernel",[0,0,0],variant==="solar_muzzle"?2.1:3.0,0);
        for(let k=0;k<8;k++){
            const a=k*Math.PI/4;const path=Array.from({length:10},(_,j)=>{const t=j/9,r=1+t*(7+(k%3)*1.5);
                return[Math.cos(a)*r+Math.sin(t*8+k)*t,.8*Math.sin(t*6+k)+t*(k%2?3:1),Math.sin(a)*r];});
            ribbon("flames","flame_petals_"+k,path,t=>Math.pow(1-t,.7)*(k%2?.7:1.2)+.02,k%2?1:2,[Math.cos(a+.5),1,Math.sin(a+.5)]);
            const center=path[path.length-1];orb("embers","spark_"+k,center,.12+(k%3)*.04,k%2);
        }
        bones.core=keys([0,.05,.15,duration],[.02,1,.65,.01]);bones.flames=keys([0,.05,.18,duration],[.01,.85,1.15,.01]);
        bones.embers=[{time:0,scale:.01},{time:.08,scale:.7},{time:.3,scale:1.4,position:[0,1,0]},{time:duration,scale:.01,position:[0,2,0]}];
    }else if(variant==="void_anchor"){
        group("singularity");group("orbits");group("tendrils");animation="loop";duration=1.2;
        orb("singularity","white_void_seed",[0,2,0],1.7,0);orb("singularity","pink_inner",[0,2,0],1.3,1);
        for(let k=0;k<4;k++){
            const path=Array.from({length:29},(_,j)=>{const t=j/28,a=k*Math.PI/2+t*2.6,r=8-4*t;
                return[Math.cos(a)*r,2+Math.sin(t*Math.PI*2+k)*2,Math.sin(a)*r];});
            ribbon("orbits","broken_orbit_"+k,path,t=>.05+Math.sin(t*Math.PI)*.45,k%2?1:2,[0,1,.2]);
        }
        for(let k=0;k<6;k++){
            const a=k*Math.PI/3,path=Array.from({length:9},(_,j)=>{const t=j/8,r=2+t*10;
                return[Math.cos(a+t*.3)*r,2-t*3+Math.sin(t*5+k)*.3,Math.sin(a+t*.3)*r];});
            ribbon("tendrils","anchor_feeler_"+k,path,t=>.14*(1-t)+.02,k%2?1:2);
        }
        bones.singularity=keys([0,.3,.6,.9,1.2],[.85,1,.85,1,.85]);
        bones.orbits=[{time:0,rotation:[0,0,0]},{time:.6,rotation:[0,180,0]},{time:1.2,rotation:[0,360,0]}];
        bones.tendrils=keys([0,.3,.6,.9,1.2],[1,.85,1,.85,1]);
    }else throw new Error("Unknown ultimate VFX");
    if(triangles>1600)throw new Error("Ultimate triangle budget "+triangles);
    Undo.finishEdit("Author H15 ultimate "+variant,{elements,textures,outliner:true});Canvas.updateAll();
    return{name,variant,triangles,meshes:elements.length,renderBones:Object.keys(groups).length,bones,duration,animation};
})()
