#!/usr/bin/env python3
"""W147 Parcel of Stardust (Fell to Earth): semantic blued steel / wood shotgun.
Inert original FBX read; accepted native frame/display and gameplay preserved.
"""
import argparse,base64,collections,copy,hashlib,io,json,math,runpy,uuid
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='parcel_of_stardust_fell_to_earth'
ART=f'art/weapons/w123/{ID}/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/shotgun/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
BB=f'art/blockbench/weapons/w30/{ID}.bbmodel'
RAW=Path('/tmp/destiny-weapons-w30/raw/parcel_of_stardust_fell_to_earth/extracted/Parcel of Stardust (Fell to Earth)')
PHOTO=Path('/tmp/destiny-weapons-w31/references/parcel_of_stardust_fell_to_earth.jpg')
H=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
FACES=H['FACES'];EDGE=1024
PALETTE=dict(blue=[30,55,60],edge=[63,91,95],steel=[52,62,65],black=[20,25,27],wood=[75,47,35],woodedge=[104,68,48],silver=[162,172,169],recess=[9,15,17])

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    for name,digest in meta['source_files'].items():assert sha((RAW.parent/name).read_bytes())==digest
    roots=H['parse_fbx'](RAW/'Parcel of Stardust (Fell to Earth).fbx')
    objects=next(r[2] for r in roots if r[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]
    for n in objects:
        if n[0]!='Geometry':continue
        mid=next(p for c,p in links if c==n[1][0]);model=models[mid];name=model[1][1].split('\x00')[0]
        assert name in meta['source_objects'],name
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
        assert np.allclose(props['Lcl Scaling'],[100,100,100],atol=.0001)
        cs={c[0]:c for c in n[2]};raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        points=raw[:,[0,2,1]]*meta['scale']+meta['anchor']
        ix=np.array(cs['PolygonVertexIndex'][1][0]);assert np.all(ix[2::3]<0)
        faces=np.where(ix<0,-ix-1,ix).reshape(-1,3)
        layer=next(c for c in n[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        values={c[0]:c[1][0] for c in layer[2]}
        uv=np.array(values['UV']).reshape(-1,2)[np.array(values['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
        material=next(materials[c] for c,p in links if p==mid and c in materials)
        meshes.append(dict(name=name,vertices=points,faces=faces,uv=uv,material=material))
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    assert not meta['excluded_objects']
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==11272
    p=np.concatenate([m['vertices'] for m in meshes])
    np.testing.assert_allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=1e-5,rtol=0)
    ref=next(x for x in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if x['id']==ID)
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta,ref

def source_triangles(meshes):
    textures={name:np.asarray(Image.open(RAW/(f+'_Diffuse.png')).convert('RGBA')) for name,f in [('Frame','POSFTEFrame'),('Sight','POSFTESight')]}
    result=[]
    for m in meshes:
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((ps,uv,textures[m['material']],n))
    return result

def make_design(meta,ref):
    parts=[]
    def box(group,name,c,size,mat,motif='plain',turn=None):
        c=np.array(c,float);s=np.array(size,float)
        e=dict(name=name,**{'from':(c-s/2).round(6).tolist(),'to':(c+s/2).round(6).tolist()})
        if turn:e['rotation']=dict(origin=c.round(6).tolist(),axis=turn[0],angle=round(turn[1],6))
        parts.append(dict(group=group,material=mat,motif=motif,kind='filled_semantic_cuboid',geometry=e))
    def beam(group,name,a,b,width,depth,mat,motif='plain',x=8):
        z0,y0=a;z1,y1=b
        box(group,name,[x,(y0+y1)/2,(z0+z1)/2],[width,depth,math.hypot(z1-z0,y1-y0)],mat,motif,('x',-math.degrees(math.atan2(y1-y0,z1-z0))))
    def tube(group,name,y,z0,z1,r,thick,mat):
        # Eight actual walls: open bore and meaningful cross-section, no body card.
        for i in range(8):
            a=math.tau*i/8;rho=r-thick/2
            box(group,f'{name}_{i}',[8+rho*math.cos(a),y+rho*math.sin(a),(z0+z1)/2],
                [thick,2*rho*math.tan(math.pi/8)+.035,z1-z0],mat,'tube',('z',math.degrees(a)))
    # Uninterrupted long blued barrel and shorter underslung magazine tube.
    tube('barrel','barrel_wall',11.82,-9.75,2.60,.45,.11,'blue')
    tube('barrel','muzzle_collar',11.82,-9.75,-9.47,.48,.11,'edge')
    box('barrel','bore_backstop',[8,11.82,-9.19],[.59,.59,.04],'recess')
    tube('magazine','magazine_wall',10.40,-9.66,4.50,.31,.09,'blue')
    tube('magazine','magazine_front_collar',10.40,-9.66,-9.42,.34,.09,'edge')
    box('magazine','magazine_front_depth',[8,10.4,-9.20],[.42,.42,.04],'recess')
    # Two selected supporting saddles, not a series of decorative slices.
    for z in (-7.8,1.2):
        box('saddles',f'tube_saddle_{z}',[8,10.97,z],[.45,.44,.42],'steel','fastener')
    tube('receiver','barrel_receiver_cuff',11.82,1.78,2.14,.51,.13,'silver')
    box('receiver','filled_receiver',[8,11.48,6.03],[1.44,1.68,7.40],'blue','receiver')
    box('receiver','upper_spine',[8,12.21,5.95],[1.15,.22,7.36],'edge','rail')
    for side in (-1,1):
        box('receiver',f'receiver_top_bevel_{side}',[8+side*.63,12.24,5.95],[.28,.24,7.36],'blue','edge',('z',side*25))
        box('receiver',f'receiver_lower_bevel_{side}',[8+side*.63,10.72,6.03],[.28,.25,7.20],'steel','edge',('z',-side*25))
        box('receiver',f'lower_frame_plate_{side}',[8+side*.70,10.18,5.48],[.08,.54,4.18],'steel','receiver')
    box('receiver','loading_elevator',[8,10.28,3.29],[1.12,.40,1.62],'blue','receiver')
    # Right side ejection/loading hardware follows the original asymmetry.
    box('receiver','ejection_recess',[8.735,11.35,4.03],[.025,.44,1.72],'recess','slot')
    box('receiver','ejection_bolt',[8.765,11.29,4.13],[.075,.24,1.43],'steel','bolt')
    box('receiver','action_bar',[8.57,10.78,2.12],[.17,.23,2.94],'blue','rail')
    box('receiver','action_pivot',[8.68,10.53,3.31],[.15,.46,.49],'edge','fastener')
    # Solid rounded wooden pump. Serration/grain is UV, not dozens of geometry ribs.
    box('pump','wooden_pump_core',[8,10.00,-.83],[1.24,1.23,5.77],'wood','pump')
    for side in (-1,1):
        box('pump',f'pump_lower_round_{side}',[8+side*.48,9.50,-.83],[.38,.37,5.70],'wood','pump',('z',side*32))
        box('pump',f'pump_upper_round_{side}',[8+side*.50,10.50,-.83],[.34,.38,5.70],'woodedge','pump',('z',-side*32))
    for z in (-3.74,2.03):box('pump',f'pump_end_{z}',[8,10,z],[1.18,1.25,.18],'wood','endgrain')
    # Five broad finger scallops change the source silhouette; fine fluting stays UV.
    for i,z in enumerate((-3.05,-2.04,-1.03,-.02,.99)):
        for side in (-1,1):
            box('pump',f'finger_scallop_{i}_{side}',[8+side*.37,9.35,z],[.59,.38,.69],'wood','pump',('z',side*27))
    # Sloped wood pistol grip, with full-through silver skeleton beneath it.
    beam('grip','wood_grip',[8.65,10.12],[9.70,7.88],1.15,1.27,'wood','grip')
    beam('grip','grip_heel',[9.17,7.86],[10.10,8.25],1.17,.25,'steel','edge')
    for side in (-1,1):
        x=8+side*.44
        beam('guard',f'upper_trigger_front_{side}',[6.20,10.06],[6.45,9.09],.18,.17,'silver',x=x)
        beam('guard',f'trigger_floor_{side}',[6.45,9.09],[7.91,9.16],.18,.17,'silver',x=x)
        beam('guard',f'trigger_rear_{side}',[7.91,9.16],[8.30,10.02],.18,.17,'silver',x=x)
        # The second, deeper open skeleton loop is prominent in the reference.
        beam('guard',f'skeleton_front_{side}',[6.49,9.15],[7.70,6.67],.18,.18,'silver',x=x)
        beam('guard',f'skeleton_base_{side}',[7.70,6.67],[9.09,7.27],.18,.18,'silver',x=x)
        beam('guard',f'skeleton_rear_{side}',[9.09,7.27],[9.52,8.09],.18,.18,'silver',x=x)
    beam('guard','trigger',[7.22,10.15],[7.50,9.53],.16,.15,'steel')
    # Open short stock: wood upper/lower rails and real rectangular cutout.
    beam('stock','stock_neck',[9.43,11.65],[10.35,11.49],1.22,1.30,'wood','stock')
    box('stock','wood_upper_stock',[8,11.93,12.45],[1.38,.72,5.39],'wood','stock')
    box('stock','wood_lower_stock',[8,10.65,12.53],[1.23,.43,4.62],'wood','stock')
    box('stock','stock_end',[8,10.83,14.80],[1.40,3.02,.80],'wood','stock')
    box('stock','dark_butt_pad',[8,10.82,15.21],[1.44,3.07,.09],'black','pad')
    box('stock','steel_cheek',[8,12.35,11.99],[1.02,.20,3.92],'edge','rail')
    box('stock','stock_lower_heel',[8,9.42,14.25],[1.19,.42,1.34],'steel','edge')
    box('stock','rear_sling_mount',[8.74,10.02,14.66],[.17,.61,.20],'steel','fastener')
    # Source sight object, not a tall invented optic; notch remains physical air.
    box('sight','rear_sight_base',[8,12.37,5.14],[.80,.20,1.77],'black','sight')
    for side in (-1,1):
        beam('sight',f'rear_sight_ear_{side}',[4.35,12.45],[5.12,12.70],.17,.18,'blue','sight',x=8+side*.23)
    box('sight','rear_sight_bridge',[8,12.47,5.67],[.60,.16,.34],'blue','sight')
    return dict(id=ID,revision='W147',family='shotgun',source=meta,reference=ref,parts=parts,
        scale=meta['scale'],anchor=meta['anchor'],source_mapping='baked FBX [X,Z,Y]*scale+anchor; muzzle negative native Z',palette=PALETTE,
        method='Hand-authored continuous filled bodies, actual hollow bores/guard/stock, opaque per-face UV. Not rip islands/voxel shell.',
        required_air_probes={'barrel_bore':[8,11.82,-9.67],'magazine_end':[8,10.4,-9.60],'trigger_guard':[8,9.55,6.9],'skeleton_loop':[8,7.9,7.9],'stock_cutout':[8,11.20,12.50],'sight_notch':[8,12.69,4.85]},
        solid_probes={'receiver':[8,11.5,6.0],'pump':[8,10,-1],'wood_stock':[8,12,12]},
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in (BASE,BB,'art/weapons/w31/references.json','scripts/generate_surface_w123_beloved.py')},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in (RAW/'Parcel of Stardust (Fell to Earth).blend',RAW/'Parcel of Stardust (Fell to Earth).fbx',RAW/'POSFTEFrame_Diffuse.png',RAW/'POSFTESight_Diffuse.png',PHOTO)},
        limitations=['Static matte default-dye approximation, not recovered PBR/reflection.','Selected barrel/wood bevels are faceted; source fine engraving not invented as fake lettering.','Generic/per-shell reload and original display/item graphs/audio retained; native verification owned by master.'])

def tile(s,face,w,h):
    base=np.array(PALETTE[s['material']],float);yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h
    a=np.zeros((h,w,4),np.uint8);a[:,:,3]=255;a[:,:,:3]=base
    ps=vertices(s['geometry'])[list(FACES[face])];p=ps[0]+u[:,:,None]*(ps[1]-ps[0])+v[:,:,None]*(ps[3]-ps[0]);X,Y,Z=(p[:,:,i] for i in range(3))
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    if s['material'] in ('blue','edge','steel','silver'):
        a[:,:,:3]=np.clip(base[None,None,:]*(.96+.04*np.sin(v*math.pi))[:,:,None],0,255)
        a[edge<.8,:3]=np.clip(base+14,0,255)
        if s['motif']=='receiver' and face in ('east','west'):
            a[(edge>1)&(edge<2),:3]=base*.67
            # Clean accepted receiver panel joints, no invented logos/screw voxels.
            for z in (3.0,5.1,8.6):a[(abs(Z-z)<.014)&(Y<11.2),:3]=base*.55
        if s['motif']=='pad':a[(np.mod(Y,.13)<.022),:3]=base*.6
        if s['motif']=='tube':a[(abs(Y-11.82)<.06)&(face in ('east','west')),:3]=np.minimum(base+13,255)
    if s['material'] in ('wood','woodedge'):
        # Low contrast long grain and physically continuous pump grooves.
        grain=np.sin(Y*48+np.sin(Z*1.2)*1.5)*.035+np.sin(Y*17+Z*.15)*.025
        a[:,:,:3]=np.clip(base[None,None,:]*(1+grain[:,:,None]),0,255)
        a[edge<.7,:3]=np.minimum(base+10,255)
        if s['motif']=='pump' and face in ('east','west','down'):
            grooves=(np.mod(Z,.19)<.027)&(Z>-3.3)&(Z<1.6)&(Y<10.42)
            a[grooves,:3]=base*.48
            a[(np.mod(Z,.19)>.037)&(np.mod(Z,.19)<.051)&(Y<10.42),:3]=np.minimum(base+17,255)
    return Image.fromarray(a)

def compile_model(d,meshes):
    atlas=Image.new('RGBA',(EDGE,EDGE),(20,26,29,255));requests=[]
    for s in d['parts']:
        s['geometry']['faces']={}
        for face in FACES:
            p=vertices(s['geometry'])[list(FACES[face])];w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*18));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*18))
            requests.append((h,w,s['geometry']['name'],face,s))
    requests.sort(key=lambda q:(-q[0],-q[1],q[2],q[3]));x=y=2;row=0;ledger=[]
    for h,w,name,face,s in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        assert y+h+2<=EDGE,'Atlas overflow'
        im=tile(s,face,w,h);atlas.paste(Image.fromarray(np.pad(np.asarray(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        s['geometry']['faces'][face]=dict(uv=[v*16/EDGE for v in (x,y,x+w,y+h)],texture='#0')
        ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    d['atlas']=dict(size=EDGE,gutter=2,islands=ledger)
    return atlas,dict(credit='Parcel of Stardust Fell to Earth W147 / semantic solids and clean face UV',textures={'0':f'destiny:item/weapon/w123/{ID}','particle':f'destiny:item/weapon/w123/{ID}'},elements=[copy.deepcopy(s['geometry']) for s in d['parts']],display=json.loads((ROOT/BASE).read_bytes())['display'])

def comparison(d,meshes,atlas,model):
    w,h=800,335;sheet=Image.new('RGB',(2400,1570),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=19):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'PARCEL OF STARDUST (FELL TO EARTH) W147 / CLEAN VOLUMES + WOOD / BLUED STEEL',26)
    photo=Image.open(PHOTO).convert('RGB').crop((655,250,1870,680));photo.thumbnail((1060,400));sheet.paste(photo,(8,55))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / full only / <=1000 assembled',
        'Long octagonal barrel / twin deep bores / wood pump grain + UV flutes',
        'Continuous receiver / open silver double guard / open short wood stock',
        'Actual original FBX11272 textured triangles; original native frame/display',
        'Offline render, not native or FPS evidence']):label(1100,90+i*60,line)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+f'textures/item/weapon/w30/{ID}.png'))
    ts=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)];points=np.concatenate([m['vertices'] for m in meshes])
    for i,name in enumerate(('RAW UNDYED DIFFUSE /11272TRI','CANONICAL READ ONLY',f'NEW /{len(model["elements"])}SEMANTIC SOLIDS')):label(i*w+12,470,name,18)
    for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('MUZZLE OBLIQUE',[1,.4,-.6]),('STOCK OBLIQUE',[-1,.35,.55])]):
        ext=H['frame'](points,cam,w,h)
        for col,tris in enumerate(ts):
            im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,510+row*h));label(col*w+12,518+row*h,name,17)
    return png(sheet)

def generate(include_comparison=True):
    meshes,meta,ref=source_meshes();d=make_design(meta,ref);atlas,model=compile_model(d,meshes);n=len(model['elements']);assert n<=1000
    review=f'''# Parcel of Stardust (Fell to Earth) W147\n\n{n} opaque semantic cuboids,1024² face UV atlas,full-only. Actual default photo opened; original inert FBX2objects11272texturedtriangles, both BLEND/FBX hashes pinned, baked [X,Z,Y]*scale+anchor bounds verified. No downloaded scripts/shaders executed.\n\nBlued-steel receiver, long exposed barrel and underslung magazine, warm wood pump/short open stock and two-hole silver grip skeleton retain the reference identity. Eight-wall barrels have physical depth/backstops. Large continuous bodies and meaningful bevels replace rip fragments; pump flutes/grain and shallow receiver joints are UV. No invented engraving/logos, voxel-shell or alpha sidecards.\n\nAccepted scale{meta['scale']},anchor{meta['anchor']},muzzle-Z/display preserved; original generic/per-shell reload, ADS/twohand, ammo/timing/audio unchanged. Actual reflection, PBR and continuous source curvature not recovered. comparison shows raw/canonical/new at matched side/front/rear views, editable inspection embeds final atlas. Master owns native/parser/pack/held/ADS/fire/reload/20display verification.\n'''
    out={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review.encode()}
    if include_comparison:out[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    ps=np.concatenate([vertices(e) for e in model['elements']]);manifest=dict(id=ID,revision='W147',assembled_elements=n,opaque_cuboids=n,triangle_adapter_elements=0,alpha_body_elements=0,emitted_faces=n*6,texture_size=[EDGE,EDGE],max_assembled_elements=1000,groups=dict(collections.Counter(s['group'] for s in d['parts'])),actual_bounds=[ps.min(0).tolist(),ps.max(0).tolist()],source_bounds=meta['model_bounds'],source_triangles=11272,textured_triangles=11272,canonical_display_exact=True,full_only=True,native_accepted=False,input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={p:sha(b) for p,b in out.items()},limitations=d['limitations'])
    out[ART+'manifest.json']=encode(manifest);return out


def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()

def sha(v):return hashlib.sha256(v).hexdigest()

def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()

def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w147:parcel_of_stardust:'+n))

def vertices(e):
    e=copy.deepcopy(e)
    if 'rotation' in e:
        q=e['rotation'];e['rotation']=dict(origin=q['origin'],**{q['axis']:q['angle']})
    return H['vertices'](e)

def model_triangles(model,atlas):
    model=copy.deepcopy(model)
    for e in model['elements']:
        if 'rotation' in e:
            q=e['rotation'];e['rotation']=dict(origin=q['origin'],**{q['axis']:q['angle']})
    return H['model_triangles']({'full':model},atlas)

def inspection(d,model,atlas):
    es=[];groups=collections.defaultdict(list)
    for s,e in zip(d['parts'],model['elements']):
        b=copy.deepcopy(e);q=b.pop('rotation',None);rot=[0,0,0]
        if q:rot['xyz'.index(q['axis'])]=q['angle']
        b.update(type='cube',uuid=uid(b['name']),origin=q['origin'] if q else [8,8,8],rotation=rot,box_uv=False,autouv=0)
        for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
        es.append(b);groups[s['group']].append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Parcel of Stardust (Fell to Earth) W147 owned inspection',resolution={'width':EDGE,'height':EDGE},elements=es,
        outliner=[dict(name=g,uuid=uid('group:'+g),origin=[8,8,8],rotation=[0,0,0],children=names,export=True) for g,names in groups.items()],
        textures=[dict(name=ID+'.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=copy.deepcopy(model['display']))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    for path,data in generate().items():
        target=ROOT/path
        if args.verify:assert target.read_bytes()==data,path
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    print('Parcel W147 verified' if args.verify else 'Parcel W147 generated')
