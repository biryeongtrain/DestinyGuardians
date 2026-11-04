#!/usr/bin/env python3
"""Practical offline regressions for the full Bad Omens art candidate."""
import base64
import json
from pathlib import Path
import sys
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import generate_surface_w123_bad_omens as g


def hits(origin, direction, elements):
    """Ray/solid OBB entry distances, used for a few actual opening probes."""
    origin=np.array(origin,float);direction=np.array(direction,float);result=[]
    for e in elements:
        r=e.get('rotation',{});R=g.rotation(r);c=np.array(r.get('origin',[0,0,0]))
        o=(origin-c)@R+c;v=direction@R;lo=np.array(e['from']);hi=np.array(e['to'])
        near=0.;far=float('inf')
        for a in range(3):
            if abs(v[a])<1e-9:
                if o[a]<lo[a] or o[a]>hi[a]:far=-1;break
            else:
                aa,bb=sorted(((lo[a]-o[a])/v[a],(hi[a]-o[a])/v[a]))
                near=max(near,aa);far=min(far,bb)
        if far>=near:result.append((near,e['name']))
    return sorted(result)


class BadOmensTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads((g.ROOT/(g.ART+'design.json')).read_bytes())
        cls.m=json.loads((g.ROOT/(g.ART+'manifest.json')).read_bytes())
        cls.model=json.loads((g.ROOT/g.MODEL).read_bytes());cls.es=cls.model['elements']
        cls.atlas=Image.open(g.ROOT/g.TEXTURE).convert('RGBA')

    def test_01_full_schema_and_emitted_budget(self):
        self.assertEqual(set(self.d['parts']),{'full'})
        n=len(self.es);self.assertGreater(n,0);self.assertLessEqual(n,1000)
        self.assertEqual(self.m['counts'],{'full':n})
        self.assertEqual(self.m['assembled_elements'],n)
        self.assertEqual(self.m['triangle_adapter_elements'],0)
        self.assertEqual(self.m['alpha_elements'],0)
        self.assertEqual(self.m['emitted_faces'],n*6)
        self.assertEqual(len({e['name'] for e in self.es}),n)
        self.assertEqual(set(self.model),{'credit','textures','elements','display'})
        for e in self.es:
            self.assertEqual(set(e)-{'name','from','to','rotation','faces'},set())
            self.assertTrue(np.isfinite(g.vertices(e)).all())
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertEqual(set(e['faces']),set(g.FACES))
            if 'rotation' in e:self.assertEqual(set(e['rotation']),{'origin','x','y','z'})

    def test_02_face_uv_and_opaque_gutters(self):
        self.assertEqual(self.atlas.size,(1024,1024));a=np.asarray(self.atlas)
        islands=self.d['atlas']['islands'];self.assertEqual(len(islands),len(self.es)*6)
        lookup={e['name']:e for e in self.es};used=np.zeros((1024,1024),bool)
        for island in islands:
            x,y,xx,yy=island['rect'];self.assertTrue(2<=x<xx<=1022 and 2<=y<yy<=1022)
            self.assertFalse(used[y-2:yy+2,x-2:xx+2].any())
            used[y-2:yy+2,x-2:xx+2]=True
            self.assertTrue((a[y-2:yy+2,x-2:xx+2,3]==255).all())
            face=lookup[island['element']]['faces'][island['face']]
            self.assertEqual(face['texture'],'#0')
            self.assertEqual(face['uv'],[q/64 for q in (x,y,xx,yy)])
        self.assertEqual(self.model['textures']['0'],'destiny:item/weapon/w123/bad_omens')

    def test_03_source_reference_and_input_hashes(self):
        for p,digest in self.m['input_sha256'].items():self.assertEqual(g.sha((g.ROOT/p).read_bytes()),digest,p)
        for p,digest in self.m['raw_input_sha256'].items():self.assertEqual(g.sha(Path(p).read_bytes()),digest,p)
        self.assertEqual(self.d['reference']['sha256'],g.sha(g.PHOTO.read_bytes()))
        self.assertEqual(self.d['reference']['bungie_hash'],'991314988')
        self.assertEqual(len(self.d['reference']['default_dyes']),3)
        self.assertEqual(self.m['source_triangles'],27470)
        self.assertEqual(g.sha(Path(g.__file__).read_bytes()),self.m['generator_sha256'])

    def test_04_frame_display_and_hand_contacts(self):
        old=json.loads((g.ROOT/g.BASE).read_bytes())
        self.assertEqual(self.model['display'],old['display'])
        self.assertEqual(self.m['source_anchor'],[8,8,8])
        self.assertEqual(self.m['source_scale'],24.638767902867134)
        self.assertEqual(self.m['frame']['muzzle_axis'],'-Z')
        points=np.concatenate([g.vertices(e) for e in self.es])
        self.assertAlmostEqual(points[:,2].min(),self.d['source']['model_bounds'][0][2],places=5)
        self.assertAlmostEqual(points[:,2].max(),self.d['source']['model_bounds'][1][2],places=5)
        for name in ('foregrip_contact','pistol_contact'):
            h=hits(self.m['frame'][name],[1,0,0],self.es)
            self.assertTrue(h and h[0][0]==0,name)

    def test_05_deep_open_muzzle_and_real_wall(self):
        for dx,dy in ((0,0),(.3,.1),(-.25,-.2)):
            self.assertEqual(hits([8+dx,12.2245+dy,-7],[0,0,1],self.es),[])
        wall=hits([8.92,12.2245,-7],[0,0,1],self.es)
        self.assertTrue(wall);self.assertTrue(wall[0][1].startswith('muzzle_rim'))

    def test_06_guard_and_wood_frame_openings(self):
        self.assertEqual(hits([5,9.18,6.25],[1,0,0],self.es),[])
        self.assertTrue(hits([5,8.77,6.25],[1,0,0],self.es)[0][1].startswith('guard'))
        self.assertEqual(hits([5,10.43,3.3],[1,0,0],self.es),[])
        self.assertEqual(hits([5,10.20,3.3],[1,0,0],self.es)[0][1],'forearm_lower_wood')

    def test_07_recessed_optic_and_notch(self):
        optic=hits([9.72,12.18,2.8],[0,0,1],self.es)
        self.assertEqual(optic[0][1],'right_recessed_glass')
        self.assertGreater(optic[0][0],.8)
        rim=hits([10.14,12.18,2.8],[0,0,1],self.es)
        self.assertTrue(rim[0][1].startswith('right_optic_lip'))
        top=hits([8,13.59,1.2],[0,0,1],self.es)
        self.assertEqual(top[0][1],'top_front_glass')
        self.assertGreater(top[0][0],.6)
        self.assertEqual(hits([8,14.12,3.6],[0,0,1],self.es),[])

    def test_08_embedded_editable_solids_and_texture(self):
        bb=json.loads((g.ROOT/(g.ART+'inspection.bbmodel')).read_bytes())
        self.assertEqual(len(bb['elements']),len(self.es));self.assertFalse(bb['destiny_w130']['nativeAccepted'])
        self.assertEqual(bb['display'],self.model['display'])
        texture=base64.b64decode(bb['textures'][0]['source'].split(',',1)[1])
        self.assertEqual(texture,(g.ROOT/g.TEXTURE).read_bytes())
        for b,e in zip(bb['elements'],self.es):
            self.assertEqual(b['type'],'cube');self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
            self.assertEqual(b['rotation'],[e.get('rotation',{}).get(a,0) for a in 'xyz'])
            for f in g.FACES:self.assertEqual(b['faces'][f]['uv'],[q*64 for q in e['faces'][f]['uv']])
        self.assertEqual(sum(len(gp['children']) for gp in bb['outliner']),len(self.es))

    def test_09_output_hashes_and_owned_artifacts(self):
        for p,digest in self.m['output_sha256'].items():self.assertEqual(g.sha((g.ROOT/p).read_bytes()),digest,p)
        batch=json.loads((g.ROOT/'docs/qa/2026-10-26/w130/batch.json').read_bytes())
        owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w130-bad_omens'))
        self.assertEqual(len(owned),10)
        self.assertTrue(set(self.m['output_sha256'])|{g.ART+'manifest.json'}<=owned)
        self.assertTrue(self.m['full_only']);self.assertFalse(self.m['native_accepted'])
        self.assertEqual(set(p.name for p in (g.ROOT/(g.ASSET+'models/weapon_surface_w123')).glob('bad_omens*.json')),{'bad_omens.json'})
        with Image.open(g.ROOT/(g.ART+'comparison.png')) as image:
            self.assertEqual(image.size,(2000,2000))


if __name__=='__main__':unittest.main(verbosity=2)
