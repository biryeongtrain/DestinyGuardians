import json,numpy as np,importlib.util,math,hashlib,base64,io,sys
from pathlib import Path
from PIL import Image
root=Path('/tmp');repo=Path('/Users/qf/IdeaProjects/DestinyGuardians');sp=importlib.util.spec_from_file_location('builder',repo/'scripts/strikes/build_devils_models.py');b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
def run(name):
 p=Path('/tmp/devils-drive-marauder-dual');m=json.loads((p/('dl_'+name+'.bbmodel')).read_text());stat=json.loads((p/'native-stats.json').read_text());reg=json.loads((p/'native-registration.json').read_text());assert len(m['elements'])<=b.MODELS[name][2];assert len(set(e['uuid'] for e in m['elements']))==len(m['elements']);assert m['name']=='dl_'+name
 for e in m['elements']:
  assert all(math.isfinite(v) for v in e['from']+e['to']);assert any(e['from'][i]==e['to'][i] for i in range(3));assert sum(f['texture'] is not None for f in e['faces'].values())==1
 im=Image.open(io.BytesIO(base64.b64decode(m['textures'][0]['source'].split(',')[1])));assert im.size==(2048,2048)
 groups={};pa={};ids=[]
 def walk(g,parent=None):
  assert g['name'] not in groups;groups[g['name']]=g;pa[g['name']]=parent
  for c in g['children']:
   if isinstance(c,dict):walk(c,g['name'])
   else:ids.append(c)
 for g in m['outliner']:walk(g)
 assert sorted(ids)==sorted(e['uuid'] for e in m['elements'])
 anim={a['name']:a for a in m['animations']};assert {'idle','walk','run','shoot','hit','damage','death','spawn'}<=set(anim)
 for a in m['animations']:
  assert a['length']>0
  for an in a['animators'].values():
   assert an['name'] in groups
   for k in an['keyframes']:
    assert 0<=k['time']<=a['length']+1e-5;assert all(math.isfinite(float(v)) for dp in k['data_points'] for v in dp.values())
 motion=np.load('/tmp/devils-models-evidence/'+name+'_motion.npz',allow_pickle=True);meta=json.loads(str(motion['meta']));idx={str(n):i for i,n in enumerate(motion['names'])};bm=b.spec_for(name,b.baker())['bones'];basis=np.array([[1,0,0],[0,0,1],[0,-1,0]],float);maxp=0.;maxr=0.;samples=0
 def vals(an,ch,t):
  if not an:return np.zeros(3)
  keys=sorted((k for k in an['keyframes'] if k['channel']==ch),key=lambda x:x['time'])
  if not keys:return np.zeros(3)
  times=[k['time'] for k in keys];v=np.array([[float(k['data_points'][0][c]) for c in 'xyz'] for k in keys]);return np.array([np.interp(t,times,v[:,i]) for i in range(3)])
 def rot(v):
  x,y,z=np.deg2rad(v);cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z);return np.array([[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],[sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],[-sy,cy*sx,cy*cx]])
 def pose(a,t):
  ans={v['name']:v for v in a['animators'].values()};pos={};rs={}
  for n,g in groups.items():
   origin=np.array(g['origin']);local=vals(ans.get(n),'position',t);R=rot(vals(ans.get(n),'rotation',t));parent=pa[n]
   if parent:pos[n]=pos[parent]+rs[parent]@(origin-np.array(groups[parent]['origin'])+local);rs[n]=rs[parent]@R
   else:pos[n]=origin+local;rs[n]=R
  return pos,rs
 for clip in meta:
  a=anim['source_'+clip['name'].lower()];mats=motion['clip_'+clip['name']]
  for frame in sorted(set([0,len(mats)//2,len(mats)-1])):
   pos,rs=pose(a,frame/30)
   for n,h in bm.items():
    i=idx[h];src=mats[frame,i,:3,3]*reg['scale'];expected=np.array([src[0]*stat['k'],src[2]*stat['k']+stat['y0'],-src[1]*stat['k']]);maxp=max(maxp,float(abs(pos[n]-expected).max()));R=mats[frame,i,:3,:3]@np.linalg.inv(motion['rest'][i,:3,:3]);u,_,v=np.linalg.svd(R);R=basis@(u@v)@basis.T;maxr=max(maxr,float(abs(rs[n]-R).max()));samples+=1
 assert maxp<.003,(name,maxp);assert maxr<.0001,(name,maxr)
 if name in ('acolyte','knight'):
  assert any(e['name'].startswith('weapon_') for e in m['elements']);assert any('weapon_source' in r for r in m['devils_lair']['source']['compatibility_repairs'])
 if name=='brig':
  assert {'armor_plate','weakpoint_glow','optics_glow'}<=set(groups);assert pa['optics_glow']=='armor_plate';assert any(e['name'].startswith('armor_plate_') for e in m['elements']);assert any(e['name'].startswith('weakpoint_glow_') and e.get('light_emission')==15 for e in m['elements']);assert any(e['name'].startswith('spine_upper_') for e in m['elements']);assert any('Dusk_authored_dye' in r for r in m['devils_lair']['source']['compatibility_repairs'])
 source=m['devils_lair']['source']
 if 'source_sha256' in source:assert hashlib.sha256(Path(source['source_blend']).read_bytes()).hexdigest()==source['source_sha256']
 for row in source.get('resolved_shader_images',[]):assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']
 result={'name':name,'model_sha256':hashlib.sha256((p/('dl_'+name+'.bbmodel')).read_bytes()).hexdigest(),'quads':len(m['elements']),'clips':len(anim),'serialized_native_fk_samples':samples,'max_position_error_px':maxp,'max_rotation_matrix_error':maxr,'mean_luma':stat['mean_luma'],'luma_reference_below80':stat['mean_luma']<80,'game_qa':'pending'};(p/'native-validation.json').write_text(json.dumps(result,indent=2));print('VERIFIED',result,flush=True)
for name in (sys.argv[1:] or ['thrall','acolyte','knight','wizard','servitor','sepiks','brig']):run(name)
