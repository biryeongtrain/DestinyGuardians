#!/usr/bin/env python3
"""Bad Omens W130: authored full-only solid model; offline art candidate."""
import argparse
import base64
import copy
import json
import math
from pathlib import Path
import uuid

import numpy as np
from PIL import Image, ImageDraw

# Read-only common binary FBX reader, cuboid math, and CPU preview camera.
import generate_surface_w123_beloved as common

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/bad_omens/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/rocket_launcher/bad_omens.json'
MODEL = ASSET + 'models/weapon_surface_w123/bad_omens.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/bad_omens.png'
SOURCE = 'art/blockbench/weapons/w30/bad_omens.bbmodel'
RAW = Path('/tmp/destiny-weapons-w30/raw/bad_omens/extracted/Bad Omens')
PHOTO = Path('/tmp/destiny-weapons-w31/references/bad_omens.jpg')
REFS = Path('/tmp/destiny-weapons-w31/references.json')
EDGE = 1024
FACES = common.FACES
encode, sha, png = common.encode, common.sha, common.png
vertices, rotation = common.vertices, common.rotation
PALETTE = dict(teal=[58, 77, 79], steel=[157, 172, 173], dark=[40, 49, 51],
               wood=[94, 55, 35], rubber=[25, 28, 29], lens=[15, 36, 35])


def read_reference():
    meta = json.loads((ROOT / SOURCE).read_bytes())['destiny_w30']
    fbx = RAW / 'Bad Omens.fbx'
    assert sha(fbx.read_bytes()) == meta['source_files']['Bad Omens/Bad Omens.fbx']
    nodes = common.parse_fbx(fbx)
    meshes = []
    for n in next(n[2] for n in nodes if n[0] == 'Objects'):
        if n[0] != 'Geometry' or n[1][1].split('\0')[0] not in meta['source_objects']:
            continue
        cs = {c[0]: c for c in n[2]}
        raw = np.asarray(cs['Vertices'][1][0]).reshape(-1, 3)
        # W30 actual basis: X=thin, Y=height, Z=longitudinal; muzzle negative Z.
        pts = raw[:, [0, 2, 1]] * meta['scale'] + meta['anchor']
        indices = cs['PolygonVertexIndex'][1][0]
        assert sum(i < 0 for i in indices) * 3 == len(indices)
        meshes.append((pts, sum(i < 0 for i in indices)))
    pts = np.concatenate([p for p, _ in meshes])
    assert np.allclose([pts.min(0), pts.max(0)], meta['model_bounds'], atol=1e-6)
    assert sum(n for _, n in meshes) == meta['source_triangles']
    reference = next(r for r in json.loads(REFS.read_bytes()) if r['id'] == 'bad_omens')
    assert sha(PHOTO.read_bytes()) == reference['sha256']
    # Read actual neutral diffuse; never mutate it or confuse it with default dye.
    with Image.open(RAW / 'BOFrame_Diffuse.png') as diffuse:
        diffuse.load()
        diffuse_size = list(diffuse.size)
    return meta, reference, diffuse_size


def make_design(meta, reference, diffuse_size):
    specs = []

    def box(name, lo, hi, mat, group, motif='panel', turn=None):
        e = dict(name=name, **{'from': lo, 'to': hi})
        if turn:
            e['rotation'] = dict(origin=[round((a+b)/2, 6) for a,b in zip(lo,hi)], x=0, y=0, z=0)
            e['rotation'][turn[0]] = turn[1]
        specs.append(dict(geometry=e, material=mat, group=group, motif=motif))

    def center(name, c, size, mat, group, motif='panel', turn=None):
        box(name, [round(a-b/2,6) for a,b in zip(c,size)],
            [round(a+b/2,6) for a,b in zip(c,size)], mat, group, motif, turn)

    def tube(name, x, y, z0, z1, radius, thick, mat, group, motif):
        # Eight solid tangent wall beams form a thick octagonal tube, no cards.
        # Tangent overlap closes corners; the central bore remains truly empty.
        width = 2 * radius * math.tan(math.pi/8) + .012
        for i in range(8):
            a = i*45; r = radius-thick/2
            center(f'{name}_{i}', [x-r*math.sin(math.radians(a)), y+r*math.cos(math.radians(a)), (z0+z1)/2],
                   [width, thick, z1-z0], mat, group, motif, ('z',a))

    y = 12.2245
    tube('launch_tube', 8,y,-5.42,9.85,.985,.22,'teal','tube','tube')
    tube('aft_tube',8,y,9.80,20.95,.94,.24,'teal','tube','aft')
    tube('muzzle_rim',8,y,-5.834693,-5.15,1.05,.25,'steel','muzzle','vent')
    tube('vent_collar',8,y,12.15,13.02,1.025,.23,'steel','collars','vent')
    tube('breech_band',8,y,9.5,9.88,1.025,.24,'dark','collars','band')
    tube('tail_rim',8,y,20.65,21.165307,.99,.24,'steel','tail','band')
    # The forward handguard is a substantial wood frame with a real side slot.
    box('forearm_upper_wood',[7.63,10.56,.40],[8.37,10.85,5.05],'wood','forearm','wood')
    box('forearm_lower_wood',[7.63,10.08,.70],[8.37,10.32,4.72],'wood','forearm','wood')
    center('forearm_front_join',[8,10.48,.58],[.74,.64,.43],'wood','forearm','wood',('x',-24))
    center('forearm_rear_join',[8,10.48,4.88],[.74,.65,.47],'wood','forearm','wood',('x',24))
    box('forearm_top_saddle',[7.53,10.85,.48],[8.47,11.25,5.12],'dark','forearm','saddle')
    center('front_grip_wood',[8,8.86,1.88],[.77,2.80,.88],'wood','foregrip','wood')
    center('front_grip_front_bevel',[8,8.85,1.40],[.65,2.72,.23],'wood','foregrip','finger',('x',-3))
    center('front_grip_rear_bevel',[8,8.85,2.34],[.65,2.72,.22],'wood','foregrip','wood',('x',3))
    box('front_grip_heel',[7.57,7.321,1.31],[8.43,7.53,2.47],'steel','foregrip','band')
    box('front_grip_neck',[7.63,10.16,1.52],[8.37,10.66,2.25],'dark','foregrip','panel')
    for side in (-1,1):
        center(f'front_grip_bracket_{side}',[8+side*.46,10.48,2.12],[.22,1.06,.64],'teal','foregrip','pivot',('x',-12))
    # Continuous lower action housing and pistol hand-contact envelope.
    box('action_saddle',[7.48,10.51,5.08],[8.52,11.27,9.02],'dark','receiver','receiver')
    box('action_lower',[7.61,9.75,5.08],[8.39,10.52,8.54],'teal','receiver','receiver')
    box('action_front_lug',[7.55,9.55,5.16],[8.45,10.08,5.64],'dark','receiver','lug')
    center('pistol_wood',[8,8.25,8.13],[.76,2.96,1.02],'wood','pistol','wood',('x',-12))
    center('pistol_backstrap',[8,8.26,8.66],[.68,2.96,.22],'wood','pistol','wood',('x',-12))
    center('pistol_frontstrap',[8,8.31,7.58],[.66,2.83,.18],'wood','pistol','wood',('x',-12))
    center('pistol_heel',[8,6.87,8.43],[.83,.24,1.13],'wood','pistol','wood',('x',-12))
    center('pistol_mount',[8,9.79,8.04],[.91,.53,1.37],'dark','pistol','pivot',('x',-12))
    # Open bow: a forward upright, floor and rear elbow, with a small trigger.
    box('guard_front',[7.73,8.78,5.66],[8.27,9.82,5.89],'steel','guard','band')
    box('guard_floor',[7.73,8.66,5.87],[8.27,8.88,7.37],'dark','guard','band')
    center('guard_elbow',[8,8.89,7.32],[.54,.24,.53],'dark','guard','band',('x',-24))
    center('trigger',[8,9.28,6.62],[.18,.63,.17],'dark','guard','band',('x',-17))
    # Raised long top sight, physically hollow at either end; recessed lenses.
    box('sight_rail',[7.59,13.16,1.57],[8.41,13.35,8.08],'dark','top_sight','rail')
    for i,z in enumerate((2.10,7.50)):
        box(f'sight_foot_{i}',[7.60,13.30,z-.22],[8.40,13.57,z+.22],'teal','top_sight','pivot')
    tube('top_sight',8,13.59,1.67,7.94,.39,.13,'teal','top_sight','sight')
    box('top_front_glass',[7.76,13.35,1.93],[8.24,13.83,1.97],'lens','top_sight','glass')
    box('top_rear_glass',[7.76,13.35,7.66],[8.24,13.83,7.70],'lens','top_sight','glass')
    # Paired open notch, not a silhouette-only plate.
    box('top_notch_base',[7.69,13.97,3.88],[8.31,14.06,4.47],'dark','sights','panel')
    for side in (-1,1):
        center(f'top_notch_ear_{side}',[8+side*.22,14.11,4.15],[.16,.1385,.42],'teal','sights','panel')
    box('rear_sight_base',[7.74,13.17,17.74],[8.26,13.36,18.23],'steel','sights','band')
    for side in (-1,1):
        center(f'rear_sight_ear_{side}',[8+side*.18,13.55,17.99],[.12,.45,.21],'dark','sights','band')
    # Photo-right offset optic: independent solid mount, deep lip and lens.
    box('side_optic_mount',[8.70,11.12,4.54],[9.20,12.02,8.02],'teal','optic_mount','receiver')
    center('side_optic_front_foot',[9.40,11.63,4.34],[1.43,.28,.42],'steel','optic_mount','pivot')
    center('side_optic_rear_foot',[9.40,11.63,6.50],[1.43,.28,.42],'steel','optic_mount','pivot')
    tube('right_optic',9.72,12.18,3.31,6.66,.43,.13,'teal','right_optic','sight')
    tube('right_optic_lip',9.72,12.18,3.15,3.43,.48,.14,'steel','right_optic','band')
    box('right_recessed_glass',[9.425,11.885,3.72],[10.015,12.475,3.76],'lens','right_optic','glass')
    # Opaque rubber ocular housing with UV bellows; major mounting depth solid.
    center('optic_bellows_core',[9.72,12.18,7.17],[.76,.76,1.10],'rubber','right_optic','bellows')
    center('optic_bellows_bevel_a',[9.72,12.18,7.17],[.74,.74,1.10],'rubber','right_optic','bellows',('z',45))
    center('optic_rear_socket',[9.60,12.16,7.96],[.94,.94,.53],'dark','right_optic','pivot')
    box('breech_side_spine',[8.91,11.84,8.01],[9.15,12.25,10.00],'teal','receiver','rail')
    box('breech_bottom_spine',[7.71,11.01,8.80],[8.29,11.30,12.24],'dark','receiver','rail')
    box('aft_lock_lug',[7.60,10.61,11.21],[8.40,11.30,11.65],'dark','receiver','pivot')

    inputs = [BASE, SOURCE, ASSET+'textures/item/weapon/w30/bad_omens.png',
              ASSET+'models/weapon/rocket_launcher/bad_omens_ads.json',
              'scripts/generate_surface_w123_beloved.py']
    raw_inputs = [RAW/'Bad Omens.fbx',RAW/'BOFrame_Diffuse.png',RAW/'BOSight_Diffuse.png',PHOTO,REFS]
    return dict(id='bad_omens',family='rocket_launcher',revision='W130',source=meta,
                method='Hand-authored semantic solid cuboids; no connected-island conversion or voxel transplant',
                reference=reference,neutral_diffuse_size=diffuse_size,palette=PALETTE,parts={'full':specs},
                atlas=dict(size=EDGE,gutter=2,texels_per_unit=22),
                frame=dict(anchor=meta['anchor'],scale=meta['scale'],muzzle_axis='-Z',tube_axis=[8,y],
                           foregrip_contact=[8,8.6,1.88],pistol_contact=[8,8.2,8.13]),
                integration='Full candidate only. Preserve current display, ADS, generic reload, timing and audio; master registers candidate.',
                identity=['long dark desaturated teal steel tube','silver muzzle and vented collars',
                          'brown wood front frame, vertical foregrip and pistol grip',
                          'raised top sight tube; right recessed optic; true muzzle bore'],
                input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
                raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
                limitations=['Offline CPU preview only; native integration pending master.',
                             'Octagonal cross sections simplify smooth source tubes; RGBA has no live metallic reflection.',
                             'Shallow collar vents, grooves and grip grain are face UV; major rings, bore, guard and sight recesses are solid geometry.'])


def face_position(spec, face, u, v):
    p = vertices(spec['geometry'])[list(FACES[face])]
    return ((1-u)*(1-v))[:,:,None]*p[0] + (u*(1-v))[:,:,None]*p[1] + (u*v)[:,:,None]*p[2] + ((1-u)*v)[:,:,None]*p[3]


def tile(spec, face, w, h):
    u,v = np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    xyz = face_position(spec,face,u,v); z=xyz[:,:,2]; y=xyz[:,:,1]
    mat=spec['material']; motif=spec['motif']
    rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
    rgb *= (.97+.065*np.exp(-((v-.3)/.38)**2))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    rgb[edge<.7]*=.72
    rgb[(edge>=.7)&(edge<1.5)]*=1.12
    # Broad uninterrupted steel panels; grooves align across adjacent faces.
    if motif in ('tube','aft') and face not in ('north','south'):
        if motif=='tube':
            phase=np.mod((z+.28*(y-12.2245)+1.5)/.40,1)
            grooves=(z>-1.60)&(z<1.33)&(phase<.075)
            lips=(z>-1.60)&(z<1.33)&(phase>.075)&(phase<.14)
        else:
            phase=np.mod((z-13.85)/.86,1)
            grooves=(z>14.1)&(z<18.45)&(phase<.05)
            lips=(z>14.1)&(z<18.45)&(phase>.05)&(phase<.11)
        rgb[grooves]*=.46;rgb[lips]*=1.65
        for seam in (7.95,10.05,13.12,19.1):
            rgb[abs(z-seam)<.035]*=1.7
        # Restrained directional brushed steel rather than source grime.
        rgb += (1.0*np.sin(z*27+y*1.8))[:,:,None]
    if motif=='vent' and face in ('up','down'):
        vent=(u>.25)&(u<.75)&(v>.23)&(v<.67)
        rgb[vent]=[18,29,31]
        rgb[(u>.25)&(u<.75)&(v>.67)&(v<.75)]=[194,207,204]
    if motif in ('band','vent'):
        rgb[(edge>2)&(edge<3)]*=.75
    if mat=='wood':
        # Longitudinal grain follows the component rather than copying rip UVs.
        if spec['group']=='forearm':
            grain=np.sin(y*83+2*np.sin(z*1.4))+.4*np.sin(y*157+z*3)
        else:
            grain=np.sin(z*72+2*np.sin(y*1.6))+.4*np.sin(z*141+y*3)
        rgb *= (1+.058*grain)[:,:,None]
        rgb += (2.6*np.sin(y*4+z*2))[:,:,None]
        if motif=='finger':
            rgb[(np.mod(y-.3,.46)<.065)&(y>7.9)&(y<9.7)]*=.68
    if motif in ('receiver','rail','saddle') and face in ('east','west'):
        border=(u>.1)&(u<.9)&((abs(v-.22)<.022)|(abs(v-.79)<.022))
        rgb[border]*=.5
        rgb[(u>.18)&(u<.48)&(v>.43)&(v<.54)]*=.48
    if motif=='pivot' and face in ('east','west'):
        r=((u-.5)/.29)**2+((v-.52)/.29)**2
        rgb[(r>.72)&(r<1.05)]*=1.6
        rgb[r<.58]*=.75
    if motif=='bellows':
        rgb[np.mod(z,.28)<.09]*=.55
        rgb[(np.mod(z,.28)>.09)&(np.mod(z,.28)<.14)]*=1.25
    if motif=='sight':
        rgb[abs(z-6.45)<.035]*=1.7
    if motif=='glass':
        r=((u-.5)*2)**2+((v-.5)*2)**2
        rgb[:]=[9,22,23]
        rgb += np.clip(1-r,0,1)[:,:,None]*[5,22,20]
        rgb += np.exp(-(((u-.28)/.12)**2+((v-.24)/.10)**2))[:,:,None]*[55,87,83]
    return Image.fromarray(np.dstack((np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,dtype='uint8'))))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));tiles=[]
    for spec in d['parts']['full']:
        pts=vertices(spec['geometry'])
        for face,indices in FACES.items():
            p=pts[list(indices)]
            w=max(6,min(320,math.ceil(np.linalg.norm(p[1]-p[0])*22)))
            h=max(6,min(320,math.ceil(np.linalg.norm(p[3]-p[0])*22)))
            tiles.append((spec,face,w,h))
    tiles.sort(key=lambda t:(-t[3],-t[2],t[0]['geometry']['name'],t[1]))
    x=y=2;row=0;uv={};islands=[]
    for spec,face,w,h in tiles:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow')
        painted=tile(spec,face,w,h)
        atlas.paste(Image.fromarray(np.pad(np.asarray(painted),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        name=spec['geometry']['name'];uv[name,face]=[q*16/EDGE for q in (x,y,x+w,y+h)]
        islands.append(dict(element=name,face=face,rect=[x,y,x+w,y+h]))
        x+=w+4;row=max(row,h)
    es=[]
    for spec in d['parts']['full']:
        e=copy.deepcopy(spec['geometry']);e['faces']={f:dict(uv=uv[e['name'],f],texture='#0') for f in FACES};es.append(e)
    d['atlas'].update(islands=islands,used_height=y+row+2)
    model=dict(credit='W130 Bad Omens | authored semantic solids / default-photo face UV | offline candidate',
               textures={'0':'destiny:item/weapon/w123/bad_omens','particle':'destiny:item/weapon/w123/bad_omens'},
               elements=es,display=json.loads((ROOT/BASE).read_bytes())['display'])
    return atlas,model


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w130:bad_omens:'+name))


def inspection(d,model,atlas):
    elements=[];groups={}
    for spec,e in zip(d['parts']['full'],model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation',{})
        b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,
                 origin=r.get('origin',[8,8,8]),rotation=[r.get(a,0) for a in 'xyz'])
        for f in b['faces'].values():f.update(texture=0,uv=[q*EDGE/16 for q in f['uv']])
        elements.append(b);groups.setdefault(spec['group'],[]).append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},
                name='Bad Omens W130 / editable solids / offline inspection',
                resolution={'width':EDGE,'height':EDGE},elements=elements,
                outliner=[dict(name=g,uuid=uid(g),origin=[8,8,8],rotation=[0,0,0],children=children,export=True) for g,children in groups.items()],
                textures=[dict(name='bad_omens.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,
                               uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
                display=model['display'],destiny_w130=dict(nativeAccepted=False,frame=d['frame'],fullOnly=True))


def comparison(d,model,atlas):
    w,h=1000,300
    sheet=Image.new('RGB',(2000,1730),'#161e27');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e0e8ec',font_size=size)
    label(22,14,'BAD OMENS / W130 / semantic solid remodel / OFFLINE CPU INSPECTION',29)
    photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((1360,690));sheet.paste(photo,(12,55))
    label(1380,100,'Actual default photo',25)
    for i,line in enumerate(['Dark desaturated teal steel','Silver muzzle / vented rings','Brown wood grips and frame','Top sight + recessed right optic','Neutral raw diffuse is NOT default dye']):
        label(1380,155+i*39,line,20)
    old=json.loads((ROOT/BASE).read_bytes())
    oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/bad_omens.png'))
    oldtris=common.model_triangles({'canonical':old},oldtex)
    newtris=common.model_triangles({'full':model},atlas)
    pts=np.concatenate([vertices(e) for e in old['elements']]+[vertices(e) for e in model['elements']])
    label(22,680,'W30 LOCAL CANONICAL / 253 cuboids / neutral projected texture',22)
    label(1022,680,f'W130 / {len(model["elements"])} solid cuboids / authored default-dye UV',22)
    for row,(name,cam) in enumerate([('RIGHT SIDE',[1,0,0]),('MUZZLE OBLIQUE',[1,.50,-.72]),('REAR / OPPOSITE SIDE',[-1,.42,.68])]):
        extent=common.frame(pts,cam,w,h)
        for col,tris in enumerate((oldtris,newtris)):
            im,_=common.render(tris,cam,extent,(w,h));sheet.paste(im,(col*w,715+row*h))
            label(col*w+15,723+row*h,name,18)
    # Four actual-depth closeups, kept in the same owned image.
    for i,(name,gs,cam) in enumerate([
        ('BORE / thick walls',('muzzle','tube'),[.11,.07,-1]),
        ('OPEN WOOD FRAME',('forearm',),[1,.22,-.25]),
        ('GUARD / hand contact',('guard','pistol'),[1,.15,-.25]),
        ('RIGHT OPTIC / recess',('right_optic','optic_mount'),[.55,.18,-1])]):
        selected=[e for s,e in zip(d['parts']['full'],model['elements']) if s['group'] in gs]
        if i==0:
            selected=[e for e in selected if not e['name'].startswith('aft_tube')]
        p=np.concatenate([vertices(e) for e in selected])
        tris=common.model_triangles({'detail':dict(elements=selected)},atlas)
        im,_=common.render(tris,cam,common.frame(p,cam,500,240),(500,240))
        # Extend this same owned image below the unobscured full-model rows.
        if i==0:
            extended=Image.new('RGB',(2000,2000),'#161e27');extended.paste(sheet,(0,0));sheet=extended;draw=ImageDraw.Draw(sheet)
        sheet.paste(im,(i*500,1645));label(i*500+12,1650,name,18)
    label(20,1910,'Same camera and scale in each full comparison row. Details isolate unchanged final solids.',19)
    label(20,1946,'Native pack/parser, first/third person, ADS, generic reload/audio and 10-20 displays: PENDING MASTER.',20)
    return png(sheet)


def review(count):
    return f'''# Bad Omens W130 — offline remodel

Actual default photograph: `/tmp/destiny-weapons-w31/references/bad_omens.jpg`, Bungie item 991314988, with provenance/default dyes from `references.json`. The opened photo shows a long dark desaturated teal steel tube, silver vented muzzle and collars, brown wooden front frame/vertical grip and pistol grip, raised top sight and a right-offset recessed optic. The original BOFrame diffuse is neutral gray; its wood grain and panel locations are evidence, not the finished default dye.

The full candidate contains **{count} opaque solid cuboids**, zero triangle adapter elements, zero alpha cards. Long octagonal wall beams preserve the launcher cross section and deep muzzle bore. Major collars have actual radial depth. Shallow circumferential/diagonal grooves and vent pockets use face UV. The wood frame has a real slot, the trigger bow is open, and both sight tubes have recessed glass behind solid lips. Grips and action are filled volumes; no source connected islands or voxels are transplanted. The authored atlas is 1024 square with independent per-face islands and two-pixel extruded gutters. Muted teal, satin steel, restrained wood grain and coherent grooves replace the undyed projected texture. No invented writing or decorative hardware.

`comparison.png` contains the actual photo, clearly labeled W30 canonical neutral reconstruction and new side/front/rear obliques at matching camera scale. Detail views isolate unchanged final solids for the bore, open wooden frame, trigger guard and recessed optic. The editable inspection project embeds exactly the final model solids and texture; semantic groups are editing groups, not split runtime resources.

Frame: source anchor [8,8,8], source scale 24.638767902867134, muzzle negative Z, tube center [8,12.2245], source muzzle/tail endpoints retained. Front and pistol grip envelopes remain at the source contacts (z about 1.9 and 8.1). The canonical full display dictionary is copied exactly. Current ADS, generic reload, timing/audio, registries and Java are untouched. Only one full candidate resource is supplied under weapon_surface_w123; master owns registration and native integration.

Validation is targeted offline schema, assembled budget, opaque face UV, input hashes, frame/contact, practical bore/guard/frame/optic opening probes, embedded project parity and deterministic regeneration. Curved surfaces are visibly octagonal, collar vents are shallow UV pockets, and live metallic reflection/source micro wear is simplified. Native 26.3 parser/rotations, pack loading, first/third-person hand placement, ADS sight alignment, generic reload/firing/audio and 10–20 simultaneous displays remain pending master. No GUI, game, Gradle, native success or performance claim is made.
'''


def generate():
    meta,ref,size=read_reference();d=make_design(meta,ref,size);atlas,model=compile_model(d)
    n=len(model['elements']);points=np.concatenate([vertices(e) for e in model['elements']])
    outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'comparison.png':comparison(d,model,atlas),
             ART+'review.md':review(n).encode()}
    counts={g:sum(s['group']==g for s in d['parts']['full']) for g in sorted({s['group'] for s in d['parts']['full']})}
    manifest=dict(id='bad_omens',revision='W130',family='rocket_launcher',counts={'full':n},
                  groups=counts,assembled_elements=n,opaque_cuboids=n,triangle_adapter_elements=0,alpha_elements=0,
                  max_assembled_elements=1000,emitted_faces=n*6,full_only=True,native_accepted=False,
                  source_anchor=meta['anchor'],source_scale=meta['scale'],source_bounds=meta['model_bounds'],
                  actual_bounds=[points.min(0).round(7).tolist(),points.max(0).round(7).tolist()],
                  source_triangles=meta['source_triangles'],canonical_display_exact=True,
                  texture_size=[EDGE,EDGE],frame=d['frame'],input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
                  generator_sha256=sha(Path(__file__).read_bytes()),output_sha256={p:sha(b) for p,b in sorted(outputs.items())},
                  limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate()
    batch=json.loads((ROOT/'docs/qa/2026-10-26/w130/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w130-bad_omens'))
    assert set(outputs)<=owned
    for p,b in outputs.items():
        dest=ROOT/p
        if args.verify:assert dest.is_file() and dest.read_bytes()==b,'Regeneration differs: '+p
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
    m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts; full={m["assembled_elements"]}; faces={m["emitted_faces"]}')


if __name__=='__main__':main()
