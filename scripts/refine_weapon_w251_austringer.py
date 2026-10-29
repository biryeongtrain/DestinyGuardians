#!/usr/bin/env python3
"""W251 매사냥꾼: 원본 semantic 설계의 형상과 UV 보강. --verify 지원."""
import sys
sys.dont_write_bytecode = True
import argparse, collections, copy, importlib.util, json, math
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('scripts/refine_weapon_w251_the_recluse.py','w251_common')
KEY='austringer';SCRIPT='scripts/refine_weapon_w251_austringer.py';ART='art/weapons/w251/austringer/'
MODEL=C.MODEL+KEY+'.json';TEX=C.ASSET+'textures/item/weapon/w123/'+KEY+'.png'

def design(old,meta,rotation_helper):
    d=old.design(meta);out=[]
    for s in d['parts']:
        s=copy.deepcopy(s);e=s['geometry'];n=e['name']
        if s['group']=='grip':
            continue
        if n=='Shroud_mass':
            out+=C.rounded(s,rotation_helper,.29);continue
        if n.startswith('Nose_flank'):
            center=(np.array(e['from'])+e['to'])/2
            e['rotation']['y']=-7 if center[0]<8 else 7
            out+=C.rounded(s,rotation_helper,.12);continue
        if n=='Shroud_crown':
            # 연속 crown은 유지, 원본의 앞으로 낮아지는 nose를 별도 어깨로 표현.
            e['from'][2]= -5.58;e['to'][1]-=.025
        if n=='Nose_upper':
            e['rotation']['x']=-9;e['from'][2]-=.05
        if n=='Nose_lower':
            e['rotation']['x']=8
        if n.startswith('Crown_chamfer'):
            # 기존 얇은 전장 strip 대신 새 shroud의 큰 대각 단면이 담당.
            continue
        if n.startswith('Bezel_'):
            out+=C.rounded(s,rotation_helper,.16,axes=(1,2));continue
        if n=='Breech':
            out+=C.rounded(s,rotation_helper,.16);continue
        if n=='Rear_tang':
            e['rotation']['x']+=6
        out.append(s)
    # 원본 파지 frame 안에서 두 큰 입체로 이어지는 곡선 grip.
    # 이전의 palm/heel/backstrap 여러 단면이 드러나던 단절을 없앤다.
    for name,a,b,width,depth,radius,axes,motif in [
        ('Grip_neck_W251',[8,11.32,6.82],[8,10.10,7.08],1.32,1.75,.20,(0,2),'grip_curve'),
        ('Grip_curve_W251',[8,10.23,7.13],[8,7.28,8.49],1.40,1.83,.64,(1,2),'grip_curve')]:
        a=np.array(a,float);b=np.array(b,float);center=(a+b)/2;size=np.array([width,np.linalg.norm(b-a),depth])
        s=dict(group='grip',material='grip',motif=motif,geometry=dict(name=name,
            **{'from':(center-size/2).tolist(),'to':(center+size/2).tolist()},
            rotation={'origin':center.tolist(),'x':math.degrees(math.atan2(b[2]-a[2],b[1]-a[1])),'y':0,'z':0}))
        # 긴 축 방향은 뒤집혀도 같은 입체지만 motif world 좌표는 그대로 유지된다.
        out+=C.rounded(s,rotation_helper,radius,axes=axes)
    # 약실의 넓은 longitudinal lands: 실루엣과 깊이, 얕은 flutes는 UV.
    for side in (-1,1):
        center=np.array([8+side*1.025,12.37,4.34]);size=np.array([.12,.62,2.57])
        out.append(dict(group='receiver',material='steel_dark',motif='cylinder_land',geometry=dict(name=f'Cylinder_land_{side}',
            **{'from':(center-size/2).tolist(),'to':(center+size/2).tolist()},rotation={'origin':center.tolist(),'x':0,'y':0,'z':side*9})))
    d.update(stage='W251',revision='큰단면-곡선그립-재질홈-r1',parts=out,
        groups=dict(collections.Counter(s['group'] for s in out)),method='기능 부품 선택적 팔각 단면·taper nose·둥근 heel + 면별 UV',
        palette={**old.PALETTE,'steel_dark':[68,78,81]},limitations=['팔각 단면은 원본 미세 곡률의 단순화다.','보라 inset의 정적 색은 원본 동적 shader 복원이 아니다.','native 판정은 master 대기.'])
    return d

def paint(old,s,face,w,h):
    a=np.array(old.tile(s,face,w,h));u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=old.face_points(s['geometry'],face);p=q[0]+u[:,:,None]*(q[1]-q[0])+v[:,:,None]*(q[3]-q[0]);X,Y,Z=(p[:,:,i] for i in range(3))
    motif=s['motif'];mat=s['material'];side=face in ('east','west');base=np.array(old.PALETTE[mat],float)
    if motif=='bezel':
        # 한 bezel의 world UV. 단면을 늘려도 기존 네 모서리 장식은 한 번만 그린다.
        center=np.array(s['geometry']['rotation']['origin']);z=-3.56 if center[2]<-1.8 else -.16
        dy=abs(Y-12.92);dz=abs(Z-z);a[:,:,:3]=base
        rim=(abs(np.maximum(dy/.675,dz/.710)-.91)<.045)&(dy+dz<1.27)
        a[rim,:3]=[218,201,145]
        for sy in (-1,1):
            for sz in (-1,1):
                r=np.hypot(Y-(12.92+sy*.48),Z-(z+sz*.52))
                a[r<.067,:3]=[185,167,108];a[(r>.067)&(r<.087),:3]=[82,74,45]
    if motif=='grip_curve':
        a[:,:,:3]=base
        stripe=np.mod(Y+.47*Z,.56)
        if side:
            wrap=(Y>8.15)&(Y<10.55)
            a[wrap&(stripe<.050),:3]=[21,28,31]
            a[wrap&(stripe>.050)&(stripe<.078),:3]=[64,72,71]
            cells=np.hypot(np.mod(Y*1.07+.20,.18)-.09,np.mod(Z,.18)-.09)
            a[(cells<.022)&(Y<8.12),:3]=[23,30,32]
            for y,z in ((10.65,6.99),(7.60,8.65)):
                r=np.hypot(Z-z,Y-y);a[(r<.12)&(r>.085),:3]=[110,115,105];a[r<.061,:3]=[26,34,35]
    if motif=='shroud' and side:
        # 원본의 넓은 금속 면 아래 recessed band와 밝은 lip. 위치가 모든 새 단면에 연속.
        seam=(Y>11.88)&(Y<12.12);a[seam,:3]=[119,99,56]
        a[(Y>12.10)&(Y<12.145),:3]=[221,208,160]
        for z in (-5.30,-1.86,1.58):
            dy=Y-12.56;half=.25+.42*np.clip(dy/.80,0,1);edge=abs(abs(Z-z)-half)
            a[(dy>0)&(dy<.82)&(edge<.035),:3]=[113,94,53]
    if motif in ('cylinder','cylinder_band','cylinder_land'):
        # 실린더의 실제 rib 사이 긴 얕은 groove. 광원 방향을 고정하지 않는다.
        if side:
            groove=(Y>12.75)&(Y<12.92)&(Z>3.15)&(Z<5.53)
            a[groove,:3]=[19,26,29];a[(Y>12.92)&(Y<12.955)&(Z>3.15)&(Z<5.53),:3]=[104,116,116]
            a[(Y>11.82)&(Y<11.86)&(Z>3.12)&(Z<5.57),:3]=[78,90,92]
        if motif=='cylinder_land':
            a[:,:,:3]=[64,76,80];a[(v<.05)|(v>.95),:3]=[99,112,114]
    if motif in ('grip_lower','wrap','grip_upper') and side:
        # 넓은 고무 면에 동일 노이즈 대신 원본 wrap와 분리된 접촉 가장자리.
        a[(abs(X-8)>.64)&(Y<9.5),:3]=(base*.90).astype(np.uint8)
    if mat.startswith('gold') and motif not in ('bezel',):
        # 긴 면을 가로지르는 가짜 blotch 없이 좁은 절삭 edge만 추가.
        edge=(u<.008)|(u>.992)|(v<.009)|(v>.991)
        a[edge,:3]=np.minimum(base*.90+[23,22,18],255)
    return Image.fromarray(a)

def compile_model(d,old,before):
    requests=[];atlas=Image.new('RGBA',(1024,1024))
    for s in d['parts']:
        e=s['geometry'];e['faces']={}
        for face in old.FACES:
            q=old.face_points(e,face);density=23 if s['group'] in ('shroud','insets','grip') else 16
            w=max(4,math.ceil(np.linalg.norm(q[1]-q[0])*density));h=max(4,math.ceil(np.linalg.norm(q[3]-q[0])*density))
            requests.append((h,w,e['name'],face,s))
    x=y=2;row=0;ledger=[]
    for h,w,name,face,s in sorted(requests,key=lambda t:(-t[0],-t[1],t[2],t[3])):
        if x+w+2>1024:x=2;y+=row+4;row=0
        assert y+h+2<=1024,'1024 atlas overflow'
        im=paint(old,s,face,w,h);atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        s['geometry']['faces'][face]={'uv':[q*16/1024 for q in (x,y,x+w,y+h)],'texture':'#0'}
        ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    d['atlas']=dict(size=1024,gutter=2,islands=ledger,used_texels=sum((q['pixels'][2]-q['pixels'][0])*(q['pixels'][3]-q['pixels'][1]) for q in ledger))
    return atlas,dict(credit='W251 매사냥꾼 / 형상·재질·UV 보강',textures={'0':'destiny:item/weapon/w123/austringer','particle':'destiny:item/weapon/w123/austringer'},elements=[s['geometry'] for s in d['parts']],display=before['display'])

def generate():
    old=load('scripts/generate_surface_w123_austringer.py','w251_austringer_base');rot=C.load('scripts/generate_surface_w123_the_recluse.py','rotation_helper')
    meshes,meta=old.source();before=json.loads((C.BEFORE/MODEL).read_bytes());btex=Image.open(C.BEFORE/TEX).convert('RGBA')
    assert before['display']==json.loads((ROOT/old.BASE).read_bytes())['display']
    old.PALETTE.update(gold=[196,178,118],gold_edge=[224,209,157],gold_shadow=[133,111,62],black=[43,51,55],grip=[45,51,52],steel=[139,148,147],steel_dark=[68,78,81])
    d=design(old,meta,rot);atlas,model=compile_model(d,old,before);raster=C.load('scripts/generate_surface_w115_hammerhead.py','austringer_raster')
    faces=C.validate({'full':model},atlas,before['display'],raster);n=len(model['elements'])
    # 실제 원본 local FBX/UV로 만든 작은 중립 diffuse 참고 그림.
    pts=np.concatenate([m['vertices'] for m in meshes]);cam=np.array([-1,.35,-.65]);cam/=np.linalg.norm(cam)
    right=np.cross([0,1,0],cam);right/=np.linalg.norm(right);up=np.cross(cam,right);proj=np.c_[pts@right,pts@up];lo,hi=proj.min(0),proj.max(0)
    rawim,_=raster.render(old.raw_triangles(meshes),cam,((lo+hi)/2,min(740/(hi[0]-lo[0]),320/(hi[1]-lo[1]))),(780,360),raw=True)
    d.update(before_kind='마스터 dirty 통합본 snapshot',before_sha256={MODEL:C.pin(C.BEFORE/MODEL),TEX:C.pin(C.BEFORE/TEX)},native_accepted=False)
    d['input_sha256'].update({C.SCRIPT:C.pin(ROOT/C.SCRIPT),'scripts/generate_surface_w123_austringer.py':C.pin(ROOT/'scripts/generate_surface_w123_austringer.py')})
    groups=collections.defaultdict(list)
    for s in d['parts']:groups[s['group']].append(s['geometry'])
    outputs={MODEL:C.encode(model),TEX:C.png(atlas),ART+'design.json':C.encode(d),
        ART+'inspection.bbmodel':C.encode(C.inspection(KEY,groups,atlas,before['display'])),
        ART+'comparison.png':C.compare(KEY,old.PHOTO,before,btex,model,atlas,raster,rawim,([8,8.5,8.3],95))}
    command='rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B '+SCRIPT
    outputs[ART+'review.md']=(f'# W251 매사냥꾼 미술 보강\n\n실제 출력 {n} 큐브 / {faces} UV 면 / 1024² atlas. full 전용이며 1,000 상한 이내다.\n\n기본 안료 사진·원본 AFrame diffuse·실제 복구 FBX 15,680삼각면을 확인했다. 금색 shroud의 큰 직육면체를 넓은 연속 면과 사선 단면으로 교체하고, nose flanks는 좁아지는 회전 부품으로 만들었다. 네 bezel의 모서리를 둥글려 보라 inset과 단차를 연결했다. 그립의 전후 단면과 특히 heel의 측면 윤곽을 실제 형상으로 둥글리고, 원통 약실에는 두 개의 넓은 bearing land를 추가했다.\n\n원본 triangle recess·보라 inset·wrap 무늬는 유지한다. 금속 하단 홈과 밝은 lip, 약실의 긴 flute·고무 접촉 경계를 면별 연속 UV에 넣었다. 무작위 오염·노이즈·전역 contrast 필터나 full-bright 보상은 없다. 보라 무늬는 기존 정적 해석이며 원본 동적 shader 복원이 아니다.\n\n비교 그림: 실제 기본안료 사진 + 실제 local rip 중립 diffuse 참고 + 마스터 변경 전 snapshot과 W251의 동일광원/동일카메라/동일배율 측면·앞뒤사선·그립 확대. legacy axis/angle도 XYZ로 정규화했다. CPU 그림은 native 수락 근거가 아니다.\n\n검사: JSON parse·요소/면 count·UV 범위·texture ref·exact display·FBX source pin·--verify 재생성. 기존 모션·ADS display·손 파지점·canonical 및 장전 graph는 보존한다.\n\n실행: `{command}` 및 같은 명령의 `--verify`. 두 W251 스크립트의 공용 읽기 전용 helper를 사용하며 원본 semantic design에서 매번 재생성한다.\n\n남은 master native QA: shader 수정 후 실내/주간 1·3인칭 재질 대비, 그립 손 접촉·ADS notch 통공, 일반 장전 복귀, 10~20개 표시의 틈·깜박임·끊김. 미세 곡률은 팔각 단순화이며 native 성능은 미측정이다.\n').encode()
    outputs[ART+'manifest.json']=C.encode(dict(stage='W251',id=KEY,counts={'full':n},emitted_faces=faces,atlas=[1024,1024],max_assembled_elements=1000,
        rotated_elements=sum(any(abs(s['geometry']['rotation'][a])>1e-6 for a in 'xyz') for s in d['parts']),display_exact=True,
        native_accepted=False,generator=SCRIPT,generator_sha256=C.pin(ROOT/SCRIPT),source_triangles=15680,
        sha256={p:C.sha(b) for p,b in outputs.items()},verification='JSON/UV/refs/display targeted + byte deterministic regeneration',native_qa='master 대기'))
    return outputs

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args();C.write_outputs(generate(),SCRIPT,args.verify)
