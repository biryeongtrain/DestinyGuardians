#!/usr/bin/env python3
"""W251 해머헤드 형상·UV. 원본 semantic 설계부터 매번 재생성.
게임·DCC·빌드 없이 소유 경로만 출력. 용광로가 순수 authoring 함수를 재사용.
"""
import sys
sys.dont_write_bytecode=True
import argparse, base64, copy, hashlib, io, json, math, uuid
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import generate_surface_w123_hammerhead as legacy
ROOT=Path(__file__).resolve().parents[1]
EDGE=1024
FACES=legacy.FACES
NORMALS=legacy.NORMALS
PYTHON='/Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
    b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def normalize_rotation(e):
    """Legacy axis/angle -> XYZ on inspection copy, never alter saved display."""
    e=copy.deepcopy(e)
    if 'rotation' in e:
        r=e['rotation'];axis=r.pop('axis',None);angle=r.pop('angle',0)
        if axis:assert axis in 'xyz';r[axis]=angle
        for a in 'xyz':r.setdefault(a,0)
    return e

def vertices(e):
    e=normalize_rotation(e)
    v=np.array([[e['to' if mask>>a&1 else 'from'][a] for a in range(3)] for mask in range(8)],float)
    if 'rotation' in e:
        r=e['rotation'];o=np.array(r['origin']);v-=o
        if r.get('rescale'):
            axes=[a for a in 'xyz' if r[a]];assert len(axes)==1
            v[:,[i for i,a in enumerate('xyz') if a!=axes[0]]]*=1/math.cos(math.radians(r[axes[0]]))
        v=v@legacy.rotation(r).T+o
    return v

def triangles(models,atlas):
    out=[];tex=np.asarray(atlas.convert('RGBA'))
    for m in models.values():
        for e0 in m['elements']:
            e=normalize_rotation(e0);vs=vertices(e);R=legacy.rotation(e.get('rotation',{}))
            for f,uvf in e['faces'].items():
                p=vs[list(FACES[f])];a,b,c,d=uvf['uv'];uv=np.array([[a,b],[c,b],[c,d],[a,d]])/16;n=R@NORMALS[f]
                for ix in ((0,1,2),(0,2,3)):out.append((p[list(ix)],uv[list(ix)],tex,n))
    return out

def euler(M):
    return tuple(math.degrees(a) for a in (math.atan2(M[2,1],M[2,2]),math.asin(np.clip(-M[2,0],-1,1)),math.atan2(M[1,0],M[0,0])))

class Author:
    def __init__(self,d):self.d=d
    def remove(self,*names):
        for p,ss in self.d['parts'].items():self.d['parts'][p]=[s for s in ss if s['geometry']['name'] not in names]
    def box(self,name,c,size,mat,group,motif='panel',turn=(0,0,0),part='body'):
        c=np.array(c,float);size=np.array(size,float)
        self.d['parts'][part].append(dict(material=mat,group=group,motif=motif,geometry=dict(name=name,
            **{'from':(c-size/2).round(7).tolist(),'to':(c+size/2).round(7).tolist()},
            rotation=dict(origin=c.round(7).tolist(),**dict(zip('xyz',turn))))))
    def section(self,name,c,size,cut,mat,group,motif='panel',part='body',pitch=0):
        """Solid octagon union with broad side faces and four real shoulders.
        Continuous world UV hides coplanar subdivision; no hollow alpha skin.
        """
        w,h,l=size;assert 0<cut<min(w,h)/2;R=legacy.rotation({'x':pitch})
        def add(suffix,offset,sz,roll=0):self.box(name+suffix,np.array(c)+R@offset,sz,mat,group,motif,euler(R@legacy.rotation({'z':roll})),part)
        add('_vertical',[0,0,0],[w-2*cut,h,l]);add('_side',[0,0,0],[w,h-2*cut,l])
        for sx in (-1,1):
            for sy in (-1,1):add(f'_shoulder_{sx}_{sy}',[sx*(w/2-cut),sy*(h/2-cut),0],[cut*math.sqrt(2),cut*math.sqrt(2),l],45)
    def round_grip(self,name,c,size,cut,mat,group,pitch,part='body'):
        # Rounded XZ section, original hand contact and pitch are preserved.
        R=legacy.rotation({'x':pitch});c=np.array(c);w,h,z=size
        self.box(name+'_contact',c,[w-2*cut,h,z],mat,group,'grip',(pitch,0,0),part)
        self.box(name+'_side',c,[w,h,z-2*cut],mat,group,'grip',(pitch,0,0),part)
        for sx in (-1,1):
            for sz in (-1,1):
                cc=c+R@np.array([sx*(w/2-cut),0,sz*(z/2-cut)])
                self.box(f'{name}_round_{sx}_{sz}',cc,[cut*math.sqrt(2),h,cut*math.sqrt(2)],mat,group,'grip',euler(R@legacy.rotation({'y':45})),part)

def hammer_design(meta):
    d=legacy.make_design(meta);a=Author(d)
    a.remove('shroud_roof','shroud_roof_bevel_-1','shroud_roof_bevel_1','shroud_front_ramp_-1','shroud_front_ramp_1',
        'receiver_main','receiver_rear','receiver_front_bulkhead','receiver_side_rib_-1','receiver_side_rib_1',
        'stock_upper_beam','stock_cheek','stock_butt','stock_butt_toe','pistol_grip','grip_heel','carry_bottom',
        'cover_shell','cover_bevel_-1','cover_bevel_1','cover_skirt_-1','cover_skirt_1')
    a.section('W251_shroud',[8,12.82,-4.40],[1.72,.60,11.60],.19,'graphite','shroud','shroud')
    a.section('W251_nose_ramp',[8,12.57,-10.62],[1.38,.37,1.72],.13,'graphite','shroud','shroud',pitch=-12)
    a.section('W251_receiver',[8,10.91,5.645],[1.84,1.78,6.03],.25,'black','receiver','receiver')
    a.section('W251_rear_receiver',[8,10.92,10.67],[1.40,1.52,4.08],.22,'black','receiver','receiver')
    a.section('W251_feed_bulkhead',[8,11.24,2.04],[1.68,2.74,1.57],.25,'graphite','receiver','bulkhead')
    for side in (-1,1):
        a.box(f'W251_receiver_taper_{side}',[8+side*.72,11.03,8.61],[.32,1.23,1.12],'graphite','receiver','receiver',(0,side*12,0))
        a.box(f'W251_belt_port_cheek_{side}',[8+side*.80,11.66,3.20],[.20,.69,.82],'black','receiver','feed',(13,0,0))
    a.section('W251_stock_beam',[8,11.975,10.815],[.98,.53,7.21],.16,'graphite','stock','stock')
    a.section('W251_cheek_contact',[8,12.43,11.74],[.92,.43,3.70],.14,'graphite','stock','stock')
    a.section('W251_cheek_front_rise',[8,12.31,9.62],[.92,.37,.72],.12,'graphite','stock','stock',pitch=-14)
    a.section('W251_cheek_rear_fall',[8,12.36,13.78],[.87,.35,.75],.10,'graphite','stock','stock',pitch=16)
    a.round_grip('W251_butt_middle',[8,10.60,14.71],[.98,3.48,.70],.15,'rubber','stock',0)
    a.round_grip('W251_butt_heel',[8,12.48,14.67],[.94,.64,.66],.14,'rubber','stock',-14)
    a.round_grip('W251_butt_toe',[8,8.61,14.61],[.93,.56,.67],.13,'rubber','stock',14)
    a.round_grip('W251_pistol_grip',[8,8.49,7.98],[.66,2.35,.85],.16,'rubber','grip',-18)
    a.round_grip('W251_grip_heel',[8,7.43,8.34],[.74,.28,.96],.12,'black','grip',-18)
    a.section('W251_carry_contact',[8,8.035,-.63],[.78,.43,4.96],.15,'black','carry','grip')
    a.section('W251_cover_crown',[8,12.84,4.765],[1.64,.56,6.33],.19,'graphite','cover','cover','cover')
    for side in (-1,1):
        a.box(f'W251_cover_sloping_skirt_{side}',[8+side*.67,12.30,5.96],[.25,.80,3.85],'black','cover','cover',(0,0,side*12),'cover')
        a.box(f'W251_cover_rear_ramp_{side}',[8+side*.49,12.72,7.82],[.55,.28,.75],'graphite','cover','cover',(14,0,0),'cover')
    d['palette']={'graphite':[66,72,79],'black':[38,43,49],'steel':[132,139,145],
        'red':[163,29,26],'red_edge':[196,43,32],'rubber':[27,30,33],'belt':[133,140,144],'recess':[17,21,26]}
    d['improvements']=[
        '긴 외장과 receiver의 넓은 면을 유지하고 실제 사선 단면·뒤쪽 테이퍼·급탄구 단차를 추가했다.',
        '볼받침 앞뒤를 경사로 연결하고 개머리판 접촉부와 그립을 둥근 단면으로 재설계했다.',
        '덮개 경사 치마는 원래 hinge 부품에 남기고 원래 시야 구멍·탄띠·탄창 접촉 좌표를 보존했다.',
        '사진과 diffuse의 긴 패널·외장 각인·검붉은 레일·드럼 동심 홈을 연속 UV에 다시 그렸다.']
    return d

def paint(spec,face,w,h,d,key):
    """Albedo and authored shallow cuts; no light compensation/random dirt.
    World-projected markings remain continuous across coplanar solid unions.
    """
    role=spec['material'];base=np.array(d['palette'][role],float)
    yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h;p=vertices(spec['geometry'])[list(FACES[face])]
    pos=p[0]+u[:,:,None]*(p[1]-p[0])+v[:,:,None]*(p[3]-p[0]);x,y,z=pos[:,:,0],pos[:,:,1],pos[:,:,2]
    col=np.broadcast_to(base,(h,w,3)).copy()
    side=abs((legacy.rotation(normalize_rotation(spec['geometry']).get('rotation',{}))@NORMALS[face])[0])>.65
    motif=spec['motif'];group=spec['group'];name=spec['geometry']['name']
    def setc(mask,c):col[mask]=c
    def path(points,color,thick=.025):
        distance=np.full((h,w),np.inf)
        for (za,ya),(zb,yb) in zip(points,points[1:]):
            dz=zb-za;dy=yb-ya;t=np.clip(((z-za)*dz+(y-ya)*dy)/max(dz*dz+dy*dy,1e-10),0,1)
            distance=np.minimum(distance,np.hypot(z-(za+t*dz),y-(ya+t*dy)))
        pixel=max(np.linalg.norm(p[1]-p[0])/w,np.linalg.norm(p[3]-p[0])/h)
        coverage=np.clip((thick/2-distance)/pixel+.5,0,1)[:,:,None]
        col[:]=col*(1-coverage)+np.array(color)*coverage
    dark=[19,24,29];lip=[98,105,112];mid=[51,57,64]
    # Deliberate, source-derived long panel borders; no per-island box outline.
    if key=='hammerhead':
        if side and group=='shroud':
            path([(-10.0,12.94),(-6.8,12.94),(-6.6,13.03),(-3.45,13.03),(-3.30,12.94),(.98,12.94)],[116,122,129],.032)
            path([(-3.2,12.45),(-2.45,12.45),(-2.18,12.30),(-.45,12.30),(-.20,12.47),(1.15,12.47),(1.15,12.94)],dark,.042)
            path([(-9.9,12.72),(-6.1,12.72),(-5.9,12.61),(-3.4,12.61),(-3.3,12.42),(.9,12.42)],dark,.032)
            path([(-9.9,12.76),(-6.1,12.76)],lip,.024)
            for zz in (-3.0,-2.2,-1.4,-.6):path([(zz-.10,12.82),(zz+.06,12.77),(zz+.13,12.88),(zz-.10,12.94),(zz-.10,12.82)],dark,.025)
        if side and group=='receiver':
            path([(3.05,11.34),(3.50,11.34),(3.60,11.49),(6.45,11.49),(6.7,11.27),(7.85,11.27),(8.2,10.99),(8.2,10.36),(3.05,10.36),(3.05,11.34)],dark,.048)
            path([(3.60,11.54),(6.45,11.54)],[87,94,101],.028)
            path([(9.0,11.28),(10.55,11.28),(10.85,11.47),(12.15,11.47),(12.15,10.48),(9.0,10.48),(9.0,11.28)],dark,.045)
            path([(9.05,11.33),(10.55,11.33)],[79,87,95],.027)
            path([(3.1,10.30),(7.6,10.30),(7.9,10.58),(11.8,10.58)],dark,.04)
            path([(3.1,10.35),(7.6,10.35)],mid,.028);path([(4.0,11.10),(4.0,11.35),(6.6,11.35)],dark,.035)
        if side and group=='cover':
            path([(2.25,12.95),(4.0,12.95),(4.20,12.80),(6.8,12.80),(7.25,12.95)],[106,113,120],.032)
            path([(2.1,12.82),(3.0,12.82),(3.2,12.66),(6.1,12.66),(6.4,12.78),(7.4,12.78)],dark,.03)
            path([(2.1,12.86),(3.0,12.86)],lip,.024)
        if side and motif=='inset':
            path([(-9.30,11.67),(-3.60,11.67),(-3.35,11.87),(-3.35,12.16),(-9.30,12.16),(-9.30,11.67)],[119,125,130],.032)
            path([(-9.15,11.73),(-3.67,11.73)],dark,.048)
        if side and motif=='vents':
            for yy0 in (11.69,11.86,12.03):
                setc((z> -2.95)&(z< -1.84)&(abs(y-yy0)<.035),dark)
                setc((z> -2.95)&(z< -1.84)&(abs(y-yy0+.046)<.015),[72,79,85])
        if side and group=='stock':
            path([(9.85,12.35),(12.85,12.35),(13.10,12.48)],dark,.028);path([(9.9,12.55),(12.9,12.55)],lip,.022)
        if motif=='drum' and face in ('north','south'):
            cx=6.02 if 'drum_0' in name else 9.98;r=np.hypot(x-cx,y-8.415)
            setc(np.ones((h,w),bool),[31,35,40]);setc((r>1.06)&(r<1.095),[67,74,80]);setc((r>.93)&(r<.98),[20,24,29]);setc((r>.28)&(r<.32),[58,64,70])
        if motif=='drum' and face not in ('north','south'):setc((abs(z-3.15)<.025)|(abs(z-4.58)<.025),dark)
        if motif in ('rail','gas','latch') and side:path([(-8.9,10.48),(-6.4,10.48),(-6.25,10.57),(-2.1,10.57),(-1.9,10.48),(1.8,10.48)],[105,19,20],.03)
        if motif=='cartridge':setc((abs(z-4.40)<.035),[60,67,73]);setc((abs(z-3.58)<.025),[158,164,167])
    else:
        if side and group in ('receiver','foreend'):
            path([(-5.65,13.50),(-3.0,13.50),(-2.65,13.60),(1.8,13.60)],[114,121,127],.028)
            path([(-2.25,12.43),(-1.4,12.43),(-1.2,12.55),(1.92,12.55),(2.30,12.27),(2.30,11.76),(-2.25,11.76),(-2.25,12.43)],dark,.043)
            path([(-1.15,12.59),(1.85,12.59)],[86,94,102],.028)
            path([(3.20,11.40),(6.5,11.40),(6.72,11.55),(9.25,11.55)],dark,.045)
            path([(-5.7,12.15),(-4.1,12.15),(-4.1,11.98),(-2.9,11.98),(-2.55,12.15),(1.95,12.15),(2.2,12.00),(6.7,12.00),(6.85,11.45),(9.4,11.45)],dark,.035)
            path([(-5.6,13.45),(1.7,13.45),(2.3,13.34)],lip,.024)
            path([(3.2,13.22),(5.3,13.22),(5.7,12.98),(6.4,12.98)],dark,.035);path([(3.2,13.26),(5.3,13.26)],lip,.025)
        if side and motif=='armory_vents':
            for zz in (.1,.55,1.,1.45):
                for yy0 in (11.94,12.17):path([(zz-.07,yy0-.06),(zz+.07,yy0-.06),(zz+.09,yy0+.06),(zz-.04,yy0+.06),(zz-.07,yy0-.06)],dark,.028)
            for zz in np.arange(-.6,1.8,.20):path([(zz,11.66),(zz,11.81)],lip,.014)
            path([(-.6,11.73),(1.8,11.73)],dark,.02)
        if side and motif=='nose':
            for yy0 in (12.08,12.18,12.28):path([(-5.65,yy0),(-4.10,yy0)],dark,.034)
        if side and group=='breech':
            setc((z>7.18)&(z<7.70)&(abs(y-13.15)<.17),dark);setc((z>8.05)&(z<8.65)&(abs(y-12.77)<.15),[91,20,23])
        if side and motif=='well':
            path([(10.65,10.12),(10.65,10.84),(11.7,10.84),(11.85,10.69),(13.12,10.69),(13.12,10.12)],[35,40,33],.04)
            path([(10.68,10.88),(11.7,10.88)],[106,111,92],.025)
            path([(11.1,10.15),(11.1,10.75),(11.3,10.88),(11.5,10.75),(11.5,10.15)],[116,117,96],.027);setc((z-12.8)**2+(y-10.6)**2<.13**2,dark)
        if side and group=='stock' and role!='rubber':path([(12.3,12.36),(15.5,12.36)],lip,.024)
        if side and motif=='magazine':
            for zz in (11.08,11.76,12.42):
                path([(zz,6.95),(zz+.34,9.57)],dark,.04);path([(zz+.055,6.95),(zz+.395,9.57)],[101,104,85],.022)
            path([(10.7,7.52),(11.65,8.0),(12.74,9.03)],dark,.04)
    if motif in ('grip','foregrip','pad','butt') and role=='rubber':
        if motif=='foregrip':setc(np.mod(z+.2,.18)<.022,[18,22,25])
        else:setc((np.mod(y,.21)<.024)&side,[17,21,24])
    if side and motif in ('rail','redline') and role in ('red','red_edge'):setc(np.mod(z+.5,2.6)<.025,[98,19,20])
    return Image.fromarray(np.dstack((np.clip(col,0,255).astype('uint8'),np.full((h,w),255,dtype='uint8'))))

def compile_models(d,key,display):
    for density in (22,20,18,16):
        requests=[]
        for part,ss in d['parts'].items():
            for spec in ss:
                vs=vertices(spec['geometry'])
                for f,ix in FACES.items():
                    p=vs[list(ix)];w=max(5,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(5,math.ceil(np.linalg.norm(p[3]-p[0])*density));requests.append((part,spec,f,w,h))
        requests.sort(key=lambda t:(-t[4],-t[3],t[1]['geometry']['name'],t[2]));x=y=2;rh=0;placed=[]
        for part,spec,f,w,h in requests:
            if x+w+2>EDGE:x=2;y+=rh+4;rh=0
            if y+h+2>EDGE:break
            placed.append((part,spec,f,w,h,x,y));x+=w+4;rh=max(rh,h)
        if len(placed)==len(requests):break
    else:raise ValueError('1024 atlas capacity exceeded')
    atlas=Image.new('RGBA',(EDGE,EDGE));uvs={};ledger=[]
    for part,spec,f,w,h,x,y in placed:
        tile=paint(spec,f,w,h,d,key);atlas.paste(Image.fromarray(np.pad(np.asarray(tile),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        name=spec['geometry']['name'];uvs[name,f]=[q*16/EDGE for q in (x,y,x+w,y+h)];ledger.append(dict(element=name,face=f,rect=[x,y,x+w,y+h]))
    models={}
    for part,ss in d['parts'].items():
        es=[]
        for spec in ss:
            e=copy.deepcopy(spec['geometry']);e['faces']={f:dict(uv=uvs[e['name'],f],texture='#0') for f in FACES};es.append(e)
        tex='destiny:item/weapon/w123/'+key;models[part]=dict(credit='W251 '+key+' 형상·연속 면 UV',textures={'0':tex,'particle':tex},elements=es)
    full=copy.deepcopy(models['body']);full['elements']=sum([copy.deepcopy(m['elements']) for m in models.values()],[]);full['display']=copy.deepcopy(display);models['full']=full
    d['atlas']=dict(size=EDGE,gutter=2,density=density,islands=ledger,used_height=y+rh+2)
    return atlas,models

def inspection(d,models,atlas,key):
    elements=[];groups=[]
    def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w251:'+key+':'+s))
    for part in d['parts']:
        children=[]
        for e0 in models[part]['elements']:
            e=normalize_rotation(e0);r=e.pop('rotation',{});e.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,origin=r.get('origin',[8,8,8]),rotation=[r.get(a,0) for a in 'xyz'])
            for f in e['faces'].values():f['texture']=0;f['uv']=[q*EDGE/16 for q in f['uv']]
            elements.append(e);children.append(e['uuid'])
        groups.append(dict(name=part,uuid=uid(part),origin=legacy.HINGE if part=='cover' else [8,8,8],rotation=[0,0,0],export=True,children=children))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='W251 '+key+' | 오프라인 미술 검수',resolution={'width':EDGE,'height':EDGE},elements=elements,outliner=groups,
        textures=[dict(name=key+'.png',id='0',uuid=uid('texture'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=models['full']['display'],destiny_w251=dict(nativeAccepted=False,rotationOrder='RzRyRx',sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale']))

def font(size):return ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc',size)
def comparison(d,meshes,rawtris,before,oldatlas,models,atlas,key,photo):
    w,h=800,330;sheet=Image.new('RGB',(2400,2180),'#17202a');dr=ImageDraw.Draw(sheet)
    def label(x,y,s,size=23):dr.text((x,y),s,fill='#e4ebf2',font=font(size))
    title='해머헤드' if key=='hammerhead' else '용광로'
    label(20,12,f'W251 {title} | 기본 안료 사진 / 원본 rip / 기존 생성 / 형상·UV 보강',32)
    crop=(410,170,1880,790) if key=='hammerhead' else (840,195,1920,710)
    im=Image.open(photo).convert('RGB').crop(crop);im.thumbnail((1170,340));sheet.paste(im,(15,58))
    for y,s in [(75,'원본 기본 안료 사진: 색·재질 기준'),(120,'아래 세 열: 같은 카메라·프레임·고정 방향광'),(162,'legacy axis/angle → XYZ 정규화 후 CPU 렌더'),(204,'원본 diffuse/참고색은 원작 PBR/기본 안료 복원이 아님'),(246,f'실제 출력: {len(models["full"]["elements"])} 큐브 / 1024 RGBA'),(288,'native 조명·1/3인칭·ADS·장전 검수는 master 대기')]:label(1220,y,s,24)
    for x,s in [(20,'원본 FBX / diffuse 또는 부위별 참고색'),(820,'이전: W123 원본 semantic 생성기 재생성'),(1620,'이후: W251 새 형상 + 면 UV')]:label(x,411,s)
    arrays=[rawtris,triangles({'full':before['full']},oldatlas),triangles({'full':models['full']},atlas)]
    points=np.concatenate([np.concatenate([vertices(e) for e in m['full']['elements']]) for m in (before,models)]+[np.concatenate([m['vertices'] for m in meshes])])
    for row,(text,cam) in enumerate([('측면',[1,0,0]),('앞 사선',[1,.48,-.63]),('뒤 사선',[-1,.39,.62])]):
        ext=legacy.frame(points,cam,w,h)
        for col,ts in enumerate(arrays):
            im,_=legacy.render(ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,449+row*h));label(col*w+12,455+row*h,text,20)
    close=[('receiver·볼받침 입체 단차',{'receiver','stock','cover'},[1,.36,.65]),('포구·앞 외장 단면',{'muzzle','shroud','foreend'},[.5,.25,-1])]
    for i,(text,groups,cam) in enumerate(close):
        ss=[s for vv in d['parts'].values() for s in vv if s['group'] in groups]
        if i==1:ss=[s for s in ss if min(s['geometry']['from'][2],s['geometry']['to'][2])<(-8 if key=='hammerhead' else -3)]
        ps=np.concatenate([vertices(s['geometry']) for s in ss]);ext=legacy.frame(ps,cam,w,h)
        for col,ts in enumerate(arrays):
            im,_=legacy.render(ts,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,1439+i*h));label(col*w+12,1446+i*h,text,20)
    label(20,2120,'W251 오프라인 미술 비교. CPU 그림은 native 합격 근거가 아니다. 동적 PBR·성능은 검증하지 않았다.',24)
    return png(sheet)

def validate(d,models,atlas,display,key):
    parts=list(d['parts']);full=models['full'];es=full['elements'];counts={p:len(models[p]['elements']) for p in (*parts,'full')}
    assert len(es)<=1000 and es==sum([models[p]['elements'] for p in parts],[])
    assert full['display']==display and all('display' not in models[p] for p in parts)
    assert len({e['name'] for e in es})==len(es);tex=np.asarray(atlas);assert atlas.size==(1024,1024)
    for e in es:
        assert np.isfinite(vertices(e)).all() and np.all(np.array(e['to'])>e['from']);assert set(e['faces'])==set(FACES)
        for f in e['faces'].values():
            assert f['texture']=='#0';a,b,c,dd=f['uv'];assert 0<=a<c<=16 and 0<=b<dd<=16
            x,y,x1,y1=[round(q*EDGE/16) for q in (a,b,c,dd)];assert np.all(tex[y:y1,x:x1,3]==255)
    # A handful of designed mechanical gaps; no exhaustive scene sweep.
    probes=d.get('required_air_probes',{}) if key=='blast_furnace' else {'trigger_guard':[8,9.9,6.0],'stock_window':[8,10,13.5],'optic_aperture':[8,14.1,3.37],'muzzle_entry':[8,11.94,-11.7]}
    for name,point in probes.items():
        for e0 in es:
            e=normalize_rotation(e0);r=e.get('rotation',{});o=np.array(r.get('origin',[8,8,8]));v=(np.array(point)-o)@legacy.rotation(r)+o
            assert not (np.all(v>np.array(e['from'])+1e-5) and np.all(v<np.array(e['to'])-1e-5)), '막힌 구멍: '+name
    probe={'from':[1,2,3],'to':[3,5,7],'rotation':{'axis':'x','angle':22.5,'origin':[8,8,8]}}
    expected=copy.deepcopy(probe);expected['rotation']={'x':22.5,'y':0,'z':0,'origin':[8,8,8]}
    assert np.array_equal(vertices(probe),vertices(expected))
    return counts

def generate(key,original,make_design):
    meshes,meta=original.source_meshes()
    if key=='hammerhead':before_d=original.make_design(meta);oldatlas,before=original.compile_models(before_d);d=make_design(meta)
    else:before_d=original.make_design(meshes,meta);oldatlas,before=original.compile_models(before_d,meshes);d=make_design(meshes,meta)
    d.update(stage='W251',revision='W251-semantic-r1',generator='scripts/refine_weapon_w251_'+key+'.py',method='원본 semantic 설계에서 재생성한 입체 단면과 연속 면 UV; voxel·rip 자동변환 없음')
    d.pop('groups',None);d.pop('canonical_reload_delta',None)
    d['limitations']=['오프라인 CPU 미술 검수이며 native 합격·성능 검증이 아니다.','단일 기본 안료 사진과 원본 diffuse로 보수적으로 재구성한 색·홈이며 원작 PBR 복원은 아니다.','손·장전·ADS·타이밍은 변경하지 않았다.']
    d['uv_policy']='1024 RGBA 고정, 넓은 면 연속 UV, 2px gutter. world 좌표의 패널·홈은 겹치는 solid 분해 면에서도 연속. 임의 노이즈·full-bright 보상 없음.'
    d['before_policy']='W123 원본 semantic 생성기의 geometry·UV를 매번 재생성. W251 출력을 누적 필터링하지 않음.'
    d['legacy_rotation_policy']='비교 전 axis/angle을 XYZ로 정규화; legacy rescale도 평가. output display는 원본 그대로.'
    display=json.loads((ROOT/original.BASE).read_bytes())['display'];atlas,models=compile_models(d,key,display);counts=validate(d,models,atlas,display,key)
    art='art/weapons/w251/'+key+'/';asset='src/main/resources/assets/destiny/';model=asset+'models/weapon_surface_w123/'+key
    outputs={art+'design.json':encode(d),asset+'textures/item/weapon/w123/'+key+'.png':png(atlas),art+'inspection.bbmodel':encode(inspection(d,models,atlas,key))}
    for p,m in models.items():outputs[model+('' if p=='full' else '_'+p)+'.json']=encode(m)
    photo=original.PHOTO if key=='hammerhead' else original.W31/'references/blast_furnace.jpg'
    outputs[art+'comparison.png']=comparison(d,meshes,original.source_triangles(meshes),before,oldatlas,models,atlas,key,photo)
    paths=sorted([*outputs,art+'review.md',art+'manifest.json','scripts/refine_weapon_w251_'+key+'.py'])
    title='해머헤드' if key=='hammerhead' else '용광로';improvements='\n'.join('- '+s for s in d['improvements'])
    command=f'rtk proxy {PYTHON} -B scripts/refine_weapon_w251_{key}.py'
    review=f"""# W251 {title} 미술 검수

기본 안료 사진 `{photo}`와 로컬 FBX·diffuse를 직접 열어 확인했다.
원본 좌표·분할 provenance는 design.json의 source, input_sha256, raw_input_sha256에 기록한다.
원본 전체 비례와 긴 연속 질량을 유지하고 다음 부위를 다시 설계했다.

{improvements}

실제 출력: {', '.join(p+' '+str(n) for p,n in counts.items())}.
full은 분할 부품의 정확한 합계다. 삼각 adapter 0, alpha 윤곽판 0, 1,000 요소 상한 준수.
면 {counts['full']*6}개에 명시 UV, 1024 atlas, 2px bleed, 밀도 {d['atlas']['density']} texel/unit.
같은 평면에서 겹치는 solid 조각의 페인트는 world 좌표로 이어진다.
이전 모든 면 사각 테두리·반복 얼룩 대신 제한된 패널선·홈·재질 대비를 사용한다.
밝은 모서리·중간 금속 면·짙은 홈은 재질 정보이며 shader full-bright 보상은 없다.

원본 canonical display 사전은 exact 보존하고 부품 display는 추가하지 않았다.
[8,8,8] carrier·원본 scale·탄창 local 좌표·cover hinge를 유지했다.
손 리깅·ADS display·모션·타이밍·canonical/reload는 변경하지 않았다.
inspection.bbmodel은 별도 검사 파일이며 사용자 DCC scene을 조작하지 않았다.

comparison.png는 실제 기본 안료 사진 + 원본 rip + 이전 semantic 재생성 + W251이다.
측면·앞/뒤 사선·receiver/stock 및 포구 근접을 동일 광원·동일 카메라로 비교한다.
legacy axis/angle은 XYZ로 정규화한 후 렌더한다. 원본 diffuse/부위별 참고색은 PBR 복원이 아니다.
CPU 그림을 직접 확인했다. 이는 native parser·광원·인게임 합격 근거가 아니다.
파싱·유효 좌표·출력 수·면별 UV/opaque texel·texture 경로·assembly·display 및 --verify byte 일치를 확인한다.
중앙 Gradle·서버·Vision·CU는 실행하지 않았다.

통합 시 master는 shared surface manifest의 이 무기 replacementSha256을 새 출력으로 갱신해야 한다.
shared manifest는 소유 범위 밖이므로 수정하지 않았다. 필요한 값은 W251 manifest.json의
required_surface_manifest_updates에 있다. 기존 routing과 canonical sourceSha256은 읽기 전용으로 확인했다.

남은 master native QA:

- 공통 조명 수정 뒤 밝은/어두운 위치에서 금속 면·홈 대비 확인.
- 1/3인칭 휴대·ADS에서 외곽·시야 구멍·손 접촉 확인.
- 탄창 분리/재삽입, 해머헤드는 cover hinge·탄띠와 receiver 접합 확인.
- 10~20개 표시에서 깨짐·눈에 띄는 끊김 관측. 성능 보증 미실시.

재현 명령:

```sh
{command}
{command} --verify
```

변경 경로:

"""+'\n'.join('- `'+p+'`' for p in paths)+'\n'
    outputs[art+'review.md']=review.encode()
    inputs={p:sha((ROOT/p).read_bytes()) for p in [original.BASE,original.BB,'scripts/generate_surface_w123_'+key+'.py','scripts/refine_weapon_w251_hammerhead.py','scripts/refine_weapon_w251_'+key+'.py']};inputs.update(d.get('input_sha256',{}))
    # Only inspect shared routing. Master owns its replacement hash refresh.
    shared=json.loads((ROOT/'src/main/resources/weapon_surface_w123/manifest.json').read_bytes());updates=[]
    for row in shared['targets']:
        rel='src/main/resources/'+row['replacement']
        if rel not in outputs:continue
        source=ROOT/'src/main/resources'/row['path']
        assert sha(source.read_bytes())==row['sourceSha256'],'원본 source hash 변경: '+row['path']
        assert row['replacement']=='assets/destiny/models/weapon_surface_w123/'+row['path'].rsplit('/',1)[1]
        updates.append(dict(path=row['path'],replacement=row['replacement'],replacementSha256=sha(outputs[rel]),sourceSha256=sha(source.read_bytes())))
    assert len(updates)==len(models),'surface routing 누락'
    manifest=dict(stage='W251',id=key,counts=counts,assembled_elements=counts['full'],maximum_assembled_elements=1000,emitted_faces=counts['full']*6,alpha_body_plates=0,triangle_adapter_elements=0,
        texture_size=[EDGE,EDGE],native_accepted=False,full_is_part_union=True,canonical_display_exact=True,part_display_absent=True,anchor=meta['anchor'],scale=meta['scale'],cover_pivot=legacy.HINGE if key=='hammerhead' else None,
        baseline=dict(policy=d['before_policy'],counts={p:len(m['elements']) for p,m in before.items()},models_sha256={p:sha(encode(m)) for p,m in before.items()},texture_sha256=sha(png(oldatlas))),
        input_sha256=inputs,raw_input_sha256=d['raw_input_sha256'],owned_paths=paths,required_surface_manifest_updates=updates,
        validation={'targeted':'파싱/좌표/UV/opaque texel/요소 수/부품 합계/display/legacy rotation 확인','determinism':'--verify로 전체 출력 byte 비교','native':'master 대기; shared replacementSha256 갱신 필요','performance':'미측정'},output_sha256={p:sha(v) for p,v in sorted(outputs.items())})
    outputs[art+'manifest.json']=encode(manifest)
    return outputs,manifest

def run(key,original,make_design):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args();outputs,m=generate(key,original,make_design)
    features=json.loads(Path('/private/tmp/destiny-w251/manifest.json').read_bytes())['features'];owned=set(next(f['owned_paths'] for f in features if f['name']=='w251-art-hammerhead'))
    assert set(outputs)<=owned
    for rel,data in outputs.items():
        p=ROOT/rel
        if args.verify:assert p.read_bytes()==data,'재생성 불일치: '+rel
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    print(('검증' if args.verify else '생성')+' W251 '+key+' '+json.dumps(m['counts'])+f'; {m["emitted_faces"]} faces; '+str(len(outputs))+'개 파일')
if __name__=='__main__':run('hammerhead',legacy,hammer_design)
