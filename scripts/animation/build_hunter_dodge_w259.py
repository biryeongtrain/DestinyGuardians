#!/usr/bin/env python3
"""W259: retarget 61 evaluated poses per original Hunter dodge action.

Uses W255 torso/limb retarget, H20 floor fit and static source/skin review.
Reads original source hashes and master-evaluated Blender samples; never opens
Blender, runs Gradle, changes gameplay, or writes to the source delivery.
Writes only the W259 animation, timing and manifest; PNGs go to --review-dir.
--verify reconstructs assets and compares bytes without writing.
"""
import sys, json, math, argparse, hashlib, zipfile, io
from pathlib import Path
sys.dont_write_bytecode = True
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
parser.add_argument('--samples', type=Path, required=True)
parser.add_argument('--output-root', type=Path)
parser.add_argument('--review-dir', type=Path, default=Path('/private/tmp/destiny-w259/art-review'))
parser.add_argument('--bettermodel-jar', type=Path)
parser.add_argument('--verify', action='store_true')
args = parser.parse_args()
ROOT = args.root.resolve()
OUTPUT = (args.output_root or ROOT).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_animation_h20 as h20
import build_hunter_source_w197 as w197
C = w197.C
ENTRY_TICKS = 1  # Runtime entry transition is separate from unmodified source time.
MODEL_PATH = ROOT / 'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel'
model = json.loads(MODEL_PATH.read_text())
GROUPS = {g['name']: g for g in model['groups']}
data = json.loads(args.samples.read_text())
assert data['autoexecDisabled'] and data['sampleSpace'] == 'armature_object'
assert len(data['groups']) == 3 and sum(len(g['clips']) for g in data['groups']) == 20
for g in data['groups']:
 assert len(g['bones']) == 72 and g['sceneFps'] == 30
 for c in g['clips']:
  assert c['fps'] == 30 and len(c['frames']) == 61
  assert c['actualFrameRange'] == [c['firstFrame'], c['lastFrame']]
  assert abs(c['durationSeconds'] - (c['lastFrame'] - c['firstFrame']) / 30) < 1e-12
  for i, f in enumerate(c['frames']):
   assert abs(f['frame'] - (c['firstFrame'] + (c['lastFrame'] - c['firstFrame']) * i / 60)) < 1e-7
   assert set(f['joints']) == {b['name'] for b in g['bones']}
   assert all(math.isfinite(v) for m in f['joints'].values() for row in m for v in row)
clips = {c['tag']: (g, c) for g in data['groups'] for c in g['clips']}
SELECTION = {
 'h15_roll_forward': '80A8A8D5', 'h15_roll_back': '80A8A8CA',
 'h15_roll_left': '80A8ADC4', 'h15_roll_right': '80A8ADC7',
 'h15_dodge_marksman_forward': '80A8AA4F', 'h15_dodge_marksman_back': '80A8AA50',
 'h15_dodge_marksman_left': '80A8AA48', 'h15_dodge_marksman_right': '80A8AA4A',
}
CHAIN = [('C7C0BA6E','A152A6A2'),('A152A6A2','A252A6A2'),('A252A6A2','A352A6A2'),
 ('A352A6A2','7E92D640'),('A352A6A2','D1232BA2'),('D1232BA2','897A1504'),('897A1504','8C83CB67'),
 ('A352A6A2','17025F50'),('17025F50','A3781DCD'),('A3781DCD','DE9D6BEA'),
 ('C7C0BA6E','695DAF09'),('695DAF09','35B14D1B'),('35B14D1B','0F8B505D'),
 ('C7C0BA6E','9F0FD28C'),('9F0FD28C','8BD44A3F'),('8BD44A3F','B9B9E05D')]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def xyz(m):return [m[i][3] for i in range(3)]

def convert(v):return h19.vector(C,v)

def local(pose,name,desired):
 actual=h19.fk(model,pose)[name]
 now=h15.rot(h19.add(GROUPS[name].get('rotation',[0]*3),pose[name]))
 parent=h15.mm(w197.rotation(actual),h19.inverse_rotation(now))
 pose[name]=h19.sub(h19.euler(h15.mm(h19.inverse_rotation(parent),desired)),GROUPS[name].get('rotation',[0]*3))

def pose(g,frame,normals):
 # Move evaluated pelvis orientation to the common parent of hip AND thighs.
 # Descendant desired world rotations remain source-derived, preventing double spin.
 p=h15.zero();m=frame['joints'];points={n:xyz(v) for n,v in m.items()};bones={b['name']:b for b in g['bones']}
 local(p,'player_root',h15.mm(C,h15.mm(w197.rotation(m['C7C0BA6E']),h15.mm(h19.inverse_rotation(w197.rotation(bones['C7C0BA6E']['matrix'])),h19.inverse_rotation(C)))))
 for target,source in [('phip_hip','C7C0BA6E'),('pw_waist','A252A6A2'),('pc_chest','A352A6A2'),('h_ph_head','7E92D640')]:
  desired=h15.mm(C,h15.mm(w197.rotation(m[source]),h15.mm(h19.inverse_rotation(w197.rotation(bones[source]['matrix'])),h19.inverse_rotation(C))))
  local(p,target,desired)
 for upper,lower,chain in [('prl_right_leg','prfl_right_foreleg',['9F0FD28C','8BD44A3F','B9B9E05D']),('pll_left_leg','plfl_left_foreleg',['695DAF09','35B14D1B','0F8B505D'])]:
  down=h19.unit(h19.sub(points[chain[1]],points[chain[0]]))
  lower_dir=h19.unit(h19.sub(points[chain[2]],points[chain[1]]))
  bend=math.degrees(math.acos(max(-1,min(1,h19.dot(down,lower_dir)))))
  x=normals[chain[0]];y=h19.mul(down,-1);z=h19.cross(x,y)
  frame=[[x[i],y[i],z[i],0] for i in range(3)]+[[0,0,0,1]]
  # Flip anatomical X and Z together: negative-X knee bend, sole faces forward.
  frame=h15.mm(frame,h15.rot([0,180,0]))
  local(p,upper,h15.mm(C,frame));p[lower]=[-bend,0,0]
 for side,upper,fore,item,chain in [('left','pla_left_arm','plfa_left_forearm','pli_left_item',['D1232BA2','897A1504','8C83CB67']),('right','pra_right_arm','prfa_right_forearm','pri_right_item',['17025F50','A3781DCD','DE9D6BEA'])]:
  shoulder=h19.point(h19.fk(model,p)[upper],[0,0,0]);a=h19.norm(h19.sub(GROUPS[fore]['origin'],GROUPS[upper]['origin']));b=h19.norm(h19.sub(GROUPS[item]['origin'],GROUPS[fore]['origin']))
  u=convert(h19.unit(h19.sub(points[chain[1]],points[chain[0]])));v=convert(h19.unit(h19.sub(points[chain[2]],points[chain[1]])))
  delta=h19.add(h19.mul(u,a),h19.mul(v,b));distance=h19.norm(delta)
  if distance>10.9:delta=h19.mul(delta,10.9/distance)
  # At a straight source elbow u is parallel to delta, so raw-u bias has no
  # defined side. The transported source bend plane remains well-defined.
  bias=convert(h19.cross(h19.unit(h19.sub(points[chain[1]],points[chain[0]])),normals[chain[0]]))
  h19.solve_arm(model,p,side,h19.add(shoulder,delta),bias)
 return p

def unwrap(frames):
 previous=None
 for _,p in frames:
  if previous:
   for n in p:
    x,y,z=p[n]
    candidates=[[v+360*round((old-v)/360) for v,old in zip(family,previous[n])] for family in ([x,y,z],[x+180,180-y,z+180])]
    p[n]=min(candidates,key=lambda q:sum((a-b)**2 for a,b in zip(q,previous[n])))
  else:
   # Choose an equivalent compact initial family before preserving accumulated turns.
   for n in p:
    x,y,z=p[n]
    families=[[((v+180)%360)-180 for v in family] for family in ([x,y,z],[x+180,180-y,z+180])]
    p[n]=min(families,key=lambda q:sum(v*v for v in q))
  previous=p

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


def source_rotation(g, frame, bone):
 rest = next(b['matrix'] for b in g['bones'] if b['name'] == bone)
 return h15.mm(C, h15.mm(w197.rotation(frame['joints'][bone]),
     h15.mm(h19.inverse_rotation(w197.rotation(rest)), h19.inverse_rotation(C))))


def angle_error(a, b):
 delta = h15.mm(h19.inverse_rotation(a), b)
 return math.degrees(math.acos(max(-1, min(1, (sum(delta[i][i] for i in range(3)) - 1) / 2))))


def stable_normals(c, chain):
 # A collinear joint has no geometric bend plane. Fill only those samples
 # from bracketing source planes transported in the upper bone's own frame.
 # This retains the evaluated source twist during fully extended intervals.
 rotations=[]; directions=[]; normals=[]; repaired=[]
 for f in c['frames']:
  a,b,d=[xyz(f['joints'][n]) for n in chain]
  u=h19.unit(h19.sub(b,a));v=h19.unit(h19.sub(d,b))
  cross=h19.cross(u,v)
  rotations.append(w197.rotation(f['joints'][chain[0]]));directions.append(u)
  normals.append(h19.unit(cross) if h19.norm(cross)>1e-4 else None)
 valid=[i for i,n in enumerate(normals) if n is not None]
 assert valid, ('Entire source chain is collinear',c['tag'],chain)
 for i,n in enumerate(normals):
  if n is not None:continue
  before=max((j for j in valid if j<i),default=valid[0])
  after=min((j for j in valid if j>i),default=valid[-1])
  a=h19.vector(h19.inverse_rotation(rotations[before]),normals[before])
  b=h19.vector(h19.inverse_rotation(rotations[after]),normals[after])
  alpha=0 if before==after else (i-before)/(after-before)
  dot=max(-1,min(1,h19.dot(a,b)))
  if dot>.9995:
   mixed=h19.unit(h19.add(h19.mul(a,1-alpha),h19.mul(b,alpha)))
  else:
   angle=math.acos(dot)
   tangent=h19.sub(b,h19.mul(a,dot))
   if h19.norm(tangent)<1e-8:
    axis=min(([1,0,0],[0,1,0],[0,0,1]),key=lambda v:abs(h19.dot(v,a)))
    tangent=h19.cross(a,axis)
   tangent=h19.unit(tangent)
   mixed=h19.add(h19.mul(a,math.cos(angle*alpha)),h19.mul(tangent,math.sin(angle*alpha)))
  world=h19.vector(rotations[i],mixed)
  normals[i]=h19.unit(h19.sub(world,h19.mul(directions[i],h19.dot(world,directions[i]))))
  repaired.append({'sampleIndex':i,'sourceFrame':c['frames'][i]['frame'],
      'bracketingSampleIndices':[before,after]})
 return normals,repaired


def assemble(name, tag):
 g, c = clips[tag]
 normals={};repairs={}
 for chain in [['9F0FD28C','8BD44A3F','B9B9E05D'],['695DAF09','35B14D1B','0F8B505D'],
     ['D1232BA2','897A1504','8C83CB67'],['17025F50','A3781DCD','DE9D6BEA']]:
  normals[chain[0]],repairs[chain[0]]=stable_normals(c,chain)
 frames = [(round(c['durationSeconds'] * i / 60, 9),
     pose(g, f, {n:vs[i] for n,vs in normals.items()})) for i, f in enumerate(c['frames'])]
 unwrap(frames)
 animation = h20.new_clip(model, name, frames)
 animation['length'] = round(c['durationSeconds'], 9)
 animation['snapping'] = 120
 root = next(a for a in animation['animators'].values() if a['name'] == 'player_root')
 anchors = {t for t, _ in frames}
 # H20's regular floor grid may overshoot the 29/30 second end or collide
 # with a source anchor under BetterModel's 1ms key-time comparator.
 root['keyframes'] = [k for k in root['keyframes'] if k['channel'] != 'position' or
     (k['time'] <= animation['length'] and
      (k['time'] in anchors or all(abs(k['time'] - t) > .00101 for t in anchors)))]
 for _ in range(8):
  keys = sorted([k for k in root['keyframes'] if k['channel'] == 'position'], key=lambda k: k['time'])
  additions = []
  for a, b in zip(keys, keys[1:]):
   if b['time'] - a['time'] <= .00202:
    continue
   t = round((a['time'] + b['time']) / 2, 9)
   p, _ = h19.sample(animation, t)
   floor = h15.floor_y(model, p)
   # The lowest cube can switch twice within one segment. A midpoint alone
   # misses a head/hand contact cusp, so also probe both quarter points.
   errors=[]
   for alpha in (.25,.5,.75):
    sample_t=a['time']+(b['time']-a['time'])*alpha
    sample_p,_=h19.sample(animation,sample_t)
    line_y=a['data_points'][0]['y']*(1-alpha)+b['data_points'][0]['y']*alpha
    errors.append(abs(line_y-h15.floor_y(model,sample_p)))
   if max(errors) > .025:
    additions.append({'uuid': h15.uid(f'w259/{name}/root/{t}'), 'channel': 'position',
        'time': t, 'interpolation': 'linear', 'data_points': [{'x': 0, 'y': floor, 'z': 0}]})
  if not additions:
   break
  assert len(keys) + len(additions) <= 256, ('floor refinement budget', name)
  root['keyframes'].extend(additions)
 summary = {
  'name': name, 'kind': 'gamblers' if name.startswith('h15_roll_') else 'marksman',
  'direction': c['direction'], 'sourceTag': tag, 'action': c['action'],
  'durationSeconds': animation['length'], 'sourceFps': 30,
  'sourceFrameRange': c['actualFrameRange'], 'clipDurationTicks': c['durationSeconds'] * 20,
  'roundedClipTicks': math.ceil(c['durationSeconds'] * 20 - 1e-9),
  'entryTicks': ENTRY_TICKS, 'assembledPoseCount': 61,
  'collinearSourceJointRepairs': {n:r for n,r in repairs.items() if r},
  'rotationRangesDegrees': {n: [[min(p[n][j] for _, p in frames), max(p[n][j] for _, p in frames)]
      for j in range(3)] for n in h15.BONES},
  'rootEulerEndpointsDegrees': [frames[0][1]['player_root'], frames[-1][1]['player_root']],
  'rootYRange': [min(h15.floor_y(model, p) for _, p in frames), max(h15.floor_y(model, p) for _, p in frames)],
 }
 return animation, summary


def validate(animation, summary):
 assert animation['loop'] == 'once' and animation['override'] is False
 g, c = clips[summary['sourceTag']]
 assert abs(animation['length'] - c['durationSeconds']) < 1e-8
 max_step = 0
 for a in animation['animators'].values():
  for channel in {k['channel'] for k in a['keyframes']}:
   keys = sorted([k for k in a['keyframes'] if k['channel'] == channel], key=lambda k: k['time'])
   times = [k['time'] for k in keys]
   assert len(times) == len(set(times)) <= 256, (a['name'], channel, len(times))
   assert times[0] == 0 and abs(times[-1] - animation['length']) < 1e-8
   assert min(b - a for a, b in zip(times, times[1:])) > .001, 'BetterModel frame comparator collision'
   assert all(k['interpolation'] == 'linear' and all(math.isfinite(float(v))
       for v in k['data_points'][0].values()) for k in keys)
   if channel == 'rotation':
    assert len(keys) == 61
    step = max(abs(b['data_points'][0][axis] - a['data_points'][0][axis])
        for a, b in zip(keys, keys[1:]) for axis in 'xyz')
    max_step = max(max_step, step)
    assert step < 120, (animation['name'], a['name'], 'Euler discontinuity', step)
   if a['name'] == 'player_root' and channel == 'position':
    assert all(k['data_points'][0]['x'] == k['data_points'][0]['z'] == 0 for k in keys)
 # Check every evaluated orientation after export and the actual target hierarchy.
 root_error = torso_error = leg_error = 0
 for i, f in enumerate(c['frames']):
  t = round(c['durationSeconds'] * i / 60, 9)
  p, y = h19.sample(animation, t)
  matrices = h19.fk(model, p, y)
  root_error = max(root_error, angle_error(w197.rotation(matrices['player_root']), source_rotation(g, f, 'C7C0BA6E')))
  for target, source in [('phip_hip','C7C0BA6E'),('pw_waist','A252A6A2'),('pc_chest','A352A6A2'),('h_ph_head','7E92D640')]:
   torso_error = max(torso_error, angle_error(w197.rotation(matrices[target]), source_rotation(g, f, source)))
  for upper, lower, chain in [('prl_right_leg','prfl_right_foreleg',['9F0FD28C','8BD44A3F','B9B9E05D']),
      ('pll_left_leg','plfl_left_foreleg',['695DAF09','35B14D1B','0F8B505D'])]:
   source_down = h19.unit(convert(h19.sub(xyz(f['joints'][chain[1]]), xyz(f['joints'][chain[0]]))))
   target_down = h19.unit(h19.sub(xyz(matrices[lower]), xyz(matrices[upper])))
   leg_error = max(leg_error, math.degrees(math.acos(max(-1,min(1,h19.dot(source_down,target_down))))))
 assert max(root_error, torso_error, leg_error) < .001, ('source pose mismatch', root_error, torso_error, leg_error)
 error = 0
 # Inspect source anchors, 240Hz envelope and every floor-segment midpoint.
 root = next(a for a in animation['animators'].values() if a['name'] == 'player_root')
 floor_times = sorted(k['time'] for k in root['keyframes'] if k['channel'] == 'position')
 times = {min(i / 240, animation['length']) for i in range(math.ceil(animation['length'] * 240) + 1)}
 times.update((a + b) / 2 for a, b in zip(floor_times, floor_times[1:]))
 for t in times:
  p, y = h19.sample(animation, t)
  error = max(error, abs(y - h15.floor_y(model, p)))
 assert error < .075, ('floor interpolation', animation['name'], error)
 # The pelvis residual intentionally becomes identity after its world rotation
 # moves to root. Root, torso, thighs and knees must still articulate.
 for n in ['player_root','pw_waist','pc_chest','prl_right_leg','prfl_right_foreleg','pll_left_leg','plfl_left_foreleg']:
  assert max(b - a for a, b in summary['rotationRangesDegrees'][n]) > 3, ('frozen full body', n)
 summary['validation'] = {'maxAdjacentEulerStepDegrees': max_step,
     'maxRootSourceOrientationErrorDegrees': root_error, 'maxTorsoSourceOrientationErrorDegrees': torso_error,
     'maxThighSourceDirectionErrorDegrees': leg_error, 'maxInterpolatedFloorErrorModelUnits': error,
     'floorEnvelopeHz': 240, 'rootPositionKeyCount': len(floor_times), 'rotationSamplesPerBone': 61}


def source_points(c, i):
 points = {n: h19.mul(convert(xyz(m)), 16) for n, m in c['frames'][i]['joints'].items()}
 center = points['C7C0BA6E']
 # A rolling skeleton's lowest point can be its head or hand, not its ankle.
 floor = min(points[n][1] for edge in CHAIN for n in edge) - 1.8
 return {n: [v[0] - center[0], v[1] - floor, v[2] - center[2]] for n, v in points.items()}


def project(v, cx, base, view):
 horizontal = v[0] + v[2] * .22 if view == 'front' else -v[2] + v[0] * .2
 return cx + horizontal * 5.6, base - v[1] * 5.6


def draw_source(draw, points, cx, base, view):
 for a, b in CHAIN:
  draw.line([project(points[a], cx, base, view), project(points[b], cx, base, view)], fill='#f5aa62', width=3)
 for n in ['8C83CB67','DE9D6BEA']:
  x,y = project(points[n], cx, base, view)
  draw.ellipse((x-3,y-3,x+3,y+3), fill='#fff0ba')


def review(animation, summary):
 paths = []
 _, c = clips[summary['sourceTag']]
 for view in ('front', 'side'):
  path = args.review_dir / (animation['name'] + '-' + view + '.png')
  if not args.verify:
   from PIL import Image, ImageDraw
   args.review_dir.mkdir(parents=True, exist_ok=True)
   indices = [0, 9, 18, 30, 42, 51, 60]
   cell = 210
   im = Image.new('RGB', (cell * len(indices), 570), '#101b28')
   draw = ImageDraw.Draw(im)
   draw.text((12, 10), animation['name'] + ' | ' + view + ' | source skeleton / target skin cubes', fill='#ffffff')
   for col, i in enumerate(indices):
    t = round(c['durationSeconds'] * i / 60, 9)
    cx = col * cell + cell / 2
    draw.text((col * cell + 10, 34), f'{t:.3f}s  pose {i}/60', fill='#ffffff')
    draw.line([(col*cell,260),((col+1)*cell,260)], fill='#536579')
    draw_source(draw, source_points(c, i), cx, 260, view)
    draw.text((col * cell + 10, 271), 'source ' + c['tag'], fill='#f5aa62')
    p, y = h19.sample(animation, t)
    faces = skin_faces(p, y)
    depth = lambda face: sum((v[2] if view == 'front' else v[0]) for v in face[0]) / 4
    for vertices, bone in sorted(faces, key=depth, reverse=True):
     color = '#63b9d2' if 'leg' in bone else '#92c5e2' if 'arm' in bone else '#c2d6e8'
     draw.polygon([project(v,cx,532,view) for v in vertices], fill=color, outline='#243d54')
    draw.line([(col*cell,532),((col+1)*cell,532)], fill='#536579')
   draw.text((12,550), 'Static FK only. Independent floor normalization; source horizontal travel omitted. Native Vision acceptance pending.', fill='#b3c5d7')
   im.save(path)
  paths.append({'path': str(path), 'sha256': sha(path)})
 return paths


def variant_review():
 paths = []
 for direction in ('front','back','left','right'):
  candidates = [c for _,c in clips.values() if c['group'] == 'hunter_marksman_dodge' and c['direction'] == direction]
  path = args.review_dir / ('marksman-variants-' + direction + '.png')
  if not args.verify:
   from PIL import Image, ImageDraw
   args.review_dir.mkdir(parents=True, exist_ok=True)
   im = Image.new('RGB', (1260, 830), '#101b28')
   draw = ImageDraw.Draw(im)
   draw.text((12, 10), 'Marksman ' + direction + ': all three original takes; front / side pairs', fill='#ffffff')
   for row,c in enumerate(candidates):
    base = 245 + row * 260
    selected = c['tag'] in SELECTION.values()
    draw.text((12,base-200), c['tag'] + (' SELECTED: compact paired hands' if selected else 'AUDIT ONLY'), fill='#a8e6a3' if selected else '#f5aa62')
    for col,i in enumerate((0,30,60)):
     draw.text((col*420+10,base-180), f'pose {i}/60', fill='#ffffff')
     for v,view in enumerate(('front','side')):
      draw_source(draw,source_points(c,i),col*420+105+210*v,base,view)
    draw.line([(0,base),(1260,base)],fill='#536579')
   draw.text((12,810), 'Source pose families are a visual choice; weapon/stance selection conditions are not decoded.', fill='#b3c5d7')
   im.save(path)
  paths.append({'path':str(path),'sha256':sha(path)})
 return paths


# Bind all evidence to the actual delivered originals and the current target rig.
source_root = Path(data['sourceRoot'])
for relative, digest in data['sourceHashes'].items():
 assert sha(source_root / relative) == digest, ('Source drift', relative)
for g in data['groups']:
 assert sha(source_root / g['source']) == g['sha256']
engine_evidence = engine_template()
old = json.loads((ROOT / 'art/weapons/w197/hunter-source-motion.json').read_text())['bones']
rest_difference = 0
for g in data['groups']:
 new = {b['name']: b for b in g['bones']}
 assert set(old) == set(new) and len(old) == 72
 rest_difference = max(rest_difference, max(abs(old[n]['restMatrix'][i][j] - new[n]['matrix'][i][j])
     for n in old for i in range(4) for j in range(4)))
assert rest_difference < .00001, 'Not the existing source rig'
animations = []
summaries = []
for name,tag in SELECTION.items():
 animation, summary = assemble(name,tag)
 validate(animation,summary)
 summary['renderReview'] = review(animation,summary)
 animations.append(animation)
 summaries.append(summary)
 print(json.dumps({'clip':name,'duration':animation['length'],**summary['validation']}), flush=True)
selected = set(SELECTION.values())
helper_paths = ['scripts/animation/build_class_ability_w255.py','scripts/build_hunter_animation_h15.py',
 'scripts/build_hunter_animation_h19.py','scripts/build_hunter_animation_h20.py','scripts/build_hunter_source_w197.py']
manifest = {
 'schemaVersion': 1,
 'generatorHashes': {'scripts/animation/build_hunter_dodge_w259.py': sha(Path(__file__)),
     **{p:sha(ROOT/p) for p in helper_paths}},
 'sourceRoot': data['sourceRoot'], 'sourceHashAlgorithm':'sha256', 'sourceHashes':data['sourceHashes'],
 'evaluatedSamples': {'path':str(args.samples.resolve()), 'sha256':sha(args.samples),
     'blenderVersion':data['blenderVersion'], 'actions':20, 'bones':72, 'samplesPerSourceClip':61,
     'sampleSpace':data['sampleSpace'], 'autoexecDisabled':True,
     'evaluationOwner':'master reopened all three source.blend files; worker consumes evaluated matrices'},
 'target': {'rig':'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel', 'rigSha256':sha(MODEL_PATH),
     'currentBetterModelTemplate':engine_evidence,
     'profileSkin':'static Steve skin cubes; actual profile/armor appearance belongs to runtime',
     'basis':C, 'axes':'source armature-object +X forward,+Y left,+Z up => target +X right,+Y up,-Z forward; outer FBX 0.01 scale/+90X wrapper excluded',
     'rootRotation':'source pelvis pose * inverse(rest), basis converted, carried by player_root; hip residual becomes identity and thighs solve relative to actual root; source pedestal is not the animated root',
     'rootTranslation':'x=z=0; original horizontal travel omitted to avoid double movement with server; Y fits lowest target skin cube including inverted head/hand contact',
     'rotationContinuity':'Rz*Ry*Rx equivalent Euler families unwrapped across all61 anchors; accumulated turns retained, no modulo360 endpoint reset and no synthetic roll curve',
     'torso':'W255 pose/rest world rotations solved against actual parents',
     'arms':'W255 shoulder-elbow-wrist directions with actual Steve link lengths and source elbow bias; reach projected to10.9 model units',
     'legs':'W255 geometric thigh/knee bend plane, negative-X knee flex, relative to shared player_root',
     'collinearJoints':'Only undefined bend planes (cross length<=1e-4) use bracketing source planes transported through the actual source upper-bone rotations; no joint position or timing edits',
     'floor':'H20 all-skin floor fit plus W255 adaptive refinement extended with quarter-point probes; <=256 keys and >1ms spacing per channel',
     'sourceVerticalTranslation':'source pedestal/pelvis translation is replaced by target floor fit; source ballistic height is not copied',
     'scale':'retarget rotations and limb directions; target rigid skin proportions retained'},
 'selection': {'gamblers':'all four unique original direction clips',
     'marksman':{'front':'80A8AA4F','back':'80A8AA50','left':'80A8AA48','right':'80A8AA4A'},
     'marksmanRationale':'Inspected all12 supplied source contact sheets: selected front/back keep hands close together; selected left/right recover into the same compact paired-hand posture. Other takes keep hands farther apart or swing independently. This is a consistent visual default, not a decoded original-game weapon/stance mapping.',
     'variantReview':variant_review()},
 'clips':summaries,
 'auditOnly':[{'tag':c['tag'],'group':c['group'],'direction':c['direction'],'action':c['action'],
     'reason':'empower is outside requested ability types' if c['group']=='hunter_empower_dodge' else 'alternate marksman take; original selection conditions unverified'}
     for _,c in clips.values() if c['tag'] not in selected],
 'sourceActions':[{'tag':c['tag'],'action':c['action'],'blend':c['blend'],'fps':c['fps'],
     'firstFrame':c['firstFrame'],'lastFrame':c['lastFrame'],'evaluatedSamples':len(c['frames']),
     'eventsUninterpreted':c['eventsUninterpreted']} for _,c in clips.values()],
 'sourceRigCompatibility':{'reference':'art/weapons/w197/hunter-source-motion.json',
     'referenceSha256':sha(ROOT/'art/weapons/w197/hunter-source-motion.json'),
     'same72BoneIds':True,'maxRestMatrixDifference':rest_difference},
 'runtimeScope':{'gamblersReplacementPrefix':'h15_roll_','marksmanPrefix':'h15_dodge_marksman_',
     'integrationOwner':'master owns selector, server travel, lifecycle, installer and Vision',
     'timing':'29/30s marksman forward; all other selected clips1s at30source fps; entryTicks is separate runtime transition, not an original event'},
 'verification':{'standalone':'finite61rotation samples per bone; source root/torso/thigh matrix checks; accumulated Euler unwrap; 240Hz floor envelope and every floor-segment midpoint; original hashes checked',
     'renderReviewStatus':'worker inspected all16 source/target front+side PNGs and4 marksman variant comparisons; inversion, directional roll, upright marksman step and recovery preserved; static review passed',
     'nativeVision':'pending master first pass and worker follow-up',
     'notRun':['Gradle','server/client/UI','original-game variant selector decoding']},
}
timing = {'schemaVersion':1,'clips':[{'name':s['name'],'durationSeconds':s['durationSeconds'],
    'entryTicks':ENTRY_TICKS} for s in summaries]}
for relative,obj in [('src/main/resources/destiny/animation/hunter_dodge_w259.animation.json',{'animations':animations}),
    ('src/main/resources/destiny/animation/hunter_dodge_w259.timing.json',timing),
    ('art/abilities/w259/dodge-motion-manifest.json',manifest)]:
 path = OUTPUT / relative
 raw = ((json.dumps(obj,separators=(',',':'),allow_nan=False) if 'resources/' in relative else
     json.dumps(obj,indent=2,allow_nan=False)) + '\n').encode()
 if args.verify:
  assert path.read_bytes() == raw, ('Reproduction differs',path)
 else:
  path.parent.mkdir(parents=True,exist_ok=True)
  path.write_bytes(raw)
