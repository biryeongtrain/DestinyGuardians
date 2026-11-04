#!/usr/bin/env python3
"""Deterministic editable bbmodel -> vanilla native held-item pack (no Blender needed).

--verify checks bytes without writing. Does not touch supers, source downloads,
existing Blockbench projects, other namespaces, or the user's resource packs.
"""
import argparse,base64,copy,hashlib,itertools,json,math,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/destiny'
ART=ROOT/'art/weapons/w30'
def dump(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def digest(b):return hashlib.sha256(b).hexdigest()
def transform(rotation,translation,scale):return dict(rotation=rotation,translation=translation,scale=[scale]*3)
def centered_context(bounds,rotation,limit=14.8):
    def rotate(v):
        x,y,z=v
        # ItemTransform uses rotationXYZ: apply local Z, then Y, then X.
        rx,ry,rz=map(math.radians,rotation)
        x,y=x*math.cos(rz)-y*math.sin(rz),x*math.sin(rz)+y*math.cos(rz)
        x,z=x*math.cos(ry)+z*math.sin(ry),-x*math.sin(ry)+z*math.cos(ry)
        y,z=y*math.cos(rx)-z*math.sin(rx),y*math.sin(rx)+z*math.cos(rx)
        return x,y,z
    points=[rotate([p[a]-8 for a in range(3)]) for p in itertools.product(*zip(*bounds))]
    low=[min(p[a] for p in points) for a in range(3)];high=[max(p[a] for p in points) for a in range(3)]
    scale=min(.75,limit/max(high[a]-low[a] for a in (0,1)))
    return transform(rotation,[round(-(low[a]+high[a])*.5*scale,5) for a in range(3)],round(scale,5))

def legacy_display(row,state='hip',bounds=None):
    tall=row['family'] in ('bow','sword','glaive')
    # These are ordinary ItemTransforms, NOT DisplayHud's vecToQuat axis adapter.
    d={
      'firstperson_righthand':transform([0,12,0],[0,0,-2],.85),
      'firstperson_lefthand':transform([0,-12,0],[0,0,-2],.85),
      'thirdperson_righthand':transform([90,0,0],[0,2,0],.7),
      'thirdperson_lefthand':transform([90,0,0],[0,2,0],.7),
      'gui':transform([10,65,-10],[0,0,0],.52 if tall else .6),
      'ground':transform([0,0,0],[0,3,0],.4),
      'fixed':transform([0,90,0],[0,0,0],.65),
      'head':transform([0,0,0],[0,8,0],.6)}
    if tall:
        scale={'sword':.9,'bow':.85,'glaive':1.0}[row['family']]
        d['thirdperson_righthand']=transform([90,0,0],[0,2,0],scale)
        d['thirdperson_lefthand']=transform([90,0,0],[0,2,0],scale)
        center=(bounds[0][1]+bounds[1][1])/2-8 if bounds else 4
        y=round(5.92-center*.6,4)
        d['firstperson_righthand']=transform([0,12,0],[0,y,-7],.6)
        d['firstperson_lefthand']=transform([0,-12,0],[0,y,-7],.6)
    if bounds:
        d['gui']=centered_context(bounds,[10,65,-10])
        d['fixed']=centered_context(bounds,[0,90,0])
    if state=='ads':
        if tall:
            d['firstperson_righthand']=transform([0,0,0],[-8.96,round(5.92-center*.6,4),-7],.6)
            d['firstperson_lefthand']=transform([0,0,0],[8.96,round(5.92-center*.6,4),-7],.6)
            return d
        y=round(8.32-(bounds[1][1]-8)*.95,4) if bounds and not tall else 1
        d['firstperson_righthand']=transform([0,0,0],[-8.96,y,-4],.95)
        d['firstperson_lefthand']=transform([0,0,0],[8.96,y,-4],.95)
    elif state=='inspect':
        if tall:
            d['firstperson_righthand']=transform([5,45,-5],[-2,round(5.92-center*.6,4),-7],.6)
            d['firstperson_lefthand']=transform([5,-45,5],[2,round(5.92-center*.6,4),-7],.6)
            return d
        d['firstperson_righthand']=transform([5,45,-15],[-2,1,-3],.85)
        d['firstperson_lefthand']=transform([5,-45,15],[2,1,-3],.85)
    return d

def display(row,state='hip',bounds=None):
    d=legacy_display(row,state,bounds)
    if row['family']=='glaive':
        # W37: local +Y is the shaft/head axis, not a rifle's -Z muzzle.
        # Pitch that shaft into depth and twist the broad blade toward the viewer.
        pose=json.loads((ROOT/'art/weapons/w37/firstperson-poses.json').read_text())['poses'][state]
        # Left-handed ItemTransform performs the reflection itself. Do not double-mirror.
        for hand in ('righthand','lefthand'):
            d['firstperson_'+hand]=copy.deepcopy(pose)
    return d

def two_hand_display(d,family=None):
    """W32: separate pose parents; leave all accepted W31 displays untouched.

    MC26.3 charged crossbow idle: T(-.641864*sign,0,0) Ry(10*sign).
    Invert that before the native ItemTransform (left-hand reflection is native).
    This compensation is for idle main hand, not an arbitrary first-person IK rig.
    """
    d=copy.deepcopy(d)
    angle=math.radians(-10);c,s=math.cos(angle),math.sin(angle)
    def mul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    for hand in ('righthand','lefthand'):
        t=d['firstperson_'+hand];x,y,z=t['translation'];x+=.641864*16
        t['translation']=[round(c*x+s*z,6),y,round(-s*x+c*z,6)]
        a,b,g=map(math.radians,t['rotation'])
        rx=[[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]]
        ry=[[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]]
        rz=[[math.cos(g),-math.sin(g),0],[math.sin(g),math.cos(g),0],[0,0,1]]
        m=mul([[c,0,s],[0,1,0],[-s,0,c]],mul(rx,mul(ry,rz)))
        t['rotation']=[round(math.degrees(v),6) for v in (math.atan2(-m[1][2],m[2][2]),math.asin(m[0][2]),math.atan2(-m[0][1],m[0][0]))]
        # Cancel the vanilla crossbow's inward arm yaw and raised pitch at level aim.
        if family=='glaive':
            # W38: shaft local +Y points into avatar forward -Z (not sideways across chest).
            # Separate from a rifle's -Z axis; preserve W37 first-person compensation.
            pose=json.loads((ROOT/'art/weapons/w38/thirdperson-pose.json').read_text())
            d['thirdperson_'+hand]={k:copy.deepcopy(pose[k]) for k in ('rotation','translation','scale')}
        else:
            d['thirdperson_'+hand]=transform([round(math.degrees(.1),6),round(math.degrees(-.3),6),0],[0,-2,2],.7)
    return d

def grip_model(model):
    native=dict(type='minecraft:model',model='destiny:'+model)
    return dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,
                on_true=dict(type='minecraft:model',model='destiny:'+model+'_twohand'),on_false=native)

def generate():
    rows=json.loads((ART/'catalog.json').read_text());outputs={};entries=[];models=[]
    keys=set()
    for row in rows:
        key=(row['family'],row['frame']);assert key not in keys,key;keys.add(key)
        id=row['id'];family=row['family'];path=ROOT/f'art/blockbench/weapons/w30/{id}.bbmodel'
        source=json.loads(path.read_text());cubes=source['elements']
        assert 8<len(cubes)<=256,(id,len(cubes))
        texture=base64.b64decode(source['textures'][0]['source'].split(',')[1],validate=True)
        assert digest(texture)==source['destiny_w30']['texture_sha256']
        tex=f'item/weapon/w30/{id}'
        outputs[ASSETS/f'textures/{tex}.png']=texture
        elements=[]
        for c in cubes:
            assert c['type']=='cube'
            for axis in range(3):assert -16<=c['from'][axis]<c['to'][axis]<=32,(id,c['name'])
            element={'from':c['from'],'to':c['to'],'faces':{n:dict(uv=f['uv'],texture='#0') for n,f in c['faces'].items()}}
            elements.append(element)
        model=f'weapon/{family}/{id}'
        # Denser source sampling can change tiny accessory extents. Preserve the
        # accepted held/GUI transforms rather than moving the weapon in-hand.
        bounds=source.get('destiny_w31',{}).get('display_bounds',source['destiny_w30']['model_bounds'])
        outputs[ASSETS/f'models/{model}.json']=dump(dict(credit='W30 source-referenced cuboid reconstruction; local review only',textures={'0':'destiny:'+tex,'particle':'destiny:'+tex},elements=elements,display=display(row,bounds=bounds)))
        for state in ('ads','inspect'):
            outputs[ASSETS/f'models/{model}_{state}.json']=dump(dict(parent='destiny:'+model,display=display(row,state,bounds)))
        for state in ('hip','ads','inspect'):
            suffix='' if state=='hip' else '_'+state
            outputs[ASSETS/f'models/{model}{suffix}_twohand.json']=dump(dict(parent='destiny:'+model+suffix,display=two_hand_display(display(row,state,bounds),family)))
        definition=dict(type='minecraft:select',property='minecraft:custom_model_data',index=0,
                        cases=[dict(when=s,model=grip_model(model+'_'+s)) for s in ('ads','inspect')],
                        fallback=grip_model(model))
        outputs[ASSETS/f'items/weapon/{id}.json']=dump(dict(model=definition,hand_animation_on_swap=False))
        entries.append(dict(id=id,family=family,frame=row['frame'],name=row['name'],source_frame_label=row['source_frame_label'],item_model='destiny:weapon/'+id))
        info=source['destiny_w30']
        models.append(dict(id=id,family=family,frame=row['frame'],cubes=len(cubes),bbmodel_sha256=digest(path.read_bytes()),texture_sha256=digest(texture),source_triangles=info['source_triangles'],textured_triangles=info['textured_triangles'],source_files=info['source_files'],source_drive_id=row['source']['id']))
    runtime=ROOT/'src/main/resources/destiny/weapons/w30.json';outputs[runtime]=dump(entries)
    hashes={str(p.relative_to(ROOT)):digest(b) for p,b in outputs.items()}
    outputs[ART/'manifest.json']=dump(dict(schema=1,models=models,counts=dict(families=len({r['family'] for r in rows}),models=len(rows)),catalog_sha256=digest((ART/'catalog.json').read_bytes()),runtime_sha256=hashes))
    text=['# W30 — 무기군·프레임 선정표','',
          '공유 시즌 1~20 아카이브에서 확보한 전통 프레임 대표 63종. 최신 전체 프레임 목록이 아님.',
          '발사/재장전 기능 없이 네이티브 held item과 hip/ads/inspect 정적 포즈 프리뷰를 제공한다.',
          '','| 분류 | 카탈로그 프레임 | 공식 intrinsic | 대표 무기 | 큐브 | 원본 |','|---|---|---|---|---:|---|']
    for row,m in zip(rows,models):
        text.append(f"| `{row['family']}` | `{row['frame']}` | {row['source_frame_label']} | {row['name']} | {m['cubes']} | [Drive](https://drive.google.com/file/d/{row['source']['id']}/view) / [item hash](https://www.light.gg/db/items/{row['bungie_hash']}/) `{row['bungie_hash']}` |")
    text+=['','## 명시적 후속 범위','',
           '- 아카이브에 없는 공격적/속사 글레이브 및 이후 추가된 프레임은 다른 총을 대체 등록하지 않는다.',
           '- 경이 무기 고유 프레임과 최신 지원/로켓보조/신규 점사 계열은 별도 원본 확보·선정이 필요하다.',
           '- Stormchaser: 과거 Aggressive 계열로 불렸으나 조회한 공식 데이터 intrinsic은 Adaptive Burst.',
           '- Brass Attacks: 과거 Aggressive Burst, 조회한 공식 데이터는 Heavy Burst.',
           '- 초안의 잘못된 RPM/프레임 이름과 기존 밸런스 수치를 모델 카탈로그와 혼합하지 않았다.',
           '- Cube reconstruction은 source side-volume 기반이므로 PBR·미세 곡면·동적 부품은 원본과 다르다.','']
    outputs[ROOT/'docs/design/45_W30_무기_선정표.md']='\n'.join(text).encode()
    return outputs

def main():
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args()
    outputs=generate();bad=[]
    for path,b in outputs.items():
        if args.verify:
            if not path.exists() or path.read_bytes()!=b:bad.append(str(path.relative_to(ROOT)))
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
    if bad:print('W30 stale outputs:',*bad,sep='\n');return 1
    print(f"W30 {'verified' if args.verify else 'generated'} {len(outputs)} files")
    return 0
if __name__=='__main__':sys.exit(main())
