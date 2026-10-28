#!/usr/bin/env python3
"""Player-skin arm overlays on existing 26.3 item-model graphs; no gameplay state."""
import argparse
import copy
import hashlib
import json
import math
import re
from functools import lru_cache
from pathlib import Path
import skin_arm_models_w204 as skin_arms
import first_person_framing_w205 as framing
import rig_arms_w205 as rig_arms
import reload_hand_w218 as reload_hand

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'src/main/resources/assets/destiny'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PREFIX = 'weapon_hands_w201/'
CONTACTS = ROOT / 'art/weapons/w201/contacts.json'
MANIFEST = ROOT / 'art/weapons/w201/manifest.json'
ROUTES = ROOT / 'src/main/resources/destiny/weapons/w201-first-person-hands.json'

def enc(v):
    return (json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()

def sha(v):
    return hashlib.sha256(v).hexdigest()

def xyz(degrees):
    x,y,z=map(math.radians,degrees);a,b,c,d,e,f=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return [[c*e,-c*f,d],[b*d*e+a*f,-b*d*f+a*e,-b*c],[-a*d*e+b*f,a*d*f+b*e,a*c]]

def mul(a,b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def vec(a,b):
    return [sum(a[i][j]*b[j] for j in range(3)) for i in range(3)]

def euler(r):
    y=math.asin(max(-1,min(1,r[0][2])))
    if abs(math.cos(y))>1e-8:x,z=math.atan2(-r[1][2],r[2][2]),math.atan2(-r[0][1],r[0][0])
    else:x,z=math.atan2(r[2][1],r[1][1]),0
    return [round(math.degrees(v),8) for v in (x,y,z)]

def model_path(key):
    assert key.startswith('destiny:') and '..' not in key
    return A/'models'/(key.split(':',1)[1]+'.json')

@lru_cache(None)
def resolve(key):
    p=model_path(key);d=json.loads(p.read_bytes());parent=d.get('parent');chain=[key]
    result={}
    if parent and parent.startswith('destiny:'):
        base,ancestors=resolve(parent);result=copy.deepcopy(base);chain+=ancestors
    # Display contexts inherit independently, unlike the elements array.
    display={**result.get('display',{}),**d.get('display',{})}
    textures={**result.get('textures',{}),**d.get('textures',{})}
    result.update(d);result['display']=display;result['textures']=textures
    return result,chain

def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)

def source_mesh_contacts(config,amount,bow_draw_displacement=0.0):
    """Keep mesh-specific bow anchors when replaying the original arm chain."""
    contacts={side:framing.contact(config,side) for side in ('right','left')}
    if config['family']=='bow':
        contacts['left']['position'][1]-=config['framing'].get('supportHipLower',0)*amount
        contacts['right']['position'][2]+=bow_draw_displacement
    return contacts

def display_at(source,contact):
    out={}
    for context in FP:
        root=source.get(context,{})
        r=xyz(root.get('rotation',[0,0,0]));scale=root.get('scale',[1,1,1]);t=root.get('translation',[0,0,0])
        if max(scale)-min(scale)>1e-5:raise ValueError('Nonuniform grip frame requires a baked adapter')
        anchor=contact['position'];local=xyz(contact.get('rotation',[0,0,0]))
        delta=vec(r,[(anchor[i]-8)*scale[i] for i in range(3)])
        out[context]={'rotation':euler(mul(r,local)),
                      'translation':[round(t[i]+delta[i],8) for i in range(3)],
                      'scale':list(scale)}
    return out

def blend_display(a,b,t):
    # Interpolate contact frames as rotations, not wrapped Euler coordinates.
    # Reuse the project's audited quaternion helper, with no asset regeneration.
    import runpy
    if not hasattr(blend_display,'helper'):
        blend_display.helper=runpy.run_path(str(ROOT/'scripts/generate_ace_reload_w157.py'))
    h=blend_display.helper
    out={}
    for ctx in FP:
        x,y=a[ctx],b[ctx]
        r=h['slerp'](h['quaternion'](xyz(x['rotation'])),h['quaternion'](xyz(y['rotation'])),t)
        out[ctx]={'rotation':euler(r),'translation':[round(u+(v-u)*t,8) for u,v in zip(x['translation'],y['translation'])],
                  'scale':[round(u+(v-u)*t,8) for u,v in zip(x['scale'],y['scale'])]}
    return out

def generated():
    resolve.cache_clear()
    framing_data=framing.load()
    rigs,rig_inputs=rig_arms.load()
    contacts=json.loads(CONTACTS.read_bytes())['weapons']
    # Sword belongs to the existing forced-camera player/BetterModel route.
    contacts={k:framing.contacts(framing_data,k,v) for k,v in contacts.items() if v['family']!='sword'}
    originals={v['canonicalModel']:k for k,v in contacts.items()}
    counts={side:112 for side in ('right','left')} # worst case: classic forearm skin surfaces
    outputs=skin_arms.generated();inputs={str(framing.CONFIG.relative_to(ROOT)):sha(framing.CONFIG.read_bytes()),'scripts/reload_hand_w218.py':sha((ROOT/'scripts/reload_hand_w218.py').read_bytes()),**rig_inputs,**framing_data['profileInputs']};routes={};budgets={};stats={'overlaidGraphs':0,'contactFrames':0,'rigFrames':0}
    def source(key):
        geo,chain=resolve(key)
        for name in chain:
            p=model_path(name);inputs[str(p.relative_to(ROOT))]=sha(p.read_bytes())
        return geo,chain
    def identity(key,fallback):
        _,chain=source(key)
        for name in reversed(chain):
            if name in originals:return originals[name]
        # Split reload geometry names retain the exact weapon ID.
        for name in reversed(chain):
            basename=name.rsplit('/',1)[-1]
            for id in sorted(contacts,key=len,reverse=True):
                if basename==id or basename.startswith(id+'_'):return id
        return fallback
    def glove(side,display):
        return skin_arms.arm_nodes(side,display,outputs)
    def eligible(ref):
        if not isinstance(ref,dict) or ref.get('type')!='minecraft:model':return False
        key=ref.get('model','')
        if not key.startswith('destiny:'):return False
        geo,_=source(key)
        return len(geo.get('elements',[]))>=18
    def role(ref):
        return ref['model'].rsplit('/',1)[-1]
    def with_hands(node,refs,id,state):
        if not refs:return copy.deepcopy(node)
        primary=next((r for r in refs if re.search(r'_(body|fixed|receiver)(_|$)',role(r))),refs[0])
        id=identity(primary['model'],id)
        if id not in contacts:return copy.deepcopy(node)
        config={**contacts[id],'framing':framing.profile(framing_data,id,contacts[id]['family'])}
        geo,_=source(primary['model'])
        amount=framing.weight(state,primary['model'])
        progress=state.get(1)
        insert_phase=None
        if id in ('dust_rock_blues', 'first_in_last_out', 'ikelos_sg_v1_0_1', 'mindbender_s_ambition_adept', 'parcel_of_stardust_fell_to_earth', 'long_arm') and 4 in state:
            value=state[4]
            if 0 <= value <= 5:
                insert_phase=('initial','loop','return')[min(2,int(value//2))]
                progress=max(0.0,min(1.0,value-2*min(2,int(value//2))))
                config['insertPhase']=insert_phase
        if id=='izanagis_burden':
            # W91 owns CMD6: ordinary 0..1, Honed 2..3, charged idle 4.
            value=state.get(6)
            progress=(value-2 if 2<=value<=3 else value if 0<=value<=1 else None) if value is not None else None
        source_chain=config['framing'].get('sourceFullChain',False)
        authored_body=framing.display(geo['display'],config['framing'],amount,xyz,mul,euler,vec)
        ready_key=config['canonicalModel']
        if '_twohand' in primary['model'] and model_path(ready_key+'_twohand').exists():ready_key+='_twohand'
        ready_body=framing.display(source(ready_key)[0]['display'],config['framing'],amount,xyz,mul,euler,vec) if source_chain else None
        def framed(original):
            result=framing.display(original,config['framing'],amount,xyz,mul,euler,vec)
            if source_chain and progress is not None and 0<=progress<=1:
                result=rig_arms.source_weapon_display(rigs[id],state,progress,config,authored_body,ready_body,result,xyz,mul,euler,vec)
            lift=framing.reload_camera_lift(config['framing'],progress,insert_phase)*amount
            if lift:
                for ctx in FP:
                    result[ctx]['translation'][1]+=lift
            # Keep normal-length forearms connected to the lower screen edge
            # when the authored reload raises the weapon. Move the whole
            # assembly in camera Y, never stretch a forearm or move its palm.
            if progress is not None and 0<progress<1:
                lower=config['framing'].get('reloadCameraLower',0)
                envelope=smooth((progress-.02)/.12)*(1-smooth((progress-.80)/.18))
                for ctx in FP:
                    result[ctx]['translation'][1]-=lower*envelope
            return result
        body_display=framed(geo['display'])
        right=display_at(body_display,framing.contact(config,'right'))
        left=display_at(body_display,framing.contact(config,'left'))
        base_right=copy.deepcopy(right)
        reload_target=None;reload_grip_weight=0.;moving_key=None
        handling_side=reload_hand.side(config['reload'])
        bow_draw_displacement=0.0
        if config['family']=='bow':
            # Keep the palm on the lower riser pad, below the sight aperture.
            # This is mesh-contact retargeting, not a recovered camera offset.
            contact=framing.contact(config,'left')
            contact['position'][1]-=config['framing'].get('supportHipLower',0)*amount
            left=display_at(body_display,contact)
            # W50 bakes string displacement into geometry, rather than display.
            moving=next((r for r in refs if re.search(r'_draw_\d+',role(r))),None)
            if moving:
                frame=int(re.search(r'_draw_(\d+)',role(moving))[1])
                contact=framing.contact(config,'right')
                bow_draw_displacement={'biting_winds':4.8,'whispering_slab':3.4}[id]*frame/20
                contact['position'][2]+=bow_draw_displacement
                right=display_at(framed(source(moving['model'])[0]['display']),contact)
        elif progress is not None and (insert_phase is not None or 0<progress<1):
            reload=config['reload'];hint=reload.get('partHint','magazine')
            moving=next((r for r in refs if r is not primary and re.search('_'+re.escape(hint)+r'(_|$)',role(r))),None)
            if moving is None:
                moving=next((r for r in refs if r is not primary and re.search(r'_(magazine|moving|cylinder|cell|shell|bolt)(_|$)',role(r))),None)
            target=source(moving['model'])[0]['display'] if moving else geo['display']
            pose={'position':reload['contact'],'rotation':reload.get('rotation',[0,0,0])}
            target=display_at(framed(target),pose)
            reload_target=target
            moving_key=moving['model'] if moving else None
            # Reach, contact during extraction/reseat, then return to fore-end.
            if insert_phase=='initial':
                weight=smooth((progress-.04)/.32)
            elif insert_phase=='loop':
                weight=1.0
            elif insert_phase=='return':
                weight=1-smooth(progress)
            else:
                # Some cylinders close well before the end of recovery.
                # Release that part before closure instead of trapping the palm
                # in the receiver with the generic magazine envelope.
                start,attached,release,end=reload.get('gripWindow',[.05,.20,.78,.98])
                if not 0<=start<attached<=release<end<=1:
                    raise ValueError('Invalid reload gripWindow: '+id)
                weight=smooth((progress-start)/(attached-start))*(1-smooth((progress-release)/(end-release)))
            if handling_side=='right':right=blend_display(right,target,weight)
            else:left=blend_display(left,target,weight)
            reload_grip_weight=weight
        if id in rigs:
            # Compensate the vanilla charged-crossbow carrier in its own frame.
            # In native grip this is identity. Avoid baking the animated weapon
            # rotation into the source elbow/wrist direction a second time.
            carrier_rotation={ctx:xyz([0,0,0]) for ctx in FP}
            if '_twohand' in primary['model']:
                normal=source(config['canonicalModel'])[0]['display']
                two_key=config['canonicalModel']+'_twohand'
                if model_path(two_key).exists():
                    two=source(two_key)[0]['display']
                    for ctx in FP:
                        a=xyz(two[ctx].get('rotation',[0,0,0]));b=xyz(normal[ctx].get('rotation',[0,0,0]))
                        carrier_rotation[ctx]=mul(a,[list(x) for x in zip(*b)])
            rig_arms.apply(rigs[id],state,progress,config,right,left,base_right,body_display,carrier_rotation,
                           config['framing'],amount,xyz,mul,euler,vec)
            stats['rigFrames']+=1
        part_shift={}
        if source_chain:
            mesh_contacts=source_mesh_contacts(config,amount,bow_draw_displacement)
            palms=rig_arms.source_palm_translations(rigs[id],state,progress,config,body_display,mesh_contacts,xyz,vec)
            for side,display in [('right',right),('left',left)]:
                for ctx in FP:display[ctx]['translation']=palms[side][ctx]
            # A generic full-shotgun action has no extracted shell event track.
            # Fit its normal-length source limb to the authored cartridge only
            # during the existing handling envelope, preserving source bend.
            # This is an explicit mesh contact fit, not exact wrist replay.
            if reload_target and config['reload'].get('sourcePalmContactFit',False):
                if config['reload'].get('policy')!='shell':
                    raise ValueError('Source palm contact fit currently requires shell policy: '+id)
                for ctx in FP:
                    left[ctx]['translation']=[round(v+(reload_target[ctx]['translation'][i]-v)*reload_grip_weight,8)
                                              for i,v in enumerate(left[ctx]['translation'])]
            # A detached magazine travels with the source handling hand while
            # attached. A hinged cylinder stays on the gun; the source hand
            # reaches for rounds instead of being pinned to its open flank.
            if moving_key and reload_target and config['reload'].get('policy')=='magazine':
                part_shift=reload_hand.attached_translation_shift(config['reload'],
                    {'right':right,'left':left},reload_target,reload_grip_weight,FP)
        if config['framing'].get('hideSupportAtRest'):
            # Apply visibility after rig retargeting. A source wrist bone does
            # not establish that its mesh is visible during pistol idle.
            visibility=smooth((progress-.01)/.07)*(1-smooth((progress-.91)/.08)) if progress is not None else 0
            for ctx in FP:
                left[ctx]['translation'][1]-=22*(1-visibility)
        arms=[glove('right',right),glove('left',left)]
        upper=rig_arms.upper_arm_displays(rigs[id],state,progress,config,right,left,xyz,mul,euler,vec) if id in rigs and source_chain else {}
        for side,display in upper.items():
            arms.append(skin_arms.arm_nodes(side,display,outputs,segment='upper'))
        assembled=sum(len(source(r['model'])[0].get('elements',[])) for r in refs)+sum(counts.values())+112*len(upper)
        budgets[id]=max(budgets.get(id,0),assembled)
        if assembled>1000:raise ValueError('Assembled budget exceeded: '+id)
        stats['contactFrames']+=1
        def weapon(n):
            if not isinstance(n,dict):return copy.deepcopy(n)
            if n.get('type')=='minecraft:model' and n.get('model','').startswith('destiny:'):
                original,_=source(n['model'])
                calibrated=framed(original['display'])
                if part_shift and n['model']==moving_key:
                    for ctx in FP:
                        calibrated[ctx]['translation']=[round(v+part_shift[ctx][i],8) for i,v in enumerate(calibrated[ctx]['translation'])]
                return framing.weapon_node(n,calibrated,outputs,A) if amount or config['framing'].get('cameraDepth',0) else copy.deepcopy(n)
            return {k:[weapon(x) for x in v] if isinstance(v,list) else weapon(v) if isinstance(v,dict) else copy.deepcopy(v) for k,v in n.items()}
        return {'type':'minecraft:composite','models':[weapon(node),*arms]}
    def rewrite(n,id,state):
        if not isinstance(n,dict):return copy.deepcopy(n)
        typ=n.get('type')
        if typ=='minecraft:composite':
            refs=[r for r in n['models'] if isinstance(r,dict) and r.get('type')=='minecraft:model' and r.get('model','').startswith('destiny:')]
            if any(eligible(r) for r in refs):return with_hands(n,refs,id,state)
        if typ=='minecraft:model':
            return with_hands(n,[n],id,state) if eligible(n) else copy.deepcopy(n)
        out={}
        for k,v in n.items():
            if k=='entries' and typ=='minecraft:range_dispatch':
                idx=n.get('index',0) if n.get('property')=='minecraft:custom_model_data' else None
                out[k]=[{**e,'model':rewrite(e['model'],id,{**state,**({idx:e['threshold']} if idx is not None else {})})} for e in v]
            elif k=='cases' and typ=='minecraft:select' and n.get('property')=='minecraft:custom_model_data' and n.get('index',0)==0:
                out[k]=[{**e,'model':rewrite(e['model'],id,{**state,'mode':e['when']})} for e in v]
            elif isinstance(v,dict):out[k]=rewrite(v,id,state)
            elif isinstance(v,list):out[k]=[rewrite(x,id,state) if isinstance(x,dict) else copy.deepcopy(x) for x in v]
            else:out[k]=v
        return out
    def specialize(n):
        # This graph runs only in the two first-person contexts. Do not bake
        # third-person/GUI branches (and their duplicate per-pixel tint lists).
        if not isinstance(n,dict):
            return [specialize(v) for v in n] if isinstance(n,list) else n
        if n.get('type')=='minecraft:select' and n.get('property')=='minecraft:display_context':
            selected=[]
            for ctx in FP:
                branch=n.get('fallback',{'type':'minecraft:empty'})
                for case in n.get('cases',[]):
                    when=case['when'];when=[when] if isinstance(when,str) else when
                    if ctx in when:branch=case['model'];break
                selected.append(specialize(branch))
            if selected[0]==selected[1]:return selected[0]
            return {'type':'minecraft:select','property':'minecraft:display_context',
                'cases':[{'when':ctx,'model':branch} for ctx,branch in zip(FP,selected)],
                'fallback':{'type':'minecraft:empty'}}
        out={k:specialize(v) for k,v in n.items()}
        if out.get('type')=='minecraft:condition' and out.get('on_true')==out.get('on_false'):
            return out['on_true']
        return out
    retired={'weapon_reload_w64','weapon_reload_w100','weapon_sight_w156'}
    for p in sorted((A/'items').rglob('*.json')):
        rel=p.relative_to(A/'items');folder=rel.parts[0]
        if folder in retired or folder.startswith(PREFIX.rstrip('/')):continue
        if not (folder=='weapon' or folder.startswith(('weapon_reload_w','weapon_sight_w','weapon_insert_w','weapon_swap_w'))
                or folder in {'weapon_aim_w70','weapon_bow_w50','weapon_izanagi_w91'}):continue
        stem=p.stem;id=stem if stem in contacts else stem[:-4] if stem.endswith('_bow') else stem.split('_to_')[-1]
        if id not in contacts:continue
        graph=json.loads(p.read_bytes());inputs[str(p.relative_to(ROOT))]=sha(p.read_bytes())
        original=graph['model'];augmented=specialize(rewrite(specialize(original),id,{}))
        wrapped={**graph,'hand_animation_on_swap':False,'model':{
            'type':'minecraft:select','property':'minecraft:display_context',
            'cases':[{'when':list(FP),'model':augmented}],'fallback':original}}
        key=rel.with_suffix('').as_posix();routes['destiny:'+key]='destiny:'+PREFIX+key
        outputs[A/f'items/{PREFIX}{key}.json']=(json.dumps(wrapped,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode();stats['overlaidGraphs']+=1
    outputs[ROUTES]=enc({'schemaVersion':1,'models':routes})
    outputs[MANIFEST]=enc({'stage':'W205','generator':'scripts/build_first_person_hands_w201.py',
        'skinArmElements':counts,'upperSkinArmElements':counts,
        'reloadHands':{k:reload_hand.side(v['reload']) for k,v in contacts.items()},
        'upperArmWeapons':sorted(k for k,v in rigs.items() if k in contacts and 'leftShoulder' in v['names'] and framing.profile(framing_data,k,contacts[k]['family']).get('sourceFullChain',False)),
        'weapons':sorted(contacts),'maxAssembledElements':budgets,'stats':stats,
        'routeCount':len(routes),'inputSha256':inputs,'contactsSha256':sha(CONTACTS.read_bytes()),
        'displayContexts':list(FP),'originalsEdited':False,
        'limitations':['Actual player skin via BetterModel DynamicUV; no fingers; sleeve composited onto base surface.',
          'Authored contacts follow existing item part frames, not source finger IK.',
          'Static item-model frame selection follows server updates; no continuous interpolation added.',
          'Generated coverage is not native visual acceptance for every weapon.'],
        'sha256':{str(p.relative_to(ROOT)):sha(b) for p,b in outputs.items()}})
    return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    previous=json.loads(MANIFEST.read_bytes()).get('sha256',{}) if MANIFEST.exists() else {}
    outputs=generated()
    for path,data in outputs.items():
        if args.verify:
            if not path.exists() or path.read_bytes()!=data:raise SystemExit('W201 output drift: '+str(path.relative_to(ROOT)))
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    if not args.verify:
        for rel,digest in previous.items():
            path=ROOT/rel
            if path in outputs or not path.exists():continue
            if not (path.is_relative_to(A/'models'/PREFIX/'poses') or path.is_relative_to(A/'models'/'skin_arm_w204'/'poses') or path.is_relative_to(A/'models'/framing.PREFIX)):continue
            if sha(path.read_bytes())!=digest:raise ValueError('Modified obsolete output retained: '+rel)
            path.unlink()
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} hand overlay files')
if __name__=='__main__':main()
