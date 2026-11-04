#!/usr/bin/env python3
"""Null Composure-specific FP energy-cell reload from inspected same-weapon gameplay.
Canonical W144 solids/UV/paint and display endpoints preserved; no runtime edits.
W178 supplies only rigid composition algebra/graph conventions, not motion keys.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w179/null_composure')
KEY='weapon_reload_w179_null_composure/null_composure'
SOURCE=A/'models/weapon_surface_w123/null_composure.json'
TWOHAND=A/'models/weapon/fusion_rifle/null_composure_twohand.json'
ITEM=A/'items/weapon/null_composure.json'
TEXTURE=A/'textures/item/weapon/w123/null_composure.png'
FP=('firstperson_righthand','firstperson_lefthand')
CELL_NAMES=('Battery_keel_solid','Battery_blue_spine','Battery_heel')
GRIP=(8.,8.4,5.4)
MAG_ANCHOR=(8.,7.48,.27)
# Same-weapon pixels: steep upright presentation, lower battery reach, then top
# sweep before lowering. Exact hidden cell stroke/pivot/angles are authored.
# This compact source-local stroke is independent of W178's long cuff-cell path.
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0)),
 (.11,(78,5,14),(.35,-.45,.35),(0,0,0)),
 (.22,(84,9,18),(.50,-.35,.45),(0,-.6,-.35)),
 (.34,(80,11,21),(.55,-.35,.50),(-.3,-3.2,-.4)),
 (.45,(81,11,20),(.55,-.35,.50),(-.3,-3.2,-.4)),
 (.56,(82,10,17),(.50,-.30,.45),(-.1,-1.25,-.35)),
 (.64,(80,7,14),(.40,-.30,.35),(0,0,0)),
 (.73,(68,3,9),(.30,-.25,.25),(0,0,0)),
 (.80,(71,3,6),(.25,-.20,.20),(0,0,0)),
 (.90,(34,1,2),(.10,-.10,.10),(0,0,0)),
 (1.,(0,0,0),(0,0,0),(0,0,0)),
)
REFERENCE_URL='https://www.youtube.com/watch?v=FdLSPBirfps'
REFERENCE_DIR=Path('/private/tmp/w179-null-composure-report')
REFERENCE_TIMES=(20.,136.8,137.,137.2,137.4,137.6,137.8,138.,138.2,138.4,138.6,138.8)
OBSERVATIONS=(
 'Readable NULL COMPOSURE nameplate; silver shroud, blue capacitor, gold crest and open lower frame match canonical identity.',
 'Hip view before reload; same optic, silver shroud and blue breech.',
 'Support side starts to rise; both hands still at held weapon.',
 'Muzzle steeply upright on right; left hand reaches the lower perforated battery face.',
 'Weapon turns to expose the lower battery; support hand leaves frame; exact cell travel occluded.',
 'Upright hold with perforated battery face still visible; no recovered cell trajectory.',
 'Upright hold continues; receiver remains high, support hand offscreen.',
 'Support hand returns to lower battery face; ammo counter changes in source only.',
 'Support hand leaves the battery area while receiver starts slight lowering.',
 'Support hand sweeps above receiver/optic; no separately moving top geometry is claimed.',
 'Support hand withdraws and barrel lowers toward hip.',
 'Hip silhouette recovered. Exact canonical final pose is an authored endpoint.'
)
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/null_composure.json': '37a221b93407ff720959b59c7192135cff81f6658743a92892204916e00d0c5f', 'src/main/resources/assets/destiny/textures/item/weapon/w123/null_composure.png': '0a37c3c55da27f611bc6129d1995e892656f3e66bc32594f7c1af9444a5db823', 'src/main/resources/assets/destiny/items/weapon/null_composure.json': 'dc07bbf4c78835f030430fd3e3335d26e3b154c409b9b5c38803accbe2e11e62', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/weapon_surface_w123/manifest.json': '4972bd808e5150d09e8f55e2c663b45f88ad8e660300310c5ecc04f4f672db6b', 'src/main/resources/assets/destiny/items/weapon_sight_w153/null_composure.json': 'b191c508ac6cec7c63d50736384dc109faca0f6615fde22227074412e1715922', 'src/main/resources/assets/destiny/items/weapon_aim_w70/null_composure.json': 'e1cb1cae46bef879e55f2010eef551784bacb98f9b673e9d8db7fe3f3e4be0b3', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure.json': 'e5e5ead55de6a921d9bb452c9ea460c573f36150c625a526df7db10d04c5bc75', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure_ads.json': '336241a84c9037af386724ce0c10be1e4be25bf0a7e5a8ccff610ceb7de29dc7', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure_ads_twohand.json': 'a1e7aa04b9d88e516d1153b7f90bfb85d5bad61e27a7419b922d332efec24ed2', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure_inspect.json': '6618d1a786c6265e05e5c9e5052d72da6eba90a40e444ca4bcf06dc5bc1a3abf', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure_inspect_twohand.json': '50412d28adb055cb68865b37b4229485348842186dad000197e5fec1542e5b65', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/null_composure_twohand.json': '7479921650278a6901ed39bf72a41c16de75b8fdb3021964dac966b2539c9a96'}

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
    """Three connected canonical battery solids; diagonal web and frame stay fixed.
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

def reference():
    frames=[]
    for i,(t,observation) in enumerate(zip(REFERENCE_TIMES,OBSERVATIONS),1):
        p=REFERENCE_DIR/f'reference-{i:02}.png'
        if not p.is_file():raise ValueError('Decode reference frames first; see SOURCE.md: '+str(p))
        with Image.open(p) as im:
            if im.size!=(1280,720):raise ValueError('Reference dimensions: '+str(p))
        frames.append(dict(file=p.name,timestampSeconds=t,sourceFrameIndex=round(t*60),
            sha256=sha(p.read_bytes()),nearestAuthoredProgress=max(0,min(1,(t-137)/1.8)),observation=observation))
    return dict(url=REFERENCE_URL,creator='Datto',title='Destiny 2: Null Composure is LITERALLY A Fusion Rifle (Season 14 Pursuit Weapon)',
        selectedSeconds=[137,138.8],identitySeconds=20,inspectedActualFrames=True,frames=frames,
        sourceVideoSha256=sha((REFERENCE_DIR/'null-composure-hls.mp4').read_bytes()),
        sourceMetadataSha256=sha((REFERENCE_DIR/'null-composure-hls.info.json').read_bytes()),
        timeBasis='60fps decoded frame index / 60 relative to first frame; MPEG-TS starts at PTS .016667 seconds.',
        referenceConfidence='Strong weapon identity and visible receiver/hand sequence; exact battery travel, pivot and angles occluded and authored.',
        limitations=['Normalized presentation only; source ammo/perks do not set local gameplay.',
            'Battery housing remains visible in footage: modest cell clearance is authored, not a measured full-magazine ejection.',
            'No extracted bones, exact pose reconstruction, hands, hand IK or native verification.'])

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
    draw.text((12,10),'W179 NULL COMPOSURE | emitted JSON reconstructed independently | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for row,cam in enumerate(cams):
        groups=[posed(i) for i in (0,7,20)]
        extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,500,300)
        for col,(i,g) in enumerate(zip((0,7,20),groups)):
            sheet.paste(raster(g,cam,500,300,extent),(col*500,55+row*340))
            draw.text((col*500+12,35+row*340),f'p={i/20:.2f} / {labels[row]} / common framing',fill='white')
    draw.text((12,1060),'88 receiver + 3 existing battery solids = 91 output cubes / 0 triangle adapters. Geometry, face UV and paint intact.',fill='white')
    for col,cam in enumerate(cams):
        sheet.paste(raster(posed(7,('magazine',)),cam,500,240),(col*500,1110))
        draw.text((col*500+12,1088),'CELL: keel + blue spine + heel | '+labels[col],fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]))):
        sheet.paste(raster(posed(15,grip=grip,hand=hand),[1,.2,-.45],500,240),(col*500,1380))
        draw.text((col*500+12,1357),f'Top-sweep rock p=.75 | {grip} / {hand}',fill='white')
    draw.text((12,1620),'Exact hip endpoints; modest hidden stroke and top-sweep rock authored. Native hand framing/clearance/sound remain master QA.',fill='white')
    story=Image.new('RGB',(1600,1660),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL Datto / FdLSPBirfps | nameplate + 11 same-weapon frames paired with nearest AUTHORED sample | OFFLINE / NO HAND IK',fill='white')
    for i,f in enumerate(reference['frames']):
        x=i%4*400;y=42+i//4*530
        im=Image.open(REFERENCE_DIR/f['file']).convert('RGB');im.thumbnail((400,225));story.paste(im,(x,y))
        draw.text((x+8,y+228),f"ACTUAL {f['timestampSeconds']:.2f}s / n={f['sourceFrameIndex']}",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[-1,.35,.6],400,225),(x,y+260))
        draw.text((x+8,y+488),f'AUTHORED p={index/20:.2f} / '+('identity' if i==0 else 'reload sequence'),fill='white')
    draw.text((12,1640),'Pixels show receiver and hand sequence; exact hidden cell stroke/angles/pivot are authored. No native or third-person reload claim.',fill='white')
    return png(sheet),png(story)

def generate():
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=91:raise ValueError('W144 canonical geometry drift')
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w179_null_composure.py'),Path('scripts/generate_surface_w123_hammerhead.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W179',weapon='null_composure',revision=1,itemModel='destiny:'+KEY,
      ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,
      progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
      sourceElements=91,bodyElements=88,movingElements=3,maxAssembledElements=91,cubeElements=91,triangleAdapterElements=0,elementLimit=1000,addedElements=0,
      sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),sourceRevision='W144 semantic solid model selected by weapon_surface_w123 manifest',geometryAndUVPreserved=True,
      partitionIndices={part:[i for i,e in enumerate(source['elements']) if (e['name'] in CELL_NAMES)==(part=='magazine')] for part in ('body','magazine')},cellNames=CELL_NAMES,
      partitionRationale='Existing connected battery keel, blue spine and heel move together. Forward diagonal web, upper fill, open frame brace and front blue capacitor stay on receiver. All canonical fields occur once.',
      authoredHiddenDetails='Visible housing and hand conceal exact energy-cell extraction. Modest downward stroke and source-local forward clearance, grip pivot and angles are authored. Battery is never shrunk, spun or hidden.',
      keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAG_ANCHOR,hipEndpoints=[0,20],
      normalizedPhases={'uprightPresentation':[0,.11],'batteryReachAndWithdrawal':[.11,.34],'clearHold':[.34,.45],'replacementAndSeat':[.45,.64],'topHandSweepRock':[.64,.80],'hipReturn':[.80,1]},
      endpointPolicy='Both parts at 0/1 use exact canonical display for each hand/grip. ADS/inspect precedence and nonFP graph exact.',
      reference=ref,motionAuthorship='Null Composure upright presentation, modest lower battery exchange, then top-hand sweep rock and hip recovery. W178 reused only rigid composition algebra/graph conventions; independent keys, pivot, partition, stroke and phases.',
      timingPolicy='Normalized visuals only. Existing magazine6/reload41ticks/charge533ms/burst9/cadence14.333333333333 unchanged; no ammo, clock, audio or runtime changes.',
      rotationConvention='JOML Rx Ry Rz; rotate about grip contact, translate battery in receiver local axes; rigid twohand carrier. Constant scale. Left mirror applied by native ItemTransform.',
      nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
      integration={'requiresMasterRouting':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'null_composure','progress':'float1 normalized, flag0 twohand, negative inactive; ADS/inspect guards precede progress, nonFP canonical. Routing/lifecycle tests belong to master.'},
      nativeQueue=['Both FP contexts and both grips: upright framing, short battery clearance/reseat, top sweep rock and exact hip recovery.',
        'ADS/inspect plus canonical nonFP observer/GUI/ground/fixed/head; completion/cancel/swap/equip/death/disconnect restoration controlled by master.',
        'Master single native session: listen to unchanged audio and briefly check 10-20 held displays for visible defects. No native success claimed.'],
      canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact 90')
    return output

def main():
    global REFERENCE_DIR
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--reference-dir',type=Path,default=REFERENCE_DIR);args=ap.parse_args();
    REFERENCE_DIR=args.reference_dir;output=generate()
    owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w179-manifest.json').read_bytes())['features'] if f['name']=='w179-null-composure'))
    if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 87 pack assets; 88+3=91 assembled elements; native pending')
if __name__=='__main__':main()
