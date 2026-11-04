#!/usr/bin/env python3
"""Small targeted offline W134 regression; no native aesthetic gate."""
import base64
import io
import json
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
g=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_bite_of_the_fox.py'))


def contains(e,p):
    p=np.array(p,float);r=e.get('rotation')
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


class BiteOfTheFoxArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs=g['generate']()
        cls.design=json.loads(cls.outputs[g['ART']+'design.json'])
        cls.manifest=json.loads(cls.outputs[g['ART']+'manifest.json'])
        cls.model=json.loads(cls.outputs[g['MODEL']]);cls.es=cls.model['elements']
        cls.atlas=np.asarray(Image.open(io.BytesIO(cls.outputs[g['TEXTURE']])))

    def test_01_exact_deterministic_regeneration(self):
        for rel,data in self.outputs.items():
            with self.subTest(path=rel):self.assertEqual((ROOT/rel).read_bytes(),data)
        self.assertEqual(set(self.outputs),{g['ART']+n for n in ('design.json','manifest.json','review.md','inspection.bbmodel','comparison.png')}|{g['MODEL'],g['TEXTURE']})
        self.assertLess(sum(map(len,self.outputs.values())),25*1024*1024)

    def test_02_schema_and_combined_budget(self):
        self.assertLessEqual(len(self.es),1000)
        self.assertEqual(self.manifest['counts']['combined'],len(self.es))
        self.assertEqual(self.manifest['counts']['triangles'],0)
        self.assertEqual(self.manifest['emitted_faces'],6*len(self.es))
        self.assertEqual(self.manifest['candidate'],'FULL ONLY')
        self.assertEqual(len({e['name'] for e in self.es}),len(self.es))
        for e in self.es:
            self.assertLessEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertEqual(set(e['faces']),set(g['FACES']))
            self.assertTrue(np.isfinite(g['vertices'](e)).all())
            if 'rotation' in e:self.assertEqual(set(e['rotation']),{'origin','x','y','z'})

    def test_03_source_basis_frame_and_display(self):
        meshes,meta=g['source_meshes']()
        self.assertEqual(meta['source_axis'],{'length':1,'thin':0,'muzzle_sign':-1})
        self.assertEqual(meta['scale'],16.92788203029053)
        self.assertEqual(meta['anchor'],[8.,8.,8.16267280333182])
        self.assertEqual(sum(len(m['faces']) for m in meshes),30932)
        self.assertEqual([m['name'] for m in meshes],meta['source_objects'])
        old=json.loads((ROOT/g['BASE']).read_bytes())
        self.assertEqual(self.model['display'],old['display'])
        ps=np.concatenate([g['vertices'](e) for e in self.es])
        self.assertAlmostEqual(ps[:,2].min(),-15.5)
        self.assertAlmostEqual(ps[:,2].max(),13.5)
        self.assertTrue(any(contains(e,[8,8,8.35]) for e in self.es),'hand grip stays in source frame')
        self.assertAlmostEqual(self.manifest['source_scale'],meta['scale'])
        self.assertEqual(self.manifest['source_anchor'],meta['anchor'])

    def test_04_real_holes_and_solid_depth(self):
        # Probe actual geometry, not a rendered black pixel or transparent texel.
        holes=[('bore',[8,9.89,z]) for z in (-13.94,-13,-12,-10,-8)]
        holes += [('stock',[8,y,z]) for y,z in ((9.35,11.5),(9.45,12),(9.50,12.3))]
        holes += [('guard',[x,8.30,6.65]) for x in (7.8,8,8.2)]
        holes += [('iron sight',[8,10.60,9.11])]
        for tag,p in holes:
            self.assertFalse(any(contains(e,p) for e in self.es),(tag,p))
        for p in ([8,9.5,0],[8,9.6,5.5],[8,9.19,-15.3],[8,10.30,-12.5],[8,8.1,8.35]):
            self.assertTrue(any(contains(e,p) for e in self.es),p)
        # Major filled chassis has cross section in both depth axes.
        for name in ('forearm_core','receiver','pistol_grip','magazine'):
            e=next(e for e in self.es if e['name']==name)
            self.assertGreater(min(np.array(e['to'])-e['from']),.6)

    def test_05_connected_assembly(self):
        # One meaningful regression from observed first-draft blade/hood gaps.
        reached={0};pending=set(range(1,len(self.es)))
        # Precompute all overlap edges once; traversal doesn't rerun geometry.
        edges={i:set() for i in range(len(self.es))}
        for i,a in enumerate(self.es):
            for j in range(i):
                if intersects(a,self.es[j]):edges[i].add(j);edges[j].add(i)
        todo=[0]
        while todo:
            for j in edges[todo.pop()]-reached:reached.add(j);pending.discard(j);todo.append(j)
        self.assertFalse(pending,'Detached solids: '+', '.join(self.es[i]['name'] for i in sorted(pending)))

    def test_06_face_uv_alpha_and_extruded_gutters(self):
        self.assertEqual(self.atlas.shape,(1024,1024,4))
        occupied=np.zeros((1024,1024),bool);rects=[]
        for e in self.es:
            for f in e['faces'].values():
                self.assertEqual(f['texture'],'#0')
                x0,y0,x1,y1=[int(round(q*1024/16)) for q in f['uv']]
                self.assertTrue(2<=x0<x1<=1022 and 2<=y0<y1<=1022)
                self.assertFalse(occupied[y0-2:y1+2,x0-2:x1+2].any())
                occupied[y0-2:y1+2,x0-2:x1+2]=True
                tile=self.atlas[y0:y1,x0:x1];self.assertTrue(np.all(tile[:,:,3]==255))
                for d in (1,2):
                    np.testing.assert_array_equal(self.atlas[y0-d,x0:x1],tile[0])
                    np.testing.assert_array_equal(self.atlas[y1+d-1,x0:x1],tile[-1])
                    np.testing.assert_array_equal(self.atlas[y0:y1,x0-d],tile[:,0])
                    np.testing.assert_array_equal(self.atlas[y0:y1,x1+d-1],tile[:,-1])
                rects.append((x0,y0,x1,y1))
        self.assertEqual(len(set(rects)),6*len(self.es))
        self.assertEqual(self.manifest['alpha_elements'],0)
        self.assertGreater(self.design['palette']['burgundy'][0],self.design['palette']['burgundy'][1]*1.6)
        self.assertGreater(self.design['palette']['brass'][0],self.design['palette']['brass'][2]*2)

    def test_07_provenance_and_output_hashes(self):
        m=self.manifest
        for rel,h in m['input_sha256'].items():self.assertEqual(g['sha']((ROOT/rel).read_bytes()),h)
        for path,h in m['raw_input_sha256'].items():self.assertEqual(g['sha'](Path(path).read_bytes()),h)
        for path,h in m['output_sha256'].items():self.assertEqual(g['sha'](self.outputs[path]),h)
        self.assertEqual(g['sha']((ROOT/'scripts/generate_surface_w123_bite_of_the_fox.py').read_bytes()),m['generator_sha256'])
        ref=next(x for x in json.loads((ROOT/g['REFERENCES']).read_bytes()) if x['id']=='bite_of_the_fox')
        self.assertEqual(g['sha'](g['PHOTO'].read_bytes()),ref['sha256'])
        self.assertEqual(m['default_photo_sha256'],ref['sha256'])
        self.assertFalse(m['native_accepted'])

    def test_08_editable_inspection_parity(self):
        bb=json.loads(self.outputs[g['ART']+'inspection.bbmodel'])
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),self.outputs[g['TEXTURE']])
        self.assertEqual(len(bb['elements']),len(self.es))
        self.assertEqual(sum(len(x['children']) for x in bb['outliner']),len(self.es))
        self.assertEqual(bb['display'],self.model['display'])
        for e,b in zip(self.es,bb['elements']):
            self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            self.assertEqual(e['name'],b['name']);self.assertFalse(b['box_uv'])
            r=e.get('rotation',{});self.assertEqual(b['rotation'],[r.get(a,0) for a in 'xyz'])
            self.assertEqual(b['origin'],r.get('origin',[8,8,8]))
            for face in g['FACES']:
                np.testing.assert_allclose(np.array(e['faces'][face]['uv'])*1024/16,b['faces'][face]['uv'])
                self.assertEqual(b['faces'][face]['texture'],0)
        self.assertFalse(bb['destiny_w134']['nativeAccepted'])

if __name__=='__main__':unittest.main(verbosity=2)
