#!/usr/bin/env python3
"""Source-derived Devil's Lair Dreg-Light assets.
Current candidates use drive-dump -> drive-register -> drive-native, one species/cache
at a time. Original dump/bake/refresh modes are historical palette experiments,
NOT accepted production assets. Preserve existing rg_walker and its 50-bone rig.
All source extraction is read-only; caches and review evidence are separate.
"""
import argparse, importlib.util, json, math, os, sys, hashlib, subprocess
from pathlib import Path
SOURCE = Path('/Users/qf/Downloads/Devils-Lair-Strike-KO-2026-11-02')
REPO = Path(os.environ.get('DEVILS_REPO', str(Path(__file__).resolve().parents[2]) if Path(__file__).parent.name=='strikes' else '/Users/qf/IdeaProjects/DestinyGuardians'))
CACHE = Path('/tmp/devils-models-evidence')
NATIVE_CACHE = CACHE
DRIVE_HUMANOID_HASHES = {'Pedestal': '1A5C68E5', 'Pelvis': 'C7C0BA6E', 'Thigh.L': '695DAF09', 'Calf.L': '35B14D1B', 'Foot.L': '0F8B505D', 'Toe.L': '9D7EE73A', 'Thigh.R': '9F0FD28C', 'Calf.R': '8BD44A3F', 'Foot.R': 'B9B9E05D', 'Toe.R': '6B138432', 'Spine_1': 'A152A6A2', 'Spine_2': 'A252A6A2', 'Spine_3': 'A352A6A2', 'Clav.L': '038E2D3A', 'UpperArm.L': 'D1232BA2', 'ForeArm.L': '897A1504', 'Hand.L': '8C83CB67', 'Index_1.L': '512BAB0F', 'Index_2.L': '522BAB0F', 'Index_3.L': '532BAB0F', 'Pinky_1.L': '3C17867B', 'Pinky_2.L': '3F17867B', 'Pinky_3.L': '3E17867B', 'Thumb_1.L': '8961B2FD', 'Thumb_2.L': '8A61B2FD', 'Thumb_3.L': '8B61B2FD', 'Neck_1': '0D4EBB10', 'Neck_2': '0E4EBB10', 'Head': '7E92D640', 'Jaw': 'D27A97B2', 'Clav.R': 'A9D76416', 'UpperArm.R': '17025F50', 'ForeArm.R': 'A3781DCD', 'Hand.R': 'DE9D6BEA', 'Index_1.R': '63B2C7F1', 'Index_2.R': '60B2C7F1', 'Index_3.R': '61B2C7F1', 'Pinky_1.R': 'C22F2F1F', 'Pinky_2.R': 'C12F2F1F', 'Pinky_3.R': 'C02F2F1F', 'Thumb_1.R': '03394092', 'Thumb_2.R': '00394092', 'Thumb_3.R': '01394092', 'unk_238377640': 'A85A350E'}
MODELS = {'thrall':('80E1464C',1.9,2000), 'acolyte':('80E14679',2.05,2100),
 'knight':('80E14652',2.9,2400), 'wizard':('80E1060D',2.4,2200),
 'marauder':('80E1AFA1',2.3,2200), 'servitor':('80E109AF',2.6,1800),
 'walker':('80CC073C',5.5,3000), 'brig':('80E29EF1',5.5,3000), 'sepiks':('80E2A0BC',6.5,3000)}

# Reference-reviewed material roles. RGB values are authored D2 faction palette approximations,
# not recovered Bungie shader constants. Source texel value variation is retained per material.
COLOR_ROLES = {
 'thrall': {'80E23815':('bone_claws',(186,156,108)), '80E23810':('red_carapace',(106,46,39)), '80E2366A':('bone_skin',(178,147,101))},
 'acolyte': {'80A6DA8D':('weapon_chitin',(62,72,58)), '80A6DA89':('weapon_energy',(102,90,135)), '80E23DE6':('red_tabard',(115,29,42)), '80E2367F':('red_chitin',(149,43,52)), '80E240FA':('eyes',(180,208,130)), '80E240FD':('face_bone',(160,177,146)), '80E23694':('pale_hide',(171,181,158))},
 'knight': {'80A6DAB0':('weapon_chitin',(66,80,71)), '80A6DA96':('weapon_energy',(117,143,169)), '80E236FD':('red_chitin',(146,44,52)), '80E23B77':('pale_hide',(182,190,164)), '80E23DE6':('weathered_cloth',(100,108,94)), '80E23956':('face_bone',(158,174,144))},
 'wizard': {'80E23DB5':('under_hide',(94,111,94)), '80E23FA2':('red_chitin',(120,32,44)), '80E23FAF':('horn_bone',(163,145,101)), '80E23F9C':('inner_robe',(71,25,37)), '80E23FB6':('outer_robe',(91,99,88)), '80E23DAF':('face_bone',(137,151,113)), '80E23815':('claws',(156,142,109))},
 'marauder': {'80A6DB79':('blade_steel',(117,137,143)), '80CEA450':('arc_glass',(105,205,226)), '80E1D19D':('mask_steel',(140,139,129)), '80E1D61B':('cyan_optics',(115,223,255)), '80E1D61D':('bone_spines',(162,151,132)), '80E12FB9':('dusk_robe',(96,55,127)), '80E1D0A6':('dark_bandage',(63,55,66)), '80E1D357':('dark_leather',(80,57,45)), '80E1D1BF':('weathered_armour',(121,77,49)), '80E1D0AD':('shoulder_steel',(133,115,91)), '80E1D553':('helmet_rim',(131,131,126)), '80E12E20':('dusk_scarf',(99,59,135)), '80E1D621':('pale_dusk_emblem',(176,153,188)), '80E1D619':('lower_blade',(113,131,139)), '80E1D1A7':('boot_steel',(93,89,86)), '80E12FDB':('fallen_skin',(112,83,103)), '80E12FAA':('dusk_hood',(105,65,139))},
 'servitor': {'80E12AEB':('dusk_shell',(63,45,85)), '80E1D1B9':('bronze_struts',(151,99,57)), '80E1D1BC':('violet_inner',(100,62,133)), '80E12AEE':('inner_metal',(104,76,124))},
 'walker': {'80CA8D3D':('ochre_armour',(137,92,45)), '80CA8CC7':('dusk_paint',(93,54,121)), '80CA8CCA':('weathered_dusk_marking',(124,86,148)), '80CA8CDE':('vent_steel',(76,82,78)), '80CA8CEA':('engine_metal',(64,66,67)), '80CA8CE4':('cannon_steel',(78,85,79)), '80CA8CF2':('dark_mechanics',(61,64,58)), '80CA8CDB':('dark_mechanics',(61,64,58))},
 'brig': {'80E1137D':('leg_mechanics',(94,72,52)), '80E113D1':('steel_frame',(72,77,78)), '80E1130E':('rust_leg_armour',(143,85,49)), '80E1133A':('gun_dye_mask',(78,87,89)), '80E11316':('armour_trim',(125,83,58)), '80E11356':('waist_mechanics',(79,70,62)), '80E1135C':('dusk_shell',(110,76,124)), '80E1D07B':('engine_slots',(111,78,52)), '80E1D09E':('optics',(243,73,31)), '80E11355':('rust_shoulders',(139,81,46)), '80E1D621':('pale_dusk_plate',(151,122,158)), '80E1D081':('dark_fx',(54,47,65)), '80E1D082':('dark_fx',(54,47,65)), '80E1D092':('engine_trim',(119,78,47)), '80E112DA':('rear_armour',(102,73,56)), '80E1D095':('engine_trim',(119,78,47)), '80E1D07A':('neck_plate',(84,67,87)), '80E112D9':('dusk_banner',(67,37,90)), '80E1E257':('vents',(93,76,61)), '80E1138D':('cannon_body',(76,69,81)), '80E1D61F':('cannon_mechanics',(73,76,73)), '80E113A2':('leg_cables',(72,64,58)), '80E112DB':('gun_frame',(79,82,80))},
 'sepiks': {'80E37304':('bronze_struts',(148,98,51)), '80E134CC':('violet_inner',(91,58,121)), '80E37305':('dusk_shell',(69,51,92))}
}
REFERENCE_PAGES = {
 'thrall':'https://www.destinypedia.com/Thrall', 'acolyte':'https://www.destinypedia.com/Acolyte',
 'knight':'https://www.destinypedia.com/Knight', 'wizard':'https://www.destinypedia.com/Wizard',
 'marauder':'https://www.destinypedia.com/Marauder','servitor':'https://www.destinypedia.com/Servitor',
 'walker':'https://www.destinypedia.com/Walker','brig':'https://www.destinypedia.com/Brig','sepiks':'https://www.destinypedia.com/Sepiks_Prime'}

REFERENCE_IMAGES = {'brig': {'page': 'https://www.destinypedia.com/Brig', 'image_url': 'https://destiny.wiki.gallery/images/9/99/Brig4.jpg', 'sha256': 'c81e7474acd5fb15bde468550936b8ff13fc5fda46f32d2d6b7c7fb63c7010ee'}, 'walker': {'page': 'https://www.destinypedia.com/Walker', 'image_url': 'https://destiny.wiki.gallery/images/e/e1/Destiny2-FallenWalker-Render-01.jpg', 'sha256': '6d46ef534e2de6c0afaa192e2c034b5de545ed6b2c2763c6df458cbb5d766c54'}, 'marauder': {'page': 'https://www.destinypedia.com/Marauder', 'image_url': 'https://destiny.wiki.gallery/images/2/27/Dusk_Marauder_Closeup.jpg', 'sha256': 'b45ab599ff143d8001e0525ba0b3a2802160f538a71a0486e404487dc0f590fa'}, 'acolyte': {'page': 'https://www.destinypedia.com/Acolyte', 'image_url': 'https://destiny.wiki.gallery/images/d/d3/Acolyte_%28HS2%29.jpg', 'sha256': 'bbd51c8c2a38e0e352ca862090076f1ee76f9e6b5e9abb17caf3d1d15a673723'}, 'thrall': {'page': 'https://www.destinypedia.com/Thrall', 'image_url': 'https://destiny.wiki.gallery/images/c/cc/Thrall_%28HS2%29.jpg', 'sha256': 'c06f44099bc7a13a0134328c6dbee31ed56c460c3ba406d20fa278a031bb63ce'}, 'knight': {'page': 'https://www.destinypedia.com/Knight', 'image_url': 'https://destiny.wiki.gallery/images/a/a7/Knight_%28HS2%29.jpg', 'sha256': 'e1c74601d710a3d1e659de2545fcf0a16df542af100f021d18dfba3a3f035cbc'}, 'wizard': {'page': 'https://www.destinypedia.com/Wizard', 'image_url': 'https://destiny.wiki.gallery/images/8/87/Wizard_%28HS2%29.jpg', 'sha256': '940664a8db14ae710f778af573d1c1f8db51abf0c1e9cc584e49c1c51b61c176'}, 'servitor': {'page': 'https://www.destinypedia.com/Servitor', 'image_url': 'https://destiny.wiki.gallery/images/b/b8/K1DuskServitor.jpg', 'sha256': 'acff66555cc0ffde8ed5890741567f3439beaa02ae5d2ce9fab1f0522640b9b1'}, 'sepiks': {'page': 'https://www.destinypedia.com/Sepiks_Prime', 'image_url': 'https://destiny.wiki.gallery/images/2/29/SepiksD2.jpg', 'sha256': '430396115a2d97bdb167f72ccb668036384c8a13e0fb0b5d15ffb4df44b4b678'}}

def baker():
 spec=importlib.util.spec_from_file_location('dreglight',REPO/'scripts/campaign/bake_dreglight.py')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod

def spec_for(name,b):
 for mat,(role,rgb) in COLOR_ROLES[name].items():b.DUSK['dl_'+name+'_'+role]=tuple(c/255 for c in rgb)
 tag,height,cap=MODELS[name]; src=next((SOURCE/'models').glob('*__'+tag))
 bones=json.loads((SOURCE/'motions'/tag/'bones.json').read_text()); hashes={x['HashString'] for x in bones}
 if name=='walker':
  labels={0:'root',1:'body',2:'turret',13:'rear_hatch',22:'cannon'}
  for leg,chain in {'fl':[4,14,23,31,37],'ml':[6,16,25,32,38],'bl':[7,17,26,33,39],'fr':[9,18,27,34,40],'mr':[11,20,29,35,41],'br':[12,21,30,36,42]}.items():
   for segment,index in zip(('upper','lower','ankle','toe','tip'),chain):labels[index]='leg_'+leg+'_'+segment
  bone_map={labels.get(x['Index'],'part_'+str(x['Index'])):x['HashString'] for x in bones}
 elif name in ('servitor','sepiks'):
  bone_map={'root':'1A5C68E5', **{('shell_'+str(x['Index'])):x['HashString'] for x in bones if x['Index']>0}}
 else:
  bone_map={'root':'1A5C68E5',**{k:v for k,v in b.FALLEN_BONES.items() if v in hashes}, 'spine_mid':'A252A6A2','spine_upper':'A352A6A2'}
  if name=='wizard': bone_map.update({'robe_'+str(i):h for i,h in enumerate(['C61EEBE2','C51EEBE2','C41EEBE2','C31EEBE2'])})
  if name=='brig':
   # Separate armor and guns remain independently animated in the native rig.
   bone_map.update({'part_'+str(x['Index']):x['HashString'] for x in bones if x['ParentNodeIndex'] in (10,11,18) and x['HashString'] not in bone_map.values()})
 weapons={'acolyte':[('80CEA8A0','weapon','hand_r')],'knight':[('80CEAA13','weapon','hand_r')],'marauder':[('80A6DFDC','blade_r','hand_r'),('80A6DB65','blade_l','hand_l')]}.get(name,[])
 for prefix,weapon,socket in weapons:bone_map[weapon]=b.SOCKET[socket]
 inv={v:k for k,v in bone_map.items()}; by={x['HashString']:x for x in bones}; parents={}
 for n,h in bone_map.items():
  i=by[h]['ParentNodeIndex']
  while i>=0 and bones[i]['HashString'] not in inv:i=bones[i]['ParentNodeIndex']
  parents[n]=inv[bones[i]['HashString']] if i>=0 else None
 if name in ('servitor','sepiks'):parents.update({'eye_glow':'shell_12','eye_core_glow':'shell_12'})
 if name=='marauder':parents['eyes_glow']='head'
 if name=='brig':parents.update({'armor_plate':'spine_upper','weakpoint_glow':'spine_upper','optics_glow':'armor_plate'})
 if name=='walker':
  for leg in ('fl','ml','bl','fr','mr','br'):parents['leg_'+leg+'_upper_glow']='leg_'+leg+'_upper'
 result=dict(kind='native',src=src.name,include=[tag],weapons=[dict(prefix=p,bone=w,parent=so,socket=so) for p,w,so in weapons],roles=({'80CA8CF7':'legglow'} if name=='walker' else {'80E12AEC':'drop','80E1D1CA':'glow:eye_glow'} if name=='servitor' else {'80E37302':'drop','80E134BB':'glow:eye_glow'} if name=='sepiks' else {}),bones=bone_map,parents=parents,root='root',k=16,
             max_quads=cap,height=height,spacing_scale=(4.5 if name=='walker' else 1.0),fine=('head','hand_l','hand_r'),density=(.13 if name=='walker' else .23 if name in ('brig','sepiks') else .8), walls=6)
 result['roles'].update({mat:'dl_'+name+'_'+role for mat,(role,rgb) in COLOR_ROLES[name].items()})
 if name=='marauder':result['roles']['80E1D61B']='glow:eyes_glow'
 return result

def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def inputs(name):
 b=baker();sp=spec_for(name,b);tag=MODELS[name][0];src=SOURCE/'models'/sp['src'];motion=SOURCE/'motions'/tag
 files=[src/(sp['src']+'.fbx'),src/'source.json',motion/'native'/('rig_'+tag+'.fbx'),motion/'bones.json',motion/'original-clips.json',motion/'entity.json']
 files.extend(sorted(src.glob('Materials/*.slots.json')))
 for slot in src.glob('Materials/*.slots.json'):
  for t in json.loads(slot.read_text())['slots']:
   p=SOURCE/'model_textures'/(t['texture']+'.png')
   if t.get('srgb') and p.is_file():files.append(p)
 hero={'brig':'Brig','sepiks':'Sepiks_Prime','walker':'Walker'}.get(name)
 if hero:files.append(SOURCE/'hero_scenes'/(hero+'.blend'))
 return {str(p.relative_to(SOURCE)):sha(p) for p in sorted(set(files))}

def runtime_contract(name):
 if name=='brig':return {'hide_group':'armor_plate','weakpoint_group':'weakpoint_glow','weakpoint_center_blocks':[0,3.25,-1.05],'weakpoint_radius_blocks':.43,'weakpoint_provenance':'authored emissive disc; source-derived front shell partition only for armor_plate'}
 if name!='walker':return {}
 import numpy as np
 mesh=np.load(CACHE/'walker_mesh.npz');k=5.5/np.ptp(mesh['V'][...,2]);y0=-mesh['V'][...,2].min()*k;legs={}
 for leg,h in {'fl':'1ABE862E','ml':'B325CFF2','bl':'3D749CA1','fr':'5434883E','mr':'95404CDA','br':'138DAA1A'}.items():
  v=mesh['V'][mesh['BONE']==h].reshape(-1,3);v=np.stack([v[:,0]*k,v[:,2]*k+y0,-v[:,1]*k],1);lo,hi=v.min(0),v.max(0)
  legs[leg]={'bone':'leg_'+leg+'_lower','source_hash':h,'center_blocks':((lo+hi)/2).round(4).tolist(),'aabb_size_blocks':(hi-lo).round(4).tolist()}
 return {'height_blocks':5.5,'legs':legs,'coordinate_note':'model-space bind-pose; rotate by display yaw and add actor origin; not world or animated collision coordinates','core_source_hash':'7E92D640','core_idle_first_blocks':[-.0001,2.854,-2.3824],'core_exposed_first_blocks':[-.3846,1.4555,-2.8498],'core_exposed_mean_blocks':[-.4118,1.4542,-2.8455],'core_note':'native turret source locator; hitbox extent must be authored and reconciled with runtime exposed animation'}

def write_manifest(output):
 rows=[]
 for name in MODELS:
  path=output/('dl_'+name+'.bbmodel')
  if not path.is_file():continue
  model=json.loads(path.read_text());stat=json.loads((CACHE/(name+'_stats.json')).read_text())
  rows.append({'id':'dl_'+name,'file':path.name,'sha256':sha(path),'source_entity':MODELS[name][0],
   'six_leg_source_rig':(name=='walker'),'geometry':'source FBX depth-slice quads','rig_bones':stat['rig_bones'],'quads':len(model['elements']),
   'height_blocks':MODELS[name][1],'atlas':[2048,2048],'mean_luma':stat['mean_luma'],
   'runtime_clips':model['devils_lair']['runtime_clips'],'runtime_contract':runtime_contract(name),'reference_page':REFERENCE_PAGES[name],'reference_image':REFERENCE_IMAGES[name],'material_roles':COLOR_ROLES[name],'inputs':inputs(name),
   'limitations':['Minecraft visual and multiplayer performance verification pending','Authored fallback locomotion and hit/death overlays are identified per clip','Source shaders are approximated by sRGB albedo and explicit emissive lenses']})
 doc={'version':1,'source_root':SOURCE.name,'generator':'scripts/strikes/build_devils_models.py','generator_sha256':sha(__file__),
 'baker_sha256':sha(REPO/'scripts/campaign/bake_dreglight.py'),'baker_reference_handoff_sha256':sha(baker().HANDOFF),'technique':'Dreg-Light',
 'status':'candidate; requires integrated client review','models':rows}
 (output/'manifest.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n')

def verify(output):
 import base64,io
 from PIL import Image
 manifest=json.loads((output/'manifest.json').read_text());assert len(manifest['models'])==len(MODELS)
 for r in manifest['models']:
  p=output/r['file'];assert sha(p)==r['sha256'];m=json.loads(p.read_text());assert len(m['elements'])<=MODELS[m['name'][3:]][2]
  assert len({x['uuid'] for x in m['elements']})==len(m['elements'])
  for e in m['elements']:
   assert sum(e['from'][i]==e['to'][i] for i in range(3))>=1
   assert all(math.isfinite(v) for v in e['from']+e['to'])
   assert sum(v['texture'] is not None for v in e['faces'].values())==1
  if m['name']=='dl_walker':
   for leg in ('fl','ml','bl','fr','mr','br'):
    assert sum(e['name'].startswith('leg_'+leg+'_') for e in m['elements'])>40,leg
    assert any(e['name'].startswith('leg_'+leg+'_upper_glow') and e.get('light_emission')==15 for e in m['elements']),leg
  tex=Image.open(io.BytesIO(base64.b64decode(m['textures'][0]['source'].split(',')[1])));assert tex.size==(2048,2048)
  for rel,digest in r['inputs'].items():assert sha(SOURCE/rel)==digest,rel
  assert {'idle','walk','run','shoot','hit','damage','death','spawn'}<={a['name'] for a in m['animations']}
  for a in m['animations']:
   assert a['length']>0
   for an in a['animators'].values():
    for k in an['keyframes']:
     assert 0<=k['time']<=a['length']+1e-5
     assert all(math.isfinite(float(v)) for dp in k['data_points'] for v in dp.values())
  print('VERIFIED',r['id'],r['quads'],'quads',len(m['animations']),'clips')

def native_dump(name):
 import bpy,numpy as np
 from mathutils import Matrix
 b=baker(); spec=spec_for(name,b); tag=MODELS[name][0]
 b.GRIP_HAND_R=np.eye(4,dtype=float)
 b.SRC=str(SOURCE/'models');b.SPECS['dl_'+name]=spec
 out=CACHE/(name+'_mesh.npz')
 b._blender_main(['dump','dl_'+name,str(out)])
 d=dict(np.load(out,allow_pickle=True));d['mat_tex']=np.array([str(SOURCE/'model_textures'/next((x['texture']+'.png' for x in json.loads((SOURCE/'models'/spec['src']/'Materials'/(str(t)+'.slots.json')).read_text())['slots'] if x.get('srgb') and (SOURCE/'model_textures'/(x['texture']+'.png')).exists()),'')) for t in d['mats']])
 d['mat_tex']=np.array([str(p) if Path(str(p)).is_file() else '' for p in d['mat_tex']]);np.savez_compressed(out,**d)
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(SOURCE/'motions'/tag/'native'/('rig_'+tag+'.fbx')))
 arm=max((o for o in bpy.data.objects if o.type=='ARMATURE'),key=lambda o:len(o.data.bones))
 R=Matrix.Rotation(math.pi/2,4,'Z') @ Matrix.Rotation(-math.pi/2,4,'X') @ Matrix.Scale(100,4)
 for o in list(bpy.data.objects):
  if o.parent is None:o.matrix_world=R@o.matrix_world
 bpy.context.view_layer.update();arm.animation_data_create()
 names=[x.name for x in arm.data.bones]; rest=np.array([arm.matrix_world @ arm.data.bones[n].matrix_local for n in names])
 result={'names':np.array(names),'rest':rest};meta=[]
 for a in sorted(bpy.data.actions,key=lambda a:a.name):
  arm.animation_data.action=a
  if a.slots:arm.animation_data.action_slot=a.slots[0]
  f0,f1=map(lambda f:int(round(f)),a.frame_range); mats=[]
  for frame in range(f0,f1+1):
   bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
   mats.append(np.array([arm.matrix_world @ arm.pose.bones[n].matrix for n in names]))
  clip=a.name.split('|')[1];result['clip_'+clip]=np.array(mats)
  meta.append({'name':clip,'frames':len(mats),'fps':30,'source_action':a.name})
 result['meta']=json.dumps(meta);np.savez_compressed(CACHE/(name+'_motion.npz'),**result)
 (CACHE/(name+'_inputs.json')).write_text(json.dumps(inputs(name),sort_keys=True));print('DUMP_COMPLETE',name,len(meta),flush=True)

def bake_one(name,output):
 import numpy as np,shutil
 from PIL import Image
 assert json.loads((CACHE/(name+'_inputs.json')).read_text())==inputs(name),'source drift; re-run dump'
 b=baker();sp=spec_for(name,b);d=np.load(CACHE/(name+'_mesh.npz'),allow_pickle=True)
 if name in ('servitor','sepiks'):b.GLOW_RGB.update({'eye_glow':(157,81,255),'eye_core_glow':(235,215,255)})
 if name=='brig':b.GLOW_RGB['optics_glow']=(255,76,28)
 if name=='walker':b.GLOW_RGB.update({'leg_'+leg+'_upper_glow':(150,110,255) for leg in ('fl','ml','bl','fr','mr','br')})
 if name=='brig':b.GLOW_RGB['weakpoint_glow']=(255,112,65)
 sp['k']=sp['height']*16/float(np.ptp(d['V'][...,2])); b.SPECS['dl_'+name]=sp
 # The shared baker currently names caches by model. Our input hash validation runs before this copy.
 shutil.copyfile(CACHE/(name+'_mesh.npz'),'/tmp/r7_dump_dl_'+name+'.npz')
 class NativeBake(b.Bake):
  def __init__(self,key):
   super().__init__(key)
   if name=='brig':
    # Authored exposed core: source supplies shell/rig, but no shader-driven luminous core.
    center=self.m_of(0,3.25*16,-1.05*16);radius=.43*16/self.k
    self._add(self._cyl(center,radius,.06*16/self.k,1,n=12),'weakpoint_glow','AUTHORED_CORE','glow:weakpoint_glow')
    self._bones()
  def _bones(self):
   super()._bones()
   if name=='marauder':
    blade_materials={self.mats.index(m) for m in ('ShockBlade','ShockBladeVFX') if m in self.mats}
    for bone,hand in [('blade_l','8C83CB67'),('blade_r','DE9D6BEA')]:
     self.tri_bone[np.isin(self.MAT,list(blade_materials))&(self.bone_raw==hand)]=bone
   if name=='brig':
    c=self.V.mean(1);mask=(self.bone_raw=='A352A6A2')&(c[:,1]>.65)&(c[:,2]>2.6)
    self.tri_bone[mask]='armor_plate'
    optics=self.MAT==self.mats.index('80E1D09E');self.tri_bone[optics]='optics_glow';self.parent['optics_glow']='armor_plate';self.origin['optics_glow']=self.origin['armor_plate']
   if name in ('servitor','sepiks'):
    c=self.V.mean(1);center=1.38 if name=='servitor' else 3.44;rad=.23 if name=='servitor' else .48;mat='80E12AEB' if name=='servitor' else '80E134CC'
    mask=(self.MAT==self.mats.index(mat))&(c[:,0]**2+(c[:,2]-center)**2<rad**2)&(c[:,1]>(.7 if name=='servitor' else 1.5))
    if mask.any():self.tri_bone[mask]='eye_core_glow';self.parent['eye_core_glow']='shell_12';self.origin['eye_core_glow']=self.origin['shell_12']
  def authored_animations(self,groups):return []
  def planes(self):
   self._silhouettes={(r['bone'],r['face']):set(zip(r['gi'].tolist(),r['gj'].tolist())) for r in self.recs}
   super().planes()
  def image(self,p):
   # Extend each slice by one texel only within the original projected silhouette.
   # This closes oblique pinholes without enlarging the source silhouette.
   cells={tuple(a):c for a,c in zip(p['A'],p['C'])};support=self._silhouettes[(p['bone'],p['face'])];add={}
   for (x,y),color in cells.items():
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)):
     q=(x+dx,y+dy)
     if q in support and q not in cells and q not in add:add[q]=color
   cells.update(add);p=dict(p,A=np.array(list(cells)),C=np.array(list(cells.values())))
   return super().image(p)
  def recolour(self):
   super().recolour()
   # Dye masks are NOT albedo: carry their luminance detail, never their raw green/grey hue.
   # Compress the shared-material contrast so white mask regions do not clip to neon gold.
   luminances={}
   for r in self.recs:
    mids=self.MAT[self.S['tri'][r['win']]];lum=r['rgb']@np.array([.299,.587,.114])
    for mi in np.unique(mids):luminances.setdefault(int(mi),[]).append(lum[mids==mi])
   medians={mi:max(float(np.median(np.concatenate(v))),12.) for mi,v in luminances.items()}
   for r in self.recs:
    if r['bone'].endswith('_glow'):continue
    mids=self.MAT[self.S['tri'][r['win']]];lum=r['rgb']@np.array([.299,.587,.114]);c=r['col'].astype(float)
    for mi in np.unique(mids):
     tag=self.mats[int(mi)]
     if tag not in COLOR_ROLES[name]:continue
     mask=mids==mi;rgb=COLOR_ROLES[name][tag][1];detail=np.clip(lum[mask]/medians[int(mi)],.20,1.9)**.55;c[mask]=np.clip(np.array(rgb)*detail[:,None],0,255)
    r['col']=c.astype(np.uint8)

   if name=='brig':
    # Rip includes green dye masks in colour slots. Explicit approximate gunmetal treatment,
    # preserving mask value variation; this is not the original Destiny shader equation.
    for r in self.recs:
     c=r['col'].astype(float)
     if r['bone']=='weakpoint_glow':
      points=self.S['P'][r['win']];rad=np.sqrt(points[:,0]**2+(points[:,1]-3.25*16)**2)/(.43*16);hot=np.clip(1-rad,0,1)**.65
      c=np.array([205,38,12])+(np.array([255,244,182])-np.array([205,38,12]))*hot[:,None];r['col']=c.astype(np.uint8);continue
     r['col']=c.astype(np.uint8)

 modeler=NativeBake('dl_'+name).build()
 provenance={'technique':'Dreg-Light depth-slice quads','source':sp['src'],'palette':'reference-reviewed per-material House of Dusk / D2 Hidden Swarm dye roles; compressed source luminance detail, no raw dye-mask hue','authored_geometry':(['exposed Brig core, 12-sided emissive disc'] if name=='brig' else False),'crack_fill':'six depth walls plus one projected-silhouette-constrained texel dilation','material_approximations':['reference-based per-material tint, not recovered Bungie shader equations'],'reference_page':REFERENCE_PAGES[name],'reference_image':REFERENCE_IMAGES[name],'material_roles':COLOR_ROLES[name]}
 model=modeler.model(provenance);model['devils_lair']=model.pop('w300')
 model['animations'],mapping=runtime_clips(name,retarget(name,modeler,model));model['devils_lair']['runtime_clips']=mapping
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(model,separators=(',',':')))
 Image.fromarray(modeler.atlas).save(CACHE/(name+'_atlas.png'))
 stats={**modeler.stats,'model_height_blocks':sp['height'],'source_tag':MODELS[name][0], 'rig_bones':len(modeler.parent),'animations':len(model['animations'])}
 (CACHE/(name+'_stats.json')).write_text(json.dumps(stats,indent=2))
 print('BAKED',name,stats['quads'],stats['mean_luma'],flush=True)
 return stats

def retarget(name,bake,model):
 import numpy as np
 d=np.load(CACHE/(name+'_motion.npz'),allow_pickle=True)
 meta=json.loads(str(d['meta']));names=list(d['names']);idx={h:i for i,h in enumerate(names)}
 bm=bake.spec['bones']; out=[];basis=np.array([[1,0,0],[0,0,1],[0,-1,0]],float)
 groups={}
 def walk(g):
  groups[g['name']]=g
  for x in g['children']:
   if isinstance(x,dict):walk(x)
 for g in model['outliner']:walk(g)
 uid=baker()._uid
 for clip in meta:
  mats=d['clip_'+clip['name']]; animators={}; world={};orig={}
  for bone,h in bm.items():
   i=idx[h];rest=d['rest'][i].astype(float); ps=mats[:,i].astype(float);rs=ps[:,:3,:3]@np.linalg.inv(rest[:3,:3])
   # Remove numerical scale from FBX transforms; model bones have axis-aligned bind rotations.
   u,_,vh=np.linalg.svd(rs);rs=u@vh;world[bone]=basis@rs@basis.T
   orig[bone]=bake.to_px(ps[:,:3,3])
  for bone,h in bm.items():
   parent=bake.parent[bone]; wr=world[bone];origin=np.array(bake.origin[bone])
   if parent:
    pr=world[parent];rot=pr.transpose(0,2,1)@wr
    pos=np.einsum('tij,tj->ti',pr.transpose(0,2,1),orig[bone]-orig[parent])-(origin-np.array(bake.origin[parent]))
   else:rot=wr;pos=orig[bone]-origin
   # BB uses intrinsic ZYX Euler (Three Euler order ZYX); nearest continuous representation avoids 360 flips.
   sy=np.sqrt(rot[:,0,0]**2+rot[:,1,0]**2)
   angles=np.stack([np.arctan2(rot[:,2,1],rot[:,2,2]),np.arctan2(-rot[:,2,0],sy),np.arctan2(rot[:,1,0],rot[:,0,0])],axis=1)
   singular=sy<1e-7
   angles[singular,0]=np.arctan2(-rot[singular,1,2],rot[singular,1,1]);angles[singular,2]=0
   for f in range(1,len(angles)):
    primary=angles[f]; alternate=np.array([primary[0]+math.pi,math.pi-primary[1],primary[2]+math.pi]); candidates=[v+2*math.pi*np.round((angles[f-1]-v)/(2*math.pi)) for v in (primary,alternate)];angles[f]=min(candidates,key=lambda v:np.linalg.norm(v-angles[f-1]))
   # Reconstruct every sampled rotation before serialization; catch axis/order/branch mistakes.
   x,y,z=angles.T;cx,sx=np.cos(x),np.sin(x);cy,sy2=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z)
   check=np.stack([cz*cy,cz*sy2*sx-sz*cx,cz*sy2*cx+sz*sx,sz*cy,sz*sy2*sx+cz*cx,sz*sy2*cx-cz*sx,-sy2,cy*sx,cy*cx],axis=1).reshape(-1,3,3)
   assert np.max(np.abs(check-rot))<1e-5,(name,clip['name'],bone,'Euler reconstruction')
   if parent:
    reconstructed=orig[parent]+np.einsum('tij,tj->ti',world[parent],pos+origin-np.array(bake.origin[parent]))
    assert np.max(np.abs(reconstructed-orig[bone]))<1e-5,(name,clip['name'],bone,'FK reconstruction')
   angles=np.rad2deg(angles)
   keys=[]
   for channel,values in [('rotation',angles),('position',pos)]:
    for f,value in enumerate(values):
     if f not in (0,len(values)-1) and np.max(np.abs(value-values[f-1]))<1e-5 and np.max(np.abs(value-values[f+1]))<1e-5:continue
     keys.append({'channel':channel,'time':round(f/30,6),'interpolation':'linear','uuid':uid('dl_'+name,clip['name'],bone,channel,f),'data_points':[dict(zip('xyz',[round(float(x),5) for x in value]))]})
   animators[groups[bone]['uuid']]={'name':bone,'type':'bone','keyframes':keys}
  out.append({'name':'source_'+clip['name'].lower(),'uuid':uid('dl_'+name,clip['name']),'length':max(1/30,(clip['frames']-1)/30),'loop':'once','animators':animators})
 return out

def runtime_clips(name, clips):
 import copy
 uid=baker()._uid
 ids={c['name'].split('_')[1]:c for c in clips}
 aliases={
  'thrall': {'idle':'80e138b7','melee':'80e13b36'},
  'acolyte': {'melee':'80e13bb9'}, 'knight': {'melee':'80e13aa2'},
  'wizard': {'idle':'80e13d5e','new_target':'80e13d5a'},
  'marauder': {'melee':'80e11013'},
  'servitor': {'idle':'80e10740','taunt':'80e1073e','brace':'80e1074a'},
  'walker': {'idle':'80a8af52','walk':'80a8af53','shoot':'80a8af5f','fire':'80a8af5f','death':'80a8af5b','exposed':'80a8af5d','expose_enter':'80a8af65','weakpoint_open':'80a8af65','leg_break':'80a8af65','charge':'80a8af5f','recover':'80a8af60','spawn':'80a8af61','emp':'80a8af67'},
  'brig': {'idle':'80e15e2e','aoe':'80e15ded','exposed':'80e15de9','recover':'80e15df3','armor_break':'80e15dee','weakpoint_open':'80e15de9','charge':'80e15ded','evade_left':'80e15e0b','evade_right':'80e15e0a'},
  'sepiks': {'idle':'80e10767','spawn':'80e10752','shield':'80e10756','teleport':'80e10764','teleport_end':'80e1075f','soul_suck':'80e10761','soul_suck_end':'80e10768','aoe':'80e10765'}
 }[name]
 mapping={}; result=list(clips)
 for new,tag in aliases.items():
  if tag not in ids:raise ValueError((name,new,tag))
  a=copy.deepcopy(ids[tag]);a['name']=new;a['uuid']=uid('dl_'+name,'alias',new)
  a['loop']='loop' if new in ('idle','walk','shield','exposed') else 'once'
  result.append(a);mapping[new]={'source_clip':tag.upper(),'method':'native sampled base clip'}
 seedtag={'acolyte':'80e13784','knight':'80e1040c','marauder':'80e11013'}.get(name)
 seed=ids[seedtag] if seedtag else next(c for c in result if c['name']=='idle')
 def pose_channel(an,ch,last=False):
  keys=[k for k in an['keyframes'] if k['channel']==ch]
  k=(max if last else min)(keys,key=lambda k:k['time'])
  return [float(k['data_points'][0][v]) for v in 'xyz']
 last=name in ('knight','marauder')
 def author(action,length,loop=False):
  a={'name':action,'uuid':uid('dl_'+name,'authored',action),'length':length,'loop':'loop' if loop else 'once','animators':{}}
  for boneid,an in seed['animators'].items():
   bone=an['name'];kfs=[]
   for f in range(31):
    t=f/30;theta=t*2*math.pi; pos=pose_channel(an,'position',last);rot=pose_channel(an,'rotation',last)
    if action in ('walk','run'):
     if name in ('wizard','servitor','sepiks'):
      if bone=='root':pos[1]+=.6*math.sin(theta)
     else:
      sign=1 if bone.endswith('_l') else -1
      if bone.startswith('thigh_'):rot[0]+=sign*math.sin(theta)*(24 if action=='run' else 16)
      if bone.startswith('shin_'):rot[0]+=max(0,-sign*math.sin(theta))*20
      if bone=='hips':pos[1]+=.35*(1-math.cos(theta*2))
    elif action=='idle':
     if bone in ('chest','spine_upper'):rot[0]+=.6*math.sin(theta)
    elif action in ('shoot','fire'):
     if bone in ('chest','spine_upper'):rot[0]-=4*math.sin(math.pi*t)**2
    elif action in ('hit','damage','stagger'):
     if bone in ('chest','spine_upper') or name=='walker' and bone=='body':rot[0]-=8*math.sin(math.pi*t)
    elif action=='death':
     if bone=='root':rot[0]+=85*t;pos[1]-=3*t
    elif action=='spawn':
     if bone=='root':pos[1]-=2*(1-t)**2
    for channel,vals in [('rotation',rot),('position',pos)]:
     kfs.append({'channel':channel,'time':round(length*t,6),'interpolation':'linear','uuid':uid('dl_'+name,action,bone,channel,f),'data_points':[dict(zip('xyz',[round(v,5) for v in vals]))]})
   a['animators'][boneid]={'name':bone,'type':'bone','keyframes':kfs}
  result.append(a);mapping[action]={'method':'authored display animation over source reference pose','reference_clip':seed['name']}
 for action,length,loop in [('idle',3,True),('walk',1,True),('run',.65,True),('shoot',.4,False),('fire',.4,False),('hit',.35,False),('damage',.35,False),('stagger',.5,False),('death',1.3,False),('spawn',.7,False)]:
  if action not in aliases:
   if name=='walker' and action=='run':
    a=copy.deepcopy(next(c for c in result if c['name']=='walk'));a['name']='run';a['uuid']=uid('dl_walker','alias','run');a['length']*=.72
    for an in a['animators'].values():
     for k in an['keyframes']:k['time']*=.72
    result.append(a);mapping['run']={'source_clip':'80A8AF53','method':'native locomotion sped to 0.72 duration'}
   else:author(action,length,loop)
 return result,mapping

def refresh_one(name,output):
 import numpy as np,shutil
 assert json.loads((CACHE/(name+'_inputs.json')).read_text())==inputs(name),'source drift; re-run dump'
 b=baker();sp=spec_for(name,b);d=np.load(CACHE/(name+'_mesh.npz'),allow_pickle=True)
 if name in ('servitor','sepiks'):b.GLOW_RGB.update({'eye_glow':(157,81,255),'eye_core_glow':(235,215,255)})
 if name=='brig':b.GLOW_RGB['optics_glow']=(255,76,28)
 if name=='walker':b.GLOW_RGB.update({'leg_'+leg+'_upper_glow':(150,110,255) for leg in ('fl','ml','bl','fr','mr','br')})
 if name=='brig':b.GLOW_RGB['weakpoint_glow']=(255,112,65)
 sp['k']=sp['height']*16/float(np.ptp(d['V'][...,2]));b.SPECS['dl_'+name]=sp
 shutil.copyfile(CACHE/(name+'_mesh.npz'),'/tmp/r7_dump_dl_'+name+'.npz')
 modeler=b.Bake('dl_'+name);model=json.loads(output.read_text())
 model['animations'],mapping=runtime_clips(name,retarget(name,modeler,model));model['devils_lair']['runtime_clips']=mapping
 model['devils_lair'].update(reference_page=REFERENCE_PAGES[name],reference_image=REFERENCE_IMAGES[name],material_roles=COLOR_ROLES[name])
 output.write_text(json.dumps(model,separators=(',',':')))
 print('REFRESHED',name,len(model['animations']),flush=True)

def motion_evidence(name,output):
 """Offline source-vs-serialized-bone FK strips. Not a Minecraft render."""
 import numpy as np
 from PIL import Image,ImageDraw
 model=json.loads((output/('dl_'+name+'.bbmodel')).read_text());groups={};parents={}
 def walk(g,parent=None):
  groups[g['name']]=g;parents[g['name']]=parent
  for child in g['children']:
   if isinstance(child,dict):walk(child,g['name'])
 for g in model['outliner']:walk(g)
 animations={a['name']:a for a in model['animations']};native=next((a for a in animations.values() if a['name']=='melee'),animations['idle'])
 native=animations[{'walker':'walk','brig':'aoe','sepiks':'spawn'}.get(name,native['name'])]
 mapping=model['devils_lair']['runtime_clips'].get(native['name'],{});tag=mapping.get('source_clip')
 if not tag:
  tag=mapping['reference_clip'].split('_')[1].upper()
 source=np.load(CACHE/(name+'_motion.npz'),allow_pickle=True);meta=json.loads(str(source['meta']));clip=next(m for m in meta if m['name'].split('_')[0]==tag)
 mats=source['clip_'+clip['name']];idx={h:i for i,h in enumerate(source['names'])};sp=spec_for(name,baker());stats=json.loads((CACHE/(name+'_stats.json')).read_text());basis=np.array([[1,0,0],[0,0,1],[0,-1,0]],float)
 def vals(an,ch,t):
  keys=sorted((k for k in an['keyframes'] if k['channel']==ch),key=lambda k:k['time']);times=[k['time'] for k in keys]
  values=np.array([[float(k['data_points'][0][v]) for v in 'xyz'] for k in keys]);return np.array([np.interp(t,times,values[:,i]) for i in range(3)])
 def pose(a,t):
  ans={v['name']:v for v in a['animators'].values()};result={};rots={}
  def bone(n):
   if n in result:return
   g=groups[n];pa=parents[n];origin=np.array(g['origin']);pos=np.zeros(3);angles=np.zeros(3)
   if n in ans:pos=vals(ans[n],'position',t);angles=np.radians(vals(ans[n],'rotation',t))
   x,y,z=angles;cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z)
   r=np.array([[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],[sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],[-sy,cy*sx,cy*cx]])
   if pa:
    bone(pa);result[n]=result[pa]+rots[pa]@(origin-np.array(groups[pa]['origin'])+pos);rots[n]=rots[pa]@r
   else:result[n]=origin+pos;rots[n]=r
  for n in groups:bone(n)
  return result
 frames=np.linspace(0,len(mats)-1,5).astype(int);rows=[]
 srcanim=next(a for a in animations.values() if a['name'].startswith('source_'+tag.lower()))
 maxerr=0
 for frame in frames:
  sourcepose={n:basis@mats[frame,idx[h],:3,3]*stats['k']+np.array([0,stats['y0'],0]) for n,h in sp['bones'].items()}
  bakedpose=pose(srcanim,frame/30);maxerr=max(maxerr,max(float(np.linalg.norm(sourcepose[n]-bakedpose[n])) for n in sourcepose));rows.append((sourcepose,bakedpose))
 assert maxerr<.002,(name,'serialized FK residual',maxerr)
 canvas=Image.new('RGB',(1500,850),(25,29,35));draw=ImageDraw.Draw(canvas)
 def drawpose(points,x,y):
  coords=np.array(list(points.values()));lo=coords.min(0);hi=coords.max(0);scale=min(245/max(hi[0]-lo[0],1),325/max(hi[1]-lo[1],1));center=(lo+hi)/2
  def xy(p):return (x+150+(p[0]-center[0])*scale,y+185-(p[1]-center[1])*scale)
  for n,p in points.items():
   pa=parents.get(n)
   if pa in points:draw.line([xy(p),xy(points[pa])],fill=(125,207,255),width=3)
   xx,yy=xy(p);draw.ellipse((xx-3,yy-3,xx+3,yy+3),fill=(240,215,122))
 for i,(src,baked) in enumerate(rows):
  draw.text((i*300+10,12),f'{name} source {tag} frame {frames[i]}',fill='white');drawpose(src,i*300,35)
  draw.text((i*300+10,425),'serialized BB skeleton / offline',fill='white');drawpose({n:baked[n] for n in src},i*300,445)
 draw.text((15,825),f'Max sampled FK residual: {maxerr:.6f} px; does not verify BetterModel Euler convention or in-game clip feel.',fill='white')
 canvas.save(CACHE/(name+'_retarget_comparison.png'));print('MOTION_FK',name,maxerr,flush=True)


def drive_shader_dump(name):
 import bpy,json,numpy as np,hashlib,os
 from pathlib import Path
 from mathutils import Vector
 srcroot=Path(bpy.data.filepath).parent
 shader_images=set()
 def collect_images(tree,seen):
  if not tree or tree.name in seen:return
  seen.add(tree.name)
  for node in tree.nodes:
   if node.type=='TEX_IMAGE' and node.image:shader_images.add(node.image)
   if node.type=='GROUP':collect_images(node.node_tree,seen)
 for material in bpy.data.materials:
  if material.use_nodes:collect_images(material.node_tree,set())
 for image in bpy.data.images:
  if image.source=='FILE':
   relative=image.filepath.replace('\\','/')
   candidate=srcroot/relative[2:] if relative.startswith('//') else Path(relative)
   if not candidate.is_file():candidate=srcroot/Path(relative).name
   if not candidate.is_file():candidate=srcroot/image.name.removesuffix('.001').removesuffix('.002')
   if not candidate.is_file():
    matches=list(srcroot.rglob(Path(relative).name))
    if not matches:matches=list(srcroot.parent.rglob(Path(relative).name))
    if len(matches)==1:candidate=matches[0]
   if candidate.is_file():image.filepath=str(candidate);image.reload()
   elif not image.packed_file and image in shader_images:raise FileNotFoundError('Unresolved source shader image: '+image.filepath)
 # Compatibility repair in the temporary evaluated scene only. Legacy cutout branches
 # have an opacity-mask Factor but an unconnected transparent-side closure.
 repairs=[]
 for material in bpy.data.materials:
  if not material.use_nodes:continue
  tree=material.node_tree
  for node in list(tree.nodes):
   if node.type=='MIX_SHADER' and node.inputs[0].is_linked and not node.inputs[1].is_linked and node.inputs[2].is_linked:
    transparent=tree.nodes.new('ShaderNodeBsdfTransparent');tree.links.new(transparent.outputs[0],node.inputs[1]);repairs.append({'material':material.name,'node':node.name,'repair':'restore transparent closure on zero-opacity mask branch','factor_source':[(l.from_node.name,l.from_socket.name) for l in node.inputs[0].links]})
 out=CACHE;out.mkdir(parents=True,exist_ok=True);scene=bpy.context.scene
 scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.device='CPU';scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 if name in ('acolyte','knight'):
  # The delivered blend contains weapon shaders, but no weapon mesh. Use the original
  # supplied native weapon mesh/UVs at its source hand socket; retain source provenance.
  native=np.load(NATIVE_CACHE/(name+'_mesh.npz'));mask=np.array([str(b).startswith('WPN:weapon') for b in native['BONE']]);scale=1.0286287699437537 if name=='knight' else 1.
  V=native['V'][mask].reshape(-1,3)*scale*np.array([-1.,-1.,1.]);UV=native['UV'][mask].reshape(-1,2)
  mesh=bpy.data.meshes.new('native_weapon_geometry');mesh.from_pydata(V,[],[list(range(i,i+3)) for i in range(0,len(V),3)]);mesh.update();obj=bpy.data.objects.new('native_'+name+'_weapon',mesh);scene.collection.objects.link(obj);uv=mesh.uv_layers.new(name='uv');uv.data.foreach_set('uv',UV.reshape(-1));mesh.materials.append(bpy.data.materials['HiveBoomer' if name=='knight' else 'HiveAcolyteShredder']);group=obj.vertex_groups.new(name='Hand.R');group.add(list(range(len(V))),1.,'REPLACE')
  repairs.append({'weapon_source':'original delivered native '+name+' weapon mesh and UVs','triangles':int(mask.sum()),'shader':'Drive HiveBoomer' if name=='knight' else 'Drive HiveAcolyteShredder','scale':scale,'attachment':'source Hand.R socket'})
 if name=='marauder':
  # Delivered editable scene shows a launcher and one unbound blade. Restore the
  # supplied combat loadout: two native blade meshes at their audited hand sockets.
  for obj in list(bpy.data.objects):
   if obj.type=='MESH' and any(m and m.name in ('ShrapnelLauncher','ShrapnelRifleVFX_01','ShockBlade','ShockBladeVFX') for m in obj.data.materials):
    obj.hide_render=True;obj.hide_set(True)
  native=np.load(NATIVE_CACHE/'marauder_mesh.npz')
  for blade,hand in [('blade_l','hand.l'),('blade_r','hand.r')]:
   mask=native['BONE']=='WPN:'+blade
   V=native['V'][mask].reshape(-1,3)*np.array([-1.,-1.,1.]);UV=native['UV'][mask].reshape(-1,2)
   mesh=bpy.data.meshes.new('native_'+blade);mesh.from_pydata(V,[],[list(range(i,i+3)) for i in range(0,len(V),3)]);mesh.update()
   obj=bpy.data.objects.new('native_'+blade,mesh);scene.collection.objects.link(obj);uv=mesh.uv_layers.new(name='uv');uv.data.foreach_set('uv',UV.reshape(-1))
   for mat in ('ShockBlade','ShockBladeVFX'):mesh.materials.append(bpy.data.materials[mat])
   for face,mi in zip(mesh.polygons,native['MAT'][mask]):face.material_index=1 if native['mats'][mi]=='80CEA450' else 0
   obj.vertex_groups.new(name=hand).add(list(range(len(V))),1.,'REPLACE')
   repairs.append({'weapon_source':'original supplied native '+blade+' mesh and UVs','triangles':int(mask.sum()),'shader':['Drive ShockBlade','Drive ShockBladeVFX'],'attachment':hand})
 if name=='brig':
  # Authored Dusk adaptation through original dye/overlay shader inputs, never flat albedo replacement.
  changes={'FallenBrigBody_02':{'Group.001':('Color',(.12,.05,.22,1)),'Group.002':('Color',(.27,.12,.045,1))},'FallenBrigBody_05':{'Group.001':('Color',(.30,.125,.05,1))},'FallenBrigBody_03':{'Group.001':('Diffuse',(.095,.065,.045,1))}}
  for mat,entries in changes.items():
   for nod,(sock,color) in entries.items():
    node=bpy.data.materials[mat].node_tree.nodes[nod];assert not node.inputs[sock].is_linked;old=list(node.inputs[sock].default_value);node.inputs[sock].default_value=color;repairs.append({'material':mat,'node':nod,'input':sock,'old':old,'Dusk_authored_dye':color})
  for mat,color in [('FallenBrigBody_01',(.17,.075,.28,1)),('FallenBrigBody_05',(.33,.16,.07,1)),('FallenBrigBody_03',(.38,.18,.065,1))]:
   material=bpy.data.materials[mat];tree=material.node_tree;bs=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED');link=bs.inputs['Base Color'].links[0];upstream=link.from_socket;mix=tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1.;mix.inputs[2].default_value=color;tree.links.new(upstream,mix.inputs[1]);tree.links.new(mix.outputs[0],bs.inputs['Base Color']);repairs.append({'material':material.name,'Dusk_authored_dye':'multiplication over original textured Base Color; normal/roughness/metal masks unchanged','tint':color})
 
 deps=bpy.context.evaluated_depsgraph_get()
 rigs={'names':[b.name for b in rig.data.bones],'parents':[b.parent.name if b.parent else '' for b in rig.data.bones],'rest':[list(map(list,rig.matrix_world@rig.pose.bones[b.name].matrix)) for b in rig.data.bones]}
 meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.data.materials and o.vertex_groups and not o.hide_render and o.name in bpy.context.view_layer.objects and o.visible_get()]
 # Evaluate source rig once, preserving source shaders and vertex-group membership; do not save the source.
 for o in meshes:
  ev=o.evaluated_get(deps);me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=deps);o.modifiers.clear();o.data=me
  source_uv=next((u for u in me.uv_layers if u.active_render),me.uv_layers.active);assert source_uv is not None,o.name
  values=np.empty(len(source_uv.data)*2,dtype=np.float32);source_uv.data.foreach_get('uv',values);shared=me.uv_layers.new(name='__source_active_uv');shared.data.foreach_set('uv',values)
 for o in bpy.context.selected_objects:o.select_set(False)
 for o in meshes:o.select_set(True)
 bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join();obj=bpy.context.object
 # Explicit original UV nodes prevent the output atlas becoming an accidental input UV.
 seen_trees=set()
 def fix_source_uv(tree):
  if tree.as_pointer() in seen_trees:return
  seen_trees.add(tree.as_pointer());uv=tree.nodes.new('ShaderNodeUVMap');uv.uv_map='__source_active_uv'
  for node in list(tree.nodes):
   if node.type=='TEX_COORD':
    for link in list(node.outputs['UV'].links):tree.links.new(uv.outputs['UV'],link.to_socket)
   if node.type=='TEX_IMAGE' and not node.inputs['Vector'].is_linked:tree.links.new(uv.outputs['UV'],node.inputs['Vector'])
   if node.type=='GROUP':fix_source_uv(node.node_tree)
 for material in obj.data.materials:
  if material and material.use_nodes:fix_source_uv(material.node_tree)
 obj.data.uv_layers.new(name='shader_bake');obj.data.uv_layers.active_index=len(obj.data.uv_layers)-1
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.00001);bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.001);bpy.ops.object.mode_set(mode='OBJECT')
 scene.world=bpy.data.worlds.new('QA neutral world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.12,.12,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=1.
 verts=np.array([list(obj.matrix_world@v.co) for v in obj.data.vertices]);lo,hi=verts.min(0),verts.max(0);c=(lo+hi)/2;h=max(hi-lo)
 for o in list(scene.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 for v,power in [((-1,-2,3),1400),((2,0,1),700)]:
  bpy.ops.object.light_add(type='AREA',location=c+np.array(v)*h);light=bpy.context.object;light.data.energy=power*h*h;light.data.shape='DISK';light.data.size=h*2;light.rotation_euler=(Vector(c)-light.location).to_track_quat('-Z','Y').to_euler()
 for o in bpy.context.selected_objects:o.select_set(False)
 obj.select_set(True);bpy.context.view_layer.objects.active=obj
 original_outputs=[];emission_materials=[];pure_emission_materials=[]
 for material in obj.data.materials:
  tree=material.node_tree
  positive=any(n.type=='EMISSION' and (n.inputs['Strength'].is_linked or n.inputs['Strength'].default_value>0) for n in tree.nodes)
  opaque=any(n.type.startswith('BSDF_') and n.type!='BSDF_TRANSPARENT' for n in tree.nodes)
  if positive and not opaque:pure_emission_materials.append(material.name)
 for mode in ['COMBINED','EMIT']:
  if mode=='EMIT':
   for material in obj.data.materials:
    tree=material.node_tree;outputs=[node for node in tree.nodes if node.type=='OUTPUT_MATERIAL']
    emitters=[node for node in tree.nodes if node.type=='EMISSION' and (node.inputs['Strength'].is_linked or node.inputs['Strength'].default_value>0)]
    for output in outputs:
     original_outputs.append((tree,output,output.inputs['Surface'].links[0].from_socket if output.inputs['Surface'].is_linked else None))
     if emitters:
      emitter=emitters[0];emission_materials.append(material.name)
     else:
      emitter=tree.nodes.new('ShaderNodeEmission');emitter.inputs['Color'].default_value=(0,0,0,1)
     tree.links.new(emitter.outputs[0],output.inputs['Surface'])
  im=bpy.data.images.new('source_'+mode,width=4096,height=4096,alpha=True);im.colorspace_settings.name='sRGB'
  for m in obj.data.materials:
   if not m or not m.use_nodes:continue
   node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;m.node_tree.nodes.active=node
  scene.render.bake.use_clear=True;scene.render.bake.margin=3;scene.render.bake.use_pass_direct=True;scene.render.bake.use_pass_indirect=True;scene.render.bake.use_pass_color=True
  bpy.ops.object.bake(type=mode,uv_layer='shader_bake');im.filepath_raw=str(out/(mode.lower()+'.png'));im.save_render(im.filepath_raw,scene=scene);print('BAKED SOURCE',mode,flush=True)
 for tree,output,socket in original_outputs:
  if socket:tree.links.new(socket,output.inputs['Surface'])
 me=obj.data;me.calc_loop_triangles();uv=me.uv_layers['shader_bake'];V=[];UV=[];B=[];VB=[];MAT=[]
 for t in me.loop_triangles:
  vi=list(t.vertices);V.append([list(obj.matrix_world@me.vertices[i].co) for i in vi]);UV.append([list(uv.data[i].uv) for i in t.loops]);bones=[]
  for i in vi:
   groups=me.vertices[i].groups;bones.append(obj.vertex_groups[max(groups,key=lambda g:g.weight).group].name if groups else 'Pedestal')
  VB.append(bones);B.append(max(set(bones),key=bones.count));MAT.append(t.material_index)
 basis=np.diag([-1.,-1.,1.,1.]) if os.environ.get('DEVILS_ROTATE_Z','180')=='180' else np.eye(4);V=np.asarray(V)@basis[:3,:3].T;rigs['rest']=[(basis@np.array(m)).tolist() for m in rigs['rest']]
 np.savez_compressed(out/'shader_mesh.npz',V=V,UV=UV,MAT=MAT,BONE=B,VBONE=VB,names=rigs['names'],parents=rigs['parents'],rest=rigs['rest'],mats=[m.name for m in obj.data.materials],mat_tex=[str(out/'combined.png')]*len(obj.data.materials))
 (out/'shader-bake.json').write_text(json.dumps({'pipeline_version':4,'emission_materials':emission_materials,'pure_emission_materials':pure_emission_materials,'emission_bake':'actual positive-strength source Emission node evaluated directly, separate from additive transparency closure','compatibility_repairs':repairs,'source_blend':bpy.data.filepath,'source_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'resolved_shader_images':[{ 'path':im.filepath,'sha256':hashlib.sha256(Path(im.filepath).read_bytes()).hexdigest()} for im in bpy.data.images if im.source=='FILE' and Path(im.filepath).is_file()],'triangles':len(V),'bounds':[lo.tolist(),hi.tolist()],'rig':rigs,'lighting':'authored neutral QA lighting; source graphs preserved except recorded UV/compatibility repairs and authored Brig dyes; combined plus separate emission bake','animations':'source blend has no actions; dump stores rig only; drive-native separately retargets original delivered native clips'},indent=2))
 # Save temporary evaluated QA scene for exact same source/candidate camera comparisons.
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'evaluated-qa.blend'));print('DONE SOURCE',len(V),flush=True)

def drive_shader_project(name):
 import numpy as np,json,sys,importlib.util,shutil,os
 from pathlib import Path
 from PIL import Image
 P=CACHE;repo=REPO;key='dl_'+name+'_drive'
 s=importlib.util.spec_from_file_location('b',repo/'scripts/campaign/bake_dreglight.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
 d=np.load(P/'shader_mesh.npz');names=list(map(str,d['names']));safe=lambda n:n.lower().replace(' ','_').replace('.','_')
 bones={safe(n):n for n in names};parents={safe(n):safe(str(p)) if str(p) else None for n,p in zip(names,d['parents'])}
 roles={};extra={}
 for i,m in enumerate(d['mats']):
  if any(k in m for k in ('Light','Inside','Eye','Core','Magic','VFX')):
   for n in set(d['BONE'][d['MAT']==i]):extra[safe(str(n))+'_glow']=safe(str(n))
 parents.update(extra)
 if name=='thrall':
  # Keep the source mesh intact; collapse finger/helper rig only, freeing slice budget for silhouettes.
  keep={'Pedestal','Pelvis','Spine_2','Spine_3','Head','Jaw'}|{part+'.'+side for part in ['Thigh','Calf','Foot','UpperArm','ForeArm','Hand'] for side in ['L','R']}
  rawparents=dict(zip(names,map(str,d['parents'])));bones={safe(n):n for n in names if n in keep};parents={}
  for n in keep:
   parent=rawparents[n]
   while parent and parent not in keep:parent=rawparents[parent]
   parents[safe(n)]=safe(parent) if parent else None
 
 b.SPECS[key]=dict(kind='native',src=str(SOURCE),bones=bones,parents=parents,root=safe(str(d['names'][0])),roles=roles,k=MODELS[name][1]*16/np.ptp(d['V'][...,2]),max_quads=MODELS[name][2],density=(.23 if name in ('brig','sepiks') else .8),spacing_scale=(.45 if name=="thrall" else 1.0),walls=(2 if name=="thrall" else 6),fine=())
 shutil.copyfile(P/'shader_mesh.npz','/tmp/r7_dump_'+key+'.npz')
 class ShaderBake(b.Bake):
  def samples(self):
   super().samples()
   # The shader bake carries cutout/transparency. RGB-only sampling made transparent decals black.
   tri=self.S['tri'];T=self.to_px(self.V)[tri];q=self.S['P']-T[:,0];v0=T[:,1]-T[:,0];v1=T[:,2]-T[:,0]
   a=np.einsum('ij,ij->i',v0,v0);b0=np.einsum('ij,ij->i',v0,v1);c=np.einsum('ij,ij->i',v1,v1);d0=np.einsum('ij,ij->i',q,v0);e=np.einsum('ij,ij->i',q,v1);den=a*c-b0*b0
   u=np.divide(c*d0-b0*e,den,out=np.zeros_like(den),where=abs(den)>1e-12);v=np.divide(a*e-b0*d0,den,out=np.zeros_like(den),where=abs(den)>1e-12);uv=self.UV[tri,0]+u[:,None]*(self.UV[tri,1]-self.UV[tri,0])+v[:,None]*(self.UV[tri,2]-self.UV[tri,0])
   rgba=np.asarray(Image.open(P/'combined.png').convert('RGBA'));h,w=rgba.shape[:2];xx=(np.mod(uv[:,0],1)*w).astype(int)%w;yy=((1-np.mod(uv[:,1],1))*h).astype(int)%h;keep=rgba[yy,xx,3]>=128
   self.stats['transparent_source_samples_removed']=int((~keep).sum());self.S={key:value[keep] for key,value in self.S.items()};self.stats['samples']=int(keep.sum())
  def _bones(self):
   super()._bones()
   for i,m in enumerate(self.mats):
    if any(k in m for k in ('Light','Inside','Eye','Core','Magic','VFX')):
     mask=self.MAT==i
     for n in set(self.tri_bone[mask]):
      g=n+'_glow';self.tri_bone[mask&(self.tri_bone==n)]=g;self.parent[g]=n;self.origin[g]=self.origin[n]
  def planes(self):
   self._silhouettes={(r['bone'],r['face']):set(zip(r['gi'].tolist(),r['gj'].tolist())) for r in self.recs}
   super().planes()
  def image(self,p):
   cells={tuple(a):c for a,c in zip(p['A'],p['C'])};support=self._silhouettes[(p['bone'],p['face'])];add={}
   for (x,y),color in cells.items():
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)):
     q=(x+dx,y+dy)
     if q in support and q not in cells and q not in add:add[q]=color
   cells.update(add);p=dict(p,A=np.array(list(cells)),C=np.array(list(cells.values())))
   return super().image(p)
  def recolour(self):
   # No tint, role palette, gamma floor or replacement glow: original shader output only.
   for r in self.recs:r['col']=r['rgb'].copy()
  def authored_animations(self,groups):return []
 x=ShaderBake(key).build();m=x.model({'source':str(SOURCE),'material':'Cycles combined shader output with original nodes, normal maps, emission; authored QA lighting','animation':'static source pose only; no action reuse; rig mapping pending','status':'offline candidate'})
 (P/(key+'.bbmodel')).write_text(json.dumps(m,separators=(',',':')));(P/'stats.json').write_text(json.dumps(x.stats,indent=2));Image.fromarray(x.atlas).save(P/'projected-atlas.png');print('CANDIDATE',x.stats['quads'],x.stats['mean_luma'])


def drive_register_native(name):
 import numpy as np,json,sys,hashlib
 from pathlib import Path
 p=CACHE
 # Preserve the extracted source rig before registration; later projections use the audited native clip rig.
 source=p/'source_shader_mesh.npz'
 o=np.load(NATIVE_CACHE/(name+'_mesh.npz'));current=np.load(p/'shader_mesh.npz')
 if list(current['names'])!=list(o['names']):source.write_bytes((p/'shader_mesh.npz').read_bytes())
 n=dict(np.load(source));known=DRIVE_HUMANOID_HASHES;ni={str(v):i for i,v in enumerate(n['names'])};oi={str(v):i for i,v in enumerate(o['names'])};scale=1.0286287699437537 if name=='knight' else 1.
 used=set(map(str,n['BONE']))|set(map(str,n['VBONE'].reshape(-1)));mapping={};evidence=[]
 for bone in sorted(used):
  h=None;method='nearest exact anatomical locator'
  if bone in known and known[bone] in oi:h=known[bone];method='validated homologous humanoid bone name'
  if bone.startswith('unk_'):
   candidate=int(bone[4:]).to_bytes(4,'little').hex().upper()
   if candidate in oi:h=candidate;method='source numeric bone hash'
  if name=='marauder':
   controls={'arm_stretch.l':'D1232BA2','arm_stretch.r':'17025F50','arm_stretch_dupli_001.l':'5B58FBAF','arm_stretch_dupli_001.r':'C10E6B03','thigh_stretch.l':'695DAF09','thigh_stretch.r':'9F0FD28C','leg_stretch.l':'35B14D1B','leg_stretch.r':'8BD44A3F','root.x':'C7C0BA6E'}
   if bone in controls:h=controls[bone];method='anatomical four-arm/leg deform control restored to native pivot'
  if name=='brig' and bone.startswith(('thigh_stretch.','leg_stretch.')):
   h=known[('Thigh.' if bone.startswith('thigh') else 'Calf.')+bone[-1].upper()];method='anatomical leg control restored to native pivot'
  loc=n['rest'][ni[bone],:3,3];dist=np.linalg.norm(o['rest'][:,:3,3]*scale-loc,axis=1)
  if h is None:
   j=dist.argmin();h=str(o['names'][j]);assert dist[j]<.008,(name,bone,dist[j])
  err=float(np.linalg.norm(o['rest'][oi[h],:3,3]*scale-loc));mapping[bone]=h;evidence.append({'source':bone,'native':h,'method':method,'rest_origin_difference_m':err})
 n['BONE']=np.array([mapping[str(x)] for x in n['BONE']]);n['VBONE']=np.array([[mapping[str(x)] for x in row] for row in n['VBONE']]);n['names']=o['names'];n['parents']=o['parents'];n['rest']=o['rest'].copy();n['rest'][:,:3,3]*=scale
 np.savez_compressed(p/'shader_mesh.npz',**n);(p/'native-registration.json').write_text(json.dumps({'name':name,'scale':scale,'geometry_sha256':hashlib.sha256(n['V'].tobytes()).hexdigest(),'source_rig_snapshot':str(source),'evidence':evidence,'note':'Geometry unchanged. Native clip pivot locations restored for edited source control rigs; rotations use original native world-delta matrices, not copied Euler keys.'},indent=2));print('REGISTERED',name,len(mapping),len(set(mapping.values())))

def drive_native_candidate(name):
 import numpy as np,json,sys,importlib.util,shutil,types,hashlib
 from pathlib import Path
 from PIL import Image
 P=CACHE;repo=REPO;key='dl_'+name
 spec=importlib.util.spec_from_file_location('builder',repo/'scripts/strikes/build_devils_models.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);builder.CACHE=NATIVE_CACHE;b=builder.baker()
 d=np.load(P/'shader_mesh.npz');registration=json.loads((P/'native-registration.json').read_text());source_meta=json.loads((P/'shader-bake.json').read_text());sp=builder.spec_for(name,b);sp.update(src=source_meta.get('source_blend','Drive source'),roles={},k=builder.MODELS[name][1]*16/np.ptp(d['V'][...,2]),walls=2 if name=='thrall' else 6,density=.8 if name in ('thrall','acolyte','knight','wizard') else .8 if name=='marauder' else .23,spacing_scale=.7 if name=='thrall' else 1.0)
 b.SPECS[key]=sp;shutil.copyfile(P/'shader_mesh.npz','/tmp/r7_dump_'+key+'.npz');emission_materials=set(source_meta.get('emission_materials',[]))
 class ShaderBake(b.Bake):
  def __init__(self,key):
   super().__init__(key)
   if name=='brig':
    center=self.m_of(0,3.25*16,-1.05*16);radius=.43*16/self.k
    self._add(self._cyl(center,radius,.06*16/self.k,1,n=12),'weakpoint_glow','AUTHORED_CORE','glow:weakpoint_glow');self._bones()
  def _bones(self):
   super()._bones()
   if name in ('acolyte','knight'):
    weapon='HiveBoomer' if name=='knight' else 'HiveAcolyteShredder'
    self.tri_bone[self.MAT==self.mats.index(weapon)]='weapon'
   if name=='marauder':
    blade_materials={self.mats.index(m) for m in ('ShockBlade','ShockBladeVFX') if m in self.mats}
    for bone,hand in [('blade_l','8C83CB67'),('blade_r','DE9D6BEA')]:
     self.tri_bone[np.isin(self.MAT,list(blade_materials))&(self.bone_raw==hand)]=bone
   if name=='brig':
    c=self.V.mean(1);mask=(self.bone_raw=='A352A6A2')&(c[:,1]>.65)&(c[:,2]>2.6);self.tri_bone[mask]='armor_plate';self.parent['armor_plate']='spine_upper';self.origin['armor_plate']=self.origin['spine_upper']
   for i,mat in enumerate(self.mats):
    if mat not in emission_materials:continue
    mask=self.MAT==i
    for parent in set(self.tri_bone[mask]):
     g='optics_glow' if name=='brig' and 'Eyes' in mat else parent+'_shader_glow';sel=mask&(self.tri_bone==parent);self.tri_bone[sel]=g;self.parent[g]='armor_plate' if g=='optics_glow' else parent;self.origin[g]=self.origin[parent]
  def extract(self):
      """Per bone x face: nearest surface per texel cell, quantised to absolute depth planes -> texel records."""
      np = self.np
      S = self.S
      tri = self.to_px(self.V)
      normals = np.cross(tri[:,1]-tri[:,0], tri[:,2]-tri[:,0])
      normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-12
      sb = self.tri_bone[S['tri']]
      recs = []
      for bone in sorted(set(sb)):
          sel = np.nonzero(sb == bone)[0]
          pitch, spacing = self.pitch_of(bone)
          P = S['P'][sel]
          for face in b.FACES:
              da, near, (ua, va), us, vs = b.FACE_DEF[face]
              selected = np.nonzero(sb == bone)[0]
              sel = selected[np.abs(normals[S['tri'][selected], da]) >= .5]
              if not len(sel): continue
              P = S['P'][sel]
              gi = np.floor(P[:, ua] / pitch).astype(np.int64); gj = np.floor(P[:, va] / pitch).astype(np.int64)
              dsg = P[:, da] if near == 'min' else -P[:, da]
              cell = (gi - gi.min()) * (gj.max() - gj.min() + 1) + (gj - gj.min())
              order = np.lexsort((dsg, cell))
              cs = cell[order]
              start = np.ones(len(order), bool); start[1:] = cs[1:] != cs[:-1]
              gid = np.cumsum(start) - 1
              first = np.nonzero(start)[0]
              dmin = dsg[order][first][gid]
              near_ok = dsg[order] - dmin <= 0.5 * spacing
              n = len(first)
              cnt = np.bincount(gid[near_ok], minlength=n).astype(float)
              rgb = np.stack([np.bincount(gid[near_ok], S['rgb'][sel][order][near_ok][:, c].astype(float), minlength=n)
                              for c in range(3)], 1) / cnt[:, None]
              win = sel[order[first]]
              L = np.round(S['P'][win, da] / spacing).astype(np.int64)
              recs.append(dict(bone=bone, face=face, pitch=pitch, spacing=spacing, gi=gi[order[first]], gj=gj[order[first]],
                               L=L, rgb=rgb, win=win))
      self.recs = recs

  def samples(self):
   super().samples();tri=self.S['tri'];T=self.to_px(self.V)[tri];q=self.S['P']-T[:,0];v0=T[:,1]-T[:,0];v1=T[:,2]-T[:,0]
   a=np.einsum('ij,ij->i',v0,v0);bb=np.einsum('ij,ij->i',v0,v1);c=np.einsum('ij,ij->i',v1,v1);dd=np.einsum('ij,ij->i',q,v0);e=np.einsum('ij,ij->i',q,v1);den=a*c-bb*bb
   u=np.divide(c*dd-bb*e,den,out=np.zeros_like(den),where=abs(den)>1e-12);v=np.divide(a*e-bb*dd,den,out=np.zeros_like(den),where=abs(den)>1e-12);uv=self.UV[tri,0]+u[:,None]*(self.UV[tri,1]-self.UV[tri,0])+v[:,None]*(self.UV[tri,2]-self.UV[tri,0])
   rgba=np.asarray(Image.open(P/'combined.png').convert('RGBA'));emit=np.asarray(Image.open(P/'emit.png').convert('RGB'));h,w=rgba.shape[:2];xx=(np.mod(uv[:,0],1)*w).astype(int)%w;yy=((1-np.mod(uv[:,1],1))*h).astype(int)%h;em=emit[yy,xx];emitting=em.max(1)>16;authored=np.array([self.mats[mi]=='AUTHORED_CORE' for mi in self.MAT[tri]])
   pure=np.array([self.mats[mi] in source_meta.get('pure_emission_materials',[]) for mi in self.MAT[tri]]);keep=np.where(pure,emitting,(rgba[yy,xx,3]>=128)|emitting)|authored;self.S['rgb'][emitting&~authored]=np.maximum(self.S['rgb'][emitting&~authored],em[emitting&~authored]);self.stats['transparent_source_samples_removed']=int((~keep).sum());self.stats['source_emission_samples']=int(emitting.sum());self.S={key:value[keep] for key,value in self.S.items()};self.stats['samples']=int(keep.sum())
  def planes(self):
   self._silhouettes={(r['bone'],r['face']):dict(zip(zip(r['gi'].tolist(),r['gj'].tolist()),r['col'])) for r in self.recs};super().planes()
  def image(self,p):
   cells={tuple(a):c for a,c in zip(p['A'],p['C'])};support=self._silhouettes[(p['bone'],p['face'])];add={}
   for (x,y),color in cells.items():
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)):
     q=(x+dx,y+dy)
     if q in support and q not in cells and q not in add:add[q]=support[q]
   cells.update(add);return super().image(dict(p,A=np.array(list(cells)),C=np.array(list(cells.values()))))
  def recolour(self):
   for r in self.recs:
    r['col']=r['rgb'].copy()
    if r['bone']=='weakpoint_glow':
     points=self.S['P'][r['win']];rad=np.sqrt(points[:,0]**2+(points[:,1]-3.25*16)**2)/(.43*16);hot=np.clip(1-rad,0,1)**.65;r['col']=(np.array([205,38,12])+(np.array([255,244,182])-np.array([205,38,12]))*hot[:,None]).astype(np.uint8)
  def authored_animations(self,groups):return []
 x=ShaderBake(key).build();model=x.model({'source':source_meta,'technique':'Dreg-Light; source shader radiance/alpha/emission bake; native clip registration','registration':registration,'runtime_contract':builder.runtime_contract(name),'status':'candidate for isolated game QA','limits':['PBR response baked under authored QA lighting','0.5 alpha cutout and emission threshold16 approximate Minecraft cutout','depth-slice silhouette still requires game-distance review']})
 scale=registration['scale'];proxy=types.SimpleNamespace(spec=x.spec,parent=x.parent,origin=x.origin,to_px=lambda p:x.to_px(p*scale));model['animations'],mapping=builder.runtime_clips(name,builder.retarget(name,proxy,model));model['devils_lair']=model.pop('w300');model['devils_lair']['runtime_clips']=mapping
 for e in model['elements']:
  if '_shader_glow_' in e['name']:e['light_emission']=15
 model['devils_lair']['native_inputs']=builder.inputs(name)
 x.stats['source_shader_luma_by_bone']={bone:float((np.concatenate([r['col'] for r in x.recs if r['bone']==bone])@np.array([.299,.587,.114])).mean()) for bone in set(r['bone'] for r in x.recs)}
 output=P/(key+'.bbmodel');output.write_text(json.dumps(model,separators=(',',':')));(P/'native-stats.json').write_text(json.dumps(x.stats,indent=2));print('NATIVE',name,len(model['elements']),len(model['animations']),x.stats['mean_luma'],hashlib.sha256(output.read_bytes()).hexdigest())

def main():
 global REPO,SOURCE,CACHE,NATIVE_CACHE
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['dump','bake','refresh','verify','evidence','drive-dump','drive-project','drive-register','drive-native']);ap.add_argument('--names',nargs='+',default=list(MODELS));ap.add_argument('--repo',type=Path,default=REPO);ap.add_argument('--source',type=Path,default=SOURCE);ap.add_argument('--cache',type=Path,default=CACHE);ap.add_argument('--output',type=Path);ap.add_argument('--native-cache',type=Path,default=NATIVE_CACHE)
 a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
 if a.mode.startswith('drive-'):
  assert len(a.names)==1 and a.names[0] in ('thrall','acolyte','knight','wizard','servitor','sepiks','brig','marauder'), 'Drive pipeline supports reviewed species; keep rg_walker unchanged'
 REPO=a.repo;SOURCE=a.source;CACHE=a.cache;NATIVE_CACHE=a.native_cache;CACHE.mkdir(parents=True,exist_ok=True)
 output=a.output or REPO/'src/main/resources/destiny/devils_lair/models'
 if a.mode=='drive-dump':
  import bpy
  assert Path(bpy.data.filepath).resolve()==SOURCE.resolve(), 'load the requested source blend explicitly'
  assert len(a.names)==1, 'choose one --names species for a Drive source'
  drive_shader_dump(a.names[0]);return
 if a.mode in ('drive-register','drive-native'):
  assert len(a.names)==1, 'one species per Drive cache'
  (drive_register_native if a.mode=='drive-register' else drive_native_candidate)(a.names[0]);return
 if a.mode=='drive-project':
  assert len(a.names)==1, 'one source cache per Drive candidate'
  drive_shader_project(a.names[0]);return
 if a.mode=='verify':verify(output);return
 for name in a.names:
  if a.mode=='dump':native_dump(name)
  elif a.mode=='evidence':motion_evidence(name,output)
  elif a.mode=='refresh':refresh_one(name,output/('dl_'+name+'.bbmodel'))
  else:bake_one(name,output/('dl_'+name+'.bbmodel'))
 if a.mode in ('bake','refresh'):write_manifest(output)
if __name__=='__main__':main()
