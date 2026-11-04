#!/usr/bin/env python3
"""Halfdan-D reload from inspected same-weapon gameplay; W179 rigid algebra/graph only.
Canonical geometry/UV/dye, gameplay, sound and ADS preserved.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w180/halfdan_d')
KEY='weapon_reload_w180_halfdan_d/halfdan_d'
SOURCE=A/'models/weapon_surface_w123/halfdan_d.json'
TWOHAND=A/'models/weapon/auto_rifle/halfdan_d_twohand.json'
ITEM=A/'items/weapon/halfdan_d.json'
TEXTURE=A/'textures/item/weapon/w123/halfdan_d.png'
FP=('firstperson_righthand','firstperson_lefthand')
MAGAZINE_NAMES=('Magazine_neck','Magazine_body','Magazine_floor','Magazine_heel')
GRIP=(8.,8.5,8.55)
MAG_ANCHOR=(8.,10.,3.05)
# Independent Halfdan keys: shallow lift, downward draw, clear hold, approach,
# positive seating rock and support-hand recovery. Hidden exact stroke authored.
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0)),
 (.10,(16,-3,17),(.25,-.25,.2),(0,0,0)),
 (.20,(22,-6,23),(.35,-.20,.25),(-.15,-1.3,-.15)),
 (.33,(23,-7,24),(.35,-.20,.25),(-.65,-6.2,-.65)),
 (.53,(24,-6,22),(.35,-.15,.25),(-.65,-6.2,-.65)),
 (.60,(25,-5,21),(.30,-.15,.20),(-.25,-2.8,-.25)),
 (.67,(25,-4,20),(.25,-.1,.15),(0,0,0)),
 (.73,(33,-3,25),(.25,-.05,.15),(0,0,0)),
 (.80,(18,-1,13),(.15,-.10,.1),(0,0,0)),
 (.90,(7,0,4),(.05,-.05,.05),(0,0,0)),
 (1.,(0,0,0),(0,0,0),(0,0,0)),
)
REFERENCE_URL='https://www.youtube.com/watch?v=JkSdcwO-MGM'
REFERENCE_DIR=Path('/private/tmp/w180-halfdan-d-report')
REFERENCE_TIMES=(5.,77.1,77.2,77.3,77.4,77.5,77.6,77.7,77.8,77.9,78.,78.1,78.2,78.3,78.4,78.5,78.6)
OBSERVATIONS=(
 'HALFDAN-D nameplate and Hakke silhouette; source blue-marked paint/optic are not local canonical dye/iron sights.',
 'Leaves ADS after firing; same long shroud, stock and narrow magazine.',
 'Receiver starts shallow muzzle-up presentation; support hand approaches underside.',
 'Support hand reaches magazine as receiver rolls to expose well.',
 'Hand contacts magazine; raised presentation holds.',
 'Long box magazine withdrawn downward by support hand below well.',
 'Magazine clears well and leaves lower view; empty well visible.',
 'Empty well held in view; support hand offscreen.',
 'Empty well hold continues with shallow receiver rock.',
 'Empty well still visible before replacement approach.',
 'Replacement magazine rises from lower left toward well.',
 'Magazine enters well; source ammo changes 26 to 35, not local mechanics.',
 'Support hand braces/slaps seated magazine; receiver kicks higher.',
 'Support hand moves forward beneath handguard as receiver lowers.',
 'Receiver returns toward hip; magazine seated.',
 'Hip settling and support-hand recovery.',
 'Hip silhouette recovered; no separately measurable charging-handle travel established.'
)
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/halfdan_d.json': '74405ad3341ee8a0bc6240d29277337415df78421e2cba488bc72f54ad2c33c8', 'src/main/resources/assets/destiny/textures/item/weapon/w123/halfdan_d.png': 'bfdcc8d15ebb032077d2dccb8c155d8e11208e1a65f9c8a79f85ac3b3311ee6e', 'src/main/resources/assets/destiny/items/weapon/halfdan_d.json': '9575f42312bb37216e8a004bf31df33f805242d4230cc84366f762cbff692d2e', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/weapon_surface_w123/manifest.json': '4972bd808e5150d09e8f55e2c663b45f88ad8e660300310c5ecc04f4f672db6b', 'src/main/resources/assets/destiny/items/weapon_aim_w70/halfdan_d.json': 'fc6e58c07328135f80b444455eacba3ed2b6a00f10d5bf6b1006c327ffa3ff35', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/halfdan_d.json': 'a6c1fa0e4084403c66e8136179f320ace92bd4b7962f0bc59ae648df0830f378', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/halfdan_d_ads.json': '6160aa78789d33b707625d6949531924d0fb268e6565e74d8041d91171d1e326', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/halfdan_d_ads_twohand.json': 'e48bbe749a0faed7d0a47016a3a31493e4faf2e81ab193171227ab279c227f49', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/halfdan_d_inspect.json': 'af9185e2fa7832bba3f84a084ac1076b34acfffcc25cf25f2a6bc529fd24a8d8', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/halfdan_d_inspect_twohand.json': 'b3cd442ad0e9cbd107930855da82a95afaaaf5e13385c8e87dfc72147492bccd', 'src/main/resources/assets/destiny/models/weapon/auto_rifle/halfdan_d_twohand.json': '7cee64d8be7658399091fab9e851c2e701395622c212e75dc6f9c522a38d3ebf'}

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
    """Four connected canonical magazine solids; well and charging handle stay fixed.
    Each original element appears exactly once, with every field/UV value retained.
    """
    parts={}
    for part in ('body','magazine'):
        model={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        model['elements']=[copy.deepcopy(e) for e in source['elements'] if (e['name'] in MAGAZINE_NAMES)==(part=='magazine')]
        parts[part]=model
    return parts

def pose_display(original,twohand,p,part,grip):
    if part not in ('body','magazine') or grip not in ('native','twohand'):raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8));anchor=sub(MAG_ANCHOR,(8,8,8))
    # Rotate both intact canonical parts around pistol contact. Magazine receives only
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

def reference():
    frames=[]
    for i,(t,observation) in enumerate(zip(REFERENCE_TIMES,OBSERVATIONS),1):
        p=REFERENCE_DIR/f'reference-{i:02}.png'
        with Image.open(p) as im:
            if im.size!=(1280,720):raise ValueError('Reference dimensions: '+str(p))
        frames.append(dict(file=p.name,timestampSeconds=t,sourceFrameIndex=round(t*60),sha256=sha(p.read_bytes()),
            nearestAuthoredProgress=max(0,min(1,(t-77.1)/1.5)),observation=observation))
    return dict(url=REFERENCE_URL,creator='CammyCakes Gaming',title='Halfdan-D | Review | Destiny 2',published='2019-08-06',
        selectedSeconds=[77.1,78.6],identitySeconds=5.,inspectedActualFrames=True,frames=frames,
        sourceVideoSha256=sha((REFERENCE_DIR/'halfdan-reference.mp4').read_bytes()),
        sourceMetadataSha256=sha((REFERENCE_DIR/'halfdan-reference.info.json').read_bytes()),
        timeBasis='Sequential decoded n/60 from first frame; transport first PTS .016667 is not added.',
        referenceConfidence='Same-weapon nameplate and visible magazine withdrawal, clear well, insertion and seating rock. Exact hidden stroke and transforms authored.',
        chargingObservation='No separately measurable charging-handle travel established; canonical Charging_handle stays fixed to receiver.',
        limitations=['Source alternate blue-marked dye and optic establish motion only; canonical local dye/iron sights preserved.',
          'Source magazine/perks/counter do not determine local gameplay or timing.',
          'No bones, hands, hand IK, native success or third-person reload claim.'])

def previews(source,reference,output):
    """Independent NumPy reconstruction of emitted display JSON; offline/no hands."""
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles={part:helper['model_triangles']({part:json.loads(output[A/f'models/{KEY}_{part}.json'])},texture) for part in ('body','magazine')}
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
            for points,uv,tex,normal in triangles[part]:
                flip=np.diag([-1,1,1]) if hand==FP[1] else np.eye(3)
                ps=((np.asarray(points)-8)@flip)*ss@rr.T+tt
                ts.append((ps@flip,uv,tex,flip@rr@flip@normal))
        return ts
    def raster(ts,cam,w,h,extent=None):
        if extent is None:extent=helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]
    cams=([1,.2,-.45],[-1,.35,.6],[.4,.4,1]);labels=('muzzle oblique','receiver oblique','stock oblique')
    sheet=Image.new('RGB',(1500,1640),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),'W180 HALFDAN-D | emitted JSON reconstructed independently | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for row,cam in enumerate(cams):
        groups=[posed(i) for i in (0,8,20)]
        extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,500,300)
        for col,(i,g) in enumerate(zip((0,8,20),groups)):
            sheet.paste(raster(g,cam,500,300,extent),(col*500,55+row*340))
            draw.text((col*500+12,35+row*340),f'p={i/20:.2f} / {labels[row]} / common framing',fill='white')
    draw.text((12,1060),'110 receiver + 4 whole magazine solids = 114 cubes / 0 adapters. Canonical geometry, UV and dye retained.',fill='white')
    for col,cam in enumerate(cams):
        sheet.paste(raster(posed(8,('magazine',)),cam,500,240),(col*500,1110))
        draw.text((col*500+12,1088),'WHOLE MAG: neck + body + floor + heel | '+labels[col],fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(15,grip=grip,hand=hand),[1,.2,-.45],375,240),(col*375,1380))
        draw.text((col*375+8,1357),f'Seat rock p=.75 | {grip} / {hand}',fill='white')
    draw.text((12,1620),'Exact hip endpoints; hidden stroke and seat rock authored. No independent bolt motion. Native framing/sound pending master QA.',fill='white')
    story=Image.new('RGB',(2000,2210),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL CammyCakes / JkSdcwO-MGM | Halfdan-D identity + reload frames paired with AUTHORED sample | OFFLINE / NO HAND IK',fill='white')
    for i,f in enumerate(reference['frames']):
        x=i%5*400;y=42+i//5*530
        im=Image.open(REFERENCE_DIR/f['file']).convert('RGB');im.thumbnail((400,225));story.paste(im,(x,y))
        draw.text((x+8,y+228),f"ACTUAL {f['timestampSeconds']:.2f}s / n={f['sourceFrameIndex']}",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[-1,.35,.6],400,225),(x,y+260))
        draw.text((x+8,y+488),f'AUTHORED p={index/20:.2f} / '+('identity only' if i==0 else 'reload sequence'),fill='white')
    draw.text((12,2180),'Source alternate blue-marked paint/optic NOT transferred. Local canonical dye/iron sights retained. Hidden stroke/pivot authored; charging handle fixed.',fill='white')
    return png(sheet),png(story)

def generate():
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=114:raise ValueError('W129 canonical geometry drift')
    ref=reference()
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w180_halfdan_d.py'),Path('scripts/generate_surface_w123_hammerhead.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W180',weapon='halfdan_d',revision=1,itemModel='destiny:'+KEY,
      ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,
      progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
      sourceElements=114,bodyElements=110,movingElements=4,maxAssembledElements=114,cubeElements=114,triangleAdapterElements=0,elementLimit=1000,addedElements=0,
      sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),sourceRevision='W129 semantic 114-solid model, canonical weapon_surface_w123',geometryAndUVPreserved=True,
      partitionIndices={part:[i for i,e in enumerate(source['elements']) if (e['name'] in MAGAZINE_NAMES)==(part=='magazine')] for part in ('body','magazine')},magazineNames=MAGAZINE_NAMES,
      partitionRationale='All four connected neck/body/floor/heel solids move as one complete magazine. Well, straps, charging handle, grip and guard remain receiver. Every canonical element/field occurs once.',
      authoredHiddenDetails='Hand and screen edge conceal full stroke. Exact downward clearance 6.2 units, lateral/forward .65, grip pivot and angles are authored. Never scale-hide or spin magazine.',
      keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAG_ANCHOR,hipEndpoints=[0,20],
      normalizedPhases={'shallowPresentation':[0,.10],'magazineWithdrawal':[.10,.33],'emptyWellHold':[.33,.53],'replacementAndSeat':[.53,.67],'seatingRock':[.67,.73],'supportRecovery':[.73,.90],'hipReturn':[.90,1]},
      endpointPolicy='Both parts at 0/1 use exact canonical display for each hand/grip. ADS/inspect precedence and nonFP graph exact.',
      reference=ref,motionAuthorship='Halfdan-specific shallow presentation, whole box-mag withdrawal/empty-well pause/replacement, positive seating rock, forward support return. W179 supplies rigid algebra/graph only; independent keys/pivot/partition/phases.',
      sourceChronology=[{'stage':'W129','evidence':'art/weapons/w123/halfdan_d/review.md','role':'Accepted clean 114 solids + 684 explicit face UVs and canonical dye.'},
        {'stage':'W179','evidence':'scripts/generate_reload_w179_null_composure.py','role':'Whole-part parent/display graph and rigid composition conventions only.'},
        {'stage':'W180','evidence':REFERENCE_URL,'role':'Same-weapon motion inspected at 77.1-78.6s; 5s identity; alternate source paint/optic not transferred.'}],
      timingPolicy='Normalized visuals only. Existing magazine33/reload44ticks/rpm400/cadence3ticks/single-shot ammo unchanged; no ammo, clock, audio or runtime edits.',
      rotationConvention='JOML Rx Ry Rz; grip pivot; receiver-local magazine translation; rigid twohand carrier; constant scale. Native ItemTransform applies left mirror.',
      nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
      integration={'requiresMasterRouting':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'halfdan_d',
        'progress':'float1 normalized, flag0 twohand, negative inactive; ADS/inspect guard first; nonFP canonical. Master owns admission/routing/lifecycle.'},
      nativeQueue=['Both FP contexts x both grips: shallow presentation; whole-mag withdrawal; empty well; insertion; seat rock; exact hip recovery. Watch well/guard and near-plane clearance.',
        'ADS/inspect precedence; all canonical nonFP contexts and observer; no new third-person reload claim.',
        'Completion/cancel/swap/equip/death/disconnect: master routing restores canonical state; unchanged 33 rounds/44 ticks and actual sound listening.',
        'Master single native session: briefly observe 10-20 held displays. Native hand framing, performance and audio unverified.'],
      canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact 90')
    return output


def main():
    global REFERENCE_DIR
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--reference-dir',type=Path,default=REFERENCE_DIR);args=ap.parse_args()
    REFERENCE_DIR=args.reference_dir;output=generate()
    scope=Path('/private/tmp/w180-manifest.json')
    if scope.exists():
        owned=set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w180-halfdan-d'))
        if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 87 pack assets; 110+4=114 assembled elements; native pending')
if __name__=='__main__':main()
