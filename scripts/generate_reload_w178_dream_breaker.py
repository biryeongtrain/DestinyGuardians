#!/usr/bin/env python3
"""Dream Breaker-specific FP energy-cell reload from inspected same-weapon gameplay.
Canonical W144 solids/UV/paint and display endpoints preserved; no runtime edits.
W177 supplies only rigid composition algebra, not trajectory or weapon topology.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w178/dream_breaker')
KEY='weapon_reload_w178_dream_breaker/dream_breaker'
SOURCE=A/'models/weapon_surface_w123/dream_breaker.json'
TWOHAND=A/'models/weapon/fusion_rifle/dream_breaker_twohand.json'
ITEM=A/'items/weapon/dream_breaker.json'
TEXTURE=A/'textures/item/weapon/w123/dream_breaker.png'
FP=('firstperson_righthand','firstperson_lefthand')
CELL_NAMES=('powerpack_full','pack_heel','pack_ribbed_side_-1','pack_ribbed_side_1')
GRIP=(8.,8.05,9.21)
MAG_ANCHOR=(8.,7.75,3.57)
# Seconds observed: 128.10..129.85. Hands obscure exact cell travel.
# Muzzle-up presentation, forward underside hand reach, cell withdrawal and reseat.
# Angles, clearance path, pivot and the final return are authored, never extracted bones.
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0)),
 (.09,(40,-6,-15),(.15,-.25,.15),(0,0,0)),
 (.20,(62,-12,-27),(.25,-.15,.25),(0,-.5,0)),
 (.30,(66,-10,-25),(.20,-.1,.30),(-.5,-4.3,.25)),
 (.43,(69,-9,-23),(.20,-.1,.30),(-2.4,-7.8,.5)),
 (.54,(61,-12,-27),(.20,-.15,.25),(-2.4,-7.8,.5)),
 (.66,(59,-12,-27),(.20,-.15,.25),(-1.2,-5.5,.3)),
 (.78,(62,-11,-24),(.20,-.1,.20),(0,-1.2,0)),
 (.84,(60,-10,-22),(.15,-.1,.15),(0,0,0)),
 (.92,(29,-5,-11),(.05,-.05,.05),(0,0,0)),
 (1.,(0,0,0),(0,0,0),(0,0,0)),
)
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/dream_breaker.json': '2116c53ffc4ad4ec6fa7c0cd9c8ff96fe71b8233af9b0927c579ed594d4d8e93', 'src/main/resources/assets/destiny/textures/item/weapon/w123/dream_breaker.png': 'c9bcbf03e80e6209c46fc13ea6b1097161d74fbb1983e1162fdeccc1d72a5b1c', 'src/main/resources/assets/destiny/items/weapon/dream_breaker.json': '5e5ee00e4d9473bd672f16eabece08040b660c8420817ac7ddf1cb158098e540', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/weapon_surface_w123/manifest.json': '4972bd808e5150d09e8f55e2c663b45f88ad8e660300310c5ecc04f4f672db6b', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker.json': 'c76b3daea47cdc06ed707bc178884f78a669762f6fea35d3fc811422269ddf42', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker_ads.json': 'fe623cf2b7406cc392faf49339ca2c6d1a8318a044dc85bb16eca8ab83d776a7', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker_ads_twohand.json': '58283e54b15e5f3aefa92487c172171934d70ae783dcf596cdedbec77edfa0e4', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker_inspect.json': '1d86bff6c34993a1c39246d8d899c7a47806a2a2656cf450e14561a94e060137', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker_inspect_twohand.json': '4f742e62ad2da47bda62ed931a3e6f927d8a315423226282e756f366fcaae34c', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/dream_breaker_twohand.json': '65edb5025d2143143f8c389d2f81fbd98286699ba01c725fa092076fef84102f', 'src/main/resources/assets/destiny/items/weapon_sight_w153/dream_breaker.json': '7509576bf38bb5dbc5042a1b3cb69247bd08260eaafa3cba69b8a3a3aa594a19', 'src/main/resources/assets/destiny/items/weapon_aim_w70/dream_breaker.json': '9c2fe78b37bfe96b43066d9f5c0568aa3c3edfc3b7cc707c5b4a493f66f79055'}

def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def add(a,b): return [x+y for x,y in zip(a,b)]
def sub(a,b): return [x-y for x,y in zip(a,b)]
def mul(a,b): return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def vec(m,v): return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]
def transpose(m): return list(map(list,zip(*m)))
def xyz(angles):
    x,y,z=map(math.radians,angles);a,b,c,d,e,f=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return [[c*e,-c*f,d],[b*d*e+a*f,-b*d*f+a*e,-b*c],[-a*d*e+b*f,a*d*f+b*e,a*c]]
def euler(m):
    b=math.asin(max(-1.,min(1.,m[0][2])))
    a,c=(math.atan2(-m[1][2],m[2][2]),math.atan2(-m[0][1],m[0][0])) if abs(math.cos(b))>1e-8 else (math.atan2(m[2][1],m[1][1]),0)
    return [round(math.degrees(v),9) for v in (a,b,c)]
def sample(p):
    if not math.isfinite(p) or not 0<=p<=1: raise ValueError(p)
    for a,b in zip(KEYS,KEYS[1:]):
        if p<=b[0]:
            t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return tuple([a[k][i]+(b[k][i]-a[k][i])*t for i in range(3)] for k in (1,2,3))
    raise ValueError(p)


def partition(source):
    """Four connected canonical cell solids; cuff/hose/ropes remain receiver cradle.
    Each original element appears exactly once, with every field/UV value retained.
    """
    parts={}
    for part in ('body','magazine'):
        model={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        model['elements']=[copy.deepcopy(e) for e in source['elements'] if (e['name'] in CELL_NAMES)==(part=='magazine')]
        parts[part]=model
    return parts

def pose_display(original,twohand,p,part,grip):
    if part not in ('body','magazine') or grip not in ('native','twohand'):raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8));anchor=sub(MAG_ANCHOR,(8,8,8))
    # Rotate both intact canonical parts around pistol contact. Cell receives only
    # authored source-local withdrawal/clearance; no artificial scaling or generic spin.
    local=(sub(add(h,vec(body,add(sub(anchor,h),offset))),vec(body,anchor))
           if part=='magazine' else sub(h,vec(body,h)))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
        if twohand[context]['scale']!=s or len(set(s))!=1:raise ValueError('Rigid carrier requires equal uniform grip scales')
        rotation=mul(base,body)
        position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
        if grip=='twohand':
            carrier=mul(xyz(twohand[context]['rotation']),transpose(base))
            position=add(vec(carrier,position),sub(twohand[context]['translation'],vec(carrier,idle['translation'])))
            rotation=mul(carrier,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def expected_output_paths():
    paths={A/f'models/{KEY}_{part}.json' for part in ('body','magazine')}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(21) for part in ('body','magazine') for grip in ('native','twohand'))
    return paths|{A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'}

def previews(source,reference,output):
    """Render independent emitted JSON reconstruction; orthographic/offline, no hands.
    Separate matrix implementation avoids asking authoring function to validate itself.
    """
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA');triangles={}
    def tris(model):
        model=copy.deepcopy(model)
        for e in model['elements']:
            r=e.get('rotation',{})
            if 'axis' in r:e['rotation']={'origin':r['origin'],r['axis']:r['angle']}
        return helper['model_triangles']({'part':model},texture)
    for part in ('body','magazine'):triangles[part]=tris(json.loads(output[A/f'models/{KEY}_{part}.json']))
    def rotation(a):
        x,y,z=np.radians(a)
        rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
        ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
        rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        return rx@ry@rz
    def posed(i,parts=('body','magazine'),grip='native',hand='firstperson_righthand'):
        ts=[]
        for part in parts:
            d=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_{grip}.json'])['display'][hand]
            rr=rotation(d['rotation']);ss=np.array(d['scale']);tt=np.array(d['translation'])
            for points,uv,tex,normal in triangles[part]:ts.append(((np.asarray(points)-8)*ss@rr.T+tt,uv,tex,rr@normal))
        return ts
    def raster(ts,cam,w,h,extent=None):
        if extent is None:extent=helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]
    cams=([1,.2,-.45],[-1,.35,.6],[.4,.4,1]);labels=('muzzle oblique','receiver oblique','stock oblique')
    sheet=Image.new('RGB',(1500,1890),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),'W178 DREAM BREAKER | emitted 26.3 display JSON reconstructed independently | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for row,cam in enumerate(cams):
        groups=[posed(i) for i in (0,9,20)]
        extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,500,310)
        for col,(i,g) in enumerate(zip((0,9,20),groups)):
            sheet.paste(raster(g,cam,500,310,extent),(col*500,55+row*345))
            draw.text((col*500+12,35+row*345),f'p={i/20:.2f} / {labels[row]} / common framing',fill='white')
    draw.text((12,1085),'182 receiver + 4 existing connected CELL solids = 186 total. Original geometry / face UV / paint; no added cubes or tiles.',fill='white')
    for col,cam in enumerate(cams):
        sheet.paste(raster(posed(9,('magazine',)),cam,500,310),(col*500,1140))
        draw.text((col*500+12,1115),'CELL ONLY: core + heel + 2 ribs | '+labels[col],fill='white')
    draw.text((12,1465),'Cell slides from fixed cuff/hose cradle. Exact hidden path and pivot authored; same canonical cell dimensions/UV retained.',fill='white')
    for col,cam in enumerate(cams):
        sheet.paste(raster(posed(9,('body',)),cam,500,310),(col*500,1525))
        draw.text((col*500+12,1500),'RECEIVER ONLY: fixed cuffs / hose / rope cradle',fill='white')
    draw.text((12,1852),'Endpoint 0 and 1 reproduce canonical assembled geometry and accepted grip displays. Native hand framing, sound and performance pending.',fill='white')
    story=Image.new('RGB',(1600,1630),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL 10u8PCK4B2c | Dream Breaker nameplate + 11 reload frames / nearest authored sample | OFFLINE, NO HAND IK',fill='white')
    for i,f in enumerate(reference['frames']):
        x=i%4*400;y=42+i//4*520
        im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));story.paste(im,(x,y))
        draw.text((x+8,y+228),f"ACTUAL {f['timestampSeconds']:.2f}s / source n={f['sourceFrameIndex']}",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[1,.2,-.45],400,225),(x,y+260))
        draw.text((x+8,y+488),f'AUTHORED p={index/20:.2f} | '+f['phase'],fill='white')
    draw.text((12,1600),'Original pixels above; authored orthographic transforms below. Source exit enters ability use; final canonical hip return is authored.',fill='white')
    return png(sheet),png(story)

def generate():
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=186:raise ValueError('W144 canonical geometry drift')
    ref=json.loads((ROOT/ART/'motion-reference.json').read_bytes())
    if not ref['inspectedActualFrames'] or len(ref['frames'])!=12:raise ValueError('Missing inspected actual frames')
    for f in ref['frames']:
        if sha((ROOT/f['path']).read_bytes())!=f['sha256']:raise ValueError('Reference drift')
    output={}
    def emit(p,v):output[p]=encode(v)
    parts=partition(source)
    for part,model in parts.items():emit(A/f'models/{KEY}_{part}.json',model)
    entries=[]
    for i in range(21):
        for part in ('body','magazine'):
            for grip in ('native','twohand'):emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],two,i/20,part,grip)))
        def composite(grip):return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in ('body','magazine')])
        entries.append(dict(threshold=i/20,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    reload=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=copy.deepcopy(item['model']))
    # Retain the exact accepted ADS/inspect branches even if stale positive reload
    # progress coexists with a mode string. Non-FP and negative inactive are canonical.
    mode_guard=copy.deepcopy(item['model']);mode_guard['fallback']=reload
    wrapper=copy.deepcopy(item);wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=mode_guard)],fallback=copy.deepcopy(item['model']))
    emit(A/f'items/{KEY}.json',wrapper)
    output[ART/'comparison.png'],output[ART/'storyboard.png']=previews(source,ref,output)
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,ART/'motion-reference.json',Path('scripts/generate_reload_w178_dream_breaker.py'),Path('scripts/generate_surface_w123_hammerhead.py')]
    emit(ART/'manifest.json',dict(stage='W178',weapon='dream_breaker',revision=1,itemModel='destiny:'+KEY,ownedFiles=106,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),sourceElements=186,bodyElements=182,movingElements=4,maxAssembledElements=186,elementLimit=1000,addedElements=0,
      sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),sourceRevision='W144 full-only semantic surface selected by weapon_surface_w123 manifest',geometryAndUVPreserved=True,
      partitionIndices={part:[i for i,e in enumerate(source['elements']) if (e['name'] in CELL_NAMES)==(part=='magazine')] for part in ('body','magazine')},cellNames=CELL_NAMES,
      partitionRationale='Four existing connected powerpack solids (full core, heel, two ribs) form energy cell. Fixed cuffs, ropes and hose remain receiver cradle. All canonical elements/UV fields occur once. No floating cap, flat tile, new payload or extra path.',
      authoredHiddenDetails='Part assignment is a semantic interpretation, not recovered bones. Exact latch, cell travel, grip pivot and angles are hand-occluded and authored. No geometry/UV/paint added or changed.',
      keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAG_ANCHOR,hipEndpoints=[0,20],endpointPolicy='Both parts use exact accepted canonical display at both endpoints for both hands and grips; assembled canonical geometry exact. Other contexts always canonical graph.',
      normalizedPhases={'raiseAndReach':[0,.20],'cellWithdrawal':[.20,.43],'holdClear':[.43,.54],'replacementApproach':[.54,.78],'seat':[.78,.84],'authoredHipReturn':[.84,1]},
      sourceObservedSeconds=ref['selectedSeconds'],reference=ref['url'],actualReferenceFrames=12,identityFrames=1,reloadFrames=11,referenceConfidence=ref['referenceConfidence'],motionAuthorship='Dream Breaker steep muzzle presentation and support-hand lower energy-cell manipulation; exact cell path authored from occluded same-weapon footage. W177 math/graph composition only; no borrowed sidearm trajectory.',
      timingPolicy='Normalized visual progression only: existing magazine6 / reload46ticks / charge667ms / burst7 / cadence13ticks unchanged; source match ammo/perks do not set gameplay.',
      rotationConvention='JOML Rx Ry Rz; body rotates about authored existing lattice pistol-grip contact; canonical cell translates in carrier-local coordinates; twohand uses rigid base compensation. Scale constant.',
      comparisonMethod='Independent reconstruction of emitted children: three obliques with endpoints and p=.45 common framing; separate cell and receiver cradle closeups; 12 actual PNG/offline authored pairs.',
      nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
      integration={'requiresNewMasterRoute':True,'masterRoute':23,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'dream_breaker','liveOwnerOnly':'Master publishes float1 only for active local owner FP reload; boolean0 selects existing grip. Negative inactive and non-FP use canonical graph. Master restores on completion/cancel/swap/equip/unequip/death/disconnect.','masterTests':'Master owns actual reload lifecycle/ammo/timing tests and route23 integration. Worker standalone tests cover asset parser/codec/JOML only.'},
      nativeQueue=['Both FP hands / both grips: raised muzzle framing, energy cell clearance/reseat, exact endpoint recovery.','ADS/inspect, interruption, completion, equip/unequip, swap, death/disconnect: route23 owner publication and cleanup.','Third-person observer / GUI / ground / fixed / head canonical; no third-person reload claimed.','Native sound and brief 10-20 displays for obvious defects remain master-owned and unverified.'],
      canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()},limitations=ref['limitations']))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact 90')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args();output=generate()
    owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w178-manifest.json').read_bytes())['features'] if f['name']=='w178-dream-breaker-reload'))
    if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 87 pack assets; 182+4=186 assembled elements; native pending')
if __name__=='__main__':main()
