from pathlib import Path
import importlib.util,json,math,hashlib
R=Path(__file__).resolve().parents[4];A=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('kit',R/'scripts/art/w325/kit.py');k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k)
d=json.loads((R/'src/main/resources/destiny/weapon_skins/brigands_law.json').read_text());es=[e for v in d['parts'].values() for e in v];des=json.loads((A/'design.json').read_text())
for e in es:
 assert all(-16<=e['from'][i]<e['to'][i]<=32 for i in range(3)),e['name']
 assert len(e['faces'])==6
 for f in e['faces'].values():assert all(0<=v<=16 for v in f['uv']) and f['texture']=='#0'
assert len(es)<1000 and len(set(e['name'] for e in es))==len(es)
def dot(a,b):return sum(a[i]*b[i] for i in range(3))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def obb(e):
 c=k.rotate(tuple((e['from'][i]+e['to'][i])/2 for i in range(3)),k.rot_of(e));axes=[k.rotate_vec(tuple(int(j==i) for j in range(3)),k.rot_of(e)) for i in range(3)];h=[(e['to'][i]-e['from'][i])/2 for i in range(3)];return c,axes,h
O=[obb(e) for e in es]
def intersects(a,b,tol=.025):
 c,u,h=a;d,v,g=b;delta=[d[i]-c[i] for i in range(3)]
 for ax in u+v+[cross(x,y) for x in u for y in v]:
  nn=math.sqrt(dot(ax,ax))
  if nn<1e-7:continue
  if abs(dot(delta,ax))>sum(h[i]*abs(dot(u[i],ax))+g[i]*abs(dot(v[i],ax)) for i in range(3))+tol*nn:return False
 return True
adj=[set() for e in es]
for i in range(len(es)):
 for j in range(i):
  if intersects(O[i],O[j]):adj[i].add(j);adj[j].add(i)
seen=set();comps=[]
for i in range(len(es)):
 if i in seen:continue
 q=[i];out=[];seen.add(i)
 while q:
  x=q.pop();out.append(es[x]['name'])
  for y in adj[x]-seen:seen.add(y);q.append(y)
 comps.append(out)
source=json.loads((A/'source-evaluation.json').read_text());assert hashlib.sha256(Path(source['source']).read_bytes()).hexdigest()==source['sha256']
from PIL import Image
im=Image.open(R/'src/main/resources/assets/destiny/textures/item/weapon/w327/brigands_law.png');assert list(im.size)==d['texture_size']
report=dict(revision=3,parse='PASS',strict_positive_boxes='PASS',unique_names='PASS',normalized_uv='PASS',elements=len(es),parts={p:len(v) for p,v in d['parts'].items()},atlas=list(im.size),rotated_elements=sum(bool(e.get('rotation')) for e in es),source_original_unchanged=True,connection_method='Native rotated OBB separating-axis test, 0.025px tolerance; solid overlap/contact adjacency',connected_components=comps,connections='PASS' if len(comps)==1 else 'REVIEW',native_pack_load='MASTER_PENDING',native_hand_ads_reload='MASTER_PENDING',native_10_20_display='MASTER_PENDING')
(A/'validation.json').write_text(json.dumps(report,indent=1)+'\n');print('components',len(comps),[len(c) for c in comps]);print([c for c in comps if len(c)<20])
