#!/usr/bin/env python3
"""Mindbender W179: authored one-shell initial / held loop / cosmetic return.

W147's 104 canonical solids, UV, texture and HIP transforms are unchanged.
Rigid matrix composition follows W178; anchors, curves and shell are Mindbender
specific. Actual gameplay observations are in SOURCE.md. No hand/bone extraction.
Reference downloads are external; --reference-dir supplies retained PNG evidence.
"""
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w179/mindbender_s_ambition_adept')
KEY = 'weapon_insert_w179_mindbender_s_ambition_adept/mindbender_s_ambition_adept'
SOURCE = A/'models/weapon_surface_w123/mindbender_s_ambition_adept.json'
TWOHAND = A/'models/weapon/shotgun/mindbender_s_ambition_adept_twohand.json'
ITEM = A/'items/weapon/mindbender_s_ambition_adept.json'
TEXTURE = A/'textures/item/weapon/w123/mindbender_s_ambition_adept.png'
SELF = Path('scripts/generate_insert_w179_mindbender_s_ambition_adept.py')
FP = ('firstperson_righthand', 'firstperson_lefthand')
PHASES = ('initial', 'loop', 'return')
PARTS = ('body', 'shell')
GRIPS = ('native', 'twohand')
GRIP = (8., 8.70, 8.18)
# Source Z runs from the stock (+Z) toward the muzzle (-Z). Cartridge is
# parallel to that axis: crimp at -Z, metal head/rim at +Z. Never vertical.
SHELL_ANCHOR = (8., 10.04, 4.45)
HOLD = ((22., -11., -36.), (-.24, .44, .16))
APPROACH = (1.10, -1.65, .45)
CONTACT = (0., -.05, 0.)
# Fully inside unmodified action_solid, forward of loading_tray and guard.
SEATED = (0., .96, -1.90)
# Normalized phase, local body XYZ, presentation shift, local cartridge offset.
# The receiver raises ONCE. Repeated inserts retain the large held silhouette.
KEYS = {
 'initial': (
  (0., (0,0,0), (0,0,0), APPROACH),
  (.14, (9,-4,-17), (-.10,.19,.06), APPROACH),
  (.30, *HOLD, APPROACH),
  (.38, *HOLD, APPROACH),
  (.59, *HOLD, (.40,-.72,.20)),
  (.72, (22.45,-11.2,-36.65), (-.23,.47,.15), CONTACT),
  (.90, (22.70,-11.3,-36.4), (-.24,.49,.14), SEATED),
  (1., *HOLD, SEATED)),
 'loop': (
  (0., *HOLD, APPROACH),
  (.10, *HOLD, APPROACH),
  (.38, *HOLD, (.40,-.72,.20)),
  (.57, (22.45,-11.2,-36.65), (-.23,.47,.15), CONTACT),
  (.84, (22.70,-11.3,-36.4), (-.24,.49,.14), SEATED),
  (1., *HOLD, SEATED)),
 'return': (
  (0., *HOLD, SEATED),
  (.28, (17,-8,-28), (-.19,.34,.12), SEATED),
  (.72, (4,-2,-7), (-.04,.06,.02), SEATED),
  (1., (0,0,0), (0,0,0), SEATED))
}
VISIBLE = {'initial': (.38,.90), 'loop': (.10,.84)}
PINS = {'src/main/resources/assets/destiny/models/weapon_surface_w123/mindbender_s_ambition_adept.json': '2c972e49103f55ce199d21b90c74f2b934ce7376f9066c7ee4eaf00fb8a65112', 'src/main/resources/assets/destiny/models/weapon/shotgun/mindbender_s_ambition_adept.json': '3ee94558c88b7a1a072eb2adfb77f89e207834dca46a63d537cfebcd5ca13375', 'src/main/resources/assets/destiny/models/weapon/shotgun/mindbender_s_ambition_adept_twohand.json': '5bad9cfe918e3e59ea65f811a003979f4ead89e788e911f758026b4f8b0e5873', 'src/main/resources/assets/destiny/items/weapon/mindbender_s_ambition_adept.json': 'c41d916c7210ac84ba74dcbecbc2e55a95197883ec9f45ea99f72e2775ce1130', 'src/main/resources/assets/destiny/textures/item/weapon/w123/mindbender_s_ambition_adept.png': '98036d622834bb5ecfb2ab823cba4e116136516facb3e9f8ac9bea326a4f16db', 'src/main/resources/weapon_surface_w123/manifest.json': '4972bd808e5150d09e8f55e2c663b45f88ad8e660300310c5ecc04f4f672db6b', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b'}

def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def png(im):
 out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def mul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def vec(m,v):return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]
def transpose(m):return list(map(list,zip(*m)))
def xyz(angles):
 x,y,z=map(math.radians,angles);a,b,c,d,e,f=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
 return [[c*e,-c*f,d],[b*d*e+a*f,-b*d*f+a*e,-b*c],[-a*d*e+b*f,a*d*f+b*e,a*c]]
def euler(m):
 b=math.asin(max(-1.,min(1.,m[0][2])))
 a,c=(math.atan2(-m[1][2],m[2][2]),math.atan2(-m[0][1],m[0][0])) if abs(math.cos(b))>1e-8 else (math.atan2(m[2][1],m[1][1]),0)
 return [round(math.degrees(v),9) for v in (a,b,c)]
def sample(phase,p):
 if phase not in KEYS or not math.isfinite(p) or not 0<=p<=1:raise ValueError((phase,p))
 for a,b in zip(KEYS[phase],KEYS[phase][1:]):
  if p<=b[0]:
   t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
   return tuple([a[k][i]+(b[k][i]-a[k][i])*t for i in range(3)] for k in (1,2,3))
 raise ValueError((phase,p))
def shell_visible(phase,p):
 return phase in VISIBLE and VISIBLE[phase][0]<=p<VISIBLE[phase][1]

def pose_display(original,twohand,phase,p,part,grip):
 accepted=original if grip=='native' else twohand
 display=copy.deepcopy(accepted)
 if part=='body' and ((phase=='initial' and p==0) or (phase=='return' and p==1)):return display
 angles,shift,offset=sample(phase,p)
 body=xyz(angles);h=sub(GRIP,(8,8,8));anchor=sub(SHELL_ANCHOR,(8,8,8))
 visible=part=='body' or shell_visible(phase,p)
 # Source-local shell anchor, carried by same rigid receiver rotation.
 # Compensate rotation and visibility scale around the ANCHOR, not item origin.
 desired=add(h,vec(body,add(sub(anchor,h),offset)))
 local=sub(h,vec(body,h)) if part=='body' else sub(desired,vec(body,anchor if visible else (0,0,0)))
 for context in FP:
  idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
  if twohand[context]['scale']!=s or len(set(s))!=1:raise ValueError('Uniform equal first-person grip scale required')
  rotation=mul(base,body)
  position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
  if grip=='twohand':
   carrier=mul(xyz(twohand[context]['rotation']),transpose(base))
   position=add(vec(carrier,position),sub(twohand[context]['translation'],vec(carrier,idle['translation'])))
   rotation=mul(carrier,rotation)
  display[context]['rotation']=euler(rotation)
  display[context]['translation']=[round(v,9) for v in position]
  if not visible:display[context]['scale']=[0,0,0]
 if part=='shell':
  for ctx in set(display)-set(FP):display[ctx]['scale']=[0,0,0]
 return display


def shell_geometry(source):
    """One octagonal cartridge, twelve connected solids, no new atlas.

    Longitudinal Z case; head/rim at the rear (+Z), crimp end toward muzzle.
    Four intersecting rectangular solids per section fill the octagonal section.
    Reuse clean existing graphite tray and silver collar texels, no rune decals.
    """
    elements = []
    for name, radius, z0, z1, paint in (
        ('case', .25, -.77, .49, 'loading_tray'),
        ('head', .26, .46, .70, 'barrel_silver_collar_0'),
        ('rim', .29, .67, .77, 'barrel_silver_collar_0')):
        donor = next(e for e in source['elements'] if e['name'] == paint)
        uv = donor['faces']['east']['uv']
        u, v = (uv[0]+uv[2])/2, (uv[1]+uv[3])/2
        for angle in (0,45,-45,90):
            width = 2*radius*math.tan(math.pi/8)
            sizes = [width, 2*radius]
            if angle == 90:
                sizes.reverse()
            center = list(SHELL_ANCHOR)
            center[2] += (z0+z1)/2
            faces = copy.deepcopy(donor['faces'])
            for face in faces.values():
                face['uv'] = [u,v,u,v]
            element = dict(name=f'insert_{name}_{angle}', **{
                'from': [center[0]-sizes[0]/2,center[1]-sizes[1]/2,SHELL_ANCHOR[2]+z0],
                'to': [center[0]+sizes[0]/2,center[1]+sizes[1]/2,SHELL_ANCHOR[2]+z1]}, faces=faces)
            if angle in (45,-45):
                element['rotation'] = dict(origin=center,axis='z',angle=angle)
            elements.append(element)
    return dict(credit='W179 authored model-only cartridge; longitudinal -Z crimp / +Z head. Canonical graphite tray / silver collar texels.',
                textures=copy.deepcopy(source['textures']), elements=elements)


def expected_output_paths():
    return ({A/f'models/{KEY}_{part}.json' for part in PARTS} |
        {A/f'models/{KEY}_{phase}_{i:02}_{part}_{grip}.json'
         for phase in PHASES for i in range(21) for part in PARTS for grip in GRIPS} |
        {A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'})


def previews(output, reference_dir, reference):
    """Offline raster of emitted JSON, independent rotation/element reconstruction.

    Reuses only inert W123 raster functions. No motion sampler is called here.
    Native player hands, projection and runtime routing require master's session.
    """
    helper = runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    tex = Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles = {}
    for part in PARTS:
        parent = json.loads(output[A/f'models/{KEY}_{part}.json'])
        for element in parent['elements']:
            rotation = element.get('rotation',{})
            if 'axis' in rotation:
                element['rotation'] = {'origin':rotation['origin'],rotation['axis']:rotation['angle']}
        triangles[part] = helper['model_triangles']({part:parent},tex)

    def rotation(angles):
        x,y,z = np.radians(angles)
        rx = np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
        ry = np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
        rz = np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        return rx@ry@rz

    def posed(phase,i,parts=PARTS,grip='native',hand=FP[0]):
        result = []
        for part in parts:
            display = json.loads(output[A/f'models/{KEY}_{phase}_{i:02}_{part}_{grip}.json'])['display'][hand]
            scale, rr, tt = np.array(display['scale']),rotation(display['rotation']),np.array(display['translation'])
            if max(scale) == 0:
                continue
            for points,uv,texture,normal in triangles[part]:
                result.append(((np.asarray(points)-8)*scale@rr.T+tt,uv,texture,rr@normal))
        return result

    def raster(ts,cam,w,h,extent=None):
        if extent is None:
            extent = helper['frame'](np.concatenate([x[0] for x in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]

    sheet = Image.new('RGB',(1600,1610),'#111925')
    draw = ImageDraw.Draw(sheet)
    draw.text((12,10),"W179 MINDBENDER'S AMBITION (ADEPT) | emitted-JSON offline reconstruction | no hands / no native claim",fill='white')
    cams = ([1,.25,-.5],[-1,-.35,.45],[.65,-.7,1])
    selections = (('initial',0),('initial',20),('loop',11),('return',20))
    for row,cam in enumerate(cams):
        groups = [posed(phase,i) for phase,i in selections]
        extent = helper['frame'](np.concatenate([x[0] for ts in groups for x in ts]),cam,400,290)
        for col,((phase,i),ts) in enumerate(zip(selections,groups)):
            y = 50+row*325
            sheet.paste(raster(ts,cam,400,290,extent),(col*400,y))
            draw.text((col*400+10,y-16),f'{phase} {i/20:.2f} | oblique {row+1}',fill='white')
    draw.text((12,1020),'104 exact canonical body + 12 cartridge solids = 116 maximum. Held seams identical; one full-size shell per insert.',fill='white')
    # Fixed receiver-space crop shows loading tray, guard and correctly longitudinal shell.
    d = json.loads(output[A/f'models/{KEY}_loop_00_body_native.json'])['display'][FP[0]]
    rr,ss,tt = rotation(d['rotation']),np.array(d['scale']),np.array(d['translation'])
    box = np.array([[x,y,z] for x in (6.4,10.) for y in (7.8,11.8) for z in (1.4,7.4)])
    box = (box-8)*ss@rr.T+tt
    for col,(phase,i) in enumerate((('loop',2),('loop',11),('loop',17),('return',0))):
        cam = [1,-.85,.4]
        extent = helper['frame'](box,cam,400,290)
        sheet.paste(raster(posed(phase,i),cam,400,290,extent),(col*400,1080))
        draw.text((col*400+8,1058),f'UNDERSIDE {phase} {i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed('loop',11,grip=grip,hand=hand),[1,-.25,.5],400,190),(col*400,1400))
        draw.text((col*400+8,1382),grip+' / '+hand.removeprefix('firstperson_'),fill='white')
    draw.text((12,1590),'Crimp toward muzzle (-Z); rim toward stock (+Z). Contact under canonical tray; hidden inside solid action. Port travel authored where hands occlude.',fill='white')

    story = Image.new('RGB',(1600,1630),'#111925')
    draw = ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL MINDBENDER GAMEPLAY / AUTHORED ADEPT ASSET | original source PNGs above; emitted-JSON reconstruction below',fill='white')
    for index,frame in enumerate(reference['frames']):
        x,y = index%4*400,40+index//4*520
        path = reference_dir/frame['file']
        if sha(path.read_bytes()) != frame['sha256']:
            raise ValueError('Reference frame drift: '+str(path))
        im = Image.open(path).convert('RGB')
        im.thumbnail((400,225))
        story.paste(im,(x,y))
        draw.text((x+8,y+228),f"ACTUAL {frame['timestampSeconds']:.3f}s | {frame['observation'][:48]}",fill='white')
        phase,i = frame['authoredPhase'],round(frame['authoredProgress']*20)
        story.paste(raster(posed(phase,i),[1,-.2,.5],400,225),(x,y+258))
        draw.text((x+8,y+487),f'AUTHORED {phase} {i/20:.2f} | no extracted bones',fill='white')
    draw.text((12,1605),'Source version / dye identified in SOURCE.md. Per-shell hand passes observed; exact cartridge path, angles and 16-tick retiming authored.',fill='white')
    return png(sheet),png(story)


def generate(reference_dir):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes()) != digest:
            raise ValueError('Canonical input drift: '+path)
    source = json.loads((ROOT/SOURCE).read_bytes())
    twohand = json.loads((ROOT/TWOHAND).read_bytes())['display']
    canonical = json.loads((ROOT/ITEM).read_bytes())
    reference = json.loads((reference_dir/'reference-frames.json').read_bytes())
    rule = next(r for r in json.loads((ROOT/'src/main/resources/weapon_surface_w123/manifest.json').read_bytes())['targets']
                if r['path']=='assets/destiny/models/weapon/shotgun/mindbender_s_ambition_adept.json')
    if rule['replacement'] != str(SOURCE).removeprefix('src/main/resources/') or rule['replacementSha256'] != PINS[str(SOURCE)]:
        raise ValueError('Effective canonical surface mapping drift')
    if len(source['elements']) != 104 or len(reference['frames']) != 12 or not reference['inspectedActualFrames']:
        raise ValueError('Canonical count or actual reference missing')
    output = {}
    def emit(path,value):
        output[path] = encode(value)
    emit(A/f'models/{KEY}_body.json',copy.deepcopy(source))
    emit(A/f'models/{KEY}_shell.json',shell_geometry(source))
    entries = []
    for phase_index,phase in enumerate(PHASES):
        for i in range(21):
            for part in PARTS:
                for grip in GRIPS:
                    emit(A/f'models/{KEY}_{phase}_{i:02}_{part}_{grip}.json',dict(
                        parent=f'destiny:{KEY}_{part}',
                        display=pose_display(source['display'],twohand,phase,i/20,part,grip)))
            def composite(grip):
                return dict(type='minecraft:composite',models=[dict(type='minecraft:model',
                    model=f'destiny:{KEY}_{phase}_{i:02}_{part}_{grip}') for part in PARTS])
            entries.append(dict(threshold=phase_index*2+i/20,model=dict(type='minecraft:condition',
                property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    dispatch = dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=4,
                    entries=entries,fallback=copy.deepcopy(canonical['model']))
    modes = dict(type='minecraft:select',property='minecraft:custom_model_data',index=0,
                 cases=[dict(when=mode,model=copy.deepcopy(canonical['model'])) for mode in ('ads','inspect')],fallback=dispatch)
    wrapper = copy.deepcopy(canonical)
    wrapper['model'] = dict(type='minecraft:select',property='minecraft:display_context',
        cases=[dict(when=list(FP),model=modes)],fallback=copy.deepcopy(canonical['model']))
    emit(A/f'items/{KEY}.json',wrapper)
    comparison,story = previews(output,reference_dir,reference)
    output[ART/'comparison.png'],output[ART/'storyboard.png'] = comparison,story
    inputs = [SELF,Path('scripts/generate_surface_w123_hammerhead.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W179',weapon='mindbender_s_ambition_adept',itemModel='destiny:'+KEY,
        ownedFiles=262,generatedFiles=258,packFiles=255,parents=2,displayChildren=252,phases=list(PHASES),
        framesPerPhase=21,progressFloatIndex=4,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceGeometryPath=str(SOURCE),sourceElements=104,bodyElements=104,shellElements=12,
        triangleAdapterElements=0,maxAssembledElements=116,elementLimit=1000,
        bodyGeometryAndUVPreserved=True,bodyElementsAndUVSha256=sha(encode(source['elements'])),
        newTextures=0,shellAnchor=SHELL_ANCHOR,gripPivot=GRIP,keyframes=KEYS,visibility=VISIBLE,
        shellAxis=dict(longitudinal='Z',crimpDirection=[0,0,-1],rimDirection=[0,0,1],
                       chamberContact=add(SHELL_ANCHOR,CONTACT),occludedSeat=add(SHELL_ANCHOR,SEATED)),
        hiddenGeometry='One authored cartridge; 12 overlapping case/head/rim solids using canonical tray/collar texels. Full-size visible approach; occlusion inside unmodified action_solid. No port cut or hand model.',
        bodyHipEndpoints=[['initial',0],['return',20]],
        heldSeams=[['initial',20],['loop',0],['loop',20],['return',0]],
        returnTicks=6,returnBlocksGameplay=False,
        ammoTransferPolicy='Existing WeaponCycle alone pays exactly one shell at each successful 16-tick insert; capacity5. Initial raises once, loop stays held; six-tick return is cosmetic and supplies no ammunition.',
        rotationConvention='Rigid Rx Ry Rz about Mindbender source grip. Rotate source-local cartridge offset, compensate anchor, apply .85 scale once, then carry native to twohand frame. No additive Euler.',
        fallback='Exact canonical graph in non-FP and ADS/inspect. Negative inactive float4 selects canonical graph.',
        reference=reference,nativeGameplayVerified=False,handIK=False,extractedBones=False,
        thirdPersonReloadClaim=False,mechanicsOrAudioChanged=False,
        integration=dict(masterOwnsRuntime=True,workerRuntimeEdited=False,requiredMasterModel='destiny:'+KEY,
            requiredContract='Master adds exact canonical ID to WeaponInsertPresentation support/model routing and shared registries. Existing float4 initial0..1 / loop2..3 / return4..5, flag0 grip, .001 collision policy and one-shell mechanics remain authoritative.',
            nativeQueue=['Both FP contexts and native/twohand; empty5mag with finite reserves: initial once, then held one-shell loops every16ticks, stop/full/reserve exhaustion.',
                'Interrupt after a paid shell and fire during return; cancel/restart, ADS/inspect, swap/death/disconnect neutral restoration; verify no shell at phase seams.',
                'Underside loading contact/crimp axis, guard clearance, bone/rune silhouette; canonical third-person/GUI/ground/head/fixed; brief10-20 display check.']),
        limitations=['Offline raster/parser/codec are not native visual, server, performance or listening verification.',
            'Hands occlude the source loading contact; exact cartridge path/angles are authored. Canonical solid tray is preserved, not a new open chamber.',
            'Source gameplay variant/dye and local Adept art are distinguished in SOURCE.md. No extracted bones or IK.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},
        sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output) != expected_output_paths():
        raise ValueError('Generated path contract drift')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--reference-dir',type=Path,default=Path('/private/tmp/w179-mindbender-s-ambition-adept-report'))
    args = parser.parse_args()
    output = generate(args.reference_dir)
    scope = Path('/private/tmp/w179-manifest.json')
    if scope.exists():
        owned = set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features']
                         if f['name']=='w179-mindbender-s-ambition-adept'))
        if not {str(p) for p in output} <= owned:
            raise SystemExit('Outside exact ownership')
    for path,content in output.items():
        target = ROOT/path
        if args.verify:
            if not target.is_file() or target.read_bytes() != content:
                raise SystemExit('Asset differs: '+str(path))
        else:
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(content)
    print(('Verified' if args.verify else 'Generated')+' 258 deterministic outputs / 255 pack assets; 104 canonical +12 shell =116; native QA pending master.')

if __name__ == '__main__':
    main()
