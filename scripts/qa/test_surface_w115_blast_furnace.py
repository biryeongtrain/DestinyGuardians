#!/usr/bin/env python3
"""Independent W118 Blast Furnace R5 product regressions. No DCC/game writes.

Spatial tolerances are in original model units. Bounds and source-vertex-to-solid
coverage <=0.1 reject frozen R2's lost stock/well/foreguard features. Projected
cuboid overreach remains an explicitly disclosed approximation, not exact mesh
fidelity. Opaque primary surfaces independently reject all R2 alpha-card panels.
"""
import base64,hashlib,importlib.util,io,itertools,json,math,subprocess,sys,unittest
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'art/weapons/w115/blast_furnace'
GEN=ROOT/'scripts/generate_surface_w115_blast_furnace.py'
PINS={'src/main/resources/assets/destiny/models/weapon/pulse_rifle/blast_furnace.json': 'f3922a28cc58de8c7a7f965ba3464aeb5841d1a53bde72bf74d58e48aca39706', 'src/main/resources/assets/destiny/textures/item/weapon/w30/blast_furnace.png': '0f252ca03244d8b2d7d5c63e9d67c90dc87e6bbac3faeb402572aacb7df4cd91', 'art/blockbench/weapons/w30/blast_furnace.bbmodel': '1bc6e5720e7579a952550ca30795bcd31df02c8c5e5e78f0539d0d854f669bc4', 'art/weapons/w114/blast_furnace/partition-audit.json': '300adc56f67dc112d9cbec491400f1d6cde762b879b0235b5de33ee8ffeef0e8', 'art/weapons/w114/blast_furnace/inspection.bbmodel': '8a27b109475e7c27809a571256df57996e5d319640f3a816259faeaaf4fde367', 'src/main/resources/assets/destiny/models/weapon_reload_w114_blast_furnace/blast_furnace_body.json': '1c92741af670629976269083b2c054efd6d9d28087da61e19b6226c255ff665a', 'src/main/resources/assets/destiny/models/weapon_reload_w114_blast_furnace/blast_furnace_magazine.json': '32e31c399e609adaea4319ca17208420d0b62e44b624cc2de8e1742d4baa5397', 'scripts/generate_reload_w114_blast_furnace.py': '72a071ad4e6e298e74e61e187bc8e28fca5015985329c881af30c13eaf577d14', 'art/weapons/w114/blast_furnace/gameplay-contact.png': '52d91dbbc6e38c112ad04c85c36140eddb49e489d60b8f267924839a93671aed', 'art/weapons/w114/blast_furnace/partition-contact.png': 'd2d69837dc80bf32ef1e66198a73b385f4578fd6c2dbd5ad8c8b9f8552223503', 'art/weapons/w83/model/offline-preview.png': 'c7ea56fd490d3246bf8a0824294d0fcd758d964087e414e26aa9ff228c9d9bad', 'art/weapons/w84/model/offline-preview.png': '6d46a9dcb52171e71c1e6470b0afe79a65c516a8fc78911191feb6b0de3ea7b8', 'src/main/resources/assets/destiny/models/item/weapon/ace_of_spades.json': 'bb40d48c86fc75b0e509b1b98c87eb8dde879c3e4c11a389f48928043025d69f', 'art/weapons/w84/model/source/izanagi.bbmodel': '9ae28369f80ff0f81bb7e1344ee50b618b9a2de62dcafc631287084dbe3c8f31'}
FACES={'north','south','west','east','up','down'}
NORMALS={'north':(0,0,-1),'south':(0,0,1),'west':(-1,0,0),'east':(1,0,0),'up':(0,1,0),'down':(0,-1,0)}
def read(path):return json.loads(path.read_bytes())
def sha(data):return hashlib.sha256(data).hexdigest()

def box(e):
 # Independent Euler implementation. Columns are the rotated local basis.
 r=e.get('rotation',{});angles=np.radians([r.get(a,0) for a in ('x','y','z')])
 cx,cy,cz=np.cos(angles);sx,sy,sz=np.sin(angles)
 rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
 ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
 rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
 axes=rz@ry@rx;lo=np.array(e['from']);hi=np.array(e['to']);o=np.array(r.get('origin',[0,0,0]))
 return axes@((lo+hi)/2-o)+o,axes,(hi-lo)/2

def corners(e):
 c,a,h=box(e);return np.array([c+a@(h*np.array(s)) for s in itertools.product((-1,1),repeat=3)])

def inside(points,e,margin=0):
 c,a,h=box(e);return np.all(np.abs((np.asarray(points)-c)@a)<=h+margin,axis=-1)

def triangle_distances(points,triangles):
 t=np.asarray(triangles);p=np.asarray(points);result=[]
 for point in p:
  a=t[:,0];u=t[:,1]-a;v=t[:,2]-a;n=np.cross(u,v);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-20);offset=point-a;d=np.sum(offset*n,axis=1);q=offset-d[:,None]*n
  uu=np.sum(u*u,1);vv=np.sum(v*v,1);uv=np.sum(u*v,1);qu=np.sum(q*u,1);qv=np.sum(q*v,1);det=uu*vv-uv*uv;safe=np.where(abs(det)>1e-22,det,1e22);x=(qu*vv-qv*uv)/safe;y=(qv*uu-qu*uv)/safe;best=np.where((abs(det)>1e-22)&(x>=-1e-8)&(y>=-1e-8)&(x+y<=1+1e-8),abs(d),np.inf)
  for i,j in ((0,1),(1,2),(2,0)):
   edge=t[:,j]-t[:,i];fraction=np.clip(np.sum((point-t[:,i])*edge,1)/np.maximum(np.sum(edge*edge,1),1e-22),0,1);closest=t[:,i]+fraction[:,None]*edge;best=np.minimum(best,np.linalg.norm(point-closest,axis=1))
  result.append(best.min())
 return np.array(result)

def touches(a,b,tolerance=1e-6):
 ca,aa,ha=box(a);cb,ab,hb=box(b);delta=cb-ca
 axes=[*aa.T,*ab.T,*[np.cross(x,y) for x in aa.T for y in ab.T]]
 for v in axes:
  n=np.linalg.norm(v)
  if n<1e-9:continue
  v=v/n
  if abs(delta@v)>sum(ha*np.abs(aa.T@v))+sum(hb*np.abs(ab.T@v))+tolerance:return False
 return True


class SurfaceProduct(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.design=read(ART/'design.json');cls.manifest=read(ART/'manifest.json')
  cls.models={p:read(ROOT/f'src/main/resources/assets/destiny/models/weapon_surface_w115/blast_furnace_{p}.json') for p in ('body','magazine')}
  cls.parts={p:m['elements'] for p,m in cls.models.items()};cls.elements=sum(cls.parts.values(),[])
  cls.specs=sum(cls.design['parts'].values(),[]);cls.named={e['name']:e for e in cls.elements}
  cls.spec_by_name={s['name']:s for s in cls.specs}
  cls.texture=ROOT/'src/main/resources/assets/destiny/textures/item/weapon/w115/blast_furnace.png';cls.atlas=np.array(Image.open(cls.texture))
  cls.owned=next(f['owned_paths'] for f in read(ROOT/'docs/qa/2026-10-25/w118/batch.json')['features'] if f['name']=='w118-blast_furnace')
  spec=importlib.util.spec_from_file_location('bf_w116',GEN);cls.gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.gen)
  cls.sources=cls.gen.source_data();cls.r2=read(ROOT/'docs/qa/2026-10-25/w116/r2-inputs/art/weapons/w115/blast_furnace/design.json')
  cls.bycomp={}
  for s in cls.specs:cls.bycomp.setdefault((s['source_mesh'],s['source_component']),[]).append(s)
  cls.spatial={}
  for key,ss in cls.bycomp.items():
   m=cls.sources[key[0]];tri=np.array(m['vertices'])[np.array(m['faces'])[m['components'][key[1]]['sourcePolygonIndices']]];p=np.unique(tri.reshape(-1,3),axis=0);vv=np.concatenate([np.array(s['support_triangles']).reshape(-1,3) if s['kind']=='alpha_patch' else corners(cls.named[s['name']]) for s in ss]);dist=[]
   for s in ss:
    c,a,h=box(cls.named[s['name']]);dist.append(triangle_distances(p,s['support_triangles']) if s['kind']=='alpha_patch' else np.linalg.norm(np.maximum(abs((p-c)@a)-h,0),axis=1))
   cls.spatial[key]=(np.array([p.min(0),p.max(0)]),np.array([vv.min(0),vv.max(0)]),np.min(dist,axis=0),tri)

 def test_01_pinned_original_inputs_and_common_helper(self):
  self.assertTrue(PINS.items()<=self.design['input_pins'].items())
  for rel,pin in self.design['input_pins'].items():
   p=Path(rel) if Path(rel).is_absolute() else ROOT/rel
   with self.subTest(path=rel):self.assertEqual(sha(p.read_bytes()),pin)
  self.assertEqual(sha((ROOT/'scripts/mesh/native_triangle_elements_w115.py').read_bytes()),self.design['compilerSha256'])

 def test_02_native_cuboids_and_source_supported_native_planes_no_raw_mesh(self):
  for m in self.models.values():
   self.assertEqual(set(m),{'credit','textures','elements'});self.assertTrue(m['elements'])
   self.assertEqual(m['textures'],{'0':'destiny:item/weapon/w115/blast_furnace','particle':'destiny:item/weapon/w115/blast_furnace'})
   for e in m['elements']:
    size=np.array(e['to'])-e['from'];spec=self.spec_by_name[e['name']]
    if spec['kind']=='alpha_patch':
     self.assertTrue((size[:2]>0).all());self.assertEqual(size[2],0);self.assertEqual(set(e['faces']),{'north','south'})
     uv=e['faces']['south']['uv'];self.assertEqual(e['faces']['north']['uv'],[uv[2],uv[1],uv[0],uv[3]])
     self.assertTrue(spec.get('neck_patch'));self.assertIn(spec['source_component'],(3,10))
    elif spec.get('opaque_source_plane'):
     self.assertTrue((size[:2]>0).all());self.assertEqual(size[2],0);self.assertEqual(set(e['faces']),{'north','south'})
    else:self.assertTrue((size>0).all())
    self.assertTrue(e['faces']);self.assertLessEqual(set(e['faces']),FACES)
    self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
    self.assertTrue(all(-16<=x<=32 for k in ('from','to') for x in e[k]))
    for f in e['faces'].values():
     self.assertEqual(f['texture'],'#0');self.assertTrue(all(0<=v<=16 for v in f['uv']))
     self.assertNotEqual(f['uv'][0],f['uv'][2]);self.assertNotEqual(f['uv'][1],f['uv'][3])

 def test_03_unique_named_parts_exact_owned_W118_scope(self):
  self.assertEqual(len(self.named),len(self.elements));self.assertEqual([s['name'] for s in self.specs],[e['name'] for e in self.elements])
  self.assertEqual(set(self.parts),{'body','magazine'});self.assertEqual(set(self.manifest['changedPaths']),set(self.owned));self.assertEqual(len(self.owned),11)
  self.assertIn('docs/qa/2026-10-25/w118/blast_furnace-worker.md',self.owned)
  self.assertEqual(self.manifest['revision'],5);self.assertEqual(self.manifest['stage'],'W118')

 def test_04_original_frame_grip_sight_heights_pivots(self):
  v=np.concatenate([np.array(m['vertices']) for m in self.sources]);p=np.concatenate([np.array(s['support_triangles']).reshape(-1,3) if s['kind']=='alpha_patch' else corners(self.named[s['name']]) for s in self.specs])
  np.testing.assert_allclose([p.min(0),p.max(0)],[v.min(0),v.max(0)],atol=.03)
  self.assertEqual(self.manifest['partPivots'],{'body':[8,8,8],'magazine':[8,8,8]});self.assertEqual(self.design['coordinate_frame']['muzzle_axis'],'-Z')
  for key in ((0,6),(0,18),(1,0),(2,0)):
   a,b,_,_=self.spatial[key];np.testing.assert_allclose(a,b,atol=.1)

 def test_05_actual_face_and_element_budget(self):
  self.assertLessEqual(len(self.elements),2048);n=sum(len(e['faces']) for e in self.elements);self.assertLessEqual(n,6144)
  self.assertEqual(self.manifest['cubeCount'],len(self.elements));self.assertEqual(self.manifest['quadCount'],n)
  self.assertEqual(self.manifest['primitiveTypes'],{'cuboid':sum(s['kind']=='cuboid' and not s.get('opaque_source_plane') for s in self.specs),'opaque_plane':sum(bool(s.get('opaque_source_plane')) for s in self.specs),'alpha_patch':sum(s['kind']=='alpha_patch' for s in self.specs)})
  self.assertEqual(self.manifest['partCounts'],{p:len(es) for p,es in self.parts.items()})
  self.assertEqual(self.manifest['elementCount'],len(self.elements));self.assertEqual(self.manifest['solidCuboidCount'],self.manifest['primitiveTypes']['cuboid']);self.assertEqual(self.manifest['opaquePlaneCount'],self.manifest['primitiveTypes']['opaque_plane']);self.assertEqual(self.manifest['alphaPatchCount'],self.manifest['primitiveTypes']['alpha_patch'])

 def test_06_all270_components_and29124_source_triangles(self):
  expected={(i,j) for i,m in enumerate(self.sources) for j in range(len(m['components']))};self.assertEqual(len(expected),270);self.assertEqual(set(self.bycomp),expected)
  ledger={(r['source_mesh'],r['source_component']):r for r in self.design['componentSpecs']};self.assertEqual(set(ledger),expected)
  self.assertEqual(sum(r['sourceTriangleCount'] for r in ledger.values()),29124)
  for key,ss in self.bycomp.items():self.assertEqual(ledger[key]['elements'],len(ss))

 def test_07_source_skin_boundary_no_fixed_magazine_stub(self):
  moving=set();count=0
  for i,m in enumerate(self.sources):
   for j,c in enumerate(m['components']):
    labels={m['faceMagazine'][f] for f in c['sourcePolygonIndices']};self.assertEqual(len(labels),1)
    if True in labels:moving.add((i,j));count+=len(c['sourcePolygonIndices'])
  self.assertEqual((len(moving),count),(7,681))
  self.assertEqual({(s['source_mesh'],s['source_component']) for s in self.design['parts']['magazine']},moving)
  self.assertFalse(moving & {(s['source_mesh'],s['source_component']) for s in self.design['parts']['body']})
  for part,ss in self.design['parts'].items():self.assertTrue(all(s['source_bone']==('Magazine' if part=='magazine' else 'Pedestal') for s in ss))

 def test_08_independent_per_component_extents_not_just_membership(self):
  rows={(r['source_mesh'],r['source_component']):r for r in self.manifest['spatialFidelity']}
  for key,(a,b,dist,_) in self.spatial.items():
   with self.subTest(component=key):
    self.assertLessEqual(float(abs(a-b).max()),.1)
    np.testing.assert_allclose(rows[key]['sourceBounds'],a,atol=1e-7);np.testing.assert_allclose(rows[key]['productBounds'],b,atol=1e-7)
    self.assertAlmostEqual(rows[key]['extentDeviationMax'],float(abs(a-b).max()),places=6)

 def test_09_independent_source_vertices_to_effective_solids_and_surfaces(self):
  for key,(_,_,dist,_) in self.spatial.items():
   with self.subTest(component=key):self.assertLessEqual(float(dist.max()),.1)

 def test_10_frozen_R2_negative_control_rejects_missing_anatomy(self):
  for key in ((0,5),(0,29),(0,45),(0,12)):
   old=[s for ss in self.r2['parts'].values() for s in ss if (s['source_mesh'],s['source_component'])==key]
   p=np.concatenate([np.array(s['support_triangles']).reshape(-1,3) if s['kind']=='alpha_patch' else corners(s) for s in old]);a,b,_,_=self.spatial[key]
   self.assertGreater(float(abs(np.array([p.min(0),p.max(0)])-a).max()),.1)
   self.assertLessEqual(float(abs(b-a).max()),.1)
  oldplanes=[s for ss in self.r2['parts'].values() for s in ss if s['kind']=='alpha_patch'];self.assertGreater(len(oldplanes),1000)
  self.assertTrue(all(s['kind']=='cuboid' for s in self.specs if not s.get('neck_patch')))

 def test_11_broad_planar_coherent_panels_no_QEM_fins(self):
  for ci in (0,2,8,12,16,18,24,29,34):
   ss=[p for p in self.bycomp[0,ci] if not p.get('surface_panel')];self.assertTrue(all(s['kind']=='cuboid' for s in ss))
   # Continuous cap-normal frames, no sliver-triangle normals or QEM bridges.
   rotations={tuple(s['rotation'][a] for a in 'xyz') for s in ss};self.assertEqual(len(rotations),1)
   areas=sorted([float(np.prod(sorted(np.array(s['to'])-s['from'])[-2:])) for s in ss],reverse=True)
   self.assertGreater(areas[0],.4)
  self.assertTrue(all(r['profileOverreachMax']<=.5 for r in self.manifest['spatialFidelity']))

 def test_12_original_rotated_grip_magazine_not_grid_quantized(self):
  for ci,angle in ((6,-26.732485083748223),(18,17.959959518075436)):
   for s in self.bycomp[0,ci]:self.assertAlmostEqual(s['rotation']['x'],angle)
  values=np.array([v for e in self.elements for v in e['from']]);self.assertGreater((abs(values*16-np.round(values*16))>1e-4).mean(),.9)
  self.assertFalse(any('voxel' in e['name'] or 'grid' in e['name'] for e in self.elements))

 def test_13_primary_panels_opaque_and_clean_material_palette(self):
  self.assertEqual(self.atlas.shape,(1024,1024,4));self.assertEqual(set(np.unique(self.atlas[:,:,3])),{0,255})
  opaque=self.atlas[self.atlas[:,:,3]>0,:3];self.assertLessEqual(len(np.unique(opaque,axis=0)),60)
  for e in self.elements:
   if self.spec_by_name[e['name']]['kind']=='alpha_patch':continue
   for f in e['faces'].values():
    u,v,w,z=np.array(f['uv'])*64;x0,x1=sorted([u,w]);y0,y1=sorted([v,z]);samples=self.atlas[max(0,int(y0)):min(1024,int(y1)+1),max(0,int(x0)):min(1024,int(x1)+1),3]
    self.assertTrue(samples.size);self.assertTrue((samples==255).all(),e['name'])

 def test_14_component_islands_and_duplicated_two_pixel_gutters(self):
  occupied=np.zeros((1024,1024),bool)
  for row in self.manifest['atlasComponents']+self.manifest['atlasPatches']:
   x,y,w,h=row['pixels'];self.assertEqual(row['gutter'],2)
   sl=np.s_[y-2:y+h+2,x-2:x+w+2];self.assertFalse(occupied[sl].any());occupied[sl]=True
   expected=np.pad(self.atlas[y:y+h,x:x+w],((2,2),(2,2),(0,0)),mode='edge');np.testing.assert_array_equal(self.atlas[sl],expected)
  self.assertEqual(len(self.manifest['atlasComponents']),270)

 def test_15_original_rear_port_and_receiver_recess_materials(self):
  rows={(r['source_mesh'],r['source_component']):r for r in self.manifest['atlasComponents']}
  def pixel(ci,z,y):
   x0,y0,w,h=rows[0,ci]['pixels'];lo,hi=np.array(self.bycomp[0,ci][0]['profile_frame_bounds']);x=x0+int((z-lo[2])/(hi[2]-lo[2])*(w-1));yy=y0+int((hi[1]-y)/(hi[1]-lo[1])*(h-1));return self.atlas[yy,x,:3]
  self.assertLess(pixel(12,14.08,12.50).mean(),60);self.assertGreater(pixel(12,14.08,12.28).mean(),120)
  self.assertLess(pixel(0,14.08,12.50).mean(),60);self.assertGreater(pixel(0,14.08,12.28).mean(),120)
  self.assertLess(pixel(0,11.1,12.05).mean(),100);self.assertGreater(pixel(0,11.1,12.4).mean(),100)
  self.assertEqual(sum(r['source_edge_repair'] for r in self.specs if 'source_edge_repair' in r),20)

 def test_16_hidden_faces_covered_only_by_same_reload_part(self):
  # Independent solid sample check: removed faces must be covered just outside by
  # another cube of THIS part, never by the assembled/moving other part.
  for part,all_es in self.parts.items():
   es=[e for e in all_es if self.spec_by_name[e['name']]['kind']=='cuboid'];centers=np.array([box(e)[0] for e in es]);axes=np.array([box(e)[1] for e in es]);half=np.array([box(e)[2] for e in es])
   for idx,e in enumerate(es):
    c,a,h=box(e)
    for face in FACES-set(e['faces']):
     n=np.array(NORMALS[face]);axis=int(np.argmax(abs(n)))
     if np.prod(np.delete(2*h,axis))<1e-16:continue
     uv=[j for j in range(3) if j!=axis];ps=[]
     for u,v in itertools.product((-.98,0,.98),repeat=2):
      q=n*h;q[uv]=[u*h[uv[0]],v*h[uv[1]]];ps.append(c+a@(q+n*5e-7))
     q=np.einsum('pni,nij->pnj',np.array(ps)[:,None]-centers,axes);covered=np.all(abs(q)<=half+1e-8,axis=2);covered[:,idx]=False
     if not covered.any(1).all():
      # Separate exact coincident-face ownership, not relaxed internal coverage.
      onface=np.array(ps)- (a@n)*5e-7;owner=np.zeros(len(ps),bool);worldnormal=a@n
      for j,other in enumerate(es):
       if j==idx:continue
       cc,aa,hh=box(other)
       for ff in other['faces']:
        nn=np.array(NORMALS[ff]);ww=aa@nn
        if ww@worldnormal<1-1e-10:continue
        plane=cc+aa@(nn*hh)
        if abs((onface[0]-plane)@ww)>1e-8:continue
        owner |= inside(onface,other,margin=1e-8)
      self.assertTrue((covered.any(1)|owner).all(),(part,e['name'],face))

 def test_17_original_openings_not_solid_bounding_boxes(self):
  # Center of actual muzzle bore / trigger opening / stock opening stays open.
  probes=[((0,19),[8,12.785,-6.6]),((0,7),[8,9.7,5.5]),((0,12),[8,11.7,16.1])]
  for key,p in probes:self.assertFalse(any(inside([p],self.named[s['name']],margin=-1e-7)[0] for s in self.bycomp[key]),key)

 def test_18_editable_embedded_inspection_native_RzRyRx(self):
  bb=read(ART/'inspection.bbmodel');self.assertEqual(bb['resolution'],{'width':1024,'height':1024});self.assertEqual(len(bb['elements']),len(self.elements))
  self.assertEqual([g['name'] for g in bb['outliner']],['body','magazine']);self.assertEqual({tuple(g['origin']) for g in bb['outliner']},{(8,8,8)})
  self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),self.texture.read_bytes())
  for b,e in zip(bb['elements'],self.elements):
   self.assertEqual(b['name'],e['name']);self.assertEqual(b['rotation'],[e['rotation'][a] for a in 'xyz'])
   for f in FACES:self.assertEqual(b['faces'][f]['texture'],0 if f in e['faces'] else None)

 def test_19_six_draft_eight_view_actual_offline_comparison(self):
  im=Image.open(ART/'comparison.png');self.assertEqual(im.size,(4200,3020));a=np.array(im)
  for row in range(8):
   for col in range(6):
    crop=a[110+370*row:390+370*row,700*col:700*(col+1),0]
    self.assertGreater(int(((crop>=50)|(crop<=20)).sum()),100)
  s=GEN.read_text();self.assertIn('RAW / 29124 original triangles',s);self.assertIn('HIGH TOP / ADS SURFACES',s);self.assertIn('NOT IN-GAME',s);self.assertIn('MAGAZINE REMOVED',s)
  self.assertEqual(self.r2['revision'],2);self.assertEqual(self.design['rejected_r1']['cubeCount'],71) if 'cubeCount' in self.design['rejected_r1'] else None

 def test_20_reload_moves_whole_original_magazine_group(self):
  v=np.concatenate([corners(e) for e in self.parts['magazine']]);self.assertLess(v[:,1].max()-5.5,6)
  captured=[i for r in self.design['componentSpecs'] if r['source_bone']=='Magazine' for i in r['captured_triangle_ids']]
  self.assertEqual(len(set(captured)),681)

 def test_21_manifest_hashes_exact_delivery_scope(self):
  self.assertEqual(set(self.manifest['deliverySha256']),set(self.owned)-{'art/weapons/w115/blast_furnace/manifest.json'})
  for rel,pin in self.manifest['deliverySha256'].items():self.assertEqual(sha((ROOT/rel).read_bytes()),pin,rel)
  self.assertFalse(self.manifest['nativeAcceptance']);self.assertFalse(self.design['nativeAcceptance'])

 def test_22_repeat_generation_deterministic_and_verify_read_only(self):
  before={p:sha((ROOT/p).read_bytes()) for p in self.owned}
  output=self.gen.generate()
  for rel,data in output.items():self.assertEqual((ROOT/rel).read_bytes(),data,str(rel))
  cp=subprocess.run(['rtk','proxy',sys.executable,str(GEN),'--verify'],cwd=ROOT,text=True,capture_output=True)
  self.assertEqual(cp.returncode,0,cp.stdout+cp.stderr)
  self.assertEqual(before,{p:sha((ROOT/p).read_bytes()) for p in self.owned})


 def test_23_R3_component_fidelity_not_deteriorated(self):
  before={(r['source_mesh'],r['source_component']):r for r in self.design['previous_r3']['spatialFidelity']}
  for row in self.manifest['spatialFidelity']:
   key=row['source_mesh'],row['source_component']
   for metric in ('extentDeviationMax','sourceCoverageMax','profileOverreachMax'):
    self.assertLessEqual(row[metric],before[key][metric]+1e-6,(key,metric))

 def test_24_rotated_source_bevels_are_actual_thin_source_planes(self):
  source=self.sources[0];tri=np.array(source['vertices'])[np.array(source['faces'])];valid=set(source['components'][0]['sourcePolygonIndices']);panels=[s for s in self.specs if s.get('surface_panel') and not s.get('neck_patch')]
  self.assertEqual(len(panels),73);seen=set()
  for s in panels:
   self.assertEqual((s['source_mesh'],s['source_component']),(0,0));self.assertEqual(s['uv_projection'],'solid_role')
   plane=s['source_plane'];normal=np.array(plane['normal']);origin=np.array(plane['origin']);support=np.array(plane['support_triangles']);self.assertTrue(set(plane['source_polygon_indices'])<=valid)
   _,axes,half=box(self.named[s['name']]);np.testing.assert_allclose(axes[:,2],normal,atol=1e-7);np.testing.assert_allclose(axes,plane['basis'],atol=1e-7)
   self.assertLessEqual(2*half[2],.02001);self.assertLessEqual(abs((support-origin)@normal).max(),.008001)
   ids=tuple(plane['source_polygon_indices'])
   if ids in seen:continue
   seen.add(ids);raw=tri[list(ids)];points=np.unique(support.reshape(-1,3),axis=0)
   # Independent exact point-to-source-triangle distance (not copied manifest).
   aa=raw[:,0];ab=raw[:,1]-aa;ac=raw[:,2]-aa;nn=np.cross(ab,ac);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-20)
   delta=points[:,None]-aa;normalDistance=(delta*nn).sum(2);projected=delta-normalDistance[:,:,None]*nn
   d00=(ab*ab).sum(1);d01=(ab*ac).sum(1);d11=(ac*ac).sum(1);d20=(projected*ab).sum(2);d21=(projected*ac).sum(2);den=d00*d11-d01*d01;den=np.where(abs(den)>1e-20,den,1e20)
   u=(d11*d20-d01*d21)/den;v=(d00*d21-d01*d20)/den;dist=np.where((u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7),abs(normalDistance),np.inf)
   for a,b in ((raw[:,0],raw[:,1]),(raw[:,1],raw[:,2]),(raw[:,2],raw[:,0])):
    ed=b-a;q=((points[:,None]-a)*ed).sum(2)/np.maximum((ed*ed).sum(1),1e-20);foot=a+np.clip(q,0,1)[:,:,None]*ed;dist=np.minimum(dist,np.linalg.norm(points[:,None]-foot,axis=2))
   self.assertLessEqual(float(dist.min(1).max()),1e-6)
  self.assertGreaterEqual(len(seen),50)

 def test_25_root_cause_return_wall_area_reduced_not_recolored(self):
  removed=set(self.design['surface_refinement']['removedR3Elements']);old=[e for e in self.design['previous_r3']['models']['body']['elements'] if e['name'] in removed]
  new=[self.named[s['name']] for s in self.specs if s.get('surface_panel') and not s.get('neck_patch')]
  def area(e,f):
   half=box(e)[2];axis=int(np.argmax(np.abs(NORMALS[f])));return float(np.prod(np.delete(2*half,axis)))
  oldarea=sum(area(e,f) for e in old for f in ('north','south') if f in e['faces'])
  newarea=sum(area(e,f) for e in new for f in ('west','east','up','down') if f in e['faces'])
  self.assertEqual(len(old),11);self.assertLess(newarea,oldarea*.3)
  oldtex=np.array(Image.open(io.BytesIO(base64.b64decode(self.design['previous_r3']['texture_base64']))))
  for r in self.manifest['atlasComponents']:
   x,y,w,h=r['pixels'];np.testing.assert_array_equal(self.atlas[y-2:y+h+2,x-2:x+w+2],oldtex[y-2:y+h+2,x-2:x+w+2])

 def test_26_coincident_owner_is_exact_same_part_not_blind_deletion(self):
  template=dict(source_mesh=0,source_component=0,source_bone='Pedestal',material='graphite',local_bounds=[[0,0,0],[1,1,1]],rotation={'origin':[0,0,0],'x':0,'y':0,'z':0})
  import copy
  a=copy.deepcopy(template);a['name']='a';b=copy.deepcopy(template);b['name']='b'
  h=self.gen.hidden_faces([a,b]);self.assertEqual(h['a'],[]);self.assertEqual(len(h['b']),5) # nonempty editable representation retained
  b['source_bone']='Magazine';self.assertEqual(self.gen.hidden_faces([a,b]),{'a':[],'b':[]})
  b['source_bone']='Pedestal';b['local_bounds']=[[.5,0,0],[1.5,1,1]]
  self.assertNotIn('north',self.gen.hidden_faces([a,b])['b']) # partial face cannot be discarded

 def test_27_Euler_gimbal_roundtrip_not_ItemTransform_XYZ(self):
  for angles in ([0,90,33],[0,-90,71],[18,90,-47],[21,-90,14],[19,89.999,65],[27,31,-46]):
   original={'from':[0,0,0],'to':[1,1,1],'rotation':dict(origin=[0,0,0],**dict(zip('xyz',angles)))}
   axes=box(original)[1];degrees=self.gen.euler_rzryrx(axes);copy=dict(original,rotation=dict(origin=[0,0,0],**dict(zip('xyz',degrees))))
   np.testing.assert_allclose(box(copy)[1],axes,atol=1e-7)

 def test_28_actual_R3_geometry_unchanged_except_named_bevel_and_contour_not_worse(self):
  removed=set(self.design['surface_refinement']['removedR3Elements']);old=sum([m['elements'] for m in self.design['previous_r3']['models'].values()],[])
  for e in old:
   if e['name'] in removed or e['name'] in set(self.design['neck_refinement']['removedR4Elements']):continue
   for k in ('from','to','rotation'):self.assertEqual(e[k],self.named[e['name']][k],(e['name'],k))
  old0=[e for e in old if '_s0_c000_' in e['name']];new0=[self.named[s['name']] for s in self.bycomp[0,0]];raw=self.spatial[0,0][3]
  points=np.unique(raw.reshape(-1,3),axis=0)
  def coverage(es):
   ds=[]
   for e in es:
    c,a,h=box(e);ds.append(np.linalg.norm(np.maximum(abs((points-c)@a)-h,0),axis=1))
   return float(np.min(ds,axis=0).max())
  self.assertLessEqual(coverage(new0),coverage(old0)+1e-6)
  def contour(es):
   samples=[]
   for e in es:
    v=corners(e);samples.extend(v);samples.extend((v[i]+v[j])/2 for i,j in ((0,1),(0,2),(0,4),(7,6),(7,5),(7,3)))
   p=np.array(samples)[:,[1,2]];tri=raw[:,:,[1,2]];aa=tri[:,0];bb=tri[:,1];cc=tri[:,2];ab=bb-aa;ac=cc-aa;den=ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0];maxdistance=0
   for start in range(0,len(p),24):
    q=p[start:start+24];d=q[:,None]-aa;safe=np.where(abs(den)>1e-12,den,1);u=(d[:,:,0]*ac[:,1]-d[:,:,1]*ac[:,0])/safe;v=(ab[:,0]*d[:,:,1]-ab[:,1]*d[:,:,0])/safe;inside=(abs(den)>1e-12)&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7);dist=np.full((len(q),len(tri)),np.inf)
    for a,b in ((aa,bb),(bb,cc),(cc,aa)):
     edge=b-a;t=((q[:,None]-a)*edge).sum(2)/np.maximum((edge*edge).sum(1),1e-24);closest=a+np.clip(t,0,1)[:,:,None]*edge;dist=np.minimum(dist,np.linalg.norm(q[:,None]-closest,axis=2))
    dist[inside]=0;maxdistance=max(maxdistance,float(dist.min(1).max()))
   return maxdistance
  self.assertLessEqual(contour(new0),contour(old0)+1e-6)


 def test_29_R4_component_fidelity_not_deteriorated_and_non_target_unchanged(self):
  before={(r['source_mesh'],r['source_component']):r for r in self.design['previous_r4']['spatialFidelity']}
  for row in self.manifest['spatialFidelity']:
   key=row['source_mesh'],row['source_component']
   for metric in ('extentDeviationMax','sourceCoverageMax','profileOverreachMax'):self.assertLessEqual(row[metric],before[key][metric]+1e-6,(key,metric))
  removed=set(self.design['neck_refinement']['removedR4Elements'])
  for e in sum([m['elements'] for m in self.design['previous_r4']['models'].values()],[]):
   if e['name'] in removed:continue
   for key in ('from','to','rotation'):self.assertEqual(e[key],self.named[e['name']][key])
  self.assertEqual(len(removed),44)

 def test_30_neck_all_original_polygons_preserved_not_QEM_or_hull_fill(self):
  for ci in (3,10):
   source=self.sources[0];expected=set(source['components'][ci]['sourcePolygonIndices']);actual=[]
   for s in self.bycomp[0,ci]:
    self.assertTrue(s['neck_patch']);plane=s['source_plane'];actual.extend(plane['source_polygon_indices']);original=np.array(source['vertices'])[np.array(source['faces'])[plane['source_polygon_indices']]]
    np.testing.assert_allclose(plane['support_triangles'],original,atol=1e-12)
    a=box(self.named[s['name']])[1];np.testing.assert_allclose(a,plane['basis'],atol=1e-7)
    normal=np.array(plane['normal']);np.testing.assert_allclose(a[:,2],normal,atol=1e-7)
    support=np.array(s['support_triangles']);self.assertEqual(original.shape,support.shape)
    delta=original-support;self.assertLessEqual(float(np.linalg.norm(delta,axis=2).max()),.0004)
    self.assertLessEqual(float(np.linalg.norm(np.cross(delta,normal),axis=2).max()),1e-7)
   self.assertEqual(set(actual),expected);self.assertEqual(len(actual),len(expected))

 def test_31_neck_true_circular_planes_reject_old_comb_and_keep_source_envelope(self):
  for ci in (3,10):
   ss=self.bycomp[0,ci];normals=np.array([box(self.named[s['name']])[1][:,2] for s in ss])
   self.assertGreater(len(np.unique(np.round(normals[:,:2],2),axis=0)),25)
   old=[e for e in self.design['previous_r4']['models']['body']['elements'] if f'_s0_c{ci:03}_' in e['name']]
   self.assertEqual(len({tuple(e['rotation'][a] for a in 'xyz') for e in old}),1)
   a,b,dist,raw=self.spatial[0,ci];self.assertLess(float(abs(a-b).max()),.0005);self.assertLess(float(dist.max()),.0005)
   for s in ss:
    support=np.array(s['support_triangles']);sample=np.r_[support.reshape(-1,3),support.mean(1)]
    self.assertLessEqual(float(triangle_distances(sample,raw).max()),.000401)

 def test_32_patch_masks_are_source_local_conservative_not_missing_or_noise(self):
  rows={r['name']:r for r in self.manifest['atlasPatches']};self.assertEqual(set(rows),{s['name'] for s in self.specs if s['kind']=='alpha_patch'})
  for name,row in rows.items():
   s=self.spec_by_name[name];lo,hi=np.array(s['local_bounds']);a=box(self.named[name])[1];x,y,w,h=row['pixels'];tile=self.atlas[y:y+h,x:x+w];support=np.array(s['support_triangles']);q=np.r_[support.reshape(-1,3),support.mean(1)]@a;u=(q[:,0]-lo[0])/(hi[0]-lo[0]);v=(hi[1]-q[:,1])/(hi[1]-lo[1]);ix=np.clip(np.floor(u*w).astype(int),0,w-1);iy=np.clip(np.floor(v*h).astype(int),0,h-1)
   self.assertTrue((tile[iy,ix,3]==255).all(),name)
   palette=np.array(self.design['palette'][s['material']]);self.assertTrue((tile[:,:,:3]==palette).all())
   ys,xs=np.where(tile[:,:,3]>0);step=max(1,len(xs)//12);ps=np.c_[lo[0]+(xs[::step]+.5)/w*(hi[0]-lo[0]),hi[1]-(ys[::step]+.5)/h*(hi[1]-lo[1]),np.full(len(xs[::step]),lo[2])]@a.T
   self.assertLessEqual(float(triangle_distances(ps,support).max()),row['maxTexelDiagonal']+.000001)
   uv=self.named[name]['faces']['south']['uv'];np.testing.assert_allclose(uv,np.array([x,y,x+w,y+h])/64)


 def test_33_actual_opaque_texel_envelope_not_just_ideal_support_retains_R4(self):
  before={(r['source_mesh'],r['source_component']):r for r in self.design['previous_r4']['spatialFidelity']};rows={r['name']:r for r in self.manifest['atlasPatches']};reported={r['source_component']:r for r in self.manifest['rasterFidelity']}
  for ci in (3,10):
   points=[]
   for spec in self.bycomp[0,ci]:
    e=self.named[spec['name']]
    if spec['kind']=='cuboid':points.extend(corners(e));continue
    row=rows[spec['name']];x,y,w,h=row['pixels'];ys,xs=np.where(self.atlas[y:y+h,x:x+w,3]>0);lo,hi=np.array(spec['local_bounds']);axes=box(e)[1]
    for u,v in ((0,0),(1,0),(0,1),(1,1)):
     p=np.c_[lo[0]+(xs+u)/w*(hi[0]-lo[0]),hi[1]-(ys+v)/h*(hi[1]-lo[1]),np.full(len(xs),lo[2])]@axes.T;points.extend(p)
   points=np.array(points);bbox=np.array([points.min(0),points.max(0)]);source=self.spatial[0,ci][0];deviation=float(abs(bbox-source).max())
   self.assertLessEqual(deviation,before[0,ci]['extentDeviationMax']+1e-6)
   self.assertLessEqual(deviation,.1);np.testing.assert_allclose(bbox,reported[ci]['occupiedTexelBounds'],atol=1e-7)
   self.assertAlmostEqual(deviation,reported[ci]['extentDeviationMax'],places=6)

if __name__=='__main__':unittest.main(verbosity=2)
