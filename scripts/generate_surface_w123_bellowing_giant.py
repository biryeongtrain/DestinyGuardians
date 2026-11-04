#!/usr/bin/env python3
"""W150 Bellowing Giant: photo-backed semantic solids; seven owned artifacts only."""
import argparse
import base64
import collections
import copy
import json
import math
from pathlib import Path
import uuid
import numpy as np
from PIL import Image, ImageDraw
import generate_surface_w123_beloved as H
import generate_surface_w123_temptation_s_hook as SDNA

ROOT=Path(__file__).resolve().parents[1]
ID='bellowing_giant'
ART='art/weapons/w123/'+ID+'/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+'models/weapon/rocket_launcher/'+ID+'.json'
MODEL=ASSET+'models/weapon_surface_w123/'+ID+'.json'
TEXTURE=ASSET+'textures/item/weapon/w123/'+ID+'.png'
BB='art/blockbench/weapons/w30/'+ID+'.bbmodel'
GENERATOR='scripts/generate_surface_w123_'+ID+'.py'
TEST='scripts/qa/test_surface_w150_'+ID+'.py'
RAW=Path('/tmp/destiny-weapons-w30/raw/bellowing_giant/extracted/Bellowing Giant')
PHOTO=Path('/tmp/destiny-weapons-w31/references/bellowing_giant.jpg')
REFS=Path('/tmp/destiny-weapons-w31/references.json')
EDGE=1024
FACES=H.FACES
sha,encode,png=H.sha,H.encode,H.png
PALETTE=dict(red=[189,44,37],rededge=[227,65,53],graphite=[51,57,65],black=[27,31,36],
             steel=[128,139,142],bore=[65,72,76],rubber=[73,76,66],recess=[15,19,23],pin=[236,107,78])

def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w150:'+ID+':'+n))
def render_element(e):
    e=copy.deepcopy(e)
    if 'rotation' in e:
        r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return e

def vertices(e):return H.vertices(render_element(e))
def triangles(model,atlas):
    m=copy.deepcopy(model);m['elements']=[render_element(e) for e in model['elements']]
    return H.model_triangles({'full':m},atlas)

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert meta['source_axis']==dict(length=1,thin=0,muzzle_sign=1)
    for name,digest in meta['source_files'].items():assert sha((RAW.parent/name).read_bytes())==digest
    # Both readers decode inert arrays. No bpy, embedded source scripts or shaders.
    blend=SDNA.Blend(RAW/'Bellowing Giant.blend');stored={}
    for _,obj in blend.records('Object'):
        name=blend.field(blend.field(obj,'Object','id'),'ID','name')[2:]
        if name not in meta['source_objects']+meta['excluded_objects']:continue
        matrix=np.array(blend.field(obj,'Object','obmat')).reshape(4,4)
        mesh=blend.pointed(blend.field(obj,'Object','data'));n=blend.field(mesh,'Mesh','totvert')
        v=np.ndarray((n,3),'<f4',blend.pointed(blend.field(mesh,'Mesh','mvert')),
            offset=blend.fields['MVert']['co'][0],strides=(blend.sizes['MVert'],4)).astype(float)
        stored[name]=dict(world=(np.c_[v,np.ones(n)]@matrix)[:,:3],matrix=matrix.tolist(),
                          triangles=blend.field(mesh,'Mesh','totpoly'))
    roots=H.parse_fbx(RAW/'Bellowing Giant.fbx');objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    materials={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]
    for node in objects:
        if node[0]!='Geometry':continue
        model=models[next(p for c,p in links if c==node[1][0])];name=model[1][1].split('\x00')[0]
        assert name in stored,name
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        np.testing.assert_allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
        assert props['Lcl Scaling']==[100,100,100]
        ch={c[0]:c for c in node[2]};local=np.array(ch['Vertices'][1][0]).reshape(-1,3)
        fbx=(local*np.array(props['Lcl Scaling']))@H.rotation(dict(zip('xyz',props['Lcl Rotation']))).T
        fbx+=props.get('Lcl Translation',[0,0,0]);world=fbx[:,[0,2,1]]*[1,-1,1]/100
        np.testing.assert_allclose(world,stored[name]['world'],atol=1.5e-7,rtol=0)
        ix=np.array(ch['PolygonVertexIndex'][1][0]);assert np.all(ix[2::3]<0) and len(ix)%3==0
        faces=np.where(ix<0,-ix-1,ix).reshape(-1,3)
        assert len(faces)==stored[name]['triangles']
        if name not in meta['source_objects']:continue
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        uvdata={c[0]:c[1][0] for c in layer[2]}
        assert uvdata['MappingInformationType']=='ByPolygonVertex'
        uv=np.array(uvdata['UV']).reshape(-1,2)[np.array(uvdata['UVIndex'])].reshape(-1,3,2);uv[:,:,1]=1-uv[:,:,1]
        mat=next(materials[c] for c,p in links if p==model[1][0] and c in materials)
        # Reproduce W30 exactly for audit, including its extent-based sign heuristic.
        canonical=world[:,[0,2,1]]*[1,1,-1]*meta['scale']+meta['anchor']
        # The actual photo/foregrip identifies raw -Y as front. Functional authored
        # geometry uses -Z front: preserve anchor/scale, correct the semantic direction.
        authored=world[:,[0,2,1]]*meta['scale']+meta['anchor']
        meshes.append(dict(name=name,vertices=authored,canonical=canonical,world=world,faces=faces,uv=uv,material=mat,
                           object_matrix=stored[name]['matrix']))
    assert sorted(stored)==sorted(meta['source_objects']+meta['excluded_objects'])
    world=np.concatenate([m['world'] for m in meshes]);p=np.concatenate([m['canonical'] for m in meshes])
    np.testing.assert_allclose([world.min(0),world.max(0)],meta['source_bounds'],atol=1.5e-7,rtol=0)
    np.testing.assert_allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=4e-6,rtol=0)
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==18468
    ref=next(r for r in json.loads(REFS.read_bytes()) if r['id']==ID)
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta

def make_design(meta):
    solids=[]
    def box(group,name,c,size,mat,turn=None,motif='panel'):
        c=np.array(c,float);size=np.array(size,float)
        e=dict(name=name,**{'from':(c-size/2).round(7).tolist(),'to':(c+size/2).round(7).tolist()})
        if turn:e['rotation']=dict(origin=c.round(7).tolist(),axis=turn[0],angle=turn[1])
        solids.append(dict(group=group,material=mat,motif=motif,geometry=e))
    def ring(group,name,x,y,z0,z1,r,t,mat,motif='panel'):
        for i in range(8):
            a=i*45;q=math.radians(a)
            box(group,f'{name}_{i}',[x-r*math.sin(q),y+r*math.cos(q),(z0+z1)/2],
                [2*r*math.tan(math.pi/8)+.012,t,z1-z0],mat,('z',a),motif)
    # Substantial launch jacket: thick octagonal panels + filled heart after the
    # 2.6-unit silver-lined throat. No alpha body, source-island/voxel conversion.
    ring('launch_jacket','Red_launch_jacket',8,12.05,-5.50,8.95,.76,.26,'red','jacket')
    box('launch_jacket','Launch_chamber_heart',[8,12.05,3.14],[1.23,1.23,12.0],'red',motif='jacket')
    ring('bore','Silver_throat',8,12.05,-5.5500227,-2.95,.61,.13,'steel','throat')
    box('bore','Recessed_throat_end',[8,12.05,-2.82],[1.14,1.14,.20],'recess')
    ring('muzzle_collar','Muzzle_dark_shroud',8,12.05,-4.90,-4.35,.85,.24,'graphite','damascus')
    # Long charcoal structural blades leave red strips visible between real steps.
    for side in (-1,1):
        box('barrel_rails',f'Upper_blade_{side}',[8+side*.61,12.90,1.61],[.34,.28,12.35],'graphite',motif='damascus')
        box('barrel_rails',f'Equator_blade_{side}',[8+side*.86,12.04,2.20],[.24,.28,10.8],'graphite',motif='rail')
        box('barrel_rails',f'Lower_blade_{side}',[8+side*.62,11.20,2.33],[.32,.22,13.42],'black',motif='rail')
        # Angular rail ramp at muzzle and receiver, not shallow contour cards.
        box('barrel_rails',f'Front_blade_ramp_{side}',[8+side*.85,12.12,-3.78],[.24,.39,1.27],'graphite',('x',-22.5),'damascus')
        box('barrel_rails',f'Rear_blade_ramp_{side}',[8+side*.83,12.10,7.90],[.25,.45,1.22],'graphite',('x',22.5),'damascus')
    box('barrel_rails','Continuous_graphite_roof',[8,13.04,1.50],[1.42,.20,12.10],'graphite',motif='damascus')
    # Receiver is a closed structural mass. Red breech wraps transition to stock.
    box('receiver','Receiver_core',[8,11.95,7.45],[1.73,1.72,2.65],'black',motif='armory')
    for side in (-1,1):
        box('receiver',f'Receiver_cheek_{side}',[8+side*.89,11.95,6.90],[.22,1.38,1.55],'graphite',motif='armory')
    ring('breech','Red_breech',8,12.03,8.55,9.65,.78,.28,'red','jacket')
    ring('breech','Steel_lock_band',8,12.03,9.57,10.0,.87,.22,'steel','band')
    # Stock is filled with full cross-sectional depth, not two thin side cards.
    ring('stock','Rear_sleeve',8,12.03,9.95,21.4499773,.76,.24,'graphite','stock')
    box('stock','Stock_filled_heart',[8,12.03,15.70],[1.30,1.30,11.45],'black',motif='stock')
    for side in (-1,1):
        box('stock',f'Stock_bottom_fin_{side}',[8+side*.43,10.93,20.90],[.22,.66,.56],'black')
    # Open lower stock strut: connects receiver to stock saddle, with air above.
    box('stock_frame','Stock_lower_strut',[8,10.22,10.31],[.82,.23,5.94],'black',motif='rail')
    box('stock_frame','Stock_strut_rear_rise',[8,10.50,13.17],[.82,.24,1.04],'graphite',('x',-25),'rail')
    box('stock_frame','Stock_rear_saddle',[8,11.0,13.55],[.86,.40,.64],'black')
    # Photo grip contact regions in source coordinates; the lower forearm is an
    # open bridge with a structural heel and hanging vertical front grip.
    box('underrail','Lower_backbone',[8,10.60,3.02],[1.06,.27,12.55],'black',motif='rail')
    box('underrail','Front_bridge_floor',[8,10.17,-.30],[.60,.18,4.91],'graphite',motif='rail')
    box('underrail','Bridge_front_join',[8,10.36,-2.75],[.60,.45,.24],'black',('x',22.5))
    box('underrail','Bridge_rear_join',[8,10.32,2.13],[.60,.53,.29],'black',('x',-22.5))
    box('foregrip','Foregrip_neck',[8,10.13,2.17],[.79,.44,.70],'black')
    box('foregrip','Foregrip_body',[8,8.99,2.17],[.72,2.14,.70],'steel',motif='foregrip')
    box('foregrip','Foregrip_heel',[8,7.81,2.17],[.82,.23,.79],'graphite',motif='foreheel')
    box('action','Action_closed_housing',[8,10.0,5.56],[1.08,.95,4.10],'graphite',motif='action')
    box('action','Action_front_chamfer',[8,9.78,3.70],[1.08,.30,.95],'graphite',('x',-22.5),'action')
    box('pistol','Pistol_mount',[8,9.52,7.37],[.95,.59,1.08],'black')
    box('pistol','Pistol_grip',[8,8.29,7.86],[.88,2.42,1.02],'rubber',('x',-25),'grip')
    box('pistol','Pistol_heel',[8,7.1988981,8.41],[1.00,.25,1.18],'rubber',('x',-25),'grip')
    box('pistol','Backstrap',[8,8.34,8.40],[.82,2.40,.18],'black',('x',-25),'grip')
    box('guard','Guard_front',[8,9.12,5.87],[.38,.81,.18],'black')
    box('guard','Guard_floor',[8,8.75,6.40],[.38,.16,1.22],'black')
    box('guard','Guard_rear',[8,9.10,7.02],[.38,.84,.18],'black',('x',-12))
    box('guard','Trigger',[8,9.22,6.61],[.16,.48,.14],'steel',('x',-18))
    # Offset open optic follows the photo's ring, without an opaque lens blocking
    # the ray. A pin terminates .08 below center; its tip is painted red.
    box('optic','Optic_standoff',[9.07,11.58,5.13],[.63,.27,.50],'black')
    ring('optic','Open_ring_sight',9.55,12.10,4.94,5.33,.49,.13,'graphite','optic')
    ring('optic','Silver_optic_inner_lip',9.55,12.10,4.89,4.96,.44,.05,'steel','optic')
    box('optic','Optic_top_lug',[9.55,12.65,5.13],[.30,.17,.53],'black')
    box('optic','Optic_bottom_lug',[9.55,11.55,5.13],[.30,.17,.53],'black')
    box('optic','Sight_pin',[9.55,11.86,5.11],[.065,.30,.11],'steel',motif='pin')
    box('optic','Sight_pin_tip',[9.55,12.005,5.11],[.08,.04,.12],'pin')
    # Original top furniture: solid short pedestal and open rear notch.
    box('top_sight','Top_pedestal',[8,13.255,5.40],[.63,.53,.55],'black')
    box('top_sight','Top_sight_hood',[8,13.63,5.40],[.68,.22,1.60],'graphite',motif='damascus')
    box('top_sight','Top_front_wedge',[8,13.64,4.41],[.45,.14,.64],'black',('x',-12))
    box('top_sight','Rear_notch_floor',[8,13.04,7.70],[.66,.28,.58],'black')
    for side in (-1,1):box('top_sight',f'Notch_ear_{side}',[8+side*.25,13.32,7.70],[.16,.38,.43],'graphite')
    inputs=[BASE,BB,ASSET+'textures/item/weapon/w30/'+ID+'.png',
            'scripts/generate_surface_w123_beloved.py','scripts/generate_surface_w123_temptation_s_hook.py']
    # Snapshot all currently relevant held/aim/reload records without editing them.
    for folder in ('models/weapon/rocket_launcher','models/weapon_aim_w70','models/weapon_reload_w47','items/weapon','items/weapon_aim_w70'):
        inputs.extend(str(p.relative_to(ROOT)) for p in sorted((ROOT/(ASSET+folder)).glob(ID+'*.json')))
    raw=[PHOTO,REFS]+sorted(p for p in RAW.rglob('*') if p.is_file())
    return dict(id=ID,stage='W150',family='rocket_launcher',full_only=True,source=meta,palette=PALETTE,
        solids=solids,groups=dict(collections.Counter(s['group'] for s in solids)),
        frame=dict(anchor=meta['anchor'],scale=meta['scale'],muzzle_axis='-Z',foregrip_contact=[8,8.99,2.17],pistol_contact=[8,8.29,7.86]),
        ads_sight=dict(sightCenter=[9.55,12.10,5.13],forwardPoint=[9.55,12.10,3.13],eyeSide='+Z',plane='XY',style='optic'),
        coordinate_audit=dict(w30='anchor + scale * [world.X,world.Z,-world.Y]',
            authored='anchor + scale * [world.X,world.Z,world.Y]',
            reason='W30 chooses muzzle_sign from farther extent, not muzzle semantics. Photo and front grip identify world -Y as muzzle. Direction corrected around unchanged anchor; no model-wide rescale/recenter.',
            original_source_bounds=meta['source_bounds'],original_native_bounds=meta['model_bounds']),
        air_probes=dict(bore_mouth=[8,12.05,-5.5],bore_deep=[8,12.05,-3.1],
            forearm_bridge=[8,10.39,-.3],grip_separation=[8,8.5,4.5],trigger_loop=[8,9.08,6.20],
            stock_strut=[8,10.75,11.0],optic_center=[9.55,12.10,5.13]),
        paint_evidence=dict(photo=str(PHOTO),observations=['Red launch jacket with dark continuous blades',
            'Silver recessed bore, grey topographic steel, long filled rear sleeve',
            'Offset open ring, light metal foregrip, olive-grey checkered pistol grip'],
            method='Independent opaque face UV; global-coordinate contour engraving, panel seams and Black Armory mark. Neutral diffuse is reference, not default dye.'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in sorted(set(inputs))},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw},
        limitations=['Offline CPU inspection; native parser, held/ADS, generic reload, timing/audio and 10-20 displays remain parent-owned.',
            'Octagonal contours and authored default palette approximate reflective PBR; contour engraving simplified.',
            'W30 extent-derived front/back semantics corrected without changing anchor/scale/display; parent must verify muzzle and hand fit.'])

def tile(spec,face,w,h):
    e=spec['geometry'];p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    xyz=p[0]+u[:,:,None]*(p[1]-p[0])+v[:,:,None]*(p[3]-p[0]);x,y,z=[xyz[:,:,i] for i in range(3)]
    mat=spec['material'];motif=spec['motif'];c=np.array(PALETTE[mat],float)
    a=np.broadcast_to(c,(h,w,3)).copy();edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    a+=(1.2*np.sin(z*21+y*13))[:,:,None]
    a[edge<.65]*=.72;a[(edge>.65)&(edge<1.35)]*=1.23
    if motif in ('damascus','stock'):
        # Coherent topographic contours visible on actual Black Armory steel.
        q=np.sin(z*1.8+.62*np.sin(y*8))+.52*np.sin(y*5+z*2.3)
        lines=np.abs(np.sin(q*16))<.105;a[lines]+=9
        if motif=='stock' and face in ('east','west'):
            stripe=(y>11.46)&(y<11.63)&(z>10.18)&(z<20.9);a[stripe]*=.34
            stripe=(y>12.52)&(y<12.57)&(z>10.18)&(z<20.9);a[stripe]*=1.45
    if motif=='jacket' and face in ('east','west','up','down'):
        # Small paired vents and latch outlines are face paint, not cube noise.
        a[abs(y-11.69)<.035]*=.55
        for zz in (-1.8,2.65,6.1,8.9):
            slit=(abs(z-zz)<.055)&(y>11.98)&(y<12.28);a[slit]=[25,29,34]
            slot=(abs(z-zz-.14)<.045)&(y>11.98)&(y<12.28);a[slot]=[30,31,34]
        for zz in (-3.35,.65,4.7):
            q=((z-zz)/.25)**2+((y-12.0)/.095)**2
            a[(q>.72)&(q<1.18)]*=.65
    if motif in ('rail','action','band'):
        a[(edge>2.2)&(edge<3.1)]*=.65
        if motif=='action' and face in ('east','west'):
            for zz,yy in ((4.05,10.19),(6.78,9.72)):
                r=(z-zz)**2+(y-yy)**2;a[(r<.012)&(r>.004)]=[153,159,151]
    if motif=='armory' and face in ('east','west'):
        # Photo-backed fork/arch emblem, intentionally side-specific face UV.
        zz=z-6.83;yy=y-12.0
        mark=((abs(zz-.16)<.027)|(abs(zz+.16)<.027))&(abs(yy)<.40)
        mark|=(abs(yy-.12)<.024)&(abs(zz)<.31)
        mark|=(abs(yy-.38+abs(zz)*.7)<.028)&(abs(zz)<.24)
        a[mark]=[107,113,115]
    if motif=='throat':
        a*= (.78+.22*u)[:,:,None];a[abs(z+5.40)<.05]*=1.5
    if motif=='grip':
        inset=(u>.12)&(u<.88)&(v>.13)&(v<.88)
        diamond=(np.sin(y*77+z*54)*np.sin(y*77-z*54)>.1)
        a[inset]*=.66;a[inset&diamond]*=.66
    if motif=='foregrip':
        a+=np.cos(u*math.pi*2)[:,:,None]*8
        a[abs(y-8.15)<.035]*=.6
    if motif=='foreheel':
        a[(u>.3)&(u<.7)&(v>.16)&(v<.83)]=PALETTE['red']
    if motif=='pin':a[y>11.96]=PALETTE['pin']
    return Image.fromarray(np.dstack((np.clip(a,0,255).astype('uint8'),np.full((h,w),255,dtype='uint8'))))

def compile_model(d):
    requests=[]
    for s in d['solids']:
        for face,indices in FACES.items():
            p=vertices(s['geometry'])[list(indices)];w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*19));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*19))
            requests.append((h,w,s['geometry']['name'],face,s))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,255))
    x=y=2;row=0;islands=[];uv={}
    for h,w,name,face,s in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        assert y+h+2<=EDGE,('atlas overflow',name,y+h)
        patch=tile(s,face,w,h);atlas.paste(Image.fromarray(np.pad(np.array(patch),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uv[name,face]=[q*16/EDGE for q in (x,y,x+w,y+h)];islands.append(dict(element=name,face=face,rect=[x,y,x+w,y+h]))
        x+=w+4;row=max(row,h)
    es=[]
    for s in d['solids']:
        e=copy.deepcopy(s['geometry']);e['faces']={f:dict(uv=uv[e['name'],f],texture='#0') for f in FACES};es.append(e)
    d['atlas']=dict(size=EDGE,gutter=2,islands=islands,used_height=y+row+2)
    model=dict(credit='W150 Bellowing Giant / authored filled solids and photo-backed opaque face UV',
        textures={'0':'destiny:item/weapon/w123/'+ID,'particle':'destiny:item/weapon/w123/'+ID},
        elements=es,display=json.loads((ROOT/BASE).read_bytes())['display'])
    return model,atlas

def inspection(d,model,atlas):
    es=[];groups=collections.defaultdict(list)
    for s,e in zip(d['solids'],model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation',None)
        b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],
                 rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],box_uv=False,autouv=0)
        for f in b['faces'].values():f.update(texture=0,uv=[q*EDGE/16 for q in f['uv']])
        es.append(b);groups[s['group']].append(b['uuid'])
    return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name='Bellowing Giant W150 / semantic solids',
        resolution=dict(width=EDGE,height=EDGE),elements=es,display=model['display'],
        outliner=[dict(name=g,uuid=uid('group:'+g),origin=[8,8,8],rotation=[0,0,0],children=v,export=True) for g,v in groups.items()],
        textures=[dict(name=ID+'.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        destiny_w150=dict(full_only=True,frame=d['frame'],ads_sight=d['ads_sight'],native_accepted=False))

def raw_triangles(meshes):
    textures={m:np.array(Image.open(RAW/f).convert('RGBA')) for m,f in [('Frame','BGFrame_Diffuse.png'),('Sight','BGSight_Diffuse.png')]};out=[]
    for m in meshes:
        for p,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20);out.append((p,uv,textures[m['material']],n))
    return out

def comparison(d,meshes,model,atlas):
    w,h=800,285;sheet=Image.new('RGB',(2400,1835),'#17202a');draw=ImageDraw.Draw(sheet)
    def text(x,y,s,size=20):draw.text((x,y),s,fill='#e3e9ee',font_size=size)
    text(20,12,'BELLOWING GIANT | W150 | SEMANTIC SOLIDS / OFFLINE DIAGNOSTIC',30)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((1100,505));sheet.paste(photo,(10,55))
    for i,s in enumerate([f'{len(model["elements"])} closed solid cuboids / {len(model["elements"])*6} opaque independent face UVs',
        'Actual default photo: red launch tube / graphite blades / olive grip',
        'Real deep silver bore, open underrail / stock strut, open ring optic',
        'Actual FBX + BLEND matrices checked against W30 source/native bounds',
        'W30 extent sign reverses visible front; new muzzle corrected to -Z',
        'Same original anchor / scale / complete display; full only',
        'Native / held / ADS / reload / audio / 10-20 displays: parent pending']):text(1140,95+i*51,s,21)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/'+ID+'.png'))
    ts=[triangles(old,oldtex),raw_triangles(meshes),triangles(model,atlas)]
    points=np.concatenate([vertices(e) for e in old['elements']+model['elements']]+[m['vertices'] for m in meshes])
    for col,label in enumerate(['OLD W30 CANONICAL (UNMODIFIED / 217)', 'ACTUAL RAW / FRONT ADAPTED / NEUTRAL', 'W150 / PHOTO-BASED DEFAULT DYE']):text(col*w+12,570,label,19)
    for row,(name,cam) in enumerate([('SIDE / matched frame',[1,0,0]),('FRONT QUARTER / -Z',[1,.4,-.67]),('OPPOSITE QUARTER / +Z',[-1,.35,.65])]):
        extent=H.frame(points,cam,w,h)
        for col,tris in enumerate(ts):
            im,_=H.render(tris,cam,extent,(w,h),raw=col==1);sheet.paste(im,(col*w,600+row*h));text(col*w+12,605+row*h,name,18)
    # Final actual geometry, isolated close-ups; all use the same emitted model.
    for i,(label,gs,cam) in enumerate([
        ('DEEP OPEN BORE',('bore','launch_jacket','muzzle_collar'),[.10,.06,-1]),
        ('UNDERARM / SEPARATE GRIPS',('underrail','foregrip','pistol','guard','action'),[1,.14,-.25]),
        ('STOCK AIR / FILLED SLEEVE',('stock','stock_frame','receiver','action'),[-1,.15,.25]),
        ('OPEN OPTIC / PIN BELOW CENTER',('optic',),[.08,.04,1])]):
        selected=[e for s,e in zip(d['solids'],model['elements']) if s['group'] in gs]
        ps=np.concatenate([vertices(e) for e in selected]);t=triangles(dict(elements=selected),atlas)
        im,_=H.render(t,cam,H.frame(ps,cam,600,290),(600,290));sheet.paste(im,(i*600,1465));text(i*600+9,1470,label,18)
    text(20,1775,'Old/source/new use identical cameras and framing per full-model row. Source albedo is neutral, not recovered PBR/default shader.',21)
    text(20,1807,'Final details isolate the same native-output geometry. No DCC, game, native parser or performance acceptance claimed.',20)
    return png(sheet)

def review_text(d,n):
    return f"""# Bellowing Giant W150 art review

Actual opened photo: `{PHOTO}`. Source: nested Bellowing Giant folder, inert
Blender 3.3 SDNA and FBX 7400 arrays; original hashes pinned for every raw file.
Retained .00.001 and .01.000: 18,468 triangles; .02.001 reticle excluded.
BLEND matrices are identity; FBX rotation -90 X and 100 scale convert back to
Blender raw coordinates. Vertex agreement and W30 source/native bounds checked.

{n} closed cuboids, {n*6} independent opaque faces, 0 triangle adapters/cards.
Red thick octagonal launch jacket and filled chamber, deep silver throat, broad
continuous graphite blades, filled long graphite stock, paired grips and open
underarm/stock bridges preserve photo identity. Fine paired vents, topographic
engraving, action fasteners and Armory fork emblem use authored face UV.
The basic red/graphite/olive dye follows the photo, not neutral raw albedo.
Each face owns a separate proportionate island and opaque two-pixel gutter.
Visual revision: replaced the overly red upper plane with a broad continuous
graphite roof and added the photo's silver optic lining, then re-opened the final
comparison. Geometry remains substantial.

Axis caveat discovered in actual data: W30 picks muzzle_sign=+1 only because
world Y max .568299 exceeds abs(min -.564103). Its [X,Z,-Y] mapping therefore
places the photo's front (thicker muzzle beside foregrip at raw -Y) toward +Z.
We reproduce those exact W30 bounds for provenance, then design the functional
muzzle at native -Z using [X,Z,Y]. Original anchor {d['frame']['anchor']} and
scale {d['frame']['scale']} are unchanged, all complete display contexts copied
exactly. Authored endpoints deliberately match W30 native length bounds; no
model-wide rescale/recenter. This corrects semantic direction, not runtime data.
Parent must verify native muzzle/hand fit in its single session.

Functional sight: offset open octagonal ring at X9.55/Y12.10/Z5.13, eye +Z,
plane XY, forward point Z3.13. Clear ray through the whole assembly toward -Z;
physical red pin tip stops below center. No opaque lens blocks it. Underrail,
trigger bow, separated grips and lower-stock strut have true geometric air.

Comparison includes actual default photo; unmodified old canonical; actual
textured source adapted to functional front; authored side and both quarters;
final bore, grip/bridge, stock and optic closeups. CPU-only diagnostic.
Original full-only generic reload, timing, audio and shared registrations are
untouched. Seven artifacts only; parent owns shared integration and tests.

Limitations: faceted octagons; simplified UV engraving and authored matte dye,
not exact reflective shader reconstruction. Native parser/pack, first/third
person, ADS, generic reload/muzzle alignment, audio and 10-20 display checks
remain parent-owned and unverified here.
"""

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);model,atlas=compile_model(d)
    outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),
        ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,len(model['elements'])).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,model,atlas)
    p=np.concatenate([vertices(e) for e in model['elements']]);n=len(model['elements'])
    manifest=dict(stage='W150',id=ID,assembled_elements=n,counts=dict(full=n),emitted_faces=n*6,
        max_assembled_elements=1000,alpha_contour_elements=0,triangle_adapter_elements=0,opaque_cuboids=n,
        source_triangles=meta['source_triangles'],groups=d['groups'],full_only=True,native_accepted=False,
        actual_bounds=[p.min(0).round(7).tolist(),p.max(0).round(7).tolist()],original_bounds=meta['model_bounds'],
        anchor=meta['anchor'],scale=meta['scale'],canonical_display_exact=True,ads_sight=d['ads_sight'],
        generator_sha256=sha((ROOT/GENERATOR).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={k:sha(v) for k,v in sorted(outputs.items())},limitations=d['limitations'],
        validation=dict(targeted_test=TEST,determinism='generator --verify',native='pending parent',performance='not measured'))
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w150/batch.json').read_bytes())
    scope=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w150-'+ID))
    assert len(scope)==10 and len(outputs)==7 and set(outputs)<=scope
    for path,data in outputs.items():
        dest=ROOT/path
        if args.verify:assert dest.read_bytes()==data,'Regeneration differs: '+path
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    print(('Verified' if args.verify else 'Generated')+f' seven artifacts; {len(json.loads(outputs[MODEL])["elements"])} solid cuboids')

if __name__=='__main__':main()
