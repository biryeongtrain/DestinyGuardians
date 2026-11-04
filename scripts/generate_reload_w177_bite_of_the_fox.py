#!/usr/bin/env python3
"""Bite of the Fox: existing W123 solids and UV, bespoke long-rifle reload.

Nexas Gaming moebSjSRyoE, identity32s / reload158.8..161.4s.
W176 rigid display composition/graph pattern only; no pistol motion/topology.
No hands, extracted bones, independent bolt or native/third-person reload claim.
"""
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
from PIL import Image, ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w177/bite_of_the_fox')
KEY='weapon_reload_w177_bite_of_the_fox/bite_of_the_fox'
SOURCE=A/'models/weapon_surface_w123/bite_of_the_fox.json'
TWOHAND=A/'models/weapon/sniper_rifle/bite_of_the_fox_twohand.json'
ITEM=A/'items/weapon/bite_of_the_fox.json'
TEXTURE=A/'textures/item/weapon/w123/bite_of_the_fox.png'
FP=('firstperson_righthand','firstperson_lefthand')
MOVING=(51,52,53)
NAMES=('magazine','magazine_floor','magazine_brass_catch')
# Magazine group is forward of guard/grip, never grip-fed like a sidearm.
GRIP=(8.,8.03,8.35)
MAG_ANCHOR=(8.,8.31,4.875)
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0)),
 (.08,(9,-3,-10),(.05,.06,.05),(0,0,0)),
 (.16,(19,-6,-25),(.14,.18,.12),(0,-.2,0)),
 (.24,(22,-8,-32),(.18,.22,.15),(-.25,-2.4,.2)),
 (.32,(25,-8,-38),(.18,.25,.16),(-.65,-3.6,.55)),
 (.40,(26,-7,-36),(.12,.25,.12),(-.3,-1.6,.2)),
 (.46,(24,-6,-33),(.08,.20,.10),(0,0,0)),
 (.54,(16,2,-15),(-.05,.08,.08),(0,0,0)),
 (.62,(2,12,22),(-.18,-.10,.05),(0,0,0)),
 (.72,(8,10,20),(-.12,-.08,.10),(0,0,0)),
 (.80,(14,8,12),(-.06,.05,.10),(0,0,0)),
 (.88,(-5,5,5),(-.02,-.20,.05),(0,0,0)),
 (.95,(-2,2,2),(0,-.08,.02),(0,0,0)),
 (1.,(0,0,0),(0,0,0),(0,0,0)),
)
SOURCE_SHA256='f80083332b3e0ee8903bc825287a254cd4cead6c9d8605896f51ce580b292c2a'
PINS={'src/main/resources/assets/destiny/models/weapon/sniper_rifle/bite_of_the_fox.json': '00dce3691476617a9a0e9d98e7c18cc486a0c80f637a8ec6ad101cc76a261154', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/bite_of_the_fox_twohand.json': '217e9042fe3ccfc1b281d7d522a94b4535f58c500ed04f336371010dfb496b11', 'src/main/resources/assets/destiny/items/weapon/bite_of_the_fox.json': '620d970a89d977772f808425fff90db3949be88cb11007e7fa5dea9215e6bb54', 'src/main/resources/assets/destiny/textures/item/weapon/w123/bite_of_the_fox.png': '747f936b662b4c4e8857ee57142d35936a21df1dd6cd1dd19c7b66223836279b', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b'}

def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b): return hashlib.sha256(b).hexdigest()
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

def pose_display(original,twohand,p,part,grip):
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8))
    anchor=sub(MAG_ANCHOR,(8,8,8))
    # Place the unchanged magazine anchor at its body-carried position plus
    # source-local withdrawal, then subtract its rotated child-space anchor.
    # This is translation only; no recentering or extra magazine spin.
    local=(sub(add(h,vec(body,add(sub(anchor,h),offset))),vec(body,anchor))
           if part=='magazine' else sub(h,vec(body,h)))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
        if twohand[context]['scale'] != s: raise ValueError('Grip scale mismatch')
        if len(set(s))!=1: raise ValueError('Rigid part motion requires uniform first-person scale')
        rotation=mul(base,body)
        position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
        if grip=='twohand':
            comp=mul(xyz(twohand[context]['rotation']),transpose(base))
            carrier=sub(twohand[context]['translation'],vec(comp,idle['translation']))
            position=add(vec(comp,position),carrier);rotation=mul(comp,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def expected_output_paths():
    paths={A/f'models/{KEY}_{part}.json' for part in ('body','magazine')}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(21) for part in ('body','magazine') for grip in ('native','twohand'))
    return paths|{A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'}

def previews(source,reference,output):
    """Independent child-display reconstruction; offline views, not native QA.

    Uses emitted children and explicit axis matrices instead of pose_display's
    pivot/offset derivation. Existing inert raster helper supplies face UVs.
    """
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles={}
    for part in ('body','magazine'):
        parent=json.loads(output[A/f'models/{KEY}_{part}.json'])
        # Raster helper expects XYZ element rotation. Convert a render-only copy;
        # emitted axis/angle geometry and face UV remain byte-value exact.
        for element in parent['elements']:
            r=element.get('rotation',{})
            if 'axis' in r:
                element['rotation']={'origin':r['origin'],r['axis']:r['angle']}
        triangles[part]=helper['model_triangles']({part:parent},texture)
    def rotation(a):
        x,y,z=np.radians(a)
        rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
        ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
        rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        return rx@ry@rz
    def posed(i,parts=('body','magazine')):
        ts=[]
        for part in parts:
            disp=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_native.json'])['display']['firstperson_righthand']
            rr=rotation(disp['rotation']);ss=np.array(disp['scale']);tt=np.array(disp['translation'])
            for points,uv,tex,normal in triangles[part]:
                ts.append(((np.asarray(points)-8)*ss@rr.T+tt,uv,tex,rr@normal))
        return ts
    def raster(ts,cam,w,h,extent=None):
        if extent is None: extent=helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]
    sheet=Image.new('RGB',(1440,1410),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),'W177 BITE OF THE FOX | independent reconstruction of emitted native display JSON | OFFLINE, no hands / IK',fill='white')
    for row,cam in enumerate(([1,.2,-.45],[-1,.35,.6],[.4,.4,1])):
        ts=[posed(i) for i in (0,6,20)]
        extent=helper['frame'](np.concatenate([t[0] for group in ts for t in group]),cam,480,300)
        for col,(i,group) in enumerate(zip((0,6,20),ts)):
            sheet.paste(raster(group,cam,480,300,extent),(col*480,50+row*330))
            draw.text((col*480+12,35+row*330),f'p={i/20:.2f} / '+('muzzle oblique','rear oblique','grip-facing oblique')[row],fill='white')
    draw.text((12,1035),'109 fixed + 3 existing magazine solids = 112. All canonical elements / face UV exact. No added hidden geometry. Common framing per row.',fill='white')
    closeup=posed(6,('magazine',))
    for col,cam in enumerate(([1,.2,-.45],[-1,.35,.6],[.4,.4,1])):
        sheet.paste(raster(closeup,cam,480,295),(col*480,1090))
        draw.text((col*480+12,1073),'p=0.30 magazine close-up | existing box + connected floorplate + catch',fill='white')
    draw.text((12,1390),'Existing magazine51 / floor52 / catch53 stay rigidly connected. Fixed bolt49/50; action gesture via rifle roll only. Native review pending.',fill='white')
    story=Image.new('RGB',(1600,1620),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL moebSjSRyoE gameplay vs AUTHORED Bite of the Fox | source seconds / nearest authored sample | NO native or bone claim',fill='white')
    start,end=reference['selectedSeconds']
    for i,f in enumerate(reference['frames']):
        x=i%4*400;y=40+i//4*520
        im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));story.paste(im,(x,y))
        p=(f['timestampSeconds']-start)/(end-start);index=0 if i==0 else max(0,min(20,round(p*20)))
        draw.text((x+8,y+228),f"ACTUAL {f['timestampSeconds']:.6f}s / frame {f['sourceFrameIndex']}",fill='white')
        story.paste(raster(posed(index),[1,.2,.4],400,225),(x,y+260))
        draw.text((x+8,y+488),('IDENTITY ONLY / idle' if i==0 else f'AUTHORED p={index/20:.2f}')+' | '+f['phase'],fill='white')
    draw.text((12,1600),'Original frame pixels above; authored offline orthographic render below. Hand occlusion and HUD overlay limit exact magazine-path inference.',fill='white')
    return png(sheet),png(story)


def generate():
    source=json.loads((ROOT/SOURCE).read_bytes())
    twohand=json.loads((ROOT/TWOHAND).read_bytes())['display']
    canonical=json.loads((ROOT/ITEM).read_bytes())
    if sha((ROOT/SOURCE).read_bytes())!=SOURCE_SHA256: raise ValueError('Canonical clean source drift')
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest: raise ValueError('Canonical input drift: '+path)
    if len(source['elements'])!=112 or tuple(source['elements'][i]['name'] for i in MOVING)!=NAMES:
        raise ValueError('Semantic partition drift')
    design_path=Path('art/weapons/w123/bite_of_the_fox/design.json')
    design=json.loads((ROOT/design_path).read_bytes())
    if tuple(p['geometry']['name'] for p in design['parts']['full'] if p['group']=='magazine')!=NAMES:
        raise ValueError('Design magazine group drift')
    ref=json.loads((ROOT/ART/'motion-reference.json').read_bytes())
    if not ref['inspectedActualFrames'] or len(ref['frames'])!=12: raise ValueError('Actual reference missing')
    for f in ref['frames']:
        if sha((ROOT/f['path']).read_bytes())!=f['sha256']: raise ValueError('Reference hash drift')
    output={}
    def emit(path,value): output[path]=encode(value)
    for part in ('body','magazine'):
        geo={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        geo['elements']=[copy.deepcopy(e) for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='magazine')]
        emit(A/f'models/{KEY}_{part}.json',geo)
    entries=[]
    for i in range(21):
        for part in ('body','magazine'):
            for grip in ('native','twohand'):
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],twohand,i/20,part,grip)))
        def composite(grip): return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in ('body','magazine')])
        entries.append(dict(threshold=i/20,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    wrapper=copy.deepcopy(canonical)
    wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=copy.deepcopy(canonical['model'])))],fallback=copy.deepcopy(canonical['model']))
    emit(A/f'items/{KEY}.json',wrapper)
    comparison,storyboard=previews(source,ref,output)
    output[ART/'comparison.png']=comparison;output[ART/'storyboard.png']=storyboard
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,design_path,ART/'motion-reference.json',Path('scripts/generate_reload_w177_bite_of_the_fox.py'),Path('scripts/generate_surface_w123_hammerhead.py')]
    emit(ART/'manifest.json',dict(stage='W177',weapon='bite_of_the_fox',itemModel='destiny:'+KEY,
        ownedFiles=106,generatedFiles=90,packFiles=87,frames=21,staticParts=2,parentDisplayChildren=84,
        progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=112,bodyElements=109,magazineElements=3,movingElements=3,maxAssembledElements=112,elementLimit=1000,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=SOURCE_SHA256,geometryAndUVPreserved=True,
        movingIndices=list(MOVING),movingNames=list(NAMES),addedElements=0,authoredHiddenDetails=[],
        partitionRationale='Exact existing W123 magazine group: box51 + overlapping floor52 + brass catch53. Three connected solid volumes, no flat tile or new payload. Guard57..60, grip54..56, bolt49/50, receiver46..48 and scope/stock stay fixed in body. All source element values and UV preserved.',
        sourceElementsAndUVSha256=sha(encode(source['elements'])),
        partElementsAndUVSha256={part:sha(encode([e for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='magazine')])) for part in ('body','magazine')},
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAG_ANCHOR,hipEndpoints=[0,20],
        normalizedPhases={'rifleRaiseAndCant':[0,.16],'underReceiverWithdrawal':[.16,.32],'replacementApproach':[.32,.46],'reseat':[.46,.54],'receiverGestureProxy':[.54,.80],'recover':[.80,1]},
        reference=ref['url'],sourceObservedSeconds=ref['selectedSeconds'],actualReferenceFrames=12,identityFrames=1,reloadFrames=11,
        referenceConfidence=ref['referenceConfidence'],motionAuthorship='Bite-specific long-rifle lift/cant, forward receiver-well box exchange, opposite receiver-side roll gesture, then lower to hip. Curves, grip pivot and travel authored from Nexas actual footage; only graph and rigid transform algebra follow W176. No pistol curve or grip-fed partition.',
        timingPolicy='Normalized visual phase order only; source video perks and seconds do not override existing catalog 3 rounds / 67 reload ticks / 72rpm.',
        rotationConvention='Rx Ry Rz child display; rotate about source grip, apply scale once, source-local magazine translation, rigid carrier for twohand. Endpoints exact existing displays.',
        fallback='Exact canonical item graph for non-FP and inactive negative progress; canonical ADS/inspect remain reachable through fallback.',
        comparisonMethod='Offline independent reconstruction from emitted child transforms. Three oblique cameras with common row framing at start/extraction/end; three magazine closeups; twelve actual unmodified reference frames paired with nearest authored sample (identity paired with idle).',
        nativeGameplayVerified=False,handIK=False,extractedAnimation=False,extractedBones=False,thirdPersonReloadClaim=False,mechanicsOrAudioChanged=False,
        integration={'requiresNewMasterRoute':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'masterRoute':21,'requiredMasterModel':'destiny:'+KEY,'catalogId':'bite_of_the_fox','liveOwnerOnly':'Master publishes float1 only for active local owner FP reload. Negative inactive progress and non-FP use canonical graph; clear on completion/cancel/swap/equip/death/disconnect.','preserve':'Canonical models/UV/paint/ADS/inspect, ammo3, reload67ticks, 72rpm, catalog/perks/audio unchanged.'},
        nativeQueue=['Both first-person hands and both grips: long-rifle framing, clear box extraction/reseat and exact hip recovery','ADS/inspect entry/exit; cancel, complete, equip/swap, death/disconnect progress restore; owner-only route21 publication','Third-person observer, GUI/ground/fixed/head must remain canonical; no third-person reload claim','Brief 10-20 displayed weapons for obvious defects; native sound/performance not evaluated offline'],
        limitations=ref['limitations'],canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths(): raise ValueError('Generated path contract drift')
    return output

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    output=generate()
    manifest=Path('/private/tmp/w177-manifest.json')
    if manifest.exists():
        owned=set(next(f['owned_paths'] for f in json.loads(manifest.read_bytes())['features'] if f['name']=='w177-bite-of-the-fox-reload'))
        if not {str(p) for p in output}<=owned: raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        target=ROOT/p
        if args.verify:
            if not target.is_file() or target.read_bytes()!=b: raise SystemExit('Asset differs: '+str(p))
        else:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+' 90 deterministic outputs; 87 pack files; 109 body + 3 magazine = 112 exact canonical elements; no added hidden detail')
if __name__=='__main__':main()
