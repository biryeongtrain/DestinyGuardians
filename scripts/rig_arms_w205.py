"""Retarget evaluated Destiny wrist/elbow FK to fingerless player-skin arms.
No camera is present in the source. X-forward/Z-up -> view XYZ is explicit
calibration. The weapon/grip's accepted screen transform remains the anchor.
"""
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'art/weapons/w205/rigs'
C=((0,-1,0),(0,0,1),(-1,0,0))

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def unit(a):
 n=norm(a)
 if n<1e-8:raise ValueError('Degenerate rig arm')
 return [x/n for x in a]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def pos(m):return [m[i][3] for i in range(3)]
def transpose(m):return [list(x) for x in zip(*m)]

def load():
 result={};inputs={}
 import hashlib
 for path in sorted(DIR.glob('*.json')):
  data=path.read_bytes();d=json.loads(data);inputs[str(path.relative_to(ROOT))]=hashlib.sha256(data).hexdigest()
  for weapon in d['weapons']:
   if weapon not in result or (result[weapon]['fallback'] and not d['fallback']):result[weapon]=d
 for path in sorted((ROOT/'art/weapons/w218/rigs').glob('*.json')):
  raw=path.read_bytes();d=json.loads(raw);inputs[str(path.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
  for weapon in ('line_in_the_sand', 'stormchaser', 'code_duello', 'bellowing_giant', 'bad_omens'):
   if weapon in d['weapons']:result[weapon]=d
 for path in sorted((ROOT/'art/weapons/w219/rigs').glob('*.json')):
  raw=path.read_bytes();d=json.loads(raw);inputs[str(path.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
  for weapon in ('allied_demand', 'dead_man_walking_xx7463', 'high_albedo', 'frontier_justice', 'retraced_path'):
   if weapon in d['weapons']:result[weapon]=d
 for path in sorted((ROOT/'art/weapons/w220/rigs').glob('*.json')):
  raw=path.read_bytes();d=json.loads(raw);inputs[str(path.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
  for weapon in ('edge_transit', 'canis_major', 'dimensional_hypotrochoid', 'deafening_whisper', 'salvager_s_salvo'):
   if weapon in d['weapons']:result[weapon]=d
 for path in sorted((ROOT/'art/weapons/w221/rigs').glob('*.json')):
  raw=path.read_bytes();d=json.loads(raw);inputs[str(path.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
  for weapon in ('ikelos_sg_v1_0_1', 'mindbender_s_ambition_adept', 'parcel_of_stardust_fell_to_earth', 'pyroclastic_flow', 'seventh_seraph_officer_revolver'):
   if weapon in d['weapons']:result[weapon]=d
 return result,inputs

# Source maps label all three Ammit/Blast variants reload_full/reload_empty,
# without a weapon-specific selector. The caller must select an audited variant.
RELOAD_ACTIONS = {
 'ikelos_sg_v1_0_1': ('80A8A3F1',),
 'mindbender_s_ambition_adept': ('80A8A3F1',),
 'parcel_of_stardust_fell_to_earth': ('80A8A3F1',),
 'pyroclastic_flow': ('80A8A1A2',),
 'seventh_seraph_officer_revolver': ('80A8A53D',),

 'edge_transit': ('80A8A104',),
 'canis_major': ('80A8A104',),
 'dimensional_hypotrochoid': ('80A8A104',),
 'deafening_whisper': ('80A8A136',),
 'salvager_s_salvo': ('80A8A136',),

 'allied_demand': ('80A8A560',),
 'dead_man_walking_xx7463': ('80A8A560',),
 'high_albedo': ('80A8ADE2',),
 'frontier_justice': ('80A8A345',),
 'retraced_path': ('80A8A43C',),

 'line_in_the_sand': ('80A8ADD3',),
 'stormchaser': ('80A8ADE1',),
 'code_duello': ('80A8A1F5',),
 'bellowing_giant': ('80A8A1F5',),
 'bad_omens': ('80A8A1F5',),

 'erentil_fr4': ('80A8ADD3',),
 'hollow_words': ('80A8ADD3',),
 'dream_breaker': ('80A8ADD3',),
 'null_composure': ('80A8ADD3',),
 'coriolis_force': ('80A8A43C',),

 'distant_relation': ('80A8A345','80A8A337','80A8A331'),
 'patron_of_lost_causes': ('80A8A345','80A8A337','80A8A331'),
 'brass_attacks': ('80A8ADE2',),
 'ikelos_smg_v1_0_1': ('80A8A170',),
 'duke_mk_44': ('80A8A53D',),
 'farewell': ('80A8ADE2',),
 'apostate': ('80A8A17D',),
 'fixed_odds': ('80A8A005',),
 'halfdan_d': ('80A8A395','80A8A38C','80A8A38A'),
 'claws_of_the_wolf': ('80A8A36A','80A8A368','80A8A366'),
 'bite_of_the_fox': ('80A8A140','80A8A14D','80A8A150'),
 'retrofit_escapade': ('80A8A005',),
 'lonesome': ('80A8A560',),
 'steelfeather_repeater': ('80A8A395','80A8A38C','80A8A38A'),
 'aishas_embrace': ('80A8A345','80A8A337','80A8A331'),
 'chattering_bone': ('80A8A36A','80A8A368','80A8A366'),
 'antiope_d': ('80A8A170',),
 'bug_out_bag': ('80A8A170',),
 'cold_denial': ('80A8A36A','80A8A368','80A8A366'),
 'bygones': ('80A8A36A','80A8A368','80A8A366'),
 'ammit_ar2': ('80A8A395','80A8A38C','80A8A38A'),
 'blast_furnace': ('80A8A36A','80A8A368','80A8A366'),
 'hammerhead': ('80A8A005',),
 'dust_rock_blues': ('80A8A3F1',),
 'the_recluse': ('80A8A192',),
 'beloved': ('80A8A140','80A8A14D','80A8A150'),
 'gnawing_hunger': ('80A8A395','80A8A38C','80A8A38A'),
 'first_in_last_out': ('80A8A3F1',),
 'austringer': ('80A8A53D',),
}

def smooth(t):
 t=max(0.,min(1.,t));return t*t*(3-2*t)

def quaternion(m):
 # Largest-component extraction avoids the 180-degree trace singularity.
 v=[1+m[0][0]+m[1][1]+m[2][2],1+m[0][0]-m[1][1]-m[2][2],
    1-m[0][0]+m[1][1]-m[2][2],1-m[0][0]-m[1][1]+m[2][2]]
 i=max(range(4),key=v.__getitem__);a=math.sqrt(max(0,v[i]))/2;d=4*a
 if i==0:q=[a,(m[2][1]-m[1][2])/d,(m[0][2]-m[2][0])/d,(m[1][0]-m[0][1])/d]
 elif i==1:q=[(m[2][1]-m[1][2])/d,a,(m[0][1]+m[1][0])/d,(m[0][2]+m[2][0])/d]
 elif i==2:q=[(m[0][2]-m[2][0])/d,(m[0][1]+m[1][0])/d,a,(m[1][2]+m[2][1])/d]
 else:q=[(m[1][0]-m[0][1])/d,(m[0][2]+m[2][0])/d,(m[1][2]+m[2][1])/d,a]
 return unit(q)

def interpolate(a,b,t):
 """Linear evaluated joint position, shortest-arc quaternion rotation."""
 if t<=0:return [row[:] for row in a]
 if t>=1:return [row[:] for row in b]
 qa,qb=quaternion(a),quaternion(b);cosine=dot(qa,qb)
 if cosine<0:qb=[-x for x in qb];cosine=-cosine
 if cosine>.9995:q=unit([x+(y-x)*t for x,y in zip(qa,qb)])
 else:
  angle=math.acos(max(-1,min(1,cosine)));s=math.sin(angle)
  q=[(x*math.sin((1-t)*angle)+y*math.sin(t*angle))/s for x,y in zip(qa,qb)]
 w,x,y,z=q;p=[a[i][3]+(b[i][3]-a[i][3])*t for i in range(3)]
 return [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),p[0]],
         [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),p[1]],
         [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y),p[2]],[0.,0.,0.,1.]]

def blend_joints(a,b,t):
 return {name:interpolate(m,b[name],t) for name,m in a.items()}

def sample(action,progress):
 """Use actual exported progress coordinates, not round(progress*20)."""
 frames=action['frames'];p=max(0.,min(1.,progress))
 if p<=frames[0]['progress']:return frames[0]['joints']
 for a,b in zip(frames,frames[1:]):
  if p<=b['progress']:
   t=(p-a['progress'])/(b['progress']-a['progress'])
   return blend_joints(a['joints'],b['joints'],t)
 return frames[-1]['joints']

def rest_joints(data,state):
 tag=data['ads'] if (state.get('mode')=='ads' or state.get(3,0)>=.95) and data['ads'] else data['idle']
 return data['actions'][tag]['frames'][0]['joints']

def joints(data,state,progress,config=None):
 """Optional config extends the old API; apply already receives it.

 reload.rigAction disambiguates shared selectors; insertPhase is the caller's
 normalized Dust initial/loop/return lifecycle, not a source event claim.
 """
 config=config or {};rest=rest_joints(data,state)
 if progress is None or not 0<=progress<=1:return rest,False
 weapon=config.get('weapon',config.get('canonicalModel','').rsplit('/',1)[-1])
 group=data['group'];tag=None;phase=config.get('insertPhase')
 if group=='hand_cannon_f163a4c8':tag='80A8A567'
 elif group=='hand_cannon_cedb29ae':tag='80A8A53D'
 elif group=='sniper_rifle_ececad46':
  value=state.get(6,-1)
  if value==4:return rest,False
  tag='80A8A14D' if 2<=value<=3 else '80A8A140'
 elif weapon in RELOAD_ACTIONS:
  choices=RELOAD_ACTIONS[weapon];tag=config.get('reload',{}).get('rigAction')
  if tag is None and len(choices)==1:tag=choices[0]
  if tag not in choices:raise ValueError(f'{weapon}: reload.rigAction must select an audited source action from {choices}')
 if tag is None:return rest,False
 if tag not in data['actions']:raise ValueError(f'Missing evaluated reload action {tag}')
 p=progress;weight=smooth(p/.1)*smooth((1-p)/.1);source_p=p
 if weapon in ('dust_rock_blues', 'first_in_last_out', 'ikelos_sg_v1_0_1', 'mindbender_s_ambition_adept', 'parcel_of_stardust_fell_to_earth'):
  # One generic full reload is not an extracted shell-loop event track.
  # Calibrated continuous slice: hold the port pose at .35 across phase
  # boundaries; excursion/retrace during each insert avoids a loop-end pop.
  if phase=='initial':
   source_p=.35*smooth(p/.36);weight=smooth(p/.1)
  elif phase=='loop':
   source_p=.35 if config.get('reload',{}).get('sourceShellPoseHold',False) else .35+.30*math.sin(math.pi*p)**2
   weight=1.
  elif phase=='return':
   if config.get('reload',{}).get('sourceShellPoseHold',False):
    # Keep the generic source body AND arm sample together. Replaying the
    # rest of its full reload during recovery turns the shotgun sideways;
    # holding only its body instead makes the source upper arms enter view.
    # This explicit calibration is not an extracted shell-loop event track.
    source_p=.35;weight=1-smooth(p)
   else:source_p=.35+.65*smooth(p);weight=smooth((1-p)/.1)
  else:raise ValueError(f'{weapon} requires insertPhase initial, loop or return')
 if weight==0:return rest,False
 return blend_joints(rest,sample(data['actions'][tag],source_p),weight),True

def forearm_basis(joints, side):
 """Evaluated forearm frame: elbow->wrist is source +X, elbow +Y is transverse.

 Do not project wrist +X: hand articulation can align it with the forearm,
 producing artificial 180-degree roll flips. Elbow +Y carries actual
 forearm roll without that wrist-axis singularity.
 """
 wrist=joints[side+'Wrist'];elbow=joints[side+'Elbow']
 y=unit(sub(pos(wrist),pos(elbow)))
 x=[elbow[i][1] for i in range(3)]
 x=unit([x[i]-y[i]*dot(x,y) for i in range(3)])
 z=unit(cross(x,y));x=cross(y,z)
 return transpose([x,y,z])

def weapon_basis(joints):
 """Remove tiny exported scale/shear before inverting the weapon rotation."""
 m=joints['weapon'];x=unit([m[i][0] for i in range(3)])
 y=[m[i][1] for i in range(3)];y=unit([y[i]-x[i]*dot(y,x) for i in range(3)])
 z=unit(cross(x,y));y=cross(z,x)
 return transpose([x,y,z])

def weapon_relative_delta(reference,current,side,mul):
 """Rotation change in the common source weapon-parent frame.

 A contact frame is a mesh calibration, not the source bone's local axes.
 Transport the swing in weapon space before applying that calibration.
 """
 rest=mul(transpose(weapon_basis(reference)),forearm_basis(reference,side))
 active=mul(transpose(weapon_basis(current)),forearm_basis(current,side))
 return mul(active,transpose(rest))

def source_weapon_display(data,state,progress,config,body,ready,part,xyz,mul,euler,vec):
 """Replay the source weapon bone, retaining authored part/body transforms.

 Only the rest camera/mesh placement is calibrated. Source pose and limb
 matrices share one parent frame; the source file has no exported camera.
 """
 current,_=joints(data,state,progress,config);rest=rest_joints(data,state)
 wr=weapon_basis(rest);wt=weapon_basis(current)
 delta=mul(mul(C,mul(transpose(wr),wt)),transpose(C))
 shift=vec(C,vec(transpose(wr),sub(pos(current['weapon']),pos(rest['weapon']))))
 out={k:dict(v) for k,v in part.items()}
 for ctx in ('firstperson_righthand','firstperson_lefthand'):
  b,r,p=body[ctx],ready[ctx],part[ctx]
  before=xyz(b['rotation']);after=mul(xyz(r['rotation']),delta)
  change=mul(after,transpose(before))
  displacement=vec(xyz(r['rotation']),[v*32*r['scale'][0] for v in shift])
  anchor=[r['translation'][i]+displacement[i] for i in range(3)]
  offset=vec(change,sub(p['translation'],b['translation']))
  out[ctx]={'rotation':euler(mul(change,xyz(p['rotation']))),
            'translation':[round(anchor[i]+offset[i],8) for i in range(3)],
            'scale':list(p['scale'])}
 return out

def source_palm_translations(data,state,progress,config,body,contacts,xyz,vec):
 """Retarget source wrist travel, not just its direction, to the remodeled grip.

 A fixed rest-space mesh offset follows the weapon. Pinning the animated
 wrist to an unrelated authored reload target translates its whole source
 shoulder chain into the sky even when the rotations are internally correct.
 """
 current,_=joints(data,state,progress,config);rest=rest_joints(data,state)
 wt=transpose(weapon_basis(current));wr=transpose(weapon_basis(rest))
 result={}
 for side,contact in contacts.items():
  active=vec(C,vec(wt,sub(pos(current[side+'Wrist']),pos(current['weapon']))))
  ready=vec(C,vec(wr,sub(pos(rest[side+'Wrist']),pos(rest['weapon']))))
  result[side]={}
  for ctx,b in body.items():
   local=[(contact['position'][i]-8+32*(active[i]-ready[i]))*b['scale'][i] for i in range(3)]
   offset=vec(xyz(b['rotation']),local)
   result[side][ctx]=[round(b['translation'][i]+offset[i],8) for i in range(3)]
 return result

def upper_arm_displays(data,state,progress,config,right,left,xyz,mul,euler,vec):
 """Attach a normal-length upper arm to the retargeted forearm elbow.

 The source shoulder origins are evaluated from the original Blender action.
 Keep its shoulder/elbow/forearm bend; anchor the chain at the accepted palm
 contact instead of moving that palm to an unrelated original mesh.
 """
 reference=rest_joints(data,state)
 if not all(side+'Shoulder' in reference for side in ('right','left')):return {}
 current,_=joints(data,state,progress,config)
 result={}
 for side,forearm in [('right',right),('left',left)]:
  shoulder=current[side+'Shoulder'];elbow=current[side+'Elbow']
  y=unit(sub(pos(elbow),pos(shoulder)))
  x=[shoulder[i][1] for i in range(3)]
  x=unit([x[i]-y[i]*dot(x,y) for i in range(3)])
  z=unit(cross(x,y));x=cross(y,z)
  upper=transpose([x,y,z])
  bend=mul(transpose(forearm_basis(current,side)),upper)
  length=norm(sub(pos(reference[side+'Elbow']),pos(reference[side+'Shoulder'])))*32
  result[side]={}
  for ctx,display in forearm.items():
   r=xyz(display['rotation']);s=display['scale']
   # W204's open forearm elbow is local Y1.5, wrist pivot Y8.
   offset=vec(r,[0,-6.5*s[1],0])
   result[side][ctx]={'rotation':euler(mul(r,bend)),
                    'translation':[round(v+offset[i],8) for i,v in enumerate(display['translation'])],
                    'scale':[s[0],round(s[0]*length/7.5,8),s[2]]}
 return result

def apply(data,state,progress,config,right,left,base_right,body_display,carrier_rotation,settings,amount,xyz,mul,euler,vec):
 j,dynamic=joints(data,state,progress,config)
 reference=rest_joints(data,state)
 # Actual source direction and twist. Hand/finger geometry is never imported.
 for ctx in ('firstperson_righthand','firstperson_lefthand'):
  side=-1 if ctx.endswith('lefthand') else 1
  rot=[v*amount for v in settings.get('rotation',[0,0,0])];rot[1]*=side;rot[2]*=side
  q=mul(mul(xyz(rot),carrier_rotation[ctx]),xyz(settings.get('sourceViewRotation',[0,0,0])))
  for name,display in [('right',right),('left',left)]:
   h=j[name+'Wrist'];elbow=j[name+'Elbow']
   # Interpolating FK positions can shorten a chord. Keep ordinary source
   # forearm length; only direction/twist animate, never extend the arm.
   length=norm(sub(pos(reference[name+'Wrist']),pos(reference[name+'Elbow'])))*32
   # W209: remodeled grips/handling parts have their own calibrated contact
   # frame. Absolute source-camera twist is incompatible with that frame;
   # keep its orientation attached to the body/part, including during reload.
   # Still retain the ordinary source forearm length below (never stretch).
   if settings.get('sourceFullChain',False):
    if name+'Shoulder' not in j:raise ValueError('Full chain requires evaluated source shoulder: '+name)
    # A whole source limb needs its actual longitudinal axes, not an arbitrary
    # per-contact direction bias. Otherwise the same upper-arm bend turns
    # upward into the ADS view. Palm location is still the remodeled contact.
    body=xyz(body_display[ctx].get('rotation',[0,0,0]))
    source=mul(transpose(weapon_basis(j)),forearm_basis(j,name))
    display[ctx]['rotation']=euler(mul(mul(body,C),source))
   elif settings.get('sourceWeaponRelative',False) and dynamic:
    # Calibrate once in weapon space. Absolute armature-space source FK was
    # incompatible with the animated remodeled weapon's frame. Preserve the
    # actual source elbow/wrist motion relative to weapon bone 4A0810C4;
    # current mesh palm translations remain attached to their handling parts.
    body=xyz(body_display[ctx].get('rotation',[0,0,0]))
    # Contact is already composed by display_at/blend_display, including
    # wrist roll and the current moving-part grip/release frame. Rebuilding
    # it from ready config here discarded the left handling-part rotation.
    contact=xyz(display[ctx]['rotation'])
    delta=weapon_relative_delta(reference,j,name,mul)
    # Source X-forward/Z-up -> canonical -Z-forward/Y-up. The swing must
    # precede the authored contact frame; postmultiplication changes its axis
    # with each hand's rest calibration and made raised reloads splay sideways.
    canonical_delta=mul(mul(C,delta),transpose(C))
    swing=mul(mul(body,canonical_delta),transpose(body))
    display[ctx]['rotation']=euler(mul(swing,contact))
   elif not settings.get('meshArmDirections', False):
    y=unit(vec(C,sub(pos(h),pos(elbow))))
    x=vec(C,[h[i][0] for i in range(3)])
    x=unit([x[i]-y[i]*dot(x,y) for i in range(3)])
    z=unit(cross(x,y));x=cross(y,z)
    rotation=transpose([x,y,z])
    display[ctx]['rotation']=euler(mul(q,rotation))
   display[ctx]['scale'][1]=round(display[ctx]['scale'][1]*length/6.5,8)
  # Idle/ADS hand separation comes from this weapon's source rig. For the
  # imported Ace/Duke reload, also follow the actual changing FK separation.
  # Bow right hand alone follows the existing string draw displacement.
  # The remodeled bows have a different riser/string separation from the
  # extracted source mesh. Retain the actual riser pad contact; copying the
  # source wrist delta makes the support palm float beside/above the sight.
  # W206 per-weapon mesh anchors opt in to the same rule for remodeled guns.
  if config['family']!='bow' and not settings.get('keepMeshSupport', False) and (dynamic or progress is None or progress in (0,1)):
   delta=vec(q,vec(C,sub(pos(j['leftWrist']),pos(j['rightWrist']))))
   anchor=right[ctx] if dynamic else base_right[ctx]
   scale=body_display[ctx]['scale'][0]
   left[ctx]['translation']=[round(anchor['translation'][i]+delta[i]*32*scale,8) for i in range(3)]
 return dynamic
