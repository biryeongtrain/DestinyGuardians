#!/usr/bin/env python3
"""Distant Relation W132: authored solid volumes, full-only offline candidate.

Run with the bundled numpy/Pillow Python and -B. No DCC, native or game claims.
Only the seven generated files in this feature's ten-path scope are written.
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
ART = 'art/weapons/w123/distant_relation/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/scout_rifle/distant_relation.json'
MODEL = ASSET + 'models/weapon_surface_w123/distant_relation.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/distant_relation.png'
BB = 'art/blockbench/weapons/w30/distant_relation.bbmodel'
HELPER = 'scripts/generate_surface_w123_beloved.py'
BATCH = 'docs/qa/2026-10-26/w132/batch.json'
RAW = Path('/tmp/destiny-weapons-w30/raw/distant_relation/extracted/Distant Relation')
PHOTO = Path('/tmp/destiny-weapons-w31/references/distant_relation.jpg')
REFERENCES = Path('/tmp/destiny-weapons-w31/references.json')
EDGE = 1024
PALETTE = dict(teal=[39, 65, 66], teal_edge=[55, 80, 80], steel=[167, 177, 177],
               dark=[30, 41, 42], wood=[101, 69, 49], wood_top=[116, 81, 57],
               rubber=[28, 32, 32], glass=[19, 55, 54])
_HELP = None


def helper():
    global _HELP
    if _HELP is None:
        _HELP = runpy.run_path(str(ROOT / HELPER))
    return _HELP


def encode(v):
    return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def png(im):
    buf = io.BytesIO(); im.save(buf, format='PNG'); return buf.getvalue()


def uid(s):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'destiny:w132:distant_relation:'+s))


def vertices(e):
    return helper()['vertices'](e)


def source():
    """Read actual W30 metadata and inert FBX arrays, never transplant islands."""
    meta = json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha((RAW/'Distant Relation.fbx').read_bytes()) == meta['source_files']['Distant Relation/Distant Relation.fbx']
    roots = helper()['parse_fbx'](RAW/'Distant Relation.fbx')
    objects = next(n[2] for n in roots if n[0]=='Objects')
    links = [n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models = {n[1][0]:n for n in objects if n[0]=='Model'}
    points = []; triangles = 0; observed = []
    for n in objects:
        if n[0]!='Geometry':
            continue
        m = models[next(p for c,p in links if c==n[1][0])]
        name = m[1][1].split('\x00')[0]
        if name not in meta['source_objects']:
            continue
        props = {p[1][0]:p[1][4:] for c in m[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'], [-90,0,0], atol=1e-4)
        assert np.allclose(props['Lcl Scaling'], [100,100,100], atol=2e-5)
        assert np.allclose(props['Lcl Translation'], [0,0,0], atol=1e-6)
        cs = {c[0]:c for c in n[2]}
        raw = np.array(cs['Vertices'][1][0]).reshape(-1,3)
        points.append(raw[:,[0,2,1]]*meta['scale']+meta['anchor'])
        triangles += sum(i<0 for i in cs['PolygonVertexIndex'][1][0])
        observed.append(name)
    points = np.concatenate(points)
    assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=1e-5)
    assert triangles==meta['source_triangles']==29579
    assert observed==meta['source_objects']
    # Read actual undyed diffuse; it is evidence, never the finished dye atlas.
    with Image.open(RAW/'DRFrame_Diffuse.png') as im:
        im.load(); assert im.size==(2048,2048)
    ref = next(r for r in json.loads(REFERENCES.read_bytes()) if r['id']=='distant_relation')
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meta, ref


def design(meta, ref):
    parts = []

    def box(group, name, c, size, mat, motif='panel', angles=(0,0,0)):
        e = dict(name=name, **{'from':[round(a-b/2,6) for a,b in zip(c,size)],
                              'to':[round(a+b/2,6) for a,b in zip(c,size)]})
        if any(angles):
            e['rotation'] = dict(origin=list(c), **dict(zip('xyz',angles)))
        parts.append(dict(group=group, material=mat, motif=motif, geometry=e))

    def beam(group, name, a, b, width, depth, mat, motif='panel'):
        # a,b are [z,y]; beam local long axis +Z, native pivot unchanged.
        z0,y0 = a; z1,y1 = b
        box(group,name,[8,(y0+y1)/2,(z0+z1)/2],
            [width,depth,math.hypot(z1-z0,y1-y0)],mat,motif,
            (-math.degrees(math.atan2(y1-y0,z1-z0)),0,0))

    def ring(group, name, z0, z1, y, radius, thick, mat):
        # Eight opaque solid tangent walls, true bore/recess; no alpha silhouette.
        r = radius-thick/2
        w = 2*radius*math.tan(math.pi/8)+.009
        for i in range(8):
            a = math.radians(i*45)
            box(group,f'{name}_{i}',[8-r*math.sin(a),y+r*math.cos(a),(z0+z1)/2],
                [w,thick,z1-z0],mat,'rim',(0,0,i*45))

    def prism(group,name,c,width,height,length,mat,motif='panel'):
        # Filled faceted cross section in three intersecting structural cubes.
        box(group,name+'_core',c,[width*.72,height,length],mat,motif)
        box(group,name+'_shoulder_l',c,[width,height*.70,length],mat,motif)
        # One continuous top land defines the broad readable plane.

    # Native barrel centre y=10.357, muzzle -8.263; ends/source frame retained.
    ring('muzzle','silver_brake',-8.263094,-6.18,10.357,.275,.085,'steel')
    prism('barrel','barrel',[8,10.357,-4.94],.48,.48,2.48,'teal','barrel')
    ring('barrel','barrel_collar',-4.14,-3.83,10.357,.345,.13,'steel')
    box('sight','sight_base',[8,10.78,-3.72],[.79,.22,.65],'teal')
    box('sight','sight_left',[7.68,11.035,-3.72],[.16,.37,.56],'steel')
    box('sight','sight_right',[8.32,11.035,-3.72],[.16,.37,.56],'steel')
    box('sight','sight_post',[8,10.98,-3.72],[.105,.29,.19],'dark')
    # Broad filled shroud, vent pockets authored in individual face UVs.
    box('shroud','shroud_main',[8,10.37,.09],[1.01,1.07,7.04],'teal','vents')
    box('shroud','shroud_roof',[8,10.98,.09],[.71,.24,7.04],'teal_edge','vents')
    for s in (-1,1):
        box('shroud',f'shroud_shoulder_{s}',[8+s*.42,10.88,.09],
            [.29,.29,7.04],'teal','vents',(0,0,s*45))
    box('shroud','shroud_rear_sleeve',[8,10.28,3.55],[1.28,1.58,.60],'teal','collar')
    # Long solid wood fore-end, slightly rising lower contour, broad grain panels.
    beam('forewood','forewood_main',[-3.38,9.73],[4.56,9.49],1.07,.61,'wood','forewood')
    box('forewood','forewood_bed',[8,9.97,.59],[1.10,.27,7.80],'wood_top','grain')
    box('forewood','forewood_nose',[8,9.75,-3.42],[1.01,.57,.23],'dark')
    # Main action and two stepped sections, no thin side-card replacement.
    box('receiver','receiver_core',[8,10.14,6.03],[1.10,1.62,4.50],'teal','receiver')
    box('receiver','action_top',[8,10.97,6.07],[.84,.29,4.30],'teal_edge','action')
    box('receiver','receiver_tail',[8,9.91,8.47],[1.06,1.31,.62],'teal','receiver')
    box('receiver','lower_action',[8,8.99,6.91],[.97,.69,2.47],'dark','receiver')
    # Silver bolt and offset handle; not duplicated on both sides.
    box('bolt','bolt_slide',[8.574,10.43,6.46],[.11,.39,2.15],'steel','bolt')
    box('bolt','bolt_stem',[8.71,9.79,4.33],[.46,.19,.24],'steel')
    box('bolt','bolt_knob',[8.81,9.79,4.30],[.28,.46,.46],'steel','dial',(0,0,22.5))
    # Wood stock is filled above/below a large physical thumb opening.
    beam('stock','stock_comb_rise',[8.60,10.37],[11.32,10.77],1.08,.78,'wood_top','grain')
    box('stock','stock_comb',[8,10.67,13.24],[1.10,1.12,4.34],'wood','stock')
    box('stock','stock_cheek',[8,11.17,13.47],[.95,.29,3.84],'wood_top','grain')
    beam('stock','stock_grip',[7.94,9.70],[8.75,7.74],.96,.83,'wood','gripwood')
    beam('stock','stock_lower_sweep',[8.98,7.74],[14.94,8.18],1.03,.62,'wood','stock')
    # Filled rear stock, not the perimeter of a huge invented skeleton opening.
    box('stock','stock_main_solid',[8,9.34,12.64],[1.06,2.48,5.28],'wood','stock')
    box('stock','thumbhole_rear_web',[8,9.19,10.05],[1.06,2.12,.36],'wood','stock')
    box('stock','stock_heel',[8,9.49,15.11],[.92,2.95,.74],'wood','stock')
    beam('stock','stock_toe',[14.04,8.06],[15.43,8.16],.92,.67,'wood','grain')
    # Butt plate is dark teal metal with an actual slanted lower toe.
    beam('stock','buttplate',[15.48,7.67],[15.63,11.34],.93,.24,'teal','butt')
    beam('stock','buttplate_heel',[15.70,11.29],[16.45,10.94],.66,.23,'steel','butt')
    beam('stock','buttplate_toe',[15.54,7.66],[16.64,7.20],.65,.20,'dark','butt')
    box('stock','butt_fastener',[8,10.99,16.57],[.39,.37,.33],'teal','dial')
    # Large dark under-hand loop from the photo, open through the weapon's width.
    beam('hand_loop','loop_front',[6.35,8.73],[7.07,6.35],.63,.27,'dark','loop')
    beam('hand_loop','loop_bottom',[7.07,6.35],[9.63,6.25],.65,.27,'steel','loop')
    beam('hand_loop','loop_back',[9.63,6.25],[8.75,9.13],.95,.70,'teal','gripmetal')
    beam('hand_loop','loop_root',[6.35,8.73],[6.97,8.70],.81,.24,'teal','loop')
    # Small trigger guard is separate, ahead of the grip and above the large loop.
    beam('trigger','trigger_guard_front',[6.70,8.72],[6.89,7.99],.43,.14,'steel','loop')
    beam('trigger','trigger_guard_base',[6.89,7.99],[8.00,7.91],.43,.14,'steel','loop')
    beam('trigger','trigger_guard_back',[8.00,7.91],[8.26,8.70],.43,.14,'dark','loop')
    beam('trigger','trigger',[7.55,8.75],[7.40,8.27],.15,.17,'dark')
    # Short slanted magazine/heel remains integrated in this full-only candidate.
    beam('magazine','magazine_body',[10.14,5.88],[11.30,7.50],.64,.65,'teal','magazine')
    beam('magazine','magazine_floor',[9.86,5.76],[10.50,5.88],.72,.23,'dark','magazine')
    box('stock','sling_mount',[8,7.29,13.33],[.34,.39,.48],'dark','dial')
    # Optic: solid centre housing, real front/rear recess and distinct mounts.
    for i,z in enumerate((4.52,6.70)):
        box('optic',f'optic_mount_{i}',[8,11.24,z],[.72,.26,.42],'dark')
        box('optic',f'optic_foot_{i}',[8,11.12,z],[1.00,.14,.64],'teal')
    prism('optic','optic_housing',[8,11.88,5.65],1.08,1.30,2.88,'teal','optic')
    box('optic','optic_roof',[8,12.53,5.65],[.72,.18,2.79],'teal','optic')
    ring('optic','objective_rim',3.80,4.31,11.88,.535,.13,'teal')
    ring('optic','ocular_rim',6.99,7.51,11.88,.535,.13,'steel')
    box('optic','objective_glass',[8,11.88,4.30],[.78,.78,.035],'glass','lens')
    box('optic','ocular_glass',[8,11.88,7.005],[.78,.78,.035],'glass','lens')
    # Two lateral adjustment bosses are source-backed major depth, not screw cubes.
    box('optic','optic_dial_near',[8.62,11.51,5.80],[.25,.53,.53],'teal_edge','dial',(45,0,0))
    box('optic','optic_dial_far',[7.38,11.51,5.80],[.25,.53,.53],'dark','dial',(45,0,0))
    inputs = [BASE, BB, HELPER, BATCH, ASSET+'textures/item/weapon/w30/distant_relation.png']
    return dict(id='distant_relation',family='scout_rifle',revision='W132',
        construction='authored semantic opaque solid cuboids; full only', parts=parts,
        source=dict(anchor=meta['anchor'],scale=meta['scale'],bounds=meta['model_bounds'],
                    axis=meta['source_axis'],triangles=meta['source_triangles']),
        reference=ref,palette=PALETTE,atlas=dict(size=[EDGE,EDGE],gutter=2,texels_per_unit=23),
        openings=dict(thumbhole=[8,9.12,9.38],hand_loop=[8,7.16,8.10],
                      trigger_guard=[8,8.32,7.03],muzzle=[8,10.357,-7.70],
                      objective_recess=[8,11.88,3.99],front_sight=[8,11.18,-3.72]),
        hand_contact=[8,8.55,8.30],muzzle_axis='-Z',native_accepted=False,
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in
                         [RAW/'Distant Relation.fbx',RAW/'DRFrame_Diffuse.png',PHOTO,REFERENCES]},
        limitations=['Offline candidate; native master QA pending.',
                     'Subtle stock curvature and reflective finish simplified; no runtime PBR.',
                     'Shroud vent relief uses opaque face UV; muzzle/stock/guards/sight/optic recess use real geometry.'])


def tile(spec, face, w, h):
    """Purpose-painted per-face panels, opaque and deterministic, no projection."""
    u,v = np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    mat = spec['material']; motif = spec['motif']; e = spec['geometry']
    rgb = np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
    rgb *= (.94+.09*np.exp(-((v-.28)/.30)**2))[:,:,None]
    edge = np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
    rgb[edge<.8] *= .72
    rgb[(edge>=.8)&(edge<1.8)] *= 1.13
    side = face in ('east','west')
    pts = vertices(e)[list(helper()['FACES'][face])]
    pos = ((1-u)*(1-v))[:,:,None]*pts[0]+(u*(1-v))[:,:,None]*pts[1]+(u*v)[:,:,None]*pts[2]+((1-u)*v)[:,:,None]*pts[3]
    z = pos[:,:,2]; y = pos[:,:,1]; x = pos[:,:,0]
    if mat.startswith('wood'):
        # Continuous world-space walnut grain bends around the real stock hole.
        grain = np.sin(y*31+2.6*np.sin(z*.7)+.5*np.sin(z*3))
        fine = np.sin(y*85+3*np.sin(z*.9))
        rgb *= (1+.065*grain+.022*fine)[:,:,None]
        if side and motif=='forewood':
            ribs = (np.mod(z+.14,.095)<.027)&(y<9.80)&(y>9.40)
            rgb[ribs] *= .75
        if side and motif=='gripwood':
            cross = ((np.mod(z*9+y*7,1)<.10)|(np.mod(z*9-y*7,1)<.10))
            rgb[cross] *= .82
        if side and motif=='stock':
            # Restrained edge channel, no invented insignia or mirrored lettering.
            rgb[(abs(y-10.58)<.025)&(z>11.5)&(z<14.8)] *= .81
    if motif=='vents' and face in ('east','west','up'):
        # Observed long shroud has several rows of small pill-shaped recesses.
        # Positions use world coordinates so shoulder/roof seams do not reset rows.
        if face=='up':
            row = np.minimum(abs(x-7.79),abs(x-8.21)); across = row/.055
        else:
            row = np.minimum(abs(y-10.68),abs(y-10.91)); across = row/.047
        along = (np.mod(z+2.97,.61)-.305)/.19
        inside = (along**4+across**4<1)&(z>-3.15)&(z<3.16)
        lip = (along**4+across**4<1.55)&~inside&(z>-3.15)&(z<3.16)
        rgb[inside] *= .34; rgb[lip] *= 1.25
    if motif in ('receiver','action','optic') and side:
        inset = (u>.10)&(u<.90)&(v>.18)&(v<.82)
        rgb[inset&((abs(v-.22)<.012)|(abs(v-.77)<.012))] *= .65
        if motif=='receiver':
            p = (z>5.35)&(z<7.32)&(y>10.35)&(y<10.65)
            rgb[p] *= .43
    if motif in ('dial','bolt') and face in ('east','west'):
        r = np.sqrt(((u-.5)*2)**2+((v-.5)*2)**2)
        rgb[(r>.63)&(r<.77)] *= .44
        rgb[(abs(u-.5)<.035)&(v>.27)&(v<.73)] *= .40
    if motif=='gripmetal' and side:
        r=np.sqrt(((z-9.30)/.22)**2+((y-7.36)/.25)**2)
        rgb[r<1]=[146,158,157]
        rgb[(r>.76)&(r<.88)] *= .52
        rgb[(abs(z-9.30)<.025)&(abs(y-7.36)<.10)] *= .37
    if motif=='magazine' and side:
        stripe = (np.mod(z*4.0-y*2.8,1)<.12)&(edge>3)
        rgb[stripe] *= .56
    if e['name'].startswith('silver_brake') and face in ('east','west','up','down'):
        # Brake's longitudinal relief and small rear port pattern stay UV detail.
        stripe = (np.mod(z+8.2,.66)<.055)&(edge>2)
        rgb[stripe] *= .46
        dots = (np.sin(z*26)> .78)&(np.sin((x+y)*30)>.8)&(z>-6.90)
        rgb[dots] *= .33
    if motif=='lens' and face in ('north','south'):
        r = np.sqrt(((x-8)/.48)**2+((y-11.88)/.48)**2)
        rgb[:] = [10,29,30]
        rgb += np.clip(1-r,0,1)[:,:,None]*[8,35,31]
        glint = np.exp(-(((x-7.85)/.12)**2+((y-12.06)/.07)**2))
        rgb += glint[:,:,None]*[40,74,68]
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,dtype='uint8')]))


def compile_model(d):
    atlas = Image.new('RGBA',(EDGE,EDGE),(0,0,0,0)); tiles = []
    faces = helper()['FACES']
    for spec in d['parts']:
        pts = vertices(spec['geometry'])
        for face,ix in faces.items():
            p = pts[list(ix)]
            w = max(5,min(256,math.ceil(np.linalg.norm(p[1]-p[0])*23)))
            h = max(5,min(256,math.ceil(np.linalg.norm(p[3]-p[0])*23)))
            tiles.append((spec,face,w,h))
    tiles.sort(key=lambda t:(-t[3],-t[2],t[0]['geometry']['name'],t[1]))
    uvmap = {}; islands = []; x=y=2; row=0
    for spec,face,w,h in tiles:
        if x+w+2>EDGE:
            x=2; y+=row+4; row=0
        assert y+h+2<=EDGE, 'UV atlas overflow'
        a = np.array(tile(spec,face,w,h))
        atlas.paste(Image.fromarray(np.pad(a,((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        name=spec['geometry']['name']; rect=[x,y,x+w,y+h]
        uvmap[name,face]=[v*16/EDGE for v in rect]
        islands.append(dict(element=name,face=face,rect=rect))
        x+=w+4; row=max(row,h)
    es=[]
    for spec in d['parts']:
        e=copy.deepcopy(spec['geometry'])
        e['faces']={f:dict(uv=uvmap[e['name'],f],texture='#0') for f in faces}
        es.append(e)
    d['atlas'].update(islands=islands,used_height=y+row+2)
    return atlas,dict(credit='Distant Relation W132 | authored solid volumes and default-dye face UV | offline candidate',
        textures={'0':'destiny:item/weapon/w123/distant_relation','particle':'destiny:item/weapon/w123/distant_relation'},
        elements=es,display=json.loads((ROOT/BASE).read_bytes())['display'])


def inspection(d,atlas,model):
    es=[]; groups={}
    for spec,e in zip(d['parts'],model['elements']):
        b=copy.deepcopy(e); r=b.pop('rotation',{})
        b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,
                 origin=r.get('origin',[8,8,8]),rotation=[r.get(a,0) for a in 'xyz'])
        for f in b['faces'].values():
            f['texture']=0; f['uv']=[v*EDGE/16 for v in f['uv']]
        es.append(b); groups.setdefault(spec['group'],[]).append(b['uuid'])
    return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),
        name='Distant Relation W132 - full solids / offline inspection',
        resolution=dict(width=EDGE,height=EDGE),elements=es,
        outliner=[dict(name=n,uuid=uid(n),origin=[8,8,8],rotation=[0,0,0],children=cs,export=True) for n,cs in groups.items()],
        textures=[dict(name='distant_relation.png',id='0',uuid=uid('texture'),width=EDGE,height=EDGE,
            uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=model['display'],destiny_w132=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],
            sourceScale=d['source']['scale'],muzzleAxis='-Z',representation='full only'))


def comparison(d,atlas,model):
    """Actual photo and explicitly labelled canonical (not original FBX) render."""
    w,h=1100,310
    sheet=Image.new('RGB',(2200,1740),'#151e26'); draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=22):
        draw.text((x,y),s,fill='#e2e8eb',font_size=size)
    label(24,14,'DISTANT RELATION / W132 / solid remodel / OFFLINE ART REVIEW',30)
    photo=Image.open(PHOTO).convert('RGB').crop((300,180,1910,770))
    photo.thumbnail((1500,390)); sheet.paste(photo,(24,58))
    label(1580,95,'Actual default-dye photo',25)
    label(1580,138,'Bungie item 2034817450',21)
    label(1580,183,'Teal steel / brown wood',21)
    label(1580,219,'Silver brake + bolt',21)
    label(1580,267,f'{len(model["elements"])} opaque solid cubes',23)
    label(1580,307,'Full only / 1024 face atlas',21)
    label(1580,351,'Native integration pending',21)
    old=json.loads((ROOT/BASE).read_bytes())
    oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/distant_relation.png'))
    oldtris=helper()['model_triangles']({'full':old},oldtex)
    newtris=helper()['model_triangles']({'full':model},atlas)
    pts=np.concatenate([vertices(e) for e in old['elements']]+[vertices(e) for e in model['elements']])
    label(24,460,'LOCAL CANONICAL / 244 cuboids / existing W30 texture',22)
    label(1124,460,f'NEW / {len(model["elements"])} authored cubes / default-dye palette',22)
    for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('FRONT OBLIQUE / depth',[1,.48,-.62]),
                                    ('REAR OBLIQUE / depth',[-1,.38,.66])]):
        extent=helper()['frame'](pts,cam,w,h)
        for col,tris in enumerate((oldtris,newtris)):
            im,_=helper()['render'](tris,cam,extent,(w,h))
            sheet.paste(im,(col*w,495+row*h)); label(col*w+18,503+row*h,name,17)
    # Close views provide readable aperture/depth evidence at practical scale.
    for col,(group,cam,title) in enumerate([
        ('stock',[1,.25,-.40],'Wood thumbhole / filled stock'),
        ('hand_loop',[1,.25,-.40],'Open lower hand loop'),
        ('optic',[.35,.15,-1],'Recessed optic'),
        ('muzzle',[.32,.15,-1],'Open muzzle brake')]):
        names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        subset=[e for e in model['elements'] if e['name'] in names]
        p=np.concatenate([vertices(e) for e in subset])
        im,_=helper()['render'](helper()['model_triangles']({'detail':dict(elements=subset)},atlas),
            cam,helper()['frame'](p,cam,550,250),(550,250))
        sheet.paste(im,(col*550,1440)); label(col*550+12,1449,title,17)
    label(24,1708,'Canonical comparison is not a raw FBX render. No native claims. First/third person, ADS, generic reload and 10-20 displays: master pending.',18)
    return png(sheet)


def review(d,model):
    count=len(model['elements'])
    return f'''# Distant Relation W132 — offline art review

Actual default photo: `{PHOTO}`; W31 references.json Bungie item 2034817450, screenshot SHA-256 verified. Opened this photo and DRFrame_Diffuse.png with view_image. The raw diffuse is neutral/undyed and is not the finished default palette. Parsed original read-only Distant Relation FBX (29,579 selected triangles), six W30 source objects, measured W30 bounds and source coordinate basis. Excluded W30 object remains excluded. No component, voxel or polygon transplantation.

The full candidate has **{count} opaque solid cuboids**, zero triangle adapters, zero alpha cards, and no split resources. Large continuous receiver/shroud/wood panels replace the old projected 244-cuboid canonical. The wood stock remains filled above and below its real large thumbhole. The dark lower hand loop, separate trigger guard, silver bored muzzle, front sight between two ears and separate optic with recessed front/rear glass are structural geometry. The shroud is a filled volume; the restrained pill vent pockets are opaque face paint. Every face has independent authored UVs with a 2px extruded gutter on a 1024² atlas. Walnut grain is aligned in weapon space; fine fore-end ribs, ports, fasteners, action seams and magazine flutes are face detail. No speculative lettering, decorative bolts or random grunge was added.

Default-dye observations: desaturated dark teal steel on the long shroud, barrel and scope; long brown wood fore-end, comb and lower stock; silver muzzle brake, bolt and optic rear rim; dark under-hand loop. Curved stock transitions and metallic response are simplified. This static palette does not claim original PBR restoration.

Frame preserved: source scale {d['source']['scale']}, anchor {d['source']['anchor']}, muzzle -Z at Z=-8.263094 and barrel Y=10.357. Existing full native display dictionary is copied exactly, with no new top-level model scale or repositioning. Grip remains around [8,8.55,8.30] in the canonical hand-contact region. Existing ADS, generic reload, timing/audio and registry files are unchanged. Inspection project embeds all editable solid cubes, per-face UVs and final texture, grouped by semantic region; it is full-only and creates no animations.

comparison.png includes the actual default photo, clearly labelled W30 local canonical with its existing W30 texture, new side, matched-camera front/rear obliques, and close stock/loop/optic/muzzle views. Canonical is not claimed to be the raw textured FBX or the undyed diffuse. Native rotation/parser, pack registration/texture load, first/third-person contact, ADS, generic reload and fire timing/audio, and representative 10–20 displays remain master-owned pending scenarios. No Gradle, server, GUI, DCC, leases or native performance tests were run.
'''


def generate(include_comparison=True):
    meta,ref=source(); d=design(meta,ref); atlas,model=compile_model(d)
    pts=np.concatenate([vertices(e) for e in model['elements']]); count=len(model['elements'])
    groups={}
    for spec in d['parts']:
        groups[spec['group']]=groups.get(spec['group'],0)+1
    outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),
             ART+'inspection.bbmodel':encode(inspection(d,atlas,model)),ART+'review.md':review(d,model).encode()}
    if include_comparison:
        outputs[ART+'comparison.png']=comparison(d,atlas,model)
    manifest=dict(id='distant_relation',revision='W132',family='scout_rifle',counts=dict(full=count),
        assembled_elements=count,opaque_cuboids=count,triangle_adapter_elements=0,alpha_elements=0,
        max_assembled_elements=1000,emitted_faces=count*6,groups=groups,texture_size=[EDGE,EDGE],
        actual_bounds=[pts.min(0).round(7).tolist(),pts.max(0).round(7).tolist()],
        source_bounds=meta['model_bounds'],source_anchor=meta['anchor'],source_scale=meta['scale'],
        source_triangles=meta['source_triangles'],canonical_display_exact=True,
        representation='full only',native_accepted=False,input_sha256=d['input_sha256'],
        raw_input_sha256=d['raw_input_sha256'],generator_sha256=sha(Path(__file__).read_bytes()),
        output_sha256={p:sha(b) for p,b in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--verify',action='store_true')
    args=parser.parse_args(); outputs=generate()
    batch=json.loads((ROOT/BATCH).read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w132-distant_relation'))
    assert set(outputs)<=owned
    for rel,data in outputs.items():
        p=ROOT/rel
        if args.verify:
            assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+rel
        else:
            p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} owned artifacts; full={m["counts"]["full"]}; faces={m["emitted_faces"]}; native pending')


if __name__=='__main__':
    main()
