"""W255 source-driven full-body class clips; writes only the owned pack and manifest.
First evaluate original .blend files with sample_class_ability_w255.py.
Use --root to select the refreshed checkout, --output-root for scratch drafts,
--review-dir for static source-skeleton/target-skin PNG contact sheets (Pillow),
and --verify to compare outputs without writing. No model/runtime edits.
"""
import sys,json,math,argparse,hashlib,copy,zipfile,io
from pathlib import Path
sys.dont_write_bytecode=True
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
parser.add_argument('--samples',type=Path,required=True)
parser.add_argument('--output-root',type=Path)
parser.add_argument('--review-dir',type=Path,default=Path('/private/tmp/destiny-w255/class-worker/review'))
parser.add_argument('--verify',action='store_true')
parser.add_argument('--bettermodel-jar',type=Path,help='Optional explicit BetterModel dependency jar; defaults to cached version from gradle.properties without running Gradle')
args=parser.parse_args()
ROOT=args.root.resolve()
OUTPUT=(args.output_root or ROOT).resolve()
sys.path.insert(0,str(ROOT/'scripts'))
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_animation_h20 as h20
import build_hunter_source_w197 as w197
C=w197.C
ENTRY_TICKS=1  # Runtime one-shot SwordTiming.START_TICKS; body source time stays unchanged.
MODEL_PATH=ROOT/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel'
model=json.loads(MODEL_PATH.read_text())
data=json.loads(args.samples.read_text())
assert data['autoexecDisabled'] and data['sampleSpace']=='armature_object'
assert len(data['groups'])==6 and sum(len(g['clips']) for g in data['groups'])==18
for g in data['groups']:
 assert len(g['bones'])==72
 for clip in g['clips']:
  assert len(clip['frames'])==61 and clip['actualFrameRange']==[clip['firstFrame'],clip['lastFrame']]
  assert clip['fps']==30
  for f in clip['frames']:
   assert len(f['joints'])==72 and all(math.isfinite(v) for m in f['joints'].values() for row in m for v in row)
clips={c['tag']:(g,c) for g in data['groups'] for c in g['clips']}
GROUPS={g['name']:g for g in model['groups']}
def xyz(m):return [m[i][3] for i in range(3)]
def convert(v):return h19.vector(C,v)
def local(pose,name,desired):
 actual=h19.fk(model,pose)[name]
 now=h15.rot(h19.add(GROUPS[name].get('rotation',[0]*3),pose[name]))
 parent=h15.mm(w197.rotation(actual),h19.inverse_rotation(now))
 pose[name]=h19.sub(h19.euler(h15.mm(h19.inverse_rotation(parent),desired)),GROUPS[name].get('rotation',[0]*3))
def pose(g,frame):
 # Use evaluated matrices, never bone-map list order; source root wrapper is excluded.
 p=h15.zero();m=frame['joints'];points={n:xyz(v) for n,v in m.items()};bones={b['name']:b for b in g['bones']}
 for target,source in [('phip_hip','C7C0BA6E'),('pw_waist','A252A6A2'),('pc_chest','A352A6A2'),('h_ph_head','7E92D640')]:
  desired=h15.mm(C,h15.mm(w197.rotation(m[source]),h15.mm(h19.inverse_rotation(w197.rotation(bones[source]['matrix'])),h19.inverse_rotation(C))))
  local(p,target,desired)
 for upper,lower,chain in [('prl_right_leg','prfl_right_foreleg',['9F0FD28C','8BD44A3F','B9B9E05D']),('pll_left_leg','plfl_left_foreleg',['695DAF09','35B14D1B','0F8B505D'])]:
  frame,bend=w197.leg_frame(points,chain)
  # Flip anatomical X and Z together: negative-X knee bend, sole faces forward.
  frame=h15.mm(frame,h15.rot([0,180,0]))
  local(p,upper,h15.mm(C,frame));p[lower]=[-bend,0,0]
 for side,upper,fore,item,chain in [('left','pla_left_arm','plfa_left_forearm','pli_left_item',['D1232BA2','897A1504','8C83CB67']),('right','pra_right_arm','prfa_right_forearm','pri_right_item',['17025F50','A3781DCD','DE9D6BEA'])]:
  shoulder=h19.point(h19.fk(model,p)[upper],[0,0,0]);a=h19.norm(h19.sub(GROUPS[fore]['origin'],GROUPS[upper]['origin']));b=h19.norm(h19.sub(GROUPS[item]['origin'],GROUPS[fore]['origin']))
  u=convert(h19.unit(h19.sub(points[chain[1]],points[chain[0]])));v=convert(h19.unit(h19.sub(points[chain[2]],points[chain[1]])))
  delta=h19.add(h19.mul(u,a),h19.mul(v,b));distance=h19.norm(delta)
  if distance>10.9:delta=h19.mul(delta,10.9/distance)
  h19.solve_arm(model,p,side,h19.add(shoulder,delta),u)
 return p
SELECTION={'h15_class_titan_towering':['80A8AD7C','80A8AD79'],'h15_class_titan_rally':['80A8AD7B','80A8AD7F'],'h15_class_warlock_healing':['80A8AA08','80A8AA01','80A8A9FE'],'h15_class_warlock_empowering':['80A8AA04','80A8AA03','80A8AA06']}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def unwrap(frames):
 previous=None
 for _,p in frames:
  if previous:
   for n in p:
    x,y,z=p[n]
    candidates=[[v+360*round((old-v)/360) for v,old in zip(family,previous[n])] for family in ([x,y,z],[x+180,180-y,z+180])]
    p[n]=min(candidates,key=lambda q:sum((a-b)**2 for a,b in zip(q,previous[n])))
  previous=p

def assemble(name,tags):
 frames=[];offset=0;stages=[];seams=[]
 for tag in tags:
  g,c=clips[tag];prior=copy.deepcopy(frames[-1][1]) if frames else None
  stages.append({'tag':tag,'stage':c['stage'],'startSeconds':offset,'startTicks':offset*20,'durationSeconds':c['durationSeconds'],'durationTicks':c['durationSeconds']*20,'evaluatedSamples':61,'action':c['action']})
  if prior:seams.append({'timeSeconds':offset,'blendSeconds':2/30,'policy':'incoming first two source frames slerp from outgoing endpoint; no hold or duration extension'})
  for i,f in enumerate(c['frames']):
   seconds=c['durationSeconds']*i/60;t=round(offset+seconds,9);pp=pose(g,f)
   if prior and seconds<2/30:pp=w197.blend_pose(prior,pp,seconds/(2/30))
   if frames and abs(t-frames[-1][0])<1e-8:continue
   frames.append((t,pp))
  offset+=c['durationSeconds']
 unwrap(frames)
 animation=h20.new_clip(model,name,frames)
 animation['length']=round(offset,9);animation['snapping']=120
 # Refine only root-floor interpolation; retain all source rotation samples.
 root=next(a for a in animation['animators'].values() if a['name']=='player_root')
 anchors={t for t,_ in frames}
 # BM treats frame times within1ms as equal. Keep source anchors and omit
 # regular floor-grid times too close to them, before midpoint refinement.
 root['keyframes']=[k for k in root['keyframes'] if k['channel']!='position' or k['time'] in anchors or all(abs(k['time']-t)>.00101 for t in anchors)]
 for _ in range(8):
  keys=sorted([k for k in root['keyframes'] if k['channel']=='position'],key=lambda k:k['time'])
  additions=[]
  for a,b in zip(keys,keys[1:]):
   t=round((a['time']+b['time'])/2,9)
   if t>animation['length'] or b['time']-a['time']<=.00202:continue
   pp,_=h19.sample(animation,t);actual=h15.floor_y(model,pp)
   if abs((a['data_points'][0]['y']+b['data_points'][0]['y'])/2-actual)>.035:
    additions.append({'uuid':h15.uid(f'w255/{name}/root/{t}'),'channel':'position','time':t,'interpolation':'linear','data_points':[{'x':0,'y':actual,'z':0}]})
  if not additions:break
  assert len(keys)+len(additions)<=256,('root floor refinement budget',name,len(keys),len(additions))
  root['keyframes'].extend(additions)
 # H20's rounded regular grid can otherwise extend beyond fractional 30Hz ends.
 for a in animation['animators'].values():
  a['keyframes']=[k for k in a['keyframes'] if k['time']<=animation['length']]
 contact=clips[tags[1] if 'warlock' in name else tags[0]][1]
 index=min(range(61),key=lambda i:contact['frames'][i]['joints']['8C83CB67'][2][3])
 contact_seconds=(stages[1]['startSeconds'] if 'warlock' in name else 0)+contact['durationSeconds']*index/60
 release=math.ceil(contact_seconds*20-1e-9);rounded=math.ceil(offset*20-1e-9)
 summary={'name':name,'runtimeStatus':'active existing ability' if name in ('h15_class_titan_towering','h15_class_warlock_healing') else 'prepared asset only; no playable ability added','durationSeconds':round(offset,9),'clipDurationTicks':offset*20,'roundedClipTicks':rounded,'startModifierTicks':ENTRY_TICKS,'lifecycleTicks':rounded+ENTRY_TICKS,'recommendedReleaseTicks':release,'elapsedReleaseTicks':release+ENTRY_TICKS,'contact':{'sourceTag':contact['tag'],'sourceFrame':contact['frames'][index]['frame'],'sampleIndex':index,'seconds':contact_seconds,'sourceLeftWristHeight':contact['frames'][index]['joints']['8C83CB67'][2][3],'interpretation':'Minecraft visual calibration from minimum left wrist height in enter (Titan) or cast (Warlock); not decoded source event; not verified original-game trigger; native planting calibration pending'},'stages':stages,'seams':seams,'assembledPoseCount':len(frames),'rotationRangesDegrees':{n:[[min(p[n][j] for _,p in frames),max(p[n][j] for _,p in frames)] for j in range(3)] for n in h15.BONES},'rootYRange':[min(h15.floor_y(model,p) for _,p in frames),max(h15.floor_y(model,p) for _,p in frames)]}
 return animation,summary

CHAIN=[('C7C0BA6E','A152A6A2'),('A152A6A2','A252A6A2'),('A252A6A2','A352A6A2'),('A352A6A2','7E92D640'),('A352A6A2','D1232BA2'),('D1232BA2','897A1504'),('897A1504','8C83CB67'),('A352A6A2','17025F50'),('17025F50','A3781DCD'),('A3781DCD','DE9D6BEA'),('C7C0BA6E','695DAF09'),('695DAF09','35B14D1B'),('35B14D1B','0F8B505D'),('C7C0BA6E','9F0FD28C'),('9F0FD28C','8BD44A3F'),('8BD44A3F','B9B9E05D')]
def source_frame(tags,time):
 offset=0
 for tag in tags:
  g,c=clips[tag]
  if time<=offset+c['durationSeconds']+1e-8:
   i=round(max(0,min(1,(time-offset)/c['durationSeconds']))*60)
   return c['frames'][i],tag
  offset+=c['durationSeconds']
 return clips[tags[-1]][1]['frames'][-1],tags[-1]

def skin_faces(p,y):
 matrices=h19.fk(model,p,y);groups={g['uuid']:g for g in model['groups']};elements={e['uuid']:e for e in model['elements']};faces=[]
 def walk(nodes,parent):
  for node in nodes:
   if isinstance(node,str):
    e=elements.get(node,{})
    if e.get('name')!='skin':continue
    origin=parent['origin'];corners=[]
    for x,y0,z in [(x,y0,z) for x in (e['from'][0],e['to'][0]) for y0 in (e['from'][1],e['to'][1]) for z in (e['from'][2],e['to'][2])]:
     corners.append(h19.point(matrices[parent['name']],[x-origin[0],y0-origin[1],z-origin[2]]))
    for indices in ([0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]):faces.append(([corners[i] for i in indices],parent['name']))
   else:walk(node['children'],groups[node['uuid']])
 walk(model['outliner'],None)
 return faces

def review(animation,summary,tags):
 paths=[]
 if args.verify:
  return [{'path':str(args.review_dir/(animation['name']+'-'+view+'.png')),'sha256':sha(args.review_dir/(animation['name']+'-'+view+'.png'))} for view in ('front','side')]
 from PIL import Image,ImageDraw
 args.review_dir.mkdir(parents=True,exist_ok=True)
 length=animation['length'];times=sorted({0,round(length*.15,9),round(length*.35,9),round(summary['contact']['seconds'],9),round(length*.65,9),round(length*.85,9),length})
 for view in ('front','side'):
  cell=210;im=Image.new('RGB',(cell*len(times),510),'#101b28');draw=ImageDraw.Draw(im)
  draw.text((12,10),animation['name']+' | '+view+' | evaluated source / target skin cubes (static FK)',fill='#ffffff')
  def project(v,cx,base):
   horizontal=v[0]+v[2]*.22 if view=='front' else -v[2]+v[0]*.2
   return (cx+horizontal*5.6,base-v[1]*5.6)
  for i,t in enumerate(times):
   cx=i*cell+cell/2;draw.text((i*cell+10,34),f'{t:.3f}s',fill='#ffffff')
   f,tag=source_frame(tags,t);points={n:h19.mul(convert(xyz(m)),16) for n,m in f['joints'].items()}
   center=points['C7C0BA6E'];floor=min(points[n][1] for n in ['0F8B505D','B9B9E05D'])-1.8
   points={n:[v[0]-center[0],v[1]-floor,v[2]-center[2]] for n,v in points.items()}
   draw.line([(i*cell,240),((i+1)*cell,240)],fill='#536579')
   for a,b in CHAIN:draw.line([project(points[a],cx,240),project(points[b],cx,240)],fill='#f5aa62',width=3)
   draw.text((i*cell+10,250),'source '+tag,fill='#f5aa62')
   p,y=h19.sample(animation,t);faces=skin_faces(p,y)
   depth=lambda face:sum((v[2] if view=='front' else v[0]) for v in face[0])/4
   for vertices,bone in sorted(faces,key=depth,reverse=True):
    color='#63b9d2' if 'leg' in bone else '#92c5e2' if 'arm' in bone else '#c2d6e8'
    draw.polygon([project(v,cx,474) for v in vertices],fill=color,outline='#243d54')
   draw.line([(i*cell,474),((i+1)*cell,474)],fill='#536579')
  draw.text((12,490),'Source object-space axes converted once; skin/profile supplied by runtime. No native Blender scene or Minecraft QA.',fill='#b3c5d7')
  path=args.review_dir/(animation['name']+'-'+view+'.png');im.save(path);paths.append({'path':str(path),'sha256':sha(path)})
 return paths

def validate(animation,summary):
 assert animation['loop']=='once' and animation['override'] is False
 assert 0<summary['recommendedReleaseTicks']<summary['roundedClipTicks']
 for a in animation['animators'].values():
  for channel in {k['channel'] for k in a['keyframes']}:
   keys=sorted([k for k in a['keyframes'] if k['channel']==channel],key=lambda k:k['time'])
   times=[k['time'] for k in keys]
   assert len(times)==len(set(times))<=256,(a['name'],channel,len(times))
   assert times[0]==0 and abs(times[-1]-animation['length'])<1e-8
   assert min(b-a for a,b in zip(times,times[1:]))>.001, 'BetterModel frame comparator collision'
   assert all(k['interpolation']=='linear' and all(math.isfinite(float(v)) for v in k['data_points'][0].values()) for k in keys)
   if channel=='rotation':
    assert max(abs(b['data_points'][0][axis]-c['data_points'][0][axis]) for b,c in zip(keys,keys[1:]) for axis in 'xyz')<120,(animation['name'],a['name'],'Euler discontinuity')
   if a['name']=='player_root' and channel=='position':assert all(k['data_points'][0]['x']==k['data_points'][0]['z']==0 for k in keys)
 # 120Hz skin envelope verifies interpolation as well as authored samples.
 error=0
 for i in range(math.ceil(animation['length']*120)+1):
  t=min(i/120,animation['length']);p,y=h19.sample(animation,t)
  error=max(error,abs(y-h15.floor_y(model,p)))
 assert error<.075,('floor interpolation',animation['name'],error)
 summary['maxInterpolatedFloorErrorModelUnits']=error
 for n in ['phip_hip','pw_waist','pc_chest','prl_right_leg','prfl_right_foreleg','pll_left_leg','plfl_left_foreleg']:
  assert max(b-a for a,b in summary['rotationRangesDegrees'][n])>3,('frozen full body',n)

def engine_template():
 version=next(line.split('=',1)[1].strip() for line in (ROOT/'gradle.properties').read_text().splitlines() if line.startswith('bettermodel_version='))
 candidates=[args.bettermodel_jar] if args.bettermodel_jar else sorted((Path.home()/'.gradle/caches/modules-2/files-2.1/io.github.toxicity188/bettermodel-fabric'/version).glob('*/*.jar'))
 assert candidates, 'Pass --bettermodel-jar to inspect the current runtime template'
 jar=candidates[0]
 def find(raw,depth=0):
  with zipfile.ZipFile(io.BytesIO(raw)) as archive:
   if 'steve.bbmodel' in archive.namelist():return archive.read('steve.bbmodel')
   if depth<3:
    for name in archive.namelist():
     if name.endswith('.jar'):
      found=find(archive.read(name),depth+1)
      if found:return found
  return None
 raw=find(jar.read_bytes());assert raw, 'BetterModel jar lacks steve.bbmodel'
 template=json.loads(raw)
 comparison={k:template.get(k)==model.get(k) for k in ['groups','elements','outliner']}
 assert all(comparison.values()), 'Current runtime Steve geometry/hierarchy differs from the FK rig'
 return {'version':version,'dependencyJar':str(jar),'dependencyJarSha256':sha(jar),'steveSha256':hashlib.sha256(raw).hexdigest(),'exactCurrentTemplateMatch':comparison,'engineRotationEvidence':'BetterModel3.5.1 MathUtil.toQuaternion(Vector3f,Quaternionf) bytecode inspected: identity().rotateZYX(z*DEG,y*DEG,x*DEG), same Rz*Ry*Rx as h15/h19; no live engine execution'}
engine_evidence=engine_template()
old=json.loads((ROOT/'art/weapons/w197/hunter-source-motion.json').read_text())['bones']
new={b['name']:b for b in data['groups'][0]['bones']}
assert set(old)==set(new) and len(old)==72
rest_difference=max(abs(old[n]['restMatrix'][i][j]-new[n]['matrix'][i][j]) for n in old for i in range(4) for j in range(4))
assert rest_difference<.00001, 'Not the existing 72-bone source rig'
animations=[];summaries=[]
for name,tags in SELECTION.items():
 animation,summary=assemble(name,tags);validate(animation,summary)
 summary['renderReview']=review(animation,summary,tags)
 animations.append(animation);summaries.append(summary)
selected={t for tags in SELECTION.values() for t in tags}
manifest={'schemaVersion':1,'generatorHashes':{p:sha(ROOT/p) for p in ['scripts/animation/sample_class_ability_w255.py','scripts/animation/build_class_ability_w255.py','scripts/build_hunter_animation_h15.py','scripts/build_hunter_animation_h19.py','scripts/build_hunter_animation_h20.py','scripts/build_hunter_source_w197.py']},'sourceRoot':data['sourceRoot'],'sourceHashAlgorithm':'sha256','sourceHashes':data['sourceHashes'],'evaluatedSamples':{'path':str(args.samples.resolve()),'sha256':sha(args.samples),'blenderVersion':data['blenderVersion'],'actions':18,'bones':72,'samplesPerSourceClip':61,'sampleSpace':data['sampleSpace'],'autoexecDisabled':True},'target':{'rig':'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel','rigSha256':sha(MODEL_PATH),'currentBetterModelTemplate':engine_evidence,'runtimeModelOwnedByMaster':'guardian_hunter_w255_r2','profileSkin':'runtime BetterModel skin; no texture/mesh source in SSD','hierarchy':'player_root parents hip and both thighs; hip > waist > chest > head/arms; solve against actual outliner parents','eulerOrder':'Rz*Ry*Rx (h15.rot and h19.fk); equivalent Euler families unwrapped before linear export','basis':C,'axes':'source armature-object +X anterior,+Y left,+Z up => target +X right,+Y up,-Z forward; source object 0.01 scale and +90X FBX import wrapper intentionally excluded; no duplicate preview -Y-up conversion','torso':'source pose * inverse(rest) basis-calibrated onto hip, collapsed spine and head; no manual replacement curve','legs':'source hip-knee-ankle geometric bend-plane; negative-X knee flex, source world thigh directions; legs solved relative to actual player_root (siblings of hip)','arms':'source shoulder-elbow-wrist segment directions scaled to actual Steve link lengths; h19.solve_arm with source elbow bias, reach projected to10.9 model units near singular extension','rootOrder':'root rotation keys remain identity; root Y is applied before descendants; actual outliner has thighs as hip siblings; source pedestal/wrapper is not an animated target root', 'root':'h20.new_clip skin-cube floor fit preserves crouch silhouette; horizontal source displacement omitted while runtime blocks movement; no entity teleport','scale':'source deform scales within 0.000023 of1: no authored squash-scale animation discarded; crouch is joint pose','stitch':'61 evaluated poses per stage; shared seam time emits one pose; incoming first2source frames blended in quaternion space; source durations preserved'},'clips':summaries,'auditOnly':[{'tag':c['tag'],'group':c['group'],'aliases':c['aliases'],'reason':'alternate source take/variant; not a third class ability type'} for _,c in clips.values() if c['tag'] not in selected],'sourceRigCompatibility':{'reference':'art/weapons/w197/hunter-source-motion.json','referenceSha256':sha(ROOT/'art/weapons/w197/hunter-source-motion.json'),'same72BoneIds':True,'maxRestMatrixDifference':rest_difference},'sourceActions':[{'tag':c['tag'],'action':c['action'],'blend':c['blend'],'fps':c['fps'],'firstFrame':c['firstFrame'],'lastFrame':c['lastFrame'],'evaluatedSamples':len(c['frames']),'eventsUninterpreted':c['eventsUninterpreted']} for _,c in clips.values()],'runtimeScope':{'activeExistingAbilities':['h15_class_titan_towering','h15_class_warlock_healing'],'preparedAssetsOnly':['h15_class_titan_rally','h15_class_warlock_empowering'],'gameplayExpansion':False,'masterAcceptanceScope':'two existing class ability lifecycles plus four grenade species; master owns runtime/model installer/camera/GameTest retiming'},'verification':{'staticFullBodyAndFloor':'passed; 120Hz interpolation envelope; no duplicate keys; <=256 keys/channel; finite linear keys; Euler equivalent-family unwrap; >1ms key spacing for BM frame comparator; all hip/spine/thigh/knee channels vary','renderReviewStatus':'eight generated orthographic sheets inspected by worker: source crouch, asymmetric knees, torso turns and distinct cast gestures retained; human/native acceptance pending','standaloneAssetTest':'two standalone JUnit asset tests passed; evidence /private/tmp/destiny-w255/class-worker/assettest.log; no Gradle', 'notRun':['Gradle','Minecraft/Vision/native camera and terrain contact','live Blender scene','original-game event decoding'],'contactTiming':'Minecraft recommendation from visible sampled wrist low point; native calibration pending, never an original trigger claim'}}
# Small runtime contract; contactSeconds is visual calibration, not a decoded source event.
timing={'schemaVersion':1,'clips':[{'name':s['name'],'durationSeconds':s['durationSeconds'],'contactSeconds':s['contact']['seconds'],'entryTicks':ENTRY_TICKS} for s in summaries]}
for relative,obj in [('src/main/resources/destiny/animation/class_ability_w255.animation.json',{'animations':animations}),('src/main/resources/destiny/animation/class_ability_w255.timing.json',timing),('art/abilities/w255/class-motion-manifest.json',manifest)]:
 path=OUTPUT/relative
 raw=(json.dumps(obj,separators=(',',':'),allow_nan=False)+'\n').encode() if 'resources/' in relative else (json.dumps(obj,indent=2,allow_nan=False)+'\n').encode()
 if args.verify:assert path.read_bytes()==raw,('Reproduction differs',path)
 else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
print(json.dumps({s['name']:{k:s[k] for k in ['durationSeconds','roundedClipTicks','lifecycleTicks','recommendedReleaseTicks','elapsedReleaseTicks','assembledPoseCount','maxInterpolatedFloorErrorModelUnits']} for s in summaries},indent=2))
