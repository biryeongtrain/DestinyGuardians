from pathlib import Path
import json
p=Path('/Users/qf/.codex/worktrees/legendary-models-rifles/DestinyGuardians/art/animation/w337/maul-grip/review.py');g={'__file__':str(p),'__name__':'inspect'};exec(p.read_text().split("\nreport=")[0],g)
h=g['h'];m=g['m'];model=g['model'];mesh=g['mesh'];a=g['a'];fk=g['frame'](a['w230_titan_burning_maul_idle'],3.425)[3]
def obb(lo,hi,transform):
 c=[(x+y)/2 for x,y in zip(lo,hi)];wc=transform(c);axes=[];r=[]
 for dim in range(3):
  v=list(c);v[dim]+=1;axes.append(h.unit(h.sub(transform(v),wc)));r.append((hi[dim]-lo[dim])/2)
 return wc,axes,r
bodies=[];groups={x['uuid']:x for x in model['groups']};elements={x['uuid']:x for x in model['elements']}
def walk(nodes,parent=None):
 for node in nodes:
  if isinstance(node,str):
   e=elements[node]
   if e.get('name')!='skin' or parent['name']not in ['h_ph_head','pc_chest','pra_right_arm','pla_left_arm','prfa_right_forearm','plfa_left_forearm']:continue
   bone=parent['name'];origin=parent['origin'];bodies.append((bone,obb(e['from'],e['to'],lambda p:h.point(fk[bone],h.sub(p,origin)))))
  else:walk(node['children'],groups[node['uuid']])
walk(model['outliner'])
def props(item):
 result=[]
 for e in mesh['elements']:
  if e['from'][1]<20 or min(y-x for x,y in zip(e['from'],e['to']))<1e-5:continue
  rot=e.get('rotation',{});o=rot.get('origin',[8,8,8]);angles=[rot.get(k,0)for k in ['x','y','z']]
  if'axis'in rot:angles['xyz'.index(rot['axis'])]=rot['angle']
  R=m.h15.rot(angles)
  transform=lambda p:h.point(item,h.add(h.sub(h.add(h.vector(R,h.sub(p,o)),o),[8,8,8]),[0,2,0]))
  result.append((e.get('name'),obb(e['from'],e['to'],transform)))
 return result

def overlap(a,b):
 ac,aa,ar=a;bc,ba,br=b;delta=h.sub(bc,ac);values=[]
 for axis in aa+ba+[h.cross(x,y)for x in aa for y in ba]:
  if h.norm(axis)<1e-8:continue
  axis=h.unit(axis);radius=sum(r*abs(h.dot(axis,d))for r,d in zip(ar,aa))+sum(r*abs(h.dot(axis,d))for r,d in zip(br,ba));values.append(radius-abs(h.dot(delta,axis)))
 return min(values)

results=[]
for lower in [5.25]:
 item=[list(row)for row in fk['pri_right_item']]
 checks=[]
 for bone,body in bodies:
  name,distance=max([(name,overlap(body,prop))for name,prop in props(item)],key=lambda pair:pair[1]);checks.append({'body':bone,'headElement':name,'overlapDepthUnits':max(0,distance),'separatingGapUnits':max(0,-distance)})
 results.append({'lowerGripRawY':lower,'checks':checks})
print(json.dumps(results,indent=2))
Path('/Users/qf/.codex/worktrees/legendary-models-rifles/DestinyGuardians/art/animation/w337/maul-grip/render-pose-overlap.json').write_text(json.dumps(results,indent=2)+'\n')
