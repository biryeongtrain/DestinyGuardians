#!/usr/bin/env python3
"""W251 은둔자: 원본 semantic 설계에서 형상·UV 재생성. --verify는 쓰지 않는다."""
import sys
sys.dont_write_bytecode = True
import argparse, base64, collections, copy, hashlib, importlib.util, io, json, math, uuid
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
KEY = 'the_recluse'
SCRIPT = 'scripts/refine_weapon_w251_the_recluse.py'
ART = 'art/weapons/w251/the_recluse/'
ASSET = 'src/main/resources/assets/destiny/'
MODEL = ASSET+'models/weapon_surface_w123/'
TEX = ASSET+'textures/item/weapon/w123/the_recluse.png'
BEFORE = Path('/private/tmp/destiny-w251/before')
PHOTO = Path('/tmp/destiny-weapons-w31/references/the_recluse.jpg')
EDGE = 1024

def load(path, name):
    s=importlib.util.spec_from_file_location(name,ROOT/path); m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def png(im):
    b=io.BytesIO();im.save(b,'PNG',compress_level=9);return b.getvalue()
def pin(path):return sha(Path(path).read_bytes())
def font(size):return ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc',size)

def normalize(model):
    """기존 axis/angle도 실제 Rz Ry Rx 표현으로 정규화; 원본은 수정하지 않는다."""
    m=copy.deepcopy(model)
    for e in m['elements']:
        if 'rotation' not in e:continue
        r=e['rotation'];e['rotation']={'origin':r.get('origin',[0,0,0]),
            **{a:r.get(a,r.get('angle',0) if r.get('axis')==a else 0) for a in 'xyz'}}
        assert not r.get('rescale',False),'rescale은 별도 평가 필요'
    return m

def euler(R):
    y=math.asin(float(np.clip(-R[2,0],-1,1)))
    x=math.atan2(R[2,1],R[2,2]);z=math.atan2(R[1,0],R[0,0])
    return dict(zip('xyz',np.degrees([x,y,z]).round(8).tolist()))

def rounded(spec, helper, radius, axes=(0,1)):
    """큰 기능 부품의 팔각 단면: 넓은 연속 평면 두 개와 네 대각 모서리."""
    e=spec.get('geometry',spec);lo=np.array(e['from']);hi=np.array(e['to']);c=(lo+hi)/2;s=hi-lo
    a,b=axes;long=3-a-b;R=helper.rotation(e);o=np.array(e['rotation']['origin']);out=[]
    dims=[s.copy(),s.copy()];dims[0][a]-=2*radius;dims[1][b]-=2*radius
    entries=[(c,dims[0],np.eye(3),'web'),(c,dims[1],np.eye(3),'face')]
    r={'origin':[0,0,0],**{k:45 if i==long else 0 for i,k in enumerate('xyz')}}
    L=helper.rotation({'rotation':r})
    for i in (-1,1):
        for j in (-1,1):
            cc=c.copy();cc[a]+=i*(s[a]/2-radius);cc[b]+=j*(s[b]/2-radius)
            size=s.copy();size[a]=size[b]=radius*math.sqrt(2)
            entries.append((cc,size,L,f'round-{i}-{j}'))
    for cc,size,L,label in entries:
        q=copy.deepcopy(spec);g=q.get('geometry',q);wc=(cc-o)@R.T+o
        g.update(name=e['name']+'/'+label,**{'from':(wc-size/2).round(8).tolist(),'to':(wc+size/2).round(8).tolist()},rotation={'origin':wc.round(8).tolist(),**euler(R@L)})
        out.append(q)
    return out

def inspection(key,parts,atlas,display):
    es=[];groups=[]
    for part,rows in parts.items():
        ids=[]
        for e in rows:
            b=copy.deepcopy(e);r=b.pop('rotation',{'origin':[0,0,0]});u=str(uuid.uuid5(uuid.NAMESPACE_URL,'W251/'+key+'/'+e['name']));ids.append(u)
            b.update(type='cube',uuid=u,origin=r['origin'],rotation=[r.get(a,0) for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
            es.append(b)
        groups.append(dict(name=part,origin=[8,8,8],rotation=[0,0,0],uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'W251/'+key+'/group/'+part)),children=ids))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='W251 '+key,
        resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name=key+'.png',id='0',uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'W251/'+key+'/atlas')),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=display,
        destiny_w251={'native_accepted':False,'frame_anchor':[8,8,8],'rotation_order':'RzRyRx'})

def compare(key,photo,before,btex,after,atex,helper,raw_image,focus):
    """같은 카메라/프레이밍/광원. before는 master dirty baseline의 실제 파일."""
    w,h=860,350;sheet=Image.new('RGB',(1720,1900),'#141c25');d=ImageDraw.Draw(sheet)
    d.text((20,10),'W251 / '+key+' / 형상 + UV 보강',font=font(27),fill='#f3ead7')
    ref=Image.open(photo).convert('RGB');ref=ref.crop((790,110,1870,850)) if key=='the_recluse' else ref.crop((865,260,1835,790))
    ref.thumbnail((680,285));sheet.paste(ref,(15,55))
    raw_image=raw_image.copy();raw_image.thumbnail((410,255));sheet.paste(raw_image,(690,62))
    for i,line in enumerate(['기본 안료 사진 / 실제 로컬 rip 확인','오른쪽 작은 그림: 복구 원본 FBX 또는 원본 UV','좌: 변경 전 통합본  |  우: W251','광원·카메라·배율은 좌우 동일','CPU 렌더만 수행 / native 판정 대기']):
        d.text((1120,70+i*39),line,font=font(19),fill='#cbd6e1')
    rows=[('측면',[-1,0,0],None),('앞 사선',[-1,.40,-.70],None),('뒤 사선',[1,.32,.72],None),('접촉부 / 단면 확대',[-1,.33,-.48],focus)]
    arrays=[helper.model_triangles({'full':normalize(before)},btex,{}),helper.model_triangles({'full':normalize(after)},atex,{})]
    points=np.concatenate([helper.vertices(e) for m in (normalize(before),normalize(after)) for e in m['elements']])
    for row,(label,cam,detail) in enumerate(rows):
        cam=np.array(cam,float);cam/=np.linalg.norm(cam);right=np.cross([0,1,0],cam);right/=np.linalg.norm(right);up=np.cross(cam,right)
        if detail:
            center=np.array(detail[0]);extent=(np.array([center@right,center@up]),detail[1])
        else:
            p=np.c_[points@right,points@up];lo,hi=p.min(0),p.max(0);extent=((lo+hi)/2,min((w-75)/(hi[0]-lo[0]),(h-55)/(hi[1]-lo[1])))
        for col,tris in enumerate(arrays):
            im,_=helper.render(tris,cam,extent,(w,h));sheet.paste(im,(col*w,400+row*h))
            d.text((col*w+18,406+row*h),'W251 '+('변경 전 / ' if col==0 else '보강 후 / ')+label,font=font(20),fill='#e4e9ee')
    d.text((20,1830),'긴 면의 연속 UV · 원본 파지 좌표 유지 · native 조명은 공통 셰이더에서 처리',font=font(23),fill='#b4c9db')
    return png(sheet)

def validate(models,atlas,expected_display,helper):
    full=models['full'];assert full.get('display')==expected_display
    assert atlas.size==(1024,1024);assert len(full['elements'])<=1000
    if 'body' in models:
        assert full['elements']==models['body']['elements']+models['magazine']['elements']
        assert all('display' not in models[p] for p in ('body','magazine'))
    names=[]
    for e in full['elements']:
        names.append(e['name']);assert np.all(np.array(e['to'])>e['from']);assert np.isfinite(helper.vertices(e)).all()
        assert len(e['faces'])==6
        for f in e['faces'].values():assert f['texture']=='#0' and len(f['uv'])==4 and all(0<=v<=16 for v in f['uv'])
    assert len(names)==len(set(names));return len(names)*6

def atlas_models(specs,paint,old):
    atlas=Image.new('RGBA',(EDGE,EDGE));parts={'body':[],'magazine':[]};requests=[]
    for s in specs:
        e={k:copy.deepcopy(s[k]) for k in ('name','from','to','rotation')};e['faces']={};parts[s['part']].append(e)
        points=old.vertices(s)
        for face,ids in old.CORNERS.items():
            q=points[list(ids)];density=24 if s['artwork'] and face in ('east','west') else 18
            w=max(3,math.ceil(np.linalg.norm(q[1]-q[0])*density));h=max(3,math.ceil(np.linalg.norm(q[3]-q[0])*density))
            requests.append((h,w,e['name'],face,e,s,q))
    x=y=2;row=0;islands=[]
    for h,w,name,face,e,s,q in sorted(requests,key=lambda t:(-t[0],-t[1],t[2],t[3])):
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        assert y+h+2<=EDGE,'1024 atlas overflow'
        im=paint.tile(s,face,w,h,q);atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        e['faces'][face]={'texture':'#0','uv':[v*16/EDGE for v in (x,y,x+w,y+h)]}
        islands.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    return atlas,parts,dict(resolution=EDGE,density='측면24 / 일반18',padding=2,islands=islands,used_pixels=sum((r['pixels'][2]-r['pixels'][0])*(r['pixels'][3]-r['pixels'][1]) for r in islands))

def raw_source(old):
    parser=old.load_module('scripts/generate_reload_models_w100.py','w251_raw')
    # 복구 archive를 읽기 전용 경로 adapter로 연결. 역사적 파서/캐시는 수정 안 함.
    archive=Path('/private/tmp/destiny-w251/downloads/the_recluse.rar')
    class CachePath(type(Path())):
        def __truediv__(self, other):
            return archive if str(other)=='source.archive' else super().__truediv__(other)
    return parser,parser.source_meshes(CachePath(old.CACHE)),archive

def geometry(old):
    base=old.semantic_geometry();out=[]
    for s in base:
        n=s['name'];s=copy.deepcopy(s)
        if n=='receiver/main':
            s['to'][1]=11.78;s['from'][1]=10.38
            out+=rounded(s,old,.22);continue
        if n in ('stock/pad','stock/painted-spine'):
            # 丸い butt profile rather than a vertical rectangular board.
            out+=rounded(s,old,.30 if n=='stock/pad' else .22,axes=(1,2));continue
        if n=='stock/bird-field':
            s['from'][1]=9.60;s['to'][1]=12.30
            out+=rounded(s,old,.42,axes=(1,2));continue
        if n=='stock/bird-body':
            out+=rounded(s,old,.32,axes=(1,2));continue
        if n=='stock/bird-shoulder':
            out+=rounded(s,old,.16);continue
        if n=='optic/hood-main':
            s['from'][1]=11.94;s['to'][1]=12.99
            out+=rounded(s,old,.21);continue
        if n=='receiver/rear-top':
            out+=rounded(s,old,.32,axes=(1,2));continue
        if n=='optic/crown':
            out+=rounded(s,old,.12);continue
        if n in ('foregrip/core','foregrip/backstrap','magazine/core','magazine/front-round'):
            out+=rounded(s,old,.30 if n.endswith('core') else .14,axes=(1,2));continue
        if n=='foregrip/white-beavertail':
            # 기존 떠 있는 수평 판을 앞쪽의 taper 어깨로 바꾼다.
            s['rotation']['x']+=8;s['from'][2]+=.12;s['to'][2]-=.12
        if n.startswith('barrel/') or n.startswith('muzzle/shroud'):
            # 기존 두 직교 상자 대신 매끈한 팔각형의 긴 barrel shell.
            if n.endswith('-1'):continue
            lo=np.array(s['from']);hi=np.array(s['to']);c=(lo+hi)/2;r=(hi[0]-lo[0])/2
            s['from']=[8-r,11.51-r,float(lo[2])];s['to']=[8+r,11.51+r,float(hi[2])]
            out+=rounded(s,old,r*.42);continue
        out.append(s)
    return out

class Paint:
    PALETTE={'white':(202,211,209),'burgundy':(145,25,42),'rubber':(32,39,44),'steel':(89,99,108),'bore':(13,18,22)}
    def __init__(self,old,canonical):self.old=old;self.bird=old.LegacyPaint(canonical)
    def tile(self,s,face,w,h,q):
        u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
        p=q[0]+u[:,:,None]*(q[1]-q[0])+v[:,:,None]*(q[3]-q[0]);X,Y,Z=(p[:,:,i] for i in range(3))
        n=self.old.rotation(s)@np.array(self.old.NORMALS[face]);side=abs(n[0])>.60
        mat=s['material'];base=np.array(self.PALETTE[mat],float);a=np.zeros((h,w,4),np.uint8);a[:,:,3]=255
        # 소재별 면 분리. 방향 광원을 bake하지 않고 접촉 홈과 경계만 칠한다.
        a[:,:,:3]=base
        name=s['name']
        if s['artwork'] and side and not name.startswith('optic/'):
            old=self.bird.sample(p,n);red=(old[:,:,0]>old[:,:,1]*1.45)&(old[:,:,0]>old[:,:,2]*1.35)
            if name.startswith('receiver/'):red &= Z>12.5
            a[red,:3]=self.PALETTE['burgundy']
        if name.startswith(('receiver/','stock/')) and side:
            seam=(abs(Y-10.48)<.026)&(Z>6.6)&(Z<15.5)
            a[seam,:3]=[88,106,109]
            a[(abs(Y-10.54)<.020)&(Z>6.6)&(Z<15.5),:3]=[224,230,225]
            # 원본 총몸의 긴 눌린 채널: 동일 world 좌표라 새 면 사이에도 연속.
            chan=(Y>10.72)&(Y<11.12)&(Z>6.8)&(Z<11.5)
            a[chan,:3]=[155,172,174]
            a[chan&(Y>11.07),:3]=[93,115,119]
            a[chan&(Y<10.77),:3]=[222,230,226]
        if name.startswith('optic/hood-main') and side:
            border=(Z>5.05)&(Z<7.45)&(Y>12.40)&(Y<12.91)
            a[border,:3]=[82,99,102];a[border&(Z>5.14)&(Z<7.36)&(Y>12.46)&(Y<12.85),:3]=[160,29,43]
            for z,Z1 in ((5.25,6.02),(6.11,6.42),(6.51,6.82),(6.91,7.25)):
                a[(Z>z)&(Z<Z1)&(Y>12.54)&(Y<12.77),:3]=[235,229,211]
        if name.startswith('foregrip/') and mat=='rubber' and side:
            for y,z in ((6.60,4.3),(7.45,4.0),(8.30,3.7),(9.15,3.4)):
                a[(abs(Y-y-.33*(Z-z))<.060)&(abs(Z-z)<.56),:3]=[142,26,40]
        if name.startswith('muzzle/shroud') and side:
            for y in (11.24,11.62):
                for z in np.arange(-1.94,.43,.39):
                    r=np.hypot(Y-y,Z-z);a[r<.075,:3]=[17,24,30];a[(r>.075)&(r<.096),:3]=[123,134,140]
        if name.startswith('power-rail/') and side:
            a[(abs(Y-12.13)<.025)|(abs(Y-12.48)<.025),:3]=[64,24,33]
        if name.startswith('barrel/collar'):
            for z in np.arange(2.65,3.4,.12):a[abs(Z-z)<.018,:3]=[39,48,55]
        if mat=='steel':
            # 금속 절삭부에만 좁은 edge. bird/도장 UV에는 사각 island 테두리를 넣지 않는다.
            edge=(u<.009)|(u>.991)|(v<.009)|(v>.991)
            a[edge,:3]=np.clip(base*.83+np.array([234,239,233])*.17,0,255)
        return Image.fromarray(a)

def generate():
    old=load('scripts/generate_surface_w123_the_recluse.py','w251_recluse_base')
    raster=load('scripts/generate_surface_w115_hammerhead.py','w251_raster')
    parser,meshes,archive=raw_source(old);canonical=json.loads((ROOT/old.CANON).read_bytes())
    bp=MODEL+KEY+'.json';before=json.loads((BEFORE/bp).read_bytes());btex=Image.open(BEFORE/TEX).convert('RGBA')
    assert before['display']==canonical['display']
    specs=geometry(old);atlas,parts,uv=atlas_models(specs,Paint(old,canonical),old);models={}
    for part,es in [('full',parts['body']+parts['magazine']),*parts.items()]:
        j=dict(credit='W251 은둔자 / 형태·재질·연속 UV 보강',ambientocclusion=False,
            textures={'0':'destiny:item/weapon/w123/'+KEY,'particle':'destiny:item/weapon/w123/'+KEY},elements=es)
        if part=='full':j['display']=before['display']
        models[part]=j
    faces=validate(models,atlas,before['display'],raster)
    rawim=old.render([],None,old.camera(-27,14),meshes=meshes,paint=old.LegacyPaint(canonical),width=780,height=360)
    out={TEX:png(atlas)}
    for p,m in models.items():out[MODEL+KEY+('' if p=='full' else '_'+p)+'.json']=encode(m)
    inputs=[ROOT/'scripts/generate_surface_w123_the_recluse.py',ROOT/old.BB,ROOT/old.CANON,archive,PHOTO,old.CACHE/'Recluse.fbx']
    counts={p:len(es) for p,es in parts.items()}
    design=dict(stage='W251',id=KEY,method='기능 단위의 선택적 팔각 단면·기울어진 stock 어깨·연속 면 UV',
        source_frame=json.loads((ROOT/'art/weapons/w123/the_recluse/design.json').read_bytes())['frame'],
        before_kind='마스터가 보관한 dirty 통합본 snapshot',before_sha256={bp:pin(BEFORE/bp),TEX:pin(BEFORE/TEX)},
        source_sha256={str(p):pin(p) for p in inputs},parts={p:[s for s in specs if s['part']==p] for p in parts},uv_layout=uv,
        palette=Paint.PALETTE,changes=['receiver와 optic hood의 연속 사선 단면','stock pad의 둥근 측면과 bird field의 둥근 어깨','파지 좌표 내 둥근 두 grip','팔각 barrel과 원본 위치의 포구 천공 UV','회백 도장·붉은 안료·고무·절삭 금속과 접촉 채널 UV'],
        invariants=['원본 display exact','full = body + magazine','파지·분리부품 anchor·모션·ADS·타이밍 보존'],native_accepted=False)
    out[ART+'design.json']=encode(design);out[ART+'inspection.bbmodel']=encode(inspection(KEY,parts,atlas,before['display']))
    out[ART+'comparison.png']=compare(KEY,PHOTO,before,btex,models['full'],atlas,raster,rawim,([8,11.8,14.8],88))
    command='rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B '+SCRIPT
    out[ART+'review.md']=(f'# W251 은둔자 미술 보강\n\n실제 출력 {sum(counts.values())} 큐브: 본체 {counts["body"]}, 탄창 {counts["magazine"]}. full은 같은 조립체이며 중복 합산하지 않는다. 면 {faces}개 모두 명시적 UV, 1024² atlas 유지.\n\n기본 안료 사진과 복구 원본 FBX 20,369면·원본 stock/barrel 자료를 검토했다. 긴 receiver와 optic hood를 넓은 면을 가진 팔각 단면으로 바꾸고, stock의 세로 판·어깨를 둥글고 기울어진 부품으로 바꿨다. 두 grip의 단면·총열 단면도 실제 회전 큐브다. sight, 방아쇠 울, 포구 빈 공간을 보존한다. 기존 bird 마스크를 세계 좌표로 연속 전사하고, receiver 채널·빨간 charge 창·고무 liner·총구 천공은 면 UV로 정리했다. 무작위 얼룩이나 조명 보상 필터를 사용하지 않았다.\n\n비교 그림은 마스터의 변경 전 snapshot과 W251을 동일 카메라·광원·배율로 렌더한다. axis/angle과 XYZ를 RzRyRx로 정규화했다. CPU 그림은 native 수락 증거가 아니다. 작은 원본 FBX 그림의 색은 W31 안료 lookup으로, 원본 셰이더 복원은 아니다.\n\n검사: JSON parse, 실제 요소 수/UV 범위/texture 참조, full과 분리 조립체 일치, exact display, 원본 archive/FBX 해시, 재생성 --verify.\n\n실행: `{command}` 및 같은 명령의 `--verify`. 원본 생성기는 읽기 전용 import하며 매번 semantic 설계부터 시작한다.\n\n남은 master native QA: 공통 shader 수정 후 주간/실내의 1·3인칭, ADS sight 통공과 손 접촉, 탄창 분리·복귀, 10~20개 표시에서 틈·깜박임·끊김 확인. stock의 bird 경계는 이전 W31 마스크 해상도에 제한되며 미세 곡률은 팔각으로 단순화했다.\n').encode()
    manifest=dict(stage='W251',id=KEY,counts={'full':sum(counts.values()),**counts},emitted_faces=faces,atlas=[EDGE,EDGE],
        rotated_elements=sum(any(abs(s['rotation'][a])>1e-6 for a in 'xyz') for s in specs),max_assembled_elements=1000,
        full_equals_parts=True,display_exact=True,native_accepted=False,source_triangles=20369,
        generator=SCRIPT,generator_sha256=pin(ROOT/SCRIPT),sha256={p:sha(b) for p,b in out.items()},
        verification='소유 출력 bytes 재생성 비교; JSON/UV/refs/조립체/display targeted 검사',native_qa='master 대기')
    out[ART+'manifest.json']=encode(manifest);return out

def write_outputs(outputs,script,verify):
    batch=json.loads(Path('/private/tmp/destiny-w251/manifest.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['destination']==str(ROOT)))
    assert set(outputs)|{script}<=owned
    for p,data in outputs.items():
        target=ROOT/p
        if verify:assert target.read_bytes()==data,'재생성 drift: '+p
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    m=next(json.loads(b) for p,b in outputs.items() if p.endswith('/manifest.json'))
    print(json.dumps({'W251':m['id'],'검사' if verify else '생성':len(outputs),'실제_요소':m['counts'],'면':m['emitted_faces'],'native':'대기'},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');a=ap.parse_args();write_outputs(generate(),SCRIPT,a.verify)
