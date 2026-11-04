#!/usr/bin/env python3
"""Portable W138 Apostate CPU checks; no native/DCC/game acceptance implied."""
import base64
import hashlib
import io
import json
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_apostate.py'))
ART=ROOT/G['ART']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def occupied(p,e):
    r=e.get('rotation',{});o=np.array(r.get('origin',[8,8,8]))
    q=(np.array(p)-o)@G['rotation'](r)+o
    return bool(np.all(q>np.array(e['from'])+1e-6) and np.all(q<np.array(e['to'])-1e-6))
def ray_hits(a,b,e):
    r=e.get('rotation',{});o=np.array(r.get('origin',[8,8,8]));R=G['rotation'](r)
    a=(np.array(a)-o)@R+o;b=(np.array(b)-o)@R+o;v=b-a;t0=0.;t1=1.
    for k in range(3):
        lo,hi=e['from'][k],e['to'][k]
        if abs(v[k])<1e-10:
            if a[k]<=lo+1e-7 or a[k]>=hi-1e-7:return False
        else:
            ts=sorted(((lo-a[k])/v[k],(hi-a[k])/v[k]));t0=max(t0,ts[0]);t1=min(t1,ts[1])
            if t1-t0<1e-7:return False
    return True

def intersects(a,b):
    ar=G['rotation'](a.get('rotation',{}));br=G['rotation'](b.get('rotation',{}))
    av,bv=G['vertices'](a),G['vertices'](b)
    for axis in [*ar.T,*br.T,*[np.cross(u,v) for u in ar.T for v in br.T]]:
        length=np.linalg.norm(axis)
        if length<1e-9:continue
        aa=av@(axis/length);bb=bv@(axis/length)
        if aa.max()+.003<bb.min() or bb.max()+.003<aa.min():return False
    return True

class ApostateArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads((ART/'design.json').read_bytes());cls.m=json.loads((ART/'manifest.json').read_bytes())
        cls.model=json.loads((ROOT/G['MODEL']).read_bytes());cls.es=cls.model['elements']
        cls.lookup={e['name']:e for e in cls.es};cls.bb=json.loads((ART/'inspection.bbmodel').read_bytes())
        cls.atlas=np.array(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))

    def test_01_full_only_emitted_budget_and_semantic_volumes(self):
        self.assertEqual(self.m['counts'],{'full':len(self.es)})
        self.assertEqual(self.m['assembled_elements'],len(self.es));self.assertLessEqual(len(self.es),1000)
        self.assertTrue(self.m['full_only']);self.assertEqual(self.m['emitted_faces'],len(self.es)*6)
        self.assertEqual(self.m['triangle_adapter_elements'],0);self.assertEqual(self.m['alpha_elements'],0)
        self.assertEqual(len(self.lookup),len(self.es));self.assertFalse(self.d['source_component_tessellation'])
        self.assertFalse(self.d['source_voxel_conversion'])
        for name in ('foreend/filled-core','receiver/core','optic/housing'):
            size=np.array(self.lookup[name]['to'])-self.lookup[name]['from']
            self.assertGreaterEqual(size.min(),.95,name)
        for suffix in ('_body','_magazine','_cover'):
            self.assertFalse((ROOT/G['MODEL'].replace('.json',suffix+'.json')).exists())

    def test_02_native_elements_are_finite_filled_six_face_cuboids(self):
        for e in self.es:
            self.assertLessEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.isfinite(G['vertices'](e)).all());self.assertEqual(set(e['faces']),set(G['FACES']))
            if 'rotation' in e:
                self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
                R=G['rotation'](e['rotation']);np.testing.assert_allclose(R.T@R,np.eye(3),atol=1e-10)

    def test_03_original_frame_display_grip_and_envelope(self):
        old=json.loads((ROOT/G['BASE']).read_bytes());meta=json.loads((ROOT/G['BB']).read_bytes())['destiny_w30']
        self.assertEqual(self.model['display'],old['display']);self.assertEqual(self.d['frame']['anchor'],meta['anchor'])
        self.assertEqual(self.d['frame']['scale'],meta['scale']);self.assertEqual(self.d['frame']['muzzle'],'-Z')
        self.assertFalse(self.d['frame']['recentered'])
        self.assertEqual(self.d['frame']['source_axis'],{'length':1,'thin':0,'muzzle_sign':-1})
        self.assertTrue(occupied([8,8.2,8.1],self.lookup['grip/core']))
        ps=np.concatenate([G['vertices'](e) for e in self.es]);bounds=np.array([ps.min(0),ps.max(0)])
        self.assertTrue(np.all(abs(bounds-np.array(meta['model_bounds']))<.36),(bounds,meta['model_bounds']))
        self.assertAlmostEqual(bounds[0,2],meta['model_bounds'][0][2],places=5)
        self.assertAlmostEqual(bounds[1,2],meta['model_bounds'][1][2],places=5)
        np.testing.assert_allclose(bounds,self.m['actual_bounds'],atol=1e-7)

    def test_04_real_through_openings_and_positive_solid_probes(self):
        for name,p in self.d['required_air_probes'].items():
            self.assertFalse(any(occupied(p,e) for e in self.es),name)
        for name in ('trigger','thumbhole'):
            _,y,z=self.d['required_air_probes'][name]
            self.assertFalse(any(ray_hits([6,y,z],[10,y,z],e) for e in self.es),name)
        for name,p in self.d['required_solid_probes'].items():
            self.assertTrue(any(occupied(p,e) for e in self.es),name)
        for y in (9.6,9.92,10.2):
            for z in (-5,-3,0,2):
                self.assertTrue(any(occupied([8,y,z],e) for e in self.es),(y,z))

    def test_05_deep_muzzle_and_recessed_green_lens(self):
        self.assertFalse(any(ray_hits([8,9.96,-15.45],[8,9.96,-10.5],e) for e in self.es))
        hits=[e['name'] for e in self.es if ray_hits([8,9.96,-10.5],[8,9.96,-10.42],e)]
        self.assertEqual(hits,['muzzle/bore-stop'])
        # Lens must be the first opaque face on the central objective ray.
        hits=[e['name'] for e in self.es if ray_hits([8,11.56,1.2],[8,11.56,1.97],e)]
        self.assertEqual(hits,['optic/green-lens'])
        self.assertGreater(self.lookup['optic/green-lens']['from'][2],1.36+.3)

    def test_06_connected_assembly_no_floating_braces_thorns_or_grip(self):
        reached={0};pending=set(range(1,len(self.es)))
        points=[G['vertices'](e) for e in self.es]
        low=np.array([p.min(0) for p in points]);high=np.array([p.max(0) for p in points])
        adjacency=[set() for _ in self.es]
        for i,a in enumerate(self.es):
            for j in range(i):
                if np.any(high[i]+.003<low[j]) or np.any(high[j]+.003<low[i]):continue
                if intersects(a,self.es[j]):adjacency[i].add(j);adjacency[j].add(i)
        frontier=[0]
        while frontier:
            i=frontier.pop()
            for j in adjacency[i]-reached:reached.add(j);frontier.append(j)
        pending-=reached
        self.assertFalse(pending,'Detached: '+', '.join(self.es[i]['name'] for i in sorted(pending)))

    def test_07_opaque_unique_aspect_correct_face_uv_and_gutters(self):
        self.assertEqual(self.atlas.shape,(1024,1024,4));self.assertTrue((self.atlas[:,:,3]==255).all())
        coverage=np.zeros((1024,1024),bool);islands=self.d['atlas']['islands'];self.assertEqual(len(islands),len(self.es)*6)
        seen=set()
        for island in islands:
            x,y,xx,yy=island['pixels'];self.assertTrue(2<=x<xx<=1022 and 2<=y<yy<=1022)
            self.assertFalse(coverage[y-2:yy+2,x-2:xx+2].any());coverage[y-2:yy+2,x-2:xx+2]=True
            key=(island['element'],island['face']);self.assertNotIn(key,seen);seen.add(key)
            e=self.lookup[key[0]];f=e['faces'][key[1]];self.assertEqual(f['texture'],'#0')
            self.assertEqual(f['uv'],[q/64 for q in (x,y,xx,yy)])
            p=G['vertices'](e)[list(G['FACES'][key[1]])];w=np.linalg.norm(p[1]-p[0]);h=np.linalg.norm(p[3]-p[0])
            self.assertEqual(xx-x,max(5,int(np.ceil(w*26))))
            self.assertEqual(yy-y,max(5,int(np.ceil(h*26))))
            np.testing.assert_array_equal(self.atlas[y:yy,x-1],self.atlas[y:yy,x])
            np.testing.assert_array_equal(self.atlas[y-1,x:xx],self.atlas[y,x:xx])
        self.assertGreater(self.d['atlas']['used_texels'],200000)

    def test_08_authored_materials_and_continuous_identity_faces(self):
        a=self.atlas[:,:,:3].astype(int)
        for name,mask in [('red',(a[:,:,0]>a[:,:,1]*1.8)&(a[:,:,0]>60)),
                          ('green',(a[:,:,1]>a[:,:,0]*1.7)&(a[:,:,1]>65)),
                          ('ivory',(a[:,:,0]>140)&(a[:,:,1]>130)&(a[:,:,2]>110)),
                          ('silver',(a[:,:,2]>120)&(a[:,:,1]>110)&(a[:,:,0]>90))]:
            self.assertGreater(np.count_nonzero(mask),50,name)
        for face in ('west','east'):
            uv=self.lookup['foreend/filled-core']['faces'][face]['uv']
            x,y,xx,yy=[round(q*64) for q in uv]
            self.assertGreater(max(xx-x,yy-y),250)
            self.assertGreater(len(np.unique(self.atlas[y:yy,x:xx,:3].reshape(-1,3),axis=0)),20)
        self.assertNotEqual(self.lookup['foreend/filled-core']['faces']['west']['uv'],self.lookup['foreend/filled-core']['faces']['east']['uv'])

    def test_09_inspection_exact_geometry_uv_group_and_embedded_texture(self):
        self.assertEqual(self.bb['display'],self.model['display']);self.assertEqual(len(self.bb['elements']),len(self.es))
        bb={b['name']:b for b in self.bb['elements']}
        for e in self.es:
            b=bb[e['name']];r=e.get('rotation',{})
            self.assertEqual(b['type'],'cube');self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
            self.assertEqual(b['origin'],r.get('origin',[8,8,8]));self.assertEqual(b['rotation'],[r.get(a,0) for a in 'xyz'])
            for f in G['FACES']:
                self.assertEqual(b['faces'][f]['texture'],0);self.assertEqual(b['faces'][f]['uv'],[q*64 for q in e['faces'][f]['uv']])
        self.assertEqual({g['name'] for g in self.bb['outliner']},set(self.d['groups']))
        self.assertEqual({b['uuid'] for b in bb.values()},{u for group in self.bb['outliner'] for u in group['children']})
        self.assertEqual(base64.b64decode(self.bb['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
        self.assertFalse(self.bb['destiny_w138']['nativeAccepted'])

    def test_10_frozen_baseline_inputs_and_portable_integration(self):
        prov=self.d['baseline_provenance'];self.assertEqual(prov,self.m['baseline_provenance'])
        self.assertEqual(prov['name'],'w138-apostate');self.assertEqual(len(prov['baseline_sha256']),64)
        self.assertTrue(prov['owned_paths_initially_absent'])
        for p,h in self.d['input_sha256'].items():self.assertEqual(sha(ROOT/p),h,p)
        for p,h in self.d['raw_input_sha256'].items():self.assertEqual(sha(Path(p)),h,p)
        # A checkout integrated into main has a different .git layout and no
        # worker state. Verify the worker state only when present for THIS batch.
        git=ROOT/'.git'
        if git.is_file():
            gd=Path(git.read_text().strip().split(': ',1)[1]);statepath=gd/'worktree-batch.json'
            if statepath.is_file():
                state=json.loads(statepath.read_bytes())
                if state.get('name')=='w138-apostate':
                    self.assertEqual(state['baseline_sha256'],prov['baseline_sha256'])
                    for p,h in self.d['input_sha256'].items():self.assertEqual(state['baseline'][p]['sha256'],h)
        for p,h in self.m['output_sha256'].items():self.assertEqual(sha(ROOT/p),h,p)
        self.assertEqual(sha(ROOT/'scripts/generate_surface_w123_apostate.py'),self.m['generator_sha256'])

    def test_11_exact_owned_set_budget_and_no_native_claims(self):
        batch=json.loads((ROOT/G['BATCH']).read_bytes())
        owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w138-apostate'))
        expected=set(self.m['output_sha256'])|{G['ART']+'manifest.json','scripts/generate_surface_w123_apostate.py',
            'scripts/qa/test_surface_w123_apostate.py','docs/qa/2026-10-26/w138/apostate-worker.md'}
        self.assertEqual(expected,owned);self.assertEqual(len(owned),10)
        self.assertLess(sum((ROOT/p).stat().st_size for p in owned if (ROOT/p).exists()),25*1024*1024)
        self.assertFalse(self.m['native_accepted']);self.assertEqual(self.m['validation']['native'],'pending master')

    def test_12_actual_source_fbx_basis_and_no_mesh_island_conversion(self):
        meshes,meta=G['source_meshes']();self.assertEqual(sum(len(m['faces']) for m in meshes),37378)
        self.assertEqual({m['name'] for m in meshes},set(meta['source_objects']))
        ps=np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([ps.min(0),ps.max(0)],meta['model_bounds'],atol=1e-5)
        # The material-less locator must not break CPU reference QA.
        locator=next(m for m in meshes if m['name']=='Apostate.03.004')
        self.assertEqual(locator['material'],'Glow');self.assertEqual(locator['uv'].shape,(2,3,2));self.assertTrue(np.isfinite(locator['uv']).all())

    def test_13_comparison_contains_side_and_oblique_rendered_models(self):
        im=Image.open(ART/'comparison.png');self.assertEqual(im.size,(2640,1770))
        for row in range(3):
            for col in range(3):
                a=np.array(im.crop((col*880+25,435+row*310+42,(col+1)*880-25,435+(row+1)*310-20))).astype(int)
                self.assertGreater(np.count_nonzero(np.max(abs(a-[32,39,48]),axis=2)>12),1800,(row,col))

    def test_14_regenerated_model_atlas_and_inspection(self):
        # Fast data regeneration; full comparison is checked by --verify next.
        outputs=G['generate'](include_comparison=False)
        for p,data in outputs.items():
            if p.endswith('manifest.json'):continue
            self.assertEqual((ROOT/p).read_bytes(),data,p)

if __name__=='__main__':unittest.main(verbosity=2)
