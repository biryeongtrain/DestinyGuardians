#!/usr/bin/env python3
"""W126 semantic volumes, physical apertures, UV allocation and integration invariants."""
import hashlib
import importlib.util
import io
import json
import math
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
from PIL import Image
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'art/weapons/w123/the_recluse'
ASSETS=ROOT/'src/main/resources/assets/destiny'
MODELS=ASSETS/'models/weapon_surface_w123'


class RecluseSurface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models={part:json.loads((MODELS/f'the_recluse{suffix}.json').read_bytes())
                    for part,suffix in [('full',''),('body','_body'),('magazine','_magazine')]}
        cls.manifest=json.loads((ART/'manifest.json').read_bytes())

    def test_native_schema_and_display(self):
        canon=json.loads((ASSETS/'models/weapon/submachine_gun/the_recluse.json').read_bytes())
        self.assertEqual(self.models['full']['display'],canon['display'])
        for part,model in self.models.items():
            if part!='full':self.assertNotIn('display',model)
            self.assertEqual(model['textures']['0'],'destiny:item/weapon/w123/the_recluse')
            for e in model['elements']:
                self.assertEqual(len(e['from']),3)
                self.assertTrue(all(-16<=x<=32 for x in e['from']+e['to']))
                self.assertTrue(all(a<=b for a,b in zip(e['from'],e['to'])))
                self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
                self.assertTrue(all(math.isfinite(e['rotation'][a]) for a in 'xyz'))
                self.assertTrue(e['faces'])
                for face in e['faces'].values():
                    self.assertEqual(face['texture'],'#0')
                    self.assertTrue(all(0<=u<=16 for u in face['uv']))

    @staticmethod
    def generator():
        spec=importlib.util.spec_from_file_location('recluse_semantic',ROOT/'scripts/generate_surface_w123_the_recluse.py')
        g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
        return g

    def test_solid_semantic_assembly_and_reload_frame(self):
        g=self.generator();body=self.models['body']['elements'];mag=self.models['magazine']['elements']
        self.assertEqual(self.models['full']['elements'],body+mag)
        self.assertTrue(all(e['name'].startswith('magazine/') for e in mag))
        self.assertTrue(set(e['name'] for e in body).isdisjoint(e['name'] for e in mag))
        self.assertEqual(len(body)+len(mag),self.manifest['elements'])
        self.assertLessEqual(len(body)+len(mag),1000)
        self.assertLess(len(body)+len(mag),120)  # current authored design, not a global quality cap
        for e in body+mag:
            self.assertEqual(len(e['faces']),6)
            self.assertTrue(all(b-a>.03 for a,b in zip(e['from'],e['to'])),e['name'])
        receiver=next(e for e in body if e['name']=='receiver/main')
        self.assertGreater(receiver['to'][0]-receiver['from'][0],1.2)
        self.assertGreater(receiver['to'][2]-receiver['from'][2],10)
        self.assertEqual(self.manifest['profile_caps'],0)
        self.assertEqual(self.manifest['profile_wall_cuboids'],0)
        self.assertEqual(self.manifest['source_plane_skins'],0)
        design=json.loads((ART/'design.json').read_bytes())
        self.assertFalse(design['magazine']['coordinate_rebase'])
        self.assertEqual(design['frame']['anchor'],[8,8,8])
        # Independent W100 source proxy envelope; compare world vertices, not
        # local unrotated box coordinates. No pivot/axis rebase is permitted.
        v=np.concatenate([g.vertices(e) for e in mag])
        expected=np.array([[7.395,6.201,7.119],[8.605,9.870,10.056]])
        self.assertTrue(np.all(abs(np.array([v.min(0),v.max(0)])-expected)<.55))
        g.assert_assembled_budget([None]*1000)
        with self.assertRaisesRegex(AssertionError,'1001 > 1000'):g.assert_assembled_budget([None]*1001)

    def test_physical_apertures(self):
        g=self.generator();es=self.models['full']['elements']
        def ray_hits(e,origin,direction):
            # Transform ray into each solid's local box frame and intersect.
            R=g.rotation(e);o=np.array(e['rotation']['origin'])
            p=(np.array(origin)-o)@R+o;d=np.array(direction)@R
            near,far=-float('inf'),float('inf')
            for a in range(3):
                lo,hi=e['from'][a],e['to'][a]
                if abs(d[a])<1e-9:
                    if not lo<=p[a]<=hi:return False
                else:
                    t=sorted(((lo-p[a])/d[a],(hi-p[a])/d[a]))
                    near=max(near,t[0]);far=min(far,t[1])
            return far>=max(0,near)
        # These paths are in the holes, and adjacent rays must hit actual bars.
        sight=[e for e in es if e['name'].startswith('sight/')]
        self.assertFalse(any(ray_hits(e,[8,14.1,0],[0,0,1]) for e in sight))
        self.assertTrue(any(ray_hits(e,[7.46,13.8,0],[0,0,1]) for e in sight))
        self.assertFalse(any(ray_hits(e,[5,9.25,6.60],[1,0,0]) for e in es))
        self.assertTrue(any(ray_hits(e,[5,8.52,6.60],[1,0,0]) for e in es))
        # Central stock opening, surrounded by the diagonal brace and receiver.
        self.assertFalse(any(ray_hits(e,[5,9.0,12.0],[1,0,0]) for e in es))
        crown=[e for e in es if e['name'].startswith('muzzle/crown')]
        self.assertFalse(any(ray_hits(e,[8,11.51,-4],[0,0,1]) for e in crown))
        self.assertTrue(any(ray_hits(e,[8.52,11.51,-4],[0,0,1]) for e in crown))
        bore=next(e for e in es if e['name']=='muzzle/bore-recess')
        self.assertTrue(ray_hits(bore,[8,11.51,-4],[0,0,1]))
        self.assertGreater(bore['from'][2]-min(e['from'][2] for e in crown),.4)

    def test_face_uv_packing_artwork_and_inspection(self):
        tex=Image.open(ASSETS/'textures/item/weapon/w123/the_recluse.png')
        self.assertEqual(tex.mode,'RGBA');self.assertEqual(tex.size,(1024,1024))
        design=json.loads((ART/'design.json').read_bytes());pixels=np.array(tex)
        occupied=np.zeros((1024,1024),bool);tiles={}
        for island in design['uv_layout']['islands']:
            x,y,X,Y=island['pixels'];region=np.s_[y:Y,x:X]
            self.assertFalse(occupied[region].any());occupied[region]=True
            tile=pixels[region];self.assertTrue((tile[:,:,3]==255).all())
            tiles[(island['element'],island['face'])]=tile
        self.assertEqual(len(tiles),self.manifest['elements']*6)
        # Default two-sided burgundy bird fields must survive the UV repack.
        # Require both chromatic art and pale interior fields, not a flat tint.
        for face in ('west','east'):
            tile=tiles[('stock/bird-field',face)].astype(float)
            red=(tile[:,:,0]>tile[:,:,1]*1.45)&(tile[:,:,0]>tile[:,:,2]*1.35)
            white=(tile[:,:,1]>150)&(tile[:,:,2]>150)
            self.assertGreater(red.mean(),.12)
            self.assertGreater(white.mean(),.05)
            # The front hood is white with a small charge window, not a
            # misplaced patch of the coarse rear bird decoration.
            hood=tiles[('optic/hood-main',face)].astype(float)
            red=(hood[:,:,0]>hood[:,:,1]*1.45)&(hood[:,:,0]>hood[:,:,2]*1.35)
            white=(hood[:,:,1]>150)&(hood[:,:,2]>150)
            self.assertLess(red.mean(),.30)
            self.assertGreater(white.mean(),.65)
        self.assertGreater(occupied.mean(),.30)
        self.assertLess(occupied.mean(),.90)
        for rel,pin in self.manifest['sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),pin,rel)
        bb=json.loads((ART/'inspection.bbmodel').read_bytes())
        self.assertEqual(len(bb['elements']),self.manifest['elements'])
        self.assertEqual([g['name'] for g in bb['outliner']],['body','magazine'])
        for native,editor in zip(self.models['full']['elements'],bb['elements']):
            self.assertEqual(editor['from'],native['from']);self.assertEqual(editor['to'],native['to'])
            self.assertEqual(set(editor['faces']),{'north','south','west','east','up','down'})
            for face in native['faces']:
                self.assertEqual(editor['faces'][face]['uv'],[u*64 for u in native['faces'][face]['uv']])
        with Image.open(ART/'comparison.png') as comparison:
            self.assertEqual(comparison.size,(2100,1510))

    def test_regenerated_assets(self):
        for path,data in self.generator().generate().items():
            with self.subTest(path=str(path)):self.assertEqual((ROOT/path).read_bytes(),data)


if __name__=='__main__':unittest.main()

