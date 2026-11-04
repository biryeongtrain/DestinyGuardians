#!/usr/bin/env python3
"""Practical W143 offline regression checks; no native/PBR certification."""
import base64
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
G = runpy.run_path(str(ROOT/'scripts/generate_surface_w123_brass_attacks.py'))


def read(path):
    return json.loads((ROOT/path).read_bytes())


def local(points, e):
    points = np.asarray(points, float)
    if 'rotation' in e:
        r=e['rotation'];o=np.array(r['origin'])
        points=(points-o)@G['H']['rotation']({r['axis']:r['angle']})+o
    return points


def inside(point, e):
    p=local(point,e)
    return bool(np.all(p>np.array(e['from'])+1e-7) and np.all(p<np.array(e['to'])-1e-7))


def intersects(a, b, e):
    """Finite segment / rotated solid box intersection, including boundary hits."""
    a,b=local([a,b],e);delta=b-a;t0,t1=0.,1.
    for i in range(3):
        lo,hi=e['from'][i],e['to'][i]
        if abs(delta[i])<1e-10:
            if a[i]<lo or a[i]>hi:
                return False
        else:
            near,far=sorted(((lo-a[i])/delta[i],(hi-a[i])/delta[i]))
            t0=max(t0,near);t1=min(t1,far)
            if t0>t1:
                return False
    return True


class BrassAttacksArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=read(G['ART']+'design.json');cls.m=read(G['ART']+'manifest.json')
        cls.model=read(G['MODEL']);cls.es=cls.model['elements']
        cls.lookup={e['name']:e for e in cls.es}
        cls.bb=read(G['ART']+'inspection.bbmodel')
        cls.px=np.array(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))

    def test_emitted_schema_positive_dimensions_and_filled_cores(self):
        self.assertEqual(len(self.es),len(self.lookup))
        self.assertEqual(len(self.es),self.m['assembled_elements'])
        self.assertLessEqual(len(self.es),1000)
        self.assertEqual(0,self.m['triangle_adapter_elements'])
        self.assertEqual(0,self.m['alpha_body_elements'])
        for e in self.es:
            self.assertLessEqual(set(e),{'name','from','to','faces','rotation'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']),e['name'])
            self.assertTrue(np.isfinite(G['vertices'](e)).all())
            self.assertEqual(set(G['FACES']),set(e['faces']))
        grip=self.lookup['grip_core'];receiver=self.lookup['receiver_core']
        self.assertGreater(grip['to'][0]-grip['from'][0],1.3)
        self.assertGreater(grip['to'][1]-grip['from'][1],5)
        self.assertGreater(receiver['to'][2]-receiver['from'][2],6)
        for e in (grip,receiver):
            lo,hi=np.array(e['from']),np.array(e['to'])
            r=e.get('rotation');o=np.array(r['origin']) if r else np.zeros(3)
            R=G['H']['rotation']({r['axis']:r['angle']}) if r else np.eye(3)
            for t in (.15,.5,.85):
                p=((lo*(1-t)+hi*t)-o)@R.T+o
                self.assertTrue(inside(p,e))

    def test_original_source_frame_scale_anchor_display_and_envelope(self):
        meta=read(G['BB'])['destiny_w30']
        self.assertEqual(read(G['BASE'])['display'],self.model['display'])
        self.assertEqual(meta['scale'],self.m['source_scale'])
        self.assertEqual(meta['anchor'],self.m['source_anchor'])
        self.assertEqual('-Z',self.d['coordinate_policy']['muzzle'])
        self.assertEqual(meta['scale'],self.d['coordinate_policy']['scale'])
        self.assertEqual(meta['anchor'],self.d['coordinate_policy']['anchor'])
        p=np.concatenate([G['vertices'](e) for e in self.es])
        np.testing.assert_allclose([p.min(0),p.max(0)],self.m['actual_bounds'],atol=1e-9)
        # Remodeling changes exact silhouette; retain the baseline hand envelope.
        self.assertTrue(np.all(abs(np.array(self.m['actual_bounds'])-meta['model_bounds'])<.20))

    def test_real_bore_exposed_trigger_bay_and_three_keyhole_rays(self):
        rays=[([8,G['BARREL_Y'],-4.25],[8,G['BARREL_Y'],-2.25]),
              ([6,11.85,5.45],[10,11.85,5.45])]
        for z in (-2.63,-1.08,.47):
            rays.extend([([6,13.30,z],[10,13.30,z]),
                         ([6,12.94,z],[10,12.94,z])])
        for a,b in rays:
            hits=[e['name'] for e in self.es if intersects(a,b,e)]
            self.assertEqual([],hits,(a,b,hits))
        self.assertTrue(inside([8,G['BARREL_Y'],-2.10],self.lookup['bore_backstop']))
        self.assertTrue(inside([8,13.3,-3.5],self.lookup['underlug_web_0']))
        self.assertTrue(inside([8,13.79,5.19],self.lookup['receiver_core']))
        self.assertTrue(inside([8,9.8,8.5],self.lookup['grip_core']))

    def test_every_face_uv_opaque_with_gutters_and_no_island_overlap(self):
        self.assertEqual((1024,1024,4),self.px.shape)
        self.assertEqual(len(self.es)*6,len(self.d['atlas']['islands']))
        cover=np.zeros((1024,1024),bool)
        for row in self.d['atlas']['islands']:
            x,y,X,Y=row['pixels']
            self.assertTrue(2<=x<X<=1022 and 2<=y<Y<=1022)
            self.assertTrue(np.all(self.px[y-2:Y+2,x-2:X+2,3]==255))
            self.assertFalse(cover[y-2:Y+2,x-2:X+2].any())
            cover[y-2:Y+2,x-2:X+2]=True
            uv=self.lookup[row['element']]['faces'][row['face']]['uv']
            np.testing.assert_allclose(uv,np.array([x,y,X,Y])/64)
            self.assertEqual('#0',self.lookup[row['element']]['faces'][row['face']]['texture'])

    def test_accepted_inert_source_counts_bounds_and_provenance(self):
        meshes,meta=G['source_meshes']()
        self.assertEqual(sorted(meta['source_objects']),sorted(m['name'] for m in meshes))
        self.assertEqual({'Brass-Attacks.00.000':19864,'Brass-Attacks.01.000':432},
                         {m['name']:len(m['faces']) for m in meshes})
        self.assertEqual(sum(len(m['faces']) for m in meshes),self.m['source_counts']['actual_total'])
        self.assertEqual(self.m['source_counts']['actual_total']-meta['source_triangles'],
                         self.m['source_counts']['difference'])
        p=np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=3e-6,rtol=0)
        for path,h in self.d['input_sha256'].items():
            self.assertEqual(h,G['sha']((ROOT/path).read_bytes()),path)
        for path,h in self.d['raw_input_sha256'].items():
            self.assertEqual(h,G['sha'](Path(path).read_bytes()),path)
        self.assertNotIn('src/main/resources/weapon_surface_w123/manifest.json',self.d['input_sha256'])

    def test_editable_inspection_parity_and_embedded_texture(self):
        self.assertEqual(len(self.es),len(self.bb['elements']))
        self.assertEqual(len(self.es),sum(len(g['children']) for g in self.bb['outliner']))
        self.assertEqual(self.model['display'],self.bb['display'])
        self.assertEqual((ROOT/G['TEXTURE']).read_bytes(),base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]))
        for b in self.bb['elements']:
            e=self.lookup[b['name']]
            self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            r=e.get('rotation')
            self.assertEqual([r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],b['rotation'])
            for f in G['FACES']:
                np.testing.assert_allclose(np.array(e['faces'][f]['uv'])*64,b['faces'][f]['uv'])

    def test_output_provenance_and_honest_scope(self):
        self.assertTrue(self.m['full_only'])
        self.assertFalse(self.m['native_accepted']);self.assertFalse(self.m['pbr_accepted'])
        for path,h in self.m['output_sha256'].items():
            self.assertEqual(h,G['sha']((ROOT/path).read_bytes()),path)
        self.assertEqual(6*len(self.es),self.m['emitted_faces'])
        self.assertEqual(len(self.es),sum(self.m['groups'].values()))
        self.assertTrue(any('exposed trigger' in s for s in self.m['limitations']))
        with Image.open(ROOT/(G['ART']+'comparison.png')) as im:
            self.assertEqual((2220,2225),im.size)

    def test_deterministic_complete_generation(self):
        out=G['generate']()
        self.assertEqual({G['ART']+s for s in ('design.json','manifest.json','review.md','inspection.bbmodel','comparison.png')}
                         | {G['MODEL'],G['TEXTURE']},set(out))
        for path,data in out.items():
            self.assertEqual((ROOT/path).read_bytes(),data,path)


if __name__=='__main__':
    unittest.main(verbosity=2)
