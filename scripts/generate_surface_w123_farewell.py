#!/usr/bin/env python3
"""W142 Farewell: semantic solids, open muzzle/guard, clean default-dye face UV.

The inert Blender reference is never used as exported geometry. Full model only;
canonical item/ADS/generic reload/display and all gameplay remain unchanged.
"""
import argparse
import base64
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import uuid
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/farewell/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/sidearm/farewell.json'
MODEL = ASSET+'models/weapon_surface_w123/farewell.json'
TEXTURE = ASSET+'textures/item/weapon/w123/farewell.png'
RAW = Path('/tmp/destiny-weapons-w30/raw/farewell/extracted')
PHOTO = Path('/tmp/destiny-weapons-w31/references/farewell.jpg')
BB = 'art/blockbench/weapons/w30/farewell.bbmodel'
EDGE = 1024
H = runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
FACES = H['FACES']
PALETTE = dict(blue=[120,150,162], silver=[174,184,187], steel=[91,104,110], black=[29,34,36], recess=[10,15,17], rubber=[28,30,29], bronze=[132,108,85], green=[64,166,60], green_edge=[34,133,45], orange=[207,139,39], purple=[124,84,151], magenta=[153,16,164])

def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v): return hashlib.sha256(v).hexdigest()
def png(im):
    b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(v): return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w142:farewell:'+v))
def vertices(e):
    e=copy.deepcopy(e)
    if 'rotation' in e:
        r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return H['vertices'](e)

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    reference=json.loads((ROOT/ART/'source-reference.json').read_bytes())
    assert reference['sourceSha256']==sha((RAW/'Farewell.blend').read_bytes())
    meshes=[]
    for m in reference['meshes']:
        v=np.array(m['vertices'])[:,[0,2,1]]*meta['scale']+meta['anchor']
        uv=np.array(m['uv']);uv[:,:,1]=1-uv[:,:,1]
        meshes.append(dict(name=m['name'],vertices=v,faces=np.array(m['faces']),uv=uv,materials=m['materials'],materialIndices=m['materialIndices']))
    p=np.concatenate([m['vertices'] for m in meshes])
    assert sum(len(m['faces']) for m in meshes)==31946
    assert np.allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=1e-5)
    return meshes,meta

def make_design(meta):
    parts=[]
    def box(group,name,c,size,mat,motif='plain',turn=None):
        c=np.array(c,float);sz=np.array(size,float)
        e=dict(name=name,**{'from':(c-sz/2).round(6).tolist(),'to':(c+sz/2).round(6).tolist()})
        if turn:e['rotation']=dict(origin=c.tolist(),axis=turn[0],angle=turn[1])
        parts.append(dict(group=group,material=mat,motif=motif,kind='opaque_solid_cuboid',geometry=e))
    def beam(group,name,a,b,width,depth,mat,motif='plain'):
        a=np.array(a,float);b=np.array(b,float);v=b-a
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],mat,motif,('x',math.degrees(math.atan2(v[2],v[1]))))
    # Long continuous slide/receiver: no imported islands or voxel skin.
    box('receiver','action_core',[8,12.52,3.12],[1.46,1.96,8.70],'black','stencil')
    box('receiver','upper_rail',[8,13.50,3.17],[1.12,.21,8.62],'steel','rail')
    box('receiver','blue_rear_core',[8,12.67,8.39],[1.42,1.43,2.70],'blue','stencil')
    box('receiver','sloped_rear_cap',[8,12.66,9.86],[1.33,1.30,.25],'blue','rear_slots',('x',-12))
    for side in (-1,1):
        box('receiver',f'upper_chamfer_{side}',[8+side*.67,13.37,3.10],[.25,.30,8.60],'steel','rail',('z',side*45))
        box('receiver',f'blue_lower_rail_{side}',[8+side*.76,11.77,4.39],[.14,.45,8.88],'blue','panel')
        box('receiver',f'rear_armor_{side}',[8+side*.75,12.62,8.62],[.14,1.45,2.10],'blue','rear_slots')
        box('receiver',f'rear_upper_bevel_{side}',[8+side*.67,13.37,8.39],[.22,.22,2.63],'silver','edge',('z',side*45))
        box('receiver',f'rear_lower_bevel_{side}',[8+side*.67,11.95,8.39],[.20,.20,2.60],'blue','edge',('z',side*45))
        box('receiver',f'action_plate_{side}',[8+side*.78,12.60,-.02],[.14,1.59,1.80],'black','panel')
    # Actual rectangular muzzle opening and its recessed inner barrel.
    box('muzzle','muzzle_roof',[8,13.27,-3.02],[1.78,.24,3.65],'black','edge')
    box('muzzle','muzzle_floor',[8,12.04,-3.02],[1.78,.22,3.65],'black','edge')
    for side in (-1,1):
        box('muzzle',f'muzzle_wall_{side}',[8+side*.80,12.65,-3.03],[.20,1.20,3.67],'black','muzzle_vents')
        box('muzzle',f'upper_muzzle_bevel_{side}',[8+side*.78,13.20,-3.04],[.23,.23,3.62],'steel','edge',('z',side*45))
    box('muzzle','bore_backstop',[8,12.65,-2.40],[1.19,.89,.08],'recess')
    box('muzzle','inner_bore_floor',[8,12.20,-3.37],[1.16,.10,1.85],'steel')
    for side in (-1,1):
        box('clamp',f'bronze_clamp_{side}',[8+side*.85,12.65,-1.30],[.18,1.56,.40],'bronze','edge')
    box('clamp','bronze_clamp_roof',[8,13.40,-1.30],[1.65,.20,.42],'bronze','edge')
    box('clamp','bronze_vent_rail',[8,11.65,1.45],[1.76,.25,4.95],'bronze','rail')
    # Lower heat sink: a filled spine, with real separated fins around the edge.
    box('heatsink','heat_core',[8,11.05,1.51],[1.14,.81,4.42],'black','panel')
    for i in range(12):
        z=-.25+i*.33
        box('heatsink',f'cooling_fin_{i}',[8,10.88,z],[1.94,1.06+.15*math.sin(i/11*math.pi),.13],'steel','fin',('x',-12))
    # Four visible green cables per side. Curved transitions are a few solid spans;
    # the much smaller strap/rib detail is UV, not hundreds of geometric rings.
    for side in (-1,1):
        x=8+side*.89
        for i in range(4):
            y=13.25-i*.14
            beam('cables',f'green_run_{side}_{i}',[x,y,.35],[x,y,2.88],.12,.12,'green','wire')
            beam('cables',f'green_curve_a_{side}_{i}',[x,y,2.88],[x,y-.16,3.22],.12,.12,'green','wire')
            beam('cables',f'green_curve_b_{side}_{i}',[x,y-.16,3.22],[x,y-.49,3.48],.12,.12,'green','wire')
            beam('cables',f'green_drop_{side}_{i}',[x,y-.49,3.48],[x,11.59,3.72+i*.09],.12,.12,'green','wire')
        beam('cables',f'large_cable_{side}',[x,12.45,.55],[x,12.45,2.60],.17,.23,'green_edge','wire')
        beam('cables',f'large_bend_{side}',[x,12.45,2.60],[x,11.57,3.72],.17,.23,'green_edge','wire')
    # Filled tilted grip, contact at canonical anchor kept inside the handle.
    box('grip','grip_shoulder',[8,11.40,7.61],[1.23,.74,1.78],'black','stencil')
    beam('grip','grip_core',[8,7.36,8.66],[8,11.25,7.69],1.22,1.59,'rubber','grip')
    for side in (-1,1):
        beam('grip',f'palm_panel_{side}',[8+side*.60,7.60,8.61],[8+side*.60,10.72,7.83],.16,1.30,'rubber','grip')
    box('grip','heel',[8,7.05,8.83],[1.33,.35,1.33],'black','panel')
    for i in range(8):
        a=math.radians(i*45);r=.25
        box('grip',f'open_heel_loop_{i}',[8,6.82+r*math.cos(a),8.83+r*math.sin(a)],[1.13,.12,.22],'black','edge',('x',i*45))
    beam('grip','backstrap',[8,7.30,9.35],[8,11.40,8.32],1.02,.22,'black','grip')
    # Real U-shaped trigger guard, not a painted opaque side plate.
    beam('guard','front_guard',[8,11.44,3.65],[8,9.74,4.30],.52,.35,'black','stencil')
    beam('guard','guard_front_curve',[8,9.74,4.30],[8,9.28,5.28],.52,.35,'black','stencil')
    beam('guard','guard_base',[8,9.28,5.28],[8,9.42,6.40],.52,.35,'black','stencil')
    beam('guard','rear_guard',[8,9.42,6.40],[8,10.30,6.93],.52,.32,'black','stencil')
    beam('guard','orange_trigger',[8,11.34,5.04],[8,10.39,5.39],.32,.34,'orange','edge')
    beam('guard','trigger_toe',[8,10.39,5.39],[8,10.03,4.92],.32,.25,'orange','edge')
    # Hinged underbarrel bayonet with open circular pivot and a tapering blade.
    for i in range(8):
        a=math.radians(i*45);r=.36
        box('bayonet',f'pivot_ring_{i}',[8,10.66+r*math.cos(a),-1.03+r*math.sin(a)],[1.30,.15,.32],'steel','edge',('x',i*45))
    beam('bayonet','pivot_support',[8,11.62,-1.41],[8,10.90,-1.59],1.14,.49,'black','panel')
    beam('bayonet','hinge_arm',[8,11.50,-1.56],[8,10.68,-2.51],.86,.48,'steel','panel')
    beam('bayonet','blade_tang',[8,10.68,-2.51],[8,10.04,-3.03],.62,.37,'black','panel')
    beam('bayonet','blade_body',[8,10.10,-2.98],[8,8.75,-4.23],.44,.30,'silver','blade')
    beam('bayonet','blade_tip',[8,8.75,-4.23],[8,8.33,-4.62],.21,.18,'silver','blade')
    # Actual open rear sight notch. Purple shoulders match W31 standard paint.
    box('sights','front_sight_base',[8,13.57,-.88],[.87,.22,1.22],'black','edge')
    box('sights','front_sight_post',[8,13.91,-1.02],[.21,.46,.26],'silver','dot')
    box('sights','rear_sight_floor',[8,13.78,7.38],[1.12,.17,.84],'black','edge')
    for side in (-1,1):
        box('sights',f'rear_sight_ear_{side}',[8+side*.39,14.0,7.39],[.24,.41,.74],'purple','edge')
    inputs=[BASE,BB,'art/weapons/w31/references.json','src/main/resources/destiny/weapons/w30.json',
            'src/main/resources/assets/destiny/items/weapon/farewell.json',ART+'source-reference.json']
    raw=[RAW/'Farewell.blend',RAW/'Tex_1514.dds',PHOTO]
    return dict(id='farewell',stage='W142',source=meta,parts=parts,
        coordinate_policy=dict(anchor=meta['anchor'],scale=meta['scale'],mapping='world[X,Z,Y]*scale+anchor',muzzle='-Z',display='canonical exact'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw},
        identity=['angular black and blue body','green bound cable bundle','magenta receiver and guard stencil','ribbed heat sink','hanging bayonet with open pivot'],
        limitations=['Static authored paint approximates the W31 magenta stencil and material dye; not original dynamic PBR',
                    'Small muzzle side vents and rear slots use recessed UV, central bore and guard/pivot holes are physical',
                    'Full-only generic reload; no newly split magazine, animated bayonet or slide'])

def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])];u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=(1-u)[:,:,None]*(1-v)[:,:,None]*p[0]+u[:,:,None]*(1-v)[:,:,None]*p[1]+u[:,:,None]*v[:,:,None]*p[2]+(1-u)[:,:,None]*v[:,:,None]*p[3]
    return u,v,q

def tile(spec,face,w,h):
    u,v,q=world_points(spec['geometry'],face,w,h);mat=spec['material'];motif=spec['motif']
    rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
    rgb*=(.98+.025*np.sin(q[:,:,2]*7))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<.6]*=.68;rgb[(edge>.6)&(edge<1.3)]*=1.12
    side=face in ('east','west')
    if motif=='stencil' and side:
        y=q[:,:,1];z=q[:,:,2]
        r=np.sqrt(((z-5.78)/.73)**2+((y-12.04)/1.27)**2)
        stripe=((z>5.86)&(z<6.10)&(y<13.45))|((r>.81)&(r<1.06)&(z<5.86))
        rgb[stripe]=PALETTE['magenta']
    if motif in ('panel','rear_slots') and side:
        r=(abs(u-.53)<.34)&(abs(v-.48)<.08)
        rgb[r]=PALETTE['recess'];rgb[(abs(u-.53)<.34)&(v>.56)&(v<.60)]=PALETTE['steel']
    if motif=='rear_slots' and side:
        rgb[(u>.17)&(u<.7)&(v>.75)&(v<.85)]=PALETTE['recess']
    if motif=='muzzle_vents' and side:
        slot=(u>.31)&(u<.64)&(v>.35)&(v<.63);rgb[slot]=PALETTE['recess']
        for yy in (.14,.29,.44):rgb[(u<.14)&(abs(v-yy)<.035)]=PALETTE['steel']
    if motif=='wire':
        # Sparse black binding intervals, not fine barcode/noise on each strand.
        t=np.mod((q[:,:,2]+q[:,:,1]) *1.6,1);rgb[t<.13]*=.42
    if motif=='grip' and side:
        z=q[:,:,2];y=q[:,:,1];r=np.hypot(np.mod(z*3,1)-.5,np.mod(y*3,1)-.5)
        rgb[r<.17]*=.57
    if motif=='rail' and face=='up':rgb[np.mod(q[:,:,0]*6,1)<.17]*=.65
    if motif=='blade':
        rgb*=(.76+.24*np.cos((u-.5)*math.pi))[:,:,None]
        rgb[(u>.46)&(u<.51)]=PALETTE['steel']
    if motif=='fin':rgb[(u<.10)|(u>.90)]=PALETTE['silver']
    if motif=='dot':rgb[(abs(u-.5)<.14)&(abs(v-.28)<.15)]=PALETTE['recess']
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=24
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,e['name'],face,spec))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));x=y=2;row=0;ledger=[];uvs={}
    for h,w,name,face,spec in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow '+name)
        im=tile(spec,face,w,h);atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uvs[(name,face)]=[v*16/EDGE for v in [x,y,x+w,y+h]];ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    elements=[]
    for spec in d['parts']:
        e=copy.deepcopy(spec['geometry']);e['faces']={f:dict(uv=uvs[(e['name'],f)],texture='#0') for f in FACES};elements.append(e)
    d['atlas']=dict(size=EDGE,gutter=2,used_height=y+row+2,face_islands=len(ledger),islands=ledger)
    return atlas,dict(credit='W142 Farewell / authored solids / opaque default dye face atlas',
        textures={'0':'destiny:item/weapon/w123/farewell','particle':'destiny:item/weapon/w123/farewell'},
        elements=elements,display=json.loads((ROOT/BASE).read_bytes())['display'])

def model_triangles(model,atlas):
    m=copy.deepcopy(model)
    for e in m['elements']:
        if 'rotation' in e:
            r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return H['model_triangles']({'full':m},atlas)

def inspection(d,model,atlas):
    es=[];groups=[]
    for group in sorted({s['group'] for s in d['parts']}):
        children=[];names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        for e in model['elements']:
            if e['name'] not in names:continue
            b=copy.deepcopy(e);r=b.pop('rotation',None);b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
            es.append(b);children.append(b['uuid'])
        groups.append(dict(name=group,uuid=uid(group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Farewell W142 owned inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='farewell.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=copy.deepcopy(model['display']))

def comparison(d,meshes,atlas,model):
    w,h=820,400;sheet=Image.new('RGB',(2460,1780),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'FAREWELL W142 / SEMANTIC SOLIDS + CLEAN DEFAULT DYE UV',28)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((940,475));sheet.paste(photo,(0,50))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / full only / no alpha body shells','Angular blue/black body / magenta stencil / green cables','Ribbed heat sink / hinged underbarrel bayonet','Actual rectangular bore / open guard / rear sight notch','Small side vents = recessed UV, not physical perforations','Original anchor/axis/display/ADS/audio/gameplay preserved','Offline comparison, not native or PBR certification']):label(1000,85+i*48,line,23)
    raw=[];source_tex=np.array(Image.open(RAW/'Tex_1514.dds').convert('RGBA'))
    for m in meshes:
        if not m['materials']:continue
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);n/=max(np.linalg.norm(n),1e-20);raw.append((ps,uv,source_tex,n))
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/farewell.png'))
    ts=[raw,model_triangles(old,oldtex),model_triangles(model,atlas)];points=np.concatenate([m['vertices'] for m in meshes])
    for col,s in enumerate(['RIP / UNDYED DIFFUSE','OLD CANONICAL / READ ONLY',f'NEW / {len(model["elements"])} SEMANTIC CUBOIDS']):label(col*w+15,540,s)
    for row,(s,cam) in enumerate([('SIDE',[1,0,0]),('MUZZLE OBLIQUE',[1,.4,-.65]),('REAR OBLIQUE',[-1,.3,.6])]):
        ext=H['frame'](points,cam,w,h)
        for col,tris in enumerate(ts):
            im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,580+row*h));label(col*w+15,588+row*h,s,18)
    return png(sheet)

def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    counts={g:sum(s['group']==g for s in d['parts']) for g in sorted({s['group'] for s in d['parts']})}
    review=f'''# Farewell W142\n\n{len(model['elements'])} authored opaque semantic cuboids, filled receiver/grip, open rectangular bore, U guard and bayonet pivot. Recognizable bound green cable bundle, ribbed heat sink and hanging blade; black/blue standard paint with magenta authored stencil approximation. Small side slots are recessed UV, not physical perforations. No alpha body shell or rip-island transfer.\n\nSource: actual Farewell.blend library mesh extraction,3 W30 accepted objects/31946triangles; --disable-autoexec in separate background Blender, user session untouched. Reference raw undyed body diffuse Tex_1514.dds and W31 Bungie/light.gg default screenshot. Geometry recreated semantically, no ripped triangles exported.\n\nCanonical scale/anchor/axis/display/ADS/generic reload/gameplay/audio retained. Full-only; no new moving magazine, slide or bayonet animation. Static face paint does not recover original PBR. Offline comparisons are not native acceptance; targeted tests/BB/native recorded by master.\n'''
    out={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review.encode()}
    if include_comparison:out[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    p=np.concatenate([vertices(e) for e in model['elements']]);assert 0<len(model['elements'])<=1000
    manifest=dict(id='farewell',revision='W142',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),groups=counts,alpha_body_elements=0,triangle_adapter_elements=0,emitted_faces=6*len(model['elements']),max_assembled_elements=1000,texture_size=[EDGE,EDGE],actual_bounds=[p.min(0).tolist(),p.max(0).tolist()],source_bounds=meta['model_bounds'],source_triangles=31946,source_scale=meta['scale'],source_anchor=meta['anchor'],canonical_display_exact=True,full_only=True,native_accepted=False,input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={p:sha(data) for p,data in out.items()},limitations=d['limitations'])
    out[ART+'manifest.json']=encode(manifest);return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    for path,data in generate().items():
        target=ROOT/path
        if args.verify:assert target.is_file() and target.read_bytes()==data,path
        else:target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(data)
    print('Farewell W142', 'verified' if args.verify else 'generated')
if __name__=='__main__':main()
