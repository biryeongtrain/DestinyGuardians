#!/usr/bin/env python3
"""Targeted offline W136 art tests; native acceptance remains with master."""
import base64
import io
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
g=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_retrofit_escapade.py'))


def contains(e,p):
    p=np.asarray(p,float);r=e.get('rotation')
    if r:
        o=np.array(r['origin']);p=(p-o)@g['rotation'](r)+o
    return bool(np.all(p>=np.array(e['from'])-1e-6) and np.all(p<=np.array(e['to'])+1e-6))


def intersects(a,b):
    ar=g['rotation'](a.get('rotation',{}));br=g['rotation'](b.get('rotation',{}))
    av=g['vertices'](a);bv=g['vertices'](b)
    for axis in [*ar.T,*br.T,*[np.cross(u,v) for u in ar.T for v in br.T]]:
        length=np.linalg.norm(axis)
        if length<1e-10:continue
        axis=axis/length;aa=av@axis;bb=bv@axis
        if aa.max()+.003<bb.min() or bb.max()+.003<aa.min():return False
    return True


class RetrofitEscapadeArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs=g['generate']()
        cls.d=json.loads(cls.outputs[g['ART']+'design.json'])
        cls.m=json.loads(cls.outputs[g['ART']+'manifest.json'])
        cls.model=json.loads(cls.outputs[g['MODEL']]);cls.es=cls.model['elements']
        cls.atlas=np.asarray(Image.open(io.BytesIO(cls.outputs[g['TEXTURE']])))

    def test_01_exact_scope_and_deterministic_artifacts(self):
        feature=next(f for f in json.loads((ROOT/g['BATCH']).read_bytes())['features'] if f['name']=='w136-retrofit_escapade')
        self.assertEqual(set(feature['owned_paths']),g['OWNED']);self.assertEqual(len(g['OWNED']),10)
        expected={g['ART']+n for n in ('design.json','manifest.json','review.md','inspection.bbmodel','comparison.png')}|{g['MODEL'],g['TEXTURE']}
        self.assertEqual(set(self.outputs),expected)
        for rel,data in self.outputs.items():
            with self.subTest(path=rel):self.assertEqual((ROOT/rel).read_bytes(),data)
        self.assertLess(sum(map(len,self.outputs.values())),25*1024*1024)

    def test_02_budget_schema_and_opaque_filled_solids(self):
        self.assertLessEqual(len(self.es),1000)
        self.assertEqual(self.m['assembled_elements'],len(self.es))
        self.assertEqual(self.m['counts']['combined'],len(self.es))
        self.assertEqual(self.m['triangle_adapter_elements'],0)
        self.assertEqual(self.m['alpha_body_elements'],0)
        self.assertEqual(self.m['emitted_faces'],len(self.es)*6)
        self.assertEqual(len({e['name'] for e in self.es}),len(self.es))
        for e in self.es:
            self.assertLessEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.isfinite(g['vertices'](e)).all())
            self.assertEqual(set(e['faces']),set(g['FACES']))
            if 'rotation' in e:self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
        for name in ('receiver_core','forebody_upper','receiver_wrap','foregrip_body','pistol_grip','drum_solid_core'):
            e=next(e for e in self.es if e['name']==name)
            self.assertGreater(min(np.array(e['to'])-e['from']),.60)
            center=(np.array(e['from'])+e['to'])/2
            self.assertTrue(contains(e,center))
        # Probe entire interior sections: cannot pass with two side shells.
        for y in np.linspace(10.4,11.8,4):
            for x in np.linspace(7.25,8.75,5):
                self.assertTrue(any(contains(e,[x,y,1.0]) for e in self.es))
        for x in (4.9,5.7,6.5,7.7,8.1):
            self.assertTrue(any(contains(e,[x,8.47,3.92]) for e in self.es))

    def test_03_catalogue_source_correctness_and_basis(self):
        cat=next(x for x in json.loads((ROOT/g['CATALOG']).read_bytes()) if x['id']=='retrofit_escapade')
        self.assertEqual(cat['family'],'machine_gun');self.assertEqual(cat['frame'],'rapid_fire')
        meshes,meta=g['source_meshes']()
        self.assertEqual(meta['scale'],22.39711503632459);self.assertEqual(meta['anchor'],[8.,8.,8.])
        self.assertEqual(meta['source_axis'],{'length':0,'thin':1,'muzzle_sign':1})
        self.assertEqual(sum(len(m['faces']) for m in meshes),26031)
        self.assertEqual(self.m['fbx_missing_triangles'],116)
        self.assertEqual(meta['source_triangles'],26147)
        self.assertEqual(len(meshes),9)
        self.assertEqual(set(meta['source_objects'])-{m['name'] for m in meshes},{'79D7FB80_Group7_Index34_17__lod_category_01'})
        ps=np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([ps.min(0),ps.max(0)],meta['model_bounds'],atol=2e-6)
        self.assertEqual(self.d['coordinate_policy']['mapping'],'[8-raw.Y*s,8+raw.Z*s,8-raw.X*s]')

    def test_04_display_length_and_hand_frame(self):
        old=json.loads((ROOT/g['BASE']).read_bytes())
        self.assertEqual(self.model['display'],old['display'])
        self.assertEqual(self.m['source_anchor'],[8.,8.,8.])
        self.assertEqual(self.m['source_scale'],22.39711503632459)
        ps=np.concatenate([g['vertices'](e) for e in self.es])
        self.assertAlmostEqual(ps[:,2].min(),-12.526633583091776)
        self.assertAlmostEqual(ps[:,2].max(),14.473366416908222)
        for p in ([8,8,8.75],[8,8.6,8.49]):self.assertTrue(any(contains(e,p) for e in self.es),p)
        self.assertTrue(self.m['full_only']);self.assertTrue(self.m['generic_reload_ADS_unchanged'])
        self.assertEqual(self.m['candidate'],'FULL ONLY')

    def test_05_physical_openings(self):
        holes=[('fork',[x,12.0,-10]) for x in (7.6,8,8.4)]
        holes += [('sleeve slot',[x,11.6,-6]) for x in (7.4,8,8.6)]
        holes += [('bore',[8,10.74,z]) for z in (-12.20,-11.0,-7.0)]
        holes += [('stock',[x,11.35,11.6]) for x in (7.6,8,8.4)]
        holes += [('guard',[x,8.35,7.65]) for x in (7.8,8,8.2)]
        holes += [('top loop',[8,14.37,5.66])]
        holes += [('receiver slot',[x,12.1,3.5]) for x in (7.2,8,8.8)]
        for tag,p in holes:self.assertFalse(any(contains(e,p) for e in self.es),(tag,p))
        for p in ([8,13.1,-10],[8,10.25,-10],[8,12.5,-6],[8,11.20,-6],[8,12.5,0]):
            self.assertTrue(any(contains(e,p) for e in self.es),p)

    def test_06_face_uv_continuity_opacity_and_gutters(self):
        self.assertEqual(self.atlas.shape,(1024,1024,4))
        self.assertTrue(np.all(self.atlas[:,:,3]==255))
        occupied=np.zeros((1024,1024),bool);rects=[]
        for e in self.es:
            for f in e['faces'].values():
                self.assertEqual(f['texture'],'#0')
                x0,y0,x1,y1=[int(round(q*1024/16)) for q in f['uv']]
                self.assertTrue(2<=x0<x1<=1022 and 2<=y0<y1<=1022)
                self.assertFalse(occupied[y0-2:y1+2,x0-2:x1+2].any())
                occupied[y0-2:y1+2,x0-2:x1+2]=True
                tile=self.atlas[y0:y1,x0:x1]
                for d in (1,2):
                    np.testing.assert_array_equal(self.atlas[y0-d,x0:x1],tile[0])
                    np.testing.assert_array_equal(self.atlas[y1+d-1,x0:x1],tile[-1])
                    np.testing.assert_array_equal(self.atlas[y0:y1,x0-d],tile[:,0])
                    np.testing.assert_array_equal(self.atlas[y0:y1,x1+d-1],tile[:,-1])
                rects.append((x0,y0,x1,y1))
        self.assertEqual(len(set(rects)),6*len(self.es))
        self.assertGreater(self.d['palette']['teal'][1],self.d['palette']['teal'][0])
        self.assertGreater(self.d['palette']['copper'][0],2*self.d['palette']['copper'][2])
        self.assertEqual(len(self.d['atlas']['islands']),6*len(self.es))

    def test_07_source_and_output_hashes(self):
        for path,digest in self.m['input_sha256'].items():self.assertEqual(g['sha']((ROOT/path).read_bytes()),digest)
        for path,digest in self.m['raw_input_sha256'].items():self.assertEqual(g['sha'](Path(path).read_bytes()),digest)
        for path,digest in self.m['output_sha256'].items():self.assertEqual(g['sha'](self.outputs[path]),digest)
        self.assertEqual(g['sha']((ROOT/'scripts/generate_surface_w123_retrofit_escapade.py').read_bytes()),self.m['generator_sha256'])
        ref=next(x for x in json.loads((ROOT/g['REFS']).read_bytes()) if x['id']=='retrofit_escapade')
        self.assertEqual(g['sha'](g['PHOTO'].read_bytes()),ref['sha256'])
        self.assertEqual(self.m['default_photo_sha256'],ref['sha256'])
        self.assertFalse(self.m['native_accepted']);self.assertGreater(len(self.m['limitations']),3)

    def test_08_editable_bb_exact_parity(self):
        bb=json.loads(self.outputs[g['ART']+'inspection.bbmodel'])
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),self.outputs[g['TEXTURE']])
        self.assertEqual(len(bb['elements']),len(self.es));self.assertEqual(bb['display'],self.model['display'])
        self.assertEqual(sum(len(g['children']) for g in bb['outliner']),len(self.es))
        self.assertEqual(len({e['uuid'] for e in bb['elements']}),len(self.es))
        for e,b in zip(self.es,bb['elements']):
            self.assertEqual(e['name'],b['name']);self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            r=e.get('rotation',{});self.assertEqual(b['rotation'],[r.get(a,0) for a in 'xyz'])
            self.assertEqual(b['origin'],r.get('origin',[8,8,8]));self.assertFalse(b['box_uv'])
            for face in g['FACES']:np.testing.assert_allclose(np.array(e['faces'][face]['uv'])*64,b['faces'][face]['uv'])
        self.assertFalse(bb['destiny_w136']['nativeAccepted'])

    def test_09_no_detached_geometry(self):
        edges={i:set() for i in range(len(self.es))}
        for i,a in enumerate(self.es):
            for j in range(i):
                if intersects(a,self.es[j]):edges[i].add(j);edges[j].add(i)
        reached={0};todo=[0]
        while todo:
            for j in edges[todo.pop()]-reached:reached.add(j);todo.append(j)
        missing=set(range(len(self.es)))-reached
        self.assertFalse(missing,'Detached: '+', '.join(self.es[i]['name'] for i in sorted(missing)))


if __name__=='__main__':unittest.main(verbosity=2)
