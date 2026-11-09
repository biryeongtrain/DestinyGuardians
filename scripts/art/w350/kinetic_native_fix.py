"""First native Vision binding fixes over preserved R2 geometry/atlas UVs.
Run after kinetic_quality_r2.py. No atlas rebuild or shared runtime edits.
"""
import json,copy,math,sys,hashlib
from types import SimpleNamespace
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent))
import kinetic as old
ROOT=old.ROOT;A=old.A
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def target(anchor,pitch,distance,scale=.85):
 a=math.radians(pitch);y,z=anchor[1]-8,anchor[2]-8;yy=y*math.cos(a)-z*math.sin(a);zz=y*math.sin(a)+z*math.cos(a)
 return dict(rotation=[pitch,0,0],translation=[-8.96,round(8.32-scale*yy,8),round(16*(.72-distance)-scale*zz,8)],scale=[scale]*3)
def solid_box(name,lo,hi,role):
 verts=[[hi[i] if m>>i&1 else lo[i] for i in range(3)] for m in range(8)];faces=[[3,2,0,1],[6,7,5,4],[2,6,4,0],[7,3,1,5],[2,3,7,6],[4,5,1,0]]
 return dict(name=name,vertices=verts,mesh_faces=faces,role=role)
def color_uv(w,col):
 im=Image.open(A/f'textures/item/weapon/w350/{w}.png').convert('RGBA');W,H=im.size
 for y in range(1,H-1):
  for x in range(1,W-1):
   if im.getpixel((x,y))==tuple(col)+(255,) and all(im.getpixel((x+dx,y+dy))==tuple(col)+(255,) for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]):return [16*(x+.25)/W,16*(y+.25)/H,16*(x+.75)/W,16*(y+.75)/H]
 raise ValueError((w,'no constant color island',col))
def run(w):
 ad=old.art(w);d=json.loads((ad/'parts.json').read_text());tex=A/f'textures/item/weapon/w350/{w}.png';texsha=digest(tex);design=json.loads((ad/'design.json').read_text());solids=json.loads((ad/'r2-authored-solids.json').read_text());roles=design['roles'];adjust=[];previous_manifest=json.loads((ad/'manifest.json').read_text())
 if not d.get('nativeFirstVisionFixVersion'):
  if w=='thorn':
   dy=25*21.5/1044
   for e in d['parts']['body']:
    if e['name'].startswith('sight_bead/'):
     for key in ['from','to']:e[key][1]+=dy
     e['rotation']['origin'][1]+=dy
   for rec in solids['solids']:
    if rec['name']=='sight_bead':
     for p in rec['vertices']:p[1]+=dy
   adjust.append('Lifted the existing green front bead by 0.51484674 model units above the forward roof; UV/atlas unchanged.')
  if w=='outbreak_perfected':
   oldnames={e['name'] for e in d['parts']['body'] if e['name'].startswith('sight/')};d['parts']['body']=[e for e in d['parts']['body'] if e['name'] not in oldnames];solids['solids']=[s for s in solids['solids'] if s['name']!='sight']
   for n in oldnames:roles.pop(n,None)
   uv=color_uv(w,(148,25,26));dotuv=color_uv(w,(231,49,40));cx,cy,cz=8,14.30,1.18;half=.64;hh=.83;t=.09;depth=.11
   boxes=[('sight_hood_left',[cx-half,cy-hh,cz-depth/2],[cx-half+t,cy+hh,cz+depth/2]),('sight_hood_right',[cx+half-t,cy-hh,cz-depth/2],[cx+half,cy+hh,cz+depth/2]),('sight_hood_top',[cx-half+t,cy+hh-t,cz-depth/2],[cx+half-t,cy+hh,cz+depth/2]),('sight_hood_base',[cx-half+t,cy-hh,cz-depth/2],[cx+half-t,cy-hh+t,cz+depth/2]),('sight_reticle',[cx-.018,cy-.018,cz-.022],[cx+.018,cy+.018,cz+.022])]
   for n,lo,hi in boxes:
    role='glow' if n=='sight_reticle' else 'accent';e=dict(name=n,**{'from':lo,'to':hi},faces={f:dict(uv=dotuv if role=='glow' else uv,texture='#0') for f in old.kit.FACE_AXES})
    if role=='glow':e.update(shade=False,light_emission=10)
    d['parts']['body'].append(e);roles[n]=role;solids['solids'].append(solid_box(n,lo,hi,role))
   adjust.append('Replaced opaque vertical holographic-sight slab with a physically open four-rail hood and 0.036-unit reticle; constant existing atlas islands reused.')
  d['nativeFirstVisionFixVersion']=1;old.emit(ad/'parts.json',d)
 full=d['parts']['body']+d['parts']['magazine'];solids['solidCount']=len(solids['solids']);solids['emittedElements']=len(full);solids['nativeFirstVisionAdjustments']=adjust or solids.get('nativeFirstVisionAdjustments',[]);old.emit(ad/'r2-authored-solids.json',solids)
 frame=solids['sourceFrame'];lo,hi,top,L,z0,yt=frame
 point=lambda px,py:[8,yt-(py-top)*L/(hi-lo),z0+(px-lo)*L/(hi-lo)]
 anchor,pitch,distance={'crimson':(point(248,128),2.,1.75),'thorn':(point(178,136),3.,1.90),'outbreak_perfected':([8,14.30,1.18],2.,1.10)}[w]
 ads=target(anchor,pitch,distance);s=SimpleNamespace(e=full,roles=roles,anchors=solids['anchors'],adsTarget=ads)
 if w=='outbreak_perfected':s.thirdPerson=dict(rotation=[5.729578,-17.188734,0],translation=[0,-2,2],scale=[.7]*3)
 old.BUILDERS[w]=lambda:s
 old.bake=lambda wid,shape:(d['parts'],d['texture_size'])
 old.build(w)
 generated=json.loads((ad/'manifest.json').read_text());previous_manifest.update(generated);previous_manifest.update(nativeFirstVisionFixVersion=1,solidCount=len(solids['solids']));old.emit(ad/'manifest.json',previous_manifest)
 design.update(elements=full,roles=roles,nativeFirstVisionFixVersion=1);old.emit(ad/'design.json',design)
 assert digest(tex)==texsha
 report=dict(revision='R2 first native Vision fix',sourceCapturePrefix=f'/tmp/exotic-expansion-20261109/qa/native/first-{w}',captureReview='Hip, third person, ADS endpoint and all five valid reload captures reviewed. Reload frames 3/4 return to hip; screen tutorial obscures upper barrel in some raised frames.',observedADS='All three sightlines were below/right of screen center at confirmed ADS 1.0. Original x=-5.6 leaves +0.21m lateral offset; y=-2.8 leaves a negative camera-space sight height.',sightAnchor=anchor,adsDisplay=ads,projection=dict(cameraBaseMeters=[.56,-.52,-.72],modelPivot=[8,8,8],eyeToSightMeters=distance,sightCameraSpaceMeters=[0,0,-distance]),localGeometryAdjustments=solids['nativeFirstVisionAdjustments'],thirdPerson='W327 Krait TWO_HAND compensation, same -Z-forward model basis' if w=='outbreak_perfected' else 'Preserved normal hand-cannon lowered idle stance',atlasSHA256=texsha,atlasUnchanged=True,secondNativeVision='PENDING MASTER',nativeReloadAcceptance='Return/contact inspected in first set; source motion remains authored approximation; second set required')
 old.emit(ad/'native-review-first.json',report);print(w,'ADS',ads,'elements',len(full),flush=True)
if __name__=='__main__':
 for w in sys.argv[1:] or old.IDS:run(w)
