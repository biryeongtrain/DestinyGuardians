#!/usr/bin/env python3
"""W141 Temptation's Hook offline geometry/paint/provenance regression.
No DCC, game, server, builds, or shared writes. Run with python -B.
"""
import base64
import io
import json
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_temptation_s_hook.py'))
CANONICAL_SHA='f5c48f76395c7b969fbb6867d75fd3b0bf038e1f1d6a73992d91e94a01b92277'
ITEM_SHA='05268a824156333a6fcb122cb5d6ef60283c36635b5688ac5b705ecb14e8ec69'


def read(p):return json.loads((ROOT/p).read_bytes())


def inside(p,e):
    p=np.array(p,float);r=e.get('rotation')
    if r:
        o=np.array(r['origin']);p=(p-o)@G['H']['rotation']({r['axis']:r['angle']})+o
    return bool(np.all(p>=np.array(e['from'])-1e-8) and np.all(p<=np.array(e['to'])+1e-8))


def obb(e):
    r=e.get('rotation');R=G['H']['rotation']({r['axis']:r['angle']}) if r else np.eye(3)
    return G['vertices'](e).mean(0),R,(np.array(e['to'])-e['from'])/2


def touches(a,b):
    """15 separating axes: catches floating slabs hidden by a side projection."""
    ca,aa,ha=a;cb,ab,hb=b
    for axis in [*aa.T,*ab.T]+[np.cross(u,v) for u in aa.T for v in ab.T]:
        if np.linalg.norm(axis)<1e-8:continue
        if abs((cb-ca)@axis)>sum(ha*abs(aa.T@axis))+sum(hb*abs(ab.T@axis))+1e-6:return False
    return True


class TemptationsHookArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=read(G['MODEL']);cls.d=read(G['ART']+'design.json');cls.man=read(G['ART']+'manifest.json')
        cls.bb=read(G['ART']+'inspection.bbmodel');cls.es={e['name']:e for e in cls.m['elements']}
        cls.atlas=Image.open(ROOT/G['TEXTURE']).convert('RGBA');cls.px=np.asarray(cls.atlas)
        cls.meshes,cls.meta=G['source_meshes']()

    def test_emitted_budget_and_supported_cuboid_schema(self):
        n=len(self.m['elements'])
        self.assertGreater(n,0);self.assertEqual(n,len(self.es));self.assertLessEqual(n,1000)
        self.assertEqual(n,self.man['assembled_elements']);self.assertEqual(n,sum(self.man['groups'].values()))
        self.assertEqual(n*6,self.man['emitted_faces']);self.assertEqual(0,self.man['triangle_adapter_elements'])
        for e in self.es.values():
            self.assertTrue(set(e)<={'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.isfinite(G['vertices'](e)).all())
            self.assertEqual(set(G['FACES']),set(e['faces']))
            self.assertFalse(e['name'].startswith(('source_volume','voxel')))
            if 'rotation' in e:
                self.assertEqual({'axis','angle','origin'},set(e['rotation']));self.assertIn(e['rotation']['axis'],'xyz')

    def test_canonical_display_scale_grip_and_bounds(self):
        self.assertEqual(CANONICAL_SHA,G['sha']((ROOT/G['BASE']).read_bytes()))
        self.assertEqual(read(G['BASE'])['display'],self.m['display'])
        self.assertEqual([8,4.738785774747939,8],self.man['source_anchor'])
        self.assertEqual(21.078860348466854,self.man['source_scale'])
        self.assertTrue(inside(self.man['source_anchor'],self.es['grip_core']))
        self.assertAlmostEqual(7.715,(self.es['grip_core']['from'][2]+self.es['grip_core']['to'][2])/2)
        np.testing.assert_allclose(self.man['actual_bounds'],self.meta['model_bounds'],atol=.06,rtol=0)
        self.assertEqual('+Y',self.d['coordinate_policy']['length'])
        self.assertGreater(self.es['hook_terminal']['to'][1],31)

    def test_real_blend_source_and_default_photo_provenance(self):
        self.assertEqual(6,len(self.meshes));self.assertEqual(4278,sum(len(m['faces']) for m in self.meshes))
        self.assertEqual(sorted(self.meta['source_objects']),sorted(m['name'] for m in self.meshes))
        pts=np.concatenate([m['vertices'] for m in self.meshes])
        np.testing.assert_allclose([pts.min(0),pts.max(0)],self.meta['model_bounds'],atol=1e-7,rtol=0)
        self.assertEqual('b471a3a024428117d59b192f84d3438e62ca63bf48d2ebeb774e90ac33da79f7',self.meta['source_files']["Temptation's Hook.blend"])
        for p,digest in self.d['input_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        for p,digest in self.d['raw_input_sha256'].items():self.assertEqual(digest,G['sha'](Path(p).read_bytes()),p)
        ref=next(r for r in read(G['REFS']) if r['id']==G['ID'])
        self.assertEqual(ref['sha256'],G['sha'](G['PHOTO'].read_bytes()))
        catalogue=read('src/main/resources/destiny/weapons/w30.json')
        row=next(w for w in catalogue if w['id']==G['ID']);self.assertEqual('sword',row['family']);self.assertEqual('caster',row['frame'])

    def test_whole_assembly_has_no_detached_geometry(self):
        es=list(self.es.values());obs=[obb(e) for e in es];graph={i:set() for i in range(len(es))}
        for i in range(len(es)):
            for j in range(i):
                if touches(obs[i],obs[j]):graph[i].add(j);graph[j].add(i)
        seen=set();todo={0}
        while todo:
            i=todo.pop();seen.add(i);todo|=graph[i]-seen
        self.assertEqual(set(range(len(es))),seen,[es[i]['name'] for i in graph.keys()-seen])

    def test_filled_blade_and_changing_cross_section(self):
        webs=[e for n,e in self.es.items() if n.startswith('blade_web_')]
        energy=[e for n,e in self.es.items() if n.startswith('arc_cutting_edge_')]
        for e in webs:
            center=G['vertices'](e).mean(0)
            for dx in (-.14,0,.14):self.assertTrue(inside(center+[dx,0,0],e),e['name'])
            self.assertGreater(e['to'][1]-e['from'][1],.5)
        for e in energy:
            center=G['vertices'](e).mean(0)
            self.assertTrue(inside(center,e));self.assertFalse(inside(center+[.12,0,0],e))
        # Grip-to-heel diagonal must contain actual interior, not two side skins.
        for p in ([8,11.8,7.7],[8,12.5,8.3],[8,13.5,9],[8,4.739,7.715]):
            self.assertTrue(any(inside(p,e) for e in self.es.values()),p)

    def test_physical_fin_gaps_and_raised_inset(self):
        occupancy=[any(inside([8,y,6.34],e) for e in self.es.values()) for y in np.arange(7.8,11,.01)]
        self.assertTrue(any(occupancy));self.assertFalse(all(occupancy))
        self.assertGreater(sum(a!=b for a,b in zip(occupancy,occupancy[1:])),4)
        # Pale inset sits beyond the hilt side plane, giving actual oblique relief.
        self.assertTrue(inside([8.39,8.7,7.7],self.es['pale_inset_1']))
        self.assertFalse(any(inside([8.39,8.7,8.4],e) for e in self.es.values()))

    def test_fully_opaque_face_atlas_and_gutter_integrity(self):
        self.assertEqual((1024,1024,4),self.px.shape);self.assertTrue((self.px[:,:,3]==255).all())
        cover=np.zeros((1024,1024),bool);seen=set()
        for r in self.d['atlas']['islands']:
            x,y,X,Y=r['pixels'];key=(r['element'],r['face']);self.assertNotIn(key,seen);seen.add(key)
            self.assertGreaterEqual(min(x,y),2);self.assertLessEqual(max(X,Y),1022)
            self.assertGreater(X,x);self.assertGreater(Y,y)
            self.assertFalse(cover[y-2:Y+2,x-2:X+2].any());cover[y-2:Y+2,x-2:X+2]=True
            f=self.es[r['element']]['faces'][r['face']]
            self.assertEqual('#0',f['texture']);np.testing.assert_allclose(f['uv'],np.array([x,y,X,Y])/64)
            self.assertNotIn('cullface',f)
            np.testing.assert_array_equal(self.px[y-2:Y+2,x-2:X+2],np.pad(self.px[y:Y,x:X],((2,2),(2,2),(0,0)),mode='edge'))
        self.assertEqual(len(self.es)*6,len(seen));self.assertEqual(0,self.man['alpha_body_elements'])

    def test_authored_material_contrast_and_face_resolution(self):
        islands={(r['element'],r['face']):r['pixels'] for r in self.d['atlas']['islands']}
        def samples(name,face='east'):
            x,y,X,Y=islands[(name,face)];return self.px[y:Y,x:X,:3]
        hilt=samples('hilt_root');grip=samples('grip_core');edge=samples('arc_cutting_edge_0')
        # Default bronze and teal remain distinct; no grayscale rip reused as dye.
        self.assertTrue(((hilt[:,:,1]>hilt[:,:,0]*1.25)&(hilt[:,:,2]>hilt[:,:,0]*1.25)).any())
        self.assertTrue(((hilt[:,:,0]>hilt[:,:,2]*1.3)&(hilt[:,:,1]>70)).any())
        self.assertGreater(np.mean(edge),np.mean(grip)*3)
        self.assertTrue((edge[:,:,2]>edge[:,:,0]).all())
        self.assertGreater(max(samples('spine_rivet_rail').shape[:2]),160)
        self.assertGreater(max(samples('grip_core').shape[:2]),120)

    def test_inspection_matches_model_geometry_and_face_uv(self):
        self.assertEqual({*self.es},{e['name'] for e in self.bb['elements']})
        self.assertEqual(len(self.es),sum(len(g['children']) for g in self.bb['outliner']))
        self.assertEqual((ROOT/G['TEXTURE']).read_bytes(),base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]))
        self.assertEqual(self.m['display'],self.bb['display'])
        self.assertEqual(self.meta['anchor'],self.bb['destiny_w141']['sourceAnchor'])
        for b in self.bb['elements']:
            e=self.es[b['name']]
            self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            r=e.get('rotation');self.assertEqual([r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],b['rotation'])
            for face,f in b['faces'].items():
                self.assertEqual(0,f['texture']);np.testing.assert_allclose(f['uv'],np.array(e['faces'][face]['uv'])*64)

    def test_side_and_oblique_silhouette_remain_recognizable(self):
        # Shape-only evidence, not a default appearance or native quality score.
        source=G['source_triangles'](self.meshes);new=G['model_triangles'](self.m,self.atlas)
        pts=np.concatenate([m['vertices'] for m in self.meshes])
        for cam in ([1,0,0],[.67,.12,.73]):
            frame=G['H']['frame'](pts,cam,500,1000)
            _,a=G['H']['render'](source,cam,frame,(500,1000),raw=True)
            _,b=G['H']['render'](new,cam,frame,(500,1000))
            self.assertGreater((a&b).sum()/(a|b).sum(),.82,cam)
            self.assertGreater((a&b).sum()/a.sum(),.90,cam)

    def test_shared_item_variants_stay_valid_and_full_only(self):
        self.assertEqual(ITEM_SHA,G['sha']((ROOT/G['ITEM']).read_bytes()))
        refs=[]
        def walk(v):
            if isinstance(v,dict):
                if v.get('type')=='minecraft:model':refs.append(v['model'])
                for w in v.values():walk(w)
            elif isinstance(v,list):
                for w in v:walk(w)
        walk(read(G['ITEM']))
        self.assertEqual(6,len(refs))
        for ref in refs:
            self.assertTrue((ROOT/G['ASSET']/'models'/(ref.split(':',1)[1]+'.json')).is_file())
        self.assertTrue(self.man['full_only']);self.assertFalse(self.man['native_accepted'])
        self.assertFalse((ROOT/G['MODEL'].replace('.json','_body.json')).exists())
        self.assertFalse((ROOT/G['MODEL'].replace('.json','_magazine.json')).exists())
        for ref in self.m['textures'].values():
            self.assertTrue((ROOT/G['ASSET']/'textures'/(ref.split(':',1)[1]+'.png')).is_file())

    def test_manifest_artifacts_hashes_and_owned_scope(self):
        scope=next(f['owned_paths'] for f in read(G['BATCH'])['features'] if f['name']=='w141-'+G['ID'])
        self.assertEqual(10,len(scope));self.assertTrue(all((ROOT/p).is_file() for p in scope))
        self.assertLess(sum((ROOT/p).stat().st_size for p in scope),25*1024*1024)
        for p,digest in self.man['output_sha256'].items():
            self.assertIn(p,scope);self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()))
        self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/G['SCRIPT']).read_bytes()))
        with Image.open(ROOT/G['ART']/'comparison.png') as im:self.assertEqual((1800,2500),im.size)

    def test_deterministic_all_generated_bytes_including_comparison(self):
        outputs=G['generate']()
        self.assertEqual(7,len(outputs))
        for p,data in outputs.items():self.assertEqual((ROOT/p).read_bytes(),data,p)

if __name__=='__main__':unittest.main(verbosity=2)
